#!/usr/bin/env python3
"""Capacity-first lane picker for pre-dispatch routing (operator 2026-08-12).

Drivers run this before every implement dispatch. Prefer cool/idle seats;
mark hot / near_cap / deficit lanes AVOID. Shares the Monitor snapshot and
blocking native refresh path with ``scripts.fleet.usage``. The admission line
reports whether ``delegate.py dispatch`` would admit a write worker on this host
now, from the same function dispatch calls (#8645).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from scripts.fleet.reset_reserve import (
        codex_is_threatened,
        codex_reset_reserve_eligible,
        effective_reset_reserve,
        load_reset_reserve,
    )
except ImportError:  # pragma: no cover - script path fallback
    from reset_reserve import (  # type: ignore
        codex_is_threatened,
        codex_reset_reserve_eligible,
        effective_reset_reserve,
        load_reset_reserve,
    )

try:
    from scripts.agent_runtime.agent_identity import RETIRED_AGENT_ALIASES
except ImportError:  # pragma: no cover - script path fallback
    from agent_runtime.agent_identity import RETIRED_AGENT_ALIASES  # type: ignore

from scripts.common.task_store_paths import tasks_dir as default_tasks_dir
from scripts.fleet import credit_lane
from scripts.orchestration import dispatch_admission

# Subscription + free seats drivers may pick for code implement. "gemini" and
# "glm" are kept here for budget-row VISIBILITY (their quota/status still
# shows in the table) but are force-AVOID via RETIRED_AGENT_ALIASES below —
# the gemini CLI is retired (operator 2026-08-18) and the z.ai GLM
# subscription is retired (operator 2026-09-03); neither may ever be a `pick`.
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

_AVOID_STATUSES = frozenset({"hot", "near_cap", "need_login"})
_COOL_STATUSES = frozenset({"cool", "warm", "idle"})
# Retired lanes (gemini, glm) rank alongside each other near the bottom —
# is_avoid_lane() already force-excludes them from `pick`, this ordering only
# affects stable table/tie-break display among AVOID rows.
_CODE_LANE_PRIORITY = {
    "cursor": 0,
    "codex": 1,
    "claude": 2,
    "grok": 3,
    "kimi": 4,
    "gemini": 5,
    "glm": 6,
    "agy": 7,
    "deepseek": 8,
}
_MONITOR_DEFAULT = "http://127.0.0.1:8765"
# delegate.py's task records, anchored to the primary checkout.


def _monitor_base() -> str:
    return os.environ.get("DELEGATE_MONITOR_API", _MONITOR_DEFAULT).rstrip("/")


def lane_status(agent_info: dict[str, Any] | None) -> str:
    """Resolve display status for a routing-budget agent record."""
    info = agent_info or {}
    native = info.get("codexbar") or {}
    if info.get("freshness", native.get("freshness")) == "unavailable":
        return "unknown"
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


def _is_hard_avoid(agent_info: dict[str, Any] | None, *, lane: str | None = None) -> bool:
    """True when ``lane`` is retired, ineligible, unhealthy or needs login: no capacity source relaxes these."""
    if lane is not None and lane.strip().lower() in RETIRED_AGENT_ALIASES:
        return True
    info = agent_info or {}
    if info.get("eligible") is False or (info.get("health") or {}).get("healthy") is False:
        return True
    return info.get("login_state") == "NEED_LOGIN" or info.get("probe_state") == "NEED_LOGIN"


def is_avoid_lane(
    agent_info: dict[str, Any] | None,
    *,
    lane: str | None = None,
    deficit: dict[str, Any] | None = None,
) -> bool:
    """True when hot/near_cap/need_login, CodexBar deficit, or ``lane`` is retired."""
    if _is_hard_avoid(agent_info, lane=lane):
        return True
    deficit = deficit if deficit is not None else credit_lane.pace_deficit_state(lane or "", agent_info)
    status = lane_status({**(agent_info or {}), "status": deficit["status"]})
    if status in _AVOID_STATUSES:
        return True
    return deficit["uncovered"] is True


def remaining_pct(agent_info: dict[str, Any] | None) -> float | None:
    info = agent_info or {}
    rem = info.get("remaining_pct")
    if isinstance(rem, (int, float)):
        return float(rem)
    provider_windows = info.get("provider_windows")
    if isinstance(provider_windows, dict):
        auto = provider_windows.get("auto")
        if isinstance(auto, dict) and isinstance(auto.get("remaining_pct"), (int, float)):
            return float(auto["remaining_pct"])
    headroom = info.get("headroom_pct")
    if isinstance(headroom, (int, float)):
        return float(headroom)
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


def _has_capacity_signal(info: dict[str, Any]) -> bool:
    """True when a lane entry carries a real probe reading, not an empty shell."""
    if not info:
        return False
    if str(info.get("status") or "") not in {"", "unknown"}:
        return True
    if remaining_pct(info) is not None:
        return True
    interactive = info.get("interactive")
    return isinstance(interactive, dict) and str(interactive.get("status") or "") not in {"", "unknown"}


# Live dispatch lanes that share a subscription probe keyed under a retired
# provider id in routing-budget (PROVIDER_TO_LANE). Do NOT mirror every
# RETIRED_AGENT_ALIASES entry — e.g. glm→cursor is retirement-only, not a
# shared Z.AI/Cursor quota pool (CF #8095).
_SHARED_QUOTA_SOURCES: dict[str, str] = {
    "agy": "gemini",
}


def _mirror_retired_quota(agents: dict[str, Any], lane: str, info: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    """Mirror a shared-subscription probe onto its live dispatch lane.

    ``PROVIDER_TO_LANE`` keys AGY usage under ``gemini``, while
    ``RETIRED_AGENT_ALIASES`` routes dispatch ``gemini`` → ``agy``. Without this
    mirror the ``agy`` row renders ``unknown`` even when ``agy /usage`` is
    healthy. Only explicit shared-quota pairs are mirrored — never every
    retired alias (``glm`` → ``cursor`` must not inherit Z.AI capacity).
    """
    if _has_capacity_signal(info):
        return info, None
    source_lane = _SHARED_QUOTA_SOURCES.get(lane)
    if not source_lane:
        return info, None
    source = agents.get(source_lane)
    if isinstance(source, dict) and source:
        return dict(source), source_lane
    return info, None


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


# Credit states that keep the lane in its plan state; the row notes say why.
_CREDIT_NOTE_STATES = frozenset(
    {
        credit_lane.CREDITS_EXHAUSTED,
        credit_lane.CREDITS_UNVERIFIED,
        credit_lane.CREDIT_USE_UNCONFIRMED,
        credit_lane.POLICY_ERROR,
    }
)


def build_lane_rows(
    budget: dict[str, Any],
    *,
    active_in_flight: dict[str, int] | None = None,
    lanes: tuple[str, ...] = CODE_LANES,
    reset_reserve: dict[str, Any] | None = None,
    credit_policy: credit_lane.CreditPolicy | None = None,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Pure formatter input: one row per lane from a routing-budget payload.

    A lane the credit policy marks ``credit_balance_present`` is usable (that
    status) instead of near_cap/AVOID; retirement, ineligibility, ill health
    and NEED_LOGIN still avoid it. Each row carries ``credit``. An unreadable
    policy marks the built-in credit lanes ``policy_error`` (plan state
    applies) and leaves every other lane unchanged.
    """
    policy = credit_policy
    policy_error: str | None = None
    if policy is None:
        try:
            policy = credit_lane.load_policy()
        except ValueError as exc:
            policy_error = str(exc)
    agents = budget.get("agents") if isinstance(budget.get("agents"), dict) else {}
    budget_flight = budget.get("in_flight") if isinstance(budget.get("in_flight"), dict) else {}
    active = active_in_flight or {}
    reserve = (
        reset_reserve
        if reset_reserve is not None
        else load_reset_reserve(Path(__file__).resolve().parents[2], codex_info=agents.get("codex"))
    )
    reserve = effective_reset_reserve(reserve, agents.get("codex"))
    diagnostics = budget.get("diagnostics") if isinstance(budget.get("diagnostics"), dict) else {}
    snapshot_stale = bool(diagnostics.get("stale"))
    rows: list[dict[str, Any]] = []
    for lane in lanes:
        info = agents.get(lane) if isinstance(agents.get(lane), dict) else {}
        quota_source: str | None = None
        if lane == "deepseek":
            from scripts.fleet.prepaid_status import api_lane_status_from_account

            account = (budget.get("api_accounts") or {}).get(lane) or {}
            status = api_lane_status_from_account(lane, account)
            info = {**info, "status": status, "probe_state": account.get("probe_state")}
            # Prepaid balance probes stay green while the dispatch lane itself
            # is down (e.g. opencode provider config loss, #8514) — carry the
            # lane-health record so is_avoid_lane can demote it.
            if isinstance(account.get("health"), dict):
                info["health"] = account["health"]
            if (
                status not in {"cool", "warm"}
                or account.get("is_available") is False
                or account.get("status") == "near_cap"
            ):
                info["eligible"] = False
        else:
            info, quota_source = _mirror_retired_quota(agents, lane, info)
        if budget.get("transport") == "acp" and info.get("eligible") is not True:
            info = {**info, "eligible": False}
        reserve_relaxes = (
            lane == "codex"
            and codex_is_threatened(info)
            and codex_reset_reserve_eligible(reserve, info, snapshot_stale=snapshot_stale)
        )
        credit = (
            credit_lane.lane_credit_report(lane, info, policy, now=now, snapshot_stale=snapshot_stale)
            if policy is not None
            else credit_lane.policy_error_state(lane, policy_error or "unknown error")
        )
        credit_relaxes = credit["state"] == credit_lane.CREDIT_BALANCE_PRESENT and not _is_hard_avoid(info, lane=lane)
        deficit = credit_lane.pace_deficit_state(
            lane,
            info,
            policy=policy,
            now=now,
            snapshot_stale=snapshot_stale,
        )
        status = (
            credit_lane.CREDIT_BALANCE_PRESENT if credit_relaxes else lane_status({**info, "status": deficit["status"]})
        )
        will_last = will_last_to_reset(info)
        cb = info.get("codexbar") if isinstance(info.get("codexbar"), dict) else None
        pace_deficit = deficit["uncovered"] is True
        retired_target = RETIRED_AGENT_ALIASES.get(lane)
        avoid = is_avoid_lane(info, lane=lane, deficit=deficit) and not reserve_relaxes and not credit_relaxes
        in_flight = int(active.get(lane, budget_flight.get(lane, 0) or 0) or 0)
        notes: list[str] = []
        if deficit["covered_by"]:
            notes.append(deficit["reason"])
        if quota_source:
            notes.append(f"quota:{quota_source}")
        if credit_relaxes:
            notes.append(
                f"credit balance present ({credit['credit_balance']:g}; draw not verified by the router; "
                f"models {', '.join(credit['allowed_models'])} only)"
            )
        elif credit["state"] in _CREDIT_NOTE_STATES:
            notes.append(f"{credit['state']}: {credit['reason']}")
        # Reuse the verified inventory for display; near-cap reset admission
        # still requires the separately asserted operator reserve above.
        # An unreadable policy cannot supply inventory freshness bounds, so
        # policy_error deliberately suppresses this informational note too.
        if lane == "codex" and codex_is_threatened(info):
            available = (credit.get("reset_advice") or {}).get("free_resets_available")
            if isinstance(available, int) and available > 0:
                notes.append(f"free full reset available ({available}; operator decision)")
        if reserve_relaxes:
            notes.append(f"reset reserve eligible ({reserve.get('remaining_resets')} remaining)")
        if avoid:
            notes.append("AVOID")
            health_info = info.get("health") if isinstance(info.get("health"), dict) else {}
            if health_info.get("healthy") is False:
                last_error = str(health_info.get("last_error") or "").strip()
                notes.append(f"unhealthy: {last_error}" if last_error else "unhealthy lane")
            if info.get("eligible") is False:
                notes.append(str(info.get("health", {}).get("failure_code") or "ineligible"))
            if info.get("login_state") == "NEED_LOGIN" or info.get("probe_state") == "NEED_LOGIN":
                notes.append("NEED_LOGIN")
            if retired_target:
                notes.append(f"retired→{retired_target}")
            if pace_deficit:
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
                "reset_reserve_eligible": reserve_relaxes,
                "notes": "; ".join(notes) if notes else "",
                "credit": credit,
                **(
                    {
                        "pace_deficit": deficit,
                        "codexbar": cb,
                        **{
                            key: info[key]
                            for key in (
                                "freshness",
                                "age_s",
                                "fetched_at",
                                "reset_credits",
                                "credit_balance",
                                "runtime",
                                "status_source",
                            )
                            if key in info
                        },
                    }
                    if deficit["raw_deficit"] is True
                    else {}
                ),
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
        lane_name = str(row.get("lane") or "")
        lane_rank = _CODE_LANE_PRIORITY.get(lane_name, 50)
        status_rank = {
            "cool": 0,
            "warm": 1,
            "unknown": 2,
            "pre_launch": 3,
            # Credit balance present (draw not verified by the router): after every plan-backed seat.
            credit_lane.CREDIT_BALANCE_PRESENT: 7,
            "hot": 8,
            "near_cap": 9,
        }.get(status, 5)
        reserve_priority = 0 if row.get("reset_reserve_eligible") else 1
        return (avoid, reserve_priority, status_rank, lane_rank, in_flight, rem_key, lane_name)

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
    return [
        str(row["lane"])
        for row in rows
        if not row.get("avoid")
        and (
            row.get("status") in _COOL_STATUSES
            or row.get("reset_reserve_eligible")
            or row.get("status") == credit_lane.CREDIT_BALANCE_PRESENT
        )
    ]


