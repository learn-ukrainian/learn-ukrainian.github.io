"""Cap pytest-xdist fan-out for dispatch workers (#8645 part B).

SCOPE: part B guards dispatch workers against accidental xdist fan-out and
concurrent full suites. It is not a sandbox against deliberate evasion; parts
A (memory admission) and C (per-worker cgroup) are the hard limits.

When ``LEARN_UKRAINIAN_DISPATCH_TASK_ID`` is set, a worker never starts more
than two xdist processes, and a full-suite run takes one host-wide lock. A
``--collect-only`` run executes no test, so it never takes the lock (#9434).
An exact ``-m repo_wide`` selection runs the bounded invariant registry and
also skips the lock (#9670); other full-tree filters remain locked.
``delegate.py`` sets ``PYTEST_PLUGINS``, and ``build_agent_env`` forwards only
``ci.pytest_dispatch_cap`` while the dispatch marker is set, so the cap still
loads when a worker copies CI's ``--override-ini addopts=-v`` and drops the
``addopts`` ``-p`` registration. Operator shells and CI leave the dispatch
variable unset, so they are unchanged.

When pytest-xdist is not importable (a minimal venv with only pytest and
pyyaml, as the rules-deployment-check lane builds), the fan-out cap is a no-op:
xdist is the only thing that fans a run out, so it also owns the ``-n``/``--tx``
options this plugin clamps. The full-suite lock does not depend on xdist and
still applies.

A dispatch run also holds host test slots for its whole session (#10662): it
asks ``scripts/common/test_slots.py`` for its process count (its xdist workers
after the cap, or one), waits in the host's FIFO queue with progress lines, and
starts no more workers than the slots it holds. ``LU_TEST_SLOTS=off`` and a
true ``CI`` variable disable this. ``--collect-only``, ``--help`` and other runs
that execute no test take no slots. A run nested inside a live holder
(``LU_TEST_SLOTS_HOLDER``) queues for nothing, dispatch run or not, and starts
at most the inherited count of workers: ``maxprocesses``, an explicit ``--tx``
list and ``PYTEST_XDIST_AUTO_NUM_WORKERS`` are all capped before the session.
"""

from __future__ import annotations

import atexit
import fcntl
import os
from collections.abc import Generator, Mapping
from pathlib import Path
from types import ModuleType

import pytest

DISPATCH_TASK_ENV = "LEARN_UKRAINIAN_DISPATCH_TASK_ID"
LOCK_ENV = "LU_PYTEST_FULL_SUITE_LOCK"
MAX_PROCESSES = 2
# Keep this allowlist narrow: repo_wide has a maintained scanner registry.
# Negation, OR expressions and unknown markers can still select a large suite.
BOUNDED_MARKERS = frozenset({"repo_wide"})
LOCK_DIR = Path("/var/tmp/lu/learn-ukrainian")
LOCK_PATH = LOCK_DIR / "pytest-full-suite.lock"
FULL_SUITE_BUSY = "full suite already running on this host; run targeted tests — CI runs the full suite"
CAP_LINE = f"dispatch xdist cap: maxprocesses={MAX_PROCESSES}"
TX_TOO_MANY = "dispatch xdist cap: --tx specifies {count} workers; at most {max} are allowed"
_LOCK_ATTR = "_lu_dispatch_full_suite_lock_fd"
_CLAMP_ATTR = "_lu_dispatch_cap_clamped"
_SLOTS_ATTR = "_lu_test_slots_hold"
_SLOTS_PRIOR_MARKER_ATTR = "_lu_test_slots_prior_marker"
_AUTO_PRIOR_ATTR = "_lu_test_slots_prior_auto_workers"
# Informational runs execute no test, so they never queue for slots.
_NO_TEST_OPTIONS = ("help", "version", "showfixtures", "show_fixtures_per_test", "markers")

_lock_fd: int | None = None


def dispatch_marker_set(environ: Mapping[str, str] | None = None) -> bool:
    env = os.environ if environ is None else environ
    return bool(env.get(DISPATCH_TASK_ENV, "").strip())


def xdist_available() -> bool:
    """Whether pytest-xdist is importable in this interpreter.

    xdist is the only plugin that fans a run out, so when it is absent the cap
    has nothing to constrain and every fan-out hook no-ops. A run that loads
    xdist only partially (for example ``-p no:xdist``) is handled by the
    option guards, which treat a missing ``numprocesses``/``tx`` as no fan-out.
    """
    try:
        import xdist  # noqa: F401
    except ImportError:
        return False
    return True


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
    """Whether the invocation needs the host-wide full-suite lock.

    Zero path arguments are a full suite wherever the process was started.
    Only an exact allowlisted marker selection exempts a full-tree run;
    ``-k`` and other ``-m`` expressions stay locked. Pytest's rootdir is ignored.
    """
    options = getattr(config, "option", None)
    if getattr(options, "markexpr", "").strip() in BOUNDED_MARKERS:
        return False
    if config.args_source != config.ArgsSource.ARGS:
        return True
    paths = list(config.getoption("file_or_dir") or [])
    if not paths:
        return True
    invocation_dir = Path(config.invocation_params.dir)
    return any(path_covers_full_suite(path, invocation_dir=invocation_dir) for path in paths)


