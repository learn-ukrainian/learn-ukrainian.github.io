"""Tests for read-only dispatch checkout mutation guard (#7124).

Dedicated test module to keep CI fastlane slim and avoid pulling heavy
dependencies from tests/test_delegate.py.

- Scoping read-only snapshot off .worktrees/ entirely
- Preserving real worker failures alongside read-only mutation diagnostics
- Negative returncode signal decoding
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import delegate


def _sanitize_git_env_for_test(monkeypatch) -> None:
    for key in tuple(os.environ):
        if key.startswith(("GIT_", "PRE_COMMIT")):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.delenv("AGENT_NO_MERGE", raising=False)


def _init_git_repo_for_test(path: Path, monkeypatch) -> None:
    _sanitize_git_env_for_test(monkeypatch)
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True, timeout=30)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=path,
        check=True,
        capture_output=True,
        timeout=30,
    )
    subprocess.run(
        ["git", "config", "user.name", "test"],
        cwd=path,
        check=True,
        capture_output=True,
        timeout=30,
    )


def _seed_read_only_checkout_fixture(repo: Path, monkeypatch) -> None:
    """Git repo with production-shaped ignore rules + one tracked file."""
    _init_git_repo_for_test(repo, monkeypatch)
    entire = repo / ".entire"
    entire.mkdir(parents=True, exist_ok=True)
    (entire / ".gitignore").write_text(
        "tmp/\nsettings.local.json\nmetadata/\nlogs/\nredactors/local/\n",
        encoding="utf-8",
    )
    (repo / ".gitignore").write_text(
        ".agent/\n"
        "batch_state/\n"
        ".pytest_cache/\n"
        ".pytest_breadcrumbs/\n"
        ".ruff_cache/\n"
        "__pycache__/\n"
        ".runtime/\n"
        "*.sqlite3-wal\n"
        "*.sqlite3-shm\n"
        "*.sqlite3-journal\n",
        encoding="utf-8",
    )
    (repo / "tracked.txt").write_text("baseline\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", ".entire/.gitignore", ".gitignore", "tracked.txt"],
        cwd=repo,
        check=True,
        timeout=30,
    )
    subprocess.run(
        ["git", "commit", "-m", "fixture"],
        cwd=repo,
        check=True,
        capture_output=True,
        timeout=30,
    )


def _finalize_mock_result():
    return type(
        "_Result",
        (),
        {
            "ok": True,
            "response": "done",
            "stderr_excerpt": None,
            "returncode": 0,
            "rate_limited": False,
            "model": "grok-4.6",
            "effort": "high",
            "cli_version": "0.2.111",
        },
    )()


@pytest.fixture
def tmp_tasks_dir(tmp_path, monkeypatch):
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    monkeypatch.setattr(delegate, "_TASKS_DIR", tasks_dir)
    return tasks_dir


def test_read_only_snapshot_excluded_path_classification():
    """#7124: every ``.worktrees/`` path is out of snapshot scope."""
    assert delegate._is_read_only_snapshot_excluded_path(".worktrees")
    assert delegate._is_read_only_snapshot_excluded_path(
        ".worktrees/dispatch/other-lane/other-task/scripts/foo.py"
    )
    assert delegate._is_read_only_snapshot_excluded_path("./.worktrees/dispatch/a/b/")
    assert not delegate._is_read_only_snapshot_excluded_path("tracked.txt")
    assert not delegate._is_read_only_snapshot_excluded_path("sub/.worktrees/file")
    assert not delegate._is_read_only_snapshot_excluded_path(".worktreesish/file")


def test_real_delegate_snapshot_sidecar_is_runtime_state_via_batch_state():
    """#7208: real sidecars under batch_state/tasks/<task>.snapshots/ are exempt.

    Sidecars are built from ``_TASKS_DIR`` (``batch_state/tasks``), so the
    existing ``batch_state`` runtime-state dir-name check covers them. A
    synthetic ``tasks/…`` path without that prefix is not a production shape.
    """
    abs_path = delegate._read_only_snapshot_sidecar_path("read-only-task", "pre")
    sidecar = str(abs_path.relative_to(delegate._REPO_ROOT)).replace("\\", "/")
    assert sidecar == (
        "batch_state/tasks/read-only-task.snapshots/read_only_checkout_pre.json"
    )
    assert delegate._is_read_only_runtime_state_path(sidecar)
    assert not delegate._is_read_only_runtime_telemetry_path(sidecar)


