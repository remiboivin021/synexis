from __future__ import annotations

from rag.config import RagConfig


def rewrite_question(question: str, config: RagConfig) -> dict:
    if not config.enable_rewrite:
        return {"search_query": question, "subqueries": []}

    # Conservative baseline rewrite: normalize whitespace and emit single query.
    rewritten = " ".join(question.split())
    return {"search_query": rewritten, "subqueries": []}
