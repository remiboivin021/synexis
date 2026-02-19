from __future__ import annotations

import sqlite3
from typing import Any


class SQLiteBm25Index:
    """Bootstrap BM25-like search using SQLite FTS5 until Tantivy integration."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn
        self.conn.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS bm25_chunks
            USING fts5(chunk_id UNINDEXED, vault_id UNINDEXED, path UNINDEXED, heading, text, tags, type, status)
            """
        )
        self.conn.commit()

    def upsert_chunks(self, chunks: list[dict[str, Any]]) -> None:
        for chunk in chunks:
            self.conn.execute("DELETE FROM bm25_chunks WHERE chunk_id = ?", (chunk["chunk_id"],))
            self.conn.execute(
                """
                INSERT INTO bm25_chunks (chunk_id, vault_id, path, heading, text, tags, type, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chunk["chunk_id"],
                    chunk["vault_id"],
                    chunk["path"],
                    chunk.get("heading", ""),
                    chunk.get("text", ""),
                    str(chunk.get("tags", "")),
                    str(chunk.get("type", "")),
                    str(chunk.get("status", "")),
                ),
            )
        self.conn.commit()

    def delete_file(self, vault_id: str, path: str) -> None:
        self.conn.execute("DELETE FROM bm25_chunks WHERE vault_id = ? AND path = ?", (vault_id, path))
        self.conn.commit()

    def topk(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT chunk_id, vault_id, path, heading, snippet(bm25_chunks, 4, '[', ']', '...', 16) AS preview, bm25(bm25_chunks) AS score, tags, type, status
            FROM bm25_chunks
            WHERE bm25_chunks MATCH ?
            ORDER BY score
            LIMIT ?
            """,
            (query, limit),
        ).fetchall()
        return [
            {
                "chunk_id": row[0],
                "vault_id": row[1],
                "path": row[2],
                    "heading": row[3],
                    "preview": row[4],
                    "score": row[5],
                    "tags": row[6],
                    "type": row[7],
                    "status": row[8],
                }
            for row in rows
        ]
