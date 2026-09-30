"""Tests for ULIF derived forms builder, verification, and disagreement reporting."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

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
    raw_entry_page_absent, weaker provenance, is_invariable=False (do not infer invariable).
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
    assert rep["entries_done"] == 1
    assert rep["entries_failed"] == 0

    records = sources_db.get_ulif_word_records(["академічний"], db_path=db_path)
    first_entry = records[0]["entries"][0]
    assert len(first_entry["forms"]) == 1
    base_form = first_entry["forms"][0]
    assert base_form["is_lemma"] is True
    assert base_form["is_invariable"] is False  # Must NOT infer invariable status
    assert base_form["form_stressed"] == "академі́чний"

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
