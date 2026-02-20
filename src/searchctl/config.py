from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, model_validator


class ChunkingConfig(BaseModel):
    target_chars: int = 2200
    overlap_chars: int = 250
    min_chunk_chars: int = 400


class EmbeddingsConfig(BaseModel):
    model_name: str = "intfloat/e5-small-v2"
    batch_size: int = 32
    device: Literal["auto", "cpu", "cuda"] = "auto"


class OpenSearchConfig(BaseModel):
    url: str = "http://localhost:9200"
    index_name: str = "personal_chunks_v1"


class QdrantConfig(BaseModel):
    url: str = "http://localhost:6333"
    collection_name: str = "personal_chunks_v1"
    vector_size: int = 384
    distance: Literal["Cosine"] = "Cosine"


class IndexingConfig(BaseModel):
    reindex_policy: Literal["incremental", "force"] = "incremental"
    max_workers: int = 8


class SearchConfig(BaseModel):
    bm25_top_k: int = 50
    vector_top_k: int = 50
    fusion: Literal["rrf"] = "rrf"
    rrf_k: int = 60
    rerank: Literal["off"] = "off"
    rerank_top_k: int = 20
    return_top_n: int = 10
    collapse_by_doc_default: bool = False


class MetadataConfig(BaseModel):
    sqlite_path: str = "./data/metadata.db"
    extracted_text_cache_dir: str = "./data/extracted_text"


class LLMConfig(BaseModel):
    provider: Literal["openrouter"] = "openrouter"
    base_url: str = "https://openrouter.ai/api/v1"
    model: str = "openrouter/auto"
    api_key: str = ""


class AppConfig(BaseModel):
    roots: list[str] = Field(default_factory=list)
    include_extensions: list[str] = Field(default_factory=lambda: [".md", ".pdf", ".txt"])
    exclude_globs: list[str] = Field(default_factory=list)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    embeddings: EmbeddingsConfig = Field(default_factory=EmbeddingsConfig)
    opensearch: OpenSearchConfig = Field(default_factory=OpenSearchConfig)
    qdrant: QdrantConfig = Field(default_factory=QdrantConfig)
    indexing: IndexingConfig = Field(default_factory=IndexingConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    metadata: MetadataConfig = Field(default_factory=MetadataConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)

    @model_validator(mode="after")
    def validate_constraints(self) -> "AppConfig":
        c = self.chunking
        if c.overlap_chars >= c.target_chars:
            raise ValueError("chunking.overlap_chars must be < chunking.target_chars")
        if c.min_chunk_chars > c.target_chars:
            raise ValueError("chunking.min_chunk_chars must be <= chunking.target_chars")
        if self.qdrant.distance != "Cosine":
            raise ValueError("qdrant.distance must be Cosine")
        return self


def load_config(path: str | Path = "config.yaml") -> AppConfig:
    cfg_path = Path(path)
    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    config = AppConfig.model_validate(raw)
    if config.qdrant.vector_size != 384:
        raise ValueError("qdrant.vector_size must match intfloat/e5-small-v2 output dimension (384)")
    return config
