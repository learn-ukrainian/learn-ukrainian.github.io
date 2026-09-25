#!/usr/bin/env python3
"""Shrink clean read-only snapshot sidecars under batch_state, and report the rest.

Use this to turn old terminal ``tasks/*.snapshots/`` directories that recorded an
explicit clean checkout into a ``digest.json``. Do not use it to delete manifests,
atlas output, open-model data, or any other batch_state subtree: those are
reported and left untouched. Dry-run is the default; pass ``--apply`` to write.
"""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
for _path in (REPO_ROOT, SCRIPTS_DIR):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from scripts import delegate
from scripts.orchestration.dead_worker_state import task_state_lock
from scripts.orchestration.stale_task_records import _record_age_days
from scripts.orchestration.task_record_store import ARCHIVE_DIR_NAME
from scripts.orchestration.worktree_claims import RELEASED_TASK_STATUSES

DEFAULT_BATCH_STATE = REPO_ROOT / "batch_state"
# A clean verdict already lives on the task record, so the full JSON has no
# forensic value after a day. Seven days reclaimed nothing: the dirs are younger.
DEFAULT_MIN_AGE_DAYS = 1.0
_SNAPSHOT_SUFFIX = delegate._READ_ONLY_CHECKOUT_SNAPSHOT_SUFFIX
# Only these directory globs may be rewritten. Everything else under batch_state
# is measured and left alone.
_ALLOWLISTED_SNAPSHOT_PARENTS = ("", ARCHIVE_DIR_NAME)
_PHASES = ("pre", "post")


def _root_dir(batch_state: Path) -> Path:
    """Return the real batch_state directory, refusing a symlink or any other name."""
    try:
        info = batch_state.lstat()
    except OSError as exc:
        raise ValueError(f"refusing to sweep {batch_state}: path must be a directory named batch_state") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode) or batch_state.name != "batch_state":
        raise ValueError(f"refusing to sweep {batch_state}: path must be a directory named batch_state")
    root = batch_state.resolve()
    if root.name != "batch_state":
        raise ValueError(f"refusing to sweep {batch_state}: path must be a directory named batch_state")
    return root


def _nofollow(root: Path, path: Path, *, allow_missing_leaf: bool = False) -> Path | None:
    """Return ``path`` when every component from ``root`` is a real, contained entry.

    ``lstat`` rejects a symlink at any level. The leaf may be absent when the
    caller is about to create it. ``..`` and paths outside ``root`` are refused.
    """
    try:
        relative = path.absolute().relative_to(root)
    except ValueError:
        return None
    if not relative.parts or any(part in {"", ".", ".."} for part in relative.parts):
        return None
    current = root
    for index, part in enumerate(relative.parts):
        current = current / part
        leaf = index == len(relative.parts) - 1
        try:
            info = current.lstat()
        except FileNotFoundError:
            if allow_missing_leaf and leaf:
                return current
            return None
        except OSError:
            return None
        if stat.S_ISLNK(info.st_mode):
            return None
    return current


def _read_regular(root: Path, path: Path) -> bytes | None:
    """Read a regular file with ``O_NOFOLLOW``, or return None if that is unsafe."""
    checked = _nofollow(root, path)
    if checked is None:
        return None
    try:
        info = checked.lstat()
    except OSError:
        return None
    if not stat.S_ISREG(info.st_mode):
        return None
    try:
        fd = os.open(checked, os.O_RDONLY | os.O_NOFOLLOW)
    except OSError:
        return None
    try:
        chunks: list[bytes] = []
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(fd)


def _write_bytes_nofollow(root: Path, path: Path, raw: bytes) -> None:
    """Create or replace ``path`` without following a symlink at any level."""
    checked = _nofollow(root, path, allow_missing_leaf=True)
    if checked is None:
        raise OSError(f"refusing to write {path}: symlink or path outside batch_state")
    parent = _nofollow(root, checked.parent)
    if parent is None:
        raise OSError(f"refusing to write {path}: symlink or path outside batch_state")
    tmp = parent / f".{checked.name}.tmp.{os.getpid()}"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        os.write(fd, raw)
    finally:
        os.close(fd)
    os.replace(tmp, checked)


