"""Boundary tests for the evaluator's provider runner and adapters."""

from __future__ import annotations

import json
import subprocess
from typing import Any

import pytest

from scripts.eval.zno_nmt import adapters, runner
from scripts.eval.zno_nmt.core import prepare_exam


def _packet() -> dict[str, Any]:
    return {
        "schema": "zno-nmt.questions.v1",
        "packet_sha256": "a" * 64,
        "items": [
            {
                "id": "opaque-1",
                "kind": "single",
                "question": "Питання",
                "options": [{"id": "A", "text": "Варіант"}],
                "rows": [],
            }
        ],
    }


def _config(**extra: Any) -> dict[str, Any]:
    config: dict[str, Any] = {
        "schema": "zno-nmt.config.v1",
        "adapter": "chat-http",
        "model": "local-test-model",
        "effort": None,
        "timeout_seconds": 15,
        "max_output_tokens": 100,
        "max_tool_calls": 2,
        "repeats": 1,
        "tools": ["verify_word"],
        "corpus_id": "fixture-corpus",
        "endpoint_env": "ZNO_NMT_ENDPOINT",
        "key_env": "ZNO_NMT_KEY",
    }
    config.update(extra)
    return config


def test_config_is_exact_and_sources_tools_are_proxy_allowlist() -> None:
    assert adapters.validate_config(_config())["tools"] == ["verify_word"]
    with pytest.raises(adapters.AdapterError, match="unsupported fields"):
        adapters.validate_config(_config(untrusted="value"))
    with pytest.raises(adapters.AdapterError, match="allowlisted"):
        adapters.validate_config(_config(tools=["search_external"]))
    with pytest.raises(adapters.AdapterError, match="allowlisted"):
        adapters.validate_config(_config(tools=["mcp__sources__verify_word"]))


