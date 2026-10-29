"""Shared SQLite connections must go through ``open_readonly`` (#11217).

CPython 3.12 keeps a per-connection statement cache that is not safe when
threads share the connection (CPython #118172, #11208). ``open_readonly`` sets
``cached_statements=0`` for ``check_same_thread=False``; the AST guard below
stops a new shared connection from bypassing it.
"""

from __future__ import annotations

import ast
import os
import sqlite3
import threading
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
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
    (
        "scripts/api/resilience.py",
        "connect_sqlite",
    ): "pass-through wrapper; no caller shares a connection or opens sources.db",
    ("scripts/control_plane/storage.py", "_connect_postgres"): "psycopg connect, not sqlite",
    ("scripts/control_plane/storage.py", "connect"): "control-plane stores; callers pass no check_same_thread",
}


# sqlite3.connect(database, timeout, detect_types, isolation_level, check_same_thread, ...)
_CHECK_SAME_THREAD_POSITION = 4


def _is_true(node: ast.expr) -> bool:
    return isinstance(node, ast.Constant) and node.value is True


def _positional_args(call: ast.Call) -> list[ast.expr] | None:
    """Positional arguments with literal ``*(...)``/``*[...]`` expanded; ``None`` if any stays opaque."""
    args: list[ast.expr] = []
    for arg in call.args:
        if not isinstance(arg, ast.Starred):
            args.append(arg)
        elif isinstance(arg.value, ast.Tuple | ast.List):
            nested = ast.Call(func=call.func, args=list(arg.value.elts), keywords=[])
            expanded = _positional_args(nested)
            if expanded is None:
                return None
            args.extend(expanded)
        else:
            return None
    return args


def _is_unsafe_connect(call: ast.Call) -> bool:
    """True when a ``connect(...)`` call is, or may be, a thread-shared connection.

    The default ``check_same_thread=True`` is safe. Anything else is flagged: a
    ``False``/non-constant keyword, a positional argument in the fifth slot that
    is not ``True``, or ``**kwargs`` / ``*args`` the scanner cannot inspect (an
    explicit ``check_same_thread=True`` keyword still proves safety for ``*args``,
    since a duplicate fifth positional would raise ``TypeError``).
    """
    flag = next((kw for kw in call.keywords if kw.arg == "check_same_thread"), None)
    if any(kw.arg is None for kw in call.keywords):
        return True
    if flag is not None:
        return not _is_true(flag.value)
    args = _positional_args(call)
    if args is None:
        return True
    return len(args) > _CHECK_SAME_THREAD_POSITION and not _is_true(args[_CHECK_SAME_THREAD_POSITION])


def _is_connect_ref(node: ast.expr | None, names: set[str]) -> bool:
    """``sqlite3.connect`` / ``x.connect``, a name known to alias it, or a walrus wrapping either."""
    if isinstance(node, ast.NamedExpr):
        return _is_connect_ref(node.value, names)
    if isinstance(node, ast.Attribute):
        return node.attr == "connect"
    return isinstance(node, ast.Name) and node.id in names


def _alias_targets(node: ast.AST) -> list[ast.expr]:
    if isinstance(node, ast.Assign):
        return node.targets
    if isinstance(node, ast.AnnAssign | ast.NamedExpr):
        return [node.target]
    return []


def _shared_connects(source: str) -> list[tuple[int, str]]:
    """(line, enclosing function) of every ``connect(...)`` that may be thread-shared."""
    tree = ast.parse(source)
    found: list[tuple[int, str]] = []
    # ``from sqlite3 import connect as c`` / ``c = sqlite3.connect`` / ``d = c`` rebind the name.
    names = {"connect"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "sqlite3":
            names |= {a.asname for a in node.names if a.name == "connect" and a.asname}
    grew = True
    while grew:  # fixpoint: alias chains resolve regardless of statement order
        grew = False
        for node in ast.walk(tree):
            if _is_connect_ref(getattr(node, "value", None), names):
                new = {t.id for t in _alias_targets(node) if isinstance(t, ast.Name)} - names
                if new:
                    names |= new
                    grew = True

    def visit(node: ast.AST, scope: tuple[str, ...]) -> None:
        if isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            scope += (node.name,)
        if isinstance(node, ast.Call) and _is_connect_ref(node.func, names) and _is_unsafe_connect(node):
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
        "sqlite3.connect(*(':memory:', 5.0, 0, 'DEFERRED', False))\n",
        "sqlite3.connect('x', *rest)\n",
        "sqlite3.connect(*args)\n",
        "sqlite3.connect('x', *(5.0, 0, 'DEFERRED'), False)\n",
        "sqlite3.connect(*[':memory:', *rest])\n",
        "c: object = sqlite3.connect\nc('x', check_same_thread=False)\n",
        "from sqlite3 import connect as c\nd = c\nd('x', check_same_thread=False)\n",
        "d = c\nc = sqlite3.connect\nd('x', check_same_thread=False)\n",
        "c = sqlite3.connect\nd: object = c\ne = d\ne('x', 5.0, 0, 'DEFERRED', False)\n",
        "(c := sqlite3.connect)('x', check_same_thread=False)\n",
        "(c := sqlite3.connect)('x')\nc('x', check_same_thread=False)\n",
        "d = (c := sqlite3.connect)\nd('x', check_same_thread=False)\n",
        "(c := sqlite3.connect)\n(d := c)('x', 5.0, 0, 'DEFERRED', False)\n",
        "(d := (c := sqlite3.connect))('x', **opts)\n",
    ],
)
def test_shared_connect_scanner_flags_unsafe_call_forms(call: str) -> None:
    assert len(_shared_connects(call)) == 1


