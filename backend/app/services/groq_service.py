import json
import logging
from typing import Any, Dict, List
from groq import AsyncGroq

from app.core.config import settings
from app.prompts.moments import (
    MOMENT_FINDER_SYSTEM_PROMPT,
    build_moment_finder_user_prompt,
)
from app.prompts.shorts import (
    SHORTS_WRITER_SYSTEM_PROMPT,
    build_shorts_writer_user_prompt,
)
from app.schemas.short import (
    LLMMomentCandidate,
    LLMMomentsResponse,
    LLMScriptItem,
    LLMScriptsResponse,
)

logger = logging.getLogger(__name__)


def get_groq_client() -> AsyncGroq:
    """Instantiates an AsyncGroq client using settings."""
    if not settings.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not configured in settings or environment variables.")
    return AsyncGroq(api_key=settings.GROQ_API_KEY)


async def find_viral_moments(
    chunks: List[Dict[str, Any]],
    count: int = 5,
    style: str = "VIRAL",
) -> List[LLMMomentCandidate]:
    """
    Stage 1: Analyzes transcript chunks with Groq LLM to identify and rank candidate moments.
    """
    client = get_groq_client()
    user_prompt = build_moment_finder_user_prompt(chunks=chunks, count=count, style=style)

    try:
        response = await client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": MOMENT_FINDER_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.4,
        )

        content = response.choices[0].message.content
        data = json.loads(content)
        parsed = LLMMomentsResponse.model_validate(data)
        return parsed.moments
    except Exception as e:
        logger.error(f"Error in find_viral_moments: {e}", exc_info=True)
        raise RuntimeError(f"Failed to extract viral moments from LLM: {str(e)}") from e


async def write_short_scripts(
    selected_moments: List[Dict[str, Any]],
    source_chunks: List[Dict[str, Any]],
    duration_seconds: int = 60,
    style: str = "VIRAL",
) -> List[LLMScriptItem]:
    """
    Stage 2: Generates complete Hook -> Context -> Main -> Payoff -> CTA scripts.
    """
    client = get_groq_client()
    user_prompt = build_shorts_writer_user_prompt(
        selected_moments=selected_moments,
        source_chunks=source_chunks,
        duration_seconds=duration_seconds,
        style=style,
    )

    try:
        response = await client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": SHORTS_WRITER_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.6,
        )

        content = response.choices[0].message.content
        data = json.loads(content)
        parsed = LLMScriptsResponse.model_validate(data)
        return parsed.shorts
    except Exception as e:
        logger.error(f"Error in write_short_scripts: {e}", exc_info=True)
        raise RuntimeError(f"Failed to generate Short scripts from LLM: {str(e)}") from e
