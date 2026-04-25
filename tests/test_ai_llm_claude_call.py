from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime.result import Result
from ai_llm.claude_call import call_claude_with_fallback


def _result(
    *,
    ok: bool,
    response: str = "",
    stderr_excerpt: str | None = None,
    model: str = "claude-opus-4-7",
) -> Result:
    return Result(
        ok=ok,
        agent="claude",
        model=model,
        mode="read-only",
        response=response,
        stderr_excerpt=stderr_excerpt,
        duration_s=1.0,
        session_id=None,
        rate_limited=False,
        stalled=False,
        returncode=0 if ok else 1,
    )


def test_happy_path_returns_callresult(tmp_path):
    with patch(
        "ai_llm.agent_runtime_call.runner.invoke",
        return_value=_result(ok=True, response="done"),
    ) as invoke:
        result = call_claude_with_fallback(
            "prompt",
            task_name="unit-test",
            cwd=tmp_path,
            logger=lambda _msg: None,
            sleep_fn=lambda _seconds, _reason: None,
        )

    assert result.response_text == "done"
    assert result.error_message is None
    invoke.assert_called_once()


def test_returns_error_on_runner_failure(tmp_path):
    with patch(
        "ai_llm.agent_runtime_call.runner.invoke",
        return_value=_result(ok=False, stderr_excerpt="broken"),
    ):
        result = call_claude_with_fallback(
            "prompt",
            task_name="unit-test",
            cwd=tmp_path,
            max_retries=1,
            logger=lambda _msg: None,
            sleep_fn=lambda _seconds, _reason: None,
        )

    assert result.response_text is None
    assert result.error_message == "broken"


def test_respects_max_retries(tmp_path):
    responses = [
        _result(ok=False, stderr_excerpt="first"),
        _result(ok=False, stderr_excerpt="second"),
        _result(ok=True, response="done"),
    ]

    with patch("ai_llm.agent_runtime_call.runner.invoke", side_effect=responses):
        result = call_claude_with_fallback(
            "prompt",
            task_name="unit-test",
            cwd=tmp_path,
            max_retries=3,
            logger=lambda _msg: None,
            sleep_fn=lambda _seconds, _reason: None,
        )

    assert result.response_text == "done"
    assert [attempt.status for attempt in result.attempts] == [
        "retryable_error",
        "retryable_error",
        "success",
    ]
