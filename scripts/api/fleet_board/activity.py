"""Seat state, pull-request idle time, blockers, and throughput.

Liveness is the roster or fresh harness process flag. Delegate collection
reports source health only: task rows have no approved seat identity binding.
Screen text is never an input. A missing number stays None.
"""

from __future__ import annotations

import json
import math
import os
import re
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from scripts.api.delegate_router import seat_delegate_tasks
from scripts.api.epics_router import _response_registry_text
from scripts.api.occupancy import occupancy_payload

from .snapshot import finite_number, mapping
from .sources import SourceReport, read_location, report

STATES = frozenset({"working", "idle", "stuck", "dead", "paused", "off"})
STUCK_IDLE_MIN = 30.0
ACTIVITY_TOKENS = frozenset({"working", "idle"})


def load_delegate_health() -> SourceReport:
    """Report collector health without interpreting unbound task identities."""
    try:
        payload = seat_delegate_tasks()
    except Exception:
        return report("delegate", "unavailable")
    return report("delegate", "ok" if isinstance(payload, dict) else "unavailable")


def _occupant_activity(status: object) -> str | None:
    """Explicit activity only. Presence without a status is not working."""
    if not isinstance(status, str):
        return None
    token = status.strip().lower()
    if token in ACTIVITY_TOKENS:
        return token
    return None


def _observation_age(host: Mapping[str, Any]) -> float | None:
    age = host.get("age_seconds")
    if isinstance(age, bool) or not isinstance(age, (int, float)):
        return None
    try:
        number = float(age)
    except (OverflowError, ValueError):
        return None
    if not math.isfinite(number) or number < 0:
        return None
    return number


def load_occupancy_activity() -> tuple[SourceReport, dict[str, str]]:
    """Working or idle per agent id. Host identity is not copied out.

    Only fresh hosts contribute explicit working/idle activity. With no fresh
    host, retained stale observations report ``stale``; otherwise failed
    observations report ``unavailable`` with unknown age. An empty valid host
    collection is ``ok`` with no activity.
    """
    try:
        payload = occupancy_payload()
    except Exception:
        return report("occupancy", "unavailable"), {}
    if not isinstance(payload, dict):
        return report("occupancy", "unavailable"), {}
    hosts = payload.get("hosts")
    if not isinstance(hosts, dict):
        return report("occupancy", "unavailable"), {}
    activity: dict[str, str] = {}
    saw_fresh = False
    saw_stale = False
    saw_unavailable = False
    stale_age: float | None = None
    for host in hosts.values():
        if not isinstance(host, dict):
            saw_unavailable = True
            continue
        status = host.get("status")
        if status == "stale":
            saw_stale = True
            age = _observation_age(host)
            if age is not None and (stale_age is None or age > stale_age):
                stale_age = age
            continue
        if status != "fresh":
            saw_unavailable = True
            continue
        saw_fresh = True
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
    if saw_stale and not saw_fresh:
        return report("occupancy", "stale", age_s=stale_age), {}
    if saw_unavailable and not saw_fresh:
        return report("occupancy", "unavailable"), {}
    return report("occupancy", "ok"), activity


