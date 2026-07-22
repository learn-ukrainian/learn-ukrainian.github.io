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
        model=kwargs.pop("model", "gemini-3.1-pro-high"),
        task_id=None,
        session_id=None,
        tool_config=kwargs.pop("tool_config", None),
        effort=kwargs.pop("effort", None),
    )


def test_small_prompt_passes_via_stdin_with_placeholder_p_arg(tmp_path):
    """Gemini CLI 0.40.1 yargs bug (#1730): prompts containing `-p` substrings
    cause "Not enough arguments following: p" when passed inline. Workaround
    is to put the prompt on stdin, with a single-space placeholder via -p."""
    prompt = "x" * 200
    plan = _build(prompt, tmp_path)

    assert "-p" in plan.cmd
    # Placeholder, not the prompt — prompt goes via stdin.
    assert plan.cmd[plan.cmd.index("-p") + 1] == " "
    assert plan.stdin_payload == prompt
    assert "--approval-mode=yolo" in plan.cmd
    assert "--skip-trust" in plan.cmd


def test_large_prompt_also_passes_via_stdin(tmp_path):
    """Same workaround for large prompts — stdin has no length limit
    that's relevant here (well below pipe buffer concerns) and bypasses
    the yargs argv bug uniformly."""
    prompt = "x" * 200_000
    adapter = GeminiAdapter()
    plan = adapter.build_invocation(
        prompt=prompt,
        mode="workspace-write",
        cwd=tmp_path,
        model="gemini-3.1-pro-high",
        task_id=None,
        session_id=None,
        tool_config=None,
    )

    assert plan.cmd[plan.cmd.index("-p") + 1] == " "
    assert plan.stdin_payload == prompt
    # No temp prompt file created; cleanup_invocation is a no-op for stdin.
    adapter.cleanup_invocation(plan)


def test_prompt_with_p_substrings_works_post_yargs_workaround(tmp_path):
    """Regression test for #1730: prompts containing the literal text `-p`
    or `--prompt` (e.g., when an earlier gemini failure stderr lands in
    channel history seen by `ab discuss`) used to fail with
    'Not enough arguments following: p'. Stdin workaround eliminates the
    issue because argv contains no prompt content."""
    prompt = "Use -p/--prompt for non-interactive mode. Say hi."
    plan = _build(prompt, tmp_path)

    assert plan.cmd[plan.cmd.index("-p") + 1] == " "
    assert plan.stdin_payload == prompt


def test_large_prompt_api_fail_fast_does_not_create_temp_file(tmp_path, monkeypatch):
    """API-mode misconfiguration must fail before any temp-file creation.

    NOTE: post-#1730 we no longer write prompt files at all — prompts go
    via stdin. The `learn-ukrainian-gemini-prompt-*` glob is checked here
    only as a defense-in-depth assertion that no stale legacy code path
    creates files under any circumstance.
    """
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
            model="gemini-3.1-pro-high",
            task_id=None,
            session_id=None,
            tool_config=None,
        )

    after = set(temp_dir.glob("learn-ukrainian-gemini-prompt-*"))
    assert after == before


def test_mcp_server_names_present_with_stdin_prompt_workaround(tmp_path):
    plan = _build("hello", tmp_path, tool_config={"mcp_server_names": ["sources"]})

    assert "--allowed-mcp-server-names" in plan.cmd
    assert plan.cmd[plan.cmd.index("--allowed-mcp-server-names") + 1] == "sources"
    # -p still present (placeholder), real prompt on stdin (#1730).
    assert plan.cmd[plan.cmd.index("-p") + 1] == " "
    assert plan.stdin_payload == "hello"


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
