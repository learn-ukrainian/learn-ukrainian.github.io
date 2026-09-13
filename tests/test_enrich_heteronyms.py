"""Unit tests for Word Atlas heteronym disambiguation (scripts/lexicon/enrich_heteronyms.py)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from scripts.lexicon import enrich_heteronyms


def test_curated_heteronyms_structure():
    """Curated heteronyms must include all required fields for Word Atlas."""
    for lemma, items in enrich_heteronyms.CURATED_HETERONYMS.items():
        assert len(items) >= 2, f"Expected at least 2 heteronyms for {lemma}"
        heads = [item["headword"] for item in items]
        assert len(set(heads)) == len(heads), f"Duplicate headwords found for {lemma}"
        for item in items:
            assert "headword" in item
            assert "gloss" in item
            assert "short_label" in item
            assert "heritage_status" in item
            assert "distinction_note" in item
            assert "morphology" in item
            assert "pronunciation" in item
            assert "stress" in item


def test_gorod_disambiguation():
    """Verify город vegetable garden is distinguished from archaic город city."""
    items = enrich_heteronyms.build_heteronyms_for_lemma("город")
    assert items is not None
    assert len(items) == 2

    garden, city = items[0], items[1]

    # Sense 0: vegetable garden (A2, modern standard)
    assert garden["headword"] == "горо́д"
    assert garden["cefr"] == "A2"
    assert garden["heritage_status"]["classification"] == "standard"
    assert garden["pronunciation"]["ipa"] == "[ɦɔˈrɔd]"
    assert garden["morphology"]["paradigm"]["cases"]["родовий"]["singular"] == "горо́ду"
    assert garden["morphology"]["paradigm"]["cases"]["місцевий"]["singular"] == "на горо́ді / горо́ду"
    assert "місто" not in garden["sections"]["synonyms"]["items"]
    assert "грядка" in garden["sections"]["synonyms"]["items"]

    # Sense 1: archaic city
    assert city["headword"] == "го́род"
    assert city["heritage_status"]["classification"] == "authentic-archaism"
    assert city["heritage_status"]["warning_severity"] == "treasured"
    assert city["pronunciation"]["ipa"] == "[ˈɦɔrɔd]"
    assert "місто" in city["sections"]["synonyms"]["items"]


def test_zamok_disambiguation():
    """Verify замок castle vs lock disambiguation."""
    items = enrich_heteronyms.build_heteronyms_for_lemma("замок")
    assert items is not None
    assert len(items) == 2

    castle, lock = items[0], items[1]

    assert castle["headword"] == "за́мок"
    assert castle["pronunciation"]["ipa"] == "[ˈzamɔk]"
    assert castle["morphology"]["paradigm"]["cases"]["родовий"]["singular"] == "за́мку"
    assert "фортеця" in castle["sections"]["synonyms"]["items"]

    assert lock["headword"] == "замо́к"
    assert lock["pronunciation"]["ipa"] == "[zɐˈmɔk]"
    assert lock["morphology"]["paradigm"]["cases"]["родовий"]["singular"] == "замка́"
    assert "колодка" in lock["sections"]["synonyms"]["items"]


def test_sum11_parsing():
    """Verify regex extraction of heteronyms from multi-headword СУМ-11 text."""
    sample_text = (
        "А́ТЛАС, у, ч. Укладений за певною системою збірник карт.\n"
        "АТЛА́С, у, ч. Шовкова або напівшовкова тканина, блискуча з лиця."
    )
    parsed = enrich_heteronyms.parse_sum11_heteronyms("атлас", sample_text)
    assert len(parsed) == 2
    assert parsed[0]["head"] == "А́ТЛАС"
    assert "збірник карт" in parsed[0]["body"]
    assert parsed[1]["head"] == "АТЛА́С"
    assert "Шовкова" in parsed[1]["body"]


def test_apply_heteronyms_to_db(tmp_path: Path):
    """Verify apply_heteronyms updates SQLite database properly."""
    db_path = tmp_path / "test_atlas.db"
    dummy_manifest = tmp_path / "empty_manifest.json"
    dummy_manifest.write_text("{}", encoding="utf-8")

    conn = sqlite3.connect(db_path)
    conn.execute(
        """CREATE TABLE article_payloads (
            slug TEXT PRIMARY KEY,
            route_order INTEGER,
            payload_json TEXT NOT NULL,
            is_public_route INTEGER NOT NULL DEFAULT 1
        )"""
    )
    conn.execute(
        """CREATE TABLE articles (
            slug TEXT PRIMARY KEY,
            display_head TEXT NOT NULL,
            pos TEXT,
            gloss TEXT,
            heritage_classification TEXT
        )"""
    )

    initial_payload = {
        "lemma": "город",
        "url_slug": "город",
        "gloss": "vegetable garden",
        "heritage_status": {"classification": "authentic-archaism"},
        "enrichment": {"stress": {"form": "го́род"}},
        "sections": {"synonyms": {"items": ["місто"]}},
    }
    conn.execute(
        "INSERT INTO article_payloads VALUES (?, ?, ?, 1)",
        ("город", 1, json.dumps(initial_payload)),
    )
    conn.execute(
        "INSERT INTO articles VALUES (?, ?, ?, ?, ?)",
        ("город", "город", "noun", "vegetable garden", "authentic-archaism"),
    )
    conn.commit()
    conn.close()

    counts = enrich_heteronyms.apply_heteronyms(
        db_path=db_path, manifest_path=dummy_manifest, lemmas=["город"]
    )
    assert counts["db_payloads"] == 1
    assert counts["db_articles"] == 1

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    row = cur.execute("SELECT payload_json FROM article_payloads WHERE slug = 'город'").fetchone()
    assert row is not None
    payload = json.loads(row[0])
    assert "heteronyms" in payload
    assert len(payload["heteronyms"]) == 2
    assert payload["heteronyms"][0]["headword"] == "горо́д"
    assert payload["heritage_status"]["classification"] == "standard"
    assert payload["sections"]["synonyms"]["items"] == ["грядка", "городчик"]

    article_row = cur.execute("SELECT display_head, heritage_classification FROM articles WHERE slug = 'город'").fetchone()
    assert article_row == ("горо́д", "standard")
    conn.close()


def test_apply_heteronyms_to_manifest(tmp_path: Path):
    """Verify apply_heteronyms updates JSON manifest properly."""
    manifest_path = tmp_path / "lexicon-manifest.json"
    data = {
        "entries": [
            {
                "lemma": "город",
                "url_slug": "город",
                "gloss": "vegetable garden",
                "heritage_status": {"classification": "authentic-archaism"},
            }
        ]
    }
    manifest_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    dummy_db = tmp_path / "empty.db"
    counts = enrich_heteronyms.apply_heteronyms(
        db_path=dummy_db, manifest_path=manifest_path, lemmas=["город"]
    )
    assert counts["manifest_entries"] == 1

    updated = json.loads(manifest_path.read_text(encoding="utf-8"))
    entry = updated["entries"][0]
    assert "heteronyms" in entry
    assert len(entry["heteronyms"]) == 2
    assert entry["heteronyms"][0]["headword"] == "горо́д"
    assert entry["heritage_status"]["classification"] == "standard"
