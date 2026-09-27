"""Safety checks for the explicit stale Git lock remover (#8887)."""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

import pytest

from scripts.ops import clear_stale_git_lock as tool


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, timeout=10)
    return tmp_path


def _lock(repo: Path, *, age: int = 601, content: bytes = b"") -> Path:
    path = repo / ".git" / "index.lock"
    path.write_bytes(content)
    old = time.time() - age
    os.utime(path, (old, old))
    return path


def test_dry_run_keeps_eligible_lock(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    lock = _lock(repo)
    monkeypatch.setattr(tool, "_git_process_for_repo", lambda *_: False)
    assert "DRY RUN" in tool.clear_lock(repo)
    assert lock.exists()


def test_apply_removes_old_lock(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    lock = _lock(repo, content=b"stale content")
    monkeypatch.setattr(tool, "_git_process_for_repo", lambda *_: False)
    assert "REMOVED" in tool.clear_lock(repo, apply=True)
    assert not lock.exists()


def test_young_lock_refused(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    lock = _lock(repo, age=60)
    monkeypatch.setattr(tool, "_git_process_for_repo", lambda *_: False)
    with pytest.raises(ValueError, match="younger than 10 minutes"):
        tool.clear_lock(repo, apply=True)
    assert lock.exists()


def test_running_git_refused(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    lock = _lock(repo)
    monkeypatch.setattr(tool, "_git_process_for_repo", lambda *_: True)
    with pytest.raises(ValueError, match="Git process"):
        tool.clear_lock(repo, apply=True)
    assert lock.exists()


def test_git_dash_c_from_other_directory_is_detected(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class GitProcess:
        def name(self) -> str:
            return "git"

        def cmdline(self) -> list[str]:
            return ["git", "-C", str(repo), "status"]

        def cwd(self) -> str:
            return "/tmp"

        def environ(self) -> dict[str, str]:
            return {}

    monkeypatch.setattr(tool.psutil, "process_iter", lambda: [GitProcess()])
    assert tool._git_process_for_repo(repo, repo / ".git")


def test_changed_lock_refused(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    lock = _lock(repo)
    calls = 0

    def change_between_checks(*_args: object) -> bool:
        nonlocal calls
        calls += 1
        if calls == 1:
            lock.write_bytes(b"new")
        return False

    monkeypatch.setattr(tool, "_git_process_for_repo", change_between_checks)
    with pytest.raises(ValueError, match=r"younger than 10 minutes|changed during inspection"):
        tool.clear_lock(repo, apply=True)
    assert lock.read_bytes() == b"new"


@pytest.mark.parametrize("name", ["../index.lock", "other", "/tmp/index.lock"])
def test_lock_name_cannot_escape_git_dir(repo: Path, name: str) -> None:
    with pytest.raises(ValueError, match="basename"):
        tool.clear_lock(repo, name, apply=True)


def test_symlink_lock_refused(repo: Path) -> None:
    target = repo / "valuable"
    target.write_text("keep")
    (repo / ".git" / "index.lock").symlink_to(target)
    with pytest.raises(ValueError, match="regular file"):
        tool.clear_lock(repo, apply=True)
    assert target.read_text() == "keep"
