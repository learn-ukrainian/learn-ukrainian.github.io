"""Task-owned disposable scratch directories with provable orphan recovery (#8738).

Large ad-hoc Atlas / QA runs (410k synthetic Atlas DBs, runtime-shard
exports, delegated QA scratch) used to write straight into ``/tmp`` under
hand-picked names. Nothing tied those files to the process that made them, so
the scheduled sweep could neither prove they were abandoned nor drain them,
and multi-gigabyte residue had to be removed by hand.

This module gives every wrapper invocation one unique directory under the
``task-scratch`` namespace below the disk-backed fleet scratch root
(:mod:`scripts.common.scratch`)::

    <scratch root>/task-scratch/<task>.<random>/
        lease.json    versioned owner metadata (regular file, 0600)
        lease.lock    flock held by the owning wrapper for its lifetime
        scratch/      the payload directory exposed as $LU_TASK_SCRATCH_DIR

Ownership and liveness are recorded, never inferred from a filename:

* the lease binds the task id, the unique invocation id, the directory's
  device/inode, the owner's uid, the wrapper pid + ``/proc`` start time +
  kernel boot id, and — once spawned — the child process-group id + start
  time;
* the owner metadata is persisted *before* the payload directory exists;
* the child starts in a new session behind a launch gate: it may not run the
  payload until the wrapper has durably recorded its identity. If the wrapper
  dies first, the gate reads EOF and the child exits without running;
* the owning wrapper removes its lease only while holding the lock, after
  re-checking directory identity and proving its child group is gone;
* scheduled recovery additionally proves the recorded owner dead (pid absent,
  start time mismatch, or a different boot id). A live group leader, any
  surviving member of the recorded group, a reused numeric group id, or an
  unknown probe all preserve the directory. Recovery never sends signals.

Deletion is fd-relative (``O_NOFOLLOW`` + ``dir_fd``), refuses to cross mount
boundaries, and re-verifies the invocation directory's device/inode against
the lease immediately before it starts.

Linux ``/proc`` is required for every liveness proof; hosts without it only
ever report "unknown", which preserves.
"""

from __future__ import annotations

import contextlib
import errno
import fcntl
import json
import os
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts.common.acp_runtime_lock import owner_alive, process_start_time
from scripts.common.scratch import (
    DEFAULT_SCRATCH_ROOT,
    ensure_scratch_root,
    fallback_scratch_root,
    resolve_scratch_root,
)

NAMESPACE_DIRNAME = "task-scratch"
LEASE_FILENAME = "lease.json"
LOCK_FILENAME = "lease.lock"
PAYLOAD_DIRNAME = "scratch"
EVIDENCE_DIRNAME = "evidence"
LEASE_SCHEMA_VERSION = 1
LEASE_MAX_BYTES = 64 * 1024
EVIDENCE_MAX_BYTES = 16 * 1024 * 1024

SCRATCH_DIR_ENV_VAR = "LU_TASK_SCRATCH_DIR"
TASK_ID_ENV_VAR = "LU_TASK_SCRATCH_TASK_ID"
INVOCATION_ID_ENV_VAR = "LU_TASK_SCRATCH_INVOCATION_ID"
FAULT_ENV_VAR = "LU_TASK_SCRATCH_FAULT"
FAULT_KILL_BEFORE_RELEASE = "kill-before-release"

# Orphan age gates (#8738): 2h after the newest directory/metadata change
# normally; 30m when the scratch volume has under 15 GiB free. Pressure only
# ever shortens the age gate — identity and liveness proofs are unchanged.
DEFAULT_MIN_AGE_S = 2 * 60 * 60
DEFAULT_PRESSURE_MIN_AGE_S = 30 * 60
DEFAULT_MIN_FREE_GB = 15.0

DEFAULT_GROUP_GRACE_S = 15.0
DEFAULT_KILL_AFTER_S = 30.0
GATE_ABORT_EXIT = 125
EXEC_FAILED_EXIT = 127

_PROC_ROOT = Path("/proc")
_BOOT_ID_PATH = Path("/proc/sys/kernel/random/boot_id")
_DIR_OPEN_FLAGS = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
_TASK_ID_SAFE = re.compile(r"[^A-Za-z0-9._-]+")

_FORWARDED_SIGNALS = (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)

# The child runs this shim first. It blocks on the gate pipe until the wrapper
# has durably recorded the child's identity; EOF (wrapper died) means "exit
# without running the payload". Only then does it exec the real argv, in
# place, so the recorded pid/start time stay those of the payload process.
_GATE_SHIM = (
    "import os, signal, sys\n"
    "signal.signal(signal.SIGINT, signal.SIG_DFL)\n"
    "fd = int(sys.argv[1])\n"
    "try:\n"
    "    token = os.read(fd, 1)\n"
    "except OSError:\n"
    "    token = b''\n"
    f"if token != b'G':\n    os._exit({GATE_ABORT_EXIT})\n"
    "os.close(fd)\n"
    "try:\n"
    "    os.execvp(sys.argv[2], sys.argv[2:])\n"
    "except OSError as exc:\n"
    "    sys.stderr.write(f'task-scratch: cannot execute {sys.argv[2]!r}: {exc}\\n')\n"
    "    sys.stderr.flush()\n"
    f"    os._exit({EXEC_FAILED_EXIT})\n"
)


class TaskScratchError(RuntimeError):
    """Raised when a task-scratch lifecycle guard cannot be satisfied."""


class ContainmentError(TaskScratchError):
    """Raised when a deletion would leave the verified invocation directory."""


