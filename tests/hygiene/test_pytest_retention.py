"""Behavioral retention proofs for inactive pytest scratch on disposable roots (#10831, #11297)."""

from __future__ import annotations

import fcntl
import json
import math
import os
import resource
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.common import pytest_scratch, task_scratch
from scripts.common.scratch import scratch_scan_roots
from scripts.hygiene import pytest_retention, tmp_sweep

pytest_plugins = ("pytester",)
REPO = Path(__file__).resolve().parents[2]
HOUR = 3600.0


@pytest.fixture
def area(tmp_path, monkeypatch):
    root = tmp_path / "managed"
    root.mkdir(mode=0o700)
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    temp = tmp_path / "system-temp"
    temp.mkdir()
    proc = tmp_path / "proc"
    proc.mkdir()
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(root))
    monkeypatch.setattr(pytest_retention, "scratch_scan_roots", lambda: [root])
    # An empty process table: a lease owner is judged against the real one only where a test says so.
    monkeypatch.setattr(pytest_retention, "PROC_ROOT", proc)
    monkeypatch.setattr(tmp_sweep, "SYSTEM_TEMP_AREAS", (temp,))
    monkeypatch.setattr(tmp_sweep, "process_snapshot", lambda: ([], True))
    monkeypatch.setattr(tmp_sweep, "registered_worktrees", lambda _: set())
    return root, dict(temp_root=temp, task_root=tasks, state_dir=tmp_path / "state", repo_root=REPO)


def namespace(root: Path, name: str = pytest_scratch.RUNS_DIRNAME) -> Path:
    path = root / pytest_scratch.NAMESPACE / name
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    (root / pytest_scratch.NAMESPACE).chmod(0o700)
    path.chmod(0o700)
    return path


def unowned(root: Path, name: str, *, ns: str = pytest_scratch.RUNS_DIRNAME) -> Path:
    """A run folder with no ownership record or lock at all."""
    path = namespace(root, ns) / name
    (path / "scratch" / "base").mkdir(parents=True)
    (path / "scratch" / "base" / "payload").write_bytes(b"x" * 8192)
    return path


def malformed(root: Path, name: str, *, ns: str = pytest_scratch.RUNS_DIRNAME) -> Path:
    path = unowned(root, name, ns=ns)
    (path / "lease.json").write_text("{not json")
    (path / "lease.lock").touch(mode=0o600)
    return path


