"""Shared pytest JUnit parsing for #9067 and #9063."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.ci.junit_results import SUMMARY_ROW_CAP, parse_junit, render_failure_summary
from scripts.ci.junit_results import main as junit_main
from scripts.common.flake_quarantine import TIMEOUT_PATTERN


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


def _write_summary_junit(path: Path) -> Path:
    path.write_text(
        '<testsuites><testsuite name="pytest">'
        '<testcase classname="tests.test_a" name="test_ok" file="tests/test_a.py"/>'
        '<testcase classname="tests.test_a" name="test_skip" file="tests/test_a.py"><skipped message="why"/></testcase>'
        '<testcase classname="tests.test_a.TestX" name="test_bad[a|b]" file="tests/test_a.py">'
        '<failure message="assert 1 == 2&#10;  +  where 1 = f()">long traceback</failure></testcase>'
        '<testcase classname="tests.test_a" name="test_err" file="tests/test_a.py">'
        '<error message="&lt;boom&gt; `x`">trace</error></testcase>'
        '</testsuite></testsuites>',
        encoding="utf-8",
    )
    return path


def test_summary_lists_failures_and_errors_only(tmp_path: Path):
    text = render_failure_summary([_write_summary_junit(tmp_path / "j.xml")], title="pytest (3)")
    assert "2 failing of 4 tests" in text
    assert "tests/test_a.py::TestX::test_bad[a\\|b] | failed | assert 1 == 2 |" in text
    assert "tests/test_a.py::test_err | error | &lt;boom&gt; \\`x\\` |" in text
    assert "test_ok" not in text and "test_skip" not in text
    assert "traceback" not in text


def test_summary_green_is_one_line(tmp_path: Path):
    path = tmp_path / "green.xml"
    path.write_text(
        '<testsuite><testcase classname="tests.test_a" name="test_ok" file="tests/test_a.py"/>'
        '<testcase classname="tests.test_a" name="test_skip" file="tests/test_a.py"><skipped/></testcase></testsuite>',
        encoding="utf-8",
    )
    assert render_failure_summary([path]) == "pytest: 2 tests, no failures.\n"


def test_summary_caps_rows_and_reports_remainder(tmp_path: Path):
    cases = "".join(
        f'<testcase classname="tests.test_a" name="test_{i}" file="tests/test_a.py"><failure message="m{i}"/></testcase>'
        for i in range(SUMMARY_ROW_CAP + 7)
    )
    path = tmp_path / "many.xml"
    path.write_text(f"<testsuite>{cases}</testsuite>", encoding="utf-8")
    text = render_failure_summary([path])
    assert text.count("| failed |") == SUMMARY_ROW_CAP
    assert text.rstrip().endswith("and 7 more")


def test_summary_tolerates_missing_empty_and_corrupt_files(tmp_path: Path):
    empty = tmp_path / "empty.xml"
    empty.write_text("", encoding="utf-8")
    corrupt = tmp_path / "corrupt.xml"
    corrupt.write_text("<testsuite><testcase", encoding="utf-8")
    assert render_failure_summary([tmp_path / "absent.xml", empty]) == "pytest: no JUnit results to summarise.\n"
    assert render_failure_summary([]) == "pytest: no JUnit results to summarise.\n"
    unreadable = render_failure_summary([corrupt])
    assert unreadable.startswith("pytest: JUnit results unreadable") and unreadable.count("\n") == 1


def test_summary_cli_never_fails_on_missing_input(tmp_path: Path, capsys):
    assert junit_main([str(tmp_path / "nope.xml"), "--title", "pytest (1)"]) == 0
    assert capsys.readouterr().out == "pytest (1): no JUnit results to summarise.\n"
