"""Tests for TypeSafe System One Cyrillic Gate (ULDR #8173)."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from scripts.projects.open_model_data.typesafe_cyrillic_gate import (
    CyrillicGateVerdict,
    evaluate_cyrillic_text,
    resolve_api_key,
)


class DummyAns:
    """Mock answer container mimicking typesafe_sdk answer types."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def test_resolve_api_key_from_env():
    with patch.dict(os.environ, {"TYPESAFE_API_KEY": "test-key-12345"}):
        assert resolve_api_key() == "test-key-12345"


def test_evaluate_clean_standard_mock():
    mock_resp = {
        "model": "jev-test",
        "answers": {
            "ocr_corruption": DummyAns(score=0.10, confidence=0.95),
            "lexical_variety": DummyAns(choice="standard_modern", confidence=0.92),
            "colonial_shadow": DummyAns(noul=0.12),
            "curriculum_action": DummyAns(choice="admit_standard", confidence=0.88),
        },
    }
    verdict = evaluate_cyrillic_text(
        text="Сонце світить над Дніпром.",
        mock_response=mock_resp,
    )
    assert isinstance(verdict, CyrillicGateVerdict)
    assert verdict.decision == "admit_standard"
    assert verdict.lexical_variety == "standard_modern"
    assert verdict.ocr_corruption_score == 0.10
    assert verdict.colonial_shadow_prob == 0.12
    assert not verdict.needs_review


def test_evaluate_ocr_garbage_mock():
    mock_resp = {
        "model": "jev-test",
        "answers": {
            "ocr_corruption": DummyAns(score=1.85, confidence=0.90),
            "lexical_variety": DummyAns(choice="standard_modern", confidence=0.50),
            "colonial_shadow": DummyAns(noul=0.10),
            "curriculum_action": DummyAns(choice="admit_standard", confidence=0.50),
        },
    }
    verdict = evaluate_cyrillic_text(
        text="ро3вntкy ykpa1нcьk0ї м0ви",
        mock_response=mock_resp,
    )
    assert verdict.decision == "reject"
    assert verdict.ocr_corruption_score >= 1.40


def test_evaluate_surzhyk_override_mock():
    # Model mistakenly proposed admit_standard, but colonial_shadow P(yes) is high
    mock_resp = {
        "model": "jev-test",
        "answers": {
            "ocr_corruption": DummyAns(score=0.05, confidence=0.95),
            "lexical_variety": DummyAns(choice="colonial_surzhyk", confidence=0.85),
            "colonial_shadow": DummyAns(noul=0.82),
            "curriculum_action": DummyAns(choice="admit_standard", confidence=0.70),
        },
    }
    verdict = evaluate_cyrillic_text(
        text="Я вибачаюся, у нас сьогодні важне міроприємство.",
        mock_response=mock_resp,
    )
    # Surzhyk invariant must override to anti-calque drill foil and flag review
    assert verdict.decision == "use_as_anti_calque"
    assert verdict.needs_review
    assert "Colonial Surzhyk flagged" in (verdict.review_reason or "")


def test_evaluate_authentic_dialect_mock():
    mock_resp = {
        "model": "jev-test",
        "answers": {
            "ocr_corruption": DummyAns(score=0.20, confidence=0.85),
            "lexical_variety": DummyAns(choice="authentic_dialect", confidence=0.90),
            "colonial_shadow": DummyAns(noul=0.15),
            "curriculum_action": DummyAns(choice="admit_dialect_heritage", confidence=0.85),
        },
    }
    verdict = evaluate_cyrillic_text(
        text="Ґазда пішов у полонину дивитися на овець.",
        mock_response=mock_resp,
    )
    assert verdict.decision == "admit_heritage"
    assert not verdict.needs_review


def test_evaluate_low_confidence_escalation_mock():
    mock_resp = {
        "model": "jev-test",
        "answers": {
            "ocr_corruption": DummyAns(score=0.30, confidence=0.40),
            "lexical_variety": DummyAns(choice="historical_literary", confidence=0.35),
            "colonial_shadow": DummyAns(noul=0.30),
            "curriculum_action": DummyAns(choice="admit_standard", confidence=0.38),
        },
    }
    verdict = evaluate_cyrillic_text(
        text="Руська правда у списку XIV століття.",
        mock_response=mock_resp,
    )
    assert verdict.needs_review
    assert "low variety confidence" in (verdict.review_reason or "")


@pytest.mark.live_network
def test_live_cyrillic_gate_smoke():
    key = resolve_api_key()
    if not key:
        pytest.skip("TypeSafe API key not available on host.")

    verdict = evaluate_cyrillic_text(
        text="Українська мова має багату та самобутню історію.",
        context="Historical & pedagogical corpus sample",
    )
    assert isinstance(verdict, CyrillicGateVerdict)
    assert verdict.lexical_variety in {"standard_modern", "historical_literary"}
    assert verdict.ocr_corruption_score < 0.50
    assert verdict.colonial_shadow_prob < 0.50
    assert verdict.latency_seconds > 0.0
