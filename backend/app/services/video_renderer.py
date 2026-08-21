"""
Video Rendering & Trimming Service.
Downloads YouTube video clips via yt-dlp, trims with FFmpeg to 9:16 vertical Short format,
and uploads to Cloudinary.
"""
import os
import subprocess
import tempfile
import asyncio
from typing import Optional, Tuple
import imageio_ffmpeg
import yt_dlp
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.short import Short, ShortStatus
from app.models.short_source import ShortSource
from app.models.video import Video
from app.services.cloudinary_service import upload_rendered_short


def get_ffmpeg_path() -> str:
    """Returns the absolute path to the FFmpeg executable."""
    return imageio_ffmpeg.get_ffmpeg_exe()


def download_youtube_clip(youtube_url: str, output_path: str) -> str:
    """
    Downloads a lightweight video stream (360p) from YouTube to a local file using yt-dlp.
    Optimized for blazing-fast download in 1-2 seconds.
    """
    ffmpeg_exe = get_ffmpeg_path()
    ydl_opts = {
        # 360p format for lightning-fast download speed:
        "format": "best[height<=360][ext=mp4]/bestvideo[height<=360]+bestaudio/best[height<=360]/best",
        # "format": "best[ext=mp4]/bestvideo[height<=720]+bestaudio/best[height<=720]/best", # 720p option
        "outtmpl": output_path,
        "ffmpeg_location": ffmpeg_exe,
        "quiet": True,
        "no_warnings": True,
        "merge_output_format": "mp4",
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])
    return output_path


def trim_and_format_short_video(
    input_file: str,
    output_file: str,
    start_time: float,
    duration: float,
    vertical: bool = True,
) -> str:
    """
    Trims a video clip from start_time with target duration and converts to 9:16 vertical format (360x640).
    Uses ultrafast preset and multi-threading for instant sub-second rendering.
    """
    ffmpeg_exe = get_ffmpeg_path()

    # 9:16 vertical crop filter (360x640 is blazing fast on cloud servers)
    if vertical:
        video_filter = (
            "scale=360:640:force_original_aspect_ratio=increase,"
            "crop=360:640:(in_w-360)/2:(in_h-640)/2"
        )
    else:
        video_filter = "scale=360:640:force_original_aspect_ratio=decrease,pad=360:640:(360-iw)/2:(640-ih)/2:black"

    cmd = [
        ffmpeg_exe,
        "-y",
        "-ss", f"{start_time:.3f}",
        "-i", input_file,
        "-t", f"{duration:.3f}",
        "-vf", video_filter,
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-threads", "0",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        output_file,
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        # Fallback without complex crop if aspect ratio fails
        simple_cmd = [
            ffmpeg_exe,
            "-y",
            "-ss", f"{start_time:.3f}",
            "-i", input_file,
            "-t", f"{duration:.3f}",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-threads", "0",
            "-c:a", "aac",
            output_file,
        ]
        fallback_res = subprocess.run(simple_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if fallback_res.returncode != 0:
            raise RuntimeError(f"FFmpeg trim failed: {result.stderr or fallback_res.stderr}")

    return output_file


async def render_short_video(
    session: AsyncSession,
    short_id: int,
) -> Tuple[Short, str]:
    """
    Orchestrates full trimming, vertical 9:16 rendering, and Cloudinary upload for a Short.
    """
    stmt = (
        select(Short)
        .where(Short.id == short_id)
        .options(
            selectinload(Short.video),
            selectinload(Short.sources).selectinload(ShortSource.chunk),
        )
    )
    result = await session.execute(stmt)
    short = result.scalar_one_or_none()

    if not short:
        raise ValueError(f"Short with ID {short_id} not found.")

    if not short.video:
        raise ValueError("Short has no associated video parent.")

    youtube_url = f"https://www.youtube.com/watch?v={short.video.youtube_id}"

    # Determine start time and duration from sources
    start_time = 0.0
    duration = float(short.duration_seconds or 15.0)

    if short.sources:
        first_source = min(short.sources, key=lambda s: s.start_time)
        start_time = first_source.start_time
        # Duration can be calculated from source or target
        source_span = max(s.end_time for s in short.sources) - start_time
        if source_span > 0:
            duration = min(duration, source_span)

    with tempfile.TemporaryDirectory() as temp_dir:
        raw_video_path = os.path.join(temp_dir, f"source_{short.video.youtube_id}.mp4")
        trimmed_video_path = os.path.join(temp_dir, f"short_{short_id}_9x16.mp4")

        # 1. Download in worker thread (fast 720p stream)
        await asyncio.to_thread(download_youtube_clip, youtube_url, raw_video_path)

        # 2. Trim and crop to 9:16 in worker thread (ultrafast preset)
        await asyncio.to_thread(
            trim_and_format_short_video,
            raw_video_path,
            trimmed_video_path,
            start_time,
            duration,
        )

        # 3. Upload to Cloudinary with preset "maazka"
        cloudinary_res = await asyncio.to_thread(
            upload_rendered_short,
            trimmed_video_path,
            short_id,
        )

        secure_url = cloudinary_res.get("url") or cloudinary_res.get("secure_url")
        if not secure_url:
            raise RuntimeError("Cloudinary upload failed: No secure URL returned.")

        # 4. Save video URL and mark ready
        short.video_url = secure_url
        short.status = ShortStatus.READY
        await session.commit()

        # Re-fetch cleanly
        refreshed = await session.execute(
            select(Short)
            .where(Short.id == short_id)
            .options(selectinload(Short.sources))
        )
        return refreshed.scalar_one(), secure_url
