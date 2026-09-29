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
    candidate_balla_heads,
    english_head,
    load_sum11_definitions,
    meaning_problem,
    source_bound_meaning,
)

_TEST_BALLA = {"test": ["тест"], "examination": ["тест"], "explanation": ["тест"]}


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
    assert source_bound_meaning(entry, "test", "test", None, balla=_TEST_BALLA) == (
        {"source": "learner_english_gloss", "field": "enrichment.translation.en"}, None
    )


def test_only_the_supported_atlas_head_is_displayed() -> None:
    entry = {"lemma": "тест", "gloss": "test; examination", "enrichment": {
        "translation": {"en": ["test (trial)"], "source": "learner_english_gloss"}
    }}
    assert source_bound_meaning(entry, "test; examination", "test", None, balla=_TEST_BALLA)[1] == "unattributed_english"
    entry["enrichment"]["translation"]["en"].append("examination")
    assert source_bound_meaning(entry, "test", "test", None, balla=_TEST_BALLA)[0] is not None
    assert source_bound_meaning(entry, "examination", "examination", None, level="A1", balla=_TEST_BALLA)[1] == "unbound_english_sense"


def test_existing_beginner_english_may_use_a_single_attributed_head() -> None:
    entry = {"lemma": "тест", "gloss": "Пояснення", "enrichment": {
        "translation": {"en": ["explanation"], "source": "learner_english_gloss"}
    }}
    assert source_bound_meaning(entry, "explanation", "explanation", None, level="A1", balla=_TEST_BALLA)[0] is not None
    assert source_bound_meaning(entry, "explanation", "explanation", None, level="A2", balla=_TEST_BALLA)[0] is not None


def test_balla_lookup_includes_candidate_on_ukrainian_atlas_row() -> None:
    entry = {"lemma": "тест", "gloss": "Пояснення", "enrichment": {
        "translation": {"en": ["explanation"], "source": "learner_english_gloss"}}}
    assert "explanation" in candidate_balla_heads([entry])


@pytest.mark.parametrize(
    ("atlas", "candidate", "expected"),
    [
        ("pharmacist, pharmacy worker", "pharmacist (dispenses medicine)", "pharmacist"),
        ("American", "American man", ""),
        ("fairy tale (folktale)", "(dated) fairy tale (folktale)", "fairy tale (folktale)"),
    ],
)
def test_supported_english_head_survives_extra_text(atlas: str, candidate: str, expected: str) -> None:
    entry = {"lemma": "тест", "url_slug": "test", "gloss": atlas, "pos": "noun", "cefr": "A2",
             "enrichment": {"translation": {"en": [candidate], "source": "dmklinger"}}}
    result = _build_lexeme(entry, JsonVesumVerifier({}), {})
    assert result is not None
    assert result["gloss"] == expected
    assert bool(result["meaningSource"]) == bool(expected)


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
    "зосереджуватися": "to concentrate (to approach or meet in a common center)",
    "бирка": "label", "бризнути": "to splash",
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
    expected = _EVALUATION_EXPECTED[entry["lemma"]]
    balla_head = english_head(expected).removeprefix("to ").removeprefix("be ")
    balla = {balla_head: [entry["lemma"]]} if expected else {}
    result = _build_lexeme(entry, JsonVesumVerifier({}), {}, balla)
    assert result is not None
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


@pytest.mark.parametrize(
    ("lemma", "gloss", "candidates", "source", "balla", "level", "expected"),
    [
        ("дно", "bed (of a river), bottom (of a lake)", ["bed (of a river), bottom (of a lake)"],
         "dmklinger", {"bed": ["5) русло (ріки); дно (моря)"]}, "B1", "bed (of a river)"),
        ("ураження", "impression (overall effect of something)", ["impression (overall effect of something)"],
         "dmklinger", {"impression": ["1) враження"]}, "B1", ""),
        ("електронний", "electron (attributive)", ["(relational) electron (attributive)"],
         "dmklinger", {"electron": ["n фіз. електрон ~ microscope — електронний мікроскоп"]}, "A1", ""),
        ("музичний", "music (adjective), musical", ["music (adjective), musical"],
         "learner_english_gloss", {"music": ["1) музика"], "musical": ["1) музичний"]}, "A1", ""),
        ("тікати", "to tick (of a clock)", ["(intransitive) to tick (of a clock)"],
         "dmklinger", {"tick": ["1) цокання годинника"]}, "A1", ""),
        ("слізний", "tear (water from the eyes); lacrimal", ["tear (water from the eyes)"],
         "learner_english_gloss", {"tear": ["1) сльоза"]}, "B1", ""),
    ],
)
def test_qualified_head_requires_same_lemma_independent_support(
    lemma: str, gloss: str, candidates: list[str], source: str,
    balla: dict[str, list[str]], level: str, expected: str,
) -> None:
    entry = {"lemma": lemma, "url_slug": lemma, "gloss": gloss, "pos": "noun", "cefr": level,
             "enrichment": {"translation": {"en": candidates, "source": source}}}
    result = _build_lexeme(entry, JsonVesumVerifier({}), {}, balla)
    assert result is not None
    assert result["gloss"] == result["glossClean"] == expected
    assert bool(result["meaningSource"]) == bool(expected)


@pytest.mark.parametrize("text", [
    "used before awkward consonant clusters and chiefly before мно́ю",
    "female equivalent of нача́льник", "endearing form of мале́нький",
    "female equivalent of незнайо́мець", "female equivalent of однокла́сник",
    "kiwi 2",
])
def test_cross_reference_and_numbered_english_fragments_are_withheld(text: str) -> None:
    assert meaning_problem(text, "тест") == "dictionary_fragment"


def test_balla_example_is_not_a_headword_mapping() -> None:
    entry = {"lemma": "електронний", "gloss": "electron", "enrichment": {
        "translation": {"en": ["electron"], "source": "dmklinger"}}}
    assert source_bound_meaning(entry, "electron", "electron", None,
                                balla={"electron": ["n фіз. електрон ~ microscope — електронний мікроскоп"]})[1] == "unsupported_independent_head"


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
