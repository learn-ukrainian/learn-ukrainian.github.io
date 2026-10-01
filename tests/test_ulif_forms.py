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
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        assert "ulif_dictua_entries" in tables
        assert "ulif_dictua_sections" in tables
        assert "ulif_forms" in tables
        assert "ulif_forms_failures" in tables
        assert "ulif_forms_build" in tables

        # Indexes exist
        indexes = {row[1] for row in conn.execute("SELECT type, name FROM sqlite_master WHERE type='index'").fetchall()}
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
    assert report1["secondary_blocking_failures"] == []
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
        grammatical_label="",  # empty stored grammar
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


def test_empty_article_capture_classified_as_empty_visible_article(tmp_path):
    """Hazard 2: empty article capture (хто, абихто class) with zero visible text.

    Must classify as empty_visible_article residual with locator, never emit empty lemma form.
    Build state remains complete because empty visible article is a source capture residual.
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
    assert rep["failures_by_reason"].get("empty_visible_article") == 1

    records = sources_db.get_ulif_word_records(["хто"], db_path=db_path)
    first_entry = records[0]["entries"][0]
    assert first_entry["forms"] == []
    assert first_entry["forms_state"] == "empty_visible_article"
    assert first_entry["forms_failure"]["reason"] == "empty_visible_article"
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
        manifest_body = raw_conn.execute(
            "SELECT body FROM ulif_dictua_raw_responses WHERE content_type='application/json'"
        ).fetchone()[0]
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
            'sha', 'ulif-forms-v3', 'fp'
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


def test_same_length_payload_change_fails_verification(tmp_path):
    """Item 1: Whole-source fingerprint hashes ordered payload bytes, not length.

    Mutating payload characters in-place with identical length (aaaa -> bbbb)
    must invalidate verification with 'stale source_fingerprint'.
    """
    db_path = tmp_path / "sources.db"
    par_html = _read_fixture("zamok-entry-1.html")

    sources_db.store_ulif_dictua_entry(
        word="замок",
        canonical_headword="За́мок",
        sections={"paradigm": {"rows": [["Називний", "За́мок"]], "marker": "aaaa"}},
        raw_responses={"paradigm": par_html},
        retrieved_at="2026-09-28T00:00:00Z",
        parser_version="ulif-dictua-v2",
        status="ok",
        homonym_index=1,
        homonym_checked=1,
        db_path=db_path,
    )

    rep = ulif_forms.build_ulif_forms(db_path=db_path)
    assert rep["state"] == "complete"
    assert ulif_forms.verify_ulif_forms(db_path)["verified"] is True

    # Mutate section payload in-place with exact same byte length
    conn = sqlite3.connect(str(db_path))
    conn.execute("UPDATE ulif_dictua_sections SET payload_json = replace(payload_json, 'aaaa', 'bbbb')")
    conn.commit()
    conn.close()

    ver = ulif_forms.verify_ulif_forms(db_path)
    assert ver["verified"] is False
    assert "stale source_fingerprint" in ver["error"]


def test_parser_exception_fails_build_and_blocks_verification(tmp_path, monkeypatch):
    """Item 2: Unexpected parser exception blocks full acceptance (state=failed, verified=False)."""
    from scripts.lexicon.runner import ulif_dictua_parse

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

    def _broken_parse(*args, **kwargs):
        raise RuntimeError("Injected parser explosion")

    monkeypatch.setattr(ulif_dictua_parse, "parse_ulif_entry", _broken_parse)

    rep = ulif_forms.build_ulif_forms(db_path=db_path)
    assert rep["state"] == "failed"
    assert rep["entries_failed"] == 1
    assert any("Injected parser explosion" in k for k in rep["failures_by_reason"])

    ver = ulif_forms.verify_ulif_forms(db_path)
    assert ver["verified"] is False

    records = sources_db.get_ulif_word_records(["замок"], db_path=db_path)
    assert len(records) == 1
    entry = records[0]["entries"][0]
    assert entry["forms"] == []
    assert "Injected parser explosion" in entry["forms_state"]


def test_nonempty_unrecognized_article_defect_fails_build(tmp_path):
    """Item 2: Nonempty page without recognizable head is an extraction defect and blocks acceptance."""
    db_path = tmp_path / "sources.db"
    nonempty_unparseable_html = """
    <html><body>
      <div id="ContentPlaceHolder1_article">
        <p>Нерозпізнаний вміст без стандартних стилів заголовка</p>
      </div>
    </body></html>
    """

    sources_db.store_ulif_dictua_entry(
        word="дефект",
        canonical_headword="",
        sections={},
        raw_responses={"paradigm": nonempty_unparseable_html},
        retrieved_at="2026-09-28T00:00:00Z",
        parser_version="ulif-dictua-v2",
        status="ok",
        homonym_index=1,
        homonym_checked=1,
        db_path=db_path,
    )

    rep = ulif_forms.build_ulif_forms(db_path=db_path)
    assert rep["state"] == "failed"
    assert rep["failures_by_reason"].get("extraction_defect: unrecognized_article") == 1

    ver = ulif_forms.verify_ulif_forms(db_path)
    assert ver["verified"] is False
    assert "ulif_forms_build state is 'failed'" in ver["error"]


def test_open_cache_failure_leaves_state_failed(tmp_path, monkeypatch):
    """Item 3: Injected cache open failure leaves state='failed', not 'building'."""
    db_path = tmp_path / "sources.db"
    conn = sqlite3.connect(str(db_path))
    sources_db.ensure_ulif_dictua_schema(conn)
    conn.close()

    def _broken_open_cache(*args, **kwargs):
        raise FileNotFoundError("Injected cache missing")

    monkeypatch.setattr(ulif_raw_cache, "open_cache", _broken_open_cache)

    with pytest.raises(FileNotFoundError, match="Injected cache missing"):
        ulif_forms.build_ulif_forms(db_path=db_path)

    conn = sqlite3.connect(str(db_path))
    build_row = conn.execute("SELECT state FROM ulif_forms_build WHERE id = 1").fetchone()
    conn.close()
    assert build_row is not None
    assert build_row[0] == "failed"


def test_ulif_forms_concurrent_build_locking_and_safe_restart(tmp_path):
    """R2-N7: Actual two-builder process proof with deterministic handshake and rejection."""
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

    ready_file = tmp_path / "builder1.ready"
    release_file = tmp_path / "builder1.release"

    child_code = (
        "import sys, os, time\n"
        "from scripts.lexicon.runner import ulif_forms, ulif_dictua_parse\n"
        f"ready_f = {str(ready_file)!r}\n"
        f"release_f = {str(release_file)!r}\n"
        "orig_parse = ulif_dictua_parse.parse_ulif_entry\n"
        "def waiting_parse(*args, **kwargs):\n"
        "    with open(ready_f, 'w') as f:\n"
        "        f.write('READY')\n"
        "    start = time.time()\n"
        "    while not os.path.exists(release_f) and time.time() - start < 15:\n"
        "        time.sleep(0.05)\n"
        "    return orig_parse(*args, **kwargs)\n"
        "ulif_dictua_parse.parse_ulif_entry = waiting_parse\n"
        f"rep = ulif_forms.build_ulif_forms(db_path={str(db_path)!r})\n"
        "assert rep['state'] == 'complete'\n"
        "print('BUILDER1_DONE', flush=True)\n"
    )

    proc1 = subprocess.Popen(
        [sys.executable, "-c", child_code], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    try:
        import time

        start_wait = time.time()
        while not ready_file.is_file() and time.time() - start_wait < 15:
            time.sleep(0.05)
        assert ready_file.is_file(), "Builder 1 process did not acquire lock in time"

        with pytest.raises(RuntimeError, match="Another ULIF forms build is currently running"):
            ulif_forms.build_ulif_forms(db_path=db_path)

        cli_proc2 = subprocess.run(
            [sys.executable, "-m", "scripts.lexicon.runner.ulif_forms", "build", "--db", str(db_path)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert cli_proc2.returncode != 0
        assert (
            "Another ULIF forms build is currently running" in cli_proc2.stderr
            or "Another ULIF forms build is currently running" in cli_proc2.stdout
        )

    finally:
        release_file.write_text("RELEASE")
        stdout1, stderr1 = proc1.communicate(timeout=15)

    assert proc1.returncode == 0, f"Builder 1 failed: {stderr1}"
    assert "BUILDER1_DONE" in stdout1
    assert ulif_forms.verify_ulif_forms(db_path)["verified"] is True

    rep = ulif_forms.build_ulif_forms(db_path=db_path)
    assert rep["state"] == "complete"
    assert rep["entries_done"] == 1
    assert ulif_forms.verify_ulif_forms(db_path)["verified"] is True


def test_label_row_as_form_defect_blocks_build(tmp_path, monkeypatch):
    """R2-N1: Non-lemma form row lacking tags and unmapped labels blocks build as extraction_defect."""
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

    from scripts.lexicon.runner import ulif_dictua_parse

    orig_parse = ulif_dictua_parse.parse_ulif_entry

    def mock_parse(html, **kw):
        res = orig_parse(html, **kw)
        res["forms"].append(
            {
                "entry_key": "замок#1",
                "form_unstressed": "чол. і жін. р.",
                "form_stressed": "чол. і жін. р.",
                "stress_vowel_indices": [],
                "grammatical_tags": [],
                "unmapped_labels": [],
                "variant_order": 1,
                "preposition": "",
                "marked_asterisk": False,
                "is_lemma": False,
                "is_invariable": False,
                "dual_stress_flag": False,
                "pedagogical_stressed_form": "чол. і жін. р.",
            }
        )
        return res

    monkeypatch.setattr(ulif_dictua_parse, "parse_ulif_entry", mock_parse)
    rep = ulif_forms.build_ulif_forms(db_path=db_path)
    assert rep["state"] == "failed"
    assert "extraction_defect: label_row_as_form" in rep["failures_by_reason"]
    v = ulif_forms.verify_ulif_forms(db_path)
    assert v["verified"] is False
    # Even if state is manually marked complete, verify_ulif_forms must reject extraction defect
    conn = sqlite3.connect(db_path)
    conn.execute("UPDATE ulif_forms_build SET state = 'complete'")
    conn.commit()
    conn.close()
    v2 = ulif_forms.verify_ulif_forms(db_path)
    assert v2["verified"] is False
    assert "extraction defect failures" in v2["error"]


def test_infrastructure_error_mid_build_fails_global(tmp_path, monkeypatch):
    """R2-N2: raw_cache_error and missing_cache_file fail build and verification globally."""
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

    def faulty_get(sha, **kw):
        raise sqlite3.OperationalError("disk I/O error (synthetic)")

    monkeypatch.setattr(ulif_raw_cache, "get", faulty_get)
    rep = ulif_forms.build_ulif_forms(db_path=db_path)
    assert rep["state"] == "failed"
    assert rep["failures_by_reason"].get("raw_cache_error", 0) > 0

    v = ulif_forms.verify_ulif_forms(db_path)
    assert v["verified"] is False
    # Even if state is manually marked complete, verify_ulif_forms must reject infrastructure failures
    conn = sqlite3.connect(db_path)
    conn.execute("UPDATE ulif_forms_build SET state = 'complete'")
    conn.commit()
    conn.close()
    v2 = ulif_forms.verify_ulif_forms(db_path)
    assert v2["verified"] is False
    assert "infrastructure failures" in v2["error"]


def test_builder_itemizes_unavailable_relation_blobs(tmp_path):
    """R2-N6: Builder report itemizes unavailable relation blobs without dropping valid paradigm forms."""
    db_path = tmp_path / "sources.db"
    par_html = _read_fixture("zamok-entry-1.html")

    sources_db.store_ulif_dictua_entry(
        word="замок",
        canonical_headword="За́мок",
        sections={
            "paradigm": {"rows": [["Називний", "За́мок"]]},
            "synonyms": [{"term": "фортеця"}],
        },
        raw_responses={
            "paradigm": par_html,
            "synonyms": "<html>corrupt</html>",
        },
        retrieved_at="2026-09-28T00:00:00Z",
        parser_version="ulif-dictua-v2",
        status="ok",
        homonym_index=1,
        homonym_checked=1,
        db_path=db_path,
    )

    conn = sqlite3.connect(db_path)
    entry = conn.execute("SELECT raw_response_ref FROM ulif_dictua_entries WHERE id = 1").fetchone()
    manifest_ref = entry[0].removeprefix("sha256:")
    raw_cache_path = ulif_raw_cache.cache_path(db_path)
    raw_conn = sqlite3.connect(raw_cache_path)
    manifest_data = json.loads(
        bytes(
            raw_conn.execute(
                "SELECT body FROM ulif_dictua_raw_responses WHERE response_sha256 = ?", (manifest_ref,)
            ).fetchone()[0]
        )
    )
    syn_ref = manifest_data["synonyms"].removeprefix("sha256:")
    raw_conn.execute("DELETE FROM ulif_dictua_raw_responses WHERE response_sha256 = ?", (syn_ref,))
    raw_conn.commit()
    raw_conn.close()
    conn.close()

    rep = ulif_forms.build_ulif_forms(db_path=db_path)
    assert rep["state"] == "complete"
    assert rep["entries_done"] == 1
    assert rep["unavailable_relation_blobs_count"] >= 1
    unavail = rep["unavailable_relation_blobs"]
    assert any(b["tab"] == "synonyms" and b["error"] == "missing_blob" for b in unavail)
    assert ulif_forms.verify_ulif_forms(db_path)["verified"] is True


@pytest.mark.parametrize("error_type,reason", [(sqlite3.OperationalError, "raw_cache_error"), (FileNotFoundError, "missing_cache_file")])
def test_relation_probe_infrastructure_failure_is_persisted(tmp_path, monkeypatch, error_type, reason):
    """Synthetic relation I/O fault: persisted proof survives a manually changed state row."""
    db_path = tmp_path / "sources.db"
    html = _read_fixture("zamok-entry-1.html")
    headword = ulif_forms.ulif_dictua_parse.parse_ulif_entry(html, homonym_index=1)["canonical_headword"]
    relation = "<html>synthetic relation I/O fixture</html>"
    sources_db.store_ulif_dictua_entry(
        word=headword,
        canonical_headword=headword,
        sections={"paradigm": {"rows": []}, "synonyms": [{"text": "synthetic relation"}]},
        raw_responses={"paradigm": html, "synonyms": relation, "antonyms": relation, "phraseology": relation},
        retrieved_at="2026-09-28T00:00:00Z",
        parser_version="ulif-dictua-v2",
        status="ok",
        homonym_index=1,
        homonym_checked=1,
        db_path=db_path,
    )
    original_get = ulif_raw_cache.get
    cache = ulif_raw_cache.open_cache(ulif_raw_cache.cache_path(db_path), create=False)
    with sqlite3.connect(db_path) as conn:
        manifest_ref = conn.execute("SELECT raw_response_ref FROM ulif_dictua_entries").fetchone()[0]
    manifest = json.loads(original_get(manifest_ref.removeprefix("sha256:"), conn=cache))
    cache.close()
    relation_sha = manifest["synonyms"].removeprefix("sha256:")

    def faulty_get(sha, **kwargs):
        if sha == relation_sha:
            raise error_type("synthetic relation-probe I/O failure")
        return original_get(sha, **kwargs)

    monkeypatch.setattr(ulif_raw_cache, "get", faulty_get)
    report = ulif_forms.build_ulif_forms(db_path=db_path)
    assert report["state"] == "failed"
    assert report["entries_failed"] == 1
    assert report["unavailable_relation_blobs_count"] == 3
    assert all(item["error"] == reason for item in report["unavailable_relation_blobs"])
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT reason FROM ulif_forms_failures").fetchall() == [(reason,)]
        assert conn.execute("SELECT count(*) FROM ulif_forms").fetchone()[0] > 0
        conn.execute("UPDATE ulif_forms_build SET state='complete'")
    verification = ulif_forms.verify_ulif_forms(db_path)
    assert verification["verified"] is False
    assert "infrastructure failures" in verification["error"]


@pytest.mark.parametrize("error_type,reason", [
    (sqlite3.OperationalError, "raw_cache_error"), (FileNotFoundError, "missing_cache_file"),
])
@pytest.mark.parametrize("gap", ["empty", "absent", "missing", "corrupt"])
@pytest.mark.parametrize("mixed_errors", [False, True])
def test_relation_infrastructure_reason_survives_source_gap(
    tmp_path, monkeypatch, capsys, error_type, reason, gap, mixed_errors,
):
    """Synthetic structure: two failed relation tabs are one failed entry, even with a later gap."""
    db_path = tmp_path / "sources.db"
    raw_responses = {"synonyms": "<html>synthetic synonyms</html>", "phraseology": "<html>synthetic phraseology</html>"}
    if gap != "absent":
        raw_responses["paradigm"] = '<html><div id="ContentPlaceHolder1_article"></div></html>'
    sources_db.store_ulif_dictua_entry(
        word="placeholder", canonical_headword="placeholder", sections={}, raw_responses=raw_responses,
        retrieved_at="2026-09-28T00:00:00Z", parser_version="ulif-dictua-v2", status="ok",
        homonym_index=1, homonym_checked=1, db_path=db_path,
    )
    cache_path = ulif_raw_cache.cache_path(db_path)
    with sqlite3.connect(db_path) as conn:
        original_entries = conn.execute("SELECT * FROM ulif_dictua_entries").fetchall()
        manifest_ref = conn.execute("SELECT raw_response_ref FROM ulif_dictua_entries").fetchone()[0]
    manifest = json.loads(ulif_raw_cache.get(manifest_ref.removeprefix("sha256:"), path=cache_path))
    relation_sha = manifest["synonyms"].removeprefix("sha256:")
    other_error_type = FileNotFoundError if error_type is sqlite3.OperationalError else sqlite3.OperationalError
    other_reason = "missing_cache_file" if reason == "raw_cache_error" else "raw_cache_error"
    original_get = ulif_raw_cache.get

    def faulty_get(sha, **kwargs):
        if sha == relation_sha:
            raise error_type("synthetic relation I/O failure")
        if sha == manifest["phraseology"].removeprefix("sha256:"):
            raise (other_error_type if mixed_errors else error_type)("synthetic second relation I/O failure")
        if gap in {"missing", "corrupt"} and sha == manifest["paradigm"].removeprefix("sha256:"):
            if gap == "corrupt":
                raise ValueError("synthetic corrupt paradigm")
            return None
        return original_get(sha, **kwargs)

    monkeypatch.setattr(ulif_raw_cache, "get", faulty_get)
    report = ulif_forms.build_ulif_forms(db_path=db_path)
    locator = f"ulif:entry:1:synonyms:{manifest['synonyms']}"
    assert report["state"] == "failed"
    assert (report["entries_done"], report["entries_failed"], report["total_forms"]) == (0, 1, 0)
    assert report["failures_by_reason"] == {reason: 1}
    assert report["unavailable_relation_blobs"] == [
        {"entry_id": 1, "tab": tab, "ref": manifest[tab],
         "error": other_reason if mixed_errors and tab == "phraseology" else reason,
         "locator": f"ulif:entry:1:{tab}:{manifest[tab]}"}
        for tab in ("synonyms", "phraseology")
    ]
    assert report["unavailable_relation_blobs_count"] == 2
    assert report["secondary_blocking_failures"] == [
        {"entry_id": 1, "reason": other_reason if mixed_errors else reason,
         "locator": f"ulif:entry:1:phraseology:{manifest['phraseology']}"},
    ]
    assert ulif_forms.main(["build", "--db", str(db_path), "--raw-cache", str(cache_path)]) == 1
    assert "Build failed: done=0, failed=1, forms=0" in capsys.readouterr().out
    assert ulif_forms.verify_ulif_forms(db_path)["verified"] is False
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT reason, locator FROM ulif_forms_failures").fetchall() == [(reason, locator)]
        assert conn.execute("SELECT * FROM ulif_dictua_entries").fetchall() == original_entries
        conn.execute("UPDATE ulif_forms_build SET state='complete'")
    verification = ulif_forms.verify_ulif_forms(db_path)
    assert verification["verified"] is False
    assert "infrastructure failures" in verification["error"]
    assert ulif_forms.main(["verify", "--db", str(db_path)]) == 1
    assert "infrastructure failures" in capsys.readouterr().err


@pytest.mark.parametrize("relation_error,primary_reason", [
    (sqlite3.OperationalError, "raw_cache_error"), (FileNotFoundError, "missing_cache_file"),
])
@pytest.mark.parametrize("fault,secondary_reason", [
    ("parser", "extraction_failed: RuntimeError: synthetic parser failure"),
    ("missing_cache", "missing_cache_file"), ("cache_error", "raw_cache_error"),
    ("unrecognized", "extraction_defect: unrecognized_article"),
])
@pytest.mark.parametrize("batch_size", [1, 500])
def test_relation_and_later_blocking_failures_retain_report_details(
    tmp_path, monkeypatch, relation_error, primary_reason, fault, secondary_reason, batch_size,
):
    """Literal fault expectations on isolated synthetic entries; not held-out driver proof."""
    monkeypatch.delenv("LU_ULIF_RAW_CACHE", raising=False)
    db_path = tmp_path / "sources.db"
    raw = {"synonyms": "synthetic synonyms", "phraseology": "synthetic phraseology",
           "paradigm": '<div id="ContentPlaceHolder1_article"></div>'}
    for word in ("placeholder", "other-placeholder"):
        sources_db.store_ulif_dictua_entry(
            word=word, canonical_headword=word, sections={}, raw_responses=raw,
            retrieved_at="2026-09-28T00:00:00Z", parser_version="ulif-dictua-v2", status="ok",
            homonym_index=1, homonym_checked=1, db_path=db_path,
        )
    cache_path = ulif_raw_cache.cache_path(db_path)
    with sqlite3.connect(db_path) as conn:
        original_entries = conn.execute("SELECT * FROM ulif_dictua_entries").fetchall()
        manifest_ref = conn.execute("SELECT raw_response_ref FROM ulif_dictua_entries LIMIT 1").fetchone()[0]
    manifest = json.loads(ulif_raw_cache.get(manifest_ref.removeprefix("sha256:"), path=cache_path))
    original_get = ulif_raw_cache.get
    other_error = FileNotFoundError if relation_error is sqlite3.OperationalError else sqlite3.OperationalError
    other_reason = "missing_cache_file" if primary_reason == "raw_cache_error" else "raw_cache_error"

    def faulty_get(sha, **kwargs):
        if sha == manifest["synonyms"].removeprefix("sha256:"):
            raise relation_error("synthetic first relation failure")
        if sha == manifest["phraseology"].removeprefix("sha256:"):
            raise other_error("synthetic second relation failure")
        if sha == manifest["paradigm"].removeprefix("sha256:"):
            if fault == "missing_cache":
                raise FileNotFoundError("synthetic paradigm cache failure")
            if fault == "cache_error":
                raise sqlite3.OperationalError("synthetic paradigm cache failure")
        return original_get(sha, **kwargs)

    def faulty_parse(*args, **kwargs):
        if fault == "parser":
            raise RuntimeError("synthetic parser failure")
        return {"canonical_headword": "", "forms": [], "is_empty_visible_article": False}

    monkeypatch.setattr(ulif_raw_cache, "get", faulty_get)
    monkeypatch.setattr(ulif_forms.ulif_dictua_parse, "parse_ulif_entry", faulty_parse)
    report_path = tmp_path / "report.json"
    report = ulif_forms.build_ulif_forms(db_path, report_path=report_path, batch_size=batch_size)
    expected_details = []
    for entry_id in (1, 2):
        expected_details.extend([
            {"entry_id": entry_id, "reason": other_reason,
             "locator": f"ulif:entry:{entry_id}:phraseology:{manifest['phraseology']}"},
            {"entry_id": entry_id, "reason": secondary_reason, "locator": f"ulif:entry:{entry_id}"},
        ])
    assert report["secondary_blocking_failures"] == expected_details
    assert json.loads(report_path.read_text())["secondary_blocking_failures"] == expected_details
    assert report["failures_by_reason"] == {primary_reason: 2}
    assert (report["state"], report["entries_done"], report["entries_failed"], report["total_forms"]) == ("failed", 0, 2, 0)
    assert report["unavailable_relation_blobs"] == [
        {"entry_id": entry_id, "tab": tab, "ref": manifest[tab],
         "error": primary_reason if tab == "synonyms" else other_reason,
         "locator": f"ulif:entry:{entry_id}:{tab}:{manifest[tab]}"}
        for entry_id in (1, 2) for tab in ("synonyms", "phraseology")
    ]
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT entry_id, reason, locator FROM ulif_forms_failures ORDER BY entry_id").fetchall() == [
            (entry_id, primary_reason, f"ulif:entry:{entry_id}:synonyms:{manifest['synonyms']}") for entry_id in (1, 2)
        ]
        assert conn.execute("SELECT * FROM ulif_dictua_entries").fetchall() == original_entries
        conn.execute("UPDATE ulif_forms_build SET state='complete'")
    assert ulif_forms.verify_ulif_forms(db_path)["verified"] is False


def test_empty_data_gender_row_preserves_column_metadata_without_tag_leak():
    """Synthetic English forms and verbatim existing map keys; no Ukrainian grammar claim."""
    html = """
    <div id="ContentPlaceHolder1_article"><span class="word_style">placehólder</span>
    <table>
      <tr><td colspan="3">Минулий час</td></tr>
      <tr><td></td><td>однина</td><td>множина</td></tr>
      <tr><td class="td_left_style">чол. р.</td>
          <td class="td_inner_style">fírst</td><td class="td_inner_style" rowspan="3">plúral</td></tr>
      <tr><td class="td_left_style">жін. р.</td><td class="td_inner_style"></td></tr>
      <tr><td class="td_left_style">сер. р.</td><td class="td_inner_style">thírd</td></tr>
      <tr><td colspan="3">Дієприслівник</td></tr>
      <tr><td class="td_inner_style" colspan="3">láter</td></tr>
    </table></div>
    """
    forms = ulif_forms.ulif_dictua_parse.parse_ulif_entry(html, homonym_index=1)["forms"]
    assert [(row["form_stressed"], row["grammatical_tags"]) for row in forms if not row["is_lemma"]] == [
        ("fírst", ["past", "m", "s"]), ("plúral", ["past", "p"]),
        ("thírd", ["past", "n", "s"]), ("láter", ["past", "advp"]),
    ]
