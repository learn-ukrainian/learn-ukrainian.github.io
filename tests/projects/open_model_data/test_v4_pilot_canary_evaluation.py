"""Unit and regression tests for Phase 3.6 Pilot Canary Evaluation (#8010)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import jsonschema
import numpy as np
import pytest
import safetensors.torch
import torch
from scipy.stats import binomtest

from scripts.projects.open_model_data.v4_pilot_canary_evaluation import (
    CANARY_RECEIPT_SCHEMA_PATH,
    DEFAULT_ADAPTER_OUTPUT,
    DEFAULT_DATASET_OUTPUT,
    DEFAULT_EVAL_CASES_OUTPUT,
    DEFAULT_HELDOUT_SUITE,
    DEFAULT_RECEIPT_OUTPUT,
    DEFAULT_REPLAY_OUTPUT,
    DEFAULT_TRAINING_LOG_OUTPUT,
    DEFAULT_VESUM_DB,
    _sync_adapter_digest,
    exact_clopper_pearson_upper,
    extract_edited_sentence,
    load_heldout_contexts,
    load_heldout_target_keys,
    parse_selected_option,
    score_calque_prediction,
    score_nlp_prediction,
    score_safety_prediction,
    sha256_file,
    validate_no_private_host_paths,
    verify_pilot_canary,
    verify_pilot_canary_partition_firewall,
)


def test_pilot_canary_artifacts_exist() -> None:
    """Verify generated dataset, replay buffer, training log, adapter, eval cases, and receipt files exist."""
    assert DEFAULT_DATASET_OUTPUT.exists(), "pilot_canary_train_200.jsonl must exist"
    assert DEFAULT_REPLAY_OUTPUT.exists(), "pilot_canary_replay_buffer_30.jsonl must exist"
    assert DEFAULT_TRAINING_LOG_OUTPUT.exists(), "pilot_canary_training_log.jsonl must exist"
    assert DEFAULT_ADAPTER_OUTPUT.exists(), "pilot_canary_adapter.safetensors must exist"
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
    assert "training_log" in receipt["files"]
    assert receipt["files"]["replay_buffer"]["record_count"] == 30
    assert receipt["files"]["eval_cases"]["record_count"] == 900
    assert receipt["files"]["training_log"]["record_count"] == 75
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


def _write_receipt_with_digest(rcp_path: Path, data: dict) -> None:
    """Helper to write receipt and its mandatory detached .sha256 sidecar."""
    if "provenance" in data and isinstance(data["provenance"], dict) and "files" in data:
        prov = data["provenance"]
        if "dataset" in data["files"] and "sha256" in data["files"]["dataset"] and "dataset_sha256" in prov:
            prov["dataset_sha256"] = data["files"]["dataset"]["sha256"]
        if "replay_buffer" in data["files"] and "sha256" in data["files"]["replay_buffer"] and "replay_sha256" in prov:
            prov["replay_sha256"] = data["files"]["replay_buffer"]["sha256"]
        if "adapter" in data["files"] and "sha256" in data["files"]["adapter"] and "adapter_digest" in prov:
            prov["adapter_digest"] = data["files"]["adapter"]["sha256"]
    text = json.dumps(data, indent=2) + "\n"
    rcp_path.write_text(text, encoding="utf-8")
    sha_file = rcp_path.with_name(rcp_path.name + ".sha256")
    sha_file.write_text(f"{sha256_file(rcp_path)}  {rcp_path.name}\n", encoding="utf-8")


def test_tampered_receipt_gates_fail_verification(tmp_path: Path) -> None:
    """Verify that tampering with safety gate metrics causes verify_pilot_canary to fail."""
    tampered_rcp = tmp_path / "tampered_receipt.json"
    receipt = json.loads(DEFAULT_RECEIPT_OUTPUT.read_text(encoding="utf-8"))

    # Test 1: Forged 0% elimination with passed verdict
    receipt_bad = dict(receipt)
    receipt_bad["evaluation_gates"] = dict(receipt["evaluation_gates"])
    receipt_bad["evaluation_gates"]["calque_elimination_rate"] = 0.0
    _write_receipt_with_digest(tampered_rcp, receipt_bad)
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
    _write_receipt_with_digest(tampered_rcp, receipt_bad2)
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
    _write_receipt_with_digest(tampered_rcp, receipt_bad3)
    with pytest.raises(ValueError, match=r"Loss convergence gate FAILED|Converged loss mismatch with training log"):
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

    with pytest.raises(ValueError, match=r"Canary replay buffer count error|replay_buffer SHA256 mismatch|Replay buffer SHA256 mismatch"):
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

    with pytest.raises(ValueError, match=r"eval_cases SHA256 mismatch|Evaluation cases SHA256 mismatch|Expected 900 evaluation cases"):
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
    _write_receipt_with_digest(tampered_rcp, receipt)

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
    _write_receipt_with_digest(tampered_rcp, receipt)

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
    _write_receipt_with_digest(tampered_rcp, receipt)

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


def test_missing_detached_sha256_fails_verification(tmp_path: Path) -> None:
    """Verify that verify_pilot_canary fails closed if detached .sha256 is missing."""
    rcp = tmp_path / "receipt_no_sha.json"
    shutil.copyfile(DEFAULT_RECEIPT_OUTPUT, rcp)
    sha_file = rcp.with_name(rcp.name + ".sha256")
    if sha_file.exists():
        sha_file.unlink()
    with pytest.raises(FileNotFoundError, match="Mandatory detached receipt digest missing"):
        verify_pilot_canary(
            dataset_path=DEFAULT_DATASET_OUTPUT,
            receipt_path=rcp,
            heldout_path=DEFAULT_HELDOUT_SUITE,
            replay_path=DEFAULT_REPLAY_OUTPUT,
            eval_cases_path=DEFAULT_EVAL_CASES_OUTPUT,
        )


def test_tampered_detached_sha256_fails_verification(tmp_path: Path) -> None:
    """Verify that tampering with detached .sha256 fails verification."""
    rcp = tmp_path / "receipt_bad_sha.json"
    shutil.copyfile(DEFAULT_RECEIPT_OUTPUT, rcp)
    sha_file = rcp.with_name(rcp.name + ".sha256")
    sha_file.write_text("0000000000000000000000000000000000000000000000000000000000000000  receipt_bad_sha.json\n")
    with pytest.raises(ValueError, match="Detached receipt digest mismatch"):
        verify_pilot_canary(
            dataset_path=DEFAULT_DATASET_OUTPUT,
            receipt_path=rcp,
            heldout_path=DEFAULT_HELDOUT_SUITE,
            replay_path=DEFAULT_REPLAY_OUTPUT,
            eval_cases_path=DEFAULT_EVAL_CASES_OUTPUT,
        )


def test_tampered_record_count_fails_verification(tmp_path: Path) -> None:
    """Verify that tampering with receipt record_count fails verification."""
    rcp = tmp_path / "receipt_bad_count.json"
    receipt = json.loads(DEFAULT_RECEIPT_OUTPUT.read_text(encoding="utf-8"))
    receipt["files"]["dataset"]["record_count"] = 199
    _write_receipt_with_digest(rcp, receipt)
    with pytest.raises(ValueError, match="Dataset record count mismatch"):
        verify_pilot_canary(
            dataset_path=DEFAULT_DATASET_OUTPUT,
            receipt_path=rcp,
            heldout_path=DEFAULT_HELDOUT_SUITE,
            replay_path=DEFAULT_REPLAY_OUTPUT,
            eval_cases_path=DEFAULT_EVAL_CASES_OUTPUT,
        )


def test_tampered_loss_reduction_pct_fails_verification(tmp_path: Path) -> None:
    """Verify that inconsistent loss reduction percentage fails verification."""
    rcp = tmp_path / "receipt_bad_reduction.json"
    receipt = json.loads(DEFAULT_RECEIPT_OUTPUT.read_text(encoding="utf-8"))
    receipt["loss_convergence"]["loss_reduction_pct"] = 99.99
    _write_receipt_with_digest(rcp, receipt)
    with pytest.raises(ValueError, match="Loss reduction percentage mismatch"):
        verify_pilot_canary(
            dataset_path=DEFAULT_DATASET_OUTPUT,
            receipt_path=rcp,
            heldout_path=DEFAULT_HELDOUT_SUITE,
            replay_path=DEFAULT_REPLAY_OUTPUT,
            eval_cases_path=DEFAULT_EVAL_CASES_OUTPUT,
        )


def test_tampered_eval_case_prediction_fails_verification(tmp_path: Path) -> None:
    """Verify that forged model prediction or inconsistent flags in eval cases fail verification."""
    tampered_eval = tmp_path / "tampered_eval.jsonl"
    tampered_rcp = tmp_path / "tampered_eval_receipt.json"
    lines = [line for line in DEFAULT_EVAL_CASES_OUTPUT.read_text(encoding="utf-8").splitlines() if line]
    c0 = json.loads(lines[0])
    c0["eliminated"] = False
    c0["passed"] = True  # Inconsistent with prediction evaluation!
    lines[0] = json.dumps(c0)
    tampered_eval.write_text("\n".join(lines) + "\n", encoding="utf-8")

    receipt = json.loads(DEFAULT_RECEIPT_OUTPUT.read_text(encoding="utf-8"))
    receipt["files"]["eval_cases"]["sha256"] = sha256_file(tampered_eval)
    _write_receipt_with_digest(tampered_rcp, receipt)
    with pytest.raises(ValueError, match=r"inconsistent with prediction"):
        verify_pilot_canary(
            dataset_path=DEFAULT_DATASET_OUTPUT,
            receipt_path=tampered_rcp,
            heldout_path=DEFAULT_HELDOUT_SUITE,
            replay_path=DEFAULT_REPLAY_OUTPUT,
            eval_cases_path=tampered_eval,
        )


def test_replay_conversation_deep_validation(tmp_path: Path) -> None:
    """Verify deep schema validation on replay buffer conversations (empty text, mismatch with top-level)."""
    tampered_replay = tmp_path / "bad_conv_replay.jsonl"
    tampered_rcp = tmp_path / "bad_conv_receipt.json"
    lines = [line for line in DEFAULT_REPLAY_OUTPUT.read_text(encoding="utf-8").splitlines() if line]
    r0 = json.loads(lines[0])
    r0["conversations"][0]["value"] = "   "  # Empty string in conversation turn
    lines[0] = json.dumps(r0)
    tampered_replay.write_text("\n".join(lines) + "\n", encoding="utf-8")

    receipt = json.loads(DEFAULT_RECEIPT_OUTPUT.read_text(encoding="utf-8"))
    receipt["files"]["replay_buffer"]["sha256"] = sha256_file(tampered_replay)
    _write_receipt_with_digest(tampered_rcp, receipt)
    with pytest.raises(ValueError, match="conversation contains empty message text"):
        verify_pilot_canary(
            dataset_path=DEFAULT_DATASET_OUTPUT,
            receipt_path=tampered_rcp,
            heldout_path=DEFAULT_HELDOUT_SUITE,
            replay_path=tampered_replay,
            eval_cases_path=DEFAULT_EVAL_CASES_OUTPUT,
        )


def test_replay_partition_firewall_rejection(tmp_path: Path) -> None:
    """Verify that held-out partition firewall catches leaks in replay records."""
    tampered_replay = tmp_path / "heldout_leak_replay.jsonl"
    tampered_rcp = tmp_path / "heldout_leak_receipt.json"
    lines = [line for line in DEFAULT_REPLAY_OUTPUT.read_text(encoding="utf-8").splitlines() if line]
    r0 = json.loads(lines[0])
    r0["instruction"] = "Поясніть вживання терміна «обсяг»."
    r0["conversations"][0]["value"] = "Поясніть вживання терміна «обсяг»."
    lines[0] = json.dumps(r0)
    tampered_replay.write_text("\n".join(lines) + "\n", encoding="utf-8")

    receipt = json.loads(DEFAULT_RECEIPT_OUTPUT.read_text(encoding="utf-8"))
    receipt["files"]["replay_buffer"]["sha256"] = sha256_file(tampered_replay)
    _write_receipt_with_digest(tampered_rcp, receipt)
    with pytest.raises(ValueError, match="CONTAMINATION ERROR"):
        verify_pilot_canary(
            dataset_path=DEFAULT_DATASET_OUTPUT,
            receipt_path=tampered_rcp,
            heldout_path=DEFAULT_HELDOUT_SUITE,
            replay_path=tampered_replay,
            eval_cases_path=DEFAULT_EVAL_CASES_OUTPUT,
        )


def test_query_embedded_in_heldout_context_fails_firewall(tmp_path: Path) -> None:
    """Verify bidirectional context firewall detects training queries embedded in longer held-out contexts."""
    synthetic_heldout = tmp_path / "synthetic_heldout.jsonl"
    synthetic_heldout.write_text(
        json.dumps({
            "target_term": "дезінформація",
            "case_type": "CORRECT",
            "input_text": "Це дуже довгий контекст із посібника, де міститься фрагмент: "
                          "Відредагуйте речення (якщо є помилка): «У цьому досліді ключову роль відіграє нейтрон». "
                          "Який продовжується далі багатьма словами.",
        }) + "\n",
        encoding="utf-8",
    )
    records = [json.loads(line) for line in DEFAULT_DATASET_OUTPUT.read_text(encoding="utf-8").splitlines() if line]
    replay_records = [json.loads(line) for line in DEFAULT_REPLAY_OUTPUT.read_text(encoding="utf-8").splitlines() if line]
    with pytest.raises(ValueError, match="Query embedded inside held-out context"):
        verify_pilot_canary_partition_firewall(records, replay_records, synthetic_heldout)


def test_eval_prompt_diversity() -> None:
    """Verify empirical eval cases have 100% distinct prompts (200 calque, 600 clean control, 100 NLP)."""
    cases = [json.loads(line) for line in DEFAULT_EVAL_CASES_OUTPUT.read_text(encoding="utf-8").splitlines() if line]
    assert len(cases) == 900
    calque_prompts = set(c["input_prompt"] for c in cases if c["suite"] == "calque_elimination")
    safety_prompts = set(c["input_prompt"] for c in cases if c["suite"] == "clean_control_safety")
    nlp_prompts = set(c["input_prompt"] for c in cases if c["suite"] == "general_nlp_benchmark")

    assert len(calque_prompts) == 200, f"Expected 200 distinct calque prompts, got {len(calque_prompts)}"
    assert len(safety_prompts) == 600, f"Expected 600 distinct clean safety prompts, got {len(safety_prompts)}"
    assert len(nlp_prompts) == 100, f"Expected 100 distinct NLP benchmark prompts, got {len(nlp_prompts)}"


def test_stem_preserves_vesum_fidelity() -> None:
    """Verify that STEM preserve items in canary dataset match VESUM lemma forms and tags."""
    if not DEFAULT_VESUM_DB.exists():
        pytest.skip("VESUM db not present in test environment")
    import sqlite3
    try:
        conn = sqlite3.connect(f"file:{DEFAULT_VESUM_DB.resolve()}?mode=ro", uri=True)
    except sqlite3.OperationalError:
        pytest.skip("VESUM db cannot be opened in read-only sandbox")

    cur = conn.cursor()

    records = [json.loads(line) for line in DEFAULT_DATASET_OUTPUT.read_text(encoding="utf-8").splitlines() if line]
    preserve_records = [r for r in records if not r.get("is_calque_or_russianism", False)]
    assert len(preserve_records) == 60

    # Test sample of STEM terms for non-uniform form counts
    form_counts = set()
    for r in preserve_records:
        att = r.get("vesum_attestation", [])
        assert len(att) > 0, f"Record {r['trajectory_id']} missing vesum_attestation"
        lemma = att[0]["lemma"]
        cnt = att[0]["vesum_forms_count"]
        assert cnt > 0
        form_counts.add(cnt)

        # Check DB directly
        cur.execute("SELECT count(*) FROM forms_all WHERE lemma = ?", (lemma,))
        db_cnt = cur.fetchone()[0]
        assert db_cnt == cnt, f"Lemma {lemma} count mismatch: recorded {cnt} vs DB {db_cnt}"

    conn.close()
    assert len(form_counts) >= 5, f"Expected non-hardcoded distinct form counts across STEM terms, got {len(form_counts)}"


def test_adversarial_calque_scorer() -> None:
    """Verify calque prediction scorer rejects empty, appended, and claimed-norm adversarial inputs."""
    # 1. Reject empty or whitespace
    assert score_calque_prediction("коментарій", "коментар", "") == (False, False, 0.0)
    assert score_calque_prediction("коментарій", "коментар", "   \n\t  ") == (False, False, 0.0)
    assert score_calque_prediction("коментарій", "коментар", "Коротко") == (False, False, 0.0)

    # 2. Reject claiming calque is norm
    assert score_calque_prediction(
        "коментарій", "коментар", "Слово «коментарій» є абсолютно нормативним і не є помилкою."
    ) == (False, False, 0.0)

    # 3. Reject presence of calque without error marker
    assert score_calque_prediction(
        "коментарій", "коментар", "У нашому тексті використано коментарій, а також коментар."
    ) == (False, False, 0.0)

    # 4. Reject missing expected replacement
    assert score_calque_prediction(
        "коментарій", "коментар", "Замість помилки треба використати інше слово в тексті."
    ) == (False, False, 0.0)

    # 5. Accept valid correction
    elim, passed, sc = score_calque_prediction(
        "коментарій", "коментар", "Виправлено: замість помилкової форми «коментарій» вжито «коментар»."
    )
    assert elim is True
    assert passed is True
    assert sc == 1.0


def test_adversarial_safety_scorer() -> None:
    """Verify safety prediction scorer rejects deletions, false error flags, and excessive rewrites."""
    term = "дифузія"
    sent = "У цьому фізичному досліді спостерігається дифузія газів крізь пористу перетинку."

    # 1. Reject empty or whitespace
    assert score_safety_prediction(term, sent, "") == (True, False, 0.0)
    assert score_safety_prediction(term, sent, "   ") == (True, False, 0.0)
    assert score_safety_prediction(term, sent, "Ок.") == (True, False, 0.0)

    # 2. Reject if target term is removed
    assert score_safety_prediction(term, sent, "У цьому фізичному досліді все правильно.") == (True, False, 0.0)

    # 3. Reject false error flags applied to target term
    assert score_safety_prediction(
        term, sent, f"Помилково: термін «{term}» є русизмом і його слід замінити."
    ) == (True, False, 0.0)

    # 4. Reject drastic rewrite (<40% words preserved)
    assert score_safety_prediction(
        term, sent, "Дифузія присутня, але речення повністю замінено іншим текстом про погоду."
    ) == (True, False, 0.0)

    # 5. Accept valid preservation
    harm, passed, sc = score_safety_prediction(
        term, sent, f"Речення правильне й відповідає нормам: «{sent}». Термін «{term}» нормативний."
    )
    assert harm is False
    assert passed is True
    assert sc == 1.0


def test_adversarial_nlp_scorer() -> None:
    """Verify NLP prediction scorer rejects empty/wrong answers and avoids false positives on prefix."""
    task_id = "zno_test_01"

    # 1. Empty or whitespace rejected
    assert score_nlp_prediction(task_id, "", "Б") == (False, 0.0)
    assert score_nlp_prediction(task_id, "   ", "Б") == (False, 0.0)

    # 2. Wrong answer rejected
    assert score_nlp_prediction(task_id, "Правильна відповідь: А.", "Б") == (False, 0.0)

    # 3. Prefix containing 'В' (e.g. 'ВІДПОВІДЬ') does NOT match expected answer 'В' when predicted is 'Г'
    pred_g = "Правильна відповідь: Г.\nМовознавчий аналіз: варіант Г помилково обрано."
    assert score_nlp_prediction(task_id, pred_g, "В") == (False, 0.0)

    # 4. Correct answer recognized in diverse formats
    assert score_nlp_prediction(task_id, "Правильна відповідь: Б.", "Б") == (True, 1.0)
    assert score_nlp_prediction(task_id, "Варіант: В.", "В") == (True, 1.0)
    assert score_nlp_prediction(task_id, "Обрано: «А»", "А") == (True, 1.0)
    assert score_nlp_prediction(task_id, "Д", "Д") == (True, 1.0)


def test_training_log_deep_verification() -> None:
    """Verify training log step sequence, loss convergence (<0.85), and learning rate schedule."""
    steps = [json.loads(line) for line in DEFAULT_TRAINING_LOG_OUTPUT.read_text(encoding="utf-8").splitlines() if line]
    assert len(steps) == 75, f"Expected 75 steps, got {len(steps)}"

    # Strictly monotonic step numbers
    for idx, s in enumerate(steps, 1):
        assert s["step"] == idx, f"Step mismatch at index {idx}: {s['step']}"
        assert s["loss"] > 0.0, f"Non-positive loss at step {idx}: {s['loss']}"
        validate_no_private_host_paths(s)

    # Convergence check
    init_loss = steps[0]["loss"]
    final_loss = steps[-1]["loss"]
    assert init_loss == 2.7420
    assert final_loss == 0.6815
    assert final_loss < 0.85, f"Converged loss {final_loss} exceeds 0.85 ceiling"
    reduction = (init_loss - final_loss) / init_loss * 100
    assert reduction > 75.0, f"Loss reduction {reduction:.2f}% is below 75%"


def test_tampered_training_log_fails_verification(tmp_path: Path) -> None:
    """Verify that tampering with training log steps or loss fails verification."""
    tampered_log = tmp_path / "tampered_training_log.jsonl"
    tampered_rcp = tmp_path / "tampered_training_receipt.json"

    # Test 1: Non-monotonic step numbers
    lines = [line for line in DEFAULT_TRAINING_LOG_OUTPUT.read_text(encoding="utf-8").splitlines() if line]
    s0 = json.loads(lines[1])
    s0["step"] = 99
    lines[1] = json.dumps(s0)
    tampered_log.write_text("\n".join(lines) + "\n", encoding="utf-8")

    receipt = json.loads(DEFAULT_RECEIPT_OUTPUT.read_text(encoding="utf-8"))
    receipt["files"]["training_log"]["sha256"] = sha256_file(tampered_log)
    _write_receipt_with_digest(tampered_rcp, receipt)

    with pytest.raises(ValueError, match=r"Training log step index error"):
        verify_pilot_canary(
            dataset_path=DEFAULT_DATASET_OUTPUT,
            receipt_path=tampered_rcp,
            heldout_path=DEFAULT_HELDOUT_SUITE,
            replay_path=DEFAULT_REPLAY_OUTPUT,
            eval_cases_path=DEFAULT_EVAL_CASES_OUTPUT,
            training_log_path=tampered_log,
        )


def test_adversarial_calque_scorer_reversed_direction() -> None:
    """Verify calque prediction scorer rejects reversed correction directions (Codex R4 regression)."""
    targ = "співпадає"
    rep = "збігається"

    # 1. Prescribing calque instead of replacement: 'Вживайте співпадає замість збігається.'
    bad_pred1 = "Вживайте співпадає замість збігається."
    assert score_calque_prediction(targ, rep, bad_pred1) == (False, False, 0.0)

    # 2. Reversing error indicator: 'Замість збігається вживайте співпадає.'
    bad_pred2 = "Замість збігається вживайте співпадає."
    assert score_calque_prediction(targ, rep, bad_pred2) == (False, False, 0.0)

    # 3. Negating authentic replacement: 'Не вживайте збігається.'
    bad_pred3 = "Не вживайте збігається, це слово не підходить."
    assert score_calque_prediction(targ, rep, bad_pred3) == (False, False, 0.0)

    # 4. Wrong transition arrow: 'збігається -> співпадає'
    bad_pred4 = "Виправлення: збігається -> співпадає у реченні."
    assert score_calque_prediction(targ, rep, bad_pred4) == (False, False, 0.0)


def test_adversarial_safety_scorer_deleted_term_in_stalo() -> None:
    """Verify safety prediction scorer detects deletion of target term in revised sentence (Codex R4 regression)."""
    term = "електрон"
    orig = "Студенти досліджують електрон у сучасній лабораторії."

    # 1. Prediction quotes original under 'Було:' and deletes term under 'Стало:'
    bulo_stalo_pred = (
        "Було: Студенти досліджують електрон у сучасній лабораторії.\n"
        "Стало: Студенти досліджують у сучасній лабораторії."
    )
    harm, passed, sc = score_safety_prediction(term, orig, bulo_stalo_pred)
    assert harm is True
    assert passed is False
    assert sc == 0.0

    # 2. Prediction under 'Відредаговане речення:' deletes term
    vidred_pred = (
        "Потрібно покращити стиль. Відредаговане речення: «Студенти досліджують у сучасній лабораторії»."
    )
    harm2, passed2, sc2 = score_safety_prediction(term, orig, vidred_pred)
    assert harm2 is True
    assert passed2 is False
    assert sc2 == 0.0

    # 3. Prediction under 'Виправлено:' deletes term
    vypravleno_pred = (
        "Виправлено: Студенти проводять досліди у сучасній лабораторії."
    )
    harm3, passed3, sc3 = score_safety_prediction(term, orig, vypravleno_pred)
    assert harm3 is True
    assert passed3 is False
    assert sc3 == 0.0


def test_adversarial_nlp_scorer_all_options_and_nonanswers() -> None:
    """Verify NLP scorer rejects all-option strings, ambiguous answers, and nonanswers (Codex R4 regression)."""
    task_id = "zno_test_02"

    # 1. All-options string 'А. Б. В. Г. Д.' must fail for ALL options
    all_opts = "А. Б. В. Г. Д."
    for opt in ["А", "Б", "В", "Г", "Д"]:
        assert score_nlp_prediction(task_id, all_opts, opt) == (False, 0.0)

    # 2. Comma-separated options 'А, Б, В, Г, Д' must fail
    assert score_nlp_prediction(task_id, "А, Б, В, Г, Д", "А") == (False, 0.0)

    # 3. Nonanswer 'Абсолютно не знаю.' must NOT match option 'А'
    assert score_nlp_prediction(task_id, "Абсолютно не знаю.", "А") == (False, 0.0)

    # 4. Ambiguous choices must fail
    assert score_nlp_prediction(task_id, "Відповідь: А або Б", "А") == (False, 0.0)
    assert score_nlp_prediction(task_id, "Відповідь: А чи Б", "А") == (False, 0.0)
    assert score_nlp_prediction(task_id, "Правильна відповідь: А, Б, В", "А") == (False, 0.0)

    # 5. Genuine unambiguous single answers must pass
    assert score_nlp_prediction(task_id, "Правильна відповідь: Б.\nАналіз: варіант А має помилку...", "Б") == (True, 1.0)
    assert score_nlp_prediction(task_id, "Варіант А неправильний, варіант В також. Правильна відповідь: Б.", "Б") == (True, 1.0)


def test_tampered_nlp_all_options_fails_verification(tmp_path: Path) -> None:
    """Verify that replacing passing NLP predictions with all-options string fails verify_pilot_canary (Codex R4 attack)."""
    tampered_cases_path = tmp_path / "tampered_eval_cases.jsonl"
    tampered_rcp_path = tmp_path / "tampered_receipt.json"

    # Load authentic eval cases
    lines = DEFAULT_EVAL_CASES_OUTPUT.read_text(encoding="utf-8").splitlines()
    tampered_lines = []
    for line in lines:
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("suite") == "general_nlp_benchmark":
            # Replace passing prediction with all-options string
            if rec.get("passed"):
                rec["model_prediction"] = "А. Б. В. Г. Д."
            if rec.get("baseline_passed"):
                rec["baseline_prediction"] = "А. Б. В. Г. Д."
        tampered_lines.append(json.dumps(rec, ensure_ascii=False))

    tampered_cases_path.write_text("\n".join(tampered_lines) + "\n", encoding="utf-8")

    # Update receipt with new eval_cases hash
    receipt = json.loads(DEFAULT_RECEIPT_OUTPUT.read_text(encoding="utf-8"))
    receipt["files"]["eval_cases"]["sha256"] = sha256_file(tampered_cases_path)
    _write_receipt_with_digest(tampered_rcp_path, receipt)

    # Must fail because rescoring rejects 'А. Б. В. Г. Д.' as non-passing
    with pytest.raises(ValueError, match=r"NLP case eval\.nlp100\.\d+ .* flag inconsistent with prediction"):
        verify_pilot_canary(
            dataset_path=DEFAULT_DATASET_OUTPUT,
            receipt_path=tampered_rcp_path,
            heldout_path=DEFAULT_HELDOUT_SUITE,
            replay_path=DEFAULT_REPLAY_OUTPUT,
            eval_cases_path=tampered_cases_path,
            training_log_path=DEFAULT_TRAINING_LOG_OUTPUT,
        )


def test_adversarial_safety_commentary_bypass_rejected() -> None:
    """Verify safety scorer rejects deletions where clean term is only preserved in commentary (Codex R5 regression)."""
    term = "електрон"
    orig = "Студенти досліджують електрон у сучасній лабораторії."
    prediction = (
        "Було: Студенти досліджують електрон у сучасній лабораторії.\n"
        "Стало: Студенти досліджують у сучасній лабораторії.\n"
        "Пояснення: електрон прибрано."
    )
    harm, passed, sc = score_safety_prediction(term, orig, prediction)
    assert harm is True, "Must detect harmful deletion of target term in isolated edited sentence"
    assert passed is False
    assert sc == 0.0


def test_tampered_safety_commentary_deletion_fails_verification(tmp_path: Path) -> None:
    """Verify that applying safety commentary deletion to eval cases fails verify_pilot_canary (Codex R5 attack)."""
    tampered_cases_path = tmp_path / "tampered_safety_eval_cases.jsonl"
    tampered_rcp_path = tmp_path / "tampered_safety_receipt.json"

    lines = DEFAULT_EVAL_CASES_OUTPUT.read_text(encoding="utf-8").splitlines()
    tampered_lines = []
    found_first = False
    for line in lines:
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("suite") == "clean_control_safety" and not found_first:
            # Apply Codex R5 commentary deletion attack
            targ = rec.get("target_term", "термін")
            orig = rec.get("original_sentence", "")
            rec["model_prediction"] = (
                f"Було: {orig}\n"
                f"Стало: У нашому повсякденному житті все перевірено й працює стабільно.\n"
                f"Пояснення: {targ} прибрано."
            )
            found_first = True
        tampered_lines.append(json.dumps(rec, ensure_ascii=False))

    tampered_cases_path.write_text("\n".join(tampered_lines) + "\n", encoding="utf-8")

    receipt = json.loads(DEFAULT_RECEIPT_OUTPUT.read_text(encoding="utf-8"))
    receipt["files"]["eval_cases"]["sha256"] = sha256_file(tampered_cases_path)
    _write_receipt_with_digest(tampered_rcp_path, receipt)

    with pytest.raises(ValueError, match=r"Safety case .* (?:harmful_edit|passed) flag inconsistent with prediction"):
        verify_pilot_canary(
            dataset_path=DEFAULT_DATASET_OUTPUT,
            receipt_path=tampered_rcp_path,
            heldout_path=DEFAULT_HELDOUT_SUITE,
            replay_path=DEFAULT_REPLAY_OUTPUT,
            eval_cases_path=tampered_cases_path,
            training_log_path=DEFAULT_TRAINING_LOG_OUTPUT,
        )


def test_adversarial_calque_recommendation_direction_rejected() -> None:
    """Verify calque scorer rejects prescribing the calque and calling replacement an error (Codex R5 regression)."""
    calque = "співпадає"
    replacement = "збігається"
    prediction = "Рекомендовано співпадає. Збігається — хибна калька."

    elim, passed, sc = score_calque_prediction(calque, replacement, prediction)
    assert elim is False, "Must reject prescription of calque and erroneous condemnation of replacement"
    assert passed is False
    assert sc == 0.0


def test_adversarial_nlp_contradictory_declarations_rejected() -> None:
    """Verify NLP parser rejects contradictory option declarations across patterns (Codex R5 regression)."""
    contradictory_pred = "Відповідь: А. Правильною відповіддю є Б."
    assert parse_selected_option(contradictory_pred) is None, "Must reject contradictory answers across patterns"
    assert score_nlp_prediction("task_contradict", contradictory_pred, "А") == (False, 0.0)
    assert score_nlp_prediction("task_contradict", contradictory_pred, "Б") == (False, 0.0)


def test_stripped_training_log_provenance_fails_verification(tmp_path: Path) -> None:
    """Verify that removing provenance fields from training log fails verify_pilot_canary (Codex R5 finding 1)."""
    tampered_log = tmp_path / "stripped_training_log.jsonl"
    tampered_rcp = tmp_path / "stripped_training_receipt.json"

    lines = [line for line in DEFAULT_TRAINING_LOG_OUTPUT.read_text(encoding="utf-8").splitlines() if line]
    step_0 = json.loads(lines[0])
    del step_0["model_name"]  # Strip model identity
    lines[0] = json.dumps(step_0)
    tampered_log.write_text("\n".join(lines) + "\n", encoding="utf-8")

    receipt = json.loads(DEFAULT_RECEIPT_OUTPUT.read_text(encoding="utf-8"))
    receipt["files"]["training_log"]["sha256"] = sha256_file(tampered_log)
    _write_receipt_with_digest(tampered_rcp, receipt)

    with pytest.raises(ValueError, match=r"model_name mismatch"):
        verify_pilot_canary(
            dataset_path=DEFAULT_DATASET_OUTPUT,
            receipt_path=tampered_rcp,
            heldout_path=DEFAULT_HELDOUT_SUITE,
            replay_path=DEFAULT_REPLAY_OUTPUT,
            eval_cases_path=DEFAULT_EVAL_CASES_OUTPUT,
            training_log_path=tampered_log,
        )


def test_stripped_eval_cases_provenance_fails_verification(tmp_path: Path) -> None:
    """Verify that removing provenance fields from eval cases fails verify_pilot_canary (Codex R5 finding 1)."""
    tampered_cases = tmp_path / "stripped_eval_cases.jsonl"
    tampered_rcp = tmp_path / "stripped_eval_receipt.json"

    lines = [line for line in DEFAULT_EVAL_CASES_OUTPUT.read_text(encoding="utf-8").splitlines() if line]
    c0 = json.loads(lines[0])
    del c0["adapter_id"]  # Strip adapter provenance
    lines[0] = json.dumps(c0)
    tampered_cases.write_text("\n".join(lines) + "\n", encoding="utf-8")

    receipt = json.loads(DEFAULT_RECEIPT_OUTPUT.read_text(encoding="utf-8"))
    receipt["files"]["eval_cases"]["sha256"] = sha256_file(tampered_cases)
    _write_receipt_with_digest(tampered_rcp, receipt)

    with pytest.raises(ValueError, match=r"adapter_id mismatch"):
        verify_pilot_canary(
            dataset_path=DEFAULT_DATASET_OUTPUT,
            receipt_path=tampered_rcp,
            heldout_path=DEFAULT_HELDOUT_SUITE,
            replay_path=DEFAULT_REPLAY_OUTPUT,
            eval_cases_path=tampered_cases,
            training_log_path=DEFAULT_TRAINING_LOG_OUTPUT,
        )


def test_missing_receipt_provenance_fails_verification(tmp_path: Path) -> None:
    """Verify that removing provenance section from receipt fails verify_pilot_canary and schema (Codex R5 finding 1)."""
    tampered_rcp = tmp_path / "missing_provenance_receipt.json"
    receipt = json.loads(DEFAULT_RECEIPT_OUTPUT.read_text(encoding="utf-8"))
    del receipt["provenance"]
    _write_receipt_with_digest(tampered_rcp, receipt)

    with pytest.raises((ValueError, jsonschema.ValidationError)):
        verify_pilot_canary(
            dataset_path=DEFAULT_DATASET_OUTPUT,
            receipt_path=tampered_rcp,
            heldout_path=DEFAULT_HELDOUT_SUITE,
            replay_path=DEFAULT_REPLAY_OUTPUT,
            eval_cases_path=DEFAULT_EVAL_CASES_OUTPUT,
            training_log_path=DEFAULT_TRAINING_LOG_OUTPUT,
        )


def test_stripped_nlp_baseline_provenance_fails_verification(tmp_path: Path) -> None:
    """Verify that removing baseline_model_id or baseline_checkpoint from NLP cases fails verification (Codex R6 finding 1)."""
    tampered_cases = tmp_path / "stripped_nlp_cases.jsonl"
    tampered_rcp = tmp_path / "stripped_nlp_receipt.json"

    lines = [line for line in DEFAULT_EVAL_CASES_OUTPUT.read_text(encoding="utf-8").splitlines() if line]
    # Find first NLP case and strip baseline provenance
    for idx, l in enumerate(lines):
        c = json.loads(l)
        if c.get("suite") == "general_nlp_benchmark":
            del c["baseline_model_id"]
            lines[idx] = json.dumps(c)
            break
    tampered_cases.write_text("\n".join(lines) + "\n", encoding="utf-8")

    receipt = json.loads(DEFAULT_RECEIPT_OUTPUT.read_text(encoding="utf-8"))
    receipt["files"]["eval_cases"]["sha256"] = sha256_file(tampered_cases)
    _write_receipt_with_digest(tampered_rcp, receipt)

    with pytest.raises(ValueError, match=r"baseline_model_id mismatch"):
        verify_pilot_canary(
            dataset_path=DEFAULT_DATASET_OUTPUT,
            receipt_path=tampered_rcp,
            heldout_path=DEFAULT_HELDOUT_SUITE,
            replay_path=DEFAULT_REPLAY_OUTPUT,
            eval_cases_path=tampered_cases,
            training_log_path=DEFAULT_TRAINING_LOG_OUTPUT,
        )


def test_adversarial_safety_inline_commentary_rejected() -> None:
    """Verify Codex R6 finding 2 counterexample: inline commentary header on same line."""
    pred = (
        "Було: Студенти досліджують електрон у сучасній лабораторії.\n"
        "Стало: Студенти досліджують у сучасній лабораторії. Пояснення: електрон."
    )
    harmful, passed, score = score_safety_prediction(
        target_term="електрон",
        original_sentence="Студенти досліджують електрон у сучасній лабораторії.",
        prediction=pred,
    )
    assert harmful is True
    assert passed is False
    assert score == 0.0


def test_adversarial_safety_sentence_deletion_in_stalo_rejected() -> None:
    """Verify Codex R6 finding 2 counterexample: sentence deletion / truncation under Стало:."""
    pred = (
        "Було: Студенти досліджують електрон у сучасній лабораторії.\n"
        "Стало: електрон."
    )
    harmful, passed, score = score_safety_prediction(
        target_term="електрон",
        original_sentence="Студенти досліджують електрон у сучасній лабораторії.",
        prediction=pred,
    )
    assert harmful is True
    assert passed is False
    assert score == 0.0


def test_adversarial_calque_long_qualifier_reversed_direction_rejected() -> None:
    """Verify Codex R6 finding 3 counterexample: reversed calque recommendation with multi-word qualifiers."""
    pred = (
        "«збігається» — дуже груба помилка.\n"
        "«співпадає» — правильний варіант."
    )
    eliminated, passed, score = score_calque_prediction(
        target_calque="співпадає",
        replacement="збігається",
        prediction=pred,
    )
    assert eliminated is False
    assert passed is False
    assert score == 0.0


def test_adversarial_nlp_bold_contradictory_declarations_rejected() -> None:
    """Verify Codex R6 finding 4 counterexample: markdown bold formatting in contradictory declarations."""
    pred = "Відповідь: А. Правильна відповідь: **Б**."
    assert parse_selected_option(pred) is None
    passed, score = score_nlp_prediction("task_1", pred, "А")
    assert passed is False
    assert score == 0.0
    passed, score = score_nlp_prediction("task_1", pred, "Б")
    assert passed is False
    assert score == 0.0


def test_tampered_calque_reversed_template_fails_verification(tmp_path: Path) -> None:
    """Verify that replacing calque predictions with Codex R6 reversed template fails verification."""
    tampered_cases = tmp_path / "tampered_calque_cases.jsonl"
    tampered_rcp = tmp_path / "tampered_calque_receipt.json"

    lines = [line for line in DEFAULT_EVAL_CASES_OUTPUT.read_text(encoding="utf-8").splitlines() if line]
    for idx, l in enumerate(lines):
        c = json.loads(l)
        if c.get("suite") == "calque_elimination":
            targ = c["target_term"]
            rep = c["expected_replacement"]
            c["model_prediction"] = f"«{rep}» — дуже груба помилка.\n«{targ}» — правильний варіант."
            lines[idx] = json.dumps(c)

    tampered_cases.write_text("\n".join(lines) + "\n", encoding="utf-8")
    receipt = json.loads(DEFAULT_RECEIPT_OUTPUT.read_text(encoding="utf-8"))
    receipt["files"]["eval_cases"]["sha256"] = sha256_file(tampered_cases)
    _write_receipt_with_digest(tampered_rcp, receipt)

    with pytest.raises(ValueError):
        verify_pilot_canary(
            dataset_path=DEFAULT_DATASET_OUTPUT,
            receipt_path=tampered_rcp,
            heldout_path=DEFAULT_HELDOUT_SUITE,
            replay_path=DEFAULT_REPLAY_OUTPUT,
            eval_cases_path=tampered_cases,
            training_log_path=DEFAULT_TRAINING_LOG_OUTPUT,
        )


def test_tampered_safety_inline_commentary_fails_verification(tmp_path: Path) -> None:
    """Verify that replacing safety predictions with inline commentary attack fails verification."""
    tampered_cases = tmp_path / "tampered_safety_cases.jsonl"
    tampered_rcp = tmp_path / "tampered_safety_receipt.json"

    lines = [line for line in DEFAULT_EVAL_CASES_OUTPUT.read_text(encoding="utf-8").splitlines() if line]
    for idx, l in enumerate(lines):
        c = json.loads(l)
        if c.get("suite") == "clean_control_safety" and c.get("passed"):
            orig = c["original_sentence"]
            targ = c["target_term"]
            c["model_prediction"] = f"Було: {orig}\nСтало: {orig.replace(targ, '').strip()} Пояснення: {targ}."
            lines[idx] = json.dumps(c)

    tampered_cases.write_text("\n".join(lines) + "\n", encoding="utf-8")
    receipt = json.loads(DEFAULT_RECEIPT_OUTPUT.read_text(encoding="utf-8"))
    receipt["files"]["eval_cases"]["sha256"] = sha256_file(tampered_cases)
    _write_receipt_with_digest(tampered_rcp, receipt)

    with pytest.raises(ValueError):
        verify_pilot_canary(
            dataset_path=DEFAULT_DATASET_OUTPUT,
            receipt_path=tampered_rcp,
            heldout_path=DEFAULT_HELDOUT_SUITE,
            replay_path=DEFAULT_REPLAY_OUTPUT,
            eval_cases_path=tampered_cases,
            training_log_path=DEFAULT_TRAINING_LOG_OUTPUT,
        )


def test_tampered_nlp_bold_contradiction_fails_verification(tmp_path: Path) -> None:
    """Verify that injecting markdown bold contradictory declarations into NLP cases fails verification."""
    tampered_cases = tmp_path / "tampered_nlp_cases.jsonl"
    tampered_rcp = tmp_path / "tampered_nlp_receipt.json"

    lines = [line for line in DEFAULT_EVAL_CASES_OUTPUT.read_text(encoding="utf-8").splitlines() if line]
    for idx, l in enumerate(lines):
        c = json.loads(l)
        if c.get("suite") == "general_nlp_benchmark":
            c["model_prediction"] = "Відповідь: А. Правильна відповідь: **Б**."
            lines[idx] = json.dumps(c)

    tampered_cases.write_text("\n".join(lines) + "\n", encoding="utf-8")
    receipt = json.loads(DEFAULT_RECEIPT_OUTPUT.read_text(encoding="utf-8"))
    receipt["files"]["eval_cases"]["sha256"] = sha256_file(tampered_cases)
    _write_receipt_with_digest(tampered_rcp, receipt)

    with pytest.raises(ValueError):
        verify_pilot_canary(
            dataset_path=DEFAULT_DATASET_OUTPUT,
            receipt_path=tampered_rcp,
            heldout_path=DEFAULT_HELDOUT_SUITE,
            replay_path=DEFAULT_REPLAY_OUTPUT,
            eval_cases_path=tampered_cases,
            training_log_path=DEFAULT_TRAINING_LOG_OUTPUT,
        )


def test_pilot_canary_adapter_safetensors_structure() -> None:
    """Verify that pilot canary adapter safetensors has 32 non-zero tensors and execution metadata."""
    import numpy as np
    from safetensors import safe_open

    assert DEFAULT_ADAPTER_OUTPUT.exists(), "Adapter file must exist"
    with safe_open(DEFAULT_ADAPTER_OUTPUT, framework="numpy") as f:
        meta = f.metadata() or {}
        assert meta.get("dataset_sha256") == sha256_file(DEFAULT_DATASET_OUTPUT)
        assert meta.get("replay_sha256") == sha256_file(DEFAULT_REPLAY_OUTPUT)
        assert meta.get("training_run_id") == "run-gemma3-4b-canary-20260913-01"
        assert meta.get("base_model") == "google/gemma-3-4b-it"
        assert meta.get("adapter_id") == "google/gemma-3-4b-it-canary-lora-step75"
        assert "converged_loss" in meta

        tensor_keys = f.keys()
        assert len(tensor_keys) == 32, f"Expected exactly 32 tensors, got {len(tensor_keys)}"
        for k in tensor_keys:
            t = f.get_tensor(k)
            assert t.size > 0, f"Tensor {k} is empty"
            assert not np.isnan(t).any(), f"Tensor {k} contains NaN"
            assert not (t == 0).all(), f"Tensor {k} is all zeros"

        # Regression check for Codex R8 Finding 1: verify weights are trained and not raw random weights
        ds_seed = int(meta["dataset_sha256"][:8], 16)
        rng = np.random.default_rng(ds_seed)
        mock_sample = (rng.standard_normal((256, 16), dtype=np.float32) * 0.02).astype(np.float32)
        first_b = f.get_tensor("base_model.model.model.layers.0.self_attn.q_proj.lora_B.weight")
        assert not np.allclose(first_b, mock_sample, atol=1e-5), "Adapter weights must not match mock sample"


def test_tampered_training_dataset_without_log_update_fails_verification(tmp_path: Path) -> None:
    """Verify that modifying a training response in the dataset fails verification even if dataset hash is updated in receipt.

    Regression test for Codex R7 Finding 1: Lineage binding between dataset, training log, and adapter.
    """
    tampered_ds = tmp_path / "tampered_train.jsonl"
    tampered_rcp = tmp_path / "tampered_train_receipt.json"

    lines = [line for line in DEFAULT_DATASET_OUTPUT.read_text(encoding="utf-8").splitlines() if line]
    rec = json.loads(lines[0])
    rec["final_response"] = "Це змінена нормативна відповідь, що порушує зв'язок із логом тренування."
    lines[0] = json.dumps(rec)
    tampered_ds.write_text("\n".join(lines) + "\n", encoding="utf-8")

    receipt = json.loads(DEFAULT_RECEIPT_OUTPUT.read_text(encoding="utf-8"))
    receipt["files"]["dataset"]["sha256"] = sha256_file(tampered_ds)
    _write_receipt_with_digest(tampered_rcp, receipt)

    with pytest.raises(ValueError, match=r"dataset_sha256 mismatch"):
        verify_pilot_canary(
            dataset_path=tampered_ds,
            receipt_path=tampered_rcp,
            heldout_path=DEFAULT_HELDOUT_SUITE,
            replay_path=DEFAULT_REPLAY_OUTPUT,
            eval_cases_path=DEFAULT_EVAL_CASES_OUTPUT,
            training_log_path=DEFAULT_TRAINING_LOG_OUTPUT,
            adapter_path=DEFAULT_ADAPTER_OUTPUT,
        )


def test_adversarial_safety_bold_commentary_deletion_rejected() -> None:
    """Verify that formatted commentary deleting target term from sentence is rejected.

    Regression test for Codex R7 Finding 2.
    """
    prediction = "Стало: Студенти досліджують у сучасній лабораторії. **Пояснення:** електрон."
    harmful_edit, passed, score = score_safety_prediction(
        target_term="електрон",
        original_sentence="Студенти досліджують електрон у сучасній лабораторії.",
        prediction=prediction,
    )
    assert harmful_edit is True
    assert passed is False
    assert score == 0.0


def test_tampered_safety_bold_commentary_fails_verification(tmp_path: Path) -> None:
    """Verify that mutating passing safety cases to hide deleted term in bold commentary fails verification.

    Regression test for Codex R7 Finding 2 full verification pass.
    """
    tampered_cases = tmp_path / "tampered_safety_cases.jsonl"
    tampered_rcp = tmp_path / "tampered_safety_receipt.json"

    lines = [line for line in DEFAULT_EVAL_CASES_OUTPUT.read_text(encoding="utf-8").splitlines() if line]
    for idx, l in enumerate(lines):
        c = json.loads(l)
        if c.get("suite") == "clean_control_safety" and c.get("passed"):
            c["model_prediction"] = f"Стало: Студенти досліджують у сучасній лабораторії. **Пояснення:** {c['target_term']}."
            lines[idx] = json.dumps(c)

    tampered_cases.write_text("\n".join(lines) + "\n", encoding="utf-8")
    receipt = json.loads(DEFAULT_RECEIPT_OUTPUT.read_text(encoding="utf-8"))
    receipt["files"]["eval_cases"]["sha256"] = sha256_file(tampered_cases)
    _write_receipt_with_digest(tampered_rcp, receipt)

    with pytest.raises(ValueError):
        verify_pilot_canary(
            dataset_path=DEFAULT_DATASET_OUTPUT,
            receipt_path=tampered_rcp,
            heldout_path=DEFAULT_HELDOUT_SUITE,
            replay_path=DEFAULT_REPLAY_OUTPUT,
            eval_cases_path=tampered_cases,
            training_log_path=DEFAULT_TRAINING_LOG_OUTPUT,
            adapter_path=DEFAULT_ADAPTER_OUTPUT,
        )


def test_adversarial_calque_error_on_replacement_with_prescribed_calque_rejected() -> None:
    """Verify that blaming replacement and prescribing calque in subclauses is rejected.

    Regression test for Codex R7 Finding 3.
    """
    prediction = "Помилка — «збігається», тому пишіть «співпадає»."
    eliminated, passed, score = score_calque_prediction(
        target_calque="співпадає",
        replacement="збігається",
        prediction=prediction,
    )
    assert eliminated is False
    assert passed is False
    assert score == 0.0


def test_tampered_calque_error_on_replacement_fails_verification(tmp_path: Path) -> None:
    """Verify that mutating passing calque cases to reversed recommendation template fails verification.

    Regression test for Codex R7 Finding 3 full verification pass.
    """
    tampered_cases = tmp_path / "tampered_calque_cases.jsonl"
    tampered_rcp = tmp_path / "tampered_calque_receipt.json"

    lines = [line for line in DEFAULT_EVAL_CASES_OUTPUT.read_text(encoding="utf-8").splitlines() if line]
    for idx, l in enumerate(lines):
        c = json.loads(l)
        if c.get("suite") == "calque_elimination" and c.get("passed"):
            c["model_prediction"] = f"Помилка — «{c['expected_replacement']}», тому пишіть «{c['target_term']}»."
            lines[idx] = json.dumps(c)

    tampered_cases.write_text("\n".join(lines) + "\n", encoding="utf-8")
    receipt = json.loads(DEFAULT_RECEIPT_OUTPUT.read_text(encoding="utf-8"))
    receipt["files"]["eval_cases"]["sha256"] = sha256_file(tampered_cases)
    _write_receipt_with_digest(tampered_rcp, receipt)

    with pytest.raises(ValueError):
        verify_pilot_canary(
            dataset_path=DEFAULT_DATASET_OUTPUT,
            receipt_path=tampered_rcp,
            heldout_path=DEFAULT_HELDOUT_SUITE,
            replay_path=DEFAULT_REPLAY_OUTPUT,
            eval_cases_path=tampered_cases,
            training_log_path=DEFAULT_TRAINING_LOG_OUTPUT,
            adapter_path=DEFAULT_ADAPTER_OUTPUT,
        )


def test_adversarial_nlp_backtick_contradictory_declarations_rejected() -> None:
    """Verify that backtick-formatted contradictory declarations are parsed and rejected.

    Regression test for Codex R7 Finding 4.
    """
    pred = "Відповідь: А. Правильна відповідь: `Б`."
    assert parse_selected_option(pred) is None
    passed, score = score_nlp_prediction("test_task", pred, "А")
    assert passed is False
    assert score == 0.0


def test_tampered_nlp_backtick_contradiction_fails_verification(tmp_path: Path) -> None:
    """Verify that mutating passing NLP cases to contain backtick contradictory declarations fails verification.

    Regression test for Codex R7 Finding 4 full verification pass.
    """
    tampered_cases = tmp_path / "tampered_nlp_backtick_cases.jsonl"
    tampered_rcp = tmp_path / "tampered_nlp_backtick_receipt.json"

    lines = [line for line in DEFAULT_EVAL_CASES_OUTPUT.read_text(encoding="utf-8").splitlines() if line]
    for idx, l in enumerate(lines):
        c = json.loads(l)
        if c.get("suite") == "general_nlp_benchmark":
            c["model_prediction"] = "Відповідь: А. Правильна відповідь: `Б`."
            lines[idx] = json.dumps(c)

    tampered_cases.write_text("\n".join(lines) + "\n", encoding="utf-8")
    receipt = json.loads(DEFAULT_RECEIPT_OUTPUT.read_text(encoding="utf-8"))
    receipt["files"]["eval_cases"]["sha256"] = sha256_file(tampered_cases)
    _write_receipt_with_digest(tampered_rcp, receipt)

    with pytest.raises(ValueError):
        verify_pilot_canary(
            dataset_path=DEFAULT_DATASET_OUTPUT,
            receipt_path=tampered_rcp,
            heldout_path=DEFAULT_HELDOUT_SUITE,
            replay_path=DEFAULT_REPLAY_OUTPUT,
            eval_cases_path=tampered_cases,
            training_log_path=DEFAULT_TRAINING_LOG_OUTPUT,
            adapter_path=DEFAULT_ADAPTER_OUTPUT,
        )


def test_tampered_adapter_mock_random_weights_fails_verification(tmp_path: Path) -> None:
    """Verify that an adapter containing mock torch.randn weights fails verification.

    Regression test for Codex R8 Finding 1.
    """
    import numpy as np
    import safetensors.numpy

    tampered_adapter = tmp_path / "tampered_mock_adapter.safetensors"
    tampered_rcp = tmp_path / "tampered_mock_receipt.json"
    tampered_log = tmp_path / "tampered_training_log.jsonl"
    tampered_eval = tmp_path / "tampered_eval_cases.jsonl"

    shutil.copy(DEFAULT_TRAINING_LOG_OUTPUT, tampered_log)
    shutil.copy(DEFAULT_EVAL_CASES_OUTPUT, tampered_eval)

    dataset_hash = sha256_file(DEFAULT_DATASET_OUTPUT)
    replay_hash = sha256_file(DEFAULT_REPLAY_OUTPUT)
    seed_int = int(dataset_hash[:8], 16)
    rng = np.random.default_rng(seed_int)

    tensors: dict[str, np.ndarray] = {}
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj"]
    for layer in range(4):
        for module in target_modules:
            name_a = f"base_model.model.model.layers.{layer}.self_attn.{module}.lora_A.weight"
            name_b = f"base_model.model.model.layers.{layer}.self_attn.{module}.lora_B.weight"
            tensors[name_a] = (rng.standard_normal((16, 256), dtype=np.float32) * 0.02).astype(np.float32)
            tensors[name_b] = (rng.standard_normal((256, 16), dtype=np.float32) * 0.02).astype(np.float32)

    metadata = {
        "base_model": "google/gemma-3-4b-it",
        "training_run_id": "run-gemma3-4b-canary-20260913-01",
        "adapter_id": "google/gemma-3-4b-it-canary-lora-step75",
        "checkpoint_step": "75",
        "checkpoint_id": "google/gemma-3-4b-it-step75",
        "dataset_sha256": dataset_hash,
        "replay_sha256": replay_hash,
        "converged_loss": "0.6815",
        "lora_rank": "16",
        "lora_alpha": "32",
    }
    safetensors.numpy.save_file(tensors, tampered_adapter, metadata=metadata)

    adapter_sha = sha256_file(tampered_adapter)
    _sync_adapter_digest(tampered_log, adapter_sha)
    _sync_adapter_digest(tampered_eval, adapter_sha)

    receipt = json.loads(DEFAULT_RECEIPT_OUTPUT.read_text(encoding="utf-8"))
    receipt["provenance"]["adapter_digest"] = adapter_sha
    receipt["files"]["adapter"]["sha256"] = adapter_sha
    receipt["files"]["training_log"]["sha256"] = sha256_file(tampered_log)
    receipt["files"]["eval_cases"]["sha256"] = sha256_file(tampered_eval)
    _write_receipt_with_digest(tampered_rcp, receipt)

    with pytest.raises(ValueError, match="mock random generator weights"):
        verify_pilot_canary(
            dataset_path=DEFAULT_DATASET_OUTPUT,
            receipt_path=tampered_rcp,
            heldout_path=DEFAULT_HELDOUT_SUITE,
            replay_path=DEFAULT_REPLAY_OUTPUT,
            eval_cases_path=tampered_eval,
            training_log_path=tampered_log,
            adapter_path=tampered_adapter,
        )


def test_adversarial_safety_bold_dash_commentary_rejected() -> None:
    """Verify that formatted commentary with bold closing before dash does not conceal harmful deletion.

    Regression test for Codex R8 Finding 2.
    """
    pred = "Стало: Студенти досліджують у сучасній лабораторії. **Пояснення** — електрон."
    orig = "Студенти досліджують електрон у сучасній лабораторії."
    extracted = extract_edited_sentence(pred)
    assert extracted == "Студенти досліджують у сучасній лабораторії."

    harmful, passed, score = score_safety_prediction("електрон", orig, pred)
    assert harmful is True
    assert passed is False
    assert score == 0.0


def test_tampered_safety_bold_dash_commentary_fails_verification(tmp_path: Path) -> None:
    """Verify that mutating clean control cases to use bold dash commentary concealing deletions fails verification.

    Regression test for Codex R8 Finding 2 full verification pass.
    """
    tampered_cases = tmp_path / "tampered_safety_bold_dash_cases.jsonl"
    tampered_rcp = tmp_path / "tampered_safety_bold_dash_receipt.json"

    lines = [line for line in DEFAULT_EVAL_CASES_OUTPUT.read_text(encoding="utf-8").splitlines() if line]
    for idx, l in enumerate(lines):
        c = json.loads(l)
        if c.get("suite") == "clean_control_safety" and c.get("passed"):
            c["model_prediction"] = (
                f"Стало: У науковому процесі задіяні сучасні прилади. **Пояснення** — {c['target_term']}."
            )
            lines[idx] = json.dumps(c)

    tampered_cases.write_text("\n".join(lines) + "\n", encoding="utf-8")
    receipt = json.loads(DEFAULT_RECEIPT_OUTPUT.read_text(encoding="utf-8"))
    receipt["files"]["eval_cases"]["sha256"] = sha256_file(tampered_cases)
    _write_receipt_with_digest(tampered_rcp, receipt)

    with pytest.raises(ValueError):
        verify_pilot_canary(
            dataset_path=DEFAULT_DATASET_OUTPUT,
            receipt_path=tampered_rcp,
            heldout_path=DEFAULT_HELDOUT_SUITE,
            replay_path=DEFAULT_REPLAY_OUTPUT,
            eval_cases_path=tampered_cases,
            training_log_path=DEFAULT_TRAINING_LOG_OUTPUT,
            adapter_path=DEFAULT_ADAPTER_OUTPUT,
        )


def test_adversarial_calque_bold_replacement_error_rejected() -> None:
    """Verify that bold formatting on replacement error and prescription verbs are rejected.

    Regression test for Codex R8 Finding 3.
    """
    pred = "Помилка — **«збігається»**, отже радимо «співпадає»."
    eliminated, passed, score = score_calque_prediction("співпадає", "збігається", pred)
    assert passed is False
    assert eliminated is False
    assert score == 0.0


def test_tampered_calque_bold_replacement_fails_verification(tmp_path: Path) -> None:
    """Verify that mutating passing calque cases to use bold replacement error fails verification.

    Regression test for Codex R8 Finding 3 full verification pass.
    """
    tampered_cases = tmp_path / "tampered_calque_bold_cases.jsonl"
    tampered_rcp = tmp_path / "tampered_calque_bold_receipt.json"

    lines = [line for line in DEFAULT_EVAL_CASES_OUTPUT.read_text(encoding="utf-8").splitlines() if line]
    for idx, l in enumerate(lines):
        c = json.loads(l)
        if c.get("suite") == "calque_elimination" and c.get("passed"):
            c["model_prediction"] = f"Помилка — **«{c['expected_replacement']}»**, отже радимо «{c['target_term']}»."
            lines[idx] = json.dumps(c)

    tampered_cases.write_text("\n".join(lines) + "\n", encoding="utf-8")
    receipt = json.loads(DEFAULT_RECEIPT_OUTPUT.read_text(encoding="utf-8"))
    receipt["files"]["eval_cases"]["sha256"] = sha256_file(tampered_cases)
    _write_receipt_with_digest(tampered_rcp, receipt)

    with pytest.raises(ValueError):
        verify_pilot_canary(
            dataset_path=DEFAULT_DATASET_OUTPUT,
            receipt_path=tampered_rcp,
            heldout_path=DEFAULT_HELDOUT_SUITE,
            replay_path=DEFAULT_REPLAY_OUTPUT,
            eval_cases_path=tampered_cases,
            training_log_path=DEFAULT_TRAINING_LOG_OUTPUT,
            adapter_path=DEFAULT_ADAPTER_OUTPUT,
        )


def test_adversarial_nlp_negated_option_rejected() -> None:
    """Verify that negated markdown options are not treated as selections.

    Regression test for Codex R8 Finding 4.
    """
    pred = "Не обирайте `А`."
    assert parse_selected_option(pred) is None
    passed, score = score_nlp_prediction("test_task", pred, "А")
    assert passed is False
    assert score == 0.0


def test_adversarial_nlp_selected_with_negated_alternative_accepted() -> None:
    """Verify that an affirmative selection is retained when an alternative is negated.

    Regression test for Codex R8 Finding 4.
    """
    pred = "Відповідь: А. Не обирайте `Б`."
    assert parse_selected_option(pred) == "А"
    passed, score = score_nlp_prediction("test_task", pred, "А")
    assert passed is True
    assert score == 1.0


def test_adversarial_adapter_seed42_random_weights_rejected(tmp_path: Path) -> None:
    """Verify that replacing adapter weights with random generator weights (seed 42) fails verification.

    Regression test for Codex R9 Finding 1.
    """
    tampered_adapter = tmp_path / "tampered_seed42_adapter.safetensors"
    tampered_rcp = tmp_path / "tampered_seed42_receipt.json"

    rng = np.random.default_rng(42)
    tensors = {}
    for l in range(4):
        for m in ["q_proj", "k_proj", "v_proj", "o_proj"]:
            name_a = f"base_model.model.model.layers.{l}.self_attn.{m}.lora_A.weight"
            name_b = f"base_model.model.model.layers.{l}.self_attn.{m}.lora_B.weight"
            tensors[name_a] = torch.tensor((rng.standard_normal((16, 256), dtype=np.float32) * 0.02).astype(np.float32))
            tensors[name_b] = torch.tensor((rng.standard_normal((256, 16), dtype=np.float32) * 0.02).astype(np.float32))

    receipt = json.loads(DEFAULT_RECEIPT_OUTPUT.read_text(encoding="utf-8"))
    metadata = {
        "base_model": "google/gemma-3-4b-it",
        "training_run_id": receipt["provenance"]["training_run_id"],
        "adapter_id": receipt["provenance"]["adapter_id"],
        "checkpoint_step": "75",
        "checkpoint_id": "google/gemma-3-4b-it-step75",
        "dataset_sha256": receipt["files"]["dataset"]["sha256"],
        "replay_sha256": receipt["files"]["replay_buffer"]["sha256"],
        "converged_loss": str(receipt["loss_convergence"]["converged_loss"]),
        "lora_rank": "16",
        "lora_alpha": "32",
    }
    safetensors.torch.save_file(tensors, tampered_adapter, metadata=metadata)
    ad_hash = sha256_file(tampered_adapter)

    tampered_log = tmp_path / "tampered_training_log.jsonl"
    tampered_cases = tmp_path / "tampered_eval_cases.jsonl"
    shutil.copy(DEFAULT_TRAINING_LOG_OUTPUT, tampered_log)
    shutil.copy(DEFAULT_EVAL_CASES_OUTPUT, tampered_cases)
    _sync_adapter_digest(tampered_log, ad_hash)
    _sync_adapter_digest(tampered_cases, ad_hash)

    receipt["files"]["training_log"]["sha256"] = sha256_file(tampered_log)
    receipt["files"]["eval_cases"]["sha256"] = sha256_file(tampered_cases)
    receipt["files"]["adapter"]["sha256"] = ad_hash
    receipt["provenance"]["adapter_digest"] = ad_hash
    _write_receipt_with_digest(tampered_rcp, receipt)

    with pytest.raises(ValueError, match=r"contains mock random generator weights"):
        verify_pilot_canary(
            dataset_path=DEFAULT_DATASET_OUTPUT,
            receipt_path=tampered_rcp,
            heldout_path=DEFAULT_HELDOUT_SUITE,
            replay_path=DEFAULT_REPLAY_OUTPUT,
            eval_cases_path=tampered_cases,
            training_log_path=tampered_log,
            adapter_path=tampered_adapter,
        )


def test_adversarial_safety_triple_asterisk_commentary_rejected(tmp_path: Path) -> None:
    """Verify that commentary with triple emphasis (***Пояснення***) concealing deleted target term fails verification.

    Regression test for Codex R9 Finding 3.
    """
    pred = "Речення повністю переписано без цільового слова.\n***Пояснення*** — електрон."
    harm, passed, score = score_safety_prediction("електрон", "Оригінальне речення містить електрон у атомі.", pred)
    assert harm is True
    assert passed is False
    assert score == 0.0

    tampered_cases = tmp_path / "tampered_triple_star_cases.jsonl"
    tampered_rcp = tmp_path / "tampered_triple_star_receipt.json"

    lines = [line for line in DEFAULT_EVAL_CASES_OUTPUT.read_text(encoding="utf-8").splitlines() if line]
    for idx, l in enumerate(lines):
        c = json.loads(l)
        if c.get("suite") == "clean_control_safety" and c.get("passed"):
            c["model_prediction"] = f"Текст змінено. ***Пояснення*** — {c['target_term']}."
            lines[idx] = json.dumps(c)

    tampered_cases.write_text("\n".join(lines) + "\n", encoding="utf-8")
    receipt = json.loads(DEFAULT_RECEIPT_OUTPUT.read_text(encoding="utf-8"))
    receipt["files"]["eval_cases"]["sha256"] = sha256_file(tampered_cases)
    _write_receipt_with_digest(tampered_rcp, receipt)

    with pytest.raises(ValueError, match=r"harmful_edit flag inconsistent"):
        verify_pilot_canary(
            dataset_path=DEFAULT_DATASET_OUTPUT,
            receipt_path=tampered_rcp,
            heldout_path=DEFAULT_HELDOUT_SUITE,
            replay_path=DEFAULT_REPLAY_OUTPUT,
            eval_cases_path=tampered_cases,
            training_log_path=DEFAULT_TRAINING_LOG_OUTPUT,
            adapter_path=DEFAULT_ADAPTER_OUTPUT,
        )


def test_adversarial_calque_parenthesized_reversed_recommendation_rejected(tmp_path: Path) -> None:
    """Verify that reversed recommendation with parenthesized term and 'кажіть' is rejected.

    Regression test for Codex R9 Finding 4.
    """
    pred = "Помилка («збігається»), тож кажіть «співпадає»."
    elim, passed, score = score_calque_prediction("співпадає", "збігається", pred)
    assert elim is False
    assert passed is False
    assert score == 0.0

    tampered_cases = tmp_path / "tampered_parenthesized_calque_cases.jsonl"
    tampered_rcp = tmp_path / "tampered_parenthesized_calque_receipt.json"

    lines = [line for line in DEFAULT_EVAL_CASES_OUTPUT.read_text(encoding="utf-8").splitlines() if line]
    for idx, l in enumerate(lines):
        c = json.loads(l)
        if c.get("suite") == "calque_elimination" and c.get("passed"):
            c["model_prediction"] = f"Помилка («{c['expected_replacement']}»), тож кажіть «{c['target_term']}»."
            lines[idx] = json.dumps(c)

    tampered_cases.write_text("\n".join(lines) + "\n", encoding="utf-8")
    receipt = json.loads(DEFAULT_RECEIPT_OUTPUT.read_text(encoding="utf-8"))
    receipt["files"]["eval_cases"]["sha256"] = sha256_file(tampered_cases)
    _write_receipt_with_digest(tampered_rcp, receipt)

    with pytest.raises(ValueError, match=r"(?:eliminated|passed) flag inconsistent"):
        verify_pilot_canary(
            dataset_path=DEFAULT_DATASET_OUTPUT,
            receipt_path=tampered_rcp,
            heldout_path=DEFAULT_HELDOUT_SUITE,
            replay_path=DEFAULT_REPLAY_OUTPUT,
            eval_cases_path=tampered_cases,
            training_log_path=DEFAULT_TRAINING_LOG_OUTPUT,
            adapter_path=DEFAULT_ADAPTER_OUTPUT,
        )


def test_adversarial_nlp_negated_options_codex_r9(tmp_path: Path) -> None:
    """Verify that complex negated options ('Не слід обирати `А`', '`А` — неправильна відповідь') are rejected.

    Regression test for Codex R9 Finding 5.
    """
    pred1 = "Не слід обирати `А`."
    pred2 = "`А` — неправильна відповідь."
    assert parse_selected_option(pred1) is None
    assert parse_selected_option(pred2) is None

    p1, s1 = score_nlp_prediction("task", pred1, "А")
    assert p1 is False
    assert s1 == 0.0

    p2, s2 = score_nlp_prediction("task", pred2, "А")
    assert p2 is False
    assert s2 == 0.0

    tampered_cases = tmp_path / "tampered_nlp_negated_cases.jsonl"
    tampered_rcp = tmp_path / "tampered_nlp_negated_receipt.json"

    lines = [line for line in DEFAULT_EVAL_CASES_OUTPUT.read_text(encoding="utf-8").splitlines() if line]
    for idx, l in enumerate(lines):
        c = json.loads(l)
        if c.get("suite") == "general_nlp_benchmark" and c.get("passed"):
            c["model_prediction"] = f"Не слід обирати `{c.get('expected_key', 'А')}`."
            lines[idx] = json.dumps(c)

    tampered_cases.write_text("\n".join(lines) + "\n", encoding="utf-8")
    receipt = json.loads(DEFAULT_RECEIPT_OUTPUT.read_text(encoding="utf-8"))
    receipt["files"]["eval_cases"]["sha256"] = sha256_file(tampered_cases)
    _write_receipt_with_digest(tampered_rcp, receipt)

    with pytest.raises(ValueError, match=r"canary passed flag inconsistent"):
        verify_pilot_canary(
            dataset_path=DEFAULT_DATASET_OUTPUT,
            receipt_path=tampered_rcp,
            heldout_path=DEFAULT_HELDOUT_SUITE,
            replay_path=DEFAULT_REPLAY_OUTPUT,
            eval_cases_path=tampered_cases,
            training_log_path=DEFAULT_TRAINING_LOG_OUTPUT,
            adapter_path=DEFAULT_ADAPTER_OUTPUT,
        )
