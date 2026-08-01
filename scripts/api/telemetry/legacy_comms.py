"""Privacy-safe usage telemetry for legacy direct-message HTTP routes.

The telemetry is deliberately aggregate-only.  It never persists request path
parameters, query values, bodies, credentials, client addresses, or raw
headers.  Direct ``ask-*`` CLI calls do not pass through these routes and need
their own telemetry before they can be considered for migration.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import sqlite3
import threading
from collections import defaultdict
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal

from fastapi import Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from starlette.background import BackgroundTask
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..config import PROJECT_ROOT
from ..resilience import connect_sqlite

logger = logging.getLogger(__name__)

_DB_PATH = PROJECT_ROOT / "data" / "telemetry" / "legacy_comms_routes.db"
_RETENTION_DAYS = 90
_WINDOWS = {
    "1h": timedelta(hours=1),
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
    "90d": timedelta(days=90),
}
_CALLER_TAG_HEADER = "x-learn-uk-caller"
_TAGGED_CALLERS = frozenset({"automation", "broker-ops", "canary", "cli", "dashboard", "test"})
_CALLER_CLASSES = frozenset({*_TAGGED_CALLERS, "browser", "programmatic", "unknown"})
_ROUTE_METHODS = {
    "messages": "GET",
    "conversations": "GET",
    "conversation_detail": "GET",
    "acknowledge": "POST",
    "send": "POST",
}
_EXACT_ROUTES = {
    ("GET", "/api/comms/messages"): "messages",
    ("GET", "/api/comms/conversations"): "conversations",
    ("POST", "/api/comms/send"): "send",
}
_CONVERSATION_DETAIL_RE = re.compile(r"^/api/comms/conversation/[^/]+$")
_ACKNOWLEDGE_RE = re.compile(r"^/api/comms/acknowledge/[^/]+$")
_init_lock = threading.Lock()
_initialized_paths: set[Path] = set()


def _now_utc() -> datetime:
    return datetime.now(UTC)


def _normalized_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _iso_z(value: datetime) -> str:
    return _normalized_utc(value).isoformat().replace("+00:00", "Z")


def _hour_z(value: datetime) -> str:
    return _iso_z(_normalized_utc(value).replace(minute=0, second=0, microsecond=0))


def _prepare_private_db_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_CREAT | os.O_RDWR
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        if not os.path.isfile(path):
            raise OSError(f"legacy comms telemetry path is not a regular file: {path}")
        os.fchmod(descriptor, 0o600)
    finally:
        os.close(descriptor)


def _initialize_db(path: Path, *, now: datetime | None = None) -> None:
    _prepare_private_db_file(path)
    observed_at = _iso_z(now or _now_utc())
    with closing(connect_sqlite(str(path), timeout=5.0)) as connection:
        connection.execute("PRAGMA busy_timeout=5000")
        connection.execute("PRAGMA journal_mode=WAL")
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS telemetry_meta (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS legacy_comms_route_usage (
                hour_utc     TEXT NOT NULL,
                route_id     TEXT NOT NULL CHECK (
                    route_id IN (
                        'messages', 'conversations', 'conversation_detail',
                        'acknowledge', 'send'
                    )
                ),
                method       TEXT NOT NULL CHECK (method IN ('GET', 'POST')),
                caller_class TEXT NOT NULL CHECK (
                    caller_class IN (
                        'automation', 'broker-ops', 'browser', 'canary', 'cli',
                        'dashboard', 'programmatic', 'test', 'unknown'
                    )
                ),
                status_class TEXT NOT NULL CHECK (
                    status_class IN ('1xx', '2xx', '3xx', '4xx', '5xx', 'unknown')
                ),
                count        INTEGER NOT NULL CHECK (count >= 1),
                first_seen   TEXT NOT NULL,
                last_seen    TEXT NOT NULL,
                PRIMARY KEY (hour_utc, route_id, method, caller_class, status_class)
            );
            CREATE INDEX IF NOT EXISTS idx_legacy_comms_usage_last_seen
                ON legacy_comms_route_usage(last_seen);
            """
        )
        connection.execute(
            "INSERT OR IGNORE INTO telemetry_meta(key, value) VALUES ('schema_version', '1')"
        )
        connection.execute(
            "INSERT OR IGNORE INTO telemetry_meta(key, value) VALUES ('coverage_started_at', ?)",
            (observed_at,),
        )
        connection.commit()


