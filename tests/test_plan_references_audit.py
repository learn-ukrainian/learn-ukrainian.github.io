"""Smoke tests for ``scripts/audit/plan_references_audit``.

The audit is deterministic against ``data/sources.db`` + plan YAMLs;
these tests exercise the resolver logic on synthetic fixtures so the
production DB is not needed.

Run: ``.venv/bin/pytest tests/test_plan_references_audit.py -v``
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from audit.plan_references_audit import (
    PAGED_CITATION_RE,
    Citation,
    _audit_citation,
    _classify_level_mismatch,
    _source_files_for,
)


@pytest.fixture
def fake_db(tmp_path: Path) -> Path:
    db = tmp_path / "fake_sources.db"
    conn = sqlite3.connect(str(db))
    conn.executescript(
        """
        CREATE TABLE textbooks (
            id INTEGER PRIMARY KEY,
            chunk_id TEXT NOT NULL DEFAULT '',
            title TEXT NOT NULL DEFAULT '',
            text TEXT NOT NULL DEFAULT '',
            source_file TEXT NOT NULL DEFAULT '',
            grade TEXT DEFAULT '',
            author TEXT DEFAULT '',
            char_count INTEGER DEFAULT 0
        );
        """
    )
    rows = [
        # year-suffix file — matched by `%-translit-%`
        (
            "4-klas-ukrayinska-mova-zaharijchuk-2021-1_s0162",
            "Сторінка 100",
            "Зворотні дієслова закінчуються на -ся. Вмиватися, "
            "одягатися, чесатися.",
            "4-klas-ukrayinska-mova-zaharijchuk-2021-1",
            "4",
            "zaharijchuk",
        ),
        # no-year-suffix file — matched only by `%-translit`
        (
            "4-klas-ukrmova-zaharijchuk_s0050",
            "Сторінка 50",
            "Іменник позначає предмет.",
            "4-klas-ukrmova-zaharijchuk",
            "4",
            "",
        ),
        # Grade 10 textbook for level-mismatch + topic-mismatch cases
        (
            "10-klas-ukrmova-karaman-2018_s0176",
            "Сторінка 99",
            "Запозичена лексика із тюркських мов: кинджал, орда, отаман.",
            "10-klas-ukrmova-karaman-2018",
            "10",
            "karaman",
        ),
    ]
    conn.executemany(
        "INSERT INTO textbooks (chunk_id, title, text, source_file, "
        "grade, author) VALUES (?, ?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    conn.close()
    return db


def test_paged_citation_regex_matches_canonical_form():
    text = "Some prose Караман Grade 10, p.179 trailing"
    m = PAGED_CITATION_RE.search(text)
    assert m is not None
    assert m.group(1) == "Караман"
    assert m.group(2) == "10"
    assert m.group(3) == "179"


def test_paged_citation_regex_accepts_ukrainian_s_dot():
    text = "Варзацька Grade 4, с. 38 — повна таблиця"
    m = PAGED_CITATION_RE.search(text)
    assert m is not None
    assert m.group(1) == "Варзацька"
    assert m.group(3) == "38"


def test_level_mismatch_thresholds():
    assert _classify_level_mismatch("a1", 7) is True
    assert _classify_level_mismatch("a1", 6) is False
    assert _classify_level_mismatch("a2", 10) is True
    assert _classify_level_mismatch("a2", 9) is False
    assert _classify_level_mismatch("b1", 10) is False


def test_source_files_for_fixed_pattern_catches_no_year_file(fake_db: Path):
    """The FIXED matcher must find `4-klas-ukrmova-zaharijchuk` (no
    year suffix) alongside the dated 2021 file."""
    with sqlite3.connect(str(fake_db)) as conn:
        conn.row_factory = sqlite3.Row
        files = _source_files_for(conn, ["zaharijchuk"], 4)
    assert "4-klas-ukrmova-zaharijchuk" in files
    assert "4-klas-ukrayinska-mova-zaharijchuk-2021-1" in files


def test_audit_citation_topic_mismatch(fake_db: Path):
    cite = Citation(
        plan_slug="my-morning",
        level="a1",
        raw="Караман Grade 10, p.176",
        author="Караман",
        grade=10,
        page=176,
        field_source="references",
        ref_index=0,
    )
    plan_text = (
        "Моє ранкове життя зворотні дієслова вмиватися одягатися "
        "чистити зуби сніданок"
    )
    with sqlite3.connect(str(fake_db)) as conn:
        conn.row_factory = sqlite3.Row
        finding = _audit_citation(cite, plan_text, conn)
    # Plan is about morning reflexive verbs; chunk is about Turkic loanwords.
    assert finding.mode == "TOPIC_MISMATCH"
    assert "тюркських" in finding.chunk_preview or "Запозичена" in finding.chunk_preview


def test_audit_citation_ok_when_topic_matches(fake_db: Path):
    cite = Citation(
        plan_slug="my-morning",
        level="a2",
        raw="Захарійчук Grade 4, p.162",
        author="Захарійчук",
        grade=4,
        page=162,
        field_source="references",
        ref_index=0,
    )
    plan_text = (
        "Моє ранкове життя: зворотні дієслова, вмиватися, "
        "одягатися, чесатися — на -ся."
    )
    with sqlite3.connect(str(fake_db)) as conn:
        conn.row_factory = sqlite3.Row
        finding = _audit_citation(cite, plan_text, conn)
    assert finding.mode == "OK", (finding.mode, finding.detail, finding.overlap)


def test_audit_citation_unknown_author_for_uncatalogued_name(fake_db: Path):
    """An author absent from CANONICAL_TRANSLITS flags UNKNOWN_AUTHOR.

    Previously this test exercised the SUGGESTED_TRANSLITS path with
    `Літвінова`, but those entries have since been promoted into
    CANONICAL_TRANSLITS — a fictional name preserves the regression on
    the UNKNOWN_AUTHOR mode.
    """
    cite = Citation(
        plan_slug="euphony",
        level="a1",
        raw="Неіснуючий Grade 5, p.174",
        author="Неіснуючий",
        grade=5,
        page=174,
        field_source="references",
        ref_index=0,
    )
    with sqlite3.connect(str(fake_db)) as conn:
        conn.row_factory = sqlite3.Row
        finding = _audit_citation(cite, "Милозвучність", conn)
    assert finding.mode == "UNKNOWN_AUTHOR"


def test_audit_citation_ghost_page(fake_db: Path):
    cite = Citation(
        plan_slug="my-morning",
        level="a2",
        raw="Захарійчук Grade 4, p.999",
        author="Захарійчук",
        grade=4,
        page=999,
        field_source="references",
        ref_index=0,
    )
    with sqlite3.connect(str(fake_db)) as conn:
        conn.row_factory = sqlite3.Row
        finding = _audit_citation(cite, "ранок", conn)
    assert finding.mode == "GHOST_PAGE"


def test_audit_citation_ghost_source(fake_db: Path):
    cite = Citation(
        plan_slug="x",
        level="a1",
        raw="Міщенко Grade 4, p.10",
        author="Міщенко",
        grade=4,
        page=10,
        field_source="references",
        ref_index=0,
    )
    with sqlite3.connect(str(fake_db)) as conn:
        conn.row_factory = sqlite3.Row
        finding = _audit_citation(cite, "test plan text", conn)
    # Міщенко exists in TRANSLITS but not for Grade 4 in our fixture
    assert finding.mode == "GHOST_SOURCE"
