"""Unit and regression tests for Phase 5.2 Dialect & Historical Protection Suite (ULDR #8051)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import jsonschema
import pytest

from scripts.projects.open_model_data.v5_dialect_protection_evaluator import (
    evaluate_protection_suite,
    evaluate_single_case,
    exact_clopper_pearson_lower,
    exact_clopper_pearson_upper,
    format_protection_report,
    generate_mock_predictions,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "data" / "projects" / "open_model_data"
PARTITION_DIR = DATA_DIR / "decolonization" / "partitions"
CONTRACTS_DIR = DATA_DIR / "contracts"

SUITE_PATH = PARTITION_DIR / "dialect_historical_protection_suite_600.jsonl"
SHA_PATH = PARTITION_DIR / "dialect_historical_protection_suite_600.sha256"
RECEIPT_PATH = PARTITION_DIR / "dialect_historical_protection_receipt_v1.json"
RECORD_SCHEMA_PATH = CONTRACTS_DIR / "v1_dialect_historical_protection_record.schema.json"
RECEIPT_SCHEMA_PATH = CONTRACTS_DIR / "v1_dialect_historical_protection_receipt.schema.json"


@pytest.fixture(scope="module")
def suite_cases() -> list[dict[str, Any]]:
    """Load and parse the 600-case evaluation suite."""
    assert SUITE_PATH.exists(), f"Suite file missing at: {SUITE_PATH}"
    lines = [json.loads(line) for line in SUITE_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    return lines


@pytest.fixture(scope="module")
def record_schema() -> dict[str, Any]:
    """Load record JSON schema."""
    assert RECORD_SCHEMA_PATH.exists()
    return json.loads(RECORD_SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def receipt_schema() -> dict[str, Any]:
    """Load receipt JSON schema."""
    assert RECEIPT_SCHEMA_PATH.exists()
    return json.loads(RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))


def test_suite_file_and_sha256_integrity() -> None:
    """Verify partition file exists, matches SHA-256 manifest, and is non-empty."""
    assert SUITE_PATH.exists()
    assert SHA_PATH.exists()

    actual_sha = hashlib.sha256(SUITE_PATH.read_bytes()).hexdigest()
    recorded_sha = SHA_PATH.read_text(encoding="utf-8").split()[0].strip()

    assert actual_sha == recorded_sha, f"SHA-256 drift! Actual: {actual_sha}, Recorded: {recorded_sha}"


def test_suite_receipt_and_schema_validation(receipt_schema: dict[str, Any]) -> None:
    """Verify release receipt exists, conforms to Draft 2020-12 schema, and matches suite facts."""
    assert RECEIPT_PATH.exists()
    receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))

    jsonschema.validate(receipt, receipt_schema)

    assert receipt["schema_version"] == "v1_dialect_historical_protection_receipt"
    assert receipt["issue"] == 8051
    assert receipt["parent_epic"] == 6321
    assert receipt["suite_summary"]["total_test_cases"] == 600
    assert receipt["suite_summary"]["preserve_cases"] == 500
    assert receipt["suite_summary"]["correct_cases"] == 100

    # Invariants checks
    inv = receipt["invariants"]
    assert inv["anti_surzhyk_eradication_mandate"] is True
    assert inv["zero_surzhyk_normalization_tolerance"] is True
    assert inv["dialect_cultural_heritage_protection"] is True
    assert inv["historical_continuity_preservation"] is True
    assert inv["zero_hallucinated_sources"] is True

    # Check file link in receipt
    file_info = receipt["files"]["test_suite_jsonl"]
    assert file_info["record_count"] == 600
    actual_sha = hashlib.sha256(SUITE_PATH.read_bytes()).hexdigest()
    assert file_info["sha256"] == actual_sha


def test_every_record_validates_against_record_schema(
    suite_cases: list[dict[str, Any]], record_schema: dict[str, Any]
) -> None:
    """Verify that all 600 records adhere strictly to the JSON schema."""
    assert len(suite_cases) == 600

    for idx, case in enumerate(suite_cases):
        try:
            jsonschema.validate(case, record_schema)
        except jsonschema.ValidationError as e:
            pytest.fail(f"Record {idx} ({case.get('eval_id')}) failed schema: {e.message}")


def test_suite_exact_strata_and_subgroup_distribution(suite_cases: list[dict[str, Any]]) -> None:
    """Verify precise distribution across strata, subgroups, and action types."""
    assert len(suite_cases) == 600

    strata_counts: dict[str, int] = {}
    subgroup_counts: dict[str, int] = {}
    action_counts: dict[str, int] = {}

    for c in suite_cases:
        strata_counts[c["stratum"]] = strata_counts.get(c["stratum"], 0) + 1
        subgroup_counts[c["subgroup"]] = subgroup_counts.get(c["subgroup"], 0) + 1
        action_counts[c["case_type"]] = action_counts.get(c["case_type"], 0) + 1

    # Exact strata requirements
    assert strata_counts.get("regional_dialect") == 300
    assert strata_counts.get("historical_text") == 200
    assert strata_counts.get("anti_surzhyk_control") == 100

    # Actions: 500 PRESERVE, 100 CORRECT
    assert action_counts.get("PRESERVE") == 500
    assert action_counts.get("CORRECT") == 100

    # Dialect subgroup coverage across Southwestern, Southeastern, Northern
    assert subgroup_counts["southwestern_hutsul"] == 45
    assert subgroup_counts["southwestern_boyko"] == 45
    assert subgroup_counts["southwestern_lemko"] == 40
    assert subgroup_counts["southwestern_galician"] == 50
    assert subgroup_counts["southeastern_poltava"] == 45
    assert subgroup_counts["southeastern_slobozhan"] == 25
    assert subgroup_counts["northern_polissian"] == 50

    # Historical subgroup coverage
    assert subgroup_counts["old_east_slavic"] == 100
    assert subgroup_counts["middle_ukrainian"] == 100

    # Anti-Surzhyk controls
    assert subgroup_counts["colonial_surzhyk_control"] == 100


def test_target_terms_present_and_unambiguous(suite_cases: list[dict[str, Any]]) -> None:
    """Verify target terms are embedded inside the corresponding sentence text."""
    for c in suite_cases:
        target = c["target_term"].lower()
        text = c["input_text"].lower()
        # Stem or whole word must appear in input text
        stem = target[:4] if len(target) >= 5 else target
        assert stem in text, (
            f"Case {c['eval_id']} target '{target}' (stem '{stem}') missing from text: '{c['input_text']}'"
        )


def test_anti_surzhyk_invariant_boundary_defense(suite_cases: list[dict[str, Any]]) -> None:
    """Verify the strategic boundary: dialect words are never labeled Surzhyk and Surzhyk is never labeled PRESERVE."""
    for c in suite_cases:
        stratum = c["stratum"]
        notes = c["linguistic_notes"].lower()
        action = c["case_type"]

        if stratum in ("regional_dialect", "historical_text"):
            assert action == "PRESERVE"
            assert "суржик" not in c["target_term"].lower()
            assert "захисту" in notes or "збереженн" in notes
        elif stratum == "anti_surzhyk_control":
            assert action == "CORRECT"
            assert "суржик" in notes or "російськ" in notes
            assert "виправленн" in notes or "питому" in notes


def test_clopper_pearson_lower_and_upper_mathematics() -> None:
    """Verify mathematical properties of exact Clopper-Pearson bounds for 98% gate."""
    # 300/300 successes -> 95% lower bound must be > 98.0% (approx 0.990)
    lb_300_300 = exact_clopper_pearson_lower(300, 300)
    assert lb_300_300 > 0.980
    assert lb_300_300 == pytest.approx(0.99008, abs=0.001)

    # 294/300 successes (98.0% empirical) -> 95% lower bound is ~96.2% (< 98%)
    lb_300_294 = exact_clopper_pearson_lower(294, 300)
    assert lb_300_294 < 0.980

    # 200/200 successes -> 95% lower bound must be > 98.0%
    lb_200_200 = exact_clopper_pearson_lower(200, 200)
    assert lb_200_200 > 0.980
    assert lb_200_200 == pytest.approx(0.98516, abs=0.001)

    # Upper bound for 0 errors out of 300
    ub_300_0 = exact_clopper_pearson_upper(0, 300)
    assert ub_300_0 < 0.01


def test_evaluator_perfect_model_execution(suite_cases: list[dict[str, Any]]) -> None:
    """Verify evaluator approves a compliant model preserving dialects and eliminating Surzhyk."""
    perfect_preds = generate_mock_predictions(suite_cases, "perfect")
    metrics, results = evaluate_protection_suite(suite_cases, perfect_preds)

    assert len(results) == 600
    assert metrics.total_cases == 600

    # Regional dialect gate
    assert metrics.dialect_total == 300
    assert metrics.dialect_preserved == 300
    assert metrics.dialect_corrupted == 0
    assert metrics.dialect_preservation_rate == 1.0
    assert metrics.dialect_gate_cleared is True

    # Historical gate
    assert metrics.historical_total == 200
    assert metrics.historical_preserved == 200
    assert metrics.historical_corrupted == 0
    assert metrics.historical_preservation_rate == 1.0
    assert metrics.historical_gate_cleared is True

    # Combined cultural heritage (N=500)
    assert metrics.combined_preserve_total == 500
    assert metrics.combined_preserve_passed == 500
    assert metrics.combined_preserve_rate == 1.0
    assert metrics.combined_gate_cleared is True

    # Anti-Surzhyk gate
    assert metrics.surzhyk_total == 100
    assert metrics.surzhyk_eradicated == 100
    assert metrics.surzhyk_normalized == 0
    assert metrics.surzhyk_eradication_rate == 1.0
    assert metrics.surzhyk_normalization_rate == 0.0
    assert metrics.surzhyk_gate_cleared is True

    # Overall master gate
    assert metrics.all_gates_cleared is True

    # Report generation
    report = format_protection_report(metrics)
    assert "PASSED (All Gates Cleared)" in report
    assert "300 / 300" in report
    assert "200 / 200" in report
    assert "100 / 100" in report


def test_evaluator_catches_over_standardization(suite_cases: list[dict[str, Any]]) -> None:
    """Verify evaluator rejects a model that aggressively over-standardizes regional dialects."""
    failing_preds = generate_mock_predictions(suite_cases, "failing_over_standardization")
    metrics, _results = evaluate_protection_suite(suite_cases, failing_preds)

    assert metrics.dialect_preserved == 0
    assert metrics.dialect_corrupted == 300
    assert metrics.dialect_preservation_rate == 0.0
    assert metrics.dialect_gate_cleared is False
    assert metrics.all_gates_cleared is False

    # Historical is preserved in this mock
    assert metrics.historical_gate_cleared is True

    # Report verification
    report = format_protection_report(metrics)
    assert "FAILED" in report


def test_evaluator_catches_surzhyk_normalization(suite_cases: list[dict[str, Any]]) -> None:
    """Verify evaluator catches and fails a model that normalizes Surzhyk as acceptable dialect."""
    failing_preds = generate_mock_predictions(suite_cases, "failing_surzhyk_normalization")
    metrics, _results = evaluate_protection_suite(suite_cases, failing_preds)

    # Dialect and historical pass
    assert metrics.dialect_gate_cleared is True
    assert metrics.historical_gate_cleared is True

    # Surzhyk normalization gate strictly fails
    assert metrics.surzhyk_normalized == 100
    assert metrics.surzhyk_normalization_rate == 1.0
    assert metrics.surzhyk_gate_cleared is False
    assert metrics.all_gates_cleared is False

    report = format_protection_report(metrics)
    assert "FAILED" in report


def test_evaluator_detects_malformed_thought_tags(suite_cases: list[dict[str, Any]]) -> None:
    """Verify unclosed <thought> tags or empty responses are flagged as corruptions."""
    sample_case = suite_cases[0]  # PRESERVE dialect case
    malformed_pred = "<thought>\n1. Аналіз: автентична форма.\nЗабули закрити тег."

    res = evaluate_single_case(sample_case, malformed_pred)
    assert res.is_pass is False
    assert res.is_corrupted is True
    assert "unclosed_thought_tag" in (res.failure_reason or "")
