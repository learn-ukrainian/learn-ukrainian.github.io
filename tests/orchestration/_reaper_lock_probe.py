"""Record what the reaper reads, and how it waits, while it holds the cleanup-wide lock (#10637).

The cleanup-wide lock (``worktree-reaper.lock``) is held for one removable
candidate at a time. No Monitor, forge or remote Git read runs while it is
held: a candidate reads them afresh inside its own bounded section before it
requests the lock, and under the lock its checks are answered from those
reads. Ownership storage, a local authority, is read under the lock only
inside a candidate section, with a bound. Nothing under the lock waits on
another lock without a bound.

The probe tracks which thread holds the lock, and for which phase, by wrapping
``_ReapLock`` itself, so a lock held by another thread or process never counts.
A hold ends at its real unlock: an early release before removal, the watchdog
at the hold deadline, or the context exit, whichever comes first.
"""

from __future__ import annotations

import fcntl
import math
import threading
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import pytest

from scripts.orchestration import reap_worktrees as rw

# Captured at import, before any test patches them: the real lookups reach the
# forge only through ``_run_gh``; a test's stand-in answers directly, so it is
# itself the network seam. It is answered before the lock like the lookup it
# replaces, and the seam records only the calls that would reach the forge.
_REAL_LOOKUPS = {
    name: getattr(rw, name) for name in ("_query_pr_states", "_query_pr_by_number", "_query_prs_by_head_sha")
}
_REMOTE_GIT = frozenset({"fetch", "ls-remote", "pull", "push", "remote"})
_NETWORK = frozenset({"_run_gh", "_active_task_ids", *_REAL_LOOKUPS, *(f"git {command}" for command in _REMOTE_GIT)})
_CANDIDATE_PHASE = "candidate-mutation"


@dataclass(frozen=True)
class SeamCall:
    """One Monitor, forge, ownership-storage or remote Git read.

    ``in_section`` is whether a candidate's bounded locked region was active:
    with ``held`` false, the read ran in that candidate's section before its
    cleanup-wide lock was requested.
    """

    name: str
    held: bool
    phase: str | None
    bounded: bool
    in_section: bool


def _finite_positive(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool) and math.isfinite(value) and value > 0


def _region_active() -> bool:
    return rw._remaining_locked_s() is not None


class ReaperLockProbe:
    """Seam calls, blocking lock waits and lock acquisitions of the reaper in this process."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.calls: list[SeamCall] = []
        self.blocking_waits: list[str] = []
        self.acquisitions: list[str] = []
        # Open holds: lock object id -> (holding thread, phase).
        self._held: dict[int, tuple[int, str]] = {}
        self._mutex = threading.Lock()
        self._install(monkeypatch)

    # -- holder tracking -------------------------------------------------
    def _holding(self) -> str | None:
        thread = threading.get_ident()
        with self._mutex:
            phases = [phase for holder, phase in self._held.values() if holder == thread]
            return phases[-1] if phases else None

    def _record(self, name: str, bounded: bool) -> None:
        phase = self._holding()
        self.calls.append(SeamCall(name, phase is not None, phase, bounded, _region_active()))

    def _install(self, monkeypatch: pytest.MonkeyPatch) -> None:
        probe = self
        real_enter = rw._ReapLock.__enter__
        real_unlock = rw._ReapLock._unlock

        def enter(lock: Any) -> Any:
            entered = real_enter(lock)
            with probe._mutex:
                probe._held[id(lock)] = (threading.get_ident(), lock.phase)
                probe.acquisitions.append(lock.phase)
            return entered

        def unlock(lock: Any) -> Any:
            # Every way a hold ends unlocks here once, on whichever thread ends it.
            with probe._mutex:
                probe._held.pop(id(lock), None)
            return real_unlock(lock)

        monkeypatch.setattr(rw._ReapLock, "__enter__", enter)
        monkeypatch.setattr(rw._ReapLock, "_unlock", unlock)

        def seam(
            name: str, original: Callable[..., Any], bound: Callable[[dict[str, Any]], bool]
        ) -> Callable[..., Any]:
            def call(*args: Any, **kwargs: Any) -> Any:
                probe._record(name, bound(kwargs))
                return original(*args, **kwargs)

            return call

        def explicit_timeout(kwargs: dict[str, Any]) -> bool:
            return rw._effective_timeout(kwargs.get("timeout")) is not None

        def region_only(_kwargs: dict[str, Any]) -> bool:
            return _region_active()

        def storage_timeout(kwargs: dict[str, Any]) -> bool:
            return _finite_positive(kwargs.get("timeout_s")) or _finite_positive(kwargs.get("timeout"))

        monkeypatch.setattr(rw, "_run_gh", seam("_run_gh", rw._run_gh, explicit_timeout))
        monkeypatch.setattr(rw, "_active_task_ids", seam("_active_task_ids", rw._active_task_ids, region_only))
        monkeypatch.setattr(rw, "cp_connect", seam("ownership_storage", rw.cp_connect, storage_timeout))
        for name, real in _REAL_LOOKUPS.items():
            current = getattr(rw, name)
            if current is not real:
                answered = rw._answered_before_the_lock(rw._unanswered_forge)(seam(name, current, region_only))
                monkeypatch.setattr(rw, name, answered)
        original_run = rw._run

        def run(args: list[str], **kwargs: Any) -> Any:
            if len(args) > 1 and args[0] == "git" and args[1] in _REMOTE_GIT:
                probe._record(f"git {args[1]}", explicit_timeout(kwargs))
            return original_run(args, **kwargs)

        monkeypatch.setattr(rw, "_run", run)
        real_flock = fcntl.flock

        def flock(descriptor: Any, operation: int) -> Any:
            acquiring = operation & (fcntl.LOCK_EX | fcntl.LOCK_SH)
            if acquiring and not operation & fcntl.LOCK_NB and probe._holding() is not None:
                probe.blocking_waits.append(f"flock({operation:#x}) under {probe._holding()}")
            return real_flock(descriptor, operation)

        monkeypatch.setattr(fcntl, "flock", flock)

    # -- verdicts ----------------------------------------------------------
    def under_lock(self, name: str) -> list[SeamCall]:
        return [call for call in self.calls if call.held and call.name == name]

    def before_lock(self, name: str) -> list[SeamCall]:
        """``name`` reads a candidate took in its own bounded section, before its cleanup-wide lock."""
        return [call for call in self.calls if not call.held and call.in_section and call.name == name]

    def violations(self) -> list[str]:
        """Every breach of the locked-section contract; empty when the run honoured it."""
        found: list[str] = []
        for call in self.calls:
            if not call.held:
                continue
            if call.name in _NETWORK:
                found.append(f"{call.name} under the lock (phase {call.phase})")
            elif call.phase != _CANDIDATE_PHASE:
                found.append(f"{call.name} under the lock outside a candidate section (phase {call.phase})")
            elif not call.bounded:
                found.append(f"{call.name} under the lock without a bound")
        found.extend(f"blocking lock wait: {wait}" for wait in self.blocking_waits)
        return found


def probe_reaper_lock(monkeypatch: pytest.MonkeyPatch) -> ReaperLockProbe:
    """Install a :class:`ReaperLockProbe` for the rest of the test."""
    return ReaperLockProbe(monkeypatch)
