"""Fixture-backed mphdict query and Atlas integration coverage.

The real mphdict SQLite exports are local ODbL data and intentionally absent
from CI.  These small databases model only the columns the query layer uses.
"""

from __future__ import annotations

import hashlib
import inspect
import sqlite3
from pathlib import Path

from scripts.lexicon import enrich_manifest
from scripts.lexicon.source_attribution import ESUM_LABEL, MPHDICT_SYNONYMS_LABEL
from scripts.mphdict import (
    mphdict_etymology,
    mphdict_headword,
    mphdict_synonyms,
    normalize_gloss,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _mphdict_fixture(tmp_path: Path) -> tuple[Path, Path]:
    db_dir = tmp_path / "mphdict"
    db_dir.mkdir()
    index_path = tmp_path / "mphdict-index.sqlite3"

    with sqlite3.connect(db_dir / "synsets_ua.db") as connection:
        connection.executescript(
            """
            CREATE TABLE pofs (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
            CREATE TABLE synsets (id INTEGER PRIMARY KEY, interpretation TEXT, pofs INTEGER NOT NULL);
            CREATE TABLE wlist (
                id INTEGER PRIMARY KEY,
                id_set INTEGER NOT NULL,
                id_syn INTEGER NOT NULL,
                word TEXT,
                interpretation TEXT,
                sign INTEGER,
                hyperonym TEXT,
                homonym INTEGER
            );
            """
        )
        connection.execute("INSERT INTO pofs VALUES (3, 'Прикметник')")
        connection.executemany(
            "INSERT INTO synsets VALUES (?, ?, 3)",
            [
                (10, "про людину — [S]конкретний[/S]"),
                (20, "про предмет — привабливий вигляд"),
            ],
        )
        connection.executemany(
            "INSERT INTO wlist VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (1, 10, 1, 'га"рний', "Приємний [B]вигляд[/B]", 0, "", 0),
                (2, 10, 2, 'краси"вий', "Те саме, що [S]га́рний[/S]", 0, "", 0),
                (3, 20, 1, 'га"рний', "Привабливий предмет", 0, "", 0),
                (4, 20, 2, 'чудо"вий', "Дуже [B]гарний[/B]", 1, 'приго"жий', 2),
            ],
        )

    with sqlite3.connect(db_dir / "etym.db") as connection:
        connection.executescript(
            """
            CREATE TABLE root (id INTEGER PRIMARY KEY, volume_num INTEGER, page_initial INTEGER, page_last INTEGER);
            CREATE TABLE e_classes (
                id INTEGER PRIMARY KEY,
                id_root INTEGER NOT NULL,
                class_type INTEGER NOT NULL,
                class_num INTEGER NOT NULL,
                subclass_num INTEGER NOT NULL,
                formal_type INTEGER NOT NULL,
                subclass_text TEXT
            );
            CREATE TABLE etymons (
                id INTEGER PRIMARY KEY,
                id_e_classes INTEGER NOT NULL,
                word_num INTEGER NOT NULL,
                ishead INTEGER NOT NULL,
                word TEXT NOT NULL,
                homonym INTEGER NOT NULL,
                dialect INTEGER NOT NULL,
                antroponym INTEGER NOT NULL DEFAULT 0,
                lang_code INTEGER,
                lang_marker TEXT,
                lang_note TEXT,
                note TEXT,
                sense TEXT,
                bibliography TEXT
            );
            CREATE TABLE lang_all (lang_code INTEGER PRIMARY KEY, lang_name TEXT);
            CREATE TABLE bibl (id INTEGER PRIMARY KEY, id_root INTEGER NOT NULL, biblio_num INTEGER NOT NULL, biblio_text TEXT);
            CREATE TABLE links (id INTEGER PRIMARY KEY, id_root INTEGER NOT NULL, link_type INTEGER NOT NULL, link_num INTEGER NOT NULL, word TEXT, homonym INTEGER);
            """
        )
        connection.executemany("INSERT INTO root VALUES (?, ?, ?, ?)", [(1, 1, 414, 415), (2, 1, 416, 416)])
        connection.executemany(
            "INSERT INTO e_classes VALUES (?, ?, 0, ?, 0, 0, '')",
            [(11, 1, 1), (12, 1, 2), (21, 2, 1)],
        )
        connection.executemany(
            "INSERT INTO lang_all VALUES (?, ?)", [(183, "українська"), (57, "давньоруська")]
        )
        connection.executemany(
            """INSERT INTO etymons
               (id, id_e_classes, word_num, ishead, word, homonym, dialect, antroponym,
                lang_code, lang_marker, lang_note, note, sense, bibliography)
               VALUES (?, ?, ?, ?, ?, 0, 0, 0, ?, ?, '', ?, ?, ?)""",
            [
                (101, 11, 1, 1, "вода\u0301", 183, "укр.", "", "", ""),
                (102, 12, 1, 0, "вода", 57, "др.", "", "«рідина»", "Ref A"),
                (201, 21, 1, 1, "водни\u0301к", 183, "укр.", "", "", ""),
                (202, 21, 2, 0, "вода", 183, "укр.", "", "embedded comparison", ""),
            ],
        )
        connection.execute("INSERT INTO bibl VALUES (1, 1, 1, 'Фасмер I 1')")
        connection.execute("INSERT INTO links VALUES (1, 1, 2, 4, 'вода', 0)")

    with sqlite3.connect(db_dir / "mph_ua.db") as connection:
        connection.executescript(
            """
            CREATE TABLE nom (
                reestr TEXT NOT NULL,
                part INTEGER NOT NULL,
                type INTEGER NOT NULL,
                nom_old INTEGER PRIMARY KEY,
                isdel INTEGER NOT NULL,
                isproblem INTEGER
            );
            CREATE TABLE parts (id INTEGER PRIMARY KEY, part TEXT, com TEXT);
            """
        )
        connection.execute("INSERT INTO parts VALUES (11, 'п', 'прикметник')")
        connection.executemany(
            "INSERT INTO nom VALUES (?, 11, 2302, ?, ?, ?)",
            [('га"рний', 1, 0, 0), ('га"рний', 2, 1, 0)],
        )
    return db_dir, index_path


