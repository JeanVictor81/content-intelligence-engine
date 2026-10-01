"""Tests for conservative URL and title based duplicate matching."""

from datetime import UTC, datetime

from app.connectors.rss import RSSFeed, RSSFeedItem
from app.models import Content, Source
from app.services.deduplication import canonicalize_url, find_duplicate
from app.services.normalization import normalize_rss_item

FEED = RSSFeed(name="First Feed", url="https://news.example/feed.xml")
SOURCE = Source(id=1, name=FEED.name, platform="rss", base_url=FEED.url, source_type="feed")


def make_item(
    *,
    url: str = "https://news.example/story",
    title: str = "A long headline about the central bank and interest rates",
    external_id: str = "source-item-1",
    published_at: datetime | None = datetime(2026, 10, 1, 12, tzinfo=UTC),
):
    entry = {
        "link": url,
        "title": title,
        "guid": external_id,
        "published_parsed": published_at.timetuple() if published_at else None,
    }
    return normalize_rss_item(RSSFeedItem(feed=FEED, raw_entry=entry))


def make_content(
    *,
    id: int = 1,
    source: Source = SOURCE,
    url: str = "https://news.example/story",
    title: str = "A long headline about the central bank and interest rates",
    external_id: str = "source-item-1",
    published_at: datetime | None = datetime(2026, 10, 1, 12, tzinfo=UTC),
) -> Content:
    return Content(
        id=id,
        source=source,
        url=url,
        title=title,
        external_id=external_id,
        published_at=published_at,
    )


def test_canonicalize_url_removes_tracking_and_fragment_only() -> None:
    assert (
        canonicalize_url("HTTPS://News.Example/story/?utm_source=feed&category=finance#top")
        == "https://news.example/story?category=finance"
    )


def test_exact_canonical_url_matches_across_sources() -> None:
    second_source = Source(
        id=2,
        name="Second Feed",
        platform="rss",
        base_url="https://another.example/feed.xml",
        source_type="feed",
    )
    match = find_duplicate(
        make_item(url="https://news.example/story?utm_campaign=weekly"),
        second_source,
        [make_content(url="https://news.example/story?fbclid=tracking")],
    )

    assert match is not None
    assert match.canonical_content.id == 1
    assert match.match_type == "exact_url"
    assert match.similarity == 1.0


def test_external_id_matches_only_within_the_same_source() -> None:
    item = make_item(url="https://news.example/other")
    same_source_match = find_duplicate(
        item, SOURCE, [make_content(url="https://news.example/original")]
    )

    different_source = Source(
        id=3,
        name="Other Feed",
        platform="rss",
        base_url="https://other.example/feed.xml",
        source_type="feed",
    )
    different_source_match = find_duplicate(
        item,
        SOURCE,
        [
            make_content(
                source=different_source,
                url="https://other.example/story",
                title="Completely different story about sports and players",
            )
        ],
    )

    assert same_source_match is not None
    assert same_source_match.match_type == "source_external_id"
    assert different_source_match is None


def test_similar_title_is_a_candidate_only_within_publication_window() -> None:
    item = make_item(
        url="https://news.example/new-story",
        title="Central bank cuts rates after its latest policy meeting",
    )
    recent = make_content(
        title="Central bank cuts rates after its latest policy meeting today",
        external_id="another-id",
        published_at=datetime(2026, 10, 2, 8, tzinfo=UTC),
    )
    old = make_content(
        title=recent.title,
        external_id="old-id",
        published_at=datetime(2026, 10, 5, 12, tzinfo=UTC),
    )

    match = find_duplicate(item, SOURCE, [recent])
    old_match = find_duplicate(item, SOURCE, [old])

    assert match is not None
    assert match.match_type == "similar_title_candidate"
    assert 0.92 <= match.similarity < 1
    assert old_match is None
