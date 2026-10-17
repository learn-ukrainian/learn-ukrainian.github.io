"""Synthetic fixtures for the shared SQLite reader boundary (#9609, #9662)."""

from __future__ import annotations

import sqlite3
import subprocess
import sys
import textwrap
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path

import pytest

from scripts.lib.readonly_sqlite import is_sqlite_connection, open_readonly


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "space ї # ?.db"
    with closing(sqlite3.connect(path)) as conn:
        conn.execute("CREATE TABLE synthetic (id INTEGER)")
        conn.execute("INSERT INTO synthetic VALUES (7)")
        conn.commit()
    return path


@pytest.mark.parametrize("immutable", [False, True])
def test_special_character_path_opens_exact_file_readonly(database, immutable):
    before = database.read_bytes()
    with closing(open_readonly(database, immutable=immutable)) as conn:
        assert conn.execute("SELECT id FROM synthetic").fetchall() == [(7,)]
        assert conn.execute("PRAGMA query_only").fetchone() == (1,)
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            conn.execute("INSERT INTO synthetic VALUES (8)")
        conn.execute("PRAGMA query_only=OFF")
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            conn.execute("CREATE TABLE forbidden (id)")
    assert database.read_bytes() == before


@pytest.mark.parametrize("memory", [False, True])
def test_attach_is_refused(database, tmp_path, memory):
    attached = tmp_path / "attachment.db"
    with closing(open_readonly(database)) as conn:
        assert conn.getlimit(sqlite3.SQLITE_LIMIT_ATTACHED) == 0
        with pytest.raises(sqlite3.OperationalError, match="too many attached databases"):
            conn.execute("ATTACH DATABASE ? AS side", (":memory:" if memory else str(attached),))
        for sql, args, refusal in (
            ("ATTACH DATABASE ? AS side", (str(attached),), "too many attached databases - max 0"),
            ("ATTACH DATABASE ':memory:' AS side", (), "too many attached databases - max 0"),
            ("DETACH DATABASE main", (), "cannot detach database main"),
            ("DETACH DATABASE temp", (), "no such database: temp|cannot detach database temp"),
        ):
            with pytest.raises(sqlite3.DatabaseError, match=refusal):
                conn.execute(sql, args)
        assert [row[1] for row in conn.execute("PRAGMA database_list")] == ["main"]
    assert not attached.exists()


@pytest.mark.parametrize("name", ["main", "temp", "missing"])
def test_detach_is_refused(database, name):
    with closing(open_readonly(database)) as conn:
        with pytest.raises(sqlite3.OperationalError, match=r"cannot detach|no such database"):
            conn.execute(f"DETACH DATABASE {name}")


def test_vacuum_into_is_refused(database, tmp_path):
    target = tmp_path / "vacuum.db"
    with closing(open_readonly(database)) as conn:
        with pytest.raises(sqlite3.OperationalError, match="too many attached databases"):
            conn.execute("VACUUM INTO ?", (str(target),))
    assert not target.exists()


def test_schema_and_journal_pragmas_cannot_write(database):
    before = database.read_bytes()
    with closing(open_readonly(database)) as conn:
        conn.execute("PRAGMA writable_schema=ON")
        assert conn.execute("PRAGMA writable_schema").fetchone() == (1,)
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            conn.execute("UPDATE sqlite_master SET name='changed'")
    with closing(open_readonly(database)) as conn:
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            conn.execute("PRAGMA journal_mode=WAL")
    assert database.read_bytes() == before


@pytest.mark.skipif(
    not hasattr(sqlite3.Connection, "enable_load_extension"),
    reason="Python was built without the extension-loading API; there is no API loading path to test",
)
@pytest.mark.parametrize("initially_enabled", [False, True])
def test_extension_loading_is_not_enabled(monkeypatch, database, tmp_path, initially_enabled):
    connect = sqlite3.connect

    def connect_with_build_default(*args, **kwargs):
        conn = connect(*args, **kwargs)
        if initially_enabled:
            conn.enable_load_extension(True)
        return conn

    monkeypatch.setattr(sqlite3, "connect", connect_with_build_default)
    extension = tmp_path / "missing_extension_10747"
    assert not extension.exists()
    with closing(open_readonly(database)) as conn:
        functions_before = conn.execute("PRAGMA function_list").fetchall()
        for load in (
            lambda: conn.execute("SELECT load_extension(?)", (str(extension),)),
            lambda: conn.load_extension(str(extension)),
        ):
            with pytest.raises(sqlite3.OperationalError) as error:
                load()
            # Disabled loading must fail before looking up a library. Loader
            # errors include its filename, with platform-specific wording.
            assert "missing_extension_10747" not in str(error.value)
            assert "cannot open shared object file" not in str(error.value)
        assert conn.execute("PRAGMA function_list").fetchall() == functions_before
        assert conn.execute("SELECT id FROM synthetic").fetchall() == [(7,)]
    assert not extension.exists()


