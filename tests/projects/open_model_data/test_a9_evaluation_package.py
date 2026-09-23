"""V4 A9 evaluation package: held-out scoring, manifest/hash checks, and
consumer-view reproduction, wired to (never replacing) the shared
``v4_evaluation_scorer`` engine and bound to the merged A8 admission/assembly
receipt, the frozen V4 pilot slot manifest, and the V4 SHA.

Everything here runs against public artifacts only -- no ``batch_state/``,
no A3 held-out membership, no A4 private ledger -- so this suite passes in a
fresh checkout.
"""

from __future__ import annotations

import copy
import functools
import json
from pathlib import Path

import _v4_synthetic_chain_fixture as fixture
import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import v4_a9_evaluation_package as a9
from scripts.projects.open_model_data import v4_evaluation_scorer as scorer

ROOT = Path(__file__).resolve().parents[3]
ADMISSION = ROOT / "data/projects/open_model_data/admission"
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
RECEIPT = ADMISSION / "dataset_v4_a9_evaluation_package_receipt_v1.json"
SCHEMA = CONTRACTS / "dataset_v4_a9_evaluation_package_receipt_v1.schema.json"
A2_RECEIPT_PATH = ADMISSION / "dataset_v4_a2_source_operation_admission_receipt_v1.json"
A4_RECEIPT_PATH = ADMISSION / "dataset_v4_a4_deterministic_extraction_receipt_v1.json"
A5_RECEIPT_PATH = ADMISSION / "dataset_v4_a5_evidence_enrichment_receipt_v1.json"
A6_RECEIPT_PATH = ADMISSION / "dataset_v4_a6_blind_arena_receipt_v1.json"
A7_RECEIPT_PATH = ADMISSION / "dataset_v4_a7_original_row_factory_receipt_v1.json"
A8_RECEIPT_PATH = ADMISSION / "dataset_v4_a8_admission_assembly_receipt_v1.json"
MANIFEST_PATH = ADMISSION / "dataset_v4_pilot_slot_manifest_v1.json"

V4_SHA256 = "78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20"


@functools.cache
def _cached_json(path: Path) -> dict:
    """Read a JSON artifact on first use so collection survives a sparse worktree."""
    return json.loads(path.read_text(encoding="utf-8"))


FORBIDDEN_KEYS = a9.FORBIDDEN_KEYS
FORBIDDEN_SUBSTRINGS = a9.FORBIDDEN_SUBSTRINGS


def _all_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(_all_keys(item) for item in value.values()), set())
    if isinstance(value, list):
        return set().union(*(_all_keys(item) for item in value), set())
    return set()


def _write_receipt_tree(tmp_path: Path, *, a2=None, a4=None, a5=None, a6=None, a7=None, a8=None, manifest=None) -> Path:
    admission_dir = tmp_path / "data/projects/open_model_data/admission"
    admission_dir.mkdir(parents=True)
    (admission_dir / "dataset_v4_a2_source_operation_admission_receipt_v1.json").write_text(json.dumps(a2 if a2 is not None else _cached_json(A2_RECEIPT_PATH)))
    (admission_dir / "dataset_v4_a4_deterministic_extraction_receipt_v1.json").write_text(json.dumps(a4 if a4 is not None else _cached_json(A4_RECEIPT_PATH)))
    (admission_dir / "dataset_v4_a5_evidence_enrichment_receipt_v1.json").write_text(json.dumps(a5 if a5 is not None else _cached_json(A5_RECEIPT_PATH)))
    (admission_dir / "dataset_v4_a6_blind_arena_receipt_v1.json").write_text(json.dumps(a6 if a6 is not None else _cached_json(A6_RECEIPT_PATH)))
    (admission_dir / "dataset_v4_a7_original_row_factory_receipt_v1.json").write_text(json.dumps(a7 if a7 is not None else _cached_json(A7_RECEIPT_PATH)))
    (admission_dir / "dataset_v4_a8_admission_assembly_receipt_v1.json").write_text(json.dumps(a8 if a8 is not None else _cached_json(A8_RECEIPT_PATH)))
    (admission_dir / "dataset_v4_pilot_slot_manifest_v1.json").write_text(json.dumps(manifest if manifest is not None else _cached_json(MANIFEST_PATH)))
    return tmp_path


# --- evaluation gate --------------------------------------------------------------


