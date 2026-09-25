"""
Pytest configuration and shared fixtures for audit tests.

Provides reusable content snippets and module templates for testing.
"""

import ast
import contextlib
import functools
import ipaddress
import itertools
import os
import shutil
import socket
import sqlite3
import subprocess
import sys
import threading
import weakref
from collections.abc import Collection, Generator
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.common.bridge_paths import configured_bridge_db_path, default_bridge_db_path
from scripts.common.repo_root import resolve_repo_root
from tests import sparse_trees

_REPO_ROOT = Path(__file__).resolve().parents[1]

# Identity a launched agent session carries (#8778). A test that inherits it
# keys hook dedupe, leases, and telemetry on the operator's live session.
# tests/test_session_identity_env_isolation.py parses the export sites and
# fails when a launcher or runtime exports a name missing here.
SESSION_IDENTITY_ENV_VARS = (
    # Launcher driver identity (scripts/lib/launcher_core.sh).
    "SESSION_EPIC",
    "SESSION_HANDOFF_AGENT",
    # Stream lease capsule (scripts/lib/session_supervisor.sh).
    "SESSION_STREAM_ID",
    "SESSION_STREAM_SESSION_ID",
    "SESSION_STREAM_LEASE_ID",
    "SESSION_STREAM_GENERATION",
    "SESSION_STREAM_FENCING_TOKEN",
    "SESSION_STREAM_AGENT",
    "SESSION_STREAM_HARNESS",
    "SESSION_STREAM_INSTANCE_ID",
    "SESSION_STREAM_PROCESS_ID",
    "SESSION_STREAM_HEARTBEAT_AT",
    "SESSION_STREAM_EXPIRES_AT",
    "SESSION_STREAM_TTL_SECONDS",
    "SESSION_STREAM_VERSION",
    "SESSION_STREAM_TASK_ID",
    "SESSION_SUPERVISOR_CAPSULE_PATH",
    "SESSION_SUPERVISOR_WAKE_DELIVERY",
    "SESSION_SUPERVISOR_WAKE_STREAM",
    # Codex launcher and thread rollover (scripts/launchers/codex.sh,
    # scripts/lib/thread_rollover_link.sh).
    "CODEX_SESSION",
    "CODEX_LAUNCHER_ROLLOVER_AGENT",
    "CODEX_LAUNCHER_ROLLOVER_LINEAGE_ID",
    "CODEX_LAUNCHER_ROLLOVER_ID",
    # Resolved context profile (scripts/lib/profile_resolver.sh and the
    # glmcc/kimicc route libraries).
    "LEARN_UKRAINIAN_PROFILE_ID",
    "LEARN_UKRAINIAN_TRANSPORT",
    "LEARN_UKRAINIAN_MAIN_MODEL_ID",
    "LEARN_UKRAINIAN_MAIN_CONTEXT_WINDOW_TOKENS",
    "LEARN_UKRAINIAN_AUTO_COMPACT_CAPACITY_TOKENS",
    "LEARN_UKRAINIAN_COLD_START_PROFILE",
    "LEARN_UKRAINIAN_COLD_START_BUDGET_TOKENS",
    "LEARN_UKRAINIAN_ROLLOVER_WARNING_PERCENTAGES",
    "LEARN_UKRAINIAN_REQUESTED_PROFILE_ID",
    "LEARN_UKRAINIAN_REQUESTED_MODEL_ID",
    "LEARN_UKRAINIAN_RESOLUTION_REASON",
    "LEARN_UKRAINIAN_TRUSTED",
    "LEARN_UKRAINIAN_MODEL_MISMATCH",
    "LEARN_UKRAINIAN_EXPECTED_PROFILE_ID",
    "LEARN_UKRAINIAN_EXPECTED_MAIN_MODEL_ID",
    "LEARN_UKRAINIAN_EXPECTED_MAIN_CONTEXT_WINDOW_TOKENS",
    "LEARN_UKRAINIAN_KIMICC_MANAGED_LAUNCH",
    # Claudex supervisor child launch (scripts/orchestration/claudex_supervisor.py);
    # rollover and SessionStart bind to the supervisor run through these.
    "LEARN_UKRAINIAN_CLAUDEX_MANAGED_LAUNCH",
    "LEARN_UKRAINIAN_CLAUDEX_RUN_ID",
    "LEARN_UKRAINIAN_CLAUDEX_LAUNCH_GENERATION",
    # SessionStart runtime (scripts/lib/session_record.py, session-setup.sh).
    "LEARN_UKRAINIAN_SESSION_ID",
    "LEARN_UKRAINIAN_SESSION_RECORD",
    "LEARN_UKRAINIAN_TRANSCRIPT_PATH",
    "LEARN_UKRAINIAN_OBSERVED_MODEL_ID",
    "LEARN_UKRAINIAN_OBSERVED_CONTEXT_WINDOW_TOKENS",
    "LEARN_UKRAINIAN_THREAD_LEASE_GENERATION",
    # Dispatch worker identity (scripts/delegate.py ``_build_worker_env``).
    "LEARN_UKRAINIAN_DISPATCH_TASK_ID",
    "LEARN_UKRAINIAN_DISPATCH_AGENT",
    "LU_X_AGENT_TRAILER",
    "LU_RUNTIME_INITIATOR",
    "LU_RUNTIME_INITIATOR_SOURCE",
    "LU_RUNTIME_RUN_NONCE",
    # Telemetry run/session ids (scripts/telemetry/emit.py).
    "LU_RUN_ID",
    "LU_SESSION_ID",
    # Codex hook probe session (scripts/agent_runtime/codex_hook_probe.py).
    "CODEX_HOOK_PROBE_LOG",
    "CODEX_HOOK_PROBE_DENY_TOOLS",
    # Harness-native ids the hooks read; the harness, not a launcher, sets them.
    "LEARN_UK_HOOK_SESSION_ID",
    "CODEX_THREAD_ID",
    "CODEX_SESSION_ID",
    "CLAUDE_CODE_SESSION_ID",
    # SessionStart env file; a leaked path lets a test append to the live session.
    "CLAUDE_ENV_FILE",
)


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtest_protocol(item: pytest.Item, nextitem: pytest.Item | None) -> Generator[None, object, object]:
    """Run every test without the launching agent session's identity (#8778).

    The outermost wrapper around setup, call, and teardown, so no fixture of
    any scope sees the identity. Tests that need a variable set it themselves;
    the original environment returns after teardown.
    """
    with pytest.MonkeyPatch.context() as patch:
        for name in SESSION_IDENTITY_ENV_VARS:
            patch.delenv(name, raising=False)
        return (yield)


def _is_agent_runtime_shim(path: str | os.PathLike[str]) -> bool:
    parts = Path(path).parts
    return len(parts) >= 3 and parts[-3:-1] == ("agent_runtime", "shims")


def _resolve_real_gh_binary() -> str | None:
    """Resolve gh behind agent-runtime shims using the runner's path rules."""
    candidates = [os.environ.get("AGENT_REAL_GH")]
    search_path = os.environ.get("AGENT_ORIGINAL_PATH", os.environ.get("PATH", os.defpath))
    candidates.extend(
        os.path.join(entry, "gh")
        for entry in search_path.split(os.pathsep)
        if entry
    )
    for candidate in candidates:
        if not candidate or _is_agent_runtime_shim(candidate):
            continue
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return os.path.realpath(candidate)
    return None


_REAL_GH_BINARY = _resolve_real_gh_binary()
_LIVE_GITHUB_ALLOWED = False


@pytest.fixture(autouse=True)
def _live_github_spawn_policy(request: pytest.FixtureRequest) -> Generator[None, None, None]:
    """Permit real ``gh`` only for tests explicitly marked as integrations."""
    global _LIVE_GITHUB_ALLOWED
    previous = _LIVE_GITHUB_ALLOWED
    _LIVE_GITHUB_ALLOWED = request.node.get_closest_marker("live_github") is not None
    try:
        yield
    finally:
        _LIVE_GITHUB_ALLOWED = previous


@pytest.fixture(autouse=True)
def _default_fake_github_cli(
    _fake_github_bin: Path,
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
) -> None:
    """Resolve ordinary test GitHub CLI lookups to a failing local stub."""
    if request.node.get_closest_marker("live_github") is not None:
        return
    # An empty PATH entry means "the current directory". Drop unset, empty,
    # and blank inherited entries so the stub is prepended without putting
    # cwd on PATH.
    inherited = [entry for entry in os.environ.get("PATH", "").split(os.pathsep) if entry]
    monkeypatch.setenv("PATH", os.pathsep.join([os.fspath(_fake_github_bin), *inherited]))


