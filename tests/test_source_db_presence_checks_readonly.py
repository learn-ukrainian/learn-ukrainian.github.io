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

import tests.conftest as project_conftest
import tests.test_atlas_conformance as atlas
import tests.test_esum_search as esum
import tests.test_reattribute_ukrlib as ukrlib
import tests.test_vocab_coverage as vocab
from scripts.audit._judge_eval_lib import ANTONENKO_SOURCE
from scripts.lib.readonly_sqlite import open_readonly
from tests.audit import test_antonenko_prose_narrowing as antonenko
from tests.helpers import source_db_write_guard as guard
from tests.mcp import test_ua_gec_search as ua_gec


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
        connection.execute("INSERT INTO textbooks (source_file) VALUES (?)", (ANTONENKO_SOURCE,))
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


def test_presence_checks_open_readonly_copy_and_skip_when_absent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
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
    monkeypatch.setattr(antonenko, "DB", copy)
    monkeypatch.setattr(ua_gec, "_DB_PATH", copy)
    monkeypatch.setattr(esum, "_SOURCES_DB", copy)
    monkeypatch.setattr(ukrlib, "_SOURCES_DB", copy)
    monkeypatch.setattr(atlas, "SOURCES_PATH", copy)
    monkeypatch.setattr(vocab.vocab_coverage, "VESUM_DB_PATH", copy)
    monkeypatch.setenv("LEARN_UKRAINIAN_TEST_DATA_ROOT", str(root))

    assert antonenko._antonenko_corpus_present() is True
    assert ua_gec._ua_gec_table_present() is True
    assert esum._esum_row_count() == 1
    assert ukrlib._literary_corpus_available() is True
    assert atlas._sources_has_grinchenko_table() is True
    assert vocab._vesum_has_sound_lemma() is True
    found = project_conftest._require_data_artifact(
        "data/sources.db",
        required_sqlite_tables=(
            "textbooks",
            "ua_gec_errors_fts",
            "esum_etymology",
            "literary_texts",
            "grinchenko",
        ),
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
    monkeypatch.setattr(antonenko, "DB", absent)
    monkeypatch.setattr(ua_gec, "_DB_PATH", absent)
    monkeypatch.setattr(esum, "_SOURCES_DB", absent)
    monkeypatch.setattr(ukrlib, "_SOURCES_DB", absent)
    monkeypatch.setattr(atlas, "SOURCES_PATH", absent)
    monkeypatch.setattr(vocab.vocab_coverage, "VESUM_DB_PATH", absent)
    assert antonenko._antonenko_corpus_present() is False
    assert ua_gec._ua_gec_table_present() is False
    assert esum._esum_row_count() == 0
    assert ukrlib._literary_corpus_available() is False
    assert atlas._sources_has_grinchenko_table() is False
    assert vocab._vesum_has_sound_lemma() is False
    empty_vesum = tmp_path / "empty-vesum.db"
    empty_vesum.write_bytes(b"")
    monkeypatch.setattr(vocab.vocab_coverage, "VESUM_DB_PATH", empty_vesum)
    assert vocab._vesum_has_sound_lemma() is False

    empty = tmp_path / "empty-root"
    empty.mkdir()
    monkeypatch.setenv("LEARN_UKRAINIAN_TEST_DATA_ROOT", str(empty))
    monkeypatch.setattr("scripts.guardrails.worktree_containment.resolve_main_root", lambda _repo: empty)
    with pytest.raises(pytest.skip.Exception, match=r"requires data/sources\.db"):
        project_conftest._require_data_artifact("data/sources.db", required_sqlite_tables=("textbooks",))
    assert calls[seen:] == []
    assert copy.read_bytes() == before
