"""A failed ``git worktree add`` never has a registered worktree removed for it (#8663).

Dispatch reserves the path with ``mkdir`` and records the reservation before
git starts. A slow add is stopped with SIGTERM first, so git's own signal
cleanup deletes its partial worktree and admin directory; SIGKILL follows
only after a grace. Dispatch then removes nothing, not even the empty
directory it reserved: git 2.53 can register another add there while it is
still empty, so the directory is left as it is and ``reserved_dir_left``
records that. A worktree git left registered is reported as
``needs_attention: initializing_leftover`` with a "verify first:" removal
command, never removed, unlocked or pruned.

Every test runs in a tmp git repository. Slowness is simulated, by a fake
runner that leaves the state a killed add leaves, by ``sleep`` stubs, or by a
slow smudge filter or ``reference-transaction`` hook behind a ``git``
wrapper, under tiny bounds; nothing here generates host load.
"""

from __future__ import annotations

import ast
import inspect
import json
import os
import shutil
import signal
import stat
import subprocess
import sys
import textwrap
import time
from pathlib import Path
from typing import Any

import pytest

from scripts import delegate
from scripts.fleet import post_task_reap
from scripts.orchestration import reap_worktrees, reaper_lifecycle, worktree_prep
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


def _assert_leftover_reported(cleanup: dict[str, Any], repo: Path, worktree: Path) -> None:
    assert cleanup["action"] == "skipped"
    assert cleanup["needs_attention"] == worktree_prep.LEFTOVER_KIND
    assert cleanup["lock_reason"] == "initializing"
    assert cleanup["command"] == worktree_prep.verify_first_command(repo, worktree)
    assert cleanup["command"].startswith("verify first: ")
    assert cleanup["branch_ref_kept"] is True


