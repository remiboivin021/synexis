from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import Any

from synexis_brain.config import load_config
from synexis_brain.indexer.incremental import apply_incremental_index
from synexis_brain.indexer.metadata import connect_meta, ensure_meta_tables
from synexis_brain.indexer.pipeline import run_dot_file
from synexis_brain.indexer.scan import scan_vaults
from synexis_brain.search.bm25 import SQLiteBm25Index


@dataclass
class SearchFilters:
    vault_id: str = ""
    chunk_type: str = ""
    tag: str = ""
    status: str = ""


class SearchService:
    def __init__(self, db_path: str, config_path: str) -> None:
        self.db_path = db_path
        self.config_path = config_path
        self.config = load_config(config_path)
        self.vault_paths = {str(v["id"]): Path(str(v["path"])) for v in self.config.get("vaults", [])}
        self.conn = connect_meta(db_path)
        ensure_meta_tables(self.conn)
        self.bm25 = SQLiteBm25Index(self.conn)

    def reindex(self) -> dict[str, Any]:
        ctx = {
            "config_path": self.config_path,
            "db_path": self.db_path,
            "db_conn": self.conn,
        }

        # Keep execution through the pipeline runner contract.
        out = run_dot_file(
            path=Path("synexis_brain/pipelines/index.dot"),
            registry={
                "scan_vaults": scan_vaults,
                "apply_incremental_index": apply_incremental_index,
            },
            context=ctx,
        )
        return out.get("changes", {})

    def search(self, query: str, filters: SearchFilters, limit: int = 50) -> list[dict[str, Any]]:
        if not query.strip():
            return []

        rows = self.conn.execute(
            """
            SELECT chunk_id, vault_id, path, heading,
                   snippet(bm25_chunks, 4, '[', ']', '...', 16) AS preview,
                   bm25(bm25_chunks) AS score,
                   tags, type, status
            FROM bm25_chunks
            WHERE bm25_chunks MATCH ?
              AND (? = '' OR vault_id = ?)
              AND (? = '' OR type = ?)
              AND (? = '' OR status = ?)
              AND (? = '' OR tags LIKE ?)
            ORDER BY score
            LIMIT ?
            """,
            (
                query,
                filters.vault_id,
                filters.vault_id,
                filters.chunk_type,
                filters.chunk_type,
                filters.status,
                filters.status,
                filters.tag,
                f"%{filters.tag}%" if filters.tag else "",
                limit,
            ),
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

    def citation_for(self, result: dict[str, Any]) -> str:
        heading = result.get("heading") or ""
        if heading:
            return f"[[{result['path']}#{heading}]]"
        return f"[[{result['path']}]]"

    def open_note_path(self, result: dict[str, Any]) -> str:
        vault_root = self.vault_paths.get(result["vault_id"])
        if vault_root is None:
            return result["path"]
        return str((vault_root / result["path"]).resolve())
