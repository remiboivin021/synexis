from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from rag.config import RagConfig
from rag.generation.chain import answer_question
from rag.ingestion.pipeline import ingest_path
from rag.retrieval.retriever import retrieve_documents


class QueryRequest(BaseModel):
    question: str
    filters: dict = Field(default_factory=dict)
    debug: bool = True


class IngestRequest(BaseModel):
    path: str
    tenant_id: str | None = None


def create_app(config: RagConfig | None = None) -> FastAPI:
    cfg = config or RagConfig.from_env()
    app = FastAPI(title="rag-langchain")

    @app.post("/query")
    def query(payload: QueryRequest):
        docs, retrieval_debug = retrieve_documents(cfg, payload.question, filters=payload.filters)
        return answer_question(cfg, payload.question, docs, retrieval_debug=retrieval_debug)

    @app.post("/ingest")
    def ingest(payload: IngestRequest):
        return ingest_path(cfg, payload.path, tenant_id=payload.tenant_id)

    return app
