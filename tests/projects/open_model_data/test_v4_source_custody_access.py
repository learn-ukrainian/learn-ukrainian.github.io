"""Tests for V4 source custody access resolution and verification (#7884).

Validates ACCESS-1 through ACCESS-4 under epic #7423.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import v4_source_custody_access as custody

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = Path("data/projects/open_model_data/custody/v4_source_custody_access_config_v1.json")
CONFIG_SCHEMA = Path("data/projects/open_model_data/contracts/v4_source_custody_access_config_v1.schema.json")
ITEM_SCHEMA = Path("data/projects/open_model_data/contracts/v4_source_custody_access_item_v1.schema.json")
MISSING_SCHEMA = Path("data/projects/open_model_data/contracts/v4_source_custody_missing_report_v1.schema.json")
RECEIPT_SCHEMA = Path("data/projects/open_model_data/contracts/v4_source_custody_access_receipt_v1.schema.json")


@pytest.fixture
def repo_root() -> Path:
    return Path.cwd()


def test_contracts_are_valid_schemas() -> None:
    for schema_path in (CONFIG_SCHEMA, ITEM_SCHEMA, MISSING_SCHEMA, RECEIPT_SCHEMA):
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)


def test_config_passes_schema() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    schema = json.loads(CONFIG_SCHEMA.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors = list(validator.iter_errors(config))
    assert not errors, f"Config schema errors: {errors}"


def test_verify_passes_on_committed_artifacts(repo_root: Path) -> None:
    # Uses repo_root for input-root and output-root
    input_root = (
        Path("/home/ops/learn-ukrainian") if Path("/home/ops/learn-ukrainian/data/sources.db").is_file() else repo_root
    )
    assert custody.verify(CONFIG_PATH, input_root=input_root, output_root=repo_root) is True


def test_first_eligible_cohort_100_percent_accessible() -> None:
    receipt_path = Path("data/projects/open_model_data/custody/v4_source_custody_access_receipt_v1.json")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    first_cohort = receipt["summary"]["first_eligible_cohort"]

    assert first_cohort["cohort_id"] == "literary-non-ocr"
    assert first_cohort["total_sources"] == 229
    assert first_cohort["accessible_sources"] == 229
    assert first_cohort["confirmed_native"] == 229
    assert first_cohort["coverage_ratio"] == 1.0
    assert first_cohort["permitted_to_proceed"] is True
    assert receipt["safety_assertions"]["first_eligible_cohort_ready"] is True
    assert receipt["verdict"] == "PROCEED_WITH_ACCESSIBLE_SOURCES"


def test_missing_report_records_unmounted_archive_and_owner() -> None:
    missing_path = Path("data/projects/open_model_data/custody/v4_source_custody_missing_report_v1.json")
    report = json.loads(missing_path.read_text(encoding="utf-8"))

    assert report["schema_version"] == "v4_source_custody_missing_report_v1"
    assert report["owner"] == "existing custody/source-access owner"
    assert report["operator_decision_date"] == "2026-09-10"
    assert report["issue"] == 7884
    assert len(report["missing_inputs"]) > 0

    for item in report["missing_inputs"]:
        assert item["owner"] == "existing custody/source-access owner"
        assert item["cohort_id"] == "public-textbooks-non-stem-non-ocr"
        assert "execution_host_resolver_unmounted" in item["reason"]
        assert "direct PDF byte extraction" in item["blocks"]

    proceed = report["accessible_eligible_sources_permitted_to_proceed"]
    assert proceed["permitted"] is True
    assert "literary-non-ocr" in proceed["permitted_cohort_ids"]


def test_index_records_pass_schema_and_have_no_corpus_text() -> None:
    index_path = Path("data/projects/open_model_data/custody/v4_source_custody_access_index_v1.jsonl")
    schema = json.loads(ITEM_SCHEMA.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)

    with index_path.open(encoding="utf-8") as f:
        header = json.loads(f.readline())
        assert header["schema_version"] == "v4_source_custody_access_index_v1"
        assert header["records"] == 351

        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            errors = list(validator.iter_errors(row))
            assert not errors, f"Row error: {errors}"
            # Ensure no corpus text leaked
            assert "text" not in row
            assert "content" not in row
            assert "raw" not in row


def test_check_chunk_file_lineage_native(tmp_path: Path) -> None:
    chunk_file = tmp_path / "native_sample.jsonl"
    rows = [
        {
            "chunk_id": "c1",
            "extraction_mode": "native_text",
            "page_extraction_mode": "native_text",
            "text": "Привіт світ.",
        },
        {
            "chunk_id": "c2",
            "extraction_mode": "native_pdf_text",
            "page_extraction_mode": "native_pdf_text",
            "text": "Українська мова.",
        },
    ]
    chunk_file.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    mode, is_ocr, count, chars = custody.check_chunk_file_lineage(chunk_file)
    assert mode == "native_pdf_text"
    assert is_ocr is False
    assert count == 2
    assert chars > 0


def test_check_chunk_file_lineage_ocr_excluded(tmp_path: Path) -> None:
    chunk_file = tmp_path / "ocr_sample.jsonl"
    rows = [
        {"chunk_id": "c1", "extraction_mode": "native_text", "page_extraction_mode": "native_text", "text": "Привіт."},
        {
            "chunk_id": "c2",
            "extraction_mode": "apple_vision_ocr",
            "page_extraction_mode": "apple_vision_ocr",
            "text": "Скан.",
        },
    ]
    chunk_file.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    mode, is_ocr, count, _chars = custody.check_chunk_file_lineage(chunk_file)
    assert mode == "apple_vision_ocr"
    assert is_ocr is True
    assert count == 2


def test_check_chunk_file_lineage_unknown_fails_closed(tmp_path: Path) -> None:
    chunk_file = tmp_path / "unknown_sample.jsonl"
    rows = [
        {"chunk_id": "c1", "extraction_mode": "some_heuristic_extract", "text": "Привіт."},
    ]
    chunk_file.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    mode, is_ocr, _count, _chars = custody.check_chunk_file_lineage(chunk_file)
    assert mode == "unknown"
    assert is_ocr is False


def test_bounded_custody_reader_mock_sqlite(tmp_path: Path) -> None:
    db_path = tmp_path / "test_sources.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("CREATE TABLE literary_texts (id INTEGER PRIMARY KEY, chunk_id TEXT, source_file TEXT, text TEXT);")
    cur.executemany(
        "INSERT INTO literary_texts (chunk_id, source_file, text) VALUES (?, ?, ?);",
        [
            ("c1", "sample_source", "CONFIDENTIAL CORPUS TEXT 1"),
            ("c2", "sample_source", "CONFIDENTIAL CORPUS TEXT 2"),
            ("c3", "other_source", "OTHER TEXT"),
        ],
    )
    conn.commit()
    conn.close()

    reader = custody.BoundedCustodyReader(db_path)
    result = reader.read_source_stream("literary_texts", "sample_source", batch_size=2)

    assert result["source_file"] == "sample_source"
    assert result["table"] == "literary_texts"
    assert result["records_streamed"] == 2
    assert result["chars_streamed"] == len("CONFIDENTIAL CORPUS TEXT 1") + len("CONFIDENTIAL CORPUS TEXT 2")
    assert result["stream_sha256"] is not None
    # Verify stream hash does NOT disclose text directly
    assert "CONFIDENTIAL" not in str(result)


def test_verify_detects_hash_tampering(tmp_path: Path, repo_root: Path) -> None:
    # Copy receipt to tmp_path and tamper with config hash
    receipt_orig = Path("data/projects/open_model_data/custody/v4_source_custody_access_receipt_v1.json")
    receipt_data = json.loads(receipt_orig.read_text(encoding="utf-8"))
    receipt_data["config_sha256"] = "0" * 64

    tampered_out = tmp_path / "out"
    custody_dir = tampered_out / "data/projects/open_model_data/custody"
    custody_dir.mkdir(parents=True)

    # Copy index and missing report
    (custody_dir / "v4_source_custody_access_index_v1.jsonl").write_bytes(
        Path("data/projects/open_model_data/custody/v4_source_custody_access_index_v1.jsonl").read_bytes()
    )
    (custody_dir / "v4_source_custody_missing_report_v1.json").write_bytes(
        Path("data/projects/open_model_data/custody/v4_source_custody_missing_report_v1.json").read_bytes()
    )
    (custody_dir / "v4_source_custody_access_receipt_v1.json").write_text(json.dumps(receipt_data), encoding="utf-8")

    with pytest.raises(custody.CustodyAccessError, match="Receipt config_sha256 mismatch"):
        custody.verify(CONFIG_PATH, input_root=repo_root, output_root=tampered_out)
