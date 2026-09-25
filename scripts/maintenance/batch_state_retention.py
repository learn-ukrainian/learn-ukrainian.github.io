#!/usr/bin/env python3
"""Shrink clean read-only snapshot sidecars under batch_state, and report the rest.

Use this to turn old terminal ``tasks/*.snapshots/`` directories that recorded no
checkout mutation into a ``digest.json``. Do not use it to delete manifests,
atlas output, open-model data, or any other batch_state subtree: those are
reported and left untouched. Dry-run is the default; pass ``--apply`` to write.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
for _path in (REPO_ROOT, SCRIPTS_DIR):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from scripts import delegate
from scripts.orchestration.stale_task_records import _record_age_days
from scripts.orchestration.task_record_store import ARCHIVE_DIR_NAME
from scripts.orchestration.worktree_claims import RELEASED_TASK_STATUSES

DEFAULT_BATCH_STATE = REPO_ROOT / "batch_state"
DEFAULT_MIN_AGE_DAYS = 7.0
_SNAPSHOT_SUFFIX = delegate._READ_ONLY_CHECKOUT_SNAPSHOT_SUFFIX
# Only these directory globs may be rewritten. Everything else under batch_state
# is measured and left alone.
_ALLOWLISTED_SNAPSHOT_PARENTS = ("", ARCHIVE_DIR_NAME)


def _inside(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        return False
    return True


def _file_bytes(path: Path) -> int:
    if path.is_symlink() or not path.is_file():
        return 0
    try:
        return path.stat().st_size
    except OSError:
        return 0


def _tree_bytes(path: Path) -> int:
    if path.is_symlink():
        return 0
    if path.is_file():
        return _file_bytes(path)
    total = 0
    try:
        children = path.rglob("*")
    except OSError:
        return 0
    for child in children:
        total += _file_bytes(child)
    return total


def _phase_snapshots(snapshot_dir: Path) -> tuple[dict[str, str], dict[str, str]] | None:
    """Return parsed phase maps, or None when a file is missing or not a JSON object."""
    loaded: list[dict[str, str]] = []
    for phase in ("pre", "post"):
        path = snapshot_dir / f"read_only_checkout_{phase}.json"
        if not path.is_file():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if not isinstance(payload, dict):
            return None
        loaded.append(payload)
    return loaded[0], loaded[1]


def _eligible(
    record: dict[str, Any] | None,
    record_path: Path,
    *,
    min_age_days: float,
    now: datetime,
) -> bool:
    if record is None or record.get("status") not in RELEASED_TASK_STATUSES:
        return False
    try:
        mtime_ns = record_path.stat().st_mtime_ns
    except OSError:
        return False
    if _record_age_days(record, mtime_ns, now) < min_age_days:
        return False
    mutations = record.get("read_only_mutation_paths")
    if isinstance(mutations, list) and mutations:
        return False
    if not isinstance(mutations, list) and mutations is not None:
        return False
    return record.get("read_only_checkout_snapshot_error") is None


def _snapshot_candidates(tasks_dir: Path) -> list[Path]:
    found: list[Path] = []
    for parent_name in _ALLOWLISTED_SNAPSHOT_PARENTS:
        parent = tasks_dir / parent_name if parent_name else tasks_dir
        if not parent.is_dir() or parent.is_symlink():
            continue
        try:
            children = sorted(parent.glob(f"*{_SNAPSHOT_SUFFIX}"))
        except OSError:
            continue
        for path in children:
            if path.is_dir() and not path.is_symlink() and path.name.endswith(_SNAPSHOT_SUFFIX):
                found.append(path)
    return found


def _record_for_snapshot(snapshot_dir: Path) -> Path:
    stem = snapshot_dir.name[: -len(_SNAPSHOT_SUFFIX)]
    return snapshot_dir.with_name(f"{stem}.json")


def plan_retention(
    batch_state: Path,
    *,
    min_age_days: float = DEFAULT_MIN_AGE_DAYS,
    apply: bool = False,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Measure every batch_state subtree. Rewrite only eligible snapshot sidecars.

    ``batch_state`` must be a directory named ``batch_state``. Paths that resolve
    outside it are ignored. Non-terminal tasks and snapshot dirs with a recorded
    mutation or snapshot error are left as they are.
    """
    root = batch_state.resolve()
    if root.name != "batch_state" or not root.is_dir():
        raise ValueError(f"refusing to sweep {batch_state}: path must be a directory named batch_state")
    now = now or datetime.now(UTC)
    tasks_dir = root / "tasks"
    reclaimable_by_top: dict[str, int] = {}
    selected: list[dict[str, Any]] = []

    if tasks_dir.is_dir() and _inside(root, tasks_dir):
        for snapshot_dir in _snapshot_candidates(tasks_dir):
            if not _inside(root, snapshot_dir):
                continue
            record_path = _record_for_snapshot(snapshot_dir)
            record = delegate._read_state_json(record_path) if record_path.is_file() else None
            if not _eligible(record, record_path, min_age_days=min_age_days, now=now):
                continue
            phases = _phase_snapshots(snapshot_dir)
            if phases is None:
                continue
            pre, post = phases
            digest_raw = json.dumps(
                delegate.read_only_snapshot_digest(pre, post),
                separators=(",", ":"),
            ).encode("utf-8")
            before = sum(
                _file_bytes(snapshot_dir / f"read_only_checkout_{phase}.json") for phase in ("pre", "post")
            )
            reclaimed = before - len(digest_raw)
            row = {
                "snapshot_dir": str(snapshot_dir.relative_to(root)),
                "task_id": record.get("task_id") if record else record_path.stem,
                "status": record.get("status") if record else None,
                "reclaimable_bytes": reclaimed,
                "action": "would_digest",
            }
            if apply:
                delegate.collapse_read_only_snapshot_dir(snapshot_dir, pre, post)
                if record is not None:
                    record["read_only_snapshot_retention"] = delegate._READ_ONLY_SNAPSHOT_RETENTION_DIGEST
                    delegate._write_state_atomic(record_path, record)
                row["action"] = "digested"
            selected.append(row)
            top = "tasks"
            reclaimable_by_top[top] = reclaimable_by_top.get(top, 0) + reclaimed

    subtrees: list[dict[str, Any]] = []
    try:
        entries = sorted(root.iterdir(), key=lambda path: path.name)
    except OSError:
        entries = []
    for entry in entries:
        if entry.is_symlink() or not _inside(root, entry):
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
            "Report batch_state size and replace clean terminal read-only snapshot\n"
            "sidecars with a digest. Dry-run unless --apply is passed. Never deletes\n"
            "an unknown subtree, a non-terminal task, or anything outside batch_state."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  /home/ops/learn-ukrainian/.venv/bin/python scripts/maintenance/batch_state_retention.py\n"
            "  /home/ops/learn-ukrainian/.venv/bin/python scripts/maintenance/batch_state_retention.py \\\n"
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
            f"(finished_at, else file mtime). Default: {DEFAULT_MIN_AGE_DAYS:g}. Example: 0"
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