def completed(root: Path, count: int = 2, *, ns: str = task_scratch.NAMESPACE_DIRNAME) -> list[Path]:
    # Real ownership metadata and flocks, released by a different process that exits.
    namespace(root, ns)
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
""", str(root), str(count), ns],
        cwd=REPO, capture_output=True, text=True, check=True, timeout=30,
    )
    return [Path(path) for path in json.loads(result.stdout)]


def later(monkeypatch, seconds: float, *, base: float | None = None) -> float:
    now = (tmp_sweep.time.time() if base is None else base) + seconds
    monkeypatch.setattr(tmp_sweep.time, "time", lambda: now)
    return now


def reaped_pid() -> tuple[int, int]:
    """A real pid and start time that are provably dead once the child exits (#11409)."""
    from scripts.common.acp_runtime_lock import process_start_time

    # The child stays alive until communicate() closes its stdin, so its start time is always readable.
    child = subprocess.Popen(
        [sys.executable, "-c", "import os, sys; print(os.getpid(), flush=True); sys.stdin.read()"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
    )
    try:
        pid = int(child.stdout.readline())
        start = process_start_time(pid)
        assert start is not None
    finally:
        child.communicate(timeout=10)
    assert child.returncode == 0
    return pid, start


def live_pid() -> tuple[subprocess.Popen, int, int]:
    """A real live child with its recorded start time; the caller stops it."""
    from scripts.common.acp_runtime_lock import process_start_time

    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    start = process_start_time(child.pid)
    assert start is not None
    return child, child.pid, start


def write_lease(
    run: Path, *, pid: int, start_time: int | None, boot_id: str | None, state: str = "preserved",
) -> None:
    """A real lease file in the run's own format, plus the lock the owner would have created."""
    info = run.stat()
    payload = {
        "schema_version": task_scratch.LEASE_SCHEMA_VERSION,
        "kind": task_scratch.NAMESPACE_DIRNAME,
        "task_id": "pytest",
        "invocation_id": run.name,
        "uid": os.geteuid(),
        "dir": {"dev": info.st_dev, "ino": info.st_ino},
        "owner": {"pid": pid, "start_time": start_time, "boot_id": boot_id},
        "child": None,
        "state": state,
        "created_at": 0.0,
    }
    (run / "lease.json").write_text(json.dumps(payload))
    (run / "lease.lock").touch(mode=0o600)


def leased(
    root: Path, name: str, *, pid: int, start_time: int | None, boot_id: str | None,
    ns: str = pytest_scratch.RUNS_DIRNAME, size: int = 8192,
) -> Path:
    run = unowned(root, name, ns=ns)
    (run / "scratch" / "base" / "payload").write_bytes(b"x" * size)
    write_lease(run, pid=pid, start_time=start_time, boot_id=boot_id)
    return run


def current_boot() -> str:
    boot = task_scratch.current_boot_id()
    assert boot is not None
    return boot


def tree_state(*roots: Path) -> list[tuple]:
    """Every node's identity and timestamps except atime: a dry run must leave all of it alone."""
    state = []
    for root in roots:
        for path in sorted([root, *root.rglob("*")]):
            info = path.lstat()
            state.append((str(path), info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns, info.st_ctime_ns))
    return state


def allocated(path: Path) -> int:
    seen, total = set(), 0
    for node in [path, *path.rglob("*")]:
        info = node.lstat()
        if (info.st_dev, info.st_ino) not in seen:
            seen.add((info.st_dev, info.st_ino))
            total += info.st_blocks * 512
    return total


def row_for(report: dict, path: Path) -> dict:
    return next(row for row in report["rows"] if row["name"] == path.name)


def test_old_unowned_malformed_and_completed_runs_dry_run_then_delete(area, monkeypatch):
    root, args = area
    runs = [
        unowned(root, "unowned"), malformed(root, "malformed"), *completed(root, 1, ns=pytest_scratch.RUNS_DIRNAME),
        unowned(root, "legacy-unowned", ns=task_scratch.NAMESPACE_DIRNAME), *completed(root, 2),
    ]
    later(monkeypatch, 2 * HOUR + 1)
    before = tree_state(root, args["temp_root"])
    sizes = {path.name: allocated(path) for path in runs}

    dry = tmp_sweep.sweep(**args)["pytest_retention"]
    assert tree_state(root, args["temp_root"]) == before  # zero effects
    assert not args["state_dir"].exists()
    assert {row["name"]: row["decision"] for row in dry["rows"]} == dict.fromkeys(sizes, "would_delete")
    assert {row["reason"] for row in dry["rows"]} == {"inactive_pytest_scratch"}
    assert dry["would_delete_bytes"] == sum(sizes.values()) > 0
    assert dry["deleted_bytes"] == 0 and dry["errors"] == 0

    report = tmp_sweep.sweep(**args, apply=True)
    retention = report["pytest_retention"]
    assert report["digest"] == tmp_sweep.plan_digest(report)
    assert {row["name"]: row["decision"] for row in retention["rows"]} == dict.fromkeys(sizes, "deleted")
    assert retention["deleted_entries"] == len(runs)
    assert retention["deleted_bytes"] == sum(sizes.values()) == dry["would_delete_bytes"]
    assert retention["errors"] == 0 and retention["remaining_runs"] == 0
    assert not any(path.exists() for path in runs)
    # No quarantine, no custody: nothing recoverable is left behind or recorded.
    assert not [path for path in root.rglob("*") if path.name.startswith(tmp_sweep.QUARANTINE_PREFIX)]
    assert tmp_sweep.Ledger(args["state_dir"]).entries()[0] == {}


def test_deeply_nested_lease_is_malformed_and_later_runs_are_still_swept(area, monkeypatch):
    """Defect class #11413: a parser failure on one lease aborted the whole sweep."""
    root, args = area
    nested = malformed(root, "a-nested")
    depth = (task_scratch.LEASE_MAX_BYTES - 2) // 2
    (nested / "lease.json").write_text("[" * depth + "]" * depth)
    following = malformed(root, "z-following")
    later(monkeypatch, 2 * HOUR + 1)

    report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    # The nested lease records no owner, like any malformed lease, so the lock
    # and idle time decide; the run after it is still processed.
    for run in (nested, following):
        assert (row_for(report, run)["decision"], row_for(report, run)["reason"]) == (
            "deleted", "inactive_pytest_scratch",
        )
        assert not run.exists()
    assert report["errors"] == 0


def test_young_runs_are_retained_until_strictly_past_two_hours(area, monkeypatch):
    root, args = area
    run = unowned(root, "boundary")
    _bytes, _newest, changed, problem = tmp_sweep.tree_facts(run)
    assert problem is None
    assert row_for(tmp_sweep.sweep(**args, apply=True)["pytest_retention"], run)["reason"] == "too_young"
    # Exactly two hours after the newest change, in float arithmetic, is still young.
    boundary = changed + 2 * HOUR
    while boundary - changed > 2 * HOUR:
        boundary = math.nextafter(boundary, 0)
    while boundary - changed < 2 * HOUR:
        boundary = math.nextafter(boundary, math.inf)
    later(monkeypatch, 0, base=boundary)
    report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    assert row_for(report, run)["reason"] == "too_young" and run.is_dir()
    later(monkeypatch, 0, base=math.nextafter(boundary, math.inf))
    assert row_for(tmp_sweep.sweep(**args)["pytest_retention"], run)["decision"] == "would_delete"
    assert row_for(tmp_sweep.sweep(**args, apply=True)["pytest_retention"], run)["decision"] == "deleted"


def test_recently_extracted_old_mtime_files_keep_the_folder_young(area, monkeypatch):
    root, args = area
    run = unowned(root, "extracted")
    for path in [run, *run.rglob("*")]:
        os.utime(path, (1, 1), follow_symlinks=False)
    assert max(path.lstat().st_mtime for path in [run, *run.rglob("*")]) == 1
    later(monkeypatch, HOUR)
    row = row_for(tmp_sweep.sweep(**args, apply=True)["pytest_retention"], run)
    assert (row["decision"], row["reason"]) == ("preserve", "too_young")
    assert (run / "scratch" / "base" / "payload").is_file()


def test_held_run_lock_preserves_the_run(area, monkeypatch):
    root, args = area
    run = completed(root, 1)[0]
    later(monkeypatch, 3 * HOUR)
    with (run / "lease.lock").open("r+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    assert row_for(report, run)["reason"] == "in_use" and run.is_dir()


@pytest.mark.parametrize("cohort", ["young96", "eligible96", "cross_namespace50"])
def test_run_locks_do_not_exhaust_descriptors_across_repeated_sweeps(area, cohort):
    """Retained and disposed locks must not starve later runs or namespaces (#11386)."""
    root, args = area
    if cohort == "cross_namespace50":
        runs = [malformed(root, f"run-{index:03d}", ns=ns)
                for ns in (pytest_scratch.RUNS_DIRNAME, task_scratch.NAMESPACE_DIRNAME) for index in range(25)]
    else:
        runs = [malformed(root, f"run-{index:03d}") for index in range(96)]
    before = tree_state(root)
    expected_bytes = sum(allocated(run) for run in runs)
    parent_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
    result = subprocess.run(
        [sys.executable, "-c", """
import json, os, resource, sys, time
from pathlib import Path
from scripts.hygiene import pytest_retention as retention, tmp_sweep
from scripts.hygiene.tmp_sweep_ledger import Ledger
root, state, tasks, proc = map(Path, sys.argv[1:5])
cohort = sys.argv[5]
runs = [root / relative for relative in json.loads(sys.argv[6])]
real_time = time.time
if cohort != 'young96':
    tmp_sweep.time.time = lambda: real_time() + 3 * 3600
retention.scratch_scan_roots = lambda: [root]
retention.PROC_ROOT = proc
tmp_sweep.registered_worktrees = lambda _: set()
def no_delete(*args, **kwargs):
    raise AssertionError('young runs must never enter deletion')
if cohort == 'young96':
    retention._delete = no_delete
real_lock = retention._lock
def fd_open(fd):
    try:
        os.fstat(fd)
        return True
    except OSError:
        return False
fd_count = lambda: sum(fd_open(fd) for fd in range(64))
peak = fd_count()
lock_fd_counts = set()
def measured_lock(fd):
    global peak
    result = real_lock(fd)
    count = fd_count()
    lock_fd_counts.add(count)
    peak = max(peak, count)
    return result
retention._lock = measured_lock
soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
assert soft >= 64
resource.setrlimit(resource.RLIMIT_NOFILE, (64, hard))
reports = []
for index in range(3):
    if index and cohort != 'young96':
        for run in runs:
            (run / 'scratch' / 'base').mkdir(parents=True)
            (run / 'scratch' / 'base' / 'payload').write_bytes(b'x' * 8192)
            (run / 'lease.json').write_text('{not json')
            (run / 'lease.lock').touch(mode=0o600)
    start = fd_count()
    lock_fd_counts.clear()
    report = retention.sweep_pytest_runs(
        apply=True, ledger=Ledger(state), run_id=f'bounded-{index}', task_root=tasks,
        quarantine_s=7 * 86400, repo_root=Path.cwd(),
    )
    reports.append(dict(
        reasons=report['by_reason'], decisions=report['by_decision'], errors=report['errors'],
        protected_bytes=report['protected_bytes'], deleted=report['deleted_entries'],
        unmeasured=report['unmeasured_entries'], bytes_complete=report['bytes_complete'],
        remaining=report['remaining_runs'], deleted_bytes=report['deleted_bytes'],
        fd_start=start, fd_end=fd_count(), fd_peak=peak, lock_fd_counts=sorted(lock_fd_counts),
    ))
print(json.dumps(reports))
""", str(root), str(args["state_dir"]), str(args["task_root"]), str(root.parent / "proc"), cohort,
         json.dumps([str(run.relative_to(root)) for run in runs])],
        cwd=REPO, capture_output=True, text=True, check=True, timeout=60,
    )
    reports = json.loads(result.stdout)
    print("low-FD repeated sweeps:", result.stdout.strip())
    assert resource.getrlimit(resource.RLIMIT_NOFILE) == parent_limit
    for report in reports:
        if cohort == "young96":
            assert report["reasons"] == {"too_young": 96}
            assert report["decisions"] == {"preserve": 96}
            assert report["deleted"] == report["deleted_bytes"] == 0
            assert report["protected_bytes"] == expected_bytes
            assert report["remaining"] == 96
        else:
            count = 50 if cohort == "cross_namespace50" else 96
            assert report["reasons"] == {"inactive_pytest_scratch": count}
            assert report["decisions"] == {"deleted": count}
            assert report["deleted"] == count
            assert report["deleted_bytes"] == expected_bytes
            assert report["remaining"] == report["protected_bytes"] == 0
        assert report["errors"] == report["unmeasured"] == 0
        assert report["bytes_complete"] is True
        assert report["fd_start"] == report["fd_end"]
        assert report["fd_peak"] < 64
        assert len(report["lock_fd_counts"]) == 1  # no accumulation as earlier runs are disposed
    if cohort == "young96":
        assert tree_state(root) == before
    else:
        assert all(not run.exists() for run in runs)


@pytest.mark.parametrize("rejection", ["too_young", "tree_unknown", "mount_point", "scan_error"])
def test_rejected_lock_is_released_before_the_next_eligible_run(area, monkeypatch, rejection):
    """Preserve and exception paths must release their lock before inspecting the next run."""
    root, args = area
    rejected, eligible = malformed(root, "a-rejected"), malformed(root, "z-eligible")
    now = later(monkeypatch, 3 * HOUR)
    if rejection == "mount_point":
        mounts = task_scratch.mount_points()
        monkeypatch.setattr(tmp_sweep, "mount_points", lambda: mounts | {str(rejected / "scratch")})
    real_fingerprint, real_facts = tmp_sweep.tree_fingerprint, tmp_sweep.tree_facts

    def fingerprint(path, **kwargs):
        return None if path == rejected and rejection == "tree_unknown" else real_fingerprint(path, **kwargs)

    def facts(path, **kwargs):
        if path == rejected and rejection == "scan_error":
            raise OSError(5, "inspection failed after locking")
        return real_facts(path, **kwargs)

    real_classify = pytest_retention._classify

    def classify(name, *positional, **kwargs):
        if name == rejected.name and rejection == "too_young":
            kwargs["now"] = now - 3 * HOUR
        if name == eligible.name:
            with (rejected / "lease.lock").open("r+") as contender:
                fcntl.flock(contender, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return real_classify(name, *positional, **kwargs)

    monkeypatch.setattr(tmp_sweep, "tree_fingerprint", fingerprint)
    monkeypatch.setattr(tmp_sweep, "tree_facts", facts)
    monkeypatch.setattr(pytest_retention, "_classify", classify)
    report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    assert (row_for(report, rejected)["decision"], row_for(report, rejected)["reason"]) == ("preserve", rejection)
    assert row_for(report, eligible)["decision"] == "deleted"
    assert rejected.is_dir() and not eligible.exists()
    assert report["errors"] == (1 if rejection == "scan_error" else 0)


@pytest.mark.parametrize("outcome", ["deleted", "recent_write", "delete_refused", "partial_failure"])
@pytest.mark.parametrize("next_ns", [pytest_scratch.RUNS_DIRNAME, task_scratch.NAMESPACE_DIRNAME])
def test_eligible_lock_covers_rename_recheck_delete_and_return(area, monkeypatch, outcome, next_ns):
    """Early lock release must not admit a competing owner during deletion or restoration."""
    root, args = area
    run = malformed(root, "locked")
    following = malformed(root, "z-following", ns=next_ns)
    later(monkeypatch, 3 * HOUR)
    phases = []
    with (run / "lease.lock").open("r+") as contender:
        def locked(phase):
            with pytest.raises(BlockingIOError):
                fcntl.flock(contender, fcntl.LOCK_EX | fcntl.LOCK_NB)
            phases.append(phase)

        def renamed(held):
            locked("rename")
            if outcome == "recent_write":
                (held / "new-output").write_text("fresh")

        _after_rename(monkeypatch, run, renamed)
        real_recheck, real_return = pytest_retention._recheck, pytest_retention._return
        real_classify = pytest_retention._classify
        real_reap = tmp_sweep.reap_attributed_temp

        def classify(name, *positional, **kwargs):
            if name == following.name:
                # The previous disposition is complete before another run or
                # namespace is inspected, even if the previous run was restored.
                fcntl.flock(contender, fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(contender, fcntl.LOCK_UN)
                phases.append("next_candidate")
            return real_classify(name, *positional, **kwargs)

        def recheck(*positional):
            if positional[0].name == run.name:
                locked("recheck")
            return real_recheck(*positional)

        def restore(*positional):
            locked("before_return")
            result = real_return(*positional)
            locked("after_return")
            return result

        def reap(path, **kwargs):
            if path.name != run.name:
                return real_reap(path, **kwargs)
            locked("delete")
            if outcome == "partial_failure":
                (path / "scratch" / "base" / "payload").unlink()
            if outcome in {"delete_refused", "partial_failure"}:
                raise OSError(13, "remover refused")
            return real_reap(path, **kwargs)

        monkeypatch.setattr(pytest_retention, "_recheck", recheck)
        monkeypatch.setattr(pytest_retention, "_classify", classify)
        monkeypatch.setattr(pytest_retention, "_return", restore)
        monkeypatch.setattr(tmp_sweep, "reap_attributed_temp", reap)
        report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
        fcntl.flock(contender, fcntl.LOCK_EX | fcntl.LOCK_NB)
    row = row_for(report, run)
    if outcome == "deleted":
        assert row["decision"] == "deleted" and not run.exists()
        assert phases == ["rename", "recheck", "delete", "next_candidate"]
    else:
        assert (row["decision"], row["reason"]) == (
            "preserve", "recent_write" if outcome == "recent_write" else "delete_refused",
        )
        assert phases == ["rename", "recheck", *([] if outcome == "recent_write" else ["delete"]),
                          "before_return", "after_return", "next_candidate"]
        assert run.is_dir()
        if outcome == "partial_failure":
            assert not (run / "scratch" / "base" / "payload").exists()
            assert (run / "lease.json").read_text() == "{not json"
        else:
            assert (run / "scratch" / "base" / "payload").read_bytes() == b"x" * 8192
    assert report["errors"] == (1 if outcome in {"delete_refused", "partial_failure"} else 0)
    assert row_for(report, following)["decision"] == "deleted" and not following.exists()
    assert report["unmeasured_entries"] == (0 if outcome == "deleted" else 1)
    assert report["protected_bytes_complete"] is (outcome == "deleted")


@pytest.mark.parametrize("failure", ["in_use", "lock_unknown"])
def test_summary_keeps_lock_failures_visible_beside_measured_protected_bytes(area, monkeypatch, failure):
    """Lock failures must remain counted even when their tree bytes could not be classified."""
    root, args = area
    young, uncertain = malformed(root, "young"), malformed(root, "uncertain")
    expected_bytes = allocated(young)
    real_open = os.open
    identity = uncertain.stat().st_ino

    def open_lock(path, flags, *positional, **kwargs):
        if (failure == "lock_unknown" and path == "lease.lock" and "dir_fd" in kwargs
                and os.fstat(kwargs["dir_fd"]).st_ino == identity):
            raise PermissionError(13, "unreadable lock")
        return real_open(path, flags, *positional, **kwargs)

    monkeypatch.setattr(pytest_retention.os, "open", open_lock)
    with (uncertain / "lease.lock").open("r+") as contender:
        if failure == "in_use":
            fcntl.flock(contender, fcntl.LOCK_EX | fcntl.LOCK_NB)
        report = tmp_sweep.sweep(**args, apply=True)
    summary = tmp_sweep.summarize(report)["pytest_retention"]
    assert summary["by_reason"] == {"too_young": 1, failure: 1}
    assert summary["by_decision"] == {"preserve": 2}
    assert summary["protected_bytes"] == summary["remaining_bytes"] == expected_bytes
    assert summary["unmeasured_entries"] == summary["protected_unmeasured_entries"] == 1
    assert summary["remaining_unmeasured_entries"] == 1
    assert summary["bytes_complete"] is False
    assert summary["protected_bytes_complete"] is summary["remaining_bytes_complete"] is False
    assert summary["deleted_entries"] == summary["deleted_bytes"] == 0
    assert row_for(report["pytest_retention"], uncertain)["reason"] == failure
    assert row_for(report["pytest_retention"], uncertain)["bytes"] is None
    assert young.is_dir() and uncertain.is_dir()


def test_real_descriptor_exhaustion_is_an_error_and_preserves_runs(area):
    """EMFILE on the run lock must not masquerade as a free lock or measured zero bytes."""
    root, args = area
    run = malformed(root, "preserved")
    parent_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
    result = subprocess.run(
        [sys.executable, "-c", """
import json, os, resource, sys, time
from pathlib import Path
from scripts.hygiene import pytest_retention as retention, tmp_sweep
from scripts.hygiene.tmp_sweep_ledger import Ledger
root, state, tasks, proc = map(Path, sys.argv[1:5])
retention.scratch_scan_roots = lambda: [root]
retention.PROC_ROOT = proc
tmp_sweep.registered_worktrees = lambda _: set()
real_time = time.time
tmp_sweep.time.time = lambda: real_time() + 3 * 3600
held = []
def exhaust():
    while True:
        try:
            held.append(os.open(os.devnull, os.O_RDONLY))
        except OSError as error:
            assert error.errno == 24
            return
def release():
    for fd in held:
        os.close(fd)
    held.clear()
real_lock = retention._lock
def lock(fd):
    exhaust()
    try:
        return real_lock(fd)
    finally:
        release()
retention._lock = lock
resource.setrlimit(resource.RLIMIT_NOFILE, (64, resource.getrlimit(resource.RLIMIT_NOFILE)[1]))
report = retention.sweep_pytest_runs(
    apply=True, ledger=Ledger(state), run_id='emfile', task_root=tasks,
    quarantine_s=7 * 86400, repo_root=Path.cwd(),
)
print(json.dumps(report))
""", str(root), str(args["state_dir"]), str(args["task_root"]), str(root.parent / "proc")],
        cwd=REPO, capture_output=True, text=True, check=True, timeout=60,
    )
    report = json.loads(result.stdout)
    print("real EMFILE", result.stdout.strip())
    assert resource.getrlimit(resource.RLIMIT_NOFILE) == parent_limit
    assert report["by_reason"] == {"descriptor_exhausted": 1}
    assert report["by_decision"] == {"preserve": 1}
    assert report["errors"] == report["descriptor_exhaustion_entries"] == 1
    assert report["deleted_entries"] == 0
    assert report["unmeasured_entries"] == report["protected_unmeasured_entries"] == 1
    assert report["protected_bytes_complete"] is False
    assert report["rows"][0]["bytes"] is None
    assert (run / "scratch" / "base" / "payload").read_bytes() == b"x" * 8192


@pytest.mark.parametrize("output", ["--summary", "--json", "table"])
def test_cli_publishes_unmeasured_busy_bytes_without_claiming_a_complete_total(area, capsys, output):
    """Every CLI output must expose unknown busy-run bytes while preserving numeric subtotal compatibility."""
    root, args = area
    busy = malformed(root, "busy")
    with (busy / "lease.lock").open("r+") as contender:
        fcntl.flock(contender, fcntl.LOCK_EX | fcntl.LOCK_NB)
        flags = ["--temp-root", str(args["temp_root"]), "--task-root", str(args["task_root"]),
                 "--state-dir", str(args["state_dir"]), "--apply"]
        assert tmp_sweep.main(flags + ([] if output == "table" else [output])) == 0
    rendered = capsys.readouterr().out
    if output == "table":
        summary = json.loads(rendered.split("pytest_retention=", 1)[1])
        assert "| None |" in rendered
    else:
        summary = json.loads(rendered)["pytest_retention"]
        if output == "--json":
            assert summary["rows"][0]["bytes"] is None
    assert summary["by_reason"] == {"in_use": 1}
    assert summary["protected_bytes"] == summary["remaining_bytes"] == 0  # measured subtotal only
    assert summary["protected_bytes_complete"] is summary["remaining_bytes_complete"] is False
    assert summary["protected_unmeasured_entries"] == summary["remaining_unmeasured_entries"] == 1
    assert (busy / "scratch" / "base" / "payload").read_bytes() == b"x" * 8192


@pytest.mark.parametrize("phase", ["root", "namespace", "classify", "quarantine"])
def test_descriptor_failure_does_not_duplicate_or_underreport_candidate_rows(area, monkeypatch, phase):
    """A failed directory open must report exhaustion once and never leave a would-delete receipt."""
    root, args = area
    run = malformed(root, "kept")
    later(monkeypatch, 3 * HOUR)
    real_private, real_classify = pytest_retention._open_private, pytest_retention._classify

    def private(path, *positional, **kwargs):
        if (phase == "root" and path == root) or (phase == "namespace" and path == run.parent):
            raise OSError(24, "descriptor limit")
        return real_private(path, *positional, **kwargs)

    def classify(*positional, **kwargs):
        if phase == "classify":
            raise OSError(24, "descriptor limit")
        return real_classify(*positional, **kwargs)

    def quarantine(*positional):
        raise OSError(24, "descriptor limit")

    monkeypatch.setattr(pytest_retention, "_open_private", private)
    monkeypatch.setattr(pytest_retention, "_classify", classify)
    if phase == "quarantine":
        monkeypatch.setattr(tmp_sweep, "open_quarantine", quarantine)
    report = tmp_sweep.sweep(**args, apply=True)
    summary = report["pytest_retention"]
    assert summary["by_reason"] == {"descriptor_exhausted": 1}
    assert summary["by_decision"] == {"preserve": 1}
    assert summary["runs"] == summary["errors"] == report["errors"] == 1
    assert summary["unmeasured_entries"] == 1
    assert summary["protected_bytes_complete"] is summary["remaining_bytes_complete"] is False
    assert summary["rows"][0]["bytes"] is None
    assert (run / "scratch" / "base" / "payload").read_bytes() == b"x" * 8192
    with (run / "lease.lock").open("r+") as contender:
        fcntl.flock(contender, fcntl.LOCK_EX | fcntl.LOCK_NB)


@pytest.mark.parametrize("kind", ["unlocked_lock", "unreadable_lock", "lock_fifo", "lock_symlink"])
def test_lock_files_are_used_where_available_but_never_required(area, monkeypatch, tmp_path, kind):
    root, args = area
    run = unowned(root, "locks")
    lock = run / "lease.lock"
    outside = tmp_path / "outside.lock"
    outside.write_text("outside")
    if kind == "unlocked_lock":
        lock.touch(mode=0o600)
    elif kind == "unreadable_lock":
        lock.touch(mode=0o000)
    elif kind == "lock_fifo":
        os.mkfifo(lock)
    else:
        lock.symlink_to(outside)
    later(monkeypatch, 3 * HOUR)
    row = row_for(tmp_sweep.sweep(**args, apply=True)["pytest_retention"], run)
    if kind == "unreadable_lock" and os.geteuid() != 0:
        assert (row["decision"], row["reason"]) == ("preserve", "lock_unknown")
        assert run.is_dir()
    else:
        assert row["decision"] == "deleted" and not run.exists()
    assert outside.read_text() == "outside"


def _after_rename(monkeypatch, run: Path, action):
    """Run ``action(held_path)`` right after the run moves aside, before its recheck."""
    original = tmp_sweep.rename_noreplace
    calls = []

    def intervene(src_fd, src, dst_fd, dst):
        original(src_fd, src, dst_fd, dst)
        if src == run.name and not run.exists() and not calls:
            calls.append(True)
            held = next(run.parent.glob(f"{tmp_sweep.QUARANTINE_PREFIX}*/{run.name}"))
            action(held)

    monkeypatch.setattr(tmp_sweep, "rename_noreplace", intervene)
    return calls


@pytest.mark.parametrize("race", ["write", "replaced"])
def test_post_rename_recheck_returns_changed_runs(area, monkeypatch, race):
    root, args = area
    run = unowned(root, "raced")
    later(monkeypatch, 3 * HOUR)
    identity = run.stat().st_ino

    def act(held: Path) -> None:
        (held / "scratch" / "new-output").write_text("fresh")

    if race == "replaced":
        original = tmp_sweep.rename_noreplace
        calls = []

        def swap_before_rename(src_fd, src, dst_fd, dst):
            # After the pre-rename identity check, before the rename itself.
            if src == run.name and not calls:
                calls.append(True)
                run.rename(run.with_name("moved-away"))
                run.mkdir()
                (run / "impostor").write_text("keep")
            return original(src_fd, src, dst_fd, dst)

        monkeypatch.setattr(tmp_sweep, "rename_noreplace", swap_before_rename)
    else:
        calls = _after_rename(monkeypatch, run, act)
    report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    assert calls == [True]
    row = row_for(report, run)
    assert row["decision"] == "preserve"
    assert row["reason"] == {"write": "recent_write", "replaced": "identity_changed"}[race]
    if race == "replaced":
        assert (run / "impostor").read_text() == "keep"
        assert (run.with_name("moved-away") / "scratch" / "base" / "payload").is_file()
    else:
        assert run.stat().st_ino == identity
        assert (run / "scratch" / "base" / "payload").read_bytes() == b"x" * 8192
    assert not [path for path in run.parent.iterdir() if path.name.startswith(tmp_sweep.QUARANTINE_PREFIX)]


def test_occupied_name_keeps_returned_run_for_next_recovery(area, monkeypatch):
    root, args = area
    run = unowned(root, "occupied")
    real_time, real_rename = tmp_sweep.time.time, tmp_sweep.rename_noreplace
    later(monkeypatch, 3 * HOUR)

    def act(held: Path) -> None:
        (held / "scratch" / "late").write_text("write")
        run.mkdir()

    _after_rename(monkeypatch, run, act)
    report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    row = row_for(report, run)
    assert (row["decision"], row["reason"], row["found"]) == ("preserve", "restore_blocked", "recent_write")
    assert report["errors"] == 1
    held = next(run.parent.glob(f"{tmp_sweep.QUARANTINE_PREFIX}*/{run.name}"))
    assert (held / "scratch" / "late").read_text() == "write"
    run.rmdir()
    monkeypatch.setattr(tmp_sweep, "rename_noreplace", real_rename)
    monkeypatch.setattr(tmp_sweep.time, "time", real_time)
    recovered = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    assert (run / "scratch" / "late").read_text() == "write"
    # The rename that returned it is a fresh change, so it is young again.
    assert row_for(recovered, run)["reason"] == "too_young"


@pytest.mark.parametrize("change", ["replaced", "vanished", "namespace_swapped"])
def test_change_between_proof_and_rename_is_never_moved(area, monkeypatch, change):
    root, args = area
    run = unowned(root, "between")
    ns = run.parent
    later(monkeypatch, 3 * HOUR)
    real_delete = pytest_retention._delete

    def intervene(candidates, namespace, ns_fd, **kwargs):
        if change == "replaced":
            run.rename(ns.with_name("moved-away"))
            run.mkdir()
            (run / "impostor").write_text("keep")
        elif change == "vanished":
            run.rename(ns.with_name("moved-away"))
        else:
            ns.rename(ns.with_name("old-namespace"))
            ns.mkdir(mode=0o700)
        return real_delete(candidates, namespace, ns_fd, **kwargs)

    monkeypatch.setattr(pytest_retention, "_delete", intervene)
    report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    assert (row_for(report, run)["decision"], row_for(report, run)["reason"]) == ("preserve", "identity_changed")
    if change == "replaced":
        assert (run / "impostor").read_text() == "keep"
    if change == "namespace_swapped":
        assert (ns.with_name("old-namespace") / run.name / "scratch" / "base" / "payload").is_file()
    else:
        assert (ns.with_name("moved-away") / "scratch" / "base" / "payload").is_file()


def test_namespace_swapped_after_rename_returns_through_descriptors(area, monkeypatch):
    root, args = area
    run = unowned(root, "swap-after")
    ns = run.parent
    later(monkeypatch, 3 * HOUR)

    def act(_held: Path) -> None:
        ns.rename(ns.with_name("old-namespace"))
        ns.mkdir(mode=0o700)

    _after_rename(monkeypatch, run, act)
    report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    assert row_for(report, run)["reason"] == "identity_changed"
    # The return rename follows the held descriptors, into the real (moved) namespace.
    assert (ns.with_name("old-namespace") / run.name / "scratch" / "base" / "payload").is_file()
    assert list(ns.iterdir()) == []


def test_refused_rename_and_unreadable_tree_preserve_with_reasons(area, monkeypatch):
    root, args = area
    refused = unowned(root, "refused")
    unreadable = unowned(root, "unreadable")
    later(monkeypatch, 3 * HOUR)
    real_rename, real_fingerprint = tmp_sweep.rename_noreplace, tmp_sweep.tree_fingerprint

    def rename(src_fd, src, dst_fd, dst):
        if src == refused.name:
            raise OSError(13, "refused")
        return real_rename(src_fd, src, dst_fd, dst)

    monkeypatch.setattr(tmp_sweep, "rename_noreplace", rename)
    monkeypatch.setattr(
        tmp_sweep, "tree_fingerprint",
        lambda path, **kwargs: None if path == unreadable else real_fingerprint(path, **kwargs),
    )
    report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    assert (row_for(report, refused)["reason"], row_for(report, refused)["error"]) == ("rename_refused", "EACCES")
    assert row_for(report, unreadable)["reason"] == "tree_unknown"
    assert report["errors"] == 1
    assert refused.is_dir() and unreadable.is_dir()


def test_entry_vanishing_during_scan_is_a_reported_error(area, monkeypatch):
    root, args = area
    run = unowned(root, "present")
    later(monkeypatch, 3 * HOUR)
    real_listdir = os.listdir
    monkeypatch.setattr(
        pytest_retention.os, "listdir",
        lambda target: [*real_listdir(target), "ghost"] if isinstance(target, int) else real_listdir(target),
    )
    report = tmp_sweep.sweep(**args)["pytest_retention"]
    ghost = next(row for row in report["rows"] if row["name"] == "ghost")
    assert (ghost["reason"], ghost["error"]) == ("scan_error", "ENOENT")
    assert row_for(report, run)["decision"] == "would_delete"


def test_remover_refusal_returns_the_run(area, monkeypatch):
    root, args = area
    run = unowned(root, "mounted-later")
    later(monkeypatch, 3 * HOUR)
    real = task_scratch.mount_points

    def mount_appears():
        mounts = real()
        held = list(run.parent.glob(f"{tmp_sweep.QUARANTINE_PREFIX}*/{run.name}"))
        return mounts | {str(held[0] / "scratch")} if held and mounts is not None else mounts

    monkeypatch.setattr(task_scratch, "mount_points", mount_appears)
    report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    row = row_for(report, run)
    assert (row["decision"], row["reason"], row["error"]) == ("preserve", "delete_refused", "ContainmentError")
    assert (run / "scratch" / "base" / "payload").is_file()
    assert report["errors"] == 1


@pytest.mark.parametrize("problem", ["mount_point", "hardlinked_content", "special_file", "git_metadata"])
def test_only_a_mount_inside_keeps_an_abandoned_run(area, monkeypatch, tmp_path, problem):
    """A run's contents are pytest's own scratch: links, FIFOs and repositories in it keep nothing (DISK-1109)."""
    root, args = area
    run = unowned(root, "unsafe")
    if problem == "mount_point":
        mounts = task_scratch.mount_points()
        monkeypatch.setattr(tmp_sweep, "mount_points", lambda: mounts | {str(run / "scratch")})
    elif problem == "hardlinked_content":
        os.link(run / "scratch" / "base" / "payload", tmp_path / "outside-link")
    elif problem == "special_file":
        os.mkfifo(run / "scratch" / "fifo")
    else:
        (run / "scratch" / ".git").mkdir()
    later(monkeypatch, 3 * HOUR)
    row = row_for(tmp_sweep.sweep(**args, apply=True)["pytest_retention"], run)
    if problem == "mount_point":
        assert (row["decision"], row["reason"]) == ("preserve", problem)
        assert (run / "scratch" / "base" / "payload").is_file()
    else:
        assert (row["decision"], row["reason"]) == ("deleted", "inactive_pytest_scratch")
        assert not run.exists()
    if problem == "hardlinked_content":
        assert (tmp_path / "outside-link").read_bytes() == b"x" * 8192


def test_symlinks_never_lead_outside_the_namespace(area, monkeypatch, tmp_path):
    root, args = area
    outside = tmp_path / "outside"
    (outside / "keep").mkdir(parents=True)
    (outside / "keep" / "data").write_text("outside data")
    ns = namespace(root)
    (ns / "linked-run").symlink_to(outside, target_is_directory=True)
    (ns / "stray-file").write_text("not a folder")
    run = unowned(root, "inner-link")
    (run / "scratch" / "escape").symlink_to(outside / "keep", target_is_directory=True)
    later(monkeypatch, 3 * HOUR)
    report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    reasons = {row["name"]: (row["decision"], row["reason"]) for row in report["rows"]}
    assert reasons["linked-run"] == ("preserve", "symlink_or_not_directory")
    assert reasons["stray-file"] == ("preserve", "symlink_or_not_directory")
    assert reasons["inner-link"] == ("deleted", "inactive_pytest_scratch")
    assert (outside / "keep" / "data").read_text() == "outside data"
    assert (ns / "linked-run").is_symlink() and (ns / "stray-file").is_file()


def test_symlinked_or_shared_namespace_is_untrusted(area, monkeypatch, tmp_path):
    root, args = area
    outside = tmp_path / "elsewhere"
    run = unowned(root, "real")
    (root / pytest_scratch.NAMESPACE / pytest_scratch.RUNS_DIRNAME).rename(outside)
    (root / pytest_scratch.NAMESPACE / pytest_scratch.RUNS_DIRNAME).symlink_to(outside, target_is_directory=True)
    shared = unowned(root, "shared", ns=task_scratch.NAMESPACE_DIRNAME)
    shared.parent.chmod(0o755)
    later(monkeypatch, 3 * HOUR)
    report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    assert report["by_reason"] == {"namespace_untrusted": 2} and report["errors"] == 2
    assert (outside / run.name / "scratch" / "base" / "payload").is_file()
    assert (shared / "scratch" / "base" / "payload").is_file()


@pytest.mark.parametrize("worktrees,reason", [("registered", "registered_worktree"), (None, "git_registration_unknown")])
def test_worktree_registration_still_preserves(area, monkeypatch, worktrees, reason):
    root, args = area
    run = unowned(root, "worktree")
    registered = {run / "scratch"} if worktrees else None
    monkeypatch.setattr(tmp_sweep, "registered_worktrees", lambda _: registered)
    later(monkeypatch, 3 * HOUR)
    assert row_for(tmp_sweep.sweep(**args, apply=True)["pytest_retention"], run)["reason"] == reason


def test_crash_leftover_returns_to_its_name_and_waits_again(area, monkeypatch):
    root, args = area
    run = unowned(root, "crashed")
    holding = run.parent / (tmp_sweep.QUARANTINE_PREFIX + "deadbeef")
    holding.mkdir(mode=0o700)
    run.rename(holding / run.name)
    dry = tmp_sweep.sweep(**args)["pytest_retention"]
    assert dry["by_reason"] == {"quarantine_leftover": 1}
    assert dry["rows"][0]["bytes"] is None
    assert dry["unmeasured_entries"] == dry["protected_unmeasured_entries"] == 1
    assert dry["protected_bytes_complete"] is dry["remaining_bytes_complete"] is False
    report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    assert (run / "scratch" / "base" / "payload").is_file() and not holding.exists()
    assert row_for(report, run)["reason"] == "too_young"


def test_other_scratch_classes_keep_their_policy(area, monkeypatch):
    root, args = area
    legacy = root / "pytest-legacy"
    legacy.mkdir()
    (legacy / "payload").write_text("unknown")
    unrelated = task_scratch.allocate("other", root=root)
    unrelated.preserve()
    general = args["temp_root"] / "hand-made"
    general.mkdir()
    (general / "payload").write_text("recoverable")
    run = unowned(root, "pytest-old")
    monkeypatch.setattr(tmp_sweep, "protected_roots", lambda: {root})
    later(monkeypatch, 3 * 86400)
    report = tmp_sweep.sweep(**args, scratch=tmp_sweep.ScratchPolicy(), apply=True)
    assert legacy.is_dir() and unrelated.path.is_dir()
    assert report["pytest_retention"]["by_reason"] == {"legacy_ownership_unknown": 1, "inactive_pytest_scratch": 1}
    assert not run.exists()
    # The general class is still quarantined recoverably, not deleted.
    assert tmp_sweep.summarize(report)["by_decision"] == {"quarantined": 1}
    entry = next(iter(tmp_sweep.Ledger(args["state_dir"]).entries()[0].values()))
    assert (entry.location / "payload").read_text() == "recoverable"
    summary = tmp_sweep.summarize(report)
    assert "rows" not in summary["pytest_retention"]
    assert "pytest-legacy" not in json.dumps(summary) and "pytest-old" not in json.dumps(summary)


def test_nonprivate_namespace_preserves_all_runs(area, monkeypatch):
    root, args = area
    runs = completed(root, 3)
    runs[0].parent.chmod(0o755)
    later(monkeypatch, 3 * HOUR)
    report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    assert report["by_decision"] == {"preserve": 1}
    assert report["by_reason"] == {"namespace_untrusted": 1}
    assert report["errors"] == 1
    assert all((path / "scratch" / "payload").is_file() for path in runs)


def test_cli_summary_reports_deleted_bytes_without_names(area, monkeypatch, capsys):
    root, args = area
    runs = [unowned(root, "cli-one"), unowned(root, "cli-two")]
    expected = sum(allocated(path) for path in runs)
    later(monkeypatch, 3 * HOUR)
    flags = [
        "--temp-root", str(args["temp_root"]), "--task-root", str(args["task_root"]),
        "--state-dir", str(args["state_dir"]), "--summary",
    ]
    assert tmp_sweep.main(flags) == 0
    dry = json.loads(capsys.readouterr().out)["pytest_retention"]
    assert (dry["would_delete_entries"], dry["would_delete_bytes"]) == (2, expected)
    assert tmp_sweep.main([*flags, "--apply"]) == 0
    output = capsys.readouterr().out
    summary = json.loads(output)["pytest_retention"]
    assert (summary["deleted_entries"], summary["deleted_bytes"], summary["inactive_hours"]) == (2, expected, 2.0)
    assert "cli-one" not in output and not any(path.exists() for path in runs)
    with pytest.raises(SystemExit) as exc:
        tmp_sweep.main([*flags, "--pytest-keep", "3"])
    assert exc.value.code == 2


def test_scan_confinement_excludes_other_managed_roots(area, monkeypatch, tmp_path):
    root, args = area
    runs = [unowned(root, "confined-a"), unowned(root, "confined-b")]
    confined = tmp_path / "confined"
    confined.mkdir()
    later(monkeypatch, 3 * HOUR)
    monkeypatch.setattr(pytest_retention, "scratch_scan_roots", scratch_scan_roots)
    monkeypatch.setenv("LU_SCRATCH_SCAN_ROOT", str(confined))
    report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    assert report["runs"] == 0
    assert all(path.exists() for path in runs)
    monkeypatch.setenv("LU_SCRATCH_SCAN_ROOT", str(root))
    report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    assert report["by_decision"] == {"deleted": 2}


def test_invalid_scan_root_still_reports_applied_sweep(area, monkeypatch, capsys):
    root, args = area
    run = unowned(root, "kept")
    candidate = args["temp_root"] / "unowned-scratch"
    candidate.mkdir()
    (candidate / "payload").write_text("recoverable")
    later(monkeypatch, 3 * 86400)
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
    assert summary["pytest_retention"]["errors"] == 1
    assert summary["pytest_retention"]["by_reason"] == {"scan_root_invalid": 1}
    assert not candidate.exists() and run.is_dir()


def test_live_pytest_session_is_held_by_its_own_lock(area, monkeypatch):
    """A real running pytest owner holds its run lock, so its run is never taken."""
    root, args = area
    proc = subprocess.Popen(
        [sys.executable, "-c", """
import sys
from pathlib import Path
from scripts.common.task_scratch import allocate
run = allocate('pytest', root=Path(sys.argv[1]) / 'pytest-runs', namespace_dirname='runs')
print(run.path, flush=True)
sys.stdin.read()
run.preserve()
""", str(root)], cwd=REPO, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
    )
    try:
        live = Path(proc.stdout.readline().strip())
        later(monkeypatch, 3 * HOUR)
        row = row_for(tmp_sweep.sweep(**args, apply=True)["pytest_retention"], live)
        assert (row["decision"], row["reason"]) == ("preserve", "in_use")
        assert live.is_dir()
    finally:
        proc.communicate(timeout=10)
    assert proc.returncode == 0


@pytest.mark.parametrize("namespace_name", ["../escape", "a/b", "", ".", "/absolute"])
def test_namespace_override_rejects_noncomponents(tmp_path, namespace_name):
    with pytest.raises(task_scratch.TaskScratchError, match="invalid scratch namespace"):
        task_scratch.allocate("pytest", root=tmp_path, namespace_dirname=namespace_name)
    assert not list(tmp_path.iterdir())


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
    # The caller asks to keep the run, so what the session published can be inspected.
    result = subprocess.run(
        [sys.executable, "-c", "import os, pytest; os.umask(0o002); raise SystemExit(pytest.main(['-q', '-n', '2']))"],
        cwd=pytester.path, capture_output=True, text=True, timeout=30,
        env={**env, "TMPDIR": str(caller_temp), pytest_scratch.KEEP_ENV_VAR: "1"},
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 passed" in result.stdout
    assert stat.S_IMODE((root / "pytest-runs").stat().st_mode) == 0o700
    runs_dir = root / "pytest-runs" / "runs"
    runs = list(runs_dir.iterdir())
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
    assert list(runs_dir.iterdir()) == runs


@pytest.mark.parametrize(
    ("finish", "returncode", "keep"),
    [
        pytest.param("", pytest.ExitCode.OK, "", id="clean_pass_removes"),
        pytest.param("fail", pytest.ExitCode.TESTS_FAILED, "", id="failed_test_removes"),
        pytest.param("later_monitor_usage_error", pytest.ExitCode.USAGE_ERROR, "", id="later_hook_usage_error_removes"),
        # Pytest catches this exit and leaves the exit status at 0.
        pytest.param("hook_exit", pytest.ExitCode.OK, "", id="finish_hook_exit_removes"),
        pytest.param("fail", pytest.ExitCode.TESTS_FAILED, "1", id="keep_requested_keeps"),
    ],
)
def test_every_session_removes_its_run_unless_kept(pytester, area, finish, returncode, keep):
    """Defect class (DISK-1109): a failed or aborted session kept gigabytes of scratch with no owner to free it."""
    root, _args = area
    pytester.makeini("[pytest]\ntmp_path_retention_policy = failed\n")
    pytester.makeconftest(f'''
import os
import sys
import pytest
sys.path.insert(0, {str(REPO)!r})
pytest_plugins = ["scripts.common.pytest_scratch"]
FINISH = os.environ.get("SESSION_FINISH")

# Outermost, so this monitor is added last and wraps every other one.
@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtestloop(session):
    result = yield
    if FINISH == "later_monitor_usage_error":
        def after(outcome, hook_name, _impls, kwargs):
            if hook_name == "pytest_sessionfinish":
                raise pytest.UsageError("a later session-finish monitor failed")
        session.config.pluginmanager.add_hookcall_monitoring(lambda *_: None, after)
    return result

def pytest_sessionfinish(session):
    if FINISH == "hook_exit":
        pytest.exit("abort")
''')
    pytester.makepyfile(
        "import os\n"
        "def test_session(tmp_path):\n"
        "    (tmp_path / 'payload').write_text('hello')\n"
        "    assert os.environ.get('SESSION_FINISH') != 'fail'\n"
    )
    (root / "pytest-runs").mkdir(mode=0o700)
    runs_dir = root / "pytest-runs" / "runs"

    # Pytester's runner injects --basetemp, which intentionally opts out of ownership.
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
        cwd=pytester.path, capture_output=True, text=True, timeout=60,
        env={**os.environ, "LU_SCRATCH_ROOT": str(root), "SESSION_FINISH": finish,
             pytest_scratch.KEEP_ENV_VAR: keep},
    )
    assert result.returncode == returncode, result.stdout + result.stderr
    runs = list(runs_dir.iterdir())
    if keep:
        (run,) = runs
        assert list((run / "scratch" / "base").rglob("payload"))
    else:
        assert not runs


def use_real_proc(monkeypatch) -> None:
    """Judge lease liveness against the real process table, never a fabricated one."""
    monkeypatch.setattr(pytest_retention, "PROC_ROOT", Path("/proc"))


@pytest.mark.parametrize("ns", [pytest_scratch.RUNS_DIRNAME, task_scratch.NAMESPACE_DIRNAME])
@pytest.mark.parametrize("fixture_git", [False, True])
def test_reaped_lease_owner_is_reclaimed_without_all_process_visibility(area, monkeypatch, ns, fixture_git):
    """Defect class #11409: an unreadable unrelated process blocked every reclaim.

    The lease names a real child that has exited; the run lock is free and the
    tree is old, so the run must be deleted against the real process table,
    whatever else runs on the host. Fixture Git metadata inside does not keep it.
    """
    root, args = area
    pid, start = reaped_pid()
    run = leased(root, "dead-owner", pid=pid, start_time=start, boot_id=current_boot(), ns=ns)
    if fixture_git:
        subprocess.run(["git", "init", str(run / "scratch" / "fixture")], check=True, capture_output=True, timeout=10)
    expected_bytes = allocated(run)
    later(monkeypatch, 3 * HOUR)
    use_real_proc(monkeypatch)
    before = tree_state(root, args["temp_root"])
    dry = tmp_sweep.sweep(**args)["pytest_retention"]
    assert tree_state(root, args["temp_root"]) == before  # a dry run changes nothing
    assert (row_for(dry, run)["decision"], row_for(dry, run)["reason"]) == (
        "would_delete", "inactive_pytest_scratch",
    )
    assert dry["would_delete_bytes"] == expected_bytes > 0
    # No snapshot of other processes is taken; the lease proof admits the deletion.
    report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    row = row_for(report, run)
    assert row["decision"] == "deleted" and not run.exists()
    assert report["reclaimed_entries"] == 1
    assert report["reclaimed_bytes"] == report["deleted_bytes"] == expected_bytes > 0


@pytest.mark.parametrize("ns", [pytest_scratch.RUNS_DIRNAME, task_scratch.NAMESPACE_DIRNAME])
@pytest.mark.parametrize("case", [
    "remote_and_branch", "linked_worktrees_inside", "alternates_outside", "worktree_config", "hooks_path",
    "core_worktree_inside", "submodule_style_gitfile", "separate_git_dir_inside", "bare_repo_with_remote",
    "linked_worktree_config",
])
def test_self_contained_fixture_git_is_reclaimed_and_outside_is_untouched(area, monkeypatch, tmp_path, ns, case):
    """Fixture repositories as the test suite really makes them are reclaimed, and what they name survives.

    A remote, a branch tracking it, linked worktrees located in the same run, an
    alternates file naming an outside object store, a per-worktree config and a
    hooks path only describe the repository; deleting the run removes none of
    what they name (host measurement: these kept most of tens of GiB of dead runs).
    """
    root, args = area
    pid, start = reaped_pid()
    run = leased(root, "fixture-self-contained", pid=pid, start_time=start, boot_id=current_boot(), ns=ns)
    fixture = run / "scratch" / "fixture"
    outside = tmp_path / "external"
    (outside / "objects").mkdir(parents=True)
    (outside / "sentinel").write_text("keep outside")

    def git(*arguments, cwd=None):
        return subprocess.run(["git", *map(str, arguments)], check=True, capture_output=True, timeout=10, cwd=cwd)

    git("init", fixture)
    metadata = fixture / ".git"
    commit = ["-c", "user.name=Fixture", "-c", "user.email=fixture@example.test", "commit", "--allow-empty", "-m", "x"]
    if case == "remote_and_branch":
        git("remote", "add", "origin", "https://example.test/fixture.git", cwd=fixture)
        git("config", "branch.main.remote", "origin", cwd=fixture)
        git("config", "branch.main.merge", "refs/heads/main", cwd=fixture)
    elif case == "linked_worktrees_inside":
        git(*commit, cwd=fixture)
        git("worktree", "add", "--detach", run / "scratch" / "linked-a", cwd=fixture)
        git("worktree", "add", "--detach", fixture / "linked-b", cwd=fixture)
    elif case == "alternates_outside":
        (metadata / "objects" / "info").mkdir(exist_ok=True)
        (metadata / "objects" / "info" / "alternates").write_text(str(outside / "objects") + "\n")
    elif case == "worktree_config":
        git("config", "extensions.worktreeConfig", "true", cwd=fixture)
        git("config", "--file", metadata / "config.worktree", "core.sparseCheckout", "true")
    elif case == "hooks_path":
        git("config", "core.hooksPath", str(outside), cwd=fixture)
        git("config", "credential.helper", "store", cwd=fixture)
    elif case == "core_worktree_inside":
        git("config", "--file", metadata / "config", "core.worktree", "../checkout")
    elif case == "separate_git_dir_inside":
        shutil.rmtree(fixture)
        git("init", "--separate-git-dir", run / "scratch" / "meta", fixture)
        git(*commit, cwd=fixture)
        git("worktree", "add", "--detach", run / "scratch" / "linked", cwd=fixture)
    elif case == "bare_repo_with_remote":
        git("clone", "--bare", "--no-hardlinks", fixture, run / "scratch" / "canonical.git")
        git("--git-dir", run / "scratch" / "canonical.git", "remote", "add", "mirror", "https://example.test/x.git")
    elif case == "linked_worktree_config":
        git(*commit, cwd=fixture)
        git("config", "extensions.worktreeConfig", "true", cwd=fixture)
        git("worktree", "add", "--detach", run / "scratch" / "linked", cwd=fixture)
        (config,) = (metadata / "worktrees").glob("*/")
        git("config", "--file", config / "config.worktree", "core.sparseCheckout", "true")
    else:
        (fixture / "module").mkdir()
        (fixture / "module" / ".git").write_text("gitdir: ../.git/modules/module\n")
    later(monkeypatch, 3 * HOUR)
    before = tree_state(root, outside)
    dry = tmp_sweep.sweep(**args)["pytest_retention"]
    assert (row_for(dry, run)["decision"], row_for(dry, run)["reason"]) == ("would_delete", "inactive_pytest_scratch")
    assert tree_state(root, outside) == before
    report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    assert row_for(report, run)["decision"] == "deleted" and not run.exists()
    assert (outside / "sentinel").read_text() == "keep outside"
    assert (outside / "objects").is_dir()


@pytest.mark.parametrize("ns", [pytest_scratch.RUNS_DIRNAME, task_scratch.NAMESPACE_DIRNAME])
@pytest.mark.parametrize("fixture_git", [False, True])
def test_managed_ledger_purge_keeps_git_protection_and_retention_window(area, monkeypatch, ns, fixture_git):
    """Data-loss class: the fixture exception bypasses a retained entry's Git guard or recovery window."""
    root, args = area
    run = unowned(root, "retained", ns=ns)
    now = later(monkeypatch, 3 * HOUR)
    row = row_for(tmp_sweep.sweep(**args)["pytest_retention"], run)
    before = tmp_sweep.tree_fingerprint(run)
    ledger = tmp_sweep.Ledger(args["state_dir"])
    ns_fd = os.open(run.parent, tmp_sweep._DIR_FLAGS)
    try:
        with ledger.exclusive(wait=False):
            quarantine = tmp_sweep.open_quarantine(run.parent, ns_fd)
            try:
                result = tmp_sweep.quarantine_entry(
                    run, row, before, quarantine, root_fd=ns_fd, task_root=args["task_root"],
                    ledger=ledger, run_id="prior-policy", digest_limit=tmp_sweep.DEFAULT_DIGEST_LIMIT,
                )
                assert result["decision"] == "quarantined"
            finally:
                tmp_sweep.close_quarantine(quarantine, ns_fd)
    finally:
        os.close(ns_fd)
    [entry] = ledger.entries()[0].values()
    if fixture_git:
        subprocess.run(["git", "init", str(entry.location / "fixture")], check=True, capture_output=True, timeout=10)
    # Neither mode may purge inside the existing recovery window.
    for apply in (False, True):
        report = tmp_sweep.sweep(**args, apply=apply)["pytest_retention"]
        assert report["rows"] == [] and entry.location.exists()
    later(monkeypatch, 8 * 86400, base=now)
    before = tree_state(root)
    dry = tmp_sweep.sweep(**args)["pytest_retention"]
    assert tree_state(root) == before
    applied = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    if fixture_git:
        for report in (dry, applied):
            assert (row_for(report, run)["decision"], row_for(report, run)["reason"]) == (
                "preserve", "purge_git_metadata",
            )
            assert report["purged_entries"] == 0
        assert tree_state(root) == before
    else:
        assert row_for(dry, run)["decision"] == "would_purge"
        assert row_for(applied, run)["decision"] == "purged"
        assert not entry.location.exists()


def test_live_lease_owner_preserves_the_run(area, monkeypatch):
    """Defect class: a lease owner that is alive on the same boot was reclaimed."""
    root, args = area
    child, pid, start = live_pid()
    try:
        run = leased(root, "live-owner", pid=pid, start_time=start, boot_id=current_boot())
        later(monkeypatch, 3 * HOUR)
        use_real_proc(monkeypatch)
        row = row_for(tmp_sweep.sweep(**args, apply=True)["pytest_retention"], run)
        assert (row["decision"], row["reason"]) == ("preserve", "live_owner")
        assert (run / "scratch" / "base" / "payload").read_bytes() == b"x" * 8192
    finally:
        child.terminate()
        child.wait(timeout=10)


def test_held_lease_lock_preserves_a_dead_owner_run(area, monkeypatch):
    """Defect class: a competing writer won a race while its lock was held."""
    root, args = area
    pid, start = reaped_pid()
    run = leased(root, "lock-held", pid=pid, start_time=start, boot_id=current_boot())
    later(monkeypatch, 3 * HOUR)
    with (run / "lease.lock").open("r+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        row = row_for(tmp_sweep.sweep(**args, apply=True)["pytest_retention"], run)
    assert (row["decision"], row["reason"]) == ("preserve", "in_use")
    assert run.is_dir()


def test_tree_change_on_recheck_preserves_a_dead_owner_run(area, monkeypatch):
    """Defect class: a write after the proof but before deletion was not rechecked."""
    root, args = area
    pid, start = reaped_pid()
    run = leased(root, "recent-write", pid=pid, start_time=start, boot_id=current_boot())
    subprocess.run(["git", "init", str(run / "scratch" / "fixture")], check=True, capture_output=True, timeout=10)
    later(monkeypatch, 3 * HOUR)

    def write(held: Path) -> None:
        (held / "scratch" / "new-output").write_text("fresh")

    calls = _after_rename(monkeypatch, run, write)
    row = row_for(tmp_sweep.sweep(**args, apply=True)["pytest_retention"], run)
    assert calls == [True]
    assert (row["decision"], row["reason"]) == ("preserve", "recent_write")
    assert (run / "scratch" / "new-output").read_text() == "fresh"


def test_lease_from_a_different_boot_is_reclaimed(area, monkeypatch):
    """Defect class: a run from before a reboot was kept forever, though its owner cannot be alive."""
    root, args = area
    from scripts.common.acp_runtime_lock import process_start_time

    run = leased(
        root, "other-boot", pid=os.getpid(), start_time=process_start_time(os.getpid()),
        boot_id="00000000-0000-0000-0000-000000000000",
    )
    later(monkeypatch, 3 * HOUR)
    # The recorded pid is alive on this boot, so only the boot id can prove the owner dead.
    use_real_proc(monkeypatch)
    row = row_for(tmp_sweep.sweep(**args, apply=True)["pytest_retention"], run)
    assert (row["decision"], row["reason"]) == ("deleted", "inactive_pytest_scratch")
    assert not run.exists()


def test_unreadable_lease_is_kept(area, monkeypatch):
    """Defect class: metadata that could not be read was treated as no owner at all."""
    if os.geteuid() == 0:
        pytest.skip("root can read a mode-000 lease")
    root, args = area
    pid, start = reaped_pid()
    run = leased(root, "unreadable-lease", pid=pid, start_time=start, boot_id=current_boot())
    (run / "lease.json").chmod(0o000)
    later(monkeypatch, 3 * HOUR)
    row = row_for(tmp_sweep.sweep(**args, apply=True)["pytest_retention"], run)
    assert (row["decision"], row["reason"]) == ("preserve", "lease_unreadable")
    assert run.is_dir()


def test_reused_pid_with_a_different_start_time_is_reclaimed(area, monkeypatch):
    """Defect class: a recycled numeric pid kept an abandoned run alive forever."""
    root, args = area
    child, pid, start = live_pid()
    try:
        run = leased(root, "reused-pid", pid=pid, start_time=start + 1, boot_id=current_boot())
        later(monkeypatch, 3 * HOUR)
        use_real_proc(monkeypatch)
        row = row_for(tmp_sweep.sweep(**args)["pytest_retention"], run)
        assert (row["decision"], row["reason"]) == ("would_delete", "inactive_pytest_scratch")
        report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
        assert row_for(report, run)["decision"] == "deleted" and not run.exists()
    finally:
        child.terminate()
        child.wait(timeout=10)


def test_copied_dead_owner_lease_does_not_prove_abandonment(area, monkeypatch):
    """Data-loss class: a lease copied from another run vouched for this run's owner.

    Its dead owner says nothing about this run, so the run is preserved; the
    run the lease names is the control.
    """
    root, args = area
    pid, start = reaped_pid()
    source = leased(root, "lease-source", pid=pid, start_time=start, boot_id=current_boot())
    copied = unowned(root, "lease-copy")
    for name in ("lease.json", "lease.lock"):
        (copied / name).write_bytes((source / name).read_bytes())
    later(monkeypatch, 3 * HOUR)
    report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    row = row_for(report, copied)
    assert (row["decision"], row["reason"]) == ("preserve", "owner_liveness_unknown")
    assert (copied / "scratch" / "base" / "payload").read_bytes() == b"x" * 8192
    assert row_for(report, source)["decision"] == "deleted" and not source.exists()


def test_receipt_carries_preserved_reasons_measured_bytes_and_largest_preserved(area, monkeypatch):
    """Defect class: a receipt could not tell an operator what was kept, why, or how large."""
    if os.geteuid() == 0:
        pytest.skip("root can read a mode-000 lease")
    root, args = area
    dead_pid, dead_start = reaped_pid()
    deleted = leased(root, "rx-dead", pid=dead_pid, start_time=dead_start, boot_id=current_boot(), size=4096)
    deleted_bytes = allocated(deleted)
    child, pid, start = live_pid()
    try:
        live = leased(root, "rx-live", pid=pid, start_time=start, boot_id=current_boot(), size=16384)
        use_real_proc(monkeypatch)
        other = leased(
            root, "rx-other-boot", pid=dead_pid, start_time=dead_start,
            boot_id="00000000-0000-0000-0000-000000000000", size=8192,
        )
        deleted_bytes += allocated(other)
        unreadable = leased(
            root, "rx-unreadable", pid=dead_pid, start_time=dead_start, boot_id=current_boot(), size=32768
        )
        (unreadable / "lease.json").chmod(0o000)
        later(monkeypatch, 3 * HOUR)
        report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    finally:
        child.terminate()
        child.wait(timeout=10)
    assert report["preserved_by_reason"] == {"live_owner": 1, "lease_unreadable": 1}
    assert report["reclaimed_entries"] == 2 and not other.exists()
    assert report["reclaimed_bytes"] == report["deleted_bytes"] == deleted_bytes
    expected = sorted(((allocated(path), path.name) for path in (live, unreadable)), reverse=True)
    receipts = report["largest_preserved_runs"]
    assert [entry["rank"] for entry in receipts] == [1, 2]
    assert [(entry["bytes"], entry["reason"]) for entry in receipts] == [
        (expected[0][0], "lease_unreadable"),
        (expected[1][0], "live_owner"),
    ]
    ranked = {
        row["largest_preserved_rank"]: row["name"]
        for row in report["rows"] if "largest_preserved_rank" in row
    }
    assert ranked == {1: unreadable.name, 2: live.name}
