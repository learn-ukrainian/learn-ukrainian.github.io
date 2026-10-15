"""#10637: one enforced deadline on every hold of the cleanup-wide lock, released on every exit path.

A removable candidate is re-proven under delegate's per-worktree lock and the
cleanup-wide lock. A watchdog ends that hold at the candidate's locked-region
deadline whatever read is still in flight; the candidate is then retained and
the rest of the pass is deferred. A release at or after the deadline is an
expired hold too, even when scheduling delayed the watchdog. Preservation and
removal run after the hold, under the per-worktree lock alone. Every resource
is released on every exit path, a failed reservation clear or a failed unlock
included, and neither lets the pass remove anything further. A removal is
counted against the daily cap before it starts, and its slot is given back
only when nothing destructive started.
"""

from __future__ import annotations

import errno
import fcntl
import http.client
import json
import os
import select
import socket
import subprocess
import sys
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from scripts.orchestration import lock_wait_bound, reaper_lifecycle, worktree_claims
from scripts.orchestration import reap_worktrees as rw
from tests.orchestration.test_reap_worktrees import _backdate_tree, add_worktree, init_repo, patch_gh, result_for
from tests.orchestration.test_reap_worktrees import (
    _no_default_foreign_scratch_roots as _no_default_foreign_scratch_roots,
)
from tests.orchestration.test_reap_worktrees import _repo_template as _repo_template

# Captured at import, before the autouse fixture replaces it with a stub.
_REAL_ACTIVE_TASK_IDS = rw._active_task_ids
# The candidate's locked-region deadline in these tests, and so its hold deadline.
_HOLD_S = 1.0
# How far past the deadline a contending process may be granted the lock: thread
# and process scheduling on a loaded host, not reaper work.
_GRANT_SLACK_S = 0.75
# A read that outlasts the hold: twelve bytes, each within the socket timeout.
_TRICKLE_BYTE_S = 0.25
_FORGE_PAGES = 12
_FORGE_PAGE_S = 0.25

# Another process: waits for "go", blocks on the cleanup lock, prints the
# CLOCK_MONOTONIC second it was granted, and holds the lock until "release".
_CONTENDER = (
    "import fcntl, sys, time\n"
    "sys.stdin.readline()\n"
    "handle = open(sys.argv[1], 'a')\n"
    "fcntl.flock(handle, fcntl.LOCK_EX)\n"
    "print(time.monotonic(), flush=True)\n"
    "sys.stdin.readline()\n"
)


class _Contender:
    """A separate process that takes the cleanup-wide lock as soon as it is free."""

    def __init__(self, repo: Path) -> None:
        self.process = subprocess.Popen(
            [sys.executable, "-c", _CONTENDER, str(rw._common_git_dir(repo) / "worktree-reaper.lock")],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
        )
        self.started_at: float | None = None

    def go(self) -> None:
        assert self.process.stdin is not None
        self.started_at = time.monotonic()
        self.process.stdin.write("go\n")
        self.process.stdin.flush()

    def granted_at(self, timeout: float = 10.0) -> float | None:
        assert self.process.stdout is not None
        ready, _, _ = select.select([self.process.stdout], [], [], timeout)
        if not ready:
            return None
        line = self.process.stdout.readline().strip()
        return float(line) if line else None

    def release(self) -> None:
        stdin = self.process.stdin
        if self.process.poll() is None and stdin is not None:
            try:
                stdin.write("release\n")
                stdin.flush()
            except BrokenPipeError:
                pass
        try:
            self.process.wait(10)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(10)


class _StalledWatchdog:
    """A watchdog that scheduling delays past the hold deadline: it has not run when the holder looks."""

    def __init__(self, _interval: float, _function: Any) -> None:
        self.daemon = False

    def start(self) -> None:
        pass

    def cancel(self) -> None:
        pass


def _seed_cap(repo: Path, count: int) -> tuple[Path, str]:
    """Today's daily-cap count set to ``count``; returns the cap file and today's key."""
    today = datetime.now(UTC)
    cap_file = reaper_lifecycle._cap_path(repo)
    cap_file.parent.mkdir(parents=True, exist_ok=True)
    cap_file.write_text(
        json.dumps(
            {
                "schema_version": "worktree-reaper-first-class-cap.v1",
                "enabled_at": today.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                "counts": {today.date().isoformat(): count},
            }
        ),
        encoding="utf-8",
    )
    return cap_file, today.date().isoformat()


def _cap_count(cap_file: Path, day: str) -> int:
    return json.loads(cap_file.read_text(encoding="utf-8"))["counts"][day]


