"""Tests for ACPX shadow seats — Codex (#6027) and Grok (#6043).

The NDJSON transcripts below (inlined as module-level constants rather than
``tests/fixtures/acpx/*.ndjson`` files, to keep this seat's changed-file
footprint bounded) are bounded fixtures. ``_TIMEOUT_NDJSON``, and the shape of
``_AUTH_REQUIRED_NDJSON`` / ``_AGENT_DISCONNECTED_NDJSON``, mirror
byte-for-byte or structurally the real output captured live against the
pinned local ``acpx@0.13.0`` binary and the
``acpxCode``/``detailCode``/``EXIT_CODES`` constants read directly out of
``node_modules/acpx/dist/*.js`` — see the module docstring in
``scripts/agent_runtime/adapters/acpx.py`` for the captured contract this
suite verifies against. No test in this file spawns a real subprocess or
touches the network; all process-lifecycle categories (success, cancel,
timeout, crash, malformed/partial NDJSON, duplicate replay, auth failure) are
exercised as pure ``parse_response()`` calls over fixture stdout, exactly as
the runner would call the adapter after collecting subprocess output. Grok
build-invocation tests mock binary resolution and version probes only.
"""

from __future__ import annotations

import shlex
from pathlib import Path

import pytest

from scripts.agent_runtime.adapters import acpx as acpx_module
from scripts.agent_runtime.adapters.acpx import (
    ACPX_PARSED_RESPONSE_LIMIT_BYTES,
    ACPX_SUPPORTED_PARTICIPANTS,
    AcpxAdapter,
    AcpxAgyShadowAdapter,
    AcpxClaudeShadowAdapter,
    AcpxCursorShadowAdapter,
    AcpxDeepSeekShadowAdapter,
    AcpxGlmShadowAdapter,
    AcpxGrokShadowAdapter,
    AcpxKimiCcShadowAdapter,
    AcpxKimiShadowAdapter,
    AcpxPoolShadowAdapter,
    AcpxShadowRefusalError,
)
from scripts.agent_runtime.env_sanitize import build_agent_env

_SUCCESS_NDJSON = (
    '{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":1,'
    '"clientCapabilities":{"fs":{"readTextFile":false,"writeTextFile":false},"terminal":false},'
    '"clientInfo":{"name":"acpx","version":"0.13.0"}}}\n'
    '{"jsonrpc":"2.0","id":0,"result":{"protocolVersion":1,"agentCapabilities":{}}}\n'
    '{"jsonrpc":"2.0","id":1,"method":"session/new","params":{"cwd":"/repo","mcpServers":[]}}\n'
    '{"jsonrpc":"2.0","id":1,"result":{"sessionId":"sess-fixture-001"}}\n'
    '{"jsonrpc":"2.0","id":2,"method":"session/prompt","params":{"sessionId":"sess-fixture-001",'
    '"prompt":[{"type":"text","text":"ping"}]}}\n'
    '{"jsonrpc":"2.0","method":"session/update","params":{"sessionId":"sess-fixture-001",'
    '"update":{"sessionUpdate":"agent_message_chunk","content":{"type":"text","text":"Hello "}}}}\n'
    '{"jsonrpc":"2.0","method":"session/update","params":{"sessionId":"sess-fixture-001",'
    '"update":{"sessionUpdate":"agent_message_chunk","content":{"type":"text","text":"world."}}}}\n'
    '{"jsonrpc":"2.0","id":2,"result":{"stopReason":"end_turn"}}\n'
)

_CANCELLED_NDJSON = (
    '{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":1,'
    '"clientCapabilities":{"fs":{"readTextFile":false,"writeTextFile":false},"terminal":false},'
    '"clientInfo":{"name":"acpx","version":"0.13.0"}}}\n'
    '{"jsonrpc":"2.0","id":0,"result":{"protocolVersion":1,"agentCapabilities":{}}}\n'
    '{"jsonrpc":"2.0","id":2,"method":"session/prompt","params":{"sessionId":"sess-fixture-002",'
    '"prompt":[{"type":"text","text":"ping"}]}}\n'
    '{"jsonrpc":"2.0","method":"session/update","params":{"sessionId":"sess-fixture-002",'
    '"update":{"sessionUpdate":"agent_message_chunk","content":{"type":"text","text":"partial answer"}}}}\n'
    '{"jsonrpc":"2.0","id":2,"result":{"stopReason":"cancelled"}}\n'
)

_TIMEOUT_NDJSON = (
    '{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":1,'
    '"clientCapabilities":{"fs":{"readTextFile":false,"writeTextFile":false},"terminal":false},'
    '"clientInfo":{"name":"acpx","version":"0.13.0"}}}\n'
    '{"jsonrpc":"2.0","id":null,"error":{"code":-32070,"message":"Timed out after 5000ms",'
    '"data":{"acpxCode":"TIMEOUT","origin":"cli","sessionId":"unknown"}}}\n'
)

_CRASH_NO_TERMINAL_NDJSON = (
    '{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":1,'
    '"clientCapabilities":{"fs":{"readTextFile":false,"writeTextFile":false},"terminal":false},'
    '"clientInfo":{"name":"acpx","version":"0.13.0"}}}\n'
    '{"jsonrpc":"2.0","id":0,"result":{"protocolVersion":1,"agentCapabilities":{}}}\n'
    '{"jsonrpc":"2.0","id":2,"method":"session/prompt","params":{"sessionId":"sess-fixture-003",'
    '"prompt":[{"type":"text","text":"ping"}]}}\n'
    '{"jsonrpc":"2.0","method":"session/update","params":{"sessionId":"sess-fixture-003",'
    '"update":{"sessionUpdate":"agent_message_chunk","content":{"type":"text","text":"star"}}}}\n'
)

_AGENT_DISCONNECTED_NDJSON = (
    '{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":1,'
    '"clientCapabilities":{"fs":{"readTextFile":false,"writeTextFile":false},"terminal":false},'
    '"clientInfo":{"name":"acpx","version":"0.13.0"}}}\n'
    '{"jsonrpc":"2.0","id":0,"result":{"protocolVersion":1,"agentCapabilities":{}}}\n'
    '{"jsonrpc":"2.0","id":null,"error":{"code":-32603,'
    '"message":"codex-acp process exited unexpectedly (code 1)",'
    '"data":{"acpxCode":"RUNTIME","detailCode":"AGENT_DISCONNECTED","origin":"cli","sessionId":"unknown"}}}\n'
)

_MALFORMED_LINE_NDJSON = (
    '{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":1,'
    '"clientCapabilities":{"fs":{"readTextFile":false,"writeTextFile":false},"terminal":false},'
    '"clientInfo":{"name":"acpx","version":"0.13.0"}}}\n'
    '{"jsonrpc":"2.0","id":0,"result":{"protocolVersion":1,"agentCapabilities":{}}}\n'
    '{"jsonrpc":"2.0","method":"session/update","params":{"sessionId":"sess-fixture-004",'
    '"update":{"sessionUpdate":"agent_mess\n'
)

_UNRECOGNIZED_SCHEMA_NDJSON = (
    '{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":1,'
    '"clientCapabilities":{"fs":{"readTextFile":false,"writeTextFile":false},"terminal":false},'
    '"clientInfo":{"name":"acpx","version":"0.13.0"}}}\n'
    '{"unexpected":"payload","reason":"neither method, result, nor error"}\n'
)

_DUPLICATE_REPLAY_NDJSON = (
    '{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":1,'
    '"clientCapabilities":{"fs":{"readTextFile":false,"writeTextFile":false},"terminal":false},'
    '"clientInfo":{"name":"acpx","version":"0.13.0"}}}\n'
    '{"jsonrpc":"2.0","id":0,"result":{"protocolVersion":1,"agentCapabilities":{}}}\n'
    '{"jsonrpc":"2.0","id":2,"method":"session/prompt","params":{"sessionId":"sess-fixture-005",'
    '"prompt":[{"type":"text","text":"ping"}]}}\n'
    '{"jsonrpc":"2.0","method":"session/update","params":{"sessionId":"sess-fixture-005",'
    '"update":{"sessionUpdate":"agent_message_chunk","content":{"type":"text","text":"pong"}}}}\n'
    '{"jsonrpc":"2.0","id":2,"result":{"stopReason":"end_turn"}}\n'
    '{"jsonrpc":"2.0","id":2,"result":{"stopReason":"end_turn"}}\n'
)

_AUTH_REQUIRED_NDJSON = (
    '{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":1,'
    '"clientCapabilities":{"fs":{"readTextFile":false,"writeTextFile":false},"terminal":false},'
    '"clientInfo":{"name":"acpx","version":"0.13.0"}}}\n'
    '{"jsonrpc":"2.0","id":null,"error":{"code":-32603,'
    '"message":"Authentication required for codex and --auth-policy is \'fail\'",'
    '"data":{"acpxCode":"RUNTIME","detailCode":"AUTH_REQUIRED","origin":"acp","sessionId":"unknown"}}}\n'
)

_USAGE_BODY_NDJSON = (
    '{"jsonrpc":"2.0","method":"session/update","params":{"update":'
    '{"sessionUpdate":"usage_update","inputTokens":3,"output_tokens":4}}}\n'
)

_USAGE_META_NDJSON = (
    '{"jsonrpc":"2.0","method":"session/update","params":{"update":'
    '{"sessionUpdate":"usage_update","_meta":{"usage":{"total_tokens":24}}}}}\n'
)

_USAGE_CONTEXT_NDJSON = (
    '{"jsonrpc":"2.0","method":"session/update","params":{"update":'
    '{"sessionUpdate":"usage_update","used":321,"size":258400}}}\n'
)

