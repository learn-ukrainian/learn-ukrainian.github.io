"""Body-free aggregate telemetry for legacy one-shot ``ask-*`` aliases.

This module is intentionally independent of FastAPI so the bridge CLI can
record use without importing the API layer.  Prompts, task IDs, attachments,
models, responses, error text, paths, and raw caller identities never enter
the store.
"""

from __future__ import annotations

import logging
import os
import sqlite3
import stat
import threading
from collections import defaultdict
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal

from scripts.common.repo_root import main_checkout_root

logger = logging.getLogger(__name__)

_SOURCE_REPO_ROOT = Path(__file__).resolve().parents[2]


def _shared_telemetry_db_path(source_repo_root: Path | None = None) -> Path:
    """Anchor one fleet-wide store to the primary checkout, never a worktree."""
    source_root = (source_repo_root or _SOURCE_REPO_ROOT).resolve()
    primary_root = main_checkout_root(source_root)
    return primary_root / "data" / "telemetry" / "legacy_comms_routes.db"


_DB_PATH = _shared_telemetry_db_path()
_RETENTION_DAYS = 90
_WINDOWS = {
    "1h": timedelta(hours=1),
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
    "90d": timedelta(days=90),
}
_TARGETS = (
    "agy",
    "claude",
    "codex",
    "cursor",
    "deepseek",
    "glm",
    "grok",
    "kimi",
    "pool",
)
_init_lock = threading.Lock()
_initialized_paths: set[Path] = set()


@dataclass(frozen=True, slots=True)
class BridgeInvocationToken:
    """Normalized bucket identity returned after a persisted start."""

    hour_utc: str
    target: str
    caller_family: str
    started_at: str
    db_path: Path


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


def normalize_target(value: str) -> str:
    normalized = str(value).strip().lower()
    if normalized not in _TARGETS:
        raise ValueError("bridge telemetry target is not allowlisted")
    return normalized


def classify_caller_family(source: str | None) -> str:
    """Collapse a caller identity to one fixed family without retaining it."""
    normalized = str(source or "operator").strip().lower()
    if normalized in {"operator", "human"}:
        return "operator"
    prefixes = (
        (("claude",), "anthropic"),
        (("codex",), "openai"),
        (("agy", "gemini"), "google"),
        (("grok",), "xai"),
        (("kimi",), "moonshot"),
        (("glm",), "zhipu"),
        (("deepseek", "hermes"), "deepseek"),
        (("cursor",), "cursor"),
    )
    for candidates, family in prefixes:
        if normalized.startswith(candidates):
            return family
    return "unknown"


def _connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(str(path), timeout=5.0)
    connection.execute("PRAGMA busy_timeout=5000")
    return connection


def _prepare_private_db_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_CREAT | os.O_RDWR
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise OSError(f"legacy bridge telemetry path is not a regular file: {path}")
        os.fchmod(descriptor, 0o600)
    finally:
        os.close(descriptor)


