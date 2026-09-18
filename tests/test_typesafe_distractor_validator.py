"""Tests for TypeSafe Practice Distractor & Misconception Validator (Practice Hub #8174)."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from scripts.practice.typesafe_distractor_validator import (
    DistractorValidationVerdict,
    ground_with_sources,
    resolve_api_key,
    validate_practice_card,
)


class DummyAns:
    """Mock answer container mimicking typesafe_sdk answer types."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)



def _hermetic_ground(
    target: str,
    distractors: list[str],
    vesum_db_path=None,
    sources_db_path=None,
    *,
    calque_forms: list[str] | None = None,
) -> dict:
    """Deterministic grounding stub for CI (no VESUM/sources.db required)."""
    calques = [{"form": f, "source": "stub"} for f in (calque_forms or [])]
    return {
        "target": {
            "word": target,
            "in_vesum": True,
            "status": "CLEAN",
            "analyses": [],
        },
        "distractors": {
            "verified_in_vesum": list(distractors),
            "missing_from_vesum": [],
            "analyses": {},
        },
        "calques_and_shadows": calques,
        "has_calque_foil": any(c["form"] in distractors for c in calques),
        "grounded": True,
    }


def _hermetic_ground_with_calque(
    target: str,
    distractors: list[str],
    vesum_db_path=None,
    sources_db_path=None,
) -> dict:
    """Hermetic ground that marks classic протязі calque foils as detected."""
    calques = [d for d in distractors if "протяз" in d]
    return _hermetic_ground(
        target,
        distractors,
        vesum_db_path=vesum_db_path,
        sources_db_path=sources_db_path,
        calque_forms=calques,
    )


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
    assert not verdict.grounded


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
        ground_hook=_hermetic_ground,
    )
    assert verdict.verdict == "fail_ambiguous"
    assert verdict.needs_review
    assert any("Ambiguity alert" in f for f in verdict.findings)
    assert verdict.grounded


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
        ground_hook=_hermetic_ground,
    )
    assert verdict.verdict == "warn_weak_foils"
    assert any("Weak foils" in f for f in verdict.findings)
    assert verdict.grounded


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
        ground_hook=_hermetic_ground_with_calque,
    )
    assert verdict.verdict == "pass"
    assert any("High anti-calque value" in f for f in verdict.findings)
    assert any("grounded in Sources" in f for f in verdict.findings)
    assert verdict.grounded


def test_escalate_path_invokes_grounding():
    """Verify that ambiguous card triggers grounding via the escalate path."""
    mock_resp = {
        "model": "jev-test",
        "answers": {
            "distractor_plausibility": DummyAns(score=1.20, confidence=0.80),
            "is_unambiguous": DummyAns(noul=0.45),  # Triggers escalate
            "anti_calque_yield": DummyAns(noul=0.10),
            "card_quality": DummyAns(choice="pass", confidence=0.60),
        },
    }
    with patch(
        "scripts.practice.typesafe_distractor_validator.ground_with_sources",
        side_effect=_hermetic_ground,
    ) as mock_ground:
        verdict = validate_practice_card(
            stem="Він пішов до лісу з _____ (брат).",
            target="братом",
            distractors=["брати", "братів", "братові"],
            mock_response=mock_resp,
        )
        mock_ground.assert_called_once()
        assert verdict.grounded is True
        assert verdict.grounding is not None
        assert verdict.grounding["target"]["in_vesum"] is True


def test_clean_card_fast_path_skips_grounding():
    """Verify clean passing card does not invoke grounding on fast path."""
    mock_resp = {
        "model": "jev-test",
        "answers": {
            "distractor_plausibility": DummyAns(score=1.80, confidence=0.95),
            "is_unambiguous": DummyAns(noul=0.95),
            "anti_calque_yield": DummyAns(noul=0.20),
            "card_quality": DummyAns(choice="pass", confidence=0.90),
        },
    }
    with patch(
        "scripts.practice.typesafe_distractor_validator.ground_with_sources"
    ) as mock_ground:
        verdict = validate_practice_card(
            stem="Вчора ми побачили старого _____ (друг).",
            target="друга",
            distractors=["другові", "другом", "друг"],
            mock_response=mock_resp,
        )
        mock_ground.assert_not_called()
        assert verdict.grounded is False
        assert verdict.grounding is None


def test_always_ground_forces_grounding_on_clean_card():
    """Verify always_ground=True forces grounding even on clean pass."""
    mock_resp = {
        "model": "jev-test",
        "answers": {
            "distractor_plausibility": DummyAns(score=1.80, confidence=0.95),
            "is_unambiguous": DummyAns(noul=0.95),
            "anti_calque_yield": DummyAns(noul=0.20),
            "card_quality": DummyAns(choice="pass", confidence=0.90),
        },
    }
    with patch(
        "scripts.practice.typesafe_distractor_validator.ground_with_sources",
        side_effect=_hermetic_ground,
    ) as mock_ground:
        verdict = validate_practice_card(
            stem="Вчора ми побачили старого _____ (друг).",
            target="друга",
            distractors=["другові", "другом", "друг"],
            mock_response=mock_resp,
            always_ground=True,
        )
        mock_ground.assert_called_once()
        assert verdict.grounded is True


