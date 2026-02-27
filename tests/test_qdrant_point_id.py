from __future__ import annotations

from uuid import UUID

from searchctl.qdrant.collections import qdrant_point_id


def test_qdrant_point_id_is_deterministic_uuid() -> None:
    chunk_id = "abc123-chunk"
    p1 = qdrant_point_id(chunk_id)
    p2 = qdrant_point_id(chunk_id)
    assert p1 == p2
    assert str(UUID(p1)) == p1
