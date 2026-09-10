"""Tests for V4 source custody access resolution and verification (#7884).

Validates ACCESS-1 through ACCESS-4 under epic #7423.
"""

from __future__ import annotations

import copy
import json
import re
import sqlite3
from pathlib import Path
from typing import Any

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
        assert any(term in item["reason"] for term in ("unmounted", "does_not_match", "not_found", "missing"))
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

    mode, is_ocr, count, chars, digest = custody.check_chunk_file_lineage(chunk_file)
    assert mode == "mixed_native"
    assert is_ocr is False
    assert count == 2
    assert chars > 0
    assert digest is not None


def test_check_chunk_file_lineage_pure_native_text(tmp_path: Path) -> None:
    chunk_file = tmp_path / "native_text_sample.jsonl"
    rows = [
        {"chunk_id": "c1", "extraction_mode": "native_text", "text": "Привіт."},
    ]
    chunk_file.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    mode, is_ocr, count, _chars, digest = custody.check_chunk_file_lineage(chunk_file)
    assert mode == "native_text"
    assert is_ocr is False
    assert count == 1
    assert digest is not None


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

    mode, is_ocr, count, _chars, _digest = custody.check_chunk_file_lineage(chunk_file)
    assert mode == "apple_vision_ocr"
    assert is_ocr is True
    assert count == 2


def test_check_chunk_file_lineage_unknown_fails_closed(tmp_path: Path) -> None:
    chunk_file = tmp_path / "unknown_sample.jsonl"
    rows = [
        {"chunk_id": "c1", "extraction_mode": "some_heuristic_extract", "text": "Привіт."},
    ]
    chunk_file.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    mode, is_ocr, _count, _chars, _digest = custody.check_chunk_file_lineage(chunk_file)
    assert mode == "unknown"
    assert is_ocr is False


def test_check_chunk_file_lineage_unlabelled_mixed_row_fails_closed(tmp_path: Path) -> None:
    """Finding 1: Unlabelled/absent extraction mode mixed with native row must fail closed as unknown."""
    chunk_file = tmp_path / "mixed_unlabelled.jsonl"
    rows = [
        {"chunk_id": "c1", "extraction_mode": "native_text", "page_extraction_mode": "native_text", "text": "Привіт."},
        {"chunk_id": "c2", "text": "Unlabelled row."},
    ]
    chunk_file.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    mode, is_ocr, count, _chars, _digest = custody.check_chunk_file_lineage(chunk_file)
    assert mode == "unknown"
    assert is_ocr is False
    assert count == 2


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


def test_stream_digest_sensitive_to_same_length_text_replacement(tmp_path: Path) -> None:
    """Finding 2A: Stream digest must change if text content is altered even with identical character count."""
    db1_path = tmp_path / "db1.db"
    conn1 = sqlite3.connect(db1_path)
    conn1.execute("CREATE TABLE literary_texts (id INTEGER PRIMARY KEY, chunk_id TEXT, source_file TEXT, text TEXT);")
    conn1.execute("INSERT INTO literary_texts (chunk_id, source_file, text) VALUES ('c1', 'src', 'TEXT_AAAAA');")
    conn1.commit()
    conn1.close()

    db2_path = tmp_path / "db2.db"
    conn2 = sqlite3.connect(db2_path)
    conn2.execute("CREATE TABLE literary_texts (id INTEGER PRIMARY KEY, chunk_id TEXT, source_file TEXT, text TEXT);")
    # Same length (10 chars), different content
    conn2.execute("INSERT INTO literary_texts (chunk_id, source_file, text) VALUES ('c1', 'src', 'TEXT_BBBBB');")
    conn2.commit()
    conn2.close()

    reader1 = custody.BoundedCustodyReader(db1_path)
    reader2 = custody.BoundedCustodyReader(db2_path)

    res1 = reader1.read_source_stream("literary_texts", "src")
    res2 = reader2.read_source_stream("literary_texts", "src")

    assert res1["chars_streamed"] == res2["chars_streamed"]
    assert res1["stream_sha256"] != res2["stream_sha256"]


