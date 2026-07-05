from __future__ import annotations

from scripts.audit import qg_factcheck_scoring as scoring


def test_locked_factcheck_scoring_constants() -> None:
    assert scoring.score_verdict("CONFIRMED", claim_is_true=True) == 20
    assert scoring.score_verdict("CONFIRMED", claim_is_true=False) == -100
    assert scoring.score_verdict("REFUTED_BY_CONTRADICTION", claim_is_true=False) == 30
    assert scoring.score_verdict("UNATTESTED_AFTER_SEARCH", claim_is_true=False) == 10
    assert scoring.score_verdict("UNATTESTED_AFTER_SEARCH", claim_is_true=True) == -10
    assert scoring.score_verdict("UNVERIFIED_INSUFFICIENT_SEARCH", claim_is_true=True) == -10
    assert scoring.score_verdict("REFUTED_BY_CONTRADICTION", claim_is_true=True) == -50


def test_scores_fact_check_rows_by_claim_truth_map() -> None:
    fact_checks = [
        {"claim": "true claim", "verdict": "CONFIRMED"},
        {"claim": "fabricated claim", "verdict": "UNATTESTED_AFTER_SEARCH"},
        {"claim": "ignored claim", "verdict": "CONFIRMED"},
    ]

    assert scoring.score_fact_checks(
        fact_checks,
        {"true claim": True, "fabricated claim": False},
    ) == 30


def test_admissibility_downgraded_rows_score_the_original_verdict() -> None:
    """Gate downgrade (#4429) must not mask the model's raw judgment (−100 class)."""
    fact_checks = [
        {
            "claim": "fabricated claim",
            "verdict": "UNVERIFIED_INSUFFICIENT_SEARCH",
            "original_verdict": "CONFIRMED",
            "admissibility_downgraded": True,
        },
        {
            # Model-emitted UNVERIFIED without the downgrade flag scores as-is.
            "claim": "true claim",
            "verdict": "UNVERIFIED_INSUFFICIENT_SEARCH",
        },
    ]

    assert scoring.score_fact_checks(
        fact_checks,
        {"fabricated claim": False, "true claim": True},
    ) == -110