def _unlink_regular(root: Path, path: Path) -> None:
    checked = _nofollow(root, path)
    if checked is None:
        return
    try:
        info = checked.lstat()
    except OSError:
        return
    if stat.S_ISREG(info.st_mode):
        checked.unlink()


def _file_bytes(path: Path) -> int:
    try:
        info = path.lstat()
    except OSError:
        return 0
    if not stat.S_ISREG(info.st_mode):
        return 0
    return info.st_size


def _tree_bytes(path: Path) -> int:
    try:
        info = path.lstat()
    except OSError:
        return 0
    if stat.S_ISLNK(info.st_mode):
        return 0
    if stat.S_ISREG(info.st_mode):
        return info.st_size
    total = 0
    try:
        children = path.rglob("*")
    except OSError:
        return 0
    for child in children:
        total += _file_bytes(child)
    return total


def _phase_snapshots(root: Path, snapshot_dir: Path) -> tuple[dict[str, str], dict[str, str]] | None:
    """Return parsed phase maps when both files are regular JSON objects under ``root``."""
    loaded: list[dict[str, str]] = []
    for phase in _PHASES:
        raw = _read_regular(root, snapshot_dir / f"read_only_checkout_{phase}.json")
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
    record_path: Path,
    *,
    min_age_days: float,
    now: datetime,
) -> bool:
    if record is None or record.get("status") not in RELEASED_TASK_STATUSES or not _explicit_clean(record):
        return False
    try:
        info = record_path.lstat()
    except OSError:
        return False
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        return False
    return _record_age_days(record, info.st_mtime_ns, now) >= min_age_days


def _read_record(root: Path, record_path: Path) -> dict[str, Any] | None:
    raw = _read_regular(root, record_path)
    if raw is None:
        return None
    try:
        loaded = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return loaded if isinstance(loaded, dict) else None


def _snapshot_candidates(root: Path, tasks_dir: Path) -> list[Path]:
    found: list[Path] = []
    for parent_name in _ALLOWLISTED_SNAPSHOT_PARENTS:
        parent = tasks_dir / parent_name if parent_name else tasks_dir
        if _nofollow(root, parent) is None:
            continue
        try:
            children = sorted(parent.glob(f"*{_SNAPSHOT_SUFFIX}"))
        except OSError:
            continue
        for path in children:
            if path.name.endswith(_SNAPSHOT_SUFFIX) and _nofollow(root, path) is not None:
                try:
                    info = path.lstat()
                except OSError:
                    continue
                if stat.S_ISDIR(info.st_mode):
                    found.append(path)
    return found


def _record_for_snapshot(snapshot_dir: Path) -> Path:
    stem = snapshot_dir.name[: -len(_SNAPSHOT_SUFFIX)]
    return snapshot_dir.with_name(f"{stem}.json")


def _digest_bytes(pre: dict[str, str], post: dict[str, str]) -> bytes:
    return json.dumps(delegate.read_only_snapshot_digest(pre, post), separators=(",", ":")).encode("utf-8")


