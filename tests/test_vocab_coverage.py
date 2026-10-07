"""Tests for plan-required vocabulary coverage validation."""

from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

vocab_coverage = import_module("build.phases.vocab_coverage")
_extract_ukrainian_term = vocab_coverage._extract_ukrainian_term
check_vocab_coverage = vocab_coverage.check_vocab_coverage


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


def test_inflection_via_vesum_lemma(tmp_path: Path, requires_vesum_db, monkeypatch) -> None:
    monkeypatch.setattr(vocab_coverage, "VESUM_DB_PATH", requires_vesum_db)

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
