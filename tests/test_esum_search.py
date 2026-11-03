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


# --- Registration (no data) and real-store query contracts ----------------


@needs_esum_data
def test_search_esum_sibir_is_outside_volume_one_scope() -> None:
    """The volume=1 filter excludes ``сибір`` (a vol. 5 entry).

    The DB holds all 6 volumes (А–Я); this asserts the volume filter works, not
    that vols 2–6 are absent.
    """
    assert search_esum("сибір", volume=1, limit=3) == []


# --- Data-content tests (skipped when esum_etymology is empty) -------


@needs_esum_data
def test_search_esum_berkut_returns_turkic_origin() -> None:
    """A clean volume-1 Turkic-origin entry is returned with its etymology.

    The test keeps its historical name (its node id is pinned in the data-tier
    selection) but no longer queries "беркут": that row's OCR text interleaves a
    neighbouring column and carries the `\\У` mojibake marker, so since
    55254d8acd46 ("filter garbled ESUM etymologies") ``search_esum`` withholds it by
    design. "баклан" is a clean volume-1 row with the same Turkic-origin claim.
    """
    hits = search_esum("баклан", volume=1, limit=3)
    assert hits[0]["lemma"] == "баклан"
    assert "запозичення з тюркських мов" in hits[0]["etymology_text"]
    assert "тат. ст. баклан" in hits[0]["etymology_text"]