def test_discrepant_database_chunks_fail_closed(tmp_path: Path) -> None:
    """Finding 2B: Database rows with different chunk IDs or text from native chunk file must fail closed."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE textbooks (id INTEGER PRIMARY KEY, chunk_id TEXT, source_file TEXT, text TEXT);")
    conn.execute("INSERT INTO textbooks (chunk_id, source_file, text) VALUES ('db_chunk_X', 'tb_test', 'DB text');")
    conn.commit()

    chunk_file = tmp_path / "tb_test.jsonl"
    chunk_rows = [
        {
            "chunk_id": "chk_chunk_Y",
            "extraction_mode": "native_pdf_text",
            "page_extraction_mode": "native_pdf_text",
            "text": "CHK text",
        },
    ]
    chunk_file.write_text("\n".join(json.dumps(r) for r in chunk_rows) + "\n", encoding="utf-8")

    chunks_map = {"tb_test": chunk_file}
    cohort_cfg = {
        "cohort_id": "public-textbooks-non-stem-non-ocr",
        "source_family": "public_textbooks",
        "resolver_kind": "hybrid_sqlite_chunks_archive",
        "lineage_rule": "native_pdf_text",
        "archive_locator": "gdrive:test/tb_test.pdf",
        "excluded_modes": ["apple_vision_ocr", "ocr"],
    }

    record, missing = custody.resolve_source_access(
        source_id="source.public_textbooks.1234567890abcdef12345678",
        source_file="tb_test",
        cohort_id="public-textbooks-non-stem-non-ocr",
        source_family="public_textbooks",
        cohort_cfg=cohort_cfg,
        input_root=tmp_path,
        db_conn=conn,
        chunks_map=chunks_map,
    )

    conn.close()

    assert record["permitted_to_proceed"] is False
    assert record["lineage_verification"]["status"] == "UNKNOWN_LINEAGE"
    assert record["blocking_reason"] == "database_content_does_not_match_lineage_chunk_evidence"
    assert missing is not None
    assert missing["reason"] == "database_content_does_not_match_lineage_chunk_evidence"


def test_verify_detects_contradictory_eligibility_and_forged_summary(tmp_path: Path, repo_root: Path) -> None:
    """Finding 3: Verify must reject contradictory index records and recompute/reject forged receipt summaries."""
    custody_orig = Path("data/projects/open_model_data/custody")
    out_dir = tmp_path / "out"
    tgt_custody = out_dir / "data/projects/open_model_data/custody"
    tgt_custody.mkdir(parents=True)

    index_lines = (custody_orig / "v4_source_custody_access_index_v1.jsonl").read_text(encoding="utf-8").splitlines()
    header = index_lines[0]
    records = [json.loads(line) for line in index_lines[1:]]

    # Tamper 1: Make a permitted record contradictory (EXCLUDED_OCR but permitted_to_proceed=True)
    records[0]["lineage_verification"]["status"] = "EXCLUDED_OCR"
    records[0]["lineage_verification"]["is_ocr_derived"] = True
    records[0]["permitted_to_proceed"] = True
    records[0]["blocking_reason"] = None

    tampered_index_lines = [header] + [json.dumps(r) for r in records]
    (tgt_custody / "v4_source_custody_access_index_v1.jsonl").write_text(
        "\n".join(tampered_index_lines) + "\n", encoding="utf-8"
    )
    (tgt_custody / "v4_source_custody_missing_report_v1.json").write_bytes(
        (custody_orig / "v4_source_custody_missing_report_v1.json").read_bytes()
    )

    # Re-hash index into receipt to isolate semantic/schema rejection from simple hash mismatch
    receipt_data = json.loads((custody_orig / "v4_source_custody_access_receipt_v1.json").read_text(encoding="utf-8"))
    receipt_data["index_sha256"] = custody.sha256_file(tgt_custody / "v4_source_custody_access_index_v1.jsonl")
    receipt_data["receipt_id"] = custody._make_receipt_id(
        receipt_data["config_sha256"], receipt_data["index_sha256"], receipt_data["missing_report_sha256"]
    )
    (tgt_custody / "v4_source_custody_access_receipt_v1.json").write_text(json.dumps(receipt_data), encoding="utf-8")

    # Must fail schema / semantic invariant validation
    with pytest.raises(custody.CustodyAccessError, match=r"(error|Contradictory|CONFIRMED_NATIVE)"):
        custody.verify(CONFIG_PATH, input_root=repo_root, output_root=out_dir)

    # Tamper 2: Restore valid index, but forge receipt summary count
    (tgt_custody / "v4_source_custody_access_index_v1.jsonl").write_bytes(
        (custody_orig / "v4_source_custody_access_index_v1.jsonl").read_bytes()
    )
    receipt_forged = json.loads((custody_orig / "v4_source_custody_access_receipt_v1.json").read_text(encoding="utf-8"))
    receipt_forged["summary"]["accessible_sources_count"] += 999
    (tgt_custody / "v4_source_custody_access_receipt_v1.json").write_text(json.dumps(receipt_forged), encoding="utf-8")

    with pytest.raises(custody.CustodyAccessError, match=r"Receipt summary accessible_sources_count mismatch"):
        custody.verify(CONFIG_PATH, input_root=repo_root, output_root=out_dir)


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


def test_verify_detects_forged_receipt_id_and_verdict(tmp_path: Path, repo_root: Path) -> None:
    tampered_out = tmp_path / "out"
    custody_dir = tampered_out / "data/projects/open_model_data/custody"
    custody_dir.mkdir(parents=True)

    (custody_dir / "v4_source_custody_access_index_v1.jsonl").write_bytes(
        Path("data/projects/open_model_data/custody/v4_source_custody_access_index_v1.jsonl").read_bytes()
    )
    (custody_dir / "v4_source_custody_missing_report_v1.json").write_bytes(
        Path("data/projects/open_model_data/custody/v4_source_custody_missing_report_v1.json").read_bytes()
    )

    receipt_orig = Path("data/projects/open_model_data/custody/v4_source_custody_access_receipt_v1.json")
    receipt_data = json.loads(receipt_orig.read_text(encoding="utf-8"))

    # Test 1: Forged receipt_id
    receipt_tampered = copy.deepcopy(receipt_data)
    receipt_tampered["receipt_id"] = "receipt.custody.111122223333444455556666"
    (custody_dir / "v4_source_custody_access_receipt_v1.json").write_text(
        json.dumps(receipt_tampered), encoding="utf-8"
    )
    with pytest.raises(custody.CustodyAccessError, match="Receipt receipt_id mismatch"):
        custody.verify(CONFIG_PATH, input_root=repo_root, output_root=tampered_out)

    # Test 2: Forged verdict
    receipt_tampered = copy.deepcopy(receipt_data)
    receipt_tampered["verdict"] = "HALT_INACCESSIBLE_SOURCES"
    (custody_dir / "v4_source_custody_access_receipt_v1.json").write_text(
        json.dumps(receipt_tampered), encoding="utf-8"
    )
    with pytest.raises(custody.CustodyAccessError, match="Receipt verdict mismatch"):
        custody.verify(CONFIG_PATH, input_root=repo_root, output_root=tampered_out)

    # Test 3: Contradictory safety assertion
    receipt_tampered = copy.deepcopy(receipt_data)
    receipt_tampered["safety_assertions"]["first_eligible_cohort_ready"] = False
    (custody_dir / "v4_source_custody_access_receipt_v1.json").write_text(
        json.dumps(receipt_tampered), encoding="utf-8"
    )
    with pytest.raises(
        custody.CustodyAccessError, match=r"Receipt safety_assertions\.first_eligible_cohort_ready mismatch"
    ):
        custody.verify(CONFIG_PATH, input_root=repo_root, output_root=tampered_out)


def test_verify_detects_forged_access_id(tmp_path: Path, repo_root: Path) -> None:
    tampered_out = tmp_path / "out"
    custody_dir = tampered_out / "data/projects/open_model_data/custody"
    custody_dir.mkdir(parents=True)

    index_lines = (
        Path("data/projects/open_model_data/custody/v4_source_custody_access_index_v1.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    header = index_lines[0]
    records = [json.loads(line) for line in index_lines[1:]]

    # Tamper with access_id to another schema-valid access id
    records[0]["access_id"] = "access.000000000000000000000000"
    tampered_lines = [header] + [json.dumps(r) for r in records]
    (custody_dir / "v4_source_custody_access_index_v1.jsonl").write_text(
        "\n".join(tampered_lines) + "\n", encoding="utf-8"
    )

    (custody_dir / "v4_source_custody_missing_report_v1.json").write_bytes(
        Path("data/projects/open_model_data/custody/v4_source_custody_missing_report_v1.json").read_bytes()
    )

    receipt_orig = Path("data/projects/open_model_data/custody/v4_source_custody_access_receipt_v1.json")
    receipt_data = json.loads(receipt_orig.read_text(encoding="utf-8"))
    receipt_tampered = copy.deepcopy(receipt_data)
    receipt_tampered["index_sha256"] = custody.sha256_file(custody_dir / "v4_source_custody_access_index_v1.jsonl")
    receipt_tampered["receipt_id"] = custody._make_receipt_id(
        receipt_tampered["config_sha256"],
        receipt_tampered["index_sha256"],
        receipt_tampered["missing_report_sha256"],
    )
    (custody_dir / "v4_source_custody_access_receipt_v1.json").write_text(
        json.dumps(receipt_tampered), encoding="utf-8"
    )

    with pytest.raises(custody.CustodyAccessError, match=r"access_id mismatch"):
        custody.verify(CONFIG_PATH, input_root=repo_root, output_root=tampered_out)


def test_verify_detects_duplicate_source_id(tmp_path: Path, repo_root: Path) -> None:
    tampered_out = tmp_path / "out"
    custody_dir = tampered_out / "data/projects/open_model_data/custody"
    custody_dir.mkdir(parents=True)

    index_lines = (
        Path("data/projects/open_model_data/custody/v4_source_custody_access_index_v1.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    header = index_lines[0]
    records = [json.loads(line) for line in index_lines[1:]]

    # Replace second record with a duplicate of the first record in the same cohort
    records[1] = copy.deepcopy(records[0])
    tampered_lines = [header] + [json.dumps(r) for r in records]
    (custody_dir / "v4_source_custody_access_index_v1.jsonl").write_text(
        "\n".join(tampered_lines) + "\n", encoding="utf-8"
    )

    (custody_dir / "v4_source_custody_missing_report_v1.json").write_bytes(
        Path("data/projects/open_model_data/custody/v4_source_custody_missing_report_v1.json").read_bytes()
    )

    receipt_orig = Path("data/projects/open_model_data/custody/v4_source_custody_access_receipt_v1.json")
    receipt_data = json.loads(receipt_orig.read_text(encoding="utf-8"))
    receipt_tampered = copy.deepcopy(receipt_data)
    receipt_tampered["index_sha256"] = custody.sha256_file(custody_dir / "v4_source_custody_access_index_v1.jsonl")
    receipt_tampered["receipt_id"] = custody._make_receipt_id(
        receipt_tampered["config_sha256"],
        receipt_tampered["index_sha256"],
        receipt_tampered["missing_report_sha256"],
    )
    (custody_dir / "v4_source_custody_access_receipt_v1.json").write_text(
        json.dumps(receipt_tampered), encoding="utf-8"
    )

    with pytest.raises(custody.CustodyAccessError, match=r"duplicate source_id"):
        custody.verify(CONFIG_PATH, input_root=repo_root, output_root=tampered_out)


def test_verify_detects_duplicate_source_locator(tmp_path: Path, repo_root: Path) -> None:
    tampered_out = tmp_path / "out"
    custody_dir = tampered_out / "data/projects/open_model_data/custody"
    custody_dir.mkdir(parents=True)

    index_lines = (
        Path("data/projects/open_model_data/custody/v4_source_custody_access_index_v1.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    header = index_lines[0]
    records = [json.loads(line) for line in index_lines[1:]]

    # Keep a different source_id but duplicate another source's source_file locator in the same cohort
    records[1]["source_locator"]["source_file"] = records[0]["source_locator"]["source_file"]
    tampered_lines = [header] + [json.dumps(r) for r in records]
    (custody_dir / "v4_source_custody_access_index_v1.jsonl").write_text(
        "\n".join(tampered_lines) + "\n", encoding="utf-8"
    )

    (custody_dir / "v4_source_custody_missing_report_v1.json").write_bytes(
        Path("data/projects/open_model_data/custody/v4_source_custody_missing_report_v1.json").read_bytes()
    )

    receipt_orig = Path("data/projects/open_model_data/custody/v4_source_custody_access_receipt_v1.json")
    receipt_data = json.loads(receipt_orig.read_text(encoding="utf-8"))
    receipt_tampered = copy.deepcopy(receipt_data)
    receipt_tampered["index_sha256"] = custody.sha256_file(custody_dir / "v4_source_custody_access_index_v1.jsonl")
    receipt_tampered["receipt_id"] = custody._make_receipt_id(
        receipt_tampered["config_sha256"],
        receipt_tampered["index_sha256"],
        receipt_tampered["missing_report_sha256"],
    )
    (custody_dir / "v4_source_custody_access_receipt_v1.json").write_text(
        json.dumps(receipt_tampered), encoding="utf-8"
    )

    with pytest.raises(custody.CustodyAccessError, match=r"duplicate source locator"):
        custody.verify(CONFIG_PATH, input_root=repo_root, output_root=tampered_out)


def test_verify_detects_provenance_projection_mismatch(tmp_path: Path, repo_root: Path) -> None:
    tampered_out = tmp_path / "out"
    custody_dir = tampered_out / "data/projects/open_model_data/custody"
    custody_dir.mkdir(parents=True)

    index_lines = (
        Path("data/projects/open_model_data/custody/v4_source_custody_access_index_v1.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    header = index_lines[0]
    records = [json.loads(line) for line in index_lines[1:]]

    # Change source_file for record 0 to create a projection mismatch with provenance denominator
    records[0]["source_locator"]["source_file"] = "tampered_source_file"
    tampered_lines = [header] + [json.dumps(r) for r in records]
    (custody_dir / "v4_source_custody_access_index_v1.jsonl").write_text(
        "\n".join(tampered_lines) + "\n", encoding="utf-8"
    )

    (custody_dir / "v4_source_custody_missing_report_v1.json").write_bytes(
        Path("data/projects/open_model_data/custody/v4_source_custody_missing_report_v1.json").read_bytes()
    )

    receipt_orig = Path("data/projects/open_model_data/custody/v4_source_custody_access_receipt_v1.json")
    receipt_data = json.loads(receipt_orig.read_text(encoding="utf-8"))
    receipt_tampered = copy.deepcopy(receipt_data)
    receipt_tampered["index_sha256"] = custody.sha256_file(custody_dir / "v4_source_custody_access_index_v1.jsonl")
    receipt_tampered["receipt_id"] = custody._make_receipt_id(
        receipt_tampered["config_sha256"],
        receipt_tampered["index_sha256"],
        receipt_tampered["missing_report_sha256"],
    )
    (custody_dir / "v4_source_custody_access_receipt_v1.json").write_text(
        json.dumps(receipt_tampered), encoding="utf-8"
    )

    with pytest.raises(custody.CustodyAccessError, match=r"projection does not match provenance denominator"):
        custody.verify(CONFIG_PATH, input_root=repo_root, output_root=tampered_out)


def test_verify_detects_missing_provenance_index(tmp_path: Path, repo_root: Path) -> None:
    tampered_out = tmp_path / "out"
    custody_dir = tampered_out / "data/projects/open_model_data/custody"
    custody_dir.mkdir(parents=True)

    config_data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    config_data["inputs"]["provenance_index"] = "data/projects/open_model_data/nonexistent_provenance_index.jsonl"
    tampered_config = tmp_path / "config.json"
    tampered_config.write_text(json.dumps(config_data), encoding="utf-8")
    expected_config_sha = custody.sha256_file(tampered_config)

    index_lines = (
        Path("data/projects/open_model_data/custody/v4_source_custody_access_index_v1.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    header = json.loads(index_lines[0])
    header["config_sha256"] = expected_config_sha
    tampered_lines = [json.dumps(header), *index_lines[1:]]
    (custody_dir / "v4_source_custody_access_index_v1.jsonl").write_text(
        "\n".join(tampered_lines) + "\n", encoding="utf-8"
    )

    (custody_dir / "v4_source_custody_missing_report_v1.json").write_bytes(
        Path("data/projects/open_model_data/custody/v4_source_custody_missing_report_v1.json").read_bytes()
    )

    receipt_orig = Path("data/projects/open_model_data/custody/v4_source_custody_access_receipt_v1.json")
    receipt_data = json.loads(receipt_orig.read_text(encoding="utf-8"))
    receipt_tampered = copy.deepcopy(receipt_data)
    receipt_tampered["config_sha256"] = expected_config_sha
    receipt_tampered["index_sha256"] = custody.sha256_file(custody_dir / "v4_source_custody_access_index_v1.jsonl")
    receipt_tampered["receipt_id"] = custody._make_receipt_id(
        expected_config_sha, receipt_tampered["index_sha256"], receipt_tampered["missing_report_sha256"]
    )
    (custody_dir / "v4_source_custody_access_receipt_v1.json").write_text(
        json.dumps(receipt_tampered), encoding="utf-8"
    )

    with pytest.raises(custody.CustodyAccessError, match=r"Provenance index missing"):
        custody.verify(tampered_config, input_root=repo_root, output_root=tampered_out)


def test_is_private_or_absolute_host_path() -> None:
    # Allowed clean paths and prose
    assert not custody._is_private_or_absolute_host_path("")
    assert not custody._is_private_or_absolute_host_path("sources/textbooks/math.pdf")
    assert not custody._is_private_or_absolute_host_path("data/clean/source.txt")
    assert not custody._is_private_or_absolute_host_path("file:data/textbook_chunks/grade-06/6-klas.jsonl")
    assert not custody._is_private_or_absolute_host_path("sqlite:sources.db#textbooks")
    assert not custody._is_private_or_absolute_host_path("gdrive:learn-ukrainian-data/textbooks/6-klas.pdf")
    assert not custody._is_private_or_absolute_host_path("A: follow up with the custodian")
    assert not custody._is_private_or_absolute_host_path("B: check item status")
    assert not custody._is_private_or_absolute_host_path("Note: this is clean text")
    assert not custody._is_private_or_absolute_host_path("private archive unavailable")
    assert not custody._is_private_or_absolute_host_path("root cause analysis")
    assert not custody._is_private_or_absolute_host_path("temp storage failure")
    assert not custody._is_private_or_absolute_host_path("clean users list")
    assert not custody._is_private_or_absolute_host_path("home page link")
    assert not custody._is_private_or_absolute_host_path("var environment unset")

    # Unix absolute paths and home expansion
    assert custody._is_private_or_absolute_host_path("/opt/data/book.pdf")
    assert custody._is_private_or_absolute_host_path("/home/ops/book.pdf")
    assert custody._is_private_or_absolute_host_path("~/data.txt")
    assert custody._is_private_or_absolute_host_path("~ops/data.txt")

    # Windows drive paths
    assert custody._is_private_or_absolute_host_path(r"C:\Users\alice\private\book.pdf")
    assert custody._is_private_or_absolute_host_path("c:/users/bob/doc.txt")
    assert custody._is_private_or_absolute_host_path(r"D:\repo\data.txt")

    # Windows UNC paths
    assert custody._is_private_or_absolute_host_path(r"\\server\share\data.pdf")
    assert custody._is_private_or_absolute_host_path("//server/share/data.pdf")

    # Private directory segments in path-shaped tokens
    assert custody._is_private_or_absolute_host_path("foo/home/bar.txt")
    assert custody._is_private_or_absolute_host_path("foo/appdata/bar.txt")
    assert custody._is_private_or_absolute_host_path("foo/tmp/bar.txt")
    assert custody._is_private_or_absolute_host_path(r"foo\private\bar.txt")
    assert custody._is_private_or_absolute_host_path("Users/alice/doc.pdf")
    assert custody._is_private_or_absolute_host_path("private/archive")
    assert custody._is_private_or_absolute_host_path(r"private\archive")
    assert custody._is_private_or_absolute_host_path("root/folder")
    assert custody._is_private_or_absolute_host_path("temp/dir")


@pytest.mark.parametrize(
    "bad_path",
    [
        "/home/ops/private/book.pdf",
        r"C:\Users\alice\private\book.pdf",
        r"\\server\share\private\book.pdf",
        "relative/path/appdata/secrets.txt",
    ],
)
def test_verify_detects_recomputed_safety_assertion_violations(tmp_path: Path, repo_root: Path, bad_path: str) -> None:
    tampered_out = tmp_path / "out"
    custody_dir = tampered_out / "data/projects/open_model_data/custody"
    custody_dir.mkdir(parents=True)

    index_lines = (
        Path("data/projects/open_model_data/custody/v4_source_custody_access_index_v1.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    header = index_lines[0]
    records = [json.loads(line) for line in index_lines[1:]]

    (custody_dir / "v4_source_custody_missing_report_v1.json").write_bytes(
        Path("data/projects/open_model_data/custody/v4_source_custody_missing_report_v1.json").read_bytes()
    )

    receipt_orig = Path("data/projects/open_model_data/custody/v4_source_custody_access_receipt_v1.json")
    receipt_data = json.loads(receipt_orig.read_text(encoding="utf-8"))

    # Test private/absolute host path insertion in custody_resolution archive_store
    records[0]["custody_resolution"]["archive_store"] = bad_path
    tampered_lines = [header] + [json.dumps(r) for r in records]
    (custody_dir / "v4_source_custody_access_index_v1.jsonl").write_text(
        "\n".join(tampered_lines) + "\n", encoding="utf-8"
    )

    receipt_tampered = copy.deepcopy(receipt_data)
    receipt_tampered["index_sha256"] = custody.sha256_file(custody_dir / "v4_source_custody_access_index_v1.jsonl")
    receipt_tampered["receipt_id"] = custody._make_receipt_id(
        receipt_tampered["config_sha256"],
        receipt_tampered["index_sha256"],
        receipt_tampered["missing_report_sha256"],
    )
    (custody_dir / "v4_source_custody_access_receipt_v1.json").write_text(
        json.dumps(receipt_tampered), encoding="utf-8"
    )

    with pytest.raises(
        custody.CustodyAccessError, match=r"Receipt safety_assertions\.no_private_host_paths_disclosed mismatch"
    ):
        custody.verify(CONFIG_PATH, input_root=repo_root, output_root=tampered_out)


@pytest.mark.parametrize(
    "bad_evidence_ref",
    [
        "/home/alice/source.jsonl",
        r"C:\Users\alice\source.jsonl",
        r"\\server\share\evidence.jsonl",
    ],
)
def test_verify_detects_evidence_ref_private_host_path(tmp_path: Path, repo_root: Path, bad_evidence_ref: str) -> None:
    tampered_out = tmp_path / "out"
    custody_dir = tampered_out / "data/projects/open_model_data/custody"
    custody_dir.mkdir(parents=True)

    index_lines = (
        Path("data/projects/open_model_data/custody/v4_source_custody_access_index_v1.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    header = index_lines[0]
    records = [json.loads(line) for line in index_lines[1:]]

    (custody_dir / "v4_source_custody_missing_report_v1.json").write_bytes(
        Path("data/projects/open_model_data/custody/v4_source_custody_missing_report_v1.json").read_bytes()
    )

    receipt_orig = Path("data/projects/open_model_data/custody/v4_source_custody_access_receipt_v1.json")
    receipt_data = json.loads(receipt_orig.read_text(encoding="utf-8"))

    # Test private/absolute host path insertion in lineage evidence_ref
    records[0]["lineage_verification"]["evidence_ref"] = bad_evidence_ref
    tampered_lines = [header] + [json.dumps(r) for r in records]
    (custody_dir / "v4_source_custody_access_index_v1.jsonl").write_text(
        "\n".join(tampered_lines) + "\n", encoding="utf-8"
    )

    receipt_tampered = copy.deepcopy(receipt_data)
    receipt_tampered["index_sha256"] = custody.sha256_file(custody_dir / "v4_source_custody_access_index_v1.jsonl")
    receipt_tampered["receipt_id"] = custody._make_receipt_id(
        receipt_tampered["config_sha256"],
        receipt_tampered["index_sha256"],
        receipt_tampered["missing_report_sha256"],
    )
    (custody_dir / "v4_source_custody_access_receipt_v1.json").write_text(
        json.dumps(receipt_tampered), encoding="utf-8"
    )

    with pytest.raises(
        custody.CustodyAccessError, match=r"Receipt safety_assertions\.no_private_host_paths_disclosed mismatch"
    ):
        custody.verify(CONFIG_PATH, input_root=repo_root, output_root=tampered_out)


@pytest.mark.parametrize(
    ("field_path", "bad_val"),
    [
        (("unmounted_archive_locator",), "/home/ops/secret_archive"),
        (("owner",), "alice at /home/alice"),
        (("scope",), r"processing C:\Users\alice\data"),
        (("accessible_eligible_sources_permitted_to_proceed", "description"), r"Proceed using \\server\share\data.pdf"),
        (("missing_inputs", 0, "reason"), "unmounted at /home/ops/gdrive"),
        (("missing_inputs", 0, "blocks"), r"blocked by C:\private\job"),
        (("missing_inputs", 0, "owner"), "/root/admin"),
    ],
)
def test_verify_detects_missing_report_freeform_private_host_paths(
    tmp_path: Path, repo_root: Path, field_path: tuple, bad_val: str
) -> None:
    tampered_out = tmp_path / "out"
    custody_dir = tampered_out / "data/projects/open_model_data/custody"
    custody_dir.mkdir(parents=True)

    (custody_dir / "v4_source_custody_access_index_v1.jsonl").write_bytes(
        Path("data/projects/open_model_data/custody/v4_source_custody_access_index_v1.jsonl").read_bytes()
    )

    missing_data = json.loads(
        Path("data/projects/open_model_data/custody/v4_source_custody_missing_report_v1.json").read_text(
            encoding="utf-8"
        )
    )
    target = missing_data
    for k in field_path[:-1]:
        target = target[k]
    target[field_path[-1]] = bad_val

    missing_path = custody_dir / "v4_source_custody_missing_report_v1.json"
    missing_path.write_text(json.dumps(missing_data), encoding="utf-8")

    receipt_orig = Path("data/projects/open_model_data/custody/v4_source_custody_access_receipt_v1.json")
    receipt_data = json.loads(receipt_orig.read_text(encoding="utf-8"))
    receipt_tampered = copy.deepcopy(receipt_data)
    receipt_tampered["missing_report_sha256"] = custody.sha256_file(missing_path)
    receipt_tampered["receipt_id"] = custody._make_receipt_id(
        receipt_tampered["config_sha256"],
        receipt_tampered["index_sha256"],
        receipt_tampered["missing_report_sha256"],
    )
    (custody_dir / "v4_source_custody_access_receipt_v1.json").write_text(
        json.dumps(receipt_tampered), encoding="utf-8"
    )

    with pytest.raises(
        custody.CustodyAccessError, match=r"Receipt safety_assertions\.no_private_host_paths_disclosed mismatch"
    ):
        custody.verify(CONFIG_PATH, input_root=repo_root, output_root=tampered_out)


def test_verify_allows_missing_report_valid_prose_with_reserved_words(tmp_path: Path, repo_root: Path) -> None:
    valid_out = tmp_path / "out"
    custody_dir = valid_out / "data/projects/open_model_data/custody"
    custody_dir.mkdir(parents=True)

    # Use valid prose containing reserved words ('root', 'temp', 'private') in scope
    prose = "root cause analysis: temp failure investigation for private archive reachability"
    cfg_data = json.loads(Path(CONFIG_PATH).read_text(encoding="utf-8"))
    cfg_data["ownership"]["blocks_scope"] = prose
    test_cfg_path = tmp_path / "test_config.json"
    test_cfg_path.write_text(json.dumps(cfg_data, indent=2), encoding="utf-8")

    idx_path = custody_dir / "v4_source_custody_access_index_v1.jsonl"
    lines = (
        Path("data/projects/open_model_data/custody/v4_source_custody_access_index_v1.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    header = json.loads(lines[0])
    header["config_sha256"] = custody.sha256_file(test_cfg_path)
    lines[0] = custody.canonical_json(header)
    idx_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    missing_data = json.loads(
        Path("data/projects/open_model_data/custody/v4_source_custody_missing_report_v1.json").read_text(
            encoding="utf-8"
        )
    )
    missing_data["scope"] = prose

    missing_path = custody_dir / "v4_source_custody_missing_report_v1.json"
    missing_path.write_text(json.dumps(missing_data, indent=2) + "\n", encoding="utf-8")

    receipt_orig = Path("data/projects/open_model_data/custody/v4_source_custody_access_receipt_v1.json")
    receipt_data = json.loads(receipt_orig.read_text(encoding="utf-8"))
    receipt_updated = copy.deepcopy(receipt_data)
    receipt_updated["config_sha256"] = custody.sha256_file(test_cfg_path)
    receipt_updated["index_sha256"] = custody.sha256_file(idx_path)
    receipt_updated["missing_report_sha256"] = custody.sha256_file(missing_path)
    receipt_updated["receipt_id"] = custody._make_receipt_id(
        receipt_updated["config_sha256"],
        receipt_updated["index_sha256"],
        receipt_updated["missing_report_sha256"],
    )
    (custody_dir / "v4_source_custody_access_receipt_v1.json").write_text(
        json.dumps(receipt_updated, indent=2) + "\n", encoding="utf-8"
    )

    assert custody.verify(test_cfg_path, input_root=repo_root, output_root=valid_out) is True


def test_check_chunk_file_lineage_preserves_excluded_mode(tmp_path: Path) -> None:
    chunk_file = tmp_path / "scanned_sample.jsonl"
    rows = [
        {"chunk_id": "c1", "extraction_mode": "scanned_image", "text": "Скан."},
    ]
    chunk_file.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    mode, is_ocr, count, _chars, _digest = custody.check_chunk_file_lineage(chunk_file)
    assert mode == "scanned_image"
    assert is_ocr is True
    assert count == 1


def test_input_root_takes_precedence_over_cwd(tmp_path: Path) -> None:
    custom_input = tmp_path / "input"
    prov_dir = custom_input / "data/projects/open_model_data/provenance"
    prov_dir.mkdir(parents=True)
    custom_prov = prov_dir / "v4_source_provenance_index_v1.jsonl"
    custom_prov.write_text("CUSTOM_PROV_HEADER\n", encoding="utf-8")

    rel_path = Path("data/projects/open_model_data/provenance/v4_source_provenance_index_v1.jsonl")
    resolved = custody._resolve_file(rel_path, [custom_input, Path.cwd()])
    assert resolved == custom_prov


def test_verify_detects_cohort_id_mismatch_in_summary(tmp_path: Path, repo_root: Path) -> None:
    tampered_out = tmp_path / "out"
    custody_dir = tampered_out / "data/projects/open_model_data/custody"
    custody_dir.mkdir(parents=True)

    (custody_dir / "v4_source_custody_access_index_v1.jsonl").write_bytes(
        Path("data/projects/open_model_data/custody/v4_source_custody_access_index_v1.jsonl").read_bytes()
    )
    (custody_dir / "v4_source_custody_missing_report_v1.json").write_bytes(
        Path("data/projects/open_model_data/custody/v4_source_custody_missing_report_v1.json").read_bytes()
    )

    receipt_orig = Path("data/projects/open_model_data/custody/v4_source_custody_access_receipt_v1.json")
    receipt_data = json.loads(receipt_orig.read_text(encoding="utf-8"))

    # Tamper first_eligible_cohort cohort_id
    receipt_tampered = copy.deepcopy(receipt_data)
    receipt_tampered["summary"]["first_eligible_cohort"]["cohort_id"] = "wrong-cohort"
    (custody_dir / "v4_source_custody_access_receipt_v1.json").write_text(
        json.dumps(receipt_tampered), encoding="utf-8"
    )
    with pytest.raises(custody.CustodyAccessError, match=r"Receipt first_eligible_cohort discrepancy"):
        custody.verify(CONFIG_PATH, input_root=repo_root, output_root=tampered_out)

    # Tamper textbook_cohort cohort_id
    receipt_tampered2 = copy.deepcopy(receipt_data)
    receipt_tampered2["summary"]["textbook_cohort"]["cohort_id"] = "wrong-cohort"
    (custody_dir / "v4_source_custody_access_receipt_v1.json").write_text(
        json.dumps(receipt_tampered2), encoding="utf-8"
    )
    with pytest.raises(custody.CustodyAccessError, match=r"Receipt textbook_cohort discrepancy"):
        custody.verify(CONFIG_PATH, input_root=repo_root, output_root=tampered_out)


def test_read_command_fails_when_source_yields_zero_records(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE literary_texts (id INTEGER PRIMARY KEY, source_file TEXT, chunk_id TEXT, text TEXT);")
    conn.commit()
    conn.close()

    exit_code = custody.main(
        ["read", "--database", str(db_path), "--table", "literary_texts", "--source-file", "nonexistent"]
    )
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Access proof failed" in captured.err
    assert '"records_streamed":0' in captured.out


def test_resolve_source_access_requires_exact_cohort_and_source_family(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE literary_texts (id INTEGER PRIMARY KEY, source_file TEXT, chunk_id TEXT, text TEXT);")
    conn.commit()

    # Empty cohort_cfg
    with pytest.raises(custody.CustodyAccessError, match=r"requires an exact configured cohort entry"):
        custody.resolve_source_access(
            source_id="s1",
            source_file="f1",
            cohort_id="literary-non-ocr",
            source_family="literary",
            cohort_cfg={},
            input_root=tmp_path,
            db_conn=conn,
            chunks_map={},
        )

    # Cohort ID mismatch
    with pytest.raises(custody.CustodyAccessError, match=r"requires an exact configured cohort entry"):
        custody.resolve_source_access(
            source_id="s1",
            source_file="f1",
            cohort_id="literary-non-ocr",
            source_family="literary",
            cohort_cfg={"cohort_id": "other-cohort", "source_family": "literary"},
            input_root=tmp_path,
            db_conn=conn,
            chunks_map={},
        )

    # Source family mismatch
    with pytest.raises(
        custody.CustodyAccessError,
        match=r"source_family 'literary' does not match configured cohort source_family 'public_textbooks'",
    ):
        custody.resolve_source_access(
            source_id="s1",
            source_file="f1",
            cohort_id="literary-non-ocr",
            source_family="literary",
            cohort_cfg={"cohort_id": "literary-non-ocr", "source_family": "public_textbooks"},
            input_root=tmp_path,
            db_conn=conn,
            chunks_map={},
        )

    conn.close()


def test_build_and_verify_detect_unconfigured_and_mismatched_cohort(tmp_path: Path, repo_root: Path) -> None:
    custom_input = tmp_path / "input"
    custom_out = tmp_path / "out"
    custom_input.mkdir(parents=True)
    custom_out.mkdir(parents=True)

    config_path = custom_input / "config.json"
    config_data = json.loads(Path(CONFIG_PATH).read_text(encoding="utf-8"))
    config_data["cohorts"] = [c for c in config_data["cohorts"] if c["cohort_id"] == "literary-non-ocr"]
    config_path.write_text(json.dumps(config_data, indent=2), encoding="utf-8")

    prov_dir = custom_input / "data/projects/open_model_data/provenance"
    prov_dir.mkdir(parents=True)
    prov_file = prov_dir / "v4_provenance_restoration_index_v1.jsonl"
    prov_rows = [
        json.dumps({"schema_version": "v4_provenance_restoration_index_v1", "records": 1}),
        json.dumps(
            {
                "source_id": "source.public_textbooks.123",
                "cohort_id": "public-textbooks-non-stem-non-ocr",
                "source_family": "public_textbooks",
                "source_locator": {"source_file": "tb1"},
            }
        ),
    ]
    prov_file.write_text("\n".join(prov_rows) + "\n", encoding="utf-8")

    db_file = custom_input / "data/sources.db"
    db_file.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_file)
    conn.execute("CREATE TABLE literary_texts (id INTEGER PRIMARY KEY, source_file TEXT, chunk_id TEXT, text TEXT);")
    conn.commit()
    conn.close()

    with pytest.raises(
        custody.CustodyAccessError, match=r"references unconfigured cohort_id 'public-textbooks-non-stem-non-ocr'"
    ):
        custody.build(config_path, input_root=custom_input, output_root=custom_out)

    # Mismatched source_family between provenance row and config cohort
    config_data2 = json.loads(Path(CONFIG_PATH).read_text(encoding="utf-8"))
    for c in config_data2["cohorts"]:
        if c["cohort_id"] == "public-textbooks-non-stem-non-ocr":
            c["source_family"] = "literary"
            c["resolver_kind"] = "sqlite_database"
            c["lineage_rule"] = "native_digital_source"
            c["primary_store"] = "sqlite:sources.db#literary_texts"
    config_path2 = custom_input / "config2.json"
    config_path2.write_text(json.dumps(config_data2, indent=2), encoding="utf-8")

    with pytest.raises(custody.CustodyAccessError, match=r"does not match configured cohort source_family"):
        custody.build(config_path2, input_root=custom_input, output_root=custom_out)


def test_validate_cohort_spec_enforces_compatible_resolver_and_lineage_rule() -> None:
    # Literary incompatible resolver_kind
    with pytest.raises(custody.CustodyAccessError, match=r"requires resolver_kind 'sqlite_database'"):
        custody.validate_cohort_spec(
            {
                "cohort_id": "lit",
                "source_family": "literary",
                "resolver_kind": "hybrid_sqlite_chunks_archive",
                "lineage_rule": "native_digital_source",
            }
        )

    # Literary incompatible lineage_rule
    with pytest.raises(custody.CustodyAccessError, match=r"requires lineage_rule 'native_digital_source'"):
        custody.validate_cohort_spec(
            {
                "cohort_id": "lit",
                "source_family": "literary",
                "resolver_kind": "sqlite_database",
                "lineage_rule": "native_pdf_text",
            }
        )

    # Public textbooks incompatible resolver_kind
    with pytest.raises(custody.CustodyAccessError, match=r"requires resolver_kind 'hybrid_sqlite_chunks_archive'"):
        custody.validate_cohort_spec(
            {
                "cohort_id": "tb",
                "source_family": "public_textbooks",
                "resolver_kind": "sqlite_database",
                "lineage_rule": "native_pdf_text",
            }
        )

    # Public textbooks incompatible lineage_rule
    with pytest.raises(custody.CustodyAccessError, match=r"requires lineage_rule 'native_pdf_text'"):
        custody.validate_cohort_spec(
            {
                "cohort_id": "tb",
                "source_family": "public_textbooks",
                "resolver_kind": "hybrid_sqlite_chunks_archive",
                "lineage_rule": "native_digital_source",
            }
        )

    # Unknown source_family
    with pytest.raises(custody.CustodyAccessError, match=r"unsupported source_family 'unknown'"):
        custody.validate_cohort_spec(
            {
                "cohort_id": "unknown",
                "source_family": "unknown",
                "resolver_kind": "sqlite_database",
                "lineage_rule": "native_digital_source",
            }
        )


def test_verify_detects_incompatible_cohort_lineage_rule_in_config(tmp_path: Path, repo_root: Path) -> None:
    tampered_out = tmp_path / "out"
    custody_dir = tampered_out / "data/projects/open_model_data/custody"
    custody_dir.mkdir(parents=True)

    # Tamper config so literary specifies native_pdf_text
    config_data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    for c in config_data["cohorts"]:
        if c["cohort_id"] == "literary-non-ocr":
            c["lineage_rule"] = "native_pdf_text"
    tampered_config = tmp_path / "config.json"
    tampered_config.write_text(json.dumps(config_data), encoding="utf-8")

    with pytest.raises(custody.CustodyAccessError, match=r"requires lineage_rule 'native_digital_source'"):
        custody.verify(tampered_config, input_root=repo_root, output_root=tampered_out)


def test_verify_rejects_unknown_mode_labeled_as_confirmed_native(tmp_path: Path, repo_root: Path) -> None:
    """Codex finding r3980769771: Blocked record with status=CONFIRMED_NATIVE and lineage_mode=unknown must fail."""
    custody_orig = Path("data/projects/open_model_data/custody")
    tampered_out = tmp_path / "out"
    tgt_custody = tampered_out / "data/projects/open_model_data/custody"
    tgt_custody.mkdir(parents=True)

    index_lines = (custody_orig / "v4_source_custody_access_index_v1.jsonl").read_text(encoding="utf-8").splitlines()
    header = index_lines[0]
    records = [json.loads(line) for line in index_lines[1:]]

    # Pick a blocked textbook record
    target_idx = None
    for i, r in enumerate(records):
        if not r["permitted_to_proceed"] and r["lineage_verification"]["status"] == "UNKNOWN_LINEAGE":
            target_idx = i
            break
    assert target_idx is not None

    # Set status to CONFIRMED_NATIVE while leaving lineage_mode as unknown (and permitted_to_proceed=False)
    records[target_idx]["lineage_verification"]["status"] = "CONFIRMED_NATIVE"
    records[target_idx]["lineage_verification"]["lineage_mode"] = "unknown"

    tampered_index_lines = [header] + [json.dumps(r) for r in records]
    (tgt_custody / "v4_source_custody_access_index_v1.jsonl").write_text(
        "\n".join(tampered_index_lines) + "\n", encoding="utf-8"
    )
    (tgt_custody / "v4_source_custody_missing_report_v1.json").write_bytes(
        (custody_orig / "v4_source_custody_missing_report_v1.json").read_bytes()
    )

    # Re-hash index and update receipt summary counts to test semantic rejection
    receipt_data = json.loads((custody_orig / "v4_source_custody_access_receipt_v1.json").read_text(encoding="utf-8"))
    receipt_data["index_sha256"] = custody.sha256_file(tgt_custody / "v4_source_custody_access_index_v1.jsonl")
    receipt_data["receipt_id"] = custody._make_receipt_id(
        receipt_data["config_sha256"], receipt_data["index_sha256"], receipt_data["missing_report_sha256"]
    )
    receipt_data["summary"]["confirmed_native_count"] += 1
    receipt_data["summary"]["textbook_cohort"]["confirmed_native"] += 1
    (tgt_custody / "v4_source_custody_access_receipt_v1.json").write_text(json.dumps(receipt_data), encoding="utf-8")

    with pytest.raises(
        custody.CustodyAccessError,
        match=r"lineage status is CONFIRMED_NATIVE but lineage_mode is 'unknown'",
    ):
        custody.verify(CONFIG_PATH, input_root=repo_root, output_root=tampered_out)


def test_verify_rejects_contradictory_lineage_status_and_mode_combinations(tmp_path: Path, repo_root: Path) -> None:
    """Validate that any mismatch between lineage status and mode is rejected by verify."""
    custody_orig = Path("data/projects/open_model_data/custody")
    tampered_out = tmp_path / "out"
    tgt_custody = tampered_out / "data/projects/open_model_data/custody"
    tgt_custody.mkdir(parents=True)

    index_lines = (custody_orig / "v4_source_custody_access_index_v1.jsonl").read_text(encoding="utf-8").splitlines()
    header = index_lines[0]
    records = [json.loads(line) for line in index_lines[1:]]

    # Test 1: UNKNOWN_LINEAGE status with native_digital_source mode
    records_copy = copy.deepcopy(records)
    for r in records_copy:
        if not r["permitted_to_proceed"]:
            r["lineage_verification"]["lineage_mode"] = "native_digital_source"
            break
    tampered_index_lines = [header] + [json.dumps(r) for r in records_copy]
    (tgt_custody / "v4_source_custody_access_index_v1.jsonl").write_text(
        "\n".join(tampered_index_lines) + "\n", encoding="utf-8"
    )
    (tgt_custody / "v4_source_custody_missing_report_v1.json").write_bytes(
        (custody_orig / "v4_source_custody_missing_report_v1.json").read_bytes()
    )
    receipt_data = json.loads((custody_orig / "v4_source_custody_access_receipt_v1.json").read_text(encoding="utf-8"))
    receipt_data["index_sha256"] = custody.sha256_file(tgt_custody / "v4_source_custody_access_index_v1.jsonl")
    receipt_data["receipt_id"] = custody._make_receipt_id(
        receipt_data["config_sha256"], receipt_data["index_sha256"], receipt_data["missing_report_sha256"]
    )
    (tgt_custody / "v4_source_custody_access_receipt_v1.json").write_text(json.dumps(receipt_data), encoding="utf-8")

    with pytest.raises(
        custody.CustodyAccessError,
        match=r"lineage status is UNKNOWN_LINEAGE but lineage_mode is 'native_digital_source'",
    ):
        custody.verify(CONFIG_PATH, input_root=repo_root, output_root=tampered_out)

    # Test 2: EXCLUDED_OCR status with native_digital_source mode (and is_ocr_derived=True so schema passes)
    records_copy = copy.deepcopy(records)
    for r in records_copy:
        if not r["permitted_to_proceed"]:
            r["lineage_verification"]["status"] = "EXCLUDED_OCR"
            r["lineage_verification"]["lineage_mode"] = "native_digital_source"
            r["lineage_verification"]["is_ocr_derived"] = True
            break
    tampered_index_lines = [header] + [json.dumps(r) for r in records_copy]
    (tgt_custody / "v4_source_custody_access_index_v1.jsonl").write_text(
        "\n".join(tampered_index_lines) + "\n", encoding="utf-8"
    )
    receipt_data["index_sha256"] = custody.sha256_file(tgt_custody / "v4_source_custody_access_index_v1.jsonl")
    receipt_data["receipt_id"] = custody._make_receipt_id(
        receipt_data["config_sha256"], receipt_data["index_sha256"], receipt_data["missing_report_sha256"]
    )
    (tgt_custody / "v4_source_custody_access_receipt_v1.json").write_text(json.dumps(receipt_data), encoding="utf-8")

    with pytest.raises(
        custody.CustodyAccessError,
        match=r"lineage status is EXCLUDED_OCR but lineage_mode is 'native_digital_source'",
    ):
        custody.verify(CONFIG_PATH, input_root=repo_root, output_root=tampered_out)


def test_bounded_custody_reader_rejects_non_positive_batch_size(tmp_path: Path) -> None:
    """BoundedCustodyReader.read_source_stream must reject batch_size <= 0 (ACCESS-3)."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE tbl (source_file TEXT, text TEXT)")
    conn.execute("INSERT INTO tbl VALUES ('f1', 'hello')")
    conn.commit()
    conn.close()

    reader = custody.BoundedCustodyReader(db_path)
    with pytest.raises(custody.CustodyAccessError, match=r"batch_size must be strictly positive \(> 0\), got 0"):
        reader.read_source_stream("tbl", "f1", batch_size=0)

    with pytest.raises(custody.CustodyAccessError, match=r"batch_size must be strictly positive \(> 0\), got -10"):
        reader.read_source_stream("tbl", "f1", batch_size=-10)


