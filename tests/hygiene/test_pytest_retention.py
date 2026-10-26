"""Behavioral retention proofs for inactive pytest scratch on disposable roots (#10831, #11297)."""

from __future__ import annotations

import errno
import fcntl
import json
import math
import os
import resource
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
SECRET = "RAW-VALUE-NEVER-EMITTED"
# Waits on stdin; the first line names a path for fd/maps holders, the rest keeps it alive.
HOLDER = """
import ctypes, mmap, os, sys
mode = sys.argv[1]
target = sys.stdin.readline().strip()
handles = []
if mode == "fd":
    handles.append(open(target, "rb"))
elif mode == "maps":
    # Python's mmap keeps a duplicate descriptor; map through libc so only the mapping remains.
    libc = ctypes.CDLL(None, use_errno=True)
    libc.mmap.restype = ctypes.c_void_p
    libc.mmap.argtypes = (ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_long)
    fd = os.open(target, os.O_RDONLY)
    handles.append(libc.mmap(None, os.fstat(fd).st_size, mmap.PROT_READ, mmap.MAP_SHARED, fd, 0))
    os.close(fd)
    assert handles[0] not in (None, ctypes.c_void_p(-1).value)
print("ready", flush=True)
sys.stdin.read()
"""


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
    # An empty process table is a complete probe with no holders; tests add real or fake processes.
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


def expose(proc: Path, *pids: int) -> None:
    """Show only these real processes to the probe, through links to their /proc entries."""
    for pid in pids:
        (proc / str(pid)).symlink_to(f"/proc/{pid}", target_is_directory=True)


def fake_process(proc: Path, pid: int, state: str, *, cwd: Path | None = None) -> None:
    entry = proc / str(pid)
    entry.mkdir()
    (entry / "stat").write_text(f"{pid} (fake) {state} 1 1 1")
    for name in ("cmdline", "environ", "maps"):
        (entry / name).write_bytes(b"")
    (entry / "fd").mkdir()
    if cwd is not None:
        (entry / "cwd").symlink_to(cwd)


def spawn(mode: str, target: Path | None = None, *, cwd: Path | None = None, argv=(), env=None):
    proc = subprocess.Popen(
        [sys.executable, "-c", HOLDER, mode, *argv], cwd=cwd or REPO, env=env,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
    )
    proc.stdin.write(f"{target or ''}\n")
    proc.stdin.flush()
    assert proc.stdout.readline().strip() == "ready"
    return proc


def stop(proc: subprocess.Popen) -> None:
    proc.communicate(timeout=10)
    assert proc.returncode == 0


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
    assert dry["deleted_bytes"] == 0 and dry["errors"] == 0 and dry["liveness_complete"] is True

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
    # and holder evidence decide; the run after it is still processed.
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


@pytest.mark.parametrize("channel", ["cwd", "fd", "maps", "argv", "environ", "relative_argv"])
def test_every_live_holder_channel_preserves_the_run(area, monkeypatch, tmp_path, channel):
    root, args = area
    run = unowned(root, "held")
    other = unowned(root, "quiet-run")
    payload = run / "scratch" / "base" / "payload"
    later(monkeypatch, 3 * HOUR)
    env = {**os.environ, "SECRET_MARKER": SECRET}
    if channel == "cwd":
        proc = spawn("idle", cwd=payload.parent, env=env)
    elif channel in {"fd", "maps"}:
        proc = spawn(channel, payload, env=env)
    elif channel == "argv":
        proc = spawn("idle", argv=[f"--scratch={run}/scratch", SECRET], env=env)
    elif channel == "environ":
        proc = spawn("idle", env={**env, "TMPDIR": str(run / "scratch")})
    else:
        proc = spawn("idle", cwd=run.parent, argv=[f"./{run.name}/scratch", SECRET], env=env)
    try:
        expose(pytest_retention.PROC_ROOT, proc.pid)
        dry = row_for(tmp_sweep.sweep(**args)["pytest_retention"], run)
        assert (dry["decision"], dry["reason"], dry["live_pids"]) == ("preserve", "live_process", [proc.pid])
        report = tmp_sweep.sweep(**args, apply=True)
        retention = report["pytest_retention"]
        row = row_for(retention, run)
        assert (row["decision"], row["reason"]) == ("preserve", "live_process")
        assert row["live_pids"] == [proc.pid]
        assert row["holders"] == ["argv" if channel == "relative_argv" else channel]
        assert payload.read_bytes() == b"x" * 8192
        assert row_for(retention, other)["decision"] == "deleted" and not other.exists()
        emitted = json.dumps(report) + json.dumps(tmp_sweep.summarize(report))
        assert SECRET not in emitted and "--scratch=" not in emitted
    finally:
        stop(proc)


