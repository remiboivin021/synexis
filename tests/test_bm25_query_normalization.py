import unittest
import sqlite3

from synexis_brain.search.bm25 import SQLiteBm25Index


class Bm25QueryNormalizationTest(unittest.TestCase):
    def test_plural_query_matches_singular_document(self) -> None:
        conn = sqlite3.connect(":memory:")
        index = SQLiteBm25Index(conn)
        index.upsert_chunks(
            [
                {
                    "chunk_id": "c1",
                    "vault_id": "v",
                    "path": "a.md",
                    "heading": "H",
                    "text": "projet en cours",
                    "tags": "",
                    "type": "",
                    "status": "",
                }
            ]
        )

        hits = index.topk("projets en cours", limit=5)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["chunk_id"], "c1")

    def test_fallback_or_query_when_and_has_no_hits(self) -> None:
        conn = sqlite3.connect(":memory:")
        index = SQLiteBm25Index(conn)
        index.upsert_chunks(
            [
                {
                    "chunk_id": "c2",
                    "vault_id": "v",
                    "path": "b.md",
                    "heading": "H",
                    "text": "projet roadmap",
                    "tags": "",
                    "type": "",
                    "status": "",
                }
            ]
        )

        hits = index.topk("projets en cours", limit=5)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["chunk_id"], "c2")


if __name__ == "__main__":
    unittest.main()
