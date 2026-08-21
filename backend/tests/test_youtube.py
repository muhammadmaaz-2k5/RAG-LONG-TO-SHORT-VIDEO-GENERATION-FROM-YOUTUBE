"""Tests for YouTube URL parsing and extraction."""

from app.services.youtube import extract_youtube_id


def test_extract_youtube_id_standard_url():
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert extract_youtube_id(url) == "dQw4w9WgXcQ"


def test_extract_youtube_id_short_url():
    url = "https://youtu.be/dQw4w9WgXcQ"
    assert extract_youtube_id(url) == "dQw4w9WgXcQ"


def test_extract_youtube_id_shorts_format():
    url = "https://www.youtube.com/shorts/dQw4w9WgXcQ"
    assert extract_youtube_id(url) == "dQw4w9WgXcQ"


def test_extract_youtube_id_embed_format():
    url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
    assert extract_youtube_id(url) == "dQw4w9WgXcQ"


def test_extract_youtube_id_raw_id():
    raw_id = "dQw4w9WgXcQ"
    assert extract_youtube_id(raw_id) == "dQw4w9WgXcQ"


def test_extract_youtube_id_invalid():
    assert extract_youtube_id("https://google.com") is None
    assert extract_youtube_id("") is None
