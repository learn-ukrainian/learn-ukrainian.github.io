"""delegate.py dispatch host admission, prompt liveness and peak RSS (#8645 part A).

Task records live under tmp_path. Memory and load come from a monkeypatched
probe; no test allocates memory, generates load, or spawns a worker.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import delegate
from scripts.fleet import capacity_pick
from scripts.orchestration import dispatch_admission, job_host_exec

_GIB = 1024**3


@pytest.fixture
def tasks_dir(tmp_path, monkeypatch):
    tasks = tmp_path / "tasks"
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(tmp_path / "scratch"))
    for name in (
        "_resolve_dirty_primary_checkout_error",
        "_resolve_primary_integrity_error",
    ):
        monkeypatch.setattr(delegate, name, lambda **_kwargs: None)
    for name in (
        "_warn_node_modules_integrity",
        "_warn_venv_integrity",
        "_warn_worktree_cleanup_integrity",
        "_warn_if_monitor_api_unreachable",
    ):
        monkeypatch.setattr(delegate, name, lambda: None)
    monkeypatch.setattr(
        delegate,
        "_sweep_runtime_tmp_orphans",
        lambda: {"leases_reaped": 0, "bytes_freed": 0, "errors": 0, "error_details": []},
    )
    monkeypatch.setattr(job_host_exec, "decide_dispatch_placement", lambda **_kwargs: ("local", "test", None))
    return tasks


def _running_record(tasks: Path, task_id: str, *, pid: int, mode: str = "workspace-write") -> Path:
    tasks.mkdir(parents=True, exist_ok=True)
    path = tasks / f"{task_id}.json"
    path.write_text(
        json.dumps(
            {
                "task_id": task_id,
                "status": "running",
                "mode": mode,
                "pid": pid,
                "run_nonce": f"nonce-{task_id}",
                "started_at": datetime.now(UTC).isoformat(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


def _dispatch_worktree(tasks: Path, name: str = "wt") -> Path:
    """An explicit ``--worktree`` inside the fixture primary's codex dispatch subtree (#8775)."""
    return tasks.parent / "primary" / ".worktrees" / "dispatch" / "codex" / name


def _live_danger_args(tasks: Path, task_id: str):

    _dispatch_worktree(tasks).mkdir(parents=True, exist_ok=True)
    return argparse.Namespace(
        agent="codex",
        task_id=task_id,
        prompt="test",
        prompt_file=None,
        mode="danger",
        model=None,
        cwd=None,
        worktree=str(_dispatch_worktree(tasks)),
        base="main",
        hard_timeout=3600,
        owned_path=["scripts/example.py"],
    )


def _stub_worktree(monkeypatch, tasks: Path):
    """A prepared worktree without git: live-dispatch tests stop at the admission lock or at Popen."""
    wt = _dispatch_worktree(tasks)
    primary = tasks.parent / "primary"
    (primary / ".git").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(delegate, "_REPO_ROOT", primary)
    monkeypatch.chdir(primary)
    monkeypatch.setattr(delegate, "_resolve_write_cwd_error", lambda **_kwargs: None)

    def run(cmd, **kwargs):
        # The creation inventory requests binary, NUL-delimited Git output;
        # other dispatch probes opt into text mode, just as subprocess does.
        text_mode = (
            kwargs.get("text") or kwargs.get("universal_newlines") or kwargs.get("encoding") or kwargs.get("errors")
        )
        output = "" if text_mode else b""
        return delegate.subprocess.CompletedProcess(cmd, 0, output, output)

    monkeypatch.setattr(delegate.subprocess, "run", run)
    monkeypatch.setattr(delegate, "_resolve_worktree_base_sha", lambda **_kwargs: "abc1234")
    monkeypatch.setattr(
        delegate,
        "_ensure_worktree",
        lambda **_kwargs: (wt, "codex/adm", {"base_sha": "abc1234", "layout": "dispatch"}),
    )
    monkeypatch.setattr(delegate, "_resolve_sha", lambda *_args, **_kwargs: "abc1234")
    # Git is stubbed, so branch authorship cannot be enumerated; these tests
    # cover host admission. Authoring-review admission has its own tests (#9739).
    monkeypatch.setattr(delegate, "_authoring_review_admission", lambda *_args, **_kwargs: None)


# --- #8717: admission runs before the worktree and holds the slot until the spawn ------------


# ``_stub_worktree`` replaces ``subprocess.run`` for delegate; the scratch repo needs the real one.


def test_capacity_pick_prints_the_admission_line(tmp_path, monkeypatch, capsys):
    from scripts.fleet import usage

    tasks = tmp_path / "tasks"
    _running_record(tasks, "busy", pid=515151)
    dead = _running_record(tasks, "gone", pid=424242)
    monkeypatch.setattr(dispatch_admission, "process_alive", lambda pid: pid == 515151)
    monkeypatch.setattr(dispatch_admission, "slice_usage_clause", lambda: None)
    monkeypatch.setattr(
        dispatch_admission.admission_shadow, "read_pressure",
        lambda _: {"cpu.some": {"avg10": None, "avg60": None}},
    )
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    monkeypatch.setattr(capacity_pick, "fetch_active_in_flight", lambda **_kwargs: {})
    monkeypatch.setattr(
        usage,
        "read_budget",
        lambda **_kwargs: {"agents": {}, "recommendation": {"warnings": []}, "diagnostics": {}},
    )

    assert capacity_pick.main([]) == 0
    assert capsys.readouterr().out.splitlines()[-1] == (
        "admission (write dispatch): would admit now | live write workers 1/2, "
        "MemAvailable 64.0 GiB (floor 8.5 GiB), load 0.00 per CPU (limit 1.00), "
        "lu.slice pool check skipped (test host), test-slot queue check skipped (test host), "
        "disk check skipped (test host), PSI shadow unknown (calibration only; "
        "unknown: test journal not configured; CPU ownership unknown, unattributed load unknown); "
        "1 record(s) dead pid, not counted: gone"
    )

    monkeypatch.setenv("DISPATCH_MAX_LIVE_WRITE_WORKERS", "1")
    assert capacity_pick.main(["--json"]) == 0
    admission = json.loads(capsys.readouterr().out)["admission"]
    assert admission["admitted"] is False
    assert admission["line"].startswith("admission (write dispatch): would REFUSE now: live write workers 1/1")
    # capacity_pick only reports; marking dead records crashed is dispatch's job.
    assert json.loads(dead.read_text(encoding="utf-8"))["status"] == "running"


