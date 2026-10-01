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

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from scripts.lexicon import ulif_raw_cache
from scripts.lexicon.runner import ulif_forms
from scripts.wiki import sources_db

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "ulif_dictua"


@pytest.mark.parametrize("gap", ["empty", "absent"])
def test_reader_keeps_relation_infrastructure_reason_over_source_gap(tmp_path, monkeypatch, gap):
    """The combined-fault reader withholds forms before and after forcing build complete."""
    db_path = tmp_path / "sources.db"
    relation = "<html>synthetic relation</html>"
    raw = {"phraseology": relation}
    if gap == "empty":
        raw["paradigm"] = '<div id="ContentPlaceHolder1_article"></div>'
    sources_db.store_ulif_dictua_entry(
        word="placeholder", canonical_headword="placeholder", sections={}, raw_responses=raw,
        retrieved_at="2026-09-28T00:00:00Z", parser_version="ulif-dictua-v2", status="ok",
        homonym_index=1, homonym_checked=1, db_path=db_path,
    )
    original_get = ulif_raw_cache.get
    relation_sha = hashlib.sha256(relation.encode()).hexdigest()

    def faulty_get(sha, **kwargs):
        if sha == relation_sha:
            raise sqlite3.OperationalError("synthetic relation I/O failure")
        return original_get(sha, **kwargs)

    monkeypatch.setattr(ulif_raw_cache, "get", faulty_get)
    report = ulif_forms.build_ulif_forms(db_path=db_path)
    assert report["state"] == "failed"
    locator = f"ulif:entry:1:phraseology:sha256:{relation_sha}"
    for state in ("failed", "complete"):
        with sqlite3.connect(db_path) as conn:
            conn.execute("UPDATE ulif_forms_build SET state=?", (state,))
        entry = sources_db.get_ulif_word_records(["placeholder"], db_path=db_path)[0]["entries"][0]
        assert entry["canonical_headword"] == "placeholder"
        assert entry["forms"] == []
        assert entry["forms_state"] == "raw_cache_error"
        assert entry["forms_failure"] == {"reason": "raw_cache_error", "locator": locator}


def test_runbook_source_provenance_and_relative_examples():
    """Pin literal supported provenance and all five formerly absolute host-path occurrences."""
    text = (Path(__file__).parents[1] / "docs/atlas/word-cards/ulif-source-records.md").read_text()
    expected_url = "https://lcorp.ulif.org.ua/dictua"
    expected_label = "«Словники України» (Український мовно-інформаційний фонд НАН України)"
    assert expected_url == sources_db.ULIF_DICTUA_OFFICIAL_URL
    assert expected_label == sources_db.ULIF_DICTUA_ATTRIBUTION_LABEL
    assert f'"official_url": "{expected_url}"' in text
    assert f'"attribution_label": "{expected_label}"' in text
    assert "/home/" not in text
    assert text.count(".venv/bin/python -m ") == 4
    assert "--raw-cache data/lexicon/cache/ulif_raw.sqlite" in text
    for subcommand in ("build", "verify", "disagreement-report"):
        assert f".venv/bin/python -m scripts.lexicon.runner.ulif_forms {subcommand}" in text


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
    assert rec1[0]["entries"][0]["forms_state"] == "unbuilt"
    assert rec1[0]["entries"][0]["forms"] == []
    # F7: No top-level homonyms alias or single-entry clones
    assert "homonyms" not in rec1[0]
    assert "canonical_headword" not in rec1[0]
    assert "forms_state" not in rec1[0]

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
    assert rec2[0]["entries"][0]["forms_state"] == "building"

    # 3. Simulate stale parser version
    conn = sqlite3.connect(str(db_path))
    conn.execute("UPDATE ulif_forms_build SET state='complete', parser_version='old-v0' WHERE id=1")
    conn.commit()
    conn.close()
    rec3 = sources_db.get_ulif_word_records(["замок"], db_path=db_path)
    assert rec3[0]["entries"][0]["forms_state"] == "stale_parser_version"

    # 4. Actual complete build
    ulif_forms.build_ulif_forms(db_path=db_path)
    rec4 = sources_db.get_ulif_word_records(["замок"], db_path=db_path)
    assert rec4[0]["entries"][0]["forms_state"] == "complete"
    assert len(rec4[0]["entries"][0]["forms"]) > 0


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


