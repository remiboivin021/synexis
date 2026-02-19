from pathlib import Path
import tempfile
import unittest

from synexis_brain.tui.backend import SearchFilters, SearchService


class TuiBackendTest(unittest.TestCase):
    def test_search_and_filters(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vault = root / "vault"
            vault.mkdir()
            (vault / "one.md").write_text("""---\nstatus: open\ntype: playbook\ntags: alpha,beta\n---\n# Intro\nincident response\n""", encoding="utf-8")
            (vault / "two.md").write_text("""---\nstatus: done\ntype: decision\ntags: gamma\n---\n# Intro\nincident postmortem\n""", encoding="utf-8")

            cfg = root / "config.yaml"
            cfg.write_text(
                f"""
vaults:
  - id: main
    path: {vault.as_posix()}
    include: [\"**/*.md\"]
    exclude: []
""",
                encoding="utf-8",
            )

            service = SearchService(db_path=str(root / "meta.db"), config_path=str(cfg))
            service.reindex()

            all_results = service.search("incident", SearchFilters())
            self.assertEqual(len(all_results), 2)

            filtered = service.search("incident", SearchFilters(status="open", chunk_type="playbook", tag="alpha"))
            self.assertEqual(len(filtered), 1)
            citation = service.citation_for(filtered[0])
            self.assertTrue(citation.startswith("[[one.md#"))


if __name__ == "__main__":
    unittest.main()
