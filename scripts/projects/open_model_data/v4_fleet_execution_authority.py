#!/usr/bin/env python3
"""V4 fleet execution attester: the sole authority permitted to sign an
author/reviewer execution receipt admissible to A7's private ledger (PR
#7662 repair 4, blocking repair E -- designated-advisor ``GO_REPAIR``).

Before this module existed, ``v4_a7_private_ledger.build_authorship_receipt``
/``build_review_receipt`` accepted raw caller-supplied identity dictionaries
(model family, session id, ``saw_*`` attestations, verdict) and only ever
self-hashed them -- a consistently fabricated distinct-family ``PASS`` pair
survived every check, including replay. This module is the distinct
authority that closes that gap: it owns an Ed25519 private key never
available to the A7 caller, consumes trusted delegate/runtime/
provider-adapter evidence directly (never caller-submitted receipt JSON),
verifies an observed terminal successful execution plus the role-specific
structured result, and only then signs a text-free receipt binding model/
family/harness/task/run/session identity to the row it authored or
reviewed.

``issue_author_execution_receipt``/``issue_reviewer_execution_receipt`` are
called only by the attester itself (production custody: Hramatka, outside
git/prompts/CLI arguments/logs; every test here uses an ephemeral key
generated fresh under ``tmp_path``). A7's private ledger only ever calls
``verify_author_execution_receipt``/``verify_reviewer_execution_receipt``,
against the pinned ``fleet_execution`` keyring in the trust policy -- it can
verify a receipt already issued here, never mint one itself.

The resulting receipts carry hashes, ids, and booleans only -- no row text,
source text, membership, or corpus text ever passes through this module.
"""

from __future__ import annotations

from typing import Any

from scripts.projects.open_model_data import v4_trust_authority as trust

SCHEMA_VERSION = "v4-fleet-execution-receipt-v1"
AUTHOR_DOMAIN = b"v4-fleet-execution-author-v1"
REVIEWER_DOMAIN = b"v4-fleet-execution-reviewer-v1"