def test_synonym_groups_stress_markup_and_sidecar_leave_sources_untouched(tmp_path: Path) -> None:
    db_dir, index_path = _mphdict_fixture(tmp_path)
    source_paths = sorted(db_dir.glob("*.db"))
    before = {path.name: _sha256(path) for path in source_paths}

    result = mphdict_synonyms("га́рний", db_dir=db_dir, index_path=index_path)

    assert result is not None
    assert result["lemma"] == "гарний"
    assert [group["id"] for group in result["synsets"]] == [10, 20]
    first = result["synsets"][0]
    assert first["pos"] == "Прикметник"
    assert first["gloss"] == {
        "text": "про людину — конкретний",
        "markup": [{"tag": "S", "text": "конкретний"}],
    }
    assert first["members"][0]["stressed"] == "га́рний"
    assert first["members"][0]["encoded_stressed"] == 'га"рний'
    assert first["members"][1]["gloss"]["markup"] == [{"tag": "S", "text": "га́рний"}]
    assert result["synsets"][1]["members"][1]["hyperonym"]["stressed"] == "приго́жий"
    assert result["synsets"][1]["members"][1]["homonym"] == 2
    assert before == {path.name: _sha256(path) for path in source_paths}

    with sqlite3.connect(index_path) as connection:
        plan = connection.execute(
            "EXPLAIN QUERY PLAN SELECT row_id FROM normalized_words WHERE source_key = ? AND lookup_key = ?",
            (f"{(db_dir / 'synsets_ua.db').resolve()}::wlist::id::word", "гарний"),
        ).fetchall()
    assert any("normalized_words_lookup" in str(row) for row in plan)


def test_gloss_normalization_keeps_label_text_and_tagged_structure() -> None:
    assert normalize_gloss("&lt;рідко.&gt;Те саме, що [B]завда́ток[/B]") == {
        "text": "рідко. Те саме, що завда́ток",
        "markup": [{"tag": "B", "text": "завда́ток"}],
    }


