"""No provider calls: eligibility retry bounds and AGY result/record persistence (#8771)."""

from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from scripts.agent_runtime import runner
from scripts.agent_runtime.adapters.base import InvocationPlan
from scripts.agent_runtime.result import AgyAttempt, ParseResult

ELIGIBILITY_503 = "Eligibility check failed: UNAVAILABLE (code 503)"


def _outcome(*, pre_model=True, ok=False, stderr=ELIGIBILITY_503, reason=None, kill=None, commands=(), duration=2):
    return runner._ExecutionOutcome(
        parse=ParseResult(
            ok=ok,
            response="Complete reply." if ok else "",
            stderr_excerpt=reason,
            provider_error_text="",
            agy_killed_commands=list(commands),
            agy_pre_model_failure=pre_model,
            agy_attempt=AgyAttempt(completion_reason=reason.splitlines()[0]) if reason else None,
            failure_code="provider_stream_incomplete" if reason == "agy_background_task_canceled\nmore" else None,
        ),
        duration_s=duration,
        returncode=0 if ok else 1,
        kill_reason=kill,
        stdout_text="",
        stderr_text=stderr,
        liveness_paths=(),
    )


def _execute(tmp_path, monkeypatch, outcomes, *, agent="agy", mode="read-only", times=(0, 2, 2)):
    once = Mock(side_effect=outcomes)
    monkeypatch.setattr(runner, "_execute_invocation_once", once)

    def clock():
        if once.call_count == 0:
            return times[0]
        if adapter.build_invocation.call_count == 0:
            return times[min(1, len(times) - 1)]
        return times[-1]

    monkeypatch.setattr(runner.time, "monotonic", clock)
    first_plan = InvocationPlan(cmd=["fake-agy"], cwd=tmp_path)
    retry_plan = InvocationPlan(cmd=["fake-agy-retry"], cwd=tmp_path)
    adapter = SimpleNamespace(build_invocation=Mock(return_value=retry_plan))
    result = runner._execute_invocation_plan(
        agent_name=agent,
        adapter=adapter,
        plan=first_plan,
        prompt="prompt",
        mode=mode,
        cwd=tmp_path,
        model="gemini-3.8-flash-high",
        task_id="fixture-task",
        session_id=None,
        entrypoint="delegate",
        hard_timeout=30,
        stall_timeout=10,
    )
    return result, once, adapter, first_plan, retry_plan


@pytest.mark.parametrize("retry_ok", [True, False], ids=["retry-success", "retry-fails-no-third-attempt"])
def test_agy_eligibility_503_retries_once_then_returns_outcome(tmp_path, monkeypatch, retry_ok):
    result, once, adapter, first, retry = _execute(
        tmp_path,
        monkeypatch,
        [_outcome(), _outcome(ok=retry_ok, duration=3)],
    )
    assert once.call_count == 2
    assert once.call_args_list[0].kwargs["plan"] is first
    assert once.call_args_list[1].kwargs["plan"] is retry
    assert once.call_args_list[1].kwargs["hard_timeout"] == 28
    assert result.parse.ok is retry_ok
    assert result.duration_s == 5
    assert result.parse.agy_attempt_count == 2
    assert result.parse.agy_retry_reason == "pre_model_eligibility_503"
    adapter.build_invocation.assert_called_once()


@pytest.mark.parametrize(
    "first,agent",
    [
        (_outcome(stderr="Eligibility check failed: account blocked"), "agy"),
        (_outcome(stderr="UNAVAILABLE (code 503)"), "agy"),
        (_outcome(stderr="Eligibility check failed: UNAVAILABLE (code 500)"), "agy"),
        (_outcome(), "codex"),
        (_outcome(ok=True), "agy"),
        (_outcome(kill="hard_timeout"), "agy"),
        (_outcome(commands=["pytest"]), "agy"),
        (_outcome(reason="agy_background_task_canceled\nmore"), "agy"),
    ],
    ids=[
        "account-block",
        "bare-503",
        "other-code",
        "other-adapter",
        "already-success",
        "timeout",
        "model-kill",
        "external-cancel",
    ],
)
def test_agy_non_eligibility_failures_are_not_retried(tmp_path, monkeypatch, first, agent):
    result, once, adapter, *_ = _execute(tmp_path, monkeypatch, [first], agent=agent)
    assert result.parse.ok is first.parse.ok
    assert once.call_count == 1
    adapter.build_invocation.assert_not_called()


