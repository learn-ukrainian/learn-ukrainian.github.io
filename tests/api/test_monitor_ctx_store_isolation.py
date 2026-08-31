"""#7494 residual: consumed store injection, ctx-scoped caches, epics stub via create_app."""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import scripts.api.main as api_main
from scripts.api import dashboard_router, work_router
from scripts.api.monitor_context import fixture_context, production_context
from scripts.api.observer_presence import _STORE as PRODUCTION_PRESENCE_STORE
from scripts.api.observer_presence import list_live, reset_observer_presence
from scripts.api.opsec_sanitize import REDACTED_ABSOLUTE_PATH, opsec_path_sanitizer_middleware
from scripts.api.project_state_store import _STORE as PRODUCTION_REPORT_STORE
from scripts.api.project_state_store import reset_project_state_store
from scripts.api.state_helpers import cache_get, cache_invalidate, cache_set, ctx_cache_scope
from tests.epics_monitor_stub import epics_app_for_store

pytestmark = pytest.mark.repo_invariant

PLANTED_PATH = "/tmp/opsec-canary-root/repo"
_HEARTBEAT = {
    "agent": "grok-bot",
    "kind": "observer",
    "task_id": "7494",
    "epic": "7177",
    "status": "working",
    "summary": "fixture isolation probe",
}


@asynccontextmanager
async def _no_lifespan(_app):
    yield


@pytest.fixture(autouse=True)
def _clear_production_stores() -> None:
    reset_observer_presence()
    reset_project_state_store()
    cache_invalidate()
    yield
    reset_observer_presence()
    reset_project_state_store()
    cache_invalidate()


def test_fixture_presence_post_never_touches_production_store(tmp_path: Path) -> None:
    """#7494 / 4.3: create_app fixture writes land on ctx.stores.presence_store only."""
    before = len(PRODUCTION_PRESENCE_STORE)
    app = api_main.create_app(fixture_context(tmp_path), lifespan=_no_lifespan)
    client = TestClient(
        app,
        base_url="http://127.0.0.1",
        client=("127.0.0.1", 50000),
        raise_server_exceptions=False,
    )
    posted = client.post("/api/observer/presence", json=_HEARTBEAT)
    assert posted.status_code == 200, posted.text
    assert posted.json()["agent"] == "grok-bot"

    fixture_store = app.state.ctx.stores.presence_store
    assert fixture_store is not None
    assert fixture_store is not PRODUCTION_PRESENCE_STORE
    assert len(fixture_store) == 1
    assert len(PRODUCTION_PRESENCE_STORE) == before
    assert list_live(store=fixture_store)
    assert not list_live(store=PRODUCTION_PRESENCE_STORE) or all(
        row.task_id != "7494" for row in list_live(store=PRODUCTION_PRESENCE_STORE)
    )


def test_fixture_report_post_never_touches_production_store(tmp_path: Path, monkeypatch) -> None:
    """#7494 / 4.3: project-state report ingest uses ctx.stores.report_store."""
    from datetime import UTC, datetime

    from scripts.api import project_state_router

    before = set(PRODUCTION_REPORT_STORE)
    ctx = fixture_context(tmp_path)
    app = api_main.create_app(ctx, lifespan=_no_lifespan)
    monkeypatch.setattr(
        project_state_router,
        "allowed_reporter_host_ids",
        lambda _ctx=None: {"host-teacher"},
    )
    monkeypatch.setattr(
        project_state_router,
        "validate_report_document",
        lambda _doc: None,
    )
    client = TestClient(
        app,
        base_url="http://127.0.0.1",
        client=("127.0.0.1", 50000),
        raise_server_exceptions=False,
    )
    collected = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    document = {
        "host_id": "host-teacher",
        "primary": {"origin_main_sha": "abc1234"},
        "worktrees": {"count": 0},
        "services": [],
        "collected_at": collected,
    }
    posted = client.post("/api/fleet/projects/v1/report", json=document)
    assert posted.status_code == 200, posted.text

    fixture_store = app.state.ctx.stores.report_store
    assert fixture_store is not None
    assert fixture_store is not PRODUCTION_REPORT_STORE
    assert "host-teacher" in fixture_store
    assert "host-teacher" not in before
    assert "host-teacher" not in PRODUCTION_REPORT_STORE


