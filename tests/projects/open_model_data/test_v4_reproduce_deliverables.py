"""Tests for final private dataset and learning-study deliverables reproduction (Issue #7433)."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import jsonschema
import pytest

from scripts.projects.open_model_data.v4_reproduce_deliverables import (
    _get_language_usage_masks,
    assert_file_no_private_host_paths,
    assert_no_private_host_paths,
    build_delivery_receipt,
    clear_caches,
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


def _has_full_sources_db() -> bool:
    candidates = [Path("data/sources.db"), Path.cwd() / "data/sources.db"]
    for p in [Path.cwd(), *Path.cwd().parents]:
        candidates.append(p / "data/sources.db")
    for cand in candidates:
        if cand.is_file():
            try:
                conn = sqlite3.connect(f"file:{cand.resolve()}?mode=ro", uri=True)
                cur = conn.cursor()
                cur.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('literary_texts', 'textbooks')"
                )
                tables = {row[0] for row in cur.fetchall()}
                conn.close()
                if "literary_texts" in tables and "textbooks" in tables:
                    return True
            except Exception:
                pass
    return False


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
    if not _has_full_sources_db():
        pytest.skip("Full data/sources.db with literary_texts/textbooks not available in test runner environment")

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
    receipt["dataset_reproduction"]["manifest_sha256"] = (
        "0000000000000000000000000000000000000000000000000000000000000000"
    )
    tampered_receipt = tmp_path / "tampered_receipt.json"
    tampered_receipt.write_text(json.dumps(receipt), encoding="utf-8")
    assert verify_delivery(Path.cwd(), tampered_receipt) is False

    # Modified receipt with mismatched runs digest fails verification
    receipt2 = json.loads(DELIVERY_RECEIPT_PATH.read_text(encoding="utf-8"))
    receipt2["learning_study_reproduction"]["runs_sha256"] = (
        "0000000000000000000000000000000000000000000000000000000000000000"
    )
    tampered_receipt2 = tmp_path / "tampered_receipt2.json"
    tampered_receipt2.write_text(json.dumps(receipt2), encoding="utf-8")
    assert verify_delivery(Path.cwd(), tampered_receipt2) is False

    # Modified receipt with mismatched document digest fails verification
    receipt3 = json.loads(DELIVERY_RECEIPT_PATH.read_text(encoding="utf-8"))
    receipt3["document_digests"]["dataset_card_sha256"] = (
        "0000000000000000000000000000000000000000000000000000000000000000"
    )
    tampered_receipt3 = tmp_path / "tampered_receipt3.json"
    tampered_receipt3.write_text(json.dumps(receipt3), encoding="utf-8")
    assert verify_delivery(Path.cwd(), tampered_receipt3) is False

    # Modified receipt with mismatched language usage index digest fails verification
    receipt4 = json.loads(DELIVERY_RECEIPT_PATH.read_text(encoding="utf-8"))
    receipt4["dataset_reproduction"]["language_usage_index_sha256"] = (
        "0000000000000000000000000000000000000000000000000000000000000000"
    )
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
    study_runs.write_text(
        orig_runs
        + '{"run_id": "run.999", "recipe_id": "recipe.v4.learning.open_weight_pilot.20260910", "seed": 42, "path": "/workspace/checkout"}\n',
        encoding="utf-8",
    )
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


def test_validate_mask_span_schema_and_interval_bounds() -> None:
    """Verify that validate_mask_span rejects missing required fields and invalid interval bounds."""
    from scripts.projects.open_model_data.v4_reproduce_deliverables import validate_mask_span

    # Valid mask span
    valid_span = {"start_char": 10, "end_char": 25, "reason": "historical_period"}
    assert validate_mask_span(valid_span, char_len=50) is True

    # Reject empty dict
    assert validate_mask_span({}, char_len=50) is False

    # Reject missing reason
    assert validate_mask_span({"start_char": 10, "end_char": 25}, char_len=50) is False
    assert validate_mask_span({"start_char": 10, "end_char": 25, "reason": ""}, char_len=50) is False

    # Reject missing start_char or end_char
    assert validate_mask_span({"end_char": 25, "reason": "historical_period"}, char_len=50) is False
    assert validate_mask_span({"start_char": 10, "reason": "historical_period"}, char_len=50) is False

    # Reject non-integer or boolean coordinates
    assert validate_mask_span({"start_char": True, "end_char": 25, "reason": "historical_period"}, char_len=50) is False
    assert validate_mask_span({"start_char": "10", "end_char": 25, "reason": "historical_period"}, char_len=50) is False
    assert validate_mask_span({"start_char": -1, "end_char": 25, "reason": "historical_period"}, char_len=50) is False

    # Reject inverted interval (start > end)
    assert validate_mask_span({"start_char": 30, "end_char": 20, "reason": "historical_period"}, char_len=50) is False

    # Reject end_char exceeding record char_length
    assert validate_mask_span({"start_char": 10, "end_char": 60, "reason": "historical_period"}, char_len=50) is False

    # Reject unexpected extra fields (additionalProperties: False)
    assert (
        validate_mask_span(
            {"start_char": 10, "end_char": 25, "reason": "historical_period", "extra": "field"},
            char_len=50,
        )
        is False
    )


def test_assert_file_no_private_host_paths_detects_unicode_escaped_paths(tmp_path: Path) -> None:
    """Ensure unicode-escaped host paths in json and jsonl files are caught and rejected."""
    # JSON file with unicode-escaped slash: \u002fworkspace\u002frepo
    json_file = tmp_path / "escaped.json"
    json_file.write_text('{"target_dir": "\\u002fworkspace\\u002frepo"}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="Prohibited host path detected"):
        assert_file_no_private_host_paths(json_file, "escaped.json")

    # JSONL file with unicode-escaped /home path
    jsonl_file = tmp_path / "escaped.jsonl"
    jsonl_file.write_text('{"entry": 1, "path": "\\u002fhome\\u002fuser\\u002fdata"}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="Prohibited host path detected"):
        assert_file_no_private_host_paths(jsonl_file, "escaped.jsonl")


def test_persisted_records_reject_preexisting_raw_text(tmp_path: Path) -> None:
    """Ensure load_dataset_stream and verify_delivery reject persisted records containing raw text."""
    # Write a test records jsonl with raw text
    bad_records_file = tmp_path / "bad_records.jsonl"
    bad_record = {
        "schema_version": "v4_human_source_dataset_record_v1",
        "record_id": "record.human.test12345678901234",
        "source_id": "source.literary.test",
        "text": "Private corpus text directly serialized",
    }
    bad_records_file.write_text("# header\n" + json.dumps(bad_record) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="contains raw text"):
        next(load_dataset_stream(bad_records_file, resolve_masks=False, resolve_text=False))

    # Also test text under source_fidelity
    bad_record2 = {
        "schema_version": "v4_human_source_dataset_record_v1",
        "record_id": "record.human.test12345678901235",
        "source_fidelity": {"text": "Private text in fidelity"},
    }
    bad_records_file.write_text("# header\n" + json.dumps(bad_record2) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="contains raw text"):
        next(load_dataset_stream(bad_records_file, resolve_masks=False, resolve_text=False))


def test_mock_delivery_stream_loader_with_text(tmp_path: Path) -> None:
    """Verify stream loading and partition filtering with text in mock environment (runs in CI)."""
    fake_repo = tmp_path / "fake_repo"
    fake_repo.mkdir()

    # 1. Create mock sqlite DB
    mock_db = tmp_path / "mock_sources.db"
    conn = sqlite3.connect(str(mock_db))
    cur = conn.cursor()
    cur.execute("CREATE TABLE literary_texts (source_file TEXT, chunk_id INTEGER, text TEXT)")
    cur.execute("CREATE TABLE textbooks (source_file TEXT, chunk_id INTEGER, text TEXT)")
    sample_text = "Тестовий український текст для перевірки динамічного завантаження."
    sample_sha = hashlib.sha256(sample_text.encode("utf-8")).hexdigest()
    sample_len = len(sample_text)
    cur.execute(
        "INSERT INTO textbooks (source_file, chunk_id, text) VALUES (?, ?, ?)",
        ("tb_sample.txt", 10, sample_text),
    )
    conn.commit()
    conn.close()

    # 2. Create mock extraction index
    ext_dir = fake_repo / "data/projects/open_model_data/extraction"
    ext_dir.mkdir(parents=True)
    ext_file = ext_dir / "v4_native_extraction_index_v1.jsonl"
    ext_entry = {
        "extraction_id": "ext.test.1",
        "source_file": "tb_sample.txt",
        "chunk_id": 10,
        "source_family": "textbook",
        "span_locator": {"span_sha256": sample_sha},
    }
    ext_file.write_text("# header\n" + json.dumps(ext_entry) + "\n", encoding="utf-8")

    # 3. Create mock record
    mock_rec = {
        "schema_version": "v4_human_source_dataset_record_v1",
        "record_id": "record.human.test_tb_1",
        "source_id": "source.textbook.test",
        "split_clearance": {
            "split_partition": "training",
            "builder_training_cleared": True,
        },
        "source_fidelity": {
            "char_length": sample_len,
            "span_sha256": sample_sha,
            "is_native_text": True,
            "verbatim_preserved": True,
        },
    }

    rec_file = tmp_path / "mock_records.jsonl"
    rec_file.write_text("# header\n" + json.dumps(mock_rec) + "\n", encoding="utf-8")

    stream_records = list(
        load_dataset_stream(rec_file, resolve_text=True, repo_root=fake_repo, sources_db_path=mock_db)
    )
    assert len(stream_records) == 1
    assert stream_records[0]["text"] == sample_text

    part_records = load_partition_view(
        rec_file, "training", resolve_text=True, repo_root=fake_repo, sources_db_path=mock_db
    )
    assert len(part_records) == 1
    assert part_records[0]["text"] == sample_text


def _setup_fake_repo_with_records(tmp_path: Path, records_content: str) -> tuple[Path, Path]:
    repo_root = Path.cwd()
    fake_repo = tmp_path / "repo"
    fake_repo.mkdir(parents=True, exist_ok=True)

    # Symlink docs
    (fake_repo / "docs").symlink_to((repo_root / "docs").resolve())

    # Symlink shared open_model_data directories
    data_omd = fake_repo / "data/projects/open_model_data"
    data_omd.mkdir(parents=True, exist_ok=True)
    for sub in ["contracts", "study", "language", "extraction", "delivery"]:
        (data_omd / sub).symlink_to((repo_root / "data/projects/open_model_data" / sub).resolve())

    # Setup dataset dir with symlinked manifest & receipt, and custom records file
    dataset_dir = data_omd / "dataset"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    (dataset_dir / "v4_human_source_dataset_manifest_v1.json").symlink_to(
        (repo_root / "data/projects/open_model_data/dataset/v4_human_source_dataset_manifest_v1.json").resolve()
    )
    (dataset_dir / "v4_human_source_dataset_receipt_v1.json").symlink_to(
        (repo_root / "data/projects/open_model_data/dataset/v4_human_source_dataset_receipt_v1.json").resolve()
    )

    custom_records = dataset_dir / "v4_human_source_dataset_records_v1.jsonl"
    custom_records.write_text(records_content, encoding="utf-8")

    from scripts.projects.open_model_data.v4_reproduce_deliverables import sha256_file

    receipt_data = json.loads(DELIVERY_RECEIPT_PATH.read_text(encoding="utf-8"))
    receipt_data["dataset_reproduction"]["records_sha256"] = sha256_file(custom_records)
    fake_receipt = tmp_path / "test_delivery_receipt.json"
    fake_receipt.write_text(json.dumps(receipt_data), encoding="utf-8")

    return fake_repo, fake_receipt


def test_verify_delivery_rejects_schema_violating_record(tmp_path: Path) -> None:
    """Verify that verify_delivery and build_delivery_receipt reject records violating schema contract (Finding 1)."""
    with open(RECORDS_PATH, encoding="utf-8") as f:
        header = f.readline()
        lines = [f.readline() for _ in range(1419)]

    rec1 = json.loads(lines[0])
    rec1_bad = dict(rec1)
    rec1_bad["admission_evidence"] = dict(rec1["admission_evidence"])
    rec1_bad["admission_evidence"]["firewall_verified"] = False  # Schema const: true

    bad_content = header + json.dumps(rec1_bad) + "\n" + "".join(lines[1:])
    fake_repo, fake_receipt = _setup_fake_repo_with_records(tmp_path, bad_content)

    assert verify_delivery(fake_repo, fake_receipt) is False

    with pytest.raises(ValueError, match=r"violates record schema"):
        build_delivery_receipt(fake_repo, tmp_path / "out_receipt.json")


def test_verify_delivery_rejects_duplicate_record_id_or_span_sha(tmp_path: Path) -> None:
    """Verify that verify_delivery and build_delivery_receipt reject duplicate records or span hashes (Finding 3)."""
    with open(RECORDS_PATH, encoding="utf-8") as f:
        header = f.readline()
        lines = [f.readline() for _ in range(1419)]

    rec1 = json.loads(lines[0])
    rec2 = json.loads(lines[1])

    # 1. Duplicate record_id
    rec2_bad_id = dict(rec2)
    rec2_bad_id["record_id"] = rec1["record_id"]
    dup_id_content = header + lines[0] + json.dumps(rec2_bad_id) + "\n" + "".join(lines[2:])
    fake_repo_id, fake_receipt_id = _setup_fake_repo_with_records(tmp_path / "dup_id", dup_id_content)
    assert verify_delivery(fake_repo_id, fake_receipt_id) is False
    with pytest.raises(ValueError, match=r"Duplicate or missing record_id"):
        build_delivery_receipt(fake_repo_id, tmp_path / "out_receipt1.json")

    # 2. Duplicate span_sha256
    rec2_bad_sha = dict(rec2)
    rec2_bad_sha["source_fidelity"] = dict(rec2["source_fidelity"])
    rec2_bad_sha["source_fidelity"]["span_sha256"] = rec1["source_fidelity"]["span_sha256"]
    dup_sha_content = header + lines[0] + json.dumps(rec2_bad_sha) + "\n" + "".join(lines[2:])
    fake_repo_sha, fake_receipt_sha = _setup_fake_repo_with_records(tmp_path / "dup_sha", dup_sha_content)
    assert verify_delivery(fake_repo_sha, fake_receipt_sha) is False
    with pytest.raises(ValueError, match=r"Duplicate or missing span_sha256"):
        build_delivery_receipt(fake_repo_sha, tmp_path / "out_receipt2.json")


def test_cache_refreshes_on_index_change(tmp_path: Path) -> None:
    """Verify that language usage cache dynamically reloads on content change without stale results (Finding 2)."""
    fake_repo = tmp_path / "fake_repo_cache"
    lang_dir = fake_repo / "data/projects/open_model_data/language"
    lang_dir.mkdir(parents=True)
    lang_file = lang_dir / "v4_language_usage_index_v1.jsonl"

    item1 = {
        "language_usage_id": "lu.1",
        "span_locator": {"span_sha256": "1111" * 16},
        "consumer_views": {"modern_view": {"loss_mask_spans": [{"start_char": 0, "end_char": 5, "reason": "dialect"}]}},
    }
    lang_file.write_text("# header\n" + json.dumps(item1) + "\n", encoding="utf-8")
    clear_caches()

    masks1 = _get_language_usage_masks(fake_repo)
    assert "1111" * 16 in masks1
    assert len(masks1["1111" * 16]) == 1

    # Modify file
    item2 = {
        "language_usage_id": "lu.2",
        "span_locator": {"span_sha256": "2222" * 16},
        "consumer_views": {
            "modern_view": {"loss_mask_spans": [{"start_char": 10, "end_char": 20, "reason": "foreign_citation"}]}
        },
    }
    lang_file.write_text("# header\n" + json.dumps(item1) + "\n" + json.dumps(item2) + "\n", encoding="utf-8")

    masks2 = _get_language_usage_masks(fake_repo)
    assert "2222" * 16 in masks2
    assert len(masks2["2222" * 16]) == 1
