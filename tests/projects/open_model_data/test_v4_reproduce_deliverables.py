"""Tests for final private dataset and learning-study deliverables reproduction (Issue #7433)."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from scripts.projects.open_model_data.v4_reproduce_deliverables import (
    assert_no_private_host_paths,
    load_dataset_stream,
    load_partition_view,
    verify_delivery,
)

CONTRACTS_DIR = Path("data/projects/open_model_data/contracts")
DATASET_DIR = Path("data/projects/open_model_data/dataset")
DELIVERY_DIR = Path("data/projects/open_model_data/delivery")
RECORDS_PATH = DATASET_DIR / "v4_human_source_dataset_records_v1.jsonl"
DELIVERY_RECEIPT_PATH = DELIVERY_DIR / "v4_delivery_reproduction_receipt_v1.json"


def test_schema_valid() -> None:
    """The delivery reproduction receipt schema must be Draft 2020-12 valid."""
    schema_path = CONTRACTS_DIR / "v4_delivery_reproduction_receipt_v1.schema.json"
    assert schema_path.is_file(), f"Missing schema contract: {schema_path}"
    schema_data = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema_data)


def test_delivery1_stream_loader_and_partition_views() -> None:
    """Verify stream loader and exact partition filtering (DELIVERY-1)."""
    assert RECORDS_PATH.is_file(), f"Missing records: {RECORDS_PATH}"
    stream_records = list(load_dataset_stream(RECORDS_PATH))
    assert len(stream_records) == 1419

    training_records = load_partition_view(RECORDS_PATH, "training")
    assert len(training_records) == 614

    heldout_records = load_partition_view(RECORDS_PATH, "heldout_evaluation")
    assert len(heldout_records) == 559

    dev_records = load_partition_view(RECORDS_PATH, "development")
    assert len(dev_records) == 245


def test_delivery2_documentation_artifacts_exist() -> None:
    """Verify all deliverable documentation exists and is linked in the receipt (DELIVERY-2 & DELIVERY-6)."""
    assert DELIVERY_RECEIPT_PATH.is_file(), f"Missing receipt: {DELIVERY_RECEIPT_PATH}"
    receipt = json.loads(DELIVERY_RECEIPT_PATH.read_text(encoding="utf-8"))
    docs = receipt["deliverable_documents"]

    card_path = Path(docs["dataset_card"])
    report_path = Path(docs["technical_report"])
    summary_path = Path(docs["research_summary"])

    assert card_path.is_file(), f"Missing dataset card: {card_path}"
    assert report_path.is_file(), f"Missing technical report: {report_path}"
    assert summary_path.is_file(), f"Missing research summary: {summary_path}"

    assert len(card_path.read_text(encoding="utf-8")) > 100
    assert len(report_path.read_text(encoding="utf-8")) > 100
    assert len(summary_path.read_text(encoding="utf-8")) > 100


def test_delivery3_learning_results_reported() -> None:
    """Verify actual controlled open-weight learning study outcomes are reproduced (DELIVERY-3)."""
    receipt = json.loads(DELIVERY_RECEIPT_PATH.read_text(encoding="utf-8"))
    study = receipt["learning_study_reproduction"]

    assert study["runs_count"] == 9
    assert study["baseline_perplexity_mean"] == 14.805
    assert study["adapted_perplexity_mean"] == 10.935
    assert study["perplexity_delta_pct"] < -20.0


def test_delivery4_distinct_verdicts() -> None:
    """Verify dataset quality and learning utility verdicts are stated separately (DELIVERY-4)."""
    receipt = json.loads(DELIVERY_RECEIPT_PATH.read_text(encoding="utf-8"))
    assert receipt["dataset_quality_verdict"] == "DATASET_QUALITY_CONFIRMED"
    assert receipt["learning_utility_verdict"] == "LEARNING_UTILITY_CONFIRMED"
    assert receipt["overall_delivery_verdict"] == "EPIC_DELIVERABLES_CONFIRMED"


def test_delivery5_custody_and_zero_host_paths() -> None:
    """Verify custody retention and absence of private host paths (DELIVERY-5)."""
    receipt = json.loads(DELIVERY_RECEIPT_PATH.read_text(encoding="utf-8"))
    assert receipt["custody_retained"] is True
    assert receipt["zero_host_paths_verified"] is True
    assert_no_private_host_paths(receipt)

    with pytest.raises(ValueError, match="Prohibited host path detected"):
        assert_no_private_host_paths({"leak": "/home/user/data"})


def test_verify_delivery_clean_pass() -> None:
    """Verify delivery verification passes on intact deliverables."""
    assert verify_delivery(Path.cwd(), DELIVERY_RECEIPT_PATH) is True


def test_verify_delivery_detects_tampered_artifact(tmp_path: Path) -> None:
    """Verify delivery verification detects missing or corrupted artifacts."""
    # Modified receipt with mismatched dataset manifest digest fails verification
    receipt = json.loads(DELIVERY_RECEIPT_PATH.read_text(encoding="utf-8"))
    receipt["dataset_reproduction"]["manifest_sha256"] = "0000000000000000000000000000000000000000000000000000000000000000"
    tampered_receipt = tmp_path / "tampered_receipt.json"
    tampered_receipt.write_text(json.dumps(receipt), encoding="utf-8")
    assert verify_delivery(Path.cwd(), tampered_receipt) is False

    # Modified receipt with mismatched runs digest fails verification
    receipt2 = json.loads(DELIVERY_RECEIPT_PATH.read_text(encoding="utf-8"))
    receipt2["learning_study_reproduction"]["runs_sha256"] = "0000000000000000000000000000000000000000000000000000000000000000"
    tampered_receipt2 = tmp_path / "tampered_receipt2.json"
    tampered_receipt2.write_text(json.dumps(receipt2), encoding="utf-8")
    assert verify_delivery(Path.cwd(), tampered_receipt2) is False
