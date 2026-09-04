#!/usr/bin/env python3
"""V4 sources execution authority: the sole role permitted to issue a
production-capable verifier attestation (PR #7662 repair 4, blocking repair
A -- designated-advisor ``GO_REPAIR``).

Before this module existed, ``v4_a7_evidence_binder.build_verifier_receipt``
accepted every supposedly evidentiary field straight from its A7 caller and
promoted an unkeyed ``sha256(body)`` self-hash to ``production_capable:
True`` -- ordinary self-integrity, never proof that a real
``mcp__sources__*`` tool call ever happened. This module is the distinct
authority that closes that gap: only ``issue_verifier_attestation`` (called
by whatever process actually ran the sanctioned tool, never by A7 itself)
can mint a signed attestation, and only ``verify_verifier_attestation`` --
which A7's evidence binder calls, never the issuing half -- can turn that
signature into trust. The Ed25519 private key ``issue_verifier_attestation``
needs stays outside git, outside prompts, and outside CLI arguments/logs;
production custody lives on Hramatka. Every test here uses an ephemeral key
generated fresh under ``tmp_path`` via ``v4_trust_authority
.generate_test_keypair``.
"""

from __future__ import annotations

import re
from typing import Any

from scripts.projects.open_model_data import v4_trust_authority as trust

SCHEMA_VERSION = "v4-sources-verifier-attestation-v1"
ATTESTATION_DOMAIN = b"v4-sources-verifier-attestation-v1"
VERIFIER_TOOL_PREFIX = "mcp__sources__"
SHA256_HEX_RE = re.compile(r"^[a-f0-9]{64}$")


class SourcesAuthorityError(ValueError):
    """A verifier attestation cannot be issued or verified safely."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SourcesAuthorityError(message)


def issue_verifier_attestation(
    *,
    signing_key_hex: str,
    signer_key_id: str,
    outcome_sha256: str,
    row_content_sha256: str,
    identifier: str,
    tool_id: str,
    tool_version: str,
    request_id: str,
    tool_result_sha256: str,
    lookup_ids: list[str],
    invocation_id: str,
) -> dict[str, Any]:
    """Issue a signed, text-free attestation that a real, sanctioned
    ``mcp__sources__*`` verifier tool invocation happened and produced the
    given result digest / immutable lookup ids. The only way any evidence
    receipt can ever become ``production_capable`` -- called only by the
    sources execution authority (which is expected to have actually run the
    invocation before calling this), never reachable from A7."""
    require(isinstance(tool_id, str) and tool_id.startswith(VERIFIER_TOOL_PREFIX), f"tool_id must be a sanctioned {VERIFIER_TOOL_PREFIX!r} verifier tool -- refusing")
    require(isinstance(tool_version, str) and tool_version, "tool_version must be a nonempty string -- refusing")
    require(isinstance(identifier, str) and identifier, "identifier must be a nonempty string -- refusing")
    require(isinstance(row_content_sha256, str) and bool(SHA256_HEX_RE.match(row_content_sha256)), "row_content_sha256 is not a well-formed sha256 -- refusing")
    require(isinstance(tool_result_sha256, str) and bool(SHA256_HEX_RE.match(tool_result_sha256)), "tool_result_sha256 is not a well-formed sha256 -- refusing")
    require(isinstance(lookup_ids, list) and bool(lookup_ids) and all(isinstance(x, str) and x for x in lookup_ids), "lookup_ids must be a nonempty list of immutable identifiers -- refusing")
    require(isinstance(request_id, str) and request_id, "request_id must be a nonempty string -- refusing")
    require(isinstance(invocation_id, str) and invocation_id, "invocation_id must be a nonempty string -- refusing")
    require(isinstance(signer_key_id, str) and signer_key_id, "signer_key_id must be a nonempty string -- refusing")

    body = {
        "schema_version": SCHEMA_VERSION,
        "outcome_sha256": outcome_sha256,
        "row_content_sha256": row_content_sha256,
        "identifier": identifier,
        "tool_id": tool_id,
        "tool_version": tool_version,
        "request_id": request_id,
        "tool_result_sha256": tool_result_sha256,
        "lookup_ids": sorted(lookup_ids),
        "success": True,
        "invocation_id": invocation_id,
        "signer_key_id": signer_key_id,
    }
    signature_hex = trust.sign(signing_key_hex, ATTESTATION_DOMAIN, body)
    return {**body, "signature_hex": signature_hex}


def verify_verifier_attestation(attestation: dict[str, Any], *, trust_policy: dict[str, Any], outcome_sha256: str, row_content_sha256: str) -> None:
    """Fail-closed verification against the pinned ``sources`` keyring in
    ``trust_policy`` -- the only way anything downstream may treat
    ``attestation`` as authentic. Requires an exact
    ``outcome_sha256``/``row_content_sha256`` bind, a ``success``
    disposition, and a signature that verifies against an active
    (registered, non-revoked) key."""
    require(isinstance(attestation, dict), "verifier attestation must be an object -- refusing")
    body = {k: v for k, v in attestation.items() if k != "signature_hex"}
    require(body.get("schema_version") == SCHEMA_VERSION, "verifier attestation schema_version mismatch -- refusing")
    require(body.get("outcome_sha256") == outcome_sha256, "verifier attestation is bound to a different outcome_sha256 -- refusing")
    require(body.get("row_content_sha256") == row_content_sha256, "verifier attestation is not bound to this row's content hash -- refusing")
    require(body.get("success") is True, "verifier attestation does not declare a successful invocation -- refusing")
    signature_hex = attestation.get("signature_hex")
    require(isinstance(signature_hex, str) and bool(signature_hex), "verifier attestation carries no signature -- refusing")
    try:
        trust.verify_with_policy(trust_policy, "sources", body.get("signer_key_id"), ATTESTATION_DOMAIN, body, signature_hex)
    except trust.TrustAuthorityError as exc:
        raise SourcesAuthorityError(f"verifier attestation failed signature verification -- refusing: {exc}") from exc
