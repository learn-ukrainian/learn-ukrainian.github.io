"""Find and stop the processes a dispatch worker left running (#8991).

A headless worker can end its turn while its own background jobs still run: a
``claude -p`` Bash call moved to the background, a detached ``pytest``. Nothing
resumes the session, so those jobs are orphans of a finished run. This module
names them and stops them, and never looks outside the worker's own boundary:

* ``launch_mode: scope`` (``dispatch_isolation``): the worker's systemd scope
  cgroup. Every descendant stays in it, whatever session or process group it
  moved to. The ``cgroup.procs`` list is the authority. The unit and cgroup
  are used only when they are exactly the ones ``dispatch_isolation`` derives
  from the task id and run nonce, under ``lu-dispatch.slice``.
* ``popen-fallback``: processes whose environment carries this task's
  ``LEARN_UKRAINIAN_DISPATCH_TASK_ID`` (exported by ``delegate`` into every
  worker and allowlisted through ``agent_runtime.env_sanitize``, so it
  survives the CLI's ``setsid`` and reparenting), plus the worker's own
  session while that session leader is the caller. After the worker is gone
  its session id can be reused, so only the environment marker is trusted.
  Processes of another real uid, or started before the worker, cannot be its
  jobs and are not read.

A scan that cannot read something it needs raises :class:`ScanUnknown`: an
unreadable ``cgroup.procs`` or process environment is not proof that no job is
alive. Individual processes are signalled only through a pidfd whose target is
re-verified after it is opened; without pidfd support nothing is signalled.
The caller and its ancestors are never reported or signalled, and zombies are
not processes that can still do work.
"""

from __future__ import annotations

import ctypes
import errno
import os
import platform
import signal
import subprocess
import sys
import time
from collections.abc import Callable, Collection, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from scripts.orchestration import dispatch_isolation

BACKGROUND_JOBS_REASON = "background_jobs_alive_at_exit"
SCAN_UNKNOWN_REASON = "leftovers_scan_unknown"
DISPATCH_TASK_ENV = "LEARN_UKRAINIAN_DISPATCH_TASK_ID"
LAUNCH_SCOPE = dispatch_isolation.LAUNCH_SCOPE
LAUNCH_FALLBACK = dispatch_isolation.LAUNCH_FALLBACK

# Task-record keys written by the exit scan and read by every reaper.
SCAN_KEY = "leftovers_scan"
SCOPE_KEY = "leftovers_scope"
SCAN_ERROR_KEY = "leftovers_scan_error"
SCAN_CLEAR = "clear"
SCAN_LIVE = "live"
SCAN_UNKNOWN = "unknown"

# Bounds for the task record: enough to name the jobs, never the whole table.
MAX_RECORDED_PROCESSES = 20
CMDLINE_MAX_CHARS = 200

_STOP_UNIT_TIMEOUT_S = 30.0
_POLL_S = 0.1

# A process that vanished between listing and reading is gone, not unreadable.
_GONE = (FileNotFoundError, ProcessLookupError)


class ScanUnknown(Exception):
    """Something inside the worker's boundary could not be read."""


class ProcessReader(Protocol):
    """What this module reads about processes. Tests pass a fake.

    Every method returns ``None`` for a process (or cgroup) that is gone and
    raises :class:`ScanUnknown` when it exists but cannot be read.
    """

    def pids(self) -> list[int]: ...

    def stat(self, pid: int) -> ProcStat | None: ...

    def real_uid(self, pid: int) -> int | None: ...

    def dispatch_task_id(self, pid: int) -> str | None: ...

    def proc_cgroup(self, pid: int) -> str | None: ...

    def cmdline(self, pid: int) -> str: ...

    def cwd(self, pid: int) -> Path | None: ...

    def cgroup_procs(self, cgroup: str) -> list[int] | None: ...

    def own_cgroup(self) -> str | None: ...


@dataclass(frozen=True)
class ProcStat:
    state: str
    ppid: int
    sid: int
    start_ticks: int


