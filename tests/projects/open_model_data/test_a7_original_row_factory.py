"""V4 A7 independent original-row factory: source-derived candidate rows/cases
with independent construction and lineage, wired to (never replacing) the
shared ``v4_original_row_admission`` engine and bound to the merged A6 blind
arena receipt, the frozen V4 pilot slot manifest, and the V4 SHA.

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

from scripts.projects.open_model_data import v4_a7_original_row_factory as a7
from scripts.projects.open_model_data import v4_original_row_admission as admission

ROOT = Path(__file__).resolve().parents[3]
ADMISSION = ROOT / "data/projects/open_model_data/admission"
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
RECEIPT = ADMISSION / "dataset_v4_a7_original_row_factory_receipt_v1.json"
SCHEMA = CONTRACTS / "dataset_v4_a7_original_row_factory_receipt_v1.schema.json"
A2_RECEIPT_PATH = ADMISSION / "dataset_v4_a2_source_operation_admission_receipt_v1.json"
A4_RECEIPT_PATH = ADMISSION / "dataset_v4_a4_deterministic_extraction_receipt_v1.json"
A5_RECEIPT_PATH = ADMISSION / "dataset_v4_a5_evidence_enrichment_receipt_v1.json"
A6_RECEIPT_PATH = ADMISSION / "dataset_v4_a6_blind_arena_receipt_v1.json"
MANIFEST_PATH = ADMISSION / "dataset_v4_pilot_slot_manifest_v1.json"

V4_SHA256 = "78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20"

REAL_RECEIPT = json.loads(RECEIPT.read_text(encoding="utf-8"))
REAL_A2_RECEIPT = json.loads(A2_RECEIPT_PATH.read_text(encoding="utf-8"))
REAL_A4_RECEIPT = json.loads(A4_RECEIPT_PATH.read_text(encoding="utf-8"))
REAL_A5_RECEIPT = json.loads(A5_RECEIPT_PATH.read_text(encoding="utf-8"))
REAL_A6_RECEIPT = json.loads(A6_RECEIPT_PATH.read_text(encoding="utf-8"))
REAL_MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

FORBIDDEN_KEYS = a7.FORBIDDEN_KEYS
FORBIDDEN_SUBSTRINGS = a7.FORBIDDEN_SUBSTRINGS


def _all_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(_all_keys(item) for item in value.values()), set())
    if isinstance(value, list):
        return set().union(*(_all_keys(item) for item in value), set())
    return set()


def _write_receipt_tree(tmp_path: Path, *, a2=None, a4=None, a5=None, a6=None, manifest=None) -> Path:
    admission_dir = tmp_path / "data/projects/open_model_data/admission"
    admission_dir.mkdir(parents=True)
    (admission_dir / "dataset_v4_a2_source_operation_admission_receipt_v1.json").write_text(json.dumps(a2 if a2 is not None else REAL_A2_RECEIPT))
    (admission_dir / "dataset_v4_a4_deterministic_extraction_receipt_v1.json").write_text(json.dumps(a4 if a4 is not None else REAL_A4_RECEIPT))
    (admission_dir / "dataset_v4_a5_evidence_enrichment_receipt_v1.json").write_text(json.dumps(a5 if a5 is not None else REAL_A5_RECEIPT))
    (admission_dir / "dataset_v4_a6_blind_arena_receipt_v1.json").write_text(json.dumps(a6 if a6 is not None else REAL_A6_RECEIPT))
    (admission_dir / "dataset_v4_pilot_slot_manifest_v1.json").write_text(json.dumps(manifest if manifest is not None else REAL_MANIFEST))
    return tmp_path


# --- stratum reason mapping ---------------------------------------------------


def test_a7_stratum_reason_codes_map_every_stratum_to_one_of_three_typed_reasons() -> None:
    reasons = a7.stratum_reason_codes(REAL_A2_RECEIPT)
    assert set(reasons) == {s["stratum"] for s in REAL_MANIFEST["slot_series"]}
    assert set(reasons.values()) <= {"rights_unknown", "source_incomplete", "independence_unavailable"}
    # Locked to the real A2 receipt's own reason codes today.
    assert reasons["standard_correct"] == "rights_unknown"
    assert reasons["correction"] == "independence_unavailable"  # A2 coverage_blocked
    assert reasons["dialect_regional"] == "source_incomplete"


# --- factory gate --------------------------------------------------------------


def test_a7_gate_against_the_real_production_artifacts_stays_closed_today() -> None:
    gate = a7.check_factory_gate()
    assert gate["a6_receipt_valid"] is True
    assert gate["all_slots_assigned"] is False
    assert gate["a2_rights_resolved"] is False
    assert gate["factory_slice_ready"] is False
    assert gate["blocked_reason_code"] == "rights_unresolved_and_slots_unassigned"


def test_a7_gate_closed_when_a_required_public_artifact_is_missing(tmp_path: Path) -> None:
    _write_receipt_tree(tmp_path)
    (tmp_path / "data/projects/open_model_data/admission/dataset_v4_a6_blind_arena_receipt_v1.json").unlink()
    gate = a7.check_factory_gate(tmp_path)
    assert gate["factory_slice_ready"] is False
    assert gate["blocked_reason_code"] == "required_public_artifact_missing:a6_receipt"


def test_a7_gate_closed_when_a6_receipt_is_invalid(tmp_path: Path) -> None:
    forged = copy.deepcopy(REAL_A6_RECEIPT)
    forged["bindings"]["a5_evidence_enrichment"]["sha256"] = "0" * 64
    _write_receipt_tree(tmp_path, a6=forged)
    gate = a7.check_factory_gate(tmp_path)
    assert gate["a6_receipt_valid"] is False
    assert gate["blocked_reason_code"] == "a6_receipt_invalid"


def test_a7_gate_opens_only_once_rights_are_resolved_and_every_slot_is_assigned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    resolved_a2 = copy.deepcopy(REAL_A2_RECEIPT)
    resolved_a2["residuals"] = []
    for coverage in resolved_a2["stratum_coverage_map"]:
        coverage["residual_ids"] = []
    assigned_manifest = copy.deepcopy(REAL_MANIFEST)
    for series in assigned_manifest["slot_series"]:
        series["assignment_state"] = "ASSIGNED"
    # A2 rights + manifest assignment alone are never sufficient -- A6's own
    # per-slot evidence must also genuinely clear for every frozen slot.
    cleared_a6 = copy.deepcopy(REAL_A6_RECEIPT)
    cleared_a6["a6_residuals"] = []
    _write_receipt_tree(tmp_path, a2=resolved_a2, manifest=assigned_manifest, a6=cleared_a6)
    monkeypatch.setattr(a7.a6, "validate_receipt_independently", lambda *a, **k: None)
    gate = a7.check_factory_gate(tmp_path)
    assert gate["a2_rights_resolved"] is True
    assert gate["all_slots_assigned"] is True
    assert gate["upstream_stage_evidence_present"] is True
    assert gate["factory_slice_ready"] is True
    assert gate["blocked_reason_code"] is None


def test_a7_gate_stays_closed_when_a2_and_manifest_resolve_but_a6_evidence_does_not(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A2 rights + manifest assignment metadata alone must never open the
    gate: this is exactly the previous scenario with A6's own per-slot
    evidence left untouched (still 100 residuals)."""
    resolved_a2 = copy.deepcopy(REAL_A2_RECEIPT)
    resolved_a2["residuals"] = []
    for coverage in resolved_a2["stratum_coverage_map"]:
        coverage["residual_ids"] = []
    assigned_manifest = copy.deepcopy(REAL_MANIFEST)
    for series in assigned_manifest["slot_series"]:
        series["assignment_state"] = "ASSIGNED"
    _write_receipt_tree(tmp_path, a2=resolved_a2, manifest=assigned_manifest)
    monkeypatch.setattr(a7.a6, "validate_receipt_independently", lambda *a, **k: None)
    gate = a7.check_factory_gate(tmp_path)
    assert gate["a2_rights_resolved"] is True
    assert gate["all_slots_assigned"] is True
    assert gate["upstream_stage_evidence_present"] is False
    assert gate["slots_ready"] == 0
    assert gate["factory_slice_ready"] is False
    assert gate["blocked_reason_code"] == "upstream_stage_evidence_unavailable"


