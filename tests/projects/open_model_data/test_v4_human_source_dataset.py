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
    (splits_dir / "v4_work_grouping_split_index_v1.jsonl").write_text("\n".join(truncated_lines) + "\n", encoding="utf-8")

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
