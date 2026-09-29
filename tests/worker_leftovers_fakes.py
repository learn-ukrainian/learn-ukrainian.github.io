"""A fake process table for ``scripts.orchestration.worker_leftovers`` tests (#8991).

No real process is ever read or signalled: the fake pidfd pins the fake
process it was opened on, records each signal, and removes that process
unless it is marked to ignore the signal. A pidfd whose process has gone (even
if its pid was handed to a new fake process) fails with ``ProcessLookupError``,
as the kernel's does. Fake pids sit above the kernel's default ``pid_max`` so a
stray real signal could not reach anything either.
"""

from __future__ import annotations

import functools
import os
import signal
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts.orchestration import dispatch_isolation, worker_leftovers

FAKE_PID_BASE = 5_000_000
TASK_ID = "t1"
RUN_NONCE = "n0nce"
UNIT = f"lu-worker-{TASK_ID}-{RUN_NONCE}-0123abcd"
SCOPE_CGROUP = dispatch_isolation.scope_cgroup(UNIT, uid=os.getuid())
OUTSIDE_CGROUP = "/user.slice/user-0.slice/session-1.scope"


def scope_of(task_id: str = TASK_ID, **fields: Any) -> worker_leftovers.WorkerScope:
    """A ``WorkerScope`` that passes the launch-identity check by default."""
    defaults: dict[str, Any] = {"launch_mode": "popen-fallback", "run_nonce": RUN_NONCE}
    if fields.get("launch_mode") == "scope":
        defaults.update(unit=UNIT, cgroup=SCOPE_CGROUP)
    return worker_leftovers.WorkerScope(task_id=task_id, **{**defaults, **fields})


@dataclass
class FakeProc:
    task: str | None = None
    sid: int = 1
    state: str = "S"
    start: int = 100
    cmd: str = "python -m pytest tests/test_x.py"
    cwd: Path | None = None
    ignores: frozenset[int] = frozenset()
    uid: int = field(default_factory=os.getuid)
    env_unreadable: bool = False


@dataclass
class FakeProcs:
    procs: dict[int, FakeProc] = field(default_factory=dict)
    cgroups: dict[str, list[int]] = field(default_factory=dict)
    own: str | None = OUTSIDE_CGROUP
    signals: list[tuple[int, int]] = field(default_factory=list)
    stopped_units: list[str] = field(default_factory=list)
    unit_stop_kills: bool = True
    unreadable_cgroups: set[str] = field(default_factory=set)
    ticks: float = 0.0
    _fds: dict[int, tuple[int, FakeProc]] = field(default_factory=dict)

    def pids(self) -> list[int]:
        return list(self.procs)

    def stat(self, pid: int) -> worker_leftovers.ProcStat | None:
        proc = self.procs.get(pid)
        if proc is None:
            return None
        return worker_leftovers.ProcStat(state=proc.state, ppid=1, sid=proc.sid, start_ticks=proc.start)

    def real_uid(self, pid: int) -> int | None:
        proc = self.procs.get(pid)
        return proc.uid if proc else None

    def dispatch_task_id(self, pid: int) -> str | None:
        proc = self.procs.get(pid)
        if proc is not None and proc.env_unreadable:
            raise worker_leftovers.ScanUnknown(f"/proc/{pid}/environ: Permission denied")
        return proc.task if proc else None

    def proc_cgroup(self, pid: int) -> str | None:
        if pid not in self.procs:
            return None
        return next((cgroup for cgroup, members in self.cgroups.items() if pid in members), OUTSIDE_CGROUP)

    def cmdline(self, pid: int) -> str:
        proc = self.procs.get(pid)
        return proc.cmd if proc else ""

    def cwd(self, pid: int) -> Path | None:
        proc = self.procs.get(pid)
        return proc.cwd if proc else None

    def cgroup_procs(self, cgroup: str) -> list[int] | None:
        if cgroup in self.unreadable_cgroups:
            raise worker_leftovers.ScanUnknown(f"{cgroup}/cgroup.procs: Permission denied")
        if cgroup not in self.cgroups:
            return None
        # The real caller pid may be listed as a member without a fake entry.
        return [pid for pid in self.cgroups[cgroup] if pid in self.procs or pid == os.getpid()]

    def own_cgroup(self) -> str | None:
        return self.own

    def pidfd_open(self, pid: int) -> int:
        proc = self.procs.get(pid)
        if proc is None:
            raise ProcessLookupError(pid)
        fd = 1000 + len(self._fds)
        self._fds[fd] = (pid, proc)
        return fd

    def pidfd_send(self, fd: int, sig: int) -> None:
        pid, pinned = self._fds[fd]
        if self.procs.get(pid) is not pinned:
            raise ProcessLookupError(pid)
        self.signals.append((pid, sig))
        if sig not in pinned.ignores:
            del self.procs[pid]

    def pidfd_ops(self) -> worker_leftovers.PidfdOps:
        return worker_leftovers.PidfdOps(open=self.pidfd_open, send=self.pidfd_send, close=lambda _fd: None)

    def stop_unit(self, unit: str) -> bool:
        self.stopped_units.append(unit)
        if self.unit_stop_kills:
            for cgroup, members in list(self.cgroups.items()):
                if cgroup.endswith(f"/{unit}.scope"):
                    for pid in members:
                        self.procs.pop(pid, None)
                    del self.cgroups[cgroup]
        return True

    def clock(self) -> float:
        self.ticks += 1.0
        return self.ticks

    def signalled(self) -> set[int]:
        return {pid for pid, _sig in self.signals}


UNKILLABLE = frozenset({signal.SIGTERM, signal.SIGKILL})


def stop_kwargs(fake: FakeProcs) -> dict[str, Any]:
    return {
        "pidfd": fake.pidfd_ops(),
        "stop_unit": fake.stop_unit,
        "sleep": lambda _s: None,
        "clock": fake.clock,
    }


def patch_stop(monkeypatch: Any, fake: FakeProcs) -> None:
    """Route every ``stop_leftovers`` call through ``fake``'s pidfd, unit stop and clock."""
    original = worker_leftovers.stop_leftovers
    monkeypatch.setattr(worker_leftovers, "stop_leftovers", functools.partial(original, **stop_kwargs(fake)))
