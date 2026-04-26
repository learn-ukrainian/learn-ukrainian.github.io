from __future__ import annotations

from scripts.build import linear_pipeline
from scripts.common.thresholds import QG_DIMS


def test_a1_20_plan_context_matches_phase_4_contract() -> None:
    plan_path = linear_pipeline.plan_path_for("a1", "my-morning")
    plan = linear_pipeline.plan_check(plan_path)
    context = linear_pipeline.writer_context(
        plan,
        plan_path.read_text(encoding="utf-8"),
        "packet",
    )

    assert context["LEVEL"] == "A1"
    assert context["MODULE_NUM"] == "20"
    assert "TARGET: 15-35% Ukrainian." in context["IMMERSION_RULE"]
    assert "classify" in context["FORBIDDEN_ACTIVITY_TYPES"]
    assert "select" in context["FORBIDDEN_ACTIVITY_TYPES"]
    assert "fill-in" in context["ALLOWED_ACTIVITY_TYPES"]


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
