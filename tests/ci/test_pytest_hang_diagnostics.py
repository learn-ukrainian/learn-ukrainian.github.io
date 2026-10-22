"""Hang diagnostics must not arm pytest's native faulthandler watchdog (#11391).

Defect class: the native faulthandler dump racing with changing frames crashes
the worker. ``faulthandler.dump_traceback_later`` is implemented as a C watchdog
thread (CPython library reference, "Dumping the tracebacks after a timeout"), so
it walks frames without the GIL while the test keeps mutating them. That race
produced SIGSEGV (exit -11) in ``ast.unparse`` during a 110 s diagnostic dump
(PR 11390), and a worker that disappears hides the real cause.

The ordinary suite therefore leaves pytest's ``faulthandler_timeout`` off and
relies on pytest-timeout's 120 s budget for hang reporting. The selected value
is ``0``: ``_pytest.faulthandler.get_timeout_config_value`` only arms the native
watchdog when the effective value is greater than zero.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import textwrap
import tomllib
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_PYPROJECT = _REPO_ROOT / "pyproject.toml"
_NATIVE_WATCHDOG_KEY = "faulthandler_timeout"
# pytest-timeout 2.4.0 ``dump_stacks`` writes ``terminal.sep("~", title="Stack of %s (%s)")``.
_THREAD_DUMP_MARKER = "Stack of "
_TIMEOUT_MARKER = "Timeout"


def _pytest_ini_options(text: str) -> dict[str, object]:
    data = tomllib.loads(text)
    return data.get("tool", {}).get("pytest", {}).get("ini_options", {})


def _native_watchdog_seconds(ini_options: dict[str, object]) -> float:
    return float(ini_options.get(_NATIVE_WATCHDOG_KEY) or 0.0)


def _native_watchdog_armed(ini_options: dict[str, object]) -> bool:
    return _native_watchdog_seconds(ini_options) > 0


def _child_env(tmp_path: Path) -> dict[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("PYTEST_")
        and key not in {"LEARN_UKRAINIAN_DISPATCH_TASK_ID", "LU_TEST_SLOTS_HOLDER", "PYTHONPATH"}
    }
    env["PYTHONPATH"] = str(tmp_path)
    return env


def _effective_native_watchdog_seconds(scratch_dir: Path, config_path: Path) -> float:
    probe_dir = scratch_dir / "config_probe"
    probe_dir.mkdir(parents=True)
    (probe_dir / "probe_ini.py").write_text(
        textwrap.dedent(
            """\
            def pytest_configure(config):
                value = float(config.getini("faulthandler_timeout") or 0.0)
                print(f"EFFECTIVE_FAULTHANDLER_TIMEOUT={value}")
            """
        ),
        encoding="utf-8",
    )
    (probe_dir / "test_probe.py").write_text("def test_probe():\n    pass\n", encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-c",
            str(config_path),
            "--noconftest",
            "--collect-only",
            "-q",
            str(probe_dir / "test_probe.py"),
            "-p",
            "probe_ini",
            "-o",
            "addopts=",
        ],
        cwd=str(probe_dir),
        capture_output=True,
        text=True,
        timeout=60,
        env=_child_env(probe_dir),
    )

    combined = f"{completed.stdout}\n{completed.stderr}"
    assert completed.returncode == 0, f"config probe failed:\n{combined}"
    match = re.search(r"EFFECTIVE_FAULTHANDLER_TIMEOUT=([0-9.]+)", completed.stdout)
    assert match, f"config probe did not report the effective value:\n{combined}"
    return float(match.group(1))


def _assert_native_watchdog_off(scratch_dir: Path, config_path: Path) -> None:
    ini_options = _pytest_ini_options(config_path.read_text(encoding="utf-8"))

    assert not _native_watchdog_armed(ini_options), (
        f"{_NATIVE_WATCHDOG_KEY} must stay 0/absent in {config_path.name}; "
        "pytest-timeout's 120 s thread budget owns hang reporting"
    )
    assert _effective_native_watchdog_seconds(scratch_dir, config_path) == 0.0


def test_ordinary_runs_leave_the_native_watchdog_off(tmp_path: Path) -> None:
    """Native faulthandler dump racing with changing frames crashes the worker (#11391)."""
    _assert_native_watchdog_off(tmp_path / "current", _PYPROJECT)


def test_rearming_the_native_watchdog_fails_the_config_check(tmp_path: Path) -> None:
    """Mutation: restoring ``faulthandler_timeout = 110`` makes the ordinary-run check fail."""
    original = _PYPROJECT.read_text(encoding="utf-8")
    mutated, replacements = re.subn(
        rf"(?m)^{_NATIVE_WATCHDOG_KEY}\s*=.*$",
        f"{_NATIVE_WATCHDOG_KEY} = 110",
        original,
    )
    assert replacements == 1, "the mutation must replace exactly one faulthandler_timeout line"
    mutated_path = tmp_path / "pyproject.toml"
    mutated_path.write_text(mutated, encoding="utf-8")

    with pytest.raises(AssertionError, match=_NATIVE_WATCHDOG_KEY):
        _assert_native_watchdog_off(tmp_path / "mutated", mutated_path)
    assert _effective_native_watchdog_seconds(tmp_path / "mutated-effective", mutated_path) == 110.0


def _write_hang_project(tmp_path: Path) -> Path:
    project = tmp_path / "hang_project"
    project.mkdir()
    (project / "pyproject.toml").write_text(
        textwrap.dedent(
            """\
            [tool.pytest.ini_options]
            timeout = 2
            timeout_method = "thread"
            faulthandler_timeout = 0
            """
        ),
        encoding="utf-8",
    )
    (project / "test_hang.py").write_text(
        textwrap.dedent(
            """\
            import time

            def test_intentional_hang():
                time.sleep(10)
            """
        ),
        encoding="utf-8",
    )
    return project


def _run_hang_project(project: Path, extra_args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "pytest", *extra_args, "-q", "-o", "addopts="],
        cwd=str(project),
        capture_output=True,
        text=True,
        timeout=90,
        env=_child_env(project),
    )