def test_missing_tables_reported_explicitly(tmp_path):
    """F4: Missing forms/failures/sections tables report explicit missing_table state."""
    db_path = tmp_path / "sources.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE ulif_dictua_entries (
            id INTEGER PRIMARY KEY,
            normalized_query TEXT,
            homonym_index INTEGER,
            canonical_headword TEXT,
            grammatical_label TEXT,
            sense_gloss TEXT,
            raw_response_ref TEXT,
            status TEXT,
            homonym_checked INTEGER,
            retrieved_at TEXT,
            parser_version TEXT
        )
        """
    )
    conn.execute(
        """
        INSERT INTO ulif_dictua_entries VALUES
        (1, 'тест', 1, 'тест', 'іменник', '', '', 'ok', 1, '2026-09-30T00:00:00Z', 'ulif-dictua-v2')
        """
    )
    conn.commit()
    conn.close()

    records = sources_db.get_ulif_word_records(["тест"], db_path=db_path)
    assert len(records) == 1
    entry = records[0]["entries"][0]
    assert entry["forms_state"] == "missing_table"
    assert entry["sections_state"] == "missing_table"


def test_corrupt_manifest_and_stale_fingerprint_isolation(tmp_path):
    """F2/F3/F5: Isolate corrupt raw refs per-entry and detect stale entry fingerprints."""
    db_path = tmp_path / "sources.db"
    par_html = _read_fixture("zamok-entry-1.html")

    # Entry 1: healthy entry
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
    # Entry 2: corrupt raw response ref
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        INSERT INTO ulif_dictua_entries (
            id, normalized_query, homonym_index, canonical_headword,
            grammatical_label, sense_gloss, raw_response_ref, status,
            homonym_checked, retrieved_at, parser_version
        ) VALUES (2, 'битий', 1, 'би́тий', 'прикметник', '', 'sha256:corruptbadhash', 'ok', 1, '2026-09-30T00:00:00Z', 'ulif-dictua-v2')
        """
    )
    conn.commit()
    conn.close()

    ulif_forms.build_ulif_forms(db_path=db_path)

    # Batch query containing both healthy and corrupt entries
    records = sources_db.get_ulif_word_records(["замок", "битий"], db_path=db_path)
    assert len(records) == 2

    # Healthy entry has complete forms
    rec_healthy = records[0]
    assert rec_healthy["entries"][0]["forms_state"] == "complete"
    assert rec_healthy["entries"][0]["identity_from_raw"]["source_page_sha256"] != ""

    # Corrupt entry does not fail batch; returns isolated raw error
    rec_corrupt = records[1]
    assert rec_corrupt["entries"][0]["identity_from_raw"]["error"] == "raw_manifest_corrupt"
    assert rec_corrupt["entries"][0]["identity_from_raw"]["stored_matches_raw"] is None

    # F3: Mutate canonical_headword of entry 1 in source database
    conn = sqlite3.connect(str(db_path))
    conn.execute("UPDATE ulif_dictua_entries SET canonical_headword = 'За́мок-змінений' WHERE id = 1")
    conn.commit()
    conn.close()

    # Querying again immediately flags stale_source_snapshot
    records_after_mutation = sources_db.get_ulif_word_records(["замок"], db_path=db_path)
    assert records_after_mutation[0]["entries"][0]["forms_state"] == "stale_source_snapshot"


