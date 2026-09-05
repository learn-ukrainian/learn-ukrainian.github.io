"""Synthetic real-slot fixture for the v4-real-slot-mechanism PR-A acceptance
proof: builds on top of ``_v4_synthetic_chain_fixture``'s own partial-
prerequisite-eligible root (15 eligible slots in ``standard_correct``),
issues a real, live-verified A3 private builder packet naming
``CANDIDATE_UNIT_IDS`` as builder-eligible, and constructs exactly one
genuine, gate-passing A7/A8 completion using ``v4_a7_private_ledger`` --
never a hand-authored shape standing in for the real mechanism.

Every text used here is synthetic, English-safe placeholder content, never
real Ukrainian corpus text and never anything resembling production
material -- this fixture proves the *mechanism*, not a real row. Production
stays untouched: nothing here ever writes outside ``tmp_path``.

Repair (PR #7662, repair 2): the split/near-duplicate and reconstruction-
gate comparison against reference text is now A3-owned
(``v4_a3_reference_check``) -- this fixture builds that receipt directly
(simulating the A3 role, which privately holds ``REFERENCE_TEXTS``) and
passes only the resulting text-free receipt into
``v4_a7_private_ledger.construct_completion``. A real A3 seal receipt and
private builder packet are issued here too (``build_sealed_receipt_and_
packet``), over a test-only salt, with ``CANDIDATE_UNIT_IDS`` registered as
members of a builder-eligible family and ``HELDOUT_SENTINEL_UNIT_ID``
registered as a member of that salt's held-out family -- so a tamper test
can prove an ineligible/held-out unit is refused before row construction.

Repair (PR #7662, repair 4 -- designated-advisor ``GO_REPAIR``): this
fixture now also plays every distinct signing authority role the trust
boundary requires, each with its own ephemeral Ed25519 keypair generated
fresh under this process (never a production key):

* the sources execution authority (``v4_sources_authority``), signing the
  one verifier attestation behind ``AUTHOR``/``REVIEWER``'s evidence;
* the A3 authority (``v4_a3_reference_check``), signing both the reference-
  check receipt signature and the mandatory replay attestation;
* the fleet execution attester (``v4_fleet_execution_authority``), signing
  the author/reviewer execution receipts ``construct_completion`` now
  requires instead of raw caller dictionaries.

All three public keys are assembled into one explicit, unmistakably
test-only trust policy (``TRUST_POLICY``, via
``v4_trust_authority.build_test_trust_policy``) -- never reachable from any
default production code path. ``RIGHTS_RECEIPT_ID`` is the real value
derived from repository-root ``LICENSE-CONTENT.md`` (see
``v4_a7_private_ledger.derive_project_rights_receipt_id``), not a
placeholder -- ``ZERO_RIGHTS_RECEIPT_ID`` is kept as the explicit negative
tamper case.

Repair (PR #7662, repair 5 -- accountable-review blocker): the fleet
execution attester now consumes a trusted execution *observation* rather
than caller-asserted identity keywords. ``build_author_task_state``/
``build_reviewer_task_state`` build a synthetic, terminal
``fleet_execution.TaskExecutionState`` (task/run/session id, ``status:
"done"``, a zero return code, and an exact seat/model string that resolves
-- via the canonical cross-family resolver -- to a distinct concrete family
per role); ``build_terminal_envelope`` builds the matching typed
``ResponseEnvelope`` (``CompletionState.COMPLETE``, an observed terminal
event, a zero process return code, and the raw-capture digest the
observation's ``execution_result_sha256`` must equal).
``build_author_execution_receipt``/``build_reviewer_execution_receipt``
assemble the role-specific structured observation from those two plus this
fixture's own hashes and call ``issue_*_execution_receipt`` -- never the
retired keyword-only signature.

Repair (PR #7662 repair 6 -- operator-approved canonical-authority
architecture): production's ``issue_author_execution_receipt``/``issue_
reviewer_execution_receipt``/``issue_verifier_attestation``/``sign_
reference_check_receipt``/``issue_replay_attestation`` now accept opaque
IDs only and resolve/load everything else (evidence, signing key, trust-
policy digest) internally. This fixture is not production: it plays each
distinct signing-authority role directly, with its own ephemeral test keys
and a synthetic trust-policy digest it computes itself
(``TRUST_POLICY_SHA256``), so it calls each module's private, unchanged
signing *engine* (``_issue_author_receipt_from_evidence``, ``_issue_
reviewer_receipt_from_evidence``, ``_issue_verifier_attestation_from_
evidence``, ``_sign_reference_check_receipt_from_evidence``, ``_issue_
replay_attestation_from_evidence``) directly -- exercising the identical
validation/signing logic the production wrappers delegate to, never a
production bypass. Evidence is always verifier-backed and
``production_capable`` here (``build_verifier_backed_evidence_receipt``) --
``construct_completion`` has no synthetic-admission switch to opt out with.
"""

