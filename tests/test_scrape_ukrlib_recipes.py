from __future__ import annotations

from pathlib import Path

import pytest

from scripts.rag import scrape_ukrlib as scrape

FIXTURES = Path(__file__).parent / "fixtures" / "ukrlib"


@pytest.mark.parametrize(
    ("slug", "source_author", "death_year"),
    [
        ("teliha", "Теліга Олена", "1942"),
        ("rylsky", "Рильський Максим", "1964"),
    ],
)
def test_literary_gap_recipes_have_ukrlib_metadata_shape(
    slug: str,
    source_author: str,
    death_year: str,
) -> None:
    recipe = {**scrape.P1_AUTHORS, **scrape.P2_AUTHORS, **scrape.P3_AUTHORS}[slug]

    assert set(recipe) >= {
        "id",
        "name",
        "full_name",
        "source_author",
        "years",
        "genre_default",
        "period",
    }
    assert recipe["source_author"] == source_author
    assert recipe["years"].endswith(death_year)
    assert recipe["id"] not in scrape.BLACKLISTED_IDS


@pytest.mark.parametrize(
    ("fixture_name", "author", "title"),
    [
        ("teliha-suchasnykam.html", "Теліга Олена", "Сучасникам"),
        ("rylsky-molyus-i-viryu.html", "Рильський Максим", "Молюсь і вірю"),
    ],
)
def test_source_content_verification_accepts_declared_author_and_title(
    fixture_name: str,
    author: str,
    title: str,
) -> None:
    page_html = (FIXTURES / fixture_name).read_text(encoding="utf-8")

    scrape.verify_source_content(
        page_html,
        expected_author=author,
        expected_title=title,
        source_url="https://example.test/source",
    )


def test_source_content_verification_rejects_resolving_wrong_work() -> None:
    page_html = (FIXTURES / "teliha-suchasnykam.html").read_text(encoding="utf-8")

    with pytest.raises(scrape.SourceContentError, match="Подорожній"):
        scrape.verify_source_content(
            page_html,
            expected_author="Теліга Олена",
            expected_title="Подорожній",
            source_url="https://example.test/resolves-but-is-wrong",
        )
