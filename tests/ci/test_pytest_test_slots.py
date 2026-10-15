"""Dispatch-worker pytest runs draw from the host test-slot pool (#10662).

Each case runs real pytest in a subprocess against a fixture project that loads the dispatch plugin, with a
private pool whose slots this process holds or leaves free.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
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
        assert len(cleanups) == 1
        cleanups.pop()()  # pytest's config cleanup stack, closed when the session ends
        assert os.environ.get(test_slots.XDIST_AUTO_ENV) == prior
        assert os.environ[test_slots.HOLDER_ENV] == hold.marker()
        assert test_slots.inherited_hold() == 2


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
