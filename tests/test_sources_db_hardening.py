"""Shared SQLite connections must go through ``open_readonly`` (#11217).

CPython 3.12 keeps a per-connection statement cache that is not safe when
threads share the connection (CPython #118172, #11208). ``open_readonly`` sets
``cached_statements=0`` for ``check_same_thread=False``; the AST guard below
stops a new shared connection from bypassing it.
"""

from __future__ import annotations

import ast
import sqlite3
import threading
from pathlib import Path

import pytest

from scripts.lib.readonly_sqlite import open_readonly
from scripts.wiki import sources_db

REPO_ROOT = Path(__file__).resolve().parents[1]
SCANNED_ROOTS = ("scripts", ".mcp")

# (path, enclosing function) -> why this shared connection may skip open_readonly.
ALLOWED_SHARED_CONNECTS: dict[tuple[str, str], str] = {
    ("scripts/wiki/sources_db.py", "_open_writer_conn"): "writable branch: schema create/migrate, not a shared reader",
    ("scripts/audit/verbatim_overlap_gate.py", "ShingleIndex.__init__"): "writable derived index, not sources.db",
    ("scripts/wiki/embedding_manifest.py", "EmbeddingManifest.__init__"): "writable embedding manifest",
    ("scripts/rag/wiki_cache.py", "WikiCache.__init__"): "writable response cache",
    (".mcp/servers/sources/server.py", "_discard_sources_conn"): ":memory: stand-in that fails every query",
    ("scripts/lib/readonly_sqlite.py", "open_readonly"): "the hardened opener itself (sets cached_statements=0)",
    ("scripts/api/resilience.py", "connect_sqlite"): "pass-through wrapper; no caller shares a connection or opens sources.db",
    ("scripts/control_plane/storage.py", "_connect_postgres"): "psycopg connect, not sqlite",
    ("scripts/control_plane/storage.py", "connect"): "control-plane stores; callers pass no check_same_thread",
}


# sqlite3.connect(database, timeout, detect_types, isolation_level, check_same_thread, ...)
_CHECK_SAME_THREAD_POSITION = 4


def _is_true(node: ast.expr) -> bool:
    return isinstance(node, ast.Constant) and node.value is True


def _is_unsafe_connect(call: ast.Call) -> bool:
    """True when a ``connect(...)`` call is, or may be, a thread-shared connection.

    The default ``check_same_thread=True`` is safe. Anything else is flagged: a
    ``False``/non-constant keyword, a positional argument in the fifth slot that
    is not ``True``, or ``**kwargs`` the scanner cannot inspect.
    """
    if len(call.args) > _CHECK_SAME_THREAD_POSITION and not _is_true(call.args[_CHECK_SAME_THREAD_POSITION]):
        return True
    return any(
        kw.arg is None or (kw.arg == "check_same_thread" and not _is_true(kw.value)) for kw in call.keywords
    )


def _shared_connects(source: str) -> list[tuple[int, str]]:
    """(line, enclosing function) of every ``connect(...)`` that may be thread-shared."""
    tree = ast.parse(source)
    found: list[tuple[int, str]] = []
    # ``from sqlite3 import connect as c`` / ``c = sqlite3.connect`` rebind the name.
    names = {"connect"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "sqlite3":
            names |= {a.asname for a in node.names if a.name == "connect" and a.asname}
        elif (
            isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Attribute)
            and node.value.attr == "connect"
        ):
            names |= {t.id for t in node.targets if isinstance(t, ast.Name)}

    def visit(node: ast.AST, scope: tuple[str, ...]) -> None:
        if isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            scope += (node.name,)
        if isinstance(node, ast.Call):
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
            if name in names and _is_unsafe_connect(node):
                found.append((node.lineno, ".".join(scope)))
        for child in ast.iter_child_nodes(node):
            visit(child, scope)

    visit(tree, ())
    return found


def test_shared_connect_scanner_flags_plain_connect() -> None:
    src = "import sqlite3\nclass A:\n    def f(self):\n        sqlite3.connect('x', check_same_thread=False)\n"
    assert _shared_connects(src) == [(4, "A.f")]
    assert _shared_connects("sqlite3.connect('x')\nopen_readonly('x', check_same_thread=False)\n") == []
    assert _shared_connects("sqlite3.connect('x', check_same_thread=True)\n") == []


