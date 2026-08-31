"""Tests for subprocess call timeouts and TimeoutExpired handling in scripts/delegate.py (#7213)."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.delegate import (
    DEFAULT_GH_CLI_TIMEOUT_S,
    DEFAULT_GIT_TIMEOUT_S,
    DEFAULT_NETWORK_GIT_TIMEOUT_S,
    WorktreeStaleBase,
    _apply_dispatch_sparse_checkout,
    _auto_finalize_changed_files,
    _auto_finalize_dirty_worktree,
    _branch_worktree_paths,
    _count_commits_ahead,
    _create_auto_finalize_pr,
    _current_branch,
    _ensure_worktree,
    _fetch_base,
    _fetch_existing_branch,
    _list_worktree_top_dirs,
    _push_auto_finalize_branch,
    _read_only_checkout_snapshot,
    _release_stale_branch_holders,
    _require_local_branch_is_ancestor_of_origin,
    _resolve_sha,
    _tracking_remote_for_current_branch,
    _validate_existing_worktree,
    _worktree_is_clean,
    _worktree_is_dirty,
)


def _completed(args: list[str] | None = None, returncode: int = 0, stdout: str = "", stderr: str = ""):
    return subprocess.CompletedProcess(args=args or [], returncode=returncode, stdout=stdout, stderr=stderr)


def test_fetch_base_timeouts() -> None:
    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0)

    # Pin the single-remote host shape (#7522): origin IS the canonical
    # GitHub remote, so _fetch_base stays a two-call origin fetch regardless
    # of which fleet host (some carry a mirror origin + github remote) runs
    # the suite.
    origin_only = {"origin": "https://github.com/learn-ukrainian/learn-ukrainian.github.io.git"}
    with (
        patch("scripts.delegate._git_remote_urls", return_value=origin_only),
        patch("subprocess.run", side_effect=fake_run),
    ):
        assert _fetch_base("main") is True

    assert len(calls) == 2
    assert calls[0]["timeout"] == DEFAULT_NETWORK_GIT_TIMEOUT_S
    assert calls[1]["timeout"] == DEFAULT_GIT_TIMEOUT_S

    with (
        patch("scripts.delegate._git_remote_urls", return_value=origin_only),
        patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["git", "fetch"], DEFAULT_NETWORK_GIT_TIMEOUT_S)),
    ):
        assert _fetch_base("main") is False

    with (
        patch("scripts.delegate._git_remote_urls", return_value=origin_only),
        patch(
            "subprocess.run",
            side_effect=[
                _completed(returncode=0),
                subprocess.TimeoutExpired(["git", "rev-parse"], DEFAULT_GIT_TIMEOUT_S),
            ],
        ),
    ):
        assert _fetch_base("main") is False


def test_fetch_existing_branch_timeouts() -> None:
    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0)

    with patch("subprocess.run", side_effect=fake_run):
        _fetch_existing_branch("feature-branch")

    assert len(calls) == 2
    assert calls[0]["timeout"] == DEFAULT_NETWORK_GIT_TIMEOUT_S
    assert calls[1]["timeout"] == DEFAULT_GIT_TIMEOUT_S

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["git", "fetch"], DEFAULT_NETWORK_GIT_TIMEOUT_S)):
        with pytest.raises(RuntimeError, match=r"fetch timed out after 180\.0s"):
            _fetch_existing_branch("feature-branch")

    with patch(
        "subprocess.run",
        side_effect=[
            _completed(returncode=0),
            subprocess.TimeoutExpired(["git", "rev-parse"], DEFAULT_GIT_TIMEOUT_S),
        ],
    ):
        with pytest.raises(RuntimeError, match=r"rev-parse timed out after 30\.0s"):
            _fetch_existing_branch("feature-branch")


def test_require_local_branch_is_ancestor_of_origin_timeouts() -> None:
    with (
        patch("scripts.delegate._resolve_sha", side_effect=["sha_remote", "sha_local"]),
        patch(
            "subprocess.run",
            side_effect=subprocess.TimeoutExpired(["git", "merge-base"], DEFAULT_GIT_TIMEOUT_S),
        ) as run_mock,
    ):
        with pytest.raises(RuntimeError, match=r"merge-base timed out after 30\.0s"):
            _require_local_branch_is_ancestor_of_origin("feature-branch")


def test_branch_worktree_paths_timeouts() -> None:
    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="worktree /path/to/wt\nbranch refs/heads/feature\n\n")

    with patch("subprocess.run", side_effect=fake_run):
        paths = _branch_worktree_paths("feature")
        assert paths == [Path("/path/to/wt").resolve()]

    assert len(calls) == 1
    assert calls[0]["timeout"] == DEFAULT_GIT_TIMEOUT_S

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["git", "worktree", "list"], DEFAULT_GIT_TIMEOUT_S)):
        with pytest.raises(RuntimeError, match=r"timed out after 30\.0s"):
            _branch_worktree_paths("feature")


def test_worktree_is_clean_timeouts(tmp_path: Path) -> None:
    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="")

    with patch("subprocess.run", side_effect=fake_run):
        assert _worktree_is_clean(tmp_path) is True

    assert len(calls) == 1
    assert calls[0]["timeout"] == DEFAULT_GIT_TIMEOUT_S

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["git", "status"], DEFAULT_GIT_TIMEOUT_S)):
        assert _worktree_is_clean(tmp_path) is False


def test_release_stale_branch_holders_timeouts(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    with (
        patch("scripts.delegate._stale_branch_holder_releasable", return_value=(True, "clean")),
        patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["git", "worktree", "remove"], DEFAULT_GIT_TIMEOUT_S)) as run_mock,
    ):
        released = _release_stale_branch_holders(branch="feature", holders=[tmp_path], dry_run=False)
        assert released == []

    err = capsys.readouterr().err
    assert "failed to release stale branch holder" in err
    assert "TimeoutExpired" in err


def test_resolve_sha_timeouts(tmp_path: Path) -> None:
    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="a" * 40 + "\n")

    with patch("subprocess.run", side_effect=fake_run):
        assert _resolve_sha(tmp_path, "HEAD") == "a" * 40

    assert len(calls) == 1
    assert calls[0]["timeout"] == DEFAULT_GIT_TIMEOUT_S

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["git", "rev-parse"], DEFAULT_GIT_TIMEOUT_S)):
        assert _resolve_sha(tmp_path, "HEAD") is None


def test_tracking_remote_for_current_branch_timeouts(tmp_path: Path) -> None:
    with (
        patch("scripts.delegate._current_branch", return_value="feature"),
        patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["git", "config"], DEFAULT_GIT_TIMEOUT_S)) as run_mock,
    ):
        assert _tracking_remote_for_current_branch(tmp_path) is None


def test_count_commits_ahead_timeouts(tmp_path: Path) -> None:
    with (
        patch("scripts.delegate._commit_count_refs", return_value=("origin/main",)),
        patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["git", "rev-list"], DEFAULT_GIT_TIMEOUT_S)) as run_mock,
    ):
        assert _count_commits_ahead(tmp_path, "origin/main") is None


def test_worktree_is_dirty_timeouts(tmp_path: Path) -> None:
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["git", "status"], DEFAULT_GIT_TIMEOUT_S)):
        assert _worktree_is_dirty(tmp_path) is None


def test_read_only_checkout_snapshot_timeouts(tmp_path: Path) -> None:
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["git", "status"], DEFAULT_GIT_TIMEOUT_S)):
        snapshot, err = _read_only_checkout_snapshot(tmp_path)
        assert snapshot is None
        assert err is not None
        assert "status snapshot could not start: TimeoutExpired" in err


def test_auto_finalize_changed_files_timeouts(tmp_path: Path) -> None:
    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="file.py\n")

    with patch("subprocess.run", side_effect=fake_run):
        assert _auto_finalize_changed_files(tmp_path) == ("file.py",)

    assert len(calls) == 2
    assert calls[0]["timeout"] == DEFAULT_GIT_TIMEOUT_S
    assert calls[1]["timeout"] == DEFAULT_GIT_TIMEOUT_S

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["git", "diff"], DEFAULT_GIT_TIMEOUT_S)):
        assert _auto_finalize_changed_files(tmp_path) == ()


def test_current_branch_timeouts(tmp_path: Path) -> None:
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["git", "rev-parse"], DEFAULT_GIT_TIMEOUT_S)):
        assert _current_branch(tmp_path) is None


def test_push_auto_finalize_branch_timeouts(tmp_path: Path) -> None:
    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0)

    with patch("subprocess.run", side_effect=fake_run):
        _push_auto_finalize_branch(tmp_path, "feature")

    assert len(calls) == 1
    assert calls[0]["timeout"] == DEFAULT_NETWORK_GIT_TIMEOUT_S

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["git", "push"], DEFAULT_NETWORK_GIT_TIMEOUT_S)):
        with pytest.raises(RuntimeError, match=r"git push timed out after 180\.0s"):
            _push_auto_finalize_branch(tmp_path, "feature")


def test_create_auto_finalize_pr_timeouts(tmp_path: Path) -> None:
    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="https://github.com/org/repo/pull/1\n")

    with patch("subprocess.run", side_effect=fake_run):
        url = _create_auto_finalize_pr(
            tmp_path,
            branch="feature",
            base_branch="main",
            title="title",
            body="body",
        )
        assert url == "https://github.com/org/repo/pull/1"

    assert len(calls) == 1
    assert calls[0]["timeout"] == DEFAULT_GH_CLI_TIMEOUT_S

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["gh", "pr", "create"], DEFAULT_GH_CLI_TIMEOUT_S)):
        with pytest.raises(RuntimeError, match=r"gh pr create timed out after 180\.0s"):
            _create_auto_finalize_pr(
                tmp_path,
                branch="feature",
                base_branch="main",
                title="title",
                body="body",
            )


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
        )
        assert res.ok is False
        assert "timed out" in str(res.error)

    # 3. git commit failure with restore
    with (
        patch("scripts.delegate._auto_finalize_changed_files", return_value=("file.py",)),
        patch(
            "subprocess.run",
            side_effect=[
                _completed(stdout="true\n"),  # is-inside-work-tree
                _completed(returncode=0),     # git add
                _completed(returncode=1, stderr="pre-commit hook failed"),  # git commit failed
                _completed(returncode=0),     # git restore --staged
            ],
        ) as run_mock,
    ):
        res = _auto_finalize_dirty_worktree(
            worktree=tmp_path,
            task_id="task1",
            agent="agy",
            branch="feature",
            base_branch="main",
        )
        assert res.ok is False
        assert "git commit failed" in str(res.error)


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


def test_list_worktree_top_dirs_timeouts(tmp_path: Path) -> None:
    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="dir1\ndir2\n")

    with patch("subprocess.run", side_effect=fake_run):
        assert _list_worktree_top_dirs(tmp_path) == ["dir1", "dir2"]

    assert len(calls) == 1
    assert calls[0]["timeout"] == DEFAULT_GIT_TIMEOUT_S

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["git", "ls-tree"], DEFAULT_GIT_TIMEOUT_S)):
        with pytest.raises(RuntimeError, match=r"timed out after 30\.0s"):
            _list_worktree_top_dirs(tmp_path)


def test_apply_dispatch_sparse_checkout_timeouts(tmp_path: Path) -> None:
    with (
        patch("scripts.delegate._list_worktree_top_dirs", return_value=["scripts", "tests", "curriculum"]),
        patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["git", "sparse-checkout"], DEFAULT_GIT_TIMEOUT_S)),
    ):
        with pytest.raises(RuntimeError, match=r"failed to init sparse-checkout"):
            _apply_dispatch_sparse_checkout(tmp_path, full_checkout=False, sparse_include=())


def test_ensure_worktree_timeouts(tmp_path: Path) -> None:
    # 1. worktree add timeout
    with (
        patch("scripts.delegate._fetch_base", return_value=True),
        patch("scripts.delegate._resolve_sha", return_value="sha123"),
        patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["git", "worktree", "add"], DEFAULT_GIT_TIMEOUT_S)),
    ):
        with pytest.raises(RuntimeError, match=r"git worktree add timed out after 30\.0s"):
            _ensure_worktree(
                agent="agy",
                task_id="task-123",
                raw_path=str(tmp_path / "wt"),
                base="main",
                resolved_base_sha="sha123",
            )

    # 2. branch --set-upstream-to timeout
    with (
        patch("scripts.delegate._fetch_base", return_value=True),
        patch("scripts.delegate._branch_worktree_paths", return_value=[]),
        patch("scripts.delegate._resolve_sha", return_value="sha123"),
        patch(
            "subprocess.run",
            side_effect=[
                _completed(returncode=0),  # worktree add
                subprocess.TimeoutExpired(["git", "branch"], DEFAULT_GIT_TIMEOUT_S),  # branch --set-upstream-to
            ],
        ),
    ):
        with pytest.raises(RuntimeError, match=r"could not configure upstream .* timed out after 30\.0s"):
            _ensure_worktree(
                agent="agy",
                task_id="task-123",
                raw_path=str(tmp_path / "wt"),
                base="main",
                branch="feature-branch",
                resolved_base_sha="sha123",
            )

