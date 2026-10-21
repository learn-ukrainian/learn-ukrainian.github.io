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
import functools
import json
from pathlib import Path

import pytest

from scripts.projects.open_model_data import v4_a8_admission_assembly as a8
from scripts.projects.open_model_data import v4_original_row_admission as admission
from scripts.projects.open_model_data.paths import REGISTRY_OPEN_MODEL_DATA_DIR

ADMISSION = REGISTRY_OPEN_MODEL_DATA_DIR / "admission"
RECEIPT = ADMISSION / "dataset_v4_a8_admission_assembly_receipt_v1.json"
A2_RECEIPT_PATH = ADMISSION / "dataset_v4_a2_source_operation_admission_receipt_v1.json"
A4_RECEIPT_PATH = ADMISSION / "dataset_v4_a4_deterministic_extraction_receipt_v1.json"
A5_RECEIPT_PATH = ADMISSION / "dataset_v4_a5_evidence_enrichment_receipt_v1.json"
A6_RECEIPT_PATH = ADMISSION / "dataset_v4_a6_blind_arena_receipt_v1.json"
A7_RECEIPT_PATH = ADMISSION / "dataset_v4_a7_original_row_factory_receipt_v1.json"
MANIFEST_PATH = ADMISSION / "dataset_v4_pilot_slot_manifest_v1.json"

V4_SHA256 = "78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20"


@functools.cache
def _cached_json(path: Path) -> dict:
    """Read a JSON artifact on first use so collection survives a sparse worktree."""
    return json.loads(path.read_text(encoding="utf-8"))


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
    (admission_dir / "dataset_v4_a2_source_operation_admission_receipt_v1.json").write_text(
        json.dumps(a2 if a2 is not None else _cached_json(A2_RECEIPT_PATH))
    )
    (admission_dir / "dataset_v4_a4_deterministic_extraction_receipt_v1.json").write_text(
        json.dumps(a4 if a4 is not None else _cached_json(A4_RECEIPT_PATH))
    )
    (admission_dir / "dataset_v4_a5_evidence_enrichment_receipt_v1.json").write_text(
        json.dumps(a5 if a5 is not None else _cached_json(A5_RECEIPT_PATH))
    )
    (admission_dir / "dataset_v4_a6_blind_arena_receipt_v1.json").write_text(
        json.dumps(a6 if a6 is not None else _cached_json(A6_RECEIPT_PATH))
    )
    (admission_dir / "dataset_v4_a7_original_row_factory_receipt_v1.json").write_text(
        json.dumps(a7 if a7 is not None else _cached_json(A7_RECEIPT_PATH))
    )
    (admission_dir / "dataset_v4_pilot_slot_manifest_v1.json").write_text(
        json.dumps(manifest if manifest is not None else _cached_json(MANIFEST_PATH))
    )
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
    forged = copy.deepcopy(_cached_json(A7_RECEIPT_PATH))
    forged["bindings"]["a6_blind_arena"]["sha256"] = "0" * 64
    _write_receipt_tree(tmp_path, a7=forged)
    gate = a8.check_assembly_gate(tmp_path)
    assert gate["a7_receipt_valid"] is False
    assert gate["blocked_reason_code"] == "upstream_receipt_invalid"


# --- A8 residuals + admitted slice view ------------------------------------------


def test_a8_residuals_are_one_typed_entry_per_frozen_slot_never_a_silent_drop() -> None:
    gate = a8.check_assembly_gate()
    residuals = a8.derive_a8_slot_residuals(_cached_json(MANIFEST_PATH), _cached_json(A2_RECEIPT_PATH), gate)
    assert len(residuals) == 100
    assert len({r["residual_id"] for r in residuals}) == 100
    assert {r["subject_id"] for r in residuals} == set(a8.a7.a6.all_frozen_slot_ids(_cached_json(MANIFEST_PATH)))
    assert all(r["stage"] == "A8" for r in residuals)
    assert {r["reason_code"] for r in residuals} == {"rights_unknown", "source_incomplete", "independence_unavailable"}
    # Never a fabricated row standing in for the missing admitted row.
    assert not any("row_id" in r or "content" in r for r in residuals)


def test_a8_admitted_slice_view_is_empty_plus_residuals_never_not_applicable() -> None:
    gate = a8.check_assembly_gate()
    residuals = a8.derive_a8_slot_residuals(_cached_json(MANIFEST_PATH), _cached_json(A2_RECEIPT_PATH), gate)
    view = a8.build_admitted_slice_view(_cached_json(MANIFEST_PATH), residuals)
    assert len(view) == 100
    assert {entry["slot_id"] for entry in view} == set(a8.a7.a6.all_frozen_slot_ids(_cached_json(MANIFEST_PATH)))
    assert all(entry["row_admitted"] is False and entry["row_id"] is None for entry in view)
    residual_ids = {r["residual_id"] for r in residuals}
    assert {entry["residual_id"] for entry in view} <= residual_ids
    serialized = json.dumps(view, ensure_ascii=False)
    assert "not_applicable" not in serialized


