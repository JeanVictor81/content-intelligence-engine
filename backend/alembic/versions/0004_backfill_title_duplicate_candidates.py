"""Backfill conservative title-similarity candidates in existing content.

Revision ID: 0004_backfill_title_candidates
Revises: 0003_content_deduplication
Create Date: 2026-10-01
"""

import re
import unicodedata
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from difflib import SequenceMatcher
from html import unescape

import sqlalchemy as sa

from alembic import op

revision: str = "0004_backfill_title_candidates"
down_revision: str | None = "0003_content_deduplication"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SIMILARITY_THRESHOLD = 0.92
MIN_TITLE_LENGTH = 30
PUBLICATION_WINDOW = timedelta(hours=48)


def _normalize_title(title: str | None) -> str:
    if not title:
        return ""
    normalized = unicodedata.normalize("NFKC", unescape(title)).casefold()
    return " ".join(re.findall(r"\w+", normalized))


def _published_close(first: datetime | None, second: datetime | None) -> bool:
    if first is None or second is None:
        return False
    first_utc = first.replace(tzinfo=UTC) if first.tzinfo is None else first.astimezone(UTC)
    second_utc = second.replace(tzinfo=UTC) if second.tzinfo is None else second.astimezone(UTC)
    return abs(first_utc - second_utc) <= PUBLICATION_WINDOW


def upgrade() -> None:
    connection = op.get_bind()
    rows = connection.execute(
        sa.text("SELECT id, title, published_at, duplicate_of_id FROM contents ORDER BY id")
    ).mappings()
    previous: list[dict[str, object]] = []

    for row in rows:
        title = _normalize_title(row["title"])
        published_at = row["published_at"]
        duplicate_of_id = row["duplicate_of_id"]

        if duplicate_of_id is None and len(title) >= MIN_TITLE_LENGTH:
            matches: list[tuple[float, int]] = []
            for candidate in previous:
                candidate_title = candidate["title"]
                candidate_date = candidate["published_at"]
                if (
                    isinstance(candidate_title, str)
                    and len(candidate_title) >= MIN_TITLE_LENGTH
                    and isinstance(candidate_date, datetime)
                    and isinstance(published_at, datetime)
                    and _published_close(published_at, candidate_date)
                ):
                    similarity = SequenceMatcher(
                        None, title, candidate_title, autojunk=False
                    ).ratio()
                    if similarity >= SIMILARITY_THRESHOLD:
                        matches.append((similarity, int(candidate["canonical_id"])))

            if matches:
                similarity, canonical_id = max(matches, key=lambda match: (match[0], -match[1]))
                connection.execute(
                    sa.text(
                        "UPDATE contents "
                        "SET duplicate_of_id=:canonical_id, "
                        "duplicate_match_type='similar_title_candidate', "
                        "duplicate_similarity=:similarity "
                        "WHERE id=:content_id AND duplicate_of_id IS NULL"
                    ),
                    {
                        "canonical_id": canonical_id,
                        "similarity": round(similarity, 4),
                        "content_id": row["id"],
                    },
                )
                duplicate_of_id = canonical_id

        previous.append(
            {
                "title": title,
                "published_at": published_at,
                "canonical_id": duplicate_of_id or row["id"],
            }
        )


def downgrade() -> None:
    """Keep additive candidate links so new runtime decisions are not erased."""
