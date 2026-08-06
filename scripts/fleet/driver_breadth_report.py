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

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Catalog tier map is loaded best-effort; fall back to coarse agent tiers.
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

_AUTHORITY_MODEL_HINTS = (
    "fable",
    "sol",
    "opus",
    "gpt-5.6-sol",
    "claude-fable",
    "claude-opus",
)
# Delimiter-aware heap tokens. Bare substring "flash"/"mini" mis-classifies
# gemini-3.6-flash-high (practical) and gemini-* (via "mini" inside "gemini").
_HEAP_MODEL_SUBSTRINGS = (
    "luna",
    "haiku",
    "k2.5",
    "laguna",
)
_HEAP_TOKEN_RE = re.compile(
    r"(?:^|[-_.])(?:flash|mini)(?:$|[-_.])",
)
_PRACTICAL_OVERRIDE_RE = re.compile(
    r"flash-high|gemini-3\.[0-9]+-flash-high|gpt-5\.6-terra|claude-sonnet",
)


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _tier_for(agent: str | None, model: str | None) -> str:
    agent_l = (agent or "").strip().lower()
    model_l = (model or "").strip().lower()
    for hint in _AUTHORITY_MODEL_HINTS:
        if hint in model_l:
            return "authority"
    # Practical before heap: *-flash-high is frontier_practical, not heap Flash.
    if _PRACTICAL_OVERRIDE_RE.search(model_l):
        return "practical"
    for hint in _HEAP_MODEL_SUBSTRINGS:
        if hint in model_l:
            return "heap"
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
        if started is not None and started < since and (finished is None or finished < since):
            continue
        if finished is not None and finished < since and (started is None or started < since):
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
    distinct_agents = len([a for a in agents if a != "unknown"])
    distinct_tiers = len(tiers)
    done = statuses.get("done", 0)
    # Floor after 3+ implement-ish dispatches (anything not pure review-*)
    implement = [
        t
        for t in tasks
        if not str(t.get("task_id") or "").startswith("review-")
        and str(t.get("agent") or "") not in ("",)
    ]
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
        "statuses": dict(statuses),
        "done_count": done,
        "done_rate": (done / n) if n else None,
        "breadth_floor_applies": floor_applies,
        "breadth_floor_ok": floor_ok,
        "breadth_floor_rule": "after >=3 implement dispatches: >=2 agents AND >=2 tiers",
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
        help="Exit 2 when breadth floor fails and no --note-file is provided",
    )
    parser.add_argument(
        "--note-file",
        type=Path,
        help="Path to a written NOTE: fleet_breadth justification (waives --enforce fail)",
    )
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON only")
    args = parser.parse_args(argv)

    since = datetime.now(UTC) - timedelta(hours=args.since_hours)
    tasks = load_tasks(args.tasks_dir, initiator_prefix=args.initiator, since=since)
    report = build_report(tasks)
    report["initiator_filter"] = args.initiator
    report["since_hours"] = args.since_hours
    report["generated_at"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

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

    if args.enforce and report["breadth_floor_applies"] and not report["breadth_floor_ok"]:
        if args.note_file and args.note_file.is_file() and args.note_file.stat().st_size > 0:
            if not args.json:
                print(f"  enforce: waived by note-file {args.note_file}")
            return 0
        if not args.json:
            print(
                "  enforce: FAIL — need >=2 agents and >=2 tiers after 3+ implement "
                "dispatches, or pass --note-file with a fleet_breadth NOTE",
                file=sys.stderr,
            )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
