"""Pytest temp-run retention (#10779): keep the newest N ``pytest-<N>`` run directories.

Every test builds a fake ``pytest-of-<user>`` root in ``tmp_path``; the real pytest
temp root is never touched. Inode change times cannot be backdated, so fake runs
are made idle by pruning with a clock ``IDLE_AGE_HOURS`` ahead (``_prune``), unless
a test is about the grace window itself.
"""

from __future__ import annotations

import functools
import getpass
import os
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
from _pytest.tmpdir import TempPathFactory

import tests.conftest as retention

pytest_plugins = ("pytester",)


@pytest.fixture
def root(tmp_path: Path) -> Path:
    path = tmp_path / "pytest-of-tester"
    path.mkdir()
    return path


IDLE_AGE_HOURS = 48
HOUR = 3600


def _later(hours: float = IDLE_AGE_HOURS) -> float:
    return time.time() + hours * HOUR


def _prune(basetemp: Path, keep: int, **kwargs: object) -> list[Path]:
    """Prune as if ``IDLE_AGE_HOURS`` had passed since every run was last changed."""
    kwargs.setdefault("now", _later())
    return retention._prune_pytest_run_dirs(basetemp, keep, **kwargs)  # type: ignore[arg-type]


def _age(run: Path, hours: float = IDLE_AGE_HOURS) -> None:
    """Backdate the mtimes of ``run`` and everything in it (inode change times stay current)."""
    stamp = time.time() - hours * HOUR
    for path in [run, *run.rglob("*")]:
        os.utime(path, (stamp, stamp), follow_symlinks=False)


def _runs(root: Path, *numbers: int) -> dict[int, Path]:
    made = {}
    for number in numbers:
        run = root / f"pytest-{number}"
        (run / "test_x0").mkdir(parents=True)
        (run / "test_x0" / "payload.txt").write_text("x", encoding="utf-8")
        _age(run)
        made[number] = run
    return made


def _names(root: Path) -> list[str]:
    return sorted(entry.name for entry in root.iterdir())


def test_keeps_newest_n_by_run_number_not_lexical_order(root: Path) -> None:
    runs = _runs(root, 2, 9, 10, 11, 100)

    removed = _prune(runs[100], 3)

    assert _names(root) == ["pytest-10", "pytest-100", "pytest-11"]
    assert sorted(path.name for path in removed) == ["pytest-2", "pytest-9"]


def test_never_removes_the_current_run_even_when_it_is_not_among_the_newest(root: Path) -> None:
    runs = _runs(root, 1, 2, 3, 4, 5)

    _prune(runs[1], 2)

    assert _names(root) == ["pytest-1", "pytest-4", "pytest-5"]


def test_fewer_runs_than_keep_removes_nothing(root: Path) -> None:
    runs = _runs(root, 1, 2)

    assert _prune(runs[2], 3) == []
    assert _names(root) == ["pytest-1", "pytest-2"]


def test_symlinked_run_is_neither_followed_nor_removed(root: Path, tmp_path: Path) -> None:
    runs = _runs(root, 5, 6, 7)
    outside = tmp_path / "outside"
    (outside / "keep").mkdir(parents=True)
    (outside / "keep" / "precious.txt").write_text("data", encoding="utf-8")
    (root / "pytest-1").symlink_to(outside, target_is_directory=True)

    _prune(runs[7], 1)

    assert (root / "pytest-1").is_symlink()
    assert (outside / "keep" / "precious.txt").read_text(encoding="utf-8") == "data"
    assert _names(root) == ["pytest-1", "pytest-7"]


def test_symlink_inside_an_old_run_is_removed_without_touching_its_target(root: Path, tmp_path: Path) -> None:
    runs = _runs(root, 1, 2)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "precious.txt").write_text("data", encoding="utf-8")
    (runs[1] / "link").symlink_to(outside, target_is_directory=True)
    _age(runs[1])

    _prune(runs[2], 1)

    assert _names(root) == ["pytest-2"]
    assert (outside / "precious.txt").read_text(encoding="utf-8") == "data"


