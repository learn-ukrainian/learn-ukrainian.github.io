#!/usr/bin/env python3
"""V4 A7 private ledger: the one place a real, independently-constructed
candidate row's *actual* text, bound source unit, and full authorship /
review / evidence receipts are held -- privately, under
``batch_state/open-model-data/v4-a7-factory/`` (mode 0700 directory / 0600
files, `.gitignore`d, never committed, resolved against the one shared
primary checkout exactly like ``v4_a3_heldout_family_assignment``'s own
private membership artifact).

This module is the private-replay half of the mechanism the public
``v4_a7_original_row_factory`` receipt only ever *claims*: a public
``a7_completions`` entry carries text-free hashes and a copy of the
already-evaluated, self-consistent row receipt, which is enough for a
fresh checkout to confirm the claim is *well-formed* -- but not enough to
prove it is *genuine* (a well-formed receipt can be hand-fabricated without
ever running the real gates). ``verify_private_replay`` closes that gap: it
reruns every gate from this ledger's own stored raw materials (the real
row text, the real bound unit, the real authorship/review receipt bodies)
and requires the result to reproduce the public claim byte for byte.

Slot -> unit selection uses the same private-salt-HMAC-rank construction as
``v4_a3_heldout_family_assignment``'s own family split (deterministic,
content-blind, never guessable without the salt) -- but under its own
domain-separation label, so it can never be confused with, or reduced to,
the held-out assignment commitment over the same secret. Which candidate
unit a slot actually used is therefore never observable from any public
artifact.

No live corpus or model call happens here, and no real row exists yet in
production -- every entrypoint in this module is exercised in this PR only
against synthetic reference texts and a test-only salt (see
``v4_a3_heldout_family_assignment.TEST_SALT_ENV_VAR`` for the analogous
production-salt-safety pattern; this module never reads or writes A3's own
private salt file).
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import v4_a3_heldout_family_assignment as heldout
from scripts.projects.open_model_data import v4_a3_split_duplicate_check as split_check
from scripts.projects.open_model_data import v4_a7_evidence_binder as evidence_binder
from scripts.projects.open_model_data import v4_original_row_admission as admission

ROOT = heldout.ROOT
PRIMARY_ROOT = heldout.PRIMARY_ROOT
PRIVATE_ROOT = heldout.PRIVATE_ROOT
DEFAULT_PRIVATE_DIR = PRIVATE_ROOT / "open-model-data/v4-a7-factory"
LEDGER_FILENAME = "v4_a7_private_ledger_v1.json"

CONTRACTS_RELATIVE = "data/projects/open_model_data/contracts"
AUTHORSHIP_SCHEMA_PATH = ROOT / CONTRACTS_RELATIVE / "dataset_v4_a7_authorship_receipt_v1.schema.json"
REVIEW_SCHEMA_PATH = ROOT / CONTRACTS_RELATIVE / "dataset_v4_a7_review_receipt_v1.schema.json"

V4_SHA256 = "78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20"

# Domain-separation labels, distinct from every other private-salt use in
# this project (see v4_a3_heldout_family_assignment.ASSIGNMENT_COMMITMENT_DOMAIN
# and v4_a3_builder_packet.PACKET_COMMITMENT_DOMAIN) -- reproducing either of
# these still requires the same 32-byte salt, but neither can be reduced to
# or confused with a different keyed digest over that secret.
SLOT_UNIT_PICK_DOMAIN = b"v4-a7-slot-unit-pick-v1"
LINEAGE_ID_DOMAIN = b"v4-a7-lineage-id-v1"

LEDGER_ID = "v4-a7-private-ledger-v1"
LEDGER_REQUIRED_FIELDS = frozenset({"ledger_id", "controlling_outcome_sha256", "entries"})

canonical_json = heldout.canonical_json
sha256_text = heldout.sha256_text


class PrivateLedgerError(ValueError):
    """The private ledger, a candidate completion, or its replay is unsafe."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PrivateLedgerError(message)


# --- slot -> unit selection, lineage ids (private-salt HMAC, content-blind) --


def _rank(salt: bytes, domain: bytes, *parts: str) -> int:
    message = domain + b"\x00" + b"\x00".join(part.encode("utf-8") for part in parts)
    return int(hmac.new(salt, message, hashlib.sha256).hexdigest(), 16)


