"""Tests for LLM QG terminal/warning dim split (PR-A, 2026-05-23)."""

from scripts.build import linear_pipeline
from scripts.common.thresholds import (
    QG_DIMS,
    aggregate_review,
)


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


def test_core_decolonization_revise_is_warning_not_terminal() -> None:
    """On core tracks, decolonization revises the full verdict only."""
    scores = {
        "pedagogical": 9.0,
        "naturalness": 9.0,
        "decolonization": 7.0,  # REVISE
        "engagement": 8.5,
        "tone": 8.5,
    }
    verdict = aggregate_review(scores, "A1", profile="core")
    assert verdict.verdict == "REVISE"
    assert verdict.terminal_verdict == "PASS"
    assert "decolonization" in verdict.failing_dims
    assert "decolonization" in verdict.warning_dims


def test_seminar_decolonization_revise_stays_terminal() -> None:
    """On seminar tracks, decolonization still drives terminal_verdict."""
    scores = {
        "pedagogical": 9.0,
        "naturalness": 9.0,
        "decolonization": 7.0,  # REVISE
        "engagement": 9.0,
        "tone": 9.0,
    }
    verdict = aggregate_review(scores, "bio", profile="seminar")
    assert verdict.verdict == "REVISE"
    assert verdict.terminal_verdict == "REVISE"
    assert "decolonization" in verdict.failing_dims
    assert "decolonization" not in verdict.warning_dims


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


def test_aggregate_llm_review_threads_core_profile_for_decolonization() -> None:
    report = {
        dim: {
            "score": 7.0 if dim == "decolonization" else 9.0,
            "evidence": '"The module uses standard Ukrainian forms."',
            "verdict": "REVISE" if dim == "decolonization" else "PASS",
        }
        for dim in QG_DIMS
    }

    aggregate = linear_pipeline.aggregate_llm_review(
        report,
        "A1",
        profile="core",
    )["aggregate"]

    assert aggregate["verdict"] == "REVISE"
    assert aggregate["terminal_verdict"] == "PASS"
    assert aggregate["warning_dims"] == ("decolonization",)


def test_curriculum_profile_for_level_reads_manifest_types(tmp_path) -> None:
    manifest = tmp_path / "curriculum.yaml"
    manifest.write_text(
        """
levels:
  a1:
    type: core
  bio:
    type: track
""".lstrip(),
        encoding="utf-8",
    )

    assert (
        linear_pipeline.curriculum_profile_for_level(
            "A1",
            curriculum_manifest=manifest,
        )
        == "core"
    )
    assert (
        linear_pipeline.curriculum_profile_for_level(
            "BIO",
            curriculum_manifest=manifest,
        )
        == "seminar"
    )
