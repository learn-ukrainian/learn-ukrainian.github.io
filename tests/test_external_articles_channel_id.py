"""Regression test for #1969 / 2026-05-14 corpus audit finding:
``build_sources_db.py`` was inserting only 8 columns into the
``external_articles`` table (chunk_id, url, url_normalized, title, text,
source_file, domain, char_count), leaving ``channel_id`` empty on every
row.

The audit found:
- All 1199 pre-existing ``external_articles`` rows had ``channel_id=''``.
- The Codex 2026-05-13 pohribnyi ingest emitted a per-record
  ``channel_id='pohribnyi-pronunciation'`` (hyphen) into the JSONL but the
  filename used ``pohribnyi_pronunciation`` (underscore). Using the
  filename stem keeps retrieval keys stable across ingestion runs.

These tests lock the fix in place:
- The SQL string includes ``channel_id``, ``speaker``, ``video_id``,
  ``publish_date``, ``duration_s``.
- A round-trip ingest populates ``channel_id`` from the filename stem.
- Audio/video metadata fields are populated when present in JSONL.
- Older blog-style records (no extra metadata) still land with empty
  audio/video fields and a populated ``channel_id``.
"""
from __future__ import annotations

import importlib.util
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_SPEC = importlib.util.spec_from_file_location(
    "build_sources_db",
    ROOT / "scripts" / "wiki" / "build_sources_db.py",
)
assert _SPEC is not None and _SPEC.loader is not None
bs = importlib.util.module_from_spec(_SPEC)
sys.modules["build_sources_db"] = bs
_SPEC.loader.exec_module(bs)


def _make_external_articles_db(path: Path) -> sqlite3.Connection:
    """Create a fresh DB with just the external_articles schema needed
    for this test — no FTS5 triggers, since we are exercising the INSERT
    layer, not retrieval.
    """
    conn = sqlite3.connect(str(path))
    conn.executescript(
        """
        CREATE TABLE external_articles (
            id INTEGER PRIMARY KEY,
            chunk_id TEXT NOT NULL DEFAULT '',
            url TEXT NOT NULL DEFAULT '',
            url_normalized TEXT NOT NULL DEFAULT '',
            title TEXT NOT NULL DEFAULT '',
            text TEXT NOT NULL DEFAULT '',
            source_file TEXT NOT NULL DEFAULT '',
            domain TEXT DEFAULT '',
            char_count INTEGER DEFAULT 0,
            channel_id TEXT DEFAULT '',
            speaker TEXT DEFAULT '',
            register_tag TEXT DEFAULT '',
            decolonization_tag TEXT DEFAULT '',
            quality_tier INTEGER DEFAULT 2,
            publish_date TEXT DEFAULT '',
            duration_s INTEGER DEFAULT 0,
            chunk_start_ts INTEGER,
            chunk_end_ts INTEGER,
            video_id TEXT DEFAULT ''
        );
        """
    )
    return conn


def test_ingest_external_articles_populates_channel_id_from_filename(tmp_path: Path) -> None:
    """Filename stem ``foo.jsonl`` must produce rows with channel_id='foo'."""
    ext_dir = tmp_path / "external_articles"
    ext_dir.mkdir()

    # Two records, neither carries channel_id in the record itself —
    # this matches the older blog-style JSONLs (imtgsh, realna_istoria,
    # etc.) on disk that were the source of the empty-channel_id rows.
    jsonl = ext_dir / "imtgsh.jsonl"
    jsonl.write_text(
        json.dumps({"url": "https://youtu.be/aaa", "title": "A", "text": "x" * 50}) + "\n"
        + json.dumps({"url": "https://youtu.be/bbb", "title": "B", "text": "y" * 60}) + "\n",
        encoding="utf-8",
    )

    db_path = tmp_path / "sources.db"
    conn = _make_external_articles_db(db_path)
    inserted = bs._ingest_external_articles(conn, ext_dir)
    conn.commit()
    assert inserted == 2

    rows = list(conn.execute(
        "SELECT channel_id, source_file, url, video_id, speaker FROM external_articles"
    ))
    assert {r[0] for r in rows} == {"imtgsh"}, (
        f"channel_id must match filename stem 'imtgsh', got {[r[0] for r in rows]}"
    )
    assert {r[1] for r in rows} == {"imtgsh"}
    # Older blog records do not carry video metadata, so those fields stay
    # empty even when channel_id is populated.
    assert all(r[3] == "" for r in rows), "older blog records must have empty video_id"
    assert all(r[4] == "" for r in rows), "older blog records must have empty speaker"
    conn.close()


