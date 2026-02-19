from __future__ import annotations

import logging
import sqlite3
from typing import Any

from synexis_brain.search.bm25 import SQLiteBm25Index
from synexis_brain.search.bm25_tantivy import TantivyBm25Index, TantivyConfig


def build_bm25_backend(config: dict[str, Any], conn: sqlite3.Connection):
    search_cfg = config.get("search", {}) if isinstance(config.get("search", {}), dict) else {}
    backend = str(search_cfg.get("bm25_backend", "tantivy")).strip().lower()

    if backend == "tantivy":
        index_dir = str(search_cfg.get("tantivy_index_dir", "data/tantivy"))
        try:
            return TantivyBm25Index(TantivyConfig(index_dir=index_dir))
        except RuntimeError as exc:
            logging.getLogger("synexis.search").warning("%s; fallback to sqlite bm25", exc)
            return SQLiteBm25Index(conn)

    return SQLiteBm25Index(conn)
