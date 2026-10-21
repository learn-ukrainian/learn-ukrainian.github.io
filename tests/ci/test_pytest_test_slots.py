"""Dispatch-worker pytest runs draw from the host test-slot pool (#10662).

Each case runs real pytest in a subprocess against a fixture project that loads the dispatch plugin, with a
private pool whose slots this process holds or leaves free.
"""

from __future__ import annotations

import contextlib
import json
import os
import signal
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.ci import pytest_dispatch_cap
from scripts.ci.pytest_dispatch_cap import DISPATCH_TASK_ENV
from scripts.common import test_slots
from tests.wait_helpers import wait_for_line

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SAMPLE = """\
import json
import os


def _record():
    with open(os.environ["SLOT_PROBE_OUT"], "a", encoding="utf-8") as stream:
        stream.write(json.dumps({
            "holder": os.environ.get("LU_TEST_SLOTS_HOLDER"),
            "worker": os.environ.get("PYTEST_XDIST_WORKER"),
            "workers": os.environ.get("PYTEST_XDIST_WORKER_COUNT"),
            "auto": os.environ.get("PYTEST_XDIST_AUTO_NUM_WORKERS"),
        }) + "\\n")


def test_first():
    _record()


def test_second():
    _record()


def test_third():
    _record()
"""


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    scripts = (_REPO_ROOT / "scripts").as_posix()
    root = tmp_path / "project"
    (root / "tests").mkdir(parents=True)
    (root / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\n"
        "testpaths = ['tests']\n"
        f"pythonpath = ['{scripts}']\n"
        "addopts = '-p ci.pytest_dispatch_cap'\n",
        encoding="utf-8",
    )
    (root / "tests" / "test_sample.py").write_text(_SAMPLE, encoding="utf-8")
    monkeypatch.setenv(test_slots.ENABLE_ENV, "on")
    monkeypatch.setenv(test_slots.DIR_ENV, str(tmp_path / "pool"))
    monkeypatch.setenv(test_slots.COUNT_ENV, "1")
    monkeypatch.delenv(test_slots.HOLDER_ENV, raising=False)
    return root


def _env(project: Path, **extra: str | None) -> dict[str, str]:
    """This run's environment, minus anything that would make the child look nested or like an xdist worker."""
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in {test_slots.HOLDER_ENV, "PYTEST_ADDOPTS"} and not key.startswith("PYTEST_XDIST_")
    }
    env.update(
        {
            DISPATCH_TASK_ENV: "impl-slots",
            "SLOT_PROBE_OUT": str(project / "probe.jsonl"),
            "LU_PYTEST_FULL_SUITE_LOCK": str(project / "full-suite.lock"),
            "PYTHONPATH": os.pathsep.join((str(_REPO_ROOT), str(_REPO_ROOT / "scripts"))),
            test_slots.WAIT_ENV: "30",
        }
    )
    for key, value in extra.items():
        if value is None:
            env.pop(key, None)
        else:
            env[key] = value
    return env


