"""V4 real-slot mechanism (PR-A, mechanism-only, zero real rows): the
acceptance proof that a genuine, independently-authored, evidence-bound,
non-reconstructive row can traverse A7 and A8 -- built entirely from
synthetic fixtures, never real corpus or held-out membership -- plus the
tamper-refusal coverage the frozen packet requires.

Every completion here is constructed live through
``v4_a7_private_ledger.construct_completion`` (real gates, real admission
engine call, real receipt schemas) -- never a hand-authored shape standing
in for the mechanism.

PR #7662 repair 4 (designated-advisor ``GO_REPAIR``) added the signed
Ed25519 trust-boundary tests below: sources-verification attestations
(repair A), mandatory A3 replay authenticity (repair B), Invariant D1 at
every load-bearing path (repair C), the exact project-row rights binding
(repair D), and authenticated author/reviewer fleet-execution receipts
(repair E).
"""

from __future__ import annotations

import copy
import dataclasses
import inspect
import json
from pathlib import Path

import _v4_a7_real_slot_fixture as fx
import pytest

from scripts.fleet_comms.contracts import CompletionState, ResponseEnvelope
from scripts.projects.open_model_data import v4_a3_builder_packet as packet
from scripts.projects.open_model_data import v4_a3_candidate_family_floor as floor
from scripts.projects.open_model_data import v4_a3_d1_transition_validator as d1_validator
from scripts.projects.open_model_data import v4_a3_heldout_family_assignment as heldout
from scripts.projects.open_model_data import v4_a3_reference_check as reference_check
from scripts.projects.open_model_data import v4_a3_reissue as reissue
from scripts.projects.open_model_data import v4_a3_split_duplicate_check as split_check
from scripts.projects.open_model_data import v4_a7_evidence_binder as evidence_binder
from scripts.projects.open_model_data import v4_a7_original_row_factory as a7
from scripts.projects.open_model_data import v4_a7_private_ledger as ledger
from scripts.projects.open_model_data import v4_a8_admission_assembly as a8
from scripts.projects.open_model_data import v4_fleet_execution_authority as fleet_execution
from scripts.projects.open_model_data import v4_original_row_admission as admission
from scripts.projects.open_model_data import v4_sources_authority as sources_authority
from scripts.projects.open_model_data import v4_stage_evidence as ev
from scripts.projects.open_model_data import v4_trust_authority as trust

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


def _real_slot_construction_kwargs(tmp_root: Path, sealed: dict) -> dict:
    """The full, valid kwargs for a real ``construct_completion`` call
    against the fixture's standard target slot -- callers override only
    what they want to tamper with."""
    manifest = json.loads((tmp_root / "data/projects/open_model_data/admission/dataset_v4_pilot_slot_manifest_v1.json").read_text(encoding="utf-8"))
    a2_receipt = json.loads((tmp_root / "data/projects/open_model_data/admission/dataset_v4_a2_source_operation_admission_receipt_v1.json").read_text(encoding="utf-8"))
    row_content_sha256 = ledger.sha256_text(fx.ROW_TEXT)
    reference_check_receipt = fx.build_reference_check_receipt()
    reference_check_signature, replay_attestation = fx.build_reference_check_authenticity(reference_check_receipt)
    author_execution_receipt = fx.build_author_execution_receipt(row_content_sha256)
    authorship_receipt = ledger.build_authorship_receipt(author_execution_receipt=author_execution_receipt, trust_policy=fx.TRUST_POLICY, row_content_sha256=row_content_sha256)
    authorship_receipt_sha256 = ledger.sha256_text(ledger.canonical_json(authorship_receipt))
    reviewer_execution_receipt = fx.build_reviewer_execution_receipt(row_content_sha256, authorship_receipt_sha256)
    return {
        "slot_id": fx.TARGET_SLOT_ID,
        "salt": fx.TEST_SALT,
        "candidate_unit_ids": list(fx.CANDIDATE_UNIT_IDS),
        "a4_unit_commitments": fx.a4_unit_commitments(tmp_root),
        "seal_receipt_path": sealed["seal_receipt_path"],
        "membership_dir": sealed["membership_dir"],
        "packet_dir": sealed["packet_dir"],
        "manifest": manifest,
        "a2_receipt": a2_receipt,
        "row_text": fx.ROW_TEXT,
        "tier": "silver",
        "author_execution_receipt": author_execution_receipt,
        "reviewer_execution_receipt": reviewer_execution_receipt,
        "evidence_receipt": evidence_binder.build_synthetic_fixture_evidence_receipt(row_content_sha256, list(fx.VESUM_IDS)),
        "reference_check_receipt": reference_check_receipt,
        "reference_check_signature": reference_check_signature,
        "replay_attestation": replay_attestation,
        "rights_receipt_id": fx.RIGHTS_RECEIPT_ID,
        "trust_policy": fx.TRUST_POLICY,
        "allow_synthetic_fixture": True,
    }


