"""Tests for /api/atlas-jobs Monitor facade."""

from __future__ import annotations

import json
import re
import time

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from scripts.api import atlas_jobs_router as router_mod
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


def test_submit_allows_hramatka(_isolate: atlas_job.FakeHostAdapter) -> None:
    resp = client.post(
        "/api/atlas-jobs/submit",
        json={"plan": _plan(host="hramatka"), "dry_run": True},
    )
    assert resp.status_code == 200
    assert resp.json()["exit_code"] == 0


def test_submit_rejects_unknown_host(_isolate: atlas_job.FakeHostAdapter) -> None:
    resp = client.post(
        "/api/atlas-jobs/submit",
        json={"plan": _plan(host="mystery-host"), "dry_run": True},
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


def test_api_rejects_path_injection_job_id(
    tmp_path, _isolate: atlas_job.FakeHostAdapter, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Unsafe job_id must 400 before any Path join; no writes outside registry."""
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    outside = tmp_path.parent / "escape-marker"
    if outside.exists():
        outside.unlink()

    # Single-segment unsafe tokens reach the atlas-jobs handler (encoded
    # ``../`` is often normalized by the ASGI stack before routing).
    for bad in ("..escape", ".hidden", "-leading-dash", "has%20space"):
        get_resp = client.get(f"/api/atlas-jobs/{bad}")
        assert get_resp.status_code == 400, (bad, get_resp.status_code, get_resp.text)
        close_resp = client.post(
            f"/api/atlas-jobs/{bad}/close",
            json={"summary": {}, "skip_pull": True, "skip_restic": True},
        )
        assert close_resp.status_code == 400, (bad, close_resp.status_code, close_resp.text)

    # Explicit path-param values that CodeQL flags (handler-level, not URL routing).
    from scripts.api import atlas_jobs_router as router_mod

    for bad in ("../../tmp", "../escape", "/etc/passwd"):
        with pytest.raises(HTTPException) as excinfo:
            router_mod.job_status(bad)
        assert excinfo.value.status_code == 400
        with pytest.raises(HTTPException) as excinfo:
            router_mod.close_job(bad, router_mod.CloseBody(skip_pull=True, skip_restic=True))
        assert excinfo.value.status_code == 400

    assert not outside.exists()
    assert list(tmp_path.iterdir()) == []


def test_load_and_results_not_swallowed_by_job_id(
    _isolate: atlas_job.FakeHostAdapter,
) -> None:
    load_resp = client.get("/api/atlas-jobs/load")
    assert load_resp.status_code == 200
    assert load_resp.json()["schema"] == "atlas-jobs-load.v1"

    results_resp = client.get("/api/atlas-jobs/results")
    assert results_resp.status_code == 200
    assert "results" in results_resp.json()


def test_load_endpoint_shape_and_cache(
    _isolate: atlas_job.FakeHostAdapter,
) -> None:
    router_mod.clear_host_load_cache()
    # Populate fresh cache for both hosts
    router_mod.set_host_load_cache(
        "atlas-runner",
        _isolate.host_load("atlas-runner"),
    )
    router_mod.set_host_load_cache(
        "hramatka",
        _isolate.host_load("hramatka"),
    )

    resp = client.get("/api/atlas-jobs/load")
    assert resp.status_code == 200
    assert resp.headers.get("cache-control") == "no-store"
    data = resp.json()
    assert data["schema"] == "atlas-jobs-load.v1"
    assert "observed_at" in data
    assert sorted(data["hosts"].keys()) == ["atlas-runner", "hramatka"]

    for host_name in ("atlas-runner", "hramatka"):
        host_info = data["hosts"][host_name]
        assert host_info["status"] == "fresh"
        assert isinstance(host_info["age_seconds"], (int, float))
        assert "observed_at" in host_info
        assert host_info["cpu_count"] == 4
        assert host_info["loadavg"] == [0.15, 0.22, 0.18]
        assert host_info["mem"]["total_bytes"] == 16 * 1024 * 1024 * 1024
        assert host_info["mem"]["available_bytes"] == 8 * 1024 * 1024 * 1024
        assert host_info["mem"]["pct"] == 50.0
        assert host_info["disk"]["available_bytes"] == 50 * 1024 * 1024 * 1024
        assert "total_bytes" in host_info["disk"]
        assert "pct" in host_info["disk"]
        assert host_info["job_unit"]["active_count"] == 0
        assert host_info["job_unit"]["job_id"] is None
        assert host_info["job_unit"]["state"] is None


def test_load_endpoint_host_filter_and_vps_normalization(
    _isolate: atlas_job.FakeHostAdapter,
) -> None:
    router_mod.clear_host_load_cache()
    router_mod.set_host_load_cache("hramatka", _isolate.host_load("hramatka"))
    router_mod.set_host_load_cache("atlas-runner", _isolate.host_load("atlas-runner"))

    # ?host=vps normalizes to hramatka and never emits 'vps' in keys
    resp_vps = client.get("/api/atlas-jobs/load?host=vps")
    assert resp_vps.status_code == 200
    data_vps = resp_vps.json()
    assert list(data_vps["hosts"].keys()) == ["hramatka"]
    assert "vps" not in data_vps["hosts"]

    resp_runner = client.get("/api/atlas-jobs/load?host=atlas-runner")
    assert resp_runner.status_code == 200
    assert list(resp_runner.json()["hosts"].keys()) == ["atlas-runner"]

    resp_unknown = client.get("/api/atlas-jobs/load?host=unknown-host")
    assert resp_unknown.status_code == 400


def test_load_endpoint_ip_sanitization_and_forbidden_fields(
    _isolate: atlas_job.FakeHostAdapter,
) -> None:
    router_mod.clear_host_load_cache()
    router_mod.set_host_load_cache("atlas-runner", _isolate.host_load("atlas-runner"))
    router_mod.set_host_load_cache("hramatka", _isolate.host_load("hramatka"))

    resp = client.get("/api/atlas-jobs/load")
    assert resp.status_code == 200
    text = resp.text

    # IP address pattern
    ip_pattern = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
    assert ip_pattern.findall(text) == []

    # Check that forbidden fields are absent
    data = resp.json()
    for host_data in data["hosts"].values():
        forbidden = {
            "pid", "main_pid", "user", "port", "hostname", "ip",
            "ssh", "stderr", "logs", "config", "path", "workdir",
        }
        assert not any(k.lower() in forbidden for k in host_data)


def test_load_endpoint_dead_host_isolation(
    _isolate: atlas_job.FakeHostAdapter,
) -> None:
    router_mod.clear_host_load_cache()
    # atlas-runner has fresh cache, hramatka has no cache / failed
    router_mod.set_host_load_cache("atlas-runner", _isolate.host_load("atlas-runner"))

    resp = client.get("/api/atlas-jobs/load")
    assert resp.status_code == 200
    data = resp.json()
    assert data["hosts"]["atlas-runner"]["status"] == "fresh"
    assert data["hosts"]["hramatka"]["status"] == "unavailable"
    assert data["hosts"]["hramatka"]["error"] == "unreachable"
    # Never zero-fill healthy metrics on unavailable host
    assert "cpu_count" not in data["hosts"]["hramatka"]
    assert "mem" not in data["hosts"]["hramatka"]


def test_load_stale_while_revalidate_cache_lifecycle(
    _isolate: atlas_job.FakeHostAdapter,
) -> None:
    router_mod.clear_host_load_cache()
    now_mono = time.monotonic()

    # 1. Fresh cache: age <= 30s
    router_mod.set_host_load_cache(
        "atlas-runner",
        _isolate.host_load("atlas-runner"),
        mono_ts=now_mono - 10.0,
    )
    entry = router_mod._get_host_load_entry("atlas-runner")
    assert entry["status"] == "fresh"
    assert 9.0 <= entry["age_seconds"] <= 12.0

    # 2. Stale cache: 30s < age <= 300s
    router_mod.set_host_load_cache(
        "atlas-runner",
        _isolate.host_load("atlas-runner"),
        mono_ts=now_mono - 60.0,
    )
    entry_stale = router_mod._get_host_load_entry("atlas-runner")
    assert entry_stale["status"] == "stale"
    assert 59.0 <= entry_stale["age_seconds"] <= 62.0
    assert "cpu_count" in entry_stale

    # 3. Expired cache: age > 300s -> unavailable
    router_mod.set_host_load_cache(
        "atlas-runner",
        _isolate.host_load("atlas-runner"),
        mono_ts=now_mono - 350.0,
    )
    entry_expired = router_mod._get_host_load_entry("atlas-runner")
    assert entry_expired["status"] == "unavailable"
    assert entry_expired["error"] == "unreachable"

    # 4. ?fresh=true with cached entry returns the cached entry immediately
    router_mod.set_host_load_cache(
        "atlas-runner",
        _isolate.host_load("atlas-runner"),
        mono_ts=now_mono - 5.0,
    )
    resp_fresh = client.get("/api/atlas-jobs/load?fresh=true&host=atlas-runner")
    assert resp_fresh.status_code == 200
    data_fresh = resp_fresh.json()
    assert data_fresh["hosts"]["atlas-runner"]["status"] == "fresh"


def test_results_allowlist_and_sorting(
    tmp_path, _isolate: atlas_job.FakeHostAdapter, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))

    # Create two fixture result files with raw / non-allowlisted fields
    receipt1 = {
        "schema": "atlas-job-result.v1",
        "id": "job-001",
        "host": "atlas-runner",
        "kind": "reenrich",
        "state": "succeeded",
        "closed_at": "2026-08-17T10:00:00Z",
        "issue": 6867,
        "denominator": 10,
        "delivery": "ok",
        "pulled": True,
        "summary": {
            "targets": 100,
            "filled_translation": 85,
            "circuit_breaker_tripped": False,
            "extra_raw_metric": "ignore_me",
        },
        "raw_forbidden_workdir": "/home/ops/workdir",
        "plan_sha256": "abcdef123456",
        "backup": {"attempted": True, "ok": True},
    }
    receipt2 = {
        "schema": "atlas-job-result.v1",
        "id": "job-002",
        "host": "vps",
        "kind": "reenrich",
        "state": "failed",
        "closed_at": "2026-08-17T12:00:00Z",
        "issue": 6876,
        "denominator": 20,
        "delivery": "failed",
        "pulled": False,
        "summary": {
            "targets": 50,
            "filled_translation": 0,
            "circuit_breaker_tripped": True,
        },
        "raw_forbidden_workdir": "/home/ops/workdir2",
    }

    (tmp_path / "job-001.result.json").write_text(json.dumps(receipt1), encoding="utf-8")
    (tmp_path / "job-002.result.json").write_text(json.dumps(receipt2), encoding="utf-8")

    resp = client.get("/api/atlas-jobs/results")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 2
    assert data["total"] == 2

    # Newest-first by (closed_at, id): job-002 (12:00:00Z) before job-001 (10:00:00Z)
    assert data["results"][0]["id"] == "job-002"
    assert data["results"][0]["host"] == "hramatka"  # normalized
    assert data["results"][0]["circuit_breaker_tripped"] is True
    assert data["results"][1]["id"] == "job-001"
    assert data["results"][1]["targets"] == 100
    assert data["results"][1]["filled_translation"] == 85

    expected_keys = {
        "id", "host", "kind", "state", "closed_at", "issue",
        "denominator", "delivery", "pulled", "targets",
        "filled_translation", "circuit_breaker_tripped",
    }
    for item in data["results"]:
        assert set(item.keys()) == expected_keys
        assert "raw_forbidden_workdir" not in item
        assert "plan_sha256" not in item
        assert "backup" not in item
        assert "summary" not in item


def test_results_pagination_and_filters(
    tmp_path, _isolate: atlas_job.FakeHostAdapter, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))

    for i in range(1, 6):
        job_id = f"job-{i:03d}"
        receipt = {
            "schema": "atlas-job-result.v1",
            "id": job_id,
            "host": "atlas-runner" if i % 2 == 1 else "hramatka",
            "kind": "reenrich",
            "state": "succeeded" if i <= 3 else "failed",
            "closed_at": f"2026-08-17T{10 + i:02d}:00:00Z",
            "issue": 6867,
            "denominator": 10,
            "delivery": "ok",
            "pulled": True,
            "summary": {
                "targets": 10 * i,
                "filled_translation": 8 * i,
                "circuit_breaker_tripped": False,
            },
        }
        (tmp_path / f"{job_id}.result.json").write_text(json.dumps(receipt), encoding="utf-8")

    # Limit = 2 pagination
    page1 = client.get("/api/atlas-jobs/results?limit=2")
    assert page1.status_code == 200
    p1_data = page1.json()
    assert p1_data["count"] == 2
    assert p1_data["total"] == 5
    assert p1_data["results"][0]["id"] == "job-005"
    assert p1_data["results"][1]["id"] == "job-004"
    assert p1_data["next_cursor"] is not None

    # Fetch next page using cursor
    cursor = p1_data["next_cursor"]
    page2 = client.get(f"/api/atlas-jobs/results?limit=2&cursor={cursor}")
    assert page2.status_code == 200
    p2_data = page2.json()
    assert p2_data["count"] == 2
    assert p2_data["total"] == 5
    assert p2_data["results"][0]["id"] == "job-003"
    assert p2_data["results"][1]["id"] == "job-002"
    assert p2_data["next_cursor"] is not None

    # Filter by host (including vps alias)
    vps_resp = client.get("/api/atlas-jobs/results?host=vps")
    assert vps_resp.status_code == 200
    vps_data = vps_resp.json()
    assert vps_data["count"] == 2
    assert all(r["host"] == "hramatka" for r in vps_data["results"])

    # Filter by state
    failed_resp = client.get("/api/atlas-jobs/results?state=failed")
    assert failed_resp.status_code == 200
    failed_data = failed_resp.json()
    assert failed_data["count"] == 2
    assert all(r["state"] == "failed" for r in failed_data["results"])

