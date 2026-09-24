"""
Pytest configuration and shared fixtures for audit tests.

Provides reusable content snippets and module templates for testing.
"""

import ast
import contextlib
import functools
import ipaddress
import os
import socket
import sqlite3
import subprocess
import sys
import threading
from collections.abc import Collection, Generator
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests import sparse_trees

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _bridge_db_paths() -> tuple[Path, Path]:
    """Return the primary bridge DB and any configured path before tests begin."""
    from scripts.ai_agent_bridge import _config

    primary = _config.PRIMARY_REPO_ROOT / ".mcp" / "servers" / "message-broker" / "messages.db"
    return primary.resolve(), Path(_config.DB_PATH).resolve()


_REAL_BRIDGE_DB_PATH, _CONFIGURED_BRIDGE_DB_PATH = _bridge_db_paths()
_API_BRIDGE_DB_PATH = (_REPO_ROOT / ".mcp" / "servers" / "message-broker" / "messages.db").resolve()
_UNISOLATED_BRIDGE_DB_PATHS = frozenset(
    {_REAL_BRIDGE_DB_PATH, _CONFIGURED_BRIDGE_DB_PATH, _API_BRIDGE_DB_PATH}
)
_BRIDGE_DB_SUFFIXES = tuple(sorted({path.name for path in _UNISOLATED_BRIDGE_DB_PATHS}))
_BRIDGE_DB_BINDINGS_TO_REPLACE = set(_UNISOLATED_BRIDGE_DB_PATHS)


def _sqlite_database_path(database: object) -> tuple[Path | None, bool]:
    """Return a SQLite path and whether a URI explicitly opens it read-only."""
    raw_path = os.fspath(database) if isinstance(database, (str, os.PathLike)) else None
    if raw_path is None:
        return None, False
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


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Report this session's temp usage and optionally enforce a CI budget."""
    config = session.config
    if hasattr(config, "workerinput"):
        return

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
        pytest.skip(f"requires {relative_path} (not provisioned in CI)")

    if required_sqlite_tables:
        try:
            with sqlite3.connect(f"file:{artifact}?mode=ro", uri=True) as connection:
                available_tables = {
                    row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
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
def _isolate_write_ownership_ledger(tmp_path_factory, monkeypatch):
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
    first version of this fixture did exactly that.
    """
    ledger_dir = tmp_path_factory.mktemp("write-ownership")
    db_file = ledger_dir / "write-ownership.sqlite3"
    conn = sqlite3.connect(db_file)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS write_claims (task_id TEXT NOT NULL, claim_json TEXT NOT NULL, pid INTEGER, created_at REAL NOT NULL, PRIMARY KEY (task_id, claim_json))"
    )
    conn.commit()
    conn.close()
    monkeypatch.setenv("LEARN_UKRAINIAN_OWNERSHIP_LEDGER", str(db_file))
    monkeypatch.setenv("LEARN_UKRAINIAN_OWNERSHIP_TASK_STATE_DIR", str(ledger_dir))


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
    # The live app's request middleware defaults to 10s. Tests that drive
    # TestClient(api_main.app) and read the real decision/ADR tree have
    # exceeded that under xdist and come back as 504 (#8439). The assertions
    # are about the payload. A test that sets API_REQUEST_TIMEOUT_S itself
    # still wins, including the 0.05s timeout case.
    os.environ.setdefault("API_REQUEST_TIMEOUT_S", "60")


def pytest_runtest_setup(item: pytest.Item) -> None:
    if item.get_closest_marker("live_network"):
        _set_live_network_allowed(True)


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
