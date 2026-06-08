from __future__ import annotations

import asyncio
import json
import threading
from pathlib import Path

import pytest
from fastapi import HTTPException

from scripts.api import coordination_router
from scripts.orchestration import agent_ledger


def test_upsert_task_records_parallel_agent_metadata(tmp_path: Path):
    task = agent_ledger.upsert_task(
        tmp_path,
        task_id="2823-ui-worker",
        agent="codex",
        status="running",
        issue=2823,
        lane="ui",
        module_family="site",
        task_family="design",
        model="gpt-5.4",
        thread_id="thread-1",
        branch="codex/2823-lightweight-ui",
        worktree=".worktrees/dispatch/codex/2823-lightweight-ui",
        owned_paths=["starlight/src/pages", "starlight/src/styles/course.css"],
    )

    assert task["issue"] == 2823
    assert task["task_family"] == "design"
    assert task["owned_paths"] == ["starlight/src/pages", "starlight/src/styles/course.css"]
    assert task["events"][0]["type"] == "created"

    path = agent_ledger.task_path(tmp_path, "2823-ui-worker")
    assert json.loads(path.read_text(encoding="utf-8"))["thread_id"] == "thread-1"


def test_active_owned_path_conflict_is_blocked(tmp_path: Path):
    agent_ledger.upsert_task(
        tmp_path,
        task_id="a1-worker",
        agent="codex",
        status="running",
        task_family="content_writing",
        owned_paths=["curriculum/l2-uk-en/a1"],
    )

    try:
        agent_ledger.upsert_task(
            tmp_path,
            task_id="a1-m8-worker",
            agent="gemini",
            status="running",
            task_family="code_review",
            owned_paths=["curriculum/l2-uk-en/a1/things-have-gender/module.md"],
        )
    except agent_ledger.OwnershipConflictError as exc:
        assert exc.conflicts[0]["task_id"] == "a1-worker"
        assert exc.conflicts[0]["owned_path"] == "curriculum/l2-uk-en/a1"
    else:
        raise AssertionError("expected active owned-path conflict")


def test_terminal_task_does_not_block_new_owner(tmp_path: Path):
    agent_ledger.upsert_task(
        tmp_path,
        task_id="old-worker",
        agent="codex",
        status="done",
        owned_paths=["starlight/src/pages"],
    )

    task = agent_ledger.upsert_task(
        tmp_path,
        task_id="new-worker",
        agent="codex",
        status="running",
        owned_paths=["starlight/src/pages/index.astro"],
    )

    assert task["task_id"] == "new-worker"


def test_append_event_heartbeat_and_summary(tmp_path: Path):
    agent_ledger.upsert_task(
        tmp_path,
        task_id="reviewer",
        agent="gemini",
        status="reviewing",
        task_family="code_review",
    )

    task = agent_ledger.append_event(
        tmp_path,
        "reviewer",
        event_type="review",
        actor="gemini",
        message="VERDICT: CLEAN",
        data={"verdict": "clean"},
    )
    assert task["events"][-1]["data"]["verdict"] == "clean"

    task = agent_ledger.heartbeat(tmp_path, "reviewer", actor="gemini", message="still reviewing")
    assert task["heartbeat_at"] == task["events"][-1]["timestamp"]

    summary = agent_ledger.summary(tmp_path)
    assert summary["active"] == 1
    assert summary["by_task_family"] == {"code_review": 1}
    assert summary["by_agent"] == {"gemini": 1}


