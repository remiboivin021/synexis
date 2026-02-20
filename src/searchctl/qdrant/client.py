from __future__ import annotations

import time

from qdrant_client import QdrantClient


def make_client(url: str) -> QdrantClient:
    return QdrantClient(url=url)


def wait_ready(client: QdrantClient, max_attempts: int = 10) -> bool:
    for attempt in range(max_attempts):
        try:
            client.get_collections()
            return True
        except Exception:
            time.sleep(min(0.5 * (attempt + 1), 3.0))
    return False
