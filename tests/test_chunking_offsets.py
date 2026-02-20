from searchctl.chunking import split_into_chunks


def test_chunk_offsets_are_valid_and_stable() -> None:
    text = "A" * 5000
    chunks = split_into_chunks(text, target_chars=2200, overlap_chars=250, min_chunk_chars=400)
    assert chunks
    for c in chunks:
        assert 0 <= c.start_char < c.end_char <= len(text)
        assert c.text == text[c.start_char : c.end_char]