from __future__ import annotations

import copy
import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import patch

import _v4_synthetic_chain_fixture as base_fixture

from scripts.fleet_comms.contracts import CompletionState, ResponseEnvelope
from scripts.projects.open_model_data import v4_a3_builder_packet as packet
from scripts.projects.open_model_data import v4_a3_heldout_family_assignment as heldout
from scripts.projects.open_model_data import v4_a3_reference_check as reference_check
from scripts.projects.open_model_data import v4_a7_evidence_binder as evidence_binder
from scripts.projects.open_model_data import v4_a7_original_row_factory as a7
from scripts.projects.open_model_data import v4_a7_private_ledger as ledger
from scripts.projects.open_model_data import v4_a8_admission_assembly as a8
from scripts.projects.open_model_data import v4_fleet_execution_authority as fleet_execution
from scripts.projects.open_model_data import v4_sources_authority as sources_authority
from scripts.projects.open_model_data import v4_trust_authority as trust

ROOT = Path(__file__).resolve().parents[3]

# A7's own private slot-unit-pick/lineage salt (construct_completion's own
# ``salt`` argument) -- unrelated to, and never derived from, A3's
# membership/packet salt below.
TEST_SALT = bytes.fromhex("ab" * 32)

# A3's private membership/packet salt for this fixture only -- never the
# real production salt. Chosen (see PR body / repair notes) so that
# ELIGIBLE_FAMILY_ID is builder-eligible and HELDOUT_FAMILY_ID is held out
# for the real 9-family production family registry.
A3_FIXTURE_SALT_HEX = "cd" * 32
A3_FIXTURE_SALT = bytes.fromhex(A3_FIXTURE_SALT_HEX)
ELIGIBLE_FAMILY_ID = "fam-db-textbooks-public"
HELDOUT_FAMILY_ID = "fam-db-external-articles"

TARGET_SLOT_ID = "v4p-standard-correct-001"
CANDIDATE_UNIT_IDS = ["synthetic-fixture-unit-alpha", "synthetic-fixture-unit-beta"]
HELDOUT_SENTINEL_UNIT_ID = "synthetic-fixture-unit-heldout-sentinel"

ROW_TEXT = "This is a synthetic, independently authored placeholder sentence used only to exercise the V4 A7 mechanism."
REFERENCE_TEXTS = {
    "synthetic-fixture-unit-alpha": "A completely different placeholder passage about an unrelated everyday topic entirely.",
    "synthetic-fixture-unit-beta": "Another unrelated placeholder passage, deliberately dissimilar in wording and structure.",
}
VESUM_IDS = ["vesum:lemma-synthetic-example-001", "sources:fixture-attestation-001"]

RIGHTS_RECEIPT_ID = ledger.derive_project_rights_receipt_id()
ZERO_RIGHTS_RECEIPT_ID = "license.content.cc-by-sa-4.0@0000000000000000000000000000000000000000000000000000000000000000"

