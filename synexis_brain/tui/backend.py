from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import sqlite3
import unicodedata
from typing import Any

from synexis_brain.config import load_config
from synexis_brain.indexer.incremental import apply_incremental_index
from synexis_brain.indexer.metadata import connect_meta, ensure_meta_tables
from synexis_brain.indexer.pipeline import run_dot_file
from synexis_brain.indexer.scan import scan_vaults
from synexis_brain.search.backends import build_bm25_backend
from synexis_brain.search.bm25 import SQLiteBm25Index
from synexis_brain.search.vector import EmbeddingService, VectorStore


@dataclass
class SearchFilters:
    vault_id: str = ""
    chunk_type: str = ""
    tag: str = ""
    status: str = ""


class SearchService:
    def __init__(self, db_path: str, config_path: str) -> None:
        config_file = Path(config_path).expanduser().resolve()
        self.config_path = str(config_file)
        config_dir = config_file.parent

        raw_db_path = Path(db_path).expanduser()
        if not raw_db_path.is_absolute():
            raw_db_path = config_dir / raw_db_path
        self.db_path = str(raw_db_path)

        self.config = load_config(self.config_path)

        # Normalize relative config paths against config file location to avoid cwd-dependent reindexing.
        search_cfg = self.config.get("search", {}) if isinstance(self.config.get("search", {}), dict) else {}
        self.vector_min_hits = int(search_cfg.get("vector_min_hits", 2))
        self.vector_min_score = float(search_cfg.get("vector_min_score", 0.15))
        self.bm25_min_term_coverage = float(search_cfg.get("bm25_min_term_coverage", 0.5))
        tantivy_dir = search_cfg.get("tantivy_index_dir")
        if isinstance(tantivy_dir, str) and tantivy_dir and not Path(tantivy_dir).is_absolute():
            search_cfg["tantivy_index_dir"] = str((config_dir / tantivy_dir).resolve())
            self.config["search"] = search_cfg

        self.vault_paths = {}
        for vault in self.config.get("vaults", []):
            vault_id = str(vault["id"])
            raw_vault = Path(str(vault["path"])).expanduser()
            if not raw_vault.is_absolute():
                raw_vault = config_dir / raw_vault
            resolved_vault = raw_vault.resolve()
            vault["path"] = str(resolved_vault)
            self.vault_paths[vault_id] = resolved_vault
        vector_cfg = self.config.get("vector", {}) if isinstance(self.config.get("vector", {}), dict) else {}
        embedding_backend = str(vector_cfg.get("embedding_backend", "sentence-transformers")).strip().lower()
        embedding_model = str(
            vector_cfg.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2")
        ).strip()
        self.conn = connect_meta(self.db_path)
        ensure_meta_tables(self.conn)
        self.bm25 = build_bm25_backend(self.config, self.conn)
        self.embedder = EmbeddingService(
            self.conn,
            model_name=embedding_model,
            backend=embedding_backend,
        )
        self.vector = VectorStore(self.conn, self.config)

    def reindex(self) -> dict[str, Any]:
        ctx = {
            "config_path": self.config_path,
            "db_path": self.db_path,
            "db_conn": self.conn,
        }

        # Keep execution through the pipeline runner contract.
        out = run_dot_file(
            path=Path("synexis_brain/pipelines/index.dot"),
            registry={
                "scan_vaults": scan_vaults,
                "apply_incremental_index": apply_incremental_index,
            },
            context={**ctx, "bm25_backend": self.bm25},
        )
        chunks = out.get("chunks", [])
        vectors = self.embedder.embeddings_for_chunks(chunks)
        self.vector.upsert(chunks, vectors)
        self._bootstrap_missing_vectors()
        for item in out.get("changes", {}).get("deleted", []):
            self.vector.delete_file(item["vault_id"], item["path"])
        return out.get("changes", {})

    def search(self, query: str, filters: SearchFilters, limit: int = 50) -> list[dict[str, Any]]:
        if not query.strip():
            return []

        query_text = query.strip()
        query_vector = self.embedder.embed_text(query_text)
        vector_results = self.vector.topk(query_vector=query_vector, limit=limit * 4)

        filtered = self._apply_filters(vector_results, filters)
        focused_vector = self._apply_query_coverage(filtered, query_text)
        if focused_vector:
            filtered = focused_vector
        structural_candidates = self._structural_candidates(query_text, filters, limit=max(3, limit // 2))
        has_explicit_filters = bool(filters.vault_id or filters.chunk_type or filters.tag or filters.status)
        top_vector_score = float(filtered[0].get("score", 0.0)) if filtered else 0.0
        vector_reliable = bool(filtered) and top_vector_score >= self.vector_min_score
        if vector_reliable and len(filtered) >= min(self.vector_min_hits, limit):
            filtered.sort(key=lambda x: float(x.get("score", 0.0)), reverse=True)
            if structural_candidates:
                out: list[dict[str, Any]] = []
                seen: set[str] = set()
                for row in structural_candidates + filtered:
                    cid = str(row.get("chunk_id", ""))
                    if cid in seen:
                        continue
                    out.append(row)
                    seen.add(cid)
                    if len(out) >= limit:
                        return out
                return out
            return filtered[:limit]
        if has_explicit_filters and filtered:
            filtered.sort(key=lambda x: float(x.get("score", 0.0)), reverse=True)
            return filtered[:limit]

        # Fallback lexical search when vector backend has no/too few usable hits.
        bm25_results = self.bm25.topk(query=query_text, limit=limit * 4)
        filtered_bm25 = self._apply_filters(bm25_results, filters)
        if structural_candidates:
            seen = {str(r.get("chunk_id", "")) for r in filtered_bm25}
            for row in structural_candidates:
                cid = str(row.get("chunk_id", ""))
                if cid in seen:
                    continue
                filtered_bm25.append(row)
                seen.add(cid)
        filtered_bm25 = self._apply_query_coverage(filtered_bm25, query_text)
        filtered_bm25.sort(key=lambda x: float(x.get("score", 0.0)))
        if not filtered or not vector_reliable:
            return filtered_bm25[:limit]

        # Blend: keep vector hits first, then complete with lexical hits.
        out: list[dict[str, Any]] = []
        seen: set[str] = set()
        for row in filtered:
            cid = str(row.get("chunk_id", ""))
            if cid in seen:
                continue
            out.append(row)
            seen.add(cid)
            if len(out) >= limit:
                return out
        for row in filtered_bm25:
            cid = str(row.get("chunk_id", ""))
            if cid in seen:
                continue
            out.append(row)
            seen.add(cid)
            if len(out) >= limit:
                break
        return out

    def citation_for(self, result: dict[str, Any]) -> str:
        heading = result.get("heading") or ""
        if heading:
            return f"[[{result['path']}#{heading}]]"
        return f"[[{result['path']}]]"

    def open_note_path(self, result: dict[str, Any]) -> str:
        vault_root = self.vault_paths.get(result["vault_id"])
        if vault_root is None:
            return result["path"]
        return str((vault_root / result["path"]).resolve())

    def _apply_filters(self, rows: list[dict[str, Any]], filters: SearchFilters) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for row in rows:
            if filters.vault_id and row.get("vault_id") != filters.vault_id:
                continue
            if filters.chunk_type and row.get("type") != filters.chunk_type:
                continue
            if filters.status and row.get("status") != filters.status:
                continue
            if filters.tag and filters.tag not in str(row.get("tags", "")):
                continue
            out.append(row)
        return out

    def _apply_query_coverage(self, rows: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
        terms = _query_terms(query)
        if len(terms) < 2:
            return rows

        out: list[dict[str, Any]] = []
        for row in rows:
            structural_haystack = _fold_text(
                " ".join(
                [
                    str(row.get("path", "")),
                    str(row.get("heading", "")),
                    str(row.get("type", "")),
                    str(row.get("status", "")),
                    str(row.get("tags", "")),
                ]
                )
            )
            haystack = " ".join(
                [
                    structural_haystack,
                    _fold_text(str(row.get("preview", ""))),
                ]
            )
            hay_tokens = re.findall(r"[a-z0-9]+", haystack)
            structural_tokens = re.findall(r"[a-z0-9]+", structural_haystack)
            matched = 0
            structural_matched = 0
            for term in terms:
                variants = {term}
                if term.endswith("s") and len(term) > 4:
                    variants.add(term[:-1])
                is_match = any(v in haystack for v in variants)
                structural_match = any(v in structural_haystack for v in variants)
                if not is_match:
                    # Prefix/radical fallback (e.g. "projets" vs "projects").
                    for v in variants:
                        if len(v) < 4:
                            continue
                        root = v[:5]
                        if any(tok.startswith(root) or root.startswith(tok[:5]) for tok in hay_tokens if len(tok) >= 5):
                            is_match = True
                            break
                if not structural_match:
                    for v in variants:
                        if len(v) < 4:
                            continue
                        root = v[:5]
                        if any(tok.startswith(root) or root.startswith(tok[:5]) for tok in structural_tokens if len(tok) >= 5):
                            structural_match = True
                            break
                if is_match:
                    matched += 1
                if structural_match:
                    structural_matched += 1
            coverage = matched / len(terms)
            if coverage >= self.bm25_min_term_coverage and structural_matched >= 1:
                out.append(row)
        return out

    def _bootstrap_missing_vectors(self) -> None:
        if not isinstance(self.bm25, SQLiteBm25Index):
            return
        try:
            rows = self.conn.execute(
                """
                SELECT b.chunk_id, b.vault_id, b.path, b.heading, b.text, b.tags, b.type, b.status
                FROM bm25_chunks AS b
                LEFT JOIN vector_chunks AS v ON v.chunk_id = b.chunk_id
                WHERE v.chunk_id IS NULL
                """
            ).fetchall()
        except sqlite3.Error:
            return
        if not rows:
            return
        chunks: list[dict[str, Any]] = []
        for row in rows:
            chunks.append(
                {
                    "chunk_id": row[0],
                    "chunk_hash": row[0],
                    "vault_id": row[1],
                    "path": row[2],
                    "heading": row[3],
                    "text": row[4],
                    "tags": row[5],
                    "type": row[6],
                    "status": row[7],
                }
            )
        vectors = self.embedder.embeddings_for_chunks(chunks)
        self.vector.upsert(chunks, vectors)

    def _structural_candidates(self, query: str, filters: SearchFilters, limit: int) -> list[dict[str, Any]]:
        if not isinstance(self.bm25, SQLiteBm25Index):
            return []
        terms = _query_terms(query)
        if not terms:
            return []
        try:
            rows = self.conn.execute(
                """
                SELECT chunk_id, vault_id, path, heading, text, tags, type, status
                FROM bm25_chunks
                """
            ).fetchall()
        except sqlite3.Error:
            return []

        best_by_path: dict[str, dict[str, Any]] = {}
        for row in rows:
            candidate = {
                "chunk_id": row[0],
                "vault_id": row[1],
                "path": row[2],
                "heading": row[3],
                "preview": str(row[4])[:240],
                "tags": row[5],
                "type": row[6],
                "status": row[7],
                "score": -1.0,
            }
            if self._apply_filters([candidate], filters) == []:
                continue
            path_only = _fold_text(str(candidate.get("path", "")))
            structural = _fold_text(
                " ".join(
                [
                    str(candidate.get("path", "")),
                    str(candidate.get("heading", "")),
                        str(candidate.get("type", "")),
                        str(candidate.get("status", "")),
                        str(candidate.get("tags", "")),
                    ]
                )
            )
            hits = 0
            path_hits = 0
            for term in terms:
                variants = {term}
                if term.endswith("s") and len(term) > 4:
                    variants.add(term[:-1])
                if any(v in structural for v in variants):
                    hits += 1
                if any(v in path_only for v in variants):
                    path_hits += 1
            if hits == 0:
                continue
            # Boost only when file path itself matches query terms.
            if path_hits == 0:
                continue
            candidate["score"] = 1.2 + 0.1 * float(path_hits)
            path_key = str(candidate.get("path", ""))
            existing = best_by_path.get(path_key)
            if existing is None or float(candidate["score"]) > float(existing.get("score", 0.0)):
                best_by_path[path_key] = candidate
        out = list(best_by_path.values())
        out.sort(key=lambda x: float(x.get("score", 0.0)), reverse=True)
        return out[:limit]


_STOPWORDS = {
    "de",
    "du",
    "des",
    "le",
    "la",
    "les",
    "un",
    "une",
    "et",
    "en",
    "dans",
    "sur",
    "a",
    "au",
    "aux",
    "the",
    "and",
    "in",
    "on",
    "to",
    "for",
}


def _query_terms(query: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", _fold_text(query))
    out: list[str] = []
    for tok in tokens:
        if len(tok) <= 1 or tok in _STOPWORDS:
            continue
        out.append(tok)
    return out


def _fold_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch)).lower()
