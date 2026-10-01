"""Offline tests for the RSS connector."""

from pathlib import Path

import httpx
import pytest

from app.connectors.base import SearchOptions
from app.connectors.rss import (
    FeedFetchError,
    RSSConnector,
    RSSFeed,
    RSSFeedItem,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "rss_sample.xml"
FEED = RSSFeed(name="Sample Esports Feed", url="https://news.example/feed.xml")


def make_client(body: bytes, *, status_code: int = 200, headers: dict[str, str] | None = None):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == httpx.URL(FEED.url)
        return httpx.Response(status_code, content=body, headers=headers, request=request)

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_search_filters_fixture_items_case_insensitively() -> None:
    with make_client(FIXTURE_PATH.read_bytes()) as client:
        connector = RSSConnector([FEED], client=client)

        results = connector.search("cblol")

    assert len(results) == 1
    assert isinstance(results[0], RSSFeedItem)
    assert results[0].feed == FEED
    assert results[0].raw_entry["title"] == "CBLOL announces a new match schedule"
    assert connector.fetch(results[0]) is results[0]


def test_search_obeys_result_limit() -> None:
    with make_client(FIXTURE_PATH.read_bytes()) as client:
        connector = RSSConnector([FEED], client=client)

        results = connector.search("the", SearchOptions(max_results=1))

    assert len(results) == 1


def test_search_rejects_empty_query() -> None:
    with make_client(FIXTURE_PATH.read_bytes()) as client:
        connector = RSSConnector([FEED], client=client)

        with pytest.raises(ValueError, match="query must not be empty"):
            connector.search("  ")


def test_feed_url_rejects_local_hosts() -> None:
    with pytest.raises(ValueError, match="Non-public IP addresses"):
        RSSFeed(name="Local", url="http://127.0.0.1/private-feed")


def test_feed_url_rejects_embedded_credentials() -> None:
    with pytest.raises(ValueError, match="embedded credentials"):
        RSSFeed(name="Credentials", url="https://user:password@news.example/feed.xml")


def test_redirects_are_not_followed() -> None:
    redirect_headers = {"Location": "http://127.0.0.1/admin"}
    with make_client(b"", status_code=302, headers=redirect_headers) as client:
        connector = RSSConnector([FEED], client=client)

        with pytest.raises(FeedFetchError, match="returned a redirect"):
            connector.search("cblol")


def test_oversized_feed_is_rejected() -> None:
    payload = FIXTURE_PATH.read_bytes()
    with make_client(payload) as client:
        connector = RSSConnector([FEED], client=client, max_feed_bytes=16)

        with pytest.raises(FeedFetchError, match="exceeds the size limit"):
            connector.search("cblol")


def test_search_returns_results_when_one_configured_feed_fails() -> None:
    failed_feed = RSSFeed(name="Unavailable Feed", url="https://unavailable.example/feed.xml")
    working_feed = RSSFeed(name="Working Feed", url="https://working.example/feed.xml")

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url == httpx.URL(failed_feed.url):
            return httpx.Response(503, request=request)
        return httpx.Response(200, content=FIXTURE_PATH.read_bytes(), request=request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        connector = RSSConnector([failed_feed, working_feed], client=client)

        results = connector.search("cblol")

    assert len(results) == 1
    assert results[0].feed == working_feed
    assert results[0].raw_entry["title"] == "CBLOL announces a new match schedule"
