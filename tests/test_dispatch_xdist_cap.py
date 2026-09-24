"""Dispatch-worker xdist cap and host-wide full-suite lock (#8645 part B)."""

from __future__ import annotations

import os
import subprocess
import textwrap
from pathlib import Path

from tests.dispatch_xdist_cap import (
    CAP_LINE,
    DISPATCH_TASK_ENV,
    FULL_SUITE_BUSY,
    acquire_full_suite_lock,
    dispatch_marker_set,
    is_full_suite,
    is_tests_root,
    release_full_suite_lock,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_PYTEST = "/home/ops/learn-ukrainian/.venv/bin/python"


def _write_probe(directory: Path) -> None:
    (directory / "probe_workers.py").write_text(
        textwrap.dedent(
            """\
            def pytest_configure(config):
                if hasattr(config, "workerinput"):
                    return
                tx = list(getattr(config.option, "tx", None) or [])
                print(f"OBSERVED_WORKERS={len(tx)}", flush=True)
                config.option.tx = []
                config.option.numprocesses = 0
                config.option.dist = "no"
            """
        ),
        encoding="utf-8",
    )
    (directory / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\ntestpaths = ['tests']\n",
        encoding="utf-8",
    )
    tests = directory / "tests"
    tests.mkdir()
    (tests / "test_sample.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")


def _run_pytest(directory: Path, args: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [_PYTEST, "-m", "pytest", "-p", "probe_workers", "-p", "tests.dispatch_xdist_cap", "--noconftest", *args],
        cwd=directory,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


def _child_env(directory: Path, *, marker: str | None) -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([str(directory), str(_REPO_ROOT), env.get("PYTHONPATH", "")])
    env.pop("PYTEST_ADDOPTS", None)
    env.pop("PYTEST_XDIST_AUTO_NUM_WORKERS", None)
    env.pop("PYTEST_XDIST_WORKER", None)
    env.pop("PYTEST_XDIST_WORKER_COUNT", None)
    env.pop("PYTEST_XDIST_TESTRUNUID", None)
    if marker is None:
        env.pop(DISPATCH_TASK_ENV, None)
    else:
        env[DISPATCH_TASK_ENV] = marker
    return env


def test_marker_and_n8_clamps_to_two_workers(tmp_path: Path) -> None:
    _write_probe(tmp_path)
    completed = _run_pytest(
        tmp_path, ["-n", "8", "-q", "tests/test_sample.py"], _child_env(tmp_path, marker="impl-8645-b")
    )
    assert completed.returncode == 0, completed.stderr
    assert "OBSERVED_WORKERS=2" in completed.stdout
    assert CAP_LINE in completed.stdout


def test_marker_and_nauto_clamps_to_at_most_two_workers(tmp_path: Path) -> None:
    _write_probe(tmp_path)
    completed = _run_pytest(
        tmp_path, ["-n", "auto", "-q", "tests/test_sample.py"], _child_env(tmp_path, marker="impl-8645-b")
    )
    assert completed.returncode == 0, completed.stderr
    observed = next(line for line in completed.stdout.splitlines() if line.startswith("OBSERVED_WORKERS="))
    assert int(observed.removeprefix("OBSERVED_WORKERS=")) <= 2
    assert CAP_LINE in completed.stdout


def test_without_marker_explicit_n_is_unchanged(tmp_path: Path) -> None:
    _write_probe(tmp_path)
    completed = _run_pytest(tmp_path, ["-n", "4", "-q", "tests/test_sample.py"], _child_env(tmp_path, marker=None))
    assert completed.returncode == 0, completed.stderr
    assert "OBSERVED_WORKERS=4" in completed.stdout
    assert CAP_LINE not in completed.stdout


def test_full_suite_lock_fails_fast_and_targeted_paths_do_not(tmp_path: Path) -> None:
    _write_probe(tmp_path)
    env = _child_env(tmp_path, marker="impl-8645-b")
    acquire_full_suite_lock()
    try:
        blocked = _run_pytest(tmp_path, ["-q"], env)
        targeted = _run_pytest(tmp_path, ["-q", "tests/test_sample.py"], env)
    finally:
        release_full_suite_lock()
    assert blocked.returncode != 0
    assert FULL_SUITE_BUSY in blocked.stderr + blocked.stdout
    assert targeted.returncode == 0, targeted.stderr
    assert FULL_SUITE_BUSY not in targeted.stderr + targeted.stdout


def test_ci_workflows_do_not_set_the_dispatch_marker() -> None:
    workflow_dir = _REPO_ROOT / ".github" / "workflows"
    offenders = [
        str(path.relative_to(_REPO_ROOT))
        for path in sorted(workflow_dir.glob("*.yml"))
        if DISPATCH_TASK_ENV in path.read_text(encoding="utf-8")
    ]
    assert offenders == []


def test_blank_marker_is_unset() -> None:
    assert dispatch_marker_set({DISPATCH_TASK_ENV: "  "}) is False
    assert dispatch_marker_set({DISPATCH_TASK_ENV: "task"}) is True
    assert dispatch_marker_set({}) is False


def test_tests_root_detection(tmp_path: Path) -> None:
    tests = tmp_path / "tests"
    tests.mkdir()
    assert is_tests_root("tests", invocation_dir=tmp_path, rootpath=tmp_path)
    assert is_tests_root("tests/", invocation_dir=tmp_path, rootpath=tmp_path)
    assert not is_tests_root("tests/test_sample.py", invocation_dir=tmp_path, rootpath=tmp_path)
    assert not is_tests_root("tests/test_sample.py::test_ok", invocation_dir=tmp_path, rootpath=tmp_path)


class _Args:
    def __init__(self, source: object, paths: list[str], root: Path) -> None:
        self.args_source = source
        self.invocation_params = type("Inv", (), {"dir": root})()
        self.rootpath = root
        self._paths = paths
        self.ArgsSource = type("Src", (), {"ARGS": "args", "TESTPATHS": "testpaths", "INVOCATION_DIR": "invocation"})()

    def getoption(self, name: str) -> list[str]:
        assert name == "file_or_dir"
        return self._paths


def test_full_suite_classification(tmp_path: Path) -> None:
    (tmp_path / "tests").mkdir()
    source = _Args("args", [], tmp_path).ArgsSource
    assert is_full_suite(_Args(source.TESTPATHS, [], tmp_path))  # type: ignore[arg-type]
    assert is_full_suite(_Args(source.ARGS, ["tests"], tmp_path))  # type: ignore[arg-type]
    assert not is_full_suite(_Args(source.ARGS, ["tests/test_sample.py"], tmp_path))  # type: ignore[arg-type]
    nested = tmp_path / "tests" / "nested"
    nested.mkdir()
    invoked = _Args(source.INVOCATION_DIR, [], tmp_path)
    invoked.invocation_params = type("Inv", (), {"dir": nested})()
    assert not is_full_suite(invoked)  # type: ignore[arg-type]
