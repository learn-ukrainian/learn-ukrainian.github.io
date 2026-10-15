"""``GET /api/ops/v1/test-slots``: the host test-slot pool, read-only and path-free (#10662)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from scripts.api.monitor_context import fixture_context
from scripts.api.ops_router import router
from scripts.api.route_contracts import contract_for_route
from scripts.common import test_slots

ROUTE = "/api/ops/v1/test-slots"


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv(test_slots.ENABLE_ENV, "on")
    monkeypatch.setenv(test_slots.DIR_ENV, str(tmp_path / "pool"))
    monkeypatch.setenv(test_slots.COUNT_ENV, "3")
    monkeypatch.delenv(test_slots.HOLDER_ENV, raising=False)
    app = FastAPI()
    app.state.ctx = fixture_context(tmp_path)
    app.include_router(router, prefix="/api/ops")
    return TestClient(app)


def test_route_reports_holders_by_task_without_paths(client: TestClient, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv(test_slots.TASK_ENV, "impl-7")
    with test_slots.acquire(2, kind="gate"):
        response = client.get(ROUTE)
    assert response.status_code == 200
    payload = response.json()
    assert payload["schema"] == "test-slots.status.v1" and payload["enabled"] is True
    assert (payload["pool_size"], payload["slots_in_use"], payload["slots_free"]) == (3, 2, 1)
    assert payload["queue_depth"] == 0
    [holder] = payload["holders"]
    assert (holder["task_id"], holder["kind"], holder["slots"], holder["pid"]) == ("impl-7", "gate", 2, os.getpid())
    assert str(tmp_path) not in json.dumps(payload) and "/" not in json.dumps(payload)
    assert client.get(ROUTE).json()["slots_in_use"] == 0


def test_route_reports_a_missing_or_disabled_pool_without_creating_it(
    client: TestClient, tmp_path: Path, monkeypatch
) -> None:
    payload = client.get(ROUTE).json()
    assert (payload["enabled"], payload["pool_exists"], payload["queue_depth"]) == (True, False, 0)
    monkeypatch.setenv(test_slots.ENABLE_ENV, "off")
    assert client.get(ROUTE).json()["enabled"] is False
    monkeypatch.setenv(test_slots.ENABLE_ENV, "maybe")
    broken = client.get(ROUTE)
    assert broken.status_code == 200 and broken.json()["error"]["reason"] == "invalid_configuration"
    assert not (tmp_path / "pool").exists()


def test_route_has_a_read_only_host_affine_contract() -> None:
    contract = contract_for_route(ROUTE)
    assert contract is not None and contract.pattern == ROUTE and contract.match == "exact"
    assert contract.mutates is False and contract.locality == "host_affine"
    assert contract.response_schema_version == "test-slots.status.v1"