def test_nested_relation_unavailable_blobs_reported_per_entry(tmp_path):
    """Item 4: Missing/corrupt nested relation blobs reported in identity_from_raw per entry."""
    db_path = tmp_path / "sources.db"
    par_html = _read_fixture("zamok-entry-1.html")
    syn_html = "<html>synonyms content</html>"
    raw_cache_path = ulif_raw_cache.cache_path(db_path)

    # Entry 1: will have missing synonym blob and malformed phraseology ref
    sources_db.store_ulif_dictua_entry(
        word="замок",
        canonical_headword="За́мок",
        sections={
            "paradigm": {"rows": [["Називний", "За́мок"]]},
            "synonyms": [{"text": "твердиня"}],
        },
        raw_responses={"paradigm": par_html, "synonyms": syn_html},
        retrieved_at="2026-09-28T00:00:00Z",
        parser_version="ulif-dictua-v2",
        status="ok",
        homonym_index=1,
        homonym_checked=1,
        db_path=db_path,
    )

    # Entry 2: healthy entry
    sources_db.store_ulif_dictua_entry(
        word="будинок",
        canonical_headword="Буди́нок",
        sections={"paradigm": {"rows": [["Називний", "Буди́нок"]]}},
        raw_responses={"paradigm": par_html},
        retrieved_at="2026-09-28T00:00:00Z",
        parser_version="ulif-dictua-v2",
        status="ok",
        homonym_index=1,
        homonym_checked=1,
        db_path=db_path,
    )

    # Tamper with raw cache for Entry 1 before building forms:
    # 1. Delete synonyms blob so it's missing
    syn_sha = hashlib.sha256(syn_html.encode("utf-8")).hexdigest()
    cache_conn = sqlite3.connect(str(raw_cache_path))
    cache_conn.execute("DELETE FROM ulif_dictua_raw_responses WHERE response_sha256 = ?", (syn_sha,))
    cache_conn.commit()

    # 2. Add a malformed phraseology ref into entry 1's manifest
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    entry1 = conn.execute("SELECT raw_response_ref FROM ulif_dictua_entries WHERE id = 1").fetchone()
    manifest_sha = entry1["raw_response_ref"].removeprefix("sha256:")
    manifest_bytes = ulif_raw_cache.get(manifest_sha, path=raw_cache_path)
    manifest = json.loads(manifest_bytes)
    manifest["phraseology"] = "corrupt_non_sha_ref"
    new_manifest_bytes = json.dumps(manifest).encode("utf-8")
    new_manifest_sha = hashlib.sha256(new_manifest_bytes).hexdigest()
    ulif_raw_cache.put(
        new_manifest_sha, new_manifest_bytes, "application/json", "2026-09-28T00:00:00Z", path=raw_cache_path
    )
    cache_conn.close()

    conn.execute("UPDATE ulif_dictua_entries SET raw_response_ref = ? WHERE id = 1", (f"sha256:{new_manifest_sha}",))
    conn.commit()
    conn.close()

    ulif_forms.build_ulif_forms(db_path=db_path)

    records = sources_db.get_ulif_word_records(["замок", "будинок"], db_path=db_path)
    assert len(records) == 2

    # Entry 1: forms are complete, sections are intact, but unavailable relation blobs are listed
    rec1 = records[0]["entries"][0]
    assert rec1["forms_state"] == "complete"
    assert len(rec1["forms"]) > 0
    assert len(rec1["sections"]["synonyms"]) == 1
    unavail = rec1["identity_from_raw"]["unavailable_relation_blobs"]
    assert len(unavail) == 2
    tabs = {u["tab"]: u for u in unavail}
    assert tabs["synonyms"]["error"] == "missing_blob"
    assert tabs["synonyms"]["ref"] == f"sha256:{syn_sha}"
    assert tabs["synonyms"]["locator"] == f"ulif:entry:1:synonyms:sha256:{syn_sha}"
    assert tabs["phraseology"]["error"] == "corrupt_blob"
    assert tabs["phraseology"]["locator"] == "ulif:entry:1:phraseology"

    # Entry 2: healthy entry in same batch is unaffected
    rec2 = records[1]["entries"][0]
    assert rec2["forms_state"] == "complete"
    assert rec2["identity_from_raw"]["unavailable_relation_blobs"] == []


def test_reader_checks_all_rows_and_missing_tables(tmp_path):
    """Item 1: Reader rejects empty fingerprint on any row and handles missing tables."""
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

    ulif_forms.build_ulif_forms(db_path=db_path)

    # Verify initial read works
    records = sources_db.get_ulif_word_records(["замок"], db_path=db_path)
    assert records[0]["entries"][0]["forms_state"] == "complete"
    assert len(records[0]["entries"][0]["forms"]) > 1

    # Tamper with the SECOND row's source_entry_fingerprint in ulif_forms
    conn = sqlite3.connect(str(db_path))
    rows = conn.execute("SELECT id FROM ulif_forms WHERE entry_id = 1 ORDER BY id").fetchall()
    assert len(rows) > 1
    second_row_id = rows[1][0]
    conn.execute("UPDATE ulif_forms SET source_entry_fingerprint = '' WHERE id = ?", (second_row_id,))
    conn.commit()
    conn.close()

    # Reader must not just check the first row; it must reject the whole set as stale_source_snapshot
    records_tampered = sources_db.get_ulif_word_records(["замок"], db_path=db_path)
    assert records_tampered[0]["entries"][0]["forms_state"] == "stale_source_snapshot"
    assert records_tampered[0]["entries"][0]["forms"] == []

    # Missing ulif_dictua_entries table returns status="unavailable"
    empty_db = tmp_path / "empty.db"
    conn_empty = sqlite3.connect(str(empty_db))
    conn_empty.close()
    unavail_records = sources_db.get_ulif_word_records(["замок"], db_path=empty_db)
    assert unavail_records[0]["status"] == "unavailable"
    assert unavail_records[0]["verified"] is False
    assert unavail_records[0]["entry_count"] == 0