def _spelled_holder(channel: str, cwd: Path, value: str):
    env = {**os.environ, "SECRET_MARKER": SECRET}
    if channel == "environ":
        return spawn("idle", cwd=cwd, env={**env, "SCRATCH_HOME": value})
    return spawn("idle", cwd=cwd, argv=[value, SECRET], env=env)


@pytest.mark.parametrize("channel", ["argv", "environ"])
@pytest.mark.parametrize(
    "spelling",
    [
        "ancestor_relative", "namespace_dotdot", "absolute_dotdot", "symlink_alias", "path_list",
        "symlink_dotdot", "absolute_symlink_dotdot", "path_list_symlink_dotdot",
    ],
)
def test_noncanonical_argv_and_environment_spellings_hold_the_run(area, monkeypatch, tmp_path, channel, spelling):
    """Defect class: a live path named relative to an ancestor cwd, through ``..``, an alias, or an alias
    followed by ``..`` (which the kernel resolves through the alias target, not lexically) went unmatched."""
    root, args = area
    run = unowned(root, "spelled")
    quiet = unowned(root, "quiet-run")
    ns = run.parent
    alias = tmp_path / "alias"
    alias.symlink_to(ns, target_is_directory=True)
    below = f"{pytest_scratch.NAMESPACE}/{ns.name}/{run.name}/scratch"
    through = f"alias/../{ns.name}/{run.name}/scratch"  # alias -> ns, so its .. is ns's parent, not tmp_path
    cwd, value = {
        "ancestor_relative": (root, below),
        "namespace_dotdot": (ns, f"../{ns.name}/{run.name}/scratch"),
        "absolute_dotdot": (REPO, f"{ns}/../{ns.name}/{run.name}/scratch"),
        "symlink_alias": (REPO, f"{alias}/{run.name}/scratch"),
        "path_list": (root, f"/absent-11297:{below}"),
        "symlink_dotdot": (tmp_path, through),
        "absolute_symlink_dotdot": (REPO, f"{tmp_path}/{through}"),
        "path_list_symlink_dotdot": (tmp_path, f"/absent-11297:{through}"),
    }[spelling]
    assert str(run) not in value  # none of these spellings carries the canonical path
    # Kernel oracle: the spelling, read from the holder's cwd, reaches the run.
    assert os.path.samestat(os.stat(cwd / value.rpartition(":")[2]), os.stat(run / "scratch"))
    later(monkeypatch, 3 * HOUR)
    proc = _spelled_holder(channel, cwd, value)
    try:
        expose(pytest_retention.PROC_ROOT, proc.pid)
        dry = row_for(tmp_sweep.sweep(**args)["pytest_retention"], run)
        assert (dry["decision"], dry["reason"], dry["live_pids"], dry["holders"]) == (
            "preserve", "live_process", [proc.pid], [channel],
        )
        report = tmp_sweep.sweep(**args, apply=True)
        retention = report["pytest_retention"]
        row = row_for(retention, run)
        assert (row["decision"], row["reason"], row["holders"]) == ("preserve", "live_process", [channel])
        assert (run / "scratch" / "base" / "payload").read_bytes() == b"x" * 8192
        assert row_for(retention, quiet)["decision"] == "deleted" and not quiet.exists()
        emitted = json.dumps(report) + json.dumps(tmp_sweep.summarize(report))
        assert SECRET not in emitted and value not in emitted
    finally:
        stop(proc)


@pytest.mark.parametrize("channel", ["argv", "environ"])
@pytest.mark.parametrize("spelling", ["longer_name", "wrong_anchor", "dotdot_out"])
def test_lookalike_relative_spellings_do_not_hold_the_run(area, monkeypatch, channel, spelling):
    """Defect class: over-broad relative matching would keep an eligible run forever."""
    root, args = area
    run = unowned(root, "spelled")
    ns = run.parent
    cwd, value = {
        "longer_name": (ns, f"{run.name}-other/scratch"),
        "wrong_anchor": (root, f"{ns.name}/{run.name}"),
        "dotdot_out": (ns, f"{run.name}x/../../{run.name}"),
    }[spelling]
    later(monkeypatch, 3 * HOUR)
    proc = _spelled_holder(channel, cwd, value)
    try:
        expose(pytest_retention.PROC_ROOT, proc.pid)
        dry = row_for(tmp_sweep.sweep(**args)["pytest_retention"], run)
        assert (dry["decision"], dry["live_pids"]) == ("would_delete", [])
        assert row_for(tmp_sweep.sweep(**args, apply=True)["pytest_retention"], run)["decision"] == "deleted"
        assert not run.exists()
    finally:
        stop(proc)


