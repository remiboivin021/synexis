from __future__ import annotations

import logging

from langchain_core.documents import Document

from rag.config import RagConfig
from rag.embeddings.factory import build_embeddings
from rag.retrieval.rerank import rerank_documents
from rag.retrieval.rewrite import rewrite_question
from rag.vectorstore.factory import build_vectorstore

LOG = logging.getLogger("rag.retrieval")


def retrieve_documents(
    config: RagConfig,
    question: str,
    filters: dict | None = None,
) -> tuple[list[Document], dict]:
    filters = filters or {}
    embeddings = build_embeddings(config)
    vectorstore = build_vectorstore(config, embeddings)

    rewritten = rewrite_question(question, config)
    retrieval_query = rewritten.get("search_query") or question

    search_kwargs: dict = {
        "k": config.retrieval_k,
        "filter": _build_filter(filters),
    }

    docs_with_scores: list[tuple[Document, float]]
    if config.search_type == "mmr":
        mmr_kwargs = {
            "k": config.retrieval_k,
            "fetch_k": config.fetch_k,
            "lambda_mult": 0.5,
            "filter": _build_filter(filters),
        }
        docs = vectorstore.max_marginal_relevance_search(retrieval_query, **mmr_kwargs)
        docs_with_scores = [(doc, float(doc.metadata.get("score", 0.0) or 0.0)) for doc in docs]
    else:
        docs_with_scores = vectorstore.similarity_search_with_relevance_scores(
            retrieval_query,
            k=config.retrieval_k,
            filter=_build_filter(filters),
        )

    docs = [doc for doc, _ in docs_with_scores]
    scores = [float(score) for _, score in docs_with_scores]

    if config.enable_rerank:
        docs = rerank_documents(docs, question, top_n=config.rerank_top_n)

    LOG.info(
        "query.retrieve question=%s rewritten=%s docs=%s",
        question,
        retrieval_query,
        len(docs),
    )

    debug = {
        "question": question,
        "rewritten_query": retrieval_query,
        "filters": filters,
        "search_type": config.search_type,
        "retrieved": [
            {
                "doc_id": doc.metadata.get("doc_id"),
                "chunk_id": doc.metadata.get("chunk_id"),
                "source": doc.metadata.get("source"),
                "score": scores[idx] if idx < len(scores) else None,
            }
            for idx, doc in enumerate(docs)
        ],
    }
    return docs, debug


def _build_filter(filters: dict) -> dict | None:
    allowed = {"tenant_id", "doc_id", "source"}
    clean = {k: v for k, v in (filters or {}).items() if k in allowed and v is not None}
    return clean or None