def test_thread_method_keeps_its_stack_dump_without_the_native_watchdog(tmp_path: Path) -> None:
    """A hang still fails with pytest-timeout's GIL-holding stack dump (#11391 AC-02)."""
    project = _write_hang_project(tmp_path)

    completed = _run_hang_project(project, ["-p", "no:xdist"])
    combined = f"{completed.stdout}\n{completed.stderr}"

    assert completed.returncode != 0, f"the hang must fail the child run:\n{combined}"
    assert _TIMEOUT_MARKER in combined, f"the pytest-timeout marker is missing:\n{combined}"
    assert _THREAD_DUMP_MARKER in combined, f"the all-thread stack dump is missing:\n{combined}"
    assert "test_intentional_hang" in combined, f"the hang must name the hanging test:\n{combined}"


def test_hung_test_is_reported_by_the_controller_under_xdist(tmp_path: Path) -> None:
    """The xdist controller still surfaces the hung test after the native watchdog is off.

    pytest-timeout 2.4.0's ``thread`` method ends the worker with ``os._exit(1)``
    after its Python-timer dump, so the controller reports a downed worker even
    without the native watchdog. The native dump cannot be observed here because
    an xdist worker's ``sys.stdout`` is ``/dev/null`` while pytest-timeout writes
    its dump through the terminal writer. Worker survival under xdist therefore
    cannot be asserted for the ``thread`` method; the stack dump proof lives in
    ``test_thread_method_keeps_its_stack_dump_without_the_native_watchdog``.
    """
    project = _write_hang_project(tmp_path)

    completed = _run_hang_project(project, ["-p", "xdist", "-n", "2"])
    combined = f"{completed.stdout}\n{completed.stderr}"

    assert completed.returncode != 0, f"the hang must fail the child run:\n{combined}"
    assert "test_intentional_hang" in combined, f"the controller must name the hung test:\n{combined}"
