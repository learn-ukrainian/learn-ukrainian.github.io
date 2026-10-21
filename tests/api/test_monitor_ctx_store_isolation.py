"""#7494 residual: consumed store injection, ctx-scoped caches, epics stub via create_app."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scripts.api.monitor_context import fixture_context
from scripts.api.observer_presence import reset_observer_presence
from scripts.api.opsec_sanitize import REDACTED_ABSOLUTE_PATH, opsec_path_sanitizer_middleware
from scripts.api.project_state_store import reset_project_state_store
from scripts.api.state_helpers import cache_invalidate
from tests.epics_monitor_stub import epics_app_for_store

pytestmark = pytest.mark.repo_invariant

PLANTED_PATH = "/srv/opsec-canary-root/repo"


@pytest.fixture(autouse=True)
def _clear_production_stores() -> None:
    reset_observer_presence()
    reset_project_state_store()
    cache_invalidate()
    yield
    reset_observer_presence()
    reset_project_state_store()
    cache_invalidate()


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
    assert app.title == "Ops API"
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
