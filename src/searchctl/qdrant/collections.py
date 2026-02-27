from __future__ import annotations

from uuid import NAMESPACE_URL, uuid4, uuid5

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


def qdrant_point_id(chunk_id: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"searchctl:{chunk_id}"))


def upsert_vectors(client: QdrantClient, collection_name: str, vectors: list[list[float]], payloads: list[dict]) -> None:
    points = [
        models.PointStruct(id=qdrant_point_id(payload["chunk_id"]), vector=vec, payload=payload)
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


def probe_collection_write(client: QdrantClient, collection_name: str, vector_size: int) -> None:
    probe_id = str(uuid4())
    client.upsert(
        collection_name=collection_name,
        points=[models.PointStruct(id=probe_id, vector=[0.0] * vector_size, payload={"_probe": True})],
        wait=True,
    )
    client.delete(
        collection_name=collection_name,
        points_selector=models.PointIdsList(points=[probe_id]),
        wait=True,
    )
