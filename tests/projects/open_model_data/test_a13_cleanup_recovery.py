"""V4 A13 cleanup/recovery receipt: the typed cleanup-policy and closeout
receipt bound to the merged A12 gold-overlay gate receipt, the frozen V4
pilot slot manifest, and the V4 SHA.

Everything here runs against public artifacts only -- no ``batch_state/``,
no A3 held-out membership, no A4 private ledger -- so this suite passes in a
fresh checkout. Most tamper-detection tests monkeypatch
``a13.a12.validate_receipt_independently`` to a fast no-op: they exercise
A13's own receipt-tampering logic, not a re-verification of the whole
upstream A2..A12 chain (which is itself expensive and already covered by
``test_a12_gold_overlay_gate.py``). A small number of tests deliberately run
the real, unmonkeypatched chain against the real production artifacts.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import v4_a13_cleanup_recovery as a13

ROOT = Path(__file__).resolve().parents[3]
ADMISSION = ROOT / "data/projects/open_model_data/admission"
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
RECEIPT = ADMISSION / "dataset_v4_a13_cleanup_recovery_receipt_v1.json"
SCHEMA = CONTRACTS / "dataset_v4_a13_cleanup_recovery_receipt_v1.schema.json"
A2_RECEIPT_PATH = ADMISSION / "dataset_v4_a2_source_operation_admission_receipt_v1.json"
A4_RECEIPT_PATH = ADMISSION / "dataset_v4_a4_deterministic_extraction_receipt_v1.json"
A5_RECEIPT_PATH = ADMISSION / "dataset_v4_a5_evidence_enrichment_receipt_v1.json"
A6_RECEIPT_PATH = ADMISSION / "dataset_v4_a6_blind_arena_receipt_v1.json"
A7_RECEIPT_PATH = ADMISSION / "dataset_v4_a7_original_row_factory_receipt_v1.json"
A8_RECEIPT_PATH = ADMISSION / "dataset_v4_a8_admission_assembly_receipt_v1.json"
A9_RECEIPT_PATH = ADMISSION / "dataset_v4_a9_evaluation_package_receipt_v1.json"
A10_RECEIPT_PATH = ADMISSION / "dataset_v4_a10_pilot_review_gate_receipt_v1.json"
A11_RECEIPT_PATH = ADMISSION / "dataset_v4_a11_silver_release_gate_receipt_v1.json"
A12_RECEIPT_PATH = ADMISSION / "dataset_v4_a12_gold_overlay_gate_receipt_v1.json"
MANIFEST_PATH = ADMISSION / "dataset_v4_pilot_slot_manifest_v1.json"

V4_SHA256 = "78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20"

REAL_RECEIPT = json.loads(RECEIPT.read_text(encoding="utf-8"))
REAL_A2_RECEIPT = json.loads(A2_RECEIPT_PATH.read_text(encoding="utf-8"))
REAL_A12_RECEIPT = json.loads(A12_RECEIPT_PATH.read_text(encoding="utf-8"))
REAL_MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

FORBIDDEN_KEYS = a13.FORBIDDEN_KEYS
FORBIDDEN_SUBSTRINGS = a13.FORBIDDEN_SUBSTRINGS


def _all_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(_all_keys(item) for item in value.values()), set())
    if isinstance(value, list):
        return set().union(*(_all_keys(item) for item in value), set())
    return set()


def _write_receipt_tree(tmp_path: Path, *, a2=None, manifest=None, a12_receipt=None) -> Path:
    """A minimal synthetic tree carrying only what
    ``check_cleanup_recovery_state`` itself reads directly (manifest, A2,
    A12). Used together with a fast, monkeypatched ``a12.validate_receipt_
    independently`` so these tests never pay for a real re-verification of
    the whole upstream chain."""
    admission_dir = tmp_path / "data/projects/open_model_data/admission"
    admission_dir.mkdir(parents=True)
    (admission_dir / "dataset_v4_a2_source_operation_admission_receipt_v1.json").write_text(json.dumps(a2 if a2 is not None else REAL_A2_RECEIPT))
    (admission_dir / "dataset_v4_a12_gold_overlay_gate_receipt_v1.json").write_text(json.dumps(a12_receipt if a12_receipt is not None else REAL_A12_RECEIPT))
    (admission_dir / "dataset_v4_pilot_slot_manifest_v1.json").write_text(json.dumps(manifest if manifest is not None else REAL_MANIFEST))
    return tmp_path


def _fast_a12(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stubs out A12's own (expensive, chained) independent re-verification
    so synthetic-tree tests exercise only A13's own logic."""
    monkeypatch.setattr(a13.a12, "validate_receipt_independently", lambda *a, **k: None)


