"""V4 per-slot prerequisite eligibility / positive completion / residual
model (PR #7654 repair cycle 2, Option A -- ``batch_state/tasks/design-7654-
partial-stage-evidence.result``): proves per-slot prerequisite eligibility is
not stage completion for A6-A9 and the private per-slot factory companion,
and that neither can be faked -- every positive result here comes from a
real, live builder/validator, never a stubbed one.

Everything here except the private-ledger permission checks and the
synthetic-chain fixture runs against public artifacts only -- no
``batch_state/`` required for the gate/receipt functions themselves, so the
bulk of this suite passes in a fresh checkout.
"""

from __future__ import annotations

import ast
import copy
import json
import stat
from pathlib import Path

import _v4_synthetic_chain_fixture as fixture
import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import v4_a6_blind_arena as a6
from scripts.projects.open_model_data import v4_a7_original_row_factory as a7
from scripts.projects.open_model_data import v4_a8_admission_assembly as a8
from scripts.projects.open_model_data import v4_a9_evaluation_package as a9
from scripts.projects.open_model_data import v4_per_slot_private_factory as factory
from scripts.projects.open_model_data import v4_stage_evidence as ev

ROOT = Path(__file__).resolve().parents[3]
ADMISSION = ROOT / "data/projects/open_model_data/admission"
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
MANIFEST_PATH = ADMISSION / "dataset_v4_pilot_slot_manifest_v1.json"
A2_RECEIPT_PATH = ADMISSION / "dataset_v4_a2_source_operation_admission_receipt_v1.json"
A6_RECEIPT_PATH = ADMISSION / "dataset_v4_a6_blind_arena_receipt_v1.json"
A7_RECEIPT_PATH = ADMISSION / "dataset_v4_a7_original_row_factory_receipt_v1.json"
A8_RECEIPT_PATH = ADMISSION / "dataset_v4_a8_admission_assembly_receipt_v1.json"
A9_RECEIPT_PATH = ADMISSION / "dataset_v4_a9_evaluation_package_receipt_v1.json"
FACTORY_RECEIPT_PATH = ADMISSION / "dataset_v4_per_slot_private_factory_receipt_v1.json"
FACTORY_SCHEMA_PATH = CONTRACTS / "dataset_v4_per_slot_private_factory_receipt_v1.schema.json"

REAL_MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
REAL_A2_RECEIPT = json.loads(A2_RECEIPT_PATH.read_text(encoding="utf-8"))
REAL_A6_RECEIPT = json.loads(A6_RECEIPT_PATH.read_text(encoding="utf-8"))
REAL_A7_RECEIPT = json.loads(A7_RECEIPT_PATH.read_text(encoding="utf-8"))
REAL_A8_RECEIPT = json.loads(A8_RECEIPT_PATH.read_text(encoding="utf-8"))
REAL_A9_RECEIPT = json.loads(A9_RECEIPT_PATH.read_text(encoding="utf-8"))
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


# --- prerequisite eligibility is a real, per-stratum, live-validated fact ---


def test_stratum_eligibility_covers_every_manifest_stratum_exactly_once() -> None:
    eligibility = ev.stratum_eligibility(REAL_MANIFEST, REAL_A2_RECEIPT)
    assert len(eligibility) == 8
    assert {record["stratum"] for record in eligibility} == {s["stratum"] for s in REAL_MANIFEST["slot_series"]}


def test_stratum_eligibility_against_real_production_data_is_zero_eligible() -> None:
    # Matches the binding contract's own "0 assigned / 100 residual" count.
    eligibility = ev.stratum_eligibility(REAL_MANIFEST, REAL_A2_RECEIPT)
    assert all(not record["prerequisite_eligible"] for record in eligibility)
    assert ev.eligible_slot_ids(eligibility) == set()


def test_stratum_eligibility_resolving_one_stratum_never_needs_every_other_stratum_resolved() -> None:
    """The per-stratum-independence property: resolving one stratum's A2
    residual and manifest assignment must never depend on any other
    stratum's state."""
    resolved_a2 = fixture.resolved_a2_receipt("standard_correct")
    assigned_manifest = fixture.assigned_manifest("standard_correct")
    eligibility = ev.stratum_eligibility(assigned_manifest, resolved_a2)
    eligible = {record["stratum"] for record in eligibility if record["prerequisite_eligible"]}
    assert eligible == {"standard_correct"}
    assert len(ev.eligible_slot_ids(eligibility)) == 15


def test_stratum_eligibility_refuses_a_coverage_entry_referencing_an_absent_residual() -> None:
    """The first hole the cycle-1 stubbed tests exploited: a coverage entry
    referencing a residual id absent from A2's own residuals list must
    refuse, never silently drop the reference."""
    tampered = copy.deepcopy(REAL_A2_RECEIPT)
    tampered["stratum_coverage_map"][0]["residual_ids"] = ["a2-residual-does-not-exist"]
    with pytest.raises(ValueError, match="absent from A2's own residuals"):
        ev.stratum_eligibility(REAL_MANIFEST, tampered)


