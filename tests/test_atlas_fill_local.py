from __future__ import annotations

import json
import os
import socket
import sqlite3
from pathlib import Path

from scripts.atlas import atlas_db, fill_local
from scripts.lexicon import enrich_manifest


def _build_atlas_db(tmp_path: Path) -> Path:
    manifest = {
        "entries": [
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
    }
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

    def fake_enrich_entry(entry, conn, kaikki_lookup, *, has_sum11_flags):
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

    def fake_enrich_entry(entry, conn, kaikki_lookup, *, has_sum11_flags):
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

    def fake_enrich_entry(entry, conn, kaikki_lookup, *, has_sum11_flags):
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

    def fake_enrich_entry(entry, conn, kaikki_lookup, *, has_sum11_flags):
        assert enrich_manifest._fetch_slovnyk_entry("немає", "немає", "vts") is None
        assert enrich_manifest._cached_wikipedia_summary("Тестова стаття без кешу") is None
        assert enrich_manifest._fetch_grac_frequency_batch(["немає"]) == {"немає": None}
        entry["enrichment"] = {"stress": {"form": "нема́є", "source": "stress fixture"}}
        entry["heritage_status"] = {"classification": "unknown"}
        return True

    monkeypatch.setattr(fill_local, "enrich_entry", fake_enrich_entry)

    fill_local.fill_local(db_path, sources_db_path, tmp_path / "missing-kaikki.json", slug="бігти")
    assert os.environ["LEXICON_SLOVNYK_OFFLINE"] == "0"
