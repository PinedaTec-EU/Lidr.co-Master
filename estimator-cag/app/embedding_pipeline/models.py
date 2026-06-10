from __future__ import annotations

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.embedding_pipeline.db import Base


class DocumentRecord(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source_path: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    metadata_json: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        server_default="{}",
        nullable=False,
    )

    chunks: Mapped[list["ChunkRecord"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class ChunkRecord(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        server_default="{}",
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    document: Mapped[DocumentRecord] = relationship(back_populates="chunks")
