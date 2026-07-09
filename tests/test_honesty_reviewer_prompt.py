"""Policy pins for Honesty review rules in the active V7 prompt path."""

from __future__ import annotations

from pathlib import Path

CONTRACT_PATH = (
    Path(__file__).resolve().parent.parent
    / "scripts"
    / "build"
    / "contracts"
    / "module-contract.md"
)
REVIEWER_PROMPT_PATH = (
    Path(__file__).resolve().parent.parent
    / "scripts"
    / "build"
    / "phases"
    / "linear-review-dim.md"
)
CONTRACT_RELATIVE_PATH = "scripts/build/contracts/module-contract.md"


def _contract_text() -> str:
    return CONTRACT_PATH.read_text(encoding="utf-8")


def _reviewer_text() -> str:
    return REVIEWER_PROMPT_PATH.read_text(encoding="utf-8")


def test_active_reviewer_references_honesty_contract() -> None:
    assert CONTRACT_RELATIVE_PATH in _reviewer_text()


def test_contract_states_verify_presence_positive_signal() -> None:
    lowered = _contract_text().lower()
    assert "verify" in lowered
    assert "positive honesty signal" in lowered
    assert "scores its presence" in lowered


def test_contract_requires_specific_claim_markers() -> None:
    lowered = _contract_text().lower()
    assert "verify: {claim}" in lowered
    assert "specific claims" in lowered
    assert "scattered hedging" in lowered