@dataclass(frozen=True)
class WorkerScope:
    """The boundary a worker's processes live in, as recorded on the task."""

    task_id: str
    launch_mode: str | None = None
    unit: str | None = None
    cgroup: str | None = None
    session_id: int | None = None
    run_nonce: str | None = None
    # The worker's own start time: nothing older can be one of its jobs.
    worker_start_ticks: int | None = None

    def as_state(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "launch_mode": self.launch_mode,
            "unit": self.unit,
            "cgroup": self.cgroup,
            "session_id": self.session_id,
            "run_nonce": self.run_nonce,
            "worker_start_ticks": self.worker_start_ticks,
        }

    @classmethod
    def from_state(cls, raw: object) -> WorkerScope | None:
        """Parse a recorded scope; ``None`` when any field is malformed."""
        if not isinstance(raw, Mapping):
            return None
        task_id = raw.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            return None
        strings = {key: raw.get(key) for key in ("launch_mode", "unit", "cgroup", "run_nonce")}
        ints = {key: raw.get(key) for key in ("session_id", "worker_start_ticks")}
        if any(value is not None and (not isinstance(value, str) or not value) for value in strings.values()):
            return None
        if any(
            value is not None and (isinstance(value, bool) or not isinstance(value, int) or value <= 0)
            for value in ints.values()
        ):
            return None
        return cls(task_id=task_id, **strings, **ints)


def scope_identity_error(scope: WorkerScope, *, uid: int | None = None) -> str | None:
    """Why ``scope`` is not a boundary ``dispatch_isolation`` could have created, or None.

    A scope unit must carry the name derived from the task id and run nonce,
    and a recorded cgroup must be that unit's scope under ``lu-dispatch.slice``
    for this user. A fallback launch has neither.
    """
    uid = os.getuid() if uid is None else uid
    if scope.launch_mode == LAUNCH_FALLBACK:
        if scope.unit is not None or scope.cgroup is not None:
            return "popen-fallback scope records a unit or cgroup"
        return None
    if scope.launch_mode != LAUNCH_SCOPE:
        return f"unknown launch_mode {scope.launch_mode!r}"
    if scope.unit is None or scope.run_nonce is None:
        return "scope launch without a unit or run nonce"
    if not dispatch_isolation.scope_unit_matches(scope.unit, task_id=scope.task_id, run_nonce=scope.run_nonce):
        return f"unit {scope.unit!r} is not this task's launch unit"
    if scope.cgroup is not None and scope.cgroup != dispatch_isolation.scope_cgroup(scope.unit, uid=uid):
        return f"cgroup {scope.cgroup!r} is not {scope.unit}.scope under {dispatch_isolation.SLICE_UNIT}"
    return None


def scope_from_record(record: Mapping[str, Any], *, task_id: str) -> tuple[WorkerScope | None, str | None]:
    """The scope whose jobs must be stopped before this task's worktree goes.

    ``(None, None)``: the record claims no unconfirmed jobs. ``(scope, None)``:
    stop inside ``scope``. ``(None, refusal)``: the record says jobs may be
    alive but its scope is malformed or does not match the task's launch
    identity (task id, run nonce, launch mode and unit), so nothing may be
    signalled and the worktree must stay.
    """
    scan = record.get(SCAN_KEY)
    if scan is None or scan == SCAN_CLEAR:
        return None, None
    if scan not in (SCAN_LIVE, SCAN_UNKNOWN):
        return None, f"unrecognised {SCAN_KEY} {scan!r}"
    scope = WorkerScope.from_state(record.get(SCOPE_KEY))
    if scope is None:
        return None, f"{SCOPE_KEY} missing or malformed"
    recorded = {
        "task_id": task_id,
        "run_nonce": record.get("run_nonce"),
        "launch_mode": record.get("launch_mode"),
        "unit": record.get("launch_unit"),
    }
    for key, expected in recorded.items():
        if getattr(scope, key) != expected:
            return None, f"{SCOPE_KEY} {key} does not match the task's launch record"
    error = scope_identity_error(scope)
    if error is not None:
        return None, error
    return scope, None