@pytest.mark.parametrize("channel", ["cwd", "fd"])
def test_callers_own_preexisting_references_still_count(area, monkeypatch, channel):
    """Only the sweep's own lock handles are excused; the caller's real cwd and descriptors are holders."""
    root, args = area
    run = unowned(root, "caller")
    later(monkeypatch, 3 * HOUR)
    expose(pytest_retention.PROC_ROOT, os.getpid())
    if channel == "cwd":
        monkeypatch.chdir(run / "scratch")
        report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    else:
        with open(run / "scratch" / "base" / "payload", "rb"):
            report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    row = row_for(report, run)
    assert (row["reason"], row["holders"], row["live_pids"]) == ("live_process", [channel], [os.getpid()])
    assert run.is_dir()


def test_sweeps_own_lock_handles_are_not_holders_but_disabling_the_excuse_is_caught(area, monkeypatch):
    root, args = area
    runs = completed(root, 2)
    later(monkeypatch, 3 * HOUR)
    expose(pytest_retention.PROC_ROOT, os.getpid())
    real = pytest_retention.holder_snapshot
    # Negative control: without the own-handle excuse the held run locks look like holders.
    monkeypatch.setattr(pytest_retention, "holder_snapshot", lambda own_fds=frozenset(): real())
    report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    assert {(row["reason"], tuple(row["holders"])) for row in report["rows"]} == {("live_process", ("fd",))}
    assert all(path.is_dir() for path in runs)
    monkeypatch.setattr(pytest_retention, "holder_snapshot", real)
    report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    assert report["by_decision"] == {"deleted": 2}
    assert not any(path.exists() for path in runs)


def test_held_run_lock_preserves_even_when_the_holder_is_invisible(area, monkeypatch):
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


@pytest.mark.parametrize("rejection", ["too_young", "tree_unknown", "git_metadata", "scan_error"])
def test_rejected_lock_is_released_before_the_next_eligible_run(area, monkeypatch, rejection):
    """Preserve and exception paths must release their lock before inspecting the next run."""
    root, args = area
    rejected, eligible = malformed(root, "a-rejected"), malformed(root, "z-eligible")
    now = later(monkeypatch, 3 * HOUR)
    if rejection == "git_metadata":
        (rejected / ".git").mkdir()
    real_fingerprint, real_facts = tmp_sweep.tree_fingerprint, tmp_sweep.tree_facts

    def fingerprint(path):
        return None if path == rejected and rejection == "tree_unknown" else real_fingerprint(path)

    def facts(path):
        if path == rejected and rejection == "scan_error":
            raise OSError(5, "inspection failed after locking")
        return real_facts(path)

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


@pytest.mark.parametrize("phase", ["initial", "recheck", "lock", "process_state", "process_maps"])
def test_real_descriptor_exhaustion_is_an_error_and_preserves_runs(area, phase):
    """EMFILE must not masquerade as successful liveness probing or measured zero bytes."""
    root, args = area
    run = malformed(root, "preserved")
    expected = allocated(run)
    parent_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
    result = subprocess.run(
        [sys.executable, "-c", """
import json, os, resource, sys, time
from pathlib import Path
from scripts.hygiene import pytest_retention as retention, tmp_sweep
from scripts.hygiene.tmp_sweep_ledger import Ledger
root, state, tasks, proc = map(Path, sys.argv[1:5])
phase = sys.argv[5]
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
if phase.startswith('process_'):
    entry = proc / '4242'
    entry.mkdir()
    (entry / 'stat').write_bytes(b'4242 (fixture) S 1 2 3')
    (entry / 'cwd').symlink_to(root.parent, target_is_directory=True)
    (entry / 'fd').mkdir()
    (entry / 'maps').write_bytes(b'')
    (entry / 'cmdline').write_bytes(b'')
    (entry / 'environ').write_bytes(b'')
real_state = retention._process_state
def process_state(entry):
    if phase == 'process_state':
        exhaust()
    return real_state(entry)
retention._process_state = process_state
real_read = Path.read_bytes
def read_bytes(path):
    if phase == 'process_maps' and path.name == 'maps':
        exhaust()
    return real_read(path)
Path.read_bytes = read_bytes
real_snapshot = retention.holder_snapshot
def snapshot(own_fds=frozenset()):
    if phase == 'initial' or (phase == 'recheck' and own_fds):
        exhaust()
    try:
        return real_snapshot(own_fds)
    finally:
        release()
retention.holder_snapshot = snapshot
real_lock = retention._lock
def lock(fd):
    if phase == 'lock':
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
""", str(root), str(args["state_dir"]), str(args["task_root"]), str(root.parent / "proc"), phase],
        cwd=REPO, capture_output=True, text=True, check=True, timeout=60,
    )
    report = json.loads(result.stdout)
    print("real EMFILE", phase, result.stdout.strip())
    assert resource.getrlimit(resource.RLIMIT_NOFILE) == parent_limit
    assert report["by_reason"] == {"descriptor_exhausted": 1}
    assert report["by_decision"] == {"preserve": 1}
    assert report["errors"] == report["descriptor_exhaustion_entries"] == 1
    assert report["deleted_entries"] == 0
    assert report["liveness_complete"] is (phase == "lock")
    assert report["liveness_unreadable_processes"] == 0
    if phase in {"lock", "recheck"}:
        assert report["unmeasured_entries"] == report["protected_unmeasured_entries"] == 1
        assert report["protected_bytes_complete"] is False
        assert report["rows"][0]["bytes"] is None
    else:
        assert report["unmeasured_entries"] == 0
        assert report["protected_bytes_complete"] is True
        assert report["protected_bytes"] == expected
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


