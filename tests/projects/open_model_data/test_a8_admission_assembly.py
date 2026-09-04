"""V4 A8 admission/assembly: admitted-slice assembly, schema checks, and
residual attachment, wired to (never replacing) the shared
``v4_original_row_admission`` engine and bound to the merged A7 original-row
factory receipt, the frozen V4 pilot slot manifest, and the V4 SHA.

Everything here runs against public artifacts only -- no ``batch_state/``,
no A3 held-out membership, no A4 private ledger -- so this suite passes in a
fresh checkout.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import _v4_synthetic_chain_fixture as fixture
import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import v4_a8_admission_assembly as a8
from scripts.projects.open_model_data import v4_original_row_admission as admission

ROOT = Path(__file__).resolve().parents[3]
ADMISSION = ROOT / "data/projects/open_model_data/admission"
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
RECEIPT = ADMISSION / "dataset_v4_a8_admission_assembly_receipt_v1.json"
SCHEMA = CONTRACTS / "dataset_v4_a8_admission_assembly_receipt_v1.schema.json"
A2_RECEIPT_PATH = ADMISSION / "dataset_v4_a2_source_operation_admission_receipt_v1.json"
A4_RECEIPT_PATH = ADMISSION / "dataset_v4_a4_deterministic_extraction_receipt_v1.json"
A5_RECEIPT_PATH = ADMISSION / "dataset_v4_a5_evidence_enrichment_receipt_v1.json"
A6_RECEIPT_PATH = ADMISSION / "dataset_v4_a6_blind_arena_receipt_v1.json"
A7_RECEIPT_PATH = ADMISSION / "dataset_v4_a7_original_row_factory_receipt_v1.json"
MANIFEST_PATH = ADMISSION / "dataset_v4_pilot_slot_manifest_v1.json"

V4_SHA256 = "78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20"

REAL_RECEIPT = json.loads(RECEIPT.read_text(encoding="utf-8"))
REAL_A2_RECEIPT = json.loads(A2_RECEIPT_PATH.read_text(encoding="utf-8"))
REAL_A4_RECEIPT = json.loads(A4_RECEIPT_PATH.read_text(encoding="utf-8"))
REAL_A5_RECEIPT = json.loads(A5_RECEIPT_PATH.read_text(encoding="utf-8"))
REAL_A6_RECEIPT = json.loads(A6_RECEIPT_PATH.read_text(encoding="utf-8"))
REAL_A7_RECEIPT = json.loads(A7_RECEIPT_PATH.read_text(encoding="utf-8"))
REAL_MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

FORBIDDEN_KEYS = a8.FORBIDDEN_KEYS
FORBIDDEN_SUBSTRINGS = a8.FORBIDDEN_SUBSTRINGS


def _all_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(_all_keys(item) for item in value.values()), set())
    if isinstance(value, list):
        return set().union(*(_all_keys(item) for item in value), set())
    return set()


def _write_receipt_tree(tmp_path: Path, *, a2=None, a4=None, a5=None, a6=None, a7=None, manifest=None) -> Path:
    admission_dir = tmp_path / "data/projects/open_model_data/admission"
    admission_dir.mkdir(parents=True)
    (admission_dir / "dataset_v4_a2_source_operation_admission_receipt_v1.json").write_text(json.dumps(a2 if a2 is not None else REAL_A2_RECEIPT))
    (admission_dir / "dataset_v4_a4_deterministic_extraction_receipt_v1.json").write_text(json.dumps(a4 if a4 is not None else REAL_A4_RECEIPT))
    (admission_dir / "dataset_v4_a5_evidence_enrichment_receipt_v1.json").write_text(json.dumps(a5 if a5 is not None else REAL_A5_RECEIPT))
    (admission_dir / "dataset_v4_a6_blind_arena_receipt_v1.json").write_text(json.dumps(a6 if a6 is not None else REAL_A6_RECEIPT))
    (admission_dir / "dataset_v4_a7_original_row_factory_receipt_v1.json").write_text(json.dumps(a7 if a7 is not None else REAL_A7_RECEIPT))
    (admission_dir / "dataset_v4_pilot_slot_manifest_v1.json").write_text(json.dumps(manifest if manifest is not None else REAL_MANIFEST))
    return tmp_path


# --- assembly gate --------------------------------------------------------------


def test_a8_gate_against_the_real_production_artifacts_stays_closed_today() -> None:
    gate = a8.check_assembly_gate()
    assert gate["a7_receipt_valid"] is True
    assert gate["slots_prerequisite_eligible"] == 0
    assert gate["slots_upstream_complete"] == 0
    assert gate["slots_stage_complete"] == 0
    assert gate["slots_residual"] == 100
    assert gate["assembly_slice_ready"] is False
    assert gate["blocked_reason_code"] == "no_slot_prerequisite_eligible"


def test_a8_gate_closed_when_a_required_public_artifact_is_missing(tmp_path: Path) -> None:
    _write_receipt_tree(tmp_path)
    (tmp_path / "data/projects/open_model_data/admission/dataset_v4_a7_original_row_factory_receipt_v1.json").unlink()
    gate = a8.check_assembly_gate(tmp_path)
    assert gate["assembly_slice_ready"] is False
    assert gate["blocked_reason_code"] == "required_public_artifact_missing:a7_receipt"


def test_a8_gate_closed_when_a7_receipt_is_invalid(tmp_path: Path) -> None:
    forged = copy.deepcopy(REAL_A7_RECEIPT)
    forged["bindings"]["a6_blind_arena"]["sha256"] = "0" * 64
    _write_receipt_tree(tmp_path, a7=forged)
    gate = a8.check_assembly_gate(tmp_path)
    assert gate["a7_receipt_valid"] is False
    assert gate["blocked_reason_code"] == "upstream_receipt_invalid"


def test_a8_gate_reports_eligible_but_stays_closed_pending_upstream_a7_completion(tmp_path: Path) -> None:
    """The A8-layer regression test for the same P1: A2 rights + manifest
    assignment resolving a stratum must never, by itself, produce a
    positive A8 completion count. Every validator here runs live (A6's and
    A7's own real builders/validators, never stubbed) against a synthetic
    root where one stratum is genuinely prerequisite-eligible; A7's own
    ``a7_completions`` stays empty, so A8 -- which requires A7's positive
    completion evidence -- stays at 0 complete."""
    fixture.build_synthetic_chain_root(tmp_path, resolved_stratum="standard_correct")
    fixture.run_chain_a6_through_a9(tmp_path)

    gate = a8.check_assembly_gate(tmp_path)
    assert gate["a7_receipt_valid"] is True
    assert gate["slots_prerequisite_eligible"] == 15
    assert gate["slots_upstream_complete"] == 0
    assert gate["slots_stage_complete"] == 0
    assert gate["slots_residual"] == 100
    assert gate["assembly_slice_ready"] is False
    assert gate["blocked_reason_code"] == "eligible_slots_awaiting_upstream_stage_completion"


# --- A8 residuals + admitted slice view ------------------------------------------


def test_a8_residuals_are_one_typed_entry_per_frozen_slot_never_a_silent_drop() -> None:
    gate = a8.check_assembly_gate()
    residuals = a8.derive_a8_slot_residuals(REAL_MANIFEST, REAL_A2_RECEIPT, gate)
    assert len(residuals) == 100
    assert len({r["residual_id"] for r in residuals}) == 100
    assert {r["subject_id"] for r in residuals} == set(a8.a7.a6.all_frozen_slot_ids(REAL_MANIFEST))
    assert all(r["stage"] == "A8" for r in residuals)
    assert {r["reason_code"] for r in residuals} == {"rights_unknown", "source_incomplete", "independence_unavailable"}
    # Never a fabricated row standing in for the missing admitted row.
    assert not any("row_id" in r or "content" in r for r in residuals)


def test_a8_admitted_slice_view_is_empty_plus_residuals_never_not_applicable() -> None:
    gate = a8.check_assembly_gate()
    residuals = a8.derive_a8_slot_residuals(REAL_MANIFEST, REAL_A2_RECEIPT, gate)
    view = a8.build_admitted_slice_view(REAL_MANIFEST, residuals)
    assert len(view) == 100
    assert {entry["slot_id"] for entry in view} == set(a8.a7.a6.all_frozen_slot_ids(REAL_MANIFEST))
    assert all(entry["row_admitted"] is False and entry["row_id"] is None for entry in view)
    residual_ids = {r["residual_id"] for r in residuals}
    assert {entry["residual_id"] for entry in view} <= residual_ids
    serialized = json.dumps(view, ensure_ascii=False)
    assert "not_applicable" not in serialized


# --- receipt assembly and independent verification ------------------------------


def test_a8_receipt_validates_independently_against_the_real_public_artifacts() -> None:
    assert a8.validate_receipt_independently(REAL_RECEIPT) is None


def test_a8_receipt_matches_schema() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors = list(Draft202012Validator(schema).iter_errors(REAL_RECEIPT))
    assert not errors, errors[0].message if errors else None


def test_a8_receipt_binds_v4_sha_and_control_surfaces() -> None:
    assert REAL_RECEIPT["controlling_outcome_sha256"] == V4_SHA256
    assert REAL_RECEIPT["control_surfaces"] == {
        "public_control_issue": 7423,
        "pilot_child_issue": 7430,
        "private_operational_board": 622,
    }
    assert REAL_RECEIPT["bindings"]["a7_original_row_factory"]["sha256"] == a8.sha256_file(A7_RECEIPT_PATH)
    assert REAL_RECEIPT["bindings"]["pilot_slot_manifest"]["sha256"] == a8.sha256_file(MANIFEST_PATH)


def test_a8_receipt_binds_the_merged_a7_receipt_by_its_known_public_sha() -> None:
    # The merged A7 receipt's public sha256, frozen at dispatch time (PR #7662 repair 1:
    # repaired stale pin from db80476d0a's A7 P1 fix, which changed A7 receipt content).
    assert a8.sha256_file(A7_RECEIPT_PATH) == "1d807da2761cadc6d3578b123217096cec65260034470873b7e6ea41c0a70821"


def test_a8_receipt_carries_forward_every_a2_a4_a5_a6_a7_residual_unresolved() -> None:
    assert {e["residual_id"] for e in REAL_RECEIPT["a2_residuals_carried_forward"]} == {e["residual_id"] for e in REAL_A2_RECEIPT["residuals"]}
    assert {e["residual_id"] for e in REAL_RECEIPT["a4_residuals_carried_forward"]} == {e["residual_id"] for e in REAL_A4_RECEIPT["a4_residuals"]}
    assert {e["residual_id"] for e in REAL_RECEIPT["a5_residuals_carried_forward"]} == {e["residual_id"] for e in REAL_A5_RECEIPT["a5_residuals"]}
    assert {e["residual_id"] for e in REAL_RECEIPT["a6_residuals_carried_forward"]} == {e["residual_id"] for e in REAL_A6_RECEIPT["a6_residuals"]}
    assert {e["residual_id"] for e in REAL_RECEIPT["a7_residuals_carried_forward"]} == {e["residual_id"] for e in REAL_A7_RECEIPT["a7_residuals"]}
    for key in (
        "a2_residuals_carried_forward",
        "a4_residuals_carried_forward",
        "a5_residuals_carried_forward",
        "a6_residuals_carried_forward",
        "a7_residuals_carried_forward",
    ):
        assert all(e["status"] == "unresolved_carried_to_a8" for e in REAL_RECEIPT[key])


def test_a8_receipt_does_not_claim_admitted_slice_ready_while_the_gate_is_closed() -> None:
    assert REAL_RECEIPT["assembly_gate"]["assembly_slice_ready"] is False
    assert REAL_RECEIPT["status"] != "ADMITTED_SLICE_READY"
    assert REAL_RECEIPT["execution_counters"]["slots_prerequisite_eligible"] == 0
    assert REAL_RECEIPT["execution_counters"]["slots_stage_complete"] == 0
    assert REAL_RECEIPT["execution_counters"]["slots_residual"] == 100


def test_a8_receipt_never_claims_training_ready_silver_arena_slice_ready_or_eval_artifact_ready() -> None:
    serialized = json.dumps(REAL_RECEIPT, ensure_ascii=False, sort_keys=True)
    assert "TRAINING_READY_SILVER" not in serialized
    assert "ARENA_SLICE_READY" not in serialized
    assert "EVAL_ARTIFACT_READY" not in serialized
    assert REAL_RECEIPT["safety_assertions"]["training_ready_silver_claimed"] is False
    assert REAL_RECEIPT["safety_assertions"]["arena_slice_ready_claimed"] is False
    assert REAL_RECEIPT["safety_assertions"]["eval_artifact_ready_claimed"] is False


def test_a8_receipt_eligibility_all_false_and_zero_rows_emitted() -> None:
    assert REAL_RECEIPT["eligibility"] == {"gold": False, "training": False, "evaluation": False, "teaching": False, "coverage": False}
    assert REAL_RECEIPT["execution_counters"]["dataset_rows_emitted"] == 0
    assert REAL_RECEIPT["execution_counters"]["candidate_rows_assembled"] == 0
    assert REAL_RECEIPT["safety_assertions"]["rows_not_admitted"] is True
    assert all(v is False for k, v in REAL_RECEIPT["safety_assertions"].items() if k != "rows_not_admitted")


def test_a8_receipt_never_names_source_text_a_held_out_family_or_a_plaintext_source_id() -> None:
    keys = _all_keys(REAL_RECEIPT)
    assert not keys & FORBIDDEN_KEYS
    serialized = json.dumps(REAL_RECEIPT, ensure_ascii=False, sort_keys=True)
    assert not any(needle in serialized for needle in FORBIDDEN_SUBSTRINGS)
    assert REAL_RECEIPT["a8_residuals"][0]["subject_id"].startswith("v4p-")


def test_a8_bindings_hash_to_disk_for_every_bound_artifact() -> None:
    for name, binding in REAL_RECEIPT["bindings"].items():
        path = ROOT / binding["path"]
        assert path.is_file(), name
        assert a8.sha256_file(path) == binding["sha256"], name


# --- shared engine wiring (real call, exercised against production artifacts) ---


def test_a8_engine_wiring_is_a_live_call_into_the_shared_admission_engine() -> None:
    wiring = REAL_RECEIPT["engine_wiring"]
    assert wiring["engine_schema_version"] == admission.SCHEMA_VERSION
    assert wiring["engine_input_schema_version"] == admission.INPUT_SCHEMA_VERSION
    assert wiring["model_only_bases_blocked"] == sorted(admission.MODEL_ONLY_BASES)
    recomputed = admission.admit_rows(outcome_sha256=V4_SHA256, rows=[])
    assert wiring["admission_receipt"] == recomputed
    assert admission.verify_receipt(wiring["admission_receipt"]) == wiring["admission_receipt"]
    assert wiring["admission_receipt"]["counts"] == {"input_rows": 0, "admitted_rows": 0, "rejected_rows": 0}


def test_a8_engine_still_refuses_a_model_only_basis_row_never_admits_silver() -> None:
    """Proves A8 wires the *unmodified* shared engine: a model-agreement /
    arena-vote basis can never satisfy authorship, evidence, rights, or the
    reconstruction gates -- exercised against a synthetic, non-corpus row."""
    row = {
        "row_id": "engine-self-test-row-01",
        "row_content_sha256": "a" * 64,
        "lineage": {"immutable": True, "source_ids": ["engine-self-test-source"], "evidence_ids": ["engine-self-test-evidence"]},
        "label_tier": "silver",
        "authorship": {"basis": "model_agreement"},
        "evidence": {"basis": "arena_vote"},
        "rights": {"basis": "model_vote"},
        "split_duplicate_safety": {"passed": True, "receipt_id": "engine-self-test-split"},
        "reconstruction_gates": {gate: {"basis": "model_agreement"} for gate in admission.RECONSTRUCTION_GATES},
    }
    receipt = admission.evaluate_row(row)
    assert receipt["disposition"] == "rejected"
    assert receipt["training_eligible"] is False
    assert "MODEL_AGREEMENT_CANNOT_SATISFY_AUTHORSHIP" in receipt["residual_codes"]
    assert "MODEL_AGREEMENT_CANNOT_SATISFY_EVIDENCE" in receipt["residual_codes"]
    assert "MODEL_AGREEMENT_CANNOT_SATISFY_RIGHTS" in receipt["residual_codes"]
    assert "MODEL_AGREEMENT_CANNOT_SATISFY_RECONSTRUCTION" in receipt["residual_codes"]
    assert receipt["eligibility"] == {"gold": False, "training": False, "evaluation": False, "teaching": False, "coverage": False}


# --- fail-closed on tampering ----------------------------------------------------


def test_a8_refuses_a_tampered_binding_hash() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["bindings"]["a7_original_row_factory"]["sha256"] = "0" * 64
    with pytest.raises(a8.AdmissionAssemblyError):
        a8.validate_receipt_independently(receipt)


def test_a8_refuses_a_forged_admitted_slice_ready_claim() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["status"] = "ADMITTED_SLICE_READY"
    receipt["assembly_gate"] = {**receipt["assembly_gate"], "assembly_slice_ready": True, "blocked_reason_code": None}
    with pytest.raises(a8.AdmissionAssemblyError):
        a8.validate_receipt_independently(receipt)


def test_a8_refuses_a_dropped_a7_residual() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["a7_residuals_carried_forward"].pop()
    with pytest.raises(a8.AdmissionAssemblyError):
        a8.validate_receipt_independently(receipt)


def test_a8_refuses_a_missing_frozen_slot_residual() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["a8_residuals"].pop()
    with pytest.raises(a8.AdmissionAssemblyError):
        a8.validate_receipt_independently(receipt)


def test_a8_refuses_a_dropped_admitted_slice_view_entry() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["admitted_slice_view"].pop()
    with pytest.raises(a8.AdmissionAssemblyError):
        a8.validate_receipt_independently(receipt)


def test_a8_refuses_a_forged_admitted_row_in_the_slice_view() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["admitted_slice_view"][0] = {**receipt["admitted_slice_view"][0], "row_admitted": True, "row_id": "forged-row"}
    with pytest.raises(a8.AdmissionAssemblyError):
        a8.validate_receipt_independently(receipt)


def test_a8_refuses_a_nonzero_dataset_rows_emitted_claim() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["execution_counters"]["dataset_rows_emitted"] = 1
    with pytest.raises(a8.AdmissionAssemblyError):
        a8.validate_receipt_independently(receipt)


def test_a8_refuses_a_fabricated_nonempty_engine_admission_row() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["engine_wiring"]["admission_receipt"] = admission.admit_rows(
        outcome_sha256=V4_SHA256,
        rows=[
            {
                "row_id": "forged-row",
                "row_content_sha256": "b" * 64,
                "lineage": {"immutable": True, "source_ids": ["s"], "evidence_ids": ["e"]},
                "label_tier": "silver",
                "authorship": {"basis": "model_agreement"},
                "evidence": {"basis": "model_agreement"},
                "rights": {"basis": "model_agreement"},
                "split_duplicate_safety": {"passed": True, "receipt_id": "x"},
                "reconstruction_gates": {gate: {"basis": "model_agreement"} for gate in admission.RECONSTRUCTION_GATES},
            }
        ],
    )
    with pytest.raises(a8.AdmissionAssemblyError):
        a8.validate_receipt_independently(receipt)


def test_a8_schema_rejects_a_leaked_gold_label_value() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["eligibility"]["gold"] = True
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema).iter_errors(receipt))
    assert errors


def test_a8_gold_key_is_a_frozen_false_eligibility_flag_never_a_real_label() -> None:
    assert "gold" not in FORBIDDEN_KEYS
    assert REAL_RECEIPT["eligibility"]["gold"] is False
