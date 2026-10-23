from __future__ import annotations

from scripts.build import linear_pipeline
from scripts.common.thresholds import QG_DIMS


def test_a1_20_passing_review_aggregates_to_pass() -> None:
    report = {
        dim: {
            "score": 9.0,
            "evidence": '"The module gives a concrete morning sequence."',
            "verdict": "PASS",
        }
        for dim in QG_DIMS
    }

    aggregate = linear_pipeline.aggregate_llm_review(report, "A1")

    assert aggregate["aggregate"]["verdict"] == "PASS"
    assert aggregate["aggregate"]["failing_dims"] == ()
