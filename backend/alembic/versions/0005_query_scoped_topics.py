"""Store query-scoped topics and their content memberships.

Revision ID: 0005_query_scoped_topics
Revises: 0004_backfill_title_candidates
Create Date: 2026-10-01
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005_query_scoped_topics"
down_revision: str | None = "0004_backfill_title_candidates"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "topics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("query", sa.String(length=200), nullable=False),
        sa.Column("normalized_query", sa.String(length=200), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("title_key", sa.String(length=64), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "normalized_query",
            "title_key",
            "event_date",
            name="uq_topics_query_title_date",
        ),
    )
    op.create_table(
        "topic_contents",
        sa.Column(
            "topic_id",
            sa.Integer(),
            sa.ForeignKey("topics.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "content_id",
            sa.Integer(),
            sa.ForeignKey("contents.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
        sa.Column("relevance", sa.Float(), nullable=True),
        sa.Column("relationship_type", sa.String(length=32), nullable=False),
    )
    op.create_index("ix_topic_contents_content_id", "topic_contents", ["content_id"])


def downgrade() -> None:
    op.drop_index("ix_topic_contents_content_id", table_name="topic_contents")
    op.drop_table("topic_contents")
    op.drop_table("topics")
