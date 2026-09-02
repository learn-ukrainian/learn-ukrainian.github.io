"""Tests for GET /api/occupancy (#7050)."""

from __future__ import annotations

import json
import re
import threading
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agents_extensions.shared.session_streams.db import SessionStreamDatabase
from agents_extensions.shared.session_streams.model import LeaseHolder
from agents_extensions.shared.session_streams.store import SessionStreamStore
from scripts.api import atlas_jobs_router as load_mod
from scripts.api.main import app
from scripts.api.observer_presence import (
    PRESENCE_FRESHNESS_SECONDS,
    PresenceRequest,
    list_live,
    reset_observer_presence,
    upsert_presence,
)
from scripts.api.occupancy import MAC_OPERATOR_HOST_ID, parse_host_id_map
from scripts.api.occupancy_local import write_marker
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


@pytest.fixture(autouse=True)
def _isolate_local_occupants(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    marker_root = tmp_path / "no-markers"
    marker_root.mkdir()
    monkeypatch.setenv("MONITOR_OCCUPANCY_MARKERS", str(marker_root))
    monkeypatch.delenv("MONITOR_OCCUPANCY_DRIVER_HOST_ID", raising=False)
    monkeypatch.delenv("MONITOR_OCCUPANCY_FOUNDRY_HOST_ID", raising=False)
    monkeypatch.delenv("ATLAS_JOB_SELF_HOST", raising=False)
    monkeypatch.setattr(
        "scripts.api.occupancy_local.session_streams_db_path",
        lambda: tmp_path / "missing-session-streams.sqlite3",
    )


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


def _open_lease(db_path: Path, *, ttl_seconds: int = 600) -> None:
    store = SessionStreamStore(SessionStreamDatabase(db_path))
    store.open_session(
        stream_id="epic:7139",
        holder=LeaseHolder(
            agent="claude",
            harness="claude-code",
            instance_id="runtime-occupancy",
            process_id=41001,
            task_id="occupancy-driver",
        ),
        lineage_id="lineage-occupancy",
        ttl_seconds=ttl_seconds,
        session_id="session-occupancy",
        lease_id="lease-occupancy",
    )


def _assert_quiet_mac_row(host: dict) -> None:
    assert host["host_id"] == MAC_OPERATOR_HOST_ID
    assert host["status"] == "unavailable"
    assert host["error"] == "unreachable"
    assert host["occupants"] == []
    assert host["occupant_count"] == 0
    assert host["ai_seats"] == []
    assert host["idle_or_empty"] is False
    assert "cpu_count" not in host
    assert "mem" not in host
    assert "loadavg" not in host


def test_occupancy_enumerates_both_default_hosts_without_opaque_map(tmp_path, monkeypatch) -> None:
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
        assert sorted(data["hosts"].keys()) == ["host-teacher", "mac-operator"]
        for host_id in ("host-teacher",):
            entry = data["hosts"][host_id]
            assert entry["host_id"] == host_id
            assert entry["status"] == "unavailable"
            assert entry["error"] == "unreachable"
            assert entry["idle_or_empty"] is False
            assert entry["occupants"] == []
            assert entry["occupant_count"] == 0
            assert entry["ai_seats"] == []
            assert "cpu_count" not in entry
            assert "mem" not in entry
            assert set(entry["burn_sources"]) == {
                "atlas_job",
                "driver",
                "foundry",
                "service",
                "observer",
            }
        _assert_quiet_mac_row(data["hosts"]["mac-operator"])
        text = resp.text
        for alias in _ALIAS_LEAKS:
            assert alias not in text
        assert "host-job" not in data["hosts"]
    finally:
        atlas_job.set_host_adapter(None)
        load_mod.clear_host_load_cache()


def test_occupancy_default_glance_keeps_quiet_mac(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    monkeypatch.delenv("MONITOR_OCCUPANCY_HOST_IDS", raising=False)
    fake = atlas_job.FakeHostAdapter()
    atlas_job.set_host_adapter(fake)
    try:
        _warm_load(fake)
        assert list_live() == []
        resp = client.get("/api/occupancy")
        assert resp.status_code == 200
        data = resp.json()
        assert "mac-operator" in data["hosts"]
        _assert_quiet_mac_row(data["hosts"]["mac-operator"])
        assert data["hosts"]["mac-operator"]["burn_state"] == "unknown"
    finally:
        atlas_job.set_host_adapter(None)
        load_mod.clear_host_load_cache()


def test_occupancy_default_glance_merges_live_mac_observer(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    monkeypatch.delenv("MONITOR_OCCUPANCY_HOST_IDS", raising=False)
    fake = atlas_job.FakeHostAdapter()
    atlas_job.set_host_adapter(fake)
    try:
        _warm_load(fake)
        upsert_presence(
            PresenceRequest.model_validate(
                {
                    "agent": "cursor",
                    "kind": "observer",
                    "task_id": "7104",
                    "status": "working",
                    "host_id": "mac-operator",
                    "instance_id": "gui",
                }
            )
        )
        resp = client.get("/api/occupancy")
        assert resp.status_code == 200
        data = resp.json()
        assert sorted(data["hosts"].keys()) == ["host-teacher", "mac-operator"]
        host = data["hosts"]["mac-operator"]
        assert host["status"] == "unavailable"
        assert host["error"] == "unreachable"
        assert host["occupants"] == [
            {
                "kind": "observer",
                "agent": "cursor",
                "task_id": "7104",
                "epic": None,
                "status": "working",
                "instance_id": "gui",
            }
        ]
        assert host["occupant_count"] == 1
        assert host["ai_seats"] == ["cursor"]
        assert host["idle_or_empty"] is False
        assert host["burn_state"] == "active"
        assert host["burn_sources"]["observer"]["state"] == "active"
        assert host["burn_sources"]["foundry"]["state"] == "clear"
        assert "cpu_count" not in host
        assert "mem" not in host
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
        assert sorted(data["hosts"].keys()) == ["host-job", "host-teacher", "mac-operator"]
        for host_id in ("host-job", "host-teacher"):
            host = data["hosts"][host_id]
            assert host["host_id"] == host_id
            assert host["status"] == "fresh"
            assert "cpu_count" in host
            assert "loadavg" in host
            assert "mem" in host
            assert "disk" in host
            assert isinstance(host["occupants"], list)
            assert isinstance(host["occupant_count"], int)
            assert isinstance(host["ai_seats"], list)
            assert host["burn_state"] == "idle"
            assert set(host["burn_sources"]) == {
                "atlas_job",
                "driver",
                "foundry",
                "service",
                "observer",
            }
            assert all(source["state"] == "clear" for source in host["burn_sources"].values())
            assert all(source["observation_age_s"] >= 0 for source in host["burn_sources"].values())
            assert isinstance(host["idle_or_empty"], bool)
            assert host["idle_or_empty"] is True
            assert "error" not in host
        _assert_quiet_mac_row(data["hosts"]["mac-operator"])
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
        assert dead["burn_state"] == "unknown"
        assert dead["burn_sources"]["atlas_job"]["state"] == "unknown"
        assert dead["idle_or_empty"] is False
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


def test_occupancy_heartbeat_boundary_stays_fresh_while_probe_runs(tmp_path, monkeypatch) -> None:
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
    parsed = parse_host_id_map("job-box=host-job,teach-box=atlas-runner,bad=1.2.3.4,also=vps,ok=host-teacher")
    assert parsed == {"job-box": "host-job", "ok": "host-teacher"}
    assert not _opaque_host_id("atlas-runner")
    assert not _opaque_host_id("hramatka")
    assert not _opaque_host_id("vps")
    assert not _opaque_host_id("192.0.2.1")
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
        "192.0.2.1",
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
        "192.0.2.1 sweep",
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


def test_occupancy_dual_host_partial_map(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", "job-box=host-job")
    fake = atlas_job.FakeHostAdapter()
    atlas_job.set_host_adapter(fake)
    try:
        load_mod.clear_host_load_cache()
        load_mod.set_host_load_cache("job-box", fake.host_load("job-box"))
        resp = client.get("/api/occupancy")
        assert resp.status_code == 200
        data = resp.json()
        assert sorted(data["hosts"].keys()) == ["host-job", "host-teacher", "mac-operator"]
        assert data["hosts"]["host-job"]["status"] == "fresh"
        assert data["hosts"]["host-job"]["cpu_count"] == 4
        assert data["hosts"]["host-teacher"]["status"] == "unavailable"
        assert data["hosts"]["host-teacher"]["error"] == "unreachable"
        assert data["hosts"]["host-teacher"]["burn_state"] == "unknown"
        assert data["hosts"]["host-teacher"]["idle_or_empty"] is False
        _assert_quiet_mac_row(data["hosts"]["mac-operator"])
    finally:
        atlas_job.set_host_adapter(None)
        load_mod.clear_host_load_cache()


def test_occupancy_idle_or_empty_flag_transitions(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    fake = atlas_job.FakeHostAdapter()
    atlas_job.set_host_adapter(fake)
    try:
        # Case 1: Low load, no occupants -> idle_or_empty is True
        load_mod.clear_host_load_cache()
        idle_load = fake.host_load("job-box")
        idle_load["loadavg"] = [0.10, 0.15, 0.12]
        idle_load["job_unit"] = {"active_count": 0, "job_id": None, "state": None}
        load_mod.set_host_load_cache("job-box", idle_load)
        resp = client.get("/api/occupancy?host_id=host-job")
        assert resp.status_code == 200
        idle_host = resp.json()["hosts"]["host-job"]
        assert idle_host["burn_state"] == "idle"
        assert idle_host["idle_or_empty"] is True

        # Case 2: High CPU load (>= 1.0) -> idle_or_empty is False
        load_mod.clear_host_load_cache()
        busy_load = fake.host_load("job-box")
        busy_load["loadavg"] = [2.50, 1.80, 1.20]
        load_mod.set_host_load_cache("job-box", busy_load)
        resp = client.get("/api/occupancy?host_id=host-job")
        assert resp.status_code == 200
        busy_host = resp.json()["hosts"]["host-job"]
        assert busy_host["burn_state"] == "active"
        assert busy_host["burn_sources"]["atlas_job"]["state"] == "active"
        assert busy_host["idle_or_empty"] is False

        # Case 3: Active job_unit -> idle_or_empty is False
        load_mod.clear_host_load_cache()
        active_unit_load = fake.host_load("job-box")
        active_unit_load["loadavg"] = [0.10, 0.10, 0.10]
        active_unit_load["job_unit"] = {"active_count": 1, "job_id": "unit-job", "state": "running"}
        load_mod.set_host_load_cache("job-box", active_unit_load)
        resp = client.get("/api/occupancy?host_id=host-job")
        assert resp.status_code == 200
        unit_host = resp.json()["hosts"]["host-job"]
        assert unit_host["burn_state"] == "active"
        assert unit_host["burn_sources"]["atlas_job"]["state"] == "active"
        assert unit_host["idle_or_empty"] is False

        # Case 4: Occupant in registry -> idle_or_empty is False
        load_mod.clear_host_load_cache()
        load_mod.set_host_load_cache("job-box", idle_load)
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
                "agent": "gemini",
            }
        )
        resp = client.get("/api/occupancy?host_id=host-job")
        assert resp.status_code == 200
        host_entry = resp.json()["hosts"]["host-job"]
        assert host_entry["burn_state"] == "active"
        assert host_entry["burn_sources"]["atlas_job"]["state"] == "active"
        assert host_entry["idle_or_empty"] is False
        assert host_entry["occupant_count"] == 1
        assert host_entry["ai_seats"] == ["gemini"]
    finally:
        atlas_job.set_host_adapter(None)
        load_mod.clear_host_load_cache()


def test_occupancy_active_driver_lease_wins_at_low_hardware_load(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path / "registry"))
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    monkeypatch.setenv("MONITOR_OCCUPANCY_DRIVER_HOST_ID", "host-job")
    db_path = tmp_path / "session-streams.sqlite3"
    _open_lease(db_path)
    monkeypatch.setattr("scripts.api.occupancy_local.session_streams_db_path", lambda: db_path)
    fake = atlas_job.FakeHostAdapter()
    atlas_job.set_host_adapter(fake)
    try:
        load_mod.clear_host_load_cache()
        low_load = fake.host_load("job-box")
        low_load["loadavg"] = [0.05, 0.05, 0.05]
        low_load["job_unit"] = {"active_count": 0, "job_id": None, "state": None}
        load_mod.set_host_load_cache("job-box", low_load)
        load_mod.set_host_load_cache("teach-box", fake.host_load("teach-box"))
        host = client.get("/api/occupancy?host_id=host-job").json()["hosts"]["host-job"]
        assert host["burn_state"] == "active"
        assert host["burn_sources"]["driver"]["state"] == "active"
        assert host["burn_sources"]["driver"]["observation_age_s"] >= 0
        assert any(row["kind"] == "driver" for row in host["occupants"])
        assert host["idle_or_empty"] is False
    finally:
        atlas_job.set_host_adapter(None)
        load_mod.clear_host_load_cache()


def test_occupancy_fresh_compiler_marker_wins_at_low_hardware_load(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path / "registry"))
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    markers = tmp_path / "markers"
    markers.mkdir()
    monkeypatch.setenv("MONITOR_OCCUPANCY_MARKERS", str(markers))
    write_marker(
        kind="service",
        agent="evidence-compiler",
        task_id="phase3-cycle007-evidence-compiler",
        epic="phase3-cycle007",
        host_id="host-job",
        path=markers,
    )
    fake = atlas_job.FakeHostAdapter()
    atlas_job.set_host_adapter(fake)
    try:
        load_mod.clear_host_load_cache()
        low_load = fake.host_load("job-box")
        low_load["loadavg"] = [0.05, 0.05, 0.05]
        low_load["job_unit"] = {"active_count": 0, "job_id": None, "state": None}
        load_mod.set_host_load_cache("job-box", low_load)
        host = client.get("/api/occupancy?host_id=host-job").json()["hosts"]["host-job"]
        assert host["burn_state"] == "active"
        assert host["burn_sources"]["foundry"]["state"] == "active"
        assert any(row["kind"] == "service" for row in host["occupants"])
    finally:
        atlas_job.set_host_adapter(None)
        load_mod.clear_host_load_cache()


def test_occupancy_generic_service_marker_explains_burn_via_service_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path / "registry"))
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    markers = tmp_path / "markers"
    monkeypatch.setenv("MONITOR_OCCUPANCY_MARKERS", str(markers))
    write_marker(
        kind="service",
        agent="codex",
        task_id="lu-codex-6375",
        epic="6375",
        host_id="host-job",
        path=markers,
    )
    fake = atlas_job.FakeHostAdapter()
    atlas_job.set_host_adapter(fake)
    try:
        load_mod.clear_host_load_cache()
        low_load = fake.host_load("job-box")
        low_load["loadavg"] = [0.05, 0.05, 0.05]
        low_load["job_unit"] = {"active_count": 0, "job_id": None, "state": None}
        load_mod.set_host_load_cache("job-box", low_load)
        host = client.get("/api/occupancy?host_id=host-job").json()["hosts"]["host-job"]
        assert host["occupants"] == [
            {"kind": "service", "agent": "codex", "task_id": "lu-codex-6375", "epic": "6375"}
        ]
        assert host["burn_sources"]["foundry"]["state"] == "clear"
        assert host["burn_sources"]["service"]["state"] == "active"
        assert host["burn_state"] == "active"
        assert host["idle_or_empty"] is False
    finally:
        atlas_job.set_host_adapter(None)
        load_mod.clear_host_load_cache()


