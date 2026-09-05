"""PR #7662 repair 8: Sources MCP wire records only authenticated attempts.

Caller ``_v4_evidence_*`` correlation arguments are discarded and cannot
mint authority. Recording requires a real PG-resolved running capability and a
typed handler outcome. These transport unit tests supply typed outcomes; real
HTTP and lexical-input mechanism proofs live in test_v4_protected_parent_mechanism. These tests drive ``_dispatch_tool_call`` — the same
path ``tools/call`` uses — against an isolated plane. There is no argument,
environment variable, or admission switch that could do this in production.
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import mcp  # noqa: F401  # Declares the Sources wire dependency to the CI fastlane.
import pytest
from learn_ukrainian_v4_runtime import sources_transport
from learn_ukrainian_v4_runtime.operation_auth import digest
from learn_ukrainian_v4_runtime.resources import read_bytes
from psycopg.conninfo import make_conninfo

# Shared test-only PostgreSQL setup; the product is an installed dependency.
sys.path.insert(0, str(Path(__file__).parent / "projects/open_model_data"))
from test_v4_operation_lifecycle import claim, role_connection

pytest_plugins = ("test_v4_operation_lifecycle",)

SOURCES_SERVER_PATH = Path(__file__).resolve().parents[1] / ".mcp" / "servers" / "sources" / "server.py"
TYPED_IDENTIFIER = "vesum:" + "a" * 64
TYPED_SUPPORTED = {
    "tool": "verify_word",
    "disposition": "supported",
    "success": True,
    "evidence_identifiers": [TYPED_IDENTIFIER],
    "result": {"word": "книга", "matches": [{"lemma": "книга"}]},
}


@pytest.fixture
def server_module():
    spec = importlib.util.spec_from_file_location("sources_server_v4", SOURCES_SERVER_PATH)
    srv = importlib.util.module_from_spec(spec)
    sys.modules["sources_server_v4"] = srv
    spec.loader.exec_module(srv)
    return srv


@pytest.fixture
def isolated_plane(tmp_path, monkeypatch, pg_cluster):
    # Only this owned ephemeral cluster receives LOGIN. Production grants are
    # separately controlled deployment work.
    pg_cluster.execute("ALTER ROLE hramatka_v4_sources_writer LOGIN")
    credential = tmp_path / "sources-dsn"
    credential.write_text(make_conninfo(pg_cluster.info.dsn, user="hramatka_v4_sources_writer"))
    credential.chmod(0o600)
    monkeypatch.setattr(sources_transport, "credential_path", lambda: credential)
    pg_cluster.execute("DELETE FROM v4_sources_invocations")
    return pg_cluster


def _stub_handler(server_module: Any, monkeypatch: pytest.MonkeyPatch, *, typed: dict[str, Any] | None = TYPED_SUPPORTED, text: str = "книга — FOUND") -> list[dict[str, Any]]:
    seen: list[dict[str, Any]] = []

    async def _handler(args: dict[str, Any]) -> Any:
        seen.append(dict(args))
        content = [server_module.TextContent(type="text", text=text)]
        if typed is None:
            return content
        return content, typed

    monkeypatch.setattr(server_module, "handle_verify_word", _handler)
    return seen


def _call(server_module: Any, arguments: dict[str, Any]) -> tuple[list[Any], bool, dict[str, Any] | None]:
    return asyncio.run(server_module._dispatch_tool_call("verify_word", arguments))


def _recorded(pg):
    rows = pg.execute("SELECT record_json FROM v4_sources_invocations").fetchall()
    return [json.loads(str(row["record_json"])) for row in rows]


def _running_attempt(pg, prepared):
    with role_connection(pg, "hramatka_v4_control_writer") as conn:
        owned = claim(conn, prepared)
    # Resolve the actual capability through the real scoped stored operation.
    resolved = sources_transport.resolve_attempt(owned["capability_token"])
    assert resolved["attempt_id"] == owned["attempt_id"]
    return resolved


def test_dispatch_returns_a_typed_outcome_tuple(server_module, isolated_plane, monkeypatch):
    _stub_handler(server_module, monkeypatch)
    content, is_error, typed = _call(server_module, {"word": "книга"})
    assert is_error is False
    assert content[0].text
    assert typed == TYPED_SUPPORTED


def test_caller_v4_evidence_args_are_discarded_and_record_nothing(server_module, isolated_plane, monkeypatch):
    seen = _stub_handler(server_module, monkeypatch)
    content, is_error, _typed = _call(
        server_module,
        {
            "word": "книга",
            "_v4_evidence_request_id": "req-1",
            "_v4_evidence_row_content_sha256": "b" * 64,
            "_v4_evidence_lookup_ids": ["vesum:12345"],
            "_v4_evidence_identifier": "totally-made-up",
        },
    )
    assert is_error is False
    assert seen == [{"word": "книга"}]
    assert _recorded(isolated_plane) == []
    assert "totally-made-up" not in content[0].text


def test_an_ordinary_call_records_nothing(server_module, isolated_plane, monkeypatch):
    _stub_handler(server_module, monkeypatch)
    _call(server_module, {"word": "книга"})
    assert _recorded(isolated_plane) == []


def test_authenticated_attempt_records_a_server_derived_identifier(server_module, isolated_plane, monkeypatch, prepared):
    claim = _running_attempt(isolated_plane, prepared)
    _stub_handler(server_module, monkeypatch)
    token = server_module._V4_ACTIVE_ATTEMPT.set(claim)
    try:
        _content, is_error, typed = _call(server_module, {"word": "книга"})
    finally:
        server_module._V4_ACTIVE_ATTEMPT.reset(token)
    assert is_error is False
    assert typed is not None
    records = _recorded(isolated_plane)
    assert len(records) == 1
    assert records[0]["identifier"] == TYPED_IDENTIFIER
    assert records[0]["identifier"] != "книга"
    assert records[0]["tool_id"] == "mcp__sources__verify_word"
    assert records[0]["attempt_id"] == claim["attempt_id"]
    assert records[0]["success"] is True
    assert records[0]["tool_version"] == digest(read_bytes("sources_handlers.py"))


def test_unsuccessful_typed_outcome_is_stored_but_not_successful(server_module, isolated_plane, monkeypatch, prepared):
    claim = _running_attempt(isolated_plane, prepared)
    typed = {
        "tool": "verify_word",
        "disposition": "not_found",
        "success": False,
        "evidence_identifiers": [],
        "result": {"word": "книга", "matches": []},
    }
    _stub_handler(server_module, monkeypatch, typed=typed, text="NOT FOUND")
    token = server_module._V4_ACTIVE_ATTEMPT.set(claim)
    try:
        _content, is_error, _typed = _call(server_module, {"word": "книга"})
    finally:
        server_module._V4_ACTIVE_ATTEMPT.reset(token)
    assert is_error is False
    records = _recorded(isolated_plane)
    assert len(records) == 1
    assert records[0]["success"] is False
    assert records[0]["disposition"] == "not_found"


def test_a_failed_tool_call_records_nothing(server_module, isolated_plane, monkeypatch, prepared):
    claim = _running_attempt(isolated_plane, prepared)

    async def _boom(args: dict[str, Any]) -> list[Any]:
        raise RuntimeError("tool failed")

    monkeypatch.setattr(server_module, "handle_verify_word", _boom)
    token = server_module._V4_ACTIVE_ATTEMPT.set(claim)
    try:
        _content, is_error, typed = _call(server_module, {"word": "книга"})
    finally:
        server_module._V4_ACTIVE_ATTEMPT.reset(token)
    assert is_error is True
    assert typed is None
    assert _recorded(isolated_plane) == []


def test_recording_failure_never_breaks_the_tool_call(server_module, monkeypatch):
    """With no canonical authority available, the call still succeeds."""
    _stub_handler(server_module, monkeypatch)
    content, is_error, typed = _call(server_module, {"word": "книга"})
    assert is_error is False
    assert typed == TYPED_SUPPORTED
    assert content[0].text == "книга — FOUND"
