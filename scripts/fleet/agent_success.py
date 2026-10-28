"""Metadata-only agent/model dispatch-v2 rollup CLI (#10468)."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from scripts.common.task_store_paths import tasks_dir
from scripts.fleet_comms.agent_success_metrics import collect_agent_success
from scripts.fleet_comms.efficiency_metrics import _parse_timestamp


def _instant(value: str) -> datetime:
    parsed = _parse_timestamp(value)
    if parsed is None:
        raise argparse.ArgumentTypeError("expected an ISO-8601 date or timestamp")
    return parsed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Report dispatch-v2 success, failure and delivery metrics by agent and concrete model.\n"
        "Use for metadata comparisons; missing evidence stays unknown. Do not use to infer routing quality from unequal task mixes.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
        "  .venv/bin/python -m scripts.fleet.agent_success\n"
        "  .venv/bin/python -m scripts.fleet.agent_success --window 14d --json\n"
        "  .venv/bin/python -m scripts.fleet.agent_success --since 2026-10-25 --until 2026-10-28\n"
        "Outputs: stdout only; hot and archived task records and final review results are read-only. No network calls.\n"
        "Exit codes: 0 complete cohort; 1 unavailable/partial ledger; 2 invalid arguments.\n"
        "Related: #10468; docs/dev/agent-success-metrics.md; scripts.fleet_comms.efficiency_metrics.",
    )
    parser.add_argument(
        "--tasks-dir",
        type=Path,
        default=None,
        help="Task ledger directory (default: LU_TASKS_DIR or primary batch_state/tasks; archive included)",
    )
    parser.add_argument(
        "--window",
        choices=("24h", "3d", "14d"),
        default="3d",
        help="Lookback ending at --until (default: 3d); --since overrides this duration",
    )
    parser.add_argument(
        "--since", type=_instant, help="Inclusive UTC start, e.g. 2026-10-25 (default: --until minus --window)"
    )
    parser.add_argument(
        "--until", type=_instant, help="Exclusive UTC end, e.g. 2026-10-28T00:00:00Z (default: current UTC time)"
    )
    parser.add_argument(
        "--json", action="store_true", help="Print full JSON metrics (default: text summary plus full metrics JSON)"
    )
    args = parser.parse_args(argv)
    until = args.until or datetime.now(UTC)
    since = args.since or until - timedelta(days={"24h": 1, "3d": 3, "14d": 14}[args.window])
    if since >= until:
        parser.error("--since must precede --until")
    payload = collect_agent_success(tasks_dir=args.tasks_dir or tasks_dir(), since=since, until=until)
    if not args.json:
        print(f"Dispatch v2: {payload['tasks']} tasks; started_at in [{since.isoformat()}, {until.isoformat()})")
        print("Group | Tasks | Done/all | Done/terminal | Failed | Timeout | No deliverable")
        for dimension in ("by_agent", "by_model"):
            print(dimension)
            for name, row in payload[dimension].items():
                state = row["status"]
                print(
                    f"{name} | {row['tasks']} | {row['success']['percent']}% | {row['terminal_success']['percent']}%"
                    f" | {state['failed']} | {state['timeout']} | {state['no_deliverable']}"
                )
        print("Full metrics follow. Values aggregate observed records only; unknown counts expose missing evidence.")
    print(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False))
    return 0 if payload["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
