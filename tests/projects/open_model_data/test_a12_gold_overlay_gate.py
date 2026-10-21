"""V4 A12 later gold-overlay path: the typed gold-overlay eligibility receipt
bound to the merged A11 silver release gate receipt, the frozen V4 pilot slot
manifest, and the V4 SHA.

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
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import v4_a12_gold_overlay_gate as a12
from scripts.projects.open_model_data.paths import REGISTRY_OPEN_MODEL_DATA_DIR

ROOT = Path(__file__).resolve().parents[3]
ADMISSION = REGISTRY_OPEN_MODEL_DATA_DIR / "admission"
CONTRACTS = ROOT / "registry/projects/open_model_data/contracts"
RECEIPT = ADMISSION / "dataset_v4_a12_gold_overlay_gate_receipt_v1.json"
SCHEMA = CONTRACTS / "dataset_v4_a12_gold_overlay_gate_receipt_v1.schema.json"
A2_RECEIPT_PATH = ADMISSION / "dataset_v4_a2_source_operation_admission_receipt_v1.json"
A4_RECEIPT_PATH = ADMISSION / "dataset_v4_a4_deterministic_extraction_receipt_v1.json"
A5_RECEIPT_PATH = ADMISSION / "dataset_v4_a5_evidence_enrichment_receipt_v1.json"
A6_RECEIPT_PATH = ADMISSION / "dataset_v4_a6_blind_arena_receipt_v1.json"
A7_RECEIPT_PATH = ADMISSION / "dataset_v4_a7_original_row_factory_receipt_v1.json"
A8_RECEIPT_PATH = ADMISSION / "dataset_v4_a8_admission_assembly_receipt_v1.json"
A9_RECEIPT_PATH = ADMISSION / "dataset_v4_a9_evaluation_package_receipt_v1.json"
A10_RECEIPT_PATH = ADMISSION / "dataset_v4_a10_pilot_review_gate_receipt_v1.json"
A11_RECEIPT_PATH = ADMISSION / "dataset_v4_a11_silver_release_gate_receipt_v1.json"
MANIFEST_PATH = ADMISSION / "dataset_v4_pilot_slot_manifest_v1.json"

V4_SHA256 = "78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20"


@functools.cache
def _cached_json(path: Path) -> dict:
    """Read a JSON artifact on first use so collection survives a sparse worktree."""
    return json.loads(path.read_text(encoding="utf-8"))


FORBIDDEN_KEYS = a12.FORBIDDEN_KEYS
FORBIDDEN_SUBSTRINGS = a12.FORBIDDEN_SUBSTRINGS


def _all_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(_all_keys(item) for item in value.values()), set())
    if isinstance(value, list):
        return set().union(*(_all_keys(item) for item in value), set())
    return set()


def _write_receipt_tree(
    tmp_path: Path, *, a2=None, a4=None, a5=None, a6=None, a7=None, a8=None, a9=None, a10=None, a11=None, manifest=None
) -> Path:
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
    (admission_dir / "dataset_v4_a8_admission_assembly_receipt_v1.json").write_text(
        json.dumps(a8 if a8 is not None else _cached_json(A8_RECEIPT_PATH))
    )
    (admission_dir / "dataset_v4_a9_evaluation_package_receipt_v1.json").write_text(
        json.dumps(a9 if a9 is not None else _cached_json(A9_RECEIPT_PATH))
    )
    (admission_dir / "dataset_v4_a10_pilot_review_gate_receipt_v1.json").write_text(
        json.dumps(a10 if a10 is not None else _cached_json(A10_RECEIPT_PATH))
    )
    (admission_dir / "dataset_v4_a11_silver_release_gate_receipt_v1.json").write_text(
        json.dumps(a11 if a11 is not None else _cached_json(A11_RECEIPT_PATH))
    )
    (admission_dir / "dataset_v4_pilot_slot_manifest_v1.json").write_text(
        json.dumps(manifest if manifest is not None else _cached_json(MANIFEST_PATH))
    )
    return tmp_path


# --- gold overlay gate --------------------------------------------------------------


def test_a12_gate_against_the_real_production_artifacts_stays_closed_today() -> None:
    gate = a12.check_gold_overlay_gate()
    assert gate["a11_receipt_valid"] is True
    assert gate["model_agreement_exclusion_confirmed"] is True
    assert gate["all_slots_assigned"] is False
    assert gate["a2_rights_resolved"] is False
    assert gate["upstream_silver_release_ready"] is False
    assert gate["source_qualified_human_adjudication_recorded"] is False
    assert gate["gold_overlay_executed"] is False
    assert gate["gold_overlay_slice_ready"] is False
    assert gate["blocked_reason_code"] == "rights_unresolved_and_slots_unassigned"


def test_a12_gate_closed_when_a_required_public_artifact_is_missing(tmp_path: Path) -> None:
    _write_receipt_tree(tmp_path)
    (tmp_path / "data/projects/open_model_data/admission/dataset_v4_a11_silver_release_gate_receipt_v1.json").unlink()
    gate = a12.check_gold_overlay_gate(tmp_path)
    assert gate["gold_overlay_slice_ready"] is False
    assert gate["blocked_reason_code"] == "required_public_artifact_missing:a11_receipt"


def test_a12_gate_closed_when_a11_receipt_is_invalid(tmp_path: Path) -> None:
    forged = copy.deepcopy(_cached_json(A11_RECEIPT_PATH))
    forged["bindings"]["a10_pilot_review_gate"]["sha256"] = "0" * 64
    _write_receipt_tree(tmp_path, a11=forged)
    gate = a12.check_gold_overlay_gate(tmp_path)
    assert gate["a11_receipt_valid"] is False
    assert gate["blocked_reason_code"] == "a11_receipt_invalid"


def test_a12_gate_closed_when_the_live_engines_model_only_bases_drifts_from_the_frozen_expectation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_receipt_tree(tmp_path)
    monkeypatch.setattr(a12.a11.a10.a9.a8.admission, "MODEL_ONLY_BASES", frozenset({"model_agreement"}))
    gate = a12.check_gold_overlay_gate(tmp_path)
    assert gate["model_agreement_exclusion_confirmed"] is False
    assert gate["blocked_reason_code"] == "model_agreement_exclusion_engine_drifted"


def test_a12_gate_carries_the_upstream_a11_blocked_reason_once_rights_and_slots_clear(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    resolved_a2 = copy.deepcopy(_cached_json(A2_RECEIPT_PATH))
    resolved_a2["residuals"] = []
    assigned_manifest = copy.deepcopy(_cached_json(MANIFEST_PATH))
    for series in assigned_manifest["slot_series"]:
        series["assignment_state"] = "ASSIGNED"
    _write_receipt_tree(tmp_path, a2=resolved_a2, manifest=assigned_manifest)
    monkeypatch.setattr(a12.a11, "validate_receipt_independently", lambda *a, **k: None)
    gate = a12.check_gold_overlay_gate(tmp_path)
    assert gate["a2_rights_resolved"] is True
    assert gate["all_slots_assigned"] is True
    assert gate["a11_receipt_valid"] is True
    # A11's own silver release gate is still closed in _cached_json(A11_RECEIPT_PATH).
    assert gate["upstream_silver_release_ready"] is False
    assert gate["gold_overlay_slice_ready"] is False
    assert gate["blocked_reason_code"] == "upstream_a11_blocked:rights_unresolved_and_slots_unassigned"


def test_a12_gate_stays_closed_even_once_upstream_a11_gate_reports_ready(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Proves the gate can never open by accident: even if every upstream
    flag flips true, ``source_qualified_human_adjudication_recorded`` and
    ``gold_overlay_executed`` have no execution mechanism and stay hardcoded
    False."""
    resolved_a2 = copy.deepcopy(_cached_json(A2_RECEIPT_PATH))
    resolved_a2["residuals"] = []
    assigned_manifest = copy.deepcopy(_cached_json(MANIFEST_PATH))
    for series in assigned_manifest["slot_series"]:
        series["assignment_state"] = "ASSIGNED"
    ready_a11 = copy.deepcopy(_cached_json(A11_RECEIPT_PATH))
    ready_a11["release_gate"] = {
        **ready_a11["release_gate"],
        "silver_release_slice_ready": True,
        "blocked_reason_code": None,
    }
    _write_receipt_tree(tmp_path, a2=resolved_a2, a11=ready_a11, manifest=assigned_manifest)
    monkeypatch.setattr(a12.a11, "validate_receipt_independently", lambda *a, **k: None)
    gate = a12.check_gold_overlay_gate(tmp_path)
    assert gate["upstream_silver_release_ready"] is True
    assert gate["source_qualified_human_adjudication_recorded"] is False
    assert gate["gold_overlay_executed"] is False
    assert gate["gold_overlay_slice_ready"] is False
    assert gate["blocked_reason_code"] == "gold_overlay_not_yet_executed_no_source_qualified_adjudication"


