"""Invocation-owned cancellation recovery for #8771; complete synthetic envelopes."""

from __future__ import annotations

import json
from dataclasses import replace

import pytest

from scripts.agent_runtime.adapters import agy
from scripts.agent_runtime.adapters.agy import AgyAdapter
from tests.agent_runtime.adapters.test_agy_adapter import (
    _FINISHED_CONVERSATION_ID,
    _TASK_2,
    _TASK_3,
    _background_plan,
    _canceled,
    _event,
    _finish,
    _prompt,
    _reply,
    _start,
    _stream_stdout,
    _task_message,
)


def _kill(task=_TASK_2, **extra):
    return _event(
        "PLANNER_RESPONSE",
        "",
        source="MODEL",
        tool_calls=[
            {
                "name": "manage_task",
                "args": {
                    "Action": json.dumps("kill"),
                    "TaskId": json.dumps(task),
                },
            }
        ],
        **extra,
    )


def _parse(tmp_path, events, *, stderr="", envelope=None, returncode=0):
    plan = _background_plan(tmp_path, _FINISHED_CONVERSATION_ID, events)
    plan = replace(plan, cmd=["agy", "--input-format", "stream-json", "--output-format", "stream-json"])
    stdout = _stream_stdout(
        envelope
        or {
            "conversation_id": _FINISHED_CONVERSATION_ID,
            "status": "SUCCESS",
            "response": "Complete reply.",
        }
    )
    return AgyAdapter().parse_response(
        stdout=stdout,
        stderr=stderr,
        returncode=returncode,
        output_file=None,
        plan=plan,
    )


@pytest.mark.parametrize(
    "command",
    [
        "grep -rn needle scripts",
        "rg needle scripts",
        "git grep needle",
        "find scripts -name '*.py'",
        "ls -la scripts",
        "git log -Sneedle --oneline",
        "git show HEAD:scripts/config.py",
        "cat scripts/config.py",
        "sed -n '1,20p' scripts/config.py",
        "head -20 scripts/config.py",
        "tail -20 scripts/config.py",
        "rg needle scripts 2>/dev/null",
        "rg needle scripts || true",
        "rg needle scripts 2>/dev/null || true",
        "git grep -E 'a|b'",
        'git grep -E "a|b"',
        "git log -S x || true",
        "git grep x | head -n 5",
        "rg 'a|b' scripts | grep needle",
        "rg 'a*b' src",
        'rg "a*b" src',
        r"rg a\*b src",
        "rg 'a?b' src",
        'rg "[ab]" src',
        r"rg \[ab\] src",
        "ls '{a,b}'",
        'ls "{a,b}"',
        r"ls \{a,b\}",
        "cat '|'",
    ],
)
def test_agy_model_killed_read_with_complete_reply_is_accepted(tmp_path, command):
    result = _parse(
        tmp_path,
        [
            _prompt(),
            _start(_TASK_2, description=command),
            _kill(),
            _canceled(_TASK_2),
            _reply("Complete reply."),
        ],
    )
    assert result.ok
    assert result.response == "Complete reply."
    assert result.agy_killed_commands == [command]


@pytest.mark.parametrize(
    "command",
    [
        "pytest -q",
        "python -m pytest",
        "npm test",
        "make check",
        "sh checks.sh",
        "checks.sh",
        "unknown",
        "rg needle; pytest",
        "rg needle && pytest",
        "cat file > output",
        "cat $(script)",
        "cat `script`",
        "find . -delete",
        "find . -exec sh checks.sh +",
        "find . -execdir sh checks.sh +",
        "find . -ok sh checks.sh +",
        "find . -fprint output",
        "rg --pre=script needle",
        "rg --hostname-bin script needle",
        "git grep --open-files-in-pager=script needle",
        "git grep -Oscript needle",
        "git -c alias.x=script show",
        "git show --ext-diff",
        "git show --textconv",
        "git log --output=file",
        "sed -n '1e script' file",
        "sed -i '1p' file",
        "sed -n 'w output' file",
        "rg 'unterminated",
        "cat list | xargs sed -n 1p",
        "cat list | xargs rg needle",
        "cat list | xargs git log",
        "cat list | xargs find .",
        "find scripts -name '*.py' | xargs grep -l foo",
        "find scripts -name '*.py' | xargs -r grep -l needle",
        "find scripts -name '*.py' | xargs -- grep -l needle",
        "xargs grep needle",
        "xargs grep needle | head -n 5",
        "cat list | xargs grep needle | head -n 5",
        "cat list | 'xargs' grep needle",
        "rg needle *",
        "grep -r x src/*.py",
        "ls {a,b}",
        "rg needle ?",
        "rg needle [ab]",
        "ls {1..3}",
        "rg 'needle'* src",
        'rg "needle"? src',
        "cat list | rg needle *",
        "rg needle src 2>/dev/null || true | xargs grep needle",
    ],
)
def test_agy_model_killed_check_is_rejected_and_named(tmp_path, command):
    result = _parse(
        tmp_path,
        [
            _prompt(),
            _start(_TASK_2, description=command),
            _kill(),
            _canceled(_TASK_2),
            _reply("Complete reply."),
        ],
    )
    assert not result.ok
    assert result.response == ""
    assert result.stderr_excerpt.startswith(agy.AGY_BACKGROUND_TASK_CANCELED)
    assert json.dumps(command) in result.stderr_excerpt
    assert result.agy_killed_commands == [command]


