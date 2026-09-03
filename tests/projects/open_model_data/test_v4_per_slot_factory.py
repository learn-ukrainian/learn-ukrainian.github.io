"""V4 per-slot private factory: proves the global-AND root cause is gone
from A7 (and A8/A9, which copied the same bug) and that the new private
factory module never leaks a slot->HMAC/source-unit table, never claims a
public row, and never touches A3's held-out membership.

Everything here except the private-ledger permission checks runs against
public artifacts only -- no ``batch_state/`` required for the gate/receipt
functions themselves, so the bulk of this suite passes in a fresh checkout.
"""

from __future__ import annotations

import copy
import json
import stat
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import v4_a7_original_row_factory as a7
from scripts.projects.open_model_data import v4_a8_admission_assembly as a8
from scripts.projects.open_model_data import v4_a9_evaluation_package as a9
from scripts.projects.open_model_data import v4_per_slot_private_factory as factory

ROOT = Path(__file__).resolve().parents[3]
ADMISSION = ROOT / "data/projects/open_model_data/admission"
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
MANIFEST_PATH = ADMISSION / "dataset_v4_pilot_slot_manifest_v1.json"
A2_RECEIPT_PATH = ADMISSION / "dataset_v4_a2_source_operation_admission_receipt_v1.json"
A7_RECEIPT_PATH = ADMISSION / "dataset_v4_a7_original_row_factory_receipt_v1.json"
FACTORY_RECEIPT_PATH = ADMISSION / "dataset_v4_per_slot_private_factory_receipt_v1.json"
FACTORY_SCHEMA_PATH = CONTRACTS / "dataset_v4_per_slot_private_factory_receipt_v1.schema.json"

REAL_MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
REAL_A2_RECEIPT = json.loads(A2_RECEIPT_PATH.read_text(encoding="utf-8"))
REAL_A7_RECEIPT = json.loads(A7_RECEIPT_PATH.read_text(encoding="utf-8"))
REAL_FACTORY_RECEIPT = json.loads(FACTORY_RECEIPT_PATH.read_text(encoding="utf-8"))

# The forbidden slot->HMAC/source-unit vocabulary this dispatch exists to
# keep out of every public V4 artifact -- see PR #7646's own
# COMMITMENT_BINDING_POLICY and the binding contract's rights/firewall.
FORBIDDEN_PUBLIC_TERMS = ("commitment_sha256", "commitment_hmac", "slot_commitment", "source_unit_id", "heldout_membership")


def _all_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(_all_keys(item) for item in value.values()), set())
    if isinstance(value, list):
        return set().union(*(_all_keys(item) for item in value), set())
    return set()


def _resolved_a2_receipt(resolved_strata: set[str]) -> dict[str, object]:
    """A synthetic A2 receipt where only ``resolved_strata`` have their
    residual cleared -- the rest keep their real, unresolved residual. Used
    to prove per-slot (not all-or-nothing) readiness."""
    receipt = copy.deepcopy(REAL_A2_RECEIPT)
    cleared_residual_ids = set()
    for coverage in receipt["stratum_coverage_map"]:
        if coverage["stratum"] in resolved_strata:
            cleared_residual_ids.update(coverage["residual_ids"])
            coverage["residual_ids"] = []
    receipt["residuals"] = [r for r in receipt["residuals"] if r["residual_id"] not in cleared_residual_ids]
    return receipt


# --- root cause: per_slot_readiness is a pure per-slot function, never a --
# --- single global AND ------------------------------------------------------


def test_per_slot_readiness_covers_every_frozen_slot_exactly_once() -> None:
    readiness = a7.per_slot_readiness(REAL_MANIFEST, REAL_A2_RECEIPT)
    assert len(readiness) == 100
    assert len({r["slot_id"] for r in readiness}) == 100
    assert {r["slot_id"] for r in readiness} == set(a7.a6.all_frozen_slot_ids(REAL_MANIFEST))


def test_per_slot_readiness_against_real_production_data_is_zero_ready_hundred_residual() -> None:
    # Matches the binding contract's own "0 assigned / 100 residual" count.
    readiness = a7.per_slot_readiness(REAL_MANIFEST, REAL_A2_RECEIPT)
    assert sum(1 for r in readiness if r["slot_ready"]) == 0
    assert sum(1 for r in readiness if not r["slot_ready"]) == 100


