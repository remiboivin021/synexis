from __future__ import annotations

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
    for row in rows[:top_n]:
        out.append(
            {
                "rank": row.get("rank"),
                "doc_title": row.get("doc_title"),
                "doc_path": row.get("doc_path"),
                "snippet": row.get("snippet"),
                "citation": row.get("citation"),
            }
        )
    return out
