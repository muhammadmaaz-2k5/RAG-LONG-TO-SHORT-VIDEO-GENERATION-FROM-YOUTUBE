from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.video import VideoStatus


class VideoCreate(BaseModel):
    youtube_url: str = Field(
        ...,
        description="Full YouTube URL (e.g. https://www.youtube.com/watch?v=... or https://youtu.be/...)",
        examples=["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
    )


class TranscriptChunkResponse(BaseModel):
    id: int
    video_id: int
    chunk_index: int
    start_time: float
    end_time: float
    text: str
    has_embedding: bool = Field(default=True, description="Indicates if embedding vector is populated")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VideoResponse(BaseModel):
    id: int
    youtube_id: str
    youtube_url: str
    title: Optional[str] = None
    channel_name: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    status: VideoStatus
    chunk_count: Optional[int] = None
    shorts_count: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VideoDetailResponse(VideoResponse):
    transcript_text: Optional[str] = None
    chunks: Optional[List[TranscriptChunkResponse]] = None


class VideoProcessResponse(BaseModel):
    id: int
    youtube_id: str
    status: VideoStatus
    chunks_created: int
    message: str