def test_agy_retry_reads_only_provider_error_not_model_response(tmp_path, monkeypatch):
    first = _outcome(stderr="unrelated")
    first = replace(first, parse=replace(first.parse, response=ELIGIBILITY_503))
    result, once, *_ = _execute(tmp_path, monkeypatch, [first])
    assert result.parse.ok is first.parse.ok
    assert once.call_count == 1


def test_agy_terminal_provider_eligibility_503_is_retried(tmp_path, monkeypatch):
    first = _outcome(stderr="")
    first = replace(first, parse=replace(first.parse, provider_error_text=ELIGIBILITY_503))
    result, once, *_ = _execute(tmp_path, monkeypatch, [first, _outcome(ok=True)])
    assert result.parse.ok
    assert once.call_count == 2


def test_agy_retry_does_not_extend_exhausted_timeout(tmp_path, monkeypatch):
    first = _outcome()
    result, once, adapter, *_ = _execute(tmp_path, monkeypatch, [first], times=(0, 30))
    assert result.parse.ok is first.parse.ok
    assert once.call_count == 1
    adapter.build_invocation.assert_not_called()


@pytest.mark.parametrize("ok", [True, False], ids=["accepted-read", "abandoned-check"])
def test_agy_killed_commands_reach_result_and_persisted_usage_record(tmp_path, monkeypatch, ok):
    commands = ["git grep needle", "pytest -q"] if not ok else ["git grep needle"]
    execution = _outcome(ok=ok, stderr="", commands=commands)
    execution = replace(
        execution, parse=replace(execution.parse, agy_attempt_count=2, agy_retry_reason="pre_model_eligibility_503")
    )
    adapter = SimpleNamespace(
        default_model="gemini-3.8-flash-high",
        supported_modes={"read-only"},
        build_invocation=Mock(return_value=InvocationPlan(cmd=["fake-agy"], cwd=tmp_path)),
    )
    monkeypatch.setattr(runner, "_load_adapter", lambda _: adapter)
    monkeypatch.setattr(runner, "has_headroom", lambda *_: (True, ""))
    monkeypatch.setattr(runner, "load_failover_chain", lambda *_, **__: None)
    monkeypatch.setattr(runner, "_execute_invocation_once", lambda **_: execution)
    monkeypatch.setattr(
        runner,
        "_resolve_plan_telemetry",
        lambda **_: SimpleNamespace(
            model="gemini-3.8-flash-high",
            effort="high",
            cli_version="fixture",
        ),
    )
    write = Mock()
    monkeypatch.setattr(runner, "write_record", write)
    result = runner._invoke_impl("agy", "prompt", cwd=tmp_path, task_id="fixture-task", entrypoint="delegate")
    assert result.ok is ok
    assert result.agy_killed_commands == commands
    assert result.usage_record["agy_killed_commands"] == commands
    assert write.call_args.args[0]["agy_killed_commands"] == commands
    assert write.call_args.args[0]["agy_attempt_count"] == 1
    assert write.call_args.args[0]["agy_retry_reason"] is None


def test_agy_retry_plan_build_counts_against_original_timeout(tmp_path, monkeypatch):
    first = _outcome()
    result, once, adapter, *_ = _execute(tmp_path, monkeypatch, [first], times=(0, 2, 30))
    assert result.parse.ok is first.parse.ok
    assert once.call_count == 1
    adapter.build_invocation.assert_called_once()


