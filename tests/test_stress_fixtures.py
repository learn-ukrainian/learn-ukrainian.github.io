"""Source fixtures exercise ULIF admission and its explicitly labelled fallback."""

import sqlite3

import pytest

from scripts.verification import stress
from scripts.wiki import sources_db


def test_captured_ulif_snapshot_is_readonly_and_joins_frozen_identity(ulif_stress_db):
    with pytest.raises(sqlite3.OperationalError, match="readonly"):
        sources_db._get_conn().execute("DELETE FROM ulif_forms")
    result = stress.verify_stress("переймімо", pos="VERB", tags="Mood=Imp,Number=Plur")
    assert result["status"] == "ok"
    assert result["stress_source"] == "ulif"
    assert [m["stressed_form"] for m in result["matches"]] == ["переймі́мо"]
    assert result["matches"][0]["vesum_analyses"] == [
        {"lemma": "перейняти", "pos": "verb", "tags": "verb:perf:impr:p:1"}
    ]
    assert result["matches"][0]["evidence"]
    # Capitalized lookup merges analyses internally; it must not mutate the
    # frozen lowercase source list used by a later lookup in the same test.
    before = stress._vesum_lookup("мене")
    stress.verify_stress("Мене", lemma="я")
    assert stress._vesum_lookup("мене") == before


def test_stress_unit_default_has_no_ambient_ulif_store():
    assert sources_db.ulif_stress_build() == {"state": "unavailable"}
    result = stress.verify_stress("село")
    assert result["stress_source"] == "trie"
    assert {m["source"] for m in result["matches"]} == {"trie"}


def test_missing_ulif_keeps_trie_label_and_withholds_ambiguous_distractor(ulif_stress_db, monkeypatch):
    from scripts.audit.generate_practice_deck import _imperative_display

    def missing():
        raise FileNotFoundError("test source unavailable")

    monkeypatch.setattr(sources_db, "_get_conn", missing)
    result = stress.verify_stress("переймемо", pos="VERB", tags="Mood=Ind,Number=Plur")
    assert result["status"] == "ambiguous"
    assert result["stress_source"] == "trie"
    assert {m["source"] for m in result["matches"]} == {"trie"}
    _imperative_display.cache_clear()
    try:
        assert _imperative_display("переймемо", "p", mood="Ind") is None
    finally:
        _imperative_display.cache_clear()
