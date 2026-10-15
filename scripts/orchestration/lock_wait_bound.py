"""Bounded ``flock`` waits for code that runs while a shared lock is held (#10637).

The worktree reaper holds one repository-wide cleanup lock while it re-proves
and removes a single checkout. Every other cleanup waits on that lock, so code
running under it must never wait on another lock without a bound: one stuck
holder of a task record or reaper state file would otherwise stall every
cleanup. :func:`bounded_lock_waits` sets the bound for the current context
(the reaper sets it for exactly as long as it holds the cleanup lock), and
:func:`flock_exclusive` honours it. Outside such a context the wait stays
blocking, as before.
"""

from __future__ import annotations

import contextlib
import contextvars
import fcntl
import time
from collections.abc import Iterator

_POLL_S = 0.02
_WAIT_BOUND_S: contextvars.ContextVar[float | None] = contextvars.ContextVar("lock_wait_bound_s", default=None)


class LockWaitTimeout(TimeoutError):
    """Another process held a lock past the active wait bound."""


@contextlib.contextmanager
def bounded_lock_waits(timeout_s: float) -> Iterator[None]:
    """Within this context, :func:`flock_exclusive` gives up after ``timeout_s`` seconds."""
    token = _WAIT_BOUND_S.set(max(0.0, timeout_s))
    try:
        yield
    finally:
        _WAIT_BOUND_S.reset(token)


def active_wait_bound() -> float | None:
    """The bound in force for this context, or ``None`` when waits block."""
    return _WAIT_BOUND_S.get()


def flock_exclusive(descriptor: int, *, label: str) -> None:
    """Take ``LOCK_EX`` on ``descriptor``, polling under an active bound.

    Under :func:`bounded_lock_waits` the lock is polled with ``LOCK_NB`` and
    :class:`LockWaitTimeout` is raised once the bound passes; ``label`` names
    the lock in that message (never a path). Without a bound this is a plain
    blocking ``flock``.
    """
    bound = _WAIT_BOUND_S.get()
    if bound is None:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        return
    deadline = time.monotonic() + bound
    while True:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return
        except BlockingIOError:
            if time.monotonic() >= deadline:
                raise LockWaitTimeout(f"{label} still held by another process after {bound:g}s") from None
            time.sleep(_POLL_S)
