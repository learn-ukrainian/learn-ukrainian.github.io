"""Monitor API and reporter git helpers never take optional locks (#8874).

A read-only ``git status`` refreshes stale index stat data and writes the
index under ``index.lock``. A caller killed mid-write leaves the lock behind
and blocks every later writer in that checkout. These tests drive the real
helpers against a throwaway repository whose index is stale and prove the
index file is left untouched.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from scripts.api import git_hygiene_router, project_state_collect, repository_authority, worktrees_router

_FLAG = "--no-optional-locks"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        timeout=30,
    )


@pytest.fixture
def stale_index_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A committed repo whose tracked file has a newer mtime than its index entry."""
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OPTIONAL_LOCKS"):
        monkeypatch.delenv(key, raising=False)
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    tracked = repo / "tracked.txt"
    tracked.write_text("content\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-q", "-m", "fixture")
    index = repo / ".git" / "index"
    past = index.stat().st_mtime - 120
    os.utime(index, (past, past))
    future = past + 60
    os.utime(tracked, (future, future))
    return repo


def _index_fingerprint(repo: Path) -> tuple[int, bytes]:
    index = repo / ".git" / "index"
    return index.stat().st_mtime_ns, index.read_bytes()


def test_plain_status_rewrites_a_stale_index(stale_index_repo: Path) -> None:
    """Control: without the flag git refreshes the index, so the fixture is meaningful."""
    before = _index_fingerprint(stale_index_repo)
    _git(stale_index_repo, "status", "--porcelain")
    assert _index_fingerprint(stale_index_repo) != before


def test_project_state_collect_git_leaves_index_untouched(stale_index_repo: Path) -> None:
    before = _index_fingerprint(stale_index_repo)
    assert project_state_collect._git(stale_index_repo, "status", "--porcelain") == ""
    assert _index_fingerprint(stale_index_repo) == before


def test_git_hygiene_run_git_leaves_index_untouched(stale_index_repo: Path) -> None:
    before = _index_fingerprint(stale_index_repo)
    code, stdout, _stderr = git_hygiene_router._run_git(["status", "--porcelain"], cwd=stale_index_repo)
    assert (code, stdout) == (0, "")
    assert _index_fingerprint(stale_index_repo) == before


def test_worktrees_router_status_leaves_index_untouched(stale_index_repo: Path) -> None:
    before = _index_fingerprint(stale_index_repo)
    status = worktrees_router._wt_status(stale_index_repo)
    assert status["dirty"] is False
    assert status["last_commit"]["subject"] == "fixture"
    assert _index_fingerprint(stale_index_repo) == before


@pytest.mark.parametrize(
    "invocation",
    [
        lambda cwd: git_hygiene_router._git_invocation(["status"], cwd),
        lambda cwd: git_hygiene_router._git_invocation(["status"], cwd / "worktree"),
        lambda cwd: git_hygiene_router._git_invocation(["status"], cwd / "plain"),
    ],
)
def test_git_hygiene_invocation_puts_flag_before_subcommand(tmp_path: Path, invocation) -> None:
    (tmp_path / ".git").mkdir()
    (tmp_path / "worktree").mkdir()
    (tmp_path / "worktree" / ".git").write_text("gitdir: ../.git\n", encoding="utf-8")
    (tmp_path / "plain").mkdir()
    argv = invocation(tmp_path)
    assert argv[:2] == ["git", _FLAG]
    assert argv[-1] == "status"


def test_repository_authority_git_passes_flag(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    seen: list[list[str]] = []

    def _fake_run(argv: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        seen.append(list(argv))
        return subprocess.CompletedProcess(argv, 0, stdout="ok\n", stderr="")

    monkeypatch.setattr(repository_authority.subprocess, "run", _fake_run)
    assert repository_authority._git(tmp_path, "rev-parse", "HEAD") == "ok"
    assert seen == [["git", _FLAG, "rev-parse", "HEAD"]]
