from __future__ import annotations

import re
from pathlib import Path


H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)


def extract_markdown(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    match = H1_RE.search(text)
    title = match.group(1).strip() if match else path.stem
    return text, title
