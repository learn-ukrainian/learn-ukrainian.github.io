"""Recorded diagnostics travel through the real adapter before retry (#10206).

Sanitized excerpts read from batch_state/tasks on 2026-10-09:
* impl-9384-cov-yaml: terminal API error
* codex-w0-two-pair-modern-agy: terminal interrupted stream
* gemini-10105-practical-task-semantics: init-only/missing result
* e3c-census-b6a.20261003T204239629414Z.archived: eligibility error
* uk9623-v2-smoke-flash-none-r1-review-00: load-code-assist eligibility error
Only diagnostic text is retained; no prompts, private paths or source output.
"""

import json
from dataclasses import replace
from unittest.mock import Mock

import pytest

from scripts.agent_runtime import runner
from scripts.agent_runtime.adapters import agy
from scripts.agent_runtime.adapters.agy import AgyAdapter
from scripts.agent_runtime.adapters.base import InvocationPlan
from tests.agent_runtime.adapters.test_agy_adapter import (
    _FINISHED_CONVERSATION_ID,
    _TASK_2,
    _background_plan,
    _canceled,
    _event,
    _prompt,
    _reply,
    _start,
    _stream_stdout,
)

API_503 = "API error (attempt 1): UNAVAILABLE (code 503): The service is currently unavailable."
INTERRUPTED = "The stream was interrupted. Please continue the task you were working on."
ELIGIBILITY_503 = "Eligibility check failed: UNAVAILABLE (code 503): The service is currently unavailable."
LOAD_503 = (
    "Eligibility check failed: failed to get load code assist response: UNAVAILABLE (code 503): The service is currently unavailable."
)
INIT = json.dumps({"event": "init", "conversation_id": _FINISHED_CONVERSATION_ID})


def _raw(error=API_503, *, stderr=False, events=None, returncode=1):
    stdout = (
        INIT
        if error is None or stderr
        else _stream_stdout(
            {
                "conversation_id": _FINISHED_CONVERSATION_ID,
                "status": "ERROR",
                "error": error,
            }
        )
    )
    return stdout, (error or "") if stderr else "", returncode, events


def _success():
    return (
        _stream_stdout(
            {
                "conversation_id": _FINISHED_CONVERSATION_ID,
                "status": "SUCCESS",
                "response": "Complete reply.",
            }
        ),
        "",
        0,
        [_prompt(), _reply("Complete reply.")],
    )


def _cancel():
    return (
        _stream_stdout(
            {
                "conversation_id": _FINISHED_CONVERSATION_ID,
                "status": "SUCCESS",
                "response": "Complete reply.",
            }
        ),
        "",
        0,
        [_prompt(), _start(_TASK_2), _canceled(_TASK_2), _reply("Complete reply.")],
    )


def _run(tmp_path, monkeypatch, raw_attempts, *, mode="read-only", exited=True, budget=None, tool_config=None):
    adapter = AgyAdapter()
    plans = []
    parsed = []
    for index, (_stdout, _stderr, _returncode, events) in enumerate(raw_attempts):
        directory = tmp_path / str(index)
        directory.mkdir()
        plan = (
            _background_plan(directory, _FINISHED_CONVERSATION_ID, events)
            if events is not None
            else InvocationPlan(
                cmd=["agy"],
                cwd=directory,
            )
        )
        plan = replace(plan, cmd=["agy", "--output-format", "stream-json"])
        plans.append(plan)

    def execute(**kwargs):
        index = len(parsed)
        stdout, stderr, returncode, _ = raw_attempts[index]
        result = adapter.parse_response(
            stdout=stdout,
            stderr=stderr,
            returncode=returncode,
            output_file=None,
            plan=kwargs["plan"],
        )
        # This is adapter evidence, never a hand-built failure code or diagnostic.
        parsed.append(result)
        return runner._ExecutionOutcome(
            parse=result,
            duration_s=0.01,
            returncode=returncode,
            kill_reason=None,
            stdout_text=stdout,
            stderr_text=stderr,
            liveness_paths=(),
            process_group_exited=exited,
        )

    once = Mock(side_effect=execute)
    build = Mock(return_value=plans[-1])
    monkeypatch.setattr(runner, "_execute_invocation_once", once)
    monkeypatch.setattr(adapter, "build_invocation", build)
    monkeypatch.setattr(runner, "_agy_git_state", lambda _: (b"head", b"clean"))
    outcome = runner._execute_invocation_plan(
        agent_name="agy",
        adapter=adapter,
        plan=plans[0],
        prompt="fixture",
        mode=mode,
        cwd=tmp_path,
        model="gemini-3.8-flash-high",
        task_id="fixture",
        session_id=None,
        entrypoint="delegate",
        hard_timeout=30,
        stall_timeout=10,
        agy_budget=budget,
        tool_config=tool_config,
    )
    return outcome.parse, once.call_count, parsed, build


