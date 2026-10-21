"""Hermetic and live tests for TypeSafe Word Atlas Sense Gate.

Hermetic tests run offline without network access.
Live network tests require TYPESAFE_API_KEY and test against the real Jev endpoint.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from scripts.atlas.typesafe_sense_gate import (
    evaluate_atlas_example,
)


class MockChoiceResult:
    def __init__(self, choice: str, prob: float = 0.95, conf: float = 0.92):
        self.choice = choice
        self.probabilities = {choice: prob}
        self.confidence = conf


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
        self.usage = MagicMock(input_tokens=150, output_tokens=45)


def test_hermetic_admit_valid_example():
    mock_resp = {
        "model": "jev-test",
        "answers": {
            "sense_match": MockChoiceResult("primary_sense", 0.96),
            "is_authentic_ukrainian": MockNoulResult(0.95),
            "calque_risk": MockChoiceResult("none_authentic", 0.98),
            "pedagogical_clarity": MockScoreResult(4.5, 0.90),
            "cefr_level": MockChoiceResult("A2", 0.85, 0.88),
        },
    }

    verdict = evaluate_atlas_example(
        lemma="вірний",
        definition="відданий, незрадливий у дружбі, коханні",
        sentence="Він мій найвірніший друг уже багато років.",
        pos="adj",
        mock_response=mock_resp,
    )

    assert verdict.verdict == "admit"
    assert verdict.sense_match == "primary_sense"
    assert verdict.is_authentic_prob == 0.95
    assert verdict.calque_risk == "none_authentic"
    assert verdict.pedagogical_score == 4.5
    assert verdict.cefr_level == "A2"
    assert not verdict.needs_review


def test_hermetic_reject_polysemous_calque():
    mock_resp = {
        "model": "jev-test",
        "answers": {
            "sense_match": MockChoiceResult("primary_sense", 0.85),
            "is_authentic_ukrainian": MockNoulResult(0.20),
            "calque_risk": MockChoiceResult("direct_russian_calque", 0.94),
            "pedagogical_clarity": MockScoreResult(3.0, 0.80),
            "cefr_level": MockChoiceResult("A2", 0.80, 0.85),
        },
    }

    verdict = evaluate_atlas_example(
        lemma="вірний",
        definition="відданий, незрадливий",
        sentence="У цій задачі тільки одне вірне рішення.",
        pos="adj",
        mock_response=mock_resp,
    )

    assert verdict.verdict == "reject_calque"
    assert verdict.calque_risk == "direct_russian_calque"
    assert any("Calque or unauthentic" in f for f in verdict.findings)


def test_hermetic_reject_wrong_sense():
    mock_resp = {
        "model": "jev-test",
        "answers": {
            "sense_match": MockChoiceResult("unrelated_or_wrong_sense", 0.92),
            "is_authentic_ukrainian": MockNoulResult(0.92),
            "calque_risk": MockChoiceResult("none_authentic", 0.95),
            "pedagogical_clarity": MockScoreResult(4.0, 0.85),
            "cefr_level": MockChoiceResult("B1", 0.80, 0.85),
        },
    }

    verdict = evaluate_atlas_example(
        lemma="лава",
        definition="вулканічна маса, що виливається з вулкана",
        sentence="Дідусь сів на дерев'яну лаву біля хати.",
        pos="noun",
        mock_response=mock_resp,
    )

    assert verdict.verdict == "reject_off_sense"
    assert verdict.sense_match == "unrelated_or_wrong_sense"
    assert any("does not illustrate definition" in f for f in verdict.findings)
