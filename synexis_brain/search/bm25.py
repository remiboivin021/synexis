from __future__ import annotations

import re
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

    def is_empty(self) -> bool:
        row = self.conn.execute("SELECT COUNT(*) FROM bm25_chunks").fetchone()
        if row is None:
            return True
        return int(row[0]) == 0

    def delete_file(self, vault_id: str, path: str) -> None:
        self.conn.execute("DELETE FROM bm25_chunks WHERE vault_id = ? AND path = ?", (vault_id, path))
        self.conn.commit()

    def topk(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        clauses = _build_fts_clauses(query)
        fts_query = _join_clauses(clauses, mode="and") or query
        rows = self._run_fts_query(fts_query, limit)
        if not rows:
            if len(clauses) > 1:
                rows = self._run_fts_query(clauses[0], limit)
            if not rows:
                fallback_or = _join_clauses(clauses, mode="or")
                if fallback_or and fallback_or != fts_query:
                    rows = self._run_fts_query(fallback_or, limit)
        if not rows and fts_query != query:
            rows = self._run_fts_query(query, limit)
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

    def _run_fts_query(self, query: str, limit: int) -> list[tuple[Any, ...]]:
        return self.conn.execute(
            """
            SELECT chunk_id, vault_id, path, heading, snippet(bm25_chunks, 4, '[', ']', '...', 16) AS preview, bm25(bm25_chunks) AS score, tags, type, status
            FROM bm25_chunks
            WHERE bm25_chunks MATCH ?
            ORDER BY score
            LIMIT ?
            """,
            (query, limit),
        ).fetchall()


def _build_fts_clauses(raw: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z0-9_]+", raw.lower())
    if not tokens:
        return []

    clauses: list[str] = []
    for token in tokens:
        variants = {token}
        if token.endswith("s") and len(token) > 4:
            variants.add(token[:-1])
        opts = [f"{v}*" for v in sorted(variants) if v]
        if not opts:
            continue
        clause = opts[0] if len(opts) == 1 else "(" + " OR ".join(opts) + ")"
        clauses.append(clause)
    return clauses


def _join_clauses(clauses: list[str], mode: str = "and") -> str:
    if not clauses:
        return ""
    if mode == "or":
        return " OR ".join(clauses)
    return " AND ".join(clauses)
