"""The guarded worktree-removal chokepoint shared by every remover (#8610).

Dispatch (``scripts/delegate.py``) holds :func:`worktree_lock` from before it
mutates or creates a checkout until it publishes the task record that names
that checkout. :func:`remove_unclaimed_worktree` takes the same lock, runs the
caller's ownership proof, refuses while :func:`active_worktree_claim_refusal`
finds an unfinished task record naming the checkout, and removes only while it
still holds the lock. No removal can therefore land between an attachment and
the record that claims it.

Python callers use :func:`remove_unclaimed_worktree`; shell and YAML callers
use ``python -m scripts.orchestration.worktree_claims remove``. The one raw
``git worktree remove`` is :func:`git_worktree_remove`, and
``tests/orchestration/test_worktree_removal_invariant.py`` fails on any other
removal call site under ``scripts/``.
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

from scripts.common.git_context import sanitized_git_env
from scripts.common.repo_root import main_checkout_root
from scripts.orchestration.fleet_repos import FleetRepoError, load_fleet_repos
from scripts.orchestration.task_record_store import task_record_path
from scripts.path_safety import assert_delete_target

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


LOCK_BUSY = "worktree lock busy"
LOCK_REENTRY = "worktree lock already held by this thread"
LOCK_UNAVAILABLE = "worktree lock unavailable"
# Every skip reason :func:`lock_refusal` returns.
LOCK_REFUSALS = frozenset({LOCK_BUSY, LOCK_REENTRY, LOCK_UNAVAILABLE})


def lock_refusal(exc: WorktreeLockError) -> str:
    """Return the skip reason a remover records when the lock is not taken."""
    if isinstance(exc, WorktreeLockTimeout):
        return LOCK_BUSY
    if isinstance(exc, WorktreeLockReentry):
        return LOCK_REENTRY
    return LOCK_UNAVAILABLE


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
    resolves ``--worktree``. The owner's canonical record is exempt only after
    its embedded task ID and non-empty run nonce establish the run identity.
    If that proof is absent, the owner receives no exemption and the regular
    scan decides whether its record is an unfinished claim. Another record
    with the same task ID remains a claim. ``None`` exempts nothing. Only
    candidate records (:func:`record_may_claim_worktree`)
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
    owner_identity: tuple[Path, str] | None = None
    if owner_task_id is not None:
        owner_path = owner_state_file or task_record_path(tasks_dir, owner_task_id)
        try:
            owner = json.loads(owner_path.read_bytes())
        except (OSError, ValueError, RecursionError):
            owner = None
        nonce = owner.get("run_nonce") if isinstance(owner, dict) else None
        if (
            isinstance(owner, dict)
            and owner.get("task_id") == owner_task_id
            and isinstance(nonce, str)
            and nonce.strip()
        ):
            owner_identity = (owner_path, nonce)
    try:
        state_files = sorted(tasks_dir.glob("*.json"))
    except OSError as exc:
        return f"task claims unreadable ({type(exc).__name__}); refusing worktree removal"
    for state_file in state_files:
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
        if (
            owner_identity is not None
            and state_file == owner_identity[0]
            and record.get("task_id") == owner_task_id
            and record.get("run_nonce") == owner_identity[1]
        ):
            continue
        if not claimed_path:
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


# Read-only git probes degrade to "unknown" instead of hanging a remover.
_GIT_PROBE_TIMEOUT_S = 30.0
# ``git worktree remove`` of a large checkout (node_modules, a worker .venv)
# can take a while; past this bound the removal is reported as an error.
GIT_WORKTREE_REMOVE_TIMEOUT_S = 120.0


@dataclasses.dataclass(frozen=True)
class WorktreeRemoval:
    """Outcome of :func:`remove_unclaimed_worktree`.

    ``action`` is ``removed``, ``skipped`` (a guard refused; nothing was
    touched), or ``error`` (removal was attempted or a step raised).
    """

    action: str
    path: str
    reason: str
    branch: str | None = None
    dirty: bool | None = None
    error: str | None = None

    def as_record(self) -> dict[str, Any]:
        """Return the outcome as a JSON-ready dict."""
        return dataclasses.asdict(self)


def _git_probe(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str] | None:
    """Run a read-only git command; ``None`` when it could not run at all."""
    try:
        return subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            env=sanitized_git_env(),
            timeout=_GIT_PROBE_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def repository_lock_dir(repo_root: Path) -> Path:
    """Return ``<git common dir>/<LOCK_DIR_NAME>`` for ``repo_root``'s repository.

    Raises :class:`WorktreeLockError` when the common dir cannot be resolved.
    """
    proc = _git_probe(["rev-parse", "--path-format=absolute", "--git-common-dir"], cwd=repo_root)
    common_dir = (proc.stdout or "").strip() if proc is not None and proc.returncode == 0 else ""
    if not common_dir:
        raise WorktreeLockError(f"git common dir of {repo_root} unresolvable")
    return Path(common_dir) / LOCK_DIR_NAME


class ControlPlaneError(RuntimeError):
    """The control-plane root of a repository could not be resolved."""


def public_primary_root() -> Path:
    """Return the public primary checkout that owns ``scripts/delegate.py``.

    Test seam: tests monkeypatch this to lay out a public primary and sibling
    checkouts under a temporary directory.
    """
    return main_checkout_root(Path(__file__).resolve().parents[2])


def control_plane_root(repo_root: Path) -> Path:
    """Return the checkout whose ``batch_state/`` and lock dir govern ``repo_root``'s worktrees.

    Dispatch keeps every task record and per-worktree lock on the public
    primary, even for ``--repo infra-private|hramatka`` worktrees (#672 P2.1,
    :mod:`scripts.orchestration.fleet_repos`). A worktree of an allowlisted
    sibling checkout therefore resolves to the public primary, so a remover
    acting on it reads the records and takes the lock dispatch wrote and holds
    (#8624). Any other repository is its own control plane. Raises
    :class:`ControlPlaneError` when the fleet catalog cannot be read: a caller
    that mutates must then refuse, since it cannot tell whether the repository
    is a sibling.
    """
    public = public_primary_root().resolve()
    repo = main_checkout_root(repo_root).resolve()
    try:
        catalog = load_fleet_repos()
    except (FleetRepoError, OSError, ValueError) as exc:
        raise ControlPlaneError(f"fleet repository catalog unreadable ({type(exc).__name__}: {exc})") from exc
    for fleet_repo in catalog.values():
        if not fleet_repo.default and (public.parent / fleet_repo.local_name).resolve() == repo:
            return public
    return repo


def owning_repo_root(worktree: Path, *, default: Path) -> Path:
    """Return the primary checkout a linked ``worktree`` belongs to, else ``default``.

    Read from the worktree's own ``.git`` pointer, so a sibling-repo checkout
    is git-operated in its own repository rather than the public primary.
    """
    root = main_checkout_root(worktree)
    return root if root != worktree and (root / ".git").is_dir() else default


def checked_out_branch(worktree: Path) -> str | None:
    """Return the branch checked out at ``worktree``, or ``None`` when detached or unknown."""
    proc = _git_probe(["rev-parse", "--abbrev-ref", "HEAD"], cwd=worktree)
    if proc is None or proc.returncode != 0:
        return None
    name = (proc.stdout or "").strip()
    return name if name and name != "HEAD" else None


def worktree_is_dirty(worktree: Path) -> bool | None:
    """Return whether ``git status --porcelain`` lists anything; ``None`` when unknown."""
    proc = _git_probe(["status", "--porcelain"], cwd=worktree)
    if proc is None or proc.returncode != 0:
        return None
    return bool((proc.stdout or "").strip())


def git_worktree_remove(repo_root: Path, worktree: Path, *, force: bool) -> str | None:
    """Run the repository's only raw ``git worktree remove``; return an error or ``None``.

    Only :func:`remove_unclaimed_worktree` and the scheduled reaper's guarded
    pipeline call this; ``tests/orchestration/test_worktree_removal_invariant.py``
    fails on any other caller. ``force`` first passes the delete-target guard,
    then runs ``git worktree remove --force``, which a clean porcelain tree
    still needs when it holds ignored residue such as a worker ``.venv``.
    Without ``force`` git itself refuses a checkout with modified or untracked
    files, and a locked one. The removal is bounded by
    :data:`GIT_WORKTREE_REMOVE_TIMEOUT_S`; a timeout is an error, never a
    removal, since the killed git may leave a half-deleted checkout behind.
    """
    target = worktree
    if force:
        try:
            target = assert_delete_target(worktree, repo_root=repo_root)
        except ValueError as exc:
            return f"delete guard refused worktree target: {exc}"
    argv = ["git", "worktree", "remove", *(["--force"] if force else []), str(target)]
    try:
        proc = subprocess.run(
            argv,
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            env=sanitized_git_env(),
            timeout=GIT_WORKTREE_REMOVE_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        return f"git worktree remove timed out after {GIT_WORKTREE_REMOVE_TIMEOUT_S:g}s"
    except PermissionError as exc:
        return f"permission denied removing worktree: {exc}"
    except OSError as exc:
        return f"OS error removing worktree: {exc}"
    if proc.returncode == 0:
        return None
    detail = (proc.stderr or proc.stdout or "").strip()
    failure = detail.splitlines()[-1] if detail else f"exit {proc.returncode}"
    if "permission" in failure.lower() or "denied" in failure.lower():
        return f"permission denied removing worktree: {failure}"
    return failure


def remove_unclaimed_worktree(
    worktree: Path,
    *,
    repo_root: Path,
    reason: str,
    owner_task_id: str | None,
    releasable: Callable[[], tuple[bool, str]] | None = None,
    force: bool = False,
    dirty_probe: Callable[[Path], bool | None] | None = None,
    unlock: bool = False,
    control_root: Path | None = None,
    tasks_dir: Path | None = None,
    lock_dir: Path | None = None,
    lock_timeout_s: float | None = None,
) -> WorktreeRemoval:
    """Remove ``worktree`` unless a live task claims it. Every remover comes here (#8610).

    Holding :func:`worktree_lock` for ``worktree``, in order:

    1. ``releasable()``, the caller's ownership proof returning ``(ok, detail)``;
    2. with ``force``, ``dirty_probe(worktree)`` (default
       :func:`worktree_is_dirty`) must return ``False``: dirty or unknown
       refuses;
    3. :func:`active_worktree_claim_refusal`, which exempts only
       ``owner_task_id``'s own record (``None`` exempts nothing);
    4. with ``unlock``, ``git worktree unlock``, for a caller that holds a git
       worktree lock of its own on the checkout (an ACP runtime);
    5. :func:`git_worktree_remove`.

    Dispatch holds the same lock from before it touches a checkout until it
    publishes the record that names it, so every attachment is either visible
    to step 3 or waits and then finds the checkout gone. ``repo_root`` is the
    primary checkout of the worktree's repository: git runs there and
    recorded claims resolve against it. ``control_root`` is the checkout that
    holds the task records and lock dir; it defaults to
    :func:`control_plane_root`, which is ``repo_root`` itself except for a
    ``--repo`` sibling repository, whose records and locks live on the public
    primary (#8624). ``tasks_dir`` defaults to
    ``<control_root>/batch_state/tasks`` and ``lock_dir`` to
    :func:`repository_lock_dir` of ``control_root``. ``reason`` is the
    caller's purpose, recorded on success. This never raises.
    """
    branch: str | None = None
    dirty: bool | None = None

    def outcome(action: str, why: str, *, error: str | None = None) -> WorktreeRemoval:
        return WorktreeRemoval(action=action, path=str(worktree), reason=why, branch=branch, dirty=dirty, error=error)

    with contextlib.ExitStack() as locks:
        try:
            if tasks_dir is None or lock_dir is None:
                control_root = control_root if control_root is not None else control_plane_root(repo_root)
            if tasks_dir is None:
                tasks_dir = control_root / "batch_state" / "tasks"
            if lock_dir is None:
                lock_dir = repository_lock_dir(control_root)
            locks.enter_context(worktree_lock(worktree, lock_dir=lock_dir, timeout_s=lock_timeout_s))
        except ControlPlaneError as exc:
            return outcome("skipped", LOCK_UNAVAILABLE, error=str(exc))
        except WorktreeLockError as exc:
            return outcome("skipped", lock_refusal(exc), error=str(exc))
        try:
            ok, detail = releasable() if releasable is not None else (True, "")
            if not ok:
                return outcome("skipped", detail)
            branch = checked_out_branch(worktree)
            if force:
                dirty = (dirty_probe if dirty_probe is not None else worktree_is_dirty)(worktree)
                if dirty is not False:
                    return outcome("skipped", "dirty or unknown; refusing worktree removal")
            claim_refusal = active_worktree_claim_refusal(
                worktree,
                tasks_dir=tasks_dir,
                repo_root=repo_root,
                owner_task_id=owner_task_id,
                owner_state_file=task_record_path(tasks_dir, owner_task_id) if owner_task_id is not None else None,
            )
            if claim_refusal is not None:
                return outcome("skipped", claim_refusal)
            if unlock:
                # Best effort: a checkout that stays locked fails the removal,
                # which reports git's own error.
                _git_probe(["worktree", "unlock", str(worktree)], cwd=repo_root)
            error = git_worktree_remove(repo_root, worktree, force=force)
        except Exception as exc:
            return outcome("error", "worktree removal raised", error=f"{type(exc).__name__}: {exc}")
        if error is not None:
            return outcome("error", "worktree removal failed", error=error)
        return outcome("removed", f"{reason} ({detail})" if detail else reason)


def owner_release_refusal(worktree: Path, *, owner_task_id: str, tasks_dir: Path, repo_root: Path) -> str | None:
    """Return why ``owner_task_id`` may not release ``worktree``, or ``None`` when it may.

    The owner's record must identify the requested task and run with a
    non-empty ``run_nonce``, be finished (its status is in
    :data:`RELEASED_TASK_STATUSES`), name ``worktree`` as its
    ``worktree_path``, and record ``worktree_reused: false``, the proof that
    its dispatch created the checkout. A reused checkout belongs to its
    creator, which reaps it.
    """
    record_path = task_record_path(tasks_dir, owner_task_id)
    try:
        record = json.loads(record_path.read_bytes())
    except FileNotFoundError:
        return f"owner task {owner_task_id} has no task record; refusing worktree removal"
    except (OSError, ValueError, RecursionError):
        return f"owner task record {record_path.name} unreadable; refusing worktree removal"
    if not isinstance(record, dict):
        return f"owner task record {record_path.name} unreadable; refusing worktree removal"
    if record.get("task_id") != owner_task_id:
        return f"owner task {owner_task_id} identity mismatch; refusing worktree removal"
    nonce = record.get("run_nonce")
    if not isinstance(nonce, str) or not nonce.strip():
        return f"owner task {owner_task_id} has no valid run_nonce; refusing worktree removal"
    status = record.get("status")
    if not isinstance(status, str) or status not in RELEASED_TASK_STATUSES:
        return f"owner task {owner_task_id} is not finished (status {status!r}); refusing worktree removal"
    claimed_path = record.get("worktree_path")
    if not isinstance(claimed_path, str) or not claimed_path:
        return f"owner task {owner_task_id} records no worktree_path; refusing worktree removal"
    try:
        claimed = resolve_claim_path(claimed_path, repo_root=repo_root)
        target = resolve_claim_path(str(worktree), repo_root=repo_root)
    except (OSError, RuntimeError, ValueError):
        return f"owner task {owner_task_id} worktree_path unresolvable; refusing worktree removal"
    if claimed != target:
        return f"owner task {owner_task_id} records a different worktree_path; refusing worktree removal"
    if record.get("worktree_reused") is not False:
        return f"owner task {owner_task_id} did not create this worktree; its creator reaps"
    return None


EXIT_REMOVED = 0
EXIT_ERROR = 2
EXIT_REFUSED = 3


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.orchestration.worktree_claims",
        description=(
            "Guarded git worktree removal: remove a checkout only when no unfinished task claims it (#8610).\n"
            "Use it from shell and YAML callers instead of raw `git worktree remove`; Python callers\n"
            "call remove_unclaimed_worktree() directly. Not for dirty checkouts: it never forces."
        ),
        epilog=(
            "Commands:\n"
            "  remove PATH   Remove one linked worktree through the guarded chokepoint.\n"
            "                Run `remove --help` for its four guards.\n"
            "\n"
            "Examples:\n"
            "  .venv/bin/python -m scripts.orchestration.worktree_claims remove \\\n"
            "      .worktrees/dispatch/codex/impl-123 --owner-task-id impl-123 --reason 'rb2 failed-dispatch cleanup'\n"
            "  .venv/bin/python -m scripts.orchestration.worktree_claims remove ../learn-ukrainian-wt-817 --json\n"
            "\n"
            "Outputs:\n"
            "  remove deletes the checkout and its git worktree registration; branch refs are never touched.\n"
            "  stdout: 'removed: PATH (REASON)' or, with --json, the outcome object. stderr: refusal/error reason.\n"
            "\n"
            "Exit codes:\n"
            "  0  removed\n"
            "  2  error: git failed to remove PATH, or the arguments are unusable\n"
            "  3  refused: a guard failed and nothing was removed\n"
            "\n"
            "Related: scripts/delegate.py (dispatch holds the same per-worktree lock),\n"
            "  scripts/orchestration/reap_worktrees.py (scheduled reaper),\n"
            "  tests/orchestration/test_worktree_removal_invariant.py, issue #8610."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    commands = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")
    remove = commands.add_parser(
        "remove",
        help="Remove one linked worktree unless a live task claims it.",
        description=(
            "Remove one linked git worktree under the per-worktree lock dispatch holds while it attaches.\n"
            "Use it for any shell-side cleanup of a checkout; never for the primary checkout."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.orchestration.worktree_claims remove \\\n"
            "      .worktrees/dispatch/codex/impl-123 --owner-task-id impl-123 --reason 'rb2 failed-dispatch cleanup'\n"
            "  .venv/bin/python -m scripts.orchestration.worktree_claims remove ../learn-ukrainian-wt-817 \\\n"
            "      --reason 'wt.sh clean 817'\n"
            "  .venv/bin/python -m scripts.orchestration.worktree_claims remove .worktrees/dispatch/claude/x --json\n"
            "\n"
            "Guards, all checked while holding <public git common dir>/lu-worktree-locks/<key>.lock:\n"
            "  1. PATH is a registered linked worktree of its repository, never the primary checkout.\n"
            "  2. With --owner-task-id: that task's record is finished, names PATH as its\n"
            "     worktree_path, and records worktree_reused: false (its dispatch created PATH).\n"
            "  3. No other unfinished task record in <public primary>/batch_state/tasks names PATH\n"
            "     (the public primary also holds the records and locks of --repo sibling worktrees, #8624).\n"
            "  4. Plain `git worktree remove`: git refuses modified, untracked, or locked checkouts.\n"
            "\n"
            "Outputs:\n"
            "  Deletes the checkout and its git worktree registration; branch refs are never touched.\n"
            "  stdout: 'removed: PATH (REASON)', or with --json one object\n"
            "          {action, path, reason, branch, dirty, error} for every outcome.\n"
            "  stderr: the refusal or error reason.\n"
            "\n"
            "Exit codes:\n"
            "  0  removed\n"
            "  2  error: git failed to remove PATH, or the arguments are unusable\n"
            "  3  refused: a guard failed and nothing was removed\n"
            "\n"
            "Related: remove_unclaimed_worktree() in scripts/orchestration/worktree_claims.py; issue #8610."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    remove.add_argument(
        "path",
        metavar="PATH",
        help="Worktree to remove; a relative path resolves against the current directory. "
        "Example: .worktrees/dispatch/codex/impl-123",
    )
    remove.add_argument(
        "--owner-task-id",
        metavar="ID",
        default=None,
        help="Task on whose behalf PATH is removed (guard 2). Its own record is exempt from the claim scan. "
        "Default: none, so every unfinished record naming PATH refuses. Example: impl-123",
    )
    remove.add_argument(
        "--reason",
        default="operator cleanup",
        help="Purpose recorded in the outcome. Default: 'operator cleanup'. Example: 'wt.sh clean 817'",
    )
    remove.add_argument(
        "--json",
        action="store_true",
        help="Print the outcome as one JSON object on stdout for every outcome. Default: off.",
    )
    return parser


def _cli_removal(args: argparse.Namespace, worktree: Path, *, repo_root: Path, control_root: Path) -> WorktreeRemoval:
    # Deferred: containment's git plumbing is only needed by the CLI.
    from scripts.guardrails import worktree_containment

    tasks_dir = control_root / "batch_state" / "tasks"

    def releasable() -> tuple[bool, str]:
        registered = worktree_containment.registered_worktrees(repo_root)
        if not registered:
            return False, "git worktree list failed; refusing worktree removal"
        if worktree == registered[0]:
            return False, "PATH is the primary checkout; refusing worktree removal"
        if worktree not in registered[1:]:
            return False, "not a registered linked worktree; refusing worktree removal"
        if args.owner_task_id is None:
            return True, ""
        refusal = owner_release_refusal(
            worktree, owner_task_id=args.owner_task_id, tasks_dir=tasks_dir, repo_root=repo_root
        )
        return (False, refusal) if refusal is not None else (True, f"owner task {args.owner_task_id}")

    return remove_unclaimed_worktree(
        worktree,
        repo_root=repo_root,
        reason=args.reason,
        owner_task_id=args.owner_task_id,
        releasable=releasable,
        control_root=control_root,
    )


def _cli_remove(args: argparse.Namespace) -> int:
    from scripts.guardrails import worktree_containment

    raw = Path(args.path).expanduser()
    worktree = (raw if raw.is_absolute() else Path.cwd() / raw).resolve()
    try:
        repo_root = worktree_containment.resolve_main_root(worktree if worktree.exists() else worktree.parent)
    except worktree_containment.NotAGitRepositoryError:
        removal = WorktreeRemoval(
            action="skipped", path=str(worktree), reason="not inside a git repository; refusing worktree removal"
        )
    else:
        try:
            control_root = control_plane_root(repo_root)
        except ControlPlaneError as exc:
            removal = WorktreeRemoval(action="skipped", path=str(worktree), reason=LOCK_UNAVAILABLE, error=str(exc))
        else:
            removal = _cli_removal(args, worktree, repo_root=repo_root, control_root=control_root)
    if args.json:
        print(json.dumps(removal.as_record(), sort_keys=True))
    if removal.action == "removed":
        if not args.json:
            print(f"removed: {removal.path} ({removal.reason})")
        return EXIT_REMOVED
    if removal.action == "skipped":
        print(f"refused: {removal.path}: {removal.reason}", file=sys.stderr)
        return EXIT_REFUSED
    print(f"error: {removal.path}: {removal.reason}: {removal.error}", file=sys.stderr)
    return EXIT_ERROR


def main(argv: list[str] | None = None) -> int:
    """Run the CLI; see ``--help``."""
    args = _build_parser().parse_args(argv)
    return _cli_remove(args)


if __name__ == "__main__":
    raise SystemExit(main())