def test_a12_gate_refuses_when_manifest_drops_a_required_gate_id(tmp_path: Path) -> None:
    stripped_manifest = copy.deepcopy(_cached_json(MANIFEST_PATH))
    stripped_manifest["required_gate_ids"] = [
        g for g in stripped_manifest["required_gate_ids"] if g != "SILVER_FIRST_STABLE_IDS"
    ]
    _write_receipt_tree(tmp_path, manifest=stripped_manifest)
    with pytest.raises(a12.GoldOverlayGateError):
        a12.check_gold_overlay_gate(tmp_path)


# --- A12 residuals + gold overlay view ---------------------------------------


def test_a12_residuals_are_one_typed_entry_per_frozen_slot_never_a_silent_drop() -> None:
    gate = a12.check_gold_overlay_gate()
    residuals = a12.derive_a12_slot_residuals(_cached_json(MANIFEST_PATH), _cached_json(A2_RECEIPT_PATH), gate)
    assert len(residuals) == 100
    assert len({r["residual_id"] for r in residuals}) == 100
    assert {r["subject_id"] for r in residuals} == set(
        a12.a11.a10.a9.a8.a7.a6.all_frozen_slot_ids(_cached_json(MANIFEST_PATH))
    )
    assert all(r["stage"] == "A12" for r in residuals)
    assert {r["reason_code"] for r in residuals} == {"rights_unknown", "source_incomplete", "independence_unavailable"}
    # Never a fabricated gold-overlay verdict standing in for the missing released row.
    assert not any("gold" in r or "overlay" in r for r in residuals)