def test_agy_retry_wrapper_leaves_other_adapters_clock_and_plan_untouched(tmp_path, monkeypatch):
    first = _outcome()
    result, once, adapter, *_ = _execute(tmp_path, monkeypatch, [first], agent="codex", times=())
    assert result.parse.ok is first.parse.ok
    assert once.call_count == 1
    adapter.build_invocation.assert_not_called()


@pytest.mark.parametrize(
    "fields",
    [
        {},
        {"agy_attempt_count": None, "agy_retry_reason": None, "agy_killed_commands": None},
        {"agy_attempt_count": "2", "agy_retry_reason": 503, "agy_killed_commands": "git grep needle"},
        {"agy_attempt_count": True, "agy_retry_reason": [], "agy_killed_commands": ["git grep needle", 1]},
        {"agy_attempt_count": object(), "agy_retry_reason": object(), "agy_killed_commands": ("git grep needle",)},
    ],
    ids=["missing", "none", "wrong-types", "bool-and-mixed-list", "objects-and-tuple"],
)
def test_non_agy_result_optional_retry_fields_are_typed(tmp_path, monkeypatch, fields):
    values = vars(ParseResult(ok=True, response="Complete reply.")).copy()
    for name in ("agy_attempt_count", "agy_retry_reason", "agy_killed_commands"):
        values.pop(name)
    values.update(fields)
    execution = replace(_outcome(ok=True, stderr=""), parse=SimpleNamespace(**values))
    adapter = SimpleNamespace(
        default_model="fixture-model",
        supported_modes={"read-only"},
        build_invocation=Mock(return_value=InvocationPlan(cmd=["fake-codex"], cwd=tmp_path)),
    )
    monkeypatch.setattr(runner, "_load_adapter", lambda _: adapter)
    monkeypatch.setattr(runner, "has_headroom", lambda *_: (True, ""))
    monkeypatch.setattr(runner, "load_failover_chain", lambda *_, **__: None)
    monkeypatch.setattr(runner, "_execute_invocation_once", lambda **_: execution)
    monkeypatch.setattr(
        runner,
        "_resolve_plan_telemetry",
        lambda **_: SimpleNamespace(model="fixture-model", effort="high", cli_version="fixture"),
    )
    write = Mock()
    monkeypatch.setattr(runner, "write_record", write)

    result = runner._invoke_impl("codex", "prompt", cwd=tmp_path, task_id="fixture-task", entrypoint="delegate")

    assert result.ok
    assert result.agy_killed_commands == []
    assert not {"agy_attempt_count", "agy_retry_reason", "agy_killed_commands"} & result.usage_record.keys()
    assert write.call_args.args[0] == result.usage_record


@pytest.mark.parametrize("agent", ["agy", "codex", "gemini"])
@pytest.mark.parametrize(
    "count, reason, commands, expected",
    [
        ("2", 503, "git grep needle", (1, None, [])),
        (True, [], ("git grep needle",), (1, None, [])),
        (None, None, None, (1, None, [])),
        (2, object(), ["git grep needle"], (2, None, ["git grep needle"])),
        (
            object(),
            "pre_model_eligibility_503",
            ["git grep needle"],
            (1, "pre_model_eligibility_503", ["git grep needle"]),
        ),
        (2, "pre_model_eligibility_503", ["git grep needle", 1], (2, "pre_model_eligibility_503", [])),
    ],
)
def test_usage_record_validates_optional_retry_fields_for_every_agent(
    tmp_path, agent, count, reason, commands, expected
):
    record = runner._build_usage_record(
        agent=agent,
        entrypoint="delegate",
        model="fixture",
        mode="read-only",
        task_id="fixture",
        cwd=tmp_path,
        session_id=None,
        duration_s=1,
        input_chars=1,
        output_chars=1,
        returncode=0,
        outcome="ok",
        rate_limited=False,
        stalled=False,
        stderr_excerpt=None,
        tokens=None,
        agy_attempt_count=count,
        agy_retry_reason=reason,
        agy_killed_commands=commands,
    )
    assert (
        record.get("agy_attempt_count", 1),
        record.get("agy_retry_reason"),
        record.get("agy_killed_commands", []),
    ) == expected


