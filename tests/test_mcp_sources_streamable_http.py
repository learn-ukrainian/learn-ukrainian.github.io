"""Streamable HTTP transport tests for the MCP sources server."""

from __future__ import annotations

import importlib.util
import socket
import threading
import time
from pathlib import Path

import httpx
import prometheus_client  # noqa: F401  # Declares the Sources metrics dependency to the CI fastlane.
import pytest
import uvicorn

SERVER_PATH = Path(__file__).resolve().parents[1] / ".mcp" / "servers" / "sources" / "server.py"


def _load_sources_server():
    spec = importlib.util.spec_from_file_location("mcp_sources_streamable_server", SERVER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _metric_value(body: str, name: str, **labels: str) -> float:
    """Return one exposition sample. Missing series are zero."""
    wanted = tuple(sorted(labels.items()))
    total = 0.0
    for line in body.splitlines():
        if not line or line.startswith("#"):
            continue
        pieces = line.split()
        head = pieces[0]
        metric, separator, raw_labels = head.partition("{")
        if metric != name:
            continue
        parsed: list[tuple[str, str]] = []
        if separator:
            for item in raw_labels.rstrip("}").split(","):
                if not item:
                    continue
                key, _, quoted = item.partition("=")
                parsed.append((key, quoted.strip('"')))
        if tuple(sorted(parsed)) == wanted:
            total += float(pieces[1])
    return total


def _metrics_text(base_url: str) -> str:
    response = httpx.get(f"{base_url}/metrics", timeout=5)
    assert response.status_code == 200
    content_type = response.headers.get("content-type", "")
    assert content_type.startswith("text/plain")
    assert content_type.count("charset=") == 1
    assert "sources.db" not in response.text
    assert "query=" not in response.text
    return response.text


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
    before = _metrics_text(sources_http_url)
    again = httpx.post(
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
    assert again.status_code == 200
    after = _metrics_text(sources_http_url)
    assert _metric_value(after, "sources_mcp_requests_total", request_type="mcp", method="initialize", status="ok") == (
        _metric_value(before, "sources_mcp_requests_total", request_type="mcp", method="initialize", status="ok") + 1
    )
    assert _metric_value(
        after, "sources_mcp_request_errors_total", request_type="mcp", method="initialize", status="error"
    ) == _metric_value(
        before, "sources_mcp_request_errors_total", request_type="mcp", method="initialize", status="error"
    )
    assert _metric_value(
        after, "sources_mcp_request_duration_seconds_count", request_type="mcp", method="initialize", status="ok"
    ) == (
        _metric_value(
            before, "sources_mcp_request_duration_seconds_count", request_type="mcp", method="initialize", status="ok"
        )
        + 1
    )
    for status in ("2xx", "4xx", "5xx"):
        assert _metric_value(
            after, "sources_mcp_requests_total", request_type="http", method="POST", status=status
        ) == _metric_value(before, "sources_mcp_requests_total", request_type="http", method="POST", status=status)
    assert _metric_value(after, "sources_mcp_requests_total", request_type="health", method="GET", status="2xx") >= 1
    assert "sources_mcp_requests_total" in after
    assert "sources_mcp_request_errors_total" in after
    assert "sources_mcp_request_duration_seconds" in after

    # Legacy notifications are dispatched after the 202; modern HTTP accepts
    # and drops them. Neither path may add a phantom HTTP POST observation.
    for version in ("2025-06-18", "2026-07-28"):
        before = _metrics_text(sources_http_url)
        initialized = httpx.post(
            f"{sources_http_url}/mcp",
            headers={"MCP-Protocol-Version": version},
            json={"jsonrpc": "2.0", "method": "notifications/initialized"},
            timeout=5,
        )
        cancelled = httpx.post(
            f"{sources_http_url}/mcp",
            headers={"MCP-Protocol-Version": version},
            json={"jsonrpc": "2.0", "method": "notifications/cancelled", "params": {"requestId": 999}},
            timeout=5,
        )
        assert initialized.status_code == cancelled.status_code == 202
        after = _metrics_text(sources_http_url)
        for method in ("notifications/initialized", "notifications/cancelled"):
            assert _metric_value(
                after, "sources_mcp_requests_total", request_type="notification", method=method, status="ok"
            ) == _metric_value(
                before, "sources_mcp_requests_total", request_type="notification", method=method, status="ok"
            ) + 1
            assert _metric_value(
                after, "sources_mcp_request_duration_seconds_count", request_type="notification", method=method, status="ok"
            ) == _metric_value(
                before, "sources_mcp_request_duration_seconds_count", request_type="notification", method=method, status="ok"
            ) + 1
        assert _metric_value(
            after, "sources_mcp_requests_total", request_type="http", method="POST", status="2xx"
        ) == _metric_value(before, "sources_mcp_requests_total", request_type="http", method="POST", status="2xx")

    # An accepted JSON-RPC response never becomes an MCP middleware message.
    before = _metrics_text(sources_http_url)
    reply = httpx.post(
        f"{sources_http_url}/mcp",
        headers={"MCP-Protocol-Version": "2025-06-18"},
        json={"jsonrpc": "2.0", "id": 999, "result": {}},
        timeout=5,
    )
    assert reply.status_code == 202
    after = _metrics_text(sources_http_url)
    assert _metric_value(after, "sources_mcp_requests_total", request_type="http", method="POST", status="2xx") == (
        _metric_value(before, "sources_mcp_requests_total", request_type="http", method="POST", status="2xx") + 1
    )


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
    before = _metrics_text(sources_http_url)
    rejected = httpx.get(
        f"{sources_http_url}/mcp",
        headers={"Accept": "text/event-stream", "MCP-Protocol-Version": "2025-06-18"},
        timeout=timeout,
    )
    assert rejected.status_code == 405
    after = _metrics_text(sources_http_url)
    assert _metric_value(after, "sources_mcp_requests_total", request_type="http", method="GET", status="4xx") == (
        _metric_value(before, "sources_mcp_requests_total", request_type="http", method="GET", status="4xx") + 1
    )
    assert _metric_value(
        after, "sources_mcp_request_errors_total", request_type="http", method="GET", status="4xx"
    ) == _metric_value(before, "sources_mcp_request_errors_total", request_type="http", method="GET", status="4xx")


def test_streamable_http_delete_mcp_returns_405(sources_http_url):
    timeout = httpx.Timeout(1.0, connect=1.0, read=1.0, write=1.0, pool=1.0)
    response = httpx.delete(
        f"{sources_http_url}/mcp",
        headers={"MCP-Protocol-Version": "2025-06-18"},
        timeout=timeout,
    )
    assert response.status_code == 405
    assert "POST" in response.headers.get("allow", "")
    before = _metrics_text(sources_http_url)
    rejected = httpx.delete(
        f"{sources_http_url}/mcp",
        headers={"MCP-Protocol-Version": "2025-06-18"},
        timeout=timeout,
    )
    assert rejected.status_code == 405
    after = _metrics_text(sources_http_url)
    assert _metric_value(after, "sources_mcp_requests_total", request_type="http", method="DELETE", status="4xx") == (
        _metric_value(before, "sources_mcp_requests_total", request_type="http", method="DELETE", status="4xx") + 1
    )
    assert _metric_value(
        after, "sources_mcp_request_errors_total", request_type="http", method="DELETE", status="4xx"
    ) == _metric_value(
        before, "sources_mcp_request_errors_total", request_type="http", method="DELETE", status="4xx"
    )


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
    before = _metrics_text(sources_http_url)
    listed = httpx.post(
        f"{sources_http_url}/mcp",
        json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        timeout=5,
    )
    assert listed.status_code == 200
    after = _metrics_text(sources_http_url)
    assert _metric_value(after, "sources_mcp_requests_total", request_type="mcp", method="tools/list", status="ok") == (
        _metric_value(before, "sources_mcp_requests_total", request_type="mcp", method="tools/list", status="ok") + 1
    )
    assert _metric_value(
        after, "sources_mcp_request_errors_total", request_type="mcp", method="tools/list", status="error"
    ) == _metric_value(
        before, "sources_mcp_request_errors_total", request_type="mcp", method="tools/list", status="error"
    )
    assert "verify_words" not in after
    assert "vet_vocabulary" not in after


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
    # Acceptance: any one of these shapes proves the streamable-HTTP transport
    # round-tripped a real tools/call (the test's actual subject).
    #   (a) `lemma` / `v_naz` — VESUM data present (local / cached-db path).
    #   (b) fail-closed MCP-wire envelope ``Tool call failed: verify_word.`` —
    #       the real `_on_call_tool` path (Cycle007 fixes v3 / c28df06).
    #       Handler exceptions (VESUM db missing on the runner, KeyError on
    #       a bad argument, …) are isError=True with a privacy-safe generic
    #       text; the raw exception never leaves the process. This is the
    #       merge_group CI path. The legacy ``Error in verify_word:`` prose
    #       stays on the in-process `call_tool()` helper only — see
    #       test_call_tool_legacy_error_marker_never_appears_on_the_real_wire_path.
    # If none of these shapes appear, the transport itself is broken (was
    # the original symptom of the ASGI bug we fixed at 8174ea3f52).
    has_vesum_data = "v_naz" in text_blob or "lemma" in text_blob
    has_fail_closed_envelope = "Tool call failed: verify_word" in text_blob
    has_legacy_inprocess_envelope = "Error in verify_word" in text_blob
    assert has_vesum_data or has_fail_closed_envelope or has_legacy_inprocess_envelope, (
        f"verify_word response is neither VESUM data nor structured error envelope; "
        f"transport likely broken. text_blob (truncated): {text_blob[:300]}"
    )
    before = _metrics_text(sources_http_url)
    repeated = httpx.post(
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
    assert repeated.status_code == 200
    repeated_failed = repeated.json()["result"].get("isError", False) is True
    after = _metrics_text(sources_http_url)
    outcome = "error" if repeated_failed else "ok"
    assert _metric_value(
        after, "sources_mcp_requests_total", request_type="mcp", method="tools/call", status=outcome
    ) == (
        _metric_value(before, "sources_mcp_requests_total", request_type="mcp", method="tools/call", status=outcome) + 1
    )
    other = "ok" if repeated_failed else "error"
    assert _metric_value(
        after, "sources_mcp_requests_total", request_type="mcp", method="tools/call", status=other
    ) == _metric_value(before, "sources_mcp_requests_total", request_type="mcp", method="tools/call", status=other)
    assert _metric_value(
        after, "sources_mcp_request_errors_total", request_type="mcp", method="tools/call", status="error"
    ) == (
        _metric_value(
            before, "sources_mcp_request_errors_total", request_type="mcp", method="tools/call", status="error"
        )
        + (1 if repeated_failed else 0)
    )
    assert "стіл" not in after
    assert "verify_word" not in after


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
    before = _metrics_text(sources_http_url)
    sse_again = httpx.get(f"{sources_http_url}/sse", timeout=timeout)
    messages_again = httpx.post(
        f"{sources_http_url}/messages/",
        content=b"{}",
        headers={"content-type": "application/json"},
        timeout=timeout,
    )
    assert sse_again.status_code in {404, 405}
    assert messages_again.status_code in {404, 405}
    after = _metrics_text(sources_http_url)
    assert _metric_value(after, "sources_mcp_requests_total", request_type="http", method="GET", status="4xx") == (
        _metric_value(before, "sources_mcp_requests_total", request_type="http", method="GET", status="4xx") + 1
    )
    assert _metric_value(after, "sources_mcp_requests_total", request_type="http", method="POST", status="4xx") == (
        _metric_value(before, "sources_mcp_requests_total", request_type="http", method="POST", status="4xx") + 1
    )
    assert "/sse" not in after
    assert "/messages" not in after
    assert "clientInfo" not in after
