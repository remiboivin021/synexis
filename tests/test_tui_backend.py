from pathlib import Path
import tempfile
import unittest

from synexis_brain.tui.backend import SearchFilters, SearchService


class TuiBackendTest(unittest.TestCase):
    def test_semantic_search_and_filters(self) -> None:
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
            service.vector.topk = lambda *args, **kwargs: [
                {
                    "chunk_id": "c1",
                    "vault_id": "main",
                    "path": "one.md",
                    "heading": "Intro",
                    "preview": "incident response",
                    "score": 0.91,
                    "tags": "alpha,beta",
                    "type": "playbook",
                    "status": "open",
                },
                {
                    "chunk_id": "c2",
                    "vault_id": "main",
                    "path": "two.md",
                    "heading": "Intro",
                    "preview": "incident postmortem",
                    "score": 0.78,
                    "tags": "gamma",
                    "type": "decision",
                    "status": "done",
                },
            ]

            all_results = service.search("incident", SearchFilters())
            self.assertEqual(len(all_results), 2)
            self.assertEqual(all_results[0]["chunk_id"], "c1")

            filtered = service.search("incident", SearchFilters(status="open", chunk_type="playbook", tag="alpha"))
            self.assertEqual(len(filtered), 1)
            citation = service.citation_for(filtered[0])
            self.assertTrue(citation.startswith("[[one.md#"))

    def test_bm25_fallback_when_vector_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vault = root / "vault"
            vault.mkdir()
            (vault / "seed.md").write_text("# Seed\ntext\n", encoding="utf-8")

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
            service.bm25.topk = lambda query, limit: [
                {
                    "chunk_id": "pb",
                    "vault_id": "main",
                    "path": "playbooks/alpha.md",
                    "heading": "Alpha",
                    "preview": "projet",
                    "score": -1.0,
                    "tags": "",
                    "type": "playbook",
                    "status": "done",
                },
                {
                    "chunk_id": "prj",
                    "vault_id": "main",
                    "path": "projets/beta.md",
                    "heading": "Beta",
                    "preview": "projet en cours",
                    "score": -2.0,
                    "tags": "",
                    "type": "projet",
                    "status": "open",
                },
            ]
            service.vector.topk = lambda *args, **kwargs: []

            results = service.search("projets en cours", SearchFilters())
            self.assertEqual(results[0]["chunk_id"], "prj")

    def test_bm25_fallback_when_vector_has_too_few_hits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vault = root / "vault"
            vault.mkdir()
            (vault / "seed.md").write_text("# Seed\ntext\n", encoding="utf-8")

            cfg = root / "config.yaml"
            cfg.write_text(
                f"""
vaults:
  - id: main
    path: {vault.as_posix()}
    include: [\"**/*.md\"]
    exclude: []
search:
  vector_min_hits: 3
""",
                encoding="utf-8",
            )

            service = SearchService(db_path=str(root / "meta.db"), config_path=str(cfg))
            service.reindex()
            service.vector.topk = lambda *args, **kwargs: [
                {
                    "chunk_id": "dash",
                    "vault_id": "main",
                    "path": "90_Dashboard/index.md",
                    "heading": "Dashboard",
                    "preview": "",
                    "score": 0.98,
                    "tags": "",
                    "type": "",
                    "status": "",
                }
            ]
            service.bm25.topk = lambda query, limit: [
                {
                    "chunk_id": "prj",
                    "vault_id": "main",
                    "path": "03_Projects/proof_and_case_studies.md",
                    "heading": "Proof",
                    "preview": "",
                    "score": -3.0,
                    "tags": "",
                    "type": "",
                    "status": "",
                }
            ]

            results = service.search("projets en cours", SearchFilters(), limit=10)
            ids = [r["chunk_id"] for r in results]
            self.assertIn("dash", ids)
            self.assertIn("prj", ids)

    def test_bm25_coverage_reduces_false_positives(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vault = root / "vault"
            vault.mkdir()
            (vault / "seed.md").write_text("# Seed\ntext\n", encoding="utf-8")

            cfg = root / "config.yaml"
            cfg.write_text(
                f"""
vaults:
  - id: main
    path: {vault.as_posix()}
    include: [\"**/*.md\"]
    exclude: []
search:
  vector_min_hits: 3
  vector_min_score: 0.3
  bm25_min_term_coverage: 0.5
""",
                encoding="utf-8",
            )

            service = SearchService(db_path=str(root / "meta.db"), config_path=str(cfg))
            service.reindex()
            service.vector.topk = lambda *args, **kwargs: [
                {
                    "chunk_id": "dash",
                    "vault_id": "main",
                    "path": "90_Dashboard/index.md",
                    "heading": "Dashboard",
                    "preview": "",
                    "score": 0.2,
                    "tags": "",
                    "type": "",
                    "status": "",
                }
            ]
            service.bm25.topk = lambda query, limit: [
                {
                    "chunk_id": "dash",
                    "vault_id": "main",
                    "path": "90_Dashboard/index.md",
                    "heading": "Dashboard",
                    "preview": "weekly goals",
                    "score": -9.0,
                    "tags": "",
                    "type": "",
                    "status": "",
                },
                {
                    "chunk_id": "prj",
                    "vault_id": "main",
                    "path": "03_Projects/proof_and_case_studies.md",
                    "heading": "Projet en cours",
                    "preview": "",
                    "score": -3.0,
                    "tags": "",
                    "type": "",
                    "status": "open",
                },
            ]

            results = service.search("projets en cours", SearchFilters(), limit=10)
            ids = [r["chunk_id"] for r in results]
            self.assertIn("prj", ids)
            self.assertNotIn("dash", ids)

    def test_bm25_requires_structural_match_not_preview_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vault = root / "vault"
            vault.mkdir()
            (vault / "seed.md").write_text("# Seed\ntext\n", encoding="utf-8")

            cfg = root / "config.yaml"
            cfg.write_text(
                f"""
vaults:
  - id: main
    path: {vault.as_posix()}
    include: [\"**/*.md\"]
    exclude: []
search:
  vector_min_hits: 3
  vector_min_score: 0.3
  bm25_min_term_coverage: 0.5
""",
                encoding="utf-8",
            )

            service = SearchService(db_path=str(root / "meta.db"), config_path=str(cfg))
            service.reindex()
            service.vector.topk = lambda *args, **kwargs: []
            service.bm25.topk = lambda query, limit: [
                {
                    "chunk_id": "dash",
                    "vault_id": "main",
                    "path": "90_Dashboard/index.md",
                    "heading": "Dashboard",
                    "preview": "projets en cours",
                    "score": -9.0,
                    "tags": "",
                    "type": "",
                    "status": "",
                },
                {
                    "chunk_id": "prj",
                    "vault_id": "main",
                    "path": "03_Projects/proof_and_case_studies.md",
                    "heading": "Projet actif",
                    "preview": "",
                    "score": -3.0,
                    "tags": "",
                    "type": "",
                    "status": "",
                },
            ]
            results = service.search("projets en cours", SearchFilters(), limit=10)
            ids = [r["chunk_id"] for r in results]
            self.assertIn("prj", ids)
            self.assertNotIn("dash", ids)


if __name__ == "__main__":
    unittest.main()
