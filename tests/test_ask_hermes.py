"""Hermes bridge and Cursor adapter plan tests."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.agent_runtime.errors import AgentUnavailableError
from scripts.agent_runtime.result import Result
from scripts.ai_agent_bridge._hermes import _invoke_hermes


def test_cursor_adapter_plan_is_headless_and_records_the_requested_model(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.agent_runtime.adapters.cursor import CursorAdapter

    monkeypatch.setattr("shutil.which", lambda _name: "/fake/cursor-agent")
    for mode in ("read-only", "workspace-write", "danger"):
        plan = CursorAdapter().build_invocation(
            prompt="fixture",
            mode=mode,
            cwd=tmp_path,
            model="grok-4.7",
            task_id="cursor-headless-fixture",
            session_id=None,
            tool_config={},
        )
        assert "-p" in plan.cmd
        assert plan.metadata["requested_model"] == "grok-4.7-high"


def _hermes_result(*, ok: bool = True, response: str = "response body") -> Result:
    return Result(
        ok=ok,
        agent="deepseek",
        model="deepseek-v4.1-flash",
        mode="read-only",
        response=response,
        stderr_excerpt=None,
        duration_s=0.1,
        session_id=None,
        rate_limited=False,
        stalled=False,
        returncode=0 if ok else 1,
    )


def test_invoke_hermes_raises_when_binary_missing():
    with patch(
        "scripts.agent_runtime.runner.invoke",
        side_effect=AgentUnavailableError("missing"),
    ):
        with pytest.raises(SystemExit, match="AgentUnavailableError"):
            _invoke_hermes("hello", "deepseek-v4.1-flash")


def test_invoke_hermes_raises_on_nonzero_exit():
    with patch(
        "scripts.agent_runtime.runner.invoke",
        return_value=_hermes_result(ok=False, response=""),
    ):
        with pytest.raises(SystemExit, match="no usable response"):
            _invoke_hermes("hello", "deepseek-v4.1-flash")
