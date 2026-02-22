from __future__ import annotations

from pathlib import Path

from langchain_core.documents import Document

ALLOWED_EXTENSIONS = {".md", ".txt"}


def discover_local_files(root: Path, pattern: str = "**/*") -> list[Path]:
    if root.is_file():
        return [root]
    candidates = [p for p in root.glob(pattern) if p.is_file()]
    return sorted([p for p in candidates if p.suffix.lower() in ALLOWED_EXTENSIONS])


def load_local_documents(paths: list[Path], tenant_id: str | None = None) -> list[Document]:
    docs: list[Document] = []
    for path in paths:
        text = _normalize_text(path.read_text(encoding="utf-8", errors="ignore"))
        if not text.strip():
            continue
        docs.append(
            Document(
                page_content=text,
                metadata={
                    "source": str(path),
                    "title": path.stem,
                    "tenant_id": tenant_id,
                },
            )
        )
    return docs


def _normalize_text(text: str) -> str:
    return "\n".join(line.strip() for line in text.replace("\x00", "").splitlines()).strip()
