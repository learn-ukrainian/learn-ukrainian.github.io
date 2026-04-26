"""Tests for plan hashing and stale-plan resume behavior."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import build.orch_index as orch_index
import build.v6_build as v6_build
from build.io_utils import plan_hash


def _write_manifest(curriculum_root: Path, *, level: str, slug: str) -> None:
    curriculum_root.mkdir(parents=True, exist_ok=True)
    (curriculum_root / "curriculum.yaml").write_text(
        "levels:\n"
        f"  {level}:\n"
        "    modules:\n"
        f"      - {slug}\n",
        "utf-8",
    )


def _write_plan(curriculum_root: Path, *, level: str, slug: str, title: str) -> Path:
    plan_path = curriculum_root / "plans" / level / f"{slug}.yaml"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        yaml.safe_dump(
            {
                "module": slug,
                "slug": slug,
                "level": level.upper(),
                "sequence": 1,
                "version": "1.0",
                "title": title,
                "focus": "grammar",
                "pedagogy": "PPP",
                "phase": f"{level.upper()}.1",
                "objectives": ["Plan hash test"],
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
    return plan_path


def _write_state(
    curriculum_root: Path,
    *,
    level: str,
    slug: str,
    tracked_hash: str,
    stale_plan_phases: bool = False,
) -> Path:
    phases = {
        phase: {"status": "complete", "ts": "2026-04-10T00:00:00+00:00"}
        for phase in v6_build._ALL_PHASES
    }
    for phase in ("skeleton", "write", "exercises", "annotate", "verify"):
        phases[phase]["plan_hash"] = tracked_hash
        if stale_plan_phases:
            phases[phase]["status"] = "stale"
            phases[phase]["stale_reason"] = "plan hash drift: skeleton -> skeleton, write, exercises, annotate, verify"

    orch_dir = curriculum_root / level / "orchestration" / slug
    orch_dir.mkdir(parents=True, exist_ok=True)
    state_path = orch_dir / "state.json"
    state_path.write_text(
        json.dumps({"mode": "v6", "track": level, "slug": slug, "phases": phases}, indent=2),
        "utf-8",
    )
    (orch_dir / "pre-verify-results.md").write_text("Verified facts.\n", "utf-8")
    return state_path


def _write_resume_inputs(curriculum_root: Path, *, level: str, slug: str) -> None:
    research_path = curriculum_root / level / "research" / f"{slug}-knowledge-packet.md"
    research_path.parent.mkdir(parents=True, exist_ok=True)
    research_path.write_text("Knowledge packet.\n", "utf-8")


def _write_passing_status(curriculum_root: Path, *, level: str, slug: str) -> None:
    status_path = curriculum_root / level / "status" / f"{slug}.json"
    status_path.parent.mkdir(parents=True, exist_ok=True)
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


def test_plan_hash_changes_when_plan_file_changes(tmp_path: Path) -> None:
    plan_path = tmp_path / "demo.yaml"
    plan_path.write_text("title: Demo\nversion: '1.0'\n", "utf-8")

    first_hash = plan_hash(plan_path)

    plan_path.write_text("title: Demo updated\nversion: '1.1'\n", "utf-8")

    assert plan_hash(plan_path) != first_hash


def test_stale_flag_set_when_plan_changes_between_write_and_review(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    level = "b1"
    slug = "hash-drift"
    _write_manifest(curriculum_root, level=level, slug=slug)
    plan_path = _write_plan(curriculum_root, level=level, slug=slug, title="Original plan")
    tracked_hash = plan_hash(plan_path)
    state_path = _write_state(
        curriculum_root,
        level=level,
        slug=slug,
        tracked_hash=tracked_hash,
    )

    plan_path.write_text(plan_path.read_text("utf-8").replace("Original plan", "Updated plan"), "utf-8")

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    monkeypatch.setattr(v6_build, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(v6_build.ModuleBuildLock, "acquire", lambda self: True)
    monkeypatch.setattr(v6_build.ModuleBuildLock, "release", lambda self: None)
    monkeypatch.setattr(
        sys,
        "argv",
        ["v6_build.py", level, "1", "--step", "review", "--writer", "codex"],
    )

    assert v6_build.main() is False

    state = json.loads(state_path.read_text("utf-8"))
    for phase in ("skeleton", "write", "exercises", "annotate", "verify"):
        assert state["phases"][phase]["status"] == "stale"

    output = capsys.readouterr().out
    assert "WARN: Plan version changed since write phase" in output
    assert "Plan changed since last write — re-run from skeleton to rebuild with updated plan" in output


def test_resume_reruns_stale_phase(tmp_path: Path, monkeypatch) -> None:
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    level = "b1"
    slug = "stale-resume"
    _write_manifest(curriculum_root, level=level, slug=slug)
    plan_path = _write_plan(curriculum_root, level=level, slug=slug, title="Resume plan")
    _write_state(
        curriculum_root,
        level=level,
        slug=slug,
        tracked_hash=plan_hash(plan_path),
        stale_plan_phases=True,
    )
    _write_resume_inputs(curriculum_root, level=level, slug=slug)

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    monkeypatch.setattr(v6_build, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(v6_build.ModuleBuildLock, "acquire", lambda self: True)
    monkeypatch.setattr(v6_build.ModuleBuildLock, "release", lambda self: None)
    monkeypatch.setattr(v6_build, "_run_pre_build_gate", lambda *args, **kwargs: True)
    monkeypatch.setattr(v6_build, "_ensure_contract_artifacts", lambda *args, **kwargs: ({}, {}))
    monkeypatch.setattr(orch_index, "generate_index", lambda *args, **kwargs: None)

    calls: list[str] = []

    def fake_skeleton(*args, **kwargs):
        calls.append("skeleton")
        return "## Intro\n- Paragraph 1\n"

    def fake_pre_verify(*args, **kwargs):
        calls.append("pre-verify")
        return "Verified facts.\n"

    def fake_write(*args, **kwargs):
        calls.append("write")
        content_path = curriculum_root / level / f"{slug}.md"
        content_path.parent.mkdir(parents=True, exist_ok=True)
        content_path.write_text("# Content\n", "utf-8")
        return content_path

    def fake_activities(*args, **kwargs):
        calls.append("activities")
        path = curriculum_root / level / "activities" / f"{slug}.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("version: '1.0'\nmodule: stale-resume\nlevel: b1\ninline: []\nworkbook: []\n", "utf-8")
        return path

    def fake_vocab(*args, **kwargs):
        calls.append("vocab")
        path = curriculum_root / level / "vocabulary" / f"{slug}.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("[]\n", "utf-8")
        return path

    def fake_audit(*args, **kwargs):
        calls.append("audit")
        _write_passing_status(curriculum_root, level=level, slug=slug)
        return True

    monkeypatch.setattr(v6_build, "step_skeleton", fake_skeleton)
    monkeypatch.setattr(v6_build, "step_pre_verify", fake_pre_verify)
    monkeypatch.setattr(v6_build, "step_write_with_retry", fake_write)
    monkeypatch.setattr(v6_build, "step_activities", fake_activities)
    monkeypatch.setattr(v6_build, "step_repair", lambda *args, **kwargs: (True, False))
    monkeypatch.setattr(v6_build, "step_verify_exercises", lambda *args, **kwargs: True)
    monkeypatch.setattr(v6_build, "_post_process_content", lambda *args, **kwargs: 0)
    monkeypatch.setattr(v6_build, "step_vocab", fake_vocab)
    monkeypatch.setattr(v6_build, "step_verify", lambda *args, **kwargs: True)
    from build.convergence_loop import (
        ConvergenceRunResult,
    )

    monkeypatch.setattr(
        v6_build,
        "_run_convergence_loop",
        lambda *args, **kwargs: ConvergenceRunResult(
            terminal="pass",
            rounds=(
                {
                    "round_num": 1,
                    "writer": "codex",
                    "score_overall": 9.5,
                },
            ),
            trace=(),
            writer="codex",
        ),
    )
    monkeypatch.setattr(v6_build, "step_review_style", lambda *args, **kwargs: (True, 9.4, "phase: review-style\n"))
    monkeypatch.setattr(v6_build, "step_audit", fake_audit)
    monkeypatch.setattr(v6_build, "step_publish", lambda *args, **kwargs: True)
    monkeypatch.setattr(v6_build, "_inject_abetka_activities", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        sys,
        "argv",
        ["v6_build.py", level, "1", "--step", "publish", "--resume", "--writer", "codex"],
    )

    assert v6_build.main() is True
    assert "skeleton" in calls
    assert "write" in calls
    assert "audit" in calls