@pytest.mark.parametrize(
    "case",
    [
        "external",
        "terminated",
        "timeout",
        "open-timer",
        "open-command",
        "missing-end",
        "late-end",
        "late-kill",
        "kill-before-start",
        "failed-end",
        "tool-reply",
        "empty-reply",
        "partial-reply",
        "progress-after-end",
        "wrong-task",
        "non-model-kill",
        "quoted-kill",
        "error-envelope",
    ],
)
def test_agy_cancel_exception_preserves_fail_closed_cases(tmp_path, case):
    start = _start(_TASK_2, description="git grep needle")
    end = _canceled(_TASK_2)
    events = [_prompt(), start, _kill(), end, _reply("Complete reply.")]
    stderr = ""
    envelope = None
    if case == "external":
        events.pop(2)
    elif case == "terminated":
        stderr = "terminating 1 background task(s)"
    elif case == "timeout":
        stderr = "print timeout after 120m with turn in progress"
    elif case in {"open-timer", "open-command"}:
        events.insert(1, _start(_TASK_3, description="Timer: check later" if case == "open-timer" else "ls"))
    elif case == "missing-end":
        events.pop(3)
    elif case == "late-end":
        events[3], events[4] = events[4], events[3]
    elif case == "late-kill":
        events[2], events[3] = events[3], events[2]
    elif case == "kill-before-start":
        events[1], events[2] = events[2], events[1]
    elif case == "failed-end":
        events[3] = _task_message(_TASK_2, f'Task id "{_TASK_2}" failed with result:')
    elif case == "tool-reply":
        events[4] = _event("PLANNER_RESPONSE", "Complete reply.", source="MODEL", tool_calls=[{"name": "run_command"}])
    elif case == "empty-reply":
        events[4] = _reply("")
    elif case == "partial-reply":
        events[4] = _event("PLANNER_RESPONSE", "Complete reply.", source="MODEL", status="RUNNING")
    elif case == "progress-after-end":
        events.insert(4, _task_message(_TASK_2, "Still running"))
    elif case == "wrong-task":
        events[2] = _kill(_TASK_3)
    elif case == "non-model-kill":
        kill = json.loads(events[2])
        kill["source"] = "SYSTEM"
        events[2] = json.dumps(kill)
    elif case == "quoted-kill":
        events[2] = _event("GENERIC", _kill(), source="MODEL")
    elif case == "error-envelope":
        envelope = {"conversation_id": _FINISHED_CONVERSATION_ID, "status": "ERROR", "error": "failed"}
    result = _parse(tmp_path, events, stderr=stderr, envelope=envelope)
    assert not result.ok
    assert result.response == ""
    if case not in {"external", "non-model-kill", "quoted-kill"}:
        assert result.agy_killed_commands


def test_agy_all_killed_commands_survive_mixed_outcome(tmp_path):
    events = [
        _prompt(),
        _start(_TASK_2, description="git grep needle"),
        _kill(),
        _canceled(_TASK_2),
        _start(_TASK_3, description="pytest -q"),
        _kill(_TASK_3),
        _canceled(_TASK_3),
        _reply("Complete reply."),
    ]
    result = _parse(tmp_path, events)
    assert not result.ok
    assert result.agy_killed_commands == ["git grep needle", "pytest -q"]
    assert "pytest -q" in result.stderr_excerpt


