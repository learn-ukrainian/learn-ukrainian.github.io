"""Text-free university denominator/database reconciliation tests."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import yaml

from scripts.projects.open_model_data import phase3_university_reconciliation as reconciliation


def _denominator(path: Path) -> Path:
    value = {
        "schema_version": "university_corpus_denominator_v1",
        "sources": [
            {
                "source_id": "uni-expected-a",
                "domain": "ukrainian_language",
                "admission_state": "canary_passed",
                "database_identity": {
                    "source_file": "uni-expected-a",
                    "inserted_rows": 2,
                    "linked_rows": 2,
                },
            }
        ],
        "rejected_candidates": [{"source_id": "uni-rejected-b"}],
    }
    path.write_text(yaml.safe_dump(value, allow_unicode=True), encoding="utf-8")
    return path


def _database(
    path: Path,
    sources: list[tuple[str, list[str]]],
    *,
    rebuild_fts: bool = True,
) -> Path:
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        PRAGMA foreign_keys = ON;
        CREATE TABLE textbook_sections (
            section_id INTEGER PRIMARY KEY,
            source_file TEXT NOT NULL,
            grade INTEGER NOT NULL,
            section_title TEXT NOT NULL,
            section_number TEXT,
            page_start INTEGER,
            page_end INTEGER,
            chunk_count INTEGER NOT NULL,
            full_text TEXT NOT NULL
        );
        CREATE TABLE textbooks (
            id INTEGER PRIMARY KEY,
            chunk_id TEXT NOT NULL,
            title TEXT NOT NULL,
            text TEXT NOT NULL,
            source_file TEXT NOT NULL,
            grade TEXT,
            author TEXT,
            char_count INTEGER,
            parent_section_id INTEGER REFERENCES textbook_sections(section_id),
            author_uk TEXT,
            subject TEXT
        );
        CREATE VIRTUAL TABLE textbooks_fts USING fts5(title, text, content='textbooks', content_rowid='id');
        """
    )
    row_id = 1
    section_id = 1
    for source_file, chunks in sources:
        connection.execute(
            "INSERT INTO textbook_sections VALUES (?, ?, 0, ?, NULL, NULL, NULL, ?, ?)",
            (section_id, source_file, "section metadata", len(chunks), "section metadata only"),
        )
        for chunk in chunks:
            connection.execute(
                "INSERT INTO textbooks VALUES (?, ?, ?, ?, ?, 'university', NULL, ?, ?, NULL, 'ukrmova')",
                (row_id, f"chunk-{row_id}", "fixture title", chunk, source_file, len(chunk), section_id),
            )
            row_id += 1
        section_id += 1
    if rebuild_fts:
        connection.execute("INSERT INTO textbooks_fts(textbooks_fts) VALUES('rebuild')")
    connection.commit()
    connection.close()
    return path


def test_clean_identity_still_requires_authorized_content_audit(tmp_path: Path) -> None:
    denominator = _denominator(tmp_path / "denominator.yaml")
    database = _database(tmp_path / "sources.db", [("uni-expected-a", ["secret alpha", "secret beta"])])
    receipt = reconciliation.reconcile(
        denominator_path=denominator,
        database_path=database,
        as_of="fixture-clean",
    )
    assert receipt["status"] == "identity_reconciled_content_audit_pending"
    assert receipt["gates"] == {
        "database_identity_reconciled": True,
        "university_content_audit_complete": False,
        "proceed_to_source_freeze": False,
    }
    assert receipt["source_counts"] == {
        "expected_sources": 1,
        "expected_rows": 2,
        "exact_match_sources": 1,
        "missing_sources": 0,
        "mismatched_sources": 0,
        "extra_sources": 0,
        "extra_rows": 0,
    }
    serialized = json.dumps(receipt, ensure_ascii=False)
    assert "secret alpha" not in serialized
    assert "secret beta" not in serialized