def test_textbook_cohort_summary_missing_on_host_reflects_archive_reachability(tmp_path: Path, repo_root: Path) -> None:
    """Receipt summary must count all textbooks with unmounted host archives as missing_on_host (122)."""
    receipt_orig = Path("data/projects/open_model_data/custody/v4_source_custody_access_receipt_v1.json")
    receipt_data = json.loads(receipt_orig.read_text(encoding="utf-8"))
    assert receipt_data["summary"]["textbook_cohort"]["missing_on_host"] == 122

    tampered_out = tmp_path / "out"
    tgt_custody = tampered_out / "data/projects/open_model_data/custody"
    tgt_custody.mkdir(parents=True)

    (tgt_custody / "v4_source_custody_access_index_v1.jsonl").write_bytes(
        Path("data/projects/open_model_data/custody/v4_source_custody_access_index_v1.jsonl").read_bytes()
    )
    (tgt_custody / "v4_source_custody_missing_report_v1.json").write_bytes(
        Path("data/projects/open_model_data/custody/v4_source_custody_missing_report_v1.json").read_bytes()
    )

    # Tamper missing_on_host back to 60 (only counting not-permitted) and verify rejection
    receipt_tampered = copy.deepcopy(receipt_data)
    receipt_tampered["summary"]["textbook_cohort"]["missing_on_host"] = 60
    (tgt_custody / "v4_source_custody_access_receipt_v1.json").write_text(
        json.dumps(receipt_tampered), encoding="utf-8"
    )

    with pytest.raises(custody.CustodyAccessError, match=r"Receipt textbook_cohort discrepancy"):
        custody.verify(CONFIG_PATH, input_root=repo_root, output_root=tampered_out)


