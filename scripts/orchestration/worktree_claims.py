"""Per-worktree lock and active-claim scan shared by dispatch-worktree removers.

Dispatch (``scripts/delegate.py``) holds :func:`worktree_lock` from before it
mutates or creates a checkout until it publishes the task record that names
that checkout. A remover takes the same lock, refuses while
:func:`active_worktree_claim_refusal` finds an unfinished task record naming
the checkout, and removes only while it still holds the lock. No removal can
therefore land between an attachment and the record that claims it (#8610).
"""

from __future__ import annotations

import contextlib
import fcntl
import hashlib
import json
import os
import re
import threading
import time
from collections.abc import Iterator
from pathlib import Path

# Lock files live in ``<git common dir>/<LOCK_DIR_NAME>`` so every checkout of
# the repository contends on the same file.
LOCK_DIR_NAME = "lu-worktree-locks"
DEFAULT_LOCK_TIMEOUT_S = 30.0
_LOCK_POLL_S = 0.05
# (lock key, thread ident) pairs this process holds; see worktree_lock.
_HELD_LOCKS: set[tuple[str, int]] = set()

# Every status a finished task persists. Any other value, including
# ``needs_finalize``, ``spawning``, ``running``, ``""``, a missing status, or
# an unknown value such as ``queued``, still claims the task's worktree.
RELEASED_TASK_STATUSES = frozenset(
    {
        "done",
        "failed",
        "no_deliverable",
        "timeout",
        "rate_limited",
        "cancelled",
        "crashed",
        "dry_run",
        "reaped",
    }
)


class WorktreeLockError(RuntimeError):
    """A per-worktree advisory lock could not be acquired."""


class WorktreeLockTimeout(WorktreeLockError):
    """Another process held the worktree lock for longer than the timeout."""


class WorktreeLockReentry(WorktreeLockError):
    """This process already holds the worktree lock; nesting would self-deadlock."""


def lock_path(path: Path | str, *, lock_dir: Path) -> tuple[str, Path]:
    """Return the canonical absolute worktree path and its lock file."""
    raw = Path(path).expanduser()
    if not raw.is_absolute():
        raise WorktreeLockError(f"worktree lock path must be absolute: {raw}")
    try:
        canonical = str(raw.resolve())
    except (OSError, RuntimeError) as exc:
        raise WorktreeLockError(f"worktree lock path {raw} unresolvable: {type(exc).__name__}: {exc}") from exc
    key = hashlib.sha256(canonical.encode("utf-8", "surrogateescape")).hexdigest()[:32]
    return canonical, lock_dir / f"{key}.lock"


@contextlib.contextmanager
def worktree_lock(path: Path | str, *, lock_dir: Path, timeout_s: float | None = None) -> Iterator[None]:
    """Hold an exclusive ``flock`` advisory lock for one worktree path.

    The lock file is ``<lock_dir>/<key>.lock``, where the key is the first 32
    hex digits of the SHA-256 of the canonical absolute path. Lock files are
    never deleted: unlinking one while it is held would let a second process
    lock a fresh inode, and a stale file is harmless. The lock is polled with
    ``LOCK_NB`` until ``timeout_s`` (default :data:`DEFAULT_LOCK_TIMEOUT_S`)
    elapses, then :class:`WorktreeLockTimeout` is raised. Every failure raises
    a :class:`WorktreeLockError`. ``flock`` locks conflict between two opens in
    one process too, so a nested acquisition on the same thread raises
    :class:`WorktreeLockReentry` instead of waiting on itself.
    """
    canonical, lock_file = lock_path(path, lock_dir=lock_dir)
    holder = (lock_file.stem, threading.get_ident())
    if holder in _HELD_LOCKS:
        raise WorktreeLockReentry(f"worktree lock for {canonical} is already held by this thread")
    if timeout_s is None:
        timeout_s = DEFAULT_LOCK_TIMEOUT_S
    try:
        lock_file.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        fd = os.open(lock_file, os.O_RDWR | os.O_CREAT | os.O_CLOEXEC, 0o600)
    except OSError as exc:
        raise WorktreeLockError(f"worktree lock for {canonical} unavailable: {type(exc).__name__}: {exc}") from exc
    try:
        deadline = time.monotonic() + max(timeout_s, 0.0)
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise WorktreeLockTimeout(
                        f"worktree lock for {canonical} still held by another process after {timeout_s:g}s"
                    ) from None
                time.sleep(_LOCK_POLL_S)
            except OSError as exc:
                raise WorktreeLockError(f"worktree lock for {canonical} failed: {type(exc).__name__}: {exc}") from exc
    except BaseException:
        os.close(fd)
        raise
    _HELD_LOCKS.add(holder)
    try:
        yield
    finally:
        _HELD_LOCKS.discard(holder)
        # Closing the descriptor releases the flock.
        os.close(fd)


def lock_refusal(exc: WorktreeLockError) -> str:
    """Return the skip reason a remover records when the lock is not taken."""
    if isinstance(exc, WorktreeLockTimeout):
        return "worktree lock busy"
    if isinstance(exc, WorktreeLockReentry):
        return "worktree lock already held by this thread"
    return "worktree lock unavailable"


