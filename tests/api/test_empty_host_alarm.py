"""Tests for empty-host alarm and estate-wide lane_usage (#7139)."""

from __future__ import annotations

import json
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from scripts.api import atlas_jobs_router as load_mod
from scripts.api import occupancy as occupancy_mod
from scripts.api import state_router
from scripts.api.codexbar_usage import compute_weekly_pace_delta_pct, lane_is_under_weekly_pace
from scripts.api.main import app
from scripts.api.observer_presence import reset_observer_presence
from scripts.api.project_state_sanitize import (
    ProjectStateValidationError,
    sanitize_lane_usage_entry,
    validate_lane_usage_block,
    validate_report_document,
)
from scripts.api.project_state_store import (
    REPORT_TTL_SECONDS,
    get_freshest_lane_usage,
    reset_project_state_store,
    upsert_report,
)
from scripts.lexicon.runner import atlas_job
from tests.api.test_project_state import SHA_HEAD, SHA_MAIN, _document, _primary, _service

ROOT = Path(__file__).resolve().parents[2]
FLEET_HTML = ROOT / "dashboards" / "fleet.html"

loop_client = TestClient(
    app,
    base_url="http://127.0.0.1",
    client=("127.0.0.1", 50000),
    raise_server_exceptions=False,
)
client = TestClient(app, raise_server_exceptions=False)

_PLACEHOLDER_MAP = "teach-box=host-teacher,job-box=host-job"

PII_CODEXBAR_FIXTURE = {
    "provider": "claude",
    "usage": {
        "accountEmail": "operator@example.com",
        "accountOrganization": "Example Org",
        "loginMethod": "Claude Max 20x",
        "providerCost": {"limit": 20, "used": 5, "currencyCode": "USD"},
        "primary": {
            "windowMinutes": 300,
            "resetsAt": "2026-08-25T12:00:00Z",
            "usedPercent": 40,
        },
        "secondary": {
            "windowMinutes": 10080,
            "resetsAt": "2026-08-31T12:00:00Z",
            "usedPercent": 12,
        },
    },
}


FROZEN_NOW = datetime(2026, 8, 27, 12, 0, tzinfo=UTC)
WEEKLY_RESETS_AT = "2026-08-31T12:00:00Z"


def _under_pace_lane_usage(lane: str = "claude") -> dict[str, Any]:
    return _lane_usage(lane=lane, used_pct=5.0, resets_at=WEEKLY_RESETS_AT)


def _freeze_attention_now(monkeypatch: pytest.MonkeyPatch) -> None:
    original = occupancy_mod._evaluate_attention

    def wrapped(hosts: dict[str, Any], *, now_mono: float | None = None, now: datetime | None = None) -> list[str]:
        return original(hosts, now_mono=now_mono, now=FROZEN_NOW)

    monkeypatch.setattr(occupancy_mod, "_evaluate_attention", wrapped)


def _lane_usage(
    lane: str = "claude",
    *,
    used_pct: float = 10.0,
    resets_at: str = "2026-08-31T12:00:00Z",
    window: str = "weekly",
) -> dict[str, Any]:
    return {
        "lane": lane,
        "window": window,
        "used_pct": used_pct,
        "resets_at": resets_at,
    }


def _document_with_lane_usage(**overrides: Any) -> dict[str, Any]:
    doc = _document(host_id="mac-operator", services=[_service("api")])
    doc["lane_usage"] = overrides.pop("lane_usage", [_lane_usage()])
    doc.update(overrides)
    return doc


@pytest.fixture(autouse=True)
def _clear_store() -> None:
    reset_project_state_store()
    reset_observer_presence()
    occupancy_mod.reset_empty_host_tracking()
    yield
    reset_project_state_store()
    reset_observer_presence()
    occupancy_mod.reset_empty_host_tracking()


