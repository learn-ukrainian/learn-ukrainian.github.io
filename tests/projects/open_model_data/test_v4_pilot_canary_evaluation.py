"""Unit and regression tests for Phase 3.6 Pilot Canary Evaluation (#8010)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import jsonschema
import pytest
from scipy.stats import binomtest

from scripts.projects.open_model_data.v4_pilot_canary_evaluation import (
    CANARY_RECEIPT_SCHEMA_PATH,
    DEFAULT_DATASET_OUTPUT,
    DEFAULT_EVAL_CASES_OUTPUT,
    DEFAULT_HELDOUT_SUITE,
    DEFAULT_RECEIPT_OUTPUT,
    DEFAULT_REPLAY_OUTPUT,
    exact_clopper_pearson_upper,
    load_heldout_contexts,
    load_heldout_target_keys,
    sha256_file,
    validate_no_private_host_paths,
    verify_pilot_canary,
)


def test_pilot_canary_artifacts_exist() -> None:
    """Verify generated dataset, replay buffer, eval cases, and receipt files exist."""
    assert DEFAULT_DATASET_OUTPUT.exists(), "pilot_canary_train_200.jsonl must exist"
    assert DEFAULT_REPLAY_OUTPUT.exists(), "pilot_canary_replay_buffer_30.jsonl must exist"
    assert DEFAULT_EVAL_CASES_OUTPUT.exists(), "pilot_canary_eval_cases.jsonl must exist"
    assert DEFAULT_RECEIPT_OUTPUT.exists(), "pilot_canary_receipt.json must exist"
    assert DEFAULT_RECEIPT_OUTPUT.with_suffix(".json.sha256").exists(), "detached sha256 must exist"


def test_pilot_canary_replay_buffer_composition() -> None:
    """Verify exact 30-item replay buffer composition, provenance grounding, and schema fields."""
    records = [json.loads(line) for line in DEFAULT_REPLAY_OUTPUT.read_text(encoding="utf-8").splitlines() if line]
    assert len(records) == 30, f"Expected exactly 30 replay buffer items, got {len(records)}"

    for idx, r in enumerate(records, 1):
        assert r.get("id"), f"Record {idx} missing id"
        assert r.get("domain"), f"Record {idx} missing domain"
        assert r.get("instruction"), f"Record {idx} missing instruction"
        assert r.get("response"), f"Record {idx} missing response"
        assert r.get("source") == "authentic_ukrainian_corpus"
        assert r.get("source_table") in ("textbooks", "literary_texts"), f"Record {idx} invalid source_table"
        assert r.get("chunk_id"), f"Record {idx} missing chunk_id"
        assert r.get("source_locator"), f"Record {idx} missing source_locator"
        convs = r.get("conversations", [])
        assert len(convs) == 2, f"Record {idx} expected 2 conversation turns, got {len(convs)}"
        assert convs[0]["from"] == "human"
        assert convs[1]["from"] == "gpt"
        validate_no_private_host_paths(r)


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


def test_negative_control_diversity() -> None:
    """Verify 60 distinct PRESERVE negative controls with genuine diverse STEM terms."""
    records = [json.loads(line) for line in DEFAULT_DATASET_OUTPUT.read_text(encoding="utf-8").splitlines() if line]
    preserve_records = [r for r in records if not r.get("is_calque_or_russianism", False)]
    assert len(preserve_records) == 60

    terms = set(r["target_term"].strip().lower() for r in preserve_records)
    assert len(terms) == 60, f"Expected 60 distinct PRESERVE terms, got {len(terms)}"

    queries = set(r["query"].strip() for r in preserve_records)
    assert len(queries) >= 50, f"Expected diverse queries for PRESERVE items, got {len(queries)}"


def test_partition_firewall_zero_heldout_contamination() -> None:
    """Verify zero overlap between pilot canary dataset and held-out suite."""
    if not DEFAULT_HELDOUT_SUITE.exists():
        pytest.skip("Held-out suite file absent in test environment")

    heldout_keys = load_heldout_target_keys(DEFAULT_HELDOUT_SUITE)
    heldout_contexts = load_heldout_contexts(DEFAULT_HELDOUT_SUITE)
    records = [json.loads(line) for line in DEFAULT_DATASET_OUTPUT.read_text(encoding="utf-8").splitlines() if line]

    for r in records:
        target = (r.get("target_term") or "").strip().lower()
        if target:
            assert target not in heldout_keys, f"Contamination: target term '{target}' leaked into pilot canary"

        q_norm = " ".join((r.get("query") or "").strip().lower().split())
        resp_norm = " ".join((r.get("final_response") or "").strip().lower().split())
        for ctx in heldout_contexts:
            if len(ctx) >= 30:
                assert ctx not in q_norm, f"Context leakage in query: {ctx[:40]}"
                assert ctx not in resp_norm, f"Context leakage in response: {ctx[:40]}"


def test_partition_firewall_fails_closed(tmp_path: Path) -> None:
    """Verify that load_heldout_target_keys fails closed if file is missing or empty."""
    missing_file = tmp_path / "missing_heldout.jsonl"
    with pytest.raises(FileNotFoundError):
        load_heldout_target_keys(missing_file)

    empty_file = tmp_path / "empty_heldout.jsonl"
    empty_file.touch()
    with pytest.raises(ValueError, match="empty"):
        load_heldout_target_keys(empty_file)


def test_receipt_schema_validation() -> None:
    """Validate receipt structure against official JSON schema."""
    assert CANARY_RECEIPT_SCHEMA_PATH.exists(), "Schema file must exist"
    schema = json.loads(CANARY_RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))
    receipt = json.loads(DEFAULT_RECEIPT_OUTPUT.read_text(encoding="utf-8"))

    jsonschema.validate(instance=receipt, schema=schema)
    assert receipt["issue"] == 8010
    assert receipt["epic"] == 6321
    assert receipt["verdict"] == "CANARY_PILOT_PASSED"
    assert "replay_buffer" in receipt["files"]
    assert "eval_cases" in receipt["files"]
    assert receipt["files"]["replay_buffer"]["record_count"] == 30
    assert receipt["files"]["eval_cases"]["record_count"] == 900
    assert "receipt" not in receipt["files"], "Receipt self-hash paradox must be removed"


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
        replay_path=DEFAULT_REPLAY_OUTPUT,
        eval_cases_path=DEFAULT_EVAL_CASES_OUTPUT,
    )
    assert result is True


def test_tampered_receipt_gates_fail_verification(tmp_path: Path) -> None:
    """Verify that tampering with safety gate metrics causes verify_pilot_canary to fail."""
    tampered_rcp = tmp_path / "tampered_receipt.json"
    receipt = json.loads(DEFAULT_RECEIPT_OUTPUT.read_text(encoding="utf-8"))

    # Test 1: Forged 0% elimination with passed verdict
    receipt_bad = dict(receipt)
    receipt_bad["evaluation_gates"] = dict(receipt["evaluation_gates"])
    receipt_bad["evaluation_gates"]["calque_elimination_rate"] = 0.0
    tampered_rcp.write_text(json.dumps(receipt_bad, indent=2), encoding="utf-8")
    with pytest.raises(ValueError, match=r"mismatch|FAILED"):
        verify_pilot_canary(
            dataset_path=DEFAULT_DATASET_OUTPUT,
            receipt_path=tampered_rcp,
            heldout_path=DEFAULT_HELDOUT_SUITE,
            replay_path=DEFAULT_REPLAY_OUTPUT,
            eval_cases_path=DEFAULT_EVAL_CASES_OUTPUT,
        )

    # Test 2: Forged 100% harmful edit rate
    receipt_bad2 = dict(receipt)
    receipt_bad2["evaluation_gates"] = dict(receipt["evaluation_gates"])
    receipt_bad2["evaluation_gates"]["harmful_edit_rate"] = 1.0
    receipt_bad2["evaluation_gates"]["harmful_edit_binomial_upper_bound_95"] = 1.0
    tampered_rcp.write_text(json.dumps(receipt_bad2, indent=2), encoding="utf-8")
    with pytest.raises(ValueError, match=r"mismatch|FAILED"):
        verify_pilot_canary(
            dataset_path=DEFAULT_DATASET_OUTPUT,
            receipt_path=tampered_rcp,
            heldout_path=DEFAULT_HELDOUT_SUITE,
            replay_path=DEFAULT_REPLAY_OUTPUT,
            eval_cases_path=DEFAULT_EVAL_CASES_OUTPUT,
        )

    # Test 3: Forged un-converged loss
    receipt_bad3 = dict(receipt)
    receipt_bad3["loss_convergence"] = dict(receipt["loss_convergence"])
    receipt_bad3["loss_convergence"]["converged_loss"] = 99.0
    receipt_bad3["loss_convergence"]["loss_converged"] = False
    tampered_rcp.write_text(json.dumps(receipt_bad3, indent=2), encoding="utf-8")
    with pytest.raises(ValueError, match="Loss convergence gate FAILED"):
        verify_pilot_canary(
            dataset_path=DEFAULT_DATASET_OUTPUT,
            receipt_path=tampered_rcp,
            heldout_path=DEFAULT_HELDOUT_SUITE,
            replay_path=DEFAULT_REPLAY_OUTPUT,
            eval_cases_path=DEFAULT_EVAL_CASES_OUTPUT,
        )


def test_tampered_dataset_fails_verification(tmp_path: Path) -> None:
    """Verify that tampering with dataset records causes verify_pilot_canary to fail."""
    tampered_ds = tmp_path / "tampered_dataset.jsonl"
    shutil.copyfile(DEFAULT_DATASET_OUTPUT, tampered_ds)

    with tampered_ds.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"schema_version": "v1_decolonization_trajectory", "trajectory_id": "bad"}) + "\n")

    with pytest.raises(ValueError, match=r"Canary dataset count error|SHA256 mismatch"):
        verify_pilot_canary(
            dataset_path=tampered_ds,
            receipt_path=DEFAULT_RECEIPT_OUTPUT,
            heldout_path=DEFAULT_HELDOUT_SUITE,
            replay_path=DEFAULT_REPLAY_OUTPUT,
            eval_cases_path=DEFAULT_EVAL_CASES_OUTPUT,
        )


def test_tampered_replay_buffer_fails_verification(tmp_path: Path) -> None:
    """Verify that tampering with replay buffer records causes verify_pilot_canary to fail."""
    tampered_replay = tmp_path / "tampered_replay.jsonl"
    shutil.copyfile(DEFAULT_REPLAY_OUTPUT, tampered_replay)

    with tampered_replay.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"id": "bad", "instruction": "test", "response": "test"}) + "\n")

    with pytest.raises(ValueError, match=r"Canary replay buffer count error|Replay buffer SHA256 mismatch"):
        verify_pilot_canary(
            dataset_path=DEFAULT_DATASET_OUTPUT,
            receipt_path=DEFAULT_RECEIPT_OUTPUT,
            heldout_path=DEFAULT_HELDOUT_SUITE,
            replay_path=tampered_replay,
            eval_cases_path=DEFAULT_EVAL_CASES_OUTPUT,
        )


def test_tampered_eval_cases_fails_verification(tmp_path: Path) -> None:
    """Verify that modifying eval cases causes hash mismatch and verification failure."""
    tampered_eval = tmp_path / "tampered_eval.jsonl"
    shutil.copyfile(DEFAULT_EVAL_CASES_OUTPUT, tampered_eval)

    with tampered_eval.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"case_id": "spurious", "suite": "calque_elimination"}) + "\n")

    with pytest.raises(ValueError, match=r"Evaluation cases SHA256 mismatch|Expected 900 evaluation cases"):
        verify_pilot_canary(
            dataset_path=DEFAULT_DATASET_OUTPUT,
            receipt_path=DEFAULT_RECEIPT_OUTPUT,
            heldout_path=DEFAULT_HELDOUT_SUITE,
            replay_path=DEFAULT_REPLAY_OUTPUT,
            eval_cases_path=tampered_eval,
        )


def test_trajectory_schema_deep_validation(tmp_path: Path) -> None:
    """Verify that trajectory records missing required fields fail deep validation even with matching hash."""
    tampered_ds = tmp_path / "invalid_schema_dataset.jsonl"
    tampered_rcp = tmp_path / "invalid_schema_receipt.json"

    lines = [line for line in DEFAULT_DATASET_OUTPUT.read_text(encoding="utf-8").splitlines() if line]
    rec = json.loads(lines[0])
    del rec["final_response"]
    lines[0] = json.dumps(rec)

    tampered_ds.write_text("\n".join(lines) + "\n", encoding="utf-8")

    receipt = json.loads(DEFAULT_RECEIPT_OUTPUT.read_text(encoding="utf-8"))
    receipt["files"]["dataset"]["sha256"] = sha256_file(tampered_ds)
    tampered_rcp.write_text(json.dumps(receipt, indent=2), encoding="utf-8")

    with pytest.raises(jsonschema.ValidationError):
        verify_pilot_canary(
            dataset_path=tampered_ds,
            receipt_path=tampered_rcp,
            heldout_path=DEFAULT_HELDOUT_SUITE,
            replay_path=DEFAULT_REPLAY_OUTPUT,
            eval_cases_path=DEFAULT_EVAL_CASES_OUTPUT,
        )


def test_empty_replay_object_fails_verification(tmp_path: Path) -> None:
    """Verify that empty replay records fail validation even with matching hash."""
    tampered_replay = tmp_path / "empty_replay.jsonl"
    tampered_rcp = tmp_path / "empty_replay_receipt.json"

    tampered_replay.write_text("\n".join([json.dumps({}) for _ in range(30)]) + "\n", encoding="utf-8")

    receipt = json.loads(DEFAULT_RECEIPT_OUTPUT.read_text(encoding="utf-8"))
    receipt["files"]["replay_buffer"]["sha256"] = sha256_file(tampered_replay)
    tampered_rcp.write_text(json.dumps(receipt, indent=2), encoding="utf-8")

    with pytest.raises(ValueError, match="missing or empty field"):
        verify_pilot_canary(
            dataset_path=DEFAULT_DATASET_OUTPUT,
            receipt_path=tampered_rcp,
            heldout_path=DEFAULT_HELDOUT_SUITE,
            replay_path=tampered_replay,
            eval_cases_path=DEFAULT_EVAL_CASES_OUTPUT,
        )


def test_no_private_host_paths_in_dataset_or_receipt() -> None:
    """Verify OPSEC invariant: zero private host paths or IP addresses."""
    receipt = json.loads(DEFAULT_RECEIPT_OUTPUT.read_text(encoding="utf-8"))
    validate_no_private_host_paths(receipt)

    for line in DEFAULT_DATASET_OUTPUT.read_text(encoding="utf-8").splitlines():
        if line.strip():
            validate_no_private_host_paths(json.loads(line))

    for line in DEFAULT_REPLAY_OUTPUT.read_text(encoding="utf-8").splitlines():
        if line.strip():
            validate_no_private_host_paths(json.loads(line))

    for line in DEFAULT_EVAL_CASES_OUTPUT.read_text(encoding="utf-8").splitlines():
        if line.strip():
            validate_no_private_host_paths(json.loads(line))


def test_opsec_sentinel_fails_verification(tmp_path: Path) -> None:
    """Verify that injecting a private host path sentinel causes immediate failure even with matching hash."""
    tampered_ds = tmp_path / "opsec_dataset.jsonl"
    tampered_rcp = tmp_path / "opsec_receipt.json"

    lines = [line for line in DEFAULT_DATASET_OUTPUT.read_text(encoding="utf-8").splitlines() if line]
    rec = json.loads(lines[0])
    rec["query"] = "Знайдено шлях /home/ops/secret/data.txt"
    lines[0] = json.dumps(rec)
    tampered_ds.write_text("\n".join(lines) + "\n", encoding="utf-8")

    receipt = json.loads(DEFAULT_RECEIPT_OUTPUT.read_text(encoding="utf-8"))
    receipt["files"]["dataset"]["sha256"] = sha256_file(tampered_ds)
    tampered_rcp.write_text(json.dumps(receipt, indent=2), encoding="utf-8")

    with pytest.raises(ValueError, match="OPSEC VIOLATION"):
        verify_pilot_canary(
            dataset_path=tampered_ds,
            receipt_path=tampered_rcp,
            heldout_path=DEFAULT_HELDOUT_SUITE,
            replay_path=DEFAULT_REPLAY_OUTPUT,
            eval_cases_path=DEFAULT_EVAL_CASES_OUTPUT,
        )


def test_clopper_pearson_exact_calculation() -> None:
    """Verify statistical soundness of Clopper-Pearson upper bound against scipy exact."""
    # Compare with scipy.stats.binomtest exact one-sided CI
    for k, n in [(0, 600), (1, 600), (10, 600), (300, 600), (599, 600), (600, 600)]:
        computed = exact_clopper_pearson_upper(k, n, confidence=0.95)
        scipy_exact = binomtest(k, n, alternative="less").proportion_ci(confidence_level=0.95, method="exact").high
        assert abs(computed - scipy_exact) < 1e-10, f"Mismatch at k={k}, n={n}: {computed} vs {scipy_exact}"

    # Verify boundary and error cases
    assert exact_clopper_pearson_upper(600, 600, 0.95) == 1.0

    with pytest.raises(ValueError, match="Sample size n must be positive"):
        exact_clopper_pearson_upper(0, 0, 0.95)

    with pytest.raises(ValueError, match="Sample size n must be positive"):
        exact_clopper_pearson_upper(5, -1, 0.95)

    with pytest.raises(ValueError, match="Success count k must satisfy"):
        exact_clopper_pearson_upper(-1, 600, 0.95)

    with pytest.raises(ValueError, match="Success count k must satisfy"):
        exact_clopper_pearson_upper(601, 600, 0.95)
