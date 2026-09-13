"""Unit and contract tests for ULDR Phase 3.0: Pre-Extraction Partition Firewall & Source Custody (#8005)."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.projects.open_model_data.phase3_decolonization_partition import (
    exact_clopper_pearson_upper,
    verify_manifest,
)

CONTRACTS_DIR = REPO_ROOT / "data" / "projects" / "open_model_data" / "contracts"
PARTITIONS_DIR = REPO_ROOT / "data" / "projects" / "open_model_data" / "decolonization" / "partitions"

MANIFEST_SCHEMA_PATH = CONTRACTS_DIR / "v1_decolonization_partition_manifest.schema.json"
MANIFEST_FILE = PARTITIONS_DIR / "decolonization_partition_manifest.json"
TRAIN_CUSTODY_FILE = PARTITIONS_DIR / "train_source_custody.json"
HELDOUT_SUITE_FILE = PARTITIONS_DIR / "heldout_evaluation_suite_1000.jsonl"
MINHASH_REPORT_FILE = PARTITIONS_DIR / "minhash_dedup_summary.json"


@pytest.fixture(scope="module")
def manifest_schema() -> dict:
    assert MANIFEST_SCHEMA_PATH.is_file(), f"Missing schema: {MANIFEST_SCHEMA_PATH}"
    with MANIFEST_SCHEMA_PATH.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    jsonschema.Draft202012Validator.check_schema(schema)
    return schema


def test_partition_manifest_integrity(manifest_schema: dict) -> None:
    """Verify partition manifest matches Draft2020-12 schema and files match exact SHA-256."""
    assert MANIFEST_FILE.is_file(), f"Missing manifest: {MANIFEST_FILE}"
    with MANIFEST_FILE.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    # 1. Schema Validation
    validator = jsonschema.Draft202012Validator(manifest_schema)
    errors = list(validator.iter_errors(manifest))
    assert not errors, f"Manifest schema errors: {[e.message for e in errors]}"

    # 2. Metadata Invariants
    assert manifest["schema_version"] == "v1_decolonization_partition_manifest"
    assert manifest["issue"] == 8005
    assert manifest["parent_epic"] == 6321

    # 3. File existence and cryptographic SHA-256 validation
    for key, fmeta in manifest["files"].items():
        fpath = PARTITIONS_DIR / fmeta["filename"]
        assert fpath.is_file(), f"Missing artifact file: {fpath}"
        actual_sha = hashlib.sha256(fpath.read_bytes()).hexdigest()
        assert actual_sha == fmeta["sha256"], f"SHA256 mismatch for {key}: expected {fmeta['sha256']}, got {actual_sha}"


def test_source_custody_invariants() -> None:
    """Verify custody rules: UA-GEC test protected, ZNO and style-guide Train-only."""
    with MANIFEST_FILE.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    custody = manifest["source_custody_summary"]
    # UA-GEC test split must be explicitly excluded
    assert custody["ua_gec_excluded_test_count"] == 1159
    assert custody["ua_gec_train_documents_count"] > 0
    assert custody["ua_gec_heldout_documents_count"] > 0

    # Pretraining Contamination Defense: ZNO and style guide 100% Train-only
    assert custody["zno_tasks_train_only_count"] == 1646
    assert custody["style_guide_train_only_count"] == 342

    # Textbooks partitioned
    assert custody["textbook_train_chunks_count"] > 30000
    assert custody["textbook_heldout_chunks_count"] > 5000


def test_phenomenon_derivational_closure_zero_leakage() -> None:
    """Verify phenomenon-level partitioning and strict zero derivational family leakage."""
    with MANIFEST_FILE.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    p_summary = manifest["phenomenon_partition_summary"]
    assert p_summary["total_phenomena_count"] > 0
    assert p_summary["train_phenomena_count"] > 0
    assert p_summary["heldout_unseen_phenomena_count"] > 0
    # Mandatory Acceptance Criterion: Zero lemma/root family leakage
    assert p_summary["lemma_family_leakage_count"] == 0


def test_minhash_near_duplicate_zero_collisions() -> None:
    """Verify MinHash / token Jaccard deduplication report has zero pairs >= 0.80 similarity."""
    assert MINHASH_REPORT_FILE.is_file(), f"Missing MinHash report: {MINHASH_REPORT_FILE}"
    with MINHASH_REPORT_FILE.open("r", encoding="utf-8") as f:
        report = json.load(f)

    assert report["similarity_threshold"] == 0.80
    assert report["cross_split_duplicates_above_threshold"] == 0
    assert report["max_cross_split_similarity"] < 0.80
    assert report["status"] == "PASS"


def test_heldout_suite_exact_allocation_and_statistical_power() -> None:
    """Verify held-out suite has exactly 600 PRESERVE + 400 CORRECT cases and HER <= 1.0% power."""
    assert HELDOUT_SUITE_FILE.is_file(), f"Missing held-out suite: {HELDOUT_SUITE_FILE}"

    cases = []
    with HELDOUT_SUITE_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line.strip()))

    assert len(cases) == 1000

    preserve_cases = [c for c in cases if c["case_type"] == "PRESERVE"]
    correct_cases = [c for c in cases if c["case_type"] == "CORRECT"]

    assert len(preserve_cases) == 600
    assert len(correct_cases) == 400

    # Verify required fields on all cases
    for c in cases:
        assert "eval_id" in c
        assert "case_type" in c
        assert "input_text" in c
        assert "target_term" in c
        assert "expected_action" in c
        assert "phenomenon_category" in c
        assert "source_metadata" in c
        assert "derivational_family" in c

        if c["case_type"] == "PRESERVE":
            assert c["expected_action"] == "PRESERVE"
            assert c["expected_replacement"] is None
        else:
            assert c["expected_action"] == "CORRECT"
            assert c["expected_replacement"] is not None

    # Verify statistical power: exact one-sided 95% binomial upper bound for k=1 in n=600
    bound = exact_clopper_pearson_upper(1, 600, confidence=0.95)
    assert bound < 0.010, f"Statistical bound {bound} does not satisfy HER <= 1.0% gate"


def test_partition_cli_verify_only() -> None:
    """Verify that verify_manifest function returns True on disk artifacts."""
    assert verify_manifest(PARTITIONS_DIR) is True
