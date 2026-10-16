"""No process of a test's child command outlives it (#10777, tests/process_group_child.py).

Each case starts a child that starts a long-lived grandchild and records both
pids, then ends the call a different way: timeout, an exception in the
caller, a normal exit, and the death of the calling process itself (what
pytest-timeout's thread method does to an xdist worker).
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import textwrap
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

from tests import process_group_child
from tests.process_group_child import run_in_process_group

_REPO_ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(not sys.platform.startswith("linux"), reason="process groups and /proc are Linux")

# argv: pid file, then "exit" to return at once or "stay" to sleep.
_CHILD = textwrap.dedent(
    """
    import os
    import subprocess
    import sys
    import time

    grandchild = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(300)"])
    with open(sys.argv[1] + ".tmp", "w") as handle:
        handle.write(f"{os.getpid()} {grandchild.pid}")
    os.replace(sys.argv[1] + ".tmp", sys.argv[1])
    print("child-out", flush=True)
    print("child-err", file=sys.stderr, flush=True)
    if sys.argv[2] == "stay":
        time.sleep(300)
    """
)


def _alive(pid: int) -> bool:
    try:
        stat = Path(f"/proc/{pid}/stat").read_text()
    except (FileNotFoundError, ProcessLookupError):
        return False
    # A killed process waits as a zombie (state Z) until its new parent reaps it.
    return stat.rpartition(")")[2].split()[0] != "Z"


def _wait_for_pids(pid_file: Path, timeout: float = 60) -> list[int]:
    deadline = time.monotonic() + timeout
    while not pid_file.is_file():
        assert time.monotonic() < deadline, "the child never recorded its pids"
        time.sleep(0.05)
    return [int(pid) for pid in pid_file.read_text().split()]


def _assert_all_gone(pids: list[int], timeout: float = 20) -> None:
    deadline = time.monotonic() + timeout
    while any(_alive(pid) for pid in pids) and time.monotonic() < deadline:
        time.sleep(0.05)
    survivors = [pid for pid in pids if _alive(pid)]
    assert not survivors, f"processes outlived the call: {survivors}"


@pytest.fixture
def pid_file(tmp_path: Path) -> Iterator[Path]:
    """Where the child records its pids; a failing case still leaves no process behind."""
    path = tmp_path / "pids"
    yield path
    if path.is_file():
        for pid in (int(pid) for pid in path.read_text().split()):
            if _alive(pid):
                os.kill(pid, signal.SIGKILL)


def test_returns_output_and_status_like_subprocess_run(tmp_path: Path) -> None:
    result = run_in_process_group(
        [sys.executable, "-c", "import sys; print('out'); print('err', file=sys.stderr); sys.exit(3)"],
        timeout=60,
        cwd=tmp_path,
    )

    assert (result.returncode, result.stdout, result.stderr) == (3, "out\n", "err\n")


def test_reports_a_child_killed_by_a_signal_as_subprocess_run_does() -> None:
    result = run_in_process_group([sys.executable, "-c", "import os; os.kill(os.getpid(), 15)"], timeout=60)

    assert result.returncode == -15


def test_timeout_kills_the_child_and_its_grandchild(pid_file: Path) -> None:

    with pytest.raises(subprocess.TimeoutExpired) as raised:
        run_in_process_group([sys.executable, "-c", _CHILD, str(pid_file), "stay"], timeout=5)

    assert "child-out" in raised.value.output
    _assert_all_gone(_wait_for_pids(pid_file))


def test_an_error_in_the_caller_kills_the_child_and_its_grandchild(
    pid_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sleep = time.sleep

    def interrupted(seconds: float) -> None:
        if pid_file.is_file():
            raise RuntimeError("caller failed")
        sleep(seconds)

    monkeypatch.setattr(process_group_child.time, "sleep", interrupted)

    with pytest.raises(RuntimeError, match="caller failed"):
        run_in_process_group([sys.executable, "-c", _CHILD, str(pid_file), "stay"], timeout=60)

    monkeypatch.undo()
    _assert_all_gone(_wait_for_pids(pid_file))


def test_a_normal_exit_leaves_no_grandchild_behind(pid_file: Path) -> None:

    result = run_in_process_group([sys.executable, "-c", _CHILD, str(pid_file), "exit"], timeout=60)

    assert result.returncode == 0
    _assert_all_gone(_wait_for_pids(pid_file))


def test_the_death_of_the_calling_process_kills_the_child_and_its_grandchild(pid_file: Path) -> None:
    """pytest-timeout's thread method ends a worker with ``os._exit``; no ``finally`` runs."""
    caller = textwrap.dedent(
        """
        import os
        import sys
        import threading
        import time
        from pathlib import Path

        from tests.process_group_child import run_in_process_group


        def die():
            while not Path(sys.argv[1]).is_file():
                time.sleep(0.05)
            os._exit(1)


        threading.Thread(target=die, daemon=True).start()
        run_in_process_group([sys.executable, "-c", sys.argv[2], sys.argv[1], "stay"], timeout=300)
        """
    )

    died = subprocess.run(
        [sys.executable, "-c", caller, str(pid_file), _CHILD],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=90,
    )

    assert died.returncode == 1, died.stderr
    _assert_all_gone(_wait_for_pids(pid_file))
