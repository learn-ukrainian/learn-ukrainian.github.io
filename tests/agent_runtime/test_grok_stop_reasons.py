"""Native Grok terminal diagnostics without widening completion or permissions."""

from __future__ import annotations

import json

import pytest

from scripts.agent_runtime.adapters.base import InvocationPlan
from scripts.agent_runtime.adapters.grok_build import GrokBuildAdapter
from scripts.agent_runtime.runner import classify_failover_trigger


def _parse(envelope, *, stderr="", returncode=0, plan=None, call_start_time=None):
    return GrokBuildAdapter().parse_response(
        stdout=json.dumps(envelope),
        stderr=stderr,
        returncode=returncode,
        output_file=None,
        plan=plan,
        call_start_time=call_start_time,
    )


@pytest.mark.parametrize(
    "reason",
    [
        "cancelled",
        "max_tokens",
        "max_turns",
        "refusal",
        "tool_use",
        "error",
        "new_provider_reason",
        "EndTurn",
        "",
        None,
        0,
        [],
        {},
    ],
)
@pytest.mark.parametrize("returncode", [0, 1])
def test_exact_nonterminal_reason_is_recorded(reason, returncode):
    result = _parse({"text": "partial report", "stopReason": reason}, returncode=returncode)
    assert not result.ok and result.response == ""
    assert result.failure_code == "provider_stream_incomplete"
    assert "stopReason=" + json.dumps(reason) in result.stderr_excerpt
    assert len(result.stderr_excerpt) <= 500
    assert (
        classify_failover_trigger(
            parse=result,
            returncode=returncode,
            kill_reason=None,
            stdout_text="",
            stderr_text="",
        )
        is None
    )


@pytest.mark.parametrize("returncode", [0, 1])
def test_missing_and_null_stop_reason_remain_distinct(returncode):
    missing = _parse({"text": "partial"}, returncode=returncode)
    null = _parse({"text": "partial", "stopReason": None}, returncode=returncode)
    assert "missing stopReason" in missing.stderr_excerpt
    assert "stopReason=null" in null.stderr_excerpt


@pytest.mark.parametrize("returncode", [0, 1])
def test_empty_answer_still_names_stop_reason(returncode):
    result = _parse({"stopReason": "cancelled"}, returncode=returncode)
    assert 'stopReason="cancelled"' in result.stderr_excerpt


def test_terminal_detail_precedes_long_partial_answer_and_stderr():
    result = _parse(
        {
            "stopReason": "cancelled",
            "cancellation_category": "permission_cancelled",
            "text": "partial " * 1000,
        },
        stderr="provider detail " * 1000,
    )
    assert 'stopReason="cancelled"' in result.stderr_excerpt
    assert "permission_cancelled" in result.stderr_excerpt
    assert len(result.stderr_excerpt) == 500
    assert "\n" not in result.stderr_excerpt


@pytest.mark.parametrize(
    "path",
    [
        "/private/reviewer/session.log",
        "~/reviewer/session.log",
        "../reviewer/session.log",
        "reports/session.log",
        r"C:\private\session.log",
        r"\\server\share\session.log",
    ],
)
def test_paths_and_secrets_are_redacted_before_bounding(path):
    secret = "sk-" + "abcdefghijklmnopqrstuvwx" * 2
    result = _parse(
        {
            "stopReason": "cancelled",
            "stopDetail": f"permission_cancelled {path} {secret}",
            "text": f"partial {path} {secret}",
        },
        stderr=f"error detail {path} {secret}",
    )
    assert path not in result.stderr_excerpt
    assert secret not in result.stderr_excerpt
    assert "<path>" in result.stderr_excerpt
    assert "[REDACTED_SECRET]" in result.stderr_excerpt
    assert "permission_cancelled" in result.stderr_excerpt


def test_provider_error_retains_classification_and_stop_detail():
    result = _parse(
        {
            "type": "error",
            "stopReason": "cancelled",
            "message": "HTTP 429 rate limit",
            "stopReasonDetail": "provider stopped",
        }
    )
    assert result.failure_code == "rate_limited" and result.rate_limited
    assert 'stopReason="cancelled"' in result.stderr_excerpt
    assert "provider stopped" in result.stderr_excerpt
    assert "HTTP 429" in result.stderr_excerpt


