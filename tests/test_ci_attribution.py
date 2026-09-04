"""Unit tests for CI test timeout attribution and per-worker breadcrumb hooks."""

import os
import subprocess
import sys
import time
from pathlib import Path

from scripts.ci.stall_watch import (
    StallWatcher,
    breadcrumb_dir_from_env,
    find_stalled_nodes,
    format_stall_message,
    stall_budget_seconds,
)
from tests.conftest import _get_breadcrumb_file, pytest_runtest_logfinish, pytest_runtest_logstart


def test_get_breadcrumb_file_default(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PYTEST_BREADCRUMB_DIR", raising=False)
    monkeypatch.delenv("PYTEST_XDIST_WORKER", raising=False)

    breadcrumb_file = _get_breadcrumb_file()
    assert breadcrumb_file is not None
    assert breadcrumb_file.name == "breadcrumb_master.txt"
    assert breadcrumb_file.parent.name == ".pytest_breadcrumbs"


def test_get_breadcrumb_file_custom_dir_and_worker(tmp_path: Path, monkeypatch) -> None:
    bdir = tmp_path / "custom_breadcrumbs"
    monkeypatch.setenv("PYTEST_BREADCRUMB_DIR", str(bdir))
    monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw2")

    breadcrumb_file = _get_breadcrumb_file()
    assert breadcrumb_file is not None
    assert breadcrumb_file.name == "breadcrumb_gw2.txt"
    assert breadcrumb_file.parent == bdir


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


def test_breadcrumb_subprocess_pytest_run(tmp_path: Path) -> None:
    repo_root = Path(__file__).parents[1]
    bdir = tmp_path / "breadcrumbs"
    test_file = repo_root / "tests" / "_temp_breadcrumb_test.py"
    try:
        test_file.write_text("def test_one(): pass\ndef test_two(): pass\n", encoding="utf-8")

        env = os.environ.copy()
        env["PYTEST_BREADCRUMB_DIR"] = str(bdir)
        env["PYTEST_XDIST_WORKER"] = "gw1"

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            str(test_file),
            "-o",
            f"cache_dir={tmp_path / '.pytest_cache'}",
        ]
        res = subprocess.run(cmd, env=env, capture_output=True, text=True, check=False, cwd=str(repo_root), timeout=30)
        assert res.returncode == 0, f"stdout: {res.stdout}\nstderr: {res.stderr}"

        breadcrumb_file = bdir / "breadcrumb_gw1.txt"
        assert breadcrumb_file.exists(), (
            f"Breadcrumb file missing in {bdir}. Files present: {list(bdir.glob('*')) if bdir.exists() else 'bdir missing'}\n"
            f"stdout: {res.stdout}\nstderr: {res.stderr}"
        )
        lines = breadcrumb_file.read_text(encoding="utf-8").splitlines()
        assert "START tests/_temp_breadcrumb_test.py::test_one" in lines
        assert "FINISH tests/_temp_breadcrumb_test.py::test_one" in lines
        assert "START tests/_temp_breadcrumb_test.py::test_two" in lines
        assert "FINISH tests/_temp_breadcrumb_test.py::test_two" in lines
    finally:
        if test_file.exists():
            test_file.unlink()


# --- Controller-side stall watch (#5776 leftover) -------------------------
#
# pytest-timeout only fires inside xdist workers; a controller-side or
# pipe-full stall is otherwise invisible until the job's timeout-minutes
# cancels it (docs/bug-autopsies/2026-07-25-ci-gate-reboot.md §3). These
# tests exercise the watcher directly against fake breadcrumbs — they never
# run the full suite to prove the fail-fast behavior. Default stall budget
# must exceed pytest-timeout (120s) so healthy slow tests are not false-killed.


def test_stall_budget_default_exceeds_pytest_timeout(monkeypatch) -> None:
    """Default budget stays above worker timeout so healthy slow tests survive."""
    monkeypatch.delenv("CI_STALL_WATCH_SECONDS", raising=False)
    assert stall_budget_seconds() > 120


def test_find_stalled_nodes_flags_start_without_finish(tmp_path: Path) -> None:
    bdir = tmp_path / "breadcrumbs"
    bdir.mkdir()
    (bdir / "breadcrumb_gw0.txt").write_text("START tests/test_slow.py::test_hangs\n", encoding="utf-8")

    state: dict = {}
    # First poll only records when the START was first observed.
    assert find_stalled_nodes(bdir, stall_budget=0.05, state=state) == []
    time.sleep(0.1)
    stalled = find_stalled_nodes(bdir, stall_budget=0.05, state=state)

    assert len(stalled) == 1
    assert stalled[0].worker_id == "gw0"
    assert stalled[0].nodeid == "tests/test_slow.py::test_hangs"
    assert stalled[0].stalled_for >= 0.05


def test_find_stalled_nodes_ignores_finished_tests(tmp_path: Path) -> None:
    bdir = tmp_path / "breadcrumbs"
    bdir.mkdir()
    (bdir / "breadcrumb_gw0.txt").write_text(
        "START tests/test_fast.py::test_ok\nFINISH tests/test_fast.py::test_ok\n",
        encoding="utf-8",
    )

    state: dict = {}
    find_stalled_nodes(bdir, stall_budget=0.05, state=state)
    time.sleep(0.1)

    assert find_stalled_nodes(bdir, stall_budget=0.05, state=state) == []