@pytest.fixture(scope="session")
def _fake_github_bin(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """One failing local gh binary shared by tests in this pytest session."""
    fake_bin = tmp_path_factory.mktemp("fake-gh")
    fake_gh = fake_bin / "gh"
    fake_gh.write_text(
        "#!/bin/sh\nprintf '%s\\n' 'gh stub: inject a test response instead of contacting GitHub' >&2\nexit 127\n",
        encoding="utf-8",
    )
    fake_gh.chmod(0o755)
    return fake_bin


def _bridge_db_paths() -> tuple[Path, Path]:
    """Return the primary bridge DB and any configured path before tests begin."""
    primary_repo_root = resolve_repo_root(Path(__file__), 1)
    return (
        default_bridge_db_path(primary_repo_root).resolve(),
        configured_bridge_db_path(primary_repo_root).resolve(),
    )


_REAL_BRIDGE_DB_PATH, _CONFIGURED_BRIDGE_DB_PATH = _bridge_db_paths()
_API_BRIDGE_DB_PATH = default_bridge_db_path(_REPO_ROOT).resolve()
_UNISOLATED_BRIDGE_DB_PATHS = frozenset(
    {_REAL_BRIDGE_DB_PATH, _CONFIGURED_BRIDGE_DB_PATH, _API_BRIDGE_DB_PATH}
)
_BRIDGE_DB_SUFFIXES = tuple(sorted({path.name for path in _UNISOLATED_BRIDGE_DB_PATHS}))
_BRIDGE_DB_BINDINGS_TO_REPLACE = set(_UNISOLATED_BRIDGE_DB_PATHS)


def _sqlite_database_path(database: object) -> tuple[Path | None, bool]:
    """Return a SQLite path and whether a URI explicitly opens it read-only.

    ``bytes`` and ``os.PathLike`` objects whose ``__fspath__`` returns bytes are
    paths. Decode them before the ``file:`` check so the guard does not raise
    ``TypeError`` or treat a raw bytes path as "not a path".
    """
    if not isinstance(database, (str, bytes, os.PathLike)):
        return None, False
    raw_path = os.fsdecode(os.fspath(database))
    if raw_path.startswith("file:"):
        parsed = urlsplit(raw_path)
        query = parse_qs(parsed.query)
        return Path(unquote(parsed.path)).resolve(), query.get("mode") == ["ro"]
    return Path(raw_path).resolve(), False


@pytest.fixture(autouse=True)
def isolated_bridge_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect imported and future bridge users to one per-test database."""
    isolated_path = tmp_path / "messages.db"
    monkeypatch.setenv("AB_DB_PATH", str(isolated_path))
    # A module first imported during a prior test may retain that test's path.
    # Carry those paths forward so each test gets its own DB under xdist too.
    _BRIDGE_DB_BINDINGS_TO_REPLACE.add(isolated_path.resolve())
    for name, module in tuple(sys.modules.items()):
        if module is None or not name.startswith(("scripts.", "ai_agent_bridge", "agent_runtime.")):
            continue
        for attribute, value in tuple(vars(module).items()):
            if not isinstance(value, (str, os.PathLike)) or not os.fspath(value).endswith(_BRIDGE_DB_SUFFIXES):
                continue
            if Path(value).resolve() in _BRIDGE_DB_BINDINGS_TO_REPLACE:
                monkeypatch.setattr(module, attribute, isolated_path)

    # The production API app has a context and store handles created at import.
    # Rebuild both against the isolated path, preserving other configured roots.
    api_main = sys.modules.get("scripts.api.main")
    if api_main is not None:
        app = vars(api_main).get("app")
        context = getattr(getattr(app, "state", None), "ctx", None)
        if context is not None and context.roots.message_db_path.resolve() in _BRIDGE_DB_BINDINGS_TO_REPLACE:
            monkeypatch.setattr(app.state, "ctx", context.with_roots(message_db_path=isolated_path))
    return isolated_path


@pytest.fixture(autouse=True)
def _guard_real_bridge_db_writes(monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest):
    """Fail the test that tries to open the live bridge DB with write access."""
    original_connect = sqlite3.connect

    def guarded_connect(database, *args, **kwargs):
        path, read_only = _sqlite_database_path(database)
        if path in _UNISOLATED_BRIDGE_DB_PATHS and not read_only:
            pytest.fail(
                f"{request.node.nodeid} attempted a writable connection to the real bridge DB "
                f"at {path}; isolate it with AB_DB_PATH or a DB_PATH fixture",
                pytrace=False,
            )
        return original_connect(database, *args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", guarded_connect)


def _pytest_tmp_size(root: Path, stop_after_bytes: int | None = None) -> tuple[int, bool]:
    """Return the size of a tree without following symlinks.

    When a budget is supplied, stop as soon as the measured size exceeds it.
    The boolean reports that the walk stopped early, so callers do not present
    a lower bound as an exact size.
    """
    size = 0
    pending = [root]
    while pending:
        directory = pending.pop()
        try:
            entries_context = os.scandir(directory)
        except (FileNotFoundError, PermissionError):
            # A temp directory may disappear or become unreadable during teardown.
            continue
        with entries_context as entries:
            for entry in entries:
                try:
                    if entry.is_dir(follow_symlinks=False):
                        pending.append(Path(entry.path))
                    else:
                        file_stat = entry.stat(follow_symlinks=False)
                        size += getattr(file_stat, "st_blocks", 0) * 512 or file_stat.st_size
                except FileNotFoundError:
                    # A test may have removed a temp file while the walk ran.
                    continue
                if stop_after_bytes is not None and size > stop_after_bytes:
                    return size, True
    return size, False


# =============================================================================
# CONTENT-TREE POLLUTION GUARD (#8631)
# =============================================================================
# A test that drives a build/promote writer against the real repo root leaves
# files under ``curriculum/`` (e.g. ``a1/my-morning/wiki_completeness_gate.json``).
# That makes the checkout dirty, and ``curriculum/`` changes read as content
# drift. The controller snapshots ``git status`` for the content trees at
# session start and fails the session if it differs at session end.

_CONTENT_TREE_PATHSPECS = ("curriculum/", "site/src/content/")
_CONTENT_TREE_GIT_TIMEOUT_S = 60
_CONTENT_TREE_SNAPSHOT_KEY = "_content_tree_snapshot"


def _content_tree_snapshot(root: Path) -> frozenset[str] | None:
    """``git status --porcelain`` lines for the content trees, or None outside git."""
    git_args = ["git", "-C", str(root)]
    try:
        top = subprocess.run(
            [*git_args, "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=_CONTENT_TREE_GIT_TIMEOUT_S,
            check=False,
        )
        if top.returncode != 0 or Path(top.stdout.strip()).resolve() != root.resolve():
            return None
        status = subprocess.run(
            [*git_args, "status", "--porcelain", "--untracked-files=all", "--", *_CONTENT_TREE_PATHSPECS],
            capture_output=True,
            text=True,
            timeout=_CONTENT_TREE_GIT_TIMEOUT_S,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if status.returncode != 0:
        return None
    return frozenset(line for line in status.stdout.splitlines() if line.strip())


def _content_tree_changes(
    before: frozenset[str] | None, after: frozenset[str] | None
) -> tuple[list[str], list[str]]:
    """Sorted ``(added, removed)`` status lines between two snapshots.

    Both directions count: deleting a pre-existing untracked file or restoring a
    pre-existing tracked modification changes the tree just as much as a new file.
    """
    if before is None or after is None:
        return [], []
    return sorted(after - before), sorted(before - after)


def pytest_sessionstart(session: pytest.Session) -> None:
    config = session.config
    if hasattr(config, "workerinput"):
        return
    setattr(config, _CONTENT_TREE_SNAPSHOT_KEY, _content_tree_snapshot(_REPO_ROOT))


def _enforce_content_tree_clean(session: pytest.Session) -> None:
    before = getattr(session.config, _CONTENT_TREE_SNAPSHOT_KEY, None)
    added, removed = _content_tree_changes(before, _content_tree_snapshot(_REPO_ROOT))
    if not added and not removed:
        return
    print(
        "content-tree guard: git status under "
        f"{', '.join(_CONTENT_TREE_PATHSPECS)} changed during the test session. "
        "Either a test wrote to (or removed files from) the real checkout — point its "
        "writer at tmp_path — or another process in the same checkout, such as an "
        "operator build, wrote concurrently:"
    )
    for label, lines in (("added", added), ("removed", removed)):
        if lines:
            print(f"  status entries {label} since session start:")
            for line in lines:
                print(f"    {line}")
    if session.exitstatus == pytest.ExitCode.OK:
        session.exitstatus = pytest.ExitCode.TESTS_FAILED


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Report this session's temp usage and optionally enforce a CI budget."""
    config = session.config
    if hasattr(config, "workerinput"):
        return
    _enforce_content_tree_clean(session)

    tmp_path_factory = getattr(config, "_tmp_path_factory", None)
    if tmp_path_factory is None:
        return
    if getattr(tmp_path_factory, "_basetemp", None) is None:
        return
    basetemp = tmp_path_factory.getbasetemp()
    budget_value = os.environ.get("LU_PYTEST_TMP_BUDGET_GB")
    if budget_value is not None and not budget_value.strip():
        budget_value = None
    budget_bytes: int | None = None
    if budget_value is not None:
        try:
            budget_gb = float(budget_value)
            if not (budget_gb >= 0 and budget_gb < float("inf")):
                raise ValueError
            budget_bytes = int(budget_gb * 1024**3)
        except ValueError:
            print(f"pytest-tmp: invalid LU_PYTEST_TMP_BUDGET_GB={budget_value!r}")
            session.exitstatus = pytest.ExitCode.TESTS_FAILED
            return

    try:
        size, stopped_early = _pytest_tmp_size(basetemp, budget_bytes)
    except OSError as error:
        print(f"pytest-tmp: unable to measure {basetemp}: {error}")
        session.exitstatus = pytest.ExitCode.TESTS_FAILED
        return

    size_gb = size / 1024**3
    reported_size = f"at least {size:,} bytes (walk stopped at budget)" if stopped_early else f"{size_gb:.2f} GB"
    print(f"pytest-tmp: {reported_size} in {basetemp}")
    if budget_bytes is not None and size > budget_bytes:
        print(
            f"pytest-tmp: session temp size exceeded LU_PYTEST_TMP_BUDGET_GB={budget_value} "
            f"({budget_bytes / 1024**3:.2f} GB)"
        )
        session.exitstatus = pytest.ExitCode.TESTS_FAILED


# =============================================================================
# CI FILE-PLANE SHARD ALLOWLIST (ci-shard-balance-2026-09-07)
# =============================================================================
# GitHub Actions collects through one initial `tests` path instead of ~337
# positional file arguments per shard (1,345 test files total on the baseline
# head; collection cost, not test selection); this hook
# narrows that single-path collection back down to one shard's files. See
# scripts/ci/pytest_shards.py `plan-files` and docs/runbooks/ci-gate.md.

LU_PYTEST_SHARD_FILES_ENV_VAR = "LU_PYTEST_SHARD_FILES"


@functools.lru_cache(maxsize=1)
def _load_shard_allowlist() -> frozenset[str] | None:
    """Load this shard's file allowlist once per session.

    Unset ``LU_PYTEST_SHARD_FILES``: returns ``None`` and every caller treats
    that as "don't filter" — local/default collection is byte-for-byte
    unchanged. Set: the file must exist, be readable, and contain at least
    one non-blank, non-duplicate ``.../test_*.py`` line — anything else is a
    loud failure raised here at first collection, never a silent full run
    (allowlist ignored) or silent empty run (everything ignored).
    """
    allowlist_path_str = os.environ.get(LU_PYTEST_SHARD_FILES_ENV_VAR)
    if not allowlist_path_str:
        return None
    allowlist_path = Path(allowlist_path_str)
    try:
        text = allowlist_path.read_text(encoding="utf-8")
    except OSError as error:
        raise RuntimeError(
            f"{LU_PYTEST_SHARD_FILES_ENV_VAR}={allowlist_path_str!r} is set but unreadable: {error}"
        ) from error
    entries = [line.strip() for line in text.splitlines() if line.strip()]
    if not entries:
        raise RuntimeError(f"{LU_PYTEST_SHARD_FILES_ENV_VAR}={allowlist_path_str!r} is empty")
    if len(set(entries)) != len(entries):
        raise RuntimeError(f"{LU_PYTEST_SHARD_FILES_ENV_VAR}={allowlist_path_str!r} contains a duplicate entry")
    for entry in entries:
        if not entry.endswith(".py") or not Path(entry).name.startswith("test_"):
            raise RuntimeError(
                f"{LU_PYTEST_SHARD_FILES_ENV_VAR}={allowlist_path_str!r} has a malformed entry: {entry!r}"
            )
    return frozenset(entries)


def pytest_ignore_collect(collection_path: Path, config: pytest.Config) -> bool | None:
    """Ignore test files this shard's allowlist doesn't include.

    Explicitly admit directories so pytest's default ``norecursedirs``
    (including ``build``) cannot hide an allowed file. Inactive local
    collection still defers to pytest's normal traversal rules.
    """
    allowlist = _load_shard_allowlist()
    if allowlist is None:
        return None
    if collection_path.is_dir():
        return False
    try:
        relative = collection_path.resolve().relative_to(_REPO_ROOT).as_posix()
    except ValueError:
        return True
    return relative not in allowlist


def _get_breadcrumb_file() -> Path | None:
    breadcrumb_dir_str = os.environ.get("PYTEST_BREADCRUMB_DIR", ".pytest_breadcrumbs")
    if not breadcrumb_dir_str:
        return None
    dir_path = Path(breadcrumb_dir_str)
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
    except OSError:
        return None
    worker_id = os.environ.get("PYTEST_XDIST_WORKER", "master")
    return dir_path / f"breadcrumb_{worker_id}.txt"


def _append_breadcrumb(line: str) -> None:
    try:
        breadcrumb_file = _get_breadcrumb_file()
        if breadcrumb_file:
            with open(breadcrumb_file, "a", encoding="utf-8") as f:
                f.write(line)
                f.flush()
                with contextlib.suppress(OSError):
                    os.fsync(f.fileno())
    except OSError:
        pass


def pytest_runtest_logstart(nodeid: str, location: tuple[str, int | None, str]) -> None:
    _append_breadcrumb(f"START {nodeid}\n")


def pytest_runtest_logfinish(nodeid: str, location: tuple[str, int | None, str]) -> None:
    _append_breadcrumb(f"FINISH {nodeid}\n")


def _require_data_artifact(
    relative_path: str,
    *,
    required_sqlite_tables: Collection[str] = (),
) -> Path:
    """Return a local data artifact or skip tests that cannot run without it."""
    data_root = Path(os.environ.get("LEARN_UKRAINIAN_TEST_DATA_ROOT", _REPO_ROOT))
    artifact = data_root / relative_path
    if not artifact.is_file():
        try:
            from scripts.guardrails.worktree_containment import resolve_main_root

            fallback = resolve_main_root(_REPO_ROOT) / relative_path
            if fallback.is_file():
                artifact = fallback
        except Exception:
            pass
    if not artifact.is_file():
        pytest.skip(f"requires {relative_path} (not provisioned in CI)")

    if required_sqlite_tables:
        try:
            with sqlite3.connect(f"file:{artifact}?mode=ro", uri=True) as connection:
                available_tables = {
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type IN ('table', 'view')"
                    )
                }
        except sqlite3.Error:
            available_tables = set()
        missing_tables = sorted(set(required_sqlite_tables) - available_tables)
        if missing_tables:
            pytest.skip(
                f"requires {relative_path} with SQLite tables: {', '.join(missing_tables)} (not provisioned in CI)"
            )
    return artifact


