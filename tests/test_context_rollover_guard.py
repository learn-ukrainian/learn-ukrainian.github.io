"""Operator-restart rollover guard: post-tier-3 reminder and PreCompact block (#8511)."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
HOOKS = PROJECT_ROOT / "agents_extensions/shared/hooks"
GUARD = HOOKS / "context-rollover-guard.sh"
LIB = HOOKS / "context-rollover-lib.sh"
SETTINGS = PROJECT_ROOT / "agents_extensions/shared/settings.json"
SESSION = "guard-session"


def _project(tmp_path: Path, *, rollover_mode: str | None = "operator_restart") -> tuple[Path, Path]:
    project = tmp_path / "project"
    project.mkdir()
    record: dict[str, object] = {
        "schema_version": 1,
        "session_id": SESSION,
        "effective_profile_id": "native_claude" if rollover_mode == "operator_restart" else "sol_lead",
        "rollover_warning_percentages": [65.0, 70.0, 75.0],
    }
    if rollover_mode is not None:
        record["rollover_mode"] = rollover_mode
    record_path = tmp_path / "record.json"
    record_path.write_text(json.dumps(record), encoding="utf-8")
    return project, record_path


def _tier_state(project: Path, tier: int, tokens: int) -> None:
    state = project / "batch_state/context_monitor" / f"{SESSION}.tier"
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(f"{tier} {tokens}\n", encoding="utf-8")


def _prepared_rollover(
    project: Path,
    *,
    thread_id: str = SESSION,
    status: str = "pending_start",
    write_handoff: bool = True,
    agent: str = "claude",
) -> Path:
    """A lease as ``thread_handoff.py prepare`` leaves it under the canonical root."""
    lineage = "lineage-" + hashlib.sha256(f"{agent}\0{thread_id}".encode()).hexdigest()[:24]
    handoff = f".agent/thread-rollovers/{agent}/{lineage}/generation-0001/rollover-1/handoff.md"
    lease = project / ".agent/thread-rollovers" / agent / lineage / "lease.json"
    lease.parent.mkdir(parents=True, exist_ok=True)
    lease.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "agent": agent,
                "lineage_id": lineage,
                "active": {"thread_id": thread_id, "generation": 0},
                "replacement": {"status": status, "rollover_id": "rollover-1", "handoff_path": handoff},
            }
        ),
        encoding="utf-8",
    )
    if write_handoff:
        (project / handoff).parent.mkdir(parents=True, exist_ok=True)
        (project / handoff).write_text("# Handoff\n", encoding="utf-8")
    return lease


def _transcript(tmp_path: Path, tokens: int) -> Path:
    path = tmp_path / "transcript.jsonl"
    path.write_text(
        json.dumps(
            {
                "type": "assistant",
                "message": {"usage": {"input_tokens": tokens, "output_tokens": 50_000}},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _run(
    project: Path,
    record_path: Path,
    payload: dict[str, object],
    **extra_env: str,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    for name in (
        "CLAUDE_NON_INTERACTIVE",
        "LEARN_UK_PIPELINE",
        "LEARN_UKRAINIAN_PIPELINE",
        "GEMINI_SESSION",
        "GROK_AGENT",
        "CODEX_THREAD_ID",
        "CODEX_SESSION_ID",
        "SESSION_HANDOFF_AGENT",
        "LEARN_UKRAINIAN_DISPATCH_TASK_ID",
        "LEARN_UKRAINIAN_ROLLOVER_MODE",
        "LEARN_UKRAINIAN_SESSION_ID",
        "CODEX_CANONICAL_REPO_ROOT",
    ):
        env.pop(name, None)
    env.update(
        {
            "CLAUDE_PROJECT_DIR": os.fspath(project),
            "LEARN_UKRAINIAN_SESSION_RECORD": os.fspath(record_path),
            **extra_env,
        }
    )
    return subprocess.run(
        [os.fspath(GUARD)],
        input=json.dumps({"session_id": SESSION, **payload}),
        text=True,
        capture_output=True,
        check=False,
        cwd=project,
        env=env,
        timeout=30,
    )


def _reminder(completed: subprocess.CompletedProcess[str]) -> str:
    assert completed.returncode == 0, completed.stderr
    if not completed.stdout.strip():
        return ""
    output = json.loads(completed.stdout)["hookSpecificOutput"]
    assert output["hookEventName"] == "UserPromptSubmit"
    return output["additionalContext"]


def test_reminder_only_after_tier_three(tmp_path: Path) -> None:
    project, record_path = _project(tmp_path)
    transcript = _transcript(tmp_path, 760_000)
    payload = {"hook_event_name": "UserPromptSubmit", "transcript_path": os.fspath(transcript)}

    assert _reminder(_run(project, record_path, payload)) == ""  # no tier yet
    _tier_state(project, 2, 705_000)
    assert _reminder(_run(project, record_path, payload)) == ""  # tier 2 is not the handoff

    _tier_state(project, 3, 755_000)
    first = _reminder(_run(project, record_path, payload))
    second = _reminder(_run(project, record_path, payload))

    assert first == second  # every later prompt carries the same short reminder
    assert "above this session's final rollover tier (~760k tokens)" in first
    assert "Only answer briefly; do not start new work or dispatches." in first
    assert "tell the operator to restart the session" in first


def test_reminder_is_silent_after_a_manual_compaction_drop(tmp_path: Path) -> None:
    project, record_path = _project(tmp_path)
    _tier_state(project, 3, 760_000)
    transcript = _transcript(tmp_path, 120_000)

    completed = _run(
        project,
        record_path,
        {"hook_event_name": "UserPromptSubmit", "transcript_path": os.fspath(transcript)},
    )

    assert _reminder(completed) == ""


@pytest.mark.parametrize("rollover_mode", ["continuation", None])
def test_reminder_never_fires_for_continuation_profiles(tmp_path: Path, rollover_mode: str | None) -> None:
    project, record_path = _project(tmp_path, rollover_mode=rollover_mode)
    _tier_state(project, 3, 760_000)

    completed = _run(project, record_path, {"hook_event_name": "UserPromptSubmit"})

    assert _reminder(completed) == ""


def test_precompact_auto_is_blocked_only_with_this_sessions_prepared_handoff(tmp_path: Path) -> None:
    project, record_path = _project(tmp_path)
    _prepared_rollover(project)

    completed = _run(project, record_path, {"hook_event_name": "PreCompact", "trigger": "auto"})

    assert completed.returncode == 2
    assert completed.stdout == ""
    assert "Automatic compaction is blocked for this session" in completed.stderr
    assert "its rollover handoff is prepared" in completed.stderr
    assert "Manual /compact remains available" in completed.stderr


def _assert_compaction_runs(completed: subprocess.CompletedProcess[str]) -> None:
    assert (completed.returncode, completed.stdout, completed.stderr) == (0, "", "")


def test_precompact_auto_runs_without_any_handoff_or_tier_marker(tmp_path: Path) -> None:
    """Review probe 1: operator_restart with neither a handoff nor a tier marker."""
    project, record_path = _project(tmp_path)

    _assert_compaction_runs(_run(project, record_path, {"hook_event_name": "PreCompact", "trigger": "auto"}))


def test_precompact_auto_runs_when_the_record_is_missing_despite_env_mode(tmp_path: Path) -> None:
    """Review probe 2: no session record plus LEARN_UKRAINIAN_ROLLOVER_MODE=operator_restart.
    The environment is not a session record, so the guard does nothing."""
    project, record_path = _project(tmp_path)
    record_path.unlink()
    _prepared_rollover(project)

    for event in ("PreCompact", "UserPromptSubmit"):
        _tier_state(project, 3, 760_000)
        completed = _run(
            project,
            tmp_path / "missing-record.json",
            {"hook_event_name": event, "trigger": "auto"},
            LEARN_UKRAINIAN_ROLLOVER_MODE="operator_restart",
            CODEX_CANONICAL_REPO_ROOT=os.fspath(project),
        )
        _assert_compaction_runs(completed)


def test_precompact_auto_runs_when_the_record_names_another_session(tmp_path: Path) -> None:
    project, record_path = _project(tmp_path)
    record = json.loads(record_path.read_text(encoding="utf-8"))
    record["session_id"] = "another-session"
    record_path.write_text(json.dumps(record), encoding="utf-8")
    _prepared_rollover(project)

    _assert_compaction_runs(_run(project, record_path, {"hook_event_name": "PreCompact", "trigger": "auto"}))


def test_precompact_auto_runs_when_the_record_is_unreadable(tmp_path: Path) -> None:
    project, record_path = _project(tmp_path)
    record_path.write_text("{not json", encoding="utf-8")
    _prepared_rollover(project)

    _assert_compaction_runs(_run(project, record_path, {"hook_event_name": "PreCompact", "trigger": "auto"}))


@pytest.mark.parametrize(
    "rollover",
    [
        {"thread_id": "another-session"},  # another session's packet
        {"status": "resumed"},  # already taken over by its replacement
        {"status": "superseded"},
        {"write_handoff": False},  # lease without a usable handoff
    ],
)
def test_precompact_auto_runs_without_a_usable_prepared_handoff_for_this_session(
    tmp_path: Path, rollover: dict[str, object]
) -> None:
    project, record_path = _project(tmp_path)
    _tier_state(project, 3, 760_000)  # a tier announcement alone is not a handoff
    _prepared_rollover(project, **rollover)

    _assert_compaction_runs(_run(project, record_path, {"hook_event_name": "PreCompact", "trigger": "auto"}))


def test_precompact_auto_runs_when_the_rollover_state_is_unreadable(tmp_path: Path) -> None:
    project, record_path = _project(tmp_path)
    lease = _prepared_rollover(project)
    lease.write_text("{truncated", encoding="utf-8")

    _assert_compaction_runs(_run(project, record_path, {"hook_event_name": "PreCompact", "trigger": "auto"}))


def test_precompact_manual_is_allowed(tmp_path: Path) -> None:
    project, record_path = _project(tmp_path)
    _prepared_rollover(project)

    completed = _run(project, record_path, {"hook_event_name": "PreCompact", "trigger": "manual"})

    _assert_compaction_runs(completed)


@pytest.mark.parametrize(
    ("rollover_mode", "extra_env"),
    [
        ("continuation", {}),
        (None, {}),
        ("operator_restart", {"LEARN_UKRAINIAN_DISPATCH_TASK_ID": "impl-1"}),
        ("operator_restart", {"CLAUDE_NON_INTERACTIVE": "1"}),
        ("operator_restart", {"SESSION_HANDOFF_AGENT": "codex"}),
        ("operator_restart", {"GROK_AGENT": "1"}),
    ],
)
def test_precompact_auto_is_untouched_outside_interactive_operator_restart(
    tmp_path: Path, rollover_mode: str | None, extra_env: dict[str, str]
) -> None:
    project, record_path = _project(tmp_path, rollover_mode=rollover_mode)
    _prepared_rollover(project)

    completed = _run(project, record_path, {"hook_event_name": "PreCompact", "trigger": "auto"}, **extra_env)

    _assert_compaction_runs(completed)


def test_settings_register_guard_for_prompts_and_auto_compaction_only() -> None:
    hooks = json.loads(SETTINGS.read_text(encoding="utf-8"))["hooks"]
    command = "$CLAUDE_PROJECT_DIR/.claude/hooks/context-rollover-guard.sh"

    precompact = hooks["PreCompact"]
    assert [group.get("matcher") for group in precompact] == ["auto"]
    assert [hook["command"] for hook in precompact[0]["hooks"]] == [command]
    prompt_commands = [hook["command"] for group in hooks["UserPromptSubmit"] for hook in group["hooks"]]
    assert command in prompt_commands


@pytest.mark.parametrize("script", [GUARD, LIB])
def test_guard_scripts_are_executable_bash(script: Path) -> None:
    assert os.access(script, os.X_OK)
    completed = subprocess.run(
        ["bash", "-n", os.fspath(script)], text=True, capture_output=True, check=False, timeout=30
    )
    assert completed.returncode == 0, completed.stderr