def test_stratum_eligibility_refuses_an_empty_residual_list_without_a_resolved_coverage_state() -> None:
    """The second hole: a coverage entry cannot legitimately clear its
    residual_ids without a matching ``coverage_state: "resolved"``
    transition -- deleting a residual without that transition refuses."""
    tampered = copy.deepcopy(REAL_A2_RECEIPT)
    tampered["stratum_coverage_map"][0]["residual_ids"] = []
    # coverage_state left at its real, non-resolved value.
    with pytest.raises(ValueError, match="coverage_state"):
        ev.stratum_eligibility(REAL_MANIFEST, tampered)


# --- the synthetic partial-prerequisite chain: every validator live --------


def test_synthetic_chain_reports_fifteen_eligible_zero_complete_hundred_residual_at_a6_through_a9(tmp_path: Path) -> None:
    """The acceptance proof for this repair: a fully valid synthetic chain
    where exactly one manifest stratum (15 slots) is genuinely prerequisite-
    eligible, built and verified with every A6-A9 validator running live --
    no monkeypatch, no stub, no deleted residual standing in for real
    upstream evidence. Every stage reports 15 eligible, 0 complete, 100
    residual, proving eligibility and completion are visibly distinct
    everywhere this repair touches."""
    fixture.build_synthetic_chain_root(tmp_path, resolved_stratum="standard_correct")
    receipts = fixture.run_chain_a6_through_a9(tmp_path)

    for stage, gate_key, ready_key in (
        ("a6", "arena_gate", "arena_slice_ready"),
        ("a7", "factory_gate", "factory_slice_ready"),
        ("a8", "assembly_gate", "assembly_slice_ready"),
        ("a9", "evaluation_gate", "evaluation_slice_ready"),
    ):
        gate = receipts[stage][gate_key]
        assert gate["slots_prerequisite_eligible"] == 15, stage
        assert gate["slots_stage_complete"] == 0, stage
        assert gate["slots_residual"] == 100, stage
        assert gate[ready_key] is False, stage


# --- tamper tests: overlap, gap, ineligible completion, upstream-missing ---


def test_partition_refuses_a_slot_in_both_completion_and_residual_lists() -> None:
    """Overlap: a slot claimed complete must never also carry a residual --
    completion and residual must exactly partition the frozen denominator.
    Exercises the shared validator ``v4_stage_evidence`` module directly --
    the same function every A6-A9 gate calls -- since a stage's own gate
    always independently recomputes today's real completion count as 0 (no
    execution mechanism exists yet), which would otherwise mask which
    specific check refused a hand-tampered receipt."""
    total = set(a6.all_frozen_slot_ids(REAL_MANIFEST))
    completion = {"v4p-standard-correct-001"}
    residual = total - completion  # correct complement...
    residual.add("v4p-standard-correct-001")  # ...deliberately re-added: now overlaps completion.
    with pytest.raises(ValueError, match="overlap"):
        ev.validate_partition(total, completion, residual, label="test")


def test_partition_refuses_a_slot_dropped_from_both_completion_and_residual_lists() -> None:
    """Gap: a slot that is neither complete nor residual must refuse --
    never a silently forgotten slot."""
    total = set(a6.all_frozen_slot_ids(REAL_MANIFEST))
    completion = {"v4p-standard-correct-001"}
    residual = total - completion - {"v4p-standard-correct-002"}  # a second slot silently dropped from both.
    with pytest.raises(ValueError, match="partition"):
        ev.validate_partition(total, completion, residual, label="test")


def test_subset_refuses_a_completion_for_a_prerequisite_ineligible_slot() -> None:
    """A completion claim for a slot whose stratum is not prerequisite-
    eligible must refuse -- completion can never precede eligibility."""
    eligible = {"v4p-standard-correct-001"}
    completion = {"v4p-literary-001"}  # not in the eligible set.
    with pytest.raises(ValueError, match="subset"):
        ev.validate_subset(completion, eligible, label="test")


def test_subset_refuses_a_completion_with_no_matching_upstream_completion() -> None:
    """Upstream-missing: a downstream stage that does declare an upstream-
    completion dependency (A8 on A7, A9 on A8) cannot claim a slot complete
    unless the immediately upstream stage's own positive completion
    evidence also names it -- eligibility, and even a real downstream-level
    construction, can never stand in for the missing upstream proof. (A7
    itself declares no such dependency on A6 -- an explicitly deferred
    policy decision, design packet F2 -- so this exercises the shared
    ``ev.validate_subset`` primitive directly, the same one A8/A9's gates
    call against their own immediate upstream.)"""
    upstream_completion: set[str] = set()  # A7's own a7_completions, empty today.
    completion = {"v4p-standard-correct-001"}  # A8 claims this slot complete anyway.
    with pytest.raises(ValueError, match="subset"):
        ev.validate_subset(completion, upstream_completion, label="test")