@pytest.mark.parametrize(
    "call",
    [
        "from sqlite3 import connect\nconnect('x', check_same_thread=False)\n",
        "from sqlite3 import connect as c\nc('x', check_same_thread=False)\n",
        "db.connect('x', check_same_thread=False)\n",
        "c = sqlite3.connect\nc('x', check_same_thread=False)\n",
        "sqlite3.connect('x', 5.0, 0, 'DEFERRED', False)\n",
        "sqlite3.connect('x', 5.0, 0, 'DEFERRED', flag)\n",
        "sqlite3.connect('x', check_same_thread=flag)\n",
        "sqlite3.connect('x', **opts)\n",
        "connect('x', check_same_thread=False, **opts)\n",
    ],
)
def test_shared_connect_scanner_flags_unsafe_call_forms(call: str) -> None:
    assert len(_shared_connects(call)) == 1


def test_shared_connect_scanner_ignores_safe_positional_forms() -> None:
    assert _shared_connects("sqlite3.connect('x', 5.0, 0, 'DEFERRED', True)\n") == []
    assert _shared_connects("sqlite3.connect('x', 5.0)\n") == []


@pytest.mark.repo_wide
def test_shared_sqlite_connections_route_through_open_readonly() -> None:
    violations: list[str] = []
    seen: set[tuple[str, str]] = set()
    for root in SCANNED_ROOTS:
        for path in sorted((REPO_ROOT / root).rglob("*.py")):
            rel = path.relative_to(REPO_ROOT).as_posix()
            if "/node_modules/" in rel or "/." in rel.removeprefix(".mcp/"):
                continue
            text = path.read_text(encoding="utf-8")
            if "connect" not in text:
                continue
            for line, scope in _shared_connects(text):
                if (rel, scope) in ALLOWED_SHARED_CONNECTS:
                    seen.add((rel, scope))
                else:
                    violations.append(f"{rel}:{line} ({scope or '<module>'})")
    assert not violations, (
        "check_same_thread=False connections must use scripts.lib.readonly_sqlite.open_readonly "
        f"(cached_statements=0), or be allowlisted with a reason: {violations}"
    )
    assert seen == set(ALLOWED_SHARED_CONNECTS), "stale allowlist entries: " + str(
        sorted(set(ALLOWED_SHARED_CONNECTS) - seen)
    )


@pytest.fixture
def small_db(tmp_path: Path) -> Path:
    path = tmp_path / "s.db"
    conn = sqlite3.connect(path)
    try:
        with conn:
            conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, v TEXT)")
            conn.executemany("INSERT INTO t VALUES (?, ?)", [(i, f"v{i}") for i in range(50)])
    finally:
        conn.close()
    return path


def test_open_conn_read_only_disables_statement_cache(small_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}
    real = sqlite3.connect

    def spy(*args, **kwargs):
        seen.update(kwargs)
        return real(*args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", spy)
    conn = sources_db._open_conn(small_db, read_only=True)
    try:
        assert seen["cached_statements"] == 0
        assert seen["check_same_thread"] is False
        assert conn.row_factory is sqlite3.Row
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("INSERT INTO t VALUES (999, 'x')")
    finally:
        conn.close()


def test_open_conn_honours_connection_factory(small_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class Marked(sqlite3.Connection):
        pass

    monkeypatch.setattr(sources_db, "_connection_factory", Marked)
    conn = sources_db._open_conn(small_db, read_only=True)
    try:
        assert isinstance(conn, Marked)
    finally:
        conn.close()


def test_open_readonly_accepts_factory(small_db: Path) -> None:
    class Marked(sqlite3.Connection):
        pass

    conn = open_readonly(small_db, check_same_thread=False, factory=Marked)
    try:
        assert isinstance(conn, Marked)
    finally:
        conn.close()


def test_shared_read_only_connection_survives_threads(small_db: Path) -> None:
    conn = sources_db._open_conn(small_db, read_only=True)
    errors: list[BaseException] = []

    def work() -> None:
        try:
            for i in range(200):
                row = conn.execute("SELECT v FROM t WHERE id = ?", (i % 50,)).fetchone()
                assert row["v"] == f"v{i % 50}"
        except BaseException as exc:
            errors.append(exc)

    threads = [threading.Thread(target=work) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    conn.close()
    assert not errors, errors[:1]
