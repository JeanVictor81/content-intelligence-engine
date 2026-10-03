"""Persist query-scoped topic groups and their content relationships."""

from datetime import UTC, date, datetime
from hashlib import sha256

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Content, Topic, TopicContent
from app.services.deduplication import canonicalize_url, normalize_title
from app.services.topic_extraction import (
    TOPIC_TITLE_SIMILARITY,
    extract_topic_groups,
    headline_similarity,
    same_duplicate_family,
)


def persist_topic_groups(session: Session, query: str, contents: list[Content]) -> list[Topic]:
    """Save groups, reusing related topics and unique source items."""
    if not contents:
        return []

    normalized_query = normalize_title(query)
    groups = extract_topic_groups(contents)
    existing_topics = list(
        session.scalars(
            select(Topic)
            .where(Topic.normalized_query == normalized_query)
            .options(
                selectinload(Topic.content_links)
                .selectinload(TopicContent.content)
                .selectinload(Content.source)
            )
            .order_by(Topic.id)
        ).all()
    )
    now = datetime.now(UTC)
    by_key = {(topic.title_key, topic.event_date): topic for topic in existing_topics}
    topics_by_id: dict[int, Topic] = {}

    for group in groups:
        representative = group.representative
        normalized_title = normalize_title(representative.title)
        if not normalized_title:
            normalized_title = f"untitled-content-{representative.id}"
        title_key = sha256(normalized_title.encode("utf-8")).hexdigest()
        event_date = _event_date(representative, now)
        topic_key = (title_key, event_date)
        topic = by_key.get(topic_key)
        if topic is None:
            topic = find_related_topic(representative, existing_topics)

        if topic is None:
            topic = Topic(
                query=query,
                normalized_query=normalized_query,
                title=representative.title,
                title_key=title_key,
                event_date=event_date,
                first_seen_at=now,
                last_seen_at=now,
            )
            session.add(topic)
            session.flush()
            existing_topics.append(topic)
        else:
            topic.last_seen_at = now
            if topic.title is None and representative.title:
                topic.title = representative.title

        by_key[topic_key] = topic
        linked_item_keys = {
            _source_item_key(link.content)
            for link in topic.content_links
            if link.content is not None
        }
        for content, relevance in zip(group.contents, group.relevance, strict=True):
            source_item_key = _source_item_key(content)
            if source_item_key in linked_item_keys:
                continue
            session.add(
                TopicContent(
                    topic=topic,
                    content=content,
                    relevance=round(relevance, 4),
                    relationship_type=(
                        "representative" if content is representative else "related"
                    ),
                )
            )
            linked_item_keys.add(source_item_key)
        topics_by_id[topic.id] = topic

    session.flush()
    return list(topics_by_id.values())


def unique_topic_contents(topic: Topic) -> list[Content]:
    """Return one content row per source and canonical URL for API summaries."""
    items_by_key: dict[tuple[str, str | None, str], Content] = {}
    for link in topic.content_links:
        content = link.content
        if content is None:
            continue
        key = _source_item_key(content)
        current = items_by_key.get(key)
        if current is None or (content.id or 0) < (current.id or 0):
            items_by_key[key] = content
    return sorted(items_by_key.values(), key=lambda content: content.id or 0)


def find_related_topic(representative: Content, topics: list[Topic]) -> Topic | None:
    """Reuse the strongest existing topic supported by a related headline."""
    matches: list[tuple[float, int, Topic]] = []
    for topic in topics:
        for link in topic.content_links:
            existing = link.content
            if same_duplicate_family(representative, existing):
                score = 1.0
            else:
                score = headline_similarity(representative, existing)
            if score >= TOPIC_TITLE_SIMILARITY:
                matches.append((score, topic.id, topic))
    if not matches:
        return None
    return max(matches, key=lambda match: (match[0], -match[1]))[2]


def _event_date(content: Content, fallback: datetime) -> date:
    published_at = content.published_at
    if published_at is None:
        return fallback.date()
    if published_at.tzinfo is None:
        return published_at.date()
    return published_at.astimezone(UTC).date()


def _source_item_key(content: Content) -> tuple[str, str | None, str]:
    """Identify one article from one source across repeated feed collections."""
    return (
        content.source.platform,
        content.source.base_url,
        canonicalize_url(content.url),
    )