@pytest.mark.parametrize("error", [API_503, INTERRUPTED, LOAD_503, None])
@pytest.mark.parametrize("stderr", [False, True])
def test_recorded_faults_reach_retry_and_exhaustion(tmp_path, monkeypatch, error, stderr):
    raw = _raw(error, stderr=stderr)
    result, launches, parsed, _ = _run(tmp_path, monkeypatch, [raw, raw])
    assert launches == 2
    assert all(p.agy_provider_fault.transient for p in parsed)
    fields = result.agy_telemetry.task_fields()
    assert fields["agy_retry_disposition"] == "exhausted"
    assert fields["agy_reroute_required"] is True
    assert fields["agy_reroute_reason"] == "agy_retry_exhausted"
    assert fields["agy_replacement_task_id"] == "fixture-agy-reroute-1"


@pytest.mark.parametrize("returncode", [0, 1])
def test_init_only_missing_terminal_result_retries_without_write_evidence(tmp_path, monkeypatch, returncode):
    result, launches, parsed, _ = _run(tmp_path, monkeypatch, [_raw(None, returncode=returncode), _success()])
    assert launches == 2 and result.ok
    assert parsed[0].agy_provider_fault.kind == "missing_terminal_result"
    assert result.agy_telemetry.accepted_attempt == 2


@pytest.mark.parametrize("status,code", [("PERMISSION_DENIED", 403), ("INVALID_ARGUMENT", 400)])
@pytest.mark.parametrize("stderr", [False, True])
def test_permanent_status_quoting_503_never_retries(tmp_path, monkeypatch, status, code, stderr):
    error = f'Eligibility check failed: failed to get load code assist response: {status} (code {code}): quotes "UNAVAILABLE (code 503)".'
    result, launches, parsed, _ = _run(tmp_path, monkeypatch, [_raw(error, stderr=stderr)])
    assert launches == 1
    assert not parsed[0].agy_provider_fault.transient
    assert parsed[0].agy_provider_fault.status == status
    assert result.agy_telemetry.retry_disposition == "no_retry"


def test_real_503_quoting_cancellation_is_transient(tmp_path, monkeypatch):
    raw = _raw(API_503 + ' Quoted "agy_background_task_canceled".')
    result, launches, parsed, _ = _run(tmp_path, monkeypatch, [raw, _success()])
    assert launches == 2 and result.ok
    assert parsed[0].agy_attempt.completion_reason != agy.AGY_BACKGROUND_TASK_CANCELED


@pytest.mark.parametrize("mode", ["read-only", "workspace-write", "danger"])
@pytest.mark.parametrize("exited", [False, None])
def test_process_exit_must_be_confirmed_before_transient_replay(tmp_path, monkeypatch, mode, exited):
    result, launches, _, build = _run(tmp_path, monkeypatch, [_raw(events=[_prompt()])], mode=mode, exited=exited)
    assert launches == 1
    build.assert_not_called()
    assert result.agy_telemetry.reroute_reason == "unsafe_replay"


@pytest.mark.parametrize("mode", ["workspace-write", "danger"])
@pytest.mark.parametrize("events", [None, ["unreadable"]])
def test_write_replay_requires_affirmative_complete_evidence(tmp_path, monkeypatch, mode, events):
    result, launches, parsed, _ = _run(tmp_path, monkeypatch, [_raw(events=events)], mode=mode)
    assert launches == 1
    assert parsed[0].agy_attempt.evidence_complete is False
    assert result.agy_telemetry.reroute_reason == "unsafe_replay"


def _tool(name, args=None, status="DONE"):
    return [
        _prompt(),
        _event(
            "PLANNER_RESPONSE",
            "",
            source="MODEL",
            tool_calls=[
                {
                    "name": name,
                    "args": args or {},
                }
            ],
        ),
        _event("GENERIC", "Tool completed.", status=status),
    ]


@pytest.mark.parametrize(
    "name,args",
    [
        ("run_command", {"CommandLine": '"fixture-command"'}),
        ("write_to_file", {}),
        ("replace_file_content", {}),
        ("multi_replace_file_content", {}),
        ("manage_task", {"Action": '"create"'}),
        ("future_tool", {}),
        ("call_mcp_tool", {"ServerName": '"filesystem"', "ToolName": '"write_file"'}),
        ("call_mcp_tool", {"ServerName": '"sources"', "ToolName": '"future_unknown"'}),
        ("call_mcp_tool", {"ServerName": '"sources"', "ToolName": '"query_ulif"'}),
        ("mcp_sources_query_ulif", {}),
        ("call_mcp_tool", {}),
        ("mcp_sources_future_unknown", {}),
        ("mcp__sources__future_unknown", {}),
        ("mcp_sources_mcp__sources__verify_words", {}),
    ],
)
@pytest.mark.parametrize("status", ["DONE", "RUNNING"])
def test_side_effecting_and_unknown_tools_block_write_replay(tmp_path, monkeypatch, name, args, status):
    result, launches, parsed, _ = _run(
        tmp_path, monkeypatch, [_raw(events=_tool(name, args, status))], mode="workspace-write"
    )
    assert launches == 1
    assert parsed[0].agy_attempt.evidence_complete is True
    assert parsed[0].agy_attempt.side_effect_tool_count > 0
    assert result.agy_telemetry.reroute_reason == "unsafe_replay"