def test_occupancy_foundry_and_generic_markers_keep_foundry_burn_honest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path / "registry"))
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    markers = tmp_path / "markers"
    monkeypatch.setenv("MONITOR_OCCUPANCY_MARKERS", str(markers))
    write_marker(
        kind="service",
        agent="cursor",
        task_id="routine-service",
        host_id="host-job",
        path=markers,
    )
    write_marker(
        kind="service",
        agent="evidence-compiler",
        task_id="phase3-cycle007-evidence-compiler",
        epic="phase3-cycle007",
        host_id="host-job",
        path=markers,
    )
    fake = atlas_job.FakeHostAdapter()
    atlas_job.set_host_adapter(fake)
    try:
        load_mod.clear_host_load_cache()
        low_load = fake.host_load("job-box")
        low_load["loadavg"] = [0.05, 0.05, 0.05]
        low_load["job_unit"] = {"active_count": 0, "job_id": None, "state": None}
        load_mod.set_host_load_cache("job-box", low_load)
        host = client.get("/api/occupancy?host_id=host-job").json()["hosts"]["host-job"]
        assert host["occupant_count"] == 2
        assert {row["agent"] for row in host["occupants"]} == {"cursor", "evidence-compiler"}
        assert host["burn_sources"]["foundry"]["state"] == "active"
        assert host["burn_sources"]["service"]["state"] == "active"
        assert host["burn_state"] == "active"
        assert host["idle_or_empty"] is False
    finally:
        atlas_job.set_host_adapter(None)
        load_mod.clear_host_load_cache()


