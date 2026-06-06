from __future__ import annotations

import json
from pathlib import Path

from scripts.orchestration import orchestrator_control as oc


def _option(command: list[str], name: str) -> str:
    return command[command.index(name) + 1]


def _write_task(repo_root: Path, task_id: str, payload: dict) -> Path:
    path = oc.task_state_path(oc.tasks_dir(repo_root), task_id)
    oc.write_json_atomic(path, {"task_id": task_id, **payload})
    return path


def test_start_run_and_add_existing_task(tmp_path: Path, capsys):
    _write_task(tmp_path, "worker-1", {"agent": "codex", "status": "running"})

    rc = oc.main(
        [
            "--repo-root",
            str(tmp_path),
            "start-run",
            "--run-id",
            "a1-policy",
            "--description",
            "A1 policy slice",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert payload["run_id"] == "a1-policy"

    rc = oc.main(
        [
            "--repo-root",
            str(tmp_path),
            "add-task",
            "--run-id",
            "a1-policy",
            "--task-id",
            "worker-1",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert payload["agent"] == "codex"
    state = oc.load_run_state(tmp_path, "a1-policy")
    assert state is not None
    assert state["tasks"][0]["task_id"] == "worker-1"


def test_inbox_markdown_includes_result_excerpt_and_pr_attention(tmp_path: Path, capsys):
    result_path = tmp_path / "batch_state" / "tasks" / "worker-2.result"
    result_path.parent.mkdir(parents=True)
    result_path.write_text(
        "Opened draft PR: https://github.com/org/repo/pull/42\n\nSummary text.",
        encoding="utf-8",
    )
    _write_task(
        tmp_path,
        "worker-2",
        {
            "agent": "codex",
            "status": "done",
            "started_at": "2026-06-06T10:00:00Z",
            "duration_s": 12.5,
            "result_file": str(result_path),
            "worktree_path": str(tmp_path / ".worktrees/dispatch/codex/worker-2"),
        },
    )
    oc.record_task(tmp_path, "a1-policy", task_id="worker-2", agent="codex")

    rc = oc.main(
        [
            "--repo-root",
            str(tmp_path),
            "inbox",
            "--run-id",
            "a1-policy",
            "--include-results",
        ]
    )
    output = capsys.readouterr().out

    assert rc == 0
    assert "# Orchestrator Worker Inbox" in output
    assert "worker-2" in output
    assert "#42" in output
    assert "pr_ready_for_review" in output
    assert "Summary text." in output


def test_inbox_json_reports_missing_recorded_task(tmp_path: Path, capsys):
    oc.record_task(tmp_path, "a1-policy", task_id="missing-worker", agent="codex")

    rc = oc.main(
        [
            "--repo-root",
            str(tmp_path),
            "inbox",
            "--run-id",
            "a1-policy",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert payload["missing"] == [{"task_id": "missing-worker", "reason": "delegate state not found"}]
    assert payload["tasks"][0]["status"] == "missing"


def test_dispatch_dry_run_builds_delegate_command(tmp_path: Path, capsys):
    prompt = tmp_path / "prompt.md"
    prompt.write_text("Do the worker task.", encoding="utf-8")

    rc = oc.main(
        [
            "--repo-root",
            str(tmp_path),
            "dispatch",
            "--run-id",
            "a1-policy",
            "--task-id",
            "worker-3",
            "--agent",
            "codex",
            "--mode",
            "danger",
            "--worktree",
            "--prompt-file",
            str(prompt),
            "--dry-run",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    command = payload["command"]

    assert rc == 0
    assert command[:3] == [".venv/bin/python", "scripts/delegate.py", "dispatch"]
    assert _option(command, "--agent") == "codex"
    assert _option(command, "--task-id") == "worker-3"
    assert _option(command, "--mode") == "danger"
    assert _option(command, "--prompt-file") == str(prompt)
    assert "--worktree" in command
    assert _option(command, "--base") == "main"
    assert not oc.run_state_path(tmp_path, "a1-policy").exists()
