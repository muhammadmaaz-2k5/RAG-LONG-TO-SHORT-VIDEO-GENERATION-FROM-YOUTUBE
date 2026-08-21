import logging
from typing import Any, Dict, Optional
import cloudinary
import cloudinary.uploader

from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize Cloudinary if credentials are present
if settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY and settings.CLOUDINARY_API_SECRET:
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )


def upload_thumbnail(image_url_or_path: str, video_id: int) -> str:
    """
    Uploads a YouTube or custom thumbnail to Cloudinary.
    Falls back to original URL if Cloudinary is not configured.
    """
    if not (settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY):
        logger.warning("Cloudinary credentials not configured. Using raw thumbnail URL.")
        return image_url_or_path

    try:
        result = cloudinary.uploader.upload(
            image_url_or_path,
            folder="youtube-shorts-ai/thumbnails",
            public_id=f"video_{video_id}",
            overwrite=True,
        )
        return result.get("secure_url", image_url_or_path)
    except Exception as e:
        logger.error(f"Failed to upload thumbnail to Cloudinary: {e}")
        return image_url_or_path


def upload_rendered_short(file_path: str, short_id: int) -> Dict[str, Any]:
    """
    Uploads a rendered MP4 short to Cloudinary with automatic video transformation and thumbnail creation.
    """
    if not (settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY):
        raise ValueError("Cloudinary credentials are required for video uploads.")

    result = cloudinary.uploader.upload(
        file_path,
        resource_type="video",
        folder="youtube-shorts-ai/shorts",
        public_id=f"short_{short_id}",
        overwrite=True,
    )

    thumbnail_url = cloudinary.CloudinaryImage(result["public_id"]).build_url(
        resource_type="video", format="jpg"
    )

    return {
        "url": result.get("secure_url"),
        "duration": result.get("duration"),
        "thumbnail": thumbnail_url,
    }