def collection_only(config: pytest.Config) -> bool:
    """True for ``--collect-only``: pytest collects and reports, and runs no test.

    pytest's ``pytest_runtestloop`` returns before the first test, and xdist
    starts no workers, so such a run is outside what the full-suite lock guards.
    A repository check that collects the tree in a child process while its own
    parent run holds the lock relies on this (#9434).
    """
    return bool(getattr(config.option, "collectonly", False))


def configured_lock_path(environ: Mapping[str, str] | None = None) -> Path:
    """Host lock, unless ``LU_PYTEST_FULL_SUITE_LOCK`` names another file."""
    env = os.environ if environ is None else environ
    override = env.get(LOCK_ENV, "").strip()
    return Path(override) if override else LOCK_PATH


def expand_tx_specs(specs: list[str]) -> list[str]:
    """One spec per worker, ``N*popen`` expanded exactly as xdist's ``parse_tx_spec_config`` expands it."""
    expanded: list[str] = []
    for spec in specs:
        star = spec.find("*")
        try:
            count = int(spec[:star])
        except ValueError:
            expanded.append(spec)
        else:
            expanded.extend([spec[star + 1 :]] * count)
    return expanded


def tx_spec_worker_count(specs: list[str]) -> int:
    """Workers an xdist ``--tx`` list will start, including ``N*popen`` forms."""
    return len(expand_tx_specs(specs))


