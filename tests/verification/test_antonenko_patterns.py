"""Book-rule positives, sense negatives and clean-text holdout for #9640."""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from scripts.curriculum.resolver.tokenize import tokenize
from scripts.verification import antonenko_patterns as patterns
from scripts.verification.antonenko_patterns import BOOK, PATTERNS, find_book_calques
from scripts.verification.check_text import _is_closed_class_token, check_text
from scripts.verification.vesum import verify_words

FIXTURES = Path(__file__).with_name("antonenko_fixtures.json")
FIXTURE_DATA = json.loads(FIXTURES.read_text())
CLEAN_SENTENCES = FIXTURE_DATA["clean_sentences"]
MORPHOLOGY = FIXTURE_DATA["morphology"]


@pytest.fixture
def hermetic_check(monkeypatch, tmp_path):
    """Exercise orchestration with source-verified, frozen VESUM readings."""
    module = importlib.import_module("scripts.verification.check_text")
    db = tmp_path / "vesum.db"
    db.touch()
    monkeypatch.setattr(module, "_vesum_path_resolved", lambda: db)
    monkeypatch.setattr(module, "verify_words", lambda words, **kw: {w: MORPHOLOGY.get(w.lower(), []) for w in words})
    monkeypatch.setattr(module, "_vesum_version", lambda: "fixture")
    monkeypatch.setattr(module, "source_info", lambda: {"fixture": True})
    monkeypatch.setattr(
        module, "check_russian_patterns_batch", lambda words, **kw: {w: {"matches_russian": False} for w in words}
    )
    monkeypatch.setattr(module, "_morph_uk", type("Morph", (), {"parse": staticmethod(lambda word: [])})())
    return module


@pytest.mark.parametrize("pattern", PATTERNS, ids=lambda p: p.id)
def test_each_pattern_positive_and_sense_negative(pattern, hermetic_check):
    findings = find_book_calques(pattern.positive, tokenize(pattern.positive), MORPHOLOGY)
    hit = next(f for f in findings if f["detail"]["pattern_id"] == pattern.id)
    assert hit["detail"]["evidence"] == {
        "source": BOOK,
        "source_file": "antonenko-davydovych-yak-my-hovorymo",
        "chunk_id": pattern.chunk_id,
    }
    assert pattern.positive[hit["start"] : hit["end"]] == hit["form"]
    expected_status = patterns.TEMPORAL_PROTIAH_STATUS if pattern.id == "temporal-protiah" else "documented_calque"
    assert hit["detail"]["status"] == expected_status
    result = hermetic_check.check_text(text=pattern.positive, checks=["russian_shadow"])
    destination, empty = ("suspicions", "problems") if expected_status == "suspicion" else ("problems", "suspicions")
    public_hit = next(f for f in result[destination] if f["detail"]["pattern_id"] == pattern.id)
    assert public_hit["detail"]["status"] == expected_status
    assert public_hit["detail"]["evidence"] == hit["detail"]["evidence"]
    assert not any(f["detail"].get("pattern_id") == pattern.id for f in result[empty])
    if expected_status == "suspicion":
        assert public_hit["detail"]["label"] == "suspicion, not a verdict"
    assert not find_book_calques(pattern.negative, tokenize(pattern.negative), MORPHOLOGY)


@pytest.mark.parametrize("form", FIXTURE_DATA["participation_forms"])
def test_entire_vesum_participation_paradigms(form):
    text = f"Ми {form} участь у конкурсі"
    assert any(
        f["detail"]["pattern_id"] == "participation" for f in find_book_calques(text, tokenize(text), MORPHOLOGY)
    )


@pytest.mark.parametrize(
    "text",
    [
        "Ми будемо приймати активну участь у конкурсі",
        "На протязі двох років ми працювали",
        "На протязі цього року ми працювали",
        "Він робить вигляд, що\nне розуміє",
    ],
)
def test_adjectives_auxiliaries_and_duration(text):
    assert find_book_calques(text, tokenize(text), MORPHOLOGY)


@pytest.mark.parametrize(
    "text",
    [
        "Ми приймаємо. Участь у конкурсі важлива",
        "Ми приймаємо, участь у конкурсі важлива",
        "Ми приймаємо test участь у конкурсі",
        "Ми приймаємо 2 участь у конкурсі",
        "Ми приймаємо гостей. Участь у конкурсі важлива",
        "На протязі. Року ще немає",
        "На протязі, року ще немає",
        "На протязі біля дверей холодно",
        "Не сиди на протязі",
        "Він робить вигляд. Що це означає",
        "Сильний протяг заважає працювати",
        "Назва Безчасся з'явилася на екрані",
        "Ми купили радіо і телефон",
    ],
)
def test_boundaries_proper_names_and_borrowings(text):
    assert not find_book_calques(text, tokenize(text), MORPHOLOGY)


def test_unavailable_morphology_never_guesses_inflections():
    text = "Ми приймаємо участь у конкурсі"
    assert not find_book_calques(text, tokenize(text), {})