def test_a9_gate_against_the_real_production_artifacts_stays_closed_today() -> None:
    gate = a9.check_evaluation_gate()
    assert gate["a8_receipt_valid"] is True
    assert gate["slots_prerequisite_eligible"] == 0
    assert gate["slots_upstream_complete"] == 0
    assert gate["slots_stage_complete"] == 0
    assert gate["slots_residual"] == 100
    assert gate["evaluation_slice_ready"] is False
    assert gate["blocked_reason_code"] == "no_slot_prerequisite_eligible"


def test_a9_gate_closed_when_a_required_public_artifact_is_missing(tmp_path: Path) -> None:
    _write_receipt_tree(tmp_path)
    (tmp_path / "data/projects/open_model_data/admission/dataset_v4_a8_admission_assembly_receipt_v1.json").unlink()
    gate = a9.check_evaluation_gate(tmp_path)
    assert gate["evaluation_slice_ready"] is False
    assert gate["blocked_reason_code"] == "required_public_artifact_missing:a8_receipt"


def test_a9_gate_closed_when_a8_receipt_is_invalid(tmp_path: Path) -> None:
    forged = copy.deepcopy(_cached_json(A8_RECEIPT_PATH))
    forged["bindings"]["a7_original_row_factory"]["sha256"] = "0" * 64
    _write_receipt_tree(tmp_path, a8=forged)
    gate = a9.check_evaluation_gate(tmp_path)
    assert gate["a8_receipt_valid"] is False
    assert gate["blocked_reason_code"] == "upstream_receipt_invalid"


def test_a9_gate_reports_eligible_but_stays_closed_pending_upstream_a8_completion(tmp_path: Path) -> None:
    """The A9-layer regression test for the same P1: A2 rights + manifest
    assignment resolving a stratum must never, by itself, produce a
    positive A9 completion count. Every validator here runs live (A6's,
    A7's, and A8's own real builders/validators, never stubbed) against a
    synthetic root where one stratum is genuinely prerequisite-eligible;
    A8's own ``a8_completions`` stays empty, so A9 -- which requires A8's
    positive completion evidence -- stays at 0 complete."""
    fixture.build_synthetic_chain_root(tmp_path, resolved_stratum="standard_correct")
    fixture.run_chain_a6_through_a9(tmp_path)

    gate = a9.check_evaluation_gate(tmp_path)
    assert gate["a8_receipt_valid"] is True
    assert gate["slots_prerequisite_eligible"] == 15
    assert gate["slots_upstream_complete"] == 0
    assert gate["slots_stage_complete"] == 0
    assert gate["slots_residual"] == 100
    assert gate["evaluation_slice_ready"] is False
    assert gate["blocked_reason_code"] == "eligible_slots_awaiting_upstream_stage_completion"


# --- A9 residuals + consumer reproduction view ------------------------------------


def test_a9_residuals_are_one_typed_entry_per_frozen_slot_never_a_silent_drop() -> None:
    gate = a9.check_evaluation_gate()
    residuals = a9.derive_a9_slot_residuals(_cached_json(MANIFEST_PATH), _cached_json(A2_RECEIPT_PATH), gate)
    assert len(residuals) == 100
    assert len({r["residual_id"] for r in residuals}) == 100
    assert {r["subject_id"] for r in residuals} == set(a9.a8.a7.a6.all_frozen_slot_ids(_cached_json(MANIFEST_PATH)))
    assert all(r["stage"] == "A9" for r in residuals)
    assert {r["reason_code"] for r in residuals} == {"rights_unknown", "source_incomplete", "independence_unavailable"}
    # Never a fabricated score standing in for the missing evaluation.
    assert not any("score" in r or "content" in r for r in residuals)


def test_a9_consumer_reproduction_view_is_empty_plus_residuals_never_a_fabricated_score() -> None:
    gate = a9.check_evaluation_gate()
    residuals = a9.derive_a9_slot_residuals(_cached_json(MANIFEST_PATH), _cached_json(A2_RECEIPT_PATH), gate)
    view = a9.build_consumer_reproduction_view(_cached_json(MANIFEST_PATH), _cached_json(A8_RECEIPT_PATH), residuals)
    assert len(view) == 100
    assert {entry["slot_id"] for entry in view} == set(a9.a8.a7.a6.all_frozen_slot_ids(_cached_json(MANIFEST_PATH)))
    assert all(entry["row_admitted"] is False and entry["row_id"] is None for entry in view)
    assert all(entry["scored"] is False and entry["score"] is None for entry in view)
    residual_ids = {r["residual_id"] for r in residuals}
    assert {entry["residual_id"] for entry in view} <= residual_ids
    serialized = json.dumps(view, ensure_ascii=False)
    assert "not_applicable" not in serialized


