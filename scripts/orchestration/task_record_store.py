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

This module is stdlib-only so any reader can import it cheaply.
"""

from __future__ import annotations

import json
import os
import re
import uuid
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

ARCHIVE_DIR_NAME = "archive"
# The two files a reader resolves by name: the record and its reply.
RECORD_SUFFIXES = (".json", ".result")
_STAGING = re.compile(r"\.(?P<name>.+)\.\d+\.[0-9a-f]{32}\.moving")
_PARKED = re.compile(r"(?P<name>.+)\.unplaced-[0-9a-f]{12}")


class TaskRecordUnavailable(RuntimeError):
    """A by-id record is missing, unreadable, malformed or kept moving."""


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
    The lock and writer are the dispatch ones, imported lazily so readers of
    this module stay stdlib-only.
    """
    from scripts.orchestration.dead_worker_state import task_state_lock, write_state_unlocked

    for _attempt in range(2):
        path = locate_task_record(tasks_dir, task_id)
        if path is None:
            raise TaskRecordUnavailable("task record not found")
        with task_state_lock(path):
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
