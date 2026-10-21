"""Host-wide test-run slot pool: worker pytest runs and the pre-push gate share the host's CPUs (#10662).

A governed test run takes slots from one pool before it starts its processes and returns them when it ends.
It asks for its xdist worker count (one for a serial run), capped at the pool size so every request can be met,
and waits in a first-come-first-served queue, printing its position, until that many slots are free. Only the
head of the queue takes slots, so a large request is never starved by smaller ones behind it.

``flock`` is the only liveness proof. Each slot is a lock file, and each waiting or holding run keeps its ticket
locked. The kernel drops a lock when its process exits, including on SIGKILL, so a crashed run frees its slots
at once. Files a dead process leaves behind are inert and the next waiter reaps them. Lock files are permanent:
deleting one while a holder keeps it open would let a second holder lock a fresh inode.

The pool is ``<fleet scratch root>/test-slots-<uid>``, beside the pre-push gate's ``pre-push-gate-<uid>``.
``LU_SCRATCH_ROOT`` overrides the default root (``DEFAULT_SCRATCH_ROOT``), as in ``scratch.py``. The whole path is
verified from ``/`` as the gate verifies its own (#10654): no directory or link on it may let another user redirect
it, and missing components are created mode 0700 whatever the umask. The pool is owned by this user and mode 0700.
It never falls back to a per-process temp directory, which would split the pool, and it never lies inside a Git
checkout or Git directory.

A holder's descendants run inside its slots through :data:`HOLDER_ENV`. The marker is checked, not trusted: it
counts only while it names a ticket in this pool's ``holders`` directory that this user owns and a live process
locks, whose record carries the marker's count for the same dispatch task, and while every slot that record
claims is locked and its slot file names that ticket and the marker's nonce, minted when the slots were issued.
A sandbox that shows the pool's root-owned ancestors under an unmapped owner and mounts it read-only cannot prepare
the pool, so a Codex read-only review takes ``review`` slots in its trusted dispatch worker before the sandbox
starts (#11230, #10744). There, a process in a user namespace that maps only part of the id range, as a sandbox
does, may not choose the pool (:data:`DIR_ENV`, :data:`SCRATCH_ROOT_ENV`) and may join only a ``review`` hold.

A review's governed test runs take turns: one run holds the hold's session lock, and only that run's own
descendants join its turn. They prove it through :data:`SESSION_ENV`, which names the turn's process, its start
time and the descriptor that holds the session lock; the kernel's ancestry and lock tables decide, so a sibling
that copies or guesses the value is refused (``session_unverified``). Every run of a turn also holds the hold's
slot files and its turn file shared, so slots stay taken, and no next turn starts, until the last of those runs
ends, even when the worker that issued the hold ends or is killed first.

Environment:
  LU_TEST_SLOTS         on or off. Default on, except where ``CI`` is true, so CI runs are unchanged.
  LU_TEST_SLOTS_COUNT   pool size. Default: half the CPU count, rounded down, and at least 2.
  LU_TEST_SLOTS_WAIT_S  longest wait for slots in seconds (default 3600), then a typed refusal.
  LU_TEST_SLOTS_DIR     absolute pool directory, for tests and experiments.
  LU_TEST_SLOTS_HOLDER  set by a holder for its descendants, which then run inside its slots.
  LU_TEST_SLOTS_SESSION set by the test run that holds a review hold's turn, for its own descendants to prove it.
  LU_TEST_THREAD_CAP    off preserves native thread settings; otherwise governed runs apply native thread caps.

Users: the dispatch pytest plugin (``scripts/ci/pytest_dispatch_cap.py``), the pre-push gate's pytest stage,
dispatch admission's queue-depth check, ``GET /api/ops/v1/test-slots`` and the CLI below.

Stdlib only and self-contained: the pre-push gate loads this one file by path before any project import is
trustworthy, so it imports no project module, not even ``scratch.py``. It follows that module's scratch-root
convention through the two constants below, which a test keeps equal to ``scratch.py``.
"""

from __future__ import annotations

import argparse
import contextlib
import errno
import fcntl
import hmac
import json
import math
import os
import re
import secrets
import stat
import sys
import time
import uuid
from collections.abc import Callable, Iterator, Mapping
from pathlib import Path
from typing import NamedTuple

# The fleet scratch-root convention of scripts/common/scratch.py, minus its per-process temp fallback.
SCRATCH_ROOT_ENV = "LU_SCRATCH_ROOT"
DEFAULT_SCRATCH_ROOT = Path("/var/tmp/lu")

ENABLE_ENV = "LU_TEST_SLOTS"
COUNT_ENV = "LU_TEST_SLOTS_COUNT"
WAIT_ENV = "LU_TEST_SLOTS_WAIT_S"
DIR_ENV = "LU_TEST_SLOTS_DIR"
HOLDER_ENV = "LU_TEST_SLOTS_HOLDER"
SESSION_ENV = "LU_TEST_SLOTS_SESSION"
TASK_ENV = "LEARN_UKRAINIAN_DISPATCH_TASK_ID"
XDIST_AUTO_ENV = "PYTEST_XDIST_AUTO_NUM_WORKERS"
MIN_DEFAULT_SLOTS = 2
DEFAULT_WAIT_S = 3600.0
POLL_S = 0.1
REPORT_EVERY_S = 30.0
MAX_TICKETS = 1024
MAX_RECORD_BYTES = 4096
PENDING_GRACE_S = 60.0
LINK_LIMIT = 40  # links followed while verifying the pool directory, as Linux's MAXSYMLINKS
STATUS_SCHEMA = "test-slots.status.v1"
EXIT_REFUSED = 75  # EX_TEMPFAIL: the command did not run; retry once slots free up
KINDS = frozenset({"gate", "pytest", "launcher", "review"})
SESSION_SUFFIX = ".session"  # a review hold's session lock, beside its holder ticket
TURN_SUFFIX = ".turn"  # every run of a review hold's current turn holds it shared
NONCE_BYTES = 16  # the nonce minted for each hold, recorded in its ticket and its slot files
ANCESTRY_LIMIT = 64  # parents followed when a run proves it descends from the turn
_WHOLE_ID_MAP = ["0", "0", "4294967295"]  # /proc/self/uid_map outside any user namespace
_TRUE = frozenset({"on", "1", "true", "yes"})
_FALSE = frozenset({"off", "0", "false", "no"})
_TASK_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}")
_COUNT_RE = re.compile(r"[0-9]{1,6}")
_NONCE_RE = re.compile(rf"[0-9a-f]{{{2 * NONCE_BYTES}}}")
_TOKEN_RE = re.compile(r"([0-9]{1,10}):([0-9]{1,20}):([0-9]{1,6})")
_PROCESS_FLAGS = ("-n", "--numprocesses")
_AUTO_VALUES = frozenset({"auto", "logical"})