def test_occupancy_unreadable_marker_store_is_unknown_and_opsec_safe(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path / "registry"))
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    markers = tmp_path / "corrupt-markers"
    markers.mkdir()
    (markers / "corrupt.json").write_text("not-json", encoding="utf-8")
    monkeypatch.setenv("MONITOR_OCCUPANCY_MARKERS", str(markers))
    fake = atlas_job.FakeHostAdapter()
    atlas_job.set_host_adapter(fake)
    try:
        load_mod.clear_host_load_cache()
        load_mod.set_host_load_cache("job-box", fake.host_load("job-box"))
        host = client.get("/api/occupancy?host_id=host-job").json()["hosts"]["host-job"]
        assert host["burn_state"] == "unknown"
        assert host["burn_sources"]["foundry"]["state"] == "unknown"
        assert host["idle_or_empty"] is False
        text = json.dumps(host).lower()
        for forbidden in ("/users/", "192.0.2.1", "atlas-runner", "tunnel", "ssh", "not-json"):
            assert forbidden not in text
    finally:
        atlas_job.set_host_adapter(None)
        load_mod.clear_host_load_cache()


def test_occupancy_corrupt_driver_db_is_unknown_and_not_idle(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path / "registry"))
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    monkeypatch.setenv("MONITOR_OCCUPANCY_DRIVER_HOST_ID", "host-job")
    db_path = tmp_path / "broken-session-streams.sqlite3"
    db_path.write_text("not-a-database", encoding="utf-8")
    monkeypatch.setattr("scripts.api.occupancy_local.session_streams_db_path", lambda: db_path)
    fake = atlas_job.FakeHostAdapter()
    atlas_job.set_host_adapter(fake)
    try:
        load_mod.clear_host_load_cache()
        load_mod.set_host_load_cache("job-box", fake.host_load("job-box"))
        host = client.get("/api/occupancy?host_id=host-job").json()["hosts"]["host-job"]
        assert host["burn_state"] == "unknown"
        assert host["burn_sources"]["driver"]["state"] == "unknown"
        assert host["idle_or_empty"] is False
    finally:
        atlas_job.set_host_adapter(None)
        load_mod.clear_host_load_cache()


