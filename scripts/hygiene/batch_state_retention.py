"""Report stale top-level batch_state directories; never deletes anything (#9737).

A directory is stale when nothing below it was written for ``stale_days``.
Live machinery (``tasks/``, ``preserved/``, ``reports/``, ``branch-archive/``)
is excluded, and paths listed in ``batch_state_retention.json`` are reported
as held evidence instead of stale candidates. Sizing and digesting of task
snapshot sidecars stays with ``scripts.maintenance.batch_state_retention``
(#8783); this module only answers "what has gone untouched".
"""

from __future__ import annotations

import argparse
import json
import math
import stat
import time
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from scripts.common.repo_root import resolve_repo_root
from scripts.common.task_scratch import mount_points

SCHEMA = "batch-state-retention.v1"
EXCLUDED = frozenset({"tasks", "preserved", "reports", "branch-archive"})
RETENTION_LIST = Path(__file__).with_name("batch_state_retention.json")


class RetentionListError(ValueError):
    """The evidence-retention list is malformed; holds must never be ignored silently."""


def default_batch_root() -> Path:
    """The primary checkout's shared batch_state directory."""
    return resolve_repo_root(Path(__file__), 2) / "batch_state"


def load_holds(path: Path) -> list[dict[str, Any]]:
    """Read and validate held paths; every entry names a repo-relative batch_state path."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise RetentionListError(f"unreadable retention list: {error}") from error
    if not isinstance(data, dict) or data.get("schema") != SCHEMA or not isinstance(data.get("holds"), list):
        raise RetentionListError(f"retention list must be a {SCHEMA} object with a holds list")
    holds = []
    for entry in data["holds"]:
        if not isinstance(entry, dict) or not all(isinstance(entry.get(key), str) for key in ("path", "reason")):
            raise RetentionListError("each hold needs string path and reason fields")
        parts = PurePosixPath(entry["path"]).parts
        if len(parts) < 2 or parts[0] != "batch_state" or any(part in {"..", "."} for part in parts):
            raise RetentionListError(f"hold path must lie below batch_state/: {entry['path']!r}")
        holds.append({**entry, "parts": parts[1:]})
    return holds


def tree_activity(path: Path, cutoff: float) -> tuple[int, float, str | None]:
    """Allocated bytes and newest write below ``path``, never following links or mounts.

    The walk stops early once a write newer than ``cutoff`` proves the tree
    fresh, so the byte count is complete only for stale trees.
    """
    mounts = mount_points()
    if mounts is None:
        return 0, 0.0, "mount_probe_unknown"
    allocated = 0
    newest = 0.0
    reason = None
    seen = set()
    try:
        device = path.lstat().st_dev
        pending = [path]
        while pending:
            node = pending.pop()
            info = node.lstat()
            newest = max(newest, info.st_mtime)
            if newest >= cutoff:
                return allocated, newest, None
            if (info.st_dev, info.st_ino) not in seen:
                seen.add((info.st_dev, info.st_ino))
                allocated += info.st_blocks * 512
            if info.st_dev != device or str(node) in mounts:
                reason = reason or "mount_point"
                continue
            if stat.S_ISDIR(info.st_mode):
                pending.extend(node.iterdir())
    except OSError:
        return allocated, newest, "tree_unknown"
    return allocated, newest, reason


def report(
    batch_root: Path,
    *,
    holds: list[dict[str, Any]],
    stale_days: float = 7,
    now: float | None = None,
) -> dict[str, Any]:
    """Classify each top-level directory as excluded, held, fresh or stale."""
    if not math.isfinite(stale_days) or stale_days <= 0:
        raise ValueError("stale days must be finite and positive")
    if batch_root.is_symlink() or not batch_root.is_dir():
        raise ValueError("batch_state root must be a real directory")
    now = time.time() if now is None else now
    cutoff = now - stale_days * 86400
    counts = {"excluded": 0, "fresh": 0, "held": 0, "stale": 0, "unknown": 0}
    rows = []
    for path in sorted(batch_root.iterdir()):
        if path.is_symlink() or not path.is_dir():
            continue
        if path.name in EXCLUDED:
            counts["excluded"] += 1
            continue
        row: dict[str, Any] = {"path": f"batch_state/{path.name}/"}
        held = [hold for hold in holds if hold["parts"][0] == path.name]
        allocated, newest, reason = tree_activity(path, cutoff)
        if held:
            row.update(status="held", holds=[{k: v for k, v in h.items() if k != "parts"} for h in held])
        elif reason:
            row.update(status="unknown", reason=reason)
        elif newest >= cutoff:
            counts["fresh"] += 1
            continue
        else:
            row.update(status="stale")
        if row["status"] != "held" or newest < cutoff:
            row["bytes"] = allocated
        row["newest_write_utc"] = datetime.fromtimestamp(newest, UTC).strftime("%Y-%m-%d") if newest else None
        counts[row["status"]] += 1
        rows.append(row)
    return {
        "schema": "batch-state-staleness.v1",
        "stale_days": stale_days,
        "excluded_names": sorted(EXCLUDED),
        "counts": counts,
        "stale_bytes": sum(row["bytes"] for row in rows if row["status"] == "stale"),
        "rows": rows,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Report top-level batch_state directories with no write for N days, with size and newest write.\n"
            "Report only: it never deletes. Use it to pick cleanup candidates; hold evidence in the retention list."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.hygiene.batch_state_retention\n"
            "  .venv/bin/python -m scripts.hygiene.batch_state_retention --json --stale-days 14\n"
            "Outputs: stdout table (or --json); no files written, nothing deleted.\n"
            "Exit codes: 0 report complete; 1 some directories could not be scanned; "
            "2 invalid arguments or malformed retention list.\n"
            "Related: #9737; scripts/hygiene/batch_state_retention.json; docs/runbooks/tmp-retention.md."
        ),
    )
    parser.add_argument(
        "--batch-root",
        type=Path,
        help="batch_state directory to scan (default: the primary checkout's batch_state; example fixture/batch_state).",
    )
    parser.add_argument(
        "--retention-list",
        type=Path,
        default=RETENTION_LIST,
        help="Evidence-retention list (default scripts/hygiene/batch_state_retention.json).",
    )
    parser.add_argument(
        "--stale-days", type=float, default=7, help="Days without any write before a directory is stale (default 7)."
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON (default Markdown table).")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        holds = load_holds(args.retention_list)
        result = report(args.batch_root or default_batch_root(), holds=holds, stale_days=args.stale_days)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("| Directory | Status | Allocated bytes | Newest write (UTC) | Note |")
        print("|---|---|---:|---|---|")
        for row in result["rows"]:
            note = "; ".join(f"{h['reason']} until {h.get('until', 'released')}" for h in row.get("holds", []))
            print(
                f"| {row['path']} | {row['status']} | {row.get('bytes', '')} | {row['newest_write_utc']} "
                f"| {note or row.get('reason', '')} |"
            )
        counts = " ".join(f"{key}={value}" for key, value in result["counts"].items())
        print(f"stale_days={result['stale_days']} {counts} stale_bytes={result['stale_bytes']}")
    return 1 if result["counts"]["unknown"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
