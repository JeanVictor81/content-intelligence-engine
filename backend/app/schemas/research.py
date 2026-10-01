"""Schemas for topic research requests and persisted RSS results."""

from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, StringConstraints


class ResearchRequest(BaseModel):
    """A bounded, non-empty topic query."""

    query: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


class SourceResult(BaseModel):
    """Origin details included with each collected item."""

    name: str
    platform: str
    base_url: str | None
    source_type: str


class ContentResult(BaseModel):
    """Persisted content and its available source metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    source: SourceResult
    external_id: str | None
    url: str
    title: str | None
    text_excerpt: str | None
    author: str | None
    published_at: datetime | None
    collected_at: datetime
    metadata: dict[str, Any]


class ResearchResponse(BaseModel):
    """Summary and persisted items returned by a research request."""

    query: str
    result_count: int
    skipped_count: int
    results: list[ContentResult]
