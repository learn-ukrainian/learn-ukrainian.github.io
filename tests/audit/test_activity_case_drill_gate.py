"""Unit tests for #5917 activity case-drill audit gate on VESUM indeclinables."""

import sqlite3
from pathlib import Path

import pytest

from scripts.audit.checks.activity_validation import (
    _check_word_indeclinable,
    check_indeclinable_case_drills,
)
from scripts.verification.vesum import VESUM_DB_PATH, _resolve_vesum_db_path
from scripts.yaml_activities import FillInActivity, FillInItem


@pytest.fixture
def vesum_fixture_db(tmp_path: Path) -> Path:
    """Create a minimal VESUM sqlite database fixture for testing."""
    db_path = tmp_path / "vesum_fixture.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "CREATE TABLE forms (word_form TEXT, lemma TEXT, pos TEXT, tags TEXT)"
    )
    rows = [
        # завдяки (prep - non-casing POS)
        ("завдяки", "завдяки", "prep", "prep"),
        # книга (noun - declinable, 3 distinct forms)
        ("книга", "книга", "noun", "noun:inanim:f:v_naz"),
        ("книжку", "книга", "noun", "noun:inanim:f:v_zna"),
        ("книзі", "книга", "noun", "noun:inanim:f:v_mis"),
        # два (numr - declinable numeral)
        ("два", "два", "numr", "numr:m:v_naz"),
        ("двох", "два", "numr", "numr:m:v_rod"),
        ("двом", "два", "numr", "numr:m:v_dav"),
        # метро (noun - indeclinable, only 1 distinct form)
        ("метро", "метро", "noun", "noun:inanim:n:nv:v_naz"),
        # згодом (adv - non-casing POS)
        ("згодом", "згодом", "adv", "adv"),
    ]
    conn.executemany("INSERT INTO forms VALUES (?, ?, ?, ?)", rows)
    conn.commit()
    conn.close()
    return db_path


def test_zavdiaky_case_drill_must_fail(vesum_fixture_db: Path):
    """Acceptance test: case drill on 'завдяки' (prep) must FAIL the gate."""
    activity = FillInActivity(
        type="fill-in",
        title="Preposition Case Drill",
        instruction="Put the word „завдяки” in the correct case.",
        items=[
            FillInItem(
                sentence="___ допомозі друзів ми закінчили проект.",
                answer="Завдяки",
                options=["Завдяки", "Завдякам"],
            )
        ],
    )
    violations = check_indeclinable_case_drills([activity], db_path=vesum_fixture_db)
    assert len(violations) == 1
    assert violations[0]["type"] == "INDECLINABLE_CASE_DRILL"
    assert violations[0]["severity"] == "critical"
    assert "завдяки" in violations[0]["message"]
    assert "prep" in violations[0]["message"] or "prep" in violations[0]["pedagogical_issue"]


def test_real_noun_case_drill_must_pass(vesum_fixture_db: Path):
    """Control test: case drill on 'книга' (noun) must PASS the gate."""
    activity = FillInActivity(
        type="fill-in",
        title="Noun Case Drill",
        instruction="Put the word „книга” in the correct case.",
        items=[
            FillInItem(
                sentence="Я читаю цікаву ___.",
                answer="книжку",
                options=["книга", "книжку", "книзі"],
            )
        ],
    )
    violations = check_indeclinable_case_drills([activity], db_path=vesum_fixture_db)
    assert len(violations) == 0


def test_numeral_case_drill_must_pass(vesum_fixture_db: Path):
    """Control test: case drill on numeral 'два' (numr) must PASS the gate (#5956)."""
    activity = FillInActivity(
        type="fill-in",
        title="Numeral Case Drill",
        instruction="Put the number „два” in the correct case.",
        items=[
            FillInItem(
                sentence="У мене немає ___ гривень.",
                answer="двох",
                options=["два", "двох", "двом"],
            )
        ],
    )
    violations = check_indeclinable_case_drills([activity], db_path=vesum_fixture_db)
    assert len(violations) == 0


