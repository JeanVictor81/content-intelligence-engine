"""Convert connector-native records into the shared source/content shape."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from time import struct_time
from typing import Any
from urllib.parse import urlsplit

from app.connectors.rss import RSSFeedItem


class NormalizationError(ValueError):
    """A connector item does not contain the minimum data required to normalize it."""


@dataclass(frozen=True, slots=True)
class NormalizedSource:
    """Source fields shared with the Source database model."""

    name: str
    platform: str
    base_url: str
    source_type: str


@dataclass(frozen=True, slots=True)
class NormalizedContent:
    """Content fields shared with the Content database model."""

    external_id: str | None
    url: str
    title: str | None
    text_excerpt: str | None
    author: str | None
    published_at: datetime | None
    metadata: dict[str, Any]


@dataclass(frozen=True, slots=True)
class NormalizedRSSItem:
    """A normalized RSS item, split into its source and content records."""

    source: NormalizedSource
    content: NormalizedContent


def normalize_rss_item(item: RSSFeedItem) -> NormalizedRSSItem:
    """Convert an RSS entry to fields compatible with the Source and Content models.

    Missing optional feed fields remain ``None``. Collection time is left to the
    database's server default when this normalized content is later persisted.
    """
    entry = item.raw_entry
    url = _optional_text(entry.get("link"))
    if url is None or not _is_absolute_http_url(url):
        raise NormalizationError("RSS entry must have an absolute HTTP or HTTPS URL.")

    title = _optional_text(entry.get("title"))
    excerpt = _optional_text(entry.get("summary")) or _optional_text(entry.get("description"))
    author = _optional_text(entry.get("author"))
    external_id = _optional_text(entry.get("id")) or _optional_text(entry.get("guid"))
    published_at = _publication_datetime(entry)

    return NormalizedRSSItem(
        source=NormalizedSource(
            name=item.feed.name,
            platform="rss",
            base_url=item.feed.url,
            source_type="feed",
        ),
        content=NormalizedContent(
            external_id=external_id,
            url=url,
            title=title,
            text_excerpt=excerpt,
            author=author,
            published_at=published_at,
            metadata={"connector": "rss"},
        ),
    )


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _is_absolute_http_url(value: str) -> bool:
    parsed = urlsplit(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _publication_datetime(entry: Mapping[str, Any]) -> datetime | None:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if isinstance(parsed, struct_time):
        return datetime(*parsed[:6], tzinfo=UTC)

    raw_date = _optional_text(entry.get("published")) or _optional_text(entry.get("updated"))
    if raw_date is None:
        return None
    try:
        result = parsedate_to_datetime(raw_date)
    except (TypeError, ValueError, OverflowError):
        return None
    if result.tzinfo is None:
        return result.replace(tzinfo=UTC)
    return result.astimezone(UTC)
