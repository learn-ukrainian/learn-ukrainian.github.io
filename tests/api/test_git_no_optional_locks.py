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


_GIT_ENV_DROP = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_OPTIONAL_LOCKS",
    "GIT_CONFIG",
    "GIT_CONFIG_COUNT",
    "GIT_CONFIG_PARAMETERS",
    "GIT_TEMPLATE_DIR",
)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, timeout=30)


def _isolate_git_env(monkeypatch: pytest.MonkeyPatch, home: Path) -> None:
    """Run fixture and helper git calls with no inherited configuration or templates."""
    for key in _GIT_ENV_DROP:
        monkeypatch.delenv(key, raising=False)
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    for role in ("AUTHOR", "COMMITTER"):
        monkeypatch.setenv(f"GIT_{role}_NAME", "fixture")
        monkeypatch.setenv(f"GIT_{role}_EMAIL", "fixture@example.invalid")


def _build_stale_index_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    _isolate_git_env(monkeypatch, tmp_path / "home")
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "--template=")
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


@pytest.fixture
def stale_index_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A committed repo whose tracked file has a newer mtime than its index entry."""
    return _build_stale_index_repo(tmp_path, monkeypatch)


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
    "checkout,options",
    [
        (".", lambda root: [f"--git-dir={root / '.git'}", f"--work-tree={root}"]),
        (
            "worktree",
            lambda root: [f"--git-dir={root / 'worktree' / '..' / '.git'}", f"--work-tree={root / 'worktree'}"],
        ),
        ("plain", lambda _root: []),
    ],
)
def test_git_hygiene_invocation_puts_flag_before_subcommand(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, checkout: str, options
) -> None:
    (tmp_path / ".git").mkdir()
    (tmp_path / "worktree").mkdir()
    (tmp_path / "worktree" / ".git").write_text("gitdir: ../.git\n", encoding="utf-8")
    (tmp_path / "plain").mkdir()
    seen: list[list[str]] = []

    def _fake_run(argv: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        seen.append(list(argv))
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    monkeypatch.setattr(git_hygiene_router.subprocess, "run", _fake_run)
    git_hygiene_router._run_git(["status"], cwd=tmp_path / checkout)
    assert seen == [["git", _FLAG, *options(tmp_path), "status"]]


def test_repository_authority_git_passes_flag(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    seen: list[list[str]] = []

    def _fake_run(argv: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        seen.append(list(argv))
        return subprocess.CompletedProcess(argv, 0, stdout="ok\n", stderr="")

    monkeypatch.setattr(repository_authority.subprocess, "run", _fake_run)
    assert repository_authority._git(tmp_path, "rev-parse", "HEAD") == "ok"
    assert seen == [["git", _FLAG, "rev-parse", "HEAD"]]


def test_fixture_ignores_hostile_inherited_git_configuration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Signing with a failing signer, a failing hook template or no identity never reach the fixture."""
    hostile = tmp_path / "hostile"
    hooks = hostile / "templates" / "hooks"
    hooks.mkdir(parents=True)
    (hooks / "pre-commit").write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    (hooks / "pre-commit").chmod(0o755)
    config = hostile / "gitconfig"
    config.write_text(
        f"[commit]\n\tgpgsign = true\n[gpg]\n\tprogram = false\n[init]\n\ttemplateDir = {hostile / 'templates'}\n",
        encoding="utf-8",
    )
    for key in ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(config))
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "commit.gpgsign")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "true")
    monkeypatch.setenv("GIT_TEMPLATE_DIR", str(hostile / "templates"))

    repo = _build_stale_index_repo(tmp_path, monkeypatch)

    assert not (repo / ".git" / "hooks").exists()
    before = _index_fingerprint(repo)
    assert project_state_collect._git(repo, "status", "--porcelain") == ""
    assert _index_fingerprint(repo) == before
