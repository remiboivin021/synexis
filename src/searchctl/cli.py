from __future__ import annotations

import json
import logging
import re
import time
import unicodedata
from pathlib import Path
from typing import Any
import typer
from opensearchpy.exceptions import NotFoundError

from searchctl.chunking import split_into_chunks
from searchctl.config import AppConfig, load_config
from searchctl.document_map import classify_document, infer_scope, map_boost, write_document_map
from searchctl.extractors import extract_markdown, extract_pdf, extract_text
from searchctl.fs_scanner import discover_files
from searchctl.fusion import rrf_fuse
from searchctl.hashing import make_chunk_id, make_doc_id, sha256_text
from searchctl.inspect import inspect_chunk
from searchctl.logging import configure_logging
from searchctl.llm_openrouter import OpenRouterConfig, call_openrouter_summary
from searchctl.metadata.db import MetadataDB
from searchctl.opensearch.client import make_client as make_opensearch_client
from searchctl.opensearch.client import wait_ready as opensearch_ready
from searchctl.opensearch.index import delete_doc_chunks as delete_doc_chunks_os
from searchctl.opensearch.index import ensure_index, index_chunks
from searchctl.opensearch.queries import bm25_search
from searchctl.qdrant.client import make_client as make_qdrant_client
from searchctl.qdrant.client import wait_ready as qdrant_ready
from searchctl.qdrant.collections import delete_doc_vectors, ensure_collection, probe_collection_write, upsert_vectors
from searchctl.qdrant.queries import vector_search
from searchctl.prompts import build_summary_user_prompt
from searchctl.snippets import build_snippet
from searchctl.summary import collect_sources, format_sources, summary_input_rows

app = typer.Typer(help="Local personal search CLI")
LOG = logging.getLogger("searchctl")
STOPWORDS_FR = {"de", "des", "du", "la", "le", "les", "un", "une", "et", "en", "dans", "sur", "pour", "au", "aux"}


def _extract(path: Path) -> tuple[str, str, str]:
    suffix = path.suffix.lower()
    if suffix == ".md":
        text, title = extract_markdown(path)
        source_type = "markdown"
    elif suffix == ".pdf":
        text, title = extract_pdf(path)
        source_type = "pdf"
    else:
        text, title = extract_text(path)
        source_type = "text"
    return text, title, source_type


