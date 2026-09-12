"""Unit tests for Practice Quality Gate (Issue #7944)."""

import json
from pathlib import Path

from scripts.audit.practice_quality_gate import (
    audit_error_correction_deck,
    audit_sentence_inventory,
    audit_teacher_cloze_deck,
    run_all_practice_audits,
)


def test_audit_teacher_cloze_validates_blank_count(tmp_path: Path):
    deck = {
        "cloze": [
            {
                "clozeId": "good_1",
                "sentence": "Це гарне _____ речення.",
                "form": "гарне",
                "options": [{"label": "гарне", "kind": "answer"}, {"label": "погане", "kind": "distractor"}],
            },
            {
                "clozeId": "bad_multi",
                "sentence": "Перше _____ і друге _____ речення.",
                "form": "гарне",
                "options": [{"label": "гарне", "kind": "answer"}, {"label": "погане", "kind": "distractor"}],
            },
        ]
    }
    deck_path = tmp_path / "cloze.json"
    deck_path.write_text(json.dumps(deck, ensure_ascii=False), encoding="utf-8")

    violations = audit_teacher_cloze_deck(deck_path)
    assert any(v["type"] == "INVALID_BLANK_COUNT" and v["item"] == "bad_multi" for v in violations)
    assert not any(v["item"] == "good_1" for v in violations)


def test_audit_teacher_cloze_detects_intentional_error_leak(tmp_path: Path):
    deck = {
        "cloze": [
            {
                "clozeId": "leaked_1",
                "sentence": "НЕПРАВИЛЬНО ПРАВИЛЬНО _____ рішення зволікати з рішенням",
                "form": "затягувати",
                "options": [{"label": "затягувати", "kind": "answer"}, {"label": "робити", "kind": "distractor"}],
            }
        ]
    }
    deck_path = tmp_path / "cloze.json"
    deck_path.write_text(json.dumps(deck, ensure_ascii=False), encoding="utf-8")

    violations = audit_teacher_cloze_deck(deck_path)
    assert any(v["type"] == "INTENTIONAL_ERROR_LEAK" for v in violations)


def test_audit_teacher_cloze_detects_duplicate_options(tmp_path: Path):
    deck = {
        "cloze": [
            {
                "clozeId": "dup_opt",
                "sentence": "Я читаю цікаву _____ увечері.",
                "form": "книгу",
                "options": [
                    {"label": "книгу", "kind": "answer"},
                    {"label": "книгу", "kind": "distractor"},
                ],
            }
        ]
    }
    deck_path = tmp_path / "cloze.json"
    deck_path.write_text(json.dumps(deck, ensure_ascii=False), encoding="utf-8")

    violations = audit_teacher_cloze_deck(deck_path)
    assert any(v["type"] == "DUPLICATE_OPTIONS" for v in violations)


def test_audit_error_correction_validates_contract(tmp_path: Path):
    # Valid drill
    valid_deck = {
        "drills": [
            {
                "id": "drill_good",
                "sentence": "Він приймав участь у зборах.",
                "errorWord": "приймав участь",
                "correctForm": "брав участь",
                "options": ["брав участь", "приймав участь"],
                "explanation": "Калька з російської мови.",
            },
            {
                "id": "drill_missing_target",
                "sentence": "Він прийшов додому вчасно.",
                "errorWord": "приймав участь",
                "correctForm": "брав участь",
                "options": ["брав участь", "приймав участь"],
                "explanation": "Калька з російської мови.",
            },
            {
                "id": "drill_missing_in_options",
                "sentence": "У нього був високий авторитет.",
                "errorWord": "авторитет",
                "correctForm": "престиж",
                "options": ["повага", "визнання"],
                "explanation": "Стилістична заміна.",
            },
        ]
    }
    deck_path = tmp_path / "ec.json"
    deck_path.write_text(json.dumps(valid_deck, ensure_ascii=False), encoding="utf-8")

    violations = audit_error_correction_deck(deck_path)
    assert any(v["type"] == "ERROR_TARGET_NOT_IN_SENTENCE" and v["item"] == "drill_missing_target" for v in violations)
    assert any(
        v["type"] == "CORRECT_TARGET_MISSING_IN_OPTIONS" and v["item"] == "drill_missing_in_options" for v in violations
    )
    assert not any(v["item"] == "drill_good" for v in violations)


def test_audit_sentence_inventory_intentional_errors(tmp_path: Path):
    inv = {
        "rows": [
            {"lemma": "тест", "sentence": "Це звичайне речення."},
            {"lemma": "помилка", "sentence": "Помилку допущено у варіанті А."},
        ]
    }
    inv_path = tmp_path / "inv.json"
    inv_path.write_text(json.dumps(inv, ensure_ascii=False), encoding="utf-8")

    violations = audit_sentence_inventory(inv_path)
    assert len(violations) == 1
    assert violations[0]["type"] == "INTENTIONAL_ERROR_LEAK"


def test_audit_error_correction_vesum_attestation(tmp_path: Path, monkeypatch):
    """Verify that unattested Ukrainian words in error-correction drills are flagged by VESUM."""
    from scripts.audit import practice_quality_gate

    deck = {
        "drills": [
            {
                "id": "drill_valid",
                "sentence": "Він брав участь у зборах.",
                "errorWord": "приймав участь",
                "correctForm": "брав",
                "options": ["брав", "приймав"],
                "explanation": "Калька.",
            },
            {
                "id": "drill_unattested",
                "sentence": "Це неіснуючеслово речення.",
                "errorWord": "помилка",
                "correctForm": "неіснуючеслово",
                "options": ["неіснуючеслово", "варіант"],
                "explanation": "Неіснуюче слово.",
            },
        ]
    }
    deck_path = tmp_path / "ec.json"
    deck_path.write_text(json.dumps(deck, ensure_ascii=False), encoding="utf-8")

    def mock_verify_word(word: str, db_path=None):
        return word == "брав"

    monkeypatch.setattr(practice_quality_gate, "verify_word", mock_verify_word)
    fake_db = tmp_path / "mock_vesum.db"
    fake_db.touch()

    violations = audit_error_correction_deck(deck_path, vesum_db=fake_db)
    assert any(v["type"] == "VESUM_UNATTESTED" and v["item"] == "drill_unattested" for v in violations), (
        f"Expected VESUM_UNATTESTED violation, got: {violations}"
    )


def test_production_practice_quality_gate_passes():
    """Verify that current repository practice datasets pass with 0 violations."""
    results = run_all_practice_audits()
    total_violations = sum(len(v) for v in results.values())
    assert total_violations == 0, f"Practice Quality Gate failed with violations: {results}"
