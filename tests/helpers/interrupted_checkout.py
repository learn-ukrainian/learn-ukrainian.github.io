"""Shared interrupted dispatch checkout used by orchestration tests."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pytest


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True, timeout=30
    ).stdout.strip()


def hashes(paths):
    return tuple(hashlib.sha256(path.read_bytes()).hexdigest() for path in paths)


def make_interrupted_checkout(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.name", "Caller Test")
    git(repo, "config", "user.email", "caller@example.invalid")
    (repo / "base").write_text("base")
    git(repo, "add", "base")
    git(repo, "commit", "-m", "base")
    remote = tmp_path / "origin.git"
    git(repo, "init", "--bare", str(remote))
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "-u", "origin", "main")
    (repo / ".git/info/exclude").write_text("batch_state/\n.cache/\n.worktrees/\n")
    tree = repo / ".worktrees/dispatch/codex/interrupted"
    git(repo, "worktree", "add", "-b", "codex/interrupted", str(tree), "main")
    (tree / "unique.txt").write_bytes(b"unique commit\x00\xff")
    git(tree, "add", "unique.txt")
    git(tree, "commit", "-m", "unique work")
    tasks = repo / "batch_state/tasks"
    tasks.mkdir(parents=True)
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    from scripts.common import task_store_paths

    monkeypatch.setattr(task_store_paths, "tasks_dir", lambda: tasks)
    record = tasks / "interrupted.json"
    result = record.with_suffix(".result")
    result.write_text("Український звіт\u2028recoverable result\n", encoding="utf-8")
    output = tree / ".cache/output.bin"
    output.parent.mkdir()
    output.write_bytes(b"ignored output\x00\xff")
    from scripts.orchestration import reap_worktrees as rw

    monkeypatch.setattr(rw, "_active_task_ids", lambda: set())
    monkeypatch.setattr(rw, "_live_cwd_paths", lambda _repo: set())
    monkeypatch.setattr(rw, "_query_pr_states", lambda *_args: ([], None))
    monkeypatch.setattr(rw, "_query_prs_by_head_sha", lambda *_args, **_kw: ([], None))
    return repo, tree, tasks, record, result, output


@pytest.fixture
def interrupted_checkout(tmp_path, monkeypatch):
    return make_interrupted_checkout(tmp_path, monkeypatch)
