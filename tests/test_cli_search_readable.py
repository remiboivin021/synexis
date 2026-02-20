from searchctl.cli import _format_search_results


def test_search_readable_format_contains_key_fields() -> None:
    rows = [
        {
            "rank": 1,
            "score": 0.123456789,
            "doc_path": "/vault/note.md",
            "doc_title": "Note",
            "snippet": "hello world",
            "citation": {"chunk_id": "abc", "start_char": 10, "end_char": 20},
            "signals": {"bm25_rank": 1, "vector_rank": 3, "fusion_method": "rrf"},
        }
    ]
    out = _format_search_results("hello", rows)
    assert 'Results for: "hello"' in out
    assert "[1] Note" in out
    assert "path: /vault/note.md" in out
    assert "snippet: hello world" in out
    assert "citation: abc [10:20]" in out
    assert "signals: bm25_rank=1 vector_rank=3 fusion=rrf" in out


def test_search_readable_no_results() -> None:
    assert _format_search_results("x", []) == "No results for query: x"
