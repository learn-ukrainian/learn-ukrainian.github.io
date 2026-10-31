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
import logging
import os
import re
import threading
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

ARCHIVE_DIR_NAME = "archive"
# Lock-file inodes each thread holds through task_state_lock.
_HELD_TASK_LOCKS = threading.local()
_REDISPATCH_ARCHIVED_STEM_RE = re.compile(r"^(?P<base>.+)\.(?P<tag>\d{8}T\d{6}\d*Z(?:\.\d+)?)\.archived$")
_LOG = logging.getLogger(__name__)


def parse_task_record(path: Path, raw: bytes, *, display_unknown_schema: bool = False) -> dict[str, Any] | None:
    """Distinguish records from sidecars without hiding damaged record claims.

    Dispatch writes an integer schema version and a task-id basename; legacy
    records may identify a run by filename and lifecycle fields alone. The v2
    basename and archive collision stamps follow the by-id naming contract. A
    broken JSON object may have lost its markers to truncation, so it remains
    a record claim and fails closed.
    """
    try:
        record = json.loads(raw.decode("utf-8"))
    except RecursionError as exc:
        raise ValueError(f"task record {path} exceeds JSON parser nesting") from exc
    except ValueError as exc:
        if isinstance(exc, UnicodeDecodeError) or raw.lstrip().removeprefix(b"\xef\xbb\xbf").startswith(b"{"):
            raise
        record = None
    if not isinstance(record, dict):
        _LOG.warning("NON_RECORD_FILE: %s", path)
        return None
    task_id = record.get("task_id")
    legacy = "schema_version" not in record and (
        any(key in record for key in (
            "run_nonce", "worktree_path", "cwd", "acp_runtime_paths", "worktree_prep",
            "review_attempt", "review_contract", "worktree_branch"
        )) or ("agent" in record and "status" in record)
    )
    receipt = ("schema" in record and "schema_version" not in record
               and isinstance(task_id, str) and not candidate_task_record_names(task_id, (path.name,)))
    if receipt or not ("task_id" in record or isinstance(record.get("schema_version"), int) or legacy):
        _LOG.warning("NON_RECORD_FILE: %s", path)
        return None
    if "schema_version" in record and (type(record["schema_version"]) is not int
                                       or record["schema_version"] not in {1, 2}):
        if display_unknown_schema and type(record["schema_version"]) is int and record["schema_version"] > 2:
            # API visibility only: no unknown field can claim a live worker,
            # reviewer, repository, process, grant or result.
            return {"schema_version": record["schema_version"]}
        raise ValueError(f"task record {path} has invalid schema_version")
    if (("task_id" in record and (not isinstance(task_id, str) or not task_id))
            or (record.get("schema_version") == 2 and (
                not isinstance(task_id, str) or not candidate_task_record_names(task_id, (path.name,))
            ))):
        raise ValueError(f"task record {path} has invalid task identity")
    return record


def read_task_record(path: Path) -> dict[str, Any] | None:
    """Read a scan candidate; foreign files are reported, damaged records raise."""
    return parse_task_record(path, path.read_bytes())


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
        for path in paths:
            try:
                if read_task_record(path) is None:
                    continue
            except (OSError, ValueError):
                # The caller owns its refusal/unknown policy. Never filter a
                # damaged record out of an admission, quota or cleanup scan.
                pass
            yield path


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

    The lock is reentrant within one thread: dispatcher settlement holds it while
    worktree removal preserves artifacts into the same record, and a second flock on
    a new descriptor would wait on its own holder forever. Other threads still wait.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path.with_suffix(path.suffix + ".lock"), os.O_CREAT | os.O_RDWR, 0o600)
    held = _HELD_TASK_LOCKS.__dict__.setdefault("inodes", set())
    status = os.fstat(descriptor)
    key = (status.st_dev, status.st_ino)
    if key in held:
        os.close(descriptor)
        yield
        return
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        held.add(key)
        yield
    finally:
        held.discard(key)
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
