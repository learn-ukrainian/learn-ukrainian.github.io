"""Read-only Monitor surface for Entire capture and local context recall."""

from __future__ import annotations

import logging
import os
import sqlite3
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Query

from scripts.entire_context.paths import projection_path, shared_repository_root
from scripts.entire_context.provider import load_provider_capabilities, load_provider_status
from scripts.entire_context.recall import RecallInputError, search_past_work
from scripts.entire_context.resolvers import (
    default_fleet_root,
    default_issue_cache,
    default_monitor_root,
)
from scripts.entire_context.store import ContextLinkStore
from scripts.fleet_comms.message_plane import default_plane_root

from .config import LIVE_REPO_ROOT, PROJECT_ROOT
from .repository_authority import preparation_data_root

router = APIRouter(tags=["entire-context"])
logger = logging.getLogger(__name__)

_PROJECTION_COUNT_STATES = ("pending", "promoted", "tombstoned")
_ACP_HEALTH_NUMBER_FIELDS = ("attempts", "failures", "lag_seconds", "retries")
_ACP_HEALTH_TEXT_FIELDS = (
    "last_attempt_at",
    "last_failure_at",
    "last_failure_reason",
    "last_reconciliation_at",
    "last_success_at",
    "source_latest_at",
)


def _repo_root() -> Path:
    return preparation_data_root(
        project_root=Path(PROJECT_ROOT),
        live_repo_root=Path(LIVE_REPO_ROOT),
    )


def _rollover_root(root: Path) -> Path:
    """Resolve the existing shared rollover registry, with an explicit service override."""
    configured = os.environ.get("ENTIRE_CONTEXT_ROLLOVER_ROOT")
    return Path(configured) if configured else shared_repository_root(root)


def _safe_count(value: Any) -> int:
    """Normalize one aggregate count without letting malformed telemetry fail a GET."""
    if isinstance(value, bool):
        return 0
    try:
        return max(0, int(value))
    except (TypeError, ValueError, OverflowError):
        return 0


