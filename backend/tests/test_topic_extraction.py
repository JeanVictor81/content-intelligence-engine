"""Tests for conservative topic grouping."""

from datetime import UTC, datetime

from app.models import Content
from app.services.topic_extraction import extract_topic_groups


def make_content(
    content_id: int,
    title: str,
    published_at: datetime | None = datetime(2026, 10, 1, 12, tzinfo=UTC),
    *,
    duplicate_of_id: int | None = None,
) -> Content:
    return Content(
        id=content_id,
        title=title,
        published_at=published_at,
        duplicate_of_id=duplicate_of_id,
    )


def test_groups_similar_headlines_about_same_event() -> None:
    contents = [
        make_content(1, "Rockstar announces GTA 6 trailer release date"),
        make_content(2, "GTA 6 trailer release date announced by Rockstar Games"),
    ]

    groups = extract_topic_groups(contents)

    assert len(groups) == 1
    assert groups[0].representative.id == 1
    assert [content.id for content in groups[0].contents] == [1, 2]


def test_keeps_gta_and_cblol_in_separate_topics_even_for_broad_search() -> None:
    contents = [
        make_content(1, "Rockstar announces GTA 6 trailer release date"),
        make_content(2, "CBLOL team announces its new player roster"),
    ]

    groups = extract_topic_groups(contents)

    assert len(groups) == 2
    assert {group.contents[0].id for group in groups} == {1, 2}


def test_groups_launch_news_but_separates_npc_news_about_gta_6() -> None:
    contents = [
        make_content(1, "Rockstar confirms GTA 6 launch date for May"),
        make_content(2, "Rockstar announces GTA 6 launch date for May"),
        make_content(3, "Rockstar details GTA 6 NPC behavior in a new interview"),
    ]

    groups = extract_topic_groups(contents)

    assert len(groups) == 2
    assert [content.id for content in groups[0].contents] == [1, 2]
    assert [content.id for content in groups[1].contents] == [3]


def test_groups_different_headlines_reporting_the_same_event() -> None:
    contents = [
        make_content(
            1,
            "Técnico deixa seleção após Copa, consegue renovação e sai 2 jogos depois",
        ),
        make_content(
            2,
            "Técnico se despede na Copa, renova e deixa cargo depois de dois jogos",
        ),
    ]

    groups = extract_topic_groups(contents)

    assert len(groups) == 1
    assert [content.id for content in groups[0].contents] == [1, 2]


def test_requires_nearby_publication_dates_for_title_similarity() -> None:
    first = make_content(1, "Rockstar announces GTA 6 trailer release date")
    second = make_content(
        2,
        "GTA 6 trailer release date announced by Rockstar Games",
        datetime(2026, 10, 4, 12, tzinfo=UTC),
    )

    assert len(extract_topic_groups([first, second])) == 2


def test_exact_duplicate_family_can_group_without_title_or_date_evidence() -> None:
    first = make_content(1, "Unrelated first headline", published_at=None)
    duplicate = make_content(
        2, "Different syndicated headline", published_at=None, duplicate_of_id=1
    )

    groups = extract_topic_groups([first, duplicate])

    assert len(groups) == 1
    assert [content.id for content in groups[0].contents] == [1, 2]


def test_keeps_items_without_title_match_as_individual_topics() -> None:
    contents = [
        make_content(1, "CBLOL team signs a new coach"),
        make_content(2, "GTA 6 release window changes"),
    ]

    assert len(extract_topic_groups(contents)) == 2
