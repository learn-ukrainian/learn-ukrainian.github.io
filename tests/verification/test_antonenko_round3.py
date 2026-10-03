"""Final-round #9640 counterexamples using frozen live verify_words readings."""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from scripts.curriculum.resolver.tokenize import tokenize
from scripts.verification import antonenko_patterns as patterns
from scripts.verification.antonenko_patterns import _duration_case, _genitive_modifier, find_book_calques

FIXTURE_DATA = json.loads(Path(__file__).with_name("antonenko_round3_fixtures.json").read_text())
MORPHOLOGY = FIXTURE_DATA["morphology"]


@pytest.mark.parametrize("text", FIXTURE_DATA["blockers"] + FIXTURE_DATA["correct"])
def test_correct_draught_durations_have_no_book_finding(text):
    findings = find_book_calques(text, tokenize(text), MORPHOLOGY)
    if "на протязі" in text.lower():
        assert len(findings) == 1
        assert findings[0]["detail"]["status"] == "suspicion"
    else:
        assert findings == []


@pytest.mark.parametrize("text", FIXTURE_DATA["regressions"] + FIXTURE_DATA["incorrect"])
def test_temporal_calques_follow_status_switch(text):
    findings = find_book_calques(text, tokenize(text), MORPHOLOGY)
    assert len(findings) == 1
    finding = findings[0]
    assert finding["detail"]["pattern_id"] == "temporal-protiah"
    assert finding["detail"]["status"] == patterns.TEMPORAL_PROTIAH_STATUS
    assert finding["detail"]["evidence"]["chunk_id"].endswith("_p131")
    assert text[finding["start"] : finding["end"]] == finding["form"]


@pytest.mark.parametrize("modifier", ["двох", "кількох", "останніх", "цілого"])
def test_animate_accusative_alternatives_do_not_erase_genitives(modifier):
    assert _genitive_modifier([r for r in MORPHOLOGY[modifier] if r["pos"] in {"adj", "numr"}])


@pytest.mark.parametrize("modifier", ["двох", "кількох"])
def test_postposed_genitive_numerals_remain_matched(modifier):
    text = f"На протязі годин {modifier} ми працювали."
    assert len(find_book_calques(text, tokenize(text), MORPHOLOGY)) == 1


@pytest.mark.parametrize(
    "readings",
    [
        [{"lemma": "modifier", "pos": "adj", "tags": "adj:v_rod:nv"}],
        [
            {"lemma": "modifier", "pos": "adj", "tags": "adj:v_rod"},
            {"lemma": "modifier", "pos": "adj", "tags": "adj:v_zna"},
        ],
        [
            {"lemma": "modifier", "pos": "numr", "tags": "numr:v_rod"},
            {"lemma": "modifier", "pos": "numr", "tags": "numr:v_zna:rinanim"},
        ],
    ],
)
def test_indeclinable_and_plain_accusative_modifiers_withhold(readings):
    # Exercise the tag contract independently of the current dictionary contents.
    assert _duration_case(readings)
    assert not _genitive_modifier(readings)
    morphology = {**MORPHOLOGY, "modifier": readings}
    # Reuse a Cyrillic token; the synthetic lemma is only a reading identifier.
    morphology["цілого"] = morphology.pop("modifier")
    text = "На протязі цілого дня ми працювали."
    findings = find_book_calques(text, tokenize(text), morphology)
    assert len(findings) == 1
    assert findings[0]["detail"]["status"] == "suspicion"


@pytest.mark.parametrize(
    "text",
    [
        "На протязі години. Дві хвилини ми працювали.",
        "На протязі години, зо дві хвилини ми працювали.",
        "На протязі години зо, дві хвилини ми працювали.",
        "На протязі години з двох днів ми працювали.",
        "На протязі години із",
        "На протязі години зо",
        "На протязі години з",
    ],
)
def test_only_adjacent_duration_numerals_withhold(text):
    assert len(find_book_calques(text, tokenize(text), MORPHOLOGY)) == 1


def test_unattested_range_requires_numeral_components():
    text = "На протязі року наша-школа працювала."
    assert len(find_book_calques(text, tokenize(text), MORPHOLOGY)) == 1


def test_missing_morphology_does_not_manufacture_duration():
    text = "На протязі року ми працювали."
    findings = find_book_calques(text, tokenize(text), {})
    assert len(findings) == 1
    assert findings[0]["detail"]["status"] == "suspicion"


def test_all_new_sentence_words_have_frozen_vesum_evidence():
    for text in FIXTURE_DATA["correct"] + FIXTURE_DATA["incorrect"] + FIXTURE_DATA["stopping_rule_cases"]:
        for token in tokenize(text):
            # Range spellings are absent as a whole; both numeral parts attest.
            assert all(MORPHOLOGY.get(part.lower()) for part in token.parts)