@pytest.mark.parametrize("ok", [True, False])
@pytest.mark.parametrize("has_kills", [True, False], ids=["kills", "no-kills"])
def test_agy_killed_commands_survive_gemini_ladder_result(tmp_path, monkeypatch, ok, has_kills):
    from ai_llm.fallback import PRIMARY_GEMINI_MODEL

    adapter = SimpleNamespace(build_invocation=lambda **_: InvocationPlan(cmd=["fake-cli"], cwd=tmp_path))
    commands = (["git grep needle"] if ok else ["pytest -q"]) if has_kills else []

    def execute(**kwargs):
        is_agy = kwargs["agent_name"] == "agy"
        outcome = _outcome(ok=ok and is_agy, stderr="", commands=commands if is_agy else ())
        if is_agy:
            outcome = replace(
                outcome, parse=replace(outcome.parse, agy_attempt_count=2, agy_retry_reason="pre_model_eligibility_503")
            )
        if not is_agy:
            outcome = replace(outcome, parse=replace(outcome.parse, rate_limited=True, stderr_excerpt="429 quota"))
        return outcome

    monkeypatch.setattr(runner, "_load_adapter", lambda _: adapter)
    monkeypatch.setattr(runner, "has_headroom", lambda *_: (True, ""))
    monkeypatch.setattr(runner, "_execute_invocation_plan", execute)
    monkeypatch.setattr(runner, "_resolve_gemini_ladder_auth_modes", lambda _: ("oauth",))
    monkeypatch.setattr(
        runner,
        "_resolve_plan_telemetry",
        lambda **kw: SimpleNamespace(
            model=kw["requested_model"],
            effort="high",
            cli_version="fixture",
        ),
    )
    write = Mock()
    monkeypatch.setattr(runner, "write_record", write)
    result = runner._invoke_gemini_with_fallback(
        agent_name="gemini",
        adapter=adapter,
        prompt="prompt",
        mode="read-only",
        cwd=tmp_path,
        model=PRIMARY_GEMINI_MODEL,
        task_id="fixture-task",
        session_id=None,
        tool_config=None,
        entrypoint="delegate",
        hard_timeout=30,
        stall_timeout=10,
    )
    assert result.ok is ok
    assert result.agy_killed_commands == commands
    assert result.usage_record["agy_killed_commands"] == commands
    assert write.call_args.args[0]["agy_killed_commands"] == commands
    assert result.usage_record["agy_attempt_count"] == 2
    assert result.usage_record["agy_retry_reason"] == "pre_model_eligibility_503"


@pytest.mark.parametrize("mode", ["read-only", "workspace-write", "danger"])
@pytest.mark.parametrize("pre_model", [True, False], ids=["pre-model", "model-started"])
def test_agy_retry_requires_pre_model_proof_in_every_mode(tmp_path, monkeypatch, mode, pre_model):
    first = _outcome(pre_model=pre_model)
    eligible = pre_model and mode == "read-only"
    outcomes = [first, _outcome(ok=True)] if eligible else [first]
    result, once, *_ = _execute(tmp_path, monkeypatch, outcomes, mode=mode)
    assert once.call_count == (2 if eligible else 1)
    assert result.parse.agy_attempt_count == (2 if eligible else 1)


@pytest.mark.parametrize("provider_record", [False, True])
def test_agy_retry_rejects_503_from_an_unrelated_error(tmp_path, monkeypatch, provider_record):
    errors = "API error (attempt 1): UNAVAILABLE (code 503)\nEligibility check failed: PERMISSION_DENIED (code 403)"
    first = _outcome(stderr="" if provider_record else errors)
    if provider_record:
        first = replace(first, parse=replace(first.parse, provider_error_text=errors))
    result, once, *_ = _execute(tmp_path, monkeypatch, [first])
    assert result.parse.ok is first.parse.ok
    assert once.call_count == 1


