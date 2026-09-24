"""A failed or timed-out ``git worktree add`` is undone before dispatch fails (#8663).

Every test runs in a tmp git repository. The timeout is simulated, either by a
fake runner that leaves the half-built state a killed add leaves or by a
``sleep`` stub under tiny bounds; nothing here generates host load.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

import pytest

from scripts import delegate

_REAL_RUN = subprocess.run


def _git_env() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_") and not key.startswith("PRE_COMMIT") and key != "AGENT_NO_MERGE"
    }


def git(cwd: Path, *args: str, check: bool = True) -> str:
    proc = _REAL_RUN(["git", *args], cwd=cwd, capture_output=True, text=True, check=False, env=_git_env())
    if check:
        assert proc.returncode == 0, proc.stderr or proc.stdout
    return (proc.stdout or "").strip()


def _registered(repo: Path) -> set[Path]:
    return {
        Path(line.removeprefix("worktree ")).resolve()
        for line in git(repo, "worktree", "list", "--porcelain").splitlines()
        if line.startswith("worktree ")
    }


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "repo"
    git(tmp_path, "init", "--initial-branch=main", str(root))
    git(root, "config", "user.email", "tester@example.com")
    git(root, "config", "user.name", "Test User")
    (root / ".gitignore").write_text(".worktrees/\nbatch_state/\n", encoding="utf-8")
    for name in ("README.md", "a.txt", "b.txt", "c.txt"):
        (root / name).write_text(f"{name}\n", encoding="utf-8")
    git(root, "add", ".")
    git(root, "commit", "-m", "base")
    monkeypatch.setattr(delegate, "_REPO_ROOT", root.resolve())
    monkeypatch.setattr(delegate, "_TASKS_DIR", root.resolve() / "batch_state" / "tasks")
    monkeypatch.setattr(delegate, "_WORKTREE_LOCK_DIR", tmp_path / "locks")
    return root.resolve()


def _half_built_add(add_command: list[str], *, cwd: Path, worktree_path: Path, env: Any = None):
    """Run the real add, then leave the state a killed add leaves, and time out."""
    proc = _REAL_RUN(add_command, cwd=cwd, capture_output=True, text=True, check=False, env=_git_env())
    assert proc.returncode == 0, proc.stderr
    admin = Path(git(worktree_path, "rev-parse", "--absolute-git-dir"))
    (admin / "locked").write_text("initializing", encoding="utf-8")
    (worktree_path / "b.txt").unlink()
    (worktree_path / "c.txt").unlink()
    (worktree_path / "untracked-by-git.txt").write_text("written before the index\n", encoding="utf-8")
    raise subprocess.TimeoutExpired(add_command, 120.0)


def test_timed_out_add_is_removed_branch_kept_and_recorded(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(delegate, "_run_worktree_add", _half_built_add)
    base_sha = git(repo, "rev-parse", "HEAD")
    task_id = "impl-8663-r1"
    raw_path = str(repo / ".worktrees" / "dispatch" / "claude" / task_id)
    worktree = Path(raw_path)

    # Dispatch holds the worktree lock across preparation; the undo reuses it.
    with delegate.worktree_lock(worktree), pytest.raises(delegate.WorktreeAddFailed) as caught:
        delegate._ensure_worktree(agent="claude", task_id=task_id, raw_path=raw_path, resolved_base_sha=base_sha)

    exc = caught.value
    assert str(exc) == "git worktree add timed out after 120.0s"
    assert exc.cleanup["action"] == "removed"
    assert exc.cleanup["branch_ref_kept"] is True
    assert not worktree.exists()
    assert worktree.resolve() not in _registered(repo)
    assert git(repo, "rev-parse", "--verify", "refs/heads/claude/impl-8663-r1") == base_sha

    wrote = delegate._record_worktree_prep_failure(
        task_id=task_id,
        run_nonce="nonce-8663",
        attribution=type("Attr", (), {"initiator": "test", "source": "test"})(),
        agent="claude",
        mode="workspace-write",
        prompt="probe",
        error=exc,
        worktree_path=str(worktree),
        worktree_prep_cleanup=exc.cleanup,
    )
    assert wrote is True
    record = json.loads(delegate._state_path(task_id).read_text(encoding="utf-8"))
    assert record["status"] == "failed"
    assert record["pid"] is None
    assert record["worktree_prep_cleanup"]["action"] == "removed"
    assert record["worktree_prep_cleanup"]["path"] == str(worktree)


def test_registration_left_without_its_directory_is_pruned(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def add_then_lose_directory(add_command: list[str], *, cwd: Path, worktree_path: Path, env: Any = None):
        proc = _REAL_RUN(add_command, cwd=cwd, capture_output=True, text=True, check=False, env=_git_env())
        assert proc.returncode == 0, proc.stderr
        admin = Path(git(worktree_path, "rev-parse", "--absolute-git-dir"))
        (admin / "locked").write_text("initializing", encoding="utf-8")
        shutil.rmtree(worktree_path)
        raise subprocess.TimeoutExpired(add_command, 120.0)

    monkeypatch.setattr(delegate, "_run_worktree_add", add_then_lose_directory)
    worktree = repo / ".worktrees" / "dispatch" / "claude" / "lost-dir"
    worktree.parent.mkdir(parents=True)

    with pytest.raises(delegate.WorktreeAddFailed) as caught:
        delegate._add_worktree_or_undo(
            ["git", "worktree", "add", "-b", "claude/lost-dir", str(worktree), "main"],
            repo_root=repo,
            worktree_path=worktree,
            task_id="lost-dir",
        )

    assert caught.value.cleanup["action"] == "removed"
    assert caught.value.cleanup["pruned"] is True
    assert worktree.resolve() not in _registered(repo)
    assert git(repo, "rev-parse", "--verify", "refs/heads/claude/lost-dir")


def test_pre_existing_path_is_never_removed(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    existing = repo / ".worktrees" / "dispatch" / "claude" / "already-here"
    existing.parent.mkdir(parents=True)
    git(repo, "worktree", "add", "-b", "claude/already-here", str(existing), "main")
    (existing / "work-in-progress.txt").write_text("keep me\n", encoding="utf-8")

    def timed_out(add_command: list[str], **_kwargs: Any):
        raise subprocess.TimeoutExpired(add_command, 120.0)

    monkeypatch.setattr(delegate, "_run_worktree_add", timed_out)
    with pytest.raises(delegate.WorktreeAddFailed) as caught:
        delegate._add_worktree_or_undo(
            ["git", "worktree", "add", str(existing), "main"],
            repo_root=repo,
            worktree_path=existing,
            task_id="already-here",
        )

    assert caught.value.cleanup["action"] == "skipped"
    assert (existing / "work-in-progress.txt").read_text(encoding="utf-8") == "keep me\n"
    assert existing.resolve() in _registered(repo)


def test_add_that_git_cleaned_up_itself_records_nothing_to_undo(repo: Path) -> None:
    git(repo, "branch", "claude/taken")
    taken_sha = git(repo, "rev-parse", "refs/heads/claude/taken")
    worktree = repo / ".worktrees" / "dispatch" / "claude" / "taken"
    worktree.parent.mkdir(parents=True)

    with pytest.raises(delegate.WorktreeAddFailed) as caught:
        delegate._add_worktree_or_undo(
            ["git", "worktree", "add", "-b", "claude/taken", str(worktree), "main"],
            repo_root=repo,
            worktree_path=worktree,
            task_id="taken",
        )

    assert "already exists" in str(caught.value)
    assert caught.value.cleanup["action"] == "none"
    assert git(repo, "rev-parse", "refs/heads/claude/taken") == taken_sha


def test_undo_refuses_while_another_unfinished_task_claims_the_path(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(delegate, "_run_worktree_add", _half_built_add)
    worktree = repo / ".worktrees" / "dispatch" / "claude" / "claimed"
    worktree.parent.mkdir(parents=True)
    delegate._TASKS_DIR.mkdir(parents=True)
    (delegate._TASKS_DIR / "other.json").write_text(
        json.dumps({"task_id": "other", "status": "running", "worktree_path": str(worktree)}),
        encoding="utf-8",
    )

    with pytest.raises(delegate.WorktreeAddFailed) as caught:
        delegate._add_worktree_or_undo(
            ["git", "worktree", "add", "-b", "claude/claimed", str(worktree), "main"],
            repo_root=repo,
            worktree_path=worktree,
            task_id="claimed",
        )

    assert caught.value.cleanup["action"] == "skipped"
    assert "claimed by active task other" in caught.value.cleanup["reason"]
    assert worktree.exists()


def test_stalled_add_is_stopped_with_its_process_group(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(delegate, "_WORKTREE_ADD_TIMEOUT_S", 0.2)
    monkeypatch.setattr(delegate, "_WORKTREE_ADD_STALL_S", 0.2)
    monkeypatch.setattr(delegate, "_WORKTREE_ADD_MAX_S", 5.0)
    monkeypatch.setattr(delegate, "_WORKTREE_ADD_POLL_S", 0.05)
    monkeypatch.setattr(delegate, "_WORKTREE_ADD_STOP_GRACE_S", 5.0)
    # The child ``sleep`` keeps the output pipes open: the stop returns
    # promptly only when the whole process group is signalled.
    command = ["sh", "-c", "sleep 30 & wait"]

    started = time.monotonic()
    with pytest.raises(subprocess.TimeoutExpired):
        delegate._run_worktree_add(command, cwd=tmp_path, worktree_path=tmp_path / "never-written")

    assert time.monotonic() - started < 4.0


def test_add_that_keeps_writing_outlives_the_base_window(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(delegate, "_WORKTREE_ADD_TIMEOUT_S", 0.2)
    monkeypatch.setattr(delegate, "_WORKTREE_ADD_STALL_S", 0.5)
    monkeypatch.setattr(delegate, "_WORKTREE_ADD_MAX_S", 10.0)
    monkeypatch.setattr(delegate, "_WORKTREE_ADD_POLL_S", 0.05)
    target = tmp_path / "checkout"
    target.mkdir()
    # Writes one file every 0.1 s for ~1.2 s: six times the base window, but
    # never idle for the stall window.
    command = ["sh", "-c", f'for i in 1 2 3 4 5 6 7 8 9 10 11 12; do : > "{target}/f$i"; sleep 0.1; done']

    proc = delegate._run_worktree_add(command, cwd=tmp_path, worktree_path=target)

    assert proc.returncode == 0
    assert len(list(target.iterdir())) == 12
