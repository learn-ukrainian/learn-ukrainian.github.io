"""Process-local resilience helpers for the playground API."""

from __future__ import annotations

import asyncio
import inspect
import logging
import os
import sqlite3
import time
from collections import deque
from datetime import UTC, datetime
from threading import Lock
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

DEFAULT_REQUEST_TIMEOUT_S = 10.0
DEFAULT_MAX_CONCURRENCY = 16
DEFAULT_SLOW_REQUEST_MS = 500.0
DEFAULT_SLOW_SQL_MS = 500.0
_MAX_EVENTS = 50


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def request_timeout_s() -> float:
    return max(0.1, _env_float("API_REQUEST_TIMEOUT_S", DEFAULT_REQUEST_TIMEOUT_S))


def max_concurrency() -> int:
    return max(1, _env_int("API_MAX_CONCURRENCY", DEFAULT_MAX_CONCURRENCY))


def slow_request_ms() -> float:
    return max(0.0, _env_float("API_SLOW_REQUEST_MS", DEFAULT_SLOW_REQUEST_MS))


def slow_sql_ms() -> float:
    return max(0.0, _env_float("API_SLOW_SQL_MS", DEFAULT_SLOW_SQL_MS))


class _ConcurrencyLimiter:
    def __init__(self) -> None:
        self._lock = Lock()
        self._in_flight = 0
        self._max_seen = 0
        self._saturated_count = 0

    def try_acquire(self, limit: int) -> bool:
        with self._lock:
            if self._in_flight >= limit:
                self._saturated_count += 1
                return False
            self._in_flight += 1
            self._max_seen = max(self._max_seen, self._in_flight)
            return True

    def release(self) -> None:
        with self._lock:
            self._in_flight = max(0, self._in_flight - 1)

    def snapshot(self) -> dict[str, int]:
        with self._lock:
            return {
                "in_flight": self._in_flight,
                "max_seen": self._max_seen,
                "saturated_count": self._saturated_count,
            }

    def reset_for_tests(self) -> None:
        with self._lock:
            self._in_flight = 0
            self._max_seen = 0
            self._saturated_count = 0


_limiter = _ConcurrencyLimiter()
_stats_lock = Lock()
_timeout_count = 0
_slow_requests: deque[dict[str, Any]] = deque(maxlen=_MAX_EVENTS)
_slow_sql: deque[dict[str, Any]] = deque(maxlen=_MAX_EVENTS)


def _now_z() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _record_timeout(path: str, method: str, elapsed_ms: float) -> None:
    global _timeout_count
    with _stats_lock:
        _timeout_count += 1
        _slow_requests.append(
            {
                "ts": _now_z(),
                "method": method,
                "path": path,
                "status": 504,
                "duration_ms": round(elapsed_ms, 2),
                "event": "timeout",
            }
        )


def _record_slow_request(path: str, method: str, status: int, elapsed_ms: float) -> None:
    event = {
        "ts": _now_z(),
        "method": method,
        "path": path,
        "status": status,
        "duration_ms": round(elapsed_ms, 2),
        "event": "slow_request",
    }
    with _stats_lock:
        _slow_requests.append(event)
    logger.warning(
        "slow_api_request method=%s path=%s status=%s duration_ms=%.2f",
        method,
        path,
        status,
        elapsed_ms,
    )


def _record_slow_sql(query: str, elapsed_ms: float, caller: str) -> None:
    event = {
        "ts": _now_z(),
        "query": " ".join(str(query).split())[:240],
        "caller": caller,
        "duration_ms": round(elapsed_ms, 2),
    }
    with _stats_lock:
        _slow_sql.append(event)
    logger.warning(
        "slow_sql_query caller=%s duration_ms=%.2f query=%s",
        caller,
        elapsed_ms,
        event["query"],
    )


def _caller() -> str:
    for frame in inspect.stack()[2:8]:
        if not frame.filename.endswith("scripts/api/resilience.py"):
            return f"{frame.filename}:{frame.lineno}"
    return "unknown"


