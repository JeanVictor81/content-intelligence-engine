"""Collected content model."""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.source import Source


class Content(Base):
    """A collected item with its source and available publication metadata."""

    __tablename__ = "contents"
    __table_args__ = (
        Index("ix_contents_source_id", "source_id"),
        Index("ix_contents_duplicate_of_id", "duplicate_of_id"),
        CheckConstraint(
            "duplicate_of_id IS NULL OR duplicate_of_id <> id",
            name="ck_contents_not_duplicate_of_self",
        ),
        CheckConstraint(
            "duplicate_similarity IS NULL OR "
            "(duplicate_similarity >= 0 AND duplicate_similarity <= 1)",
            name="ck_contents_duplicate_similarity_range",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(
        ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False
    )
    external_id: Mapped[str | None] = mapped_column(Text)
    duplicate_of_id: Mapped[int | None] = mapped_column(
        ForeignKey("contents.id", ondelete="RESTRICT")
    )
    duplicate_match_type: Mapped[str | None] = mapped_column(String(32))
    duplicate_similarity: Mapped[float | None] = mapped_column(Float)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(Text)
    text_excerpt: Mapped[str | None] = mapped_column(Text)
    author: Mapped[str | None] = mapped_column(String(500))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    content_hash: Mapped[str | None] = mapped_column(String(128))
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB)

    source: Mapped["Source"] = relationship(back_populates="contents")
    duplicate_of: Mapped["Content | None"] = relationship(
        back_populates="duplicates", remote_side="Content.id"
    )
    duplicates: Mapped[list["Content"]] = relationship(back_populates="duplicate_of")
