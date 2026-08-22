"""Cycle 007 amendment step 3: hash-only privacy-mode tool-call logging.

Also covers step 4's additive ``cache_only`` option on ``query_ulif`` /
``query_grac`` — never a live fetch, fails closed to ``unavailable`` when no
cache is available.

Exercises the real ``_log_tool_call``/``call_tool`` functions (not a
reimplementation) against the repo's actual
``logs/mcp-sources-requests.jsonl`` — the same file real tool calls append
to — by recording the file's length before each call and reading only the
newly appended line(s) after.
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
from pathlib import Path

import pytest
import requests

SERVER_PATH = Path(__file__).resolve().parents[1] / ".mcp" / "servers" / "sources" / "server.py"
LOG_PATH = SERVER_PATH.parents[2].parent / "logs" / "mcp-sources-requests.jsonl"


def _load_sources_server():
    # The dynamically loaded server imports requests at module scope. Keep
    # this direct import visible to the changed-test fastlane dependency
    # planner so its slim environment matches the real runtime dependency.
    assert requests.__name__ == "requests"
    spec = importlib.util.spec_from_file_location("mcp_sources_privacy_logging_server", SERVER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def server():
    return _load_sources_server()


def _call_and_capture_log_entry(server, name: str, arguments: dict) -> dict:
    """Run one tool call and return the exact log entry it appended."""
    LOG_PATH.parent.mkdir(exist_ok=True)
    offset = LOG_PATH.stat().st_size if LOG_PATH.exists() else 0
    asyncio.run(server.call_tool(name, dict(arguments)))
    with open(LOG_PATH, "rb") as handle:
        handle.seek(offset)
        new_bytes = handle.read()
    lines = [line for line in new_bytes.decode("utf-8").splitlines() if line.strip()]
    assert len(lines) == 1, f"expected exactly one new log line, got {len(lines)}: {lines}"
    return json.loads(lines[0])


def test_privacy_mode_logs_no_argument_values(server):
    private_word = "СЕКРЕТНЕ_СЛОВО_НЕ_ДРУКУВАТИ"
    entry = _call_and_capture_log_entry(server, "check_russian_shadow", {"word": private_word, "_privacy_mode": True})
    assert entry["privacy_mode"] is True
    dumped = json.dumps(entry, ensure_ascii=False)
    assert private_word not in dumped
    assert "args" not in entry
    assert entry["arg_names"] == ["word"]
    assert entry["arg_count"] == 1
    assert len(entry["arg_sha256"]) == 64


def test_privacy_mode_logs_no_response_text(server):
    entry = _call_and_capture_log_entry(server, "check_russian_shadow", {"word": "тест", "_privacy_mode": True})
    assert "response_text" not in entry
    assert "response" not in entry
    assert entry["response_sha256"] is None or len(entry["response_sha256"]) == 64


def test_privacy_mode_error_never_leaks_the_exception_message(server):
    entry = _call_and_capture_log_entry(server, "verify_words", {"_privacy_mode": True})  # missing required "words"
    assert "error" not in entry  # the non-privacy full-message key must be absent
    assert "error_class" not in entry or "words" not in entry.get("error_class", "")


def test_non_privacy_mode_is_unchanged(server):
    entry = _call_and_capture_log_entry(server, "check_russian_shadow", {"word": "слово"})
    assert "privacy_mode" not in entry
    assert entry["args"] == {"word": "слово"}


def test_privacy_mode_flag_is_stripped_before_dispatch(server):
    """The reserved _privacy_mode key must never reach a tool handler/schema."""
    result = asyncio.run(server.call_tool("check_russian_shadow", {"word": "слово", "_privacy_mode": True}))
    text = result[0].text
    assert "_privacy_mode" not in text


def test_query_ulif_cache_only_never_makes_a_live_call(server):
    result = asyncio.run(server.call_tool("query_ulif", {"word": "стіл", "cache_only": True}))
    payload = json.loads(result[0].text)
    assert payload["status"] in {"attested", "not_found", "unavailable"}
    assert "entry" in payload


def test_query_grac_cache_only_always_unavailable(server):
    result = asyncio.run(server.call_tool("query_grac", {"query": "стіл", "cache_only": True}))
    payload = json.loads(result[0].text)
    assert payload["status"] == "unavailable"
    assert payload["entry"] is None


# --------------------------------------------------------------------------
# Amendment (fixes v3, item 2): MCP-wire fail-closed error results —
# ``_on_call_tool`` is the actual ``tools/call`` handler, distinct from the
# legacy ``call_tool`` module-level entry point exercised above.
# --------------------------------------------------------------------------


def _call_on_call_tool(server, name: str, arguments: dict):
    params = server.CallToolRequestParams(name=name, arguments=arguments)
    return asyncio.run(server._on_call_tool(None, params))


def test_on_call_tool_marks_a_handler_exception_iserror_true(server):
    private_word = "СЕКРЕТНЕ_СЛОВО_ІНТЕГРАЦІЙНОГО_ТЕСТУ"
    result = _call_on_call_tool(server, "verify_word", {"word_typo": private_word})
    assert result.is_error is True
    dumped = json.dumps([block.text for block in result.content])
    # No raw exception message or argument value ever reaches the wire result.
    assert private_word not in dumped
    assert "word_typo" not in dumped


def test_on_call_tool_marks_unknown_tool_iserror_true(server):
    result = _call_on_call_tool(server, "not_a_real_tool", {})
    assert result.is_error is True


def test_on_call_tool_success_is_iserror_false(server):
    result = _call_on_call_tool(server, "collection_stats", {})
    assert result.is_error is False


_SOURCES_DB = Path(__file__).resolve().parents[1] / "data" / "sources.db"
_VESUM_DB = Path(__file__).resolve().parents[1] / "data" / "vesum.db"


@pytest.mark.skipif(
    not (_SOURCES_DB.exists() and _VESUM_DB.exists()),
    reason="sources.db/vesum.db not present in this checkout — run locally for coverage",
)
def test_on_call_tool_mcp_server_identity_returns_public_safe_hashes(server):
    result = _call_on_call_tool(server, "mcp_server_identity", {})
    assert result.is_error is False
    payload = json.loads(result.content[0].text)
    assert set(payload) == {
        "server_code_sha256",
        "sources_db_sha256",
        "sources_db_bytes",
        "vesum_db_sha256",
        "vesum_db_bytes",
    }
    assert len(payload["server_code_sha256"]) == 64
    # Public-safe: never a filesystem path in the response.
    assert "/" not in payload["server_code_sha256"]


def test_call_tool_legacy_error_marker_never_appears_on_the_real_wire_path(server):
    """The legacy 'Error in ...' prose marker stays inside call_tool(); the real MCP path never emits it."""
    result = _call_on_call_tool(server, "verify_word", {})  # missing required "word"
    assert result.is_error is True
    for block in result.content:
        assert not block.text.startswith("Error in ")