class SlotError(Exception):
    """A typed refusal. ``reason`` is ``invalid_configuration``, ``pool_unavailable``, ``wait_timeout``,
    ``pool_override_refused`` (a sandboxed run chose the pool) or ``session_unverified`` (a review turn's
    session value that does not prove this run descends from the run holding the turn).

    ``detail`` never names a path, so it is safe in API responses and public logs.
    """

    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(f"test_slots_{reason}: {detail}")
        self.reason = reason
        self.detail = detail


# ---- configuration --------------------------------------------------------------------------------------------


def enabled(environ: Mapping[str, str] | None = None) -> bool:
    """Whether governed runs use the pool. Unset means on, except under a true ``CI`` variable."""
    env = os.environ if environ is None else environ
    value = env.get(ENABLE_ENV, "").strip().lower()
    if value in _TRUE:
        return True
    if value in _FALSE:
        return False
    if value:
        raise SlotError("invalid_configuration", f"{ENABLE_ENV} must be on or off")
    return env.get("CI", "").strip().lower() not in _TRUE


def pool_size(environ: Mapping[str, str] | None = None) -> int:
    env = os.environ if environ is None else environ
    value = env.get(COUNT_ENV, "").strip()
    if value:
        if _COUNT_RE.fullmatch(value) is None or int(value) < 1:
            raise SlotError("invalid_configuration", f"{COUNT_ENV} must be a positive whole number")
        return int(value)
    return max(MIN_DEFAULT_SLOTS, (os.cpu_count() or 0) // 2)


def wait_timeout(environ: Mapping[str, str] | None = None) -> float:
    env = os.environ if environ is None else environ
    value = env.get(WAIT_ENV, "").strip()
    if not value:
        return DEFAULT_WAIT_S
    try:
        seconds = float(value)
    except ValueError:
        seconds = math.nan
    if not math.isfinite(seconds) or seconds < 0:
        raise SlotError("invalid_configuration", f"{WAIT_ENV} must be a non-negative number of seconds")
    return seconds


def auto_worker_cap(environ: Mapping[str, str] | None = None) -> int | None:
    """Workers ``-n auto`` starts under an existing :data:`XDIST_AUTO_ENV`, read as xdist reads it, else ``None``.

    A driver scope sets it as a memory cap (#9624); a governed run may lower it but never raise it. A negative
    value starts no worker, like ``0``.
    """
    env = os.environ if environ is None else environ
    try:
        return max(0, int(env.get(XDIST_AUTO_ENV, "")))
    except ValueError:  # unset or not a number: xdist ignores it and counts CPUs
        return None


def user_namespaced() -> bool:
    """Whether this process runs in a user namespace that maps only part of the id range, as a sandbox does.

    The kernel writes the map, so a process cannot hide it. An unreadable map counts as namespaced: the caller then
    refuses what a sandbox may not do, which is the safe side.
    """
    try:
        with open("/proc/self/uid_map", encoding="ascii") as handle:
            return handle.read().split() != _WHOLE_ID_MAP
    except OSError:
        return True


def pool_dir(environ: Mapping[str, str] | None = None) -> Path:
    """The pool directory this environment selects; nothing is created.

    A sandboxed process (:func:`user_namespaced`) gets only the default location: a pool it could point at, such as
    one it built in a writable directory, would let it count slots no launcher issued (#11230).
    """
    env = os.environ if environ is None else environ
    override = env.get(DIR_ENV, "").strip()
    root = env.get(SCRATCH_ROOT_ENV, "").strip()
    if (override or root) and user_namespaced():
        raise SlotError(
            "pool_override_refused",
            f"a sandboxed run cannot choose the pool; unset {DIR_ENV} and {SCRATCH_ROOT_ENV} so it uses the "
            "launcher's pool at its default location",
        )
    if override:
        if not os.path.isabs(override):
            raise SlotError("invalid_configuration", f"{DIR_ENV} must be an absolute path")
        return Path(override)
    base = Path(root) if root else DEFAULT_SCRATCH_ROOT
    if not base.is_absolute():
        raise SlotError("invalid_configuration", f"{SCRATCH_ROOT_ENV} must be an absolute path")
    return base / f"test-slots-{os.geteuid()}"


# ---- the pool directory ---------------------------------------------------------------------------------------


def _inside_git(path: Path) -> bool:
    """Whether ``path`` or an ancestor is a Git checkout, a linked worktree or a Git directory."""
    for candidate in (path, *path.parents):
        if candidate.name == ".git" or os.path.lexists(candidate / ".git"):
            return True
        if (candidate / "HEAD").is_file() and (candidate / "objects").is_dir() and (candidate / "refs").is_dir():
            return True
    return False


def _unsafe_component(info: os.stat_result) -> str | None:
    """Name the class of a directory or link another user could replace or redirect, or ``None`` if safe.

    Only this user and root are trusted. A directory writable by group or others is safe only when it is
    sticky, as the system temp directories are: there only an entry's owner can rename or replace it.
    """
    kind = "link" if stat.S_ISLNK(info.st_mode) else "directory"
    if info.st_uid not in (0, os.geteuid()):
        return f"a {kind} owned by another user"
    if kind == "directory" and info.st_mode & (stat.S_IWGRP | stat.S_IWOTH) and not info.st_mode & stat.S_ISVTX:
        return "a directory writable by group or others without the sticky bit"
    return None


def _verified_directory(path: Path, *, create: bool) -> Path | None:
    """Resolve absolute ``path`` from ``/`` one component at a time, so no other user can redirect it.

    The pre-push gate verifies its pytest base temp root the same way (#10654), and both live under one
    scratch root. Every directory passed must be safe (``_unsafe_component``), and a link must be owned by
    this user or root and is followed only into a target that passes the same checks; the pool directory
    itself must not be a link. Missing components are created mode 0700, whatever the umask, after the Git
    check, and verified again: a umask-derived group-writable root would make the gate refuse its own base
    temp. Without ``create`` a missing component returns ``None`` and nothing is written. Raises
    ``SlotError`` for an unsafe, linked or in-Git path, else ``OSError`` when it cannot be inspected or created.
    """

    def verify(info: os.stat_result) -> None:
        if not (stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode)):
            raise NotADirectoryError(errno.ENOTDIR, "a pool directory component is not a directory")
        problem = _unsafe_component(info)
        if problem is not None:
            raise SlotError(
                "pool_unavailable",
                f"the pool directory or one of its ancestors is {problem}, so another user could redirect it; "
                f"point {SCRATCH_ROOT_ENV} or {DIR_ENV} at a private directory",
            )

    current = Path("/")
    verify(os.lstat(current))
    pending, missing, links = list(reversed(path.parts[1:])), [], 0
    while pending:
        part = pending.pop()
        if part == "..":
            if missing:
                missing.pop()
            else:
                current = current.parent  # an ancestor of a verified directory, so verified itself
            continue
        if missing:
            missing.append(part)
            continue
        try:
            info = os.lstat(current / part)
        except FileNotFoundError:
            missing.append(part)
            continue
        verify(info)
        if not stat.S_ISLNK(info.st_mode):
            current = current / part
            continue
        if not pending:  # link targets stack above the requested path, so this is its last component
            raise SlotError("pool_unavailable", "the pool directory is a symbolic link")
        links += 1
        if links > LINK_LIMIT:
            raise SlotError("pool_unavailable", "the pool directory passes through a link loop")
        target = Path(os.readlink(current / part))
        if target.is_absolute():
            current = Path("/")
        pending.extend(reversed(target.parts[1:] if target.is_absolute() else target.parts))
    if missing and not create:
        return None
    if _inside_git(current.joinpath(*missing)):
        raise SlotError(
            "pool_unavailable",
            f"the pool directory lies inside a Git checkout or Git directory; point {DIR_ENV} or "
            f"{SCRATCH_ROOT_ENV} outside every checkout",
        )
    for part in missing:
        current = current / part
        with contextlib.suppress(FileExistsError):  # a concurrent run created it; verify it like any other
            os.mkdir(current, 0o700)
        info = os.lstat(current)
        verify(info)
        if stat.S_ISLNK(info.st_mode):
            raise NotADirectoryError(errno.ENOTDIR, "a created pool directory component is not a directory")
    return current


