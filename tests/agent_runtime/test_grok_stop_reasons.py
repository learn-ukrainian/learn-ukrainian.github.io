"""Native Grok terminal diagnostics without widening completion or permissions."""

from __future__ import annotations

import json

import pytest

from scripts.agent_runtime.adapters.base import InvocationPlan
from scripts.agent_runtime.adapters.grok_build import GrokBuildAdapter
from scripts.agent_runtime.runner import classify_failover_trigger


def _parse(envelope, *, stderr="", returncode=0, plan=None):
    return GrokBuildAdapter().parse_response(
        stdout=json.dumps(envelope),
        stderr=stderr,
        returncode=returncode,
        output_file=None,
        plan=plan,
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