def test_agy_usage_record_caps_encoded_killed_commands(tmp_path):
    import json

    commands = ["git grep " + "ї" * 800 for _ in range(100)]
    record = runner._build_usage_record(
        agent="agy",
        entrypoint="delegate",
        model="gemini-3.8-flash-high",
        mode="read-only",
        task_id="fixture",
        cwd=tmp_path,
        session_id=None,
        duration_s=5,
        input_chars=10,
        output_chars=10,
        returncode=0,
        outcome="ok",
        rate_limited=False,
        stalled=False,
        stderr_excerpt="ї" * 500,
        tokens=None,
        agy_killed_commands=commands,
        agy_attempt_count=2,
        agy_retry_reason="pre_model_eligibility_503",
    )
    assert len((json.dumps(record, ensure_ascii=False, default=str) + "\n").encode("utf-8")) <= 4096
    kept = record["agy_killed_commands"]
    assert kept and all(len(command) <= 500 for command in kept)
    assert kept[-1] == f"{100 - len(kept) + 1} more"
    assert record["agy_attempt_count"] == 2
    assert record["agy_retry_reason"] == "pre_model_eligibility_503"


def _cancel(*, kill=None, exited=True):
    outcome = _outcome(stderr="", reason="agy_background_task_canceled", kill=kill)
    return replace(
        outcome,
        process_group_exited=exited,
        parse=replace(
            outcome.parse,
            failure_code="provider_stream_incomplete",
            provider_error_text="",
            agy_attempt=AgyAttempt(completion_reason="agy_background_task_canceled", evidence_complete=True),
        ),
    )


@pytest.mark.parametrize("second", [_outcome(ok=True, stderr=""), _cancel(), _outcome()])
def test_cancellation_retries_once_with_fresh_input(tmp_path, monkeypatch, second):
    monkeypatch.setattr(runner, "_agy_git_state", lambda _: (b"head", b"clean"))
    result, once, adapter, *_ = _execute(tmp_path, monkeypatch, [_cancel(), second])
    assert once.call_count == 2
    assert result.parse.ok is second.parse.ok
    assert result.parse.agy_retry_reason == "incomplete_cancellation"
    telemetry = result.parse.agy_telemetry
    assert len(telemetry.attempts) == 2
    assert telemetry.accepted_attempt == (2 if second.parse.ok else None)
    assert telemetry.reroute_required is not second.parse.ok
    assert telemetry.retry_disposition == ("retried" if second.parse.ok else "exhausted")
    assert adapter.build_invocation.call_args.kwargs["session_id"] is None
    assert adapter.build_invocation.call_args.kwargs["prompt"] == "prompt"
    assert once.call_args.kwargs["hard_timeout"] == 28


def test_503_then_cancellation_shares_retry(tmp_path, monkeypatch):
    result, once, *_ = _execute(tmp_path, monkeypatch, [_outcome(), _cancel()])
    assert once.call_count == 2
    assert result.parse.agy_telemetry.retry_disposition == "exhausted"
    assert result.parse.agy_telemetry.reroute_required


@pytest.mark.parametrize(
    "before,after,exited",
    [
        ((b"head", b"clean"), (b"new", b"clean"), True),
        ((b"head", b"clean"), (b"head", b"dirty"), True),
        (None, None, True),
        ((b"head", b"clean"), None, True),
        ((b"head", b"clean"), (b"head", b"clean"), False),
    ],
)
def test_cancellation_replay_requires_unchanged_readable_git_and_group_exit(
    tmp_path, monkeypatch, before, after, exited
):
    monkeypatch.setattr(runner, "_agy_git_state", Mock(side_effect=[before, after]))
    result, once, adapter, *_ = _execute(tmp_path, monkeypatch, [_cancel(exited=exited)])
    assert once.call_count == 1
    adapter.build_invocation.assert_not_called()
    assert result.parse.agy_telemetry.retry_disposition == "unsafe_replay"


