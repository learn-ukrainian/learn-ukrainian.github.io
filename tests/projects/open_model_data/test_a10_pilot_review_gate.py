"""V4 A10 pilot review gate: independent Ukrainian-language review plus
exact-head cross-family (CF) review packet and gate, bound to the merged A9
evaluation package receipt, the frozen V4 pilot slot manifest, and the V4
SHA.

Everything here runs against public artifacts only -- no ``batch_state/``,
no A3 held-out membership, no A4 private ledger -- so this suite passes in a
fresh checkout.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import v4_a10_pilot_review_gate as a10

ROOT = Path(__file__).resolve().parents[3]
ADMISSION = ROOT / "data/projects/open_model_data/admission"
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
RECEIPT = ADMISSION / "dataset_v4_a10_pilot_review_gate_receipt_v1.json"
SCHEMA = CONTRACTS / "dataset_v4_a10_pilot_review_gate_receipt_v1.schema.json"
A2_RECEIPT_PATH = ADMISSION / "dataset_v4_a2_source_operation_admission_receipt_v1.json"
A4_RECEIPT_PATH = ADMISSION / "dataset_v4_a4_deterministic_extraction_receipt_v1.json"
A5_RECEIPT_PATH = ADMISSION / "dataset_v4_a5_evidence_enrichment_receipt_v1.json"
A6_RECEIPT_PATH = ADMISSION / "dataset_v4_a6_blind_arena_receipt_v1.json"
A7_RECEIPT_PATH = ADMISSION / "dataset_v4_a7_original_row_factory_receipt_v1.json"
A8_RECEIPT_PATH = ADMISSION / "dataset_v4_a8_admission_assembly_receipt_v1.json"
A9_RECEIPT_PATH = ADMISSION / "dataset_v4_a9_evaluation_package_receipt_v1.json"
MANIFEST_PATH = ADMISSION / "dataset_v4_pilot_slot_manifest_v1.json"

V4_SHA256 = "78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20"

REAL_RECEIPT = json.loads(RECEIPT.read_text(encoding="utf-8"))
REAL_A2_RECEIPT = json.loads(A2_RECEIPT_PATH.read_text(encoding="utf-8"))
REAL_A4_RECEIPT = json.loads(A4_RECEIPT_PATH.read_text(encoding="utf-8"))
REAL_A5_RECEIPT = json.loads(A5_RECEIPT_PATH.read_text(encoding="utf-8"))
REAL_A6_RECEIPT = json.loads(A6_RECEIPT_PATH.read_text(encoding="utf-8"))
REAL_A7_RECEIPT = json.loads(A7_RECEIPT_PATH.read_text(encoding="utf-8"))
REAL_A8_RECEIPT = json.loads(A8_RECEIPT_PATH.read_text(encoding="utf-8"))
REAL_A9_RECEIPT = json.loads(A9_RECEIPT_PATH.read_text(encoding="utf-8"))
REAL_MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

FORBIDDEN_KEYS = a10.FORBIDDEN_KEYS
FORBIDDEN_SUBSTRINGS = a10.FORBIDDEN_SUBSTRINGS


def _all_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(_all_keys(item) for item in value.values()), set())
    if isinstance(value, list):
        return set().union(*(_all_keys(item) for item in value), set())
    return set()


def _write_receipt_tree(tmp_path: Path, *, a2=None, a4=None, a5=None, a6=None, a7=None, a8=None, a9=None, manifest=None) -> Path:
    admission_dir = tmp_path / "data/projects/open_model_data/admission"
    admission_dir.mkdir(parents=True)
    (admission_dir / "dataset_v4_a2_source_operation_admission_receipt_v1.json").write_text(json.dumps(a2 if a2 is not None else REAL_A2_RECEIPT))
    (admission_dir / "dataset_v4_a4_deterministic_extraction_receipt_v1.json").write_text(json.dumps(a4 if a4 is not None else REAL_A4_RECEIPT))
    (admission_dir / "dataset_v4_a5_evidence_enrichment_receipt_v1.json").write_text(json.dumps(a5 if a5 is not None else REAL_A5_RECEIPT))
    (admission_dir / "dataset_v4_a6_blind_arena_receipt_v1.json").write_text(json.dumps(a6 if a6 is not None else REAL_A6_RECEIPT))
    (admission_dir / "dataset_v4_a7_original_row_factory_receipt_v1.json").write_text(json.dumps(a7 if a7 is not None else REAL_A7_RECEIPT))
    (admission_dir / "dataset_v4_a8_admission_assembly_receipt_v1.json").write_text(json.dumps(a8 if a8 is not None else REAL_A8_RECEIPT))
    (admission_dir / "dataset_v4_a9_evaluation_package_receipt_v1.json").write_text(json.dumps(a9 if a9 is not None else REAL_A9_RECEIPT))
    (admission_dir / "dataset_v4_pilot_slot_manifest_v1.json").write_text(json.dumps(manifest if manifest is not None else REAL_MANIFEST))
    return tmp_path


# --- pilot review gate --------------------------------------------------------------


def test_a10_gate_against_the_real_production_artifacts_stays_closed_today() -> None:
    gate = a10.check_pilot_review_gate()
    assert gate["a9_receipt_valid"] is True
    assert gate["all_slots_assigned"] is False
    assert gate["a2_rights_resolved"] is False
    assert gate["upstream_evaluation_slice_ready"] is False
    assert gate["independent_review_recorded"] is False
    assert gate["pilot_review_slice_ready"] is False
    assert gate["blocked_reason_code"] == "rights_unresolved_and_slots_unassigned"


def test_a10_gate_closed_when_a_required_public_artifact_is_missing(tmp_path: Path) -> None:
    _write_receipt_tree(tmp_path)
    (tmp_path / "data/projects/open_model_data/admission/dataset_v4_a9_evaluation_package_receipt_v1.json").unlink()
    gate = a10.check_pilot_review_gate(tmp_path)
    assert gate["pilot_review_slice_ready"] is False
    assert gate["blocked_reason_code"] == "required_public_artifact_missing:a9_receipt"


def test_a10_gate_closed_when_a9_receipt_is_invalid(tmp_path: Path) -> None:
    forged = copy.deepcopy(REAL_A9_RECEIPT)
    forged["bindings"]["a8_admission_assembly"]["sha256"] = "0" * 64
    _write_receipt_tree(tmp_path, a9=forged)
    gate = a10.check_pilot_review_gate(tmp_path)
    assert gate["a9_receipt_valid"] is False
    assert gate["blocked_reason_code"] == "a9_receipt_invalid"


def test_a10_gate_carries_the_upstream_a9_blocked_reason_once_rights_and_slots_clear(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    resolved_a2 = copy.deepcopy(REAL_A2_RECEIPT)
    resolved_a2["residuals"] = []
    assigned_manifest = copy.deepcopy(REAL_MANIFEST)
    for series in assigned_manifest["slot_series"]:
        series["assignment_state"] = "ASSIGNED"
    _write_receipt_tree(tmp_path, a2=resolved_a2, manifest=assigned_manifest)
    monkeypatch.setattr(a10.a9, "validate_receipt_independently", lambda *a, **k: None)
    gate = a10.check_pilot_review_gate(tmp_path)
    assert gate["a2_rights_resolved"] is True
    assert gate["all_slots_assigned"] is True
    assert gate["a9_receipt_valid"] is True
    # A9's own evaluation gate is still closed in REAL_A9_RECEIPT.
    assert gate["upstream_evaluation_slice_ready"] is False
    assert gate["pilot_review_slice_ready"] is False
    assert gate["blocked_reason_code"] == "upstream_a9_blocked:no_slot_prerequisite_eligible"


def test_a10_gate_stays_closed_even_once_upstream_a9_gate_reports_ready(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Proves the gate can never open by accident: even if every upstream
    flag flips true, ``independent_review_recorded`` has no execution
    mechanism and stays a hardcoded False."""
    resolved_a2 = copy.deepcopy(REAL_A2_RECEIPT)
    resolved_a2["residuals"] = []
    assigned_manifest = copy.deepcopy(REAL_MANIFEST)
    for series in assigned_manifest["slot_series"]:
        series["assignment_state"] = "ASSIGNED"
    ready_a9 = copy.deepcopy(REAL_A9_RECEIPT)
    ready_a9["evaluation_gate"] = {**ready_a9["evaluation_gate"], "evaluation_slice_ready": True, "blocked_reason_code": None}
    _write_receipt_tree(tmp_path, a2=resolved_a2, a9=ready_a9, manifest=assigned_manifest)
    monkeypatch.setattr(a10.a9, "validate_receipt_independently", lambda *a, **k: None)
    gate = a10.check_pilot_review_gate(tmp_path)
    assert gate["upstream_evaluation_slice_ready"] is True
    assert gate["independent_review_recorded"] is False
    assert gate["pilot_review_slice_ready"] is False
    assert gate["blocked_reason_code"] == "independent_review_not_yet_executed_no_admitted_rows"