@pytest.mark.parametrize(
    ("meta_key", "tampered_val", "expected_err"),
    [
        ("owner", "unauthorized-party", r"Missing report owner mismatch"),
        ("scope", "all datasets globally", r"Missing report scope mismatch"),
        ("operator_decision_date", "1999-01-01", r"Missing report operator_decision_date mismatch"),
        ("issue", 12345, r"Missing report issue mismatch"),
        ("unmounted_archive_locator", "s3://tampered-bucket", r"Missing report unmounted_archive_locator mismatch"),
    ],
)
def test_verify_detects_tampered_missing_report_metadata(
    tmp_path: Path, repo_root: Path, meta_key: str, tampered_val: Any, expected_err: str
) -> None:
    """Missing report metadata must strictly match custody config (ACCESS-4)."""
    tampered_out = tmp_path / "out"
    tgt_custody = tampered_out / "data/projects/open_model_data/custody"
    tgt_custody.mkdir(parents=True)

    (tgt_custody / "v4_source_custody_access_index_v1.jsonl").write_bytes(
        Path("data/projects/open_model_data/custody/v4_source_custody_access_index_v1.jsonl").read_bytes()
    )

    missing_path = tgt_custody / "v4_source_custody_missing_report_v1.json"
    missing_data = json.loads(
        Path("data/projects/open_model_data/custody/v4_source_custody_missing_report_v1.json").read_text(
            encoding="utf-8"
        )
    )
    missing_data[meta_key] = tampered_val
    missing_path.write_text(json.dumps(missing_data), encoding="utf-8")

    receipt_orig = Path("data/projects/open_model_data/custody/v4_source_custody_access_receipt_v1.json")
    receipt_data = json.loads(receipt_orig.read_text(encoding="utf-8"))
    receipt_tampered = copy.deepcopy(receipt_data)
    receipt_tampered["missing_report_sha256"] = custody.sha256_file(missing_path)
    receipt_tampered["receipt_id"] = custody._make_receipt_id(
        receipt_tampered["config_sha256"],
        receipt_tampered["index_sha256"],
        receipt_tampered["missing_report_sha256"],
    )
    (tgt_custody / "v4_source_custody_access_receipt_v1.json").write_text(
        json.dumps(receipt_tampered), encoding="utf-8"
    )

    with pytest.raises(custody.CustodyAccessError, match=expected_err):
        custody.verify(CONFIG_PATH, input_root=repo_root, output_root=tampered_out)