@pytest.mark.parametrize("mode", ["danger", "workspace-write"])
@pytest.mark.parametrize("first", [_cancel(), _outcome()])
def test_write_modes_never_replay(tmp_path, monkeypatch, mode, first):
    result, once, *_ = _execute(tmp_path, monkeypatch, [first], mode=mode)
    assert once.call_count == 1
    assert result.parse.agy_telemetry.retry_disposition == "unsafe_replay"


@pytest.mark.parametrize(
    "reason,kill,rate_limit",
    [
        ("agy_background_task_unconfirmed", None, False),
        ("agy_headless_permission_denied", None, False),
        ("agy_background_task_canceled", "hard_timeout", False),
        ("agy_background_task_canceled", "stdout_silence_timeout", False),
        ("agy_background_task_canceled", "initial_response_timeout", False),
        ("agy_background_task_canceled", "primary_tree_write", False),
        ("agy_background_task_canceled", None, True),
    ],
)
def test_ineligible_cancellation_classes_never_retry(tmp_path, monkeypatch, reason, kill, rate_limit):
    outcome = _outcome(stderr="", kill=kill)
    outcome = replace(
        outcome, parse=replace(outcome.parse, rate_limited=rate_limit, agy_attempt=AgyAttempt(completion_reason=reason))
    )
    result, once, adapter, *_ = _execute(tmp_path, monkeypatch, [outcome])
    assert once.call_count == 1
    adapter.build_invocation.assert_not_called()
    assert result.parse.agy_telemetry.retry_reason is None


@pytest.mark.parametrize("empty", [True, False, None])
@pytest.mark.parametrize("cancellation", [True, False])
def test_receipt_cancellation_requires_fresh_dispatch_and_503_requires_empty_ledger(
    tmp_path,
    monkeypatch,
    empty,
    cancellation,
):
    ledger = tmp_path / "attempt.jsonl"
    if empty is not None:
        ledger.write_text("" if empty else '{"receipt": true}\n')
    first = _cancel() if cancellation else _outcome()
    once = Mock(side_effect=[first, _outcome(ok=True)])
    monkeypatch.setattr(runner, "_execute_invocation_once", once)
    monkeypatch.setattr(runner, "_agy_git_state", lambda _: (b"head", b"clean"))
    adapter = SimpleNamespace(build_invocation=Mock(return_value=InvocationPlan(cmd=["agy"], cwd=tmp_path)))
    result = runner._execute_invocation_plan(
        agent_name="agy",
        adapter=adapter,
        plan=InvocationPlan(cmd=["agy"], cwd=tmp_path),
        prompt="original",
        mode="read-only",
        cwd=tmp_path,
        model="fixture",
        task_id="parent",
        session_id=None,
        entrypoint="delegate",
        hard_timeout=30,
        stall_timeout=10,
        tool_config={"attempt_id": "attempt", "review_ledger_path": str(ledger)},
    )
    assert once.call_count == (2 if empty and not cancellation else 1)
    fields = result.parse.agy_telemetry.task_fields()
    if cancellation:
        assert fields["agy_reroute_reason"] == "receipt_attempt_requires_fresh_dispatch"
        assert fields["agy_replacement_task_id"] == "parent-agy-reroute-1"
    elif not empty:
        assert fields["agy_retry_disposition"] == "unsafe_replay"


def test_real_git_state_detects_worktree_changes(tmp_path, monkeypatch):
    from tests.test_delegate_readonly_guard import _seed_read_only_checkout_fixture

    _seed_read_only_checkout_fixture(tmp_path, monkeypatch)
    before = runner._agy_git_state(tmp_path)
    assert before is not None
    (tmp_path / "tracked.txt").write_text("changed\n")
    assert runner._agy_git_state(tmp_path) != before
    assert runner._agy_git_state(tmp_path / "missing") is None


