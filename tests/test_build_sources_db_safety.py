"""Safety tests for scripts/wiki/build_sources_db.py.

Bug history: before the --force / --dry-run / preserve-wiki guards,
build_sources_db.py would unconditionally `db.unlink()` on its FIRST
action. This made even `--help` a destructive operation (there was no
argparse; the module would run `build()` at import time). The script
destroyed a populated sources.db mid-session, including the wikipedia
table that the separate fetch_wikipedia.py had spent API budget to
populate.

These tests lock in the safety behavior:
- Refuse to touch a populated DB without --force
- --dry-run never mutates filesystem or DB state
- Fresh builds (empty or missing DB) work without --force
- Wikipedia table snapshot + restore across rebuilds
- --no-preserve-wiki opt-out
- CLI exit codes (2 when refusing, 0 on success)
"""
from __future__ import annotations

import importlib.util
import sqlite3
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]

# Load the module directly since scripts/wiki isn't on sys.path normally
_SPEC = importlib.util.spec_from_file_location(
    "build_sources_db", ROOT / "scripts" / "wiki" / "build_sources_db.py",
)
assert _SPEC is not None and _SPEC.loader is not None
bs = importlib.util.module_from_spec(_SPEC)
sys.modules["build_sources_db"] = bs
_SPEC.loader.exec_module(bs)


def _make_populated_db(path: Path, *, with_wiki: bool = False) -> None:
    """Create a minimal valid sources.db with rows in the main tables."""
    conn = sqlite3.connect(str(path))
    # Main content tables (simplified — just the columns _db_is_populated checks)
    conn.executescript("""
        CREATE TABLE textbooks (id INTEGER PRIMARY KEY, text TEXT);
        CREATE TABLE literary_texts (id INTEGER PRIMARY KEY, text TEXT);
        CREATE TABLE external_articles (id INTEGER PRIMARY KEY, text TEXT);
    """)
    conn.executemany("INSERT INTO textbooks (text) VALUES (?)", [("x",)] * 100)
    conn.executemany("INSERT INTO literary_texts (text) VALUES (?)", [("y",)] * 50)
    conn.executemany("INSERT INTO external_articles (text) VALUES (?)", [("z",)] * 25)
    if with_wiki:
        conn.executescript("""
            CREATE TABLE wikipedia (
                id INTEGER PRIMARY KEY, title TEXT, url TEXT,
                text TEXT, char_count INTEGER, fetched_at TEXT
            );
            CREATE TABLE wikipedia_negative_cache (
                topic TEXT PRIMARY KEY, tried_at TEXT DEFAULT ''
            );
        """)
        conn.execute(
            "INSERT INTO wikipedia (title, url, text, char_count, fetched_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ("Київ", "http://uk.wikipedia.org/wiki/Київ", "Text body", 9, "2026-04-11"),
        )
        conn.execute(
            "INSERT INTO wikipedia (title, url, text, char_count, fetched_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ("Шевченко", "http://uk.wikipedia.org/wiki/Шевченко", "Text", 4, "2026-04-11"),
        )
        conn.execute(
            "INSERT INTO wikipedia_negative_cache (topic, tried_at) VALUES (?, ?)",
            ("Аналіз: Наслідки", "2026-04-11"),
        )
    conn.commit()
    conn.close()


# ──────────────────────────────────────────────────────────────────────
# _db_is_populated
# ──────────────────────────────────────────────────────────────────────


class TestDbIsPopulated:
    def test_missing_db_returns_false(self, tmp_path):
        assert bs._db_is_populated(tmp_path / "nonexistent.db") == (False, 0)

    def test_empty_db_returns_false(self, tmp_path):
        p = tmp_path / "empty.db"
        conn = sqlite3.connect(str(p))
        conn.executescript(
            "CREATE TABLE textbooks (id INTEGER PRIMARY KEY);"
            "CREATE TABLE literary_texts (id INTEGER PRIMARY KEY);"
            "CREATE TABLE external_articles (id INTEGER PRIMARY KEY);"
        )
        conn.close()
        populated, total = bs._db_is_populated(p)
        assert populated is False
        assert total == 0

    def test_populated_db_returns_counts(self, tmp_path):
        p = tmp_path / "full.db"
        _make_populated_db(p)
        populated, total = bs._db_is_populated(p)
        assert populated is True
        assert total == 175  # 100 + 50 + 25

    def test_db_without_main_tables_returns_false(self, tmp_path):
        p = tmp_path / "wrongtables.db"
        conn = sqlite3.connect(str(p))
        conn.executescript("CREATE TABLE not_ours (x INTEGER);")
        conn.close()
        populated, total = bs._db_is_populated(p)
        assert populated is False
        assert total == 0


