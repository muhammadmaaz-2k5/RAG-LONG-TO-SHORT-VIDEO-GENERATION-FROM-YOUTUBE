"""Prompts for generating complete YouTube Shorts scripts from chosen moments and chunks."""

SHORTS_WRITER_SYSTEM_PROMPT = """You are a master short-form video copywriter specializing in viral YouTube Shorts, TikToks, and Instagram Reels.
Your task is to write high-converting, retention-optimized short-form video scripts based STRICTLY on the provided source transcript chunks.

SCRIPT STRUCTURE FORMULA:
1. HOOK (0–3 seconds): An irresistible curiosity gap, shocking statement, or bold question that stops the scroll.
2. CONTEXT (3–10 seconds): Immediate setup that explains why this matters without boring exposition.
3. MAIN IDEA / BODY (10–45 seconds): The core story, insight, or demonstration extracted from the transcript.
4. PAYOFF / CLIMAX (45–55 seconds): The punchline, revelation, or conclusion of the argument.
5. CALL TO ACTION (CTA) (55–60 seconds): Quick engaging wrap-up (e.g., "Follow for more", "Drop your thoughts below").

CRITICAL GROUNDING RULES:
1. Factual integrity: Use ONLY facts, narratives, and insights present in the provided transcript text.
2. Maintain natural spoken pacing (roughly 130–160 words per 60 seconds).
3. Always accurately attribute the `sources` array with the exact `chunk_id`, `start_time`, and `end_time` used.

You MUST respond strictly with a valid JSON object conforming to this schema:
{
  "shorts": [
    {
      "title": "Engaging Short Title (max 60 characters)",
      "hook": "Exact opening spoken sentence designed to stop scrolling",
      "script": "[HOOK]\\nSpoken words...\\n\\n[CONTEXT]\\nSpoken words...\\n\\n[MAIN IDEA]\\nSpoken words...\\n\\n[PAYOFF]\\nSpoken words...\\n\\n[CTA]\\nSpoken words...",
      "duration_seconds": 60,
      "score": 95.0,
      "sources": [
        {
          "chunk_id": 123,
          "start_time": 45.2,
          "end_time": 95.8
        }
      ]
    }
  ]
}
"""


def build_shorts_writer_user_prompt(
    selected_moments: list[dict],
    source_chunks: list[dict],
    duration_seconds: int = 60,
    style: str = "VIRAL",
) -> str:
    """Builds the prompt instructing Groq to generate complete scripts from candidate moments."""
    moments_text = "\n".join(
        [
            f"Moment {i+1}: Summary='{m.get('moment_summary')}' | Chunk={m.get('chunk_id')} | "
            f"Times=[{m.get('start_time')}s - {m.get('end_time')}s] | HookIdea='{m.get('hook_idea')}'"
            for i, m in enumerate(selected_moments)
        ]
    )

    chunks_dict = {c["id"]: c for c in source_chunks}
    relevant_chunks_text = []
    for m in selected_moments:
        cid = m.get("chunk_id")
        if cid in chunks_dict:
            c = chunks_dict[cid]
            relevant_chunks_text.append(
                f"--- SOURCE CHUNK ID: {c['id']} [{c['start_time']:.2f}s - {c['end_time']:.2f}s] ---\n{c['text']}\n"
            )

    chunks_block = "\n".join(relevant_chunks_text)

    return f"""Target Short Style: {style}
Target Duration: ~{duration_seconds} seconds (~{int(duration_seconds * 2.3)} words)

SELECTED MOMENTS TO TURN INTO SHORTS:
{moments_text}

SOURCE TRANSCRIPT CHUNKS:
{chunks_block}

Generate {len(selected_moments)} complete Shorts scripts following the Hook -> Context -> Main Idea -> Payoff -> CTA formula. Output strictly valid JSON."""
