"""Tests for the complete private human-source dataset denominator and coverage audit (Issue #7432)."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from scripts.projects.open_model_data.v4_human_source_dataset import (
    OPERATOR_EXCLUDED_RESIDUALS,
    assert_no_private_host_paths,
    build_dataset,
    load_dataset_stream,
    load_partition_view,
    resolve_record_loss_masks,
    resolve_record_text,
    verify_dataset,
)

CONTRACTS_DIR = Path("data/projects/open_model_data/contracts")
DATASET_DIR = Path("data/projects/open_model_data/dataset")
MANIFEST_PATH = DATASET_DIR / "v4_human_source_dataset_manifest_v1.json"
RECEIPT_PATH = DATASET_DIR / "v4_human_source_dataset_receipt_v1.json"
RECORDS_PATH = DATASET_DIR / "v4_human_source_dataset_records_v1.jsonl"


def test_schema_contracts_valid() -> None:
    """The 3 JSON schemas for dataset manifest, record, and receipt must be valid Draft 2020-12 schemas."""
    for schema_name in [
        "v4_human_source_dataset_manifest_v1.schema.json",
        "v4_human_source_dataset_record_v1.schema.json",
        "v4_human_source_dataset_receipt_v1.schema.json",
    ]:
        p = CONTRACTS_DIR / schema_name
        assert p.is_file(), f"Missing schema contract: {p}"
        schema_data = json.loads(p.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema_data)


def test_manifest_denominator_accounting() -> None:
    """Check explicit denominator accounting and residual tracking (SCALE-1 & SCALE-2)."""
    assert MANIFEST_PATH.is_file(), f"Missing manifest: {MANIFEST_PATH}"
    manifest_data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest_data["schema_version"] == "v4_human_source_dataset_manifest_v1"
    assert manifest_data["dataset_version"] == "v4.0.0-human-pilot-scale"

    acct = manifest_data["denominator_accounting"]
    assert acct["total_holdings_sources"] == 16
    assert acct["total_selected_sources"] == 3
    assert acct["total_work_families"] == 3
    assert acct["total_evaluated_spans"] == 1419
    assert acct["total_admitted_spans"] == 1418
    assert acct["exported_training_spans"] == 614
    assert acct["firewalled_heldout_evaluation_spans"] == 559
    assert acct["development_spans"] == 245
    assert acct["quarantined_spans"] == 1

    strata = acct["strata_coverage"]
    assert strata["literary_prose"] == "covered"
    assert strata["educational_textbook"] == "covered"
    assert strata["stem_technical"] == "residual_operator_excluded"
    assert strata["video_captions"] == "residual_operator_excluded"
    assert strata["ocr_scans"] == "residual_operator_excluded"
    assert strata["private_teaching_material"] == "residual_operator_excluded"

    assert acct["operator_excluded_residuals"] == OPERATOR_EXCLUDED_RESIDUALS


def test_dataset_receipt_and_storage_accounting() -> None:
    """Verify receipt accounting, deduplication yield, and storage limits (SCALE-4 & SCALE-5)."""
    assert RECEIPT_PATH.is_file(), f"Missing receipt: {RECEIPT_PATH}"
    receipt_data = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
    assert receipt_data["verdict"] == "DATASET_CONFIRMED"
    assert receipt_data["dataset_version"] == "v4.0.0-human-pilot-scale"

    acct = receipt_data["dataset_accounting"]
    assert acct["total_evaluated_spans"] == 1419
    assert acct["total_admitted_spans"] == 1418
    assert acct["exported_training_spans"] == 614
    assert acct["firewalled_heldout_evaluation_spans"] == 559
    assert acct["development_spans"] == 245
    assert acct["rejected_quarantine_spans"] == 1
    assert acct["silent_drops"] == 0

    dedup = receipt_data["deduplication_yield"]
    assert dedup["unique_spans_count"] == 1419
    assert dedup["duplicate_spans_count"] == 0
    assert dedup["deduplication_rate"] == 1.0

    storage = receipt_data["storage_accounting"]
    assert storage["below_2000kb_precommit_limit"] is True
    assert storage["records_byte_size"] < 2000 * 1024

    assert receipt_data["frozen_for_downstream"]["open_weight_learning_study_issue"] == 7889
    assert receipt_data["frozen_for_downstream"]["deliverable_reproduction_issue"] == 7433


def test_dataset_record_fidelity_and_invariants() -> None:
    """Verify individual records satisfy verbatim preservation and privacy invariants (SCALE-3)."""
    assert RECORDS_PATH.is_file(), f"Missing records: {RECORDS_PATH}"
    with RECORDS_PATH.open("r", encoding="utf-8") as f:
        header = json.loads(f.readline())
        assert header["schema_version"] == "v4_human_source_dataset_records_v1"
        assert header["records"] == 1419

        sample_count = 0
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue
            rec = json.loads(line_str)
            assert rec["schema_version"] == "v4_human_source_dataset_record_v1"
            assert rec["record_id"].startswith("record.human.")
            assert rec["source_fidelity"]["is_native_text"] is True
            assert rec["source_fidelity"]["verbatim_preserved"] is True
            assert rec["admission_evidence"]["firewall_verified"] is True
            sample_count += 1

        assert sample_count == 1419


def test_privacy_host_paths_clean() -> None:
    """Ensure zero private host paths exist in any public dataset artifact."""
    manifest_data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert_no_private_host_paths(manifest_data)

    receipt_data = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
    assert_no_private_host_paths(receipt_data)

    with pytest.raises(ValueError, match="Prohibited host path detected"):
        assert_no_private_host_paths({"bad": "/home/ops/secret"})


def test_verify_dataset_clean_pass() -> None:
    """The verify_dataset function must return True on intact artifacts."""
    assert verify_dataset(Path.cwd()) is True


def test_build_dataset_atomic_prewrite_validation_on_denominator_mismatch(tmp_path: Path) -> None:
    """Denominator discrepancy must raise ValueError before writing files, leaving targets untouched."""
    repo_root = Path.cwd()
    fake_repo = tmp_path / "repo"
    fake_repo.mkdir(parents=True)

    # Recreate input paths in fake_repo
    contracts_target = fake_repo / "data/projects/open_model_data/contracts"
    contracts_target.parent.mkdir(parents=True, exist_ok=True)
    contracts_target.symlink_to((repo_root / CONTRACTS_DIR).resolve())

    for dir_name in ["language", "extraction", "provenance", "pilot"]:
        target = fake_repo / f"data/projects/open_model_data/{dir_name}"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to((repo_root / f"data/projects/open_model_data/{dir_name}").resolve())

    splits_dir = fake_repo / "data/projects/open_model_data/splits"
    splits_dir.mkdir(parents=True, exist_ok=True)
    (splits_dir / "v4_work_grouping_split_receipt_v1.json").symlink_to(
        (repo_root / "data/projects/open_model_data/splits/v4_work_grouping_split_receipt_v1.json").resolve()
    )

    # Create split_index with one line missing to create an intentional denominator mismatch
    src_split_index = repo_root / "data/projects/open_model_data/splits/v4_work_grouping_split_index_v1.jsonl"
    lines = src_split_index.read_text(encoding="utf-8").splitlines()
    truncated_lines = [lines[0], *lines[2:]]  # drop line 1 (1 span omitted)
    (splits_dir / "v4_work_grouping_split_index_v1.jsonl").write_text(
        "\n".join(truncated_lines) + "\n", encoding="utf-8"
    )

    out_dir = tmp_path / "out"
    out_dir.mkdir(parents=True)
    test_manifest_out = out_dir / "manifest.json"
    test_records_out = out_dir / "records.jsonl"
    test_receipt_out = out_dir / "receipt.json"

    # Pre-populate sentinel content
    test_manifest_out.write_text("sentinel manifest", encoding="utf-8")
    test_records_out.write_text("sentinel records", encoding="utf-8")
    test_receipt_out.write_text("sentinel receipt", encoding="utf-8")

    with pytest.raises(ValueError, match="Evaluated spans 1418 does not match manifest 1419"):
        build_dataset(fake_repo, test_manifest_out, test_records_out, test_receipt_out)

    # Verify target files were NOT overwritten
    assert test_manifest_out.read_text(encoding="utf-8") == "sentinel manifest"
    assert test_records_out.read_text(encoding="utf-8") == "sentinel records"
    assert test_receipt_out.read_text(encoding="utf-8") == "sentinel receipt"

    # Verify no temporary files were leaked
    tmp_files = list(out_dir.glob("*.tmp*"))
    assert tmp_files == []


def test_build_dataset_transactional_rollback_on_replacement_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If an error occurs during atomic replacement, all target files roll back to previous state."""
    repo_root = Path.cwd()
    out_dir = tmp_path / "out"
    out_dir.mkdir(parents=True)
    test_manifest_out = out_dir / "manifest.json"
    test_records_out = out_dir / "records.jsonl"
    test_receipt_out = out_dir / "receipt.json"

    # Pre-populate sentinel content
    test_manifest_out.write_text("sentinel manifest", encoding="utf-8")
    test_records_out.write_text("sentinel records", encoding="utf-8")
    test_receipt_out.write_text("sentinel receipt", encoding="utf-8")

    orig_replace = Path.replace

    def mock_replace(self: Path, target: Path | str) -> Path:
        target_path = Path(target)
        if target_path.name == "receipt.json" and ".tmp." in self.name:
            raise OSError("Simulated disk error during receipt replacement")
        return orig_replace(self, target)

    monkeypatch.setattr(Path, "replace", mock_replace)

    with pytest.raises(OSError, match="Simulated disk error"):
        build_dataset(repo_root, test_manifest_out, test_records_out, test_receipt_out)

    # All targets must have rolled back to sentinel contents
    assert test_manifest_out.read_text(encoding="utf-8") == "sentinel manifest"
    assert test_records_out.read_text(encoding="utf-8") == "sentinel records"
    assert test_receipt_out.read_text(encoding="utf-8") == "sentinel receipt"

    # No stray tmp or backup files remain
    assert list(out_dir.glob("*.tmp*")) == []
    assert list(out_dir.glob("*.bak*")) == []