# --------------------------------------------------------------------------
# Process identity probes
# --------------------------------------------------------------------------


def current_boot_id() -> str | None:
    """Return the kernel boot id, or ``None`` when it cannot be read."""
    try:
        value = _BOOT_ID_PATH.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return value or None


@dataclass(frozen=True)
class GroupProbe:
    """Result of enumerating the members of one process group.

    ``complete`` is False when ``/proc`` could not be enumerated reliably;
    callers must treat that as unknown, never as "empty".
    """

    members: tuple[int, ...]
    complete: bool


def _stat_fields_after_comm(stat_text: str) -> list[str] | None:
    end = stat_text.rfind(")")
    if end < 0:
        return None
    return stat_text[end + 2 :].split()


def probe_process_group(pgid: int, *, proc_root: Path = _PROC_ROOT) -> GroupProbe:
    """Enumerate every live pid whose process group is ``pgid``."""
    if pgid <= 0 or not proc_root.is_dir():
        return GroupProbe(members=(), complete=False)
    members: list[int] = []
    complete = True
    try:
        entries = list(proc_root.iterdir())
    except OSError:
        return GroupProbe(members=(), complete=False)
    for entry in entries:
        if not entry.name.isdigit():
            continue
        try:
            fields = _stat_fields_after_comm((entry / "stat").read_text(encoding="utf-8", errors="replace"))
        except FileNotFoundError:
            continue  # exited between listing and read
        except ProcessLookupError:
            continue
        except OSError:
            complete = False
            continue
        if fields is None or len(fields) < 3:
            complete = False
            continue
        try:
            entry_pgid = int(fields[2])
        except ValueError:
            complete = False
            continue
        if entry_pgid == pgid:
            members.append(int(entry.name))
    return GroupProbe(members=tuple(sorted(members)), complete=complete)


def _pid_exists(pid: int, *, proc_root: Path = _PROC_ROOT) -> bool | None:
    if pid <= 0:
        return None
    if not proc_root.is_dir():
        return None
    return (proc_root / str(pid)).is_dir()


def free_space_gb(path: Path) -> float | None:
    """Return free space in GiB for the volume containing ``path``."""
    try:
        usage = shutil.disk_usage(path)
    except OSError:
        return None
    return usage.free / (1024**3)


# --------------------------------------------------------------------------
# Namespace + lease metadata
# --------------------------------------------------------------------------


def task_scratch_namespace(root: Path | None = None) -> Path:
    """Return the managed namespace path (may not exist yet)."""
    base = root if root is not None else resolve_scratch_root()
    return base / NAMESPACE_DIRNAME


def managed_scratch_paths() -> set[Path]:
    """Return every path a legacy sweep must never treat as residue.

    Covers the managed namespace under every scratch root the fleet resolves
    (current, default, fallback, dispatcher base), the roots themselves, and
    all of their ancestors. Paths are lexically absolute; callers compare
    against resolved candidates where possible.
    """
    roots: list[Path] = [resolve_scratch_root(), DEFAULT_SCRATCH_ROOT, fallback_scratch_root()]
    base_override = os.environ.get("LU_RUNTIME_TMP_BASE_ROOT", "").strip()
    if base_override:
        roots.append(Path(base_override))
    protected: set[Path] = set()
    for root in roots:
        candidates = [Path(os.path.abspath(str(root)))]
        with contextlib.suppress(OSError):
            candidates.append(root.resolve())
        for candidate in candidates:
            protected.add(candidate)
            protected.add(candidate / NAMESPACE_DIRNAME)
            protected.update(candidate.parents)
    return protected


def _sanitize_task_id(task_id: str) -> str:
    cleaned = _TASK_ID_SAFE.sub("-", task_id.strip()).strip("-.")
    if not cleaned:
        raise TaskScratchError("task id must contain at least one of [A-Za-z0-9._-]")
    return cleaned[:48]


def _verify_private_dir(path: Path, *, what: str) -> os.stat_result:
    try:
        st = path.lstat()
    except OSError as exc:
        raise TaskScratchError(f"{what} is not accessible: {path}: {exc}") from exc
    if stat.S_ISLNK(st.st_mode):
        raise TaskScratchError(f"{what} is a symlink, refusing: {path}")
    if not stat.S_ISDIR(st.st_mode):
        raise TaskScratchError(f"{what} is not a directory: {path}")
    if st.st_uid != os.geteuid():
        raise TaskScratchError(f"{what} is owned by uid {st.st_uid}, not {os.geteuid()}: {path}")
    return st


def ensure_namespace(root: Path | None = None) -> Path:
    """Create (or validate) the owner-only managed namespace and return it."""
    if root is None:
        base = ensure_scratch_root()
    else:
        base = root
        base.mkdir(parents=True, exist_ok=True)
    namespace = base / NAMESPACE_DIRNAME
    with contextlib.suppress(FileExistsError):
        namespace.mkdir(mode=0o700)
    st = _verify_private_dir(namespace, what="task-scratch namespace")
    if stat.S_IMODE(st.st_mode) & 0o077:
        os.chmod(namespace, 0o700)
    return namespace