def initialize_legacy_comms_telemetry(
    db_path: Path | None = None,
    *,
    now: datetime | None = None,
) -> Path:
    """Initialize the aggregate store once per process and return its path."""
    path = db_path or _DB_PATH
    key = path.resolve(strict=False)
    with _init_lock:
        if key not in _initialized_paths or not path.exists():
            _initialize_db(path, now=now)
            _initialized_paths.add(key)
    return path


def _reset_initialized_paths_for_tests() -> None:
    with _init_lock:
        _initialized_paths.clear()


def match_legacy_route(method: str, path: str) -> str | None:
    """Return an allowlisted normalized route id without retaining path data."""
    normalized_method = method.upper()
    exact = _EXACT_ROUTES.get((normalized_method, path))
    if exact is not None:
        return exact
    if normalized_method == "GET" and _CONVERSATION_DETAIL_RE.fullmatch(path):
        return "conversation_detail"
    if normalized_method == "POST" and _ACKNOWLEDGE_RE.fullmatch(path):
        return "acknowledge"
    return None


def _header_value(headers, name: str) -> str:
    value = headers.get(name)
    if value is not None:
        return str(value)
    for key, candidate in headers.items():
        if str(key).lower() == name:
            return str(candidate)
    return ""


def classify_caller(headers) -> str:
    """Classify a caller without returning or storing any raw header value."""
    tagged = _header_value(headers, _CALLER_TAG_HEADER).strip().lower()
    if tagged in _TAGGED_CALLERS:
        return tagged

    user_agent = _header_value(headers, "user-agent").lower()
    if "testclient" in user_agent:
        return "test"
    if any(token in user_agent for token in ("mozilla", "chrome", "safari", "webkit", "firefox")):
        return "browser"
    if any(token in user_agent for token in ("curl", "httpie", "wget")):
        return "cli"
    if any(
        token in user_agent
        for token in ("aiohttp", "go-http-client", "httpx", "node-fetch", "python-requests", "urllib")
    ):
        return "programmatic"
    return "unknown"


def _status_class(status_code: int) -> str:
    family = status_code // 100
    return f"{family}xx" if 1 <= family <= 5 else "unknown"


def record_legacy_route_usage(
    route_id: str,
    method: str,
    caller_class: str,
    status_code: int,
    *,
    db_path: Path | None = None,
    now: datetime | None = None,
) -> None:
    """Atomically increment one body-free hourly aggregate."""
    normalized_method = method.upper()
    if _ROUTE_METHODS.get(route_id) != normalized_method:
        raise ValueError("route_id and method are not an approved legacy route")
    if caller_class not in _CALLER_CLASSES:
        raise ValueError("caller_class is not allowlisted")

    observed = _normalized_utc(now or _now_utc())
    observed_at = _iso_z(observed)
    path = initialize_legacy_comms_telemetry(db_path, now=observed)
    cutoff = _hour_z(observed - timedelta(days=_RETENTION_DAYS))
    status_class = _status_class(status_code)
    with closing(connect_sqlite(str(path), timeout=5.0)) as connection:
        connection.execute("PRAGMA busy_timeout=5000")
        connection.execute(
            "DELETE FROM legacy_comms_route_usage WHERE hour_utc < ?",
            (cutoff,),
        )
        connection.execute(
            """
            INSERT INTO legacy_comms_route_usage(
                hour_utc, route_id, method, caller_class, status_class,
                count, first_seen, last_seen
            ) VALUES (?, ?, ?, ?, ?, 1, ?, ?)
            ON CONFLICT(hour_utc, route_id, method, caller_class, status_class)
            DO UPDATE SET
                count = count + 1,
                first_seen = MIN(first_seen, excluded.first_seen),
                last_seen = MAX(last_seen, excluded.last_seen)
            """,
            (
                _hour_z(observed),
                route_id,
                normalized_method,
                caller_class,
                status_class,
                observed_at,
                observed_at,
            ),
        )
        connection.commit()


def _record_safely(route_id: str, method: str, caller_class: str, status_code: int) -> None:
    try:
        record_legacy_route_usage(route_id, method, caller_class, status_code)
    except (OSError, RuntimeError, sqlite3.Error, ValueError):
        logger.exception(
            "legacy route telemetry failed route_id=%s method=%s status_class=%s",
            route_id,
            method,
            _status_class(status_code),
        )


async def _run_background(
    previous_background,
    route_id: str,
    method: str,
    caller_class: str,
    status_code: int,
) -> None:
    try:
        if previous_background is not None:
            await previous_background()
    finally:
        await asyncio.to_thread(_record_safely, route_id, method, caller_class, status_code)


