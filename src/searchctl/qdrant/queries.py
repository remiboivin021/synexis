from __future__ import annotations

from qdrant_client import QdrantClient


def vector_search(client: QdrantClient, collection_name: str, query_vector: list[float], top_k: int, source_type: str | None, path_contains: str | None) -> list[dict]:
    _ = source_type
    _ = path_contains
    rows = client.search(collection_name=collection_name, query_vector=query_vector, limit=top_k, with_payload=True)
    return [dict(r.payload or {}) for r in rows]
