"""Initial schema with pgvector, enums, tables, and HNSW index

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-20 18:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
from pgvector.sqlalchemy import Vector
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 2. Enums
    video_status_enum = postgresql.ENUM(
        "PENDING", "PROCESSING", "READY", "FAILED", name="video_status"
    )
    video_status_enum.create(op.get_bind(), checkfirst=True)

    short_status_enum = postgresql.ENUM(
        "GENERATING", "READY", "FAILED", name="short_status"
    )
    short_status_enum.create(op.get_bind(), checkfirst=True)

    short_style_enum = postgresql.ENUM(
        "VIRAL", "EDUCATIONAL", "STORYTELLING", "NEWS", "MOTIVATIONAL", "CONTROVERSIAL", name="short_style"
    )
    short_style_enum.create(op.get_bind(), checkfirst=True)

    # 3. Create 'videos' table
    op.create_table(
        "videos",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("youtube_id", sa.String(length=32), nullable=False, unique=True),
        sa.Column("youtube_url", sa.String(length=500), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=True),
        sa.Column("channel_name", sa.String(length=255), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("thumbnail_url", sa.String(length=1000), nullable=True),
        sa.Column("transcript_text", sa.Text(), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(name="video_status", create_type=False),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_videos_youtube_id", "videos", ["youtube_id"])

    # 4. Create 'transcript_chunks' table
    op.create_table(
        "transcript_chunks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("video_id", sa.Integer(), sa.ForeignKey("videos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Float(), nullable=False),
        sa.Column("end_time", sa.Float(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(384), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_transcript_chunks_video_id", "transcript_chunks", ["video_id"])

    # Create HNSW index for cosine distance similarity
    op.execute(
        "CREATE INDEX transcript_chunks_embedding_idx ON transcript_chunks USING hnsw (embedding vector_cosine_ops);"
    )

    # 5. Create 'shorts' table
    op.create_table(
        "shorts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("video_id", sa.Integer(), sa.ForeignKey("videos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("hook", sa.Text(), nullable=False),
        sa.Column("script", sa.Text(), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column(
            "style",
            postgresql.ENUM(name="short_style", create_type=False),
            nullable=False,
            server_default="VIRAL",
        ),
        sa.Column(
            "status",
            postgresql.ENUM(name="short_status", create_type=False),
            nullable=False,
            server_default="GENERATING",
        ),
        sa.Column("video_url", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_shorts_video_id", "shorts", ["video_id"])

    # 6. Create 'short_sources' table
    op.create_table(
        "short_sources",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("short_id", sa.Integer(), sa.ForeignKey("shorts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_id", sa.Integer(), sa.ForeignKey("transcript_chunks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("start_time", sa.Float(), nullable=False),
        sa.Column("end_time", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_short_sources_short_id", "short_sources", ["short_id"])
    op.create_index("idx_short_sources_chunk_id", "short_sources", ["chunk_id"])


def downgrade() -> None:
    op.drop_table("short_sources")
    op.drop_table("shorts")
    op.execute("DROP INDEX IF EXISTS transcript_chunks_embedding_idx;")
    op.drop_table("transcript_chunks")
    op.drop_table("videos")

    op.execute("DROP TYPE IF EXISTS short_style;")
    op.execute("DROP TYPE IF EXISTS short_status;")
    op.execute("DROP TYPE IF EXISTS video_status;")
