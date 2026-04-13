"""Regression tests for shared resume invalidation planning in v6_build."""

from __future__ import annotations

import json
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
    (module_dir / f"{slug}.md").write_text("# Content\n", "utf-8")

    import os
    import time

    future = time.time() + 3600
    os.utime(status_path, (future, future))


def test_resume_publish_reruns_review_when_saved_review_is_below_threshold(tmp_path, monkeypatch):
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    slug = "single-module"
    _write_manifest(curriculum_root, [slug])
    _write_state(curriculum_root, slug)
    _write_review(curriculum_root, slug, 8)
    _write_passing_status(curriculum_root, slug)

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    monkeypatch.setattr(v6_build, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(v6_build.ModuleBuildLock, "acquire", lambda self: True)
    monkeypatch.setattr(v6_build.ModuleBuildLock, "release", lambda self: None)
    monkeypatch.setattr(v6_build, "_run_pre_build_gate", lambda *args, **kwargs: True, raising=False)
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
    monkeypatch.setattr(v6_build, "step_audit", track_step_audit)
    monkeypatch.setattr(v6_build, "step_publish", track_step_publish)
    monkeypatch.setattr(v6_build, "_apply_review_fixes", lambda *args, **kwargs: (False, 0))
    monkeypatch.setattr(v6_build, "step_verify", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        sys,
        "argv",
        ["v6_build.py", "b1", "1", "--step", "publish", "--resume"],
    )

    v6_build.main()

    assert len(review_calls) == 1
    assert len(audit_calls) == 1
    assert len(publish_calls) == 1
