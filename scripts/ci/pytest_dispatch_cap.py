"""Cap pytest-xdist fan-out for dispatch workers (#8645 part B).

SCOPE: part B guards dispatch workers against accidental xdist fan-out and
concurrent full suites. It is not a sandbox against deliberate evasion; parts
A (memory admission) and C (per-worker cgroup) are the hard limits.

When ``LEARN_UKRAINIAN_DISPATCH_TASK_ID`` is set, a worker never starts more
than two xdist processes, and a full-suite run takes one host-wide lock. A
``--collect-only`` run executes no test, so it never takes the lock (#9434).
An exact ``-m repo_wide`` selection runs the bounded invariant registry and
also skips the lock (#9670); other full-tree filters remain locked.
Legacy worker environments set ``PYTEST_PLUGINS``, and ``build_agent_env`` forwards only
``ci.pytest_dispatch_cap`` while the dispatch marker is set, so the cap still
loads when a worker copies CI's ``--override-ini addopts=-v`` and drops the
``addopts`` ``-p`` registration. Operator shells and CI leave the dispatch
variable unset. CI is unchanged. An operator shell with no live inherited
hold is refused before startup when the worker count xdist would start is
above the cap, and the error names the governed ``test_slots run`` command.

When pytest-xdist is not importable (a minimal venv with only pytest and
pyyaml, as the rules-deployment-check lane builds), the fan-out cap is a no-op:
xdist is the only thing that fans a run out, so it also owns the ``-n``/``--tx``
options this plugin clamps. The full-suite lock does not depend on xdist and
still applies.

A dispatch run also holds host test slots for its whole session (#10662): it
asks ``scripts/common/test_slots.py`` for its process count (its xdist workers
after the cap, or one), waits in the host's FIFO queue with progress lines, and
starts no more workers than the slots it holds. Each xdist worker joins those
slots and keeps them until it exits, so they stay taken when the controller is
killed while its workers still run tests (#11230). ``LU_TEST_SLOTS=off`` and a
true ``CI`` variable disable acquisition. ``LU_TEST_SLOTS=off`` also disables
acquisition and does not authorize a local run above the cap. ``--collect-only``,
``--help``, ``--version`` and ``--markers`` execute no test and take no slots.
``--fixtures`` and ``--fixtures-per-test`` take no slots when they start no
workers; when they would, they follow the same refusal and inherited clamp as
any other run. A run nested inside a live holder (``LU_TEST_SLOTS_HOLDER``)
queues for nothing, dispatch run or not, and starts at most the inherited
count of workers: ``maxprocesses``, an explicit ``--tx`` list and
``PYTEST_XDIST_AUTO_NUM_WORKERS`` are all capped before the session.
"""

from __future__ import annotations

import atexit
import fcntl
import os
from collections.abc import Generator, Mapping
from pathlib import Path
from types import ModuleType

import pytest

try:
    from scripts.common.repo_root import PRODUCT_ROOT_ENV, native_hook_roots, product_root
    from scripts.common.test_thread_caps import THREAD_CAPS
    from scripts.common.test_thread_caps import apply as apply_thread_caps
except ImportError:
    from common.repo_root import PRODUCT_ROOT_ENV, native_hook_roots, product_root  # type: ignore[no-redef]
    from common.test_thread_caps import THREAD_CAPS
    from common.test_thread_caps import apply as apply_thread_caps

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
PRODUCT_UNRESOLVED = (
    "dispatch xdist cap: no product checkout for this pytest invocation; "
    f"run pytest inside the product checkout or set {PRODUCT_ROOT_ENV} to it"
)
_LOCK_ATTR = "_lu_dispatch_full_suite_lock_fd"
_CLAMP_ATTR = "_lu_dispatch_cap_clamped"
_SLOTS_ATTR = "_lu_test_slots_hold"
_SLOTS_PRIOR_MARKER_ATTR = "_lu_test_slots_prior_marker"
_AUTO_PRIOR_ATTR = "_lu_test_slots_prior_auto_workers"
_THREAD_PRIOR_ATTR = "_lu_test_slots_prior_thread_caps"
# These execute no test and start no xdist worker, so they never queue or refuse.
_NO_TEST_OPTIONS = ("help", "version", "markers")
# ``--fixtures`` and ``--fixtures-per-test`` start workers when ``-n`` / ``--tx`` ask
# for them. A serial invocation of either still executes no test and must not queue.
_FIXTURE_OPTIONS = ("showfixtures", "show_fixtures_per_test")
_PACKAGE_NAME = Path(__file__).parents[1].name
GOVERNED_PYTEST = f".venv/bin/python -m {_PACKAGE_NAME}.common.test_slots run -- .venv/bin/python -m pytest ..."

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