# --- test-only trust authority keypairs (PR #7662 repair 4) ----------------
#
# One ephemeral Ed25519 keypair per distinct signing authority, generated
# fresh in this process -- never a production key, never persisted.
SOURCES_SIGNING_KEY_HEX, SOURCES_PUBLIC_KEY_HEX = trust.generate_test_keypair()
A3_SIGNING_KEY_HEX, A3_PUBLIC_KEY_HEX = trust.generate_test_keypair()
FLEET_SIGNING_KEY_HEX, FLEET_PUBLIC_KEY_HEX = trust.generate_test_keypair()
SOURCES_KEY_ID = "fixture-sources-key-1"
A3_KEY_ID = "fixture-a3-key-1"
FLEET_KEY_ID = "fixture-fleet-execution-key-1"

TRUST_POLICY = trust.build_test_trust_policy(
    sources={SOURCES_KEY_ID: SOURCES_PUBLIC_KEY_HEX},
    a3={A3_KEY_ID: A3_PUBLIC_KEY_HEX},
    fleet_execution={FLEET_KEY_ID: FLEET_PUBLIC_KEY_HEX},
)
# The digest every signed body this fixture issues binds as
# ``trust_policy_sha256`` -- computed the identical way production does
# (``v4_trust_authority.trust_policy_sha256``), just over this test-only
# policy dict instead of the checked-in production file.
TRUST_POLICY_SHA256 = trust.trust_policy_sha256(TRUST_POLICY)


@contextmanager
def installed_fixture_policy():
    """Isolated test-policy seam: cannot serve production admission."""
    with patch.object(trust, "load_production_trust_policy", lambda: (TRUST_POLICY, TRUST_POLICY_SHA256)):
        yield

AUTHOR_TASK_ID = "fixture-author-task-001"
AUTHOR_RUN_NONCE = "fixture-author-run-nonce-001"
REVIEWER_TASK_ID = "fixture-reviewer-task-001"
REVIEWER_RUN_NONCE = "fixture-reviewer-run-nonce-001"

# PR #7662 repair 5: the attester derives model_family/exact_model/harness
# from authoritative task/runtime evidence alone -- these are the exact
# runtime-resolved seat/model strings and canonical harness executables the
# fixture's own synthetic terminal task-state attests to. "claude"/"codex"
# are both members of the project's canonical known-harness allowlist
# (``scripts.orchestration.thread_handoff.KNOWN_HARNESS_EXECUTABLES``); the
# seat strings resolve, via the canonical cross-family resolver, to two
# distinct concrete families (anthropic vs. openai) -- never the same table
# twice, never a caller-asserted family string.
AUTHOR_SEAT_OR_MODEL = "claude-sonnet-5-fixture-author"
AUTHOR_HARNESS = "claude"
AUTHOR_SESSION_ID = "fixture-author-session-001"
REVIEWER_SEAT_OR_MODEL = "gpt-5.6-fixture-reviewer"
REVIEWER_HARNESS = "codex"
REVIEWER_SESSION_ID = "fixture-reviewer-session-001"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def a4_unit_commitments(tmp_root: Path) -> list[str]:
    a4_receipt = _load(tmp_root / "data/projects/open_model_data/admission/dataset_v4_a4_deterministic_extraction_receipt_v1.json")
    return a4_receipt["builder_packet_consumption"]["unit_commitments"]


