"""Task-owned scratch lifecycle, wrapper CLI and orphan recovery (#8738)."""

from __future__ import annotations

import contextlib
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

from scripts.common import task_scratch as ts

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI = REPO_ROOT / "scripts" / "tools" / "task_scratch.py"

pytestmark = pytest.mark.skipif(not Path("/proc").is_dir(), reason="task-scratch liveness proofs need Linux /proc")


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------


def _namespace(root: Path) -> Path:
    return root / ts.NAMESPACE_DIRNAME


def _leases(root: Path) -> dict[str, dict]:
    found: dict[str, dict] = {}
    namespace = _namespace(root)
    if not namespace.is_dir():
        return found
    for child in namespace.iterdir():
        lease_file = child / ts.LEASE_FILENAME
        if lease_file.is_file():
            parsed = ts.parse_lease(lease_file.read_bytes())
            if parsed is not None:
                found[child.name] = parsed
    return found


def _wait_for(predicate, *, timeout_s: float = 10.0, what: str = "condition"):
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(0.05)
    raise AssertionError(f"timed out waiting for {what}")


def _wait_running_lease(root: Path) -> tuple[str, dict]:
    def running():
        for name, lease in _leases(root).items():
            if lease["state"] == "running" and lease["child"]:
                return name, lease
        return None

    return _wait_for(running, what="a running lease")


def _spawn_cli(
    root: Path,
    task_id: str,
    payload: list[str],
    *,
    extra_env: dict[str, str] | None = None,
    cli_args=(),
    capture: bool = False,
):
    """Start the wrapper CLI. ``capture`` pipes stderr; only use it when the
    payload is guaranteed to exit (a surviving child would hold the pipe open)."""
    env = dict(os.environ)
    env.pop(ts.FAULT_ENV_VAR, None)
    env.update(extra_env or {})
    sink = subprocess.PIPE if capture else subprocess.DEVNULL
    return subprocess.Popen(
        [sys.executable, str(CLI), "run", "--task-id", task_id, "--scratch-root", str(root), *cli_args, "--", *payload],
        env=env,
        stdout=sink,
        stderr=sink,
        cwd=str(REPO_ROOT),
    )


STUBBORN = [
    sys.executable,
    "-c",
    "import signal, time; signal.signal(signal.SIGTERM, signal.SIG_IGN); "
    "signal.signal(signal.SIGINT, signal.SIG_IGN); time.sleep(30)",
]


def _pid_alive(pid: int) -> bool:
    return Path(f"/proc/{pid}").is_dir()


def _comm(pid: int) -> str | None:
    try:
        return Path(f"/proc/{pid}/comm").read_text().strip()
    except OSError:
        return None


def _age_tree(path: Path, age_s: float) -> None:
    past = time.time() - age_s
    for item in [path, *path.rglob("*")]:
        os.utime(item, (past, past), follow_symlinks=False)


def _plant_dead_owner(root: Path, task_id: str = "8738-dead", *, payload_bytes: int = 2048) -> Path:
    scratch = ts.allocate(task_id, root=root)
    (scratch.payload_dir / "atlas.db").write_bytes(b"d" * payload_bytes)
    scratch.lease["owner"]["pid"] = 2_000_000_000  # above pid_max: provably absent
    scratch.lease["owner"]["start_time"] = 1
    ts._write_lease_at(scratch._dir_fd, scratch.lease)
    scratch.preserve()
    return scratch.path


def _recover(root: Path, **kwargs):
    kwargs.setdefault("min_age_s", 0)
    kwargs.setdefault("pressure_min_age_s", 0)
    return ts.recover_orphans(root=root, **kwargs)


def _entry(report: dict, name: str) -> dict:
    return next(entry for entry in report["entries"] if entry["name"] == name)


# --------------------------------------------------------------------------
# wrapper: success / failure / signals / environment
# --------------------------------------------------------------------------


def test_success_removes_scratch_and_exposes_env(tmp_path: Path) -> None:
    root = tmp_path / "root"
    probe = tmp_path / "probe.json"
    payload = [
        "bash",
        "-euc",
        'printf \'{"tmpdir":"%s","scratch":"%s","task":"%s"}\' "$TMPDIR" "$LU_TASK_SCRATCH_DIR" "$LU_TASK_SCRATCH_TASK_ID" > "$1"; '
        'dd if=/dev/zero of="$LU_TASK_SCRATCH_DIR/atlas.db" bs=1k count=64 status=none',
        "_",
        str(probe),
    ]
    outcome = ts.run_task("atlas-8307-410k", payload, root=root, log=lambda _m: None)

    assert outcome.exit_status == 0
    assert outcome.action == "removed"
    assert outcome.group_status == "absent"
    assert not outcome.scratch_path.exists()
    assert _namespace(root).is_dir()
    assert oct(_namespace(root).stat().st_mode & 0o777) == "0o700"
    seen = json.loads(probe.read_text())
    assert seen["tmpdir"] == seen["scratch"]
    assert Path(seen["scratch"]).parent == outcome.scratch_path
    assert seen["task"] == "atlas-8307-410k"
    assert not _leases(root)


def test_nonzero_exit_is_preserved_and_scratch_removed(tmp_path: Path) -> None:
    root = tmp_path / "root"
    outcome = ts.run_task(
        "qa-1", ["bash", "-c", 'echo x > "$LU_TASK_SCRATCH_DIR/f"; exit 7'], root=root, log=lambda _m: None
    )
    assert outcome.exit_status == 7
    assert outcome.action == "removed"
    assert not outcome.scratch_path.exists()


