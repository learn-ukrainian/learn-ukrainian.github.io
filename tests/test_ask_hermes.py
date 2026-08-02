"""Tests for the ask-hermes bridge runtime path."""

from unittest.mock import patch

import pytest

from scripts.agent_runtime.errors import AgentUnavailableError
from scripts.agent_runtime.result import Result
from scripts.ai_agent_bridge._hermes import HERMES_DEFAULT_MODEL, _invoke_hermes


def _result(*, ok: bool = True, response: str = "response body") -> Result:
    return Result(
        ok=ok,
        agent="deepseek",
        model="deepseek-v4-flash",
        mode="read-only",
        response=response,
        stderr_excerpt=None,
        duration_s=0.1,
        session_id=None,
        rate_limited=False,
        stalled=False,
        returncode=0 if ok else 1,
    )


def test_hermes_default_model_is_deepseek_flash():
    """Default changed from qwen/qwen3.6-plus (PR #4473): qwen is banned by
    standing user spend order; deepseek-flash is the Hermes tool-heavy default."""
    assert HERMES_DEFAULT_MODEL == "deepseek-v4-flash"


def test_invoke_hermes_uses_shared_runtime():
    with patch("scripts.agent_runtime.runner.invoke", return_value=_result()) as invoke_mock:
        assert _invoke_hermes("hello", "deepseek-v4-flash", task_id="task-1") == "response body"
    args, kwargs = invoke_mock.call_args
    assert args == ("deepseek", "hello")
    assert kwargs["model"] == "deepseek-v4-flash"
    assert kwargs["task_id"] == "task-1"
    assert kwargs["entrypoint"] == "bridge"
    assert kwargs["mode"] == "read-only"
    assert kwargs["tool_config"]["repo_read_root"]


def test_invoke_hermes_attaches_data_file(tmp_path):
    data_file = tmp_path / "context.md"
    data_file.write_text("# Context\nSome content.")
    with patch("scripts.agent_runtime.runner.invoke", return_value=_result(response="ok")) as invoke_mock:
        _invoke_hermes("review this", "deepseek-v4-flash", data=str(data_file))
    prompt = invoke_mock.call_args.args[1]
    assert "Some content." in prompt
    assert "review this" in prompt


def test_invoke_hermes_raises_when_binary_missing():
    with patch(
        "scripts.agent_runtime.runner.invoke",
        side_effect=AgentUnavailableError("missing"),
    ):
        with pytest.raises(SystemExit, match="AgentUnavailableError"):
            _invoke_hermes("hello", "deepseek-v4-flash")


def test_invoke_hermes_raises_on_nonzero_exit():
    with patch("scripts.agent_runtime.runner.invoke", return_value=_result(ok=False, response="")):
        with pytest.raises(SystemExit, match="no usable response"):
            _invoke_hermes("hello", "deepseek-v4-flash")
