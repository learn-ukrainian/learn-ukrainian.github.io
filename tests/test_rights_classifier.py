from __future__ import annotations

from pathlib import Path

import pytest

from scripts.readings.rights_classifier import classify_rights, load_author_rights

CURRENT_YEAR = 2026


@pytest.mark.parametrize(
    "author",
    [
        "Франко",
        "Шевченко",
        "Коцюбинський",
        "Винниченко",
    ],
)
def test_public_domain_authors(author: str) -> None:
    verdict = classify_rights(author, "Твір", None, "", "", current_year=CURRENT_YEAR)

    assert verdict["rights_class"] == "public_domain"


@pytest.mark.parametrize(
    "author",
    [
        "Зеров",
        "Підмогильний",
        "Хвильовий",
        "Стус",
    ],
)
def test_repressed_rehabilitated_authors_are_hosted_heritage(author: str) -> None:
    # Executed Renaissance + persecuted authors (incl. Стус) are hosted in full as
    # freely-accessible Ukrainian heritage — never gatekept (user order 2026-06-22).
    verdict = classify_rights(author, "Твір", None, "", "", current_year=CURRENT_YEAR)

    assert verdict["rights_class"] == "public_domain"
    assert "repressed" in verdict["basis"]


def test_established_source_basis_is_hosted() -> None:
    verdict = classify_rights(
        "Будь-який Автор", "Твір", None, "textbook-10-klas-ukrlit", "", current_year=CURRENT_YEAR
    )

    assert verdict["rights_class"] == "public_domain"


def test_folk_author_is_public_domain() -> None:
    verdict = classify_rights("Народна творчість", "Дума", None, "", "", current_year=CURRENT_YEAR)

    assert verdict["rights_class"] == "public_domain"


def test_premodern_track_is_public_domain_without_year() -> None:
    verdict = classify_rights("Невідомий книжник", "Твір", None, "", "oes", current_year=CURRENT_YEAR)

    assert verdict["rights_class"] == "public_domain"
    assert verdict["basis"] == "pre-modern track/work before 1800"


def test_unknown_author_defaults_in_copyright() -> None:
    verdict = classify_rights("Іван Невідомий", "Твір", None, "", "", current_year=CURRENT_YEAR)

    assert verdict["rights_class"] == "in_copyright"
    assert verdict["basis"] == "conservative default (author not in rights table)"


def test_ambiguous_canonical_author_key_keeps_exact_only(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    rights_path = tmp_path / "authors_rights.yaml"
    rights_path.write_text(
        """
"Тарас Спільний":
  death_year: 1900
"Теодор Спільний":
  death_year: 1960
""",
        encoding="utf-8",
    )
    caplog.set_level("WARNING", logger="scripts.readings.rights_classifier")

    table = load_author_rights(rights_path)

    assert table.get("Тарас Спільний").death_year == 1900
    assert table.get("Теодор Спільний").death_year == 1960
    assert table.get("Спільний Т.") is None
    assert "ambiguous canonical author key" in caplog.text
