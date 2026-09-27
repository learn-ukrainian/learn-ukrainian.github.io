#!/usr/bin/env python3
"""Shrink clean read-only snapshot sidecars under batch_state, and report the rest.

Use this to turn old terminal ``tasks/*.snapshots/`` directories that recorded an
explicit clean checkout into a ``digest.json``. Do not use it to delete manifests,
atlas output, open-model data, or any other batch_state subtree: those are
reported and left untouched. Dry-run is the default; pass ``--apply`` to write.
"""

from __future__ import annotations

import argparse
import contextlib
import errno
import fcntl
import json
import os
import re
import secrets
import stat
import sys
from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
for _path in (REPO_ROOT, SCRIPTS_DIR):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from scripts import delegate
from scripts.orchestration.stale_task_records import (
    DEFAULT_LOCK_TIMEOUT_S,
    _record_age_days,
    _record_lock_target,
)
from scripts.orchestration.task_record_store import ARCHIVE_DIR_NAME
from scripts.orchestration.worktree_claims import RELEASED_TASK_STATUSES, WorktreeLockError

DEFAULT_BATCH_STATE = REPO_ROOT / "batch_state"
# A clean verdict already lives on the task record, so the full JSON has no
# forensic value after a day. Seven days reclaimed nothing: the dirs are younger.
DEFAULT_MIN_AGE_DAYS = 1.0
_SNAPSHOT_SUFFIX = delegate._READ_ONLY_CHECKOUT_SNAPSHOT_SUFFIX
# Only these directory globs may be rewritten. Everything else under batch_state
# is measured and left alone.
_ALLOWLISTED_SNAPSHOT_PARENTS = ("", ARCHIVE_DIR_NAME)
_PHASES = ("pre", "post")
# ``path_safety`` does not open by directory fd. Every name below the
# batch_state fd is a single path component; ``..`` and symlinks never become
# a path string passed to open/stat/replace/unlink.
_DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
_READ_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
# ``_temp_name`` is ``.{name}.{pid}.{16 hex}.tmp``. Only that shape is ours.
_OWN_TEMP_RE = re.compile(r"^\..+\.[0-9]+\.[0-9a-f]{16}\.tmp\Z")
_OWN_TEMP_MAX_AGE_S = 60 * 60


def _component(name: str) -> bool:
    return name not in {"", ".", ".."} and "/" not in name and "\x00" not in name


def _open_root(batch_state: Path) -> int:
    """Open the real ``batch_state`` directory. A symlink or any other name is refused."""
    if batch_state.name != "batch_state":
        raise ValueError(f"refusing to sweep {batch_state}: path must be a directory named batch_state")
    try:
        return os.open(batch_state, _DIR_FLAGS)
    except OSError as exc:
        raise ValueError(f"refusing to sweep {batch_state}: path must be a directory named batch_state") from exc


def _open_dir(dir_fd: int, name: str) -> int | None:
    if not _component(name):
        return None
    try:
        return os.open(name, _DIR_FLAGS, dir_fd=dir_fd)
    except OSError:
        return None


def _lstat_at(dir_fd: int, name: str) -> os.stat_result | None:
    if not _component(name):
        return None
    try:
        return os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
    except OSError:
        return None


def _is_regular(dir_fd: int, name: str) -> bool:
    info = _lstat_at(dir_fd, name)
    return info is not None and stat.S_ISREG(info.st_mode)


def _read_regular_at(dir_fd: int, name: str) -> bytes | None:
    """Read one regular file in ``dir_fd``. A symlink or a swap of ``name`` is not followed."""
    if not _component(name):
        return None
    try:
        fd = os.open(name, _READ_FLAGS, dir_fd=dir_fd)
    except OSError:
        return None
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            return None
        chunks: list[bytes] = []
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(fd)


def _temp_name(name: str) -> str:
    """A private name inside one directory fd. A leftover ``.{name}.tmp.{pid}`` does not match it."""
    return f".{name}.{os.getpid()}.{secrets.token_hex(8)}.tmp"