@dataclass(frozen=True)
class LeftoverProcess:
    pid: int
    start_ticks: int
    cmdline: str

    def as_state(self) -> dict[str, Any]:
        return {"pid": self.pid, "cmdline": self.cmdline[:CMDLINE_MAX_CHARS]}


@dataclass(frozen=True)
class ExitScan:
    """What the worker's exit scan found: ``clear``, ``live`` or ``unknown``."""

    status: str
    scope: WorkerScope
    leftovers: tuple[LeftoverProcess, ...] = ()
    error: str | None = None

    @property
    def unconfirmed(self) -> bool:
        return self.status != SCAN_CLEAR

    @property
    def reason(self) -> str | None:
        if self.status == SCAN_LIVE:
            return BACKGROUND_JOBS_REASON
        if self.status == SCAN_UNKNOWN:
            return SCAN_UNKNOWN_REASON
        return None

    def record_fields(self) -> dict[str, Any]:
        """Task-record fields; the scope is kept whenever jobs may be alive."""
        fields: dict[str, Any] = {SCAN_KEY: self.status}
        if not self.unconfirmed:
            return fields
        fields[SCOPE_KEY] = self.scope.as_state()
        fields["incomplete_run_reason"] = self.reason
        if self.status == SCAN_LIVE:
            fields[BACKGROUND_JOBS_REASON] = leftovers_state(self.scope, list(self.leftovers))
        else:
            fields[SCAN_ERROR_KEY] = self.error
        return fields


@dataclass(frozen=True)
class StopResult:
    ok: bool
    signalled: list[int] = field(default_factory=list)
    survivors: list[LeftoverProcess] = field(default_factory=list)
    # Processes a signal could not be delivered to safely (no pidfd, refused).
    unsignalled: list[int] = field(default_factory=list)
    unit_stopped: bool = False
    error: str | None = None

    def as_state(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "signalled": list(self.signalled),
            "survivors": [proc.as_state() for proc in self.survivors[:MAX_RECORDED_PROCESSES]],
            "unsignalled": list(self.unsignalled),
            "unit_stopped": self.unit_stopped,
            "error": self.error,
        }


@dataclass(frozen=True)
class PidfdOps:
    """pidfd primitives. ``None`` when this Python or kernel lacks them."""

    open: Callable[[int], int] | None
    send: Callable[[int, int], None] | None
    close: Callable[[int], None] = os.close


# Syscalls added after Linux 5.1 share one number on every architecture but
# alpha (which adds 110): include/uapi/asm-generic/unistd.h.
_NR_PIDFD_SEND_SIGNAL = 424
_NR_PIDFD_OPEN = 434


def live_pidfd_ops() -> PidfdOps:
    """The host's pidfd calls: the stdlib's, else the raw Linux syscalls.

    Some CPython builds (the uv-managed interpreter this project runs on
    among them) are compiled without ``os.pidfd_open`` and
    ``signal.pidfd_send_signal`` even though the kernel has both.
    """
    open_ = getattr(os, "pidfd_open", None)
    send = getattr(signal, "pidfd_send_signal", None)
    if open_ is not None and send is not None:
        return PidfdOps(open=open_, send=send)
    return _syscall_pidfd_ops() or PidfdOps(open=None, send=None)


