"""Behavioral tests for pytest temp retention and the session size guard."""

import re
from pathlib import Path

import pytest

pytest_plugins = ("pytester",)

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _configure_nested_pytest(pytester: pytest.Pytester) -> Path:
    """Load the real session hook into an isolated pytester project."""
    basetemp = pytester.path / "nested-basetemp"
    conftest = f"""
import importlib.util
spec = importlib.util.spec_from_file_location("project_tests_conftest", {str(_REPO_ROOT / "tests" / "conftest.py")!r})
project_tests_conftest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(project_tests_conftest)
pytest_sessionfinish = project_tests_conftest.pytest_sessionfinish
"""
    pytester.makeconftest(conftest)
    pytester.makeini(
        """
[pytest]
tmp_path_retention_policy = failed
tmp_path_retention_count = 1
"""
    )
    return basetemp


def test_tmp_guard_reports_only_when_budget_is_unset(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("LU_PYTEST_TMP_BUDGET_GB", raising=False)
    basetemp = _configure_nested_pytest(pytester)
    pytester.makepyfile("def test_writes_tmp(tmp_path):\n    (tmp_path / 'payload').write_bytes(b'x' * 1024)\n")

    result = pytester.runpytest_subprocess("-q", "-s", "--basetemp", str(basetemp))

    assert result.ret == 0
    assert f"pytest-tmp: 0.00 GB in {basetemp}" in result.stdout.str()


def test_tmp_guard_does_not_create_an_unused_basetemp(pytester: pytest.Pytester) -> None:
    basetemp = _configure_nested_pytest(pytester)
    pytester.makepyfile("def test_does_not_use_tmp_path():\n    pass\n")

    result = pytester.runpytest_subprocess("-q", "-s")

    assert result.ret == 0
    assert "pytest-tmp:" not in result.stdout.str()
    assert not basetemp.exists()


@pytest.mark.parametrize("budget", ["", "   "])
def test_tmp_guard_treats_empty_budget_as_unset(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch, budget: str
) -> None:
    monkeypatch.setenv("LU_PYTEST_TMP_BUDGET_GB", budget)
    basetemp = _configure_nested_pytest(pytester)
    pytester.makepyfile("def test_writes_tmp(tmp_path):\n    (tmp_path / 'payload').write_bytes(b'x')\n")

    result = pytester.runpytest_subprocess("-q", "-s", "--basetemp", str(basetemp))

    output = result.stdout.str()
    assert result.ret == 0
    assert f"pytest-tmp: 0.00 GB in {basetemp}" in output
    assert "invalid LU_PYTEST_TMP_BUDGET_GB" not in output


def test_tmp_guard_fails_when_budget_is_exceeded(pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LU_PYTEST_TMP_BUDGET_GB", "0.0001")
    basetemp = _configure_nested_pytest(pytester)
    pytester.makepyfile(
        "def test_writes_tmp(tmp_path):\n    (tmp_path / 'payload').write_bytes(b'x' * 1024 * 1024)\n    assert False\n"
    )

    result = pytester.runpytest_subprocess("-q", "-s", "--basetemp", str(basetemp))

    output = result.stdout.str()
    assert result.ret != 0
    size_lines = re.findall(r"pytest-tmp:[^\n]*", output)
    assert len(size_lines) == 2
    assert size_lines[0].startswith("pytest-tmp: at least ")
    assert "bytes (walk stopped at budget)" in size_lines[0]
    assert size_lines[1] == ("pytest-tmp: session temp size exceeded LU_PYTEST_TMP_BUDGET_GB=0.0001 (0.00 GB)")
    retained_dir = basetemp / "test_writes_tmp0"
    assert (retained_dir / "payload").stat().st_size == 1024 * 1024


def test_failing_session_under_budget_does_not_fail_guard(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LU_PYTEST_TMP_BUDGET_GB", "1")
    basetemp = _configure_nested_pytest(pytester)
    pytester.makepyfile(
        "def test_fails_with_small_tmp(tmp_path):\n    (tmp_path / 'payload').write_text('kept')\n    assert False\n"
    )

    result = pytester.runpytest_subprocess("-q", "-s", "--basetemp", str(basetemp))

    output = result.stdout.str()
    assert result.ret != 0
    assert f"pytest-tmp: 0.00 GB in {basetemp}" in output
    assert "session temp size exceeded" not in output


@pytest.mark.parametrize("budget", ["not-a-number", "-1"])
def test_tmp_guard_rejects_invalid_budget(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch, budget: str
) -> None:
    monkeypatch.setenv("LU_PYTEST_TMP_BUDGET_GB", budget)
    basetemp = _configure_nested_pytest(pytester)
    pytester.makepyfile("def test_passes(tmp_path):\n    (tmp_path / 'payload').write_text('x')\n")

    result = pytester.runpytest_subprocess("-q", "-s", "--basetemp", str(basetemp))

    output = result.stdout.str()
    assert result.ret != 0
    assert f"pytest-tmp: invalid LU_PYTEST_TMP_BUDGET_GB={budget!r}" in output
    assert "pytest-tmp: 0.00 GB" not in output


def test_tmp_guard_reports_once_with_xdist(pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LU_PYTEST_TMP_BUDGET_GB", raising=False)
    basetemp = _configure_nested_pytest(pytester)
    pytester.makepyfile("def test_passes(tmp_path):\n    (tmp_path / 'payload').write_text('x')\n")

    result = pytester.runpytest_subprocess("-q", "-s", "-n", "2", "--basetemp", str(basetemp))

    size_lines = re.findall(r"pytest-tmp:[^\n]*", result.stdout.str())
    assert result.ret == 0
    assert len(size_lines) == 1
    assert size_lines[0] == f"pytest-tmp: 0.00 GB in {basetemp}"


def test_passing_session_removes_per_test_tmp_dirs_under_failed_policy(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("LU_PYTEST_TMP_BUDGET_GB", raising=False)
    basetemp = _configure_nested_pytest(pytester)
    pytester.makepyfile("def test_success(tmp_path):\n    (tmp_path / 'payload').write_text('ok')\n")

    result = pytester.runpytest_subprocess("-q", "--basetemp", str(basetemp))

    assert result.ret == 0
    assert list(basetemp.iterdir()) == []


def test_failing_test_keeps_its_tmp_dir_under_failed_policy(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("LU_PYTEST_TMP_BUDGET_GB", raising=False)
    basetemp = _configure_nested_pytest(pytester)
    pytester.makepyfile(
        "def test_failure_keeps_tmp(tmp_path):\n    (tmp_path / 'payload').write_text('kept')\n    assert False\n"
    )

    result = pytester.runpytest_subprocess("-q", "--basetemp", str(basetemp))

    assert result.ret != 0
    retained_dir = basetemp / "test_failure_keeps_tmp0"
    assert retained_dir.is_dir()
    assert (retained_dir / "payload").read_text() == "kept"