def _to_json(data: dict | list, as_json: bool) -> None:
    if as_json:
        typer.echo(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        typer.echo(data)


def _format_search_results(query: str, rows: list[dict]) -> str:
    if not rows:
        return f"No results for query: {query}"

    lines = [f'Results for: "{query}"', ""]
    for row in rows:
        citation = row.get("citation", {})
        signals = row.get("signals", {})
        lines.extend(
            [
                f'[{row.get("rank")}] {row.get("doc_title") or "(untitled)"}',
                f'  score: {float(row.get("score", 0.0)):.6f}',
                f'  path: {row.get("doc_path") or "-"}',
                f'  snippet: {row.get("snippet") or ""}',
                (
                    "  citation: "
                    f'{citation.get("chunk_id")} '
                    f'[{citation.get("start_char")}:{citation.get("end_char")}]'
                ),
                (
                    "  signals: "
                    f'bm25_rank={signals.get("bm25_rank")} '
                    f'vector_rank={signals.get("vector_rank")} '
                    f'fusion={signals.get("fusion_method")}'
                ),
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def _summarize_with_openrouter(query: str, rows: list[dict[str, Any]], cfg: AppConfig, top_n: int) -> str:
    summary_input = summary_input_rows(rows, top_n)
    prompt = build_summary_user_prompt(query, summary_input)
    llm_cfg = OpenRouterConfig(
        base_url=cfg.llm.base_url,
        model=cfg.llm.model,
        api_key=cfg.llm.api_key,
        app_name="searchctl",
    )
    return call_openrouter_summary(llm_cfg, prompt)


def _normalize_text(text: str) -> str:
    no_accents = "".join(ch for ch in unicodedata.normalize("NFKD", text) if not unicodedata.combining(ch))
    return no_accents.lower()


def _query_terms(query: str) -> list[str]:
    terms = []
    for raw in _normalize_text(query).replace('"', " ").replace("'", " ").split():
        token = raw.strip(".,:;!?()[]{}")
        if len(token) < 3 or token in STOPWORDS_FR:
            continue
        terms.append(token)
    return terms


def _matches_terms(payload: dict, required_terms: list[str]) -> bool:
    if not required_terms:
        return True
    haystack = _normalize_text(
        " ".join(
            [
                str(payload.get("title") or ""),
                str(payload.get("path") or ""),
                str(payload.get("text") or ""),
            ]
        )
    )
    words = set(re.findall(r"[a-z0-9_]+", haystack))
    return all(term in words for term in required_terms)


def _project_intent_guard(query: str, payload: dict) -> bool:
    q = _normalize_text(query)
    wants_project = "projet" in q or "project" in q
    wants_active = ("en cours" in q) or ("actif" in q) or ("active" in q) or ("current" in q)
    if not (wants_project and wants_active):
        return True
    title = _normalize_text(str(payload.get("title") or ""))
    path = _normalize_text(str(payload.get("path") or ""))
    text = _normalize_text(str(payload.get("text") or ""))
    is_project_doc = ("03_projects" in path) or ("project" in title) or ("projet" in title)
    is_active_doc = ("en cours" in text) or ("actif" in text) or ("active" in text) or ("current" in text)
    return is_project_doc and is_active_doc


def _write_doc_error(db: MetadataDB, path: Path, doc_id: str, source_type: str, err: Exception) -> None:
    now = int(time.time())
    db.log_error("extract", str(err), path=str(path), doc_id=doc_id)
    db.upsert_document(
        {
            "doc_id": doc_id,
            "path": str(path),
            "source_type": source_type,
            "title": path.stem,
            "mtime": int(path.stat().st_mtime),
            "content_hash": "",
            "status": "error",
            "error": str(err),
            "updated_at": now,
        }
    )


def _process_one(path: Path, cfg: AppConfig, db: MetadataDB, embedder: Any, os_client, q_client) -> dict:
    doc_id = make_doc_id(path)
    mtime = int(path.stat().st_mtime)

    try:
        extracted, title, source_type = _extract(path)
    except Exception as exc:
        source_type = "pdf" if path.suffix.lower() == ".pdf" else "text"
        _write_doc_error(db, path, doc_id, source_type, exc)
        return {"status": "error", "map_entry": classify_document(str(path), path.stem, "")}

    map_entry = classify_document(str(path), title, extracted)

    content_hash = sha256_text(extracted)

    existing = db.get_document(doc_id)
    if cfg.indexing.reindex_policy == "incremental" and existing and existing["content_hash"] == content_hash:
        return {"status": "skipped", "map_entry": map_entry}

    cache_dir = Path(cfg.metadata.extracted_text_cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{doc_id}.txt"
    cache_path.write_text(extracted, encoding="utf-8")

    delete_doc_chunks_os(os_client, cfg.opensearch.index_name, doc_id)
    if q_client is not None:
        delete_doc_vectors(q_client, cfg.qdrant.collection_name, doc_id)
    db.delete_doc_chunks(doc_id)

    chunks = split_into_chunks(
        extracted,
        cfg.chunking.target_chars,
        cfg.chunking.overlap_chars,
        cfg.chunking.min_chunk_chars,
    )

    chunk_payloads: list[dict] = []
    chunk_texts: list[str] = []
    for c in chunks:
        chunk_id = make_chunk_id(doc_id, c.ordinal, c.text)
        payload = {
            "chunk_id": chunk_id,
            "doc_id": doc_id,
            "path": str(path),
            "title": title,
            "source_type": source_type,
            "ordinal": c.ordinal,
            "text": c.text,
            "start_char": c.start_char,
            "end_char": c.end_char,
            "heading_path": c.heading_path,
            "mtime": mtime,
            "doc_scope": map_entry["scope"],
            "doc_active": map_entry["active"],
        }
        chunk_payloads.append(payload)
        chunk_texts.append(c.text)

    index_chunks(os_client, cfg.opensearch.index_name, chunk_payloads)

    partial = False
    if chunk_texts and embedder is not None and q_client is not None:
        try:
            vectors = embedder.encode_passages(chunk_texts, batch_size=cfg.embeddings.batch_size).tolist()
            upsert_vectors(q_client, cfg.qdrant.collection_name, vectors, chunk_payloads)
        except Exception as exc:
            partial = True
            db.log_error("embed", str(exc), path=str(path), doc_id=doc_id)

    now = int(time.time())
    db.upsert_document(
        {
            "doc_id": doc_id,
            "path": str(path),
            "source_type": source_type,
            "title": title,
            "mtime": mtime,
            "content_hash": content_hash,
            "status": "partial" if partial else "indexed",
            "error": None,
            "updated_at": now,
        }
    )

    for p in chunk_payloads:
        db.insert_chunk_row(
            {
                "chunk_id": p["chunk_id"],
                "doc_id": doc_id,
                "ordinal": p["ordinal"],
                "text_hash": sha256_text(p["text"]),
                "start_char": p["start_char"],
                "end_char": p["end_char"],
                "heading_path": p["heading_path"],
            }
        )
    return {"status": "partial" if partial else "indexed", "map_entry": map_entry}


def _delete_removed_docs(db: MetadataDB, current_paths: set[str], cfg: AppConfig, os_client, q_client) -> int:
    removed = 0
    for row in db.list_documents():
        if row["path"] in current_paths:
            continue
        doc_id = row["doc_id"]
        delete_doc_chunks_os(os_client, cfg.opensearch.index_name, doc_id)
        if q_client is not None:
            delete_doc_vectors(q_client, cfg.qdrant.collection_name, doc_id)
        db.delete_doc_chunks(doc_id)
        db.delete_document(doc_id)
        removed += 1
    return removed


@app.command()
def ingest(
    config: str = typer.Option("config.yaml", "--config"),
    force: bool = typer.Option(False, "--force"),
    debug: bool = typer.Option(False, "--debug"),
    no_vector: bool = typer.Option(False, "--no-vector", help="Skip embedding and vector indexing (BM25-only ingest)."),
) -> None:
    configure_logging(debug=debug)
    cfg = load_config(config)
    if force:
        cfg.indexing.reindex_policy = "force"

    db = MetadataDB(cfg.metadata.sqlite_path)
    db.init_schema()

    os_client = make_opensearch_client(cfg.opensearch.url)
    q_client = None if no_vector else make_qdrant_client(cfg.qdrant.url)

    if not opensearch_ready(os_client):
        typer.echo("OpenSearch not ready")
        raise typer.Exit(1)
    if q_client is not None and not qdrant_ready(q_client):
        typer.echo("Qdrant not ready")
        raise typer.Exit(1)

    ensure_index(os_client, cfg.opensearch.index_name)
    if q_client is not None:
        ensure_collection(q_client, cfg.qdrant.collection_name, cfg.qdrant.vector_size, cfg.qdrant.distance)
        try:
            probe_collection_write(q_client, cfg.qdrant.collection_name, cfg.qdrant.vector_size)
        except Exception as exc:
            typer.echo(f"Qdrant write check failed: {exc}")
            raise typer.Exit(1)

    paths = discover_files(cfg.roots, cfg.include_extensions, cfg.exclude_globs)
    path_set = {str(p) for p in paths}
    removed = _delete_removed_docs(db, path_set, cfg, os_client, q_client)

    embedder = None
    if not no_vector:
        from searchctl.embeddings import Embedder

        embedder = Embedder(cfg.embeddings.model_name, cfg.embeddings.device)

    indexed = 0
    skipped = 0
    errors = 0
    partial = 0
    map_entries: list[dict] = []

    for path in paths:
        result = _process_one(path, cfg, db, embedder, os_client, q_client)
        status = result["status"]
        if result.get("map_entry"):
            map_entries.append(result["map_entry"])
        if status == "indexed":
            indexed += 1
        elif status == "partial":
            partial += 1
        elif status == "skipped":
            skipped += 1
        else:
            errors += 1

    map_path = Path(cfg.metadata.sqlite_path).parent / "document_map.json"
    write_document_map(map_entries, map_path)

    db.commit()
    typer.echo(
        f"ingest complete: indexed={indexed} partial={partial} skipped={skipped} removed={removed} errors={errors}"
    )


@app.command()
def search(
    query: str,
    config: str = typer.Option("config.yaml", "--config"),
    json_out: bool = typer.Option(False, "--json"),
    top: int | None = typer.Option(None, "--top"),
    collapse_by_doc: bool = typer.Option(False, "--collapse-by-doc"),
    source_type: str | None = typer.Option(None, "--source-type"),
    path_contains: str | None = typer.Option(None, "--path-contains"),
    strict: bool = typer.Option(False, "--strict", help="Require lexical term match for each result."),
    scope: str | None = typer.Option(
        None,
        "--scope",
        help="Restrict to scope: projects|playbooks|decisions|dashboard|knowledge|other",
    ),
    active_only: bool = typer.Option(False, "--active-only", help="Keep only documents inferred as active."),
    must_contain: list[str] = typer.Option(
        None,
        "--must-contain",
        help="Repeatable required term(s) that must appear in title/path/text.",
    ),
    summarize: bool = typer.Option(False, "--summarize", help="Generate a human-readable synthesis with OpenRouter."),
    summary_top_k: int = typer.Option(8, "--summary-top-k", help="How many ranked results are provided to LLM summary."),
    summary_use_hybrid: bool = typer.Option(
        False,
        "--summary-use-hybrid",
        help="Use vector retrieval in summarize mode (may load heavy embedding runtime).",
    ),
) -> None:
    cfg = load_config(config)
    os_client = make_opensearch_client(cfg.opensearch.url)
    use_vector = (not summarize) or summary_use_hybrid
    q_client = make_qdrant_client(cfg.qdrant.url) if use_vector else None

    try:
        bm25 = bm25_search(
            os_client,
            cfg.opensearch.index_name,
            query,
            cfg.search.bm25_top_k,
            source_type,
            path_contains,
        )
    except NotFoundError as exc:
        if getattr(exc, "error", "") == "index_not_found_exception":
            typer.echo(
                f"OpenSearch index '{cfg.opensearch.index_name}' not found. Run `searchctl ingest --config {config}` first."
            )
            raise typer.Exit(1)
        raise
    if use_vector:
        from searchctl.embeddings import Embedder

        embedder = Embedder(cfg.embeddings.model_name, cfg.embeddings.device)
        qvec = embedder.encode_query(query).tolist()
        vec = vector_search(
            q_client,
            cfg.qdrant.collection_name,
            qvec,
            cfg.search.vector_top_k,
            source_type,
            path_contains,
        )
    else:
        vec = []

    fused = rrf_fuse(bm25, vec, cfg.search.rrf_k)
    boosted_rows = [
        (row, row.score + map_boost(row.payload, query))
        for row in fused
    ]
    boosted_rows.sort(
        key=lambda item: (
            -item[1],
            item[0].bm25_rank if item[0].bm25_rank is not None else 10**9,
            item[0].vector_rank if item[0].vector_rank is not None else 10**9,
            item[0].chunk_id,
        )
    )
    limit = top or cfg.search.return_top_n
    strict_terms = _query_terms(query) if strict else []
    explicit_terms = [_normalize_text(t) for t in (must_contain or []) if t.strip()]
    required_terms = strict_terms + explicit_terms
    result_rows = []
    seen_docs: set[str] = set()
    for rank, (row, effective_score) in enumerate(boosted_rows, start=1):
        payload = row.payload
        if source_type and payload.get("source_type") != source_type:
            continue
        if path_contains and path_contains not in payload.get("path", ""):
            continue
        payload_scope = str(payload.get("doc_scope") or infer_scope(str(payload.get("path") or "")))
        if scope and payload_scope != scope:
            continue
        if active_only and not bool(payload.get("doc_active")):
            continue
        if not _matches_terms(payload, required_terms):
            continue
        if strict and not _project_intent_guard(query, payload):
            continue
        if collapse_by_doc and payload.get("doc_id") in seen_docs:
            continue
        seen_docs.add(payload.get("doc_id"))
        result_rows.append(
            {
                "rank": rank,
                "score": effective_score,
                "doc_path": payload.get("path"),
                "doc_title": payload.get("title"),
                "snippet": build_snippet(payload.get("text", ""), payload.get("highlight")),
                "citation": {
                    "chunk_id": payload.get("chunk_id"),
                    "start_char": payload.get("start_char"),
                    "end_char": payload.get("end_char"),
                },
                "signals": {
                    "bm25_rank": row.bm25_rank,
                    "vector_rank": row.vector_rank,
                    "fusion_method": "rrf",
                    "scope": payload_scope,
                    "active": bool(payload.get("doc_active")),
                },
            }
        )
        if len(result_rows) >= limit:
            break

    if summarize:
        sources = collect_sources(result_rows)
        if not result_rows:
            summary = f"Aucun resultat pour la requete: {query}"
        else:
            summary = _summarize_with_openrouter(query, result_rows, cfg, summary_top_k)

        if json_out:
            _to_json({"query": query, "summary": summary, "sources": sources, "results": result_rows}, True)
        else:
            typer.echo(summary.rstrip())
            typer.echo("")
            typer.echo(format_sources(sources))
        return

    if json_out:
        _to_json(result_rows, True)
    else:
        typer.echo(_format_search_results(query, result_rows))


@app.command()
def status(
    config: str = typer.Option("config.yaml", "--config"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    cfg = load_config(config)
    db = MetadataDB(cfg.metadata.sqlite_path)
    db.init_schema()
    os_client = make_opensearch_client(cfg.opensearch.url)
    q_client = make_qdrant_client(cfg.qdrant.url)
    payload = db.status()
    payload["opensearch"] = "ok" if opensearch_ready(os_client, max_attempts=1) else "down"
    payload["qdrant"] = "ok" if qdrant_ready(q_client, max_attempts=1) else "down"
    _to_json(payload, json_out)


@app.command()
def inspect(
    doc: str | None = typer.Option(None, "--doc"),
    chunk: str | None = typer.Option(None, "--chunk"),
    config: str = typer.Option("config.yaml", "--config"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    if not doc and not chunk:
        raise typer.BadParameter("provide --doc or --chunk")
    cfg = load_config(config)
    db = MetadataDB(cfg.metadata.sqlite_path)
    db.init_schema()

    if chunk:
        out = inspect_chunk(db, cfg.metadata.extracted_text_cache_dir, chunk)
    else:
        row = db.fetch_doc(str(Path(doc).resolve()))
        out = dict(row) if row else None
    _to_json(out or {}, json_out)


@app.command()
def web(
    config: str = typer.Option("config.yaml", "--config"),
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8080, "--port"),
    allow_remote: bool = typer.Option(
        False,
        "--allow-remote",
        help="Allow non-local bind host (disabled by default).",
    ),
) -> None:
    from searchctl.web import serve_web

    serve_web(config, host, port, allow_remote)


if __name__ == "__main__":
    app()
