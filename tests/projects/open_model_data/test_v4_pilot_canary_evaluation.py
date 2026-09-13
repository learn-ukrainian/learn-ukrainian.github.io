"""Unit and regression tests for Phase 3.6 Pilot Canary Evaluation (#8010)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import jsonschema
import pytest

from scripts.projects.open_model_data.v4_pilot_canary_evaluation import (
    CANARY_RECEIPT_SCHEMA_PATH,
    DEFAULT_DATASET_OUTPUT,
    DEFAULT_HELDOUT_SUITE,
    DEFAULT_RECEIPT_OUTPUT,
    exact_clopper_pearson_upper,
    load_heldout_target_keys,
    validate_no_private_host_paths,
    verify_pilot_canary,
)


def test_pilot_canary_artifacts_exist() -> None:
    """Verify generated dataset and receipt files exist."""
    assert DEFAULT_DATASET_OUTPUT.exists(), "pilot_canary_train_200.jsonl must exist"
    assert DEFAULT_RECEIPT_OUTPUT.exists(), "pilot_canary_receipt.json must exist"


def test_pilot_canary_composition() -> None:
    """Verify exact 200-item composition and format breakdown."""
    records = [json.loads(line) for line in DEFAULT_DATASET_OUTPUT.read_text(encoding="utf-8").splitlines() if line]
    assert len(records) == 200, f"Expected exactly 200 items, got {len(records)}"

    correct = [r for r in records if r.get("is_calque_or_russianism", True)]
    preserve = [r for r in records if not r.get("is_calque_or_russianism", False)]
    assert len(correct) == 140, f"Expected 140 CORRECT items, got {len(correct)}"
    assert len(preserve) == 60, f"Expected 60 PRESERVE items, got {len(preserve)}"

    # Format distribution verification
    qt = [r for r in records if r.get("format_type") == "quick_tip"]
    me = [r for r in records if r.get("format_type") == "minimal_edit"]
    ct = [r for r in records if r.get("format_type") == "contrastive"]
    da = [r for r in records if r.get("format_type") == "deep_analysis"]

    assert len(qt) == 80, f"Expected 80 Quick Tip (40%), got {len(qt)}"
    assert len(me) == 50, f"Expected 50 Minimal Edit (25%), got {len(me)}"
    assert len(ct) == 40, f"Expected 40 Contrastive (20%), got {len(ct)}"
    assert len(da) == 30, f"Expected 30 Deep Analysis (15%), got {len(da)}"

    # Per-format CORRECT / PRESERVE split
    assert sum(1 for r in qt if r.get("is_calque_or_russianism", True)) == 56
    assert sum(1 for r in qt if not r.get("is_calque_or_russianism", False)) == 24
    assert sum(1 for r in me if r.get("is_calque_or_russianism", True)) == 35
    assert sum(1 for r in me if not r.get("is_calque_or_russianism", False)) == 15
    assert sum(1 for r in ct if r.get("is_calque_or_russianism", True)) == 28
    assert sum(1 for r in ct if not r.get("is_calque_or_russianism", False)) == 12
    assert sum(1 for r in da if r.get("is_calque_or_russianism", True)) == 21
    assert sum(1 for r in da if not r.get("is_calque_or_russianism", False)) == 9


def test_partition_firewall_zero_heldout_contamination() -> None:
    """Verify zero overlap between pilot canary dataset and held-out suite."""
    if not DEFAULT_HELDOUT_SUITE.exists():
        pytest.skip("Held-out suite file absent in test environment")

    heldout_keys = load_heldout_target_keys(DEFAULT_HELDOUT_SUITE)
    records = [json.loads(line) for line in DEFAULT_DATASET_OUTPUT.read_text(encoding="utf-8").splitlines() if line]

    for r in records:
        target = (r.get("target_term") or "").strip().lower()
        if target:
            assert target not in heldout_keys, f"Contamination: target term '{target}' leaked into pilot canary"


def test_receipt_schema_validation() -> None:
    """Validate receipt structure against official JSON schema."""
    assert CANARY_RECEIPT_SCHEMA_PATH.exists(), "Schema file must exist"
    schema = json.loads(CANARY_RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))
    receipt = json.loads(DEFAULT_RECEIPT_OUTPUT.read_text(encoding="utf-8"))

    jsonschema.validate(instance=receipt, schema=schema)
    assert receipt["issue"] == 8010
    assert receipt["epic"] == 6321
    assert receipt["verdict"] == "CANARY_PILOT_PASSED"


def test_canary_safety_gates() -> None:
    """Verify non-negotiable safety gate thresholds in receipt."""
    receipt = json.loads(DEFAULT_RECEIPT_OUTPUT.read_text(encoding="utf-8"))
    gates = receipt["evaluation_gates"]

    # Gate 1: Calque elimination rate >= 90%
    assert gates["calque_elimination_rate"] >= 0.90
    assert gates["calque_elimination_gate_passed"] is True

    # Gate 2: Harmful edit rate <= 1.0% with binomial upper bound < 1.0%
    assert gates["harmful_edit_rate"] <= 0.01
    assert gates["harmful_edit_binomial_upper_bound_95"] < 0.01
    assert gates["harmful_edit_gate_passed"] is True

    # Gate 3: General NLP non-inferiority margin <= 1.5%
    assert gates["general_nlp_non_inferiority_margin"] <= 0.015
    assert gates["general_nlp_gate_passed"] is True

    assert gates["all_gates_passed"] is True


def test_verify_only_succeeds_on_valid_artifacts() -> None:
    """Verify --verify-only check passes on committed artifacts."""
    result = verify_pilot_canary(
        dataset_path=DEFAULT_DATASET_OUTPUT,
        receipt_path=DEFAULT_RECEIPT_OUTPUT,
        heldout_path=DEFAULT_HELDOUT_SUITE,
    )
    assert result is True


def test_tampered_dataset_fails_verification(tmp_path: Path) -> None:
    """Verify that tampering with dataset records causes verify_pilot_canary to fail."""
    tampered_ds = tmp_path / "tampered_dataset.jsonl"
    tampered_rcp = tmp_path / "tampered_receipt.json"

    shutil.copyfile(DEFAULT_DATASET_OUTPUT, tampered_ds)
    shutil.copyfile(DEFAULT_RECEIPT_OUTPUT, tampered_rcp)

    # Append a spurious item
    with tampered_ds.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"schema_version": "v1_decolonization_trajectory", "trajectory_id": "bad"}) + "\n")

    with pytest.raises(ValueError, match=r"Canary dataset count error|SHA256 mismatch"):
        verify_pilot_canary(
            dataset_path=tampered_ds,
            receipt_path=tampered_rcp,
            heldout_path=DEFAULT_HELDOUT_SUITE,
        )


def test_no_private_host_paths_in_dataset_or_receipt() -> None:
    """Verify OPSEC invariant: zero private host paths or IP addresses."""
    receipt = json.loads(DEFAULT_RECEIPT_OUTPUT.read_text(encoding="utf-8"))
    validate_no_private_host_paths(receipt)

    for line in DEFAULT_DATASET_OUTPUT.read_text(encoding="utf-8").splitlines():
        if line.strip():
            validate_no_private_host_paths(json.loads(line))


def test_clopper_pearson_exact_calculation() -> None:
    """Verify statistical soundness of Clopper-Pearson upper bound."""
    # 0 errors out of 600
    ub_0 = exact_clopper_pearson_upper(0, 600, 0.95)
    assert ub_0 < 0.005

    # 1 error out of 600
    ub_1 = exact_clopper_pearson_upper(1, 600, 0.95)
    assert ub_1 < 0.010
