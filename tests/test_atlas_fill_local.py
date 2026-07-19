from __future__ import annotations

import json
import os
import socket
import sqlite3
from pathlib import Path
from typing import Any

from scripts.atlas import atlas_db, fill_local
from scripts.atlas import measure_fill_enrich_divergence as measure
from scripts.lexicon import enrich_manifest


def _build_atlas_db(tmp_path: Path, entries: list[dict[str, Any]] | None = None) -> Path:
    if entries is None:
        entries = [
            {
                "lemma": "прапор",
                "url_slug": "прапор",
                "gloss": "flag",
                "pos": "noun",
                "primary_source": "fixture",
                "enrichment": {
                    "meaning": {
                        "definitions": ["стяг"],
                        "source": "fixture meaning",
                    }
                },
            },
            {
                "lemma": "бігти",
                "url_slug": "бігти",
                "gloss": "run",
                "pos": "verb",
                "primary_source": "fixture",
            },
            {
                "lemma": "сліпа зона",
                "url_slug": "сліпа-зона",
                "gloss": "blind spot",
                "pos": "noun",
                "primary_source": "fixture",
            },
        ]
    manifest = {"entries": entries}
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    db_path = tmp_path / "atlas.db"
    atlas_db.migrate_manifest(manifest_path, db_path)
    return db_path


def _empty_sources_db(tmp_path: Path) -> Path:
    path = tmp_path / "sources.db"
    sqlite3.connect(path).close()
    return path


def _rows(db_path: Path) -> dict[tuple[str, str], sqlite3.Row]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = {
        (row["slug"], row["section"]): row
        for row in conn.execute(
            "SELECT slug, section, payload_json, source, phase FROM enrichment ORDER BY slug, section"
        )
    }
    conn.close()
    return rows


def test_section_mapping_writes_local_rows_and_honest_uncovered(tmp_path, monkeypatch):
    db_path = _build_atlas_db(tmp_path)
    sources_db_path = _empty_sources_db(tmp_path)

    def fake_enrich_entry(entry, conn, kaikki_lookup, *, has_sum11_flags, **_kwargs):
        if entry["lemma"] == "прапор":
            entry["heritage_status"] = {
                "classification": "standard",
                "attestations": [{"source": "VESUM"}],
                "\u00a76_note": {"note": "native alternative", "source": ["Антоненко"]},
            }
            entry["pronunciation"] = {"ipa": "[ˈprɑpɔr]", "source": "Kaikki"}
            entry["sections"] = {
                "synonyms": {"items": ["стяг"], "source": "fixture synonyms"},
                "antonyms": {"items": ["безпрапорність"], "source": "fixture antonyms"},
                "idioms": {"items": ["під прапором"], "source": "fixture idioms"},
            }
            entry["enrichment"] = {
                "stress": {"form": "пра́пор", "source": "stress fixture"},
                "morphology": {"pos": "noun", "form_count": 7, "source": "VESUM"},
                "translation": {"en": ["flag"], "source": "Kaikki"},
                "sources": ["not a section"],
            }
        return True

    monkeypatch.setattr(fill_local, "enrich_entry", fake_enrich_entry)

    result = fill_local.fill_local(db_path, sources_db_path, tmp_path / "missing-kaikki.json")
    rows = _rows(db_path)

    assert result.considered == 3
    assert json.loads(rows[("прапор", "meaning")]["payload_json"]) == {
        "definitions": ["стяг"],
        "source": "fixture meaning",
    }
    assert rows[("прапор", "meaning")]["phase"] == "migration"
    assert json.loads(rows[("прапор", "synonyms")]["payload_json"])["items"] == ["стяг"]
    assert rows[("прапор", "synonyms")]["phase"] == "local"
    assert rows[("прапор", "calque_note")]["source"] == "Антоненко"
    assert rows[("прапор", "pronunciation")]["source"] == "Kaikki"
    assert ("сліпа-зона", "wiki_reference") not in rows
    assert ("сліпа-зона", "synonyms") not in rows
    assert json.loads(rows[("сліпа-зона", "cefr")]["payload_json"]) == {}
    assert rows[("сліпа-зона", "cefr")]["phase"] == "uncovered"


