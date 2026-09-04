#!/usr/bin/env python3
"""V4 A3 reference-check receipt: the one place a candidate independently-
authored row is compared against *every* candidate-family's private
reference text -- split/near-duplicate safety and all five reconstruction
gates together -- and the one place that comparison ever touches held-out-
adjacent source text at all.

Repair (PR #7662, repair 2, P1 "A7 directly receives the all-family
reference texts"): the advisor assigned the all-nine-unit split/near-
duplicate check to A3, not A7, and required it to emit a text-free receipt.
Before this module existed, ``v4_a7_private_ledger.construct_completion``
ran this comparison itself, which meant A7's own construction process
received every candidate-family's raw reference text directly -- exactly
the held-out/source-text exposure the advisor's role split forbids. This
module is now the *only* place ``reference_texts`` (raw text) is ever
passed as a Python value; A7 (``v4_a7_private_ledger.py``,
``v4_a7_evidence_binder.py``, and the A7 construction API) never accepts or
stores ``reference_texts`` again -- it receives only the text-free receipt
this module produces.

Two entry points, one owner:

* ``build_reference_check_receipt`` -- run live (in the A3 role, wherever
  the private reference text actually lives) against the candidate text and
  the full reference-text set. Returns a text-free receipt: gate booleans,
  each gate's own deterministic receipt_id, a policy fingerprint, a
  one-way candidate fingerprint (never the candidate text itself), and a
  salted, keyed commitment over the *actual content* of the reference set
  (not just its size -- see ``reference_set_commitment_sha256``).
* ``verify_reference_check_receipt`` -- the A3-role replay command: rebuild
  the receipt from the same raw candidate text, reference-text set, and
  salt, and require it to reproduce the stored receipt byte for byte. This
  is the sanctioned way anything downstream (A7's private ledger) proves a
  stored reference-check receipt is genuine rather than hand-fabricated --
  it requires the same private material A3 already holds, so it can only
  ever run in the A3 role, never inside A7's own construction process.

Reuses (never reimplements) the sealed near-duplicate policy and its
deterministic implementation (``phase3_near_duplicate.py``) and A3's own
``v4_a3_split_duplicate_check`` for the split/near-duplicate half. This
module adds no new similarity algorithm -- only the reconstruction-gate
math (moved here, unchanged, from the former
``v4_a7_evidence_binder.run_reconstruction_gates``) and the receipt/
commitment shape that keeps every field text-free.

No live corpus or model call happens here, and this module is exercised in
this PR only against synthetic, caller-supplied reference texts -- never
real corpus or held-out text.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

from scripts.projects.open_model_data import phase3_near_duplicate as near_duplicate
from scripts.projects.open_model_data import v4_a3_split_duplicate_check as split_check
from scripts.projects.open_model_data import v4_original_row_admission as admission
from scripts.projects.open_model_data import v4_trust_authority as trust

RECONSTRUCTION_GATES = admission.RECONSTRUCTION_GATES

# --- signed authenticity (PR #7662 repair 4, blocking repair B) -------------
#
# Two distinct signed artifacts, both issued only by the A3 authority (which
# alone holds the real reference-text set, salt, and A3 keyring key):
#
# * a receipt *signature* -- proves this exact reference_check_receipt was
#   produced by A3, without re-running anything;
# * a replay *attestation* -- proves A3 has *also* independently
#   recomputed the receipt live from the real candidate text, reference-text
#   set, salt, and policy, and it reproduced byte for byte. Bound to the
#   receipt's own digest, so it goes stale the instant the receipt changes.
#
# Both are mandatory (no ``None`` success path) for every nonempty
# completion in ``v4_a7_private_ledger.construct_completion``/
# ``verify_private_replay``.
RECEIPT_SIGNATURE_SCHEMA_VERSION = "v4-a3-reference-check-signature-v1"
RECEIPT_SIGNATURE_DOMAIN = b"v4-a3-reference-check-signature-v1"
REPLAY_ATTESTATION_SCHEMA_VERSION = "v4-a3-replay-attestation-v1"
REPLAY_ATTESTATION_DOMAIN = b"v4-a3-replay-attestation-v1"

# A stricter band than the near-duplicate policy's own 0.9 near-duplicate
# minimum -- deliberately lower, so "structural" catches shorter shared
# skeletons the near-duplicate check alone would pass.
STRUCTURAL_SIMILARITY_THRESHOLD = 0.6

# Domain separation for the reference-set content commitment -- distinct
# from every other private-salt use in this project (see
# v4_a3_heldout_family_assignment.ASSIGNMENT_COMMITMENT_DOMAIN,
# v4_a3_builder_packet.PACKET_COMMITMENT_DOMAIN/ELIGIBLE_UNITS_COMMITMENT_DOMAIN,
# v4_a7_private_ledger.SLOT_UNIT_PICK_DOMAIN/LINEAGE_ID_DOMAIN). Reproducing
# this commitment still requires the same private salt, but it can never be
# confused with, or reduced to, a different keyed digest over that secret.
REFERENCE_SET_COMMITMENT_DOMAIN = b"v4-a3-reference-set-commitment-v1"


class ReferenceCheckError(ValueError):
    """A reference-check receipt cannot be built or verified safely."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReferenceCheckError(message)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _gate_receipt_id(gate: str, candidate_fingerprint: str, policy_fingerprint: str) -> str:
    payload = f"v4-a3-reconstruction-gate-v1\x00{gate}\x00{candidate_fingerprint}\x00{policy_fingerprint}"
    return f"reconstruction-gate:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"


