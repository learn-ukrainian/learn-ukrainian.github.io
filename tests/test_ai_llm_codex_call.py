from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime.result import Result
from ai_llm.codex_call import call_codex_with_fallback


def _result(
    *,
    ok: bool,
    response: str = "",
    stderr_excerpt: str | None = None,
    model: str = "gpt-6-astra",
) -> Result:
    return Result(
        ok=ok,
        agent="codex",
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
        result = call_codex_with_fallback(
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
        result = call_codex_with_fallback(
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
        result = call_codex_with_fallback(
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


def test_codex_model_ladder_is_gpt6_only():
    from ai_llm.codex_call import CODEX_MODEL_LADDER

    assert CODEX_MODEL_LADDER == ("gpt-6-astra",)


def test_retry_exhaustion_never_falls_back_to_gpt5(tmp_path):
    with patch(
        "ai_llm.agent_runtime_call.runner.invoke", return_value=_result(ok=False, stderr_excerpt="broken")
    ) as invoke:
        result = call_codex_with_fallback(
            "prompt", task_name="test", cwd=tmp_path, max_retries=2, logger=lambda _: None, sleep_fn=lambda *_: None
        )
    assert result.error_message == "broken"
    assert invoke.call_count == 2
    assert {call.kwargs["model"] for call in invoke.call_args_list} == {"gpt-6-astra"}
    assert {call.kwargs["effort"] for call in invoke.call_args_list} == {"low"}


def test_unapproved_preference_never_calls_runner(tmp_path):
    with patch("ai_llm.agent_runtime_call.runner.invoke") as invoke:
        with pytest.raises(ValueError, match="rejected"):
            call_codex_with_fallback("prompt", task_name="test", preferred_model="gpt-5.5", cwd=tmp_path)
    invoke.assert_not_called()