def test_released_lock_idle_owner_without_reference_is_eligible(area, monkeypatch):
    """Ownership state is not a holder channel: an idle former owner that references nothing does not preserve."""
    root, args = area
    run = completed(root, 1)[0]
    lease = json.loads((run / "lease.json").read_text())
    assert lease["state"] == "preserved"
    later(monkeypatch, 3 * HOUR)
    proc = spawn("idle")
    try:
        expose(pytest_retention.PROC_ROOT, proc.pid)
        assert row_for(tmp_sweep.sweep(**args, apply=True)["pytest_retention"], run)["decision"] == "deleted"
    finally:
        stop(proc)


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
    elif kind == "lock_fifo":  # tree safety, not custody: a FIFO endpoint cannot be proven unused
        assert (row["decision"], row["reason"]) == ("preserve", "special_file")
    else:
        assert row["decision"] == "deleted" and not run.exists()
    assert outside.read_text() == "outside"


@pytest.mark.parametrize("case", ["unreadable", "zombie", "dead", "vanished"])
def test_process_liveness_unknown_preserves_and_finished_processes_hold_nothing(area, monkeypatch, case):
    root, args = area
    run = unowned(root, "liveness")
    proc = pytest_retention.PROC_ROOT
    later(monkeypatch, 3 * HOUR)
    if case == "unreadable":
        fake_process(proc, 4242, "S")  # alive, cwd unreadable
    elif case == "zombie":
        fake_process(proc, 4242, "Z")
    elif case == "dead":
        fake_process(proc, 4242, "X")
    else:
        fake_process(proc, 4242, "S")
        real_state = pytest_retention._process_state

        def exits_during_scan(entry):
            if entry.name == "4242":
                for child in sorted(entry.rglob("*"), reverse=True):
                    child.unlink() if not child.is_dir() or child.is_symlink() else child.rmdir()
                entry.rmdir()
                return None
            return real_state(entry)

        monkeypatch.setattr(pytest_retention, "_process_state", exits_during_scan)
    report = tmp_sweep.sweep(**args)["pytest_retention"]
    row = row_for(report, run)
    if case == "unreadable":
        assert (row["decision"], row["reason"]) == ("preserve", "liveness_unknown")
        assert report["liveness_complete"] is False and report["liveness_unreadable_processes"] == 1
        assert tmp_sweep.sweep(**args, apply=True)["pytest_retention"]["deleted_entries"] == 0
        assert run.is_dir()
        # A spoofed command line alone still blocks; kernel unit and parent facts excuse it.
        entry = proc / "4242"
        uid = os.getuid()
        (entry / "status").write_text(f"Name:\tssh-agent\nPPid:\t20\nUid:\t{uid}\t{uid}\t{uid}\t{uid}\n")
        (entry / "cmdline").write_bytes(b"/usr/bin/ssh-agent\0-D\0")
        assert tmp_sweep.sweep(**args, apply=True)["pytest_retention"]["deleted_entries"] == 0
        assert run.is_dir()
        manager = f"0::/user.slice/user-{uid}.slice/user@{uid}.service"
        (entry / "cgroup").write_text(f"{manager}/app.slice/ssh-agent.service\n")
        fake_process(proc, 20, "S")
        (proc / "20" / "status").write_text(f"Name:\tsystemd\nUid:\t{uid}\t{uid}\t{uid}\t{uid}\n")
        (proc / "20" / "cgroup").write_text(f"{manager}/init.scope\n")
        report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
        assert row_for(report, run)["decision"] == "deleted" and not run.exists()
        assert report["liveness_complete"] is True and report["liveness_unreadable_processes"] == 0
        assert report["allowed_session_daemons"] == [{"pid": 20, "identity": "systemd"}, {"pid": 4242, "identity": "ssh-agent"}]
    else:
        assert row["decision"] == "would_delete" and report["liveness_complete"] is True


def test_unreadable_process_table_is_unknown(area, monkeypatch, tmp_path):
    root, args = area
    run = unowned(root, "no-proc")
    monkeypatch.setattr(pytest_retention, "PROC_ROOT", tmp_path / "missing-proc")
    later(monkeypatch, 3 * HOUR)
    assert row_for(tmp_sweep.sweep(**args, apply=True)["pytest_retention"], run)["reason"] == "liveness_unknown"


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


