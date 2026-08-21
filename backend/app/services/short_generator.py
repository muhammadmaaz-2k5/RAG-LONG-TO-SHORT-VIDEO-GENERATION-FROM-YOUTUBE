import logging
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.short import Short, ShortStatus, ShortStyle
from app.models.short_source import ShortSource
from app.models.video import Video, VideoStatus
from app.services.groq_service import find_viral_moments, write_short_scripts
from app.services.rag import retrieve_short_worthy_chunks

logger = logging.getLogger(__name__)


async def generate_shorts_for_video(
    session: AsyncSession,
    video_id: int,
    count: int = 5,
    duration_seconds: int = 60,
    style: ShortStyle = ShortStyle.VIRAL,
) -> List[Short]:
    """
    End-to-end Shorts generation orchestration:
    1. Verify video is in READY state
    2. RAG multi-angle candidate chunk retrieval
    3. Groq Stage 1: Moment extraction & virality scoring
    4. Groq Stage 2: Script generation (Hook -> Context -> Main -> Payoff -> CTA)
    5. Database persistence for Shorts and ShortSources
    """
    # 1. Verify Video
    video_res = await session.execute(select(Video).where(Video.id == video_id))
    video = video_res.scalar_one_or_none()
    if not video:
        raise ValueError(f"Video with ID {video_id} not found.")
    if video.status != VideoStatus.READY:
        raise ValueError(f"Video {video_id} is not in READY state (current status: {video.status.value}).")

    # 2. RAG Retrieval
    candidate_chunks = await retrieve_short_worthy_chunks(
        session=session,
        video_id=video_id,
        top_per_angle=4,
        max_total_chunks=15,
    )
    if not candidate_chunks:
        raise ValueError(f"No transcript chunks found with embeddings for video {video_id}.")

    # 3. Groq Stage 1: Moment Finding
    raw_moments = await find_viral_moments(
        chunks=candidate_chunks,
        count=count,
        style=style.value,
    )

    moments_dicts = [m.model_dump() for m in raw_moments]

    # 4. Groq Stage 2: Script Writing
    script_items = await write_short_scripts(
        selected_moments=moments_dicts,
        source_chunks=candidate_chunks,
        duration_seconds=duration_seconds,
        style=style.value,
    )

    # 5. Persist to Database
    created_shorts: List[Short] = []

    for item in script_items:
        short_record = Short(
            video_id=video_id,
            title=item.title,
            hook=item.hook,
            script=item.script,
            duration_seconds=item.duration_seconds or duration_seconds,
            score=item.score,
            style=style,
            status=ShortStatus.READY,
        )
        session.add(short_record)
        await session.flush()  # populate short_record.id

        # Add source records
        for src in item.sources:
            source_record = ShortSource(
                short_id=short_record.id,
                chunk_id=src.chunk_id,
                start_time=src.start_time,
                end_time=src.end_time,
            )
            session.add(source_record)

        created_shorts.append(short_record)

    await session.commit()

    # Re-fetch with loaded sources
    short_ids = [s.id for s in created_shorts]
    result = await session.execute(
        select(Short)
        .where(Short.id.in_(short_ids))
        .options(selectinload(Short.sources))
    )
    return list(result.scalars().all())


async def regenerate_single_short(
    session: AsyncSession,
    short_id: int,
    style: Optional[ShortStyle] = None,
    duration_seconds: Optional[int] = None,
) -> Short:
    """
    Re-runs script generation for a specific Short using its existing source chunks or refreshed RAG candidates.
    """
    result = await session.execute(
        select(Short)
        .where(Short.id == short_id)
        .options(selectinload(Short.sources).selectinload(ShortSource.chunk))
    )
    short = result.scalar_one_or_none()
    if not short:
        raise ValueError(f"Short with ID {short_id} not found.")

    target_style = style or short.style
    target_duration = duration_seconds or short.duration_seconds

    # Fetch candidate chunks from existing sources or video
    source_chunks = []
    for s in short.sources:
        if s.chunk:
            source_chunks.append(
                {
                    "id": s.chunk.id,
                    "start_time": s.start_time,
                    "end_time": s.end_time,
                    "text": s.chunk.text,
                }
            )

    # Fallback to RAG if short had no attached chunks
    if not source_chunks:
        source_chunks = await retrieve_short_worthy_chunks(
            session=session,
            video_id=short.video_id,
            top_per_angle=3,
            max_total_chunks=8,
        )

    # Stage 1: find refreshed moment
    moments = await find_viral_moments(chunks=source_chunks, count=1, style=target_style.value)
    moments_dicts = [m.model_dump() for m in moments]

    # Stage 2: generate script
    scripts = await write_short_scripts(
        selected_moments=moments_dicts,
        source_chunks=source_chunks,
        duration_seconds=target_duration,
        style=target_style.value,
    )

    if not scripts:
        raise RuntimeError("Failed to regenerate script from LLM.")

    chosen_script = scripts[0]

    # Update short record
    short.title = chosen_script.title
    short.hook = chosen_script.hook
    short.script = chosen_script.script
    short.duration_seconds = chosen_script.duration_seconds or target_duration
    short.score = chosen_script.score
    short.style = target_style
    short.status = ShortStatus.READY

    await session.commit()
    
    # Re-query eagerly with relationships to prevent MissingGreenlet on serialization
    refreshed_res = await session.execute(
        select(Short)
        .where(Short.id == short_id)
        .options(selectinload(Short.sources))
    )
    return refreshed_res.scalar_one()