def test_etymology_uses_direct_headword_root_with_citation_and_bibliography(tmp_path: Path) -> None:
    db_dir, index_path = _mphdict_fixture(tmp_path)

    result = mphdict_etymology("вода", db_dir=db_dir, index_path=index_path)

    assert result is not None
    assert result["lemma"] == "вода"
    assert len(result["roots"]) == 1
    root = result["roots"][0]
    assert root["id"] == 1
    assert root["match"] == {"is_direct_headword": True, "kind": "headword"}
    assert root["citation"] == {
        "volume": 1,
        "page_initial": 414,
        "page_last": 415,
        "display": "т. 1, с. 414–415",
    }
    assert root["etymons"][0]["stressed"] == "вода́"
    assert root["etymons"][1]["language"] == "давньоруська"
    assert root["etymons"][1]["bibliography"] == "Ref A"
    assert root["bibliography"] == [{"number": 1, "text": "Фасмер I 1"}]
    assert root["links"] == [{"type": 2, "number": 4, "word": "вода", "homonym": 0}]


def test_headword_returns_active_official_stressed_registry_row(tmp_path: Path) -> None:
    db_dir, index_path = _mphdict_fixture(tmp_path)

    result = mphdict_headword("гарний", db_dir=db_dir, index_path=index_path)

    assert result == {
        "registry_id": 1,
        "lemma": "гарний",
        "stressed": "га́рний",
        "encoded_stressed": 'га"рний',
        "pos": "прикметник",
        "pos_code": "п",
        "part_id": 11,
        "flexion_type": 2302,
    }


def test_atlas_adapters_use_mphdict_without_the_legacy_enrichment_sources(monkeypatch) -> None:
    synsets = [{"id": 9, "pos": "Іменник", "members": [{"lemma": "ключ", "stressed": "ключ"}, {"lemma": "замок", "stressed": "замо́к"}]}]
    monkeypatch.setattr(enrich_manifest, "mphdict_synonyms", lambda word: {"lemma": word, "synsets": synsets})
    monkeypatch.setattr(
        enrich_manifest,
        "mphdict_etymology",
        lambda word: {
            "lemma": word,
            "roots": [
                {
                    "id": 5,
                    "match": {"is_direct_headword": True, "kind": "headword"},
                    "citation": {"display": "т. 6, с. 181"},
                    "etymons": [{"is_head": True, "stressed": "хліб"}],
                    "bibliography": [{"number": 1, "text": "Fixture bibliography"}],
                }
            ],
        },
    )

    synonyms = enrich_manifest._synonyms_mphdict("ключ")
    etymology = enrich_manifest._etymology(sqlite3.connect(":memory:"), "хліб", {})

    assert synonyms == {"items": ["замок"], "synsets": synsets, "source": MPHDICT_SYNONYMS_LABEL}
    assert etymology == {
        "text": "Стаття ЕСУМ: хліб; етимонів: 1.",
        "source": f"{ESUM_LABEL}, т. 6, с. 181",
        "mphdict_root": {
            "id": 5,
            "match": {"is_direct_headword": True, "kind": "headword"},
            "citation": {"display": "т. 6, с. 181"},
            "bibliography": [{"number": 1, "text": "Fixture bibliography"}],
        },
    }
    enrichment_source = inspect.getsource(enrich_manifest.enrich_entry)
    etymology_source = inspect.getsource(enrich_manifest._etymology)
    assert "ukrajinet" not in enrichment_source.casefold()
    assert "_synonyms_slovnyk" not in enrichment_source
    assert "_source_etymology" not in etymology_source


def test_active_slovnyk_cache_excludes_retired_synonym_slugs() -> None:
    assert "synonyms" not in enrich_manifest._SLOVNYK_LOOKUP_SLUGS
    assert "synonyms_karavansky" not in enrich_manifest._SLOVNYK_LOOKUP_SLUGS
