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

Repair 6 (PR #7662, operator-approved architecture -- see ``batch_state/
briefs/v4-real-slot-mechanism-repair-6-approval.md``): the production
entrypoint (``issue_verifier_attestation``) now accepts an opaque
``invocation_id`` only. It resolves every evidentiary field from the
canonical Sources invocation store (``scripts.fleet_comms.v4_canonical_
authority_store``, written only by the Sources MCP wire handler after it
independently confirms the claimed fields are present in the tool's own
genuine result -- never a caller-created object), loads the signing key
from fixed, root-owned Hramatka custody (``v4_trust_authority.load_
production_signing_key``), and binds the pinned production trust-policy
digest into the signed body as ``trust_policy_sha256``. The prior
full-keyword signing engine is retained, unchanged, as the private
``_issue_verifier_attestation_from_evidence`` -- production never calls it
directly; only the opaque-ID wrapper and this module's own tests do.
"""

from __future__ import annotations

import contextlib
import re
from typing import Any

from learn_ukrainian_v4_runtime import v4_trust_authority as trust

# The one outcome this attester ever signs for -- never a caller-supplied
# argument (PR #7662 repair 6; see ``v4_a7_private_ledger.V4_SHA256``).
V4_SHA256 = "78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20"

SCHEMA_VERSION = "v4-sources-verifier-attestation-v1"
ATTESTATION_DOMAIN = b"v4-sources-verifier-attestation-v1"
VERIFIER_TOOL_PREFIX = "mcp__sources__"
SHA256_HEX_RE = re.compile(r"^[a-f0-9]{64}$")

# Exact allowed key set for a signed attestation body (PR #7662 repair 5) --
# a signature can never smuggle an extra field into an artifact documented
# as text-free.
ATTESTATION_KEYS = frozenset(
    {
        "schema_version",
        "outcome_sha256",
        "row_content_sha256",
        "identifier",
        "tool_id",
        "tool_version",
        "request_id",
        "tool_result_sha256",
        "lookup_ids",
        "success",
        "invocation_id",
        "signer_key_id",
        "trust_policy_sha256",
    }
)


class SourcesAuthorityError(ValueError):
    """A verifier attestation cannot be issued or verified safely."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SourcesAuthorityError(message)


def _issue_verifier_attestation_from_evidence(
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
    trust_policy_sha256: str,
) -> dict[str, Any]:
    """Issue a signed, text-free attestation that a real, sanctioned
    ``mcp__sources__*`` verifier tool invocation happened and produced the
    given result digest / immutable lookup ids. The only way any evidence
    receipt can ever become ``production_capable`` -- called only by the
    sources execution authority (which is expected to have actually run the
    invocation before calling this), never reachable from A7."""
    require(
        isinstance(tool_id, str) and tool_id.startswith(VERIFIER_TOOL_PREFIX),
        f"tool_id must be a sanctioned {VERIFIER_TOOL_PREFIX!r} verifier tool -- refusing",
    )
    require(isinstance(tool_version, str) and tool_version, "tool_version must be a nonempty string -- refusing")
    require(isinstance(identifier, str) and identifier, "identifier must be a nonempty string -- refusing")
    require(
        isinstance(row_content_sha256, str) and bool(SHA256_HEX_RE.match(row_content_sha256)),
        "row_content_sha256 is not a well-formed sha256 -- refusing",
    )
    require(
        isinstance(tool_result_sha256, str) and bool(SHA256_HEX_RE.match(tool_result_sha256)),
        "tool_result_sha256 is not a well-formed sha256 -- refusing",
    )
    require(
        isinstance(lookup_ids, list) and bool(lookup_ids) and all(isinstance(x, str) and x for x in lookup_ids),
        "lookup_ids must be a nonempty list of immutable identifiers -- refusing",
    )
    require(len(lookup_ids) == len(set(lookup_ids)), "lookup_ids must not contain duplicates -- refusing")
    require(isinstance(request_id, str) and request_id, "request_id must be a nonempty string -- refusing")
    require(isinstance(invocation_id, str) and invocation_id, "invocation_id must be a nonempty string -- refusing")
    require(isinstance(signer_key_id, str) and signer_key_id, "signer_key_id must be a nonempty string -- refusing")
    trust.require_sha256_hex(trust_policy_sha256, "trust_policy_sha256", error_cls=SourcesAuthorityError)

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
        "trust_policy_sha256": trust_policy_sha256,
    }
    signature_hex = trust.sign(signing_key_hex, ATTESTATION_DOMAIN, body)
    return {**body, "signature_hex": signature_hex}


# --- production entrypoint: opaque invocation_id only (PR #7662 repair 6) --


def _open_canonical_authority_store() -> Any:
    """Fixed, argument-free canonical-authority selection -- see
    ``v4_fleet_execution_authority._open_canonical_authority_store``. The
    Sources resolver is held to the identical rule: only the
    operator-approved live Fleet Comms PostgreSQL plane, never a
    caller-owned SQLite store, path, connection or authority override."""
    from learn_ukrainian_v4_runtime import v4_canonical_authority_store as v4_store

    return v4_store.open_production_authority_store()


def _resolve_sources_invocation(*, invocation_id: str) -> dict[str, Any] | None:
    """``None`` means the canonical authority holds no record for this
    opaque id; a non-PostgreSQL or unreachable authority raises. Both
    refuse before any key access."""
    from learn_ukrainian_v4_runtime import v4_canonical_authority_store as v4_store

    try:
        store = _open_canonical_authority_store()
    except v4_store.CanonicalAuthorityUnavailableError as exc:
        raise SourcesAuthorityError(
            f"canonical V4 Sources authority unavailable -- refusing (no key access): {exc}"
        ) from exc
    try:
        return store.resolve_v4_sources_invocation(invocation_id=invocation_id)
    except Exception as exc:
        raise SourcesAuthorityError("canonical V4 Sources authority read failed -- refusing (no key access)") from exc
    finally:
        with contextlib.suppress(Exception):
            store.close()


