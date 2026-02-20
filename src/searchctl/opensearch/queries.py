from __future__ import annotations

from opensearchpy import OpenSearch


def bm25_search(client: OpenSearch, index_name: str, query: str, top_k: int, source_type: str | None, path_contains: str | None) -> list[dict]:
    must: list[dict] = [{"multi_match": {"query": query, "fields": ["title^2", "text", "path.text"]}}]
    filters: list[dict] = []
    if source_type:
        filters.append({"term": {"source_type": source_type}})
    if path_contains:
        filters.append({"wildcard": {"path": f"*{path_contains}*"}})

    body = {
        "size": top_k,
        "query": {"bool": {"must": must, "filter": filters}},
        "highlight": {"fields": {"text": {}}},
    }
    resp = client.search(index=index_name, body=body)
    out: list[dict] = []
    for hit in resp.get("hits", {}).get("hits", []):
        src = hit.get("_source", {})
        src["highlight"] = " ".join(hit.get("highlight", {}).get("text", []))
        out.append(src)
    return out
