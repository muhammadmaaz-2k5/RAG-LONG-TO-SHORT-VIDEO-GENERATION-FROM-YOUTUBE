from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.short import ShortStatus, ShortStyle


class ShortSourceResponse(BaseModel):
    id: int
    short_id: int
    chunk_id: int
    start_time: float
    end_time: float

    model_config = ConfigDict(from_attributes=True)


class ShortSourceInput(BaseModel):
    chunk_id: int
    start_time: float
    end_time: float


class ShortGenerateRequest(BaseModel):
    video_id: int = Field(..., description="ID of the processed video to generate shorts from")
    count: int = Field(default=5, ge=1, le=10, description="Number of shorts to generate (1-10)")
    duration: int = Field(default=60, ge=15, le=90, description="Target duration in seconds (15-90)")
    style: ShortStyle = Field(default=ShortStyle.VIRAL, description="Viral, Educational, Storytelling, etc.")


class ShortRegenerateRequest(BaseModel):
    style: Optional[ShortStyle] = Field(None, description="Optional new style for regeneration")
    duration: Optional[int] = Field(None, ge=15, le=90, description="Optional new duration target")


class ShortResponse(BaseModel):
    id: int
    video_id: int
    title: str
    hook: str
    script: str
    duration_seconds: int
    score: Optional[float] = None
    style: ShortStyle
    status: ShortStatus
    video_url: Optional[str] = None
    sources: List[ShortSourceResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ShortListResponse(BaseModel):
    total: int
    items: List[ShortResponse]


class ShortGenerateResponse(BaseModel):
    video_id: int
    status: str
    generated_count: int
    shorts: List[ShortResponse]


# LLM Structured Output Parsing Schemas
class LLMMomentCandidate(BaseModel):
    moment_summary: str
    chunk_id: int
    start_time: float
    end_time: float
    score: float = Field(..., ge=0, le=100)
    hook_idea: str
    reason: str


class LLMMomentsResponse(BaseModel):
    moments: List[LLMMomentCandidate]


class LLMScriptItem(BaseModel):
    title: str
    hook: str
    script: str
    duration_seconds: int
    score: float = Field(..., ge=0, le=100)
    sources: List[ShortSourceInput]


class LLMScriptsResponse(BaseModel):
    shorts: List[LLMScriptItem]