def test_verify_detects_tampered_missing_report_items(tmp_path: Path, repo_root: Path) -> None:
    """Missing report items must strictly match derived missing items from the access index (ACCESS-4)."""
    tampered_out = tmp_path / "out"
    tgt_custody = tampered_out / "data/projects/open_model_data/custody"
    tgt_custody.mkdir(parents=True)

    (tgt_custody / "v4_source_custody_access_index_v1.jsonl").write_bytes(
        Path("data/projects/open_model_data/custody/v4_source_custody_access_index_v1.jsonl").read_bytes()
    )

    orig_missing = json.loads(
        Path("data/projects/open_model_data/custody/v4_source_custody_missing_report_v1.json").read_text(
            encoding="utf-8"
        )
    )
    receipt_orig = Path("data/projects/open_model_data/custody/v4_source_custody_access_receipt_v1.json")
    receipt_data = json.loads(receipt_orig.read_text(encoding="utf-8"))

    # Case 1: Dropping an item (count mismatch)
    missing_tampered = copy.deepcopy(orig_missing)
    missing_tampered["missing_inputs"].pop()
    missing_path = tgt_custody / "v4_source_custody_missing_report_v1.json"
    missing_path.write_text(json.dumps(missing_tampered), encoding="utf-8")

    receipt_tampered = copy.deepcopy(receipt_data)
    receipt_tampered["missing_report_sha256"] = custody.sha256_file(missing_path)
    receipt_tampered["receipt_id"] = custody._make_receipt_id(
        receipt_tampered["config_sha256"],
        receipt_tampered["index_sha256"],
        receipt_tampered["missing_report_sha256"],
    )
    (tgt_custody / "v4_source_custody_access_receipt_v1.json").write_text(
        json.dumps(receipt_tampered), encoding="utf-8"
    )

    with pytest.raises(custody.CustodyAccessError, match=r"Missing report item count mismatch"):
        custody.verify(CONFIG_PATH, input_root=repo_root, output_root=tampered_out)

    # Case 2: Unexpected source_id
    missing_tampered = copy.deepcopy(orig_missing)
    missing_tampered["missing_inputs"][0]["source_id"] = "source.public_textbooks.unexpected_fictitious_id"
    missing_path.write_text(json.dumps(missing_tampered), encoding="utf-8")
    receipt_tampered["missing_report_sha256"] = custody.sha256_file(missing_path)
    receipt_tampered["receipt_id"] = custody._make_receipt_id(
        receipt_tampered["config_sha256"],
        receipt_tampered["index_sha256"],
        receipt_tampered["missing_report_sha256"],
    )
    (tgt_custody / "v4_source_custody_access_receipt_v1.json").write_text(
        json.dumps(receipt_tampered), encoding="utf-8"
    )

    with pytest.raises(
        custody.CustodyAccessError, match=r"unexpected source_id 'source\.public_textbooks\.unexpected_fictitious_id'"
    ):
        custody.verify(CONFIG_PATH, input_root=repo_root, output_root=tampered_out)

    # Case 3: Altered field in an item (e.g. reason)
    missing_tampered = copy.deepcopy(orig_missing)
    sid = missing_tampered["missing_inputs"][0]["source_id"]
    missing_tampered["missing_inputs"][0]["reason"] = "tampered_arbitrary_reason"
    missing_path.write_text(json.dumps(missing_tampered), encoding="utf-8")
    receipt_tampered["missing_report_sha256"] = custody.sha256_file(missing_path)
    receipt_tampered["receipt_id"] = custody._make_receipt_id(
        receipt_tampered["config_sha256"],
        receipt_tampered["index_sha256"],
        receipt_tampered["missing_report_sha256"],
    )
    (tgt_custody / "v4_source_custody_access_receipt_v1.json").write_text(
        json.dumps(receipt_tampered), encoding="utf-8"
    )

    with pytest.raises(custody.CustodyAccessError, match=rf"Missing report entry for '{re.escape(sid)}' mismatch"):
        custody.verify(CONFIG_PATH, input_root=repo_root, output_root=tampered_out)


