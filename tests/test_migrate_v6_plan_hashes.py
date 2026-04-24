"""Tests for the one-shot v6 plan-hash migration."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import migrate.migrate_v6_plan_hashes as migrate_plan_hashes


def test_migration_backfills_plan_hashes_and_marks_stale_when_plan_is_newer(
    tmp_path: Path,
    monkeypatch,
) -> None:
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    monkeypatch.setattr(migrate_plan_hashes, "CURRICULUM_ROOT", curriculum_root)

    plan_path = curriculum_root / "plans" / "a1" / "demo.yaml"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        yaml.safe_dump(
            {
                "module": "demo",
                "slug": "demo",
                "level": "A1",
                "sequence": 1,
                "version": "1.0",
                "title": "Demo",
                "focus": "grammar",
                "pedagogy": "PPP",
                "phase": "A1.1",
                "objectives": ["Demo"],
                "word_target": 1200,
                "content_outline": [{"section": "Intro", "words": 600}, {"section": "Підсумок", "words": 600}],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        "utf-8",
    )

    orch_dir = curriculum_root / "a1" / "orchestration" / "demo"
    orch_dir.mkdir(parents=True, exist_ok=True)
    state_path = orch_dir / "state.json"
    phases = {
        phase: {"status": "complete", "ts": "2026-04-10T00:00:00+00:00"}
        for phase in migrate_plan_hashes.PHASE_ORDER
    }
    state_path.write_text(
        json.dumps({"mode": "v6", "track": "a1", "slug": "demo", "phases": phases}, indent=2),
        "utf-8",
    )

    future = time.time() + 3600
    os.utime(plan_path, (future, future))

    result = migrate_plan_hashes.migrate_state_file(state_path, apply=True)

    assert result is not None
    assert result["backfilled_phases"] == 6
    assert result["stale_modules"] == 1
    updated = json.loads(state_path.read_text("utf-8"))
    assert updated["phases"]["skeleton"]["plan_hash"]
    assert updated["phases"]["skeleton"]["status"] == "stale"
    assert updated["phases"]["publish"]["status"] == "stale"