def build_sealed_receipt_and_packet(tmp_path: Path) -> dict[str, Any]:
    """A real, schema-conformant, freshly-sealed A3 receipt over the real
    9-family production registry (deep-copied, never the real private
    membership/salt), with ``CANDIDATE_UNIT_IDS`` added as members of
    ``ELIGIBLE_FAMILY_ID`` and ``HELDOUT_SENTINEL_UNIT_ID`` added as a
    member of ``HELDOUT_FAMILY_ID``, plus a real, live-issued private
    builder packet over it. Returns the paths a privileged caller (A7's
    private ledger) needs to independently re-verify the packet."""
    real_receipt = json.loads((ROOT / heldout.DEFAULT_RECEIPT.relative_to(ROOT)).read_text(encoding="utf-8"))
    receipt = copy.deepcopy(real_receipt)
    for family in receipt["source_family_registry"]["families"]:
        if family["family_id"] == ELIGIBLE_FAMILY_ID:
            family["member_source_unit_ids"] = sorted({*family["member_source_unit_ids"], *CANDIDATE_UNIT_IDS})
        if family["family_id"] == HELDOUT_FAMILY_ID:
            family["member_source_unit_ids"] = sorted({*family["member_source_unit_ids"], HELDOUT_SENTINEL_UNIT_ID})

    private_dir = tmp_path / "v4-a3-heldout-fixture"
    family_ids = sorted(f["family_id"] for f in receipt["source_family_registry"]["families"])

    os.environ[heldout.TEST_SALT_ENV_VAR] = A3_FIXTURE_SALT_HEX
    try:
        result = heldout.assign(A3_FIXTURE_SALT, family_ids)
        assert ELIGIBLE_FAMILY_ID in result["builder_eligible_family_ids"]
        assert HELDOUT_FAMILY_ID in result["heldout_family_ids"]
        summary = heldout.public_commitment_summary(A3_FIXTURE_SALT, result)
        receipt["heldout_partition_seal"]["assignment_algorithm"]["salt_commitment_sha256"] = summary["salt_commitment_sha256"]
        receipt["heldout_partition_seal"]["assignment_algorithm"]["assignment_commitment_sha256"] = summary["assignment_commitment_sha256"]
        heldout.write_private_artifact(private_dir / heldout.MEMBERSHIP_FILENAME, A3_FIXTURE_SALT, result, heldout.receipt_binding_sha256(receipt))
    finally:
        del os.environ[heldout.TEST_SALT_ENV_VAR]

    seal_receipt_path = tmp_path / "v4_a3_seal_receipt_fixture.json"
    seal_receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    packet.issue_packet(seal_receipt_path, private_dir, private_dir)

    return {"seal_receipt_path": seal_receipt_path, "membership_dir": private_dir, "packet_dir": private_dir, "seal_receipt": receipt}


def build_reference_check_receipt(row_text: str = ROW_TEXT, reference_texts: dict[str, str] | None = None) -> dict[str, Any]:
    """Simulates the A3 role: builds the text-free reference-check receipt
    from the (here, synthetic) private reference-text set -- the only thing
    A7's construction API ever receives from this comparison."""
    return reference_check.build_reference_check_receipt(row_text, dict(reference_texts if reference_texts is not None else REFERENCE_TEXTS), A3_FIXTURE_SALT)


