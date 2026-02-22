from __future__ import annotations

from langchain_core.documents import Document

from rag.config import RagConfig
from rag.generation.chain import answer_question


def test_generation_refuses_without_context(monkeypatch) -> None:
    monkeypatch.setenv("RAG_EMBED_MODEL", "hashing")
    cfg = RagConfig.from_env()
    result = answer_question(cfg, "What is the answer?", docs=[])
    assert result["answer"] == "I don't know based on the provided documents."
    assert result["citations"] == []


def test_generation_includes_citations(monkeypatch) -> None:
    monkeypatch.setenv("RAG_EMBED_MODEL", "hashing")
    cfg = RagConfig.from_env()
    docs = [
        Document(
            page_content="LangChain composes retriever and generator for grounded responses.",
            metadata={"source": "tests/fixtures/doc1.md", "doc_id": "doc1", "chunk_id": "chunk1"},
        )
    ]
    result = answer_question(cfg, "What does LangChain compose?", docs=docs)
    assert result["citations"]
    assert "[" in result["answer"] and "]" in result["answer"]
    assert result["answer"] != "I don't know based on the provided documents."
