"""Persist normalized source and content records using a caller-owned transaction."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Content, Source
from app.services.deduplication import find_duplicate
from app.services.normalization import NormalizedRSSItem


def persist_normalized_items(session: Session, items: list[NormalizedRSSItem]) -> list[Content]:
    """Store normalized RSS items and reuse existing source records.

    Source identity is the pair ``(platform, base_url)``. Content duplicates are
    intentionally retained for the later deduplication stage. This function
    flushes pending rows but leaves commit and rollback to its caller.
    """
    if not items:
        return []

    candidates = list(
        session.scalars(
            select(Content)
            .options(
                selectinload(Content.source),
                selectinload(Content.duplicate_of),
            )
            .order_by(Content.id)
        ).all()
    )
    sources: dict[tuple[str, str], Source] = {}
    persisted: list[Content] = []

    for item in items:
        source_data = item.source
        source_key = (source_data.platform, source_data.base_url)
        source = sources.get(source_key)

        if source is None:
            source = session.scalar(
                select(Source)
                .where(
                    Source.platform == source_data.platform,
                    Source.base_url == source_data.base_url,
                )
                .order_by(Source.id)
                .limit(1)
            )
            if source is None:
                source = Source(
                    name=source_data.name,
                    platform=source_data.platform,
                    base_url=source_data.base_url,
                    source_type=source_data.source_type,
                )
                session.add(source)
            sources[source_key] = source

        content_data = item.content
        content = Content(
            source=source,
            external_id=content_data.external_id,
            url=content_data.url,
            title=content_data.title,
            text_excerpt=content_data.text_excerpt,
            author=content_data.author,
            published_at=content_data.published_at,
            metadata_=content_data.metadata,
        )
        match = find_duplicate(item, source, candidates)
        if match is not None:
            content.duplicate_of = match.canonical_content
            content.duplicate_match_type = match.match_type
            content.duplicate_similarity = match.similarity
        session.add(content)
        persisted.append(content)
        candidates.append(content)

    session.flush()
    return persisted
