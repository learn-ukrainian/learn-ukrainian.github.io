"""V4 real-slot mechanism (PR-A, mechanism-only, zero real rows): the
acceptance proof that a genuine, independently-authored, evidence-bound,
non-reconstructive row can traverse A7 and A8 -- built entirely from
synthetic fixtures, never real corpus or held-out membership -- plus the
tamper-refusal coverage the frozen packet requires.

Every completion here is constructed live through
``v4_a7_private_ledger.construct_completion`` (real gates, real admission
engine call, real receipt schemas) -- never a hand-authored shape standing
in for the mechanism.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import _v4_a7_real_slot_fixture as fx
import pytest

from scripts.projects.open_model_data import v4_a3_builder_packet as packet
from scripts.projects.open_model_data import v4_a3_candidate_family_floor as floor
from scripts.projects.open_model_data import v4_a3_heldout_family_assignment as heldout
from scripts.projects.open_model_data import v4_a3_reissue as reissue
from scripts.projects.open_model_data import v4_a3_split_duplicate_check as split_check
from scripts.projects.open_model_data import v4_a7_evidence_binder as evidence_binder
from scripts.projects.open_model_data import v4_a7_original_row_factory as a7
from scripts.projects.open_model_data import v4_a7_private_ledger as ledger
from scripts.projects.open_model_data import v4_a8_admission_assembly as a8
from scripts.projects.open_model_data import v4_original_row_admission as admission
from scripts.projects.open_model_data import v4_stage_evidence as ev

ROOT = Path(__file__).resolve().parents[3]
FORBIDDEN_PUBLIC_TERMS = ("fam-", "db.", "historical.", "heldout_membership", "source_unit_id")


def _all_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(_all_keys(item) for item in value.values()), set())
    if isinstance(value, list):
        return set().union(*(_all_keys(item) for item in value), set())
    return set()


# --- acceptance proof: exactly 1/99 at A7 and A8, 0/100 at A9 --------------


def test_synthetic_chain_reaches_exactly_one_completion_at_a7_and_a8_and_stays_zero_at_a9(tmp_path: Path) -> None:
    tmp_root, info = fx.build_real_slot_root(tmp_path)

    a7_gate = info["a7_receipt"]["factory_gate"]
    assert a7_gate["slots_prerequisite_eligible"] == 15
    assert a7_gate["slots_stage_complete"] == 1
    assert a7_gate["slots_residual"] == 99
    assert len(info["a7_receipt"]["a7_completions"]) == 1
    assert len(info["a7_receipt"]["a7_residuals"]) == 99

    a8_gate = info["a8_receipt"]["assembly_gate"]
    assert a8_gate["slots_prerequisite_eligible"] == 15
    assert a8_gate["slots_stage_complete"] == 1
    assert a8_gate["slots_residual"] == 99
    assert len(info["a8_receipt"]["a8_completions"]) == 1
    assert len(info["a8_receipt"]["a8_residuals"]) == 99
    admitted = [entry for entry in info["a8_receipt"]["admitted_slice_view"] if entry["row_admitted"]]
    assert len(admitted) == 1
    assert admitted[0]["slot_id"] == fx.TARGET_SLOT_ID

    a9_gate = info["a9_receipt"]["evaluation_gate"]
    assert a9_gate["slots_stage_complete"] == 0
    assert a9_gate["slots_residual"] == 100
    assert info["a9_receipt"]["a9_completions"] == []

    # Every validator ran live -- reproduce all three independently again.
    a7.validate_receipt_independently(info["a7_receipt"], tmp_root)
    a8.validate_receipt_independently(info["a8_receipt"], tmp_root)


def test_private_replay_succeeds_against_the_synthetic_private_ledger(tmp_path: Path) -> None:
    tmp_root, info = fx.build_real_slot_root(tmp_path)
    stored_ledger = ledger.load_ledger(info["ledger_path"])
    ledger.verify_private_replay(info["a7_receipt"], stored_ledger, a4_unit_commitments=fx.a4_unit_commitments(tmp_root))


def test_fresh_checkout_public_validation_needs_no_batch_state(tmp_path: Path) -> None:
    """Public validation of the A7/A8 receipts must succeed even after the
    private ledger is deleted entirely -- proving the well-formedness proof
    is separate from (and does not require) the private replay."""
    import shutil

    tmp_root, info = fx.build_real_slot_root(tmp_path)
    batch_state_dir = tmp_path / "batch_state"
    assert batch_state_dir.is_dir()  # the private ledger really was written under tmp_path/batch_state
    shutil.rmtree(batch_state_dir)

    a7.validate_receipt_independently(json.loads(json.dumps(info["a7_receipt"])), tmp_root)
    a8.validate_receipt_independently(json.loads(json.dumps(info["a8_receipt"])), tmp_root)


def test_no_forbidden_public_terms_leak_into_a7_or_a8_receipts(tmp_path: Path) -> None:
    _, info = fx.build_real_slot_root(tmp_path)
    for receipt in (info["a7_receipt"], info["a8_receipt"]):
        serialized = json.dumps(receipt, ensure_ascii=False, sort_keys=True)
        for needle in FORBIDDEN_PUBLIC_TERMS:
            assert needle not in serialized, f"forbidden term leaked: {needle}"
        keys = _all_keys(receipt)
        assert not keys & a7.FORBIDDEN_KEYS
        # No slot-to-unit or slot-to-commitment table: the private ledger's
        # own bound_unit_id/lineage_source_id never appear publicly.
        assert fx.CANDIDATE_UNIT_IDS[0] not in serialized
        assert fx.CANDIDATE_UNIT_IDS[1] not in serialized


def test_a7_never_reads_or_depends_on_a6_completions() -> None:
    """Static guard: A7's own gate/build_receipt source never references
    a6_completions -- A7 completion must never depend on A6 completion
    membership or count (binding advisor decision, A7_VS_A6)."""
    source = (ROOT / "scripts/projects/open_model_data/v4_a7_original_row_factory.py").read_text(encoding="utf-8")
    assert 'a6_receipt.get("a6_completions"' not in source
    assert 'a6_receipt["a6_completions"]' not in source


# --- tamper: same-family / same-session author-reviewer --------------------


def test_review_receipt_refuses_same_model_family_as_author() -> None:
    authorship = ledger.build_authorship_receipt(row_content_sha256="a" * 64, **fx.AUTHOR)
    reviewer = dict(fx.REVIEWER)
    reviewer["model_family"] = fx.AUTHOR["model_family"]
    with pytest.raises(ledger.PrivateLedgerError, match="model family"):
        ledger.build_review_receipt(authorship_receipt=authorship, row_content_sha256="a" * 64, **reviewer)


def test_review_receipt_refuses_same_session_as_author() -> None:
    authorship = ledger.build_authorship_receipt(row_content_sha256="a" * 64, **fx.AUTHOR)
    reviewer = dict(fx.REVIEWER)
    reviewer["session_id"] = fx.AUTHOR["session_id"]
    with pytest.raises(ledger.PrivateLedgerError, match="session"):
        ledger.build_review_receipt(authorship_receipt=authorship, row_content_sha256="a" * 64, **reviewer)


# --- tamper: saw_source_text / saw_heldout / saw_eligible_unit_ids ---------


def test_authorship_receipt_refuses_saw_source_text_true() -> None:
    with pytest.raises(ledger.PrivateLedgerError, match="saw_source_text"):
        ledger.build_authorship_receipt(row_content_sha256="a" * 64, saw_source_text=True, **fx.AUTHOR)


def test_authorship_receipt_refuses_saw_heldout_true() -> None:
    with pytest.raises(ledger.PrivateLedgerError, match="saw_heldout"):
        ledger.build_authorship_receipt(row_content_sha256="a" * 64, saw_heldout=True, **fx.AUTHOR)


def test_authorship_receipt_refuses_saw_eligible_unit_ids_true() -> None:
    with pytest.raises(ledger.PrivateLedgerError, match="saw_eligible_unit_ids"):
        ledger.build_authorship_receipt(row_content_sha256="a" * 64, saw_eligible_unit_ids=True, **fx.AUTHOR)


def test_review_receipt_refuses_saw_source_text_true() -> None:
    authorship = ledger.build_authorship_receipt(row_content_sha256="a" * 64, **fx.AUTHOR)
    with pytest.raises(ledger.PrivateLedgerError, match="saw_source_text"):
        ledger.build_review_receipt(authorship_receipt=authorship, row_content_sha256="a" * 64, saw_source_text=True, **fx.REVIEWER)


# --- tamper: public lineage equal to an A4 commitment -----------------------


def test_lineage_id_colliding_with_an_a4_commitment_refuses() -> None:
    with pytest.raises(ledger.PrivateLedgerError, match="unit_commitments"):
        ledger.validate_lineage_not_equal_to_a4_commitment(["some-a4-commitment-hex"], ["some-a4-commitment-hex"])


def test_real_construction_refuses_when_lineage_collides_with_a4_commitment(tmp_path: Path) -> None:
    tmp_root = fx.base_fixture.build_synthetic_chain_root(tmp_path, resolved_stratum="standard_correct")
    real_commitments = fx.a4_unit_commitments(tmp_root)
    # Force a collision by asserting against the private lineage id this
    # construction would actually produce.
    salt = fx.TEST_SALT
    bound_unit = ledger.pick_bound_unit(salt, fx.TARGET_SLOT_ID, fx.CANDIDATE_UNIT_IDS)
    real_lineage_id = ledger.per_row_lineage_id(salt, fx.TARGET_SLOT_ID, bound_unit)
    with pytest.raises(ledger.PrivateLedgerError, match="unit_commitments"):
        ledger.construct_completion(
            slot_id=fx.TARGET_SLOT_ID,
            salt=salt,
            candidate_unit_ids=fx.CANDIDATE_UNIT_IDS,
            a4_unit_commitments=[*real_commitments, real_lineage_id],
            row_text=fx.ROW_TEXT,
            tier="silver",
            author=dict(fx.AUTHOR),
            reviewer=dict(fx.REVIEWER),
            vesum_ids=list(fx.VESUM_IDS),
            reference_texts=dict(fx.REFERENCE_TEXTS),
            rights_receipt_id=fx.RIGHTS_RECEIPT_ID,
        )


# --- tamper: forged public completion without private replay ---------------


def test_verify_private_replay_refuses_a_completion_with_no_matching_ledger_entry(tmp_path: Path) -> None:
    tmp_root, info = fx.build_real_slot_root(tmp_path)
    forged_receipt = copy.deepcopy(info["a7_receipt"])
    forged_completion = copy.deepcopy(forged_receipt["a7_completions"][0])
    forged_completion["slot_id"] = "v4p-standard-correct-002"
    forged_completion["row_receipt"]["row_id"] = "v4a7-row-v4p-standard-correct-002"
    forged_receipt["a7_completions"] = [forged_completion]
    stored_ledger = ledger.load_ledger(info["ledger_path"])
    with pytest.raises(ledger.PrivateLedgerError, match="forged public completion"):
        ledger.verify_private_replay(forged_receipt, stored_ledger, a4_unit_commitments=fx.a4_unit_commitments(tmp_root))


def test_verify_private_replay_refuses_a_hash_mismatch_against_the_ledger(tmp_path: Path) -> None:
    tmp_root, info = fx.build_real_slot_root(tmp_path)
    forged_receipt = copy.deepcopy(info["a7_receipt"])
    forged_receipt["a7_completions"][0]["row_content_sha256"] = "0" * 64
    stored_ledger = ledger.load_ledger(info["ledger_path"])
    with pytest.raises(ledger.PrivateLedgerError):
        ledger.verify_private_replay(forged_receipt, stored_ledger, a4_unit_commitments=fx.a4_unit_commitments(tmp_root))


# --- tamper: candidate-family floor violation (Invariant D1) ---------------


def _family_registry(*, single_family: bool) -> dict:
    if single_family:
        families = [
            {"family_id": "fam-a", "member_source_unit_ids": ["unit-1", "unit-2"]},
            {"family_id": "fam-b", "member_source_unit_ids": ["unit-3"]},
        ]
        supporting = ["unit-1", "unit-2"]  # both from fam-a: 1 distinct family.
    else:
        families = [
            {"family_id": "fam-a", "member_source_unit_ids": ["unit-1"]},
            {"family_id": "fam-b", "member_source_unit_ids": ["unit-2"]},
            {"family_id": "fam-c", "member_source_unit_ids": ["unit-3"]},
        ]
        supporting = ["unit-1", "unit-2"]  # 2 distinct families.
    return {"families": families}, supporting


def test_candidate_family_floor_violation_refuses() -> None:
    registry, supporting = _family_registry(single_family=True)
    coverage_entry = {"stratum": "standard_correct", "supporting_existing_source_unit_ids": supporting}
    with pytest.raises(floor.CandidateFamilyFloorError, match="floor not met"):
        floor.validate_candidate_family_floor("standard_correct", coverage_entry, registry, heldout_count=1)


def test_candidate_family_floor_met_passes() -> None:
    registry, supporting = _family_registry(single_family=False)
    coverage_entry = {"stratum": "standard_correct", "supporting_existing_source_unit_ids": supporting}
    floor.validate_candidate_family_floor("standard_correct", coverage_entry, registry, heldout_count=1)  # no raise


def test_candidate_family_floor_refuses_an_unregistered_supporting_unit() -> None:
    registry, _ = _family_registry(single_family=False)
    coverage_entry = {"stratum": "standard_correct", "supporting_existing_source_unit_ids": ["unit-not-registered"]}
    with pytest.raises(floor.CandidateFamilyFloorError, match="not a member of any registered family"):
        floor.validate_candidate_family_floor("standard_correct", coverage_entry, registry, heldout_count=1)


# --- tamper: reissue with changed membership/eligible commitment ----------


def _generate_sealed_receipt(tmp_path: Path, salt_hex: str) -> tuple[dict, Path]:
    """Build a minimal, schema-conformant, freshly-sealed A3 receipt over a
    small synthetic family registry, using a test-only salt -- never the
    real production salt or membership file."""
    real_receipt = json.loads((ROOT / heldout.DEFAULT_RECEIPT.relative_to(ROOT)).read_text(encoding="utf-8"))
    receipt = copy.deepcopy(real_receipt)
    private_dir = tmp_path / "v4-a3-heldout"
    import os

    os.environ["V4_A3_HELDOUT_TEST_SALT_HEX_ONLY"] = salt_hex
    try:
        family_ids = sorted(f["family_id"] for f in receipt["source_family_registry"]["families"])
        salt = bytes.fromhex(salt_hex)
        result = heldout.assign(salt, family_ids)
        summary = heldout.public_commitment_summary(salt, result)
        receipt["heldout_partition_seal"]["assignment_algorithm"]["salt_commitment_sha256"] = summary["salt_commitment_sha256"]
        receipt["heldout_partition_seal"]["assignment_algorithm"]["assignment_commitment_sha256"] = summary["assignment_commitment_sha256"]
        heldout.write_private_artifact(private_dir / heldout.MEMBERSHIP_FILENAME, salt, result, heldout.receipt_binding_sha256(receipt))
    finally:
        del os.environ["V4_A3_HELDOUT_TEST_SALT_HEX_ONLY"]
    return receipt, private_dir / heldout.MEMBERSHIP_FILENAME


def test_reissue_refuses_a_changed_assignment_commitment(tmp_path: Path) -> None:
    old_receipt, membership_path = _generate_sealed_receipt(tmp_path, "11" * 32)
    new_receipt = copy.deepcopy(old_receipt)
    new_receipt["heldout_partition_seal"]["assignment_algorithm"]["assignment_commitment_sha256"] = "0" * 64
    with pytest.raises(reissue.ReissueError, match="reseal, not a reissue"):
        reissue.reissue_private_artifact(membership_path, old_receipt, new_receipt, sorted(f["family_id"] for f in old_receipt["source_family_registry"]["families"]))


def test_reissue_refuses_a_changed_family_registry(tmp_path: Path) -> None:
    old_receipt, membership_path = _generate_sealed_receipt(tmp_path, "22" * 32)
    new_receipt = copy.deepcopy(old_receipt)
    new_receipt["source_family_registry"]["families"][0]["member_source_unit_ids"].append("a-new-unit")
    with pytest.raises(reissue.ReissueError, match="reseal, not a reissue"):
        reissue.reissue_private_artifact(membership_path, old_receipt, new_receipt, sorted(f["family_id"] for f in old_receipt["source_family_registry"]["families"]))


def test_reissue_succeeds_and_rebinds_when_membership_is_provably_unchanged(tmp_path: Path) -> None:
    """A trivial (identical-content) reissue still exercises the full
    equality-check-then-rebind path live -- the mechanism under test is
    that the three core commitments and the registry are proven unchanged
    before any rewrite happens, not that the receipt content itself
    differs."""
    old_receipt, membership_path = _generate_sealed_receipt(tmp_path, "33" * 32)
    new_receipt = copy.deepcopy(old_receipt)
    family_ids = sorted(f["family_id"] for f in old_receipt["source_family_registry"]["families"])
    summary = reissue.reissue_private_artifact(membership_path, old_receipt, new_receipt, family_ids)
    assert summary["assignment_commitment_sha256"] == old_receipt["heldout_partition_seal"]["assignment_algorithm"]["assignment_commitment_sha256"]
    # The artifact still reproduces against both (identical) receipts.
    reissue.heldout.verify_against_receipt(membership_path, new_receipt, family_ids)
    reissue.heldout.verify_against_receipt(membership_path, old_receipt, family_ids)


def test_builder_packet_reissue_succeeds_and_refuses_a_wrong_expected_commitment(tmp_path: Path) -> None:
    old_receipt, membership_path = _generate_sealed_receipt(tmp_path, "44" * 32)
    private_dir = membership_path.parent
    old_receipt_path = tmp_path / "old_seal_receipt.json"
    old_receipt_path.write_text(json.dumps(old_receipt), encoding="utf-8")

    packet.issue_packet(old_receipt_path, private_dir, private_dir)
    summary = packet.verify_packet(old_receipt_path, private_dir, private_dir)

    new_receipt = copy.deepcopy(old_receipt)
    family_ids = sorted(f["family_id"] for f in old_receipt["source_family_registry"]["families"])
    reissue.reissue_private_artifact(membership_path, old_receipt, new_receipt, family_ids)
    new_receipt_path = tmp_path / "new_seal_receipt.json"
    new_receipt_path.write_text(json.dumps(new_receipt), encoding="utf-8")

    # A wrong operator-asserted expectation refuses.
    with pytest.raises(packet.BuilderPacketError, match="expect-eligible-units-commitment"):
        packet.reissue_packet(old_receipt_path, new_receipt_path, private_dir, private_dir, expect_eligible_units_commitment="0" * 64)

    # The real reissue (no false expectation) succeeds and preserves the
    # eligible-units commitment exactly.
    reissued_summary = packet.reissue_packet(old_receipt_path, new_receipt_path, private_dir, private_dir)
    assert reissued_summary["eligible_units_commitment_sha256"] == summary["eligible_units_commitment_sha256"]


# --- tamper: gap/overlap in completion-residual partition -------------------


def test_a7_completion_residual_overlap_refuses() -> None:
    total = {"v4p-standard-correct-001", "v4p-standard-correct-002"}
    completion = {"v4p-standard-correct-001"}
    residual = {"v4p-standard-correct-001", "v4p-standard-correct-002"}  # overlaps completion
    with pytest.raises(ValueError, match="overlap"):
        ev.validate_partition(total, completion, residual, label="A7")


def test_a7_completion_residual_gap_refuses() -> None:
    total = {"v4p-standard-correct-001", "v4p-standard-correct-002", "v4p-standard-correct-003"}
    completion = {"v4p-standard-correct-001"}
    residual = {"v4p-standard-correct-002"}  # v4p-standard-correct-003 dropped from both
    with pytest.raises(ValueError, match="partition"):
        ev.validate_partition(total, completion, residual, label="A7")


def test_real_a7_receipt_refuses_an_overlapping_residual_for_its_own_completed_slot(tmp_path: Path) -> None:
    tmp_root, info = fx.build_real_slot_root(tmp_path)
    tampered = copy.deepcopy(info["a7_receipt"])
    extra_residual = copy.deepcopy(tampered["a7_residuals"][0])
    extra_residual["residual_id"] = "a7-residual-stage-completion-not-yet-available-v4p-standard-correct-001"
    extra_residual["subject_id"] = fx.TARGET_SLOT_ID
    tampered["a7_residuals"].append(extra_residual)  # now overlaps the real completion for this slot.
    with pytest.raises(a7.OriginalRowFactoryError, match="does not exactly cover"):
        a7.validate_receipt_independently(tampered, tmp_root)


def test_real_a7_receipt_refuses_a_dropped_residual_for_a_gap_slot(tmp_path: Path) -> None:
    tmp_root, info = fx.build_real_slot_root(tmp_path)
    tampered = copy.deepcopy(info["a7_receipt"])
    tampered["a7_residuals"] = [r for r in tampered["a7_residuals"] if r["subject_id"] != "v4p-standard-correct-002"]
    with pytest.raises(a7.OriginalRowFactoryError, match="a7_residuals does not exactly cover"):
        a7.validate_receipt_independently(tampered, tmp_root)


# --- split-duplicate check and reconstruction gates: basic behavior -------


def test_split_duplicate_check_fails_closed_on_empty_references() -> None:
    with pytest.raises(split_check.SplitDuplicateCheckError, match="nonempty"):
        split_check.check_split_duplicate_safety("some text", {})


def test_split_duplicate_check_passes_for_dissimilar_text() -> None:
    result = split_check.check_split_duplicate_safety(fx.ROW_TEXT, fx.REFERENCE_TEXTS)
    assert result["passed"] is True


def test_split_duplicate_check_fails_for_a_near_duplicate_reference() -> None:
    result = split_check.check_split_duplicate_safety(fx.ROW_TEXT, {"x": fx.ROW_TEXT})
    assert result["passed"] is False


def test_reconstruction_gates_fail_when_candidate_matches_a_reference_exactly() -> None:
    results = evidence_binder.run_reconstruction_gates(fx.ROW_TEXT, {"x": fx.ROW_TEXT})
    assert results["exact"]["passed"] is False
    assert results["reconstruction"]["passed"] is False


def test_reconstruction_gates_pass_for_dissimilar_text() -> None:
    results = evidence_binder.run_reconstruction_gates(fx.ROW_TEXT, fx.REFERENCE_TEXTS)
    assert all(gate["passed"] for gate in results.values())


def test_evidence_receipt_refuses_a_malformed_identifier() -> None:
    with pytest.raises(evidence_binder.EvidenceBinderError, match="VESUM/sources shape"):
        evidence_binder.build_evidence_receipt("a" * 64, ["not-a-valid-id"])


# --- the shared admission engine: the new helper is byte-identical at zero -


def test_assemble_receipt_from_row_receipts_matches_admit_rows_at_zero() -> None:
    assert admission.assemble_receipt_from_row_receipts(outcome_sha256=a7.V4_SHA256, row_receipts=[]) == admission.admit_rows(
        outcome_sha256=a7.V4_SHA256, rows=[]
    )
