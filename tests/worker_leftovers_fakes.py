"""A fake process table for ``scripts.orchestration.worker_leftovers`` tests (#8991).

No real process is ever read or signalled: ``kill`` records the signal and
removes the fake process unless it is marked to ignore that signal. Fake pids
sit above the kernel's default ``pid_max`` so a stray real ``os.kill`` could
not reach anything either.
"""

from __future__ import annotations

import functools
import os
import signal
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts.orchestration import worker_leftovers

FAKE_PID_BASE = 5_000_000


@dataclass
class FakeProc:
    task: str | None = None
    sid: int = 1
    state: str = "S"
    start: int = 100
    cmd: str = "python -m pytest tests/test_x.py"
    cwd: Path | None = None
    ignores: frozenset[int] = frozenset()


@dataclass
class FakeProcs:
    procs: dict[int, FakeProc] = field(default_factory=dict)
    cgroups: dict[str, list[int]] = field(default_factory=dict)
    own: str | None = None
    signals: list[tuple[int, int]] = field(default_factory=list)
    stopped_units: list[str] = field(default_factory=list)
    unit_stop_kills: bool = True
    ticks: float = 0.0

    def pids(self) -> list[int] | None:
        return list(self.procs)

    def stat(self, pid: int) -> worker_leftovers.ProcStat | None:
        proc = self.procs.get(pid)
        if proc is None:
            return None
        return worker_leftovers.ProcStat(state=proc.state, ppid=1, sid=proc.sid, start_ticks=proc.start)

    def dispatch_task_id(self, pid: int) -> str | None:
        proc = self.procs.get(pid)
        return proc.task if proc else None

    def cmdline(self, pid: int) -> str:
        proc = self.procs.get(pid)
        return proc.cmd if proc else ""

    def cwd(self, pid: int) -> Path | None:
        proc = self.procs.get(pid)
        return proc.cwd if proc else None

    def cgroup_procs(self, cgroup: str) -> list[int] | None:
        # The real caller pid may be listed as a member without a fake entry.
        return [pid for pid in self.cgroups.get(cgroup, []) if pid in self.procs or pid == os.getpid()]

    def own_cgroup(self) -> str | None:
        return self.own

    def kill(self, pid: int, sig: int) -> None:
        self.signals.append((pid, sig))
        proc = self.procs.get(pid)
        if proc is None:
            raise ProcessLookupError(pid)
        if sig not in proc.ignores:
            del self.procs[pid]

    def stop_unit(self, unit: str) -> bool:
        self.stopped_units.append(unit)
        if self.unit_stop_kills:
            for cgroup, members in self.cgroups.items():
                if cgroup.endswith(f"/{unit}.scope"):
                    for pid in members:
                        self.procs.pop(pid, None)
        return True

    def clock(self) -> float:
        self.ticks += 1.0
        return self.ticks

    def signalled(self) -> set[int]:
        return {pid for pid, _sig in self.signals}


UNKILLABLE = frozenset({signal.SIGTERM, signal.SIGKILL})


def patch_stop(monkeypatch: Any, fake: FakeProcs) -> None:
    """Route every ``stop_leftovers`` call through ``fake``'s kill and clock."""
    original = worker_leftovers.stop_leftovers
    monkeypatch.setattr(
        worker_leftovers,
        "stop_leftovers",
        functools.partial(
            original,
            kill=fake.kill,
            stop_unit=fake.stop_unit,
            sleep=lambda _s: None,
            clock=fake.clock,
        ),
    )