def test_a10_gate_refuses_when_manifest_drops_the_required_gate_id(tmp_path: Path) -> None:
    stripped_manifest = copy.deepcopy(REAL_MANIFEST)
    stripped_manifest["required_gate_ids"] = [g for g in stripped_manifest["required_gate_ids"] if g != a10.REQUIRED_GATE_ID]
    _write_receipt_tree(tmp_path, manifest=stripped_manifest)
    with pytest.raises(a10.PilotReviewGateError):
        a10.check_pilot_review_gate(tmp_path)


# --- A10 residuals + review readiness view ------------------------------------


def test_a10_residuals_are_one_typed_entry_per_frozen_slot_never_a_silent_drop() -> None:
    gate = a10.check_pilot_review_gate()
    residuals = a10.derive_a10_slot_residuals(REAL_MANIFEST, REAL_A2_RECEIPT, gate)
    assert len(residuals) == 100
    assert len({r["residual_id"] for r in residuals}) == 100
    assert {r["subject_id"] for r in residuals} == set(a10.a9.a8.a7.a6.all_frozen_slot_ids(REAL_MANIFEST))
    assert all(r["stage"] == "A10" for r in residuals)
    assert {r["reason_code"] for r in residuals} == {"rights_unknown", "source_incomplete", "independence_unavailable"}
    # Never a fabricated review verdict standing in for the missing scored row.
    assert not any("review" in r or "reviewer" in r for r in residuals)