def _lock_file(path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
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
    numprocesses = getattr(config.option, "numprocesses", None)
    if not numprocesses:
        return
    current = getattr(config.option, "maxprocesses", None)
    # xdist treats a missing or non-positive maxprocesses as unlimited.
    value = MAX_PROCESSES if current is None else int(current)
    if value < 1 or value > MAX_PROCESSES:
        value = MAX_PROCESSES
    config.option.maxprocesses = value
    setattr(config, _CLAMP_ATTR, True)


def _shrink_tx(config: pytest.Config) -> None:
    """Cut an already-built worker list down to the cap.

    xdist's own ``pytest_cmdline_main`` applies ``--maxprocesses`` when it runs
    first. A wrapper that runs after that hook still has to shrink ``tx`` when
    this plugin was registered earlier than xdist.
    """
    tx = list(getattr(config.option, "tx", None) or [])
    numprocesses = getattr(config.option, "numprocesses", None)
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
    if _is_xdist_worker(early_config) or not dispatch_marker_set() or not xdist_available():
        return
    specs = list(getattr(early_config.known_args_namespace, "tx", None) or [])
    count = tx_spec_worker_count(specs)
    if count > MAX_PROCESSES:
        raise pytest.UsageError(TX_TOO_MANY.format(count=count, max=MAX_PROCESSES))


def _test_slots():
    """The host test-slot governor, from the repository root or, like this plugin, from ``scripts/``."""
    try:
        from scripts.common import test_slots
    except ImportError:
        from common import test_slots  # type: ignore[no-redef]
    return test_slots


def requested_test_processes(config: pytest.Config) -> int:
    """Processes this run starts: its xdist workers after the dispatch cap, otherwise one."""
    if not xdist_available():
        return 1
    option = config.option
    numprocesses = getattr(option, "numprocesses", None)
    cap = int(getattr(option, "maxprocesses", None) or MAX_PROCESSES)
    if numprocesses in ("auto", "logical"):
        return cap
    if isinstance(numprocesses, int) and numprocesses > 0:
        return min(numprocesses, cap)
    tx = list(getattr(option, "tx", None) or [])
    return max(1, min(tx_spec_worker_count(tx), cap)) if tx else 1


def _limit_workers(config: pytest.Config, count: int) -> None:
    """Start at most ``count`` xdist workers: cap ``-n`` (``auto`` included) and cut an explicit ``--tx`` list.

    Runs before xdist's own ``pytest_cmdline_main`` turns ``-n`` into a ``tx`` list, and before the session
    expands ``N*popen`` specs.
    """
    option = config.option
    if getattr(option, "numprocesses", None):
        current = getattr(option, "maxprocesses", None)
        # xdist treats a missing or non-positive maxprocesses as unlimited.
        option.maxprocesses = count if current is None or int(current) < 1 else min(int(current), count)
        return
    specs = expand_tx_specs(list(getattr(option, "tx", None) or []))
    if len(specs) > count:
        option.tx = specs[:count]


def _run_inside_inherited_hold(config: pytest.Config, slots: ModuleType, count: int) -> None:
    """Start at most ``count`` workers, the slots a live ancestor holds, here and in this run's descendants."""
    config.add_cleanup(lambda: _release_test_slots(config))
    _limit_workers(config, count)
    name = slots.XDIST_AUTO_ENV
    auto_cap = slots.auto_worker_cap()  # a lower existing cap, such as a driver scope's, is kept
    setattr(config, _AUTO_PRIOR_ATTR, (name, os.environ.get(name)))
    os.environ[name] = str(count if auto_cap is None else min(auto_cap, count))


def _acquire_test_slots(config: pytest.Config, *, acquire: bool) -> None:
    """Start no more xdist workers than the host test slots this session runs inside.

    A live ancestor hold bounds every run below it, dispatch run or not: the run queues for nothing and starts
    at most the inherited count of workers. Otherwise only a dispatch run (``acquire``) waits for and holds
    slots of its own. A marker without a live holder is ignored, so a dispatch run under it still queues.
    """
    if collection_only(config) or any(getattr(config.option, name, False) for name in _NO_TEST_OPTIONS):
        return
    slots = _test_slots()
    if not acquire and not os.environ.get(slots.HOLDER_ENV, "").strip():
        return  # no hold to run inside and none to take: an operator shell or CI run stays unchanged
    try:
        if not slots.enabled():
            return
        inherited = slots.inherited_hold()
        if inherited is not None:
            _run_inside_inherited_hold(config, slots, inherited)
            return
        if not acquire:
            return
        hold = slots.acquire(requested_test_processes(config), kind="pytest")
    except slots.SlotError as error:
        raise pytest.UsageError(str(error)) from None
    # pytest closes the cleanup stack even when a later hook refuses the run before the session configures.
    config.add_cleanup(lambda: _release_test_slots(config))
    setattr(config, _SLOTS_ATTR, hold)
    setattr(config, _SLOTS_PRIOR_MARKER_ATTR, os.environ.get(slots.HOLDER_ENV))
    # Workers and nested runs inherit the marker and run inside these slots instead of queueing.
    os.environ.update(hold.environment())
    _limit_workers(config, hold.count)
    if hold.waited >= 1.0:
        print(f"TEST SLOTS: holding {hold.count} of {hold.pool_size} slot(s) after {hold.waited:.1f}s", flush=True)


def _release_test_slots(config: pytest.Config) -> None:
    """Give back what this session took: its slots, its holder marker and the auto-worker count it set.

    A ``config.add_cleanup`` callback, so it also runs when a hook refuses the run before it configures.
    """
    recorded = getattr(config, _AUTO_PRIOR_ATTR, None)
    if recorded is not None:
        setattr(config, _AUTO_PRIOR_ATTR, None)
        name, prior = recorded
        if prior is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = prior
    hold = getattr(config, _SLOTS_ATTR, None)
    if hold is None:
        return
    setattr(config, _SLOTS_ATTR, None)
    holder_env = _test_slots().HOLDER_ENV
    prior = getattr(config, _SLOTS_PRIOR_MARKER_ATTR, None)
    if prior is None:
        os.environ.pop(holder_env, None)
    else:
        os.environ[holder_env] = prior
    hold.release()


def pytest_load_initial_conftests(early_config: pytest.Config, parser: pytest.Parser, args: list[str]) -> None:
    del parser, args
    _reject_oversized_tx(early_config)


@pytest.hookimpl(wrapper=True)
def pytest_cmdline_main(config: pytest.Config) -> Generator[None, object, object]:
    """Clamp before xdist, and take the full-suite lock before the session runs.

    ``pytest_cmdline_main`` runs the session and ``pytest_unconfigure`` before
    it returns, so a lock taken after ``yield`` does not cover execution.
    xdist workers already have ``workerinput`` and ``PYTEST_XDIST_WORKER`` set
    and must not take the host lock; neither does a ``--collect-only`` run.
    Test slots skip only real workers (``workerinput``): a pytest that a test
    starts inside a worker inherits ``PYTEST_XDIST_WORKER`` but is a new run,
    and it must start no more workers than the hold it runs inside.

    A new-style wrapper, so an exception raised inside the session (for
    example pytest's own ``tmp_path`` teardown ``KeyError`` after a SIGINT
    lands during a test's setup) propagates through ``yield`` unchanged. The
    old-style ``outcome.get_result()`` re-raised it from this plugin's
    teardown, and pluggy reported ``PluggyTeardownRaisedWarning`` naming
    this plugin as the culprit.
    """
    armed = not _is_xdist_worker(config) and dispatch_marker_set()
    cap_armed = armed and xdist_available()
    if cap_armed:
        _arm_maxprocesses(config)
    if armed and is_full_suite(config) and not collection_only(config):
        _acquire_for_config(config)
    if not hasattr(config, "workerinput"):
        _acquire_test_slots(config, acquire=armed)
    result = yield
    if cap_armed:
        _shrink_tx(config)
    return result


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
