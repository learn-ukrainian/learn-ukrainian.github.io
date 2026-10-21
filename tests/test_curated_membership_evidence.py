"""Regression for checked ULIF homonyms whose entry header is blank (#9151)."""

import json
import sqlite3

from scripts.lexicon.curated_membership_evidence import read_checked_ulif


def test_real_section_shapes_resolve_blank_headers() -> None:
    # Values and section shapes are reduced from checked sources.db rows; the
    # checked ID, paradigm head, and matching synonym term are kept verbatim.
    examples = [
        (77657, "запинитися", "запини́тися", "ЗАПИНИ́ТИСЯ"),
        (73555, "загостритися", "загостри́тися", "загостри́тися"),
        (44822, "вкритися", "вкри́тися", "вкри́тися"),
        (137720, "нищівний", "нищівни́й", "НИЩІВНИ́Й"),
        (205476, "розпоряджатися", "розпоряджа́тися", "розпоряджа́тися"),
        (153644, "папка", "па́пка", "ПА́ПКА"),
    ]
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """CREATE TABLE ulif_dictua_entries
           (id INTEGER, normalized_query TEXT, homonym_index INTEGER,
            canonical_headword TEXT, grammatical_label TEXT, status TEXT,
            homonym_checked INTEGER);
           CREATE TABLE ulif_dictua_sections
           (id INTEGER, entry_id INTEGER, kind TEXT, source_order INTEGER,
            payload_json TEXT);"""
    )
    for index, (entry_id, lemma, head, synonym) in enumerate(examples):
        conn.execute(
            "INSERT INTO ulif_dictua_entries VALUES (?,?,?,?,?,?,1)",
            (entry_id, lemma, 2 if entry_id == 153644 else 1, "", "", "ok"),
        )
        label = "називний" if lemma in {"нищівний", "папка"} else "Інфінітив"
        conn.execute(
            "INSERT INTO ulif_dictua_sections VALUES (?,?,?,?,?)",
            (index * 2 + 1, entry_id, "paradigm", 0, json.dumps({"rows": [[label, head]]})),
        )
        conn.execute(
            "INSERT INTO ulif_dictua_sections VALUES (?,?,?,?,?)",
            (
                index * 2 + 2,
                entry_id,
                "synonyms",
                0,
                json.dumps({"terms": [{"text": synonym}], "text": synonym}),
            ),
        )
    for entry_id, lemma, head, synonym in examples:
        checked = read_checked_ulif(conn, lemma)
        row = next(item for item in checked if item["id"] == entry_id)
        assert row["headword"] == head
        assert row["paradigm_headword"] == head
        assert synonym in row["matching_synonym_terms"]
        assert row["section_kinds"] == ["paradigm", "synonyms"]
        assert row["lexical_attestation"] is True


def test_empty_checked_homonym_without_matching_sections_is_not_attested() -> None:
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """CREATE TABLE ulif_dictua_entries
           (id INTEGER, normalized_query TEXT, homonym_index INTEGER,
            canonical_headword TEXT, grammatical_label TEXT, status TEXT,
            homonym_checked INTEGER);
           CREATE TABLE ulif_dictua_sections
           (id INTEGER, entry_id INTEGER, kind TEXT, source_order INTEGER,
            payload_json TEXT);
           INSERT INTO ulif_dictua_entries VALUES (1,'слово',1,'','','ok',1);"""
    )
    assert read_checked_ulif(conn, "слово")[0]["lexical_attestation"] is False


def test_only_headword_cell_attests_and_unchecked_homonyms_are_excluded() -> None:
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """CREATE TABLE ulif_dictua_entries
           (id INTEGER, normalized_query TEXT, homonym_index INTEGER,
            canonical_headword TEXT, grammatical_label TEXT, status TEXT,
            homonym_checked INTEGER);
           CREATE TABLE ulif_dictua_sections
           (id INTEGER, entry_id INTEGER, kind TEXT, source_order INTEGER,
            payload_json TEXT);
           INSERT INTO ulif_dictua_entries VALUES (1,'слово',1,'','','ok',1);
           INSERT INTO ulif_dictua_entries VALUES (2,'слово',2,'слово','','ok',0);
           INSERT INTO ulif_dictua_entries VALUES (3,'п’єса',1,'','','ok',1);"""
    )
    conn.execute(
        "INSERT INTO ulif_dictua_sections VALUES (1,1,'paradigm',0,?)",
        (json.dumps({"rows": [["називний", "інше", "слово"], ["родовий", "слово"]]}),),
    )
    conn.execute(
        "INSERT INTO ulif_dictua_sections VALUES (2,3,'paradigm',0,?)",
        (json.dumps({"rows": [["називний", "пʼєса"]]}),),
    )
    checked = read_checked_ulif(conn, "слово")
    assert [row["id"] for row in checked] == [1]
    assert checked[0]["paradigm_headword"] == ""
    assert checked[0]["lexical_attestation"] is False
    apostrophe = read_checked_ulif(conn, "п’єса")
    assert apostrophe[0]["paradigm_headword"] == "пʼєса"
    assert apostrophe[0]["lexical_attestation"] is True
