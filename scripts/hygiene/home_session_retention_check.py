#!/usr/bin/env python3
"""Check the #4956 home-session retention policy without mutating any files.

The policy boundary is 14 days: every allowlisted session file at or beyond
that age must be archived before local deletion. The checker deliberately does
not accept ``--apply`` and never reads ``LU_HOME_SESSION_APPLY``; it is a
scheduled observation and warning surface, not a second reaper.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.hygiene import inventory_home_sessions

SCHEMA_VERSION = "home-session-retention-check.v1"


def build_report(*, retention_days: float = inventory_home_sessions.DEFAULT_RETENTION_DAYS) -> dict[str, Any]:
    """Measure allowlisted session stores and flag stale or unmeasurable lanes."""
    roots, candidates = inventory_home_sessions.inventory_home_sessions(
        retention_days=retention_days
    )
    candidates_by_provider: dict[str, list[inventory_home_sessions.SessionCandidate]] = defaultdict(list)
    for candidate in candidates:
        candidates_by_provider[candidate.provider].append(candidate)

    lanes: list[dict[str, Any]] = []
    violations: list[dict[str, Any]] = []
    for root in roots:
        stale = candidates_by_provider[root.provider]
        stale_bytes = sum(candidate.size_bytes for candidate in stale)
        lane = {
            "provider": root.provider,
            "exists": root.exists,
            "session_files": root.session_files,
            "root_bytes": root.size_bytes,
            "stale_files": len(stale),
            "stale_bytes": stale_bytes,
            "skipped_reason": root.skipped_reason,
        }
        lanes.append(lane)
        if root.exists and root.size_bytes is None:
            violations.append(
                {
                    "provider": root.provider,
                    "kind": "unmeasurable_root",
                    "detail": root.skipped_reason or "provider root size could not be measured",
                }
            )
        if stale:
            violations.append(
                {
                    "provider": root.provider,
                    "kind": "stale_sessions",
                    "stale_files": len(stale),
                    "stale_bytes": stale_bytes,
                }
            )

    return {
        "schema": SCHEMA_VERSION,
        "mode": "read_only",
        "policy": {
            "retention_days": retention_days,
            "max_stale_files": 0,
            "max_stale_bytes": 0,
        },
        "lanes": lanes,
        "summary": {
            "lanes": len(lanes),
            "session_files": sum(lane["session_files"] for lane in lanes),
            "root_bytes": sum(lane["root_bytes"] or 0 for lane in lanes),
            "stale_files": sum(lane["stale_files"] for lane in lanes),
            "stale_bytes": sum(lane["stale_bytes"] for lane in lanes),
            "violations": len(violations),
        },
        "violations": violations,
    }


def warning_lines(report: dict[str, Any]) -> list[str]:
    """Return actionable warnings for a failed policy observation."""
    retention_days = report["policy"]["retention_days"]
    lines: list[str] = []
    for violation in report["violations"]:
        provider = violation["provider"]
        if violation["kind"] == "stale_sessions":
            lines.append(
                "HARD WARNING: "
                f"{provider} has {violation['stale_files']} allowlisted session file(s) "
                f"({violation['stale_bytes']} bytes) at least {retention_days:g} days old; "
                "archive them before any local deletion."
            )
        else:
            lines.append(
                "HARD WARNING: "
                f"cannot verify {provider} home-session retention: {violation['detail']}."
            )
    return lines


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--retention-days",
        type=float,
        default=inventory_home_sessions.DEFAULT_RETENTION_DAYS,
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.retention_days < 0:
        raise SystemExit("--retention-days must be non-negative")
    report = build_report(retention_days=args.retention_days)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(
            "Home-session retention check "
            f"(read-only; stale >= {args.retention_days:g} days)"
        )
        for lane in report["lanes"]:
            root_bytes = "unknown" if lane["root_bytes"] is None else lane["root_bytes"]
            print(
                f"  {lane['provider']}: sessions={lane['session_files']} root_bytes={root_bytes} "
                f"stale_files={lane['stale_files']} stale_bytes={lane['stale_bytes']}"
            )
    for line in warning_lines(report):
        print(line, file=sys.stderr)
    return 1 if report["violations"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