def test_keep_on_failure_preserves_lease_for_recovery(tmp_path: Path) -> None:
    root = tmp_path / "root"
    outcome = ts.run_task("qa-2", ["bash", "-c", "exit 3"], root=root, keep_on_failure=True, log=lambda _m: None)
    assert outcome.exit_status == 3
    assert outcome.action == "kept"
    assert outcome.scratch_path.is_dir()
    lease = _leases(root)[outcome.invocation_id]
    assert lease["state"] == "preserved"
    assert lease["task_id"] == "qa-2"


def test_signal_killed_child_maps_to_128_plus_signal(tmp_path: Path) -> None:
    root = tmp_path / "root"
    outcome = ts.run_task("qa-3", ["bash", "-c", "kill -TERM $$"], root=root, log=lambda _m: None)
    assert outcome.returncode == -signal.SIGTERM
    assert outcome.exit_status == 128 + signal.SIGTERM
    assert not outcome.scratch_path.exists()


@pytest.mark.parametrize(("signum", "expected"), [(signal.SIGTERM, 143), (signal.SIGINT, 130)])
def test_wrapper_forwards_signal_waits_and_cleans(tmp_path: Path, signum: int, expected: int) -> None:
    root = tmp_path / "root"
    proc = _spawn_cli(root, "sig", ["sleep", "30"], cli_args=("--json",), capture=True)
    try:
        name, lease = _wait_running_lease(root)
        child_pid = lease["child"]["pid"]
        _wait_for(lambda: _comm(child_pid) == "sleep", what="payload to exec")
        proc.send_signal(signum)
        _out, err = proc.communicate(timeout=15)
    finally:
        if proc.poll() is None:
            proc.kill()
    assert proc.returncode == expected, err.decode()
    assert not (_namespace(root) / name).exists()
    assert not _pid_alive(child_pid)
    summary = json.loads(err.decode().strip().splitlines()[-1])
    assert summary["interrupted_by"] == int(signum)
    assert summary["action"] == "removed"


def test_wrapper_escalates_to_sigkill_when_child_ignores_term(tmp_path: Path) -> None:
    root = tmp_path / "root"
    proc = _spawn_cli(root, "stubborn", STUBBORN, cli_args=("--kill-after-s", "0.5"))
    try:
        name, lease = _wait_running_lease(root)
        _wait_for(lambda: _pid_alive(lease["child"]["pid"]), what="stubborn child")
        time.sleep(0.3)  # let the child install its SIG_IGN handlers
        proc.send_signal(signal.SIGTERM)
        proc.wait(timeout=15)
    finally:
        if proc.poll() is None:
            proc.kill()
    assert proc.returncode == 128 + signal.SIGKILL
    assert not (_namespace(root) / name).exists()
    assert not _pid_alive(lease["child"]["pid"])


def test_grandchild_surviving_leader_is_drained_before_cleanup(tmp_path: Path) -> None:
    root = tmp_path / "root"
    marker = tmp_path / "grandchild.pid"
    outcome = ts.run_task(
        "gc",
        ["bash", "-c", f'sleep 30 & echo $! > "{marker}"; exit 0'],
        root=root,
        group_grace_s=0.3,
        log=lambda _m: None,
    )
    grandchild = int(marker.read_text().strip())
    assert outcome.exit_status == 0
    assert outcome.group_status == "absent"
    assert outcome.action == "removed"
    assert not outcome.scratch_path.exists()
    assert not _pid_alive(grandchild)


def test_concurrent_invocations_of_same_task_are_distinct(tmp_path: Path) -> None:
    root = tmp_path / "root"
    first = ts.allocate("atlas-8307-410k", root=root)
    second = ts.allocate("atlas-8307-410k", root=root)
    try:
        assert first.path != second.path
        assert first.invocation_id != second.invocation_id
        assert first.lease["task_id"] == second.lease["task_id"] == "atlas-8307-410k"
        (second.payload_dir / "keep").write_text("x")
        first.remove()
        assert not first.path.exists()
        assert (second.payload_dir / "keep").is_file()
        report = _recover(root)
        assert _entry(report, second.invocation_id)["reason"] == "in_use"
    finally:
        if not second._released:
            second.remove()
    assert not second.path.exists()


def test_owner_metadata_exists_before_payload_and_is_private(tmp_path: Path) -> None:
    root = tmp_path / "root"
    scratch = ts.allocate("meta", root=root)
    try:
        lease_file = scratch.path / ts.LEASE_FILENAME
        assert lease_file.is_file() and not lease_file.is_symlink()
        assert oct(lease_file.stat().st_mode & 0o777) == "0o600"
        assert oct(scratch.path.stat().st_mode & 0o777) == "0o700"
        assert lease_file.stat().st_mtime <= scratch.payload_dir.stat().st_mtime
        lease = ts.parse_lease(lease_file.read_bytes())
        assert lease is not None
        assert lease["owner"]["pid"] == os.getpid()
        assert lease["owner"]["start_time"] == ts.process_start_time(os.getpid())
        assert lease["owner"]["boot_id"] == ts.current_boot_id()
        st = scratch.path.stat()
        assert lease["dir"] == {"dev": st.st_dev, "ino": st.st_ino}
        assert lease["uid"] == os.geteuid()
        assert lease["child"] is None
    finally:
        scratch.remove()


