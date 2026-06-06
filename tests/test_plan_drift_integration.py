"""Integration coverage for plan drift invalidation and contradiction checks."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import migrate.migrate_v6_plan_hashes as migrate_plan_hashes
from build.phases.plan_validator import validate_plan_consistency
from build.plan_tracking import PLAN_HASH_PHASES

PROJECT_ROOT = Path(__file__).resolve().parent.parent


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
                "objectives": ["Plan drift integration test"],
                "word_target": 1200,
                "content_outline": [
                    {"section": "Intro", "words": 600, "points": ["Dialogue about the current plan."]},
                    {"section": "Підсумок", "words": 600},
                ],
                "dialogue_situations": [
                    {
                        "setting": "classroom planning discussion",
                        "speakers": ["Викладач", "Студент"],
                        "motivation": "Discuss the lesson plan",
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
    tracked_hash: str | None = None,
) -> Path:
    phases = {
        phase: {"status": "complete", "ts": "2026-04-10T00:00:00+00:00"}
        for phase in (*PLAN_HASH_PHASES, "publish")
    }
    if tracked_hash is not None:
        for phase in PLAN_HASH_PHASES:
            phases[phase]["plan_hash"] = tracked_hash

    orch_dir = curriculum_root / level / "orchestration" / slug
    orch_dir.mkdir(parents=True, exist_ok=True)
    state_path = orch_dir / "state.json"
    state_path.write_text(
        json.dumps({"mode": "v6", "track": level, "slug": slug, "phases": phases}, indent=2),
        "utf-8",
    )
    (orch_dir / "pre-verify-results.md").write_text("Verified facts.\n", "utf-8")
    # Create a minimal review artifact so the ``review_complete_no_artifact``
    # state-drift detector doesn't fire before the plan-hash detector —
    # these tests target the plan-hash path. Without this, every test
    # here asserts on the wrong drift reason.
    review_dir = curriculum_root / level / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / f"{slug}-review.md").write_text(
        "## Verdict: PASS\nscore 9.0/10\n", "utf-8",
    )
    return state_path


def test_two_track_migration_flags_both_correctly(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    monkeypatch.setattr(migrate_plan_hashes, "CURRICULUM_ROOT", curriculum_root)

    state_paths: dict[str, Path] = {}
    future = time.time() + 3600
    for track in ("a1", "a2"):
        slug = f"{track}-plan-drift"
        plan_path = _write_plan(curriculum_root, level=track, slug=slug, title=f"{track} plan")
        state_paths[track] = _write_state(curriculum_root, level=track, slug=slug)
        os.utime(plan_path, (future, future))

    monkeypatch.setattr(sys, "argv", ["migrate_v6_plan_hashes.py", "--apply"])

    assert migrate_plan_hashes.main() == 0

    output = capsys.readouterr().out
    assert "a1: scanned=1" in output
    assert "a2: scanned=1" in output

    for state_path in state_paths.values():
        state = json.loads(state_path.read_text("utf-8"))
        for phase in PLAN_HASH_PHASES:
            assert state["phases"][phase]["plan_hash"]
            assert state["phases"][phase]["status"] == "stale"
        assert state["phases"]["publish"]["status"] == "stale"


def test_plan_contradiction_validator_integration() -> None:
    clean_plan_path = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "plans" / "a1" / "at-the-cafe.yaml"
    clean_plan = yaml.safe_load(clean_plan_path.read_text("utf-8"))

    assert clean_plan.get("dialogue_situations")
    assert validate_plan_consistency(clean_plan, clean_plan_path.stem) == []

    contradictory_plan = {
        "dialogue_situations": [
            {
                "setting": "At a pet shop with animals and pet items, not room furniture.",
                "speakers": ["Марія", "Оленка"],
                "motivation": "Practice він/вона/воно with pet-shop nouns",
            }
        ],
        "content_outline": [
            {
                "section": "Діалоги",
                "words": 300,
                "points": [
                    "Dialogue 1 — Video call showing your room with a table, lamp, and bed.",
                    "Dialogue 2 — Ask what is in your bag.",
                ],
            }
        ],
    }

    messages = validate_plan_consistency(contradictory_plan, "synthetic-pet-shop")

    assert len(messages) == 1
    assert "synthetic-pet-shop" in messages[0]
    assert "room furniture" in messages[0]
    assert "room" in messages[0]
