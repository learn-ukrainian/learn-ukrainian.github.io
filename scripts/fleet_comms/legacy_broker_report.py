"""Read-only retirement evidence for legacy Broker Ops telemetry (#6106).

The legacy HTTP-route and one-shot bridge telemetry currently share a private
SQLite store.  This report intentionally opens candidate databases read-only:
asking whether a zero-use window exists must never create a store, advance
coverage, or change the evidence it is evaluating.
"""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from scripts.common.repo_root import main_checkout_root

_SOURCE_REPO_ROOT = Path(__file__).resolve().parents[2]
_ROUTES_TABLE = "legacy_comms_route_usage"
_BRIDGE_TABLE = "legacy_bridge_ask_usage"
_ROUTE_SEAT_CALLERS = frozenset({"browser", "broker-ops", "cli", "dashboard"})
_ROUTE_BACKGROUND_CALLERS = frozenset({"automation", "programmatic"})
_BRIDGE_BACKGROUND_CALLERS = frozenset(
    {
        "anthropic",
        "cursor",
        "deepseek",
        "google",
        "moonshot",
        "openai",
        "xai",
        "zhipu",
    }
)


def default_routes_db() -> Path:
    """Return the shared legacy telemetry database without creating it."""
    return main_checkout_root(_SOURCE_REPO_ROOT) / "data" / "telemetry" / "legacy_comms_routes.db"


def default_legacy_bridge_path() -> Path:
    """Return the optional historical bridge store path without creating it."""
    return main_checkout_root(_SOURCE_REPO_ROOT) / "data" / "telemetry" / "legacy_bridge"


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _iso_z(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _open_read_only(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)


def _table_exists(connection: sqlite3.Connection, table: str) -> bool:
    return (
        connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)).fetchone()
        is not None
    )


def _meta_value(connection: sqlite3.Connection, key: str) -> str | None:
    if not _table_exists(connection, "telemetry_meta"):
        return None
    row = connection.execute("SELECT value FROM telemetry_meta WHERE key = ?", (key,)).fetchone()
    return str(row[0]) if row is not None else None


def _coverage_is_complete(coverage_started_at: str | None, window_start: datetime) -> bool | None:
    if coverage_started_at is None:
        return None
    try:
        coverage_start = datetime.fromisoformat(coverage_started_at.replace("Z", "+00:00"))
    except ValueError:
        return None
    return coverage_start.astimezone(UTC) <= window_start


def _usage_bucket(caller: str, *, bridge: bool) -> str:
    if bridge:
        if caller == "operator":
            return "seat"
        if caller in _BRIDGE_BACKGROUND_CALLERS:
            return "background"
        return "other"
    if caller in _ROUTE_SEAT_CALLERS:
        return "seat"
    if caller in _ROUTE_BACKGROUND_CALLERS:
        return "background"
    return "other"


def _usage_summary(rows: list[sqlite3.Row], *, bridge: bool) -> dict[str, Any]:
    buckets: dict[str, dict[str, Any]] = {
        name: {"count": 0, "by_caller": {}} for name in ("seat", "background", "other")
    }
    for row in rows:
        caller = str(row["caller"])
        count = int(row["count"] or 0)
        bucket = buckets[_usage_bucket(caller, bridge=bridge)]
        bucket["count"] += count
        bucket["by_caller"][caller] = bucket["by_caller"].get(caller, 0) + count
    for bucket in buckets.values():
        bucket["by_caller"] = dict(sorted(bucket["by_caller"].items()))
    return buckets


def _missing_store(path: Path, *, kind: str) -> dict[str, Any]:
    return {
        "kind": kind,
        "path": str(path),
        "state": "missing",
        "coverage_started_at": None,
        "window_fully_observed": None,
        "usage": _usage_summary([], bridge=kind == "legacy_bridge"),
    }