def test_build_without_extension_loading_api_still_opens_readonly(monkeypatch, database):
    class NoExtensionAPIConnection(sqlite3.Connection):
        def __getattribute__(self, name):
            if name in {"enable_load_extension", "load_extension"}:
                raise AttributeError(name)
            return super().__getattribute__(name)

    connect = sqlite3.connect
    monkeypatch.setattr(sqlite3, "connect", lambda *a, **kw: connect(*a, **kw, factory=NoExtensionAPIConnection))
    with closing(open_readonly(database)) as conn:
        assert not hasattr(conn, "enable_load_extension")
        assert conn.execute("SELECT id FROM synthetic").fetchall() == [(7,)]
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            conn.execute("INSERT INTO synthetic VALUES (8)")


def test_executescript_preserves_readonly_and_attachment_refusal(database):
    before = database.read_bytes()
    with closing(open_readonly(database)) as conn:
        conn.executescript("SELECT id FROM synthetic;")
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            conn.executescript("INSERT INTO synthetic VALUES(8);")
        with pytest.raises(sqlite3.OperationalError, match="too many attached databases"):
            conn.executescript("ATTACH ':memory:' AS side;")
        assert conn.execute("SELECT id FROM synthetic").fetchall() == [(7,)]
    assert database.read_bytes() == before


def test_helper_installs_no_python_sql_callbacks(monkeypatch, database):
    registrations = {
        "set_authorizer",
        "set_progress_handler",
        "set_trace_callback",
        "create_function",
        "create_collation",
        "create_aggregate",
        "create_window_function",
    }

    class CallbackFreeConnection(sqlite3.Connection):
        def __getattribute__(self, name):
            if name in registrations:
                raise AssertionError(f"helper attempted to register a Python callback: {name}")
            return super().__getattribute__(name)

    connect = sqlite3.connect
    with closing(connect(":memory:")) as baseline:
        functions = baseline.execute("PRAGMA function_list").fetchall()
        collations = baseline.execute("PRAGMA collation_list").fetchall()
    monkeypatch.setattr(sqlite3, "connect", lambda *a, **kw: connect(*a, **kw, factory=CallbackFreeConnection))
    with closing(open_readonly(database)) as conn:
        assert conn.execute("PRAGMA function_list").fetchall() == functions
        assert conn.execute("PRAGMA collation_list").fetchall() == collations
        assert conn.execute("SELECT id FROM synthetic").fetchall() == [(7,)]
    # sqlite3 exposes no getters for authorizer, progress, or trace handlers.
    # Interception above covers their registration, including cleared handlers.


def test_missing_file_is_not_created(tmp_path):
    path = tmp_path / "missing ї # ?.db"
    with pytest.raises(sqlite3.OperationalError):
        open_readonly(path)
    assert not path.exists()


def test_reader_settings_preserve_thread_and_transaction_contract(database):
    with closing(open_readonly(database, check_same_thread=False, isolation_level=None, timeout=0.25)) as conn:
        assert conn.isolation_level is None
        with ThreadPoolExecutor(max_workers=1) as pool:
            assert pool.submit(lambda: conn.execute("SELECT id FROM synthetic").fetchone()).result() == (7,)
        conn.execute("BEGIN")
        assert conn.in_transaction
        conn.rollback()


@pytest.mark.parametrize("stage", ["extension_loading", "query_only", "attachment_limit"])
def test_setup_failure_closes_connection(monkeypatch, database, stage):
    class BrokenConnection:
        closed = False

        def enable_load_extension(self, enabled):
            if stage == "extension_loading":
                raise RuntimeError("synthetic setup failure")

        def execute(self, sql):
            if stage == "attachment_limit":
                return
            raise RuntimeError("synthetic setup failure")

        def setlimit(self, category, limit):
            raise RuntimeError("synthetic setup failure")

        def close(self):
            self.closed = True

    broken = BrokenConnection()
    monkeypatch.setattr(sqlite3, "connect", lambda *args, **kwargs: broken)
    with pytest.raises(RuntimeError, match="synthetic setup failure"):
        open_readonly(database)
    assert broken.closed