class LegacyCommsTelemetryRoute(APIRoute):
    """APIRoute wrapper that observes only the explicit legacy allowlist."""

    def get_route_handler(self):
        route_handler = super().get_route_handler()

        async def instrumented(request: Request) -> Response:
            route_id = match_legacy_route(request.method, request.url.path)
            if route_id is None:
                return await route_handler(request)

            caller_class = classify_caller(request.headers)
            try:
                response = await route_handler(request)
            except RequestValidationError:
                await asyncio.to_thread(_record_safely, route_id, request.method, caller_class, 422)
                raise
            except StarletteHTTPException as exc:
                await asyncio.to_thread(
                    _record_safely,
                    route_id,
                    request.method,
                    caller_class,
                    exc.status_code,
                )
                raise
            except Exception:
                await asyncio.to_thread(_record_safely, route_id, request.method, caller_class, 500)
                raise

            response.background = BackgroundTask(
                _run_background,
                response.background,
                route_id,
                request.method,
                caller_class,
                response.status_code,
            )
            return response

        return instrumented


def legacy_comms_summary(
    window: Literal["1h", "24h", "7d", "30d", "90d"],
    *,
    db_path: Path | None = None,
    now: datetime | None = None,
) -> dict:
    """Return bounded aggregates with explicit observation-coverage truth."""
    generated = _normalized_utc(now or _now_utc())
    requested_start = generated - _WINDOWS[window]
    query_start = _hour_z(requested_start)
    path = initialize_legacy_comms_telemetry(db_path, now=generated)

    with closing(connect_sqlite(str(path), timeout=5.0)) as connection:
        connection.row_factory = sqlite3.Row
        coverage_row = connection.execute(
            "SELECT value FROM telemetry_meta WHERE key = 'coverage_started_at'"
        ).fetchone()
        rows = connection.execute(
            """
            SELECT route_id, method, caller_class, status_class,
                   SUM(count) AS count,
                   MIN(first_seen) AS first_seen,
                   MAX(last_seen) AS last_seen
            FROM legacy_comms_route_usage
            WHERE hour_utc >= ?
            GROUP BY route_id, method, caller_class, status_class
            ORDER BY route_id, method, caller_class, status_class
            """,
            (query_start,),
        ).fetchall()

    coverage_started_at = str(coverage_row["value"])
    routes: dict[str, dict] = {
        route_id: {
            "route_id": route_id,
            "method": method,
            "count": 0,
            "first_seen": None,
            "last_seen": None,
            "by_caller": {},
            "by_status": {},
        }
        for route_id, method in _ROUTE_METHODS.items()
    }
    for row in rows:
        item = routes[row["route_id"]]
        count = int(row["count"])
        item["count"] += count
        item["first_seen"] = min(
            value for value in (item["first_seen"], row["first_seen"]) if value is not None
        )
        item["last_seen"] = max(
            value for value in (item["last_seen"], row["last_seen"]) if value is not None
        )
        item["by_caller"][row["caller_class"]] = (
            item["by_caller"].get(row["caller_class"], 0) + count
        )
        item["by_status"][row["status_class"]] = (
            item["by_status"].get(row["status_class"], 0) + count
        )

    caller_totals: defaultdict[str, int] = defaultdict(int)
    status_totals: defaultdict[str, int] = defaultdict(int)
    total = 0
    for item in routes.values():
        total += item["count"]
        item["by_caller"] = dict(sorted(item["by_caller"].items()))
        item["by_status"] = dict(sorted(item["by_status"].items()))
        for caller, count in item["by_caller"].items():
            caller_totals[caller] += count
        for status, count in item["by_status"].items():
            status_totals[status] += count

    coverage_start = datetime.fromisoformat(coverage_started_at.replace("Z", "+00:00"))
    return {
        "generated_at": _iso_z(generated),
        "coverage_started_at": coverage_started_at,
        "window": window,
        "window_start": _iso_z(requested_start),
        "window_fully_observed": coverage_start <= requested_start,
        "retention_days": _RETENTION_DAYS,
        "aggregate_granularity": "hour",
        "total": total,
        "by_caller": dict(sorted(caller_totals.items())),
        "by_status": dict(sorted(status_totals.items())),
        "routes": list(routes.values()),
        "scope_note": "Direct ask-* CLI calls bypass these HTTP routes and are not counted.",
    }
