"""Tests for transactional historical-source ingestion."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from ingest import incremental_historical_source_ingest as ingest
from wiki.historical_sources import ensure_historical_source_schema, sha256_file


def _record(record_id: str, text: str, *, disposition: str = "text_bearing") -> dict:
    return {
        "schema_version": "historical-source-record.v1",
        "collection_id": "saint-sophia-inscriptions",
        "source_record_id": record_id,
        "title": f"Inscription {record_id}",
        "source_url": f"https://saintsophia.dh.gu.se/inscription/{record_id}",
        "published": True,
        "original_transcription": text,
        "epidoc_text": f"<ab>{text}</ab>",
        "epidoc_interpretation": "",
        "interpretative_edition": text,
        "romanisation": "",
        "translation_ukr": "",
        "translation_eng": "",
        "commentary_ukr": "",
        "commentary_eng": "",
        "source_language_label": "Church Slavonic",
        "source_writing_system_label": "Cyrillic",
        "min_year": 1100,
        "max_year": 1200,
        "stage_label": None,
        "disposition": disposition,
        "quality_flags": [],
        "metadata": {"portal_id": int(record_id)},
        "raw_record_sha256": hashlib.sha256(f"raw-{record_id}".encode()).hexdigest(),
    }


def _write_source(tmp_path: Path, records: list[dict]) -> tuple[Path, Path]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    jsonl = tmp_path / "historical_source_records.jsonl"
    payload = "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for row in records
    )
    jsonl.write_text(payload, encoding="utf-8")
    id_payload = "".join(
        f"{value}\n"
        for value in sorted(
            (row["source_record_id"] for row in records),
            key=lambda value: int(value),
        )
    )
    coverage = tmp_path / "coverage-receipt.json"
    coverage.write_text(
        json.dumps(
            {
                "public_inscription_count": len(records),
                "id_set_sha256": hashlib.sha256(id_payload.encode()).hexdigest(),
                "output_hashes": {"historical_source_records.jsonl": sha256_file(jsonl)},
                "known_identified_total_lower_bound": 7000,
                "known_unexposed_residual": True,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return jsonl, coverage


def _database(tmp_path: Path) -> Path:
    path = tmp_path / "sources.db"
    conn = sqlite3.connect(path)
    ensure_historical_source_schema(conn)
    conn.commit()
    conn.close()
    return path


def test_ingest_replaces_collection_preserves_exact_layers_and_rebuilds_fts(tmp_path: Path):
    db = _database(tmp_path)
    old_jsonl, old_coverage = _write_source(tmp_path / "old", [_record("1", "старий")])
    ingest.ingest(
        db_path=db,
        jsonl_path=old_jsonl,
        coverage_receipt_path=old_coverage,
        output_receipt_path=tmp_path / "old-receipt.json",
    )

    exact = "слово <supplied reason=\"lost\">[ѣ]</supplied>"
    records = [_record("1", exact), _record("2", "другий")]
    jsonl, coverage = _write_source(tmp_path / "new", records)
    receipt_path = tmp_path / "ingest-receipt.json"
    receipt = ingest.ingest(
        db_path=db,
        jsonl_path=jsonl,
        coverage_receipt_path=coverage,
        output_receipt_path=receipt_path,
    )

    conn = sqlite3.connect(db)
    assert conn.execute(
        "SELECT original_transcription FROM historical_source_records "
        "WHERE collection_id=? AND source_record_id='1'",
        ("saint-sophia-inscriptions",),
    ).fetchone()[0] == exact
    assert conn.execute("SELECT COUNT(*) FROM historical_source_records").fetchone()[0] == 2
    assert conn.execute("SELECT COUNT(*) FROM historical_source_records_fts").fetchone()[0] == 2
    assert conn.execute(
        "SELECT COUNT(*) FROM historical_source_records_fts "
        "WHERE historical_source_records_fts MATCH 'другий'"
    ).fetchone()[0] == 1
    conn.close()
    assert receipt["before_transaction"]["collection_rows"] == 1
    assert receipt["after_transaction"]["collection_rows"] == 2
    assert receipt["coverage_known_unexposed_residual"] is True
    assert receipt_path.is_file()


def test_ingest_preserves_null_text_layers(tmp_path: Path):
    db = _database(tmp_path)
    record = _record("1", "")
    record["title"] = None
    record["epidoc_text"] = None
    record["translation_ukr"] = None
    record["source_language_label"] = None
    jsonl, coverage = _write_source(tmp_path / "source", [record])
    ingest.ingest(
        db_path=db,
        jsonl_path=jsonl,
        coverage_receipt_path=coverage,
        output_receipt_path=tmp_path / "receipt.json",
    )
    conn = sqlite3.connect(db)
    assert conn.execute(
        "SELECT title, epidoc_text, translation_ukr, source_language_label "
        "FROM historical_source_records"
    ).fetchone() == (None, None, None, None)
    conn.close()


def test_coverage_mismatch_fails_before_database_mutation(tmp_path: Path):
    db = _database(tmp_path)
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    jsonl, coverage = _write_source(source_dir, [_record("1", "текст")])
    value = json.loads(coverage.read_text(encoding="utf-8"))
    value["public_inscription_count"] = 2
    coverage.write_text(json.dumps(value), encoding="utf-8")

    with pytest.raises(ingest.HistoricalSourceError, match="count"):
        ingest.ingest(
            db_path=db,
            jsonl_path=jsonl,
            coverage_receipt_path=coverage,
            output_receipt_path=tmp_path / "receipt.json",
        )

    conn = sqlite3.connect(db)
    assert conn.execute("SELECT COUNT(*) FROM historical_source_records").fetchone()[0] == 0
    conn.close()


def test_failure_rolls_back_replacement_and_fts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db = _database(tmp_path)
    source_dir = tmp_path / "old"
    source_dir.mkdir()
    old_jsonl, old_coverage = _write_source(source_dir, [_record("1", "збережений")])
    ingest.ingest(
        db_path=db,
        jsonl_path=old_jsonl,
        coverage_receipt_path=old_coverage,
        output_receipt_path=tmp_path / "old-receipt.json",
    )
    new_dir = tmp_path / "new"
    new_dir.mkdir()
    jsonl, coverage = _write_source(new_dir, [_record("2", "не має лишитися")])

    def fail_validation(_conn: sqlite3.Connection) -> None:
        raise ingest.HistoricalSourceError("injected validation failure")

    monkeypatch.setattr(ingest, "validate_historical_fts", fail_validation)
    with pytest.raises(ingest.HistoricalSourceError, match="injected"):
        ingest.ingest(
            db_path=db,
            jsonl_path=jsonl,
            coverage_receipt_path=coverage,
            output_receipt_path=tmp_path / "failed-receipt.json",
        )

    conn = sqlite3.connect(db)
    assert conn.execute(
        "SELECT source_record_id FROM historical_source_records"
    ).fetchall() == [("1",)]
    assert conn.execute(
        "SELECT COUNT(*) FROM historical_source_records_fts "
        "WHERE historical_source_records_fts MATCH 'збережений'"
    ).fetchone()[0] == 1
    assert conn.execute(
        "SELECT COUNT(*) FROM historical_source_records_fts "
        "WHERE historical_source_records_fts MATCH 'лишитися'"
    ).fetchone()[0] == 0
    conn.close()


def test_dry_run_does_not_create_database(tmp_path: Path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    jsonl, coverage = _write_source(source_dir, [_record("1", "текст")])
    missing_db = tmp_path / "missing.db"
    receipt = ingest.ingest(
        db_path=missing_db,
        jsonl_path=jsonl,
        coverage_receipt_path=coverage,
        output_receipt_path=tmp_path / "unused.json",
        dry_run=True,
    )
    assert receipt["dry_run"] is True
    assert not missing_db.exists()


def test_numeric_id_hash_order_matches_crawler(tmp_path: Path):
    db = _database(tmp_path)
    jsonl, coverage = _write_source(
        tmp_path / "source",
        [_record("2", "два"), _record("10", "десять")],
    )
    receipt = ingest.ingest(
        db_path=db,
        jsonl_path=jsonl,
        coverage_receipt_path=coverage,
        output_receipt_path=tmp_path / "receipt.json",
    )
    assert receipt["input_rows"] == 2
