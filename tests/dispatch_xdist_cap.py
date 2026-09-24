"""Cap pytest-xdist fan-out for dispatch workers (#8645 part B).

When ``LEARN_UKRAINIAN_DISPATCH_TASK_ID`` is set, a worker never starts more
than two xdist processes, and a full-suite run takes one host-wide lock.
Operator shells and CI leave the variable unset, so they are unchanged.
"""

from __future__ import annotations

import atexit
import fcntl
import os
from collections.abc import Mapping
from pathlib import Path

import pytest

DISPATCH_TASK_ENV = "LEARN_UKRAINIAN_DISPATCH_TASK_ID"
LOCK_ENV = "LU_PYTEST_FULL_SUITE_LOCK"
MAX_PROCESSES = 2
LOCK_DIR = Path("/var/tmp/lu/learn-ukrainian")
LOCK_PATH = LOCK_DIR / "pytest-full-suite.lock"
FULL_SUITE_BUSY = "full suite already running on this host; run targeted tests — CI runs the full suite"
CAP_LINE = f"dispatch xdist cap: maxprocesses={MAX_PROCESSES}"

_lock_fd: int | None = None
_clamp_applied = False


def dispatch_marker_set(environ: Mapping[str, str] | None = None) -> bool:
    env = os.environ if environ is None else environ
    return bool(env.get(DISPATCH_TASK_ENV, "").strip())


def _is_xdist_worker(config: pytest.Config) -> bool:
    return hasattr(config, "workerinput") or bool(os.environ.get("PYTEST_XDIST_WORKER"))


def _resolved(path: Path) -> Path:
    return path.resolve()


def is_tests_root(raw: str, *, invocation_dir: Path, rootpath: Path) -> bool:
    """True when ``raw`` is the tests directory and not a node id or a file under it."""
    if "::" in raw:
        return False
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = invocation_dir / candidate
    try:
        resolved = _resolved(candidate)
        tests_root = _resolved(rootpath / "tests")
    except OSError:
        return False
    return resolved == tests_root


def path_covers_full_suite(raw: str, *, invocation_dir: Path, rootpath: Path) -> bool:
    """True when ``raw`` is the repo root, the tests root, or an ancestor of the tests root.

    ``.``, ``./``, ``tests``, ``tests/``, and absolute forms all resolve before the
    comparison. ``--rootdir`` is ``rootpath``. A node id is never the whole suite.
    """
    if "::" in raw:
        return False
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = invocation_dir / candidate
    try:
        resolved = _resolved(candidate)
        root = _resolved(rootpath)
        tests_root = _resolved(rootpath / "tests")
    except OSError:
        return False
    if resolved in (root, tests_root):
        return True
    try:
        tests_root.relative_to(resolved)
    except ValueError:
        return False
    return True


def is_full_suite(config: pytest.Config) -> bool:
    """No path args, or any path that covers the tests tree, is a full-suite run.

    ``-k`` and ``-m`` are not path args, so a filtered full tree stays locked.
    """
    invocation_dir = Path(config.invocation_params.dir)
    rootpath = Path(config.rootpath)
    if config.args_source == config.ArgsSource.TESTPATHS:
        return True
    paths = list(config.getoption("file_or_dir") or [])
    if not paths:
        if config.args_source == config.ArgsSource.ARGS:
            return True
        paths = [str(invocation_dir)]
    return any(path_covers_full_suite(path, invocation_dir=invocation_dir, rootpath=rootpath) for path in paths)


def configured_lock_path(environ: Mapping[str, str] | None = None) -> Path:
    """Host lock, unless ``LU_PYTEST_FULL_SUITE_LOCK`` names another file."""
    env = os.environ if environ is None else environ
    override = env.get(LOCK_ENV, "").strip()
    return Path(override) if override else LOCK_PATH


def acquire_full_suite_lock(lock_path: Path | None = None) -> None:
    """Take a non-blocking exclusive lock. Fail immediately when it is held."""
    global _lock_fd
    if _lock_fd is not None:
        return
    path = configured_lock_path() if lock_path is None else lock_path
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
        raise pytest.UsageError(FULL_SUITE_BUSY) from None
    _lock_fd = fd


def release_full_suite_lock() -> None:
    global _lock_fd
    if _lock_fd is None:
        return
    fd = _lock_fd
    _lock_fd = None
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


atexit.register(release_full_suite_lock)


def _arm_maxprocesses(config: pytest.Config) -> None:
    """Set the cap before xdist turns ``-n`` into a ``tx`` list."""
    global _clamp_applied
    numprocesses = config.option.numprocesses
    if not numprocesses:
        return
    current = config.option.maxprocesses
    config.option.maxprocesses = MAX_PROCESSES if current is None else min(int(current), MAX_PROCESSES)
    _clamp_applied = True


def _shrink_tx(config: pytest.Config) -> None:
    """Cut an already-built worker list down to the cap.

    xdist's own ``pytest_cmdline_main`` applies ``--maxprocesses`` when it runs
    first. A wrapper that runs after that hook still has to shrink ``tx`` when
    this plugin was registered earlier than xdist.
    """
    global _clamp_applied
    tx = list(config.option.tx or [])
    numprocesses = config.option.numprocesses
    if not tx and not numprocesses:
        return
    if len(tx) > MAX_PROCESSES or (isinstance(numprocesses, int) and numprocesses > MAX_PROCESSES):
        config.option.numprocesses = MAX_PROCESSES
        config.option.maxprocesses = MAX_PROCESSES
        config.option.tx = ["popen"] * MAX_PROCESSES
        _clamp_applied = True


@pytest.hookimpl(hookwrapper=True)
def pytest_cmdline_main(config: pytest.Config) -> object:
    """Clamp before xdist, and take the full-suite lock before the session runs.

    ``pytest_cmdline_main`` runs the session and ``pytest_unconfigure`` before
    it returns, so a lock taken after ``yield`` does not cover execution.
    xdist workers already have ``workerinput`` and ``PYTEST_XDIST_WORKER`` set
    and must not take the host lock.
    """
    armed = not _is_xdist_worker(config) and dispatch_marker_set()
    if armed:
        _arm_maxprocesses(config)
        if is_full_suite(config):
            acquire_full_suite_lock()
    outcome = yield
    outcome.get_result()
    if not armed:
        return
    _shrink_tx(config)


def pytest_sessionstart(session: pytest.Session) -> None:
    if _is_xdist_worker(session.config) or not _clamp_applied:
        return
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    if reporter is not None:
        reporter.write_line(CAP_LINE)
    else:
        print(CAP_LINE, flush=True)


def pytest_unconfigure(config: pytest.Config) -> None:
    del config
    release_full_suite_lock()
