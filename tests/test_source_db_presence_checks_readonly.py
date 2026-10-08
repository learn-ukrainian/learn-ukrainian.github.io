"""Presence checks open a repository source database read-only (#9662).

The copy lives under a path whose name contains ``?`` and ``#``. A raw
``file:{path}?mode=ro`` string drops ``mode=ro`` at the ``#``, so the
source-database guard would refuse it. ``open_readonly`` percent-encodes
the path first.
"""

from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

import pytest

from scripts.lib.readonly_sqlite import open_readonly
from scripts.storage.topology import StoreBinding
from tests.helpers import source_db_write_guard as guard


def _write_source_shaped_db(path: Path) -> None:
    connection = sqlite3.connect(path)
    try:
        connection.executescript(
            """
            CREATE TABLE textbooks (source_file TEXT);
            CREATE TABLE ua_gec_errors_fts (body TEXT);
            CREATE TABLE esum_etymology (headword TEXT);
            CREATE TABLE literary_texts (author TEXT);
            CREATE TABLE grinchenko (lemma TEXT);
            CREATE TABLE vesum (form TEXT, lemma TEXT);
            """
        )
        connection.execute("INSERT INTO textbooks (source_file) VALUES (?)", ("antonenko-davydovych-yak-my-hovorymo",))
        connection.execute("INSERT INTO esum_etymology (headword) VALUES ('x')")
        connection.execute("INSERT INTO literary_texts (author) VALUES ('x')")
        connection.execute("INSERT INTO grinchenko (lemma) VALUES ('x')")
        connection.execute("INSERT INTO vesum (form, lemma) VALUES ('звук', 'звук')")
        connection.execute("INSERT INTO vesum (form, lemma) VALUES ('звуки', 'звук')")
        connection.commit()
    finally:
        connection.close()


def _assert_readonly_open(database: object, copy: Path) -> None:
    assert isinstance(database, str)
    parts = urlsplit(database)
    assert parts.scheme == "file"
    assert parse_qs(parts.query).get("mode") == ["ro"]
    assert Path(unquote(parts.path)).resolve() == copy.resolve()


def test_presence_checks_open_readonly_copy_and_skip_when_absent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, data_store_factory) -> None:
    shaped = tmp_path / "shaped.sqlite"
    _write_source_shaped_db(shaped)
    root = tmp_path / "root?#x"
    data = root / "data"
    data.mkdir(parents=True)
    copy = data / "sources.db"
    shutil.copy2(shaped, copy)
    copy.chmod(0o444)
    before = copy.read_bytes()
    assert (copy.stat().st_mode & 0o777) == 0o444
    # The unencoded form is not a read-only URI once ``#`` starts a fragment.
    assert parse_qs(urlsplit(f"file:{copy}?mode=ro").query).get("mode") != ["ro"]

    monkeypatch.setattr(guard, "DATA_ROOTS", frozenset({data.resolve()}))
    with pytest.raises(pytest.fail.Exception, match="Writable SQLite open"):
        sqlite3.connect(copy)
    assert copy.read_bytes() == before

    calls: list[object] = []
    wrapped = sqlite3.connect

    def spy(database: object, *args: object, **kwargs: object) -> sqlite3.Connection:
        calls.append(database)
        return wrapped(database, *args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", spy)
    binding = StoreBinding("sources", copy)
    # Six former module-level presence probes now exercise one factory.
    for table in ("textbooks", "ua_gec_errors_fts", "esum_etymology", "literary_texts", "grinchenko", "vesum"):
        assert data_store_factory("sources", binding=binding, required_sqlite_tables=(table,)) == copy
    found = data_store_factory(
        "sources", binding=binding,
        required_sqlite_tables=("textbooks", "ua_gec_errors_fts", "esum_etymology", "literary_texts", "grinchenko"),
    )
    assert found.resolve() == copy.resolve()
    with open_readonly(copy) as connection:
        with pytest.raises(sqlite3.OperationalError):
            connection.execute("INSERT INTO textbooks (source_file) VALUES ('mutated')")

    assert len(calls) == 8
    for database in calls:
        _assert_readonly_open(database, copy)
    assert copy.read_bytes() == before
    assert not copy.with_name(copy.name + "-wal").exists()
    assert not copy.with_name(copy.name + "-shm").exists()

    absent = data / "absent.db"
    seen = len(calls)
    with pytest.raises(pytest.skip.Exception, match="store=sources reason=store_missing"):
        data_store_factory("sources", binding=StoreBinding("sources", absent), required_sqlite_tables=("textbooks",))
    assert calls[seen:] == []
    assert copy.read_bytes() == before
