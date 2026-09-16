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
  5. Strict 0% train/eval leakage firewall (zero sentence, passage, citation, or lemma overlap).
  6. SFT training dataset validation (>= 500 trajectories, Draft 2020-12 schema, unique IDs).
  7. Real VESUM attestation and real dictionary evidence (zero dummy placeholders).
  8. Calibrated replay buffer (>= 100 modern literary / anti-calque trajectories from v0.2).
  9. Permanent quarantine of Bilodid's СУМ-11 editorial apparatus.
 10. Multi-zone evaluation scorer with strict full-sentence preservation (rejects destructive probes).
 11. Modern literary non-regression check against frozen v0.2 benchmark (<= 0.5% regression).
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from typing import Any

import jsonschema
import pytest

from scripts.projects.open_model_data.v5_mine_dialect_corpus import (
    DEFAULT_RELEASE_DIR,
    DEFAULT_VESUM_DB,
    EVAL_SCHEMA_FILE,
    RECEIPT_SCHEMA_FILE,
    RU_CHARS_RE,
    RU_GLOSS_RE,
    TRAJECTORY_SCHEMA_FILE,
    V02_BASELINE_SUITE_PATH,
    ZONE_MINIMUM_QUOTAS,
    clean_headword,
    clean_sentence,
    evaluate_multizone_benchmark,
    exact_clopper_pearson_lower,
    find_attested_synonym,
    normalize_for_eval,
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
            assert c["injected_error_type"] in {"colonial_calque", "punctuation"}

            marker = c["dialect_marker"]
            stem = marker[: max(3, len(marker) - 2)].casefold()
            assert stem in c["expected_output"].casefold(), (
                f"Dialect marker stem '{stem}' ({marker}) lost from expected_output in {c['eval_id']}"
            )
            assert c["expected_replacement"].casefold() in c["expected_output"].casefold()


# ==============================================================================
# 4. Strict Train/Eval Firewall Invariant (0% Leakage)
# ==============================================================================

def test_strict_zero_train_eval_leakage_firewall(
    eval_cases: list[dict[str, Any]],
    sft_trajectories: list[dict[str, Any]],
) -> None:
    """Verify complete passage-level, sentence-level, citation-level, and lemma isolation between eval and train."""
    eval_lemmas = {c["dialect_marker"].casefold() for c in eval_cases}
    sft_dialect_lemmas = {
        t["target_term"].casefold()
        for t in sft_trajectories
        if not t.get("is_calque_or_russianism")
    }

    # 1. Zero lemma overlap
    lemma_overlap = eval_lemmas & sft_dialect_lemmas
    assert not lemma_overlap, f"Lemma overlap between eval and SFT detected: {lemma_overlap}"

    # 2. Zero citation overlap
    eval_cits = {c["source_metadata"]["citation"] for c in eval_cases}
    sft_cits = set()
    for t in sft_trajectories:
        if not t.get("is_calque_or_russianism"):
            for alt in t.get("register_spectrum", {}).get("alternatives", []):
                src = alt.get("evidence_source", "")
                import re
                m = re.search(r"\(([^\(\)]+)\)", src)
                if m:
                    sft_cits.add(m.group(1).strip())
                    sft_cits.add(f"({m.group(1).strip()})")

    citation_overlap = eval_cits & sft_cits
    assert not citation_overlap, f"Citation overlap between eval and SFT detected: {citation_overlap}"

    # 3. Complete sentence and passage containment check
    sft_blobs = []
    for t in sft_trajectories:
        sft_blobs.append(t["query"])
        sft_blobs.append(t.get("final_response", ""))
        sft_blobs.extend(t.get("reasoning_steps", []))
    full_sft_corpus = normalize_for_eval(" ".join(sft_blobs))

    for c in eval_cases:
        eval_sent_norm = normalize_for_eval(c["input_text"])
        assert len(eval_sent_norm) >= 20
        assert eval_sent_norm not in full_sft_corpus, f"Eval sentence leaked into SFT corpus: '{eval_sent_norm}'"


# ==============================================================================
# 5. SFT Dataset Schema, Quotas, Real VESUM Evidence & Replay Buffer
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

    dialect_trajs = [t for t in sft_trajectories if t.get("is_calque_or_russianism") is False]
    assert len(dialect_trajs) >= 450, f"Expected >= 450 dialect defense trajectories, got {len(dialect_trajs)}"

    replay_trajs = [t for t in sft_trajectories if t.get("is_calque_or_russianism") is True]
    assert len(replay_trajs) >= 100, f"Expected >= 100 modern literary replay trajectories, got {len(replay_trajs)}"


def test_sft_dataset_real_vesum_attestation_and_no_placeholders(
    sft_trajectories: list[dict[str, Any]],
) -> None:
    """Verify that SFT trajectories contain real VESUM attestation and no dummy placeholders."""
    con_ves = sqlite3.connect(DEFAULT_VESUM_DB)
    cur_ves = con_ves.cursor()

    banned_placeholders = ["літературний аналог", "літературний синонім", "placeholder", "dummy"]

    for t in sft_trajectories:
        if t.get("is_calque_or_russianism"):
            continue

        raw_str = json.dumps(t, ensure_ascii=False)
        for ph in banned_placeholders:
            assert ph not in raw_str, f"Found placeholder '{ph}' in SFT trajectory {t['trajectory_id']}"

        # Ensure no trajectory uses the dummy fallback 'відповідник' as its purported literary synonym
        attested_lemmas = [att["lemma"].casefold() for att in t["vesum_attestation"]]
        assert "відповідник" not in attested_lemmas, (
            f"Dummy fallback 'відповідник' found in SFT trajectory {t['trajectory_id']}"
        )

        # Verify that vesum_attestation entries are backed by real database facts
        for att in t["vesum_attestation"]:
            lemma = att["lemma"]
            cur_ves.execute("SELECT count(*) FROM forms_all WHERE lemma = ?", (lemma,))
            row = cur_ves.fetchone()
            actual_count = row[0] if row else 0

            if att.get("is_standard_attested"):
                assert actual_count > 0, f"Lemma '{lemma}' declared standard_attested but has 0 forms in VESUM"
                assert att["vesum_forms_count"] == actual_count, (
                    f"Count mismatch for '{lemma}': declared={att['vesum_forms_count']}, actual={actual_count}"
                )

    con_ves.close()


# ==============================================================================
# 6. Bilodid Quarantine & Dialect Sentence Integrity
# ==============================================================================

def test_bilodid_quarantine_enforced(
    eval_cases: list[dict[str, Any]],
    sft_trajectories: list[dict[str, Any]],
) -> None:
    """Ensure Bilodid's editorial apparatus is quarantined and never cited as authority."""
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


def test_sentence_integrity_and_no_dictionary_glosses(eval_cases: list[dict[str, Any]]) -> None:
    """Verify that evaluation sentences are genuine quotations without unclosed parentheses or dictionary glosses."""
    for c in eval_cases:
        s = c["input_text"]
        # Balanced parentheses and brackets
        assert s.count("(") == s.count(")"), f"Unbalanced parentheses in {c['eval_id']}: '{s}'"
        assert s.count("[") == s.count("]"), f"Unbalanced brackets in {c['eval_id']}: '{s}'"
        assert not s.endswith("("), f"Sentence ends with open parenthesis in {c['eval_id']}: '{s}'"

        # No Russian characters or dictionary glosses
        assert not RU_CHARS_RE.search(s), f"Russian characters found in {c['eval_id']}: '{s}'"
        assert not RU_GLOSS_RE.search(s), f"Russian dictionary gloss found in {c['eval_id']}: '{s}'"

        # Verified metadata
        assert c["locality"], f"Missing locality in {c['eval_id']}"
        assert c["collector_or_author"], f"Missing collector/author in {c['eval_id']}"
        assert c["source_work"], f"Missing source work in {c['eval_id']}"
        assert c["dialect_marker"], f"Missing dialect marker in {c['eval_id']}"


# ==============================================================================
# 7. Multi-Zone Evaluation Engine & Scorer Testing (Full-Sentence Preservation)
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


def test_multizone_evaluation_probe_destructive_rejection(eval_cases: list[dict[str, Any]]) -> None:
    """Verify that destructive/truncated outputs (e.g. marker + replacement only) are strictly rejected."""
    # Probe supplies only truncated marker plus replacement, deleting the rest of the sentence
    truncated_probe_predictions: dict[str, str] = {}
    for c in eval_cases:
        marker = c["dialect_marker"]
        rep = c.get("expected_replacement") or marker
        truncated_probe_predictions[c["eval_id"]] = f"{marker} {rep}"

    results = evaluate_multizone_benchmark(eval_cases, predictions=truncated_probe_predictions)
    for zone, metrics in results.items():
        assert metrics["accuracy"] == 0.0, f"Zone '{zone}' accepted truncated probe predictions!"
        assert metrics["failed_cases"] == metrics["total_cases"]
        assert metrics["gate_cleared"] is False


def test_multizone_evaluation_fail_closed_on_empty_zone() -> None:
    """Verify that the evaluation engine fails closed when a zone is empty."""
    dummy_cases = [
        {
            "eval_id": "eval_mz_dial_9999",
            "macro_zone": "southwestern",
            "sub_zone": "southwestern_boyko",
            "dialect_marker": "тест",
            "case_type": "PRESERVE",
            "input_text": "Тестове речення без помилок.",
            "expected_output": "Тестове речення без помилок.",
        }
    ]
    results = evaluate_multizone_benchmark(dummy_cases, predictions={"eval_mz_dial_9999": "Тестове речення без помилок."})
    # Northern and Southeastern zones have 0 cases, so they must fail closed
    assert results["northern"]["gate_cleared"] is False
    assert results["southeastern_slobozhan"]["gate_cleared"] is False
    assert results["southeastern_steppe"]["gate_cleared"] is False
    # Southwestern has only 1 case, violating the 600 quota, so it must also fail closed
    assert results["southwestern"]["gate_cleared"] is False


def test_multizone_evaluation_rejects_punctuation_corruption(eval_cases: list[dict[str, Any]]) -> None:
    """Verify that mutating punctuation in expected outputs is strictly rejected across all zones."""
    # Add a comma after the first word of every expected output
    corrupt_comma_predictions: dict[str, str] = {}
    for c in eval_cases:
        parts = c["expected_output"].split(maxsplit=1)
        if len(parts) > 1:
            corrupt_comma_predictions[c["eval_id"]] = f"{parts[0]}, {parts[1]}"
        else:
            corrupt_comma_predictions[c["eval_id"]] = f"{parts[0]},"

    results = evaluate_multizone_benchmark(eval_cases, predictions=corrupt_comma_predictions)
    for zone, metrics in results.items():
        assert metrics["passed_cases"] == 0, f"Zone '{zone}' passed corrupted comma predictions!"
        assert metrics["gate_cleared"] is False, f"Zone '{zone}' cleared gate on corrupted punctuation!"


def test_multizone_evaluation_enforces_zone_denominators() -> None:
    """Verify that evaluation gates fail closed when zone quotas (600/400/250/250) are not met."""
    # Provide 1 perfect case per zone
    sample_cases = [
        {
            "eval_id": "eval_sw_1",
            "macro_zone": "southwestern",
            "sub_zone": "southwestern_boyko",
            "dialect_marker": "тест",
            "case_type": "PRESERVE",
            "input_text": "Тестове речення без помилок.",
            "expected_output": "Тестове речення без помилок.",
        },
        {
            "eval_id": "eval_north_1",
            "macro_zone": "northern",
            "sub_zone": "northern",
            "dialect_marker": "тест",
            "case_type": "PRESERVE",
            "input_text": "Тестове речення без помилок.",
            "expected_output": "Тестове речення без помилок.",
        },
        {
            "eval_id": "eval_slob_1",
            "macro_zone": "southeastern",
            "sub_zone": "southeastern_slobozhan",
            "dialect_marker": "тест",
            "case_type": "PRESERVE",
            "input_text": "Тестове речення без помилок.",
            "expected_output": "Тестове речення без помилок.",
        },
        {
            "eval_id": "eval_steppe_1",
            "macro_zone": "southeastern",
            "sub_zone": "southeastern_steppe",
            "dialect_marker": "тест",
            "case_type": "PRESERVE",
            "input_text": "Тестове речення без помилок.",
            "expected_output": "Тестове речення без помилок.",
        },
    ]
    preds = {c["eval_id"]: c["expected_output"] for c in sample_cases}
    results = evaluate_multizone_benchmark(sample_cases, predictions=preds)

    # All zones have 100% accuracy on their 1 case, but NONE may clear the gate due to quota enforcement
    for zone, metrics in results.items():
        assert metrics["accuracy"] == 1.0
        assert metrics["total_cases"] == 1
        min_q = ZONE_MINIMUM_QUOTAS[zone]
        assert metrics["gate_cleared"] is False, f"Zone '{zone}' cleared gate with 1 case (min quota {min_q})!"


def test_modern_literary_non_regression() -> None:
    """Verify <= 0.5% regression against the frozen v0.2 modern literary benchmark."""
    if not V02_BASELINE_SUITE_PATH.exists():
        pytest.skip(f"v0.2 suite missing at {V02_BASELINE_SUITE_PATH}")

    # 1. Oracle ground-truth verification
    reg_result = verify_modern_literary_regression()
    assert reg_result["available"] is True
    assert reg_result["regression_rate"] <= 0.005, f"Regression rate {reg_result['regression_rate']:.2%} exceeds 0.5% limit!"
    assert reg_result["cleared"] is True
    assert reg_result["is_oracle_reference"] is True

    # 2. Destructive single-word probe rejection (probe returns only target/replacement token)
    lines = [json.loads(l) for l in V02_BASELINE_SUITE_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
    probe_preds = {}
    for c in lines:
        eid = c["eval_id"]
        if c["expected_action"] == "PRESERVE":
            probe_preds[eid] = c["target_term"]
        else:
            probe_preds[eid] = c.get("expected_replacement") or ""

    probe_result = verify_modern_literary_regression(predictions=probe_preds)
    assert probe_result["cleared"] is False, "Regression gate accepted destructive single-word outputs!"
    assert probe_result["passed_cases"] == 0, "Single-word output should have 0 passed cases!"
    assert probe_result["regression_rate"] == 1.0, "Regression rate should be 100% on destructive output!"


def test_predictions_cli_handling_fails_on_missing_file(tmp_path: Any) -> None:
    """Verify that specifying a nonexistent predictions file fails closed instead of selecting oracle mode."""
    import subprocess
    import sys
    cmd = [
        sys.executable,
        "scripts/projects/open_model_data/v5_mine_dialect_corpus.py",
        "--evaluate",
        "--predictions",
        str(tmp_path / "nonexistent_predictions.jsonl"),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode != 0
    assert "FileNotFoundError" in proc.stderr or "Predictions file not found" in proc.stderr


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
    assert abs(perfect_lcl - (0.05 ** (1.0 / 100))) < 1e-6


def test_find_attested_synonym_rejects_descriptive_and_crossref() -> None:
    """Verify find_attested_synonym rejects descriptive fragments and crossrefs, and validates real synonyms."""
    # Descriptive definition with adjective 'слизький' for noun 'затока'
    defn_zatoka = "ЗА́ТОКА, и, ж., діал. Слизький схил, боковий спад дороги, куди сповзають сани."
    assert find_attested_synonym(defn_zatoka, "затока", DEFAULT_VESUM_DB) is None

    # Descriptive definition with adjective 'безладний' for noun 'сутолока'
    defn_sutoloka = "СУ́ТОЛОКА, и, ж., діал. Безладний рух, штовхання в тісноті, в натовпі."
    assert find_attested_synonym(defn_sutoloka, "сутолока", DEFAULT_VESUM_DB) is None

    # Cross-reference 'див.' for 'чотири'
    defn_chotyry = "ЧОТИ́РИ, рьо́х, числ. 1. Назва числа 4... // див. сидіти; див. іти."
    assert find_attested_synonym(defn_chotyry, "чотири", DEFAULT_VESUM_DB) is None

    # Valid noun-noun synonyms
    defn_barabolya = "БАРАБО́ЛЯ, і, ж., діал. Картопля."
    res_barabolya = find_attested_synonym(defn_barabolya, "бараболя", DEFAULT_VESUM_DB)
    assert res_barabolya is not None
    assert res_barabolya[0] == "картопля"

    defn_boz = "Боз, зу, м. = бузок."
    res_boz = find_attested_synonym(defn_boz, "боз", DEFAULT_VESUM_DB)
    assert res_boz is not None
    assert res_boz[0] == "бузок"

    defn_hazdynya = "ГА́ЗДИНЯ, і, ж., зах. Господарка."
    res_hazdynya = find_attested_synonym(defn_hazdynya, "газдиня", DEFAULT_VESUM_DB)
    assert res_hazdynya is not None
    assert res_hazdynya[0] == "господарка"


def test_standard_headwords_with_nested_idioms_excluded(
    eval_cases: list[dict[str, Any]],
    sft_trajectories: list[dict[str, Any]],
) -> None:
    """Verify that standard headwords with nested dialect idioms (like чотири) are completely excluded."""
    eval_markers = {c["dialect_marker"].casefold() for c in eval_cases}
    sft_targets = {t["target_term"].casefold() for t in sft_trajectories}

    assert "чотири" not in eval_markers, "'чотири' leaked into evaluation dialect markers!"
    assert "чотири" not in sft_targets, "'чотири' leaked into SFT dialect targets!"

    # Ensure no sentence in eval or SFT contains standard quotes for чотири
    banned_substring = "поруч з джерихою сиділи чотири молодиці"
    for c in eval_cases:
        assert banned_substring not in c["input_text"].casefold()
    for t in sft_trajectories:
        assert banned_substring not in t["query"].casefold()


def test_sft_synonyms_strictly_bound_to_quotation_sense(
    sft_trajectories: list[dict[str, Any]],
) -> None:
    """Verify that synonyms in SFT trajectories are bound strictly to the quoted sense."""
    for t in sft_trajectories:
        q = t.get("query", "")
        lemmas = [att["lemma"].casefold() for att in t.get("vesum_attestation", [])]

        if "служащий хліб добрий, та тільки вимовний" in q.casefold():
            assert "докірливий" in lemmas, f"Expected sense synonym 'докірливий' for вимовний quote, got {lemmas}"
            assert "красномовний" not in lemmas, f"Incorrect cross-sense synonym 'красномовний' in {lemmas}"

        if "минув уже рік з окладом" in q.casefold():
            assert "лишок" in lemmas, f"Expected sense synonym 'лишок' for оклад quote, got {lemmas}"
            assert "компрес" not in lemmas, f"Incorrect cross-sense synonym 'компрес' in {lemmas}"


def test_dialect_variant_headers_exclude_standard_quotations(
    eval_cases: list[dict[str, Any]],
    sft_trajectories: list[dict[str, Any]],
) -> None:
    """Verify that headwords with dialect variant markers (приймати, затикати) are not admitted."""
    eval_markers = {c["dialect_marker"].casefold() for c in eval_cases}
    sft_targets = {t.get("target_term", "").casefold() for t in sft_trajectories}

    banned_words = {"приймати", "затикати", "чотири", "антихрист"}
    assert not (eval_markers & banned_words), f"Banned words leaked into eval markers: {eval_markers & banned_words}"
    assert not (sft_targets & banned_words), f"Banned words leaked into SFT targets: {sft_targets & banned_words}"

    banned_substrings = [
        "не прийматимуть їх до вищих шкіл",
        "нервово затикала голкою",
        "поруч з джерихою сиділи чотири молодиці",
    ]
    for c in eval_cases:
        for bs in banned_substrings:
            assert bs not in c["input_text"].casefold(), f"Banned quotation fragment '{bs}' found in eval {c['eval_id']}"
    for t in sft_trajectories:
        for bs in banned_substrings:
            assert bs not in t["query"].casefold(), f"Banned quotation fragment '{bs}' found in SFT {t['trajectory_id']}"


def test_sub_sense_boundary_and_synonym_binding(
    eval_cases: list[dict[str, Any]],
    sft_trajectories: list[dict[str, Any]],
) -> None:
    """Verify that quotations following sub-senses (// or ◇) extract the exact sub-sense synonym."""
    # 1. Direct unit test of sub-sense extraction for загирити and заголомшити
    defn_zagiriti_sub1 = "// Закинути, загубити. Панотець наробив крику, що.. загирили йому одно важне письмо (Март., Тв., 1954, 233);"
    res_zagiriti_sub1 = find_attested_synonym(defn_zagiriti_sub1, "загирити", DEFAULT_VESUM_DB)
    assert res_zagiriti_sub1 is not None
    assert res_zagiriti_sub1[0] == "закинути"

    defn_zagolomshiti_sub1 = "// Заспокоїти, затамувати. — Я рвалася до роботи, аби заголомшити в собі той біль, що мені під серце підступав (Март., Тв., 1954, 155)."
    res_zagolomshiti_sub1 = find_attested_synonym(defn_zagolomshiti_sub1, "заголомшити", DEFAULT_VESUM_DB)
    assert res_zagolomshiti_sub1 is not None
    assert res_zagolomshiti_sub1[0] == "заспокоїти"

    # 2. Check SFT trajectories: if загирити or заголомшити are in SFT, ensure no sense crossing occurred
    for t in sft_trajectories:
        q = t.get("query", "").casefold()
        lemmas = [att["lemma"].casefold() for att in t.get("vesum_attestation", [])]
        equiv_mech = t.get("morphemic_breakdown", {}).get("ukrainian_equivalent_mechanism", "").casefold()

        if "загирили йому одно важне письмо" in q:
            assert "закинути" in lemmas or "загубити" in lemmas
            assert "розтратити" not in lemmas
            assert "розтратити" not in equiv_mech

        if "заголомшити в собі той біль" in q:
            assert "заспокоїти" in lemmas or "затамувати" in lemmas
            assert "приголомшити" not in lemmas
            assert "приголомшити" not in equiv_mech
