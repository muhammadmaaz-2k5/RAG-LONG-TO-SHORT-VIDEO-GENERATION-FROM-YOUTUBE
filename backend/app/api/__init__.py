from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.shorts import router as shorts_router
from app.api.videos import router as videos_router

api_router = APIRouter(prefix="/api")
api_router.include_router(health_router)
api_router.include_router(videos_router)
api_router.include_router(shorts_router)

__all__ = ["api_router"]