def test_shared_connect_scanner_counts_walrus_call_and_alias_call_separately() -> None:
    src = "(c := sqlite3.connect)('x', check_same_thread=False)\nc('x', check_same_thread=False)\n"
    assert [line for line, _ in _shared_connects(src)] == [1, 2]


def test_shared_connect_scanner_ignores_safe_positional_forms() -> None:
    assert _shared_connects("sqlite3.connect('x', 5.0, 0, 'DEFERRED', True)\n") == []
    assert _shared_connects("sqlite3.connect('x', 5.0)\n") == []
    assert _shared_connects("sqlite3.connect(*(':memory:', 5.0, 0, 'DEFERRED', True))\n") == []
    assert _shared_connects("sqlite3.connect(*args, check_same_thread=True)\n") == []
    assert _shared_connects("c: object = sqlite3.connect\nd = c\nd('x')\n") == []
    assert _shared_connects("(c := sqlite3.connect)('x')\nc('x', check_same_thread=True)\n") == []


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


@pytest.fixture
def cached_db(small_db: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    monkeypatch.setattr(sources_db, "SOURCES_DB_PATH", small_db)
    monkeypatch.setattr(sources_db, "_conn", None)
    monkeypatch.setattr(sources_db, "_conn_state", None)
    yield small_db
    if sources_db._conn is not None:
        sources_db._conn.close()


@pytest.mark.parametrize("changed", ["inode", "mtime"])
def test_cached_reader_reopens_on_file_identity_change(
    cached_db: Path, changed: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    held = sources_db._get_conn()
    assert held.execute("SELECT v FROM t WHERE id = 0").fetchone()[0] == "v0"
    before = cached_db.stat()
    if changed == "inode":
        replacement = cached_db.with_name("replacement.db")
        with sqlite3.connect(replacement) as writer:
            writer.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, v TEXT)")
            writer.execute("INSERT INTO t VALUES (0, 'replacement')")
        os.utime(replacement, ns=(before.st_atime_ns, before.st_mtime_ns))
        replacement.replace(cached_db)
        assert cached_db.stat().st_ino != before.st_ino
        assert cached_db.stat().st_mtime_ns == before.st_mtime_ns
        expected = "replacement"
    else:
        os.utime(cached_db, ns=(before.st_atime_ns, before.st_mtime_ns + 1_000_000_000))
        assert cached_db.stat().st_ino == before.st_ino
        expected = "v0"
    cached_db.chmod(0o444)
    opened: list[str] = []
    real = sqlite3.connect

    def spy(database, **kwargs):
        opened.append(database)
        assert kwargs["uri"] is True
        return real(database, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", spy)
    try:
        fresh = sources_db._get_conn()
        assert fresh is not held
        assert fresh.execute("SELECT v FROM t WHERE id = 0").fetchone()[0] == expected
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            fresh.execute("INSERT INTO t VALUES (999, 'mutation')")
        assert sources_db._get_conn() is fresh
        assert opened == [cached_db.as_uri() + "?mode=ro"]
        assert held.execute("SELECT v FROM t WHERE id = 0").fetchone()[0] == "v0"
    finally:
        held.close()


def test_unchanged_cached_reader_does_not_reopen(cached_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    opened: list[tuple[str, dict]] = []
    real = sqlite3.connect

    def spy(database, **kwargs):
        opened.append((database, kwargs))
        return real(database, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", spy)
    held = sources_db._get_conn()
    for _ in range(5):
        assert sources_db._get_conn() is held
        assert held.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 50
    assert len(opened) == 1
    assert opened[0][0] == cached_db.as_uri() + "?mode=ro"
    assert opened[0][1]["uri"] is True


def test_concurrent_cache_misses_open_only_one_reader(cached_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    opened: list[sqlite3.Connection] = []
    real = sources_db._open_conn
    ready = threading.Barrier(4)

    def spy(path, *, read_only=False):
        conn = real(path, read_only=read_only)
        opened.append(conn)
        return conn

    def read():
        ready.wait(timeout=5)
        return sources_db._get_conn()

    monkeypatch.setattr(sources_db, "_open_conn", spy)
    with ThreadPoolExecutor(max_workers=4) as pool:
        readers = list(pool.map(lambda _: read(), range(4)))
    assert len(opened) == 1
    assert all(reader is opened[0] for reader in readers)
    assert readers[0].execute("SELECT COUNT(*) FROM t").fetchone()[0] == 50


def test_request_connection_override_survives_missing_cached_file(cached_db: Path) -> None:
    held = sources_db._get_conn()
    with sources_db.using_connection(held):
        sources_db.SOURCES_DB_PATH = cached_db.with_name("missing.db")
        assert sources_db._get_conn() is held
        assert held.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 50


def test_failed_reopen_preserves_cache_until_retry(cached_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    held = sources_db._get_conn()
    before = cached_db.stat()
    os.utime(cached_db, ns=(before.st_atime_ns, before.st_mtime_ns + 1_000_000_000))

    with monkeypatch.context() as patch:

        def fail_open(*args, **kwargs):
            raise sqlite3.OperationalError("unable to open database file")

        patch.setattr(sources_db, "_open_conn", fail_open)
        with pytest.raises(sqlite3.OperationalError, match="unable to open database file"):
            sources_db._get_conn()
        assert sources_db._conn is held
        assert held.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 50

    try:
        fresh = sources_db._get_conn()
        assert fresh is not held
        assert fresh.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 50
    finally:
        held.close()


def test_self_healer_cache_swap_does_not_trigger_a_duplicate_open(
    cached_db: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    held = sources_db._get_conn()
    before = cached_db.stat()
    os.utime(cached_db, ns=(before.st_atime_ns, before.st_mtime_ns + 1_000_000_000))
    healed = sources_db._open_conn(cached_db, read_only=True)
    monkeypatch.setattr(sources_db, "_conn", healed)

    def unexpected_open(*args, **kwargs):
        pytest.fail("The self-healer already opened the current file")

    monkeypatch.setattr(sources_db, "_open_conn", unexpected_open)
    try:
        assert sources_db._get_conn() is healed
        assert sources_db._get_conn() is healed
        assert healed.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 50
        assert held.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 50
    finally:
        held.close()


def test_missing_file_keeps_existing_reader_available(cached_db: Path) -> None:
    held = sources_db._get_conn()
    cached_db.rename(cached_db.with_name("moved.db"))
    assert sources_db._get_conn() is held
    assert held.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 50
    assert not cached_db.exists()


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


def test_cached_reader_follows_the_selector_and_keeps_calls_in_flight(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import gc
    import weakref
    from contextlib import closing

    from scripts.storage import generations

    monkeypatch.setenv("LU_EVIDENCE_FREE_DISK_FLOOR_BYTES", "0")
    monkeypatch.setenv("LU_EVIDENCE_WAL_CEILING_BYTES", "0")
    data = tmp_path / "data"
    data.mkdir()
    seed = data / "seed.db"
    with closing(sqlite3.connect(seed)) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, v TEXT)")
        conn.executemany("INSERT INTO t VALUES (?, ?)", [(i, f"v{i}") for i in range(50)])
        conn.commit()
    selector = data / "sources.db"
    seed.rename(selector)
    generations.hold_database(selector)
    with generations.writer_lock(selector) as held:
        generations.checkpoint_legacy_store(held)
        generations.publish_generation(selector, held, mode="bootstrap")
    monkeypatch.setattr(sources_db, "SOURCES_DB_PATH", selector)
    monkeypatch.setattr(sources_db, "_conn", None)
    monkeypatch.setattr(sources_db, "_conn_state", None)

    held_reader = sources_db._get_conn()
    in_flight = held_reader.execute("SELECT v FROM t ORDER BY id")
    assert in_flight.fetchone()[0] == "v0"
    assert sources_db._get_conn() is held_reader  # an unchanged selector does not reopen

    with generations.writer_lock(selector) as held:
        stage = data / "stage.db"
        with closing(open_readonly(held.generation)) as source, closing(sqlite3.connect(stage)) as copy:
            source.backup(copy)
            copy.execute("UPDATE t SET v = 'new' || id")
            copy.commit()
        generations.publish_generation(stage, held)

    fresh = sources_db._get_conn()
    try:
        assert fresh is not held_reader
        assert fresh.execute("SELECT v FROM t WHERE id = 0").fetchone()[0] == "new0"
        assert sources_db._get_conn() is fresh
        assert [row[0] for row in in_flight.fetchmany(2)] == ["v1", "v2"]  # still the old generation
        closed = weakref.ref(held_reader)
        del in_flight, held_reader
        gc.collect()
        assert closed() is None  # the old connection closes once its last call ends
    finally:
        fresh.close()
        sources_db._conn = None
