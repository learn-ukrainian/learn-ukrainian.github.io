"""A failed or timed-out ``git worktree add`` is undone only on ownership proof (#8663).

Dispatch reserves the path with ``mkdir`` and records the reservation before
git starts, with the reserved directory's inode, git's admin directory, git's
and the dispatcher's (pid, start time), and the base commit. The undo removes
a registered worktree only while git still holds its ``initializing`` lock,
once git is proven exited, while the path is still the reserved inode under
the recorded admin directory, and only when the tree holds nothing but an
unfinished checkout; a path this run did not reserve is never touched.

Every test runs in a tmp git repository. Slowness is simulated, by a fake
runner that leaves the half-built state a killed add leaves, by ``sleep``
stubs, or by a slow smudge filter behind a ``git`` wrapper, under tiny
bounds; nothing here generates host load.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest

from scripts import delegate
from scripts.orchestration import worktree_prep
from tests.worktree_prep_helpers import leave_half_built

_REAL_RUN = subprocess.run
_NONCE = "nonce-8663"


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


def _record(task_id: str) -> dict[str, Any] | None:
    path = delegate._state_path(task_id)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


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


def _dispatch_path(repo: Path, name: str) -> Path:
    path = repo / ".worktrees" / "dispatch" / "claude" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _report_git_spawned_then_exited(on_spawn: Any) -> None:
    """Hand dispatch the identity of a stand-in git that then exits, as the real add does."""
    stand_in = subprocess.Popen(["sleep", "30"], start_new_session=True)
    try:
        on_spawn(stand_in.pid)
    finally:
        stand_in.kill()
        stand_in.wait()


def _half_built_add(add_command: list[str], *, cwd: Path, worktree_path: Path, exited: bool = True, **kwargs: Any):
    """Run the real add, then leave the state a killed add leaves, and time out."""
    _report_git_spawned_then_exited(kwargs["on_spawn"])
    proc = _REAL_RUN(add_command, cwd=cwd, capture_output=True, text=True, check=False, env=_git_env())
    assert proc.returncode == 0, proc.stderr
    leave_half_built(worktree_path, drop=("b.txt", "c.txt"))
    raise delegate.WorktreeAddTimeout(add_command, 120.0, git_exited=exited)


def test_timed_out_add_is_removed_branch_kept_and_recorded(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    task_id = "impl-8663-r1"
    seen_before_git: list[dict[str, Any] | None] = []

    def half_built_after_checking_the_record(add_command: list[str], **kwargs: Any):
        # The reservation is on disk and in the task record before git runs.
        assert kwargs["worktree_path"].is_dir()
        assert not any(kwargs["worktree_path"].iterdir())
        seen_before_git.append(_record(task_id))
        _half_built_add(add_command, **kwargs)

    monkeypatch.setattr(delegate, "_run_worktree_add", half_built_after_checking_the_record)
    base_sha = git(repo, "rev-parse", "HEAD")
    raw_path = str(repo / ".worktrees" / "dispatch" / "claude" / task_id)
    worktree = Path(raw_path)

    # Dispatch holds the worktree lock across preparation; the undo reuses it.
    with delegate.worktree_lock(worktree), pytest.raises(delegate.WorktreeAddFailed) as caught:
        delegate._ensure_worktree(
            agent="claude",
            task_id=task_id,
            raw_path=raw_path,
            resolved_base_sha=base_sha,
            run_nonce=_NONCE,
        )

    [provisional] = seen_before_git
    assert provisional is not None
    assert provisional["status"] == "spawning"
    assert provisional["pid"] is None
    assert provisional["run_nonce"] == _NONCE
    reserved = provisional["worktree_prep"]
    assert reserved["reserved_by_mkdir"] is True
    assert reserved["run_nonce"] == _NONCE
    assert reserved["path"] == str(worktree)
    assert reserved["base_sha"] == base_sha
    assert isinstance(reserved["dir_ino"], int)
    assert reserved["owner_pid"] == os.getpid()
    assert isinstance(reserved["owner_start"], int)
    assert reserved["git_pid"] is None
    assert reserved["git_admin_dir"] == ""

    exc = caught.value
    assert str(exc) == "git worktree add timed out after 120.0s"
    assert exc.cleanup["action"] == "removed"
    assert exc.cleanup["branch_ref_kept"] is True
    assert exc.prep is not None
    # git's identity and admin directory were added to the reservation.
    assert {key: exc.prep[key] for key in reserved if key not in ("git_pid", "git_start", "git_admin_dir")} == {
        key: value for key, value in reserved.items() if key not in ("git_pid", "git_start", "git_admin_dir")
    }
    assert isinstance(exc.prep["git_pid"], int)
    assert isinstance(exc.prep["git_start"], int)
    assert Path(exc.prep["git_admin_dir"]).parent == repo / ".git" / "worktrees"
    assert not worktree.exists()
    assert worktree.resolve() not in _registered(repo)
    assert git(repo, "rev-parse", "--verify", "refs/heads/claude/impl-8663-r1") == base_sha

    # Dispatch then replaces its own provisional record with the failed one.
    wrote = delegate._record_worktree_prep_failure(
        task_id=task_id,
        run_nonce=_NONCE,
        attribution=type("Attr", (), {"initiator": "test", "source": "test"})(),
        agent="claude",
        mode="workspace-write",
        prompt="probe",
        error=exc,
        worktree_path=str(worktree),
        worktree_prep_cleanup=exc.cleanup,
        worktree_prep=exc.prep,
    )
    assert wrote is True
    record = _record(task_id)
    assert record is not None
    assert record["status"] == "failed"
    assert record["pid"] is None
    assert record["worktree_prep"] == exc.prep
    assert record["worktree_prep_cleanup"]["action"] == "removed"
    assert record["worktree_prep_cleanup"]["path"] == str(worktree)


def test_failure_record_never_overwrites_another_runs_live_record(repo: Path) -> None:
    delegate._TASKS_DIR.mkdir(parents=True)
    other = {
        "task_id": "shared",
        "run_nonce": "another-run",
        "status": "spawning",
        "pid": None,
        "worktree_prep": {"path": "/x", "run_nonce": "another-run", "reserved_by_mkdir": True},
    }
    delegate._state_path("shared").write_text(json.dumps(other), encoding="utf-8")

    wrote = delegate._record_worktree_prep_failure(
        task_id="shared",
        run_nonce=_NONCE,
        attribution=type("Attr", (), {"initiator": "test", "source": "test"})(),
        agent="claude",
        mode="workspace-write",
        prompt="probe",
        error="boom",
    )

    assert wrote is False
    assert _record("shared") == other


def test_successful_add_retires_the_reservation_record(repo: Path) -> None:
    worktree = _dispatch_path(repo, "ok")

    proc = delegate._add_worktree_or_undo(
        ["git", "worktree", "add", "-b", "claude/ok", str(worktree), "main"],
        repo_root=repo,
        worktree_path=worktree,
        task_id="ok",
        run_nonce=_NONCE,
    )

    assert proc.returncode == 0
    assert worktree.resolve() in _registered(repo)
    assert _record("ok") is None


def test_registration_left_without_its_directory_is_kept(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """With the reserved directory gone, nothing proves whose registration remains."""

    def add_then_lose_directory(add_command: list[str], *, cwd: Path, worktree_path: Path, **kwargs: Any):
        _report_git_spawned_then_exited(kwargs["on_spawn"])
        proc = _REAL_RUN(add_command, cwd=cwd, capture_output=True, text=True, check=False, env=_git_env())
        assert proc.returncode == 0, proc.stderr
        leave_half_built(worktree_path)
        shutil.rmtree(worktree_path)
        raise delegate.WorktreeAddTimeout(add_command, 120.0, git_exited=True)

    monkeypatch.setattr(delegate, "_run_worktree_add", add_then_lose_directory)
    worktree = _dispatch_path(repo, "lost-dir")

    with pytest.raises(delegate.WorktreeAddFailed) as caught:
        delegate._add_worktree_or_undo(
            ["git", "worktree", "add", "-b", "claude/lost-dir", str(worktree), "main"],
            repo_root=repo,
            worktree_path=worktree,
            task_id="lost-dir",
        )

    assert caught.value.cleanup["action"] == "skipped"
    assert "device/inode differ" in caught.value.cleanup["reason"]
    assert worktree.resolve() in _registered(repo)


def test_pre_existing_path_is_never_passed_to_git_or_removed(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    existing = _dispatch_path(repo, "already-here")
    git(repo, "worktree", "add", "-b", "claude/already-here", str(existing), "main")
    (existing / "work-in-progress.txt").write_text("keep me\n", encoding="utf-8")

    def must_not_run(add_command: list[str], **_kwargs: Any):
        raise AssertionError("git worktree add ran against a path this call did not reserve")

    monkeypatch.setattr(delegate, "_run_worktree_add", must_not_run)
    with pytest.raises(delegate.WorktreeAddFailed) as caught:
        delegate._add_worktree_or_undo(
            ["git", "worktree", "add", str(existing), "main"],
            repo_root=repo,
            worktree_path=existing,
            task_id="already-here",
            run_nonce=_NONCE,
        )

    assert caught.value.cleanup["action"] == "skipped"
    assert caught.value.prep is None
    assert (existing / "work-in-progress.txt").read_text(encoding="utf-8") == "keep me\n"
    assert existing.resolve() in _registered(repo)
    assert _record("already-here") is None


def test_completed_worktree_made_in_the_reserved_path_is_never_removed(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Review blocker: someone else's finished worktree at the path survives a failed add."""
    worktree = _dispatch_path(repo, "raced")

    def human_wins_the_race(add_command: list[str], *, cwd: Path, worktree_path: Path, **_kwargs: Any):
        # git accepts the empty reserved directory, so another add can land in it.
        git(repo, "worktree", "add", "-b", "human/raced", str(worktree_path), "main")
        (worktree_path / "uncommitted-human-work.txt").write_text("keep me\n", encoding="utf-8")
        return _REAL_RUN(add_command, cwd=cwd, capture_output=True, text=True, check=False, env=_git_env())

    monkeypatch.setattr(delegate, "_run_worktree_add", human_wins_the_race)
    with pytest.raises(delegate.WorktreeAddFailed) as caught:
        delegate._add_worktree_or_undo(
            ["git", "worktree", "add", "-b", "claude/raced", str(worktree), "main"],
            repo_root=repo,
            worktree_path=worktree,
            task_id="raced",
        )

    assert caught.value.cleanup["action"] == "skipped"
    assert "not locked 'initializing'" in caught.value.cleanup["reason"]
    assert (worktree / "uncommitted-human-work.txt").read_text(encoding="utf-8") == "keep me\n"
    assert worktree.resolve() in _registered(repo)


