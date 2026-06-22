from __future__ import annotations

from pathlib import Path

import pytest

from scripts.readings.generate_readings import CorpusText, is_public_domain
from scripts.readings.rights_classifier import classify_rights

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
        "Стус",
        "Тичина",
        "Рильський",
    ],
)
def test_standard_life_plus_70_in_copyright(author: str) -> None:
    verdict = classify_rights(author, "Твір", None, "", "", current_year=CURRENT_YEAR)

    assert verdict["rights_class"] == "in_copyright"


@pytest.mark.parametrize(
    "author",
    [
        "Зеров",
        "Підмогильний",
        "Хвильовий",
    ],
)
def test_repressed_rehabilitated_authors_stay_in_copyright(author: str) -> None:
    verdict = classify_rights(author, "Твір", None, "", "", current_year=CURRENT_YEAR)

    assert verdict["rights_class"] == "in_copyright"
    assert "rehabilitation" in verdict["basis"]


def test_folk_author_is_public_domain() -> None:
    verdict = classify_rights("Народна творчість", "Дума", None, "", "", current_year=CURRENT_YEAR)

    assert verdict["rights_class"] == "public_domain"


def test_unknown_author_defaults_in_copyright() -> None:
    verdict = classify_rights("Іван Невідомий", "Твір", None, "", "", current_year=CURRENT_YEAR)

    assert verdict["rights_class"] == "in_copyright"
    assert verdict["basis"] == "conservative default (unknown)"


def test_pre_1929_year_is_public_domain_fallback() -> None:
    verdict = classify_rights("Іван Невідомий", "Твір", 1928, "", "", current_year=CURRENT_YEAR)

    assert verdict["rights_class"] == "public_domain"


def test_boundary_death_years(tmp_path: Path) -> None:
    rights_path = tmp_path / "authors_rights.yaml"
    rights_path.write_text(
        """
"Boundary PD":
  death_year: 1955
"Boundary Copyright":
  death_year: 1956
""",
        encoding="utf-8",
    )

    pd_verdict = classify_rights(
        "Boundary PD",
        "Твір",
        None,
        "",
        "",
        current_year=CURRENT_YEAR,
        rights_path=rights_path,
    )
    copyright_verdict = classify_rights(
        "Boundary Copyright",
        "Твір",
        None,
        "",
        "",
        current_year=CURRENT_YEAR,
        rights_path=rights_path,
    )

    assert pd_verdict["rights_class"] == "public_domain"
    assert copyright_verdict["rights_class"] == "in_copyright"


def test_generate_readings_gate_delegates_to_classifier() -> None:
    corpus = CorpusText(
        chunk_id="x",
        author="Василь Стус",
        work="Вірш",
        work_id="stus",
        year=None,
        genre="poetry",
        language_period="modern",
        source_file="ukrlib-poetry",
        source_url="",
        text="",
    )

    assert is_public_domain(corpus, current_year=CURRENT_YEAR) is False
