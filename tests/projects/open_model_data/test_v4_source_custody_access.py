"""Tests for V4 source custody access resolution and verification (#7884).

Validates ACCESS-1 through ACCESS-4 under epic #7423.
"""

from __future__ import annotations

import copy
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

    mode, is_ocr, count, chars, records = custody.check_chunk_file_lineage(chunk_file)
    assert mode == "native_pdf_text"
    assert is_ocr is False
    assert count == 2
    assert chars > 0
    assert len(records) == 2


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

    mode, is_ocr, count, _chars, _records = custody.check_chunk_file_lineage(chunk_file)
    assert mode == "apple_vision_ocr"
    assert is_ocr is True
    assert count == 2


def test_check_chunk_file_lineage_unknown_fails_closed(tmp_path: Path) -> None:
    chunk_file = tmp_path / "unknown_sample.jsonl"
    rows = [
        {"chunk_id": "c1", "extraction_mode": "some_heuristic_extract", "text": "Привіт."},
    ]
    chunk_file.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    mode, is_ocr, _count, _chars, _records = custody.check_chunk_file_lineage(chunk_file)
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

    mode, is_ocr, count, _chars, _records = custody.check_chunk_file_lineage(chunk_file)
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
    receipt_data["receipt_id"] = custody._make_receipt_id(receipt_data["config_sha256"], receipt_data["index_sha256"])
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
        receipt_tampered["config_sha256"], receipt_tampered["index_sha256"]
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
        receipt_tampered["config_sha256"], receipt_tampered["index_sha256"]
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
        receipt_tampered["config_sha256"], receipt_tampered["index_sha256"]
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

    # Change source_family for record 0 to create a projection mismatch with provenance denominator
    records[0]["source_family"] = "public_textbooks"
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
        receipt_tampered["config_sha256"], receipt_tampered["index_sha256"]
    )
    (custody_dir / "v4_source_custody_access_receipt_v1.json").write_text(
        json.dumps(receipt_tampered), encoding="utf-8"
    )

    with pytest.raises(custody.CustodyAccessError, match=r"projection does not match provenance denominator"):
        custody.verify(CONFIG_PATH, input_root=repo_root, output_root=tampered_out)


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
        receipt_tampered["config_sha256"], receipt_tampered["index_sha256"]
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
        receipt_tampered["config_sha256"], receipt_tampered["index_sha256"]
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

    (custody_dir / "v4_source_custody_access_index_v1.jsonl").write_bytes(
        Path("data/projects/open_model_data/custody/v4_source_custody_access_index_v1.jsonl").read_bytes()
    )

    missing_data = json.loads(
        Path("data/projects/open_model_data/custody/v4_source_custody_missing_report_v1.json").read_text(
            encoding="utf-8"
        )
    )
    missing_data["missing_inputs"][0]["reason"] = "private archive unavailable"
    missing_data["owner"] = "root cause investigator"
    missing_data["scope"] = "temp failure investigation for non-stem cohort"

    missing_path = custody_dir / "v4_source_custody_missing_report_v1.json"
    missing_path.write_text(json.dumps(missing_data, indent=2) + "\n", encoding="utf-8")

    receipt_orig = Path("data/projects/open_model_data/custody/v4_source_custody_access_receipt_v1.json")
    receipt_data = json.loads(receipt_orig.read_text(encoding="utf-8"))
    receipt_updated = copy.deepcopy(receipt_data)
    receipt_updated["missing_report_sha256"] = custody.sha256_file(missing_path)
    (custody_dir / "v4_source_custody_access_receipt_v1.json").write_text(
        json.dumps(receipt_updated, indent=2) + "\n", encoding="utf-8"
    )

    assert custody.verify(CONFIG_PATH, input_root=repo_root, output_root=valid_out) is True