@pytest.mark.parametrize("error,expected", [(ProcessLookupError(), True), (PermissionError(), False), (None, False)])
def test_process_group_confirmation_fails_closed(monkeypatch, error, expected):
    monkeypatch.setattr(runner.os, "killpg", Mock(side_effect=error))
    assert runner._agy_process_group_exited(12345) is expected
    assert runner._agy_process_group_exited(None) is False


def test_gemini_ladder_cannot_launch_agy_a_third_time(tmp_path, monkeypatch):
    from ai_llm.fallback import CallResult, GeminiRung

    adapter = SimpleNamespace(build_invocation=Mock(return_value=InvocationPlan(cmd=["agy"], cwd=tmp_path)))
    outcomes = Mock(side_effect=[_outcome(stderr="error"), _outcome(stderr="error")])
    monkeypatch.setattr(runner, "_load_adapter", lambda _: adapter)
    monkeypatch.setattr(runner, "has_headroom", lambda *_: (True, ""))
    monkeypatch.setattr(runner, "_execute_invocation_once", outcomes)
    monkeypatch.setattr(
        runner,
        "_resolve_plan_telemetry",
        lambda **_: SimpleNamespace(
            model="fixture",
            effort="high",
            cli_version="fixture-version",
        ),
    )
    monkeypatch.setattr(runner, "write_record", Mock())
    statuses = []

    def ladder(**kwargs):
        for index in range(3):
            outcome = kwargs["attempt_runner"](GeminiRung(index, 3, "fixture", "oauth", "agy-cli"), 1, 30)
            statuses.append(outcome.status)
        return CallResult(None, None, None, 4, error_message="failed")

    monkeypatch.setattr(runner, "run_gemini_fallback_ladder", ladder)
    result = runner._invoke_gemini_with_fallback(
        agent_name="gemini",
        adapter=adapter,
        prompt="original",
        mode="read-only",
        cwd=tmp_path,
        model="fixture",
        task_id="parent",
        session_id=None,
        tool_config=None,
        entrypoint="delegate",
        hard_timeout=30,
        stall_timeout=10,
    )
    assert statuses == ["retryable_error", "retryable_error", "fatal"]
    assert outcomes.call_count == 2
    assert adapter.build_invocation.call_count == 2
    assert result.agy_telemetry.reroute_required
    assert result.usage_record["agy_attempt_count"] == 2
    assert all(attempt["cli_version"] == "fixture-version" for attempt in result.usage_record["agy_attempts"])


def test_retry_preparation_failure_preserves_first_attempt(tmp_path, monkeypatch):
    first = _outcome()
    monkeypatch.setattr(runner, "_execute_invocation_once", Mock(return_value=first))
    adapter = SimpleNamespace(build_invocation=Mock(side_effect=ValueError("refused")))
    result = runner._execute_invocation_plan(
        agent_name="agy",
        adapter=adapter,
        plan=InvocationPlan(cmd=["agy"], cwd=tmp_path),
        prompt="original",
        mode="read-only",
        cwd=tmp_path,
        model="fixture",
        task_id="parent",
        session_id=None,
        entrypoint="delegate",
        hard_timeout=30,
        stall_timeout=10,
    )
    assert result.parse.agy_telemetry.retry_disposition == "preparation_failed"
    assert result.parse.agy_telemetry.retry_reason is None
    assert len(result.parse.agy_telemetry.attempts) == 1


def test_second_attempt_timeout_retains_both_attempts(tmp_path, monkeypatch):
    from scripts.agent_runtime.errors import AgentTimeoutError

    monkeypatch.setattr(runner, "_agy_git_state", lambda _: (b"head", b"clean"))
    execution, *_ = _execute(tmp_path, monkeypatch, [_cancel(), _cancel(kill="hard_timeout")])
    monkeypatch.setattr(runner, "write_record", Mock())
    with pytest.raises(AgentTimeoutError) as caught:
        runner._raise_for_kill_reason(
            agent_name="agy",
            kill_reason="hard_timeout",
            execution=execution,
            prompt="original",
            entrypoint="delegate",
            model="fixture",
            mode="read-only",
            task_id="parent",
            cwd=tmp_path,
            session_id=None,
            stdout_silence_timeout=None,
            initial_response_timeout=None,
            stall_timeout=10,
            hard_timeout=30,
        )
    assert len(caught.value.agy_telemetry.attempts) == 2
    assert caught.value.agy_telemetry.retry_reason == "incomplete_cancellation"


