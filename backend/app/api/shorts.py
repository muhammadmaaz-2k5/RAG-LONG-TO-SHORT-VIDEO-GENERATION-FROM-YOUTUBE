from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.short import Short, ShortStatus, ShortStyle
from app.models.short_source import ShortSource
from app.schemas.short import (
    ShortGenerateRequest,
    ShortGenerateResponse,
    ShortListResponse,
    ShortRegenerateRequest,
    ShortResponse,
)
from app.services.short_generator import generate_shorts_for_video, regenerate_single_short

router = APIRouter(prefix="/shorts", tags=["Shorts"])


@router.post("/generate", response_model=ShortGenerateResponse, status_code=status.HTTP_201_CREATED, summary="Generate Shorts via RAG & LLM")
async def generate_shorts(payload: ShortGenerateRequest, db: AsyncSession = Depends(get_db)):
    """
    Runs multi-query RAG search on the video transcript, discovers viral moments with Groq,
    and writes structured Short scripts (Hook -> Context -> Main -> Payoff -> CTA).
    """
    try:
        shorts = await generate_shorts_for_video(
            session=db,
            video_id=payload.video_id,
            count=payload.count,
            duration_seconds=payload.duration,
            style=payload.style,
        )

        return ShortGenerateResponse(
            video_id=payload.video_id,
            status="GENERATED",
            generated_count=len(shorts),
            shorts=[ShortResponse.model_validate(s) for s in shorts],
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Short generation pipeline failed: {str(e)}",
        )


@router.get("", response_model=ShortListResponse, summary="List Shorts")
async def list_shorts(
    video_id: Optional[int] = Query(None, description="Filter by video ID"),
    style: Optional[ShortStyle] = Query(None, description="Filter by style"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Lists generated Shorts with filtering and pagination."""
    query = (
        select(Short)
        .options(selectinload(Short.sources))
        .order_by(Short.created_at.desc())
    )

    if video_id is not None:
        query = query.where(Short.video_id == video_id)
    if style is not None:
        query = query.where(Short.style == style)

    # Execute total count & page query
    result = await db.execute(query.offset(skip).limit(limit))
    shorts = result.scalars().all()

    return ShortListResponse(
        total=len(shorts),
        items=[ShortResponse.model_validate(s) for s in shorts],
    )


@router.get("/{short_id}", response_model=ShortResponse, summary="Get Single Short")
async def get_short(short_id: int, db: AsyncSession = Depends(get_db)):
    """Fetches a single Short script along with its exact source timestamp chunk citations."""
    query = (
        select(Short)
        .where(Short.id == short_id)
        .options(selectinload(Short.sources))
    )
    result = await db.execute(query)
    short = result.scalar_one_or_none()
    if not short:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Short with ID {short_id} not found.",
        )
    return ShortResponse.model_validate(short)


@router.post("/{short_id}/regenerate", response_model=ShortResponse, summary="Regenerate Short Script")
async def regenerate_short(
    short_id: int,
    payload: Optional[ShortRegenerateRequest] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Re-runs Groq script generation for a specific Short without reprocessing the entire video.
    """
    try:
        updated_short = await regenerate_single_short(
            session=db,
            short_id=short_id,
            style=payload.style if payload else None,
            duration_seconds=payload.duration if payload else None,
        )
        return ShortResponse.model_validate(updated_short)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Short regeneration failed: {str(e)}",
        )


@router.post("/{short_id}/render", response_model=ShortResponse, summary="Render and Trim Short Video")
async def render_short(
    short_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Downloads source video, trims exact Short timestamps, crops to 9:16 vertical MP4,
    and uploads to Cloudinary.
    """
    from app.services.video_renderer import render_short_video
    try:
        updated_short, video_url = await render_short_video(
            session=db,
            short_id=short_id,
        )
        return ShortResponse.model_validate(updated_short)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Short video rendering failed: {str(e)}",
        )
