"""Policy pins for Plan Adherence review rules in the active V7 prompt path."""

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


def test_active_reviewer_references_plan_adherence_contract() -> None:
    assert CONTRACT_RELATIVE_PATH in _reviewer_text()


def test_contract_marks_section_word_budgets_as_soft() -> None:
    lowered = _contract_text().lower()
    assert "soft" in lowered
    assert "penalize only silent deferrals" in lowered


def test_contract_requires_activity_marker_after_tested_teaching() -> None:
    lowered = _contract_text().lower()
    assert "after the teaching prose" in lowered
    assert "not before" in lowered
    assert "marker placed before" in lowered
    assert "is a defect" in lowered
