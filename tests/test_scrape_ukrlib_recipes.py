from __future__ import annotations

from pathlib import Path

import pytest

from scripts.rag import scrape_ukrlib as scrape

FIXTURES = Path(__file__).parent / "fixtures" / "ukrlib"


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
