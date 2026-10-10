"""Who-is-doing-what views: now, epics, and agents."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .activity import (
    derive_state,
    harness_row,
    load_delegate_health,
    load_occupancy_activity,
    pr_stale_minutes,
    resolve_activity,
    resolve_idle_min,
    resolve_pid,
    seat_id,
    text,
)
from .snapshot import as_timestamp, finite_number, load_snapshot, mapping, utc_now
from .sources import SourceReport, collect_source_reports, report

USAGE_NEAR_FLOOR = 80.0
USAGE_NEAR_GAP = 20.0
USAGE_HARD_FLOOR = 95.0
_KIND_ORDER = {
    "dead_driver": 0,
    "stuck_driver": 1,
    "red_foundation": 2,
    "unqueued_pr": 3,
    "alert": 4,
    "usage": 5,
}
_SEVERITY_ORDER = {"bad": 0, "warn": 1}
_NOT_QUEUED = frozenset({"not_queued", "none"})


@dataclass(frozen=True)
class Board:
    sources: tuple[SourceReport, ...]
    epics: list[dict[str, Any]]
    agents: list[dict[str, Any]]
    attention: list[dict[str, Any]]


def _overlay_sources(
    base: tuple[SourceReport, ...],
    replacements: Mapping[str, SourceReport],
    extra: tuple[SourceReport, ...],
) -> tuple[SourceReport, ...]:
    rows = [replacements.get(item.name, item) for item in base]
    return tuple(rows) + extra


def _whole_number(value: object) -> int | None:
    number = finite_number(value)
    if number is None or (isinstance(value, float) and not number.is_integer()):
        return None
    whole = int(number)
    if whole <= 0:
        return None
    return whole


def _layer(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    if value < 0:
        return None
    return value


def _task(value: object) -> dict[str, Any]:
    row = mapping(value)
    kind = row.get("kind")
    if not isinstance(kind, str) or kind not in {"issue", "pr"}:
        return {"kind": "none", "number": None, "title": None}
    return {"kind": kind, "number": _whole_number(row.get("number")), "title": text(row.get("title"))}


def _worker_task(value: object) -> str | None:
    if isinstance(value, str):
        return text(value)
    title = mapping(value).get("title")
    return text(title)


def _seat_signals(
    roster: Mapping[str, Any],
    harness: Mapping[str, Any],
    occupancy: str | None,
    *,
    intended: str | None,
    seat_present: bool,
    require_liveness: bool,
) -> tuple[str, str, bool | None]:
    pid_alive = resolve_pid(roster.get("pid_alive"), harness)
    state, reason = derive_state(
        intended=intended,
        pid_alive=pid_alive,
        idle_min=resolve_idle_min(roster, harness),
        activity=resolve_activity(roster, harness),
        occupancy=occupancy,
        seat_present=seat_present,
        require_liveness=require_liveness,
    )
    return state, reason, pid_alive


def _driver(
    raw: object,
    harness_doc: dict[str, Any] | None,
    occupancy: Mapping[str, str],
    *,
    intended: str | None,
) -> tuple[dict[str, Any] | None, str, str]:
    roster = mapping(raw)
    agent_id = seat_id(roster.get("agent_id"))
    if agent_id is None:
        state, reason = derive_state(
            intended=intended,
            pid_alive=None,
            idle_min=None,
            activity=None,
            occupancy=None,
            seat_present=False,
            require_liveness=True,
        )
        return None, state, reason
    harness = harness_row(harness_doc, agent_id)
    state, reason, pid_alive = _seat_signals(
        roster,
        harness,
        occupancy.get(agent_id),
        intended=intended,
        seat_present=True,
        require_liveness=True,
    )
    driver = {
        "agent_id": agent_id,
        "cli": text(roster.get("cli")),
        "model": text(roster.get("model")),
        "harness": text(roster.get("harness")),
        "pid_alive": pid_alive,
    }
    return driver, state, reason


def _workers(
    raw: object,
    harness_doc: dict[str, Any] | None,
    occupancy: Mapping[str, str],
    *,
    intended: str | None,
) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    rows: list[dict[str, Any]] = []
    for item in raw:
        try:
            roster = mapping(item)
            agent_id = seat_id(roster.get("agent_id"))
            if agent_id is None:
                continue
            harness = harness_row(harness_doc, agent_id)
            state, reason, _pid = _seat_signals(
                roster,
                harness,
                occupancy.get(agent_id),
                intended=intended,
                seat_present=True,
                require_liveness=False,
            )
            rows.append(
                {
                    "agent_id": agent_id,
                    "cli": text(roster.get("cli")),
                    "model": text(roster.get("model")),
                    "task": _worker_task(roster.get("task")),
                    "state": state,
                    "state_reason": text(reason) or reason,
                    "since": as_timestamp(roster.get("since")),
                }
            )
        except (TypeError, ValueError, OverflowError, ArithmeticError):
            continue
    return rows


def _epic(
    raw: object,
    harness_doc: dict[str, Any] | None,
    occupancy: Mapping[str, str],
) -> dict[str, Any] | None:
    roster = mapping(raw)
    epic_id = seat_id(roster.get("epic"))
    if epic_id is None:
        return None
    intended = text(roster.get("intended"))
    driver, state, reason = _driver(
        roster.get("driver"),
        harness_doc,
        occupancy,
        intended=intended,
    )
    parent = roster.get("parent")
    if isinstance(parent, bool):
        parent_text = None
    elif isinstance(parent, int):
        parent_text = str(parent)
    else:
        parent_text = text(parent)
    return {
        "epic": epic_id,
        "title": text(roster.get("title")),
        "focus": text(roster.get("focus")),
        "parent": parent_text,
        "layer": _layer(roster.get("layer")),
        "intended": intended,
        "state": state,
        "state_reason": text(reason) or reason,
        "since": as_timestamp(roster.get("since")),
        "driver": driver,
        "task": _task(roster.get("task")),
        "workers": _workers(roster.get("workers"), harness_doc, occupancy, intended=intended),
    }


def _agent_from_seat(
    *,
    agent_id: str,
    role: str,
    epic: str | None,
    cli: str | None,
    model: str | None,
    task: str | None,
    state: str,
    reason: str,
    last_seen: str | None,
) -> dict[str, Any]:
    return {
        "agent_id": agent_id,
        "role": role,
        "epic": epic,
        "cli": cli,
        "model": model,
        "task": task,
        "state": state,
        "state_reason": reason,
        "last_seen": last_seen,
    }


def _agents_for_epic(epic: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    driver = epic.get("driver")
    if isinstance(driver, dict) and text(driver.get("agent_id")):
        task = epic.get("task") if isinstance(epic.get("task"), dict) else {}
        task_title = text(task.get("title"))
        rows.append(
            _agent_from_seat(
                agent_id=driver["agent_id"],
                role="driver",
                epic=epic.get("epic"),
                cli=driver.get("cli"),
                model=driver.get("model"),
                task=task_title,
                state=epic["state"],
                reason=epic["state_reason"],
                last_seen=epic.get("since"),
            )
        )
    for worker in epic.get("workers") or []:
        if not isinstance(worker, dict):
            continue
        rows.append(
            _agent_from_seat(
                agent_id=worker["agent_id"],
                role="worker",
                epic=epic.get("epic"),
                cli=worker.get("cli"),
                model=worker.get("model"),
                task=worker.get("task"),
                state=worker["state"],
                reason=worker["state_reason"],
                last_seen=worker.get("since"),
            )
        )
    return rows


def _bots(
    raw: object,
    harness_doc: dict[str, Any] | None,
    occupancy: Mapping[str, str],
) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    rows: list[dict[str, Any]] = []
    for item in raw:
        roster = mapping(item)
        agent_id = seat_id(roster.get("agent_id"))
        if agent_id is None:
            continue
        harness = harness_row(harness_doc, agent_id)
        intended = text(roster.get("intended"))
        state, reason, _pid = _seat_signals(
            roster,
            harness,
            occupancy.get(agent_id),
            intended=intended,
            seat_present=True,
            require_liveness=False,
        )
        rows.append(
            _agent_from_seat(
                agent_id=agent_id,
                role="bot",
                epic=seat_id(roster.get("epic")),
                cli=text(roster.get("cli")),
                model=text(roster.get("model")),
                task=_worker_task(roster.get("task")),
                state=state,
                reason=text(reason) or reason,
                last_seen=as_timestamp(roster.get("last_seen")) or as_timestamp(roster.get("since")),
            )
        )
    return rows


def _attention_item(
    *,
    severity: str,
    kind: str,
    title: str,
    summary: str,
    target_type: str,
    target_id: str,
) -> dict[str, Any]:
    return {
        "severity": severity,
        "kind": kind,
        "title": text(title) or title,
        "summary": text(summary) or summary,
        "target": {"type": target_type, "id": text(target_id) or target_id},
    }


def _driver_attention(epics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for epic in epics:
        state = epic.get("state")
        if state not in {"dead", "stuck"}:
            continue
        title = epic.get("title") or epic["epic"]
        items.append(
            _attention_item(
                severity="bad",
                kind="dead_driver" if state == "dead" else "stuck_driver",
                title=title,
                summary=epic.get("state_reason") or state,
                target_type="epic",
                target_id=epic["epic"],
            )
        )
    return items


def _foundation_attention(raw: object) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    items: list[dict[str, Any]] = []
    for item in raw:
        row = mapping(item)
        if row.get("red") is not True:
            continue
        name = text(row.get("foundation")) or text(row.get("name"))
        if name is None:
            continue
        reasons = row.get("reasons")
        summary = "red"
        if isinstance(reasons, list):
            parts = [part for part in (text(reason) for reason in reasons) if part]
            if parts:
                summary = "; ".join(parts)
        elif isinstance(reasons, str):
            summary = text(reasons) or "red"
        items.append(
            _attention_item(
                severity="bad",
                kind="red_foundation",
                title=name,
                summary=summary,
                target_type="foundation",
                target_id=name,
            )
        )
    return items


def _pr_attention(raw: object, *, stale_after: float) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    items: list[dict[str, Any]] = []
    for item in raw:
        row = mapping(item)
        if row.get("ci") != "green" or row.get("cf_at_head") is not True:
            continue
        queue = text(row.get("mq"))
        if queue is None:
            continue
        token = queue.lower().replace(" ", "_")
        if token.startswith("queued") or token not in _NOT_QUEUED:
            continue
        minutes = finite_number(row.get("unqueued_min"))
        if minutes is None or minutes <= stale_after:
            continue
        number = _whole_number(row.get("number"))
        if number is None:
            continue
        title = text(row.get("title")) or str(number)
        items.append(
            _attention_item(
                severity="warn",
                kind="unqueued_pr",
                title=title,
                summary="green with approval at head and not queued",
                target_type="pr",
                target_id=str(number),
            )
        )
    return items


def _alert_attention(raw: object) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    items: list[dict[str, Any]] = []
    for item in raw:
        row = mapping(item)
        name = text(row.get("name"))
        if name is None:
            continue
        severity_token = (text(row.get("severity")) or "").lower()
        severity = "bad" if severity_token == "critical" else "warn"
        summary = text(row.get("summary")) or name
        items.append(
            _attention_item(
                severity=severity,
                kind="alert",
                title=name,
                summary=summary,
                target_type="alert",
                target_id=name,
            )
        )
    return items


def _usage_attention(raw: object) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    items: list[dict[str, Any]] = []
    for item in raw:
        row = mapping(item)
        used = finite_number(row.get("used_pct"))
        if used is None:
            continue
        name = text(row.get("subscription"))
        if name is None:
            continue
        stop = finite_number(row.get("hard_stop_pct"))
        if stop is None:
            near = used >= USAGE_NEAR_FLOOR
            hard = used >= USAGE_HARD_FLOOR
        else:
            near = used >= stop - USAGE_NEAR_GAP
            hard = used >= stop
        if not near and not hard:
            continue
        items.append(
            _attention_item(
                severity="bad" if hard else "warn",
                kind="usage",
                title=name,
                summary="usage at the hard stop" if hard else "usage near the limit",
                target_type="usage",
                target_id=name,
            )
        )
    return items


def _sort_attention(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        items,
        key=lambda item: (
            _KIND_ORDER.get(item["kind"], 99),
            _SEVERITY_ORDER.get(item["severity"], 99),
            item["title"],
            item["target"]["id"],
        ),
    )


def load_board(environ: Mapping[str, str] | None = None) -> Board:
    """Build epics, agents, and attention. Collector failures stay in sources."""
    clock = utc_now()
    roster_report, roster = load_snapshot(
        source_name="roster_snapshot",
        env_var="FLEET_ROSTER_SNAPSHOT",
        environ=environ,
        now=clock,
    )
    harness_report, harness = load_snapshot(
        source_name="harness_snapshot",
        env_var="FLEET_HARNESS_SNAPSHOT",
        environ=environ,
        now=clock,
    )
    try:
        delegate_report = load_delegate_health()
    except Exception:
        delegate_report = report("delegate", "unavailable")
    try:
        occupancy_report, occupancy = load_occupancy_activity()
    except Exception:
        occupancy_report, occupancy = report("occupancy", "unavailable"), {}

    # Retain stale snapshot payloads, but only fresh harness fields override seats.
    if harness_report.status != "ok":
        harness = None
    document = roster or {}
    epic_rows = document.get("epics")
    epics = []
    if isinstance(epic_rows, list):
        for item in epic_rows:
            try:
                built = _epic(item, harness, occupancy)
            except (TypeError, ValueError, OverflowError, ArithmeticError):
                continue
            if built is not None:
                epics.append(built)

    agents: list[dict[str, Any]] = []
    seen: set[str] = set()
    for epic in epics:
        for agent in _agents_for_epic(epic):
            if agent["agent_id"] in seen:
                continue
            seen.add(agent["agent_id"])
            agents.append(agent)
    for agent in _bots(document.get("bots"), harness, occupancy):
        if agent["agent_id"] in seen:
            continue
        seen.add(agent["agent_id"])
        agents.append(agent)

    attention_parts: list[dict[str, Any]] = []
    for builder in (
        lambda: _driver_attention(epics),
        lambda: _foundation_attention(document.get("foundations")),
        lambda: _pr_attention(document.get("prs"), stale_after=pr_stale_minutes(environ)),
        lambda: _alert_attention(document.get("alerts")),
        lambda: _usage_attention(document.get("usage")),
    ):
        try:
            attention_parts.extend(builder())
        except (TypeError, ValueError, OverflowError, ArithmeticError):
            continue
    attention = _sort_attention(attention_parts)
    try:
        base = collect_source_reports(environ)
    except Exception:
        base = (report("sources", "unavailable"),)
    sources = _overlay_sources(
        base,
        {"roster_snapshot": roster_report, "harness_snapshot": harness_report},
        (delegate_report, occupancy_report),
    )
    return Board(sources=sources, epics=epics, agents=agents, attention=attention)
