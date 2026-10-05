"""No provider calls: eligibility retry bounds and AGY result/record persistence (#8771)."""

from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from scripts.agent_runtime import runner
from scripts.agent_runtime.adapters.base import InvocationPlan
from scripts.agent_runtime.result import ParseResult

ELIGIBILITY_503 = "Eligibility check failed: UNAVAILABLE (code 503)"


def _outcome(*, ok=False, stderr=ELIGIBILITY_503, reason=None, kill=None, commands=(), duration=2):
    return runner._ExecutionOutcome(
        parse=ParseResult(
            ok=ok,
            response="Complete reply." if ok else "",
            stderr_excerpt=reason,
            provider_error_text="",
            agy_killed_commands=list(commands),
        ),
        duration_s=duration,
        returncode=0 if ok else 1,
        kill_reason=kill,
        stdout_text="",
        stderr_text=stderr,
        liveness_paths=(),
    )


def _execute(tmp_path, monkeypatch, outcomes, *, agent="agy", times=(0, 2, 2)):
    once = Mock(side_effect=outcomes)
    monkeypatch.setattr(runner, "_execute_invocation_once", once)
    monkeypatch.setattr(runner.time, "monotonic", Mock(side_effect=times))
    first_plan = InvocationPlan(cmd=["fake-agy"], cwd=tmp_path)
    retry_plan = InvocationPlan(cmd=["fake-agy-retry"], cwd=tmp_path)
    adapter = SimpleNamespace(build_invocation=Mock(return_value=retry_plan))
    result = runner._execute_invocation_plan(
        agent_name=agent,
        adapter=adapter,
        plan=first_plan,
        prompt="prompt",
        mode="read-only",
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
    assert result is first
    assert once.call_count == 1
    adapter.build_invocation.assert_not_called()


def test_agy_retry_reads_only_provider_error_not_model_response(tmp_path, monkeypatch):
    first = _outcome(stderr="unrelated")
    first = replace(first, parse=replace(first.parse, response=ELIGIBILITY_503))
    result, once, *_ = _execute(tmp_path, monkeypatch, [first])
    assert result is first
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
    assert result is first
    assert once.call_count == 1
    adapter.build_invocation.assert_not_called()


@pytest.mark.parametrize("ok", [True, False], ids=["accepted-read", "abandoned-check"])
def test_agy_killed_commands_reach_result_and_persisted_usage_record(tmp_path, monkeypatch, ok):
    commands = ["git grep needle", "pytest -q"] if not ok else ["git grep needle"]
    execution = _outcome(ok=ok, stderr="", commands=commands)
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


def test_agy_retry_plan_build_counts_against_original_timeout(tmp_path, monkeypatch):
    first = _outcome()
    result, once, adapter, *_ = _execute(tmp_path, monkeypatch, [first], times=(0, 2, 30))
    assert result is first
    assert once.call_count == 1
    adapter.build_invocation.assert_called_once()


def test_agy_retry_wrapper_leaves_other_adapters_clock_and_plan_untouched(tmp_path, monkeypatch):
    first = _outcome()
    result, once, adapter, *_ = _execute(tmp_path, monkeypatch, [first], agent="codex", times=())
    assert result is first
    assert once.call_count == 1
    adapter.build_invocation.assert_not_called()


@pytest.mark.parametrize("ok", [True, False])
def test_agy_killed_commands_survive_gemini_ladder_result(tmp_path, monkeypatch, ok):
    from ai_llm.fallback import PRIMARY_GEMINI_MODEL

    adapter = SimpleNamespace(build_invocation=lambda **_: InvocationPlan(cmd=["fake-cli"], cwd=tmp_path))
    commands = ["git grep needle"] if ok else ["pytest -q"]

    def execute(**kwargs):
        is_agy = kwargs["agent_name"] == "agy"
        outcome = _outcome(ok=ok and is_agy, stderr="", commands=commands if is_agy else ())
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
