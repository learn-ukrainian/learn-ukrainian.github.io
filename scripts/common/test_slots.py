"""Host-wide test-run slot pool: worker pytest runs and the pre-push gate share the host's CPUs (#10662).

A governed test run takes slots from one pool before it starts its processes and returns them when it ends.
It asks for its xdist worker count (one for a serial run), capped at the pool size so every request can be met,
and waits in a first-come-first-served queue, printing its position, until that many slots are free. Only the
head of the queue takes slots, so a large request is never starved by smaller ones behind it.

``flock`` is the only liveness proof. Each slot is a lock file, and each waiting or holding run keeps its ticket
locked. The kernel drops a lock when its process exits, including on SIGKILL, so a crashed run frees its slots
at once. Files a dead process leaves behind are inert and the next waiter reaps them. Lock files are permanent:
deleting one while a holder keeps it open would let a second holder lock a fresh inode.

The pool is ``<fleet scratch root>/learn-ukrainian/test-slots-<uid>``. ``LU_SCRATCH_ROOT`` overrides the default
root (``DEFAULT_SCRATCH_ROOT``), as in ``scratch.py``. It is mode 0700 and owned by this user. It never falls back to
a per-process temp directory, which would split the pool, and it never lies inside a Git checkout or Git directory.

Environment:
  LU_TEST_SLOTS         on or off. Default on, except where ``CI`` is true, so CI runs are unchanged.
  LU_TEST_SLOTS_COUNT   pool size. Default: the CPU count minus 2 for services, and at least 2.
  LU_TEST_SLOTS_WAIT_S  longest wait for slots in seconds (default 3600), then a typed refusal.
  LU_TEST_SLOTS_DIR     absolute pool directory, for tests and experiments.
  LU_TEST_SLOTS_HOLDER  set by a holder for its descendants, which then run inside its slots.

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
import json
import math
import os
import re
import stat
import sys
import time
import uuid
from collections.abc import Callable, Iterator, Mapping
from pathlib import Path

# The fleet scratch-root convention of scripts/common/scratch.py, minus its per-process temp fallback.
SCRATCH_ROOT_ENV = "LU_SCRATCH_ROOT"
DEFAULT_SCRATCH_ROOT = Path("/var/tmp/lu")

ENABLE_ENV = "LU_TEST_SLOTS"
COUNT_ENV = "LU_TEST_SLOTS_COUNT"
WAIT_ENV = "LU_TEST_SLOTS_WAIT_S"
DIR_ENV = "LU_TEST_SLOTS_DIR"
HOLDER_ENV = "LU_TEST_SLOTS_HOLDER"
TASK_ENV = "LEARN_UKRAINIAN_DISPATCH_TASK_ID"
XDIST_AUTO_ENV = "PYTEST_XDIST_AUTO_NUM_WORKERS"
SERVICE_RESERVE = 2
MIN_DEFAULT_SLOTS = 2
DEFAULT_WAIT_S = 3600.0
POLL_S = 0.1
REPORT_EVERY_S = 30.0
MAX_TICKETS = 1024
MAX_RECORD_BYTES = 4096
PENDING_GRACE_S = 60.0
STATUS_SCHEMA = "test-slots.status.v1"
EXIT_REFUSED = 75  # EX_TEMPFAIL: the command did not run; retry once slots free up
KINDS = frozenset({"gate", "pytest", "launcher"})
_TRUE = frozenset({"on", "1", "true", "yes"})
_FALSE = frozenset({"off", "0", "false", "no"})
_TASK_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}")
_COUNT_RE = re.compile(r"[0-9]{1,6}")
_PROCESS_FLAGS = ("-n", "--numprocesses")
_AUTO_VALUES = frozenset({"auto", "logical"})


class SlotError(Exception):
    """A typed refusal. ``reason`` is ``invalid_configuration``, ``pool_unavailable`` or ``wait_timeout``.

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
    return max(MIN_DEFAULT_SLOTS, (os.cpu_count() or 0) - SERVICE_RESERVE)


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


def pool_dir(environ: Mapping[str, str] | None = None) -> Path:
    """The pool directory this environment selects; nothing is created."""
    env = os.environ if environ is None else environ
    override = env.get(DIR_ENV, "").strip()
    if override:
        if not os.path.isabs(override):
            raise SlotError("invalid_configuration", f"{DIR_ENV} must be an absolute path")
        return Path(override)
    root = env.get(SCRATCH_ROOT_ENV, "").strip()
    base = Path(root) if root else DEFAULT_SCRATCH_ROOT
    if not base.is_absolute():
        raise SlotError("invalid_configuration", f"{SCRATCH_ROOT_ENV} must be an absolute path")
    return base / "learn-ukrainian" / f"test-slots-{os.geteuid()}"


# ---- the pool directory ---------------------------------------------------------------------------------------


def _inside_git(path: Path) -> bool:
    """Whether ``path`` or an ancestor is a Git checkout, a linked worktree or a Git directory."""
    for candidate in (path, *path.parents):
        if candidate.name == ".git" or os.path.lexists(candidate / ".git"):
            return True
        if (candidate / "HEAD").is_file() and (candidate / "objects").is_dir() and (candidate / "refs").is_dir():
            return True
    return False


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
    path = pool_dir(env)
    if _inside_git(Path(os.path.realpath(path))):
        raise SlotError(
            "pool_unavailable",
            f"the pool directory lies inside a Git checkout or Git directory; point {DIR_ENV} or "
            f"{SCRATCH_ROOT_ENV} outside every checkout",
        )
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
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
    """Live tickets in queue order with their records; ``reap`` unlinks the ones no process holds."""
    try:
        names = sorted(name for name in os.listdir(directory) if name.endswith(".ticket") and not name.startswith("."))
    except FileNotFoundError:
        return []
    if len(names) > MAX_TICKETS:
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


