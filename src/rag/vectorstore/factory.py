from __future__ import annotations

from rag.config import RagConfig


def build_vectorstore(config: RagConfig, embedding_function):
    kind = config.vectorstore
    if kind == "chroma":
        from langchain_chroma import Chroma

        return Chroma(
            collection_name="rag_chunks",
            embedding_function=embedding_function,
            persist_directory=str(config.persist_path),
        )

    if kind in {"faiss", "qdrant", "weaviate", "pinecone"}:
        raise NotImplementedError(f"Vector store '{kind}' is declared but not implemented in this baseline")

    raise ValueError(f"Unsupported vector store: {kind}")
