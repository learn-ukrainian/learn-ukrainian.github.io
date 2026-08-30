"""Tests for /api/cluster/readiness (#7365 Phase 0b ping · #7493 hardening).

Contract under test:
- an absent sqlite database is NOT accessible, and a GET creates no
  directories or files (readiness has zero side effects);
- pg authority requires a live ``SELECT 1`` (DSN presence alone never reads
  as ready) and fails closed quickly against an unreachable DSN;
- reasons are fixed OPSEC-safe codes, never exception text or paths;
- ``task_index`` is optional in Phase 0 and never affects readiness.
"""

from __future__ import annotations

import os
import sqlite3
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scripts.api import main as api_main
from scripts.api.cluster_router import check_cluster_readiness
from scripts.api.monitor_context import fixture_context
from scripts.control_plane import storage
from scripts.control_plane.storage import StoreId

pytestmark = pytest.mark.repo_invariant

# Unreachable local port — fails closed quickly without DNS (no example.invalid).
_UNREACHABLE_DSN = "postgresql://cp_ci:cp_ci@127.0.0.1:1/postgres"
_PG_DSN_ENV = "LEARN_UKRAINIAN_CP_PG_DSN"

_PROBED_SQLITE_STORES = (StoreId.FLEET_COMMS, StoreId.WRITE_OWNERSHIP)


def _ready_context(tmp_path: Path):
    """Fixture context with every probed sqlite database actually present."""
    ctx = fixture_context(tmp_path)
    for store_id in _PROBED_SQLITE_STORES:
        db_path = storage.sqlite_path(store_id, repo_root=tmp_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        sqlite3.connect(db_path).close()
    session_path = Path(ctx.stores.session_streams_database.path)
    session_path.parent.mkdir(parents=True, exist_ok=True)
    sqlite3.connect(session_path).close()
    return ctx


def test_absent_databases_are_not_ready_and_get_has_no_side_effects(
    tmp_path: Path,
) -> None:
    """#7493: an empty host must answer unready, and the GET must not mkdir."""
    client = TestClient(api_main.create_app(fixture_context(tmp_path)))
    before = {p.relative_to(tmp_path) for p in tmp_path.rglob("*")}

    resp = client.get("/api/cluster/readiness")
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "unready"
    assert data["ready"] is False
    assert data["can_serve_cluster_reads"] is False
    assert data["ha_claimed"] is False

    seam = data["storage_seam"]
    for store_id in _PROBED_SQLITE_STORES:
        entry = seam[store_id.value]
        assert entry["accessible"] is False
        assert entry["reason"] == "sqlite_database_missing"

    # Zero side effects: the probe created no directories or files.
    after = {p.relative_to(tmp_path) for p in tmp_path.rglob("*")}
    assert after == before


def test_existing_databases_answer_ready(tmp_path: Path) -> None:
    ctx = _ready_context(tmp_path)
    data = TestClient(api_main.create_app(ctx)).get("/api/cluster/readiness").json()
    assert data["status"] == "ready"
    assert data["ready"] is True
    assert data["can_serve_cluster_reads"] is True
    assert data["ha_claimed"] is False  # Never claims multi-host HA in Phase 0
    assert "checked_at" in data

    seam = data["storage_seam"]
    for store_id in (*_PROBED_SQLITE_STORES, StoreId.SESSION_STREAMS):
        entry = seam[store_id.value]
        assert entry["authority"] == "sqlite"
        assert entry["accessible"] is True, store_id


def test_session_streams_probes_the_injected_store(tmp_path: Path) -> None:
    """#7493: readiness must probe the context's store, not a re-derived path."""
    ctx = _ready_context(tmp_path)
    database = ctx.stores.session_streams_database
    assert database is not None
    assert Path(database.path).exists()

    data = check_cluster_readiness(ctx)
    assert data["storage_seam"][StoreId.SESSION_STREAMS.value]["accessible"] is True


def test_task_index_is_optional_and_never_blocks(tmp_path: Path) -> None:
    data = check_cluster_readiness(_ready_context(tmp_path))
    entry = data["storage_seam"][StoreId.TASK_INDEX.value]
    assert entry["accessible"] is False
    assert entry["optional"] is True
    assert data["ready"] is True  # inaccessible-but-optional must not block


def test_reasons_are_codes_not_paths(tmp_path: Path) -> None:
    data = check_cluster_readiness(fixture_context(tmp_path))
    for entry in data["storage_seam"].values():
        reason = entry.get("reason")
        if reason is not None:
            assert "/" not in reason and "\\" not in reason
            assert str(tmp_path) not in reason


def test_cluster_readiness_plain_python_fallback() -> None:
    data = check_cluster_readiness()
    assert data["ha_claimed"] is False
    assert "storage_seam" in data
    assert "checked_at" in data


def test_fails_closed_when_pg_dsn_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY_FLEET_COMMS", "pg")
    monkeypatch.delenv(_PG_DSN_ENV, raising=False)
    ctx = _ready_context(tmp_path)

    data = TestClient(api_main.create_app(ctx)).get("/api/cluster/readiness").json()
    assert data["ready"] is False
    fleet = data["storage_seam"][StoreId.FLEET_COMMS.value]
    assert fleet["authority"] == "pg"
    assert fleet["accessible"] is False
    assert fleet["reason"] == "pg_dsn_missing"


def test_unreachable_pg_dsn_fails_closed_quickly(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """DSN presence alone is never ready; the probe answers within its budget."""
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY_FLEET_COMMS", "pg")
    monkeypatch.setenv(_PG_DSN_ENV, _UNREACHABLE_DSN)
    ctx = _ready_context(tmp_path)

    started = time.monotonic()
    data = check_cluster_readiness(ctx)
    elapsed = time.monotonic() - started

    fleet = data["storage_seam"][StoreId.FLEET_COMMS.value]
    assert fleet["accessible"] is False
    assert fleet["reason"] == "pg_probe_failed"
    assert data["ready"] is False
    assert elapsed < 8.0  # bounded: connect_timeout + deadline, not a hang


@pytest.mark.postgres
def test_live_pg_select_one(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    dsn = (os.environ.get(_PG_DSN_ENV) or "").strip()
    if not dsn:
        pytest.skip(f"{_PG_DSN_ENV} unset/empty — Postgres readiness skipped")
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY_FLEET_COMMS", "pg")
    ctx = _ready_context(tmp_path)

    data = check_cluster_readiness(ctx)
    fleet = data["storage_seam"][StoreId.FLEET_COMMS.value]
    assert fleet["authority"] == "pg"
    assert fleet["accessible"] is True