def pick_bound_unit(salt: bytes, slot_id: str, candidate_unit_ids: list[str]) -> str:
    """Deterministic, content-blind pick among ``candidate_unit_ids`` for
    ``slot_id`` -- the lexicographically-smallest-ranked unit under an
    HMAC keyed by the private salt. Never guessable without the salt;
    never published."""
    require(bool(candidate_unit_ids), "candidate_unit_ids must be nonempty")
    require(len(candidate_unit_ids) == len(set(candidate_unit_ids)), "candidate_unit_ids must not contain duplicates")
    ordered = sorted(candidate_unit_ids, key=lambda unit_id: (_rank(salt, SLOT_UNIT_PICK_DOMAIN, slot_id, unit_id), unit_id))
    return ordered[0]


def per_row_lineage_id(salt: bytes, slot_id: str, unit_id: str) -> str:
    """A per-row salted lineage id -- never the real ``source_unit_id``,
    never reproducible without the salt, and (see
    ``validate_lineage_not_equal_to_a4_commitment``) never equal to a
    published A4 ``unit_commitments`` entry."""
    digest = hmac.new(salt, LINEAGE_ID_DOMAIN + b"\x00" + slot_id.encode("utf-8") + b"\x00" + unit_id.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"v4a7-lineage-{digest}"


def validate_lineage_not_equal_to_a4_commitment(lineage_source_ids: list[str], a4_unit_commitments: list[str]) -> None:
    """The advisor-decision invariant: a public lineage id must never equal
    a published A4 ``unit_commitments`` entry -- that would let a reader
    directly bind a slot to a real builder-eligible unit."""
    colliding = set(lineage_source_ids) & set(a4_unit_commitments)
    require(not colliding, f"lineage source id(s) collide with published A4 unit_commitments entries -- refusing: {sorted(colliding)}")


# --- authorship / review receipts (private; schema-validated) ---------------


def _load_schema(path: Path) -> dict[str, Any]:
    schema = json.loads(path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return schema


def _validate_against_schema(receipt: dict[str, Any], schema_path: Path) -> None:
    errors = sorted(Draft202012Validator(_load_schema(schema_path)).iter_errors(receipt), key=lambda e: list(e.path))
    require(not errors, f"receipt fails schema validation ({schema_path.name}): {errors[0].message}" if errors else "")


def _finalize_receipt(domain: str, body: dict[str, Any]) -> dict[str, Any]:
    receipt_id = f"{domain}:{sha256_text(canonical_json(body))}"
    return {**body, "receipt_id": receipt_id}


def build_authorship_receipt(
    *,
    model_family: str,
    exact_model: str,
    harness: str,
    session_id: str,
    prompt_sha256: str,
    packet_sha256: str,
    row_content_sha256: str,
    saw_source_text: bool = False,
    saw_heldout: bool = False,
    saw_eligible_unit_ids: bool = False,
    verification_tool_ids: list[str] = (),  # type: ignore[assignment]
) -> dict[str, Any]:
    """Independent-row-eligibility requires every ``saw_*`` attestation to
    be false -- refuses (fail closed) otherwise, never silently coerces."""
    require(saw_source_text is False, "author must attest saw_source_text is false -- refusing")
    require(saw_heldout is False, "author must attest saw_heldout is false -- refusing")
    require(saw_eligible_unit_ids is False, "author must attest saw_eligible_unit_ids is false -- refusing")
    body = {
        "role": "author",
        "model_family": model_family,
        "exact_model": exact_model,
        "harness": harness,
        "session_id": session_id,
        "prompt_sha256": prompt_sha256,
        "packet_sha256": packet_sha256,
        "row_content_sha256": row_content_sha256,
        "saw_source_text": False,
        "saw_heldout": False,
        "saw_eligible_unit_ids": False,
        "verification_tool_ids": sorted(verification_tool_ids),
    }
    receipt = _finalize_receipt("authorship", body)
    _validate_against_schema(receipt, AUTHORSHIP_SCHEMA_PATH)
    return receipt


def build_review_receipt(
    *,
    authorship_receipt: dict[str, Any],
    model_family: str,
    exact_model: str,
    harness: str,
    session_id: str,
    prompt_sha256: str,
    packet_sha256: str,
    row_content_sha256: str,
    verdict: str,
    rubric_sha256: str,
    saw_source_text: bool = False,
    saw_heldout: bool = False,
    saw_eligible_unit_ids: bool = False,
    verification_tool_ids: list[str] = (),  # type: ignore[assignment]
) -> dict[str, Any]:
    """Independent-row-eligibility requires the reviewer's model family and
    session to be distinct from the author's -- refuses (fail closed) on a
    same-family or same-session review, and on any ``saw_*`` attestation
    true, exactly like the author's own receipt."""
    require(model_family != authorship_receipt["model_family"], "reviewer must be a distinct model family from the author -- refusing (same-family review)")
    require(session_id != authorship_receipt["session_id"], "reviewer must be a distinct session from the author -- refusing (same-session review)")
    require(saw_source_text is False, "reviewer must attest saw_source_text is false -- refusing")
    require(saw_heldout is False, "reviewer must attest saw_heldout is false -- refusing")
    require(saw_eligible_unit_ids is False, "reviewer must attest saw_eligible_unit_ids is false -- refusing")
    require(verdict in {"PASS", "FAIL"}, "verdict must be PASS or FAIL")
    body = {
        "role": "reviewer",
        "model_family": model_family,
        "exact_model": exact_model,
        "harness": harness,
        "session_id": session_id,
        "prompt_sha256": prompt_sha256,
        "packet_sha256": packet_sha256,
        "row_content_sha256": row_content_sha256,
        "saw_source_text": False,
        "saw_heldout": False,
        "saw_eligible_unit_ids": False,
        "verification_tool_ids": sorted(verification_tool_ids),
        "verdict": verdict,
        "rubric_sha256": rubric_sha256,
    }
    receipt = _finalize_receipt("review", body)
    _validate_against_schema(receipt, REVIEW_SCHEMA_PATH)
    return receipt


# --- admission input row construction ----------------------------------------


def build_admission_input_row(
    *,
    slot_id: str,
    salt: bytes,
    bound_unit_id: str,
    row_text: str,
    tier: str,
    authorship_receipt: dict[str, Any],
    review_receipt: dict[str, Any],
    evidence_receipt: dict[str, Any],
    rights_receipt_id: str,
    split_duplicate_receipt: dict[str, Any],
    reconstruction_gate_receipts: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    require(review_receipt["verdict"] == "PASS", "review verdict must be PASS to construct an admission input row -- refusing")
    row_content_sha256 = sha256_text(row_text)
    require(
        row_content_sha256 == authorship_receipt["row_content_sha256"] == review_receipt["row_content_sha256"] == evidence_receipt["row_content_sha256"],
        "row_content_sha256 mismatch across authorship/review/evidence receipts -- refusing",
    )
    lineage_id = per_row_lineage_id(salt, slot_id, bound_unit_id)
    return {
        "row_id": f"v4a7-row-{slot_id}",
        "row_content_sha256": row_content_sha256,
        "lineage": {"immutable": True, "source_ids": [lineage_id], "evidence_ids": list(evidence_receipt["vesum_ids"])},
        "label_tier": tier,
        "authorship": {"independently_authored": True, "receipt_id": authorship_receipt["receipt_id"]},
        "evidence": {
            "grade": evidence_receipt["grade"],
            "uncertainty": evidence_receipt["uncertainty"],
            "disposition": evidence_receipt["disposition"],
            "receipt_id": evidence_receipt["receipt_id"],
        },
        "rights": {
            "training": True,
            "derived_dataset_redistribution": True,
            "receipt_id": rights_receipt_id,
            "operation_cells": ["training", "derived_dataset_redistribution"],
        },
        "split_duplicate_safety": {"passed": split_duplicate_receipt["passed"], "receipt_id": split_duplicate_receipt["receipt_id"]},
        "reconstruction_gates": {
            gate: {"passed": reconstruction_gate_receipts[gate]["passed"], "receipt_id": reconstruction_gate_receipts[gate]["receipt_id"]}
            for gate in admission.RECONSTRUCTION_GATES
        },
    }


# --- end-to-end construction (private; the only place a real row is built) --


def construct_completion(
    *,
    slot_id: str,
    salt: bytes,
    candidate_unit_ids: list[str],
    a4_unit_commitments: list[str],
    row_text: str,
    tier: str,
    author: dict[str, Any],
    reviewer: dict[str, Any],
    vesum_ids: list[str],
    reference_texts: dict[str, str],
    rights_receipt_id: str,
) -> dict[str, Any]:
    """Run every gate live and return ``{"private_entry", "public_completion"}``.
    Refuses (fail closed) unless every gate genuinely passes -- never
    constructs a completion for a row that failed a gate."""
    bound_unit_id = pick_bound_unit(salt, slot_id, candidate_unit_ids)
    row_content_sha256 = sha256_text(row_text)

    authorship_receipt = build_authorship_receipt(row_content_sha256=row_content_sha256, **author)

    split_duplicate_receipt = split_check.check_split_duplicate_safety(row_text, reference_texts)
    require(split_duplicate_receipt["passed"], "split-duplicate safety check failed -- refusing to construct a completion")

    reconstruction_gate_receipts = evidence_binder.run_reconstruction_gates(row_text, reference_texts)
    for gate, result in reconstruction_gate_receipts.items():
        require(result["passed"], f"reconstruction gate {gate!r} failed -- refusing to construct a completion")

    evidence_receipt = evidence_binder.build_evidence_receipt(row_content_sha256, vesum_ids)
    review_receipt = build_review_receipt(authorship_receipt=authorship_receipt, row_content_sha256=row_content_sha256, **reviewer)
    require(review_receipt["verdict"] == "PASS", "review verdict is not PASS -- refusing to construct a completion")

    input_row = build_admission_input_row(
        slot_id=slot_id,
        salt=salt,
        bound_unit_id=bound_unit_id,
        row_text=row_text,
        tier=tier,
        authorship_receipt=authorship_receipt,
        review_receipt=review_receipt,
        evidence_receipt=evidence_receipt,
        rights_receipt_id=rights_receipt_id,
        split_duplicate_receipt=split_duplicate_receipt,
        reconstruction_gate_receipts=reconstruction_gate_receipts,
    )
    validate_lineage_not_equal_to_a4_commitment(input_row["lineage"]["source_ids"], a4_unit_commitments)

    admission_receipt = admission.admit_rows(outcome_sha256=V4_SHA256, rows=[input_row])
    row_receipt = admission_receipt["rows"][0]
    require(row_receipt["disposition"] == "admitted", f"constructed row was not admitted by the shared engine: {row_receipt['residual_codes']} -- refusing")

    authorship_sha256 = sha256_text(canonical_json(authorship_receipt))
    review_sha256 = sha256_text(canonical_json(review_receipt))

    private_entry = {
        "slot_id": slot_id,
        "row_id": input_row["row_id"],
        "row_text": row_text,
        "row_content_sha256": row_content_sha256,
        "bound_unit_id": bound_unit_id,
        "lineage_source_id": input_row["lineage"]["source_ids"][0],
        "authorship_receipt": authorship_receipt,
        "review_receipt": review_receipt,
        "evidence_receipt": evidence_receipt,
        "split_duplicate_receipt": split_duplicate_receipt,
        "reconstruction_gate_receipts": reconstruction_gate_receipts,
        "admission_input_row": input_row,
        "admission_row_receipt": row_receipt,
    }
    public_completion = {
        "stage": "A7",
        "slot_id": slot_id,
        "row_id": input_row["row_id"],
        "row_content_sha256": row_content_sha256,
        "admission_receipt_sha256": row_receipt["receipt_sha256"],
        "authorship_receipt_sha256": authorship_sha256,
        "review_receipt_sha256": review_sha256,
        "row_receipt": row_receipt,
    }
    return {"private_entry": private_entry, "public_completion": public_completion}


# --- private ledger persistence (0700/0600, never committed) ----------------


def build_ledger_payload(entries: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {"ledger_id": LEDGER_ID, "controlling_outcome_sha256": V4_SHA256, "entries": entries}


def write_ledger(entries: dict[str, dict[str, Any]], path: Path) -> None:
    """Create-only write (never overwrites) -- reuses
    ``v4_a3_heldout_family_assignment``'s own symlink-safe, atomic,
    fsync'd-to-disk filesystem hardening rather than reimplementing it."""
    heldout.write_new_private_json_artifact(path, build_ledger_payload(entries))


def load_ledger(path: Path) -> dict[str, Any]:
    ledger = heldout.load_private_artifact(path, required_fields=LEDGER_REQUIRED_FIELDS)
    require(ledger["ledger_id"] == LEDGER_ID, "private ledger ledger_id mismatch -- refusing")
    require(ledger["controlling_outcome_sha256"] == V4_SHA256, "private ledger controlling_outcome_sha256 mismatch -- refusing")
    return ledger


# --- private replay: proves a public completion is genuine, not just well-formed --


def verify_private_replay(public_receipt: dict[str, Any], ledger: dict[str, Any], *, a4_unit_commitments: list[str]) -> None:
    """For every ``a7_completions`` entry in ``public_receipt``, require a
    matching private ledger entry to exist and to reproduce -- byte for
    byte, via a live re-derivation, never a stored/trusted copy -- every
    hash the public receipt declares. Refuses (fail closed) on a missing
    ledger entry (a forged public completion with no private replay), any
    hash mismatch, a same-family/same-session author/reviewer, any
    ``saw_*`` attestation true, a non-PASS verdict, or a lineage id
    colliding with a published A4 commitment."""
    entries = ledger["entries"]
    for completion in public_receipt.get("a7_completions", []):
        slot_id = completion["slot_id"]
        require(slot_id in entries, f"no private ledger entry for completed slot {slot_id!r} -- refusing (forged public completion without private replay)")
        entry = entries[slot_id]
        require(entry["row_id"] == completion["row_id"], f"private ledger row_id does not match the public completion for slot {slot_id!r} -- refusing")

        recomputed_content_sha256 = sha256_text(entry["row_text"])
        require(
            recomputed_content_sha256 == entry["row_content_sha256"] == completion["row_content_sha256"],
            f"row_content_sha256 does not reproduce from the private ledger's own stored row text for slot {slot_id!r} -- refusing",
        )

        authorship_receipt = entry["authorship_receipt"]
        review_receipt = entry["review_receipt"]
        require(sha256_text(canonical_json(authorship_receipt)) == completion["authorship_receipt_sha256"], f"authorship_receipt_sha256 does not reproduce for slot {slot_id!r} -- refusing")
        require(sha256_text(canonical_json(review_receipt)) == completion["review_receipt_sha256"], f"review_receipt_sha256 does not reproduce for slot {slot_id!r} -- refusing")

        require(authorship_receipt["model_family"] != review_receipt["model_family"], f"slot {slot_id!r}: author and reviewer share a model family -- refusing")
        require(authorship_receipt["session_id"] != review_receipt["session_id"], f"slot {slot_id!r}: author and reviewer share a session -- refusing")
        for receipt, role in ((authorship_receipt, "author"), (review_receipt, "reviewer")):
            require(receipt["saw_source_text"] is False, f"slot {slot_id!r}: {role} attests saw_source_text is not false -- refusing")
            require(receipt["saw_heldout"] is False, f"slot {slot_id!r}: {role} attests saw_heldout is not false -- refusing")
            require(receipt["saw_eligible_unit_ids"] is False, f"slot {slot_id!r}: {role} attests saw_eligible_unit_ids is not false -- refusing")
        require(review_receipt["verdict"] == "PASS", f"slot {slot_id!r}: review verdict is not PASS -- refusing")

        input_row = entry["admission_input_row"]
        validate_lineage_not_equal_to_a4_commitment(input_row["lineage"]["source_ids"], a4_unit_commitments)

        recomputed_admission = admission.admit_rows(outcome_sha256=V4_SHA256, rows=[input_row])
        recomputed_row_receipt = recomputed_admission["rows"][0]
        require(recomputed_row_receipt == entry["admission_row_receipt"], f"slot {slot_id!r}: private replay does not reproduce the ledger's own stored row receipt -- refusing")
        require(recomputed_row_receipt == completion.get("row_receipt"), f"slot {slot_id!r}: private replay does not reproduce the public completion's row_receipt -- refusing")
        require(recomputed_row_receipt["receipt_sha256"] == completion["admission_receipt_sha256"], f"slot {slot_id!r}: admission_receipt_sha256 does not reproduce from private replay -- refusing")
        require(recomputed_row_receipt["disposition"] == "admitted", f"slot {slot_id!r}: private replay does not reproduce an admitted disposition -- refusing")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--public-receipt", required=True, type=Path, help="the public A7 original-row-factory receipt JSON to replay against")
    parser.add_argument("--ledger", required=True, type=Path, help="the private ledger JSON (0700/0600, never committed)")
    parser.add_argument("--a4-receipt", required=True, type=Path, help="the public A4 deterministic-extraction receipt JSON (for unit_commitments)")
    parser.add_argument("--verify-private", action="store_true", required=True, help="run the private replay (the only supported mode)")
    args = parser.parse_args(argv)

    public_receipt = json.loads(args.public_receipt.read_text(encoding="utf-8"))
    ledger = load_ledger(args.ledger)
    a4_receipt = json.loads(args.a4_receipt.read_text(encoding="utf-8"))
    a4_unit_commitments = a4_receipt["builder_packet_consumption"]["unit_commitments"]

    try:
        verify_private_replay(public_receipt, ledger, a4_unit_commitments=a4_unit_commitments)
    except PrivateLedgerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(json.dumps({"verified": True, "completions_replayed": len(public_receipt.get("a7_completions", []))}))


if __name__ == "__main__":
    main()
