from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from fastapi.testclient import TestClient

from scripts.api import git_hygiene_router
from scripts.api.main import app

client = TestClient(app, raise_server_exceptions=False)


def _git(repo: Path, *args: str) -> str:
    env = os.environ.copy()
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX", "GIT_COMMON_DIR"):
        env.pop(key, None)
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        env=env,
        text=True,
        check=True,
    )
    return proc.stdout


def _write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def _commit_all(repo: Path, message: str) -> None:
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", message)


def _create_branch(repo: Path, branch: str, filename: str) -> None:
    _git(repo, "checkout", "-b", branch, "main")
    _write(repo / filename, f"{branch}\n")
    _commit_all(repo, f"add {branch}")
    _git(repo, "checkout", "main")


def _create_merged_branch(repo: Path, branch: str, filename: str) -> None:
    _create_branch(repo, branch, filename)
    _git(repo, "cherry-pick", branch)


def _create_upstream_gone_branch(repo: Path, branch: str, filename: str) -> None:
    _create_branch(repo, branch, filename)
    _git(repo, "checkout", branch)
    _git(repo, "push", "-u", "origin", branch)
    _git(repo, "checkout", "main")
    _git(repo, "push", "origin", "--delete", branch)


def _add_worktree(repo: Path, path: Path, branch: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _git(repo, "worktree", "add", str(path), branch)


def _cleanup_fixture(tmp_path: Path, monkeypatch) -> Path:
    repo = tmp_path / "repo"
    remote = tmp_path / "origin.git"
    repo.mkdir()
    remote.mkdir()
    _git(remote, "init", "--bare")
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "codex@example.invalid")
    _git(repo, "config", "user.name", "Codex Test")
    _git(repo, "remote", "add", "origin", str(remote))
    _write(repo / ".gitignore", ".worktrees/\nbatch_state/\n")
    _write(repo / "README.md", "base\n")
    _commit_all(repo, "initial")
    _git(repo, "push", "-u", "origin", "main")

    _create_upstream_gone_branch(repo, "codex/upstream-gone", "branches/upstream-gone.txt")
    _create_merged_branch(repo, "codex/merged-stale", "branches/merged-stale.txt")

    _create_merged_branch(repo, "codex/removable-merged", "branches/removable-merged.txt")
    _add_worktree(repo, repo / ".worktrees" / "removable-merged", "codex/removable-merged")

    _create_upstream_gone_branch(repo, "codex/dirty-gone", "branches/dirty-gone.txt")
    _add_worktree(repo, repo / ".worktrees" / "dirty-gone", "codex/dirty-gone")
    _write(repo / ".worktrees" / "dirty-gone" / "local.txt", "dirty\n")

    _create_merged_branch(repo, "codex/interactive-merged", "branches/interactive-merged.txt")
    _add_worktree(repo, repo / ".worktrees" / "codex-interactive", "codex/interactive-merged")

    _create_merged_branch(repo, "codex/active-dispatch-merged", "branches/active-dispatch.txt")
    _add_worktree(
        repo,
        repo / ".worktrees" / "dispatch" / "codex" / "1526-item2-anchor-parity",
        "codex/active-dispatch-merged",
    )
    _write(
        repo / "batch_state" / "tasks" / "1526-item2-anchor-parity.json",
        json.dumps({"task_id": "1526-item2-anchor-parity", "status": "running"}),
    )

    monkeypatch.setattr(git_hygiene_router, "PROJECT_ROOT", repo)
    return repo


def _report(tmp_path: Path, monkeypatch):
    repo = _cleanup_fixture(tmp_path, monkeypatch)
    return git_hygiene_router.compute_git_cleanup(repo)


def test_stale_branch_upstream_gone(tmp_path: Path, monkeypatch) -> None:
    result = _report(tmp_path, monkeypatch)

    stale = {branch.name: branch for branch in result.stale_branches}
    assert stale["codex/upstream-gone"].upstream_gone is True


def test_stale_branch_merged_to_main(tmp_path: Path, monkeypatch) -> None:
    result = _report(tmp_path, monkeypatch)

    stale = {branch.name: branch for branch in result.stale_branches}
    assert stale["codex/merged-stale"].fully_merged_to_main is True


def test_checked_out_branch_not_stale(tmp_path: Path, monkeypatch) -> None:
    result = _report(tmp_path, monkeypatch)

    stale_names = {branch.name for branch in result.stale_branches}
    assert "codex/removable-merged" not in stale_names
    assert "codex/dirty-gone" not in stale_names


def test_main_never_stale(tmp_path: Path, monkeypatch) -> None:
    result = _report(tmp_path, monkeypatch)

    assert "main" not in {branch.name for branch in result.stale_branches}


def test_clean_merged_worktree_is_removable(tmp_path: Path, monkeypatch) -> None:
    result = _report(tmp_path, monkeypatch)

    removable = {worktree.branch: worktree for worktree in result.removable_worktrees}
    assert removable["codex/removable-merged"].clean is True
    assert removable["codex/removable-merged"].fully_merged_to_main is True


def test_dirty_worktree_not_removable(tmp_path: Path, monkeypatch) -> None:
    result = _report(tmp_path, monkeypatch)

    assert "codex/dirty-gone" not in {worktree.branch for worktree in result.removable_worktrees}


def test_interactive_worktree_is_protected(tmp_path: Path, monkeypatch) -> None:
    result = _report(tmp_path, monkeypatch)

    protected = {worktree.branch: worktree for worktree in result.protected_worktrees}
    assert protected["codex/interactive-merged"].reason == "interactive session (contains 'interactive' in path)"
    assert "codex/interactive-merged" not in {worktree.branch for worktree in result.removable_worktrees}


def test_active_dispatch_worktree_is_protected(tmp_path: Path, monkeypatch) -> None:
    result = _report(tmp_path, monkeypatch)

    protected = {worktree.branch: worktree for worktree in result.protected_worktrees}
    assert protected["codex/active-dispatch-merged"].reason == "active dispatch (matches .worktrees/dispatch/**)"
    assert "codex/active-dispatch-merged" not in {worktree.branch for worktree in result.removable_worktrees}


def test_total_reclaimable_sums_correctly(tmp_path: Path, monkeypatch) -> None:
    result = _report(tmp_path, monkeypatch)

    expected = sum(
        worktree.disk_bytes for worktree in result.removable_worktrees if worktree.disk_bytes is not None
    )
    assert result.total_reclaimable_bytes == expected


def test_endpoint_performance_under_budget(tmp_path: Path, monkeypatch) -> None:
    _cleanup_fixture(tmp_path, monkeypatch)

    response = client.get("/api/git/cleanup")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "stale_branches",
        "removable_worktrees",
        "protected_worktrees",
        "total_reclaimable_bytes",
        "computed_at",
        "performance_ms",
    }
    assert body["performance_ms"] < 500
