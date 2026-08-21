import logging
import os
import tempfile
from typing import Dict, List, Optional, Tuple
import groq
import imageio_ffmpeg
import yt_dlp
from youtube_transcript_api import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
    YouTubeTranscriptApi,
)

from app.core.config import settings

logger = logging.getLogger(__name__)


class TranscriptFetchError(Exception):
    """Raised when transcript cannot be fetched or transcribed."""
    pass


def transcribe_youtube_audio_with_whisper(
    youtube_id: str,
) -> Tuple[List[Dict[str, float | str]], str, float]:
    """
    Fallback audio transcription using yt-dlp + Groq Whisper API (whisper-large-v3-turbo).
    Used when YouTube closed captions are disabled by the video owner.
    """
    logger.info(f"Falling back to Groq Whisper AI transcription for video: {youtube_id}")
    youtube_url = f"https://www.youtube.com/watch?v={youtube_id}"
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    with tempfile.TemporaryDirectory() as temp_dir:
        ydl_opts = {
            "format": "bestaudio[ext=m4a]/bestaudio/best",
            "outtmpl": os.path.join(temp_dir, "audio.%(ext)s"),
            "ffmpeg_location": ffmpeg_exe,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "64",
                }
            ],
            "quiet": True,
            "no_warnings": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])

        mp3_files = [f for f in os.listdir(temp_dir) if f.endswith(".mp3")]
        if not mp3_files:
            raise TranscriptFetchError(f"Could not extract audio for video {youtube_id}")

        mp3_path = os.path.join(temp_dir, mp3_files[0])

        client = groq.Groq(api_key=settings.GROQ_API_KEY)
        with open(mp3_path, "rb") as audio_file:
            transcript_res = client.audio.transcriptions.create(
                file=(mp3_files[0], audio_file.read()),
                model="whisper-large-v3-turbo",
                response_format="verbose_json",
            )

        segments = (
            getattr(transcript_res, "segments", None)
            or (transcript_res.get("segments", []) if isinstance(transcript_res, dict) else [])
        )

        if not segments:
            # Fallback to single text block if segments missing
            full_text = getattr(transcript_res, "text", "") or ""
            return [{"text": full_text, "start": 0.0, "duration": 30.0}], full_text, 30.0

        raw_snippets: List[Dict[str, float | str]] = []
        full_text_parts = []
        total_duration = 0.0

        for seg in segments:
            seg_dict = seg if isinstance(seg, dict) else seg.__dict__
            text = seg_dict.get("text", "").strip()
            start = float(seg_dict.get("start", 0.0))
            end = float(seg_dict.get("end", start + 3.0))
            duration = max(0.5, end - start)

            if text:
                raw_snippets.append({"text": text, "start": start, "duration": duration})
                full_text_parts.append(text)
                total_duration = max(total_duration, end)

        full_text = " ".join(full_text_parts)
        return raw_snippets, full_text, total_duration


def fetch_youtube_transcript(
    youtube_id: str, languages: Optional[List[str]] = None
) -> Tuple[List[Dict[str, float | str]], str, float]:
    """
    Fetches the video transcript using youtube-transcript-api.
    If subtitles are disabled or unavailable, automatically falls back to Groq Whisper AI transcription.
    """
    if languages is None:
        languages = ["en", "en-US", "en-GB", "a.en"]

    raw_snippets: List[Dict[str, float | str]] = []

    try:
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
                transcript = (
                    first_transcript.translate("en")
                    if first_transcript.is_translatable
                    else first_transcript
                )
            raw_snippets = transcript.fetch()

    except Exception as e:
        logger.warning(
            f"YouTube captions unavailable for {youtube_id} ({e}). Switching to Groq Whisper AI fallback."
        )
        try:
            return transcribe_youtube_audio_with_whisper(youtube_id)
        except Exception as whisper_err:
            raise TranscriptFetchError(
                f"Transcript and Whisper transcription failed for {youtube_id}: {str(whisper_err)}"
            ) from whisper_err

    if not raw_snippets:
        # If empty snippets, try Whisper fallback
        try:
            return transcribe_youtube_audio_with_whisper(youtube_id)
        except Exception as whisper_err:
            raise TranscriptFetchError(f"Empty transcript returned for video {youtube_id}") from whisper_err

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
