"""In-process TTL store for pushed per-host project-state reports."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any

REPORT_TTL_SECONDS = 15 * 60
STALE_UPSTREAM_THRESHOLD_S = 3600
PROJECT_STATE_SCHEMA = "monitor-project-state.v1"

_STORE_LOCK = threading.Lock()
_STORE: dict[str, StoredReport] = {}


@dataclass(frozen=True)
class StoredReport:
    host_id: str
    document: dict[str, Any]
    received_at_mono: float
    expires_at_mono: float


def reset_project_state_store() -> None:
    with _STORE_LOCK:
        _STORE.clear()


def upsert_report(
    document: dict[str, Any],
    *,
    now_mono: float | None = None,
    ttl_seconds: int = REPORT_TTL_SECONDS,
) -> StoredReport:
    stamp = time.monotonic() if now_mono is None else now_mono
    host_id = str(document["host_id"])
    row = StoredReport(
        host_id=host_id,
        document=document,
        received_at_mono=stamp,
        expires_at_mono=stamp + ttl_seconds,
    )
    with _STORE_LOCK:
        _STORE[host_id] = row
    return row


def get_live_report(host_id: str, *, now_mono: float | None = None) -> StoredReport | None:
    deadline = time.monotonic() if now_mono is None else now_mono
    with _STORE_LOCK:
        row = _STORE.get(host_id)
        if row is None:
            return None
        if row.expires_at_mono <= deadline:
            del _STORE[host_id]
            return None
        return row


def list_live_reports(*, now_mono: float | None = None) -> list[StoredReport]:
    deadline = time.monotonic() if now_mono is None else now_mono
    with _STORE_LOCK:
        stale = [host_id for host_id, row in _STORE.items() if row.expires_at_mono <= deadline]
        for host_id in stale:
            del _STORE[host_id]
        return list(_STORE.values())


def compute_service_drift(
    service: dict[str, Any],
    primary: dict[str, Any],
    *,
    stale_upstream: bool,
) -> bool | str:
    if service.get("repo") == "sibling":
        return "not_applicable"
    if stale_upstream:
        return "unknown"
    if service.get("state") != "running":
        return "unknown"
    origin_main_sha = primary.get("origin_main_sha")
    if not isinstance(origin_main_sha, str):
        return "unknown"
    mode = service.get("serving_mode")
    if mode == "release":
        serving_sha = service.get("serving_sha")
        if not isinstance(serving_sha, str):
            return "unknown"
        return serving_sha != origin_main_sha
    if mode == "checkout":
        checkout_sha = service.get("checkout_sha")
        if not isinstance(checkout_sha, str):
            return "unknown"
        return checkout_sha != origin_main_sha
    return "unknown"


def shape_host_payload(
    document: dict[str, Any],
    *,
    age_s: float,
    freshness: str,
    collected_at: str,
) -> dict[str, Any]:
    primary = document["primary"]
    stale_upstream = float(primary.get("origin_main_age_s", 0)) > STALE_UPSTREAM_THRESHOLD_S
    services_out: list[dict[str, Any]] = []
    attention: list[str] = []

    if stale_upstream:
        attention.append("stale_upstream")
    if int(primary.get("dirty_count", 0)) > 0:
        attention.append("dirty_primary")
    if freshness == "stale":
        attention.append("stale_report")

    for service in document.get("services", []):
        drift = compute_service_drift(service, primary, stale_upstream=stale_upstream)
        if drift is True:
            attention.append(f"drift:{service.get('name')}")
        services_out.append(
            {
                "name": service["name"],
                "state": service["state"],
                "repo": service["repo"],
                "serving_mode": service["serving_mode"],
                "serving_sha": service.get("serving_sha"),
                "checkout_sha": service.get("checkout_sha"),
                "drift": drift,
            }
        )

    return {
        "host_id": document["host_id"],
        "freshness": freshness,
        "age_s": round(max(0.0, age_s), 2),
        "collected_at": collected_at,
        "primary": {
            "head_sha": primary["head_sha"],
            "origin_main_sha": primary["origin_main_sha"],
            "origin_main_age_s": primary["origin_main_age_s"],
            "ahead": primary["ahead"],
            "behind": primary["behind"],
            "dirty_count": primary["dirty_count"],
        },
        "worktrees": document.get("worktrees", {"count": 0}),
        "services": services_out,
        "attention": attention,
    }


def freshness_from_age(age_s: float, *, ttl_seconds: int = REPORT_TTL_SECONDS) -> str:
    if age_s < 0:
        return "unknown"
    if age_s <= ttl_seconds:
        return "fresh"
    return "stale"


def unknown_host_payload(host_id: str) -> dict[str, Any]:
    return {
        "host_id": host_id,
        "freshness": "unknown",
        "age_s": None,
        "collected_at": None,
        "primary": None,
        "worktrees": None,
        "services": [],
        "attention": [],
    }