def test_reservation_recorded_before_git_and_a_leftover_is_reported_not_removed(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
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

    exc = caught.value
    assert str(exc) == "git worktree add timed out after 120.0s"
    _assert_leftover_reported(exc.cleanup, repo, worktree)
    assert exc.prep is not None
    assert {key: exc.prep[key] for key in reserved if key not in ("git_pid", "git_start")} == {
        key: value for key, value in reserved.items() if key not in ("git_pid", "git_start")
    }
    assert isinstance(exc.prep["git_pid"], int)
    assert isinstance(exc.prep["git_start"], int)
    # Registered, locked, and left exactly as git left it.
    assert (worktree / "a.txt").exists()
    assert delegate._worktree_registration(repo, worktree) == (True, "initializing")
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
    assert record["worktree_prep_cleanup"] == exc.cleanup


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

    proc = delegate._add_reserved_worktree(
        ["git", "worktree", "add", "-b", "claude/ok", str(worktree), "main"],
        repo_root=repo,
        worktree_path=worktree,
        task_id="ok",
        run_nonce=_NONCE,
    )

    assert proc.returncode == 0
    assert worktree.resolve() in _registered(repo)
    assert _record("ok") is None


def test_registration_left_without_its_directory_is_reported(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
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
        delegate._add_reserved_worktree(
            ["git", "worktree", "add", "-b", "claude/lost-dir", str(worktree), "main"],
            repo_root=repo,
            worktree_path=worktree,
            task_id="lost-dir",
        )

    _assert_leftover_reported(caught.value.cleanup, repo, worktree)
    # Not pruned either: the registration stays for a human to inspect.
    assert worktree.resolve() in _registered(repo)


def test_pre_existing_path_is_never_passed_to_git_or_removed(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    existing = _dispatch_path(repo, "already-here")
    git(repo, "worktree", "add", "-b", "claude/already-here", str(existing), "main")
    (existing / "work-in-progress.txt").write_text("keep me\n", encoding="utf-8")

    def must_not_run(add_command: list[str], **_kwargs: Any):
        raise AssertionError("git worktree add ran against a path this call did not reserve")

    monkeypatch.setattr(delegate, "_run_worktree_add", must_not_run)
    with pytest.raises(delegate.WorktreeAddFailed) as caught:
        delegate._add_reserved_worktree(
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
    worktree = _dispatch_path(repo, "raced")

    def human_wins_the_race(add_command: list[str], *, cwd: Path, worktree_path: Path, **_kwargs: Any):
        # git accepts the empty reserved directory, so another add can land in it.
        git(repo, "worktree", "add", "-b", "human/raced", str(worktree_path), "main")
        (worktree_path / "uncommitted-human-work.txt").write_text("keep me\n", encoding="utf-8")
        return _REAL_RUN(add_command, cwd=cwd, capture_output=True, text=True, check=False, env=_git_env())

    monkeypatch.setattr(delegate, "_run_worktree_add", human_wins_the_race)
    with pytest.raises(delegate.WorktreeAddFailed) as caught:
        delegate._add_reserved_worktree(
            ["git", "worktree", "add", "-b", "claude/raced", str(worktree), "main"],
            repo_root=repo,
            worktree_path=worktree,
            task_id="raced",
        )

    cleanup = caught.value.cleanup
    assert cleanup["action"] == "skipped"
    assert "needs_attention" not in cleanup
    assert cleanup["reason"] == "git left a registered worktree (lock=None); never removed automatically"
    assert (worktree / "uncommitted-human-work.txt").read_text(encoding="utf-8") == "keep me\n"
    assert worktree.resolve() in _registered(repo)


def test_git_not_confirmed_exited_touches_nothing(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def still_running(add_command: list[str], **kwargs: Any):
        _report_git_spawned_then_exited(kwargs["on_spawn"])
        raise delegate.WorktreeAddTimeout(add_command, 120.0, git_exited=False)

    monkeypatch.setattr(delegate, "_run_worktree_add", still_running)
    worktree = _dispatch_path(repo, "stuck")

    with pytest.raises(delegate.WorktreeAddFailed) as caught:
        delegate._add_reserved_worktree(
            ["git", "worktree", "add", "-b", "claude/stuck", str(worktree), "main"],
            repo_root=repo,
            worktree_path=worktree,
            task_id="stuck",
            run_nonce=_NONCE,
        )

    assert caught.value.cleanup["action"] == "skipped"
    assert caught.value.cleanup["git_exited"] is False
    # Even the empty reservation stays: git might still write into it.
    assert worktree.is_dir()
    record = _record("stuck")
    assert record is not None
    assert record["worktree_prep"] == caught.value.prep


def test_add_that_git_refused_leaves_the_empty_reservation_in_place(repo: Path) -> None:
    git(repo, "branch", "claude/taken")
    taken_sha = git(repo, "rev-parse", "refs/heads/claude/taken")
    worktree = _dispatch_path(repo, "taken")

    with pytest.raises(delegate.WorktreeAddFailed) as caught:
        delegate._add_reserved_worktree(
            ["git", "worktree", "add", "-b", "claude/taken", str(worktree), "main"],
            repo_root=repo,
            worktree_path=worktree,
            task_id="taken",
            run_nonce=_NONCE,
        )

    assert "already exists" in str(caught.value)
    cleanup = caught.value.cleanup
    assert cleanup["action"] == "skipped"
    assert (
        cleanup["reason"] == "git registered no worktree; reserved directory left in place, never removed automatically"
    )
    assert cleanup["reserved_dir_left"] is True
    assert caught.value.prep is not None
    assert caught.value.prep["reserved_dir_left"] is True
    # The provisional record carries it too, before dispatch writes the failed one.
    record = _record("taken")
    assert record is not None
    assert record["worktree_prep"]["reserved_dir_left"] is True
    assert worktree.is_dir()
    assert not any(worktree.iterdir())
    assert git(repo, "rev-parse", "refs/heads/claude/taken") == taken_sha


@pytest.mark.parametrize("left", ["empty", "not-empty", "another-inode"])
def test_unregistered_reservation_is_left_as_it_is(repo: Path, monkeypatch: pytest.MonkeyPatch, left: str) -> None:
    def leaves_a_file(add_command: list[str], *, worktree_path: Path, **kwargs: Any):
        _report_git_spawned_then_exited(kwargs["on_spawn"])
        if left == "another-inode":
            # Made before the reservation goes, so it is surely another inode.
            replacement = worktree_path.with_name("replacement")
            replacement.mkdir()
            os.rmdir(worktree_path)
            replacement.rename(worktree_path)
        elif left == "not-empty":
            (worktree_path / "someone-elses.txt").write_text("keep me\n", encoding="utf-8")
        return subprocess.CompletedProcess(add_command, 128, "", "fatal: simulated")

    monkeypatch.setattr(delegate, "_run_worktree_add", leaves_a_file)
    worktree = _dispatch_path(repo, "leftover-dir")

    with pytest.raises(delegate.WorktreeAddFailed) as caught:
        delegate._add_reserved_worktree(
            ["git", "worktree", "add", "-b", "claude/leftover-dir", str(worktree), "main"],
            repo_root=repo,
            worktree_path=worktree,
            task_id="leftover-dir",
        )

    assert caught.value.cleanup["action"] == "skipped"
    assert caught.value.cleanup["reserved_dir_left"] is True
    assert worktree.is_dir()
    if left == "not-empty":
        assert (worktree / "someone-elses.txt").read_text(encoding="utf-8") == "keep me\n"


def _forbid_removing(monkeypatch: pytest.MonkeyPatch, reserved: Path) -> None:
    """Fail on any removal syscall aimed at ``reserved`` (the runtime twin of the static test)."""
    target = os.path.realpath(reserved)

    def guard(name: str, real: Any) -> Any:
        def checked(path: Any, *args: Any, **kwargs: Any) -> Any:
            if os.path.realpath(os.fspath(path)) == target:
                raise AssertionError(f"{name} of the reserved path {reserved}")
            return real(path, *args, **kwargs)

        return checked

    for module, name in ((os, "rmdir"), (os, "unlink"), (os, "remove"), (os, "removedirs"), (shutil, "rmtree")):
        monkeypatch.setattr(module, name, guard(name, getattr(module, name)))
    for name in ("rmdir", "unlink"):
        monkeypatch.setattr(Path, name, guard(f"Path.{name}", getattr(Path, name)))


def _register_empty_path_as_another_add(repo: Path, worktree: Path) -> None:
    """Leave the state git 2.53 writes mid-add: admin registration, target still empty, no ``.git``."""
    admin = repo / ".git" / "worktrees" / worktree.name
    admin.mkdir(parents=True)
    (admin / "gitdir").write_text(f"{worktree / '.git'}\n", encoding="utf-8")
    (admin / "locked").write_text("initializing", encoding="utf-8")


def test_empty_reservation_registered_by_another_add_after_the_check_is_left_alone(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    worktree = _dispatch_path(repo, "interleaved")

    def fails_without_registering(add_command: list[str], **kwargs: Any):
        _report_git_spawned_then_exited(kwargs["on_spawn"])
        return subprocess.CompletedProcess(add_command, 128, "", "fatal: simulated")

    real_registration = delegate._worktree_registration

    def registration_then_another_add(repo_root: Path, path: Path):
        # Our check sees nothing registered; another add registers the still-empty path right after.
        result = real_registration(repo_root, path)
        _register_empty_path_as_another_add(repo, worktree)
        return result

    monkeypatch.setattr(delegate, "_run_worktree_add", fails_without_registering)
    monkeypatch.setattr(delegate, "_worktree_registration", registration_then_another_add)
    _forbid_removing(monkeypatch, worktree)

    with pytest.raises(delegate.WorktreeAddFailed) as caught:
        delegate._add_reserved_worktree(
            ["git", "worktree", "add", "-b", "claude/interleaved", str(worktree), "main"],
            repo_root=repo,
            worktree_path=worktree,
            task_id="interleaved",
        )

    assert caught.value.cleanup["reserved_dir_left"] is True
    assert worktree.is_dir()
    assert (repo / ".git" / "worktrees" / "interleaved" / "gitdir").exists()


def test_reservation_whose_record_cannot_be_published_is_left_alone(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    worktree = _dispatch_path(repo, "unpublished")

    def publish_fails_while_another_add_registers(task_id: str, run_nonce: str, prep: dict[str, Any]) -> None:
        _register_empty_path_as_another_add(repo, worktree)
        raise RuntimeError("task record is running; refusing to overwrite it")

    def must_not_run(add_command: list[str], **_kwargs: Any):
        raise AssertionError("git worktree add ran without a published reservation")

    monkeypatch.setattr(delegate, "_publish_worktree_prep", publish_fails_while_another_add_registers)
    monkeypatch.setattr(delegate, "_run_worktree_add", must_not_run)
    _forbid_removing(monkeypatch, worktree)

    with pytest.raises(delegate.WorktreeAddFailed) as caught:
        delegate._add_reserved_worktree(
            ["git", "worktree", "add", "-b", "claude/unpublished", str(worktree), "main"],
            repo_root=repo,
            worktree_path=worktree,
            task_id="unpublished",
            run_nonce=_NONCE,
        )

    assert str(caught.value).startswith(f"could not record the reservation of {worktree}")
    cleanup = caught.value.cleanup
    assert cleanup["action"] == "skipped"
    assert cleanup["reserved_dir_left"] is True
    assert caught.value.prep is not None
    assert caught.value.prep["reserved_dir_left"] is True
    assert worktree.is_dir()
    assert (repo / ".git" / "worktrees" / "unpublished" / "gitdir").exists()


# --- the real ``git`` Popen path -------------------------------------------------------------


def _slow_git(
    repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    stage: str,
    block_sigterm: bool = False,
) -> list[int]:
    """Put a ``git`` wrapper on PATH and make ``git worktree add`` stall at ``stage``.

    ``before-checkout`` stalls in a ``reference-transaction`` hook while git
    writes the new worktree's HEAD: registered and locked ``initializing``,
    nothing checked out. ``early-checkout``, ``mid-checkout`` and
    ``last-file`` stall in a smudge filter on ``a.txt``, ``c.txt`` or
    ``e.txt`` (checkout order: ``.gitignore``, ``README.md``, ``a.txt`` ..
    ``e.txt``); ``every-file`` on each ``*.txt``. With ``block_sigterm`` the
    wrapper execs the real git with SIGTERM blocked, so git's own cleanup
    never runs and only SIGKILL stops it, exactly the killed add of #8663.
    (The filter itself still dies on SIGTERM and git then carries on with the
    next file, so that case needs ``every-file``.) Returns the list the
    signals sent to the add's process group are appended to.
    """
    real_git = shutil.which("git")
    assert real_git is not None
    for name in ("d.txt", "e.txt"):
        (repo / name).write_text(f"{name}\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "more files")
    if stage == "before-checkout":
        hooks = repo / ".git" / "test-hooks"
        hooks.mkdir()
        hook = hooks / "reference-transaction"
        hook.write_text(
            '#!/bin/sh\nin=$(cat)\n[ "$1" = prepared ] && case "$in" in *" HEAD") sleep 30;; esac\nexit 0\n',
            encoding="utf-8",
        )
        hook.chmod(0o755)
        git(repo, "config", "core.hooksPath", str(hooks))
    else:
        slow = {"early-checkout": "a.txt", "mid-checkout": "c.txt", "last-file": "e.txt", "every-file": "*.txt"}[stage]
        git(repo, "config", "filter.slow.smudge", "sleep 30; cat")
        (repo / ".git" / "info" / "attributes").write_text(f"{slow} filter=slow\n", encoding="utf-8")
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
        f'#!/bin/sh\nif [ "$1" = worktree ] && [ "$2" = add ]; then\n  {exec_real}\nfi\nexec "{real_git}" "$@"\n',
        encoding="utf-8",
    )
    wrapper.chmod(wrapper.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setattr(delegate, "_WORKTREE_ADD_TIMEOUT_S", 1.0)
    monkeypatch.setattr(delegate, "_WORKTREE_ADD_STALL_S", 0.3)
    monkeypatch.setattr(delegate, "_WORKTREE_ADD_MAX_S", 5.0)
    monkeypatch.setattr(delegate, "_WORKTREE_ADD_POLL_S", 0.05)
    monkeypatch.setattr(delegate, "_WORKTREE_ADD_STOP_GRACE_S", 5.0)
    signals: list[int] = []
    real_killpg = os.killpg

    def recording_killpg(pgid: int, sig: int) -> None:
        signals.append(sig)
        real_killpg(pgid, sig)

    monkeypatch.setattr(delegate.os, "killpg", recording_killpg)
    return signals


# What each stage has checked out when the add is stopped.
_STALLED_FILES = {
    "before-checkout": set(),
    "early-checkout": {".gitignore", "README.md"},
    "mid-checkout": {".gitignore", "README.md", "a.txt", "b.txt"},
    "last-file": {".gitignore", "README.md", "a.txt", "b.txt", "c.txt", "d.txt"},
}


@pytest.mark.parametrize("stage", list(_STALLED_FILES))
def test_real_git_add_stopped_by_sigterm_leaves_nothing_behind(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stage: str
) -> None:
    signals = _slow_git(repo, tmp_path, monkeypatch, stage=stage)
    worktree = _dispatch_path(repo, "termed")
    observed: dict[str, Any] = {}
    real_stop = delegate._stop_worktree_add

    def observe_then_stop(proc: subprocess.Popen[str]) -> bool:
        # The add really is stalled at ``stage``: registered, locked, partly written.
        observed["registration"] = delegate._worktree_registration(repo, worktree)
        observed["files"] = {entry.name for entry in worktree.iterdir() if entry.name != ".git"}
        return real_stop(proc)

    monkeypatch.setattr(delegate, "_stop_worktree_add", observe_then_stop)
    base_sha = git(repo, "rev-parse", "HEAD")

    with pytest.raises(delegate.WorktreeAddFailed) as caught:
        delegate._add_reserved_worktree(
            ["git", "worktree", "add", "-b", "claude/termed", str(worktree), base_sha],
            repo_root=repo,
            worktree_path=worktree,
            task_id="termed",
            run_nonce=_NONCE,
        )

    assert observed == {"registration": (True, "initializing"), "files": _STALLED_FILES[stage]}
    assert signals == [signal.SIGTERM]
    assert str(caught.value).startswith("git worktree add timed out after ")
    # git's own cleanup removed the tree and its admin directory, reservation included.
    assert caught.value.cleanup["action"] == "none"
    assert caught.value.cleanup["reserved_dir_left"] is False
    assert not worktree.exists()
    assert worktree.resolve() not in _registered(repo)
    assert not any((repo / ".git" / "worktrees").glob("*"))
    assert git(repo, "rev-parse", "--verify", "refs/heads/claude/termed") == base_sha


def test_real_git_add_killed_leaves_a_leftover_that_is_reported_never_removed(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    signals = _slow_git(repo, tmp_path, monkeypatch, stage="every-file", block_sigterm=True)
    monkeypatch.setattr(delegate, "_WORKTREE_ADD_STOP_GRACE_S", 0.5)
    base_sha = git(repo, "rev-parse", "HEAD")
    task_id = "killed"
    worktree = _dispatch_path(repo, task_id)

    with pytest.raises(delegate.WorktreeAddFailed) as caught:
        delegate._add_reserved_worktree(
            ["git", "worktree", "add", "-b", "claude/killed", str(worktree), base_sha],
            repo_root=repo,
            worktree_path=worktree,
            task_id=task_id,
            run_nonce=_NONCE,
        )

    assert signals == [signal.SIGTERM, signal.SIGKILL]
    _assert_leftover_reported(caught.value.cleanup, repo, worktree)
    assert delegate._worktree_registration(repo, worktree) == (True, "initializing")
    assert (worktree / "README.md").exists()
    assert not (worktree / "e.txt").exists()
    delegate._record_worktree_prep_failure(
        task_id=task_id,
        run_nonce=_NONCE,
        attribution=type("Attr", (), {"initiator": "test", "source": "test"})(),
        agent="claude",
        mode="workspace-write",
        prompt="probe",
        error=caught.value,
        worktree_path=str(worktree),
        worktree_prep_cleanup=caught.value.cleanup,
        worktree_prep=caught.value.prep,
    )

    # The canonical reaper reports it and removes nothing, even under --apply.
    monkeypatch.setattr(reap_worktrees, "_active_task_ids", lambda: set())
    monkeypatch.setattr(reap_worktrees, "_live_cwd_paths", lambda _repo: set())
    results = reap_worktrees.reap_worktrees(repo_root=repo, apply=True, live_cwds=set(), safe_only=True)
    [row] = [result for result in results if Path(result.path).resolve() == worktree.resolve()]
    assert row.action == "skipped"
    assert row.reason.startswith("needs_attention: initializing_leftover; task-id=killed status=failed")
    assert reap_worktrees.classify_preservation(row) == "needs_attention"
    assert row.needs_attention is not None
    evidence = row.needs_attention["evidence"]
    assert evidence["reserved_directory_intact"] is True
    assert evidence["git_add_exited"] is True
    assert evidence["head"] == base_sha
    assert evidence["head_is_base"] is True
    assert evidence["status"]["deleted"] >= 1
    assert row.needs_attention["command"] == worktree_prep.verify_first_command(repo, worktree)
    journal = reaper_lifecycle.journal_path(repo).read_text(encoding="utf-8").splitlines()
    events = [json.loads(line) for line in journal]
    assert [event["event"] for event in events if event["path"] == str(worktree)] == ["needs_attention"]
    # A second pass reports it again and still removes nothing.
    again = reap_worktrees.reap_worktrees(repo_root=repo, apply=True, live_cwds=set(), safe_only=True)
    assert [result.action for result in again if result.needs_attention is not None] == ["skipped"]
    assert delegate._worktree_registration(repo, worktree) == (True, "initializing")
    assert (worktree / "README.md").exists()
    assert git(repo, "rev-parse", "--verify", "refs/heads/claude/killed") == base_sha


# --- no automatic removal of a registered worktree ------------------------------------------

# Every function on the worktree-prep path and the reaper's ``initializing``
# class. None may run a removal, unlock or prune of a registered worktree.
_REPORT_ONLY_FUNCTIONS = [
    delegate._add_reserved_worktree,
    delegate._run_worktree_add,
    delegate._stop_worktree_add,
    delegate._settle_failed_worktree_add,
    delegate._leave_reservation,
    delegate._publish_worktree_prep,
    delegate._update_worktree_prep,
    delegate._retire_worktree_prep,
    reap_worktrees._initializing_leftover_result,
    post_task_reap._reap_main_worktree,
    *(
        obj
        for _name, obj in inspect.getmembers(worktree_prep, inspect.isfunction)
        if obj.__module__ == worktree_prep.__name__
    ),
]
_FORBIDDEN_CALLS = {
    "remove_unclaimed_worktree",
    "git_worktree_remove",
    "rmtree",
    "_remove_acp_runtime_worktree",
    "rmdir",
    "removedirs",
}
# ``unlink``/``remove`` are allowed only on the task-record file, never on a worktree path.
_FILE_REMOVALS = {"unlink", "remove"}
_TASK_RECORD_NAMES = {"state_path"}
_FORBIDDEN_GIT_WORDS = {"remove", "unlock", "prune"}


def _string_constants(node: ast.AST) -> set[str]:
    return {item.value for item in ast.walk(node) if isinstance(item, ast.Constant) and isinstance(item.value, str)}


@pytest.mark.parametrize("function", _REPORT_ONLY_FUNCTIONS, ids=lambda fn: f"{fn.__module__}.{fn.__name__}")
def test_worktree_prep_and_leftover_report_never_remove_a_registered_worktree(function: Any) -> None:
    tree = ast.parse(textwrap.dedent(inspect.getsource(function)))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        callee = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
        assert callee not in _FORBIDDEN_CALLS, f"{function.__name__} calls {callee}"
        if callee in _FILE_REMOVALS:
            receiver = node.func.value if isinstance(node.func, ast.Attribute) else None
            targets = [receiver, *node.args] if isinstance(receiver, ast.Name) and receiver.id != "os" else node.args
            names = {target.id for target in targets if isinstance(target, ast.Name)}
            assert names and names <= _TASK_RECORD_NAMES, f"{function.__name__} calls {callee} on {sorted(names)}"
        # A git argv (a list/tuple literal passed to a call) never names remove, unlock or prune.
        for arg in [*node.args, *(keyword.value for keyword in node.keywords)]:
            if isinstance(arg, (ast.List, ast.Tuple)):
                words = _string_constants(arg) & _FORBIDDEN_GIT_WORDS
                assert not words, f"{function.__name__} passes {sorted(words)} to {callee}"


def test_the_removal_command_is_only_ever_displayed() -> None:
    source = inspect.getsource(worktree_prep.verify_first_command)
    assert "subprocess" not in source and "_git(" not in source
    assert worktree_prep.verify_first_command(Path("/r"), Path("/r/w x")).startswith(
        "verify first: git -C /r worktree unlock '/r/w x' && "
    )


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
