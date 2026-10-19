"""Catch-up regressions for #11098, using disposable repositories only."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import pytest

from scripts.orchestration import reap_worktrees as rw
from tests.orchestration import test_reap_worktrees_clean_pushed as helpers

_template = helpers._template
repo = helpers.repo
free_fuser = helpers.free_fuser
_host_processes_out_of_scope = helpers._host_processes_out_of_scope


def test_stale_lock_metadata_does_not_block_or_replace_inode(repo: Path) -> None:
    lock = repo / ".git" / "worktree-reaper.lock"
    lock.write_text("999999999", encoding="utf-8")
    inode = lock.stat().st_ino
    with rw._ReapLock(repo, timeout_s=0):
        assert lock.read_text() == str(os.getpid())
    assert lock.stat().st_ino == inode


def test_crashed_lock_owner_releases_kernel_lock(repo: Path) -> None:
    code = (
        "import os, sys; from pathlib import Path; "
        "from scripts.orchestration.reap_worktrees import _ReapLock; "
        "lock = _ReapLock(Path(sys.argv[1])); lock.__enter__(); os._exit(0)"
    )
    subprocess.run([sys.executable, "-c", code, str(repo)], check=True, timeout=30)
    lock = repo / ".git" / "worktree-reaper.lock"
    previous = lock.read_text()
    inode = lock.stat().st_ino
    assert previous != str(os.getpid())
    with rw._ReapLock(repo, timeout_s=0):
        assert lock.read_text() == str(os.getpid())
    assert lock.stat().st_ino == inode


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="/proc/locks is Linux")
def test_lock_diagnostic_distinguishes_pid_text_from_live_kernel_owner(repo: Path) -> None:
    holder = rw._ReapLock(repo)
    with holder:
        holder.path.write_text("999999999", encoding="utf-8")
        with pytest.raises(rw._ReapLockBusy) as caught:
            with rw._ReapLock(repo, timeout_s=0):
                pytest.fail("a live holder must not be displaced")
        assert "recorded holder pid=999999999" in str(caught.value)
        assert f"kernel holder pid={os.getpid()}" in str(caught.value)


def test_kernel_owner_unavailable_is_unknown(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    original = Path.open

    def unavailable(path, *args, **kwargs):
        if str(path) == "/proc/locks":
            raise PermissionError("denied")
        return original(path, *args, **kwargs)

    with rw._ReapLock(repo):
        # Use a separate read descriptor; inode identity, not file contents, decides.
        with (repo / ".git" / "worktree-reaper.lock").open() as handle:
            monkeypatch.setattr(Path, "open", unavailable)
            assert rw._kernel_lock_holder(handle.fileno()) == "unknown"


def test_legacy_discovery_does_not_hold_sweep_lock(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    helpers.dispatch_tree(repo)
    queried = []

    def inspect(*args):
        with rw._ReapLock(repo, timeout_s=0):
            queried.append(True)
        return [], [], None, []

    monkeypatch.setattr(rw, "_review_pr_context", inspect)
    monkeypatch.setattr(rw, "_read_active_task_probe", lambda: set())
    rw.reap_worktrees(repo_root=repo, live_cwds=set(), apply=False)
    assert queried


def test_clean_pushed_inspection_and_size_do_not_hold_sweep_lock(
    repo: Path, free_fuser: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tree = helpers.dispatch_tree(repo)
    real_check = rw._clean_pushed_refusal
    real_size = rw._tree_size_mb
    inspected = []
    measured = []

    def check(info, ctx, claims, *, recheck, **kwargs):
        if not recheck:
            with rw._ReapLock(repo, timeout_s=0):
                inspected.append(info.path)
        return real_check(info, ctx, claims, recheck=recheck, **kwargs)

    def size(path):
        with rw._ReapLock(repo, timeout_s=0):
            measured.append(path)
        return real_size(path)

    monkeypatch.setattr(rw, "_clean_pushed_refusal", check)
    monkeypatch.setattr(rw, "_tree_size_mb", size)
    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)
    assert helpers.outcome_for(report, tree, repo).action == "removed"
    assert tree in inspected
    assert measured == [tree]


def test_contention_after_progress_reports_partial_results(
    repo: Path, free_fuser: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    trees = {helpers.dispatch_tree(repo, f"idle-{i}") for i in range(2)}
    enter = rw._ReapLock.__enter__
    calls = 0

    def contend(lock):
        nonlocal calls
        calls += 1
        if calls == 3:  # recovery, first removal, then second removal
            raise rw._ReapLockBusy("another worktree cleanup holds the lock; kernel holder pid=42")
        return enter(lock)

    monkeypatch.setattr(rw._ReapLock, "__enter__", contend)
    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)
    assert report.lock_busy
    assert len(report.removed) == 1
    assert sum(tree.exists() for tree in trees) == 1
    assert any(item.reason == report.refusal for item in report.skipped)
    assert len(helpers.abandon_log(repo)) == 1
    formatted = rw.format_clean_pushed_report(report)
    assert "1 removed" in formatted
    assert "stopped:" in formatted
    assert "nothing done" not in formatted


def test_exited_denied_process_does_not_poison_later_candidates(
    repo: Path, free_fuser: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tree = helpers.dispatch_tree(repo)
    scans = 0

    def scan(root, *, uninspectable, **kwargs):
        nonlocal scans
        scans += 1
        if scans == 1:
            uninspectable.append(424242)
        return False

    monkeypatch.setattr(rw, "_proc_users_inside", scan)
    seen = set()
    assert "uninspectable_process" in rw._process_refusal(tree, seen)
    assert rw._process_refusal(tree, seen) is None
    assert seen == {424242}  # diagnostic history is retained


def test_process_disappearing_during_denied_probe_is_not_retained(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    proc = tmp_path / "proc"
    base = helpers.fake_process(proc, 42, name="worker", ppid=1, uids=os.getuid())
    tree = tmp_path / "tree"
    tree.mkdir()
    readlink = os.readlink

    def exited(path):
        if Path(path).is_relative_to(base):
            if base.exists():
                shutil.rmtree(base)
            raise PermissionError("exited during inspection")
        return readlink(path)

    monkeypatch.setattr(os, "readlink", exited)
    monkeypatch.setattr(rw, "_uninspectable_same_user", helpers._REAL_UNINSPECTABLE)
    denied = []
    assert rw._proc_users_inside(tree, deadline=time.monotonic() + 2, proc_root=proc, uninspectable=denied) is False
    assert denied == []


@pytest.mark.parametrize("directory_state", ["same_user", "other_owner", "unreadable"])
def test_unreadable_live_process_status_is_fail_safe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, directory_state: str
) -> None:
    proc = tmp_path / "proc"
    base = helpers.fake_process(proc, 42, name="worker", ppid=1, uids=os.getuid())
    monkeypatch.setattr(rw, "_proc_status", lambda path: None)
    stat = Path.stat

    def directory_stat(path, *args, **kwargs):
        if path == base:
            if directory_state == "unreadable":
                raise PermissionError("denied")
            if directory_state == "other_owner":
                fields = list(stat(path, *args, **kwargs))
                fields[4] = os.getuid() + 1
                return os.stat_result(fields)
        return stat(path, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", directory_stat)
    assert helpers._REAL_UNINSPECTABLE(base, proc) is True


@pytest.mark.parametrize("stamp", [None, 1, "bad", "2026-01-01T00:00:00"])
def test_unknown_terminal_time_keeps_tree(repo: Path, free_fuser: Path, stamp) -> None:
    tree = helpers.dispatch_tree(repo)
    helpers.write_task(repo, "task-a", tree, finished_at=stamp)
    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)
    outcome = helpers.outcome_for(report, tree, repo)
    assert outcome.action == "skipped"
    assert outcome.reason == "task record task-a.json terminal time unknown"
    assert tree.is_dir()


@pytest.mark.parametrize("missing", ["HEAD", "index"])
def test_missing_admin_activity_source_is_unknown(repo: Path, missing: str) -> None:
    tree = helpers.dispatch_tree(repo)
    (helpers.admin_dir(tree) / missing).unlink()
    assert rw._tree_mtime_sources(tree, repo / ".git") == ([], None, f"{missing} missing; activity unknown")


def test_unresolvable_admin_activity_is_unknown(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tree = helpers.dispatch_tree(repo)
    monkeypatch.setattr(rw, "_worktree_git_dir", lambda path: None)
    assert rw._tree_mtime_sources(tree, repo / ".git") == ([], None, "git admin directory unresolvable")


def test_foreign_admin_activity_is_unknown(repo: Path, tmp_path: Path) -> None:
    tree = helpers.dispatch_tree(repo)
    other = tmp_path / "other"
    (other / "worktrees").mkdir(parents=True)
    assert rw._tree_mtime_sources(tree, other) == (
        [],
        None,
        "git admin directory is outside the repository's .git/worktrees/",
    )


def test_failed_tracked_activity_listing_is_unknown(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tree = helpers.dispatch_tree(repo)
    monkeypatch.setattr(rw, "_run", lambda args, **kwargs: subprocess.CompletedProcess(args, 1, "", "denied"))
    assert rw._tree_mtime_sources(tree, repo / ".git") == ([], None, "tracked-file activity unavailable")


def test_recent_terminal_time_keeps_tree_despite_old_record_mtime(repo: Path, free_fuser: Path) -> None:
    tree = helpers.dispatch_tree(repo)
    record = helpers.write_task(repo, "task-a", tree, finished_at=datetime.now(UTC).isoformat())
    helpers.age([record])
    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)
    outcome = helpers.outcome_for(report, tree, repo)
    assert outcome.action == "skipped"
    assert outcome.reason == "last activity 0 min ago (< 60 min)"
    assert tree.is_dir()


def test_inspection_index_rewrite_does_not_change_eligibility(repo: Path, free_fuser: Path) -> None:
    tree = helpers.dispatch_tree(repo)
    # Stale cached file stats, while the tracked file is still genuinely old.
    stamp = time.time() - 90 * 60
    os.utime(tree / "README.md", (stamp, stamp))
    before = rw.reap_clean_pushed(repo_root=repo)
    assert helpers.outcome_for(before, tree, repo).action == "would_remove"
    index = helpers.admin_dir(tree) / "index"
    index_before = index.stat().st_mtime_ns
    helpers.git(tree, "status", "--porcelain")
    assert index.stat().st_mtime_ns > index_before  # inspection really rewrote it
    after = rw.reap_clean_pushed(repo_root=repo, dry_run=False)
    assert helpers.outcome_for(after, tree, repo).action == "removed"


def test_undoing_observed_staged_only_edit_is_recent_activity(repo: Path, free_fuser: Path) -> None:
    tree = helpers.dispatch_tree(repo)
    # Stage an existing blob from another tracked path, without writing the
    # working file or HEAD. Resetting this edit changes only semantic index data.
    blob = helpers.git(tree, "rev-parse", "HEAD:.gitignore")
    helpers.git(tree, "update-index", "--cacheinfo", f"100644,{blob},README.md")
    dirty = rw.reap_clean_pushed(repo_root=repo, dry_run=False)
    assert helpers.outcome_for(dirty, tree, repo).reason == "dirty or untracked files"
    helpers.git(tree, "reset", "HEAD", "--", "README.md")
    assert helpers.git(tree, "status", "--porcelain") == ""
    clean = rw.reap_clean_pushed(repo_root=repo, dry_run=False)
    outcome = helpers.outcome_for(clean, tree, repo)
    assert outcome.action == "skipped"
    assert outcome.reason == "last activity 0 min ago (< 60 min)"
    assert tree.is_dir()


def test_inspection_preserves_dry_run_apply_set(repo: Path, free_fuser: Path) -> None:
    eligible = {helpers.dispatch_tree(repo, f"idle-{i}") for i in range(3)}
    dirty = helpers.dispatch_tree(repo, "dirty")
    (dirty / "README.md").write_text("uncommitted\n", encoding="utf-8")
    unpushed = helpers.dispatch_tree(repo, "unpushed")
    (unpushed / "README.md").write_text("unique commit\n", encoding="utf-8")
    helpers.git(unpushed, "commit", "-am", "unique")
    helpers.age_tree(unpushed, repo, "unpushed")
    active = helpers.dispatch_tree(repo, "active", status="running")
    recent = helpers.dispatch_tree(repo, "recent")
    # A write restored the original bytes. It is clean but genuinely recent.
    original = (recent / "README.md").read_bytes()
    (recent / "README.md").write_bytes(original)

    before = rw.reap_clean_pushed(repo_root=repo)
    expected = {p.relative_to(repo).as_posix() for p in eligible}
    assert {item.path for item in before.removed} == expected
    for tree in (*eligible, dirty, unpushed, active, recent):
        helpers.git(tree, "status", "--porcelain")
        subprocess.run(["du", "-s", str(tree)], capture_output=True, check=True, timeout=30)
    inspected = rw.reap_clean_pushed(repo_root=repo)
    assert {item.path for item in inspected.removed} == expected
    after = rw.reap_clean_pushed(repo_root=repo, dry_run=False)
    assert {item.path for item in after.removed} == expected
    assert all(not tree.exists() for tree in eligible)
    assert all(tree.is_dir() for tree in (dirty, unpushed, active, recent))
    assert (dirty / "README.md").read_text() == "uncommitted\n"
    assert {item["path"] for item in helpers.abandon_log(repo)} == expected