def test_reserved_path_recreated_by_another_add_is_kept(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Review blocker: the path string is not ownership once the reserved inode is gone."""
    worktree = _dispatch_path(repo, "recreated")

    def path_recreated_by_someone_else(add_command: list[str], *, cwd: Path, worktree_path: Path, **kwargs: Any):
        _report_git_spawned_then_exited(kwargs["on_spawn"])
        # This run's git failed before writing; someone removes the empty
        # reservation and their own add lands at the path and is itself killed.
        os.rmdir(worktree_path)
        git(repo, "worktree", "add", "-b", "human/recreated", str(worktree_path), "main")
        leave_half_built(worktree_path, drop=("b.txt",))
        raise delegate.WorktreeAddTimeout(add_command, 120.0, git_exited=True)

    monkeypatch.setattr(delegate, "_run_worktree_add", path_recreated_by_someone_else)
    with pytest.raises(delegate.WorktreeAddFailed) as caught:
        delegate._add_worktree_or_undo(
            ["git", "worktree", "add", "-b", "claude/recreated", str(worktree), "main"],
            repo_root=repo,
            worktree_path=worktree,
            task_id="recreated",
            run_nonce=_NONCE,
        )

    assert caught.value.cleanup["action"] == "skipped"
    assert "device/inode differ" in caught.value.cleanup["reason"]
    # The other add's admin directory was never recorded as this run's.
    assert caught.value.prep is not None
    assert caught.value.prep["git_admin_dir"] == ""
    assert worktree.resolve() in _registered(repo)
    assert (worktree / "a.txt").exists()


def test_completed_checkout_locked_initializing_with_work_is_kept(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Review blocker: the ``initializing`` lock alone never proves the checkout is unfinished."""

    def completed_then_locked(add_command: list[str], *, cwd: Path, worktree_path: Path, **kwargs: Any):
        _report_git_spawned_then_exited(kwargs["on_spawn"])
        proc = _REAL_RUN(add_command, cwd=cwd, capture_output=True, text=True, check=False, env=_git_env())
        assert proc.returncode == 0, proc.stderr
        git(repo, "worktree", "lock", "--reason", "initializing", str(worktree_path))
        (worktree_path / "a.txt").write_text("uncommitted work\n", encoding="utf-8")
        raise delegate.WorktreeAddTimeout(add_command, 120.0, git_exited=True)

    monkeypatch.setattr(delegate, "_run_worktree_add", completed_then_locked)
    worktree = _dispatch_path(repo, "completed")

    with pytest.raises(delegate.WorktreeAddFailed) as caught:
        delegate._add_worktree_or_undo(
            ["git", "worktree", "add", "-b", "claude/completed", str(worktree), "main"],
            repo_root=repo,
            worktree_path=worktree,
            task_id="completed",
        )

    assert caught.value.cleanup["action"] == "skipped"
    assert "no proof the checkout never completed: tracked change ' M' at a.txt" in caught.value.cleanup["reason"]
    assert (worktree / "a.txt").read_text(encoding="utf-8") == "uncommitted work\n"
    assert worktree.resolve() in _registered(repo)


def test_git_still_alive_keeps_the_half_built_tree(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Review blocker: nothing is removed while the recorded git (pid, start time) still runs."""
    still_running = subprocess.Popen(["sleep", "30"], start_new_session=True)

    def half_built_git_alive(add_command: list[str], *, cwd: Path, worktree_path: Path, **kwargs: Any):
        kwargs["on_spawn"](still_running.pid)
        proc = _REAL_RUN(add_command, cwd=cwd, capture_output=True, text=True, check=False, env=_git_env())
        assert proc.returncode == 0, proc.stderr
        leave_half_built(worktree_path, drop=("b.txt",))
        raise delegate.WorktreeAddTimeout(add_command, 120.0, git_exited=True)

    monkeypatch.setattr(delegate, "_run_worktree_add", half_built_git_alive)
    worktree = _dispatch_path(repo, "alive")
    try:
        with pytest.raises(delegate.WorktreeAddFailed) as caught:
            delegate._add_worktree_or_undo(
                ["git", "worktree", "add", "-b", "claude/alive", str(worktree), "main"],
                repo_root=repo,
                worktree_path=worktree,
                task_id="alive",
                run_nonce=_NONCE,
            )
        assert caught.value.cleanup["undo_skipped"] == "git_not_confirmed_exited"
        assert worktree.exists()
        assert caught.value.prep is not None
        assert caught.value.prep["git_pid"] == still_running.pid
        assert worktree_prep.git_gone(caught.value.prep) is False
    finally:
        still_running.kill()
        still_running.wait()
    assert worktree_prep.git_gone(caught.value.prep) is True


def test_git_not_confirmed_exited_skips_the_undo(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def half_built_still_running(add_command: list[str], **kwargs: Any):
        _half_built_add(add_command, exited=False, **kwargs)

    monkeypatch.setattr(delegate, "_run_worktree_add", half_built_still_running)
    worktree = _dispatch_path(repo, "stuck")

    with pytest.raises(delegate.WorktreeAddFailed) as caught:
        delegate._add_worktree_or_undo(
            ["git", "worktree", "add", "-b", "claude/stuck", str(worktree), "main"],
            repo_root=repo,
            worktree_path=worktree,
            task_id="stuck",
            run_nonce=_NONCE,
        )

    assert caught.value.cleanup["action"] == "skipped"
    assert caught.value.cleanup["undo_skipped"] == "git_not_confirmed_exited"
    assert worktree.exists()
    assert worktree.resolve() in _registered(repo)
    # The reservation stays recorded, so the reaper can prove ownership later.
    assert caught.value.prep is not None
    record = _record("stuck")
    assert record is not None
    assert record["worktree_prep"] == caught.value.prep


def test_add_that_git_cleaned_up_itself_releases_only_the_empty_reservation(repo: Path) -> None:
    git(repo, "branch", "claude/taken")
    taken_sha = git(repo, "rev-parse", "refs/heads/claude/taken")
    worktree = _dispatch_path(repo, "taken")

    with pytest.raises(delegate.WorktreeAddFailed) as caught:
        delegate._add_worktree_or_undo(
            ["git", "worktree", "add", "-b", "claude/taken", str(worktree), "main"],
            repo_root=repo,
            worktree_path=worktree,
            task_id="taken",
        )

    assert "already exists" in str(caught.value)
    assert caught.value.cleanup["action"] == "removed"
    assert caught.value.cleanup["reason"] == "git registered no worktree; removed the empty path reservation"
    assert not worktree.exists()
    assert git(repo, "rev-parse", "refs/heads/claude/taken") == taken_sha


def test_undo_refuses_while_another_unfinished_task_claims_the_path(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(delegate, "_run_worktree_add", _half_built_add)
    worktree = _dispatch_path(repo, "claimed")
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


# --- the real ``git`` Popen path -------------------------------------------------------------


def _slow_git(repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, block_sigterm: bool) -> None:
    """Put a ``git`` wrapper on PATH and make every checkout stall mid-add.

    The repository's smudge filter sleeps, so ``git worktree add`` stops
    after creating the branch and registering the worktree under its
    ``initializing`` lock, halfway through the checkout. With
    ``block_sigterm`` the wrapper execs the real git with SIGTERM blocked, so
    git's own cleanup never runs and only SIGKILL stops it, exactly the
    killed add of #8663.
    """
    real_git = shutil.which("git")
    assert real_git is not None
    git(repo, "config", "filter.slow.smudge", "sleep 30; cat")
    (repo / ".git" / "info" / "attributes").write_text("*.txt filter=slow\n", encoding="utf-8")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    wrapper = bin_dir / "git"
    exec_real = (
        f'exec "{sys.executable}" -c "import os, signal, sys; '
        f'signal.pthread_sigmask(signal.SIG_BLOCK, {{signal.SIGTERM}}); os.execv(sys.argv[1], sys.argv[1:])" '
        f'"{real_git}" "$@"'
        if block_sigterm
        else f'exec "{real_git}" "$@"'
    )
    wrapper.write_text(
        "#!/bin/sh\n"
        f'if [ "$1" = worktree ] && [ "$2" = add ]; then\n  sleep 0.05\n  {exec_real}\nfi\n'
        f'exec "{real_git}" "$@"\n',
        encoding="utf-8",
    )
    wrapper.chmod(wrapper.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setattr(delegate, "_WORKTREE_ADD_TIMEOUT_S", 0.5)
    monkeypatch.setattr(delegate, "_WORKTREE_ADD_STALL_S", 0.3)
    monkeypatch.setattr(delegate, "_WORKTREE_ADD_MAX_S", 5.0)
    monkeypatch.setattr(delegate, "_WORKTREE_ADD_POLL_S", 0.05)
    monkeypatch.setattr(delegate, "_WORKTREE_ADD_STOP_GRACE_S", 0.5)


def test_real_git_add_killed_mid_checkout_is_undone_and_branch_kept(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _slow_git(repo, tmp_path, monkeypatch, block_sigterm=True)
    base_sha = git(repo, "rev-parse", "HEAD")
    worktree = _dispatch_path(repo, "killed")
    observed: dict[str, Any] = {}
    real_undo = delegate._undo_failed_worktree_add

    def observe_then_undo(path: Path, **kwargs: Any) -> dict[str, Any]:
        observed["registration"] = delegate._worktree_registration(repo, path)
        observed["git_exited"] = kwargs["git_exited"]
        return real_undo(path, **kwargs)

    monkeypatch.setattr(delegate, "_undo_failed_worktree_add", observe_then_undo)

    started = time.monotonic()
    with pytest.raises(delegate.WorktreeAddFailed) as caught:
        delegate._add_worktree_or_undo(
            ["git", "worktree", "add", "-b", "claude/killed", str(worktree), base_sha],
            repo_root=repo,
            worktree_path=worktree,
            task_id="killed",
            run_nonce=_NONCE,
        )

    assert time.monotonic() - started < 10.0
    assert str(caught.value).startswith("git worktree add timed out after ")
    # SIGKILL left what the incident left: registered, still locked by the add.
    assert observed == {"registration": (True, "initializing"), "git_exited": True}
    assert caught.value.cleanup["action"] == "removed"
    assert not worktree.exists()
    assert worktree.resolve() not in _registered(repo)
    assert git(repo, "rev-parse", "--verify", "refs/heads/claude/killed") == base_sha
    record = _record("killed")
    assert record is not None
    prep = record["worktree_prep"]
    assert prep["reserved_by_mkdir"] is True
    # The real add's identities were recorded while it ran.
    assert isinstance(prep["git_pid"], int)
    assert isinstance(prep["git_start"], int)
    assert prep["git_admin_dir"].startswith(str(repo / ".git" / "worktrees"))
    assert prep["base_sha"] == base_sha


def test_real_git_add_stopped_by_sigterm_cleans_up_after_itself(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _slow_git(repo, tmp_path, monkeypatch, block_sigterm=False)
    worktree = _dispatch_path(repo, "termed")

    with pytest.raises(delegate.WorktreeAddFailed) as caught:
        delegate._add_worktree_or_undo(
            ["git", "worktree", "add", "-b", "claude/termed", str(worktree), "main"],
            repo_root=repo,
            worktree_path=worktree,
            task_id="termed",
        )

    assert caught.value.cleanup["action"] == "none"
    assert not worktree.exists()
    assert worktree.resolve() not in _registered(repo)
    assert git(repo, "rev-parse", "--verify", "refs/heads/claude/termed")


# --- the bounded add itself ------------------------------------------------------------------


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
    with pytest.raises(delegate.WorktreeAddTimeout) as caught:
        delegate._run_worktree_add(command, cwd=tmp_path, worktree_path=tmp_path / "never-written")

    assert time.monotonic() - started < 4.0
    assert caught.value.git_exited is True


def test_stop_reports_a_process_that_outlives_sigkill(monkeypatch: pytest.MonkeyPatch) -> None:
    signals: list[int] = []
    monkeypatch.setattr(delegate.os, "killpg", lambda _pid, sig: signals.append(sig))
    monkeypatch.setattr(delegate, "_WORKTREE_ADD_STOP_GRACE_S", 0.01)

    class Unkillable:
        pid = 999_999_999

        def communicate(self, timeout: float):
            raise subprocess.TimeoutExpired(["git"], timeout)

    assert delegate._stop_worktree_add(Unkillable()) is False  # type: ignore[arg-type]
    assert signals == [delegate.signal.SIGTERM, delegate.signal.SIGKILL]


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
