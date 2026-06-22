from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from scripts.readings.textbook_curation import load_sections, lookup_curation, main


def test_exact_work_and_author_match_has_high_confidence(tmp_path: Path) -> None:
    db_path = _write_sources_db(tmp_path)
    sections = load_sections(db_path)

    result = lookup_curation("Тіні забутих предків", "Михайло Коцюбинський", sections)

    assert result["in_school_canon"] is True
    assert result["confidence"] == 1.0
    assert result["grades"] == [10]
    assert result["best_hit"] is not None
    assert result["best_hit"]["source_file"] == "10-klas-ukrlit-avramenko-2018"
    assert "full_text" not in result["best_hit"]
    assert result["excerpt_boundary"] == {
        "page_start": 141,
        "page_end": 142,
        "full_text_chars": len(TINI_TEXT),
        "source_file": "10-klas-ukrlit-avramenko-2018",
        "section_title": "Михайло Коцюбинський. Повість «Тіні забутих предків» ⦿ 141",
    }


def test_pua_page_decoration_matches_clean_demanded_work(tmp_path: Path) -> None:
    db_path = _write_sources_db(tmp_path)
    sections = load_sections(db_path)

    result = lookup_curation("Камінний хрест", "Василь Стефаник", sections)

    assert result["in_school_canon"] is True
    assert result["confidence"] == 1.0
    assert result["best_hit"] is not None
    assert result["best_hit"]["work_match"] == "exact"
    assert result["excerpt_boundary"] is not None
    assert result["excerpt_boundary"]["page_start"] == 149
    assert result["excerpt_boundary"]["page_end"] == 150


def test_false_positive_guard_keeps_substring_only_hit_low_confidence(
    tmp_path: Path,
) -> None:
    db_path = _write_sources_db(tmp_path)
    sections = load_sections(db_path)

    result = lookup_curation("Маруся", "Григорій Квітка-Основ'яненко", sections)

    assert result["in_school_canon"] is False
    assert result["confidence"] == 0.4
    assert result["grades"] == []
    assert result["best_hit"] is not None
    assert result["best_hit"]["section_title"] == "Ліна Костенко. Роман «Маруся Чурай» ⦿ 99"
    assert result["best_hit"]["work_match"] == "substring"
    assert result["best_hit"]["author_match"] is False


def test_no_matching_textbook_section_returns_empty_result(tmp_path: Path) -> None:
    db_path = _write_sources_db(tmp_path)
    sections = load_sections(db_path)

    result = lookup_curation(
        "A Historical Phonology of the Ukrainian Language",
        "Shevelov",
        sections,
    )

    assert result["in_school_canon"] is False
    assert result["confidence"] == 0.0
    assert result["hit_count"] == 0
    assert result["best_hit"] is None
    assert result["excerpt_boundary"] is None
    assert result["hits"] == []


def test_cli_work_author_prints_json(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    db_path = _write_sources_db(tmp_path)

    exit_code = main(
        [
            "--db",
            str(db_path),
            "--work",
            "Заповіт",
            "--author",
            "Тарас Шевченко",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["in_school_canon"] is True
    assert payload["grades"] == [0]
    assert payload["excerpt_boundary"]["full_text_chars"] == len(ZAPOVIT_TEXT)


def test_cli_manifest_writes_summary_with_expected_keys(tmp_path: Path) -> None:
    db_path = _write_sources_db(tmp_path)
    plans_dir = _write_plan_fixture(tmp_path)
    out_path = tmp_path / "primary_text_curation.json"

    exit_code = main(
        [
            "--manifest",
            "--db",
            str(db_path),
            "--plans-dir",
            str(plans_dir),
            "--out",
            str(out_path),
        ]
    )

    assert exit_code == 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["summary"] == {
        "total_works": 2,
        "in_canon_count": 1,
        "high_confidence_count": 1,
        "no_hit_count": 1,
    }
    assert sorted(payload["summary"]) == [
        "high_confidence_count",
        "in_canon_count",
        "no_hit_count",
        "total_works",
    ]
    assert len(payload["entries"]) == 2


KAMIN_TEXT = "Камінний хрест. " * 320
TINI_TEXT = "Тіні забутих предків. " * 220
ZAPOVIT_TEXT = "Заповіт. " * 140
MARUSIA_TEXT = "Маруся Чурай. " * 100
FOREST_TEXT = "Лісова пісня. " * 180


def _write_sources_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "sources.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE textbook_sections (
                section_id INTEGER,
                source_file TEXT,
                grade INTEGER,
                section_title TEXT,
                section_number TEXT,
                page_start INTEGER,
                page_end INTEGER,
                chunk_count INTEGER,
                full_text TEXT
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO textbook_sections (
                section_id,
                source_file,
                grade,
                section_title,
                section_number,
                page_start,
                page_end,
                chunk_count,
                full_text
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    1,
                    "10-klas-ukrlit-avramenko-2018",
                    10,
                    "Василь Стефаник. Новела «Камінний хрест» \ue000 149",
                    "1",
                    149,
                    150,
                    2,
                    KAMIN_TEXT,
                ),
                (
                    2,
                    "lesson-222",
                    0,
                    "Lesson 222: Українська поезія. Тарас Шевченко «Заповіт»",
                    "222",
                    None,
                    None,
                    8,
                    ZAPOVIT_TEXT,
                ),
                (
                    3,
                    "10-klas-ukrlit-avramenko-2018",
                    10,
                    "Михайло Коцюбинський. Повість «Тіні забутих предків» ⦿ 141",
                    "3",
                    141,
                    142,
                    2,
                    TINI_TEXT,
                ),
                (
                    4,
                    "11-klas-ukrlit",
                    11,
                    "Ліна Костенко. Роман «Маруся Чурай» ⦿ 99",
                    "4",
                    99,
                    100,
                    1,
                    MARUSIA_TEXT,
                ),
                (
                    5,
                    "10-klas-ukrlit-avramenko-2018",
                    10,
                    "Леся Українка. Драма-феєрія «Лісова пісня» ⦿ 177",
                    "5",
                    177,
                    178,
                    2,
                    FOREST_TEXT,
                ),
            ],
        )
    return db_path


def _write_plan_fixture(tmp_path: Path) -> Path:
    plans_dir = tmp_path / "plans"
    (plans_dir / "lit").mkdir(parents=True)
    (plans_dir / "lit" / "kaminnyi-khrest.yaml").write_text(
        """
grade: LIT
references:
  - title: Камінний хрест
    author: Василь Стефаник
    type: primary
  - title: A Historical Phonology of the Ukrainian Language
    author: Shevelov
    type: primary
""",
        encoding="utf-8",
    )
    return plans_dir
