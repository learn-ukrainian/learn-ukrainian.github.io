#!/usr/bin/env python3
"""V4 A7 evidence binder: builds and integrity-checks the evidence receipt a
candidate independently-authored row must carry before it may reach the
shared admission engine (``v4_original_row_admission.evaluate_row`` requires
``evidence.grade == "verified"``, resolved/bounded uncertainty, a supported/
admitted disposition, and a nonempty ``receipt_id``).

Repair (PR #7662, repair 2, P1 "syntactic evidence IDs are falsely promoted
to verified evidence"): the previous ``build_evidence_receipt`` promoted any
identifier matching the pinned VESUM/``sources`` shape regex (e.g.
``vesum:any-made-up-id``) straight to ``grade: "verified"`` -- a shape check,
never a verification. A well-shaped but unverified identifier is now
refused, not promoted:

* ``build_evidence_receipt`` (production-capable) requires a nonempty list
  of already-built, individually integrity-checked **verifier receipts**
  (``build_verifier_receipt``) -- each one binds a sanctioned
  ``mcp__sources__*`` verifier tool's identity/version, a digest of that
  tool's actual result, and the immutable lookup id(s) it returned, plus
  this row's own content hash. A bare identifier string, with no bound
  verifier receipt, can never produce a ``production_capable`` evidence
  receipt.
* ``build_synthetic_fixture_evidence_receipt`` is the explicit, unmistakably
  named test/fixture path: shape-checked identifiers with no verifier
  receipt at all. It always carries ``production_capable: False`` and
  ``evidence_source: "synthetic_fixture"``, and
  ``v4_a7_private_ledger.construct_completion`` refuses to build a
  completion from it unless the caller explicitly passes
  ``allow_synthetic_fixture=True`` -- never the default, and never reachable
  from a caller that does not deliberately opt in.
* ``validate_evidence_receipt_integrity`` recomputes an evidence receipt's
  own ``receipt_id`` (and, for a verifier-backed one, every embedded
  verifier receipt's own ``receipt_id``) from its current body and refuses
  on any mismatch -- the private-replay half of this fix
  (``v4_a7_private_ledger.verify_private_replay`` calls this rather than
  trusting a stored ``grade``/``production_capable`` value at face value).

Real live VESUM/``sources`` MCP tool calls are still a documented follow-up
(this module has no network/MCP access and cannot itself confirm a verifier
receipt's ``tool_result_sha256`` was produced by a genuine tool
invocation) -- what this repair closes is the *structural* promotion gap:
no evidence receipt can claim ``grade: "verified"`` from shape alone, and no
completion can be constructed from a non-``production_capable`` evidence
receipt without an explicit, named opt-in.

This module never accepts or stores raw candidate-family reference text --
see ``v4_a3_reference_check.py`` for the split-duplicate/reconstruction-gate
receipt, which is A3-owned for exactly that reason.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

VERIFIER_TOOL_PREFIX = "mcp__sources__"

# Deterministic, offline identifier-shape check only -- real VESUM/`sources`
# resolution is a documented follow-up (see module docstring). Accepts
# "vesum:<id>" and "sources:<id>" forms.
VESUM_IDENTIFIER_RE = re.compile(r"^(vesum|sources):[a-z0-9][a-z0-9_.:-]*$")
SHA256_HEX_RE = re.compile(r"^[a-f0-9]{64}$")


class EvidenceBinderError(ValueError):
    """Evidence cannot be recorded or verified safely."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise EvidenceBinderError(message)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def verify_identifier_shape(identifier: str) -> bool:
    return isinstance(identifier, str) and bool(VESUM_IDENTIFIER_RE.match(identifier))


# --- verifier receipts (binds a real mcp__sources__ tool call, never a shape guess) --


