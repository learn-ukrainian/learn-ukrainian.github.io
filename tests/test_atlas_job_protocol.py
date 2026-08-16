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
        "issue": 6867,
        "success": {"circuit_breaker": False, "min_filled": 0},
    }
    base.update(overrides)
    return base


def _good_summary() -> dict:
    return {
        "targets": 10,
        "consecutive_misses": 0,
        "filled_translation": 4,
        "circuit_breaker_tripped": False,
    }


@pytest.fixture(autouse=True)
def _isolate_host(monkeypatch: pytest.MonkeyPatch) -> atlas_job.FakeHostAdapter:
    fake = atlas_job.FakeHostAdapter()
    atlas_job.set_host_adapter(fake)
    yield fake
    atlas_job.set_host_adapter(None)


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


def test_requires_campaign_issue() -> None:
    errors = atlas_job.validate_plan(_plan(issue=None))
    assert any("issue" in e for e in errors)


def test_submit_dry_run_sets_host_and_workdir(capsys: pytest.CaptureFixture[str]) -> None:
    rc = atlas_job.submit(_plan(), dry_run=True)
    assert rc == 0
    out = capsys.readouterr().out
    assert "atlas-runner" in out
    assert "launch_reenrich_class_b_remote.sh" in out
    assert "--no-poll" in out
    assert "atlas-job-missing-tr-example.service" in out
    assert "run-atlas-job-missing-tr-example" in out


def test_submit_invalid_plan_exits_2() -> None:
    assert atlas_job.submit(_plan(host="hramatka"), dry_run=True) == 2


def test_submit_checks_host_units(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, _isolate_host: atlas_job.FakeHostAdapter
) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    _isolate_host.units = [
        {
            "name": "atlas-job-other.service",
            "active": "active",
            "sub": "running",
            "main_pid": 99,
        }
    ]
    rc = atlas_job.submit(_plan(id="new-job"), dry_run=False, host_adapter=_isolate_host)
    assert rc == 2


def test_close_without_registry_exits_2(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    assert atlas_job.close_job("no-such-job", skip_pull=True, skip_restic=True) == 2


def test_close_empty_summary_is_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, _isolate_host: atlas_job.FakeHostAdapter
) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    plan = _plan()
    workdir = atlas_job.work_dir_for(plan["id"], plan)
    atlas_job.save_registry(
        {
            "id": plan["id"],
            "state": "running",
            "host": "atlas-runner",
            "kind": "reenrich",
            "unit": atlas_job.unit_name(plan["id"]),
            "workdir": workdir,
            "result_sink": "restic",
            "issue": plan["issue"],
            "plan": plan,
        }
    )
    rc = atlas_job.close_job(plan["id"], summary={}, skip_pull=True, skip_restic=True)
    assert rc == 1
    receipt = json.loads((tmp_path / f"{plan['id']}.result.json").read_text(encoding="utf-8"))
    assert receipt["state"] == "needs_finalize"
    assert receipt["pulled"] is False


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
            "workdir": atlas_job.work_dir_for(plan["id"], plan),
            "result_sink": "restic",
            "issue": plan["issue"],
            "plan": plan,
        }
    )
    rc = atlas_job.close_job(
        plan["id"],
        summary=_good_summary(),
        skip_pull=True,
        skip_restic=True,
    )
    assert rc == 0
    receipt = json.loads((tmp_path / f"{plan['id']}.result.json").read_text(encoding="utf-8"))
    assert receipt["state"] == "succeeded"
    assert receipt["pulled"] is False
    assert receipt["backup"]["ok"] is False
    assert receipt["issue"] == 6867
    row = atlas_job.load_registry(plan["id"])
    assert row is not None
    assert row["state"] == "succeeded"


def test_restic_doctor_fail_blocks_success_via_sink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    plan = _plan()
    atlas_job.save_registry(
        {
            "id": plan["id"],
            "state": "running",
            "host": "atlas-runner",
            "kind": "reenrich",
            "unit": atlas_job.unit_name(plan["id"]),
            "workdir": atlas_job.work_dir_for(plan["id"], plan),
            "result_sink": "restic",
            "issue": plan["issue"],
            "plan": plan,
        }
    )

    def fake_doctor() -> int:
        return 3

    monkeypatch.setattr(atlas_job, "_run_backup_doctor", fake_doctor)
    rc = atlas_job.close_job(
        plan["id"],
        summary=_good_summary(),
        skip_pull=True,
        skip_restic=False,
    )
    assert rc == 1
    receipt = json.loads((tmp_path / f"{plan['id']}.result.json").read_text(encoding="utf-8"))
    assert receipt["state"] == "succeeded"  # real job outcome kept
    assert receipt["backup"]["attempted"] is True
    assert receipt["backup"]["ok"] is False
    assert receipt["delivery"] == "failed"
    assert receipt["workdir_retained"] is True
    assert atlas_job.restic_sink_blocked()