def test_receipt_id_includes_missing_report_sha256() -> None:
    """Receipt ID must cryptographically bind config, index, and missing report hashes."""
    id1 = custody._make_receipt_id("cfg_hash", "idx_hash", "missing_hash_1")
    id2 = custody._make_receipt_id("cfg_hash", "idx_hash", "missing_hash_2")
    assert id1 != id2

    receipt_orig = Path("data/projects/open_model_data/custody/v4_source_custody_access_receipt_v1.json")
    receipt_data = json.loads(receipt_orig.read_text(encoding="utf-8"))
    expected_id = custody._make_receipt_id(
        receipt_data["config_sha256"],
        receipt_data["index_sha256"],
        receipt_data["missing_report_sha256"],
    )
    assert receipt_data["receipt_id"] == expected_id


def test_validate_and_resolve_paths_rejects_aliasing_collision_and_escaping(tmp_path: Path) -> None:
    """Validate that output paths cannot alias inputs, collide with each other, or escape output_root."""
    in_root = tmp_path / "inputs"
    out_root = tmp_path / "outputs"
    in_root.mkdir()
    out_root.mkdir()

    base_cfg: dict[str, Any] = {
        "inputs": {
            "provenance_index": "data/provenance.jsonl",
            "database": "data/sources.db",
            "textbook_chunks_dir": "data/chunks",
        },
        "outputs": {
            "index": "out/index.jsonl",
            "missing_report": "out/missing.json",
            "receipt": "out/receipt.json",
        },
    }

    # Normal valid resolution
    _res_in, res_out = custody.validate_and_resolve_paths(base_cfg, in_root, out_root)
    assert res_out["index"] == (out_root / "out/index.jsonl").resolve()

    # Output aliases database input
    cfg_alias_db = copy.deepcopy(base_cfg)
    cfg_alias_db["outputs"]["index"] = "data/sources.db"
    with pytest.raises(custody.CustodyAccessError, match=r"aliases input 'database'"):
        custody.validate_and_resolve_paths(cfg_alias_db, input_root=tmp_path, output_root=tmp_path)

    # Output inside textbook_chunks_dir
    cfg_inside_chunks = copy.deepcopy(base_cfg)
    cfg_inside_chunks["outputs"]["index"] = "data/chunks/sub/index.jsonl"
    with pytest.raises(custody.CustodyAccessError, match=r"located inside input directory 'textbook_chunks_dir'"):
        custody.validate_and_resolve_paths(cfg_inside_chunks, input_root=tmp_path, output_root=tmp_path)

    # Output collision between two outputs
    cfg_collision = copy.deepcopy(base_cfg)
    cfg_collision["outputs"]["receipt"] = "out/index.jsonl"
    with pytest.raises(custody.CustodyAccessError, match=r"Output path collision between 'index' and 'receipt'"):
        custody.validate_and_resolve_paths(cfg_collision, in_root, out_root)

    # Output escapes output_root
    cfg_escape = copy.deepcopy(base_cfg)
    cfg_escape["outputs"]["index"] = "../../escaped.jsonl"
    with pytest.raises(custody.CustodyAccessError, match=r"escapes output_root"):
        custody.validate_and_resolve_paths(cfg_escape, in_root, out_root)

    # Missing required output key
    cfg_missing_key = copy.deepcopy(base_cfg)
    del cfg_missing_key["outputs"]["receipt"]
    with pytest.raises(custody.CustodyAccessError, match=r"Missing required output key in config: 'receipt'"):
        custody.validate_and_resolve_paths(cfg_missing_key, in_root, out_root)


