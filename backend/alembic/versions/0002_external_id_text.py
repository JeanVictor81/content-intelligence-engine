"""Allow source-native external identifiers longer than 512 characters.

Revision ID: 0002_external_id_text
Revises: 0001_sources_contents
Create Date: 2026-10-01
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_external_id_text"
down_revision: str | None = "0001_sources_contents"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "contents",
        "external_id",
        existing_type=sa.String(length=512),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM contents
                WHERE external_id IS NOT NULL AND length(external_id) > 512
            ) THEN
                RAISE EXCEPTION
                    'Cannot downgrade external_id to VARCHAR(512): values exceed 512 characters';
            END IF;
        END $$;
        """
    )
    op.alter_column(
        "contents",
        "external_id",
        existing_type=sa.Text(),
        type_=sa.String(length=512),
        existing_nullable=True,
    )
