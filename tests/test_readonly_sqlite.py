"""Synthetic fixtures for the shared SQLite reader boundary (#9609, #9662)."""

from __future__ import annotations

import sqlite3
import subprocess
import sys
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


def test_attach_and_detach_are_refused(database, tmp_path):
    attached = tmp_path / "attachment.db"
    with closing(open_readonly(database)) as conn:
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


def test_setup_failure_closes_connection(monkeypatch, database):
    class BrokenConnection:
        closed = False

        def execute(self, sql):
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