def _write_lease_at(dir_fd: int, lease: Mapping[str, Any]) -> None:
    """Atomically persist ``lease.json`` inside the directory behind ``dir_fd``."""
    tmp_name = f".{LEASE_FILENAME}.tmp"
    with contextlib.suppress(FileNotFoundError):
        os.unlink(tmp_name, dir_fd=dir_fd)
    fd = os.open(tmp_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600, dir_fd=dir_fd)
    try:
        payload = json.dumps(dict(lease), sort_keys=True, indent=2).encode("utf-8") + b"\n"
        os.write(fd, payload)
        os.fsync(fd)
    finally:
        os.close(fd)
    os.rename(tmp_name, LEASE_FILENAME, src_dir_fd=dir_fd, dst_dir_fd=dir_fd)
    os.fsync(dir_fd)


def _read_regular_owned_file(dir_fd: int, name: str, *, max_bytes: int) -> bytes | None:
    """Read a regular, owner-owned, non-symlink file relative to ``dir_fd``."""
    try:
        fd = os.open(name, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0), dir_fd=dir_fd)
    except OSError:
        return None
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_uid != os.geteuid() or st.st_size > max_bytes:
            return None
        chunks: list[bytes] = []
        remaining = max_bytes + 1
        while remaining > 0:
            chunk = os.read(fd, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        data = b"".join(chunks)
        if len(data) > max_bytes:
            return None
        return data
    except OSError:
        return None
    finally:
        os.close(fd)


def _as_optional_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("expected integer")
    return value


def parse_lease(raw: bytes | None) -> dict[str, Any] | None:
    """Return a validated lease dictionary, or ``None`` for anything malformed."""
    if not raw:
        return None
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    try:
        if payload.get("schema_version") != LEASE_SCHEMA_VERSION:
            return None
        if payload.get("kind") != NAMESPACE_DIRNAME:
            return None
        task_id = payload.get("task_id")
        invocation_id = payload.get("invocation_id")
        if not isinstance(task_id, str) or not task_id or not isinstance(invocation_id, str) or not invocation_id:
            return None
        directory = payload.get("dir")
        owner = payload.get("owner")
        if not isinstance(directory, dict) or not isinstance(owner, dict):
            return None
        lease: dict[str, Any] = {
            "schema_version": LEASE_SCHEMA_VERSION,
            "kind": NAMESPACE_DIRNAME,
            "task_id": task_id,
            "invocation_id": invocation_id,
            "uid": int(payload["uid"]),
            "dir": {"dev": int(directory["dev"]), "ino": int(directory["ino"])},
            "owner": {
                "pid": int(owner["pid"]),
                "start_time": _as_optional_int(owner.get("start_time")),
                "boot_id": owner.get("boot_id") if isinstance(owner.get("boot_id"), str) else None,
            },
            "child": None,
            "state": str(payload.get("state") or "registered"),
            "created_at": float(payload.get("created_at") or 0.0),
        }
        child = payload.get("child")
        if child is not None:
            if not isinstance(child, dict):
                return None
            lease["child"] = {
                "pid": int(child["pid"]),
                "pgid": int(child["pgid"]),
                "start_time": _as_optional_int(child.get("start_time")),
            }
    except (KeyError, TypeError, ValueError):
        return None
    return lease


# --------------------------------------------------------------------------
# Guarded, fd-relative deletion
# --------------------------------------------------------------------------

_MOUNTINFO_PATH = Path("/proc/self/mountinfo")


def _unescape_mountinfo(field_text: str) -> str:
    return re.sub(r"\\([0-7]{3})", lambda m: chr(int(m.group(1), 8)), field_text)


def mount_points() -> frozenset[str] | None:
    """Return every mount point visible to this process, or ``None`` if unknown.

    ``st_dev`` alone misses bind mounts of the same filesystem, so deletion
    also refuses any directory that is a mount point by path.
    """
    try:
        text = _MOUNTINFO_PATH.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    points: set[str] = set()
    for line in text.splitlines():
        fields = line.split(" ")
        if len(fields) < 5:
            continue
        points.add(_unescape_mountinfo(fields[4]))
    return frozenset(points)


def _mounts_below(logical: Path, mounts: frozenset[str] | None) -> list[str]:
    if mounts is None:
        return []
    prefix = str(logical).rstrip("/") + "/"
    return sorted(point for point in mounts if point == str(logical) or point.startswith(prefix))


def _open_dir_at(dir_fd: int, name: str) -> int:
    return os.open(name, _DIR_OPEN_FLAGS | getattr(os, "O_CLOEXEC", 0), dir_fd=dir_fd)


def _rmtree_fd(dir_fd: int, *, device: int) -> None:
    """Remove every entry below ``dir_fd`` without leaving ``device``.

    Symlinks are unlinked, never followed. A directory on another device is a
    mount point: refuse instead of descending. Owner-only permission barriers
    are repaired once (owner rwx) and retried.
    """
    with os.scandir(dir_fd) as it:
        entries = [(entry.name, entry.stat(follow_symlinks=False)) for entry in it]
    for name, st in entries:
        if stat.S_ISDIR(st.st_mode):
            if st.st_dev != device:
                raise ContainmentError(f"refusing to cross a mount boundary at {name!r}")
            try:
                child_fd = _open_dir_at(dir_fd, name)
            except PermissionError:
                os.chmod(name, stat.S_IMODE(st.st_mode) | stat.S_IRWXU, dir_fd=dir_fd, follow_symlinks=False)
                child_fd = _open_dir_at(dir_fd, name)
            try:
                child_st = os.fstat(child_fd)
                if (child_st.st_dev, child_st.st_ino) != (st.st_dev, st.st_ino):
                    raise ContainmentError(f"directory {name!r} changed identity during deletion")
                _rmtree_fd(child_fd, device=device)
            finally:
                os.close(child_fd)
            os.rmdir(name, dir_fd=dir_fd)
        else:
            os.unlink(name, dir_fd=dir_fd)


def _remove_invocation_dir(
    namespace_fd: int,
    name: str,
    *,
    namespace: Path,
    expected_dev: int,
    expected_ino: int,
) -> None:
    """Delete one direct child of the namespace after re-verifying its identity."""
    if "/" in name or name in {"", ".", ".."}:
        raise ContainmentError(f"invalid invocation directory name {name!r}")
    below = _mounts_below(namespace / name, mount_points())
    if below:
        raise ContainmentError(f"mount point(s) below {name!r}: {len(below)}")
    ns_st = os.fstat(namespace_fd)
    st = os.stat(name, dir_fd=namespace_fd, follow_symlinks=False)
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISDIR(st.st_mode):
        raise ContainmentError(f"{name!r} is not a plain directory")
    if (st.st_dev, st.st_ino) != (expected_dev, expected_ino):
        raise ContainmentError(f"{name!r} no longer matches its recorded device/inode")
    if st.st_uid != os.geteuid():
        raise ContainmentError(f"{name!r} is not owned by uid {os.geteuid()}")
    if st.st_dev != ns_st.st_dev:
        raise ContainmentError(f"{name!r} sits on a different device than the namespace")
    inv_fd = _open_dir_at(namespace_fd, name)
    try:
        inv_st = os.fstat(inv_fd)
        if (inv_st.st_dev, inv_st.st_ino) != (expected_dev, expected_ino):
            raise ContainmentError(f"{name!r} changed identity between check and open")
        _rmtree_fd(inv_fd, device=inv_st.st_dev)
    finally:
        os.close(inv_fd)
    os.rmdir(name, dir_fd=namespace_fd)


def _walk_stats(dir_fd: int, *, device: int) -> tuple[int, float]:
    """Return ``(bytes, newest_mtime)`` below ``dir_fd`` without crossing mounts."""
    total = 0
    newest = 0.0
    with os.scandir(dir_fd) as it:
        entries = [(entry.name, entry.stat(follow_symlinks=False)) for entry in it]
    for name, st in entries:
        newest = max(newest, st.st_mtime)
        if stat.S_ISDIR(st.st_mode):
            if st.st_dev != device:
                raise ContainmentError(f"mount boundary at {name!r}")
            child_fd = _open_dir_at(dir_fd, name)
            try:
                child_st = os.fstat(child_fd)
                if (child_st.st_dev, child_st.st_ino) != (st.st_dev, st.st_ino):
                    raise ContainmentError(f"directory {name!r} changed identity during walk")
                sub_bytes, sub_newest = _walk_stats(child_fd, device=device)
            finally:
                os.close(child_fd)
            total += sub_bytes
            newest = max(newest, sub_newest)
        else:
            total += st.st_size
    return total, newest


# --------------------------------------------------------------------------
# Owning wrapper side
# --------------------------------------------------------------------------


@dataclass
class TaskScratch:
    """One allocated invocation directory, owned by this process."""

    task_id: str
    invocation_id: str
    namespace: Path
    path: Path
    payload_dir: Path
    lease: dict[str, Any]
    _dir_fd: int = field(repr=False)
    _lock_fd: int = field(repr=False)
    _child: subprocess.Popen[bytes] | None = field(default=None, repr=False)
    _released: bool = field(default=False, repr=False)

    # -- environment ------------------------------------------------------

    def child_environment(self, base: Mapping[str, str] | None = None) -> dict[str, str]:
        env = dict(os.environ if base is None else base)
        payload = str(self.payload_dir)
        env["TMPDIR"] = payload
        env["TMP"] = payload
        env["TEMP"] = payload
        env[SCRATCH_DIR_ENV_VAR] = payload
        env[TASK_ID_ENV_VAR] = self.task_id
        env[INVOCATION_ID_ENV_VAR] = self.invocation_id
        return env

    # -- spawn ------------------------------------------------------------

    def spawn(
        self,
        argv: Sequence[str],
        *,
        env: Mapping[str, str] | None = None,
        cwd: Path | None = None,
        fault: str | None = None,
    ) -> subprocess.Popen[bytes]:
        """Start ``argv`` in a new session behind the launch gate.

        The child identity (pid == pgid, start time) is persisted to the lease
        before the gate opens. ``fault`` is a test-only hook that kills the
        wrapper between persisting and releasing, to prove the gate closes.
        """
        if self._child is not None:
            raise TaskScratchError("scratch already has a child")
        if not argv:
            raise TaskScratchError("argv must not be empty")
        gate_r, gate_w = os.pipe()
        try:
            shim_argv = [sys.executable, "-I", "-S", "-c", _GATE_SHIM, str(gate_r), *argv]
            proc = subprocess.Popen(
                shim_argv,
                env=self.child_environment(env),
                cwd=str(cwd) if cwd is not None else None,
                start_new_session=True,
                pass_fds=(gate_r,),
            )
        except BaseException:
            os.close(gate_w)
            raise
        finally:
            os.close(gate_r)
        try:
            start = process_start_time(proc.pid)
            if start is None:
                raise TaskScratchError("cannot record child start time (no /proc); refusing to release the child")
            self.lease["child"] = {"pid": proc.pid, "pgid": proc.pid, "start_time": start}
            self.lease["state"] = "running"
            _write_lease_at(self._dir_fd, self.lease)
            if fault == FAULT_KILL_BEFORE_RELEASE:
                os.kill(os.getpid(), signal.SIGKILL)
            os.write(gate_w, b"G")
        except BaseException:
            os.close(gate_w)
            proc.wait()
            raise
        os.close(gate_w)
        self._child = proc
        return proc

    @property
    def child(self) -> subprocess.Popen[bytes] | None:
        return self._child

    @property
    def child_pgid(self) -> int | None:
        child = self.lease.get("child")
        return int(child["pgid"]) if child else None

    # -- group control ----------------------------------------------------

    def signal_group(self, signum: int) -> bool:
        """Send ``signum`` to the owned process group; False when no group."""
        pgid = self.child_pgid
        if pgid is None:
            return False
        try:
            os.killpg(pgid, signum)
        except ProcessLookupError:
            return False
        return True

    def group_status(self) -> str:
        """Classify the recorded child group: ``absent``, ``members``, ``reused``, ``unknown``."""
        child = self.lease.get("child")
        if not child:
            return "absent"
        pgid = int(child["pgid"])
        probe = probe_process_group(pgid)
        if not probe.complete:
            return "unknown"
        if not probe.members:
            return "absent"
        leader_state = owner_alive(int(child["pid"]), child.get("start_time"))
        if leader_state is None:
            return "unknown"
        if leader_state is False and _pid_exists(int(child["pid"])) is True:
            # The leader pid exists with a different start time: the numeric
            # group id was reused by an unrelated process. Never kill it.
            return "reused"
        return "members"

    def wait_group_clear(self, *, grace_s: float, escalate: bool = True) -> str:
        """Wait for the owned group to drain, escalating TERM then KILL.

        Returns the final :meth:`group_status`.
        """
        status = self._poll_group("absent", timeout_s=grace_s)
        if status != "members" or not escalate:
            return status
        self.signal_group(signal.SIGTERM)
        status = self._poll_group("absent", timeout_s=grace_s)
        if status != "members":
            return status
        self.signal_group(signal.SIGKILL)
        return self._poll_group("absent", timeout_s=5.0)

    def _poll_group(self, target: str, *, timeout_s: float) -> str:
        deadline = time.monotonic() + max(0.0, timeout_s)
        while True:
            status = self.group_status()
            if status == target or status in {"unknown", "reused"}:
                return status
            if time.monotonic() >= deadline:
                return status
            time.sleep(0.05)

    # -- evidence + release -----------------------------------------------

    def export_evidence(self, destination: Path) -> dict[str, Any]:
        """Copy ``scratch/evidence`` (small, size-capped) to ``destination``."""
        source = self.payload_dir / EVIDENCE_DIRNAME
        report: dict[str, Any] = {"source_present": False, "files": 0, "bytes": 0, "destination": str(destination)}
        if not source.is_dir() or source.is_symlink():
            return report
        report["source_present"] = True
        total = 0
        files: list[tuple[Path, Path]] = []
        for path in sorted(source.rglob("*")):
            if path.is_symlink() or not path.is_file():
                continue
            total += path.stat().st_size
            if total > EVIDENCE_MAX_BYTES:
                raise TaskScratchError(f"evidence exceeds {EVIDENCE_MAX_BYTES} bytes; keep summaries small")
            files.append((path, path.relative_to(source)))
        destination.mkdir(parents=True, exist_ok=True)
        for src, rel in files:
            target = destination / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, target)
        report["files"] = len(files)
        report["bytes"] = total
        return report

    def verify_identity(self) -> None:
        """Confirm the directory behind our fd is still the one we allocated."""
        st = os.fstat(self._dir_fd)
        expected = self.lease["dir"]
        if (st.st_dev, st.st_ino) != (expected["dev"], expected["ino"]):
            raise TaskScratchError("invocation directory identity changed")
        lease = parse_lease(_read_regular_owned_file(self._dir_fd, LEASE_FILENAME, max_bytes=LEASE_MAX_BYTES))
        if lease is None or lease["invocation_id"] != self.invocation_id:
            raise TaskScratchError("lease no longer matches this invocation")

    def remove(self) -> None:
        """Delete this invocation directory. Requires an absent child group."""
        if self._released:
            raise TaskScratchError("scratch already released")
        status = self.group_status()
        if status != "absent":
            raise TaskScratchError(f"child group still present ({status}); preserving scratch")
        self.verify_identity()
        expected = self.lease["dir"]
        ns_fd = os.open(self.namespace, _DIR_OPEN_FLAGS | getattr(os, "O_CLOEXEC", 0))
        try:
            _remove_invocation_dir(
                ns_fd,
                self.path.name,
                namespace=self.namespace,
                expected_dev=expected["dev"],
                expected_ino=expected["ino"],
            )
        finally:
            os.close(ns_fd)
        self._close()

    def preserve(self) -> None:
        """Release the lock and fds without deleting anything."""
        if self._released:
            return
        self.lease["state"] = "preserved"
        with contextlib.suppress(OSError):
            _write_lease_at(self._dir_fd, self.lease)
        self._close()

    def _close(self) -> None:
        self._released = True
        for fd in (self._lock_fd, self._dir_fd):
            with contextlib.suppress(OSError):
                os.close(fd)


