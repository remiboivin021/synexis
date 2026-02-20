from __future__ import annotations

from qdrant_client import QdrantClient
from qdrant_client.http import models


def ensure_collection(client: QdrantClient, name: str, vector_size: int, distance: str) -> None:
    existing = {c.name for c in client.get_collections().collections}
    if name in existing:
        return
    client.create_collection(
        collection_name=name,
        vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
    )


def upsert_vectors(client: QdrantClient, collection_name: str, vectors: list[list[float]], payloads: list[dict]) -> None:
    points = [
        models.PointStruct(id=payload["chunk_id"], vector=vec, payload=payload)
        for vec, payload in zip(vectors, payloads, strict=True)
    ]
    if points:
        client.upsert(collection_name=collection_name, points=points, wait=True)


def delete_doc_vectors(client: QdrantClient, collection_name: str, doc_id: str) -> None:
    client.delete(
        collection_name=collection_name,
        points_selector=models.FilterSelector(filter=models.Filter(must=[models.FieldCondition(key="doc_id", match=models.MatchValue(value=doc_id))])),
        wait=True,
    )