def _take_slots(pool: Path, count: int, size: int) -> list[tuple[int, int]] | None:
    """Lock ``count`` free slot files, or none at all."""
    taken: list[tuple[int, int]] = []
    try:
        for index in range(size):
            fd = os.open(pool / f"slot-{index:03d}.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
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
        descriptors: tuple[int, ...] = (),
    ) -> None:
        self.count = count
        self.requested = requested
        self.pool_size = pool_size
        self.waited = waited
        self.queue_position = queue_position
        self._record = record
        self._descriptors = descriptors
        self._released = False

    @classmethod
    def inherited(cls, count: int) -> Hold:
        """The slots of a live ancestor holder: nothing to release, and children inherit its marker."""
        return cls(count=count, requested=count, pool_size=count, waited=0.0, queue_position=0)

    def marker(self) -> str:
        """``<count>:<holder record>`` for :data:`HOLDER_ENV`; empty for an inherited hold."""
        return f"{self.count}:{self._record}" if self._record is not None else ""

    def environment(self) -> dict[str, str]:
        """Variables a child needs to run inside these slots rather than queue for its own."""
        return {HOLDER_ENV: self.marker()} if self._record is not None else {}

    def inheritable(self) -> None:
        """Keep the locks across ``exec``, so the command itself holds the slots until it exits."""
        for fd in self._descriptors:
            os.set_inheritable(fd, True)

    def release(self) -> None:
        if self._released:
            return
        self._released = True
        if self._record is not None:
            with contextlib.suppress(OSError):
                self._record.unlink()
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
    """Publish the holder record and leave the queue while the queue decision is still serialized."""
    waited = time.monotonic() - started
    record = {
        **identity,
        "held": count,
        "slots": [index for index, _ in slots],
        "acquired_at": time.time(),
        "waited_s": round(waited, 3),
    }
    try:
        holder, holder_fd = _publish(pool / "holders", record)
    except BaseException:
        for _, fd in slots:
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
        descriptors=(*(fd for _, fd in slots), holder_fd),
    )


def inherited_hold(environ: Mapping[str, str] | None = None) -> int | None:
    """Slots of a live ancestor holder named by :data:`HOLDER_ENV`, else ``None``.

    The marker is checked, not trusted: a dead holder's record is unlocked, so a stale variable is ignored.
    """
    env = os.environ if environ is None else environ
    count, _, record = env.get(HOLDER_ENV, "").partition(":")
    path = Path(record)
    if _COUNT_RE.fullmatch(count) is None or int(count) < 1 or not path.is_absolute():
        return None
    if path.parent.name != "holders" or path.suffix != ".ticket":
        return None
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError:
        return None
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            return None
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return int(count)
        return None
    finally:
        os.close(fd)


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


def status(environ: Mapping[str, str] | None = None) -> dict[str, object]:
    """Read-only pool view: holders by task, the queue in order, and wait times. Never names a path."""
    env = os.environ if environ is None else environ
    report: dict[str, object] = {
        "schema": STATUS_SCHEMA,
        "enabled": None,
        "pool_size": None,
        "wait_timeout_s": None,
        "location": "override" if env.get(DIR_ENV, "").strip() else "default",
        "pool_exists": False,
        "slots_in_use": 0,
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
        path = pool_dir(env)
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
            for _, record in _scan(path / "holders", reap=False)
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
            slots_free=max(0, size - in_use),
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


def requested_processes(command: list[str], size: int) -> int:
    """The worker count a wrapped command asks for: its last ``-n``, the pool for auto, otherwise 1."""
    requested = 1
    for index in range(len(command)):
        found = _process_value(command, index)
        if found is None:
            continue
        value = found[2]
        if value in _AUTO_VALUES:
            requested = size
        elif value.isdigit():
            requested = max(1, int(value))
    return requested


def limit_processes(command: list[str], count: int) -> list[str]:
    """Rewrite every visible ``-n`` above ``count`` (or auto) to ``count``."""
    limited = list(command)
    for index in range(len(command)):
        found = _process_value(command, index)
        if found is None:
            continue
        token_index, value_index, value = found
        if value in _AUTO_VALUES or (value.isdigit() and int(value) > count):
            if value_index == token_index:
                prefix = limited[token_index][: len(limited[token_index]) - len(value)]
                limited[token_index] = f"{prefix}{count}"
            else:
                limited[value_index] = str(count)
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
    try:
        if not enabled(env):
            return _exec(command, env)
        size = pool_size(env)
        inherited = inherited_hold(env)
        if inherited is not None:
            hold = Hold.inherited(inherited)
        else:
            requested = arguments.slots if arguments.slots is not None else requested_processes(command, size)
            hold = acquire(requested, kind="launcher", environ=env)
    except SlotError as error:
        return _refuse(error)
    env.update(hold.environment())
    env[XDIST_AUTO_ENV] = str(hold.count)
    hold.inheritable()
    return _exec(limit_processes(command, hold.count), env)


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
            "default CPUs minus 2, at least 2), LU_TEST_SLOTS_WAIT_S (default 3600), LU_TEST_SLOTS_DIR.\n\n"
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
        help="slots to request; default: the command's -n/--numprocesses value, the pool size for -n auto, "
        "otherwise 1 (capped at the pool size)",
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
