"""End-to-end tests for the noninteractive task-family CLI."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
from pathlib import Path
from uuid import uuid4

import pytest

from scripts.orchestration.task_family import cli, git_safety
from scripts.orchestration.task_family.model import RelationType, TaskFamilyManifest, TaskNode, TaskRelation
from scripts.orchestration.task_family.storage import TaskFamilyStorage


def _git_env() -> dict[str, str]:
    return {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}


def _git(cwd: Path, *args: str) -> None:
    result = subprocess.run(["git", *args], cwd=cwd, env=_git_env(), capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr or result.stdout


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    _git(tmp_path, "init", "--initial-branch=main", str(repo))
    _git(repo, "config", "user.email", "cli@example.invalid")
    _git(repo, "config", "user.name", "CLI test")
    (repo / "README.md").write_text("seed\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-m", "seed")
    return repo


def _write_db(path: Path, rows: list[tuple[str, str, str, int, str | None, str]]) -> None:
    connection = sqlite3.connect(path)
    connection.execute(
        "CREATE TABLE threads (id TEXT PRIMARY KEY, title TEXT, cwd TEXT, "
        "archived INTEGER, archived_at TEXT, host TEXT)"
    )
    connection.executemany("INSERT INTO threads VALUES (?, ?, ?, ?, ?, ?)", rows)
    connection.commit()
    connection.close()


def _manifest(repo: Path) -> tuple[TaskFamilyManifest, dict[str, str]]:
    task_ids = {name: str(uuid4()) for name in ("root", "worker", "review", "handoff", "replacement", "unrelated")}
    nodes = tuple(
        TaskNode(task_id, title, str(repo), metadata={"cwd": str(repo), "host": "test-host"})
        for name, task_id, title in (
            ("root", task_ids["root"], "Planner"),
            ("worker", task_ids["worker"], "Implementation"),
            ("review", task_ids["review"], "Review"),
            ("handoff", task_ids["handoff"], "Continuation"),
            ("replacement", task_ids["replacement"], "Continuation"),
            ("unrelated", task_ids["unrelated"], "Planner"),
        )
    )
    relations = (
        TaskRelation(task_ids["worker"], task_ids["root"], RelationType.SUBAGENT_OF, "spawn"),
        TaskRelation(task_ids["review"], task_ids["worker"], RelationType.REVIEWER_FOR, "review"),
        TaskRelation(task_ids["handoff"], task_ids["worker"], RelationType.HANDOFF_OF, "handoff"),
        TaskRelation(task_ids["replacement"], task_ids["handoff"], RelationType.REPLACEMENT_OF, "replacement"),
        TaskRelation(task_ids["replacement"], task_ids["handoff"], RelationType.ROLLOVER_GENERATION_OF, "generation"),
    )
    return TaskFamilyManifest("family-cli", task_ids["root"], nodes, relations), task_ids


def _write_manifest(path: Path, manifest: TaskFamilyManifest) -> None:
    path.write_text(json.dumps(manifest.to_dict()), encoding="utf-8")


def _selection_args(ids: dict[str, str]) -> list[str]:
    selected = [ids[name] for name in ("root", "worker", "review", "handoff", "replacement")]
    args: list[str] = []
    for task_id in selected:
        args.extend(("--select-task", task_id))
    args.extend(("--actor", "operator"))
    for task_id in selected:
        args.extend(("--confirm-pin-unknown", task_id))
    return args


def _preview_args(command: str, repo: Path, manifest_path: Path, db: Path, ids: dict[str, str], operation: str, lineage: str) -> list[str]:
    return [
        command,
        "--repo-root",
        str(repo),
        "--manifest",
        str(manifest_path),
        "--operation-id",
        operation,
        "--lineage-id",
        lineage,
        "--base-title",
        "Lifecycle repair",
        "--db",
        str(db),
        *_selection_args(ids),
    ]


def test_inspect_renders_roles_counts_and_similar_title_exclusion(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo = _repo(tmp_path)
    manifest, ids = _manifest(repo)
    path = tmp_path / "manifest.json"
    _write_manifest(path, manifest)

    assert cli.main(["inspect", "--manifest", str(path), "--json"]) == cli.EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["counts"]["included"] == 5
    assert payload["counts"]["excluded"] == 1
    assert payload["excluded"] == [{"task_id": ids["unrelated"], "title": "Planner", "reason": "outside exact-ID seed component"}]
    assert next(task for task in payload["tasks"] if task["task_id"] == ids["replacement"])["roles"] == ["Replacement", "Generation 1"]

    assert cli.main(["inspect", "--manifest", str(path)]) == cli.EXIT_OK
    assert "excluded" in capsys.readouterr().out


def test_preview_rename_persists_immutable_mapping_and_requires_each_pin_confirmation(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo = _repo(tmp_path)
    manifest, ids = _manifest(repo)
    path = tmp_path / "manifest.json"
    _write_manifest(path, manifest)
    operation = str(uuid4())
    args = [
        "preview-rename",
        "--repo-root",
        str(repo),
        "--manifest",
        str(path),
        "--operation-id",
        operation,
        "--base-title",
        "Lifecycle repair",
        *_selection_args(ids),
        "--json",
    ]

    assert cli.main(args) == cli.EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    replacement = next(item for item in payload["rename_map"] if item["task_id"] == ids["replacement"])
    assert replacement["new_title"] == "Lifecycle repair [Replacement · Generation 1]"
    storage = TaskFamilyStorage(repo, manifest.family_id, operation)
    assert storage.rename_plan_path.exists()
    assert storage.manifest_path.exists()

    incomplete = args.copy()
    confirmation_index = incomplete.index("--confirm-pin-unknown", incomplete.index("--actor"))
    while incomplete[confirmation_index + 1] != ids["worker"]:
        confirmation_index = incomplete.index("--confirm-pin-unknown", confirmation_index + 1)
    del incomplete[confirmation_index : confirmation_index + 2]
    incomplete[incomplete.index("--operation-id") + 1] = str(uuid4())
    assert cli.main(incomplete) == cli.EXIT_BLOCKED
    assert "pin_state_unconfirmed" in json.loads(capsys.readouterr().out)["planner_blockers"][0]["code"]


def test_conflicting_graph_blocks_preview_without_db_or_git_mutation(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo = _repo(tmp_path)
    root, one, two = str(uuid4()), str(uuid4()), str(uuid4())
    manifest = TaskFamilyManifest(
        "conflict",
        root,
        (TaskNode(root, "Root", str(repo)), TaskNode(one, "One", str(repo)), TaskNode(two, "Two", str(repo))),
        (
            TaskRelation(root, one, RelationType.ROLLOVER_GENERATION_OF, "one"),
            TaskRelation(root, two, RelationType.ROLLOVER_GENERATION_OF, "two"),
        ),
    )
    path = tmp_path / "conflict.json"
    _write_manifest(path, manifest)
    db = tmp_path / "state_5.sqlite"
    _write_db(db, [(root, "Root", str(repo), 0, None, "test-host")])
    operation, lineage = str(uuid4()), str(uuid4())
    args = [
        "preview-archive",
        "--repo-root", str(repo), "--manifest", str(path), "--operation-id", operation,
        "--lineage-id", lineage, "--base-title", "Repair", "--db", str(db),
        "--select-task", root, "--actor", "operator", "--confirm-pin-unknown", root, "--json",
    ]
    assert cli.main(args) == cli.EXIT_BLOCKED
    payload = json.loads(capsys.readouterr().out)
    assert any(item["code"] == "conflicting_membership" for item in payload["planner_blockers"])
    with sqlite3.connect(db) as connection:
        assert connection.execute("SELECT archived FROM threads WHERE id = ?", (root,)).fetchone()[0] == 0


def test_reconcile_title_and_partial_archive_retry_append_receipts(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo = _repo(tmp_path)
    manifest, ids = _manifest(repo)
    path = tmp_path / "manifest.json"
    _write_manifest(path, manifest)
    db = tmp_path / "state_5.sqlite"
    rows = []
    for name, task_id in ids.items():
        title = "Planner" if name in {"root", "unrelated"} else {"worker": "Implementation", "review": "Review", "handoff": "Continuation", "replacement": "Continuation"}[name]
        rows.append((task_id, title, str(repo), 1 if name != "worker" else 0, "2026-07-14T00:00:00Z" if name != "worker" else None, "test-host"))
    _write_db(db, rows)
    operation, lineage = str(uuid4()), str(uuid4())
    assert cli.main(_preview_args("preview-archive", repo, path, db, ids, operation, lineage)) == cli.EXIT_OK
    capsys.readouterr()

    assert cli.main(["reconcile-title", "--db", str(db), "--task-id", ids["root"], "--cwd", str(repo), "--expected-title", "Planner", "--host", "test-host"]) == cli.EXIT_OK
    assert json.loads(capsys.readouterr().out)["ok"] is True

    reconcile = [
        "reconcile-archive", "--repo-root", str(repo), "--family-id", manifest.family_id,
        "--operation-id", operation, "--db", str(db), "--task-id", ids["worker"],
        "--cwd", str(repo), "--expected-title", "Implementation", "--host", "test-host",
    ]
    assert cli.main(reconcile) == cli.EXIT_BLOCKED
    assert json.loads(capsys.readouterr().out)["ok"] is False
    with sqlite3.connect(db) as connection:
        connection.execute("UPDATE threads SET archived = 1, archived_at = ? WHERE id = ?", ("2026-07-14T01:00:00Z", ids["worker"]))
        connection.commit()
    assert cli.main(reconcile) == cli.EXIT_OK
    assert json.loads(capsys.readouterr().out)["thread"]["archived"] is True
    storage = TaskFamilyStorage(repo, manifest.family_id, operation)
    assert len(storage.load_events()) == 2


def test_apply_archive_uses_persisted_digest_zero_git_mutation_and_completed_repeat_is_noop(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    repo = _repo(tmp_path)
    manifest, ids = _manifest(repo)
    path = tmp_path / "manifest.json"
    _write_manifest(path, manifest)
    db = tmp_path / "state_5.sqlite"
    titles = {"root": "Planner", "worker": "Implementation", "review": "Review", "handoff": "Continuation", "replacement": "Continuation", "unrelated": "Planner"}
    _write_db(db, [(task_id, titles[name], str(repo), 1, "2026-07-14T00:00:00Z", "test-host") for name, task_id in ids.items()])
    operation, lineage = str(uuid4()), str(uuid4())
    assert cli.main(_preview_args("preview-archive", repo, path, db, ids, operation, lineage)) == cli.EXIT_OK
    preview = capsys.readouterr().out
    digest = next(line.split(": ", 1)[1] for line in preview.splitlines() if line.startswith("Plan digest:"))
    monkeypatch.setattr(git_safety, "run_git", lambda *_args, **_kwargs: pytest.fail("archive-only called git"))
    apply = [
        "apply-cleanup", "--repo-root", str(repo), "--family-id", manifest.family_id,
        "--operation-id", operation, "--lineage-id", lineage, "--plan-digest", digest,
    ]
    assert cli.main(apply) == cli.EXIT_OK
    assert "tasks_archived" in capsys.readouterr().out

    assert cli.main([
        "receipt", "--repo-root", str(repo), "--family-id", manifest.family_id,
        "--operation-id", operation, "--json",
    ]) == cli.EXIT_OK
    assert json.loads(capsys.readouterr().out)["state"] == "tasks_archived"

    calls = {"count": 0}
    original = cli.codex_state.await_task_target

    def counted(*args: object, **kwargs: object):
        calls["count"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(cli.codex_state, "await_task_target", counted)
    assert cli.main(apply) == cli.EXIT_OK
    assert calls["count"] == 0

    drift = apply.copy()
    drift[-1] = "0" * 64
    assert cli.main(drift) == cli.EXIT_BLOCKED
    assert "digest" in capsys.readouterr().out

    storage = TaskFamilyStorage(repo, manifest.family_id, operation)
    execution_data = storage.load_execution()
    execution_data["target_db"] = str(tmp_path / "other.sqlite")
    storage.execution_path.write_text(json.dumps(execution_data), encoding="utf-8")
    assert cli.main(apply) == cli.EXIT_BLOCKED
    assert "drifted" in capsys.readouterr().out


def test_preview_cleanup_reports_only_explicit_owned_resource_targets(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo = _repo(tmp_path)
    task_id = str(uuid4())
    worktree = repo / "managed"
    manifest = TaskFamilyManifest(
        "cleanup-cli",
        task_id,
        (
            TaskNode(
                task_id,
                "Done",
                str(repo),
                worktree=str(worktree),
                branch="codex/cleanup-cli",
                pr_id="42",
                metadata={"cwd": str(repo), "worktree_family": "cleanup-cli", "pr_base": "main"},
            ),
        ),
        (),
    )
    path = tmp_path / "cleanup.json"
    _write_manifest(path, manifest)
    db = tmp_path / "state_5.sqlite"
    _write_db(db, [(task_id, "Done", str(repo), 0, None, "test-host")])
    assert cli.main([
        "preview-cleanup", "--repo-root", str(repo), "--manifest", str(path),
        "--operation-id", str(uuid4()), "--lineage-id", str(uuid4()), "--base-title", "Done",
        "--db", str(db), "--select-task", task_id, "--actor", "operator",
        "--confirm-pin-unknown", task_id, "--json",
    ]) == cli.EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["resources"]["worktree_targets"] == [{
        "id": task_id, "worktree": str(worktree), "branch": "codex/cleanup-cli",
        "pr_number": 42, "pr_base": "main", "explicit_family": "cleanup-cli",
    }]
