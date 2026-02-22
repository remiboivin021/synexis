from __future__ import annotations

from langchain_core.documents import Document


def load_url_documents(urls: list[str]) -> list[Document]:
    # Optional module placeholder: URL loading is intentionally explicit.
    return [Document(page_content="", metadata={"source": url}) for url in urls]
