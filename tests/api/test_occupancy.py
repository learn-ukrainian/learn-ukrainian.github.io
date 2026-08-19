"""Tests for GET /api/occupancy (#7050)."""

from __future__ import annotations

import json
import re
import time

from fastapi.testclient import TestClient

from scripts.api import atlas_jobs_router as load_mod
from scripts.api.main import app
from scripts.lexicon.runner import atlas_job

client = TestClient(app, raise_server_exceptions=False)

_IP = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
_ALIAS_LEAKS = ("atlas-runner", "hramatka", "vps")
_PLACEHOLDER_MAP = "atlas-runner=host-job,hramatka=host-teacher"


def _plan(**overrides: object) -> dict:
    base: dict = {
        "schema": "atlas-job.v1",
        "id": "occupancy-job-example",
        "host": "atlas-runner",
        "kind": "reenrich",
        "args": ["--target", "missing-translation"],
        "pointer_write": False,
        "result_sink": "git",
        "denominator": 3,
        "issue": 7050,
        "epic": "atlas",
        "success": {"circuit_breaker": False, "min_filled": 0},
    }
    base.update(overrides)
    return base


def _warm_load(fake: atlas_job.FakeHostAdapter) -> None:
    load_mod.clear_host_load_cache()
    load_mod.set_host_load_cache("atlas-runner", fake.host_load("atlas-runner"))
    load_mod.set_host_load_cache("hramatka", fake.host_load("hramatka"))


def test_occupancy_empty_without_opaque_map(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    monkeypatch.delenv("MONITOR_OCCUPANCY_HOST_IDS", raising=False)
    fake = atlas_job.FakeHostAdapter()
    atlas_job.set_host_adapter(fake)
    try:
        _warm_load(fake)
        resp = client.get("/api/occupancy")
        assert resp.status_code == 200
        data = resp.json()
        assert data["schema"] == "monitor-occupancy.v1"
        assert data["hosts"] == {}
        text = resp.text
        for alias in _ALIAS_LEAKS:
            assert alias not in text
    finally:
        atlas_job.set_host_adapter(None)
        load_mod.clear_host_load_cache()


def test_occupancy_shape_uses_placeholders(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    fake = atlas_job.FakeHostAdapter()
    atlas_job.set_host_adapter(fake)
    try:
        _warm_load(fake)
        resp = client.get("/api/occupancy")
        assert resp.status_code == 200
        assert resp.headers.get("cache-control") == "no-store"
        data = resp.json()
        assert data["schema"] == "monitor-occupancy.v1"
        assert sorted(data["hosts"].keys()) == ["host-job", "host-teacher"]
        for host_id, host in data["hosts"].items():
            assert host["host_id"] == host_id
            assert host["status"] == "fresh"
            assert "cpu_count" in host
            assert "loadavg" in host
            assert "mem" in host
            assert "disk" in host
            assert isinstance(host["occupants"], list)
            assert "error" not in host
        text = json.dumps(data)
        assert _IP.findall(text) == []
        for alias in _ALIAS_LEAKS:
            assert alias not in text
        for host in data["hosts"].values():
            forbidden = {
                "pid",
                "main_pid",
                "user",
                "port",
                "hostname",
                "ip",
                "ssh",
                "stderr",
                "logs",
                "path",
                "workdir",
            }
            assert not any(k.lower() in forbidden for k in host)
    finally:
        atlas_job.set_host_adapter(None)
        load_mod.clear_host_load_cache()


def test_occupancy_unavailable_has_no_metrics_or_ssh_text(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    fake = atlas_job.FakeHostAdapter()
    atlas_job.set_host_adapter(fake)
    try:
        load_mod.clear_host_load_cache()
        load_mod.set_host_load_cache("atlas-runner", fake.host_load("atlas-runner"))
        resp = client.get("/api/occupancy")
        assert resp.status_code == 200
        data = resp.json()
        dead = data["hosts"]["host-teacher"]
        assert dead["status"] == "unavailable"
        assert dead["error"] == "unreachable"
        assert "cpu_count" not in dead
        assert "mem" not in dead
        assert "ssh" not in json.dumps(dead).lower()
        live = data["hosts"]["host-job"]
        assert live["status"] == "fresh"
        assert "cpu_count" in live
    finally:
        atlas_job.set_host_adapter(None)
        load_mod.clear_host_load_cache()


def test_occupancy_occupants_from_registry_and_job_unit(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    fake = atlas_job.FakeHostAdapter()
    atlas_job.set_host_adapter(fake)
    try:
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
        fake.units = [
            {
                "name": atlas_job.unit_name(plan["id"]),
                "active": "active",
                "sub": "running",
            }
        ]
        _warm_load(fake)
        resp = client.get("/api/occupancy?host_id=host-job")
        assert resp.status_code == 200
        data = resp.json()
        assert list(data["hosts"].keys()) == ["host-job"]
        occupants = data["hosts"]["host-job"]["occupants"]
        assert occupants == [
            {
                "kind": "job",
                "agent": None,
                "task_id": "occupancy-job-example",
                "epic": "atlas",
            }
        ]
        kinds = {row["kind"] for row in occupants}
        assert kinds <= {"driver", "worker", "job", "service"}
        text = resp.text
        for alias in _ALIAS_LEAKS:
            assert alias not in text
    finally:
        atlas_job.set_host_adapter(None)
        load_mod.clear_host_load_cache()


def test_occupancy_rejects_unknown_host_id(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    fake = atlas_job.FakeHostAdapter()
    atlas_job.set_host_adapter(fake)
    try:
        _warm_load(fake)
        resp = client.get("/api/occupancy?host_id=atlas-runner")
        assert resp.status_code == 400
        assert "atlas-runner" not in resp.text or resp.json()["detail"] == "unknown host_id"
        assert resp.json()["detail"] == "unknown host_id"
    finally:
        atlas_job.set_host_adapter(None)
        load_mod.clear_host_load_cache()


def test_occupancy_stale_while_revalidate_reuse(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    fake = atlas_job.FakeHostAdapter()
    atlas_job.set_host_adapter(fake)
    try:
        load_mod.clear_host_load_cache()
        now_mono = time.monotonic()
        load_mod.set_host_load_cache(
            "atlas-runner",
            fake.host_load("atlas-runner"),
            mono_ts=now_mono - 60.0,
        )
        load_mod.set_host_load_cache(
            "hramatka",
            fake.host_load("hramatka"),
            mono_ts=now_mono - 10.0,
        )
        resp = client.get("/api/occupancy")
        assert resp.status_code == 200
        data = resp.json()
        assert data["hosts"]["host-job"]["status"] == "stale"
        assert "cpu_count" in data["hosts"]["host-job"]
        assert data["hosts"]["host-teacher"]["status"] == "fresh"
    finally:
        atlas_job.set_host_adapter(None)
        load_mod.clear_host_load_cache()
