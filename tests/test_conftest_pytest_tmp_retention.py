"""Pytest temp-run retention (#10779): keep the newest N ``pytest-<N>`` run directories.

Every test builds a fake ``pytest-of-<user>`` root in ``tmp_path``; the real pytest
temp root is never touched.
"""

from __future__ import annotations

import getpass
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import tests.conftest as retention

pytest_plugins = ("pytester",)


@pytest.fixture
def root(tmp_path: Path) -> Path:
    path = tmp_path / "pytest-of-tester"
    path.mkdir()
    return path


def _runs(root: Path, *numbers: int) -> dict[int, Path]:
    made = {}
    for number in numbers:
        run = root / f"pytest-{number}"
        (run / "test_x0").mkdir(parents=True)
        (run / "test_x0" / "payload.txt").write_text("x", encoding="utf-8")
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

    retention._prune_pytest_run_dirs(runs[3], 1)

    assert _names(root) == ["pytest-1", "pytest-3"]


def test_run_locked_by_a_dead_process_is_removed(root: Path) -> None:
    runs = _runs(root, 1, 2)
    dead = subprocess.Popen([sys.executable, "-c", "pass"])
    dead.wait(timeout=60)
    (runs[1] / ".lock").write_text(str(dead.pid), encoding="utf-8")

    retention._prune_pytest_run_dirs(runs[2], 1)

    assert _names(root) == ["pytest-2"]


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
