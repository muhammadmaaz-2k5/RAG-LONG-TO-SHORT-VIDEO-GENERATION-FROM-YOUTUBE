from sqlalchemy import Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class ShortSource(Base, TimestampMixin):
    __tablename__ = "short_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    short_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("shorts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    chunk_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("transcript_chunks.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    start_time: Mapped[float] = mapped_column(Float, nullable=False)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)

    # Relationships
    short: Mapped["Short"] = relationship("Short", back_populates="sources")
    chunk: Mapped["TranscriptChunk"] = relationship("TranscriptChunk", back_populates="sources")
