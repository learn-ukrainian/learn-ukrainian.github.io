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


def test_atlas_disambiguation():
    """Verify атлас maps collection vs satin fabric disambiguation."""
    items = enrich_heteronyms.build_heteronyms_for_lemma("атлас")
    assert items is not None
    assert len(items) == 2

    maps, satin = items[0], items[1]

    assert maps["headword"] == "а́тлас"
    assert maps["pronunciation"]["ipa"] == "[ˈatɫɐs]"
    assert maps["short_label"] == "збірник карт"
    assert "збірник карт" in maps["sections"]["synonyms"]["items"]

    assert satin["headword"] == "атла́с"
    assert satin["pronunciation"]["ipa"] == "[ɐtˈɫas]"
    assert satin["short_label"] == "тканина"
    assert "шовк" in satin["sections"]["synonyms"]["items"]


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
    """Verify apply_heteronyms updates SQLite database properly for all heteronym lemmas."""
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

    initial_records = [
        ("город", "город", "vegetable garden", "authentic-archaism", {"items": ["місто"]}),
        ("замок", "замок", "castle / lock", "standard", {"items": ["палац"]}),
        ("атлас", "атлас", "atlas / satin", "standard", None),
    ]
    for slug, head, gloss, heritage, syns in initial_records:
        sec = {"synonyms": syns} if syns else {}
        p = {"lemma": slug, "url_slug": slug, "gloss": gloss, "heritage_status": {"classification": heritage}, "sections": sec}
        conn.execute("INSERT INTO article_payloads VALUES (?, 1, ?, 1)", (slug, json.dumps(p)))
        conn.execute("INSERT INTO articles VALUES (?, ?, 'noun', ?, ?)", (slug, head, gloss, heritage))
    conn.commit()
    conn.close()

    counts = enrich_heteronyms.apply_heteronyms(
        db_path=db_path, manifest_path=dummy_manifest, lemmas=["город", "замок", "атлас"]
    )
    assert counts["db_payloads"] == 3
    assert counts["db_articles"] == 3

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Verify город
    g_row = cur.execute("SELECT payload_json FROM article_payloads WHERE slug = 'город'").fetchone()
    assert g_row is not None
    g_payload = json.loads(g_row[0])
    assert len(g_payload["heteronyms"]) == 2
    assert g_payload["heteronyms"][0]["headword"] == "горо́д"
    assert g_payload["display_head"] == "горо́д"
    assert g_payload["heritage_status"]["classification"] == "standard"
    assert g_payload["sections"]["synonyms"]["items"] == ["грядка", "городчик"]

    # Verify замок
    z_row = cur.execute("SELECT payload_json FROM article_payloads WHERE slug = 'замок'").fetchone()
    assert z_row is not None
    z_payload = json.loads(z_row[0])
    assert len(z_payload["heteronyms"]) == 2
    assert z_payload["display_head"] == "за́мок"
    assert "фортеця" in z_payload["sections"]["synonyms"]["items"]
    z_art = cur.execute("SELECT display_head, gloss FROM articles WHERE slug = 'замок'").fetchone()
    assert z_art == ("за́мок", "castle, fortress, palace")

    # Verify атлас
    a_row = cur.execute("SELECT payload_json FROM article_payloads WHERE slug = 'атлас'").fetchone()
    assert a_row is not None
    a_payload = json.loads(a_row[0])
    assert len(a_payload["heteronyms"]) == 2
    assert a_payload["display_head"] == "а́тлас"
    assert "збірник карт" in a_payload["sections"]["synonyms"]["items"]
    a_art = cur.execute("SELECT display_head, gloss FROM articles WHERE slug = 'атлас'").fetchone()
    assert a_art == ("а́тлас", "atlas (bound collection of maps)")

    conn.close()


def test_apply_heteronyms_to_manifest(tmp_path: Path):
    """Verify apply_heteronyms updates JSON manifest properly for all heteronyms."""
    manifest_path = tmp_path / "lexicon-manifest.json"
    data = {
        "entries": [
            {
                "lemma": "город",
                "url_slug": "город",
                "gloss": "vegetable garden",
                "heritage_status": {"classification": "authentic-archaism"},
            },
            {
                "lemma": "замок",
                "url_slug": "замок",
                "gloss": "castle / lock",
                "heritage_status": {"classification": "standard"},
            },
            {
                "lemma": "атлас",
                "url_slug": "атлас",
                "gloss": "atlas / satin",
                "heritage_status": {"classification": "standard"},
            },
        ]
    }
    manifest_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    dummy_db = tmp_path / "empty.db"
    counts = enrich_heteronyms.apply_heteronyms(
        db_path=dummy_db, manifest_path=manifest_path, lemmas=["город", "замок", "атлас"]
    )
    assert counts["manifest_entries"] == 3

    updated = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = {e["lemma"]: e for e in updated["entries"]}

    assert entries["город"]["display_head"] == "горо́д"
    assert entries["город"]["sections"]["synonyms"]["items"] == ["грядка", "городчик"]

    assert entries["замок"]["display_head"] == "за́мок"
    assert "фортеця" in entries["замок"]["sections"]["synonyms"]["items"]

    assert entries["атлас"]["display_head"] == "а́тлас"
    assert "збірник карт" in entries["атлас"]["sections"]["synonyms"]["items"]


def test_curated_heteronyms_ts_parity():
    """Verify site/src/lib/lexicon/curated-heteronyms.ts aligns with enrich_heteronyms.py."""
    ts_file = Path(__file__).resolve().parents[1] / "site" / "src" / "lib" / "lexicon" / "curated-heteronyms.ts"
    assert ts_file.is_file(), f"Expected {ts_file} to exist"
    content = ts_file.read_text(encoding="utf-8")

    for lemma, expected_items in enrich_heteronyms.CURATED_HETERONYMS.items():
        assert f"{lemma}: [" in content, f"Lemma {lemma} missing from curated-heteronyms.ts"
        for item in expected_items:
            headword = item["headword"]
            assert f'headword: "{headword}"' in content, f"Headword {headword} missing from {lemma} in TS"
            assert f'lemma: "{lemma}"' in content, f"Lemma {lemma} missing from TS"
            assert f'url_slug: "{lemma}"' in content, f"url_slug {lemma} missing from TS"
