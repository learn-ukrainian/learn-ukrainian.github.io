"""Behavioral tests for pytest temp retention and the session size guard."""

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


def test_tmp_guard_fails_when_budget_is_exceeded(pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LU_PYTEST_TMP_BUDGET_GB", "0.000000001")
    basetemp = _configure_nested_pytest(pytester)
    pytester.makepyfile("def test_writes_tmp(tmp_path):\n    (tmp_path / 'payload').write_bytes(b'x' * 1024)\n")

    result = pytester.runpytest_subprocess("-q", "-s", "--basetemp", str(basetemp))

    output = result.stdout.str()
    assert result.ret != 0
    assert "pytest-tmp: at least " in output
    assert f"bytes (walk stopped at budget) in {basetemp}" in output
    assert "pytest-tmp: session temp size exceeded LU_PYTEST_TMP_BUDGET_GB=0.000000001" in output


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