# --- receipt assembly and independent verification ------------------------------


def test_a8_receipt_validates_independently_against_the_real_public_artifacts() -> None:
    assert a8.validate_receipt_independently(_cached_json(RECEIPT)) is None


def test_a8_receipt_never_names_source_text_a_held_out_family_or_a_plaintext_source_id() -> None:
    keys = _all_keys(_cached_json(RECEIPT))
    assert not keys & FORBIDDEN_KEYS
    serialized = json.dumps(_cached_json(RECEIPT), ensure_ascii=False, sort_keys=True)
    assert not any(needle in serialized for needle in FORBIDDEN_SUBSTRINGS)
    assert _cached_json(RECEIPT)["a8_residuals"][0]["subject_id"].startswith("v4p-")


def test_a8_bindings_hash_to_disk_for_every_bound_artifact() -> None:
    from learn_ukrainian_v4_runtime.resources import resource_root

    for name, binding in _cached_json(RECEIPT)["bindings"].items():
        path = resource_root() / (
            "provenance/v1/blobs/sha256/" + binding["sha256"] + ".blob"
            if binding["path"].startswith("scripts/")
            else binding["path"]
        )
        assert path.is_file(), name
        assert a8.sha256_file(path) == binding["sha256"], name


# --- shared engine wiring (real call, exercised against production artifacts) ---


def test_a8_engine_wiring_is_a_live_call_into_the_shared_admission_engine() -> None:
    wiring = _cached_json(RECEIPT)["engine_wiring"]
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
        "lineage": {
            "immutable": True,
            "source_ids": ["engine-self-test-source"],
            "evidence_ids": ["engine-self-test-evidence"],
        },
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
    assert receipt["eligibility"] == {
        "gold": False,
        "training": False,
        "evaluation": False,
        "teaching": False,
        "coverage": False,
    }


# --- fail-closed on tampering ----------------------------------------------------


def test_a8_refuses_a_tampered_binding_hash() -> None:
    receipt = copy.deepcopy(_cached_json(RECEIPT))
    receipt["bindings"]["a7_original_row_factory"]["sha256"] = "0" * 64
    with pytest.raises(a8.AdmissionAssemblyError):
        a8.validate_receipt_independently(receipt)


def test_a8_refuses_a_forged_admitted_slice_ready_claim() -> None:
    receipt = copy.deepcopy(_cached_json(RECEIPT))
    receipt["status"] = "ADMITTED_SLICE_READY"
    receipt["assembly_gate"] = {**receipt["assembly_gate"], "assembly_slice_ready": True, "blocked_reason_code": None}
    with pytest.raises(a8.AdmissionAssemblyError):
        a8.validate_receipt_independently(receipt)


def test_a8_refuses_a_dropped_a7_residual() -> None:
    receipt = copy.deepcopy(_cached_json(RECEIPT))
    receipt["a7_residuals_carried_forward"].pop()
    with pytest.raises(a8.AdmissionAssemblyError):
        a8.validate_receipt_independently(receipt)


def test_a8_refuses_a_dropped_admitted_slice_view_entry() -> None:
    receipt = copy.deepcopy(_cached_json(RECEIPT))
    receipt["admitted_slice_view"].pop()
    with pytest.raises(a8.AdmissionAssemblyError):
        a8.validate_receipt_independently(receipt)


def test_a8_refuses_a_forged_admitted_row_in_the_slice_view() -> None:
    receipt = copy.deepcopy(_cached_json(RECEIPT))
    receipt["admitted_slice_view"][0] = {
        **receipt["admitted_slice_view"][0],
        "row_admitted": True,
        "row_id": "forged-row",
    }
    with pytest.raises(a8.AdmissionAssemblyError):
        a8.validate_receipt_independently(receipt)


def test_a8_refuses_a_nonzero_dataset_rows_emitted_claim() -> None:
    receipt = copy.deepcopy(_cached_json(RECEIPT))
    receipt["execution_counters"]["dataset_rows_emitted"] = 1
    with pytest.raises(a8.AdmissionAssemblyError):
        a8.validate_receipt_independently(receipt)


def test_a8_refuses_a_fabricated_nonempty_engine_admission_row() -> None:
    receipt = copy.deepcopy(_cached_json(RECEIPT))
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