# --- cleanup/recovery state ---------------------------------------------------


def test_a13_state_against_the_real_production_artifacts_stays_blocked_today() -> None:
    state = a13.check_cleanup_recovery_state()
    assert state["a12_receipt_valid"] is True
    assert state["model_agreement_exclusion_confirmed"] is True
    assert state["a2_rights_resolved"] is False
    assert state["all_slots_assigned"] is False
    assert state["denominator_stable"] is True
    assert state["epic_closed"] is False
    assert state["owner_role"] == "A2_A3_PRIVATE_ARTIFACT"
    assert state["blocked_reason_code"] == "rights_unresolved_and_slots_unassigned"


def test_a13_state_closed_when_a_required_public_artifact_is_missing(tmp_path: Path) -> None:
    _write_receipt_tree(tmp_path)
    (tmp_path / "data/projects/open_model_data/admission/dataset_v4_a12_gold_overlay_gate_receipt_v1.json").unlink()
    state = a13.check_cleanup_recovery_state(tmp_path)
    assert state["blocked_reason_code"] == "required_public_artifact_missing:a12_receipt"
    assert state["epic_closed"] is False


def test_a13_state_closed_when_a12_receipt_is_invalid(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_receipt_tree(tmp_path)
    monkeypatch.setattr(a13.a12, "validate_receipt_independently", lambda *a, **k: (_ for _ in ()).throw(a13.a12.GoldOverlayGateError("forged")))
    state = a13.check_cleanup_recovery_state(tmp_path)
    assert state["a12_receipt_valid"] is False
    assert state["blocked_reason_code"] == "a12_receipt_invalid"


def test_a13_state_flags_engine_drift_before_a12_validity(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _fast_a12(monkeypatch)
    _write_receipt_tree(tmp_path)
    monkeypatch.setattr(a13.a12.a11.a10.a9.a8.admission, "MODEL_ONLY_BASES", frozenset({"model_agreement"}))
    state = a13.check_cleanup_recovery_state(tmp_path)
    assert state["model_agreement_exclusion_confirmed"] is False
    assert state["blocked_reason_code"] == "model_agreement_exclusion_engine_drifted"


def test_a13_state_reports_rights_unresolved_and_slots_unassigned_when_both_pending(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _fast_a12(monkeypatch)
    _write_receipt_tree(tmp_path)
    state = a13.check_cleanup_recovery_state(tmp_path)
    assert state["a2_rights_resolved"] is False
    assert state["all_slots_assigned"] is False
    assert state["blocked_reason_code"] == "rights_unresolved_and_slots_unassigned"


def test_a13_state_reports_rights_unresolved_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _fast_a12(monkeypatch)
    assigned_manifest = copy.deepcopy(REAL_MANIFEST)
    for series in assigned_manifest["slot_series"]:
        series["assignment_state"] = "ASSIGNED"
    _write_receipt_tree(tmp_path, manifest=assigned_manifest)
    state = a13.check_cleanup_recovery_state(tmp_path)
    assert state["a2_rights_resolved"] is False
    assert state["all_slots_assigned"] is True
    assert state["blocked_reason_code"] == "rights_unresolved"


def test_a13_state_reports_slot_assignment_pending_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _fast_a12(monkeypatch)
    resolved_a2 = copy.deepcopy(REAL_A2_RECEIPT)
    resolved_a2["residuals"] = []
    _write_receipt_tree(tmp_path, a2=resolved_a2)
    state = a13.check_cleanup_recovery_state(tmp_path)
    assert state["a2_rights_resolved"] is True
    assert state["all_slots_assigned"] is False
    assert state["blocked_reason_code"] == "slot_assignment_pending_a2_a3"


def test_a13_state_never_reports_epic_closed_even_when_fully_resolved(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Proves epic_closed can never flip true by accident: it is hardcoded
    False regardless of upstream resolution state."""
    _fast_a12(monkeypatch)
    resolved_a2 = copy.deepcopy(REAL_A2_RECEIPT)
    resolved_a2["residuals"] = []
    assigned_manifest = copy.deepcopy(REAL_MANIFEST)
    for series in assigned_manifest["slot_series"]:
        series["assignment_state"] = "ASSIGNED"
    _write_receipt_tree(tmp_path, a2=resolved_a2, manifest=assigned_manifest)
    state = a13.check_cleanup_recovery_state(tmp_path)
    assert state["a2_rights_resolved"] is True
    assert state["all_slots_assigned"] is True
    assert state["blocked_reason_code"] is None
    assert state["epic_closed"] is False


# --- named residual -----------------------------------------------------------


def test_a13_named_residual_reuses_the_a2_a3_owner_role_and_never_deletes_to_close_it() -> None:
    state = a13.check_cleanup_recovery_state()
    residual = a13.build_named_residual(state)
    assert residual["residual_id"] == "a13-residual-rights-unresolved-and-slots-unassigned"
    assert residual["owner_role"] == "A2_A3_PRIVATE_ARTIFACT"
    assert residual["reason_code"] == "rights_unresolved_and_slots_unassigned"
    assert "A13 never deletes or reassigns a slot" in residual["next_action"]


# --- a13 per-slot residuals -----------------------------------------------------


def test_a13_residuals_are_one_typed_entry_per_frozen_slot_never_a_silent_drop() -> None:
    state = a13.check_cleanup_recovery_state()
    residuals = a13.derive_a13_slot_residuals(REAL_MANIFEST, REAL_A2_RECEIPT, state)
    assert len(residuals) == 100
    assert len({r["residual_id"] for r in residuals}) == 100
    assert {r["subject_id"] for r in residuals} == set(a13.a12.a11.a10.a9.a8.a7.a6.all_frozen_slot_ids(REAL_MANIFEST))
    assert all(r["stage"] == "A13" for r in residuals)
    assert {r["reason_code"] for r in residuals} == {"rights_unknown", "source_incomplete", "independence_unavailable"}
    # Never a fabricated cleanup/recovery verdict standing in for the missing released row.
    assert not any("delete" in r["next_action"].lower() and "never" not in r["next_action"].lower() for r in residuals)


# --- cleanup policy (fixed contract) ------------------------------------------


def test_a13_cleanup_policy_forbids_source_evidence_a3_heldout_and_a4_extraction() -> None:
    policy = a13.build_cleanup_policy()
    assert policy == a13.CLEANUP_POLICY
    assert "data/sources.db" in policy["forbidden_paths"]
    assert "batch_state/open-model-data/v4-a3-heldout/" in policy["forbidden_paths"]
    assert "batch_state/open-model-data/v4-a4-extraction/" in policy["forbidden_paths"]
    assert "delete_source_evidence" in policy["forbidden_actions"]
    assert "delete_private_a4_jsonl" in policy["forbidden_actions"]
    assert "open_a3_heldout_membership" in policy["forbidden_actions"]
    assert "delete_heldout_membership_to_save_disk" in policy["forbidden_actions"]


def test_a13_cleanup_policy_approves_only_dispatch_worktrees_and_pytest_cache() -> None:
    policy = a13.build_cleanup_policy()
    class_ids = {entry["class_id"] for entry in policy["approved_temp_output_classes"]}
    assert class_ids == {"dispatch_worktree_after_merged", "pytest_cache"}
    for entry in policy["approved_temp_output_classes"]:
        if entry["class_id"] == "dispatch_worktree_after_merged":
            assert entry["condition"] == "pr_status_is_merged"


def test_a13_cleanup_policy_is_immutable_across_calls() -> None:
    policy = a13.build_cleanup_policy()
    policy["forbidden_paths"].append("data/sources.db.bak")
    assert "data/sources.db.bak" not in a13.CLEANUP_POLICY["forbidden_paths"]
    assert "data/sources.db.bak" not in a13.build_cleanup_policy()["forbidden_paths"]


# --- shared engine wiring (real call, zero rows today) -----------------------


def test_a13_engine_wiring_reuses_the_shared_admission_engine_unmodified() -> None:
    receipt = a13.run_engine_admission_check([])
    assert receipt["counts"] == {"input_rows": 0, "admitted_rows": 0, "rejected_rows": 0}
    a13.a12.a11.a10.a9.a8.admission.verify_receipt(receipt)


# --- receipt assembly and independent verification --------------------------------


def test_a13_receipt_validates_independently_against_the_real_public_artifacts() -> None:
    assert a13.validate_receipt_independently(REAL_RECEIPT) is None


def test_a13_receipt_matches_schema() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors = list(Draft202012Validator(schema).iter_errors(REAL_RECEIPT))
    assert not errors, errors[0].message if errors else None


def test_a13_receipt_binds_v4_sha_and_control_surfaces() -> None:
    assert REAL_RECEIPT["controlling_outcome_sha256"] == V4_SHA256
    assert REAL_RECEIPT["control_surfaces"] == {
        "public_control_issue": 7423,
        "pilot_child_issue": 7430,
        "private_operational_board": 622,
    }
    assert REAL_RECEIPT["bindings"]["a12_gold_overlay_gate"]["sha256"] == a13.sha256_file(A12_RECEIPT_PATH)
    assert REAL_RECEIPT["bindings"]["pilot_slot_manifest"]["sha256"] == a13.sha256_file(MANIFEST_PATH)


def test_a13_receipt_binds_the_merged_a12_receipt_by_its_known_public_sha() -> None:
    # The merged A12 receipt's public sha256, frozen at dispatch time (PR #7643).
    assert a13.sha256_file(A12_RECEIPT_PATH) == "8d8c000fe3a3e20356a497fa94cacbbdd66a1343f52c5f4e1d80bccaaabb86a0"
    assert a13.A12_RECEIPT_SHA256_AT_MERGE == "8d8c000fe3a3e20356a497fa94cacbbdd66a1343f52c5f4e1d80bccaaabb86a0"


def test_a13_receipt_carries_forward_every_a2_a4_a5_a6_a7_a8_a9_a10_a11_a12_residual_unresolved() -> None:
    pairs = (
        ("a2_residuals_carried_forward", A2_RECEIPT_PATH, "residuals"),
        ("a4_residuals_carried_forward", A4_RECEIPT_PATH, "a4_residuals"),
        ("a5_residuals_carried_forward", A5_RECEIPT_PATH, "a5_residuals"),
        ("a6_residuals_carried_forward", A6_RECEIPT_PATH, "a6_residuals"),
        ("a7_residuals_carried_forward", A7_RECEIPT_PATH, "a7_residuals"),
        ("a8_residuals_carried_forward", A8_RECEIPT_PATH, "a8_residuals"),
        ("a9_residuals_carried_forward", A9_RECEIPT_PATH, "a9_residuals"),
        ("a10_residuals_carried_forward", A10_RECEIPT_PATH, "a10_residuals"),
        ("a11_residuals_carried_forward", A11_RECEIPT_PATH, "a11_residuals"),
        ("a12_residuals_carried_forward", A12_RECEIPT_PATH, "a12_residuals"),
    )
    for receipt_key, path, source_key in pairs:
        source = json.loads(path.read_text(encoding="utf-8"))
        assert {e["residual_id"] for e in REAL_RECEIPT[receipt_key]} == {e["residual_id"] for e in source[source_key]}
        assert all(e["status"] == "unresolved_carried_to_a13" for e in REAL_RECEIPT[receipt_key])


def test_a13_receipt_denominator_stays_100_and_visible() -> None:
    assert REAL_RECEIPT["frozen_slot_denominator"]["total_slots"] == 100
    assert REAL_RECEIPT["execution_counters"]["frozen_slot_count"] == 100
    assert len(REAL_RECEIPT["a13_residuals"]) == 100
    assert REAL_RECEIPT["recovery_state"]["denominator_stable"] is True


def test_a13_receipt_never_claims_a_stronger_release_state_than_the_evidence() -> None:
    assert REAL_RECEIPT["status"] == "A13_CLEANUP_RECOVERY_WIRED_TEXT_FREE_NO_STRONGER_RELEASE_STATE_CLAIM"
    assert REAL_RECEIPT["recovery_state"]["epic_closed"] is False
    serialized = json.dumps(REAL_RECEIPT, ensure_ascii=False, sort_keys=True)
    for forbidden in ("EPIC_DONE", "TRAINING_READY_SILVER", "TRAINING_READY_GOLD_SUBSET", "GOLD_UPGRADE_READY", "EVAL_ARTIFACT_READY", "PILOT_REVIEW_PASSED", "ARENA_SLICE_READY", "ADMITTED_SLICE_READY"):
        assert forbidden not in serialized, forbidden
    safety = REAL_RECEIPT["safety_assertions"]
    assert safety["epic_done_claimed"] is False
    assert safety["training_ready_silver_claimed"] is False
    assert safety["training_ready_gold_subset_claimed"] is False
    assert safety["gold_upgrade_ready_claimed"] is False
    assert safety["eval_artifact_ready_claimed"] is False
    assert safety["pilot_review_passed_claimed"] is False


def test_a13_receipt_dataset_rows_emitted_stays_zero() -> None:
    assert REAL_RECEIPT["execution_counters"]["dataset_rows_emitted"] == 0
    assert REAL_RECEIPT["engine_wiring"]["admission_receipt"]["counts"] == {"input_rows": 0, "admitted_rows": 0, "rejected_rows": 0}
    assert REAL_RECEIPT["safety_assertions"]["rows_not_admitted"] is True


def test_a13_receipt_never_deletes_a_forbidden_path_or_touches_private_artifacts() -> None:
    assert REAL_RECEIPT["execution_counters"]["temp_outputs_reaped"] == 0
    assert REAL_RECEIPT["execution_counters"]["forbidden_paths_touched"] == 0
    safety = REAL_RECEIPT["safety_assertions"]
    assert safety["held_out_membership_referenced"] is False
    assert safety["held_out_membership_opened"] is False
    assert safety["held_out_membership_deleted"] is False
    assert safety["a4_private_ledger_loaded"] is False
    assert safety["a4_private_ledger_deleted"] is False
    assert safety["source_evidence_deleted"] is False
    assert safety["sources_db_deleted"] is False
    assert safety["a3_membership_opened_by_a13"] is False
    assert safety["slot_reassigned_or_deleted_to_close_residual"] is False


def test_a13_receipt_never_names_source_text_a_held_out_family_or_a_plaintext_source_id() -> None:
    keys = _all_keys(REAL_RECEIPT)
    assert not keys & FORBIDDEN_KEYS
    serialized = json.dumps(REAL_RECEIPT, ensure_ascii=False, sort_keys=True)
    assert not any(needle in serialized for needle in FORBIDDEN_SUBSTRINGS)
    assert REAL_RECEIPT["a13_residuals"][0]["subject_id"].startswith("v4p-")


def test_a13_bindings_hash_to_disk_for_every_bound_artifact() -> None:
    for name, binding in REAL_RECEIPT["bindings"].items():
        path = ROOT / binding["path"]
        assert path.is_file(), name
        assert a13.sha256_file(path) == binding["sha256"], name


def test_a13_receipt_eligibility_all_false() -> None:
    assert REAL_RECEIPT["eligibility"] == {"gold": False, "training": False, "evaluation": False, "teaching": False, "coverage": False}


# --- fail-closed on tampering (fast: monkeypatched a12 validity) ----------------


def test_a13_refuses_a_tampered_binding_hash(monkeypatch: pytest.MonkeyPatch) -> None:
    _fast_a12(monkeypatch)
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["bindings"]["a12_gold_overlay_gate"]["sha256"] = "0" * 64
    with pytest.raises(a13.CleanupRecoveryError):
        a13.validate_receipt_independently(receipt)


def test_a13_refuses_a_receipt_bound_to_an_unmerged_a12_receipt_sha() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["bindings"]["a12_gold_overlay_gate"]["sha256"] = "1" * 64
    with pytest.raises(a13.CleanupRecoveryError):
        a13.validate_bound_to_merged_a12_receipt(receipt)


def test_a13_refuses_a_forged_epic_closed_claim(monkeypatch: pytest.MonkeyPatch) -> None:
    _fast_a12(monkeypatch)
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["recovery_state"]["epic_closed"] = True
    with pytest.raises((a13.CleanupRecoveryError, Exception)):
        a13.validate_receipt_independently(receipt)


def test_a13_refuses_a_dropped_a12_residual(monkeypatch: pytest.MonkeyPatch) -> None:
    _fast_a12(monkeypatch)
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["a12_residuals_carried_forward"].pop()
    with pytest.raises(a13.CleanupRecoveryError):
        a13.validate_receipt_independently(receipt)


def test_a13_refuses_a_missing_frozen_slot_residual(monkeypatch: pytest.MonkeyPatch) -> None:
    _fast_a12(monkeypatch)
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["a13_residuals"].pop()
    with pytest.raises(a13.CleanupRecoveryError):
        a13.validate_receipt_independently(receipt)


def test_a13_refuses_a_nonzero_dataset_rows_emitted_claim(monkeypatch: pytest.MonkeyPatch) -> None:
    _fast_a12(monkeypatch)
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["execution_counters"]["dataset_rows_emitted"] = 1
    with pytest.raises(a13.CleanupRecoveryError):
        a13.validate_receipt_independently(receipt)


def test_a13_refuses_a_nonzero_temp_outputs_reaped_claim(monkeypatch: pytest.MonkeyPatch) -> None:
    _fast_a12(monkeypatch)
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["execution_counters"]["temp_outputs_reaped"] = 1
    with pytest.raises(a13.CleanupRecoveryError):
        a13.validate_receipt_independently(receipt)


def test_a13_refuses_a_weakened_cleanup_policy_dropping_a_forbidden_path(monkeypatch: pytest.MonkeyPatch) -> None:
    _fast_a12(monkeypatch)
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["cleanup_policy"]["forbidden_paths"] = [p for p in receipt["cleanup_policy"]["forbidden_paths"] if p != "data/sources.db"]
    with pytest.raises(a13.CleanupRecoveryError):
        a13.validate_receipt_independently(receipt)


def test_a13_refuses_a_forged_named_residual_owner(monkeypatch: pytest.MonkeyPatch) -> None:
    _fast_a12(monkeypatch)
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["named_residual"]["owner_role"] = "A13"
    with pytest.raises((a13.CleanupRecoveryError, Exception)):
        a13.validate_receipt_independently(receipt)


def test_a13_refuses_a_tampered_model_only_bases_blocked_list(monkeypatch: pytest.MonkeyPatch) -> None:
    _fast_a12(monkeypatch)
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["engine_wiring"]["model_only_bases_blocked"] = ["model_agreement"]
    with pytest.raises(a13.CleanupRecoveryError):
        a13.validate_receipt_independently(receipt)


def test_a13_refuses_a_forged_epic_done_status_string() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["status"] = "EPIC_DONE"
    errors = list(Draft202012Validator(schema).iter_errors(receipt))
    assert errors


def test_a13_forbidden_completion_claims_include_epic_done_and_upstream_ready_terms() -> None:
    assert "EPIC_DONE" in a13.FORBIDDEN_COMPLETION_CLAIMS
    assert "GOLD_UPGRADE_READY" in a13.FORBIDDEN_COMPLETION_CLAIMS
    assert "TRAINING_READY_SILVER" in a13.FORBIDDEN_COMPLETION_CLAIMS
    assert "TRAINING_READY_GOLD_SUBSET" in a13.FORBIDDEN_COMPLETION_CLAIMS
    # The status string itself must never accidentally contain a forbidden term.
    assert not any(claim in REAL_RECEIPT["status"] for claim in a13.FORBIDDEN_COMPLETION_CLAIMS)