def _pytest(project: Path, *args: str) -> list[str]:
    """An explicit file: a run without paths is a full suite and would take the host full-suite lock."""
    return [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/test_sample.py", *args]


def _probe(project: Path) -> list[dict[str, str | None]]:
    return [json.loads(line) for line in (project / "probe.jsonl").read_text(encoding="utf-8").splitlines()]


def test_a_dispatch_run_waits_for_a_free_slot_and_runs_inside_it(project: Path) -> None:
    held = test_slots.acquire(1, kind="pytest")
    log = project / "stderr.log"
    with log.open("w", encoding="utf-8") as stderr:
        process = subprocess.Popen(
            _pytest(project), cwd=project, env=_env(project), stdout=subprocess.PIPE, stderr=stderr, text=True
        )
    try:
        assert "queue position 1/1" in wait_for_line(log, stop_if=lambda: process.poll() is not None)
        assert not (project / "probe.jsonl").exists()
    finally:
        held.release()
    stdout, _ = process.communicate(timeout=120)
    assert process.returncode == 0, stdout + log.read_text()
    rows = _probe(project)
    assert len(rows) == 3 and all(row["holder"] and row["holder"].startswith("1:") for row in rows)
    assert test_slots.status()["slots_in_use"] == 0


@pytest.mark.parametrize("case", ["nested", "disabled", "operator_shell", "collect_only", "help"])
def test_runs_outside_the_governor_never_wait(project: Path, case: str) -> None:
    with test_slots.acquire(1, kind="pytest") as held:
        extra: dict[str, str | None] = {test_slots.WAIT_ENV: "1"}
        args: list[str] = []
        if case == "nested":
            extra[test_slots.HOLDER_ENV] = held.marker()
        elif case == "disabled":
            extra[test_slots.ENABLE_ENV] = "off"
        elif case == "operator_shell":
            extra[DISPATCH_TASK_ENV] = None
        elif case == "collect_only":
            args = ["--collect-only"]
        else:
            args = ["--help"]
        result = subprocess.run(
            _pytest(project, *args),
            cwd=project,
            env=_env(project, **extra),
            capture_output=True,
            text=True,
            timeout=120,
        )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "test_slots" not in result.stderr


@pytest.mark.parametrize("case", ["governed", "opt_out", "disabled", "operator_shell", "ci", "nested"])
def test_worker_children_inherit_thread_caps_only_when_governed(project: Path, case: str) -> None:
    from tests.common.test_test_thread_caps import EXPECTED

    source = f"import json, os; print(json.dumps({{key: os.environ.get(key) for key in {list(EXPECTED)!r}}}))"
    (project / "tests/test_sample.py").write_text(
        "import json, os, subprocess, sys\nimport pytest\n"
        "@pytest.mark.parametrize('index', range(4))\n"
        "def test_child(index):\n"
        f"    output = subprocess.check_output([sys.executable, '-c', {source!r}], text=True, timeout=30)\n"
        "    with open(os.environ['SLOT_PROBE_OUT'], 'a') as stream:\n"
        "        stream.write(json.dumps({'worker': os.environ['PYTEST_XDIST_WORKER'], "
        "'env': json.loads(output)}) + '\\n')\n",
        encoding="utf-8",
    )
    extra = dict.fromkeys(EXPECTED, "8")
    extra.update({"LU_TEST_THREAD_CAP": "off" if case == "opt_out" else "on", test_slots.COUNT_ENV: "2"})
    if case == "disabled":
        extra[test_slots.ENABLE_ENV] = "off"
    elif case == "operator_shell":
        extra[DISPATCH_TASK_ENV] = None
    elif case == "ci":
        extra.update({"CI": "true", test_slots.ENABLE_ENV: None})
    with contextlib.ExitStack() as stack:
        if case == "nested":
            held = stack.enter_context(test_slots.acquire(2, kind="launcher", environ=_env(project, **extra)))
            extra[test_slots.HOLDER_ENV] = held.marker()
            extra[DISPATCH_TASK_ENV] = None
        result = subprocess.run(
            _pytest(project, "-n", "2"),
            cwd=project,
            env=_env(project, **extra),
            capture_output=True,
            text=True,
            timeout=120,
        )
    assert result.returncode == 0, result.stdout + result.stderr
    rows = _probe(project)
    assert {row["worker"] for row in rows} == {"gw0", "gw1"}
    expected = EXPECTED if case in {"governed", "nested"} else dict.fromkeys(EXPECTED, "8")
    assert all(row["env"] == expected for row in rows)


def test_a_slot_wait_timeout_is_a_typed_usage_error(project: Path) -> None:
    with test_slots.acquire(1, kind="pytest"):
        result = subprocess.run(
            _pytest(project),
            cwd=project,
            env=_env(project, **{test_slots.WAIT_ENV: "0.5"}),
            capture_output=True,
            text=True,
            timeout=120,
        )
    assert result.returncode == pytest.ExitCode.USAGE_ERROR, result.stdout + result.stderr
    assert "test_slots_wait_timeout" in result.stderr
    assert not (project / "probe.jsonl").exists()


def test_xdist_workers_never_exceed_the_slots_held(project: Path) -> None:
    result = subprocess.run(
        _pytest(project, "-p", "xdist", "-n", "2"),
        cwd=project,
        env=_env(project),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    rows = _probe(project)
    assert len(rows) == 3
    assert {row["worker"] for row in rows} == {"gw0"}
    assert all(row["holder"] and row["holder"].startswith("1:") for row in rows)


def _xdist_run(project: Path, *args: str, **extra: str | None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        _pytest(project, "-p", "xdist", *args),
        cwd=project,
        env=_env(project, **extra),
        capture_output=True,
        text=True,
        timeout=120,
    )


# xdist sets PYTEST_XDIST_WORKER_COUNT in every worker it starts, so the probe reads the real fan-out.
_NESTED_CASES = [
    pytest.param(1, "dispatch", ["-n", "2"], id="dispatch-n2-held1"),
    pytest.param(1, "dispatch", ["-n", "auto"], id="dispatch-nauto-held1"),
    pytest.param(1, "dispatch", ["--dist=load", "--tx", "popen", "--tx", "popen"], id="dispatch-tx-list-held1"),
    pytest.param(1, "dispatch", ["--dist=load", "--tx", "2*popen"], id="dispatch-tx-star-held1"),
    pytest.param(1, "inside_a_worker", ["-n", "2"], id="inside-a-worker-n2-held1"),
    pytest.param(2, "operator_shell", ["-n", "4"], id="operator-n4-held2"),
    pytest.param(2, "operator_shell", ["-n", "auto"], id="operator-nauto-held2"),
    pytest.param(2, "operator_shell", ["--dist=load", "--tx", "3*popen"], id="operator-tx-star-held2"),
]


@pytest.mark.parametrize(("held", "case", "args"), _NESTED_CASES)
def test_a_nested_run_starts_no_more_workers_than_the_hold_it_inherits(
    project: Path, monkeypatch: pytest.MonkeyPatch, held: int, case: str, args: list[str]
) -> None:
    """A pytest run below a live holder runs inside its slots: it never queues and never fans out wider (#10662)."""
    monkeypatch.setenv(test_slots.COUNT_ENV, str(held))
    with test_slots.acquire(held, kind="pytest") as hold:
        # The test holds the whole pool, so a child that queued for its own slots would time out.
        extra: dict[str, str | None] = {
            test_slots.HOLDER_ENV: hold.marker(),
            test_slots.WAIT_ENV: "1",
            test_slots.XDIST_AUTO_ENV: "4",
        }
        if case == "operator_shell":  # a descendant of the gate or the launcher in an operator shell
            extra[DISPATCH_TASK_ENV] = None
        elif case == "inside_a_worker":  # started by a test that itself runs in an xdist worker
            extra["PYTEST_XDIST_WORKER"] = "gw0"
        result = _xdist_run(project, *args, **extra)
        rows = _probe(project) if (project / "probe.jsonl").exists() else []
        assert result.returncode == 0, result.stdout + result.stderr
        assert len(rows) == 3
        assert {row["workers"] for row in rows} == {str(held)}
        assert {row["holder"] for row in rows} == {hold.marker()}
        assert {row["auto"] for row in rows} == {str(held)}
        assert "test_slots" not in result.stderr


@pytest.mark.parametrize("marker", ["stale", "forged"])
def test_a_stale_or_forged_holder_marker_never_loosens_the_cap(project: Path, marker: str) -> None:
    """A marker without a live holder is ignored: the dispatch run queues for its own slots and fans out to them."""
    with test_slots.acquire(1, kind="pytest") as gone:
        stale = gone.marker()
    value = stale if marker == "stale" else f"9:{Path(stale).parent / 'forged.ticket'}"
    result = _xdist_run(project, "-n", "2", **{test_slots.HOLDER_ENV: value})
    assert result.returncode == 0, result.stdout + result.stderr
    rows = _probe(project)
    assert len(rows) == 3 and {row["workers"] for row in rows} == {"1"}
    holders = {row["holder"] for row in rows}
    assert len(holders) == 1 and holders != {value} and holders.pop().startswith("1:")
    assert test_slots.status()["slots_in_use"] == 0


def test_a_dispatch_run_cuts_a_starred_tx_list_to_the_slots_it_holds(project: Path) -> None:
    result = _xdist_run(project, "--dist=load", "--tx", "2*popen")
    assert result.returncode == 0, result.stdout + result.stderr
    rows = _probe(project)
    assert len(rows) == 3 and {row["workers"] for row in rows} == {"1"}
    assert all(row["holder"] and row["holder"].startswith("1:") for row in rows)


@pytest.mark.parametrize("prior", [None, "8", "1", "0"])
def test_an_in_process_nested_session_restores_the_auto_worker_count(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, prior: str | None
) -> None:
    """``pytest.main`` inside a holder caps ``-n auto`` for its own session only and leaves the outer hold held.

    An existing lower cap, ``0`` (serial) included, is kept.
    """
    monkeypatch.setenv(test_slots.ENABLE_ENV, "on")
    monkeypatch.setenv(test_slots.DIR_ENV, str(tmp_path / "pool"))
    monkeypatch.setenv(test_slots.COUNT_ENV, "2")
    monkeypatch.setenv("LU_TEST_THREAD_CAP", "on")
    monkeypatch.setenv("OMP_NUM_THREADS", "8")
    monkeypatch.delenv("MKL_NUM_THREADS", raising=False)
    if prior is None:
        monkeypatch.delenv(test_slots.XDIST_AUTO_ENV, raising=False)
    else:
        monkeypatch.setenv(test_slots.XDIST_AUTO_ENV, prior)
    with test_slots.acquire(2, kind="pytest") as hold:
        monkeypatch.setenv(test_slots.HOLDER_ENV, hold.marker())
        option = SimpleNamespace(numprocesses="auto", maxprocesses=None, tx=None, collectonly=False)
        cleanups: list[Callable[[], None]] = []
        config = SimpleNamespace(option=option, add_cleanup=cleanups.append)
        pytest_dispatch_cap._acquire_test_slots(config, acquire=True)
        assert option.maxprocesses == 2
        assert os.environ[test_slots.XDIST_AUTO_ENV] == (prior if prior in {"0", "1"} else "2")
        assert os.environ["OMP_NUM_THREADS"] == "1"
        assert os.environ["MKL_NUM_THREADS"] == "1"
        assert len(cleanups) == 1
        cleanups.pop()()  # pytest's config cleanup stack, closed when the session ends
        assert os.environ.get(test_slots.XDIST_AUTO_ENV) == prior
        assert os.environ["OMP_NUM_THREADS"] == "8"
        assert "MKL_NUM_THREADS" not in os.environ
        assert os.environ[test_slots.HOLDER_ENV] == hold.marker()
        assert test_slots.inherited_hold() == 2


_LONG_TESTS = """\
import os
import time


def _run():
    out = os.environ["SLOT_PROBE_OUT"] + "." + os.environ["PYTEST_XDIST_WORKER"]
    start = time.monotonic()
    with open(out + ".start", "w", encoding="utf-8") as stream:
        stream.write(f"{start}\\n")
    time.sleep(float(os.environ["SLOT_TEST_SECONDS"]))
    with open(out + ".end", "w", encoding="utf-8") as stream:
        stream.write(f"{start} {time.monotonic()}\\n")


def test_first():
    _run()


def test_second():
    _run()
"""

# The replacement run's command: when it ran, on the host's monotonic clock, which every process shares.
_STAMP = "import sys, time; open(sys.argv[1], 'w').write(f'{time.monotonic()}\\n')"


def _wait_for_files(paths: list[Path], process: subprocess.Popen[str], seconds: float = 60) -> None:
    deadline = time.monotonic() + seconds
    while not all(path.exists() and path.read_text(encoding="utf-8").endswith("\n") for path in paths):
        assert time.monotonic() < deadline, f"timed out waiting for {[path.name for path in paths]}"
        assert process.poll() is None or all(path.exists() for path in paths), "the controller ended early"
        time.sleep(0.05)


@pytest.mark.parametrize("hold", ["review-turn", "dispatch-hold"])
def test_slots_stay_taken_until_the_last_xdist_worker_of_a_killed_controller_exits(
    project: Path, monkeypatch: pytest.MonkeyPatch, hold: str
) -> None:
    """Killing a governed pytest controller while its xdist workers run tests never frees its slots early.

    Workers start with their inherited descriptors closed, so they must join the hold themselves: the slots stay
    taken, and no replacement run starts, until the last worker has finished its test and exited.
    """
    monkeypatch.setenv(test_slots.COUNT_ENV, "2")
    (project / "tests" / "test_sample.py").write_text(_LONG_TESTS, encoding="utf-8")
    probe = project / "probe.jsonl"  # SLOT_PROBE_OUT, which each worker suffixes with its id
    extra: dict[str, str | None] = {"SLOT_TEST_SECONDS": "4", test_slots.SESSION_ENV: None}
    issued = test_slots.acquire(2, kind="review", environ=_env(project)) if hold == "review-turn" else None
    if issued is not None:  # the dispatch worker's review hold; the controller below takes its turn
        extra[test_slots.HOLDER_ENV] = issued.marker()
    controller = subprocess.Popen(
        _pytest(project, "-p", "xdist", "-n", "2"),
        cwd=project,
        env=_env(project, **extra),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,  # its own process group, so cleanup reaches the orphaned workers
    )
    try:
        _wait_for_files([Path(f"{probe}.gw0.start"), Path(f"{probe}.gw1.start")], controller)
        if issued is not None:
            issued.release()  # the issuing worker ends first; only the turn's runs keep the slots now
        os.kill(controller.pid, signal.SIGKILL)
        controller.wait(timeout=30)
        report = test_slots.status()
        assert (report["slots_in_use"], report["slots_draining"], report["slots_free"]) == (0, 2, 0), report
        stamp = project / "replacement"
        governor = [sys.executable, "-m", "scripts.common.test_slots", "run", "--slots", "2", "--"]
        replacement = subprocess.run(
            [*governor, sys.executable, "-c", _STAMP, str(stamp)],
            cwd=_REPO_ROOT,
            env=_env(project, **{test_slots.WAIT_ENV: "60", DISPATCH_TASK_ENV: None, test_slots.SESSION_ENV: None}),
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert replacement.returncode == 0, replacement.stdout + replacement.stderr
        ends = [Path(f"{probe}.{worker}.end") for worker in ("gw0", "gw1")]
        assert all(path.exists() for path in ends), "a worker never finished its test"
        last_worker_end = max(float(path.read_text(encoding="utf-8").split()[1]) for path in ends)
        assert float(stamp.read_text(encoding="utf-8")) >= last_worker_end
    finally:
        if issued is not None:
            issued.release()
        with contextlib.suppress(ProcessLookupError):
            os.killpg(controller.pid, signal.SIGKILL)
        if controller.poll() is None:
            controller.wait(timeout=30)


# The fixture project's conftest: in an xdist worker only, opening a slot file to join the hold fails.
_WORKER_JOIN_FAULT = """\
import errno
import os
import sys
from pathlib import Path

from scripts.common import test_slots

_real_open = os.open


def _opening(path, flags, *args, **kwargs):
    # Only the worker's own join of a slot fails; the marker's checks and every other open stay real.
    if Path(os.fspath(path)).name.startswith("slot-") and sys._getframe(1).f_code.co_name == "_share":
        raise OSError(errno.EIO, "injected slot open failure")
    return _real_open(path, flags, *args, **kwargs)


if os.environ.get("PYTEST_XDIST_WORKER"):
    test_slots.os.open = _opening
"""


def _stamps(probe: Path, suffix: str) -> dict[str, float]:
    """Each worker's ``start`` time, or its ``end`` time, keyed by worker id (a replaced worker gets a new id)."""
    found: dict[str, float] = {}
    for path in probe.parent.glob(f"{probe.name}.*.{suffix}"):
        text = path.read_text(encoding="utf-8")
        if text.endswith("\n"):
            found[path.name.split(".")[-2]] = float(text.split()[-1])
    return found


@pytest.mark.parametrize("hold", ["review-turn", "dispatch-hold"])
def test_a_worker_that_cannot_join_its_controllers_hold_runs_no_test(
    project: Path, monkeypatch: pytest.MonkeyPatch, hold: str
) -> None:
    """A marked xdist worker whose own join fails runs no test, so a killed controller frees no slot it still uses.

    The controller's hold is real; every worker's open of a slot file fails. A worker that ran its tests anyway would
    hold no slot, and killing its controller would admit a replacement run beside it. It refuses before its session
    instead, typed, and the controller's run fails visibly.
    """
    monkeypatch.setenv(test_slots.COUNT_ENV, "2")
    (project / "tests" / "test_sample.py").write_text(_LONG_TESTS, encoding="utf-8")
    (project / "tests" / "conftest.py").write_text(_WORKER_JOIN_FAULT, encoding="utf-8")
    probe = project / "probe.jsonl"  # SLOT_PROBE_OUT, which each worker suffixes with its id
    extra: dict[str, str | None] = {"SLOT_TEST_SECONDS": "4", test_slots.SESSION_ENV: None}
    issued = test_slots.acquire(2, kind="review", environ=_env(project)) if hold == "review-turn" else None
    if issued is not None:
        extra[test_slots.HOLDER_ENV] = issued.marker()
    log = project / "controller.log"  # a file, not a pipe: orphaned workers keep a pipe open until they exit
    with log.open("w", encoding="utf-8") as stream:
        controller = subprocess.Popen(
            _pytest(project, "-p", "xdist", "-n", "2"),
            cwd=project,
            env=_env(project, **extra),
            stdout=stream,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,  # its own process group, so cleanup reaches the orphaned workers
        )
    try:
        deadline = time.monotonic() + 60
        while controller.poll() is None and len(_stamps(probe, "start")) < 2:
            assert time.monotonic() < deadline, "the controller neither ran its tests nor ended"
            time.sleep(0.05)
        if issued is not None:
            issued.release()  # the issuing worker ends first; only the turn's runs keep the slots now
        with contextlib.suppress(ProcessLookupError):
            os.kill(controller.pid, signal.SIGKILL)  # the controller dies while any worker it started still runs
        controller.wait(timeout=30)
        stamp = project / "replacement"
        governor = [sys.executable, "-m", "scripts.common.test_slots", "run", "--slots", "2", "--"]
        replacement = subprocess.run(
            [*governor, sys.executable, "-c", _STAMP, str(stamp)],
            cwd=_REPO_ROOT,
            env=_env(project, **{test_slots.WAIT_ENV: "60", DISPATCH_TASK_ENV: None, test_slots.SESSION_ENV: None}),
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert replacement.returncode == 0, replacement.stdout + replacement.stderr
        admitted = float(stamp.read_text(encoding="utf-8"))
        started = _stamps(probe, "start")
        deadline = time.monotonic() + 30
        while set(_stamps(probe, "end")) != set(started):
            assert time.monotonic() < deadline, "a worker never finished its test"
            time.sleep(0.05)
        ended = _stamps(probe, "end")
        output = log.read_text(encoding="utf-8")
        overlapped_by_replacement = sorted(worker for worker, end in ended.items() if admitted < end)
        assert overlapped_by_replacement == [], output
        assert started == {}, output
        assert controller.returncode not in (0, -signal.SIGKILL), output
        assert "test_slots_pool_unavailable" in output
    finally:
        if issued is not None:
            issued.release()
        with contextlib.suppress(ProcessLookupError):
            os.killpg(controller.pid, signal.SIGKILL)
        if controller.poll() is None:
            controller.wait(timeout=30)


@pytest.mark.parametrize("marker", ["stale", "forged"])
def test_a_worker_no_live_hold_names_runs_as_before(project: Path, marker: str) -> None:
    """An xdist worker under a marker that names no live hold is not its run's to keep: it runs, never refused.

    The run is not a dispatch run, so it takes no slots of its own and passes the stale or forged marker to its
    workers unchanged. Their slot opens would fail as above, yet they never try one.
    """
    (project / "tests" / "conftest.py").write_text(_WORKER_JOIN_FAULT, encoding="utf-8")
    with test_slots.acquire(1, kind="pytest") as gone:
        stale = gone.marker()
    value = stale if marker == "stale" else f"9:{Path(stale).parent / 'forged.ticket'}"
    result = _xdist_run(project, "-n", "2", **{test_slots.HOLDER_ENV: value, DISPATCH_TASK_ENV: None})
    assert result.returncode == 0, result.stdout + result.stderr
    rows = _probe(project)
    assert len(rows) == 3 and {row["holder"] for row in rows} == {value}
    assert "test_slots" not in result.stdout + result.stderr


_REFUSED_AFTER_THE_PLUGIN = """\
import json
import os

import pytest

from scripts.common import test_slots

code = pytest.main(["-q", "-p", "no:cacheprovider", "tests/test_sample.py", "-n", "2", "--pdb"])
print(json.dumps({
    "code": int(code),
    "in_use": test_slots.status()["slots_in_use"],
    "holder": os.environ.get(test_slots.HOLDER_ENV),
    "auto": os.environ.get(test_slots.XDIST_AUTO_ENV),
}))
"""


@pytest.mark.parametrize("nested", [False, True], ids=["own-slots", "inherited-hold"])
def test_an_in_process_run_refused_after_the_plugin_ran_gives_everything_back(project: Path, nested: bool) -> None:
    """xdist refuses ``--pdb`` with workers after this plugin's hook, before the session configures.

    ``pytest.main`` must still return the slots it took and restore the variables it set.
    """
    outer = test_slots.acquire(1, kind="pytest") if nested else None
    marker = outer.marker() if outer is not None else None
    try:
        result = subprocess.run(
            [sys.executable, "-c", _REFUSED_AFTER_THE_PLUGIN],
            cwd=project,
            env=_env(project, **{test_slots.HOLDER_ENV: marker}),
            capture_output=True,
            text=True,
            timeout=120,
        )
    finally:
        if outer is not None:
            outer.release()
    assert result.returncode == 0, result.stdout + result.stderr
    seen = json.loads(result.stdout.strip().splitlines()[-1])
    expected = {"code": pytest.ExitCode.USAGE_ERROR, "in_use": 1 if nested else 0, "holder": marker, "auto": None}
    assert seen == expected, result.stderr