class FleetExecutionError(ValueError):
    """An author/reviewer execution receipt cannot be issued or verified safely."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise FleetExecutionError(message)


def _require_common_identity(model_family: str, exact_model: str, harness: str, task_id: str, run_nonce: str, prompt_sha256: str, packet_sha256: str, row_content_sha256: str, issuance_nonce: str, signer_key_id: str) -> None:
    for name, value in (
        ("model_family", model_family),
        ("exact_model", exact_model),
        ("harness", harness),
        ("task_id", task_id),
        ("run_nonce", run_nonce),
        ("issuance_nonce", issuance_nonce),
        ("signer_key_id", signer_key_id),
    ):
        require(isinstance(value, str) and value, f"{name} must be a nonempty string -- refusing")
    for name, value in (("prompt_sha256", prompt_sha256), ("packet_sha256", packet_sha256), ("row_content_sha256", row_content_sha256)):
        require(isinstance(value, str) and len(value) == 64, f"{name} must be a well-formed sha256 -- refusing")


def issue_author_execution_receipt(
    *,
    signing_key_hex: str,
    signer_key_id: str,
    outcome_sha256: str,
    task_id: str,
    run_nonce: str,
    fleet_receipt_sha256: str,
    provider_session_id: str | None,
    model_family: str,
    exact_model: str,
    harness: str,
    prompt_sha256: str,
    packet_sha256: str,
    row_content_sha256: str,
    execution_result_sha256: str,
    verification_tool_ids: list[str] = (),  # type: ignore[assignment]
    saw_source_text: bool = False,
    saw_heldout: bool = False,
    saw_eligible_unit_ids: bool = False,
    issuance_nonce: str,
) -> dict[str, Any]:
    """Sign a text-free author execution receipt. Requires every ``saw_*``
    attestation to already be false (fail closed otherwise -- never silently
    coerces) and a terminal, observed, successful execution to already have
    been confirmed by the caller (the attester) from authoritative runtime
    evidence before this is ever called."""
    require(saw_source_text is False, "author must attest saw_source_text is false -- refusing")
    require(saw_heldout is False, "author must attest saw_heldout is false -- refusing")
    require(saw_eligible_unit_ids is False, "author must attest saw_eligible_unit_ids is false -- refusing")
    _require_common_identity(model_family, exact_model, harness, task_id, run_nonce, prompt_sha256, packet_sha256, row_content_sha256, issuance_nonce, signer_key_id)
    require(isinstance(execution_result_sha256, str) and len(execution_result_sha256) == 64, "execution_result_sha256 must be a well-formed sha256 -- refusing")
    require(isinstance(fleet_receipt_sha256, str) and len(fleet_receipt_sha256) == 64, "fleet_receipt_sha256 must be a well-formed sha256 -- refusing")
    require(provider_session_id is None or (isinstance(provider_session_id, str) and provider_session_id), "provider_session_id must be None or a nonempty string -- refusing")

    body = {
        "schema_version": SCHEMA_VERSION,
        "domain": "author",
        "outcome_sha256": outcome_sha256,
        "task_id": task_id,
        "run_nonce": run_nonce,
        "fleet_receipt_sha256": fleet_receipt_sha256,
        "provider_session_id": provider_session_id,
        "model_family": model_family,
        "exact_model": exact_model,
        "harness": harness,
        "prompt_sha256": prompt_sha256,
        "packet_sha256": packet_sha256,
        "row_content_sha256": row_content_sha256,
        "execution_result_sha256": execution_result_sha256,
        "verification_tool_ids": sorted(verification_tool_ids),
        "saw_source_text": False,
        "saw_heldout": False,
        "saw_eligible_unit_ids": False,
        "signer_key_id": signer_key_id,
        "issuance_nonce": issuance_nonce,
    }
    signature_hex = trust.sign(signing_key_hex, AUTHOR_DOMAIN, body)
    return {**body, "signature_hex": signature_hex}


def issue_reviewer_execution_receipt(
    *,
    signing_key_hex: str,
    signer_key_id: str,
    outcome_sha256: str,
    task_id: str,
    run_nonce: str,
    fleet_receipt_sha256: str,
    provider_session_id: str | None,
    model_family: str,
    exact_model: str,
    harness: str,
    prompt_sha256: str,
    packet_sha256: str,
    row_content_sha256: str,
    execution_result_sha256: str,
    authorship_receipt_sha256: str,
    rubric_sha256: str,
    verdict: str,
    verification_tool_ids: list[str] = (),  # type: ignore[assignment]
    saw_source_text: bool = False,
    saw_heldout: bool = False,
    saw_eligible_unit_ids: bool = False,
    issuance_nonce: str,
) -> dict[str, Any]:
    """Sign a text-free reviewer execution receipt, additionally binding
    the exact authorship-receipt digest, rubric hash, row hash, and
    verdict."""
    require(saw_source_text is False, "reviewer must attest saw_source_text is false -- refusing")
    require(saw_heldout is False, "reviewer must attest saw_heldout is false -- refusing")
    require(saw_eligible_unit_ids is False, "reviewer must attest saw_eligible_unit_ids is false -- refusing")
    require(verdict in {"PASS", "FAIL"}, "verdict must be PASS or FAIL -- refusing")
    _require_common_identity(model_family, exact_model, harness, task_id, run_nonce, prompt_sha256, packet_sha256, row_content_sha256, issuance_nonce, signer_key_id)
    require(isinstance(execution_result_sha256, str) and len(execution_result_sha256) == 64, "execution_result_sha256 must be a well-formed sha256 -- refusing")
    require(isinstance(fleet_receipt_sha256, str) and len(fleet_receipt_sha256) == 64, "fleet_receipt_sha256 must be a well-formed sha256 -- refusing")
    require(isinstance(authorship_receipt_sha256, str) and len(authorship_receipt_sha256) == 64, "authorship_receipt_sha256 must be a well-formed sha256 -- refusing")
    require(isinstance(rubric_sha256, str) and len(rubric_sha256) == 64, "rubric_sha256 must be a well-formed sha256 -- refusing")
    require(provider_session_id is None or (isinstance(provider_session_id, str) and provider_session_id), "provider_session_id must be None or a nonempty string -- refusing")

    body = {
        "schema_version": SCHEMA_VERSION,
        "domain": "reviewer",
        "outcome_sha256": outcome_sha256,
        "task_id": task_id,
        "run_nonce": run_nonce,
        "fleet_receipt_sha256": fleet_receipt_sha256,
        "provider_session_id": provider_session_id,
        "model_family": model_family,
        "exact_model": exact_model,
        "harness": harness,
        "prompt_sha256": prompt_sha256,
        "packet_sha256": packet_sha256,
        "row_content_sha256": row_content_sha256,
        "execution_result_sha256": execution_result_sha256,
        "authorship_receipt_sha256": authorship_receipt_sha256,
        "rubric_sha256": rubric_sha256,
        "verdict": verdict,
        "verification_tool_ids": sorted(verification_tool_ids),
        "saw_source_text": False,
        "saw_heldout": False,
        "saw_eligible_unit_ids": False,
        "signer_key_id": signer_key_id,
        "issuance_nonce": issuance_nonce,
    }
    signature_hex = trust.sign(signing_key_hex, REVIEWER_DOMAIN, body)
    return {**body, "signature_hex": signature_hex}


def _verify_common(receipt: dict[str, Any], *, domain_name: str, domain: bytes, trust_policy: dict[str, Any], outcome_sha256: str, row_content_sha256: str) -> dict[str, Any]:
    require(isinstance(receipt, dict), f"{domain_name} execution receipt must be an object -- refusing")
    body = {k: v for k, v in receipt.items() if k != "signature_hex"}
    require(body.get("schema_version") == SCHEMA_VERSION and body.get("domain") == domain_name, f"malformed {domain_name} execution receipt -- refusing")
    require(body.get("outcome_sha256") == outcome_sha256, f"{domain_name} execution receipt is bound to a different outcome -- refusing")
    require(body.get("row_content_sha256") == row_content_sha256, f"{domain_name} execution receipt is not bound to this row's content hash -- refusing")
    for flag in ("saw_source_text", "saw_heldout", "saw_eligible_unit_ids"):
        require(body.get(flag) is False, f"{domain_name} execution receipt attests {flag} is not false -- refusing")
    for name in ("model_family", "exact_model", "harness", "task_id", "run_nonce"):
        require(isinstance(body.get(name), str) and body[name], f"{domain_name} execution receipt is missing {name} -- refusing")
    signature_hex = receipt.get("signature_hex")
    require(isinstance(signature_hex, str) and bool(signature_hex), f"{domain_name} execution receipt carries no signature -- refusing")
    try:
        trust.verify_with_policy(trust_policy, "fleet_execution", body.get("signer_key_id"), domain, body, signature_hex)
    except trust.TrustAuthorityError as exc:
        raise FleetExecutionError(f"{domain_name} execution receipt failed signature verification -- refusing: {exc}") from exc
    return body


def verify_author_execution_receipt(receipt: dict[str, Any], *, trust_policy: dict[str, Any], outcome_sha256: str, row_content_sha256: str) -> None:
    _verify_common(receipt, domain_name="author", domain=AUTHOR_DOMAIN, trust_policy=trust_policy, outcome_sha256=outcome_sha256, row_content_sha256=row_content_sha256)


def verify_reviewer_execution_receipt(
    receipt: dict[str, Any],
    *,
    trust_policy: dict[str, Any],
    outcome_sha256: str,
    row_content_sha256: str,
    authorship_receipt_sha256: str,
    rubric_sha256: str,
) -> None:
    body = _verify_common(receipt, domain_name="reviewer", domain=REVIEWER_DOMAIN, trust_policy=trust_policy, outcome_sha256=outcome_sha256, row_content_sha256=row_content_sha256)
    require(body.get("authorship_receipt_sha256") == authorship_receipt_sha256, "reviewer execution receipt is bound to a different authorship receipt -- refusing")
    require(body.get("rubric_sha256") == rubric_sha256, "reviewer execution receipt is bound to a different rubric -- refusing")
    require(body.get("verdict") in {"PASS", "FAIL"}, "reviewer execution receipt verdict must be PASS or FAIL -- refusing")
