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
    _candidate_alternatives,
    candidate_balla_heads,
    english_candidates_support_display,
    english_head,
    load_sum11_definitions,
    meaning_problem,
    source_bound_meaning,
    split_english_alternatives,
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


@pytest.mark.parametrize("raw", [
    "intensified form of (superlative) найкра́ще (najkrášče)",
    "form of інший", "alternative form of інший", "diminutive of інший",
    "endearing form of інший", "female equivalent of інший",
    "male equivalent of інший", "a specific spelling of інший",
    "alternative letter-case form of інший", "dialectal form of інший",
    "used as a friendly form of інший",
])
def test_cross_reference_source_vocabulary_cannot_become_a_head(raw: str) -> None:
    assert english_head(raw) == ""
    assert _candidate_alternatives(raw) == set()


def test_mixed_script_fragment_is_rejected_before_qualifier_splitting() -> None:
    raw = "intensified form of (superlative) найкра́ще (najkrášče)"
    entry = {"lemma": "якнайкраще", "url_slug": "якнайкраще", "gloss": "прислівник до якнайкращий",
             "pos": "adv", "cefr": "A2", "enrichment": {"translation": {"en": [raw], "source": "kaikki"}}}
    result = _build_lexeme(entry, JsonVesumVerifier({}), {})
    assert result is not None and result["gloss"] == ""


@pytest.mark.parametrize("raw", ["intensified form of another word", "form of another word",
                                "alternative form of another word", "diminutive of another word",
                                "female equivalent of another word", "a specific spelling of another word"])
def test_english_only_cross_reference_stubs_are_not_meanings(raw: str) -> None:
    assert english_head(raw) == ""


@pytest.mark.parametrize(("lemma", "gloss"), [
    ("навколішки", "onto one's knees (get down, get up, fall, etc.)"),
    ("інтелектуальний", "intellectual (pertaining to, or performed by, the intellect)"),
    ("практикувати", "to practise (perform or observe in a habitual fashion; put into practice; apply in practice)"),
    ("зіграти", "to play (to render (a musical title, compositional style, film title, etc.) using a musical instrument or device)"),
])
def test_qualifier_pieces_are_never_top_level_alternatives(lemma: str, gloss: str) -> None:
    assert split_english_alternatives(gloss) == [gloss]
    for piece in ("get up", "or performed by", "put into practice", "compositional style"):
        assert not english_candidates_support_display([gloss], piece)
    entry = {"lemma": lemma, "url_slug": lemma, "gloss": gloss, "pos": "verb", "cefr": "B1",
             "enrichment": {"translation": {"en": [gloss], "source": "dmklinger"}}}
    result = _build_lexeme(entry, JsonVesumVerifier({}), {})
    assert result is not None and result["gloss"] == ""


def test_top_level_slash_is_an_alternative() -> None:
    assert split_english_alternatives("to call / be named") == ["to call", "be named"]
    entry = {"lemma": "звати", "url_slug": "звати", "gloss": "to call / be named", "pos": "verb", "cefr": "A1",
             "enrichment": {"translation": {"en": ["to call"], "source": "learner_english_gloss"}}}
    result = _build_lexeme(entry, JsonVesumVerifier({}), {}, {"call": ["v звати"]})
    assert result is not None and result["gloss"] == "to call"


@pytest.mark.parametrize(("lemma", "gloss", "candidate", "balla", "extra", "expected"), [
    ("очікувати", "to wait for", "to wait for, to await", {"await": ["v очікувати"]}, {}, "to wait for"),
    ("снідати", "to have breakfast", "to have breakfast", {"breakfast": ["v снідати"]}, {}, "to have breakfast"),
    ("збільшити", "to increase", "to increase", {"increase": ["v збільшувати"]},
     {"verb_pedagogy": {"aspect_partner": {"lemma": "збільшувати"}}}, "to increase"),
    ("сірий", "grey", "gray", {"grey": ["adj сірий"]}, {}, "grey"),
    ("довкілля", "environment", "environment", {"environment": ["n середовище"]},
     {"definition_cards": [{"id": "vts", "definitions": ["1》 Навколишнє середовище."]}]}, "environment"),
    ("ремонт", "renovation", "renovation", {"renovation": ["n лагодження"]},
     {"definition_cards": [{"id": "vts", "definitions": ["1》 Лагодження чого-небудь."]}]}, "renovation"),
    ("ураження", "impression", "impression", {"impression": ["n враження"]},
     {"definition_cards": [{"id": "vts", "definitions": ["1》 Дія за значенням уразити."]}]}, ""),
])
def test_independent_support_uses_same_sense_variants_and_forward_evidence(
    lemma: str, gloss: str, candidate: str, balla: dict, extra: dict, expected: str,
) -> None:
    source = "dmklinger" if extra.get("definition_cards") else "learner_english_gloss"
    entry = {"lemma": lemma, "url_slug": lemma, "gloss": gloss, "pos": "noun", "cefr": "A1",
             "enrichment": {"translation": {"en": [candidate], "source": source}, **extra}}
    result = _build_lexeme(entry, JsonVesumVerifier({}), {}, balla)
    assert result is not None and result["gloss"] == expected


def test_learner_list_first_sense_must_fit_atlas_head() -> None:
    entry = {"lemma": "впливати", "url_slug": "впливати", "gloss": "to swim in", "pos": "verb", "cefr": "B1",
             "enrichment": {"translation": {"en": ["to influence, to affect", "to swim in"],
                                            "source": "learner_english_gloss"}}}
    result = _build_lexeme(entry, JsonVesumVerifier({}), {}, {"swim in": ["v впливати"]})
    assert result is not None and result["gloss"] == ""
    assert result["meaningWithheldReason"] == "unbound_english_sense"


@pytest.mark.parametrize(("lemma", "gloss", "candidate", "source", "balla", "extra", "expected"), [
    ("перед", "in front of; before", "1) before something; 2) in front of", "learner_english_gloss",
     {"before": ["prep перед"]}, {}, "in front of"),
    ("змішати", "to mix", "to mix", "dmklinger", {"mix": ["v змішувати"]},
     {"definition_cards": [{"id": "vts", "definitions": ["змішати I див. змішувати ."]}]}, "to mix"),
    ("влаштувати", "to arrange, to establish", "to arrange, to establish", "learner_english_gloss",
     {"arrange": ["v упорядковувати"], "establish": ["v влаштовувати"]},
     {"verb_pedagogy": {"aspect_partner": {"lemma": "влаштовувати"}}}, "to arrange"),
    ("проігнорувати", "to ignore", "to ignore", "dmklinger", {"ignore": ["v ігнорувати"]},
     {"definition_cards": [{"id": "vts", "definitions": ["проігнорувати, док. 1》 Не помітити."]}]}, "to ignore"),
    ("зазначати", "to state, note", "to mention, to note", "dmklinger",
     {"note": ["v зазначати"]}, {}, "to note"),
])
def test_independent_support_handles_source_phrasing_and_recorded_aspect_links(
    lemma: str, gloss: str, candidate: str, source: str, balla: dict, extra: dict, expected: str,
) -> None:
    entry = {"lemma": lemma, "url_slug": lemma, "gloss": gloss, "pos": "verb", "cefr": "B1",
             "enrichment": {"translation": {"en": [candidate], "source": source}, **extra}}
    result = _build_lexeme(entry, JsonVesumVerifier({}), {}, balla)
    assert result is not None and result["gloss"] == expected


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
