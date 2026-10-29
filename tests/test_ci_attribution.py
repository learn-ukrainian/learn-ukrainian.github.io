"""CI test timeout attribution and cancellation survival of worker breadcrumbs."""

import contextlib
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest
import yaml

from scripts.ci.stall_watch import (
    StallWatcher,
)
from tests.conftest import pytest_runtest_logfinish, pytest_runtest_logstart


@pytest.mark.parametrize("cancel_signal", [signal.SIGINT, signal.SIGKILL])
def test_cancelled_shard_keeps_running_test_evidence(tmp_path: Path, cancel_signal: int) -> None:
    root = Path(__file__).resolve().parents[1]
    job = yaml.safe_load((root / ".github/workflows/ci.yml").read_text())["jobs"]["pytest"]
    diagnostic = next(step for step in job["steps"] if step.get("name") == "Show pytest cancellation diagnostics")
    upload = next(step for step in job["steps"] if step.get("name") == "Upload pytest JUnit report")
    assert diagnostic["if"] == "${{ failure() || cancelled() }}"
    assert upload["if"] == "${{ always() }}"
    assert upload["with"]["overwrite"] is True
    assert "ci-artifacts/pytest-shard-*-breadcrumbs/" in upload["with"]["path"]
    breadcrumb_dir = job["env"]["PYTEST_BREADCRUMB_DIR"].replace("${{ matrix.shard }}", "15")
    env = {key: value for key, value in os.environ.items() if not key.startswith(("PYTEST_", "LU_"))}
    env.update(
        PYTHONPATH=str(root),
        PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
        PYTEST_BREADCRUMB_DIR=str(tmp_path / breadcrumb_dir),
    )
    (tmp_path / "pytest.ini").write_text("[pytest]\n")
    (tmp_path / "conftest.py").write_text(
        "from tests.conftest import pytest_runtest_logstart, pytest_runtest_logfinish\n"
    )
    (tmp_path / "test_cancel.py").write_text(
        "import time\ndef test_running_when_cancelled():\n    time.sleep(60)\n"
    )
    log = tmp_path / "pytest.log"
    with log.open("w") as output:
        child = subprocess.Popen(
            [sys.executable, "-m", "pytest", "-p", "xdist.plugin", "-n", "2", "-q"],
            cwd=tmp_path, env=env, stdout=output, stderr=subprocess.STDOUT, start_new_session=True,
        )
        try:
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                crumbs = list((tmp_path / breadcrumb_dir).glob("breadcrumb_gw*.txt"))
                if any("START test_cancel.py::test_running_when_cancelled\n" in p.read_text() for p in crumbs):
                    break
                assert child.poll() is None, log.read_text()
                time.sleep(0.02)
            else:
                pytest.fail(f"child did not start its test:\n{log.read_text()}")
            os.killpg(child.pid, cancel_signal)
            assert child.wait(timeout=15) != 0
        finally:
            # A hard cancellation must leave no xdist worker behind, even on an assertion failure.
            with contextlib.suppress(ProcessLookupError):
                os.killpg(child.pid, signal.SIGKILL)
            child.wait(timeout=15)

    result = subprocess.run(
        ["bash", "-e", "-o", "pipefail", "-c", diagnostic["run"]],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert "breadcrumb_gw" in result.stdout
    assert "START test_cancel.py::test_running_when_cancelled" in result.stdout
    assert "FINISH test_cancel.py::test_running_when_cancelled" not in result.stdout


def test_breadcrumb_logstart_and_logfinish(tmp_path: Path, monkeypatch) -> None:
    bdir = tmp_path / "breadcrumbs"
    monkeypatch.setenv("PYTEST_BREADCRUMB_DIR", str(bdir))
    monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw0")

    pytest_runtest_logstart("tests/test_foo.py::test_bar", ("tests/test_foo.py", 1, "test_bar"))
    breadcrumb_file = bdir / "breadcrumb_gw0.txt"
    assert breadcrumb_file.exists()
    assert breadcrumb_file.read_text(encoding="utf-8") == "START tests/test_foo.py::test_bar\n"

    pytest_runtest_logfinish("tests/test_foo.py::test_bar", ("tests/test_foo.py", 1, "test_bar"))
    lines = breadcrumb_file.read_text(encoding="utf-8").splitlines()
    assert lines == [
        "START tests/test_foo.py::test_bar",
        "FINISH tests/test_foo.py::test_bar",
    ]


# --- Controller-side stall watch (#5776 leftover) -------------------------
#
# pytest-timeout only fires inside xdist workers; a controller-side or
# pipe-full stall is otherwise invisible until the job's timeout-minutes
# cancels it (docs/bug-autopsies/2026-07-25-ci-gate-reboot.md §3). These
# tests exercise the watcher directly against fake breadcrumbs — they never
# run the full suite to prove the fail-fast behavior. Default stall budget
# must exceed pytest-timeout (120s) so healthy slow tests are not false-killed.


def test_stall_watcher_reports_and_terminates_on_a_stuck_node(tmp_path: Path) -> None:
    bdir = tmp_path / "breadcrumbs"
    bdir.mkdir()
    (bdir / "breadcrumb_gw2.txt").write_text("START tests/test_wedged.py::test_never_finishes\n", encoding="utf-8")

    current_time = 0.0
    reported: list = []
    terminated = []
    watcher = StallWatcher(
        bdir,
        stall_budget=0.05,
        report=reported.append,
        terminate=lambda: terminated.append(True),
        now=lambda: current_time,
    )

    # First poll observes the START and records the start time.
    watcher.poll_once()
    assert not terminated
    assert not reported

    # Time passes within budget; no stall yet.
    current_time += 0.03
    watcher.poll_once()
    assert not terminated
    assert not reported

    # Budget exceeded with no FINISH breadcrumb -> stall reported and terminated.
    current_time += 0.03
    watcher.poll_once()

    assert terminated, "stall watcher never called terminate() on a stuck breadcrumb"
    assert len(reported) == 1
    stalled = reported[0]
    assert len(stalled) == 1
    assert stalled[0].nodeid == "tests/test_wedged.py::test_never_finishes"
    assert stalled[0].worker_id == "gw2"
    assert stalled[0].stalled_for >= 0.05


def test_stall_watcher_stays_quiet_while_tests_finish_in_time(tmp_path: Path) -> None:
    bdir = tmp_path / "breadcrumbs"
    bdir.mkdir()
    breadcrumb_file = bdir / "breadcrumb_gw0.txt"

    current_time = 0.0
    terminated = []
    watcher = StallWatcher(
        bdir,
        stall_budget=0.2,
        terminate=lambda: terminated.append(True),
        now=lambda: current_time,
    )

    for i in range(6):
        nodeid = f"tests/test_a.py::test_{i}"
        breadcrumb_file.write_text(f"START {nodeid}\n", encoding="utf-8")
        watcher.poll_once()

        # Advance clock within budget (0.15s < 0.2s budget)
        current_time += 0.15
        watcher.poll_once()
        assert not terminated

        # Test finishes in time before the 0.2s stall budget expires
        breadcrumb_file.write_text(f"START {nodeid}\nFINISH {nodeid}\n", encoding="utf-8")
        watcher.poll_once()
        assert not terminated

        # Further time passes after test finished; watcher remains quiet
        current_time += 0.10
        watcher.poll_once()
        assert not terminated

    assert not terminated, "stall watcher fired even though FINISH breadcrumbs kept arriving"
