from typing import Dict, List, Optional, Tuple
from youtube_transcript_api import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
    YouTubeTranscriptApi,
)


class TranscriptFetchError(Exception):
    """Raised when transcript cannot be fetched."""
    pass


def fetch_youtube_transcript(
    youtube_id: str, languages: Optional[List[str]] = None
) -> Tuple[List[Dict[str, float | str]], str, float]:
    """
    Fetches the video transcript using youtube-transcript-api.

    Returns:
        Tuple of:
        - raw_snippets: List of dicts with 'text', 'start', and 'duration'
        - full_text: Combined string of all transcript snippets
        - total_duration: Estimated duration from last snippet end
    """
    if languages is None:
        languages = ["en", "en-US", "en-GB", "a.en"]

    try:
        # Try fetching using specified or default language preference
        transcript_list = YouTubeTranscriptApi.list_transcripts(youtube_id)
        
        # Try finding requested language or auto-generated
        try:
            transcript = transcript_list.find_transcript(languages)
        except Exception:
            # Fall back to finding any manually created or generated transcript
            try:
                transcript = transcript_list.find_generated_transcript(languages)
            except Exception:
                # Pick the first available transcript and translate if necessary
                first_transcript = next(iter(transcript_list))
                if first_transcript.is_translatable:
                    transcript = first_transcript.translate("en")
                else:
                    transcript = first_transcript

        raw_snippets = transcript.fetch()
        
    except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable) as e:
        raise TranscriptFetchError(f"Transcript unavailable for video {youtube_id}: {str(e)}") from e
    except Exception as e:
        # Direct fallback attempt with get_transcript
        try:
            raw_snippets = YouTubeTranscriptApi.get_transcript(youtube_id, languages=languages)
        except Exception as inner_e:
            raise TranscriptFetchError(
                f"Failed to retrieve transcript for {youtube_id}: {str(inner_e)}"
            ) from inner_e

    if not raw_snippets:
        raise TranscriptFetchError(f"Empty transcript returned for video {youtube_id}")

    # Build full text and compute duration
    full_text_parts = []
    total_duration = 0.0

    for snippet in raw_snippets:
        text = snippet.get("text", "").strip()
        if text:
            full_text_parts.append(text)
        start = float(snippet.get("start", 0.0))
        duration = float(snippet.get("duration", 0.0))
        total_duration = max(total_duration, start + duration)

    full_text = " ".join(full_text_parts)
    return raw_snippets, full_text, total_duration