@pytest.fixture
def hermetic_checker(monkeypatch, tmp_path):
    checker = importlib.import_module("scripts.verification.check_text")
    db = tmp_path / "vesum.db"
    db.touch()
    monkeypatch.setattr(checker, "_vesum_path_resolved", lambda: db)
    monkeypatch.setattr(checker, "verify_words", lambda words, **kw: {w: MORPHOLOGY.get(w.lower(), []) for w in words})
    monkeypatch.setattr(checker, "_vesum_version", lambda: "fixture")
    monkeypatch.setattr(checker, "source_info", lambda: {"fixture": True})
    monkeypatch.setattr(
        checker, "check_russian_patterns_batch", lambda words, **kw: {w: {"matches_russian": False} for w in words}
    )
    monkeypatch.setattr(checker, "_morph_uk", type("Morph", (), {"parse": staticmethod(lambda word: [])})())
    return checker


@pytest.mark.parametrize(
    "text, expected",
    [(s, False) for s in FIXTURE_DATA["blockers"] + FIXTURE_DATA["correct"]]
    + [(s, True) for s in FIXTURE_DATA["regressions"] + FIXTURE_DATA["incorrect"]],
)
def test_review_cases_through_public_checker(text, expected, hermetic_checker):
    result = hermetic_checker.check_text(text=text, checks=["russian_shadow"])
    destination, empty = (
        ("suspicions", "problems") if patterns.TEMPORAL_PROTIAH_STATUS == "suspicion" else ("problems", "suspicions")
    )
    assert result[empty] == []
    assert len(result[destination]) == 1
    if result[destination]:
        finding = result[destination][0]
        assert finding["detail"]["status"] == patterns.TEMPORAL_PROTIAH_STATUS
        assert finding["detail"]["evidence"]["chunk_id"].endswith("_p131")
        if destination == "suspicions":
            assert finding["detail"]["label"] == "suspicion, not a verdict"


@pytest.mark.parametrize("text", FIXTURE_DATA["stopping_rule_cases"])
def test_stopping_rule_counterexamples_are_at_most_suspicions(text, hermetic_checker):
    assert patterns.TEMPORAL_PROTIAH_STATUS == "suspicion"
    findings = find_book_calques(text, tokenize(text), MORPHOLOGY)
    assert all(f["detail"]["status"] == "suspicion" for f in findings)
    result = hermetic_checker.check_text(text=text, checks=["russian_shadow"])
    assert result["problems"] == []
    assert len(result["suspicions"]) == len(findings)
    for finding in result["suspicions"]:
        assert finding["detail"]["pattern_id"] == "temporal-protiah"
        assert finding["detail"]["status"] == "suspicion"
        assert finding["detail"]["label"] == "suspicion, not a verdict"
        assert finding["detail"]["evidence"]["chunk_id"].endswith("_p131")


@pytest.mark.parametrize("checks", [["russian_shadow"], ["vesum", "russian_shadow"]])
def test_range_parts_do_not_change_whole_token_diagnostics(checks, hermetic_checker):
    result = hermetic_checker.check_text(text="Він постояв на протязі хвилини три-чотири.", checks=checks)
    assert not any(f["detail"].get("pattern_id") == "temporal-protiah" for f in result["problems"])
    if "vesum" in checks:
        assert [f["form"] for f in result["problems"]] == ["три-чотири"]
        assert result["problems"][0]["detail"]["status"] == "no_vesum_row"


@pytest.mark.parametrize("status", ["documented_calque", "suspicion"])
def test_status_switch_routes_through_public_checker(status, monkeypatch, hermetic_checker):
    # Exercise per-candidate routing; the global status is now fallback only.
    original = patterns.classify

    def classified(*args, **kwargs):
        result = original(*args, **kwargs)
        result["status"] = status
        result["evidence"].pop("parser_unavailable", None)
        return result

    monkeypatch.setattr(patterns, "classify", classified)
    checker = hermetic_checker
    result = checker.check_text(
        items=[
            {"id": "a", "text": "На протязі року ми працювали."},
            {"id": "b", "text": "На протязі року ми працювали."},
        ],
        checks=["russian_shadow"],
    )
    destination, empty = ("problems", "suspicions") if status == "documented_calque" else ("suspicions", "problems")
    assert result[empty] == []
    assert len(result[destination]) == 1
    finding = result[destination][0]
    assert finding["detail"]["status"] == status
    assert finding["form"] == "На протязі року"
    assert finding["locations"] == [["a", 0, 15], ["b", 0, 15]]
    assert finding["detail"]["evidence"]["chunk_id"].endswith("_p131")
    if status == "suspicion":
        assert finding["detail"]["label"] == "suspicion, not a verdict"
    other = next(p for p in patterns.PATTERNS if p.id == "dependence")
    assert (
        patterns.find_book_calques(other.positive, tokenize(other.positive), {})[0]["detail"]["status"]
        == "documented_calque"
    )
