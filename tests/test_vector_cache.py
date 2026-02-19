from pathlib import Path
import tempfile
import unittest

from synexis_brain.indexer.metadata import connect_meta
from synexis_brain.search.vector import EmbeddingService


class VectorCacheTest(unittest.TestCase):
    def test_embedding_cache_by_chunk_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            conn = connect_meta(str(Path(tmp) / "meta.db"))
            svc = EmbeddingService(conn)

            v1 = svc.embedding_for_chunk("h1", "hello world")
            v2 = svc.embedding_for_chunk("h1", "hello world changed")
            self.assertEqual(v1, v2)


if __name__ == "__main__":
    unittest.main()
