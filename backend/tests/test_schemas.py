"""Tests for Pydantic schemas and enum validation."""

import pytest
from pydantic import ValidationError

from app.models.short import ShortStyle
from app.schemas.short import ShortGenerateRequest, ShortSourceInput
from app.schemas.video import VideoCreate


def test_video_create_schema():
    valid = VideoCreate(youtube_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert valid.youtube_url == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def test_short_generate_request_validation():
    req = ShortGenerateRequest(video_id=1, count=5, duration=60, style=ShortStyle.VIRAL)
    assert req.video_id == 1
    assert req.count == 5
    assert req.duration == 60
    assert req.style == ShortStyle.VIRAL

    # Count out of range
    with pytest.raises(ValidationError):
        ShortGenerateRequest(video_id=1, count=25)


def test_short_source_input():
    src = ShortSourceInput(chunk_id=10, start_time=12.5, end_time=45.0)
    assert src.chunk_id == 10
    assert src.start_time == 12.5
    assert src.end_time == 45.0
