import unittest

from synexis_brain.search.hybrid import hybrid_merge


class HybridMergeTest(unittest.TestCase):
    def test_merge_by_chunk_id(self) -> None:
        bm25 = [
            {"chunk_id": "a", "score": 0.2, "path": "a.md"},
            {"chunk_id": "b", "score": 0.1, "path": "b.md"},
        ]
        vec = [
            {"chunk_id": "b", "score": 0.9, "path": "b.md"},
            {"chunk_id": "c", "score": 0.8, "path": "c.md"},
        ]

        merged = hybrid_merge(bm25, vec, w_bm25=0.5, w_vector=0.5, limit=3)
        ids = [x["chunk_id"] for x in merged]
        self.assertEqual(ids, ["b", "a", "c"])


if __name__ == "__main__":
    unittest.main()
