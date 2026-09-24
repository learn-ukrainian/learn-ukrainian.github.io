"""Held worktree-lock identity includes the lock directory (#8663).

``worktree_lock`` refuses a reentry on this thread instead of waiting on
itself. Holding a path's lock in directory A must not count as holding it in
directory B, while the same directory spelled another way is the same lock.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.orchestration import worktree_claims


def test_holding_a_lock_in_one_dir_is_not_holding_it_in_another(tmp_path: Path) -> None:
    worktree = tmp_path / "wt"

    with worktree_claims.worktree_lock(worktree, lock_dir=tmp_path / "locks-a"):
        # A different lock file is no reentry: nesting it cannot self-deadlock.
        with worktree_claims.worktree_lock(worktree, lock_dir=tmp_path / "locks-b", timeout_s=0.5):
            pass


def test_same_dir_through_another_spelling_is_a_reentry(tmp_path: Path) -> None:
    worktree = tmp_path / "wt"
    (tmp_path / "locks").mkdir()
    (tmp_path / "alias").symlink_to(tmp_path / "locks")

    with worktree_claims.worktree_lock(worktree, lock_dir=tmp_path / "locks"):
        with pytest.raises(worktree_claims.WorktreeLockReentry):
            with worktree_claims.worktree_lock(worktree, lock_dir=tmp_path / "alias", timeout_s=0.5):
                pass
