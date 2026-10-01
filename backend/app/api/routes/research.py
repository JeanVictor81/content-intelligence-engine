"""RSS research endpoint: search, normalize, persist and return results."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.connectors.base import SearchOptions
from app.connectors.rss import RSSConnector, RSSConnectorError, RSSFeed
from app.core.config import settings
from app.database.session import get_db
from app.schemas.research import ContentResult, ResearchRequest, ResearchResponse, SourceResult
from app.services.normalization import NormalizationError, normalize_rss_item
from app.services.persistence import persist_normalized_items

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/research", response_model=ResearchResponse, tags=["research"])
def research_topic(
    request: ResearchRequest, session: Annotated[Session, Depends(get_db)]
) -> ResearchResponse:
    """Search configured RSS feeds, persist normalized results and return them."""
    if not settings.rss_feeds:
        raise HTTPException(
            status_code=503,
            detail="No RSS feeds are configured. Add authorized feeds to RSS_FEEDS.",
        )

    try:
        feeds = [RSSFeed(name=feed.name, url=feed.url) for feed in settings.rss_feeds]
        connector = RSSConnector(feeds)
        raw_items = connector.search(request.query, SearchOptions())
    except ValueError as exc:
        logger.error("rss_feed_configuration_invalid")
        raise HTTPException(
            status_code=503, detail="The RSS feed configuration is invalid."
        ) from exc
    except RSSConnectorError as exc:
        logger.exception("rss_research_failed")
        raise HTTPException(
            status_code=502, detail="A configured RSS source could not be searched."
        ) from exc

    normalized_items = []
    skipped_count = 0
    for index, raw_item in enumerate(raw_items):
        try:
            normalized_items.append(normalize_rss_item(raw_item))
        except NormalizationError:
            skipped_count += 1
            logger.warning("rss_item_skipped", extra={"item_index": index})

    if not normalized_items:
        return ResearchResponse(
            query=request.query,
            result_count=0,
            skipped_count=skipped_count,
            duplicate_count=0,
            similarity_candidate_count=0,
            results=[],
        )

    try:
        with session.begin():
            contents = persist_normalized_items(session, normalized_items)
            results = [
                ContentResult(
                    id=content.id,
                    source=SourceResult(
                        name=item.source.name,
                        platform=item.source.platform,
                        base_url=item.source.base_url,
                        source_type=item.source.source_type,
                    ),
                    external_id=item.content.external_id,
                    duplicate_of_id=content.duplicate_of_id,
                    duplicate_match_type=content.duplicate_match_type,
                    duplicate_similarity=content.duplicate_similarity,
                    url=item.content.url,
                    title=item.content.title,
                    text_excerpt=item.content.text_excerpt,
                    author=item.content.author,
                    published_at=item.content.published_at,
                    collected_at=content.collected_at,
                    metadata=item.content.metadata,
                )
                for item, content in zip(normalized_items, contents, strict=True)
            ]
    except SQLAlchemyError as exc:
        logger.exception("research_persistence_failed")
        raise HTTPException(status_code=503, detail="Research results could not be saved.") from exc

    return ResearchResponse(
        query=request.query,
        result_count=len(results),
        skipped_count=skipped_count,
        duplicate_count=sum(
            result.duplicate_match_type in {"exact_url", "source_external_id"} for result in results
        ),
        similarity_candidate_count=sum(
            result.duplicate_match_type == "similar_title_candidate" for result in results
        ),
        results=results,
    )