def resolve_claim_path(raw_path: str, *, repo_root: Path) -> Path:
    """Resolve a recorded ``worktree_path`` the way dispatch resolves ``--worktree``."""
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = repo_root / path
    return path.resolve()


def worktree_claim_needles(worktree: Path, target: Path) -> frozenset[bytes]:
    """Byte strings one of which every task record naming ``worktree`` contains.

    A record can spell the claim as the absolute path, its resolved form, a
    repo-relative path, or with a trailing slash. Every such spelling ends in
    the checkout's own directory name, so that name, raw and JSON-escaped, is
    the pre-filter. A record that names the checkout through a differently
    named symlink is still parsed unless its status shows it released (see
    :func:`record_may_claim_worktree`). An empty set means every record is a
    candidate.
    """
    needles: set[bytes] = set()
    for name in {worktree.name, target.name}:
        if name:
            needles.add(name.encode("utf-8", "surrogateescape"))
            needles.add(json.dumps(name)[1:-1].encode("ascii"))
    return frozenset(needles)


_STATUS_KEY_RE = re.compile(rb'"status"\s*:')
# A ``status`` key whose value is a released status, spelled as ``json.dumps``
# writes it. Built from RELEASED_TASK_STATUSES so the two never drift.
_RELEASED_STATUS_TOKEN_RE = re.compile(
    rb'"status"\s*:\s*"(?:'
    + b"|".join(re.escape(status.encode("ascii")) for status in sorted(RELEASED_TASK_STATUSES))
    + rb')"'
)


def record_may_claim_worktree(raw: bytes, needles: frozenset[bytes]) -> bool:
    """Return whether a task record's bytes must be parsed by the claim scan.

    A record is skipped unparsed only when its bytes prove it released: it
    does not contain the checkout's directory name, it has at least one
    ``status`` key, and every ``status`` key carries a released status. Any
    other record is parsed, including one with an unknown status such as
    ``queued``, so the pre-filter can never release a claim that
    :func:`active_worktree_claim_refusal` would honor (#8610).
    """
    if not needles or any(needle in raw for needle in needles):
        return True
    released_status_seen = False
    # ``bytes.find`` then an anchored match is about a third cheaper than
    # ``re.finditer`` over the large finished records that dominate the scan.
    position = raw.find(b'"status"')
    while position != -1:
        if _STATUS_KEY_RE.match(raw, position):
            if not _RELEASED_STATUS_TOKEN_RE.match(raw, position):
                return True
            released_status_seen = True
        position = raw.find(b'"status"', position + 1)
    return not released_status_seen


def active_worktree_claim_refusal(
    worktree: Path,
    *,
    tasks_dir: Path,
    repo_root: Path,
    owner_task_id: str | None = None,
    owner_state_file: Path | None = None,
) -> str | None:
    """Return a skip reason when an unfinished task record still claims ``worktree``.

    A task record whose status is not in :data:`RELEASED_TASK_STATUSES` and
    whose ``worktree_path`` resolves to the same checkout blocks removal.
    Claims are resolved relative to ``repo_root``, exactly as dispatch
    resolves ``--worktree``. The record of ``owner_task_id`` (the task
    settling its own checkout) and ``owner_state_file`` are exempt; ``None``
    exempts nothing. Only candidate records (:func:`record_may_claim_worktree`)
    are parsed, so an unrelated finished corrupt record never blocks removal,
    while a candidate that cannot be read, parsed, or resolved does. Every
    failure is a skip reason, never an exception. Returns ``None`` when
    removal may proceed.
    """

    def refused(state_file: Path, problem: str) -> str:
        return f"task record {state_file.name} {problem}; refusing worktree removal"

    try:
        target = resolve_claim_path(str(worktree), repo_root=repo_root)
    except (OSError, RuntimeError, ValueError) as exc:
        return f"worktree path unresolvable ({type(exc).__name__}); refusing worktree removal"
    needles = worktree_claim_needles(worktree, target)
    try:
        state_files = sorted(tasks_dir.glob("*.json"))
    except OSError as exc:
        return f"task claims unreadable ({type(exc).__name__}); refusing worktree removal"
    for state_file in state_files:
        if owner_state_file is not None and state_file == owner_state_file:
            continue
        try:
            raw = state_file.read_bytes()
        except FileNotFoundError:
            # Removed between glob and read: it no longer claims anything.
            continue
        except OSError:
            return refused(state_file, "unreadable")
        if not record_may_claim_worktree(raw, needles):
            continue
        try:
            record = json.loads(raw)
        except (ValueError, RecursionError):
            record = None
        claimed_path = record.get("worktree_path") if isinstance(record, dict) else None
        if not isinstance(record, dict) or not isinstance(claimed_path, str | None):
            return refused(state_file, "unreadable")
        if not claimed_path or (owner_task_id is not None and record.get("task_id") == owner_task_id):
            continue
        status = record.get("status")
        if isinstance(status, str) and status in RELEASED_TASK_STATUSES:
            continue
        try:
            claimed = resolve_claim_path(claimed_path, repo_root=repo_root)
        except (OSError, RuntimeError, ValueError):
            return refused(state_file, "worktree_path unresolvable")
        if claimed == target:
            return f"worktree claimed by active task {record.get('task_id') or state_file.stem}"
    return None