@pytest.mark.parametrize(
    "race",
    [
        "write", "holder_new_path", "holder_new_relative", "holder_old_path", "holder_old_relative",
        "holder_old_dotdot", "holder_old_symlink_dotdot", "unknown", "replaced",
    ],
)
def test_post_rename_recheck_returns_changed_or_newly_held_runs(area, monkeypatch, tmp_path, race):
    root, args = area
    run = unowned(root, "raced")
    later(monkeypatch, 3 * HOUR)
    procs = []
    identity = run.stat().st_ino

    def act(held: Path) -> None:
        if race == "write":
            (held / "scratch" / "new-output").write_text("fresh")
        elif race == "holder_new_path":
            procs.append(spawn("idle", cwd=held / "scratch"))
            expose(pytest_retention.PROC_ROOT, procs[-1].pid)
        elif race == "holder_new_relative":
            procs.append(spawn("idle", cwd=held.parent, argv=[f"{run.name}/scratch"]))
            expose(pytest_retention.PROC_ROOT, procs[-1].pid)
        elif race == "holder_old_path":
            procs.append(spawn("idle", argv=[str(run / "scratch")]))
            expose(pytest_retention.PROC_ROOT, procs[-1].pid)
        elif race == "holder_old_relative":
            procs.append(spawn("idle", cwd=root, argv=[str((run / "scratch").relative_to(root))]))
            expose(pytest_retention.PROC_ROOT, procs[-1].pid)
        elif race == "holder_old_dotdot":
            dotdot = f"{run.parent}/../{run.parent.name}/{run.name}/scratch"
            procs.append(spawn("idle", env={**os.environ, "SCRATCH_HOME": dotdot}))
            expose(pytest_retention.PROC_ROOT, procs[-1].pid)
        elif race == "holder_old_symlink_dotdot":
            (tmp_path / "alias").symlink_to(run.parent, target_is_directory=True)
            procs.append(spawn("idle", cwd=tmp_path, argv=[f"alias/../{run.parent.name}/{run.name}/scratch"]))
            expose(pytest_retention.PROC_ROOT, procs[-1].pid)
        else:
            fake_process(pytest_retention.PROC_ROOT, 4343, "S")

    try:
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
    finally:
        for proc in procs:
            stop(proc)
    assert calls == [True]
    row = row_for(report, run)
    assert row["decision"] == "preserve"
    expected = {
        "write": "recent_write", "holder_new_path": "live_process", "holder_new_relative": "live_process",
        "holder_old_path": "live_process", "holder_old_relative": "live_process", "holder_old_dotdot": "live_process",
        "holder_old_symlink_dotdot": "live_process",
        "unknown": "liveness_unknown", "replaced": "identity_changed",
    }[race]
    assert row["reason"] == expected
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
        tmp_sweep, "tree_fingerprint", lambda path: None if path == unreadable else real_fingerprint(path)
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
def test_tree_safety_reasons_still_preserve(area, monkeypatch, tmp_path, problem):
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
    assert (row["decision"], row["reason"]) == ("preserve", problem)
    assert (run / "scratch" / "base" / "payload").is_file()


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


@pytest.mark.parametrize(
    "blob,cwd,side,expected",
    [
        (b"run-1\0", "/absent-11297/ns", 1, "/absent-11297/ns/run-1"),
        (b"./run-1/scratch\0", "/absent-11297/ns", 1, "/absent-11297/ns/run-1/scratch"),
        (b"TMPDIR=run-1/scratch\0", "/absent-11297/ns", 1, "/absent-11297/ns/run-1/scratch"),
        (b"ns/run-1\0", "/absent-11297", 1, "/absent-11297/ns/run-1"),
        (b"../ns/run-1\0", "/absent-11297/ns", 1, "/absent-11297/ns/run-1"),
        (b"/absent-11297/ns/../ns/run-1\0", "/elsewhere", 0, "/absent-11297/ns/run-1"),
        (b"PYTHONPATH=/x:ns/run-1\0", "/absent-11297", 1, "/absent-11297/ns/run-1"),
        (b"run-1\0", "/absent-11297/ns (deleted)", 1, "/absent-11297/ns/run-1"),
    ],
)
def test_named_paths_fold_relative_and_dotdot_spellings(blob, cwd, side, expected):
    """Defect class: a spelling that the kernel resolves to the run but the matcher never derives."""
    named = pytest_retention._named_paths(blob, cwd, {})
    assert expected in named[side] and expected not in named[1 - side]


def test_named_paths_resolve_aliases_and_skip_empty_values(tmp_path):
    target = tmp_path / "ns"
    target.mkdir()
    (tmp_path / "alias").symlink_to(target, target_is_directory=True)
    forms: dict = {}
    absolute, relative = pytest_retention._named_paths(b"alias/run-1\0\0FLAG=\0", str(tmp_path), forms)
    assert absolute == set()
    assert str(target / "run-1") in relative and str(tmp_path / "alias" / "run-1") in relative
    assert str(tmp_path) not in relative  # an empty argument or value names nothing
    assert set(forms) == {str(tmp_path / "alias" / "run-1"), str(tmp_path / "FLAG=")}