def test_read_only_checkout_snapshot_excludes_worktrees_tree(tmp_path, monkeypatch):
    """#7124: the snapshot records no ``.worktrees/`` entries at all."""
    repo = (tmp_path / "repo").resolve()
    repo.mkdir(parents=True, exist_ok=True)
    _seed_read_only_checkout_fixture(repo, monkeypatch)
    noise = repo / ".worktrees" / "dispatch" / "gemini" / "other-task"
    noise.mkdir(parents=True)
    (noise / "draft.md").write_text("other lane\n", encoding="utf-8")
    (repo / "untracked.txt").write_text("visible\n", encoding="utf-8")

    snapshot, error = delegate._read_only_checkout_snapshot(repo)

    assert error is None
    assert snapshot is not None
    assert "untracked.txt" in snapshot
    assert not any(
        delegate._is_read_only_snapshot_excluded_path(path) for path in snapshot
    )


def test_read_only_checkout_snapshot_keeps_rename_source_into_worktrees(
    tmp_path, monkeypatch
):
    """#7147: renaming a tracked file INTO ``.worktrees/`` keeps the source.

    ``git mv tracked.txt .worktrees/lane/tracked.txt`` is a mutation of the
    tracked source even though the destination is out of snapshot scope, so
    the source must still be recorded instead of the whole record dropping.
    """
    repo = (tmp_path / "repo").resolve()
    repo.mkdir(parents=True, exist_ok=True)
    _seed_read_only_checkout_fixture(repo, monkeypatch)
    lane = repo / ".worktrees" / "lane"
    lane.mkdir(parents=True)
    subprocess.run(
        ["git", "mv", "tracked.txt", ".worktrees/lane/tracked.txt"],
        cwd=repo,
        check=True,
        capture_output=True,
        timeout=30,
    )

    snapshot, error = delegate._read_only_checkout_snapshot(repo)

    assert error is None
    assert snapshot is not None
    assert snapshot["tracked.txt"] == "R :source"
    assert ".worktrees/lane/tracked.txt" not in snapshot


def test_read_only_dispatch_allows_concurrent_sibling_worktree_add(
    tmp_tasks_dir,
    tmp_path,
    monkeypatch,
):
    """#7124: a concurrent dispatch sandbox appearing under ``.worktrees/`` is excluded from snapshot."""
    checkout = (tmp_path / "repo-root").resolve()
    checkout.mkdir(parents=True, exist_ok=True)
    _seed_read_only_checkout_fixture(checkout, monkeypatch)
    gitignore = checkout / ".gitignore"
    gitignore.write_text(gitignore.read_text(encoding="utf-8") + ".worktrees/\n", encoding="utf-8")
    subprocess.run(["git", "add", ".gitignore"], cwd=checkout, check=True, timeout=30)
    subprocess.run(
        ["git", "commit", "-m", "ignore worktrees"],
        cwd=checkout,
        check=True,
        capture_output=True,
        timeout=30,
    )
    # Detach HEAD so ``git worktree add -b`` can create a sibling branch without
    # fighting the fixture branch checked out in this repo.
    subprocess.run(
        ["git", "checkout", "--detach", "HEAD"],
        cwd=checkout,
        check=True,
        capture_output=True,
        timeout=30,
    )

    task_id = "read-only-concurrent-sibling-worktree"
    state_path = delegate._state_path(task_id)
    delegate._write_state_atomic(
        state_path,
        {"task_id": task_id, "cwd": str(checkout)},
    )

    sibling = checkout / ".worktrees" / "dispatch" / "cursor" / "codeql-path-injection-fix"

    def concurrent_sibling_worktree(*_args, **_kwargs):
        sibling.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "git",
                "worktree",
                "add",
                "-b",
                "cursor/codeql-path-injection-fix",
                str(sibling),
                "HEAD",
            ],
            cwd=checkout,
            check=True,
            capture_output=True,
            timeout=30,
        )
        return _finalize_mock_result()

    with patch("agent_runtime.runner.invoke", side_effect=concurrent_sibling_worktree):
        rc = delegate._run_worker(
            task_id=task_id,
            agent="grok",
            prompt="Inventory thin-mode sources without editing the tree.",
            mode="read-only",
            cwd_str=str(checkout),
            model=None,
            hard_timeout=60,
        )

    state = delegate._read_state(state_path)
    assert rc == 0
    assert state is not None
    assert state["status"] == "done"
    assert state["read_only_mutation_paths"] == []
    assert state["last_error"] is None
    assert sibling.exists()
    post = state["read_only_checkout_post"]
    assert not any(
        delegate._is_read_only_snapshot_excluded_path(path) for path in post
    )


