"""Dispatch-worker pytest runs draw from the host test-slot pool (#10662).

Each case runs real pytest in a subprocess against a fixture project that loads the dispatch plugin, with a
private pool whose slots this process holds or leaves free.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

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
