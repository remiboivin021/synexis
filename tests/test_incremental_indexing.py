from pathlib import Path
import sqlite3
import tempfile
import unittest

from synexis_brain.indexer.incremental import apply_incremental_index
from synexis_brain.indexer.metadata import connect_meta, ensure_meta_tables
from synexis_brain.indexer.scan import scan_vaults


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


if __name__ == "__main__":
    unittest.main()
