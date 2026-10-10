from app.services.chunking import chunk_text


def test_chunking_has_overlap_and_no_empty_chunks():
    chunks = chunk_text("one two three four five six seven eight", size=4, overlap=1)
    assert chunks
    assert all(chunks)
    assert chunks[0] == "one two three four"
    assert chunks[1].startswith("four")


def test_empty_text():
    assert chunk_text("") == []