def test_a9_consumer_reproduction_fails_closed_when_a8_claims_a_row_without_a_matching_engine_admission() -> None:
    forged_a8 = copy.deepcopy(_cached_json(A8_RECEIPT_PATH))
    forged_a8["admitted_slice_view"][0] = {**forged_a8["admitted_slice_view"][0], "row_admitted": True, "row_id": "forged-row"}
    gate = a9.check_evaluation_gate()
    residuals = a9.derive_a9_slot_residuals(_cached_json(MANIFEST_PATH), _cached_json(A2_RECEIPT_PATH), gate)
    with pytest.raises(a9.EvaluationPackageError):
        a9.build_consumer_reproduction_view(_cached_json(MANIFEST_PATH), forged_a8, residuals)


def test_a9_consumer_reproduction_fails_closed_on_a_dropped_slot() -> None:
    forged_a8 = copy.deepcopy(_cached_json(A8_RECEIPT_PATH))
    forged_a8["admitted_slice_view"].pop()
    gate = a9.check_evaluation_gate()
    residuals = a9.derive_a9_slot_residuals(_cached_json(MANIFEST_PATH), _cached_json(A2_RECEIPT_PATH), gate)
    with pytest.raises(a9.EvaluationPackageError):
        a9.build_consumer_reproduction_view(_cached_json(MANIFEST_PATH), forged_a8, residuals)


# --- receipt assembly and independent verification --------------------------------


def test_a9_receipt_validates_independently_against_the_real_public_artifacts() -> None:
    assert a9.validate_receipt_independently(_cached_json(RECEIPT)) is None


def test_a9_receipt_matches_schema() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors = list(Draft202012Validator(schema).iter_errors(_cached_json(RECEIPT)))
    assert not errors, errors[0].message if errors else None


def test_a9_receipt_binds_v4_sha_and_control_surfaces() -> None:
    assert _cached_json(RECEIPT)["controlling_outcome_sha256"] == V4_SHA256
    assert _cached_json(RECEIPT)["control_surfaces"] == {
        "public_control_issue": 7423,
        "pilot_child_issue": 7430,
        "private_operational_board": 622,
    }
    assert _cached_json(RECEIPT)["bindings"]["a8_admission_assembly"]["sha256"] == a9.sha256_file(A8_RECEIPT_PATH)
    assert _cached_json(RECEIPT)["bindings"]["pilot_slot_manifest"]["sha256"] == a9.sha256_file(MANIFEST_PATH)


def test_a9_receipt_binds_the_merged_a8_receipt_by_its_known_public_sha() -> None:
    # The merged A8 receipt's public sha256, frozen at dispatch time (PR #7662 repair 1:
    # repaired stale pin, rippling from db80476d0a's A7 P1 fix through A8's receipt content).
    assert a9.sha256_file(A8_RECEIPT_PATH) == "a5e3aa667d8c539cee42cea42f13e42696d14e3be9f19097e657d7ed8cafcbb0"


def test_a9_receipt_carries_forward_every_a2_a4_a5_a6_a7_a8_residual_unresolved() -> None:
    assert {e["residual_id"] for e in _cached_json(RECEIPT)["a2_residuals_carried_forward"]} == {e["residual_id"] for e in _cached_json(A2_RECEIPT_PATH)["residuals"]}
    assert {e["residual_id"] for e in _cached_json(RECEIPT)["a4_residuals_carried_forward"]} == {e["residual_id"] for e in _cached_json(A4_RECEIPT_PATH)["a4_residuals"]}
    assert {e["residual_id"] for e in _cached_json(RECEIPT)["a5_residuals_carried_forward"]} == {e["residual_id"] for e in _cached_json(A5_RECEIPT_PATH)["a5_residuals"]}
    assert {e["residual_id"] for e in _cached_json(RECEIPT)["a6_residuals_carried_forward"]} == {e["residual_id"] for e in _cached_json(A6_RECEIPT_PATH)["a6_residuals"]}
    assert {e["residual_id"] for e in _cached_json(RECEIPT)["a7_residuals_carried_forward"]} == {e["residual_id"] for e in _cached_json(A7_RECEIPT_PATH)["a7_residuals"]}
    assert {e["residual_id"] for e in _cached_json(RECEIPT)["a8_residuals_carried_forward"]} == {e["residual_id"] for e in _cached_json(A8_RECEIPT_PATH)["a8_residuals"]}
    for key in (
        "a2_residuals_carried_forward",
        "a4_residuals_carried_forward",
        "a5_residuals_carried_forward",
        "a6_residuals_carried_forward",
        "a7_residuals_carried_forward",
        "a8_residuals_carried_forward",
    ):
        assert all(e["status"] == "unresolved_carried_to_a9" for e in _cached_json(RECEIPT)[key])


