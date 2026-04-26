"""Regression tests for plan-hash drift invalidation in v6_build."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

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


def _write_plan(curriculum_root: Path, slug: str, *, title: str = "Plan Hash Test") -> None:
    plan_path = curriculum_root / "plans" / "b1" / f"{slug}.yaml"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        yaml.safe_dump(
            {
                "module": slug,
                "slug": slug,
                "level": "B1",
                "sequence": 1,
                "version": "1.0",
                "title": title,
                "focus": "grammar",
                "pedagogy": "PPP",
                "phase": "B1.1",
                "objectives": ["Test plan hashing"],
                "word_target": 1200,
                "content_outline": [
                    {"section": "Intro", "words": 600, "points": ["Dialogue about the plan."]},
                    {"section": "Підсумок", "words": 600},
                ],
                "dialogue_situations": [
                    {
                        "setting": "classroom",
                        "speakers": ["Викладач", "Студент"],
                        "motivation": "plan discussion",
                    }
                ],
                "vocabulary_hints": {"required": ["план"]},
                "activity_hints": [{"id": "plan-check", "type": "quiz", "focus": "intro"}],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        "utf-8",
    )


def _write_state(curriculum_root: Path, slug: str, *, tracked_hash: str) -> None:
    phases = {
        phase: {"status": "complete", "ts": "2026-04-10T00:00:00+00:00"}
        for phase in v6_build._ALL_PHASES
    }
    for phase in ("skeleton", "write", "honesty-annotate", "exercises", "annotate", "verify"):
        phases[phase]["plan_hash"] = tracked_hash

    orch_dir = curriculum_root / "b1" / "orchestration" / slug
    orch_dir.mkdir(parents=True, exist_ok=True)
    (orch_dir / "state.json").write_text(
        json.dumps({"mode": "v6", "track": "b1", "slug": slug, "phases": phases}, indent=2),
        "utf-8",
    )
    (orch_dir / "skeleton.md").write_text("## Intro\n- P1: Teach it.\n", "utf-8")
    (orch_dir / "pre-verify-results.md").write_text("Verified facts.\n", "utf-8")


def _write_review_and_status(curriculum_root: Path, slug: str) -> None:
    review_dir = curriculum_root / "b1" / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    rows = "\n".join(
        f"| {i}. Dimension {i} | 10/10 | Strong evidence |"
        for i in range(1, 10)
    )
    (review_dir / f"{slug}-review.md").write_text(
        "## Scores\n"
        "| Dimension | Score | Evidence |\n"
        "|-----------|-------|----------|\n"
        f"{rows}\n\n## Verdict: PASS\n",
        "utf-8",
    )
    orch_dir = curriculum_root / "b1" / "orchestration" / slug
    orch_dir.mkdir(parents=True, exist_ok=True)
    (orch_dir / "review-structured-r1.yaml").write_text(
        "scores:\n" + "".join("  - score: 10\n" for _ in range(9)),
        "utf-8",
    )
    (orch_dir / "review-structured-style-r1.yaml").write_text(
        "phase: review-style\n"
        "verdict: PASS\n"
        "pass: true\n"
        "overall_score: 9.5\n"
        "scores:\n"
        "  - key: pragmatic_authenticity\n    score: 9.5\n"
        "  - key: stylistic_consistency\n    score: 9.5\n"
        "  - key: culture_and_register\n    score: 9.5\n"
        "  - key: naturalness\n    score: 9.5\n",
        "utf-8",
    )

    status_dir = curriculum_root / "b1" / "status"
    status_dir.mkdir(parents=True, exist_ok=True)
    status_path = status_dir / f"{slug}.json"
    status_path.write_text(
        json.dumps(
            {
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
            }
        ),
        "utf-8",
    )


def test_resume_plan_detects_plan_hash_drift_and_invalidates_from_earliest_writer_phase(
    tmp_path: Path,
    monkeypatch,
) -> None:
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    slug = "hash-drift"
    _write_manifest(curriculum_root, [slug])
    _write_plan(curriculum_root, slug)
    _write_review_and_status(curriculum_root, slug)
    _write_state(curriculum_root, slug, tracked_hash="outdated-hash")

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)

    plan = v6_build._build_resume_invalidation_plan("b1", slug, "publish", 9.0)

    assert plan.should_skip is False
    assert plan.reason.startswith("plan hash drift: skeleton")
    assert plan.invalidate_phases == (
        "skeleton",
        "pre-verify",
        "write",
        "honesty-annotate",
        "exercises",
        "activities",
        "repair",
        "activity-pre-validate",
        "verify-exercises",
        "annotate",
        "vocab",
        "enrich",
        "verify",
        "review",
        "review-style",
        "stress",
        "publish",
        "audit",
    )


def test_resume_publish_expands_to_full_pipeline_when_writer_phase_is_stale(
    tmp_path: Path,
    monkeypatch,
) -> None:
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    slug = "hash-drift"
    _write_manifest(curriculum_root, [slug])
    _write_plan(curriculum_root, slug)
    _write_review_and_status(curriculum_root, slug)

    current_hash = v6_build.current_plan_hash_for(curriculum_root, "b1", slug)
    assert current_hash is not None
    _write_state(curriculum_root, slug, tracked_hash=current_hash)

    state_path = curriculum_root / "b1" / "orchestration" / slug / "state.json"
    state = json.loads(state_path.read_text("utf-8"))
    state["phases"]["write"]["plan_hash"] = "older-hash"
    state["phases"]["honesty-annotate"]["plan_hash"] = "older-hash"
    state["phases"]["exercises"]["plan_hash"] = "older-hash"
    state["phases"]["annotate"]["plan_hash"] = "older-hash"
    state["phases"]["verify"]["plan_hash"] = "older-hash"
    state_path.write_text(json.dumps(state, indent=2), "utf-8")

    packet_path = curriculum_root / "b1" / "research" / f"{slug}-knowledge-packet.md"
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    packet_path.write_text("Knowledge packet.\n", "utf-8")

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    monkeypatch.setattr(v6_build, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(v6_build.ModuleBuildLock, "acquire", lambda self: True)
    monkeypatch.setattr(v6_build.ModuleBuildLock, "release", lambda self: None)
    monkeypatch.setattr(v6_build, "_run_pre_build_gate", lambda *args, **kwargs: True)
    monkeypatch.setattr(orch_index, "generate_index", lambda *args, **kwargs: None)

    calls: list[str] = []

    def fake_write(*args, **kwargs):
        calls.append("write")
        content_path = curriculum_root / "b1" / f"{slug}.md"
        content_path.parent.mkdir(parents=True, exist_ok=True)
        content_path.write_text("# Content\n", "utf-8")
        return content_path

    def fake_activities(*args, **kwargs):
        calls.append("activities")
        path = curriculum_root / "b1" / "activities" / f"{slug}.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("version: '1.0'\nmodule: hash-drift\nlevel: b1\ninline: []\nworkbook: []\n", "utf-8")
        return path

    def fake_vocab(*args, **kwargs):
        calls.append("vocab")
        path = curriculum_root / "b1" / "vocabulary" / f"{slug}.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("[]\n", "utf-8")
        return path

    monkeypatch.setattr(v6_build, "step_write_with_retry", fake_write)
    monkeypatch.setattr(v6_build, "step_activities", fake_activities)
    monkeypatch.setattr(v6_build, "step_repair", lambda *args, **kwargs: (True, False))
    monkeypatch.setattr(v6_build, "step_verify_exercises", lambda *args, **kwargs: True)
    monkeypatch.setattr(v6_build, "_post_process_content", lambda *args, **kwargs: 0)
    monkeypatch.setattr(v6_build, "step_vocab", fake_vocab)
    monkeypatch.setattr(v6_build, "step_verify", lambda *args, **kwargs: True)
    monkeypatch.setattr(v6_build, "step_review", lambda *args, **kwargs: (True, 9.5, "## Verdict: PASS\n"))
    monkeypatch.setattr(v6_build, "step_review_style", lambda *args, **kwargs: (True, 9.4, "phase: review-style\n"))
    monkeypatch.setattr(v6_build, "step_annotate", lambda *args, **kwargs: True)
    monkeypatch.setattr(v6_build, "step_audit", lambda *args, **kwargs: True)
    monkeypatch.setattr(v6_build, "step_publish", lambda *args, **kwargs: True)
    monkeypatch.setattr(v6_build, "_inject_abetka_activities", lambda *args, **kwargs: None)
    monkeypatch.setattr("audit.checks.contract_compliance.check_contract_compliance", lambda *args, **kwargs: [])
    monkeypatch.setattr("audit.checks.contract_compliance.has_blocking_violations", lambda *args, **kwargs: False)
    monkeypatch.setattr(
        sys,
        "argv",
        ["v6_build.py", "b1", "1", "--step", "publish", "--resume", "--writer", "codex"],
    )

    assert v6_build.main() is True
    assert "write" in calls
    assert "activities" in calls
    assert "vocab" in calls
