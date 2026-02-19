from __future__ import annotations

from typing import Any


def hybrid_merge(
    bm25_results: list[dict[str, Any]],
    vector_results: list[dict[str, Any]],
    w_bm25: float = 0.6,
    w_vector: float = 0.4,
    limit: int = 20,
) -> list[dict[str, Any]]:
    def normalize(scores: list[float], higher_is_better: bool = True) -> list[float]:
        if not scores:
            return []
        lo, hi = min(scores), max(scores)
        if hi == lo:
            return [1.0 for _ in scores]
        if higher_is_better:
            return [(s - lo) / (hi - lo) for s in scores]
        return [(hi - s) / (hi - lo) for s in scores]

    bm25_scores = [float(x.get("score", 0.0)) for x in bm25_results]
    vec_scores = [float(x.get("score", 0.0)) for x in vector_results]
    bm25_higher_is_better = any(score > 0 for score in bm25_scores)
    bm25_norm = normalize(bm25_scores, higher_is_better=bm25_higher_is_better)
    vec_norm = normalize(vec_scores, higher_is_better=True)

    merged: dict[str, dict[str, Any]] = {}

    for i, row in enumerate(bm25_results):
        cid = row["chunk_id"]
        merged[cid] = {**row, "bm25_score": bm25_norm[i], "vector_score": 0.0}

    for i, row in enumerate(vector_results):
        cid = row["chunk_id"]
        if cid not in merged:
            merged[cid] = {**row, "bm25_score": 0.0, "vector_score": vec_norm[i]}
        else:
            merged[cid]["vector_score"] = vec_norm[i]

    out: list[dict[str, Any]] = []
    for row in merged.values():
        row["score"] = w_bm25 * row["bm25_score"] + w_vector * row["vector_score"]
        out.append(row)

    out.sort(
        key=lambda x: (
            float(x.get("score", 0.0)),
            float(x.get("vector_score", 0.0)),
            float(x.get("bm25_score", 0.0)),
        ),
        reverse=True,
    )
    return out[:limit]