_INVALID_USAGE_NDJSON = (
    '{"jsonrpc":"2.0","method":"session/update","params":{"update":'
    '{"sessionUpdate":"usage_update","totalTokens":"unknown"}}}\n'
)


def _stub_binary(
    monkeypatch,
    tmp_path: Path,
    *,
    version: str = "0.13.0",
    missing: tuple[str, ...] = (),
) -> Path:
    """Point the adapter at a fake local binary + compatibility probe.

    Avoids depending on the real npm-installed ``node_modules/.bin/acpx``
    being present in whatever environment runs this suite.
    """
    binary = tmp_path / "fake-acpx-bin"
    binary.write_text("#!/bin/sh\necho stub\n", encoding="utf-8")
    binary.chmod(0o755)
    monkeypatch.setattr(acpx_module, "_ACPX_BINARY", binary)
    monkeypatch.setattr(
        acpx_module,
        "_probe_acpx_cli_compatibility",
        lambda _binary, *, builtin_agent: (version, missing),
    )
    return binary


def _shadow_env(monkeypatch) -> None:
    monkeypatch.setenv(acpx_module.TRANSPORT_ENV, "shadow")


def _build(
    adapter: AcpxAdapter,
    *,
    cwd: Path,
    prompt: str = "ping",
    model: str | None = None,
    task_id: str | None = "t-1",
    session_id: str | None = None,
    tool_config: dict | None = None,
    effort: str | None = None,
):
    if tool_config is None:
        tool_config = {
            "acpx_shadow": True,
            "correlation_id": "corr-1",
            "idempotency_key": "idem-1",
        }
    return adapter.build_invocation(
        prompt=prompt,
        mode="read-only",
        cwd=cwd,
        model=model,
        task_id=task_id,
        session_id=session_id,
        tool_config=tool_config,
        effort=effort,
    )


# ---------------------------------------------------------------------------
# Registry-level identity
# ---------------------------------------------------------------------------


def test_adapter_identity_is_read_only_only():
    adapter = AcpxAdapter()
    assert adapter.name == "acpx-codex-shadow"
    assert adapter.supported_modes == frozenset({"read-only"})


# ---------------------------------------------------------------------------
# Flag-off rollback (feature flag gate)
# ---------------------------------------------------------------------------


def test_build_invocation_refuses_when_flag_unset(tmp_path, monkeypatch):
    monkeypatch.delenv(acpx_module.TRANSPORT_ENV, raising=False)
    _stub_binary(monkeypatch, tmp_path)
    adapter = AcpxAdapter()

    with pytest.raises(AcpxShadowRefusalError, match="LU_ACPX_TRANSPORT"):
        _build(adapter, cwd=tmp_path)


def test_build_invocation_refuses_when_flag_off(tmp_path, monkeypatch):
    monkeypatch.setenv(acpx_module.TRANSPORT_ENV, "off")
    _stub_binary(monkeypatch, tmp_path)
    adapter = AcpxAdapter()

    with pytest.raises(AcpxShadowRefusalError):
        _build(adapter, cwd=tmp_path)


def test_build_invocation_refuses_unknown_flag_value(tmp_path, monkeypatch):
    monkeypatch.setenv(acpx_module.TRANSPORT_ENV, "live")
    _stub_binary(monkeypatch, tmp_path)
    adapter = AcpxAdapter()

    with pytest.raises(AcpxShadowRefusalError):
        _build(adapter, cwd=tmp_path)


def test_build_invocation_succeeds_when_flag_shadow(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path)
    adapter = AcpxAdapter()

    plan = _build(adapter, cwd=tmp_path)
    assert plan.cmd[0] == str(acpx_module._ACPX_BINARY)


def test_build_invocation_active_requires_controller_scope(tmp_path, monkeypatch):
    monkeypatch.setenv(acpx_module.TRANSPORT_ENV, "active")
    _stub_binary(monkeypatch, tmp_path)
    adapter = AcpxAdapter()
    tool_config = {
        "acpx_discussion": True,
        "target_agent": "codex",
        "correlation_id": "corr-1",
        "idempotency_key": "idem-1",
    }

    with pytest.raises(AcpxShadowRefusalError, match="discussion controller"):
        _build(adapter, cwd=tmp_path, tool_config=tool_config)

    with acpx_module.active_discussion_scope():
        plan = _build(adapter, cwd=tmp_path, tool_config=tool_config)
    assert plan.cmd[0] == str(acpx_module._ACPX_BINARY)


# ---------------------------------------------------------------------------
# Shadow marker + tool_config allowlist
# ---------------------------------------------------------------------------


def test_build_invocation_requires_explicit_shadow_marker(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path)
    adapter = AcpxAdapter()

    with pytest.raises(AcpxShadowRefusalError, match="acpx_shadow"):
        _build(adapter, cwd=tmp_path, tool_config={})


def test_build_invocation_rejects_unsupported_tool_config_keys(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path)
    adapter = AcpxAdapter()

    with pytest.raises(AcpxShadowRefusalError, match="unsupported tool_config"):
        _build(
            adapter,
            cwd=tmp_path,
            tool_config={"acpx_shadow": True, "mcp_servers": {"sources": {"url": "http://x"}}},
        )


def test_build_invocation_rejects_non_codex_target(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path)
    adapter = AcpxAdapter()

    with pytest.raises(AcpxShadowRefusalError, match="target_agent"):
        _build(
            adapter,
            cwd=tmp_path,
            tool_config={"acpx_shadow": True, "target_agent": "claude"},
        )


# ---------------------------------------------------------------------------
# Local correlation_id / idempotency_key / task_id metadata
# ---------------------------------------------------------------------------


def test_build_invocation_requires_non_empty_task_id(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path)
    adapter = AcpxAdapter()

    with pytest.raises(AcpxShadowRefusalError, match="task_id"):
        _build(adapter, cwd=tmp_path, task_id=None)


def test_build_invocation_rejects_blank_task_id(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path)
    adapter = AcpxAdapter()

    with pytest.raises(AcpxShadowRefusalError, match="task_id"):
        _build(adapter, cwd=tmp_path, task_id="   ")


def test_build_invocation_requires_correlation_id(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path)
    adapter = AcpxAdapter()

    with pytest.raises(AcpxShadowRefusalError, match="correlation_id"):
        _build(
            adapter,
            cwd=tmp_path,
            tool_config={"acpx_shadow": True, "idempotency_key": "idem-1"},
        )


def test_build_invocation_rejects_blank_correlation_id(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path)
    adapter = AcpxAdapter()

    with pytest.raises(AcpxShadowRefusalError, match="correlation_id"):
        _build(
            adapter,
            cwd=tmp_path,
            tool_config={"acpx_shadow": True, "correlation_id": "  ", "idempotency_key": "idem-1"},
        )


def test_build_invocation_requires_idempotency_key(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path)
    adapter = AcpxAdapter()

    with pytest.raises(AcpxShadowRefusalError, match="idempotency_key"):
        _build(
            adapter,
            cwd=tmp_path,
            tool_config={"acpx_shadow": True, "correlation_id": "corr-1"},
        )


def test_build_invocation_rejects_oversized_correlation_id(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path)
    adapter = AcpxAdapter()

    with pytest.raises(AcpxShadowRefusalError, match="correlation_id"):
        _build(
            adapter,
            cwd=tmp_path,
            tool_config={
                "acpx_shadow": True,
                "correlation_id": "x" * 201,
                "idempotency_key": "idem-1",
            },
        )


def test_build_invocation_rejects_unsafe_idempotency_key_characters(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path)
    adapter = AcpxAdapter()

    with pytest.raises(AcpxShadowRefusalError, match="idempotency_key"):
        _build(
            adapter,
            cwd=tmp_path,
            tool_config={
                "acpx_shadow": True,
                "correlation_id": "corr-1",
                "idempotency_key": "idem\n1",
            },
        )


def test_build_invocation_stamps_local_metadata_without_forwarding_to_argv_or_stdin(
    tmp_path, monkeypatch
):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path)
    adapter = AcpxAdapter()

    plan = _build(
        adapter,
        cwd=tmp_path,
        prompt="investigate the flaky test",
        task_id="task-42",
        tool_config={
            "acpx_shadow": True,
            "correlation_id": "corr-abc.123",
            "idempotency_key": "idem-xyz:9",
        },
    )

    assert plan.metadata["task_id"] == "task-42"
    assert plan.metadata["correlation_id"] == "corr-abc.123"
    assert plan.metadata["idempotency_key"] == "idem-xyz:9"

    # Never turned into ACP protocol flags, argv tokens, or stdin content.
    for value in ("task-42", "corr-abc.123", "idem-xyz:9"):
        assert value not in plan.cmd
        assert value not in plan.stdin_payload


# ---------------------------------------------------------------------------
# No persistent session
# ---------------------------------------------------------------------------


def test_build_invocation_rejects_non_null_session_id(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path)
    adapter = AcpxAdapter()

    with pytest.raises(AcpxShadowRefusalError, match="session_id"):
        _build(adapter, cwd=tmp_path, session_id="some-prior-session")


def test_build_invocation_never_uses_session_or_prompt_subcommand(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path)
    adapter = AcpxAdapter()

    plan = _build(adapter, cwd=tmp_path)
    assert "codex" in plan.cmd and "exec" in plan.cmd
    assert "prompt" not in plan.cmd
    assert "sessions" not in plan.cmd
    assert "-s" not in plan.cmd
    assert "--session" not in plan.cmd


# ---------------------------------------------------------------------------
# Rolling compatibility
# ---------------------------------------------------------------------------