def test_a12_gold_overlay_view_is_unoverlaid_plus_residuals_never_a_fabricated_overlay() -> None:
    gate = a12.check_gold_overlay_gate()
    residuals = a12.derive_a12_slot_residuals(_cached_json(MANIFEST_PATH), _cached_json(A2_RECEIPT_PATH), gate)
    view = a12.build_gold_overlay_view(_cached_json(MANIFEST_PATH), _cached_json(A11_RECEIPT_PATH), residuals)
    assert len(view) == 100
    assert {entry["slot_id"] for entry in view} == set(
        a12.a11.a10.a9.a8.a7.a6.all_frozen_slot_ids(_cached_json(MANIFEST_PATH))
    )
    assert all(entry["silver_row_released"] is False for entry in view)
    assert all(entry["gold_overlay_required"] is True and entry["gold_overlay_applied"] is False for entry in view)
    assert all(entry["adjudicator_source_qualification"] is None and entry["gold_label_tier"] is None for entry in view)
    residual_ids = {r["residual_id"] for r in residuals}
    assert {entry["residual_id"] for entry in view} <= residual_ids


def test_a12_gold_overlay_view_fails_closed_on_a_dropped_slot() -> None:
    forged_a11 = copy.deepcopy(_cached_json(A11_RECEIPT_PATH))
    forged_a11["silver_release_view"].pop()
    gate = a12.check_gold_overlay_gate()
    residuals = a12.derive_a12_slot_residuals(_cached_json(MANIFEST_PATH), _cached_json(A2_RECEIPT_PATH), gate)
    with pytest.raises(a12.GoldOverlayGateError):
        a12.build_gold_overlay_view(_cached_json(MANIFEST_PATH), forged_a11, residuals)


