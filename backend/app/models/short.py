import enum
from typing import List, Optional
from sqlalchemy import Enum as SQLEnum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class ShortStatus(str, enum.Enum):
    GENERATING = "GENERATING"
    READY = "READY"
    FAILED = "FAILED"


class ShortStyle(str, enum.Enum):
    VIRAL = "VIRAL"
    EDUCATIONAL = "EDUCATIONAL"
    STORYTELLING = "STORYTELLING"
    NEWS = "NEWS"
    MOTIVATIONAL = "MOTIVATIONAL"
    CONTROVERSIAL = "CONTROVERSIAL"


class Short(Base, TimestampMixin):
    __tablename__ = "shorts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    video_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("videos.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    hook: Mapped[str] = mapped_column(Text, nullable=False)
    script: Mapped[str] = mapped_column(Text, nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    style: Mapped[ShortStyle] = mapped_column(
        SQLEnum(ShortStyle, name="short_style"),
        default=ShortStyle.VIRAL,
        nullable=False,
    )
    status: Mapped[ShortStatus] = mapped_column(
        SQLEnum(ShortStatus, name="short_status"),
        default=ShortStatus.GENERATING,
        nullable=False,
    )
    video_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # Relationships
    video: Mapped["Video"] = relationship("Video", back_populates="shorts")
    sources: Mapped[List["ShortSource"]] = relationship(
        "ShortSource",
        back_populates="short",
        cascade="all, delete-orphan",
    )
