"""Removal-only containment regressions for #9160."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from scripts.audit.generate_practice_deck import JsonVesumVerifier, _build_lexeme, main
from scripts.audit.practice_quality_gate import audit_practice_shards
from scripts.practice.meaning_containment import (
    REVIEWED_WRONG_LEMMAS,
    english_head,
    load_sum11_definitions,
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


@pytest.mark.parametrize(
    ("raw", "head"),
    [
        ("1) bill, check; 2) score", "bill"),
        ("to avoid Conjugation: 1st", "to avoid"),
        ("numeral first", "first"),
        ("anatomy: tooth", "tooth"),
        ("(imperfective) to move", "to move"),
        ("with pronoun or adverb, meaning any", ""),
        ("masculine possessive of учи́тель", ""),
        ("short form of пе́вний", ""),
        ("introducing adverbial clause", ""),
        ("indicating time", ""),
    ],
)
def test_english_dictionary_markers_and_fragments(raw: str, head: str) -> None:
    assert english_head(raw) == head


def test_same_word_sum11_is_rejected() -> None:
    assert meaning_problem("Звичайне пояснення слова", "тест", ["Звичайне пояснення слова."]) == "same_word_sum11"


def test_sum11_lookup_folds_ukrainian_capitalization(tmp_path: Path) -> None:
    db = tmp_path / "sources.db"
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE sum11 (word TEXT, definition TEXT)")
        conn.execute("INSERT INTO sum11 VALUES (?, ?)", ("слово", "Звичайне пояснення слова."))
    assert load_sum11_definitions({"Слово"}, db)["Слово"] == ["Звичайне пояснення слова."]


def test_existing_attributed_english_is_retained() -> None:
    entry = {"lemma": "тест", "gloss": "test", "enrichment": {"translation": {"en": ["test"], "source": "learner_english_gloss"}}}
    assert source_bound_meaning(entry, "test", "test", None) == (
        {"source": "learner_english_gloss", "field": "enrichment.translation.en"}, None
    )


def test_only_the_supported_atlas_head_is_displayed() -> None:
    entry = {"lemma": "тест", "gloss": "test; examination", "enrichment": {
        "translation": {"en": ["test (trial)"], "source": "learner_english_gloss"}
    }}
    assert source_bound_meaning(entry, "test; examination", "test", None)[1] == "unattributed_english"
    entry["enrichment"]["translation"]["en"].append("examination")
    assert source_bound_meaning(entry, "test", "test", None)[0] is not None
    assert source_bound_meaning(entry, "examination", "examination", None, level="A1")[1] == "unbound_english_sense"


def test_existing_beginner_english_may_use_a_single_attributed_head() -> None:
    entry = {"lemma": "тест", "gloss": "Пояснення", "enrichment": {
        "translation": {"en": ["explanation"], "source": "learner_english_gloss"}
    }}
    assert source_bound_meaning(entry, "explanation", "explanation", None, level="A1")[0] is not None
    assert source_bound_meaning(entry, "explanation", "explanation", None, level="A2")[0] is not None


@pytest.mark.parametrize(
    ("atlas", "candidate", "expected"),
    [
        ("pharmacist, pharmacy worker", "pharmacist (dispenses medicine)", "pharmacist"),
        ("American", "American man", "American"),
        ("fairy tale (folktale)", "(dated) fairy tale (folktale)", "fairy tale"),
    ],
)
def test_supported_english_head_survives_extra_text(atlas: str, candidate: str, expected: str) -> None:
    entry = {"lemma": "тест", "url_slug": "test", "gloss": atlas, "pos": "noun", "cefr": "A2",
             "enrichment": {"translation": {"en": [candidate], "source": "dmklinger"}}}
    result = _build_lexeme(entry, JsonVesumVerifier({}), {})
    assert result is not None
    assert result["gloss"] == expected
    assert result["meaningSource"] is not None


def test_unaligned_ukrainian_gloss_with_multiple_english_heads_stays_withheld() -> None:
    entry = {"lemma": "тест", "url_slug": "test", "gloss": "українське значення", "pos": "noun", "cefr": "A2",
             "enrichment": {"translation": {"en": ["lie", "bark"], "source": "dmklinger"}}}
    result = _build_lexeme(entry, JsonVesumVerifier({}), {})
    assert result is not None
    assert result["gloss"] == result["glossClean"] == ""
    assert result["meaningWithheldReason"] == "unbound_english_sense"


def test_attributive_noun_label_does_not_displace_adjective_meaning() -> None:
    entry = {"lemma": "тест", "url_slug": "test", "gloss": "motivation (attributive), motivational",
             "pos": "adjective", "cefr": "B2", "enrichment": {"translation": {
                 "en": ["motivational (tending to motivate)", "motivation (attributive), motivational"],
                 "source": "dmklinger"}}}
    result = _build_lexeme(entry, JsonVesumVerifier({}), {})
    assert result is not None
    assert result["gloss"] == "motivational"
    assert result["meaningSource"] is not None


_EVALUATION_EXPECTED = {
    "словник": "dictionary", "успішно": "successfully", "одягатися": "to get dressed",
    "щеплення": "vaccination", "рік": "year", "перший": "first",
    "прем'єра": "premiere", "як-от": "for example", "буквально": "literally",
    "приборкати": "to tame", "спростувати": "to refute", "сила": "strength",
    "безсоння": "insomnia", "під'їзд": "building entrance",
    "водночас": "at the same time", "стрічка": "ribbon", "лиман": "estuary",
    "зосереджуватися": "to concentrate", "бирка": "label", "бризнути": "to splash",
    # These attributed rows still lack a defensible literal/single-sense head.
    "конфлікт": "", "виконуватися": "", "замітка": "", "потемнілий": "",
}


@pytest.mark.parametrize(
    "entry",
    json.loads((Path(__file__).parent / "fixtures/meaning_9160_eval_cases.json").read_text(encoding="utf-8")),
    ids=lambda entry: entry["lemma"],
)
def test_independent_evaluation_rows_follow_source_bound_classes(entry: dict) -> None:
    """Six held-out errors and all 18 audited over-withheld rows are pinned."""
    result = _build_lexeme(entry, JsonVesumVerifier({}), {})
    assert result is not None
    expected = _EVALUATION_EXPECTED[entry["lemma"]]
    assert result["gloss"] == result["glossClean"] == expected
    assert bool(result["meaningSource"]) == bool(expected)
    assert bool(result["meaningWithheldReason"]) != bool(expected)


def test_english_does_not_replace_a_ukrainian_display() -> None:
    entry = {"lemma": "тест", "gloss": "Пояснення", "enrichment": {"translation": {"en": ["explanation"], "source": "dmklinger"}}}
    assert source_bound_meaning(entry, "Пояснення", "Пояснення", None)[0] is None


def test_reverse_index_is_not_an_attributed_meaning() -> None:
    entry = {"lemma": "тест", "gloss": "test", "enrichment": {"translation": {"en": ["test"], "source": "e2u reverse index"}}}
    assert source_bound_meaning(entry, "test", "test", None)[1] == "unsupported_english_source"
    sense = {"id": "test_s1", "source": "e2u reverse index", "learner_en": ["test"]}
    assert source_bound_meaning(entry, "test", "test", sense)[1] == "unsupported_english_source"


def test_withheld_lexeme_keeps_nonmeaning_record() -> None:
    entry = {"lemma": "тест", "url_slug": "test", "gloss": "Прикм. до слова", "pos": "adj",
             "enrichment": {"cefr": {"level": "B1"}}}
    lexeme = _build_lexeme(entry, JsonVesumVerifier({}), {})
    assert lexeme is not None
    assert lexeme["lemmaId"] == "test"
    assert lexeme["gloss"] == lexeme["glossClean"] == ""
    assert lexeme["meaningMcEligible"] is False


def test_production_builder_requires_same_word_source_snapshot(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--sources-db", str(tmp_path / "missing.db")]) == 1
    assert "requires --sources-db" in capsys.readouterr().err


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
