"""#9539: reply/tool content is never a provider failure signal."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_runtime.adapters.agy import AgyAdapter, _brain_transcript_path
from agent_runtime.adapters.base import InvocationPlan
from agent_runtime.adapters.cursor import CursorAdapter
from agent_runtime.adapters.deepseek import DeepSeekAdapter
from agent_runtime.adapters.gemini import GeminiAdapter
from agent_runtime.adapters.glm import GlmAdapter
from agent_runtime.adapters.grok_build import GrokBuildAdapter
from agent_runtime.adapters.kimi import KimiAdapter
from agent_runtime.failover import classify_failover_trigger
from agent_runtime.result import ParseResult

CONTENT = "Investigated rate limit / 429. HTTP 429: too many requests; RESOURCE_EXHAUSTED."


def _stdout(adapter: str, content: str, *, tool: bool = False) -> str:
    if adapter in {"deepseek", "glm"}:
        part = (
            {"type": "tool", "tool": "read", "state": {"status": "completed", "output": content}}
            if tool
            else {"type": "text", "text": content}
        )
        return "\n".join(
            json.dumps(e)
            for e in [
                {"type": "tool_use" if tool else "text", "sessionID": "ses_test", "part": part},
                {"type": "text", "sessionID": "ses_test", "part": {"type": "text", "text": "Done."}}
                if tool
                else {
                    "type": "step_finish",
                    "sessionID": "ses_test",
                    "part": {"type": "step_finish", "reason": "stop"},
                },
            ]
        )
    if adapter == "kimi":
        events = [{"role": "tool" if tool else "assistant", "content": content}]
        if tool:
            events.append({"role": "assistant", "content": "Done."})
        return "\n".join(map(json.dumps, events))
    if adapter == "grok":
        return json.dumps({"text": content, "stopReason": "end_turn"})
    if adapter == "cursor":
        return json.dumps(
            {
                "type": "assistant",
                "role": "assistant",
                "message": {"role": "assistant", "content": [{"type": "text", "text": content}]},
            }
        )
    return content


def _agy_plan(tmp_path: Path, content: str) -> InvocationPlan:
    conversation = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    app_data = tmp_path / "app"
    transcript = _brain_transcript_path(app_data, conversation)
    transcript.parent.mkdir(parents=True)
    transcript.write_text(
        "\n".join(
            map(
                json.dumps,
                [
                    {"type": "USER_INPUT", "content": "Investigate."},
                    {"type": "PLANNER_RESPONSE", "content": content},
                ],
            )
        )
        + "\n"
    )
    log = tmp_path / "agy.log"
    log.write_text(f"Created conversation {conversation}\n")
    return InvocationPlan(
        cmd=["agy"], cwd=tmp_path, env_overrides={"AGY_RUNTIME_LOG_FILE": str(log), "AGY_APP_DATA_DIR": str(app_data)}
    )


ADAPTERS = {
    "deepseek": DeepSeekAdapter,
    "glm": GlmAdapter,
    "kimi": KimiAdapter,
    "grok": GrokBuildAdapter,
    "agy": AgyAdapter,
    "gemini": GeminiAdapter,
    "cursor": CursorAdapter,
}


@pytest.mark.parametrize("adapter", ADAPTERS)
@pytest.mark.parametrize("returncode", [0, 1])
@pytest.mark.parametrize("tool", [False, True])
def test_reply_and_tool_mentions_never_classify_provider_limit(adapter, returncode, tool, tmp_path):
    result = ADAPTERS[adapter]().parse_response(
        stdout=_stdout(adapter, CONTENT, tool=tool),
        stderr="",
        returncode=returncode,
        output_file=None,
        plan=_agy_plan(tmp_path, CONTENT) if adapter == "agy" else None,
    )
    assert result.rate_limited is False
    assert result.ok is (returncode == 0)
    assert (
        classify_failover_trigger(
            parse=result,
            returncode=returncode,
            kill_reason=None,
            stdout_text=_stdout(adapter, CONTENT, tool=tool),
            stderr_text="",
        )
        is None
    )


@pytest.mark.parametrize("adapter", ADAPTERS)
@pytest.mark.parametrize("returncode", [0, 1])
def test_stderr_tool_json_does_not_classify_limit(adapter, returncode, tmp_path):
    stderr = json.dumps({"type": "tool_result", "output": CONTENT})
    result = ADAPTERS[adapter]().parse_response(
        stdout=_stdout(adapter, "Done."),
        stderr=stderr,
        returncode=returncode,
        output_file=None,
        plan=_agy_plan(tmp_path, "Done.") if adapter == "agy" else None,
    )
    assert result.rate_limited is False
    assert result.ok is (returncode == 0)


@pytest.mark.parametrize("adapter", ADAPTERS)
def test_provider_diagnostic_still_classifies_failed_turn(adapter):
    result = ADAPTERS[adapter]().parse_response(
        stdout="",
        stderr="HTTP 429: Too Many Requests",
        returncode=1,
        output_file=None,
    )
    assert result.ok is False
    assert result.rate_limited is True
    assert result.failure_code == "rate_limited"
    assert result.provider_error_text == "HTTP 429: Too Many Requests"


@pytest.mark.parametrize("adapter", ["deepseek", "glm"])
@pytest.mark.parametrize("returncode", [0, 1])
def test_opencode_provider_error_is_classified_even_with_rc_zero(adapter, returncode):
    stdout = json.dumps(
        {
            "type": "error",
            "sessionID": "ses_test",
            "error": {"name": "APIError", "data": {"message": "Too Many Requests", "statusCode": 429}},
        }
    )
    result = ADAPTERS[adapter]().parse_response(stdout=stdout, stderr="", returncode=returncode, output_file=None)
    assert result.ok is False
    assert result.rate_limited is True
    assert result.failure_code == "rate_limited"


@pytest.mark.parametrize("returncode", [0, 1])
def test_agy_incomplete_reply_mentions_do_not_classify_limit(returncode):
    result = AgyAdapter().parse_response(
        stdout=CONTENT, stderr="Background tasks are still running", returncode=returncode, output_file=None
    )
    assert result.rate_limited is False


@pytest.mark.parametrize("failure_code", [None, "acp_agent_startup", "acp_turn_limit", "github_secondary_rate_limited"])
@pytest.mark.parametrize("returncode", [0, 1])
def test_failover_never_reads_raw_stdout_or_excerpt(failure_code, returncode):
    result = ParseResult(ok=False, response="", stderr_excerpt=CONTENT, failure_code=failure_code)
    assert (
        classify_failover_trigger(
            parse=result, returncode=returncode, kill_reason=None, stdout_text=CONTENT, stderr_text=""
        )
        is None
    )


def test_cursor_gh_shim_does_not_trigger_provider_failover():
    stderr = "agent-gh-shim: github_secondary_rate_limited HTTP 403; retries exhausted after 3 attempts."
    result = CursorAdapter().parse_response(stdout="", stderr=stderr, returncode=1, output_file=None)
    assert result.failure_code == "github_secondary_rate_limited"
    assert result.rate_limited is False
    assert (
        classify_failover_trigger(parse=result, returncode=1, kill_reason=None, stdout_text=CONTENT, stderr_text=stderr)
        is None
    )


@pytest.mark.parametrize("adapter", ADAPTERS)
def test_success_keeps_reply_despite_retry_diagnostic(adapter, tmp_path):
    result = ADAPTERS[adapter]().parse_response(
        stdout=_stdout(adapter, CONTENT),
        stderr="HTTP 429: Too Many Requests",
        returncode=0,
        output_file=None,
        plan=_agy_plan(tmp_path, CONTENT) if adapter == "agy" else None,
    )
    assert result.ok is True
    assert result.rate_limited is False
    assert result.failure_code is None


@pytest.mark.parametrize("failure_code", ["acp_agent_startup", "acp_turn_limit", "github_secondary_rate_limited"])
def test_unclassified_structured_failure_ignores_stderr_payload(failure_code):
    result = ParseResult(ok=False, response="", failure_code=failure_code)
    assert (
        classify_failover_trigger(
            parse=result, returncode=1, kill_reason=None, stdout_text=CONTENT, stderr_text=CONTENT
        )
        is None
    )


@pytest.mark.parametrize(
    "stdout",
    [
        json.dumps(
            {
                "role": "meta",
                "type": "turn.step.retrying",
                "error_message": "HTTP 429: rate limit exceeded",
                "status_code": 429,
            }
        ),
        json.dumps({"role": "tool", "content": json.dumps({"type": "error", "error": {"data": {"statusCode": 429}}})}),
    ],
)
def test_kimi_retry_notice_and_nested_tool_error_are_not_terminal(stdout):
    result = KimiAdapter().parse_response(stdout=stdout, stderr="", returncode=1, output_file=None)
    assert result.rate_limited is False


@pytest.mark.parametrize(
    "message,status,expected",
    [
        ("Too Many Requests", 429, "rate_limited"),
        ("Unauthorized", 401, "provider_auth"),
        ("Unavailable", 503, "provider_overloaded"),
        ("quota discussion containing 429", None, "provider_error"),
        ("connection failed", None, "provider_error"),
        ("HTTP 401: Unauthorized", None, "provider_auth"),
        ("No capacity available", None, "provider_overloaded"),
        ("HTTP 429: Too Many Requests", None, "rate_limited"),
    ],
)
def test_provider_failure_classifier(message, status, expected):
    from agent_runtime.failure_codes import provider_failure_code

    assert provider_failure_code(message, status) == expected


@pytest.mark.parametrize(
    "stdout",
    [
        "",
        "{broken",
        "null",
        "[]",
        json.dumps({"type": "error", "error": None}),
        json.dumps({"type": "error", "error": {"data": {"message": 429}}}),
    ],
)
def test_opencode_unknown_or_missing_errors_stay_unknown(stdout):
    from agent_runtime.failure_codes import opencode_provider_error

    message, code = opencode_provider_error(stdout)
    assert message == ""
    assert code in (None, "provider_error")


def test_opencode_conflicting_provider_errors_stay_unknown():
    from agent_runtime.failure_codes import opencode_provider_error

    stdout = "\n".join(
        json.dumps({"type": "error", "error": {"data": {"message": str(status), "statusCode": status}}})
        for status in (401, 429)
    )
    assert opencode_provider_error(stdout) == ("401\n429", "provider_error")


def test_cursor_tool_json_cannot_forge_gh_shim_failure():
    stderr = json.dumps({"type": "tool_result", "output": "agent-gh-shim: github_secondary_rate_limited HTTP 429"})
    result = CursorAdapter().parse_response(stdout="", stderr=stderr, returncode=1, output_file=None)
    assert result.rate_limited is False
    assert result.failure_code == "provider_error"


@pytest.mark.parametrize("status", [400, 401, 503])
def test_status_outranks_rate_limit_words_in_provider_error(status):
    from agent_runtime.failure_codes import provider_failure_code

    expected = {400: "provider_error", 401: "provider_auth", 503: "provider_overloaded"}[status]
    assert provider_failure_code(f"HTTP {status}: invalid rate limit configuration, value 429") == expected


@pytest.mark.parametrize("returncode", [0, 1])
@pytest.mark.parametrize("session_key", ["sessionId", "session_id"])
def test_grok_structured_error_not_agent_reply(returncode, session_key):
    result = GrokBuildAdapter().parse_response(
        stdout=json.dumps(
            {"type": "error", "error": "HTTP 429: Too Many Requests", "text": CONTENT, session_key: "failed-session"}
        ),
        stderr="",
        returncode=returncode,
        output_file=None,
    )
    assert result.rate_limited is True
    assert result.failure_code == "rate_limited"
    assert result.session_id == "failed-session"
    assert result.ok is False


@pytest.mark.parametrize("adapter", ADAPTERS)
def test_failed_turn_plain_stderr_mentions_are_not_provider_diagnostics(adapter):
    result = ADAPTERS[adapter]().parse_response(
        stdout="", stderr="rate limit regression test returned 429", returncode=1, output_file=None
    )
    assert result.rate_limited is False
    assert (
        classify_failover_trigger(
            parse=result,
            returncode=1,
            kill_reason=None,
            stdout_text="",
            stderr_text="rate limit regression test returned 429",
        )
        is None
    )


def test_provider_rate_limit_error_class_is_authoritative():
    from agent_runtime.failure_codes import provider_failure_code, provider_stderr_error

    text = "RateLimitError: request rejected"
    assert provider_stderr_error(text) == text
    assert provider_failure_code(text) == "rate_limited"


@pytest.mark.parametrize("status", ["SUCCESS", "CANCELED", "unknown"])
def test_agy_conflicting_or_nonprovider_terminal_does_not_classify_limit(status, tmp_path):
    plan = _agy_plan(tmp_path, CONTENT)
    plan.cmd.extend(["--output-format", "stream-json"])
    stdout = json.dumps(
        {
            "event": "result",
            "result": {
                "conversation_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                "status": status,
                "response": CONTENT,
                "error": "HTTP 429: Too Many Requests",
            },
        }
    )
    result = AgyAdapter().parse_response(stdout=stdout, stderr="", returncode=0, output_file=None, plan=plan)
    assert result.ok is False
    assert result.rate_limited is False
