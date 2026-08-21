"""
pgvector storage and similarity search service.
Handles embedding insertion and cosine distance searches.
"""
from typing import List, Dict, Any, Optional
import math
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.transcript_chunk import TranscriptChunk


async def insert_transcript_chunks(
    session: AsyncSession,
    video_id: int,
    chunks: List[Dict[str, Any]],
    embeddings: List[List[float]],
) -> List[int]:
    """
    Inserts transcript chunks with pgvector embeddings into Neon PostgreSQL.
    """
    if len(chunks) != len(embeddings):
        raise ValueError(
            f"Chunks count ({len(chunks)}) does not match embeddings count ({len(embeddings)})"
        )

    chunk_models: List[TranscriptChunk] = []
    for chunk, emb in zip(chunks, embeddings):
        chunk_obj = TranscriptChunk(
            video_id=video_id,
            chunk_index=chunk["chunk_index"],
            start_time=float(chunk["start_time"]),
            end_time=float(chunk["end_time"]),
            text=chunk["text"],
            embedding=emb,
        )
        chunk_models.append(chunk_obj)

    session.add_all(chunk_models)
    await session.flush()
    return [c.id for c in chunk_models]


async def search_similar_chunks(
    session: AsyncSession,
    video_id: int,
    query_embedding: List[float],
    limit: int = 5,
    min_similarity: float = 0.0,
) -> List[Dict[str, Any]]:
    """
    Searches for transcript chunks most similar to a query embedding using pgvector cosine distance.
    """
    distance_expr = TranscriptChunk.embedding.cosine_distance(query_embedding)
    stmt = (
        select(TranscriptChunk, distance_expr.label("distance"))
        .where(
            TranscriptChunk.video_id == video_id,
            TranscriptChunk.embedding.isnot(None),
        )
        .order_by(distance_expr.asc())
        .limit(limit)
    )

    result = await session.execute(stmt)
    rows = result.all()

    formatted_results = []
    for chunk, distance in rows:
        sim = 1.0 - float(distance) if distance is not None and not math.isnan(distance) else 0.0
        if sim >= min_similarity:
            formatted_results.append({
                "id": chunk.id,
                "video_id": chunk.video_id,
                "chunk_index": chunk.chunk_index,
                "start_time": chunk.start_time,
                "end_time": chunk.end_time,
                "text": chunk.text,
                "similarity": round(sim, 4),
            })

    return formatted_results
