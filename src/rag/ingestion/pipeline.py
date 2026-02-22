from __future__ import annotations

import logging
from pathlib import Path

from langchain_core.documents import Document

from rag.chunking.splitters import chunk_documents, stable_doc_id
from rag.config import RagConfig
from rag.embeddings.factory import build_embeddings
from rag.ingestion.manifest import compute_doc_hash, load_manifest, now_iso, save_manifest
from rag.loaders.local_files import discover_local_files, load_local_documents
from rag.vectorstore.factory import build_vectorstore

LOG = logging.getLogger("rag.ingestion")


def ingest_path(
    config: RagConfig,
    path: str,
    glob: str = "**/*",
    tenant_id: str | None = None,
    dry_run: bool = False,
) -> dict:
    config.validate()
    root = Path(path)
    files = discover_local_files(root, glob)
    docs = load_local_documents(files, tenant_id=tenant_id)

    manifest = load_manifest(config.persist_path)

    embeddings = build_embeddings(config)
    vectorstore = build_vectorstore(config, embeddings)

    processed = 0
    skipped = 0
    deleted = 0
    ingested = 0

    for doc in docs:
        processed += 1
        source = str(doc.metadata.get("source") or "")
        doc_id = stable_doc_id(source)
        content_hash = compute_doc_hash(doc.page_content)

        previous = manifest.get(doc_id)
        if previous and previous.get("hash") == content_hash:
            skipped += 1
            LOG.info("ingestion.skip doc_id=%s source=%s", doc_id, source)
            continue

        enriched = Document(page_content=doc.page_content, metadata={**doc.metadata, "doc_id": doc_id, "source": source})
        chunks = chunk_documents([enriched], chunk_size=config.chunk_size, chunk_overlap=config.chunk_overlap)
        chunks = [
            Document(page_content=c.page_content, metadata=_clean_metadata(c.metadata))
            for c in chunks
        ]

        if not dry_run:
            if previous:
                vectorstore.delete(where={"doc_id": doc_id})
                deleted += 1
                LOG.info("ingestion.delete_old doc_id=%s source=%s", doc_id, source)

            vectorstore.add_documents(chunks)

            manifest[doc_id] = {
                "hash": content_hash,
                "num_chunks": len(chunks),
                "sources": [source],
                "ingested_at": now_iso(),
            }
        ingested += 1
        LOG.info("ingestion.upsert doc_id=%s source=%s chunks=%s", doc_id, source, len(chunks))

    if not dry_run:
        existing_sources = {str(d.metadata.get("source") or "") for d in docs}
        for doc_id, meta in list(manifest.items()):
            sources = set(meta.get("sources") or [])
            if sources and not (sources & existing_sources):
                vectorstore.delete(where={"doc_id": doc_id})
                manifest.pop(doc_id, None)
                deleted += 1
                LOG.info("ingestion.delete_missing doc_id=%s", doc_id)

        save_manifest(config.persist_path, manifest)

    return {
        "processed": processed,
        "skipped": skipped,
        "ingested": ingested,
        "deleted": deleted,
        "dry_run": dry_run,
        "manifest_path": str(config.persist_path / "manifest.json"),
    }


def _clean_metadata(metadata: dict) -> dict:
    out: dict = {}
    for key, value in metadata.items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            out[str(key)] = value
    return out
