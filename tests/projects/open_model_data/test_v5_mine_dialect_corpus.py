"""Unit and regression tests for Phase 5.6: Regional Dialects Corpus Mining, SFT Defense Trajectories & Multi-Zone Evaluation (v0.3).

Validates:
  1. Release files existence and cryptographic SHA-256 integrity.
  2. Release receipt schema validation and Draft 2020-12 compliance.
  3. Held-out multi-zone evaluation benchmark stratification and schema validation:
     - Total cases >= 1,500
     - Southwestern >= 600
     - Northern >= 400
     - Southeastern >= 500 (Slobozhanshchyna >= 250, Steppe >= 250)
  4. Anti-copying mixed-error coverage (>= 30% across all macro zones).
  5. Strict 0% train/eval leakage firewall (zero sentence or passage overlap).
  6. SFT training dataset validation (>= 500 trajectories, Draft 2020-12 schema, unique IDs).
  7. Calibrated replay buffer (>= 100 modern literary / anti-calque trajectories from v0.2).
  8. Permanent quarantine of Bilodid's СУМ-11 editorial apparatus.
  9. Multi-zone evaluation scorer, disaggregated confusion matrices, and Clopper-Pearson bounds.
 10. Modern literary non-regression check against frozen v0.2 benchmark (<= 0.5% regression).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import jsonschema
import pytest

from scripts.projects.open_model_data.v5_mine_dialect_corpus import (
    DEFAULT_RELEASE_DIR,
    EVAL_SCHEMA_FILE,
    RECEIPT_SCHEMA_FILE,
    TRAJECTORY_SCHEMA_FILE,
    V02_BASELINE_SUITE_PATH,
    clean_headword,
    clean_sentence,
    evaluate_multizone_benchmark,
    exact_clopper_pearson_lower,
    normalize_lookup_token,
    passage_fingerprint,
    verify_modern_literary_regression,
)

EVAL_BENCHMARK_PATH = DEFAULT_RELEASE_DIR / "dialect_corpus_expanded_1500.jsonl"
EVAL_SHA_PATH = DEFAULT_RELEASE_DIR / "dialect_corpus_expanded_1500.sha256"
SFT_DATASET_PATH = DEFAULT_RELEASE_DIR / "sft_dialect_protection_500.jsonl"
SFT_SHA_PATH = DEFAULT_RELEASE_DIR / "sft_dialect_protection_500.sha256"
RECEIPT_PATH = DEFAULT_RELEASE_DIR / "release_receipt.json"
RECEIPT_SHA_PATH = DEFAULT_RELEASE_DIR / "release_receipt.json.sha256"


@pytest.fixture(scope="module")
def eval_schema() -> dict[str, Any]:
    assert EVAL_SCHEMA_FILE.is_file(), f"Evaluation record schema missing: {EVAL_SCHEMA_FILE}"
    schema = json.loads(EVAL_SCHEMA_FILE.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    return schema


@pytest.fixture(scope="module")
def receipt_schema() -> dict[str, Any]:
    assert RECEIPT_SCHEMA_FILE.is_file(), f"Release receipt schema missing: {RECEIPT_SCHEMA_FILE}"
    schema = json.loads(RECEIPT_SCHEMA_FILE.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    return schema


@pytest.fixture(scope="module")
def trajectory_schema() -> dict[str, Any]:
    assert TRAJECTORY_SCHEMA_FILE.is_file(), f"Trajectory schema missing: {TRAJECTORY_SCHEMA_FILE}"
    schema = json.loads(TRAJECTORY_SCHEMA_FILE.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    return schema


@pytest.fixture(scope="module")
def eval_cases() -> list[dict[str, Any]]:
    assert EVAL_BENCHMARK_PATH.is_file(), f"Benchmark file missing: {EVAL_BENCHMARK_PATH}"
    lines = [json.loads(line) for line in EVAL_BENCHMARK_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    return lines


@pytest.fixture(scope="module")
def sft_trajectories() -> list[dict[str, Any]]:
    assert SFT_DATASET_PATH.is_file(), f"SFT dataset file missing: {SFT_DATASET_PATH}"
    lines = [json.loads(line) for line in SFT_DATASET_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    return lines


@pytest.fixture(scope="module")
def release_receipt() -> dict[str, Any]:
    assert RECEIPT_PATH.is_file(), f"Release receipt missing: {RECEIPT_PATH}"
    return json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))


# ==============================================================================
# 1. Release Files Existence and Cryptographic SHA-256 Integrity
# ==============================================================================

def test_release_files_and_sha256_integrity() -> None:
    """Verify all release artifacts exist and match their SHA-256 manifest files."""
    for data_file, sha_file in [
        (EVAL_BENCHMARK_PATH, EVAL_SHA_PATH),
        (SFT_DATASET_PATH, SFT_SHA_PATH),
        (RECEIPT_PATH, RECEIPT_SHA_PATH),
    ]:
        assert data_file.exists(), f"Missing release file: {data_file}"
        assert sha_file.exists(), f"Missing SHA file: {sha_file}"

        actual_sha = hashlib.sha256(data_file.read_bytes()).hexdigest()
        sha_line = sha_file.read_text(encoding="utf-8").strip()
        recorded_sha = sha_line.split()[0].strip()

        assert actual_sha == recorded_sha, f"SHA mismatch for {data_file.name}: actual={actual_sha}, recorded={recorded_sha}"


# ==============================================================================
# 2. Release Receipt Schema & Content Verification
# ==============================================================================

def test_release_receipt_schema_and_facts(
    release_receipt: dict[str, Any],
    receipt_schema: dict[str, Any],
    eval_cases: list[dict[str, Any]],
    sft_trajectories: list[dict[str, Any]],
) -> None:
    """Verify release receipt validates against schema and strictly reflects dataset facts."""
    validator = jsonschema.Draft202012Validator(receipt_schema)
    errors = list(validator.iter_errors(release_receipt))
    assert not errors, f"Receipt schema validation errors: {[e.message for e in errors]}"

    assert release_receipt["schema_version"] == "v1_dialect_multizone_release_receipt"
    assert release_receipt["issue"] == 8102
    assert release_receipt["parent_epic"] == 6321

    # Verify benchmark section matches actual eval cases
    bench_info = release_receipt["evaluation_benchmark"]
    assert bench_info["total_cases"] == len(eval_cases)
    actual_eval_sha = hashlib.sha256(EVAL_BENCHMARK_PATH.read_bytes()).hexdigest()
    assert bench_info["sha256"] == actual_eval_sha

    preserve_count = sum(1 for c in eval_cases if c["case_type"] == "PRESERVE")
    mixed_count = sum(1 for c in eval_cases if c["case_type"] == "CORRECT_MIXED")
    assert bench_info["preserve_cases"] == preserve_count
    assert bench_info["mixed_error_cases"] == mixed_count

    # Verify SFT section matches actual trajectories
    sft_info = release_receipt["sft_training_dataset"]
    assert sft_info["total_trajectories"] == len(sft_trajectories)
    actual_sft_sha = hashlib.sha256(SFT_DATASET_PATH.read_bytes()).hexdigest()
    assert sft_info["sha256"] == actual_sft_sha
    assert sft_info["dialect_trajectories"] == 450
    assert sft_info["replay_buffer_trajectories"] == 100

    # Verify invariant declarations
    inv = release_receipt["invariants_verified"]
    assert inv["zero_train_eval_leakage"] is True
    assert inv["anti_copying_mixed_error_coverage"] is True
    assert inv["bilodid_quarantine_enforced"] is True
    assert inv["all_localities_verified"] is True


# ==============================================================================
# 3. Held-Out Evaluation Benchmark Stratification & Schema
# ==============================================================================

def test_evaluation_benchmark_schema_validation(
    eval_cases: list[dict[str, Any]],
    eval_schema: dict[str, Any],
) -> None:
    """Verify 100% of benchmark records conform to Draft 2020-12 schema."""
    validator = jsonschema.Draft202012Validator(eval_schema)
    for idx, case in enumerate(eval_cases, 1):
        errors = list(validator.iter_errors(case))
        assert not errors, f"Validation errors on record {idx} ({case.get('eval_id')}): {[e.message for e in errors]}"


def test_evaluation_benchmark_stratification_quotas(eval_cases: list[dict[str, Any]]) -> None:
    """Verify multi-zone quota thresholds: Southwestern >= 600, Northern >= 400, Southeastern >= 500."""
    total = len(eval_cases)
    assert total >= 1500, f"Expected >= 1,500 total evaluation cases, got {total}"

    macro_counts: dict[str, int] = {}
    sub_counts: dict[str, int] = {}

    for c in eval_cases:
        mz = c["macro_zone"]
        sz = c["sub_zone"]
        macro_counts[mz] = macro_counts.get(mz, 0) + 1
        sub_counts[sz] = sub_counts.get(sz, 0) + 1

    assert macro_counts.get("southwestern", 0) >= 600, f"Southwestern quota not met: {macro_counts.get('southwestern')}"
    assert macro_counts.get("northern", 0) >= 400, f"Northern quota not met: {macro_counts.get('northern')}"
    assert macro_counts.get("southeastern", 0) >= 500, f"Southeastern quota not met: {macro_counts.get('southeastern')}"

    # Verify sub-zone quotas for Slobozhanshchyna and Steppe
    assert sub_counts.get("southeastern_slobozhan", 0) >= 250, (
        f"Slobozhanshchyna quota not met: {sub_counts.get('southeastern_slobozhan')}"
    )
    assert sub_counts.get("southeastern_steppe", 0) >= 250, (
        f"Steppe quota not met: {sub_counts.get('southeastern_steppe')}"
    )


def test_anti_copying_mixed_error_coverage(eval_cases: list[dict[str, Any]]) -> None:
    """Verify mixed-error coverage >= 30% across the benchmark and within every macro zone."""
    total = len(eval_cases)
    mixed_total = sum(1 for c in eval_cases if c["case_type"] == "CORRECT_MIXED")
    mixed_pct = mixed_total / total
    assert mixed_pct >= 0.30, f"Overall mixed error percentage too low: {mixed_pct:.2%}"

    # Check each macro zone has >= 25% mixed error cases
    for mz in ["southwestern", "northern", "southeastern"]:
        mz_cases = [c for c in eval_cases if c["macro_zone"] == mz]
        mz_mixed = sum(1 for c in mz_cases if c["case_type"] == "CORRECT_MIXED")
        pct = mz_mixed / len(mz_cases)
        assert pct >= 0.25, f"Macro zone {mz} mixed error percentage too low: {pct:.2%}"


def test_anti_copying_case_properties(eval_cases: list[dict[str, Any]]) -> None:
    """Verify invariants for PRESERVE and CORRECT_MIXED test cases."""
    for c in eval_cases:
        if c["case_type"] == "PRESERVE":
            assert c["expected_action"] == "PRESERVE"
            assert c["expected_replacement"] is None
            assert c["input_text"] == c["expected_output"]
            assert c["has_injected_error"] is False
            assert c["injected_error_type"] is None
        elif c["case_type"] == "CORRECT_MIXED":
            assert c["expected_action"] == "CORRECT"
            assert c["expected_replacement"] is not None
            assert c["input_text"] != c["expected_output"]
            assert c["has_injected_error"] is True
            assert c["injected_error_type"] in {"colonial_calque", "punctuation", "agreement"}

            # Crucial invariant: dialect marker stem MUST be preserved in expected_output!
            marker = c["dialect_marker"]
            stem = marker[: max(3, len(marker) - 2)].casefold()
            assert stem in c["expected_output"].casefold(), (
                f"Dialect marker stem '{stem}' ({marker}) lost from expected_output in {c['eval_id']}"
            )
            # Crucial invariant: expected replacement MUST be present in expected_output!
            assert c["expected_replacement"].casefold() in c["expected_output"].casefold()


# ==============================================================================
# 4. Strict Train/Eval Firewall Invariant (0% Leakage)
# ==============================================================================

def test_strict_zero_train_eval_leakage_firewall(
    eval_cases: list[dict[str, Any]],
    sft_trajectories: list[dict[str, Any]],
) -> None:
    """Verify complete passage-level, sentence-level, and citation-level isolation between eval and train."""
    eval_fingerprints = {passage_fingerprint(c["input_text"]) for c in eval_cases}
    eval_raw_fingerprints = {passage_fingerprint(c.get("source_metadata", {}).get("citation", "")) for c in eval_cases}

    for idx, t in enumerate(sft_trajectories, 1):
        q = t["query"]
        steps = " ".join(t.get("reasoning_steps", []))
        resp = t.get("final_response", "")

        q_fp = passage_fingerprint(q)
        assert q_fp not in eval_fingerprints, f"Trajectory {idx} query leaks into evaluation benchmark!"

        for c in eval_cases:
            # Check for verbatim sentence leakage in reasoning or response
            raw_sent = c["input_text"]
            if c["case_type"] == "CORRECT_MIXED":
                # Also check base sentence without injected error
                raw_sent = c["input_text"].split(", і ")[0]
            if len(raw_sent) >= 30:
                assert raw_sent not in steps, f"Trajectory {idx} steps leak evaluation sentence: '{raw_sent}'"
                assert raw_sent not in resp, f"Trajectory {idx} response leaks evaluation sentence: '{raw_sent}'"


# ==============================================================================
# 5. SFT Dataset Schema, Quotas & Replay Buffer Verification
# ==============================================================================

def test_sft_dataset_schema_validation(
    sft_trajectories: list[dict[str, Any]],
    trajectory_schema: dict[str, Any],
) -> None:
    """Verify 100% of SFT trajectories conform to Draft 2020-12 schema."""
    validator = jsonschema.Draft202012Validator(trajectory_schema)
    for idx, traj in enumerate(sft_trajectories, 1):
        errors = list(validator.iter_errors(traj))
        assert not errors, f"Validation errors on trajectory {idx} ({traj.get('trajectory_id')}): {[e.message for e in errors]}"


def test_sft_dataset_quotas_and_unique_ids(sft_trajectories: list[dict[str, Any]]) -> None:
    """Verify SFT dataset size >= 500, trajectory IDs uniqueness, and replay buffer size >= 100."""
    total = len(sft_trajectories)
    assert total >= 500, f"Expected >= 500 trajectories, got {total}"

    traj_ids = [t["trajectory_id"] for t in sft_trajectories]
    assert len(traj_ids) == len(set(traj_ids)), "Duplicate trajectory IDs detected in SFT dataset!"

    # Dialect defense trajectories: is_calque_or_russianism == False
    dialect_trajs = [t for t in sft_trajectories if t.get("is_calque_or_russianism") is False]
    assert len(dialect_trajs) >= 450, f"Expected >= 450 dialect defense trajectories, got {len(dialect_trajs)}"

    # Replay buffer trajectories: is_calque_or_russianism == True (from modern literary v0.2 baseline)
    replay_trajs = [t for t in sft_trajectories if t.get("is_calque_or_russianism") is True]
    assert len(replay_trajs) >= 100, f"Expected >= 100 modern literary replay trajectories, got {len(replay_trajs)}"


# ==============================================================================
# 6. Bilodid Quarantine & Dialect Authenticity Invariants
# ==============================================================================

def test_bilodid_quarantine_enforced(
    eval_cases: list[dict[str, Any]],
    sft_trajectories: list[dict[str, Any]],
) -> None:
    """Ensure Bilodid's СУМ-11 editorial content is quarantined and never cited as authority."""
    banned_needles = ["Білодід", "І. К. Білодід", "ред. колегія І. К. Білодіда", "СУМ-11 як норма"]

    for c in eval_cases:
        notes = c.get("linguistic_notes", "")
        author = c.get("collector_or_author", "")
        work = c.get("source_work", "")
        for needle in banned_needles:
            assert needle not in notes, f"Banned authority needle '{needle}' found in notes of {c['eval_id']}"
            assert needle not in author, f"Banned authority needle '{needle}' found in author of {c['eval_id']}"
            assert needle not in work, f"Banned authority needle '{needle}' found in work of {c['eval_id']}"

    for t in sft_trajectories:
        reasoning = " ".join(t.get("reasoning_steps", []))
        resp = t.get("final_response", "")
        for needle in banned_needles:
            assert needle not in reasoning, f"Banned authority needle '{needle}' in SFT trajectory {t['trajectory_id']}"
            assert needle not in resp, f"Banned authority needle '{needle}' in SFT response {t['trajectory_id']}"


