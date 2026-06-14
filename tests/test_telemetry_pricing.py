"""Tests for strict telemetry pricing."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from telemetry.pricing import compute_cost


def test_priced_model_with_real_tokens_returns_cost():
    result = compute_cost("text-embedding-3-small", 1_000)

    assert result.billing_model == "per_token"
    assert result.provenance == "priced"
    assert result.cost_usd == pytest.approx(0.00002)


def test_priced_model_without_tokens_does_not_fabricate_cost():
    result = compute_cost("text-embedding-3-small", None)

    assert result.billing_model == "per_token"
    assert result.provenance == "no_tokens"
    assert result.cost_usd is None


def test_unknown_model_has_no_price():
    result = compute_cost("definitely-not-a-model", 1_000)

    assert result.billing_model == "unknown"
    assert result.provenance == "no_price"
    assert result.cost_usd is None


def test_subscription_lane_has_no_per_call_cost():
    result = compute_cost("claude-opus-4-8", 1_000, agent="claude")

    assert result.billing_model == "subscription"
    assert result.provenance == "subscription"
    assert result.cost_usd is None


def test_no_fabricated_dollars_without_tokens_and_table_price():
    cases = (
        compute_cost("text-embedding-3-small", None),
        compute_cost("unknown", 1_000),
        compute_cost("unknown", None),
        compute_cost("gpt-5.5", 1_000, agent="codex"),
    )

    for result in cases:
        if result.provenance != "priced":
            assert result.cost_usd is None
