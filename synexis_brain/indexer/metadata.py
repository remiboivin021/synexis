from __future__ import annotations

import sqlite3
from typing import Any


def connect_meta(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_meta_tables(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS file_meta (
          vault_id TEXT NOT NULL,
          path TEXT NOT NULL,
          mtime REAL NOT NULL,
          size INTEGER NOT NULL,
          file_hash TEXT NOT NULL,
          last_indexed TEXT NOT NULL,
          PRIMARY KEY (vault_id, path)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS chunk_meta (
          chunk_id TEXT PRIMARY KEY,
          vault_id TEXT NOT NULL,
          path TEXT NOT NULL,
          heading TEXT NOT NULL,
          chunk_hash TEXT NOT NULL,
          updated TEXT NOT NULL
        )
        """
    )
    conn.commit()


def get_file_meta(conn: sqlite3.Connection, vault_id: str, path: str) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT vault_id, path, mtime, size, file_hash, last_indexed FROM file_meta WHERE vault_id = ? AND path = ?",
        (vault_id, path),
    ).fetchone()
    return dict(row) if row else None


def list_file_meta(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute("SELECT vault_id, path FROM file_meta").fetchall()
    return [dict(row) for row in rows]


def upsert_file_meta(
    conn: sqlite3.Connection,
    vault_id: str,
    path: str,
    mtime: float,
    size: int,
    file_hash: str,
    last_indexed: str,
) -> None:
    conn.execute(
        """
        INSERT INTO file_meta (vault_id, path, mtime, size, file_hash, last_indexed)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(vault_id, path)
        DO UPDATE SET
          mtime = excluded.mtime,
          size = excluded.size,
          file_hash = excluded.file_hash,
          last_indexed = excluded.last_indexed
        """,
        (vault_id, path, mtime, size, file_hash, last_indexed),
    )


def delete_file_meta(conn: sqlite3.Connection, vault_id: str, path: str) -> None:
    conn.execute("DELETE FROM file_meta WHERE vault_id = ? AND path = ?", (vault_id, path))


def upsert_chunk_meta(
    conn: sqlite3.Connection,
    chunk_id: str,
    vault_id: str,
    path: str,
    heading: str,
    chunk_hash: str,
    updated: str,
) -> None:
    conn.execute(
        """
        INSERT INTO chunk_meta (chunk_id, vault_id, path, heading, chunk_hash, updated)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(chunk_id)
        DO UPDATE SET
          heading = excluded.heading,
          chunk_hash = excluded.chunk_hash,
          updated = excluded.updated
        """,
        (chunk_id, vault_id, path, heading, chunk_hash, updated),
    )


def delete_chunks_for_file(conn: sqlite3.Connection, vault_id: str, path: str) -> None:
    conn.execute("DELETE FROM chunk_meta WHERE vault_id = ? AND path = ?", (vault_id, path))
