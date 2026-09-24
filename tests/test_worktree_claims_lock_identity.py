"""Held worktree-lock identity includes the lock directory (#8663).

``remove_unclaimed_worktree(reuse_held_lock=True)`` skips acquisition only for
a lock this thread holds in the same lock directory. Holding a path's lock in
directory A must neither satisfy nor block its lock in directory B.
"""

from __future__ import annotations

import threading
from pathlib import Path

from scripts.orchestration import worktree_claims


def test_holding_a_lock_in_one_dir_is_not_holding_it_in_another(tmp_path: Path) -> None:
    worktree = tmp_path / "wt"
    dir_a = tmp_path / "locks-a"
    dir_b = tmp_path / "locks-b"

    with worktree_claims.worktree_lock(worktree, lock_dir=dir_a):
        assert worktree_claims.holds_worktree_lock(worktree, lock_dir=dir_a)
        assert not worktree_claims.holds_worktree_lock(worktree, lock_dir=dir_b)
        # A different lock file is no reentry: nesting it cannot self-deadlock.
        with worktree_claims.worktree_lock(worktree, lock_dir=dir_b, timeout_s=0.5):
            assert worktree_claims.holds_worktree_lock(worktree, lock_dir=dir_b)
        assert not worktree_claims.holds_worktree_lock(worktree, lock_dir=dir_b)

    assert not worktree_claims.holds_worktree_lock(worktree, lock_dir=dir_a)


def test_same_dir_through_another_spelling_is_still_held(tmp_path: Path) -> None:
    worktree = tmp_path / "wt"
    (tmp_path / "locks").mkdir()
    (tmp_path / "alias").symlink_to(tmp_path / "locks")

    with worktree_claims.worktree_lock(worktree, lock_dir=tmp_path / "locks"):
        assert worktree_claims.holds_worktree_lock(worktree, lock_dir=tmp_path / "alias")


def test_reuse_held_lock_still_acquires_another_dirs_lock(tmp_path: Path) -> None:
    worktree = tmp_path / "wt"
    dir_a = tmp_path / "locks-a"
    dir_b = tmp_path / "locks-b"
    held_in_b = threading.Event()
    release_b = threading.Event()

    def other_holder() -> None:
        with worktree_claims.worktree_lock(worktree, lock_dir=dir_b):
            held_in_b.set()
            release_b.wait(10)

    holder = threading.Thread(target=other_holder)
    holder.start()
    try:
        assert held_in_b.wait(10)
        steps: list[str] = []

        def releasable() -> tuple[bool, str]:
            steps.append("releasable")
            return False, "must not run without directory B's lock"

        with worktree_claims.worktree_lock(worktree, lock_dir=dir_a):
            removal = worktree_claims.remove_unclaimed_worktree(
                worktree,
                repo_root=tmp_path,
                reason="probe",
                owner_task_id=None,
                releasable=releasable,
                tasks_dir=tmp_path / "tasks",
                lock_dir=dir_b,
                lock_timeout_s=0.2,
                reuse_held_lock=True,
            )
    finally:
        release_b.set()
        holder.join(10)

    assert removal.action == "skipped"
    assert removal.reason == worktree_claims.LOCK_BUSY
    assert steps == []
