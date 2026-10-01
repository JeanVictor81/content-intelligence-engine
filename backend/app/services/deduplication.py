"""Conservative duplicate detection that keeps each collected source record."""

import re
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from difflib import SequenceMatcher
from html import unescape
from typing import Literal
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from app.models import Content, Source
from app.services.normalization import NormalizedRSSItem

DuplicateMatchType = Literal["exact_url", "source_external_id", "similar_title_candidate"]

SIMILAR_TITLE_THRESHOLD = 0.92
SIMILAR_TITLE_MIN_LENGTH = 30
SIMILAR_TITLE_PUBLICATION_WINDOW = timedelta(hours=48)
TRACKING_QUERY_KEYS = frozenset({"fbclid", "gclid", "oc"})


@dataclass(frozen=True, slots=True)
class DuplicateMatch:
    """A duplicate or reviewable similarity match and its canonical record."""

    canonical_content: Content
    match_type: DuplicateMatchType
    similarity: float


def find_duplicate(
    item: NormalizedRSSItem, source: Source, candidates: list[Content]
) -> DuplicateMatch | None:
    """Find the strongest exact match or conservative same-time title candidate."""
    item_url = canonicalize_url(item.content.url)
    item_source_key = (source.platform, source.base_url)
    item_title = normalize_title(item.content.title)
    matches: list[DuplicateMatch] = []

    for candidate in candidates:
        canonical_content = candidate.duplicate_of or candidate
        if canonicalize_url(candidate.url) == item_url:
            matches.append(DuplicateMatch(canonical_content, "exact_url", 1.0))
            continue

        candidate_source = candidate.source
        candidate_source_key = (candidate_source.platform, candidate_source.base_url)
        if (
            item.content.external_id
            and item.content.external_id == candidate.external_id
            and item_source_key == candidate_source_key
        ):
            matches.append(DuplicateMatch(canonical_content, "source_external_id", 1.0))
            continue

        candidate_title = normalize_title(candidate.title)
        if (
            not item_title
            or len(item_title) < SIMILAR_TITLE_MIN_LENGTH
            or len(candidate_title) < SIMILAR_TITLE_MIN_LENGTH
            or not _published_close(item.content.published_at, candidate.published_at)
        ):
            continue

        similarity = SequenceMatcher(None, item_title, candidate_title, autojunk=False).ratio()
        if similarity >= SIMILAR_TITLE_THRESHOLD:
            matches.append(
                DuplicateMatch(
                    canonical_content,
                    "similar_title_candidate",
                    round(similarity, 4),
                )
            )

    if not matches:
        return None

    priority = {"exact_url": 3, "source_external_id": 2, "similar_title_candidate": 1}
    return max(
        matches,
        key=lambda match: (
            priority[match.match_type],
            match.similarity,
            -(match.canonical_content.id or 0),
        ),
    )


def canonicalize_url(url: str) -> str:
    """Remove fragments and common tracking parameters without changing the path."""
    parsed = urlsplit(url)
    query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.casefold().startswith("utm_") and key.casefold() not in TRACKING_QUERY_KEYS
    ]
    path = parsed.path.rstrip("/") or "/"
    return urlunsplit(
        (
            parsed.scheme.casefold(),
            parsed.netloc.casefold(),
            path,
            urlencode(query, doseq=True),
            "",
        )
    )


def normalize_title(title: str | None) -> str:
    """Normalize markup, Unicode and punctuation for conservative title matching."""
    if not title:
        return ""
    normalized = unicodedata.normalize("NFKC", unescape(title)).casefold()
    return " ".join(re.findall(r"\w+", normalized))


def _published_close(first: datetime | None, second: datetime | None) -> bool:
    if first is None or second is None:
        return False
    first_utc = first.replace(tzinfo=UTC) if first.tzinfo is None else first.astimezone(UTC)
    second_utc = second.replace(tzinfo=UTC) if second.tzinfo is None else second.astimezone(UTC)
    return abs(first_utc - second_utc) <= SIMILAR_TITLE_PUBLICATION_WINDOW