@pytest.mark.parametrize(
    "envelope,reason",
    [
        ({"stopReason": "max_tokens", "stopDetails": "output budget exhausted"}, 'stopReason="max_tokens"'),
        ({}, "missing stopReason"),
    ],
)
def test_structured_output_failure_keeps_stop_diagnostics(tmp_path, envelope, reason):
    plan = InvocationPlan(cmd=["grok"], cwd=tmp_path, metadata={"output_schema": {"type": "object"}})
    result = _parse({"structuredOutput": {}, **envelope}, plan=plan)
    assert not result.ok and result.response == ""
    assert result.failure_code == "structured_output_invalid"
    assert reason in result.stderr_excerpt
    if "stopDetails" in envelope:
        assert envelope["stopDetails"] in result.stderr_excerpt


@pytest.mark.parametrize("structured", [False, True])
def test_end_turn_still_completes(tmp_path, structured):
    plan = InvocationPlan(
        cmd=["grok"],
        cwd=tmp_path,
        metadata={"output_schema": {"type": "object"}} if structured else {},
    )
    result = _parse({"stopReason": "end_turn", "text": "final report", "structuredOutput": {}}, plan=plan)
    assert result.ok and result.stderr_excerpt is None


def test_stop_detail_reaches_task_diagnostic_file(tmp_path, monkeypatch):
    from scripts import delegate

    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path))
    task = "grok-stop-test"
    record = tmp_path / f"{task}.json"
    result = _parse(
        {
            "stopReason": "cancelled",
            "cancellationCategory": "permission_cancelled",
            "text": "partial report",
        }
    )
    record.write_text(json.dumps({"stderr_excerpt": result.stderr_excerpt}), encoding="utf-8")
    delegate._worker_last_error(
        task,
        stderr_excerpt=result.stderr_excerpt,
        failure_cause=None,
        final_status="failed",
        returncode=0,
        runtime_failure_code=result.failure_code,
        worker_exception=None,
    )
    entry = json.loads((tmp_path / f"{task}.diag").read_text())
    for diagnostic in (json.loads(record.read_text())["stderr_excerpt"], entry["diagnostic"]):
        assert 'stopReason="cancelled"' in diagnostic
        assert "permission_cancelled" in diagnostic


@pytest.mark.parametrize("structured", [False, True])
@pytest.mark.parametrize("key,category", [
    ("cancellation_category", "permission_cancelled"),
    ("cancellationCategory", "PermissionCancelled"),
])
@pytest.mark.parametrize("returncode", [0, 1])
def test_permission_cancelled_is_distinct_and_does_not_fail_over(tmp_path, structured, key, category, returncode):
    from scripts.agent_runtime.failure_codes import RUNTIME_FAILURE_CODES
    from scripts.agent_runtime.runner import _privacy_safe_failure_code

    plan = InvocationPlan(
        cmd=["grok"], cwd=tmp_path,
        metadata={"output_schema": {"type": "object"}} if structured else {},
    )
    result = _parse(
        {"stopReason": "cancelled", key: category, "text": "HTTP 429 narration", "structuredOutput": {}},
        plan=plan, returncode=returncode,
    )
    assert not result.ok and result.response == "" and not result.rate_limited
    assert result.failure_code == "permission_cancelled"
    assert result.failure_code in RUNTIME_FAILURE_CODES
    assert _privacy_safe_failure_code(
        outcome="failed", rate_limited=False, stalled=False, returncode=returncode,
        explicit_code=result.failure_code,
    ) == "permission_cancelled"
    assert classify_failover_trigger(
        parse=result, returncode=returncode, kill_reason=None,
        stdout_text="HTTP 429 narration", stderr_text="HTTP 429 narration",
    ) is None


def _session_plan(tmp_path, events, *, sid="11111111-1111-4111-8111-111111111111", snapshot=()):
    from scripts.agent_runtime.adapters.grok_build import grok_session_dir

    home = tmp_path / "grok-home"
    plan = InvocationPlan(
        cmd=["grok"], cwd=tmp_path, env_overrides={"GROK_HOME": str(home)},
        metadata={"liveness_session_dir_snapshot": list(snapshot)},
    )
    trace = grok_session_dir(home, tmp_path, sid) / "events.jsonl"
    trace.parent.mkdir(parents=True)
    trace.write_text(events, encoding="utf-8")
    return plan, sid


