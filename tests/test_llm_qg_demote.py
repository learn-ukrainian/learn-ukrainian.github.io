"""Tests for LLM QG terminal/warning dim split (PR-A, 2026-05-23)."""

from scripts.build import linear_pipeline
from scripts.common.thresholds import (
    LLM_QG_TERMINAL_DIMS,
    LLM_QG_WARNING_DIMS,
    QG_DIMS,
    aggregate_review,
)


def test_terminal_and_warning_dims_partition_qg_dims() -> None:
    """LLM_QG_TERMINAL_DIMS union LLM_QG_WARNING_DIMS == QG_DIMS, disjoint."""
    assert frozenset(QG_DIMS) == LLM_QG_TERMINAL_DIMS | LLM_QG_WARNING_DIMS
    assert frozenset() == LLM_QG_TERMINAL_DIMS & LLM_QG_WARNING_DIMS


def test_decolonization_is_only_terminal_dim_in_2026_05_23_baseline() -> None:
    """Per architectural reset 2026-05-23 decision #3."""
    assert frozenset({"decolonization"}) == LLM_QG_TERMINAL_DIMS


def test_warning_dim_reject_does_not_drive_terminal_verdict() -> None:
    """A REJECT in a warning dim leaves terminal_verdict == PASS."""
    scores = {
        "pedagogical": 4.0,  # REJECT (below 6.0 reject floor)
        "naturalness": 9.0,
        "decolonization": 9.5,  # PASS
        "engagement": 8.5,
        "tone": 8.5,
    }
    verdict = aggregate_review(scores, "A1")
    assert verdict.verdict == "REJECT"
    assert verdict.terminal_verdict == "PASS"
    assert "pedagogical" in verdict.rejected_dims
    assert "pedagogical" in verdict.warning_dims


def test_decolonization_reject_drives_terminal_verdict() -> None:
    """A REJECT in decolonization terminates the build."""
    scores = {
        "pedagogical": 9.0,
        "naturalness": 9.0,
        "decolonization": 4.0,  # REJECT
        "engagement": 8.5,
        "tone": 8.5,
    }
    verdict = aggregate_review(scores, "A1")
    assert verdict.verdict == "REJECT"
    assert verdict.terminal_verdict == "REJECT"
    assert "decolonization" in verdict.rejected_dims


def test_all_pass_yields_pass_on_both() -> None:
    scores = {
        "pedagogical": 9.0,
        "naturalness": 9.0,
        "decolonization": 9.0,
        "engagement": 8.5,
        "tone": 8.5,
    }
    verdict = aggregate_review(scores, "A1")
    assert verdict.verdict == "PASS"
    assert verdict.terminal_verdict == "PASS"
    assert verdict.warning_dims == ()


def test_warning_revise_does_not_drive_terminal_revise() -> None:
    """A warning-dim REVISE yields verdict=REVISE but terminal_verdict=PASS."""
    scores = {
        "pedagogical": 7.0,  # below A1 pass floor 9.0, above reject floor 6.0
        "naturalness": 9.0,
        "decolonization": 9.0,
        "engagement": 8.5,
        "tone": 8.5,
    }
    verdict = aggregate_review(scores, "A1")
    assert verdict.verdict == "REVISE"
    assert verdict.terminal_verdict == "PASS"


def test_aggregate_llm_review_json_shape_includes_terminal_warning_fields() -> None:
    """linear_pipeline.asdict output includes the additive gate fields."""
    report = {
        dim: {
            "score": 4.0 if dim == "pedagogical" else 9.0,
            "evidence": '"The module gives a concrete morning sequence."',
            "verdict": "REJECT" if dim == "pedagogical" else "PASS",
        }
        for dim in QG_DIMS
    }

    aggregate = linear_pipeline.aggregate_llm_review(report, "A1")["aggregate"]

    assert aggregate["verdict"] == "REJECT"
    assert aggregate["terminal_verdict"] == "PASS"
    assert aggregate["warning_dims"] == ("pedagogical",)