def test_ingest_external_articles_surfaces_audio_metadata(tmp_path: Path) -> None:
    """Pohribnyi-shaped JSONL (with video_id/speaker/duration_s/...) must
    land all the extra metadata in the new columns."""
    ext_dir = tmp_path / "external_articles"
    ext_dir.mkdir()

    jsonl = ext_dir / "pohribnyi_pronunciation.jsonl"
    jsonl.write_text(
        json.dumps({
            "url": "https://www.youtube.com/watch?v=MlOzm7FQhtk",
            "title": "Side A vinyl rip",
            "text": "<lecture transcript>",
            "video_id": "MlOzm7FQhtk",
            "speaker": "Микола Погрібний",
            "publish_date": "2024-04-19",
            "duration_s": 1961,
            "char_count": 15649,
            # The record itself includes channel_id with hyphen — we
            # explicitly want the filename stem (underscore) to win.
            "channel_id": "pohribnyi-pronunciation",
        }) + "\n",
        encoding="utf-8",
    )

    db_path = tmp_path / "sources.db"
    conn = _make_external_articles_db(db_path)
    inserted = bs._ingest_external_articles(conn, ext_dir)
    conn.commit()
    assert inserted == 1

    row = conn.execute(
        """SELECT channel_id, source_file, speaker, video_id, publish_date,
                  duration_s, title FROM external_articles"""
    ).fetchone()
    # Canonical channel_id wins over per-record hyphenated variant.
    assert row[0] == "pohribnyi_pronunciation", (
        f"channel_id must come from filename stem (underscore), not the "
        f"JSONL record's hyphenated value. got {row[0]!r}"
    )
    assert row[1] == "pohribnyi_pronunciation"
    assert row[2] == "Микола Погрібний"
    assert row[3] == "MlOzm7FQhtk"
    assert row[4] == "2024-04-19"
    assert row[5] == 1961
    assert row[6] == "Side A vinyl rip"
    conn.close()


def test_ingest_external_articles_dedupes_urls(tmp_path: Path) -> None:
    """A URL repeated within or across JSONLs should only be inserted once."""
    ext_dir = tmp_path / "external_articles"
    ext_dir.mkdir()

    (ext_dir / "channel_a.jsonl").write_text(
        json.dumps({"url": "https://example.com/x", "title": "a1", "text": "x"}) + "\n"
        + json.dumps({"url": "https://example.com/x", "title": "a2-dup", "text": "x"}) + "\n",
        encoding="utf-8",
    )
    (ext_dir / "channel_b.jsonl").write_text(
        json.dumps({"url": "https://example.com/x", "title": "b-dup", "text": "x"}) + "\n"
        + json.dumps({"url": "https://example.com/y", "title": "b-new", "text": "y"}) + "\n",
        encoding="utf-8",
    )

    db_path = tmp_path / "sources.db"
    conn = _make_external_articles_db(db_path)
    inserted = bs._ingest_external_articles(conn, ext_dir)
    conn.commit()
    # x appears 3 times across two files; y appears once. Dedup keeps the
    # first-seen instance of each URL.
    assert inserted == 2
    rows = list(conn.execute("SELECT url, channel_id FROM external_articles ORDER BY url"))
    assert rows == [
        ("https://example.com/x", "channel_a"),
        ("https://example.com/y", "channel_b"),
    ]
    conn.close()


def test_ingest_external_articles_sql_includes_required_columns() -> None:
    """Substring guard: the function source must reference all required
    columns. A regression that drops one of these silently from the SQL
    is exactly the original bug — keep a literal-string check as a
    defense-in-depth signal."""
    src = (ROOT / "scripts" / "wiki" / "build_sources_db.py").read_text(encoding="utf-8")
    fn_start = src.find("def _ingest_external_articles")
    assert fn_start >= 0, "_ingest_external_articles helper must exist"
    # Take everything up to the next top-level def
    fn_end = src.find("\ndef ", fn_start + 1)
    fn_body = src[fn_start:fn_end] if fn_end > 0 else src[fn_start:]
    for col in (
        "channel_id",
        "speaker",
        "video_id",
        "publish_date",
        "duration_s",
        "source_file",
        "char_count",
    ):
        assert col in fn_body, f"_ingest_external_articles SQL/body must reference {col!r}"
