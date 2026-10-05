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
    assert command in result.stderr_excerpt
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