def test_directories_owned_by_another_account_are_skipped(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runs = _runs(root, 1, 2, 3)
    other_uid = os.geteuid() + 1
    monkeypatch.setattr(retention.os, "geteuid", lambda: other_uid)

    assert _prune(runs[3], 1) == []
    assert _names(root) == ["pytest-1", "pytest-2", "pytest-3"]


def test_unrelated_entries_are_ignored(root: Path) -> None:
    runs = _runs(root, 1, 2, 3)
    (root / "pytest-current").symlink_to(runs[3], target_is_directory=True)
    (root / "pytest-4.bak").mkdir()
    (root / "pytest-5").write_text("a file, not a run", encoding="utf-8")
    (root / "notes").mkdir()

    _prune(runs[3], 1)

    assert _names(root) == ["notes", "pytest-3", "pytest-4.bak", "pytest-5", "pytest-current"]


def test_root_that_is_not_a_pytest_of_user_directory_is_left_alone(tmp_path: Path) -> None:
    other = tmp_path / "scratch"
    other.mkdir()
    runs = _runs(other, 1, 2, 3)

    assert _prune(runs[3], 1) == []
    assert _names(other) == ["pytest-1", "pytest-2", "pytest-3"]


def test_custom_basetemp_name_is_left_alone(root: Path) -> None:
    _runs(root, 1, 2, 3)
    custom = root / "pytest-RC"
    custom.mkdir()

    assert _prune(custom, 1) == []
    assert _names(root) == ["pytest-1", "pytest-2", "pytest-3", "pytest-RC"]


def test_symlinked_root_is_refused(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    runs = _runs(real, 1, 2, 3)
    link = tmp_path / "pytest-of-link"
    link.symlink_to(real, target_is_directory=True)

    assert _prune(link / runs[3].name, 1) == []
    assert _names(real) == ["pytest-1", "pytest-2", "pytest-3"]


def test_run_locked_by_a_live_process_is_kept(root: Path) -> None:
    runs = _runs(root, 1, 2, 3)
    (runs[1] / ".lock").write_text(str(os.getpid()), encoding="utf-8")
    _age(runs[1])

    _prune(runs[3], 1)

    assert _names(root) == ["pytest-1", "pytest-3"]


def test_run_locked_by_a_dead_process_is_removed(root: Path) -> None:
    runs = _runs(root, 1, 2)
    dead = subprocess.Popen([sys.executable, "-c", "pass"])
    dead.wait(timeout=60)
    (runs[1] / ".lock").write_text(str(dead.pid), encoding="utf-8")
    _age(runs[1])

    _prune(runs[2], 1)

    assert _names(root) == ["pytest-2"]


def _swap_after_idle_check(monkeypatch: pytest.MonkeyPatch, swap: object) -> list[str]:
    """Run ``swap`` once, right after the idle check and before deletion (the TOCTOU window)."""
    original = retention._pytest_run_dir_in_use
    done: list[str] = []

    def checked_then_swapped(*args: object, **kwargs: object) -> bool:
        in_use = original(*args, **kwargs)
        if not done:
            swap()  # type: ignore[operator]
            done.append("swapped")
        return in_use

    monkeypatch.setattr(retention, "_pytest_run_dir_in_use", checked_then_swapped)
    return done


def test_symlink_swapped_in_after_enumeration_is_not_followed(
    root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runs = _runs(root, 1, 2)
    notes = root / "notes"
    notes.mkdir()
    (notes / "precious.txt").write_text("data", encoding="utf-8")

    def swap() -> None:
        runs[1].rename(root / "moved-1")
        runs[1].symlink_to(notes, target_is_directory=True)

    done = _swap_after_idle_check(monkeypatch, swap)

    assert _prune(runs[2], 1) == []

    assert done == ["swapped"]
    assert (notes / "precious.txt").read_text(encoding="utf-8") == "data"
    assert runs[1].is_symlink()
    assert (root / "moved-1" / "test_x0" / "payload.txt").is_file()
    assert _names(root) == ["moved-1", "notes", "pytest-1", "pytest-2"]


def test_directory_swapped_in_after_enumeration_is_not_deleted(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runs = _runs(root, 1, 2)
    notes = root / "notes"
    notes.mkdir()
    (notes / "precious.txt").write_text("data", encoding="utf-8")

    def swap() -> None:
        runs[1].rename(root / "moved-1")
        notes.rename(runs[1])

    done = _swap_after_idle_check(monkeypatch, swap)
    real_rename = os.rename
    fd_renames: list[object] = []

    def recording_rename(src: object, dst: object, **kwargs: object) -> None:
        if "src_dir_fd" in kwargs:
            fd_renames.append(src)
        real_rename(src, dst, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(retention.os, "rename", recording_rename)

    assert _prune(runs[2], 1) == []

    assert done == ["swapped"]
    assert fd_renames == []  # the replacement under the run's name is never even moved
    assert (runs[1] / "precious.txt").read_text(encoding="utf-8") == "data"
    assert (root / "moved-1" / "test_x0" / "payload.txt").is_file()
    assert _names(root) == ["moved-1", "pytest-1", "pytest-2"]


def test_directory_reusing_the_inode_number_after_the_idle_check_is_not_deleted(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Sol r2 blocker 1: remove the idle run, recreate the name until the kernel
    # hands out the same inode number, then put a live payload in it.
    runs = _runs(root, 1, 2)
    original_inode = runs[1].stat().st_ino
    reused: list[bool] = []

    def recreate_with_the_same_inode() -> None:
        shutil.rmtree(runs[1])
        for _attempt in range(64):
            runs[1].mkdir()
            if runs[1].stat().st_ino == original_inode:
                reused.append(True)
                break
            runs[1].rmdir()
        else:
            runs[1].mkdir()
            reused.append(False)
        (runs[1] / "new-payload.txt").write_text("live", encoding="utf-8")

    _swap_after_idle_check(monkeypatch, recreate_with_the_same_inode)

    _prune(runs[2], 1)

    assert (runs[1] / "new-payload.txt").read_text(encoding="utf-8") == "live"
    # The pinned descriptor keeps the original inode allocated, so its number cannot come back.
    assert reused == [False]


def _reaping_entries(root: Path) -> list[Path]:
    return [path for path in root.iterdir() if path.name.startswith(".pytest-1.reaping-")]


def test_replacement_under_the_reaping_name_is_left_untouched(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Sol r2 blocker 1 (sibling race): an empty directory substituted under the reaping name.
    runs = _runs(root, 1, 2)
    real_rmtree = retention.shutil.rmtree
    marker_mtime = 1_000_000_000

    def rmtree_then_substitute(*args: object, **kwargs: object) -> None:
        real_rmtree(*args, **kwargs)  # type: ignore[arg-type]
        (reaping,) = _reaping_entries(root)
        reaping.rename(root / "moved-1")
        reaping.mkdir()
        os.utime(reaping, (marker_mtime, marker_mtime))

    monkeypatch.setattr(retention.shutil, "rmtree", rmtree_then_substitute)

    assert _prune(runs[2], 1) == []

    (substitute,) = _reaping_entries(root)
    # The very same directory, never removed and recreated (ext4 may even hand back its inode number).
    assert substitute.stat().st_mtime == marker_mtime
    assert (root / "moved-1").is_dir()


def test_empty_replacement_removed_in_the_last_instant_is_recreated(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runs = _runs(root, 1, 2)
    real_rmdir = os.rmdir

    def substitute_then_rmdir(path: object, *args: object, dir_fd: int | None = None, **kwargs: object) -> None:
        if isinstance(path, str) and path.startswith(".pytest-1.reaping-") and dir_fd is not None:
            os.rename(path, "moved-1", src_dir_fd=dir_fd, dst_dir_fd=dir_fd)
            os.mkdir(path, dir_fd=dir_fd)
        real_rmdir(path, *args, dir_fd=dir_fd, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(retention.os, "rmdir", substitute_then_rmdir)

    assert _prune(runs[2], 1) == []

    (substitute,) = _reaping_entries(root)
    assert substitute.is_dir() and (root / "moved-1").is_dir()


def test_replacement_renamed_in_the_last_instant_is_put_back(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runs = _runs(root, 1, 2)
    real_rename = os.rename
    swapped: list[str] = []

    def substitute_then_rename(src: object, dst: object, **kwargs: object) -> None:
        if src == "pytest-1" and not swapped:
            real_rename(runs[1], root / "moved-1")
            runs[1].mkdir()
            (runs[1] / "precious.txt").write_text("data", encoding="utf-8")
            swapped.append("swapped")
        real_rename(src, dst, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(retention.os, "rename", substitute_then_rename)

    assert _prune(runs[2], 1) == []

    assert swapped == ["swapped"]
    assert (runs[1] / "precious.txt").read_text(encoding="utf-8") == "data"
    assert _reaping_entries(root) == []


def test_name_reused_while_the_run_is_being_deleted_is_not_removed(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runs = _runs(root, 1, 2)
    real_rmtree = retention.shutil.rmtree

    def rmtree_while_name_is_reused(*args: object, **kwargs: object) -> None:
        # Mid-deletion, the run name is taken over by a fresh (empty) directory.
        if runs[1].exists():
            runs[1].rename(root / "moved-1")
        runs[1].mkdir()
        real_rmtree(*args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(retention.shutil, "rmtree", rmtree_while_name_is_reused)

    _prune(runs[2], 1)

    assert runs[1].is_dir() and not any(runs[1].iterdir())


@pytest.mark.skipif(os.geteuid() == 0, reason="root reads files regardless of mode")
def test_unreadable_lock_naming_a_live_process_keeps_the_run(root: Path) -> None:
    runs = _runs(root, 1, 2)
    lock = runs[1] / ".lock"
    lock.write_text(str(os.getpid()), encoding="utf-8")
    lock.chmod(0)
    _age(runs[1])
    try:
        assert _prune(runs[2], 1) == []
    finally:
        lock.chmod(stat.S_IRUSR | stat.S_IWUSR)

    assert _names(root) == ["pytest-1", "pytest-2"]


@pytest.mark.parametrize("content", ["", "   \n", "garbage", "12x", "0", "-5", "9" * 100])
def test_empty_or_malformed_lock_is_unknown_and_keeps_the_run(root: Path, content: str) -> None:
    runs = _runs(root, 1, 2)
    (runs[1] / ".lock").write_text(content, encoding="utf-8")
    _age(runs[1])

    assert _prune(runs[2], 1) == []
    assert _names(root) == ["pytest-1", "pytest-2"]


def test_lock_that_is_not_a_regular_file_keeps_the_run(root: Path, tmp_path: Path) -> None:
    runs = _runs(root, 1, 2)
    target = tmp_path / "pid"
    target.write_text("1", encoding="utf-8")
    (runs[1] / ".lock").symlink_to(target)
    _age(runs[1])

    assert _prune(runs[2], 1) == []
    assert _names(root) == ["pytest-1", "pytest-2"]


def test_lock_naming_another_accounts_process_keeps_the_run(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runs = _runs(root, 1, 2)
    (runs[1] / ".lock").write_text("4242", encoding="utf-8")
    _age(runs[1])

    def foreign(pid: int, sig: int) -> None:
        raise PermissionError(1, "Operation not permitted")

    monkeypatch.setattr(retention.os, "kill", foreign)

    assert _prune(runs[2], 1) == []
    assert _names(root) == ["pytest-1", "pytest-2"]


def test_recently_changed_lockless_run_is_kept_until_the_grace_window_passes(root: Path) -> None:
    runs = _runs(root, 1, 2)
    grace = retention._PYTEST_TMP_GRACE_HOURS_DEFAULT

    assert _prune(runs[2], 1, now=_later(grace - 1)) == []
    assert _names(root) == ["pytest-1", "pytest-2"]

    assert [path.name for path in _prune(runs[2], 1, now=_later(grace + 1))] == ["pytest-1"]


def test_fresh_entry_deep_in_an_old_run_restarts_its_grace_window(root: Path) -> None:
    runs = _runs(root, 1, 2)
    now = _later()
    deep = runs[1] / "test_x0" / "a" / "b"
    deep.mkdir(parents=True)
    (deep / "late.txt").write_text("x", encoding="utf-8")
    _age(runs[1])
    os.utime(deep / "late.txt", (now, now))  # only this nested file is fresh at ``now``

    assert _prune(runs[2], 1, now=now) == []
    assert _names(root) == ["pytest-1", "pytest-2"]


def test_inode_change_time_counts_as_activity(root: Path) -> None:
    # Content extracted with preserved (old) mtimes is still new.
    runs = _runs(root, 1, 2)

    assert retention._prune_pytest_run_dirs(runs[2], 1) == []
    assert _names(root) == ["pytest-1", "pytest-2"]


@pytest.mark.parametrize("changed", [".", "test_x0/payload.txt"])
def test_inode_change_anywhere_in_a_run_counts_as_activity(root: Path, changed: str) -> None:
    runs = _runs(root, 1, 2)
    settled = max(path.lstat().st_ctime for path in [runs[1], *runs[1].rglob("*")])
    time.sleep(0.1)
    (runs[1] / changed).chmod(0o700)  # changes its ctime only
    # At ``now`` everything else has been quiet for just over the floor; the chmod has not.
    now = settled + HOUR + 0.05

    assert _prune(runs[2], 1, now=now, grace_seconds=HOUR) == []
    assert _names(root) == ["pytest-1", "pytest-2"]


def _lockless_factory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    """A real TempPathFactory with retention count 0: its run has no ``.lock``."""
    temproot = tmp_path / "temproot"
    temproot.mkdir()
    monkeypatch.setenv("PYTEST_DEBUG_TEMPROOT", str(temproot))
    factory = TempPathFactory(None, 0, "all", trace=lambda *_args: None, _ispytest=True)
    active = factory.getbasetemp()
    payload = factory.mktemp("work") / "payload.txt"
    payload.write_text("live", encoding="utf-8")
    assert not (active / ".lock").exists()
    return active, payload


def _newer_runs(active: Path) -> Path:
    number = int(active.name.removeprefix("pytest-"))
    return _runs(active.parent, number + 1, number + 2, number + 3)[number + 3]


def test_active_lockless_session_from_a_real_factory_is_kept(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    active, payload = _lockless_factory(tmp_path, monkeypatch)

    retention._prune_pytest_run_dirs(_newer_runs(active), 1)

    assert payload.read_text(encoding="utf-8") == "live"


def test_lockless_session_with_old_top_level_and_a_fresh_nested_payload_is_kept(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Sol r2 blocker 2: root and direct entries aged past the grace window, nested payload just updated.
    active, payload = _lockless_factory(tmp_path, monkeypatch)
    stamp = time.time() - IDLE_AGE_HOURS * HOUR
    for path in [active, *active.iterdir()]:
        os.utime(path, (stamp, stamp), follow_symlinks=False)
    payload.write_text("updated", encoding="utf-8")
    os.utime(payload.parent, (stamp, stamp))

    retention._prune_pytest_run_dirs(_newer_runs(active), 1)

    assert payload.read_text(encoding="utf-8") == "updated"


def test_run_whose_activity_scan_hits_the_entry_cap_is_kept(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runs = _runs(root, 1, 2)  # pytest-1 holds two entries: test_x0 and its payload
    monkeypatch.setattr(retention, "_PYTEST_TMP_SCAN_MAX_ENTRIES", 1)

    assert _prune(runs[2], 1) == []

    monkeypatch.setattr(retention, "_PYTEST_TMP_SCAN_MAX_ENTRIES", 2)
    assert [path.name for path in _prune(runs[2], 1)] == ["pytest-1"]


def test_runs_not_reached_before_the_scan_deadline_are_kept(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runs = _runs(root, 1, 2, 3)
    (root / "pytest-0").mkdir()  # empty: its own scan has no entry at which to notice the deadline
    monkeypatch.setattr(retention, "_PYTEST_TMP_SCAN_SECONDS", -1.0)

    assert _prune(runs[3], 1) == []
    assert _names(root) == ["pytest-0", "pytest-1", "pytest-2", "pytest-3"]


def test_activity_scan_past_its_deadline_is_unknown(root: Path) -> None:
    runs = _runs(root, 1)
    fd = os.open(runs[1], os.O_RDONLY | os.O_DIRECTORY)
    try:
        assert retention._pytest_run_newest_activity(fd, deadline=time.monotonic() - 1, max_entries=10**6) is None
        assert retention._pytest_run_newest_activity(fd, deadline=time.monotonic() + 60, max_entries=10**6)
    finally:
        os.close(fd)


@pytest.mark.skipif(os.geteuid() == 0, reason="root reads directories regardless of mode")
def test_run_with_an_unreadable_subdirectory_is_kept(root: Path) -> None:
    runs = _runs(root, 1, 2)
    locked = runs[1] / "test_x0"
    locked.chmod(0)
    fd = os.open(runs[1], os.O_RDONLY | os.O_DIRECTORY)
    try:
        assert retention._pytest_run_newest_activity(fd, deadline=time.monotonic() + 60, max_entries=10**6) is None
        assert _prune(runs[2], 1) == []
    finally:
        os.close(fd)
        locked.chmod(stat.S_IRWXU)

    assert _names(root) == ["pytest-1", "pytest-2"]


def test_grace_below_the_floor_is_refused_before_anything_is_deleted(root: Path) -> None:
    runs = _runs(root, 1, 2)

    for grace_seconds in (0.0, -1.0, HOUR - 1, float("nan")):
        with pytest.raises(ValueError):
            _prune(runs[2], 1, grace_seconds=grace_seconds)

    assert _names(root) == ["pytest-1", "pytest-2"]


def test_grace_hours_default_override_and_invalid_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LU_PYTEST_TMP_GRACE_HOURS", raising=False)
    assert retention._pytest_tmp_grace_seconds() == 12 * 3600
    monkeypatch.setenv("LU_PYTEST_TMP_GRACE_HOURS", "1")
    assert retention._pytest_tmp_grace_seconds() == 3600
    monkeypatch.setenv("LU_PYTEST_TMP_GRACE_HOURS", "36.5")
    assert retention._pytest_tmp_grace_seconds() == 36.5 * 3600
    for bad in ("0.99", "0.5", "0", "-1", "soon", "inf", "nan"):
        monkeypatch.setenv("LU_PYTEST_TMP_GRACE_HOURS", bad)
        with pytest.raises(ValueError):
            retention._pytest_tmp_grace_seconds()


def test_keep_runs_default_and_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LU_PYTEST_TMP_KEEP_RUNS", raising=False)
    assert retention._pytest_tmp_keep_runs() == 3
    monkeypatch.setenv("LU_PYTEST_TMP_KEEP_RUNS", "  ")
    assert retention._pytest_tmp_keep_runs() == 3
    monkeypatch.setenv("LU_PYTEST_TMP_KEEP_RUNS", "7")
    assert retention._pytest_tmp_keep_runs() == 7


@pytest.mark.parametrize("value", ["0", "-1", "three", "1.5"])
def test_keep_runs_rejects_invalid_values(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("LU_PYTEST_TMP_KEEP_RUNS", value)
    with pytest.raises(ValueError):
        retention._pytest_tmp_keep_runs()


def _session(basetemp: Path) -> SimpleNamespace:
    factory = SimpleNamespace(_basetemp=basetemp, getbasetemp=lambda: basetemp)
    return SimpleNamespace(config=SimpleNamespace(_tmp_path_factory=factory), exitstatus=pytest.ExitCode.OK)


def test_session_finish_prunes_and_reports(
    root: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    runs = _runs(root, 1, 2, 3, 4)
    monkeypatch.delenv("LU_PYTEST_TMP_KEEP_RUNS", raising=False)
    monkeypatch.delenv("LU_PYTEST_TMP_GRACE_HOURS", raising=False)
    monkeypatch.delenv("LU_PYTEST_TMP_BUDGET_GB", raising=False)
    monkeypatch.setattr(
        retention, "_prune_pytest_run_dirs", functools.partial(retention._prune_pytest_run_dirs, now=_later())
    )
    session = _session(runs[4])

    retention.pytest_sessionfinish(session, 0)

    assert _names(root) == ["pytest-2", "pytest-3", "pytest-4"]
    out = capsys.readouterr().out
    assert "removed 1 older run directories (keeping newest 3)" in out
    assert session.exitstatus == pytest.ExitCode.OK


def test_session_finish_fails_on_invalid_keep_without_deleting(
    root: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    runs = _runs(root, 1, 2, 3, 4)
    monkeypatch.setenv("LU_PYTEST_TMP_KEEP_RUNS", "0")
    session = _session(runs[4])

    retention.pytest_sessionfinish(session, 0)

    assert session.exitstatus == pytest.ExitCode.TESTS_FAILED
    assert "invalid LU_PYTEST_TMP_KEEP_RUNS='0'" in capsys.readouterr().out
    assert _names(root) == ["pytest-1", "pytest-2", "pytest-3", "pytest-4"]


@pytest.mark.parametrize("value", ["-1", "0", "0.5"])
def test_session_finish_fails_on_invalid_grace_without_deleting(
    root: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], value: str
) -> None:
    # Sol r2 blocker 2: a zero grace let a fresh lockless session lose its payload.
    runs = _runs(root, 1, 2, 3, 4)
    monkeypatch.delenv("LU_PYTEST_TMP_KEEP_RUNS", raising=False)
    monkeypatch.setenv("LU_PYTEST_TMP_GRACE_HOURS", value)
    monkeypatch.setattr(
        retention, "_prune_pytest_run_dirs", functools.partial(retention._prune_pytest_run_dirs, now=_later())
    )
    session = _session(runs[4])

    retention.pytest_sessionfinish(session, 0)

    assert session.exitstatus == pytest.ExitCode.TESTS_FAILED
    out = capsys.readouterr().out
    assert f"invalid LU_PYTEST_TMP_GRACE_HOURS={value!r}" in out and "hours >= 1" in out
    assert _names(root) == ["pytest-1", "pytest-2", "pytest-3", "pytest-4"]


def test_real_session_hook_prunes_old_runs_in_a_nested_pytest(
    pytester: pytest.Pytester, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = Path(retention.__file__).resolve().parents[1]
    temp_root = tmp_path / "temproot"
    user_root = temp_root / f"pytest-of-{getpass.getuser()}"
    old_runs = _runs(user_root, 1, 2, 3, 4, 5)
    pytester.makeconftest(
        "import importlib.util\n"
        f"spec = importlib.util.spec_from_file_location('project_tests_conftest', {str(repo / 'tests' / 'conftest.py')!r})\n"
        "project_tests_conftest = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(project_tests_conftest)\n"
        "pytest_sessionfinish = project_tests_conftest.pytest_sessionfinish\n"
        # The fake runs' inode change times are current: prune with a clock IDLE_AGE_HOURS ahead.
        "import functools, time\n"
        "project_tests_conftest._prune_pytest_run_dirs = functools.partial(\n"
        f"    project_tests_conftest._prune_pytest_run_dirs, now=time.time() + {IDLE_AGE_HOURS * HOUR})\n"
    )
    pytester.makepyfile("def test_uses_tmp(tmp_path):\n    (tmp_path / 'payload').write_text('x')\n")
    monkeypatch.setenv("PYTHONPATH", os.pathsep.join(filter(None, [str(repo), os.environ.get("PYTHONPATH", "")])))
    monkeypatch.delenv("LU_PYTEST_TMP_KEEP_RUNS", raising=False)
    monkeypatch.delenv("LU_PYTEST_TMP_GRACE_HOURS", raising=False)
    monkeypatch.delenv("LU_PYTEST_TMP_BUDGET_GB", raising=False)

    result = pytester.runpytest_subprocess(
        "-q", "-s", "-p", "no:cacheprovider", "--basetemp", str(user_root / "pytest-6")
    )

    assert result.ret == 0, result.stdout.str() + result.stderr.str()
    survivors = _names(user_root)
    assert "pytest-6" in survivors  # the nested run's own directory
    assert len(survivors) == 3
    assert not (old_runs[1].exists() or old_runs[2].exists() or old_runs[3].exists())
    assert "older run directories (keeping newest 3)" in result.stdout.str()