def repository_root(invocation_dir: Path) -> Path:
    """Product checkout whose ``tests`` tree this plugin bounds.

    A configured ``LU_PRODUCT_ROOT`` names it. Without one, the product comes from
    pytest's ``invocation_dir`` by the shared hook-root rule, read-only and without an
    interpreter; the environment is not changed. ``pytest --rootdir`` is not the suite
    boundary, and the installed package does not walk ancestors from its own file.
    An unresolvable product raises ``pytest.UsageError``, so the cap is never waived.
    """
    try:
        if os.environ.get(PRODUCT_ROOT_ENV):
            return product_root()
        return native_hook_roots(invocation_dir)[0]
    except (OSError, ValueError):
        raise pytest.UsageError(PRODUCT_UNRESOLVED) from None


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
        root = repository_root(invocation_dir)
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


def effective_xdist_workers(config: pytest.Config) -> int:
    """Workers xdist's own ``pytest_cmdline_main`` would start. Does not change ``config``.

    Mirrors ``xdist/plugin.py`` (the installed 3.8.0 hook): ``-d`` is ``--dist=load``;
    ``auto`` / ``logical`` are 0 under ``--pdb`` and otherwise the ``pytest_xdist_auto_num_workers``
    hook; a truthy ``-n`` replaces ``--tx`` and a truthy ``--maxprocesses`` caps that ``-n`` only;
    ``-n 0`` starts no worker; a bare ``--tx`` list counts only when distribution is on.
    """
    if not xdist_available():
        return 0
    option = config.option
    numprocesses = getattr(option, "numprocesses", None)
    dist = "load" if getattr(option, "distload", False) else getattr(option, "dist", "no")
    if numprocesses in ("auto", "logical"):
        if bool(config.getoption("usepdb", False)):
            numprocesses = 0
        else:
            numprocesses = config.hook.pytest_xdist_auto_num_workers(config=config)
    if numprocesses:
        count = int(numprocesses)
        maxprocesses = getattr(option, "maxprocesses", None)
        if maxprocesses:
            count = min(count, int(maxprocesses))
        return count
    if numprocesses == 0:
        return 0
    if dist == "no":
        return 0
    specs = list(getattr(option, "tx", None) or [])
    return tx_spec_worker_count(specs) if specs else 0


def _fanout_refusal(count: int, *, slots_off: bool) -> str:
    """Usage error for an ungoverned local run above :data:`MAX_PROCESSES`."""
    message = (
        f"pytest worker cap: this run would start {count} xdist workers and the cap is {MAX_PROCESSES}. "
        "An ungoverned local pytest cannot exceed it. "
        f"Run it under the governor: {GOVERNED_PYTEST}"
    )
    if slots_off:
        message += (
            " LU_TEST_SLOTS=off disables acquisition and does not authorize a larger fan-out; "
            "that command does not raise this cap while off is set."
        )
    return message


def _ci_true(slots: ModuleType) -> bool:
    """True when ``CI`` is set the way :func:`scripts.common.test_slots.enabled` reads a true value."""
    return os.environ.get("CI", "").strip().lower() in slots._TRUE


def _slots_explicitly_off(slots: ModuleType) -> bool:
    return os.environ.get(slots.ENABLE_ENV, "").strip().lower() in slots._FALSE


def _informational(config: pytest.Config) -> bool:
    if collection_only(config):
        return True
    return any(getattr(config.option, name, False) for name in _NO_TEST_OPTIONS)


def _shows_fixtures(config: pytest.Config) -> bool:
    return any(getattr(config.option, name, False) for name in _FIXTURE_OPTIONS)


def _option_requests_workers(config: pytest.Config) -> bool:
    """Whether the raw options ask xdist to start at least one worker, before the auto hook runs."""
    if not xdist_available():
        return False
    option = config.option
    numprocesses = getattr(option, "numprocesses", None)
    if numprocesses in ("auto", "logical"):
        return not bool(config.getoption("usepdb", False))
    if isinstance(numprocesses, int):
        return numprocesses > 0
    dist = "load" if getattr(option, "distload", False) else getattr(option, "dist", "no")
    specs = list(getattr(option, "tx", None) or [])
    return dist != "no" and bool(specs) and tx_spec_worker_count(specs) > 0


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


def _cap_threads(config: pytest.Config) -> None:
    """Limit threads for this session, retaining the caller's environment for cleanup."""
    setattr(config, _THREAD_PRIOR_ATTR, {name: os.environ.get(name) for name in THREAD_CAPS})
    os.environ.update(apply_thread_caps(os.environ))


def _keep_hold(config: pytest.Config, hold: object) -> None:
    """Keep ``hold`` for this session; its variables reach workers and nested runs and are restored after it."""
    environment = hold.environment()  # type: ignore[attr-defined]
    setattr(config, _SLOTS_ATTR, hold)
    setattr(config, _SLOTS_PRIOR_MARKER_ATTR, {name: os.environ.get(name) for name in environment})
    os.environ.update(environment)


def _run_inside_inherited_hold(config: pytest.Config, slots: ModuleType, hold: object) -> None:
    """Start at most the slots a live ancestor holds, here and in this run's descendants.

    A review hold's turn (its session lock) is this session's until it ends, so the review's runs never overlap.
    """
    config.add_cleanup(lambda: _release_test_slots(config))
    _keep_hold(config, hold)
    count = hold.count  # type: ignore[attr-defined]
    _limit_workers(config, count)
    name = slots.XDIST_AUTO_ENV
    auto_cap = slots.auto_worker_cap()  # a lower existing cap, such as a driver scope's, is kept
    setattr(config, _AUTO_PRIOR_ATTR, (name, os.environ.get(name)))
    os.environ[name] = str(count if auto_cap is None else min(auto_cap, count))
    _cap_threads(config)


