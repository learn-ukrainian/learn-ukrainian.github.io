"""Regression tests for the shared destructive-path guard."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.path_safety import assert_delete_target


def test_delete_guard_allows_descendants_of_standard_and_approved_roots(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = tmp_path / "repo"
    worktree = repo_root / ".worktrees" / "dispatch" / "codex" / "task"
    batch_temp = repo_root / "batch_state" / "tmp" / "render"
    approved_temp = tmp_path / "approved-temp" / "staging"
    tmpdir = tmp_path / "process-tmp"
    monkeypatch.setenv("TMPDIR", str(tmpdir))

    assert assert_delete_target(worktree, repo_root=repo_root) == worktree.resolve()
    assert assert_delete_target(batch_temp, repo_root=repo_root) == batch_temp.resolve()
    assert assert_delete_target(tmpdir / "payload", repo_root=repo_root) == (tmpdir / "payload").resolve()
    assert (
        assert_delete_target(
            approved_temp,
            repo_root=repo_root,
            approved_temp_roots=(tmp_path / "approved-temp",),
        )
        == approved_temp.resolve()
    )


@pytest.mark.parametrize(
    ("target_factory", "message"),
    [
        (lambda repo_root: "", "empty"),
        (lambda repo_root: ".", "current directory"),
        (lambda repo_root: "$TMPDIR", "unexpanded shell variable"),
        (lambda repo_root: repo_root, "repository root"),
        (lambda repo_root: repo_root / ".worktrees", "not the root itself"),
        (lambda repo_root: Path.home(), "home directory"),
        (lambda repo_root: Path("/etc"), "outside approved"),
    ],
)
def test_delete_guard_refuses_catastrophic_or_unapproved_targets(
    tmp_path: Path,
    target_factory,
    message: str,
) -> None:
    repo_root = tmp_path / "repo"

    with pytest.raises(ValueError, match=message):
        assert_delete_target(target_factory(repo_root), repo_root=repo_root)


def test_symlink_escape_is_blocked(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    worktrees = repo_root / ".worktrees"
    worktrees.mkdir(parents=True)
    (worktrees / "escape").symlink_to(Path("/etc"), target_is_directory=True)

    with pytest.raises(ValueError, match="outside approved"):
        assert_delete_target(worktrees / "escape", repo_root=repo_root)


@pytest.mark.parametrize(
    ("tmpdir", "approved_temp_roots"),
    [
        ("/", ()),
        (None, (Path("/"),)),
    ],
)
def test_delete_guard_refuses_filesystem_root_as_a_temp_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmpdir: str | None,
    approved_temp_roots: tuple[Path, ...],
) -> None:
    """Neither $TMPDIR nor an explicit root can allow arbitrary deletion."""
    repo_root = tmp_path / "repo"
    arbitrary_target = tmp_path / "arbitrary-target"
    if tmpdir is None:
        monkeypatch.delenv("TMPDIR", raising=False)
    else:
        monkeypatch.setenv("TMPDIR", tmpdir)

    with pytest.raises(ValueError, match="filesystem root"):
        assert_delete_target(
            arbitrary_target,
            repo_root=repo_root,
            approved_temp_roots=approved_temp_roots,
        )
