"""High-load attribution stays bounded and never collects process arguments (#10715)."""

from __future__ import annotations

import asyncio
import fcntl
from unittest.mock import Mock

import psutil
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from scripts.api import load_samples as sampler
from scripts.api import work_router
from scripts.api.monitor_context import fixture_context
from scripts.api.ops_router import router
from scripts.api.route_contracts import contract_for_route

ROUTE = "/api/ops/v1/load-samples"


@pytest.fixture
def observed(monkeypatch):
    monkeypatch.delenv(sampler.THRESHOLD_ENV, raising=False)
    monkeypatch.setattr(sampler.os, "getloadavg", lambda: (21.0, 18.0, 10.0))
    monkeypatch.setattr(sampler.time, "time", lambda: 1_800_000_000.0)
    processes = Mock(return_value=[{"name": "pytest", "cpu_percent": 250.0}])
    monkeypatch.setattr(sampler, "top_processes", processes)
    monkeypatch.setattr(
        sampler.test_slots,
        "status",
        lambda: {
            "holders": [{"task_id": "task-7", "slots": 2, "pid": 987, "kind": "pytest"}],
            "error": None,
            "enabled": True,
        },
    )
    return processes


@pytest.mark.parametrize("load", [0, 19.9, 20])
def test_below_or_at_threshold_never_scans_or_writes(tmp_path, monkeypatch, observed, load):
    monkeypatch.setattr(sampler.os, "getloadavg", lambda: (load, 30, 30))
    assert sampler.sample(tmp_path) is False
    observed.assert_not_called()
    assert list(tmp_path.iterdir()) == []


def test_above_threshold_has_only_attribution_fields(tmp_path, observed):
    assert sampler.sample(tmp_path) is True
    assert sampler.tail(tmp_path, 50) == {
        "schema": "load-samples.v1",
        "error": None,
        "samples": [
            {
                "timestamp": "2027-01-15T08:00:00+00:00",
                "load_averages": [21.0, 18.0, 10.0],
                "top_processes": [{"name": "pytest", "cpu_percent": 250.0}],
                "top_cpu_percent": 250.0,
                "test_slots": {"holders": [{"task_id": "task-7", "slots": 2}], "error": None, "enabled": True},
            }
        ],
    }
    observed.assert_called_once()


def test_rate_limit_survives_new_calls_and_allows_next_minute(tmp_path, monkeypatch, observed):
    assert sampler.sample(tmp_path)
    monkeypatch.setattr(sampler.time, "time", lambda: 1_800_000_059.9)
    assert sampler.sample(tmp_path) is False
    assert observed.call_count == 1
    monkeypatch.setattr(sampler.time, "time", lambda: 1_800_000_060)
    assert sampler.sample(tmp_path)
    assert len(sampler.tail(tmp_path, 500)["samples"]) == 2


