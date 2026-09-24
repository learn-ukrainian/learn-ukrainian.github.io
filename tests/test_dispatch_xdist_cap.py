"""Dispatch-worker xdist cap and host-wide full-suite lock (#8645 part B)."""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from scripts.ci.pytest_dispatch_cap import (
    CAP_LINE,
    DISPATCH_TASK_ENV,
    FULL_SUITE_BUSY,
    LOCK_ENV,
    LOCK_PATH,
    acquire_full_suite_lock,
    configured_lock_path,
    dispatch_marker_set,
    is_full_suite,
    is_tests_root,
    path_covers_full_suite,
    release_full_suite_lock,
    repository_root,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_PYTEST = sys.executable


def _write_probe(directory: Path) -> None:
    (directory / "conftest.py").write_text(
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
    scripts = (_REPO_ROOT / "scripts").as_posix()
    (directory / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\n"
        "testpaths = ['tests']\n"
        f"pythonpath = ['{scripts}']\n"
        "addopts = '-p ci.pytest_dispatch_cap'\n",
        encoding="utf-8",
    )
    tests = directory / "tests"
    tests.mkdir()
    (tests / "test_sample.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")


def _run_pytest(directory: Path, args: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [_PYTEST, "-m", "pytest", *args],
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
    env["PYTEST_XDIST_AUTO_NUM_WORKERS"] = "8"
    env.pop("PYTEST_XDIST_WORKER", None)
    env.pop("PYTEST_XDIST_WORKER_COUNT", None)
    env.pop("PYTEST_XDIST_TESTRUNUID", None)
    if marker is None:
        env.pop(DISPATCH_TASK_ENV, None)
    else:
        env[DISPATCH_TASK_ENV] = marker
    return env


def _observed_workers(completed: subprocess.CompletedProcess[str]) -> int:
    observed = next(line for line in completed.stdout.splitlines() if line.startswith("OBSERVED_WORKERS="))
    return int(observed.removeprefix("OBSERVED_WORKERS="))


def _assert_workers(completed: subprocess.CompletedProcess[str], expected: int) -> None:
    assert completed.returncode == 0, completed.stderr
    assert _observed_workers(completed) == expected
    assert CAP_LINE in completed.stdout


def test_marker_and_n8_clamps_to_two_workers(tmp_path: Path) -> None:
    _write_probe(tmp_path)
    completed = _run_pytest(
        tmp_path, ["-n", "8", "-q", "tests/test_sample.py"], _child_env(tmp_path, marker="impl-8645-b")
    )
    _assert_workers(completed, 2)


def test_marker_and_nauto_clamps_to_two_workers(tmp_path: Path) -> None:
    _write_probe(tmp_path)
    completed = _run_pytest(
        tmp_path, ["-n", "auto", "-q", "tests/test_sample.py"], _child_env(tmp_path, marker="impl-8645-b")
    )
    _assert_workers(completed, 2)


def test_marker_and_nlogical_clamps_to_two_workers(tmp_path: Path) -> None:
    _write_probe(tmp_path)
    completed = _run_pytest(
        tmp_path, ["-n", "logical", "-q", "tests/test_sample.py"], _child_env(tmp_path, marker="impl-8645-b")
    )
    _assert_workers(completed, 2)


def test_marker_and_n1_stays_one_worker(tmp_path: Path) -> None:
    _write_probe(tmp_path)
    completed = _run_pytest(
        tmp_path, ["-n", "1", "-q", "tests/test_sample.py"], _child_env(tmp_path, marker="impl-8645-b")
    )
    _assert_workers(completed, 1)


def test_without_marker_explicit_n_is_unchanged(tmp_path: Path) -> None:
    _write_probe(tmp_path)
    completed = _run_pytest(tmp_path, ["-n", "4", "-q", "tests/test_sample.py"], _child_env(tmp_path, marker=None))
    assert completed.returncode == 0, completed.stderr
    assert "OBSERVED_WORKERS=4" in completed.stdout
    assert CAP_LINE not in completed.stdout


def _arm_suite_sentinel(directory: Path) -> Path:
    ran = directory / "suite_ran"
    (directory / "tests" / "test_sample.py").write_text(
        textwrap.dedent(
            f"""\
            def test_ok():
                open({str(ran)!r}, "w", encoding="utf-8").write("ran")
                assert True
            """
        ),
        encoding="utf-8",
    )
    return ran


def _hold_tmp_lock(directory: Path, env: dict[str, str]) -> Path:
    lock = directory / "pytest-full-suite.lock"
    env[LOCK_ENV] = str(lock)
    acquire_full_suite_lock(lock)
    return lock


def _assert_refused_before_tests(completed: subprocess.CompletedProcess[str], ran: Path) -> None:
    assert completed.returncode != 0
    assert FULL_SUITE_BUSY in completed.stderr + completed.stdout
    assert not ran.is_file()
    assert "passed" not in completed.stdout


def test_full_suite_lock_fails_fast_and_targeted_paths_do_not(tmp_path: Path) -> None:
    _write_probe(tmp_path)
    ran = _arm_suite_sentinel(tmp_path)
    env = _child_env(tmp_path, marker="impl-8645-b")
    _hold_tmp_lock(tmp_path, env)
    try:
        blocked = _run_pytest(tmp_path, ["-q"], env)
        _assert_refused_before_tests(blocked, ran)
        targeted = _run_pytest(tmp_path, ["-q", "tests/test_sample.py"], env)
    finally:
        release_full_suite_lock()
    assert targeted.returncode == 0, targeted.stderr
    assert ran.is_file()
    assert FULL_SUITE_BUSY not in targeted.stderr + targeted.stdout


def _run_repo(cwd: Path, args: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [_PYTEST, "-m", "pytest", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )


def test_foreign_rootdir_and_no_path_forms_are_refused_while_lock_held(tmp_path: Path) -> None:
    env = _child_env(tmp_path, marker="impl-8645-b")
    _hold_tmp_lock(tmp_path, env)
    forms = (
        (_REPO_ROOT, ["-q", ".", "--rootdir", "/home/ops"]),
        (_REPO_ROOT, ["-q", "tests", "--rootdir", "/home/ops"]),
        (_REPO_ROOT / "tests" / "ai_agent_bridge", ["-q"]),
        (_REPO_ROOT, ["-q", ".", "-k", "nomatch", "-m", "nomatch"]),
    )
    try:
        for cwd, args in forms:
            blocked = _run_repo(cwd, args, env)
            combined = blocked.stderr + blocked.stdout
            assert blocked.returncode != 0, combined
            assert FULL_SUITE_BUSY in combined, combined
            assert " passed" not in blocked.stdout
    finally:
        release_full_suite_lock()


def test_scripts_ci_invocation_loads_the_cap(tmp_path: Path) -> None:
    env = _child_env(tmp_path, marker="impl-8645-b")
    completed = _run_repo(
        _REPO_ROOT,
        ["-n", "1", "-q", "--collect-only", "scripts/ci/test_classify_changes.py"],
        env,
    )
    combined = completed.stdout + completed.stderr
    assert CAP_LINE in combined, combined
    assert FULL_SUITE_BUSY not in combined


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


def test_full_suite_classification() -> None:
    root = repository_root()
    assert root == _REPO_ROOT
    foreign = Path("/home/ops")
    source = _Args("args", [], foreign).ArgsSource
    assert is_full_suite(_Args(source.TESTPATHS, [], foreign))  # type: ignore[arg-type]
    nested = root / "tests" / "ai_agent_bridge"
    invoked = _Args(source.INVOCATION_DIR, [str(nested)], foreign)
    invoked.invocation_params = type("Inv", (), {"dir": nested})()
    assert is_full_suite(invoked)  # type: ignore[arg-type]
    for raw in (".", "./", "tests", "tests/", "./tests", str(root), str(root / "tests"), str(foreign)):
        cfg = _Args(source.ARGS, [raw], foreign)
        cfg.invocation_params = type("Inv", (), {"dir": root})()
        assert is_full_suite(cfg), raw  # type: ignore[arg-type]
        assert path_covers_full_suite(raw, invocation_dir=root)
    targeted = _Args(source.ARGS, ["tests/test_dispatch_xdist_cap.py"], foreign)
    targeted.invocation_params = type("Inv", (), {"dir": root})()
    assert not is_full_suite(targeted)  # type: ignore[arg-type]
    elsewhere = _Args(source.ARGS, ["tests"], foreign)
    elsewhere.invocation_params = type("Inv", (), {"dir": foreign})()
    assert not is_full_suite(elsewhere)  # type: ignore[arg-type]


def test_lock_path_env_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv(LOCK_ENV, raising=False)
    assert configured_lock_path() == LOCK_PATH
    monkeypatch.setenv(LOCK_ENV, "  ")
    assert configured_lock_path() == LOCK_PATH
    override = tmp_path / "nested" / "pytest-full-suite.lock"
    monkeypatch.setenv(LOCK_ENV, str(override))
    assert configured_lock_path() == override
    acquire_full_suite_lock()
    try:
        assert override.is_file()
    finally:
        release_full_suite_lock()
