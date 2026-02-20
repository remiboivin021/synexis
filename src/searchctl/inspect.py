from __future__ import annotations

from pathlib import Path

from searchctl.metadata.db import MetadataDB


def inspect_chunk(db: MetadataDB, cache_dir: str, chunk_id: str) -> dict | None:
    row = db.fetch_chunk(chunk_id)
    if not row:
        return None
    doc_id = row["doc_id"]
    text_path = Path(cache_dir) / f"{doc_id}.txt"
    full_text = text_path.read_text(encoding="utf-8") if text_path.exists() else ""
    start = row["start_char"]
    end = row["end_char"]
    return {
        "chunk_id": row["chunk_id"],
        "doc_id": doc_id,
        "path": row["path"],
        "title": row["title"],
        "start_char": start,
        "end_char": end,
        "text": full_text[start:end],
    }
