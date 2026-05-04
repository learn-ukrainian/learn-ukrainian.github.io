"""Smoke tests for the ``search_esum`` MCP tool (issue #1662).

Tests that depend on a populated ``esum_etymology`` table are gated on
data presence. CI runners do not have the production ``data/sources.db``
populated — only the local-dev ingest step lands the data — so the
data-dependent tests are skipped there. The schema/registration tests
still run unconditionally and are sufficient for CI gating; the
data-content tests run on developer machines after ingestion.

To exercise the data-content tests locally:

    sqlite3 data/sources.db < migrations/add_esum_table.sql
    .venv/bin/python scripts/ingest/esum_load.py \\
        --jsonl data/processed/esum_vol1.jsonl \\
        --db data/sources.db
    .venv/bin/pytest tests/test_esum_search.py -v
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from wiki.sources_db import search_esum


def _esum_row_count() -> int:
    """Return the number of rows in the live ``esum_etymology`` table.

    Returns 0 if the DB or table is missing — those cases are valid
    skip-conditions for the data-content tests.
    """
    db_path = REPO / "data" / "sources.db"
    if not db_path.exists() or db_path.stat().st_size == 0:
        return 0
    try:
        conn = sqlite3.connect(db_path)
        try:
            cur = conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name='esum_etymology'"
            )
            if cur.fetchone() is None:
                return 0
            cur = conn.execute("SELECT COUNT(*) FROM esum_etymology")
            return cur.fetchone()[0]
        finally:
            conn.close()
    except sqlite3.Error:
        return 0


needs_esum_data = pytest.mark.skipif(
    _esum_row_count() == 0,
    reason=(
        "esum_etymology table empty or missing — populate it via "
        "migrations/add_esum_table.sql + scripts/ingest/esum_load.py "
        "to run data-content tests."
    ),
)


def _joined_text(query: str, limit: int = 5) -> str:
    hits = search_esum(query, volume=1, limit=limit)
    return "\n".join(str(hit["etymology_text"]) for hit in hits)


# --- Schema / registration tests (always run) -------------------------


def test_search_esum_function_is_importable() -> None:
    """search_esum must be importable from wiki.sources_db regardless
    of whether data is loaded."""
    from wiki.sources_db import search_esum as _search_esum

    assert callable(_search_esum)


def test_search_esum_nonexistent_word_returns_empty_list() -> None:
    """A made-up word never matches anything regardless of data state."""
    assert search_esum("хххх", volume=1, limit=3) == []


def test_search_esum_sibir_is_outside_volume_one_scope() -> None:
    """ЕСУМ vol. 1 covers А-Г only; ``сибір`` (vol. 5) must not match."""
    assert search_esum("сибір", volume=1, limit=3) == []


def test_search_esum_maty_is_outside_volume_one_scope() -> None:
    """ЕСУМ vol. 1 covers А-Г only; ``мати`` (vol. 3) must not match."""
    assert search_esum("мати", volume=1, limit=3) == []


# --- Data-content tests (skipped when esum_etymology is empty) -------


@needs_esum_data
def test_search_esum_berkut_returns_turkic_origin() -> None:
    hits = search_esum("беркут", volume=1, limit=3)
    assert [hit["lemma"] for hit in hits] == ["беркут"]
    assert "запозичення з тюркських мов" in hits[0]["etymology_text"]
    assert "тат. біркут" in hits[0]["etymology_text"]


@needs_esum_data
def test_search_esum_bereza_returns_indo_european_cognates() -> None:
    text = _joined_text("береза")
    assert "іє." in text
    assert "дінд." in text
    assert "лит." in text


@needs_esum_data
def test_search_esum_voda_returns_cross_slavic_and_proto_slavic_cognates() -> None:
    text = _joined_text("вода")
    assert "р. болг. вода" in text
    assert "стел, вода" in text
    assert "псл." in text
    assert "іє." in text
