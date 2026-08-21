import json
from typing import Any, Dict, List
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def insert_transcript_chunks(
    session: AsyncSession,
    video_id: int,
    chunks_data: List[Dict[str, Any]],
    embeddings: List[List[float]],
) -> List[int]:
    """
    Inserts chunk records along with their vector embeddings.
    Uses async session and direct parameter binding for pgvector.
    """
    inserted_ids: List[int] = []
    
    for chunk, emb in zip(chunks_data, embeddings):
        # Format embedding as pgvector string representation: '[0.1, 0.2, ...]'
        emb_str = f"[{','.join(map(str, emb))}]"
        
        query = text(
            """
            INSERT INTO transcript_chunks (video_id, chunk_index, start_time, end_time, text, embedding, created_at, updated_at)
            VALUES (:video_id, :chunk_index, :start_time, :end_time, :text, :embedding::vector, now(), now())
            RETURNING id;
            """
        )
        
        result = await session.execute(
            query,
            {
                "video_id": video_id,
                "chunk_index": chunk["chunk_index"],
                "start_time": chunk["start_time"],
                "end_time": chunk["end_time"],
                "text": chunk["text"],
                "embedding": emb_str,
            },
        )
        row = result.fetchone()
        if row:
            inserted_ids.append(row[0])

    await session.commit()
    return inserted_ids


async def search_similar_chunks(
    session: AsyncSession,
    video_id: int,
    query_embedding: List[float],
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """
    Searches for most similar chunks for a specific video using cosine similarity (<=>).
    """
    emb_str = f"[{','.join(map(str, query_embedding))}]"
    
    query = text(
        """
        SELECT id, video_id, chunk_index, start_time, end_time, text,
               1 - (embedding <=> :query_embedding::vector) AS similarity
        FROM transcript_chunks
        WHERE video_id = :video_id AND embedding IS NOT NULL
        ORDER BY embedding <=> :query_embedding::vector ASC
        LIMIT :limit;
        """
    )
    
    result = await session.execute(
        query,
        {
            "video_id": video_id,
            "query_embedding": emb_str,
            "limit": limit,
        },
    )
    
    rows = result.fetchall()
    return [
        {
            "id": row.id,
            "video_id": row.video_id,
            "chunk_index": row.chunk_index,
            "start_time": row.start_time,
            "end_time": row.end_time,
            "text": row.text,
            "similarity": float(row.similarity),
        }
        for row in rows
    ]