def _read_store(
    path: Path,
    *,
    window_start: datetime,
    window_end: datetime,
) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    try:
        connection = _open_read_only(path)
    except sqlite3.Error as exc:
        return [
            {
                "kind": "telemetry_store",
                "path": str(path),
                "state": "unreadable",
                "reason": type(exc).__name__,
            }
        ]

    connection.row_factory = sqlite3.Row
    try:
        query_start = _iso_z(window_start.replace(minute=0, second=0, microsecond=0))
        query_end = _iso_z(window_end.replace(minute=0, second=0, microsecond=0))
        reports: list[dict[str, Any]] = []
        if _table_exists(connection, _ROUTES_TABLE):
            rows = connection.execute(
                f"""
                SELECT caller_class AS caller, SUM(count) AS count
                FROM {_ROUTES_TABLE}
                WHERE hour_utc >= ? AND hour_utc <= ?
                GROUP BY caller_class
                ORDER BY caller_class
                """,
                (query_start, query_end),
            ).fetchall()
            coverage = _meta_value(connection, "coverage_started_at")
            reports.append(
                {
                    "kind": "legacy_comms_routes",
                    "path": str(path),
                    "state": "ok",
                    "coverage_started_at": coverage,
                    "window_fully_observed": _coverage_is_complete(coverage, window_start),
                    "usage": _usage_summary(rows, bridge=False),
                }
            )
        if _table_exists(connection, _BRIDGE_TABLE):
            rows = connection.execute(
                f"""
                SELECT caller_family AS caller, SUM(started_count) AS count,
                       SUM(succeeded_count) AS succeeded,
                       SUM(failed_count) AS failed
                FROM {_BRIDGE_TABLE}
                WHERE hour_utc >= ? AND hour_utc <= ?
                GROUP BY caller_family
                ORDER BY caller_family
                """,
                (query_start, query_end),
            ).fetchall()
            coverage = _meta_value(connection, "bridge_coverage_started_at")
            report = {
                "kind": "legacy_bridge",
                "path": str(path),
                "state": "ok",
                "coverage_started_at": coverage,
                "window_fully_observed": _coverage_is_complete(coverage, window_start),
                "usage": _usage_summary(rows, bridge=True),
            }
            report["outcomes"] = {
                "succeeded": sum(int(row["succeeded"] or 0) for row in rows),
                "failed": sum(int(row["failed"] or 0) for row in rows),
                "unfinished": sum(
                    max(
                        int(row["count"] or 0) - int(row["succeeded"] or 0) - int(row["failed"] or 0),
                        0,
                    )
                    for row in rows
                ),
            }
            reports.append(report)
        return reports
    except sqlite3.Error as exc:
        return [
            {
                "kind": "telemetry_store",
                "path": str(path),
                "state": "unreadable",
                "reason": type(exc).__name__,
            }
        ]
    finally:
        connection.close()


def build_legacy_broker_report(
    days: int,
    *,
    routes_db: Path | None = None,
    bridge_db: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Return a body-free, read-only legacy Broker Ops retirement report."""
    if not 1 <= days <= 90:
        raise ValueError("days must be between 1 and 90")

    generated_at = (now or _utc_now()).astimezone(UTC)
    window_start = generated_at - timedelta(days=days)
    routes_path = (routes_db or default_routes_db()).expanduser().resolve(strict=False)
    bridge_path = (bridge_db or default_legacy_bridge_path()).expanduser().resolve(strict=False)

    reports = _read_store(
        routes_path,
        window_start=window_start,
        window_end=generated_at,
    )
    use_separate_bridge = bridge_path != routes_path and (bridge_db is not None or bridge_path.is_file())
    if use_separate_bridge:
        reports = [report for report in reports if report.get("kind") != "legacy_bridge"]
    route_kinds = {str(report.get("kind")) for report in reports}
    if "legacy_comms_routes" not in route_kinds:
        reports.append(_missing_store(routes_path, kind="legacy_comms_routes"))
    if not use_separate_bridge and "legacy_bridge" not in route_kinds:
        reports.append(_missing_store(routes_path, kind="legacy_bridge"))
    if use_separate_bridge:
        bridge_reports = _read_store(
            bridge_path,
            window_start=window_start,
            window_end=generated_at,
        )
        bridge_reports = [
            report for report in bridge_reports if report.get("kind") in {"legacy_bridge", "telemetry_store"}
        ]
        if any(report.get("kind") == "legacy_bridge" for report in bridge_reports):
            reports.extend(bridge_reports)
        else:
            reports.append(_missing_store(bridge_path, kind="legacy_bridge"))

    totals: dict[str, dict[str, int]] = defaultdict(lambda: {"seat": 0, "background": 0, "other": 0})
    zero_use_reasons: list[str] = []
    observed_reports = [report for report in reports if report.get("kind") in {"legacy_comms_routes", "legacy_bridge"}]
    for report in observed_reports:
        kind = str(report["kind"])
        usage = report.get("usage", {})
        for bucket in ("seat", "background", "other"):
            totals[kind][bucket] += int(usage.get(bucket, {}).get("count", 0))
        if report.get("state") != "ok":
            zero_use_reasons.append(f"{kind}_not_readable")
        elif report.get("window_fully_observed") is not True:
            zero_use_reasons.append(f"{kind}_window_incomplete")
        elif any(int(usage.get(bucket, {}).get("count", 0)) for bucket in ("seat", "background", "other")):
            zero_use_reasons.append(f"{kind}_has_usage")

    if not observed_reports:
        zero_use_reasons.append("no_telemetry_store")
    zero_use_reasons = sorted(set(zero_use_reasons))
    return {
        "schema": "fleet-broker-report.v1",
        "content_included": False,
        "read_only": True,
        "generated_at": _iso_z(generated_at),
        "window": {
            "days": days,
            "start": _iso_z(window_start),
            "retention_days": 90,
        },
        "classification": {
            "seat": "HTTP browser/cli/dashboard/broker-ops callers; bridge caller_family=operator.",
            "background": "HTTP automation/programmatic callers; allowlisted non-operator bridge families.",
            "other": "canary, test, and unknown callers are retained separately and block a zero-use claim.",
        },
        "stores": reports,
        "totals": {kind: dict(counts) for kind, counts in sorted(totals.items())},
        "zero_use_candidate": {
            "eligible": not zero_use_reasons,
            "reason_codes": zero_use_reasons,
            "operator_declaration_required": True,
        },
    }