def _syscall_pidfd_ops() -> PidfdOps | None:
    if not sys.platform.startswith("linux") or platform.machine().lower().startswith("alpha"):
        return None
    try:
        syscall = ctypes.CDLL(None, use_errno=True).syscall
    except (OSError, AttributeError):
        return None
    syscall.restype = ctypes.c_long

    def checked(*args: Any) -> int:
        result = syscall(*(ctypes.c_long(arg) for arg in args), ctypes.c_long(0))
        if result < 0:
            err = ctypes.get_errno()
            # OSError(errno, ...) returns the matching subclass (ESRCH ->
            # ProcessLookupError), so callers see what os.pidfd_open raises.
            raise OSError(err, os.strerror(err))
        return int(result)

    def pidfd_open(pid: int) -> int:
        return checked(_NR_PIDFD_OPEN, pid)

    def pidfd_send_signal(fd: int, sig: int) -> None:
        # siginfo NULL (the 0 before the trailing flags 0), like kill(2).
        checked(_NR_PIDFD_SEND_SIGNAL, fd, int(sig), 0)

    return PidfdOps(open=pidfd_open, send=pidfd_send_signal)


class ProcFsReader:
    """``/proc`` and cgroup v2 reads for the live host."""

    def __init__(self, proc_root: Path = Path("/proc"), cgroup_root: Path = Path("/sys/fs/cgroup")) -> None:
        self.proc_root = proc_root
        self.cgroup_root = cgroup_root

    def _read(self, pid: int | str, name: str) -> bytes | None:
        path = self.proc_root / str(pid) / name
        try:
            return path.read_bytes()
        except _GONE:
            return None
        except OSError as exc:
            raise ScanUnknown(f"{path}: {exc.strerror or exc}") from exc

    def pids(self) -> list[int]:
        try:
            return [int(entry.name) for entry in self.proc_root.iterdir() if entry.name.isdigit()]
        except OSError as exc:
            raise ScanUnknown(f"{self.proc_root}: {exc.strerror or exc}") from exc

    def stat(self, pid: int) -> ProcStat | None:
        raw = self._read(pid, "stat")
        if raw is None:
            return None
        parsed = parse_stat(raw.decode("utf-8", errors="replace"))
        if parsed is None:
            raise ScanUnknown(f"/proc/{pid}/stat unparseable")
        return parsed

    def real_uid(self, pid: int) -> int | None:
        raw = self._read(pid, "status")
        if raw is None:
            return None
        for line in raw.decode("utf-8", errors="replace").splitlines():
            if line.startswith("Uid:"):
                fields = line.split()
                if len(fields) >= 2 and fields[1].isdigit():
                    return int(fields[1])
        raise ScanUnknown(f"/proc/{pid}/status has no Uid line")

    def dispatch_task_id(self, pid: int) -> str | None:
        raw = self._read(pid, "environ")
        if raw is None:
            return None
        prefix = f"{DISPATCH_TASK_ENV}=".encode()
        for item in raw.split(b"\0"):
            if item.startswith(prefix):
                return item[len(prefix) :].decode("utf-8", errors="replace")
        return None

    def proc_cgroup(self, pid: int) -> str | None:
        raw = self._read(pid, "cgroup")
        if raw is None:
            return None
        return _unified_cgroup(raw.decode("utf-8", errors="replace"))

    def cmdline(self, pid: int) -> str:
        try:
            raw = (self.proc_root / str(pid) / "cmdline").read_bytes()
        except OSError:
            return ""
        return raw.replace(b"\0", b" ").decode("utf-8", errors="replace").strip()[:CMDLINE_MAX_CHARS]

    def cwd(self, pid: int) -> Path | None:
        try:
            target = os.readlink(self.proc_root / str(pid) / "cwd")
        except OSError:
            return None
        return Path(target.removesuffix(" (deleted)"))

    def cgroup_procs(self, cgroup: str) -> list[int] | None:
        path = self.cgroup_root / cgroup.lstrip("/") / "cgroup.procs"
        try:
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            # systemd collects a scope once its last process is gone.
            return None
        except OSError as exc:
            raise ScanUnknown(f"{path}: {exc.strerror or exc}") from exc
        return [int(line) for line in text.split() if line.isdigit()]

    def own_cgroup(self) -> str | None:
        try:
            raw = self._read("self", "cgroup")
        except ScanUnknown:
            return None
        return _unified_cgroup(raw.decode("utf-8", errors="replace")) if raw is not None else None


