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
from scripts.projects.open_model_data import v4_a3_reference_check as reference_check
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

EMPTY_MANIFEST: dict = {"slot_series": []}
EMPTY_A2_RECEIPT: dict = {"stratum_coverage_map": []}


def _all_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(_all_keys(item) for item in value.values()), set())
    if isinstance(value, list):
        return set().union(*(_all_keys(item) for item in value), set())
    return set()


def _replay_kwargs(tmp_root: Path, info: dict) -> dict:
    sealed = info["sealed"]
    return {
        "salt": fx.TEST_SALT,
        "a4_unit_commitments": fx.a4_unit_commitments(tmp_root),
        "seal_receipt_path": sealed["seal_receipt_path"],
        "membership_dir": sealed["membership_dir"],
        "packet_dir": sealed["packet_dir"],
    }


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
    ledger.verify_private_replay(info["a7_receipt"], stored_ledger, **_replay_kwargs(tmp_root, info))


def test_private_replay_succeeds_with_full_a3_role_reference_check_replay(tmp_path: Path) -> None:
    """The strongest replay: the caller also supplies the A3-role verifier,
    so the reference-check receipt's gate *results* (not just its own
    internal self-consistency) are independently reproduced from the real
    candidate text, the real reference-text set, and the real A3 salt."""
    tmp_root, info = fx.build_real_slot_root(tmp_path)
    stored_ledger = ledger.load_ledger(info["ledger_path"])

    def _verifier(candidate_text: str, receipt: dict) -> None:
        reference_check.verify_reference_check_receipt(receipt, candidate_text, fx.REFERENCE_TEXTS, fx.A3_FIXTURE_SALT)

    ledger.verify_private_replay(info["a7_receipt"], stored_ledger, reference_check_verifier=_verifier, **_replay_kwargs(tmp_root, info))


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


