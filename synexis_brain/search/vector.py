from __future__ import annotations

import hashlib
import math
import sqlite3
from typing import Any


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class EmbeddingService:
    def __init__(self, conn: sqlite3.Connection, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        self.conn = conn
        self.model_name = model_name
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS embedding_cache (
              chunk_hash TEXT PRIMARY KEY,
              embedding TEXT NOT NULL
            )
            """
        )
        self.conn.commit()
        self._model: Any = None
        self._model_unavailable = False

    def _model_or_none(self):
        if self._model is not None:
            return self._model
        if self._model_unavailable:
            return None
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
        except ModuleNotFoundError:
            self._model_unavailable = True
            return None
        self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed_text(self, text: str) -> list[float]:
        model = self._model_or_none()
        if model is None:
            return _hash_embedding(text)
        vector = model.encode([text])[0]
        return [float(x) for x in vector]

    def embedding_for_chunk(self, chunk_hash: str, text: str) -> list[float]:
        row = self.conn.execute(
            "SELECT embedding FROM embedding_cache WHERE chunk_hash = ?", (chunk_hash,)
        ).fetchone()
        if row:
            return [float(x) for x in row[0].split(",") if x]

        vector = self.embed_text(text)
        payload = ",".join(repr(float(x)) for x in vector)
        self.conn.execute(
            "INSERT OR REPLACE INTO embedding_cache (chunk_hash, embedding) VALUES (?, ?)",
            (chunk_hash, payload),
        )
        self.conn.commit()
        return vector


class VectorStore:
    def __init__(self, conn: sqlite3.Connection, config: dict[str, Any]) -> None:
        self.conn = conn
        vector_cfg = config.get("vector", {}) if isinstance(config.get("vector", {}), dict) else {}
        self.enabled = bool(vector_cfg.get("enabled", True))
        self.collection = str(vector_cfg.get("collection", "synexis_chunks"))
        self.url = str(vector_cfg.get("qdrant_url", "http://localhost:6333"))
        self.prefer_qdrant = bool(vector_cfg.get("prefer_qdrant", True))

        self.mode = "sqlite"
        self.client = None
        if self.enabled and self.prefer_qdrant:
            try:
                from qdrant_client import QdrantClient  # type: ignore
            except ModuleNotFoundError:
                self.client = None
            else:
                self.client = QdrantClient(url=self.url)
                self.mode = "qdrant"

        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS vector_chunks (
              chunk_id TEXT PRIMARY KEY,
              vault_id TEXT NOT NULL,
              path TEXT NOT NULL,
              heading TEXT NOT NULL,
              tags TEXT NOT NULL,
              type TEXT NOT NULL,
              status TEXT NOT NULL,
              text TEXT NOT NULL,
              embedding TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def upsert(self, chunks: list[dict[str, Any]], vectors: list[list[float]]) -> None:
        if not self.enabled:
            return
        if self.mode == "qdrant" and self.client is not None:
            self._qdrant_upsert(chunks, vectors)
            return

        for chunk, vector in zip(chunks, vectors):
            self.conn.execute(
                """
                INSERT OR REPLACE INTO vector_chunks
                  (chunk_id, vault_id, path, heading, tags, type, status, text, embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chunk["chunk_id"],
                    chunk["vault_id"],
                    chunk["path"],
                    chunk.get("heading", ""),
                    str(chunk.get("tags", "")),
                    str(chunk.get("type", "")),
                    str(chunk.get("status", "")),
                    str(chunk.get("text", "")),
                    ",".join(f"{v:.8f}" for v in vector),
                ),
            )
        self.conn.commit()

    def delete_file(self, vault_id: str, path: str) -> None:
        if self.mode == "qdrant" and self.client is not None:
            self.client.delete(
                collection_name=self.collection,
                points_selector={
                    "filter": {
                        "must": [
                            {"key": "vault_id", "match": {"value": vault_id}},
                            {"key": "path", "match": {"value": path}},
                        ]
                    }
                },
            )
            return
        self.conn.execute("DELETE FROM vector_chunks WHERE vault_id = ? AND path = ?", (vault_id, path))
        self.conn.commit()

    def topk(self, query_vector: list[float], limit: int = 20) -> list[dict[str, Any]]:
        if not self.enabled:
            return []
        if self.mode == "qdrant" and self.client is not None:
            points = self.client.search(
                collection_name=self.collection,
                query_vector=query_vector,
                limit=limit,
                with_payload=True,
            )
            out: list[dict[str, Any]] = []
            for point in points:
                payload = point.payload or {}
                out.append(
                    {
                        "chunk_id": payload.get("chunk_id", ""),
                        "vault_id": payload.get("vault_id", ""),
                        "path": payload.get("path", ""),
                        "heading": payload.get("heading", ""),
                        "preview": str(payload.get("text", ""))[:240],
                        "score": float(point.score),
                        "tags": payload.get("tags", ""),
                        "type": payload.get("type", ""),
                        "status": payload.get("status", ""),
                    }
                )
            return out

        rows = self.conn.execute(
            "SELECT chunk_id, vault_id, path, heading, tags, type, status, text, embedding FROM vector_chunks"
        ).fetchall()
        scored: list[dict[str, Any]] = []
        for row in rows:
            vec = [float(x) for x in row[8].split(",") if x]
            score = _cosine(query_vector, vec)
            scored.append(
                {
                    "chunk_id": row[0],
                    "vault_id": row[1],
                    "path": row[2],
                    "heading": row[3],
                    "tags": row[4],
                    "type": row[5],
                    "status": row[6],
                    "preview": row[7][:240],
                    "score": score,
                }
            )
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:limit]

    def _qdrant_upsert(self, chunks: list[dict[str, Any]], vectors: list[list[float]]) -> None:
        if self.client is None:
            return
        try:
            from qdrant_client.http.models import Distance, PointStruct, VectorParams  # type: ignore
        except ModuleNotFoundError:
            return

        if vectors:
            self.client.recreate_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=len(vectors[0]), distance=Distance.COSINE),
            )

        points = []
        for chunk, vector in zip(chunks, vectors):
            payload = {
                "chunk_id": chunk["chunk_id"],
                "vault_id": chunk["vault_id"],
                "path": chunk["path"],
                "heading": chunk.get("heading", ""),
                "tags": str(chunk.get("tags", "")),
                "type": str(chunk.get("type", "")),
                "status": str(chunk.get("status", "")),
                "text": str(chunk.get("text", "")),
            }
            points.append(PointStruct(id=chunk["chunk_id"], vector=vector, payload=payload))
        if points:
            self.client.upsert(collection_name=self.collection, points=points)


def _hash_embedding(text: str, dim: int = 64) -> list[float]:
    digest = hashlib.sha1(text.encode("utf-8")).digest()
    values: list[float] = []
    for i in range(dim):
        byte = digest[i % len(digest)]
        values.append((byte / 255.0) * 2.0 - 1.0)
    return values
