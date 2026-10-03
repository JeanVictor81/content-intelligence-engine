"""Tests for reusing persisted topics and counting unique source items."""

from datetime import UTC, datetime
from types import SimpleNamespace

from app.models import Content, Source
from app.services.topic_persistence import find_related_topic, unique_topic_contents


def make_content(
    content_id: int,
    title: str,
    url: str,
    source: Source,
) -> Content:
    return Content(
        id=content_id,
        title=title,
        url=url,
        source=source,
        published_at=datetime(2026, 10, 1, 12, tzinfo=UTC),
    )


def test_finds_existing_topic_for_a_similar_headline() -> None:
    existing = make_content(
        1,
        "Técnico deixa seleção após Copa, consegue renovação e sai 2 jogos depois",
        "https://news.example/first",
        Source(platform="rss", base_url="https://news.example/feed"),
    )
    topic = SimpleNamespace(id=10, content_links=[SimpleNamespace(content=existing)])
    incoming = make_content(
        2,
        "Técnico se despede na Copa, renova e deixa cargo depois de dois jogos",
        "https://other.example/second",
        Source(platform="rss", base_url="https://other.example/feed"),
    )

    assert find_related_topic(incoming, [topic]) is topic


def test_does_not_merge_a_gta_6_npc_topic_into_launch_topic() -> None:
    existing = make_content(
        1,
        "Rockstar confirms GTA 6 launch date for May",
        "https://news.example/launch",
        Source(platform="rss", base_url="https://news.example/feed"),
    )
    topic = SimpleNamespace(id=10, content_links=[SimpleNamespace(content=existing)])
    incoming = make_content(
        2,
        "Rockstar details GTA 6 NPC behavior in a new interview",
        "https://other.example/npc",
        Source(platform="rss", base_url="https://other.example/feed"),
    )

    assert find_related_topic(incoming, [topic]) is None


def test_unique_topic_contents_keep_other_sources_but_hide_repeat_url() -> None:
    first_source = Source(platform="rss", base_url="https://first.example/feed")
    other_source = Source(platform="rss", base_url="https://other.example/feed")
    first = make_content(1, "Story", "https://news.example/story?utm_source=one", first_source)
    repeated = make_content(2, "Story", "https://news.example/story?utm_source=two", first_source)
    syndicated = make_content(3, "Story", "https://news.example/story", other_source)
    topic = SimpleNamespace(
        id=10,
        content_links=[
            SimpleNamespace(content=first),
            SimpleNamespace(content=repeated),
            SimpleNamespace(content=syndicated),
        ],
    )

    assert [content.id for content in unique_topic_contents(topic)] == [1, 3]
