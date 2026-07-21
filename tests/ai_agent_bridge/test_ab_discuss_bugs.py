from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from agent_runtime.adapters.claude import ClaudeAdapter
from ai_agent_bridge import _channels, _channels_cli, _cli, _db


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

    prompts: list[str] = []
    round_responses: list[str] = []

    def fake_invoke(agent_name: str, prompt: str, **kwargs):
        prompts.append(prompt)
        # Each round's reply carries a distinct marker token so we can
        # assert later rounds see the earlier-round replies in their
        # prompt history.
        round_idx = len(prompts)
        marker = f"ROUND_{round_idx}_REPLY_MARKER_{agent_name.upper()}"
        body = f"{('x' * 200)} {marker}\n[DISAGREE]"
        round_responses.append(body)
        return SimpleNamespace(ok=True, response=body, stderr_excerpt="", session_id=None)

    monkeypatch.setattr("agent_runtime.runner.invoke", fake_invoke)

    root_body = "ROOT QUESTION: preserve this exact discussion brief."
    args = SimpleNamespace(
        channel="architecture",
        body=root_body,
        with_agents="codex",
        max_rounds=4,
        review=False,
    )

    assert _channels_cli._handle_discuss(args) == 0
    assert len(prompts) == 4
    # Round 4 prompt must include the root.
    assert root_body in prompts[3]
    # Round 4 prompt must include rounds 1-3 replies (thread-mode
    # contract — peer round replies are load-bearing, never dropped).
    for previous_round in (1, 2, 3):
        marker = f"ROUND_{previous_round}_REPLY_MARKER_CODEX"
        assert marker in prompts[3], (
            f"Round 4 prompt is missing ROUND_{previous_round} reply marker — "
            f"#1808 thread-mode regression"
        )
    # Channel noise from before the discussion started must NOT appear
    # — thread mode skips the channel-wide tail entirely.
    assert "prior message 0" not in prompts[3]
    assert "prior message 204" not in prompts[3]


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

    def fake_ask_codex(
        content,
        task_id,
        msg_type,
        data,
        new_session,
        from_llm,
        from_model,
        to_model,
        no_timeout,
        **kwargs,
    ):
        captured["from_llm"] = from_llm
        return 123

    monkeypatch.setattr(_cli, "ask_codex", fake_ask_codex)
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

    def fake_ask_agy(
        content,
        task_id,
        msg_type,
        data,
        new_session,
        from_llm,
        from_model,
        to_model,
        no_timeout,
        **kwargs,
    ):
        captured.update(
            content=content,
            task_id=task_id,
            msg_type=msg_type,
            data=data,
            new_session=new_session,
            from_llm=from_llm,
            from_model=from_model,
            to_model=to_model,
            no_timeout=no_timeout,
            kwargs=kwargs,
        )
        return 123

    monkeypatch.setattr(_cli, "ask_agy", fake_ask_agy)
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
    assert captured["from_llm"] == "codex"
    assert captured["to_model"] == "gemini-3.1-pro-high"
    assert captured["new_session"] is False
    assert captured["no_timeout"] is False
    assert captured["kwargs"] == {"stdout_only": True, "output_path": None}
