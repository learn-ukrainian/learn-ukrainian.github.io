"""Concurrent status routes must share one scan and return without the request timeout.

A warm hit stays on the event loop, so a saturated worker pool cannot turn a
cached dashboard read into a timeout. Cold misses for the same key share one
compute.
"""

from __future__ import annotations

import asyncio
import json
import threading
import time
from contextlib import contextmanager
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI
from httpx import ASGITransport

from scripts.api import artifacts_router, delegate_router, epics_router, state_helpers, state_router
from scripts.api.monitor_context import fixture_context

_BURST = 20
_BUDGET_S = 2.0
_SLOW_S = 0.3


@pytest.fixture(autouse=True)
def _clear_status_cache():
    state_helpers.cache_invalidate()
    yield
    state_helpers.cache_invalidate()


def _mount(tmp_path: Path, router, prefix: str) -> FastAPI:
    app = FastAPI()
    app.state.ctx = fixture_context(tmp_path)
    app.include_router(router, prefix=prefix)
    return app


async def _burst(app: FastAPI, path: str) -> tuple[float, list[httpx.Response]]:
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        started = time.perf_counter()
        responses = await asyncio.gather(*[client.get(path) for _ in range(_BURST)])
        return time.perf_counter() - started, list(responses)


def _assert_burst(elapsed: float, responses: list[httpx.Response], calls: dict[str, int]) -> None:
    assert elapsed < _BUDGET_S, f"burst took {elapsed:.3f}s"
    assert calls["n"] == 1
    assert [response.status_code for response in responses] == [200] * _BURST


def test_delegate_active_burst_shares_one_scan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def slow(**_kwargs):
        calls["n"] += 1
        time.sleep(_SLOW_S)
        return {"total": 0, "tasks": []}

    monkeypatch.setattr(delegate_router, "active_delegate_tasks", slow)
    elapsed, responses = asyncio.run(
        _burst(_mount(tmp_path, delegate_router.router, "/api/delegate"), "/api/delegate/active")
    )
    _assert_burst(elapsed, responses, calls)


def test_delegate_tasks_burst_shares_one_scan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def slow(**_kwargs):
        calls["n"] += 1
        time.sleep(_SLOW_S)
        return {"total": 0, "tasks": []}

    monkeypatch.setattr(delegate_router, "list_delegate_tasks", slow)
    elapsed, responses = asyncio.run(
        _burst(_mount(tmp_path, delegate_router.router, "/api/delegate"), "/api/delegate/tasks")
    )
    _assert_burst(elapsed, responses, calls)


def test_state_summary_burst_shares_one_scan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def slow(**_kwargs):
        calls["n"] += 1
        time.sleep(_SLOW_S)
        return {"generated_at": "2026-01-01T00:00:00Z", "tracks": {}, "totals": {}}

    monkeypatch.setattr(state_router, "compute_summary", slow)
    elapsed, responses = asyncio.run(_burst(_mount(tmp_path, state_router.router, "/api/state"), "/api/state/summary"))
    _assert_burst(elapsed, responses, calls)


def test_pipeline_versions_burst_shares_one_scan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def slow(_ctx, _track):
        calls["n"] += 1
        time.sleep(_SLOW_S)
        return {"generated_at": "2026-01-01T00:00:00Z", "total": 0, "counts": {}}

    monkeypatch.setattr(state_router, "_compute_pipeline_versions_payload", slow)
    elapsed, responses = asyncio.run(
        _burst(_mount(tmp_path, state_router.router, "/api/state"), "/api/state/pipeline-versions")
    )
    _assert_burst(elapsed, responses, calls)


def test_weak_points_burst_shares_one_scan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def slow(_ctx, _track, _min_score, _limit):
        calls["n"] += 1
        time.sleep(_SLOW_S)
        return {"count": 0, "modules": []}

    monkeypatch.setattr(state_router, "_compute_weak_points_payload", slow)
    elapsed, responses = asyncio.run(
        _burst(_mount(tmp_path, state_router.router, "/api/state"), "/api/state/weak-points")
    )
    _assert_burst(elapsed, responses, calls)


