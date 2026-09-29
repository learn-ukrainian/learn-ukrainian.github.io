"""Find and stop the processes a dispatch worker left running (#8991).

A headless worker can end its turn while its own background jobs still run: a
``claude -p`` Bash call moved to the background, a detached ``pytest``. Nothing
resumes the session, so those jobs are orphans of a finished run. This module
names them and stops them, and never looks outside the worker's own boundary:

* ``launch_mode: scope`` (``dispatch_isolation``): the worker's systemd scope
  cgroup. Every descendant stays in it, whatever session or process group it
  moved to. The ``cgroup.procs`` list is the authority.
* ``popen-fallback``: processes whose environment carries this task's
  ``LEARN_UKRAINIAN_DISPATCH_TASK_ID`` (exported by ``delegate`` into every
  worker and allowlisted through ``agent_runtime.env_sanitize``, so it
  survives the CLI's ``setsid`` and reparenting), plus the worker's own
  session while that session leader is the caller. After the worker is gone
  its session id can be reused, so only the environment marker is trusted.

The caller and its ancestors are never reported or signalled, and zombies are
not processes that can still do work.
"""

from __future__ import annotations

import os
import signal
import subprocess
import time
from collections.abc import Callable, Collection
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

BACKGROUND_JOBS_REASON = "background_jobs_alive_at_exit"
DISPATCH_TASK_ENV = "LEARN_UKRAINIAN_DISPATCH_TASK_ID"
LAUNCH_SCOPE = "scope"

# Bounds for the task record: enough to name the jobs, never the whole table.
MAX_RECORDED_PROCESSES = 20
CMDLINE_MAX_CHARS = 200

_STOP_UNIT_TIMEOUT_S = 30.0
_POLL_S = 0.1


class ProcessReader(Protocol):
    """What this module reads about processes. Tests pass a fake."""

    def pids(self) -> list[int] | None: ...

    def stat(self, pid: int) -> ProcStat | None: ...

    def dispatch_task_id(self, pid: int) -> str | None: ...

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

    def as_state(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "launch_mode": self.launch_mode,
            "unit": self.unit,
            "cgroup": self.cgroup,
            "session_id": self.session_id,
        }

    @classmethod
    def from_state(cls, raw: object) -> WorkerScope | None:
        if not isinstance(raw, dict):
            return None
        task_id = raw.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            return None
        session_id = raw.get("session_id")
        return cls(
            task_id=task_id,
            launch_mode=raw.get("launch_mode") if isinstance(raw.get("launch_mode"), str) else None,
            unit=raw.get("unit") if isinstance(raw.get("unit"), str) else None,
            cgroup=raw.get("cgroup") if isinstance(raw.get("cgroup"), str) else None,
            session_id=session_id if isinstance(session_id, int) and session_id > 0 else None,
        )


@dataclass(frozen=True)
class LeftoverProcess:
    pid: int
    start_ticks: int
    cmdline: str

    def as_state(self) -> dict[str, Any]:
        return {"pid": self.pid, "cmdline": self.cmdline[:CMDLINE_MAX_CHARS]}


@dataclass(frozen=True)
class StopResult:
    ok: bool
    signalled: list[int] = field(default_factory=list)
    survivors: list[LeftoverProcess] = field(default_factory=list)
    unit_stopped: bool = False
    error: str | None = None

    def as_state(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "signalled": list(self.signalled),
            "survivors": [proc.as_state() for proc in self.survivors[:MAX_RECORDED_PROCESSES]],
            "unit_stopped": self.unit_stopped,
            "error": self.error,
        }


class ProcFsReader:
    """``/proc`` and cgroup v2 reads for the live host."""

    def __init__(self, proc_root: Path = Path("/proc"), cgroup_root: Path = Path("/sys/fs/cgroup")) -> None:
        self.proc_root = proc_root
        self.cgroup_root = cgroup_root

    def pids(self) -> list[int] | None:
        try:
            return [int(entry.name) for entry in self.proc_root.iterdir() if entry.name.isdigit()]
        except OSError:
            return None

    def stat(self, pid: int) -> ProcStat | None:
        try:
            text = (self.proc_root / str(pid) / "stat").read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None
        return parse_stat(text)

    def dispatch_task_id(self, pid: int) -> str | None:
        try:
            raw = (self.proc_root / str(pid) / "environ").read_bytes()
        except OSError:
            return None
        prefix = f"{DISPATCH_TASK_ENV}=".encode()
        for item in raw.split(b"\0"):
            if item.startswith(prefix):
                return item[len(prefix) :].decode("utf-8", errors="replace")
        return None

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
            return []
        except OSError:
            return None
        return [int(line) for line in text.split() if line.isdigit()]

    def own_cgroup(self) -> str | None:
        try:
            text = (self.proc_root / "self" / "cgroup").read_text(encoding="utf-8")
        except OSError:
            return None
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
    reader: ProcessReader,
) -> WorkerScope:
    """The calling worker's own boundary. Call from inside the worker process.

    The cgroup is recorded only when it really is this launch's scope unit,
    so a worker that runs in someone else's cgroup never scans it.
    """
    cgroup = None
    if launch_mode == LAUNCH_SCOPE and launch_unit:
        own = reader.own_cgroup()
        if own and own.rstrip("/").rsplit("/", 1)[-1] == f"{launch_unit}.scope":
            cgroup = own
    session_id = os.getpid() if os.getsid(0) == os.getpid() else None
    return WorkerScope(
        task_id=task_id,
        launch_mode=launch_mode,
        unit=launch_unit,
        cgroup=cgroup,
        session_id=session_id,
    )


