"""Tests for ULIF derived forms builder, verification, and disagreement reporting."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.lexicon import ulif_raw_cache
from scripts.lexicon.runner import ulif_forms
from scripts.wiki import sources_db

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "ulif_dictua"


def _read_fixture(name: str) -> str:
    path = FIXTURES_DIR / name
    if not path.is_file():
        raise FileNotFoundError(f"Fixture not found: {path}")
    return path.read_text(encoding="utf-8")


def test_ensure_ulif_dictua_schema_creates_forms_tables(tmp_path):
    db_path = tmp_path / "schema_test.db"
    conn = sqlite3.connect(str(db_path))
    try:
        sources_db.ensure_ulif_dictua_schema(conn)
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert "ulif_dictua_entries" in tables
        assert "ulif_dictua_sections" in tables
        assert "ulif_forms" in tables
        assert "ulif_forms_failures" in tables
        assert "ulif_forms_build" in tables

        # Indexes exist
        indexes = {
            row[1]
            for row in conn.execute(
                "SELECT type, name FROM sqlite_master WHERE type='index'"
            ).fetchall()
        }
        assert "idx_ulif_forms_entry_id" in indexes
        assert "idx_ulif_forms_form_unstressed" in indexes
        assert "idx_ulif_forms_failures_entry_id" in indexes
    finally:
        conn.close()


def test_ulif_forms_build_idempotent_and_verifies(tmp_path):
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

    report1 = ulif_forms.build_ulif_forms(db_path=db_path)
    assert report1["state"] == "complete"
    assert report1["total_verified"] == 1
    assert report1["entries_done"] == 1
    assert report1["entries_failed"] == 0
    assert report1["total_forms"] > 0

    ver1 = ulif_forms.verify_ulif_forms(db_path)
    assert ver1["verified"] is True
    assert ver1["entries_done"] == 1

    # Idempotent second build produces identical counts
    report2 = ulif_forms.build_ulif_forms(db_path=db_path)
    assert report2["state"] == "complete"
    assert report2["entries_done"] == 1
    assert report2["total_forms"] == report1["total_forms"]

    ver2 = ulif_forms.verify_ulif_forms(db_path)
    assert ver2["verified"] is True


def test_stored_headword_empty_derives_identity_from_raw(tmp_path):
    """Hazard 1: 12,899 checked entries have canonical_headword=''.

    The builder must derive the lemma row from the raw page and record
    stored-vs-raw mismatches.
    """
    db_path = tmp_path / "sources.db"
    par_html = _read_fixture("zamok-entry-1.html")

    sources_db.store_ulif_dictua_entry(
        word="замок",
        canonical_headword="",  # empty stored headword
        grammatical_label="",   # empty stored grammar
        sections={"paradigm": {"rows": [["Називний", "За́мок"]]}},
        raw_responses={"paradigm": par_html},
        retrieved_at="2026-09-28T00:00:00Z",
        parser_version="ulif-dictua-v2",
        status="ok",
        homonym_index=1,
        homonym_checked=1,
        db_path=db_path,
    )

    report_path = tmp_path / "report.json"
    rep = ulif_forms.build_ulif_forms(db_path=db_path, report_path=report_path)
    assert rep["state"] == "complete"
    assert rep["mismatches_count"] == 1
    assert rep["mismatches_sample"][0]["stored_headword"] == ""
    assert rep["mismatches_sample"][0]["parsed_headword"] == "За́мок"

    report_data = json.loads(report_path.read_text(encoding="utf-8"))
    assert report_data["mismatches_count"] == 1

    records = sources_db.get_ulif_word_records(["замок"], db_path=db_path)
    first_entry = records[0]["entries"][0]
    assert first_entry["canonical_headword"] == ""  # preserved byte-for-byte as stored
    raw_id = first_entry["identity_from_raw"]
    assert raw_id["canonical_headword"] == "За́мок"
    assert raw_id["stored_matches_raw"] is False
    assert "canonical_headword" in raw_id["mismatches"]
    assert "grammatical_label" in raw_id["mismatches"]


def test_empty_article_capture_classified_as_extraction_failed(tmp_path):
    """Hazard 2: empty article capture (хто, абихто class) with zero word_style/gram_style.

    Must classify as extraction_failed: empty_article with locator, never emit empty lemma form.
    """
    db_path = tmp_path / "sources.db"
    empty_article_html = """
    <html><body>
      <div id="ContentPlaceHolder1_article">
        <!-- article container present but zero word_style / gram_style -->
      </div>
    </body></html>
    """

    sources_db.store_ulif_dictua_entry(
        word="хто",
        canonical_headword="",
        sections={},
        raw_responses={"paradigm": empty_article_html},
        retrieved_at="2026-09-28T00:00:00Z",
        parser_version="ulif-dictua-v2",
        status="ok",
        homonym_index=1,
        homonym_checked=1,
        db_path=db_path,
    )

    rep = ulif_forms.build_ulif_forms(db_path=db_path)
    assert rep["state"] == "complete"
    assert rep["entries_done"] == 0
    assert rep["entries_failed"] == 1
    assert rep["failures_by_reason"].get("extraction_failed: empty_article") == 1

    records = sources_db.get_ulif_word_records(["хто"], db_path=db_path)
    first_entry = records[0]["entries"][0]
    assert first_entry["forms"] == []
    assert first_entry["forms_state"] == "extraction_failed: empty_article"
    assert first_entry["forms_failure"]["reason"] == "extraction_failed: empty_article"
    assert first_entry["forms_failure"]["locator"] == f"ulif:entry:{first_entry['entry_id']}"


def test_manifest_without_paradigm_key_handles_weaker_provenance(tmp_path):
    """Hazard 4: Entries with no paradigm key in manifest.

    If nonempty stored headword exists: base row only from stored columns, flagged
    raw_entry_page_absent, never forms-complete, is_invariable=False (do not infer invariable).
    Done/failed accounting does not double-count entries with both base assertion and failure.
    """
    db_path = tmp_path / "sources.db"
    syn_html = "<html>synonyms only</html>"

    sources_db.store_ulif_dictua_entry(
        word="академічний",
        canonical_headword="академі́чний",
        grammatical_label="прикметник",
        sections={"synonyms": [{"terms": [{"text": "науковий"}]}]},
        raw_responses={"synonyms": syn_html},  # No 'paradigm' key in manifest
        retrieved_at="2026-09-28T00:00:00Z",
        parser_version="ulif-dictua-v2",
        status="ok",
        homonym_index=1,
        homonym_checked=1,
        db_path=db_path,
    )

    rep = ulif_forms.build_ulif_forms(db_path=db_path)
    assert rep["state"] == "complete"
    assert rep["entries_done"] == 0
    assert rep["entries_failed"] == 1
    assert rep["failures_by_reason"].get("raw_entry_page_absent") == 1

    records = sources_db.get_ulif_word_records(["академічний"], db_path=db_path)
    first_entry = records[0]["entries"][0]
    assert len(first_entry["forms"]) == 1
    base_form = first_entry["forms"][0]
    assert base_form["is_lemma"] is True
    assert base_form["is_invariable"] is False  # Must NOT infer invariable status
    assert base_form["form_stressed"] == "академі́чний"

    # Never forms-complete when raw entry page is absent
    assert first_entry["forms_state"] == "raw_entry_page_absent"
    assert first_entry["forms_failure"]["reason"] == "raw_entry_page_absent"

    raw_id = first_entry["identity_from_raw"]
    assert raw_id["raw_entry_page_absent"] is True
    assert raw_id["weaker_provenance"] == "stored_columns_only"


def test_manifest_missing_paradigm_and_empty_stored_headword_fails(tmp_path):
    """When paradigm page is absent AND stored headword is empty, records raw_entry_page_absent failure."""
    db_path = tmp_path / "sources.db"

    sources_db.store_ulif_dictua_entry(
        word="невідомо",
        canonical_headword="",
        sections={"synonyms": [{"terms": [{"text": "тест"}]}]},
        raw_responses={"synonyms": "<html>synonyms</html>"},
        retrieved_at="2026-09-28T00:00:00Z",
        parser_version="ulif-dictua-v2",
        status="ok",
        homonym_index=1,
        homonym_checked=1,
        db_path=db_path,
    )

    rep = ulif_forms.build_ulif_forms(db_path=db_path)
    assert rep["state"] == "complete"
    assert rep["entries_done"] == 0
    assert rep["entries_failed"] == 1
    assert rep["failures_by_reason"].get("raw_entry_page_absent") == 1


def test_missing_raw_blob_records_explicit_failure(tmp_path):
    db_path = tmp_path / "sources.db"
    # Store entry with raw response, then delete the raw blob
    sources_db.store_ulif_dictua_entry(
        word="стіл",
        canonical_headword="сті́л",
        sections={"paradigm": {"rows": [["Називний", "сті́л"]]}},
        raw_responses={"paradigm": "<html>dummy</html>"},
        retrieved_at="2026-09-28T00:00:00Z",
        parser_version="ulif-dictua-v2",
        status="ok",
        homonym_index=1,
        homonym_checked=1,
        db_path=db_path,
    )

    # Delete the paradigm raw blob from cache
    raw_cache = ulif_raw_cache.cache_path(db_path)
    with sqlite3.connect(raw_cache) as raw_conn:
        manifest_body = raw_conn.execute("SELECT body FROM ulif_dictua_raw_responses WHERE content_type='application/json'").fetchone()[0]
        manifest = json.loads(manifest_body)
        par_sha = manifest["paradigm"].removeprefix("sha256:")
        raw_conn.execute("DELETE FROM ulif_dictua_raw_responses WHERE response_sha256 = ?", (par_sha,))
        raw_conn.commit()

    rep = ulif_forms.build_ulif_forms(db_path=db_path)
    assert rep["state"] == "complete"
    assert rep["entries_failed"] == 1
    assert rep["failures_by_reason"].get("missing_raw_paradigm_blob") == 1


def test_cli_subcommands_via_subprocess(tmp_path):
    db_path = tmp_path / "sources_cli.db"
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

    rep_path = tmp_path / "build_report.json"
    raw_cache = ulif_raw_cache.cache_path(db_path)

    # 1. build CLI
    proc_build = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.lexicon.runner.ulif_forms",
            "build",
            "--db",
            str(db_path),
            "--raw-cache",
            str(raw_cache),
            "--report",
            str(rep_path),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert proc_build.returncode == 0
    assert "Build complete" in proc_build.stdout
    assert rep_path.is_file()

    # 2. verify CLI
    proc_verify = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.lexicon.runner.ulif_forms",
            "verify",
            "--db",
            str(db_path),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert proc_verify.returncode == 0
    assert "Verification PASSED" in proc_verify.stdout

    # 3. disagreement-report CLI
    tsv_path = tmp_path / "disagreements.tsv"
    proc_disagree = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.lexicon.runner.ulif_forms",
            "disagreement-report",
            "--db",
            str(db_path),
            "--out",
            str(tsv_path),
            "--all",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert proc_disagree.returncode == 0
    assert tsv_path.is_file()
    lines = tsv_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) > 1
    assert "entry_id\tentry_key" in lines[0]


def test_cli_help_standard():
    proc = subprocess.run(
        [sys.executable, "-m", "scripts.lexicon.runner.ulif_forms", "--help"],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert proc.returncode == 0
    out = proc.stdout
    assert "Examples:" in out
    assert "Outputs:" in out
    assert "Exit codes:" in out
    assert "Related:" in out


def test_f1_preposition_variant_splitting():
    """F1: Split per comma-variant, override or inherit cell prefix, strip from form surface."""
    from scripts.lexicon.runner.ulif_dictua_parse import _split_cell_surface

    # Case 1: comma variant with overriding preposition (e.g. Абакан #1629)
    rows1 = _split_cell_surface("на/в Абака́ні, по Абака́ну")
    assert len(rows1) == 2
    assert rows1[0]["form_stressed"] == "Абака́ні"
    assert rows1[0]["form_unstressed"] == "Абакані"
    assert rows1[0]["preposition"] == "на/в"
    assert rows1[1]["form_stressed"] == "Абака́ну"
    assert rows1[1]["form_unstressed"] == "Абакану"
    assert rows1[1]["preposition"] == "по"

    # Case 2: при preposition (e.g. Євграфов #85)
    rows2 = _split_cell_surface("при Євгра́фові, Євгра́фову")
    assert len(rows2) == 2
    assert rows2[0]["form_stressed"] == "Євгра́фові"
    assert rows2[0]["preposition"] == "при"
    assert rows2[1]["form_stressed"] == "Євгра́фову"
    assert rows2[1]["preposition"] == "при"  # Inherits cell prefix при


def test_f3_verify_detects_source_modification(tmp_path):
    """F3: verify_ulif_forms detects post-build modifications to ulif_dictua_entries."""
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
    assert ulif_forms.verify_ulif_forms(db_path)["verified"] is True

    # Mutate canonical_headword directly in database
    conn = sqlite3.connect(str(db_path))
    conn.execute("UPDATE ulif_dictua_entries SET canonical_headword = 'За́мок-інший' WHERE id = 1")
    conn.commit()
    conn.close()

    # Verify fails with stale source_fingerprint
    ver = ulif_forms.verify_ulif_forms(db_path)
    assert ver["verified"] is False
    assert "stale source_fingerprint" in ver["error"]


def test_f6_batch_validation_and_parser_exception_isolation(tmp_path):
    """F6: Rejects invalid batch_size and isolates parser exceptions without corrupting state."""
    db_path = tmp_path / "sources.db"
    sources_db.store_ulif_dictua_entry(
        word="замок",
        canonical_headword="За́мок",
        sections={"paradigm": {"rows": [["Називний", "За́мок"]]}},
        raw_responses={"paradigm": "<html>bad</html>"},
        retrieved_at="2026-09-28T00:00:00Z",
        parser_version="ulif-dictua-v2",
        status="ok",
        homonym_index=1,
        homonym_checked=1,
        db_path=db_path,
    )

    # Rejects invalid batch size
    with pytest.raises(ValueError, match="batch_size must be positive"):
        ulif_forms.build_ulif_forms(db_path=db_path, batch_size=0)


def test_f9_full_mismatches_itemization_and_sidecar(tmp_path):
    """F9: Itemize all mismatches with locators and write .mismatches.jsonl sidecar."""
    db_path = tmp_path / "sources.db"
    par_html = _read_fixture("zamok-entry-1.html")

    sources_db.store_ulif_dictua_entry(
        word="замок",
        canonical_headword="Неправильний",
        grammatical_label="неправильна граматика",
        sense_gloss="неправильний глос",
        sections={"paradigm": {"rows": [["Називний", "За́мок"]]}},
        raw_responses={"paradigm": par_html},
        retrieved_at="2026-09-28T00:00:00Z",
        parser_version="ulif-dictua-v2",
        status="ok",
        homonym_index=1,
        homonym_checked=1,
        db_path=db_path,
    )

    report_path = tmp_path / "build_report.json"
    rep = ulif_forms.build_ulif_forms(db_path=db_path, report_path=report_path)
    assert rep["mismatches_count"] == 1
    mismatch = rep["mismatches"][0]
    assert mismatch["locator"] == "ulif:entry:1"
    assert "canonical_headword" in mismatch["fields"]
    assert "grammatical_label" in mismatch["fields"]
    assert "sense_gloss" in mismatch["fields"]

    sidecar = report_path.with_suffix(".mismatches.jsonl")
    assert sidecar.is_file()
    lines = sidecar.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    parsed_sidecar = json.loads(lines[0])
    assert parsed_sidecar["locator"] == "ulif:entry:1"


def test_f12_disagreement_report_separates_oracle_not_applicable(tmp_path, monkeypatch):
    """F12: Oracle invalid_input is classified as oracle_not_applicable and excluded from disagreed_count."""
    db_path = tmp_path / "sources.db"
    conn = sqlite3.connect(str(db_path))
    sources_db.ensure_ulif_dictua_schema(conn)
    conn.execute(
        """
        INSERT INTO ulif_dictua_entries (
            id, normalized_query, homonym_index, canonical_headword, grammatical_label,
            sense_gloss, raw_response_ref, status, homonym_checked, retrieved_at, parser_version
        ) VALUES (1, 'тест', 1, 'тест', 'іменник', '', '', 'ok', 1, '2026-09-30T00:00:00Z', 'ulif-dictua-v2')
        """
    )
    conn.execute(
        """
        INSERT INTO ulif_forms (
            id, entry_id, entry_key, form_unstressed, form_stressed,
            stress_vowel_indices, grammatical_tags, unmapped_labels,
            variant_order, preposition, marked_asterisk, is_lemma,
            is_invariable, dual_stress_flag, pedagogical_stressed_form,
            source_page_sha256, parser_version, source_entry_fingerprint
        ) VALUES (
            1, 1, 'тест#1', '123-abc', '123-abc',
            '[]', '[]', '[]',
            1, '', 0, 1,
            0, 0, '123-abc',
            'sha', 'ulif-forms-v2', 'fp'
        )
        """
    )
    conn.commit()
    conn.close()

    out_path = tmp_path / "disagreements.json"
    res = ulif_forms.generate_disagreement_report(db_path=db_path, out_path=out_path)
    assert res["total_checked"] == 1
    assert res["not_applicable_count"] == 1
    assert res["disagreed_count"] == 0  # Not counted as a stress disagreement!

    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert data["records"][0]["disagreement_type"] == "oracle_not_applicable"
    assert data["records"][0]["agrees"] is None