def test_find_stalled_nodes_resets_when_a_new_test_starts(tmp_path: Path) -> None:
    bdir = tmp_path / "breadcrumbs"
    bdir.mkdir()
    breadcrumb_file = bdir / "breadcrumb_gw0.txt"
    breadcrumb_file.write_text("START tests/test_a.py::test_one\n", encoding="utf-8")

    state: dict = {}
    find_stalled_nodes(bdir, stall_budget=0.05, state=state)
    time.sleep(0.1)
    # Progress arrives (FINISH + a new START) before the budget check fires.
    breadcrumb_file.write_text(
        "START tests/test_a.py::test_one\nFINISH tests/test_a.py::test_one\nSTART tests/test_a.py::test_two\n",
        encoding="utf-8",
    )

    assert find_stalled_nodes(bdir, stall_budget=0.05, state=state) == []


def test_format_stall_message_names_nodeid_and_worker() -> None:
    from scripts.ci.stall_watch import StalledNode

    node = StalledNode(worker_id="gw3", nodeid="tests/test_x.py::test_y", stalled_for=91.2)
    message = format_stall_message(node, stall_budget=90.0)

    assert "gw3" in message
    assert "tests/test_x.py::test_y" in message
    assert "91.2" in message


def test_breadcrumb_dir_from_env_default_and_disabled(monkeypatch) -> None:
    monkeypatch.delenv("PYTEST_BREADCRUMB_DIR", raising=False)
    assert breadcrumb_dir_from_env() == Path(".pytest_breadcrumbs")

    monkeypatch.setenv("PYTEST_BREADCRUMB_DIR", "")
    assert breadcrumb_dir_from_env() is None


def test_stall_watcher_reports_and_terminates_on_a_stuck_node(tmp_path: Path) -> None:
    bdir = tmp_path / "breadcrumbs"
    bdir.mkdir()
    (bdir / "breadcrumb_gw2.txt").write_text("START tests/test_wedged.py::test_never_finishes\n", encoding="utf-8")

    reported: list = []
    terminated = []
    watcher = StallWatcher(
        bdir,
        stall_budget=0.05,
        poll_interval=0.02,
        report=reported.append,
        terminate=lambda: terminated.append(True),
    )

    watcher.start()
    try:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and not terminated:
            time.sleep(0.02)
    finally:
        watcher.stop()

    assert terminated, "stall watcher never called terminate() on a stuck breadcrumb"
    assert len(reported) == 1
    stalled = reported[0]
    assert len(stalled) == 1
    assert stalled[0].nodeid == "tests/test_wedged.py::test_never_finishes"
    assert stalled[0].worker_id == "gw2"


def test_stall_watcher_stays_quiet_while_tests_finish_in_time(tmp_path: Path) -> None:
    bdir = tmp_path / "breadcrumbs"
    bdir.mkdir()
    breadcrumb_file = bdir / "breadcrumb_gw0.txt"
    breadcrumb_file.write_text("START tests/test_a.py::test_one\n", encoding="utf-8")

    terminated = []
    watcher = StallWatcher(
        bdir,
        stall_budget=0.2,
        poll_interval=0.02,
        terminate=lambda: terminated.append(True),
    )
    watcher.start()
    try:
        for _ in range(6):
            time.sleep(0.05)
            breadcrumb_file.write_text(
                "START tests/test_a.py::test_one\nFINISH tests/test_a.py::test_one\n",
                encoding="utf-8",
            )
    finally:
        watcher.stop()

    assert not terminated, "stall watcher fired even though FINISH breadcrumbs kept arriving"


def test_stall_watcher_is_a_noop_when_breadcrumbs_are_disabled() -> None:
    terminated = []
    watcher = StallWatcher(None, terminate=lambda: terminated.append(True))
    watcher.start()
    watcher.stop()

    assert watcher._thread is None
    assert not terminated


def test_run_nodeids_kills_a_wedged_test_and_names_it_on_stderr() -> None:
    """Cursor Cloud still runs pytest_shards.py; stall-watch must name the wedge."""
    repo_root = Path(__file__).parents[1]
    test_file = repo_root / "tests" / "_temp_stall_hang_test.py"
    with_tmp = repo_root / ".tmp_stall_watch_test"
    with_tmp.mkdir(exist_ok=True)
    bdir = with_tmp / "breadcrumbs"
    nodeids_file = with_tmp / "nodeids.txt"
    try:
        test_file.write_text("import time\n\n\ndef test_wedges():\n    time.sleep(60)\n", encoding="utf-8")
        nodeids_file.write_text("tests/_temp_stall_hang_test.py::test_wedges\n", encoding="utf-8")

        env = os.environ.copy()
        env["PYTEST_BREADCRUMB_DIR"] = str(bdir)
        env["CI_STALL_WATCH_SECONDS"] = "0.3"
        env["CI_STALL_WATCH_POLL_SECONDS"] = "0.05"

        cmd = [
            sys.executable,
            str(repo_root / "scripts" / "ci" / "pytest_shards.py"),
            "run",
            "--nodeids",
            str(nodeids_file),
            "--",
            "-p",
            "no:cacheprovider",
        ]
        start = time.monotonic()
        res = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            cwd=str(repo_root),
            timeout=30,
            start_new_session=True,  # isolate the killpg() below from this test's own process group
        )
        elapsed = time.monotonic() - start

        assert res.returncode != 0, f"stdout: {res.stdout}\nstderr: {res.stderr}"
        assert elapsed < 15, f"stall watch did not fail fast ({elapsed:.1f}s)\nstderr: {res.stderr}"
        assert "tests/_temp_stall_hang_test.py::test_wedges" in res.stderr, res.stderr
    finally:
        if test_file.exists():
            test_file.unlink()
        for path in sorted(with_tmp.rglob("*"), reverse=True):
            path.unlink() if path.is_file() else path.rmdir()
        if with_tmp.exists():
            with_tmp.rmdir()
