from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_abs_path(path: Path) -> str:
    p = str(path.resolve())
    if len(p) >= 2 and p[1] == ":":
        p = p[0].lower() + p[1:]
    return p.replace("\\", "/")


def make_doc_id(path: Path) -> str:
    return sha256_text("path:" + normalize_abs_path(path))


def make_chunk_id(doc_id: str, ordinal: int, chunk_text: str) -> str:
    chunk_text_hash = sha256_text(chunk_text)
    return sha256_text(f"{doc_id}:{ordinal}:{chunk_text_hash}")