def admission_status(tasks_dir: Path | None = None) -> dict[str, Any]:
    """Would ``delegate.py dispatch`` admit a write worker now? Report only: dead pids are not swept."""
    try:
        decision = dispatch_admission.evaluate("workspace-write", tasks_dir or default_tasks_dir())
    except ValueError as exc:
        return {"admitted": None, "line": f"admission (write dispatch): unknown — invalid threshold: {exc}"}
    record = decision.to_record()
    for key in ("forced", "force_reason", "swept_crashed"):
        record.pop(key, None)
    verdict = "would admit now" if decision.admitted else "would REFUSE now: " + "; ".join(decision.failures)
    record["line"] = f"admission (write dispatch): {verdict} | {decision.summary()}"
    return record


def build_report(
    budget: dict[str, Any],
    *,
    active_in_flight: dict[str, int] | None = None,
    reset_reserve: dict[str, Any] | None = None,
    admission: dict[str, Any] | None = None,
    credit_policy: credit_lane.CreditPolicy | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    rows = build_lane_rows(
        budget,
        active_in_flight=active_in_flight,
        reset_reserve=reset_reserve,
        credit_policy=credit_policy,
        now=now,
    )
    pick_order = build_pick_order(rows)
    rec = budget.get("recommendation") if isinstance(budget.get("recommendation"), dict) else {}
    warnings = list(rec.get("warnings") or [])
    primary = rec.get("primary_agent_for_code")
    # The upstream recommendation (Monitor API) doesn't know gemini is
    # retired — never surface it as a pick here, even if upstream still
    # recommends it off a stale/uninformed CodexBar reading.
    retired_target = RETIRED_AGENT_ALIASES.get(str(primary or "").strip().lower())
    if retired_target:
        warnings.append(
            f"recommendation.primary_agent_for_code was {primary!r} (retired CLI) "
            f"— capacity_pick substituted {retired_target!r}."
        )
        primary = retired_target
    if primary and any(row["lane"] == primary and row["avoid"] for row in rows):
        warnings.append(f"recommendation {primary!r} suppressed: lane is AVOID")
        primary = None
    for row in rows:
        if row["lane"] == primary and row["status"] == credit_lane.CREDIT_BALANCE_PRESENT:
            warnings.append(
                f"recommendation {primary!r} is past its plan cap with a {credit_lane.DRAW_NOT_VERIFIED}: "
                f"dispatch only {', '.join(row['credit']['allowed_models'])} (credit-period allowlist)"
            )
    policy_errors = [row for row in rows if (row.get("credit") or {}).get("state") == credit_lane.POLICY_ERROR]
    if policy_errors:
        warnings.append(
            f"{policy_errors[0]['credit']['reason']}: "
            + "; ".join(
                f"{row['lane']} keeps its plan state and dispatch admits only "
                f"{', '.join(row['credit']['allowed_models'])}"
                for row in policy_errors
            )
            + "; other lanes unaffected"
        )
    return {
        "transport": budget.get("transport", "dispatch"),
        "generated_at": budget.get("generated_at"),
        "source": budget.get("source", "unknown"),
        "rows": rows,
        "pick_order": pick_order,
        "cooler_lanes": cooler_lanes(rows),
        "recommendation": {
            "primary_agent_for_code": primary,
            "rationale": rec.get("rationale"),
            "warnings": warnings,
        },
        "diagnostics": budget.get("diagnostics") or {},
        "active_in_flight": dict(active_in_flight or {}),
        "admission": admission,
    }


def format_credit_lines(rows: list[dict[str, Any]]) -> list[str]:
    """One credit-state line and one reset-advice line per credit-configured lane."""
    lines: list[str] = []
    for row in rows:
        credit = row.get("credit") or {}
        state = credit.get("state")
        if not state or state == credit_lane.NOT_CONFIGURED:
            continue
        lane = row.get("lane")
        models = ", ".join(credit.get("allowed_models") or [])
        evidence = credit.get("evidence") or {}
        count = evidence.get("rate_limited_count")
        evidence_text = (
            f" | evidence: rate limits {'unknown' if count is None else count} in last "
            f"{evidence.get('rate_limit_window_s'):g}s; balance {evidence.get('credit_balance')} "
            f"fetched {evidence.get('credit_fetched_at') or 'unknown'}"
            if evidence
            else ""
        )
        if state == credit_lane.CREDIT_BALANCE_PRESENT:
            coverage = credit.get("coverage") or {}
            dispatches = coverage.get("dispatches")
            lines.append(
                f"credit lane {lane}: {state} ({credit.get('reason')}){evidence_text} | coverage: "
                f"{dispatches if dispatches is not None else coverage.get('basis')} | models: {models} only"
            )
        elif state == credit_lane.POLICY_ERROR:
            lines.append(f"credit lane {lane}: {state} ({credit.get('reason')}) | dispatch admits only {models}")
        else:
            gate = (
                f"dispatch admits only {models} (fresh credit balance with the plan window exhausted)"
                if credit_lane.allowlist_applies(credit)
                else f"models restricted to {models} only while a fresh credit balance exists past the plan cap"
            )
            lines.append(f"credit lane {lane}: {state} ({credit.get('reason')}){evidence_text} | {gate}")
        advice = credit.get("reset_advice") or {}
        if advice:
            free = advice.get("free_resets_available")
            expires = ", ".join(str(value or "no expiry") for value in advice.get("free_reset_expires_at") or [])
            lines.append(
                f"reset advice {lane}: {advice.get('advice')} — {advice.get('reason')} | natural reset "
                f"{advice.get('natural_reset_at') or 'unknown'} | free full resets "
                f"{'unknown' if free is None else free}{f' (expire {expires})' if expires else ''} | "
                f"window anchor {advice.get('window_anchor_evidence')} | never consumed automatically"
            )
    return lines


def format_human(report: dict[str, Any]) -> str:
    lines = [
        f"capacity_pick — capacity-first {report.get('transport', 'dispatch')} routing",
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
    lines.extend(format_credit_lines(list(report.get("rows") or [])))
    lines.append("")
    lines.append(format_pick_order(list(report.get("pick_order") or [])))
    cool = report.get("cooler_lanes") or []
    if cool:
        lines.append(f"cooler seats: {', '.join(cool)}")
    admission = report.get("admission")
    if isinstance(admission, dict) and admission.get("line"):
        lines.append(str(admission["line"]))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.fleet.capacity_pick",
        description="Print capacity-first lane pick order before implement dispatch.\nUse to compare capacity, not to certify model eligibility.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.fleet.capacity_pick --json\n"
            "  .venv/bin/python -m scripts.fleet.capacity_pick --transport acp --strict\n\n"
            "Outputs: routing table or JSON; no provider prompts. The last line (JSON: `admission`) says whether\n"
            "a write dispatch would pass host admission now: live write workers vs cap, MemAvailable vs floor,\n"
            "load per CPU vs limit (thresholds: DISPATCH_* in scripts/config.py, env-overridable). When\n"
            "lu-dispatch.slice is active the same line adds its memory use against MemoryMax.\n"
            "Credit lanes (scripts/config/credit_lanes.yaml): a lane near its plan cap with a fresh positive\n"
            "credit balance and no rate limit in the evidence window reads `credit_balance_present` (usable;\n"
            "the router does not verify the provider draws credits; dispatch admits only allowlisted models).\n"
            "A recent rate limit reads `credit_use_unconfirmed`; missing or stale credit data, or an unreadable\n"
            "policy (`policy_error`), keeps near_cap/AVOID. JSON rows carry `credit` with state, evidence,\n"
            "coverage and `reset_advice` (use_reset_now | hold_reset | not_applicable). Nothing consumes\n"
            "credits or resets.\n"
            "Weekly pace deficits covered by fresh credits (allowlisted models) or an unexpired free\n"
            "full reset are not hot. Reserve evidence must be fresh and free of recent rate limits.\n"
            "JSON rows keep the raw pace and say which reserve covers it; near_cap is unchanged.\n"
            "Exit codes: 0 success; 2 invalid arguments or no admissible lane with --strict.\n"
            "Related: /api/state/routing-budget?transport=acp; scripts/orchestration/dispatch_admission.py;\n"
            "issues #7812, #8645, #9518, #9615."
        ),
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Block for native usage probes (default: warm Monitor snapshot).",
    )
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON only.")
    parser.add_argument(
        "--transport",
        choices=("dispatch", "acp"),
        default="dispatch",
        help="Select native implementation dispatch (default) or ordinary ask-* ACP compatibility.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 2 when no cool/warm lane, admissible Codex reset reserve or credit-balance lane is available.",
    )
    args = parser.parse_args(argv)

    from scripts.fleet.usage import read_budget

    budget = read_budget(fresh=bool(args.fresh), transport=args.transport)
    active = fetch_active_in_flight()
    report = build_report(budget, active_in_flight=active, admission=admission_status())

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(format_human(report))

    if args.strict and not report.get("cooler_lanes"):
        if not args.json:
            print(
                "❌ --strict: no cool/warm lane, admissible reset reserve or credit-balance lane available",
                file=sys.stderr,
            )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
