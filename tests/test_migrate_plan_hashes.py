"""Tests for the one-time plan-hash backfill migration."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from scripts.build import migrate_plan_hashes as migrate


def _write_plan(curriculum_root: Path, *, level: str, slug: str, title: str = "Demo") -> Path:
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
                "objectives": ["Migration test"],
                "word_target": 1200,
                "content_outline": [
                    {"section": "Intro", "words": 600},
                    {"section": "Підсумок", "words": 600},
                ],
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
    phase_names: tuple[str, ...] = migrate.PLAN_HASH_PHASES,
) -> Path:
    phases = {
        phase: {"status": "complete", "ts": "2026-04-10T00:00:00+00:00"}
        for phase in phase_names
    }
    state_path = curriculum_root / level / "orchestration" / slug / "state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(
            {
                "mode": "v6",
                "track": level,
                "slug": slug,
                "phases": phases,
            },
            indent=2,
        ),
        "utf-8",
    )
    return state_path


def test_dry_run_does_not_write(tmp_path: Path, monkeypatch, capsys) -> None:
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    level = "a1"
    slug = "demo"

    monkeypatch.setattr(migrate, "CURRICULUM_ROOT", curriculum_root)
    _write_plan(curriculum_root, level=level, slug=slug)
    state_path = _write_state(curriculum_root, level=level, slug=slug)
    original = state_path.read_text("utf-8")

    assert migrate.main(["--dry-run"]) == 0

    assert state_path.read_text("utf-8") == original
    output = capsys.readouterr().out
    assert "DRY RUN a1/demo" in output
    assert "updated 5 phase records" in output


def test_migration_populates_missing_hashes(tmp_path: Path, monkeypatch) -> None:
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    level = "b1"
    slug = "hash-backfill"

    monkeypatch.setattr(migrate, "CURRICULUM_ROOT", curriculum_root)
    plan_path = _write_plan(curriculum_root, level=level, slug=slug, title="Backfill plan")
    state_path = _write_state(curriculum_root, level=level, slug=slug)

    result = migrate.migrate_state_file(state_path)

    assert result is not None
    assert result.updated_phase_records == 5
    assert result.stale_phase_records == 0

    current_hash = migrate.plan_hash(plan_path)
    updated = json.loads(state_path.read_text("utf-8"))
    for phase_name in migrate.PLAN_HASH_PHASES:
        assert updated["phases"][phase_name]["plan_hash"] == current_hash
        assert updated["phases"][phase_name]["status"] == "complete"
        assert "stale_reason" not in updated["phases"][phase_name]


def test_migration_marks_stale_when_plan_missing(tmp_path: Path, monkeypatch) -> None:
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    level = "c1"
    slug = "missing-plan"

    monkeypatch.setattr(migrate, "CURRICULUM_ROOT", curriculum_root)
    state_path = _write_state(curriculum_root, level=level, slug=slug, phase_names=("write", "verify"))

    result = migrate.migrate_state_file(state_path)

    assert result is not None
    assert result.updated_phase_records == 2
    assert result.stale_phase_records == 2

    updated = json.loads(state_path.read_text("utf-8"))
    for phase_name in ("write", "verify"):
        assert "plan_hash" not in updated["phases"][phase_name]
        assert updated["phases"][phase_name]["status"] == "stale"
        assert updated["phases"][phase_name]["stale_reason"] == "plan_file_missing"
        assert updated["phases"][phase_name]["previous_status"] == "complete"