def test_named_paths_follow_a_symlink_before_a_later_dotdot(tmp_path):
    """Defect class: folding ``..`` before resolving reads ``alias/../x`` as a sibling of the alias."""
    target = tmp_path / "deep" / "ns"
    target.mkdir(parents=True)
    (tmp_path / "alias").symlink_to(target, target_is_directory=True)
    absolute, relative = pytest_retention._named_paths(b"alias/../ns/run-1\0", str(tmp_path), {})
    assert absolute == set()
    assert str(target / "run-1") in relative  # where the kernel lands, not tmp_path/ns/run-1
    listed = b"X=/absent-11297:" + os.fsencode(tmp_path) + b"/alias/../ns/run-1\0"
    assert str(target / "run-1") in pytest_retention._named_paths(listed, "/", {})[0]


def test_relative_spellings_inside_a_held_cwd_report_only_the_cwd():
    """Defect class: every word of a process in the run misreported as an argv/environment holder."""
    run = Path("/absent-11297/ns/run-1")
    holders = pytest_retention.Holders(
        paths=[(7, "cwd", str(run / "scratch")), (8, "cwd", "/absent-11297/ns")],
        relative=[(7, "argv", str(run / "scratch" / "x")), (8, "environ", str(run / "y"))],
    )
    assert holders.holding([run]) == ([7, 8], ["cwd", "environ"])


