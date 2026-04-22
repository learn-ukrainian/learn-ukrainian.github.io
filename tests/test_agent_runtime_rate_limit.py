from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime.adapters.claude import ClaudeAdapter
from maintenance.reclassify_dispatch_status import reclassify_rate_limited_tasks


def test_claude_success_text_with_rate_limited_phrase_is_not_rate_limited():
    adapter = ClaudeAdapter()

    result = adapter.parse_response(
        stdout="Done.\nThe previous soft warning said rate limited, but the task completed.",
        stderr="",
        returncode=0,
        output_file=None,
    )

    assert result.rate_limited is False
    assert result.ok is True


def test_claude_stderr_rate_limit_failure_is_still_rate_limited():
    adapter = ClaudeAdapter()

    result = adapter.parse_response(
        stdout="",
        stderr="Error: rate limit reached, try again later.",
        returncode=1,
        output_file=None,
    )

    assert result.rate_limited is True
    assert result.ok is False


def test_claude_empty_stdout_with_stderr_rate_limit_stays_rate_limited():
    adapter = ClaudeAdapter()

    result = adapter.parse_response(
        stdout="",
        stderr="Warning: rate limit reached before any response was returned.",
        returncode=0,
        output_file=None,
    )

    assert result.rate_limited is True
    assert result.ok is False


def test_claude_failed_stdout_rate_limit_phrase_without_stderr_is_not_rate_limited():
    adapter = ClaudeAdapter()

    result = adapter.parse_response(
        stdout="Error: rate limit reached.",
        stderr="",
        returncode=1,
        output_file=None,
    )

    assert result.rate_limited is False
    assert result.ok is False


def test_reclassify_script_flips_historical_claude_false_positive(tmp_path):
    tasks_dir = tmp_path / "batch_state" / "tasks"
    usage_dir = tmp_path / "batch_state" / "api_usage"
    tasks_dir.mkdir(parents=True)
    usage_dir.mkdir(parents=True)

    task_path = tasks_dir / "claude-1370-writer-harden.json"
    task_path.write_text(json.dumps({
        "task_id": "claude-1370-writer-harden",
        "agent": "claude",
        "status": "rate_limited",
        "stderr_excerpt": "claude/claude-opus-4-7 rate limited: Done.",
        "returncode": None,
        "result_file": None,
    }))
    (usage_dir / "usage_claude-delegate_2026-04-22.jsonl").write_text(
        json.dumps({
            "ts": "2026-04-22T12:52:00.090793+00:00",
            "agent": "claude",
            "entrypoint": "delegate",
            "task_id": "claude-1370-writer-harden",
            "model": "claude-opus-4-7",
            "returncode": 0,
            "outcome": "rate_limited",
            "rate_limited": True,
            "stderr_excerpt": (
                "Done.\n\n**Delivered:** soft warning said rate limited, "
                "but work finished."
            ),
        }) + "\n"
    )

    changes = reclassify_rate_limited_tasks(tasks_dir=tasks_dir, usage_dir=usage_dir)

    assert changes["changed"] == [
        (
            "claude-1370-writer-harden",
            "rate_limited -> done (backup: claude-1370-writer-harden.json.bak)",
        )
    ]
    assert changes["skipped"] == []
    updated = json.loads(task_path.read_text())
    assert updated["status"] == "done"
    assert updated["stderr_excerpt"] == "claude/claude-opus-4-7 rate limited: Done."
    assert (tasks_dir / "claude-1370-writer-harden.json.bak").exists()