def test_a9_receipt_does_not_claim_eval_artifact_ready_while_the_gate_is_closed() -> None:
    assert _cached_json(RECEIPT)["evaluation_gate"]["evaluation_slice_ready"] is False
    assert _cached_json(RECEIPT)["status"] != "EVAL_ARTIFACT_READY"
    assert _cached_json(RECEIPT)["execution_counters"]["slots_prerequisite_eligible"] == 0
    assert _cached_json(RECEIPT)["execution_counters"]["slots_stage_complete"] == 0
    assert _cached_json(RECEIPT)["execution_counters"]["slots_residual"] == 100


def test_a9_receipt_never_claims_training_ready_silver_arena_slice_ready_or_admitted_slice_ready() -> None:
    serialized = json.dumps(_cached_json(RECEIPT), ensure_ascii=False, sort_keys=True)
    assert "TRAINING_READY_SILVER" not in serialized
    assert "ARENA_SLICE_READY" not in serialized
    assert "ADMITTED_SLICE_READY" not in serialized
    assert _cached_json(RECEIPT)["safety_assertions"]["training_ready_silver_claimed"] is False
    assert _cached_json(RECEIPT)["safety_assertions"]["arena_slice_ready_claimed"] is False
    assert _cached_json(RECEIPT)["safety_assertions"]["admitted_slice_ready_claimed"] is False
    assert _cached_json(RECEIPT)["safety_assertions"]["eval_artifact_ready_claimed"] is False


def test_a9_receipt_eligibility_all_false_and_zero_rows_emitted() -> None:
    assert _cached_json(RECEIPT)["eligibility"] == {"gold": False, "training": False, "evaluation": False, "teaching": False, "coverage": False}
    assert _cached_json(RECEIPT)["execution_counters"]["dataset_rows_emitted"] == 0
    assert _cached_json(RECEIPT)["execution_counters"]["candidate_rows_scored"] == 0
    assert _cached_json(RECEIPT)["execution_counters"]["rows_considered_for_scoring"] == 0
    assert _cached_json(RECEIPT)["safety_assertions"]["rows_not_admitted"] is True
    assert all(v is False for k, v in _cached_json(RECEIPT)["safety_assertions"].items() if k != "rows_not_admitted")


def test_a9_receipt_never_names_source_text_a_held_out_family_or_a_plaintext_source_id() -> None:
    keys = _all_keys(_cached_json(RECEIPT))
    assert not keys & FORBIDDEN_KEYS
    serialized = json.dumps(_cached_json(RECEIPT), ensure_ascii=False, sort_keys=True)
    assert not any(needle in serialized for needle in FORBIDDEN_SUBSTRINGS)
    assert _cached_json(RECEIPT)["a9_residuals"][0]["subject_id"].startswith("v4p-")


def test_a9_receipt_never_opens_held_out_membership() -> None:
    assert _cached_json(RECEIPT)["safety_assertions"]["held_out_membership_referenced"] is False
    assert _cached_json(RECEIPT)["safety_assertions"]["held_out_membership_opened"] is False
    assert _cached_json(RECEIPT)["safety_assertions"]["heldout_family_identity_leaked"] is False


def test_a9_bindings_hash_to_disk_for_every_bound_artifact() -> None:
    from learn_ukrainian_v4_runtime.resources import resource_root

    for name, binding in _cached_json(RECEIPT)["bindings"].items():
        path = resource_root() / (
            "provenance/v1/blobs/sha256/" + binding["sha256"] + ".blob"
            if binding["path"].startswith("scripts/") else binding["path"]
        )
        assert path.is_file(), name
        assert a9.sha256_file(path) == binding["sha256"], name


# --- shared scorer engine wiring (real call, exercised against production artifacts) ---


def test_a9_scorer_wiring_is_a_live_call_into_the_shared_evaluation_scorer_engine() -> None:
    wiring = _cached_json(RECEIPT)["scorer_wiring"]
    assert wiring["scorer_schema_version"] == scorer.SCHEMA_VERSION
    assert wiring["scorer_input_schema_version"] == scorer.INPUT_SCHEMA_VERSION
    assert wiring["unscorable_residual_code"] == scorer.UNSCORABLE_RESIDUAL_CODE
    recomputed = scorer.score_rows(outcome_sha256=V4_SHA256, admitted_rows=[])
    assert wiring["scoring_receipt"] == recomputed
    assert scorer.verify_receipt(wiring["scoring_receipt"]) == wiring["scoring_receipt"]
    assert wiring["scoring_receipt"]["counts"] == {"input_rows": 0, "scored_rows": 0, "unscored_rows": 0}


def test_a9_scorer_engine_never_fabricates_a_real_score() -> None:
    """Proves A9 wires the *unmodified* shared scorer: any row it is asked to
    score comes back unscored with a typed residual code, never a fabricated
    score standing in for the missing held-out reference."""
    row = {"row_id": "engine-self-test-row-01", "row_content_sha256": "a" * 64}
    receipt = scorer.score_row(row)
    assert receipt["scored"] is False
    assert receipt["score"] is None
    assert receipt["residual_code"] == "HELDOUT_REFERENCE_UNAVAILABLE"


# --- fail-closed on tampering ----------------------------------------------------


def test_a9_refuses_a_tampered_binding_hash() -> None:
    receipt = copy.deepcopy(_cached_json(RECEIPT))
    receipt["bindings"]["a8_admission_assembly"]["sha256"] = "0" * 64
    with pytest.raises(a9.EvaluationPackageError):
        a9.validate_receipt_independently(receipt)


def test_a9_refuses_a_forged_eval_artifact_ready_claim() -> None:
    receipt = copy.deepcopy(_cached_json(RECEIPT))
    receipt["status"] = "EVAL_ARTIFACT_READY"
    receipt["evaluation_gate"] = {**receipt["evaluation_gate"], "evaluation_slice_ready": True, "blocked_reason_code": None}
    with pytest.raises(a9.EvaluationPackageError):
        a9.validate_receipt_independently(receipt)


def test_a9_refuses_a_dropped_a8_residual() -> None:
    receipt = copy.deepcopy(_cached_json(RECEIPT))
    receipt["a8_residuals_carried_forward"].pop()
    with pytest.raises(a9.EvaluationPackageError):
        a9.validate_receipt_independently(receipt)


def test_a9_refuses_a_missing_frozen_slot_residual() -> None:
    receipt = copy.deepcopy(_cached_json(RECEIPT))
    receipt["a9_residuals"].pop()
    with pytest.raises(a9.EvaluationPackageError):
        a9.validate_receipt_independently(receipt)


def test_a9_refuses_a_dropped_consumer_reproduction_view_entry() -> None:
    receipt = copy.deepcopy(_cached_json(RECEIPT))
    receipt["consumer_reproduction_view"].pop()
    with pytest.raises(a9.EvaluationPackageError):
        a9.validate_receipt_independently(receipt)


def test_a9_refuses_a_forged_admitted_or_scored_row_in_the_consumer_view() -> None:
    receipt = copy.deepcopy(_cached_json(RECEIPT))
    receipt["consumer_reproduction_view"][0] = {**receipt["consumer_reproduction_view"][0], "row_admitted": True, "row_id": "forged-row"}
    with pytest.raises(a9.EvaluationPackageError):
        a9.validate_receipt_independently(receipt)


def test_a9_refuses_a_nonzero_dataset_rows_emitted_claim() -> None:
    receipt = copy.deepcopy(_cached_json(RECEIPT))
    receipt["execution_counters"]["dataset_rows_emitted"] = 1
    with pytest.raises(a9.EvaluationPackageError):
        a9.validate_receipt_independently(receipt)


def test_a9_refuses_a_fabricated_nonempty_scoring_receipt() -> None:
    receipt = copy.deepcopy(_cached_json(RECEIPT))
    receipt["scorer_wiring"]["scoring_receipt"] = scorer.score_rows(
        outcome_sha256=V4_SHA256,
        admitted_rows=[{"row_id": "forged-row", "row_content_sha256": "b" * 64}],
    )
    with pytest.raises(a9.EvaluationPackageError):
        a9.validate_receipt_independently(receipt)


def test_a9_schema_rejects_a_leaked_gold_label_value() -> None:
    receipt = copy.deepcopy(_cached_json(RECEIPT))
    receipt["eligibility"]["gold"] = True
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema).iter_errors(receipt))
    assert errors


def test_a9_gold_key_is_a_frozen_false_eligibility_flag_never_a_real_label() -> None:
    assert "gold" not in FORBIDDEN_KEYS
    assert _cached_json(RECEIPT)["eligibility"]["gold"] is False
