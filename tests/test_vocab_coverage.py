"""Tests for plan-required vocabulary coverage validation."""

from __future__ import annotations

import sqlite3
import sys
from importlib import import_module
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

vocab_coverage = import_module("build.phases.vocab_coverage")
_extract_ukrainian_term = vocab_coverage._extract_ukrainian_term
check_vocab_coverage = vocab_coverage.check_vocab_coverage


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _write_plan(tmp_path: Path, required: list[str]) -> Path:
    path = tmp_path / "plan.yaml"
    path.write_text(
        yaml.safe_dump(
            {"vocabulary_hints": {"required": required, "recommended": []}},
            allow_unicode=True,
            sort_keys=False,
        ),
        "utf-8",
    )
    return path


def _write_vocab(tmp_path: Path, words: list[str]) -> Path:
    path = tmp_path / "vocab.yaml"
    path.write_text(
        yaml.safe_dump(
            {"vocabulary": [{"word": word} for word in words]},
            allow_unicode=True,
            sort_keys=False,
        ),
        "utf-8",
    )
    return path


def _vesum_has_sound_lemma() -> bool:
    db_path = vocab_coverage.VESUM_DB_PATH
    if not db_path.exists() or db_path.stat().st_size == 0:
        return False
    try:
        with sqlite3.connect(str(db_path)) as db:
            for query in (
                "SELECT lemma FROM vesum WHERE form = ? LIMIT 1",
                "SELECT lemma FROM forms WHERE word_form = ? LIMIT 1",
            ):
                try:
                    singular = db.execute(query, ("звук",)).fetchone()
                    plural = db.execute(query, ("звуки",)).fetchone()
                except sqlite3.OperationalError:
                    continue
                if singular and plural and singular[0] == plural[0]:
                    return True
    except sqlite3.Error:
        return False
    return False


def test_all_required_present_passes(tmp_path: Path) -> None:
    plan_path = _write_plan(tmp_path, ["звук (sound)", "привіт (hi)"])
    vocab_path = _write_vocab(tmp_path, ["звук", "привіт"])

    result = check_vocab_coverage(plan_path, vocab_path)

    assert result.passed is True
    assert result.missing_terms == ()
    assert result.present_mapping == {"звук": "звук", "привіт": "привіт"}


def test_missing_term_fails(tmp_path: Path) -> None:
    plan_path = _write_plan(tmp_path, ["молоко (milk)"])
    vocab_path = _write_vocab(tmp_path, ["вода"])

    result = check_vocab_coverage(plan_path, vocab_path)

    assert result.passed is False
    assert result.missing_terms == ("молоко",)


def test_stress_marks_ignored(tmp_path: Path) -> None:
    plan_path = _write_plan(tmp_path, ["привіт (hi)"])
    vocab_path = _write_vocab(tmp_path, ["приві\u0301т"])

    result = check_vocab_coverage(plan_path, vocab_path)

    assert result.passed is True
    assert result.missing_terms == ()


def test_capitalization_ignored(tmp_path: Path) -> None:
    plan_path = _write_plan(tmp_path, ["як справи (how are you)"])
    vocab_path = _write_vocab(tmp_path, ["Як справи?"])

    result = check_vocab_coverage(plan_path, vocab_path)

    assert result.passed is True
    assert result.missing_terms == ()


def test_punctuation_ignored(tmp_path: Path) -> None:
    plan_path = _write_plan(tmp_path, ["До побачення (Goodbye)"])
    vocab_path = _write_vocab(tmp_path, ["До побачення!"])

    result = check_vocab_coverage(plan_path, vocab_path)

    assert result.passed is True
    assert result.missing_terms == ()


def test_inflection_via_vesum_lemma(tmp_path: Path) -> None:
    if not _vesum_has_sound_lemma():
        pytest.skip("VESUM DB with звук/звуки lemma data is not available")

    plan_path = _write_plan(tmp_path, ["звук (sound)"])
    vocab_path = _write_vocab(tmp_path, ["звуки"])

    result = check_vocab_coverage(plan_path, vocab_path)

    assert result.passed is True
    assert result.missing_terms == ()


def test_distinct_terms_do_not_match(tmp_path: Path) -> None:
    plan_path = _write_plan(tmp_path, ["звук (sound)"])
    vocab_path = _write_vocab(tmp_path, ["звичайний"])

    result = check_vocab_coverage(plan_path, vocab_path)

    assert result.passed is False
    assert result.missing_terms == ("звук",)


def test_ukrainian_term_extraction() -> None:
    assert _extract_ukrainian_term("Добрий день (Good day — formal)") == "Добрий день"


def test_a1_1_sounds_letters_golden() -> None:
    plan_path = (
        PROJECT_ROOT
        / "curriculum/l2-uk-en/plans/a1/sounds-letters-and-hello.yaml"
    )
    vocab_path = (
        PROJECT_ROOT
        / "curriculum/l2-uk-en/a1/vocabulary/sounds-letters-and-hello.yaml"
    )

    result = check_vocab_coverage(plan_path, vocab_path)

    assert result.passed is True
    assert result.missing_terms == ()
