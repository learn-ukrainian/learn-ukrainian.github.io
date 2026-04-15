"""Regression tests for numeric selection of versioned review artifacts."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import build.v6_build as v6_build
from audit.checks import review_validation


def _style_review_yaml(score: float) -> str:
    return (
        "phase: review-style\n"
        "verdict: PASS\n"
        "pass: true\n"
        f"overall_score: {score:.1f}\n"
        "scores:\n"
        f"  - key: pragmatic_authenticity\n    score: {score:.1f}\n"
        f"  - key: stylistic_consistency\n    score: {score:.1f}\n"
        f"  - key: culture_and_register\n    score: {score:.1f}\n"
        f"  - key: naturalness\n    score: {score:.1f}\n"
    )


def _markdown_review(score: int) -> str:
    rows = "\n".join(
        f"| {i}. Dimension {i} | {score}/10 | Strong evidence |"
        for i in range(1, 10)
    )
    return (
        "## Scores\n"
        "| Dimension | Score | Evidence |\n"
        "|-----------|-------|----------|\n"
        f"{rows}\n\n"
        "## Verdict: PASS\n"
    )


def test_review_validation_prefers_highest_numeric_round(tmp_path: Path):
    orch_dir = tmp_path / "orchestration" / "demo"
    orch_dir.mkdir(parents=True)
    (orch_dir / "review-structured-r9.yaml").write_text("scores:\n  - score: 8\n", "utf-8")
    (orch_dir / "review-structured-r17.yaml").write_text("scores:\n  - score: 10\n", "utf-8")

    latest, data, error = review_validation._load_latest_yaml(orch_dir, "review-structured-r*.yaml")

    assert error is None
    assert latest is not None
    assert latest.name == "review-structured-r17.yaml"
    assert data == {"scores": [{"score": 10}]}


def test_build_prefers_highest_numeric_markdown_review_round(tmp_path: Path, monkeypatch):
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    review_dir = curriculum_root / "b1" / "review"
    review_dir.mkdir(parents=True)
    (review_dir / "demo-review-r9.md").write_text(_markdown_review(8), "utf-8")
    (review_dir / "demo-review-r17.md").write_text(_markdown_review(10), "utf-8")
    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)

    parsed = v6_build._load_latest_review_result("b1", "demo")

    assert parsed is not None
    assert parsed.score == 10.0


def test_build_prefers_highest_numeric_style_review_round(tmp_path: Path, monkeypatch):
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    orch_dir = curriculum_root / "b1" / "orchestration" / "demo"
    orch_dir.mkdir(parents=True)
    (orch_dir / "review-structured-style-r9.yaml").write_text(_style_review_yaml(8.0), "utf-8")
    (orch_dir / "review-structured-style-r10.yaml").write_text(_style_review_yaml(9.5), "utf-8")
    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)

    parsed = v6_build._load_latest_style_review_result("b1", "demo")

    assert parsed is not None
    assert parsed.score == 9.5
