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

This module is stdlib-only so any reader can import it cheaply.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

ARCHIVE_DIR_NAME = "archive"


class TaskRecordUnavailable(RuntimeError):
    """A by-id record is missing, unreadable, malformed or kept moving."""


def task_record_path(tasks_dir: Path, task_id: str) -> Path:
    """Return the task record path dispatch writes for ``task_id``."""
    safe = task_id.replace("/", "_").replace("\\", "_")
    return tasks_dir / f"{safe}.json"


def archived_task_record_path(tasks_dir: Path, task_id: str) -> Path:
    """Return where ``stale_task_records archive`` keeps ``task_id``'s record."""
    return task_record_path(tasks_dir / ARCHIVE_DIR_NAME, task_id)


def locate_task_record(tasks_dir: Path, task_id: str) -> Path | None:
    """Return ``task_id``'s record in the hot directory, else in the archive, else ``None``."""
    for path in (task_record_path(tasks_dir, task_id), archived_task_record_path(tasks_dir, task_id)):
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
