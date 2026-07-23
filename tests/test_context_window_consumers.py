"""Executable regressions for statusline and context-warning capacity consumers."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATUSLINE = PROJECT_ROOT / "agents_extensions/shared/statusline/statusline.sh"
SUBAGENT_STATUSLINE = (
    PROJECT_ROOT / "agents_extensions/shared/statusline/subagent-statusline.sh"
)
CONTEXT_MONITOR = PROJECT_ROOT / "agents_extensions/shared/hooks/context-monitor.sh"


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
        }
    )
    for name in (
        "CLAUDE_NON_INTERACTIVE",
        "LEARN_UK_PIPELINE",
        "GEMINI_SESSION",
        "CODEX_THREAD_ID",
        "CODEX_SESSION_ID",
        "SESSION_HANDOFF_AGENT",
    ):
        env.pop(name, None)
    return env


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
    )

    assert completed.stdout == ""


@pytest.mark.parametrize("script", [STATUSLINE, CONTEXT_MONITOR])
def test_context_consumer_shell_syntax(script: Path) -> None:
    completed = subprocess.run(
        ["bash", "-n", os.fspath(script)],
        text=True,
        capture_output=True,
        check=False,
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
    )

    assert "[steps: 77]" in completed.stdout
    assert "[compacts: 2]" in completed.stdout
    assert "HANDOFF SUGGESTED" in completed.stdout

