import unittest

from synexis_brain.search.nlu import infer_filters


class NLUFiltersTest(unittest.TestCase):
    def test_infers_type_status_tag_vault(self) -> None:
        q = infer_filters(
            "playbooks en cours #client freelance",
            available_vaults=["Freelance", "Personal"],
        )
        self.assertEqual(q.inferred.chunk_type, "playbook")
        self.assertEqual(q.inferred.status, "open")
        self.assertEqual(q.inferred.tag, "client")
        self.assertEqual(q.inferred.vault_id, "Freelance")

    def test_keeps_text_query_after_filter_extraction(self) -> None:
        q = infer_filters("decision terminee pricing", available_vaults=["Freelance"])
        self.assertEqual(q.inferred.chunk_type, "decision")
        self.assertEqual(q.inferred.status, "done")
        self.assertIn("pricing", q.text_query)


if __name__ == "__main__":
    unittest.main()