def test_a2_deleting_a_residual_without_a_resolved_coverage_state_refuses() -> None:
    """Tampered-A2-state: the coverage-state transition is the only
    legitimate way a residual clears -- a receipt hand-edited to drop a
    residual without it must be refused by every stage's own eligibility
    derivation, not just by a schema shape check."""
    tampered_a2 = copy.deepcopy(REAL_A2_RECEIPT)
    tampered_a2["residuals"] = [r for r in tampered_a2["residuals"] if r["subject_id"] != "standard_correct"]
    for coverage in tampered_a2["stratum_coverage_map"]:
        if coverage["stratum"] == "standard_correct":
            coverage["residual_ids"] = []
            # coverage_state deliberately left at its real, unresolved value.
    for module, error_cls in ((a6, a6.ArenaWiringError), (a7, a7.OriginalRowFactoryError), (a8, a8.AdmissionAssemblyError), (a9, a9.EvaluationPackageError)):
        with pytest.raises(error_cls, match="coverage_state"):
            module.ev.stratum_eligibility(REAL_MANIFEST, tampered_a2, error_cls=error_cls)


# --- suite-level guard: no stubbed validator behind a nonzero-completion claim ---

_STUB_PATTERN = "monkeypatch.setattr"
_NONZERO_COMPLETION_PATTERNS = (
    'slots_stage_complete"] > 0',
    'factory_slice_ready"] is True',
    'arena_slice_ready"] is True',
    'assembly_slice_ready"] is True',
    'evaluation_slice_ready"] is True',
)


def test_no_test_in_this_suite_asserts_nonzero_completion_behind_a_stubbed_validator() -> None:
    """A static source guard: any test function that stubs a validator
    (``monkeypatch.setattr(..., "validate_receipt_independently", ...)``)
    must never also assert a stage reports positive completion. This is
    exactly the cycle-1 anti-pattern the exact-head review flagged as a P1
    -- this guard keeps it from coming back."""
    suite_dir = Path(__file__).resolve().parent
    offenders: list[str] = []
    for test_file in [*sorted(suite_dir.glob("test_a[6-9]_*.py")), Path(__file__)]:
        source = test_file.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(test_file))
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef) or not node.name.startswith("test_"):
                continue
            segment = ast.get_source_segment(source, node) or ""
            if _STUB_PATTERN in segment and any(pattern in segment for pattern in _NONZERO_COMPLETION_PATTERNS):
                offenders.append(f"{test_file.name}::{node.name}")
    assert not offenders, f"stubbed validator behind a nonzero-completion assertion: {offenders}"


# --- the private factory module: public receipt ------------------------------


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
    assert REAL_FACTORY_RECEIPT["per_slot_gate"]["slots_prerequisite_eligible"] == 0
    assert REAL_FACTORY_RECEIPT["per_slot_gate"]["slots_stage_complete"] == 0
    assert REAL_FACTORY_RECEIPT["per_slot_gate"]["slots_residual"] == 100
    assert REAL_FACTORY_RECEIPT["execution_counters"]["slots_prerequisite_eligible"] == 0
    assert REAL_FACTORY_RECEIPT["execution_counters"]["slots_stage_complete"] == 0
    assert REAL_FACTORY_RECEIPT["execution_counters"]["slots_residual"] == 100


def test_factory_receipt_dataset_rows_emitted_and_private_rows_constructed_stay_zero() -> None:
    assert REAL_FACTORY_RECEIPT["execution_counters"]["dataset_rows_emitted"] == 0
    assert REAL_FACTORY_RECEIPT["execution_counters"]["private_rows_constructed"] == 0


def test_factory_receipt_reason_code_totals_sum_to_the_full_denominator() -> None:
    totals = REAL_FACTORY_RECEIPT["reason_code_totals"]
    assert sum(totals.values()) == 100
    assert set(totals) == set(ev.RESIDUAL_REASON_CODES)


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


# --- the private factory module: private ledger (batch_state only) ----------


def test_private_ledger_is_a_pure_function_of_public_artifacts_only() -> None:
    ledger = factory.build_private_ledger()
    assert ledger["candidate_rows"] == []
    assert len(ledger["stratum_eligibility"]) == 8
    # Identical to this module's own already-public per-stratum eligibility
    # signal -- nothing here is secret; it lives under batch_state/ only
    # because that is this repo's private operational-state home.
    assert ledger["stratum_eligibility"] == REAL_FACTORY_RECEIPT["prerequisite_eligibility"]


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


# --- fail-closed on tampering (private factory) ------------------------------


def test_factory_refuses_a_forged_slots_ready_claim() -> None:
    receipt = copy.deepcopy(REAL_FACTORY_RECEIPT)
    receipt["per_slot_gate"] = {**receipt["per_slot_gate"], "slots_stage_complete": 100, "slots_residual": 0, "blocked_reason_code": None}
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
