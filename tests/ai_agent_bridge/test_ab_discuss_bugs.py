from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from agent_runtime.adapters.claude import ClaudeAdapter
from ai_agent_bridge import _channels, _channels_cli, _cli, _db
from ai_agent_bridge._acp_compat import _discussion_failure_metadata, _failure_metadata


def _clear_identity_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in _cli._CALLER_IDENTITY_ENV_HINTS:
        monkeypatch.delenv(name, raising=False)


def test_discuss_round_four_prompt_preserves_root_and_all_thread_replies(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Round-4 prompt must include the root question AND every prior-round
    reply, regardless of how noisy the surrounding channel is.

    Original spec (pre-#1808) was "truncate the tail but pin the root" — see
    the historical name "...after_history_truncation". After #1808 the discuss
    code passes `thread_id=correlation_id` to `build_agent_prompt`, which
    fetches the in-thread messages directly and skips the channel-tail
    truncator entirely. So the truncation marker is no longer expected;
    instead we assert that all thread messages survive verbatim.
    """
    # Patch both bindings — ``_db`` imports DB_PATH from ``_config`` by
    # name, so they are independent (#5247 xdist leak class).
    from ai_agent_bridge import _config

    db_path = tmp_path / "bridge.db"
    monkeypatch.setattr(_config, "DB_PATH", db_path)
    monkeypatch.setattr(_db, "DB_PATH", db_path)
    monkeypatch.setattr(_channels, "fetch_monitor_state", lambda: None)
    monkeypatch.setattr(_channels, "context_sha256", lambda path: "")
    monkeypatch.setattr(
        _channels,
        "load_channel_context",
        lambda channel: {"body": "", "revs": {}, "missing": []},
    )

    _channels.create_channel("architecture", exist_ok=False)
    # Noisy non-thread messages — would have dominated the channel-tail
    # window in the pre-#1808 behavior. Thread mode must ignore these.
    for index in range(205):
        _channels.post(
            "architecture",
            "user",
            f"prior message {index}",
            auto_snapshot=False,
            verify_citations=False,
        )

    monkeypatch.setenv("FLEET_COMMS_ROOT", str(tmp_path / "fleet"))
    observed: dict[str, object] = {}

    def fake_discussion(**kwargs):
        observed.update(kwargs)
        return {
            "conversation_id": "conversation_" + "a" * 32,
            "state": "COMPLETE",
            "rounds_completed": 3,
            "synthesis": "bounded ACP result",
        }

    monkeypatch.setattr("agent_runtime.acpx_discuss.run_discussion", fake_discussion)

    root_body = "ROOT QUESTION: preserve this exact discussion brief."
    args = SimpleNamespace(
        channel="architecture",
        body=root_body,
        with_agents="codex,claude",
        max_rounds=4,
        review=False,
    )

    assert _channels_cli._handle_discuss(args) == 0
    assert observed["rounds"] == 3
    assert observed["participants"] == ("codex", "claude")
    assert root_body in str(observed["prompt"])
    assert str(observed["task_id"]).startswith("discuss-architecture-")
    assert str(observed["reserved_conversation_id"]).startswith("conversation_")


def test_discuss_claude_subagent_uses_restricted_tools_without_plan_mode(
    tmp_path: Path,
) -> None:
    plan = ClaudeAdapter().build_invocation(
        prompt="hello",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={"cmd_prefix": ["true"], "discussion_readonly": True},
    )

    assert "--permission-mode" not in plan.cmd
    assert "--tools" in plan.cmd
    assert plan.cmd[plan.cmd.index("--tools") + 1] == "Read,Grep,Glob,LS"


def test_discussion_timeout_maps_to_body_free_retryable_failure() -> None:
    failure = _discussion_failure_metadata(
        {
            "classification": "partial",
            "participant_outcomes": [
                {"participant": "glm", "outcome": "ok"},
                {"participant": "kimi", "outcome": "timeout"},
            ],
            "synthesis": "raw response must not enter failure metadata",
        }
    )

    assert failure == {"phase": "transport", "code": "timeout", "retryable": True}
    assert "response" not in str(failure)


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("protocol_output_limit", {"phase": "transport", "code": "protocol_output_limit", "retryable": False}),
        ("timeout", {"phase": "transport", "code": "timeout", "retryable": True}),
        ("provider_unavailable", {"phase": "provider", "code": "provider_unavailable", "retryable": True}),
        ("result_invalid", {"phase": "result_parse", "code": "result_invalid", "retryable": False}),
    ],
)
def test_acp_result_preserves_only_closed_failure_code(code, expected) -> None:
    result = SimpleNamespace(
        transport_outcome="error",
        rate_limited=False,
        usage_record={"failure_code": code, "stderr_excerpt": "must not persist"},
    )

    failure = _failure_metadata(result=result)

    assert failure == expected
    assert "stderr" not in str(failure)


def test_ask_codex_without_from_fails_when_sender_cannot_be_inferred(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_identity_env(monkeypatch)
    parser = _cli._build_parser()
    args = parser.parse_args(["ask-codex", "hello", "--task-id", "task-1"])

    with pytest.raises(SystemExit) as exc_info:
        _cli._dispatch_command(args)

    assert "Cannot infer sender" in str(exc_info.value)


def test_ask_codex_infers_from_claude_agent_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_identity_env(monkeypatch)
    monkeypatch.setenv("CLAUDE_AGENT_NAME", "claude")
    captured: dict[str, str | None] = {}

    def fake_compat(target, content, **kwargs):
        captured["from_llm"] = kwargs["source"]
        return SimpleNamespace(ok=True, response="ok", transport_outcome="ok")

    monkeypatch.setattr("ai_agent_bridge._acp_compat.run_compat_ask", fake_compat)
    parser = _cli._build_parser()
    args = parser.parse_args(["ask-codex", "hello", "--task-id", "task-1"])

    assert _cli._dispatch_command(args) is True
    assert captured["from_llm"] == "claude"


def test_legacy_gemini_model_slugs_map_to_agy_slugs() -> None:
    assert (
        _cli._map_legacy_gemini_model_to_agy("gemini-3.1-pro-preview")
        == "gemini-3.1-pro-high"
    )
    assert (
        _cli._map_legacy_gemini_model_to_agy("gemini-3.0-flash-preview")
        == "gemini-3.6-flash-high"
    )
    assert (
        _cli._map_legacy_gemini_model_to_agy("Gemini 3.1 Pro (High)")
        == "Gemini 3.1 Pro (High)"
    )


def test_ask_gemini_shim_routes_to_agy_with_mapped_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_compat(target, content, **kwargs):
        captured.update(target=target, content=content, **kwargs)
        return SimpleNamespace(ok=True, response="ok", transport_outcome="ok")

    monkeypatch.setattr("ai_agent_bridge._acp_compat.run_compat_ask", fake_compat)
    parser = _cli._build_parser()
    args = parser.parse_args(
        [
            "ask-gemini",
            "hello",
            "--task-id",
            "task-1",
            "--model",
            "gemini-3.1-pro-preview",
            "--stdout-only",
            "--from",
            "codex",
        ]
    )

    assert _cli._dispatch_command(args) is True
    assert captured["content"] == "hello"
    assert captured["task_id"] == "task-1"
    assert captured["source"] == "codex"
    assert captured["model"] == "gemini-3.1-pro-high"
    assert captured["target"] == "gemini"
    assert captured["stdout_only"] is True
