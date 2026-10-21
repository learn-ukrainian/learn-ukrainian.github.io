"""Tests for subprocess call timeouts and TimeoutExpired handling in scripts/delegate.py (#7213)."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.common.git_context import sanitized_git_env
from scripts.delegate import (
    DEFAULT_GIT_TIMEOUT_S,
    WorktreeStaleBase,
    _auto_finalize_changed_files,
    _auto_finalize_dirty_worktree,
    _push_auto_finalize_branch,
    _release_stale_branch_holders,
    _validate_existing_worktree,
)


def _completed(args: list[str] | None = None, returncode: int = 0, stdout: str = "", stderr: str = ""):
    return subprocess.CompletedProcess(args=args or [], returncode=returncode, stdout=stdout, stderr=stderr)


def _timeout_only(match: list[str], timeout_s: float):
    """Time out the same logical Git argv at the runner seam; other calls stay real."""
    from scripts.orchestration.execution_safe_git import run_git

    timed_out: list[list[str]] = []

    def run(args, **kwargs):
        cmd = ["git", *args]
        if list(cmd[: len(match)]) == match:
            timed_out.append(list(cmd))
            assert kwargs["timeout"] == timeout_s
            raise subprocess.TimeoutExpired(cmd, timeout_s)
        return run_git(args, **kwargs)

    return run, timed_out


def _release_holder(holder: Path, tmp_path: Path, match: list[str], timeout_s: float) -> tuple[list[Path], list]:
    subprocess.run(["git", "init", "-q", str(holder)], check=True, env=sanitized_git_env(), timeout=30)
    side_effect, timed_out = _timeout_only(match, timeout_s)
    with (
        patch("scripts.delegate._WORKTREE_LOCK_DIR", tmp_path / "lu-worktree-locks"),
        patch.dict("os.environ", {"LU_TASKS_DIR": str(tmp_path / "tasks")}),
        patch("scripts.delegate._stale_branch_holder_releasable", return_value=(True, "clean")),
        patch("scripts.orchestration.reap_worktrees.safe_git", side_effect=side_effect),
        patch("scripts.orchestration.worktree_artifacts.safe_git", side_effect=side_effect),
        patch("scripts.orchestration.worktree_claims.safe_git", side_effect=side_effect),
    ):
        released = _release_stale_branch_holders(branch="feature", holders=[holder], dry_run=False)
    return released, timed_out


def test_release_stale_branch_holders_guard_timeout_refuses_removal(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    holder = tmp_path / "holder"
    released, timed_out = _release_holder(holder, tmp_path, ["git", "ls-files"], 30)
    assert released == []
    # The artifact guard's inventory timed out; removal was never attempted.
    assert [cmd[:2] for cmd in timed_out] == [["git", "ls-files"]]

    err = capsys.readouterr().err
    assert (
        f"ℹ️  branch 'feature' held by {holder} not auto-releasable (scratch_release_refused:TimeoutExpired:unknown)"
    ) in err
    assert "failed to release stale branch holder" not in err
    assert "🌲 released stale branch holder" not in err
    assert (holder / ".git").is_dir()


def test_auto_finalize_changed_files_timeouts(tmp_path: Path) -> None:
    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="file.py\0")

    with patch("subprocess.run", side_effect=fake_run):
        assert _auto_finalize_changed_files(tmp_path) == ("file.py",)

    assert len(calls) == 2
    assert "-z" in calls[0]["cmd"]
    assert "-z" in calls[1]["cmd"]
    assert calls[0]["timeout"] == DEFAULT_GIT_TIMEOUT_S
    assert calls[1]["timeout"] == DEFAULT_GIT_TIMEOUT_S

    # Newlines are valid filename characters with Git's NUL-delimited output.
    with patch("subprocess.run", return_value=_completed(stdout="with\nnewline.py\0")):
        assert _auto_finalize_changed_files(tmp_path) == ("with\nnewline.py",)

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["git", "diff"], DEFAULT_GIT_TIMEOUT_S)):
        assert _auto_finalize_changed_files(tmp_path) == ()


def test_auto_finalize_dirty_worktree_timeouts(tmp_path: Path) -> None:
    # 1. git rev-parse --is-inside-work-tree timeout
    with (
        patch("scripts.delegate._auto_finalize_changed_files", return_value=("file.py",)),
        patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["git", "rev-parse"], DEFAULT_GIT_TIMEOUT_S)),
    ):
        res = _auto_finalize_dirty_worktree(
            worktree=tmp_path,
            task_id="task1",
            agent="agy",
            branch="feature",
            base_branch="main",
        )
        assert res.ok is False
        assert res.error == "not a git worktree"

    # 2. git add timeout
    with (
        patch("scripts.delegate._auto_finalize_changed_files", return_value=("file.py",)),
        patch("scripts.delegate._auto_finalize_additions_deletions", return_value=((), ())),
        patch(
            "subprocess.run",
            side_effect=[
                _completed(stdout="true\n"),  # is-inside-work-tree
                subprocess.TimeoutExpired(["git", "add"], DEFAULT_GIT_TIMEOUT_S),
            ],
        ),
    ):
        res = _auto_finalize_dirty_worktree(
            worktree=tmp_path,
            task_id="task1",
            agent="agy",
            branch="feature",
            base_branch="main",
            owned_paths=["file.py"],
        )
        assert res.ok is False
        assert res.error == "auto_finalize_failed, git add, TimeoutExpired"  # #9878: typed, the step named

    # 3. git commit failure with restore
    with (
        patch("scripts.delegate._auto_finalize_changed_files", return_value=("file.py",)),
        patch("scripts.delegate._auto_finalize_additions_deletions", return_value=((), ())),
        patch(
            "subprocess.run",
            side_effect=[
                _completed(stdout="true\n"),  # is-inside-work-tree
                _completed(returncode=0),  # git add
                _completed(returncode=1, stderr="pre-commit hook failed"),  # git commit failed
                _completed(returncode=0),  # git restore --staged
            ],
        ) as run_mock,
    ):
        res = _auto_finalize_dirty_worktree(
            worktree=tmp_path,
            task_id="task1",
            agent="agy",
            branch="feature",
            base_branch="main",
            owned_paths=["file.py"],
        )
        assert res.ok is False
        assert res.error == "auto_finalize_commit_failed, exit 1"  # #9878: the hook's output stays local

    # 4. no --owned-path declared: nothing is staged or committed (#8991)
    with (
        patch("scripts.delegate._auto_finalize_changed_files", return_value=("file.py",)),
        patch("subprocess.run", side_effect=[_completed(stdout="true\n")]) as run_mock,
    ):
        res = _auto_finalize_dirty_worktree(
            worktree=tmp_path,
            task_id="task1",
            agent="agy",
            branch="feature",
            base_branch="main",
        )
        assert res.ok is False
        assert res.error == "no_owned_paths_declared"
        assert res.skipped_paths == ("file.py",)
        assert run_mock.call_count == 1


def test_validate_existing_worktree_timeouts(tmp_path: Path) -> None:
    # 1. rev-parse branch check timeout -> returns False (not a git worktree)
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["git", "rev-parse"], DEFAULT_GIT_TIMEOUT_S)):
        assert _validate_existing_worktree(path=tmp_path, expected_branch="feature", base="main") is False

    # 2. status check timeout -> raises RuntimeError
    with patch(
        "subprocess.run",
        side_effect=[
            _completed(stdout="feature\n"),
            subprocess.TimeoutExpired(["git", "status"], DEFAULT_GIT_TIMEOUT_S),
        ],
    ):
        with pytest.raises(RuntimeError, match=r"git status timed out after 30\.0s"):
            _validate_existing_worktree(path=tmp_path, expected_branch="feature", base="main")

    # 3. rev-list count timeout -> returns False (fail-open offline)
    with (
        patch("scripts.delegate._fetch_base", return_value=True),
        patch(
            "subprocess.run",
            side_effect=[
                _completed(stdout="feature\n"),
                _completed(stdout=""),  # clean
                subprocess.TimeoutExpired(["git", "rev-list"], DEFAULT_GIT_TIMEOUT_S),
            ],
        ),
    ):
        assert _validate_existing_worktree(path=tmp_path, expected_branch="feature", base="main") is False

    # 4. rebase timeout -> aborts rebase and raises WorktreeStaleBase
    with (
        patch("scripts.delegate._fetch_base", return_value=True),
        patch(
            "subprocess.run",
            side_effect=[
                _completed(stdout="feature\n"),
                _completed(stdout=""),  # clean
                _completed(stdout="3\n"),  # 3 commits behind
                subprocess.TimeoutExpired(["git", "rebase"], DEFAULT_GIT_TIMEOUT_S),  # rebase times out
                _completed(returncode=0),  # rebase --abort
            ],
        ),
    ):
        with pytest.raises(WorktreeStaleBase, match=r"rebase timed out after 30\.0s"):
            _validate_existing_worktree(path=tmp_path, expected_branch="feature", base="main", allow_rebase=True)


@pytest.fixture(autouse=True)
def _synthetic_publishing_rules(synthetic_opsec, publisher_transport, monkeypatch):
    """Use synthetic private tooling and an explicit destination for send spies."""
    monkeypatch.setenv("GH_REPO", "unit/public")


def test_auto_finalize_push_fails_closed_without_the_hook(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import delegate

    monkeypatch.setattr(delegate, "_local_repo_root", tmp_path)
    with patch("subprocess.run") as run:
        with pytest.raises(RuntimeError, match=r"^auto_finalize_push_failed, FileNotFoundError ENOENT$"):
            _push_auto_finalize_branch(tmp_path, "feature")
    run.assert_not_called()