def test_a12_gold_overlay_view_fails_closed_on_a_forged_gold_label_tier() -> None:
    forged_a11 = copy.deepcopy(_cached_json(A11_RECEIPT_PATH))
    forged_a11["silver_release_view"][0] = {**forged_a11["silver_release_view"][0], "label_tier": "gold"}
    gate = a12.check_gold_overlay_gate()
    residuals = a12.derive_a12_slot_residuals(_cached_json(MANIFEST_PATH), _cached_json(A2_RECEIPT_PATH), gate)
    with pytest.raises(a12.GoldOverlayGateError):
        a12.build_gold_overlay_view(_cached_json(MANIFEST_PATH), forged_a11, residuals)


# --- overlay packet (fixed contract) ------------------------------------------


# --- shared engine wiring (real call, zero rows today) -----------------------


def test_a12_engine_still_refuses_a_model_only_basis_for_authorship_evidence_and_rights_on_a_gold_row() -> None:
    """The exact invariant the binding contract calls out: hypotheses,
    votes, and agreement cannot independently admit gold either. Proven live
    against the real, unmodified shared engine, not merely declared."""
    admission = a12.a11.a10.a9.a8.admission
    row = {
        "row_id": "probe-row",
        "row_content_sha256": "0" * 64,
        "label_tier": "gold",
        "lineage": {"immutable": True, "source_ids": ["s1"], "evidence_ids": ["e1"]},
        "authorship": {"basis": "model_agreement"},
        "evidence": {"basis": "arena_vote"},
        "rights": {"basis": "model_vote"},
    }
    result = admission.evaluate_row(row)
    assert result["disposition"] == "rejected"
    assert "MODEL_AGREEMENT_CANNOT_SATISFY_AUTHORSHIP" in result["residual_codes"]
    assert "MODEL_AGREEMENT_CANNOT_SATISFY_EVIDENCE" in result["residual_codes"]
    assert "MODEL_AGREEMENT_CANNOT_SATISFY_RIGHTS" in result["residual_codes"]


# --- receipt assembly and independent verification --------------------------------


def test_a12_receipt_validates_independently_against_the_real_public_artifacts() -> None:
    assert a12.validate_receipt_independently(_cached_json(RECEIPT)) is None


def test_a12_receipt_matches_schema() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors = list(Draft202012Validator(schema).iter_errors(_cached_json(RECEIPT)))
    assert not errors, errors[0].message if errors else None


def test_a12_receipt_carries_forward_every_a2_a4_a5_a6_a7_a8_a9_a10_a11_residual_unresolved() -> None:
    assert {e["residual_id"] for e in _cached_json(RECEIPT)["a2_residuals_carried_forward"]} == {
        e["residual_id"] for e in _cached_json(A2_RECEIPT_PATH)["residuals"]
    }
    assert {e["residual_id"] for e in _cached_json(RECEIPT)["a4_residuals_carried_forward"]} == {
        e["residual_id"] for e in _cached_json(A4_RECEIPT_PATH)["a4_residuals"]
    }
    assert {e["residual_id"] for e in _cached_json(RECEIPT)["a5_residuals_carried_forward"]} == {
        e["residual_id"] for e in _cached_json(A5_RECEIPT_PATH)["a5_residuals"]
    }
    assert {e["residual_id"] for e in _cached_json(RECEIPT)["a6_residuals_carried_forward"]} == {
        e["residual_id"] for e in _cached_json(A6_RECEIPT_PATH)["a6_residuals"]
    }
    assert {e["residual_id"] for e in _cached_json(RECEIPT)["a7_residuals_carried_forward"]} == {
        e["residual_id"] for e in _cached_json(A7_RECEIPT_PATH)["a7_residuals"]
    }
    assert {e["residual_id"] for e in _cached_json(RECEIPT)["a8_residuals_carried_forward"]} == {
        e["residual_id"] for e in _cached_json(A8_RECEIPT_PATH)["a8_residuals"]
    }
    assert {e["residual_id"] for e in _cached_json(RECEIPT)["a9_residuals_carried_forward"]} == {
        e["residual_id"] for e in _cached_json(A9_RECEIPT_PATH)["a9_residuals"]
    }
    assert {e["residual_id"] for e in _cached_json(RECEIPT)["a10_residuals_carried_forward"]} == {
        e["residual_id"] for e in _cached_json(A10_RECEIPT_PATH)["a10_residuals"]
    }
    assert {e["residual_id"] for e in _cached_json(RECEIPT)["a11_residuals_carried_forward"]} == {
        e["residual_id"] for e in _cached_json(A11_RECEIPT_PATH)["a11_residuals"]
    }
    for key in (
        "a2_residuals_carried_forward",
        "a4_residuals_carried_forward",
        "a5_residuals_carried_forward",
        "a6_residuals_carried_forward",
        "a7_residuals_carried_forward",
        "a8_residuals_carried_forward",
        "a9_residuals_carried_forward",
        "a10_residuals_carried_forward",
        "a11_residuals_carried_forward",
    ):
        assert all(e["status"] == "unresolved_carried_to_a12" for e in _cached_json(RECEIPT)[key])