def _private_directory(path: Path) -> None:
    """Create ``path`` mode 0700, or accept it only as a real directory this user owns, made private."""
    with contextlib.suppress(FileExistsError):
        os.mkdir(path, 0o700)
    try:
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError as error:
        if error.errno in (errno.ELOOP, errno.ENOTDIR):
            raise SlotError("pool_unavailable", "a pool directory is a symbolic link or not a directory") from None
        raise
    try:
        info = os.fstat(fd)
        if info.st_uid != os.geteuid():
            raise SlotError("pool_unavailable", "a pool directory belongs to another user")
        if stat.S_IMODE(info.st_mode) != 0o700:
            os.fchmod(fd, 0o700)
    finally:
        os.close(fd)


def _open_pool(env: Mapping[str, str]) -> Path:
    """Return the verified, link-free pool directory with its queue and holder directories, creating them."""
    try:
        path = _verified_directory(pool_dir(env), create=True)
        assert path is not None  # creating never reports a missing component
        _private_directory(path)
        for name in ("queue", "holders"):
            _private_directory(path / name)
    except OSError as error:
        raise SlotError("pool_unavailable", f"the pool directory cannot be prepared ({type(error).__name__})") from None
    return path


@contextlib.contextmanager
def _pool_mutex(pool: Path) -> Iterator[bool]:
    """Serialize queue decisions for a moment; ``False`` when another process is deciding now."""
    fd = os.open(pool / "pool.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            yield False
        else:
            yield True
    finally:
        os.close(fd)  # closing the descriptor releases the lock


def _publish(directory: Path, record: dict[str, object]) -> tuple[Path, int]:
    """Lock a complete record, then rename it into place: no observer can mistake it for a dead one."""
    pending = directory / f".{uuid.uuid4().hex}.pending"
    fd = os.open(pending, os.O_CREAT | os.O_EXCL | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        os.write(fd, json.dumps(record, sort_keys=True).encode("utf-8"))
        ticket = directory / f"{time.monotonic_ns():020d}-{uuid.uuid4().hex}.ticket"
        os.rename(pending, ticket)
    except BaseException:
        with contextlib.suppress(OSError):
            pending.unlink()
        os.close(fd)
        raise
    return ticket, fd


def _discard(path: Path, fd: int) -> None:
    with contextlib.suppress(FileNotFoundError):
        path.unlink()
    os.close(fd)


def _read_record(fd: int) -> dict[str, object]:
    try:
        data = os.pread(fd, MAX_RECORD_BYTES + 1, 0)
        record = json.loads(data) if len(data) <= MAX_RECORD_BYTES else None
    except (OSError, ValueError):
        return {}
    return record if isinstance(record, dict) else {}


def _scan(directory: Path, *, reap: bool, own: Path | None = None) -> list[tuple[Path, dict[str, object]]]:
    """Live tickets in queue order with their records; ``reap`` unlinks the ones no process holds.

    At most :data:`MAX_TICKETS` may be live. A reaping scan unlinks dead tickets before it counts, so tickets
    left by killed runs or a reboot never refuse the pool for good; the read-only scan stays bounded instead.
    """
    try:
        names = sorted(name for name in os.listdir(directory) if name.endswith(".ticket") and not name.startswith("."))
    except FileNotFoundError:
        return []
    if len(names) > MAX_TICKETS and not reap:
        raise SlotError("pool_unavailable", f"more than {MAX_TICKETS} tickets; the queue scan stopped")
    live = []
    for name in names:
        path = directory / name
        if path == own:
            live.append((path, {}))
            continue
        try:
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        except FileNotFoundError:  # its holder finished between listing and opening
            continue
        except OSError:  # a symlink or another unsafe entry is never a live ticket
            if reap:
                with contextlib.suppress(OSError):
                    path.unlink()
            continue
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                continue
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                live.append((path, _read_record(fd)))
                continue
            if reap:  # names are never reused, so this name still denotes the dead inode
                with contextlib.suppress(FileNotFoundError):
                    path.unlink()
        finally:
            os.close(fd)
    if len(live) > MAX_TICKETS:
        raise SlotError("pool_unavailable", f"more than {MAX_TICKETS} live tickets; no further run may queue")
    return live


def _reap_pending(directory: Path) -> None:
    """Remove registrations a process abandoned between creating and publishing them."""
    cutoff = time.time() - PENDING_GRACE_S
    for path in directory.glob(".*.pending"):
        try:
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        except OSError:
            continue
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_mtime > cutoff:
                continue
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                continue
            with contextlib.suppress(FileNotFoundError):
                path.unlink()
        finally:
            os.close(fd)


def _reap_sessions(directory: Path) -> None:
    """Remove review session and turn files whose holder ticket is gone: no live marker can name them any more.

    A run still inside a turn keeps its descriptors, and with them its locks on the slot files, which is what keeps
    those slots taken; the names are only how new runs find a live hold.
    """
    for suffix in (SESSION_SUFFIX, TURN_SUFFIX):
        for path in directory.glob(f"*{suffix}"):
            if not os.path.lexists(path.with_suffix(".ticket")):
                with contextlib.suppress(OSError):
                    path.unlink()


def _slot_path(pool: Path, index: int) -> Path:
    return pool / f"slot-{index:03d}.lock"


def _take_slots(pool: Path, count: int, size: int) -> list[tuple[int, int]] | None:
    """Lock ``count`` free slot files, or none at all.

    A slot is free only when no process holds its file in any mode: the runs of a review turn hold it shared.
    """
    taken: list[tuple[int, int]] = []
    try:
        for index in range(size):
            fd = os.open(_slot_path(pool, index), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                os.close(fd)
                continue
            taken.append((index, fd))
            if len(taken) == count:
                return taken
    except BaseException:
        for _, fd in taken:
            os.close(fd)
        raise
    for _, fd in taken:
        os.close(fd)
    return None


# ---- holding slots --------------------------------------------------------------------------------------------


class Hold:
    """Slots held for one run. ``release()``, or the end of the holding process, returns them."""

    def __init__(
        self,
        *,
        count: int,
        requested: int,
        pool_size: int,
        waited: float,
        queue_position: int,
        record: Path | None = None,
        nonce: str = "",
        descriptors: tuple[int, ...] = (),
        companions: tuple[Path, ...] = (),
        session_environment: Mapping[str, str] | None = None,
    ) -> None:
        self.count = count
        self.requested = requested
        self.pool_size = pool_size
        self.waited = waited
        self.queue_position = queue_position
        self._record = record
        self._nonce = nonce
        self._descriptors = descriptors
        self._companions = companions  # a review hold's session and turn files, removed with its record
        self._session_environment = dict(session_environment or {})
        self._released = False

    @classmethod
    def inherited(cls, count: int) -> Hold:
        """The slots of a live ancestor holder: nothing to release, and children inherit its marker."""
        return cls(count=count, requested=count, pool_size=count, waited=0.0, queue_position=0)

    def marker(self) -> str:
        """``<count>:<nonce>:<holder record>`` for :data:`HOLDER_ENV`; empty for an inherited hold."""
        return f"{self.count}:{self._nonce}:{self._record}" if self._record is not None else ""

    def environment(self) -> dict[str, str]:
        """Variables a child needs to run inside these slots rather than queue for its own."""
        marker = {HOLDER_ENV: self.marker()} if self._record is not None else {}
        return {**marker, **self._session_environment}

    def inheritable(self) -> None:
        """Keep the locks across ``exec``, so the command itself holds the slots until it exits."""
        for fd in self._descriptors:
            os.set_inheritable(fd, True)

    def release(self) -> None:
        if self._released:
            return
        self._released = True
        for path in (self._record, *self._companions):
            if path is not None:
                with contextlib.suppress(OSError):
                    path.unlink()
        for fd in self._descriptors:
            with contextlib.suppress(OSError):
                os.close(fd)

    def __enter__(self) -> Hold:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.release()


def _task_label(value: object) -> str:
    return value if isinstance(value, str) and _TASK_RE.fullmatch(value) else "unknown"


def _print_progress(line: str) -> None:
    print(line, file=sys.stderr, flush=True)


def acquire(
    requested: int,
    *,
    kind: str,
    task_id: str | None = None,
    wait_s: float | None = None,
    progress: Callable[[str], None] | None = None,
    environ: Mapping[str, str] | None = None,
) -> Hold:
    """Wait in FIFO order for ``min(requested, pool size)`` slots and hold them.

    Raises :class:`SlotError` on invalid configuration, an unusable pool directory, or a wait longer than
    ``wait_s`` (default :data:`WAIT_ENV`). The caller decides whether the pool is :func:`enabled`.
    """
    if kind not in KINDS:
        raise ValueError(f"unknown slot holder kind: {kind!r}")
    env = os.environ if environ is None else environ
    enabled(env)  # invalid settings refuse even an explicit request
    size = pool_size(env)
    configured_wait = wait_timeout(env)
    limit = configured_wait if wait_s is None else wait_s
    count = min(max(1, int(requested)), size)
    report = progress or _print_progress
    pool = _open_pool(env)
    identity = {
        "kind": kind,
        "task_id": _task_label(task_id if task_id is not None else env.get(TASK_ENV)),
        "pid": os.getpid(),
        "requested": int(requested),
        "queued_at": time.time(),
    }
    started = time.monotonic()
    try:
        ticket, ticket_fd = _publish(pool / "queue", identity)
    except OSError as error:
        raise SlotError("pool_unavailable", f"cannot join the queue ({type(error).__name__})") from None
    last_report: tuple[int, int] | None = None
    reported_at = started
    first_position = 0
    try:
        while True:
            with _pool_mutex(pool) as deciding:
                if deciding:
                    live = [path for path, _ in _scan(pool / "queue", reap=True, own=ticket)]
                    if ticket not in live:
                        raise SlotError("pool_unavailable", "this run's queue ticket disappeared")
                    position, depth = live.index(ticket) + 1, len(live)
                    first_position = first_position or position
                    if position == 1:
                        _scan(pool / "holders", reap=True)
                        _reap_sessions(pool / "holders")
                        _reap_pending(pool / "queue")
                        _reap_pending(pool / "holders")
                        slots = _take_slots(pool, count, size)
                        if slots is not None:
                            return _hold(pool, identity, slots, count, size, started, first_position, ticket, ticket_fd)
            waited = time.monotonic() - started
            if deciding and ((position, depth) != last_report or time.monotonic() - reported_at >= REPORT_EVERY_S):
                report(
                    f"TEST SLOTS: waiting for {count} of {size} slot(s); queue position {position}/{depth}; "
                    f"waited {waited:.1f}s (limit {limit:g}s)"
                )
                last_report, reported_at = (position, depth), time.monotonic()
            if waited >= limit:
                where = f"at queue position {position}/{depth}" if last_report else "before reaching the queue"
                raise SlotError(
                    "wait_timeout",
                    f"waited {waited:.1f}s for {count} of {size} slot(s) {where} (limit {limit:g}s, {WAIT_ENV})",
                )
            time.sleep(min(POLL_S, max(0.0, limit - waited)))
    except OSError as error:
        _discard(ticket, ticket_fd)
        raise SlotError("pool_unavailable", f"the pool could not be read ({type(error).__name__})") from None
    except BaseException:
        _discard(ticket, ticket_fd)
        raise


def _hold(
    pool: Path,
    identity: dict[str, object],
    slots: list[tuple[int, int]],
    count: int,
    size: int,
    started: float,
    position: int,
    ticket: Path,
    ticket_fd: int,
) -> Hold:
    """Publish the holder record and leave the queue while the queue decision is still serialized.

    The record carries a nonce minted here, never an inherited value, and each slot file names the ticket and that
    nonce: the pool's own record of who holds the slot, which a marker must match. A ``review`` hold also gets its
    session and turn files (created exclusive, mode 0600) and holds its slots shared, so the runs of its turns can
    hold them too and keep them taken after this process ends.
    """
    waited = time.monotonic() - started
    nonce = secrets.token_hex(NONCE_BYTES)
    record = {
        **identity,
        "held": count,
        "slots": [index for index, _ in slots],
        "nonce": nonce,
        "acquired_at": time.time(),
        "waited_s": round(waited, 3),
    }
    descriptors = tuple(fd for _, fd in slots)
    try:
        holder, holder_fd = _publish(pool / "holders", record)
    except BaseException:
        for fd in descriptors:
            os.close(fd)
        raise
    review = identity["kind"] == "review"
    companions = (holder.with_suffix(SESSION_SUFFIX), holder.with_suffix(TURN_SUFFIX)) if review else ()
    created: list[Path] = []
    try:
        claim = json.dumps({"ticket": holder.name, "nonce": nonce}, sort_keys=True).encode("utf-8")
        for fd in descriptors:
            os.ftruncate(fd, 0)
            os.pwrite(fd, claim, 0)
        for path in companions:  # created before any marker names the hold, so every run joining it finds them
            os.close(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600))
            created.append(path)
        if review:  # still inside the pool mutex: no other run takes a slot between the two modes
            for fd in descriptors:
                fcntl.flock(fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
    except BaseException:
        for path in created:
            with contextlib.suppress(OSError):
                path.unlink()
        _discard(holder, holder_fd)
        for fd in descriptors:
            os.close(fd)
        raise
    _discard(ticket, ticket_fd)
    return Hold(
        count=count,
        requested=int(identity["requested"]),  # type: ignore[call-overload]
        pool_size=size,
        waited=waited,
        queue_position=position,
        record=holder,
        nonce=nonce,
        descriptors=(*descriptors, holder_fd),
        companions=companions,
    )


class _Marked(NamedTuple):
    """A verified marker: the hold's slot count, kind, ticket, claimed slots and issued nonce."""

    count: int
    kind: str
    record: Path
    slots: tuple[int, ...]
    nonce: str


def _parse_marker(value: str) -> tuple[int, str, Path] | None:
    """``(count, nonce, ticket)`` from ``<count>:<nonce>:<ticket>``, else ``None``."""
    count, _, rest = value.partition(":")
    nonce, _, record = rest.partition(":")
    path = Path(record)
    if _COUNT_RE.fullmatch(count) is None or int(count) < 1 or _NONCE_RE.fullmatch(nonce) is None:
        return None
    if not path.is_absolute() or path.parent.name != "holders" or path.suffix != ".ticket":
        return None
    return int(count), nonce, path


def _slot_claimed_by(pool: Path, index: int, ticket: str, nonce: str) -> bool:
    """Whether slot ``index`` is locked and its slot file names ``ticket`` and ``nonce``.

    Only reads, so a sandbox that mounts the pool read-only can check it. Probing a free slot locks it for a moment,
    as the queue's own liveness scans do; closing the descriptor drops that lock.
    """
    try:
        fd = os.open(_slot_path(pool, index), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError:
        return False
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid():
            return False
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            pass
        else:
            return False  # nobody holds it, so no hold owns it
        claim = _read_record(fd)
    finally:
        os.close(fd)
    return claim.get("ticket") == ticket and hmac.compare_digest(str(claim.get("nonce", "")), nonce)


def _live_holder(env: Mapping[str, str]) -> _Marked | None:
    """The live hold :data:`HOLDER_ENV` names, else ``None``.

    The marker is checked, not trusted. It counts only when it names a ticket in the ``holders`` directory of the
    pool this environment selects, the ticket is a regular file this user owns, a live process holds its lock (a
    dead holder's record is unlocked, so a stale variable is ignored), its record holds exactly the marked count,
    and the run names no dispatch task other than the hold's. (A run that names none, such as a test the suite runs
    without the agent's identity, stays inside its ancestor's slots, as before.) Then the pool itself must agree:
    every slot the record claims is locked, and its slot file names this ticket and the marker's nonce, the one
    minted when the slots were issued. A hand-written ticket, a copy claiming another run's slots or free ones, or a ticket in a pool the
    caller made without holding its slots therefore runs nothing. A sandboxed process (:func:`user_namespaced`)
    cannot choose the pool (:func:`pool_dir` refuses, typed) and may join only a ``review`` hold. Only reads, so a
    sandbox that mounts the pool read-only can check a marker its trusted launcher issued.
    """
    parsed = _parse_marker(env.get(HOLDER_ENV, ""))
    if parsed is None:
        return None
    count, nonce, path = parsed
    pool = pool_dir(env)  # a sandbox's pool override refuses here, typed, rather than counting as no marker
    try:
        if os.path.realpath(path.parent.parent) != os.path.realpath(pool):
            return None
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError:
        return None
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid():
            return None
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            held = _read_record(fd)
        else:
            return None
    finally:
        os.close(fd)
    kind = held.get("kind")
    if _whole(held.get("held")) != count or not isinstance(kind, str) or kind not in KINDS:
        return None
    claimed = held.get("slots")
    if not isinstance(claimed, list) or len(claimed) != count or any(_whole(index) is None for index in claimed):
        return None
    slots = tuple(claimed)
    if len(set(slots)) != count:
        return None
    tasks = {_task_label(held.get("task_id")), _task_label(env.get(TASK_ENV))} - {"unknown"}
    if len(tasks) > 1:
        return None
    if kind != "review" and user_namespaced():
        return None
    root = path.parent.parent
    if not all(_slot_claimed_by(root, index, path.name, nonce) for index in slots):
        return None
    return _Marked(count, kind, path, slots, nonce)


def inherited_hold(environ: Mapping[str, str] | None = None) -> int | None:
    """Slots of the live ancestor holder :data:`HOLDER_ENV` names (checked as :func:`_live_holder`), else ``None``."""
    found = _live_holder(os.environ if environ is None else environ)
    return found.count if found is not None else None


def join_inherited(
    environ: Mapping[str, str] | None = None,
    *,
    wait_s: float | None = None,
    progress: Callable[[str], None] | None = None,
) -> Hold | None:
    """Run inside a live ancestor's slots, or ``None`` when no valid marker names one.

    A ``review`` hold serves every test run of one sandboxed review, so its runs take turns. A run without
    :data:`SESSION_ENV` waits, up to ``wait_s`` (default :data:`WAIT_ENV`), for the hold's session lock and then
    for every run of the previous turn to end, and holds the turn until it ends. Its descendants (xdist workers
    aside, which take no slots; a pytest a test starts; a run the launcher execs) receive :data:`SESSION_ENV`, a
    token naming the turn's process, its start time and the descriptor holding the session lock, and join that turn
    without waiting once the kernel confirms the named process is this run or one of its ancestors and holds the
    lock through that descriptor. Every run of a turn holds the hold's slot files and its turn file shared until it
    ends, so the slots stay taken while any of them runs, whatever happens to the issuing worker.

    Raises :class:`SlotError`: ``session_unverified`` for a session value that proves nothing (a path, a copied
    token, a turn that ended), ``wait_timeout``, ``pool_override_refused`` (see :func:`pool_dir`), or
    ``pool_unavailable`` when the hold's files are unusable. Other holds keep the per-run inheritance of
    :func:`inherited_hold`.
    """
    env = os.environ if environ is None else environ
    found = _live_holder(env)
    if found is None:
        return None
    if found.kind != "review":
        return Hold.inherited(found.count)
    session = found.record.with_suffix(SESSION_SUFFIX)
    turn = found.record.with_suffix(TURN_SUFFIX)
    token = env.get(SESSION_ENV, "")
    limit = wait_timeout(env) if wait_s is None else wait_s
    report = progress or _print_progress
    started = time.monotonic()
    descriptors: list[int] = []
    try:
        if token:
            _verify_turn_token(token, session)
            turn_fd = _share(turn)
            if turn_fd is None:  # only the next turn's run holds it alone, so this run's turn has ended
                raise SlotError("session_unverified", f"the review's turn that {SESSION_ENV} names has ended")
            descriptors.append(turn_fd)
        else:
            session_fd, _ = _join_session(session, limit, report)
            descriptors.append(session_fd)
            descriptors.append(_wait_for_turn(turn, started + limit, limit, report))
            token = f"{os.getpid()}:{_start_ticks(os.getpid())}:{session_fd}"
        slot_fds = [_share(_slot_path(found.record.parent.parent, index)) for index in found.slots]
        descriptors.extend(fd for fd in slot_fds if fd is not None)
        if env.get(SESSION_ENV):  # the turn this run proved is still the one whose files it now holds
            _verify_turn_token(token, session)
        # A slot another run holds alone has changed hands, so the holder ended while this run waited or joined.
        if None in slot_fds or _live_holder(env) is None:
            for fd in descriptors:
                os.close(fd)
            return None
    except BaseException:
        for fd in descriptors:
            os.close(fd)
        raise
    return Hold(
        count=found.count,
        requested=found.count,
        pool_size=found.count,
        waited=time.monotonic() - started,
        queue_position=0,
        descriptors=tuple(descriptors),
        session_environment={SESSION_ENV: token},
    )


def _share(path: Path) -> int | None:
    """Hold ``path``, a regular file of this user, shared; the descriptor, or ``None`` while a run holds it alone."""
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError as error:
        raise SlotError("pool_unavailable", f"a file of the hold cannot be opened ({type(error).__name__})") from None
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid():
            raise SlotError("pool_unavailable", "a file of the hold is not a regular file of this user")
        try:
            fcntl.flock(fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
        except BlockingIOError:
            os.close(fd)
            return None
    except BaseException:
        os.close(fd)
        raise
    return fd


def _wait_for_turn(turn: Path, deadline: float, limit: float, report: Callable[[str], None]) -> int:
    """Wait until no run of the previous turn holds ``turn``, then hold it shared for this turn; the descriptor."""
    try:
        fd = os.open(turn, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError as error:
        raise SlotError("pool_unavailable", f"the hold's turn file cannot be opened ({type(error).__name__})") from None
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid():
            raise SlotError("pool_unavailable", "the hold's turn file is not a regular file of this user")
        reported_at: float | None = None
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                pass
            else:
                # Only the session holder takes it alone, and this run holds the session, so nothing joins in between.
                fcntl.flock(fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
                return fd
            now = time.monotonic()
            if reported_at is None or now - reported_at >= REPORT_EVERY_S:
                report("TEST SLOTS: waiting for the previous test run of this review to end")
                reported_at = now
            if now >= deadline:
                raise SlotError(
                    "wait_timeout",
                    f"waited for the previous test run of this review to end (limit {limit:g}s, {WAIT_ENV})",
                )
            time.sleep(min(POLL_S, max(0.0, deadline - now)))
    except BaseException:
        os.close(fd)
        raise


def _proc_stat(pid: int) -> tuple[int, int] | None:
    """``(parent pid, start time in clock ticks)`` of ``pid``, or ``None`` when it is gone or unreadable."""
    try:
        with open(f"/proc/{pid}/stat", "rb") as handle:
            text = handle.read().decode("ascii", "replace")
        fields = text[text.rindex(")") + 2 :].split()
        return int(fields[1]), int(fields[19])
    except (OSError, ValueError, IndexError):
        return None


def _start_ticks(pid: int) -> int:
    found = _proc_stat(pid)
    if found is None:
        raise SlotError("pool_unavailable", "this run's own start time cannot be read from /proc")
    return found[1]


def _is_self_or_ancestor(pid: int, start: int) -> bool:
    """Whether ``pid``, started at ``start``, is this process or one of its ancestors in this pid namespace."""
    current = os.getpid()
    for _ in range(ANCESTRY_LIMIT):
        if current <= 0:
            return False
        found = _proc_stat(current)
        if found is None:
            return False
        if current == pid:
            return found[1] == start
        current = found[0]
    return False


def _holds_lock_alone(pid: int, fd: int, path: Path) -> bool:
    """Whether descriptor ``fd`` of ``pid`` holds the exclusive ``flock`` on ``path``.

    ``/proc/<pid>/fdinfo/<fd>`` lists only the locks of that open file, so another descriptor of the same file,
    even in the same process, never passes.
    """
    try:
        info = os.lstat(path)
        with open(f"/proc/{pid}/fdinfo/{fd}", encoding="ascii", errors="replace") as handle:
            lines = handle.read().splitlines()
    except OSError:
        return False
    wanted = (os.major(info.st_dev), os.minor(info.st_dev), info.st_ino)
    for line in lines:
        # lock:  1: FLOCK  ADVISORY  WRITE <pid> <major>:<minor>:<inode> 0 EOF; a waiting request carries "->"
        fields = line.split()
        if fields[:1] != ["lock:"] or "->" in fields or "FLOCK" not in fields or "WRITE" not in fields:
            continue
        try:
            major, minor, inode = fields[fields.index("WRITE") + 2].split(":")
            if (int(major, 16), int(minor, 16), int(inode)) == wanted:
                return True
        except (ValueError, IndexError):
            continue
    return False


def _verify_turn_token(token: str, session: Path) -> None:
    """Refuse, ``session_unverified``, unless ``token`` names this run or an ancestor that holds the turn."""
    match = _TOKEN_RE.fullmatch(token)
    if match is None:
        raise SlotError(
            "session_unverified",
            f"{SESSION_ENV} is not a turn token; a run outside the turn must wait for it, so unset {SESSION_ENV}",
        )
    pid, start, fd = map(int, match.groups())
    if not _is_self_or_ancestor(pid, start):
        raise SlotError("session_unverified", f"{SESSION_ENV} names no test run this run descends from")
    if not _holds_lock_alone(pid, fd, session):
        raise SlotError("session_unverified", f"the test run {SESSION_ENV} names does not hold this review's turn")


def _join_session(session: Path, limit: float, report: Callable[[str], None]) -> tuple[int, float]:
    """Lock a review hold's session file, waiting while another of its runs holds it; ``(descriptor, waited)``."""
    try:
        fd = os.open(session, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError as error:
        raise SlotError(
            "pool_unavailable", f"the hold's session lock cannot be opened ({type(error).__name__})"
        ) from None
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid():
            raise SlotError("pool_unavailable", "the hold's session lock is not a regular file of this user")
        started = time.monotonic()
        reported_at: float | None = None
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return fd, time.monotonic() - started
            except BlockingIOError:
                pass
            waited = time.monotonic() - started
            if reported_at is None or time.monotonic() - reported_at >= REPORT_EVERY_S:
                report(
                    f"TEST SLOTS: waiting for another test run of this review to finish; "
                    f"waited {waited:.1f}s (limit {limit:g}s)"
                )
                reported_at = time.monotonic()
            if waited >= limit:
                raise SlotError(
                    "wait_timeout",
                    f"waited {waited:.1f}s for another test run of this review (limit {limit:g}s, {WAIT_ENV})",
                )
            time.sleep(min(POLL_S, max(0.0, limit - waited)))
    except BaseException:
        os.close(fd)
        raise


# ---- visibility -----------------------------------------------------------------------------------------------


def _whole(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def _number(value: object) -> float | None:
    if isinstance(value, int | float) and not isinstance(value, bool) and math.isfinite(value):
        return float(value)
    return None


def _age(timestamp: object, now: float) -> float:
    """Seconds since a wall-clock timestamp in a record; 0.0 when the record lacks one."""
    value = _number(timestamp)
    return round(max(0.0, now - value), 1) if value is not None else 0.0


def _kind(value: object) -> str:
    return value if isinstance(value, str) and value in KINDS else "unknown"


def _slot_locked(pool: Path, index: int) -> bool:
    """Whether some process holds slot ``index``'s file in any mode; probing a free one locks it for a moment."""
    try:
        fd = os.open(_slot_path(pool, index), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError:
        return False
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            return False
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        return False
    finally:
        os.close(fd)


def status(environ: Mapping[str, str] | None = None) -> dict[str, object]:
    """Read-only pool view: holders by task, the queue in order, and wait times. Never names a path.

    ``slots_draining`` counts slots no live holder claims that are still taken: runs of a review turn keep them
    after the worker that issued the hold has ended, until the last of those runs ends (#11230).
    """
    env = os.environ if environ is None else environ
    report: dict[str, object] = {
        "schema": STATUS_SCHEMA,
        "enabled": None,
        "pool_size": None,
        "wait_timeout_s": None,
        "location": "override" if env.get(DIR_ENV, "").strip() else "default",
        "pool_exists": False,
        "slots_in_use": 0,
        "slots_draining": 0,
        "slots_free": None,
        "queue_depth": 0,
        "longest_wait_s": 0.0,
        "holders": [],
        "queue": [],
        "error": None,
    }
    try:
        report["enabled"] = enabled(env)
        size = pool_size(env)
        report.update(pool_size=size, slots_free=size, wait_timeout_s=wait_timeout(env))
        path = _verified_directory(pool_dir(env), create=False)  # verifies the path, creates nothing
        if path is None:
            return report
        try:
            fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        except FileNotFoundError:
            return report
        try:
            info = os.fstat(fd)
        finally:
            os.close(fd)
        if info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise SlotError("pool_unavailable", "the pool directory is not private to this user")
        report["pool_exists"] = True
        now = time.time()
        records = [record for _, record in _scan(path / "holders", reap=False)]
        claimed = {index for record in records if isinstance(record.get("slots"), list) for index in record["slots"]}
        draining = sum(1 for index in range(size) if index not in claimed and _slot_locked(path, index))
        holders = [
            {
                "task_id": _task_label(record.get("task_id")),
                "kind": _kind(record.get("kind")),
                "pid": _whole(record.get("pid")),
                "requested": _whole(record.get("requested")),
                "slots": _whole(record.get("held")),
                "held_s": _age(record.get("acquired_at"), now),
                "waited_s": round(max(0.0, _number(record.get("waited_s")) or 0.0), 1),
            }
            for record in records
        ]
        queue = [
            {
                "position": position,
                "task_id": _task_label(record.get("task_id")),
                "kind": _kind(record.get("kind")),
                "pid": _whole(record.get("pid")),
                "requested": _whole(record.get("requested")),
                "waiting_s": _age(record.get("queued_at"), now),
            }
            for position, (_, record) in enumerate(_scan(path / "queue", reap=False), start=1)
        ]
        in_use = sum(holder["slots"] or 0 for holder in holders)
        report.update(
            holders=holders,
            queue=queue,
            slots_in_use=in_use,
            slots_draining=draining,
            slots_free=max(0, size - in_use - draining),
            queue_depth=len(queue),
            longest_wait_s=max((entry["waiting_s"] for entry in queue), default=0.0),
        )
    except SlotError as error:
        report["error"] = {"reason": error.reason, "detail": error.detail}
    except OSError as error:
        report["error"] = {
            "reason": "pool_unavailable",
            "detail": f"the pool could not be read ({type(error).__name__})",
        }
    return report


# ---- the launcher ---------------------------------------------------------------------------------------------


def _process_value(command: list[str], index: int) -> tuple[int, int, str] | None:
    """``(token index, value index, value)`` when ``command[index]`` sets the xdist worker count."""
    token = command[index]
    if token in _PROCESS_FLAGS:
        return (index, index + 1, command[index + 1]) if index + 1 < len(command) else None
    if token.startswith("--numprocesses="):
        return index, index, token.partition("=")[2]
    if token.startswith("-n") and not token.startswith("--"):
        value = token[2:]
        if value.isdigit() or value in _AUTO_VALUES:
            return index, index, value
    return None


def requested_processes(command: list[str], size: int, auto_cap: int | None = None) -> int:
    """The worker count a wrapped command asks for: its last ``-n``, otherwise 1.

    ``-n auto`` asks for the pool, or for ``auto_cap`` (:func:`auto_worker_cap`) when that is lower.
    """
    requested = 1
    for index in range(len(command)):
        found = _process_value(command, index)
        if found is None:
            continue
        value = found[2]
        if value in _AUTO_VALUES:
            requested = size if auto_cap is None else max(1, min(size, auto_cap))
        elif value.isdigit():
            requested = max(1, int(value))
    return requested


def limit_processes(command: list[str], count: int, auto_cap: int | None = None) -> list[str]:
    """Rewrite every visible ``-n`` above ``count`` to ``count``, and ``-n auto`` to ``count`` or a lower ``auto_cap``."""
    auto = count if auto_cap is None else min(count, auto_cap)
    limited = list(command)
    for index in range(len(command)):
        found = _process_value(command, index)
        if found is None:
            continue
        token_index, value_index, value = found
        if value in _AUTO_VALUES:
            limit = auto
        elif value.isdigit() and int(value) > count:
            limit = count
        else:
            continue
        if value_index == token_index:
            prefix = limited[token_index][: len(limited[token_index]) - len(value)]
            limited[token_index] = f"{prefix}{limit}"
        else:
            limited[value_index] = str(limit)
    return limited


def _exec(command: list[str], env: dict[str, str]) -> int:
    sys.stdout.flush()
    sys.stderr.flush()
    try:
        os.execvpe(command[0], command, env)
    except OSError as error:
        print(f"TEST SLOTS: cannot run {command[0]}: {error.strerror}", file=sys.stderr)
        return 127
    return 0  # pragma: no cover - execvpe does not return


def _refuse(error: SlotError) -> int:
    print(f"TEST SLOTS: the command did not run ({error})", file=sys.stderr)
    print(json.dumps({"test_slots": {"outcome": "refused", "reason": error.reason}}), file=sys.stderr)
    return EXIT_REFUSED


def _run(arguments: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    command = arguments.command[1:] if arguments.command[:1] == ["--"] else list(arguments.command)
    if not command:
        parser.error("run needs a command after --")
    env = dict(os.environ)
    auto_cap = auto_worker_cap(env)
    try:
        if not enabled(env):
            return _exec(command, env)
        size = pool_size(env)
        hold = join_inherited(env)
        if hold is None:
            requested = arguments.slots if arguments.slots is not None else requested_processes(command, size, auto_cap)
            hold = acquire(requested, kind="launcher", environ=env)
    except SlotError as error:
        return _refuse(error)
    env.update(hold.environment())
    if __package__:
        from .test_thread_caps import apply
    else:
        from test_thread_caps import apply

    env = apply(env)
    env[XDIST_AUTO_ENV] = str(hold.count if auto_cap is None else min(hold.count, auto_cap))
    hold.inheritable()
    return _exec(limit_processes(command, hold.count, auto_cap), env)


def _print_status(report: dict[str, object]) -> int:
    error = report["error"]
    if error:
        print(f"test slots: unavailable ({error['reason']}: {error['detail']})")  # type: ignore[index]
        return 1
    state = "enabled" if report["enabled"] else "disabled"
    print(
        f"test slots: {state}; {report['slots_in_use']} of {report['pool_size']} slots in use; "
        f"queue {report['queue_depth']} (longest wait {report['longest_wait_s']}s); "
        f"wait limit {report['wait_timeout_s']:g}s"
    )
    for holder in report["holders"]:  # type: ignore[attr-defined]
        print(
            f"  holder {holder['task_id']} {holder['kind']}: {holder['slots']} slot(s), held {holder['held_s']}s, "
            f"waited {holder['waited_s']}s, pid {holder['pid']}"
        )
    for entry in report["queue"]:  # type: ignore[attr-defined]
        print(
            f"  queued {entry['position']}. {entry['task_id']} {entry['kind']}: requests {entry['requested']}, "
            f"waiting {entry['waiting_s']}s, pid {entry['pid']}"
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.common.test_slots",
        description=(
            "Run a test command inside host-wide test slots, or show who holds and waits for them (#10662).\n"
            "Use it to wrap test commands that start several processes. Dispatch-worker pytest runs and the "
            "pre-push gate already take slots, so they need no wrapper."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.common.test_slots run -- .venv/bin/python -m pytest -n 4 -q tests/x.py\n"
            "  .venv/bin/python -m scripts.common.test_slots run --slots 2 -- bash scripts/some_suite.sh\n"
            "  .venv/bin/python -m scripts.common.test_slots status --json\n\n"
            "Environment: LU_TEST_SLOTS (on|off; default on, off under CI=true), LU_TEST_SLOTS_COUNT (pool size;\n"
            "default half the CPUs rounded down, at least 2), LU_TEST_SLOTS_WAIT_S (default 3600), LU_TEST_SLOTS_DIR.\n"
            "LU_TEST_THREAD_CAP (off preserves native thread settings; otherwise applies native thread caps).\n\n"
            "Outputs: lock and ticket files in the private pool directory; progress lines on stderr while waiting.\n"
            "Exit codes: run: the command's own exit code; 75 refused (wait timeout, unusable pool, invalid\n"
            "configuration) and the command did not run; 127 command not found. status: 0, or 1 when the pool\n"
            "cannot be read.\n"
            "Related: docs/runbooks/test-slots.md; GET /api/ops/v1/test-slots; issue #10662."
        ),
    )
    commands = parser.add_subparsers(dest="action", required=True)
    run = commands.add_parser(
        "run",
        help="hold slots, then exec the command so it holds them until it exits",
        description="Wait for slots in FIFO order, cap the command's xdist workers at the slots held, then exec it.",
    )
    run.add_argument(
        "--slots",
        type=int,
        default=None,
        metavar="N",
        help="slots to request; default: the command's -n/--numprocesses value, the pool size for -n auto "
        "(or a lower PYTEST_XDIST_AUTO_NUM_WORKERS already set), otherwise 1 (capped at the pool size)",
    )
    run.add_argument("command", nargs=argparse.REMAINDER, help="the command to run, after --")
    view = commands.add_parser("status", help="read-only view of holders, the queue and wait times")
    view.add_argument("--json", action="store_true", help="print the status object as JSON (default: a summary)")
    arguments = parser.parse_args(argv)
    if arguments.action == "run":
        return _run(arguments, parser)
    report = status()
    if arguments.json:
        print(json.dumps(report, sort_keys=True))
        return 1 if report["error"] else 0
    return _print_status(report)


if __name__ == "__main__":
    sys.exit(main())