def test_http_malicious_tool_never_reaches_broker(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ZNO_NMT_ENDPOINT", "https://example.invalid/chat")
    monkeypatch.setenv("ZNO_NMT_KEY", "secret-never-in-prompt")
    monkeypatch.setattr(adapters, "_mcp_list_tools", lambda *_args: ([{"name": "verify_word", "inputSchema": {"type": "object"}}], "server"))
    called = False

    def broker(*_args: Any, **_kwargs: Any) -> Any:
        nonlocal called
        called = True
        raise AssertionError("malicious call reached MCP broker")

    monkeypatch.setattr(adapters, "_mcp_call", broker)
    monkeypatch.setattr(
        adapters,
        "_http_json",
        lambda *_args, **_kwargs: {
            "model": "local-test-model",
            "choices": [{"message": {"tool_calls": [{"id": "call-1", "function": {"name": "mcp__sources__shell", "arguments": "{}"}}]}}],
        },
    )
    with pytest.raises(adapters.AdapterError, match="tool boundary"):
        adapters.run_chat_http(_packet(), _config(), "sources", sources_url="https://sources.invalid/mcp", prompt="exam")
    assert not called


def test_closed_book_http_sends_no_tools_or_runtime_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ZNO_NMT_ENDPOINT", "https://example.invalid/chat")
    monkeypatch.setenv("ZNO_NMT_KEY", "secret-never-in-prompt")
    captured: dict[str, Any] = {}

    def completion(_url: str, payload: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        captured.update(payload=payload, key=kwargs["key"])
        return {
            "model": "local-test-model",
            "choices": [{"message": {"content": json.dumps({"responses": {"opaque-1": "A"}})}}],
            "usage": {},
        }

    monkeypatch.setattr(adapters, "_http_json", completion)
    result = adapters.run_chat_http(_packet(), _config(), "closed-book", sources_url="https://sources.invalid/mcp", prompt="exam")
    assert "tools" not in captured["payload"]
    assert "secret-never-in-prompt" not in json.dumps(captured["payload"])
    assert captured["key"] == "secret-never-in-prompt"
    assert result["metrics"]["cost_usd"] is None
    assert result["metrics"]["input_tokens"] is None


def test_claude_empty_builtins_and_model_drift_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    config = _config(
        adapter="claude",
        endpoint_env=None,
        key_env=None,
        claude_bin="claude-fixture",
    )
    # The strict schema does not permit HTTP-only fields on the native adapter.
    del config["endpoint_env"]
    del config["key_env"]
    monkeypatch.setattr(adapters, "_claude_capabilities", lambda *_args, **_kwargs: ("claude-fixture", "2.1.fixture"))
    observed: dict[str, Any] = {}

    def fake_run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        observed.update(argv=argv, env=kwargs["env"], cwd=kwargs["cwd"], input=kwargs["prompt"])
        stdout = "\n".join(
            [
                json.dumps({"type": "system", "subtype": "init", "model": "wrong-model", "tools": []}),
                json.dumps({"type": "result", "result": json.dumps({"responses": {"opaque-1": "A"}})}),
            ]
        )
        return subprocess.CompletedProcess(argv, 0, stdout=stdout, stderr="provider output must not be retained")

    monkeypatch.setattr(adapters, "_run_claude_process", fake_run)
    with pytest.raises(adapters.AdapterError, match="model drift"):
        adapters.run_claude(_packet(), config, "closed-book", sources_url=None, prompt="exam")
    assert observed["argv"][observed["argv"].index("--tools") + 1] == ""
    assert "--strict-mcp-config" in observed["argv"]
    assert observed["env"]["CLAUDE_CODE_MAX_OUTPUT_TOKENS"] == "100"
    assert "CLAUDE_CODE_SIMPLE" not in observed["env"]
    assert "secret-never-in-prompt" not in observed["input"]


def test_claude_child_env_keeps_local_keychain_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USER", "fixture-user")
    monkeypatch.setenv("LOGNAME", "fixture-login")
    environment = adapters._child_env(100)
    assert environment["USER"] == "fixture-user"
    assert environment["LOGNAME"] == "fixture-login"
    assert "CLAUDE_CODE_SIMPLE" not in environment


def test_structured_output_tool_is_not_counted_as_retrieval() -> None:
    stdout = "\n".join(
        [
            json.dumps({"type": "system", "subtype": "init", "model": "fixture", "tools": ["StructuredOutput"]}),
            json.dumps({"type": "tool_use", "name": "StructuredOutput"}),
            json.dumps({"type": "result", "structured_output": {"responses": {"opaque-1": "A"}}}),
        ]
    )
    responses, model, calls, _usage = adapters._parse_stream_json(stdout, _packet(), set(), 1)
    assert responses == {"opaque-1": "A"}
    assert model == "fixture"
    assert calls == 0


def test_preflight_does_not_export_endpoint_or_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ZNO_NMT_ENDPOINT", "https://hidden.invalid/v1/chat/completions")
    monkeypatch.setenv("ZNO_NMT_KEY", "private-key")
    capability = adapters.preflight(_config(), "closed-book")
    rendered = json.dumps(capability)
    assert "hidden.invalid" not in rendered
    assert "private-key" not in rendered
    assert capability["capability"] == "chat-http-controller-mediated"


def test_mcp_identity_hashes_actual_safe_corpus_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    identity = {
        "server_code_sha256": "a" * 64,
        "sources_db_sha256": "b" * 64,
        "sources_db_bytes": 123,
        "vesum_db_sha256": "c" * 64,
        "vesum_db_bytes": 456,
    }
    calls: list[str] = []
    replies = iter(
        [
            {"result": {"serverInfo": {"name": "Sources"}}},
            {},
            {"result": {"tools": [
                {"name": "verify_word", "inputSchema": {"type": "object"}},
                {"name": "mcp_server_identity", "inputSchema": {"type": "object"}},
            ]}},
            {"result": {"content": [{"type": "text", "text": json.dumps(identity)}]}},
        ]
    )

    def request(_url: str, payload: dict[str, Any], _timeout: int, _session: str | None = None):
        calls.append(payload["method"])
        return next(replies), "session"

    monkeypatch.setattr(adapters, "_mcp_request", request)
    tools, identity_sha = adapters._mcp_list_tools("https://sources.invalid/mcp", 5)
    assert [tool["name"] for tool in tools] == ["verify_word", "mcp_server_identity"]
    assert identity_sha == adapters.digest(identity)
    assert calls == ["initialize", "notifications/initialized", "tools/list", "tools/call"]


def test_mcp_missing_identity_is_unknown_not_serverinfo_hash(monkeypatch: pytest.MonkeyPatch) -> None:
    replies = iter(
        [
            {"result": {"serverInfo": {"name": "Sources", "version": "different"}}},
            {},
            {"result": {"tools": [{"name": "verify_word", "inputSchema": {"type": "object"}}]}},
        ]
    )
    monkeypatch.setattr(adapters, "_mcp_request", lambda *_args: (next(replies), "session"))
    _tools, identity_sha = adapters._mcp_list_tools("https://sources.invalid/mcp", 5)
    assert identity_sha is None


def test_provider_json_rejects_duplicate_keys_and_nonfinite_numbers() -> None:
    with pytest.raises(adapters.AdapterError, match="duplicate"):
        adapters._strict_json_loads('{"responses":{},"responses":{}}')
    with pytest.raises(adapters.AdapterError, match="non-finite"):
        adapters._strict_json_loads('{"value":NaN}')


def test_response_schema_closes_every_object_and_preserves_item_kinds() -> None:
    packet = {
        "items": [
            {"id": "single", "kind": "single", "rows": []},
            {
                "id": "matching",
                "kind": "matching",
                "rows": [{"id": "row-1"}, {"id": "row-2"}],
            },
        ]
    }
    schema = adapters.response_schema(packet)

    def assert_closed(value: Any) -> None:
        if isinstance(value, dict):
            if value.get("type") == "object":
                assert value["additionalProperties"] is False
                assert set(value["required"]) == set(value["properties"])
            for child in value.values():
                assert_closed(child)
        elif isinstance(value, list):
            for child in value:
                assert_closed(child)

    assert_closed(schema)
    responses = schema["properties"]["responses"]["properties"]
    assert responses["single"] == {"anyOf": [{"type": "string"}, {"type": "null"}]}
    matching = responses["matching"]["anyOf"][0]
    assert matching["required"] == ["row-1", "row-2"]
    assert set(matching["properties"]) == {"row-1", "row-2"}
    assert "correct" not in json.dumps(schema)


def test_runner_retains_preflight_hashes_without_provider_logs(monkeypatch: pytest.MonkeyPatch) -> None:
    exam = {
        "schema": "zno-nmt.exam.v1", "title": "fixture", "subject": "Ukrainian", "year": 2022,
        "provenance": {"source_url": "https://example.invalid", "source_revision": "fixture", "license": "test", "exposure": "public"},
        "scoring": {"kind": "benchmark", "policy_url": None, "pass_threshold": None, "expected_items": 1, "expected_points": 1},
        "items": [{"id": "1", "kind": "single", "question": "Питання", "options": [{"id": "A", "text": "Варіант"}], "rows": [], "correct": "A"}],
    }
    packet, _key = prepare_exam(exam)
    cap = {"tool_schema_sha256": "b" * 64, "mcp_server_identity_sha256": "c" * 64}
    monkeypatch.setattr(runner, "preflight", lambda *_args, **_kwargs: cap)
    monkeypatch.setattr(runner.adapters, "build_prompt", lambda *_args: "exam")
    trial = {
        "responses": {"q0001": "A"},
        "identity": {"adapter": "chat-http", "harness": "chat-http", "model": "local-test-model", "effective_effort": "unknown"},
        "metrics": {"elapsed_seconds": 1.0, "input_tokens": None, "output_tokens": None, "total_tokens": None, "cost_usd": None, "tool_calls": 0},
    }
    monkeypatch.setattr(runner.adapters, "run_chat_http", lambda *_args, **_kwargs: trial)
    result = runner.run_exam(packet, _config(), "closed-book")
    assert result["status"] == "ok"
    assert result["identity"]["preflight_tool_schema_sha256"] == "b" * 64
    assert "provider output" not in json.dumps(result)
    assert result["comparison"]["constants_sha256"]


def test_native_timeout_kills_its_whole_process_group(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    seen: dict[str, Any] = {}

    class TimedOutProcess:
        pid = 321
        returncode = -9

        def communicate(self, _prompt: str | None = None, *, timeout: int | None = None):
            if timeout is not None:
                raise subprocess.TimeoutExpired("claude", timeout)
            return "", ""

        def kill(self) -> None:
            raise AssertionError("process-group kill should be preferred")

    def fake_popen(*_args: Any, **kwargs: Any) -> TimedOutProcess:
        seen.update(kwargs)
        return TimedOutProcess()

    monkeypatch.setattr(adapters.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(adapters.os, "killpg", lambda pid, sig: seen.update(kill=(pid, sig)))
    with pytest.raises(adapters.AdapterError, match="timeout"):
        adapters._run_claude_process(["claude"], cwd=tmp_path, env={}, prompt="exam", timeout=1)
    assert seen["start_new_session"] is True
    assert seen["kill"] == (321, adapters.signal.SIGKILL)
