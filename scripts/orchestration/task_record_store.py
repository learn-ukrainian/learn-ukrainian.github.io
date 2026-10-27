"""Task-record persistence and where legacy records live: the hot directory and its archive (#8625).

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

Readers remain stdlib-only; writers load cause and dispatcher support lazily.
"""

from __future__ import annotations

import fcntl
import json
import os
import re
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

ARCHIVE_DIR_NAME = "archive"
_REDISPATCH_ARCHIVED_STEM_RE = re.compile(r"^(?P<base>.+)\.(?P<tag>\d{8}T\d{6}\d*Z(?:\.\d+)?)\.archived$")


def task_record_path(tasks_dir: Path, task_id: str) -> Path:
    """Return the task record path dispatch writes for ``task_id``."""
    safe = task_id.replace("/", "_").replace("\\", "_")
    return tasks_dir / f"{safe}.json"


def candidate_task_record_names(task_id: str, names: Iterable[str]) -> tuple[str, ...]:
    """Filter enumerated basenames using dispatch's recursive collision grammar.

    Names are locators only. The caller must check every matching file and its
    embedded identity; neither a safe stem nor its location proves a run.
    """
    target = task_record_path(Path(), task_id).stem
    result = []
    for name in names:
        if not name.endswith(".json"):
            continue
        stem = name[:-5]
        while True:
            if stem == target:
                result.append(name)
                break
            match = _REDISPATCH_ARCHIVED_STEM_RE.fullmatch(stem)
            if match is None:
                break
            stem = match["base"]
    return tuple(sorted(result))


def archived_task_record_path(tasks_dir: Path, task_id: str) -> Path:
    """Return where ``stale_task_records archive`` keeps ``task_id``'s record."""
    return task_record_path(tasks_dir / ARCHIVE_DIR_NAME, task_id)


def locate_task_record(tasks_dir: Path, task_id: str) -> Path | None:
    """Return ``task_id``'s record in the hot directory, else in the archive, else ``None``."""
    for path in (task_record_path(tasks_dir, task_id), archived_task_record_path(tasks_dir, task_id)):
        if path.is_file():
            return path
    return None


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


@contextmanager
def task_state_lock(path: Path) -> Iterator[None]:
    """Use a stable adjacent lock file; locking the replaced JSON inode is unsafe.

    Lock files (<task>.json.lock) are permanent stable anchors: deleting or moving
    a lock file while a writer holds or waits on its descriptor breaks mutual exclusion
    by letting subsequent callers open a new, distinct inode (#8659).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path.with_suffix(path.suffix + ".lock"), os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def write_state_unlocked(path: Path, state: dict[str, Any]) -> None:
    """Replace state while the caller holds its per-task lock."""
    tmp = path.with_suffix(f".json.tmp.{os.getpid()}")
    tmp.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")
    os.replace(tmp, path)


def write_record_unlocked(path: Path, state: dict[str, Any]) -> None:
    """Preserve the legacy public-cause sink and use dispatcher persistence for v2."""
    from scripts.orchestration.task_record_causes import _append_diagnostics, _public_record

    public, recorded = _public_record(state)
    if state.get("schema_version") == 2:
        from scripts.dispatcher import store

        store.replace(public, path)
    else:
        write_state_unlocked(path, public)
    if recorded:
        _append_diagnostics(path, recorded, source="record")