def _require_verifier_receipt_body_shape(body: dict[str, Any]) -> None:
    require(verify_identifier_shape(body.get("identifier")), f"verifier receipt identifier does not match the pinned VESUM/sources shape: {body.get('identifier')!r}")
    require(
        isinstance(body.get("tool_id"), str) and body["tool_id"].startswith(VERIFIER_TOOL_PREFIX),
        f"verifier receipt tool_id must be a sanctioned {VERIFIER_TOOL_PREFIX!r} verifier tool -- refusing",
    )
    require(isinstance(body.get("tool_version"), str) and body["tool_version"], "verifier receipt tool_version must be a nonempty string -- refusing")
    require(isinstance(body.get("row_content_sha256"), str) and bool(SHA256_HEX_RE.match(body["row_content_sha256"])), "verifier receipt row_content_sha256 is not a well-formed sha256 -- refusing")
    require(isinstance(body.get("tool_result_sha256"), str) and bool(SHA256_HEX_RE.match(body["tool_result_sha256"])), "verifier receipt tool_result_sha256 is not a well-formed sha256 -- refusing")
    lookup_ids = body.get("lookup_ids")
    require(isinstance(lookup_ids, list) and bool(lookup_ids) and all(isinstance(x, str) and x for x in lookup_ids), "verifier receipt lookup_ids must be a nonempty list of immutable identifiers -- refusing")


def build_verifier_receipt(*, tool_id: str, tool_version: str, identifier: str, row_content_sha256: str, tool_result_sha256: str, lookup_ids: list[str]) -> dict[str, Any]:
    """A private receipt binding one sanctioned ``mcp__sources__*`` verifier
    tool call: which tool/version ran, which identifier it was asked about,
    a digest of the tool's actual result, and the immutable lookup id(s) it
    returned. Never carries the tool's raw result text or a row's own
    text -- only hashes and ids."""
    body = {
        "identifier": identifier,
        "tool_id": tool_id,
        "tool_version": tool_version,
        "row_content_sha256": row_content_sha256,
        "tool_result_sha256": tool_result_sha256,
        "lookup_ids": sorted(lookup_ids) if isinstance(lookup_ids, list) else lookup_ids,
    }
    _require_verifier_receipt_body_shape(body)
    receipt_id = f"verifier:{_sha256_text(_canonical_json(body))}"
    return {**body, "receipt_id": receipt_id}


def validate_verifier_receipt_integrity(receipt: dict[str, Any]) -> None:
    require(isinstance(receipt, dict), "verifier receipt must be an object -- refusing")
    body = {k: v for k, v in receipt.items() if k != "receipt_id"}
    _require_verifier_receipt_body_shape(body)
    recomputed = f"verifier:{_sha256_text(_canonical_json(body))}"
    require(recomputed == receipt.get("receipt_id"), "verifier receipt fails its own integrity recheck (tampered or hand-fabricated) -- refusing")


# --- evidence receipts (production-capable vs. explicitly-synthetic) -------


def build_evidence_receipt(row_content_sha256: str, verifier_receipts: list[dict[str, Any]], *, uncertainty: str = "resolved") -> dict[str, Any]:
    """Production-capable evidence: requires a nonempty list of real,
    integrity-checked verifier receipts, each bound to this row's own
    content hash. Refuses (fail closed) a duplicate identifier, a verifier
    receipt that fails its own integrity recheck, or one not bound to
    ``row_content_sha256`` -- a bare well-shaped identifier with no bound
    verifier receipt can never reach ``production_capable: True``."""
    require(isinstance(verifier_receipts, list) and verifier_receipts, "verifier_receipts must be a nonempty list of real verifier receipts (see build_verifier_receipt)")
    identifiers: list[str] = []
    for verifier_receipt in verifier_receipts:
        validate_verifier_receipt_integrity(verifier_receipt)
        require(verifier_receipt["row_content_sha256"] == row_content_sha256, "verifier receipt is not bound to this row's content hash -- refusing")
        identifiers.append(verifier_receipt["identifier"])
    require(len(identifiers) == len(set(identifiers)), "verifier_receipts carries a duplicate identifier -- refusing")
    require(uncertainty in {"resolved", "bounded"}, "uncertainty must be resolved or bounded")

    ordered_receipts = sorted(verifier_receipts, key=lambda receipt: receipt["receipt_id"])
    payload = {
        "row_content_sha256": row_content_sha256,
        "uncertainty": uncertainty,
        "vesum_ids": sorted(identifiers),
        "verifier_receipts": ordered_receipts,
        "evidence_source": "verifier_receipt",
        "production_capable": True,
        "grade": "verified",
        "disposition": "supported",
    }
    receipt_id = f"evidence:{_sha256_text(_canonical_json(payload))}"
    return {**payload, "receipt_id": receipt_id}


