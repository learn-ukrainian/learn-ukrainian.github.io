"""Shared pytest JUnit parsing for #9067 and #9063."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.ci.flake_quarantine import TIMEOUT_PATTERN
from scripts.ci.junit_results import parse_junit


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
def test_rerun_reporter_survives_real_pytest_xunit2(tmp_path: Path, workers: int):
    (tmp_path / "conftest.py").write_text(
        "from tests.conftest import _FlakeRerunReporter\n"
        "def pytest_configure(config):\n"
        "    config.pluginmanager.register(_FlakeRerunReporter(config), 'flake-reporter')\n",
        encoding="utf-8",
    )
    (tmp_path / "test_sample.py").write_text(
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
    env = os.environ | {"GITHUB_STEP_SUMMARY": str(summary)}
    command = [sys.executable, "-m", "pytest", str(tmp_path / "test_sample.py"), "-o", "addopts=", f"--junitxml={xml}"]
    if workers:
        command.extend(["-n", str(workers)])
    result = subprocess.run(
        command,
        cwd=Path(__file__).resolve().parents[1], env=env, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    parsed = parse_junit([xml])
    assert len(parsed) == 1 and parsed[0].reruns == 1 and parsed[0].outcome == "passed"
    assert "test_sample.py::test_flaky" in summary.read_text(encoding="utf-8")


def test_thread_timeout_exits_without_rerun(tmp_path: Path):
    (tmp_path / "test_timeout.py").write_text(
        "import time\nimport pytest\n"
        f"@pytest.mark.flaky(reruns=1, rerun_except=[{TIMEOUT_PATTERN!r}])\n"
        "@pytest.mark.timeout(0.1, method='thread')\n"
        "def test_timeout():\n"
        "    time.sleep(2)\n",
        encoding="utf-8",
    )
    xml = tmp_path / "timeout.xml"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(tmp_path / "test_timeout.py"), "-o", "addopts=", f"--junitxml={xml}"],
        cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=10,
    )
    assert result.returncode != 0
    assert "Timeout" in result.stdout
    assert "RERUN" not in result.stdout
    assert not xml.exists()  # pytest-timeout's thread method exits before JUnit serialization.