def allocate(task_id: str, *, root: Path | None = None) -> TaskScratch:
    """Allocate one unique, locked, owner-only invocation directory."""
    safe_id = _sanitize_task_id(task_id)
    namespace = ensure_namespace(root)
    path = Path(tempfile.mkdtemp(prefix=f"{safe_id}.", dir=namespace))
    os.chmod(path, 0o700)
    dir_fd = os.open(path, _DIR_OPEN_FLAGS | getattr(os, "O_CLOEXEC", 0))
    try:
        st = os.fstat(dir_fd)
        lock_fd = os.open(
            LOCK_FILENAME,
            os.O_RDWR | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
            0o600,
            dir_fd=dir_fd,
        )
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            lease: dict[str, Any] = {
                "schema_version": LEASE_SCHEMA_VERSION,
                "kind": NAMESPACE_DIRNAME,
                "task_id": task_id,
                "invocation_id": path.name,
                "uid": os.geteuid(),
                "dir": {"dev": st.st_dev, "ino": st.st_ino},
                "owner": {
                    "pid": os.getpid(),
                    "start_time": process_start_time(os.getpid()),
                    "boot_id": current_boot_id(),
                },
                "child": None,
                "state": "registered",
                "created_at": time.time(),
            }
            _write_lease_at(dir_fd, lease)
            os.mkdir(PAYLOAD_DIRNAME, 0o700, dir_fd=dir_fd)
        except BaseException:
            os.close(lock_fd)
            raise
    except BaseException:
        os.close(dir_fd)
        shutil.rmtree(path, ignore_errors=True)
        raise
    return TaskScratch(
        task_id=task_id,
        invocation_id=path.name,
        namespace=namespace,
        path=path,
        payload_dir=path / PAYLOAD_DIRNAME,
        lease=lease,
        _dir_fd=dir_fd,
        _lock_fd=lock_fd,
    )