def _mac_operator_report() -> dict[str, Any]:
    return {
        "host_id": "mac-operator",
        "primary": _primary(head_sha=SHA_HEAD, origin_main_sha=SHA_MAIN),
        "worktrees": {"count": 1},
        "services": [_service("api")],
        "workers": [],
        "lane_usage": [_under_pace_lane_usage()],
        "collected_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }


def _observer_presence_body(*, status: str, host_id: str = "host-job") -> dict[str, Any]:
    return {
        "agent": "claude",
        "kind": "observer",
        "task_id": "7139",
        "status": status,
        "host_id": host_id,
        "instance_id": "123e4567-e89b-12d3-a456-426614174000",
    }


def _seed_host_job_empty_host_alarm(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _freeze_attention_now(monkeypatch)
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    fake = atlas_job.FakeHostAdapter()
    atlas_job.set_host_adapter(fake)
    load_mod.clear_host_load_cache()
    load_mod.set_host_load_cache("job-box", fake.host_load("job-box"))
    posted = loop_client.post("/api/fleet/projects/v1/report", json=_mac_operator_report())
    assert posted.status_code == 200
    occupancy_mod._idle_since_mono["host-job"] = time.monotonic() - occupancy_mod.EMPTY_HOST_IDLE_THRESHOLD_S - 1


def test_collector_allowlist_strips_pii_from_codexbar_fixture(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.api import project_state_collect as collect_mod
    from scripts.api.codexbar_usage import _normalize_provider_data

    normalized = _normalize_provider_data("claude", PII_CODEXBAR_FIXTURE)
    monkeypatch.setattr(collect_mod, "fetch_codexbar_usage", lambda _provider: normalized)
    row = collect_mod._lane_usage_row_from_provider("claude")
    assert row == {
        "lane": "claude",
        "window": "weekly",
        "used_pct": 12.0,
        "resets_at": "2026-08-31T12:00:00Z",
    }
    blob = json.dumps(row)
    assert "@" not in blob
    assert "Organization" not in blob
    assert "USD" not in blob
    assert "Max" not in blob


def test_server_rejects_foreign_lane_usage_field() -> None:
    with pytest.raises(ProjectStateValidationError, match="foreign field"):
        validate_lane_usage_block(
            [{"lane": "claude", "window": "weekly", "used_pct": 5.0, "resets_at": "2026-08-31T12:00:00Z", "email": "x"}]
        )


def test_five_hour_window_ignored_for_pace() -> None:
    now = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)
    assert lane_is_under_weekly_pace(
        5.0,
        (now + timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
        window_minutes=300,
        now=now,
    )
    weekly_resets = (now + timedelta(days=3)).isoformat().replace("+00:00", "Z")
    delta = compute_weekly_pace_delta_pct(5.0, weekly_resets, now=now)
    assert delta is not None
    assert lane_is_under_weekly_pace(5.0, weekly_resets, now=now)


def test_estate_wide_selection_uses_freshest_report() -> None:
    older = _document_with_lane_usage(
        lane_usage=[_lane_usage(used_pct=80.0)],
        collected_at="2026-08-24T10:00:00.000Z",
    )
    newer = _document_with_lane_usage(
        host_id="mac-operator",
        lane_usage=[_lane_usage(used_pct=5.0)],
        collected_at="2026-08-24T11:00:00.000Z",
    )
    upsert_report(older, now=datetime(2026, 8, 24, 10, 0, tzinfo=UTC))
    upsert_report(newer, now=datetime(2026, 8, 24, 11, 0, tzinfo=UTC))
    freshest = get_freshest_lane_usage()
    assert freshest is not None
    assert freshest.lanes[0]["used_pct"] == 5.0


def test_stale_lane_usage_yields_unknown_capacity(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    fake = atlas_job.FakeHostAdapter()
    atlas_job.set_host_adapter(fake)
    load_mod.clear_host_load_cache()
    load_mod.set_host_load_cache("job-box", fake.host_load("job-box"))
    try:
        doc = _document_with_lane_usage(host_id="host-job")
        upsert_report(doc, now_mono=100.0)
        hosts = {
            "host-job": {
                "host_id": "host-job",
                "status": "fresh",
                "idle_or_empty": True,
            }
        }
        occupancy_mod._idle_since_mono["host-job"] = 50.0
        payload_stale = occupancy_mod._evaluate_attention(
            hosts,
            now_mono=100.0 + REPORT_TTL_SECONDS + 1,
        )
        assert "empty_host_unknown_capacity:host-job" in payload_stale
    finally:
        atlas_job.set_host_adapter(None)
        load_mod.clear_host_load_cache()


def test_idle_since_boot_blocks_alarm_before_threshold(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    fake = atlas_job.FakeHostAdapter()
    atlas_job.set_host_adapter(fake)
    load_mod.clear_host_load_cache()
    load_mod.set_host_load_cache("job-box", fake.host_load("job-box"))
    upsert_report(_document_with_lane_usage())
    try:
        payload = occupancy_mod.occupancy_payload()
        assert payload["hosts"]["host-job"]["idle_or_empty"] is True
        assert payload["attention"] == []
    finally:
        atlas_job.set_host_adapter(None)
        load_mod.clear_host_load_cache()


def test_alarm_after_idle_threshold_with_under_pace_lane(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _freeze_attention_now(monkeypatch)
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    fake = atlas_job.FakeHostAdapter()
    atlas_job.set_host_adapter(fake)
    load_mod.clear_host_load_cache()
    load_mod.set_host_load_cache("job-box", fake.host_load("job-box"))
    upsert_report(_document_with_lane_usage(lane_usage=[_under_pace_lane_usage()]))
    occupancy_mod._idle_since_mono["host-job"] = time.monotonic() - occupancy_mod.EMPTY_HOST_IDLE_THRESHOLD_S - 1
    try:
        payload = occupancy_mod.occupancy_payload()
        assert "empty_host_underused:host-job" in payload["attention"]
    finally:
        atlas_job.set_host_adapter(None)
        load_mod.clear_host_load_cache()


def test_alarm_none_when_all_lanes_at_or_over_pace(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    fake = atlas_job.FakeHostAdapter()
    atlas_job.set_host_adapter(fake)
    load_mod.clear_host_load_cache()
    load_mod.set_host_load_cache("job-box", fake.host_load("job-box"))
    upsert_report(_document_with_lane_usage(lane_usage=[_lane_usage(used_pct=95.0)]))
    occupancy_mod._idle_since_mono["host-job"] = time.monotonic() - occupancy_mod.EMPTY_HOST_IDLE_THRESHOLD_S - 1
    try:
        payload = occupancy_mod.occupancy_payload()
        assert payload["attention"] == []
    finally:
        atlas_job.set_host_adapter(None)
        load_mod.clear_host_load_cache()


def test_activity_resets_idle_timer(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    fake = atlas_job.FakeHostAdapter()
    atlas_job.set_host_adapter(fake)
    load_mod.clear_host_load_cache()
    load_mod.set_host_load_cache("job-box", fake.host_load("job-box"))
    upsert_report(_document_with_lane_usage())
    occupancy_mod._idle_since_mono["host-job"] = time.monotonic() - occupancy_mod.EMPTY_HOST_IDLE_THRESHOLD_S - 1
    occupancy_mod._ever_had_activity["host-job"] = True
    occupancy_mod._evaluate_attention(
        {"host-job": {"idle_or_empty": False, "status": "fresh"}},
        now_mono=time.monotonic(),
    )
    occupancy_mod._idle_since_mono.pop("host-job", None)
    payload = occupancy_mod.occupancy_payload()
    assert payload["attention"] == []


def test_routing_budget_consumes_notebook_report(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(state_router, "_load_agent_budgets", lambda: ({}, []))
    monkeypatch.setattr(state_router, "get_provider_usage_data", lambda _lane: {"weekly_used_pct": None})
    upsert_report(_document_with_lane_usage(lane_usage=[_lane_usage(used_pct=25.0)]))
    now = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)
    data = state_router.compute_routing_budget(now)
    assert data["agents"]["claude"]["burn_pct_7d"] == 25.0
    assert data["agents"]["claude"]["notebook_report"]["source"] == "notebook-report"
    assert data["diagnostics"]["notebook_report_available"] is True
    assert data["recommendation"]["primary_agent_for_code"] is not None


def test_fleet_page_contract_renders_empty_host_banner() -> None:
    html = FLEET_HTML.read_text(encoding="utf-8")
    assert 'id="occupancy-attention-banner"' in html
    assert "renderOccupancyAttention" in html
    assert "empty_host_underused:" in html
    assert "empty_host_unknown_capacity:" in html


def test_unmocked_post_lane_usage_then_occupancy_attention(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _freeze_attention_now(monkeypatch)
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    fake = atlas_job.FakeHostAdapter()
    atlas_job.set_host_adapter(fake)
    load_mod.clear_host_load_cache()
    load_mod.set_host_load_cache("job-box", fake.host_load("job-box"))
    try:
        report = {
            "host_id": "mac-operator",
            "primary": _primary(head_sha=SHA_HEAD, origin_main_sha=SHA_MAIN),
            "worktrees": {"count": 1},
            "services": [_service("api")],
            "workers": [],
            "lane_usage": [_under_pace_lane_usage()],
            "collected_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }
        posted = loop_client.post("/api/fleet/projects/v1/report", json=report)
        assert posted.status_code == 200
        occupancy_mod._idle_since_mono["host-job"] = time.monotonic() - occupancy_mod.EMPTY_HOST_IDLE_THRESHOLD_S - 1
        response = client.get("/api/occupancy")
        assert response.status_code == 200
        data = response.json()
        assert "empty_host_underused:host-job" in data["attention"]
    finally:
        atlas_job.set_host_adapter(None)
        load_mod.clear_host_load_cache()


def test_sanitize_lane_usage_rejects_email_like_lane_token() -> None:
    assert (
        sanitize_lane_usage_entry(
            {
                "lane": "claude",
                "window": "weekly",
                "used_pct": 5.0,
                "resets_at": "operator@example.com",
            }
        )
        is None
    )


def test_validate_report_document_accepts_lane_usage() -> None:
    validate_report_document(_document_with_lane_usage())


def test_empty_host_alarm_fires_with_idle_observer_seat(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _seed_host_job_empty_host_alarm(monkeypatch, tmp_path)
    try:
        presence = loop_client.post(
            "/api/observer/presence",
            json=_observer_presence_body(status="idle"),
        )
        assert presence.status_code == 200

        response = client.get("/api/occupancy")
        assert response.status_code == 200
        data = response.json()
        host = data["hosts"]["host-job"]
        assert host["burn_state"] == "idle"
        assert host["idle_or_empty"] is True
        assert "empty_host_underused:host-job" in data["attention"]
    finally:
        atlas_job.set_host_adapter(None)
        load_mod.clear_host_load_cache()


def test_empty_host_alarm_suppressed_by_active_observer_seat(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _seed_host_job_empty_host_alarm(monkeypatch, tmp_path)
    try:
        presence = loop_client.post(
            "/api/observer/presence",
            json=_observer_presence_body(status="working"),
        )
        assert presence.status_code == 200

        response = client.get("/api/occupancy")
        assert response.status_code == 200
        data = response.json()
        host = data["hosts"]["host-job"]
        assert host["burn_state"] == "active"
        assert host["idle_or_empty"] is False
        assert "empty_host_underused:host-job" not in data["attention"]
    finally:
        atlas_job.set_host_adapter(None)
        load_mod.clear_host_load_cache()


def test_post_report_rejects_foreign_lane_usage_field() -> None:
    doc = _document_with_lane_usage(
        lane_usage=[
            {
                "lane": "claude",
                "window": "weekly",
                "used_pct": 5.0,
                "resets_at": "2026-08-31T12:00:00Z",
                "accountEmail": "hidden@example.com",
            }
        ]
    )
    response = loop_client.post("/api/fleet/projects/v1/report", json=doc)
    assert response.status_code == 400
