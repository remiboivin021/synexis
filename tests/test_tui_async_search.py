import unittest

from synexis_brain.tui.backend import SearchFilters


class AsyncSearchContractTest(unittest.TestCase):
    def test_search_filters_copyable(self) -> None:
        # Guardrail for app async thread-offload path: filters are plain dataclass values.
        f = SearchFilters(vault_id="v", chunk_type="t", tag="x", status="open")
        self.assertEqual(f.vault_id, "v")
        self.assertEqual(f.chunk_type, "t")
        self.assertEqual(f.tag, "x")
        self.assertEqual(f.status, "open")


if __name__ == "__main__":
    unittest.main()
