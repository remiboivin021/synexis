from __future__ import annotations

import hashlib
import logging
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
    def __init__(
        self,
        conn: sqlite3.Connection,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        backend: str = "hash",
    ) -> None:
        self.conn = conn
        self.model_name = model_name
        self.backend = backend
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
        self._query_cache: dict[str, list[float]] = {}

    def _model_or_none(self):
        if self.backend != "sentence-transformers":
            return None
        if self._model is not None:
            return self._model
        if self._model_unavailable:
            return None
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
        except ModuleNotFoundError:
            self._model_unavailable = True
            return None
        try:
            self._model = SentenceTransformer(self.model_name)
        except Exception:
            self._model_unavailable = True
            return None
        return self._model

    def embed_text(self, text: str) -> list[float]:
        key = text.strip()
        cached = self._query_cache.get(key)
        if cached is not None:
            return cached
        model = self._model_or_none()
        if model is None:
            vector = _hash_embedding(text)
        else:
            vector = model.encode([text])[0]
            vector = [float(x) for x in vector]
        self._query_cache[key] = vector
        if len(self._query_cache) > 256:
            self._query_cache.clear()
        return vector

    def embedding_for_chunk(self, chunk_hash: str, text: str) -> list[float]:
        return self.embeddings_for_chunks([{"chunk_hash": chunk_hash, "text": text}])[0]

    def embeddings_for_chunks(self, chunks: list[dict[str, Any]]) -> list[list[float]]:
        if not chunks:
            return []

        hashes = [str(chunk["chunk_hash"]) for chunk in chunks]
        placeholders = ",".join("?" for _ in hashes)
        cached_rows = self.conn.execute(
            f"SELECT chunk_hash, embedding FROM embedding_cache WHERE chunk_hash IN ({placeholders})",
            tuple(hashes),
        ).fetchall()
        cached = {row[0]: [float(x) for x in row[1].split(",") if x] for row in cached_rows}

        missing_hashes: list[str] = []
        missing_texts: list[str] = []
        for chunk in chunks:
            chunk_hash = str(chunk["chunk_hash"])
            if chunk_hash not in cached:
                missing_hashes.append(chunk_hash)
                missing_texts.append(str(chunk.get("text", "")))

        generated: dict[str, list[float]] = {}
        if missing_hashes:
            model = self._model_or_none()
            if model is None:
                vectors = [_hash_embedding(text) for text in missing_texts]
            else:
                encoded = model.encode(missing_texts, batch_size=32, show_progress_bar=False)
                vectors = [[float(v) for v in row] for row in encoded]

            payload = []
            for chunk_hash, vector in zip(missing_hashes, vectors):
                generated[chunk_hash] = vector
                payload.append((chunk_hash, ",".join(repr(float(x)) for x in vector)))
            self.conn.executemany(
                "INSERT OR REPLACE INTO embedding_cache (chunk_hash, embedding) VALUES (?, ?)",
                payload,
            )
            self.conn.commit()

        out: list[list[float]] = []
        for chunk in chunks:
            chunk_hash = str(chunk["chunk_hash"])
            out.append(cached.get(chunk_hash) or generated[chunk_hash])
        return out

    def _legacy_embedding_for_chunk(self, chunk_hash: str, text: str) -> list[float]:
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
        self.log = logging.getLogger("synexis.search.vector")
        self.client = None
        if self.enabled and self.prefer_qdrant:
            try:
                from qdrant_client import QdrantClient  # type: ignore
            except ModuleNotFoundError:
                self.client = None
            else:
                try:
                    self.client = QdrantClient(url=self.url, timeout=2.0, check_compatibility=False)
                    self.client.get_collections()
                    self.mode = "qdrant"
                except Exception as exc:
                    self.client = None
                    self.mode = "sqlite"
                    self.log.warning("Qdrant unavailable at %s: %s; fallback sqlite vector store", self.url, exc)

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
        self._sqlite_cache: list[tuple[list[float], dict[str, Any]]] | None = None

    def _invalidate_sqlite_cache(self) -> None:
        self._sqlite_cache = None

    def _load_sqlite_cache(self) -> list[tuple[list[float], dict[str, Any]]]:
        if self._sqlite_cache is not None:
            return self._sqlite_cache
        rows = self.conn.execute(
            "SELECT chunk_id, vault_id, path, heading, tags, type, status, text, embedding FROM vector_chunks"
        ).fetchall()
        cache: list[tuple[list[float], dict[str, Any]]] = []
        for row in rows:
            vec = [float(x) for x in row[8].split(",") if x]
            payload = {
                "chunk_id": row[0],
                "vault_id": row[1],
                "path": row[2],
                "heading": row[3],
                "tags": row[4],
                "type": row[5],
                "status": row[6],
                "preview": row[7][:240],
            }
            cache.append((vec, payload))
        self._sqlite_cache = cache
        return cache

    def upsert(self, chunks: list[dict[str, Any]], vectors: list[list[float]]) -> None:
        if not self.enabled:
            return
        if self.mode == "qdrant" and self.client is not None:
            try:
                self._qdrant_upsert(chunks, vectors)
                return
            except Exception as exc:
                self.log.warning("Qdrant upsert failed: %s; fallback sqlite vector store", exc)
                self.mode = "sqlite"

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
        self._invalidate_sqlite_cache()

    def delete_file(self, vault_id: str, path: str) -> None:
        if self.mode == "qdrant" and self.client is not None:
            try:
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
            except Exception as exc:
                self.log.warning("Qdrant delete failed: %s; fallback sqlite vector store", exc)
                self.mode = "sqlite"
        self.conn.execute("DELETE FROM vector_chunks WHERE vault_id = ? AND path = ?", (vault_id, path))
        self.conn.commit()
        self._invalidate_sqlite_cache()

    def topk(self, query_vector: list[float], limit: int = 20) -> list[dict[str, Any]]:
        if not self.enabled:
            return []
        if self.mode == "qdrant" and self.client is not None:
            try:
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
            except Exception as exc:
                self.log.warning("Qdrant search failed: %s; fallback sqlite vector store", exc)
                self.mode = "sqlite"

        scored: list[dict[str, Any]] = []
        for vec, payload in self._load_sqlite_cache():
            score = _cosine(query_vector, vec)
            scored.append(
                {
                    **payload,
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

        if not vectors:
            return

        self._ensure_qdrant_collection(vector_size=len(vectors[0]), distance=Distance.COSINE, vector_params=VectorParams)

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

    def _ensure_qdrant_collection(self, vector_size: int, distance: Any, vector_params: Any) -> None:
        if self.client is None:
            return
        try:
            self.client.get_collection(self.collection)
        except Exception:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=vector_params(size=vector_size, distance=distance),
            )


def _hash_embedding(text: str, dim: int = 64) -> list[float]:
    digest = hashlib.sha1(text.encode("utf-8")).digest()
    values: list[float] = []
    for i in range(dim):
        byte = digest[i % len(digest)]
        values.append((byte / 255.0) * 2.0 - 1.0)
    return values
