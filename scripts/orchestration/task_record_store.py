"""Where delegate task records live: the hot directory and its archive (#8625).

``batch_state/tasks/*.json`` is the hot directory. Dispatch, the worktree claim
scan, reapers and every active view read it. ``scripts/orchestration/
stale_task_records.py archive`` moves old terminal records, with their
``.result`` and ``.snapshots`` sidecars, into ``batch_state/tasks/archive/``.

Readers pick one of three contracts:

* **active** views (running, queued, ``needs_finalize``, claims) read the hot
  directory only: an archived record is terminal and claims nothing;
* **by-id** readers use :func:`locate_task_record`, which falls back to the
  archive when the hot record is missing;
* **historical** readers (listings, totals, metrics, lookback reports) call
  :func:`iter_task_records` with ``include_archive=True``, or state in their
  output that their history is bounded to the hot directory.

While a record or its ``.result`` moves between the two directories it can sit
at a hidden staging name, or, when a move fails twice, at a parked name; see
:func:`relocation_residue`.

A reader that needs every record of both directories as of one instant (the
review ledger, #10501) cannot get it from directory listings: a record that
moves between the two can be missed by both. The store therefore keeps a
generation counter, a seqlock. Every supported operation that moves or
rewrites records through this module (archive, restore, stale-record settle,
the review receipt write) runs inside :func:`store_change`, which holds the
store lock, makes the generation odd, does the change, and makes it even
again. :func:`stable_read` reads the generation, runs the read, and reads the
generation again; only an equal, even pair proves no change overlapped it.
In-place atomic rewrites of one record under its own name (dispatch, reapers)
never hide a record and stay outside the protocol, so they never starve
readers. Lock order is the checkout lock, then the store lock, then the
per-task ``<record>.json.lock``.

This module is stdlib-only so any reader can import it cheaply.
"""

from __future__ import annotations

import fcntl
import json
import os
import re
import secrets
import time
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NamedTuple

ARCHIVE_DIR_NAME = "archive"
# The two files a reader resolves by name: the record and its reply.
RECORD_SUFFIXES = (".json", ".result")
_STAGING = re.compile(r"\.(?P<name>.+)\.\d+\.[0-9a-f]{32}\.moving")
_PARKED = re.compile(r"(?P<name>.+)\.unplaced-[0-9a-f]{12}")
# The store's control directory, its generation file and its lock file. No
# record reader or sweep matches these names.
CONTROL_DIR_NAME = ".task-record-store"
GENERATION_NAME = "generation"
LOCK_NAME = "lock"
_EPOCH = re.compile(r"[0-9a-f]{16}")
# A read that a change overlapped is retried this many times, backing off
# READ_BACKOFF_S, then twice that, before it is unavailable.
READ_ATTEMPTS = 3
READ_BACKOFF_S = 0.05
_DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC


class TaskRecordUnavailable(RuntimeError):
    """A by-id record is missing, unreadable, malformed or kept moving."""


class StoreGeneration(NamedTuple):
    """The store's seqlock value: odd while a change runs. ``epoch`` is ``None`` for a store never changed."""

    epoch: str | None
    value: int


LEGACY_GENERATION = StoreGeneration(None, 0)


class StoreUnstable(TaskRecordUnavailable):
    """No read of the store was coherent; ``partial`` is the last read, whose facts may predate a change."""

    def __init__(self, reason: str, partial: Any = None) -> None:
        super().__init__(reason)
        self.partial = partial


@dataclass(frozen=True)
class StoreChange:
    """One :func:`store_change`: the odd generation it holds and any abandoned change it repaired."""

    generation: StoreGeneration
    repaired: str | None


def _parse_generation(raw: bytes) -> StoreGeneration | None:
    try:
        data = json.loads(raw)
    except (ValueError, RecursionError):
        return None
    if not isinstance(data, dict) or set(data) != {"epoch", "generation"}:
        return None
    epoch, value = data["epoch"], data["generation"]
    if not isinstance(epoch, str) or not _EPOCH.fullmatch(epoch) or type(value) is not int or value < 0:
        return None
    return StoreGeneration(epoch, value)


def _read_at(dir_fd: int, name: str) -> bytes:
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=dir_fd)
    try:
        chunks = []
        while chunk := os.read(fd, 65536):
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(fd)


def read_generation(tasks_dir: Path) -> StoreGeneration:
    """The store's current generation, read without the lock.

    A store whose control directory was never created is the legacy store,
    :data:`LEGACY_GENERATION`. Once it exists, a missing, unreadable or
    malformed generation file (or a control directory that is a symlink)
    raises :class:`TaskRecordUnavailable`.
    """
    try:
        control = os.open(tasks_dir / CONTROL_DIR_NAME, _DIR_FLAGS)
    except FileNotFoundError:
        if os.path.lexists(tasks_dir / CONTROL_DIR_NAME):
            raise TaskRecordUnavailable("task store control directory unreadable") from None
        return LEGACY_GENERATION
    except OSError as exc:
        raise TaskRecordUnavailable("task store control directory unreadable") from exc
    try:
        raw = _read_at(control, GENERATION_NAME)
    except FileNotFoundError as exc:
        raise TaskRecordUnavailable("task store generation missing") from exc
    except OSError as exc:
        raise TaskRecordUnavailable("task store generation unreadable") from exc
    finally:
        os.close(control)
    generation = _parse_generation(raw)
    if generation is None:
        raise TaskRecordUnavailable("task store generation malformed")
    return generation


