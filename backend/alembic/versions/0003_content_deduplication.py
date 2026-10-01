"""Record duplicate relationships without deleting source records.

Revision ID: 0003_content_deduplication
Revises: 0002_external_id_text
Create Date: 2026-10-01
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_content_deduplication"
down_revision: str | None = "0002_external_id_text"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("contents", sa.Column("duplicate_of_id", sa.Integer(), nullable=True))
    op.add_column(
        "contents", sa.Column("duplicate_match_type", sa.String(length=32), nullable=True)
    )
    op.add_column("contents", sa.Column("duplicate_similarity", sa.Float(), nullable=True))
    op.create_foreign_key(
        "fk_contents_duplicate_of_id_contents",
        "contents",
        "contents",
        ["duplicate_of_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index("ix_contents_duplicate_of_id", "contents", ["duplicate_of_id"])
    op.create_check_constraint(
        "ck_contents_not_duplicate_of_self",
        "contents",
        "duplicate_of_id IS NULL OR duplicate_of_id <> id",
    )
    op.create_check_constraint(
        "ck_contents_duplicate_similarity_range",
        "contents",
        "duplicate_similarity IS NULL OR (duplicate_similarity >= 0 AND duplicate_similarity <= 1)",
    )
    op.create_check_constraint(
        "ck_contents_duplicate_fields_consistent",
        "contents",
        "(duplicate_of_id IS NULL AND duplicate_match_type IS NULL "
        "AND duplicate_similarity IS NULL) OR "
        "(duplicate_of_id IS NOT NULL AND duplicate_match_type IS NOT NULL "
        "AND duplicate_similarity IS NOT NULL)",
    )
    op.create_check_constraint(
        "ck_contents_duplicate_match_type",
        "contents",
        "duplicate_match_type IS NULL OR duplicate_match_type IN "
        "('exact_url', 'source_external_id', 'similar_title_candidate')",
    )
    op.execute(
        """
        WITH ranked AS (
            SELECT id,
                   first_value(id) OVER (PARTITION BY url ORDER BY id) AS canonical_id,
                   row_number() OVER (PARTITION BY url ORDER BY id) AS duplicate_rank
            FROM contents
        )
        UPDATE contents AS duplicate
        SET duplicate_of_id = ranked.canonical_id,
            duplicate_match_type = 'exact_url',
            duplicate_similarity = 1.0
        FROM ranked
        WHERE duplicate.id = ranked.id AND ranked.duplicate_rank > 1;
        """
    )
    op.execute(
        """
        WITH ranked AS (
            SELECT id, source_id,
                   first_value(id) OVER (
                       PARTITION BY source_id, external_id ORDER BY id
                   ) AS canonical_id,
                   row_number() OVER (
                       PARTITION BY source_id, external_id ORDER BY id
                   ) AS duplicate_rank
            FROM contents
            WHERE external_id IS NOT NULL
        )
        UPDATE contents AS duplicate
        SET duplicate_of_id = COALESCE(canonical.duplicate_of_id, ranked.canonical_id),
            duplicate_match_type = 'source_external_id',
            duplicate_similarity = 1.0
        FROM ranked
        JOIN contents AS canonical ON canonical.id = ranked.canonical_id
        WHERE duplicate.id = ranked.id
          AND ranked.duplicate_rank > 1
          AND duplicate.duplicate_of_id IS NULL;
        """
    )


def downgrade() -> None:
    op.drop_constraint("ck_contents_duplicate_match_type", "contents", type_="check")
    op.drop_constraint("ck_contents_duplicate_fields_consistent", "contents", type_="check")
    op.drop_constraint("ck_contents_duplicate_similarity_range", "contents", type_="check")
    op.drop_constraint("ck_contents_not_duplicate_of_self", "contents", type_="check")
    op.drop_index("ix_contents_duplicate_of_id", table_name="contents")
    op.drop_constraint("fk_contents_duplicate_of_id_contents", "contents", type_="foreignkey")
    op.drop_column("contents", "duplicate_similarity")
    op.drop_column("contents", "duplicate_match_type")
    op.drop_column("contents", "duplicate_of_id")