def test_agy_kill_diagnostics_are_redacted_before_bounding(tmp_path):
    command = "rg 'token=" + "secret-value" * 100 + "' file"
    result = _parse(
        tmp_path,
        [_prompt(), _start(_TASK_2, description=command), _kill(), _canceled(_TASK_2), _reply("Complete reply.")],
    )
    assert result.ok
    assert "secret-value" not in result.agy_killed_commands[0]
    assert len(result.agy_killed_commands[0]) <= 500
    long_read = "rg needle " + "file " * 200
    result = _parse(
        tmp_path / "long-command",
        [_prompt(), _start(_TASK_2, description=long_read), _kill(), _canceled(_TASK_2), _reply("Complete reply.")],
    )
    assert len(result.agy_killed_commands[0]) == 500


def test_agy_finished_background_work_can_coexist_with_killed_read(tmp_path):
    result = _parse(
        tmp_path,
        [
            _prompt(),
            _start(_TASK_2, description="git grep needle"),
            _kill(),
            _canceled(_TASK_2),
            _start(_TASK_3),
            _finish(_TASK_3),
            _reply("Complete reply."),
        ],
    )
    assert result.ok
    assert result.agy_killed_commands == ["git grep needle"]


@pytest.mark.parametrize("command", ["", "git", "cat file\npytest", "find . -fprintf output", "rg needle | pytest"])
def test_agy_allowlist_rejects_empty_incomplete_and_composed_commands(command):
    assert not agy._read_only_killed_command(command)


def test_agy_past_kill_cannot_authorize_a_later_external_cancellation(tmp_path):
    result = _parse(
        tmp_path,
        [
            _prompt(),
            _start(_TASK_2, description="git grep needle"),
            _kill(),
            _canceled(_TASK_2),
            _finish(_TASK_2),
            _canceled(_TASK_2),
            _reply("Complete reply."),
        ],
    )
    assert not result.ok
    assert result.agy_killed_commands == ["git grep needle"]


def test_agy_abandoned_check_is_named_even_after_a_long_killed_read(tmp_path):
    command = "rg needle " + "file " * 200
    result = _parse(
        tmp_path,
        [
            _prompt(),
            _start(_TASK_2, description=command),
            _kill(),
            _canceled(_TASK_2),
            _start(_TASK_3, description="pytest -q"),
            _kill(_TASK_3),
            _canceled(_TASK_3),
            _reply("Complete reply."),
        ],
    )
    assert not result.ok
    assert "pytest -q" in result.stderr_excerpt
    assert result.agy_killed_commands == [command[:500], "pytest -q"]


@pytest.mark.parametrize("command", ["git show --ext", "git show --textc", "git log --out=file", "cat file\npytest"])
def test_agy_executable_option_abbreviations_and_multiline_commands_fail(tmp_path, command):
    result = _parse(
        tmp_path,
        [_prompt(), _start(_TASK_2, description=command), _kill(), _canceled(_TASK_2), _reply("Complete reply.")],
    )
    assert not result.ok
    assert result.agy_killed_commands == [command]


@pytest.mark.parametrize(
    "command",
    [
        "find scripts | xargs rm",
        "grep needle scripts | sh",
        "find scripts | xargs -I{} grep needle {}",
        "find scripts | xargs -i grep needle",
        "find scripts | xargs --replace={} grep needle",
        "find scripts | xargs -0 grep needle",
        "find scripts | xargs --null grep needle",
        "find scripts | xargs",
        "find scripts | xargs bash",
        "find scripts | xargs xargs grep needle",
        "cat file > output",
        "cat file; rm x",
        "cat file && true",
        "cat file 2 > /dev/null",
        "cat file 2>/other",
        "cat file 1>/dev/null",
        "cat file 2>>/dev/null",
        "cat file 2>/dev/null | rm x",
        "cat file || true; rm x",
        "cat file || false",
        "cat file |",
        "| cat file",
        "cat file ||",
        "cat file | git show --output=file",
        "cat file | xargs git grep -Oless",
        "cat file | sed -n '1p;w output'",
        "cat file | xargs rg --pre=writer",
        "cat file | xargs sed -i '1p'",
    ],
)
def test_agy_parsed_composition_rejects_writers_and_other_shell_syntax(command):
    assert not agy._read_only_killed_command(command)


