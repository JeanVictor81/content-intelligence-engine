"""Unit tests for persisting normalized RSS records."""

from unittest.mock import Mock, call

from app.connectors.rss import RSSFeed, RSSFeedItem
from app.models import Content, Source
from app.services.normalization import normalize_rss_item
from app.services.persistence import persist_normalized_items

FEED = RSSFeed(name="Sample Esports Feed", url="https://news.example/feed.xml")


def normalized_item(url: str = "https://news.example/item", *, feed: RSSFeed = FEED):
    item = RSSFeedItem(
        feed=feed,
        raw_entry={"link": url, "title": "An item", "guid": url},
    )
    return normalize_rss_item(item)


def test_persists_content_and_reuses_existing_source() -> None:
    source = Source(
        id=7,
        name=FEED.name,
        platform="rss",
        base_url=FEED.url,
        source_type="feed",
    )
    session = Mock()
    session.scalar.return_value = source
    session.scalars.return_value.all.return_value = []

    saved = persist_normalized_items(
        session,
        [normalized_item("https://news.example/one"), normalized_item("https://news.example/two")],
    )

    assert len(saved) == 2
    assert all(isinstance(content, Content) for content in saved)
    assert all(content.source is source for content in saved)
    assert [content.url for content in saved] == [
        "https://news.example/one",
        "https://news.example/two",
    ]
    assert session.scalar.call_count == 1
    assert session.add.call_args_list == [call(saved[0]), call(saved[1])]
    session.flush.assert_called_once_with()
    session.commit.assert_not_called()


def test_creates_source_when_missing() -> None:
    session = Mock()
    session.scalar.return_value = None
    session.scalars.return_value.all.return_value = []

    saved = persist_normalized_items(session, [normalized_item()])

    added_source, added_content = (entry.args[0] for entry in session.add.call_args_list)
    assert isinstance(added_source, Source)
    assert isinstance(added_content, Content)
    assert added_content.source is added_source
    assert saved == [added_content]
    session.flush.assert_called_once_with()
    session.commit.assert_not_called()


def test_empty_input_does_not_query_or_flush() -> None:
    session = Mock()
    session.scalars.return_value.all.return_value = []

    assert persist_normalized_items(session, []) == []

    session.scalar.assert_not_called()
    session.add.assert_not_called()
    session.flush.assert_not_called()


def test_persists_duplicate_as_a_linked_record_without_losing_its_source() -> None:
    second_feed = RSSFeed(name="Sample Syndicated Feed", url="https://syndicated.example/feed.xml")
    session = Mock()
    session.scalar.return_value = None
    session.scalars.return_value.all.return_value = []

    saved = persist_normalized_items(
        session,
        [
            normalized_item("https://news.example/story?utm_source=first"),
            normalized_item("https://news.example/story?utm_source=second", feed=second_feed),
        ],
    )

    first_source, first_content, second_source, second_content = (
        entry.args[0] for entry in session.add.call_args_list
    )
    assert saved == [first_content, second_content]
    assert first_content.source is first_source
    assert second_content.source is second_source
    assert second_content is not first_content
    assert second_content.duplicate_of is first_content
    assert second_content.duplicate_match_type == "exact_url"
    assert second_content.duplicate_similarity == 1.0
