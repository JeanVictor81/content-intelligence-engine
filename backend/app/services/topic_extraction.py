"""Deterministic, conservative grouping of content into query-scoped topics."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from difflib import SequenceMatcher

from app.models import Content
from app.services.deduplication import normalize_title

TOPIC_TITLE_SIMILARITY = 0.50
MIN_TITLE_TERMS = 4
MIN_SHARED_TITLE_TERMS = 3
TOPIC_PUBLICATION_WINDOW = timedelta(hours=48)
STOP_WORDS = frozenset(
    (
        "a an and as at by da das de do dos e em for from i na nas no nos o os ou para pela pelas "
        "pelo pelos por que the um uma uns umas with after before sobre contra entre como sua seu"
    ).split()
)


@dataclass(frozen=True, slots=True)
class TopicGroup:
    """A stable representative and its related content records."""

    representative: Content
    contents: tuple[Content, ...]
    relevance: tuple[float, ...]


def extract_topic_groups(contents: Sequence[Content]) -> list[TopicGroup]:
    """Group only strongly related headlines published close together.

    Exact duplicate links from M002 are treated as the same item. Other matches
    require three shared informative title terms, sufficient headline
    similarity and publication dates within 48 hours. Content without sufficient
    evidence stays in its own group.
    """
    groups: list[list[Content]] = []

    for content in contents:
        best_group: list[Content] | None = None
        best_score = 0.0
        for group in groups:
            representative = group[0]
            if same_duplicate_family(content, representative):
                score = 1.0
            else:
                score = headline_similarity(content, representative)
            if score >= TOPIC_TITLE_SIMILARITY and score > best_score:
                best_group = group
                best_score = score

        if best_group is None:
            groups.append([content])
        else:
            best_group.append(content)

    result: list[TopicGroup] = []
    for group in groups:
        representative = next((item for item in group if item.title), group[0])
        result.append(
            TopicGroup(
                representative=representative,
                contents=tuple(group),
                relevance=tuple(
                    1.0 if item is representative else headline_similarity(item, representative)
                    for item in group
                ),
            )
        )
    return result


def same_duplicate_family(first: Content, second: Content) -> bool:
    """Return whether two records belong to the same exact duplicate family."""
    first_id = first.duplicate_of_id or first.id
    second_id = second.duplicate_of_id or second.id
    return first_id is not None and first_id == second_id


def headline_similarity(first: Content, second: Content) -> float:
    """Return a conservative score for two headlines about one recent event."""
    first_title = normalize_title(first.title)
    second_title = normalize_title(second.title)
    if not first_title or not second_title or not _published_close(first, second):
        return 0.0

    first_terms = _informative_terms(first_title)
    second_terms = _informative_terms(second_title)
    shared_terms = first_terms & second_terms
    if (
        len(first_terms) < MIN_TITLE_TERMS
        or len(second_terms) < MIN_TITLE_TERMS
        or len(shared_terms) < MIN_SHARED_TITLE_TERMS
    ):
        return 0.0
    sequence_similarity = SequenceMatcher(None, first_title, second_title, autojunk=False).ratio()
    term_similarity = 2 * len(shared_terms) / (len(first_terms) + len(second_terms))
    return max(sequence_similarity, term_similarity)


def _informative_terms(title: str) -> set[str]:
    return {term for term in title.split() if len(term) > 2 and term not in STOP_WORDS}


def _published_close(first: Content, second: Content) -> bool:
    if first.published_at is None or second.published_at is None:
        return False
    first_at = _as_utc(first.published_at)
    second_at = _as_utc(second.published_at)
    return abs(first_at - second_at) <= TOPIC_PUBLICATION_WINDOW


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
