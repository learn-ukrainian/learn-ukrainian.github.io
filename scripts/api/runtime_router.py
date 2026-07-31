"""Runtime observability API router."""

from __future__ import annotations

import asyncio
import importlib
import inspect
import json
import os
import sqlite3
import sys
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from .config import BATCH_STATE_DIR

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent_runtime.adapters.acpx import (
    GROK_SHADOW_EFFORT,
    GROK_SHADOW_MODEL,
    PINNED_GROK_VERSION,
    AcpxAdapter,
    AcpxGrokShadowAdapter,
)
from agent_runtime.adapters.acpx import (
    PINNED_VERSION as ACPX_PINNED_VERSION,
)
from agent_runtime.adapters.acpx import (
    TRANSPORT_ENV as ACPX_TRANSPORT_ENV,
)
from agent_runtime.adapters.gemini import has_gemini_oauth_credentials, resolve_gemini_auth_mode
from agent_runtime.usage import has_headroom

from scripts.fleet_comms.message_plane import default_plane_root
from scripts.orchestration.codex_transport_health import (
    DEFAULT_CONFIG_PATH as CODEX_TRANSPORT_CONFIG_PATH,
)
from scripts.orchestration.codex_transport_health import (
    TRANSPORT_RECEIPT_PATH as CODEX_TRANSPORT_RECEIPT_PATH,
)
from scripts.orchestration.codex_transport_health import current_transport_health

router = APIRouter(tags=["runtime"])