def test_a10_review_readiness_view_is_unreviewed_plus_residuals_never_a_fabricated_verdict() -> None:
    gate = a10.check_pilot_review_gate()
    residuals = a10.derive_a10_slot_residuals(REAL_MANIFEST, REAL_A2_RECEIPT, gate)
    view = a10.build_review_readiness_view(REAL_MANIFEST, REAL_A9_RECEIPT, residuals)
    assert len(view) == 100
    assert {entry["slot_id"] for entry in view} == set(a10.a9.a8.a7.a6.all_frozen_slot_ids(REAL_MANIFEST))
    assert all(entry["row_admitted"] is False and entry["row_scored"] is False for entry in view)
    assert all(entry["review_required"] is True and entry["review_executed"] is False for entry in view)
    assert all(entry["reviewer_family"] is None and entry["cf_review_of_record_passed"] is False for entry in view)
    residual_ids = {r["residual_id"] for r in residuals}
    assert {entry["residual_id"] for entry in view} <= residual_ids


def test_a10_review_readiness_view_fails_closed_on_a_dropped_slot() -> None:
    forged_a9 = copy.deepcopy(REAL_A9_RECEIPT)
    forged_a9["consumer_reproduction_view"].pop()
    gate = a10.check_pilot_review_gate()
    residuals = a10.derive_a10_slot_residuals(REAL_MANIFEST, REAL_A2_RECEIPT, gate)
    with pytest.raises(a10.PilotReviewGateError):
        a10.build_review_readiness_view(REAL_MANIFEST, forged_a9, residuals)