@dataclass
class RunOutcome:
    """What one wrapped run did."""

    returncode: int
    exit_status: int
    scratch_path: Path
    invocation_id: str
    action: str
    group_status: str
    interrupted_by: int | None
    evidence: dict[str, Any] | None
    detail: str = ""


def run_task(
    task_id: str,
    argv: Sequence[str],
    *,
    root: Path | None = None,
    cwd: Path | None = None,
    keep: bool = False,
    keep_on_failure: bool = False,
    evidence_dir: Path | None = None,
    group_grace_s: float = DEFAULT_GROUP_GRACE_S,
    kill_after_s: float = DEFAULT_KILL_AFTER_S,
    log=None,
) -> RunOutcome:
    """Run ``argv`` inside a fresh task-owned scratch directory and clean it.

    Forwards SIGINT/SIGTERM/SIGHUP to the owned group, escalating to SIGKILL
    after ``kill_after_s``. Returns the child's exit status (``128 + signal``
    when signal-killed), regardless of cleanup outcome.
    """
    emit = log if log is not None else (lambda message: sys.stderr.write(f"task-scratch: {message}\n"))
    fault = os.environ.get(FAULT_ENV_VAR, "").strip() or None
    scratch = allocate(task_id, root=root)
    emit(f"scratch {scratch.path} (task {task_id!r}, invocation {scratch.invocation_id})")
    interrupted: list[int] = []
    previous_handlers: dict[int, Any] = {}

    def _forward(signum: int, _frame: Any) -> None:
        interrupted.append(signum)
        scratch.signal_group(signum)

    # Handlers go in before the child exists so a signal that lands during
    # spawn is recorded (and forwarded right after) instead of killing the
    # wrapper with its default action and stranding a live child.
    for signum in _FORWARDED_SIGNALS:
        previous_handlers[signum] = signal.signal(signum, _forward)
    try:
        try:
            proc = scratch.spawn(argv, cwd=cwd, fault=fault)
        except BaseException:
            scratch.preserve()
            raise
        if interrupted:
            scratch.signal_group(interrupted[0])
        returncode = _wait_child(proc, scratch, interrupted, kill_after_s=kill_after_s)
    finally:
        for signum, handler in previous_handlers.items():
            signal.signal(signum, handler)
    exit_status = returncode if returncode >= 0 else 128 + (-returncode)
    group_status = scratch.wait_group_clear(grace_s=group_grace_s)
    if group_status == "members":
        emit("warning: process-group members survived SIGKILL; preserving scratch for scheduled recovery")
    elif group_status == "reused":
        emit("warning: child process-group id was reused by another process; preserving scratch")
    elif group_status == "unknown":
        emit("warning: cannot enumerate the child process group (no /proc); preserving scratch")

    evidence: dict[str, Any] | None = None
    if evidence_dir is not None:
        try:
            evidence = scratch.export_evidence(evidence_dir)
            if evidence["source_present"]:
                emit(f"evidence: {evidence['files']} file(s), {evidence['bytes']} bytes -> {evidence_dir}")
        except (OSError, TaskScratchError) as exc:
            emit(f"warning: evidence export failed: {exc}")
            evidence = {"error": str(exc)}

    action = "removed"
    detail = ""
    if keep or (keep_on_failure and returncode != 0):
        action = "kept"
        scratch.preserve()
        emit(f"kept scratch at {scratch.path} (delete it with the scheduled recovery or by hand)")
    elif group_status != "absent":
        action = "preserved"
        detail = group_status
        scratch.preserve()
    else:
        try:
            scratch.remove()
            emit("scratch removed")
        except (OSError, TaskScratchError) as exc:
            action = "preserved"
            detail = str(exc)
            emit(f"warning: cleanup failed ({exc}); scheduled recovery will reclaim it once proven orphaned")
            scratch.preserve()
    return RunOutcome(
        returncode=returncode,
        exit_status=exit_status,
        scratch_path=scratch.path,
        invocation_id=scratch.invocation_id,
        action=action,
        group_status=group_status,
        interrupted_by=interrupted[0] if interrupted else None,
        evidence=evidence,
        detail=detail,
    )


