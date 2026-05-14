"""Tests for the ESUM Astro build-manifest emitter."""

import json
import sqlite3

from scripts.etymology.build_data_manifest import load_manifest


def _make_db(path):
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE esum_etymology_meta (
            id INTEGER PRIMARY KEY,
            lemma TEXT NOT NULL,
            vol INTEGER NOT NULL,
            page INTEGER NOT NULL,
            entry_hash TEXT NOT NULL DEFAULT '',
            etymology_text TEXT NOT NULL,
            cognates TEXT NOT NULL DEFAULT '[]',
            source TEXT NOT NULL DEFAULT 'ЕСУМ',
            UNIQUE(lemma, vol, page, entry_hash)
        );
        CREATE TABLE esum_cognate_forms (
            entry_id INTEGER PRIMARY KEY,
            cognate_forms TEXT NOT NULL DEFAULT '{}',
            proto_form TEXT,
            extracted_count INTEGER NOT NULL DEFAULT 0,
            expected_count INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(entry_id) REFERENCES esum_etymology_meta(id)
        );
        """
    )
    entries = [
        (1, "дім", 2, 90, "hash-1", "дім; — р. дом, п. dom.", {"р.": "дом", "п.": "dom"}, None),
        (2, "мати", 2, 48, "hash-2", "мати більш загальне значення.", {}, None),
        (3, "мати", 3, 412, "hash-3", "мати 1 (іменник)", {"р.": "мать"}, None),
        (4, "мати", 3, 413, "hash-4", "мати 2 (дієслово); — псл. *mati.", {"псл.": "*mati"}, "*mati"),
        (5, "серце", 5, 222, "hash-5", "серце; — псл. *sьrdьce.", {"р.": "сéрдце"}, "*sьrdьce"),
    ]
    for entry_id, lemma, vol, page, entry_hash, text, forms, proto in entries:
        conn.execute(
            "INSERT INTO esum_etymology_meta (id, lemma, vol, page, entry_hash, etymology_text)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (entry_id, lemma, vol, page, entry_hash, text),
        )
        conn.execute(
            "INSERT INTO esum_cognate_forms (entry_id, cognate_forms, proto_form,"
            " extracted_count, expected_count) VALUES (?, ?, ?, ?, ?)",
            (entry_id, json.dumps(forms, ensure_ascii=False), proto, len(forms), len(forms)),
        )
    conn.commit()
    conn.close()


def test_manifest_shape_and_stats(tmp_path):
    db = tmp_path / "sources.db"
    _make_db(db)
    manifest = load_manifest(db)

    assert manifest["version"]
    assert manifest["generated_at"]
    assert manifest["stats"]["total_entries"] == 5
    assert manifest["stats"]["unique_slugs"] == 3  # дім, мати (3 senses), серце
    assert manifest["stats"]["polysemy_slugs"] == 1  # only мати has >1 entry
    assert manifest["stats"]["entries_with_cognate_forms"] == 4  # all but мати-2-48


def test_slug_groups_index_polysemy(tmp_path):
    db = tmp_path / "sources.db"
    _make_db(db)
    manifest = load_manifest(db)

    # мати should appear in slug_groups with 3 page_slugs
    assert "maty" in manifest["slug_groups"]
    assert len(manifest["slug_groups"]["maty"]) == 3
    assert all(s.startswith("maty-") for s in manifest["slug_groups"]["maty"])

    # дім should have exactly 1 page_slug
    assert manifest["slug_groups"]["dim"] == ["dim-2-90"]

    # серце should have exactly 1 page_slug
    assert manifest["slug_groups"]["sertse"] == ["sertse-5-222"]


def test_entry_fields_include_cognates_and_proto(tmp_path):
    db = tmp_path / "sources.db"
    _make_db(db)
    manifest = load_manifest(db)

    # дім has cognates but no proto
    dim = next(e for e in manifest["entries"] if e["lemma"] == "дім")
    assert dim["cognate_forms"] == {"р.": "дом", "п.": "dom"}
    assert dim["proto_form"] is None
    assert dim["slug"] == "dim"
    assert dim["page_slug"] == "dim-2-90"

    # мати vol 3 page 413 has proto and one cognate
    maty_dieslovo = next(
        e for e in manifest["entries"] if e["lemma"] == "мати" and e["vol"] == 3 and e["page"] == 413
    )
    assert maty_dieslovo["proto_form"] == "*mati"
    assert maty_dieslovo["cognate_forms"] == {"псл.": "*mati"}


def test_polysemy_page_slug_includes_ordinal_when_vol_page_collide(tmp_path):
    """When the same lemma has two entries with identical (vol, page), the
    second one needs an ordinal suffix to keep slugs unique."""
    db = tmp_path / "sources.db"
    conn = sqlite3.connect(db)
    conn.executescript(
        """
        CREATE TABLE esum_etymology_meta (
            id INTEGER PRIMARY KEY,
            lemma TEXT NOT NULL,
            vol INTEGER NOT NULL,
            page INTEGER NOT NULL,
            entry_hash TEXT NOT NULL DEFAULT '',
            etymology_text TEXT NOT NULL,
            cognates TEXT NOT NULL DEFAULT '[]',
            source TEXT NOT NULL DEFAULT 'ЕСУМ',
            UNIQUE(lemma, vol, page, entry_hash)
        );
        CREATE TABLE esum_cognate_forms (
            entry_id INTEGER PRIMARY KEY,
            cognate_forms TEXT NOT NULL DEFAULT '{}',
            proto_form TEXT,
            extracted_count INTEGER NOT NULL DEFAULT 0,
            expected_count INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(entry_id) REFERENCES esum_etymology_meta(id)
        );
        """
    )
    # Same lemma + vol + page, different entry_hash
    conn.executemany(
        "INSERT INTO esum_etymology_meta (id, lemma, vol, page, entry_hash, etymology_text)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        [
            (1, "абсолют", 1, 37, "hash-a", "абсолют 1"),
            (2, "абсолют", 1, 37, "hash-b", "абсолют 2"),
        ],
    )
    conn.commit()
    conn.close()

    manifest = load_manifest(db)
    page_slugs = sorted(manifest["slug_groups"]["absoliut"])
    # Both should be unique, ordinal-disambiguated
    assert len(page_slugs) == 2
    assert page_slugs == ["absoliut-1-37-1", "absoliut-1-37-2"]
