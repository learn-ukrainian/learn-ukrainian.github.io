"""Focused Gemini adapter regression tests for prompt passing and auth."""

from __future__ import annotations

import logging
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime.adapters.gemini import GeminiAdapter, resolve_gemini_auth_mode
from ai_llm.fallback import GEMINI_AUTH_ENV_VARS


def _build(prompt: str, tmp_path: Path, **kwargs):
    return GeminiAdapter().build_invocation(
        prompt=prompt,
        mode=kwargs.pop("mode", "workspace-write"),
        cwd=tmp_path,
        model=kwargs.pop("model", "gemini-3.1-pro-preview"),
        task_id=None,
        session_id=None,
        tool_config=kwargs.pop("tool_config", None),
        effort=kwargs.pop("effort", None),
    )


def test_small_prompt_uses_inline_p_arg_and_no_stdin(tmp_path):
    prompt = "x" * 200
    plan = _build(prompt, tmp_path)

    assert "-p" in plan.cmd
    assert plan.cmd[plan.cmd.index("-p") + 1] == prompt
    assert plan.stdin_payload == ""
    assert "--approval-mode=yolo" in plan.cmd
    assert "--skip-trust" in plan.cmd


def test_large_prompt_uses_file_ref_and_cleanup(tmp_path):
    prompt = "x" * 200_000
    adapter = GeminiAdapter()
    plan = adapter.build_invocation(
        prompt=prompt,
        mode="workspace-write",
        cwd=tmp_path,
        model="gemini-3.1-pro-preview",
        task_id=None,
        session_id=None,
        tool_config=None,
    )

    prompt_arg = plan.cmd[plan.cmd.index("-p") + 1]
    assert prompt_arg.startswith("@")
    prompt_path = Path(prompt_arg[1:])
    assert prompt_path.read_text(encoding="utf-8") == prompt

    adapter.cleanup_invocation(plan)
    assert not prompt_path.exists()


def test_large_prompt_api_fail_fast_does_not_create_temp_file(tmp_path, monkeypatch):
    monkeypatch.setenv("GEMINI_AUTH_MODE", "api")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    temp_dir = Path(tempfile.gettempdir())
    before = set(temp_dir.glob("learn-ukrainian-gemini-prompt-*"))

    with pytest.raises(RuntimeError, match="GEMINI_AUTH_MODE=api"):
        GeminiAdapter().build_invocation(
            prompt="x" * 200_000,
            mode="workspace-write",
            cwd=tmp_path,
            model="gemini-3.1-pro-preview",
            task_id=None,
            session_id=None,
            tool_config=None,
        )

    after = set(temp_dir.glob("learn-ukrainian-gemini-prompt-*"))
    assert after == before


def test_mcp_server_names_survive_prompt_flag_change(tmp_path):
    plan = _build("hello", tmp_path, tool_config={"mcp_server_names": ["sources"]})

    assert "--allowed-mcp-server-names" in plan.cmd
    assert plan.cmd[plan.cmd.index("--allowed-mcp-server-names") + 1] == "sources"
    assert plan.cmd[plan.cmd.index("-p") + 1] == "hello"


def test_subscription_auth_strips_gemini_api_env_vars(tmp_path, monkeypatch):
    monkeypatch.setenv("GEMINI_AUTH_MODE", "subscription")
    monkeypatch.setenv("GEMINI_API_KEY", "secret")

    plan = _build("hello", tmp_path)

    assert plan.env_unsets == GEMINI_AUTH_ENV_VARS


def test_effort_logs_debug_but_leaves_command_semantics_unchanged(tmp_path, caplog):
    caplog.set_level(logging.DEBUG, logger="agent_runtime.adapters.gemini")

    without_effort = _build("hello", tmp_path)
    with_effort = _build("hello", tmp_path, effort="high")

    assert with_effort.cmd == without_effort.cmd
    assert "gemini effort" in caplog.text


@pytest.mark.parametrize(
    ("env", "expected"),
    [
        ({}, "subscription"),
        ({"GEMINI_API_KEY": "secret"}, "api"),
        ({"GOOGLE_API_KEY": "secret"}, "api"),
        ({"GEMINI_AUTH_MODE": "subscription", "GEMINI_API_KEY": "secret"}, "subscription"),
        ({"GEMINI_AUTH_MODE": "api"}, "api"),
    ],
)
def test_resolve_gemini_auth_mode_api_first_matrix(env, expected):
    assert resolve_gemini_auth_mode(env, cooldown_active=False) == expected
