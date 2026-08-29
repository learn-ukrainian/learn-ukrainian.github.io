"""Tests for the separate cluster-readiness route (#7365 / Phase 0b ping).

Verifies that /api/cluster/readiness reports storage-seam authority and
store accessibility without claiming multi-host HA in Phase 0. Postgres
authority requires a live ``SELECT 1``, not merely a configured DSN.
"""

from __future__ import annotations

import os
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


def _pg_dsn_or_skip() -> str:
    dsn = (os.environ.get(_PG_DSN_ENV) or "").strip()
    if not dsn:
        pytest.skip(f"{_PG_DSN_ENV} unset/empty — Postgres readiness skipped")
    return dsn


def test_cluster_readiness_endpoint_default(tmp_path: Path) -> None:
    ctx = fixture_context(tmp_path)
    app = api_main.create_app(ctx)
    client = TestClient(app)

    resp = client.get("/api/cluster/readiness")
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "ready"
    assert data["ready"] is True
    assert data["can_serve_cluster_reads"] is True
    assert data["ha_claimed"] is False  # Never claims multi-host HA in Phase 0
    assert "checked_at" in data
    assert "storage_seam" in data

    seam = data["storage_seam"]
    assert StoreId.FLEET_COMMS.value in seam
    assert StoreId.SESSION_STREAMS.value in seam
    assert StoreId.WRITE_OWNERSHIP.value in seam
    assert StoreId.TASK_INDEX.value in seam

    assert seam[StoreId.FLEET_COMMS.value]["authority"] == "sqlite"
    assert seam[StoreId.FLEET_COMMS.value]["accessible"] is True

    assert seam[StoreId.SESSION_STREAMS.value]["authority"] == "sqlite"
    assert seam[StoreId.SESSION_STREAMS.value]["accessible"] is True

    assert seam[StoreId.WRITE_OWNERSHIP.value]["authority"] == "sqlite"
    assert seam[StoreId.WRITE_OWNERSHIP.value]["accessible"] is True

    # task_index has no sqlite backing in Phase 0
    assert seam[StoreId.TASK_INDEX.value]["accessible"] is False


def test_cluster_readiness_plain_python_fallback() -> None:
    data = check_cluster_readiness()
    assert data["ha_claimed"] is False
    assert "storage_seam" in data
    assert "checked_at" in data


def test_cluster_readiness_fails_closed_when_pg_dsn_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY_FLEET_COMMS", "pg")
    monkeypatch.delenv("LEARN_UKRAINIAN_CP_PG_DSN", raising=False)

    ctx = fixture_context(tmp_path)
    app = api_main.create_app(ctx)
    client = TestClient(app)

    resp = client.get("/api/cluster/readiness")
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "unready"
    assert data["ready"] is False
    assert data["can_serve_cluster_reads"] is False
    assert data["ha_claimed"] is False

    seam = data["storage_seam"]
    fleet_status = seam[StoreId.FLEET_COMMS.value]
    assert fleet_status["authority"] == "pg"
    assert fleet_status["accessible"] is False
    assert "reason" in fleet_status


def test_cluster_readiness_with_pg_dsn(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Unreachable DSN must fail closed — DSN presence alone is not ready."""
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY_FLEET_COMMS", "pg")
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_PG_DSN", _UNREACHABLE_DSN)

    ctx = fixture_context(tmp_path)
    app = api_main.create_app(ctx)
    client = TestClient(app)

    resp = client.get("/api/cluster/readiness")
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "unready"
    assert data["ready"] is False
    assert data["can_serve_cluster_reads"] is False
    assert data["ha_claimed"] is False

    seam = data["storage_seam"]
    fleet_status = seam[StoreId.FLEET_COMMS.value]
    assert fleet_status["authority"] == "pg"
    assert fleet_status["accessible"] is False
    assert "reason" in fleet_status
    reason = fleet_status["reason"]
    assert reason == "control-plane store 'fleet_comms' postgres connect failed"
    assert "127.0.0.1" not in reason
    assert "cp_ci" not in reason
    assert _UNREACHABLE_DSN not in reason


@pytest.mark.postgres
def test_cluster_readiness_pg_accessible_after_select_one(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Live DSN: pg-authority store is accessible only after a real SELECT 1."""
    _pg_dsn_or_skip()
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY_FLEET_COMMS", "pg")
    # Leave LEARN_UKRAINIAN_CP_PG_DSN as provided by the environment.

    ctx = fixture_context(tmp_path)
    app = api_main.create_app(ctx)
    client = TestClient(app)

    resp = client.get("/api/cluster/readiness")
    assert resp.status_code == 200
    data = resp.json()

    assert data["ha_claimed"] is False
    seam = data["storage_seam"]
    fleet_status = seam[StoreId.FLEET_COMMS.value]
    assert fleet_status["authority"] == "pg"
    assert fleet_status["accessible"] is True
    assert "reason" not in fleet_status
    # Other stores remain sqlite and keep the overall ready signal usable.
    assert data["ready"] is True
    assert data["can_serve_cluster_reads"] is True


def test_cluster_readiness_cluster_isolation(tmp_path: Path) -> None:
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first_ctx = fixture_context(first_root)
    second_ctx = fixture_context(second_root)

    # Pre-create sqlite DB in first instance
    first_db = storage.sqlite_path(StoreId.FLEET_COMMS, repo_root=first_root)
    first_db.parent.mkdir(parents=True, exist_ok=True)
    first_db.write_bytes(b"")

    first_app = api_main.create_app(first_ctx)
    second_app = api_main.create_app(second_ctx)

    with TestClient(first_app) as first_client, TestClient(second_app) as second_client:
        first_resp = first_client.get("/api/cluster/readiness").json()
        second_resp = second_client.get("/api/cluster/readiness").json()

        assert first_resp["ready"] is True
        assert second_resp["ready"] is True
        assert first_resp["ha_claimed"] is False
        assert second_resp["ha_claimed"] is False
