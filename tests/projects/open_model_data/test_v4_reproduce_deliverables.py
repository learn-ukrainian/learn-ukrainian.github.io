"""Tests for final private dataset and learning-study deliverables reproduction (Issue #7433)."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from scripts.projects.open_model_data.v4_reproduce_deliverables import (
    assert_file_no_private_host_paths,
    assert_no_private_host_paths,
    load_dataset_stream,
    load_partition_view,
    resolve_record_loss_masks,
    resolve_record_text,
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

    # Verify stream loading with resolved modern_view loss mask spans
    resolved_records = list(load_dataset_stream(RECORDS_PATH, resolve_masks=True))
    assert len(resolved_records) == 1419
    first_resolved = resolved_records[0]
    m0 = first_resolved["language_views"]["modern_view"]
    assert "loss_mask_spans" in m0
    assert len(m0["loss_mask_spans"]) == m0["loss_mask_count"]

    # Verify direct record resolution
    resolved_spans = resolve_record_loss_masks(stream_records[0])
    assert resolved_spans == m0["loss_mask_spans"]

    # Verify stream loading with both resolved modern_view loss mask spans and authenticated text
    import hashlib
    text_records = list(load_dataset_stream(RECORDS_PATH, resolve_masks=True, resolve_text=True))
    assert len(text_records) == 1419
    t0 = text_records[0]
    assert "text" in t0
    assert "text" in t0["source_fidelity"]
    assert len(t0["text"]) == t0["source_fidelity"]["char_length"]
    assert hashlib.sha256(t0["text"].encode("utf-8")).hexdigest() == t0["source_fidelity"]["span_sha256"]

    # Verify direct text resolution on record
    resolved_text = resolve_record_text(stream_records[0])
    assert resolved_text == t0["text"]

    # Verify partition loading with resolved text
    training_text_records = load_partition_view(RECORDS_PATH, "training", resolve_masks=True, resolve_text=True)
    assert len(training_text_records) == 614
    assert "text" in training_text_records[0]


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
    assert receipt["learning_utility_verdict"] == "LEARNING_UTILITY_PROTOCOL_HARNESS_CONFIRMED_EMPIRICAL_PENDING"
    assert receipt["overall_delivery_verdict"] == "EPIC_DELIVERABLES_CONFIRMED_EMPIRICAL_PENDING"


def test_delivery5_custody_and_zero_host_paths() -> None:
    """Verify custody retention and absence of private host paths (DELIVERY-5)."""
    receipt = json.loads(DELIVERY_RECEIPT_PATH.read_text(encoding="utf-8"))
    assert receipt["custody_retained"] is True
    assert receipt["zero_host_paths_verified"] is True
    assert_no_private_host_paths(receipt)

    with pytest.raises(ValueError, match="Prohibited host path detected at leak"):
        assert_no_private_host_paths({"leak": "/home/user/data"})

    with pytest.raises(ValueError, match="Prohibited host path detected at leak"):
        assert_no_private_host_paths({"leak": "/workspace/repo/data"})

    with pytest.raises(ValueError, match="Prohibited host path detected at leak"):
        assert_no_private_host_paths({"leak": "/root/secret_data"})

    # Ensure scanned content is never echoed into the exception message
    secret_text = "SECRET_DOCUMENT_CONTENT_DO_NOT_ECHO /workspace/secret/path"
    try:
        assert_no_private_host_paths(secret_text, "doc_locator")
    except ValueError as exc:
        assert "SECRET_DOCUMENT_CONTENT_DO_NOT_ECHO" not in str(exc)
        assert "Prohibited host path detected at doc_locator" in str(exc)
    else:
        pytest.fail("Expected ValueError was not raised")


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

    # Modified receipt with mismatched document digest fails verification
    receipt3 = json.loads(DELIVERY_RECEIPT_PATH.read_text(encoding="utf-8"))
    receipt3["document_digests"]["dataset_card_sha256"] = "0000000000000000000000000000000000000000000000000000000000000000"
    tampered_receipt3 = tmp_path / "tampered_receipt3.json"
    tampered_receipt3.write_text(json.dumps(receipt3), encoding="utf-8")
    assert verify_delivery(Path.cwd(), tampered_receipt3) is False

    # Modified receipt with mismatched language usage index digest fails verification
    receipt4 = json.loads(DELIVERY_RECEIPT_PATH.read_text(encoding="utf-8"))
    receipt4["dataset_reproduction"]["language_usage_index_sha256"] = "0000000000000000000000000000000000000000000000000000000000000000"
    tampered_receipt4 = tmp_path / "tampered_receipt4.json"
    tampered_receipt4.write_text(json.dumps(receipt4), encoding="utf-8")
    assert verify_delivery(Path.cwd(), tampered_receipt4) is False


def test_verify_delivery_detects_tampered_document(tmp_path: Path) -> None:
    """Verify delivery verification detects tampered or leaked deliverable documents."""
    import shutil

    # Create a mock repo root with a copied structure
    mock_root = tmp_path / "mock_repo"
    mock_root.mkdir(parents=True, exist_ok=True)

    # Copy necessary contracts and artifacts
    for subpath in [
        "data/projects/open_model_data/contracts/v4_delivery_reproduction_receipt_v1.schema.json",
        "data/projects/open_model_data/language/v4_language_usage_index_v1.jsonl",
        "data/projects/open_model_data/dataset/v4_human_source_dataset_manifest_v1.json",
        "data/projects/open_model_data/dataset/v4_human_source_dataset_records_v1.jsonl",
        "data/projects/open_model_data/dataset/v4_human_source_dataset_receipt_v1.json",
        "data/projects/open_model_data/study/v4_learning_study_recipe_v1.json",
        "data/projects/open_model_data/study/v4_learning_study_execution_runs_v1.jsonl",
        "data/projects/open_model_data/study/v4_learning_study_receipt_v1.json",
        "docs/projects/ukrainian-data-foundry-evidence/HUMAN_SOURCE_DATASET_CARD.md",
        "docs/projects/ukrainian-data-foundry-evidence/HUMAN_SOURCE_TECHNICAL_REPORT.md",
        "docs/projects/ukrainian-data-foundry-evidence/RESEARCH_SUMMARY.md",
        "data/projects/open_model_data/delivery/v4_delivery_reproduction_receipt_v1.json",
    ]:
        src = Path.cwd() / subpath
        dst = mock_root / subpath
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    mock_receipt = mock_root / "data/projects/open_model_data/delivery/v4_delivery_reproduction_receipt_v1.json"
    assert verify_delivery(mock_root, mock_receipt) is True

    # Mutating document text without updating digest fails verification
    card = mock_root / "docs/projects/ukrainian-data-foundry-evidence/HUMAN_SOURCE_DATASET_CARD.md"
    orig_text = card.read_text(encoding="utf-8")
    card.write_text(orig_text + "\nTampered content", encoding="utf-8")
    assert verify_delivery(mock_root, mock_receipt) is False

    # Restoring original text passes
    card.write_text(orig_text, encoding="utf-8")
    assert verify_delivery(mock_root, mock_receipt) is True

    # Introducing a private host path into document fails verification even if digest is recomputed
    from scripts.projects.open_model_data.v4_reproduce_deliverables import sha256_file
    card.write_text(orig_text + "\nLeaked path: /home/secret/user", encoding="utf-8")
    rcpt_data = json.loads(mock_receipt.read_text(encoding="utf-8"))
    rcpt_data["document_digests"]["dataset_card_sha256"] = sha256_file(card)
    mock_receipt.write_text(json.dumps(rcpt_data, indent=2), encoding="utf-8")
    assert verify_delivery(mock_root, mock_receipt) is False

    # Restoring card and introducing a private host path (/workspace/...) into study runs fails verification
    card.write_text(orig_text, encoding="utf-8")
    rcpt_data["document_digests"]["dataset_card_sha256"] = sha256_file(card)

    study_runs = mock_root / "data/projects/open_model_data/study/v4_learning_study_execution_runs_v1.jsonl"
    orig_runs = study_runs.read_text(encoding="utf-8")
    study_runs.write_text(orig_runs + '{"run_id": "run.999", "recipe_id": "recipe.v4.learning.open_weight_pilot.20260910", "seed": 42, "path": "/workspace/checkout"}\n', encoding="utf-8")
    rcpt_data["learning_study_reproduction"]["runs_sha256"] = sha256_file(study_runs)
    mock_receipt.write_text(json.dumps(rcpt_data, indent=2), encoding="utf-8")
    assert verify_delivery(mock_root, mock_receipt) is False


def test_assert_file_no_private_host_paths(tmp_path: Path) -> None:
    """Ensure assert_file_no_private_host_paths scans files and raises ValueError without leaking text."""
    clean_file = tmp_path / "clean.txt"
    clean_file.write_text("Normal content\nSecond line\n", encoding="utf-8")
    assert_file_no_private_host_paths(clean_file, "clean.txt")

    leaked_file = tmp_path / "leaked.txt"
    leaked_file.write_text("CONFIDENTIAL_TOP_SECRET /root/checkout/secret\n", encoding="utf-8")
    with pytest.raises(ValueError) as excinfo:
        assert_file_no_private_host_paths(leaked_file, "leaked.txt")
    assert "CONFIDENTIAL_TOP_SECRET" not in str(excinfo.value)
    assert "Prohibited host path detected at leaked.txt:1" in str(excinfo.value)


def test_verify_delivery_rejects_path_traversal_and_out_of_repo_documents(tmp_path: Path) -> None:
    """Verify delivery verification rejects absolute paths, directory traversal, and out-of-repo files."""
    import shutil

    mock_root = tmp_path / "mock_repo"
    mock_root.mkdir(parents=True, exist_ok=True)

    for subpath in [
        "data/projects/open_model_data/contracts/v4_delivery_reproduction_receipt_v1.schema.json",
        "data/projects/open_model_data/language/v4_language_usage_index_v1.jsonl",
        "data/projects/open_model_data/dataset/v4_human_source_dataset_manifest_v1.json",
        "data/projects/open_model_data/dataset/v4_human_source_dataset_records_v1.jsonl",
        "data/projects/open_model_data/dataset/v4_human_source_dataset_receipt_v1.json",
        "data/projects/open_model_data/study/v4_learning_study_recipe_v1.json",
        "data/projects/open_model_data/study/v4_learning_study_execution_runs_v1.jsonl",
        "data/projects/open_model_data/study/v4_learning_study_receipt_v1.json",
        "docs/projects/ukrainian-data-foundry-evidence/HUMAN_SOURCE_DATASET_CARD.md",
        "docs/projects/ukrainian-data-foundry-evidence/HUMAN_SOURCE_TECHNICAL_REPORT.md",
        "docs/projects/ukrainian-data-foundry-evidence/RESEARCH_SUMMARY.md",
        "data/projects/open_model_data/delivery/v4_delivery_reproduction_receipt_v1.json",
    ]:
        src = Path.cwd() / subpath
        dst = mock_root / subpath
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    mock_receipt = mock_root / "data/projects/open_model_data/delivery/v4_delivery_reproduction_receipt_v1.json"
    rcpt_data = json.loads(mock_receipt.read_text(encoding="utf-8"))

    # 1. Traversal path with '..' is rejected
    rcpt_data["deliverable_documents"]["dataset_card"] = "../../../tmp/file.md"
    mock_receipt.write_text(json.dumps(rcpt_data, indent=2), encoding="utf-8")
    assert verify_delivery(mock_root, mock_receipt) is False

    # 2. Absolute path is rejected
    rcpt_data["deliverable_documents"]["dataset_card"] = "/etc/passwd"
    mock_receipt.write_text(json.dumps(rcpt_data, indent=2), encoding="utf-8")
    assert verify_delivery(mock_root, mock_receipt) is False