def _acquire_test_slots(config: pytest.Config, *, acquire: bool) -> None:
    """Start no more xdist workers than the host test slots this session runs inside.

    A live ancestor hold bounds every run below it, dispatch run or not: the run queues for nothing and starts
    at most the inherited count of workers. Otherwise only a dispatch run (``acquire``) waits for and holds
    slots of its own. A marker without a live holder is ignored, so a dispatch run under it still queues.

    An ungoverned local run whose effective worker count is above :data:`MAX_PROCESSES` is refused here,
    before xdist builds its worker list. Dispatch runs are already clamped and are not refused. A true ``CI``
    variable is not refused. ``LU_TEST_SLOTS=off`` does not authorize the over-cap count. A run at or under
    the cap with no holder does not consult the governor, so an invalid setting stays unevaluated there.
    ``join_inherited`` runs at most once and that result both admits the hold and clamps the workers.
    """
    if _informational(config):
        return
    if _shows_fixtures(config) and not _option_requests_workers(config):
        return  # serial --fixtures executes no test and must not queue
    slots = _test_slots()
    holder_set = bool(os.environ.get(slots.HOLDER_ENV, "").strip())
    counted: int | None = None

    def worker_count() -> int:
        nonlocal counted
        if counted is None:
            counted = effective_xdist_workers(config)
        return counted

    # Within the cap and nothing to inherit or acquire: do not read slot settings.
    if not acquire and not holder_set and worker_count() <= MAX_PROCESSES:
        return
    try:
        if not slots.enabled():
            if worker_count() > MAX_PROCESSES and not _ci_true(slots) and _slots_explicitly_off(slots):
                raise pytest.UsageError(_fanout_refusal(worker_count(), slots_off=True))
            return
        inherited = slots.join_inherited()
        if inherited is not None:
            _run_inside_inherited_hold(config, slots, inherited)
            return
        # ``--fixtures`` under a dispatch marker already has the dispatch clamp and still takes no slots.
        if not acquire or _shows_fixtures(config):
            if not acquire and worker_count() > MAX_PROCESSES and not _ci_true(slots):
                raise pytest.UsageError(_fanout_refusal(worker_count(), slots_off=False))
            return
        hold = slots.acquire(requested_test_processes(config), kind="pytest")
    except slots.SlotError as error:
        raise pytest.UsageError(str(error)) from None
    # pytest closes the cleanup stack even when a later hook refuses the run before the session configures.
    config.add_cleanup(lambda: _release_test_slots(config))
    # Workers and nested runs inherit the marker and run inside these slots instead of queueing.
    _keep_hold(config, hold)
    _cap_threads(config)
    _limit_workers(config, hold.count)
    if hold.waited >= 1.0:
        print(f"TEST SLOTS: holding {hold.count} of {hold.pool_size} slot(s) after {hold.waited:.1f}s", flush=True)


def _join_as_worker(config: pytest.Config) -> None:
    """Keep the controller's slots taken while this xdist worker runs, even when the controller is killed first.

    xdist closes inherited descriptors when it starts a worker, so the worker joins the hold itself. A worker its
    run's live hold names (the checked marker, and for a review its turn token) that cannot keep the hold's slots
    is refused before its session, typed: run on no slot, it would keep running tests after a killed controller
    freed them. xdist reports the refusal as the worker going down, and the controller's run fails. A worker no
    live hold names runs as before.
    """
    slots = _test_slots()
    if not os.environ.get(slots.HOLDER_ENV, "").strip() or not slots.enabled():
        return
    try:
        hold = slots.join_as_worker()
    except slots.SlotError as error:
        raise pytest.UsageError(str(error)) from None
    if hold is not None:
        config.add_cleanup(hold.release)


def _release_test_slots(config: pytest.Config) -> None:
    """Release this session's slots and restore its holder, worker-count and thread-cap environment.

    A ``config.add_cleanup`` callback, so it also runs when a hook refuses the run before it configures.
    """
    thread_prior = getattr(config, _THREAD_PRIOR_ATTR, None)
    if thread_prior is not None:
        setattr(config, _THREAD_PRIOR_ATTR, None)
        for name, prior in thread_prior.items():
            if prior is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = prior
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
    for name, prior in (getattr(config, _SLOTS_PRIOR_MARKER_ATTR, None) or {}).items():
        if prior is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = prior
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
    A real worker (``workerinput``) joins the slots its controller holds and
    keeps them until it exits, so killing the controller frees nothing early.
    A pytest that a test starts inside a worker inherits ``PYTEST_XDIST_WORKER``
    but is a new run, and it must start no more workers than the hold it runs inside.

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
    if hasattr(config, "workerinput"):
        _join_as_worker(config)
    else:
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
