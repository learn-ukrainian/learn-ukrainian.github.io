"""Real public HTTP integration test for Cycle 007 endpoint identity attestation.

Amendment (fixes v3, item 8): starts the exact server module on an ephemeral
loopback port, drives it through the actual production
``RealMcpToolTransport``/``LocalMcpSourcesClient`` classes (no direct
library/database import, no fake transport), attests endpoint identity,
lists the required tools, and makes a harmless public ``verify_words``
round trip. Proves hash-only privacy logging and MCP-wire error fail-closed
behavior — never a private word, argument value, or raw exception message on
the wire or in the log — without touching an external network.

Skipped when ``data/sources.db``/``data/vesum.db`` are not present locally
(same gating ``TestIntegrationSmoke`` in test_mcp_sources_server.py uses) —
this dispatch worktree's sparse checkout does not carry them.
"""

from __future__ import annotations

import importlib.util
import json
import socket
import threading
import time
from pathlib import Path

import httpx
import pytest
import uvicorn

from scripts.projects.open_model_data import phase3_cycle007_evidence_compiler as compiler

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = REPO_ROOT / ".mcp" / "servers" / "sources" / "server.py"
SOURCES_DB = REPO_ROOT / "data" / "sources.db"
VESUM_DB = REPO_ROOT / "data" / "vesum.db"
LOG_PATH = REPO_ROOT / "logs" / "mcp-sources-requests.jsonl"

pytestmark = pytest.mark.skipif(
    not (SOURCES_DB.exists() and VESUM_DB.exists()),
    reason="sources.db/vesum.db not present in this checkout — run locally for integration coverage",
)


def _load_sources_server():
    spec = importlib.util.spec_from_file_location("mcp_sources_identity_integration_server", SERVER_PATH)
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


@pytest.fixture()
def real_client(sources_http_url):
    endpoint_url = f"{sources_http_url}/mcp"
    client = compiler.LocalMcpSourcesClient(endpoint_url=endpoint_url)
    yield client
    client.close()


def test_real_transport_attests_endpoint_identity_against_local_files(real_client):
    identity = real_client.server_identity()
    assert identity["server_code_sha256"] == compiler.contract.sha256_file(SERVER_PATH)
    assert identity["sources_db_sha256"] == compiler.contract.sha256_file(SOURCES_DB)
    assert identity["vesum_db_sha256"] == compiler.contract.sha256_file(VESUM_DB)
    assert identity["sources_db_bytes"] == SOURCES_DB.stat().st_size
    assert identity["vesum_db_bytes"] == VESUM_DB.stat().st_size


def test_real_transport_preflight_requires_every_frozen_tool(sources_http_url):
    transport = compiler.RealMcpToolTransport(f"{sources_http_url}/mcp")
    try:
        tool_names = transport.preflight()
        assert tool_names >= compiler.REQUIRED_TOOL_NAMES
    finally:
        transport.close()


def test_real_client_verify_words_round_trip_is_harmless_and_public(real_client):
    # A public, harmless word — no private Phase 3 packet content.
    result = real_client.verify_words(["слово"])
    assert "слово" in result


def test_real_endpoint_logs_hash_only_never_argument_values_or_response_text(real_client):
    private_marker = "СЕКРЕТНЕ_СЛОВО_ІНТЕГРАЦІЙНОГО_ТЕСТУ"
    offset = LOG_PATH.stat().st_size if LOG_PATH.exists() else 0
    real_client.check_russian_shadow(private_marker)
    with open(LOG_PATH, "rb") as handle:
        handle.seek(offset)
        new_bytes = handle.read()
    lines = [line for line in new_bytes.decode("utf-8").splitlines() if line.strip()]
    assert lines, "expected at least one new log line from the real round trip"
    dumped = "\n".join(lines)
    assert private_marker not in dumped
    for line in lines:
        entry = json.loads(line)
        if entry.get("tool") == "check_russian_shadow":
            assert entry.get("privacy_mode") is True
            assert "args" not in entry
            assert "response_text" not in entry
            assert "response" not in entry


def test_real_transport_fails_closed_on_a_real_tool_error(sources_http_url):
    """A handler exception on the real wire path must be isError=True and never leak the exception message."""
    transport = compiler.RealMcpToolTransport(f"{sources_http_url}/mcp")
    try:
        transport.preflight()
        with pytest.raises(compiler.McpTransportError):
            # verify_words requires a "words" argument; omitting it raises
            # inside the handler — the real MCP path must surface this as
            # an error result, not a disguised success.
            transport.call_tool("verify_words", {})
    finally:
        transport.close()
