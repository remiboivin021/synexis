from searchctl.summary import collect_sources, format_sources


def test_collect_sources_deduplicates_by_chunk() -> None:
    rows = [
        {
            "rank": 1,
            "doc_path": "/a.md",
            "doc_title": "A",
            "citation": {"chunk_id": "c1", "start_char": 0, "end_char": 10},
        },
        {
            "rank": 2,
            "doc_path": "/a.md",
            "doc_title": "A",
            "citation": {"chunk_id": "c1", "start_char": 0, "end_char": 10},
        },
    ]
    sources = collect_sources(rows)
    assert len(sources) == 1
    assert sources[0]["chunk_id"] == "c1"


def test_format_sources_is_human_readable() -> None:
    text = format_sources(
        [
            {
                "doc_title": "Doc",
                "doc_path": "/x.md",
                "chunk_id": "abc",
                "start_char": 12,
                "end_char": 34,
            }
        ]
    )
    assert text.startswith("Sources")
    assert "Doc | /x.md | chunk=abc [12:34]" in text