def _full_disk(monkeypatch, *readings: float) -> dict[str, list]:
    """Disk readings in order (the last repeats); a fake reaper and alert publisher (#10776)."""
    seen: dict[str, list] = {"readings": list(readings), "reaper": [], "alerts": []}

    def probe():
        values = seen["readings"]
        used = values.pop(0) if len(values) > 1 else values[0]
        used_bytes = int(400 * _GIB * used / 100)
        return dispatch_admission.DiskProbe(used_bytes=used_bytes, free_bytes=400 * _GIB - used_bytes)

    def reaper(repo_root, _timeout_s=None):
        seen["reaper"].append(repo_root)
        return dispatch_admission.ReaperOutcome(ran=True, detail="reaper removed 0 worktree(s)")

    monkeypatch.setattr(dispatch_admission, "probe_disk", probe)
    monkeypatch.setattr(dispatch_admission, "run_disk_reaper", reaper)
    monkeypatch.setattr(dispatch_admission, "post_disk_alert", lambda body, _key: seen["alerts"].append(body))
    return seen


def test_capacity_pick_shows_the_disk_decision_without_reaping(tmp_path, monkeypatch, capsys):
    from scripts.fleet import usage

    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    monkeypatch.setattr(dispatch_admission, "slice_usage_clause", lambda: None)
    monkeypatch.setattr(
        dispatch_admission.admission_shadow, "read_pressure",
        lambda _: {"cpu.some": {"avg10": None, "avg60": None}},
    )
    monkeypatch.setattr(capacity_pick, "fetch_active_in_flight", lambda **_kwargs: {})
    monkeypatch.setattr(
        usage,
        "read_budget",
        lambda **_kwargs: {"agents": {}, "recommendation": {"warnings": []}, "diagnostics": {}},
    )
    disk = _full_disk(monkeypatch, 82.0)

    assert capacity_pick.main([]) == 0
    assert capsys.readouterr().out.splitlines()[-1].endswith(
        "disk 82.0% used, 72.0 GiB free (reap at 85%, refuse at 90%, alert at 75%) [epics alert posted], "
        "PSI shadow unknown (calibration only; unknown: test journal not configured; "
        "CPU ownership unknown, unattributed load unknown)"
    )

    disk["readings"] = [91.0]
    assert capacity_pick.main(["--json"]) == 0
    admission = json.loads(capsys.readouterr().out)["admission"]
    assert admission["admitted"] is False
    assert admission["line"].startswith(
        "admission (write dispatch): would REFUSE now: disk 91.0% used, 36.0 GiB free on the .worktrees "
        "filesystem is at or above the refuse threshold of 90% (DISPATCH_DISK_REFUSE_USED_PERCENT=90); "
        "reaper not run in this check"
    )
    assert admission["disk_used_percent"] == 91.0
    assert admission["disk_free_gib"] == 36.0
    assert disk["reaper"] == []  # capacity_pick only reports
    assert len(disk["alerts"]) == 1  # rate-limited across both calls


# --- Round 3 (#10776): a disk refusal is a hard stop in both gates; reuse skips the guard -----------


# --- #10799: a refused dispatch costs almost no CPU ---------------------------------------------

_OVERLOADED = dispatch_admission.HostProbe(mem_available_bytes=1 * _GIB, load1=40.0, cpu_count=8, proc_available=True)


@pytest.mark.parametrize(
    "probe",
    [
        dispatch_admission.HostProbe(mem_available_bytes=64 * _GIB, load1=1.0, cpu_count=8, proc_available=True),
        dispatch_admission.HostProbe(mem_available_bytes=None, load1=None, cpu_count=8, proc_available=False),
    ],
    ids=["healthy", "unknown"],
)
def test_precheck_admits_nothing_and_refuses_only_failures(probe, monkeypatch):
    monkeypatch.setattr(dispatch_admission, "probe_host", lambda: probe)
    monkeypatch.setenv("DISPATCH_MAX_LIVE_WRITE_WORKERS", "0")  # the cap is the full admission's check

    assert dispatch_admission.precheck("workspace-write") is None


def test_precheck_exempts_read_only_and_rejects_invalid_thresholds(monkeypatch):
    monkeypatch.setattr(dispatch_admission, "probe_host", lambda: _OVERLOADED)
    assert dispatch_admission.precheck("read-only") is None
    monkeypatch.setenv("DISPATCH_MAX_LOAD_PER_CPU", "lots")
    with pytest.raises(ValueError, match="DISPATCH_MAX_LOAD_PER_CPU='lots' is not a number"):
        dispatch_admission.precheck("danger")
