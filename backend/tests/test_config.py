"""Configuration parsing tests."""

from app.core.config import Settings


def test_rss_feeds_are_loaded_from_json_environment_value(monkeypatch) -> None:
    monkeypatch.setenv(
        "RSS_FEEDS",
        '[{"name":"Configured Feed","url":"https://news.example/feed.xml"}]',
    )

    settings = Settings(_env_file=None)

    assert len(settings.rss_feeds) == 1
    assert settings.rss_feeds[0].name == "Configured Feed"
    assert settings.rss_feeds[0].url == "https://news.example/feed.xml"