@pytest.mark.parametrize("structured", [False, True])
def test_permission_category_comes_from_exact_session_last_terminal(tmp_path, structured):
    event = {"type": "turn_ended", "outcome": "cancelled", "cancellation_category": "permission_cancelled",
             "ts": "2026-10-07T18:00:00Z"}
    plan, sid = _session_plan(tmp_path, json.dumps(event))
    if structured:
        plan.metadata["output_schema"] = {"type": "object"}
    result = _parse({"stopReason": "cancelled", "sessionId": sid, "text": "partial"}, plan=plan,
                    call_start_time=1791395999)
    assert result.failure_code == "permission_cancelled"
    assert "permission_cancelled" in result.stderr_excerpt
    assert str(tmp_path) not in result.stderr_excerpt


@pytest.mark.parametrize("trace", [
    "broken json", "[]", "", "\n", "{",
    json.dumps({"type": "tool_output", "cancellation_category": "permission_cancelled"}),
    json.dumps({"type": "turn_ended", "outcome": "completed", "cancellation_category": "permission_cancelled"}),
    json.dumps({"type": "turn_ended", "outcome": "cancelled", "cancellation_category": "user_cancelled"}),
    json.dumps({"type": "turn_ended", "outcome": "cancelled", "cancellation_category": "permission_cancelled"})
    + "\n" + json.dumps({"type": "turn_ended", "outcome": "completed"}),
])
def test_untrusted_or_superseded_trace_does_not_classify_permission(tmp_path, trace):
    plan, sid = _session_plan(tmp_path, trace)
    result = _parse({"stopReason": "cancelled", "sessionId": sid, "text": "permission_cancelled"}, plan=plan)
    assert result.failure_code == "provider_stream_incomplete"


@pytest.mark.parametrize("case", ["missing", "preexisting", "peer", "stale", "bad_timestamp", "naive_timestamp", "traversal"])
def test_permission_trace_requires_current_bound_session(tmp_path, case):
    from scripts.agent_runtime.adapters.grok_build import grok_session_dir

    event = {"type": "turn_ended", "outcome": "cancelled", "cancellation_category": "permission_cancelled",
             "ts": "2026-10-07T18:00:00Z"}
    sid = "11111111-1111-4111-8111-111111111111"
    if case == "bad_timestamp":
        event["ts"] = "bad"
    if case == "naive_timestamp":
        event["ts"] = "2026-10-07T18:00:00"
    plan, sid = _session_plan(tmp_path, json.dumps(event), snapshot=[sid] if case == "preexisting" else [])
    if case == "missing":
        grok_session_dir(tmp_path / "grok-home", tmp_path, sid).joinpath("events.jsonl").unlink()
    if case == "peer":
        sid = "22222222-2222-4222-8222-222222222222"
    if case == "traversal":
        sid = "../" + sid
    result = _parse({"stopReason": "cancelled", "sessionId": sid}, plan=plan,
                    call_start_time=1791396001 if case == "stale" else 1791395999)
    assert result.failure_code == "provider_stream_incomplete"


@pytest.mark.parametrize("reason", ["end_turn", "max_tokens"])
def test_permission_category_does_not_override_other_terminal_reason(reason):
    result = _parse({"stopReason": reason, "cancellation_category": "permission_cancelled", "text": "report"})
    assert result.failure_code is None if reason == "end_turn" else result.failure_code == "provider_stream_incomplete"


def _ndjson(events: list[dict]) -> str:
    return "".join(json.dumps(event) + "\n" for event in events)


def _assistant_frame(text: str, *, session_id: str = "session-placeholder") -> dict:
    return {
        "type": "assistant",
        "message": {
            "id": "msg_1",
            "role": "assistant",
            "content": [{"type": "text", "text": text}],
        },
        "session_id": session_id,
    }


def _error_result(
    *,
    stop_reason: str,
    subtype: str,
    errors: list[str],
    session_id: str = "session-placeholder",
) -> dict:
    return {
        "type": "result",
        "subtype": subtype,
        "is_error": True,
        "stop_reason": stop_reason,
        "errors": errors,
        "session_id": session_id,
        "modelUsage": {"grok-4.7-build": {"modelCalls": 1}},
    }


def _parse_messages(events: list[dict], **kwargs):
    return GrokBuildAdapter().parse_response(
        stdout=_ndjson(events),
        stderr=kwargs.pop("stderr", ""),
        returncode=kwargs.pop("returncode", 0),
        output_file=None,
        **kwargs,
    )


