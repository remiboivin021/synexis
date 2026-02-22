from __future__ import annotations

from pathlib import Path

from rag.config import RagConfig
from rag.ingestion.pipeline import ingest_path
from rag.retrieval.retriever import retrieve_documents


def _set_test_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("RAG_VECTORSTORE", "chroma")
    monkeypatch.setenv("RAG_PERSIST_DIR", str(tmp_path / "chroma"))
    monkeypatch.setenv("RAG_EMBED_MODEL", "hashing")
    monkeypatch.setenv("RAG_SEARCH_TYPE", "mmr")
    monkeypatch.setenv("RAG_RETRIEVAL_K", "4")
    monkeypatch.setenv("RAG_FETCH_K", "10")


def test_retrieval_returns_relevant_chunk(tmp_path: Path, monkeypatch) -> None:
    _set_test_env(monkeypatch, tmp_path)
    raw = tmp_path / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    (raw / "chroma.txt").write_text(
        "Chroma stores vectors and metadata for retrieval augmented generation.",
        encoding="utf-8",
    )
    (raw / "other.md").write_text("This document is about gardening.", encoding="utf-8")

    cfg = RagConfig.from_env()
    ingest_path(cfg, path=str(raw))

    docs, debug = retrieve_documents(cfg, "Which system stores vectors for retrieval?")

    assert docs
    assert any("chroma" in str(d.metadata.get("source", "")).lower() for d in docs)
    assert debug["retrieved"]


def test_retrieval_filters_unrelated_query(tmp_path: Path, monkeypatch) -> None:
    _set_test_env(monkeypatch, tmp_path)
    raw = tmp_path / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    (raw / "notes.md").write_text("This corpus discusses gardens and flowers only.", encoding="utf-8")

    cfg = RagConfig.from_env()
    ingest_path(cfg, path=str(raw))

    docs, _ = retrieve_documents(cfg, "What is Chroma?")
    assert docs == []