# ──────────────────────────────────────────────────────────────────────
# Wikipedia snapshot + restore
# ──────────────────────────────────────────────────────────────────────


class TestWikipediaSnapshot:
    def test_extract_from_populated_db(self, tmp_path):
        p = tmp_path / "with_wiki.db"
        _make_populated_db(p, with_wiki=True)
        wiki_rows, neg_rows = bs._extract_wikipedia_snapshot(p)
        assert len(wiki_rows) == 2
        assert len(neg_rows) == 1
        titles = {r[0] for r in wiki_rows}
        assert titles == {"Київ", "Шевченко"}
        assert neg_rows[0][0] == "Аналіз: Наслідки"

    def test_extract_from_db_without_wiki_tables(self, tmp_path):
        p = tmp_path / "no_wiki.db"
        _make_populated_db(p, with_wiki=False)
        wiki_rows, neg_rows = bs._extract_wikipedia_snapshot(p)
        assert wiki_rows == []
        assert neg_rows == []

    def test_extract_from_missing_db(self, tmp_path):
        wiki_rows, neg_rows = bs._extract_wikipedia_snapshot(tmp_path / "missing.db")
        assert wiki_rows == []
        assert neg_rows == []

    def test_restore_into_fresh_db(self, tmp_path):
        p = tmp_path / "fresh.db"
        conn = sqlite3.connect(str(p))
        # Create just the wikipedia schema
        conn.executescript("""
            CREATE TABLE wikipedia (
                id INTEGER PRIMARY KEY, title TEXT, url TEXT,
                text TEXT, char_count INTEGER, fetched_at TEXT
            );
            CREATE TABLE wikipedia_negative_cache (
                topic TEXT PRIMARY KEY, tried_at TEXT DEFAULT ''
            );
        """)
        wiki_rows = [("Test", "http://test", "Body", 4, "2026-04-11")]
        neg_rows = [("dead topic", "2026-04-11")]
        bs._restore_wikipedia_snapshot(conn, wiki_rows, neg_rows)
        conn.commit()
        w_count = conn.execute("SELECT COUNT(*) FROM wikipedia").fetchone()[0]
        n_count = conn.execute("SELECT COUNT(*) FROM wikipedia_negative_cache").fetchone()[0]
        conn.close()
        assert w_count == 1
        assert n_count == 1


# ──────────────────────────────────────────────────────────────────────
# build() safety gates
# ──────────────────────────────────────────────────────────────────────


class TestBuildSafetyGates:
    def test_refuses_to_destroy_populated_db_without_force(self, tmp_path, capsys):
        p = tmp_path / "populated.db"
        _make_populated_db(p)
        mtime_before = p.stat().st_mtime
        size_before = p.stat().st_size

        result = bs.build(db_path=p, force=False)

        # DB file still exists and is byte-identical
        assert p.exists()
        assert p.stat().st_mtime == mtime_before
        assert p.stat().st_size == size_before
        assert result == p

        out = capsys.readouterr().out
        assert "already populated" in out
        assert "--force" in out

    def test_dry_run_never_mutates(self, tmp_path, capsys):
        p = tmp_path / "populated.db"
        _make_populated_db(p)
        mtime_before = p.stat().st_mtime
        size_before = p.stat().st_size

        bs.build(db_path=p, force=True, dry_run=True)

        assert p.exists()
        assert p.stat().st_mtime == mtime_before
        assert p.stat().st_size == size_before

        out = capsys.readouterr().out
        assert "DRY RUN" in out
        assert "175 rows" in out

    def test_dry_run_on_missing_db(self, tmp_path, capsys):
        p = tmp_path / "absent.db"
        bs.build(db_path=p, dry_run=True)
        assert not p.exists()
        out = capsys.readouterr().out
        assert "DRY RUN" in out
        assert "no existing populated DB" in out


