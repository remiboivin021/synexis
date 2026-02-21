from __future__ import annotations

from pathlib import Path

import pytest
import searchctl.web as webmod

from searchctl.config import AppConfig
from searchctl.web import (
    _is_under_roots,
    _read_doc_content,
    create_app,
    render_markdown_safe,
    resolve_bind_host,
    should_use_vector,
)


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


def test_should_use_vector_defaults_to_bm25_for_web_search() -> None:
    assert should_use_vector(use_hybrid=False, summarize=False, summary_use_hybrid=False) is False
    assert should_use_vector(use_hybrid=False, summarize=True, summary_use_hybrid=False) is False
    assert should_use_vector(use_hybrid=True, summarize=False, summary_use_hybrid=False) is True


def test_render_markdown_safe_formats_common_markdown() -> None:
    md = "# Titre\n\n- item **gras**\n\nParagraphe `code`."
    html = render_markdown_safe(md)
    assert "<h1>Titre</h1>" in html
    assert "<ul>" in html
    assert "<strong>gras</strong>" in html
    assert "<code>code</code>" in html


def test_render_markdown_safe_escapes_raw_html() -> None:
    html = render_markdown_safe("Bonjour <script>alert(1)</script>")
    assert "<script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_fastapi_search_route_uses_request_injection(tmp_path: Path) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "roots: []\n"
        "opensearch:\n"
        "  url: http://localhost:9200\n"
        "  index_name: personal_chunks_v1\n"
        "qdrant:\n"
        "  url: http://localhost:6333\n"
        "  collection_name: personal_chunks_v1\n"
        "  vector_size: 384\n"
        "  distance: Cosine\n",
        encoding="utf-8",
    )
    app = create_app(str(cfg))
    search_route = next(route for route in app.routes if getattr(route, "path", None) == "/api/search")
    assert search_route.dependant.request_param_name == "request"
    assert len(search_route.dependant.query_params) == 0


def test_fastapi_static_routes_exist(tmp_path: Path) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "roots: []\n"
        "qdrant:\n"
        "  vector_size: 384\n",
        encoding="utf-8",
    )
    app = create_app(str(cfg))
    paths = {route.path for route in app.routes if hasattr(route, "path")}
    assert "/static/app.css" in paths
    assert "/static/app.js" in paths