def test_per_slot_readiness_resolving_one_stratum_never_needs_every_other_stratum_resolved() -> None:
    """The regression test for the root cause: the old gate computed
    ``rights_resolved = len(a2_receipt["residuals"]) == 0`` -- a single
    boolean across all eight strata -- so resolving just one stratum's
    residual could never flip any slot to ready while a single other
    stratum stayed open. The fixed per-slot function must show a partial
    result here: exactly the resolved stratum's 15 slots ready, the other
    85 still residual."""
    resolved_a2 = _resolved_a2_receipt({"standard_correct"})
    assert len(resolved_a2["residuals"]) == 7  # seven of eight strata residuals remain

    assigned_manifest = copy.deepcopy(REAL_MANIFEST)
    for series in assigned_manifest["slot_series"]:
        if series["stratum"] == "standard_correct":
            series["assignment_state"] = "ASSIGNED"

    readiness = a7.per_slot_readiness(assigned_manifest, resolved_a2)
    ready_slots = {r["slot_id"] for r in readiness if r["slot_ready"]}
    assert len(ready_slots) == 15
    assert ready_slots == set(a7.a6.slot_ids_for_series(next(s for s in assigned_manifest["slot_series"] if s["stratum"] == "standard_correct")))
    # Every other stratum's slots stay exactly as unready as before --
    # resolving standard_correct never touched them.
    assert all(not r["slot_ready"] for r in readiness if r["stratum"] != "standard_correct")


# --- root cause fix proven at the gate level (A7, A8, A9) -------------------