def _apply_one(
    root: Path,
    snapshot_dir: Path,
    record_path: Path,
    *,
    observed_status: Any,
    observed_nonce: Any,
    min_age_days: float,
    now: datetime,
    crash_after: str | None,
) -> str | None:
    """Digest one sidecar under the task lock. Return the action, or None to skip.

    The lock is the same per-task lock delegate holds while it publishes the
    task record. Status and ``run_nonce`` are read again under that lock; a
    re-dispatch that changed either one keeps its new sidecars.
    """
    with task_state_lock(record_path):
        current = _read_record(root, record_path)
        if current is None:
            return None
        if current.get("status") != observed_status or current.get("run_nonce") != observed_nonce:
            return None
        if not _eligible(current, record_path, min_age_days=min_age_days, now=now):
            return None
        phases = _phase_snapshots(root, snapshot_dir)
        if phases is None:
            return None
        pre, post = phases
        digest_raw = _digest_bytes(pre, post)
        digest_path = snapshot_dir / delegate._READ_ONLY_SNAPSHOT_DIGEST_NAME
        _write_bytes_nofollow(root, digest_path, digest_raw)
        if crash_after == "digest":
            raise RuntimeError("crash after digest")
        current["read_only_snapshot_retention"] = delegate._READ_ONLY_SNAPSHOT_RETENTION_DIGEST
        _write_bytes_nofollow(
            root,
            record_path,
            json.dumps(current, indent=2, default=str).encode("utf-8"),
        )
        if crash_after == "record":
            raise RuntimeError("crash after record")
        for phase in _PHASES:
            _unlink_regular(root, snapshot_dir / f"read_only_checkout_{phase}.json")
        return "digested"


def plan_retention(
    batch_state: Path,
    *,
    min_age_days: float = DEFAULT_MIN_AGE_DAYS,
    apply: bool = False,
    now: datetime | None = None,
    on_before_lock: Callable[[], None] | None = None,
    crash_after: str | None = None,
) -> dict[str, Any]:
    """Measure every batch_state subtree. Rewrite only eligible snapshot sidecars.

    ``batch_state`` must be a directory named ``batch_state``. A symlink at any
    level, or a path that resolves outside it, is ignored. Non-terminal tasks
    and snapshot dirs without an explicit clean verdict are left as they are.
    """
    root = _root_dir(batch_state)
    now = now or datetime.now(UTC)
    tasks_dir = root / "tasks"
    reclaimable_by_top: dict[str, int] = {}
    selected: list[dict[str, Any]] = []

    if _nofollow(root, tasks_dir) is not None:
        for snapshot_dir in _snapshot_candidates(root, tasks_dir):
            record_path = _record_for_snapshot(snapshot_dir)
            if _nofollow(root, record_path) is None or _nofollow(root, snapshot_dir) is None:
                continue
            record = _read_record(root, record_path)
            if not _eligible(record, record_path, min_age_days=min_age_days, now=now):
                continue
            phases = _phase_snapshots(root, snapshot_dir)
            if phases is None or record is None:
                continue
            pre, post = phases
            digest_raw = _digest_bytes(pre, post)
            before = sum(_file_bytes(snapshot_dir / f"read_only_checkout_{phase}.json") for phase in _PHASES)
            reclaimed = before - len(digest_raw)
            row = {
                "snapshot_dir": str(snapshot_dir.relative_to(root)),
                "task_id": record.get("task_id") if record else record_path.stem,
                "status": record.get("status") if record else None,
                "reclaimable_bytes": reclaimed,
                "action": "would_digest",
            }
            if apply:
                if on_before_lock is not None:
                    on_before_lock()
                action = _apply_one(
                    root,
                    snapshot_dir,
                    record_path,
                    observed_status=record.get("status"),
                    observed_nonce=record.get("run_nonce"),
                    min_age_days=min_age_days,
                    now=now,
                    crash_after=crash_after,
                )
                if action is None:
                    continue
                row["action"] = action
            selected.append(row)
            reclaimable_by_top["tasks"] = reclaimable_by_top.get("tasks", 0) + reclaimed

    subtrees: list[dict[str, Any]] = []
    try:
        entries = sorted(root.iterdir(), key=lambda path: path.name)
    except OSError:
        entries = []
    for entry in entries:
        if _nofollow(root, entry) is None:
            continue
        subtrees.append(
            {
                "name": entry.name,
                "bytes": _tree_bytes(entry),
                "reclaimable_bytes": reclaimable_by_top.get(entry.name, 0),
            }
        )
    return {
        "mode": "apply" if apply else "dry-run",
        "batch_state": str(root),
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
            "  read_only_snapshot_retention field becomes \"digest\".\n"
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
