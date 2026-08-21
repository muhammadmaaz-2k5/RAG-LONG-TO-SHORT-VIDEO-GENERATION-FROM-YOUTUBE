from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.short import Short
from app.models.transcript_chunk import TranscriptChunk
from app.models.video import Video, VideoStatus
from app.schemas.video import (
    TranscriptChunkResponse,
    VideoCreate,
    VideoDetailResponse,
    VideoProcessResponse,
    VideoResponse,
)
from app.services.chunker import chunk_transcript
from app.services.cloudinary_service import upload_thumbnail
from app.services.embeddings import generate_embeddings_batch
from app.services.transcript import TranscriptFetchError, fetch_youtube_transcript
from app.services.vector_store import insert_transcript_chunks
from app.services.youtube import extract_youtube_id, fetch_youtube_metadata

router = APIRouter(prefix="/videos", tags=["Videos"])


@router.post("", response_model=VideoResponse, status_code=status.HTTP_201_CREATED, summary="Submit YouTube Video")
async def create_video(payload: VideoCreate, db: AsyncSession = Depends(get_db)):
    """
    Submits a YouTube URL, extracts the video ID, fetches oEmbed metadata,
    and initializes a new Video entry with PENDING status.
    """
    youtube_id = extract_youtube_id(payload.youtube_url)
    if not youtube_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid YouTube URL provided. Could not extract 11-character video ID.",
        )

    # Check if video already exists
    existing = await db.execute(select(Video).where(Video.youtube_id == youtube_id))
    video = existing.scalar_one_or_none()
    if video:
        return video

    # Fetch metadata & thumbnail
    title, channel_name, raw_thumbnail = fetch_youtube_metadata(youtube_id)

    # Create Video record
    video = Video(
        youtube_id=youtube_id,
        youtube_url=payload.youtube_url,
        title=title,
        channel_name=channel_name,
        thumbnail_url=raw_thumbnail,
        status=VideoStatus.PENDING,
    )
    db.add(video)
    await db.commit()
    await db.refresh(video)

    # Upload thumbnail to Cloudinary if configured
    if raw_thumbnail:
        cloudinary_thumb = upload_thumbnail(raw_thumbnail, video.id)
        if cloudinary_thumb != raw_thumbnail:
            video.thumbnail_url = cloudinary_thumb
            await db.commit()
            await db.refresh(video)

    return video


@router.get("", response_model=List[VideoResponse], summary="List Videos")
async def list_videos(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Lists all submitted videos with pagination."""
    query = select(Video).order_by(Video.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/{video_id}", response_model=VideoDetailResponse, summary="Get Video Details")
async def get_video(video_id: int, db: AsyncSession = Depends(get_db)):
    """Fetches details for a specific video including chunk count and status."""
    query = (
        select(Video)
        .where(Video.id == video_id)
        .options(selectinload(Video.chunks), selectinload(Video.shorts))
    )
    result = await db.execute(query)
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video with ID {video_id} not found.",
        )

    # Prepare response with counts
    detail = VideoDetailResponse.model_validate(video)
    detail.chunk_count = len(video.chunks)
    detail.shorts_count = len(video.shorts)
    detail.chunks = [
        TranscriptChunkResponse(
            id=c.id,
            video_id=c.video_id,
            chunk_index=c.chunk_index,
            start_time=c.start_time,
            end_time=c.end_time,
            text=c.text,
            has_embedding=(c.embedding is not None),
            created_at=c.created_at,
        )
        for c in video.chunks
    ]
    return detail


@router.post("/{video_id}/process", response_model=VideoProcessResponse, summary="Process Video Transcript")
async def process_video(video_id: int, db: AsyncSession = Depends(get_db)):
    """
    Synchronously processes a video:
    1. Fetches YouTube transcript
    2. Cleans and chunks into 80-150 word segments with exact timestamps
    3. Generates 384-dim vector embeddings for each chunk
    4. Persists chunks + vectors in PostgreSQL (pgvector)
    5. Marks video as READY
    """
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video with ID {video_id} not found.",
        )

    # Update status to PROCESSING
    video.status = VideoStatus.PROCESSING
    await db.commit()

    try:
        # 1. Fetch transcript
        snippets, full_text, duration = fetch_youtube_transcript(video.youtube_id)
        video.transcript_text = full_text
        video.duration_seconds = int(duration)

        # 2. Chunk transcript
        chunks_data = chunk_transcript(snippets, min_words=80, max_words=150)
        if not chunks_data:
            raise ValueError("Transcript chunking produced 0 chunks.")

        # 3. Generate embeddings
        chunk_texts = [c["text"] for c in chunks_data]
        embeddings = generate_embeddings_batch(chunk_texts)

        # 4. Remove previous chunks if reprocessing
        await db.execute(
            TranscriptChunk.__table__.delete().where(TranscriptChunk.video_id == video_id)
        )
        await db.commit()

        # 5. Insert chunks and embeddings into Neon Postgres vector store
        chunk_ids = await insert_transcript_chunks(
            session=db,
            video_id=video_id,
            chunks=chunks_data,
            embeddings=embeddings,
        )

        # 6. Mark READY
        video.status = VideoStatus.READY
        await db.commit()
        await db.refresh(video)

        return VideoProcessResponse(
            id=video.id,
            youtube_id=video.youtube_id,
            status=video.status,
            chunks_created=len(chunk_ids),
            message="Video processed successfully with timestamp-aware chunks and vector embeddings.",
        )

    except Exception as e:
        await db.rollback()
        # Cleanly update status to FAILED
        video_rec = (await db.execute(select(Video).where(Video.id == video_id))).scalar_one_or_none()
        if video_rec:
            video_rec.status = VideoStatus.FAILED
            await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Video processing failed: {str(e)}",
        )


@router.get("/{video_id}/chunks", response_model=List[TranscriptChunkResponse], summary="Inspect Transcript Chunks")
async def get_video_chunks(video_id: int, db: AsyncSession = Depends(get_db)):
    """Fetches all stored chunks and timestamps for a video."""
    result = await db.execute(
        select(TranscriptChunk)
        .where(TranscriptChunk.video_id == video_id)
        .order_by(TranscriptChunk.chunk_index.asc())
    )
    chunks = result.scalars().all()
    return [
        TranscriptChunkResponse(
            id=c.id,
            video_id=c.video_id,
            chunk_index=c.chunk_index,
            start_time=c.start_time,
            end_time=c.end_time,
            text=c.text,
            has_embedding=(c.embedding is not None),
            created_at=c.created_at,
        )
        for c in chunks
    ]