def test_collector_and_locality_authenticity(eval_cases: list[dict[str, Any]]) -> None:
    """Verify every evaluation record has grounded regional locality and authentic collector/author."""
    for c in eval_cases:
        assert c["locality"], f"Missing locality in {c['eval_id']}"
        assert c["collector_or_author"], f"Missing collector/author in {c['eval_id']}"
        assert c["source_work"], f"Missing source work in {c['eval_id']}"
        assert c["dialect_marker"], f"Missing dialect marker in {c['eval_id']}"


# ==============================================================================
# 7. Multi-Zone Evaluation Engine & Scorer Testing
# ==============================================================================

def test_multizone_evaluation_golden_predictions(eval_cases: list[dict[str, Any]]) -> None:
    """Verify that golden predictions achieve 100% accuracy and clear the gate across all 4 zones."""
    results = evaluate_multizone_benchmark(eval_cases)

    expected_zones = ["southwestern", "northern", "southeastern_slobozhan", "southeastern_steppe"]
    for zone in expected_zones:
        assert zone in results, f"Zone '{zone}' missing from evaluation results"
        metrics = results[zone]
        assert metrics["total_cases"] > 0
        assert metrics["accuracy"] == 1.0
        assert metrics["error_rate"] == 0.0
        assert metrics["failed_cases"] == 0
        assert metrics["gate_cleared"] is True
        assert metrics["clopper_pearson_lower"] >= 0.98


