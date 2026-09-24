"""Cap pytest-xdist fan-out for dispatch workers (#8645 part B).

SCOPE: part B guards dispatch workers against accidental xdist fan-out and
concurrent full suites. It is not a sandbox against deliberate evasion; parts
A (memory admission) and C (per-worker cgroup) are the hard limits.

When ``LEARN_UKRAINIAN_DISPATCH_TASK_ID`` is set, a worker never starts more
than two xdist processes, and a full-suite run takes one host-wide lock.
``delegate.py`` sets ``PYTEST_PLUGINS``, and ``build_agent_env`` forwards only
``ci.pytest_dispatch_cap`` while the dispatch marker is set, so the cap still
loads when a worker copies CI's ``--override-ini addopts=-v`` and drops the
``addopts`` ``-p`` registration. Operator shells and CI leave the dispatch
variable unset, so they are unchanged.
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
TX_TOO_MANY = "dispatch xdist cap: --tx specifies {count} workers; at most {max} are allowed"
_LOCK_ATTR = "_lu_dispatch_full_suite_lock_fd"
_CLAMP_ATTR = "_lu_dispatch_cap_clamped"

_lock_fd: int | None = None


def dispatch_marker_set(environ: Mapping[str, str] | None = None) -> bool:
    env = os.environ if environ is None else environ
    return bool(env.get(DISPATCH_TASK_ENV, "").strip())


def _is_xdist_worker(config: pytest.Config) -> bool:
    return hasattr(config, "workerinput") or bool(os.environ.get("PYTEST_XDIST_WORKER"))


def _resolved(path: Path) -> Path:
    return path.resolve()


def repository_root() -> Path:
    """Checkout that owns this plugin, from its path and the git toplevel.

    ``pytest --rootdir`` and the process cwd are not the suite boundary.
    """
    start = Path(__file__).resolve().parent
    for candidate in (start, *start.parents):
        if (candidate / "pyproject.toml").is_file() and (candidate / ".git").exists():
            return candidate
    raise RuntimeError("pytest dispatch cap cannot locate the repository root from its module path")


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


def path_covers_full_suite(raw: str, *, invocation_dir: Path) -> bool:
    """True when ``raw`` covers this checkout's tests tree.

    The tree is ``<repository_root>/tests``, resolved from this module, not from
    pytest's rootdir. ``.``, ``tests``, and absolute forms are compared after
    resolving against ``invocation_dir``. A node id is never the whole suite.
    """
    if "::" in raw:
        return False
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = invocation_dir / candidate
    try:
        resolved = _resolved(candidate)
        root = repository_root()
        tests_root = _resolved(root / "tests")
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
    """No path args, or any path that covers this checkout's tests tree.

    Zero path arguments are a full suite wherever the process was started.
    ``-k`` and ``-m`` are not path args, so a filtered full tree stays locked.
    Pytest's rootdir is ignored.
    """
    if config.args_source != config.ArgsSource.ARGS:
        return True
    paths = list(config.getoption("file_or_dir") or [])
    if not paths:
        return True
    invocation_dir = Path(config.invocation_params.dir)
    return any(path_covers_full_suite(path, invocation_dir=invocation_dir) for path in paths)


def configured_lock_path(environ: Mapping[str, str] | None = None) -> Path:
    """Host lock, unless ``LU_PYTEST_FULL_SUITE_LOCK`` names another file."""
    env = os.environ if environ is None else environ
    override = env.get(LOCK_ENV, "").strip()
    return Path(override) if override else LOCK_PATH


def tx_spec_worker_count(specs: list[str]) -> int:
    """Workers an xdist ``--tx`` list will start, including ``N*popen`` forms."""
    total = 0
    for spec in specs:
        star = spec.find("*")
        if star == -1:
            total += 1
            continue
        try:
            total += int(spec[:star])
        except ValueError:
            total += 1
    return total


def _lock_file(path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
        raise pytest.UsageError(FULL_SUITE_BUSY) from None
    return fd


def _release_fd(fd: int) -> None:
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


def acquire_full_suite_lock(lock_path: Path | None = None) -> None:
    """Take a non-blocking exclusive lock. Fail immediately when it is held.

    This module-level holder is for callers outside a pytest session. A pytest
    run stores its own fd on the config and releases only that fd.
    """
    global _lock_fd
    if _lock_fd is not None:
        return
    path = configured_lock_path() if lock_path is None else lock_path
    _lock_fd = _lock_file(path)


def release_full_suite_lock() -> None:
    global _lock_fd
    if _lock_fd is None:
        return
    fd = _lock_fd
    _lock_fd = None
    _release_fd(fd)


def _acquire_for_config(config: pytest.Config) -> None:
    """Lock for this run only. A second call on the same config is a no-op."""
    if getattr(config, _LOCK_ATTR, None) is not None:
        return
    setattr(config, _LOCK_ATTR, _lock_file(configured_lock_path()))


def _release_for_config(config: pytest.Config) -> None:
    fd = getattr(config, _LOCK_ATTR, None)
    if fd is None:
        return
    setattr(config, _LOCK_ATTR, None)
    _release_fd(fd)


atexit.register(release_full_suite_lock)


def _arm_maxprocesses(config: pytest.Config) -> None:
    """Set the cap before xdist turns ``-n`` into a ``tx`` list."""
    numprocesses = config.option.numprocesses
    if not numprocesses:
        return
    current = config.option.maxprocesses
    config.option.maxprocesses = MAX_PROCESSES if current is None else min(int(current), MAX_PROCESSES)
    setattr(config, _CLAMP_ATTR, True)


def _shrink_tx(config: pytest.Config) -> None:
    """Cut an already-built worker list down to the cap.

    xdist's own ``pytest_cmdline_main`` applies ``--maxprocesses`` when it runs
    first. A wrapper that runs after that hook still has to shrink ``tx`` when
    this plugin was registered earlier than xdist.
    """
    tx = list(config.option.tx or [])
    numprocesses = config.option.numprocesses
    if not tx and not numprocesses:
        return
    if len(tx) > MAX_PROCESSES or (isinstance(numprocesses, int) and numprocesses > MAX_PROCESSES):
        config.option.numprocesses = MAX_PROCESSES
        config.option.maxprocesses = MAX_PROCESSES
        config.option.tx = ["popen"] * MAX_PROCESSES
        setattr(config, _CLAMP_ATTR, True)


def _reject_oversized_tx(early_config: pytest.Config) -> None:
    """Refuse a ``--tx`` list that would start more than the cap.

    ``N*popen`` is one option value and expands only after configuration, and
    it does not set ``-n``. Count the expanded workers and fail before then.
    """
    if _is_xdist_worker(early_config) or not dispatch_marker_set():
        return
    specs = list(getattr(early_config.known_args_namespace, "tx", None) or [])
    count = tx_spec_worker_count(specs)
    if count > MAX_PROCESSES:
        raise pytest.UsageError(TX_TOO_MANY.format(count=count, max=MAX_PROCESSES))


def pytest_load_initial_conftests(early_config: pytest.Config, parser: pytest.Parser, args: list[str]) -> None:
    del parser, args
    _reject_oversized_tx(early_config)


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
            _acquire_for_config(config)
    outcome = yield
    outcome.get_result()
    if not armed:
        return
    _shrink_tx(config)


def pytest_sessionstart(session: pytest.Session) -> None:
    if _is_xdist_worker(session.config) or not getattr(session.config, _CLAMP_ATTR, False):
        return
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    if reporter is not None:
        reporter.write_line(CAP_LINE)
    else:
        print(CAP_LINE, flush=True)


def pytest_unconfigure(config: pytest.Config) -> None:
    _release_for_config(config)