def test_authenticated_loss_mask_resolver() -> None:
    """Verify that resolve_record_loss_masks and load_dataset_stream resolve modern_view loss masks."""
    records = list(load_dataset_stream(RECORDS_PATH, resolve_masks=True))
    assert len(records) == 1419

    # Verify first record
    rec0 = records[0]
    m0 = rec0["language_views"]["modern_view"]
    assert "loss_mask_spans" in m0
    assert len(m0["loss_mask_spans"]) == m0["loss_mask_count"]
    for span in m0["loss_mask_spans"]:
        assert "start_char" in span
        assert "end_char" in span
        assert "reason" in span
        assert span["start_char"] <= span["end_char"]

    # Verify partition loading with resolved modern_view loss masks
    training_resolved = load_partition_view(RECORDS_PATH, "training", resolve_masks=True)
    assert len(training_resolved) == 614
    assert "loss_mask_spans" in training_resolved[0]["language_views"]["modern_view"]

    # Verify direct resolution on raw record dict
    with open(RECORDS_PATH, encoding="utf-8") as f:
        _ = f.readline()  # skip header
        raw_line = f.readline()
    rec_raw = json.loads(raw_line)
    resolved_masks = resolve_record_loss_masks(rec_raw)
    assert resolved_masks == m0["loss_mask_spans"]

    # Test error handling on missing sha or mismatched count
    with pytest.raises(ValueError, match=r"Record is missing source_fidelity\.span_sha256"):
        resolve_record_loss_masks({})

    tampered_rec = dict(rec_raw)
    tampered_rec["language_views"] = {"modern_view": {"loss_mask_count": 999999}}
    with pytest.raises(ValueError, match=r"does not match record loss_mask_count"):
        resolve_record_loss_masks(tampered_rec)


