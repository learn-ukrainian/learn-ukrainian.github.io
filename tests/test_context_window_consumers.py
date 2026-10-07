"""Executable regressions for statusline and context-warning capacity consumers."""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATUSLINE = PROJECT_ROOT / "agents_extensions/shared/statusline/statusline.sh"
GEMINI_STATUSLINE = (
    PROJECT_ROOT / "agents_extensions/gemini/statusline/statusline.sh"
)
SUBAGENT_STATUSLINE = (
    PROJECT_ROOT / "agents_extensions/shared/statusline/subagent-statusline.sh"
)
CONTEXT_MONITOR = PROJECT_ROOT / "agents_extensions/shared/hooks/context-monitor.sh"
CODEX_HOOKS = PROJECT_ROOT / "agents_extensions/codex/hooks.json"


def _record(*, actual_window: int | None = 272_000) -> dict[str, object]:
    return {
        "schema_version": 1,
        "session_id": "status-session",
        "effective_profile_id": "sol_lead" if actual_window else "fallback",
        "effective_model_id": "gpt-5.6-sol" if actual_window else "unknown",
        "effective_context_window_tokens": 272_000 if actual_window else 0,
        "expected_model_id": "gpt-5.6-sol" if actual_window else None,
        "expected_context_window_tokens": 272_000 if actual_window else None,
        "observed_model_id": "gpt-5.6-sol",
        "observed_context_window_tokens": None,
        "actual_context_window_tokens": actual_window,
        "actual_context_window_provenance": (
            "declared-profile" if actual_window else "unavailable"
        ),
        "model_mismatch": False,
        "window_mismatch": False,
        "rollover_warning_percentages": [75.0, 85.0, 92.0],
    }


def _fake_project(tmp_path: Path, record: dict[str, object]) -> tuple[Path, Path]:
    project = tmp_path / "project"
    python_bin = project / ".venv/bin/python"
    session_helper = project / "scripts/lib/session_record.py"
    record_path = tmp_path / "record.json"
    record_path.write_text(json.dumps(record), encoding="utf-8")
    session_helper.parent.mkdir(parents=True)
    session_helper.write_text("# fake helper selected by fake python\n", encoding="utf-8")
    python_bin.parent.mkdir(parents=True)
    python_bin.write_text(
        """#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

record_path = Path(os.environ["TEST_SESSION_RECORD"])
record = json.loads(record_path.read_text(encoding="utf-8"))
command = sys.argv[2]
args = sys.argv[3:]
if command == "get":
    print(json.dumps(record))
    raise SystemExit(0)
if command != "update":
    raise SystemExit(2)

def value(flag):
    return args[args.index(flag) + 1] if flag in args else None

model = value("--observed-model")
window = value("--observed-context-window")
transcript = value("--transcript-path")
if model is not None:
    record["observed_model_id"] = model
    record["model_mismatch"] = model != record.get("expected_model_id")
if window is not None:
    observed = int(window)
    record["observed_context_window_tokens"] = observed
    record["actual_context_window_tokens"] = observed
    record["actual_context_window_provenance"] = value(
        "--observed-context-window-provenance"
    )
    record["window_mismatch"] = observed != record.get(
        "expected_context_window_tokens"
    )
if transcript is not None:
    record["transcript_path"] = transcript
record_path.write_text(json.dumps(record), encoding="utf-8")
print(json.dumps(record))
""",
        encoding="utf-8",
    )
    python_bin.chmod(0o755)
    return project, record_path


def _environment(project: Path, record_path: Path) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "CLAUDE_PROJECT_DIR": os.fspath(project),
            "TEST_SESSION_RECORD": os.fspath(record_path),
            # context-monitor.sh no longer spawns python for the session
            # record (perf(hooks) #6414) — it reads the record file directly
            # with jq, via this override or its canonical
            # .agent/sessions/<id>.json default. statusline.sh (still python-
            # backed) keeps using TEST_SESSION_RECORD/the fake .venv python
            # above, so both fixtures point at the same on-disk record.
            "LEARN_UKRAINIAN_SESSION_RECORD": os.fspath(record_path),
            "THREAD_ROLLOVER_PYTHON": sys.executable,
        }
    )
    for name in (
        "CLAUDE_NON_INTERACTIVE",
        "LEARN_UK_PIPELINE",
        "GEMINI_SESSION",
        "CODEX_THREAD_ID",
        "CODEX_SESSION_ID",
        "SESSION_HANDOFF_AGENT",
        "SESSION_EPIC",
        "LEARN_UKRAINIAN_DISPATCH_TASK_ID",
        "LEARN_UKRAINIAN_ROLLOVER_MODE",
    ):
        env.pop(name, None)
    return env


