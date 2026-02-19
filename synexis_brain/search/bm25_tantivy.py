from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Any


@dataclass
class TantivyConfig:
    index_dir: str


class TantivyBm25Index:
    """Tantivy backend. Requires `tantivy` package at runtime."""

    def __init__(self, config: TantivyConfig) -> None:
        self.config = config
        self.log = logging.getLogger("synexis.search.tantivy")
        self._index_dir = Path(config.index_dir)
        self._index_dir.mkdir(parents=True, exist_ok=True)

        try:
            import tantivy  # type: ignore
        except ModuleNotFoundError as exc:
            raise RuntimeError("Tantivy backend requested but package `tantivy` is not installed") from exc

        # Compatibility gate for the currently installed Python bindings.
        if not hasattr(tantivy.Index, "parse_query"):
            raise RuntimeError(
                "Tantivy backend requested but installed bindings are incompatible (missing Index.parse_query API)"
            )

        self.tantivy = tantivy
        self.schema, self.fields = self._build_schema(tantivy)
        self.index = self._open_or_create_index()

    def _build_schema(self, tantivy: Any) -> tuple[Any, dict[str, Any]]:
        builder = tantivy.SchemaBuilder()
        fields = {
            "chunk_id": builder.add_text_field("chunk_id", stored=True),
            "vault_id": builder.add_text_field("vault_id", stored=True),
            "path": builder.add_text_field("path", stored=True),
            "heading": builder.add_text_field("heading", stored=True),
            "text": builder.add_text_field("text", stored=True),
            "tags": builder.add_text_field("tags", stored=True),
            "type": builder.add_text_field("type", stored=True),
            "status": builder.add_text_field("status", stored=True),
        }
        schema = builder.build()
        return schema, fields

    def _open_or_create_index(self) -> Any:
        try:
            return self.tantivy.Index.open(self._index_dir.as_posix())
        except Exception:
            return self.tantivy.Index(self.schema, path=self._index_dir.as_posix())

    def _writer(self) -> Any:
        return self.index.writer()

    def upsert_chunks(self, chunks: list[dict[str, Any]]) -> None:
        writer = self._writer()
        for chunk in chunks:
            self._delete_by_chunk_id(writer, chunk["chunk_id"])
            writer.add_document(
                self.tantivy.Document(
                    **{
                        "chunk_id": [str(chunk["chunk_id"])],
                        "vault_id": [str(chunk["vault_id"])],
                        "path": [str(chunk["path"])],
                        "heading": [str(chunk.get("heading", ""))],
                        "text": [str(chunk.get("text", ""))],
                        "tags": [str(chunk.get("tags", ""))],
                        "type": [str(chunk.get("type", ""))],
                        "status": [str(chunk.get("status", ""))],
                    }
                )
            )
        writer.commit()
        if hasattr(self.index, "reload"):
            self.index.reload()

    def delete_file(self, vault_id: str, path: str) -> None:
        writer = self._writer()
        self._delete_by_term(writer, "vault_id", str(vault_id))
        self._delete_by_term(writer, "path", str(path))
        writer.commit()
        if hasattr(self.index, "reload"):
            self.index.reload()

    def _delete_by_chunk_id(self, writer: Any, chunk_id: str) -> None:
        self._delete_by_term(writer, "chunk_id", str(chunk_id))

    def _delete_by_term(self, writer: Any, field_name: str, value: str) -> None:
        # Binding compatibility: current tantivy exposes delete_documents_by_term(field, value).
        if hasattr(writer, "delete_documents_by_term"):
            writer.delete_documents_by_term(field_name, value)
            return
        if hasattr(writer, "delete_documents"):
            writer.delete_documents(field_name, value)
            return
        raise RuntimeError("Tantivy writer does not expose term-delete APIs")

    def topk(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        if hasattr(self.index, "reload"):
            self.index.reload()
        searcher = self.index.searcher()
        q = self.index.parse_query(query, default_field_names=["text", "heading"])
        hits = searcher.search(q, limit)

        results: list[dict[str, Any]] = []
        for score, doc_address in hits.hits:
            doc = searcher.doc(doc_address)
            doc_map = doc.to_dict() if hasattr(doc, "to_dict") else {}
            data = {k: _first(doc_map.get(k)) for k in self.fields}
            results.append(
                {
                    "chunk_id": data["chunk_id"],
                    "vault_id": data["vault_id"],
                    "path": data["path"],
                    "heading": data["heading"],
                    "preview": data["text"][:240],
                    "score": float(score),
                    "tags": data["tags"],
                    "type": data["type"],
                    "status": data["status"],
                }
            )
        return results


def _first(values: Any) -> str:
    if values is None:
        return ""
    if isinstance(values, list):
        if not values:
            return ""
        return str(values[0])
    return str(values)
