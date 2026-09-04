"""PR #7662 repair 7: the Sources MCP wire handler as a real invocation
attester.

These tests drive the actual ``_dispatch_tool_call`` path -- the same one
the MCP ``tools/call`` handler uses -- so the opt-in V4 evidentiary bundle,
the argument-derived identifier, and the canonical write are exercised as
wiring, not as a unit-tested helper in isolation. The tool handler is
replaced with a controlled, source-free stub (no sources/vesum database is
touched), and the canonical authority opener is pointed at an isolated
``tmp_path`` plane. There is no argument, environment variable or admission
switch that could do either of those in production.
"""

from __future__ import annotations

import asyncio
import importlib.util
import sys
from pathlib import Path
from typing import Any

import mcp  # noqa: F401  # Declares the Sources wire dependency to the CI fastlane.
import pytest

from scripts.fleet_comms import v4_canonical_authority_store as v4_store
from scripts.fleet_comms.artifacts import ArtifactStore

SOURCES_SERVER_PATH = Path(__file__).resolve().parents[1] / ".mcp" / "servers" / "sources" / "server.py"

ROW_SHA = "b" * 64
GENUINE_RESULT = "книга | VESUM: valid (lemma=книга, id=vesum:12345, tag=noun)"


@pytest.fixture
def server_module():
    spec = importlib.util.spec_from_file_location("sources_server_v4", SOURCES_SERVER_PATH)
    srv = importlib.util.module_from_spec(spec)
    sys.modules["sources_server_v4"] = srv
    spec.loader.exec_module(srv)
    return srv


@pytest.fixture
def isolated_plane(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(
        v4_store,
        "open_production_authority_store",
        lambda *, write=False: ArtifactStore(root=tmp_path),
    )
    return tmp_path


def _stub_handler(server_module: Any, monkeypatch: pytest.MonkeyPatch, text: str = GENUINE_RESULT) -> list[dict[str, Any]]:
    """Replace the real tool with a controlled result and capture the exact
    arguments the handler was invoked with."""
    seen: list[dict[str, Any]] = []

    async def _handler(args: dict[str, Any]) -> list[Any]:
        seen.append(dict(args))
        return [server_module.TextContent(type="text", text=text)]

    monkeypatch.setattr(server_module, "handle_verify_word", _handler)
    return seen


def _call(server_module: Any, arguments: dict[str, Any]) -> tuple[list[Any], bool]:
    return asyncio.run(server_module._dispatch_tool_call("verify_word", arguments))


def _recorded(tmp_path: Path) -> list[dict[str, Any]]:
    with ArtifactStore(root=tmp_path) as store:
        rows = store.connection.execute("SELECT record_json FROM v4_sources_invocations").fetchall()
    import json

    return [json.loads(str(row["record_json"])) for row in rows]


def test_genuine_call_is_recorded_with_an_argument_derived_identifier(server_module, isolated_plane, monkeypatch):
    seen = _stub_handler(server_module, monkeypatch)
    _content, is_error = _call(
        server_module,
        {
            "word": "книга",
            "_v4_evidence_request_id": "req-1",
            "_v4_evidence_row_content_sha256": ROW_SHA,
            "_v4_evidence_lookup_ids": ["vesum:12345"],
        },
    )
    assert is_error is False
    # The opt-in bundle never reaches the real handler.
    assert seen == [{"word": "книга"}]
    records = _recorded(isolated_plane)
    assert len(records) == 1
    assert records[0]["identifier"] == "книга"
    assert records[0]["tool_id"] == "mcp__sources__verify_word"
    assert records[0]["request_id"] == "req-1"
    assert records[0]["success"] is True
    # The tool version is the running server's own code digest, not a
    # caller-supplied or hard-coded string.
    assert records[0]["tool_version"] == server_module._v4_server_code_digest()


def test_a_caller_declared_identifier_is_ignored_entirely(server_module, isolated_plane, monkeypatch):
    """The retired ``_v4_evidence_identifier`` cannot describe an invocation
    that did not happen: it is dropped, and the identifier still comes from
    the arguments the tool really ran on."""
    seen = _stub_handler(server_module, monkeypatch)
    _call(
        server_module,
        {
            "word": "книга",
            "_v4_evidence_identifier": "totally-made-up",
            "_v4_evidence_request_id": "req-1",
            "_v4_evidence_row_content_sha256": ROW_SHA,
            "_v4_evidence_lookup_ids": ["vesum:12345"],
        },
    )
    assert seen == [{"word": "книга"}], "the retired key must not leak into the real handler"
    records = _recorded(isolated_plane)
    assert len(records) == 1
    assert records[0]["identifier"] == "книга"


def test_an_ordinary_call_records_nothing(server_module, isolated_plane, monkeypatch):
    _stub_handler(server_module, monkeypatch)
    _call(server_module, {"word": "книга"})
    assert _recorded(isolated_plane) == []


@pytest.mark.parametrize(
    ("bundle", "why"),
    [
        pytest.param({"_v4_evidence_lookup_ids": ["vesum:99999"]}, "claim absent from the genuine result", id="fabricated-claim"),
        pytest.param({"_v4_evidence_lookup_ids": ["123"]}, "substring coincidence inside vesum:12345", id="substring-coincidence"),
        pytest.param({"_v4_evidence_row_content_sha256": "not-a-digest"}, "malformed row binding", id="malformed-row-binding"),
    ],
)
def test_a_fabricated_claim_is_never_recorded(server_module, isolated_plane, monkeypatch, bundle, why):
    _stub_handler(server_module, monkeypatch)
    arguments = {
        "word": "книга",
        "_v4_evidence_request_id": "req-1",
        "_v4_evidence_row_content_sha256": ROW_SHA,
        "_v4_evidence_lookup_ids": ["vesum:12345"],
    }
    arguments.update(bundle)
    _content, is_error = _call(server_module, arguments)
    assert is_error is False, "recording is additive; it must never break the tool call itself"
    assert _recorded(isolated_plane) == [], why


def test_a_failed_tool_call_records_nothing(server_module, isolated_plane, monkeypatch):
    async def _boom(args: dict[str, Any]) -> list[Any]:
        raise RuntimeError("tool failed")

    monkeypatch.setattr(server_module, "handle_verify_word", _boom)
    _content, is_error = _call(
        server_module,
        {
            "word": "книга",
            "_v4_evidence_request_id": "req-1",
            "_v4_evidence_row_content_sha256": ROW_SHA,
            "_v4_evidence_lookup_ids": ["vesum:12345"],
        },
    )
    assert is_error is True
    assert _recorded(isolated_plane) == []


def test_recording_failure_never_breaks_the_tool_call(server_module, monkeypatch):
    """With no canonical PostgreSQL authority available (the default in any
    developer shell), the call still succeeds and simply records nothing."""
    _stub_handler(server_module, monkeypatch)
    content, is_error = _call(
        server_module,
        {
            "word": "книга",
            "_v4_evidence_request_id": "req-1",
            "_v4_evidence_row_content_sha256": ROW_SHA,
            "_v4_evidence_lookup_ids": ["vesum:12345"],
        },
    )
    assert is_error is False
    assert content[0].text == GENUINE_RESULT
