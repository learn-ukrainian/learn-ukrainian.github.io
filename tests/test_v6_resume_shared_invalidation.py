"""Regression tests for shared resume invalidation planning in v6_build."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import build.orch_index as orch_index
import build.v6_build as v6_build


def _write_manifest(curriculum_root: Path, slugs: list[str]) -> None:
    curriculum_root.mkdir(parents=True, exist_ok=True)
    (curriculum_root / "curriculum.yaml").write_text(
        "levels:\n"
        "  b1:\n"
        "    modules:\n"
        + "".join(f"      - {slug}\n" for slug in slugs),
        "utf-8",
    )


def _write_state(curriculum_root: Path, slug: str) -> None:
    phases = {
        phase: {"status": "complete", "ts": "2026-04-10T00:00:00+00:00"}
        for phase in v6_build._ALL_PHASES
    }
    orch_dir = curriculum_root / "b1" / "orchestration" / slug
    orch_dir.mkdir(parents=True, exist_ok=True)
    (orch_dir / "state.json").write_text(
        json.dumps({"mode": "v6", "track": "b1", "slug": slug, "phases": phases}, indent=2),
        "utf-8",
    )


def _mark_phase_incomplete(curriculum_root: Path, slug: str, phase: str) -> None:
    state_path = curriculum_root / "b1" / "orchestration" / slug / "state.json"
    state = json.loads(state_path.read_text("utf-8"))
    state["phases"].pop(phase, None)
    state_path.write_text(json.dumps(state, indent=2), "utf-8")


def _write_review(curriculum_root: Path, slug: str, score: float) -> None:
    review_dir = curriculum_root / "b1" / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    rows = "\n".join(
        f"| {i}. Dimension {i} | {score}/10 | Strong evidence |"
        for i in range(1, 10)
    )
    (review_dir / f"{slug}-review.md").write_text(
        "## Scores\n"
        "| Dimension | Score | Evidence |\n"
        "|-----------|-------|----------|\n"
        f"{rows}\n\n"
        "## Verdict: PASS\n",
        "utf-8",
    )
    orch_dir = curriculum_root / "b1" / "orchestration" / slug
    orch_dir.mkdir(parents=True, exist_ok=True)
    (orch_dir / "review-structured-r1.yaml").write_text(
        f"scores:\n  - score: {score}\n",
        "utf-8",
    )
    (orch_dir / "review-structured-style-r1.yaml").write_text(
        "phase: review-style\n"
        "verdict: PASS\n"
        "pass: true\n"
        f"overall_score: {score:.1f}\n"
        "scores:\n"
        f"  - key: pragmatic_authenticity\n    score: {score:.1f}\n"
        f"  - key: stylistic_consistency\n    score: {score:.1f}\n"
        f"  - key: culture_and_register\n    score: {score:.1f}\n"
        f"  - key: naturalness\n    score: {score:.1f}\n",
        "utf-8",
    )


def _write_review_text(curriculum_root: Path, slug: str, review_text: str) -> None:
    review_dir = curriculum_root / "b1" / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / f"{slug}-review.md").write_text(review_text, "utf-8")
    orch_dir = curriculum_root / "b1" / "orchestration" / slug
    orch_dir.mkdir(parents=True, exist_ok=True)
    score_matches = [int(score) for score in re.findall(r"\|\s*\d+\.\s*[^|]+\|\s*(\d+)/10\s*\|", review_text)]
    if score_matches:
        score_yaml = "scores:\n" + "".join(f"  - score: {score}\n" for score in score_matches)
        (orch_dir / "review-structured-r1.yaml").write_text(score_yaml, "utf-8")
    (orch_dir / "review-structured-style-r1.yaml").write_text(
        "phase: review-style\n"
        "verdict: PASS\n"
        "pass: true\n"
        "overall_score: 9.2\n"
        "scores:\n"
        "  - key: pragmatic_authenticity\n    score: 9.2\n"
        "  - key: stylistic_consistency\n    score: 9.2\n"
        "  - key: culture_and_register\n    score: 9.2\n"
        "  - key: naturalness\n    score: 9.2\n",
        "utf-8",
    )


def _write_plan(curriculum_root: Path, slug: str) -> None:
    plan_path = curriculum_root / "plans" / "b1" / f"{slug}.yaml"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        "module: 1\n"
        f"slug: {slug}\n"
        "level: b1\n"
        "sequence: 1\n"
        "title: Single Module\n"
        "word_target: 2200\n"
        "phase: B1.1\n"
        "content_outline:\n"
        "  - section: Intro\n"
        "    words: 7\n"
        "    points:\n"
        "      - місто\n"
        "      - classroom\n"
        "  - section: Summary\n"
        "    words: 6\n"
        "    points:\n"
        "      - Учень\n"
        "      - summary\n"
        "dialogue_situations:\n"
        "  - setting: classroom\n"
        "    speakers:\n"
        "      - Вчитель\n"
        "      - Учень\n"
        "    motivation: basic greeting\n"
        "vocabulary_hints:\n"
        "  required:\n"
        "    - місто\n"
        "activity_hints:\n"
        "  - id: quiz-intro\n"
        "    type: quiz\n"
        "    focus: intro\n",
        "utf-8",
    )


def _compliant_content() -> str:
    return (
        "## Intro\n"
        "місто classroom Вчитель Учень greeting.\n"
        "<!-- INJECT_ACTIVITY: quiz-intro -->\n\n"
        "## Summary\n"
        "місто classroom Учень summary.\n"
    )


def _write_passing_status(curriculum_root: Path, slug: str) -> None:
    status_dir = curriculum_root / "b1" / "status"
    status_dir.mkdir(parents=True, exist_ok=True)
    status_path = status_dir / f"{slug}.json"
    status_path.write_text(
        json.dumps({
            "overall": {"status": "pass"},
            "gates": {
                "meta": {"status": "pass"},
                "lesson": {"status": "pass"},
                "activities": {"status": "pass"},
                "vocabulary": {"status": "pass"},
                "naturalness": {"status": "pass"},
                "research": {"status": "pass"},
                "review": {"status": "pass"},
            },
        }),
        "utf-8",
    )
    module_dir = curriculum_root / "b1"
    module_dir.mkdir(parents=True, exist_ok=True)
    (module_dir / f"{slug}.md").write_text(_compliant_content(), "utf-8")

    import os
    import time

    future = time.time() + 3600
    os.utime(status_path, (future, future))


def test_resume_publish_reruns_review_when_saved_review_is_below_threshold(tmp_path, monkeypatch):
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    slug = "single-module"
    _write_manifest(curriculum_root, [slug])
    _write_state(curriculum_root, slug)
    _write_plan(curriculum_root, slug)
    _write_review(curriculum_root, slug, 8)
    _write_passing_status(curriculum_root, slug)

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    monkeypatch.setattr(v6_build, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(v6_build.ModuleBuildLock, "acquire", lambda self: True)
    monkeypatch.setattr(v6_build.ModuleBuildLock, "release", lambda self: None)
    monkeypatch.setattr(v6_build, "_run_pre_build_gate", lambda *args, **kwargs: True, raising=False)
    monkeypatch.setattr(v6_build, "detect_plan_hash_drift", lambda *args, **kwargs: None)
    # Also suppress the secondary write-phase plan-hash detector so the
    # fixture's state.json (no ``write.plan_hash`` pinned) doesn't
    # trigger a full-pipeline invalidation — this test targets the
    # resume-publish re-review path, not plan-hash drift.
    monkeypatch.setattr(
        v6_build, "_write_phase_plan_hash_drifted",
        lambda *args, **kwargs: False,
    )
    monkeypatch.setattr(orch_index, "generate_index", lambda *args, **kwargs: None)

    review_calls: list[tuple] = []
    audit_calls: list[tuple] = []
    publish_calls: list[tuple] = []

    def track_step_review(*args, **kwargs):
        review_calls.append((args, kwargs))
        return True, 9.5, "## Verdict: PASS\n"

    def track_step_audit(*args, **kwargs):
        audit_calls.append((args, kwargs))
        return True

    def track_step_publish(*args, **kwargs):
        publish_calls.append((args, kwargs))
        return True

    monkeypatch.setattr(v6_build, "step_review", track_step_review)
    monkeypatch.setattr(v6_build, "step_review_style", lambda *args, **kwargs: (True, 9.2, "phase: review-style\n"))
    monkeypatch.setattr(v6_build, "step_audit", track_step_audit)
    monkeypatch.setattr(v6_build, "step_publish", track_step_publish)
    monkeypatch.setattr(v6_build, "_apply_review_fixes", lambda *args, **kwargs: (False, 0))
    monkeypatch.setattr(v6_build, "step_verify", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        sys,
        "argv",
        ["v6_build.py", "b1", "1", "--step", "publish", "--resume", "--writer", "gemini"],
    )

    v6_build.main()

    assert len(review_calls) == 1
    assert len(audit_calls) == 1
    assert len(publish_calls) == 1


def test_resume_plan_reruns_when_latest_review_verdict_is_revise(tmp_path, monkeypatch):
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    slug = "single-module"
    _write_manifest(curriculum_root, [slug])
    _write_state(curriculum_root, slug)
    _write_review_text(
        curriculum_root,
        slug,
        (
            "## Scores\n"
            "| Dimension | Score | Evidence |\n"
            "|-----------|-------|----------|\n"
            + "\n".join(
                f"| {i}. Dimension {i} | 10/10 | Strong evidence |"
                for i in range(1, 10)
            )
            + "\n\n## Verdict: REVISE\n"
        ),
    )
    _write_passing_status(curriculum_root, slug)

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)

    plan = v6_build._build_resume_invalidation_plan("b1", slug, "publish", 9.0)

    assert plan.should_skip is False
    assert plan.reason == "latest review verdict REVISE"
    assert plan.invalidate_phases == ("review", "review-style", "stress", "publish", "audit")


def test_resume_plan_reruns_when_latest_review_hits_dimension_floor(tmp_path, monkeypatch):
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    slug = "single-module"
    _write_manifest(curriculum_root, [slug])
    _write_state(curriculum_root, slug)
    _write_review_text(
        curriculum_root,
        slug,
        (
            "## Scores\n"
            "| Dimension | Score | Evidence |\n"
            "|-----------|-------|----------|\n"
            "| 1. Dimension 1 | 7/10 | Factual error in the core explanation |\n"
            + "\n".join(
                f"| {i}. Dimension {i} | 10/10 | Strong evidence |"
                for i in range(2, 10)
            )
            + "\n\n## Verdict: PASS\n"
        ),
    )
    _write_passing_status(curriculum_root, slug)

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)

    plan = v6_build._build_resume_invalidation_plan("b1", slug, "publish", 8.0)

    assert plan.should_skip is False
    # Per-dim refactor (#1421) aggregates dim scores with MIN, so the failing
    # dimension IS the overall score. The ``score < threshold`` branch of
    # ``_resume_review_failure_reason`` now fires before the dimension-floor
    # branch: dim1=7 ⇒ MIN=7 ⇒ "latest review 7.0/10 < 8.0". The older
    # "dimension floor fail" reason is now effectively unreachable under
    # MIN aggregation (when a dim fails the floor, MIN reflects it).
    assert plan.reason == "latest review 7.0/10 < 8.0"
    assert plan.invalidate_phases == ("review", "review-style", "stress", "publish", "audit")


def test_incomplete_module_still_reruns_weak_saved_review(tmp_path, monkeypatch):
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    slug = "single-module"
    _write_manifest(curriculum_root, [slug])
    _write_state(curriculum_root, slug)
    _mark_phase_incomplete(curriculum_root, slug, "review-style")
    _write_review(curriculum_root, slug, 8)
    _write_passing_status(curriculum_root, slug)

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)

    plan = v6_build._build_resume_invalidation_plan("b1", slug, "all", 9.0)

    assert plan.should_skip is False
    assert plan.reason == "latest review 8.0/10 < 9.0"
    assert plan.invalidate_phases == ("review", "stress", "publish", "audit")