@pytest.mark.parametrize("events", [[], [_prompt()], [_reply("reply")]])
def test_agy_pre_model_proof_requires_no_prompt_or_model_event(tmp_path, events):
    from scripts.agent_runtime.adapters.base import InvocationPlan

    if events:
        plan = _background_plan(tmp_path, _FINISHED_CONVERSATION_ID, events)
    else:
        plan = InvocationPlan(
            cmd=["agy"], cwd=tmp_path, env_overrides={agy._AGY_LOG_ENV: str(tmp_path / "missing.log")}
        )
    result = AgyAdapter().parse_response(
        stdout="",
        stderr="Eligibility check failed: UNAVAILABLE (code 503)",
        returncode=1,
        output_file=None,
        plan=plan,
    )
    assert result.agy_pre_model_failure is (not events)


@pytest.mark.parametrize(
    "stdout",
    [
        '{"event":"user","message":{"role":"user"}}',
        '{"event":"step_update","step_update":{"state":"RUNNING"}}',
        '{"event":"result","result":{"status":"ERROR","response":"model reply"}}',
        "malformed output",
    ],
)
def test_agy_pre_model_proof_rejects_started_or_unknown_stream(tmp_path, stdout):
    from scripts.agent_runtime.adapters.base import InvocationPlan

    plan = InvocationPlan(
        cmd=["agy", "stream-json"], cwd=tmp_path, env_overrides={agy._AGY_LOG_ENV: str(tmp_path / "missing.log")}
    )
    result = AgyAdapter().parse_response(
        stdout=stdout,
        stderr="Eligibility check failed: UNAVAILABLE (code 503)",
        returncode=1,
        output_file=None,
        plan=plan,
    )
    assert not result.agy_pre_model_failure


def test_agy_pre_model_proof_accepts_lone_provider_error(tmp_path):
    from scripts.agent_runtime.adapters.base import InvocationPlan

    plan = InvocationPlan(
        cmd=["agy", "stream-json"], cwd=tmp_path, env_overrides={agy._AGY_LOG_ENV: str(tmp_path / "missing.log")}
    )
    result = AgyAdapter().parse_response(
        stdout=json.dumps(
            {
                "event": "result",
                "result": {"status": "ERROR", "error": "Eligibility check failed: UNAVAILABLE (code 503)"},
            }
        ),
        stderr="",
        returncode=1,
        output_file=None,
        plan=plan,
    )
    assert result.agy_pre_model_failure


@pytest.mark.parametrize("command", ["python -c 'print(1)'", "git grep " + "x" * 600 + " | rm output"])
def test_agy_killed_non_read_command_stays_rejected_if_finish_races_with_kill(tmp_path, command):
    result = _parse(
        tmp_path,
        [_prompt(), _start(_TASK_2, description=command), _kill(), _finish(_TASK_2), _reply("Complete reply.")],
    )
    assert not result.ok
    assert result.stderr_excerpt.startswith(agy.AGY_BACKGROUND_TASK_CANCELED)
    assert result.agy_killed_commands == [command[:500]]


@pytest.mark.parametrize(
    "case", ["unsafe-log", "missing-transcript", "unreadable-slice", "unknown-resume", "truncated-log"]
)
def test_agy_pre_model_proof_rejects_unknown_transcript_evidence(tmp_path, case):
    from scripts.agent_runtime.adapters.base import InvocationPlan

    log = tmp_path / "attempt.log"
    metadata = {}
    bound = None
    if case == "unsafe-log":
        target = tmp_path / "target.log"
        target.write_text("")
        log.symlink_to(target)
    elif case == "missing-transcript":
        log.write_text(f"Print mode: conversation={_FINISHED_CONVERSATION_ID}, sending message\n")
    elif case == "truncated-log":
        log.write_text("Print mode: conversation=partial")
    elif case == "unreadable-slice":
        bound = agy._TranscriptSlice(tmp_path / "transcript.jsonl", [], 1)
    else:
        metadata[agy._TRANSCRIPT_BASELINE_KEY] = {"conversation_id": _FINISHED_CONVERSATION_ID, "offset": None}
    plan = InvocationPlan(cmd=["agy"], cwd=tmp_path, env_overrides={agy._AGY_LOG_ENV: str(log)}, metadata=metadata)
    assert not agy._pre_model_failure(plan, "", bound)