def _unified_cgroup(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("0::"):
            return line[3:].strip() or None
    return None


def parse_stat(text: str) -> ProcStat | None:
    """Parse ``/proc/<pid>/stat``; ``comm`` may contain spaces and parentheses."""
    end = text.rfind(")")
    if end < 0:
        return None
    fields = text[end + 2 :].split()
    # After comm: state(3) ppid(4) pgrp(5) session(6) ... starttime(22).
    if len(fields) <= 19:
        return None
    try:
        return ProcStat(state=fields[0], ppid=int(fields[1]), sid=int(fields[3]), start_ticks=int(fields[19]))
    except ValueError:
        return None


def worker_scope_at_exit(
    *,
    task_id: str,
    launch_mode: str | None,
    launch_unit: str | None,
    run_nonce: str | None,
    reader: ProcessReader,
) -> WorkerScope:
    """The calling worker's own boundary. Call from inside the worker process.

    The cgroup is recorded only when the caller really runs in the scope
    ``dispatch_isolation`` derives from this task id and run nonce, so a worker
    in someone else's cgroup never scans or later stops it.
    """
    cgroup = None
    if launch_mode == LAUNCH_SCOPE and launch_unit and run_nonce:
        expected = dispatch_isolation.scope_cgroup(launch_unit, uid=os.getuid())
        matches = dispatch_isolation.scope_unit_matches(launch_unit, task_id=task_id, run_nonce=run_nonce)
        if matches and reader.own_cgroup() == expected:
            cgroup = expected
    own = reader.stat(os.getpid())
    return WorkerScope(
        task_id=task_id,
        launch_mode=launch_mode,
        unit=launch_unit if launch_mode == LAUNCH_SCOPE else None,
        cgroup=cgroup,
        session_id=os.getpid() if os.getsid(0) == os.getpid() else None,
        run_nonce=run_nonce,
        worker_start_ticks=own.start_ticks if own is not None else None,
    )


def _protected_pids(reader: ProcessReader, exclude: Collection[int]) -> set[int]:
    protected = {os.getpid(), *exclude}
    pid = os.getpid()
    for _ in range(64):
        try:
            info = reader.stat(pid)
        except ScanUnknown:
            break
        if info is None or info.ppid <= 0 or info.ppid in protected:
            break
        protected.add(info.ppid)
        pid = info.ppid
    return protected


def _in_boundary(scope: WorkerScope, reader: ProcessReader, pid: int, info: ProcStat) -> bool:
    """Whether a live ``pid`` belongs to ``scope``; raises :class:`ScanUnknown`."""
    if scope.cgroup:
        return reader.proc_cgroup(pid) == scope.cgroup
    # The session id is trusted only while its leader is the caller: after
    # the worker exits the number can be handed to an unrelated session.
    if scope.session_id is not None and scope.session_id == os.getpid() and info.sid == scope.session_id:
        return True
    if scope.worker_start_ticks is not None and info.start_ticks < scope.worker_start_ticks:
        return False
    uid = reader.real_uid(pid)
    if uid is None or uid != os.getuid():
        # Another real uid is not this worker's job (it cannot change its
        # real uid unprivileged); its environment is not readable anyway.
        return False
    return reader.dispatch_task_id(pid) == scope.task_id


def find_leftovers(
    scope: WorkerScope,
    *,
    reader: ProcessReader,
    exclude: Collection[int] = (),
) -> list[LeftoverProcess]:
    """Live processes inside ``scope``; raises :class:`ScanUnknown` when that cannot be proven."""
    protected = _protected_pids(reader, exclude)
    if scope.cgroup:
        candidates = reader.cgroup_procs(scope.cgroup)
        if candidates is None:
            if reader.own_cgroup() == scope.cgroup:
                raise ScanUnknown(f"{scope.cgroup} missing while the caller runs in it")
            candidates = []
    else:
        candidates = reader.pids()

    found: list[LeftoverProcess] = []
    for pid in sorted(set(candidates)):
        if pid in protected:
            continue
        info = reader.stat(pid)
        if info is None or info.state == "Z" or not _in_boundary(scope, reader, pid, info):
            continue
        found.append(LeftoverProcess(pid=pid, start_ticks=info.start_ticks, cmdline=reader.cmdline(pid)))
    return found


def exit_scan(
    scope: WorkerScope,
    *,
    reader: ProcessReader,
    settle_s: float,
    exclude: Collection[int] = (),
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> ExitScan:
    """Scan until nothing is left or ``settle_s`` passes.

    The grace covers children that exit on their own right after the CLI,
    such as a stdio MCP server reading EOF, and a transient unreadable
    process. What is still alive, or still unreadable, at the deadline is the
    answer.
    """
    deadline = clock() + settle_s
    while True:
        try:
            found = find_leftovers(scope, reader=reader, exclude=exclude)
        except ScanUnknown as exc:
            result = ExitScan(status=SCAN_UNKNOWN, scope=scope, error=str(exc)[:300])
        else:
            if not found:
                return ExitScan(status=SCAN_CLEAR, scope=scope)
            result = ExitScan(status=SCAN_LIVE, scope=scope, leftovers=tuple(found))
        if clock() >= deadline:
            return result
        sleep(_POLL_S)


def leftovers_state(scope: WorkerScope, leftovers: list[LeftoverProcess]) -> dict[str, Any]:
    """The ``background_jobs_alive_at_exit`` task-record value."""
    return {
        "reason": BACKGROUND_JOBS_REASON,
        "count": len(leftovers),
        "processes": [proc.as_state() for proc in leftovers[:MAX_RECORDED_PROCESSES]],
        "scope": scope.as_state(),
    }


def _systemctl_stop(unit: str) -> bool:
    try:
        proc = subprocess.run(
            ["systemctl", "--user", "stop", f"{unit}.scope"],
            capture_output=True,
            text=True,
            check=False,
            timeout=_STOP_UNIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return proc.returncode == 0


def _still_same(scope: WorkerScope, reader: ProcessReader, proc: LeftoverProcess) -> bool:
    """Whether ``proc.pid`` still names the scanned process, inside ``scope``."""
    info = reader.stat(proc.pid)
    if info is None or info.start_ticks != proc.start_ticks or info.state == "Z":
        return False
    return _in_boundary(scope, reader, proc.pid, info)


def _signal_via_pidfd(scope: WorkerScope, reader: ProcessReader, proc: LeftoverProcess, sig: int, ops: PidfdOps) -> str:
    """Signal one process through a pidfd: ``signalled``, ``gone``, ``unavailable`` or ``refused``.

    The identity check runs again after the pidfd is open. From then on the
    fd names one process: if the pid was reused before the open, the check
    sees the newcomer and fails; if the process exits after the check, the
    signal hits the dead pidfd (``ESRCH``), never the pid's next owner.
    """
    if ops.open is None or ops.send is None:
        return "unavailable"
    try:
        if not _still_same(scope, reader, proc):
            return "gone"
        fd = ops.open(proc.pid)
    except ProcessLookupError:
        return "gone"
    except ScanUnknown:
        return "refused"
    except OSError as exc:
        return "unavailable" if exc.errno == errno.ENOSYS else "refused"
    try:
        if not _still_same(scope, reader, proc):
            return "gone"
        ops.send(fd, sig)
    except ProcessLookupError:
        return "gone"
    except (ScanUnknown, OSError):
        return "refused"
    finally:
        ops.close(fd)
    return "signalled"


def stop_leftovers(
    scope: WorkerScope,
    *,
    reader: ProcessReader,
    exclude: Collection[int] = (),
    grace_s: float = 5.0,
    pidfd: PidfdOps | None = None,
    stop_unit: Callable[[str], bool] = _systemctl_stop,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> StopResult:
    """Stop every process inside ``scope``; ``ok`` only when none is left.

    Nothing is touched unless ``scope`` passes :func:`scope_identity_error`.
    A scope unit the caller is not inside is stopped as a unit, which also
    takes anything forked mid-stop. Otherwise, and for whatever that leaves,
    each process gets SIGTERM, then SIGKILL after ``grace_s``, through a
    pidfd only; without pidfd support it is left alone and reported.
    """
    identity_error = scope_identity_error(scope)
    if identity_error is not None:
        return StopResult(ok=False, error=f"worker scope refused: {identity_error}")
    ops = live_pidfd_ops() if pidfd is None else pidfd
    try:
        leftovers = find_leftovers(scope, reader=reader, exclude=exclude)
    except ScanUnknown as exc:
        return StopResult(ok=False, error=f"worker scope unreadable: {exc}")
    if not leftovers:
        return StopResult(ok=True)

    unit_stopped = False
    signalled: list[int] = []
    unsignalled: list[int] = []

    def unreadable(exc: ScanUnknown) -> StopResult:
        return StopResult(
            ok=False,
            signalled=signalled,
            unsignalled=unsignalled,
            unit_stopped=unit_stopped,
            error=f"worker scope unreadable: {exc}",
        )

    own = reader.own_cgroup()
    if scope.cgroup and scope.unit and own is not None and own != scope.cgroup:
        unit_stopped = stop_unit(scope.unit)
        try:
            leftovers = find_leftovers(scope, reader=reader, exclude=exclude)
        except ScanUnknown as exc:
            return unreadable(exc)
        if not leftovers:
            return StopResult(ok=True, unit_stopped=unit_stopped)

    for sig in (signal.SIGTERM, signal.SIGKILL):
        delivered = False
        for proc in leftovers:
            outcome = _signal_via_pidfd(scope, reader, proc, sig, ops)
            if outcome == "signalled":
                delivered = True
                if proc.pid not in signalled:
                    signalled.append(proc.pid)
            elif outcome in {"unavailable", "refused"} and proc.pid not in unsignalled:
                unsignalled.append(proc.pid)
        deadline = clock() + (grace_s if delivered else 0.0)
        while True:
            try:
                leftovers = find_leftovers(scope, reader=reader, exclude=exclude)
            except ScanUnknown as exc:
                return unreadable(exc)
            if not leftovers or clock() >= deadline:
                break
            sleep(_POLL_S)
        if not leftovers:
            return StopResult(ok=True, signalled=signalled, unsignalled=unsignalled, unit_stopped=unit_stopped)
    if ops.open is None or ops.send is None:
        error = f"pidfd unavailable; {len(leftovers)} process(es) not signalled"
    else:
        error = f"{len(leftovers)} process(es) survived SIGKILL"
    return StopResult(
        ok=False,
        signalled=signalled,
        survivors=leftovers,
        unsignalled=unsignalled,
        unit_stopped=unit_stopped,
        error=error,
    )


def only_leftovers_hold(path: Path, scope: WorkerScope, *, reader: ProcessReader) -> bool:
    """Whether every process whose cwd is inside ``path`` belongs to ``scope``.

    ``False`` when the scope fails its identity check or it or the process
    table cannot be read, so an unknown holder keeps the caller's live-cwd
    guard in force. A process whose cwd link is unreadable is invisible to
    that guard's ``lsof`` probe too.
    """
    if scope_identity_error(scope) is not None:
        return False
    try:
        owned = {proc.pid for proc in find_leftovers(scope, reader=reader)}
        pids = reader.pids()
        root = path.resolve()
    except (ScanUnknown, OSError):
        return False
    for pid in pids:
        if pid in owned:
            continue
        cwd = reader.cwd(pid)
        if cwd is None:
            continue
        if cwd == root or root in cwd.parents:
            return False
    return True
