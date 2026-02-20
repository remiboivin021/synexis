from __future__ import annotations


def build_snippet(text: str, highlight: str | None = None) -> str:
    if not text:
        return ""
    if highlight and highlight in text:
        idx = text.index(highlight)
        start = max(0, idx - 120)
        end = min(len(text), idx + len(highlight) + 120)
    else:
        start = 0
        end = min(len(text), 240)
    snippet = text[start:end].strip()
    if len(snippet) < 120 and len(text) >= 120:
        snippet = text[:120]
    if len(snippet) > 360:
        snippet = snippet[:360]
    return snippet
