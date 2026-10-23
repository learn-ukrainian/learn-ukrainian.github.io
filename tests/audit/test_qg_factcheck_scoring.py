from __future__ import annotations

from scripts.audit import qg_factcheck_scoring as scoring


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
