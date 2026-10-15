"""#10637: lock waits under the reaper's cleanup lock are bounded; elsewhere they still block."""

from __future__ import annotations

import fcntl
import json
import os
import threading
import time
from pathlib import Path

import pytest

from scripts.orchestration import dead_worker_state, lock_wait_bound, reaper_lifecycle, worktree_claims


def _hold(path: Path) -> int:
    """Hold ``path``'s lock through a second open file description, as another process would."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    return descriptor


def test_bounded_wait_gives_up_and_names_the_lock_only(tmp_path: Path) -> None:
    held = _hold(tmp_path / "x.lock")
    descriptor = os.open(tmp_path / "x.lock", os.O_RDWR)
    try:
        started = time.monotonic()
        with lock_wait_bound.bounded_lock_waits(0.2), pytest.raises(lock_wait_bound.LockWaitTimeout) as timeout:
            lock_wait_bound.flock_exclusive(descriptor, label="task state lock")
        assert 0.15 <= time.monotonic() - started < 2
        assert str(timeout.value) == "task state lock still held by another process after 0.2s"
        assert isinstance(timeout.value, TimeoutError) and isinstance(timeout.value, OSError)
        assert lock_wait_bound.active_wait_bound() is None
    finally:
        os.close(descriptor)
        os.close(held)


def test_bounded_wait_acquires_once_released(tmp_path: Path) -> None:
    held = _hold(tmp_path / "x.lock")
    descriptor = os.open(tmp_path / "x.lock", os.O_RDWR)
    timer = threading.Timer(0.1, os.close, args=(held,))
    timer.start()
    try:
        with lock_wait_bound.bounded_lock_waits(5):
            lock_wait_bound.flock_exclusive(descriptor, label="task state lock")
        contender = os.open(tmp_path / "x.lock", os.O_RDWR)
        try:
            with pytest.raises(BlockingIOError):
                fcntl.flock(contender, fcntl.LOCK_EX | fcntl.LOCK_NB)
        finally:
            os.close(contender)
    finally:
        timer.join()
        os.close(descriptor)


def test_without_a_bound_the_wait_still_blocks(tmp_path: Path) -> None:
    held = _hold(tmp_path / "x.lock")
    descriptor = os.open(tmp_path / "x.lock", os.O_RDWR)
    acquired = threading.Event()

    def take() -> None:
        lock_wait_bound.flock_exclusive(descriptor, label="task state lock")
        acquired.set()

    waiter = threading.Thread(target=take)
    waiter.start()
    try:
        assert not acquired.wait(0.3)
        os.close(held)
        assert acquired.wait(5)
    finally:
        waiter.join(5)
        os.close(descriptor)


def test_task_state_lock_is_bounded_only_under_the_reaper_bound(tmp_path: Path) -> None:
    record = tmp_path / "tasks" / "t.json"
    held = _hold(record.with_suffix(".json.lock"))
    try:
        with lock_wait_bound.bounded_lock_waits(0.1), pytest.raises(lock_wait_bound.LockWaitTimeout):
            with dead_worker_state.task_state_lock(record):
                pytest.fail("held task lock was taken")
    finally:
        os.close(held)
    with dead_worker_state.task_state_lock(record):
        pass


@pytest.mark.parametrize("operation", ["journal", "reservation"])
def test_reaper_state_locks_are_bounded_under_the_reaper_bound(tmp_path: Path, operation: str) -> None:
    journal = reaper_lifecycle.journal_path(tmp_path)
    pending_lock = reaper_lifecycle.pending_path(tmp_path).with_suffix(".lock")
    held = _hold(journal if operation == "journal" else pending_lock)
    try:
        with lock_wait_bound.bounded_lock_waits(0.1), pytest.raises(lock_wait_bound.LockWaitTimeout):
            if operation == "journal":
                reaper_lifecycle.append_journal(tmp_path, "probe")
            else:
                reaper_lifecycle.mark_reap_pending(
                    tmp_path, worktree_path=tmp_path / "wt", branch=None, head=None, task_id=None
                )
    finally:
        os.close(held)
    assert not reaper_lifecycle.is_reap_pending(tmp_path, tmp_path / "wt")


def test_reservation_recovery_takes_the_worktree_lock_before_the_reaper_lock(tmp_path: Path) -> None:
    """#10637: recovery never waits on a per-worktree lock while holding the reaper lock."""
    worktree = tmp_path / ".worktrees" / "orphan"
    lock_dir = tmp_path / "locks"
    path = reaper_lifecycle.pending_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"paths": {str(worktree.resolve()): {"pid": 2**22 + 12345}}}), encoding="utf-8")
    order: list[str] = []

    class ReaperLock:
        def __enter__(self) -> None:
            order.append("reaper-lock")

        def __exit__(self, *_exc: object) -> None:
            order.append("reaper-unlock")

    with worktree_claims.worktree_lock(worktree, lock_dir=lock_dir):
        held_elsewhere = threading.Thread(
            target=lambda: order.append(
                str(
                    reaper_lifecycle.recover_orphaned_reap_pending(
                        tmp_path, worktree, lock_dir=lock_dir, reaper_lock=ReaperLock
                    )
                )
            )
        )
        held_elsewhere.start()
        held_elsewhere.join(5)
    assert order == ["False"]
    assert reaper_lifecycle.is_reap_pending(tmp_path, worktree)

    assert reaper_lifecycle.recover_orphaned_reap_pending(tmp_path, worktree, lock_dir=lock_dir, reaper_lock=ReaperLock)
    assert order == ["False", "reaper-lock", "reaper-unlock"]
    assert not reaper_lifecycle.is_reap_pending(tmp_path, worktree)
