from __future__ import annotations

from opensearchpy import OpenSearch, helpers


def ensure_index(client: OpenSearch, index_name: str) -> None:
    if client.indices.exists(index=index_name):
        return
    mapping = {
        "mappings": {
            "properties": {
                "chunk_id": {"type": "keyword"},
                "doc_id": {"type": "keyword"},
                "path": {"type": "keyword", "fields": {"text": {"type": "text"}}},
                "title": {"type": "text"},
                "source_type": {"type": "keyword"},
                "text": {"type": "text"},
                "ordinal": {"type": "integer"},
                "start_char": {"type": "integer"},
                "end_char": {"type": "integer"},
                "heading_path": {"type": "text"},
                "mtime": {"type": "long"},
            }
        }
    }
    client.indices.create(index=index_name, body=mapping)


def index_chunks(client: OpenSearch, index_name: str, chunks: list[dict]) -> None:
    actions = [{"_op_type": "index", "_index": index_name, "_id": c["chunk_id"], "_source": c} for c in chunks]
    if actions:
        helpers.bulk(client, actions)


def delete_doc_chunks(client: OpenSearch, index_name: str, doc_id: str) -> None:
    client.delete_by_query(
        index=index_name,
        body={"query": {"term": {"doc_id": doc_id}}},
        refresh=True,
        conflicts="proceed",
    )