def test_a7_gate_reports_partial_slots_ready_when_only_one_stratum_resolves(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    resolved_a2 = _resolved_a2_receipt({"literary"})
    assigned_manifest = copy.deepcopy(REAL_MANIFEST)
    for series in assigned_manifest["slot_series"]:
        if series["stratum"] == "literary":
            series["assignment_state"] = "ASSIGNED"

    admission_dir = tmp_path / "data/projects/open_model_data/admission"
    admission_dir.mkdir(parents=True)
    (admission_dir / "dataset_v4_a2_source_operation_admission_receipt_v1.json").write_text(json.dumps(resolved_a2))
    (admission_dir / "dataset_v4_pilot_slot_manifest_v1.json").write_text(json.dumps(assigned_manifest))
    a4_receipt = json.loads((ADMISSION / "dataset_v4_a4_deterministic_extraction_receipt_v1.json").read_text())
    a5_receipt = json.loads((ADMISSION / "dataset_v4_a5_evidence_enrichment_receipt_v1.json").read_text())
    a6_receipt = json.loads((ADMISSION / "dataset_v4_a6_blind_arena_receipt_v1.json").read_text())
    (admission_dir / "dataset_v4_a4_deterministic_extraction_receipt_v1.json").write_text(json.dumps(a4_receipt))
    (admission_dir / "dataset_v4_a5_evidence_enrichment_receipt_v1.json").write_text(json.dumps(a5_receipt))
    (admission_dir / "dataset_v4_a6_blind_arena_receipt_v1.json").write_text(json.dumps(a6_receipt))

    monkeypatch.setattr(a7.a6, "validate_receipt_independently", lambda *a, **k: None)
    gate = a7.check_factory_gate(tmp_path)

    # The old global-AND gate could only ever report 0 or 100 -- this proves
    # a genuine in-between value is now reachable.
    assert 0 < gate["slots_ready"] < 100
    assert gate["slots_ready"] == 15
    assert gate["slots_residual"] == 85
    assert gate["factory_slice_ready"] is False  # not *every* slot is ready, so the aggregate claim stays closed
    assert gate["blocked_reason_code"] == "partial_slots_pending_a2_a3"


def test_a7_gate_against_real_production_artifacts_is_still_all_residual() -> None:
    gate = a7.check_factory_gate()
    assert gate["slots_ready"] == 0
    assert gate["slots_residual"] == 100
    assert gate["factory_slice_ready"] is False


def test_a8_gate_against_real_production_artifacts_is_still_all_residual() -> None:
    gate = a8.check_assembly_gate()
    assert gate["slots_ready"] == 0
    assert gate["slots_residual"] == 100
    assert gate["assembly_slice_ready"] is False


def test_a9_gate_against_real_production_artifacts_is_still_all_residual() -> None:
    gate = a9.check_evaluation_gate()
    assert gate["slots_ready"] == 0
    assert gate["slots_residual"] == 100
    assert gate["evaluation_slice_ready"] is False


def test_a7_a8_a9_factory_gate_requires_no_longer_state_a_global_all_frozen_slots_assigned_requirement() -> None:
    assert REAL_A7_RECEIPT["factory_gate"]["requires"] == [
        "a6_receipt_independently_valid",
        "per_slot_a2_rights_resolved",
        "per_slot_manifest_assignment",
    ]
    assert "all_frozen_slots_assigned" not in json.dumps(REAL_A7_RECEIPT["factory_gate"])


# --- public receipts still hold every prior invariant -----------------------


def test_a7_receipt_still_validates_independently_after_the_per_slot_fix() -> None:
    assert a7.validate_receipt_independently(REAL_A7_RECEIPT) is None


def test_a8_receipt_still_validates_independently_after_the_per_slot_fix() -> None:
    receipt = json.loads((ADMISSION / "dataset_v4_a8_admission_assembly_receipt_v1.json").read_text())
    assert a8.validate_receipt_independently(receipt) is None


def test_a9_receipt_still_validates_independently_after_the_per_slot_fix() -> None:
    receipt = json.loads((ADMISSION / "dataset_v4_a9_evaluation_package_receipt_v1.json").read_text())
    assert a9.validate_receipt_independently(receipt) is None


# --- the new private factory module: public receipt -------------------------


def test_factory_receipt_matches_schema() -> None:
    schema = json.loads(FACTORY_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors = list(Draft202012Validator(schema).iter_errors(REAL_FACTORY_RECEIPT))
    assert not errors, errors[0].message if errors else None


def test_factory_receipt_validates_independently_against_real_public_artifacts() -> None:
    assert factory.validate_receipt_independently(REAL_FACTORY_RECEIPT) is None


def test_factory_receipt_denominator_is_the_frozen_100_public_slots() -> None:
    assert REAL_FACTORY_RECEIPT["frozen_slot_denominator"]["total_slots"] == 100
    all_ids = [slot_id for stratum in REAL_FACTORY_RECEIPT["frozen_slot_denominator"]["strata"] for slot_id in stratum["slot_ids"]]
    assert len(all_ids) == 100 and len(set(all_ids)) == 100


def test_factory_receipt_counts_match_the_binding_contracts_zero_assigned_hundred_residual() -> None:
    assert REAL_FACTORY_RECEIPT["per_slot_gate"]["slots_ready"] == 0
    assert REAL_FACTORY_RECEIPT["per_slot_gate"]["slots_residual"] == 100
    assert REAL_FACTORY_RECEIPT["execution_counters"]["slots_ready"] == 0
    assert REAL_FACTORY_RECEIPT["execution_counters"]["slots_residual"] == 100


def test_factory_receipt_dataset_rows_emitted_and_private_rows_constructed_stay_zero() -> None:
    assert REAL_FACTORY_RECEIPT["execution_counters"]["dataset_rows_emitted"] == 0
    assert REAL_FACTORY_RECEIPT["execution_counters"]["private_rows_constructed"] == 0


def test_factory_receipt_reason_code_totals_sum_to_the_full_denominator() -> None:
    totals = REAL_FACTORY_RECEIPT["reason_code_totals"]
    assert sum(totals.values()) == 100
    assert set(totals) == {"rights_unknown", "source_incomplete", "independence_unavailable"}


def test_factory_receipt_never_claims_a_stronger_release_state() -> None:
    serialized = json.dumps(REAL_FACTORY_RECEIPT, ensure_ascii=False, sort_keys=True)
    for claim in ("TRAINING_READY_SILVER", "ARENA_SLICE_READY", "TRAINING_READY_GOLD_SUBSET", "GOLD_UPGRADE_READY", "EPIC_DONE"):
        assert claim not in serialized


def test_factory_receipt_has_no_slot_keyed_hmac_or_source_unit_table() -> None:
    """No per-slot table of any kind -- counts and reason-code totals only.
    Neither ``frozen_slot_denominator.strata`` (per-stratum, not per-slot,
    and carries no HMAC) nor any other field may carry a slot->HMAC or
    slot->source-unit binding."""
    serialized = json.dumps(REAL_FACTORY_RECEIPT, ensure_ascii=False, sort_keys=True)
    for needle in FORBIDDEN_PUBLIC_TERMS:
        assert needle not in serialized, f"forbidden public term leaked into the receipt: {needle}"
    keys = _all_keys(REAL_FACTORY_RECEIPT)
    assert not keys & factory.FORBIDDEN_PUBLIC_HMAC_KEYS
    assert not keys & factory.FORBIDDEN_KEYS


def test_factory_receipt_never_references_a4_private_ledger_or_a3_heldout_membership() -> None:
    assert REAL_FACTORY_RECEIPT["safety_assertions"]["a4_private_ledger_opened"] is False
    assert REAL_FACTORY_RECEIPT["safety_assertions"]["held_out_membership_referenced"] is False
    assert REAL_FACTORY_RECEIPT["safety_assertions"]["slot_to_source_unit_table_published"] is False
    assert REAL_FACTORY_RECEIPT["safety_assertions"]["slot_to_commitment_table_published"] is False


def test_factory_receipt_bindings_hash_to_disk() -> None:
    for name, binding in REAL_FACTORY_RECEIPT["bindings"].items():
        path = ROOT / binding["path"]
        assert path.is_file(), name
        assert factory.sha256_file(path) == binding["sha256"], name


# --- the new private factory module: private ledger (batch_state only) ------


def test_private_ledger_is_a_pure_function_of_public_artifacts_only() -> None:
    ledger = factory.build_private_ledger()
    assert ledger["candidate_rows"] == []
    assert len(ledger["slot_readiness"]) == 100
    # Identical to A7's own already-public per-slot readiness signal --
    # nothing here is secret; it lives under batch_state/ only because that
    # is this repo's private operational-state home.
    assert ledger["slot_readiness"] == a7.per_slot_readiness(REAL_MANIFEST, REAL_A2_RECEIPT)


def test_private_ledger_never_carries_a_slot_to_source_unit_or_commitment_binding() -> None:
    serialized = json.dumps(factory.build_private_ledger(), ensure_ascii=False, sort_keys=True)
    for needle in FORBIDDEN_PUBLIC_TERMS:
        assert needle not in serialized


def test_private_ledger_write_uses_0700_directory_and_0600_file_permissions(tmp_path: Path) -> None:
    ledger_path = tmp_path / "open-model-data" / "v4_private_per_slot_factory_ledger_v1.json"
    factory.write_private_ledger(factory.build_private_ledger(), path=ledger_path)
    try:
        dir_mode = stat.S_IMODE(ledger_path.parent.stat().st_mode)
        file_mode = stat.S_IMODE(ledger_path.stat().st_mode)
        assert oct(dir_mode) == oct(0o700)
        assert oct(file_mode) == oct(0o600)
        assert json.loads(ledger_path.read_text(encoding="utf-8"))["candidate_rows"] == []
    finally:
        ledger_path.unlink(missing_ok=True)


def test_private_ledger_default_path_is_under_gitignored_batch_state() -> None:
    assert "batch_state/open-model-data" in str(factory.PRIVATE_LEDGER_PATH)
    assert factory.PRIVATE_LEDGER_PATH.is_relative_to(ROOT / "batch_state")


# --- fail-closed on tampering ------------------------------------------------


def test_factory_refuses_a_forged_slots_ready_claim() -> None:
    receipt = copy.deepcopy(REAL_FACTORY_RECEIPT)
    receipt["per_slot_gate"] = {**receipt["per_slot_gate"], "slots_ready": 100, "slots_residual": 0, "blocked_reason_code": None}
    with pytest.raises(factory.PrivateFactoryError):
        factory.validate_receipt_independently(receipt)


def test_factory_refuses_a_nonzero_private_rows_constructed_claim() -> None:
    receipt = copy.deepcopy(REAL_FACTORY_RECEIPT)
    receipt["execution_counters"]["private_rows_constructed"] = 1
    with pytest.raises(factory.PrivateFactoryError):
        factory.validate_receipt_independently(receipt)


def test_factory_refuses_a_nonzero_dataset_rows_emitted_claim() -> None:
    receipt = copy.deepcopy(REAL_FACTORY_RECEIPT)
    receipt["execution_counters"]["dataset_rows_emitted"] = 1
    with pytest.raises(factory.PrivateFactoryError):
        factory.validate_receipt_independently(receipt)


def test_factory_refuses_an_injected_slot_to_commitment_field() -> None:
    receipt = copy.deepcopy(REAL_FACTORY_RECEIPT)
    receipt["per_slot_gate"] = dict(receipt["per_slot_gate"])
    receipt["per_slot_gate"]["commitment_sha256"] = "a" * 64
    with pytest.raises(factory.PrivateFactoryError):
        factory.validate_receipt_independently(receipt)


def test_factory_refuses_a_tampered_binding_hash() -> None:
    receipt = copy.deepcopy(REAL_FACTORY_RECEIPT)
    receipt["bindings"]["a7_original_row_factory"]["sha256"] = "0" * 64
    with pytest.raises(factory.PrivateFactoryError):
        factory.validate_receipt_independently(receipt)
