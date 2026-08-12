#!/usr/bin/env python3
"""Capacity-first lane picker for pre-dispatch routing (operator 2026-08-12).

Drivers run this before every implement dispatch. Prefer cool/idle seats;
mark hot / near_cap / deficit lanes AVOID. Uses ``compute_routing_budget``
(already embeds CodexBar) — no multi-provider refresh loops unless ``--fresh``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any

# Subscription + free seats drivers may pick for code implement.
CODE_LANES: tuple[str, ...] = (
    "claude",
    "codex",
    "gemini",
    "grok",
    "cursor",
    "kimi",
    "agy",
    "deepseek",
    "glm",
)

_AVOID_STATUSES = frozenset({"hot", "near_cap"})
_COOL_STATUSES = frozenset({"cool", "warm", "idle"})
_MONITOR_DEFAULT = "http://127.0.0.1:8765"


def _monitor_base() -> str:
    return os.environ.get("DELEGATE_MONITOR_API", _MONITOR_DEFAULT).rstrip("/")


def lane_status(agent_info: dict[str, Any] | None) -> str:
    """Resolve display status for a routing-budget agent record."""
    info = agent_info or {}
    status = info.get("status")
    if not status and isinstance(info.get("interactive"), dict):
        status = info["interactive"].get("status")
    return str(status or "unknown")


def will_last_to_reset(agent_info: dict[str, Any] | None) -> bool | None:
    info = agent_info or {}
    cb = info.get("codexbar")
    if isinstance(cb, dict) and "will_last_to_reset" in cb:
        val = cb.get("will_last_to_reset")
        if val is None:
            return None
        return bool(val)
    return None


def is_avoid_lane(agent_info: dict[str, Any] | None) -> bool:
    """True when status is hot/near_cap or CodexBar deficit (will_last_to_reset is False)."""
    status = lane_status(agent_info)
    if status in _AVOID_STATUSES:
        return True
    return will_last_to_reset(agent_info) is False


def remaining_pct(agent_info: dict[str, Any] | None) -> float | None:
    info = agent_info or {}
    rem = info.get("remaining_pct")
    if isinstance(rem, (int, float)):
        return float(rem)
    burn = info.get("burn_pct_7d")
    if isinstance(burn, (int, float)):
        return 100.0 - float(burn)
    cb = info.get("codexbar") if isinstance(info.get("codexbar"), dict) else {}
    weekly = cb.get("weekly_remaining_pct") if isinstance(cb, dict) else None
    if isinstance(weekly, (int, float)):
        return float(weekly)
    return None


def pace_summary(agent_info: dict[str, Any] | None) -> str:
    info = agent_info or {}
    cb = info.get("codexbar") if isinstance(info.get("codexbar"), dict) else {}
    if isinstance(cb, dict):
        summary = cb.get("pace_summary")
        if summary:
            return str(summary)
        delta = cb.get("weekly_pace_delta_pct")
        if isinstance(delta, (int, float)):
            return f"pace_delta={delta:+.1f}%"
    return "—"


def fetch_active_in_flight(*, timeout: float = 2.0) -> dict[str, int]:
    """Fail-open read of /api/delegate/active → agent → count."""
    url = f"{_monitor_base()}/api/delegate/active"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, TimeoutError, urllib.error.URLError, json.JSONDecodeError, ValueError):
        return {}
    if not isinstance(payload, dict):
        return {}
    counts: dict[str, int] = {}
    for task in payload.get("tasks") or []:
        if not isinstance(task, dict):
            continue
        agent = str(task.get("agent") or "").strip().lower()
        if not agent:
            continue
        counts[agent] = counts.get(agent, 0) + 1
    return counts


def build_lane_rows(
    budget: dict[str, Any],
    *,
    active_in_flight: dict[str, int] | None = None,
    lanes: tuple[str, ...] = CODE_LANES,
) -> list[dict[str, Any]]:
    """Pure formatter input: one row per lane from a routing-budget payload."""
    agents = budget.get("agents") if isinstance(budget.get("agents"), dict) else {}
    budget_flight = budget.get("in_flight") if isinstance(budget.get("in_flight"), dict) else {}
    active = active_in_flight or {}
    rows: list[dict[str, Any]] = []
    for lane in lanes:
        info = agents.get(lane) if isinstance(agents.get(lane), dict) else {}
        status = lane_status(info)
        will_last = will_last_to_reset(info)
        avoid = is_avoid_lane(info)
        in_flight = int(active.get(lane, budget_flight.get(lane, 0) or 0) or 0)
        notes: list[str] = []
        if avoid:
            notes.append("AVOID")
            if will_last is False:
                notes.append("deficit")
            if status in _AVOID_STATUSES:
                notes.append(status)
        elif in_flight == 0 and status in _COOL_STATUSES:
            notes.append("idle")
        elif in_flight > 0:
            notes.append(f"{in_flight} in flight")
        rem = remaining_pct(info)
        rows.append(
            {
                "lane": lane,
                "status": status,
                "remaining_pct": rem,
                "will_last": will_last,
                "pace": pace_summary(info),
                "in_flight": in_flight,
                "avoid": avoid,
                "notes": "; ".join(notes) if notes else "",
            }
        )
    return rows


def build_pick_order(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Cool/idle first; AVOID lanes last with pick=AVOID."""

    def _sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
        avoid = bool(row.get("avoid"))
        status = str(row.get("status") or "unknown")
        rem = row.get("remaining_pct")
        rem_key = -float(rem) if isinstance(rem, (int, float)) else 0.0
        in_flight = int(row.get("in_flight") or 0)
        status_rank = {
            "cool": 0,
            "warm": 1,
            "unknown": 2,
            "pre_launch": 3,
            "hot": 8,
            "near_cap": 9,
        }.get(status, 5)
        return (avoid, status_rank, in_flight, rem_key, str(row.get("lane")))

    ordered = sorted(rows, key=_sort_key)
    out: list[dict[str, Any]] = []
    rank = 1
    for row in ordered:
        entry = dict(row)
        if row.get("avoid"):
            entry["pick"] = "AVOID"
        else:
            entry["pick"] = rank
            rank += 1
        out.append(entry)
    return out