def _hold_cap_lock(repo: Path, held: list[int]) -> None:
    """Take the daily-cap lock from another open file description, as another process would."""
    lock = reaper_lifecycle._cap_path(repo).with_suffix(".lock")
    descriptor = os.open(lock, os.O_RDWR | os.O_CREAT | os.O_CLOEXEC, 0o600)
    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    held.append(descriptor)


def _lock_is_free(repo: Path) -> bool:
    try:
        with rw._ReapLock(repo, phase="husk-removal", timeout_s=0):
            return True
    except rw.ReapLockBusy:
        return False


def _open_descriptors() -> int:
    return len(os.listdir("/proc/self/fd"))


def _merged_trees(repo: Path, monkeypatch: pytest.MonkeyPatch, stem: str, first_pr: int) -> list[Path]:
    trees = [add_worktree(repo, f"codex/{stem}-{index}") for index in range(2)]
    patch_gh(
        monkeypatch,
        {f"codex/{stem}-{index}": [{"number": first_pr + index, "state": "MERGED"}] for index in range(2)},
    )
    return trees


def _on_candidate_grant(monkeypatch: pytest.MonkeyPatch, event: Any) -> list[float]:
    """Run ``event`` once, right after the first candidate's cleanup-wide lock is granted."""
    real_enter = rw._ReapLock.__enter__
    granted: list[float] = []

    def enter(lock: Any) -> Any:
        entered = real_enter(lock)
        if lock.phase == "candidate-mutation" and not granted:
            granted.append(time.monotonic())
            event()
        return entered

    monkeypatch.setattr(rw._ReapLock, "__enter__", enter)
    return granted


def _attempted_candidates(monkeypatch: pytest.MonkeyPatch) -> list[Path]:
    real_guard = rw._enter_dispatch_worktree_guard
    attempts: list[Path] = []

    def guard(stack: Any, **kwargs: Any) -> Any:
        attempts.append(kwargs["info"].path)
        return real_guard(stack, **kwargs)

    monkeypatch.setattr(rw, "_enter_dispatch_worktree_guard", guard)
    return attempts


def _trickling_response(body: bytes, *, timeout: float, byte_s: float, finished: list[float]) -> Any:
    """A real ``HTTPResponse`` whose body arrives a byte at a time, each inside ``timeout``."""
    server, client = socket.socketpair()
    client.settimeout(timeout)

    def serve() -> None:
        with server:
            server.sendall(
                b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: %d\r\n\r\n" % len(body)
            )
            for index in range(len(body)):
                time.sleep(byte_s)
                server.sendall(body[index : index + 1])
            finished.append(time.monotonic())

    threading.Thread(target=serve, daemon=True).start()
    response = http.client.HTTPResponse(client)
    client.close()  # the response's file keeps the socket open until it is closed
    response.begin()
    return response


def _slow_monitor(monkeypatch: pytest.MonkeyPatch, finished: list[float]) -> None:
    """The real Monitor read, over a socket whose inactivity timeout never fires."""
    import urllib.request

    monkeypatch.setattr(rw, "_active_task_ids", _REAL_ACTIVE_TASK_IDS)

    def urlopen(_url: str, *, timeout: float) -> Any:
        # Only the read under the lock trickles; the pass's opening read answers at once.
        locked = rw._remaining_locked_s() is not None
        return _trickling_response(
            b'{"tasks": []}',
            timeout=timeout,
            byte_s=_TRICKLE_BYTE_S if locked else 0.0,
            finished=finished if locked else [],
        )

    monkeypatch.setattr(urllib.request, "urlopen", urlopen)


def _slow_forge(monkeypatch: pytest.MonkeyPatch, finished: list[float]) -> None:
    """A paginated forge read under the lock: every page inside the call's timeout, the sum past the hold."""
    answer = rw._run_gh

    def paged(args: list[str], **kwargs: Any) -> Any:
        if rw._remaining_locked_s() is not None and not finished:
            for _page in range(_FORGE_PAGES):
                time.sleep(_FORGE_PAGE_S)
            finished.append(time.monotonic())
        return answer(args, **kwargs)

    monkeypatch.setattr(rw, "_run_gh", paged)


