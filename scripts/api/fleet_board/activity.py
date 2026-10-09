"""Seat state from snapshots plus delegate and occupancy records.

Liveness is the process flag on the roster or harness snapshot, or the
alive flag already computed by the delegate collector. Screen text is
never an input. A missing number stays None.
"""

from __future__ import annotations

import math
import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from scripts.api.delegate_router import active_delegate_tasks
from scripts.api.occupancy import occupancy_payload

from .snapshot import finite_number, mapping
from .sources import SourceReport, report

STATES = frozenset({"working", "idle", "stuck", "dead", "paused", "off"})
STUCK_IDLE_MIN = 30.0
WORKING_DELEGATE_STATUSES = frozenset({"running", "spawning"})
ACTIVITY_TOKENS = frozenset({"working", "idle"})


@dataclass(frozen=True)
class DelegateFact:
    alive: bool | None
    status: str | None


def _delegate_dead(fact: DelegateFact | None) -> bool:
    if fact is None:
        return False
    if fact.status == "zombie":
        return True
    return fact.alive is False and fact.status == "running"


def _delegate_working(fact: DelegateFact | None) -> bool:
    if fact is None or _delegate_dead(fact):
        return False
    return fact.alive is True and fact.status in WORKING_DELEGATE_STATUSES


def _merge_delegate(current: DelegateFact | None, incoming: DelegateFact) -> DelegateFact:
    if current is not None and _delegate_dead(current):
        return current
    if _delegate_dead(incoming):
        return incoming
    if current is not None and _delegate_working(current):
        return current
    if _delegate_working(incoming):
        return incoming
    return current or incoming


def load_delegate_facts() -> tuple[SourceReport, dict[str, DelegateFact]]:
    """Active delegate rows keyed by agent id. A failure is ``unavailable``."""
    try:
        payload = active_delegate_tasks()
    except Exception:
        return report("delegate", "unavailable"), {}
    if not isinstance(payload, dict):
        return report("delegate", "unavailable"), {}
    tasks = payload.get("tasks")
    if not isinstance(tasks, list):
        return report("delegate", "ok"), {}
    facts: dict[str, DelegateFact] = {}
    for task in tasks:
        if not isinstance(task, dict):
            continue
        agent = task.get("agent")
        if not isinstance(agent, str) or not agent.strip():
            continue
        alive = task.get("alive") if isinstance(task.get("alive"), bool) else None
        status = task.get("status") if isinstance(task.get("status"), str) else None
        agent_id = agent.strip()
        facts[agent_id] = _merge_delegate(facts.get(agent_id), DelegateFact(alive, status))
    return report("delegate", "ok"), facts


def _occupant_activity(status: object) -> str | None:
    if status is None:
        return "working"
    if not isinstance(status, str):
        return None
    token = status.strip().lower()
    if token == "idle":
        return "idle"
    if token in {"working", "running", "live", "active"}:
        return "working"
    return None


def load_occupancy_activity() -> tuple[SourceReport, dict[str, str]]:
    """Working or idle per agent id. Host identity is not copied out."""
    try:
        payload = occupancy_payload()
    except Exception:
        return report("occupancy", "unavailable"), {}
    if not isinstance(payload, dict):
        return report("occupancy", "unavailable"), {}
    hosts = payload.get("hosts")
    if not isinstance(hosts, dict):
        return report("occupancy", "ok"), {}
    activity: dict[str, str] = {}
    for host in hosts.values():
        if not isinstance(host, dict):
            continue
        occupants = host.get("occupants")
        if not isinstance(occupants, list):
            continue
        for occupant in occupants:
            if not isinstance(occupant, dict):
                continue
            agent = occupant.get("agent")
            if not isinstance(agent, str) or not agent.strip():
                continue
            token = _occupant_activity(occupant.get("status"))
            if token is None:
                continue
            agent_id = agent.strip()
            if activity.get(agent_id) == "working":
                continue
            activity[agent_id] = token
    return report("occupancy", "ok"), activity


def activity_token(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    token = value.strip().lower()
    if token in ACTIVITY_TOKENS:
        return token
    return None


def text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def derive_state(
    *,
    intended: str | None,
    pid_alive: bool | None,
    idle_min: float | None,
    activity: str | None,
    delegate: DelegateFact | None,
    occupancy: str | None,
    seat_present: bool,
    require_liveness: bool,
) -> tuple[str, str]:
    """One of the six states, always with a reason."""
    norm = (intended or "").strip().lower()
    if norm in {"off", "postponed"}:
        reason = "postponed" if norm == "postponed" else "off by roster"
        return "off", reason
    if norm == "paused":
        return "paused", "paused by roster"
    if pid_alive is False or _delegate_dead(delegate):
        return "dead", "process is not alive"
    if not seat_present and norm == "running":
        return "stuck", "no driver while intended running"
    long_idle = idle_min is not None and idle_min >= STUCK_IDLE_MIN
    if norm == "running" and long_idle:
        return "stuck", "idle while intended running"
    if _delegate_working(delegate):
        return "working", "active task"
    if activity == "working" or occupancy == "working":
        return "working", "recorded working"
    if require_liveness and norm == "running" and pid_alive is None:
        return "stuck", "liveness unknown"
    return "idle", "idle"


def pr_stale_minutes(environ: Mapping[str, str] | None = None) -> float:
    """Minutes a green, approved, unqueued PR must exceed before it is flagged."""
    source = os.environ if environ is None else environ
    raw = source.get("FLEET_PR_STALE_MIN")
    if raw is None or not str(raw).strip():
        return 60.0
    try:
        value = float(str(raw).strip())
    except ValueError:
        return 60.0
    if not math.isfinite(value) or value < 0:
        return 60.0
    return value


def harness_row(snapshot: dict[str, Any] | None, agent_id: str) -> dict[str, Any]:
    if not snapshot:
        return {}
    agents = snapshot.get("agents")
    if isinstance(agents, dict):
        return mapping(agents.get(agent_id))
    if isinstance(agents, list):
        for item in agents:
            row = mapping(item)
            if row.get("agent_id") == agent_id:
                return row
    return {}


def resolve_pid(roster_pid: object, harness: Mapping[str, Any]) -> bool | None:
    """Process flag. A harness bool wins. Anything else stays unknown."""
    if "pid_alive" in harness and isinstance(harness.get("pid_alive"), bool):
        return harness.get("pid_alive")
    if isinstance(roster_pid, bool):
        return roster_pid
    return None


def resolve_idle_min(roster: Mapping[str, Any], harness: Mapping[str, Any]) -> float | None:
    if "idle_min" in harness:
        return finite_number(harness.get("idle_min"))
    if "idle_min" in roster:
        return finite_number(roster.get("idle_min"))
    return None


def resolve_activity(roster: Mapping[str, Any], harness: Mapping[str, Any]) -> str | None:
    if "activity" in harness:
        return activity_token(harness.get("activity"))
    if "activity" in roster:
        return activity_token(roster.get("activity"))
    return None