def test_concurrent_collector_is_skipped(tmp_path, observed):
    directory = tmp_path / "load-samples"
    directory.mkdir()
    with (directory / "collector.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert sampler.sample(tmp_path) is False
    observed.assert_not_called()


def test_ring_keeps_only_last_500_physical_lines(tmp_path, monkeypatch, observed):
    for index in range(503):
        monkeypatch.setattr(sampler.time, "time", lambda index=index: 1_800_000_000 + index * 60)
        assert sampler.sample(tmp_path)
    lines = (tmp_path / "load-samples" / "samples.jsonl").read_text().split("\n")
    assert len(lines) == 501 and lines[-1] == ""
    rows = sampler.tail(tmp_path, 500)["samples"]
    assert len(rows) == 500
    assert rows[0]["timestamp"] == "2027-01-15T08:03:00+00:00"
    assert sampler.tail(tmp_path, 2)["samples"] == rows[-2:]


@pytest.mark.parametrize("value", ["garbage", "nan", "inf", "-1"])
def test_invalid_threshold_records_nothing(tmp_path, monkeypatch, observed, value):
    monkeypatch.setenv(sampler.THRESHOLD_ENV, value)
    with pytest.raises(ValueError):
        sampler.sample(tmp_path)
    observed.assert_not_called()
    assert not (tmp_path / "load-samples").exists()


def test_threshold_override_and_unknown_governor(tmp_path, monkeypatch, observed):
    monkeypatch.setenv(sampler.THRESHOLD_ENV, "22")
    assert sampler.sample(tmp_path) is False
    monkeypatch.setenv(sampler.THRESHOLD_ENV, "10")
    monkeypatch.setattr(
        sampler.test_slots,
        "status",
        lambda: {
            "holders": [],
            "error": {"reason": "pool_unavailable", "detail": "private"},
            "enabled": None,
        },
    )
    assert sampler.sample(tmp_path)
    assert sampler.tail(tmp_path, 1)["samples"][0]["test_slots"] == {
        "holders": [],
        "error": "pool_unavailable",
        "enabled": None,
    }


def test_process_scan_primes_cpu_and_never_reads_secret_arguments(tmp_path, monkeypatch):
    processes = []
    for name, cpu in [
        ("pytest", 400),
        ("codex", 100),
        ("node", 60),
        ("postgres", 30),
        ("cc", 10),
        ("idle", 0),
        ("/private/bin/tool --token=SECRET-123", 5),
        ("bad\nname", 4),
        (None, 2),
        ("invalid", float("nan")),
    ]:
        process = Mock(info={"name": name})
        process.cpu_percent.side_effect = [0.0, cpu]
        process.cmdline.side_effect = AssertionError("must never read arguments --token=SECRET-123")
        processes.append(process)
    denied = Mock()
    denied.cpu_percent.side_effect = psutil.AccessDenied()
    gone = Mock(info={"name": "gone"})
    gone.cpu_percent.side_effect = [0.0, psutil.NoSuchProcess(42)]
    scan = Mock(return_value=[*processes, denied, gone])
    monkeypatch.setattr(sampler.psutil, "process_iter", scan)
    sleep = Mock()
    monkeypatch.setattr(sampler.time, "sleep", sleep)
    monkeypatch.setattr(sampler.os, "getloadavg", lambda: (21, 20, 10))
    monkeypatch.setattr(sampler.test_slots, "status", lambda: {"holders": [], "error": None, "enabled": True})
    assert sampler.sample(tmp_path)
    row = sampler.tail(tmp_path, 1)["samples"][0]
    assert row["top_processes"] == [
        {"name": "pytest", "cpu_percent": 400.0},
        {"name": "codex", "cpu_percent": 100.0},
        {"name": "node", "cpu_percent": 60.0},
        {"name": "postgres", "cpu_percent": 30.0},
        {"name": "cc", "cpu_percent": 10.0},
    ]
    assert row["top_cpu_percent"] == 600.0
    assert "SECRET" not in (tmp_path / "load-samples" / "samples.jsonl").read_text()
    scan.assert_called_once_with(attrs=["name"])
    sleep.assert_called_once_with(0.1)
    for process in processes:
        process.cmdline.assert_not_called()


def test_invalid_command_name_is_redacted(monkeypatch):
    process = Mock(info={"name": "/private/tool --token=SECRET"})
    process.cpu_percent.return_value = 99.0
    monkeypatch.setattr(sampler.psutil, "process_iter", lambda **_: [process])
    monkeypatch.setattr(sampler.time, "sleep", lambda _: None)
    assert sampler.top_processes() == [{"name": "unknown", "cpu_percent": 99.0}]


def test_route_is_bounded_read_only_and_contract_registered(tmp_path, observed):
    app = FastAPI()
    ctx = fixture_context(tmp_path)
    app.state.ctx = ctx
    app.include_router(router, prefix="/api/ops")
    with TestClient(app) as client:
        assert client.get(ROUTE).json() == {"schema": "load-samples.v1", "samples": [], "error": None}
        assert not ctx.roots.batch_state_dir.exists()
        assert sampler.sample(ctx.roots.batch_state_dir)
        before = observed.call_count
        response = client.get(ROUTE + "?limit=1")
        assert response.status_code == 200 and len(response.json()["samples"]) == 1
        assert observed.call_count == before
        assert str(tmp_path) not in response.text
        for limit in ("0", "501", "oops"):
            assert client.get(ROUTE, params={"limit": limit}).status_code == 422
    contract = contract_for_route(ROUTE)
    assert contract.pattern == ROUTE and contract.match == "exact"
    assert contract.mutates is False and contract.locality == "host_affine"
    assert contract.response_schema_version == "load-samples.v1"


def test_unreadable_ring_returns_path_free_error(tmp_path):
    directory = tmp_path / "load-samples"
    directory.mkdir()
    (directory / "samples.jsonl").write_text("broken")
    assert sampler.tail(tmp_path, 1) == {
        "schema": "load-samples.v1",
        "samples": [],
        "error": "load_samples_unavailable",
    }


@pytest.mark.parametrize("fails", [False, True])
def test_existing_periodic_collector_samples_even_with_warm_projection(tmp_path, monkeypatch, fails):
    ctx = fixture_context(tmp_path)
    calls = []

    async def tick(_):
        if calls:
            raise asyncio.CancelledError

    def sample(path):
        assert path == ctx.roots.batch_state_dir
        calls.append("sample")
        if fails:
            raise OSError("private path must not enter logs")

    monkeypatch.setattr(work_router.asyncio, "sleep", tick)
    monkeypatch.setattr(work_router, "sample_host_load", sample)
    monkeypatch.setattr(work_router, "fetch_open_prs", lambda: calls.append("prs"))
    monkeypatch.setattr(work_router, "cache_get_with_age", lambda *_: ({}, 0))
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(work_router.refresh_projection_cache_periodically(ctx))
    assert calls == ["sample", "prs"]
