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

import sys
from functools import partial
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from wiki.sources_db import search_esum

needs_esum_data = pytest.mark.data_tier("sources", tables=("esum_etymology",))


@pytest.fixture(autouse=True)
def bound_esum_reader(request, monkeypatch):
    if request.node.get_closest_marker("data_tier"):
        path = request.getfixturevalue("data_store_factory")("sources", required_sqlite_tables=("esum_etymology",))
        monkeypatch.setitem(globals(), "search_esum", partial(search_esum, db_path=path))



def _joined_text(query: str, limit: int = 5) -> str:
    hits = search_esum(query, volume=1, limit=limit)
    return "\n".join(str(hit["etymology_text"]) for hit in hits)


# --- Registration (no data) and real-store query contracts ----------------


def test_search_esum_function_is_importable() -> None:
    """search_esum must be importable from wiki.sources_db regardless
    of whether data is loaded."""
    from wiki.sources_db import search_esum as _search_esum

    assert callable(_search_esum)


@needs_esum_data
def test_search_esum_nonexistent_word_returns_empty_list() -> None:
    """A made-up word never matches anything regardless of data state."""
    assert search_esum("хххх", volume=1, limit=3) == []


@needs_esum_data
def test_search_esum_sibir_is_outside_volume_one_scope() -> None:
    """The volume=1 filter excludes ``сибір`` (a vol. 5 entry).

    The DB holds all 6 volumes (А–Я); this asserts the volume filter works, not
    that vols 2–6 are absent.
    """
    assert search_esum("сибір", volume=1, limit=3) == []


@needs_esum_data
def test_search_esum_maty_is_outside_volume_one_scope() -> None:
    """The volume=1 filter excludes ``мати`` (a vol. 3 entry).

    The DB holds all 6 volumes (А–Я); this asserts the volume filter works, not
    that vols 2–6 are absent.
    """
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