def test_runtime_connection_discriminator_preserves_backend_identity(database):
    with closing(open_readonly(database)) as conn:
        assert is_sqlite_connection(conn)
    assert not is_sqlite_connection(object())


def test_shared_connection_makes_progress_without_python_callbacks(database):
    # A callback deadlock can hold the GIL, including the child's watchdog.
    # Only a separate interpreter can enforce the final timeout reliably.
    workload = textwrap.dedent("""\
        import json
        import os
        import sys
        import threading
        import time
        from scripts.lib.readonly_sqlite import open_readonly

        conn = open_readonly(sys.argv[1], check_same_thread=False)
        counts = [0] * 16
        errors = []
        start = threading.Barrier(17)
        stop = threading.Event()

        def work(worker):
            try:
                start.wait(timeout=5)
                while not stop.is_set():
                    sql = f"SELECT id FROM synthetic /* {worker}:{counts[worker]} */"
                    rows = conn.execute(sql).fetchall()
                    if rows != [(7,)]:
                        raise AssertionError(rows)
                    counts[worker] += 1
            except BaseException as exc:
                errors.append(repr(exc))

        threads = [threading.Thread(target=work, args=(i,), daemon=True) for i in range(16)]
        for thread in threads:
            thread.start()
        start.wait(timeout=5)
        deadline = time.monotonic() + 3
        last = 0
        last_progress = time.monotonic()
        while time.monotonic() < deadline:
            time.sleep(0.1)
            current = sum(counts)
            if current != last:
                last_progress = time.monotonic()
                last = current
            elif time.monotonic() - last_progress > 1.5:
                print("no progress", counts, flush=True)
                os._exit(2)
        stop.set()
        join_deadline = time.monotonic() + 2
        for thread in threads:
            thread.join(timeout=max(0, join_deadline - time.monotonic()))
        assert not any(thread.is_alive() for thread in threads), counts
        assert not errors, errors
        assert all(count > 0 for count in counts), counts
        conn.close()
        print(json.dumps({"queries": sum(counts), "workers": len(counts)}), flush=True)
    """)
    try:
        result = subprocess.run(
            [sys.executable, "-c", workload, str(database)],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
            timeout=12,
            check=False,
        )
    except subprocess.TimeoutExpired:
        pytest.fail("16-thread shared SQLite connection stalled: subprocess exceeded 12 seconds")
    assert result.returncode == 0, result.stdout + result.stderr



SHARED_READER_LOAD = """\
import faulthandler, random, sqlite3, sys, threading, time
from pathlib import Path

sys.path.insert(0, sys.argv[1])
from scripts.lib.readonly_sqlite import open_readonly

# A deadlock freezes every thread, so only faulthandler's C watchdog can end it.
faulthandler.dump_traceback_later(20, exit=True)
conn = open_readonly(Path(sys.argv[2]), check_same_thread=False)
conn.row_factory = sqlite3.Row
done = [0]

def reader(seed):
    rnd = random.Random(seed)
    while True:
        n = rnd.randint(1, 200)  # a new IN-list width misses the statement cache
        words = [f"w{rnd.randint(0, 5000)}" for _ in range(n)]
        sql = f"SELECT word, lemma FROM forms WHERE word IN ({','.join('?' * n)})"
        [dict(row) for row in conn.execute(sql, words).fetchall()]
        done[0] += 1

for seed in range(8):
    threading.Thread(target=reader, args=(seed,), daemon=True).start()
time.sleep(3)
print(f"completed {done[0]}", flush=True)
"""


def test_shared_connection_survives_concurrent_threads(tmp_path):
    """#10674: a connection shared across threads must not deadlock.

    A Python callback on the connection (the old ATTACH authorizer) runs while
    SQLite holds the connection mutex with the GIL released; another thread
    holding the GIL then waits for that mutex. Every thread blocks forever.
    """
    path = tmp_path / "forms.db"
    with closing(sqlite3.connect(path)) as conn:
        conn.execute("CREATE TABLE forms (word TEXT, lemma TEXT)")
        conn.executemany("INSERT INTO forms VALUES (?, ?)", [(f"w{i}", f"l{i % 97}") for i in range(5000)])
        conn.execute("CREATE INDEX forms_word ON forms(word)")
        conn.commit()
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-c", SHARED_READER_LOAD, str(root), str(path)],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, f"shared reader deadlocked:\n{result.stderr[-3000:]}"
    completed = int(result.stdout.split()[-1])
    assert completed > 100