def test_cohort_spec_and_reader_reject_unapproved_table_names_and_sql_injection(tmp_path: Path) -> None:
    """Cohort config, stream reader, and verifier reject unapproved tables and SQL injection."""
    # Config cohort with SQL injection in primary_store
    with pytest.raises(custody.CustodyAccessError, match=r"primary_store .* does not match approved store"):
        custody.validate_cohort_spec(
            {
                "cohort_id": "lit",
                "source_family": "literary",
                "resolver_kind": "sqlite_database",
                "lineage_rule": "native_digital_source",
                "primary_store": "sqlite:sources.db#literary_texts WHERE source_file = ? OR 1=1 --",
            }
        )

    # Config cohort with unapproved table
    with pytest.raises(custody.CustodyAccessError, match=r"primary_store .* does not match approved store"):
        custody.validate_cohort_spec(
            {
                "cohort_id": "tb",
                "source_family": "public_textbooks",
                "resolver_kind": "hybrid_sqlite_chunks_archive",
                "lineage_rule": "native_pdf_text",
                "primary_store": "sqlite:sources.db#sqlite_master",
            }
        )

    # BoundedCustodyReader rejects unapproved table
    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(db_file)
    conn.execute("CREATE TABLE foo (id INT);")
    conn.commit()
    conn.close()

    reader = custody.BoundedCustodyReader(db_file)
    with pytest.raises(custody.CustodyAccessError, match=r"not an approved custody database table"):
        reader.read_source_stream("sqlite_master", "dummy")

    with pytest.raises(custody.CustodyAccessError, match=r"not an approved custody database table"):
        reader.read_source_stream("literary_texts WHERE 1=1 --", "dummy")


