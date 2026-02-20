from __future__ import annotations

from pathlib import Path


def extract_text(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return text, path.stem