@pytest.mark.parametrize(
    "events",
    [
        [_prompt()],
        _tool("view_file"),
        _tool("call_mcp_tool", {"ServerName": '"sources"', "ToolName": '"verify_words"'}),
        _tool("mcp_sources_verify_words"),
        _tool("mcp__sources__verify_words"),
    ],
)
def test_audited_read_only_tool_evidence_allows_write_retry(tmp_path, monkeypatch, events):
    result, launches, parsed, _ = _run(tmp_path, monkeypatch, [_raw(events=events), _success()], mode="workspace-write")
    assert launches == 2 and result.ok
    assert parsed[0].agy_attempt.side_effect_tool_count == 0
    assert parsed[0].agy_attempt.executed_command_count == 0
    assert result.agy_telemetry.retry_reason == "transient_provider_fault"


@pytest.mark.parametrize(
    "events",
    [
        [_prompt(), _event("GENERIC", "Unknown result")],
        [_prompt(), _event("MCP_TOOL", "Unknown MCP result")],
        [_prompt(), _event("PLANNER_RESPONSE", "", tool_calls=[{"name": "write_to_file"}])],
        [_prompt(), _event("PLANNER_RESPONSE", "", source="MODEL", tool_calls=[{"name": "write_to_file"}])],
    ],
)
def test_orphan_result_and_unresolved_write_intent_are_unsafe(tmp_path, monkeypatch, events):
    result, launches, parsed, _ = _run(tmp_path, monkeypatch, [_raw(events=events)], mode="workspace-write")
    assert launches == 1
    assert parsed[0].agy_attempt.side_effect_tool_count > 0
    assert result.agy_telemetry.reroute_reason == "unsafe_replay"


@pytest.mark.parametrize(
    "first,second",
    [
        (_raw(), _cancel()),
        (_cancel(), _raw()),
        (_raw(ELIGIBILITY_503), _raw()),
        (_raw(), _raw(ELIGIBILITY_503)),
    ],
)
def test_cancellation_eligibility_and_faults_share_two_launches(tmp_path, monkeypatch, first, second):
    result, launches, parsed, _ = _run(tmp_path, monkeypatch, [first, second])
    assert any(p.agy_provider_fault is not None and p.agy_provider_fault.transient for p in parsed)
    assert launches == 2
    assert result.agy_telemetry.reroute_reason == "agy_retry_exhausted"


@pytest.mark.parametrize(
    "error",
    ["API error (attempt 1): INTERNAL (code 500): service error.", "ordinary output quoting UNAVAILABLE (code 503)"],
)
def test_other_errors_are_not_transient(tmp_path, monkeypatch, error):
    result, launches, _, _ = _run(tmp_path, monkeypatch, [_raw(error)])
    assert launches == 1
    assert result.agy_telemetry.retry_disposition == "no_retry"
    assert result.agy_provider_fault is None or not result.agy_provider_fault.transient


def test_classifier_retains_header_not_quoted_status():
    fault = agy.parse_agy_provider_fault(
        "agy_stream_result_error: API error (attempt 1): INVALID_ARGUMENT (code 400): UNAVAILABLE (code 503)"
    )
    assert (fault.kind, fault.status, fault.code, fault.transient) == ("api_error", "INVALID_ARGUMENT", 400, False)


@pytest.mark.parametrize("error", [API_503, ELIGIBILITY_503])
def test_exact_eligibility_and_api_fault_require_exit_confirmation(tmp_path, monkeypatch, error):
    result, launches, _, _ = _run(tmp_path, monkeypatch, [_raw(error)], exited=False)
    assert launches == 1
    assert result.agy_telemetry.reroute_reason == "unsafe_replay"


def test_transient_fault_with_unconfirmed_background_task_reroutes(tmp_path, monkeypatch):
    raw = _raw(events=[_prompt(), _start(_TASK_2), _reply("Complete reply.")], returncode=0)
    result, launches, _, _ = _run(tmp_path, monkeypatch, [raw])
    assert launches == 1
    assert result.agy_provider_fault.transient
    assert result.agy_telemetry.reroute_reason == "unsafe_replay"