def test_build_invocation_accepts_compatible_future_version(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path, version="0.14.7")

    plan = _build(AcpxAdapter(), cwd=tmp_path)

    assert plan.metadata["acpx_cli_version"] == "0.14.7"
    assert plan.metadata["acpx_cli_compatibility"] == "json-one-shot-v1"


def test_build_invocation_rejects_missing_acpx_capability(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path, version="0.14.7", missing=("--deny-all",))

    with pytest.raises(AcpxShadowRefusalError, match="--deny-all"):
        _build(AcpxAdapter(), cwd=tmp_path)


def test_build_invocation_rejects_missing_binary(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    monkeypatch.setattr(acpx_module, "_ACPX_BINARY", tmp_path / "does-not-exist")
    adapter = AcpxAdapter()

    with pytest.raises(AcpxShadowRefusalError, match="project-local acpx binary not found"):
        _build(adapter, cwd=tmp_path)


def _set_default_binary_candidate(monkeypatch, candidate: Path) -> None:
    """Make a test-local module candidate eligible for primary fallback."""
    monkeypatch.setattr(acpx_module, "_DEFAULT_ACPX_BINARY", candidate)
    monkeypatch.setattr(acpx_module, "_ACPX_BINARY", candidate)


def test_build_invocation_resolves_primary_pin_from_linked_worktree(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    primary = tmp_path / "primary"
    worktree = primary / ".worktrees" / "dispatch" / "codex" / "acp"
    worktree.mkdir(parents=True)
    module_candidate = worktree / "node_modules" / ".bin" / "acpx"
    _set_default_binary_candidate(monkeypatch, module_candidate)
    primary_binary = primary / "node_modules" / ".bin" / "acpx"
    primary_binary.parent.mkdir(parents=True)
    primary_binary.write_text("#!/bin/sh\n", encoding="utf-8")
    primary_binary.chmod(0o755)
    monkeypatch.setattr(acpx_module, "resolve_main_root", lambda cwd: primary)
    monkeypatch.setattr(
        acpx_module,
        "_probe_acpx_cli_compatibility",
        lambda _binary, *, builtin_agent: ("0.13.0", ()),
    )

    plan = _build(AcpxAdapter(), cwd=worktree)

    assert plan.cmd[0] == str(primary_binary)


def test_build_invocation_explicit_binary_override_never_uses_primary(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    override = _stub_binary(monkeypatch, tmp_path)
    monkeypatch.setattr(
        acpx_module,
        "resolve_main_root",
        lambda _cwd: pytest.fail("explicit binary override must remain authoritative"),
    )

    plan = _build(AcpxAdapter(), cwd=tmp_path)

    assert plan.cmd[0] == str(override)


def test_build_invocation_non_git_cwd_refuses_without_global_fallback(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    candidate = tmp_path / "worktree" / "node_modules" / ".bin" / "acpx"
    _set_default_binary_candidate(monkeypatch, candidate)
    monkeypatch.setattr(
        acpx_module,
        "resolve_main_root",
        lambda cwd: (_ for _ in ()).throw(acpx_module.NotAGitRepositoryError(str(cwd))),
    )

    with pytest.raises(AcpxShadowRefusalError, match="no canonical primary install is available"):
        _build(AcpxAdapter(), cwd=tmp_path)


def test_build_invocation_refuses_when_primary_pin_is_missing(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    candidate = tmp_path / "worktree" / "node_modules" / ".bin" / "acpx"
    primary = tmp_path / "primary"
    _set_default_binary_candidate(monkeypatch, candidate)
    monkeypatch.setattr(acpx_module, "resolve_main_root", lambda _cwd: primary)

    with pytest.raises(AcpxShadowRefusalError, match=str(primary / "node_modules" / ".bin" / "acpx")):
        _build(AcpxAdapter(), cwd=tmp_path)


def test_build_invocation_rejects_primary_binary_capability_drift(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    candidate = tmp_path / "worktree" / "node_modules" / ".bin" / "acpx"
    primary = tmp_path / "primary"
    primary_binary = primary / "node_modules" / ".bin" / "acpx"
    primary_binary.parent.mkdir(parents=True)
    primary_binary.write_text("#!/bin/sh\n", encoding="utf-8")
    primary_binary.chmod(0o755)
    _set_default_binary_candidate(monkeypatch, candidate)
    monkeypatch.setattr(acpx_module, "resolve_main_root", lambda _cwd: primary)
    monkeypatch.setattr(
        acpx_module,
        "_probe_acpx_cli_compatibility",
        lambda _binary, *, builtin_agent: ("0.14.0", ("exec --file",)),
    )

    with pytest.raises(AcpxShadowRefusalError, match="exec --file"):
        _build(AcpxAdapter(), cwd=tmp_path)


def test_build_invocation_accepts_unknown_version_when_capabilities_pass(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path, version="unknown")

    plan = _build(AcpxAdapter(), cwd=tmp_path)

    assert plan.metadata["acpx_cli_version"] == "unknown"


# ---------------------------------------------------------------------------
# Argv / permission confinement — structural, not probabilistic
# ---------------------------------------------------------------------------


def test_build_invocation_argv_is_fully_confined(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path)
    adapter = AcpxAdapter()

    plan = _build(adapter, cwd=tmp_path, prompt="investigate the flaky test")

    assert plan.cwd == tmp_path
    assert plan.stdin_payload == "investigate the flaky test"
    # Prompt travels via stdin (-f -), never as a bare argv token.
    assert "investigate the flaky test" not in plan.cmd
    assert plan.cmd[-3:] == ["exec", "-f", "-"]

    pairs = list(zip(plan.cmd, plan.cmd[1:], strict=False))
    assert ("--auth-policy", "fail") in pairs
    assert ("--non-interactive-permissions", "fail") in pairs
    assert ("--allowed-tools", "") in pairs
    assert ("--max-turns", "1") in pairs
    assert ("--prompt-retries", "0") in pairs
    assert ("--format", "json") in pairs
    assert "--deny-all" in plan.cmd
    assert "--no-fs" in plan.cmd
    assert "--no-terminal" in plan.cmd
    assert "--json-strict" in plan.cmd
    assert "--model" not in plan.cmd  # omitted entirely when caller passes none


def test_build_invocation_passes_model_only_when_given(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path)
    adapter = AcpxAdapter()

    plan = _build(adapter, cwd=tmp_path, model="gpt-5.6-terra")
    pairs = list(zip(plan.cmd, plan.cmd[1:], strict=False))
    assert ("--model", "gpt-5.6-terra") in pairs


def test_build_invocation_ignores_unsupported_effort_without_raising(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path)
    adapter = AcpxAdapter()

    plan = _build(adapter, cwd=tmp_path, effort="xhigh")
    assert plan is not None  # did not raise


def test_build_invocation_rejects_write_mode(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path)
    adapter = AcpxAdapter()

    with pytest.raises(ValueError, match="mode"):
        adapter.build_invocation(
            prompt="ping",
            mode="workspace-write",
            cwd=tmp_path,
            model=None,
            task_id=None,
            session_id=None,
            tool_config={"acpx_shadow": True},
        )


def test_liveness_signal_paths_is_empty(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path)
    adapter = AcpxAdapter()

    plan = _build(adapter, cwd=tmp_path)
    assert adapter.liveness_signal_paths(plan) == ()


# ---------------------------------------------------------------------------
# Protected primary checkout refusal
# ---------------------------------------------------------------------------


def test_build_invocation_refuses_protected_primary_checkout(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path)
    monkeypatch.setattr(
        acpx_module._worktree_containment,
        "classify_repo_path",
        lambda *_args, **_kwargs: "primary_checkout",
    )
    adapter = AcpxAdapter()

    with pytest.raises(AcpxShadowRefusalError, match="primary checkout"):
        _build(adapter, cwd=tmp_path)


def test_build_invocation_allows_non_primary_cwd(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path)
    monkeypatch.setattr(
        acpx_module._worktree_containment,
        "classify_repo_path",
        lambda *_args, **_kwargs: "dispatch_worktree",
    )
    adapter = AcpxAdapter()

    plan = _build(adapter, cwd=tmp_path)
    assert plan.cwd == tmp_path


# ---------------------------------------------------------------------------
# parse_response — success
# ---------------------------------------------------------------------------


def test_parse_response_success():
    adapter = AcpxAdapter()
    result = adapter.parse_response(
        stdout=_SUCCESS_NDJSON,
        stderr="",
        returncode=0,
        output_file=None,
    )
    assert result.ok is True
    assert result.response == "Hello world."
    assert result.stderr_excerpt is None
    assert result.rate_limited is False
    assert result.session_id is None
    assert result.tokens is None
    assert result.tool_calls == []


# ---------------------------------------------------------------------------
# parse_response — terminal stopReason schema
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "stop_reason_json",
    ['"unknown_stop_reason"', "42", "null"],
    ids=["unknown", "non-string", "null"],
)
def test_parse_response_unrecognized_stop_reason_fails_closed(stop_reason_json):
    adapter = AcpxAdapter()
    terminal = '{"stopReason":"end_turn"}'
    replacement = f'{{"stopReason":{stop_reason_json}}}'
    result = adapter.parse_response(
        stdout=_SUCCESS_NDJSON.replace(terminal, replacement),
        stderr="",
        returncode=0,
        output_file=None,
    )
    assert result.ok is False
    assert result.response == ""
    assert "unrecognized terminal stopReason schema" in result.stderr_excerpt


def test_parse_response_recognizes_max_tokens_stop_reason():
    adapter = AcpxAdapter()
    result = adapter.parse_response(
        stdout=_SUCCESS_NDJSON.replace('"end_turn"', '"max_tokens"'),
        stderr="",
        returncode=0,
        output_file=None,
    )
    assert result.ok is True
    assert result.response == "Hello world."
    assert result.stderr_excerpt is None


def test_parse_response_rejects_oversized_answer_before_authority_receipt():
    adapter = AcpxAdapter()
    oversized = "я" * (ACPX_PARSED_RESPONSE_LIMIT_BYTES // 2 + 1)
    stdout = (
        '{"jsonrpc":"2.0","method":"session/update","params":{"update":'
        '{"sessionUpdate":"agent_message_chunk","content":{"type":"text","text":"'
        + oversized
        + '"}}}}\n'
        '{"jsonrpc":"2.0","id":2,"result":{"stopReason":"end_turn"}}\n'
    )

    result = adapter.parse_response(
        stdout=stdout,
        stderr="",
        returncode=0,
        output_file=None,
    )

    assert result.ok is False
    assert result.response == ""
    assert "parsed ACP response exceeds" in result.stderr_excerpt
    assert str(ACPX_PARSED_RESPONSE_LIMIT_BYTES) in result.stderr_excerpt
    assert result.failure_code == "protocol_output_limit"


def test_parse_response_multiple_stop_reason_results_fails_closed():
    adapter = AcpxAdapter()
    second_terminal = '{"jsonrpc":"2.0","id":3,"result":{"stopReason":"max_tokens"}}\n'
    result = adapter.parse_response(
        stdout=_SUCCESS_NDJSON + second_terminal,
        stderr="",
        returncode=0,
        output_file=None,
    )
    assert result.ok is False
    assert result.response == ""
    assert "multiple terminal stopReason responses" in result.stderr_excerpt


def test_parse_response_uses_last_valid_usage_total():
    adapter = AcpxAdapter()
    terminal = '{"jsonrpc":"2.0","id":2,"result":{"stopReason":"end_turn"}}\n'
    result = adapter.parse_response(
        stdout=_SUCCESS_NDJSON.replace(terminal, _USAGE_BODY_NDJSON + _USAGE_META_NDJSON + terminal),
        stderr="",
        returncode=0,
        output_file=None,
    )
    assert result.ok is True
    assert result.tokens == 24


def test_parse_response_sums_usage_input_and_output_tokens():
    adapter = AcpxAdapter()
    terminal = '{"jsonrpc":"2.0","id":2,"result":{"stopReason":"end_turn"}}\n'
    result = adapter.parse_response(
        stdout=_SUCCESS_NDJSON.replace(terminal, _USAGE_BODY_NDJSON + terminal),
        stderr="",
        returncode=0,
        output_file=None,
    )
    assert result.ok is True
    assert result.tokens == 7


def test_parse_response_reports_context_used_not_window_size():
    adapter = AcpxAdapter()
    terminal = '{"jsonrpc":"2.0","id":2,"result":{"stopReason":"end_turn"}}\n'
    result = adapter.parse_response(
        stdout=_SUCCESS_NDJSON.replace(terminal, _USAGE_CONTEXT_NDJSON + terminal),
        stderr="",
        returncode=0,
        output_file=None,
    )
    assert result.ok is True
    assert result.tokens == 321


def test_parse_response_invalid_usage_tokens_fail_closed():
    adapter = AcpxAdapter()
    terminal = '{"jsonrpc":"2.0","id":2,"result":{"stopReason":"end_turn"}}\n'
    result = adapter.parse_response(
        stdout=_SUCCESS_NDJSON.replace(terminal, _INVALID_USAGE_NDJSON + terminal),
        stderr="",
        returncode=0,
        output_file=None,
    )
    assert result.ok is False
    assert result.response == ""
    assert "invalid totalTokens" in result.stderr_excerpt


# ---------------------------------------------------------------------------
# parse_response — cancellation
# ---------------------------------------------------------------------------


def test_parse_response_cancelled_fails_closed():
    adapter = AcpxAdapter()
    result = adapter.parse_response(
        stdout=_CANCELLED_NDJSON,
        stderr="",
        returncode=0,
        output_file=None,
    )
    assert result.ok is False
    assert result.response == ""
    assert "cancelled" in result.stderr_excerpt.lower()


# ---------------------------------------------------------------------------
# parse_response — timeout (byte-for-byte capture of the real 0.13.0 binary)
# ---------------------------------------------------------------------------


def test_parse_response_timeout_fails_closed():
    adapter = AcpxAdapter()
    result = adapter.parse_response(
        stdout=_TIMEOUT_NDJSON,
        stderr="",
        returncode=3,  # EXIT_CODES.TIMEOUT captured from node_modules/acpx/dist
        output_file=None,
    )
    assert result.ok is False
    assert result.response == ""
    assert "TIMEOUT" in result.stderr_excerpt
    assert result.rate_limited is False
    assert result.failure_code == "timeout"


# ---------------------------------------------------------------------------
# parse_response — crash / agent disconnect
# ---------------------------------------------------------------------------


def test_parse_response_crash_with_no_terminal_marker_fails_closed():
    adapter = AcpxAdapter()
    result = adapter.parse_response(
        stdout=_CRASH_NO_TERMINAL_NDJSON,
        stderr="",
        returncode=-9,  # signaled: the runner killed the process
        output_file=None,
    )
    assert result.ok is False
    assert result.response == ""
    assert "no terminal response" in result.stderr_excerpt or "rc=-9" in result.stderr_excerpt


def test_parse_response_agent_disconnected_fails_closed():
    adapter = AcpxAdapter()
    result = adapter.parse_response(
        stdout=_AGENT_DISCONNECTED_NDJSON,
        stderr="",
        returncode=1,
        output_file=None,
    )
    assert result.ok is False
    assert result.response == ""
    assert result.failure_code == "provider_unavailable"
    assert "AGENT_DISCONNECTED" in result.stderr_excerpt


# ---------------------------------------------------------------------------
# parse_response — malformed / partial NDJSON
# ---------------------------------------------------------------------------


def test_parse_response_malformed_line_fails_closed():
    adapter = AcpxAdapter()
    result = adapter.parse_response(
        stdout=_MALFORMED_LINE_NDJSON,
        stderr="",
        returncode=-9,
        output_file=None,
    )
    assert result.ok is False
    assert result.response == ""
    assert "malformed NDJSON" in result.stderr_excerpt


def test_parse_response_unrecognized_schema_fails_closed():
    adapter = AcpxAdapter()
    result = adapter.parse_response(
        stdout=_UNRECOGNIZED_SCHEMA_NDJSON,
        stderr="",
        returncode=0,
        output_file=None,
    )
    assert result.ok is False
    assert result.response == ""
    assert "unrecognized NDJSON schema" in result.stderr_excerpt


@pytest.mark.parametrize(
    ("stdout", "schema"),
    [
        ('{"jsonrpc":"2.0","method":"session/update","params":[]}\n', "params"),
        ('{"jsonrpc":"2.0","method":"session/update","params":{"update":[]}}\n', "update"),
        (
            '{"jsonrpc":"2.0","method":"session/update","params":{"update":'
            '{"sessionUpdate":"agent_message_chunk","content":[]}}}\n',
            "content",
        ),
        ('{"jsonrpc":"2.0","id":2,"result":[]}\n', "result"),
        ('{"jsonrpc":"2.0","id":null,"error":[]}\n', "error"),
        ('{"jsonrpc":"2.0","id":null,"error":{"message":"bad","data":[]}}\n', "error.data"),
        ('{"jsonrpc":"2.0","id":{},"result":{"stopReason":"end_turn"}}\n', "response id"),
        ('{"jsonrpc":"2.0","id":[],"result":{"stopReason":"end_turn"}}\n', "response id"),
    ],
    ids=["params", "update", "content", "result", "error", "error-data", "object-id", "list-id"],
)
def test_parse_response_malformed_json_rpc_containers_fail_closed(stdout, schema):
    result = AcpxAdapter().parse_response(
        stdout=stdout,
        stderr="",
        returncode=0,
        output_file=None,
    )
    assert result.ok is False
    assert result.response == ""
    assert schema in result.stderr_excerpt


def test_parse_response_empty_stdout_fails_closed():
    adapter = AcpxAdapter()
    result = adapter.parse_response(stdout="", stderr="boom", returncode=1, output_file=None)
    assert result.ok is False
    assert result.response == ""
    assert "no NDJSON output" in result.stderr_excerpt
    assert "boom" in result.stderr_excerpt


# ---------------------------------------------------------------------------
# parse_response — duplicate terminal replay
# ---------------------------------------------------------------------------


def test_parse_response_duplicate_terminal_replay_fails_closed():
    adapter = AcpxAdapter()
    result = adapter.parse_response(
        stdout=_DUPLICATE_REPLAY_NDJSON,
        stderr="",
        returncode=0,
        output_file=None,
    )
    assert result.ok is False
    assert result.response == ""
    assert "duplicate" in result.stderr_excerpt.lower()


# ---------------------------------------------------------------------------
# parse_response — authentication failure
# ---------------------------------------------------------------------------


def test_parse_response_auth_required_fails_closed():
    adapter = AcpxAdapter()
    result = adapter.parse_response(
        stdout=_AUTH_REQUIRED_NDJSON,
        stderr="",
        returncode=1,
        output_file=None,
    )
    assert result.ok is False
    assert result.response == ""
    assert "AUTH_REQUIRED" in result.stderr_excerpt
    assert result.rate_limited is False
    assert result.failure_code == "provider_unavailable"


# ---------------------------------------------------------------------------
# parse_response — never best-effort on a nonzero exit with an otherwise
# complete-looking stream (belt and suspenders on the fail-closed posture)
# ---------------------------------------------------------------------------


def test_parse_response_nonzero_exit_with_end_turn_still_fails():
    adapter = AcpxAdapter()
    result = adapter.parse_response(
        stdout=_SUCCESS_NDJSON,
        stderr="unexpected trailing crash",
        returncode=1,
        output_file=None,
    )
    assert result.ok is False
    assert result.response == ""


# ---------------------------------------------------------------------------
# AcpxGrokShadowAdapter — second bounded shadow seat (#6043)
# ---------------------------------------------------------------------------


def _stub_grok(
    monkeypatch,
    tmp_path: Path,
    *,
    version: str = "0.2.118",
    missing: tuple[str, ...] = (),
) -> Path:
    """Point the Grok seat at a fake binary + compatibility probe."""
    grok = tmp_path / "fake-grok-bin"
    grok.write_text("#!/bin/sh\necho stub-grok\n", encoding="utf-8")
    grok.chmod(0o755)
    monkeypatch.setattr(acpx_module, "_resolve_grok_binary", lambda: str(grok.resolve()))
    monkeypatch.setattr(
        acpx_module,
        "_probe_grok_cli_compatibility",
        lambda _binary: (version, missing),
    )
    return grok.resolve()


def _build_grok(
    adapter: AcpxGrokShadowAdapter,
    *,
    cwd: Path,
    prompt: str = "ping",
    model: str | None = None,
    task_id: str | None = "t-1",
    session_id: str | None = None,
    tool_config: dict | None = None,
    effort: str | None = None,
):
    if tool_config is None:
        tool_config = {
            "acpx_shadow": True,
            "target_agent": "grok",
            "correlation_id": "corr-1",
            "idempotency_key": "idem-1",
        }
    return adapter.build_invocation(
        prompt=prompt,
        mode="read-only",
        cwd=cwd,
        model=model,
        task_id=task_id,
        session_id=session_id,
        tool_config=tool_config,
        effort=effort,
    )


def test_grok_adapter_identity_is_read_only_only():
    adapter = AcpxGrokShadowAdapter()
    assert adapter.name == "acpx-grok-shadow"
    assert adapter.default_model == "grok-4.5"
    assert adapter.supported_modes == frozenset({"read-only"})


def test_grok_build_invocation_refuses_when_flag_unset(tmp_path, monkeypatch):
    monkeypatch.delenv(acpx_module.TRANSPORT_ENV, raising=False)
    _stub_binary(monkeypatch, tmp_path)
    _stub_grok(monkeypatch, tmp_path)
    adapter = AcpxGrokShadowAdapter()

    with pytest.raises(AcpxShadowRefusalError, match="LU_ACPX_TRANSPORT"):
        _build_grok(adapter, cwd=tmp_path)


def test_grok_build_invocation_refuses_when_flag_off(tmp_path, monkeypatch):
    monkeypatch.setenv(acpx_module.TRANSPORT_ENV, "off")
    _stub_binary(monkeypatch, tmp_path)
    _stub_grok(monkeypatch, tmp_path)
    adapter = AcpxGrokShadowAdapter()

    with pytest.raises(AcpxShadowRefusalError):
        _build_grok(adapter, cwd=tmp_path)


def test_grok_build_invocation_active_requires_controller_scope(tmp_path, monkeypatch):
    monkeypatch.setenv(acpx_module.TRANSPORT_ENV, "active")
    _stub_binary(monkeypatch, tmp_path)
    _stub_grok(monkeypatch, tmp_path)
    adapter = AcpxGrokShadowAdapter()
    tool_config = {
        "acpx_discussion": True,
        "target_agent": "grok",
        "correlation_id": "corr-1",
        "idempotency_key": "idem-1",
    }

    with pytest.raises(AcpxShadowRefusalError, match="discussion controller"):
        _build_grok(adapter, cwd=tmp_path, tool_config=tool_config)

    with acpx_module.active_discussion_scope():
        plan = _build_grok(adapter, cwd=tmp_path, tool_config=tool_config)
    assert plan.cmd[0] == str(acpx_module._ACPX_BINARY)


def test_grok_build_invocation_requires_explicit_shadow_marker(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path)
    _stub_grok(monkeypatch, tmp_path)
    adapter = AcpxGrokShadowAdapter()

    with pytest.raises(AcpxShadowRefusalError, match="acpx_shadow"):
        _build_grok(adapter, cwd=tmp_path, tool_config={})


def test_grok_build_invocation_rejects_unsupported_tool_config(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path)
    _stub_grok(monkeypatch, tmp_path)
    adapter = AcpxGrokShadowAdapter()

    with pytest.raises(AcpxShadowRefusalError, match="unsupported tool_config"):
        _build_grok(
            adapter,
            cwd=tmp_path,
            tool_config={
                "acpx_shadow": True,
                "target_agent": "grok",
                "allowed_tools": ["Bash"],
            },
        )


def test_grok_build_invocation_rejects_non_grok_target(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path)
    _stub_grok(monkeypatch, tmp_path)
    adapter = AcpxGrokShadowAdapter()

    with pytest.raises(AcpxShadowRefusalError, match="target_agent"):
        _build_grok(
            adapter,
            cwd=tmp_path,
            tool_config={
                "acpx_shadow": True,
                "target_agent": "codex",
                "correlation_id": "corr-1",
                "idempotency_key": "idem-1",
            },
        )


def test_grok_build_invocation_rejects_session_id(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path)
    _stub_grok(monkeypatch, tmp_path)
    adapter = AcpxGrokShadowAdapter()

    with pytest.raises(AcpxShadowRefusalError, match="session_id"):
        _build_grok(adapter, cwd=tmp_path, session_id="prior-session")


def test_grok_build_invocation_rejects_wrong_model(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path)
    _stub_grok(monkeypatch, tmp_path)
    adapter = AcpxGrokShadowAdapter()

    with pytest.raises(AcpxShadowRefusalError, match="model="):
        _build_grok(adapter, cwd=tmp_path, model="grok-3")


def test_grok_build_invocation_rejects_wrong_effort(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path)
    _stub_grok(monkeypatch, tmp_path)
    adapter = AcpxGrokShadowAdapter()

    with pytest.raises(AcpxShadowRefusalError, match="effort="):
        _build_grok(adapter, cwd=tmp_path, effort="low")


def test_grok_build_invocation_refuses_primary_checkout(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path)
    _stub_grok(monkeypatch, tmp_path)
    monkeypatch.setattr(
        acpx_module._worktree_containment,
        "classify_repo_path",
        lambda *_args, **_kwargs: "primary_checkout",
    )
    adapter = AcpxGrokShadowAdapter()

    with pytest.raises(AcpxShadowRefusalError, match="primary checkout"):
        _build_grok(adapter, cwd=tmp_path)


def test_grok_build_invocation_accepts_compatible_acpx_version_drift(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path, version="0.14.0")
    _stub_grok(monkeypatch, tmp_path)

    plan = _build_grok(AcpxGrokShadowAdapter(), cwd=tmp_path)

    assert plan.metadata["acpx_cli_version"] == "0.14.0"


def test_grok_build_invocation_rejects_missing_acpx_capability(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path, missing=("--agent",))
    _stub_grok(monkeypatch, tmp_path)

    with pytest.raises(AcpxShadowRefusalError, match="--agent"):
        _build_grok(AcpxGrokShadowAdapter(), cwd=tmp_path)


def test_grok_build_invocation_accepts_rolling_cli_version(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path)
    _stub_grok(monkeypatch, tmp_path, version="0.3.7")
    adapter = AcpxGrokShadowAdapter()

    plan = _build_grok(adapter, cwd=tmp_path)

    assert plan.metadata["grok_cli_version"] == "0.3.7"
    assert plan.metadata["grok_cli_compatibility"] == "agent-stdio-v1"


def test_grok_build_invocation_accepts_unknown_version_when_capabilities_pass(
    tmp_path, monkeypatch
):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path)
    _stub_grok(monkeypatch, tmp_path, version="unknown")
    adapter = AcpxGrokShadowAdapter()

    plan = _build_grok(adapter, cwd=tmp_path)

    assert plan.metadata["grok_cli_version"] == "unknown"


def test_grok_build_invocation_rejects_missing_cli_capability(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path)
    _stub_grok(monkeypatch, tmp_path, version="0.3.7", missing=("--agent-profile",))
    adapter = AcpxGrokShadowAdapter()

    with pytest.raises(
        AcpxShadowRefusalError,
        match="missing capabilities: --agent-profile",
    ):
        _build_grok(adapter, cwd=tmp_path)


def test_grok_build_invocation_fixed_command_and_ordering(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path)
    grok = _stub_grok(monkeypatch, tmp_path)
    adapter = AcpxGrokShadowAdapter()

    plan = _build_grok(adapter, cwd=tmp_path, prompt="shadow compare prompt")

    assert plan.cmd[0] == str(acpx_module._ACPX_BINARY)
    assert Path(plan.cmd[0]).is_absolute() or plan.cmd[0].startswith(str(tmp_path))
    assert "grok-build" not in plan.cmd
    assert "codex" not in plan.cmd
    assert plan.cmd[-3:] == ["exec", "-f", "-"]
    assert "--agent" in plan.cmd
    agent_idx = plan.cmd.index("--agent")
    agent_cmd = plan.cmd[agent_idx + 1]
    # Single --agent argument: absolute shell-safe binary + exact argv order.
    expected_agent = " ".join(
        [
            shlex.quote(str(grok)),
            "agent",
            "--model",
            "grok-4.5",
            "--reasoning-effort",
            "high",
            "--agent-profile",
            str(acpx_module._GROK_PROFILE_PATH),
            "--no-leader",
            "stdio",
        ]
    )
    assert agent_cmd == expected_agent
    tokens = shlex.split(agent_cmd)
    assert tokens[0] == str(grok)
    assert Path(tokens[0]).is_absolute()
    assert tokens[1:] == [
        "agent",
        "--model",
        "grok-4.5",
        "--reasoning-effort",
        "high",
        "--agent-profile",
        str(acpx_module._GROK_PROFILE_PATH),
        "--no-leader",
        "stdio",
    ]
    # --agent must not be combined with a positional agent name before exec.
    assert plan.cmd[agent_idx + 2] == "exec"

    pairs = list(zip(plan.cmd, plan.cmd[1:], strict=False))
    assert ("--auth-policy", "fail") in pairs
    assert ("--non-interactive-permissions", "fail") in pairs
    assert ("--allowed-tools", "") in pairs
    assert ("--max-turns", "1") in pairs
    assert ("--prompt-retries", "0") in pairs
    assert "--deny-all" in plan.cmd
    assert "--no-fs" in plan.cmd
    assert "--no-terminal" in plan.cmd
    assert "--model" not in plan.cmd  # model lives only inside --agent
    assert plan.stdin_payload == "shadow compare prompt"
    assert "shadow compare prompt" not in plan.cmd


def test_grok_build_invocation_accepts_none_or_fixed_model_and_effort(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path)
    _stub_grok(monkeypatch, tmp_path)
    adapter = AcpxGrokShadowAdapter()

    for model, effort in ((None, None), ("grok-4.5", None), (None, "high"), ("grok-4.5", "high")):
        plan = _build_grok(adapter, cwd=tmp_path, model=model, effort=effort)
        assert plan.metadata["model"] == "grok-4.5"
        assert plan.metadata["effort"] == "high"
        assert plan.metadata["target_agent"] == "grok"
        assert plan.metadata["grok_cli_version"] == "0.2.118"
        assert plan.metadata["grok_cli_compatibility"] == "agent-stdio-v1"
        assert plan.metadata["acpx_cli_version"] == "0.13.0"
        assert plan.metadata["acpx_cli_compatibility"] == "json-one-shot-v1"


def test_grok_build_invocation_auth_env_sets_cached_token_and_scrubs_xai_keys(
    tmp_path, monkeypatch
):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path)
    _stub_grok(monkeypatch, tmp_path)
    adapter = AcpxGrokShadowAdapter()

    plan = _build_grok(adapter, cwd=tmp_path)
    assert plan.env_overrides == {"ACPX_AUTH_CACHED_TOKEN": "1"}
    assert "XAI_API_KEY" in plan.env_unsets
    assert "GROK_API_KEY" in plan.env_unsets
    assert "ACPX_AUTH_XAI_API_KEY" in plan.env_unsets
    assert "ACPX_AUTH_API_KEY" in plan.env_unsets
    # Never forward credentials into argv, stdin, or metadata.
    for blob in (plan.cmd, [plan.stdin_payload], list(plan.metadata.values())):
        serialized = " ".join(str(x) for x in blob)
        assert "sk-" not in serialized
        assert "xai-" not in serialized.lower() or "xai_api_key" not in serialized.lower()


def test_grok_build_invocation_stamps_metadata_without_forwarding(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path)
    _stub_grok(monkeypatch, tmp_path)
    adapter = AcpxGrokShadowAdapter()

    plan = _build_grok(
        adapter,
        cwd=tmp_path,
        prompt="investigate flaky test",
        task_id="task-grok-42",
        tool_config={
            "acpx_shadow": True,
            "target_agent": "grok",
            "correlation_id": "corr-g.1",
            "idempotency_key": "idem-g:9",
        },
    )
    assert plan.metadata["task_id"] == "task-grok-42"
    assert plan.metadata["correlation_id"] == "corr-g.1"
    assert plan.metadata["idempotency_key"] == "idem-g:9"
    for value in ("task-grok-42", "corr-g.1", "idem-g:9"):
        assert value not in plan.cmd
        assert value not in plan.stdin_payload


def test_grok_build_invocation_rejects_write_mode(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path)
    _stub_grok(monkeypatch, tmp_path)
    adapter = AcpxGrokShadowAdapter()

    with pytest.raises(ValueError, match="mode"):
        adapter.build_invocation(
            prompt="ping",
            mode="workspace-write",
            cwd=tmp_path,
            model=None,
            task_id="t-1",
            session_id=None,
            tool_config={
                "acpx_shadow": True,
                "target_agent": "grok",
                "correlation_id": "corr-1",
                "idempotency_key": "idem-1",
            },
        )


def test_grok_parse_response_success_compatible_with_codex_parser():
    adapter = AcpxGrokShadowAdapter()
    result = adapter.parse_response(
        stdout=_SUCCESS_NDJSON,
        stderr="",
        returncode=0,
        output_file=None,
    )
    assert result.ok is True
    assert result.response == "Hello world."
    assert result.session_id is None
    assert result.tool_calls == []


def test_grok_parse_response_timeout_and_auth_fail_closed():
    adapter = AcpxGrokShadowAdapter()
    timeout = adapter.parse_response(
        stdout=_TIMEOUT_NDJSON, stderr="", returncode=3, output_file=None
    )
    assert timeout.ok is False
    assert "TIMEOUT" in timeout.stderr_excerpt

    auth = adapter.parse_response(
        stdout=_AUTH_REQUIRED_NDJSON, stderr="", returncode=1, output_file=None
    )
    assert auth.ok is False
    assert "AUTH_REQUIRED" in auth.stderr_excerpt


def test_grok_parse_response_cancel_crash_malformed_replay_fail_closed():
    adapter = AcpxGrokShadowAdapter()
    for stdout, rc, needle in (
        (_CANCELLED_NDJSON, 0, "cancelled"),
        (_CRASH_NO_TERMINAL_NDJSON, -9, "without a terminal"),
        (_MALFORMED_LINE_NDJSON, -9, "malformed"),
        (_DUPLICATE_REPLAY_NDJSON, 0, "duplicate"),
        (_AGENT_DISCONNECTED_NDJSON, 1, "AGENT_DISCONNECTED"),
    ):
        result = adapter.parse_response(stdout=stdout, stderr="", returncode=rc, output_file=None)
        assert result.ok is False
        assert result.response == ""
        assert needle.lower() in (result.stderr_excerpt or "").lower()


def test_codex_adapter_unchanged_still_targets_codex_only(tmp_path, monkeypatch):
    """Regression: Codex seat must not become a generic multi-agent adapter."""
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path)
    adapter = AcpxAdapter()
    plan = _build(adapter, cwd=tmp_path)
    assert adapter.name == "acpx-codex-shadow"
    assert "codex" in plan.cmd
    assert "exec" in plan.cmd
    assert "--agent" not in plan.cmd
    assert "grok-build" not in plan.cmd
    assert plan.env_overrides == {"ACPX_AUTH_CHAT_GPT": "1"}
    assert build_agent_env(provider=adapter.name, overrides=plan.env_overrides)[
        "ACPX_AUTH_CHAT_GPT"
    ] == "1"
    assert plan.env_unsets == ()
    with pytest.raises(AcpxShadowRefusalError, match="target_agent"):
        _build(
            adapter,
            cwd=tmp_path,
            tool_config={
                "acpx_shadow": True,
                "target_agent": "grok",
                "correlation_id": "corr-1",
                "idempotency_key": "idem-1",
            },
        )


@pytest.mark.parametrize(
    ("adapter_class", "participant", "acpx_agent", "fixed_model", "auth_env"),
    [
        (AcpxClaudeShadowAdapter, "claude", "claude", "claude-sonnet-5", None),
        (AcpxKimiShadowAdapter, "kimi", "kimi", None, "ACPX_AUTH_LOGIN"),
        (AcpxKimiCcShadowAdapter, "kimicc", "kimi", "kimi-code/k3", "ACPX_AUTH_LOGIN"),
        (AcpxCursorShadowAdapter, "cursor", "cursor", None, "ACPX_AUTH_CURSOR_LOGIN"),
        (AcpxPoolShadowAdapter, "pool", "pool", None, None),
    ],
)
def test_builtin_discussion_seats_are_fixed_active_only_and_confined(
    tmp_path, monkeypatch, adapter_class, participant, acpx_agent, fixed_model, auth_env
):
    _stub_binary(monkeypatch, tmp_path)
    adapter = adapter_class()
    tool_config = {
        "acpx_discussion": True,
        "target_agent": acpx_agent,
        "correlation_id": "corr-1",
        "idempotency_key": "idem-1",
    }

    monkeypatch.setenv(acpx_module.TRANSPORT_ENV, "active")
    with pytest.raises(AcpxShadowRefusalError, match="discussion controller"):
        adapter.build_invocation(
            prompt="ping",
            mode="read-only",
            cwd=tmp_path,
            model=fixed_model,
            task_id="t-1",
            session_id=None,
            tool_config=tool_config,
        )

    with acpx_module.active_discussion_scope():
        plan = adapter.build_invocation(
            prompt="ping",
            mode="read-only",
            cwd=tmp_path,
            model=fixed_model,
            task_id="t-1",
            session_id=None,
            tool_config=tool_config,
        )

    assert adapter.name == f"acpx-{participant}-shadow"
    assert plan.cmd[-4:] == [acpx_agent, "exec", "-f", "-"]
    assert plan.env_overrides == ({} if auth_env is None else {auth_env: "1"})
    sanitized_env = build_agent_env(provider=adapter.name, overrides=plan.env_overrides)
    if auth_env is not None:
        assert sanitized_env[auth_env] == "1"
    assert plan.metadata["target_agent"] == acpx_agent
    assert plan.metadata["acpx_discussion"] is True
    assert "--deny-all" in plan.cmd
    assert "--no-fs" in plan.cmd
    assert "--no-terminal" in plan.cmd
    assert ("--allowed-tools", "") in zip(plan.cmd, plan.cmd[1:], strict=False)
    if fixed_model is None:
        assert "--model" not in plan.cmd
        assert "model" not in plan.metadata
    else:
        assert ("--model", fixed_model) in zip(plan.cmd, plan.cmd[1:], strict=False)
        assert plan.metadata["model"] == fixed_model
    if participant == "claude":
        assert plan.metadata["effort"] == "high"


def test_builtin_discussion_seat_rejects_shadow_marker_wrong_target_and_session(tmp_path, monkeypatch):
    _shadow_env(monkeypatch)
    _stub_binary(monkeypatch, tmp_path)
    adapter = AcpxClaudeShadowAdapter()
    base = {"target_agent": "claude", "correlation_id": "corr-1", "idempotency_key": "idem-1"}
    with pytest.raises(AcpxShadowRefusalError, match="acpx_discussion"):
        adapter.build_invocation(
            prompt="ping", mode="read-only", cwd=tmp_path, model=None, task_id="t-1", session_id=None,
            tool_config={"acpx_shadow": True, **base},
        )
    monkeypatch.setenv(acpx_module.TRANSPORT_ENV, "active")
    with acpx_module.active_discussion_scope():
        with pytest.raises(AcpxShadowRefusalError, match="target_agent"):
            adapter.build_invocation(
                prompt="ping", mode="read-only", cwd=tmp_path, model=None, task_id="t-1", session_id=None,
                tool_config={"acpx_discussion": True, **base, "target_agent": "pool"},
            )
        with pytest.raises(AcpxShadowRefusalError, match="session_id"):
            adapter.build_invocation(
                prompt="ping", mode="read-only", cwd=tmp_path, model=None, task_id="t-1", session_id="prior",
                tool_config={"acpx_discussion": True, **base},
            )


def test_kimicc_rejects_a_caller_model_other_than_its_exact_pin(tmp_path, monkeypatch):
    monkeypatch.setenv(acpx_module.TRANSPORT_ENV, "active")
    _stub_binary(monkeypatch, tmp_path)
    with acpx_module.active_discussion_scope(), pytest.raises(AcpxShadowRefusalError, match="model="):
        AcpxKimiCcShadowAdapter().build_invocation(
            prompt="ping",
            mode="read-only",
            cwd=tmp_path,
            model="kimi-code/other",
            task_id="t-1",
            session_id=None,
            tool_config={
                "acpx_discussion": True,
                "target_agent": "kimi",
                "correlation_id": "corr-1",
                "idempotency_key": "idem-1",
            },
        )


def test_supported_participant_registry_has_only_fixed_direct_seats():
    assert ACPX_SUPPORTED_PARTICIPANTS == {
        "codex": {"seat": "acpx-codex-shadow", "agent": "codex", "model": None},
        "grok": {"seat": "acpx-grok-shadow", "agent": "grok", "model": "grok-4.5"},
        "claude": {
            "seat": "acpx-claude-shadow",
            "agent": "claude",
            "model": None,
        },
        "kimi": {"seat": "acpx-kimi-shadow", "agent": "kimi", "model": None},
        "kimicc": {"seat": "acpx-kimicc-shadow", "agent": "kimi", "model": "kimi-code/k3"},
        "cursor": {"seat": "acpx-cursor-shadow", "agent": "cursor", "model": None},
        "pool": {"seat": "acpx-pool-shadow", "agent": "pool", "model": None},
        "agy": {
            "seat": "acpx-agy-shadow",
            "agent": "agy",
            "model": "gemini-3.6-flash-high",
        },
        "glm": {"seat": "acpx-glm-shadow", "agent": "glm", "model": "glm-5.2"},
        "deepseek": {
            "seat": "acpx-deepseek-shadow",
            "agent": "deepseek",
            "model": "deepseek-v4-pro",
        },
    }


@pytest.mark.parametrize(
    ("adapter_class", "participant", "provider_binary", "version", "model"),
    [
        (AcpxAgyShadowAdapter, "agy", "agy", "1.1.9", "gemini-3.6-flash-high"),
        (AcpxGlmShadowAdapter, "glm", "opencode", "1.17.13", "glm-5.2"),
        (AcpxDeepSeekShadowAdapter, "deepseek", "hermes", "0.18.2", "deepseek-v4-pro"),
    ],
)
def test_new_fleet_discussion_seats_use_fixed_confined_commands(
    tmp_path, monkeypatch, adapter_class, participant, provider_binary, version, model
):
    _stub_binary(monkeypatch, tmp_path)
    binaries = {}
    for name in ("node", provider_binary):
        path = tmp_path / name
        path.write_text("#!/bin/sh\n", encoding="utf-8")
        path.chmod(0o755)
        binaries[name] = str(path)
    monkeypatch.setattr(acpx_module.shutil, "which", lambda name: binaries.get(name))
    monkeypatch.setattr(
        acpx_module,
        "_probe_participant_cli_compatibility",
        lambda _path, _executable: (version, ()),
    )
    monkeypatch.setenv(acpx_module.TRANSPORT_ENV, "active")
    for name in ("CI", "GITHUB_ACTIONS", "GITLAB_CI", "BUILDKITE", "JENKINS_URL"):
        monkeypatch.delenv(name, raising=False)

    adapter = adapter_class()
    with acpx_module.active_discussion_scope():
        plan = adapter.build_invocation(
            prompt="ping",
            mode="read-only",
            cwd=tmp_path,
            model=model,
            task_id="t-1",
            session_id=None,
            tool_config={
                "acpx_discussion": True,
                "target_agent": participant,
                "correlation_id": "corr-1",
                "idempotency_key": "idem-1",
            },
        )

    assert adapter.name == f"acpx-{participant}-shadow"
    assert "--agent" in plan.cmd
    command = plan.cmd[plan.cmd.index("--agent") + 1]
    command_tokens = shlex.split(command)
    assert command_tokens[0] == binaries[provider_binary if participant == "glm" else "node"]
    assert provider_binary in " ".join(command_tokens)
    assert plan.cmd[-3:] == ["exec", "-f", "-"]
    assert plan.metadata["model"] == model
    assert plan.metadata["provider_cli_version"] == version
    assert plan.metadata["provider_cli_compatibility"] == {
        "agy": "text-plan-sandbox-v1",
        "glm": "native-acp-pure-v1",
        "deepseek": "text-oneshot-isolated-v1",
    }[participant]
    assert "--deny-all" in plan.cmd
    assert "--no-fs" in plan.cmd
    assert "--no-terminal" in plan.cmd
    if participant == "glm":
        assert ("--model", "zai-coding-plan/glm-5.2") in zip(
            plan.cmd, plan.cmd[1:], strict=False
        )
        assert plan.env_overrides == {
            "ACPX_AUTH_OPENCODE_LOGIN": "1",
            "OPENCODE_CONFIG_CONTENT": '{"permission":{"*":"deny"},"tools":{"*":false}}'
        }
        assert build_agent_env(provider=adapter.name, overrides=plan.env_overrides)[
            "ACPX_AUTH_OPENCODE_LOGIN"
        ] == "1"
        assert build_agent_env(provider=adapter.name, overrides=plan.env_overrides)[
            "OPENCODE_CONFIG_CONTENT"
        ] == plan.env_overrides["OPENCODE_CONFIG_CONTENT"]
    else:
        assert "--model" not in plan.cmd
        assert plan.env_overrides == {}


def test_new_fleet_discussion_seat_accepts_provider_cli_version_drift(tmp_path, monkeypatch):
    _stub_binary(monkeypatch, tmp_path)
    agy = tmp_path / "agy"
    node = tmp_path / "node"
    for path in (agy, node):
        path.write_text("#!/bin/sh\n", encoding="utf-8")
        path.chmod(0o755)
    monkeypatch.setattr(
        acpx_module.shutil,
        "which",
        lambda name: str({"agy": agy, "node": node}[name]),
    )
    monkeypatch.setattr(
        acpx_module,
        "_probe_participant_cli_compatibility",
        lambda _path, _executable: ("9.9.9", ()),
    )
    monkeypatch.setenv(acpx_module.TRANSPORT_ENV, "active")

    with acpx_module.active_discussion_scope():
        plan = AcpxAgyShadowAdapter().build_invocation(
            prompt="ping",
            mode="read-only",
            cwd=tmp_path,
            model="gemini-3.6-flash-high",
            task_id="t-1",
            session_id=None,
            tool_config={
                "acpx_discussion": True,
                "target_agent": "agy",
                "correlation_id": "corr-1",
                "idempotency_key": "idem-1",
            },
        )

    assert plan.metadata["provider_cli_version"] == "9.9.9"


def test_new_fleet_discussion_seat_rejects_missing_provider_capability(tmp_path, monkeypatch):
    _stub_binary(monkeypatch, tmp_path)
    agy = tmp_path / "agy"
    node = tmp_path / "node"
    for path in (agy, node):
        path.write_text("#!/bin/sh\n", encoding="utf-8")
        path.chmod(0o755)
    monkeypatch.setattr(
        acpx_module.shutil,
        "which",
        lambda name: str({"agy": agy, "node": node}[name]),
    )
    monkeypatch.setattr(
        acpx_module,
        "_probe_participant_cli_compatibility",
        lambda _path, _executable: ("2.0.0", ("--sandbox",)),
    )
    monkeypatch.setenv(acpx_module.TRANSPORT_ENV, "active")

    with acpx_module.active_discussion_scope(), pytest.raises(
        AcpxShadowRefusalError, match="--sandbox"
    ):
        AcpxAgyShadowAdapter().build_invocation(
            prompt="ping",
            mode="read-only",
            cwd=tmp_path,
            model="gemini-3.6-flash-high",
            task_id="t-1",
            session_id=None,
            tool_config={
                "acpx_discussion": True,
                "target_agent": "agy",
                "correlation_id": "corr-1",
                "idempotency_key": "idem-1",
            },
        )


def test_participant_version_probe_accepts_v_prefix_before_build_stamp(tmp_path):
    binary = tmp_path / "hermes"
    binary.write_text(
        "#!/bin/sh\nprintf '%s\\n' 'Python 3.11.15' "
        "'Hermes Agent v0.18.2 (2026.7.7.2)'\n",
        encoding="utf-8",
    )
    binary.chmod(0o755)

    assert acpx_module._probe_participant_cli_version(str(binary), "hermes") == "0.18.2"


def test_acpx_compatibility_probe_checks_global_and_builtin_exec_surfaces(monkeypatch):
    class _Proc:
        def __init__(self, stdout: str, returncode: int = 0):
            self.stdout = stdout
            self.stderr = ""
            self.returncode = returncode

    root_help = " ".join((*acpx_module._ACPX_REQUIRED_GLOBAL_FLAGS, "codex participant"))

    def _compatible(argv, **_kwargs):
        if argv[-1] == "--version":
            return _Proc("0.14.7\n")
        if argv[1:] == ["--help"]:
            return _Proc(root_help)
        if argv[1:] == ["codex", "exec", "--help"]:
            return _Proc("one-shot --file input")
        raise AssertionError(argv)

    monkeypatch.setattr(acpx_module.subprocess, "run", _compatible)
    assert acpx_module._probe_acpx_cli_compatibility(
        "/tmp/acpx", builtin_agent="codex"
    ) == ("0.14.7", ())

    def _missing_json_strict(argv, **kwargs):
        proc = _compatible(argv, **kwargs)
        if argv[1:] == ["--help"]:
            proc.stdout = root_help.replace("--json-strict", "")
        return proc

    monkeypatch.setattr(acpx_module.subprocess, "run", _missing_json_strict)
    assert acpx_module._probe_acpx_cli_compatibility(
        "/tmp/acpx", builtin_agent="codex"
    ) == ("0.14.7", ("--json-strict",))


@pytest.mark.parametrize(
    ("executable", "help_args", "required_flag"),
    [
        ("agy", (), "--sandbox"),
        ("opencode", ("acp",), "--pure"),
        ("hermes", (), "--ignore-rules"),
    ],
)
def test_participant_compatibility_probes_exact_invoked_surface(
    monkeypatch, executable, help_args, required_flag
):
    required = {
        "agy": acpx_module._AGY_REQUIRED_FLAGS,
        "opencode": acpx_module._OPENCODE_REQUIRED_ACP_FLAGS,
        "hermes": acpx_module._HERMES_REQUIRED_FLAGS,
    }[executable]
    monkeypatch.setattr(
        acpx_module,
        "_probe_participant_cli_version",
        lambda _binary, _executable: "9.9.9",
    )
    monkeypatch.setattr(
        acpx_module,
        "_probe_cli_help",
        lambda _binary, *args: " ".join(required) if args == help_args else "",
    )

    assert acpx_module._probe_participant_cli_compatibility(
        f"/tmp/{executable}", executable
    ) == ("9.9.9", ())

    monkeypatch.setattr(
        acpx_module,
        "_probe_cli_help",
        lambda _binary, *args: "usage "
        + " ".join(flag for flag in required if flag != required_flag),
    )
    assert acpx_module._probe_participant_cli_compatibility(
        f"/tmp/{executable}", executable
    ) == ("9.9.9", (required_flag,))


def test_text_agent_digest_mismatch_refuses_before_spawn(tmp_path, monkeypatch):
    text_agent = tmp_path / "acp_text_agent.mjs"
    text_agent.write_text("unreviewed confinement change\n", encoding="utf-8")
    monkeypatch.setattr(acpx_module, "_TEXT_AGENT_PATH", text_agent)

    with pytest.raises(AcpxShadowRefusalError, match="digest mismatch"):
        acpx_module._require_text_agent(adapter_label="AcpxAgyShadowAdapter")


def test_build_grok_agent_command_quotes_absolute_paths_with_spaces(tmp_path):
    abs_path = tmp_path / "path with spaces" / "grok"
    profile_path = tmp_path / "profile with spaces" / "read only.md"
    abs_path.parent.mkdir(parents=True)
    profile_path.parent.mkdir(parents=True)
    abs_path.write_text("#!/bin/sh\n", encoding="utf-8")
    profile_path.write_text("---\nname: read-only\n---\n", encoding="utf-8")
    cmd = acpx_module._build_grok_agent_command(str(abs_path), str(profile_path))
    tokens = shlex.split(cmd)
    assert tokens[0] == str(abs_path)
    assert tokens[1:] == [
        "agent",
        "--model",
        "grok-4.5",
        "--reasoning-effort",
        "high",
        "--agent-profile",
        str(profile_path),
        "--no-leader",
        "stdio",
    ]


def test_grok_profile_is_exact_and_digest_mismatch_fails_closed(tmp_path, monkeypatch):
    assert acpx_module._require_grok_profile() == str(acpx_module._GROK_PROFILE_PATH)

    changed = tmp_path / "changed-profile.md"
    changed.write_text("---\nname: changed\n---\n", encoding="utf-8")
    monkeypatch.setattr(acpx_module, "_GROK_PROFILE_PATH", changed)
    with pytest.raises(AcpxShadowRefusalError, match="digest mismatch"):
        acpx_module._require_grok_profile()


def test_probe_grok_version_parses_semver_or_returns_empty(monkeypatch, tmp_path):
    binary = tmp_path / "grok"
    binary.write_text("#!/bin/sh\n", encoding="utf-8")
    binary.chmod(0o755)

    class _Proc:
        def __init__(self, stdout: str, stderr: str = "", returncode: int = 0):
            self.stdout = stdout
            self.stderr = stderr
            self.returncode = returncode

    monkeypatch.setattr(
        acpx_module.subprocess,
        "run",
        lambda *_a, **_k: _Proc("grok 0.2.118 (1e1687c1cf6a)\n"),
    )
    assert acpx_module._probe_grok_version(str(binary)) == "0.2.118"

    monkeypatch.setattr(
        acpx_module.subprocess,
        "run",
        lambda *_a, **_k: _Proc("not a version string"),
    )
    assert acpx_module._probe_grok_version(str(binary)) == ""

    monkeypatch.setattr(
        acpx_module.subprocess,
        "run",
        lambda *_a, **_k: _Proc(
            "wrapper 9.9.9; grok 0.2.118 (1e1687c1cf6a)\n"
        ),
    )
    assert acpx_module._probe_grok_version(str(binary)) == ""

    monkeypatch.setattr(
        acpx_module.subprocess,
        "run",
        lambda *_a, **_k: _Proc(
            "grok 0.2.118 (1e1687c1cf6a)\n",
            "fatal: startup failed\n",
            returncode=1,
        ),
    )
    assert acpx_module._probe_grok_version(str(binary)) == ""

    def _boom(*_a, **_k):
        raise OSError("missing")

    monkeypatch.setattr(acpx_module.subprocess, "run", _boom)
    assert acpx_module._probe_grok_version(str(binary)) == ""


def test_probe_grok_cli_compatibility_checks_required_command_surface(monkeypatch):
    class _Proc:
        def __init__(self, stdout: str, returncode: int = 0):
            self.stdout = stdout
            self.stderr = ""
            self.returncode = returncode

    agent_help = " ".join(acpx_module._GROK_REQUIRED_AGENT_FLAGS)

    def _compatible(argv, **_kwargs):
        if argv[-1] == "--version":
            return _Proc("grok 0.3.7 (rolling)\n")
        if argv[1:] == ["agent", "--help"]:
            return _Proc(agent_help)
        if argv[1:] == ["agent", "stdio", "--help"]:
            return _Proc("Run the agent over stdio")
        raise AssertionError(argv)

    monkeypatch.setattr(acpx_module.subprocess, "run", _compatible)
    assert acpx_module._probe_grok_cli_compatibility("/tmp/grok") == ("0.3.7", ())

    def _missing_profile(argv, **kwargs):
        proc = _compatible(argv, **kwargs)
        if argv[1:] == ["agent", "--help"]:
            proc.stdout = agent_help.replace("--agent-profile", "")
        return proc

    monkeypatch.setattr(acpx_module.subprocess, "run", _missing_profile)
    assert acpx_module._probe_grok_cli_compatibility("/tmp/grok") == (
        "0.3.7",
        ("--agent-profile",),
    )

    def _missing_stdio(argv, **kwargs):
        if argv[1:] == ["agent", "stdio", "--help"]:
            return _Proc("", returncode=2)
        return _compatible(argv, **kwargs)

    monkeypatch.setattr(acpx_module.subprocess, "run", _missing_stdio)
    assert acpx_module._probe_grok_cli_compatibility("/tmp/grok") == (
        "0.3.7",
        ("agent stdio",),
    )
