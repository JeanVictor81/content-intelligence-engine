"""Persisted topics and their links to collected content."""

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.content import Content


class Topic(Base):
    """A query-scoped group of content items about one specific event or subject."""

    __tablename__ = "topics"
    __table_args__ = (
        UniqueConstraint(
            "normalized_query", "title_key", "event_date", name="uq_topics_query_title_date"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    query: Mapped[str] = mapped_column(String(200), nullable=False)
    normalized_query: Mapped[str] = mapped_column(String(200), nullable=False)
    title: Mapped[str | None] = mapped_column(Text)
    title_key: Mapped[str] = mapped_column(String(64), nullable=False)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    content_links: Mapped[list["TopicContent"]] = relationship(back_populates="topic")


class TopicContent(Base):
    """Association between a topic and a preserved source content record."""

    __tablename__ = "topic_contents"
    __table_args__ = (Index("ix_topic_contents_content_id", "content_id"),)

    topic_id: Mapped[int] = mapped_column(
        ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True
    )
    content_id: Mapped[int] = mapped_column(
        ForeignKey("contents.id", ondelete="RESTRICT"), primary_key=True
    )
    relevance: Mapped[float | None] = mapped_column(Float)
    relationship_type: Mapped[str] = mapped_column(String(32), nullable=False)

    topic: Mapped[Topic] = relationship(back_populates="content_links")
    content: Mapped["Content"] = relationship()
