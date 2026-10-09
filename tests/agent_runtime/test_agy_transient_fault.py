"""Transient AGY provider faults retry once or end in a typed reroute (#10206)."""

from dataclasses import replace

import pytest

from scripts.agent_runtime import runner
from scripts.agent_runtime.adapters.agy import TRANSIENT_PROVIDER_FAULT, classify_agy_transient_provider_fault
from scripts.agent_runtime.result import AgyAttempt
from tests.agent_runtime.test_agy_retry import _execute, _outcome

API_503 = (
    "agy_stream_result_error: API error (attempt 1): UNAVAILABLE (code 503): "
    "The service is currently unavailable."
)
INTERRUPTED = (
    "agy_stream_result_error: The stream was interrupted. Please continue the task you were working on."
)
MISSING_TERMINAL = "agy_stream_output_invalid: missing terminal result"
LOAD_CODE_ASSIST_503 = (
    "agy_stream_result_error: Eligibility check failed: failed to get load code assist response: "
    "UNAVAILABLE (code 503): The service is currently unavailable."
)
NON_TRANSIENT = "agy_stream_result_error: INVALID_ARGUMENT (code 400): request failed"
MIXED_UNRELATED_503 = (
    "API error (attempt 1): UNAVAILABLE (code 503)\nEligibility check failed: PERMISSION_DENIED (code 403)"
)

RECORDED = (
    pytest.param(API_503, id="api-503"),
    pytest.param(INTERRUPTED, id="stream-interrupted"),
    pytest.param(MISSING_TERMINAL, id="missing-terminal-result"),
    pytest.param(LOAD_CODE_ASSIST_503, id="load-code-assist-503"),
)


def _fault(excerpt: str, *, ok: bool = False):
    base = _outcome(pre_model=False, stderr="", ok=ok)
    return replace(
        base,
        parse=replace(
            base.parse,
            ok=ok,
            response="Complete reply." if ok else "",
            failure_code=None if ok else "provider_error",
            provider_error_text="",
            stderr_excerpt=None if ok else excerpt,
            agy_pre_model_failure=False,
            agy_attempt=AgyAttempt(
                completion_reason="completed" if ok else "provider_error",
                failure_code=None if ok else "provider_error",
            ),
        ),
    )


@pytest.mark.parametrize("excerpt", RECORDED)
def test_recorded_signatures_are_transient_provider_faults(excerpt):
    assert classify_agy_transient_provider_fault(excerpt) == TRANSIENT_PROVIDER_FAULT


@pytest.mark.parametrize(
    "text",
    [
        "Eligibility check failed: UNAVAILABLE (code 503)",
        MIXED_UNRELATED_503,
        "UNAVAILABLE (code 503)",
        "agy_background_task_canceled API error (attempt 1): UNAVAILABLE (code 503)",
        NON_TRANSIENT,
    ],
)
def test_classifier_leaves_owned_and_non_transient_text_alone(text):
    assert classify_agy_transient_provider_fault(text) is None


@pytest.mark.parametrize("excerpt", RECORDED)
def test_read_only_transient_retries_once_then_reroutes(tmp_path, monkeypatch, excerpt):
    result, once, adapter, *_ = _execute(tmp_path, monkeypatch, [_fault(excerpt), _fault(excerpt)])
    assert once.call_count == 2
    adapter.build_invocation.assert_called_once()
    telemetry = result.parse.agy_telemetry
    assert result.parse.agy_retry_reason == TRANSIENT_PROVIDER_FAULT
    assert telemetry.retry_disposition == "exhausted"
    assert telemetry.reroute_required
    assert telemetry.reroute_reason == "agy_retry_exhausted"
    assert telemetry.task_fields()["agy_attempts"]


def test_read_only_transient_retry_can_succeed(tmp_path, monkeypatch):
    result, once, *_ = _execute(tmp_path, monkeypatch, [_fault(INTERRUPTED), _fault(INTERRUPTED, ok=True)])
    assert once.call_count == 2
    assert result.parse.ok
    assert result.parse.agy_retry_reason == TRANSIENT_PROVIDER_FAULT
    assert result.parse.agy_telemetry.retry_disposition == "retried"
    assert result.parse.agy_telemetry.reroute_required is False


def test_write_mode_transient_retries_when_workspace_is_unchanged(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "_agy_git_state", lambda _cwd: (b"head", b""))
    result, once, *_ = _execute(
        tmp_path,
        monkeypatch,
        [_fault(API_503), _fault(API_503, ok=True)],
        mode="workspace-write",
    )
    assert once.call_count == 2
    assert result.parse.ok
    assert result.parse.agy_retry_reason == TRANSIENT_PROVIDER_FAULT
    assert result.parse.agy_telemetry.retry_disposition == "retried"
    assert result.parse.agy_telemetry.reroute_reason is None


@pytest.mark.parametrize(
    "states",
    [
        [(b"head", b""), (b"head", b" M tracked\n")],
        [None],
    ],
    ids=["workspace-changed", "git-unreadable"],
)
def test_write_mode_transient_is_unsafe_replay_without_a_clean_workspace(tmp_path, monkeypatch, states):
    remaining = iter(states)

    monkeypatch.setattr(runner, "_agy_git_state", lambda _cwd: next(remaining))
    result, once, adapter, *_ = _execute(tmp_path, monkeypatch, [_fault(API_503)], mode="workspace-write")
    assert once.call_count == 1
    adapter.build_invocation.assert_not_called()
    assert result.parse.agy_telemetry.retry_disposition == "unsafe_replay"
    assert result.parse.agy_telemetry.reroute_reason == "unsafe_replay"
    assert result.parse.agy_telemetry.reroute_required


def test_non_transient_failure_is_not_retried(tmp_path, monkeypatch):
    result, once, adapter, *_ = _execute(tmp_path, monkeypatch, [_fault(NON_TRANSIENT)])
    assert once.call_count == 1
    adapter.build_invocation.assert_not_called()
    assert result.parse.agy_telemetry.retry_disposition == "no_retry"
    assert result.parse.agy_telemetry.reroute_required is False
