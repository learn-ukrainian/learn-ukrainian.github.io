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

from scripts.api import project_state_collect

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


def test_project_state_collect_git_leaves_index_untouched(stale_index_repo: Path) -> None:
    before = _index_fingerprint(stale_index_repo)
    assert project_state_collect._git(stale_index_repo, "status", "--porcelain") == ""
    assert _index_fingerprint(stale_index_repo) == before
