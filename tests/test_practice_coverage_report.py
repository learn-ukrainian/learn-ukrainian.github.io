"""Tests for scripts.practice.coverage_report (WP0 Practice inventory)."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.practice.coverage_report import (
    SCHEMA,
    UNIQUE_LEMMA_BAR,
    build_coverage_report,
    format_table,
    main,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "practice_coverage"
PRACTICE_DIR = FIXTURES / "lexicon"
ZNO_DIR = FIXTURES / "zno"
TEACHER_TABLE = FIXTURES / "teacher" / "lexicon-teacher-table-deck.json"


def test_build_coverage_report_fixture_inventory() -> None:
    report = build_coverage_report(
        practice_dir=PRACTICE_DIR,
        zno_dir=ZNO_DIR,
        teacher_table=TEACHER_TABLE,
    )

    assert report["schema"] == SCHEMA
    assert report["schema"] == "practice-coverage-report.v1"
    assert report["unique_lemma_bar"] == UNIQUE_LEMMA_BAR

    # flashcards: дім, кіт, вода, свобода, ефемерний → 5 unique across levels
    assert report["modes"]["flashcards"]["unique_lemmas_all_levels"] == 5
    assert report["modes"]["flashcards"]["below_1000"] is True
    assert report["modes"]["flashcards"]["by_level"] == {"A1": 3, "B2": 2, "C1": 2}

    # synonym: вода (A1), свобода (B2), ефемерний (C1) → 3
    assert report["modes"]["synonym"]["unique_lemmas_all_levels"] == 3
    assert report["modes"]["synonym"]["by_level"] == {"A1": 1, "B2": 1, "C1": 1}

    # дім appears in A1+B2 stress; unique global stress = дім + кіт = 2
    assert report["modes"]["stress"]["unique_lemmas_all_levels"] == 2
    assert report["modes"]["stress"]["by_level"] == {"A1": 2, "B2": 1}

    assert "paradigm" in report["modes_below_1000"]
    assert "flashcards" in report["modes_below_1000"]

    # B2 / C1 are first-class sections, not folded into all-levels only.
    assert report["b2"]["lexeme_count"] == 2
    assert report["b2"]["modes"]["flashcards"] == 2
    assert report["b2"]["modes"]["paradigm"] == 1
    assert report["c1"]["lexeme_count"] == 2
    assert report["c1"]["modes"]["heritage"] == 1
    assert report["c1"]["modes"]["paronym"] == 1

    assert report["zno_decks"]["stress"] == {
        "path": "practice-zno.stress.json",
        "item_count": 3,
        "thinDeck": True,
        "exam": {"nmt": 1, "zno": 2},
    }
    assert report["zno_decks"]["paronym"]["item_count"] == 1
    assert report["zno_decks"]["paronym"]["thinDeck"] is True
    assert report["zno_decks"]["paronym"]["exam"] == {"zno": 1}

    assert report["teacher_table"] == {
        "present": True,
        "path": "lexicon-teacher-table-deck.json",
        "lemma_keys_count": 3,
    }


def test_teacher_table_absent(tmp_path: Path) -> None:
    missing = tmp_path / "missing-teacher.json"
    report = build_coverage_report(
        practice_dir=PRACTICE_DIR,
        zno_dir=ZNO_DIR,
        teacher_table=missing,
    )
    assert report["teacher_table"]["present"] is False
    assert report["teacher_table"]["lemma_keys_count"] is None


def test_cli_writes_json_and_table(tmp_path: Path, capsys) -> None:
    out = tmp_path / "coverage-report.json"
    rc = main(
        [
            "--practice-dir",
            str(PRACTICE_DIR),
            "--zno-dir",
            str(ZNO_DIR),
            "--teacher-table",
            str(TEACHER_TABLE),
            "--json-out",
            str(out),
            "--table",
        ]
    )
    assert rc == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["schema"] == "practice-coverage-report.v1"
    assert payload["modes"]["flashcards"]["unique_lemmas_all_levels"] == 5
    captured = capsys.readouterr()
    assert "Mode" in captured.out
    assert "B2 section:" in captured.out
    assert "C1 section:" in captured.out
    assert "ZNO decks:" in captured.out
    assert "Teacher table keys: 3" in captured.out
    # format_table is stable for empty-ish reports too
    assert "flashcards" in format_table(payload)
