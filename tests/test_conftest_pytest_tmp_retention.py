"""Pytest temp-run retention (#10779): keep the newest N ``pytest-<N>`` run directories.

Every test builds a fake ``pytest-of-<user>`` root in ``tmp_path``; the real pytest
temp root is never touched. Fake runs are aged past the idle grace window unless a
test is about that window.
"""

from __future__ import annotations

import getpass
import os
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


def _age(run: Path, hours: float = IDLE_AGE_HOURS) -> None:
    """Backdate ``run`` and its direct entries, the mtimes the idle check reads."""
    stamp = time.time() - hours * 3600
    for path in [run, *run.iterdir()]:
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

    removed = retention._prune_pytest_run_dirs(runs[100], 3)

    assert _names(root) == ["pytest-10", "pytest-100", "pytest-11"]
    assert sorted(path.name for path in removed) == ["pytest-2", "pytest-9"]


def test_never_removes_the_current_run_even_when_it_is_not_among_the_newest(root: Path) -> None:
    runs = _runs(root, 1, 2, 3, 4, 5)

    retention._prune_pytest_run_dirs(runs[1], 2)

    assert _names(root) == ["pytest-1", "pytest-4", "pytest-5"]


def test_fewer_runs_than_keep_removes_nothing(root: Path) -> None:
    runs = _runs(root, 1, 2)

    assert retention._prune_pytest_run_dirs(runs[2], 3) == []
    assert _names(root) == ["pytest-1", "pytest-2"]


def test_symlinked_run_is_neither_followed_nor_removed(root: Path, tmp_path: Path) -> None:
    runs = _runs(root, 5, 6, 7)
    outside = tmp_path / "outside"
    (outside / "keep").mkdir(parents=True)
    (outside / "keep" / "precious.txt").write_text("data", encoding="utf-8")
    (root / "pytest-1").symlink_to(outside, target_is_directory=True)

    retention._prune_pytest_run_dirs(runs[7], 1)

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

    retention._prune_pytest_run_dirs(runs[2], 1)

    assert _names(root) == ["pytest-2"]
    assert (outside / "precious.txt").read_text(encoding="utf-8") == "data"


