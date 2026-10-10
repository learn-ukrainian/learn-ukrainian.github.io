"""Backup, download, and harness snapshot reads for the fleet board."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .snapshot import freshness
from .sources import SourceReport, read_location, report
from .values import (
    DOWNLOAD_ALIASES,
    DRIVER_ALIASES,
    UNLISTED,
    Outcome,
    _age,
    _alias,
    _cached_call,
    _done,
    _env,
    _json_number,
    _number,
    _timestamp,
    _token,
)

BACKUP_STALE_AFTER_H = 36.0
DOWNLOAD_STALL_MIN = 15.0
_MAX_FILE_BYTES = 1_000_000


def _now() -> datetime:
    return datetime.now(UTC)


def _flag(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    return None


def _optional_number(row: Mapping[str, Any], key: str) -> int | float | None:
    if key not in row:
        return None
    number = _number(row.get(key))
    if number is None or number < 0:
        return None
    return _json_number(number)


def _read_json_file(path: Path) -> object:
    if not path.is_file():
        raise FileNotFoundError
    with path.open("rb") as handle:
        raw = handle.read(_MAX_FILE_BYTES + 1)
    if len(raw) > _MAX_FILE_BYTES:
        raise ValueError
    return json.loads(raw.decode("utf-8"))


def _backup_piece(directory: Path, filename: str) -> tuple[dict[str, Any] | None, bool]:
    try:
        payload = _read_json_file(directory / filename)
    except Exception:
        return None, False
    if not isinstance(payload, dict):
        return None, False
    return payload, True


def _load_backup_raw(directory: Path) -> dict[str, Any]:
    if not directory.is_dir():
        raise ValueError
    last, last_ok = _backup_piece(directory, "last-success.json")
    fresh, fresh_ok = _backup_piece(directory, "freshness.json")
    receipt, receipt_ok = _backup_piece(directory, "receipt.json")
    return {"last": last, "fresh": fresh, "receipt": receipt, "complete": last_ok and fresh_ok and receipt_ok}


def _age_hours(fresh: object, last: object, now: datetime, elapsed_s: float = 0.0) -> float | None:
    if isinstance(fresh, dict) and "age_h" in fresh:
        number = _number(fresh.get("age_h"))
        if number is None or number < 0:
            return None
        extra = elapsed_s / 3600 if elapsed_s > 0 else 0.0
        return round(number + extra, 3)
    if isinstance(last, dict):
        stamp = _timestamp(last.get("at"))
        if stamp is None:
            return None
        then = datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
        hours = (now - then).total_seconds() / 3600
        return 0.0 if hours < 0 else hours
    return None


def _empty_backups() -> dict[str, Any]:
    return {"age_h": None, "stale": None, "last_result": None, "restore_test": None}


def _backup_view(
    raw: Mapping[str, Any], now: datetime, elapsed_s: float = 0.0
) -> tuple[dict[str, Any], str, float | None]:
    last = raw.get("last")
    fresh = raw.get("fresh")
    receipt = raw.get("receipt")
    age_h = _age_hours(fresh, last, now, elapsed_s)
    stale = None if age_h is None else age_h > BACKUP_STALE_AFTER_H
    data = {
        "age_h": None if age_h is None else _json_number(age_h),
        "stale": stale,
        "last_result": (
            {"at": _timestamp(last.get("at")), "status": _token(last.get("status"))} if isinstance(last, dict) else None
        ),
        "restore_test": (
            {"at": _timestamp(receipt.get("at")), "ok": _flag(receipt.get("ok"))} if isinstance(receipt, dict) else None
        ),
    }
    if not raw.get("complete"):
        return data, "unavailable", None
    data_age = None if age_h is None else age_h * 3600
    return data, ("stale" if stale else "ok"), data_age


def load_backups(environ: Mapping[str, str] | None = None) -> Outcome:
    """Age, last result, and restore-test result from the backup state directory."""
    location = read_location("FLEET_BACKUP_STATE_DIR", _env(environ))
    if location is None:
        return _done("backups", _empty_backups(), "not_configured")

    def load() -> dict[str, Any]:
        return _load_backup_raw(Path(location))

    try:
        raw, freshness, cache_age = _cached_call(
            "backups",
            location,
            load,
            cacheable=lambda value: bool(isinstance(value, dict) and value.get("complete")),
        )
    except Exception:
        return _done("backups", _empty_backups(), "unavailable")
    data, status, data_age = _backup_view(raw, _now(), cache_age)
    if freshness == "stale":
        status = "stale"
        if data_age is None:
            data_age = cache_age
    if status == "unavailable":
        return _done("backups", data, "unavailable")
    return _done("backups", data, status, age_s=data_age)


def _stall_limit(env: Mapping[str, str]) -> float:
    raw = env.get("FLEET_DOWNLOAD_STALL_MIN")
    if raw is None or not str(raw).strip():
        return DOWNLOAD_STALL_MIN
    try:
        value = float(str(raw).strip())
    except ValueError:
        return DOWNLOAD_STALL_MIN
    if not math.isfinite(value) or value < 0:
        return DOWNLOAD_STALL_MIN
    return value


def _stalled(stamp: str | None, now: datetime, limit: float) -> bool | None:
    if stamp is None:
        return None
    then = datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    minutes = (now - then).total_seconds() / 60
    if minutes < 0:
        return False
    return minutes > limit


def _pct(done: int | float | None, total: int | float | None) -> int | float | None:
    if done is None or total is None or float(total) <= 0:
        return None
    value = float(done) / float(total) * 100
    if not math.isfinite(value):
        return None
    return _json_number(round(value, 1))


def _download_items(payload: object, now: datetime, limit: float) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict) and isinstance(payload.get("items"), list):
        rows = payload["items"]
    else:
        raise ValueError
    items: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        source = _alias(row.get("source"), DOWNLOAD_ALIASES)
        if source is None:
            continue
        done = _optional_number(row, "done")
        total = _optional_number(row, "total")
        stamp = _timestamp(row.get("last_progress_at")) if "last_progress_at" in row else None
        items.append(
            {
                "source": source,
                "state": _token(row.get("state")) if "state" in row else None,
                "done": done,
                "total": total,
                "pct": _pct(done, total),
                "last_progress_at": stamp,
                "stalled": _stalled(stamp, now, limit),
            }
        )
    return items


def _current_stall(items: list[dict[str, Any]], now: datetime, limit: float) -> list[dict[str, Any]]:
    """Evaluate stall flags at serve time, including a cached payload."""
    current: list[dict[str, Any]] = []
    for item in items:
        row = dict(item)
        row["stalled"] = _stalled(row.get("last_progress_at"), now, limit)
        current.append(row)
    return current


def load_downloads(environ: Mapping[str, str] | None = None) -> Outcome:
    """Per-source download state, progress, and a stall flag."""
    env = _env(environ)
    location = read_location("FLEET_DOWNLOAD_STATUS", env)
    if location is None:
        return _done("downloads", {"state": None, "items": []}, "not_configured")
    limit = _stall_limit(env)

    def load() -> list[dict[str, Any]]:
        return _download_items(_read_json_file(Path(location)), _now(), limit)

    try:
        items, freshness, age = _cached_call("downloads", location, load, cacheable=lambda _value: True)
    except Exception:
        return _done("downloads", {"state": "unknown", "items": []}, "unavailable")
    items = _current_stall(items, _now(), limit)
    status = "stale" if freshness == "stale" else "ok"
    return _done("downloads", {"state": "ok", "items": items}, status, age_s=age)


def _drivers(payload: object) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        rows: object = payload
        measured = None
    elif isinstance(payload, dict) and isinstance(payload.get("drivers"), list):
        rows = payload["drivers"]
        measured = _timestamp(payload.get("measured_at")) if "measured_at" in payload else None
    else:
        raise ValueError
    if not isinstance(rows, list):
        raise ValueError
    drivers: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        agent_id = _alias(row.get("agent_id"), DRIVER_ALIASES)
        if agent_id is None:
            continue
        own = _timestamp(row.get("measured_at")) if "measured_at" in row else None
        drivers.append(
            {
                "agent_id": agent_id,
                "context_pct": _optional_number(row, "context_pct"),
                "compactions": _optional_number(row, "compactions"),
                "stop_count": _optional_number(row, "stop_count"),
                "ask_count": _optional_number(row, "ask_count"),
                "idle_min": _optional_number(row, "idle_min"),
                "measured_at": own or measured,
            }
        )
    return drivers


def _load_drivers(env: Mapping[str, str]) -> tuple[list[dict[str, Any]] | None, tuple[SourceReport, ...]]:
    location = read_location("FLEET_HARNESS_SNAPSHOT", env)
    if location is None:
        return None, (report("harness_snapshot", "not_configured"),)

    def load() -> list[dict[str, Any]]:
        return _drivers(_read_json_file(Path(location)))

    try:
        drivers, freshness, age = _cached_call("harness", location, load, cacheable=lambda _value: True)
    except Exception:
        return None, (report("harness_snapshot", "unavailable"),)
    status = "stale" if freshness == "stale" else "ok"
    return drivers, (report("harness_snapshot", status, age_s=_age(age)),)


def load_harness(environ: Mapping[str, str] | None = None) -> Outcome:
    """Per-driver harness figures. Missing measurements stay null."""
    drivers, reports = _load_drivers(_env(environ))
    if drivers is None:
        return {"drivers": []}, reports
    return {"drivers": drivers}, reports


def unknown_health() -> dict[str, Any]:
    """No attributable current measurement. Never invent a zero."""
    return {"agent_id": None, "status": "unknown", "measured_at": None,
            **{key: None for key in ("context_pct", "compactions", "stop_count", "ask_count", "idle_min")}}


def load_board_health(environ: Mapping[str, str] | None = None, *, now: datetime) -> dict[str, dict[str, Any]]:
    """Canonical driver measurements, aged independently of generic seat signals."""
    location = read_location("FLEET_HARNESS_SNAPSHOT", _env(environ))
    if location is None:
        return {}
    try:
        payload = _read_json_file(Path(location))
        drivers = _drivers(payload)
    except Exception:
        return {}
    interval = payload.get("interval_s") if isinstance(payload, dict) else None
    rows: dict[str, list[dict[str, Any]]] = {}
    for driver in drivers:
        if driver["agent_id"] != UNLISTED:
            rows.setdefault(driver["agent_id"], []).append(driver)
    result = {}
    for agent_id, matches in rows.items():
        health = unknown_health()
        if len(matches) == 1:
            driver = matches[0]
            status, age = freshness({"generated_at": driver["measured_at"], "interval_s": interval}, now)
            health["agent_id"] = agent_id
            if age is not None:
                health["measured_at"] = driver["measured_at"]
            if status in {"ok", "stale"}:
                health["status"] = status
            if status == "ok":
                for key in ("context_pct", "compactions", "stop_count", "ask_count", "idle_min"):
                    health[key] = driver[key]
        result[agent_id] = health
    return result


def load_harness_driver(agent_id: str, environ: Mapping[str, str] | None = None) -> Outcome:
    """One driver from the harness snapshot. Unknown ids are null."""
    drivers, reports = _load_drivers(_env(environ))
    if drivers is None or agent_id == UNLISTED:
        return {"driver": None}, reports
    found = next((row for row in drivers if row["agent_id"] == agent_id), None)
    return {"driver": found}, reports