def test_read_only_dispatch_ignores_other_lane_worktree_activity(
    tmp_tasks_dir,
    tmp_path,
    monkeypatch,
):
    """#7124: writes inside an EXISTING sibling dispatch sandbox are out of scope.

    #6938 exempted only newly appeared sandboxes, so a concurrent lane writing
    under a ``.worktrees/dispatch/<agent>/<task>/`` tree that already existed at
    the pre-snapshot still false-failed a clean read-only dispatch.
    """
    checkout = (tmp_path / "repo-root").resolve()
    checkout.mkdir(parents=True, exist_ok=True)
    _seed_read_only_checkout_fixture(checkout, monkeypatch)
    gitignore = checkout / ".gitignore"
    gitignore.write_text(gitignore.read_text(encoding="utf-8") + ".worktrees/\n", encoding="utf-8")
    subprocess.run(["git", "add", ".gitignore"], cwd=checkout, check=True, timeout=30)
    subprocess.run(
        ["git", "commit", "-m", "ignore worktrees"],
        cwd=checkout,
        check=True,
        capture_output=True,
        timeout=30,
    )

    other_lane = checkout / ".worktrees" / "dispatch" / "gemini" / "other-task"
    other_lane.mkdir(parents=True)
    (other_lane / "draft.md").write_text("other lane v1\n", encoding="utf-8")

    task_id = "read-only-other-lane-worktree-noise"
    state_path = delegate._state_path(task_id)
    delegate._write_state_atomic(
        state_path,
        {"task_id": task_id, "cwd": str(checkout)},
    )

    def other_lane_activity(*_args, **_kwargs):
        (other_lane / "draft.md").write_text("other lane v2\n", encoding="utf-8")
        (other_lane / "more.py").write_text("# other lane\n", encoding="utf-8")
        return _finalize_mock_result()

    with patch("agent_runtime.runner.invoke", side_effect=other_lane_activity):
        rc = delegate._run_worker(
            task_id=task_id,
            agent="grok",
            prompt="Inventory thin-mode sources without editing the tree.",
            mode="read-only",
            cwd_str=str(checkout),
            model=None,
            hard_timeout=60,
        )

    state = delegate._read_state(state_path)
    assert rc == 0
    assert state is not None
    assert state["status"] == "done"
    assert state["read_only_mutation_paths"] == []
    assert state["last_error"] is None
    post = state["read_only_checkout_post"]
    assert not any(
        delegate._is_read_only_snapshot_excluded_path(path) for path in post
    )


def test_read_only_failed_worker_keeps_real_error_alongside_mutation(
    tmp_tasks_dir,
    tmp_path,
    monkeypatch,
):
    """#7124: the guard diagnostic must not overwrite the returncode-derived error."""
    checkout = (tmp_path / "repo-root").resolve()
    checkout.mkdir(parents=True, exist_ok=True)
    _seed_read_only_checkout_fixture(checkout, monkeypatch)

    task_id = "read-only-sigkill-plus-mutation"
    state_path = delegate._state_path(task_id)
    delegate._write_state_atomic(
        state_path,
        {"task_id": task_id, "cwd": str(checkout)},
    )

    sigkill_result = type(
        "_Result",
        (),
        {
            "ok": False,
            "response": "",
            "stderr_excerpt": "worker killed: out of memory",
            "returncode": -9,
            "rate_limited": False,
            "model": "grok-4.6",
            "effort": "high",
            "cli_version": "0.2.111",
        },
    )()

    def sigkill_with_mutation(*_args, **_kwargs):
        (checkout / "tracked.txt").write_text(
            "partial write before kill\n", encoding="utf-8"
        )
        return sigkill_result

    with patch("agent_runtime.runner.invoke", side_effect=sigkill_with_mutation):
        rc = delegate._run_worker(
            task_id=task_id,
            agent="grok",
            prompt="Review the module without edits.",
            mode="read-only",
            cwd_str=str(checkout),
            model=None,
            hard_timeout=60,
        )

    state = delegate._read_state(state_path)
    assert rc == 1
    assert state is not None
    assert state["status"] == "failed"
    assert state["returncode"] == -9
    assert state["returncode_reason"] == (
        "worker subprocess terminated by SIGKILL (returncode -9)"
    )
    assert state["read_only_mutation_paths"] == ["tracked.txt"]
    last_error = state["last_error"]
    assert "worker killed: out of memory" in last_error
    assert "read-only checkout mutation detected: tracked.txt" in last_error