def test_directories_owned_by_another_account_are_skipped(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runs = _runs(root, 1, 2, 3)
    other_uid = os.geteuid() + 1
    monkeypatch.setattr(retention.os, "geteuid", lambda: other_uid)

    assert retention._prune_pytest_run_dirs(runs[3], 1) == []
    assert _names(root) == ["pytest-1", "pytest-2", "pytest-3"]


def test_unrelated_entries_are_ignored(root: Path) -> None:
    runs = _runs(root, 1, 2, 3)
    (root / "pytest-current").symlink_to(runs[3], target_is_directory=True)
    (root / "pytest-4.bak").mkdir()
    (root / "pytest-5").write_text("a file, not a run", encoding="utf-8")
    (root / "notes").mkdir()

    retention._prune_pytest_run_dirs(runs[3], 1)

    assert _names(root) == ["notes", "pytest-3", "pytest-4.bak", "pytest-5", "pytest-current"]


def test_root_that_is_not_a_pytest_of_user_directory_is_left_alone(tmp_path: Path) -> None:
    other = tmp_path / "scratch"
    other.mkdir()
    runs = _runs(other, 1, 2, 3)

    assert retention._prune_pytest_run_dirs(runs[3], 1) == []
    assert _names(other) == ["pytest-1", "pytest-2", "pytest-3"]


def test_custom_basetemp_name_is_left_alone(root: Path) -> None:
    _runs(root, 1, 2, 3)
    custom = root / "pytest-RC"
    custom.mkdir()

    assert retention._prune_pytest_run_dirs(custom, 1) == []
    assert _names(root) == ["pytest-1", "pytest-2", "pytest-3", "pytest-RC"]


def test_symlinked_root_is_refused(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    runs = _runs(real, 1, 2, 3)
    link = tmp_path / "pytest-of-link"
    link.symlink_to(real, target_is_directory=True)

    assert retention._prune_pytest_run_dirs(link / runs[3].name, 1) == []
    assert _names(real) == ["pytest-1", "pytest-2", "pytest-3"]


def test_run_locked_by_a_live_process_is_kept(root: Path) -> None:
    runs = _runs(root, 1, 2, 3)
    (runs[1] / ".lock").write_text(str(os.getpid()), encoding="utf-8")
    _age(runs[1])

    retention._prune_pytest_run_dirs(runs[3], 1)

    assert _names(root) == ["pytest-1", "pytest-3"]


def test_run_locked_by_a_dead_process_is_removed(root: Path) -> None:
    runs = _runs(root, 1, 2)
    dead = subprocess.Popen([sys.executable, "-c", "pass"])
    dead.wait(timeout=60)
    (runs[1] / ".lock").write_text(str(dead.pid), encoding="utf-8")
    _age(runs[1])

    retention._prune_pytest_run_dirs(runs[2], 1)

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

    assert retention._prune_pytest_run_dirs(runs[2], 1) == []

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

    assert retention._prune_pytest_run_dirs(runs[2], 1) == []

    assert done == ["swapped"]
    assert (runs[1] / "precious.txt").read_text(encoding="utf-8") == "data"
    assert (root / "moved-1" / "test_x0" / "payload.txt").is_file()
    assert _names(root) == ["moved-1", "pytest-1", "pytest-2"]


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

    retention._prune_pytest_run_dirs(runs[2], 1)

    assert runs[1].is_dir() and not any(runs[1].iterdir())


@pytest.mark.skipif(os.geteuid() == 0, reason="root reads files regardless of mode")
def test_unreadable_lock_naming_a_live_process_keeps_the_run(root: Path) -> None:
    runs = _runs(root, 1, 2)
    lock = runs[1] / ".lock"
    lock.write_text(str(os.getpid()), encoding="utf-8")
    lock.chmod(0)
    _age(runs[1])
    try:
        assert retention._prune_pytest_run_dirs(runs[2], 1) == []
    finally:
        lock.chmod(stat.S_IRUSR | stat.S_IWUSR)

    assert _names(root) == ["pytest-1", "pytest-2"]


@pytest.mark.parametrize("content", ["", "   \n", "garbage", "12x", "0", "-5", "9" * 100])
def test_empty_or_malformed_lock_is_unknown_and_keeps_the_run(root: Path, content: str) -> None:
    runs = _runs(root, 1, 2)
    (runs[1] / ".lock").write_text(content, encoding="utf-8")
    _age(runs[1])

    assert retention._prune_pytest_run_dirs(runs[2], 1) == []
    assert _names(root) == ["pytest-1", "pytest-2"]


def test_lock_that_is_not_a_regular_file_keeps_the_run(root: Path, tmp_path: Path) -> None:
    runs = _runs(root, 1, 2)
    target = tmp_path / "pid"
    target.write_text("1", encoding="utf-8")
    (runs[1] / ".lock").symlink_to(target)
    _age(runs[1])

    assert retention._prune_pytest_run_dirs(runs[2], 1) == []
    assert _names(root) == ["pytest-1", "pytest-2"]


def test_lock_naming_another_accounts_process_keeps_the_run(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runs = _runs(root, 1, 2)
    (runs[1] / ".lock").write_text("4242", encoding="utf-8")
    _age(runs[1])

    def foreign(pid: int, sig: int) -> None:
        raise PermissionError(1, "Operation not permitted")

    monkeypatch.setattr(retention.os, "kill", foreign)

    assert retention._prune_pytest_run_dirs(runs[2], 1) == []
    assert _names(root) == ["pytest-1", "pytest-2"]


def test_recently_touched_lockless_run_is_kept_until_the_grace_window_passes(root: Path) -> None:
    runs = _runs(root, 1, 2)
    _age(runs[1], hours=retention._PYTEST_TMP_GRACE_HOURS_DEFAULT - 1)

    assert retention._prune_pytest_run_dirs(runs[2], 1) == []
    assert _names(root) == ["pytest-1", "pytest-2"]

    _age(runs[1], hours=retention._PYTEST_TMP_GRACE_HOURS_DEFAULT + 1)
    assert [path.name for path in retention._prune_pytest_run_dirs(runs[2], 1)] == ["pytest-1"]


def test_new_entry_in_an_old_run_restarts_its_grace_window(root: Path) -> None:
    runs = _runs(root, 1, 2)
    (runs[1] / "test_late0").mkdir()
    os.utime(runs[1], (time.time() - 3 * 86400,) * 2)  # only the new entry is fresh

    assert retention._prune_pytest_run_dirs(runs[2], 1) == []
    assert _names(root) == ["pytest-1", "pytest-2"]


def test_active_lockless_session_from_a_real_factory_is_kept(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # A real TempPathFactory with retention count 0 creates its run without a .lock.
    temproot = tmp_path / "temproot"
    temproot.mkdir()
    monkeypatch.setenv("PYTEST_DEBUG_TEMPROOT", str(temproot))
    factory = TempPathFactory(None, 0, "all", trace=lambda *_args: None, _ispytest=True)
    active = factory.getbasetemp()
    (factory.mktemp("work") / "payload.txt").write_text("live", encoding="utf-8")
    assert not (active / ".lock").exists()
    active_number = int(active.name.removeprefix("pytest-"))
    newer = _runs(active.parent, active_number + 1, active_number + 2, active_number + 3)

    retention._prune_pytest_run_dirs(newer[active_number + 3], 1)

    assert (active / "work0" / "payload.txt").read_text(encoding="utf-8") == "live"


def test_grace_hours_default_override_and_invalid_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LU_PYTEST_TMP_GRACE_HOURS", raising=False)
    assert retention._pytest_tmp_grace_seconds() == 12 * 3600
    monkeypatch.setenv("LU_PYTEST_TMP_GRACE_HOURS", "0.5")
    assert retention._pytest_tmp_grace_seconds() == 1800
    monkeypatch.setenv("LU_PYTEST_TMP_GRACE_HOURS", "0")
    assert retention._pytest_tmp_grace_seconds() == 0
    for bad in ("-1", "soon", "inf", "nan"):
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


def test_session_finish_fails_on_invalid_grace_without_deleting(
    root: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    runs = _runs(root, 1, 2, 3, 4)
    monkeypatch.delenv("LU_PYTEST_TMP_KEEP_RUNS", raising=False)
    monkeypatch.setenv("LU_PYTEST_TMP_GRACE_HOURS", "-1")
    session = _session(runs[4])

    retention.pytest_sessionfinish(session, 0)

    assert session.exitstatus == pytest.ExitCode.TESTS_FAILED
    assert "invalid LU_PYTEST_TMP_GRACE_HOURS='-1'" in capsys.readouterr().out
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
