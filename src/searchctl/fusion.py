from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RankedChunk:
    chunk_id: str
    payload: dict
    bm25_rank: int | None = None
    vector_rank: int | None = None
    score: float = 0.0


def rrf_fuse(bm25_results: list[dict], vector_results: list[dict], rrf_k: int) -> list[RankedChunk]:
    merged: dict[str, RankedChunk] = {}

    for i, hit in enumerate(bm25_results, start=1):
        cid = hit["chunk_id"]
        row = merged.setdefault(cid, RankedChunk(chunk_id=cid, payload=hit, bm25_rank=i))
        row.bm25_rank = i
        row.score += 1.0 / (rrf_k + i)

    for i, hit in enumerate(vector_results, start=1):
        cid = hit["chunk_id"]
        row = merged.setdefault(cid, RankedChunk(chunk_id=cid, payload=hit, vector_rank=i))
        row.vector_rank = i
        if not row.payload:
            row.payload = hit
        row.score += 1.0 / (rrf_k + i)

    return sorted(
        merged.values(),
        key=lambda r: (
            -r.score,
            r.bm25_rank if r.bm25_rank is not None else 10**9,
            r.vector_rank if r.vector_rank is not None else 10**9,
            r.chunk_id,
        ),
    )