def test_verify_detects_duplicate_missing_source_id_and_omissions(tmp_path: Path, repo_root: Path) -> None:
    """Missing report verification detects duplicate source IDs and omitted items."""
    tampered_out = tmp_path / "out"
    custody_dir = tampered_out / "data/projects/open_model_data/custody"
    custody_dir.mkdir(parents=True)

    (custody_dir / "v4_source_custody_access_index_v1.jsonl").write_bytes(
        Path("data/projects/open_model_data/custody/v4_source_custody_access_index_v1.jsonl").read_bytes()
    )

    orig_missing = json.loads(
        Path("data/projects/open_model_data/custody/v4_source_custody_missing_report_v1.json").read_text(
            encoding="utf-8"
        )
    )

    # Duplicate an entry while keeping list length identical (replaces entry 1 with copy of entry 0)
    dup_missing = copy.deepcopy(orig_missing)
    dup_missing["missing_inputs"][1] = copy.deepcopy(dup_missing["missing_inputs"][0])
    dup_path = custody_dir / "v4_source_custody_missing_report_v1.json"
    dup_path.write_text(json.dumps(dup_missing), encoding="utf-8")

    receipt_orig = Path("data/projects/open_model_data/custody/v4_source_custody_access_receipt_v1.json")
    receipt_data = json.loads(receipt_orig.read_text(encoding="utf-8"))
    receipt_dup = copy.deepcopy(receipt_data)
    receipt_dup["missing_report_sha256"] = custody.sha256_file(dup_path)
    receipt_dup["receipt_id"] = custody._make_receipt_id(
        receipt_dup["config_sha256"],
        receipt_dup["index_sha256"],
        receipt_dup["missing_report_sha256"],
    )
    (custody_dir / "v4_source_custody_access_receipt_v1.json").write_text(json.dumps(receipt_dup), encoding="utf-8")

    with pytest.raises(custody.CustodyAccessError, match=r"duplicate source_id .* in missing_inputs"):
        custody.verify(CONFIG_PATH, input_root=repo_root, output_root=tampered_out)


@pytest.mark.parametrize(
    ("mutation_key", "mutation_val"),
    [
        ("permitted", False),
        ("permitted_cohort_ids", ["public-textbooks-non-stem-non-ocr"]),
        ("description", "Tampered progression decision text without any private paths"),
    ],
)
def test_verify_detects_tampered_progression_decision(
    tmp_path: Path, repo_root: Path, mutation_key: str, mutation_val: Any
) -> None:
    """Missing report progression decision tampering is caught by verify()."""
    tampered_out = tmp_path / "out"
    custody_dir = tampered_out / "data/projects/open_model_data/custody"
    custody_dir.mkdir(parents=True)

    (custody_dir / "v4_source_custody_access_index_v1.jsonl").write_bytes(
        Path("data/projects/open_model_data/custody/v4_source_custody_access_index_v1.jsonl").read_bytes()
    )

    missing_data = json.loads(
        Path("data/projects/open_model_data/custody/v4_source_custody_missing_report_v1.json").read_text(
            encoding="utf-8"
        )
    )
    missing_data["accessible_eligible_sources_permitted_to_proceed"][mutation_key] = mutation_val

    missing_path = custody_dir / "v4_source_custody_missing_report_v1.json"
    missing_path.write_text(json.dumps(missing_data), encoding="utf-8")

    receipt_orig = Path("data/projects/open_model_data/custody/v4_source_custody_access_receipt_v1.json")
    receipt_data = json.loads(receipt_orig.read_text(encoding="utf-8"))
    receipt_tampered = copy.deepcopy(receipt_data)
    receipt_tampered["missing_report_sha256"] = custody.sha256_file(missing_path)
    receipt_tampered["receipt_id"] = custody._make_receipt_id(
        receipt_tampered["config_sha256"],
        receipt_tampered["index_sha256"],
        receipt_tampered["missing_report_sha256"],
    )
    (custody_dir / "v4_source_custody_access_receipt_v1.json").write_text(
        json.dumps(receipt_tampered), encoding="utf-8"
    )

    with pytest.raises(
        custody.CustodyAccessError,
        match=r"Missing report accessible_eligible_sources_permitted_to_proceed mismatch",
    ):
        custody.verify(CONFIG_PATH, input_root=repo_root, output_root=tampered_out)


def test_verify_detects_tampered_primary_store_in_index(tmp_path: Path, repo_root: Path) -> None:
    """Index record with tampered primary_store (e.g. SQL injection suffix) is rejected by verify()."""
    tampered_out = tmp_path / "out"
    custody_dir = tampered_out / "data/projects/open_model_data/custody"
    custody_dir.mkdir(parents=True)

    idx_orig = Path("data/projects/open_model_data/custody/v4_source_custody_access_index_v1.jsonl")
    lines = idx_orig.read_text(encoding="utf-8").splitlines()
    # Tamper second line (first access record)
    first_record = json.loads(lines[1])
    first_record["custody_resolution"]["primary_store"] = "sqlite:sources.db#literary_texts WHERE 1=1 --"
    lines[1] = custody.canonical_json(first_record)

    idx_path = custody_dir / "v4_source_custody_access_index_v1.jsonl"
    idx_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    (custody_dir / "v4_source_custody_missing_report_v1.json").write_bytes(
        Path("data/projects/open_model_data/custody/v4_source_custody_missing_report_v1.json").read_bytes()
    )

    receipt_orig = Path("data/projects/open_model_data/custody/v4_source_custody_access_receipt_v1.json")
    receipt_data = json.loads(receipt_orig.read_text(encoding="utf-8"))
    receipt_tampered = copy.deepcopy(receipt_data)
    receipt_tampered["index_sha256"] = custody.sha256_file(idx_path)
    receipt_tampered["receipt_id"] = custody._make_receipt_id(
        receipt_tampered["config_sha256"],
        receipt_tampered["index_sha256"],
        receipt_tampered["missing_report_sha256"],
    )
    (custody_dir / "v4_source_custody_access_receipt_v1.json").write_text(
        json.dumps(receipt_tampered), encoding="utf-8"
    )

    with pytest.raises(custody.CustodyAccessError, match=r"primary_store .* does not match expected"):
        custody.verify(CONFIG_PATH, input_root=repo_root, output_root=tampered_out)


def test_validate_and_resolve_paths_protects_config_and_schemas_from_aliases(repo_root: Path) -> None:
    """Outputs cannot alias consumed config file or schema contracts."""
    base_cfg: dict[str, Any] = {
        "inputs": {
            "provenance_index": "data/provenance.jsonl",
            "database": "data/sources.db",
            "textbook_chunks_dir": "data/chunks",
        },
        "outputs": {
            "index": "out/index.jsonl",
            "missing_report": "out/missing.json",
            "receipt": "out/receipt.json",
        },
    }

    # Output aliases config path
    cfg_alias_config = copy.deepcopy(base_cfg)
    cfg_alias_config["outputs"]["index"] = str(custody.DEFAULT_CONFIG)
    with pytest.raises(custody.CustodyAccessError, match=r"aliases input 'config'"):
        custody.validate_and_resolve_paths(
            cfg_alias_config, input_root=repo_root, output_root=repo_root, config_path=custody.DEFAULT_CONFIG
        )

    # Output aliases item schema
    cfg_alias_schema = copy.deepcopy(base_cfg)
    cfg_alias_schema["outputs"]["index"] = str(custody.ITEM_SCHEMA_PATH)
    with pytest.raises(custody.CustodyAccessError, match=r"aliases input 'item_schema'"):
        custody.validate_and_resolve_paths(cfg_alias_schema, input_root=repo_root, output_root=repo_root)

    # Output aliases missing report schema
    cfg_alias_missing_schema = copy.deepcopy(base_cfg)
    cfg_alias_missing_schema["outputs"]["index"] = str(custody.MISSING_REPORT_SCHEMA_PATH)
    with pytest.raises(custody.CustodyAccessError, match=r"aliases input 'missing_report_schema'"):
        custody.validate_and_resolve_paths(cfg_alias_missing_schema, input_root=repo_root, output_root=repo_root)


def test_validate_cohort_spec_and_lineage_reject_non_ocr_excluded_modes(tmp_path: Path) -> None:
    """Cohort configuration and chunk lineage reader reject non-OCR extraction modes in excluded_modes."""
    for bad_mode in ("native_text", "native_pdf_text", "unknown", "invalid_mode"):
        with pytest.raises(custody.CustodyAccessError, match=r"excluded_modes contains unsupported or non-OCR mode"):
            custody.validate_cohort_spec(
                {
                    "cohort_id": "tb",
                    "source_family": "public_textbooks",
                    "resolver_kind": "hybrid_sqlite_chunks_archive",
                    "lineage_rule": "native_pdf_text",
                    "excluded_modes": [bad_mode],
                }
            )

        with pytest.raises(custody.CustodyAccessError, match=r"excluded_modes contains unsupported or non-OCR mode"):
            custody.check_chunk_file_lineage(tmp_path / "dummy.jsonl", excluded_modes=[bad_mode])
