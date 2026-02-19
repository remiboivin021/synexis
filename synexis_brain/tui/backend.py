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
from synexis_brain.search.backends import build_bm25_backend


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
        self.bm25 = build_bm25_backend(self.config, self.conn)

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
            context={**ctx, "bm25_backend": self.bm25},
        )
        return out.get("changes", {})

    def search(self, query: str, filters: SearchFilters, limit: int = 50) -> list[dict[str, Any]]:
        if not query.strip():
            return []

        results = self.bm25.topk(query=query, limit=limit)
        out: list[dict[str, Any]] = []
        for row in results:
            if filters.vault_id and row.get("vault_id") != filters.vault_id:
                continue
            if filters.chunk_type and row.get("type") != filters.chunk_type:
                continue
            if filters.status and row.get("status") != filters.status:
                continue
            if filters.tag and filters.tag not in str(row.get("tags", "")):
                continue
            out.append(row)
        return out

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