def _write_generation(control: int, generation: StoreGeneration) -> None:
    """Replace the generation file atomically and durably: temp file, fsync, rename, fsync the directory."""
    temp = f"{GENERATION_NAME}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
    payload = json.dumps({"epoch": generation.epoch, "generation": generation.value}).encode("utf-8")
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o644, dir_fd=control)
    try:
        try:
            os.write(fd, payload)
            os.fsync(fd)
        finally:
            os.close(fd)
        os.replace(temp, GENERATION_NAME, src_dir_fd=control, dst_dir_fd=control)
    except BaseException:
        with suppress(OSError):
            os.unlink(temp, dir_fd=control)
        raise
    os.fsync(control)


def _locked_generation(control: int) -> tuple[StoreGeneration, str | None]:
    """The generation a lock holder continues from, and what it repaired to get there.

    Every writer holds the lock for its whole odd window, so an odd value seen
    under the lock was left by a writer that died (the kernel drops a dead
    process's lock): it is repaired at once, with no age bound. A missing
    file starts a new epoch at zero; so does an unreadable or malformed one,
    and a new epoch never equals any value a reader saw before.
    """
    try:
        current = _parse_generation(_read_at(control, GENERATION_NAME))
    except FileNotFoundError:
        return StoreGeneration(secrets.token_hex(8), 0), None
    except OSError:
        current = None
    if current is None:
        return StoreGeneration(secrets.token_hex(8), 0), "malformed generation replaced by a new epoch"
    if current.value % 2:
        return current._replace(value=current.value + 1), f"abandoned change at generation {current.value} closed"
    return current, None


@contextmanager
def store_change(tasks_dir: Path) -> Iterator[StoreChange]:
    """Hold the store lock with the generation odd while the body moves or rewrites records.

    The generation is made even again when the body ends, also when it
    raises: whatever the body did is then visible. Take the store lock after
    any checkout lock and before any per-task lock, and take no other lock
    while holding it. The control directory and lock file are created on the
    first change and never removed.
    """
    control_path = tasks_dir / CONTROL_DIR_NAME
    with suppress(FileExistsError):
        os.mkdir(control_path, 0o755)
    control = os.open(control_path, _DIR_FLAGS)
    try:
        lock = os.open(LOCK_NAME, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=control)
        try:
            fcntl.flock(lock, fcntl.LOCK_EX)
            base, repaired = _locked_generation(control)
            inside = base._replace(value=base.value + 1)
            _write_generation(control, inside)
            try:
                yield StoreChange(inside, repaired)
            finally:
                _write_generation(control, inside._replace(value=inside.value + 1))
        finally:
            os.close(lock)  # Closing the descriptor releases the lock.
    finally:
        os.close(control)


# The highest generation each store showed this process: a store whose
# generation goes back, or whose epoch changes, was reset under its readers.
_GENERATION_FLOOR: dict[str, StoreGeneration] = {}


def _observe(key: str, generation: StoreGeneration) -> None:
    """Record a generation this process read; raise :class:`StoreUnstable` if it is not monotonic."""
    floor = _GENERATION_FLOOR.get(key)
    if floor is not None and floor.epoch is not None:
        if generation.epoch != floor.epoch:
            raise StoreUnstable("task store generation reset since this process read it")
        if generation.value < floor.value:
            raise StoreUnstable("task store generation went backwards")
    if floor is None or generation.epoch != floor.epoch or generation.value > floor.value:
        _GENERATION_FLOOR[key] = generation


def stable_read[T](tasks_dir: Path, read: Callable[[], T], *, attempts: int | None = None) -> T:
    """Run ``read`` until no store change overlaps it (the seqlock read side).

    The generation is read before and after ``read``; the result counts only
    when both are equal and even. Otherwise the read is retried after a short
    backoff, at most ``attempts`` (default :data:`READ_ATTEMPTS`) times, and
    then :class:`StoreUnstable` is raised with the last result as ``partial``.
    A missing, unreadable or malformed generation is retried the same way. A
    generation lower than, or in another epoch than, one this process already
    read raises at once. ``read`` exceptions propagate.
    """
    key = os.path.abspath(tasks_dir)
    limit = READ_ATTEMPTS if attempts is None else attempts
    reason = "task store unstable"
    partial: Any = None
    for attempt in range(limit):
        if attempt:
            time.sleep(READ_BACKOFF_S * 2 ** (attempt - 1))
        try:
            before = read_generation(tasks_dir)
        except TaskRecordUnavailable as exc:
            reason = str(exc)
            continue
        _observe(key, before)
        if before.value % 2:
            reason = f"task store change in progress at generation {before.value}"
            continue
        partial = read()
        try:
            after = read_generation(tasks_dir)
        except TaskRecordUnavailable as exc:
            reason = str(exc)
            continue
        _observe(key, after)
        if after == before:
            return partial
        reason = "task store changed while it was read"
    raise StoreUnstable(f"{reason}; no coherent read in {limit} attempts", partial)