def test_idempotent_rerun_skips_existing_sections(tmp_path, monkeypatch):
    db_path = _build_atlas_db(tmp_path)
    sources_db_path = _empty_sources_db(tmp_path)

    def fake_enrich_entry(entry, conn, kaikki_lookup, *, has_sum11_flags, **_kwargs):
        entry["enrichment"] = {"stress": {"form": f"{entry['lemma']}́", "source": "stress fixture"}}
        entry["heritage_status"] = {"classification": "unknown"}
        return True

    monkeypatch.setattr(fill_local, "enrich_entry", fake_enrich_entry)

    first = fill_local.fill_local(db_path, sources_db_path, tmp_path / "missing-kaikki.json")
    first_count = len(_rows(db_path))
    second = fill_local.fill_local(db_path, sources_db_path, tmp_path / "missing-kaikki.json")
    second_count = len(_rows(db_path))

    assert first.inserted > 0
    assert second.inserted == 0
    assert second.skipped_existing > 0
    assert second_count == first_count


def test_refresh_replaces_existing_section_payload(tmp_path, monkeypatch):
    db_path = _build_atlas_db(tmp_path)
    sources_db_path = _empty_sources_db(tmp_path)

    def fake_enrich_entry(entry, conn, kaikki_lookup, *, has_sum11_flags, **_kwargs):
        entry["enrichment"] = {"meaning": {"definitions": ["оновлено"], "source": "refresh fixture"}}
        entry["heritage_status"] = {"classification": "unknown"}
        return True

    monkeypatch.setattr(fill_local, "enrich_entry", fake_enrich_entry)

    fill_local.fill_local(db_path, sources_db_path, tmp_path / "missing-kaikki.json", slug="прапор", refresh=True)
    rows = _rows(db_path)

    assert json.loads(rows[("прапор", "meaning")]["payload_json"]) == {
        "definitions": ["оновлено"],
        "source": "refresh fixture",
    }
    assert rows[("прапор", "meaning")]["phase"] == "local"


def test_phase1_offline_guard_blocks_slovnyk_wikipedia_and_grac_network(tmp_path, monkeypatch):
    db_path = _build_atlas_db(tmp_path)
    sources_db_path = _empty_sources_db(tmp_path)
    monkeypatch.setenv("LEXICON_SLOVNYK_OFFLINE", "0")

    def fail_network(*args, **kwargs):
        raise AssertionError("Phase-1 local fill attempted a network call")

    monkeypatch.setattr(enrich_manifest.requests, "get", fail_network)
    monkeypatch.setattr(socket, "socket", fail_network)
    monkeypatch.setattr(enrich_manifest, "WIKI_REFERENCE_CACHE", tmp_path / "wiki_reference.json")
    monkeypatch.setattr(enrich_manifest, "_WIKI_REFERENCE_CACHE_DATA", None)
    monkeypatch.setattr(enrich_manifest, "_WIKI_REFERENCE_CACHE_DIRTY", False)
    enrich_manifest.query_wikipedia.cache_clear()

    def fake_enrich_entry(entry, conn, kaikki_lookup, *, has_sum11_flags, **_kwargs):
        assert enrich_manifest._fetch_slovnyk_entry("немає", "немає", "vts") is None
        assert enrich_manifest._cached_wikipedia_summary("Тестова стаття без кешу") is None
        assert enrich_manifest._fetch_grac_frequency_batch(["немає"]) == {"немає": None}
        entry["enrichment"] = {"stress": {"form": "нема́є", "source": "stress fixture"}}
        entry["heritage_status"] = {"classification": "unknown"}
        return True

    monkeypatch.setattr(fill_local, "enrich_entry", fake_enrich_entry)

    fill_local.fill_local(db_path, sources_db_path, tmp_path / "missing-kaikki.json", slug="бігти")
    assert os.environ["LEXICON_SLOVNYK_OFFLINE"] == "0"


