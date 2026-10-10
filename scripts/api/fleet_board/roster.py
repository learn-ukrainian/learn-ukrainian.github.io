"""Roster projection from the snapshot named by ``FLEET_ROSTER_SNAPSHOT``.

The file is read only when that variable is set. Its location is never copied
into a response. A missing, unreadable, or non-object document degrades the
source to ``unavailable`` and still returns the empty roster shape.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..opsec_scan import scan_text
from .envelope import TIMESTAMP_PATTERN
from .sources import SourceReport, report

SOURCE_NAME = "roster_snapshot"
STALE_INTERVAL_MULTIPLIER = 2
_TIMESTAMP = re.compile(TIMESTAMP_PATTERN)
_TOKEN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
_LOCATION = re.compile(r"://|^/|^\\\\|[A-Za-z0-9.-]+:\d{2,5}")
# A slash, a home prefix, a drive prefix, or a UNC prefix. Ordinary words that
# contain a slash between letters stay publishable.
_ABSOLUTE = re.compile(r"(?<![A-Za-z0-9])(?:\\\\|//|~[/\\\\]|[A-Za-z]:[\\\\/]|/)")
# Dotted names whose labels start with a letter and whose last label is letters only.
_HOSTNAME = re.compile(
    r"(?i)(?<![A-Za-z0-9_-])"
    r"(?:[A-Za-z](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+"
    r"[A-Za-z]{2,63}"
    r"(?![A-Za-z0-9_-])"
)
_TEXT_LIMIT = 400
_KNOWN_STATES = frozenset({"working", "idle", "stuck", "dead", "paused", "off"})
_FOUNDATION_ORDER = {"codebase": 0, "data": 1}
_LAYER_KINDS = (
    (0, "foundations"),
    (1, "consumers"),
    (None, "postponed"),
)


@dataclass(frozen=True)
class RosterRead:
    data: dict[str, Any]
    source: SourceReport


def _now() -> datetime:
    return datetime.now(UTC)


def empty_roster() -> dict[str, Any]:
    return {
        "layers": [{"layer": layer, "kind": kind, "epics": []} for layer, kind in _LAYER_KINDS],
        "foundation_status": [],
        "active_alerts": [],
    }


def _token(raw: Any) -> str | None:
    if not isinstance(raw, str):
        return None
    text = raw.strip()
    if _TOKEN.fullmatch(text) is None:
        return None
    return text


def _timestamp(raw: Any) -> str | None:
    if not isinstance(raw, str) or _TIMESTAMP.fullmatch(raw) is None:
        return None
    return raw


def _public_text(raw: Any) -> str | None:
    if not isinstance(raw, str):
        return None
    text = raw.strip()
    if not text or len(text) > _TEXT_LIMIT:
        return None
    if _LOCATION.search(text) is not None or _ABSOLUTE.search(text) is not None:
        return None
    if _HOSTNAME.search(text) is not None or scan_text(text):
        return None
    return text


def _flag_value(raw: Any) -> bool | str:
    """Booleans pass through. Every other value is ``unknown``, never true."""
    if raw is True or raw is False:
        return raw
    return "unknown"


def _red(raw: Any) -> bool | None:
    if raw is True or raw is False:
        return raw
    return None


def _parse_time(raw: str) -> datetime | None:
    try:
        parsed = datetime.strptime(raw, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    except ValueError:
        return None
    return parsed


def _age_s(payload: Mapping[str, Any], now: datetime) -> float | None:
    stamp = _timestamp(payload.get("generated_at"))
    if stamp is None:
        return None
    parsed = _parse_time(stamp)
    if parsed is None:
        return None
    return max(0.0, (now - parsed).total_seconds())


def _is_stale(payload: Mapping[str, Any], age_s: float | None) -> bool:
    if age_s is None:
        return False
    interval = payload.get("interval_s")
    if isinstance(interval, bool) or not isinstance(interval, (int, float)):
        return False
    if not math.isfinite(float(interval)) or interval <= 0:
        return False
    return age_s > STALE_INTERVAL_MULTIPLIER * float(interval)


def _kind(item: Mapping[str, Any]) -> str | None:
    if item.get("postponed") is True:
        return "postponed"
    layer = item.get("layer")
    if layer == "postponed":
        return "postponed"
    if layer in (0, "0"):
        return "foundations"
    if layer in (1, "1"):
        return "consumers"
    role = item.get("role")
    if role == "foundation":
        return "foundations"
    if role == "consumer":
        return "consumers"
    return None


def _state(item: Mapping[str, Any], kind: str) -> str | None:
    if kind == "postponed":
        return "off"
    raw = item.get("state")
    if isinstance(raw, str) and raw in _KNOWN_STATES:
        return raw
    return None


def _depends_on(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    seen: set[str] = set()
    rows: list[str] = []
    for item in raw:
        token = _token(item)
        if token is None or token in seen:
            continue
        seen.add(token)
        rows.append(token)
    return rows


def _flags(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    rows: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, Mapping):
            continue
        name = _token(item.get("name"))
        if name is None:
            continue
        rows.append(
            {
                "name": name,
                "value": _flag_value(item.get("value")),
                "source": _token(item.get("source")),
                "checked_at": _timestamp(item.get("checked_at")),
            }
        )
    return rows


def _epic(item: Mapping[str, Any], kind: str) -> dict[str, Any] | None:
    name = _token(item.get("epic"))
    if name is None:
        name = _token(item.get("id"))
    if name is None:
        return None
    return {
        "epic": name,
        "depends_on": _depends_on(item.get("depends_on")),
        "restart_condition": _public_text(item.get("restart_condition")),
        "state": _state(item, kind),
        "flags": _flags(item.get("flags")),
    }


def _sort_epics(kind: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if kind == "foundations":
        return sorted(rows, key=lambda row: (_FOUNDATION_ORDER.get(row["epic"], 50), row["epic"]))
    return sorted(rows, key=lambda row: row["epic"])


def _foundation_rows(raw: Any, derived: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, Mapping):
                continue
            name = _token(item.get("foundation"))
            if name is None or name in seen:
                continue
            seen.add(name)
            reasons: list[str] = []
            raw_reasons = item.get("reasons")
            if isinstance(raw_reasons, list):
                for reason in raw_reasons:
                    text = _public_text(reason)
                    if text is not None:
                        reasons.append(text)
            rows.append({"foundation": name, "red": _red(item.get("red")), "reasons": reasons})
    if rows:
        return rows
    return [{"foundation": name, "red": None, "reasons": []} for name in derived]


def _alerts(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, Mapping):
            continue
        name = _token(item.get("name"))
        if name is None or name in seen:
            continue
        seen.add(name)
        rows.append({"name": name, "summary": _public_text(item.get("summary"))})
    return rows


def project_roster(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Map a snapshot object onto the roster document. Unknown keys are dropped."""
    grouped: dict[str, list[dict[str, Any]]] = {kind: [] for _, kind in _LAYER_KINDS}
    seen: set[str] = set()
    raw_epics = payload.get("epics")
    if isinstance(raw_epics, list):
        for item in raw_epics:
            if not isinstance(item, Mapping):
                continue
            kind = _kind(item)
            if kind is None:
                continue
            epic = _epic(item, kind)
            if epic is None or epic["epic"] in seen:
                continue
            seen.add(epic["epic"])
            grouped[kind].append(epic)
    foundation_names = [row["epic"] for row in _sort_epics("foundations", grouped["foundations"])]
    data = empty_roster()
    for layer in data["layers"]:
        layer["epics"] = _sort_epics(layer["kind"], grouped[layer["kind"]])
    data["foundation_status"] = _foundation_rows(payload.get("foundations"), foundation_names)
    alerts = payload.get("alerts")
    if not isinstance(alerts, list):
        alerts = payload.get("active_alerts")
    data["active_alerts"] = _alerts(alerts)
    return data


def load_roster(location: str | None, *, now: datetime | None = None) -> RosterRead:
    """Read one snapshot. Never raises. ``location`` is not returned."""
    moment = now or _now()
    if location is None:
        return RosterRead(empty_roster(), report(SOURCE_NAME, "not_configured"))
    try:
        payload = json.loads(Path(location).read_text(encoding="utf-8"))
    except Exception:
        return RosterRead(empty_roster(), report(SOURCE_NAME, "unavailable"))
    if not isinstance(payload, Mapping):
        return RosterRead(empty_roster(), report(SOURCE_NAME, "unavailable"))
    try:
        data = project_roster(payload)
        age = _age_s(payload, moment)
        status = "stale" if _is_stale(payload, age) else "ok"
        return RosterRead(data, report(SOURCE_NAME, status, age_s=age))
    except Exception:
        return RosterRead(empty_roster(), report(SOURCE_NAME, "unavailable"))