@pytest.mark.parametrize("word", ["Я", "я", "і", "він", "що", "мою", "усіх"])
def test_vesum_closed_class_readings(word):
    assert _is_closed_class_token(word, MORPHOLOGY)


def test_shadow_suppresses_closed_class_even_at_full_confidence(hermetic_check, monkeypatch):
    monkeypatch.setattr(
        hermetic_check,
        "check_russian_patterns_batch",
        lambda words, **kw: {w: {"matches_russian": True, "confidence": 1.0} for w in words},
    )
    result = check_text(text="Я і він", checks=["russian_shadow"])
    assert result["problems"] == result["suspicions"] == []


def test_phrase_dedup_item_locations_and_truncation(hermetic_check):
    items = [
        {"id": "a", "text": "Ми приймаємо участь. Ми приймаємо участь"},
        {"id": "b", "text": "Ми приймаємо участь"},
    ]
    result = check_text(items=items, checks=["russian_shadow"], max_findings=200)
    finding = next(f for f in result["problems"] if f["detail"].get("pattern_id") == "participation")
    assert finding["locations"] == [["a", 3, 19], ["a", 24, 40], ["b", 3, 19]]
    assert finding["detail"]["status"] == "documented_calque"
    split = check_text(
        items=[{"id": 1, "text": "Ми приймаємо"}, {"id": 2, "text": "участь"}], checks=["russian_shadow"]
    )
    assert not any(f["detail"].get("pattern_id") for f in split["problems"])


def test_book_findings_respect_max_findings(hermetic_check):
    result = check_text(
        text="Ми приймаємо участь. На протязі року ми працювали", checks=["russian_shadow"], max_findings=1
    )
    assert result["summary"]["truncated"] is True
    assert result["summary"]["uncut_count"] == 2
    assert result["problems"][0]["detail"]["pattern_id"] == "participation"
    assert result["suspicions"] == []


def test_curated_and_book_evidence_share_one_finding(hermetic_check, monkeypatch):
    monkeypatch.setattr(hermetic_check, "CURATED_CALQUES", {"бажаючі": {"corrections": ["охочі"]}})
    result = check_text(text="Усі бажаючі повинні записатися", checks=["russian_shadow"])
    assert len(result["problems"]) == 1
    assert result["problems"][0]["detail"]["curated"] is True
    assert result["problems"][0]["detail"]["evidence"]["source"] == BOOK


def test_book_evidence_supersedes_only_same_span_shadow_suspicion(hermetic_check, monkeypatch):
    monkeypatch.setattr(
        hermetic_check,
        "check_russian_patterns_batch",
        lambda words, **kw: {w: {"matches_russian": w.lower() == "заключна", "confidence": 0.8} for w in words},
    )
    text = "Це заключна вистава. Назва Заключна з'явилася на екрані"
    result = check_text(text=text, checks=["russian_shadow"])
    assert len(result["problems"]) == len(result["suspicions"]) == 1
    assert result["problems"][0]["detail"]["pattern_id"] == "concluding"
    assert result["problems"][0]["locations"] == [[None, 3, 11]]
    assert result["suspicions"][0]["locations"] == [[None, 27, 35]]

    single = check_text(text="Це заключна вистава", checks=["russian_shadow"])
    assert len(single["problems"]) == 1
    assert single["suspicions"] == []


def test_proper_name_reading_is_never_book_evidence():
    text = "Безчасся"
    morphology = {"безчасся": [{"lemma": "безчасся", "pos": "noun", "tags": "noun:prop"}]}
    assert not find_book_calques(text, tokenize(text), morphology)


@pytest.mark.parametrize("text", CLEAN_SENTENCES + FIXTURE_DATA["sense_sentences"])
def test_fixed_clean_corpus_no_phrase_findings(text):
    assert not find_book_calques(text, tokenize(text), MORPHOLOGY)
    assert all(MORPHOLOGY.get(t.lookup.lower()) for t in tokenize(text))


def test_live_all_checks_clean_corpus(requires_vesum_db, requires_sources_db):
    assert len(CLEAN_SENTENCES) >= 30
    for text in CLEAN_SENTENCES:
        result = check_text(text=text)
        assert result.get("status") != "error", result
        assert result["problems"] == result["suspicions"] == [], (text, result)


def test_live_recommendations_vesum(requires_vesum_db):
    words = list({t.lookup for p in PATTERNS for t in tokenize(p.recommended)})
    assert all(verify_words(words).values())


def test_live_evidence_chunks_contain_condemned_forms(requires_sources_db):
    import sqlite3

    from scripts.verification.check_text import _sources_path_resolved
    from scripts.verification.verify_antonenko_citations import audit_citations

    with sqlite3.connect(_sources_path_resolved().resolve().as_uri() + "?mode=ro", uri=True) as conn:
        result = audit_citations(conn)
    assert result["verified"] == len(PATTERNS)
    assert result["failures"] == [], result
