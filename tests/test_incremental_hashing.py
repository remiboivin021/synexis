from pathlib import Path

from searchctl.hashing import make_doc_id, sha256_text


def test_content_hash_changes_with_extracted_text() -> None:
    assert sha256_text("hello") != sha256_text("hello!")


def test_doc_id_uses_normalized_path(tmp_path: Path) -> None:
    p = tmp_path / "A" / "b.md"
    p.parent.mkdir(parents=True)
    p.write_text("x", encoding="utf-8")
    assert make_doc_id(p) == make_doc_id(Path(str(p)))
