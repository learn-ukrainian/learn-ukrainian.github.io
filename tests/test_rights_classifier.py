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
        "Тичина",
        "Рильський",
    ],
)
def test_unpersecuted_recent_author_no_free_source_is_in_copyright(author: str) -> None:
    # Recent authors who were NOT persecuted fall to the conservative life+70 path.
    verdict = classify_rights(author, "Твір", None, "", "", current_year=CURRENT_YEAR)

    assert verdict["rights_class"] == "in_copyright"


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


def test_ukrlib_rylskyi_is_retrieval_only_under_existing_rights_gate() -> None:
    verdict = classify_rights(
        "Максим Рильський",
        "Молюсь і вірю",
        None,
        "ukrlib-rylsky",
        "modern",
        current_year=CURRENT_YEAR,
    )

    assert verdict["rights_class"] == "in_copyright"
    assert "death_year 1964" in verdict["basis"]


@pytest.mark.parametrize(
    ("current_year", "expected_rights_class"),
    [(2034, "in_copyright"), (2035, "public_domain")],
)
def test_rylskyi_life_plus_70_boundary(
    current_year: int,
    expected_rights_class: str,
) -> None:
    verdict = classify_rights(
        "Максим Рильський", "Молюсь і вірю", None, "ukrlib-rylsky", "modern", current_year=current_year
    )

    assert verdict["rights_class"] == expected_rights_class


@pytest.mark.parametrize(
    ("current_year", "expected_rights_class"),
    [(2012, "in_copyright"), (2013, "public_domain")],
)
def test_teliha_life_plus_70_boundary(
    current_year: int,
    expected_rights_class: str,
) -> None:
    verdict = classify_rights(
        "Олена Теліга", "Сучасникам", None, "ukrlib-teliha", "modern", current_year=current_year
    )

    assert verdict["rights_class"] == expected_rights_class


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
        # Authors NOT in the rights table, with NO free-source signal: the unreliable
        # birth-year must NOT trigger a year-based PD fallback. (Драй-Хмара is now a
        # tabled persecuted author → hosted; covered by the repressed-heritage test.)
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
"Rehab Early":
  death_year: 1937
  repressed_rehabilitated: true
  rehab_year: 1955
"Rehab Late":
  death_year: 1937
  repressed_rehabilitated: true
  rehab_year: 1989
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
    rehab_early_verdict = classify_rights(
        "Rehab Early",
        "Твір",
        None,
        "",
        "",
        current_year=CURRENT_YEAR,
        rights_path=rights_path,
    )
    rehab_late_verdict = classify_rights(
        "Rehab Late",
        "Твір",
        None,
        "",
        "",
        current_year=CURRENT_YEAR,
        rights_path=rights_path,
    )

    assert pd_verdict["rights_class"] == "public_domain"
    assert copyright_verdict["rights_class"] == "in_copyright"
    # Persecuted-and-rehabilitated authors are hosted heritage regardless of rehab year.
    assert rehab_early_verdict["rights_class"] == "public_domain"
    assert "repressed" in rehab_early_verdict["basis"]
    assert rehab_late_verdict["rights_class"] == "public_domain"
    assert "repressed" in rehab_late_verdict["basis"]


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
    # Стус — murdered by the Soviet regime, his work freely published on ukrlib — is
    # hosted in full. The gate delegates to the classifier, which never gatekeeps
    # persecuted Ukrainian authors or ukrlib/textbook texts (user order 2026-06-22).
    hosted = CorpusText(
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
    assert is_public_domain(hosted, current_year=CURRENT_YEAR) is True

    retrieval_only = CorpusText(
        chunk_id="rylsky",
        author="Максим Рильський",
        work="Молюсь і вірю",
        work_id="rylsky",
        year=1895,
        genre="poetry",
        language_period="modern",
        source_file="ukrlib-rylsky",
        source_url="https://www.ukrlib.com.ua/books/printit.php?tid=6176",
        text="",
    )
    assert is_public_domain(retrieval_only, current_year=CURRENT_YEAR) is False

    # Delegation also returns False for a genuinely-unknown modern author with no
    # free-source signal (the light legal backstop).
    unknown = CorpusText(
        chunk_id="y",
        author="Сучасний Невідомий Автор",
        work="Вірш",
        work_id="unknown",
        year=None,
        genre="poetry",
        language_period="modern",
        source_file="private-collection",
        source_url="",
        text="",
    )
    assert is_public_domain(unknown, current_year=CURRENT_YEAR) is False