def test_a10_review_readiness_view_fails_closed_on_a_scored_row_without_an_admitted_row() -> None:
    forged_a9 = copy.deepcopy(REAL_A9_RECEIPT)
    forged_a9["consumer_reproduction_view"][0] = {**forged_a9["consumer_reproduction_view"][0], "scored": True, "row_admitted": False}
    gate = a10.check_pilot_review_gate()
    residuals = a10.derive_a10_slot_residuals(REAL_MANIFEST, REAL_A2_RECEIPT, gate)
    with pytest.raises(a10.PilotReviewGateError):
        a10.build_review_readiness_view(REAL_MANIFEST, forged_a9, residuals)


# --- review packet (fixed contract) ------------------------------------------


def test_a10_review_packet_requires_independent_reviewer_exact_head_cf_and_no_self_review() -> None:
    packet = a10.build_review_packet()
    assert packet == a10.REVIEW_PACKET_REQUIREMENTS
    assert packet["gate_id"] == "INDEPENDENT_CROSS_FAMILY_EXACT_HEAD_REVIEW"
    assert packet["requires_independent_ukrainian_language_reviewer"] is True
    assert packet["reviewer_family_must_differ_from_author_family"] is True
    assert packet["requires_exact_head_cross_family_review_of_record"] is True
    assert packet["self_review_satisfies_gate"] is False
    assert packet["discussion_only_satisfies_gate"] is False
    assert packet["internal_helper_swarm_satisfies_gate"] is False
    assert packet["review_may_execute_against_missing_or_empty_rows"] is False
    assert packet["review_execution_state"] == "NOT_EXECUTED_NO_ADMITTED_ROWS"


def test_a10_review_packet_is_immutable_across_calls() -> None:
    packet = a10.build_review_packet()
    packet["self_review_satisfies_gate"] = True
    assert a10.REVIEW_PACKET_REQUIREMENTS["self_review_satisfies_gate"] is False
    assert a10.build_review_packet()["self_review_satisfies_gate"] is False


def test_a10_required_gate_id_is_the_manifests_own_gate_id_never_invented() -> None:
    assert a10.REQUIRED_GATE_ID in REAL_MANIFEST["required_gate_ids"]


# --- receipt assembly and independent verification --------------------------------


def test_a10_receipt_validates_independently_against_the_real_public_artifacts() -> None:
    assert a10.validate_receipt_independently(REAL_RECEIPT) is None


def test_a10_receipt_matches_schema() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors = list(Draft202012Validator(schema).iter_errors(REAL_RECEIPT))
    assert not errors, errors[0].message if errors else None


def test_a10_receipt_binds_v4_sha_and_control_surfaces() -> None:
    assert REAL_RECEIPT["controlling_outcome_sha256"] == V4_SHA256
    assert REAL_RECEIPT["control_surfaces"] == {
        "public_control_issue": 7423,
        "pilot_child_issue": 7430,
        "private_operational_board": 622,
    }
    assert REAL_RECEIPT["bindings"]["a9_evaluation_package"]["sha256"] == a10.sha256_file(A9_RECEIPT_PATH)
    assert REAL_RECEIPT["bindings"]["pilot_slot_manifest"]["sha256"] == a10.sha256_file(MANIFEST_PATH)


def test_a10_receipt_binds_the_merged_a9_receipt_by_its_known_public_sha() -> None:
    # The merged A9 receipt's public sha256, frozen at dispatch time (PR #7662 repair 3:
    # A9's content changed under the Repair 2 real-slot-mechanism fix, rippling into A10-A13).
    assert a10.sha256_file(A9_RECEIPT_PATH) == "3ea541486f0b0007799b1b54833df494c1e1fa55d5d0410e2cd6410d78b60bd8"