def build_reference_check_authenticity(
    receipt: dict[str, Any], *, row_text: str = ROW_TEXT, reference_texts: dict[str, str] | None = None, replay_invocation_id: str = "fixture-a3-replay-001"
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Simulates the A3 authority: signs ``receipt`` and issues the
    mandatory replay attestation, both under the fixture's own ephemeral A3
    key (PR #7662 repair 4, repair B)."""
    signature = reference_check._sign_reference_check_receipt_from_evidence(
        signing_key_hex=A3_SIGNING_KEY_HEX, signer_key_id=A3_KEY_ID, receipt=receipt, outcome_sha256=ledger.V4_SHA256, trust_policy_sha256=TRUST_POLICY_SHA256
    )
    attestation = reference_check._issue_replay_attestation_from_evidence(
        signing_key_hex=A3_SIGNING_KEY_HEX,
        signer_key_id=A3_KEY_ID,
        candidate_text=row_text,
        reference_texts=dict(reference_texts if reference_texts is not None else REFERENCE_TEXTS),
        salt=A3_FIXTURE_SALT,
        receipt=receipt,
        outcome_sha256=ledger.V4_SHA256,
        row_content_sha256=ledger.sha256_text(row_text),
        replay_invocation_id=replay_invocation_id,
        trust_policy_sha256=TRUST_POLICY_SHA256,
    )
    return signature, attestation


def build_verifier_backed_evidence_receipt(row_content_sha256: str, *, vesum_ids: list[str] | None = None) -> dict[str, Any]:
    """Simulates the distinct sources execution authority: issues one
    signed verifier attestation per identifier and wraps each into a
    production-capable verifier receipt (PR #7662 repair 4, repair A)."""
    with installed_fixture_policy():
        identifiers = list(vesum_ids if vesum_ids is not None else VESUM_IDS)
        verifier_receipts = []
        for index, identifier in enumerate(identifiers):
            attestation = sources_authority._issue_verifier_attestation_from_evidence(
                signing_key_hex=SOURCES_SIGNING_KEY_HEX,
                signer_key_id=SOURCES_KEY_ID,
                outcome_sha256=ledger.V4_SHA256,
                row_content_sha256=row_content_sha256,
                identifier=identifier,
                tool_id="mcp__sources__verify_word",
                tool_version="v1",
                request_id=f"fixture-request-{index}",
                tool_result_sha256=ledger.sha256_text(f"fixture-tool-result-{index}"),
                lookup_ids=[f"fixture-lookup-{index}"],
                invocation_id=f"fixture-invocation-{index}",
                trust_policy_sha256=TRUST_POLICY_SHA256,
            )
            verifier_receipts.append(evidence_binder.build_verifier_receipt(attestation=attestation))
        return evidence_binder.build_evidence_receipt(row_content_sha256, verifier_receipts)


def build_synthetic_fixture_evidence_receipt(row_content_sha256: str, vesum_ids: list[str], *, uncertainty: str = "resolved") -> dict[str, Any]:
    """Test-only evidence (PR #7662 repair 6, Sol synthetic-separation
    requirement -- moved out of production ``v4_a7_evidence_binder``):
    shape-checked identifiers with no bound verifier receipt. Always
    ``production_capable: False`` and ``evidence_source: "synthetic_
    fixture"`` -- ``grade`` stays ``"verified"`` only for the shared
    admission engine's own required shape, never as a claim of real
    verification. ``v4_a7_private_ledger.construct_completion`` has no
    parameter that could ever accept a receipt built by this function --
    only tests exercising the lower-level gates directly (never
    ``construct_completion`` itself) use it."""
    evidence_binder.require(isinstance(vesum_ids, list) and bool(vesum_ids), "vesum_ids must be a nonempty list")
    evidence_binder.require(len(vesum_ids) == len(set(vesum_ids)), "vesum_ids must not contain duplicates")
    for identifier in vesum_ids:
        evidence_binder.require(evidence_binder.verify_identifier_shape(identifier), f"identifier does not match the pinned VESUM/sources shape: {identifier!r}")
    evidence_binder.require(uncertainty in {"resolved", "bounded"}, "uncertainty must be resolved or bounded")

    payload = {
        "row_content_sha256": row_content_sha256,
        "uncertainty": uncertainty,
        "vesum_ids": sorted(vesum_ids),
        "verifier_receipts": [],
        "evidence_source": "synthetic_fixture",
        "production_capable": False,
        "grade": "verified",
        "disposition": "supported",
    }
    receipt_id = f"evidence-synthetic-fixture:{ledger.sha256_text(ledger.canonical_json(payload))}"
    return {**payload, "receipt_id": receipt_id}


def build_author_task_state(
    *,
    task_id: str = AUTHOR_TASK_ID,
    run_nonce: str = AUTHOR_RUN_NONCE,
    session_id: str | None = AUTHOR_SESSION_ID,
    seat_or_model: str = AUTHOR_SEAT_OR_MODEL,
    harness: str = AUTHOR_HARNESS,
    status: str = "done",
    return_code: int = 0,
) -> fleet_execution.TaskExecutionState:
    return fleet_execution.TaskExecutionState(task_id=task_id, run_nonce=run_nonce, status=status, return_code=return_code, seat_or_model=seat_or_model, harness=harness, session_id=session_id)


def build_reviewer_task_state(
    *,
    task_id: str = REVIEWER_TASK_ID,
    run_nonce: str = REVIEWER_RUN_NONCE,
    session_id: str | None = REVIEWER_SESSION_ID,
    seat_or_model: str = REVIEWER_SEAT_OR_MODEL,
    harness: str = REVIEWER_HARNESS,
    status: str = "done",
    return_code: int = 0,
) -> fleet_execution.TaskExecutionState:
    return fleet_execution.TaskExecutionState(task_id=task_id, run_nonce=run_nonce, status=status, return_code=return_code, seat_or_model=seat_or_model, harness=harness, session_id=session_id)


def build_terminal_envelope(*, raw_capture_sha256: str, session_id: str, raw_capture_artifact_id: str) -> ResponseEnvelope:
    """A synthetic, terminally-complete ``ResponseEnvelope`` -- the shared
    transport-neutral completion contract (``scripts.fleet_comms.contracts``)
    the attester requires alongside authoritative task-state evidence before
    it will ever sign (PR #7662 repair 5)."""
    return ResponseEnvelope(
        segments=(),
        completion_state=CompletionState.COMPLETE,
        terminal_event_observed=True,
        process_returncode=0,
        raw_capture_artifact_id=raw_capture_artifact_id,
        raw_capture_sha256=raw_capture_sha256,
        session_id=session_id,
    )


def build_author_execution_receipt(
    row_content_sha256: str,
    *,
    prompt_sha256: str = "1" * 64,
    packet_sha256: str = "2" * 64,
    task_state: fleet_execution.TaskExecutionState | None = None,
    envelope: ResponseEnvelope | None = None,
    signing_key_hex: str = FLEET_SIGNING_KEY_HEX,
    signer_key_id: str = FLEET_KEY_ID,
    **observation_overrides: Any,
) -> dict[str, Any]:
    execution_result_sha256 = ledger.sha256_text("fixture-author-execution-result")
    resolved_task_state = task_state if task_state is not None else build_author_task_state()
    resolved_envelope = envelope if envelope is not None else build_terminal_envelope(raw_capture_sha256=execution_result_sha256, session_id=AUTHOR_SESSION_ID, raw_capture_artifact_id="fixture-author-raw-capture-001")
    from learn_ukrainian_v4_runtime.provenance import verify_current_identity

    observation_kwargs: dict[str, Any] = {
        "runtime_identity": {**verify_current_identity(), "wheel_sha256": "f" * 64},
        "task_id": resolved_task_state.task_id,
        "run_nonce": resolved_task_state.run_nonce,
        "observed_model": resolved_task_state.seat_or_model,
        "row_content_sha256": row_content_sha256,
        "prompt_sha256": prompt_sha256,
        "packet_sha256": packet_sha256,
        "execution_result_sha256": execution_result_sha256,
        "fleet_receipt_sha256": ledger.sha256_text("fixture-author-fleet-receipt"),
        "provider_session_id": resolved_envelope.session_id,
        "verification_tool_ids": ("fixture-tool-1",),
    }
    observation_kwargs.update(observation_overrides)
    observation = fleet_execution.AuthorExecutionObservation(**observation_kwargs)
    return fleet_execution._issue_author_receipt_from_evidence(
        signing_key_hex=signing_key_hex,
        signer_key_id=signer_key_id,
        outcome_sha256=ledger.V4_SHA256,
        task_state=resolved_task_state,
        envelope=resolved_envelope,
        observation=observation,
        issuance_nonce="fixture-author-issuance-nonce-001",
        trust_policy_sha256=TRUST_POLICY_SHA256,
    )


def build_reviewer_execution_receipt(
    row_content_sha256: str,
    authorship_receipt_sha256: str,
    *,
    rubric_sha256: str = "5" * 64,
    verdict: str = "PASS",
    prompt_sha256: str = "3" * 64,
    packet_sha256: str = "4" * 64,
    task_state: fleet_execution.TaskExecutionState | None = None,
    envelope: ResponseEnvelope | None = None,
    signing_key_hex: str = FLEET_SIGNING_KEY_HEX,
    signer_key_id: str = FLEET_KEY_ID,
    **observation_overrides: Any,
) -> dict[str, Any]:
    execution_result_sha256 = ledger.sha256_text("fixture-reviewer-execution-result")
    resolved_task_state = task_state if task_state is not None else build_reviewer_task_state()
    resolved_envelope = envelope if envelope is not None else build_terminal_envelope(raw_capture_sha256=execution_result_sha256, session_id=REVIEWER_SESSION_ID, raw_capture_artifact_id="fixture-reviewer-raw-capture-001")
    from learn_ukrainian_v4_runtime.provenance import verify_current_identity

    observation_kwargs: dict[str, Any] = {
        "runtime_identity": {**verify_current_identity(), "wheel_sha256": "f" * 64},
        "task_id": resolved_task_state.task_id,
        "run_nonce": resolved_task_state.run_nonce,
        "observed_model": resolved_task_state.seat_or_model,
        "row_content_sha256": row_content_sha256,
        "prompt_sha256": prompt_sha256,
        "packet_sha256": packet_sha256,
        "execution_result_sha256": execution_result_sha256,
        "fleet_receipt_sha256": ledger.sha256_text("fixture-reviewer-fleet-receipt"),
        "authorship_receipt_sha256": authorship_receipt_sha256,
        "rubric_sha256": rubric_sha256,
        "verdict": verdict,
        "provider_session_id": resolved_envelope.session_id,
        "verification_tool_ids": ("fixture-tool-2",),
    }
    observation_kwargs.update(observation_overrides)
    observation = fleet_execution.ReviewerExecutionObservation(**observation_kwargs)
    return fleet_execution._issue_reviewer_receipt_from_evidence(
        signing_key_hex=signing_key_hex,
        signer_key_id=signer_key_id,
        outcome_sha256=ledger.V4_SHA256,
        task_state=resolved_task_state,
        envelope=resolved_envelope,
        observation=observation,
        issuance_nonce="fixture-reviewer-issuance-nonce-001",
        trust_policy_sha256=TRUST_POLICY_SHA256,
    )


def build_completion(
    tmp_root: Path,
    sealed: dict[str, Any],
    *,
    slot_id: str = TARGET_SLOT_ID,
    salt: bytes = TEST_SALT,
    candidate_unit_ids: list[str] | None = None,
    row_text: str = ROW_TEXT,
    reference_texts: dict[str, str] | None = None,
    rights_receipt_id: str = RIGHTS_RECEIPT_ID,
) -> dict[str, Any]:
    """Run the real, live ``v4_a7_private_ledger.construct_completion``
    pipeline -- every gate genuinely evaluated -- and return
    ``{"private_entry", "public_completion"}``. ``construct_completion`` has
    no synthetic-admission switch (PR #7662 repair 6): evidence is always a
    real, verifier-backed, ``production_capable`` receipt
    (``build_verifier_backed_evidence_receipt``), signed here under the
    fixture's own ephemeral "sources" test key. Every signed authenticity
    artifact (repair A/B/E/6) is built fresh here under the fixture's own
    ephemeral keys."""
    with installed_fixture_policy():
        row_content_sha256 = ledger.sha256_text(row_text)
        evidence_receipt = build_verifier_backed_evidence_receipt(row_content_sha256)
        reference_check_receipt = build_reference_check_receipt(row_text, reference_texts)
        reference_check_signature, replay_attestation = build_reference_check_authenticity(reference_check_receipt, row_text=row_text, reference_texts=reference_texts)

        author_execution_receipt = build_author_execution_receipt(row_content_sha256)
        provisional_authorship_receipt = ledger.build_authorship_receipt(author_execution_receipt=author_execution_receipt, row_content_sha256=row_content_sha256)
        authorship_receipt_sha256 = ledger.sha256_text(ledger.canonical_json(provisional_authorship_receipt))
        reviewer_execution_receipt = build_reviewer_execution_receipt(row_content_sha256, authorship_receipt_sha256)

        manifest = _load(tmp_root / "data/projects/open_model_data/admission/dataset_v4_pilot_slot_manifest_v1.json")
        a2_receipt = _load(tmp_root / "data/projects/open_model_data/admission/dataset_v4_a2_source_operation_admission_receipt_v1.json")

        return ledger.construct_completion(
            slot_id=slot_id,
            salt=salt,
            candidate_unit_ids=list(candidate_unit_ids or CANDIDATE_UNIT_IDS),
            a4_unit_commitments=a4_unit_commitments(tmp_root),
            seal_receipt_path=sealed["seal_receipt_path"],
            membership_dir=sealed["membership_dir"],
            packet_dir=sealed["packet_dir"],
            manifest=manifest,
            a2_receipt=a2_receipt,
            row_text=row_text,
            tier="silver",
            author_execution_receipt=author_execution_receipt,
            reviewer_execution_receipt=reviewer_execution_receipt,
            evidence_receipt=evidence_receipt,
            reference_check_receipt=reference_check_receipt,
            reference_check_signature=reference_check_signature,
            replay_attestation=replay_attestation,
            rights_receipt_id=rights_receipt_id,
        )


def build_real_slot_root(tmp_path: Path) -> tuple[Path, dict[str, Any]]:
    """Builds the synthetic partial-eligibility root (15 eligible slots in
    ``standard_correct``), issues a real A3 builder packet, constructs one
    genuine completion for ``TARGET_SLOT_ID``, writes the private ledger,
    and writes real A6/A7/A8 receipts (A9 untouched, still zero
    completions) via each stage's own live ``build_receipt``. Returns
    ``(tmp_root, info)``."""
    tmp_root = base_fixture.build_synthetic_chain_root(tmp_path, resolved_stratum="standard_correct")
    admission_dir = tmp_root / "data/projects/open_model_data/admission"
    sealed = build_sealed_receipt_and_packet(tmp_path)

    from scripts.projects.open_model_data import v4_a6_blind_arena as a6

    a6_receipt = a6.build_receipt(tmp_root)
    a6.validate_receipt_independently(a6_receipt, tmp_root)
    (admission_dir / "dataset_v4_a6_blind_arena_receipt_v1.json").write_text(json.dumps(a6_receipt))

    completion = build_completion(tmp_root, sealed)
    public_completion = completion["public_completion"]

    ledger_path = tmp_path / "batch_state/open-model-data/v4-a7-factory/v4_a7_private_ledger_v1.json"
    ledger.write_ledger({public_completion["slot_id"]: completion["private_entry"]}, ledger_path)

    a7_receipt = a7.build_receipt(tmp_root, a7_completions=[public_completion])
    a7.validate_receipt_independently(a7_receipt, tmp_root)
    (admission_dir / "dataset_v4_a7_original_row_factory_receipt_v1.json").write_text(json.dumps(a7_receipt))

    a8_completion = {
        "stage": "A8",
        "slot_id": public_completion["slot_id"],
        "row_id": public_completion["row_id"],
        "row_content_sha256": public_completion["row_content_sha256"],
        "trust_policy_sha256": public_completion.get("trust_policy_sha256"),
    }
    a8_receipt = a8.build_receipt(tmp_root, a8_completions=[a8_completion])
    a8.validate_receipt_independently(a8_receipt, tmp_root)
    (admission_dir / "dataset_v4_a8_admission_assembly_receipt_v1.json").write_text(json.dumps(a8_receipt))

    from scripts.projects.open_model_data import v4_a9_evaluation_package as a9

    a9_receipt = a9.build_receipt(tmp_root)
    a9.validate_receipt_independently(a9_receipt, tmp_root)
    (admission_dir / "dataset_v4_a9_evaluation_package_receipt_v1.json").write_text(json.dumps(a9_receipt))

    return tmp_root, {
        "completion": completion,
        "a6_receipt": a6_receipt,
        "a7_receipt": a7_receipt,
        "a8_receipt": a8_receipt,
        "a9_receipt": a9_receipt,
        "ledger_path": ledger_path,
        "sealed": sealed,
    }
