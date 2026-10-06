"""Synthetic fixtures for the shared SQLite reader boundary (#9609, #9662)."""

from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing

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
        for sql, args in (("ATTACH DATABASE ? AS side", (str(attached),)), ("DETACH DATABASE main", ())):
            with pytest.raises(sqlite3.DatabaseError, match="not authorized"):
                conn.execute(sql, args)
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
