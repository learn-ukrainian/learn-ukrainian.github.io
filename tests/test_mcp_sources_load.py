"""AC-01 (#10674): /health stays fast while the sources server is saturated.

A real uvicorn instance serves the real HTTP app. One tool is replaced by a
call that blocks a worker thread, then 120 concurrent tool calls and 150
stalled (slow-loris style) connections arrive while /health is probed. A
second run makes every call time out: the work of timed-out calls must still
count against the bound until it finishes.
"""

from __future__ import annotations

import asyncio
import importlib.util
import socket
import threading
import time
from pathlib import Path

import httpx
import pytest
import uvicorn

SERVER_PATH = Path(__file__).resolve().parents[1] / ".mcp" / "servers" / "sources" / "server.py"
MAX_CONCURRENT = 12
CALLS = 120
CALL_SECONDS = 0.5
STALLED_CONNECTIONS = 150


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture
def saturated_server(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    yield from _serve(monkeypatch, tmp_path, call_timeout=30.0, call_seconds=CALL_SECONDS)


@pytest.fixture
def timing_out_server(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    yield from _serve(monkeypatch, tmp_path, call_timeout=0.2, call_seconds=1.5)


def _serve(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, *, call_timeout: float, call_seconds: float):
    monkeypatch.setenv("LU_SOURCES_MAX_CONCURRENT_CALLS", str(MAX_CONCURRENT))
    monkeypatch.setenv("LU_SOURCES_QUEUE_TIMEOUT_S", "60")
    monkeypatch.setenv("LU_SOURCES_CALL_TIMEOUT_S", str(call_timeout))
    monkeypatch.setenv("LU_SOURCES_DUMP_DIR", str(tmp_path / "dumps"))
    monkeypatch.setenv("LU_MCP_SOURCES_LOG_DIR", str(tmp_path / "logs"))
    spec = importlib.util.spec_from_file_location("mcp_sources_load_server", SERVER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    lock = threading.Lock()
    stats = {"running": 0, "peak": 0}

    def blocking_work() -> None:
        with lock:
            stats["running"] += 1
            stats["peak"] = max(stats["peak"], stats["running"])
        time.sleep(call_seconds)
        with lock:
            stats["running"] -= 1

    async def saturating_tool(_arguments: dict) -> list:
        await asyncio.to_thread(blocking_work)
        return [module.TextContent(type="text", text="saturating tool done")]

    module.handle_collection_stats = saturating_tool
    port = _free_port()
    config = uvicorn.Config(module.create_http_app(), host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            if httpx.get(f"{base_url}/health", timeout=0.5).status_code == 200:
                break
        except httpx.HTTPError:
            time.sleep(0.05)
    else:
        server.should_exit = True
        pytest.fail("sources HTTP server did not start")
    yield base_url, port, stats
    server.should_exit = True
    thread.join(timeout=10)


async def _load(base_url: str, port: int) -> tuple[list[float], list[httpx.Response]]:
    stalled = []
    for _ in range(STALLED_CONNECTIONS):
        _reader, writer = await asyncio.open_connection("127.0.0.1", port)
        writer.write(b"POST /mcp HTTP/1.1\r\nHost: 127.0.0.1\r\nContent-Length: 500\r\n\r\n{")
        stalled.append(writer)
    limits = httpx.Limits(max_connections=CALLS + 10, max_keepalive_connections=0)
    async with httpx.AsyncClient(limits=limits, timeout=60) as client:

        async def tool_call(number: int) -> httpx.Response:
            payload = {
                "jsonrpc": "2.0",
                "id": number,
                "method": "tools/call",
                "params": {"name": "collection_stats", "arguments": {}},
            }
            return await client.post(f"{base_url}/mcp", json=payload)

        calls = [asyncio.create_task(tool_call(number)) for number in range(CALLS)]
        latencies: list[float] = []
        while not all(call.done() for call in calls):
            started = time.monotonic()
            async with httpx.AsyncClient(timeout=5) as probe:
                response = await probe.get(f"{base_url}/health")
            assert response.status_code == 200
            latencies.append(time.monotonic() - started)
            await asyncio.sleep(0.1)
        responses = await asyncio.gather(*calls)
    for writer in stalled:
        writer.close()
    return latencies, responses


def test_health_stays_under_one_second_while_saturated(saturated_server) -> None:
    base_url, port, stats = saturated_server
    latencies, responses = asyncio.run(_load(base_url, port))
    assert len(latencies) >= 10
    assert max(latencies) < 1.0, f"slowest /health {max(latencies):.3f}s"
    assert all(response.status_code == 200 for response in responses)
    texts = [response.json()["result"]["content"][0]["text"] for response in responses]
    assert texts == ["saturating tool done"] * CALLS
    assert stats["peak"] == MAX_CONCURRENT


def test_timed_out_calls_keep_counting_against_the_bound(timing_out_server) -> None:
    """Blocker 1 end to end: 120 calls time out, yet at most 12 workers ever run."""
    base_url, _port, stats = timing_out_server

    async def calls() -> tuple[list[str], list[float]]:
        limits = httpx.Limits(max_connections=CALLS + 10, max_keepalive_connections=0)
        async with httpx.AsyncClient(limits=limits, timeout=30) as client:

            async def tool_call(number: int) -> str:
                payload = {
                    "jsonrpc": "2.0",
                    "id": number,
                    "method": "tools/call",
                    "params": {"name": "collection_stats", "arguments": {"probe": "секрет"}},
                }
                response = await client.post(f"{base_url}/mcp", json=payload)
                assert response.status_code == 200
                return response.json()["result"]["content"][0]["text"]

            texts = await asyncio.gather(*(tool_call(number) for number in range(CALLS)))
            latencies = []
            for _ in range(5):
                started = time.monotonic()
                assert (await client.get(f"{base_url}/health")).status_code == 200
                latencies.append(time.monotonic() - started)
            # Once the abandoned work ends, its slots are free again.
            deadline = time.monotonic() + 10
            while stats["running"] and time.monotonic() < deadline:
                await asyncio.sleep(0.05)
            texts.append(await tool_call(CALLS))
            return texts, latencies

    texts, latencies = asyncio.run(calls())
    timed_out = [text for text in texts[:CALLS] if "(call_timeout: " in text]
    overloaded = [text for text in texts[:CALLS] if "(server_overloaded: " in text]
    assert len(timed_out) == MAX_CONCURRENT
    assert len(overloaded) == CALLS - MAX_CONCURRENT
    assert all(text.startswith("Tool call failed: collection_stats (") for text in texts)
    assert not any("секрет" in text for text in texts)
    assert stats["peak"] == MAX_CONCURRENT
    assert max(latencies) < 1.0
    # Admitted again (it times out on its own 1.5 s of work), not refused as overloaded.
    assert "(call_timeout: " in texts[-1]
