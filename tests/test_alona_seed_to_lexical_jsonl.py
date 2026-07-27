"""Alona v5 seed → ADR-017 lexical JSONL converter + projection fixture."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from scripts.atlas import alona_seed_to_lexical_jsonl as convert
from scripts.atlas import lexical_projection as projection

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "atlas" / "alona_v5_sample.jsonl"
ROOT = Path(__file__).resolve().parents[1]
REAL_VESUM = ROOT / "data" / "vesum.db"


def test_entry_slug_is_stable_for_ukrainian() -> None:
    assert convert.entry_slug("Справедливий") == "справедливий"
    assert convert.entry_slug("Відписатися від") == "відписатися-від"


def test_convert_seed_emits_required_record_types() -> None:
    assert FIXTURE.is_file(), "fixture missing"
    records = convert.convert_seed_file(FIXTURE)
    types = {r["record_type"] for r in records}
    assert "practice_deck" in types
    assert "lemma_entry" in types
    assert "sense" in types
    # sample includes ok rows with provenance
    assert "source" in types
    assert "attestation" in types
    assert "practice_deck_item" in types
    # gloss-only row (Орендодавець) still has lemma+sense, no attestation forced
    lemmas = [r for r in records if r["record_type"] == "lemma_entry"]
    assert any(r["lemma"] == "Орендодавець" for r in lemmas)


@pytest.mark.skipif(not REAL_VESUM.is_file(), reason="vesum.db not available in worktree")
def test_sample_seed_round_trips_through_projection(tmp_path: Path) -> None:
    """End-to-end: Alona sample → ADR JSONL → SQLite projection with FKs ON."""
    lexical_path = tmp_path / "lexical.jsonl"
    db_path = tmp_path / "atlas-v2.db"
    export_path = tmp_path / "export.jsonl"

    records = convert.convert_seed_file(FIXTURE)
    convert.write_jsonl(lexical_path, records)

    result = projection.build_projection(lexical_path, db_path, vesum_db=REAL_VESUM)
    projection.export_projection(db_path, export_path)

    assert result.accepted_records >= 1
    with sqlite3.connect(db_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        lemma_count = connection.execute("SELECT COUNT(*) FROM lemma_entries").fetchone()[0]
        sense_count = connection.execute("SELECT COUNT(*) FROM senses").fetchone()[0]
        assert lemma_count >= 5
        assert sense_count == lemma_count
        att_count = connection.execute("SELECT COUNT(*) FROM attestations").fetchone()[0]
        # at least the ok fixture rows with sentences should project
        assert att_count >= 1
        assert connection.execute("SELECT type FROM sqlite_master WHERE name='articles'").fetchone()[0] == "view"

    # export is non-empty canonical JSONL
    exported = [json.loads(line) for line in export_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert exported
    assert all("record_type" in row for row in exported)
