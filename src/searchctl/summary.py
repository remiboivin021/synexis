from __future__ import annotations

import re
from typing import Any


def collect_sources(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    sources: list[dict[str, Any]] = []
    for row in rows:
        citation = row.get("citation", {})
        chunk_id = str(citation.get("chunk_id") or "")
        if not chunk_id or chunk_id in seen:
            continue
        seen.add(chunk_id)
        sources.append(
            {
                "rank": row.get("rank"),
                "doc_path": row.get("doc_path"),
                "doc_title": row.get("doc_title"),
                "chunk_id": chunk_id,
                "start_char": citation.get("start_char"),
                "end_char": citation.get("end_char"),
            }
        )
    return sources


def format_sources(sources: list[dict[str, Any]]) -> str:
    if not sources:
        return "Sources: (aucune)"
    lines = ["Sources", ""]
    for i, src in enumerate(sources, start=1):
        lines.append(
            f'{i}. {src.get("doc_title") or "(untitled)"} | {src.get("doc_path")} '
            f'| chunk={src.get("chunk_id")} [{src.get("start_char")}:{src.get("end_char")}]'
        )
    return "\n".join(lines)


def summary_input_rows(rows: list[dict[str, Any]], top_n: int) -> list[dict[str, Any]]:
    out = []
    for i, row in enumerate(rows[:top_n], start=1):
        out.append(
            {
                "source_id": f"S{i}",
                "rank": row.get("rank"),
                "doc_title": row.get("doc_title"),
                "doc_path": row.get("doc_path"),
                "snippet": row.get("snippet"),
                "citation": row.get("citation"),
            }
        )
    return out


def is_strictly_grounded_summary(summary: str, allowed_source_ids: list[str]) -> bool:
    if not summary.strip():
        return False
    if not allowed_source_ids:
        return False
    cited = set(re.findall(r"\[(S\d+)\]", summary))
    if not cited:
        return False
    allowed = set(allowed_source_ids)
    return cited.issubset(allowed)