@pytest.mark.parametrize("returncode", [0, 1])
@pytest.mark.parametrize(
    "case,stop_reason,subtype,detail",
    [
        ("cancelled", "cancelled", "error", "turn cancelled"),
        ("max_turns", "max_turns", "error_max_turns", "Reached the maximum number of turns"),
        # Grok 1.0.46 --max-turns 1: stop_reason stays "cancelled"; the
        # max-turns fact is subtype error_max_turns plus errors[0].
        ("max_turns_wire", "cancelled", "error_max_turns", "Reached the maximum number of turns"),
    ],
)
def test_messages_stream_stop_reason_matches_old_format(case, stop_reason, subtype, detail, returncode):
    partial = "partial report"
    new = _parse_messages(
        [
            _assistant_frame(partial),
            _error_result(stop_reason=stop_reason, subtype=subtype, errors=[detail]),
        ],
        returncode=returncode,
    )
    old = _parse({"text": partial, "stopReason": stop_reason}, returncode=returncode)
    assert new.failure_code == old.failure_code == "provider_stream_incomplete", case
    assert new.response == "" and new.rate_limited is False
    assert f'stopReason="{stop_reason}"' in new.stderr_excerpt
    assert detail in new.stderr_excerpt
    assert partial in new.stderr_excerpt
    assert new.substitution["actual_model"] == "grok-4.7-build"
    assert (
        classify_failover_trigger(
            parse=new,
            returncode=returncode,
            kill_reason=None,
            stdout_text="",
            stderr_text="",
        )
        is None
    )


def test_real_max_turns_stderr_stays_incomplete():
    """Grok 1.0.46 exits 1 with 'Error: max turns reached' and an error result."""
    partial = "I'll read the note first."
    result = _parse_messages(
        [
            _assistant_frame(partial),
            _error_result(
                stop_reason="cancelled",
                subtype="error_max_turns",
                errors=["Reached the maximum number of turns"],
            ),
        ],
        stderr="Error: max turns reached",
        returncode=1,
    )
    assert result.failure_code == "provider_stream_incomplete"
    assert result.response == ""
    assert 'stopReason="cancelled"' in result.stderr_excerpt
    assert "Reached the maximum number of turns" in result.stderr_excerpt
    assert partial in result.stderr_excerpt


@pytest.mark.parametrize("returncode", [0, 1])
def test_messages_stream_permission_cancelled_matches_old_format(tmp_path, returncode):
    event = {
        "type": "turn_ended",
        "outcome": "cancelled",
        "cancellation_category": "permission_cancelled",
        "ts": "2026-10-07T18:00:00Z",
    }
    plan, sid = _session_plan(tmp_path, json.dumps(event))
    partial = "partial report"
    new = _parse_messages(
        [
            _assistant_frame(partial, session_id=sid),
            _error_result(
                stop_reason="cancelled",
                subtype="error",
                errors=["permission cancelled"],
                session_id=sid,
            ),
        ],
        plan=plan,
        call_start_time=1791395999,
        returncode=returncode,
    )
    old = _parse(
        {"stopReason": "cancelled", "sessionId": sid, "text": partial},
        plan=plan,
        call_start_time=1791395999,
        returncode=returncode,
    )
    assert new.failure_code == old.failure_code == "permission_cancelled"
    assert new.response == "" and new.rate_limited is False
    assert "permission_cancelled" in new.stderr_excerpt
    assert 'stopReason="cancelled"' in new.stderr_excerpt
    assert str(tmp_path) not in new.stderr_excerpt
    assert (
        classify_failover_trigger(
            parse=new,
            returncode=returncode,
            kill_reason=None,
            stdout_text="HTTP 429 narration",
            stderr_text="HTTP 429 narration",
        )
        is None
    )


def test_messages_stream_type_error_is_still_a_provider_failure():
    result = _parse_messages(
        [
            _assistant_frame("partial"),
            {"type": "error", "message": "Error code: 429"},
        ]
    )
    assert not result.ok and result.response == ""
    assert result.failure_code == "rate_limited"
    assert result.provider_error_text == "Error code: 429"


def test_result_error_without_stop_reason_is_not_a_provider_failure():
    result = _parse_messages(
        [
            _assistant_frame("partial report"),
            {
                "type": "result",
                "subtype": "error",
                "is_error": True,
                "errors": ["boom"],
                "session_id": "session-placeholder",
            },
        ]
    )
    assert result.failure_code == "provider_stream_incomplete"
    assert "missing stopReason" in result.stderr_excerpt
    assert "boom" in result.stderr_excerpt