def test_fill_local_prepares_cefr_and_passes_closed_pointer_maps(tmp_path, monkeypatch):
    """#5331: fill_local must prepare CEFR quantiles and pass reciprocal pointer maps."""
    entries = measure.build_synthetic_entries(20)
    db_path = _build_atlas_db(tmp_path, entries)
    sources_db_path = tmp_path / "sources.db"
    measure.build_synthetic_sources(sources_db_path, entries)
    grac = measure.build_synthetic_grac(entries, puls_count=10)

    previous_cefr = dict(enrich_manifest._CEFR_ESTIMATE_LEVEL_BY_KEY)
    previous_grac = enrich_manifest._GRAC_FREQUENCY_CACHE_DATA
    enrich_manifest._CEFR_ESTIMATE_LEVEL_BY_KEY.clear()
    enrich_manifest._GRAC_FREQUENCY_CACHE_DATA = dict(grac)

    seen: list[dict[str, Any]] = []

    def fake_enrich_entry(
        entry,
        conn,
        kaikki_lookup,
        *,
        has_sum11_flags,
        pointer_synonym_relations=None,
        pointer_antonym_relations=None,
        pointer_homonym_relations=None,
        pointer_paronym_relations=None,
    ):
        lemma = str(entry["lemma"])
        seen.append(
            {
                "lemma": lemma,
                "cefr": enrich_manifest._cefr(conn, lemma),
                "syn": list(pointer_synonym_relations or []),
                "ant": list(pointer_antonym_relations or []),
            }
        )
        entry["heritage_status"] = {"classification": "unknown"}
        return True

    monkeypatch.setattr(fill_local, "enrich_entry", fake_enrich_entry)
    monkeypatch.setattr(enrich_manifest, "_vesum_valid_synonym", lambda term: bool(term))
    monkeypatch.setattr(enrich_manifest, "_vesum_word_analyses", lambda word: ((word, "noun"),))

    try:
        fill_local.fill_local(db_path, sources_db_path, tmp_path / "missing-kaikki.json")
    finally:
        enrich_manifest._CEFR_ESTIMATE_LEVEL_BY_KEY.clear()
        enrich_manifest._CEFR_ESTIMATE_LEVEL_BY_KEY.update(previous_cefr)
        enrich_manifest._GRAC_FREQUENCY_CACHE_DATA = previous_grac

    assert len(seen) == 20
    # Non-PULS lemmas (indices 10+) get estimated CEFR after prepare.
    estimated = [
        row
        for row in seen
        if row["cefr"] and row["cefr"].get("source") == enrich_manifest._CEFR_ESTIMATED_SOURCE
    ]
    assert len(estimated) == 10
    assert sum(1 for row in seen if row["cefr"]) == 20

    # Antonym pairs are one-way in fixtures; closed maps add reciprocal edges.
    antonym_rows_with_edges = [row for row in seen if row["ant"]]
    assert antonym_rows_with_edges
    reciprocal_ants = [
        rel
        for row in seen
        for rel in row["ant"]
        if rel.get("direction") == "reciprocal"
    ]
    assert reciprocal_ants

    # Synonym pairs are bidirectional; closed maps still pass non-empty lists.
    synonym_rows_with_edges = [row for row in seen if row["syn"]]
    assert synonym_rows_with_edges


def test_enrich_entry_merges_pointer_synonym_relations(monkeypatch):
    """#5331: pointer_synonym_relations must land in sections.synonyms."""
    monkeypatch.setattr(enrich_manifest, "mphdict_synonyms_available", lambda: True)
    monkeypatch.setattr(
        enrich_manifest,
        "_synonyms_mphdict",
        lambda *args, **kwargs: {"items": ["mphdict-item"], "source": "mphdict"},
    )
    monkeypatch.setattr(enrich_manifest, "_antonyms_wiktionary", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest, "_definition_antonym_relations", lambda *args, **kwargs: [])
    monkeypatch.setattr(enrich_manifest, "_homonym_relations", lambda *args, **kwargs: [])
    monkeypatch.setattr(enrich_manifest, "_paronym_relations", lambda *args, **kwargs: [])
    monkeypatch.setattr(enrich_manifest, "_idioms", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest, "_slovnyk_cache", lambda lemma: {})
    monkeypatch.setattr(enrich_manifest, "_definition_cards", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        enrich_manifest,
        "classify_lemma",
        lambda lemma: {"classification": "standard", "is_russianism": False, "attestations": []},
    )
    monkeypatch.setattr(enrich_manifest, "_warning_slovnyk", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest, "_curated_calque", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest, "_reverse_calques", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest, "_kaikki_pronunciation", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest, "_stress_display_form", lambda *args, **kwargs: "")
    monkeypatch.setattr(enrich_manifest, "_kaikki_stress", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest, "_cefr", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest, "_morphology", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest, "_meaning", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest, "_etymology", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest, "_literary_attestation", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest, "_wiki_reference", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest, "_base_lookup_for_entry", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest, "_vesum_valid_synonym", lambda term: bool(term))

    entry = {"lemma": "тестслово", "pos": "noun"}
    conn = sqlite3.connect(":memory:")
    assert enrich_manifest.enrich_entry(
        entry,
        conn,
        {},
        has_sum11_flags=False,
        pointer_synonym_relations=[
            {
                "item": "синонім-вказівник",
                "source": "СУМ-11",
                "pattern": "див.",
                "vein": 1,
                "direction": "reciprocal",
            }
        ],
        pointer_antonym_relations=[],
        pointer_homonym_relations=[],
        pointer_paronym_relations=[],
    )
    items = entry["sections"]["synonyms"]["items"]
    assert "mphdict-item" in items
    assert "синонім-вказівник" in items
