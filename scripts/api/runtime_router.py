"""Runtime observability API router."""

from __future__ import annotations

import asyncio
import importlib
import inspect
import json
import os
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
