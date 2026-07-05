"""Step-3 bakeoff scoring for grounded reviewer fact-check verdicts.

This module is intentionally pure and not wired into live gates. It scores
offline proof rows where the harness knows whether a claim is true or planted.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

CONFIRMED_ON_TRUE = 20
CONFIRMED_ON_FABRICATED = -100
REFUTED_ON_FABRICATED = 30
UNATTESTED_ON_FABRICATED = 10
UNATTESTED_OR_UNVERIFIED_ON_TRUE = -10
REFUTED_ON_TRUE = -50


def score_verdict(verdict: str, *, claim_is_true: bool) -> int:
    """Score one fact-check verdict against known truth."""
    normalized = verdict.strip().upper()
    if claim_is_true:
        if normalized == "CONFIRMED":
            return CONFIRMED_ON_TRUE
        if normalized == "REFUTED_BY_CONTRADICTION":
            return REFUTED_ON_TRUE
        if normalized in {"UNATTESTED_AFTER_SEARCH", "UNVERIFIED_INSUFFICIENT_SEARCH"}:
            return UNATTESTED_OR_UNVERIFIED_ON_TRUE
        return 0

    if normalized == "CONFIRMED":
        return CONFIRMED_ON_FABRICATED
    if normalized == "REFUTED_BY_CONTRADICTION":
        return REFUTED_ON_FABRICATED
    if normalized == "UNATTESTED_AFTER_SEARCH":
        return UNATTESTED_ON_FABRICATED
    return 0


def score_fact_checks(
    fact_checks: list[Mapping[str, Any]],
    truth_by_claim: Mapping[str, bool],
) -> int:
    """Score fact-check rows by exact claim text."""
    total = 0
    for row in fact_checks:
        claim = row.get("claim")
        verdict = row.get("verdict")
        if not isinstance(claim, str) or not isinstance(verdict, str):
            continue
        if claim not in truth_by_claim:
            continue
        total += score_verdict(verdict, claim_is_true=bool(truth_by_claim[claim]))
    return total