def build_synthetic_fixture_evidence_receipt(row_content_sha256: str, vesum_ids: list[str], *, uncertainty: str = "resolved") -> dict[str, Any]:
    """Test/fixture-only evidence: shape-checked identifiers with no bound
    verifier receipt. Always ``production_capable: False`` and
    ``evidence_source: "synthetic_fixture"`` -- ``grade`` stays
    ``"verified"`` only for the shared admission engine's own required
    shape (``v4_original_row_admission.evaluate_row``), never as a claim of
    real verification. ``v4_a7_private_ledger.construct_completion`` refuses
    a completion built from this receipt unless the caller explicitly
    passes ``allow_synthetic_fixture=True``."""
    require(isinstance(vesum_ids, list) and vesum_ids, "vesum_ids must be a nonempty list")
    require(len(vesum_ids) == len(set(vesum_ids)), "vesum_ids must not contain duplicates")
    for identifier in vesum_ids:
        require(verify_identifier_shape(identifier), f"identifier does not match the pinned VESUM/sources shape: {identifier!r}")
    require(uncertainty in {"resolved", "bounded"}, "uncertainty must be resolved or bounded")

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
    receipt_id = f"evidence-synthetic-fixture:{_sha256_text(_canonical_json(payload))}"
    return {**payload, "receipt_id": receipt_id}


def validate_evidence_receipt_integrity(evidence_receipt: dict[str, Any]) -> None:
    """Recompute ``evidence_receipt``'s own ``receipt_id`` from its current
    body (and, for a verifier-backed receipt, every embedded verifier
    receipt's own ``receipt_id``) and refuse on any mismatch -- never trust
    a stored ``grade``/``production_capable``/``receipt_id`` at face value.
    Used both by a production-path caller before admission and by
    ``v4_a7_private_ledger.verify_private_replay``."""
    require(isinstance(evidence_receipt, dict), "evidence_receipt must be an object -- refusing")
    source = evidence_receipt.get("evidence_source")
    require(source in {"verifier_receipt", "synthetic_fixture"}, "evidence_receipt.evidence_source must be verifier_receipt or synthetic_fixture -- refusing")
    require(evidence_receipt.get("grade") == "verified", "evidence_receipt.grade must be 'verified' -- refusing")

    body = {k: v for k, v in evidence_receipt.items() if k != "receipt_id"}
    prefix = "evidence" if source == "verifier_receipt" else "evidence-synthetic-fixture"
    recomputed = f"{prefix}:{_sha256_text(_canonical_json(body))}"
    require(recomputed == evidence_receipt.get("receipt_id"), "evidence_receipt fails its own integrity recheck (tampered or hand-fabricated) -- refusing")

    if source == "verifier_receipt":
        require(evidence_receipt.get("production_capable") is True, "verifier-backed evidence_receipt must declare production_capable true -- refusing")
        verifier_receipts = evidence_receipt.get("verifier_receipts")
        require(isinstance(verifier_receipts, list) and verifier_receipts, "verifier-backed evidence_receipt must carry a nonempty verifier_receipts list -- refusing")
        for verifier_receipt in verifier_receipts:
            validate_verifier_receipt_integrity(verifier_receipt)
            require(verifier_receipt["row_content_sha256"] == evidence_receipt["row_content_sha256"], "verifier receipt is not bound to this evidence receipt's row_content_sha256 -- refusing")
    else:
        require(evidence_receipt.get("production_capable") is False, "synthetic-fixture evidence_receipt must declare production_capable false -- refusing")
