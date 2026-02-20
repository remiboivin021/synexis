from searchctl.fusion import rrf_fuse


def test_rrf_deterministic_ordering_and_math() -> None:
    bm25 = [{"chunk_id": "a"}, {"chunk_id": "b"}]
    vector = [{"chunk_id": "b"}, {"chunk_id": "a"}, {"chunk_id": "c"}]
    rows = rrf_fuse(bm25, vector, rrf_k=60)
    assert [r.chunk_id for r in rows] == ["a", "b", "c"]
    a = next(r for r in rows if r.chunk_id == "a")
    assert abs(a.score - ((1 / 61) + (1 / 62))) < 1e-9