def _original_mode(dir_fd: int, name: str) -> int | None:
    """Permission bits of the regular file ``name``, from the inode ``open`` returned."""
    try:
        fd = os.open(name, _READ_FLAGS, dir_fd=dir_fd)
    except OSError:
        return None
    try:
        info = os.fstat(fd)
    finally:
        os.close(fd)
    if not stat.S_ISREG(info.st_mode):
        return None
    return stat.S_IMODE(info.st_mode)


def _write_bytes_at(dir_fd: int, name: str, raw: bytes) -> None:
    """Create or replace ``name`` inside ``dir_fd`` without a path below the root fd.

    The temp name is unique, so a stale ``.{name}.tmp.{pid}`` left by a killed
    run cannot make ``O_EXCL`` fail. On any failure after the temp is created,
    that temp is unlinked; a name this call did not create is left alone.
    Replacing a regular file keeps that file's mode. A new name is owner-only.
    """
    if not _component(name):
        raise OSError(errno.EINVAL, f"refusing to write {name}: symlink or path outside batch_state")
    preserved = _original_mode(dir_fd, name)
    tmp = _temp_name(name)
    if not _component(tmp):
        raise OSError(errno.EINVAL, f"refusing to write {tmp}")
    fd = os.open(
        tmp,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
        preserved if preserved is not None else 0o600,
        dir_fd=dir_fd,
    )
    try:
        view = memoryview(raw)
        while view:
            view = view[os.write(fd, view) :]
        if preserved is not None:
            os.fchmod(fd, preserved)
    except OSError:
        os.close(fd)
        with contextlib.suppress(OSError):
            os.unlink(tmp, dir_fd=dir_fd)
        raise
    os.close(fd)
    try:
        os.replace(tmp, name, src_dir_fd=dir_fd, dst_dir_fd=dir_fd)
    except OSError:
        with contextlib.suppress(OSError):
            os.unlink(tmp, dir_fd=dir_fd)
        raise