def test_live_pytest_session_is_held_by_its_own_channels(area, monkeypatch):
    """A real running pytest owner shows through its lock descriptor and its exported TMPDIR."""
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
        expose(pytest_retention.PROC_ROOT, proc.pid)
        row = row_for(tmp_sweep.sweep(**args, apply=True)["pytest_retention"], live)
        assert row["decision"] == "preserve" and row["reason"] in {"in_use", "live_process"}
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
    result = subprocess.run(
        [sys.executable, "-c", "import os, pytest; os.umask(0o002); raise SystemExit(pytest.main(['-q', '-n', '2']))"],
        cwd=pytester.path, capture_output=True, text=True, timeout=30,
        env={**env, "TMPDIR": str(caller_temp)},
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


def use_real_proc(monkeypatch) -> None:
    """Judge lease liveness against the real process table, never a fabricated one."""
    monkeypatch.setattr(pytest_retention, "PROC_ROOT", Path("/proc"))


@pytest.mark.parametrize("ns", [pytest_scratch.RUNS_DIRNAME, task_scratch.NAMESPACE_DIRNAME])
@pytest.mark.parametrize("fixture_git", [False, True])
def test_reaped_lease_owner_is_reclaimed_without_all_process_visibility(area, monkeypatch, ns, fixture_git):
    """Defect class #11409: an unreadable unrelated process blocked every reclaim.

    The lease names a real child that has exited; the run lock is free and the
    tree is old, so the run must be deleted against the real process table.
    C-2447 also requires disposable fixture Git metadata to remain reclaimable.
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
    # The host may expose unreadable same-user processes; the lease proof, not a
    # complete snapshot, is what must admit the deletion.
    report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    row = row_for(report, run)
    assert row["decision"] == "deleted" and not run.exists()
    assert report["reclaimed_entries"] == 1
    assert report["reclaimed_bytes"] == report["deleted_bytes"] == expected_bytes > 0


@pytest.mark.parametrize("ns", [pytest_scratch.RUNS_DIRNAME, task_scratch.NAMESPACE_DIRNAME])
@pytest.mark.parametrize("case,reason", [
    ("separate_git_dir", "git_metadata"), ("linked_worktree", "git_metadata"),
    ("external_worktree", "git_metadata"), ("git_symlink", "git_metadata"),
    ("objects_symlink", "git_metadata"), ("alternates", "git_metadata"),
    ("commondir", "git_metadata"), ("core_worktree", "git_metadata"),
    ("include", "git_metadata"), ("extension", "git_metadata"),
    ("unfamiliar_config", "git_metadata"), ("invalid_config", "git_metadata"),
    ("no_owner", "git_metadata"), ("live_owner", "git_metadata"),
    ("unknown_owner", "git_metadata"), ("probe_failure", "git_metadata"),
    ("hardlink", "hardlinked_content"), ("fifo", "special_file"),
    ("registered", "registered_worktree"), ("young", "too_young"),
])
def test_fixture_git_custody_and_safety_preserve(area, monkeypatch, tmp_path, ns, case, reason):
    """Data-loss class: the disposable Git exception admits external custody or unsafe runs."""
    root, args = area
    pid, start = reaped_pid()
    run = leased(root, "fixture-control", pid=pid, start_time=start, boot_id=current_boot(), ns=ns)
    fixture = run / "scratch" / "fixture"
    outside = tmp_path / "external"
    outside.mkdir()
    (outside / "sentinel").write_text("keep outside")

    def git(*arguments):
        return subprocess.run(["git", *map(str, arguments)], check=True, capture_output=True, timeout=10)

    if case == "separate_git_dir":
        git("init", "--separate-git-dir", outside / "metadata", fixture)
    elif case == "linked_worktree":
        git("init", outside / "source")
        git("-C", outside / "source", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.test",
            "commit", "--allow-empty", "-m", "fixture")
        git("-C", outside / "source", "worktree", "add", "--detach", fixture)
    else:
        git("init", fixture)
        metadata = fixture / ".git"
        if case == "external_worktree":
            git("-C", fixture, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.test",
                "commit", "--allow-empty", "-m", "fixture")
            git("-C", fixture, "worktree", "add", "--detach", outside / "worktree")
        elif case == "git_symlink":
            metadata.rename(outside / "metadata")
            metadata.symlink_to(outside / "metadata", target_is_directory=True)
        elif case == "objects_symlink":
            (metadata / "objects").rename(outside / "objects")
            (metadata / "objects").symlink_to(outside / "objects", target_is_directory=True)
        elif case == "alternates":
            (metadata / "objects" / "info" / "alternates").write_text(str(outside) + "\n")
        elif case == "commondir":
            (metadata / "commondir").write_text(str(outside) + "\n")
        elif case in {"core_worktree", "include", "extension", "unfamiliar_config"}:
            key, value = {
                "core_worktree": ("core.worktree", str(outside)),
                "include": ("include.path", str(outside / "sentinel")),
                "extension": ("extensions.worktreeConfig", "true"),
                "unfamiliar_config": ("core.hooksPath", str(outside)),
            }[case]
            git("config", "--file", metadata / "config", key, value)
        elif case == "invalid_config":
            (metadata / "config").write_text("[broken")
        elif case == "no_owner":
            (run / "lease.json").unlink()
        elif case in {"live_owner", "unknown_owner"}:
            write_lease(run, pid=os.getpid(), start_time=None, boot_id=current_boot())
            use_real_proc(monkeypatch)
            if case == "live_owner":
                from scripts.common.acp_runtime_lock import process_start_time

                write_lease(run, pid=os.getpid(), start_time=process_start_time(os.getpid()), boot_id=current_boot())
        elif case == "probe_failure":
            def unavailable(*args, **kwargs):
                raise OSError(errno.EIO, "Git config probe unavailable")

            monkeypatch.setattr(tmp_sweep.subprocess, "run", unavailable)
        elif case == "hardlink":
            os.link(metadata / "HEAD", outside / "linked-head")
        elif case == "fifo":
            os.mkfifo(metadata / "endpoint")
        elif case == "registered":
            monkeypatch.setattr(tmp_sweep, "registered_worktrees", lambda _: {fixture})
    if case != "young":
        later(monkeypatch, 3 * HOUR)
    before = tree_state(root, outside)
    for apply in (False, True):
        report = tmp_sweep.sweep(**args, apply=apply)["pytest_retention"]
        assert (row_for(report, run)["decision"], row_for(report, run)["reason"]) == ("preserve", reason)
        assert report["deleted_bytes"] == report["would_delete_bytes"] == 0
        assert tree_state(root, outside) == before
        assert (outside / "sentinel").read_text() == "keep outside"


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


def test_lease_from_a_different_boot_is_kept(area, monkeypatch):
    """Defect class: start times from another boot were compared as if comparable."""
    root, args = area
    pid, start = reaped_pid()
    run = leased(
        root, "other-boot", pid=pid, start_time=start,
        boot_id="00000000-0000-0000-0000-000000000000",
    )
    later(monkeypatch, 3 * HOUR)
    row = row_for(tmp_sweep.sweep(**args, apply=True)["pytest_retention"], run)
    assert (row["decision"], row["reason"]) == ("preserve", "different_boot")
    assert run.is_dir()


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


def test_root_holder_takes_the_bounded_quarantine_recheck_path(area, monkeypatch):
    """Defect class: an unreadable root process blocked deletion instead of using the recheck.

    Only the process's owner classification is injected; the lease liveness and
    the quarantine/recheck remain the product code under test.
    """
    root, args = area
    pid, start = reaped_pid()
    run = leased(root, "root-held", pid=pid, start_time=start, boot_id=current_boot())
    fake_process(pytest_retention.PROC_ROOT, 4242, "S")  # alive, cwd unreadable
    real_uid = pytest_retention._process_uid
    monkeypatch.setattr(
        pytest_retention, "_process_uid",
        lambda entry: 0 if entry.name == "4242" else real_uid(entry),
    )
    rechecks = []
    real_recheck = pytest_retention._recheck

    def recheck(*positional):
        rechecks.append(True)
        return real_recheck(*positional)

    monkeypatch.setattr(pytest_retention, "_recheck", recheck)
    later(monkeypatch, 3 * HOUR)
    report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    row = row_for(report, run)
    assert rechecks == [True]
    assert row["decision"] == "deleted" and not run.exists()
    assert report["liveness_complete"] is False
    assert report["liveness_unreadable_root_processes"] == 1
    assert report["deleted_bytes"] > 0


def test_copied_dead_owner_lease_does_not_bypass_unknown_liveness(area, monkeypatch):
    """Data-loss class: a lease copied from another run vouched for this run's owner.

    Its dead owner says nothing about this run, so an incomplete process
    snapshot must still preserve it; the run the lease names is the control.
    """
    root, args = area
    pid, start = reaped_pid()
    source = leased(root, "lease-source", pid=pid, start_time=start, boot_id=current_boot())
    copied = unowned(root, "lease-copy")
    for name in ("lease.json", "lease.lock"):
        (copied / name).write_bytes((source / name).read_bytes())
    fake_process(pytest_retention.PROC_ROOT, 4242, "S")  # alive, cwd unreadable
    later(monkeypatch, 3 * HOUR)
    report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    row = row_for(report, copied)
    assert (row["decision"], row["reason"]) == ("preserve", "owner_liveness_unknown")
    assert (copied / "scratch" / "base" / "payload").read_bytes() == b"x" * 8192
    assert report["liveness_complete"] is False
    assert row_for(report, source)["decision"] == "deleted" and not source.exists()


def test_unprovable_holders_preserve_and_partial_holder_evidence_is_kept(area, monkeypatch):
    """Data-loss class: an unreadable foreign-uid process or a later failed inspection channel
    let a held run be deleted.

    An unreadable foreign-uid process must leave an unleased run preserved, and
    a holder whose working directory was read before its descriptors failed
    must still preserve a dead-owner run.
    """
    root, args = area
    proc = pytest_retention.PROC_ROOT
    unleased = unowned(root, "foreign-unprovable")
    fake_process(proc, 4242, "S")  # alive, cwd unreadable
    real_uid = pytest_retention._process_uid
    monkeypatch.setattr(
        pytest_retention, "_process_uid",
        lambda entry: os.geteuid() + 1 if entry.name == "4242" else real_uid(entry),
    )
    later(monkeypatch, 3 * HOUR)
    report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    row = row_for(report, unleased)
    assert (row["decision"], row["reason"]) == ("preserve", "liveness_unknown") and unleased.is_dir()
    assert report["liveness_complete"] is False
    assert report["liveness_unreadable_foreign_processes"] == 1

    pid, start = reaped_pid()
    partial = leased(root, "partially-read-holder", pid=pid, start_time=start, boot_id=current_boot())
    fake_process(proc, 4343, "S", cwd=partial / "scratch")
    (proc / "4343" / "fd").rmdir()  # descriptors fail after the cwd was read
    report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    held = row_for(report, partial)
    assert (held["decision"], held["reason"], held["live_pids"]) == ("preserve", "live_process", [4343])
    assert partial.is_dir() and report["deleted_entries"] == 0


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
        expose(pytest_retention.PROC_ROOT, pid)
        other = leased(
            root, "rx-other-boot", pid=dead_pid, start_time=dead_start,
            boot_id="00000000-0000-0000-0000-000000000000", size=8192,
        )
        unreadable = leased(
            root, "rx-unreadable", pid=dead_pid, start_time=dead_start, boot_id=current_boot(), size=32768
        )
        (unreadable / "lease.json").chmod(0o000)
        later(monkeypatch, 3 * HOUR)
        report = tmp_sweep.sweep(**args, apply=True)["pytest_retention"]
    finally:
        child.terminate()
        child.wait(timeout=10)
    assert report["preserved_by_reason"] == {
        "live_owner": 1, "different_boot": 1, "lease_unreadable": 1,
    }
    assert report["reclaimed_entries"] == 1
    assert report["reclaimed_bytes"] == report["deleted_bytes"] == deleted_bytes
    expected = sorted(
        ((allocated(path), path.name) for path in (live, other, unreadable)), reverse=True
    )
    receipts = report["largest_preserved_runs"]
    assert [entry["rank"] for entry in receipts] == [1, 2, 3]
    assert [(entry["bytes"], entry["reason"]) for entry in receipts] == [
        (expected[0][0], "lease_unreadable"),
        (expected[1][0], "live_owner"),
        (expected[2][0], "different_boot"),
    ]
    ranked = {
        row["largest_preserved_rank"]: row["name"]
        for row in report["rows"] if "largest_preserved_rank" in row
    }
    assert ranked == {1: unreadable.name, 2: live.name, 3: other.name}
