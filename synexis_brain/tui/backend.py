from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import Any

from synexis_brain.config import load_config
from synexis_brain.indexer.incremental import apply_incremental_index
from synexis_brain.indexer.metadata import connect_meta, ensure_meta_tables
from synexis_brain.indexer.pipeline import run_dot_file
from synexis_brain.indexer.scan import scan_vaults
from synexis_brain.search.backends import build_bm25_backend
from synexis_brain.search.hybrid import hybrid_merge
from synexis_brain.search.nlu import infer_filters
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
        embedding_backend = str(vector_cfg.get("embedding_backend", "hash")).strip().lower()
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
        for item in out.get("changes", {}).get("deleted", []):
            self.vector.delete_file(item["vault_id"], item["path"])
        return out.get("changes", {})

    def search(self, query: str, filters: SearchFilters, limit: int = 50) -> list[dict[str, Any]]:
        if not query.strip():
            return []

        nlu = infer_filters(query, available_vaults=list(self.vault_paths.keys()))
        effective = SearchFilters(
            vault_id=filters.vault_id or nlu.inferred.vault_id,
            chunk_type=filters.chunk_type or nlu.inferred.chunk_type,
            tag=filters.tag or nlu.inferred.tag,
            status=filters.status or nlu.inferred.status,
        )

        bm25_results = self.bm25.topk(query=nlu.text_query, limit=limit)
        query_vector = self.embedder.embed_text(nlu.text_query)
        vector_results = self.vector.topk(query_vector=query_vector, limit=limit)
        results = hybrid_merge(bm25_results=bm25_results, vector_results=vector_results, limit=limit)
        out: list[dict[str, Any]] = []
        for row in results:
            if effective.vault_id and row.get("vault_id") != effective.vault_id:
                continue
            if effective.chunk_type and row.get("type") != effective.chunk_type:
                continue
            if effective.status and row.get("status") != effective.status:
                continue
            if effective.tag and effective.tag not in str(row.get("tags", "")):
                continue
            out.append(row)
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