def test_empty_article_identity_no_false_mismatch(tmp_path):
    """R2-N5: Empty visible article sets stored_matches_raw=None and mismatches=None for empty/nonempty stored headword."""
    db_path = tmp_path / "sources.db"
    empty_html = '<html><body><div id="ContentPlaceHolder1_article"><style>.foo{}</style></div></body></html>'

    sources_db.store_ulif_dictua_entry(
        word="хто",
        canonical_headword="",
        grammatical_label="займенник",
        sense_gloss="",
        sections={},
        raw_responses={"paradigm": empty_html},
        retrieved_at="2026-09-28T00:00:00Z",
        parser_version="ulif-dictua-v2",
        status="ok",
        homonym_index=1,
        homonym_checked=1,
        db_path=db_path,
    )

    sources_db.store_ulif_dictua_entry(
        word="ви",
        canonical_headword="Ви",
        grammatical_label="займенник",
        sense_gloss="",
        sections={},
        raw_responses={"paradigm": empty_html},
        retrieved_at="2026-09-28T00:00:00Z",
        parser_version="ulif-dictua-v2",
        status="ok",
        homonym_index=1,
        homonym_checked=1,
        db_path=db_path,
    )

    records = sources_db.get_ulif_word_records(["хто", "ви"], db_path=db_path)
    assert len(records) == 2

    id_x = records[0]["entries"][0]["identity_from_raw"]
    assert id_x["canonical_headword"] == ""
    assert id_x["error"] == "empty_visible_article"
    assert id_x["stored_matches_raw"] is None
    assert id_x["mismatches"] is None

    id_v = records[1]["entries"][0]["identity_from_raw"]
    assert id_v["canonical_headword"] == ""
    assert id_v["error"] == "empty_visible_article"
    assert id_v["stored_matches_raw"] is None
    assert id_v["mismatches"] is None
    assert records[1]["entries"][0]["canonical_headword"] == "Ви"


def test_fingerprint_sqlite_row_and_dict_sort_consistency(tmp_path):
    """R2-N8: sqlite3.Row and dict produce identical fingerprint; reordered rows sort deterministically."""
    db_path = tmp_path / "fp_test.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute(
        "CREATE TABLE t_entries (id INTEGER, normalized_query TEXT, canonical_headword TEXT, grammatical_label TEXT, sense_gloss TEXT, homonym_index INTEGER, homonym_checked INTEGER, raw_response_ref TEXT, status TEXT)"
    )
    conn.execute(
        "CREATE TABLE t_sections (id INTEGER, kind TEXT, source_order INTEGER, sense_or_group_id TEXT, payload_json TEXT)"
    )
    conn.execute("INSERT INTO t_entries VALUES (1, 'замок', 'За́мок', 'іменник', '(будівля)', 1, 1, 'sha256:abc', 'ok')")
    conn.execute("INSERT INTO t_sections VALUES (10, 'synonyms', 0, 'synonyms:1', '{\"term\":\"фортеця\"}')")
    conn.execute(
        "INSERT INTO t_sections VALUES (20, 'paradigm', 0, 'paradigm:1', '{\"rows\":[[\"Називний\",\"За́мок\"]]}')"
    )
    conn.commit()

    entry_row = conn.execute("SELECT * FROM t_entries WHERE id = 1").fetchone()
    sec_rows_1 = conn.execute("SELECT * FROM t_sections ORDER BY id ASC").fetchall()
    sec_rows_2 = conn.execute("SELECT * FROM t_sections ORDER BY id DESC").fetchall()

    fp_rows_1 = sources_db.compute_ulif_entry_fingerprint(entry_row, sec_rows_1)
    fp_rows_2 = sources_db.compute_ulif_entry_fingerprint(entry_row, sec_rows_2)
    assert fp_rows_1 == fp_rows_2

    entry_dict = dict(entry_row)
    sec_dicts = [dict(r) for r in sec_rows_1]
    fp_dicts = sources_db.compute_ulif_entry_fingerprint(entry_dict, sec_dicts)
    assert fp_rows_1 == fp_dicts

    sec_dicts_tampered = [dict(r) for r in sec_rows_1]
    sec_dicts_tampered[0]["payload_json"] = '{"term":"фортеця!"}'
    fp_tampered = sources_db.compute_ulif_entry_fingerprint(entry_dict, sec_dicts_tampered)
    assert fp_rows_1 != fp_tampered
    conn.close()
