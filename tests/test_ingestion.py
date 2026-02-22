from __future__ import annotations

import json
from pathlib import Path

from rag.chunking.splitters import stable_chunk_id
from rag.config import RagConfig
from rag.ingestion.pipeline import ingest_path


def _set_test_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("RAG_VECTORSTORE", "chroma")
    monkeypatch.setenv("RAG_PERSIST_DIR", str(tmp_path / "chroma"))
    monkeypatch.setenv("RAG_EMBED_MODEL", "hashing")
    monkeypatch.setenv("RAG_CHUNK_SIZE", "120")
    monkeypatch.setenv("RAG_CHUNK_OVERLAP", "20")


def test_chunk_ids_are_deterministic() -> None:
    chunk_a = stable_chunk_id(doc_id="doc-1", ordinal=0, text_hash="abc")
    chunk_b = stable_chunk_id(doc_id="doc-1", ordinal=0, text_hash="abc")
    assert chunk_a == chunk_b


def test_manifest_skips_unchanged_documents(tmp_path: Path, monkeypatch) -> None:
    _set_test_env(monkeypatch, tmp_path)
    raw = tmp_path / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    source = raw / "sample.md"
    source.write_text("RAG pipelines need deterministic manifests.", encoding="utf-8")

    cfg = RagConfig.from_env()
    first = ingest_path(cfg, path=str(raw))
    second = ingest_path(cfg, path=str(raw))

    assert first["ingested"] == 1
    assert second["skipped"] == 1

    manifest = json.loads((cfg.persist_path / "manifest.json").read_text(encoding="utf-8"))
    assert len(manifest) == 1
