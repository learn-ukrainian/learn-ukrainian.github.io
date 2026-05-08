"""Streamable HTTP transport tests for the MCP sources server."""

from __future__ import annotations

import importlib.util
import socket
import threading
import time
from pathlib import Path

import httpx
import pytest
import uvicorn

SERVER_PATH = Path(__file__).resolve().parents[1] / ".mcp" / "servers" / "sources" / "server.py"


def _load_sources_server():
    spec = importlib.util.spec_from_file_location("mcp_sources_streamable_server", SERVER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture(scope="module")
def sources_http_url():
    module = _load_sources_server()
    port = _free_port()
    app = module.create_http_app()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)

    thread.start()
    base_url = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            response = httpx.get(f"{base_url}/health", timeout=0.5)
            if response.status_code == 200:
                break
        except httpx.HTTPError:
            time.sleep(0.05)
    else:
        server.should_exit = True
        thread.join(timeout=5)
        pytest.fail("MCP sources HTTP server did not start")

    yield base_url

    server.should_exit = True
    thread.join(timeout=5)


def test_streamable_http_initialize_returns_capabilities(sources_http_url):
    response = httpx.post(
        f"{sources_http_url}/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0"},
            },
        },
        timeout=5,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["jsonrpc"] == "2.0"
    assert body["id"] == 1
    assert "capabilities" in body["result"]


def test_streamable_http_tools_list_contains_verify_words(sources_http_url):
    response = httpx.post(
        f"{sources_http_url}/mcp",
        json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        timeout=5,
    )

    assert response.status_code == 200
    body = response.json()
    tool_names = {tool["name"] for tool in body["result"]["tools"]}
    assert "verify_words" in tool_names


def test_legacy_sse_endpoint_still_emits_message_endpoint(sources_http_url):
    text = ""
    timeout = httpx.Timeout(2.0, connect=2.0, read=2.0, write=2.0, pool=2.0)
    with httpx.stream("GET", f"{sources_http_url}/sse", timeout=timeout) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        for chunk in response.iter_text():
            text += chunk
            if "event: endpoint" in text and "data: /messages/?session_id=" in text:
                break

    assert "event: endpoint" in text
    assert "data: /messages/?session_id=" in text
