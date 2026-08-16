"""Tests for /api/atlas-jobs Monitor facade."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from scripts.api.main import app
from scripts.lexicon.runner import atlas_job

client = TestClient(app, raise_server_exceptions=False)


def _plan(**overrides: object) -> dict:
    base: dict = {
        "schema": "atlas-job.v1",
        "id": "api-job-example",
        "host": "atlas-runner",
        "kind": "reenrich",
        "args": ["--target", "missing-translation"],
        "pointer_write": False,
        "result_sink": "git",
        "denominator": 3,
        "issue": 6867,
        "success": {"circuit_breaker": False, "min_filled": 0},
    }
    base.update(overrides)
    return base


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    fake = atlas_job.FakeHostAdapter()
    atlas_job.set_host_adapter(fake)
    yield fake
    atlas_job.set_host_adapter(None)


def test_list_and_health(_isolate: atlas_job.FakeHostAdapter) -> None:
    health = client.get("/api/atlas-jobs/health")
    assert health.status_code == 200
    assert health.json()["ok"] is True
    listed = client.get("/api/atlas-jobs")
    assert listed.status_code == 200
    assert listed.json()["count"] == 0


def test_submit_dry_run_via_api(_isolate: atlas_job.FakeHostAdapter) -> None:
    resp = client.post("/api/atlas-jobs/submit", json={"plan": _plan(), "dry_run": True})
    assert resp.status_code == 200
    assert resp.json()["exit_code"] == 0


def test_submit_rejects_hramatka(_isolate: atlas_job.FakeHostAdapter) -> None:
    resp = client.post(
        "/api/atlas-jobs/submit",
        json={"plan": _plan(host="hramatka"), "dry_run": True},
    )
    assert resp.status_code == 400


def test_close_empty_summary_fail_closed(_isolate: atlas_job.FakeHostAdapter) -> None:
    plan = _plan()
    atlas_job.save_registry(
        {
            "id": plan["id"],
            "state": "running",
            "host": "atlas-runner",
            "kind": "reenrich",
            "unit": atlas_job.unit_name(plan["id"]),
            "workdir": atlas_job.work_dir_for(plan["id"], plan),
            "result_sink": "git",
            "issue": plan["issue"],
            "plan": plan,
        }
    )
    resp = client.post(
        f"/api/atlas-jobs/{plan['id']}/close",
        json={"summary": {}, "skip_pull": True, "skip_restic": True},
    )
    assert resp.status_code == 409
    detail = resp.json()["detail"]
    assert detail["result"]["state"] == "needs_finalize"


def test_status_reconciles(
    _isolate: atlas_job.FakeHostAdapter,
) -> None:
    plan = _plan()
    workdir = atlas_job.work_dir_for(plan["id"], plan)
    atlas_job.save_registry(
        {
            "id": plan["id"],
            "state": "running",
            "host": "atlas-runner",
            "kind": "reenrich",
            "unit": atlas_job.unit_name(plan["id"]),
            "workdir": workdir,
            "resume": "checkpoint",
            "result_sink": "git",
            "issue": plan["issue"],
            "plan": plan,
        }
    )
    _isolate.exit_status_by_workdir[workdir] = {
        "service_result": "success",
        "exit_status": "0",
    }
    resp = client.get(f"/api/atlas-jobs/{plan['id']}")
    assert resp.status_code == 200
    assert resp.json()["job"]["state"] == "needs_finalize"