# --- A7 residuals ----------------------------------------------------------------


def test_a7_residuals_are_one_typed_entry_per_frozen_slot_never_a_silent_drop() -> None:
    gate = a7.check_factory_gate()
    residuals = a7.derive_a7_slot_residuals(REAL_MANIFEST, REAL_A2_RECEIPT, gate)
    assert len(residuals) == 100
    assert len({r["residual_id"] for r in residuals}) == 100
    assert {r["subject_id"] for r in residuals} == set(a7.a6.all_frozen_slot_ids(REAL_MANIFEST))
    assert all(r["stage"] == "A7" for r in residuals)
    assert {r["reason_code"] for r in residuals} == {"rights_unknown", "source_incomplete", "independence_unavailable"}
    # Never a fabricated row standing in for the missing independent construction.
    assert not any("row_id" in r or "content" in r for r in residuals)


# --- receipt assembly and independent verification ------------------------------


def test_a7_receipt_validates_independently_against_the_real_public_artifacts() -> None:
    assert a7.validate_receipt_independently(REAL_RECEIPT) is None


def test_a7_receipt_matches_schema() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors = list(Draft202012Validator(schema).iter_errors(REAL_RECEIPT))
    assert not errors, errors[0].message if errors else None


def test_a7_receipt_binds_v4_sha_and_control_surfaces() -> None:
    assert REAL_RECEIPT["controlling_outcome_sha256"] == V4_SHA256
    assert REAL_RECEIPT["control_surfaces"] == {
        "public_control_issue": 7423,
        "pilot_child_issue": 7430,
        "private_operational_board": 622,
    }
    assert REAL_RECEIPT["bindings"]["a6_blind_arena"]["sha256"] == a7.sha256_file(A6_RECEIPT_PATH)
    assert REAL_RECEIPT["bindings"]["pilot_slot_manifest"]["sha256"] == a7.sha256_file(MANIFEST_PATH)


