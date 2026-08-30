#!/usr/bin/env python3
"""Report epic-driver fleet breadth from batch_state/tasks (operator GO 2026-08-06).

See agents_extensions/shared/rules/fleet-driver-routing.md.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from scripts.fleet import idle_settle as idle_settle

ROOT = Path(__file__).resolve().parents[2]

# Static agent→tier fallback (not a live model_catalog.yaml load).
_DEFAULT_AGENT_TIER = {
    "claude": "practical",  # seat may host authority (Fable) — model_id refines below
    "codex": "practical",
    "cursor": "practical",
    "agy": "practical",
    "gemini": "practical",
    "grok": "practical",
    "kimi": "practical",
    "deepseek": "heap",
    "glm": "practical",
    "qwen": "heap",
}

# All model-id hints match delimiter-bounded segments (or multi-segment
# compounds like gpt-5.6-sol / claude-fable). Bare substring matching mis-tiers
# e.g. gemini-3.6-flash-high (flash) and gemini-* (mini inside gemini).
_AUTHORITY_TOKEN_RE = re.compile(
    r"(?:^|[-_.])(?:fable|sol|opus|claude-fable|claude-opus|gpt-5\.6-sol)(?:$|[-_.])"
)
_HEAP_TOKEN_RE = re.compile(
    r"(?:^|[-_.])(?:luna|haiku|flash|mini|laguna|k2\.5)(?:$|[-_.])"
)
_PRACTICAL_OVERRIDE_RE = re.compile(
    r"flash-high|gemini-3\.[0-9]+-flash-high|gpt-5\.6-terra|claude-sonnet",
)


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    # Task JSON may omit offsets; always compare as UTC-aware.
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


def _tier_for(agent: str | None, model: str | None) -> str:
    agent_l = (agent or "").strip().lower()
    model_l = (model or "").strip().lower()
    if _AUTHORITY_TOKEN_RE.search(model_l):
        return "authority"
    # Practical before heap: *-flash-high is frontier_practical, not heap Flash.
    if _PRACTICAL_OVERRIDE_RE.search(model_l):
        return "practical"
    if _HEAP_TOKEN_RE.search(model_l):
        return "heap"
    return _DEFAULT_AGENT_TIER.get(agent_l, "practical")


def load_tasks(
    tasks_dir: Path,
    *,
    initiator_prefix: str,
    since: datetime,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not tasks_dir.is_dir():
        return rows
    prefix = initiator_prefix.strip().lower()
    for path in sorted(tasks_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            continue
        if not isinstance(data, dict):
            continue
        init = str(data.get("initiator") or "").lower()
        # "grok" matches initiator "grok-night-drive" via substring or startswith
        if prefix and prefix not in init and not init.startswith(prefix):
            continue
        started = _parse_ts(str(data.get("started_at") or "") or None)
        finished = _parse_ts(str(data.get("finished_at") or "") or None)
        if started is None and finished is None:
            continue
        # Fully before the lookback window only. Unfinished work that started
        # earlier stays in-scope so single-seat marathons remain visible.
        if (
            started is not None
            and started < since
            and finished is not None
            and finished < since
        ):
            continue
        if finished is not None and finished < since and started is None:
            continue
        rows.append(data)
    return rows


def build_report(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    agents = Counter()
    models = Counter()
    tiers = Counter()
    statuses = Counter()
    for task in tasks:
        agent = str(task.get("agent") or "unknown")
        model = str(task.get("model") or "unknown")
        status = str(task.get("status") or "unknown")
        tier = _tier_for(agent, model)
        agents[agent] += 1
        models[f"{agent}/{model}"] += 1
        tiers[tier] += 1
        statuses[status] += 1

    n = len(tasks)
    done = statuses.get("done", 0)
    # Floor after 3+ implement-ish dispatches (anything not pure review-*)
    implement = [
        t
        for t in tasks
        if not str(t.get("task_id") or "").startswith("review-")
        and str(t.get("agent") or "") not in ("",)
    ]
    # Floor diversity MUST use the same population as floor_applies — otherwise
    # a review-* (or other non-implement) task can launder single-seat marathons.
    impl_agents = Counter()
    impl_tiers = Counter()
    for task in implement:
        agent = str(task.get("agent") or "unknown")
        model = str(task.get("model") or "unknown")
        if agent != "unknown":
            impl_agents[agent] += 1
        impl_tiers[_tier_for(agent, model)] += 1
    distinct_agents = len(impl_agents)
    distinct_tiers = len(impl_tiers)
    floor_applies = len(implement) >= 3
    floor_ok = (not floor_applies) or (distinct_agents >= 2 and distinct_tiers >= 2)

    return {
        "schema": "fleet-driver-breadth.v1",
        "task_count": n,
        "implement_dispatch_count": len(implement),
        "distinct_agents": distinct_agents,
        "distinct_tiers": distinct_tiers,
        "agents": dict(agents),
        "models": dict(models),
        "tiers": dict(tiers),
        "implement_agents": dict(impl_agents),
        "implement_tiers": dict(impl_tiers),
        "statuses": dict(statuses),
        "done_count": done,
        "done_rate": (done / n) if n else None,
        "breadth_floor_applies": floor_applies,
        "breadth_floor_ok": floor_ok,
        "breadth_floor_rule": "after >=3 implement dispatches: >=2 agents AND >=2 tiers (implement only)",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tasks-dir",
        type=Path,
        default=ROOT / "batch_state" / "tasks",
        help="batch_state/tasks directory",
    )
    parser.add_argument(
        "--initiator",
        default="grok",
        help="Substring match on task initiator (default: grok)",
    )
    parser.add_argument(
        "--since-hours",
        type=float,
        default=24.0,
        help="Lookback window in hours (default 24)",
    )
    parser.add_argument(
        "--enforce",
        action="store_true",
        help=(
            "Exit 2 when the breadth floor fails without --note-file, or when "
            "idle-settle telemetry has MISSING/DISHONEST dispositions. Never "
            "fails on raw idle opportunity-seconds."
        ),
    )
    parser.add_argument(
        "--note-file",
        type=Path,
        help="Path to a written NOTE: fleet_breadth justification (waives breadth-floor --enforce fail only)",
    )
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON only")
    parser.add_argument(
        "--idle-store",
        type=Path,
        default=None,
        help="Optional idle-settle events JSONL to embed; --enforce fails MISSING/DISHONEST in this store",
    )
    parser.add_argument(
        "--idle-snapshot-json",
        type=Path,
        default=None,
        help="Optional eligibility snapshot; embeds first-class admission WIP state (not a dashboard)",
    )
    args = parser.parse_args(argv)

    since = datetime.now(UTC) - timedelta(hours=args.since_hours)
    tasks = load_tasks(args.tasks_dir, initiator_prefix=args.initiator, since=since)
    report = build_report(tasks)
    report["initiator_filter"] = args.initiator
    report["since_hours"] = args.since_hours
    report["generated_at"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    idle_path = args.idle_store if args.idle_store is not None else idle_settle.default_store_path()
    if idle_path.is_file():
        report["idle_settle"] = idle_settle.build_report(
            idle_settle.load_events(idle_path),
            enforce=bool(args.enforce),
        )
    else:
        report["idle_settle"] = None
    admission_state: idle_settle.AdmissionState | None = None
    if args.idle_snapshot_json is not None:
        snap_payload = json.loads(args.idle_snapshot_json.read_text(encoding="utf-8"))
        if not isinstance(snap_payload, dict):
            print(
                f"error: idle snapshot must be a JSON object: {args.idle_snapshot_json}",
                file=sys.stderr,
            )
            return 2
        admission_state = idle_settle.evaluate_admission(idle_settle.parse_snapshot(snap_payload))
        report["admission"] = admission_state.to_dict()
    else:
        report["admission"] = None

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"fleet-driver-breadth initiator~={args.initiator!r} since_hours={args.since_hours}")
        print(
            f"  tasks={report['task_count']} implement={report['implement_dispatch_count']} "
            f"agents={report['distinct_agents']} tiers={report['distinct_tiers']} "
            f"done_rate={report['done_rate']}"
        )
        print(f"  agents: {report['agents']}")
        print(f"  tiers:  {report['tiers']}")
        print(f"  models: {report['models']}")
        print(f"  statuses: {report['statuses']}")
        print(
            f"  breadth_floor_applies={report['breadth_floor_applies']} "
            f"ok={report['breadth_floor_ok']} ({report['breadth_floor_rule']})"
        )
        idle = report.get("idle_settle")
        if isinstance(idle, dict):
            print(f"  idle_settle: {idle_settle.format_report(idle)}")
        if admission_state is not None:
            print(f"  admission: {idle_settle.format_admission(admission_state)}")

    fail = 0
    if args.enforce and report["breadth_floor_applies"] and not report["breadth_floor_ok"]:
        if args.note_file and args.note_file.is_file():
            try:
                note_text = args.note_file.read_text(encoding="utf-8")
            except OSError:
                note_text = ""
            if "NOTE: fleet_breadth" in note_text and len(note_text.strip()) >= 24:
                if not args.json:
                    print(f"  enforce: breadth floor waived by note-file {args.note_file}")
            else:
                if not args.json:
                    print(
                        "  enforce: FAIL — --note-file must contain "
                        "'NOTE: fleet_breadth' and a short justification",
                        file=sys.stderr,
                    )
                fail = 2
        else:
            if not args.json:
                print(
                    "  enforce: FAIL — need >=2 agents and >=2 tiers after 3+ implement "
                    "dispatches, or pass --note-file with a fleet_breadth NOTE",
                    file=sys.stderr,
                )
            fail = 2

    idle_report = report.get("idle_settle")
    disposition_fails = idle_settle.enforce_fail_codes(
        idle_report if isinstance(idle_report, dict) else None
    )
    if args.enforce and disposition_fails:
        if not args.json:
            print(
                "  enforce: FAIL — idle disposition "
                + ",".join(disposition_fails)
                + " (never a raw idle-seconds threshold)",
                file=sys.stderr,
            )
        fail = 2
    return fail


if __name__ == "__main__":
    raise SystemExit(main())
