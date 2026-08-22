"""Hermetic tests for the Atlas VPS job protocol."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from scripts.lexicon.runner import atlas_job


def _git_env() -> dict[str, str]:
    return {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}


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


@pytest.fixture(autouse=True)
def _non_operational_run_root(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_RUN_ROOT", "/tmp/atlas-run-root")


def test_source_has_no_baked_ops_home_defaults() -> None:
    text = Path(atlas_job.__file__).read_text(encoding="utf-8")
    assert "/home/ops" not in text


def test_valid_plan_is_ok() -> None:
    assert atlas_job.validate_plan(_plan()) == []


def test_allows_hramatka_for_reenrich() -> None:
    assert atlas_job.validate_plan(_plan(host="hramatka")) == []


def test_allows_vps_alias_for_reenrich() -> None:
    # "vps" remains an allowed plan-host token (occupancy sanitizer denylist).
    assert atlas_job.validate_plan(_plan(host="vps")) == []


def test_rejects_unknown_host() -> None:
    errors = atlas_job.validate_plan(_plan(host="mystery-host"))
    assert any("host" in e for e in errors)


def test_rejects_pointer_write() -> None:
    errors = atlas_job.validate_plan(_plan(pointer_write=True))
    assert any("pointer_write" in e for e in errors)


def test_rejects_unknown_kind() -> None:
    errors = atlas_job.validate_plan(_plan(kind="scrape-web"))
    assert any("kind" in e for e in errors)


def test_requires_campaign_issue() -> None:
    errors = atlas_job.validate_plan(_plan(issue=None))
    assert any("issue" in e for e in errors)


def test_rejects_bool_for_numeric_fields() -> None:
    """bool is a subclass of int; plans must not accept true/false as numbers."""
    for field, value in (
        ("issue", True),
        ("issue", False),
        ("denominator", True),
        ("denominator", False),
        ("timeout_seconds", True),
        ("timeout_seconds", False),
    ):
        errors = atlas_job.validate_plan(_plan(**{field: value}))
        assert any(field in e for e in errors), (field, value, errors)


def test_remote_launcher_forwards_protocol_env() -> None:
    """atlas_job.submit sets protocol env; remote_cmd must forward them over SSH."""
    source = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "lexicon"
        / "runner"
        / "launch_reenrich_class_b_remote.sh"
    ).read_text(encoding="utf-8")
    # Each var must be appended to remote_cmd with the same printf %q style as UNIT.
    for var in (
        "ATLAS_RE_ENRICH_RUNTIME_MAX_SEC",
        "ATLAS_JOB_EXIT_STATUS_FILE",
        "ATLAS_RE_ENRICH_RESTART",
    ):
        assert f'if [[ -n "${{{var}:-}}" ]]; then' in source
        assert f'remote_cmd+=" {var}=$(printf \'%q\' "${var}")"' in source
    # UNIT already forwarded; protocol vars must appear after that block.
    unit_fwd = source.index('remote_cmd+=" ATLAS_RE_ENRICH_UNIT=$(printf')
    runtime_fwd = source.index("ATLAS_RE_ENRICH_RUNTIME_MAX_SEC=$(printf")
    assert runtime_fwd > unit_fwd


def test_ssh_host_adapter_list_units_uses_plain() -> None:
    import inspect

    src = inspect.getsource(atlas_job.SshHostAdapter.list_atlas_job_units)
    assert "--plain" in src
    assert "list-units" in src


def test_submit_dry_run_sets_host_and_workdir(capsys: pytest.CaptureFixture[str]) -> None:
    rc = atlas_job.submit(_plan(), dry_run=True)
    assert rc == 0
    out = capsys.readouterr().out
    assert "atlas-runner" in out
    assert "launch_reenrich_class_b_remote.sh" in out
    assert "--no-poll" in out
    assert "atlas-job-missing-tr-example.service" in out
    assert "run-atlas-job-missing-tr-example" in out


def test_submit_dry_run_uses_env_run_root_for_any_host(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = atlas_job.submit(_plan(id="hramatka-dry", host="hramatka"), dry_run=True)
    assert rc == 0
    out = capsys.readouterr().out
    assert "hramatka" in out
    assert "/tmp/atlas-run-root/run-atlas-job-hramatka-dry" in out


def test_submit_forwards_required_run_root_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, _isolate_host: atlas_job.FakeHostAdapter
) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    monkeypatch.setenv("ATLAS_RUN_ROOT", "/tmp/custom-run-root")
    captured_env: dict[str, str] = {}

    def fake_subprocess_call(cmd: list[str], **kwargs: object) -> int:
        captured_env.update(kwargs.get("env") or {})
        return 0

    monkeypatch.setattr(atlas_job.subprocess, "call", fake_subprocess_call)
    plan = _plan(id="hramatka-run-root", host="hramatka")
    rc = atlas_job.submit(plan, dry_run=False, host_adapter=_isolate_host)
    assert rc == 0
    assert captured_env["ATLAS_RUN_ROOT"] == "/tmp/custom-run-root"


def test_submit_invalid_plan_exits_2() -> None:
    assert atlas_job.submit(_plan(host="mystery-host"), dry_run=True) == 2


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
            "workdir": "/tmp/atlas-run-root/run-atlas-job-missing-tr-example",
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


def test_status_accepts_hramatka(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, _isolate_host: atlas_job.FakeHostAdapter
) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    rc = atlas_job.status(host="hramatka", host_adapter=_isolate_host)
    assert rc == 0


def test_pull_accepts_hramatka(monkeypatch: pytest.MonkeyPatch) -> None:
    launched: list[list[str]] = []

    def fake_subprocess_call(cmd: list[str], **kwargs: object) -> int:
        launched.append(cmd)
        return 0

    monkeypatch.setattr(atlas_job.subprocess, "call", fake_subprocess_call)
    rc = atlas_job.pull(host="hramatka")
    assert rc == 0
    assert launched


def test_pull_forwards_required_run_root_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """pull must forward ATLAS_RUN_ROOT (mirrors submit)."""
    monkeypatch.setenv("ATLAS_RUN_ROOT", "/tmp/custom-run-root")
    captured_env: dict[str, str] = {}

    def fake_subprocess_call(cmd: list[str], **kwargs: object) -> int:
        captured_env.update(kwargs.get("env") or {})
        return 0

    monkeypatch.setattr(atlas_job.subprocess, "call", fake_subprocess_call)
    rc = atlas_job.pull(host="hramatka")
    assert rc == 0
    assert captured_env["ATLAS_RUN_ROOT"] == "/tmp/custom-run-root"


def test_git_receipt_rejects_absolute_paths() -> None:
    bad = {
        "schema": "atlas-job-result.v1",
        "id": "x",
        "state": "succeeded",
        "summary": {"note": "/Users/secret/path"},
    }
    errors = atlas_job.validate_git_receipt(bad)
    assert any("absolute path" in e for e in errors)


def test_build_git_receipt_redacts_absolute_paths_in_backup_error() -> None:
    full = {
        "schema": "atlas-job-result.v1",
        "id": "smoke",
        "state": "succeeded",
        "delivery": "ok",
        "workdir": "/tmp/atlas-run-root/run-atlas-job-smoke",
        "backup": {
            "attempted": True,
            "ok": False,
            "snapshot_id": None,
            "error": "needs /Users/me/proj/.venv/bin/python",
        },
        "summary": {
            "targets": 5,
            "consecutive_misses": 0,
            "filled_translation": 0,
            "circuit_breaker_tripped": False,
        },
    }
    capped = atlas_job.build_git_receipt(full)
    assert capped["workdir"] == "run-atlas-job-smoke"
    assert "/Users/" not in json.dumps(capped)
    assert "<abs>" in capped["backup"]["error"]
    assert atlas_job.validate_git_receipt(capped) == []


def test_close_writes_git_receipt_with_delivery_ok(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, _isolate_host: atlas_job.FakeHostAdapter
) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    plan = _plan(id="delivery-ok", result_sink="git")
    workdir = atlas_job.work_dir_for(plan["id"], plan)
    atlas_job.save_registry(
        {
            "id": plan["id"],
            "state": "running",
            "host": plan["host"],
            "kind": plan["kind"],
            "unit": atlas_job.unit_name(plan["id"]),
            "workdir": workdir,
            "issue": plan["issue"],
            "plan_sha256": "abc",
            "denominator": plan["denominator"],
            "result_sink": "git",
            "plan": plan,
        }
    )
    _isolate_host.exit_status_by_workdir[workdir] = {
        "service_result": "success",
        "exit_status": "0",
    }
    rc = atlas_job.close_job(
        plan["id"],
        summary=_good_summary(),
        skip_pull=True,
        skip_restic=True,
        host_adapter=_isolate_host,
    )
    assert rc == 0
    receipt = json.loads(atlas_job.git_receipt_path(plan["id"]).read_text(encoding="utf-8"))
    assert receipt["delivery"] == "ok"
    assert receipt["state"] == "succeeded"


def test_cli_validate_and_dry_submit(tmp_path: Path) -> None:
    path = tmp_path / "job.json"
    path.write_text(json.dumps(_plan()), encoding="utf-8")
    assert atlas_job.main(["validate", str(path)]) == 0
    assert atlas_job.main(["submit", str(path), "--dry-run"]) == 0


def test_require_safe_job_id_rejects_traversal_and_bool() -> None:
    for bad in ("../escape", "/etc/passwd", True, False, "", "a/b", "job id", None, 12):
        with pytest.raises(ValueError):
            atlas_job.require_safe_job_id(bad)  # type: ignore[arg-type]
    assert atlas_job.require_safe_job_id("missing-tr-example") == "missing-tr-example"
    assert atlas_job.require_safe_job_id("ab") == "ab"


def test_path_builders_reject_unsafe_job_id(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    for bad in ("../escape", "/etc/passwd", "true/../x"):
        with pytest.raises(ValueError):
            atlas_job.registry_path(bad)
        with pytest.raises(ValueError):
            atlas_job.result_path(bad)
        with pytest.raises(ValueError):
            atlas_job.git_receipt_path(bad)
        with pytest.raises(ValueError):
            atlas_job.local_pull_dir(bad)
        with pytest.raises(ValueError):
            atlas_job.mirror_dir_for(bad)
        with pytest.raises(ValueError):
            atlas_job.unit_name(bad)
        with pytest.raises(ValueError):
            atlas_job.work_dir_for(bad)
        with pytest.raises(ValueError):
            atlas_job.load_registry(bad)
    # No files created outside the registry root for a traversal id attempt.
    assert list(tmp_path.iterdir()) == []
    assert not (tmp_path / "escape.json").exists()
    assert not (tmp_path.parent / "escape.json").exists()


def test_workdir_honored_only_when_safe(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_RUN_ROOT", str(tmp_path / "runs"))
    job = "safe-job"
    nested = tmp_path / "runs" / "run-atlas-job-safe-job"
    assert atlas_job.work_dir_for(job, {"workdir": str(nested)}) in {str(nested), str(nested.resolve())}
    assert atlas_job.work_dir_for(job, {"workdir": "run-atlas-job-safe-job"}) == (
        "run-atlas-job-safe-job"
    )
    for bad in ("../escape", "/etc/passwd", "/tmp/evil", "foo/../../etc", "has space"):
        with pytest.raises(ValueError):
            atlas_job.work_dir_for(job, {"workdir": bad})
        errors = atlas_job.validate_plan(_plan(workdir=bad))
        assert errors, bad

    monkeypatch.delenv("ATLAS_RUN_ROOT", raising=False)
    with pytest.raises(ValueError, match="ATLAS_RUN_ROOT is required"):
        atlas_job.require_safe_workdir("/tmp/atlas-run-root/run-atlas-job-test")


def test_work_dir_for_requires_run_root_and_ignores_host(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ATLAS_RUN_ROOT", "/tmp/atlas-run-root")
    assert atlas_job.work_dir_for("ar-job", _plan(id="ar-job")) == (
        "/tmp/atlas-run-root/run-atlas-job-ar-job"
    )
    assert atlas_job.work_dir_for(
        "hramatka-job", _plan(id="hramatka-job", host="hramatka")
    ) == "/tmp/atlas-run-root/run-atlas-job-hramatka-job"
    assert atlas_job.work_dir_for("vps-job", _plan(id="vps-job", host="vps")) == (
        "/tmp/atlas-run-root/run-atlas-job-vps-job"
    )
    monkeypatch.delenv("ATLAS_RUN_ROOT", raising=False)
    with pytest.raises(ValueError, match="ATLAS_RUN_ROOT is required"):
        atlas_job.work_dir_for("ar-job", _plan(id="ar-job"))


def test_close_and_cli_reject_unsafe_job_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    with pytest.raises(ValueError):
        atlas_job.close_job("../escape", skip_pull=True, skip_restic=True)
    assert atlas_job.main(["close", "../escape", "--skip-pull", "--skip-restic"]) == 2
    assert atlas_job.main(["pull", "--job-id", "../escape"]) == 2
    assert list(tmp_path.iterdir()) == []


def test_min_free_disk_bytes_parsing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ATLAS_MIN_FREE_DISK_BYTES", raising=False)
    monkeypatch.delenv("ATLAS_MIN_FREE_DISK_GIB", raising=False)
    monkeypatch.delenv("ATLAS_MIN_FREE_DISK_GB", raising=False)
    assert atlas_job.min_free_disk_bytes() == atlas_job.DEFAULT_MIN_FREE_DISK_BYTES
    assert atlas_job.min_free_disk_bytes() == 5 * 1024 * 1024 * 1024

    monkeypatch.setenv("ATLAS_MIN_FREE_DISK_BYTES", "10737418240")
    assert atlas_job.min_free_disk_bytes() == 10 * 1024 * 1024 * 1024

    monkeypatch.delenv("ATLAS_MIN_FREE_DISK_BYTES")
    monkeypatch.setenv("ATLAS_MIN_FREE_DISK_GIB", "2.5")
    assert atlas_job.min_free_disk_bytes() == int(2.5 * 1024 * 1024 * 1024)

    monkeypatch.delenv("ATLAS_MIN_FREE_DISK_GIB")
    monkeypatch.setenv("ATLAS_MIN_FREE_DISK_GB", "4")
    assert atlas_job.min_free_disk_bytes() == 4 * 1024 * 1024 * 1024

    # Invalid string fallbacks to default when other env vars are unset.
    monkeypatch.delenv("ATLAS_MIN_FREE_DISK_GB")
    monkeypatch.setenv("ATLAS_MIN_FREE_DISK_BYTES", "invalid")
    assert atlas_job.min_free_disk_bytes() == atlas_job.DEFAULT_MIN_FREE_DISK_BYTES


def test_submit_refuses_when_host_free_disk_below_floor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, _isolate_host: atlas_job.FakeHostAdapter
) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    # 1 GiB free disk is below the 5 GiB default floor.
    _isolate_host.free_disk_bytes_value = 1 * 1024 * 1024 * 1024

    plan = _plan(id="low-disk-job")
    rc = atlas_job.submit(plan, dry_run=False, host_adapter=_isolate_host)
    assert rc == 2

    # Journal records the refusal fail-closed.
    row = atlas_job.load_registry("low-disk-job")
    assert row is not None
    assert row["state"] == "rejected"
    assert "insufficient host free disk" in row["refusal_reason"]
    assert row["free_disk_bytes"] == 1 * 1024 * 1024 * 1024
    assert row["min_free_disk_bytes"] == atlas_job.DEFAULT_MIN_FREE_DISK_BYTES


def test_submit_honors_env_override_min_free_disk_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, _isolate_host: atlas_job.FakeHostAdapter
) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    # Override floor to 100 MB.
    monkeypatch.setenv("ATLAS_MIN_FREE_DISK_BYTES", str(100 * 1024 * 1024))
    _isolate_host.free_disk_bytes_value = 200 * 1024 * 1024

    launched: list[list[str]] = []

    def fake_subprocess_call(cmd: list[str], **kwargs: object) -> int:
        launched.append(cmd)
        return 0

    monkeypatch.setattr(atlas_job.subprocess, "call", fake_subprocess_call)

    plan = _plan(id="override-ok-job")
    rc = atlas_job.submit(plan, dry_run=False, host_adapter=_isolate_host)
    assert rc == 0
    assert len(launched) == 1

    row = atlas_job.load_registry("override-ok-job")
    assert row is not None
    assert row["state"] == "running"


def test_submit_honors_env_override_min_free_disk_gib(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, _isolate_host: atlas_job.FakeHostAdapter
) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    # Higher override via GIB causes refusal.
    monkeypatch.setenv("ATLAS_MIN_FREE_DISK_GIB", "10")
    _isolate_host.free_disk_bytes_value = 6 * 1024 * 1024 * 1024
    plan_refused = _plan(id="override-refused-job")
    rc_refused = atlas_job.submit(plan_refused, dry_run=False, host_adapter=_isolate_host)
    assert rc_refused == 2
    row_refused = atlas_job.load_registry("override-refused-job")
    assert row_refused is not None
    assert row_refused["state"] == "rejected"
    assert row_refused["min_free_disk_bytes"] == 10 * 1024 * 1024 * 1024


def test_submit_refuses_when_free_disk_check_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, _isolate_host: atlas_job.FakeHostAdapter
) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))

    def fake_free_disk_err(host: str, path: str | None = None) -> int:
        raise ConnectionError("host disk probe failed")

    monkeypatch.setattr(_isolate_host, "free_disk_bytes", fake_free_disk_err)

    plan = _plan(id="disk-err-job")
    rc = atlas_job.submit(plan, dry_run=False, host_adapter=_isolate_host)
    assert rc == 2

    row = atlas_job.load_registry("disk-err-job")
    assert row is not None
    assert row["state"] == "rejected"
    assert "host free disk check failed" in row["refusal_reason"]


def test_submit_refuses_restic_sink_when_restic_sink_blocked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, _isolate_host: atlas_job.FakeHostAdapter
) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    atlas_job.set_restic_sink_blocked("doctor failed")

    # sink='restic' is refused
    plan_restic = _plan(id="restic-job", result_sink="restic")
    rc = atlas_job.submit(plan_restic, dry_run=False, host_adapter=_isolate_host)
    assert rc == 2
    row = atlas_job.load_registry("restic-job")
    assert row is not None
    assert row["state"] == "rejected"
    assert "restic sink blocked" in row["refusal_reason"]

    # sink='both' is refused
    plan_both = _plan(id="both-job", result_sink="both")
    rc_both = atlas_job.submit(plan_both, dry_run=False, host_adapter=_isolate_host)
    assert rc_both == 2
    row_both = atlas_job.load_registry("both-job")
    assert row_both is not None
    assert row_both["state"] == "rejected"
    assert "restic sink blocked" in row_both["refusal_reason"]


def test_submit_allows_git_sink_when_restic_sink_blocked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, _isolate_host: atlas_job.FakeHostAdapter
) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    atlas_job.set_restic_sink_blocked("doctor failed")

    def fake_subprocess_call(cmd: list[str], **kwargs: object) -> int:
        return 0

    monkeypatch.setattr(atlas_job.subprocess, "call", fake_subprocess_call)

    # sink='git' is NOT blocked by restic sink block
    plan_git = _plan(id="git-job", result_sink="git")
    rc = atlas_job.submit(plan_git, dry_run=False, host_adapter=_isolate_host)
    assert rc == 0
    row = atlas_job.load_registry("git-job")
    assert row is not None
    assert row["state"] == "running"


def test_ssh_host_adapter_free_disk_bytes_source() -> None:
    import inspect

    src = inspect.getsource(atlas_job.SshHostAdapter.free_disk_bytes)
    assert "shutil.disk_usage" in src
    assert "while not p.exists()" in src


def test_load_backup_env_file_expands_home_and_refs(tmp_path: Path) -> None:
    env_file = tmp_path / "backup.env"
    env_file.write_text(
        "\n".join(
            [
                "export LU_BACKUP_REPOSITORY=rclone:example:restic",
                'RESTIC_PASSWORD_FILE="$HOME/.secrets/demo.password"',
                "RESTIC_REPOSITORY=$LU_BACKUP_REPOSITORY",
                "",
            ]
        ),
        encoding="utf-8",
    )
    loaded = atlas_job._load_backup_env_file(env_file)
    assert loaded["LU_BACKUP_REPOSITORY"] == "rclone:example:restic"
    assert loaded["RESTIC_REPOSITORY"] == "rclone:example:restic"
    assert loaded["RESTIC_PASSWORD_FILE"] == str(
        Path.home() / ".secrets" / "demo.password"
    )


def test_registry_dir_uses_primary_when_file_is_under_release_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """API release snapshots must not own batch_state/atlas-jobs."""
    primary = tmp_path / "primary"
    primary.mkdir()
    subprocess.run(
        ["git", "init", "-q", "-b", "main", str(primary)],
        check=True,
        capture_output=True,
        text=True,
        env=_git_env(),
        timeout=30,
    )

    release_sha = "a4c8c4f9" + ("0" * 32)
    fake_file = (
        primary / ".runtime" / "api" / "releases" / release_sha / "scripts" / "lexicon" / "runner" / "atlas_job.py"
    )
    fake_file.parent.mkdir(parents=True)
    fake_file.write_text("# fake release copy\n", encoding="utf-8")

    monkeypatch.setattr(atlas_job, "__file__", str(fake_file))
    monkeypatch.delenv("ATLAS_JOB_REGISTRY", raising=False)

    assert atlas_job.repo_root() == (primary / ".runtime" / "api" / "releases" / release_sha).resolve()
    assert atlas_job.registry_dir() == (primary.resolve() / "batch_state" / "atlas-jobs")


def test_backup_subprocess_env_defaults_project_root_to_primary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file = tmp_path / "backup.env"
    env_file.write_text(
        "LU_BACKUP_REPOSITORY=rclone:example:restic\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("LU_BACKUP_ENV_FILE", str(env_file))
    monkeypatch.delenv("LU_BACKUP_PROJECT_ROOT", raising=False)
    monkeypatch.setattr(
        atlas_job, "primary_checkout_root", lambda: Path("/tmp/primary-checkout")
    )

    env = atlas_job._backup_subprocess_env()
    assert env["LU_BACKUP_PROJECT_ROOT"] == "/tmp/primary-checkout"
    assert env["LU_BACKUP_REPOSITORY"] == "rclone:example:restic"


def test_backup_subprocess_env_keeps_explicit_project_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file = tmp_path / "backup.env"
    env_file.write_text("LU_BACKUP_HOST=learn-ukrainian\n", encoding="utf-8")
    monkeypatch.setenv("LU_BACKUP_ENV_FILE", str(env_file))
    monkeypatch.setenv("LU_BACKUP_PROJECT_ROOT", "/explicit/project")
    monkeypatch.setattr(
        atlas_job, "primary_checkout_root", lambda: Path("/tmp/primary-checkout")
    )

    env = atlas_job._backup_subprocess_env()
    assert env["LU_BACKUP_PROJECT_ROOT"] == "/explicit/project"


def test_mirror_dir_for_uses_primary_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        atlas_job, "primary_checkout_root", lambda: Path("/tmp/primary-checkout")
    )
    assert atlas_job.mirror_dir_for("job-1").resolve() == Path(
        "/tmp/primary-checkout/data/lexicon/runner-mirror/job-1"
    ).resolve()


def test_collect_host_load_shape(tmp_path: Path) -> None:
    payload = atlas_job.collect_host_load(run_root=tmp_path)
    assert payload["cpu_count"] >= 1
    assert len(payload["loadavg"]) == 3
    assert set(payload["mem"]) == {"available_bytes", "total_bytes", "pct"}
    assert set(payload["disk"]) == {"available_bytes", "total_bytes", "pct"}
    assert payload["disk"]["total_bytes"] > 0
    assert set(payload["job_unit"]) == {"active_count", "job_id", "state"}


def test_ssh_host_load_skips_ssh_for_self_host(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ATLAS_JOB_SELF_HOST", "job-box")
    monkeypatch.setenv("ATLAS_RUN_ROOT", str(tmp_path))
    real_run = atlas_job.subprocess.run

    def guarded(cmd: list[str], **kwargs: object) -> object:
        if cmd and cmd[0] == "ssh":
            raise AssertionError("ssh must not run for self-host load")
        return real_run(cmd, **kwargs)

    monkeypatch.setattr(atlas_job.subprocess, "run", guarded)
    payload = atlas_job.SshHostAdapter().host_load("job-box")
    assert "cpu_count" in payload
    assert "loadavg" in payload
    assert "mem" in payload
    assert "disk" in payload


def test_ssh_host_load_uses_ssh_when_not_self(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ATLAS_JOB_SELF_HOST", raising=False)
    seen: list[list[str]] = []

    def fake_run(cmd: list[str], **kwargs: object) -> object:
        seen.append(list(cmd))

        class Result:
            returncode = 1
            stdout = ""
            stderr = ""

        return Result()

    monkeypatch.setattr(atlas_job.subprocess, "run", fake_run)
    with pytest.raises(ConnectionError, match="host_load failed"):
        atlas_job.SshHostAdapter().host_load("job-box")
    assert seen
    assert seen[0][0] == "ssh"
    assert "job-box" in seen[0]


def test_is_self_host_uses_canonical_tokens(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_JOB_SELF_HOST", "vps")
    assert atlas_job.is_self_host("hramatka") is True
    assert atlas_job.is_self_host("vps") is True
    assert atlas_job.is_self_host("job-box") is False