def test_a10_receipt_carries_forward_every_a2_a4_a5_a6_a7_a8_a9_residual_unresolved() -> None:
    assert {e["residual_id"] for e in REAL_RECEIPT["a2_residuals_carried_forward"]} == {e["residual_id"] for e in REAL_A2_RECEIPT["residuals"]}
    assert {e["residual_id"] for e in REAL_RECEIPT["a4_residuals_carried_forward"]} == {e["residual_id"] for e in REAL_A4_RECEIPT["a4_residuals"]}
    assert {e["residual_id"] for e in REAL_RECEIPT["a5_residuals_carried_forward"]} == {e["residual_id"] for e in REAL_A5_RECEIPT["a5_residuals"]}
    assert {e["residual_id"] for e in REAL_RECEIPT["a6_residuals_carried_forward"]} == {e["residual_id"] for e in REAL_A6_RECEIPT["a6_residuals"]}
    assert {e["residual_id"] for e in REAL_RECEIPT["a7_residuals_carried_forward"]} == {e["residual_id"] for e in REAL_A7_RECEIPT["a7_residuals"]}
    assert {e["residual_id"] for e in REAL_RECEIPT["a8_residuals_carried_forward"]} == {e["residual_id"] for e in REAL_A8_RECEIPT["a8_residuals"]}
    assert {e["residual_id"] for e in REAL_RECEIPT["a9_residuals_carried_forward"]} == {e["residual_id"] for e in REAL_A9_RECEIPT["a9_residuals"]}
    for key in (
        "a2_residuals_carried_forward",
        "a4_residuals_carried_forward",
        "a5_residuals_carried_forward",
        "a6_residuals_carried_forward",
        "a7_residuals_carried_forward",
        "a8_residuals_carried_forward",
        "a9_residuals_carried_forward",
    ):
        assert all(e["status"] == "unresolved_carried_to_a10" for e in REAL_RECEIPT[key])


def test_a10_receipt_does_not_claim_pilot_review_passed_while_the_gate_is_closed() -> None:
    assert REAL_RECEIPT["review_gate"]["pilot_review_slice_ready"] is False
    assert REAL_RECEIPT["status"] != "PILOT_REVIEW_PASSED"
    assert REAL_RECEIPT["execution_counters"]["slots_review_ready"] == 0
    assert REAL_RECEIPT["execution_counters"]["slots_blocked"] == 100


def test_a10_receipt_never_claims_training_ready_silver_arena_admitted_or_eval_artifact_ready() -> None:
    serialized = json.dumps(REAL_RECEIPT, ensure_ascii=False, sort_keys=True)
    assert "TRAINING_READY_SILVER" not in serialized
    assert "ARENA_SLICE_READY" not in serialized
    assert "ADMITTED_SLICE_READY" not in serialized
    assert "EVAL_ARTIFACT_READY" not in serialized
    assert REAL_RECEIPT["safety_assertions"]["training_ready_silver_claimed"] is False
    assert REAL_RECEIPT["safety_assertions"]["arena_slice_ready_claimed"] is False
    assert REAL_RECEIPT["safety_assertions"]["admitted_slice_ready_claimed"] is False
    assert REAL_RECEIPT["safety_assertions"]["eval_artifact_ready_claimed"] is False
    assert REAL_RECEIPT["safety_assertions"]["pilot_review_passed_claimed"] is False


def test_a10_receipt_never_claims_a_review_was_executed_or_a_self_review_occurred() -> None:
    assert REAL_RECEIPT["safety_assertions"]["self_review_occurred"] is False
    assert REAL_RECEIPT["safety_assertions"]["review_executed_against_missing_or_empty_row"] is False
    assert all(entry["review_executed"] is False for entry in REAL_RECEIPT["review_readiness_view"])


def test_a10_receipt_eligibility_all_false_and_zero_rows_emitted() -> None:
    assert REAL_RECEIPT["eligibility"] == {"gold": False, "training": False, "evaluation": False, "teaching": False, "coverage": False}
    assert REAL_RECEIPT["execution_counters"]["dataset_rows_emitted"] == 0
    assert REAL_RECEIPT["execution_counters"]["rows_reviewed"] == 0
    assert REAL_RECEIPT["execution_counters"]["rows_admitted_and_eligible_for_review"] == 0
    assert REAL_RECEIPT["safety_assertions"]["rows_not_admitted"] is True
    assert all(v is False for k, v in REAL_RECEIPT["safety_assertions"].items() if k != "rows_not_admitted")