def format_table(rows: list[dict[str, Any]]) -> str:
    headers = ("lane", "status", "remaining%", "will_last", "pace", "in_flight", "notes")
    cells: list[tuple[str, ...]] = []
    for row in rows:
        rem = row.get("remaining_pct")
        rem_s = f"{rem:.1f}" if isinstance(rem, (int, float)) else "—"
        will = row.get("will_last")
        will_s = "—" if will is None else ("yes" if will else "no")
        cells.append(
            (
                str(row.get("lane") or ""),
                str(row.get("status") or ""),
                rem_s,
                will_s,
                str(row.get("pace") or "—"),
                str(int(row.get("in_flight") or 0)),
                str(row.get("notes") or ""),
            )
        )
    widths = [len(h) for h in headers]
    for cell in cells:
        for i, val in enumerate(cell):
            widths[i] = max(widths[i], len(val))
    lines = [
        " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers)),
        "-+-".join("-" * widths[i] for i in range(len(headers))),
    ]
    for cell in cells:
        lines.append(" | ".join(cell[i].ljust(widths[i]) for i in range(len(headers))))
    return "\n".join(lines)


def format_pick_order(pick_order: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for entry in pick_order:
        pick = entry.get("pick")
        lane = entry.get("lane")
        if pick == "AVOID":
            parts.append(f"AVOID:{lane}")
        else:
            parts.append(f"{pick}.{lane}")
    return "pick order (code implement): " + " → ".join(parts)


def cooler_lanes(rows: list[dict[str, Any]]) -> list[str]:
    return [str(r["lane"]) for r in rows if not r.get("avoid") and r.get("status") in _COOL_STATUSES]


def build_report(
    budget: dict[str, Any],
    *,
    active_in_flight: dict[str, int] | None = None,
) -> dict[str, Any]:
    rows = build_lane_rows(budget, active_in_flight=active_in_flight)
    pick_order = build_pick_order(rows)
    rec = budget.get("recommendation") if isinstance(budget.get("recommendation"), dict) else {}
    return {
        "generated_at": budget.get("generated_at"),
        "rows": rows,
        "pick_order": pick_order,
        "cooler_lanes": cooler_lanes(rows),
        "recommendation": {
            "primary_agent_for_code": rec.get("primary_agent_for_code"),
            "rationale": rec.get("rationale"),
            "warnings": list(rec.get("warnings") or []),
        },
        "diagnostics": budget.get("diagnostics") or {},
        "active_in_flight": dict(active_in_flight or {}),
    }


def format_human(report: dict[str, Any]) -> str:
    lines = [
        "capacity_pick — capacity-first dispatch routing",
        format_table(list(report.get("rows") or [])),
        "",
    ]
    rec = report.get("recommendation") or {}
    primary = rec.get("primary_agent_for_code")
    lines.append(f"recommendation.primary_agent_for_code: {primary}")
    if rec.get("rationale"):
        lines.append(f"rationale: {rec['rationale']}")
    for warning in rec.get("warnings") or []:
        lines.append(f"warning: {warning}")
    lines.append("")
    lines.append(format_pick_order(list(report.get("pick_order") or [])))
    cool = report.get("cooler_lanes") or []
    if cool:
        lines.append(f"cooler seats: {', '.join(cool)}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.fleet.capacity_pick",
        description="Print capacity-first lane pick order before implement dispatch.",
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Pass fresh_codexbar=True to compute_routing_budget (may be slow).",
    )
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON only.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 2 when no cool/warm lane is available.",
    )
    args = parser.parse_args(argv)

    try:
        from scripts.api.state_router import compute_routing_budget
    except ImportError:  # pragma: no cover - script path fallback
        from api.state_router import compute_routing_budget  # type: ignore

    budget = compute_routing_budget(fresh_codexbar=bool(args.fresh))
    active = fetch_active_in_flight()
    report = build_report(budget, active_in_flight=active)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(format_human(report))

    if args.strict and not report.get("cooler_lanes"):
        if not args.json:
            print("❌ --strict: no cool/warm lane available", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