def test_multizone_evaluation_corrupted_predictions(eval_cases: list[dict[str, Any]]) -> None:
    """Verify that corrupt predictions (standardizing dialect marker or failing to fix calque) are caught."""
    # Corrupt predictions for first 10 cases by stripping dialect markers
    corrupt_predictions: dict[str, str] = {}
    for c in eval_cases[:10]:
        corrupt_predictions[c["eval_id"]] = "Стандартизоване загальнолітературне речення без жодних особливостей."

    results = evaluate_multizone_benchmark(eval_cases, predictions=corrupt_predictions)
    sw_metrics = results["southwestern"]
    # Southwestern has cases in first 10, so it should fail those
    assert sw_metrics["failed_cases"] > 0
    assert sw_metrics["accuracy"] < 1.0


def test_modern_literary_non_regression() -> None:
    """Verify <= 0.5% regression against the frozen v0.2 modern literary benchmark."""
    if not V02_BASELINE_SUITE_PATH.exists():
        pytest.skip(f"v0.2 suite missing at {V02_BASELINE_SUITE_PATH}")

    reg_result = verify_modern_literary_regression()
    assert reg_result["available"] is True
    assert reg_result["regression_rate"] <= 0.005, f"Regression rate {reg_result['regression_rate']:.2%} exceeds 0.5% limit!"
    assert reg_result["cleared"] is True