def _structural_pass(candidate: str, reference_texts: list[str], policy: dict[str, Any]) -> bool:
    for reference in reference_texts:
        result = near_duplicate.classify_texts(candidate, reference, scope="span", policy=policy)
        if result.token_jaccard >= STRUCTURAL_SIMILARITY_THRESHOLD or result.normalized_edit_similarity >= STRUCTURAL_SIMILARITY_THRESHOLD:
            return False
    return True


def _run_reconstruction_gates(candidate_text: str, reference_texts: dict[str, str], policy: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Run all five reconstruction gates against *every* reference text --
    never just one candidate-ledger-bound unit. Fails closed on an empty
    reference set (see ``check_split_duplicate_safety`` for the identical
    rationale)."""
    references = list(reference_texts.values())

    exact_pass = all(near_duplicate.classify_texts(candidate_text, reference, scope="span", policy=policy).classification != "exact" for reference in references)
    fuzzy_pass = all(not near_duplicate.classify_texts(candidate_text, reference, scope="span", policy=policy).duplicate for reference in references)
    structural_pass = _structural_pass(candidate_text, references, policy)
    cumulative_reference = "\n".join(references)
    cumulative_pass = not near_duplicate.classify_texts(candidate_text, cumulative_reference, scope="span", policy=policy).duplicate
    normalized_candidate = near_duplicate.normalize(candidate_text)
    no_verbatim_containment = all(
        normalized_candidate not in near_duplicate.normalize(reference) and near_duplicate.normalize(reference) not in normalized_candidate for reference in references
    )
    reconstruction_pass = exact_pass and fuzzy_pass and structural_pass and cumulative_pass and no_verbatim_containment

    candidate_fingerprint = near_duplicate.fingerprint(candidate_text).exact_fingerprint
    policy_fingerprint = policy["policy_fingerprint_sha256"]
    results = {"exact": exact_pass, "fuzzy": fuzzy_pass, "structural": structural_pass, "cumulative": cumulative_pass, "reconstruction": reconstruction_pass}
    return {gate: {"passed": passed, "receipt_id": _gate_receipt_id(gate, candidate_fingerprint, policy_fingerprint)} for gate, passed in results.items()}


def reference_set_commitment_sha256(salt: bytes, reference_texts: dict[str, str]) -> str:
    """A keyed commitment over the *content* of every reference text --
    never just its size. Each reference text is first hashed individually
    (so the commitment payload itself stays text-free), then the sorted set
    of those hashes is HMAC'd under the private salt and a domain-
    separation label distinct from every other keyed use of that salt in
    this project. Non-enumerable without the salt; reproducing it still
    requires the exact reference-text content, not merely its count -- a
    caller cannot swap in a same-count, different-content reference set and
    have this commitment silently agree."""
    text_hashes = sorted(_sha256_text(text) for text in reference_texts.values())
    message = REFERENCE_SET_COMMITMENT_DOMAIN + b"\x00" + _canonical_json(text_hashes).encode("utf-8")
    return hmac.new(salt, message, hashlib.sha256).hexdigest()


def build_reference_check_receipt(candidate_text: str, reference_texts: dict[str, str], salt: bytes, *, policy: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run the split-duplicate check and all five reconstruction gates
    against every reference text, and return one text-free, integrity-bound
    receipt. Never carries the candidate text, any reference text, a unit
    id, or a family id -- only one-way fingerprints/hashes, gate booleans,
    and this receipt's own deterministic ``receipt_id``."""
    require(isinstance(candidate_text, str) and candidate_text, "candidate_text must be a nonempty string")
    require(isinstance(reference_texts, dict) and reference_texts, "reference_texts must be a nonempty mapping")
    require(isinstance(salt, (bytes, bytearray)) and len(salt) == 32, "salt must be exactly 32 bytes")
    active_policy = policy if policy is not None else near_duplicate.load_policy()
    require(active_policy.get("policy_fingerprint_sha256") == near_duplicate.policy_fingerprint(active_policy), "near-duplicate policy fingerprint drift -- refusing")

    split = split_check.check_split_duplicate_safety(candidate_text, reference_texts, policy=active_policy)
    gates = _run_reconstruction_gates(candidate_text, reference_texts, active_policy)
    passed = split["passed"] and all(result["passed"] for result in gates.values())

    payload = {
        "candidate_fingerprint_sha256": near_duplicate.fingerprint(candidate_text).exact_fingerprint,
        "policy_sha256": active_policy["policy_fingerprint_sha256"],
        "reference_count": len(reference_texts),
        "reference_set_commitment_sha256": reference_set_commitment_sha256(salt, reference_texts),
        "split_duplicate": {"passed": split["passed"], "receipt_id": split["receipt_id"]},
        "reconstruction_gates": gates,
        "passed": passed,
    }
    receipt_id = f"reference-check:{_sha256_text(_canonical_json(payload))}"
    return {**payload, "receipt_id": receipt_id}


def recompute_receipt_id(receipt: dict[str, Any]) -> str:
    """The receipt's own deterministic id, recomputed from its current body
    -- byte-for-byte identical to what ``build_reference_check_receipt``
    would have produced. Never trusts a stored ``receipt_id`` at face
    value; every caller must compare this against it."""
    body = {k: v for k, v in receipt.items() if k != "receipt_id"}
    return f"reference-check:{_sha256_text(_canonical_json(body))}"


def validate_reference_check_receipt_integrity(receipt: dict[str, Any]) -> None:
    """Structural, content-binding-only proof: the receipt's own
    ``receipt_id`` must reproduce from its current body, and its declared
    ``passed`` must be the logical AND of its own declared per-gate
    booleans -- catching a receipt that was hand-edited (e.g. ``passed``
    flipped without recomputing ``receipt_id``, or flipped while a gate
    underneath it still reads ``False``). This does **not** prove the gate
    results themselves are genuine (that requires the real candidate text
    and reference set, which this function never receives) -- that is what
    ``verify_reference_check_receipt`` is for, run in the A3 role."""
    require(isinstance(receipt, dict), "reference_check_receipt must be an object -- refusing")
    require(recompute_receipt_id(receipt) == receipt.get("receipt_id"), "reference_check_receipt fails its own integrity recheck (tampered or hand-fabricated) -- refusing")
    gates = receipt.get("reconstruction_gates")
    require(isinstance(gates, dict) and set(gates) == set(RECONSTRUCTION_GATES), "reference_check_receipt.reconstruction_gates does not cover exactly the five reconstruction gates -- refusing")
    split_passed = receipt.get("split_duplicate", {}).get("passed")
    all_gates_passed = all(isinstance(gates[gate], dict) and gates[gate].get("passed") is True for gate in RECONSTRUCTION_GATES)
    expected_passed = split_passed is True and all_gates_passed
    require(receipt.get("passed") == expected_passed, "reference_check_receipt.passed is not the logical AND of its own declared split/gate results -- refusing")


def verify_reference_check_receipt(receipt: dict[str, Any], candidate_text: str, reference_texts: dict[str, str], salt: bytes, *, policy: dict[str, Any] | None = None) -> None:
    """The A3-role replay command: rebuild the receipt from the same raw
    candidate text, reference-text set, and salt, and require it to
    reproduce ``receipt`` exactly. This is the only way to prove a stored
    reference-check receipt's gate results are genuine, not merely
    internally self-consistent -- it requires the same private reference
    material A3 already holds, so it can only run in the A3 role."""
    recomputed = build_reference_check_receipt(candidate_text, reference_texts, salt, policy=policy)
    require(recomputed == receipt, "reference_check_receipt does not reproduce from the candidate text, reference-text set, and salt -- refusing")


# --- signed authenticity: receipt signature + replay attestation -----------


def sign_reference_check_receipt(*, signing_key_hex: str, signer_key_id: str, receipt: dict[str, Any], outcome_sha256: str) -> dict[str, Any]:
    """A3-role only: sign a text-free statement that ``receipt`` (already
    self-consistent -- ``validate_reference_check_receipt_integrity`` is
    re-run here) was produced by A3. Never callable by A7; never carries
    candidate/reference text."""
    validate_reference_check_receipt_integrity(receipt)
    body = {
        "schema_version": RECEIPT_SIGNATURE_SCHEMA_VERSION,
        "outcome_sha256": outcome_sha256,
        "reference_check_receipt_sha256": _sha256_text(_canonical_json(receipt)),
        "signer_key_id": signer_key_id,
    }
    signature_hex = trust.sign(signing_key_hex, RECEIPT_SIGNATURE_DOMAIN, body)
    return {**body, "signature_hex": signature_hex}


def verify_reference_check_receipt_signature(signature: dict[str, Any], *, receipt: dict[str, Any], trust_policy: dict[str, Any], outcome_sha256: str) -> None:
    """Fail-closed verification that ``signature`` was issued by an active
    A3 key over exactly this ``receipt`` (a stale signature over a
    previously-swapped receipt refuses, since the digest binds the exact
    receipt content)."""
    require(isinstance(signature, dict), "reference-check receipt signature must be an object -- refusing")
    body = {k: v for k, v in signature.items() if k != "signature_hex"}
    require(body.get("schema_version") == RECEIPT_SIGNATURE_SCHEMA_VERSION, "reference-check receipt signature schema_version mismatch -- refusing")
    require(body.get("outcome_sha256") == outcome_sha256, "reference-check receipt signature is bound to a different outcome -- refusing")
    require(body.get("reference_check_receipt_sha256") == _sha256_text(_canonical_json(receipt)), "reference-check receipt signature does not bind this exact receipt -- refusing (stale or altered receipt)")
    signature_hex = signature.get("signature_hex")
    require(isinstance(signature_hex, str) and bool(signature_hex), "reference-check receipt signature carries no signature_hex -- refusing")
    try:
        trust.verify_with_policy(trust_policy, "a3", body.get("signer_key_id"), RECEIPT_SIGNATURE_DOMAIN, body, signature_hex)
    except trust.TrustAuthorityError as exc:
        raise ReferenceCheckError(f"reference-check receipt signature failed verification -- refusing: {exc}") from exc


def issue_replay_attestation(
    *,
    signing_key_hex: str,
    signer_key_id: str,
    candidate_text: str,
    reference_texts: dict[str, str],
    salt: bytes,
    receipt: dict[str, Any],
    outcome_sha256: str,
    row_content_sha256: str,
    replay_invocation_id: str,
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """The A3-role replay attestation: recompute the receipt live from the
    real candidate text, reference-text set, salt, and policy, require it to
    reproduce ``receipt`` exactly (never sign otherwise), and only then sign
    a text-free attestation binding the outcome, row content, receipt
    digest, policy hash, and a fresh replay invocation id/nonce. Can only
    ever run in the A3 role -- it requires the same private reference
    material A3 already holds."""
    require(isinstance(replay_invocation_id, str) and replay_invocation_id, "replay_invocation_id must be a nonempty string -- refusing")
    recomputed = build_reference_check_receipt(candidate_text, reference_texts, salt, policy=policy)
    require(recomputed == receipt, "reference_check_receipt does not reproduce from the candidate text, reference-text set, and salt -- refusing to attest replay")
    body = {
        "schema_version": REPLAY_ATTESTATION_SCHEMA_VERSION,
        "outcome_sha256": outcome_sha256,
        "row_content_sha256": row_content_sha256,
        "reference_check_receipt_sha256": _sha256_text(_canonical_json(receipt)),
        "policy_sha256": recomputed["policy_sha256"],
        "replay_invocation_id": replay_invocation_id,
        "signer_key_id": signer_key_id,
    }
    signature_hex = trust.sign(signing_key_hex, REPLAY_ATTESTATION_DOMAIN, body)
    return {**body, "signature_hex": signature_hex}


def verify_replay_attestation(attestation: dict[str, Any], *, receipt: dict[str, Any], trust_policy: dict[str, Any], outcome_sha256: str, row_content_sha256: str) -> None:
    """Fail-closed verification that ``attestation`` was issued by an
    active A3 key, binds exactly this receipt (a stale attestation over a
    previously-swapped receipt refuses), the right outcome/row, and the
    receipt's own declared policy hash."""
    require(isinstance(attestation, dict), "replay attestation must be an object -- refusing")
    body = {k: v for k, v in attestation.items() if k != "signature_hex"}
    require(body.get("schema_version") == REPLAY_ATTESTATION_SCHEMA_VERSION, "replay attestation schema_version mismatch -- refusing")
    require(body.get("outcome_sha256") == outcome_sha256, "replay attestation is bound to a different outcome -- refusing")
    require(body.get("row_content_sha256") == row_content_sha256, "replay attestation is not bound to this row's content hash -- refusing")
    require(body.get("reference_check_receipt_sha256") == _sha256_text(_canonical_json(receipt)), "replay attestation does not bind this exact receipt -- refusing (stale or altered receipt)")
    require(body.get("policy_sha256") == receipt.get("policy_sha256"), "replay attestation policy_sha256 does not match the receipt's own policy_sha256 -- refusing")
    signature_hex = attestation.get("signature_hex")
    require(isinstance(signature_hex, str) and bool(signature_hex), "replay attestation carries no signature_hex -- refusing")
    try:
        trust.verify_with_policy(trust_policy, "a3", body.get("signer_key_id"), REPLAY_ATTESTATION_DOMAIN, body, signature_hex)
    except trust.TrustAuthorityError as exc:
        raise ReferenceCheckError(f"replay attestation failed verification -- refusing: {exc}") from exc
