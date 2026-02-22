from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class RagConfig:
    openai_api_key: str
    vectorstore: str
    persist_dir: str
    embed_model: str
    chat_model: str
    chunk_size: int
    chunk_overlap: int
    retrieval_k: int
    fetch_k: int
    search_type: str
    enable_rewrite: bool
    enable_rerank: bool
    rerank_top_n: int
    log_level: str
    context_max_chars: int
    rewrite_model: str
    low_confidence_score: float

    @classmethod
    def from_env(cls) -> "RagConfig":
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            vectorstore=os.getenv("RAG_VECTORSTORE", "chroma").strip().lower(),
            persist_dir=os.getenv("RAG_PERSIST_DIR", "./data/chroma_db"),
            embed_model=os.getenv("RAG_EMBED_MODEL", "text-embedding-3-large"),
            chat_model=os.getenv("RAG_CHAT_MODEL", "gpt-4.1-mini"),
            chunk_size=int(os.getenv("RAG_CHUNK_SIZE", "1000")),
            chunk_overlap=int(os.getenv("RAG_CHUNK_OVERLAP", "150")),
            retrieval_k=int(os.getenv("RAG_RETRIEVAL_K", "8")),
            fetch_k=int(os.getenv("RAG_FETCH_K", "40")),
            search_type=os.getenv("RAG_SEARCH_TYPE", "mmr").strip().lower(),
            enable_rewrite=_is_true(os.getenv("RAG_ENABLE_REWRITE", "0")),
            enable_rerank=_is_true(os.getenv("RAG_ENABLE_RERANK", "0")),
            rerank_top_n=int(os.getenv("RAG_RERANK_TOP_N", "8")),
            log_level=os.getenv("RAG_LOG_LEVEL", "INFO").upper(),
            context_max_chars=int(os.getenv("RAG_CONTEXT_MAX_CHARS", "18000")),
            rewrite_model=os.getenv("RAG_REWRITE_MODEL", "gpt-4.1-mini"),
            low_confidence_score=float(os.getenv("RAG_LOW_CONFIDENCE_SCORE", "0.0")),
        )

    @property
    def persist_path(self) -> Path:
        return Path(self.persist_dir)

    def validate(self) -> None:
        if self.search_type not in {"similarity", "mmr"}:
            raise ValueError("RAG_SEARCH_TYPE must be similarity|mmr")
        if self.vectorstore not in {"chroma", "faiss", "qdrant", "weaviate", "pinecone"}:
            raise ValueError("RAG_VECTORSTORE must be chroma|faiss|qdrant|weaviate|pinecone")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("RAG_CHUNK_OVERLAP must be < RAG_CHUNK_SIZE")
        if self.chunk_size <= 0:
            raise ValueError("RAG_CHUNK_SIZE must be > 0")
        if self.retrieval_k <= 0 or self.fetch_k <= 0:
            raise ValueError("RAG_RETRIEVAL_K and RAG_FETCH_K must be > 0")


def _is_true(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}
