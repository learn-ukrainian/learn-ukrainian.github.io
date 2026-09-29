"""Removal-only containment regressions for #9160."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from scripts.audit.generate_practice_deck import JsonVesumVerifier, _build_lexeme
from scripts.audit.practice_quality_gate import audit_practice_shards
from scripts.practice.meaning_containment import (
    REVIEWED_WRONG_LEMMAS,
    meaning_problem,
    source_bound_meaning,
)


@pytest.mark.parametrize("lemma", sorted(REVIEWED_WRONG_LEMMAS))
def test_all_reviewed_wrong_senses_are_quarantined(lemma: str) -> None:
    assert meaning_problem("ordinary meaning", lemma) == "reviewed_wrong_sense"


@pytest.mark.parametrize(
    ("text", "reason"),
    [
        ("Це визначення. Інший текст далі.", "dictionary_fragment"),
        ("Текст «прикладу»", "example_quotation"),
        ("Текст (Автор, 1985)", "dated_citation"),
        ("Прикм. до слова", "dictionary_fragment"),
        ("Присл. до слова", "dictionary_fragment"),
        ("Дієприкм. до слова", "dictionary_fragment"),
        ("слово 1》 значення", "dictionary_fragment"),
        ("слово || значення", "dictionary_fragment"),
        ("СЛОВО, ч. значення", "dictionary_fragment"),
    ],
)
def test_prohibited_patterns(text: str, reason: str) -> None:
    assert meaning_problem(text, "тест") == reason


def test_same_word_sum11_is_rejected() -> None:
    assert meaning_problem("Звичайне пояснення слова", "тест", ["Звичайне пояснення слова."]) == "same_word_sum11"


def test_existing_attributed_english_is_retained() -> None:
    entry = {"lemma": "тест", "gloss": "test", "enrichment": {"translation": {"en": ["test"], "source": "learner_english_gloss"}}}
    assert source_bound_meaning(entry, "test", "test", None) == (
        {"source": "learner_english_gloss", "field": "enrichment.translation.en"}, None
    )


def test_all_displayed_english_alternatives_need_source_support() -> None:
    entry = {"lemma": "тест", "gloss": "test; examination", "enrichment": {
        "translation": {"en": ["test (trial)"], "source": "learner_english_gloss"}
    }}
    assert source_bound_meaning(entry, "test; examination", "test", None)[1] == "unattributed_english"
    entry["enrichment"]["translation"]["en"].append("examination")
    assert source_bound_meaning(entry, "test; examination", "test", None)[0] is not None


def test_a1_existing_english_scaffold_may_match_an_attributed_field() -> None:
    entry = {"lemma": "тест", "gloss": "Пояснення", "enrichment": {
        "translation": {"en": ["explanation"], "source": "learner_english_gloss"}
    }}
    assert source_bound_meaning(entry, "explanation", "explanation", None, level="A1")[0] is not None
    assert source_bound_meaning(entry, "explanation", "explanation", None, level="A2")[0] is None


def test_english_does_not_replace_a_ukrainian_display() -> None:
    entry = {"lemma": "тест", "gloss": "Пояснення", "enrichment": {"translation": {"en": ["explanation"], "source": "dmklinger"}}}
    assert source_bound_meaning(entry, "Пояснення", "Пояснення", None)[0] is None


def test_reverse_index_is_not_an_attributed_meaning() -> None:
    entry = {"lemma": "тест", "gloss": "test", "enrichment": {"translation": {"en": ["test"], "source": "e2u reverse index"}}}
    assert source_bound_meaning(entry, "test", "test", None)[1] == "unsupported_english_source"


def test_withheld_lexeme_keeps_nonmeaning_record() -> None:
    entry = {"lemma": "тест", "url_slug": "test", "gloss": "Прикм. до слова", "pos": "adj",
             "enrichment": {"cefr": {"level": "B1"}}}
    lexeme = _build_lexeme(entry, JsonVesumVerifier({}), {})
    assert lexeme is not None
    assert lexeme["lemmaId"] == "test"
    assert lexeme["gloss"] == lexeme["glossClean"] == ""
    assert lexeme["meaningMcEligible"] is False


def test_gate_handles_empty_sources_database(tmp_path: Path) -> None:
    db = tmp_path / "empty.db"
    sqlite3.connect(db).close()
    (tmp_path / "practice-lexemes.A1.json").write_text(
        json.dumps({"lexemes": [{"lemmaId": "x", "lemma": "тест", "gloss": "test", "glossClean": "test",
                                "meaningSource": {"source": "source", "field": "translation.en"}}]}), encoding="utf-8"
    )
    _, violations = audit_practice_shards(tmp_path, verify_vesum=False, check_volume=False, sources_db=db)
    assert any(item["type"] == "SOURCE_DB_INVALID" for item in violations)


def test_gate_checks_both_meaning_fields_without_optional_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.audit import practice_quality_gate

    monkeypatch.setattr(practice_quality_gate, "DEFAULT_SOURCES_DB", tmp_path / "absent.db")
    (tmp_path / "practice-lexemes.A1.json").write_text(
        json.dumps({"lexemes": [{"lemmaId": "x", "lemma": "тест", "gloss": "test",
                                "glossClean": "test (Author, 1980)",
                                "meaningSource": {"source": "source", "field": "translation.en"}}]}), encoding="utf-8"
    )
    _, violations = audit_practice_shards(tmp_path, verify_vesum=False, check_volume=False)
    assert any(item["type"] == "UNSAFE_PRACTICE_MEANING" and "glossClean" in item["message"] for item in violations)
    assert not any(item["type"] == "SOURCE_DB_INVALID" for item in violations)
