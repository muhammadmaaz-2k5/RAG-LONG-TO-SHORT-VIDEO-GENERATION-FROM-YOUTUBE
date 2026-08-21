"""Tests for text cleaning and timestamp-aware chunking."""

from app.services.chunker import chunk_transcript, clean_text


def test_clean_text_removes_brackets():
    raw = "Hello [Music] world! (applause) Let's learn &amp; build."
    cleaned = clean_text(raw)
    assert "[Music]" not in cleaned
    assert "(applause)" not in cleaned
    assert "&amp;" not in cleaned
    assert "Hello world! Let's learn build." == cleaned


def test_chunk_transcript_timestamps_and_words():
    # 20 snippets each having 10 words (total 200 words)
    snippets = [
        {
            "text": f"This is word group number {i} providing detailed sentences.",
            "start": float(i * 5),
            "duration": 5.0,
        }
        for i in range(20)
    ]

    chunks = chunk_transcript(snippets, min_words=80, max_words=120)
    assert len(chunks) >= 2

    # Verify timestamp continuity
    for chunk in chunks:
        assert chunk["start_time"] < chunk["end_time"]
        assert chunk["word_count"] > 0
        assert len(chunk["text"]) > 0

    assert chunks[0]["start_time"] == 0.0
