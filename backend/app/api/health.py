from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db

router = APIRouter(prefix="/health", tags=["Health"])


@router.api_route("", methods=["GET", "HEAD"], summary="Health Check")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Performs a system and database connectivity health check.
    """
    db_status = "healthy"
    is_ok = True
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        is_ok = False

    return {
        "status": "ok" if is_ok else "degraded",
        "database": db_status,
        "environment": settings.ENVIRONMENT,
        "embedding_model": settings.EMBEDDING_MODEL,
        "embedding_dimensions": settings.EMBEDDING_DIMENSIONS,
    }