def test_upsert_task_preserves_fields_on_partial_update(tmp_path: Path):
    agent_ledger.upsert_task(
        tmp_path,
        task_id="2823-ui-worker",
        agent="codex",
        status="running",
        issue=2823,
        lane="ui",
        task_family="design",
        model="gpt-5.4",
        branch="codex/2823-lightweight-ui",
        owned_paths=["starlight/src/pages"],
        metadata={"phase": "foundation"},
    )

    task = agent_ledger.upsert_task(
        tmp_path,
        task_id="2823-ui-worker",
        status="reviewing",
        metadata={"review": "agy"},
    )

    assert task["agent"] == "codex"
    assert task["issue"] == 2823
    assert task["lane"] == "ui"
    assert task["task_family"] == "design"
    assert task["model"] == "gpt-5.4"
    assert task["branch"] == "codex/2823-lightweight-ui"
    assert task["owned_paths"] == ["starlight/src/pages"]
    assert task["metadata"] == {"phase": "foundation", "review": "agy"}
    assert task["events"][-1]["message"] == "running -> reviewing"


def test_heartbeat_writes_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    agent_ledger.upsert_task(tmp_path, task_id="reviewer", agent="gemini")
    writes: list[Path] = []
    original_write = agent_ledger.write_json_atomic

    def counting_write(path: Path, payload: dict):
        writes.append(path)
        original_write(path, payload)

    monkeypatch.setattr(agent_ledger, "write_json_atomic", counting_write)

    task = agent_ledger.heartbeat(tmp_path, "reviewer", actor="gemini")

    assert task["heartbeat_at"] == task["events"][-1]["timestamp"]
    assert len(writes) == 1


def test_parallel_conflicting_claims_are_serialized(tmp_path: Path):
    barrier = threading.Barrier(2)
    outcomes: list[str] = []

    def claim(task_id: str) -> None:
        barrier.wait(timeout=5)
        try:
            agent_ledger.upsert_task(
                tmp_path,
                task_id=task_id,
                agent="codex",
                status="running",
                owned_paths=["starlight/src"],
            )
        except agent_ledger.OwnershipConflictError:
            outcomes.append("conflict")
        else:
            outcomes.append("ok")

    threads = [threading.Thread(target=claim, args=(f"worker-{index}",)) for index in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)

    assert sorted(outcomes) == ["conflict", "ok"]


def test_task_paths_do_not_collapse_valid_ids(tmp_path: Path):
    assert agent_ledger.task_path(tmp_path, "a") != agent_ledger.task_path(tmp_path, "a.")


def test_corrupt_task_json_is_not_silently_ignored(tmp_path: Path):
    agent_ledger.tasks_dir(tmp_path).mkdir(parents=True)
    agent_ledger.task_path(tmp_path, "broken").write_text("{", encoding="utf-8")

    with pytest.raises(agent_ledger.LedgerError, match="invalid JSON"):
        agent_ledger.list_tasks(tmp_path)


def test_absolute_owned_path_is_rejected(tmp_path: Path):
    with pytest.raises(agent_ledger.LedgerError, match="relative"):
        agent_ledger.upsert_task(
            tmp_path,
            task_id="absolute-owner",
            agent="codex",
            owned_paths=[str(tmp_path / "starlight/src")],
        )


def test_coordination_task_rejects_invalid_task_id():
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(coordination_router.coordination_task("bad id"))

    assert exc_info.value.status_code == 400


def test_cli_reports_bad_json(tmp_path: Path, capsys):
    rc = agent_ledger.main(
        [
            "--repo-root",
            str(tmp_path),
            "upsert-task",
            "--task-id",
            "bad-json",
            "--agent",
            "codex",
            "--metadata",
            "{",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert rc == 2
    assert "invalid JSON object" in payload["error"]


def test_cli_reports_conflict(tmp_path: Path, capsys):
    assert agent_ledger.main(
        [
            "--repo-root",
            str(tmp_path),
            "upsert-task",
            "--task-id",
            "ui",
            "--agent",
            "codex",
            "--status",
            "running",
            "--owned-path",
            "starlight/src",
        ]
    ) == 0
    capsys.readouterr()

    rc = agent_ledger.main(
        [
            "--repo-root",
            str(tmp_path),
            "upsert-task",
            "--task-id",
            "ui-css",
            "--agent",
            "codex",
            "--status",
            "running",
            "--owned-path",
            "starlight/src/styles/course.css",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert rc == 2
    assert payload["error"] == "ownership_conflict"
