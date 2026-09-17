"""Hermetic and live tests for TypeSafe Verb Valency Verifier (Practice Hub #8170)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from scripts.practice.typesafe_valency_verifier import (
    ValencyVerificationVerdict,
    resolve_api_key,
    verify_valency_card,
)


class MockScoreResult:
    def __init__(self, score: float, conf: float = 0.88):
        self.score = score
        self.confidence = conf


class MockNoulResult:
    def __init__(self, noul: float):
        self.noul = noul


class MockSystemOneResponse:
    def __init__(self, answers: dict):
        self.answers = answers
        self.model = "jev-1.13.0"
        self.usage = MagicMock(input_tokens=140, output_tokens=35)


def test_hermetic_valency_admit():
    mock_client = MagicMock()
    mock_client.system_one.return_value = MockSystemOneResponse(
        {
            "strict_government": MockNoulResult(0.96),
            "syntactic_exclusivity": MockNoulResult(0.94),
            "is_calque_foil": MockNoulResult(0.92),
            "sentence_naturalness": MockScoreResult(4.5, 0.90),
        }
    )

    verdict = verify_valency_card(
        verb="дякувати",
        stem="Ми щиро дякуємо ___ за допомогу.",
        target="вам",
        calque_distractor="вас",
        case_demanded="Dative",
        client=mock_client,
    )

    assert verdict.verdict == "admit"
    assert verdict.government_prob == 0.96
    assert verdict.exclusivity_prob == 0.94
    assert verdict.calque_foil_prob == 0.92
    assert not verdict.needs_review


def test_hermetic_valency_fail_incorrect_gov():
    mock_client = MagicMock()
    mock_client.system_one.return_value = MockSystemOneResponse(
        {
            "strict_government": MockNoulResult(0.35),  # Incorrect government
            "syntactic_exclusivity": MockNoulResult(0.40),
            "is_calque_foil": MockNoulResult(0.20),
            "sentence_naturalness": MockScoreResult(3.0, 0.80),
        }
    )

    verdict = verify_valency_card(
        verb="бачити",
        stem="Він бачить ___ на вулиці.",
        target="другу",
        calque_distractor="друга",
        case_demanded="Dative",
        client=mock_client,
    )

    assert verdict.verdict == "fail_incorrect_gov"
    assert any("Strict government not confirmed" in f for f in verdict.findings)


def test_hermetic_valency_warn_weak_foil():
    mock_client = MagicMock()
    mock_client.system_one.return_value = MockSystemOneResponse(
        {
            "strict_government": MockNoulResult(0.95),
            "syntactic_exclusivity": MockNoulResult(0.92),
            "is_calque_foil": MockNoulResult(0.40),  # Weak foil (not a real calque)
            "sentence_naturalness": MockScoreResult(4.0, 0.85),
        }
    )

    verdict = verify_valency_card(
        verb="дякувати",
        stem="Я дякую ___ за все.",
        target="мамі",
        calque_distractor="столу",
        case_demanded="Dative",
        client=mock_client,
    )

    assert verdict.verdict == "warn_weak_foil"
    assert any("not a strong calque foil" in f for f in verdict.findings)


@pytest.mark.live_network
def test_live_valency_verification_dyakuvaty():
    api_key = resolve_api_key()
    if not api_key:
        pytest.skip("TYPESAFE_API_KEY not found in env or ~/.secrets/")

    verdict = verify_valency_card(
        verb="дякувати",
        stem="Я щиро дякую ___ за підтримку.",
        target="вам",
        calque_distractor="вас",
        case_demanded="Dative",
    )

    assert isinstance(verdict, ValencyVerificationVerdict)
    assert verdict.verdict == "admit"
    assert verdict.government_prob >= 0.80
    assert verdict.calque_foil_prob >= 0.60
    assert verdict.naturalness_score >= 2.5