def test_telemetry_rejects_third_attempt_and_invalid_acceptance():
    from scripts.agent_runtime.result import AgyTelemetry

    with pytest.raises(ValueError, match="launch_cap"):
        AgyTelemetry(attempts=(AgyAttempt(),) * 3)
    with pytest.raises(ValueError, match="accepted_attempt"):
        AgyTelemetry(accepted_attempt=1)


def test_permission_refusal_cannot_borrow_cancellation_retry(tmp_path, monkeypatch):
    outcome = _cancel()
    outcome = replace(outcome, parse=replace(outcome.parse, failure_code="provider_policy_refusal"))
    result, once, *_ = _execute(tmp_path, monkeypatch, [outcome])
    assert once.call_count == 1
    assert result.parse.agy_telemetry.retry_reason is None


@pytest.mark.parametrize("kind", ["symlink", "directory", "missing"])
def test_receipt_ledger_unreadable_state_prevents_replay(tmp_path, kind):
    path = tmp_path / "attempt.jsonl"
    if kind == "directory":
        path.mkdir()
    elif kind == "symlink":
        target = tmp_path / "target"
        target.write_text("")
        path.symlink_to(target)
    assert not runner._agy_receipt_ledger_empty({"attempt_id": "attempt", "review_ledger_path": str(path)})
    assert not runner._agy_receipt_ledger_empty({"attempt_id": "attempt"})


def test_changed_tree_during_retry_preparation_prevents_launch(tmp_path, monkeypatch):
    monkeypatch.setattr(
        runner, "_agy_git_state", Mock(side_effect=[(b"head", b"clean"), (b"head", b"clean"), (b"head", b"changed")])
    )
    first = _cancel()
    once = Mock(return_value=first)
    monkeypatch.setattr(runner, "_execute_invocation_once", once)
    cleanup = Mock()
    adapter = SimpleNamespace(
        build_invocation=Mock(return_value=InvocationPlan(cmd=["agy"], cwd=tmp_path)), cleanup_invocation=cleanup
    )
    result = runner._execute_invocation_plan(
        agent_name="agy",
        adapter=adapter,
        plan=InvocationPlan(cmd=["agy"], cwd=tmp_path),
        prompt="original",
        mode="read-only",
        cwd=tmp_path,
        model="fixture",
        task_id="parent",
        session_id=None,
        entrypoint="delegate",
        hard_timeout=30,
        stall_timeout=10,
    )
    assert once.call_count == 1
    cleanup.assert_called_once()
    assert result.parse.agy_telemetry.retry_disposition == "unsafe_replay"


def test_preparation_deadline_refuses_first_launch(tmp_path, monkeypatch):
    once = Mock()
    monkeypatch.setattr(runner, "_execute_invocation_once", once)
    monkeypatch.setattr(runner.time, "monotonic", lambda: 30)
    result = runner._execute_invocation_plan(
        agent_name="agy",
        adapter=SimpleNamespace(),
        plan=InvocationPlan(cmd=["agy"], cwd=tmp_path),
        prompt="original",
        mode="read-only",
        cwd=tmp_path,
        model="fixture",
        task_id="parent",
        session_id=None,
        entrypoint="delegate",
        hard_timeout=30,
        stall_timeout=10,
        agy_budget=runner._AgyLaunchBudget(deadline=30),
    )
    once.assert_not_called()
    assert result.parse.agy_telemetry.task_fields()["agy_attempt_count"] == 0
    assert result.parse.agy_telemetry.retry_disposition == "deadline_exhausted"
