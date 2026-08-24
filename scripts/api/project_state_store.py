"""In-process TTL store for pushed per-host project-state reports."""

from __future__ import annotations

import re
import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from scripts.api.codexbar_usage import lane_is_under_weekly_pace

REPORT_TTL_SECONDS = 15 * 60
STALE_UPSTREAM_THRESHOLD_S = 3600
PROJECT_STATE_SCHEMA = "monitor-project-state.v1"
PROJECT_STATE_SCHEMA_V2 = "monitor-project-state.v2"
_COLLECTED_AT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")
_FUTURE_SKEW_SECONDS = 60

_STORE_LOCK = threading.Lock()
_STORE: dict[str, StoredReport] = {}


class CollectedAtError(ValueError):
    """collected_at failed parse or bounds validation."""


class StaleReportError(ValueError):
    """Incoming report is older than or equal to the stored report."""


@dataclass(frozen=True)
class FreshestLaneUsage:
    lanes: list[dict[str, Any]]
    collected_at: datetime
    age_s: float
    host_id: str


def reset_project_state_store() -> None:
    with _STORE_LOCK:
        _STORE.clear()


@dataclass(frozen=True)
class StoredReport:
    host_id: str
    document: dict[str, Any]
    received_at_mono: float
    expires_at_mono: float
    collected_at: datetime
    workers_status: str


def lane_usage_status_from_document(document: dict[str, Any]) -> str:
    if document.get("lane_usage") is None:
        return "unreported"
    return "reported"


def get_freshest_lane_usage(*, now_mono: float | None = None) -> FreshestLaneUsage | None:
    deadline = time.monotonic() if now_mono is None else now_mono
    with _STORE_LOCK:
        stale = [host_id for host_id, row in _STORE.items() if row.expires_at_mono <= deadline]
        for host_id in stale:
            del _STORE[host_id]
        candidates = [
            row
            for row in _STORE.values()
            if isinstance(row.document.get("lane_usage"), list) and row.document["lane_usage"]
        ]
    if not candidates:
        return None
    best = max(candidates, key=lambda row: row.collected_at)
    age_s = max(0.0, deadline - best.received_at_mono)
    lanes = [row for row in best.document["lane_usage"] if row.get("window") == "weekly"]
    if not lanes:
        return None
    return FreshestLaneUsage(
        lanes=lanes,
        collected_at=best.collected_at,
        age_s=round(age_s, 2),
        host_id=best.host_id,
    )


def any_lane_under_weekly_pace(
    lanes: list[dict[str, Any]],
    *,
    now: datetime | None = None,
) -> bool:
    for row in lanes:
        if row.get("window") != "weekly":
            continue
        used_pct = row.get("used_pct")
        resets_at = row.get("resets_at")
        if not isinstance(used_pct, (int, float)) or not isinstance(resets_at, str):
            continue
        if lane_is_under_weekly_pace(float(used_pct), resets_at, now=now):
            return True
    return False


def all_weekly_lanes_at_or_over_pace(
    lanes: list[dict[str, Any]],
    *,
    now: datetime | None = None,
) -> bool:
    weekly_rows = [row for row in lanes if row.get("window") == "weekly"]
    if not weekly_rows:
        return False
    for row in weekly_rows:
        used_pct = row.get("used_pct")
        resets_at = row.get("resets_at")
        if not isinstance(used_pct, (int, float)) or not isinstance(resets_at, str):
            return False
        if lane_is_under_weekly_pace(float(used_pct), resets_at, now=now):
            return False
    return True


def parse_collected_at(
    value: str,
    *,
    now: datetime | None = None,
    ttl_seconds: int = REPORT_TTL_SECONDS,
) -> datetime:
    if not isinstance(value, str) or not _COLLECTED_AT_RE.fullmatch(value):
        raise CollectedAtError("invalid collected_at")
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise CollectedAtError("invalid collected_at") from exc
    parsed = parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)
    clock = now or datetime.now(UTC)
    if parsed > clock + timedelta(seconds=_FUTURE_SKEW_SECONDS):
        raise CollectedAtError("collected_at in the future")
    if parsed < clock - timedelta(seconds=ttl_seconds):
        raise CollectedAtError("collected_at older than ttl")
    return parsed


def workers_status_from_document(document: dict[str, Any]) -> str:
    if document.get("workers") is None:
        return "unreported"
    return "reported"


def upsert_report(
    document: dict[str, Any],
    *,
    now_mono: float | None = None,
    now: datetime | None = None,
    ttl_seconds: int = REPORT_TTL_SECONDS,
) -> StoredReport:
    stamp = time.monotonic() if now_mono is None else now_mono
    host_id = str(document["host_id"])
    collected_at = parse_collected_at(str(document["collected_at"]), now=now, ttl_seconds=ttl_seconds)
    workers_status = workers_status_from_document(document)
    row = StoredReport(
        host_id=host_id,
        document=document,
        received_at_mono=stamp,
        expires_at_mono=stamp + ttl_seconds,
        collected_at=collected_at,
        workers_status=workers_status,
    )
    with _STORE_LOCK:
        existing = _STORE.get(host_id)
        if existing is not None and collected_at <= existing.collected_at:
            raise StaleReportError("stale_report")
        _STORE[host_id] = row
    return row


def get_stored_report(host_id: str) -> StoredReport | None:
    with _STORE_LOCK:
        return _STORE.get(host_id)


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