async def resilience_middleware(request: Request, call_next):
    """Bound request concurrency and convert wedged handlers into 504s."""
    limit = max_concurrency()
    if not _limiter.try_acquire(limit):
        return JSONResponse(
            status_code=503,
            headers={"Retry-After": "1"},
            content={
                "error": "server_saturated",
                "detail": f"Too many in-flight requests for this worker (limit={limit})",
            },
        )

    start = time.perf_counter()
    try:
        response = await asyncio.wait_for(call_next(request), timeout=request_timeout_s())
    except TimeoutError:
        elapsed_ms = (time.perf_counter() - start) * 1000
        _record_timeout(str(request.url.path), request.method, elapsed_ms)
        return JSONResponse(
            status_code=504,
            content={
                "error": "request_timeout",
                "detail": f"Request exceeded {request_timeout_s():.1f}s",
            },
        )
    finally:
        _limiter.release()

    elapsed_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Request-Duration-Ms"] = f"{elapsed_ms:.2f}"
    if elapsed_ms >= slow_request_ms():
        _record_slow_request(
            str(request.url.path),
            request.method,
            response.status_code,
            elapsed_ms,
        )
    return response


class TimedSQLiteCursor(sqlite3.Cursor):
    """sqlite3 cursor that records slow execute calls."""

    def execute(self, sql: str, parameters: Any = (), /) -> sqlite3.Cursor:
        start = time.perf_counter()
        try:
            return super().execute(sql, parameters)
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            if elapsed_ms >= slow_sql_ms():
                _record_slow_sql(sql, elapsed_ms, _caller())

    def executemany(self, sql: str, seq_of_parameters: Any, /) -> sqlite3.Cursor:
        start = time.perf_counter()
        try:
            return super().executemany(sql, seq_of_parameters)
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            if elapsed_ms >= slow_sql_ms():
                _record_slow_sql(sql, elapsed_ms, _caller())


class TimedSQLiteConnection(sqlite3.Connection):
    """sqlite3 connection that records slow direct execute calls."""

    def cursor(self, *args: Any, **kwargs: Any) -> sqlite3.Cursor:
        kwargs.setdefault("factory", TimedSQLiteCursor)
        return super().cursor(*args, **kwargs)

    def execute(self, sql: str, parameters: Any = (), /) -> sqlite3.Cursor:
        start = time.perf_counter()
        try:
            return super().execute(sql, parameters)
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            if elapsed_ms >= slow_sql_ms():
                _record_slow_sql(sql, elapsed_ms, _caller())

    def executemany(self, sql: str, seq_of_parameters: Any, /) -> sqlite3.Cursor:
        start = time.perf_counter()
        try:
            return super().executemany(sql, seq_of_parameters)
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            if elapsed_ms >= slow_sql_ms():
                _record_slow_sql(sql, elapsed_ms, _caller())

    def executescript(self, sql_script: str, /) -> sqlite3.Cursor:
        start = time.perf_counter()
        try:
            return super().executescript(sql_script)
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            if elapsed_ms >= slow_sql_ms():
                _record_slow_sql(sql_script, elapsed_ms, _caller())


def connect_sqlite(database: str, *args: Any, **kwargs: Any) -> sqlite3.Connection:
    """Create a sqlite connection whose execute calls are slow-query logged."""
    kwargs.setdefault("factory", TimedSQLiteConnection)
    return sqlite3.connect(database, *args, **kwargs)


def get_resilience_snapshot() -> dict[str, Any]:
    with _stats_lock:
        timeout_count = _timeout_count
        slow_requests = list(_slow_requests)[-10:]
        slow_sql = list(_slow_sql)[-10:]
    return {
        "request_timeout_s": request_timeout_s(),
        "max_concurrency": max_concurrency(),
        **_limiter.snapshot(),
        "timeout_count": timeout_count,
        "slow_request_threshold_ms": slow_request_ms(),
        "slow_sql_threshold_ms": slow_sql_ms(),
        "recent_slow_requests": slow_requests,
        "recent_slow_sql": slow_sql,
    }


def reset_resilience_stats_for_tests() -> None:
    global _timeout_count
    _limiter.reset_for_tests()
    with _stats_lock:
        _timeout_count = 0
        _slow_requests.clear()
        _slow_sql.clear()
