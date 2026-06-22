from __future__ import annotations

from pathlib import Path

import pytest

from scripts.readings.generate_readings import CorpusText, is_public_domain
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
        "Шевченко Т.",
        "Шевченко Т.Г.",
        "Тарас Шевченко",
        "Шевченко",
    ],
)
def test_shevchenko_initial_and_name_order_variants_use_author_table(
    author: str,
) -> None:
    verdict = classify_rights(author, "Твір", 1814, "", "modern", current_year=CURRENT_YEAR)

    assert verdict["rights_class"] == "public_domain"
    assert "death_year" in verdict["basis"]
    assert "life+70" in verdict["basis"]
    assert "publication-year" not in verdict["basis"]


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


def test_premodern_track_is_public_domain_without_year() -> None:
    verdict = classify_rights("Невідомий книжник", "Твір", None, "", "oes", current_year=CURRENT_YEAR)

    assert verdict["rights_class"] == "public_domain"
    assert verdict["basis"] == "pre-modern track/work before 1800"


def test_unknown_author_defaults_in_copyright() -> None:
    verdict = classify_rights("Іван Невідомий", "Твір", None, "", "", current_year=CURRENT_YEAR)

    assert verdict["rights_class"] == "in_copyright"
    assert verdict["basis"] == "conservative default (author not in rights table)"


def test_unknown_author_with_old_year_defaults_in_copyright() -> None:
    verdict = classify_rights("Іван Невідомий", "Твір", 1928, "", "", current_year=CURRENT_YEAR)

    assert verdict["rights_class"] == "in_copyright"
    assert verdict["basis"] == "conservative default (author not in rights table)"


@pytest.mark.parametrize(
    ("author", "year"),
    [
        ("Драй-Хмара М.", 1889),
        ("Маланюк Є.", 1897),
        ("Малишко А.", 1912),
    ],
)
def test_risky_author_misses_do_not_fall_back_to_year_pd(
    author: str,
    year: int,
) -> None:
    verdict = classify_rights(author, "Твір", year, "", "modern", current_year=CURRENT_YEAR)

    assert verdict["rights_class"] == "in_copyright"
    assert "publication-year" not in verdict["basis"]


def test_boundary_death_years(tmp_path: Path) -> None:
    rights_path = tmp_path / "authors_rights.yaml"
    rights_path.write_text(
        """
"Boundary PD":
  death_year: 1955
"Boundary Copyright":
  death_year: 1956
"Rehab PD":
  death_year: 1937
  repressed_rehabilitated: true
  rehab_year: 1955
"Rehab Copyright":
  death_year: 1937
  repressed_rehabilitated: true
  rehab_year: 1956
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
    rehab_pd_verdict = classify_rights(
        "Rehab PD",
        "Твір",
        None,
        "",
        "",
        current_year=CURRENT_YEAR,
        rights_path=rights_path,
    )
    rehab_copyright_verdict = classify_rights(
        "Rehab Copyright",
        "Твір",
        None,
        "",
        "",
        current_year=CURRENT_YEAR,
        rights_path=rights_path,
    )

    assert pd_verdict["rights_class"] == "public_domain"
    assert copyright_verdict["rights_class"] == "in_copyright"
    assert rehab_pd_verdict["rights_class"] == "public_domain"
    assert "rehabilitation+70" in rehab_pd_verdict["basis"]
    assert rehab_copyright_verdict["rights_class"] == "in_copyright"
    assert "rehabilitation+70" in rehab_copyright_verdict["basis"]


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
