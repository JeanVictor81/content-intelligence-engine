"""Offline tests for the end-to-end research API route."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, Mock

from fastapi.testclient import TestClient

from app.api.routes import research as research_route
from app.connectors.rss import FeedFetchError, RSSFeed, RSSFeedItem
from app.core.config import RSSFeedConfig, settings
from app.database.session import get_db
from app.main import app
from app.models import Content, Source

FEED_CONFIG = RSSFeedConfig(name="Sample Feed", url="https://news.example/feed.xml")
RAW_ITEM = RSSFeedItem(
    feed=RSSFeed(name=FEED_CONFIG.name, url=FEED_CONFIG.url),
    raw_entry={
        "guid": "sample-1",
        "link": "https://news.example/item-1",
        "title": "CBLOL sample result",
        "summary": "A sample feed item.",
    },
)


def make_client(session: Mock) -> TestClient:
    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_research_searches_normalizes_persists_and_returns_results(monkeypatch) -> None:
    monkeypatch.setattr(settings, "rss_feeds", [FEED_CONFIG])
    session = MagicMock()
    source = Source(
        id=4,
        name=FEED_CONFIG.name,
        platform="rss",
        base_url=FEED_CONFIG.url,
        source_type="feed",
    )
    content = Content(
        id=15,
        source=source,
        external_id="sample-1",
        url="https://news.example/item-1",
        title="CBLOL sample result",
        text_excerpt="A sample feed item.",
        author=None,
        published_at=None,
        collected_at=datetime(2026, 10, 1, tzinfo=UTC),
        metadata_={"connector": "rss"},
    )

    class StubRSSConnector:
        def __init__(self, feeds):
            assert feeds == [RSSFeed(name=FEED_CONFIG.name, url=FEED_CONFIG.url)]

        def search(self, query, options):
            assert query == "CBLOL"
            assert options.max_results == 20
            return [RAW_ITEM]

    monkeypatch.setattr(research_route, "RSSConnector", StubRSSConnector)
    monkeypatch.setattr(
        research_route, "persist_normalized_items", Mock(return_value=[content])
    )

    try:
        with make_client(session) as client:
            response = client.post("/research", json={"query": "CBLOL"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["result_count"] == 1
    assert body["skipped_count"] == 0
    assert body["results"][0]["id"] == 15
    assert body["results"][0]["source"]["name"] == "Sample Feed"
    assert body["results"][0]["url"] == "https://news.example/item-1"
    assert body["results"][0]["collected_at"] == "2026-10-01T00:00:00Z"
    session.begin.assert_called_once_with()


def test_research_returns_service_unavailable_when_no_feeds_are_configured(monkeypatch) -> None:
    monkeypatch.setattr(settings, "rss_feeds", [])
    session = MagicMock()

    try:
        with make_client(session) as client:
            response = client.post("/research", json={"query": "CBLOL"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert "RSS_FEEDS" in response.json()["detail"]
    session.begin.assert_not_called()


def test_research_rejects_blank_query(monkeypatch) -> None:
    monkeypatch.setattr(settings, "rss_feeds", [FEED_CONFIG])
    session = MagicMock()

    try:
        with make_client(session) as client:
            response = client.post("/research", json={"query": "   "})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    session.begin.assert_not_called()


def test_research_maps_feed_failure_to_gateway_error(monkeypatch) -> None:
    monkeypatch.setattr(settings, "rss_feeds", [FEED_CONFIG])
    session = MagicMock()

    class FailedRSSConnector:
        def __init__(self, feeds):
            pass

        def search(self, query, options):
            raise FeedFetchError("internal transport details")

    monkeypatch.setattr(research_route, "RSSConnector", FailedRSSConnector)

    try:
        with make_client(session) as client:
            response = client.post("/research", json={"query": "CBLOL"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 502
    assert response.json()["detail"] == "A configured RSS source could not be searched."
    assert "internal transport details" not in response.text
    session.begin.assert_not_called()


def test_research_empty_search_does_not_open_database_transaction(monkeypatch) -> None:
    monkeypatch.setattr(settings, "rss_feeds", [FEED_CONFIG])
    session = MagicMock()

    class EmptyRSSConnector:
        def __init__(self, feeds):
            pass

        def search(self, query, options):
            return []

    persist = Mock()
    monkeypatch.setattr(research_route, "RSSConnector", EmptyRSSConnector)
    monkeypatch.setattr(research_route, "persist_normalized_items", persist)

    try:
        with make_client(session) as client:
            response = client.post("/research", json={"query": "CBLOL"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["result_count"] == 0
    assert response.json()["results"] == []
    persist.assert_not_called()
    session.begin.assert_not_called()