def test_research_coverage_burst_shares_one_scan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def slow(**_kwargs):
        calls["n"] += 1
        time.sleep(_SLOW_S)
        return {"generated_at": "2026-01-01T00:00:00Z", "tracks": {}}

    monkeypatch.setattr(state_router, "compute_research_coverage", slow)
    elapsed, responses = asyncio.run(
        _burst(_mount(tmp_path, state_router.router, "/api/state"), "/api/state/research-coverage")
    )
    _assert_burst(elapsed, responses, calls)


def test_artifacts_html_burst_shares_one_scan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def slow(**_kwargs):
        calls["n"] += 1
        time.sleep(_SLOW_S)
        return {"generated_at": "2026-01-01T00:00:00Z", "total": 0, "artifacts": []}

    monkeypatch.setattr(artifacts_router, "collect_html_artifacts", slow)
    elapsed, responses = asyncio.run(
        _burst(_mount(tmp_path, artifacts_router.router, "/api/artifacts"), "/api/artifacts/html")
    )
    _assert_burst(elapsed, responses, calls)


def test_epics_list_burst_shares_one_read(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def slow(_ctx):
        calls["n"] += 1
        time.sleep(_SLOW_S)
        return {"schema": "remote-epic-lifecycle.v1", "registry_status": "ok", "streams": []}

    monkeypatch.setattr(epics_router, "_build_remote_epic_list", slow)
    elapsed, responses = asyncio.run(_burst(_mount(tmp_path, epics_router.router, "/api/epics"), "/api/epics/v1"))
    _assert_burst(elapsed, responses, calls)


def test_routing_budget_burst_shares_one_compute(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def slow(**_kwargs):
        calls["n"] += 1
        time.sleep(_SLOW_S)
        return {"generated_at": "2026-01-01T00:00:00Z", "agents": {}, "recommendation": {}}

    monkeypatch.setattr(state_router, "compute_routing_budget", slow)
    elapsed, responses = asyncio.run(
        _burst(_mount(tmp_path, state_router.router, "/api/state"), "/api/state/routing-budget")
    )
    _assert_burst(elapsed, responses, calls)


def test_warm_routing_budget_does_not_wait_on_the_worker_pool(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}
    hold = threading.Event()

    def slow(**_kwargs):
        calls["n"] += 1
        if calls["n"] > 1:
            hold.wait(timeout=2)
        return {"generated_at": "2026-01-01T00:00:00Z", "marker": calls["n"]}

    monkeypatch.setattr(state_router, "compute_routing_budget", slow)
    app = _mount(tmp_path, state_router.router, "/api/state")

    async def scenario() -> float:
        transport = ASGITransport(app=app)
        release = threading.Event()
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            first = await client.get("/api/state/routing-budget")
            assert first.status_code == 200
            loop = asyncio.get_running_loop()
            blockers = [loop.run_in_executor(None, release.wait) for _ in range(64)]
            try:
                await asyncio.sleep(0.05)
                started = time.perf_counter()
                second = await asyncio.wait_for(client.get("/api/state/routing-budget"), timeout=1.0)
                elapsed = time.perf_counter() - started
            finally:
                release.set()
                await asyncio.gather(*blockers, return_exceptions=True)
        assert second.status_code == 200
        assert second.json()["marker"] == 1
        return elapsed

    try:
        assert asyncio.run(scenario()) < 0.5
        assert calls["n"] == 1
    finally:
        hold.set()


def test_stale_routing_budget_returns_while_refresh_runs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    clock = {"t": 1_000.0}
    calls = {"n": 0}
    hold = threading.Event()
    monkeypatch.setattr(state_helpers, "_ttl_clock", lambda: clock["t"])

    def slow(**_kwargs):
        calls["n"] += 1
        if calls["n"] > 1:
            hold.wait(timeout=2)
        return {"generated_at": "2026-01-01T00:00:00Z", "marker": 1}

    monkeypatch.setattr(state_router, "compute_routing_budget", slow)
    app = _mount(tmp_path, state_router.router, "/api/state")

    async def scenario() -> float:
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            first = await client.get("/api/state/routing-budget")
            assert first.status_code == 200
            clock["t"] += state_router.ROUTING_BUDGET_TTL_S + 1
            started = time.perf_counter()
            second = await asyncio.wait_for(client.get("/api/state/routing-budget"), timeout=1.0)
            elapsed = time.perf_counter() - started
        assert second.status_code == 200
        assert second.json()["marker"] == 1
        return elapsed

    try:
        assert asyncio.run(scenario()) < 0.5
    finally:
        hold.set()


def test_expired_routing_budget_reports_age_and_withdraws_authorization(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clock = {"t": 1_000.0}
    calls = {"n": 0}
    monkeypatch.setattr(state_helpers, "_ttl_clock", lambda: clock["t"])

    def compute(**_kwargs):
        calls["n"] += 1
        if calls["n"] > 1:
            raise RuntimeError("refresh failed")
        return {
            "generated_at": "2026-01-01T00:00:00Z",
            "agents": {"codex": {"eligible": True, "status": "cool"}},
            "recommendation": {
                "primary_agent_for_code": "codex",
                "rationale": "fresh",
                "warnings": [],
            },
            "diagnostics": {"stale": False, "data_age_s": 0, "stale_threshold_s": 900},
            "ranked_by_headroom": [{"lane": "codex"}],
        }

    monkeypatch.setattr(state_router, "compute_routing_budget", compute)
    app = _mount(tmp_path, state_router.router, "/api/state")

    async def scenario() -> tuple[dict, dict]:
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            first = await client.get("/api/state/routing-budget")
            assert first.status_code == 200
            assert first.json()["diagnostics"]["stale"] is False
            clock["t"] += state_router.ROUTING_BUDGET_TTL_S + 5
            aged = await client.get("/api/state/routing-budget")
            for _ in range(50):
                if calls["n"] >= 2 and not state_helpers._refresh_keys:
                    break
                await asyncio.sleep(0.02)
            clock["t"] = 1_000.0 + state_router.ROUTING_BUDGET_MAX_AGE_S + 1
            withdrawn = await client.get("/api/state/routing-budget")
        return aged.json(), withdrawn.json()

    aged, withdrawn = asyncio.run(scenario())
    assert calls["n"] >= 2
    assert aged["diagnostics"]["stale"] is True
    assert aged["diagnostics"]["data_age_s"] == state_router.ROUTING_BUDGET_TTL_S + 5
    assert set(aged["diagnostics"]) == {"stale", "data_age_s", "stale_threshold_s"}
    assert aged["recommendation"]["primary_agent_for_code"] == "codex"
    assert withdrawn["diagnostics"]["stale"] is True
    assert withdrawn["diagnostics"]["data_age_s"] == state_router.ROUTING_BUDGET_MAX_AGE_S + 1
    assert withdrawn["recommendation"]["primary_agent_for_code"] is None
    assert withdrawn["agents"]["codex"]["eligible"] is False
    assert withdrawn["agents"]["codex"]["status"] == "unknown"
    assert withdrawn["ranked_by_headroom"] == []


def _routing_snapshot(data_age_s: float) -> dict:
    return {
        "generated_at": "2026-01-01T00:00:00Z",
        "agents": {"codex": {"eligible": True, "status": "cool"}},
        "recommendation": {
            "primary_agent_for_code": "codex",
            "rationale": "fresh",
            "warnings": [],
        },
        "diagnostics": {"stale": False, "data_age_s": data_age_s, "stale_threshold_s": 900},
        "ranked_by_headroom": [{"lane": "codex"}],
    }


def test_cumulative_source_age_withdraws_routing_authorization(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Source age plus cache residence is the age compared to the threshold."""
    clock = {"t": 1_000.0}
    calls = {"n": 0}
    monkeypatch.setattr(state_helpers, "_ttl_clock", lambda: clock["t"])

    def compute(**_kwargs):
        calls["n"] += 1
        if calls["n"] > 1:
            raise RuntimeError("refresh failed")
        return _routing_snapshot(890)

    monkeypatch.setattr(state_router, "compute_routing_budget", compute)
    app = _mount(tmp_path, state_router.router, "/api/state")

    async def scenario() -> dict:
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            first = await client.get("/api/state/routing-budget")
            assert first.status_code == 200
            assert first.json()["recommendation"]["primary_agent_for_code"] == "codex"
            clock["t"] += 20
            aged = await client.get("/api/state/routing-budget")
        return aged.json()

    body = asyncio.run(scenario())
    assert body["diagnostics"]["stale"] is True
    assert body["diagnostics"]["data_age_s"] == 910
    assert set(body["diagnostics"]) == {"stale", "data_age_s", "stale_threshold_s"}
    assert body["recommendation"]["primary_agent_for_code"] is None
    assert body["agents"]["codex"]["eligible"] is False
    assert body["ranked_by_headroom"] == []


def test_cumulative_source_age_under_threshold_keeps_authorization(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clock = {"t": 1_000.0}
    monkeypatch.setattr(state_helpers, "_ttl_clock", lambda: clock["t"])

    def compute(**_kwargs):
        return _routing_snapshot(800)

    monkeypatch.setattr(state_router, "compute_routing_budget", compute)
    app = _mount(tmp_path, state_router.router, "/api/state")

    async def scenario() -> dict:
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            first = await client.get("/api/state/routing-budget")
            assert first.status_code == 200
            clock["t"] += 20
            aged = await client.get("/api/state/routing-budget")
        return aged.json()

    body = asyncio.run(scenario())
    assert body["diagnostics"]["stale"] is True
    assert body["diagnostics"]["data_age_s"] == 820
    assert body["recommendation"]["primary_agent_for_code"] == "codex"
    assert body["agents"]["codex"]["eligible"] is True
    assert body["ranked_by_headroom"] == [{"lane": "codex"}]


def test_artifact_filters_with_colons_do_not_share_a_cache_entry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[tuple[object, object]] = []

    def collect(**kwargs):
        seen.append((kwargs.get("status"), kwargs.get("author")))
        return {"status": kwargs.get("status"), "author": kwargs.get("author"), "artifacts": []}

    monkeypatch.setattr(artifacts_router, "collect_html_artifacts", collect)
    app = _mount(tmp_path, artifacts_router.router, "/api/artifacts")

    async def scenario() -> tuple[dict, dict]:
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            first = await client.get(
                "/api/artifacts/html",
                params={"status": "draft", "author": "team:alpha"},
            )
            second = await client.get(
                "/api/artifacts/html",
                params={"status": "draft:team", "author": "alpha"},
            )
        return first.json(), second.json()

    one, two = asyncio.run(scenario())
    assert seen == [("draft", "team:alpha"), ("draft:team", "alpha")]
    assert one["author"] == "team:alpha"
    assert two["author"] == "alpha"
    assert one["status"] == "draft"
    assert two["status"] == "draft:team"


def test_delegate_list_replaces_the_previous_generation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def scan(**_kwargs):
        calls["n"] += 1
        return {"total": calls["n"], "tasks": []}

    monkeypatch.setattr(delegate_router, "active_delegate_tasks", scan)
    app = _mount(tmp_path, delegate_router.router, "/api/delegate")
    tasks_dir = tmp_path / "batch_state" / "tasks"
    tasks_dir.mkdir(parents=True)

    async def scenario() -> None:
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            first = await client.get("/api/delegate/active")
            assert first.json()["total"] == 1
            (tasks_dir / "one.json").write_text("{}", encoding="utf-8")
            second = await client.get("/api/delegate/active")
            assert second.json()["total"] == 2

    asyncio.run(scenario())
    keys = [key for key in state_helpers._ttl_cache if ":delegate:" in key]
    assert len(keys) == 1


def test_delegate_active_sequential_requests_reobserve_source(tmp_path, monkeypatch):
    calls = {"n": 0}

    def scan(**_kwargs):
        calls["n"] += 1
        return {"total": 0, "tasks": [], "sample": calls["n"]}

    monkeypatch.setattr(delegate_router, "active_delegate_tasks", scan)
    app = _mount(tmp_path, delegate_router.router, "/api/delegate")

    async def scenario():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            first = await client.get("/api/delegate/active")
            second = await client.get("/api/delegate/active")
            assert first.json()["sample"] == 1
            assert second.json()["sample"] == 2

    asyncio.run(scenario())


_REALISTIC_SERVER = r"""
import json
import os
from pathlib import Path
import socket
import sys
from fastapi import FastAPI
import uvicorn
from scripts.api import delegate_router
from scripts.api.monitor_context import fixture_context
from scripts.orchestration.dead_worker_state import capture_worker_identity
root = Path(sys.argv[1])
for i in range(8):
    (root / 'batch_state/tasks' / f'active-{i}.json').write_text(json.dumps({
        'task_id': f'active-{i}', 'status': 'running', 'agent': 'codex',
        'pid': os.getpid(), 'worker_identity': capture_worker_identity(os.getpid()),
    }))
app = FastAPI()
app.state.ctx = fixture_context(root)
app.include_router(delegate_router.router, prefix='/api/delegate')
sock = socket.socket(fileno=int(sys.argv[2]))
uvicorn.Server(uvicorn.Config(app, log_level='critical', access_log=False)).run(sockets=[sock])
"""


@pytest.fixture(scope="module")
def realistic_active_store(tmp_path_factory):
    import json

    root = tmp_path_factory.mktemp("active-realistic")
    tasks = root / "batch_state/tasks"
    tasks.mkdir(parents=True)
    # A full 212 MB denominator, including nested dispatch metadata and output.
    record = {
        "status": "done",
        "agent": "codex",
        "task_id": "terminal",
        "dispatch": [{"key": i, "value": "record metadata"} for i in range(50)],
        "output": "task output " * 1200,
    }
    record["padding"] = ""
    unpadded = json.dumps(record, ensure_ascii=False)
    record["padding"] = "x" * (16995 - len(unpadded.encode()))
    raw = json.dumps(record, ensure_ascii=False)
    assert len(raw.encode()) == 16995
    for i in range(12475):
        (tasks / f"terminal-{i:05d}.json").write_text(raw)
    assert sum(p.stat().st_size for p in tasks.iterdir()) == 212012625
    return root


@contextmanager
def _observe_consumer_http(evidence, opener, *args, **kwargs):
    try:
        with opener(*args, **kwargs) as response:
            evidence["http_status"] = response.status

            class ObservedResponse:
                def read(self, *args, **kwargs):
                    raw = response.read(*args, **kwargs)
                    evidence["_body"] = raw
                    return raw

            yield ObservedResponse()
    except Exception as exc:
        evidence.update(exception=type(exc).__name__, reason_class=type(getattr(exc, "reason", None)).__name__)
        evidence["errno"] = exc.errno if isinstance(getattr(exc, "errno", None), int) else None
        if isinstance(getattr(exc, "code", None), int):
            evidence["http_status"] = exc.code
        raise


def _consumer_evidence(evidence):
    raw = evidence.pop("_body", None)
    if raw is not None:
        try:
            payload = json.loads(raw.decode("utf-8"))
            evidence["json_shape"] = type(payload).__name__
            if isinstance(payload, dict):
                source, tasks = payload.get("source"), payload.get("tasks")
                scanned = source.get("records_scanned") if isinstance(source, dict) else None
                evidence["records_scanned"] = scanned if type(scanned) is int else None
                evidence["total"] = payload.get("total") if type(payload.get("total")) is int else None
                evidence["tasks_count"] = len(tasks) if isinstance(tasks, list) else None
        except (ValueError, UnicodeError) as exc:
            evidence["parse_exception"] = type(exc).__name__
    return evidence


@pytest.mark.parametrize("failure", [None, "open", "read"])
def test_consumer_http_observer_preserves_operations(failure):
    from io import BytesIO

    evidence, calls, error = {}, [], OSError(5, "synthetic private detail")
    raw = b'{"total":8,"tasks":[{},{},{},{},{},{},{},{}],"source":{"records_scanned":12483}}'
    response = BytesIO(raw)
    response.status = 200

    def opener(*args, **kwargs):
        calls.append((args, kwargs))
        if failure == "open":
            raise error
        return response

    def consume():
        with _observe_consumer_http(evidence, opener, "synthetic", timeout=2.0) as observed:
            if failure == "read":
                response.close()
            return observed.read()

    if failure:
        with pytest.raises(OSError if failure == "open" else ValueError) as caught:
            consume()
        assert caught.value is error if failure == "open" else evidence["exception"] == "ValueError"
    else:
        assert consume() == raw
        assert list(_consumer_evidence(evidence).values()) == [200, "dict", 12483, 8, 8]
    assert calls == [(("synthetic",), {"timeout": 2.0})]
    assert response.closed if failure != "open" else not response.closed


@pytest.mark.parametrize("consumer", ["capacity", "fleet", "goal"])
def test_realistic_active_cold_and_warm_actual_two_second_consumers(realistic_active_store, monkeypatch, consumer):
    import json
    import socket
    import subprocess
    import sys
    import urllib.error
    import urllib.request

    from scripts.fleet import capacity_pick
    from scripts.fleet_comms import cli as fleet_cli
    from scripts.goal_driver import stop_hook

    root = realistic_active_store
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen()
        base = f"http://127.0.0.1:{sock.getsockname()[1]}"
        process = subprocess.Popen(
            [sys.executable, "-c", _REALISTIC_SERVER, str(root), str(sock.fileno())],
            pass_fds=(sock.fileno(),),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        try:
            deadline = time.monotonic() + 15
            while True:
                try:
                    # Readiness must never warm the active inventory.
                    with urllib.request.urlopen(base + "/openapi.json", timeout=0.1) as response:
                        assert response.status == 200
                    break
                except (OSError, urllib.error.URLError):
                    assert time.monotonic() < deadline and process.poll() is None
                    time.sleep(0.05)
            monkeypatch.setattr(capacity_pick, "_monitor_base", lambda: base)
            monkeypatch.setattr(stop_hook, "MONITOR_API", base)
            opener = urllib.request.urlopen
            monkeypatch.setattr(
                urllib.request, "urlopen", lambda *a, **kw: _observe_consumer_http(evidence, opener, *a, **kw)
            )
            for attempt, temperature in enumerate(("cold", "warm", "warm"), 1):
                evidence = dict.fromkeys(("http_status", "exception", "errno", "reason_class"))
                evidence.update(consumer=consumer, temperature=temperature, attempt=attempt)
                started = time.perf_counter()
                try:
                    if consumer == "capacity":
                        result = capacity_pick.fetch_active_in_flight()
                    elif consumer == "fleet":
                        result = fleet_cli._fetch_json_fail_open(base + "/api/delegate/active")
                    else:
                        result = stop_hook._query_active_dispatches()
                finally:
                    elapsed = time.perf_counter() - started
                    evidence["elapsed_s"] = elapsed
                    print(json.dumps(_consumer_evidence(evidence)), flush=True)
                if consumer == "capacity":
                    assert result == {"codex": 8}
                elif consumer == "fleet":
                    assert result["available"] is True
                    assert result["payload"]["total"] == len(result["payload"]["tasks"]) == 8
                    assert result["payload"]["source"]["records_scanned"] == 12483
                else:
                    assert result is not None
                    assert result["total"] == len(result["tasks"]) == 8
                    assert result["source"]["records_scanned"] == 12483
                assert elapsed < 2.0
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            stderr = process.stderr.read(8192)
            diagnostic = dict(consumer=consumer, server_returncode=process.returncode)
            diagnostic.update(stderr_bytes_captured=len(stderr), stderr_limit=8192)
            print(json.dumps(diagnostic), flush=True)
            process.stderr.close()