def _optional_count(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        count = int(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return count if count >= 0 else None


def _safe_text(value: Any) -> str | None:
    """Return one bounded machine field; omit bodies and path-like values."""
    if not isinstance(value, str) or not value or len(value.encode("utf-8")) > 256:
        return None
    if value.startswith(("/", "~")) or "\\" in value:
        return None
    return value


def _safe_count_map(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, int] = {}
    for key, raw_count in value.items():
        safe_key = _safe_text(key)
        safe_count = _optional_count(raw_count)
        if safe_key is not None and safe_count is not None:
            result[safe_key] = safe_count
    return dict(sorted(result.items()))


def _public_projection_health(value: Any) -> dict[str, Any]:
    """Project the stable reliability contract without forwarding unknown fields."""
    if not isinstance(value, dict):
        return {}
    result: dict[str, Any] = {}
    for field in ("pending", "tombstoned", "dangling"):
        safe_count = _optional_count(value.get(field))
        if safe_count is not None:
            result[field] = safe_count
    result["tombstones_by_reason"] = _safe_count_map(value.get("tombstones_by_reason"))
    raw_acp = value.get("acp")
    if not isinstance(raw_acp, dict):
        return result
    acp: dict[str, Any] = {}
    for field in _ACP_HEALTH_NUMBER_FIELDS:
        if field == "lag_seconds" and raw_acp.get(field) is None:
            acp[field] = None
        else:
            safe_count = _optional_count(raw_acp.get(field))
            if safe_count is not None:
                acp[field] = safe_count
    for field in _ACP_HEALTH_TEXT_FIELDS:
        acp[field] = _safe_text(raw_acp.get(field))
    raw_last = raw_acp.get("last_reconciliation")
    if isinstance(raw_last, dict):
        acp["last_reconciliation"] = {
            "examined": _safe_count(raw_last.get("examined")),
            "changed": _safe_count(raw_last.get("changed")),
            "skipped": _safe_count(raw_last.get("skipped")),
            "truncated": raw_last.get("truncated") is True,
            "limit": _safe_count(raw_last.get("limit")),
        }
    result["acp"] = acp
    return result


def _public_projection_status(projection: dict[str, Any]) -> dict[str, Any]:
    """Expose only body-free, non-path projection health fields to Monitor."""
    if projection.get("available") is not True:
        return {
            "available": False,
            "reason": _safe_text(projection.get("reason")) or "projection_unavailable",
        }
    raw_counts = projection.get("counts")
    counts = raw_counts if isinstance(raw_counts, dict) else {}
    public: dict[str, Any] = {
        "available": True,
        "schema_version": _safe_count(projection.get("schema_version")),
        "counts": {
            state: _safe_count(counts.get(state, 0)) for state in _PROJECTION_COUNT_STATES
        },
        "events": _safe_count(projection.get("events")),
        "last_event_at": _safe_text(projection.get("last_event_at")),
        "use_receipts": _safe_count(projection.get("use_receipts")),
        "last_use_at": _safe_text(projection.get("last_use_at")),
        "uses_by_consumer": _safe_count_map(projection.get("uses_by_consumer")),
    }
    projection_health = _public_projection_health(projection.get("projection_health"))
    if projection_health:
        public["projection_health"] = projection_health
    return public


def _projection_status(root: Path) -> dict[str, Any]:
    db_path = projection_path(root)
    if not db_path.is_file():
        return {"available": False, "reason": "projection_missing"}
    try:
        status = ContextLinkStore(db_path).status()
    except (sqlite3.Error, KeyError, TypeError, ValueError):
        return {"available": False, "reason": "projection_unreadable"}
    return {"available": True, **status}


@router.get("/status")
def entire_context_status() -> dict[str, Any]:
    """Truthfully distinguish capture, recall availability, and proven use."""
    root = _repo_root()
    projection = _public_projection_status(_projection_status(root))
    provider = load_provider_status(root)
    capabilities = load_provider_capabilities(root)
    counts = projection.get("counts", {}) if projection.get("available") else {}
    installed_agents = (
        provider.get("installed_agents", [])
        if isinstance(provider, dict) and provider.get("available") is True
        else []
    )
    if not isinstance(installed_agents, list):
        installed_agents = []
    installed_agents = [
        agent for agent in (_safe_text(value) for value in installed_agents) if agent is not None
    ]
    promoted_links = _safe_count(counts.get("promoted"))
    use_receipts = _safe_count(projection.get("use_receipts"))
    return {
        "schema": "entire-context-monitor.v1",
        "body_free": True,
        "authoritative": False,
        "capture": {
            "configured": isinstance(provider, dict) and provider.get("enabled") is True,
            "installed_agents": installed_agents,
            "native_agent_installed": bool(installed_agents),
            "provider_status_available": isinstance(provider, dict)
            and provider.get("available") is True,
        },
        "recall": {
            "available": projection.get("available") is True
            and promoted_links > 0,
            "reason": projection.get("reason"),
            "promoted_links": promoted_links,
            "projection": projection,
        },
        "use": {
            "proven": projection.get("available") is True
            and use_receipts > 0,
            "receipts": use_receipts,
            "last_use_at": projection.get("last_use_at"),
            "by_consumer": _safe_count_map(projection.get("uses_by_consumer")),
        },
        "provider": {
            "available": isinstance(provider, dict) and provider.get("available") is True,
            "enabled": isinstance(provider, dict) and provider.get("enabled") is True,
            "stale": isinstance(provider, dict) and provider.get("stale") is True,
            "version": _safe_text(provider.get("version")) if isinstance(provider, dict) else None,
            "capabilities": capabilities,
        },
    }


@router.get("/search")
def entire_context_search(
    q: str = Query(min_length=1, max_length=256),
    limit: int = Query(default=5, ge=1, le=10),
) -> dict[str, Any]:
    """Return reverified local locator cards; never call Entire or the network."""
    root = _repo_root()
    status = _projection_status(root)
    if status.get("available") is not True:
        return {
            "schema": "ec-search.v1",
            "available": False,
            "reason": status.get("reason", "projection_unavailable"),
            "results": [],
        }
    acp_root = Path(
        os.environ.get("ENTIRE_CONTEXT_ACP_ROOT", default_plane_root(repo_root=root))
    )
    try:
        payload = search_past_work(
            ContextLinkStore(projection_path(root)),
            q,
            repo=root,
            acp_root=acp_root,
            rollover_root=_rollover_root(root),
            fleet_root=default_fleet_root(root),
            monitor_root=default_monitor_root(root),
            issue_cache_path=default_issue_cache(root),
            limit=limit,
        )
    except RecallInputError as exc:
        # Map to a closed set of stable API codes; never return raw exception
        # text to HTTP clients (CodeQL py/stack-trace-exposure).
        code = "invalid_request"
        if exc.args:
            for candidate in (
                "query_invalid",
                "seed_invalid",
                "locator_id_invalid",
                "handoff_seed_limit",
            ):
                if exc.args[0] == candidate:
                    code = candidate
                    break
            else:
                logger.exception(
                    "unexpected RecallInputError in entire-context search"
                )
        return {
            "schema": "ec-search.v1",
            "available": True,
            "error": code,
            "results": [],
        }
    except (sqlite3.Error, KeyError, TypeError, ValueError):
        return {
            "schema": "ec-search.v1",
            "available": False,
            "reason": "projection_unreadable",
            "results": [],
        }
    return {"available": True, **payload}