def _wait_child(
    proc: subprocess.Popen[bytes],
    scratch: TaskScratch,
    interrupted: list[int],
    *,
    kill_after_s: float,
) -> int:
    kill_deadline: float | None = None
    while True:
        try:
            return proc.wait(timeout=0.2)
        except subprocess.TimeoutExpired:
            pass
        if interrupted:
            if kill_deadline is None:
                kill_deadline = time.monotonic() + max(0.0, kill_after_s)
            elif time.monotonic() >= kill_deadline:
                scratch.signal_group(signal.SIGKILL)
                return proc.wait()


# --------------------------------------------------------------------------
# Scheduled recovery
# --------------------------------------------------------------------------


@dataclass
class RecoveryEntry:
    name: str
    task_id: str | None
    action: str
    reason: str
    age_s: int | None = None
    bytes: int = 0


def _preserve(entries: list[RecoveryEntry], name: str, task_id: str | None, reason: str, **extra: Any) -> None:
    entries.append(RecoveryEntry(name=name, task_id=task_id, action="preserved", reason=reason, **extra))


def _owner_dead(lease: Mapping[str, Any], *, boot: str | None) -> tuple[bool, str]:
    """Return ``(dead, reason)`` for the recorded wrapper process."""
    owner = lease["owner"]
    recorded_boot = owner.get("boot_id")
    if recorded_boot and boot and recorded_boot != boot:
        return True, "owner_dead_reboot"
    state = owner_alive(int(owner["pid"]), owner.get("start_time"))
    if state is True:
        return False, "owner_alive"
    if state is None:
        return False, "owner_liveness_unknown"
    return True, "owner_dead"