def test_a12_receipt_never_names_source_text_a_held_out_family_or_a_plaintext_source_id() -> None:
    keys = _all_keys(_cached_json(RECEIPT))
    assert not keys & FORBIDDEN_KEYS
    serialized = json.dumps(_cached_json(RECEIPT), ensure_ascii=False, sort_keys=True)
    assert not any(needle in serialized for needle in FORBIDDEN_SUBSTRINGS)
    assert _cached_json(RECEIPT)["a12_residuals"][0]["subject_id"].startswith("v4p-")


def test_a12_bindings_hash_to_disk_for_every_bound_artifact() -> None:
    from learn_ukrainian_v4_runtime.resources import resource_root

    for name, binding in _cached_json(RECEIPT)["bindings"].items():
        path = resource_root() / (
            "provenance/v1/blobs/sha256/" + binding["sha256"] + ".blob"
            if binding["path"].startswith("scripts/")
            else binding["path"]
        )
        assert path.is_file(), name
        assert a12.sha256_file(path) == binding["sha256"], name


# --- fail-closed on tampering ----------------------------------------------------


def test_a12_refuses_a_tampered_binding_hash() -> None:
    receipt = copy.deepcopy(_cached_json(RECEIPT))
    receipt["bindings"]["a11_silver_release_gate"]["sha256"] = "0" * 64
    with pytest.raises(a12.GoldOverlayGateError):
        a12.validate_receipt_independently(receipt)


def test_a12_refuses_a_forged_gold_upgrade_ready_claim() -> None:
    receipt = copy.deepcopy(_cached_json(RECEIPT))
    receipt["status"] = "GOLD_UPGRADE_READY"
    receipt["overlay_gate"] = {**receipt["overlay_gate"], "gold_overlay_slice_ready": True, "blocked_reason_code": None}
    with pytest.raises(a12.GoldOverlayGateError):
        a12.validate_receipt_independently(receipt)


def test_a12_refuses_a_dropped_a11_residual() -> None:
    receipt = copy.deepcopy(_cached_json(RECEIPT))
    receipt["a11_residuals_carried_forward"].pop()
    with pytest.raises(a12.GoldOverlayGateError):
        a12.validate_receipt_independently(receipt)


def test_a12_refuses_a_nonzero_dataset_rows_emitted_claim() -> None:
    receipt = copy.deepcopy(_cached_json(RECEIPT))
    receipt["execution_counters"]["dataset_rows_emitted"] = 1
    with pytest.raises(a12.GoldOverlayGateError):
        a12.validate_receipt_independently(receipt)


def test_a12_refuses_a_weakened_overlay_packet() -> None:
    receipt = copy.deepcopy(_cached_json(RECEIPT))
    receipt["overlay_packet"]["model_agreement_admits_gold"] = True
    with pytest.raises(a12.GoldOverlayGateError):
        a12.validate_receipt_independently(receipt)


def test_a12_refuses_a_weakened_model_agreement_quarantine() -> None:
    receipt = copy.deepcopy(_cached_json(RECEIPT))
    receipt["model_agreement_quarantine"]["self_adjudication_admits_gold"] = True
    with pytest.raises(a12.GoldOverlayGateError):
        a12.validate_receipt_independently(receipt)


def test_a12_refuses_a_tampered_model_only_bases_blocked_list() -> None:
    receipt = copy.deepcopy(_cached_json(RECEIPT))
    receipt["engine_wiring"]["model_only_bases_blocked"] = ["model_agreement"]
    with pytest.raises(a12.GoldOverlayGateError):
        a12.validate_receipt_independently(receipt)