def _native_claude_record() -> dict[str, object]:
    """The native_claude profile as SessionStart records it (#8511)."""
    record = _record(actual_window=1_000_000)
    record.update(
        {
            "effective_profile_id": "native_claude",
            "effective_model_id": "claude-native-family",
            "rollover_warning_percentages": [65.0, 70.0, 75.0],
            "rollover_mode": "operator_restart",
        }
    )
    return record


def _write_transcript(path: Path, *, input_tokens: int, cache_tokens: int) -> None:
    path.write_text(
        json.dumps(
            {
                "type": "assistant",
                "message": {
                    "usage": {
                        "input_tokens": input_tokens,
                        "cache_read_input_tokens": cache_tokens,
                        "cache_creation_input_tokens": 0,
                        "output_tokens": 999_999,
                    }
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )


def test_statusline_prefers_official_usage_and_observed_capacity(tmp_path: Path) -> None:
    project, record_path = _fake_project(tmp_path, _record())
    transcript = tmp_path / "official transcript.jsonl"
    _write_transcript(transcript, input_tokens=10, cache_tokens=5)
    payload = {
        "session_id": "status-session",
        "transcript_path": os.fspath(transcript),
        "model": {"id": "gpt-5.6-sol", "display_name": "GPT-5.6 Sol"},
        "workspace": {"current_dir": os.fspath(tmp_path)},
        "context_window": {
            "context_window_size": 260_000,
            "total_input_tokens": 130_000,
            "current_usage": {
                "input_tokens": 1,
                "cache_read_input_tokens": 2,
                "output_tokens": 999_999,
            },
        },
    }

    completed = subprocess.run(
        [os.fspath(STATUSLINE)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=True,
        cwd=tmp_path,
        env=_environment(project, record_path),
        timeout=30
    )

    assert "[ctx: 130K/260K (50%)]" in completed.stdout
    assert "MISMATCH WINDOW: 260000 vs 272000" in completed.stdout
    assert "999999" not in completed.stdout
    persisted = json.loads(record_path.read_text(encoding="utf-8"))
    assert persisted["actual_context_window_tokens"] == 260_000
    assert persisted["actual_context_window_provenance"] == (
        "statusline.context_window.context_window_size"
    )
    assert persisted["transcript_path"] == os.fspath(transcript)


def test_statusline_unknown_capacity_does_not_use_auto_compact_fallback(
    tmp_path: Path,
) -> None:
    project, record_path = _fake_project(tmp_path, _record(actual_window=None))
    payload = {
        "session_id": "status-session",
        "model": {"id": "unknown-model"},
        "workspace": {"current_dir": os.fspath(tmp_path)},
        "context_window": {"total_input_tokens": 180_000},
    }
    env = _environment(project, record_path)
    env["CLAUDE_CODE_AUTO_COMPACT_WINDOW"] = "1000000"

    completed = subprocess.run(
        [os.fspath(STATUSLINE)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=True,
        cwd=tmp_path,
        env=env,
        timeout=30
    )

    assert "[ctx:" not in completed.stdout
    assert "1000K" not in completed.stdout


def test_subagent_statusline_reports_progress_and_tokens(tmp_path: Path) -> None:
    payload = {
        "columns": 120,
        "tasks": [
            {
                "id": "task-1",
                "name": "repo-map",
                "status": "running",
                "description": "Trace launcher configuration",
                "tokenCount": 12_345,
            },
            {
                "id": "task-2",
                "label": "tests",
                "status": "completed",
                "tokenCount": 980,
            },
        ],
    }

    completed = subprocess.run(
        [os.fspath(SUBAGENT_STATUSLINE)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=True,
        cwd=tmp_path,
        timeout=30
    )

    rows = [json.loads(line) for line in completed.stdout.splitlines()]
    assert rows == [
        {
            "id": "task-1",
            "content": "[running] repo-map: Trace launcher configuration · 12K tok",
        },
        {"id": "task-2", "content": "[completed] tests · 980 tok"},
    ]


def test_context_monitor_uses_record_tiers_and_excludes_output_tokens(
    tmp_path: Path,
) -> None:
    project, record_path = _fake_project(tmp_path, _record(actual_window=360_000))
    transcript = tmp_path / "monitor.jsonl"
    _write_transcript(transcript, input_tokens=300_000, cache_tokens=6_000)
    payload = {
        "session_id": "status-session",
        "transcript_path": os.fspath(transcript),
    }

    completed = subprocess.run(
        [os.fspath(CONTEXT_MONITOR)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=True,
        cwd=tmp_path,
        env=_environment(project, record_path),
        timeout=30
    )

    hook_output = json.loads(completed.stdout)
    message = hook_output["hookSpecificOutput"]["additionalContext"]
    assert message.startswith("CRITICAL: Context is at 85%")
    assert "360000-token context window" in message
    assert "latest assistant input/cache usage" in message
    assert "auto-compact window" not in message
    assert "999999" not in message


def test_context_monitor_size_fallback_handles_long_base64_portably(
    tmp_path: Path,
) -> None:
    project, record_path = _fake_project(tmp_path, _record(actual_window=100))
    transcript = tmp_path / "monitor-without-usage.jsonl"
    transcript.write_text(
        json.dumps(
            {
                "type": "user",
                "message": {"content": ("word " * 200) + ("A" * 900)},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    payload = {
        "session_id": "status-session",
        "transcript_path": os.fspath(transcript),
    }

    completed = subprocess.run(
        [os.fspath(CONTEXT_MONITOR)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=True,
        cwd=tmp_path,
        env=_environment(project, record_path),
        timeout=30
    )

    hook_output = json.loads(completed.stdout)
    message = hook_output["hookSpecificOutput"]["additionalContext"]
    assert message.startswith("EMERGENCY: Context is at")
    assert "transcript-size estimate" in message
    assert "sed -E 's#[A-Za-z0-9+/]{800,}" not in CONTEXT_MONITOR.read_text(
        encoding="utf-8"
    )


def test_context_monitor_unknown_capacity_emits_no_warning(tmp_path: Path) -> None:
    project, record_path = _fake_project(tmp_path, _record(actual_window=None))
    transcript = tmp_path / "monitor.jsonl"
    _write_transcript(transcript, input_tokens=300_000, cache_tokens=6_000)
    payload = {
        "session_id": "status-session",
        "transcript_path": os.fspath(transcript),
    }

    completed = subprocess.run(
        [os.fspath(CONTEXT_MONITOR)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=True,
        cwd=tmp_path,
        env=_environment(project, record_path),
        timeout=30
    )

    assert completed.stdout == ""


@pytest.mark.parametrize(
    ("identity_env", "value"),
    [
        ("SESSION_HANDOFF_AGENT", "codex"),
        ("CODEX_THREAD_ID", "codex-thread"),
        ("CODEX_SESSION_ID", "codex-session"),
    ],
)
def test_context_monitor_is_silent_for_native_codex(
    tmp_path: Path,
    identity_env: str,
    value: str,
) -> None:
    project, record_path = _fake_project(tmp_path, _record(actual_window=100))
    transcript = tmp_path / "monitor.jsonl"
    _write_transcript(transcript, input_tokens=100, cache_tokens=0)
    payload = {
        "session_id": "status-session",
        "transcript_path": os.fspath(transcript),
    }
    env = _environment(project, record_path)
    env[identity_env] = value

    completed = subprocess.run(
        [os.fspath(CONTEXT_MONITOR)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=True,
        cwd=tmp_path,
        env=env,
        timeout=30,
    )

    assert completed.stdout == ""


def test_context_monitor_is_silent_from_deployed_codex_path(tmp_path: Path) -> None:
    deployed = tmp_path / ".codex" / "hooks" / "context-monitor.sh"
    deployed.parent.mkdir(parents=True)
    shutil.copy2(CONTEXT_MONITOR, deployed)
    env = os.environ.copy()
    for identity_var in (
        "SESSION_HANDOFF_AGENT",
        "CODEX_THREAD_ID",
        "CODEX_SESSION_ID",
    ):
        env.pop(identity_var, None)

    completed = subprocess.run(
        [os.fspath(deployed)],
        input="{}",
        text=True,
        capture_output=True,
        check=True,
        cwd=tmp_path,
        env=env,
        timeout=30,
    )

    assert completed.stdout == ""


def test_codex_hook_ssot_does_not_register_manual_context_monitor() -> None:
    config = json.loads(CODEX_HOOKS.read_text(encoding="utf-8"))
    commands = [
        hook["command"]
        for groups in config["hooks"].values()
        for group in groups
        for hook in group.get("hooks", [])
    ]

    assert all("context-monitor.sh" not in command for command in commands)


@pytest.mark.parametrize("script", [STATUSLINE, GEMINI_STATUSLINE, CONTEXT_MONITOR])
def test_context_consumer_shell_syntax(script: Path) -> None:
    completed = subprocess.run(
        ["bash", "-n", os.fspath(script)],
        text=True,
        capture_output=True,
        check=False,
        timeout=30
    )
    assert completed.returncode == 0, completed.stderr
def test_statusline_reports_steps_compacts_and_handoff_warning(tmp_path: Path) -> None:
    project, record_path = _fake_project(tmp_path, _record())
    transcript = tmp_path / "transcript_test.jsonl"
    lines = []
    for i in range(75):
        lines.append(json.dumps({"type": "user", "step_index": i}))
    lines.append(json.dumps({"type": "system", "subtype": "compact"}))
    lines.append(json.dumps({"type": "system", "subtype": "compact"}))
    transcript.write_text("\n".join(lines) + "\n", encoding="utf-8")

    payload = {
        "session_id": "status-session",
        "transcript_path": os.fspath(transcript),
        "model": {"id": "gpt-5.6-sol", "display_name": "GPT-5.6 Sol"},
        "workspace": {"current_dir": os.fspath(tmp_path)},
        "context_window": {
            "context_window_size": 260_000,
            "total_input_tokens": 50_000,
        },
    }

    completed = subprocess.run(
        [os.fspath(STATUSLINE)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=True,
        cwd=tmp_path,
        env=_environment(project, record_path),
        timeout=30
    )

    assert "[steps: 77]" in completed.stdout
    assert "[compacts: 2]" in completed.stdout


def test_statusline_prefer_handoff_over_compaction(tmp_path: Path) -> None:
    project, record_path = _fake_project(tmp_path, _record())
    transcript = tmp_path / "transcript_test.jsonl"
    lines = [
        json.dumps({"type": "user", "step_index": 1}),
        json.dumps({"type": "system", "subtype": "compact"}),
    ]
    transcript.write_text("\n".join(lines) + "\n", encoding="utf-8")

    payload = {
        "session_id": "status-session",
        "transcript_path": os.fspath(transcript),
        "model": {"id": "gpt-5.6-sol", "display_name": "GPT-5.6 Sol"},
        "workspace": {"current_dir": os.fspath(tmp_path)},
        "context_window": {
            "context_window_size": 260_000,
            "total_input_tokens": 50_000,
        },
    }

    completed = subprocess.run(
        [os.fspath(STATUSLINE)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=True,
        cwd=tmp_path,
        env=_environment(project, record_path),
        timeout=30
    )

    assert "[compacts: 1]" in completed.stdout
    assert "HANDOFF SUGGESTED" in completed.stdout


def test_context_monitor_announces_each_tier_once_and_rearms_after_compaction(
    tmp_path: Path,
) -> None:
    """Tier warnings are monotonic per session: a repeat, a dip-and-rise around a
    boundary, or a lower tier stays silent; a strictly higher tier announces; only a
    compaction-scale drop (below 60% of the last announced usage) re-arms."""
    project, record_path = _fake_project(tmp_path, _record(actual_window=360_000))
    transcript = tmp_path / "monitor.jsonl"
    payload = json.dumps(
        {"session_id": "status-session", "transcript_path": os.fspath(transcript)}
    )
    state_file = project / "batch_state/context_monitor/status-session.tier"

    def run(input_tokens: int) -> str:
        _write_transcript(transcript, input_tokens=input_tokens, cache_tokens=0)
        completed = subprocess.run(
            [os.fspath(CONTEXT_MONITOR)],
            input=payload,
            text=True,
            capture_output=True,
            check=True,
            cwd=tmp_path,
            env=_environment(project, record_path),
            timeout=30,
        )
        if not completed.stdout.strip():
            return ""
        return json.loads(completed.stdout)["hookSpecificOutput"]["additionalContext"]

    assert run(306_000).startswith("CRITICAL: Context is at 85%")  # tier 2 announced
    assert state_file.read_text(encoding="utf-8").split() == ["2", "306000"]
    assert run(306_000) == ""  # same tier: silent
    assert run(266_000) == ""  # dip below tier 1
    assert run(288_000) == ""  # rise back to tier 1 (< announced tier 2): silent
    assert run(335_000).startswith("EMERGENCY: Context is at 93%")  # tier 3 announced
    assert run(108_000) == ""  # compaction-scale drop: re-arms, nothing to announce
    assert not state_file.exists()
    assert run(288_000).startswith("HEADS UP: Context is at 80%")  # fresh climb announces
    assert state_file.read_text(encoding="utf-8").split() == ["1", "288000"]


def _monitor(
    project: Path,
    record_path: Path,
    transcript: Path,
    tokens: int,
    **extra_env: str,
) -> str:
    _write_transcript(transcript, input_tokens=tokens, cache_tokens=0)
    env = _environment(project, record_path)
    env.update(extra_env)
    completed = subprocess.run(
        [os.fspath(CONTEXT_MONITOR)],
        input=json.dumps({"session_id": "status-session", "transcript_path": os.fspath(transcript)}),
        text=True,
        capture_output=True,
        check=True,
        cwd=project.parent,
        env=env,
        timeout=30,
    )
    if not completed.stdout.strip():
        return ""
    return json.loads(completed.stdout)["hookSpecificOutput"]["additionalContext"]


def test_context_monitor_operator_restart_tiers_hand_off_and_wait(tmp_path: Path) -> None:
    """#8511: 650k/700k warnings, and at 750k hand off, tell the operator, end the turn."""
    project, record_path = _fake_project(tmp_path, _native_claude_record())
    transcript = tmp_path / "native.jsonl"

    assert _monitor(project, record_path, transcript, 640_000) == ""

    heads_up = _monitor(project, record_path, transcript, 655_000)
    assert heads_up.startswith("HEADS UP: Context is at 65%")

    critical = _monitor(project, record_path, transcript, 705_000)
    assert critical.startswith("CRITICAL: Context is at 70%")
    assert "Finish the current logical unit" in critical
    assert "tells the operator it is ready for a restart, and waits" in critical
    assert "Start the supported continuation" not in critical

    emergency = _monitor(project, record_path, transcript, 760_000)
    assert emergency.startswith("EMERGENCY: Context is at 76%")
    assert "waits for the operator to restart it" in emergency
    assert "Refresh your lane handoff file" in emergency
    assert "thread-rollover skill's prepare phase (references/prepare.md)" in emergency
    # The fake project has no interpreter helper: an honest placeholder, never
    # a checkout-relative .venv path that a worktree does not have.
    assert (
        "run <project interpreter> scripts/orchestration/thread_handoff.py prepare"
        " --agent claude --harness claude-code --active-thread-id status-session --stream-epic <epic-number>"
        ' --semantic-title "<specific semantic task title>" --task-family <task-family> --role "<role>"'
        " --terminal-goal <merge|deploy|certify> --context-percent 76"
    ) in emergency
    assert ".venv/bin/python" not in emergency
    assert "handoff and bootstrap packet under .agent/thread-rollovers/" in emergency
    assert "-thread-handoff.md" not in emergency  # prepare writes no lane-root handoff
    assert "Tell the operator in one plain message" in emergency
    assert "END THE TURN and wait for the operator to restart the session" in emergency
    # Nothing blocks auto-compaction (#9790), so the text must not claim it.
    assert "Claude Code may still compact it automatically near its own limit" in emergency
    assert "compaction is blocked" not in emergency
    assert "Start the supported continuation" not in emergency
    assert "start-claude-driver.sh" not in emergency  # launcher unknown: not invented

    # Tier 3 is announced on first crossing; a later sequential call stays silent.
    state_file = project / "batch_state/context_monitor/status-session.tier"
    assert state_file.read_text(encoding="utf-8") == "3 760000\n"
    assert _monitor(project, record_path, transcript, 780_000) == ""
    assert state_file.read_text(encoding="utf-8") == "3 760000\n"


def test_context_monitor_operator_restart_names_driver_launcher(tmp_path: Path) -> None:
    project, record_path = _fake_project(tmp_path, _native_claude_record())

    emergency = _monitor(project, record_path, tmp_path / "native.jsonl", 760_000, SESSION_EPIC="infra")

    assert "restart this session (./start-claude-driver.sh --epic infra)." in emergency


def test_context_monitor_dispatched_worker_keeps_continuation_text(tmp_path: Path) -> None:
    """A delegated worker has no operator to restart it, so it never waits for one."""
    project, record_path = _fake_project(tmp_path, _native_claude_record())

    emergency = _monitor(
        project,
        record_path,
        tmp_path / "native.jsonl",
        760_000,
        LEARN_UKRAINIAN_DISPATCH_TASK_ID="impl-1",
    )

    assert emergency.startswith("EMERGENCY: Context is at 76%")
    assert "Start the supported continuation" in emergency
    assert "END THE TURN" not in emergency


def test_context_monitor_other_profiles_keep_continuation_text(tmp_path: Path) -> None:
    project, record_path = _fake_project(tmp_path, _record(actual_window=360_000))

    emergency = _monitor(project, record_path, tmp_path / "sol.jsonl", 335_000)

    assert emergency.startswith("EMERGENCY: Context is at 93%")
    assert "Start the supported continuation" in emergency
    assert "END THE TURN" not in emergency


def test_context_monitor_ignores_operator_restart_from_another_sessions_record(tmp_path: Path) -> None:
    """The mode binds to this session only, as in context-rollover-guard.sh: a
    foreign record's operator_restart yields the continuation text."""
    record = _native_claude_record()
    record["session_id"] = "another-session"
    project, record_path = _fake_project(tmp_path, record)

    emergency = _monitor(project, record_path, tmp_path / "native.jsonl", 760_000)

    assert emergency.startswith("EMERGENCY: Context is at 76%")
    assert "Start the supported continuation" in emergency
    assert "waits for the operator to restart it" not in emergency
    assert "END THE TURN" not in emergency


def test_context_monitor_without_a_record_ignores_env_operator_restart(tmp_path: Path) -> None:
    """No session record: the trusted native_claude profile resolution supplies
    the window and tiers, but never the rollover mode (it resolves to
    operator_restart here), so the continuation text stays."""
    project, _ = _fake_project(tmp_path, _native_claude_record())
    (project / "scripts/lib/profile_resolver.sh").symlink_to(PROJECT_ROOT / "scripts/lib/profile_resolver.sh")

    emergency = _monitor(
        project,
        tmp_path / "missing-record.json",
        tmp_path / "native.jsonl",
        760_000,
        CODEX_CANONICAL_REPO_ROOT=os.fspath(project),
        CLAUDE_PROFILE_RESOLVER_PY=os.fspath(PROJECT_ROOT / "scripts/lib/context_profiles.py"),
        CLAUDE_PROFILE_RESOLVER_PYTHON=sys.executable,
        LEARN_UKRAINIAN_REQUESTED_PROFILE_ID="native_claude",
        LEARN_UKRAINIAN_OBSERVED_MODEL_ID="claude-opus-5-5",
    )

    assert emergency.startswith("EMERGENCY: Context is at 76% of the 1000000-token context window")
    assert "capacity: declared-profile" in emergency
    assert "Start the supported continuation" in emergency
    assert "END THE TURN" not in emergency


def _git(*args: str | os.PathLike[str]) -> None:
    subprocess.run(
        ["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid", *map(os.fspath, args)],
        check=True,
        capture_output=True,
        timeout=60,
    )


def _primary_with_worktree(tmp_path: Path) -> tuple[Path, Path]:
    """A real primary checkout with a linked dispatch worktree, as the fleet runs.
    Only the primary has a .venv; the worktree reaches the repository scripts."""
    primary = tmp_path / "primary"
    primary.mkdir()
    _git("init", "-q", "-b", "main", primary)
    (primary / ".gitignore").write_text(".agent/\n.venv/\n.worktrees/\nbatch_state/\nscripts\n", encoding="utf-8")
    _git("-C", primary, "add", ".gitignore")
    _git("-C", primary, "commit", "-q", "-m", "init")
    worktree = primary / ".worktrees/dispatch/claude/probe"
    _git("-C", primary, "worktree", "add", "-q", "-b", "probe", worktree)
    (worktree / "scripts").symlink_to(PROJECT_ROOT / "scripts", target_is_directory=True)
    interpreter = primary / ".venv/bin/python"
    interpreter.parent.mkdir(parents=True)
    interpreter.write_text(f'#!/bin/sh\nexec {shlex.quote(sys.executable)} "$@"\n', encoding="utf-8")
    interpreter.chmod(0o755)
    return primary.resolve(), worktree.resolve()


def test_context_monitor_prepare_command_runs_from_a_worktree(tmp_path: Path) -> None:
    """#8511 review finding 2: the printed command uses the shared interpreter
    and the runtime identity, runs from a dispatch worktree, and writes this
    session's pending lease into the primary checkout's runtime state."""
    primary, worktree = _primary_with_worktree(tmp_path)
    record_path = tmp_path / "record.json"
    record_path.write_text(json.dumps(_native_claude_record()), encoding="utf-8")
    transcript = tmp_path / "native.jsonl"
    _write_transcript(transcript, input_tokens=760_000, cache_tokens=0)
    env = _environment(worktree, record_path)
    env.pop("THREAD_ROLLOVER_PYTHON", None)
    for name in ("LEARN_UKRAINIAN_SESSION_ID", "CODEX_CANONICAL_REPO_ROOT"):
        env.pop(name, None)

    hook = subprocess.run(
        [os.fspath(CONTEXT_MONITOR)],
        input=json.dumps({"session_id": "status-session", "transcript_path": os.fspath(transcript)}),
        text=True,
        capture_output=True,
        check=True,
        cwd=worktree,
        env=env,
        timeout=60,
    )
    emergency = json.loads(hook.stdout)["hookSpecificOutput"]["additionalContext"]
    match = re.search(r"run (.+?) \(fill each <placeholder>", emergency)
    assert match, emergency
    printed = match.group(1)
    assert printed.startswith(
        f"{primary}/.venv/bin/python scripts/orchestration/thread_handoff.py prepare"
        " --agent claude --harness claude-code --active-thread-id status-session --stream-epic <epic-number>"
    )

    filled = (
        printed.replace("<epic-number>", "8511")
        .replace('"<specific semantic task title>"', '"Probe the rollover command"')
        .replace("<task-family>", "thread-rollover")
        .replace('"<role>"', '"driver"')
        .replace("<merge|deploy|certify>", "merge")
    )
    assert "<" not in filled
    argv = shlex.split(filled)
    # Keep the runtime state in this fixture's primary, not the real checkout.
    argv[2:2] = ["--repo-root", os.fspath(primary)]

    prepare_env = {key: value for key, value in env.items() if not key.startswith("LEARN_UKRAINIAN_SESSION")}
    prepare_env["LU_MONITOR_LOOPBACK"] = "http://127.0.0.1:9"
    prepared = subprocess.run(
        argv, cwd=worktree, env=prepare_env, text=True, capture_output=True, check=False, timeout=120
    )
    assert prepared.returncode == 0, prepared.stdout + prepared.stderr
    leases = list((primary / ".agent/thread-rollovers/claude").glob("*/lease.json"))
    assert len(leases) == 1
    lease = json.loads(leases[0].read_text(encoding="utf-8"))
    assert lease["active"]["thread_id"] == "status-session"
    assert lease["replacement"]["status"] == "pending_start"
    assert lease["replacement"]["title_transition"]["harness"] == "claude-code"