@pytest.fixture
def requires_sources_db() -> Path:
    """Skip a test requiring the complete uncommitted sources corpus database."""
    return _require_data_artifact(
        "data/sources.db",
        required_sqlite_tables=(
            "external_articles",
            "external_fts",
            "literary_fts",
            "literary_texts",
            "textbook_sections",
            "textbooks",
            "textbooks_fts",
            "ukrainian_wiki",
            "ukrainian_wiki_fts",
            "wikipedia",
            "wikipedia_fts",
        ),
    )


@pytest.fixture
def requires_vesum_db() -> Path:
    """Skip a test requiring the uncommitted VESUM database."""
    return _require_data_artifact("data/vesum.db", required_sqlite_tables=("forms",))


@pytest.fixture
def requires_literary_wave12_jsonl() -> Path:
    """Skip a test requiring the uncommitted Wave 12 literary corpus fixture."""
    return _require_data_artifact("data/literary_texts/wave12-krupnytsky-orlyk-biohrafiia.jsonl")


@pytest.fixture(autouse=True)
def _isolate_llm_qg_runtime_stores(tmp_path, monkeypatch):
    """Every test writes llm_qg runtime state (DB + circuit sidecar) to tmp_path.

    Root cause (2026-07-07): llm_qg_store resolves its stores via env-var-or-
    PROJECT_ROOT-default; tests exercising qg_workflow/store paths without
    overriding the env minted data/telemetry/llm_qg_live_circuit.json in every
    checkout/worktree they ran in — one such stray got swept into PR #4743 by
    git add -A. Hermetic by default; tests that need a specific path still
    monkeypatch their own.
    """
    monkeypatch.setenv("LEARN_UKRAINIAN_LLM_QG_DB", str(tmp_path / "llm_qg.db"))
    monkeypatch.setenv(
        "LEARN_UKRAINIAN_LLM_QG_CIRCUIT", str(tmp_path / "llm_qg_live_circuit.json")
    )


@pytest.fixture(autouse=True)
def _isolate_overview_last_good(tmp_path, monkeypatch):
    """Keep overview last-good on a per-test tmp path (#7024).

    The durable snapshot lives under ``.cache/`` in production so a Monitor
    bounce can reload it. Tests must not read or overwrite that host file,
    and in-memory last-good must not leak across cases.
    """
    import sys

    monkeypatch.setenv(
        "DASHBOARD_OVERVIEW_LAST_GOOD_PATH",
        str(tmp_path / "dashboard_overview_last_good.json"),
    )
    router = sys.modules.get("scripts.api.dashboard_router")
    if router is not None:
        router.reset_overview_state_for_tests()
    yield
    router = sys.modules.get("scripts.api.dashboard_router")
    if router is not None:
        router.reset_overview_state_for_tests()


