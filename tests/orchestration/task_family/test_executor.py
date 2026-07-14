"""Tests for the task-family cleanup executor's fail-closed boundaries."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
from dataclasses import replace
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest

from scripts.orchestration.task_family import codex_state, executor, git_safety
from scripts.orchestration.task_family.storage import TaskFamilyStorage


def _git_env() -> dict[str, str]:
    return {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}


def git(cwd: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=cwd, check=False, capture_output=True, text=True, env=_git_env()
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    return proc.stdout.strip()


def init_repo(tmp_path: Path) -> Path:
    repo, remote = tmp_path / "repo", tmp_path / "origin.git"
    git(tmp_path, "init", "--initial-branch=main", str(repo))
    git(tmp_path, "init", "--bare", str(remote))
    git(repo, "config", "user.email", "cleanup@example.invalid")
    git(repo, "config", "user.name", "Cleanup test")
    (repo / "README.md").write_text("seed\n", encoding="utf-8")
    git(repo, "add", "README.md")
    git(repo, "commit", "-m", "seed")
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "-u", "origin", "main")
    return repo


def add_worktree(repo: Path, branch: str) -> Path:
    worktree = repo.parent / f"worktree-{uuid4().hex}"
    git(repo, "worktree", "add", "-b", branch, str(worktree), "main")
    (worktree / "payload.txt").write_text(branch, encoding="utf-8")
    git(worktree, "add", "payload.txt")
    git(worktree, "commit", "-m", "payload")
    return worktree


def write_threads(path: Path, rows: list[dict[str, Any]]) -> None:
    """Match Codex's production-shaped TEXT UUID ``threads`` table."""
    connection = sqlite3.connect(path)
    connection.execute(
        "CREATE TABLE threads (id TEXT PRIMARY KEY, title TEXT, cwd TEXT, "
        "archived INTEGER, archived_at TEXT, host TEXT)"
    )
    connection.executemany(
        "INSERT INTO threads(id,title,cwd,archived,archived_at,host) VALUES (?,?,?,?,?,?)",
        [
            (row["id"], row["title"], row["cwd"], row["archived"], row["archived_at"], row["host"])
            for row in rows
        ],
    )
    connection.commit()
    connection.close()


def task(task_id: str, *, title: str, cwd: Path, db_path: Path) -> executor.TaskTarget:
    return executor.TaskTarget(task_id=task_id, title=title, cwd=str(cwd), db_path=db_path, host="host-a")


def worktree_target(worktree: Path, branch: str, family: str, number: int = 7) -> executor.WorktreeTarget:
    return executor.WorktreeTarget(
        id=str(uuid4()), worktree=worktree, branch=branch, pr_number=number, pr_base="main", explicit_family=family
    )


def persisted(plan: executor.CleanupPlan, repo: Path) -> executor.CleanupPlan:
    """Write the planner-owned immutable document; executor never writes it."""
    payload = {
        "schema_version": 1,
        "family_id": plan.family_id,
        "operation_id": plan.operation_id,
        "operation": plan.mode,
        "selected_task_ids": sorted(plan.selected_task_ids),
    }
    digest = executor._canonical_plan_digest(payload)
    payload["digest"] = digest
    path = executor.plan_path(repo, plan)
    git_safety.write_json_atomic(path, payload)
    git_safety.write_json_atomic(
        executor.manifest_path(repo, plan),
        {
            "schema_version": 1,
            "family_id": plan.family_id,
            "seed_task_id": sorted(plan.selected_task_ids)[0] if plan.selected_task_ids else str(uuid4()),
            "nodes": [{"task_id": task_id} for task_id in sorted(plan.selected_task_ids)],
            "relations": [],
        },
    )
    return replace(plan, persisted_plan_digest=digest)


