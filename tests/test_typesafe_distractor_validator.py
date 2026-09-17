"""Tests for TypeSafe Practice Distractor & Misconception Validator (Practice Hub #8174)."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from scripts.practice.typesafe_distractor_validator import (
    DistractorValidationVerdict,
    resolve_api_key,
    validate_practice_card,
)


class DummyAns:
    """Mock answer container mimicking typesafe_sdk answer types."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def test_resolve_api_key_from_env():
    with patch.dict(os.environ, {"TYPESAFE_API_KEY": "practice-test-key"}):
        assert resolve_api_key() == "practice-test-key"


def test_validate_clean_card_mock():
    mock_resp = {
        "model": "jev-test",
        "answers": {
            "distractor_plausibility": DummyAns(score=1.80, confidence=0.95),
            "is_unambiguous": DummyAns(noul=0.95),
            "anti_calque_yield": DummyAns(noul=0.20),
            "card_quality": DummyAns(choice="pass", confidence=0.90),
        },
    }
    verdict = validate_practice_card(
        stem="Вчора ми побачили старого _____ (друг).",
        target="друга",
        distractors=["другові", "другом", "друг"],
        mock_response=mock_resp,
    )
    assert isinstance(verdict, DistractorValidationVerdict)
    assert verdict.verdict == "pass"
    assert verdict.is_unambiguous_prob == 0.95
    assert verdict.plausibility_score == 1.80
    assert not verdict.needs_review


def test_validate_ambiguous_card_mock():
    # Ambiguous drill where a distractor could also be valid in context
    mock_resp = {
        "model": "jev-test",
        "answers": {
            "distractor_plausibility": DummyAns(score=1.20, confidence=0.80),
            "is_unambiguous": DummyAns(noul=0.45),  # Low unambiguous score!
            "anti_calque_yield": DummyAns(noul=0.10),
            "card_quality": DummyAns(choice="pass", confidence=0.60),
        },
    }
    verdict = validate_practice_card(
        stem="Він пішов до лісу з _____ (брат).",
        target="братом",
        distractors=["брати", "братів", "братові"],
        mock_response=mock_resp,
    )
    assert verdict.verdict == "fail_ambiguous"
    assert verdict.needs_review
    assert any("Ambiguity alert" in f for f in verdict.findings)


def test_validate_weak_foils_mock():
    # Distractors are absurd or non-foils
    mock_resp = {
        "model": "jev-test",
        "answers": {
            "distractor_plausibility": DummyAns(score=0.40, confidence=0.85),
            "is_unambiguous": DummyAns(noul=0.98),
            "anti_calque_yield": DummyAns(noul=0.05),
            "card_quality": DummyAns(choice="pass", confidence=0.75),
        },
    }
    verdict = validate_practice_card(
        stem="Діти граються на _____ (подвір'я).",
        target="подвір'ї",
        distractors=["автомобіль", "комп'ютер", "кіт"],
        mock_response=mock_resp,
    )
    assert verdict.verdict == "warn_weak_foils"
    assert any("Weak foils" in f for f in verdict.findings)


def test_validate_anti_calque_yield_mock():
    mock_resp = {
        "model": "jev-test",
        "answers": {
            "distractor_plausibility": DummyAns(score=1.90, confidence=0.95),
            "is_unambiguous": DummyAns(noul=0.92),
            "anti_calque_yield": DummyAns(noul=0.85),  # Strong anti-calque value!
            "card_quality": DummyAns(choice="pass", confidence=0.90),
        },
    }
    verdict = validate_practice_card(
        stem="Конференція триватиме _____ (during) трьох днів.",
        target="протягом",
        distractors=["на протязі", "в протязі", "по протязі"],
        grammar_focus="Prepositional government & anti-calque",
        mock_response=mock_resp,
    )
    assert verdict.verdict == "pass"
    assert any("Anti-calque value" in f for f in verdict.findings)


def test_deterministic_vesum_and_style_guide_checks(tmp_path):
    import sqlite3

    vesum_db = tmp_path / "vesum.db"
    sources_db = tmp_path / "sources.db"

    # Seed mock vesum
    conn = sqlite3.connect(vesum_db)
    conn.execute("CREATE TABLE forms (word_form TEXT, lemma TEXT)")
    conn.execute("INSERT INTO forms VALUES ('друга', 'друг')")
    conn.commit()
    conn.close()

    # Seed mock sources style_guide
    conn = sqlite3.connect(sources_db)
    conn.execute("CREATE TABLE style_guide (headword TEXT, text TEXT)")
    conn.execute("INSERT INTO style_guide VALUES ('протягом', 'на протязі - калька')")
    conn.commit()
    conn.close()

    mock_resp = {
        "model": "jev-test",
        "answers": {
            "distractor_plausibility": DummyAns(score=1.80, confidence=0.95),
            "is_unambiguous": DummyAns(noul=0.95),
            "anti_calque_yield": DummyAns(noul=0.85),
            "card_quality": DummyAns(choice="pass", confidence=0.90),
        },
    }

    verdict = validate_practice_card(
        stem="Це тривало _____ року.",
        target="протягом",
        distractors=["на протязі"],
        mock_response=mock_resp,
        vesum_db=vesum_db,
        sources_db=sources_db,
    )

    assert verdict.style_guide_attested
    assert any("Attested style-guide entry" in f for f in verdict.findings)


@pytest.mark.live_network
def test_live_practice_validator_smoke():
    key = resolve_api_key()
    if not key:
        pytest.skip("TypeSafe API key not available on host.")

    verdict = validate_practice_card(
        stem="Він завжди радий _____ (поговорити) з новими людьми.",
        target="поговорити",
        distractors=["поговорив", "поговори", "говоритиме"],
        grammar_focus="Infinitive vs finite verb forms",
    )
    assert isinstance(verdict, DistractorValidationVerdict)
    assert verdict.verdict in {"pass", "warn_weak_foils"}
    assert verdict.is_unambiguous_prob > 0.60
    assert verdict.latency_seconds > 0.0
