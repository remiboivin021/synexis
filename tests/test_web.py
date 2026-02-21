from __future__ import annotations

from pathlib import Path

import pytest

from searchctl.config import AppConfig
from searchctl.web import _is_under_roots, _read_doc_content, resolve_bind_host


def test_resolve_bind_host_accepts_local_defaults() -> None:
    assert resolve_bind_host("", allow_remote=False) == "127.0.0.1"
    assert resolve_bind_host("localhost", allow_remote=False) == "localhost"


def test_resolve_bind_host_blocks_remote_without_explicit_flag() -> None:
    with pytest.raises(ValueError, match="remote bind denied"):
        resolve_bind_host("0.0.0.0", allow_remote=False)


def test_resolve_bind_host_allows_remote_when_flag_enabled() -> None:
    assert resolve_bind_host("0.0.0.0", allow_remote=True) == "0.0.0.0"


def test_is_under_roots_detects_inside_and_outside(tmp_path: Path) -> None:
    root = tmp_path / "vault"
    root.mkdir()
    inside = root / "note.md"
    inside.write_text("hello", encoding="utf-8")
    outside = tmp_path / "other.md"
    outside.write_text("x", encoding="utf-8")

    assert _is_under_roots(inside, [str(root)]) is True
    assert _is_under_roots(outside, [str(root)]) is False


def test_read_doc_content_enforces_root_boundary(tmp_path: Path) -> None:
    root = tmp_path / "vault"
    root.mkdir()
    inside = root / "note.md"
    inside.write_text("inside", encoding="utf-8")
    outside = tmp_path / "outside.md"
    outside.write_text("outside", encoding="utf-8")

    cfg = AppConfig(roots=[str(root)])

    inside_doc = {
        "doc_id": "d1",
        "source_type": "markdown",
        "path": str(inside),
    }
    assert _read_doc_content(inside_doc, cfg) == "inside"

    outside_doc = {
        "doc_id": "d2",
        "source_type": "markdown",
        "path": str(outside),
    }
    with pytest.raises(PermissionError, match="outside configured roots"):
        _read_doc_content(outside_doc, cfg)