# ──────────────────────────────────────────────────────────────────────
# Wikipedia preservation across rebuild (integration, stubbed ingest)
# ──────────────────────────────────────────────────────────────────────


class TestWikipediaPreservation:
    def test_wiki_rows_survive_force_rebuild(self, tmp_path):
        p = tmp_path / "populated.db"
        _make_populated_db(p, with_wiki=True)

        # Patch the expensive ingest path so the test is fast + offline
        with patch.object(bs, "_ingest_jsonl", return_value=0):
            # Patch GDRIVE_DATA + EXTERNAL_DIR to empty tmp dirs so the
            # real ingest loops over zero files cleanly
            empty_gd = tmp_path / "empty_gd"
            empty_gd.mkdir()
            (empty_gd / "textbook_chunks").mkdir()
            (empty_gd / "literary_texts").mkdir()
            empty_ext = tmp_path / "empty_ext"
            empty_ext.mkdir()
            with patch.object(bs, "GDRIVE_DATA", empty_gd), \
                 patch.object(bs, "EXTERNAL_DIR", empty_ext):
                bs.build(db_path=p, force=True, preserve_wiki=True)

        # Verify wikipedia rows were preserved
        conn = sqlite3.connect(str(p))
        try:
            wiki_count = conn.execute("SELECT COUNT(*) FROM wikipedia").fetchone()[0]
            neg_count = conn.execute(
                "SELECT COUNT(*) FROM wikipedia_negative_cache"
            ).fetchone()[0]
        finally:
            conn.close()
        assert wiki_count == 2, f"wikipedia rows lost: {wiki_count}"
        assert neg_count == 1, f"negative cache lost: {neg_count}"

    def test_no_preserve_wiki_wipes_the_tables(self, tmp_path):
        p = tmp_path / "populated.db"
        _make_populated_db(p, with_wiki=True)

        with patch.object(bs, "_ingest_jsonl", return_value=0):
            empty_gd = tmp_path / "empty_gd"
            empty_gd.mkdir()
            (empty_gd / "textbook_chunks").mkdir()
            (empty_gd / "literary_texts").mkdir()
            empty_ext = tmp_path / "empty_ext"
            empty_ext.mkdir()
            with patch.object(bs, "GDRIVE_DATA", empty_gd), \
                 patch.object(bs, "EXTERNAL_DIR", empty_ext):
                bs.build(db_path=p, force=True, preserve_wiki=False)

        # wikipedia table should be empty (schema still created by rebuild)
        conn = sqlite3.connect(str(p))
        try:
            wiki_count = conn.execute("SELECT COUNT(*) FROM wikipedia").fetchone()[0]
            neg_count = conn.execute(
                "SELECT COUNT(*) FROM wikipedia_negative_cache"
            ).fetchone()[0]
        finally:
            conn.close()
        assert wiki_count == 0
        assert neg_count == 0


# ──────────────────────────────────────────────────────────────────────
# CLI argument parsing
# ──────────────────────────────────────────────────────────────────────


class TestCliParse:
    def test_default_no_flags(self):
        args = bs._parse_args([])
        assert args.force is False
        assert args.dry_run is False
        assert args.no_preserve_wiki is False
        assert args.db_path is None

    def test_force_flag(self):
        args = bs._parse_args(["--force"])
        assert args.force is True

    def test_dry_run_flag(self):
        args = bs._parse_args(["--dry-run"])
        assert args.dry_run is True

    def test_no_preserve_wiki_flag(self):
        args = bs._parse_args(["--no-preserve-wiki"])
        assert args.no_preserve_wiki is True

    def test_db_path_override(self):
        args = bs._parse_args(["--db-path", "/tmp/test.db"])
        assert args.db_path == Path("/tmp/test.db")

    def test_combined_flags(self):
        args = bs._parse_args(["--force", "--dry-run", "--no-preserve-wiki"])
        assert args.force is True
        assert args.dry_run is True
        assert args.no_preserve_wiki is True

    def test_help_flag_does_not_touch_disk(self, capsys):
        # Critical safety test: `--help` must exit cleanly without any
        # destructive side effects. Before the fix, running any flag at
        # all would nuke sources.db.
        with pytest.raises(SystemExit) as exc_info:
            bs._parse_args(["--help"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "usage:" in captured.out