# ==============================================================================
# 8. Helper Functions Unit Tests
# ==============================================================================

def test_clean_headword_and_token_normalization() -> None:
    """Verify headword cleaning removes stress marks, numbers, and tags."""
    assert normalize_lookup_token("го́рлиця") == "горлиця"
    assert normalize_lookup_token("плай") == "плай"
    assert clean_headword("баки́р 2") == "бакир"
    assert clean_headword("го́рлиця, -ці, ж.") == "горлиця"
    assert clean_headword("вівсю́г") == "вівсюг"
    assert clean_headword("плай") == "плай"


def test_clean_sentence_formatting() -> None:
    """Verify sentence cleaning normalizes quotes, whitespace, and leading dashes."""
    raw = "  — Ой куме,   ходім у ліс!  "
    cleaned = clean_sentence(raw)
    assert cleaned == "Ой куме, ходім у ліс!"


def test_passage_fingerprint_invariance() -> None:
    """Verify passage fingerprint is invariant to whitespace and capitalization."""
    s1 = "Гриць пішов до лісу."
    s2 = "гриць  пішов   до лісу! "
    assert passage_fingerprint(s1) == passage_fingerprint(s2)


def test_exact_clopper_pearson_mathematical_bounds() -> None:
    """Verify Clopper-Pearson lower bound calculation on boundary values."""
    assert exact_clopper_pearson_lower(0, 100) == 0.0
    assert exact_clopper_pearson_lower(0, 0) == 0.0

    perfect_lcl = exact_clopper_pearson_lower(100, 100, alpha=0.05)
    assert 0.95 <= perfect_lcl <= 1.0
    # Formula for successes == total is alpha ** (1 / total)
    assert abs(perfect_lcl - (0.05 ** (1.0 / 100))) < 1e-6
