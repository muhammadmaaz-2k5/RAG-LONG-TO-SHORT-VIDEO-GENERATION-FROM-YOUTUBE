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

    raw_snippets: List[Dict[str, float | str]] = []
    
    try:
        # 1. Try modern API (v1.2+): YouTubeTranscriptApi().fetch(...) or YouTubeTranscriptApi.fetch(...)
        api_obj = YouTubeTranscriptApi() if callable(YouTubeTranscriptApi) else YouTubeTranscriptApi
        
        if hasattr(api_obj, "fetch"):
            fetched = api_obj.fetch(youtube_id, languages=languages)
            raw_snippets = [
                {"text": s.text, "start": float(s.start), "duration": float(s.duration)}
                for s in fetched
            ]
        elif hasattr(api_obj, "get_transcript"):
            raw_snippets = api_obj.get_transcript(youtube_id, languages=languages)
        elif hasattr(YouTubeTranscriptApi, "list_transcripts"):
            transcript_list = YouTubeTranscriptApi.list_transcripts(youtube_id)
            try:
                transcript = transcript_list.find_transcript(languages)
            except Exception:
                first_transcript = next(iter(transcript_list))
                transcript = first_transcript.translate("en") if first_transcript.is_translatable else first_transcript
            raw_snippets = transcript.fetch()
            
    except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable) as e:
        raise TranscriptFetchError(f"Transcript unavailable for video {youtube_id}: {str(e)}") from e
    except Exception as e:
        # Fallback to fetching any available language
        try:
            api_obj = YouTubeTranscriptApi() if callable(YouTubeTranscriptApi) else YouTubeTranscriptApi
            if hasattr(api_obj, "fetch"):
                fetched = api_obj.fetch(youtube_id)
                raw_snippets = [
                    {"text": s.text, "start": float(s.start), "duration": float(s.duration)}
                    for s in fetched
                ]
            elif hasattr(api_obj, "get_transcript"):
                raw_snippets = api_obj.get_transcript(youtube_id)
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
