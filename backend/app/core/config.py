"""Validated application settings."""

from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class RSSFeedConfig(BaseModel):
    """One explicitly configured RSS/Atom feed."""

    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
    url: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2048)]


class Settings(BaseSettings):
    """Settings loaded from environment variables and the project .env file."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Content Intelligence Engine"
    app_env: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    database_url: str | None = None
    rss_feeds: list[RSSFeedConfig] = Field(default_factory=list)


settings = Settings()
