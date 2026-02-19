import sqlite3
import unittest

from synexis_brain.search.backends import build_bm25_backend
from synexis_brain.search.bm25 import SQLiteBm25Index


class Bm25BackendSelectionTest(unittest.TestCase):
    def test_tantivy_falls_back_to_sqlite_when_missing(self) -> None:
        conn = sqlite3.connect(":memory:")
        backend = build_bm25_backend({"search": {"bm25_backend": "tantivy"}}, conn)
        self.assertIsInstance(backend, SQLiteBm25Index)


if __name__ == "__main__":
    unittest.main()
