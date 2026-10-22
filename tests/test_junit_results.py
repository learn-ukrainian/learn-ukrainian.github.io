"""Shared pytest JUnit parsing for #9067 and #9063."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.ci.junit_results import parse_junit, render_failure_summary


def _child_test_path(directory: Path, parameter_id: str) -> Path:
    return directory / parameter_id / f"test_sample_{parameter_id}.py"


def test_parser_reads_recovered_rerun_failure_and_class_node_id(tmp_path: Path):
    path = tmp_path / "junit.xml"
    path.write_text(
        '<testsuites><testsuite name="pytest">'
        '<testcase classname="tests.test_sample.TestThing" name="test_flaky[x]" file="tests/test_sample.py">'
        '<properties><property name="flake.reruns" value="1"/></properties></testcase>'
        '<testcase classname="tests.test_sample" name="test_bad" file="tests/test_sample.py">'
        '<failure message="assert 0">traceback</failure></testcase>'
        '</testsuite></testsuites>',
        encoding="utf-8",
    )
    recovered, failed = parse_junit([path])
    assert (recovered.node_id, recovered.outcome, recovered.reruns) == (
        "tests/test_sample.py::TestThing::test_flaky[x]", "passed", 1
    )
    assert (failed.node_id, failed.outcome, failed.message) == (
        "tests/test_sample.py::test_bad", "failed", "assert 0"
    )


def test_parser_rejects_unidentifiable_or_invalid_rerun(tmp_path: Path):
    path = tmp_path / "bad.xml"
    path.write_text('<testsuite><testcase/></testsuite>', encoding="utf-8")
    with pytest.raises(ValueError, match="pytest name"):
        parse_junit([path])
    path.write_text(
        '<testsuite><testcase classname="tests.test_x" name="test_x" file="tests/test_x.py">'
        '<properties><property name="flake.reruns" value="many"/></properties></testcase></testsuite>',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match=r"invalid flake\.reruns"):
        parse_junit([path])


@pytest.mark.parametrize("workers", [0, 2])
def test_rerun_reporter_survives_real_pytest_xunit2(tmp_path: Path, workers: int, request):
    sample = _child_test_path(tmp_path, request.node.callspec.id)
    tmp_path = sample.parent
    tmp_path.mkdir()
    (tmp_path / "conftest.py").write_text(
        "from tests.conftest import _FlakeRerunReporter\n"
        "def pytest_configure(config):\n"
        "    config.pluginmanager.register(_FlakeRerunReporter(config), 'flake-reporter')\n",
        encoding="utf-8",
    )
    sample.write_text(
        "import pytest\n"
        "attempts = 0\n"
        "@pytest.mark.flaky(reruns=1)\n"
        "def test_flaky():\n"
        "    global attempts\n"
        "    attempts += 1\n"
        "    assert attempts == 2\n",
        encoding="utf-8",
    )
    xml = tmp_path / "junit.xml"
    summary = tmp_path / "summary.md"
    env = os.environ | {"GITHUB_STEP_SUMMARY": str(summary), "PYTHONDONTWRITEBYTECODE": "1"}
    command = [sys.executable, "-m", "pytest", str(sample), "-o", "addopts=", f"--junitxml={xml}"]
    if workers:
        command.extend(["-n", str(workers)])
    result = subprocess.run(
        command,
        cwd=Path(__file__).resolve().parents[1], env=env, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    parsed = parse_junit([xml])
    assert len(parsed) == 1 and parsed[0].reruns == 1 and parsed[0].outcome == "passed"
    assert f"{sample.name}::test_flaky" in summary.read_text(encoding="utf-8")


@pytest.mark.parametrize("event,disabled,recover,attempts,exit_code", [
    ("pull_request", "0", True, 2, 0),
    ("merge_group", "0", False, 2, 1),
    ("schedule", "0", True, 1, 1),
    ("workflow_dispatch", "1", True, 1, 1),
], ids=["pull_request", "merge_group", "schedule", "workflow_dispatch"])
def test_registry_hook_executes_assertions_with_one_rerun_or_scheduled_failure(
    tmp_path: Path, event: str, disabled: str, recover: bool, attempts: int, exit_code: int, request,
):
    """Exercise the real collection hook, rerun plugin and reporter together."""
    sample = _child_test_path(tmp_path, request.node.callspec.id)
    tmp_path = sample.parent
    tmp_path.mkdir()
    sample = tmp_path / "tests" / sample.name
    (tmp_path / "pytest.ini").write_text("[pytest]\n")
    (tmp_path / "conftest.py").write_text(
        "from datetime import date\n"
        "from tests import conftest as hooks\n"
        f"hooks.load_registry = lambda: [{{'node_id': 'tests/{sample.name}::test_flaky', "
        "'admitted_on': date.today(), 'expires_on': date.today()}]\n"
        "pytest_collection_modifyitems = hooks.pytest_collection_modifyitems\n"
        "def pytest_configure(config):\n"
        "    config.pluginmanager.register(hooks._FlakeRerunReporter(config), 'flake-reporter')\n",
    )
    sample.parent.mkdir()
    sample.write_text(
        "from pathlib import Path\n"
        "def test_flaky():\n"
        "    path = Path(__file__).with_name('attempts.txt')\n"
        "    count = int(path.read_text()) + 1 if path.exists() else 1\n"
        "    path.write_text(str(count))\n"
        f"    assert count == 2 and {recover!r}\n",
    )
    xml, summary = tmp_path / "junit.xml", tmp_path / "summary.md"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(sample), "-c", str(tmp_path / "pytest.ini"),
         "-o", "addopts=", "-q", f"--junitxml={xml}"],
        cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=30,
        env=os.environ | {"GITHUB_EVENT_NAME": event, "LU_FLAKE_DISABLE_RERUN": disabled,
                          "GITHUB_STEP_SUMMARY": str(summary), "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert result.returncode == exit_code, result.stdout + result.stderr
    assert sample.with_name("attempts.txt").read_text() == str(attempts)
    parsed = parse_junit([xml])
    assert len(parsed) == 1
    assert parsed[0].node_id == f"tests/{sample.name}::test_flaky"
    assert parsed[0].outcome == ("passed" if exit_code == 0 else "failed")
    if exit_code == 0:
        assert parsed[0].reruns == 1
        assert "first attempt failed, rerun passed" in result.stdout
        assert "first attempt failed, rerun passed" in summary.read_text()
    else:
        assert parsed[0].reruns == 0
        assert not summary.exists()


def test_summary_tolerates_missing_empty_and_corrupt_files(tmp_path: Path):
    empty = tmp_path / "empty.xml"
    empty.write_text("", encoding="utf-8")
    corrupt = tmp_path / "corrupt.xml"
    corrupt.write_text("<testsuite><testcase", encoding="utf-8")
    assert render_failure_summary([tmp_path / "absent.xml", empty]) == "pytest: no JUnit results to summarise.\n"
    assert render_failure_summary([]) == "pytest: no JUnit results to summarise.\n"
    unreadable = render_failure_summary([corrupt])
    assert unreadable.startswith("pytest: JUnit results unreadable") and unreadable.count("\n") == 1