def activity_token(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    token = value.strip().lower()
    if token in ACTIVITY_TOKENS:
        return token
    return None


def text(value: object) -> str | None:
    """Project one emitted string through the epic-registry public-text bound."""
    if not isinstance(value, str):
        return None
    return _response_registry_text(value)


def seat_id(value: object) -> str | None:
    """An identity string. A redacted value is omitted rather than published."""
    projected = text(value)
    if not projected or projected == "[redacted]":
        return None
    return projected


def derive_state(
    *,
    intended: str | None,
    pid_alive: bool | None,
    idle_min: float | None,
    activity: str | None,
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
    if pid_alive is False:
        return "dead", "process is not alive"
    if not seat_present and norm == "running":
        return "stuck", "no driver while intended running"
    long_idle = idle_min is not None and idle_min >= STUCK_IDLE_MIN
    if norm == "running" and long_idle:
        return "stuck", "idle while intended running"
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
        h_idle = finite_number(harness.get("idle_min"))
        if h_idle is not None:
            return h_idle
    if "idle_min" in roster:
        return finite_number(roster.get("idle_min"))
    return None


def resolve_activity(roster: Mapping[str, Any], harness: Mapping[str, Any]) -> str | None:
    if "activity" in harness:
        h_act = activity_token(harness.get("activity"))
        if h_act is not None:
            return h_act
    if "activity" in roster:
        return activity_token(roster.get("activity"))
    return None


STALE_PR_SOURCE = "stale_prs"
STALE_PR_ENV = "FLEET_STALE_PR_STATE"
STALE_PR_FRESH_S = 900.0
WINDOW_DAYS = 14
MAX_RECORD_BYTES = 1_000_000

_LANE = re.compile(r"^[a-z][a-z0-9_-]{0,40}\Z")
_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
_DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")
_NUMBER_KEY = re.compile(r"^[1-9][0-9]{0,8}\Z")
_BASE_STATES = frozenset({"open", "closed", "unmerged", "merged"})
_ACTIVITY_KEYS = frozenset({"commit_at", "cf_at", "merge_event_at", "owner_lane", "base"})
_EVENT_KEYS = frozenset({"date", "repo", "owner_lane", "opened", "merged"})


class _Rejected(Exception):
    """The optional record is present but not usable. The detail stays local."""


@dataclass(frozen=True)
class PrActivity:
    commit_at: datetime | None = None
    cf_at: datetime | None = None
    merge_event_at: datetime | None = None
    owner_lane: str | None = None
    base_number: int | None = None
    base_state: str | None = None


@dataclass(frozen=True)
class ThroughputEvent:
    date: str
    repo: str
    owner_lane: str | None
    opened: int
    merged: int


@dataclass(frozen=True)
class StaleSnapshot:
    usable: bool
    activity: Mapping[int, PrActivity]
    events: tuple[ThroughputEvent, ...]


def lane_token(value: object) -> str | None:
    """A lane name, or None when the value is not one."""
    if not isinstance(value, str):
        return None
    token = value.strip().casefold()
    if not _LANE.fullmatch(token):
        return None
    return token


def lane_from_ref(head_ref: str) -> str | None:
    """The lane named by the first segment of a head branch."""
    if "/" not in head_ref:
        return None
    return lane_token(head_ref.split("/", 1)[0])


def hours_idle(moment: datetime, *stamps: datetime | None) -> tuple[float | None, bool, bool]:
    """Hours since the latest known event, plus the 24h and 48h flags.

    The hour value is truncated to a tenth. A missing set of times is null
    and both flags are false. A future stamp counts as zero hours.
    """
    known = [stamp for stamp in stamps if stamp is not None]
    if not known:
        return None, False, False
    seconds = (moment - max(known)).total_seconds()
    if seconds < 0:
        seconds = 0
    hours = int(seconds // 360) / 10
    return hours, hours >= 24, hours >= 48


def attention_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Open pull requests that have been idle for at least 24 hours."""
    stuck = [
        row
        for row in rows
        if row.get("idle_24h") is True
        and isinstance(row.get("hours_idle"), (int, float))
        and type(row.get("number")) is int
    ]
    stuck.sort(key=lambda row: (-float(row["hours_idle"]), int(row["number"])))
    return [
        {
            "number": row["number"],
            "repo": row["repo"],
            "title": row["title"],
            "owner_lane": row.get("owner_lane"),
            "hours_idle": row["hours_idle"],
            "idle_24h": True,
            "idle_48h": row.get("idle_48h") is True,
            "blocker": row["blocker"],
        }
        for row in stuck
    ]


def _empty_days(count: int) -> list[list[int]]:
    return [[0, 0] for _ in range(count)]


def build_stats(
    rows: Sequence[Mapping[str, Any]],
    events: Sequence[ThroughputEvent],
    *,
    now: datetime,
) -> dict[str, Any]:
    """Opened and merged counts for the last 14 UTC days, plus the open backlog."""
    end = now.astimezone(UTC).date()
    dates = [(end - timedelta(days=offset)).isoformat() for offset in range(WINDOW_DAYS - 1, -1, -1)]
    index = {day: position for position, day in enumerate(dates)}
    repo_backlog: dict[str, int] = defaultdict(int)
    lane_backlog: dict[str | None, int] = defaultdict(int)
    for row in rows:
        repo = row.get("repo")
        if not isinstance(repo, str) or not repo:
            continue
        repo_backlog[repo] += 1
        lane = row.get("owner_lane")
        lane_backlog[lane if isinstance(lane, str) or lane is None else None] += 1

    repo_days: dict[str, list[list[int]]] = defaultdict(lambda: _empty_days(WINDOW_DAYS))
    lane_days: dict[str | None, list[list[int]]] = defaultdict(lambda: _empty_days(WINDOW_DAYS))
    for event in events:
        position = index.get(event.date)
        if position is None:
            continue
        repo_days[event.repo][position][0] += event.opened
        repo_days[event.repo][position][1] += event.merged
        lane_days[event.owner_lane][position][0] += event.opened
        lane_days[event.owner_lane][position][1] += event.merged

    def series(pairs: list[list[int]]) -> list[dict[str, Any]]:
        return [
            {"date": day, "opened": pair[0], "merged": pair[1]}
            for day, pair in zip(dates, pairs, strict=True)
        ]

    by_repo = [
        {
            "repo": repo,
            "backlog": repo_backlog.get(repo, 0),
            "days": series(repo_days.get(repo, _empty_days(WINDOW_DAYS))),
        }
        for repo in sorted(set(repo_backlog) | set(repo_days))
    ]
    lanes = set(lane_backlog) | set(lane_days)
    by_lane = [
        {
            "owner_lane": lane,
            "backlog": lane_backlog.get(lane, 0),
            "days": series(lane_days.get(lane, _empty_days(WINDOW_DAYS))),
        }
        for lane in sorted(lanes, key=lambda item: (item is None, item or ""))
    ]
    return {"window_days": WINDOW_DAYS, "by_repo": by_repo, "by_lane": by_lane}


def _parse_time(value: str) -> datetime | None:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            return None
        return parsed.astimezone(UTC)
    except (ValueError, OverflowError):
        return None


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _Rejected
        result[key] = value
    return result


def _optional_time(value: object) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise _Rejected
    parsed = _parse_time(value)
    if parsed is None:
        raise _Rejected
    return parsed


def _optional_lane(value: object) -> str | None:
    if value is None:
        return None
    token = lane_token(value)
    if token is None:
        raise _Rejected
    return token


def _count(value: object) -> int:
    if type(value) is not int or value < 0:
        raise _Rejected
    return value


def _activity_item(raw: object) -> PrActivity:
    if not isinstance(raw, dict) or set(raw) - _ACTIVITY_KEYS:
        raise _Rejected
    base_number = None
    base_state = None
    if "base" in raw and raw["base"] is not None:
        base = raw["base"]
        if not isinstance(base, dict) or set(base) != {"number", "state"}:
            raise _Rejected
        number = base["number"]
        state = base["state"]
        if type(number) is not int or number < 1 or state not in _BASE_STATES:
            raise _Rejected
        base_number = number
        base_state = state
    return PrActivity(
        commit_at=_optional_time(raw["commit_at"]) if "commit_at" in raw else None,
        cf_at=_optional_time(raw["cf_at"]) if "cf_at" in raw else None,
        merge_event_at=_optional_time(raw["merge_event_at"]) if "merge_event_at" in raw else None,
        owner_lane=_optional_lane(raw["owner_lane"]) if "owner_lane" in raw else None,
        base_number=base_number,
        base_state=base_state,
    )


def _event(raw: object) -> ThroughputEvent:
    if not isinstance(raw, dict) or set(raw) != _EVENT_KEYS:
        raise _Rejected
    date = raw["date"]
    repo = raw["repo"]
    if not isinstance(date, str) or not _DATE.fullmatch(date):
        raise _Rejected
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError as exc:
        raise _Rejected from exc
    if not isinstance(repo, str) or not _REPO.fullmatch(repo):
        raise _Rejected
    return ThroughputEvent(
        date=date,
        repo=repo,
        owner_lane=_optional_lane(raw["owner_lane"]),
        opened=_count(raw["opened"]),
        merged=_count(raw["merged"]),
    )


def _payload(raw: object) -> StaleSnapshot:
    if not isinstance(raw, dict) or raw.get("version") != 1 or set(raw) - {"version", "activity", "throughput"}:
        raise _Rejected
    activity: dict[int, PrActivity] = {}
    recorded = raw.get("activity", {})
    if not isinstance(recorded, dict):
        raise _Rejected
    for key, value in recorded.items():
        if not isinstance(key, str) or not _NUMBER_KEY.fullmatch(key):
            raise _Rejected
        activity[int(key)] = _activity_item(value)
    events_raw = raw.get("throughput", [])
    if not isinstance(events_raw, list):
        raise _Rejected
    events = tuple(_event(item) for item in events_raw)
    return StaleSnapshot(True, activity, events)


def _file_age(path: Path, now: datetime) -> float:
    modified = datetime.fromtimestamp(path.stat().st_mtime, UTC)
    return max(0.0, (now - modified).total_seconds())


def read_stale_state(
    environ: Mapping[str, str] | None = None,
    *,
    now: datetime | None = None,
) -> tuple[SourceReport, StaleSnapshot]:
    """Read ``FLEET_STALE_PR_STATE``. Unset is not configured; a bad record is unavailable."""
    empty = StaleSnapshot(False, {}, ())
    location = read_location(STALE_PR_ENV, environ)
    if location is None:
        return report(STALE_PR_SOURCE, "not_configured"), empty
    moment = now or datetime.now(UTC)
    path = Path(location)
    try:
        if not path.is_file():
            return report(STALE_PR_SOURCE, "unavailable"), empty
        if path.stat().st_size > MAX_RECORD_BYTES:
            return report(STALE_PR_SOURCE, "unavailable"), empty
        payload = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique)
        snapshot = _payload(payload)
        age = _file_age(path, moment)
    except (_Rejected, OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError, OverflowError):
        return report(STALE_PR_SOURCE, "unavailable"), empty
    status = "stale" if age > STALE_PR_FRESH_S else "ok"
    return report(STALE_PR_SOURCE, status, age_s=age), snapshot