def test_missing_expected_and_rejected_or_unlisted_extras_fail_closed(tmp_path: Path) -> None:
    denominator = _denominator(tmp_path / "denominator.yaml")
    database = _database(
        tmp_path / "sources.db",
        [("uni-rejected-b", ["not admitted"]), ("uni-unlisted-c", ["not listed", "also not listed"])],
    )
    receipt = reconciliation.reconcile(
        denominator_path=denominator,
        database_path=database,
        as_of="fixture-mismatch",
    )
    assert receipt["status"] == "mismatch_requires_reconciliation"
    assert receipt["gates"]["database_identity_reconciled"] is False
    assert receipt["source_counts"]["missing_sources"] == 1
    assert receipt["source_counts"]["extra_sources"] == 2
    assert receipt["source_counts"]["extra_rows"] == 3
    assert {item["source_file"]: item["denominator_status"] for item in receipt["extra_database_sources"]} == {
        "uni-rejected-b": "rejected_candidate",
        "uni-unlisted-c": "unlisted",
    }
    assert "denominator_sources_missing_from_database" in receipt["blockers"]
    assert "database_contains_unlisted_or_rejected_university_sources" in receipt["blockers"]


def test_count_or_fts_drift_is_not_an_exact_match(tmp_path: Path) -> None:
    denominator = _denominator(tmp_path / "denominator.yaml")
    database = _database(tmp_path / "sources.db", [("uni-expected-a", ["only one row"])])
    receipt = reconciliation.reconcile(
        denominator_path=denominator,
        database_path=database,
        as_of="fixture-count-drift",
    )
    assert receipt["expected_sources"][0]["status"] == "row_count_mismatch"
    assert receipt["source_counts"]["mismatched_sources"] == 1
    assert receipt["gates"]["proceed_to_source_freeze"] is False


def test_empty_external_content_fts_index_fails_closed(tmp_path: Path) -> None:
    denominator = _denominator(tmp_path / "denominator.yaml")
    database = _database(
        tmp_path / "sources.db",
        [("uni-expected-a", ["secret alpha", "secret beta"])],
        rebuild_fts=False,
    )
    receipt = reconciliation.reconcile(
        denominator_path=denominator,
        database_path=database,
        as_of="fixture-empty-fts-index",
    )
    assert receipt["database"]["textbook_rows"] == 2
    assert receipt["database"]["textbook_fts_rows"] == 0
    assert receipt["expected_sources"][0]["status"] == "fts_row_mismatch"
    assert receipt["gates"]["database_identity_reconciled"] is False
    assert "denominator_source_count_link_or_fts_mismatch" in receipt["blockers"]


def test_cli_returns_nonzero_after_writing_mismatch_receipt(tmp_path: Path) -> None:
    denominator = _denominator(tmp_path / "denominator.yaml")
    database = _database(tmp_path / "sources.db", [("uni-unlisted-c", ["not admitted"])])
    output = tmp_path / "receipt.json"
    assert (
        reconciliation.main(
            [
                "--denominator",
                str(denominator),
                "--db",
                str(database),
                "--as-of",
                "fixture-cli-mismatch",
                "--output",
                str(output),
            ]
        )
        == 2
    )
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == "mismatch_requires_reconciliation"


def test_cli_writes_schema_valid_text_free_receipt(tmp_path: Path) -> None:
    denominator = _denominator(tmp_path / "denominator.yaml")
    database = _database(tmp_path / "sources.db", [("uni-expected-a", ["one", "two"])])
    output = tmp_path / "receipt.json"
    assert (
        reconciliation.main(
            [
                "--denominator",
                str(denominator),
                "--db",
                str(database),
                "--as-of",
                "fixture-cli",
                "--output",
                str(output),
            ]
        )
        == 0
    )
    receipt = json.loads(output.read_text(encoding="utf-8"))
    assert receipt["text_free"] is True
    assert receipt["authority_boundary"]["may_admit_or_quarantine_sources"] is False