@pytest.fixture(autouse=True)
def _hermetic_dispatch_admission_host(monkeypatch):
    """Dispatch admission sees a healthy host and config-default thresholds (#8645).

    Admission reads this host's MemAvailable and load average; a busy CI runner
    or developer box must not refuse the write dispatches other tests make.
    Admission tests monkeypatch ``probe_host`` themselves. Imported lazily and
    skipped when unavailable, so conftest still loads in a minimal venv (#8689).
    """
    try:
        from scripts.orchestration import dispatch_admission
    except ImportError:
        return

    for name in (
        dispatch_admission.ENV_MAX_LIVE_WRITE_WORKERS,
        dispatch_admission.ENV_MIN_MEM_AVAILABLE_GIB,
        dispatch_admission.ENV_MAX_LOAD_PER_CPU,
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(
        dispatch_admission,
        "probe_host",
        lambda *_args, **_kwargs: dispatch_admission.HostProbe(
            mem_available_bytes=64 * 1024**3, load1=0.0, cpu_count=8, proc_available=True
        ),
    )


# One numbered directory per process. ``mktemp`` lists the base to pick the
# next number, so a per-test call is quadratic over a long session (#8654).
_WRITE_OWNERSHIP_SEQ = itertools.count()


@pytest.fixture(scope="session")
def _write_ownership_base(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """One base directory for every per-test ownership ledger in this process."""
    return tmp_path_factory.mktemp("write-ownership-stores")


@pytest.fixture(autouse=True)
def _isolate_write_ownership_ledger(_write_ownership_base: Path, monkeypatch):
    """Every test gets its own write-path ownership ledger.

    Root cause (2026-07-25): the ledger path was a module constant baked into
    default arguments, so the suite admitted against the LIVE fleet ledger in
    batch_state/. Dispatch tests then saw whatever real dispatches happened to
    be running: eight of them failed on a busy machine and passed on an idle
    one, which is indistinguishable from flakiness and silently erodes the
    pre-push pytest signal. Tests that want the real ledger override this.

    The directory comes from ``tmp_path_factory``, NOT from the test's own
    ``tmp_path``: an autouse fixture that creates a subdirectory there breaks
    every test asserting its ``tmp_path`` is empty. Caught in CI by
    test_grok_envelope_failure_skips_forensics_when_unconfigured after the
    first version of this fixture did exactly that. The session base is
    numbered once; each test is ``<base>/<n>`` via ``mkdir``, not another
    ``mktemp``.
    """
    ledger_dir = _write_ownership_base / str(next(_WRITE_OWNERSHIP_SEQ))
    ledger_dir.mkdir(parents=True)
    db_file = ledger_dir / "write-ownership.sqlite3"
    conn = sqlite3.connect(db_file)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS write_claims (task_id TEXT NOT NULL, claim_json TEXT NOT NULL, pid INTEGER, created_at REAL NOT NULL, PRIMARY KEY (task_id, claim_json))"
    )
    conn.commit()
    conn.close()
    monkeypatch.setenv("LEARN_UKRAINIAN_OWNERSHIP_LEDGER", str(db_file))
    monkeypatch.setenv("LEARN_UKRAINIAN_OWNERSHIP_TASK_STATE_DIR", str(ledger_dir))


# =============================================================================
# DISPATCH TASK STORE ISOLATION (#8654)
# =============================================================================
# ``delegate._TASKS_DIR`` is a module constant. Helpers compute the record,
# result, archive, snapshot, log, and admission-lock paths from it at call
# time. Tests that forget to patch the constant write into the live store
# the Monitor API and the work board read. Sibling modules keep their own
# copy of the same directory; ``_TASK_STORE_RETARGETS`` imports each one and
# retargets it. The ownership ledger above is a different seam (env override).

_REAL_TASKS_DIR = (resolve_repo_root(Path(__file__), 1) / "batch_state" / "tasks").resolve()
# Sibling constants the autouse fixture retargets by importing each module.
# ``scripts.delegate._TASKS_DIR`` is set in ``_isolate_dispatch_task_store``.
# Completeness: tests/test_conftest_task_store_guard.py::test_task_store_constants_match_retarget_tuple
_TASK_STORE_RETARGETS = (
    ("scripts.fleet.post_task_reap", "_TASKS_DIR"),
    ("scripts.fleet.hramatka_hygiene_check", "_TASKS_DIR"),
    ("scripts.fleet.capacity_pick", "_TASKS_DIR"),
    ("scripts.maintenance.reclassify_dispatch_status", "DEFAULT_TASKS_DIR"),
    ("scripts.guardrails.delegate_ownership", "DEFAULT_TASK_STATE_DIR"),
)
# Live paths ``scripts/delegate.py`` derives from ``_TASKS_DIR.parent``
# (``grep _TASKS_DIR.parent scripts/``):
# - ``_TASKS_DIR.parent / "preflight_fast_fail.jsonl"``
# - fallback ``_TASKS_DIR.parent / worktree_claims.LOCK_DIR_NAME``
#   (``lu-worktree-locks``) when the git common dir is unknown.
# This set is explicit. It does not cover the rest of ``batch_state/``.
_DERIVED_LIVE_TASK_PATHS = (
    (_REAL_TASKS_DIR.parent / "preflight_fast_fail.jsonl").resolve(),
    (_REAL_TASKS_DIR.parent / "lu-worktree-locks").resolve(),
)
_REAL_TASKS_DIR_STR = os.fspath(_REAL_TASKS_DIR)
_REAL_TASKS_DIR_PREFIX = _REAL_TASKS_DIR_STR + os.sep
_DERIVED_LIVE_TASK_STRS = tuple(os.fspath(path) for path in _DERIVED_LIVE_TASK_PATHS)
_DERIVED_LIVE_TASK_PREFIXES = tuple(path + os.sep for path in _DERIVED_LIVE_TASK_STRS)
# Directory realpaths already known not to be a symlink into the live store.
# One realpath per directory, not one Path.resolve per written file.
_TASK_STORE_OUTSIDE_PARENTS: set[str] = set()
_TASK_STORE_WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
_TASK_STORE_MUTATION_EVENTS = {
    "os.chmod": (0,),
    "os.chown": (0,),
    "os.link": (0, 1),
    "os.mkdir": (0,),
    "os.remove": (0,),
    "os.rename": (0, 1),
    "os.rmdir": (0,),
    "os.symlink": (0, 1),
    "os.truncate": (0,),
    "os.unlink": (0,),
    "os.utime": (0,),
    "shutil.copyfile": (1,),
    "shutil.copytree": (1,),
    "shutil.move": (0, 1),
    "shutil.rmtree": (0,),
}
# One membership test per audit event. Python calls every hook for every
# event (``import``, ``compile``, ``exec``, ``os.listdir``, ``sys._getframe``,
# …). The #8640 opsec hook lives in another module and is not installed for
# this suite, so this hook stays separate and returns before any path work.
_TASK_STORE_HANDLED_EVENTS = frozenset(("open", "sqlite3.connect", *_TASK_STORE_MUTATION_EVENTS))


def _text_under_live_tasks(text: str) -> bool:
    """True when ``text`` is already a normalized path inside the live store."""
    if text == _REAL_TASKS_DIR_STR or text.startswith(_REAL_TASKS_DIR_PREFIX):
        return True
    for exact, prefix in zip(_DERIVED_LIVE_TASK_STRS, _DERIVED_LIVE_TASK_PREFIXES, strict=True):
        if text == exact or text.startswith(prefix):
            return True
    return False


def _path_under_real_tasks(path: object) -> bool:
    """True for the live task store, a file inside it, or a derived sibling path."""
    if isinstance(path, int) or path is None:
        return False
    try:
        text = os.fsdecode(path)
    except (TypeError, ValueError):
        return False
    if _text_under_live_tasks(text):
        return True
    norm = os.path.normpath(text)
    if norm != text and _text_under_live_tasks(norm):
        return True
    if os.path.isabs(norm) and ".." not in norm:
        parent = os.path.dirname(norm)
        if parent not in _TASK_STORE_OUTSIDE_PARENTS:
            try:
                real_parent = os.path.realpath(parent)
            except OSError:
                return False
            if real_parent == parent:
                _TASK_STORE_OUTSIDE_PARENTS.add(parent)
            elif _text_under_live_tasks(os.path.normpath(os.path.join(real_parent, os.path.basename(norm)))):
                return True
        try:
            if os.path.islink(norm):
                return _text_under_live_tasks(os.path.normpath(os.path.realpath(norm)))
        except OSError:
            return False
        return False
    try:
        return _text_under_live_tasks(os.path.normpath(os.path.realpath(text)))
    except OSError:
        return False


def _sqlite_path_under_real_tasks(database: object) -> bool:
    path, read_only = _sqlite_database_path(database)
    return path is not None and not read_only and _path_under_real_tasks(path)


def _refuse_real_task_store_write(kind: str, path: object) -> None:
    node = os.environ.get("PYTEST_CURRENT_TEST", "<unknown>")
    pytest.fail(
        f"{node} attempted to {kind} the real dispatch task store at {path} "
        f"({_REAL_TASKS_DIR}); isolate delegate._TASKS_DIR",
        pytrace=False,
    )


def _task_store_write_hook(event: str, args: tuple[object, ...]) -> None:
    """Fail a writable open, rename, or sqlite connect under the live task store.

    Installed once with ``sys.addaudithook`` (#8640): a monkeypatch of ``open``
    misses ``Path.write_text`` aliases and ``os.open`` captured before the
    fixture ran. The hook cannot be removed, so it stays installed and only
    refuses paths inside ``_REAL_TASKS_DIR`` and the explicit derived files
    under ``_REAL_TASKS_DIR.parent`` listed in ``_DERIVED_LIVE_TASK_PATHS``.
    The first statement rejects every event this hook does not handle.
    """
    if event not in _TASK_STORE_HANDLED_EVENTS:
        return
    if event == "open" and len(args) >= 3:
        path, mode, flags = args[0], args[1], args[2]
        writing = isinstance(mode, str) and any(char in mode for char in "wax+")
        if (writing or (isinstance(flags, int) and flags & _TASK_STORE_WRITE_FLAGS)) and _path_under_real_tasks(path):
            _refuse_real_task_store_write("write", path)
        return
    indexes = _TASK_STORE_MUTATION_EVENTS.get(event)
    if indexes is not None:
        for index in indexes:
            if index < len(args) and _path_under_real_tasks(args[index]):
                _refuse_real_task_store_write(event, args[index])
        return
    if event == "sqlite3.connect" and args and _sqlite_path_under_real_tasks(args[0]):
        _refuse_real_task_store_write("open a database in", args[0])


sys.addaudithook(_task_store_write_hook)


def _retarget_api_batch_state(monkeypatch: pytest.MonkeyPatch, batch_state: Path) -> None:
    """Point Monitor's task-store root at this test's ``batch_state``.

    ``production_context()`` reads ``config.BATCH_STATE_DIR`` when called, so
    importing Monitor here would only pull in FastAPI during fixture setup in
    minimal test environments. ``create_app(production_context())`` freezes
    the root onto ``app.state.ctx`` at import. ``delegate_router._tasks_dir``
    then writes ``.task_cache.sqlite3`` under that directory. The delegate
    ``_TASKS_DIR`` retarget does not move it, and the audit guard turns that
    connect into a 500 (``Failed`` is a ``BaseException``, so the orient
    section handler does not catch it).

    ``git_hygiene_router._active_task_ids`` is not this seam: it reads
    ``project_root / "batch_state" / "tasks"`` (the checkout, via
    ``live_repo_root``), and only opens task JSON read-only. It never opens
    the task-cache database. Pointing ``live_repo_root`` at the temp store
    would detach git-backed API tests from the repo.

    ``hramatka_router`` binds ``BATCH_STATE_DIR / "hramatka"`` at import. That
    is the lesson store, not ``tasks/``, and this guard does not watch it.
    """
    import scripts.api.config as api_config

    monkeypatch.setattr(api_config, "BATCH_STATE_DIR", batch_state)
    monitor_context = sys.modules.get("scripts.api.monitor_context")
    if monitor_context is not None:
        monitor_context.production_context.cache_clear()
    api_main = sys.modules.get("scripts.api.main")
    if api_main is None:
        return
    app = vars(api_main).get("app")
    context = getattr(getattr(app, "state", None), "ctx", None)
    if context is not None:
        monkeypatch.setattr(app.state, "ctx", context.with_roots(batch_state_dir=batch_state))


def _retarget_loaded_task_dirs(monkeypatch: pytest.MonkeyPatch, isolated: Path) -> None:
    """Import available task-store modules and point their constants at ``isolated``.

    Importing here binds the name before a test body can import the module and
    keep the live path. Minimal workflow venvs omit the agent runtime package;
    modules requiring it cannot be imported there. The list is
    ``_TASK_STORE_RETARGETS``, not a scan of ``sys.modules``.
    """
    import importlib

    for module_name, attr in _TASK_STORE_RETARGETS:
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError as exc:
            if exc.name != "learn_ukrainian_v4_runtime":
                raise
            # Skipped module keeps its live path; if a test later injects a stub
            # runtime and imports it, the audit hook is the backstop.
            continue
        monkeypatch.setattr(module, attr, isolated)


# Per-process, not per-test: ``mktemp`` scans the base directory for the next
# number, and that scan grows with every directory already created (#8654 review).
_DISPATCH_STORE_SEQ = itertools.count()


@pytest.fixture(scope="session")
def _dispatch_task_store_base(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """One numbered base for every per-test task store in this process."""
    return tmp_path_factory.mktemp("dispatch-stores")


@pytest.fixture(autouse=True)
def _isolate_dispatch_task_store(
    _dispatch_task_store_base: Path, monkeypatch: pytest.MonkeyPatch
) -> Path:
    """Point the dispatch task store at a per-test directory (#8654).

    The directory is ``<session base>/<n>/tasks``, so ``_TASKS_DIR.parent``
    (where delegate writes ``preflight_fast_fail.jsonl``) is also per-test.
    It comes from ``tmp_path_factory``, not the test's ``tmp_path``: an autouse
    fixture that creates a subdirectory of ``tmp_path`` breaks tests that
    assert their tmp dir starts empty (see ``_isolate_write_ownership_ledger``).
    Nothing is copied out of the live store. A test that sets ``_TASKS_DIR``
    itself runs after this autouse fixture, so that override wins.
    The same directory's parent becomes ``config.BATCH_STATE_DIR`` and
    ``app.state.ctx.roots.batch_state_dir``, so Monitor requests do not open
    the live ``.task_cache.sqlite3``.
    """
    isolated = _dispatch_task_store_base / str(next(_DISPATCH_STORE_SEQ)) / "tasks"
    isolated.mkdir(parents=True)
    import scripts.delegate as delegate_mod

    monkeypatch.setattr(delegate_mod, "_TASKS_DIR", isolated)
    _retarget_api_batch_state(monkeypatch, isolated.parent)
    # Tests put ``scripts/`` on ``sys.path`` and ``import delegate``. That is a
    # second module object with its own ``_TASKS_DIR``, not ``scripts.delegate``.
    flat_delegate = sys.modules.get("delegate")
    if flat_delegate is not None and flat_delegate is not delegate_mod:
        flat_file = getattr(flat_delegate, "__file__", None)
        delegate_file = getattr(delegate_mod, "__file__", None)
        if flat_file and delegate_file and Path(flat_file).resolve() == Path(delegate_file).resolve():
            monkeypatch.setattr(flat_delegate, "_TASKS_DIR", isolated)
    _retarget_loaded_task_dirs(monkeypatch, isolated)
    return isolated


class SocketBlockedError(RuntimeError):
    """Raised when a unit test attempts an un-opted outbound network connection (#6968)."""


def _is_localhost_host(host: object) -> bool:
    """Return True if host is loopback or local machine identifier."""
    if not host:
        return True
    if isinstance(host, bytes):
        try:
            host = host.decode("utf-8")
        except UnicodeDecodeError:
            return False
    if not isinstance(host, str):
        return False

    host_lower = host.lower()
    if host_lower in {"localhost", "127.0.0.1", "::1", "0.0.0.0", "::"}:
        return True
    if host_lower.endswith(".localhost"):
        return True
    with contextlib.suppress(OSError):
        if host_lower in {socket.gethostname().lower(), socket.getfqdn().lower()}:
            return True
    try:
        ip = ipaddress.ip_address(host)
        return ip.is_loopback or ip.is_unspecified
    except ValueError:
        return False


def _is_localhost_address(address: object) -> bool:
    """Return True if address is AF_UNIX (str/bytes) or AF_INET(6) pointing to localhost."""
    if address is None:
        return True
    if isinstance(address, (str, bytes)):
        return True
    if isinstance(address, tuple) and address:
        return _is_localhost_host(address[0])
    return False


_ORIG_SOCKET_CONNECT = socket.socket.connect
_ORIG_SOCKET_CONNECT_EX = socket.socket.connect_ex
_ORIG_SOCKET_SENDTO = socket.socket.sendto
_ORIG_SOCKET_SENDMSG = getattr(socket.socket, "sendmsg", None)
_ORIG_SOCKET_CREATE_CONNECTION = socket.create_connection

_SOCKET_GUARD_TLS = threading.local()


def _is_live_network_allowed() -> bool:
    return getattr(_SOCKET_GUARD_TLS, "live_network_allowed", False)


def _set_live_network_allowed(allowed: bool) -> None:
    _SOCKET_GUARD_TLS.live_network_allowed = allowed


def _raise_socket_blocked(address: object) -> None:
    host = address[0] if isinstance(address, tuple) and address else address
    raise SocketBlockedError(
        f"Outbound network connection to '{host}' blocked by socket-guard. "
        f"Unit tests must be hermetic and not rely on live external services. "
        f"If this test legitimately requires live network, mark it with @pytest.mark.live_network."
    )


def _guarded_connect(sock_self: socket.socket, address: object) -> object:
    if _is_live_network_allowed():
        return _ORIG_SOCKET_CONNECT(sock_self, address)
    if getattr(sock_self, "family", None) == getattr(socket, "AF_UNIX", None):
        return _ORIG_SOCKET_CONNECT(sock_self, address)
    if _is_localhost_address(address):
        return _ORIG_SOCKET_CONNECT(sock_self, address)
    _raise_socket_blocked(address)


def _guarded_connect_ex(sock_self: socket.socket, address: object) -> int:
    if _is_live_network_allowed():
        return _ORIG_SOCKET_CONNECT_EX(sock_self, address)
    if getattr(sock_self, "family", None) == getattr(socket, "AF_UNIX", None):
        return _ORIG_SOCKET_CONNECT_EX(sock_self, address)
    if _is_localhost_address(address):
        return _ORIG_SOCKET_CONNECT_EX(sock_self, address)
    _raise_socket_blocked(address)
    return -1


def _guarded_sendto(sock_self: socket.socket, data: bytes, *args: object, **kwargs: object) -> int:
    if _is_live_network_allowed():
        return _ORIG_SOCKET_SENDTO(sock_self, data, *args, **kwargs)
    address = kwargs.get("address") or (args[-1] if args else None)
    if (
        address is not None
        and getattr(sock_self, "family", None) != getattr(socket, "AF_UNIX", None)
        and not _is_localhost_address(address)
    ):
        _raise_socket_blocked(address)
    return _ORIG_SOCKET_SENDTO(sock_self, data, *args, **kwargs)


def _guarded_sendmsg(
    sock_self: socket.socket,
    buffers: object,
    *args: object,
    **kwargs: object,
) -> int:
    if _is_live_network_allowed():
        assert _ORIG_SOCKET_SENDMSG is not None
        return _ORIG_SOCKET_SENDMSG(sock_self, buffers, *args, **kwargs)
    address = kwargs.get("address")
    if address is None and len(args) >= 3:
        address = args[2]
    if (
        address is not None
        and getattr(sock_self, "family", None) != getattr(socket, "AF_UNIX", None)
        and not _is_localhost_address(address)
    ):
        _raise_socket_blocked(address)
    assert _ORIG_SOCKET_SENDMSG is not None
    return _ORIG_SOCKET_SENDMSG(sock_self, buffers, *args, **kwargs)


def _guarded_create_connection(
    address: object,
    *args: object,
    **kwargs: object,
) -> socket.socket:
    if _is_live_network_allowed():
        return _ORIG_SOCKET_CREATE_CONNECTION(address, *args, **kwargs)
    if not _is_localhost_address(address):
        _raise_socket_blocked(address)
    return _ORIG_SOCKET_CREATE_CONNECTION(address, *args, **kwargs)


_SOCKET_GUARD_INSTALLED = False


def _install_socket_guard() -> None:
    """Install package-wide socket-guard hooks covering all outbound surfaces (#6968)."""
    global _SOCKET_GUARD_INSTALLED
    if _SOCKET_GUARD_INSTALLED:
        return
    socket.socket.connect = _guarded_connect
    socket.socket.connect_ex = _guarded_connect_ex
    socket.socket.sendto = _guarded_sendto
    if _ORIG_SOCKET_SENDMSG is not None:
        socket.socket.sendmsg = _guarded_sendmsg
    socket.create_connection = _guarded_create_connection
    _SOCKET_GUARD_INSTALLED = True


# Install immediately upon conftest load (earliest hook preceding module/session fixtures)
_install_socket_guard()


# Dispatch worktrees drop these trees by default. Tests that read them skip
# only while sparse-checkout is on AND the tree is absent. CI (sparse off)
# always runs them. Needs are derived from the test module (path joins,
# Path/open arguments, imported path constants, fixtures, and
# pytest.mark.needs_sparse_tree), not from a hand list. A string that only
# mentions the tree name is not a read.
_SPARSE_TREE_DIRS: dict[str, tuple[str, ...]] = {
    "data/projects": ("tests/projects/open_model_data",),
    "data/lexicon": ("tests/lexicon",),
}
_SPARSE_TREES = frozenset(_SPARSE_TREE_DIRS)
_SPARSE_READ_ATTRS = frozenset(
    {
        "read_text",
        "read_bytes",
        "glob",
        "rglob",
        "iterdir",
        "open",
        "exists",
        "stat",
    }
)


def sparse_missing_tree_skip_reason(
    rel_path: str,
    *,
    sparse_enabled: bool,
    missing_trees: Collection[str],
    item_name: str = "",
) -> str | None:
    """Skip reason when a sparse worktree is missing a tree the test reads.

    Returns ``None`` when sparse-checkout is off, even if the tree is absent,
    so CI (full checkout, sparse disabled) never skips these tests.
    """
    if not sparse_enabled:
        return None
    normalized = rel_path.replace("\\", "/").lstrip("./")
    needed = _trees_needed_by_test(normalized, item_name)
    for tree in ("data/projects", "data/lexicon"):
        if tree in missing_trees and tree in needed:
            return (
                f"{tree} is absent from this sparse worktree; "
                f"re-include it with --sparse-include {tree}"
            )
    return None


def _trees_needed_by_test(rel_path: str, item_name: str) -> frozenset[str]:
    needed: set[str] = set()
    for tree, prefixes in _SPARSE_TREE_DIRS.items():
        if any(rel_path == prefix or rel_path.startswith(prefix + "/") for prefix in prefixes):
            needed.add(tree)
    analysis = _analyze_test_module(rel_path)
    if analysis is not None:
        module_trees, function_pairs = analysis
        needed.update(module_trees)
        base_name = item_name.split("[", 1)[0]
        needed.update(dict(function_pairs).get(base_name, ()))
    return frozenset(needed)


def _path_trees(text: str, *, allow_bare: bool = False) -> set[str]:
    """Trees named by a path.

    A bare ``data/lexicon`` string is the skip/re-include identifier, not a
    file read. A path into the tree (``data/lexicon/...``) counts, and so does
    a path-join whose final path is exactly the tree directory.
    """
    normalized = text.replace("\\", "/")
    found: set[str] = set()
    for tree in ("data/projects", "data/lexicon"):
        into_tree = f"{tree}/" in normalized
        bare_tree = allow_bare and (normalized == tree or normalized.endswith(f"/{tree}"))
        if into_tree or bare_tree:
            found.add(tree)
    return found


def _div_parts(node: ast.AST) -> list[str]:
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return _div_parts(node.left) + _div_parts(node.right)
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    return []


def _resolve_module(dotted: str) -> Path | None:
    rel = Path(*dotted.split("."))
    for candidate in (_REPO_ROOT / rel.with_suffix(".py"), _REPO_ROOT / rel / "__init__.py"):
        if candidate.is_file():
            return candidate
    return None


_EXPORT_CACHE: dict[str, tuple[tuple[str, frozenset[str]], ...]] = {}
_EXPORT_STACK: set[str] = set()


def _module_exports(abs_path: str) -> tuple[tuple[str, frozenset[str]], ...]:
    """Module-level names whose values reference a sparse data tree."""
    cached = _EXPORT_CACHE.get(abs_path)
    if cached is not None:
        return cached
    if abs_path in _EXPORT_STACK:
        return ()
    _EXPORT_STACK.add(abs_path)
    result: tuple[tuple[str, frozenset[str]], ...] = ()
    try:
        path = Path(abs_path)
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError, UnicodeError):
            return ()
        else:
            names: dict[str, set[str]] = {}
            aliases: dict[str, Path] = {}
            _collect_imports(tree, names, aliases)
            for stmt in tree.body:
                targets: list[ast.expr] = []
                value: ast.expr | None = None
                if isinstance(stmt, ast.Assign):
                    targets = list(stmt.targets)
                    value = stmt.value
                elif isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
                    targets = [stmt.target]
                    value = stmt.value
                if value is None:
                    continue
                trees = _expr_trees(value, names, aliases)
                for target in targets:
                    if isinstance(target, ast.Name) and trees:
                        names[target.id] = set(trees)
            result = tuple((name, frozenset(bound)) for name, bound in names.items() if bound)
    finally:
        _EXPORT_STACK.discard(abs_path)
    _EXPORT_CACHE[abs_path] = result
    return result


def _export_map(path: Path) -> dict[str, frozenset[str]]:
    return dict(_module_exports(str(path.resolve())))


def _collect_imports(
    tree: ast.AST,
    names: dict[str, set[str]],
    aliases: dict[str, Path],
) -> None:
    for stmt in tree.body if isinstance(tree, ast.Module) else []:
        if isinstance(stmt, ast.Import):
            for alias in stmt.names:
                module = _resolve_module(alias.name)
                if module is not None:
                    aliases[alias.asname or alias.name.split(".", 1)[0]] = module
        elif isinstance(stmt, ast.ImportFrom) and stmt.module and stmt.level == 0:
            for alias in stmt.names:
                if alias.name == "*":
                    continue
                submodule = _resolve_module(f"{stmt.module}.{alias.name}")
                bound = alias.asname or alias.name
                if submodule is not None:
                    aliases[bound] = submodule
                    continue
                source = _resolve_module(stmt.module)
                if source is None:
                    continue
                exported = _export_map(source).get(alias.name)
                if exported:
                    names[bound] = set(exported)


def _string_is_path_operand(node: ast.Constant, parent: ast.AST | None) -> bool:
    """True when a string is a filesystem path, not prose that mentions one."""
    if isinstance(parent, ast.BinOp) and isinstance(parent.op, ast.Div):
        return node is parent.left or node is parent.right
    if isinstance(parent, ast.Attribute) and parent.attr in _SPARSE_READ_ATTRS:
        return node is parent.value
    if not isinstance(parent, ast.Call):
        return False
    func = parent.func
    is_path_call = (isinstance(func, ast.Name) and func.id in {"Path", "open"}) or (
        isinstance(func, ast.Attribute) and func.attr in _SPARSE_READ_ATTRS
    )
    return is_path_call and any(node is arg for arg in parent.args)


def _expr_trees(
    node: ast.AST,
    names: dict[str, set[str]],
    aliases: dict[str, Path],
) -> set[str]:
    found: set[str] = set()
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(node):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    for child in ast.walk(node):
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            if _string_is_path_operand(child, parents.get(child)):
                found.update(_path_trees(child.value))
        elif isinstance(child, ast.BinOp) and isinstance(child.op, ast.Div):
            parts = _div_parts(child)
            if len(parts) >= 2:
                found.update(_path_trees("/".join(parts), allow_bare=True))
        elif isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
            found.update(names.get(child.id, ()))
        elif (
            isinstance(child, ast.Attribute)
            and isinstance(child.value, ast.Name)
            and isinstance(child.value.ctx, ast.Load)
        ):
            module = aliases.get(child.value.id)
            if module is not None:
                found.update(_export_map(module).get(child.attr, ()))
    return found


def _marker_trees(node: ast.AST) -> set[str]:
    found: set[str] = set()
    if isinstance(node, (ast.List, ast.Tuple)):
        for elt in node.elts:
            found.update(_marker_trees(elt))
        return found
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
        return found
    if node.func.attr != "needs_sparse_tree":
        return found
    for arg in node.args:
        if isinstance(arg, ast.Constant) and arg.value in _SPARSE_TREES:
            found.add(str(arg.value))
    return found


def _is_fixture(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[bool, bool]:
    for dec in fn.decorator_list:
        call = dec if isinstance(dec, ast.Call) else None
        func = call.func if call is not None else dec
        name = func.attr if isinstance(func, ast.Attribute) else (func.id if isinstance(func, ast.Name) else "")
        if name != "fixture":
            continue
        autouse = False
        if call is not None:
            for keyword in call.keywords:
                if (
                    keyword.arg == "autouse"
                    and isinstance(keyword.value, ast.Constant)
                    and keyword.value.value is True
                ):
                    autouse = True
        return True, autouse
    return False, False


def _function_body(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ast.stmt]:
    body = list(fn.body)
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        return body[1:]
    return body


def _has_read_call(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        func = child.func
        if isinstance(func, ast.Name) and func.id == "open":
            return True
        if isinstance(func, ast.Attribute) and func.attr in _SPARSE_READ_ATTRS:
            return True
    return False


def _decorator_trees(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    found: set[str] = set()
    for dec in fn.decorator_list:
        found.update(_marker_trees(dec))
    return found


def _local_calls(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    calls: set[str] = set()
    for stmt in _function_body(fn):
        for node in ast.walk(stmt):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                calls.add(node.func.id)
    return calls


def _usefixtures(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    names: set[str] = set()
    for dec in fn.decorator_list:
        if not isinstance(dec, ast.Call) or not isinstance(dec.func, ast.Attribute):
            continue
        if dec.func.attr != "usefixtures":
            continue
        for arg in dec.args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                names.add(arg.value)
    return names


@functools.lru_cache(maxsize=512)
def _analyze_test_module(
    rel_path: str,
) -> tuple[frozenset[str], tuple[tuple[str, frozenset[str]], ...]] | None:
    path = _REPO_ROOT / rel_path
    if not path.is_file() or path.suffix != ".py":
        return None
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError, UnicodeError):
        return None
    names: dict[str, set[str]] = {}
    aliases: dict[str, Path] = {}
    _collect_imports(tree, names, aliases)
    module_trees: set[str] = set()
    for stmt in tree.body:
        if (
            isinstance(stmt, ast.Assign)
            and len(stmt.targets) == 1
            and isinstance(stmt.targets[0], ast.Name)
            and stmt.targets[0].id == "pytestmark"
        ):
            module_trees.update(_marker_trees(stmt.value))
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if _has_read_call(stmt):
            module_trees.update(_expr_trees(stmt, names, aliases))
        targets = []
        value: ast.expr | None = None
        if isinstance(stmt, ast.Assign):
            targets = list(stmt.targets)
            value = stmt.value
        elif isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
            targets = [stmt.target]
            value = stmt.value
        if value is None:
            continue
        trees = _expr_trees(value, names, aliases)
        for target in targets:
            if isinstance(target, ast.Name) and trees:
                names[target.id] = set(trees)

    functions: dict[str, list[ast.FunctionDef | ast.AsyncFunctionDef]] = {}

    def _add_function(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        functions.setdefault(fn.name, []).append(fn)

    for stmt in tree.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _add_function(stmt)
        elif isinstance(stmt, ast.ClassDef):
            for child in stmt.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    _add_function(child)

    direct: dict[str, set[str]] = {}
    calls: dict[str, set[str]] = {}
    fixtures: dict[str, bool] = {}
    for name, defs in functions.items():
        trees: set[str] = set()
        called: set[str] = set()
        autouse = False
        is_fixture = False
        for fn in defs:
            for stmt in _function_body(fn):
                trees.update(_expr_trees(stmt, names, aliases))
            trees.update(_decorator_trees(fn))
            called.update(_local_calls(fn))
            found, fn_autouse = _is_fixture(fn)
            is_fixture = is_fixture or found
            autouse = autouse or fn_autouse
            for arg in (*fn.args.args, *fn.args.kwonlyargs):
                if arg.arg in functions:
                    called.add(arg.arg)
            called.update(_usefixtures(fn))
        direct[name] = trees
        calls[name] = called
        if is_fixture:
            fixtures[name] = autouse

    changed = True
    while changed:
        changed = False
        for name, called in calls.items():
            for callee in called:
                extra = direct.get(callee)
                if extra and not extra <= direct[name]:
                    direct[name].update(extra)
                    changed = True
    for name, autouse in fixtures.items():
        if autouse:
            module_trees.update(direct.get(name, ()))

    function_trees = tuple(
        (name, frozenset(trees)) for name, trees in sorted(direct.items()) if trees
    )
    return frozenset(module_trees), function_trees


@functools.lru_cache(maxsize=1)
def _sparse_checkout_enabled() -> bool:
    try:
        proc = subprocess.run(
            ["git", "-C", str(_REPO_ROOT), "config", "--get", "--type=bool", "core.sparseCheckout"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return proc.returncode == 0 and proc.stdout.strip().lower() == "true"


def _sparse_missing_trees() -> frozenset[str]:
    forced = sparse_trees.forced_missing_trees() & _SPARSE_TREES
    if not _sparse_checkout_enabled():
        return frozenset(forced)
    missing = set(forced)
    for rel in ("data/projects", "data/lexicon"):
        if not (_REPO_ROOT / rel).is_dir():
            missing.add(rel)
    return frozenset(missing)


def _item_repo_rel(item: pytest.Item) -> str:
    raw = getattr(item, "path", None) or getattr(item, "fspath", "")
    path = Path(str(raw))
    try:
        return path.resolve().relative_to(_REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip tests whose sparse-excluded tree is not in this worktree."""
    del config
    missing = _sparse_missing_trees()
    if not missing:
        return
    for item in items:
        reason = sparse_missing_tree_skip_reason(
            _item_repo_rel(item),
            sparse_enabled=True,
            missing_trees=missing,
            item_name=item.name,
        )
        if reason:
            item.add_marker(pytest.mark.skip(reason=reason))


def pytest_configure(config: pytest.Config) -> None:
    _install_socket_guard()
    config.addinivalue_line(
        "markers",
        "needs_sparse_tree(tree): test reads data/projects or data/lexicon; "
        "skipped when sparse-checkout omits that tree",
    )
    config.addinivalue_line(
        "markers",
        "needs_artifact(group, rel): test requires data/<rel> from artifact group; "
        "skipped only when the artifact is absent",
    )
    # The live app's request middleware defaults to 10s. Tests that drive
    # TestClient(api_main.app) and read the real decision/ADR tree have
    # exceeded that under xdist and come back as 504 (#8439). The assertions
    # are about the payload. A test that sets API_REQUEST_TIMEOUT_S itself
    # still wins, including the 0.05s timeout case.
    os.environ.setdefault("API_REQUEST_TIMEOUT_S", "60")


def pytest_runtest_setup(item: pytest.Item) -> None:
    if item.get_closest_marker("live_network"):
        _set_live_network_allowed(True)
    marker = item.get_closest_marker("needs_artifact")
    if marker is not None:
        if len(marker.args) != 2 or marker.kwargs:
            raise pytest.UsageError("needs_artifact marker requires exactly (group, rel)")
        from scripts.storage.paths import DATA_ROOT, MissingArtifactError, find_entry, verify_file

        group, rel = marker.args
        try:
            entry = find_entry(group, rel)
            verify_file(DATA_ROOT / rel, entry, group=group, rel=rel)
        except MissingArtifactError as error:
            detail = error.detail.casefold()
            if detail == "missing" or "manifest missing" in detail or "no unique manifest entry" in detail:
                pytest.skip(f"needs_artifact: {error}")
            raise


def pytest_runtest_teardown(item: pytest.Item, nextitem: pytest.Item | None) -> None:
    _set_live_network_allowed(False)


@pytest.fixture(autouse=True)
def _socket_guard(request: pytest.FixtureRequest) -> Generator[None, None, None]:
    """Ensure per-test live_network marker status is respected and always reset (#6968)."""
    is_live = bool(request.node.get_closest_marker("live_network"))
    _set_live_network_allowed(is_live)
    try:
        yield
    finally:
        _set_live_network_allowed(False)


# =============================================================================
# MODULE TEMPLATES
# =============================================================================


@pytest.fixture
def minimal_module_b1():
    """Minimal valid B1 module structure."""
    return """---
module: 1
title: Test Module
level: B1
pedagogy: PPP
cefr: B1.1
phase: Grammar
objectives:
  - Test objective
---

# Presentation

This is the presentation section with content.

# Practice

Practice content here.

# Production

Production content here.

# Vocabulary

| Слово | Переклад | Примітки |
|-------|----------|----------|
| слово | word | noun |
"""


@pytest.fixture
def minimal_module_a1():
    """Minimal valid A1 module structure."""
    return """---
module: 1
title: Test Module
level: A1
pedagogy: PPP
cefr: A1.1
phase: Basics
objectives:
  - Test objective
---

# Presentation

This is the presentation section with content.

# Practice

Practice content here.

# Production

Production content here.

# Vocabulary

| Word | IPA | English | POS | Gender | Note |
|------|-----|---------|-----|--------|------|
| слово | /ˈslɔwɔ/ | word | noun | n | - |
"""


# =============================================================================
# ACTIVITY SNIPPETS
# =============================================================================


@pytest.fixture
def valid_quiz_b1():
    """Valid B1 quiz with proper word counts."""
    return """
## quiz: Частини мови

1. Яка частина мови в українській граматиці називає предмети та поняття для опису світу?
   - [x] Іменник
   - [ ] Дієслово
   - [ ] Прикметник
   - [ ] Прислівник

2. Яка частина мови в українській мові позначає дію або стан суб'єкта речення?
   - [ ] Іменник
   - [x] Дієслово
   - [ ] Прикметник
   - [ ] Прислівник
"""


@pytest.fixture
def valid_error_correction():
    """Valid error-correction with all required callouts."""
    return """
## error-correction: Виправлення

1. Він ходить до школа.
   > [!error] школа
   > [!answer] школи
   > [!options] школа | школи | школу | школою
   > [!explanation] Після прийменника "до" вживаємо родовий відмінок.

2. Вона читає книгу на стіл.
   > [!error] стіл
   > [!answer] столі
   > [!options] стіл | столі | столу | столом
   > [!explanation] Після прийменника "на" (місце) вживаємо місцевий відмінок.
"""


@pytest.fixture
def valid_unjumble():
    """Valid unjumble with answer callout."""
    return """
## unjumble: Речення

1. я / люблю / Україну / дуже / сильно
   > [!answer] Я дуже сильно люблю Україну.

2. вона / читає / книгу / цікаву / про / історію
   > [!answer] Вона читає цікаву книгу про історію.
"""


@pytest.fixture
def valid_match_up():
    """Valid match-up with proper pairs."""
    return """
## match-up: Терміни

| Термін | Переклад |
|--------|----------|
| слово | word |
| речення | sentence |
| граматика | grammar |
| відмінок | case |
| дієслово | verb |
| іменник | noun |
| прикметник | adjective |
| прислівник | adverb |
| займенник | pronoun |
| сполучник | conjunction |
"""


# =============================================================================
# VOCABULARY FIXTURES
# =============================================================================


@pytest.fixture
def valid_vocab_table_b1():
    """Valid B1 vocabulary table (3 columns)."""
    return """
# Словник

| Слово | Переклад | Примітки |
|-------|----------|----------|
| граматика | grammar | noun |
| відмінок | case | noun |
| дієслово | verb | noun |
| іменник | noun | noun |
"""


@pytest.fixture
def valid_vocab_table_a1():
    """Valid A1 vocabulary table (6 columns with IPA)."""
    return """
# Vocabulary

| Word | IPA | English | POS | Gender | Note |
|------|-----|---------|-----|--------|------|
| слово | /ˈslɔwɔ/ | word | noun | n | - |
| книга | /ˈknɪɦa/ | book | noun | f | - |
| читати | /tʃɪˈtatɪ/ | to read | verb | - | impf |
"""


@pytest.fixture
def invalid_vocab_missing_ipa():
    """Invalid A1 vocabulary - missing IPA."""
    return """
# Vocabulary

| Word | IPA | English | POS | Gender | Note |
|------|-----|---------|-----|--------|------|
| слово | | word | noun | n | - |
| книга | /ˈknɪɦa/ | book | noun | f | - |
"""


# =============================================================================
# CONTENT WITH ISSUES
# =============================================================================


@pytest.fixture
def content_with_russian_chars():
    """Content with Russian-only characters."""
    return """---
module: 1
title: Test
level: B1
---

# Test

Прикметник "красивый" не є українським.
"""


@pytest.fixture
def content_clean_ukrainian():
    """Clean Ukrainian content without Russian chars."""
    return """---
module: 1
title: Test
level: B1
---

# Test

Прикметник "красивий" є українським словом.
Граматика української мови цікава.
"""


@pytest.fixture
def quiz_with_short_prompts():
    """Quiz with prompts that are too short for B1."""
    return """
## quiz: Тест

1. Яка це частина мови?
   - [x] Іменник
   - [ ] Дієслово

2. Що це таке?
   - [x] Граматика
   - [ ] Лексика
"""


# =============================================================================
# PPP STRUCTURE FIXTURES
# =============================================================================


@pytest.fixture
def valid_ppp_structure():
    """Content with valid PPP structure."""
    return """---
module: 1
title: Test
level: B1
pedagogy: PPP
---

# Presentation

Content here.

# Practice

Practice content.

# Production

Production content.
"""


@pytest.fixture
def invalid_ppp_missing_section():
    """PPP content missing Production section."""
    return """---
module: 1
title: Test
level: B1
pedagogy: PPP
---

# Presentation

Content here.

# Practice

Practice content.
"""


@pytest.fixture(autouse=True)
def _enable_formal_shielded_cf_for_unit_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unit tests may still exercise isolation helpers; production CLI stays retired.

    Production / drivers leave LU_FORMAL_SHIELDED_CF unset so review-pr refuses.
    """
    monkeypatch.setenv("LU_FORMAL_SHIELDED_CF", "1")


# Real primary checkout's ``.worktrees/`` — not a ``.worktrees`` directory inside
# the worker that happens to be running the suite. Dispatch tests that call
# ``cmd_dispatch`` used to mkdir husks here while git itself was stubbed.
_REAL_WORKTREES_DIR = ""
_REAL_WORKTREES_PREFIX = ""
_WORKTREE_ENTRIES_AT_START: set[str] = set()
_CREATED_WORKTREE_ENTRIES: set[str] = set()
# path -> "PYTEST_CURRENT_TEST=... caller=file:line" for each recorded creation.
_CREATED_WORKTREE_ATTRIBUTION: dict[str, str] = {}
# How long teardown waits for a still-running ``git worktree add``.
_POPEN_CLASSIFY_TIMEOUT_SECONDS = 30
# Bookkeeping bugs are reported once at teardown. They must not raise out of
# os.mkdir / Popen and change the call the test actually made.
_GUARD_CLASSIFY_FAILURES: list[str] = []
_GUARD_CLASSIFY_FAILURE_LIMIT = 8


class _PopenWorktreeCall:
    """One ``git worktree add`` observed at ``Popen`` construction.

    Calls are not merged: each stores that call's own absent-before flag.
    ``proc`` stays reachable so teardown can poll or wait after the caller
    drops the object. ``token`` is a weakref so the call is not keyed by a
    bare ``id()`` a later Popen can reuse.
    """

    __slots__ = ("absent_before", "attribution", "destination", "proc", "token")

    def __init__(
        self,
        proc: subprocess.Popen,
        destination: str,
        absent_before: bool,
        attribution: str,
    ) -> None:
        self.token = weakref.ref(proc)
        self.proc = proc
        self.destination = destination
        self.absent_before = absent_before
        self.attribution = attribution


# One record per ``git worktree add`` Popen.
_POPEN_WORKTREE_CALLS: list[_PopenWorktreeCall] = []


def _init_real_worktrees_dir() -> str:
    """Absolute realpath of the primary checkout's ``.worktrees`` directory."""
    global _REAL_WORKTREES_DIR, _REAL_WORKTREES_PREFIX
    if _REAL_WORKTREES_DIR:
        return _REAL_WORKTREES_DIR
    from scripts.common.repo_root import main_checkout_root

    worktrees = main_checkout_root(_REPO_ROOT) / ".worktrees"
    _REAL_WORKTREES_DIR = os.path.realpath(worktrees)
    _REAL_WORKTREES_PREFIX = _REAL_WORKTREES_DIR + os.sep
    return _REAL_WORKTREES_DIR


def _record_classify_failure(exc: BaseException) -> None:
    if len(_GUARD_CLASSIFY_FAILURES) >= _GUARD_CLASSIFY_FAILURE_LIMIT:
        return
    _GUARD_CLASSIFY_FAILURES.append(f"{type(exc).__name__}: {exc}")


def _decode_guard_path(path: object) -> str:
    """Filesystem text for ``path``.

    ``os.fsdecode(os.fspath(...))`` accepts ``str``, ``bytes``, and path-like
    objects. A bytes path used to reach ``str.startswith`` and raise
    ``TypeError`` before the real mkdir ran.
    """
    return os.fsdecode(os.fspath(path))  # type: ignore[arg-type]


def _worktree_guard_enabled() -> bool:
    """``LU_WORKTREE_GUARD=0`` turns the hooks off for an overhead measurement."""
    return os.environ.get("LU_WORKTREE_GUARD", "1") != "0"


def _gh_guard_enabled() -> bool:
    """``LU_GH_GUARD=0`` disables only the real GitHub CLI spawn guard."""
    return os.environ.get("LU_GH_GUARD", "1") != "0"


def _worktree_entry_key(path: object) -> str | None:
    """Path of a new worktree root, or None for anything nested inside one.

    A dispatch entry is ``.worktrees/dispatch/<agent>/<task>``. A flat entry is
    a direct child of ``.worktrees``. Deeper paths are files inside a checkout
    that already exists — including this worker's own worktree — and must not
    trip the guard. The prefix check is a string compare so ordinary ``/tmp``
    mkdirs stay cheap.

    The final path component is not resolved. A symlink created as the entry
    is keyed by the link path, not by the directory it points at.
    """
    root = _init_real_worktrees_dir()
    try:
        text = os.path.abspath(_decode_guard_path(path))
    except (TypeError, ValueError):
        return None
    if text != root and not text.startswith(_REAL_WORKTREES_PREFIX):
        return None
    parent = os.path.realpath(os.path.dirname(text))
    if parent != root and not parent.startswith(_REAL_WORKTREES_PREFIX):
        return None
    name = os.path.basename(text)
    if not name or name in {".", ".."}:
        return None
    candidate = os.path.join(parent, name)
    if candidate == root:
        return None
    parts = [part for part in candidate[len(_REAL_WORKTREES_PREFIX) :].split(os.sep) if part]
    if len(parts) == 1 or (len(parts) == 3 and parts[0] == "dispatch"):
        return candidate
    return None


def _missing_worktree_entries(path: object) -> list[str]:
    """Worktree-root ancestors of ``path`` that do not exist yet."""
    root = _init_real_worktrees_dir()
    try:
        probe = os.path.abspath(_decode_guard_path(path))
    except (TypeError, ValueError):
        return []
    if probe != root and not probe.startswith(_REAL_WORKTREES_PREFIX):
        return []
    missing: list[str] = []
    while probe.startswith(_REAL_WORKTREES_PREFIX) or probe == root:
        key = _worktree_entry_key(probe)
        if key and key not in _WORKTREE_ENTRIES_AT_START and not os.path.lexists(key):
            missing.append(key)
        parent = os.path.dirname(probe)
        if parent == probe:
            break
        probe = parent
    return missing


def _classify_created_path(path: object) -> list[tuple[str, bool]]:
    """``(entry, existed immediately before the call)`` for one path."""
    key = _worktree_entry_key(path)
    if key is None:
        return []
    existed = key in _WORKTREE_ENTRIES_AT_START or os.path.lexists(key)
    return [(key, existed)]


def _classify_makedirs_path(path: object) -> list[tuple[str, bool]]:
    missing = _missing_worktree_entries(path)
    classified = [(key, False) for key in missing]
    key = _worktree_entry_key(path)
    if key and key not in missing and (key in _WORKTREE_ENTRIES_AT_START or os.path.lexists(key)):
        classified.append((key, True))
    return classified


def _classify_quietly(classify, path: object) -> list[tuple[str, bool]] | None:
    try:
        return classify(path)
    except Exception as exc:
        # A guard bug must not replace the original call.
        _record_classify_failure(exc)
        return None


def _caller_outside_conftest() -> str:
    """First repo frame above this file, as ``path:line``."""
    here = Path(__file__).resolve()
    repo = _REPO_ROOT.resolve()
    frame = sys._getframe()
    fallback: str | None = None
    while frame is not None:
        frame = frame.f_back
        if frame is None:
            break
        filename = frame.f_code.co_filename
        if not filename or filename.startswith("<"):
            continue
        try:
            resolved = Path(filename).resolve()
        except OSError:
            continue
        if resolved == here:
            continue
        try:
            relative = resolved.relative_to(repo).as_posix()
        except ValueError:
            if fallback is None:
                fallback = f"{resolved}:{frame.f_lineno}"
            continue
        return f"{relative}:{frame.f_lineno}"
    return fallback or "<no frame outside conftest>"


def _creation_attribution() -> str:
    """Node id plus the creating frame, captured when the entry appears."""
    node = os.environ.get("PYTEST_CURRENT_TEST", "").strip() or "<no PYTEST_CURRENT_TEST>"
    return f"PYTEST_CURRENT_TEST={node} caller={_caller_outside_conftest()}"


def _remember_if_created(key: str, existed_before: bool) -> None:
    """Record ``key`` only when this call both found it absent and created it.

    The caller observed ``os.path.lexists`` immediately before the original
    call and that call returned without raising. This checks again afterwards.
    A path that already existed — including ``os.makedirs(..., exist_ok=True)``
    on a directory another process owns — is not recorded. A call that raises
    records nothing, and an earlier absent observation is not reused.

    A tiny race remains: another process can create the path between the
    before-check and a successful ``exist_ok=True`` return. We accept that
    window. Locking the real ``.worktrees`` tree would stall every other
    agent on the host.
    """
    if existed_before or key in _WORKTREE_ENTRIES_AT_START:
        return
    if os.path.lexists(key):
        _CREATED_WORKTREE_ENTRIES.add(key)
        _CREATED_WORKTREE_ATTRIBUTION.setdefault(key, _creation_attribution())


def _remember_quietly(classified: list[tuple[str, bool]] | None) -> None:
    if not classified:
        return
    try:
        for key, existed_before in classified:
            _remember_if_created(key, existed_before)
    except Exception as exc:
        # A guard bug must not replace the original call.
        _record_classify_failure(exc)


def _guarded_mkdir(path: object, *args: object, **kwargs: object):
    classified = _classify_quietly(_classify_created_path, path)
    result = _ORIGINAL_OS_MKDIR(path, *args, **kwargs)
    # A raised call never reaches here, so a failure records nothing.
    _remember_quietly(classified)
    return result


def _guarded_makedirs(name: object, *args: object, **kwargs: object):
    classified = _classify_quietly(_classify_makedirs_path, name)
    result = _ORIGINAL_OS_MAKEDIRS(name, *args, **kwargs)
    _remember_quietly(classified)
    return result


def _guarded_symlink(src: object, dst: object, *args: object, **kwargs: object):
    # The link path is the second argument. The target may live anywhere.
    classified = _classify_quietly(_classify_created_path, dst)
    result = _ORIGINAL_OS_SYMLINK(src, dst, *args, **kwargs)
    _remember_quietly(classified)
    return result


def _decode_argv(argv: list | tuple) -> list[str] | None:
    try:
        return [_decode_guard_path(arg) for arg in argv]
    except (TypeError, ValueError):
        return None


def _resolve_against(base: str, raw: str) -> str:
    if os.path.isabs(raw):
        return os.path.abspath(raw)
    return os.path.abspath(os.path.join(base, raw))


def _git_global_option_end(args: list[str], cwd: object) -> tuple[int, str] | None:
    """Index of the subcommand, and the cwd after any ``-C`` options.

    Git globals that take a value (``-c k=v``, ``-C dir``, ``--git-dir``,
    ``--work-tree``) are skipped. Anything else that is not an option is the
    subcommand. Returns None when argv is not a git command.
    """
    if os.path.basename(args[0]) != "git":
        return None
    if cwd is None:
        base = os.getcwd()
    else:
        try:
            base = os.path.abspath(_decode_guard_path(cwd))
        except (TypeError, ValueError):
            return None
    index = 1
    while index < len(args):
        arg = args[index]
        if arg == "-C":
            if index + 1 >= len(args):
                return None
            base = _resolve_against(base, args[index + 1])
            index += 2
            continue
        if arg.startswith("-C") and arg != "-C":
            base = _resolve_against(base, arg[2:])
            index += 1
            continue
        if arg == "-c":
            if index + 1 >= len(args):
                return None
            index += 2
            continue
        if arg.startswith("-c") and len(arg) > 2:
            index += 1
            continue
        if arg in {"--git-dir", "--work-tree"}:
            if index + 1 >= len(args):
                return None
            index += 2
            continue
        if arg.startswith("--git-dir=") or arg.startswith("--work-tree="):
            index += 1
            continue
        if arg == "worktree" or not arg.startswith("-"):
            return index, base
        index += 1
    return None


def _git_worktree_add_destination(argv: object, cwd: object) -> str | None:
    """Destination of ``git worktree add``, when ``argv`` is that command."""
    if isinstance(argv, (str, bytes)) or not isinstance(argv, (list, tuple)) or not argv:
        return None
    args = _decode_argv(argv)
    if not args:
        return None
    parsed = _git_global_option_end(args, cwd)
    if parsed is None:
        return None
    index, base = parsed
    if index + 1 >= len(args) or args[index] != "worktree" or args[index + 1] != "add":
        return None
    index += 2
    valued = {"-b", "-B", "--reason"}
    while index < len(args):
        arg = args[index]
        if arg == "--":
            index += 1
            if index >= len(args):
                return None
            dest = args[index]
            break
        if arg in valued:
            if index + 1 >= len(args):
                return None
            index += 2
            continue
        if arg.startswith("-"):
            index += 1
            continue
        dest = arg
        break
    else:
        return None
    if not os.path.isabs(dest):
        dest = os.path.join(base, dest)
    return _worktree_entry_key(dest)


def _popen_cwd(pos: tuple[object, ...], kwargs: dict[str, object]) -> object:
    if "cwd" in kwargs:
        return kwargs["cwd"]
    # Popen positional order after args: bufsize, executable, stdin, stdout,
    # stderr, preexec_fn, close_fds, shell, cwd.
    if len(pos) >= 9:
        return pos[8]
    return None


def _guarded_popen_init(self, args, *pos, **kwargs):
    _guard_live_github_spawn(args, kwargs)
    if not _worktree_guard_enabled():
        _ORIGINAL_POPEN_INIT(self, args, *pos, **kwargs)
        return
    dest: str | None = None
    absent_before = False
    try:
        found = _git_worktree_add_destination(args, _popen_cwd(pos, kwargs))
        if found is not None:
            dest = found
            absent_before = (
                found not in _WORKTREE_ENTRIES_AT_START and not os.path.lexists(found)
            )
    except Exception as exc:
        # A guard bug must not replace the original call.
        _record_classify_failure(exc)
        dest = None
    _ORIGINAL_POPEN_INIT(self, args, *pos, **kwargs)
    # The process may exit without wait or poll. Remember this call only;
    # teardown decides from its own absent-before flag and its exit status.
    if dest is None:
        return
    try:
        _POPEN_WORKTREE_CALLS.append(
            _PopenWorktreeCall(self, dest, absent_before, _creation_attribution())
        )
    except Exception as exc:
        _record_classify_failure(exc)


def _guard_live_github_spawn(args: object, kwargs: dict[str, object]) -> None:
    """Reject a process spawn that resolves to the installed GitHub CLI."""
    if _LIVE_GITHUB_ALLOWED or not _gh_guard_enabled() or not _REAL_GH_BINARY:
        return
    # Limits: a string argv is not inspected, so ``shell=True`` (the command
    # is a string) is unguarded. A positional ``executable`` is ignored; only
    # ``kwargs["executable"]`` is read. ``os.system`` and
    # ``asyncio.create_subprocess_shell`` never reach this hook.
    if isinstance(args, (str, bytes)) or not isinstance(args, (list, tuple)) or not args:
        return
    argv = _decode_argv(args)
    if not argv:
        return
    executable = kwargs.get("executable") or argv[0]
    if not isinstance(executable, (str, bytes, os.PathLike)):
        return
    executable_path = os.fsdecode(executable)
    env = kwargs.get("env")
    process_env = env if isinstance(env, dict) else os.environ
    configured_backend = process_env.get("AGENT_REAL_GH")
    if not os.path.isabs(executable_path):
        if os.path.basename(executable_path) != "gh":
            return
        search_path = os.fspath(process_env.get("PATH", os.defpath))
        resolved = shutil.which(executable_path, path=search_path)
        if resolved is None:
            return
        executable_path = resolved
    is_shim = _is_agent_runtime_shim(executable_path) and os.path.basename(executable_path) == "gh"
    # The runtime shim is safe only when it has been explicitly wired to a
    # non-real test backend. Never let AGENT_REAL_GH exempt a direct real-gh
    # spawn; that environment variable is also present in normal agent runs.
    if (
        is_shim
        and configured_backend
        and os.path.isfile(os.fspath(configured_backend))
        and os.path.realpath(os.fspath(configured_backend)) != os.path.realpath(_REAL_GH_BINARY)
    ):
        return
    if not is_shim and os.path.realpath(executable_path) != os.path.realpath(_REAL_GH_BINARY):
        return

    from scripts.secret_redactor import redact_value

    rendered = redact_value(argv)
    pytest.fail(
        f"{os.environ.get('PYTEST_CURRENT_TEST', '<unknown test id>')} spawned real gh: {rendered}; "
        "@pytest.mark.live_github opts this test into real gh/network access; it does not skip the test in CI",
        pytrace=False,
    )


def _popen_exit_status(proc: subprocess.Popen) -> int | None:
    """Exit code of ``proc``, or None when it is still running after the wait."""
    code = proc.poll()
    if code is not None:
        return code
    try:
        return proc.wait(timeout=_POPEN_CLASSIFY_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        return None


def _snapshot_worktree_entries() -> set[str]:
    """Task directories plus ``git worktree list`` paths. No recursive walk."""
    root = Path(_init_real_worktrees_dir())
    found: set[str] = set()
    if root.is_dir():
        try:
            children = list(root.iterdir())
        except OSError:
            children = []
        for child in children:
            found.add(os.path.realpath(child))
            if child.name != "dispatch" or not child.is_dir():
                continue
            try:
                agents = list(child.iterdir())
            except OSError:
                continue
            for agent in agents:
                if not agent.is_dir():
                    continue
                try:
                    tasks = list(agent.iterdir())
                except OSError:
                    continue
                for task in tasks:
                    found.add(os.path.realpath(task))
    try:
        proc = _ORIGINAL_SUBPROCESS_RUN(
            ["git", "-C", str(root.parent), "worktree", "list", "--porcelain"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return found
    stdout = getattr(proc, "stdout", "") or ""
    for line in stdout.splitlines():
        if line.startswith("worktree "):
            found.add(os.path.realpath(line[len("worktree ") :].strip()))
    return found


# Bound at import time, before the session fixture installs the hooks.
_ORIGINAL_OS_MKDIR = os.mkdir
_ORIGINAL_OS_MAKEDIRS = os.makedirs
_ORIGINAL_OS_SYMLINK = os.symlink
_ORIGINAL_SUBPROCESS_RUN = subprocess.run
_ORIGINAL_POPEN_INIT = subprocess.Popen.__init__


def _worktree_guard_teardown_message() -> str | None:
    """Leftovers and classify failures for this process, or None when clean."""
    listed = _snapshot_worktree_entries()
    suspected = set(_CREATED_WORKTREE_ENTRIES)
    for call in _POPEN_WORKTREE_CALLS:
        path = call.destination
        if not call.absent_before or path in _WORKTREE_ENTRIES_AT_START:
            continue
        try:
            code = _popen_exit_status(call.proc)
        except Exception as exc:
            _record_classify_failure(exc)
            continue
        if code is None:
            _record_classify_failure(
                TimeoutError(
                    f"git worktree add {path}: timed out waiting for exit status"
                )
            )
            continue
        if code == 0 and (os.path.lexists(path) or path in listed):
            suspected.add(path)
            _CREATED_WORKTREE_ATTRIBUTION.setdefault(path, call.attribution)
    lines: list[str] = []
    if _GUARD_CLASSIFY_FAILURES:
        detail = "; ".join(_GUARD_CLASSIFY_FAILURES)
        lines.append(f"guard could not classify: {detail}")
    leftovers = sorted(
        path
        for path in suspected
        if path not in _WORKTREE_ENTRIES_AT_START and (os.path.lexists(path) or path in listed)
    )
    if leftovers:
        rendered: list[str] = []
        for path in leftovers:
            rendered.append(f"  {path}")
            rendered.append(
                "    "
                + _CREATED_WORKTREE_ATTRIBUTION.get(
                    path,
                    "PYTEST_CURRENT_TEST=<unknown> caller=<unknown>",
                )
            )
        joined = "\n".join(rendered)
        lines.append(
            "this pytest process created entries under the real .worktrees/ "
            f"that are still present:\n{joined}\n"
            "Concurrent worktrees from other processes are not listed."
        )
    if not lines:
        return None
    return "\n".join(lines)


@pytest.fixture(scope="session", autouse=True)
def _guard_real_worktree_entries() -> Generator[None, None, None]:
    """Fail the session if this process created a worktree entry on the real tree.

    Live agents add checkouts under ``.worktrees/`` for the whole time the suite
    runs, so a before/after listing of that directory false-positives on a busy
    host. This guard records only creations that pass through this process:
    ``os.mkdir`` / ``os.makedirs`` / ``os.symlink`` of a worktree root, and a
    ``git worktree add`` whose destination appears. ``subprocess.run``,
    ``call``, ``check_call``, and ``check_output`` all construct
    ``subprocess.Popen``, so the git hook sits on ``Popen`` rather than on
    ``run`` alone. Directories nested inside an existing checkout (this
    worker included) are ignored. Paths already present when the worker
    started are snapshotted and ignored even if a test touches them.

    mkdir, makedirs, and symlink record a path only when that same call saw
    it absent immediately beforehand and returned without raising. A failed
    call records nothing. There is no cross-call memory: an earlier absent
    observation does not attach to a later ``FileExistsError``. ``Popen`` of
    ``git worktree add`` records that call's destination and whether it was
    absent beforehand. Teardown obtains the exit status with ``poll`` and,
    if the process is still running, ``wait``. Creation is attributed only
    when that call's return code is 0 and the destination exists. A timeout
    is reported as "guard could not classify", not as a creation. Each
    record stores ``PYTEST_CURRENT_TEST`` and the first calling frame outside
    this file (``file:line`` under the repo). Bookkeeping errors are not
    raised from the hooked call; teardown reports them as "guard could not
    classify".

    Set ``LU_WORKTREE_GUARD=0`` to skip directory/worktree hooks and
    ``LU_GH_GUARD=0`` independently to skip the real-GitHub-CLI spawn guard.
    Under xdist each worker is its own process, so the hooks and the teardown
    check run once per worker rather than once in the controller.
    """
    guard_worktrees = _worktree_guard_enabled()
    guard_github = _gh_guard_enabled()
    if not guard_worktrees and not guard_github:
        yield
        return
    if guard_worktrees:
        _WORKTREE_ENTRIES_AT_START.clear()
        _CREATED_WORKTREE_ENTRIES.clear()
        _CREATED_WORKTREE_ATTRIBUTION.clear()
        _POPEN_WORKTREE_CALLS.clear()
        _GUARD_CLASSIFY_FAILURES.clear()
        _WORKTREE_ENTRIES_AT_START.update(_snapshot_worktree_entries())
    with pytest.MonkeyPatch.context() as patcher:
        if guard_worktrees:
            patcher.setattr(os, "mkdir", _guarded_mkdir)
            patcher.setattr(os, "makedirs", _guarded_makedirs)
            patcher.setattr(os, "symlink", _guarded_symlink)
        patcher.setattr(subprocess.Popen, "__init__", _guarded_popen_init)
        yield
    if guard_worktrees:
        message = _worktree_guard_teardown_message()
        if message:
            pytest.fail(message)


@pytest.fixture(autouse=True)
def _scope_real_checkout_acp_execution_to_tmp(tmp_path_factory, monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep ACP execution off the real primary checkout.

    ``acp_execution_cwd`` on the primary checkout mkdirs
    ``.worktrees/dispatch/acp`` before ``git worktree add``. That parent
    stays behind on a CI checkout that had no ``.worktrees`` yet. Redirect
    only when the resolved cwd is that primary checkout itself.

    ``resolve_main_root`` maps every worktree of this checkout back to the
    primary, so it must not decide the redirect. A dispatch worktree uses
    the real helper, which yields that worktree and does not mkdir. Calls
    aimed at any other repo, including a test's own ``git init`` primary,
    still run the real helper.
    """
    # Import eagerly: production imports this module function-locally, so it
    # may not be loaded yet, and skipping would run the real helper against the
    # primary checkout. Only a missing bridge runtime (the rules workflow venv
    # has just pytest + PyYAML) may skip the redirect.
    try:
        from scripts.ai_agent_bridge import _acp_execution as acp_mod
    except ImportError:
        return

    real_checkout = Path(_init_real_worktrees_dir()).parent.resolve()
    original = acp_mod.acp_execution_cwd

    @contextlib.contextmanager
    def scoped(repo_root, *, task_id):
        try:
            resolved = Path(repo_root).resolve()
        except (OSError, RuntimeError, ValueError):
            resolved = None
        if resolved == real_checkout:
            yield tmp_path_factory.mktemp("acp-execution")
            return
        with original(repo_root, task_id=task_id) as workspace:
            yield workspace

    monkeypatch.setattr(acp_mod, "acp_execution_cwd", scoped)
