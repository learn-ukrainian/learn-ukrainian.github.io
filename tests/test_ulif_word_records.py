"""Tests for ULIF source word records retrieval (issue #9250).

Verifies full-record source faithfulness:
- No first-homonym selection or silent partition merging
- Every paradigm, synonym, antonym, and phraseology section preserved with full payloads
- Unknown payload keys and raw_html kept intact
- Stored identity preserved byte-for-byte; raw identity separately attributed
- Explicit forms_state reporting (never masquerading as empty forms)
- Unverified entries exposed with verified=False and empty sections
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from scripts.lexicon.runner import ulif_forms
from scripts.wiki import sources_db

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "ulif_dictua"


def _read_fixture(name: str) -> str:
    path = FIXTURES_DIR / name
    if not path.is_file():
        raise FileNotFoundError(f"Fixture not found: {path}")
    return path.read_text(encoding="utf-8")


def test_word_records_all_sections_preserved_and_not_collapsed(tmp_path):
    db_path = tmp_path / "sources.db"
    par_html = _read_fixture("zamok-entry-1.html")
    syn_html = "<html>synonyms</html>"
    phr_html = "<html>phraseology</html>"

    sources_db.store_ulif_dictua_entry(
        word="замок",
        canonical_headword="За́мок",
        grammatical_label="іменник чоловічого роду",
        sense_gloss="(будівля)",
        sections={
            "paradigm": {
                "rows": [["Називний", "За́мок"], ["Родовий", "За́мку"]],
                "custom_unknown_key": "preserved_123",
                "raw_html": "<table>custom_raw</table>",
            },
            "synonyms": [
                {
                    "terms": [{"text": "твердиня", "raw_html": "<b>твердиня</b>"}],
                    "text": "твердиня, фортеця",
                    "source_order": 0,
                    "sense_or_group_id": "synonyms:1",
                }
            ],
            "phraseology": [
                {
                    "terms": [{"text": "повітряні замки"}],
                    "text": "будувати повітряні замки",
                    "source_order": 0,
                    "sense_or_group_id": "phraseology:1",
                    "extra_provenance": "src_456",
                }
            ],
        },
        raw_responses={
            "paradigm": par_html,
            "synonyms": syn_html,
            "phraseology": phr_html,
        },
        retrieved_at="2026-09-28T00:00:00Z",
        parser_version="ulif-dictua-v2",
        status="ok",
        homonym_index=1,
        homonym_checked=1,
        db_path=db_path,
    )

    records = sources_db.get_ulif_word_records(["замок"], db_path=db_path)
    assert len(records) == 1
    rec = records[0]
    assert rec["word"] == "замок"
    assert rec["status"] == "ok"
    assert rec["verified"] is True
    assert rec["entry_count"] == 1

    entry = rec["entries"][0]
    assert entry["canonical_headword"] == "За́мок"
    assert entry["grammatical_label"] == "іменник чоловічого роду"
    assert entry["sense_gloss"] == "(будівля)"
    assert entry["verified"] is True

    # Paradigm section is an ordered list of full payloads, NOT collapsed to a dict
    assert isinstance(entry["sections"]["paradigm"], list)
    assert len(entry["sections"]["paradigm"]) == 1
    par_payload = entry["sections"]["paradigm"][0]
    assert par_payload["custom_unknown_key"] == "preserved_123"
    assert par_payload["raw_html"] == "<table>custom_raw</table>"
    assert par_payload["rows"] == [["Називний", "За́мок"], ["Родовий", "За́мку"]]

    # Relation sections retain full ordered payloads and unknown keys
    assert len(entry["sections"]["synonyms"]) == 1
    assert entry["sections"]["synonyms"][0]["terms"][0]["text"] == "твердиня"
    assert entry["sections"]["synonyms"][0]["terms"][0]["raw_html"] == "<b>твердиня</b>"

    assert len(entry["sections"]["phraseology"]) == 1
    assert entry["sections"]["phraseology"][0]["extra_provenance"] == "src_456"
    assert entry["sections"]["phraseology"][0]["sense_or_group_id"] == "phraseology:1"


def test_distinct_homonyms_kept_separate_and_not_merged(tmp_path):
    """Ensure no silent first-homonym selection or partition merging."""
    db_path = tmp_path / "sources.db"

    # Homonym 1
    sources_db.store_ulif_dictua_entry(
        word="замок",
        canonical_headword="За́мок",
        grammatical_label="іменник чоловічого роду",
        sense_gloss="(будівля)",
        sections={"paradigm": {"rows": [["Називний", "За́мок"]]}},
        raw_responses={"paradigm": _read_fixture("zamok-entry-1.html")},
        retrieved_at="2026-09-28T00:00:00Z",
        parser_version="ulif-dictua-v2",
        status="ok",
        homonym_index=1,
        homonym_checked=1,
        db_path=db_path,
    )
    # Homonym 2
    sources_db.store_ulif_dictua_entry(
        word="замок",
        canonical_headword="за́мок",
        grammatical_label="іменник чоловічого роду",
        sense_gloss="(феодальний)",
        sections={"synonyms": [{"terms": [{"text": "палац"}]}]},
        raw_responses={"synonyms": "<html>syn</html>"},
        retrieved_at="2026-09-28T00:00:00Z",
        parser_version="ulif-dictua-v2",
        status="ok",
        homonym_index=2,
        homonym_checked=1,
        db_path=db_path,
    )
    # Homonym 3
    sources_db.store_ulif_dictua_entry(
        word="замок",
        canonical_headword="замо́к",
        grammatical_label="іменник чоловічого роду",
        sense_gloss="(пристрій для замикання)",
        sections={"phraseology": [{"terms": [{"text": "під замком"}]}]},
        raw_responses={"phraseology": "<html>phras</html>"},
        retrieved_at="2026-09-28T00:00:00Z",
        parser_version="ulif-dictua-v2",
        status="ok",
        homonym_index=3,
        homonym_checked=1,
        db_path=db_path,
    )

    records = sources_db.get_ulif_word_records(["замок"], db_path=db_path)
    assert len(records) == 1
    rec = records[0]
    assert rec["entry_count"] == 3
    assert len(rec["entries"]) == 3

    indexes = [e["homonym_index"] for e in rec["entries"]]
    assert indexes == [1, 2, 3]

    headwords = [e["canonical_headword"] for e in rec["entries"]]
    assert headwords == ["За́мок", "за́мок", "замо́к"]

    glosses = [e["sense_gloss"] for e in rec["entries"]]
    assert glosses == ["(будівля)", "(феодальний)", "(пристрій для замикання)"]

    # Each homonym's sections remain separate (not merged)
    assert "paradigm" in rec["entries"][0]["sections"]
    assert rec["entries"][0]["sections"]["paradigm"] != []
    assert rec["entries"][1]["sections"]["synonyms"] != []
    assert rec["entries"][2]["sections"]["phraseology"] != []


def test_unverified_entries_have_verified_false_and_empty_sections(tmp_path):
    db_path = tmp_path / "sources.db"

    sources_db.store_ulif_dictua_entry(
        word="неперевірено",
        canonical_headword="непереві́рено",
        sections={"synonyms": [{"terms": [{"text": "тест"}]}]},
        raw_responses={"synonyms": "<html>raw</html>"},
        retrieved_at="2026-09-28T00:00:00Z",
        parser_version="ulif-dictua-v2",
        status="ok",
        homonym_index=1,
        homonym_checked=0,  # Unverified!
        db_path=db_path,
    )

    records = sources_db.get_ulif_word_records(["неперевірено"], db_path=db_path)
    assert len(records) == 1
    rec = records[0]
    assert rec["verified"] is False
    assert rec["status"] == "unverified"
    entry = rec["entries"][0]
    assert entry["verified"] is False
    assert entry["sections"] == {}  # Unverified rows have no sections
    assert entry["forms"] == []
    assert entry["forms_state"] == "unverified"


def test_missing_word_returns_explicit_not_found(tmp_path):
    db_path = tmp_path / "sources.db"
    conn = sqlite3.connect(str(db_path))
    sources_db.ensure_ulif_dictua_schema(conn)
    conn.close()

    records = sources_db.get_ulif_word_records(["невідомеслово123"], db_path=db_path)
    assert len(records) == 1
    assert records[0]["word"] == "невідомеслово123"
    assert records[0]["status"] == "not_found"
    assert records[0]["verified"] is False
    assert records[0]["entries"] == []


def test_forms_state_transitions_and_failure_reporting(tmp_path):
    db_path = tmp_path / "sources.db"
    par_html = _read_fixture("zamok-entry-1.html")

    sources_db.store_ulif_dictua_entry(
        word="замок",
        canonical_headword="За́мок",
        sections={"paradigm": {"rows": [["Називний", "За́мок"]]}},
        raw_responses={"paradigm": par_html},
        retrieved_at="2026-09-28T00:00:00Z",
        parser_version="ulif-dictua-v2",
        status="ok",
        homonym_index=1,
        homonym_checked=1,
        db_path=db_path,
    )

    # 1. Before build: forms_state is unbuilt
    rec1 = sources_db.get_ulif_word_records(["замок"], db_path=db_path)
    assert rec1[0]["forms_state"] == "unbuilt"
    assert rec1[0]["forms"] == []

    # 2. Simulate building state
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO ulif_forms_build (id, state, parser_version, total_entries, entries_done, entries_failed, total_forms, started_at, finished_at) "
        "VALUES (1, 'building', ?, 1, 0, 0, 0, '2026-09-30T00:00:00Z', '') "
        "ON CONFLICT(id) DO UPDATE SET state='building'",
        (ulif_forms.ULIF_FORMS_PARSER_VERSION,),
    )
    conn.commit()
    conn.close()
    rec2 = sources_db.get_ulif_word_records(["замок"], db_path=db_path)
    assert rec2[0]["forms_state"] == "building"

    # 3. Simulate stale parser version
    conn = sqlite3.connect(str(db_path))
    conn.execute("UPDATE ulif_forms_build SET state='complete', parser_version='old-v0' WHERE id=1")
    conn.commit()
    conn.close()
    rec3 = sources_db.get_ulif_word_records(["замок"], db_path=db_path)
    assert rec3[0]["forms_state"] == "stale_parser_version"

    # 4. Actual complete build
    ulif_forms.build_ulif_forms(db_path=db_path)
    rec4 = sources_db.get_ulif_word_records(["замок"], db_path=db_path)
    assert rec4[0]["forms_state"] == "complete"
    assert len(rec4[0]["forms"]) > 0


def test_batch_query_returns_ordered_records(tmp_path):
    db_path = tmp_path / "sources.db"

    sources_db.store_ulif_dictua_entry(
        word="слово",
        canonical_headword="сло́во",
        sections={"paradigm": {"rows": [["Називний", "сло́во"]]}},
        raw_responses={"paradigm": "<html>slovo</html>"},
        retrieved_at="2026-09-28T00:00:00Z",
        parser_version="ulif-dictua-v2",
        status="ok",
        homonym_index=1,
        homonym_checked=1,
        db_path=db_path,
    )
    sources_db.store_ulif_dictua_entry(
        word="мова",
        canonical_headword="мо́ва",
        sections={"paradigm": {"rows": [["Називний", "мо́ва"]]}},
        raw_responses={"paradigm": "<html>mova</html>"},
        retrieved_at="2026-09-28T00:00:00Z",
        parser_version="ulif-dictua-v2",
        status="ok",
        homonym_index=1,
        homonym_checked=1,
        db_path=db_path,
    )

    query_words = ["мова", "слово", "відсутнє"]
    records = sources_db.get_ulif_word_records(query_words, db_path=db_path)
    assert len(records) == 3
    assert [r["word"] for r in records] == query_words
    assert records[0]["status"] == "ok"
    assert records[1]["status"] == "ok"
    assert records[2]["status"] == "not_found"