def test_pulled_true_only_after_pull(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    plan = _plan(result_sink="git")
    atlas_job.save_registry(
        {
            "id": plan["id"],
            "state": "running",
            "host": "atlas-runner",
            "kind": "reenrich",
            "unit": atlas_job.unit_name(plan["id"]),
            "workdir": atlas_job.work_dir_for(plan["id"], plan),
            "result_sink": "git",
            "issue": plan["issue"],
            "plan": plan,
        }
    )
    calls: list[dict] = []

    def fake_pull(**kwargs: object) -> int:
        calls.append(dict(kwargs))
        return 0

    monkeypatch.setattr(atlas_job, "pull", fake_pull)
    rc = atlas_job.close_job(plan["id"], summary=_good_summary(), skip_pull=False, skip_restic=True)
    assert rc == 0
    assert calls
    receipt = json.loads((tmp_path / f"{plan['id']}.result.json").read_text(encoding="utf-8"))
    assert receipt["pulled"] is True


def test_audit_flags_untracked_driver() -> None:
    lines = [
        "1234 /opt/x/.venv/bin/python scripts/lexicon/reenrich_thin_manifest_entries.py --local"
    ]
    orphans = atlas_job.audit_processes(lines, running_ids=[])
    assert orphans
    assert atlas_job.audit_processes(["pgrep -af reenrich"], running_ids=[]) == []


def test_audit_with_running_id_matches_main_pid() -> None:
    lines = [
        "4242 /opt/x/.venv/bin/python scripts/lexicon/reenrich_thin_manifest_entries.py --local"
    ]
    tracked = [
        {
            "id": "missing-tr-example",
            "unit": "atlas-job-missing-tr-example.service",
            "workdir": "/home/ops/atlas-runner/run-atlas-job-missing-tr-example",
            "main_pid": 4242,
        }
    ]
    assert atlas_job.audit_processes(lines, tracked=tracked) == []
    # True orphan still flagged while a tracked job exists.
    other = [
        "9999 /opt/x/.venv/bin/python scripts/lexicon/reenrich_thin_manifest_entries.py --local"
    ]
    assert atlas_job.audit_processes(other, tracked=tracked)


def test_status_reconciles_inactive_unit_to_needs_finalize(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, _isolate_host: atlas_job.FakeHostAdapter
) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    plan = _plan()
    workdir = atlas_job.work_dir_for(plan["id"], plan)
    atlas_job.save_registry(
        {
            "id": plan["id"],
            "state": "running",
            "host": "atlas-runner",
            "kind": "reenrich",
            "unit": atlas_job.unit_name(plan["id"]),
            "workdir": workdir,
            "resume": "checkpoint",
            "result_sink": "restic",
            "issue": plan["issue"],
            "plan": plan,
        }
    )
    _isolate_host.exit_status_by_workdir[workdir] = {
        "service_result": "success",
        "exit_status": "0",
    }
    rc = atlas_job.status(host="atlas-runner", host_adapter=_isolate_host)
    assert rc == 0
    row = atlas_job.load_registry(plan["id"])
    assert row is not None
    assert row["state"] == "needs_finalize"


def test_git_receipt_rejects_absolute_paths() -> None:
    bad = {
        "schema": "atlas-job-result.v1",
        "id": "x",
        "state": "succeeded",
        "summary": {"note": "/Users/secret/path"},
    }
    errors = atlas_job.validate_git_receipt(bad)
    assert any("absolute path" in e for e in errors)


def test_cli_validate_and_dry_submit(tmp_path: Path) -> None:
    path = tmp_path / "job.json"
    path.write_text(json.dumps(_plan()), encoding="utf-8")
    assert atlas_job.main(["validate", str(path)]) == 0
    assert atlas_job.main(["submit", str(path), "--dry-run"]) == 0
