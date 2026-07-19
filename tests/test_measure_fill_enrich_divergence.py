"""Fixture-backed measurement of fill_local vs enrich divergence (#5331)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from scripts.atlas import measure_fill_enrich_divergence as measure
from scripts.lexicon import enrich_manifest as em


@pytest.fixture
def cohort(tmp_path: Path) -> dict[str, object]:
    entries = measure.build_synthetic_entries(50)
    sources = tmp_path / "sources.sqlite"
    measure.build_synthetic_sources(sources, entries)
    grac = measure.build_synthetic_grac(entries, puls_count=10)
    return {"entries": entries, "sources": sources, "grac": grac}


def test_measure_reports_cefr_missing_on_fill(cohort: dict[str, object]) -> None:
    result = measure.measure_divergence(
        cohort["entries"],  # type: ignore[arg-type]
        cohort["sources"],  # type: ignore[arg-type]
        cohort["grac"],  # type: ignore[arg-type]
    )

    assert result["lemmas_compared"] == 50
    assert result["cefr"]["fill_present"] == 10  # PULS only after clear
    assert result["cefr"]["enrich_estimated"] > 0
    assert result["cefr"]["missing_on_fill_count"] == result["cefr"]["enrich_estimated"]
    assert result["cefr"]["missing_on_fill_count"] == 40
    assert result["cefr"]["prepared_estimate_keys"] == 40
    assert result["cefr"]["level_divergent_count"] == 0


def test_measure_reports_reciprocal_relation_delta(cohort: dict[str, object]) -> None:
    result = measure.measure_divergence(
        cohort["entries"],  # type: ignore[arg-type]
        cohort["sources"],  # type: ignore[arg-type]
        cohort["grac"],  # type: ignore[arg-type]
    )

    syn = result["relations"]["synonym"]
    ant = result["relations"]["antonym"]

    # Synonym pairs are bidirectional in sum11, so fill already has both directions
    # as forward edges; by_headword adds explicit direction=reciprocal copies.
    assert syn["enrich"]["edges"] > syn["fill_local"]["edges"]
    assert syn["edges_only_on_enrich"] > 0
    assert syn["reciprocal_only_on_enrich"] > 0

    # Antonym pointers are one-way in fixtures; enrich adds reciprocal edges.
    assert ant["fill_local"]["edges"] > 0
    assert ant["enrich"]["edges"] > ant["fill_local"]["edges"]
    assert ant["reciprocal_only_on_enrich"] == ant["fill_local"]["edges"]
    assert ant["edges_only_on_enrich"] == ant["reciprocal_only_on_enrich"]

    for kind in ("homonym", "paronym"):
        assert result["relations"][kind]["edges_only_on_enrich"] == 0


def test_fill_local_style_matches_enrich_entry_none_pointer_fallback(
    cohort: dict[str, object], monkeypatch: pytest.MonkeyPatch
) -> None:
    """fill_local-style maps must equal per-lemma extractors enrich_entry uses."""
    entries = cohort["entries"]
    sources = cohort["sources"]
    assert isinstance(entries, list)
    assert isinstance(sources, Path)

    monkeypatch.setattr(em, "_vesum_valid_synonym", lambda term: bool(term))
    monkeypatch.setattr(em, "_vesum_word_analyses", lambda word: ((word, "noun"),))

    conn = sqlite3.connect(f"file:{sources.resolve().as_posix()}?mode=ro", uri=True)
    try:
        has_sum11 = em._sum11_has_flag_columns(conn)
        fill_maps = measure.fill_local_style_relations(
            conn, entries, has_sum11_flags=has_sum11
        )
        for entry in entries:
            lemma = str(entry["lemma"])
            key = em._canonical_synonym_term(lemma)
            assert key
            assert fill_maps["synonym"].get(key, []) == em._definition_pointer_relations(
                conn, lemma, has_sum11_flags=has_sum11
            )
            assert fill_maps["antonym"].get(key, []) == em._definition_antonym_relations(
                conn, lemma, has_sum11_flags=has_sum11
            )
    finally:
        conn.close()


def test_run_default_measurement_cli_path_is_deterministic() -> None:
    first = measure.run_default_measurement(50)
    second = measure.run_default_measurement(50)
    # Drop non-semantic samples if present; full dict should match for hermetic run.
    assert first == second
    assert first["lemmas_compared"] == 50
    text = measure.format_summary(first)
    assert "missing_on_fill=40" in text
    assert "relations.antonym" in text


def test_cohort_size_guards() -> None:
    with pytest.raises(ValueError, match="at least 12"):
        measure.build_synthetic_entries(5)
    with pytest.raises(ValueError, match="≤50"):
        measure.build_synthetic_entries(51)


def test_json_roundtrip(tmp_path: Path, cohort: dict[str, object]) -> None:
    result = measure.measure_divergence(
        cohort["entries"],  # type: ignore[arg-type]
        cohort["sources"],  # type: ignore[arg-type]
        cohort["grac"],  # type: ignore[arg-type]
    )
    path = tmp_path / "out.json"
    path.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["issue"] == 5331
    assert loaded["cefr"]["missing_on_fill_count"] == 40
