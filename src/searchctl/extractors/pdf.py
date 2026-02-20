from __future__ import annotations

from pathlib import Path

import fitz
from pdfminer.high_level import extract_text as pdfminer_extract_text


def extract_pdf(path: Path) -> tuple[str, str]:
    text_parts: list[str] = []
    try:
        with fitz.open(path) as doc:
            for page in doc:
                text_parts.append(page.get_text("text"))
    except Exception:
        text_parts = [pdfminer_extract_text(str(path))]
    text = "\n".join(text_parts).strip()
    if len(text) < 50:
        raise ValueError("PDF_TEXT_EMPTY")
    return text, path.stem