@pytest.mark.parametrize("slow_read", ["monitor_trickle", "forge_pages"])
def test_10637_hold_ends_at_its_deadline_while_a_read_is_in_flight(tmp_path, monkeypatch, slow_read):
    """#10637 P1: reads that each honour their own cap but together outlast the hold release the lock on time.

    The review's reproducers: a Monitor response trickling inside its socket
    timeout, and forge pages each inside the call's timeout. Another process
    waiting on the lock is granted it at the hold deadline, while the read is
    still running; the candidate is retained and the rest of the pass deferred.
    """
    repo = init_repo(tmp_path)
    trees = _merged_trees(repo, monkeypatch, f"hold-{slow_read.replace('_', '-')}", 150)
    monkeypatch.setattr(rw, "_locked_region_budget_s", lambda: _HOLD_S)
    read_finished: list[float] = []
    (_slow_monitor if slow_read == "monitor_trickle" else _slow_forge)(monkeypatch, read_finished)
    attempts = _attempted_candidates(monkeypatch)
    contender = _Contender(repo)
    try:
        granted = _on_candidate_grant(monkeypatch, contender.go)
        results = rw.reap_worktrees(repo_root=repo, apply=True, live_cwds=set())
        contender_granted = contender.granted_at()
        # The reaper never unlocks a lock another process now holds.
        assert not _lock_is_free(repo)
    finally:
        contender.release()

    assert granted and read_finished, (granted, read_finished)
    assert contender_granted is not None, "the other process was never granted the lock"
    assert contender_granted < read_finished[0], "the lock stayed held until the slow read finished"
    assert contender_granted - granted[0] <= _HOLD_S + _GRANT_SLACK_S, contender_granted - granted[0]
    first, second = (result_for(results, tree) for tree in trees)
    assert all(tree.is_dir() for tree in trees)
    assert first.action == "skipped", first.reason
    assert first.reason.startswith(rw.REAP_LOCK_HOLD_EXPIRED), first.reason
    assert second.action == "skipped", second.reason
    assert second.reason.startswith(f"{rw.REAP_LOCK_HOLD_EXPIRED}; deferred to the next pass"), second.reason
    assert [path.resolve() for path in attempts] == [trees[0].resolve()]
    assert not any(reaper_lifecycle.is_reap_pending(repo, tree) for tree in trees)
    assert _lock_is_free(repo)


def test_10637_removal_runs_after_the_hold_while_another_process_holds_the_lock(tmp_path, monkeypatch):
    """#10637 P1: preservation and removal do not keep the cleanup-wide lock.

    The hold ends before ``git worktree remove``; another process waiting on
    the lock is granted it while the removal runs under the per-worktree lock
    alone. That process then holds the lock mid-sweep: the next candidate waits
    its bound, is retained and the pass defers the rest.
    """
    repo = init_repo(tmp_path)
    trees = _merged_trees(repo, monkeypatch, "remove-unlocked", 160)
    monkeypatch.setattr(rw, "DEFAULT_REAP_LOCK_TIMEOUT_S", 0.2)
    removal: dict[str, float] = {}
    real_remove = worktree_claims.git_worktree_remove

    def slow_remove(*args: Any, **kwargs: Any) -> Any:
        removal.setdefault("started", time.monotonic())
        time.sleep(1.5)
        try:
            return real_remove(*args, **kwargs)
        finally:
            removal.setdefault("finished", time.monotonic())

    monkeypatch.setattr(rw.worktree_claims, "git_worktree_remove", slow_remove)
    contender = _Contender(repo)
    try:
        _on_candidate_grant(monkeypatch, contender.go)
        results = rw.reap_worktrees(repo_root=repo, apply=True, live_cwds=set())
        contender_granted = contender.granted_at()
        assert not _lock_is_free(repo)
    finally:
        contender.release()

    first, second = (result_for(results, tree) for tree in trees)
    assert first.action == "removed", first.reason
    assert not trees[0].exists()
    assert contender_granted is not None
    assert contender_granted < removal["finished"], "the cleanup-wide lock was held across git worktree remove"
    assert second.action == "skipped", second.reason
    assert second.reason.startswith(rw.REAP_LOCK_BUSY), second.reason
    assert trees[1].is_dir()
    assert not any(reaper_lifecycle.is_reap_pending(repo, tree) for tree in trees)


