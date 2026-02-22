from __future__ import annotations

import hashlib
from typing import Iterable

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_documents(
    docs: Iterable[Document],
    chunk_size: int,
    chunk_overlap: int,
) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunked = splitter.split_documents(list(docs))

    by_doc: dict[str, int] = {}
    out: list[Document] = []
    for doc in chunked:
        source = str(doc.metadata.get("source") or "unknown")
        doc_id = str(doc.metadata.get("doc_id") or stable_doc_id(source))
        ordinal = by_doc.get(doc_id, 0)
        by_doc[doc_id] = ordinal + 1

        text_hash = hashlib.sha1(doc.page_content.encode("utf-8")).hexdigest()
        chunk_id = stable_chunk_id(doc_id=doc_id, ordinal=ordinal, text_hash=text_hash)
        enriched = dict(doc.metadata)
        enriched["doc_id"] = doc_id
        enriched["chunk_id"] = chunk_id
        enriched["chunk_ordinal"] = ordinal
        out.append(Document(page_content=doc.page_content, metadata=enriched))
    return out


def stable_doc_id(source: str) -> str:
    return hashlib.sha1(source.encode("utf-8")).hexdigest()


def stable_chunk_id(doc_id: str, ordinal: int, text_hash: str) -> str:
    raw = f"{doc_id}:{ordinal}:{text_hash}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()