def test_a7_receipt_binds_the_merged_a6_receipt_by_its_known_public_sha() -> None:
    # The merged A6 receipt's public sha256, frozen at dispatch time (PR #7637).
    assert a7.sha256_file(A6_RECEIPT_PATH) == "59d03a7eab113a16185bae5eba20d62b2643bab3ca8af2518a6d3e9f7a8464e8"


def test_a7_receipt_carries_forward_every_a2_a4_a5_a6_residual_unresolved() -> None:
    assert {e["residual_id"] for e in REAL_RECEIPT["a2_residuals_carried_forward"]} == {e["residual_id"] for e in REAL_A2_RECEIPT["residuals"]}
    assert {e["residual_id"] for e in REAL_RECEIPT["a4_residuals_carried_forward"]} == {e["residual_id"] for e in REAL_A4_RECEIPT["a4_residuals"]}
    assert {e["residual_id"] for e in REAL_RECEIPT["a5_residuals_carried_forward"]} == {e["residual_id"] for e in REAL_A5_RECEIPT["a5_residuals"]}
    assert {e["residual_id"] for e in REAL_RECEIPT["a6_residuals_carried_forward"]} == {e["residual_id"] for e in REAL_A6_RECEIPT["a6_residuals"]}
    for key in ("a2_residuals_carried_forward", "a4_residuals_carried_forward", "a5_residuals_carried_forward", "a6_residuals_carried_forward"):
        assert all(e["status"] == "unresolved_carried_to_a7" for e in REAL_RECEIPT[key])


def test_a7_receipt_does_not_claim_original_rows_ready_while_the_gate_is_closed() -> None:
    assert REAL_RECEIPT["factory_gate"]["factory_slice_ready"] is False
    assert REAL_RECEIPT["status"] != "ORIGINAL_ROWS_READY"
    assert REAL_RECEIPT["execution_counters"]["slots_factory_ready"] == 0
    assert REAL_RECEIPT["execution_counters"]["slots_blocked"] == 100


def test_a7_receipt_never_claims_training_ready_silver_or_arena_slice_ready() -> None:
    serialized = json.dumps(REAL_RECEIPT, ensure_ascii=False, sort_keys=True)
    assert "TRAINING_READY_SILVER" not in serialized
    assert "ARENA_SLICE_READY" not in serialized
    assert REAL_RECEIPT["safety_assertions"]["training_ready_silver_claimed"] is False
    assert REAL_RECEIPT["safety_assertions"]["arena_slice_ready_claimed"] is False


