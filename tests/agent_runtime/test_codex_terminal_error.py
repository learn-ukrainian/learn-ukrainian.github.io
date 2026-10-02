"""Codex outcome classification from the bound rollout's terminal error (#9532).

Synthetic replay fixtures: a rollout bound to the invocation by its prompt,
optionally carrying tool output and a ``task_complete`` event, plus the stderr
``codex exec`` prints for the same turn.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from scripts.agent_runtime.adapters.base import InvocationPlan
from scripts.agent_runtime.adapters.codex import CodexAdapter, codex_terminal_error
from scripts.agent_runtime.failover import classify_failover_trigger

PROMPT = "review the rate-limit handling in this pull request"

# What ``codex exec`` writes to stderr for a turn whose shell tool ran tests
# that print rate-limit text: banner, echoed prompt, then the codex section
# with the command output echoed verbatim.
TOOL_OUTPUT_LINES = (
    "FAILED tests/test_gh.py::test_secondary - API rate limit exceeded for installation",
    "HTTP 429 secondary rate limit; retry after 60s",
)
POLICY_MESSAGE = "This content was flagged for possible cybersecurity risk. Try rephrasing your request."


def _stderr(*codex_lines: str) -> str:
    return "\n".join(
        [
            "OpenAI Codex v0.159.3",
            "--------",
            "workdir: /tmp/work",
            "model: gpt-6.1-sol",
            "--------",
            "user",
            PROMPT,
            "--------",
            "codex",
            "exec",
            "/bin/bash -lc 'pytest tests/test_gh.py' in /tmp/work",
            " exited 1 in 812ms:",
            *TOOL_OUTPUT_LINES,
            *codex_lines,
        ]
    )


def _task_complete(error: dict[str, Any] | None, message: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"type": "task_complete", "turn_id": "turn-1", "last_agent_message": message}
    if error is not None:
        payload["error"] = error
    return {"type": "event_msg", "payload": payload}


def _tool_output_event(output: str) -> dict[str, Any]:
    return {"type": "response_item", "payload": {"type": "function_call_output", "call_id": "c1", "output": output}}


def _parse(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    events: list[dict[str, Any]],
    stderr: str,
    returncode: int = 1,
    output: str = "",
):
    adapter = CodexAdapter()
    rollout_dir = tmp_path / "sessions"
    rollout_dir.mkdir()
    monkeypatch.setattr(adapter, "_candidate_rollout_dirs", lambda: [rollout_dir])
    adapter._reset_per_invocation_state()
    user = {"type": "event_msg", "payload": {"type": "user_message", "message": PROMPT}}
    lines = [json.dumps(event) for event in [user, *events]]
    (rollout_dir / "rollout-test.jsonl").write_text("\n".join(lines) + "\n")
    output_file = tmp_path / "last-message.txt"
    output_file.write_text(output)
    plan = InvocationPlan(cmd=["codex"], cwd=tmp_path, stdin_payload=PROMPT)
    return adapter.parse_response(
        stdout="", stderr=stderr, returncode=returncode, output_file=output_file, plan=plan
    )


def test_policy_refusal_with_rate_limit_tool_output_is_typed_refusal(tmp_path, monkeypatch):
    error = {"message": POLICY_MESSAGE, "codex_error_info": "cyber_policy"}
    result = _parse(
        tmp_path,
        monkeypatch,
        events=[_tool_output_event("\n".join(TOOL_OUTPUT_LINES)), _task_complete(error)],
        stderr=_stderr(f"ERROR: {POLICY_MESSAGE}"),
    )

    assert result.ok is False
    assert result.rate_limited is False
    assert result.failure_code == "provider_policy_refusal"
    assert result.stderr_excerpt.startswith("provider_policy_refusal (codex_error_info=cyber_policy): ")
    assert POLICY_MESSAGE in result.stderr_excerpt
    assert "rate limit" not in result.stderr_excerpt.lower()


@pytest.mark.parametrize(
    ("codex_error_info", "failure_code", "rate_limited"),
    [
        ("cyber_policy", "provider_policy_refusal", False),
        ("bio_policy", "provider_policy_refusal", False),
        ("misalignment_policy_violation", "provider_policy_refusal", False),
        # A class the CLI adds later that names a policy refusal.
        ("content_policy_violation", "provider_policy_refusal", False),
        ("server_overloaded", "provider_overloaded", False),
        ("unauthorized", "provider_auth", False),
        ("other", "provider_error", False),
        ("context_window_exceeded", "provider_error", False),
        ("usage_limit_exceeded", "rate_limited", True),
        ("rate_limit_exceeded", "rate_limited", True),
        ({"http_connection_failed": {"http_status_code": 429}}, "rate_limited", True),
        ({"http_connection_failed": {"http_status_code": 502}}, "provider_error", False),
    ],
)
def test_terminal_error_class_decides_outcome(tmp_path, monkeypatch, codex_error_info, failure_code, rate_limited):
    error = {"message": "provider said no", "codex_error_info": codex_error_info}
    result = _parse(
        tmp_path,
        monkeypatch,
        events=[_task_complete(error, message="partial answer before the failure")],
        stderr=_stderr("ERROR: provider said no"),
    )

    assert result.ok is False
    assert result.response == ""
    assert result.failure_code == failure_code
    assert result.rate_limited is rate_limited
    assert "provider said no" in result.stderr_excerpt


@pytest.mark.parametrize(("returncode", "output"), [(-9, ""), (0, "partial final text")])
def test_terminal_error_wins_over_exit_status_and_output_file(tmp_path, monkeypatch, returncode, output):
    error = {"message": POLICY_MESSAGE, "codex_error_info": "cyber_policy"}
    result = _parse(
        tmp_path, monkeypatch, events=[_task_complete(error)], stderr=_stderr(), returncode=returncode, output=output
    )

    assert result.ok is False
    assert result.failure_code == "provider_policy_refusal"
    assert result.rate_limited is False


def test_genuine_usage_limit_error_line_without_structured_error_is_rate_limited(tmp_path, monkeypatch):
    result = _parse(
        tmp_path,
        monkeypatch,
        events=[],
        stderr=_stderr("ERROR: You've hit your usage limit. Try again later."),
    )

    assert result.ok is False
    assert result.rate_limited is True


def test_tool_output_alone_never_rate_limits_a_failed_turn(tmp_path, monkeypatch):
    result = _parse(
        tmp_path,
        monkeypatch,
        events=[_tool_output_event("\n".join(TOOL_OUTPUT_LINES))],
        stderr=_stderr(),
    )

    assert result.ok is False
    assert result.rate_limited is False
    assert result.failure_code is None


def test_tool_output_that_looks_like_a_codex_error_line_is_excluded(tmp_path, monkeypatch):
    tool_line = "ERROR: HTTP 429 while fetching the package index"
    result = _parse(
        tmp_path,
        monkeypatch,
        events=[_tool_output_event(f"Collecting requests\n{tool_line}\n")],
        stderr=_stderr(tool_line),
    )

    assert result.ok is False
    assert result.rate_limited is False


def test_successful_turn_is_unaffected_by_tool_output(tmp_path, monkeypatch):
    result = _parse(
        tmp_path,
        monkeypatch,
        events=[_tool_output_event("\n".join(TOOL_OUTPUT_LINES)), _task_complete(None, message="Verdict: APPROVE")],
        stderr=_stderr(),
        returncode=0,
        output="Verdict: APPROVE",
    )

    assert result.ok is True
    assert result.response == "Verdict: APPROVE"
    assert result.rate_limited is False
    assert result.failure_code is None


def test_terminal_error_message_is_scrubbed_and_truncated():
    secret = "sk-proj-" + "A1b2C3d4E5f6G7h8" * 4
    events = [
        _task_complete(
            {"message": f"unexpected status 401 Unauthorized: Incorrect API key provided: {secret} " + "x" * 600,
             "codex_error_info": "other"}
        )
    ]
    error = codex_terminal_error(events)

    assert error is not None
    assert secret not in error.message
    assert len(error.message) <= 300
    assert len(error.excerpt()) <= 500


def test_task_complete_without_error_is_not_a_terminal_error():
    assert codex_terminal_error([_task_complete(None, message="done")]) is None
    assert codex_terminal_error([_task_complete({"message": "", "codex_error_info": None})]) is None
    assert codex_terminal_error([]) is None


def test_failover_does_not_rotate_on_codex_policy_refusal(tmp_path, monkeypatch):
    error = {"message": POLICY_MESSAGE, "codex_error_info": "cyber_policy"}
    stderr = _stderr(f"ERROR: {POLICY_MESSAGE}")
    parse = _parse(tmp_path, monkeypatch, events=[_task_complete(error)], stderr=stderr)

    trigger = classify_failover_trigger(
        parse=parse, returncode=1, kill_reason=None, stdout_text="", stderr_text=stderr
    )

    assert trigger is None