def test_evidence_is_exported_only_on_request(tmp_path: Path) -> None:
    root = tmp_path / "root"
    evidence_dir = tmp_path / "evidence-out"
    payload = [
        "bash",
        "-euc",
        'mkdir -p "$LU_TASK_SCRATCH_DIR/evidence"; echo ok > "$LU_TASK_SCRATCH_DIR/evidence/summary.txt"',
    ]
    without = ts.run_task("ev", payload, root=root, log=lambda _m: None)
    assert without.evidence is None
    assert not evidence_dir.exists()
    with_evidence = ts.run_task("ev", payload, root=root, evidence_dir=evidence_dir, log=lambda _m: None)
    assert with_evidence.evidence == {
        "source_present": True,
        "files": 1,
        "bytes": 3,
        "destination": str(evidence_dir),
    }
    assert (evidence_dir / "summary.txt").read_text() == "ok\n"
    assert not with_evidence.scratch_path.exists()


def test_cli_help_shows_atlas_410k_invocation() -> None:
    completed = subprocess.run(
        [sys.executable, str(CLI), "run", "--help"],
        capture_output=True,
        text=True,
        check=True,
        cwd=str(REPO_ROOT),
        timeout=30,
    )
    for needle in (
        'export PRIMARY_REPO="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")"',
        '"$PRIMARY_REPO/.venv/bin/python" scripts/tools/task_scratch.py run --task-id atlas-8307-410k',
        '"$PRIMARY_REPO/.venv/bin/python" -m scripts.benchmarks.generate_synthetic_atlas',
        '--source-db "$PRIMARY_REPO/data/atlas.db" --out "$LU_TASK_SCRATCH_DIR/atlas.db"',
        "--seed 8307 --target 410000",
        '"$PRIMARY_REPO/.venv/bin/python" -m scripts.atlas.export_runtime_shards',
        '--out-dir "$LU_TASK_SCRATCH_DIR/export"',
        '--deck-dir "$PRIMARY_REPO/site/public/lexicon" --verify',
        "bash -euc",
        "--evidence-dir",
    ):
        assert needle in completed.stdout, needle
    # No relative interpreter / data paths survive: a dispatch worktree has neither.
    assert "  .venv/bin/python" not in completed.stdout
    assert "--source-db data/atlas.db" not in completed.stdout


def test_cli_rejects_missing_command(tmp_path: Path) -> None:
    completed = subprocess.run(
        [sys.executable, str(CLI), "run", "--task-id", "x", "--scratch-root", str(tmp_path)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=30,
    )
    assert completed.returncode != 0
    assert "missing command" in completed.stderr


# --------------------------------------------------------------------------
# launch gate + orphan recovery
# --------------------------------------------------------------------------


def test_wrapper_killed_before_release_never_runs_payload(tmp_path: Path) -> None:
    root = tmp_path / "root"
    marker = tmp_path / "ran"
    proc = _spawn_cli(
        root,
        "gate",
        ["bash", "-c", f'touch "{marker}"'],
        extra_env={ts.FAULT_ENV_VAR: ts.FAULT_KILL_BEFORE_RELEASE},
    )
    proc.wait(timeout=15)
    assert proc.returncode == -signal.SIGKILL
    name, lease = next(iter(_leases(root).items()))
    child_pid = lease["child"]["pid"]
    _wait_for(lambda: not _pid_alive(child_pid), what="gated child to exit")
    time.sleep(0.2)
    assert not marker.exists(), "payload must not run when the wrapper dies before releasing the gate"

    report = _recover(root, apply=True)
    entry = _entry(report, name)
    assert entry["action"] == "reaped"
    assert entry["reason"] == "owner_dead"
    assert not (_namespace(root) / name).exists()


def test_killed_wrapper_with_live_child_is_preserved_then_recovered(tmp_path: Path) -> None:
    root = tmp_path / "root"
    proc = _spawn_cli(root, "survivor", ["sleep", "30"])
    name, lease = _wait_running_lease(root)
    child_pid = lease["child"]["pid"]
    proc.kill()
    proc.wait(timeout=15)
    assert _pid_alive(child_pid)

    preserved = _recover(root, apply=True)
    assert _entry(preserved, name)["action"] == "preserved"
    assert _entry(preserved, name)["reason"] == "child_alive"
    assert (_namespace(root) / name).is_dir()

    os.killpg(lease["child"]["pgid"], signal.SIGKILL)
    _wait_for(lambda: not _pid_alive(child_pid), what="child to die")
    recovered = _recover(root, apply=True)
    assert _entry(recovered, name)["action"] == "reaped"
    assert not (_namespace(root) / name).exists()


def test_leader_exit_with_surviving_grandchild_preserves_until_group_dead(tmp_path: Path) -> None:
    # The running lease is fsynced before the launch gate opens. Killing the
    # wrapper on that lease alone often aborts the payload, so the recorded
    # group is empty (#8848). Wait until the grandchild has published its pid
    # and blocked; only then is it actually in the group.
    root = tmp_path / "root"
    hold = tmp_path / "hold.fifo"
    pidfile = tmp_path / "grandchild.pid"
    os.mkfifo(hold)
    payload = [
        sys.executable,
        "-c",
        "import os, sys, time\n"
        "from pathlib import Path\n"
        "pidfile, fifo = sys.argv[1], sys.argv[2]\n"
        "grandchild = os.fork()\n"
        "if grandchild == 0:\n"
        "    fd = os.open(pidfile, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)\n"
        "    os.write(fd, f'{os.getpid()}\\n'.encode())\n"
        "    os.fsync(fd)\n"
        "    os.close(fd)\n"
        "    held = os.open(fifo, os.O_RDONLY)\n"
        "    os.read(held, 1)\n"
        "    os._exit(0)\n"
        "deadline = time.monotonic() + 10\n"
        "while time.monotonic() < deadline:\n"
        "    path = Path(pidfile)\n"
        "    if path.is_file() and path.read_text(encoding='utf-8').strip() == str(grandchild):\n"
        "        os._exit(0)\n"
        "    time.sleep(0.01)\n"
        "os._exit(1)\n",
        str(pidfile),
        str(hold),
    ]
    proc = _spawn_cli(root, "grandchild", payload)
    pgid = None
    released = False
    try:

        def published_pid() -> int | None:
            if not pidfile.is_file():
                return None
            text = pidfile.read_text(encoding="utf-8").strip()
            return int(text) if text.isdigit() else None

        grandchild = _wait_for(published_pid, what="grandchild pid file")
        name, lease = _wait_running_lease(root)
        leader = lease["child"]["pid"]
        pgid = lease["child"]["pgid"]
        proc.kill()
        proc.wait(timeout=15)
        _wait_for(lambda: not _pid_alive(leader), what="leader to exit")
        probe = ts.probe_process_group(pgid)
        assert probe.complete and grandchild in probe.members, "grandchild must still be in the recorded group"

        report = _recover(root, apply=True)
        assert _entry(report, name)["reason"] == "group_members_alive"
        assert (_namespace(root) / name).is_dir()

        os.killpg(pgid, signal.SIGKILL)
        _wait_for(lambda: not ts.probe_process_group(pgid).members, what="group to drain")
        report = _recover(root, apply=True)
        assert _entry(report, name)["action"] == "reaped"
        released = True
    finally:
        if not released:
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=15)
            if pgid is None:
                for lease in _leases(root).values():
                    child = lease.get("child") or {}
                    if child.get("pgid"):
                        pgid = child["pgid"]
                        break
            if pgid is not None:
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(pgid, signal.SIGKILL)
                _wait_for(lambda: not ts.probe_process_group(pgid).members, what="group to drain")
        hold.unlink(missing_ok=True)


