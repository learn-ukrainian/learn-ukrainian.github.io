"""Tests for GET /api/occupancy (#7050)."""

from __future__ import annotations

import json
import re
import threading
import time

import pytest
from fastapi.testclient import TestClient

from scripts.api import atlas_jobs_router as load_mod
from scripts.api.main import app
from scripts.api.observer_presence import reset_observer_presence
from scripts.api.occupancy import parse_host_id_map
from scripts.api.occupancy_sanitize import occupant as _occupant
from scripts.api.occupancy_sanitize import opaque_host_id as _opaque_host_id
from scripts.api.occupancy_sanitize import safe_field as _safe_field
from scripts.api.occupancy_sanitize import safe_summary as _safe_summary
from scripts.lexicon.runner import atlas_job

client = TestClient(app, raise_server_exceptions=False)

_IP = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
_ALIAS_LEAKS = ("atlas-runner", "hramatka", "vps")
# Fictional canonical keys — never pair real SSH aliases with opaque ids in git.
_PLACEHOLDER_MAP = "job-box=host-job,teach-box=host-teacher"


@pytest.fixture(autouse=True)
def _clear_observer_presence() -> None:
    reset_observer_presence()
    yield
    reset_observer_presence()


@pytest.fixture(autouse=True)
def _non_operational_run_root(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_RUN_ROOT", "/tmp/atlas-run-root")


def _plan(**overrides: object) -> dict:
    base: dict = {
        "schema": "atlas-job.v1",
        "id": "occupancy-job-example",
        "host": "job-box",
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
    load_mod.set_host_load_cache("job-box", fake.host_load("job-box"))
    load_mod.set_host_load_cache("teach-box", fake.host_load("teach-box"))


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


def test_occupancy_awaits_missing_expired_and_fresh_load_probes(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    fake = atlas_job.FakeHostAdapter()
    atlas_job.set_host_adapter(fake)
    try:
        load_mod.clear_host_load_cache()
        expired = fake.host_load("job-box")
        expired["cpu_count"] = 1
        load_mod.set_host_load_cache(
            "job-box",
            expired,
            mono_ts=time.monotonic() - load_mod.HOST_LOAD_MAX_STALE_S - 1.0,
        )

        resp = client.get("/api/occupancy")
        assert resp.status_code == 200
        hosts = resp.json()["hosts"]
        assert hosts["host-job"]["status"] == "fresh"
        assert hosts["host-job"]["cpu_count"] == 4
        assert hosts["host-teacher"]["status"] == "fresh"
        assert hosts["host-teacher"]["cpu_count"] == 4

        cached = fake.host_load("job-box")
        cached["cpu_count"] = 1
        load_mod.set_host_load_cache("job-box", cached)
        fresh_resp = client.get("/api/occupancy?host_id=host-job&fresh=true")
        assert fresh_resp.status_code == 200
        fresh_host = fresh_resp.json()["hosts"]["host-job"]
        assert fresh_host["status"] == "fresh"
        assert fresh_host["cpu_count"] == 4
    finally:
        atlas_job.set_host_adapter(None)
        load_mod.clear_host_load_cache()


def test_occupancy_unavailable_has_no_metrics_or_ssh_text(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    fake = atlas_job.FakeHostAdapter()
    atlas_job.set_host_adapter(fake)
    try:
        original_host_load = fake.host_load

        def host_load(host: str) -> dict:
            if host == "teach-box":
                raise ConnectionError("unreachable")
            return original_host_load(host)

        monkeypatch.setattr(fake, "host_load", host_load)
        load_mod.clear_host_load_cache()
        load_mod.set_host_load_cache("job-box", fake.host_load("job-box"))
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
                "host": "job-box",
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
        assert resp.json()["detail"] == "unknown host_id"
        text = json.dumps(resp.json())
        for alias in _ALIAS_LEAKS:
            assert alias not in text
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
            "job-box",
            fake.host_load("job-box"),
            mono_ts=now_mono - 60.0,
        )
        load_mod.set_host_load_cache(
            "teach-box",
            fake.host_load("teach-box"),
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


def test_occupancy_heartbeat_boundary_stays_fresh_while_probe_runs(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    fake = atlas_job.FakeHostAdapter()
    atlas_job.set_host_adapter(fake)
    probe_started = threading.Event()
    release_probe = threading.Event()
    original_host_load = fake.host_load

    def host_load(host: str) -> dict:
        if host == "job-box":
            probe_started.set()
            assert release_probe.wait(timeout=1.0)
        return original_host_load(host)

    monkeypatch.setattr(fake, "host_load", host_load)
    try:
        load_mod.clear_host_load_cache()
        load_mod.set_host_load_cache(
            "job-box",
            original_host_load("job-box"),
            mono_ts=time.monotonic() - 31.0,
        )
        load_mod.set_host_load_cache(
            "teach-box",
            original_host_load("teach-box"),
            mono_ts=time.monotonic() - 10.0,
        )
        resp = client.get("/api/occupancy")
        assert resp.status_code == 200
        data = resp.json()
        assert data["hosts"]["host-job"]["status"] == "fresh"
        assert 30.0 <= data["hosts"]["host-job"]["age_seconds"] <= 33.0
        assert data["hosts"]["host-teacher"]["status"] == "fresh"
        assert probe_started.wait(timeout=1.0)
    finally:
        release_probe.set()
        atlas_job.set_host_adapter(None)
        load_mod.clear_host_load_cache()


def test_parse_host_id_map_drops_non_opaque_values() -> None:
    parsed = parse_host_id_map(
        "job-box=host-job,teach-box=atlas-runner,bad=1.2.3.4,also=vps,ok=host-teacher"
    )
    assert parsed == {"job-box": "host-job", "ok": "host-teacher"}
    assert not _opaque_host_id("atlas-runner")
    assert not _opaque_host_id("hramatka")
    assert not _opaque_host_id("vps")
    assert not _opaque_host_id("10.0.0.1")
    assert not _opaque_host_id("host.example")
    assert not _opaque_host_id("cloud-observer")
    assert _opaque_host_id("host-job")


def test_safe_field_drops_aliases_addresses_and_fqdn() -> None:
    assert _safe_field("cursor") == "cursor"
    assert _safe_field("occupancy-job-example", role="task_id") == "occupancy-job-example"
    assert _safe_field("v2.1-reenrich", role="task_id") == "v2.1-reenrich"
    assert _safe_field("hramatka", role="epic") == "hramatka"
    for leaked in (
        "hramatka",
        "atlas-runner",
        "vps",
        "atlas-runner-reenrich-3",
        "hramatka-drive",
        "vps-2",
        "10.0.0.1",
        "2001:db8::1",
        "box.example.com",
        "/tmp/hidden/job",
    ):
        assert _safe_field(leaked) is None
        assert _safe_field(leaked, role="task_id") is None
    occupant = _occupant(
        kind="job",
        agent="hramatka",
        task_id="v2.1-reenrich",
        epic="hramatka",
    )
    assert occupant == {
        "kind": "job",
        "agent": None,
        "task_id": "v2.1-reenrich",
        "epic": "hramatka",
    }
    assert _occupant(kind="job", task_id="atlas-runner-reenrich-3") is None
    assert _safe_field("box.example.com.", role="task_id") is None
    assert _safe_field("v2.1-reenrich", role="task_id") == "v2.1-reenrich"


def test_safe_summary_drops_paths_secrets_and_aliases() -> None:
    assert _safe_summary("tunneled Monitor observer sweep") == "tunneled Monitor observer sweep"
    assert _safe_summary("  spaced   words  ") == "spaced words"
    for leaked in (
        "talk to atlas-runner",
        "10.0.0.1 sweep",
        "/etc/passwd",
        "notes/etc/passwd",
        "box.example.com",
        "box.example.com!",
        "pid=12 reserved_ram_mb=256",
        "token=abc123",
        "bearer secret value",
        "user@host",
    ):
        assert _safe_summary(leaked) is None
    assert _occupant(kind="observer", agent="grok-bot", task_id="7061") is None
    occupant = _occupant(
        kind="observer",
        agent="grok-bot",
        task_id="7061",
        status="working",
    )
    assert occupant == {
        "kind": "observer",
        "agent": "grok-bot",
        "task_id": "7061",
        "epic": None,
        "status": "working",
    }
    assert "summary" not in occupant
