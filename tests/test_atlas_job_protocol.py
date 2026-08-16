"""Hermetic tests for the Atlas VPS job protocol."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.lexicon.runner import atlas_job


def _plan(**overrides: object) -> dict:
    base: dict = {
        "schema": "atlas-job.v1",
        "id": "missing-tr-example",
        "host": "atlas-runner",
        "kind": "reenrich",
        "args": ["--target", "missing-translation"],
        "pointer_write": False,
        "result_sink": "restic",
        "denominator": 10,
        "success": {"circuit_breaker": False, "min_filled": 0},
    }
    base.update(overrides)
    return base


def test_valid_plan_is_ok() -> None:
    assert atlas_job.validate_plan(_plan()) == []


def test_rejects_hramatka_for_reenrich() -> None:
    errors = atlas_job.validate_plan(_plan(host="hramatka"))
    assert any("cannot run" in e or "must not target" in e for e in errors)


def test_rejects_pointer_write() -> None:
    errors = atlas_job.validate_plan(_plan(pointer_write=True))
    assert any("pointer_write" in e for e in errors)


def test_rejects_unknown_kind() -> None:
    errors = atlas_job.validate_plan(_plan(kind="scrape-web"))
    assert any("kind" in e for e in errors)


def test_submit_dry_run_sets_host(capsys: pytest.CaptureFixture[str]) -> None:
    rc = atlas_job.submit(_plan(), dry_run=True)
    assert rc == 0
    out = capsys.readouterr().out
    assert "atlas-runner" in out
    assert "launch_reenrich_class_b_remote.sh" in out
    assert "--no-poll" in out
    assert "atlas-job-missing-tr-example.service" in out


def test_submit_invalid_plan_exits_2() -> None:
    assert atlas_job.submit(_plan(host="hramatka"), dry_run=True) == 2


def test_close_without_registry_exits_2(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    assert atlas_job.close_job("no-such-job", skip_pull=True, skip_restic=True) == 2


def test_consecutive_misses_equal_targets_is_failed() -> None:
    summary = {
        "targets": 43,
        "consecutive_misses": 43,
        "filled_translation": 0,
        "circuit_breaker_tripped": False,
    }
    assert atlas_job.interpret_summary(summary, _plan()) == "failed"


def test_close_writes_result(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    plan = _plan()
    atlas_job.save_registry(
        {
            "id": plan["id"],
            "state": "running",
            "host": "atlas-runner",
            "kind": "reenrich",
            "unit": atlas_job.unit_name(plan["id"]),
            "result_sink": "restic",
            "plan": plan,
        }
    )
    rc = atlas_job.close_job(
        plan["id"],
        summary={
            "targets": 10,
            "consecutive_misses": 0,
            "filled_translation": 4,
            "circuit_breaker_tripped": False,
        },
        skip_pull=True,
        skip_restic=True,
    )
    assert rc == 0
    receipt = json.loads((tmp_path / f"{plan['id']}.result.json").read_text(encoding="utf-8"))
    assert receipt["state"] == "succeeded"
    row = atlas_job.load_registry(plan["id"])
    assert row is not None
    assert row["state"] == "succeeded"


def test_audit_flags_untracked_driver() -> None:
    lines = [
        "1234 /opt/x/.venv/bin/python scripts/lexicon/reenrich_thin_manifest_entries.py --local"
    ]
    orphans = atlas_job.audit_processes(lines, running_ids=[])
    assert orphans
    assert atlas_job.audit_processes(["pgrep -af reenrich"], running_ids=[]) == []


def test_cli_validate_and_dry_submit(tmp_path: Path) -> None:
    path = tmp_path / "job.json"
    path.write_text(json.dumps(_plan()), encoding="utf-8")
    assert atlas_job.main(["validate", str(path)]) == 0
    assert atlas_job.main(["submit", str(path), "--dry-run"]) == 0
