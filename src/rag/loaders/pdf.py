from __future__ import annotations

from pathlib import Path

from langchain_core.documents import Document


def load_pdf_documents(paths: list[Path]) -> list[Document]:
    # Optional module placeholder: PDF extraction can be added without changing interfaces.
    _ = paths
    return [Document(page_content="", metadata={})]
