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


def test_discuss_round_four_prompt_pins_root_after_history_truncation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(_db, "DB_PATH", tmp_path / "bridge.db")
    monkeypatch.setattr(_channels, "fetch_monitor_state", lambda: None)
    monkeypatch.setattr(_channels, "context_sha256", lambda path: "")
    monkeypatch.setattr(
        _channels,
        "load_channel_context",
        lambda channel: {"body": "", "revs": {}, "missing": []},
    )

    _channels.create_channel("architecture", exist_ok=False)
    for index in range(205):
        _channels.post(
            "architecture",
            "user",
            f"prior message {index}",
            auto_snapshot=False,
            verify_citations=False,
        )

    prompts: list[str] = []

    def fake_invoke(agent_name: str, prompt: str, **kwargs):
        prompts.append(prompt)
        return SimpleNamespace(
            ok=True,
            response=("x" * 6000) + "\n[DISAGREE]",
            stderr_excerpt="",
        )

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
    assert "... [" in prompts[3]
    assert root_body in prompts[3]


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