def _replay_kwargs(tmp_root: Path, info: dict) -> dict:
    sealed = info["sealed"]
    manifest = json.loads((tmp_root / "data/projects/open_model_data/admission/dataset_v4_pilot_slot_manifest_v1.json").read_text(encoding="utf-8"))
    a2_receipt = json.loads((tmp_root / "data/projects/open_model_data/admission/dataset_v4_a2_source_operation_admission_receipt_v1.json").read_text(encoding="utf-8"))
    return {
        "salt": fx.TEST_SALT,
        "a4_unit_commitments": fx.a4_unit_commitments(tmp_root),
        "seal_receipt_path": sealed["seal_receipt_path"],
        "membership_dir": sealed["membership_dir"],
        "packet_dir": sealed["packet_dir"],
        "manifest": manifest,
        "a2_receipt": a2_receipt,
        "trust_policy": fx.TRUST_POLICY,
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


def test_a7_ledger_and_review_receipts_carry_no_source_or_membership_fields(tmp_path: Path) -> None:
    """Forbidden-field guard for the author/reviewer model packet
    serializer (non-blocker preserved, PR #7662 repair 4): the private
    authorship/review receipts -- including the embedded fleet-execution
    receipt -- never carry a source-unit id, family id, held-out membership
    boolean, or eligible-unit list."""
    _, info = fx.build_real_slot_root(tmp_path)
    stored_ledger = ledger.load_ledger(info["ledger_path"])
    entry = stored_ledger["entries"][fx.TARGET_SLOT_ID]
    for receipt_key in ("authorship_receipt", "review_receipt"):
        serialized = json.dumps(entry[receipt_key], ensure_ascii=False, sort_keys=True)
        for needle in FORBIDDEN_PUBLIC_TERMS:
            assert needle not in serialized, f"forbidden term leaked into {receipt_key}: {needle}"
        assert entry[receipt_key]["saw_eligible_unit_ids"] is False


# --- tamper: same-family / same-session / same-run author-reviewer ---------


def test_review_receipt_refuses_same_model_family_as_author() -> None:
    row_content_sha256 = "a" * 64
    author_execution_receipt = fx.build_author_execution_receipt(row_content_sha256)
    authorship = ledger.build_authorship_receipt(author_execution_receipt=author_execution_receipt, trust_policy=fx.TRUST_POLICY, row_content_sha256=row_content_sha256)
    authorship_receipt_sha256 = ledger.sha256_text(ledger.canonical_json(authorship))
    # A distinct task/run/session, properly signed under the fixture's own
    # fleet key, but the reviewer's task-state seat_or_model resolves (via
    # the canonical resolver) to the *same* model family as the author's --
    # never a caller-asserted family string.
    same_family_task_state = fx.build_reviewer_task_state(seat_or_model=fx.AUTHOR_SEAT_OR_MODEL)
    reviewer_execution_receipt = fx.build_reviewer_execution_receipt(row_content_sha256, authorship_receipt_sha256, task_state=same_family_task_state)
    with pytest.raises(ledger.PrivateLedgerError, match="model family"):
        ledger.build_review_receipt(authorship_receipt=authorship, reviewer_execution_receipt=reviewer_execution_receipt, trust_policy=fx.TRUST_POLICY, row_content_sha256=row_content_sha256)


def test_review_receipt_refuses_same_session_as_author() -> None:
    row_content_sha256 = "a" * 64
    author_execution_receipt = fx.build_author_execution_receipt(row_content_sha256)
    authorship = ledger.build_authorship_receipt(author_execution_receipt=author_execution_receipt, trust_policy=fx.TRUST_POLICY, row_content_sha256=row_content_sha256)
    authorship_receipt_sha256 = ledger.sha256_text(ledger.canonical_json(authorship))
    # A distinct model_family/task/run, but the same provider session
    # identity (the envelope's own session_id, cross-checked against the
    # task state) as the author -- signed under the fixture's own fleet key
    # so the signature stays valid while the session collides.
    same_session_task_state = fx.build_reviewer_task_state(session_id=fx.AUTHOR_SESSION_ID)
    same_session_envelope = fx.build_terminal_envelope(
        raw_capture_sha256=ledger.sha256_text("fixture-reviewer-execution-result"), session_id=fx.AUTHOR_SESSION_ID, raw_capture_artifact_id="fixture-reviewer-raw-capture-001"
    )
    reviewer_execution_receipt = fx.build_reviewer_execution_receipt(
        row_content_sha256, authorship_receipt_sha256, task_state=same_session_task_state, envelope=same_session_envelope
    )
    with pytest.raises(ledger.PrivateLedgerError, match="session"):
        ledger.build_review_receipt(authorship_receipt=authorship, reviewer_execution_receipt=reviewer_execution_receipt, trust_policy=fx.TRUST_POLICY, row_content_sha256=row_content_sha256)


# --- tamper: saw_source_text / saw_heldout / saw_eligible_unit_ids ---------


@pytest.mark.parametrize("saw_flag", ["saw_source_text", "saw_heldout", "saw_eligible_unit_ids"])
def test_author_execution_receipt_refuses_any_saw_flag_true(saw_flag: str) -> None:
    with pytest.raises(fleet_execution.FleetExecutionError, match=saw_flag):
        fx.build_author_execution_receipt("a" * 64, **{saw_flag: True})


@pytest.mark.parametrize("saw_flag", ["saw_source_text", "saw_heldout", "saw_eligible_unit_ids"])
def test_reviewer_execution_receipt_refuses_any_saw_flag_true(saw_flag: str) -> None:
    with pytest.raises(fleet_execution.FleetExecutionError, match=saw_flag):
        fx.build_reviewer_execution_receipt("a" * 64, "b" * 64, **{saw_flag: True})


# --- tamper: public lineage equal to an A4 commitment -----------------------


def test_lineage_id_colliding_with_an_a4_commitment_refuses() -> None:
    with pytest.raises(ledger.PrivateLedgerError, match="unit_commitments"):
        ledger.validate_lineage_not_equal_to_a4_commitment(["some-a4-commitment-hex"], ["some-a4-commitment-hex"])


def test_real_construction_refuses_when_lineage_collides_with_a4_commitment(tmp_path: Path) -> None:
    tmp_root = fx.base_fixture.build_synthetic_chain_root(tmp_path, resolved_stratum="standard_correct")
    sealed = fx.build_sealed_receipt_and_packet(tmp_path)
    real_commitments = fx.a4_unit_commitments(tmp_root)
    salt = fx.TEST_SALT
    bound_unit = ledger.pick_bound_unit(salt, fx.TARGET_SLOT_ID, fx.CANDIDATE_UNIT_IDS)
    real_lineage_id = ledger.per_row_lineage_id(salt, fx.TARGET_SLOT_ID, bound_unit)
    kwargs = _real_slot_construction_kwargs(tmp_root, sealed)
    kwargs["a4_unit_commitments"] = [*real_commitments, real_lineage_id]
    with pytest.raises(ledger.PrivateLedgerError, match="unit_commitments"):
        ledger.construct_completion(**kwargs)


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


def test_verify_private_replay_refuses_a_same_count_reference_swap_on_the_default_path(tmp_path: Path) -> None:
    """Repair B (PR #7662 repair 4): a hand-fabricated-but-internally-
    consistent reference_check_receipt (same candidate fingerprint,
    self-consistent passed/gate booleans, its own receipt_id recomputed
    correctly) built from a *different*, same-count reference-text set can
    no longer pass even the *default* replay path -- the mandatory signed
    replay attestation is bound to the original receipt's exact digest, so
    swapping the receipt without also forging a valid A3 signature over the
    new digest is refused."""
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

    with pytest.raises(ledger.PrivateLedgerError, match="A3 reference-check signed authenticity failed replay"):
        ledger.verify_private_replay(info["a7_receipt"], stored_ledger, **_replay_kwargs(tmp_root, info))

    def _verifier(candidate_text: str, receipt: dict) -> None:
        reference_check.verify_reference_check_receipt(receipt, candidate_text, fx.REFERENCE_TEXTS, fx.A3_FIXTURE_SALT)

    with pytest.raises(ledger.PrivateLedgerError, match="A3 reference-check signed authenticity failed replay"):
        ledger.verify_private_replay(info["a7_receipt"], stored_ledger, reference_check_verifier=_verifier, **_replay_kwargs(tmp_root, info))


# --- tamper: arbitrary/held-out unit selection (P1) -------------------------


def test_a7_factory_gate_closed_when_the_a3_seal_receipt_is_missing(tmp_path: Path) -> None:
    tmp_root = fx.base_fixture.build_synthetic_chain_root(tmp_path, resolved_stratum="standard_correct")
    (tmp_root / a7.A3_SEAL_RECEIPT_RELATIVE).unlink()
    gate = a7.check_factory_gate(tmp_root)
    assert gate["factory_slice_ready"] is False
    assert gate["blocked_reason_code"] == "required_public_artifact_missing:a3_seal_receipt"


def test_construct_completion_refuses_an_ineligible_candidate_unit(tmp_path: Path) -> None:
    tmp_root = fx.base_fixture.build_synthetic_chain_root(tmp_path, resolved_stratum="standard_correct")
    sealed = fx.build_sealed_receipt_and_packet(tmp_path)
    kwargs = _real_slot_construction_kwargs(tmp_root, sealed)
    kwargs["candidate_unit_ids"] = [fx.HELDOUT_SENTINEL_UNIT_ID]
    with pytest.raises(ledger.PrivateLedgerError, match="outside the A3-verified builder-eligible set"):
        ledger.construct_completion(**kwargs)


def test_construct_completion_refuses_an_arbitrary_unit_mixed_with_an_eligible_one(tmp_path: Path) -> None:
    tmp_root = fx.base_fixture.build_synthetic_chain_root(tmp_path, resolved_stratum="standard_correct")
    sealed = fx.build_sealed_receipt_and_packet(tmp_path)
    kwargs = _real_slot_construction_kwargs(tmp_root, sealed)
    kwargs["candidate_unit_ids"] = [fx.CANDIDATE_UNIT_IDS[0], "completely-arbitrary-unrecognized-unit-id"]
    with pytest.raises(ledger.PrivateLedgerError, match="outside the A3-verified builder-eligible set"):
        ledger.construct_completion(**kwargs)


# --- tamper: evidence must be verifier-backed to be production-capable -----


def test_build_evidence_receipt_refuses_without_a_nonempty_verifier_receipts_list() -> None:
    with pytest.raises(evidence_binder.EvidenceBinderError, match="verifier_receipts must be a nonempty list"):
        evidence_binder.build_evidence_receipt("a" * 64, [], trust_policy=trust.empty_trust_policy())


def test_build_verifier_receipt_succeeds_with_a_genuine_signed_attestation() -> None:
    """Repair A (PR #7662 repair 4): the only way to a production-capable
    verifier receipt is a signed sources-authority attestation."""
    row_content_sha256 = "a" * 64
    attestation = sources_authority.issue_verifier_attestation(
        signing_key_hex=fx.SOURCES_SIGNING_KEY_HEX,
        signer_key_id=fx.SOURCES_KEY_ID,
        outcome_sha256=ledger.V4_SHA256,
        row_content_sha256=row_content_sha256,
        identifier="vesum:lemma-example-001",
        tool_id="mcp__sources__verify_word",
        tool_version="v1",
        request_id="req-1",
        tool_result_sha256="b" * 64,
        lookup_ids=["vesum-row-12345"],
        invocation_id="inv-1",
    )
    verifier_receipt = evidence_binder.build_verifier_receipt(attestation=attestation, trust_policy=fx.TRUST_POLICY)
    receipt = evidence_binder.build_evidence_receipt(row_content_sha256, [verifier_receipt], trust_policy=fx.TRUST_POLICY)
    assert receipt["grade"] == "verified"
    assert receipt["production_capable"] is True
    assert receipt["evidence_source"] == "verifier_receipt"
    evidence_binder.validate_evidence_receipt_integrity(receipt, fx.TRUST_POLICY)


def test_build_verifier_receipt_refuses_an_unsigned_self_fabricated_attestation() -> None:
    """The exact prior P1: any caller who supplies the tool identity/result
    fields directly (correctly recomputed self-hash and all) but no real
    signature is refused."""
    row_content_sha256 = "a" * 64
    forged_attestation = {
        "schema_version": sources_authority.SCHEMA_VERSION,
        "outcome_sha256": ledger.V4_SHA256,
        "row_content_sha256": row_content_sha256,
        "identifier": "vesum:lemma-example-001",
        "tool_id": "mcp__sources__verify_word",
        "tool_version": "v1",
        "request_id": "req-1",
        "tool_result_sha256": "b" * 64,
        "lookup_ids": ["vesum-row-12345"],
        "success": True,
        "invocation_id": "inv-1",
        "signer_key_id": fx.SOURCES_KEY_ID,
        "signature_hex": "00" * 64,
    }
    with pytest.raises(evidence_binder.EvidenceBinderError, match="authenticity"):
        evidence_binder.build_verifier_receipt(attestation=forged_attestation, trust_policy=fx.TRUST_POLICY)


def test_build_verifier_receipt_refuses_an_unknown_signer_key() -> None:
    attestation = sources_authority.issue_verifier_attestation(
        signing_key_hex=fx.SOURCES_SIGNING_KEY_HEX,
        signer_key_id="unregistered-key",
        outcome_sha256=ledger.V4_SHA256,
        row_content_sha256="a" * 64,
        identifier="vesum:lemma-example-001",
        tool_id="mcp__sources__verify_word",
        tool_version="v1",
        request_id="req-1",
        tool_result_sha256="b" * 64,
        lookup_ids=["vesum-row-12345"],
        invocation_id="inv-1",
    )
    with pytest.raises(evidence_binder.EvidenceBinderError, match="authenticity"):
        evidence_binder.build_verifier_receipt(attestation=attestation, trust_policy=fx.TRUST_POLICY)


def test_build_verifier_receipt_refuses_a_revoked_signer_key() -> None:
    revoked_policy = trust.build_test_trust_policy(sources={fx.SOURCES_KEY_ID: fx.SOURCES_PUBLIC_KEY_HEX}, revoked_key_ids=frozenset({fx.SOURCES_KEY_ID}))
    attestation = sources_authority.issue_verifier_attestation(
        signing_key_hex=fx.SOURCES_SIGNING_KEY_HEX,
        signer_key_id=fx.SOURCES_KEY_ID,
        outcome_sha256=ledger.V4_SHA256,
        row_content_sha256="a" * 64,
        identifier="vesum:lemma-example-001",
        tool_id="mcp__sources__verify_word",
        tool_version="v1",
        request_id="req-1",
        tool_result_sha256="b" * 64,
        lookup_ids=["vesum-row-12345"],
        invocation_id="inv-1",
    )
    with pytest.raises(evidence_binder.EvidenceBinderError, match="revoked"):
        evidence_binder.build_verifier_receipt(attestation=attestation, trust_policy=revoked_policy)


def test_build_verifier_receipt_refuses_against_an_empty_production_trust_policy() -> None:
    """Mechanism-only production: an empty trust policy (no active
    ``sources`` key yet) refuses every production-capable receipt."""
    attestation = sources_authority.issue_verifier_attestation(
        signing_key_hex=fx.SOURCES_SIGNING_KEY_HEX,
        signer_key_id=fx.SOURCES_KEY_ID,
        outcome_sha256=ledger.V4_SHA256,
        row_content_sha256="a" * 64,
        identifier="vesum:lemma-example-001",
        tool_id="mcp__sources__verify_word",
        tool_version="v1",
        request_id="req-1",
        tool_result_sha256="b" * 64,
        lookup_ids=["vesum-row-12345"],
        invocation_id="inv-1",
    )
    with pytest.raises(evidence_binder.EvidenceBinderError, match="authenticity"):
        evidence_binder.build_verifier_receipt(attestation=attestation, trust_policy=trust.empty_trust_policy())


def test_verifier_attestation_refuses_a_tool_id_outside_the_sanctioned_prefix() -> None:
    with pytest.raises(sources_authority.SourcesAuthorityError, match="sanctioned"):
        sources_authority.issue_verifier_attestation(
            signing_key_hex=fx.SOURCES_SIGNING_KEY_HEX,
            signer_key_id=fx.SOURCES_KEY_ID,
            outcome_sha256=ledger.V4_SHA256,
            row_content_sha256="a" * 64,
            identifier="vesum:lemma-example-001",
            tool_id="some_other_tool",
            tool_version="v1",
            request_id="req-1",
            tool_result_sha256="b" * 64,
            lookup_ids=["vesum-row-12345"],
            invocation_id="inv-1",
        )


def test_construct_completion_refuses_synthetic_evidence_without_explicit_opt_in(tmp_path: Path) -> None:
    tmp_root = fx.base_fixture.build_synthetic_chain_root(tmp_path, resolved_stratum="standard_correct")
    sealed = fx.build_sealed_receipt_and_packet(tmp_path)
    kwargs = _real_slot_construction_kwargs(tmp_root, sealed)
    kwargs["allow_synthetic_fixture"] = False
    with pytest.raises(ledger.PrivateLedgerError, match="not production_capable"):
        ledger.construct_completion(**kwargs)


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


# --- repair C: Invariant D1 at every load-bearing path ----------------------


def _real_seal_receipt() -> dict:
    return json.loads((ROOT / "data/projects/open_model_data/admission/dataset_v4_a3_heldout_source_family_seal_receipt_v1.json").read_text(encoding="utf-8"))


def test_d1_transition_validator_refuses_a_single_family_assigned_stratum() -> None:
    manifest = {"slot_series": [{"stratum": "standard_correct", "assignment_state": "ASSIGNED"}]}
    a2_receipt = {"stratum_coverage_map": [{"stratum": "standard_correct", "supporting_existing_source_unit_ids": ["db.textbooks.public"]}]}
    with pytest.raises(d1_validator.D1TransitionError, match="floor not met"):
        d1_validator.validate_manifest_meets_d1(manifest, a2_receipt, _real_seal_receipt())


def test_d1_transition_validator_passes_two_distinct_supporting_families() -> None:
    manifest = {"slot_series": [{"stratum": "standard_correct", "assignment_state": "ASSIGNED"}]}
    a2_receipt = {"stratum_coverage_map": [{"stratum": "standard_correct", "supporting_existing_source_unit_ids": ["db.textbooks.public", "db.external_articles"]}]}
    d1_validator.validate_manifest_meets_d1(manifest, a2_receipt, _real_seal_receipt())  # no raise


def test_d1_transition_validator_ignores_an_unassigned_stratum() -> None:
    manifest = {"slot_series": [{"stratum": "standard_correct", "assignment_state": "UNASSIGNED_PENDING_A2_A3"}]}
    d1_validator.validate_manifest_meets_d1(manifest, EMPTY_A2_RECEIPT, _real_seal_receipt())  # no raise


def test_a7_factory_gate_refuses_a_directly_assigned_manifest_that_fails_d1(tmp_path: Path) -> None:
    """Directly changing a synthetic manifest to ASSIGNED with one
    supporting family (never through reissue, and never through this
    fixture's own D1-compliant top-up) must fail A7's own gate."""
    tmp_root = fx.base_fixture.build_synthetic_chain_root(tmp_path, resolved_stratum="standard_correct")
    a2_path = tmp_root / "data/projects/open_model_data/admission/dataset_v4_a2_source_operation_admission_receipt_v1.json"
    a2_receipt = json.loads(a2_path.read_text(encoding="utf-8"))
    for coverage in a2_receipt["stratum_coverage_map"]:
        if coverage["stratum"] == "standard_correct":
            coverage["supporting_existing_source_unit_ids"] = ["db.textbooks.public"]  # single family only
    a2_path.write_text(json.dumps(a2_receipt))
    with pytest.raises(a7.OriginalRowFactoryError, match="Invariant D1"):
        a7.check_factory_gate(tmp_root)


def test_construct_completion_refuses_when_the_manifest_fails_d1(tmp_path: Path) -> None:
    tmp_root = fx.base_fixture.build_synthetic_chain_root(tmp_path, resolved_stratum="standard_correct")
    sealed = fx.build_sealed_receipt_and_packet(tmp_path)
    kwargs = _real_slot_construction_kwargs(tmp_root, sealed)
    kwargs["manifest"] = {"slot_series": [{"stratum": "standard_correct", "id_prefix": "v4p-standard-correct", "start": 1, "count": 15, "assignment_state": "ASSIGNED"}]}
    kwargs["a2_receipt"] = {"stratum_coverage_map": [{"stratum": "standard_correct", "supporting_existing_source_unit_ids": ["db.textbooks.public"]}]}
    with pytest.raises(ledger.PrivateLedgerError, match="Invariant D1"):
        ledger.construct_completion(**kwargs)


def test_verify_private_replay_refuses_when_the_manifest_fails_d1(tmp_path: Path) -> None:
    tmp_root, info = fx.build_real_slot_root(tmp_path)
    stored_ledger = ledger.load_ledger(info["ledger_path"])
    replay_kwargs = _replay_kwargs(tmp_root, info)
    replay_kwargs["manifest"] = {"slot_series": [{"stratum": "standard_correct", "id_prefix": "v4p-standard-correct", "start": 1, "count": 15, "assignment_state": "ASSIGNED"}]}
    replay_kwargs["a2_receipt"] = {"stratum_coverage_map": [{"stratum": "standard_correct", "supporting_existing_source_unit_ids": ["db.textbooks.public"]}]}
    with pytest.raises(ledger.PrivateLedgerError, match="Invariant D1"):
        ledger.verify_private_replay(info["a7_receipt"], stored_ledger, **replay_kwargs)


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


# --- repair D: exact project-row rights binding -----------------------------


def test_build_admission_input_row_accepts_the_exact_derived_rights_receipt_id() -> None:
    assert ledger.derive_project_rights_receipt_id() == fx.RIGHTS_RECEIPT_ID
    assert fx.RIGHTS_RECEIPT_ID.startswith("license.content.cc-by-sa-4.0@")


@pytest.mark.parametrize(
    "bad_rights_receipt_id",
    [
        fx.ZERO_RIGHTS_RECEIPT_ID,
        "an-arbitrary-nonempty-string",
        "license.content.mit@" + ("a" * 64),
    ],
)
def test_construct_completion_refuses_a_wrong_rights_receipt_id(tmp_path: Path, bad_rights_receipt_id: str) -> None:
    tmp_root = fx.base_fixture.build_synthetic_chain_root(tmp_path, resolved_stratum="standard_correct")
    sealed = fx.build_sealed_receipt_and_packet(tmp_path)
    kwargs = _real_slot_construction_kwargs(tmp_root, sealed)
    kwargs["rights_receipt_id"] = bad_rights_receipt_id
    with pytest.raises(ledger.PrivateLedgerError, match="rights_receipt_id"):
        ledger.construct_completion(**kwargs)


def test_construct_completion_refuses_a_one_nibble_mutated_rights_receipt_id(tmp_path: Path) -> None:
    tmp_root = fx.base_fixture.build_synthetic_chain_root(tmp_path, resolved_stratum="standard_correct")
    sealed = fx.build_sealed_receipt_and_packet(tmp_path)
    kwargs = _real_slot_construction_kwargs(tmp_root, sealed)
    mutated = fx.RIGHTS_RECEIPT_ID[:-1] + ("0" if fx.RIGHTS_RECEIPT_ID[-1] != "0" else "1")
    kwargs["rights_receipt_id"] = mutated
    with pytest.raises(ledger.PrivateLedgerError, match="rights_receipt_id"):
        ledger.construct_completion(**kwargs)


def test_private_replay_refuses_a_forged_ledger_with_a_recomputed_wrong_rights_receipt_id(tmp_path: Path) -> None:
    """A fully self-consistent forged ledger (every unkeyed hash
    recomputed) where the rights identifier was swapped for the prohibited
    zero digest must still refuse, because ``build_admission_input_row``
    re-derives and asserts the exact identifier on every replay."""
    tmp_root, info = fx.build_real_slot_root(tmp_path)
    stored_ledger = ledger.load_ledger(info["ledger_path"])
    entry = stored_ledger["entries"][fx.TARGET_SLOT_ID]
    entry["admission_input_row"] = {
        **entry["admission_input_row"],
        "rights": {**entry["admission_input_row"]["rights"], "receipt_id": fx.ZERO_RIGHTS_RECEIPT_ID},
    }
    with pytest.raises(ledger.PrivateLedgerError, match="rights_receipt_id"):
        ledger.verify_private_replay(info["a7_receipt"], stored_ledger, **_replay_kwargs(tmp_root, info))


def test_derive_project_rights_receipt_id_matches_exact_license_bytes() -> None:
    """No newline-normalization drift: the derived suffix must equal
    sha256 of the exact bytes of LICENSE-CONTENT.md."""
    import hashlib

    expected = hashlib.sha256((ROOT / "LICENSE-CONTENT.md").read_bytes()).hexdigest()
    assert ledger.derive_project_rights_receipt_id() == f"license.content.cc-by-sa-4.0@{expected}"


# --- repair E: authenticated author/reviewer executions --------------------


def test_build_authorship_receipt_refuses_a_caller_supplied_signature() -> None:
    row_content_sha256 = "a" * 64
    real = fx.build_author_execution_receipt(row_content_sha256)
    forged = {**real, "model_family": "attacker-controlled-family", "signature_hex": real["signature_hex"]}
    with pytest.raises(ledger.PrivateLedgerError, match="authenticity"):
        ledger.build_authorship_receipt(author_execution_receipt=forged, trust_policy=fx.TRUST_POLICY, row_content_sha256=row_content_sha256)


def test_build_authorship_receipt_refuses_missing_signature() -> None:
    row_content_sha256 = "a" * 64
    real = fx.build_author_execution_receipt(row_content_sha256)
    without_signature = {k: v for k, v in real.items() if k != "signature_hex"}
    with pytest.raises(fleet_execution.FleetExecutionError, match="signature"):
        fleet_execution.verify_author_execution_receipt(without_signature, trust_policy=fx.TRUST_POLICY, outcome_sha256=ledger.V4_SHA256, row_content_sha256=row_content_sha256)


def test_build_authorship_receipt_refuses_an_unknown_signer_key() -> None:
    row_content_sha256 = "a" * 64
    forged = fx.build_author_execution_receipt(row_content_sha256, signer_key_id="unregistered-fleet-key")
    with pytest.raises(ledger.PrivateLedgerError, match="authenticity"):
        ledger.build_authorship_receipt(author_execution_receipt=forged, trust_policy=fx.TRUST_POLICY, row_content_sha256=row_content_sha256)


def test_build_authorship_receipt_refuses_a_revoked_signer_key() -> None:
    row_content_sha256 = "a" * 64
    real = fx.build_author_execution_receipt(row_content_sha256)
    revoked_policy = trust.build_test_trust_policy(fleet_execution={fx.FLEET_KEY_ID: fx.FLEET_PUBLIC_KEY_HEX}, revoked_key_ids=frozenset({fx.FLEET_KEY_ID}))
    with pytest.raises(ledger.PrivateLedgerError, match="authenticity"):
        ledger.build_authorship_receipt(author_execution_receipt=real, trust_policy=revoked_policy, row_content_sha256=row_content_sha256)


@pytest.mark.parametrize("field", ["model_family", "exact_model", "harness", "task_id", "run_nonce", "row_content_sha256", "prompt_sha256", "packet_sha256"])
def test_build_authorship_receipt_refuses_any_signed_field_mutation(field: str) -> None:
    row_content_sha256 = "a" * 64
    real = fx.build_author_execution_receipt(row_content_sha256)
    tampered = {**real, field: "tampered-value" if field not in {"prompt_sha256", "packet_sha256", "row_content_sha256"} else "f" * 64}
    with pytest.raises(ledger.PrivateLedgerError, match="authenticity"):
        ledger.build_authorship_receipt(author_execution_receipt=tampered, trust_policy=fx.TRUST_POLICY, row_content_sha256=row_content_sha256)


def test_build_review_receipt_refuses_a_review_swapped_across_a_different_authorship_receipt() -> None:
    row_content_sha256 = "a" * 64
    author_execution_receipt = fx.build_author_execution_receipt(row_content_sha256)
    authorship = ledger.build_authorship_receipt(author_execution_receipt=author_execution_receipt, trust_policy=fx.TRUST_POLICY, row_content_sha256=row_content_sha256)
    other_authorship = {**authorship, "session_id": "a-different-session"}
    reviewer_execution_receipt = fx.build_reviewer_execution_receipt(row_content_sha256, ledger.sha256_text(ledger.canonical_json(authorship)))
    with pytest.raises(ledger.PrivateLedgerError, match="authenticity"):
        ledger.build_review_receipt(authorship_receipt=other_authorship, reviewer_execution_receipt=reviewer_execution_receipt, trust_policy=fx.TRUST_POLICY, row_content_sha256=row_content_sha256)


def test_build_review_receipt_refuses_a_rubric_hash_mismatch() -> None:
    row_content_sha256 = "a" * 64
    author_execution_receipt = fx.build_author_execution_receipt(row_content_sha256)
    authorship = ledger.build_authorship_receipt(author_execution_receipt=author_execution_receipt, trust_policy=fx.TRUST_POLICY, row_content_sha256=row_content_sha256)
    authorship_receipt_sha256 = ledger.sha256_text(ledger.canonical_json(authorship))
    signed_for_one_rubric = fx.build_reviewer_execution_receipt(row_content_sha256, authorship_receipt_sha256, rubric_sha256="a" * 64)
    with pytest.raises(fleet_execution.FleetExecutionError, match="rubric"):
        fleet_execution.verify_reviewer_execution_receipt(
            signed_for_one_rubric, trust_policy=fx.TRUST_POLICY, outcome_sha256=ledger.V4_SHA256, row_content_sha256=row_content_sha256, authorship_receipt_sha256=authorship_receipt_sha256, rubric_sha256="b" * 64
        )


# --- repair 5: the signer is an execution attester, not a passthrough -----


def test_issue_execution_receipt_apis_accept_no_caller_supplied_family_or_harness() -> None:
    """Static guard: neither issuance function, nor either observation
    dataclass, exposes a keyword a caller could use to assert its own model
    family/harness -- identity is derived only from
    ``TaskExecutionState.seat_or_model``/``harness`` (PR #7662 repair 5)."""
    issue_author_params = set(inspect.signature(fleet_execution.issue_author_execution_receipt).parameters)
    issue_reviewer_params = set(inspect.signature(fleet_execution.issue_reviewer_execution_receipt).parameters)
    observation_fields = {f.name for f in dataclasses.fields(fleet_execution.AuthorExecutionObservation)} | {f.name for f in dataclasses.fields(fleet_execution.ReviewerExecutionObservation)}
    for forbidden in ("model_family", "exact_model", "harness", "author_family"):
        assert forbidden not in issue_author_params
        assert forbidden not in issue_reviewer_params
        assert forbidden not in observation_fields


def test_response_envelope_cannot_construct_complete_without_a_terminal_event() -> None:
    """The ``ResponseEnvelope`` contract itself refuses to construct a
    ``COMPLETE`` envelope with no observed terminal event -- the strongest
    possible enforcement of the advisor's terminal-event requirement."""
    with pytest.raises(ValueError, match="terminal event"):
        ResponseEnvelope(
            segments=(), completion_state=CompletionState.COMPLETE, terminal_event_observed=False, process_returncode=0, raw_capture_artifact_id="x", raw_capture_sha256="a" * 64, session_id="s"
        )


def test_issue_author_execution_receipt_refuses_a_nonterminal_task_status() -> None:
    task_state = fx.build_author_task_state(status="running")
    with pytest.raises(fleet_execution.FleetExecutionError, match="terminal successful"):
        fx.build_author_execution_receipt("a" * 64, task_state=task_state)


def test_issue_author_execution_receipt_refuses_a_nonzero_task_return_code() -> None:
    task_state = fx.build_author_task_state(return_code=1)
    with pytest.raises(fleet_execution.FleetExecutionError, match="return code"):
        fx.build_author_execution_receipt("a" * 64, task_state=task_state)


@pytest.mark.parametrize("completion_state", [CompletionState.FAILED, CompletionState.UNKNOWN, CompletionState.LENGTH_LIMITED, CompletionState.TRANSPORT_INCOMPLETE])
def test_issue_author_execution_receipt_refuses_a_non_complete_envelope(completion_state: CompletionState) -> None:
    envelope = ResponseEnvelope(
        segments=(),
        completion_state=completion_state,
        terminal_event_observed=False,
        process_returncode=0,
        raw_capture_artifact_id="fixture-author-raw-capture-002",
        raw_capture_sha256=ledger.sha256_text("fixture-author-execution-result"),
        session_id=fx.AUTHOR_SESSION_ID,
    )
    with pytest.raises(fleet_execution.FleetExecutionError, match="envelope is not complete"):
        fx.build_author_execution_receipt("a" * 64, envelope=envelope)


def test_issue_author_execution_receipt_refuses_an_unsuccessful_process_returncode() -> None:
    envelope = ResponseEnvelope(
        segments=(),
        completion_state=CompletionState.COMPLETE,
        terminal_event_observed=True,
        process_returncode=1,
        raw_capture_artifact_id="fixture-author-raw-capture-003",
        raw_capture_sha256=ledger.sha256_text("fixture-author-execution-result"),
        session_id=fx.AUTHOR_SESSION_ID,
    )
    with pytest.raises(fleet_execution.FleetExecutionError, match="process return code"):
        fx.build_author_execution_receipt("a" * 64, envelope=envelope)


def test_issue_author_execution_receipt_refuses_a_task_id_mismatch_against_the_task_state() -> None:
    with pytest.raises(fleet_execution.FleetExecutionError, match="task_id"):
        fx.build_author_execution_receipt("a" * 64, task_id="mismatched-task-id")


def test_issue_author_execution_receipt_refuses_a_run_nonce_mismatch_against_the_task_state() -> None:
    with pytest.raises(fleet_execution.FleetExecutionError, match="run_nonce"):
        fx.build_author_execution_receipt("a" * 64, run_nonce="mismatched-run-nonce")


def test_issue_author_execution_receipt_refuses_an_observed_model_mismatch_against_the_task_state() -> None:
    with pytest.raises(fleet_execution.FleetExecutionError, match="observed_model"):
        fx.build_author_execution_receipt("a" * 64, observed_model="a-different-model-entirely")


def test_issue_author_execution_receipt_refuses_an_execution_result_hash_mismatch_against_the_envelope() -> None:
    with pytest.raises(fleet_execution.FleetExecutionError, match="raw-capture digest"):
        fx.build_author_execution_receipt("a" * 64, execution_result_sha256="9" * 64)


def test_issue_author_execution_receipt_refuses_a_provider_session_id_mismatch_against_the_envelope() -> None:
    with pytest.raises(fleet_execution.FleetExecutionError, match="session_id"):
        fx.build_author_execution_receipt("a" * 64, provider_session_id="a-different-session-entirely")


def test_issue_author_execution_receipt_refuses_an_unresolvable_model_family() -> None:
    task_state = fx.build_author_task_state(seat_or_model="totally-unrecognized-seat-xyz")
    with pytest.raises(fleet_execution.FleetExecutionError, match="could not be resolved"):
        fx.build_author_execution_receipt("a" * 64, task_state=task_state)


def test_issue_author_execution_receipt_refuses_an_ambiguous_harness_seat() -> None:
    task_state = fx.build_author_task_state(seat_or_model="cursor")
    with pytest.raises(fleet_execution.FleetExecutionError, match="could not be resolved"):
        fx.build_author_execution_receipt("a" * 64, task_state=task_state)


def test_issue_author_execution_receipt_refuses_a_cursor_auto_union_family() -> None:
    task_state = fx.build_author_task_state(seat_or_model="cursor:auto")
    with pytest.raises(fleet_execution.FleetExecutionError, match="union family"):
        fx.build_author_execution_receipt("a" * 64, task_state=task_state)


def test_issue_author_execution_receipt_refuses_a_non_canonical_harness() -> None:
    task_state = fx.build_author_task_state(harness="some-made-up-harness")
    with pytest.raises(fleet_execution.FleetExecutionError, match="canonical known harness"):
        fx.build_author_execution_receipt("a" * 64, task_state=task_state)


def test_issue_author_execution_receipt_refuses_duplicate_verification_tool_ids() -> None:
    with pytest.raises(fleet_execution.FleetExecutionError, match="duplicate"):
        fx.build_author_execution_receipt("a" * 64, verification_tool_ids=("dup-tool", "dup-tool"))


def test_verify_author_execution_receipt_refuses_an_extra_signed_field_even_when_resigned() -> None:
    """The strongest form of the exact-key-set guard: even a fresh,
    correctly recomputed signature over a body carrying an extra (here,
    text-bearing) field must still refuse."""
    row_content_sha256 = "a" * 64
    real = fx.build_author_execution_receipt(row_content_sha256)
    body = {k: v for k, v in real.items() if k != "signature_hex"}
    tampered_body = {**body, "row_text": "this is real corpus text that must never be signable"}
    signature_hex = trust.sign(fx.FLEET_SIGNING_KEY_HEX, fleet_execution.AUTHOR_DOMAIN, tampered_body)
    tampered = {**tampered_body, "signature_hex": signature_hex}
    with pytest.raises(fleet_execution.FleetExecutionError, match="exactly"):
        fleet_execution.verify_author_execution_receipt(tampered, trust_policy=fx.TRUST_POLICY, outcome_sha256=ledger.V4_SHA256, row_content_sha256=row_content_sha256)


def test_verify_author_execution_receipt_refuses_an_uppercase_hex_hash_even_when_resigned() -> None:
    row_content_sha256 = "a" * 64
    real = fx.build_author_execution_receipt(row_content_sha256)
    body = {k: v for k, v in real.items() if k != "signature_hex"}
    tampered_body = {**body, "prompt_sha256": "A" * 64}
    signature_hex = trust.sign(fx.FLEET_SIGNING_KEY_HEX, fleet_execution.AUTHOR_DOMAIN, tampered_body)
    tampered = {**tampered_body, "signature_hex": signature_hex}
    with pytest.raises(fleet_execution.FleetExecutionError, match="lowercase-hex"):
        fleet_execution.verify_author_execution_receipt(tampered, trust_policy=fx.TRUST_POLICY, outcome_sha256=ledger.V4_SHA256, row_content_sha256=row_content_sha256)


def test_issue_verifier_attestation_refuses_duplicate_lookup_ids() -> None:
    with pytest.raises(sources_authority.SourcesAuthorityError, match="duplicate"):
        sources_authority.issue_verifier_attestation(
            signing_key_hex=fx.SOURCES_SIGNING_KEY_HEX,
            signer_key_id=fx.SOURCES_KEY_ID,
            outcome_sha256=ledger.V4_SHA256,
            row_content_sha256="a" * 64,
            identifier="vesum:lemma-example-001",
            tool_id="mcp__sources__verify_word",
            tool_version="v1",
            request_id="req-1",
            tool_result_sha256="b" * 64,
            lookup_ids=["dup-lookup", "dup-lookup"],
            invocation_id="inv-1",
        )


def test_verify_verifier_attestation_refuses_an_extra_field_even_when_resigned() -> None:
    attestation = sources_authority.issue_verifier_attestation(
        signing_key_hex=fx.SOURCES_SIGNING_KEY_HEX,
        signer_key_id=fx.SOURCES_KEY_ID,
        outcome_sha256=ledger.V4_SHA256,
        row_content_sha256="a" * 64,
        identifier="vesum:lemma-example-001",
        tool_id="mcp__sources__verify_word",
        tool_version="v1",
        request_id="req-1",
        tool_result_sha256="b" * 64,
        lookup_ids=["l-1"],
        invocation_id="inv-1",
    )
    body = {k: v for k, v in attestation.items() if k != "signature_hex"}
    tampered_body = {**body, "extra_note": "should never be signable"}
    signature_hex = trust.sign(fx.SOURCES_SIGNING_KEY_HEX, sources_authority.ATTESTATION_DOMAIN, tampered_body)
    tampered = {**tampered_body, "signature_hex": signature_hex}
    with pytest.raises(sources_authority.SourcesAuthorityError, match="exactly"):
        sources_authority.verify_verifier_attestation(tampered, trust_policy=fx.TRUST_POLICY, outcome_sha256=ledger.V4_SHA256, row_content_sha256="a" * 64)


def test_trust_policy_refuses_a_keyring_entry_with_an_extra_field() -> None:
    policy = trust.empty_trust_policy()
    policy["keyrings"]["fleet_execution"]["extra-key"] = {"public_key_hex": fx.FLEET_PUBLIC_KEY_HEX, "revoked": False, "note": "smuggled"}
    with pytest.raises(trust.TrustAuthorityError, match="exactly"):
        trust.validate_trust_policy(policy)


def test_trust_policy_refuses_a_non_lowercase_hex_public_key() -> None:
    policy = trust.empty_trust_policy()
    policy["keyrings"]["fleet_execution"]["bad-key"] = {"public_key_hex": "A" * 64, "revoked": False}
    with pytest.raises(trust.TrustAuthorityError, match="lowercase-hex"):
        trust.validate_trust_policy(policy)


def test_verify_refuses_an_uppercase_hex_signature() -> None:
    with pytest.raises(trust.TrustAuthorityError, match="lowercase-hex"):
        trust.verify(fx.FLEET_PUBLIC_KEY_HEX, fleet_execution.AUTHOR_DOMAIN, {"x": 1}, "A" * 128)


def test_verify_private_replay_refuses_a_same_task_run_author_and_reviewer(tmp_path: Path) -> None:
    tmp_root, info = fx.build_real_slot_root(tmp_path)
    stored_ledger = ledger.load_ledger(info["ledger_path"])
    entry = stored_ledger["entries"][fx.TARGET_SLOT_ID]
    entry["review_receipt"] = {
        **entry["review_receipt"],
        "execution_receipt": {**entry["review_receipt"]["execution_receipt"], "task_id": entry["authorship_receipt"]["execution_receipt"]["task_id"], "run_nonce": entry["authorship_receipt"]["execution_receipt"]["run_nonce"]},
    }
    with pytest.raises(ledger.PrivateLedgerError):
        ledger.verify_private_replay(info["a7_receipt"], stored_ledger, **_replay_kwargs(tmp_root, info))


def test_construct_completion_produces_a_completion_that_validates_empty_receipts_without_a_signer(tmp_path: Path) -> None:
    """Empty production completion sets continue to verify without
    requiring a signer -- the frozen 0/100/0 production state."""
    tmp_root = fx.base_fixture.build_synthetic_chain_root(tmp_path, resolved_stratum="standard_correct")
    empty_receipt = a7.build_receipt(tmp_root, a7_completions=[])
    a7.validate_receipt_independently(empty_receipt, tmp_root)
    assert empty_receipt["a7_completions"] == []


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


# --- repair B: reference-check receipt signature + replay attestation ------


def test_reference_check_signature_refuses_a_stale_receipt() -> None:
    receipt = fx.build_reference_check_receipt()
    signature, _ = fx.build_reference_check_authenticity(receipt)
    tampered_receipt = {**receipt, "passed": receipt["passed"]}  # identical content, sanity baseline
    reference_check.verify_reference_check_receipt_signature(signature, receipt=tampered_receipt, trust_policy=fx.TRUST_POLICY, outcome_sha256=ledger.V4_SHA256)  # no raise
    swapped_receipt = reference_check.build_reference_check_receipt(fx.ROW_TEXT, {**fx.REFERENCE_TEXTS, "synthetic-fixture-unit-alpha": "totally different text entirely"}, fx.A3_FIXTURE_SALT)
    with pytest.raises(reference_check.ReferenceCheckError, match="stale or altered"):
        reference_check.verify_reference_check_receipt_signature(signature, receipt=swapped_receipt, trust_policy=fx.TRUST_POLICY, outcome_sha256=ledger.V4_SHA256)


def test_replay_attestation_refuses_a_stale_attestation_over_a_swapped_receipt() -> None:
    receipt = fx.build_reference_check_receipt()
    _, attestation = fx.build_reference_check_authenticity(receipt)
    swapped_receipt = reference_check.build_reference_check_receipt(fx.ROW_TEXT, {**fx.REFERENCE_TEXTS, "synthetic-fixture-unit-alpha": "totally different text entirely"}, fx.A3_FIXTURE_SALT)
    with pytest.raises(reference_check.ReferenceCheckError, match="stale or altered"):
        reference_check.verify_replay_attestation(attestation, receipt=swapped_receipt, trust_policy=fx.TRUST_POLICY, outcome_sha256=ledger.V4_SHA256, row_content_sha256=ledger.sha256_text(fx.ROW_TEXT))


def test_replay_attestation_refuses_when_the_recomputation_does_not_match() -> None:
    """issue_replay_attestation itself must refuse to sign if the live
    recomputation from the real candidate/reference/salt does not reproduce
    the given receipt -- it can never attest a false replay."""
    receipt = fx.build_reference_check_receipt()
    with pytest.raises(reference_check.ReferenceCheckError, match="does not reproduce"):
        reference_check.issue_replay_attestation(
            signing_key_hex=fx.A3_SIGNING_KEY_HEX,
            signer_key_id=fx.A3_KEY_ID,
            candidate_text=fx.ROW_TEXT,
            reference_texts={**fx.REFERENCE_TEXTS, "synthetic-fixture-unit-alpha": "totally different text entirely"},
            salt=fx.A3_FIXTURE_SALT,
            receipt=receipt,
            outcome_sha256=ledger.V4_SHA256,
            row_content_sha256=ledger.sha256_text(fx.ROW_TEXT),
            replay_invocation_id="bad-replay",
        )


def test_replay_attestation_refuses_an_unknown_a3_signer_key() -> None:
    receipt = fx.build_reference_check_receipt()
    attestation = reference_check.issue_replay_attestation(
        signing_key_hex=fx.A3_SIGNING_KEY_HEX,
        signer_key_id="unregistered-a3-key",
        candidate_text=fx.ROW_TEXT,
        reference_texts=fx.REFERENCE_TEXTS,
        salt=fx.A3_FIXTURE_SALT,
        receipt=receipt,
        outcome_sha256=ledger.V4_SHA256,
        row_content_sha256=ledger.sha256_text(fx.ROW_TEXT),
        replay_invocation_id="r-1",
    )
    with pytest.raises(reference_check.ReferenceCheckError, match="unregistered"):
        reference_check.verify_replay_attestation(attestation, receipt=receipt, trust_policy=fx.TRUST_POLICY, outcome_sha256=ledger.V4_SHA256, row_content_sha256=ledger.sha256_text(fx.ROW_TEXT))


def test_construct_completion_refuses_a_nonempty_call_with_no_replay_attestation(tmp_path: Path) -> None:
    tmp_root = fx.base_fixture.build_synthetic_chain_root(tmp_path, resolved_stratum="standard_correct")
    sealed = fx.build_sealed_receipt_and_packet(tmp_path)
    kwargs = _real_slot_construction_kwargs(tmp_root, sealed)
    kwargs["replay_attestation"] = {}
    with pytest.raises(ledger.PrivateLedgerError, match="A3 reference-check signed authenticity failed"):
        ledger.construct_completion(**kwargs)


# --- the shared admission engine: the new helper is byte-identical at zero -


def test_assemble_receipt_from_row_receipts_matches_admit_rows_at_zero() -> None:
    assert admission.assemble_receipt_from_row_receipts(outcome_sha256=a7.V4_SHA256, row_receipts=[]) == admission.admit_rows(
        outcome_sha256=a7.V4_SHA256, rows=[]
    )
