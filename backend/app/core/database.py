import urllib.parse
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


def normalize_async_db_url(url: str) -> str:
    """Normalizes postgres connection string for asyncpg driver, converting sslmode and query params."""
    if not url:
        return url
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)

    parsed = urllib.parse.urlparse(url)
    if parsed.query:
        query_params = urllib.parse.parse_qs(parsed.query)
        # asyncpg accepts 'ssl' instead of 'sslmode'
        if "sslmode" in query_params:
            ssl_val = query_params.pop("sslmode")[0]
            if ssl_val in ("require", "verify-ca", "verify-full", "prefer"):
                query_params["ssl"] = ["require"]
        query_params.pop("channel_binding", None)
        new_query = urllib.parse.urlencode(query_params, doseq=True)
        url = urllib.parse.urlunparse(parsed._replace(query=new_query))
    return url


# Normalize database URL for asyncpg
db_url = normalize_async_db_url(settings.DATABASE_URL)

# Async engine creation
engine: AsyncEngine = create_async_engine(
    db_url,
    echo=(settings.LOG_LEVEL.upper() == "DEBUG"),
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Async session factory
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an async database session per request."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