def _child_group_dead(lease: Mapping[str, Any], *, boot: str | None) -> tuple[bool, str]:
    child = lease.get("child")
    if not child:
        return True, "no_child_recorded"
    recorded_boot = lease["owner"].get("boot_id")
    if recorded_boot and boot and recorded_boot != boot:
        return True, "child_dead_reboot"
    leader = owner_alive(int(child["pid"]), child.get("start_time"))
    if leader is True:
        return False, "child_alive"
    if leader is None:
        return False, "child_liveness_unknown"
    probe = probe_process_group(int(child["pgid"]))
    if not probe.complete:
        return False, "group_probe_unknown"
    if probe.members:
        if _pid_exists(int(child["pid"])) is True:
            return False, "group_id_reused"
        return False, "group_members_alive"
    return True, "child_group_dead"


def recover_orphans(
    *,
    apply: bool = False,
    root: Path | None = None,
    now: float | None = None,
    min_age_s: float = DEFAULT_MIN_AGE_S,
    pressure_min_age_s: float = DEFAULT_PRESSURE_MIN_AGE_S,
    min_free_gb: float = DEFAULT_MIN_FREE_GB,
) -> dict[str, Any]:
    """Inventory the managed namespace and reclaim provably orphaned entries.

    Dry-run (the default) is mutation-free. Every non-reclaimed entry is
    reported with the guard that preserved it.
    """
    current = time.time() if now is None else now
    namespace = task_scratch_namespace(root)
    entries: list[RecoveryEntry] = []
    result: dict[str, Any] = {
        "apply": apply,
        "namespace_present": False,
        "free_gb": None,
        "disk_pressure": False,
        "min_age_s": min_age_s,
        "candidates": 0,
        "reaped": 0,
        "bytes_freed": 0,
        "preserved": 0,
        "preserved_by_reason": {},
        "errors": 0,
        "entries": entries,
    }
    try:
        ns_st = namespace.lstat()
    except FileNotFoundError:
        return result
    except OSError as exc:
        result["errors"] += 1
        entries.append(RecoveryEntry(name="", task_id=None, action="error", reason=f"namespace_stat: {exc}"))
        return _finalize(result)
    result["namespace_present"] = True
    if stat.S_ISLNK(ns_st.st_mode) or not stat.S_ISDIR(ns_st.st_mode) or ns_st.st_uid != os.geteuid():
        result["errors"] += 1
        entries.append(RecoveryEntry(name="", task_id=None, action="error", reason="namespace_untrusted"))
        return _finalize(result)

    free_gb = free_space_gb(namespace)
    result["free_gb"] = free_gb
    under_pressure = free_gb is not None and free_gb < min_free_gb
    effective_min_age = pressure_min_age_s if under_pressure else min_age_s
    result["disk_pressure"] = under_pressure
    result["min_age_s"] = effective_min_age
    boot = current_boot_id()

    ns_fd = os.open(namespace, _DIR_OPEN_FLAGS | getattr(os, "O_CLOEXEC", 0))
    try:
        ns_fst = os.fstat(ns_fd)
        if (ns_fst.st_dev, ns_fst.st_ino) != (ns_st.st_dev, ns_st.st_ino):
            result["errors"] += 1
            entries.append(RecoveryEntry(name="", task_id=None, action="error", reason="namespace_changed"))
            return _finalize(result)
        with os.scandir(ns_fd) as it:
            names = sorted(entry.name for entry in it)
        for name in names:
            result["candidates"] += 1
            _recover_one(
                ns_fd,
                name,
                entries=entries,
                result=result,
                apply=apply,
                now=current,
                min_age_s=effective_min_age,
                boot=boot,
                ns_dev=ns_fst.st_dev,
                namespace=namespace,
            )
    finally:
        os.close(ns_fd)
    return _finalize(result)


