"""Fixture-backed measurement of fill_local vs enrich alignment (#5331)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from scripts.atlas import measure_fill_enrich_divergence as measure
from scripts.lexicon import enrich_manifest as em
from tests.helpers.sum20_store import canonical_sum20_store as canonical_sum20_store
from tests.helpers.sum20_store import seed_sum20_rows


@pytest.fixture
def cohort(tmp_path: Path, canonical_sum20_store: Path) -> dict[str, object]:
    entries = measure.build_synthetic_entries(50)
    sources = tmp_path / "sources.sqlite"
    measure.build_synthetic_sources(sources, entries)
    grac = measure.build_synthetic_grac(entries, puls_count=10)
    seed_sum20_rows(canonical_sum20_store, measure.build_synthetic_dictionary_rows(entries))
    return {
        "entries": entries,
        "sources": sources,
        "grac": grac,
        "dictionary_rows": measure.build_synthetic_dictionary_rows(entries),
    }


def test_fixed_path_reports_zero_cefr_and_relation_delta(cohort: dict[str, object]) -> None:
    """Post-#5331 fill_local path must match full enrich on the synthetic cohort."""
    result = measure.measure_divergence(
        cohort["entries"],  # type: ignore[arg-type]
        cohort["sources"],  # type: ignore[arg-type]
        cohort["grac"],  # type: ignore[arg-type]
        dictionary_rows=cohort["dictionary_rows"],  # type: ignore[arg-type]
    )

    assert result["schema"] == "fill-enrich-divergence-v2"
    assert result["lemmas_compared"] == 50
    assert result["cefr"]["fill_present"] == 50
    assert result["cefr"]["enrich_present"] == 50
    assert result["cefr"]["enrich_estimated"] == 40
    assert result["cefr"]["missing_on_fill_count"] == 0
    assert result["cefr"]["level_divergent_count"] == 0
    assert result["cefr"]["prepared_estimate_keys"] == 40

    for kind in measure.RELATION_KINDS:
        rel = result["relations"][kind]
        assert rel["edges_only_on_enrich"] == 0, kind
        assert rel["edges_only_on_fill"] == 0, kind
        assert rel["reciprocal_only_on_enrich"] == 0, kind
        assert rel["fill_local"]["edges"] == rel["enrich"]["edges"], kind


def test_fill_local_style_matches_enrich_entry_none_pointer_fallback(
    cohort: dict[str, object], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Legacy per-lemma maps must equal extractors enrich_entry uses when pointer_* is None."""
    entries = cohort["entries"]
    sources = cohort["sources"]
    assert isinstance(entries, list)
    assert isinstance(sources, Path)

    monkeypatch.setattr(em, "_vesum_valid_synonym", lambda term: bool(term))
    monkeypatch.setattr(em, "_vesum_word_analyses", lambda word: ((word, "noun"),))
    dictionary_rows = cohort["dictionary_rows"]
    assert isinstance(dictionary_rows, dict)
    monkeypatch.setattr(em, "_read_cached_slovnyk_rows", lambda lemma: dictionary_rows.get(lemma, {}))

    conn = sqlite3.connect(f"{sources.resolve().as_uri()}?mode=ro", uri=True)
    try:
        fill_maps = measure.fill_local_style_relations(
            conn, entries
        )
        for entry in entries:
            lemma = str(entry["lemma"])
            key = em._canonical_synonym_term(lemma)
            assert key
            assert fill_maps["synonym"].get(key, []) == em._definition_pointer_relations(
                conn, lemma
            )
            assert fill_maps["antonym"].get(key, []) == em._definition_antonym_relations(
                conn, lemma
            )
    finally:
        conn.close()
