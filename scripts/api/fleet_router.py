"""Unified, read-only observer for the durable fleet communications plane.

This router deliberately opens the fleet-comms SQLite database in ``mode=ro``
and projects only bounded metadata. It never initializes schema, writes a
receipt, invokes an agent, or retrieves artifact bodies. File handoffs remain
authoritative during the pre-flip soak.
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
import re
import sqlite3
from collections import Counter
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from scripts.fleet_comms.endpoints import load_endpoint_registry
from scripts.fleet_comms.message_plane import default_plane_root, read_plane_status
from scripts.fleet_comms.migrations import MIGRATIONS

from . import comms_router as legacy_comms
from .config import PROJECT_ROOT
from .runtime_router import get_acp_conversation, list_acp_conversations, recent_runtime_records

router = APIRouter(tags=["fleet"])
logger = logging.getLogger(__name__)

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100
MAX_BODY_PREVIEW_CHARS = 280
MAX_BODY_DETAIL_CHARS = 2_048
MAX_DETAIL_ROWS = 100
MAX_ACP_SCAN = 500
MAX_ACTIVITY_SCAN = 500
MAX_OPERATIONS_ITEMS = 50

_ZOMBIE_TYPES = frozenset(
    {"stale_message", "pingpong", "error_loop", "orphan_pid", "corrupt_pid"}
)
_ZOMBIE_SEVERITIES = frozenset({"warning", "critical"})
_BATCH_HEALTH = frozenset({"complete", "healthy", "stalled", "dead", "unknown"})
_TRACK_LABEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,39}$")

_SAFE_METADATA_KEYS = frozenset(
    {
        "agent",
        "completion_state",
        "harness",
        "legacy_message_id",
        "model",
        "plane_mode",
        "pr_number",
        "source",
        "source_agent",
        "stream_epic",
        "task_family",
        "task_id",
        "transport",
        "transport_mode",
        "via",
    }
)
_PROVENANCE_KEY_ALIASES = {"source": "Source", "agent": "Agent", "via": "Via"}
_SECRET_ASSIGNMENT = re.compile(
    r"(?i)\b(api[_-]?key|authorization|password|secret|token)\b(\s*[:=]\s*)([^,;\s]+)"
)
_BEARER_TOKEN = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{8,}")
_TOKEN_LITERAL = re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{16,}|sk-[A-Za-z0-9_-]{16,})\b")


def _plane_root() -> Path:
    """Resolve the existing durable plane root without creating it."""
    return default_plane_root(repo_root=Path(PROJECT_ROOT))


def _plane_db_path() -> Path:
    return _plane_root() / "comms.sqlite3"


@contextmanager
def _read_connection() -> Iterator[tuple[sqlite3.Connection | None, str]]:
    """Yield a query-only connection, never creating a database or schema."""
    db_path = _plane_db_path()
    if not db_path.is_file():
        yield None, "db_missing"
        return

    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(
            f"{db_path.resolve().as_uri()}?mode=ro",
            uri=True,
            timeout=0.25,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        yield connection, "available"
    except (OSError, ValueError, sqlite3.Error):
        logger.warning("Fleet observer could not open its read-only plane database")
        yield None, "db_unavailable"
    finally:
        if connection is not None:
            connection.close()


def _table_exists(connection: sqlite3.Connection, table: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)
    ).fetchone()
    return row is not None


def _normalize_time(value: str | None, label: str) -> str | None:
    """Normalize an ISO-8601 filter to lexical UTC form used by fleet rows."""
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"{label} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _time_clauses(
    column: str,
    *,
    since: str | None,
    until: str | None,
    clauses: list[str],
    params: list[Any],
) -> None:
    if since is not None:
        clauses.append(f"{column} >= ?")
        params.append(since)
    if until is not None:
        clauses.append(f"{column} <= ?")
        params.append(until)


def _safe_text(value: Any, *, limit: int = 160, fallback: str = "unknown") -> str:
    """Return a compact display label without reflecting arbitrary multiline data."""
    if value is None:
        return fallback
    text = " ".join(str(value).split())
    if not text:
        return fallback
    return text[:limit]


def _redact_preview(value: str) -> str:
    value = _SECRET_ASSIGNMENT.sub(
        lambda match: f"{match.group(1)}{match.group(2)}[REDACTED]", value
    )
    value = _BEARER_TOKEN.sub("Bearer [REDACTED]", value)
    return _TOKEN_LITERAL.sub("[REDACTED]", value)


def _body_preview(value: Any, *, limit: int) -> tuple[str | None, bool]:
    """Return only a redacted inline excerpt; blobs are never read here."""
    if not isinstance(value, str):
        return None, False
    return _redact_preview(value[:limit]), len(value) > limit


def _safe_metadata(value: Any) -> dict[str, Any]:
    """Allowlist terse metadata fields rather than exposing arbitrary JSON."""
    if not isinstance(value, str) or not value:
        return {}
    try:
        raw = json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}
    if not isinstance(raw, dict):
        return {}

    metadata: dict[str, Any] = {}
    for key in sorted(_SAFE_METADATA_KEYS):
        alias = _PROVENANCE_KEY_ALIASES.get(key)
        item = raw.get(alias) if alias in raw else raw.get(key)
        if isinstance(item, str):
            metadata[key] = _safe_text(item, limit=120, fallback="")
        elif isinstance(item, (int, bool)):
            metadata[key] = item
    return metadata


def _first_label(*values: Any, fallback: str) -> str:
    for value in values:
        text = _safe_text(value, fallback="")
        if text:
            return text
    return fallback


def _provenance(
    *,
    metadata: dict[str, Any] | None = None,
    source: Any = None,
    agent: Any = None,
    via: Any = None,
) -> dict[str, str]:
    """Normalize the Source / Agent / Via triplet used throughout the observer."""
    metadata = metadata or {}
    return {
        "source": _first_label(
            source,
            metadata.get("source"),
            metadata.get("source_agent"),
            fallback="fleet-comms",
        ),
        "agent": _first_label(metadata.get("agent"), agent, fallback="unknown"),
        "via": _first_label(
            metadata.get("via"),
            metadata.get("transport_mode"),
            metadata.get("transport"),
            metadata.get("harness"),
            via,
            fallback="fleet-comms",
        ),
    }


def _collection(
    key: str,
    items: list[dict[str, Any]],
    *,
    total: int,
    limit: int,
    offset: int,
    availability: str,
    filters: dict[str, Any],
) -> dict[str, Any]:
    next_offset = offset + len(items) if offset + len(items) < total else None
    return {
        "read_only": True,
        "availability": availability,
        "db_exists": availability not in {"db_missing", "db_unavailable"},
        key: items,
        "total": total,
        "limit": limit,
        "offset": offset,
        "next_offset": next_offset,
        "filters": filters,
    }


def _empty_collection(
    key: str,
    *,
    limit: int,
    offset: int,
    availability: str,
    filters: dict[str, Any],
) -> dict[str, Any]:
    return _collection(
        key,
        [],
        total=0,
        limit=limit,
        offset=offset,
        availability=availability,
        filters=filters,
    )


def _paged_query(
    connection: sqlite3.Connection,
    *,
    key: str,
    select_sql: str,
    from_sql: str,
    clauses: list[str],
    params: list[Any],
    order_sql: str,
    limit: int,
    offset: int,
    filters: dict[str, Any],
    transform: Callable[[sqlite3.Row], dict[str, Any]],
) -> dict[str, Any]:
    where_sql = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    try:
        total_row = connection.execute(f"SELECT COUNT(*){from_sql}{where_sql}", params).fetchone()
        total = int(total_row[0]) if total_row is not None else 0
        query = f"{select_sql}{from_sql}{where_sql} ORDER BY {order_sql} LIMIT ? OFFSET ?"
        rows = connection.execute(query, [*params, limit, offset]).fetchall()
    except sqlite3.Error:
        logger.warning("Fleet observer query failed")
        return _empty_collection(
            key,
            limit=limit,
            offset=offset,
            availability="db_unavailable",
            filters=filters,
        )
    return _collection(
        key,
        [transform(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
        availability="available" if total else "empty",
        filters=filters,
    )


def _safe_plane_status() -> dict[str, Any]:
    """Project the existing plane read model without paths or raw telemetry rows."""
    status = read_plane_status(repo_root=Path(PROJECT_ROOT), recent_limit=0)
    mode = _safe_text(status.get("mode"), fallback="invalid")
    authority_active = mode == "authority"
    schema = status.get("schema") if isinstance(status.get("schema"), dict) else {}
    telemetry = (
        status.get("parity_telemetry")
        if isinstance(status.get("parity_telemetry"), dict)
        else {}
    )
    return {
        "mode": mode,
        "enabled": bool(status.get("enabled")),
        "read_only": True,
        "authority": (
            "fleet_comms_authoritative" if authority_active else "file_handoffs_authoritative"
        ),
        "cutover": "authority_active" if authority_active else "pre_flip_operator_gated",
        "schema": {
            "known_version": schema.get("known_version"),
            "applied_version": schema.get("applied_version"),
            "applied_name": schema.get("applied_name"),
            "db_exists": bool(schema.get("db_exists")),
            "db_error": schema.get("db_error"),
        },
        "parity_telemetry": {
            "exists": bool(telemetry.get("exists")),
            "event_count": int(telemetry.get("event_count") or 0),
            "parity_ok_count": int(telemetry.get("parity_ok_count") or 0),
            "parity_fail_count": int(telemetry.get("parity_fail_count") or 0),
        },
    }


def _count_by_state(connection: sqlite3.Connection, table: str, column: str) -> dict[str, int]:
    if not _table_exists(connection, table):
        return {}
    try:
        rows = connection.execute(
            f"SELECT {column}, COUNT(*) FROM {table} GROUP BY {column} ORDER BY {column}"
        ).fetchall()
    except sqlite3.Error:
        return {}
    return {_safe_text(row[0], fallback="unknown"): int(row[1]) for row in rows}


def _non_negative_int(value: Any) -> int:
    """Normalize legacy numeric fields without reflecting arbitrary values."""
    if isinstance(value, bool):
        return int(value)
    try:
        return max(0, int(value))
    except (TypeError, ValueError, OverflowError):
        return 0


def _non_negative_float(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return 0.0
    if not math.isfinite(number):
        return 0.0
    return max(0.0, round(number, 1))


def _legacy_broker_snapshot() -> dict[str, Any]:
    """Read the legacy broker with an explicit query-only connection.

    The legacy health route opens a normal connection so that it can report
    writability. This consolidated observer deliberately does not reuse that
    behavior: a GET must never create, migrate, or journal the broker database.
    """
    db_path = Path(legacy_comms.MESSAGE_DB)
    result: dict[str, Any] = {
        "availability": "db_missing",
        "db_exists": False,
        "readable": False,
        "size_kb": 0.0,
        "unacknowledged_depth": 0,
    }
    if not db_path.is_file():
        return result

    result["db_exists"] = True
    try:
        result["size_kb"] = round(db_path.stat().st_size / 1024, 1)
        connection = sqlite3.connect(
            f"{db_path.resolve().as_uri()}?mode=ro",
            uri=True,
            timeout=0.25,
        )
        try:
            connection.execute("PRAGMA query_only = ON")
            result["readable"] = True
            if not _table_exists(connection, "messages"):
                result["availability"] = "table_missing"
                return result
            row = connection.execute(
                "SELECT COUNT(*) FROM messages WHERE acknowledged = 0"
            ).fetchone()
            result["unacknowledged_depth"] = _non_negative_int(row[0] if row else 0)
            result["availability"] = "available"
        finally:
            connection.close()
    except (OSError, ValueError, sqlite3.Error):
        logger.warning("Fleet operations could not read the legacy broker database")
        result["availability"] = "db_unavailable"
        result["readable"] = False
    return result


def _safe_zombie_projection(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {
            "availability": "unavailable",
            "total": 0,
            "returned": 0,
            "limit": MAX_OPERATIONS_ITEMS,
            "truncated": False,
            "by_type": {},
            "by_severity": {},
            "items": [],
        }

    source = raw.get("zombies")
    source_items = source if isinstance(source, list) else []
    items: list[dict[str, Any]] = []
    by_type: Counter[str] = Counter()
    by_severity: Counter[str] = Counter()
    for entry in source_items:
        if not isinstance(entry, dict):
            continue
        zombie_type = entry.get("type")
        if zombie_type not in _ZOMBIE_TYPES:
            zombie_type = "unknown"
        severity = entry.get("severity")
        if severity not in _ZOMBIE_SEVERITIES:
            severity = "unknown"
        by_type[zombie_type] += 1
        by_severity[severity] += 1
        if len(items) >= MAX_OPERATIONS_ITEMS:
            continue
        item: dict[str, Any] = {"type": zombie_type, "severity": severity}
        for field in ("message_count_1h", "error_count"):
            if field in entry:
                item[field] = _non_negative_int(entry[field])
        if "age_hours" in entry:
            item["age_hours"] = _non_negative_float(entry["age_hours"])
        items.append(item)

    return {
        "availability": "available",
        "total": sum(by_type.values()),
        "returned": len(items),
        "limit": MAX_OPERATIONS_ITEMS,
        "truncated": sum(by_type.values()) > len(items),
        "by_type": dict(sorted(by_type.items())),
        "by_severity": dict(sorted(by_severity.items())),
        "items": items,
    }


def _safe_batch_projection(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {
            "availability": "unavailable",
            "total": 0,
            "returned": 0,
            "limit": MAX_OPERATIONS_ITEMS,
            "truncated": False,
            "running_processes": 0,
            "by_health": {},
            "tracks": [],
        }

    source = raw.get("tracks")
    source_tracks = source if isinstance(source, dict) else {}
    tracks: list[dict[str, Any]] = []
    by_health: Counter[str] = Counter()
    for raw_track, entry in sorted(source_tracks.items(), key=lambda item: str(item[0])):
        if not isinstance(entry, dict):
            continue
        track = str(raw_track)
        if not _TRACK_LABEL.fullmatch(track):
            track = "unknown"
        health = entry.get("health")
        if health not in _BATCH_HEALTH:
            health = "unknown"
        by_health[health] += 1
        if len(tracks) >= MAX_OPERATIONS_ITEMS:
            continue
        tracks.append(
            {
                "track": track,
                "health": health,
                "total_expected": _non_negative_int(entry.get("total_expected")),
                "research_done": _non_negative_int(entry.get("research_done")),
                "remaining": _non_negative_int(entry.get("remaining")),
                "recent_30min": _non_negative_int(entry.get("recent_30min")),
                "throughput_per_hour": _non_negative_float(
                    entry.get("throughput_per_hour")
                ),
            }
        )

    return {
        "availability": "available",
        "total": sum(by_health.values()),
        "returned": len(tracks),
        "limit": MAX_OPERATIONS_ITEMS,
        "truncated": sum(by_health.values()) > len(tracks),
        "running_processes": _non_negative_int(raw.get("running_processes")),
        "by_health": dict(sorted(by_health.items())),
        "tracks": tracks,
    }


def _legacy_batch_snapshot() -> dict[str, Any]:
    """Collect the existing batch read models without populating their cache."""
    logs = legacy_comms._scan_preseed_logs()
    processes = legacy_comms._check_build_processes()
    all_tracks = {
        str(item.get("track"))
        for item in [*logs, *processes]
        if isinstance(item, dict) and item.get("track")
    }
    tracks: dict[str, dict[str, Any]] = {}
    for track in sorted(all_tracks):
        progress = legacy_comms._scan_track_progress(track)
        log = next(
            (item for item in logs if isinstance(item, dict) and item.get("track") == track),
            None,
        )
        process = next(
            (
                item
                for item in processes
                if isinstance(item, dict) and item.get("track") == track
            ),
            None,
        )
        if log and log.get("complete"):
            health = "complete"
        elif process:
            recent = _non_negative_int(progress.get("recent_30min"))
            log_is_recent = bool(
                log
                and "age_seconds" in log
                and _non_negative_int(log.get("age_seconds")) < 900
            )
            health = "healthy" if recent > 0 or log_is_recent else "stalled"
        elif (
            log
            and not log.get("complete")
            and _non_negative_int(log.get("age_seconds")) > 600
        ):
            health = "dead"
        else:
            health = "unknown"
        tracks[track] = {**progress, "health": health}
    return {"running_processes": len(processes), "tracks": tracks}


@router.get("/operations")
async def fleet_operations() -> dict[str, Any]:
    """Sanitized legacy broker, zombie, and batch operations projection."""
    broker_result, process_result, zombie_result, batch_result = await asyncio.gather(
        asyncio.to_thread(_legacy_broker_snapshot),
        legacy_comms.active_processes(),
        legacy_comms.detect_zombies(stale_hours=2.0, pingpong_threshold=5),
        asyncio.to_thread(_legacy_batch_snapshot),
        return_exceptions=True,
    )

    broker = (
        broker_result
        if isinstance(broker_result, dict)
        else {
            "availability": "db_unavailable",
            "db_exists": False,
            "readable": False,
            "size_kb": 0.0,
            "unacknowledged_depth": 0,
        }
    )
    if isinstance(process_result, dict):
        broker["live_process_count"] = _non_negative_int(process_result.get("alive"))
        broker["process_availability"] = "available"
    else:
        broker["live_process_count"] = None
        broker["process_availability"] = "unavailable"
        if broker["availability"] == "available":
            broker["availability"] = "partial"

    zombies = _safe_zombie_projection(
        zombie_result if not isinstance(zombie_result, BaseException) else None
    )
    batches = _safe_batch_projection(
        batch_result if not isinstance(batch_result, BaseException) else None
    )
    sections = (broker["availability"], zombies["availability"], batches["availability"])
    if all(section == "available" for section in sections):
        availability = "available"
    elif all(section in {"unavailable", "db_unavailable"} for section in sections):
        availability = "unavailable"
    else:
        availability = "partial"

    return {
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "read_only": True,
        "writes_enabled": False,
        "availability": availability,
        "broker": broker,
        "zombies": zombies,
        "batches": batches,
    }


@router.get("/health")
def fleet_health() -> dict[str, Any]:
    """Read-only health, mode, schema, and current authority posture."""
    status = _safe_plane_status()
    return {
        "ok": True,
        "observer": "fleet-comms-v1",
        "read_only": True,
        "writes_enabled": False,
        **status,
    }


@router.get("/overview")
def fleet_overview() -> dict[str, Any]:
    """Compact durable-plane counts for the consolidated fleet dashboard."""
    status = _safe_plane_status()
    result: dict[str, Any] = {
        "read_only": True,
        "authority": status["authority"],
        "cutover": status["cutover"],
        "health": status,
        "counts": {
            "requests": {"total": 0, "by_state": {}},
            "messages": {"total": 0, "by_kind": {}},
            "reviews": {"total": 0, "by_state": {}},
            "dead_letters": {"total": 0},
            "acp_conversations": {"total": 0},
            "authority_jobs": {"total": 0, "by_state": {}},
        },
        "availability": "db_missing",
    }
    with _read_connection() as (connection, availability):
        if connection is None:
            result["availability"] = availability
            return result
        counts = result["counts"]
        request_states = _count_by_state(connection, "requests", "state")
        message_kinds = _count_by_state(connection, "comms_messages", "kind")
        review_states = _count_by_state(connection, "formal_review_jobs", "state")
        authority_job_states = _count_by_state(connection, "authority_jobs", "state")
        counts["requests"] = {"total": sum(request_states.values()), "by_state": request_states}
        counts["messages"] = {"total": sum(message_kinds.values()), "by_kind": message_kinds}
        counts["reviews"] = {"total": sum(review_states.values()), "by_state": review_states}
        counts["authority_jobs"] = {
            "total": sum(authority_job_states.values()),
            "by_state": authority_job_states,
        }
        dead_letter_table = (
            "authority_dead_letters" if status["mode"] == "authority" else "dead_letters"
        )
        if _table_exists(connection, dead_letter_table):
            counts["dead_letters"]["total"] = int(
                connection.execute(f"SELECT COUNT(*) FROM {dead_letter_table}").fetchone()[0]
            )
        if _table_exists(connection, "acp_conversations"):
            counts["acp_conversations"]["total"] = int(
                connection.execute("SELECT COUNT(*) FROM acp_conversations").fetchone()[0]
            )
        result["availability"] = "available" if any(
            section["total"] for section in counts.values()
        ) else "empty"
    return result


def _registered_endpoints(connection: sqlite3.Connection | None) -> dict[str, dict[str, Any]]:
    if connection is None or not _table_exists(connection, "agent_endpoints"):
        return {}
    try:
        rows = connection.execute(
            """
            SELECT canonical_name, registry_version, state, successor, created_at
            FROM agent_endpoints
            ORDER BY canonical_name ASC
            """
        ).fetchall()
    except sqlite3.Error:
        return {}
    return {
        _safe_text(row["canonical_name"]): {
            "registry_version": row["registry_version"],
            "state": _safe_text(row["state"]),
            "successor": _safe_text(row["successor"], fallback="") or None,
            "created_at": row["created_at"],
        }
        for row in rows
    }


@router.get("/agents")
@router.get("/endpoints")
def fleet_agents(
    agent: str | None = Query(default=None),
    state: str | None = Query(default=None),
) -> dict[str, Any]:
    """Configured and durable endpoint inventory with configuration secrets omitted."""
    with _read_connection() as (connection, availability):
        registered = _registered_endpoints(connection)
    try:
        registry = load_endpoint_registry()
    except (OSError, ValueError):
        logger.warning("Fleet observer could not load the endpoint registry")
        registry = None

    endpoints: list[dict[str, Any]] = []
    if registry is not None:
        for endpoint in registry.endpoints:
            durable = registered.pop(endpoint.name, None)
            item = {
                "agent": endpoint.name,
                "aliases": list(endpoint.aliases),
                "state": durable["state"] if durable else endpoint.state,
                "successor": durable["successor"] if durable else endpoint.successor,
                "registry_version": registry.version,
                "transports": list(endpoint.transports),
                "completion_evidence": list(endpoint.completion_evidence),
                "default_ttl_seconds": endpoint.default_ttl_seconds,
                "concurrency_limit": endpoint.concurrency_limit,
                "formal_review_eligible": endpoint.formal_review_eligible,
                "durable_registration": durable is not None,
                "created_at": durable["created_at"] if durable else None,
                "read_only": True,
            }
            endpoints.append(item)
    for name, durable in registered.items():
        endpoints.append(
            {
                "agent": name,
                "aliases": [],
                "state": durable["state"],
                "successor": durable["successor"],
                "registry_version": durable["registry_version"],
                "transports": [],
                "completion_evidence": [],
                "default_ttl_seconds": None,
                "concurrency_limit": None,
                "formal_review_eligible": False,
                "durable_registration": True,
                "created_at": durable["created_at"],
                "read_only": True,
            }
        )
    if agent is not None:
        endpoints = [
            item for item in endpoints if agent == item["agent"] or agent in item["aliases"]
        ]
    if state is not None:
        endpoints = [item for item in endpoints if state == item["state"]]
    endpoints.sort(key=lambda item: str(item["agent"]))
    return {
        "read_only": True,
        "availability": availability if registry is None else "available",
        "registry_version": registry.version if registry is not None else None,
        "endpoints": endpoints,
        "total": len(endpoints),
        "filters": {"agent": agent, "state": state},
        "configuration_policy": "configuration_json_omitted",
    }


def _request_item(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    metadata = _safe_metadata(data.get("invocation_spec_json"))
    authority_provenance = _safe_metadata(data.get("authority_provenance_json"))
    metadata = {**metadata, **authority_provenance}
    provenance = _provenance(
        metadata=metadata,
        source=authority_provenance.get("source") or data.get("conversation_source"),
        agent=data.get("sender") or data.get("resolved_recipient"),
    )
    return {
        "request_id": data["request_id"],
        "request_message_id": data["request_message_id"],
        "conversation_id": data.get("conversation_id"),
        "requested_recipient": data["requested_recipient"],
        "resolved_recipient": data["resolved_recipient"],
        "state": data["state"],
        "completion_state": data["completion_state"],
        "expires_at": data["expires_at"],
        "created_at": data["created_at"],
        "updated_at": data["updated_at"],
        "metadata": metadata,
        "read_only": True,
        **provenance,
    }


@router.get("/requests")
def fleet_requests(
    kind: str | None = Query(default=None),
    state: str | None = Query(default=None),
    agent: str | None = Query(default=None),
    source: str | None = Query(default=None),
    conversation: str | None = Query(default=None),
    since: str | None = Query(default=None),
    until: str | None = Query(default=None),
    limit: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    """Queued, in-flight, and terminal request projection without request bodies."""
    since_value = _normalize_time(since, "since")
    until_value = _normalize_time(until, "until")
    filters = {
        "kind": kind,
        "state": state,
        "agent": agent,
        "source": source,
        "conversation": conversation,
        "since": since_value,
        "until": until_value,
    }
    with _read_connection() as (connection, availability):
        if connection is None:
            return _empty_collection(
                "requests", limit=limit, offset=offset, availability=availability, filters=filters
            )
        if not _table_exists(connection, "requests"):
            return _empty_collection(
                "requests", limit=limit, offset=offset, availability="table_missing", filters=filters
            )
        has_messages = _table_exists(connection, "comms_messages")
        has_conversations = _table_exists(connection, "conversations")
        has_authority_metadata = _table_exists(connection, "authority_message_metadata")
        select_extras = [
            "NULL AS conversation_id",
            "NULL AS sender",
            "NULL AS conversation_source",
            "NULL AS authority_provenance_json",
        ]
        from_sql = " FROM requests AS request"
        if has_messages:
            select_extras[:2] = [
                "message.conversation_id AS conversation_id",
                "message.sender AS sender",
            ]
            from_sql += " LEFT JOIN comms_messages AS message ON message.message_id = request.request_message_id"
        if has_messages and has_conversations:
            select_extras[2] = "conversation.source AS conversation_source"
            from_sql += " LEFT JOIN conversations AS conversation ON conversation.conversation_id = message.conversation_id"
        if has_messages and has_authority_metadata:
            select_extras[3] = "authority_meta.provenance_json AS authority_provenance_json"
            from_sql += (
                " LEFT JOIN authority_message_metadata AS authority_meta"
                " ON authority_meta.message_id = message.message_id"
            )
        clauses: list[str] = []
        params: list[Any] = []
        if state is not None:
            clauses.append("request.state = ?")
            params.append(state)
        if kind is not None:
            if has_messages:
                clauses.append("message.kind = ?")
                params.append(kind)
            elif kind != "request":
                clauses.append("1 = 0")
        if agent is not None:
            agent_clause = "request.requested_recipient = ? OR request.resolved_recipient = ?"
            params.extend([agent, agent])
            if has_messages:
                agent_clause += " OR message.sender = ? OR message.recipient = ?"
                params.extend([agent, agent])
            if has_messages and has_authority_metadata:
                agent_clause += " OR json_extract(authority_meta.provenance_json, '$.Agent') = ?"
                params.append(agent)
            clauses.append(f"({agent_clause})")
        if source is not None:
            if has_messages and has_conversations:
                source_expression = "conversation.source"
                if has_authority_metadata:
                    source_expression = (
                        "COALESCE(json_extract(authority_meta.provenance_json, '$.Source'), "
                        f"{source_expression})"
                    )
                clauses.append(f"{source_expression} = ?")
                params.append(source)
            else:
                clauses.append("1 = 0")
        if conversation is not None:
            if has_messages:
                clauses.append("message.conversation_id = ?")
                params.append(conversation)
            else:
                clauses.append("1 = 0")
        _time_clauses(
            "request.created_at",
            since=since_value,
            until=until_value,
            clauses=clauses,
            params=params,
        )
        return _paged_query(
            connection,
            key="requests",
            select_sql=(
                "SELECT request.request_id, request.request_message_id, request.requested_recipient, "
                "request.resolved_recipient, request.state, request.expires_at, request.completion_state, "
                "request.invocation_spec_json, request.created_at, request.updated_at, "
                + ", ".join(select_extras)
            ),
            from_sql=from_sql,
            clauses=clauses,
            params=params,
            order_sql="request.created_at DESC, request.request_id ASC",
            limit=limit,
            offset=offset,
            filters=filters,
            transform=_request_item,
        )


def _authority_job_item(row: sqlite3.Row) -> dict[str, Any]:
    """Project a durable authority job without its payload or result artifacts."""
    data = dict(row)
    metadata = _safe_metadata(data.get("authority_provenance_json"))
    job_kind = _safe_text(data.get("job_kind"), fallback="unknown")
    default_source = {
        "request": "authority",
        "discussion": "authority-discussion",
        "formal_review": "formal-review",
    }.get(job_kind, "authority")
    default_agent = "review-gate" if job_kind == "formal_review" else "authority-service"
    conversation_id = data.get("conversation_id")
    if conversation_id is None and job_kind == "discussion":
        conversation_id = data.get("subject_id")
    provenance = _provenance(
        metadata=metadata,
        source=metadata.get("source") or data.get("conversation_source") or default_source,
        agent=data.get("message_sender") or default_agent,
        via="queue",
    )
    return {
        "job_id": data["job_id"],
        "kind": job_kind,
        "subject_id": data["subject_id"],
        "conversation_id": conversation_id,
        "review_id": data.get("review_id"),
        "pr_number": data.get("pr_number"),
        "state": data["state"],
        "deadline_at": data.get("deadline_at"),
        "attempt_count": int(data.get("attempt_count") or 0),
        "created_at": data["created_at"],
        "updated_at": data["updated_at"],
        "completed_at": data.get("completed_at"),
        "payload_content": "omitted",
        "result_content": "omitted",
        "read_only": True,
        **provenance,
    }


@router.get("/authority/jobs")
def fleet_authority_jobs(
    kind: str | None = Query(default=None),
    state: str | None = Query(default=None),
    agent: str | None = Query(default=None),
    source: str | None = Query(default=None),
    pr: int | None = Query(default=None, ge=1),
    conversation: str | None = Query(default=None),
    since: str | None = Query(default=None),
    until: str | None = Query(default=None),
    limit: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    """Read-only authority queue projection; payload and result blobs remain sealed."""
    since_value = _normalize_time(since, "since")
    until_value = _normalize_time(until, "until")
    filters = {
        "kind": kind,
        "state": state,
        "agent": agent,
        "source": source,
        "pr": pr,
        "conversation": conversation,
        "since": since_value,
        "until": until_value,
    }
    with _read_connection() as (connection, availability):
        if connection is None:
            return _empty_collection(
                "jobs", limit=limit, offset=offset, availability=availability, filters=filters
            )
        if not _table_exists(connection, "authority_jobs"):
            return _empty_collection(
                "jobs", limit=limit, offset=offset, availability="table_missing", filters=filters
            )
        has_messages = _table_exists(connection, "comms_messages")
        has_metadata = _table_exists(connection, "authority_message_metadata")
        has_conversations = _table_exists(connection, "conversations")
        has_reviews = _table_exists(connection, "formal_review_jobs")
        from_sql = " FROM authority_jobs AS job"
        message_sender_select = "NULL AS message_sender"
        conversation_select = "NULL AS conversation_id"
        conversation_source_select = "NULL AS conversation_source"
        provenance_select = "NULL AS authority_provenance_json"
        review_select = "NULL AS review_id, NULL AS pr_number"
        if has_messages:
            from_sql += (
                " LEFT JOIN comms_messages AS message"
                " ON job.job_kind = 'request' AND message.message_id = job.subject_id"
            )
            message_sender_select = "message.sender AS message_sender"
            conversation_select = "message.conversation_id AS conversation_id"
        if has_metadata and has_messages:
            from_sql += (
                " LEFT JOIN authority_message_metadata AS authority_meta"
                " ON authority_meta.message_id = message.message_id"
            )
            provenance_select = "authority_meta.provenance_json AS authority_provenance_json"
        if has_conversations:
            conversation_join = "(job.job_kind = 'discussion' AND conversation.conversation_id = job.subject_id)"
            if has_messages:
                conversation_join = (
                    "conversation.conversation_id = message.conversation_id OR "
                    "(job.job_kind = 'discussion' AND conversation.conversation_id = job.subject_id)"
                )
            from_sql += (
                " LEFT JOIN conversations AS conversation ON " + conversation_join
            )
            conversation_select = "conversation.conversation_id AS conversation_id"
            if has_messages:
                conversation_select = (
                    "COALESCE(message.conversation_id, conversation.conversation_id) AS conversation_id"
                )
            conversation_source_select = "conversation.source AS conversation_source"
        if has_reviews:
            from_sql += (
                " LEFT JOIN formal_review_jobs AS review"
                " ON job.job_kind = 'formal_review' AND review.review_id = job.subject_id"
            )
            review_select = "review.review_id AS review_id, review.pr_number AS pr_number"
        clauses: list[str] = []
        params: list[Any] = []
        if kind is not None:
            clauses.append("job.job_kind = ?")
            params.append(kind)
        if state is not None:
            clauses.append("job.state = ?")
            params.append(state)
        if agent is not None:
            default_agent = (
                "CASE WHEN job.job_kind = 'formal_review' THEN 'review-gate' "
                "ELSE 'authority-service' END"
            )
            agent_expression = default_agent
            if has_messages:
                agent_expression = f"COALESCE(message.sender, {default_agent})"
            if has_metadata and has_messages:
                agent_expression = (
                    "COALESCE(json_extract(authority_meta.provenance_json, '$.Agent'), "
                    f"{agent_expression})"
                )
            agent_clause = f"{agent_expression} = ?"
            params.append(agent)
            if has_messages:
                agent_clause += " OR message.recipient = ?"
                params.append(agent)
            clauses.append(f"({agent_clause})")
        if source is not None:
            default_source = (
                "CASE WHEN job.job_kind = 'formal_review' THEN 'formal-review' "
                "WHEN job.job_kind = 'discussion' THEN 'authority-discussion' ELSE 'authority' END"
            )
            source_expression = default_source
            if has_conversations:
                source_expression = f"COALESCE(conversation.source, {default_source})"
            if has_metadata and has_messages:
                source_expression = (
                    "COALESCE(json_extract(authority_meta.provenance_json, '$.Source'), "
                    f"{source_expression})"
                )
            clauses.append(f"{source_expression} = ?")
            params.append(source)
        if pr is not None:
            if has_reviews:
                clauses.append("review.pr_number = ?")
                params.append(pr)
            else:
                clauses.append("1 = 0")
        if conversation is not None:
            if has_conversations:
                conversation_expression = "conversation.conversation_id"
                if has_messages:
                    conversation_expression = "COALESCE(message.conversation_id, conversation.conversation_id)"
                clauses.append(f"{conversation_expression} = ?")
                params.append(conversation)
            elif has_messages:
                clauses.append("message.conversation_id = ?")
                params.append(conversation)
            else:
                clauses.append("1 = 0")
        _time_clauses(
            "job.created_at",
            since=since_value,
            until=until_value,
            clauses=clauses,
            params=params,
        )
        return _paged_query(
            connection,
            key="jobs",
            select_sql=(
                "SELECT job.job_id, job.job_kind, job.subject_id, job.state, job.deadline_at, "
                "job.attempt_count, job.created_at, job.updated_at, job.completed_at, "
                f"{message_sender_select}, {conversation_select}, {conversation_source_select}, "
                f"{provenance_select}, {review_select}"
            ),
            from_sql=from_sql,
            clauses=clauses,
            params=params,
            order_sql="job.created_at DESC, job.job_id ASC",
            limit=limit,
            offset=offset,
            filters=filters,
            transform=_authority_job_item,
        )


def _message_item(row: sqlite3.Row, *, body_limit: int = MAX_BODY_PREVIEW_CHARS) -> dict[str, Any]:
    data = dict(row)
    metadata = _safe_metadata(data.get("metadata_json"))
    authority_provenance = _safe_metadata(data.get("authority_provenance_json"))
    metadata = {**metadata, **authority_provenance}
    preview, truncated = _body_preview(data.get("body_inline"), limit=body_limit)
    provenance = _provenance(
        metadata=metadata,
        source=authority_provenance.get("source") or data.get("conversation_source"),
        agent=data.get("sender"),
    )
    return {
        "message_id": data["message_id"],
        "conversation_id": data["conversation_id"],
        "in_reply_to": data.get("in_reply_to"),
        "kind": data["kind"],
        "sender": data["sender"],
        "recipient": data.get("recipient"),
        "request_state": data.get("request_state"),
        "created_at": data["created_at"],
        "body_preview": preview,
        "body_truncated": truncated,
        "body_available": bool(data.get("body_inline") or data.get("body_artifact_id")),
        "artifact_available": bool(data.get("body_artifact_id")),
        "metadata": metadata,
        "read_only": True,
        **provenance,
    }


@router.get("/messages")
def fleet_messages(
    kind: str | None = Query(default=None),
    state: str | None = Query(default=None),
    agent: str | None = Query(default=None),
    source: str | None = Query(default=None),
    conversation: str | None = Query(default=None),
    since: str | None = Query(default=None),
    until: str | None = Query(default=None),
    limit: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    """Message metadata and redacted inline previews, never artifact body content."""
    since_value = _normalize_time(since, "since")
    until_value = _normalize_time(until, "until")
    filters = {
        "kind": kind,
        "state": state,
        "agent": agent,
        "source": source,
        "conversation": conversation,
        "since": since_value,
        "until": until_value,
    }
    with _read_connection() as (connection, availability):
        if connection is None:
            return _empty_collection(
                "messages", limit=limit, offset=offset, availability=availability, filters=filters
            )
        if not _table_exists(connection, "comms_messages"):
            return _empty_collection(
                "messages", limit=limit, offset=offset, availability="table_missing", filters=filters
            )
        has_conversations = _table_exists(connection, "conversations")
        has_requests = _table_exists(connection, "requests")
        has_authority_metadata = _table_exists(connection, "authority_message_metadata")
        from_sql = " FROM comms_messages AS message"
        source_select = "NULL AS conversation_source"
        request_state_select = "NULL AS request_state"
        authority_provenance_select = "NULL AS authority_provenance_json"
        if has_conversations:
            source_select = "conversation.source AS conversation_source"
            from_sql += " LEFT JOIN conversations AS conversation ON conversation.conversation_id = message.conversation_id"
        if has_requests:
            request_state_select = "request.state AS request_state"
            from_sql += " LEFT JOIN requests AS request ON request.request_message_id = message.message_id"
        if has_authority_metadata:
            authority_provenance_select = "authority_meta.provenance_json AS authority_provenance_json"
            from_sql += (
                " LEFT JOIN authority_message_metadata AS authority_meta"
                " ON authority_meta.message_id = message.message_id"
            )
        clauses: list[str] = []
        params: list[Any] = []
        if kind is not None:
            clauses.append("message.kind = ?")
            params.append(kind)
        if state is not None:
            if has_requests:
                clauses.append("request.state = ?")
                params.append(state)
            else:
                clauses.append("1 = 0")
        if agent is not None:
            agent_clause = "message.sender = ? OR message.recipient = ?"
            params.extend([agent, agent])
            if has_authority_metadata:
                agent_clause += " OR json_extract(authority_meta.provenance_json, '$.Agent') = ?"
                params.append(agent)
            clauses.append(f"({agent_clause})")
        if source is not None:
            source_expression = "message.sender"
            if has_conversations:
                source_expression = "COALESCE(conversation.source, message.sender)"
            if has_authority_metadata:
                source_expression = (
                    "COALESCE(json_extract(authority_meta.provenance_json, '$.Source'), "
                    f"{source_expression})"
                )
            clauses.append(f"{source_expression} = ?")
            params.append(source)
        if conversation is not None:
            clauses.append("message.conversation_id = ?")
            params.append(conversation)
        _time_clauses(
            "message.created_at",
            since=since_value,
            until=until_value,
            clauses=clauses,
            params=params,
        )
        return _paged_query(
            connection,
            key="messages",
            select_sql=(
                "SELECT message.message_id, message.conversation_id, message.in_reply_to, message.kind, "
                "message.sender, message.recipient, message.body_inline, message.body_artifact_id, "
                "message.metadata_json, message.created_at, "
                f"{source_select}, {request_state_select}, {authority_provenance_select}"
            ),
            from_sql=from_sql,
            clauses=clauses,
            params=params,
            order_sql="message.created_at DESC, message.message_id ASC",
            limit=limit,
            offset=offset,
            filters=filters,
            transform=_message_item,
        )


def _message_detail(connection: sqlite3.Connection, message_id: str) -> dict[str, Any] | None:
    if not _table_exists(connection, "comms_messages"):
        return None
    has_conversations = _table_exists(connection, "conversations")
    has_requests = _table_exists(connection, "requests")
    has_authority_metadata = _table_exists(connection, "authority_message_metadata")
    from_sql = " FROM comms_messages AS message"
    source_select = "NULL AS conversation_source"
    request_state_select = "NULL AS request_state"
    authority_provenance_select = "NULL AS authority_provenance_json"
    if has_conversations:
        source_select = "conversation.source AS conversation_source"
        from_sql += " LEFT JOIN conversations AS conversation ON conversation.conversation_id = message.conversation_id"
    if has_requests:
        request_state_select = "request.state AS request_state"
        from_sql += " LEFT JOIN requests AS request ON request.request_message_id = message.message_id"
    if has_authority_metadata:
        authority_provenance_select = "authority_meta.provenance_json AS authority_provenance_json"
        from_sql += (
            " LEFT JOIN authority_message_metadata AS authority_meta"
            " ON authority_meta.message_id = message.message_id"
        )
    try:
        row = connection.execute(
            (
                "SELECT message.message_id, message.conversation_id, message.in_reply_to, message.kind, "
                "message.sender, message.recipient, message.body_inline, message.body_artifact_id, "
                "message.metadata_json, message.created_at, "
                f"{source_select}, {request_state_select}, {authority_provenance_select}"
                f"{from_sql} WHERE message.message_id = ?"
            ),
            (message_id,),
        ).fetchone()
    except sqlite3.Error:
        return None
    return _message_item(row, body_limit=MAX_BODY_DETAIL_CHARS) if row is not None else None


@router.get("/messages/{message_id}")
def fleet_message_detail(message_id: str) -> JSONResponse:
    """A no-store, explicitly bounded inline body preview for one message."""
    with _read_connection() as (connection, _availability):
        item = _message_detail(connection, message_id) if connection is not None else None
    if item is None:
        raise HTTPException(status_code=404, detail="Message not found")
    return JSONResponse(
        content={
            "read_only": True,
            "body_policy": {
                "inline_preview_limit_chars": MAX_BODY_DETAIL_CHARS,
                "artifact_content": "omitted",
                "redaction": "credential_like_values_redacted",
            },
            "message": item,
        },
        headers={"Cache-Control": "no-store"},
    )


def _discussion_item(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    provenance = _provenance(source=data.get("source"), agent="conversation")
    return {
        "conversation_id": data["conversation_id"],
        "source": provenance["source"],
        "agent": provenance["agent"],
        "via": provenance["via"],
        "title": _safe_text(data.get("title"), limit=240, fallback="") or None,
        "created_at": data["created_at"],
        "latest_message_at": data.get("latest_message_at"),
        "message_count": int(data.get("message_count") or 0),
        "rounds_requested": data.get("rounds_requested"),
        "read_only": True,
    }


@router.get("/discussions")
def fleet_discussions(
    kind: str | None = Query(default=None),
    state: str | None = Query(default=None),
    agent: str | None = Query(default=None),
    source: str | None = Query(default=None),
    conversation: str | None = Query(default=None),
    since: str | None = Query(default=None),
    until: str | None = Query(default=None),
    limit: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    """Conversations plus message/round counts; messages remain separately bounded."""
    since_value = _normalize_time(since, "since")
    until_value = _normalize_time(until, "until")
    filters = {
        "kind": kind,
        "state": state,
        "agent": agent,
        "source": source,
        "conversation": conversation,
        "since": since_value,
        "until": until_value,
    }
    with _read_connection() as (connection, availability):
        if connection is None:
            return _empty_collection(
                "discussions", limit=limit, offset=offset, availability=availability, filters=filters
            )
        if not _table_exists(connection, "conversations"):
            return _empty_collection(
                "discussions", limit=limit, offset=offset, availability="table_missing", filters=filters
            )
        has_messages = _table_exists(connection, "comms_messages")
        has_requests = _table_exists(connection, "requests")
        has_acp = _table_exists(connection, "acp_conversations")
        from_sql = " FROM conversations AS conversation"
        message_count = "0 AS message_count"
        latest_message = "NULL AS latest_message_at"
        rounds = "NULL AS rounds_requested"
        if has_messages:
            message_count = "COUNT(message.message_id) AS message_count"
            latest_message = "MAX(message.created_at) AS latest_message_at"
            from_sql += " LEFT JOIN comms_messages AS message ON message.conversation_id = conversation.conversation_id"
        if has_acp:
            rounds = "MAX(acp.rounds_requested) AS rounds_requested"
            from_sql += " LEFT JOIN acp_conversations AS acp ON acp.conversation_id = conversation.conversation_id"
        clauses: list[str] = []
        params: list[Any] = []
        if source is not None:
            clauses.append("conversation.source = ?")
            params.append(source)
        if conversation is not None:
            clauses.append("conversation.conversation_id = ?")
            params.append(conversation)
        if kind is not None:
            if has_messages:
                clauses.append(
                    "EXISTS (SELECT 1 FROM comms_messages AS kind_message "
                    "WHERE kind_message.conversation_id = conversation.conversation_id "
                    "AND kind_message.kind = ?)"
                )
                params.append(kind)
            else:
                clauses.append("1 = 0")
        if agent is not None:
            if has_messages:
                clauses.append(
                    "EXISTS (SELECT 1 FROM comms_messages AS agent_message "
                    "WHERE agent_message.conversation_id = conversation.conversation_id "
                    "AND (agent_message.sender = ? OR agent_message.recipient = ?))"
                )
                params.extend([agent, agent])
            else:
                clauses.append("1 = 0")
        if state is not None:
            if has_messages and has_requests:
                clauses.append(
                    "EXISTS (SELECT 1 FROM requests AS state_request "
                    "JOIN comms_messages AS state_message "
                    "ON state_message.message_id = state_request.request_message_id "
                    "WHERE state_message.conversation_id = conversation.conversation_id "
                    "AND state_request.state = ?)"
                )
                params.append(state)
            else:
                clauses.append("1 = 0")
        _time_clauses(
            "conversation.created_at",
            since=since_value,
            until=until_value,
            clauses=clauses,
            params=params,
        )
        where_sql = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        group_sql = " GROUP BY conversation.conversation_id, conversation.source, conversation.title, conversation.created_at"
        try:
            total = int(
                connection.execute(
                    f"SELECT COUNT(*) FROM conversations AS conversation{where_sql}", params
                ).fetchone()[0]
            )
            latest_order = (
                "COALESCE(MAX(message.created_at), conversation.created_at)"
                if has_messages
                else "conversation.created_at"
            )
            rows = connection.execute(
                (
                    "SELECT conversation.conversation_id, conversation.source, conversation.title, "
                    f"conversation.created_at, {message_count}, {latest_message}, {rounds}{from_sql}{where_sql}"
                    f"{group_sql} ORDER BY {latest_order} DESC, "
                    "conversation.conversation_id ASC LIMIT ? OFFSET ?"
                ),
                [*params, limit, offset],
            ).fetchall()
        except sqlite3.Error:
            logger.warning("Fleet observer discussion query failed")
            return _empty_collection(
                "discussions",
                limit=limit,
                offset=offset,
                availability="db_unavailable",
                filters=filters,
            )
        return _collection(
            "discussions",
            [_discussion_item(row) for row in rows],
            total=total,
            limit=limit,
            offset=offset,
            availability="available" if total else "empty",
            filters=filters,
        )


@router.get("/discussions/{conversation_id}")
def fleet_discussion_detail(
    conversation_id: str,
    limit: int = Query(default=50, ge=1, le=MAX_DETAIL_ROWS),
    offset: int = Query(default=0, ge=0),
) -> JSONResponse:
    """One bounded discussion timeline without artifact retrieval or write controls."""
    with _read_connection() as (connection, _availability):
        if connection is None or not _table_exists(connection, "conversations"):
            raise HTTPException(status_code=404, detail="Discussion not found")
        message_summary = (
            "(SELECT COUNT(*) FROM comms_messages AS summary_message "
            "WHERE summary_message.conversation_id = conversation.conversation_id) AS message_count, "
            "(SELECT MAX(summary_message.created_at) FROM comms_messages AS summary_message "
            "WHERE summary_message.conversation_id = conversation.conversation_id) AS latest_message_at"
            if _table_exists(connection, "comms_messages")
            else "0 AS message_count, NULL AS latest_message_at"
        )
        rounds_summary = (
            "(SELECT MAX(summary_acp.rounds_requested) FROM acp_conversations AS summary_acp "
            "WHERE summary_acp.conversation_id = conversation.conversation_id) AS rounds_requested"
            if _table_exists(connection, "acp_conversations")
            else "NULL AS rounds_requested"
        )
        row = connection.execute(
            "SELECT conversation.conversation_id, conversation.source, conversation.title, "
            f"conversation.created_at, {message_summary}, {rounds_summary} "
            "FROM conversations AS conversation WHERE conversation.conversation_id = ?",
            (conversation_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Discussion not found")
        if not _table_exists(connection, "comms_messages"):
            messages = _empty_collection(
                "messages",
                limit=limit,
                offset=offset,
                availability="table_missing",
                filters={"conversation": conversation_id},
            )
        else:
            has_authority_metadata = _table_exists(connection, "authority_message_metadata")
            from_sql = " FROM comms_messages"
            authority_provenance_select = "NULL AS authority_provenance_json"
            if has_authority_metadata:
                authority_provenance_select = "authority_meta.provenance_json AS authority_provenance_json"
                from_sql += (
                    " LEFT JOIN authority_message_metadata AS authority_meta"
                    " ON authority_meta.message_id = comms_messages.message_id"
                )
            messages = _paged_query(
                connection,
                key="messages",
                select_sql=(
                    "SELECT comms_messages.message_id AS message_id, "
                    "comms_messages.conversation_id AS conversation_id, "
                    "comms_messages.in_reply_to AS in_reply_to, comms_messages.kind AS kind, "
                    "comms_messages.sender AS sender, comms_messages.recipient AS recipient, "
                    "comms_messages.body_inline AS body_inline, "
                    "comms_messages.body_artifact_id AS body_artifact_id, "
                    "comms_messages.metadata_json AS metadata_json, "
                    "comms_messages.created_at AS created_at, NULL AS conversation_source, "
                    f"NULL AS request_state, {authority_provenance_select}"
                ),
                from_sql=from_sql,
                clauses=["comms_messages.conversation_id = ?"],
                params=[conversation_id],
                order_sql="comms_messages.created_at ASC, comms_messages.message_id ASC",
                limit=limit,
                offset=offset,
                filters={"conversation": conversation_id},
                transform=_message_item,
            )
    return JSONResponse(
        content={
            "read_only": True,
            "body_policy": "redacted_inline_previews_only_artifact_content_omitted",
            "discussion": _discussion_item(row),
            "messages": messages,
        },
        headers={"Cache-Control": "no-store"},
    )


def _review_item(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    return {
        "review_id": data["review_id"],
        "repository": data["repository"],
        "pr_number": data["pr_number"],
        "head_sha": data["head_sha"],
        "gate_kind": data["gate_kind"],
        "state": data["state"],
        "created_at": data["created_at"],
        "attempt_count": int(data.get("attempt_count") or 0),
        "latest_attempt_state": data.get("latest_attempt_state"),
        "publication_count": int(data.get("publication_count") or 0),
        "sealed_verdict_available": bool(data.get("sealed_verdict_artifact_id")),
        "source": "formal-review",
        "agent": "review-gate",
        "via": "fleet-comms",
        "read_only": True,
    }


@router.get("/reviews")
def fleet_reviews(
    kind: str | None = Query(default=None),
    state: str | None = Query(default=None),
    source: str | None = Query(default=None),
    pr: int | None = Query(default=None, ge=1),
    since: str | None = Query(default=None),
    until: str | None = Query(default=None),
    limit: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    """Formal-review jobs, attempts, and publication counts without sealed blobs."""
    since_value = _normalize_time(since, "since")
    until_value = _normalize_time(until, "until")
    filters = {
        "kind": kind,
        "state": state,
        "source": source,
        "pr": pr,
        "since": since_value,
        "until": until_value,
    }
    with _read_connection() as (connection, availability):
        if connection is None:
            return _empty_collection(
                "reviews", limit=limit, offset=offset, availability=availability, filters=filters
            )
        if not _table_exists(connection, "formal_review_jobs"):
            return _empty_collection(
                "reviews", limit=limit, offset=offset, availability="table_missing", filters=filters
            )
        has_attempts = _table_exists(connection, "formal_review_attempts")
        has_publications = _table_exists(connection, "github_publications")
        attempt_count = "0 AS attempt_count"
        latest_attempt = "NULL AS latest_attempt_state"
        publication_count = "0 AS publication_count"
        if has_attempts:
            attempt_count = (
                "(SELECT COUNT(*) FROM formal_review_attempts AS attempt "
                "WHERE attempt.review_id = review.review_id) AS attempt_count"
            )
            latest_attempt = (
                "(SELECT completion_state FROM formal_review_attempts AS latest_attempt "
                "WHERE latest_attempt.review_id = review.review_id "
                "ORDER BY latest_attempt.attempt_number DESC LIMIT 1) AS latest_attempt_state"
            )
        if has_publications:
            publication_count = (
                "(SELECT COUNT(*) FROM github_publications AS publication "
                "WHERE publication.review_id = review.review_id) AS publication_count"
            )
        clauses: list[str] = []
        params: list[Any] = []
        if kind is not None:
            clauses.append("review.gate_kind = ?")
            params.append(kind)
        if state is not None:
            clauses.append("review.state = ?")
            params.append(state)
        if source is not None and source != "formal-review":
            clauses.append("1 = 0")
        if pr is not None:
            clauses.append("review.pr_number = ?")
            params.append(pr)
        _time_clauses(
            "review.created_at",
            since=since_value,
            until=until_value,
            clauses=clauses,
            params=params,
        )
        return _paged_query(
            connection,
            key="reviews",
            select_sql=(
                "SELECT review.review_id, review.repository, review.pr_number, review.head_sha, review.gate_kind, "
                "review.state, review.sealed_verdict_artifact_id, review.created_at, "
                f"{attempt_count}, {latest_attempt}, {publication_count}"
            ),
            from_sql=" FROM formal_review_jobs AS review",
            clauses=clauses,
            params=params,
            order_sql="review.created_at DESC, review.review_id ASC",
            limit=limit,
            offset=offset,
            filters=filters,
            transform=_review_item,
        )


@router.get("/reviews/{review_id}")
def fleet_review_detail(
    review_id: str,
    attempt_limit: int = Query(default=MAX_DETAIL_ROWS, ge=1, le=MAX_DETAIL_ROWS),
) -> JSONResponse:
    """Bounded formal-review detail; sealed verdict and raw captures are never read."""
    with _read_connection() as (connection, _availability):
        if connection is None or not _table_exists(connection, "formal_review_jobs"):
            raise HTTPException(status_code=404, detail="Review not found")
        row = connection.execute(
            """
            SELECT review_id, repository, pr_number, head_sha, gate_kind, state,
                   sealed_verdict_artifact_id, created_at
            FROM formal_review_jobs
            WHERE review_id = ?
            """,
            (review_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Review not found")
        attempts: list[dict[str, Any]] = []
        if _table_exists(connection, "formal_review_attempts"):
            attempts = [
                {
                    "review_attempt_id": attempt["review_attempt_id"],
                    "attempt_number": attempt["attempt_number"],
                    "completion_state": attempt["completion_state"],
                    "created_at": attempt["created_at"],
                }
                for attempt in connection.execute(
                    """
                    SELECT review_attempt_id, attempt_number, completion_state, created_at
                    FROM formal_review_attempts
                    WHERE review_id = ?
                    ORDER BY attempt_number DESC, review_attempt_id ASC
                    LIMIT ?
                    """,
                    (review_id, attempt_limit),
                ).fetchall()
            ]
        publications: list[dict[str, Any]] = []
        if _table_exists(connection, "github_publications"):
            publications = [
                {
                    "publication_id": publication["publication_id"],
                    "head_sha": publication["head_sha"],
                    "status_context": publication["status_context"],
                    "published_at": publication["published_at"],
                }
                for publication in connection.execute(
                    """
                    SELECT publication_id, head_sha, status_context, published_at
                    FROM github_publications
                    WHERE review_id = ?
                    ORDER BY published_at DESC, publication_id ASC
                    LIMIT ?
                    """,
                    (review_id, attempt_limit),
                ).fetchall()
            ]
    return JSONResponse(
        content={
            "read_only": True,
            "detail_policy": "raw_capture_and_sealed_verdict_blobs_omitted",
            "review": _review_item(row),
            "attempts": attempts,
            "publications": publications,
        },
        headers={"Cache-Control": "no-store"},
    )


def _dead_letter_item(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    authority_provenance = _safe_metadata(data.get("authority_provenance_json"))
    provenance = _provenance(
        metadata=authority_provenance,
        source=authority_provenance.get("source") or data.get("conversation_source"),
        agent=data.get("resolved_recipient"),
    )
    return {
        "dead_letter_id": data["dead_letter_id"],
        "request_id": data.get("request_id"),
        "delivery_id": data.get("delivery_id"),
        "reason": _safe_text(data["reason"], limit=160),
        "successor": data.get("successor"),
        "original_expires_at": data.get("original_expires_at"),
        "request_state": data.get("request_state"),
        "created_at": data["created_at"],
        "read_only": True,
        **provenance,
    }


@router.get("/dead-letters")
def fleet_dead_letters(
    state: str | None = Query(default=None),
    agent: str | None = Query(default=None),
    source: str | None = Query(default=None),
    since: str | None = Query(default=None),
    until: str | None = Query(default=None),
    limit: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    """Current authority DLQ metadata, or the legacy read projection during rollback."""
    since_value = _normalize_time(since, "since")
    until_value = _normalize_time(until, "until")
    filters = {
        "state": state,
        "agent": agent,
        "source": source,
        "since": since_value,
        "until": until_value,
    }
    with _read_connection() as (connection, availability):
        if connection is None:
            return _empty_collection(
                "dead_letters", limit=limit, offset=offset, availability=availability, filters=filters
            )
        if _safe_plane_status()["mode"] == "authority":
            if not _table_exists(connection, "authority_dead_letters"):
                return _empty_collection(
                    "dead_letters",
                    limit=limit,
                    offset=offset,
                    availability="table_missing",
                    filters=filters,
                )
            clauses: list[str] = []
            params: list[Any] = []
            if state is not None:
                clauses.append("COALESCE(delivery.state, job.state) = ?")
                params.append(state)
            if agent is not None:
                clauses.append("COALESCE(delivery.recipient, 'authority-job') = ?")
                params.append(agent)
            if source is not None:
                clauses.append(
                    "COALESCE(json_extract(authority_meta.provenance_json, '$.Source'), "
                    "'authority') = ?"
                )
                params.append(source)
            _time_clauses(
                "letter.created_at",
                since=since_value,
                until=until_value,
                clauses=clauses,
                params=params,
            )
            return _paged_query(
                connection,
                key="dead_letters",
                select_sql=(
                    "SELECT letter.dead_letter_id, job.subject_id AS request_id, "
                    "letter.delivery_id, letter.reason_code AS reason, NULL AS successor, "
                    "COALESCE(delivery.deadline_at, job.deadline_at) AS original_expires_at, "
                    "letter.created_at, COALESCE(delivery.state, job.state) AS request_state, "
                    "delivery.recipient AS resolved_recipient, 'authority' AS conversation_source, "
                    "authority_meta.provenance_json AS authority_provenance_json"
                ),
                from_sql=(
                    " FROM authority_dead_letters AS letter"
                    " LEFT JOIN authority_deliveries AS delivery"
                    " ON delivery.delivery_id = letter.delivery_id"
                    " LEFT JOIN comms_messages AS message"
                    " ON message.message_id = delivery.message_id"
                    " LEFT JOIN authority_message_metadata AS authority_meta"
                    " ON authority_meta.message_id = message.message_id"
                    " LEFT JOIN authority_jobs AS job ON job.job_id = letter.job_id"
                ),
                clauses=clauses,
                params=params,
                order_sql="letter.created_at DESC, letter.dead_letter_id ASC",
                limit=limit,
                offset=offset,
                filters=filters,
                transform=_dead_letter_item,
            )
        if not _table_exists(connection, "dead_letters"):
            return _empty_collection(
                "dead_letters", limit=limit, offset=offset, availability="table_missing", filters=filters
            )
        has_requests = _table_exists(connection, "requests")
        has_messages = _table_exists(connection, "comms_messages")
        has_conversations = _table_exists(connection, "conversations")
        has_authority_metadata = _table_exists(connection, "authority_message_metadata")
        from_sql = " FROM dead_letters AS letter"
        request_state = "NULL AS request_state"
        resolved = "NULL AS resolved_recipient"
        source_select = "NULL AS conversation_source"
        authority_provenance_select = "NULL AS authority_provenance_json"
        if has_requests:
            request_state = "request.state AS request_state"
            resolved = "request.resolved_recipient AS resolved_recipient"
            from_sql += " LEFT JOIN requests AS request ON request.request_id = letter.request_id"
        if has_requests and has_messages:
            from_sql += " LEFT JOIN comms_messages AS message ON message.message_id = request.request_message_id"
        if has_requests and has_messages and has_conversations:
            source_select = "conversation.source AS conversation_source"
            from_sql += " LEFT JOIN conversations AS conversation ON conversation.conversation_id = message.conversation_id"
        if has_requests and has_messages and has_authority_metadata:
            authority_provenance_select = "authority_meta.provenance_json AS authority_provenance_json"
            from_sql += (
                " LEFT JOIN authority_message_metadata AS authority_meta"
                " ON authority_meta.message_id = message.message_id"
            )
        clauses: list[str] = []
        params: list[Any] = []
        if state is not None:
            if has_requests:
                clauses.append("request.state = ?")
                params.append(state)
            else:
                clauses.append("1 = 0")
        if agent is not None:
            if has_requests:
                agent_clause = "request.resolved_recipient = ?"
                params.append(agent)
                if has_messages and has_authority_metadata:
                    agent_clause += " OR json_extract(authority_meta.provenance_json, '$.Agent') = ?"
                    params.append(agent)
                clauses.append(f"({agent_clause})")
            else:
                clauses.append("1 = 0")
        if source is not None:
            if has_requests and has_messages and has_conversations:
                source_expression = "conversation.source"
                if has_authority_metadata:
                    source_expression = (
                        "COALESCE(json_extract(authority_meta.provenance_json, '$.Source'), "
                        f"{source_expression})"
                    )
                clauses.append(f"{source_expression} = ?")
                params.append(source)
            else:
                clauses.append("1 = 0")
        _time_clauses(
            "letter.created_at",
            since=since_value,
            until=until_value,
            clauses=clauses,
            params=params,
        )
        return _paged_query(
            connection,
            key="dead_letters",
            select_sql=(
                "SELECT letter.dead_letter_id, letter.request_id, letter.delivery_id, letter.reason, "
                "letter.successor, letter.original_expires_at, letter.created_at, "
                f"{request_state}, {resolved}, {source_select}, {authority_provenance_select}"
            ),
            from_sql=from_sql,
            clauses=clauses,
            params=params,
            order_sql="letter.created_at DESC, letter.dead_letter_id ASC",
            limit=limit,
            offset=offset,
            filters=filters,
            transform=_dead_letter_item,
        )


@router.get("/migrations")
def fleet_migrations() -> dict[str, Any]:
    """Schema migration status from the existing plane, without applying a migration."""
    known = [{"version": item.version, "name": item.name} for item in MIGRATIONS]
    with _read_connection() as (connection, availability):
        if connection is None:
            return {
                "read_only": True,
                "availability": availability,
                "known_migrations": known,
                "migrations": [],
                "applied_version": None,
            }
        if not _table_exists(connection, "comms_schema_migrations"):
            return {
                "read_only": True,
                "availability": "table_missing",
                "known_migrations": known,
                "migrations": [],
                "applied_version": None,
            }
        try:
            rows = connection.execute(
                "SELECT version, name, applied_at FROM comms_schema_migrations ORDER BY version ASC"
            ).fetchall()
        except sqlite3.Error:
            rows = []
            availability = "db_unavailable"
    migrations = [
        {"version": int(row["version"]), "name": row["name"], "applied_at": row["applied_at"]}
        for row in rows
    ]
    return {
        "read_only": True,
        "availability": "available" if migrations else availability,
        "known_migrations": known,
        "migrations": migrations,
        "applied_version": migrations[-1]["version"] if migrations else None,
    }


def _acp_item(item: dict[str, Any]) -> dict[str, Any]:
    participants = item.get("participants") if isinstance(item.get("participants"), list) else []
    agent = " / ".join(_safe_text(value, fallback="") for value in participants if value) or "unknown"
    return {
        **item,
        "source": "acpx",
        "agent": agent,
        "via": "fleet-comms",
        "read_only": True,
    }


@router.get("/acp/conversations")
def fleet_acp_conversations(
    state: str | None = Query(default=None),
    agent: str | None = Query(default=None),
    source: str | None = Query(default=None),
    conversation: str | None = Query(default=None),
    since: str | None = Query(default=None),
    until: str | None = Query(default=None),
    limit: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    """Reuse the ACP read model for body-free conversation and round observability."""
    since_value = _normalize_time(since, "since")
    until_value = _normalize_time(until, "until")
    filters = {
        "state": state,
        "agent": agent,
        "source": source,
        "conversation": conversation,
        "since": since_value,
        "until": until_value,
    }
    payload = list_acp_conversations(limit=MAX_ACP_SCAN)
    availability = _safe_text(payload.get("availability"), fallback="unavailable")
    records = payload.get("conversations") if isinstance(payload.get("conversations"), list) else []
    filtered: list[dict[str, Any]] = []
    for raw in records:
        if not isinstance(raw, dict):
            continue
        record = _acp_item(raw)
        created_at = record.get("created_at")
        if state is not None and state not in {record.get("classification"), record.get("current_state")}:
            continue
        if agent is not None and agent not in record.get("participants", []):
            continue
        if source is not None and source != "acpx":
            continue
        if conversation is not None and conversation != record.get("conversation_id"):
            continue
        if since_value is not None and (not isinstance(created_at, str) or created_at < since_value):
            continue
        if until_value is not None and (not isinstance(created_at, str) or created_at > until_value):
            continue
        filtered.append(record)
    return _collection(
        "conversations",
        filtered[offset : offset + limit],
        total=len(filtered),
        limit=limit,
        offset=offset,
        availability=availability,
        filters=filters,
    )


@router.get("/acp/conversations/{conversation_id}")
def fleet_acp_conversation_detail(conversation_id: str) -> JSONResponse:
    """Reuse the existing body-free ACP event timeline for one conversation."""
    record = get_acp_conversation(conversation_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return JSONResponse(
        content={
            "read_only": True,
            "body_policy": "events_only_no_transcript_or_artifact_content",
            "conversation": _acp_item(record),
        },
        headers={"Cache-Control": "no-store"},
    )


@router.get("/activity")
def fleet_activity(
    state: str | None = Query(default=None),
    agent: str | None = Query(default=None),
    source: str | None = Query(default=None),
    via: str | None = Query(default=None),
    since: str | None = Query(default=None),
    until: str | None = Query(default=None),
    limit: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    """Recent runtime provenance records projected under the unified observer."""
    since_value = _normalize_time(since, "since")
    until_value = _normalize_time(until, "until")
    filters = {
        "state": state,
        "agent": agent,
        "source": source,
        "via": via,
        "since": since_value,
        "until": until_value,
    }
    raw_records = recent_runtime_records(limit=MAX_ACTIVITY_SCAN).get("records", [])
    records: list[dict[str, Any]] = []
    for raw in raw_records:
        if not isinstance(raw, dict):
            continue
        record = {
            "ts": raw.get("ts"),
            "source": _safe_text(raw.get("source")),
            "agent": _safe_text(raw.get("agent")),
            "via": _safe_text(raw.get("via") or raw.get("entrypoint")),
            "model": _safe_text(raw.get("model"), fallback="") or None,
            "outcome": _safe_text(raw.get("outcome"), fallback="") or None,
            "duration_s": raw.get("duration_s"),
            "source_provenance": _safe_text(raw.get("source_provenance"), fallback="unknown"),
            "source_task_id": _safe_text(raw.get("source_task_id"), fallback="") or None,
            "read_only": True,
        }
        timestamp = record["ts"]
        if state is not None and state != record["outcome"]:
            continue
        if agent is not None and agent != record["agent"]:
            continue
        if source is not None and source != record["source"]:
            continue
        if via is not None and via != record["via"]:
            continue
        if since_value is not None and (not isinstance(timestamp, str) or timestamp < since_value):
            continue
        if until_value is not None and (not isinstance(timestamp, str) or timestamp > until_value):
            continue
        records.append(record)
    return _collection(
        "records",
        records[offset : offset + limit],
        total=len(records),
        limit=limit,
        offset=offset,
        availability="available" if records else "empty",
        filters=filters,
    )