ADAPTERS_DIR = Path(__file__).resolve().parent.parent / "agent_runtime" / "adapters"
USAGE_DIR = BATCH_STATE_DIR / "api_usage"
_KNOWN_OUTCOMES = ("ok", "error", "timeout", "rate_limited")
_ACP_PARTICIPANTS = ("root", "codex", "grok")
_ACP_STATES = frozenset({
    "CREATED",
    "INITIAL_FANOUT",
    "INITIAL_COMPLETE",
    "PARTIAL",
    "CROSS_EXCHANGE",
    "CROSS_EXCHANGE_COMPLETE",
    "SYNTHESIS",
    "COMPLETE",
    "PARTIAL_COMPLETE",
    "FAILED",
    "CANCELLED",
})
_ACP_EVENT_TYPES = frozenset({
    "CONVERSATION_CREATED",
    "CREATED",
    "STATE",
    "CALL_RESERVED",
    "CALL_TERMINAL",
    "SYNTHESIS_TERMINAL",
    "ORPHAN_RESERVATION",
    "INITIAL_FANOUT",
    "PARTICIPANT_MESSAGE",
    "PARTICIPANT_COMPLETE",
    "CROSS_EXCHANGE",
    "CROSS_EXCHANGE_MESSAGE",
    "CROSS_EXCHANGE_COMPLETE",
    "SYNTHESIS",
    "SYNTHESIS_COMPLETE",
    "DUPLICATE_SUPPRESSED",
    "BUDGET_EXHAUSTED",
    "DEADLINE_EXCEEDED",
    "FAILED",
    "CANCELLED",
})
_ACP_OUTCOMES = frozenset({
    "queued",
    "running",
    "succeeded",
    "partial",
    "failed",
    "cancelled",
    "duplicate_suppressed",
    "budget_exhausted",
    "deadline_exceeded",
})
_ACP_TERMINATIONS = frozenset({
    "duplicate_suppressed",
    "budget_exhausted",
    "deadline_exceeded",
    "cancelled",
    "failed",
})
_ACP_MESSAGE_EVENTS = frozenset({
    "PARTICIPANT_MESSAGE",
    "PARTICIPANT_COMPLETE",
    "CROSS_EXCHANGE_MESSAGE",
    "CROSS_EXCHANGE_COMPLETE",
    "CALL_TERMINAL",
    "SYNTHESIS_TERMINAL",
})
_ACP_EVENT_TYPE_ALIASES = {
    "created": "CONVERSATION_CREATED",
    "conversation_created": "CONVERSATION_CREATED",
    "state": "STATE",
    "call_reserved": "CALL_RESERVED",
    "call_terminal": "CALL_TERMINAL",
    "synthesis_terminal": "SYNTHESIS_TERMINAL",
    "orphan_reservation": "ORPHAN_RESERVATION",
    "initial_fanout": "INITIAL_FANOUT",
    "fanout": "INITIAL_FANOUT",
    "participant_message": "PARTICIPANT_MESSAGE",
    "message": "PARTICIPANT_MESSAGE",
    "participant_complete": "PARTICIPANT_COMPLETE",
    "cross_exchange": "CROSS_EXCHANGE",
    "cross_exchange_message": "CROSS_EXCHANGE_MESSAGE",
    "cross_exchange_complete": "CROSS_EXCHANGE_COMPLETE",
    "synthesis": "SYNTHESIS",
    "synthesis_complete": "SYNTHESIS_COMPLETE",
    "duplicate_suppressed": "DUPLICATE_SUPPRESSED",
    "budget_exhausted": "BUDGET_EXHAUSTED",
    "deadline_exceeded": "DEADLINE_EXCEEDED",
    "budget_terminal": "BUDGET_EXHAUSTED",
    "deadline_terminal": "DEADLINE_EXCEEDED",
    "failed": "FAILED",
    "cancelled": "CANCELLED",
}


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _isoformat_z(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _usage_day_from_name(path: Path) -> date | None:
    stem = path.stem
    if not stem.startswith("usage_"):
        return None
    try:
        day_str = stem.rsplit("_", 1)[1]
        return date.fromisoformat(day_str)
    except (IndexError, ValueError):
        return None


def _usage_files(*, days: int) -> list[Path]:
    if not USAGE_DIR.exists():
        return []
    today = datetime.now(UTC).date()
    earliest = today - timedelta(days=max(1, days) - 1)
    files: list[Path] = []
    # Hyphens are valid in both agent and entrypoint names, so the filename's
    # ``<agent>-<entrypoint>`` segment is intentionally not parsed here.
    # Callers apply exact filters to the JSONL record fields instead.
    for path in sorted(USAGE_DIR.glob("usage_*.jsonl")):
        day = _usage_day_from_name(path)
        if day is None or day < earliest or day > today:
            continue
        files.append(path)
    return files


def _today_usage_files() -> list[Path]:
    return _usage_files(days=1)


def _iter_usage_records(paths: list[Path]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in paths:
        try:
            with open(path, encoding="utf-8") as handle:
                for raw in handle:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        data = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(data, dict):
                        records.append(data)
        except OSError:
            continue
    return records


def _new_outcome_bucket() -> dict[str, Any]:
    bucket: dict[str, Any] = {"total": 0, "total_duration_s": 0.0}
    for key in _KNOWN_OUTCOMES:
        bucket[key] = 0
    return bucket


def _update_outcome_bucket(bucket: dict[str, Any], record: dict[str, Any]) -> None:
    bucket["total"] += 1
    outcome = str(record.get("outcome") or "")
    if outcome in _KNOWN_OUTCOMES:
        bucket[outcome] += 1
    duration = record.get("duration_s")
    if isinstance(duration, (int, float)):
        bucket["total_duration_s"] = round(bucket["total_duration_s"] + float(duration), 3)


def _new_comparison_side() -> dict[str, Any]:
    side = {key: 0 for key in _KNOWN_OUTCOMES}
    side.update({"total": 0, "total_duration_s": 0.0, "tokens_observed": 0, "total_tokens": 0})
    return side


def _update_comparison_side(
    side: dict[str, Any],
    record: dict[str, Any],
    *,
    prefix: str,
) -> None:
    outcome = str(record.get(f"{prefix}_outcome") or "")
    side["total"] += 1
    if outcome in _KNOWN_OUTCOMES:
        side[outcome] += 1
    duration = record.get(f"{prefix}_duration_s")
    if isinstance(duration, (int, float)) and not isinstance(duration, bool):
        side["total_duration_s"] = round(side["total_duration_s"] + float(duration), 3)
    tokens = record.get(f"{prefix}_tokens")
    if isinstance(tokens, int) and not isinstance(tokens, bool) and tokens >= 0:
        side["tokens_observed"] += 1
        side["total_tokens"] += tokens


def list_runtime_agents() -> list[dict[str, Any]]:
    agents: list[dict[str, Any]] = []
    for path in sorted(ADAPTERS_DIR.glob("*.py")):
        if path.stem in {"__init__", "acpx", "base", "hermes_grok", "hermes_qwen"} or path.stem.startswith("_"):
            continue
        try:
            module = importlib.import_module(f"agent_runtime.adapters.{path.stem}")
        except Exception:
            continue

        for _, obj in inspect.getmembers(module, inspect.isclass):
            if obj.__module__ != module.__name__:
                continue
            if not all(hasattr(obj, attr) for attr in ("name", "default_model", "supported_modes")):
                continue
            if not callable(getattr(obj, "build_invocation", None)):
                continue
            if not callable(getattr(obj, "parse_response", None)):
                continue
            try:
                source = inspect.getsource(obj.build_invocation)
            except (OSError, TypeError):
                source = ""
            if 'shutil.which("claude")' in source:
                binary = "claude"
            elif "@anthropic-ai/claude-code@latest" in source:
                binary = "npx @anthropic-ai/claude-code@latest"
            elif 'shutil.which("gemini")' in source:
                binary = "gemini"
            elif 'shutil.which("codex")' in source:
                binary = "codex"
            else:
                binary = str(obj.name)
            agents.append({
                "name": str(obj.name),
                "binary": binary,
                "default_model": getattr(obj, "default_model", None),
                "supported_modes": sorted(str(mode) for mode in getattr(obj, "supported_modes", [])),
            })
            break
    return agents


def summarize_runtime_usage(
    *, days: int = 7, agent: str | None = None, entrypoint: str | None = None
) -> dict[str, Any]:
    window_days = min(max(1, int(days)), 30)
    by_agent: dict[str, dict[str, Any]] = defaultdict(_new_outcome_bucket)
    by_entrypoint: dict[str, dict[str, Any]] = defaultdict(_new_outcome_bucket)
    total = 0

    for record in _iter_usage_records(_usage_files(days=window_days)):
        record_agent = record.get("agent")
        record_entrypoint = record.get("entrypoint")
        if agent and record_agent != agent:
            continue
        if entrypoint and record_entrypoint != entrypoint:
            continue
        total += 1
        if record_agent:
            _update_outcome_bucket(by_agent[str(record_agent)], record)
        if record_entrypoint:
            _update_outcome_bucket(by_entrypoint[str(record_entrypoint)], record)

    return {
        "window_days": window_days,
        "records_total": total,
        "by_agent": dict(by_agent),
        "by_entrypoint": dict(by_entrypoint),
    }


def acpx_shadow_overview(*, days: int = 7) -> dict[str, Any]:
    """Return a sanitized ACPX shadow posture and evidence snapshot.

    This is deliberately not a transport-health probe. It reads the configured
    mode plus already-persisted aggregate usage evidence; it never launches an
    agent, checks credentials, or exposes per-call identifiers and excerpts.
    """
    window_days = min(max(1, int(days)), 30)
    configured_mode = os.environ.get(ACPX_TRANSPORT_ENV, "off").strip().lower()
    mode = configured_mode if configured_mode in {"off", "shadow"} else "invalid"

    seat_specs = (
        {
            "name": AcpxAdapter.name,
            "target": "codex",
            "model": AcpxAdapter.default_model,
            "effort": None,
        },
        {
            "name": AcpxGrokShadowAdapter.name,
            "target": "grok",
            "model": GROK_SHADOW_MODEL,
            "effort": GROK_SHADOW_EFFORT,
        },
    )
    evidence_by_seat = {
        str(seat["name"]): _new_outcome_bucket()
        for seat in seat_specs
    }
    comparison = {
        "attempts": 0,
        "comparisons": 0,
        "classification_parity": 0,
        "classification_mismatch": 0,
        "duplicates_suppressed": 0,
        "busy_refusals": 0,
        "native": _new_comparison_side(),
        "shadow": _new_comparison_side(),
    }
    records = _iter_usage_records(_usage_files(days=window_days))
    for record in records:
        record_agent = str(record.get("agent") or "")
        if record_agent in evidence_by_seat:
            _update_outcome_bucket(evidence_by_seat[record_agent], record)
        if (
            record_agent == "acpx-shadow-pilot"
            and record.get("event") == "acpx_shadow_comparison"
        ):
            comparison["attempts"] += 1
            if record.get("duplicate") is True:
                comparison["duplicates_suppressed"] += 1
            if record.get("busy") is True:
                comparison["busy_refusals"] += 1
            if record.get("executed") is True:
                comparison["comparisons"] += 1
                if record.get("classification_parity") is True:
                    comparison["classification_parity"] += 1
                elif record.get("classification_parity") is False:
                    comparison["classification_mismatch"] += 1
                _update_comparison_side(comparison["native"], record, prefix="native")
                _update_comparison_side(comparison["shadow"], record, prefix="shadow")

    seats: list[dict[str, Any]] = []
    for seat in seat_specs:
        evidence = evidence_by_seat[str(seat["name"])]
        seats.append({
            **seat,
            "read_only": True,
            "stateless": True,
            "evidence_state": "observed" if evidence["total"] else "no_evidence",
            "evidence": {
                "window_days": window_days,
                **evidence,
            },
        })

    return {
        "generated_at": _isoformat_z(datetime.now(UTC)),
        "transport": {
            "mode": mode,
            "scope": "monitor_process",
            "default_mode": "off",
            "authority": "native_runtime",
            "posture": "evidence_only",
            "writable": False,
        },
        "pins": {
            "acpx": ACPX_PINNED_VERSION,
            "grok_cli": PINNED_GROK_VERSION,
            "validation": "before_spawn",
        },
        "comparison_evidence": {
            "window_days": window_days,
            "state": "observed" if comparison["attempts"] else "no_evidence",
            **comparison,
        },
        "seats": seats,
        "safety": {
            "max_in_flight": 1,
            "explicit_pilot_only": True,
            "backlog": False,
            "retries": False,
            "sessions": False,
            "chat": False,
            "mutations": False,
            "dispatch_authority": False,
            "routing_authority": False,
            "failover_authority": False,
            "review_authority": False,
        },
    }


def recent_runtime_records(*, limit: int = 50) -> dict[str, Any]:
    record_limit = min(max(1, int(limit)), 500)
    summaries: list[dict[str, Any]] = []
    for record in _iter_usage_records(_today_usage_files()):
        ts = _parse_iso_datetime(record.get("ts"))
        summaries.append({
            "ts": _isoformat_z(ts) if ts else record.get("ts"),
            "agent": record.get("agent"),
            "entrypoint": record.get("entrypoint"),
            "model": record.get("model"),
            "outcome": record.get("outcome"),
            "duration_s": record.get("duration_s"),
        })
    summaries.sort(key=lambda item: _parse_iso_datetime(item.get("ts")) or datetime.min.replace(tzinfo=UTC), reverse=True)
    return {"records": summaries[:record_limit]}


def runtime_recent_outcomes_today() -> dict[str, int]:
    counts = {key: 0 for key in _KNOWN_OUTCOMES}
    for record in _iter_usage_records(_today_usage_files()):
        outcome = str(record.get("outcome") or "")
        if outcome in counts:
            counts[outcome] += 1
    return counts


def _nested(data: dict[str, Any] | None, *keys: str) -> Any:
    value: Any = data
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _number(value: Any) -> int | float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    return None


def _rounded(value: Any, digits: int = 2) -> float | None:
    number = _number(value)
    return round(float(number), digits) if number is not None else None


# ---------------------------------------------------------------------
# ACP conversation timeline (#6078)
# ---------------------------------------------------------------------


def _acp_db_path() -> Path:
    """Return the configured fleet-comms database without creating it."""
    repo_root = Path(__file__).resolve().parents[2]
    return default_plane_root(repo_root=repo_root) / "comms.sqlite3"


def _open_acp_db_readonly() -> sqlite3.Connection | None:
    """Open fleet-comms storage read-only, returning ``None`` when unavailable."""
    db_path = _acp_db_path()
    if not db_path.is_file():
        return None
    try:
        connection = sqlite3.connect(f"{db_path.resolve().as_uri()}?mode=ro", uri=True)
    except (OSError, sqlite3.Error, ValueError):
        return None
    connection.row_factory = sqlite3.Row
    return connection


def _acp_table_exists(connection: sqlite3.Connection, table: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)
    ).fetchone()
    return row is not None


def _acp_text(value: Any, *, allowed: frozenset[str] | None = None) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if not normalized or (allowed is not None and normalized not in allowed):
        return None
    return normalized


def _acp_event_type(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower().replace("-", "_")
    normalized = _ACP_EVENT_TYPE_ALIASES.get(normalized, normalized.upper())
    return normalized if normalized in _ACP_EVENT_TYPES else None


def _acp_outcome(value: Any, state: str) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower()
    if normalized in _ACP_OUTCOMES:
        return normalized
    if normalized == "ok":
        return "succeeded"
    if normalized in {"error", "timeout", "rate_limited", "orphan"}:
        return "partial" if state in {"PARTIAL", "PARTIAL_COMPLETE"} else "failed"
    return None


def _acp_int(value: Any, *, minimum: int = 0) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        return None
    return value


def _acp_identifier(value: Any) -> str | None:
    """Accept only compact opaque IDs; malformed IDs are never reflected."""
    if not isinstance(value, str) or not 1 <= len(value) <= 128:
        return None
    if not all(character.isascii() and (character.isalnum() or character in "-_") for character in value):
        return None
    return value


def _acp_timestamp(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    parsed = _parse_iso_datetime(value)
    return _isoformat_z(parsed) if parsed else None


def _acp_classification(state: str | None) -> str:
    if state == "COMPLETE":
        return "complete"
    if state in {"PARTIAL", "PARTIAL_COMPLETE"}:
        return "partial"
    if state in {"FAILED", "CANCELLED"}:
        return "failed"
    if state == "CREATED":
        return "queued"
    return "running"


def _acp_synthesis_state(events: list[dict[str, Any]], current_state: str | None) -> str:
    states = {event["state"] for event in events if event.get("state")}
    event_types = {event["event_type"] for event in events if event.get("event_type")}
    if current_state == "FAILED":
        return "failed"
    if current_state in {"PARTIAL", "PARTIAL_COMPLETE", "CANCELLED"}:
        return "partial"
    if current_state == "COMPLETE" and (
        "SYNTHESIS" in states
        or "SYNTHESIS_COMPLETE" in event_types
        or "SYNTHESIS_TERMINAL" in event_types
    ):
        return "complete"
    if current_state == "SYNTHESIS" or "SYNTHESIS" in states:
        return "running"
    return "not_started"


def _acp_termination(events: list[dict[str, Any]], current_state: str | None) -> str | None:
    for event in reversed(events):
        outcome = event.get("outcome")
        if outcome in _ACP_TERMINATIONS:
            return outcome
        event_type = event.get("event_type")
        if event_type == "DUPLICATE_SUPPRESSED":
            return "duplicate_suppressed"
        if event_type == "BUDGET_EXHAUSTED":
            return "budget_exhausted"
        if event_type == "DEADLINE_EXCEEDED":
            return "deadline_exceeded"
    if current_state == "CANCELLED":
        return "cancelled"
    if current_state == "FAILED":
        return "failed"
    return None


def _sanitize_acp_event(row: sqlite3.Row) -> dict[str, Any] | None:
    sequence = _acp_int(row["sequence"])
    state = _acp_text(row["state"], allowed=_ACP_STATES)
    event_type = _acp_event_type(row["event_type"])
    created_at = _acp_timestamp(row["created_at"])
    if sequence is None or state is None or event_type is None or created_at is None:
        return None
    event: dict[str, Any] = {
        "sequence": sequence,
        "event_type": event_type,
        "state": state,
        "created_at": created_at,
    }
    sender = _acp_text(row["sender"], allowed=frozenset(_ACP_PARTICIPANTS))
    recipient = _acp_text(row["recipient"], allowed=frozenset(_ACP_PARTICIPANTS))
    if sender:
        event["sender"] = sender
    if recipient:
        event["recipient"] = recipient
    round_number = _acp_int(row["round"], minimum=1)
    if round_number is not None:
        event["round"] = round_number
    outcome = _acp_outcome(row["outcome"], state)
    if outcome:
        event["outcome"] = outcome
    duration_ms = _acp_int(row["duration_ms"])
    if duration_ms is not None:
        event["duration_ms"] = duration_ms
    token_count = _acp_int(row["token_count"])
    if token_count is not None:
        event["token_count"] = token_count
    return event


def _acp_events(connection: sqlite3.Connection, conversation_id: str) -> list[dict[str, Any]]:
    try:
        rows = connection.execute(
            """
            SELECT sequence, event_type, state, sender, recipient, round, outcome,
                   duration_ms, token_count, created_at
            FROM acp_conversation_events
            WHERE conversation_id = ?
            ORDER BY sequence ASC
            LIMIT 500
            """,
            (conversation_id,),
        ).fetchall()
    except sqlite3.Error:
        return []
    events = [event for row in rows if (event := _sanitize_acp_event(row)) is not None]
    return events


def _acp_rounds_completed(events: list[dict[str, Any]]) -> int:
    lanes_by_round: dict[int, set[str]] = defaultdict(set)
    for event in events:
        if event.get("event_type") not in _ACP_MESSAGE_EVENTS:
            continue
        round_number = event.get("round")
        if not isinstance(round_number, int):
            continue
        for lane in (event.get("sender"), event.get("recipient")):
            if lane in {"codex", "grok"}:
                lanes_by_round[round_number].add(lane)
    completed = 0
    for round_number in sorted(lanes_by_round):
        if round_number != completed + 1 or lanes_by_round[round_number] != {"codex", "grok"}:
            break
        completed = round_number
    return completed


def _acp_summary(row: sqlite3.Row, events: list[dict[str, Any]]) -> dict[str, Any] | None:
    conversation_id = _acp_identifier(row["conversation_id"])
    created_at = _acp_timestamp(row["created_at"])
    rounds_requested = _acp_int(row["rounds_requested"], minimum=1)
    if conversation_id is None or created_at is None or rounds_requested is None:
        return None
    current_state = events[-1]["state"] if events else "CREATED"
    updated_at = events[-1]["created_at"] if events else created_at
    duration_ms = sum(event.get("duration_ms", 0) for event in events)
    total_tokens = sum(event.get("token_count", 0) for event in events)
    termination = _acp_termination(events, current_state)
    return {
        "conversation_id": conversation_id,
        "current_state": current_state,
        "classification": _acp_classification(current_state),
        "participants": list(_ACP_PARTICIPANTS),
        "rounds_requested": rounds_requested,
        "rounds_completed": _acp_rounds_completed(events),
        "created_at": created_at,
        "updated_at": updated_at,
        "total_duration_ms": duration_ms,
        "total_tokens": total_tokens,
        "synthesis_state": _acp_synthesis_state(events, current_state),
        "duplicate_suppressed": termination == "duplicate_suppressed",
        "termination_reason": termination,
    }


def _acp_available_connection() -> sqlite3.Connection | None:
    connection = _open_acp_db_readonly()
    if connection is None:
        return None
    try:
        if not (_acp_table_exists(connection, "acp_conversations") and _acp_table_exists(connection, "acp_conversation_events")):
            connection.close()
            return None
    except sqlite3.Error:
        connection.close()
        return None
    return connection


def list_acp_conversations(*, limit: int = 50) -> dict[str, Any]:
    """Return sanitized active-conversation summaries without touching storage."""
    connection = _acp_available_connection()
    if connection is None:
        return {"availability": "unavailable", "conversations": []}
    try:
        rows = connection.execute(
            """
            SELECT conversation_id, rounds_requested, created_at
            FROM acp_conversations
            ORDER BY created_at DESC, conversation_id ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        conversations = [
            summary
            for row in rows
            if (summary := _acp_summary(row, _acp_events(connection, row["conversation_id"]))) is not None
        ]
    except sqlite3.Error:
        return {"availability": "unavailable", "conversations": []}
    finally:
        connection.close()
    return {"availability": "available" if conversations else "empty", "conversations": conversations}


def get_acp_conversation(conversation_id: str) -> dict[str, Any] | None:
    """Return one sanitized conversation timeline, or ``None`` without details."""
    safe_id = _acp_identifier(conversation_id)
    if safe_id is None:
        return None
    connection = _acp_available_connection()
    if connection is None:
        return None
    try:
        row = connection.execute(
            "SELECT conversation_id, rounds_requested, created_at FROM acp_conversations WHERE conversation_id = ?",
            (safe_id,),
        ).fetchone()
        if row is None:
            return None
        events = _acp_events(connection, safe_id)
        summary = _acp_summary(row, events)
        return {**summary, "events": events} if summary is not None else None
    except sqlite3.Error:
        return None
    finally:
        connection.close()


@router.get("/agents")
async def runtime_agents():
    agents = await asyncio.to_thread(list_runtime_agents)
    return {"agents": agents}


@router.get("/usage")
async def runtime_usage(
    agent: str | None = Query(None),
    entrypoint: str | None = Query(None),
    days: int = Query(7, ge=1, le=30),
):
    return await asyncio.to_thread(summarize_runtime_usage, days=days, agent=agent, entrypoint=entrypoint)


@router.get("/acpx")
async def runtime_acpx(days: int = Query(7, ge=1, le=30)):
    """Read-only ACPX shadow posture and aggregate evidence; never probe."""
    return await asyncio.to_thread(acpx_shadow_overview, days=days)


@router.get("/acp/conversations")
async def runtime_acp_conversations(limit: int = Query(50, ge=1, le=100)):
    """Read only, allowlisted summaries of persisted ACP conversations."""
    return await asyncio.to_thread(list_acp_conversations, limit=limit)


@router.get("/acp/conversations/{conversation_id}")
async def runtime_acp_conversation(conversation_id: str):
    """Read one allowlisted ACP conversation timeline without message content."""
    conversation = await asyncio.to_thread(get_acp_conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.get("/headroom")
async def runtime_headroom(
    agent: str | None = Query(None),
    model: str | None = Query(None),
):
    if not agent or not model:
        raise HTTPException(status_code=400, detail="Both 'agent' and 'model' query params are required")
    ok, reason = await asyncio.to_thread(has_headroom, agent, model)
    return {"agent": agent, "model": model, "has_headroom": ok, "reason": reason}


@router.get("/recent")
async def runtime_recent(limit: int = Query(50, ge=1, le=500)):
    return await asyncio.to_thread(recent_runtime_records, limit=limit)


@router.get("/transport-health")
async def runtime_transport_health():
    """Return the cached Codex fresh-process probe; never launch a model."""
    return await asyncio.to_thread(
        current_transport_health,
        receipt_path=CODEX_TRANSPORT_RECEIPT_PATH,
        config_path=CODEX_TRANSPORT_CONFIG_PATH,
    )


# ---------------------------------------------------------------------
# Auth mode snapshot (#1313 / Codex-7)
# ---------------------------------------------------------------------


@router.get("/auth")
async def runtime_auth():
    """Per-agent auth mode snapshot.

    Tells an operator — without grepping env vars — whether Gemini is
    running in ``subscription`` (logged-in OAuth / Google account) or
    ``api`` (GEMINI_API_KEY-based) or ``auto`` mode, and whether a
    key is currently inherited from the environment.

    Why it matters (Codex-7 / #1313): "would have saved us time
    immediately" — the session lost hours debugging which auth path
    Gemini actually used. This endpoint makes it deterministic.

    Shape::
        {
          "gemini": {
            "auth_mode":          "subscription" | "api",
            "auth_mode_raw_valid": true,
            "auth_mode_raw_length": 12,
            "api_key_present":    false,
            "google_key_present": false,
            "google_oauth_cred":  true,   # ~/.gemini/oauth_creds.json readable
          },
          "claude":  {"api_key_present": true,  "source": "ANTHROPIC_API_KEY"},
          "codex":   {"api_key_present": true,  "source": "OPENAI_API_KEY"},
          "checked_at": "2026-04-17T..."
        }

    All information is derived from env + filesystem — no subprocess,
    no network call. Cheap and safe to poll.
    """
    env = os.environ
    home = Path.home()

    # Sanitize GEMINI_AUTH_MODE rather than echo it raw. Reviewer
    # Codex BLOCKER on #1312 pre-merge: this endpoint's contract says
    # "never echoes key values". If an operator accidentally pastes a
    # key fragment into GEMINI_AUTH_MODE (typo in their shell
    # profile), echoing the raw value leaks it. We still surface
    # WHETHER the raw value was recognized via a ``raw_valid`` flag +
    # its LENGTH — enough to debug an invalid config without exposing
    # content.
    _AUTH_MODE_VALID = {"auto", "subscription", "api"}
    raw_mode = (env.get("GEMINI_AUTH_MODE") or "").strip()
    raw_valid = raw_mode.lower() in _AUTH_MODE_VALID
    gemini = {
        "auth_mode": resolve_gemini_auth_mode(),
        "auth_mode_raw_valid": raw_valid,
        "auth_mode_raw_length": len(raw_mode),
        "api_key_present": bool(env.get("GEMINI_API_KEY")),
        "google_key_present": bool(env.get("GOOGLE_API_KEY")),
        "google_oauth_cred": has_gemini_oauth_credentials(home),
    }

    # Claude is subscription-only via the CLI; we still surface whether a
    # key happens to be present in case someone's running the SDK too.
    claude = {
        "api_key_present": bool(env.get("ANTHROPIC_API_KEY")),
        "source": (
            "ANTHROPIC_API_KEY" if env.get("ANTHROPIC_API_KEY") else None
        ),
    }

    # Codex uses its own key env var. Same logic.
    codex = {
        "api_key_present": bool(env.get("OPENAI_API_KEY") or env.get("CODEX_API_KEY")),
        "source": (
            "OPENAI_API_KEY" if env.get("OPENAI_API_KEY")
            else "CODEX_API_KEY" if env.get("CODEX_API_KEY")
            else None
        ),
    }

    return {
        "gemini": gemini,
        "claude": claude,
        "codex": codex,
        "checked_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }
