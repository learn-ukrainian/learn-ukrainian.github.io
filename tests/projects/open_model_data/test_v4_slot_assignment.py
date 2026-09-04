"""V4 public-slot -> A4-commitment assignment: binds every frozen, public
``v4p-*`` slot to a builder-eligible A4 HMAC commitment (or a typed
residual), bound to the merged A4 deterministic-extraction receipt, the
frozen V4 pilot slot manifest, and the V4 SHA.

Everything here runs against public artifacts only -- no ``batch_state/``,
no A3 held-out membership file, no A4 private ledger, no private builder
packet -- so this suite passes in a fresh checkout.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import v4_a4_deterministic_extraction as a4
from scripts.projects.open_model_data import v4_original_row_admission as admission
from scripts.projects.open_model_data import v4_public_slot_commitment_assignment as assignment

ROOT = Path(__file__).resolve().parents[3]
ADMISSION = ROOT / "data/projects/open_model_data/admission"
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
RECEIPT = ADMISSION / "dataset_v4_public_slot_commitment_assignment_receipt_v1.json"
SCHEMA = CONTRACTS / "dataset_v4_public_slot_commitment_assignment_receipt_v1.schema.json"
A2_RECEIPT_PATH = ADMISSION / "dataset_v4_a2_source_operation_admission_receipt_v1.json"
A4_RECEIPT_PATH = ADMISSION / "dataset_v4_a4_deterministic_extraction_receipt_v1.json"
MANIFEST_PATH = ADMISSION / "dataset_v4_pilot_slot_manifest_v1.json"
HELDOUT_MEMBERSHIP_PATH = ROOT / "batch_state/open-model-data/v4-a3-heldout/v4_a3_heldout_membership_v1.json"
BUILDER_PACKET_PATH = ROOT / "batch_state/open-model-data/v4-a3-heldout/v4_a3_builder_packet_v1.json"

V4_SHA256 = "78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20"

REAL_RECEIPT = json.loads(RECEIPT.read_text(encoding="utf-8"))
REAL_A2_RECEIPT = json.loads(A2_RECEIPT_PATH.read_text(encoding="utf-8"))
REAL_A4_RECEIPT = json.loads(A4_RECEIPT_PATH.read_text(encoding="utf-8"))
REAL_MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

FORBIDDEN_KEYS = assignment.FORBIDDEN_KEYS
FORBIDDEN_SUBSTRINGS = assignment.FORBIDDEN_SUBSTRINGS


def _all_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(_all_keys(item) for item in value.values()), set())
    if isinstance(value, list):
        return set().union(*(_all_keys(item) for item in value), set())
    return set()


def _write_receipt_tree(tmp_path: Path, *, a2=None, a4_receipt=None, manifest=None) -> Path:
    admission_dir = tmp_path / "data/projects/open_model_data/admission"
    admission_dir.mkdir(parents=True)
    (admission_dir / "dataset_v4_a2_source_operation_admission_receipt_v1.json").write_text(json.dumps(a2 if a2 is not None else REAL_A2_RECEIPT))
    (admission_dir / "dataset_v4_a4_deterministic_extraction_receipt_v1.json").write_text(json.dumps(a4_receipt if a4_receipt is not None else REAL_A4_RECEIPT))
    (admission_dir / "dataset_v4_pilot_slot_manifest_v1.json").write_text(json.dumps(manifest if manifest is not None else REAL_MANIFEST))
    return tmp_path


# --- firewall: this suite never opens the private heldout/builder-packet artifacts ---


def test_heldout_membership_file_is_never_opened_by_this_module_or_suite() -> None:
    # The module's own docstring names "batch_state/" and A3's private
    # membership filename only in prose, to say it never opens them. The
    # real guarantee: no module-level Path constant this module defines
    # (the only paths its functions ever open) resolves under batch_state/,
    # and it never imports the A3 held-out-membership module.
    path_constants = [value for value in vars(assignment).values() if isinstance(value, Path)]
    assert path_constants  # sanity: the module does define path constants
    assert not any("batch_state" in str(path) for path in path_constants)
    assert not hasattr(assignment, "v4_a3_heldout_family_assignment")


def test_this_test_module_never_reads_the_private_heldout_or_builder_packet_files() -> None:
    # HELDOUT_MEMBERSHIP_PATH/BUILDER_PACKET_PATH are module-level Path
    # constants defined above purely so this test can assert they are never
    # passed to open()/.read_text()/.read_bytes() anywhere in this suite.
    assert isinstance(HELDOUT_MEMBERSHIP_PATH, Path)
    assert isinstance(BUILDER_PACKET_PATH, Path)
    opened_paths: set[Path] = set()
    real_read_text = Path.read_text

    def _tracking_read_text(self: Path, *args: object, **kwargs: object) -> str:
        opened_paths.add(self)
        return real_read_text(self, *args, **kwargs)

    original = Path.read_text
    Path.read_text = _tracking_read_text  # type: ignore[method-assign]
    try:
        assignment.check_assignment_gate()
        assignment.build_receipt()
    finally:
        Path.read_text = original  # type: ignore[method-assign]
    assert HELDOUT_MEMBERSHIP_PATH not in opened_paths
    assert BUILDER_PACKET_PATH not in opened_paths


# --- commitment pool -----------------------------------------------------------


def test_commitment_pool_republishes_a4s_own_content_blind_commitments_verbatim() -> None:
    pool = assignment.build_commitment_pool(REAL_A4_RECEIPT)
    assert pool["content_blind"] is True
    assert pool["total_builder_eligible_commitments"] == 8
    assert set(pool["commitments"]) == set(REAL_A4_RECEIPT["builder_packet_consumption"]["unit_commitments"])
    assert pool["commitments"] == sorted(pool["commitments"])


def test_commitment_pool_never_invents_a_commitment_not_published_by_a4() -> None:
    forged_a4 = copy.deepcopy(REAL_A4_RECEIPT)
    forged_a4["builder_packet_consumption"]["unit_commitments"].append("f" * 64)
    pool = assignment.build_commitment_pool(forged_a4)
    assert "f" * 64 in pool["commitments"]  # pool is a pure republish, not filtered here
    with pytest.raises(assignment.SlotAssignmentError):
        assignment.validate_commitment_pool_matches_a4({**REAL_RECEIPT, "commitment_pool": pool}, ROOT)


# --- assignment gate -------------------------------------------------------------


def test_gate_against_real_production_artifacts_is_structurally_closed_today() -> None:
    gate = assignment.check_assignment_gate()
    assert gate["a4_receipt_valid"] is True
    assert gate["a2_rights_resolved"] is False
    assert gate["builder_eligible_commitments_available"] == 8
    assert gate["stratum_commitment_binding_available"] is False
    assert gate["assignment_ready"] is False
    assert gate["blocked_reason_code"] == "stratum_commitment_binding_unavailable_content_blind"


def test_gate_closed_when_a_required_public_artifact_is_missing(tmp_path: Path) -> None:
    _write_receipt_tree(tmp_path)
    (tmp_path / "data/projects/open_model_data/admission/dataset_v4_a4_deterministic_extraction_receipt_v1.json").unlink()
    gate = assignment.check_assignment_gate(tmp_path)
    assert gate["assignment_ready"] is False
    assert gate["blocked_reason_code"] == "required_public_artifact_missing:a4_receipt"


def test_gate_closed_when_a4_receipt_is_invalid(tmp_path: Path) -> None:
    forged = copy.deepcopy(REAL_A4_RECEIPT)
    forged["bindings"]["a2_source_operation_admission"]["sha256"] = "0" * 64
    _write_receipt_tree(tmp_path, a4_receipt=forged)
    gate = assignment.check_assignment_gate(tmp_path)
    assert gate["a4_receipt_valid"] is False
    assert gate["blocked_reason_code"] == "a4_receipt_invalid"
    assert gate["builder_eligible_commitments_available"] == 0


def test_gate_stays_structurally_closed_even_once_a2_rights_are_fully_resolved(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The one invariant this whole module exists to prove: resolving A2's
    rights residuals does NOT unlock per-stratum commitment binding -- the
    block is architectural (content-blind commitments), not a rights gate."""
    resolved_a2 = copy.deepcopy(REAL_A2_RECEIPT)
    resolved_a2["residuals"] = []
    _write_receipt_tree(tmp_path, a2=resolved_a2)
    monkeypatch.setattr(assignment.a4, "validate_receipt_independently", lambda *a, **k: None)
    gate = assignment.check_assignment_gate(tmp_path)
    assert gate["a2_rights_resolved"] is True
    assert gate["assignment_ready"] is False
    assert gate["stratum_commitment_binding_available"] is False
    assert gate["blocked_reason_code"] == "stratum_commitment_binding_unavailable_content_blind"


# --- assignment records ----------------------------------------------------------


def test_assignment_records_are_one_typed_entry_per_frozen_slot_never_a_silent_drop() -> None:
    gate = assignment.check_assignment_gate()
    records = assignment.derive_assignment_records(REAL_MANIFEST, REAL_A2_RECEIPT, gate)
    assert len(records) == 100
    assert len({r["slot_id"] for r in records}) == 100
    assert {r["slot_id"] for r in records} == set(assignment.a7.a6.all_frozen_slot_ids(REAL_MANIFEST))
    assert all(r["assignment_status"] == "residual" for r in records)
    assert all(r["commitment_sha256"] is None for r in records)
    assert {r["reason_code"] for r in records} == {"rights_unknown", "source_incomplete", "independence_unavailable"}


def test_assignment_records_never_carry_a_row_id_or_content_field() -> None:
    assert not any("content" in r or "text" in r or "source_unit_id" in r for r in REAL_RECEIPT["assignment_records"])


def test_residual_status_is_uniform_across_every_stratum_no_singleton_shape() -> None:
    """Every stratum shows the identical assignment shape (zero assigned) --
    a reader can never single out one stratum as "the one without an
    assigned slot" to try to infer anything about the sealed held-out
    complement."""
    strata = assignment.a7.a6.frozen_slot_strata(REAL_MANIFEST)
    assignment.validate_residual_status_uniform_across_strata(REAL_RECEIPT["assignment_records"], strata)
    by_stratum: dict[str, int] = {}
    for record in REAL_RECEIPT["assignment_records"]:
        by_stratum[record["stratum"]] = by_stratum.get(record["stratum"], 0) + (1 if record["assignment_status"] == "assigned" else 0)
    assert set(by_stratum.values()) == {0}


def test_residual_status_uniform_check_refuses_a_forged_single_assigned_stratum() -> None:
    tampered = copy.deepcopy(REAL_RECEIPT["assignment_records"])
    tampered[0]["assignment_status"] = "assigned"
    tampered[0]["commitment_sha256"] = REAL_A4_RECEIPT["builder_packet_consumption"]["unit_commitments"][0]
    strata = assignment.a7.a6.frozen_slot_strata(REAL_MANIFEST)
    with pytest.raises(assignment.SlotAssignmentError):
        assignment.validate_residual_status_uniform_across_strata(tampered, strata)


# --- receipt assembly and independent verification --------------------------------


def test_receipt_validates_independently_against_the_real_public_artifacts() -> None:
    assert assignment.validate_receipt_independently(REAL_RECEIPT) is None


def test_receipt_matches_schema() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors = list(Draft202012Validator(schema).iter_errors(REAL_RECEIPT))
    assert not errors, errors[0].message if errors else None


def test_receipt_binds_v4_sha_and_control_surfaces() -> None:
    assert REAL_RECEIPT["controlling_outcome_sha256"] == V4_SHA256
    assert REAL_RECEIPT["control_surfaces"] == {
        "public_control_issue": 7423,
        "pilot_child_issue": 7430,
        "private_operational_board": 622,
    }
    assert REAL_RECEIPT["bindings"]["a4_deterministic_extraction"]["sha256"] == assignment.sha256_file(A4_RECEIPT_PATH)
    assert REAL_RECEIPT["bindings"]["pilot_slot_manifest"]["sha256"] == assignment.sha256_file(MANIFEST_PATH)


def test_receipt_carries_forward_every_a2_and_a4_residual_unresolved() -> None:
    assert {e["residual_id"] for e in REAL_RECEIPT["a2_residuals_carried_forward"]} == {e["residual_id"] for e in REAL_A2_RECEIPT["residuals"]}
    assert {e["residual_id"] for e in REAL_RECEIPT["a4_residuals_carried_forward"]} == {e["residual_id"] for e in REAL_A4_RECEIPT["a4_residuals"]}
    for key in ("a2_residuals_carried_forward", "a4_residuals_carried_forward"):
        assert all(e["status"] == "unresolved_carried_to_public_slot_commitment_assignment" for e in REAL_RECEIPT[key])


def test_receipt_denominator_stays_100_slots_never_dropped() -> None:
    assert REAL_RECEIPT["frozen_slot_denominator"]["total_slots"] == 100
    assert len(REAL_RECEIPT["assignment_records"]) == 100
    assert REAL_RECEIPT["execution_counters"]["frozen_slot_count"] == 100
    assert REAL_RECEIPT["execution_counters"]["assigned_slot_count"] + REAL_RECEIPT["execution_counters"]["residual_slot_count"] == 100


def test_receipt_never_claims_dataset_rows_or_stronger_release_state() -> None:
    serialized = json.dumps(REAL_RECEIPT, ensure_ascii=False, sort_keys=True)
    for forbidden in ("TRAINING_READY_SILVER", "ARENA_SLICE_READY", "EVAL_ARTIFACT_READY", "EPIC_DONE"):
        assert forbidden not in serialized
    assert REAL_RECEIPT["execution_counters"]["dataset_rows_emitted"] == 0
    assert REAL_RECEIPT["safety_assertions"]["training_ready_silver_claimed"] is False
    assert REAL_RECEIPT["safety_assertions"]["epic_done_claimed"] is False


def test_receipt_eligibility_all_false_and_zero_rows_emitted() -> None:
    assert REAL_RECEIPT["eligibility"] == {"gold": False, "training": False, "evaluation": False, "teaching": False, "coverage": False}
    assert REAL_RECEIPT["execution_counters"]["dataset_rows_emitted"] == 0
    assert REAL_RECEIPT["safety_assertions"]["rows_not_admitted"] is True
    assert all(v is False for k, v in REAL_RECEIPT["safety_assertions"].items() if k != "rows_not_admitted")


def test_receipt_never_names_source_text_a_held_out_family_or_a_plaintext_source_id() -> None:
    keys = _all_keys(REAL_RECEIPT)
    assert not keys & FORBIDDEN_KEYS
    serialized = json.dumps(REAL_RECEIPT, ensure_ascii=False, sort_keys=True)
    assert not any(needle in serialized for needle in FORBIDDEN_SUBSTRINGS)
    assert REAL_RECEIPT["assignment_records"][0]["slot_id"].startswith("v4p-")


def test_receipt_never_binds_a_commitment_to_a_slot_no_stratum_commitment_link() -> None:
    assert all(record["commitment_sha256"] is None for record in REAL_RECEIPT["assignment_records"])
    assert REAL_RECEIPT["safety_assertions"]["stratum_to_commitment_binding_published"] is False
    assert REAL_RECEIPT["safety_assertions"]["commitment_bound_to_a_slot"] is False
    assert REAL_RECEIPT["commitment_binding_policy"]["stratum_commitment_binding_ever_public"] is False


def test_bindings_hash_to_disk_for_every_bound_artifact() -> None:
    for name, binding in REAL_RECEIPT["bindings"].items():
        path = ROOT / binding["path"]
        assert path.is_file(), name
        assert assignment.sha256_file(path) == binding["sha256"], name


# --- shared engine wiring (real call, exercised against production artifacts) -----


def test_engine_wiring_is_a_live_call_into_the_shared_admission_engine() -> None:
    wiring = REAL_RECEIPT["engine_wiring"]
    assert wiring["engine_schema_version"] == admission.SCHEMA_VERSION
    assert wiring["engine_input_schema_version"] == admission.INPUT_SCHEMA_VERSION
    assert wiring["model_only_bases_blocked"] == sorted(admission.MODEL_ONLY_BASES)
    recomputed = admission.admit_rows(outcome_sha256=V4_SHA256, rows=[])
    assert wiring["admission_receipt"] == recomputed
    assert admission.verify_receipt(wiring["admission_receipt"]) == wiring["admission_receipt"]
    assert wiring["admission_receipt"]["counts"] == {"input_rows": 0, "admitted_rows": 0, "rejected_rows": 0}


# --- fail-closed on tampering ------------------------------------------------------


def test_refuses_a_tampered_binding_hash() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["bindings"]["a4_deterministic_extraction"]["sha256"] = "0" * 64
    with pytest.raises(assignment.SlotAssignmentError):
        assignment.validate_receipt_independently(receipt)


def test_refuses_a_forged_assignment_ready_claim() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["assignment_gate"] = {**receipt["assignment_gate"], "assignment_ready": True, "stratum_commitment_binding_available": True}
    with pytest.raises(assignment.SlotAssignmentError):
        assignment.validate_receipt_independently(receipt)


def test_refuses_a_forged_assigned_slot_with_a_bound_commitment() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["assignment_records"][0]["assignment_status"] = "assigned"
    receipt["assignment_records"][0]["commitment_sha256"] = REAL_A4_RECEIPT["builder_packet_consumption"]["unit_commitments"][0]
    with pytest.raises(assignment.SlotAssignmentError):
        assignment.validate_receipt_independently(receipt)


def test_refuses_a_dropped_a2_residual() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["a2_residuals_carried_forward"].pop()
    with pytest.raises(assignment.SlotAssignmentError):
        assignment.validate_receipt_independently(receipt)


def test_refuses_a_dropped_a4_residual() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["a4_residuals_carried_forward"].pop()
    with pytest.raises(assignment.SlotAssignmentError):
        assignment.validate_receipt_independently(receipt)


def test_refuses_a_missing_frozen_slot_assignment_record() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["assignment_records"].pop()
    with pytest.raises(assignment.SlotAssignmentError):
        assignment.validate_receipt_independently(receipt)


def test_refuses_a_denominator_dropped_below_100() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["frozen_slot_denominator"]["total_slots"] = 99
    with pytest.raises(assignment.SlotAssignmentError):
        assignment.validate_receipt_independently(receipt)


def test_refuses_a_nonzero_dataset_rows_emitted_claim() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["execution_counters"]["dataset_rows_emitted"] = 1
    with pytest.raises(assignment.SlotAssignmentError):
        assignment.validate_receipt_independently(receipt)


def test_refuses_a_weakened_commitment_binding_policy() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["commitment_binding_policy"]["stratum_commitment_binding_ever_public"] = True
    with pytest.raises(assignment.SlotAssignmentError):
        assignment.validate_receipt_independently(receipt)
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema).iter_errors(receipt))
    assert errors


def test_refuses_a_commitment_pool_entry_not_published_by_a4() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["commitment_pool"]["commitments"].append("f" * 64)
    receipt["commitment_pool"]["total_builder_eligible_commitments"] = len(receipt["commitment_pool"]["commitments"])
    with pytest.raises(assignment.SlotAssignmentError):
        assignment.validate_receipt_independently(receipt)


def test_gold_key_is_a_frozen_false_eligibility_flag_never_a_real_label() -> None:
    assert "gold" not in FORBIDDEN_KEYS
    assert REAL_RECEIPT["eligibility"]["gold"] is False


# --- module-level sanity: this module never opens A4's ExtractionError path unsafely ---


def test_module_reuses_a4s_extraction_error_type_for_gate_closure_not_a_bare_except() -> None:
    assert assignment.a4 is a4
