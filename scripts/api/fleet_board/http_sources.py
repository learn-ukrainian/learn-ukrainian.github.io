"""Alertmanager, Prometheus, and Grafana reads for the fleet board."""

from __future__ import annotations

import ipaddress
import math
import re
import urllib.parse
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor, wait
from typing import Any

from .fetch import HTTP_TIMEOUT_S, fetch_json, join_url
from .sources import read_location
from .values import (
    Outcome,
    _cached_call,
    _done,
    _env,
    _json_number,
    _number,
    _timestamp,
    _token,
)

_ALERT_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,63}\Z")
_URL = re.compile(r"https?://\S+", re.IGNORECASE)
_HOST = re.compile(
    r"\b(?:[a-z0-9_](?:[a-z0-9_-]{0,62}[a-z0-9_])?\.)+[a-z0-9-]{2,}\b",
    re.IGNORECASE,
)
_PATH = re.compile(r"(?:~|\.{1,2})?/(?:[A-Za-z0-9._-]+/?)+|(?:[A-Za-z]:\\(?:[^\\\s]+\\)*[^\\\s]+)")
_USER_HOST = re.compile(r"\b[A-Za-z0-9_.+-]+@[A-Za-z0-9.-]+\b")
_MEASURE = re.compile(
    r"\d+(?:[.,]\d+)?\s*(?:%|percent|pct|bytes?|[kmgtpe]i?b|[kmgtpe]i)\b",
    re.IGNORECASE,
)
_ADDRESS = re.compile(r"(?<![A-Za-z0-9])(?:\[[0-9A-Fa-f:.%]+\]|[0-9A-Fa-f:.]+)(?![A-Za-z0-9])")

# Fixed instant queries. The client cannot add or replace these.
STAT_QUERIES: tuple[tuple[str, str], ...] = (
    ("disk_pct", "fleet_disk_used_percent"),
    ("memory_pct", "fleet_memory_used_percent"),
    ("drivers_live", "fleet_drivers_live"),
    ("probe_status", "fleet_api_probe_up"),
)
DASHBOARDS: tuple[tuple[str, str], ...] = (
    ("overview", "d/overview"),
    ("fleet", "d/fleet"),
)


def _alert_name(value: object) -> str | None:
    """Publish an alert name only when it is a plain identifier."""
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not _ALERT_NAME.fullmatch(text) or _MEASURE.search(text):
        return None
    return text


