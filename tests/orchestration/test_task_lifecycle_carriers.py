from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import delegate

from scripts.api import coordination_router
from scripts.orchestration import agent_ledger, orchestrator_control, task_identity, task_lifecycle

NOW = "2026-07-16T10:00:00Z"


def _lifecycle_file(tmp_path: Path) -> Path:
    identity = task_identity.build_identity(
        repository="org/repo",
        stream_epic=10,
        stream_epic_url=None,
        github_issue_number=42,
        github_issue_url=None,
        semantic_title="Enforce task closeout",
        task_family="infrastructure",
        role="implementer",
        predecessor_task_id="thread-old",
        replacement_task_id="thread-new",
        lineage_id="lineage-closeout",
        generation=1,
        terminal_goal="merge",
        lifecycle_state="confirmed",
    )
    body = "- [ ] **AC-IMPL** — Implementation is verified.\n"
    policy = {
        "AC-IMPL": {
            "due_state": "IMPLEMENTATION_READY",
            "required_evidence": ["test"],
        }
    }
    ledger = task_lifecycle.build_lifecycle(
        identity,
        author_family="codex",
        ac_snapshot=task_lifecycle.build_ac_snapshot(body, policy, finalized_at=NOW),
        required_checks=["CI Gate"],
        now=NOW,
    )
    path = tmp_path / "task-lifecycle.json"
    task_lifecycle.write_lifecycle(path, ledger)
    return path


def test_delegate_loads_validated_carrier_and_prompt(tmp_path: Path) -> None:
    path = _lifecycle_file(tmp_path)

    carrier, prompt = delegate._load_task_lifecycle_carrier(str(path))

    assert carrier is not None
    assert carrier["state_file"] == str(path.resolve())
    assert carrier["identity"]["github_issue_number"] == 42
    assert "authoritative carrier" in prompt
    assert carrier["lifecycle_id"] in prompt


def test_agent_ledger_persists_carrier_and_monitor_returns_it(
    tmp_path: Path, monkeypatch
) -> None:
    path = _lifecycle_file(tmp_path)
    task = agent_ledger.upsert_task(
        tmp_path,
        task_id="closeout-worker",
        agent="codex",
        status="running",
        lifecycle_file=path,
    )
    monkeypatch.setattr(coordination_router, "PROJECT_ROOT", tmp_path)

    monitored = asyncio.run(coordination_router.coordination_task("closeout-worker"))

    assert task["task_lifecycle"]["state_file"] == str(path.resolve())
    assert monitored["task_lifecycle"] == task["task_lifecycle"]


def test_orchestrator_forwards_and_retains_lifecycle_carrier(
    tmp_path: Path, capsys
) -> None:
    path = _lifecycle_file(tmp_path)
    prompt = tmp_path / "prompt.md"
    prompt.write_text("Do the worker task.", encoding="utf-8")

    rc = orchestrator_control.main(
        [
            "--repo-root",
            str(tmp_path),
            "dispatch",
            "--run-id",
            "closeout-run",
            "--task-id",
            "closeout-worker",
            "--agent",
            "codex",
            "--prompt-file",
            str(prompt),
            "--lifecycle-file",
            str(path),
            "--dry-run",
        ]
    )
    command = json.loads(capsys.readouterr().out)["command"]

    assert rc == 0
    assert command[command.index("--lifecycle-file") + 1] == str(path.resolve())

    orchestrator_control.record_task(
        tmp_path,
        "closeout-run",
        task_id="closeout-worker",
        agent="codex",
        lifecycle_file=str(path),
    )
    inbox = orchestrator_control.collect_inbox(
        tmp_path,
        run_id="closeout-run",
        recent=20,
        include_results=False,
        include_logs=False,
        max_result_chars=100,
        max_log_chars=100,
    )

    assert inbox["tasks"][0]["status"] == "missing"
    assert inbox["tasks"][0]["task_lifecycle"]["current_state"] == "ISSUE_LINKED"
