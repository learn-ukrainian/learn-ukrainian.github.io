"""Quarantine of СУМ-20 rows with unestablished provenance (#9609).

Rows are marked, never deleted, and every СУМ-20 reader skips a marked row.
"""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import pytest

from scripts.ingest import sum20_quarantine_unverified as quarantine_mod
from scripts.lexicon import sum20_lookup, thin_page_report
from scripts.wiki import sources_db
from scripts.wiki.sum20_official import (
    PARSER_VERSION,
    QUARANTINE_COLUMN,
    ensure_sum20_official_schema,
    ensure_sum20_quarantine_column,
    live_article_predicate,
    live_article_predicate_for,
)

_LEGACY_ARTICLES_SQL = """
CREATE TABLE sum20_articles (
    id INTEGER PRIMARY KEY, wordid INTEGER NOT NULL UNIQUE, normalized_lookup_key TEXT NOT NULL,
    headword TEXT NOT NULL, stressed_headword TEXT NOT NULL, pos TEXT NOT NULL DEFAULT '',
    grammar TEXT NOT NULL DEFAULT '', article_html TEXT NOT NULL, article_text TEXT NOT NULL,
    definition_text TEXT NOT NULL DEFAULT '', official_url TEXT NOT NULL, fetched_at TEXT NOT NULL,
    content_sha256 TEXT NOT NULL, parser_version TEXT NOT NULL
)
"""


def _insert(conn: sqlite3.Connection, wordid: int, key: str, parser_version: str) -> str:
    text = f"{key.upper()} — synthetic article {wordid}"
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    conn.execute(
        "INSERT INTO sum20_articles (wordid, normalized_lookup_key, headword, stressed_headword, article_html,"
        " article_text, definition_text, official_url, fetched_at, content_sha256, parser_version)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            wordid,
            key,
            key.upper(),
            key.upper(),
            f"<article>{text}</article>",
            text,
            text,
            f"https://sum20ua.com/?wordid={wordid}",
            "2026-09-15T00:00:00+00:00",
            digest,
            parser_version,
        ),
    )
    return digest


@pytest.fixture
def legacy_db(tmp_path: Path) -> tuple[Path, dict[int, str]]:
    """A sources.db built before the quarantine column: two official rows, two unverified rows."""
    db = tmp_path / "sources.db"
    conn = sqlite3.connect(db)
    conn.execute(_LEGACY_ARTICLES_SQL)
    ensure_sum20_official_schema(conn)  # adds the senses/citations tables; must add the column too
    conn.execute(f"ALTER TABLE sum20_articles DROP COLUMN {QUARANTINE_COLUMN}")
    _insert(conn, 10, "дух", PARSER_VERSION)
    _insert(conn, 11, "плин", PARSER_VERSION)
    expected = {
        300051: _insert(conn, 300051, "дух", quarantine_mod.UNVERIFIED_PARSER_VERSION),
        300060: _insert(conn, 300060, "плин", quarantine_mod.UNVERIFIED_PARSER_VERSION),
    }
    conn.commit()
    conn.close()
    return db, expected


def _columns(db: Path) -> set[str]:
    with sqlite3.connect(db) as conn:
        return {row[1] for row in conn.execute("PRAGMA table_info(sum20_articles)")}


def test_schema_migration_adds_the_column_once(legacy_db):
    db, _expected = legacy_db
    conn = sqlite3.connect(db)
    assert ensure_sum20_quarantine_column(conn) is True
    assert ensure_sum20_quarantine_column(conn) is False
    conn.close()
    assert QUARANTINE_COLUMN in _columns(db)


def test_predicate_is_true_for_a_table_without_the_column():
    assert live_article_predicate(["id", "wordid"]) == "1 = 1"
    assert live_article_predicate(["id", QUARANTINE_COLUMN], "a") == f"a.{QUARANTINE_COLUMN} = ''"


def test_dry_run_reports_and_writes_nothing(legacy_db):
    db, expected = legacy_db
    before = db.read_bytes()
    receipt = quarantine_mod.quarantine(db, apply=False, expected=expected)
    assert receipt["would_mark"] == 2
    assert receipt["column_present_before"] is False
    assert db.read_bytes() == before
    assert QUARANTINE_COLUMN not in _columns(db)


def test_apply_marks_exactly_the_expected_rows_and_deletes_nothing(legacy_db):
    db, expected = legacy_db
    receipt = quarantine_mod.quarantine(db, apply=True, expected=expected)
    assert receipt["marked"] == 2
    assert receipt["counts_after"] == receipt["counts_before"]
    with sqlite3.connect(db) as conn:
        rows = dict(conn.execute(f"SELECT wordid, {QUARANTINE_COLUMN} FROM sum20_articles").fetchall())
    assert rows == {10: "", 11: "", 300051: quarantine_mod.QUARANTINE_REASON, 300060: quarantine_mod.QUARANTINE_REASON}
    rerun = quarantine_mod.quarantine(db, apply=True, expected=expected)
    assert rerun["marked"] == 0
    assert rerun["already_quarantined"] == 2