def _finalize(result: dict[str, Any]) -> dict[str, Any]:
    entries: list[RecoveryEntry] = result["entries"]
    by_reason: dict[str, int] = {}
    preserved = 0
    for entry in entries:
        if entry.action == "preserved":
            preserved += 1
            by_reason[entry.reason] = by_reason.get(entry.reason, 0) + 1
    result["preserved"] = preserved
    result["preserved_by_reason"] = dict(sorted(by_reason.items()))
    result["entries"] = [entry.__dict__ for entry in entries]
    return result


def _recover_one(
    ns_fd: int,
    name: str,
    *,
    entries: list[RecoveryEntry],
    result: dict[str, Any],
    apply: bool,
    now: float,
    min_age_s: float,
    boot: str | None,
    ns_dev: int,
    namespace: Path,
) -> None:
    if name.startswith(".") and name.endswith(".tmp"):
        _preserve(entries, name, None, "namespace_temp_file")
        return
    try:
        st = os.stat(name, dir_fd=ns_fd, follow_symlinks=False)
    except FileNotFoundError:
        _preserve(entries, name, None, "vanished")
        return
    except OSError:
        _preserve(entries, name, None, "stat_failed")
        return
    if stat.S_ISLNK(st.st_mode):
        _preserve(entries, name, None, "symlink")
        return
    if not stat.S_ISDIR(st.st_mode):
        _preserve(entries, name, None, "not_directory")
        return
    if st.st_uid != os.geteuid():
        _preserve(entries, name, None, "foreign_owner")
        return
    if st.st_dev != ns_dev:
        _preserve(entries, name, None, "mount_boundary")
        return
    try:
        inv_fd = _open_dir_at(ns_fd, name)
    except OSError:
        _preserve(entries, name, None, "open_failed")
        return
    try:
        inv_st = os.fstat(inv_fd)
        if (inv_st.st_dev, inv_st.st_ino) != (st.st_dev, st.st_ino):
            _preserve(entries, name, None, "identity_changed")
            return
        lease = parse_lease(_read_regular_owned_file(inv_fd, LEASE_FILENAME, max_bytes=LEASE_MAX_BYTES))
        if lease is None:
            _preserve(entries, name, None, "malformed_metadata")
            return
        task_id = lease["task_id"]
        if lease["uid"] != os.geteuid():
            _preserve(entries, name, task_id, "foreign_owner")
            return
        if (lease["dir"]["dev"], lease["dir"]["ino"]) != (inv_st.st_dev, inv_st.st_ino):
            _preserve(entries, name, task_id, "metadata_identity_mismatch")
            return
        if lease["invocation_id"] != name:
            _preserve(entries, name, task_id, "metadata_identity_mismatch")
            return
        # Lease lock: the owning wrapper holds it for its whole lifetime.
        try:
            lock_fd = os.open(
                LOCK_FILENAME,
                os.O_RDWR | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
                dir_fd=inv_fd,
            )
        except OSError:
            _preserve(entries, name, task_id, "lock_missing")
            return
        try:
            lock_st = os.fstat(lock_fd)
            if not stat.S_ISREG(lock_st.st_mode) or lock_st.st_uid != os.geteuid():
                _preserve(entries, name, task_id, "lock_untrusted")
                return
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                if exc.errno in {errno.EWOULDBLOCK, errno.EAGAIN}:
                    _preserve(entries, name, task_id, "in_use")
                    return
                _preserve(entries, name, task_id, "lock_failed")
                return
            # Re-read under the lock: the owner may have finished meanwhile.
            lease = parse_lease(_read_regular_owned_file(inv_fd, LEASE_FILENAME, max_bytes=LEASE_MAX_BYTES))
            if lease is None or lease["invocation_id"] != name:
                _preserve(entries, name, task_id, "malformed_metadata")
                return
            dead, reason = _owner_dead(lease, boot=boot)
            if not dead:
                _preserve(entries, name, task_id, reason)
                return
            group_dead, group_reason = _child_group_dead(lease, boot=boot)
            if not group_dead:
                _preserve(entries, name, task_id, group_reason)
                return
            try:
                size, newest = _walk_stats(inv_fd, device=inv_st.st_dev)
            except ContainmentError:
                _preserve(entries, name, task_id, "mount_boundary")
                return
            except OSError:
                _preserve(entries, name, task_id, "walk_failed")
                return
            newest = max(newest, inv_st.st_mtime)
            age = max(0.0, now - newest)
            if age < min_age_s:
                _preserve(entries, name, task_id, "too_young", age_s=int(age), bytes=size)
                return
            if not apply:
                entries.append(
                    RecoveryEntry(
                        name=name, task_id=task_id, action="would_reap", reason=reason, age_s=int(age), bytes=size
                    )
                )
                return
            try:
                _remove_invocation_dir(
                    ns_fd, name, namespace=namespace, expected_dev=inv_st.st_dev, expected_ino=inv_st.st_ino
                )
            except (ContainmentError, OSError) as exc:
                result["errors"] += 1
                entries.append(
                    RecoveryEntry(
                        name=name, task_id=task_id, action="error", reason=f"remove_failed: {exc}", bytes=size
                    )
                )
                return
            result["reaped"] += 1
            result["bytes_freed"] += size
            entries.append(
                RecoveryEntry(name=name, task_id=task_id, action="reaped", reason=reason, age_s=int(age), bytes=size)
            )
        finally:
            os.close(lock_fd)
    finally:
        os.close(inv_fd)