def test_anti_calque_unverified_by_sources_flags_review():
    """When Jev claims anti-calque but foils have no Russian calque/shadow, flag needs_review."""
    mock_resp = {
        "model": "jev-test",
        "answers": {
            "distractor_plausibility": DummyAns(score=1.80, confidence=0.90),
            "is_unambiguous": DummyAns(noul=0.90),
            "anti_calque_yield": DummyAns(noul=0.85),  # High calque claimed
            "card_quality": DummyAns(choice="pass", confidence=0.90),
        },
    }
    verdict = validate_practice_card(
        stem="Він пішов до лісу з _____ (брат).",
        target="братом",
        distractors=["брати", "братів", "братові"],  # All clean UK grammar forms
        mock_response=mock_resp,
        ground_hook=_hermetic_ground,
    )
    assert verdict.grounded is True
    assert verdict.needs_review is True
    assert any("Anti-calque yield unverified by Sources/VESUM" in f for f in verdict.findings)


def test_target_missing_from_vesum_triggers_fail_broken(requires_vesum_db):
    """When target is an invented non-word, grounding detects it and forces fail_broken."""
    mock_resp = {
        "model": "jev-test",
        "answers": {
            "distractor_plausibility": DummyAns(score=1.80, confidence=0.90),
            "is_unambiguous": DummyAns(noul=0.95),
            "anti_calque_yield": DummyAns(noul=0.10),
            "card_quality": DummyAns(choice="pass", confidence=0.90),
        },
    }
    verdict = validate_practice_card(
        stem="Ми побачили _____.",
        target="вигаданеслово12345",
        distractors=["другові", "другом"],
        mock_response=mock_resp,
        always_ground=True,
    )
    assert verdict.verdict == "fail_broken"
    assert verdict.needs_review is True
    assert any("not found in VESUM" in f for f in verdict.findings)


def test_ground_with_sources_direct(requires_vesum_db):
    """Directly test ground_with_sources function (needs real VESUM)."""
    res = ground_with_sources(
        target="протягом",
        distractors=["на протязі", "другові"],
    )
    assert res["target"]["in_vesum"] is True
    assert "другові" in res["distractors"]["verified_in_vesum"]
    assert res["has_calque_foil"] is True
    calque_forms = [c["form"] for c in res["calques_and_shadows"]]
    assert "на протязі" in calque_forms


def test_ground_with_sources_vesum_exception_fails_closed():
    """Verify ground_with_sources fails closed when VESUM raises an exception."""
    with patch(
        "scripts.practice.typesafe_distractor_validator.verify_word",
        side_effect=RuntimeError("VESUM connection error"),
    ), patch(
        "scripts.practice.typesafe_distractor_validator.verify_words",
        side_effect=RuntimeError("VESUM bulk connection error"),
    ):
        res = ground_with_sources(
            target="братом",
            distractors=["брати", "братів"],
        )
        assert res["target"]["in_vesum"] is False
        assert "ERROR: VESUM connection error" in res["target"]["status"]
        assert res["distractors"]["verified_in_vesum"] == []
        assert set(res["distractors"]["missing_from_vesum"]) == {"брати", "братів"}

    # Multi-word target exception path
    with patch(
        "scripts.practice.typesafe_distractor_validator.verify_words",
        side_effect=RuntimeError("VESUM multi-word error"),
    ):
        res_multi = ground_with_sources(
            target="минулого року",
            distractors=["цього року"],
        )
        assert res_multi["target"]["in_vesum"] is False
        assert "ERROR: VESUM multi-word error" in res_multi["target"]["status"]
        assert res_multi["distractors"]["verified_in_vesum"] == []


def test_validate_practice_card_vesum_exception_forces_fail_broken():
    """When verify_word raises an exception during grounding, validator fails closed to fail_broken."""
    mock_resp = {
        "model": "jev-test",
        "answers": {
            "distractor_plausibility": DummyAns(score=1.80, confidence=0.95),
            "is_unambiguous": DummyAns(noul=0.95),
            "anti_calque_yield": DummyAns(noul=0.10),
            "card_quality": DummyAns(choice="pass", confidence=0.90),
        },
    }
    with patch(
        "scripts.practice.typesafe_distractor_validator.verify_word",
        side_effect=RuntimeError("VESUM database locked"),
    ):
        verdict = validate_practice_card(
            stem="Він пішов до лісу з _____ (брат).",
            target="братом",
            distractors=["брати", "братів"],
            mock_response=mock_resp,
            always_ground=True,
        )
        assert verdict.verdict == "fail_broken"
        assert verdict.needs_review is True
        assert verdict.grounded is True
        assert verdict.grounding is not None
        assert verdict.grounding["target"]["in_vesum"] is False
        assert "ERROR: VESUM database locked" in verdict.grounding["target"]["status"]
        assert any("not found in VESUM morphological dictionary (grounding failure)" in f for f in verdict.findings)


def test_escalate_path_vesum_exception_forces_fail_broken():
    """Ambiguous card triggers escalate path, and VESUM exception fails closed to fail_broken."""
    mock_resp = {
        "model": "jev-test",
        "answers": {
            "distractor_plausibility": DummyAns(score=1.20, confidence=0.80),
            "is_unambiguous": DummyAns(noul=0.45),  # Triggers escalate
            "anti_calque_yield": DummyAns(noul=0.10),
            "card_quality": DummyAns(choice="pass", confidence=0.60),
        },
    }
    with patch(
        "scripts.practice.typesafe_distractor_validator.verify_word",
        side_effect=RuntimeError("VESUM IO error"),
    ):
        verdict = validate_practice_card(
            stem="Він пішов до лісу з _____ (брат).",
            target="братом",
            distractors=["брати", "братів", "братові"],
            mock_response=mock_resp,
        )
        assert verdict.verdict == "fail_broken"
        assert verdict.needs_review is True
        assert verdict.grounded is True
        assert verdict.grounding["target"]["in_vesum"] is False
        assert any("not found in VESUM morphological dictionary (grounding failure)" in f for f in verdict.findings)


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
