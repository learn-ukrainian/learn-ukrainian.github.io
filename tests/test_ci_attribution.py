"""Unit tests for CI test timeout attribution and per-worker breadcrumb hooks."""

from pathlib import Path

from scripts.ci.stall_watch import (
    StallWatcher,
)
from tests.conftest import pytest_runtest_logfinish, pytest_runtest_logstart


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