def test_a7_construction_api_never_accepts_reference_texts_or_source_material() -> None:
    """Static guard (PR #7662 repair 2, P1 "A7 directly receives the
    all-family reference texts"): neither the private ledger nor the
    evidence binder ever names ``reference_texts``, a held-out family id
    string, or an eligible-unit list constant -- that comparison is
    A3-owned (``v4_a3_reference_check.py``); A7 receives only its
    text-free receipt."""
    for relative in ("v4_a7_private_ledger.py", "v4_a7_evidence_binder.py"):
        source = (ROOT / "scripts/projects/open_model_data" / relative).read_text(encoding="utf-8")
        assert "reference_texts" not in source, f"{relative} must never accept/store reference_texts"


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
    sealed = fx.build_sealed_receipt_and_packet(tmp_path)
    real_commitments = fx.a4_unit_commitments(tmp_root)
    # Force a collision by asserting against the private lineage id this
    # construction would actually produce.
    salt = fx.TEST_SALT
    bound_unit = ledger.pick_bound_unit(salt, fx.TARGET_SLOT_ID, fx.CANDIDATE_UNIT_IDS)
    real_lineage_id = ledger.per_row_lineage_id(salt, fx.TARGET_SLOT_ID, bound_unit)
    row_content_sha256 = ledger.sha256_text(fx.ROW_TEXT)
    with pytest.raises(ledger.PrivateLedgerError, match="unit_commitments"):
        ledger.construct_completion(
            slot_id=fx.TARGET_SLOT_ID,
            salt=salt,
            candidate_unit_ids=fx.CANDIDATE_UNIT_IDS,
            a4_unit_commitments=[*real_commitments, real_lineage_id],
            seal_receipt_path=sealed["seal_receipt_path"],
            membership_dir=sealed["membership_dir"],
            packet_dir=sealed["packet_dir"],
            row_text=fx.ROW_TEXT,
            tier="silver",
            author=dict(fx.AUTHOR),
            reviewer=dict(fx.REVIEWER),
            evidence_receipt=evidence_binder.build_synthetic_fixture_evidence_receipt(row_content_sha256, list(fx.VESUM_IDS)),
            reference_check_receipt=fx.build_reference_check_receipt(),
            rights_receipt_id=fx.RIGHTS_RECEIPT_ID,
            allow_synthetic_fixture=True,
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
        ledger.verify_private_replay(forged_receipt, stored_ledger, **_replay_kwargs(tmp_root, info))


def test_verify_private_replay_refuses_a_hash_mismatch_against_the_ledger(tmp_path: Path) -> None:
    tmp_root, info = fx.build_real_slot_root(tmp_path)
    forged_receipt = copy.deepcopy(info["a7_receipt"])
    forged_receipt["a7_completions"][0]["row_content_sha256"] = "0" * 64
    stored_ledger = ledger.load_ledger(info["ledger_path"])
    with pytest.raises(ledger.PrivateLedgerError):
        ledger.verify_private_replay(forged_receipt, stored_ledger, **_replay_kwargs(tmp_root, info))


def test_verify_private_replay_refuses_a_tampered_authorship_receipt_field(tmp_path: Path) -> None:
    """Flip a stored authorship receipt field without recomputing its
    receipt_id -- the recomputed receipt_id must no longer match."""
    tmp_root, info = fx.build_real_slot_root(tmp_path)
    stored_ledger = ledger.load_ledger(info["ledger_path"])
    entry = stored_ledger["entries"][fx.TARGET_SLOT_ID]
    entry["authorship_receipt"] = {**entry["authorship_receipt"], "session_id": "tampered-session"}
    with pytest.raises(ledger.PrivateLedgerError, match="authorship receipt_id does not reproduce"):
        ledger.verify_private_replay(info["a7_receipt"], stored_ledger, **_replay_kwargs(tmp_root, info))


def test_verify_private_replay_refuses_a_tampered_evidence_receipt_grade(tmp_path: Path) -> None:
    """Flip a stored evidence receipt's production_capable flag without
    recomputing its receipt_id -- the integrity recheck must catch it."""
    tmp_root, info = fx.build_real_slot_root(tmp_path)
    stored_ledger = ledger.load_ledger(info["ledger_path"])
    entry = stored_ledger["entries"][fx.TARGET_SLOT_ID]
    entry["evidence_receipt"] = {**entry["evidence_receipt"], "production_capable": True}
    with pytest.raises(ledger.PrivateLedgerError, match="evidence receipt failed replay integrity recheck"):
        ledger.verify_private_replay(info["a7_receipt"], stored_ledger, **_replay_kwargs(tmp_root, info))


def test_verify_private_replay_refuses_an_ineligible_bound_unit(tmp_path: Path) -> None:
    """Flip the ledger's own stored bound_unit_id to the held-out sentinel
    -- membership re-verification against the A3 packet must catch it."""
    tmp_root, info = fx.build_real_slot_root(tmp_path)
    stored_ledger = ledger.load_ledger(info["ledger_path"])
    entry = stored_ledger["entries"][fx.TARGET_SLOT_ID]
    entry["bound_unit_id"] = fx.HELDOUT_SENTINEL_UNIT_ID
    with pytest.raises(ledger.PrivateLedgerError, match="builder-eligible set"):
        ledger.verify_private_replay(info["a7_receipt"], stored_ledger, **_replay_kwargs(tmp_root, info))


def test_verify_private_replay_refuses_a_same_count_reference_swap_only_with_the_a3_verifier(tmp_path: Path) -> None:
    """A hand-fabricated-but-internally-consistent reference_check_receipt
    (same candidate fingerprint, self-consistent passed/gate booleans, its
    own receipt_id recomputed correctly) built from a *different*,
    same-count reference-text set passes the structural-only replay -- that
    is the documented limit of what A7 alone can check. Supplying the
    A3-role verifier (the real reference-text set) catches it."""
    tmp_root, info = fx.build_real_slot_root(tmp_path)
    stored_ledger = ledger.load_ledger(info["ledger_path"])
    entry = stored_ledger["entries"][fx.TARGET_SLOT_ID]

    swapped_references = {
        "synthetic-fixture-unit-alpha": "A totally different placeholder passage, still nothing like the candidate row.",
        "synthetic-fixture-unit-beta": fx.REFERENCE_TEXTS["synthetic-fixture-unit-beta"],
    }
    swapped_receipt = reference_check.build_reference_check_receipt(fx.ROW_TEXT, swapped_references, fx.A3_FIXTURE_SALT)
    assert swapped_receipt != entry["reference_check_receipt"]
    entry["reference_check_receipt"] = swapped_receipt

    # Structural-only replay cannot tell the two reference sets apart.
    ledger.verify_private_replay(info["a7_receipt"], stored_ledger, **_replay_kwargs(tmp_root, info))

    def _verifier(candidate_text: str, receipt: dict) -> None:
        reference_check.verify_reference_check_receipt(receipt, candidate_text, fx.REFERENCE_TEXTS, fx.A3_FIXTURE_SALT)

    with pytest.raises(ledger.PrivateLedgerError, match="full A3-role replay"):
        ledger.verify_private_replay(info["a7_receipt"], stored_ledger, reference_check_verifier=_verifier, **_replay_kwargs(tmp_root, info))


# --- tamper: arbitrary/held-out unit selection (P1) -------------------------


def test_construct_completion_refuses_an_ineligible_candidate_unit(tmp_path: Path) -> None:
    tmp_root = fx.base_fixture.build_synthetic_chain_root(tmp_path, resolved_stratum="standard_correct")
    sealed = fx.build_sealed_receipt_and_packet(tmp_path)
    row_content_sha256 = ledger.sha256_text(fx.ROW_TEXT)
    with pytest.raises(ledger.PrivateLedgerError, match="outside the A3-verified builder-eligible set"):
        ledger.construct_completion(
            slot_id=fx.TARGET_SLOT_ID,
            salt=fx.TEST_SALT,
            candidate_unit_ids=[fx.HELDOUT_SENTINEL_UNIT_ID],
            a4_unit_commitments=fx.a4_unit_commitments(tmp_root),
            seal_receipt_path=sealed["seal_receipt_path"],
            membership_dir=sealed["membership_dir"],
            packet_dir=sealed["packet_dir"],
            row_text=fx.ROW_TEXT,
            tier="silver",
            author=dict(fx.AUTHOR),
            reviewer=dict(fx.REVIEWER),
            evidence_receipt=evidence_binder.build_synthetic_fixture_evidence_receipt(row_content_sha256, list(fx.VESUM_IDS)),
            reference_check_receipt=fx.build_reference_check_receipt(),
            rights_receipt_id=fx.RIGHTS_RECEIPT_ID,
            allow_synthetic_fixture=True,
        )


def test_construct_completion_refuses_an_arbitrary_unit_mixed_with_an_eligible_one(tmp_path: Path) -> None:
    tmp_root = fx.base_fixture.build_synthetic_chain_root(tmp_path, resolved_stratum="standard_correct")
    sealed = fx.build_sealed_receipt_and_packet(tmp_path)
    row_content_sha256 = ledger.sha256_text(fx.ROW_TEXT)
    with pytest.raises(ledger.PrivateLedgerError, match="outside the A3-verified builder-eligible set"):
        ledger.construct_completion(
            slot_id=fx.TARGET_SLOT_ID,
            salt=fx.TEST_SALT,
            candidate_unit_ids=[fx.CANDIDATE_UNIT_IDS[0], "completely-arbitrary-unrecognized-unit-id"],
            a4_unit_commitments=fx.a4_unit_commitments(tmp_root),
            seal_receipt_path=sealed["seal_receipt_path"],
            membership_dir=sealed["membership_dir"],
            packet_dir=sealed["packet_dir"],
            row_text=fx.ROW_TEXT,
            tier="silver",
            author=dict(fx.AUTHOR),
            reviewer=dict(fx.REVIEWER),
            evidence_receipt=evidence_binder.build_synthetic_fixture_evidence_receipt(row_content_sha256, list(fx.VESUM_IDS)),
            reference_check_receipt=fx.build_reference_check_receipt(),
            rights_receipt_id=fx.RIGHTS_RECEIPT_ID,
            allow_synthetic_fixture=True,
        )


# --- tamper: evidence must be verifier-backed to be production-capable -----


def test_build_evidence_receipt_refuses_a_bare_identifier_without_a_verifier_receipt() -> None:
    """The literal P1: a well-shaped identifier alone must never be
    promoted to grade=verified/production_capable evidence."""
    with pytest.raises(evidence_binder.EvidenceBinderError, match="verifier receipt must be an object"):
        evidence_binder.build_evidence_receipt("a" * 64, ["vesum:made-up"])

    with pytest.raises(evidence_binder.EvidenceBinderError, match="verifier_receipts must be a nonempty list"):
        evidence_binder.build_evidence_receipt("a" * 64, [])


def test_build_evidence_receipt_succeeds_with_a_real_verifier_receipt() -> None:
    row_content_sha256 = "a" * 64
    verifier_receipt = evidence_binder.build_verifier_receipt(
        tool_id="mcp__sources__verify_word",
        tool_version="v1",
        identifier="vesum:lemma-example-001",
        row_content_sha256=row_content_sha256,
        tool_result_sha256="b" * 64,
        lookup_ids=["vesum-row-12345"],
    )
    receipt = evidence_binder.build_evidence_receipt(row_content_sha256, [verifier_receipt])
    assert receipt["grade"] == "verified"
    assert receipt["production_capable"] is True
    assert receipt["evidence_source"] == "verifier_receipt"
    evidence_binder.validate_evidence_receipt_integrity(receipt)


def test_verifier_receipt_refuses_a_tool_id_outside_the_sanctioned_prefix() -> None:
    with pytest.raises(evidence_binder.EvidenceBinderError, match="sanctioned"):
        evidence_binder.build_verifier_receipt(
            tool_id="some_other_tool",
            tool_version="v1",
            identifier="vesum:lemma-example-001",
            row_content_sha256="a" * 64,
            tool_result_sha256="b" * 64,
            lookup_ids=["vesum-row-12345"],
        )


def test_construct_completion_refuses_synthetic_evidence_without_explicit_opt_in(tmp_path: Path) -> None:
    tmp_root = fx.base_fixture.build_synthetic_chain_root(tmp_path, resolved_stratum="standard_correct")
    sealed = fx.build_sealed_receipt_and_packet(tmp_path)
    row_content_sha256 = ledger.sha256_text(fx.ROW_TEXT)
    with pytest.raises(ledger.PrivateLedgerError, match="not production_capable"):
        ledger.construct_completion(
            slot_id=fx.TARGET_SLOT_ID,
            salt=fx.TEST_SALT,
            candidate_unit_ids=fx.CANDIDATE_UNIT_IDS,
            a4_unit_commitments=fx.a4_unit_commitments(tmp_root),
            seal_receipt_path=sealed["seal_receipt_path"],
            membership_dir=sealed["membership_dir"],
            packet_dir=sealed["packet_dir"],
            row_text=fx.ROW_TEXT,
            tier="silver",
            author=dict(fx.AUTHOR),
            reviewer=dict(fx.REVIEWER),
            evidence_receipt=evidence_binder.build_synthetic_fixture_evidence_receipt(row_content_sha256, list(fx.VESUM_IDS)),
            reference_check_receipt=fx.build_reference_check_receipt(),
            rights_receipt_id=fx.RIGHTS_RECEIPT_ID,
            # allow_synthetic_fixture defaults to False -- never silently opts in.
        )


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
        reissue.reissue_private_artifact(
            membership_path, old_receipt, new_receipt, sorted(f["family_id"] for f in old_receipt["source_family_registry"]["families"]), EMPTY_A2_RECEIPT, EMPTY_MANIFEST
        )


def test_reissue_refuses_a_changed_family_registry(tmp_path: Path) -> None:
    old_receipt, membership_path = _generate_sealed_receipt(tmp_path, "22" * 32)
    new_receipt = copy.deepcopy(old_receipt)
    new_receipt["source_family_registry"]["families"][0]["member_source_unit_ids"].append("a-new-unit")
    with pytest.raises(reissue.ReissueError, match="reseal, not a reissue"):
        reissue.reissue_private_artifact(
            membership_path, old_receipt, new_receipt, sorted(f["family_id"] for f in old_receipt["source_family_registry"]["families"]), EMPTY_A2_RECEIPT, EMPTY_MANIFEST
        )


def test_reissue_succeeds_and_rebinds_when_membership_is_provably_unchanged(tmp_path: Path) -> None:
    """A trivial (identical-content) reissue still exercises the full
    equality-check-then-rebind path live -- the mechanism under test is
    that the three core commitments and the registry are proven unchanged
    before any rewrite happens, not that the receipt content itself
    differs."""
    old_receipt, membership_path = _generate_sealed_receipt(tmp_path, "33" * 32)
    new_receipt = copy.deepcopy(old_receipt)
    family_ids = sorted(f["family_id"] for f in old_receipt["source_family_registry"]["families"])
    summary = reissue.reissue_private_artifact(membership_path, old_receipt, new_receipt, family_ids, EMPTY_A2_RECEIPT, EMPTY_MANIFEST)
    assert summary["assignment_commitment_sha256"] == old_receipt["heldout_partition_seal"]["assignment_algorithm"]["assignment_commitment_sha256"]
    # The artifact still reproduces against both (identical) receipts.
    reissue.heldout.verify_against_receipt(membership_path, new_receipt, family_ids)
    reissue.heldout.verify_against_receipt(membership_path, old_receipt, family_ids)


def test_reissue_refuses_when_an_assigned_stratum_fails_the_candidate_family_floor(tmp_path: Path) -> None:
    """End-to-end: a single-family-supported, manifest-ASSIGNED stratum
    must never survive a reissue (Invariant D1, wired PR #7662 repair 2)."""
    old_receipt, membership_path = _generate_sealed_receipt(tmp_path, "66" * 32)
    new_receipt = copy.deepcopy(old_receipt)
    family_ids = sorted(f["family_id"] for f in old_receipt["source_family_registry"]["families"])
    manifest = {"slot_series": [{"stratum": "standard_correct", "assignment_state": "ASSIGNED"}]}
    # db.textbooks.public is a member of exactly one family in the real
    # registry -- one distinct supporting family, below heldout_count(1) + 1.
    a2_receipt = {"stratum_coverage_map": [{"stratum": "standard_correct", "supporting_existing_source_unit_ids": ["db.textbooks.public"]}]}
    with pytest.raises(reissue.ReissueError, match="candidate-family floor"):
        reissue.reissue_private_artifact(membership_path, old_receipt, new_receipt, family_ids, a2_receipt, manifest)


def test_reissue_refuses_an_assigned_stratum_with_no_matching_a2_coverage_entry(tmp_path: Path) -> None:
    old_receipt, membership_path = _generate_sealed_receipt(tmp_path, "77" * 32)
    new_receipt = copy.deepcopy(old_receipt)
    family_ids = sorted(f["family_id"] for f in old_receipt["source_family_registry"]["families"])
    manifest = {"slot_series": [{"stratum": "standard_correct", "assignment_state": "ASSIGNED"}]}
    with pytest.raises(reissue.ReissueError, match="no matching A2 stratum_coverage_map entry"):
        reissue.reissue_private_artifact(membership_path, old_receipt, new_receipt, family_ids, EMPTY_A2_RECEIPT, manifest)


def test_builder_packet_reissue_succeeds_and_refuses_a_wrong_expected_commitment(tmp_path: Path) -> None:
    old_receipt, membership_path = _generate_sealed_receipt(tmp_path, "44" * 32)
    private_dir = membership_path.parent
    old_receipt_path = tmp_path / "old_seal_receipt.json"
    old_receipt_path.write_text(json.dumps(old_receipt), encoding="utf-8")

    packet.issue_packet(old_receipt_path, private_dir, private_dir)
    summary = packet.verify_packet(old_receipt_path, private_dir, private_dir)

    new_receipt = copy.deepcopy(old_receipt)
    family_ids = sorted(f["family_id"] for f in old_receipt["source_family_registry"]["families"])
    reissue.reissue_private_artifact(membership_path, old_receipt, new_receipt, family_ids, EMPTY_A2_RECEIPT, EMPTY_MANIFEST)
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


def test_reference_check_receipt_fails_when_candidate_matches_a_reference_exactly() -> None:
    receipt = reference_check.build_reference_check_receipt(fx.ROW_TEXT, {"x": fx.ROW_TEXT}, fx.A3_FIXTURE_SALT)
    assert receipt["reconstruction_gates"]["exact"]["passed"] is False
    assert receipt["reconstruction_gates"]["reconstruction"]["passed"] is False
    assert receipt["passed"] is False


def test_reference_check_receipt_passes_for_dissimilar_text() -> None:
    receipt = fx.build_reference_check_receipt()
    assert all(gate["passed"] for gate in receipt["reconstruction_gates"].values())
    assert receipt["split_duplicate"]["passed"] is True
    assert receipt["passed"] is True
    reference_check.validate_reference_check_receipt_integrity(receipt)


def test_reference_check_receipt_never_carries_candidate_or_reference_text() -> None:
    receipt = fx.build_reference_check_receipt()
    serialized = json.dumps(receipt, ensure_ascii=False, sort_keys=True)
    assert fx.ROW_TEXT not in serialized
    for text in fx.REFERENCE_TEXTS.values():
        assert text not in serialized


def test_reference_check_receipt_refuses_a_same_count_different_content_reference_swap() -> None:
    """The advisor requirement: the A3 receipt binds the actual reference
    set, not only its count -- swapping in a same-count, different-content
    reference set must invalidate the receipt under replay."""
    receipt = fx.build_reference_check_receipt()
    swapped_references = {
        "synthetic-fixture-unit-alpha": "A totally different placeholder passage, still nothing like the candidate row.",
        "synthetic-fixture-unit-beta": fx.REFERENCE_TEXTS["synthetic-fixture-unit-beta"],
    }
    with pytest.raises(reference_check.ReferenceCheckError, match="does not reproduce"):
        reference_check.verify_reference_check_receipt(receipt, fx.ROW_TEXT, swapped_references, fx.A3_FIXTURE_SALT)


def test_reference_check_receipt_integrity_catches_a_flipped_passed_flag() -> None:
    receipt = fx.build_reference_check_receipt()
    tampered = {**receipt, "passed": not receipt["passed"]}
    with pytest.raises(reference_check.ReferenceCheckError, match="fails its own integrity recheck"):
        reference_check.validate_reference_check_receipt_integrity(tampered)


def test_evidence_receipt_refuses_a_malformed_identifier() -> None:
    with pytest.raises(evidence_binder.EvidenceBinderError, match="VESUM/sources shape"):
        evidence_binder.build_synthetic_fixture_evidence_receipt("a" * 64, ["not-a-valid-id"])


# --- the shared admission engine: the new helper is byte-identical at zero -


def test_assemble_receipt_from_row_receipts_matches_admit_rows_at_zero() -> None:
    assert admission.assemble_receipt_from_row_receipts(outcome_sha256=a7.V4_SHA256, row_receipts=[]) == admission.admit_rows(
        outcome_sha256=a7.V4_SHA256, rows=[]
    )