def test_10637_reservation_clear_failure_releases_everything_and_removes_nothing_more(tmp_path, monkeypatch):
    """#10637 P1: a reservation that cannot be cleared is reported, and releases nothing else late.

    The review's reproducer: another process holds the reservation file's lock
    when the clear starts, past the (test) 0.1 s bound. The cleanup-wide lock,
    the per-worktree lock, the wait bound, the region deadline and the pinned
    descriptors are all released while the caller still holds everything the
    pass returned; the reservation stays and names its owner; the next
    candidate is not removed.
    """
    repo = init_repo(tmp_path)
    trees = _merged_trees(repo, monkeypatch, "clear-fails", 170)
    monkeypatch.setattr(rw, "_LOCKED_LOCK_WAIT_S", 0.1)
    real_clear = reaper_lifecycle.clear_reap_pending
    held: list[int] = []

    def clear_while_held(repo_root: Path, worktree_path: Path) -> None:
        if not held:
            state_lock = reaper_lifecycle.pending_path(repo_root).with_suffix(".lock")
            descriptor = os.open(state_lock, os.O_RDWR | os.O_CREAT | os.O_CLOEXEC, 0o600)
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            held.append(descriptor)
        return real_clear(repo_root, worktree_path)

    monkeypatch.setattr(reaper_lifecycle, "clear_reap_pending", clear_while_held)
    descriptors_before = _open_descriptors()
    raised: BaseException | None = None
    results: list[rw.ReapResult] = []
    try:
        try:
            results = rw.reap_worktrees(repo_root=repo, apply=True, live_cwds=set())
        except Exception as exc:  # kept referenced, as a caller's traceback would be
            raised = exc
        assert held, "the reservation clear never ran"
        # Nothing the pass took is still held while its outcome is referenced.
        assert _lock_is_free(repo), "the cleanup-wide lock outlived a failed reservation clear"
        assert not worktree_claims._HELD_LOCKS
        assert lock_wait_bound.active_wait_bound() is None
        assert rw._remaining_locked_s() is None
        assert raised is None, repr(raised)
    finally:
        for descriptor in held:
            os.close(descriptor)

    first, second = (result_for(results, tree) for tree in trees)
    assert first.action == "removed", first.reason
    assert not trees[0].exists()
    assert first.error is not None
    assert first.error.startswith(f"{rw.REAP_CLEANUP_FAILED}: reservation clear"), first.error
    assert "LockWaitTimeout" in first.error and f"owner pid={os.getpid()}" in first.error
    assert reaper_lifecycle.is_reap_pending(repo, trees[0]), "the failed clear must leave the reservation in place"
    assert second.action == "skipped", second.reason
    assert second.reason.startswith(f"{rw.REAP_CLEANUP_FAILED}; deferred to the next pass"), second.reason
    assert trees[1].is_dir()
    assert _open_descriptors() == descriptors_before


def test_10637_failed_unlock_still_frees_the_lock_and_removes_nothing(tmp_path, monkeypatch):
    """#10637: releasing the cleanup-wide lock can fail; its descriptor is closed and nothing is removed.

    ``LOCK_UN`` fails with EIO. Closing the descriptor still drops the lock;
    the candidate whose hold ended that way is retained, and the pass defers
    the rest.
    """
    repo = init_repo(tmp_path)
    trees = _merged_trees(repo, monkeypatch, "unlock-fails", 180)
    lock_descriptors: set[int] = set()
    real_enter = rw._ReapLock.__enter__

    def enter(lock: Any) -> Any:
        entered = real_enter(lock)
        lock_descriptors.add(lock.handle.fileno())
        return entered

    monkeypatch.setattr(rw._ReapLock, "__enter__", enter)
    real_flock = fcntl.flock
    failed: list[int] = []

    def flock(descriptor: Any, operation: int) -> Any:
        if operation == fcntl.LOCK_UN and descriptor in lock_descriptors and not failed:
            failed.append(descriptor)
            raise OSError(errno.EIO, "injected unlock failure")
        return real_flock(descriptor, operation)

    monkeypatch.setattr(fcntl, "flock", flock)
    raised: BaseException | None = None
    results: list[rw.ReapResult] = []
    try:
        results = rw.reap_worktrees(repo_root=repo, apply=True, live_cwds=set())
    except Exception as exc:  # kept referenced, as a caller's traceback would be
        raised = exc

    assert failed, "the cleanup-wide lock was never unlocked"
    assert _lock_is_free(repo), "a failed unlock left the cleanup-wide lock held"
    assert raised is None, repr(raised)
    first, second = (result_for(results, tree) for tree in trees)
    assert all(tree.is_dir() for tree in trees)
    assert first.action == "skipped", first.reason
    assert first.reason.startswith(rw.REAP_LOCK_RELEASE_FAILED), first.reason
    assert "injected unlock failure" in first.reason
    assert second.reason.startswith(f"{rw.REAP_LOCK_RELEASE_FAILED}; deferred to the next pass"), second.reason
    assert not any(reaper_lifecycle.is_reap_pending(repo, tree) for tree in trees)


