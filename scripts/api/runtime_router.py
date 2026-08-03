"""Runtime observability API router."""

from __future__ import annotations

import asyncio
import importlib
import inspect
import ipaddress
import json
import os
import re
import sqlite3
import sys
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from .config import BATCH_STATE_DIR, PROJECT_ROOT

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent_runtime.adapters.acpx import (
    ACPX_CLI_COMPATIBILITY_CONTRACT,
    ACPX_SUPPORTED_PARTICIPANTS,
    AGY_CLI_COMPATIBILITY_CONTRACT,
    GROK_CLI_COMPATIBILITY_CONTRACT,
    GROK_SHADOW_EFFORT,
    GROK_SHADOW_MODEL,
    HERMES_CLI_COMPATIBILITY_CONTRACT,
    OPENCODE_CLI_COMPATIBILITY_CONTRACT,
    AcpxAdapter,
    AcpxGrokShadowAdapter,
)
from agent_runtime.adapters.acpx import (
    TRANSPORT_ENV as ACPX_TRANSPORT_ENV,
)
from agent_runtime.adapters.gemini import has_gemini_oauth_credentials, resolve_gemini_auth_mode
from agent_runtime.usage import has_headroom

from scripts.fleet_comms.message_plane import default_plane_root, read_plane_status
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
_RUNTIME_ATTRIBUTION_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,99}$")
_RUNTIME_ATTRIBUTION_SOURCES = frozenset({"explicit", "session_env", "unknown"})
_RUNTIME_FAILURE_CODES = frozenset(
    {
        "adapter_refused",
        "protocol_output_limit",
        "provider_unavailable",
        "rate_limited",
        "result_invalid",
        "timeout",
        "transport_error",
        "unknown",
    }
)
_ACP_LEGACY_PARTICIPANTS = ("codex", "grok")
_ACP_ENABLED_PARTICIPANTS = frozenset(ACPX_SUPPORTED_PARTICIPANTS)
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
_ACP_MESSAGE_EVENTS = frozenset({
    "PARTICIPANT_MESSAGE",
    "PARTICIPANT_COMPLETE",
    "CROSS_EXCHANGE_MESSAGE",
    "CROSS_EXCHANGE_COMPLETE",
    "CALL_TERMINAL",
    "SYNTHESIS_TERMINAL",
})
_ACP_TRANSCRIPT_KINDS = frozenset({"request", "reply", "synthesis"})
_ACP_TRANSCRIPT_MAX_MESSAGES = 32
_ACP_TRANSCRIPT_MAX_BODY_BYTES = 256 * 1024
_ACP_TRANSCRIPT_MAX_RESPONSE_BYTES = 512 * 1024
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
        "compatibility": {
            "acpx": {
                "contract": ACPX_CLI_COMPATIBILITY_CONTRACT,
                "validation": "before_spawn",
                "version_policy": "telemetry_only",
            },
            "agy_cli": {
                "contract": AGY_CLI_COMPATIBILITY_CONTRACT,
                "validation": "before_spawn",
                "version_policy": "telemetry_only",
            },
            "grok_cli": {
                "contract": GROK_CLI_COMPATIBILITY_CONTRACT,
                "validation": "before_spawn",
                "version_policy": "telemetry_only",
            },
            "hermes_cli": {
                "contract": HERMES_CLI_COMPATIBILITY_CONTRACT,
                "validation": "before_spawn",
                "version_policy": "telemetry_only",
            },
            "opencode_cli": {
                "contract": OPENCODE_CLI_COMPATIBILITY_CONTRACT,
                "validation": "before_spawn",
                "version_policy": "telemetry_only",
            },
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
        initiator = record.get("initiator")
        if not isinstance(initiator, str) or not _RUNTIME_ATTRIBUTION_ID.fullmatch(initiator):
            initiator = "unknown"
        source_provenance = record.get("attribution_source")
        if source_provenance not in _RUNTIME_ATTRIBUTION_SOURCES or initiator == "unknown":
            source_provenance = "unknown"
        source_task_id = record.get("attribution_task_id")
        if not isinstance(source_task_id, str) or not _RUNTIME_ATTRIBUTION_ID.fullmatch(source_task_id):
            source_task_id = None
        failure_code = record.get("failure_code")
        if failure_code not in _RUNTIME_FAILURE_CODES:
            outcome = record.get("outcome")
            if outcome in {"timeout", "hard_timeout", "stalled"}:
                failure_code = "timeout"
            elif outcome == "rate_limited":
                failure_code = "rate_limited"
            else:
                failure_code = "unknown" if outcome not in {"ok", None} else None
        summaries.append({
            "ts": _isoformat_z(ts) if ts else record.get("ts"),
            "agent": record.get("agent"),
            "entrypoint": record.get("entrypoint"),
            "via": record.get("entrypoint"),
            "source": initiator,
            "source_provenance": source_provenance,
            "source_task_id": source_task_id,
            "model": record.get("model"),
            "outcome": record.get("outcome"),
            "failure_code": failure_code,
            "duration_s": record.get("duration_s"),
        })
    summaries.sort(key=lambda item: _parse_iso_datetime(item.get("ts")) or datetime.min.replace(tzinfo=UTC), reverse=True)
    return {"records": summaries[:record_limit]}


def _routing_plane_status() -> dict[str, Any]:
    """Expose the actual plane posture without inferring authority from rows."""
    try:
        raw = read_plane_status(repo_root=Path(PROJECT_ROOT), recent_limit=0)
    except Exception:
        raw = {"mode": "unavailable", "enabled": False}
    mode = str(raw.get("mode") or "unavailable")
    authority_active = mode == "authority"
    return {
        "mode": mode,
        "enabled": bool(raw.get("enabled")),
        "authority": "fleet_comms_authoritative" if authority_active else "file_handoffs_authoritative",
        "cutover": "authority_active" if authority_active else "pre_flip_operator_gated",
    }


def _routing_value(record: dict[str, Any], *keys: str) -> Any:
    """Read an optional compatible ledger field without fabricating values."""
    for key in keys:
        value = record.get(key)
        if value is not None:
            return value
    return None


def _routing_first(*values: Any) -> Any:
    """Return the first present field while preserving meaningful zero values."""
    return next((value for value in values if value is not None), None)


def _routing_trace_value(trace: dict[str, Any], *keys: str) -> Any:
    """Read a trace field across policy-version-compatible names."""
    return _routing_first(*(trace.get(key) for key in keys))


def _routing_duration_s(record: dict[str, Any]) -> float | None:
    direct = _routing_value(record, "duration_s", "duration_seconds")
    if isinstance(direct, (int, float)) and not isinstance(direct, bool):
        return float(direct)
    lifecycle = record.get("lifecycle") if isinstance(record.get("lifecycle"), dict) else {}
    started = _parse_iso_datetime(_routing_first(_routing_value(record, "started_at"), lifecycle.get("started_at")))
    settled = _parse_iso_datetime(
        _routing_first(_routing_value(record, "settled_at", "terminal_at"), lifecycle.get("settled_at"))
    )
    if started is None or settled is None:
        return None
    return max(0.0, round((settled - started).total_seconds(), 3))


def _routing_assignment_item(record: dict[str, Any]) -> dict[str, Any]:
    """Serialize an allowlisted, body-free routing decision for the Runtime UI."""
    requested = record.get("requested") if isinstance(record.get("requested"), dict) else {}
    resolved = record.get("resolved") if isinstance(record.get("resolved"), dict) else {}
    quota_detail = record.get("quota") if isinstance(record.get("quota"), dict) else {}
    quota_snapshot = _routing_first(
        quota_detail.get("snapshot") if isinstance(quota_detail.get("snapshot"), dict) else None,
        _routing_value(record, "quota_snapshot") if isinstance(_routing_value(record, "quota_snapshot"), dict) else None,
    ) or {}
    lifecycle = record.get("lifecycle") if isinstance(record.get("lifecycle"), dict) else {}
    evidence = record.get("evidence") if isinstance(record.get("evidence"), dict) else {}
    replay = record.get("replay") if isinstance(record.get("replay"), dict) else {}
    retry = record.get("retry") if isinstance(record.get("retry"), dict) else {}
    selection_trace = _routing_first(_routing_value(record, "selection_trace", "trace"), resolved.get("trace"))
    trace = selection_trace if isinstance(selection_trace, dict) else {}
    automatic = _routing_value(record, "automatic")
    if not isinstance(automatic, bool):
        automatic = _routing_value(record, "route_mode") == "auto" or requested.get("route_mode") == "auto"
    return {
        "decision_id": _routing_value(record, "decision_id"),
        "decision_event": _routing_value(record, "event_type"),
        "decision_state": _routing_value(record, "state"),
        "source_authority_id": _routing_value(record, "source_authority_id", "reservation_id"),
        "authority_key": _routing_value(record, "authority_key"),
        "timestamp": _routing_value(record, "created_at", "timestamp"),
        "initiator": _routing_first(_routing_value(record, "initiator"), requested.get("initiator")),
        "author_model": _routing_first(_routing_value(record, "author_model"), requested.get("author_model")),
        "author_family": _routing_first(_routing_value(record, "author_family"), requested.get("author_family")),
        "requested_role": _routing_first(_routing_value(record, "requested_role"), requested.get("role")),
        "requested_profile": _routing_first(_routing_value(record, "requested_profile"), requested.get("profile")),
        "requested_risk": _routing_first(_routing_value(record, "requested_risk"), requested.get("risk")),
        "requested_route": _routing_first(_routing_value(record, "requested_route"), requested.get("route")),
        "automatic": automatic,
        "resolved_candidate": _routing_first(_routing_value(record, "resolved_candidate", "candidate"), resolved.get("candidate")),
        "resolved_route": _routing_first(_routing_value(record, "resolved_route", "route"), resolved.get("route")),
        "resolved_model": _routing_first(_routing_value(record, "resolved_model", "model"), resolved.get("model")),
        "resolved_family": _routing_first(_routing_value(record, "resolved_family", "family"), resolved.get("family")),
        "quota_bucket": _routing_first(_routing_value(record, "quota_bucket"), quota_detail.get("bucket")),
        "policy_version": _routing_first(_routing_value(record, "policy_version"), resolved.get("policy_version")),
        "selection_reason": _routing_first(_routing_value(record, "selection_reason", "reason"), evidence.get("reason")),
        "selection_trace": selection_trace,
        "selection_reasoning": {
            # The order is deliberate: a candidate must first be eligible and
            # task-suitable before quota, opportunity cost, capacity, or
            # failure posture can distinguish otherwise suitable routes.
            "hard_eligibility": _routing_trace_value(
                trace,
                "hard_eligibility", "eligibility", "capability_gates", "gates",
            ),
            "task_fit_quality": _routing_trace_value(
                trace,
                "task_fit", "capability_fit", "strength", "quality_rank", "suitability",
            ),
            "tie_breakers": _routing_trace_value(
                trace,
                "tie_breakers", "quota_cost_capacity", "quota", "opportunity_cost", "failure_posture",
            ),
            "cheaper_or_idle_not_selected": _routing_trace_value(
                trace,
                "cheaper_or_idle_not_selected", "rejected_alternatives", "not_selected",
            ),
        },
        "quota_source": _routing_first(_routing_value(record, "quota_source"), quota_snapshot.get("source")),
        "quota_freshness": _routing_first(_routing_value(record, "quota_freshness", "quota_fresh_at"), quota_detail.get("fresh_at"), quota_snapshot.get("freshness")),
        "quota_headroom": _routing_first(_routing_value(record, "quota_headroom"), quota_snapshot.get("headroom")),
        "estimated_input_bytes": _routing_first(_routing_value(record, "estimated_input_bytes"), requested.get("estimated_input_bytes")),
        "actual_input_bytes": _routing_value(record, "actual_input_bytes"),
        "actual_output_bytes": _routing_value(record, "actual_output_bytes"),
        "actual_work_bytes": _routing_first(_routing_value(record, "actual_work_bytes"), lifecycle.get("actual_bytes")),
        "actual_tokens": _routing_first(_routing_value(record, "actual_tokens"), lifecycle.get("actual_tokens")),
        "reservation_state": _routing_first(_routing_value(record, "reservation_state", "status"), lifecycle.get("status")),
        "terminal_status": _routing_first(_routing_value(record, "terminal_status", "status"), lifecycle.get("status")),
        "created_at": _routing_first(_routing_value(record, "created_at"), lifecycle.get("created_at")),
        "expires_at": _routing_first(_routing_value(record, "expires_at"), lifecycle.get("expires_at")),
        "started_at": _routing_first(_routing_value(record, "started_at"), lifecycle.get("started_at")),
        "settled_at": _routing_first(_routing_value(record, "settled_at", "terminal_at"), lifecycle.get("settled_at")),
        "duration_s": _routing_duration_s(record),
        "failure_classification": _routing_first(_routing_value(record, "failure_classification"), lifecycle.get("failure_classification")),
        "retry_chain": _routing_first(_routing_value(record, "retry_chain", "retry"), retry),
        "failover_chain": _routing_value(record, "failover_chain", "failover"),
        "replay_status": _routing_first(_routing_value(record, "replay_status", "replay"), replay),
        "cache_status": _routing_value(record, "cache_status", "cache"),
    }


def list_routing_assignments(*, limit: int = 100) -> dict[str, Any]:
    """Read persisted routing decisions through the optional authority ledger.

    The routing-reservation store is owned by Fleet Comms. Runtime only calls
    its optional read-only projection and reports a distinct unavailable state
    until that authority is installed; an absent table is never treated as an
    empty history.
    """
    record_limit = min(max(1, int(limit)), 100)
    plane = _routing_plane_status()
    try:
        ledger = importlib.import_module("scripts.fleet_comms.routing_reservations")
        reader = ledger.list_routing_decisions
        rows = reader(root=default_plane_root(repo_root=Path(PROJECT_ROOT)), limit=record_limit)
    except (ImportError, AttributeError):
        return {
            "availability": "unavailable",
            "reason": "routing_decision_reader_unavailable",
            "plane": plane,
            "assignments": [],
        }
    except (OSError, sqlite3.Error, TypeError, ValueError):
        return {
            "availability": "unavailable",
            "reason": "routing_decision_reader_failed",
            "plane": plane,
            "assignments": [],
        }
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        return {
            "availability": "malformed",
            "reason": "routing_decision_reader_malformed",
            "plane": plane,
            "assignments": [],
        }
    assignments = [_routing_assignment_item(row) for row in rows[:record_limit]]
    assignments.sort(
        key=lambda item: _parse_iso_datetime(item.get("timestamp")) or datetime.min.replace(tzinfo=UTC),
        reverse=True,
    )
    return {
        "availability": "available" if assignments else "empty",
        "plane": plane,
        "assignments": assignments,
    }


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


def _acp_outcome(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower()
    if normalized in _ACP_OUTCOMES:
        return normalized
    if normalized == "ok":
        return "succeeded"
    if normalized in {"busy", "orphan"}:
        return "partial"
    if normalized in {"error", "timeout", "rate_limited"}:
        return "failed"
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


def _acp_discussion_participants(value: Any) -> tuple[str, str]:
    """Return a privacy-safe enabled pair, tolerating legacy stored shapes."""
    try:
        decoded = json.loads(value) if isinstance(value, str) else value
    except (TypeError, ValueError, json.JSONDecodeError):
        decoded = None
    enabled: list[str] = []
    if isinstance(decoded, list):
        for item in decoded:
            if item in _ACP_ENABLED_PARTICIPANTS and item not in enabled:
                enabled.append(item)
    if len(enabled) == 2:
        return enabled[0], enabled[1]
    return _ACP_LEGACY_PARTICIPANTS


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
    if state == "CANCELLED":
        return "cancelled"
    if state == "FAILED":
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
    terminal_events = {
        "DUPLICATE_SUPPRESSED": "duplicate_suppressed",
        "BUDGET_EXHAUSTED": "budget_exhausted",
        "DEADLINE_EXCEEDED": "deadline_exceeded",
    }
    for event in reversed(events):
        reason = terminal_events.get(event.get("event_type"))
        if reason:
            return reason
    if current_state == "CANCELLED":
        return "cancelled"
    if current_state == "FAILED":
        return "failed"
    return None


def _sanitize_acp_event(
    row: sqlite3.Row, *, allowed_lanes: frozenset[str]
) -> dict[str, Any] | None:
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
    sender = _acp_text(row["sender"], allowed=allowed_lanes)
    recipient = _acp_text(row["recipient"], allowed=allowed_lanes)
    if sender:
        event["sender"] = sender
    if recipient:
        event["recipient"] = recipient
    round_number = _acp_int(row["round"], minimum=1)
    if round_number is not None:
        event["round"] = round_number
    outcome = _acp_outcome(row["outcome"])
    if outcome:
        event["outcome"] = outcome
    duration_ms = _acp_int(row["duration_ms"])
    if duration_ms is not None:
        event["duration_ms"] = duration_ms
    token_count = _acp_int(row["token_count"])
    if token_count is not None:
        event["token_count"] = token_count
    return event


def _acp_events(
    connection: sqlite3.Connection,
    conversation_id: str,
    participants: tuple[str, str],
) -> list[dict[str, Any]]:
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
    allowed_lanes = frozenset({"root", "codex", *participants})
    events = [
        event
        for row in rows
        if (event := _sanitize_acp_event(row, allowed_lanes=allowed_lanes)) is not None
    ]
    return events


def _acp_rounds_completed(
    events: list[dict[str, Any]], participants: tuple[str, str]
) -> int:
    lanes_by_round: dict[int, set[str]] = defaultdict(set)
    for event in events:
        if event.get("event_type") not in _ACP_MESSAGE_EVENTS:
            continue
        round_number = event.get("round")
        if not isinstance(round_number, int):
            continue
        for lane in (event.get("sender"), event.get("recipient")):
            if lane in participants:
                lanes_by_round[round_number].add(lane)
    completed = 0
    for round_number in sorted(lanes_by_round):
        if round_number != completed + 1 or lanes_by_round[round_number] != set(participants):
            break
        completed = round_number
    return completed


def _acp_summary(
    row: sqlite3.Row,
    events: list[dict[str, Any]],
    participants: tuple[str, str],
) -> dict[str, Any] | None:
    conversation_id = _acp_identifier(row["conversation_id"])
    created_at = _acp_timestamp(row["created_at"])
    rounds_requested = _acp_int(row["rounds_requested"], minimum=1)
    if conversation_id is None or created_at is None or rounds_requested is None:
        return None
    current_state = events[-1]["state"] if events else "CREATED"
    deadline_at = _acp_timestamp(row["deadline_at"])
    terminal = current_state in {"COMPLETE", "PARTIAL_COMPLETE", "FAILED", "CANCELLED"}
    deadline = _parse_iso_datetime(deadline_at)
    expired = not terminal and (deadline is None or datetime.now(UTC) > deadline)
    stale_or_unhealthy = expired or current_state in {
        "PARTIAL", "PARTIAL_COMPLETE", "FAILED", "CANCELLED",
    }
    updated_at = events[-1]["created_at"] if events else created_at
    terminal_event = next(
        (
            event
            for event in reversed(events)
            if event.get("event_type") == "STATE"
            and event.get("state") in {"COMPLETE", "PARTIAL_COMPLETE", "FAILED", "CANCELLED"}
        ),
        None,
    )
    terminal_duration = terminal_event.get("duration_ms") if terminal_event else None
    if isinstance(terminal_duration, int):
        duration_ms = terminal_duration
    elif terminal_event:
        start = _parse_iso_datetime(created_at)
        finish = _parse_iso_datetime(terminal_event.get("created_at"))
        duration_ms = max(0, round((finish - start).total_seconds() * 1000)) if start and finish else 0
    else:
        duration_ms = sum(event.get("duration_ms", 0) for event in events)
    terminal_tokens = terminal_event.get("token_count") if terminal_event else None
    total_tokens = (
        terminal_tokens
        if isinstance(terminal_tokens, int)
        else sum(event.get("token_count", 0) for event in events)
    )
    termination = _acp_termination(events, current_state)
    return {
        "conversation_id": conversation_id,
        "current_state": current_state,
        "classification": _acp_classification(current_state),
        "participants": list(participants),
        "rounds_requested": rounds_requested,
        "rounds_completed": _acp_rounds_completed(events, participants),
        "created_at": created_at,
        "deadline_at": deadline_at,
        "expired": expired,
        "stale_or_unhealthy": stale_or_unhealthy,
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
            SELECT conversation_id, rounds_requested, participants_json, created_at, deadline_at
            FROM acp_conversations
            ORDER BY created_at DESC, conversation_id ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        conversations = []
        for row in rows:
            participants = _acp_discussion_participants(row["participants_json"])
            events = _acp_events(connection, row["conversation_id"], participants)
            summary = _acp_summary(row, events, participants)
            if summary is not None:
                conversations.append(summary)
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
            "SELECT conversation_id, rounds_requested, participants_json, created_at, deadline_at FROM acp_conversations WHERE conversation_id = ?",
            (safe_id,),
        ).fetchone()
        if row is None:
            return None
        participants = _acp_discussion_participants(row["participants_json"])
        events = _acp_events(connection, safe_id, participants)
        summary = _acp_summary(row, events, participants)
        return {**summary, "events": events} if summary is not None else None
    except sqlite3.Error:
        return None
    finally:
        connection.close()


def _acp_transcript_client_is_loopback(request: Request) -> bool:
    """Accept only direct loopback peers addressed through a loopback host.

    ``request.client`` is supplied by the accepted connection, rather than a
    forwarding header. Requiring a loopback URL host as well closes the usual
    DNS-rebinding path from a non-local browser origin.
    """
    client = request.client
    client_host = client.host if client else None
    if not isinstance(client_host, str):
        return False
    try:
        client_address = ipaddress.ip_address(client_host)
    except ValueError:
        return False
    client_mapped = getattr(client_address, "ipv4_mapped", None)
    if not client_address.is_loopback and not (client_mapped and client_mapped.is_loopback):
        return False

    url_host = request.url.hostname
    if url_host == "localhost":
        return True
    if not isinstance(url_host, str):
        return False
    try:
        url_address = ipaddress.ip_address(url_host)
    except ValueError:
        return False
    url_mapped = getattr(url_address, "ipv4_mapped", None)
    return url_address.is_loopback or bool(url_mapped and url_mapped.is_loopback)


def _acp_transcript_body(value: Any, *, remaining_bytes: int) -> str | None:
    """Return a bounded JSON-safe body or reject the whole malformed row."""
    if not isinstance(value, str):
        return None
    try:
        encoded = value.encode("utf-8")
        serialized = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    except UnicodeError:
        return None
    if len(encoded) > _ACP_TRANSCRIPT_MAX_BODY_BYTES or len(serialized) > remaining_bytes:
        return None
    return value


def _acp_transcript_entries(
    connection: sqlite3.Connection,
    conversation_id: str,
    participants: tuple[str, str],
) -> list[dict[str, Any]] | None:
    """Read a bounded, allowlisted ACP transcript without exposing store IDs."""
    try:
        rows = connection.execute(
            """
            SELECT messages.kind, messages.sender, messages.recipient,
                   messages.body_inline, messages.created_at, event_round.round
            FROM comms_messages AS messages
            JOIN (
                SELECT message_id, MIN(sequence) AS message_sequence,
                       CASE
                           WHEN MIN(round) = MAX(round) AND MIN(round) >= 1
                           THEN MIN(round)
                       END AS round
                FROM acp_conversation_events
                WHERE conversation_id = ? AND message_id IS NOT NULL
                GROUP BY message_id
            ) AS event_round ON event_round.message_id = messages.message_id
            WHERE messages.conversation_id = ?
            ORDER BY event_round.message_sequence ASC
            LIMIT ?
            """,
            (conversation_id, conversation_id, _ACP_TRANSCRIPT_MAX_MESSAGES + 1),
        ).fetchall()
    except sqlite3.Error:
        return None
    if len(rows) > _ACP_TRANSCRIPT_MAX_MESSAGES:
        return None

    entries: list[dict[str, Any]] = []
    remaining_bytes = _ACP_TRANSCRIPT_MAX_RESPONSE_BYTES
    for row in rows:
        kind = _acp_text(row["kind"], allowed=_ACP_TRANSCRIPT_KINDS)
        allowed_lanes = frozenset({"root", "codex", *participants})
        sender = _acp_text(row["sender"], allowed=allowed_lanes)
        recipient = _acp_text(row["recipient"], allowed=allowed_lanes)
        created_at = _acp_timestamp(row["created_at"])
        body = _acp_transcript_body(row["body_inline"], remaining_bytes=remaining_bytes)
        if None in (kind, sender, recipient, created_at, body):
            continue
        entry: dict[str, Any] = {
            "ordinal": len(entries) + 1,
            "kind": kind,
            "sender": sender,
            "recipient": recipient,
            "created_at": created_at,
            "body": body,
        }
        round_number = _acp_int(row["round"], minimum=1)
        if round_number is not None:
            entry["round"] = round_number
        entries.append(entry)
        remaining_bytes -= len(
            json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        )
    return entries


def get_acp_conversation_transcript(conversation_id: str) -> dict[str, Any] | None:
    """Return a single bounded ACP transcript, or ``None`` without diagnostics."""
    safe_id = _acp_identifier(conversation_id)
    if safe_id is None:
        return None
    connection = _open_acp_db_readonly()
    if connection is None:
        return None
    try:
        if not all(
            _acp_table_exists(connection, table)
            for table in ("acp_conversations", "acp_conversation_events", "comms_messages")
        ):
            return None
        conversation = connection.execute(
            "SELECT participants_json FROM acp_conversations WHERE conversation_id = ?", (safe_id,)
        ).fetchone()
        if conversation is None:
            return None
        participants = _acp_discussion_participants(conversation["participants_json"])
        entries = _acp_transcript_entries(connection, safe_id, participants)
        return {"conversation_id": safe_id, "messages": entries} if entries is not None else None
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


@router.get("/acp/conversations/{conversation_id}/transcript")
async def runtime_acp_conversation_transcript(conversation_id: str, request: Request):
    """Read body-inline ACP content for the local UI only; never mutate storage."""
    no_store = {"Cache-Control": "no-store"}
    if not _acp_transcript_client_is_loopback(request):
        return JSONResponse(status_code=403, content={"detail": "Forbidden"}, headers=no_store)
    transcript = await asyncio.to_thread(get_acp_conversation_transcript, conversation_id)
    if transcript is None:
        return JSONResponse(
            status_code=404,
            content={"detail": "Conversation not found"},
            headers=no_store,
        )
    return JSONResponse(content=transcript, headers=no_store)


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


@router.get("/routing-assignments")
async def runtime_routing_assignments(limit: int = Query(100, ge=1, le=100)):
    """Read-only routing authority decisions and their actual plane posture."""
    return await asyncio.to_thread(list_routing_assignments, limit=limit)


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