def _resolve_terminal_observation_for_invocation(record: dict[str, Any]) -> dict[str, Any] | None:
    """Join the Sources invocation to the terminal author observation.

    Row hash is obtained from the runner-owned author execution, never from
    a caller-supplied field on the invocation record.
    """
    from learn_ukrainian_v4_runtime import v4_canonical_authority_store as v4_store

    attempt_id = record.get("attempt_id")
    if not isinstance(attempt_id, str) or not attempt_id:
        return None
    try:
        store = _open_canonical_authority_store()
    except v4_store.CanonicalAuthorityUnavailableError:
        return None
    try:
        observation = v4_store.resolve_execution_observation_for_attempt(
            attempt_id=attempt_id, conn=store.connection, is_pg=store.authority.value == "pg"
        )
    except Exception:
        return None
    finally:
        with contextlib.suppress(Exception):
            store.close()
    if observation is None or observation.get("role") != "author":
        return None
    return observation


def _load_signing_key(role: str) -> tuple[str, str]:
    return trust.load_production_signing_key(role)


def issue_verifier_attestation(*, invocation_id: str) -> dict[str, Any]:
    """The only production-facing way to obtain a signed verifier
    attestation (PR #7662 repair 6, Sol minimal API). Accepts an opaque
    ``invocation_id`` only: resolves every evidentiary field from the
    canonical Sources invocation store (``_resolve_sources_invocation`` --
    an unknown invocation refuses before any key access), requires the
    canonical record to declare a successful invocation, loads the signing
    key from fixed Hramatka custody, and binds the pinned production
    trust-policy digest -- never from a caller-supplied argument."""
    require(
        isinstance(invocation_id, str) and bool(invocation_id), "invocation_id must be a nonempty string -- refusing"
    )
    record = _resolve_sources_invocation(invocation_id=invocation_id)
    require(record is not None, f"unknown invocation_id: {invocation_id!r} -- refusing (no key access)")
    require(
        record.get("success") is True,
        f"invocation {invocation_id!r} is not recorded as successful -- refusing (no key access)",
    )
    observation = _resolve_terminal_observation_for_invocation(record)
    require(
        observation is not None,
        f"invocation {invocation_id!r} has no terminal author execution to join -- refusing (no key access)",
    )
    _, trust_policy_sha256 = trust.load_production_trust_policy()
    require(observation.get("trust_policy_sha256") == trust_policy_sha256, "execution policy is not active -- refusing before key access")
    signing_key_hex, signer_key_id = _load_signing_key("sources")
    return _issue_verifier_attestation_from_evidence(
        signing_key_hex=signing_key_hex,
        signer_key_id=signer_key_id,
        outcome_sha256=V4_SHA256,
        row_content_sha256=observation["row_content_sha256"],
        identifier=record["identifier"],
        tool_id=record["tool_id"],
        tool_version=record["tool_version"],
        request_id=record["attempt_id"],
        tool_result_sha256=record["structured_result_sha256"],
        lookup_ids=list(record["lookup_ids"]),
        invocation_id=record["invocation_id"],
        trust_policy_sha256=trust_policy_sha256,
    )


def verify_verifier_attestation(
    attestation: dict[str, Any], *, trust_policy: dict[str, Any], outcome_sha256: str, row_content_sha256: str
) -> None:
    """Fail-closed verification against the pinned ``sources`` keyring in
    ``trust_policy`` -- the only way anything downstream may treat
    ``attestation`` as authentic. Requires an exact
    ``outcome_sha256``/``row_content_sha256`` bind, a ``success``
    disposition, a signature that verifies against an active (registered,
    non-revoked) key, and an exact ``trust_policy_sha256`` match against the
    policy actually being verified against."""
    require(isinstance(attestation, dict), "verifier attestation must be an object -- refusing")
    body = {k: v for k, v in attestation.items() if k != "signature_hex"}
    require(
        set(body) == ATTESTATION_KEYS,
        f"verifier attestation must declare exactly {sorted(ATTESTATION_KEYS)} -- refusing (unexpected or missing key)",
    )
    require(body.get("schema_version") == SCHEMA_VERSION, "verifier attestation schema_version mismatch -- refusing")
    require(
        body.get("outcome_sha256") == outcome_sha256,
        "verifier attestation is bound to a different outcome_sha256 -- refusing",
    )
    require(
        body.get("row_content_sha256") == row_content_sha256,
        "verifier attestation is not bound to this row's content hash -- refusing",
    )
    require(body.get("success") is True, "verifier attestation does not declare a successful invocation -- refusing")
    signature_hex = attestation.get("signature_hex")
    require(
        isinstance(signature_hex, str) and bool(signature_hex), "verifier attestation carries no signature -- refusing"
    )
    try:
        trust.verify_with_policy(
            trust_policy, "sources", body.get("signer_key_id"), ATTESTATION_DOMAIN, body, signature_hex
        )
    except trust.TrustAuthorityError as exc:
        raise SourcesAuthorityError(f"verifier attestation failed signature verification -- refusing: {exc}") from exc
    trust.require_trust_policy_binding(body, trust_policy, error_cls=SourcesAuthorityError)
