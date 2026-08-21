import re
from typing import Optional, Tuple
import requests


YOUTUBE_ID_PATTERNS = [
    r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
    r"(?:youtu\.be\/)([0-9A-Za-z_-]{11})",
    r"(?:youtube\.com\/shorts\/)([0-9A-Za-z_-]{11})",
    r"(?:youtube\.com\/embed\/)([0-9A-Za-z_-]{11})",
]


def extract_youtube_id(url: str) -> Optional[str]:
    """Extract 11-character YouTube video ID from various URL formats."""
    if not url:
        return None
    url = url.strip()
    
    # If the input is already just an 11-char ID
    if re.fullmatch(r"[0-9A-Za-z_-]{11}", url):
        return url

    for pattern in YOUTUBE_ID_PATTERNS:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def fetch_youtube_metadata(youtube_id: str) -> Tuple[Optional[str], Optional[str], str]:
    """
    Fetch title, channel_name, and high-res thumbnail URL using YouTube oEmbed.
    Falls back gracefully if network is unavailable or oEmbed fails.
    """
    video_url = f"https://www.youtube.com/watch?v=video_id"
    default_thumbnail = f"https://img.youtube.com/vi/{youtube_id}/hqdefault.jpg"
    
    title: Optional[str] = None
    channel_name: Optional[str] = None
    thumbnail_url: str = default_thumbnail

    try:
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={youtube_id}&format=json"
        response = requests.get(oembed_url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            title = data.get("title")
            channel_name = data.get("author_name")
            thumbnail_url = data.get("thumbnail_url") or default_thumbnail
    except Exception:
        # Graceful fallback to default thumbnail and empty title
        pass

    return title, channel_name, thumbnail_url
