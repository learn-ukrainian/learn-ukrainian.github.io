"""Tests for plateau-aware review loop decisions."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

v6_build = importlib.import_module("build.v6_build")


def _round(round_num: int, score: float, *, passed: bool = False, blocking: bool = True):
    violations = ({"severity": "ERROR"},) if blocking else ()
    return v6_build.ReviewRoundState(
        round_num=round_num,
        passed=passed,
        score=score,
        review_text=f"round {round_num}",
        contract_violations=violations,
    )


def test_plateau_on_two_consecutive_small_deltas() -> None:
    decision = v6_build._review_loop_decision(
        [_round(1, 8.2), _round(2, 8.3), _round(3, 8.4)]
    )

    assert decision.outcome == "plateau"
    assert decision.reason == "two_small_deltas"
    assert decision.last_delta == 0.1


def test_large_gain_resets_small_delta_counter() -> None:
    decision = v6_build._review_loop_decision(
        [_round(1, 8.0), _round(2, 8.1), _round(3, 8.4), _round(4, 8.5)]
    )

    assert decision.outcome == "continue"
    assert decision.consecutive_small_deltas == 1
    assert decision.last_delta == 0.1


def test_six_round_cap_plateaus_even_without_two_small_deltas() -> None:
    decision = v6_build._review_loop_decision(
        [
            _round(1, 7.8),
            _round(2, 8.0),
            _round(3, 8.2),
            _round(4, 8.4),
            _round(5, 8.6),
            _round(6, 8.8),
        ]
    )

    assert decision.outcome == "plateau"
    assert decision.reason == "max_rounds"
    assert decision.last_delta == 0.2


def test_pass_requires_no_contract_blockers() -> None:
    decision = v6_build._review_loop_decision(
        [_round(1, 9.0, passed=True, blocking=False)]
    )

    assert decision.outcome == "pass"
    assert decision.reason == "passed"
