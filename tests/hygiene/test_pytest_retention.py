"""Behavioral retention proofs on disposable roots, including live idle owners."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.common import task_scratch
from scripts.common.scratch import scratch_scan_roots
from scripts.hygiene import pytest_retention, tmp_sweep

pytest_plugins = ("pytester",)
REPO = Path(__file__).resolve().parents[2]


@pytest.fixture
def area(tmp_path, monkeypatch):
    root = tmp_path / "managed"
    root.mkdir(mode=0o700)
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    temp = tmp_path / "system-temp"
    temp.mkdir()
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(root))
    monkeypatch.setattr(pytest_retention, "scratch_scan_roots", lambda: [root])
    monkeypatch.setattr(tmp_sweep, "SYSTEM_TEMP_AREAS", (temp,))
    monkeypatch.setattr(tmp_sweep, "process_snapshot", lambda: ([], True))
    monkeypatch.setattr(tmp_sweep, "registered_worktrees", lambda _: set())
    return root, dict(temp_root=temp, task_root=tasks, state_dir=tmp_path / "state", repo_root=REPO)


def completed(root: Path, count: int = 6) -> list[Path]:
    # Real ownership metadata and flocks, released by a different process that exits.
    result = subprocess.run(
        [sys.executable, "-c", """
import json, sys
from pathlib import Path
from scripts.common.task_scratch import allocate
paths = []
for index in range(int(sys.argv[2])):
    run = allocate('pytest', root=Path(sys.argv[1]) / 'pytest-runs')
    (run.payload_dir / 'payload').write_bytes(b'x' * 4096)
    paths.append(str(run.path))
    run.preserve()
print(json.dumps(paths))
""", str(root), str(count)],
        cwd=REPO, capture_output=True, text=True, check=True, timeout=30,
    )
    return [Path(path) for path in json.loads(result.stdout)]


@pytest.mark.parametrize("keep", [None, 1, 4])
def test_next_sweep_retains_newest_completed_runs_and_quarantines_rest(area, keep):
    root, args = area
    runs = completed(root)
    kwargs = {} if keep is None else {"pytest_keep": keep}
    expected_keep = 3 if keep is None else keep
    dry = tmp_sweep.sweep(**args, **kwargs)["pytest_retention"]
    assert dry["by_decision"] == {"would_reap": 6 - expected_keep, "preserve": expected_keep}
    assert all(path.exists() for path in runs)

    report = tmp_sweep.sweep(**args, apply=True, **kwargs)
    assert report["digest"] == tmp_sweep.plan_digest(report)
    assert [path for path in runs if path.exists()] == runs[-expected_keep:]
    retention = report["pytest_retention"]
    assert retention["by_decision"] == {"quarantined": 6 - expected_keep, "preserve": expected_keep}
    assert retention["quarantined_bytes"] > 0
    assert retention["errors"] == 0
    # The standard ledger restore works for pytest residue as for other scratch.
    entry = next(iter(tmp_sweep.Ledger(args["state_dir"]).entries()[0].values()))
    assert (entry.location / "scratch" / "payload").read_bytes() == b"x" * 4096
    assert tmp_sweep.restore(tmp_sweep.Ledger(args["state_dir"]), entry.ledger_id)["restored"] is True


def test_concurrent_idle_session_outlives_any_age_grace(area):
    root, args = area
    runs = completed(root)
    proc = subprocess.Popen(
        [sys.executable, "-c", """
import os, sys
from pathlib import Path
from scripts.common.task_scratch import allocate
run = allocate('pytest', root=Path(sys.argv[1]) / 'pytest-runs')
for path in run.path.rglob('*'):
    os.utime(path, (1, 1), follow_symlinks=False)