def test_10637_concurrent_sweepers_never_spend_the_cap_twice(tmp_path, monkeypatch):
    """#10637: with removal outside the cleanup-wide lock, a concurrent pass still counts it.

    Two passes, one candidate each, one slot left below the hard ceiling. The
    second pass checks the cap while the first is removing (its hold ended):
    the first counted its slot under its hold before removal started, so the
    second retains its candidate and the ceiling holds.
    """
    repo = init_repo(tmp_path)
    trees = _merged_trees(repo, monkeypatch, "cap-race", 190)
    monkeypatch.setenv("LU_REAPER_MAX_REAPS_PER_DAY", "1")
    today = datetime.now(UTC)
    cap_file = reaper_lifecycle._cap_path(repo)
    cap_file.parent.mkdir(parents=True, exist_ok=True)
    cap_file.write_text(
        json.dumps(
            {
                "schema_version": "worktree-reaper-first-class-cap.v1",
                "enabled_at": today.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                "counts": {today.date().isoformat(): 1},
            }
        ),
        encoding="utf-8",
    )
    first_removing = threading.Event()
    second_done = threading.Event()
    real_remove = worktree_claims.git_worktree_remove
    removed: list[Path] = []

    def remove(repo_root: Path, target: Path, **kwargs: Any) -> Any:
        removed.append(Path(target).resolve())
        if Path(target).resolve() == trees[0].resolve():
            first_removing.set()
            second_done.wait(5)
        return real_remove(repo_root, target, **kwargs)

    monkeypatch.setattr(rw.worktree_claims, "git_worktree_remove", remove)
    outcomes: dict[str, Any] = {}

    def sweep(name: str, target: Path, wait_for: threading.Event | None) -> None:
        try:
            if wait_for is not None:
                assert wait_for.wait(10), "the first pass never reached removal"
            outcomes[name] = rw.reap_worktrees(repo_root=repo, apply=True, live_cwds=set(), target_paths=[target])
        except BaseException as exc:
            outcomes[name] = exc
        finally:
            if name == "second":
                second_done.set()

    threads = [
        threading.Thread(target=sweep, args=("first", trees[0], None)),
        threading.Thread(target=sweep, args=("second", trees[1], first_removing)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(30)
    assert not any(thread.is_alive() for thread in threads)

    assert all(isinstance(outcomes.get(name), list) for name in ("first", "second")), outcomes
    first = result_for(outcomes["first"], trees[0])
    second = result_for(outcomes["second"], trees[1])
    assert first.action == "removed", first.reason
    assert second.action == "skipped", second.reason
    assert "cap ceiling reached" in second.reason, second.reason
    assert removed == [trees[0].resolve()]
    assert trees[1].is_dir()
    counts = json.loads(cap_file.read_text(encoding="utf-8"))["counts"]
    assert counts[today.date().isoformat()] == 2
    assert not any(reaper_lifecycle.is_reap_pending(repo, tree) for tree in trees)
    assert _lock_is_free(repo)


def test_10637_watchdog_ends_a_hold_and_leaves_the_next_holder_alone(tmp_path):
    """The watchdog releases at the deadline; the late holder's exit touches nothing it no longer owns."""
    repo = init_repo(tmp_path)
    other = tmp_path / "other.lock"
    other.touch()
    with rw._ReapLock(repo, phase="husk-removal", hold_deadline=time.monotonic() + 0.2) as hold:
        freed = hold.handle.fileno()
        assert hold.is_held()
        deadline = time.monotonic() + 5
        while hold.is_held() and time.monotonic() < deadline:
            time.sleep(0.02)
        assert not hold.is_held()
        assert hold.expired
        # Another lock is taken on the very descriptor number the watchdog freed.
        opened: list[int] = []
        try:
            while freed not in opened and len(opened) < 64:
                opened.append(os.open(other, os.O_RDWR | os.O_CLOEXEC))
            assert freed in opened
            fcntl.flock(freed, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with rw._ReapLock(repo, phase="candidate-mutation", timeout_s=0) as successor:
                with pytest.raises(rw.ReapLockHoldExpired, match=rw.REAP_LOCK_HOLD_EXPIRED):
                    hold.ensure_held()
                with pytest.raises(rw.ReapLockHoldExpired):
                    hold.release()
                hold.close()
                assert successor.is_held()
                assert not _lock_is_free(repo)
                probe = os.open(other, os.O_RDWR | os.O_CLOEXEC)
                try:
                    with pytest.raises(BlockingIOError):
                        fcntl.flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)
                finally:
                    os.close(probe)
        finally:
            for descriptor in opened:
                os.close(descriptor)
    assert _lock_is_free(repo)


def test_10637_watchdog_unlock_failure_still_closes_the_descriptor(tmp_path, monkeypatch):
    """A failed ``LOCK_UN`` in the watchdog is recorded; closing the descriptor frees the lock."""
    repo = init_repo(tmp_path)
    real_flock = fcntl.flock

    def flock(descriptor: Any, operation: int) -> Any:
        if operation == fcntl.LOCK_UN:
            raise OSError(errno.EIO, "injected unlock failure")
        return real_flock(descriptor, operation)

    with rw._ReapLock(repo, phase="husk-removal", hold_deadline=time.monotonic() + 0.1) as hold:
        monkeypatch.setattr(fcntl, "flock", flock)
        deadline = time.monotonic() + 5
        while hold.is_held() and time.monotonic() < deadline:
            time.sleep(0.02)
        monkeypatch.setattr(fcntl, "flock", real_flock)
        assert hold.expired
        assert isinstance(hold.release_error, OSError)
        assert _lock_is_free(repo)
        with pytest.raises(rw.ReapLockHoldExpired, match="injected unlock failure"):
            hold.release()


def test_10637_default_hold_ends_inside_a_waiters_bound():
    """Any hold, husk and reservation recovery included, ends before a waiter's 30 s bound."""
    assert 0 < rw.DEFAULT_REAP_LOCK_HOLD_S < rw.DEFAULT_REAP_LOCK_TIMEOUT_S


def test_10637_explicit_release_reports_an_unlock_failure_once(tmp_path, monkeypatch):
    """``release`` raises on a failed unlock after closing the descriptor; a later close is quiet."""
    repo = init_repo(tmp_path)
    real_flock = fcntl.flock

    def flock(descriptor: Any, operation: int) -> Any:
        if operation == fcntl.LOCK_UN:
            raise OSError(errno.EIO, "injected unlock failure")
        return real_flock(descriptor, operation)

    with rw._ReapLock(repo, phase="husk-removal") as hold:
        monkeypatch.setattr(fcntl, "flock", flock)
        with pytest.raises(rw.ReapLockReleaseFailed, match=rw.REAP_LOCK_RELEASE_FAILED):
            hold.release()
        monkeypatch.setattr(fcntl, "flock", real_flock)
        assert not hold.is_held()
        assert not hold.expired
        assert _lock_is_free(repo)
    assert _lock_is_free(repo)


def test_10637_release_after_the_deadline_never_removes_when_the_watchdog_is_late(tmp_path, monkeypatch):
    """#10637 round 5, P1: a release 0.15 s past the hold deadline is expired, though the watchdog never ran.

    The review's reproducer: scheduling delays the watchdog (here it never
    runs) and the region's last read, the merged-head proof publication,
    finishes 0.15 s after the deadline. The release itself reads the deadline:
    the candidate is retained, the rest of the pass deferred, and its counted
    daily-cap slot given back, since nothing destructive started.
    """
    repo = init_repo(tmp_path)
    trees = _merged_trees(repo, monkeypatch, "late-release", 200)
    cap_file, today = _seed_cap(repo, 0)
    monkeypatch.setattr(rw, "_locked_region_budget_s", lambda: 2.0)
    monkeypatch.setattr(rw.threading, "Timer", _StalledWatchdog)
    real_publication = rw._record_merged_reuse_proof
    overdue: list[float] = []

    def publish_then_overrun(*args: Any, **kwargs: Any) -> Any:
        answer = real_publication(*args, **kwargs)
        if not overdue:
            deadline = rw._LOCKED_REGION_DEADLINE.get()
            assert deadline is not None
            time.sleep(max(0.0, deadline + 0.15 - time.monotonic()))
            overdue.append(time.monotonic() - deadline)
        return answer

    monkeypatch.setattr(rw, "_record_merged_reuse_proof", publish_then_overrun)
    attempts = _attempted_candidates(monkeypatch)
    results = rw.reap_worktrees(repo_root=repo, apply=True, live_cwds=set())

    assert overdue and overdue[0] >= 0.15, overdue
    first, second = (result_for(results, tree) for tree in trees)
    assert all(tree.is_dir() for tree in trees), "a release after the hold deadline authorized removal"
    assert first.action == "skipped", first.reason
    assert first.reason.startswith(rw.REAP_LOCK_HOLD_EXPIRED), first.reason
    assert second.action == "skipped", second.reason
    assert second.reason.startswith(f"{rw.REAP_LOCK_HOLD_EXPIRED}; deferred to the next pass"), second.reason
    assert [path.resolve() for path in attempts] == [trees[0].resolve()]
    assert _cap_count(cap_file, today) == 0
    assert not any(reaper_lifecycle.is_reap_pending(repo, tree) for tree in trees)
    assert _lock_is_free(repo)


def test_10637_husk_released_after_its_deadline_is_kept_when_the_watchdog_is_late(tmp_path, monkeypatch):
    """#10637 round 5: the husk path authorizes removal through the same release, so a late one keeps the husk."""
    repo = init_repo(tmp_path)
    husks = [repo / ".worktrees" / "dispatch" / "codex" / f"ww-late-{index}" for index in range(2)]
    for husk in husks:
        (husk / "site").mkdir(parents=True)
        _backdate_tree(husk, 2)
    monkeypatch.setattr(rw, "DEFAULT_REAP_LOCK_HOLD_S", 0.3)
    monkeypatch.setattr(rw.threading, "Timer", _StalledWatchdog)

    def slow_cwd_scan(_repo_root: Path) -> set[Path]:
        # The husk's last read under the lock outlasts its 0.3 s hold.
        time.sleep(0.5)
        return set()

    monkeypatch.setattr(rw, "_live_cwd_paths", slow_cwd_scan)
    results = rw._reap_dispatch_husks(repo, registered=set(), apply=True, live_cwds=set(), targets=None)

    first, second = (result_for(results, husk) for husk in husks)
    assert all((husk / "site").is_dir() for husk in husks), "a release after the hold deadline authorized removal"
    assert first.action == "skipped", first.reason
    assert first.reason.startswith(rw.REAP_LOCK_HOLD_EXPIRED), first.reason
    assert second.action == "skipped", second.reason
    assert second.reason.endswith(rw._DEFERRED), second.reason
    assert _lock_is_free(repo)


@pytest.mark.parametrize("check", ["ensure_held", "release"])
def test_10637_an_overdue_hold_is_expired_without_its_watchdog(tmp_path, monkeypatch, check):
    """``ensure_held`` and ``release`` read the deadline themselves: a delayed watchdog never extends a hold."""
    repo = init_repo(tmp_path)
    monkeypatch.setattr(rw.threading, "Timer", _StalledWatchdog)
    with rw._ReapLock(repo, phase="husk-removal", hold_deadline=time.monotonic() + 0.1) as hold:
        time.sleep(0.15)
        assert hold.is_held(), "the stalled watchdog ran"
        with pytest.raises(rw.ReapLockHoldExpired, match=rw.REAP_LOCK_HOLD_EXPIRED):
            getattr(hold, check)()
        assert hold.expired
        assert not hold.is_held()
        assert _lock_is_free(repo)
        with pytest.raises(rw.ReapLockHoldExpired):
            hold.release()
    assert _lock_is_free(repo)


def test_10637_on_time_release_is_not_expired_without_its_watchdog(tmp_path, monkeypatch):
    """The deadline read does not turn a timely release into an expired one."""
    repo = init_repo(tmp_path)
    monkeypatch.setattr(rw.threading, "Timer", _StalledWatchdog)
    with rw._ReapLock(repo, phase="husk-removal", hold_deadline=time.monotonic() + 10) as hold:
        hold.ensure_held()
        hold.release()
        assert not hold.expired
        assert _lock_is_free(repo)


@pytest.mark.parametrize("obstructed", ["after_removal", "throughout"])
def test_10637_a_cap_lock_failure_never_frees_a_spent_slot(tmp_path, monkeypatch, obstructed):
    """#10637 round 5, P1: the review's seed, one recorded removal today and a ceiling of two.

    Another process holds the daily-cap lock past the (test) 0.05 s bound,
    either from the end of the first removal or for the whole first pass. A
    second pass then runs with the lock free. Actual removals, the seed
    included, never exceed the ceiling, and every one is counted: the slot is
    counted before removal starts, so no failure afterwards can free it.
    """
    repo = init_repo(tmp_path)
    trees = _merged_trees(repo, monkeypatch, f"cap-lock-{obstructed.replace('_', '-')}", 210)
    monkeypatch.setenv("LU_REAPER_MAX_REAPS_PER_DAY", "1")
    monkeypatch.setattr(rw, "_LOCKED_LOCK_WAIT_S", 0.05)
    cap_file, today = _seed_cap(repo, 1)
    held: list[int] = []
    if obstructed == "throughout":
        _hold_cap_lock(repo, held)
    else:
        real_remove = worktree_claims.git_worktree_remove

        def remove_then_obstruct(*args: Any, **kwargs: Any) -> Any:
            answer = real_remove(*args, **kwargs)
            if not held:
                _hold_cap_lock(repo, held)
            return answer

        monkeypatch.setattr(rw.worktree_claims, "git_worktree_remove", remove_then_obstruct)
    raised: BaseException | None = None
    try:
        try:
            rw.reap_worktrees(repo_root=repo, apply=True, live_cwds=set(), target_paths=[trees[0]])
        except Exception as exc:  # the first pass may stop on the obstructed lock
            raised = exc
        assert held, "the daily-cap lock was never obstructed"
    finally:
        for descriptor in held:
            os.close(descriptor)
    second = result_for(
        rw.reap_worktrees(repo_root=repo, apply=True, live_cwds=set(), target_paths=[trees[1]]), trees[1]
    )

    removed = sum(not tree.exists() for tree in trees)
    assert 1 + removed <= 2, f"{1 + removed} removals against a ceiling of 2 ({second.action}: {second.reason})"
    assert _cap_count(cap_file, today) == 1 + removed
    if obstructed == "after_removal":
        assert raised is None, repr(raised)
        assert not trees[0].exists()
        assert second.action == "skipped" and "cap ceiling reached" in second.reason, second.reason
    else:
        assert isinstance(raised, lock_wait_bound.LockWaitTimeout), repr(raised)
        assert trees[0].is_dir()
        assert second.action == "removed", second.reason
    assert not any(reaper_lifecycle.is_reap_pending(repo, tree) for tree in trees)
    assert _lock_is_free(repo)


@pytest.mark.parametrize(
    ("remove_error", "spent"),
    [
        ("artifact preservation failed: injected; refusing worktree removal", False),
        ("fatal: injected removal failure", True),
    ],
    ids=["preservation_refused", "git_failed"],
)
def test_10637_cap_slot_is_given_back_only_when_nothing_destructive_started(tmp_path, monkeypatch, remove_error, spent):
    """A refused preservation runs before destructive Git and gives the slot back; a Git failure keeps it spent."""
    repo = init_repo(tmp_path)
    tree = add_worktree(repo, "codex/cap-give-back")
    patch_gh(monkeypatch, {"codex/cap-give-back": [{"number": 220, "state": "MERGED"}]})
    monkeypatch.setenv("LU_REAPER_MAX_REAPS_PER_DAY", "5")
    cap_file, today = _seed_cap(repo, 1)
    counted_before_removal: list[int] = []

    def remove(*_args: Any, **_kwargs: Any) -> str:
        counted_before_removal.append(_cap_count(cap_file, today))
        return remove_error

    monkeypatch.setattr(rw.worktree_claims, "git_worktree_remove", remove)
    result = result_for(rw.reap_worktrees(repo_root=repo, apply=True, live_cwds=set()), tree)

    assert counted_before_removal == [2]
    assert tree.is_dir()
    assert result.action == ("error" if spent else "skipped"), result.reason
    assert result.error is None or rw.REAP_CLEANUP_FAILED not in result.error, result.error
    assert _cap_count(cap_file, today) == (2 if spent else 1)
    assert not reaper_lifecycle.is_reap_pending(repo, tree)


def test_10637_a_slot_that_cannot_be_given_back_stays_spent_and_stops_the_run(tmp_path, monkeypatch):
    """Giving a slot back can fail; the slot then stays spent, the failure is reported and nothing more is removed."""
    repo = init_repo(tmp_path)
    trees = _merged_trees(repo, monkeypatch, "cap-give-back-fails", 230)
    monkeypatch.setenv("LU_REAPER_MAX_REAPS_PER_DAY", "5")
    monkeypatch.setattr(rw, "_LOCKED_LOCK_WAIT_S", 0.05)
    cap_file, today = _seed_cap(repo, 1)
    held: list[int] = []

    def refuse_then_obstruct(*_args: Any, **_kwargs: Any) -> str:
        if not held:
            _hold_cap_lock(repo, held)
        return "artifact preservation failed: injected; refusing worktree removal"

    monkeypatch.setattr(rw.worktree_claims, "git_worktree_remove", refuse_then_obstruct)
    try:
        results = rw.reap_worktrees(repo_root=repo, apply=True, live_cwds=set())
    finally:
        for descriptor in held:
            os.close(descriptor)

    first, second = (result_for(results, tree) for tree in trees)
    assert all(tree.is_dir() for tree in trees)
    assert first.action == "skipped", first.reason
    assert first.error is not None
    assert first.error.startswith(f"{rw.REAP_CLEANUP_FAILED}: daily-cap slot release (the slot stays spent)")
    assert "LockWaitTimeout" in first.error, first.error
    assert second.reason.startswith(f"{rw.REAP_CLEANUP_FAILED}; deferred to the next pass"), second.reason
    assert _cap_count(cap_file, today) == 2
    assert not any(reaper_lifecycle.is_reap_pending(repo, tree) for tree in trees)
    assert _lock_is_free(repo)
