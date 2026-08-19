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


def test_streamable_http_get_mcp_returns_405_instead_of_hanging(sources_http_url):
    """Stateless JSON /mcp must 405 GET. An empty SSE hang is what disabled Cursor."""
    timeout = httpx.Timeout(1.0, connect=1.0, read=1.0, write=1.0, pool=1.0)
    response = httpx.get(
        f"{sources_http_url}/mcp",
        headers={"Accept": "text/event-stream", "MCP-Protocol-Version": "2025-06-18"},
        timeout=timeout,
    )
    assert response.status_code == 405
    assert "POST" in response.headers.get("allow", "")
    assert not response.headers.get("content-type", "").startswith("text/event-stream")


def test_streamable_http_delete_mcp_returns_405(sources_http_url):
    timeout = httpx.Timeout(1.0, connect=1.0, read=1.0, write=1.0, pool=1.0)
    response = httpx.delete(
        f"{sources_http_url}/mcp",
        headers={"MCP-Protocol-Version": "2025-06-18"},
        timeout=timeout,
    )
    assert response.status_code == 405
    assert "POST" in response.headers.get("allow", "")


def test_streamable_http_tools_list_contains_vocabulary_vetting_tools(sources_http_url):
    response = httpx.post(
        f"{sources_http_url}/mcp",
        json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        timeout=5,
    )

    assert response.status_code == 200
    body = response.json()
    tool_names = {tool["name"] for tool in body["result"]["tools"]}
    assert "verify_words" in tool_names
    assert "vet_vocabulary" in tool_names
    assert "search_images" not in tool_names


def test_streamable_http_tool_call_returns_valid_response(sources_http_url):
    """Sanity check: a real `tools/call` against the streamable-HTTP endpoint
    returns a valid MCP response. This is the path that historically suffered
    from an ASGI-message-order RuntimeError when the endpoint awaited the
    transport's terminate() after handle_request() — see the NOTE in
    .mcp/servers/sources/server.py near StreamableHTTPEndpoint. The bug was
    intermittent and tied to specific client/timing conditions, so this test
    doesn't try to guarantee error-log silence; it just guards that a
    well-formed tool call still produces a valid response shape end-to-end.
    """
    init_response = httpx.post(
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
    assert init_response.status_code == 200

    response = httpx.post(
        f"{sources_http_url}/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "verify_word",
                "arguments": {"word": "стіл"},
            },
        },
        timeout=10,
    )

    assert response.status_code == 200, f"tool call returned {response.status_code}"
    body = response.json()
    assert body["jsonrpc"] == "2.0"
    assert body["id"] == 2
    assert "result" in body, f"tool call missing result: {body}"
    content = body["result"].get("content", [])
    assert content, f"verify_word returned empty content: {body}"
    text_blob = content[0].get("text", "")
    # Acceptance: any one of two shapes proves the streamable-HTTP transport
    # round-tripped a real tool call (the test's actual subject).
    #   (a) `lemma` / `v_naz` — VESUM data present (local dev path).
    #   (b) explicit `Error in verify_word:` envelope — VESUM db missing on
    #       the runner; the tool caught it and returned a structured error
    #       through the MCP response channel (CI path). Earlier shape:
    #       FileNotFoundError surfaced via the JSON-RPC `content.text` field.
    # If both shapes are absent, the transport itself is broken (was the
    # original symptom of the ASGI bug we fixed at 8174ea3f52).
    has_vesum_data = "v_naz" in text_blob or "lemma" in text_blob
    has_tool_error_envelope = "Error in verify_word" in text_blob
    assert has_vesum_data or has_tool_error_envelope, (
        f"verify_word response is neither VESUM data nor structured error envelope; "
        f"transport likely broken. text_blob (truncated): {text_blob[:300]}"
    )


def test_legacy_sse_paths_are_not_advertised(sources_http_url):
    """Legacy SSE must not hang as a public GET (#7026). 404/405 are fine."""
    timeout = httpx.Timeout(2.0, connect=2.0, read=2.0, write=2.0, pool=2.0)
    sse_response = httpx.get(f"{sources_http_url}/sse", timeout=timeout)
    assert sse_response.status_code in {404, 405}
    assert not sse_response.headers.get("content-type", "").startswith("text/event-stream")

    messages_response = httpx.post(
        f"{sources_http_url}/messages/",
        content=b"{}",
        headers={"content-type": "application/json"},
        timeout=timeout,
    )
    assert messages_response.status_code in {404, 405}
