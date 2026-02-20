from __future__ import annotations

import json
import logging
import time
from pathlib import Path

import typer
from opensearchpy.exceptions import NotFoundError

from searchctl.chunking import split_into_chunks
from searchctl.config import AppConfig, load_config
from searchctl.embeddings import Embedder
from searchctl.extractors import extract_markdown, extract_pdf, extract_text
from searchctl.fs_scanner import discover_files
from searchctl.fusion import rrf_fuse
from searchctl.hashing import make_chunk_id, make_doc_id, sha256_text
from searchctl.inspect import inspect_chunk
from searchctl.logging import configure_logging
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
from searchctl.snippets import build_snippet

app = typer.Typer(help="Local personal search CLI")
LOG = logging.getLogger("searchctl")


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


def _process_one(path: Path, cfg: AppConfig, db: MetadataDB, embedder: Embedder, os_client, q_client) -> str:
    doc_id = make_doc_id(path)
    mtime = int(path.stat().st_mtime)

    try:
        extracted, title, source_type = _extract(path)
    except Exception as exc:
        source_type = "pdf" if path.suffix.lower() == ".pdf" else "text"
        _write_doc_error(db, path, doc_id, source_type, exc)
        return "error"

    content_hash = sha256_text(extracted)

    existing = db.get_document(doc_id)
    if cfg.indexing.reindex_policy == "incremental" and existing and existing["content_hash"] == content_hash:
        return "skipped"

    cache_dir = Path(cfg.metadata.extracted_text_cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{doc_id}.txt"
    cache_path.write_text(extracted, encoding="utf-8")

    delete_doc_chunks_os(os_client, cfg.opensearch.index_name, doc_id)
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
        }
        chunk_payloads.append(payload)
        chunk_texts.append(c.text)

    index_chunks(os_client, cfg.opensearch.index_name, chunk_payloads)

    partial = False
    if chunk_texts:
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
    return "partial" if partial else "indexed"


def _delete_removed_docs(db: MetadataDB, current_paths: set[str], cfg: AppConfig, os_client, q_client) -> int:
    removed = 0
    for row in db.list_documents():
        if row["path"] in current_paths:
            continue
        doc_id = row["doc_id"]
        delete_doc_chunks_os(os_client, cfg.opensearch.index_name, doc_id)
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
) -> None:
    configure_logging(debug=debug)
    cfg = load_config(config)
    if force:
        cfg.indexing.reindex_policy = "force"

    db = MetadataDB(cfg.metadata.sqlite_path)
    db.init_schema()

    os_client = make_opensearch_client(cfg.opensearch.url)
    q_client = make_qdrant_client(cfg.qdrant.url)

    if not opensearch_ready(os_client):
        typer.echo("OpenSearch not ready")
        raise typer.Exit(1)
    if not qdrant_ready(q_client):
        typer.echo("Qdrant not ready")
        raise typer.Exit(1)

    ensure_index(os_client, cfg.opensearch.index_name)
    ensure_collection(q_client, cfg.qdrant.collection_name, cfg.qdrant.vector_size, cfg.qdrant.distance)
    try:
        probe_collection_write(q_client, cfg.qdrant.collection_name, cfg.qdrant.vector_size)
    except Exception as exc:
        typer.echo(f"Qdrant write check failed: {exc}")
        raise typer.Exit(1)

    paths = discover_files(cfg.roots, cfg.include_extensions, cfg.exclude_globs)
    path_set = {str(p) for p in paths}
    removed = _delete_removed_docs(db, path_set, cfg, os_client, q_client)

    embedder = Embedder(cfg.embeddings.model_name, cfg.embeddings.device)

    indexed = 0
    skipped = 0
    errors = 0
    partial = 0

    for path in paths:
        status = _process_one(path, cfg, db, embedder, os_client, q_client)
        if status == "indexed":
            indexed += 1
        elif status == "partial":
            partial += 1
        elif status == "skipped":
            skipped += 1
        else:
            errors += 1

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
) -> None:
    cfg = load_config(config)
    os_client = make_opensearch_client(cfg.opensearch.url)
    q_client = make_qdrant_client(cfg.qdrant.url)
    embedder = Embedder(cfg.embeddings.model_name, cfg.embeddings.device)

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
    qvec = embedder.encode_query(query).tolist()
    vec = vector_search(
        q_client,
        cfg.qdrant.collection_name,
        qvec,
        cfg.search.vector_top_k,
        source_type,
        path_contains,
    )

    fused = rrf_fuse(bm25, vec, cfg.search.rrf_k)
    limit = top or cfg.search.return_top_n
    result_rows = []
    seen_docs: set[str] = set()
    for rank, row in enumerate(fused, start=1):
        payload = row.payload
        if source_type and payload.get("source_type") != source_type:
            continue
        if path_contains and path_contains not in payload.get("path", ""):
            continue
        if collapse_by_doc and payload.get("doc_id") in seen_docs:
            continue
        seen_docs.add(payload.get("doc_id"))
        result_rows.append(
            {
                "rank": rank,
                "score": row.score,
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
                },
            }
        )
        if len(result_rows) >= limit:
            break

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


if __name__ == "__main__":
    app()
