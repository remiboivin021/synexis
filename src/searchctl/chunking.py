from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Chunk:
    ordinal: int
    text: str
    start_char: int
    end_char: int
    heading_path: str | None = None


def split_into_chunks(text: str, target_chars: int, overlap_chars: int, min_chunk_chars: int) -> list[Chunk]:
    if not text:
        return []
    chunks: list[Chunk] = []
    start = 0
    ordinal = 0
    n = len(text)
    while start < n:
        end = min(start + target_chars, n)
        piece = text[start:end]
        if len(piece) < min_chunk_chars and ordinal > 0:
            break
        chunks.append(Chunk(ordinal=ordinal, text=piece, start_char=start, end_char=end))
        ordinal += 1
        if end == n:
            break
        start = max(0, end - overlap_chars)
    if len(chunks) == 1 and len(chunks[0].text) < min_chunk_chars:
        return chunks
    return chunks