def _reap_own_temps(dir_fd: int, rel_dir: str, *, now: datetime, apply: bool) -> list[dict[str, str]]:
    """Report this sweep's temp files in ``dir_fd`` once they are older than an hour.

    Unlink them only when ``apply`` is true. Dry-run reports the same names and
    leaves every inode in place. The name must match :func:`_temp_name` exactly.
    The open uses ``O_NOFOLLOW`` on ``dir_fd``, so a symlink of that name is
    left in place. A younger file may belong to a live writer and is left alone.
    """
    cutoff = now.timestamp() - _OWN_TEMP_MAX_AGE_S
    matched: list[dict[str, str]] = []
    for name in _names(dir_fd):
        if _OWN_TEMP_RE.fullmatch(name) is None:
            continue
        try:
            fd = os.open(name, _READ_FLAGS, dir_fd=dir_fd)
        except OSError:
            continue
        try:
            info = os.fstat(fd)
        finally:
            os.close(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_mtime >= cutoff:
            continue
        if apply:
            try:
                os.unlink(name, dir_fd=dir_fd)
            except OSError:
                continue
        matched.append({"dir": rel_dir, "name": name})
    return matched


def _collect_own_temps(
    temps_removed: list[dict[str, str]],
    temps_would_remove: list[dict[str, str]],
    dir_fd: int,
    rel_dir: str,
    *,
    now: datetime,
    apply: bool,
) -> None:
    """Record stale own-temps. Only the apply pass unlinks them."""
    found = _reap_own_temps(dir_fd, rel_dir, now=now, apply=apply)
    if apply:
        temps_removed.extend(found)
    else:
        temps_would_remove.extend(found)


def _unlink_regular_at(dir_fd: int, name: str) -> None:
    if not _is_regular(dir_fd, name):
        return
    with contextlib.suppress(OSError):
        os.unlink(name, dir_fd=dir_fd)


def _file_bytes_at(dir_fd: int, name: str) -> int:
    info = _lstat_at(dir_fd, name)
    if info is None or not stat.S_ISREG(info.st_mode):
        return 0
    return info.st_size


def _tree_bytes_at(dir_fd: int) -> int:
    try:
        names = os.listdir(dir_fd)
    except OSError:
        return 0
    total = 0
    for name in names:
        info = _lstat_at(dir_fd, name)
        if info is None or stat.S_ISLNK(info.st_mode):
            continue
        if stat.S_ISREG(info.st_mode):
            total += info.st_size
        elif stat.S_ISDIR(info.st_mode):
            child = _open_dir(dir_fd, name)
            if child is None:
                continue
            try:
                total += _tree_bytes_at(child)
            finally:
                os.close(child)
    return total


def _names(dir_fd: int) -> list[str]:
    try:
        return sorted(os.listdir(dir_fd))
    except OSError:
        return []


@contextlib.contextmanager
def _task_record_lock(parent_fd: int, record_name: str) -> Iterator[None]:
    """Lock ``<record>.lock`` in ``parent_fd`` — the same file :func:`task_state_lock` uses.

    ``Path.with_suffix(suffix + ".lock")`` on ``foo.json`` is ``foo.json.lock``.
    Opening it through the directory fd keeps a parent-directory swap from
    redirecting the lock.
    """
    fd = os.open(
        record_name + ".lock",
        os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC,
        0o600,
        dir_fd=parent_fd,
    )
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _hot_pair(parent_fd: int, record_name: str, snapshot_name: str, snap_fd: int) -> bool:
    """True when the record and snapshot dir are still the hot names we locked.

    Archive renames both out of this directory. A leftover fd must not be
    treated as the hot path, and a replaced directory inode must not either.
    """
    record = _lstat_at(parent_fd, record_name)
    current = _lstat_at(parent_fd, snapshot_name)
    if record is None or current is None:
        return False
    if not stat.S_ISREG(record.st_mode) or not stat.S_ISDIR(current.st_mode):
        return False
    held = os.fstat(snap_fd)
    return (current.st_dev, current.st_ino) == (held.st_dev, held.st_ino)


def _phase_snapshots(snap_fd: int) -> tuple[dict[str, str], dict[str, str]] | None:
    """Return parsed phase maps when both files are regular JSON objects in ``snap_fd``."""
    loaded: list[dict[str, str]] = []
    for phase in _PHASES:
        raw = _read_regular_at(snap_fd, f"read_only_checkout_{phase}.json")
        if raw is None:
            return None
        try:
            payload = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None
        if not isinstance(payload, dict):
            return None
        loaded.append(payload)
    return loaded[0], loaded[1]


def _explicit_clean(record: dict[str, Any]) -> bool:
    """True only when the record itself says the checkout was clean.

    A missing key is not a clean verdict: older records predate the field and
    must keep their full sidecars.
    """
    if "read_only_mutation_paths" not in record or "read_only_checkout_snapshot_error" not in record:
        return False
    return record["read_only_mutation_paths"] == [] and record["read_only_checkout_snapshot_error"] is None


def _eligible(
    record: dict[str, Any] | None,
    info: os.stat_result | None,
    *,
    min_age_days: float,
    now: datetime,
) -> bool:
    if (
        record is None
        or info is None
        or record.get("status") not in RELEASED_TASK_STATUSES
        or not _explicit_clean(record)
    ):
        return False
    if not stat.S_ISREG(info.st_mode):
        return False
    return _record_age_days(record, info.st_mtime_ns, now) >= min_age_days


def _read_record_at(parent_fd: int, record_name: str) -> dict[str, Any] | None:
    raw = _read_regular_at(parent_fd, record_name)
    if raw is None:
        return None
    try:
        loaded = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return loaded if isinstance(loaded, dict) else None


def _record_name_for(snapshot_name: str) -> str | None:
    if not snapshot_name.endswith(_SNAPSHOT_SUFFIX):
        return None
    stem = snapshot_name[: -len(_SNAPSHOT_SUFFIX)]
    if not stem or not _component(stem):
        return None
    return f"{stem}.json"


def _digest_bytes(pre: dict[str, str], post: dict[str, str]) -> bytes:
    return json.dumps(delegate.read_only_snapshot_digest(pre, post), separators=(",", ":")).encode("utf-8")


def _apply_one(
    parent_fd: int,
    snapshot_name: str,
    record_name: str,
    logical_record: Path,
    observed: dict[str, Any],
    *,
    observed_status: Any,
    observed_nonce: Any,
    min_age_days: float,
    now: datetime,
    crash_after: str | None,
    on_after_digest: Callable[[], None] | None,
) -> dict[str, str] | None:
    """Digest one sidecar. Return the action row, or None to skip.

    Lock order is the checkout lock, then the per-task record lock
    (``<record>.json.lock``, the file :func:`task_state_lock` uses). Every
    mover of a task record:

    * this sweep: checkout lock, then the per-task lock, for the whole rewrite
    * dispatch (``_write_state_atomic``): the checkout lock, then the per-task lock
    * ``delegate._archive_task_artifacts`` (``--force-new``): the per-task lock
      around the rename, released before dispatch takes the checkout lock
    * ``stale_task_records._restore_group``: the per-task lock on the archived
      record around that record's move
    * ``stale_task_records.archive_terminal``: the checkout lock
      (:func:`_record_lock_target`) while it renames the record and its sidecar

    Taking the per-task lock and then waiting on the checkout lock deadlocks
    a holder that already has the checkout lock and is waiting for the per-task
    lock. ``_archive_task_artifacts`` does not do that: it drops the per-task
    lock before dispatch acquires the checkout lock. Under both locks the
    record and the snapshot directory must still be the hot names; if a mover
    has already moved them, this returns without writing a hot record back.
    One record's ``OSError`` is that record's error; it does not abort the sweep.
    """
    try:
        with (
            delegate.worktree_lock(_record_lock_target(observed, logical_record), timeout_s=DEFAULT_LOCK_TIMEOUT_S),
            _task_record_lock(parent_fd, record_name),
        ):
            if not _is_regular(parent_fd, record_name):
                return None
            snap_fd = _open_dir(parent_fd, snapshot_name)
            if snap_fd is None or not _hot_pair(parent_fd, record_name, snapshot_name, snap_fd):
                if snap_fd is not None:
                    os.close(snap_fd)
                return None
            try:
                current = _read_record_at(parent_fd, record_name)
                info = _lstat_at(parent_fd, record_name)
                if current is None:
                    return None
                if current.get("status") != observed_status or current.get("run_nonce") != observed_nonce:
                    return None
                if not _eligible(current, info, min_age_days=min_age_days, now=now):
                    return None
                phases = _phase_snapshots(snap_fd)
                if phases is None:
                    return None
                pre, post = phases
                _write_bytes_at(snap_fd, delegate._READ_ONLY_SNAPSHOT_DIGEST_NAME, _digest_bytes(pre, post))
                if crash_after == "digest":
                    raise RuntimeError("crash after digest")
                if on_after_digest is not None:
                    on_after_digest()
                if not _hot_pair(parent_fd, record_name, snapshot_name, snap_fd):
                    return None
                current["read_only_snapshot_retention"] = delegate._READ_ONLY_SNAPSHOT_RETENTION_DIGEST
                _write_bytes_at(
                    parent_fd,
                    record_name,
                    json.dumps(current, indent=2, default=str).encode("utf-8"),
                )
                if crash_after == "record":
                    raise RuntimeError("crash after record")
                for phase in _PHASES:
                    _unlink_regular_at(snap_fd, f"read_only_checkout_{phase}.json")
                return {"action": "digested"}
            finally:
                os.close(snap_fd)
    except WorktreeLockError:
        return None
    except OSError as exc:
        return {"action": "error", "error": errno.errorcode.get(exc.errno or 0, "OSError")}


def _measure_candidate(
    parent_fd: int,
    rel_dir: str,
    snapshot_name: str,
    *,
    root: Path,
    min_age_days: float,
    now: datetime,
    apply: bool,
    on_before_lock: Callable[[], None] | None,
    on_after_digest: Callable[[], None] | None,
    crash_after: str | None,
) -> tuple[dict[str, Any], int] | None:
    record_name = _record_name_for(snapshot_name)
    if record_name is None:
        return None
    info = _lstat_at(parent_fd, record_name)
    record = _read_record_at(parent_fd, record_name)
    if not _eligible(record, info, min_age_days=min_age_days, now=now) or record is None:
        return None
    snap_fd = _open_dir(parent_fd, snapshot_name)
    if snap_fd is None:
        return None
    try:
        phases = _phase_snapshots(snap_fd)
        if phases is None:
            return None
        pre, post = phases
        digest_raw = _digest_bytes(pre, post)
        before = sum(_file_bytes_at(snap_fd, f"read_only_checkout_{phase}.json") for phase in _PHASES)
    finally:
        os.close(snap_fd)
    reclaimed = before - len(digest_raw)
    row = {
        "snapshot_dir": f"{rel_dir}/{snapshot_name}",
        "task_id": record.get("task_id") if record else record_name[: -len(".json")],
        "status": record.get("status") if record else None,
        "reclaimable_bytes": reclaimed,
        "action": "would_digest",
    }
    if apply:
        if on_before_lock is not None:
            on_before_lock()
        outcome = _apply_one(
            parent_fd,
            snapshot_name,
            record_name,
            Path(os.path.abspath(os.path.join(os.fspath(root), rel_dir, record_name))),
            record,
            observed_status=record.get("status"),
            observed_nonce=record.get("run_nonce"),
            min_age_days=min_age_days,
            now=now,
            crash_after=crash_after,
            on_after_digest=on_after_digest,
        )
        if outcome is None:
            return None
        row["action"] = outcome["action"]
        if outcome["action"] == "error":
            row["error"] = outcome["error"]
            return row, 0
    return row, reclaimed


def plan_retention(
    batch_state: Path,
    *,
    min_age_days: float = DEFAULT_MIN_AGE_DAYS,
    apply: bool = False,
    now: datetime | None = None,
    on_before_lock: Callable[[], None] | None = None,
    on_after_digest: Callable[[], None] | None = None,
    crash_after: str | None = None,
) -> dict[str, Any]:
    """Measure every batch_state subtree. Rewrite only eligible snapshot sidecars.

    ``batch_state`` must be a directory named ``batch_state``. A symlink at any
    level is ignored: every open, stat, write, and unlink below that directory
    uses a descriptor opened with ``O_NOFOLLOW``. Non-terminal tasks and
    snapshot dirs without an explicit clean verdict are left as they are.
    """
    root_fd = _open_root(batch_state)
    try:
        return _plan_open(
            batch_state,
            root_fd,
            min_age_days=min_age_days,
            apply=apply,
            now=now or datetime.now(UTC),
            on_before_lock=on_before_lock,
            on_after_digest=on_after_digest,
            crash_after=crash_after,
        )
    finally:
        os.close(root_fd)


def _plan_open(
    batch_state: Path,
    root_fd: int,
    *,
    min_age_days: float,
    apply: bool,
    now: datetime,
    on_before_lock: Callable[[], None] | None,
    on_after_digest: Callable[[], None] | None,
    crash_after: str | None,
) -> dict[str, Any]:
    reclaimable_by_top: dict[str, int] = {}
    selected: list[dict[str, Any]] = []
    temps_removed: list[dict[str, str]] = []
    temps_would_remove: list[dict[str, str]] = []
    tasks_fd = _open_dir(root_fd, "tasks")
    if tasks_fd is not None:
        try:
            parents = [("tasks", tasks_fd)]
            archive_fd = _open_dir(tasks_fd, ARCHIVE_DIR_NAME)
            if archive_fd is not None:
                parents.append((f"tasks/{ARCHIVE_DIR_NAME}", archive_fd))
            try:
                for rel_dir, parent_fd in parents:
                    _collect_own_temps(temps_removed, temps_would_remove, parent_fd, rel_dir, now=now, apply=apply)
                    for snapshot_name in _names(parent_fd):
                        info = _lstat_at(parent_fd, snapshot_name)
                        if (
                            info is None
                            or not snapshot_name.endswith(_SNAPSHOT_SUFFIX)
                            or not stat.S_ISDIR(info.st_mode)
                        ):
                            continue
                        snap_fd = _open_dir(parent_fd, snapshot_name)
                        if snap_fd is not None:
                            try:
                                _collect_own_temps(
                                    temps_removed,
                                    temps_would_remove,
                                    snap_fd,
                                    f"{rel_dir}/{snapshot_name}",
                                    now=now,
                                    apply=apply,
                                )
                            finally:
                                os.close(snap_fd)
                        measured = _measure_candidate(
                            parent_fd,
                            rel_dir,
                            snapshot_name,
                            root=batch_state,
                            min_age_days=min_age_days,
                            now=now,
                            apply=apply,
                            on_before_lock=on_before_lock,
                            on_after_digest=on_after_digest,
                            crash_after=crash_after,
                        )
                        if measured is None:
                            continue
                        row, reclaimed = measured
                        selected.append(row)
                        reclaimable_by_top["tasks"] = reclaimable_by_top.get("tasks", 0) + reclaimed
            finally:
                if archive_fd is not None:
                    os.close(archive_fd)
        finally:
            os.close(tasks_fd)

    subtrees: list[dict[str, Any]] = []
    for name in _names(root_fd):
        info = _lstat_at(root_fd, name)
        if info is None or stat.S_ISLNK(info.st_mode):
            continue
        if stat.S_ISREG(info.st_mode):
            nbytes = info.st_size
        elif stat.S_ISDIR(info.st_mode):
            child = _open_dir(root_fd, name)
            if child is None:
                continue
            try:
                nbytes = _tree_bytes_at(child)
            finally:
                os.close(child)
        else:
            continue
        subtrees.append(
            {
                "name": name,
                "bytes": nbytes,
                "reclaimable_bytes": reclaimable_by_top.get(name, 0),
            }
        )
    return {
        "mode": "apply" if apply else "dry-run",
        "batch_state": str(batch_state),
        "min_age_days": min_age_days,
        "allowlist": [
            "tasks/*.snapshots",
            "tasks/archive/*.snapshots",
        ],
        "subtrees": subtrees,
        "totals": {
            "bytes": sum(row["bytes"] for row in subtrees),
            "reclaimable_bytes": sum(row["reclaimable_bytes"] for row in subtrees),
        },
        "selected": selected,
        "temps_removed": temps_removed,
        "temps_would_remove": temps_would_remove,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Report batch_state size and replace explicitly clean terminal snapshot sidecars with a digest.\n"
            "Use it from the scheduled hygiene run; do not use it to delete any other batch_state subtree."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/maintenance/batch_state_retention.py\n"
            "  .venv/bin/python scripts/maintenance/batch_state_retention.py \\\n"
            "      --min-age-days 0 --apply\n"
            "\n"
            "Outputs:\n"
            "  JSON on stdout: per-subtree bytes, reclaimable bytes, and selected snapshot dirs.\n"
            "  With --apply, eligible tasks/*.snapshots and tasks/archive/*.snapshots dirs lose\n"
            "  read_only_checkout_{pre,post}.json and gain digest.json. The task record's\n"
            '  read_only_snapshot_retention field becomes "digest".\n'
            "\n"
            "Exit codes:\n"
            "  0  report written (dry-run or apply)\n"
            "  2  the path is not a directory named batch_state\n"
            "\n"
            "Related:\n"
            "  scripts/delegate.py read-only snapshot sidecars (#7203, #8783)\n"
            "  scripts/orchestration/stale_task_records.py archive (moves sidecars, does not shrink them)\n"
        ),
    )
    parser.add_argument(
        "--batch-state",
        type=Path,
        default=DEFAULT_BATCH_STATE,
        help=(
            "Directory named batch_state to measure. Default: <repo>/batch_state. "
            "The sweep refuses any other directory name."
        ),
    )
    parser.add_argument(
        "--min-age-days",
        type=float,
        default=DEFAULT_MIN_AGE_DAYS,
        help=(
            "Only digest snapshot dirs whose task record is at least this many days old "
            f"(finished_at, else file mtime). Default: {DEFAULT_MIN_AGE_DAYS:g}. "
            "A clean verdict is already on the task record, so the full JSON has no "
            "forensic value after a day; 7 reclaimed nothing because these dirs are "
            "younger than a week. Example: 0"
        ),
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Rewrite eligible sidecars. Default is dry-run: report reclaimable bytes and change nothing.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        report = plan_retention(
            args.batch_state,
            min_age_days=args.min_age_days,
            apply=args.apply,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