def test_recovery_never_signals_processes(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "root"
    _plant_dead_owner(root)
    monkeypatch.setattr(ts.os, "kill", lambda *_a, **_k: pytest.fail("recovery must not kill"))
    monkeypatch.setattr(ts.os, "killpg", lambda *_a, **_k: pytest.fail("recovery must not killpg"))
    report = _recover(root, apply=True)
    assert report["reaped"] == 1


def test_reused_owner_pid_counts_as_dead_but_unknown_start_preserves(tmp_path: Path) -> None:
    root = tmp_path / "root"
    reused = ts.allocate("reused", root=root)
    reused.lease["owner"] = {"pid": os.getpid(), "start_time": 1, "boot_id": ts.current_boot_id()}
    ts._write_lease_at(reused._dir_fd, reused.lease)
    reused.preserve()
    unknown = ts.allocate("unknown", root=root)
    unknown.lease["owner"] = {"pid": os.getpid(), "start_time": None, "boot_id": ts.current_boot_id()}
    ts._write_lease_at(unknown._dir_fd, unknown.lease)
    unknown.preserve()

    report = _recover(root, apply=True)
    assert _entry(report, reused.invocation_id)["action"] == "reaped"
    assert _entry(report, unknown.invocation_id)["reason"] == "owner_liveness_unknown"
    assert unknown.path.is_dir()


def test_reused_group_id_is_preserved(tmp_path: Path) -> None:
    root = tmp_path / "root"
    pgid = os.getpgid(0)
    scratch = ts.allocate("reused-group", root=root)
    scratch.lease["owner"] = {"pid": 2_000_000_000, "start_time": 1, "boot_id": ts.current_boot_id()}
    scratch.lease["child"] = {"pid": pgid, "pgid": pgid, "start_time": 1}
    scratch.lease["state"] = "running"
    ts._write_lease_at(scratch._dir_fd, scratch.lease)
    scratch.preserve()

    report = _recover(root, apply=True)
    entry = _entry(report, scratch.invocation_id)
    assert entry["action"] == "preserved"
    assert entry["reason"] in {"group_id_reused", "group_members_alive"}
    assert scratch.path.is_dir()


def test_reboot_proves_owner_and_child_dead(tmp_path: Path) -> None:
    root = tmp_path / "root"
    scratch = ts.allocate("rebooted", root=root)
    scratch.lease["owner"] = {
        "pid": os.getpid(),
        "start_time": ts.process_start_time(os.getpid()),
        "boot_id": "old-boot",
    }
    scratch.lease["child"] = {
        "pid": os.getpid(),
        "pgid": os.getpgid(0),
        "start_time": ts.process_start_time(os.getpid()),
    }
    ts._write_lease_at(scratch._dir_fd, scratch.lease)
    scratch.preserve()
    report = _recover(root, apply=True)
    assert _entry(report, scratch.invocation_id)["action"] == "reaped"
    assert _entry(report, scratch.invocation_id)["reason"] == "owner_dead_reboot"


def test_unknown_group_probe_preserves(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "root"
    scratch = ts.allocate("probe", root=root)
    scratch.lease["owner"] = {"pid": 2_000_000_000, "start_time": 1, "boot_id": ts.current_boot_id()}
    scratch.lease["child"] = {"pid": 2_000_000_001, "pgid": 2_000_000_001, "start_time": 1}
    ts._write_lease_at(scratch._dir_fd, scratch.lease)
    scratch.preserve()
    monkeypatch.setattr(ts, "probe_process_group", lambda _pgid: ts.GroupProbe(members=(), complete=False))
    report = _recover(root, apply=True)
    assert _entry(report, scratch.invocation_id)["reason"] == "group_probe_unknown"
    assert scratch.path.is_dir()


# --------------------------------------------------------------------------
# age gates
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("free_gb", "age_s", "expected"),
    [
        (100.0, ts.DEFAULT_MIN_AGE_S - 1, "too_young"),
        (100.0, ts.DEFAULT_MIN_AGE_S, "would_reap"),
        (14.9, ts.DEFAULT_PRESSURE_MIN_AGE_S - 1, "too_young"),
        (14.9, ts.DEFAULT_PRESSURE_MIN_AGE_S, "would_reap"),
        (15.0, ts.DEFAULT_PRESSURE_MIN_AGE_S, "too_young"),
    ],
)
def test_age_gate_boundaries(tmp_path: Path, monkeypatch, free_gb: float, age_s: int, expected: str) -> None:
    root = tmp_path / "root"
    path = _plant_dead_owner(root)
    _age_tree(path, age_s)
    monkeypatch.setattr(ts, "free_space_gb", lambda _p: free_gb)
    report = ts.recover_orphans(root=root, now=time.time())
    entry = _entry(report, path.name)
    assert report["disk_pressure"] is (free_gb < ts.DEFAULT_MIN_FREE_GB)
    assert entry["action"] == ("would_reap" if expected == "would_reap" else "preserved")
    if expected == "too_young":
        assert entry["reason"] == "too_young"


def test_pressure_never_weakens_liveness_proof(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "root"
    live = ts.allocate("live", root=root)
    try:
        _age_tree(live.path, 10 * 3600)
        monkeypatch.setattr(ts, "free_space_gb", lambda _p: 1.0)
        report = ts.recover_orphans(root=root, apply=True)
        assert _entry(report, live.invocation_id)["reason"] == "in_use"
        live.preserve()
        report = ts.recover_orphans(root=root, apply=True)
        assert _entry(report, live.invocation_id)["reason"] == "owner_alive"
        assert live.path.is_dir()
    finally:
        if not live._released:
            live.preserve()


def test_recent_payload_write_refreshes_age(tmp_path: Path) -> None:
    root = tmp_path / "root"
    path = _plant_dead_owner(root)
    _age_tree(path, 10 * 3600)
    deep = path / ts.PAYLOAD_DIRNAME / "nested"
    deep.mkdir()
    (deep / "fresh.bin").write_bytes(b"fresh")
    os.utime(path, (time.time() - 10 * 3600, time.time() - 10 * 3600))
    report = ts.recover_orphans(root=root, now=time.time())
    assert _entry(report, path.name)["reason"] == "too_young"


# --------------------------------------------------------------------------
# metadata, containment and mutation-freedom
# --------------------------------------------------------------------------


def test_dry_run_is_mutation_free(tmp_path: Path) -> None:
    root = tmp_path / "root"
    path = _plant_dead_owner(root)
    _age_tree(path, 10 * 3600)
    before = {p: p.lstat().st_mtime for p in [path, *path.rglob("*")]}
    report = ts.recover_orphans(root=root)
    assert _entry(report, path.name)["action"] == "would_reap"
    assert report["reaped"] == 0
    assert {p: p.lstat().st_mtime for p in [path, *path.rglob("*")]} == before


def test_malformed_foreign_and_symlinked_metadata_are_preserved(tmp_path: Path) -> None:
    root = tmp_path / "root"
    namespace = ts.ensure_namespace(root)
    decoy = tmp_path / "decoy"
    decoy.mkdir()
    (decoy / "precious").write_text("keep")

    garbage = _plant_dead_owner(root, "garbage")
    (garbage / ts.LEASE_FILENAME).write_text("{not json")

    no_lease = namespace / "no-lease.abc"
    no_lease.mkdir()
    (no_lease / "big").write_bytes(b"z" * 10)

    linked_lease = _plant_dead_owner(root, "linked")
    genuine = tmp_path / "genuine-lease.json"
    genuine.write_bytes((linked_lease / ts.LEASE_FILENAME).read_bytes())
    (linked_lease / ts.LEASE_FILENAME).unlink()
    (linked_lease / ts.LEASE_FILENAME).symlink_to(genuine)

    foreign = _plant_dead_owner(root, "foreign")
    lease = json.loads((foreign / ts.LEASE_FILENAME).read_text())
    lease["uid"] = os.geteuid() + 1
    (foreign / ts.LEASE_FILENAME).write_text(json.dumps(lease))

    wrong_dir = _plant_dead_owner(root, "wrongdir")
    lease = json.loads((wrong_dir / ts.LEASE_FILENAME).read_text())
    lease["dir"]["ino"] += 1
    (wrong_dir / ts.LEASE_FILENAME).write_text(json.dumps(lease))

    (namespace / "entry-symlink").symlink_to(decoy)
    (namespace / "stray-file").write_text("x")
    old_schema = _plant_dead_owner(root, "oldschema")
    lease = json.loads((old_schema / ts.LEASE_FILENAME).read_text())
    lease["schema_version"] = 99
    (old_schema / ts.LEASE_FILENAME).write_text(json.dumps(lease))

    for child in namespace.iterdir():
        if child.is_dir() and not child.is_symlink():
            _age_tree(child, 10 * 3600)

    report = ts.recover_orphans(root=root, apply=True)
    reasons = {entry["name"]: entry["reason"] for entry in report["entries"]}
    assert reasons[garbage.name] == "malformed_metadata"
    assert reasons["no-lease.abc"] == "malformed_metadata"
    assert reasons[linked_lease.name] == "malformed_metadata"
    assert reasons[foreign.name] == "foreign_owner"
    assert reasons[wrong_dir.name] == "metadata_identity_mismatch"
    assert reasons["entry-symlink"] == "symlink"
    assert reasons["stray-file"] == "not_directory"
    assert reasons[old_schema.name] == "malformed_metadata"
    assert report["reaped"] == 0
    assert report["errors"] == 0
    assert report["preserved"] == 8
    for child in (garbage, no_lease, linked_lease, foreign, wrong_dir, old_schema):
        assert child.is_dir()
    assert (decoy / "precious").read_text() == "keep"
    assert (namespace / "entry-symlink").is_symlink()


def test_symlink_inside_scratch_is_unlinked_not_followed(tmp_path: Path) -> None:
    root = tmp_path / "root"
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "keep.txt").write_text("keep")
    path = _plant_dead_owner(root)
    (path / ts.PAYLOAD_DIRNAME / "escape").symlink_to(outside)
    (path / ts.PAYLOAD_DIRNAME / "escape-file").symlink_to(outside / "keep.txt")
    report = _recover(root, apply=True)
    assert _entry(report, path.name)["action"] == "reaped"
    assert not path.exists()
    assert (outside / "keep.txt").read_text() == "keep"


def test_mount_point_below_scratch_blocks_deletion(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "root"
    path = _plant_dead_owner(root)
    mounted = path / ts.PAYLOAD_DIRNAME / "mnt"
    mounted.mkdir()
    (mounted / "data").write_text("x")
    monkeypatch.setattr(ts, "mount_points", lambda: frozenset({str(mounted)}))
    report = _recover(root, apply=True)
    entry = _entry(report, path.name)
    assert entry["action"] == "error"
    assert "mount point" in entry["reason"]
    assert (mounted / "data").is_file()
    assert report["errors"] == 1


def test_foreign_device_directory_blocks_deletion(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "root"
    path = _plant_dead_owner(root)
    original_fstat = ts.os.fstat
    inv_ino = path.stat().st_ino

    def fake_fstat(fd):
        st = original_fstat(fd)
        if st.st_ino == inv_ino:
            values = list(st)
            values[2] = st.st_dev + 1  # st_dev index in the stat_result tuple
            return os.stat_result(values)
        return st

    monkeypatch.setattr(ts.os, "fstat", fake_fstat)
    report = _recover(root, apply=True)
    assert _entry(report, path.name)["action"] == "preserved"
    assert path.is_dir()


def test_namespace_replaced_by_symlink_is_refused(tmp_path: Path) -> None:
    root = tmp_path / "root"
    decoy_root = tmp_path / "decoy"
    _plant_dead_owner(decoy_root)
    root.mkdir()
    (root / ts.NAMESPACE_DIRNAME).symlink_to(decoy_root / ts.NAMESPACE_DIRNAME)
    report = ts.recover_orphans(root=root, apply=True, min_age_s=0)
    assert report["errors"] == 1
    assert report["entries"][0]["reason"] == "namespace_untrusted"
    assert list((decoy_root / ts.NAMESPACE_DIRNAME).iterdir())


def test_entry_swapped_for_symlink_before_deletion_is_refused(tmp_path: Path) -> None:
    root = tmp_path / "root"
    path = _plant_dead_owner(root)
    st = path.stat()
    decoy = tmp_path / "decoy"
    decoy.mkdir()
    (decoy / "keep").write_text("keep")
    ns_fd = os.open(_namespace(root), os.O_RDONLY | os.O_DIRECTORY)
    try:
        path.rename(tmp_path / "moved-away")
        (_namespace(root) / path.name).symlink_to(decoy)
        with pytest.raises(ts.ContainmentError):
            ts._remove_invocation_dir(
                ns_fd, path.name, namespace=_namespace(root), expected_dev=st.st_dev, expected_ino=st.st_ino
            )
    finally:
        os.close(ns_fd)
    assert (decoy / "keep").is_file()


def test_owner_remove_refuses_on_identity_change(tmp_path: Path) -> None:
    root = tmp_path / "root"
    scratch = ts.allocate("swap", root=root)
    (scratch.path / ts.LEASE_FILENAME).write_text(
        json.dumps({**scratch.lease, "invocation_id": "someone-else"}), encoding="utf-8"
    )
    with pytest.raises(ts.TaskScratchError, match="lease no longer matches"):
        scratch.remove()
    assert scratch.path.is_dir()
    scratch.preserve()


def test_managed_paths_cover_namespace_roots_and_ancestors(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(tmp_path / "scratch"))
    monkeypatch.setenv("LU_RUNTIME_TMP_BASE_ROOT", str(tmp_path / "base"))
    managed = ts.managed_scratch_paths()
    assert tmp_path / "scratch" in managed
    assert tmp_path / "scratch" / ts.NAMESPACE_DIRNAME in managed
    assert tmp_path / "base" in managed
    assert tmp_path in managed
    assert Path("/") in managed
    assert ts.DEFAULT_SCRATCH_ROOT in managed


# --------------------------------------------------------------------------
# #8738 r2: fd-relative mount / identity proofs on every destructive step
# --------------------------------------------------------------------------


def _remove_planted(root: Path, path: Path) -> None:
    st = path.stat()
    ns_fd = os.open(_namespace(root), os.O_RDONLY | os.O_DIRECTORY)
    try:
        ts._remove_invocation_dir(
            ns_fd, path.name, namespace=_namespace(root), expected_dev=st.st_dev, expected_ino=st.st_ino
        )
    finally:
        os.close(ns_fd)


def _fd_ino(fd: int) -> int:
    return os.fstat(fd).st_ino


def test_fd_mount_id_reads_fdinfo_and_matches_mountinfo(tmp_path: Path) -> None:
    fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        mount_id = ts.fd_mount_id(fd)
    finally:
        os.close(fd)
    assert isinstance(mount_id, int)
    ids = {int(line.split(" ")[0]) for line in Path("/proc/self/mountinfo").read_text().splitlines() if line}
    assert mount_id in ids
    assert ts.fd_mount_id(10_000_000) is None  # not an open descriptor: unknown, never a guess


def test_same_device_bind_mount_placed_after_snapshot_is_refused(tmp_path: Path, monkeypatch) -> None:
    """A bind mount of the same filesystem keeps st_dev; only the per-fd mount id exposes it.

    The path-based mountinfo snapshot is frozen to "nothing mounted" (as if the
    mount landed after that scan); the descriptor opened for the descent must
    still refuse.
    """
    root = tmp_path / "root"
    path = _plant_dead_owner(root)
    mounted = path / ts.PAYLOAD_DIRNAME / "mnt"
    mounted.mkdir()
    (mounted / "precious").write_text("keep")
    (path / ts.PAYLOAD_DIRNAME / "sibling").write_text("x")
    mounted_ino = mounted.stat().st_ino
    monkeypatch.setattr(ts, "mount_points", lambda: frozenset())  # stale snapshot: mount not yet visible
    real_mount_id = ts.fd_mount_id

    def bind_mounted(fd: int):
        real = real_mount_id(fd)
        return real + 1000 if real is not None and _fd_ino(fd) == mounted_ino else real

    monkeypatch.setattr(ts, "fd_mount_id", bind_mounted)
    with pytest.raises(ts.ContainmentError, match="mount point"):
        _remove_planted(root, path)
    assert (mounted / "precious").read_text() == "keep"
    assert path.is_dir()

    report = _recover(root, apply=True)
    entry = _entry(report, path.name)
    assert entry["action"] == "preserved"
    assert entry["reason"] == "mount_boundary"
    assert (mounted / "precious").read_text() == "keep"


def _userns_bind_mount_available() -> bool:
    try:
        completed = subprocess.run(["unshare", "-Urm", "true"], capture_output=True, timeout=10, check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False
    return completed.returncode == 0


_REAL_BIND_MOUNT_SCRIPT = """
import os, subprocess, sys
sys.path.insert(0, sys.argv[1])
from pathlib import Path
from scripts.common import task_scratch as ts
work = Path(sys.argv[2])
root = work / "root"
scratch = ts.allocate("bind", root=root)
(scratch.payload_dir / "sibling").write_text("x")
mounted = scratch.payload_dir / "mnt"
mounted.mkdir()
decoy = work / "decoy"
decoy.mkdir()
(decoy / "precious").write_text("keep")
snapshot = ts.mount_points()  # taken BEFORE the mount lands
ts.mount_points = lambda: snapshot
subprocess.run(["mount", "--bind", str(decoy), str(mounted)], check=True)
assert (mounted / "precious").read_text() == "keep"
st = scratch.path.stat()
ns_fd = os.open(scratch.namespace, os.O_RDONLY | os.O_DIRECTORY)
try:
    ts._remove_invocation_dir(ns_fd, scratch.path.name, namespace=scratch.namespace, expected_dev=st.st_dev, expected_ino=st.st_ino)
except ts.ContainmentError as exc:
    print("refused:", exc)
else:
    raise SystemExit("deleted through a same-device bind mount")
finally:
    os.close(ns_fd)
assert (decoy / "precious").read_text() == "keep", "bind-mounted content was destroyed"
assert (mounted / "precious").read_text() == "keep"
subprocess.run(["umount", str(mounted)], check=True)
assert (decoy / "precious").read_text() == "keep"
print("ok")
"""


@pytest.mark.skipif(not _userns_bind_mount_available(), reason="needs unprivileged user+mount namespaces")
def test_real_same_device_bind_mount_after_snapshot_is_refused(tmp_path: Path) -> None:
    completed = subprocess.run(
        ["unshare", "-Urm", sys.executable, "-c", _REAL_BIND_MOUNT_SCRIPT, str(REPO_ROOT), str(tmp_path)],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "refused:" in completed.stdout and "mount point" in completed.stdout
    assert (tmp_path / "decoy" / "precious").read_text() == "keep"


def test_directory_swapped_after_emptying_is_not_rmdired(tmp_path: Path, monkeypatch) -> None:
    """Between emptying a subdirectory and rmdir, its name is re-pointed at another directory."""
    root = tmp_path / "root"
    path = _plant_dead_owner(root)
    victim = path / ts.PAYLOAD_DIRNAME / "sub"
    victim.mkdir()
    (victim / "f").write_text("x")
    victim_ino = victim.stat().st_ino
    moved = tmp_path / "moved-away"
    original = ts._rmtree_fd

    def racy_rmtree(dir_fd: int, **kwargs):
        original(dir_fd, **kwargs)
        if _fd_ino(dir_fd) == victim_ino:
            victim.rename(moved)
            victim.mkdir()  # a different (empty) directory now answers to the same name
            (victim / "unrelated").write_text("y")

    monkeypatch.setattr(ts, "_rmtree_fd", racy_rmtree)
    with pytest.raises(ts.ContainmentError, match="replaced before rmdir"):
        _remove_planted(root, path)
    assert (victim / "unrelated").read_text() == "y"
    assert moved.is_dir() and not any(moved.iterdir())


def test_rmdir_of_swapped_directory_is_detected_after_the_fact(tmp_path: Path, monkeypatch) -> None:
    """Linux has no fd-based rmdir; a swap inside the last window is reported, not counted as clean."""
    root = tmp_path / "root"
    path = _plant_dead_owner(root)
    victim = path / ts.PAYLOAD_DIRNAME / "sub"
    victim.mkdir()
    moved = tmp_path / "moved-away"
    real_rmdir = os.rmdir

    def swapping_rmdir(name, *args, dir_fd=None, **kwargs):
        if dir_fd is not None and name == victim.name and _fd_ino(dir_fd) == victim.parent.stat().st_ino:
            victim.rename(moved)
            victim.mkdir()
        return real_rmdir(name, *args, dir_fd=dir_fd, **kwargs)

    monkeypatch.setattr(ts.os, "rmdir", swapping_rmdir)
    with pytest.raises(ts.ContainmentError, match="different directory"):
        _remove_planted(root, path)
    assert moved.is_dir()  # the directory we actually emptied and held is untouched by rmdir
    assert not victim.exists()  # only the swapped-in empty directory went


def test_top_level_swap_before_final_rmdir_is_refused(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "root"
    path = _plant_dead_owner(root)
    moved = tmp_path / "moved-away"
    original = ts._rmtree_fd
    top_ino = path.stat().st_ino

    def racy_rmtree(dir_fd: int, **kwargs):
        original(dir_fd, **kwargs)
        if _fd_ino(dir_fd) == top_ino:
            path.rename(moved)
            path.mkdir()
            (path / "someone-elses").write_text("z")

    monkeypatch.setattr(ts, "_rmtree_fd", racy_rmtree)
    with pytest.raises(ts.ContainmentError, match="replaced before rmdir"):
        _remove_planted(root, path)
    assert (path / "someone-elses").read_text() == "z"


@pytest.mark.parametrize("missing", ["mount_points", "fd_mount_id"])
def test_unavailable_mount_information_fails_closed(tmp_path: Path, monkeypatch, missing: str) -> None:
    root = tmp_path / "root"
    path = _plant_dead_owner(root)
    monkeypatch.setattr(ts, missing, lambda *_a: None)
    with pytest.raises(ts.ContainmentError, match="mount information unavailable"):
        _remove_planted(root, path)
    assert (path / ts.PAYLOAD_DIRNAME / "atlas.db").is_file()

    report = _recover(root, apply=True)
    assert report["reaped"] == 0
    assert path.is_dir()
    if missing == "fd_mount_id":
        assert report["errors"] == 1
        assert report["entries"][0]["reason"] == "mount_info_unavailable"
    else:
        entry = _entry(report, path.name)
        assert entry["action"] == "error"
        assert "mount information unavailable" in entry["reason"]


def test_owner_cleanup_preserves_when_mount_information_unavailable(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "root"
    monkeypatch.setattr(ts, "fd_mount_id", lambda _fd: None)
    outcome = ts.run_task(
        "nomount", ["bash", "-c", 'echo x > "$LU_TASK_SCRATCH_DIR/f"'], root=root, log=lambda _m: None
    )
    assert outcome.exit_status == 0
    assert outcome.action == "preserved"
    assert "mount information unavailable" in outcome.detail
    assert (outcome.scratch_path / ts.PAYLOAD_DIRNAME / "f").is_file()
    assert _leases(root)[outcome.invocation_id]["state"] == "preserved"


def test_symlink_and_cross_device_refusals_are_kept(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "root"
    path = _plant_dead_owner(root)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "keep").write_text("keep")
    (path / ts.PAYLOAD_DIRNAME / "link").symlink_to(outside)
    foreign = path / ts.PAYLOAD_DIRNAME / "foreign"
    foreign.mkdir()
    (foreign / "keep").write_text("keep")
    foreign_ino = foreign.stat().st_ino
    real_fstat = ts.os.fstat

    def other_device(fd):
        st = real_fstat(fd)
        if st.st_ino == foreign_ino:
            values = list(st)
            values[2] = st.st_dev + 1
            return os.stat_result(values)
        return st

    monkeypatch.setattr(ts.os, "fstat", other_device)
    # fstat is the only hook available; the faked device also breaks the
    # identity match, and whichever check fires first, nothing is deleted.
    with pytest.raises(ts.ContainmentError, match=r"changed identity|device boundary"):
        _remove_planted(root, path)
    assert (foreign / "keep").read_text() == "keep"
    assert (outside / "keep").read_text() == "keep"
