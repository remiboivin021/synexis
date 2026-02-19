from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
from typing import Any

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")


@dataclass(frozen=True)
class ParsedMarkdown:
    frontmatter: dict[str, Any]
    body_lines: list[str]


def parse_md(path: str | Path) -> ParsedMarkdown:
    raw = Path(path).read_text(encoding="utf-8")
    lines = raw.splitlines()

    frontmatter: dict[str, Any] = {}
    if lines and lines[0].strip() == "---":
        try:
            end = lines[1:].index("---") + 1
        except ValueError:
            end = -1
        if end > 0:
            for line in lines[1:end]:
                if ":" in line:
                    key, value = line.split(":", 1)
                    frontmatter[key.strip()] = value.strip()
            lines = lines[end + 1 :]

    return ParsedMarkdown(frontmatter=frontmatter, body_lines=lines)


def chunk_by_heading(vault_id: str, rel_path: str, parsed: ParsedMarkdown) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    current_heading = ""
    current_level = 0
    bucket: list[str] = []

    def flush() -> None:
        nonlocal bucket, current_heading, current_level
        text = "\n".join(bucket).strip()
        if not text:
            bucket = []
            return
        text_hash = hashlib.sha1(text.encode("utf-8")).hexdigest()
        chunk_id = hashlib.sha1(f"{vault_id}|{rel_path}|{current_heading}|{text_hash}".encode("utf-8")).hexdigest()
        chunks.append(
            {
                "chunk_id": chunk_id,
                "vault_id": vault_id,
                "path": rel_path,
                "heading": current_heading,
                "level": current_level,
                "text": text,
                "chunk_hash": text_hash,
                "tags": parsed.frontmatter.get("tags", ""),
                "type": parsed.frontmatter.get("type", ""),
                "status": parsed.frontmatter.get("status", ""),
            }
        )
        bucket = []

    for line in parsed.body_lines:
        match = _HEADING_RE.match(line)
        if match:
            flush()
            current_level = len(match.group(1))
            current_heading = match.group(2).strip()
            continue
        bucket.append(line)

    flush()
    return chunks