def _protected_pids(reader: ProcessReader, exclude: Collection[int]) -> set[int]:
    protected = {os.getpid(), *exclude}
    pid = os.getpid()
    for _ in range(64):
        info = reader.stat(pid)
        if info is None or info.ppid <= 0 or info.ppid in protected:
            break
        protected.add(info.ppid)
        pid = info.ppid
    return protected


def find_leftovers(
    scope: WorkerScope,
    *,
    reader: ProcessReader,
    exclude: Collection[int] = (),
) -> list[LeftoverProcess] | None:
    """Live processes inside ``scope``, or ``None`` when that cannot be read."""
    protected = _protected_pids(reader, exclude)
    # The session id is trusted only while its leader is the caller: after
    # the worker exits the number can be handed to an unrelated session.
    own_session = scope.session_id if scope.session_id == os.getpid() else None
    candidates = reader.cgroup_procs(scope.cgroup) if scope.cgroup else reader.pids()
    if candidates is None:
        return None

    def in_boundary(pid: int, info: ProcStat) -> bool:
        if scope.cgroup:
            return True
        if own_session is not None and info.sid == own_session:
            return True
        return reader.dispatch_task_id(pid) == scope.task_id

    found: list[LeftoverProcess] = []
    for pid in sorted(set(candidates)):
        if pid in protected:
            continue
        info = reader.stat(pid)
        if info is None or info.state == "Z" or not in_boundary(pid, info):
            continue
        found.append(LeftoverProcess(pid=pid, start_ticks=info.start_ticks, cmdline=reader.cmdline(pid)))
    return found


def wait_for_leftovers(
    scope: WorkerScope,
    *,
    reader: ProcessReader,
    settle_s: float,
    exclude: Collection[int] = (),
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> list[LeftoverProcess] | None:
    """Leftovers still alive after ``settle_s``; an empty list returns at once.

    The grace covers children that exit on their own right after the CLI,
    such as a stdio MCP server reading EOF.
    """
    deadline = clock() + settle_s
    while True:
        found = find_leftovers(scope, reader=reader, exclude=exclude)
        if not found or clock() >= deadline:
            return found
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


def _signal_if_same(reader: ProcessReader, proc: LeftoverProcess, sig: int, kill: Callable[[int, int], None]) -> bool:
    """Signal ``proc`` only while its pid still names the same process."""
    info = reader.stat(proc.pid)
    if info is None or info.start_ticks != proc.start_ticks or info.state == "Z":
        return False
    try:
        kill(proc.pid, sig)
    except (ProcessLookupError, PermissionError):
        return False
    return True


def stop_leftovers(
    scope: WorkerScope,
    *,
    reader: ProcessReader,
    exclude: Collection[int] = (),
    grace_s: float = 5.0,
    kill: Callable[[int, int], None] = os.kill,
    stop_unit: Callable[[str], bool] = _systemctl_stop,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> StopResult:
    """Stop every process inside ``scope``; ``ok`` only when none is left.

    A scope the caller is not inside is stopped as a unit, which also takes
    anything forked mid-stop. Otherwise, and for whatever that leaves, each
    process gets SIGTERM, then SIGKILL after ``grace_s``.
    """
    leftovers = find_leftovers(scope, reader=reader, exclude=exclude)
    if leftovers is None:
        return StopResult(ok=False, error="worker scope unreadable")
    if not leftovers:
        return StopResult(ok=True)

    unit_stopped = False
    if scope.cgroup and scope.unit:
        members = reader.cgroup_procs(scope.cgroup) or []
        if os.getpid() not in members:
            unit_stopped = stop_unit(scope.unit)
            leftovers = find_leftovers(scope, reader=reader, exclude=exclude)
            if leftovers is None:
                return StopResult(ok=False, unit_stopped=unit_stopped, error="worker scope unreadable")

    signalled: list[int] = []
    for sig in (signal.SIGTERM, signal.SIGKILL):
        for proc in leftovers:
            if _signal_if_same(reader, proc, sig, kill) and proc.pid not in signalled:
                signalled.append(proc.pid)
        deadline = clock() + grace_s
        while True:
            leftovers = find_leftovers(scope, reader=reader, exclude=exclude)
            if leftovers is None:
                return StopResult(
                    ok=False, signalled=signalled, unit_stopped=unit_stopped, error="worker scope unreadable"
                )
            if not leftovers or clock() >= deadline:
                break
            sleep(_POLL_S)
        if not leftovers:
            return StopResult(ok=True, signalled=signalled, unit_stopped=unit_stopped)
    return StopResult(
        ok=False,
        signalled=signalled,
        survivors=leftovers,
        unit_stopped=unit_stopped,
        error=f"{len(leftovers)} process(es) survived SIGKILL",
    )


def only_leftovers_hold(path: Path, scope: WorkerScope, *, reader: ProcessReader) -> bool:
    """Whether every process whose cwd is inside ``path`` belongs to ``scope``.

    ``False`` when the scope or the process table cannot be read, so an
    unknown holder keeps the caller's live-cwd guard in force. A process whose
    cwd link is unreadable is invisible to that guard's ``lsof`` probe too.
    """
    leftovers = find_leftovers(scope, reader=reader)
    pids = reader.pids()
    if leftovers is None or pids is None:
        return False
    owned = {proc.pid for proc in leftovers}
    try:
        root = path.resolve()
    except OSError:
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
