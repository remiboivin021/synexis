from __future__ import annotations

from langchain_core.documents import Document


def rerank_documents(docs: list[Document], question: str, top_n: int) -> list[Document]:
    if not docs:
        return []

    q_terms = set(question.lower().split())
    ranked = sorted(
        docs,
        key=lambda d: _overlap_score(d.page_content, q_terms),
        reverse=True,
    )
    return ranked[:top_n]


def _overlap_score(text: str, q_terms: set[str]) -> int:
    if not q_terms:
        return 0
    words = set(text.lower().split())
    return len(words & q_terms)
