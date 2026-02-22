from __future__ import annotations

import hashlib
from collections import Counter

from langchain_core.embeddings import Embeddings

from rag.config import RagConfig


class HashEmbeddings(Embeddings):
    def __init__(self, dim: int = 384):
        self.dim = dim

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed_one(text)

    def _embed_one(self, text: str) -> list[float]:
        counts = Counter(text.lower().split())
        vec = [0.0] * self.dim
        for token, freq in counts.items():
            idx = int(hashlib.sha1(token.encode("utf-8")).hexdigest(), 16) % self.dim
            vec[idx] += float(freq)
        norm = sum(v * v for v in vec) ** 0.5
        if norm == 0:
            return vec
        return [v / norm for v in vec]


def build_embeddings(config: RagConfig) -> Embeddings:
    provider = (config.embed_model or "").strip().lower()
    if provider in {"hash", "hashing", "local-hash"}:
        return HashEmbeddings()

    if config.openai_api_key:
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(model=config.embed_model, api_key=config.openai_api_key)

    # Safe local fallback for offline tests and development without API key.
    return HashEmbeddings()