def test_authenticated_source_text_resolver() -> None:
    """Verify that resolve_record_text and load_dataset_stream resolve private source text."""
    import hashlib

    records = list(load_dataset_stream(RECORDS_PATH, resolve_masks=True, resolve_text=True))
    assert len(records) == 1419

    rec0 = records[0]
    assert "text" in rec0
    assert "text" in rec0["source_fidelity"]
    assert len(rec0["text"]) == rec0["source_fidelity"]["char_length"]
    assert hashlib.sha256(rec0["text"].encode("utf-8")).hexdigest() == rec0["source_fidelity"]["span_sha256"]

    # Verify direct resolution
    with open(RECORDS_PATH, encoding="utf-8") as f:
        _ = f.readline()
        raw_line = f.readline()
    rec_raw = json.loads(raw_line)
    resolved_text = resolve_record_text(rec_raw)
    assert resolved_text == rec0["text"]

    # Test error handling on missing sha or tampered sha
    with pytest.raises(ValueError, match=r"Record is missing source_fidelity\.span_sha256"):
        resolve_record_text({})

    tampered_rec = dict(rec_raw)
    tampered_rec["source_fidelity"] = dict(rec_raw["source_fidelity"])
    tampered_rec["source_fidelity"]["span_sha256"] = "0000000000000000000000000000000000000000000000000000000000000000"
    with pytest.raises(KeyError, match=r"not found in authenticated extraction index"):
        resolve_record_text(tampered_rec)


def test_validate_mask_span_schema_and_interval_bounds() -> None:
    """Verify that validate_mask_span rejects missing required fields and invalid interval bounds."""
    from scripts.projects.open_model_data.v4_human_source_dataset import validate_mask_span

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


def test_persisted_records_reject_preexisting_raw_text(tmp_path: Path) -> None:
    """Ensure load_dataset_stream and verify_dataset reject persisted records containing raw text."""
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

    bad_record2 = {
        "schema_version": "v4_human_source_dataset_record_v1",
        "record_id": "record.human.test12345678901235",
        "source_fidelity": {"text": "Private text in fidelity"},
    }
    bad_records_file.write_text("# header\n" + json.dumps(bad_record2) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="contains raw text"):
        next(load_dataset_stream(bad_records_file, resolve_masks=False, resolve_text=False))


def test_record_schema_forbids_raw_text() -> None:
    """Ensure v4_human_source_dataset_record_v1 schema rejects raw text property."""
    import jsonschema

    schema_path = CONTRACTS_DIR / "v4_human_source_dataset_record_v1.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    # Valid base record without text
    with open(RECORDS_PATH, encoding="utf-8") as f:
        _ = f.readline()
        record = json.loads(f.readline())

    jsonschema.validate(instance=record, schema=schema)

    # Adding raw text at root must fail schema validation
    rec_with_text = dict(record)
    rec_with_text["text"] = "Sample corpus text"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=rec_with_text, schema=schema)

    # Adding raw text under source_fidelity must fail schema validation
    rec_with_fidelity_text = dict(record)
    rec_with_fidelity_text["source_fidelity"] = dict(record["source_fidelity"])
    rec_with_fidelity_text["source_fidelity"]["text"] = "Sample corpus text"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=rec_with_fidelity_text, schema=schema)