def _without_addresses(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        token = match.group(0).strip("[]")
        token = token.split("%", 1)[0]
        candidates = [token]
        if ":" in token:
            candidates.append(token.rsplit(":", 1)[0])
        for candidate in candidates:
            try:
                ipaddress.ip_address(candidate)
            except ValueError:
                continue
            return " "
        return match.group(0)

    return _ADDRESS.sub(replace, text)


def _summary(value: object) -> str | None:
    """Publish a short plain-text summary."""
    if not isinstance(value, str):
        return None
    text = _URL.sub(" ", value)
    text = _without_addresses(text)
    text = _USER_HOST.sub(" ", text)
    text = _HOST.sub(" ", text)
    text = _PATH.sub(" ", text)
    text = _MEASURE.sub(" ", text)
    text = "".join(char for char in text if char.isprintable())
    text = " ".join(text.split())
    if not text or _HOST.search(text) or _PATH.search(text) or _MEASURE.search(text):
        return None
    return text[:240]


def _alerts(payload: object) -> list[dict[str, Any]]:
    if not isinstance(payload, list):
        raise ValueError
    rows: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        labels = item.get("labels") if isinstance(item.get("labels"), dict) else {}
        notes = item.get("annotations") if isinstance(item.get("annotations"), dict) else {}
        status = item.get("status") if isinstance(item.get("status"), dict) else {}
        rows.append(
            {
                "name": _alert_name(labels.get("alertname")),
                "severity": _token(labels.get("severity")),
                "summary": _summary(notes.get("summary")),
                "starts_at": _timestamp(item.get("startsAt")),
                "state": _token(status.get("state")),
            }
        )
    return rows


def load_alerts(environ: Mapping[str, str] | None = None) -> Outcome:
    """Alertmanager v2 alerts, reduced to name, severity, summary, start, and state."""
    location = read_location("FLEET_ALERTMANAGER_URL", _env(environ))
    if location is None:
        return _done("alerts", {"alerts": []}, "not_configured")
    try:
        url = join_url(location, "api/v2/alerts")
    except ValueError:
        return _done("alerts", {"alerts": []}, "unavailable")

    def load() -> list[dict[str, Any]]:
        return _alerts(fetch_json(url, timeout_s=HTTP_TIMEOUT_S))

    try:
        alerts, freshness, age = _cached_call("alerts", url, load, cacheable=lambda _value: True)
    except Exception:
        return _done("alerts", {"alerts": []}, "unavailable")
    status = "stale" if freshness == "stale" else "ok"
    return _done("alerts", {"alerts": alerts}, status, age_s=age)


def _vector_value(payload: object) -> float | None:
    if not isinstance(payload, dict) or payload.get("status") != "success":
        return None
    data = payload.get("data")
    if not isinstance(data, dict) or data.get("resultType") != "vector":
        return None
    result = data.get("result")
    if not isinstance(result, list) or len(result) != 1 or not isinstance(result[0], dict):
        return None
    value = result[0].get("value")
    if not isinstance(value, list) or len(value) < 2:
        return None
    raw = value[1]
    if isinstance(raw, str):
        try:
            number = float(raw)
        except ValueError:
            return None
        if not math.isfinite(number):
            return None
        return number
    return _number(raw)


def _blank_stat(name: str) -> dict[str, Any]:
    return {"name": name, "value": None, "status": "unavailable"}


def empty_stats() -> dict[str, Any]:
    return {"stats": [_blank_stat(name) for name, _query in STAT_QUERIES]}


def _query_one(base: str, name: str, query: str) -> tuple[str, dict[str, Any], bool]:
    try:
        url = join_url(base, "api/v1/query") + "?" + urllib.parse.urlencode({"query": query})
        payload = fetch_json(url, timeout_s=HTTP_TIMEOUT_S)
    except Exception:
        return name, _blank_stat(name), True
    number = _vector_value(payload)
    if number is None:
        return name, _blank_stat(name), False
    return name, {"name": name, "value": _json_number(number), "status": "ok"}, False


def _query_all(base: str) -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    pool = ThreadPoolExecutor(max_workers=len(STAT_QUERIES))
    try:
        futures = [pool.submit(_query_one, base, name, query) for name, query in STAT_QUERIES]
        done, _pending = wait(futures, timeout=HTTP_TIMEOUT_S)
        for future in done:
            try:
                name, row, _failed = future.result(timeout=0)
            except Exception:
                continue
            rows[name] = row
    finally:
        pool.shutdown(wait=False, cancel_futures=True)
    stats: list[dict[str, Any]] = []
    for name, _query in STAT_QUERIES:
        stats.append(rows.get(name) or _blank_stat(name))
    if not any(row["status"] == "ok" for row in stats):
        raise RuntimeError
    return stats


def load_stats(environ: Mapping[str, str] | None = None) -> Outcome:
    """Fixed Prometheus instant queries. Client query strings are ignored."""
    location = read_location("FLEET_PROMETHEUS_URL", _env(environ))
    if location is None:
        return _done("stats", empty_stats(), "not_configured")
    try:
        join_url(location, "api/v1/query")
    except ValueError:
        return _done("stats", empty_stats(), "unavailable")
    try:
        stats, freshness, age = _cached_call(
            "stats", location, lambda: _query_all(location), cacheable=lambda _value: True
        )
    except Exception:
        return _done("stats", empty_stats(), "unavailable")
    status = "stale" if freshness == "stale" else "ok"
    return _done("stats", {"stats": stats}, status, age_s=age)


def load_links(environ: Mapping[str, str] | None = None) -> Outcome:
    """Fixed dashboard links built from the configured Grafana base."""
    location = read_location("FLEET_GRAFANA_URL", _env(environ))
    if location is None:
        return _done("links", {"links": []}, "not_configured")

    def load() -> list[dict[str, str]]:
        return [{"name": name, "href": join_url(location, suffix)} for name, suffix in DASHBOARDS]

    try:
        links, freshness, age = _cached_call("links", location, load, cacheable=lambda _value: True)
    except Exception:
        return _done("links", {"links": []}, "unavailable")
    status = "stale" if freshness == "stale" else "ok"
    return _done("links", {"links": links}, status, age_s=age)