def test_a10_receipt_never_names_source_text_a_held_out_family_or_a_plaintext_source_id() -> None:
    keys = _all_keys(REAL_RECEIPT)
    assert not keys & FORBIDDEN_KEYS
    serialized = json.dumps(REAL_RECEIPT, ensure_ascii=False, sort_keys=True)
    assert not any(needle in serialized for needle in FORBIDDEN_SUBSTRINGS)
    assert REAL_RECEIPT["a10_residuals"][0]["subject_id"].startswith("v4p-")


def test_a10_receipt_never_opens_held_out_membership() -> None:
    assert REAL_RECEIPT["safety_assertions"]["held_out_membership_referenced"] is False
    assert REAL_RECEIPT["safety_assertions"]["held_out_membership_opened"] is False
    assert REAL_RECEIPT["safety_assertions"]["heldout_family_identity_leaked"] is False


def test_a10_bindings_hash_to_disk_for_every_bound_artifact() -> None:
    from learn_ukrainian_v4_runtime.resources import resource_root

    for name, binding in REAL_RECEIPT["bindings"].items():
        path = resource_root() / (
            "provenance/v1/blobs/sha256/" + binding["sha256"] + ".blob"
            if binding["path"].startswith("scripts/") else binding["path"]
        )
        assert path.is_file(), name
        assert a10.sha256_file(path) == binding["sha256"], name


# --- fail-closed on tampering ----------------------------------------------------


def test_a10_refuses_a_tampered_binding_hash() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["bindings"]["a9_evaluation_package"]["sha256"] = "0" * 64
    with pytest.raises(a10.PilotReviewGateError):
        a10.validate_receipt_independently(receipt)


def test_a10_refuses_a_forged_pilot_review_passed_claim() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["status"] = "PILOT_REVIEW_PASSED"
    receipt["review_gate"] = {**receipt["review_gate"], "pilot_review_slice_ready": True, "blocked_reason_code": None}
    with pytest.raises(a10.PilotReviewGateError):
        a10.validate_receipt_independently(receipt)


def test_a10_refuses_a_forged_independent_review_recorded_claim() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["review_gate"]["independent_review_recorded"] = True
    with pytest.raises(a10.PilotReviewGateError):
        a10.validate_receipt_independently(receipt)


def test_a10_refuses_a_dropped_a9_residual() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["a9_residuals_carried_forward"].pop()
    with pytest.raises(a10.PilotReviewGateError):
        a10.validate_receipt_independently(receipt)


def test_a10_refuses_a_missing_frozen_slot_residual() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["a10_residuals"].pop()
    with pytest.raises(a10.PilotReviewGateError):
        a10.validate_receipt_independently(receipt)


def test_a10_refuses_a_dropped_review_readiness_view_entry() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["review_readiness_view"].pop()
    with pytest.raises(a10.PilotReviewGateError):
        a10.validate_receipt_independently(receipt)


def test_a10_refuses_a_forged_executed_review_in_the_readiness_view() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["review_readiness_view"][0] = {**receipt["review_readiness_view"][0], "review_executed": True, "reviewer_family": "fable"}
    with pytest.raises(a10.PilotReviewGateError):
        a10.validate_receipt_independently(receipt)


def test_a10_refuses_a_nonzero_dataset_rows_emitted_claim() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["execution_counters"]["dataset_rows_emitted"] = 1
    with pytest.raises(a10.PilotReviewGateError):
        a10.validate_receipt_independently(receipt)


def test_a10_refuses_a_weakened_review_packet() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["review_packet"]["self_review_satisfies_gate"] = True
    with pytest.raises(a10.PilotReviewGateError):
        a10.validate_receipt_independently(receipt)


def test_a10_schema_rejects_a_leaked_gold_label_value() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["eligibility"]["gold"] = True
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema).iter_errors(receipt))
    assert errors


def test_a10_gold_key_is_a_frozen_false_eligibility_flag_never_a_real_label() -> None:
    assert "gold" not in FORBIDDEN_KEYS
    assert REAL_RECEIPT["eligibility"]["gold"] is False