def plan(
    repo: Path,
    *,
    family: str,
    mode: str,
    task_targets: tuple[executor.TaskTarget, ...],
    worktree_targets: tuple[executor.WorktreeTarget, ...] = (),
    runtime_targets: tuple[executor.RuntimeTarget, ...] = (),
) -> executor.CleanupPlan:
    draft = executor.CleanupPlan(
        operation_id=str(uuid4()),
        family_id=family,
        lineage_id=str(uuid4()),
        mode=mode,
        task_targets=task_targets,
        worktree_targets=worktree_targets,
        runtime_targets=runtime_targets,
        selected_task_ids=frozenset(item.task_id for item in task_targets),
        pin_unknown_confirmed=True,
        persisted_plan_digest="0" * 64,
    )
    return persisted(draft, repo)


def pr(branch: str, head: str, number: int) -> dict[str, Any]:
    return {
        "number": number,
        "state": "MERGED",
        "head_ref_oid": head,
        "head_ref_name": branch,
        "base_ref_name": "main",
        "merge_state_status": "CLEAN",
        "merge_commit": {"oid": head},
        "is_cross_repository": False,
    }


def stub_remote(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(git_safety, "repo_default_branch", lambda *_args, **_kwargs: "main")
    monkeypatch.setattr(git_safety, "remote_protected_branches", lambda *_args, **_kwargs: set())


def test_discovers_state_5_and_uses_read_only_production_threads_schema(tmp_path: Path) -> None:
    home = tmp_path / ".codex"
    home.mkdir()
    task_id = str(UUID("00000000-0000-4000-8000-000000000005"))
    production_db = home / "state_5.sqlite"
    write_threads(
        production_db,
        [{"id": task_id, "title": "A", "cwd": "/repo", "archived": 0, "archived_at": None, "host": "host-a"}],
    )

    assert codex_state.discover_state_database(codex_home=home) == production_db
    with codex_state.open_state_db(production_db) as connection:
        with pytest.raises(sqlite3.OperationalError):
            connection.execute("UPDATE threads SET archived = 1 WHERE id = ?", (task_id,))
    record = codex_state.read_thread_record(production_db, task_id=task_id)
    assert record.thread_id == task_id
    assert record.archived is False


def test_executor_paths_match_task_family_storage(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    cleanup_plan = executor.CleanupPlan(
        operation_id=str(uuid4()),
        family_id="path-contract",
        lineage_id=str(uuid4()),
        mode="archive_only",
        task_targets=(),
        worktree_targets=(),
        runtime_targets=(),
        selected_task_ids=frozenset(),
        pin_unknown_confirmed=True,
        persisted_plan_digest="0" * 64,
    )
    storage = TaskFamilyStorage(repo, cleanup_plan.family_id, cleanup_plan.operation_id)

    assert executor.state_path(repo, cleanup_plan) == storage.state_path
    assert executor.plan_path(repo, cleanup_plan) == storage.plan_path
    assert executor.manifest_path(repo, cleanup_plan) == storage.manifest_path
    assert executor.receipt_path(repo, cleanup_plan) == storage.receipt_path


def test_apply_requires_caller_digest_and_exact_persisted_selection(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    task_id, other_id = str(uuid4()), str(uuid4())
    db = tmp_path / "state_5.sqlite"
    write_threads(db, [{"id": task_id, "title": "A", "cwd": str(repo), "archived": 1, "archived_at": "2026-01-01Z", "host": "host-a"}])
    approved = plan(repo, family="digest", mode="archive_only", task_targets=(task(task_id, title="A", cwd=repo, db_path=db),))

    unauthorized = replace(approved, persisted_plan_digest="f" * 64)
    rejected = executor.CleanupExecutor(repo, unauthorized).run()
    assert rejected["state"] == "blocked"
    assert "caller digest" in rejected["blocked"]["reason"]

    raw = json.loads(executor.plan_path(repo, approved).read_text(encoding="utf-8"))
    raw["selected_task_ids"] = [other_id]
    raw["digest"] = executor._canonical_plan_digest(raw)
    git_safety.write_json_atomic(executor.plan_path(repo, approved), raw)
    blocked = executor.CleanupExecutor(repo, approved).run()
    assert blocked["state"] == "blocked"
    assert "caller digest" in blocked["blocked"]["reason"]


def test_archive_only_observes_native_archive_and_stops_at_tasks_archived(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = init_repo(tmp_path)
    task_id = str(uuid4())
    db = tmp_path / "state_5.sqlite"
    write_threads(db, [{"id": task_id, "title": "A", "cwd": str(repo), "archived": 1, "archived_at": "2026-01-01Z", "host": "host-a"}])
    approved = plan(repo, family="archive", mode="archive_only", task_targets=(task(task_id, title="A", cwd=repo, db_path=db),))
    monkeypatch.setattr(git_safety, "run_git", lambda *_args, **_kwargs: pytest.fail("archive-only called git"))

    result = executor.CleanupExecutor(repo, approved).run()
    assert result["state"] == "tasks_archived"
    assert result["resources"]["task"].keys() == {task_id}
    receipt = json.loads(executor.receipt_path(repo, approved).read_text(encoding="utf-8"))
    assert receipt["final_state"] == "tasks_archived"
    assert receipt["actual"][-1]["action"] == "archive"
    assert receipt["final_resources"] == [{
        "resource_type": "task",
        "resource_id": task_id,
        "task_ids": [task_id],
        "action": "archived",
        "reason": "final executor resource status: actual",
        "error": "",
        "recovery": "",
    }]
    assert "Final resources: task:" in executor.receipt_path(repo, approved).with_name("receipt.txt").read_text(encoding="utf-8")


def test_advisory_lock_path_is_not_git_lock_but_git_worktree_lock_blocks(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    worktree = add_worktree(repo, "cleanup/locked")
    git_safety._worktree_lock_path(repo, worktree).parent.mkdir(parents=True, exist_ok=True)
    git_safety._worktree_lock_path(repo, worktree).touch()
    assert git_safety.is_worktree_locked(repo, worktree) is False

    git(repo, "worktree", "lock", "--reason", "operator-held", str(worktree))
    assert git_safety.is_worktree_locked(repo, worktree) is True
    with pytest.raises(git_safety.GitSafetyError, match="locked"):
        git_safety.verify_worktree_candidate(repo, worktree=worktree, branch="cleanup/locked")


def test_github_queries_use_valid_commands_and_normalize_merge_commit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = init_repo(tmp_path)
    calls: list[list[str]] = []

    def fake_gh(args: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        if args[:3] == ["repo", "view", "--json"]:
            return subprocess.CompletedProcess(args, 0, '{"owner":{"login":"o"},"name":"r"}', "")
        if args[:2] == ["api", "--paginate"]:
            return subprocess.CompletedProcess(args, 0, '[{"name":"main","protected":true}]', "")
        return subprocess.CompletedProcess(args, 1, "", "unexpected")

    monkeypatch.setattr(git_safety, "run_gh", fake_gh)
    assert git_safety.remote_protected_branches(repo) == {"main"}
    assert all("--json" not in call for call in calls if call and call[0] == "api")
    assert git_safety._normalize_merge_commit({"oid": "a" * 40}) == "a" * 40
    assert git_safety._normalize_merge_commit("b" * 40) == "b" * 40


def test_finish_cleanup_preserves_unrelated_worktree_and_rechecks_pr_before_mutation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = init_repo(tmp_path)
    target_branch, unrelated_branch = "cleanup/remove", "cleanup/keep"
    remove_worktree, keep_worktree = add_worktree(repo, target_branch), add_worktree(repo, unrelated_branch)
    task_id = str(uuid4())
    db = tmp_path / "state_5.sqlite"
    write_threads(db, [{"id": task_id, "title": "A", "cwd": str(remove_worktree), "archived": 1, "archived_at": "2026-01-01Z", "host": "host-a"}])
    target = worktree_target(remove_worktree, target_branch, "scope", number=9)
    approved = plan(repo, family="scope", mode="finish_and_clean", task_targets=(task(task_id, title="A", cwd=remove_worktree, db_path=db),), worktree_targets=(target,))
    stub_remote(monkeypatch)
    calls = {"count": 0}
    head = git(remove_worktree, "rev-parse", "HEAD")

    def query(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        calls["count"] += 1
        return pr(target_branch, head, 9)

    monkeypatch.setattr(git_safety, "query_pr_by_head", query)
    result = executor.CleanupExecutor(repo, approved).run()
    assert result["state"] == "completed"
    assert calls["count"] >= 3
    assert not remove_worktree.exists()
    assert keep_worktree.exists()
    git(repo, "show-ref", "--verify", "--quiet", f"refs/heads/{unrelated_branch}")
    assert not git_safety.local_branch_exists(repo, target_branch)


def test_branch_delete_crash_resumes_from_verified_bundle_when_branch_is_already_absent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = init_repo(tmp_path)
    branch, worktree = "cleanup/resume", add_worktree(repo, "cleanup/resume")
    task_id = str(uuid4())
    db = tmp_path / "state_5.sqlite"
    write_threads(db, [{"id": task_id, "title": "A", "cwd": str(worktree), "archived": 1, "archived_at": "2026-01-01Z", "host": "host-a"}])
    target = worktree_target(worktree, branch, "resume", number=10)
    approved = plan(repo, family="resume", mode="finish_and_clean", task_targets=(task(task_id, title="A", cwd=worktree, db_path=db),), worktree_targets=(target,))
    stub_remote(monkeypatch)
    head = git(worktree, "rev-parse", "HEAD")
    monkeypatch.setattr(git_safety, "query_pr_by_head", lambda *_args, **_kwargs: pr(branch, head, 10))
    original_delete = git_safety.delete_branch

    def delete_then_crash(*args: Any, **kwargs: Any) -> None:
        original_delete(*args, **kwargs)
        raise RuntimeError("simulated process crash immediately after branch deletion")

    monkeypatch.setattr(git_safety, "delete_branch", delete_then_crash)

    interrupted = executor.CleanupExecutor(repo, approved).run()
    assert interrupted["state"] == "blocked"
    assert not git_safety.local_branch_exists(repo, branch)

    monkeypatch.setattr(git_safety, "delete_branch", original_delete)
    resumed = executor.CleanupExecutor(repo, approved).run()
    assert resumed["state"] == "completed"
    assert resumed["stages"]["branches_deleted"]["results"][target.id]["status"] == "already_absent"
    receipt = json.loads(executor.receipt_path(repo, approved).read_text(encoding="utf-8"))
    assert any(item["action"] == "retired_before_resume" for item in receipt["final_resources"])


def test_remote_lookup_failure_blocks_branch_delete(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = init_repo(tmp_path)
    monkeypatch.setattr(git_safety, "run_git", lambda *_args, **_kwargs: subprocess.CompletedProcess([], 128, "", "network down"))
    with pytest.raises(git_safety.GitSafetyError, match="remote branch lookup failed"):
        git_safety.remote_branch_present(repo, "cleanup/x")


def test_runtime_without_eligibility_or_proof_is_preserved_and_blocks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = init_repo(tmp_path)
    branch, worktree = "cleanup/runtime", add_worktree(repo, "cleanup/runtime")
    task_id = str(uuid4())
    db = tmp_path / "state_5.sqlite"
    write_threads(db, [{"id": task_id, "title": "A", "cwd": str(worktree), "archived": 1, "archived_at": "2026-01-01Z", "host": "host-a"}])
    target = worktree_target(worktree, branch, "runtime", number=11)
    runtime = executor.RuntimeTarget(id=str(uuid4()), kind="handoff", eligible=False, proof=None)
    approved = plan(repo, family="runtime", mode="finish_and_clean", task_targets=(task(task_id, title="A", cwd=worktree, db_path=db),), worktree_targets=(target,), runtime_targets=(runtime,))
    stub_remote(monkeypatch)
    head = git(worktree, "rev-parse", "HEAD")
    monkeypatch.setattr(git_safety, "query_pr_by_head", lambda *_args, **_kwargs: pr(branch, head, 11))

    result = executor.CleanupExecutor(repo, approved).run()
    assert result["state"] == "blocked"
    assert result["resume_stage"] == "runtime_retired"
    saved = result["resources"]["runtime"][runtime.id]
    assert saved["status"] == "failed"
    assert "preserved" in saved["reason"]