def _initialize_db(path: Path, *, now: datetime | None = None) -> None:
    _prepare_private_db_file(path)
    observed_at = _iso_z(now or _now_utc())
    with closing(_connect(path)) as connection:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS telemetry_meta (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS legacy_bridge_ask_usage (
                hour_utc       TEXT NOT NULL,
                target         TEXT NOT NULL CHECK (
                    target IN (
                        'agy', 'claude', 'codex', 'cursor', 'deepseek',
                        'glm', 'grok', 'kimi', 'pool'
                    )
                ),
                caller_family  TEXT NOT NULL CHECK (
                    caller_family IN (
                        'anthropic', 'cursor', 'deepseek', 'google',
                        'moonshot', 'openai', 'operator', 'xai', 'zhipu',
                        'unknown'
                    )
                ),
                started_count   INTEGER NOT NULL DEFAULT 0 CHECK (started_count >= 0),
                succeeded_count INTEGER NOT NULL DEFAULT 0 CHECK (succeeded_count >= 0),
                failed_count    INTEGER NOT NULL DEFAULT 0 CHECK (failed_count >= 0),
                first_seen      TEXT NOT NULL,
                last_seen       TEXT NOT NULL,
                CHECK (succeeded_count + failed_count <= started_count),
                PRIMARY KEY (hour_utc, target, caller_family)
            );
            CREATE INDEX IF NOT EXISTS idx_legacy_bridge_usage_last_seen
                ON legacy_bridge_ask_usage(last_seen);
            """
        )
        connection.execute(
            "INSERT OR IGNORE INTO telemetry_meta(key, value) VALUES ('bridge_schema_version', '1')"
        )
        connection.execute(
            "INSERT OR IGNORE INTO telemetry_meta(key, value) "
            "VALUES ('bridge_coverage_started_at', ?)",
            (observed_at,),
        )
        connection.commit()


def initialize_bridge_telemetry(
    db_path: Path | None = None,
    *,
    now: datetime | None = None,
) -> Path:
    path = db_path or _DB_PATH
    key = path.resolve(strict=False)
    with _init_lock:
        existed = path.exists()
        _prepare_private_db_file(path)
        if key not in _initialized_paths or not existed:
            _initialize_db(path, now=now)
            _initialized_paths.add(key)
    return path


def _reset_initialized_paths_for_tests() -> None:
    with _init_lock:
        _initialized_paths.clear()


def record_bridge_invocation_start(
    target: str,
    source: str | None,
    *,
    db_path: Path | None = None,
    now: datetime | None = None,
) -> BridgeInvocationToken:
    """Persist one conservative use marker before provider execution."""
    normalized_target = normalize_target(target)
    caller_family = classify_caller_family(source)
    observed = _normalized_utc(now or _now_utc())
    observed_at = _iso_z(observed)
    hour_utc = _hour_z(observed)
    path = initialize_bridge_telemetry(db_path, now=observed)
    cutoff = _hour_z(observed - timedelta(days=_RETENTION_DAYS))
    with closing(_connect(path)) as connection:
        connection.execute(
            "DELETE FROM legacy_bridge_ask_usage WHERE hour_utc < ?",
            (cutoff,),
        )
        connection.execute(
            """
            INSERT INTO legacy_bridge_ask_usage(
                hour_utc, target, caller_family, started_count,
                succeeded_count, failed_count, first_seen, last_seen
            ) VALUES (?, ?, ?, 1, 0, 0, ?, ?)
            ON CONFLICT(hour_utc, target, caller_family)
            DO UPDATE SET
                started_count = started_count + 1,
                first_seen = MIN(first_seen, excluded.first_seen),
                last_seen = MAX(last_seen, excluded.last_seen)
            """,
            (hour_utc, normalized_target, caller_family, observed_at, observed_at),
        )
        connection.commit()
    return BridgeInvocationToken(
        hour_utc=hour_utc,
        target=normalized_target,
        caller_family=caller_family,
        started_at=observed_at,
        db_path=path,
    )


def record_bridge_invocation_finish(
    token: BridgeInvocationToken,
    *,
    succeeded: bool,
    now: datetime | None = None,
) -> None:
    """Attach a terminal count to the exact bucket returned at start."""
    finished_at = _iso_z(now or _now_utc())
    path = initialize_bridge_telemetry(token.db_path)
    succeeded_increment = 1 if succeeded else 0
    failed_increment = 0 if succeeded else 1
    with closing(_connect(path)) as connection:
        connection.execute(
            """
            INSERT INTO legacy_bridge_ask_usage(
                hour_utc, target, caller_family, started_count,
                succeeded_count, failed_count, first_seen, last_seen
            ) VALUES (?, ?, ?, 1, ?, ?, ?, ?)
            ON CONFLICT(hour_utc, target, caller_family)
            DO UPDATE SET
                succeeded_count = succeeded_count + excluded.succeeded_count,
                failed_count = failed_count + excluded.failed_count,
                first_seen = MIN(first_seen, excluded.first_seen),
                last_seen = MAX(last_seen, excluded.last_seen)
            """,
            (
                token.hour_utc,
                token.target,
                token.caller_family,
                succeeded_increment,
                failed_increment,
                token.started_at,
                finished_at,
            ),
        )
        connection.commit()


def start_bridge_invocation_safely(target: str, source: str | None) -> BridgeInvocationToken | None:
    try:
        return record_bridge_invocation_start(target, source)
    except (OSError, RuntimeError, sqlite3.Error, ValueError):
        logger.exception(
            "legacy bridge telemetry start failed target=%s caller_family=%s",
            target if target in _TARGETS else "unknown",
            classify_caller_family(source),
        )
        return None


def finish_bridge_invocation_safely(
    token: BridgeInvocationToken | None,
    *,
    succeeded: bool,
) -> None:
    if token is None:
        return
    try:
        record_bridge_invocation_finish(token, succeeded=succeeded)
    except (OSError, RuntimeError, sqlite3.Error, ValueError):
        logger.exception(
            "legacy bridge telemetry finish failed target=%s caller_family=%s",
            token.target,
            token.caller_family,
        )


def bridge_usage_summary(
    window: Literal["1h", "24h", "7d", "30d", "90d"],
    *,
    db_path: Path | None = None,
    now: datetime | None = None,
) -> dict:
    """Return bounded aggregate counts and honest observation coverage."""
    generated = _normalized_utc(now or _now_utc())
    requested_start = generated - _WINDOWS[window]
    query_start = _hour_z(requested_start)
    path = initialize_bridge_telemetry(db_path, now=generated)
    with closing(_connect(path)) as connection:
        connection.row_factory = sqlite3.Row
        coverage_row = connection.execute(
            "SELECT value FROM telemetry_meta WHERE key = 'bridge_coverage_started_at'"
        ).fetchone()
        rows = connection.execute(
            """
            SELECT target, caller_family,
                   SUM(started_count) AS started_count,
                   SUM(succeeded_count) AS succeeded_count,
                   SUM(failed_count) AS failed_count,
                   MIN(first_seen) AS first_seen,
                   MAX(last_seen) AS last_seen
            FROM legacy_bridge_ask_usage
            WHERE hour_utc >= ?
            GROUP BY target, caller_family
            ORDER BY target, caller_family
            """,
            (query_start,),
        ).fetchall()

    targets: dict[str, dict] = {
        target: {
            "target": target,
            "started": 0,
            "succeeded": 0,
            "failed": 0,
            "unfinished": 0,
            "first_seen": None,
            "last_seen": None,
            "by_caller_family": {},
        }
        for target in _TARGETS
    }
    caller_totals: defaultdict[str, int] = defaultdict(int)
    for row in rows:
        item = targets[row["target"]]
        started = int(row["started_count"])
        succeeded = int(row["succeeded_count"])
        failed = int(row["failed_count"])
        item["started"] += started
        item["succeeded"] += succeeded
        item["failed"] += failed
        item["first_seen"] = min(
            value for value in (item["first_seen"], row["first_seen"]) if value is not None
        )
        item["last_seen"] = max(
            value for value in (item["last_seen"], row["last_seen"]) if value is not None
        )
        item["by_caller_family"][row["caller_family"]] = started
        caller_totals[row["caller_family"]] += started

    started_total = 0
    succeeded_total = 0
    failed_total = 0
    unfinished_total = 0
    for item in targets.values():
        item["unfinished"] = max(item["started"] - item["succeeded"] - item["failed"], 0)
        item["by_caller_family"] = dict(sorted(item["by_caller_family"].items()))
        started_total += item["started"]
        succeeded_total += item["succeeded"]
        failed_total += item["failed"]
        unfinished_total += item["unfinished"]

    coverage_started_at = str(coverage_row["value"])
    coverage_start = datetime.fromisoformat(coverage_started_at.replace("Z", "+00:00"))
    return {
        "generated_at": _iso_z(generated),
        "coverage_started_at": coverage_started_at,
        "window": window,
        "window_start": _iso_z(requested_start),
        "window_fully_observed": coverage_start <= requested_start,
        "retention_days": _RETENTION_DAYS,
        "aggregate_granularity": "hour",
        "started": started_total,
        "succeeded": succeeded_total,
        "failed": failed_total,
        "unfinished": unfinished_total,
        "by_caller_family": dict(sorted(caller_totals.items())),
        "targets": list(targets.values()),
        "scope_note": "Counts valid run_compat_ask invocations; no prompt, task, model, or response data.",
    }
