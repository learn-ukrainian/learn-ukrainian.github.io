"""Read-only Monitor surface for Entire capture and local context recall."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Query

from scripts.entire_context.paths import projection_path, shared_repository_root
from scripts.entire_context.provider import load_provider_status
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


def _repo_root() -> Path:
    return preparation_data_root(
        project_root=Path(PROJECT_ROOT),
        live_repo_root=Path(LIVE_REPO_ROOT),
    )


def _rollover_root(root: Path) -> Path:
    """Resolve the existing shared rollover registry, with an explicit service override."""
    configured = os.environ.get("ENTIRE_CONTEXT_ROLLOVER_ROOT")
    return Path(configured) if configured else shared_repository_root(root)


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
    projection = _projection_status(root)
    provider = load_provider_status(root)
    counts = projection.get("counts", {}) if projection.get("available") else {}
    installed_agents = provider.get("installed_agents", []) if provider.get("available") else []
    return {
        "schema": "entire-context-monitor.v1",
        "body_free": True,
        "authoritative": False,
        "capture": {
            "configured": provider.get("enabled") is True,
            "installed_agents": installed_agents,
            "native_agent_installed": bool(installed_agents),
            "provider_status_available": provider.get("available") is True,
        },
        "recall": {
            "available": projection.get("available") is True
            and int(counts.get("promoted", 0)) > 0,
            "promoted_links": int(counts.get("promoted", 0)),
            "projection": projection,
        },
        "use": {
            "proven": projection.get("available") is True
            and int(projection.get("use_receipts", 0)) > 0,
            "receipts": int(projection.get("use_receipts", 0)),
            "last_use_at": projection.get("last_use_at"),
            "by_consumer": projection.get("uses_by_consumer", {}),
        },
        "provider": provider,
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
        return {
            "schema": "ec-search.v1",
            "available": True,
            "error": str(exc),
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