def test_work_projection_cache_is_scoped_per_context(tmp_path: Path) -> None:
    """#7494: two apps must not share work projection TTL entries."""
    a_ctx = fixture_context(tmp_path / "a")
    b_ctx = fixture_context(tmp_path / "b")
    key_a = work_router.projection_cache_key({}, a_ctx)
    key_b = work_router.projection_cache_key({}, b_ctx)
    assert key_a != key_b
    assert ctx_cache_scope(a_ctx) in key_a
    assert ctx_cache_scope(b_ctx) in key_b

    cache_set(key_a, {"items": [], "sentinel": "a-only"})
    assert cache_get(key_b, ttl=30.0) is None
    assert cache_get(key_a, ttl=30.0)["sentinel"] == "a-only"


def test_consultation_and_dashboard_caches_are_scoped(tmp_path: Path) -> None:
    """#7494: consultation + dashboard TTL / last-good storage scoped by context."""
    a = fixture_context(tmp_path / "a")
    b = fixture_context(tmp_path / "b")
    assert ctx_cache_scope(a) != ctx_cache_scope(b)

    hist_a = f"consultation_history_all{ctx_cache_scope(a)}"
    hist_b = f"consultation_history_all{ctx_cache_scope(b)}"
    cache_set(hist_a, [{"track": "a1", "slug": "from-a"}])
    assert cache_get(hist_b, ttl=30) is None

    scope_a = dashboard_router._overview_scope(a)
    scope_b = dashboard_router._overview_scope(b)
    dashboard_router._overview_last_good_by_scope[scope_a] = {"tracks": [], "sentinel": "a"}
    assert scope_b not in dashboard_router._overview_last_good_by_scope
    assert dashboard_router._overview_cache_key(a) != dashboard_router._overview_cache_key(b)


def test_epics_stub_runs_create_app_opsec_sanitizer(tmp_path: Path, monkeypatch) -> None:
    """#7494 / 4.8a: epics acceptance stub is a real create_app() instance."""
    ctx = fixture_context(tmp_path)
    store = ctx.stores.epics_store
    assert store is not None
    app = epics_app_for_store(store, tmp_path)

    # Middleware stack includes the OPSEC path sanitizer (bare FastAPI did not).
    dispatches = [
        entry.kwargs.get("dispatch")
        for entry in app.user_middleware
        if entry.kwargs and entry.kwargs.get("dispatch") is not None
    ]
    assert opsec_path_sanitizer_middleware in dispatches
    # Full create_app route table, not a bare epics-only FastAPI.
    assert app.title == "Playground API"
    assert len(app.routes) > 10

    real_audit = store.audit

    def _leaky_audit() -> dict:
        payload = real_audit()
        payload = dict(payload)
        payload["schema_versions"] = {"leaked_root": PLANTED_PATH}
        return payload

    monkeypatch.setattr(store, "audit", _leaky_audit)
    body = TestClient(app, base_url="http://127.0.0.1").get("/api/epics/v1/health").json()
    encoded = json.dumps(body)
    assert PLANTED_PATH not in encoded
    assert body["schema_versions"]["leaked_root"] == REDACTED_ABSOLUTE_PATH


def test_production_context_still_shares_module_presence_store() -> None:
    """Production wiring keeps the module singleton so live heartbeats stay coherent."""
    prod = production_context()
    assert prod.stores.presence_store is PRODUCTION_PRESENCE_STORE
    assert prod.stores.report_store is PRODUCTION_REPORT_STORE
    assert prod.stores.work_in_flight is work_router._IN_FLIGHT_BUILDS
