#!/usr/bin/env python3
"""Tally failed AGY and Gemini dispatches by cause.

Read-only count of ``batch_state/tasks/*.json`` records whose agent is ``agy``
or ``gemini``, whose status is ``failed``, and whose ``started_at`` is on or
after ``--since``. Dry-run records are excluded. Use it to recount provider
and harness failures, including a before/after split. Do not use it to retry,
reroute, edit task records, or decide a route.

Cause is taken from ``last_error``, ``failure_code``, ``stderr_excerpt``, and
``returncode_reason``. The shared anchored provider parser owns status codes;
quoted cancellation/status tokens are message text. CAUSE_PRECEDENCE below is
the sole precedence table. Unknown and permanent diagnostics are never transient.

Examples:
    .venv/bin/python -m scripts.fleet.agy_failure_tally --since 2026-09-25
    .venv/bin/python -m scripts.fleet.agy_failure_tally --since 2026-09-25 --before-after 2026-10-06
    .venv/bin/python -m scripts.fleet.agy_failure_tally --since 2026-09-25 --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.agent_runtime.adapters.agy import parse_agy_provider_fault
from scripts.common.task_store_paths import tasks_dir as default_tasks_dir

CAUSE_LABELS: tuple[str, ...] = (
    "cancellation",
    "unconfirmed",
    "permission denied",
    "read-only checkout mutation",
    "worktree preparation",
    "output token cutoff",
    "transient provider fault",
    "other",
)

# First matching cause wins. Transient headers outrank quoted cancellation
# tokens; cancellation/unconfirmed require an anchored structured reason line.
CAUSE_PRECEDENCE: tuple[tuple[str, str | None], ...] = (
    ("transient provider fault", None),
    ("cancellation", r"^agy_background_task_canceled(?:$|[\s:])"),
    ("unconfirmed", r"^agy_background_task_unconfirmed(?:$|[\s:])"),
    ("permission denied", r"^(?:agy_headless_permission_denied|permission[_ ]denied)(?:$|[\s:])"),
    ("read-only checkout mutation", r"read-only checkout mutation|read_only_checkout_mutation"),
    ("worktree preparation", r"worktree preparation|worktree_preparation"),
    ("output token cutoff", r"output token limit|cut off because it exceeded|output_token_limit"),
    ("other", None),
)

_TEXT_FIELDS = ("last_error", "failure_code", "stderr_excerpt", "returncode_reason")
_AGENTS = frozenset({"agy", "gemini"})


def classify_failure(record: Mapping[str, Any]) -> str:
    """Return one cause, using only diagnostic fields and the shared grammar."""
    text = "\n".join(value for key in _TEXT_FIELDS if isinstance(value := record.get(key), str))
    fault = parse_agy_provider_fault(text)
    for label, pattern in CAUSE_PRECEDENCE:
        if label == "transient provider fault":
            if fault is not None and fault.transient:
                return label
        elif (label == "permission denied" and fault is not None and fault.status == "PERMISSION_DENIED") or (
            pattern is not None and re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        ):
            return label
    return "other"


def _parse_instant(value: str) -> datetime:
    text = value.strip()
    if not text:
        raise ValueError("empty timestamp")
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _parse_bound(value: str) -> datetime:
    """Accept a calendar date as UTC midnight, or a full timestamp."""
    text = value.strip()
    if len(text) == 10:
        return _parse_instant(text + "T00:00:00+00:00")
    return _parse_instant(text)


def _started_at(record: Mapping[str, Any]) -> datetime | None:
    raw = record.get("started_at")
    if not isinstance(raw, str):
        return None
    try:
        return _parse_instant(raw)
    except ValueError:
        return None


def _is_dry_run(record: Mapping[str, Any]) -> bool:
    if record.get("status") == "dry_run" or record.get("dry_run") is True:
        return True
    return record.get("launch_mode") == "dry_run"


def load_task_records(tasks_dir: Path) -> tuple[list[dict[str, Any]], int]:
    """Read top-level task JSON. The second value is the unreadable-file count."""
    if not tasks_dir.is_dir():
        raise FileNotFoundError(f"tasks directory not found: {tasks_dir}")
    records: list[dict[str, Any]] = []
    skipped = 0
    for path in sorted(tasks_dir.glob("*.json")):
        if not path.is_file():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            skipped += 1
            continue
        if isinstance(payload, dict):
            records.append(payload)
        else:
            skipped += 1
    return records, skipped


def _eligible(record: Mapping[str, Any]) -> bool:
    return record.get("agent") in _AGENTS and record.get("status") == "failed" and not _is_dry_run(record)


def tally(
    records: list[Mapping[str, Any]],
    *,
    since: datetime,
    before_after: datetime | None = None,
    skipped_unreadable: int = 0,
) -> dict[str, Any]:
    """Count eligible failures in ``since`` and, optionally, split at ``before_after``."""
    skipped_undated = 0
    selected: list[tuple[datetime, str]] = []
    for record in records:
        if not _eligible(record):
            continue
        started = _started_at(record)
        if started is None:
            skipped_undated += 1
            continue
        if started < since:
            continue
        selected.append((started, classify_failure(record)))

    def counts_for(rows: list[tuple[datetime, str]]) -> dict[str, int]:
        found = Counter(cause for _started, cause in rows)
        return {label: int(found[label]) for label in CAUSE_LABELS}

    report: dict[str, Any] = {
        "since": since.isoformat(),
        "tasks": len(selected),
        "counts": counts_for(selected),
        "skipped_unreadable": skipped_unreadable,
        "skipped_undated": skipped_undated,
    }
    if before_after is None:
        report["before_after"] = None
        return report
    before_rows = [(started, cause) for started, cause in selected if started < before_after]
    after_rows = [(started, cause) for started, cause in selected if started >= before_after]
    report["before_after"] = before_after.isoformat()
    report["before"] = {"tasks": len(before_rows), "counts": counts_for(before_rows)}
    report["after"] = {"tasks": len(after_rows), "counts": counts_for(after_rows)}
    return report


def format_report(report: dict[str, Any]) -> str:
    """Plain-text counts. No task paths or excerpts."""
    lines = [f"since: {report['since']}", f"tasks: {report['tasks']}"]
    if report.get("before_after"):
        lines.append(f"before_after: {report['before_after']}")
        for name in ("before", "after"):
            block = report[name]
            lines.append(f"{name}:")
            lines.append(f"  tasks: {block['tasks']}")
            for label in CAUSE_LABELS:
                lines.append(f"  {label}: {block['counts'][label]}")
    else:
        for label in CAUSE_LABELS:
            lines.append(f"{label}: {report['counts'][label]}")
    if report["skipped_unreadable"] or report["skipped_undated"]:
        lines.append(f"skipped_unreadable: {report['skipped_unreadable']}")
        lines.append(f"skipped_undated: {report['skipped_undated']}")
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Count failed AGY and Gemini task records by cause.\n"
            "Use after a date to recount provider and harness failures. "
            "Do not use it to retry a dispatch or edit task records."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        allow_abbrev=False,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.fleet.agy_failure_tally --since 2026-09-25\n"
            "  .venv/bin/python -m scripts.fleet.agy_failure_tally --since 2026-09-25 "
            "--before-after 2026-10-06\n"
            "  .venv/bin/python -m scripts.fleet.agy_failure_tally --since 2026-09-25 --json\n"
            "\n"
            "Outputs: cause counts on stdout. --json prints one JSON object. "
            "Nothing is written or deleted.\n"
            "Exit codes: 0 counts printed; 2 invalid arguments or missing tasks directory.\n"
            "Related: scripts/agent_runtime/adapters/agy.py transient retry; issue #10206.\n"
        ),
    )
    parser.add_argument(
        "--since",
        required=True,
        help="Include records with started_at on or after this UTC date or timestamp. Example: 2026-09-25.",
    )
    parser.add_argument(
        "--before-after",
        default=None,
        help=(
            "Split the --since window at this UTC date or timestamp. "
            "Before is started_at < DATE; after is started_at >= DATE. Default: no split."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print one JSON object instead of plain text. Default: plain text.",
    )
    parser.add_argument(
        "--tasks-dir",
        type=Path,
        default=None,
        help="Task JSON directory. Default: the primary checkout batch_state/tasks. Example: batch_state/tasks.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        since = _parse_bound(args.since)
        before_after = _parse_bound(args.before_after) if args.before_after else None
    except ValueError:
        print("Refused: --since and --before-after must be YYYY-MM-DD or an ISO-8601 timestamp.", file=sys.stderr)
        return 2
    tasks_dir = args.tasks_dir if args.tasks_dir is not None else default_tasks_dir()
    try:
        records, skipped_unreadable = load_task_records(tasks_dir)
    except FileNotFoundError:
        print("Refused: tasks directory not found.", file=sys.stderr)
        return 2
    report = tally(records, since=since, before_after=before_after, skipped_unreadable=skipped_unreadable)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_report(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
