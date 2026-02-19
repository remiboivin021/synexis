from __future__ import annotations

import sqlite3
from typing import Any

from synexis_brain.indexer.markdown import chunk_by_heading, parse_md
from synexis_brain.indexer.metadata import (
    delete_chunks_for_file,
    delete_file_meta,
    upsert_chunk_meta,
    upsert_file_meta,
)
from synexis_brain.search.bm25 import SQLiteBm25Index


def apply_incremental_index(context: dict[str, Any], params: dict[str, str]) -> dict[str, Any]:
    conn: sqlite3.Connection = context["db_conn"]
    bm25 = context.get("bm25_backend") or SQLiteBm25Index(conn)
    chunks_out: list[dict[str, Any]] = []
    force_bm25_bootstrap = isinstance(bm25, SQLiteBm25Index) and bm25.is_empty()

    for item in context.get("scan_items", []):
        action = item["action"]
        if action == "unchanged" and not force_bm25_bootstrap:
            continue

        delete_chunks_for_file(conn, item["vault_id"], item["path"])
        parsed = parse_md(item["abs_path"])
        chunks = chunk_by_heading(item["vault_id"], item["path"], parsed)
        bm25.upsert_chunks(chunks)

        for chunk in chunks:
            upsert_chunk_meta(
                conn,
                chunk_id=chunk["chunk_id"],
                vault_id=item["vault_id"],
                path=item["path"],
                heading=chunk["heading"],
                chunk_hash=chunk["chunk_hash"],
                updated=item["last_indexed"],
            )

        upsert_file_meta(
            conn,
            vault_id=item["vault_id"],
            path=item["path"],
            mtime=item["mtime"],
            size=item["size"],
            file_hash=item["file_hash"],
            last_indexed=item["last_indexed"],
        )
        chunks_out.extend(chunks)

    for deleted in context.get("changes", {}).get("deleted", []):
        bm25.delete_file(deleted["vault_id"], deleted["path"])
        delete_chunks_for_file(conn, deleted["vault_id"], deleted["path"])
        delete_file_meta(conn, deleted["vault_id"], deleted["path"])

    conn.commit()
    return {"chunks": chunks_out}
