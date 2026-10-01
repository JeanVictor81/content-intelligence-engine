"""RSS and Atom connector for application-configured feeds."""

import ipaddress
import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

import feedparser
import httpx

from app.connectors.base import SearchOptions

DEFAULT_TIMEOUT_SECONDS = 8.0
DEFAULT_MAX_FEED_BYTES = 2 * 1024 * 1024
USER_AGENT = "ContentIntelligenceEngine/0.1 (+local research client)"
logger = logging.getLogger(__name__)


class RSSConnectorError(Exception):
    """Base exception for RSS connector failures."""


class FeedFetchError(RSSConnectorError):
    """A configured feed could not be retrieved safely."""


class FeedParseError(RSSConnectorError):
    """A feed response could not be parsed as a valid feed."""


@dataclass(frozen=True, slots=True)
class RSSFeed:
    """A feed URL trusted by application configuration, never supplied by a query."""

    name: str
    url: str

    def __post_init__(self) -> None:
        parsed = urlsplit(self.url)
        hostname = (parsed.hostname or "").casefold().rstrip(".")
        if parsed.scheme not in {"http", "https"} or not hostname:
            raise ValueError("Feed URL must be an absolute HTTP or HTTPS URL.")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("Feed URLs must not contain embedded credentials.")
        if hostname == "localhost" or hostname.endswith((".localhost", ".local", ".internal")):
            raise ValueError("Local or internal feed hosts are not allowed.")
        try:
            address = ipaddress.ip_address(hostname)
        except ValueError:
            address = None
        if address is not None and not address.is_global:
            raise ValueError("Non-public IP addresses cannot be feed hosts.")


@dataclass(frozen=True, slots=True)
class RSSFeedItem:
    """A parsed, connector-native feed entry; normalization happens downstream."""

    feed: RSSFeed
    raw_entry: Mapping[str, Any]


class RSSConnector:
    """Search a fixed collection of RSS/Atom feeds using bounded HTTP requests."""

    name = "rss"

    def __init__(
        self,
        feeds: Sequence[RSSFeed],
        *,
        client: httpx.Client | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_feed_bytes: int = DEFAULT_MAX_FEED_BYTES,
    ) -> None:
        if not feeds:
            raise ValueError("At least one application-configured feed is required.")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero.")
        if max_feed_bytes < 1:
            raise ValueError("max_feed_bytes must be greater than zero.")

        self._feeds = tuple(feeds)
        self._client = client
        self._timeout_seconds = timeout_seconds
        self._max_feed_bytes = max_feed_bytes

    def search(self, query: str, options: SearchOptions | None = None) -> list[RSSFeedItem]:
        """Fetch configured feeds and return entries whose text contains the query."""
        normalized_query = query.strip().casefold()
        if not normalized_query:
            raise ValueError("query must not be empty.")

        search_options = options or SearchOptions()
        if self._client is not None:
            return self._search_with_client(normalized_query, search_options, self._client)

        with httpx.Client(
            timeout=self._timeout_seconds,
            follow_redirects=False,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": ("application/rss+xml, application/atom+xml, application/xml, text/xml"),
            },
        ) as client:
            return self._search_with_client(normalized_query, search_options, client)

    def fetch(self, item: RSSFeedItem) -> RSSFeedItem:
        """RSS entries include their available fields in the feed; no second request is needed."""
        return item

    def _search_with_client(
        self, query: str, options: SearchOptions, client: httpx.Client
    ) -> list[RSSFeedItem]:
        results: list[RSSFeedItem] = []
        successful_feed_count = 0
        failed_feed_count = 0
        last_feed_error: RSSConnectorError | None = None
        for feed_index, feed in enumerate(self._feeds):
            try:
                payload = self._read_feed(client, feed)
                parsed_feed = feedparser.parse(payload)
                if parsed_feed.get("bozo"):
                    raise FeedParseError(f"Configured feed '{feed.name}' is malformed.")
            except RSSConnectorError as exc:
                failed_feed_count += 1
                last_feed_error = exc
                logger.warning(
                    "rss_feed_search_failed",
                    extra={
                        "feed_index": feed_index,
                        "error_type": type(exc).__name__,
                    },
                )
                continue

            successful_feed_count += 1

            for entry in parsed_feed.entries:
                searchable_fields = [
                    str(entry.get(field, ""))
                    for field in ("title", "summary", "description", "author")
                ]
                for content in entry.get("content", ()):
                    if isinstance(content, Mapping):
                        searchable_fields.append(str(content.get("value", "")))
                searchable_text = " ".join(searchable_fields).casefold()
                if query in searchable_text:
                    results.append(RSSFeedItem(feed=feed, raw_entry=entry))
                    if len(results) >= options.max_results:
                        return results

        if successful_feed_count == 0:
            if last_feed_error is not None:
                raise last_feed_error
            raise FeedFetchError("All configured RSS feeds failed.")
        if failed_feed_count:
            logger.warning(
                "rss_search_completed_with_feed_failures",
                extra={
                    "successful_feed_count": successful_feed_count,
                    "failed_feed_count": failed_feed_count,
                },
            )
        return results

    def _read_feed(self, client: httpx.Client, feed: RSSFeed) -> bytes:
        try:
            with client.stream(
                "GET", feed.url, timeout=self._timeout_seconds, follow_redirects=False
            ) as response:
                if response.is_redirect:
                    raise FeedFetchError(f"Configured feed '{feed.name}' returned a redirect.")
                response.raise_for_status()

                content_length = response.headers.get("content-length")
                if content_length is not None:
                    try:
                        declared_size = int(content_length)
                    except ValueError as exc:
                        raise FeedFetchError(
                            f"Configured feed '{feed.name}' returned an invalid content length."
                        ) from exc
                    if declared_size < 0:
                        raise FeedFetchError(
                            f"Configured feed '{feed.name}' returned an invalid content length."
                        )
                    if declared_size > self._max_feed_bytes:
                        raise FeedFetchError(
                            f"Configured feed '{feed.name}' exceeds the size limit."
                        )

                body = bytearray()
                for chunk in response.iter_bytes():
                    body.extend(chunk)
                    if len(body) > self._max_feed_bytes:
                        raise FeedFetchError(
                            f"Configured feed '{feed.name}' exceeds the size limit."
                        )
                return bytes(body)
        except FeedFetchError:
            raise
        except httpx.HTTPError as exc:
            raise FeedFetchError(f"Could not retrieve configured feed '{feed.name}'.") from exc