def test_occupancy_expired_marker_is_clear(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path / "registry"))
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    markers = tmp_path / "markers"
    markers.mkdir()
    monkeypatch.setenv("MONITOR_OCCUPANCY_MARKERS", str(markers))
    write_marker(
        kind="service",
        agent="evidence-compiler",
        task_id="phase3-cycle007-evidence-compiler",
        epic="phase3-cycle007",
        host_id="host-job",
        path=markers,
        ttl_seconds=1,
        now=datetime.now(UTC) - timedelta(seconds=5),
    )
    fake = atlas_job.FakeHostAdapter()
    atlas_job.set_host_adapter(fake)
    try:
        load_mod.clear_host_load_cache()
        load_mod.set_host_load_cache("job-box", fake.host_load("job-box"))
        host = client.get("/api/occupancy?host_id=host-job").json()["hosts"]["host-job"]
        assert host["burn_sources"]["foundry"]["state"] == "clear"
        assert host["burn_state"] == "idle"
        assert host["idle_or_empty"] is True
    finally:
        atlas_job.set_host_adapter(None)
        load_mod.clear_host_load_cache()


def test_occupancy_unmapped_default_host_query(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    monkeypatch.delenv("MONITOR_OCCUPANCY_HOST_IDS", raising=False)
    fake = atlas_job.FakeHostAdapter()
    atlas_job.set_host_adapter(fake)
    try:
        resp = client.get("/api/occupancy?host_id=host-teacher")
        assert resp.status_code == 200
        data = resp.json()
        assert list(data["hosts"].keys()) == ["host-teacher"]
        teacher = data["hosts"]["host-teacher"]
        assert teacher["host_id"] == "host-teacher"
        assert teacher["status"] == "unavailable"
        assert teacher["error"] == "unreachable"
        assert teacher["idle_or_empty"] is False
        assert teacher["occupant_count"] == 0
        assert teacher["ai_seats"] == []
    finally:
        atlas_job.set_host_adapter(None)
        load_mod.clear_host_load_cache()


def test_cloud_observer_explicit_query_with_zero_heartbeats_is_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Explicit cloud-observer query must not fake fresh/0.0 with no presence."""
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    monkeypatch.delenv("MONITOR_OCCUPANCY_HOST_IDS", raising=False)
    fake = atlas_job.FakeHostAdapter()
    atlas_job.set_host_adapter(fake)
    try:
        resp = client.get("/api/occupancy?host_id=cloud-observer")
        assert resp.status_code == 200
        host = resp.json()["hosts"]["cloud-observer"]
        assert host["host_id"] == "cloud-observer"
        assert host["status"] == "unavailable"
        assert host["error"] == "unreachable"
        assert host["age_seconds"] == 0.0
        assert host["occupants"] == []
        assert host["occupant_count"] == 0
        assert host["status"] != "fresh"
    finally:
        atlas_job.set_host_adapter(None)
        load_mod.clear_host_load_cache()


def test_cloud_observer_presence_age_uses_freshness_window(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    monkeypatch.delenv("MONITOR_OCCUPANCY_HOST_IDS", raising=False)
    fake = atlas_job.FakeHostAdapter()
    atlas_job.set_host_adapter(fake)
    try:
        stamp = time.monotonic()
        upsert_presence(
            PresenceRequest.model_validate(
                {
                    "agent": "grok-bot",
                    "kind": "observer",
                    "task_id": "7491",
                    "status": "working",
                }
            ),
            now_mono=stamp - PRESENCE_FRESHNESS_SECONDS - 5,
        )
        # Freeze presence list_live clock via occupancy snapshot now_mono by
        # advancing wall monotonic only through the stored updated_at_mono.
        host = client.get("/api/occupancy?host_id=cloud-observer").json()["hosts"]["cloud-observer"]
        assert host["status"] == "stale"
        assert host["age_seconds"] >= PRESENCE_FRESHNESS_SECONDS
        assert host["burn_state"] == "active"
        assert host["burn_sources"]["observer"]["state"] == "active"
        assert host["burn_sources"]["observer"]["observation_age_s"] >= PRESENCE_FRESHNESS_SECONDS
    finally:
        atlas_job.set_host_adapter(None)
        load_mod.clear_host_load_cache()
