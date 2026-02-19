from pathlib import Path
import sqlite3
import tempfile
import unittest

from synexis_brain.indexer.incremental import apply_incremental_index
from synexis_brain.indexer.metadata import connect_meta, ensure_meta_tables
from synexis_brain.indexer.scan import scan_vaults
from synexis_brain.search.bm25 import SQLiteBm25Index


class IncrementalIndexingTest(unittest.TestCase):
    def test_scan_and_delete_are_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vault = root / "vault"
            vault.mkdir()
            note = vault / "note.md"
            note.write_text("# H1\nhello world\n", encoding="utf-8")

            config = root / "config.yaml"
            config.write_text(
                """
vaults:
  - id: main
    path: {path}
    include: ["**/*.md"]
    exclude: []
""".format(path=vault.as_posix()),
                encoding="utf-8",
            )

            db_path = root / "meta.db"
            conn = connect_meta(str(db_path))
            ensure_meta_tables(conn)

            ctx = {
                "config_path": str(config),
                "db_path": str(db_path),
                "db_conn": conn,
            }
            out = scan_vaults(ctx, {})
            self.assertEqual(out["changes"]["new"], 1)

            ctx.update(out)
            apply_incremental_index(ctx, {})

            out_same = scan_vaults(ctx, {})
            self.assertEqual(out_same["changes"]["new"], 0)
            self.assertEqual(out_same["changes"]["changed"], 0)
            self.assertEqual(out_same["changes"]["unchanged"], 1)

            note.unlink()
            out2 = scan_vaults(ctx, {})
            self.assertEqual(len(out2["changes"]["deleted"]), 1)

    def test_bootstrap_bm25_when_meta_is_present_but_fts_is_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vault = root / "vault"
            vault.mkdir()
            note = vault / "note.md"
            note.write_text("# H1\nplaybook hello\n", encoding="utf-8")

            config = root / "config.yaml"
            config.write_text(
                """
vaults:
  - id: main
    path: {path}
    include: ["**/*.md"]
    exclude: []
""".format(path=vault.as_posix()),
                encoding="utf-8",
            )

            db_path = root / "meta.db"
            conn = connect_meta(str(db_path))
            ensure_meta_tables(conn)

            ctx = {"config_path": str(config), "db_path": str(db_path), "db_conn": conn}
            first = scan_vaults(ctx, {})
            ctx.update(first)
            apply_incremental_index(ctx, {})

            # Simulate backend switch / stale bm25 index by clearing FTS only.
            conn.execute("DELETE FROM bm25_chunks")
            conn.commit()

            second = scan_vaults(ctx, {})
            self.assertEqual(second["changes"]["unchanged"], 1)
            ctx.update(second)
            apply_incremental_index(ctx, {})

            bm25 = SQLiteBm25Index(conn)
            hits = bm25.topk("playbook", limit=5)
            self.assertGreaterEqual(len(hits), 1)


if __name__ == "__main__":
    unittest.main()
