#!/usr/bin/env python3
"""Tests for v4_native_extraction_validation.py (Issue #7885)."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import v4_native_extraction_validation as extraction

CONFIG_PATH = Path("data/projects/open_model_data/extraction/v4_native_extraction_config_v1.json")


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_schema_contracts_valid() -> None:
    """Validate all native extraction schema contracts against Draft 2020-12."""
    for path in (
        extraction.CONFIG_SCHEMA_PATH,
        extraction.ITEM_SCHEMA_PATH,
        extraction.QUARANTINE_SCHEMA_PATH,
        extraction.RECEIPT_SCHEMA_PATH,
    ):
        assert path.is_file(), f"Missing schema contract: {path}"
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)


def test_evaluate_span_fidelity_clean_native() -> None:
    """Clean authentic Ukrainian text (including apostrophes and archaic Cyrillic) passes as faithful."""
    rules = {
        "anomaly_detection": {
            "detect_replacement_characters": True,
            "detect_duplicate_lines": True,
            "detect_truncation_pairs": True,
            "detect_intraline_duplicates": True,
            "fail_closed_on_ocr": True,
        }
    }
    # Text with standard Ukrainian apostrophes, Cyrillic letters, and archaic orthography
    clean_text = "Зв'язок мови і культури: пам'ять, відродження та дух народу. Вѣдомо всѣмъ."
    status, enc_valid, findings, training_eligible = extraction.evaluate_span_fidelity(clean_text, rules, is_ocr=False)

    assert status == "ACCEPTED_FAITHFUL"
    assert enc_valid is True
    assert training_eligible is True
    assert len([f for f in findings if f["severity"] == "BLOCKING"]) == 0


def test_evaluate_span_fidelity_detects_replacement_characters() -> None:
    """Replacement character U+FFFD and illegal ASCII controls are rejected as damaged (EXTRACT-2)."""
    rules = {
        "anomaly_detection": {
            "detect_replacement_characters": True,
            "detect_duplicate_lines": True,
            "detect_truncation_pairs": True,
            "detect_intraline_duplicates": True,
            "fail_closed_on_ocr": True,
        }
    }
    # Text with replacement character
    damaged_text = "Пошкоджений текст \ufffd уривок."
    status, enc_valid, findings, training_eligible = extraction.evaluate_span_fidelity(
        damaged_text, rules, is_ocr=False
    )
    assert status == "REJECTED_DAMAGED"
    assert enc_valid is False
    assert training_eligible is False
    assert any(f["type"] == "unicode_replacement_character" for f in findings)

    # Text with illegal ASCII control character (e.g. SOH 0x01)
    control_text = "Текст з невидимим байтом \x01 контролю."
    status2, enc_valid2, findings2, training_eligible2 = extraction.evaluate_span_fidelity(
        control_text, rules, is_ocr=False
    )
    assert status2 == "REJECTED_DAMAGED"
    assert enc_valid2 is False
    assert training_eligible2 is False
    assert any(f["type"] == "illegal_control_character" for f in findings2)


def test_evaluate_span_fidelity_detects_layout_anomalies() -> None:
    """Duplicate lines and intraline repeat patterns are quarantined (EXTRACT-2)."""
    rules = {
        "anomaly_detection": {
            "detect_replacement_characters": True,
            "detect_duplicate_lines": True,
            "detect_truncation_pairs": True,
            "detect_intraline_duplicates": True,
            "fail_closed_on_ocr": True,
        }
    }
    # Duplicate line pair (>= 40 chars, >= 15 alpha)
    repeated_line = "Це дуже довгий повторюваний рядок тексту для перевірки дублікатів."
    anomalous_text = f"{repeated_line}\n{repeated_line}"
    status, enc_valid, findings, training_eligible = extraction.evaluate_span_fidelity(
        anomalous_text, rules, is_ocr=False
    )
    assert status == "QUARANTINED_ANOMALOUS"
    assert enc_valid is True  # Encoding is valid, but layout is anomalous
    assert training_eligible is False
    assert any(f["type"] == "adjacent_duplicate_line_pairs" for f in findings)


def test_evaluate_span_fidelity_excludes_ocr() -> None:
    """OCR-derived passages fail closed and are excluded from training (EXTRACT-3)."""
    rules = {"anomaly_detection": {"fail_closed_on_ocr": True}}
    status, _enc_valid, findings, training_eligible = extraction.evaluate_span_fidelity(
        "Будь-який текст.", rules, is_ocr=True
    )
    assert status == "EXCLUDED_OCR"
    assert training_eligible is False
    assert any(f["type"] == "ocr_extraction_detected" for f in findings)


def test_verify_detects_tampered_receipt_hashes(tmp_path: Path, repo_root: Path) -> None:
    """verify() detects when index_sha256 or quarantine_report_sha256 in receipt is tampered."""
    tampered_out = tmp_path / "out"
    tgt_extract = tampered_out / "data/projects/open_model_data/extraction"
    tgt_extract.mkdir(parents=True)

    orig_idx = Path("data/projects/open_model_data/extraction/v4_native_extraction_index_v1.jsonl").read_bytes()
    orig_quarantine = Path(
        "data/projects/open_model_data/extraction/v4_native_extraction_quarantine_report_v1.json"
    ).read_bytes()
    orig_receipt_data = json.loads(
        Path("data/projects/open_model_data/extraction/v4_native_extraction_receipt_v1.json").read_text(
            encoding="utf-8"
        )
    )

    (tgt_extract / "v4_native_extraction_index_v1.jsonl").write_bytes(orig_idx)
    (tgt_extract / "v4_native_extraction_quarantine_report_v1.json").write_bytes(orig_quarantine)

    # Tamper index_sha256 in receipt
    receipt_tampered = copy.deepcopy(orig_receipt_data)
    receipt_tampered["index_sha256"] = "0" * 64
    (tgt_extract / "v4_native_extraction_receipt_v1.json").write_text(json.dumps(receipt_tampered), encoding="utf-8")

    with pytest.raises(extraction.NativeExtractionError, match=r"Receipt index_sha256 mismatch"):
        extraction.verify(CONFIG_PATH, input_root=repo_root, output_root=tampered_out)

    # Tamper receipt_id
    receipt_tampered2 = copy.deepcopy(orig_receipt_data)
    receipt_tampered2["receipt_id"] = "receipt.extraction.000000000000000000000000"
    (tgt_extract / "v4_native_extraction_receipt_v1.json").write_text(json.dumps(receipt_tampered2), encoding="utf-8")

    with pytest.raises(extraction.NativeExtractionError, match=r"Receipt ID mismatch"):
        extraction.verify(CONFIG_PATH, input_root=repo_root, output_root=tampered_out)


def test_verify_detects_contradictory_fidelity_invariants(tmp_path: Path, repo_root: Path) -> None:
    """verify() rejects records where quarantined or damaged spans claim training_eligible=True."""
    tampered_out = tmp_path / "out"
    tgt_extract = tampered_out / "data/projects/open_model_data/extraction"
    tgt_extract.mkdir(parents=True)

    orig_lines = (
        Path("data/projects/open_model_data/extraction/v4_native_extraction_index_v1.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    header = orig_lines[0]
    first_record = json.loads(orig_lines[1])

    # Contradictory: status QUARANTINED_ANOMALOUS but training_eligible=True
    first_record["fidelity_assessment"]["status"] = "QUARANTINED_ANOMALOUS"
    first_record["fidelity_assessment"]["training_eligible"] = True

    tampered_lines = [header, json.dumps(first_record), *orig_lines[2:]]
    idx_path = tgt_extract / "v4_native_extraction_index_v1.jsonl"
    idx_path.write_text("\n".join(tampered_lines) + "\n", encoding="utf-8")

    quarantine_path = tgt_extract / "v4_native_extraction_quarantine_report_v1.json"
    quarantine_path.write_bytes(
        Path("data/projects/open_model_data/extraction/v4_native_extraction_quarantine_report_v1.json").read_bytes()
    )

    # Build matching receipt
    receipt_data = json.loads(
        Path("data/projects/open_model_data/extraction/v4_native_extraction_receipt_v1.json").read_text(
            encoding="utf-8"
        )
    )
    receipt_tampered = copy.deepcopy(receipt_data)
    receipt_tampered["index_sha256"] = extraction.sha256_file(idx_path)
    receipt_tampered["receipt_id"] = extraction._make_receipt_id(
        receipt_tampered["config_sha256"],
        receipt_tampered["index_sha256"],
        receipt_tampered["quarantine_report_sha256"],
    )
    (tgt_extract / "v4_native_extraction_receipt_v1.json").write_text(json.dumps(receipt_tampered), encoding="utf-8")

    with pytest.raises(
        extraction.NativeExtractionError, match=r"QUARANTINED_ANOMALOUS span cannot have training_eligible=True"
    ):
        extraction.verify(CONFIG_PATH, input_root=repo_root, output_root=tampered_out)


def test_verify_detects_non_consecutive_sequence_order(tmp_path: Path, repo_root: Path) -> None:
    """verify() rejects records with gaps or reordering in reconstruction sequence_order (EXTRACT-4)."""
    tampered_out = tmp_path / "out"
    tgt_extract = tampered_out / "data/projects/open_model_data/extraction"
    tgt_extract.mkdir(parents=True)

    orig_lines = (
        Path("data/projects/open_model_data/extraction/v4_native_extraction_index_v1.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    header = orig_lines[0]
    first_record = json.loads(orig_lines[1])
    # Tamper first record sequence_order from 0 to 5
    first_record["reconstruction_linkage"]["sequence_order"] = 5

    tampered_lines = [header, json.dumps(first_record), *orig_lines[2:]]
    idx_path = tgt_extract / "v4_native_extraction_index_v1.jsonl"
    idx_path.write_text("\n".join(tampered_lines) + "\n", encoding="utf-8")

    quarantine_path = tgt_extract / "v4_native_extraction_quarantine_report_v1.json"
    quarantine_path.write_bytes(
        Path("data/projects/open_model_data/extraction/v4_native_extraction_quarantine_report_v1.json").read_bytes()
    )

    receipt_data = json.loads(
        Path("data/projects/open_model_data/extraction/v4_native_extraction_receipt_v1.json").read_text(
            encoding="utf-8"
        )
    )
    receipt_tampered = copy.deepcopy(receipt_data)
    receipt_tampered["index_sha256"] = extraction.sha256_file(idx_path)
    receipt_tampered["receipt_id"] = extraction._make_receipt_id(
        receipt_tampered["config_sha256"],
        receipt_tampered["index_sha256"],
        receipt_tampered["quarantine_report_sha256"],
    )
    (tgt_extract / "v4_native_extraction_receipt_v1.json").write_text(json.dumps(receipt_tampered), encoding="utf-8")

    with pytest.raises(extraction.NativeExtractionError, match=r"first span sequence_order must be 0"):
        extraction.verify(CONFIG_PATH, input_root=repo_root, output_root=tampered_out)


def test_verify_detects_prohibited_private_host_paths(tmp_path: Path, repo_root: Path) -> None:
    """verify() fails closed if private host paths are found in receipt or quarantine report."""
    tampered_out = tmp_path / "out"
    tgt_extract = tampered_out / "data/projects/open_model_data/extraction"
    tgt_extract.mkdir(parents=True)

    (tgt_extract / "v4_native_extraction_index_v1.jsonl").write_bytes(
        Path("data/projects/open_model_data/extraction/v4_native_extraction_index_v1.jsonl").read_bytes()
    )

    quarantine_data = json.loads(
        Path("data/projects/open_model_data/extraction/v4_native_extraction_quarantine_report_v1.json").read_text(
            encoding="utf-8"
        )
    )
    quarantine_data["quarantined_spans"][0]["reason"] = "failed at /home/ops/secret/corpus"
    quarantine_path = tgt_extract / "v4_native_extraction_quarantine_report_v1.json"
    quarantine_path.write_text(json.dumps(quarantine_data), encoding="utf-8")

    receipt_data = json.loads(
        Path("data/projects/open_model_data/extraction/v4_native_extraction_receipt_v1.json").read_text(
            encoding="utf-8"
        )
    )
    receipt_tampered = copy.deepcopy(receipt_data)
    receipt_tampered["quarantine_report_sha256"] = extraction.sha256_file(quarantine_path)
    receipt_tampered["receipt_id"] = extraction._make_receipt_id(
        receipt_tampered["config_sha256"],
        receipt_tampered["index_sha256"],
        receipt_tampered["quarantine_report_sha256"],
    )
    (tgt_extract / "v4_native_extraction_receipt_v1.json").write_text(json.dumps(receipt_tampered), encoding="utf-8")

    with pytest.raises(
        extraction.NativeExtractionError, match=r"Quarantine report contains prohibited private or absolute host paths"
    ):
        extraction.verify(CONFIG_PATH, input_root=repo_root, output_root=tampered_out)


def test_build_and_verify_clean_exit() -> None:
    """Current committed extraction artifacts pass verify() cleanly."""
    extraction.verify(CONFIG_PATH)


def test_verify_passes_in_unprovisioned_ci_without_sources_db(tmp_path: Path, repo_root: Path) -> None:
    """verify() succeeds in CI environments where data/sources.db is not provisioned."""
    ci_root = tmp_path / "ci_runner"
    # Copy only schemas, config, and extraction artifacts (no sources.db)
    for sub in [
        "data/projects/open_model_data/contracts",
        "data/projects/open_model_data/extraction",
    ]:
        dest = ci_root / sub
        dest.mkdir(parents=True)
        for f in (repo_root / sub).iterdir():
            if f.is_file():
                (dest / f.name).write_bytes(f.read_bytes())

    # Verify that sources.db does NOT exist in ci_root
    assert not (ci_root / "data/sources.db").exists()

    # verify() must succeed on the committed artifacts
    extraction.verify(
        ci_root / "data/projects/open_model_data/extraction/v4_native_extraction_config_v1.json",
        input_root=ci_root,
        output_root=ci_root,
    )
