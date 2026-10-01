"""Offline tests for RSS-to-common-model normalization."""

from datetime import UTC, datetime
from pathlib import Path

import feedparser
import pytest

from app.connectors.rss import RSSFeed, RSSFeedItem
from app.services.normalization import NormalizationError, normalize_rss_item

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "rss_sample.xml"
FEED = RSSFeed(name="Sample Esports Feed", url="https://news.example/feed.xml")


def fixture_item() -> RSSFeedItem:
    parsed = feedparser.parse(FIXTURE_PATH.read_bytes())
    return RSSFeedItem(feed=FEED, raw_entry=parsed.entries[0])


def test_normalizes_feed_source_and_entry_fields() -> None:
    result = normalize_rss_item(fixture_item())

    assert result.source.name == "Sample Esports Feed"
    assert result.source.platform == "rss"
    assert result.source.base_url == FEED.url
    assert result.source.source_type == "feed"
    assert result.content.external_id == "cblol-schedule-1"
    assert result.content.url == "https://news.example/cblol-schedule"
    assert result.content.title == "CBLOL announces a new match schedule"
    assert result.content.text_excerpt == "The league published its upcoming schedule."
    assert result.content.author == "Editor A"
    assert result.content.published_at == datetime(2026, 9, 29, 12, 0, tzinfo=UTC)
    assert result.content.metadata == {"connector": "rss"}


def test_optional_fields_remain_absent() -> None:
    item = RSSFeedItem(
        feed=FEED,
        raw_entry={"link": "https://news.example/item", "title": "  "},
    )

    result = normalize_rss_item(item)

    assert result.content.title is None
    assert result.content.text_excerpt is None
    assert result.content.author is None
    assert result.content.external_id is None
    assert result.content.published_at is None


@pytest.mark.parametrize("url", [None, "", "/relative", "ftp://news.example/item"])
def test_rejects_missing_or_non_http_item_url(url: str | None) -> None:
    item = RSSFeedItem(feed=FEED, raw_entry={"link": url})

    with pytest.raises(NormalizationError, match="absolute HTTP or HTTPS URL"):
        normalize_rss_item(item)


def test_invalid_publication_date_remains_absent() -> None:
    item = RSSFeedItem(
        feed=FEED,
        raw_entry={"link": "https://news.example/item", "published": "not a date"},
    )

    assert normalize_rss_item(item).content.published_at is None