def test_indeclinable_neutral_prompt_must_pass(vesum_fixture_db: Path):
    """Control test: neutral insertion prompt on 'завдяки' must PASS the gate."""
    activity = FillInActivity(
        type="fill-in",
        title="Preposition Practice",
        instruction="Fill in the blank with the word „завдяки”.",
        items=[
            FillInItem(
                sentence="___ допомозі друзів ми закінчили проект.",
                answer="Завдяки",
                options=["Завдяки", "Завдякам"],
            )
        ],
    )
    violations = check_indeclinable_case_drills([activity], db_path=vesum_fixture_db)
    assert len(violations) == 0


def test_indeclinable_noun_case_drill_must_fail(vesum_fixture_db: Path):
    """Control test: case drill on indeclinable noun 'метро' must FAIL the gate."""
    activity = FillInActivity(
        type="fill-in",
        title="Indeclinable Noun Drill",
        instruction="Поставте слово „метро” у правильному відмінку.",
        items=[
            FillInItem(
                sentence="Ми їдемо в ___.",
                answer="метро",
                options=["метро"],
            )
        ],
    )
    violations = check_indeclinable_case_drills([activity], db_path=vesum_fixture_db)
    assert len(violations) == 1
    assert violations[0]["type"] == "INDECLINABLE_CASE_DRILL"
    assert "метро" in violations[0]["message"]


def test_ukrainian_adverb_case_drill_must_fail(vesum_fixture_db: Path):
    """Case drill on 'згодом' (adv) with Ukrainian prompt must FAIL the gate."""
    activity = {
        "type": "fill-in",
        "title": "Adverb Drill",
        "instruction": "Поставте слово „згодом” у правильному відмінку.",
        "items": [
            {
                "sentence": "___ він відповів.",
                "answer": "згодом",
                "options": ["згодом", "потім"],
            }
        ],
    }
    violations = check_indeclinable_case_drills([activity], db_path=vesum_fixture_db)
    assert len(violations) == 1
    assert violations[0]["type"] == "INDECLINABLE_CASE_DRILL"
    assert "згодом" in violations[0]["message"]


def test_item_level_prompt_case_drill_must_fail(vesum_fixture_db: Path):
    """Item-level prompt demanding case form of indeclinable must FAIL."""
    activity = {
        "type": "fill-in",
        "title": "Preposition Quiz",
        "instruction": "Complete the sentence.",
        "items": [
            {
                "question": "Which case form of „завдяки” should be used here?",
                "sentence": "___ допомозі...",
                "answer": "Завдяки",
                "options": ["Завдяки"],
            }
        ],
    }
    violations = check_indeclinable_case_drills([activity], db_path=vesum_fixture_db)
    assert len(violations) == 1
    assert violations[0]["type"] == "INDECLINABLE_CASE_DRILL"


def test_missing_vesum_db_raises_or_reports_unavailable(tmp_path: Path):
    """F001 requirement: missing VESUM DB must NOT return silent clean."""
    missing_db = tmp_path / "nonexistent_vesum.db"
    activity = FillInActivity(
        type="fill-in",
        title="Preposition Case Drill",
        instruction="Put the word „завдяки” in the correct case.",
        items=[FillInItem(sentence="___ допомозі...", answer="Завдяки", options=["Завдяки"])],
    )
    # 1. Direct call to _check_word_indeclinable propagates FileNotFoundError
    with pytest.raises(FileNotFoundError):
        _check_word_indeclinable("завдяки", db_path=missing_db)

    # 2. check_indeclinable_case_drills emits VESUM_DB_UNAVAILABLE violation (not empty list)
    violations = check_indeclinable_case_drills([activity], db_path=missing_db)
    assert len(violations) == 1
    assert violations[0]["type"] == "VESUM_DB_UNAVAILABLE"
    assert violations[0]["severity"] == "critical"
    assert "gate could not run — VESUM DB unavailable" in violations[0]["message"]


def test_no_ancestor_dir_walk_for_vesum_db():
    """F002 requirement: _resolve_vesum_db_path does NOT walk parent directories."""
    resolved = _resolve_vesum_db_path(None)
    assert resolved == VESUM_DB_PATH
