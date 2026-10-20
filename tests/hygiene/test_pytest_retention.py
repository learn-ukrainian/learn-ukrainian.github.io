"""Behavioral retention proofs on disposable roots, including live idle owners."""

from __future__ import annotations

import fcntl
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.common import pytest_scratch, task_scratch
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


def completed(root: Path, count: int = 6, *, namespace: str = task_scratch.NAMESPACE_DIRNAME) -> list[Path]:
    # Real ownership metadata and flocks, released by a different process that exits.
    result = subprocess.run(
        [sys.executable, "-c", """
import json, sys
from pathlib import Path
from scripts.common.task_scratch import allocate
paths = []
for index in range(int(sys.argv[2])):
    run = allocate('pytest', root=Path(sys.argv[1]) / 'pytest-runs', namespace_dirname=sys.argv[3])
    (run.payload_dir / 'payload').write_bytes(b'x' * 4096)
    paths.append(str(run.path))
    run.preserve()
print(json.dumps(paths))
""", str(root), str(count), namespace],
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


def test_preserved_runs_with_released_locks_keep_live_owner(area):
    root, args = area
    proc = subprocess.Popen(
        [sys.executable, "-c", """
import json, sys
from pathlib import Path
from scripts.common.task_scratch import allocate
paths = []
for _ in range(5):
    run = allocate('pytest', root=Path(sys.argv[1]) / 'pytest-runs')
    (run.payload_dir / 'payload').write_text('live owner')
    run.preserve()
    paths.append(str(run.path))
print(json.dumps(paths), flush=True)
sys.stdin.read()
""", str(root)], cwd=REPO, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
    )
    try:
        runs = [Path(path) for path in json.loads(proc.stdout.readline())]
        for path in runs:
            with (path / "lease.lock").open("r+") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert proc.poll() is None
        report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
        assert report["by_decision"] == {"preserve": 5}
        assert report["by_reason"] == {"owner_alive": 5}
        assert all(row["decision"] == "preserve" and row["reason"] == "owner_alive" for row in report["rows"])
        assert all((path / "scratch" / "payload").read_text() == "live owner" for path in runs)
        assert proc.poll() is None
    finally:
        proc.communicate(timeout=10)
    assert proc.returncode == 0


@pytest.mark.parametrize("fault", [
    "missing_lock", "wrong_identity", "unknown_task", "incomplete", "symlink", "metadata_fifo", "lock_fifo",
    "wrong_uid", "metadata_directory", "lock_directory",
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
    elif fault == "wrong_uid":
        lease["uid"] += 1
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
    elif fault == "metadata_directory":
        metadata.unlink()
        metadata.mkdir()
    elif fault == "lock_directory":
        (uncertain / "lease.lock").unlink()
        (uncertain / "lease.lock").mkdir()
    elif fault == "symlink":
        destination = uncertain.with_name("relocated")
        uncertain.rename(destination)
        uncertain.symlink_to(destination, target_is_directory=True)
    if fault not in {"symlink", "metadata_fifo", "metadata_directory"}:
        metadata.write_text(json.dumps(lease))
    report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    assert (uncertain / "scratch" / "payload").read_bytes() == b"x" * 4096
    assert [path for path in runs[1:] if path.exists()] == runs[-3:]
    row = next(row for row in report["rows"] if row["name"] == uncertain.name)
    assert row["decision"] == "preserve"
    if fault in {"wrong_uid", "metadata_fifo", "lock_fifo", "metadata_directory", "lock_directory"}:
        assert row["reason"] == "ownership_unknown"


def test_nonprivate_namespace_preserves_all_runs(area):
    root, args = area
    runs = completed(root, 5)
    runs[0].parent.chmod(0o755)
    report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    assert report["by_decision"] == {"preserve": 1}
    assert report["by_reason"] == {"namespace_untrusted": 1}
    assert report["errors"] == 1
    assert all((path / "scratch" / "payload").is_file() for path in runs)


def test_postrename_recheck_preserves_when_owner_probe_becomes_unknown(area, monkeypatch):
    root, args = area
    runs = completed(root, 4)
    target = runs[0]
    before = tmp_sweep.tree_fingerprint(target)
    original = tmp_sweep.rename_noreplace
    unchanged = []

    def intervene(src_fd, src, dst_fd, dst):
        original(src_fd, src, dst_fd, dst)
        if src_fd != dst_fd and src == target.name and not target.exists():
            quarantined = next(target.parent.glob(f"{tmp_sweep.QUARANTINE_PREFIX}*/{target.name}"))
            unchanged.append(tmp_sweep.tree_fingerprint(quarantined) == before)
            monkeypatch.setattr(task_scratch, "owner_alive", lambda *_: None)

    monkeypatch.setattr(tmp_sweep, "rename_noreplace", intervene)
    report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    assert unchanged == [True]
    row = next(row for row in report["rows"] if row["name"] == target.name)
    assert row["decision"] == "preserve"
    assert row["reason"] == "owner_liveness_unknown"
    assert tmp_sweep.tree_fingerprint(target) == before
    assert all((path / "scratch" / "payload").is_file() for path in runs)


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


def test_invalid_scan_root_still_reports_applied_sweep(area, monkeypatch, capsys):
    root, args = area
    runs = completed(root, 4)
    candidate = args["temp_root"] / "unowned-scratch"
    candidate.mkdir()
    (candidate / "payload").write_text("recoverable")
    now = tmp_sweep.time.time() + 3 * 86400
    monkeypatch.setattr(tmp_sweep.time, "time", lambda: now)
    monkeypatch.setattr(tmp_sweep, "protected_roots", lambda: {root})
    monkeypatch.setattr(pytest_retention, "scratch_scan_roots", scratch_scan_roots)
    monkeypatch.setenv("LU_SCRATCH_SCAN_ROOT", "relative-is-invalid")
    assert tmp_sweep.main([
        "--temp-root", str(args["temp_root"]), "--task-root", str(args["task_root"]),
        "--state-dir", str(args["state_dir"]), "--unattributed-scratch", "--apply", "--summary",
    ]) == 1
    output = capsys.readouterr()
    assert output.err == ""
    summary = json.loads(output.out)
    assert summary["mode"] == "apply"
    assert summary["errors"] == 1
    assert summary["by_decision"] == {"quarantined": 1}
    assert summary["quarantined_entries"] == 1
    assert summary["bytes_quarantined"] > 0
    assert summary["pytest_retention"]["errors"] == 1
    assert summary["pytest_retention"]["by_reason"] == {"scan_root_invalid": 1}
    assert not candidate.exists()
    entry = next(iter(tmp_sweep.Ledger(args["state_dir"]).entries()[0].values()))
    assert (entry.location / "payload").read_text() == "recoverable"
    assert all(path.is_dir() for path in runs)


def test_real_pytest_publishes_owned_run_and_respects_explicit_base(pytester, area):
    root, _args = area
    pytester.makeconftest(f'''
import sys
sys.path.insert(0, {str(REPO)!r})
pytest_plugins = ["scripts.common.pytest_scratch"]
''')
    pytester.makepyfile(f'''
import os
import tempfile
from pathlib import Path

def test_payload(tmp_path):
    runs = list(Path({str(root / "pytest-runs" / "runs")!r}).iterdir())
    assert len(runs) == 1
    expected = runs[0] / "scratch"
    root = Path(tempfile.gettempdir())
    assert root == expected
    assert os.environ["TMPDIR"] == str(expected)
    assert tmp_path.is_relative_to(root)
    with tempfile.NamedTemporaryFile() as ordinary:
        assert Path(ordinary.name).parent == root
    (tmp_path / "payload").write_text("hello")
''')
    (root / "pytest-runs").mkdir(mode=0o775)
    (root / "pytest-runs").chmod(0o775)
    caller_temp = pytester.path / "caller-temp"
    caller_temp.mkdir()
    env = {"LU_SCRATCH_ROOT": str(root)}
    # Pytester's runner injects --basetemp, which intentionally opts out of ownership.
    result = subprocess.run(
        [sys.executable, "-c", "import os, pytest; os.umask(0o002); raise SystemExit(pytest.main(['-q', '-n', '2']))"],
        cwd=pytester.path, capture_output=True, text=True, timeout=30,
        env={**env, "TMPDIR": str(caller_temp)},
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 passed" in result.stdout
    assert (root / "pytest-runs").stat().st_mode & 0o777 == 0o700
    namespace = root / "pytest-runs" / "runs"
    runs = list(namespace.iterdir())
    assert len(runs) == 1
    lease = json.loads((runs[0] / "lease.json").read_text())
    assert lease["state"] == "preserved" and lease["task_id"] == "pytest"
    assert (runs[0] / "scratch" / "base").is_dir()
    # These prefixes are recognized by secret scanners even in emitted paths.
    for path in (runs[0] / "scratch" / "base").rglob("payload"):
        relative = path.relative_to(root).as_posix().lower()
        for prefix in ("sk-", "ghp_", "github_pat_", "xoxb-", "xoxp-", "akia"):
            assert prefix not in relative
    assert list((runs[0] / "scratch" / "base").rglob("payload"))

    explicit = pytester.path / "gate-owned"
    pytester.makepyfile(f'''
import os
from pathlib import Path

def test_payload(tmp_path):
    assert "TMPDIR" not in os.environ
    assert tmp_path.is_relative_to(Path({str(explicit)!r}))
    (tmp_path / "payload").write_text("hello")
''')
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--basetemp", str(explicit)],
        cwd=pytester.path, capture_output=True, text=True, timeout=30,
        env=env,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 passed" in result.stdout
    assert explicit.is_dir()
    assert list(namespace.iterdir()) == runs


def test_retention_counts_legacy_and_neutral_namespaces_together(area):
    root, args = area
    legacy = completed(root, 4)
    neutral = completed(root, 4, namespace="runs")
    report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    assert report["errors"] == 0
    assert report["by_decision"] == {"quarantined": 5, "preserve": 3}
    assert [path for path in legacy + neutral if path.exists()] == neutral[-3:]
    assert report["quarantine_held_entries"] == 5
    again = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    assert again["quarantine_held_entries"] == 5
    assert again["by_decision"] == {"preserve": 3}


def test_missing_pytest_namespaces_do_not_probe_processes(area, monkeypatch):
    _root, args = area
    monkeypatch.setattr(tmp_sweep, "process_snapshot", lambda: pytest.fail("no owned pytest namespace to inspect"))
    report = pytest_retention.sweep_pytest_runs(
        keep=3, apply=False, ledger=tmp_sweep.Ledger(args["state_dir"]), run_id="missing",
        task_root=args["task_root"], digest_limit=1024, quarantine_s=86400, repo_root=REPO,
    )
    assert report["rows"] == []
    assert report["errors"] == 0


@pytest.mark.parametrize("namespace", ["../escape", "a/b", "", ".", "/absolute"])
def test_namespace_override_rejects_noncomponents(tmp_path, namespace):
    with pytest.raises(task_scratch.TaskScratchError, match="invalid scratch namespace"):
        task_scratch.allocate("pytest", root=tmp_path, namespace_dirname=namespace)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("previous_env", [None, "caller-temp"])
def test_pytest_restores_temp_environment_and_cache(tmp_path, monkeypatch, previous_env):
    import tempfile
    from types import SimpleNamespace

    root = tmp_path / "managed"
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(root))
    if previous_env is None:
        monkeypatch.delenv("TMPDIR", raising=False)
    else:
        monkeypatch.setenv("TMPDIR", previous_env)
    previous = tempfile.tempdir
    cleanups = []
    config = SimpleNamespace(option=SimpleNamespace(basetemp=None), add_cleanup=cleanups.append)
    try:
        pytest_scratch.pytest_configure(config)
        relative = Path(config.option.basetemp).relative_to(root).as_posix().lower()
        for prefix in ("sk-", "ghp_", "github_pat_", "xoxb-", "xoxp-", "akia"):
            assert prefix not in relative
        assert Path(config.option.basetemp).parent == Path(tempfile.gettempdir())
        assert os.environ["TMPDIR"] == tempfile.gettempdir()
    finally:
        for cleanup in reversed(cleanups):
            cleanup()
    assert os.environ.get("TMPDIR") == previous_env
    assert tempfile.tempdir == previous


def test_relative_shard_file_resolves_from_checkout_after_chdir(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from tests import conftest as suite

    checkout = tmp_path / "checkout"
    shards = checkout / "ci-artifacts"
    shards.mkdir(parents=True)
    relative = "ci-artifacts/pytest-shard-2-files.txt"
    (checkout / relative).write_text("tests/test_allowed.py\n")
    child = tmp_path / "child"
    child.mkdir()
    (child / "ci-artifacts").mkdir()
    (child / relative).write_text("tests/test_decoy.py\n")
    monkeypatch.chdir(child)
    monkeypatch.setattr(suite, "_REPO_ROOT", checkout)
    monkeypatch.setenv(suite.LU_PYTEST_SHARD_FILES_ENV_VAR, relative)
    suite._load_shard_allowlist.cache_clear()
    try:
        assert suite._load_shard_allowlist() == frozenset({"tests/test_allowed.py"})
        config = SimpleNamespace(rootpath=checkout)
        assert suite.pytest_ignore_collect(checkout / "tests/test_allowed.py", config) is False
        assert suite.pytest_ignore_collect(checkout / "tests/test_other.py", config) is True
        (checkout / relative).unlink()
        suite._load_shard_allowlist.cache_clear()
        with pytest.raises(RuntimeError, match="unreadable"):
            suite._load_shard_allowlist()
    finally:
        suite._load_shard_allowlist.cache_clear()


def test_generated_child_suite_does_not_inherit_checkout_shard(pytester, monkeypatch):
    pytester.makeconftest(f'''
import sys
sys.path.insert(0, {str(REPO)!r})
pytest_plugins = ["tests.conftest"]
''')
    pytester.makepyfile("def test_child(): pass")
    monkeypatch.setenv("LU_PYTEST_SHARD_FILES", "ci-artifacts/absent-shard.txt")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"], cwd=pytester.path,
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 passed" in result.stdout