@pytest.mark.parametrize("mutation", ["extra_row", "hash_drift"])
def test_unexpected_rows_refuse_and_write_nothing(legacy_db, mutation):
    db, expected = legacy_db
    expected = dict(expected)
    if mutation == "extra_row":
        with sqlite3.connect(db) as conn:
            _insert(conn, 300099, "ок", quarantine_mod.UNVERIFIED_PARSER_VERSION)
    else:
        expected[300051] = "0" * 64
    before = db.read_bytes()
    with pytest.raises(quarantine_mod.QuarantineError):
        quarantine_mod.quarantine(db, apply=True, expected=expected)
    assert db.read_bytes() == before


def test_cli_dry_run_is_the_default(legacy_db, monkeypatch, capsys):
    db, expected = legacy_db
    monkeypatch.setattr(quarantine_mod, "EXPECTED_ROWS", expected)
    monkeypatch.setattr(quarantine_mod.quarantine, "__defaults__", None)
    monkeypatch.setattr(quarantine_mod.quarantine, "__kwdefaults__", {"expected": expected})
    assert quarantine_mod.main(["--db", str(db)]) == 0
    assert '"mode": "dry-run"' in capsys.readouterr().out
    assert QUARANTINE_COLUMN not in _columns(db)


@pytest.fixture
def quarantined_db(legacy_db) -> Path:
    db, expected = legacy_db
    quarantine_mod.quarantine(db, apply=True, expected=expected)
    return db


def test_query_sum20_excludes_quarantined_rows(quarantined_db):
    records = sources_db.query_sum20("дух", db_path=quarantined_db)
    assert [record["source_record_id"] for record in records] == ["10"]


def test_lookup_sum20_cached_excludes_quarantined_rows(quarantined_db):
    conn = sum20_lookup._get_db(quarantined_db)
    try:
        assert [row["wordid"] for row in sum20_lookup.lookup_sum20_cached("плин", conn)] == [11]
    finally:
        conn.close()


def test_lookup_read_path_opens_read_only(quarantined_db):
    conn = sum20_lookup._get_db(quarantined_db)
    try:
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            conn.execute("DELETE FROM sum20_articles")
    finally:
        conn.close()


def test_lookup_on_a_missing_database_returns_nothing_and_creates_no_file(tmp_path):
    missing = tmp_path / "absent.db"
    assert sum20_lookup.lookup_sum20_articles("дух", missing) == []
    assert not missing.exists()


def test_read_only_uri_caller_cannot_create_a_missing_database(tmp_path):
    missing = tmp_path / "absent.db"
    with pytest.raises(sqlite3.OperationalError):
        sum20_lookup._get_db(missing.as_uri(), write=False)
    assert not missing.exists()


def test_read_only_uri_caller_cannot_write(quarantined_db):
    conn = sum20_lookup._get_db(quarantined_db.as_uri(), write=False)
    try:
        conn.execute("PRAGMA query_only = OFF")
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            conn.execute("DELETE FROM sum20_articles")
    finally:
        conn.close()


@pytest.mark.parametrize("mode", ["rw", "rwc", "memory", "%72w"])
def test_read_only_uri_caller_refuses_a_writable_mode(quarantined_db, mode):
    with pytest.raises(ValueError, match="refuses a URI"):
        sum20_lookup._get_db(f"{quarantined_db.as_uri()}?mode={mode}", write=False)


def test_read_only_uri_keeps_other_parameters_and_an_explicit_mode_ro(quarantined_db):
    for uri in (f"{quarantined_db.as_uri()}?mode=ro", f"{quarantined_db.as_uri()}?cache=shared"):
        conn = sum20_lookup._get_db(uri, write=False)
        try:
            conn.execute("PRAGMA query_only = OFF")
            with pytest.raises(sqlite3.OperationalError, match="readonly"):
                conn.execute("DELETE FROM sum20_articles")
            assert conn.execute("SELECT COUNT(*) FROM sum20_articles").fetchone()[0] > 0
        finally:
            conn.close()


def test_path_branch_still_opens_read_only_and_creates_no_file(quarantined_db, tmp_path):
    conn = sum20_lookup._get_db(quarantined_db)
    try:
        conn.execute("PRAGMA query_only = OFF")
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            conn.execute("DELETE FROM sum20_articles")
    finally:
        conn.close()
    missing = tmp_path / "absent.db"
    with pytest.raises(sqlite3.OperationalError):
        sum20_lookup._get_db(missing)
    assert not missing.exists()


def test_thin_page_report_opens_a_path_with_uri_metacharacters_read_only(quarantined_db, tmp_path):
    odd = tmp_path / "a#b?c"
    odd.mkdir()
    copy = odd / "sources.db"
    copy.write_bytes(quarantined_db.read_bytes())
    conn = thin_page_report._connect_ro(copy)
    try:
        assert conn.execute("SELECT COUNT(*) FROM sum20_articles").fetchone()[0] > 0
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            conn.execute("DELETE FROM sum20_articles")
    finally:
        conn.close()


def test_thin_page_probe_excludes_quarantined_keys(quarantined_db):
    sql, _sections = thin_page_report.SOURCES_DB_PROBES["sources.db:sum20"]
    with sqlite3.connect(quarantined_db) as conn:
        conn.execute(f"UPDATE sum20_articles SET {QUARANTINE_COLUMN} = 'x' WHERE wordid = 10")
        keys = {row[0] for row in conn.execute(sql.replace("{sum20_live}", live_article_predicate_for(conn)))}
    assert keys == {"плин"}