def test_a7_receipt_eligibility_all_false_and_zero_rows_emitted() -> None:
    assert REAL_RECEIPT["eligibility"] == {"gold": False, "training": False, "evaluation": False, "teaching": False, "coverage": False}
    assert REAL_RECEIPT["execution_counters"]["dataset_rows_emitted"] == 0
    assert REAL_RECEIPT["execution_counters"]["candidate_rows_constructed"] == 0
    assert REAL_RECEIPT["safety_assertions"]["rows_not_admitted"] is True
    assert all(v is False for k, v in REAL_RECEIPT["safety_assertions"].items() if k != "rows_not_admitted")


def test_a7_receipt_never_names_source_text_a_held_out_family_or_a_plaintext_source_id() -> None:
    keys = _all_keys(REAL_RECEIPT)
    assert not keys & FORBIDDEN_KEYS
    serialized = json.dumps(REAL_RECEIPT, ensure_ascii=False, sort_keys=True)
    assert not any(needle in serialized for needle in FORBIDDEN_SUBSTRINGS)
    assert REAL_RECEIPT["a7_residuals"][0]["subject_id"].startswith("v4p-")


def test_a7_bindings_hash_to_disk_for_every_bound_artifact() -> None:
    for name, binding in REAL_RECEIPT["bindings"].items():
        path = ROOT / binding["path"]
        assert path.is_file(), name
        assert a7.sha256_file(path) == binding["sha256"], name


# --- shared engine wiring (real call, exercised against production artifacts) ---


def test_a7_engine_wiring_is_a_live_call_into_the_shared_admission_engine() -> None:
    wiring = REAL_RECEIPT["engine_wiring"]
    assert wiring["engine_schema_version"] == admission.SCHEMA_VERSION
    assert wiring["engine_input_schema_version"] == admission.INPUT_SCHEMA_VERSION
    assert wiring["model_only_bases_blocked"] == sorted(admission.MODEL_ONLY_BASES)
    recomputed = admission.admit_rows(outcome_sha256=V4_SHA256, rows=[])
    assert wiring["admission_receipt"] == recomputed
    assert admission.verify_receipt(wiring["admission_receipt"]) == wiring["admission_receipt"]
    assert wiring["admission_receipt"]["counts"] == {"input_rows": 0, "admitted_rows": 0, "rejected_rows": 0}


def test_a7_engine_still_refuses_a_model_only_basis_row_never_admits_silver() -> None:
    """Proves A7 wires the *unmodified* shared engine: a model-agreement /
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


def test_a7_refuses_a_tampered_binding_hash() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["bindings"]["a6_blind_arena"]["sha256"] = "0" * 64
    with pytest.raises(a7.OriginalRowFactoryError):
        a7.validate_receipt_independently(receipt)


def test_a7_refuses_a_forged_original_rows_ready_claim() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["status"] = "ORIGINAL_ROWS_READY"
    receipt["factory_gate"] = {**receipt["factory_gate"], "factory_slice_ready": True, "blocked_reason_code": None}
    with pytest.raises(a7.OriginalRowFactoryError):
        a7.validate_receipt_independently(receipt)


def test_a7_refuses_a_dropped_a6_residual() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["a6_residuals_carried_forward"].pop()
    with pytest.raises(a7.OriginalRowFactoryError):
        a7.validate_receipt_independently(receipt)


def test_a7_refuses_a_missing_frozen_slot_residual() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["a7_residuals"].pop()
    with pytest.raises(a7.OriginalRowFactoryError):
        a7.validate_receipt_independently(receipt)


def test_a7_refuses_a_nonzero_dataset_rows_emitted_claim() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["execution_counters"]["dataset_rows_emitted"] = 1
    with pytest.raises(a7.OriginalRowFactoryError):
        a7.validate_receipt_independently(receipt)


def test_a7_refuses_a_fabricated_nonempty_engine_admission_row() -> None:
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
    with pytest.raises(a7.OriginalRowFactoryError):
        a7.validate_receipt_independently(receipt)


def test_a7_schema_rejects_a_leaked_gold_label_value() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["eligibility"]["gold"] = True
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema).iter_errors(receipt))
    assert errors


def test_a7_gold_key_is_a_frozen_false_eligibility_flag_never_a_real_label() -> None:
    assert "gold" not in FORBIDDEN_KEYS
    assert REAL_RECEIPT["eligibility"]["gold"] is False
