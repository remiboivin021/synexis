from __future__ import annotations

import time

from opensearchpy import OpenSearch


def make_client(url: str) -> OpenSearch:
    return OpenSearch(hosts=[url], use_ssl=False, verify_certs=False)


def wait_ready(client: OpenSearch, max_attempts: int = 10) -> bool:
    for attempt in range(max_attempts):
        try:
            if client.ping():
                return True
        except Exception:
            pass
        time.sleep(min(0.5 * (attempt + 1), 3.0))
    return False