os.utime(run.path, (1, 1))
print(run.path, flush=True)
sys.stdin.read()
run.preserve()
""", str(root)], cwd=REPO, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
    )
    try:
        live = Path(proc.stdout.readline().strip())
        report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
        assert live.is_dir()
        assert next(row for row in report["rows"] if row["name"] == live.name)["reason"] == "in_use"
        assert [path for path in runs if path.exists()] == runs[-3:]
    finally:
        proc.communicate(timeout=10)
    assert proc.returncode == 0


@pytest.mark.parametrize("fault", [
    "missing_lock", "wrong_identity", "unknown_task", "incomplete", "symlink", "metadata_fifo", "lock_fifo",
])
def test_unproven_runs_are_exempt_from_retention(area, fault):
    root, args = area
    runs = completed(root)
    uncertain = runs[0]
    metadata = uncertain / "lease.json"
    lease = json.loads(metadata.read_text())
    if fault == "missing_lock":
        (uncertain / "lease.lock").unlink()
    elif fault == "wrong_identity":
        lease["dir"]["ino"] += 1
    elif fault == "unknown_task":
        lease["task_id"] = "other"
    elif fault == "incomplete":
        lease["state"] = "registered"
    elif fault == "metadata_fifo":
        metadata.unlink()
        os.mkfifo(metadata)
    elif fault == "lock_fifo":
        (uncertain / "lease.lock").unlink()
        os.mkfifo(uncertain / "lease.lock")
    elif fault == "symlink":
        destination = uncertain.with_name("relocated")
        uncertain.rename(destination)
        uncertain.symlink_to(destination, target_is_directory=True)
    if fault not in {"symlink", "metadata_fifo"}:
        metadata.write_text(json.dumps(lease))
    report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    assert (uncertain / "scratch" / "payload").read_bytes() == b"x" * 4096
    assert [path for path in runs[1:] if path.exists()] == runs[-3:]
    row = next(row for row in report["rows"] if row["name"] == uncertain.name)
    assert row["decision"] == "preserve"


@pytest.mark.parametrize("fault", ["relocate", "substitute", "lock_swap", "namespace_swap"])
def test_rename_boundary_refuses_changed_ownership(area, monkeypatch, fault):
    root, args = area
    runs = completed(root, 4)
    target = runs[0]
    original = tmp_sweep.quarantine_entry

    def intervene(path, *positional, **kwargs):
        if fault in {"relocate", "substitute"}:
            path.rename(path.with_name("relocated"))
            if fault == "substitute":
                path.mkdir()
                (path / "foreign").write_text("preserve me")
        elif fault == "lock_swap":
            (path / "lease.lock").rename(path / "old.lock")
            (path / "lease.lock").touch(mode=0o600)
        elif fault == "namespace_swap":
            path.parent.rename(path.parent.with_name("relocated"))
            path.parent.mkdir()
        return original(path, *positional, **kwargs)

    monkeypatch.setattr(tmp_sweep, "quarantine_entry", intervene)
    report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    row = next(row for row in report["rows"] if row["name"] == target.name)
    assert row["decision"] == "preserve"
    if fault in {"relocate", "substitute"}:
        assert (target.with_name("relocated") / "scratch" / "payload").read_bytes() == b"x" * 4096
    elif fault == "lock_swap":
        assert (target / "scratch" / "payload").read_bytes() == b"x" * 4096
    else:
        assert (target.parent.with_name("relocated") / target.name / "scratch" / "payload").exists()
    if fault == "substitute":
        assert (target / "foreign").read_text() == "preserve me"


def test_legacy_and_general_managed_scratch_stay_protected(area):
    root, args = area
    legacy = root / "pytest-legacy"
    legacy.mkdir()
    (legacy / "payload").write_text("unknown")
    unrelated = task_scratch.allocate("other", root=root)
    unrelated.preserve()
    report = tmp_sweep.sweep(**args, apply=True)
    assert legacy.is_dir() and unrelated.path.is_dir()
    assert report["pytest_retention"]["by_reason"] == {"legacy_ownership_unknown": 1}
    summary = tmp_sweep.summarize(report)
    assert "rows" not in summary["pytest_retention"]
    assert "pytest-legacy" not in json.dumps(summary)


@pytest.mark.parametrize("gate", ["process_unknown", "live_reference", "task_unknown", "task_reference", "worktree"])
def test_existing_sweeper_gates_also_protect_owned_pytest_runs(area, monkeypatch, gate):
    root, args = area
    runs = completed(root, 4)
    if gate == "process_unknown":
        monkeypatch.setattr(tmp_sweep, "process_snapshot", lambda: ([], False))
    elif gate == "live_reference":
        monkeypatch.setattr(tmp_sweep, "process_snapshot", lambda: ([(123, runs[0] / "scratch")], True))
    elif gate == "task_unknown":
        (args["task_root"] / "bad.json").write_text("invalid")
    elif gate == "task_reference":
        (args["task_root"] / "busy.json").write_text(json.dumps({
            "task_id": "busy", "status": "running", "runtime_tmp_root": str(runs[0]),
        }))
    else:
        monkeypatch.setattr(tmp_sweep, "registered_worktrees", lambda _: {runs[0]})
    report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    assert all(path.exists() for path in runs)
    expected = {
        "process_unknown": "liveness_unknown", "live_reference": "live_process",
        "task_unknown": "task_inventory_unknown", "task_reference": "task_reference", "worktree": "registered_worktree",
    }[gate]
    assert next(row for row in report["rows"] if row["name"] == runs[0].name)["reason"] == expected


@pytest.mark.parametrize("keep", [0, -1, True, 1.5])
def test_invalid_count_refuses_without_removal(area, keep):
    root, args = area
    runs = completed(root, 1)
    with pytest.raises(ValueError, match="positive integer"):
        tmp_sweep.sweep(**args, apply=True, pytest_keep=keep)
    assert (runs[0] / "scratch" / "payload").is_file()


def test_repeated_sweep_keeps_retention_and_uses_existing_purge_window(area, monkeypatch):
    root, args = area
    runs = completed(root)
    first = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    second = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    assert first["quarantine_held_entries"] == second["quarantine_held_entries"] == 3
    assert second["by_decision"] == {"preserve": 3}
    assert [path for path in runs if path.exists()] == runs[-3:]
    later = tmp_sweep.time.time() + 8 * 86400
    monkeypatch.setattr(tmp_sweep.time, "time", lambda: later)
    third = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    assert third["purged_entries"] == 3
    assert third["purged_bytes"] == first["quarantined_bytes"]
    assert third["quarantine_held_entries"] == 0
    assert third["remaining_runs"] == 3
    assert [path for path in runs if path.exists()] == runs[-3:]


def test_cli_applies_retention_count_and_reports_aggregate_exceptions(area, capsys):
    root, args = area
    runs = completed(root, 4)
    assert tmp_sweep.main([
        "--temp-root", str(args["temp_root"]), "--task-root", str(args["task_root"]),
        "--state-dir", str(args["state_dir"]), "--pytest-keep", "1", "--apply", "--summary",
    ]) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["pytest_retention"]["by_decision"] == {"quarantined": 3, "preserve": 1}
    assert summary["pytest_retention"]["remaining_runs"] == 1
    assert summary["pytest_retention"]["remaining_bytes"] > 0
    assert [path for path in runs if path.exists()] == runs[-1:]


def test_scan_confinement_excludes_other_managed_roots(area, monkeypatch, tmp_path):
    root, args = area
    runs = completed(root, 4)
    confined = tmp_path / "confined"
    confined.mkdir()
    monkeypatch.setattr(pytest_retention, "scratch_scan_roots", scratch_scan_roots)
    monkeypatch.setenv("LU_SCRATCH_SCAN_ROOT", str(confined))
    report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    assert report["runs"] == 0
    assert all(path.exists() for path in runs)
    monkeypatch.setenv("LU_SCRATCH_SCAN_ROOT", str(root))
    report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    assert report["by_decision"] == {"preserve": 3, "quarantined": 1}
    assert [path for path in runs if path.exists()] == runs[-3:]


def test_real_pytest_publishes_owned_run_and_respects_explicit_base(pytester, area):
    root, _args = area
    pytester.makeconftest(f'''
import sys
sys.path.insert(0, {str(REPO)!r})
pytest_plugins = ["scripts.common.pytest_scratch"]
''')
    pytester.makepyfile("def test_payload(tmp_path):\n    (tmp_path / 'payload').write_text('hello')\n")
    (root / "pytest-runs").mkdir(mode=0o775)
    (root / "pytest-runs").chmod(0o775)
    # Pytester's runner injects --basetemp, which intentionally opts out of ownership.
    result = subprocess.run(
        [sys.executable, "-c", "import os, pytest; os.umask(0o002); raise SystemExit(pytest.main(['-q', '-n', '2']))"],
        cwd=pytester.path, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 passed" in result.stdout
    assert (root / "pytest-runs").stat().st_mode & 0o777 == 0o700
    namespace = root / "pytest-runs" / "task-scratch"
    runs = list(namespace.iterdir())
    assert len(runs) == 1
    lease = json.loads((runs[0] / "lease.json").read_text())
    assert lease["state"] == "preserved" and lease["task_id"] == "pytest"
    assert (runs[0] / "scratch" / "base").is_dir()

    explicit = pytester.path / "gate-owned"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--basetemp", str(explicit)],
        cwd=pytester.path, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 passed" in result.stdout
    assert explicit.is_dir()
    assert list(namespace.iterdir()) == runs