def staging_name(name: str) -> str:
    """The private name a file called ``name`` takes while it moves (unique per process and call)."""
    return f".{name}.{os.getpid()}.{uuid.uuid4().hex}.moving"


def parked_name(name: str) -> str:
    """The visible name a staged file gets when neither its destination nor its home is free."""
    return f"{name}.unplaced-{uuid.uuid4().hex[:12]}"


def relocation_residue(name: str) -> str | None:
    """``"moving"`` or ``"parked"`` when ``name`` is a record or reply held outside its record name.

    A reader that meets one cannot see that file where it looks for it: a
    staged file is mid-move, a parked one stays hidden until someone recovers it.
    """
    for kind, pattern in (("moving", _STAGING), ("parked", _PARKED)):
        match = pattern.fullmatch(name)
        if match is not None and match["name"].endswith(RECORD_SUFFIXES):
            return kind
    return None


def task_record_path(tasks_dir: Path, task_id: str) -> Path:
    """Return the task record path dispatch writes for ``task_id``."""
    safe = task_id.replace("/", "_").replace("\\", "_")
    return tasks_dir / f"{safe}.json"


def archived_task_record_path(tasks_dir: Path, task_id: str) -> Path:
    """Return where ``stale_task_records archive`` keeps ``task_id``'s record."""
    return task_record_path(tasks_dir / ARCHIVE_DIR_NAME, task_id)


def locate_task_record(tasks_dir: Path, task_id: str) -> Path | None:
    """Return ``task_id``'s record in the hot directory, else in the archive, else ``None``.

    The hot name is probed again after the archive: a restore that moved the
    record between the first two probes is found there. A record caught at
    its staging name by an archive move still reads as ``None``.
    """
    hot = task_record_path(tasks_dir, task_id)
    for path in (hot, archived_task_record_path(tasks_dir, task_id), hot):
        if path.is_file():
            return path
    return None


def update_located_record(
    tasks_dir: Path, task_id: str, update: Callable[[dict[str, Any]], dict[str, Any] | None]
) -> Path:
    """Apply ``update`` to ``task_id``'s hot or archived record under its per-task lock.

    The record is re-read after the lock is taken, so a concurrent locked
    writer's fields survive. ``update`` returns the record to write, or
    ``None`` to leave it as it is; it may raise to refuse. A record that an
    archive or restore moved between lookup and lock is located again, once.
    The write is a :func:`store_change`. The lock and writer are the dispatch
    ones, imported lazily so readers of this module stay stdlib-only.
    """
    from scripts.orchestration.dead_worker_state import task_state_lock, write_state_unlocked

    for _attempt in range(2):
        path = locate_task_record(tasks_dir, task_id)
        if path is None:
            raise TaskRecordUnavailable("task record not found")
        with store_change(tasks_dir), task_state_lock(path):
            if not path.is_file():
                continue
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                raise TaskRecordUnavailable("task record unreadable") from exc
            if not isinstance(record, dict):
                raise TaskRecordUnavailable("task record malformed")
            updated = update(record)
            if updated is not None:
                write_state_unlocked(path, updated)
            return path
    raise TaskRecordUnavailable("task record moved during update")


def iter_task_records(tasks_dir: Path, *, include_archive: bool) -> Iterator[Path]:
    """Yield task record files: the hot directory sorted by name, then the archive.

    ``include_archive=False`` is the hot directory alone, the view every active
    reader needs. A task id re-dispatched after its old record was archived has
    one record in each place; both are yielded because they are two runs. A
    directory that is missing or unreadable yields nothing.
    """
    directories = [tasks_dir, tasks_dir / ARCHIVE_DIR_NAME] if include_archive else [tasks_dir]
    for directory in directories:
        try:
            paths = sorted(path for path in directory.glob("*.json") if path.is_file())
        except OSError:
            continue
        yield from paths


def relocated_result_file(record_path: Path, result_file: str | None) -> str | None:
    """Return where ``result_file`` lives now for the record at ``record_path``.

    A record keeps the hot-directory ``result_file`` path it was written with.
    Archiving moves the ``.result`` sidecar next to the archived record, so an
    archived record's sidecar is looked up beside it; any other path is returned
    unchanged.
    """
    if record_path.parent.name != ARCHIVE_DIR_NAME or not isinstance(result_file, str) or not result_file:
        return result_file
    moved = record_path.with_name(Path(result_file).name)
    return str(moved) if moved.is_file() else result_file
