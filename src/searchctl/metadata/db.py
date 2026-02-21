from __future__ import annotations

import sqlite3
import time
from importlib import resources
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1


class MetadataDB:
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    def init_schema(self) -> None:
        self.conn.executescript(_load_schema_sql())
        row = self.conn.execute("SELECT schema_version FROM meta LIMIT 1").fetchone()
        if row is None:
            self.conn.execute("INSERT INTO meta(schema_version) VALUES (?)", (SCHEMA_VERSION,))
        elif row[0] != SCHEMA_VERSION:
            raise RuntimeError(f"schema version mismatch: expected {SCHEMA_VERSION}, got {row[0]}")
        self.conn.commit()

    def list_documents(self) -> list[sqlite3.Row]:
        return list(self.conn.execute("SELECT * FROM documents").fetchall())

    def get_document(self, doc_id: str) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM documents WHERE doc_id = ?", (doc_id,)).fetchone()

    def upsert_document(self, doc: dict[str, Any]) -> None:
        self.conn.execute(
            """
            INSERT INTO documents(doc_id,path,source_type,title,mtime,content_hash,status,error,updated_at)
            VALUES (:doc_id,:path,:source_type,:title,:mtime,:content_hash,:status,:error,:updated_at)
            ON CONFLICT(doc_id) DO UPDATE SET
              path=excluded.path,
              source_type=excluded.source_type,
              title=excluded.title,
              mtime=excluded.mtime,
              content_hash=excluded.content_hash,
              status=excluded.status,
              error=excluded.error,
              updated_at=excluded.updated_at
            """,
            doc,
        )

    def delete_doc_chunks(self, doc_id: str) -> None:
        self.conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))

    def delete_document(self, doc_id: str) -> None:
        self.conn.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))

    def insert_chunk_row(self, row: dict[str, Any]) -> None:
        self.conn.execute(
            """
            INSERT INTO chunks(chunk_id,doc_id,ordinal,text_hash,start_char,end_char,heading_path)
            VALUES (:chunk_id,:doc_id,:ordinal,:text_hash,:start_char,:end_char,:heading_path)
            """,
            row,
        )

    def log_error(
        self,
        stage: str,
        message: str,
        path: str | None = None,
        doc_id: str | None = None,
        chunk_id: str | None = None,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO errors(stage,path,doc_id,chunk_id,message,created_at)
            VALUES (?,?,?,?,?,?)
            """,
            (stage, path, doc_id, chunk_id, message, int(time.time())),
        )

    def commit(self) -> None:
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def status(self) -> dict[str, int | None]:
        docs_total = self.conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        docs_indexed = self.conn.execute("SELECT COUNT(*) FROM documents WHERE status='indexed'").fetchone()[0]
        docs_partial = self.conn.execute("SELECT COUNT(*) FROM documents WHERE status='partial'").fetchone()[0]
        docs_error = self.conn.execute("SELECT COUNT(*) FROM documents WHERE status='error'").fetchone()[0]
        chunks_total = self.conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        last = self.conn.execute("SELECT MAX(updated_at) FROM documents").fetchone()[0]
        return {
            "docs_total": docs_total,
            "docs_indexed": docs_indexed,
            "docs_partial": docs_partial,
            "docs_error": docs_error,
            "chunks_total": chunks_total,
            "last_ingest_timestamp": last,
        }

    def fetch_chunk(self, chunk_id: str) -> sqlite3.Row | None:
        return self.conn.execute(
            """
            SELECT c.*, d.path, d.title, d.doc_id
            FROM chunks c JOIN documents d ON c.doc_id=d.doc_id
            WHERE c.chunk_id = ?
            """,
            (chunk_id,),
        ).fetchone()

    def fetch_doc(self, path: str) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM documents WHERE path = ?", (path,)).fetchone()


def _load_schema_sql() -> str:
    schema_path = Path(__file__).with_name("schema.sql")
    if schema_path.exists():
        return schema_path.read_text(encoding="utf-8")
    try:
        return resources.files("searchctl.metadata").joinpath("schema.sql").read_text(encoding="utf-8")
    except Exception as exc:
        raise FileNotFoundError("searchctl metadata schema.sql not found in package or source tree") from exc
