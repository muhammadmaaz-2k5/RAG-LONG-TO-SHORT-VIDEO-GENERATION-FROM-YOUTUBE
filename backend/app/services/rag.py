from typing import Any, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.embeddings import generate_embedding
from app.services.vector_store import search_similar_chunks

RAG_RETRIEVAL_ANGLES = [
    "most surprising moments and shocking statements",
    "most useful practical advice and actionable tips",
    "most emotional stories and compelling personal experiences",
    "most controversial opinions and strong debates",
    "unexpected facts, secrets, and mind-blowing revelations",
]


async def retrieve_short_worthy_chunks(
    session: AsyncSession,
    video_id: int,
    top_per_angle: int = 4,
    max_total_chunks: int = 15,
) -> List[Dict[str, Any]]:
    """
    Executes a multi-query retrieval strategy across 5 viral angles,
    merges the candidate chunks, deduplicates them by ID, and ranks them.
    """
    candidate_map: Dict[int, Dict[str, Any]] = {}

    for angle in RAG_RETRIEVAL_ANGLES:
        angle_embedding = generate_embedding(angle)
        similar_chunks = await search_similar_chunks(
            session=session,
            video_id=video_id,
            query_embedding=angle_embedding,
            limit=top_per_angle,
        )

        for chunk in similar_chunks:
            cid = chunk["id"]
            if cid not in candidate_map:
                candidate_map[cid] = {**chunk, "angles_matched": [angle], "max_similarity": chunk["similarity"]}
            else:
                candidate_map[cid]["angles_matched"].append(angle)
                if chunk["similarity"] > candidate_map[cid]["max_similarity"]:
                    candidate_map[cid]["max_similarity"] = chunk["similarity"]

    # Sort deduplicated candidates primarily by max similarity and diversity of angle matches
    deduped_candidates = list(candidate_map.values())
    deduped_candidates.sort(
        key=lambda c: (len(c["angles_matched"]), c["max_similarity"]),
        reverse=True,
    )

    return deduped_candidates[:max_total_chunks]
