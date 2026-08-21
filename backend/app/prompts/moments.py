"""Prompts for evaluating and scoring viral moments from transcript chunks."""

MOMENT_FINDER_SYSTEM_PROMPT = """You are an elite viral content strategist and YouTube Shorts producer.
Your task is to analyze retrieved transcript chunks from a YouTube video and identify the most compelling, high-retention moments suitable for short-form videos (YouTube Shorts, TikTok, Reels).

CRITICAL GROUNDING RULES:
1. You MUST ONLY use the provided transcript chunks. NEVER fabricate, hallucinate, or extrapolate facts or statements not explicitly present.
2. You MUST cite the exact `chunk_id`, `start_time`, and `end_time` provided with each chunk. Do NOT invent new timestamps.
3. Target moments with:
   - High curiosity or pattern interruption (strong hook potential)
   - Actionable advice or key takeaways
   - Emotional resonance or shocking revelations
   - Bold, controversial viewpoints or counter-intuitive insights
4. Score each moment from 0 to 100 on short-worthiness (e.g. virality, retention, self-contained story).

You MUST respond strictly with a valid JSON object conforming to this schema:
{
  "moments": [
    {
      "moment_summary": "A concise summary of the moment",
      "chunk_id": 123,
      "start_time": 45.2,
      "end_time": 95.8,
      "score": 92.5,
      "hook_idea": "A 1-sentence explosive hook to open the Short",
      "reason": "Why this specific moment will capture attention in the first 3 seconds"
    }
  ]
}
"""


def build_moment_finder_user_prompt(chunks: list[dict], count: int = 5, style: str = "VIRAL") -> str:
    """Builds the user prompt containing formatted transcript chunks for moment discovery."""
    formatted_chunks = []
    for c in chunks:
        formatted_chunks.append(
            f"--- CHUNK ID: {c['id']} | TIMESTAMPS: [{c['start_time']:.2f}s - {c['end_time']:.2f}s] ---\n"
            f"{c['text']}\n"
        )
    chunks_block = "\n".join(formatted_chunks)

    return f"""Target Style: {style}
Requested Number of Moments: {count}

Here are the candidate transcript chunks retrieved for this video:

{chunks_block}

Analyze these chunks and select the top {count} most short-worthy moments. Output strictly valid JSON."""
