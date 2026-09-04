#!/usr/bin/env python3
"""V4 trust authority: the Ed25519 signature primitives and text-free
trust-policy contract shared by every authenticated crossing the V4
real-slot mechanism relies on (PR #7662 repair 4, designated-advisor
``GO_REPAIR``).

Three distinct authorities, three distinct keyrings, one shared mechanism:

* ``sources`` -- the distinct sources execution authority that alone may
  issue a production-capable verifier attestation (see
  ``v4_sources_authority.py``, consumed by ``v4_a7_evidence_binder.py``).
* ``a3`` -- A3's own reference-check signature and private-replay
  attestation authority (see the signing/verification additions in
  ``v4_a3_reference_check.py``).
* ``fleet_execution`` -- the fleet execution attester that alone may sign an
  author/reviewer execution receipt (see ``v4_fleet_execution_authority.py``).

A7 (and every other caller in this project) never holds a private signing
key. It only ever *verifies* a signature against a public key pinned in a
checked-in, text-free trust-policy artifact (``TrustPolicy`` below) --
counts/ids/hex-encoded public keys only, never a private key, never source
text, never held-out membership. Mechanism-only production ships with an
*empty* trust policy (no active key in any of the three keyrings): every
production-capable receipt therefore refuses closed until a future real-row
PR provisions real public keys here. The corresponding private signing keys
never enter git, prompts, CLI arguments, or logs -- they remain on Hramatka
under hardened custody, held by whichever process actually plays the
sources/A3/fleet-execution role.

Every domain (a fixed, distinct ``bytes`` label per signed payload shape --
``ATTESTATION_DOMAIN``/``AUTHOR_DOMAIN``/etc. in the modules that use this
one) is prepended to the canonical JSON payload before signing, so a
signature over one payload shape can never be replayed as if it were a
signature over a different one, even if the two payloads happen to share
some fields.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

SCHEMA_VERSION = "v4-trust-policy-v1"
KEYRING_ROLES = ("sources", "a3", "fleet_execution")

_SELF_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_TRUST_POLICY_RELATIVE = "data/projects/open_model_data/trust/v4_trust_policy_v1.json"
DEFAULT_TRUST_POLICY_PATH = _SELF_ROOT / DEFAULT_TRUST_POLICY_RELATIVE


class TrustAuthorityError(ValueError):
    """A signature, key, or trust-policy artifact is not safe to trust."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise TrustAuthorityError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _domain_separated_message(domain: bytes, payload: dict[str, Any]) -> bytes:
    require(isinstance(domain, bytes) and bool(domain), "signing domain must be a nonempty bytes label -- refusing")
    require(isinstance(payload, dict), "signed payload must be an object -- refusing")
    return domain + b"\x00" + canonical_json(payload).encode("utf-8")


# --- Ed25519 primitives -------------------------------------------------


def generate_test_keypair() -> tuple[str, str]:
    """Ephemeral Ed25519 keypair for tests only -- never a production key.
    Returns ``(private_key_hex, public_key_hex)``, each 32 raw bytes,
    hex-encoded."""
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    return private_key.private_bytes_raw().hex(), public_key.public_bytes_raw().hex()


def sign(private_key_hex: str, domain: bytes, payload: dict[str, Any]) -> str:
    """Sign ``payload`` under ``domain`` separation with the given raw
    Ed25519 private key (hex-encoded). Only ever called by the distinct
    authority that actually owns the private key (or, in a test, an
    ephemeral key generated fresh under ``tmp_path``) -- never by a
    production consumer of the resulting signature."""
    require(isinstance(private_key_hex, str) and len(private_key_hex) == 64, "private_key_hex must be 32 raw bytes, hex-encoded -- refusing")
    key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(private_key_hex))
    return key.sign(_domain_separated_message(domain, payload)).hex()


def verify(public_key_hex: str, domain: bytes, payload: dict[str, Any], signature_hex: str) -> None:
    """Fail-closed Ed25519 verification. Never trusts a caller's claim that
    a signature is valid -- always recomputes the domain-separated message
    from ``payload`` and checks it against ``signature_hex`` under
    ``public_key_hex``."""
    require(isinstance(public_key_hex, str) and len(public_key_hex) == 64, "public_key_hex must be 32 raw bytes, hex-encoded -- refusing")
    require(isinstance(signature_hex, str) and len(signature_hex) == 128, "signature_hex must be 64 raw bytes, hex-encoded -- refusing")
    try:
        public_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex))
        public_key.verify(bytes.fromhex(signature_hex), _domain_separated_message(domain, payload))
    except (InvalidSignature, ValueError) as exc:
        raise TrustAuthorityError("signature verification failed -- refusing") from exc


# --- text-free trust policy (public keyrings only; no private key here) --


def empty_trust_policy() -> dict[str, Any]:
    """The mechanism-only production default: every keyring empty, so every
    production-capable receipt refuses closed until real public keys are
    provisioned by a future real-row PR."""
    return {"schema_version": SCHEMA_VERSION, "keyrings": {role: {} for role in KEYRING_ROLES}}


def validate_trust_policy(policy: dict[str, Any]) -> None:
    require(isinstance(policy, dict) and policy.get("schema_version") == SCHEMA_VERSION, "trust policy schema_version mismatch -- refusing")
    keyrings = policy.get("keyrings")
    require(isinstance(keyrings, dict) and set(keyrings) == set(KEYRING_ROLES), "trust policy must declare exactly the sources/a3/fleet_execution keyrings -- refusing")
    for role, keyring in keyrings.items():
        require(isinstance(keyring, dict), f"trust policy keyring {role!r} must be an object -- refusing")
        for key_id, entry in keyring.items():
            require(isinstance(key_id, str) and key_id, f"trust policy keyring {role!r} has a malformed key_id -- refusing")
            require(isinstance(entry, dict), f"trust policy keyring {role!r} entry {key_id!r} must be an object -- refusing")
            public_key_hex = entry.get("public_key_hex")
            require(isinstance(public_key_hex, str) and len(public_key_hex) == 64, f"trust policy keyring {role!r} entry {key_id!r} public_key_hex must be 32 raw bytes, hex-encoded -- refusing")
            require(isinstance(entry.get("revoked"), bool), f"trust policy keyring {role!r} entry {key_id!r} must declare revoked true/false -- refusing")


def load_trust_policy(path: Path | None = DEFAULT_TRUST_POLICY_PATH) -> dict[str, Any]:
    """Load the text-free trust policy from ``path``. A missing file is the
    mechanism-only production default (an empty policy) -- never raises on
    a missing file, only on one that exists and is malformed."""
    if path is None or not path.is_file():
        return empty_trust_policy()
    policy = json.loads(path.read_text(encoding="utf-8"))
    validate_trust_policy(policy)
    return policy


def resolve_public_key(policy: dict[str, Any], role: str, key_id: str) -> str:
    require(role in KEYRING_ROLES, f"unknown trust-policy role {role!r} -- refusing")
    require(isinstance(key_id, str) and key_id, "signer key_id must be a nonempty string -- refusing")
    validate_trust_policy(policy)
    keyring = policy["keyrings"][role]
    require(key_id in keyring, f"unknown/unregistered {role} signer key_id {key_id!r} -- refusing (mechanism-only production has no active key yet)")
    entry = keyring[key_id]
    require(entry.get("revoked") is not True, f"{role} signer key_id {key_id!r} is revoked -- refusing")
    return entry["public_key_hex"]


def verify_with_policy(policy: dict[str, Any], role: str, key_id: str, domain: bytes, payload: dict[str, Any], signature_hex: str) -> None:
    """Resolve ``key_id`` against the pinned ``role`` keyring in ``policy``
    (fail closed on unknown/revoked) and verify the signature against it."""
    public_key_hex = resolve_public_key(policy, role, key_id)
    verify(public_key_hex, domain, payload, signature_hex)


def build_test_trust_policy(*, revoked_key_ids: frozenset[str] = frozenset(), **role_keys: dict[str, str]) -> dict[str, Any]:
    """An unmistakably test-only trust policy: pass e.g.
    ``fleet_execution={"test-key-1": public_key_hex}`` to populate one
    keyring. A role never passed stays empty (still refuses) -- callers must
    explicitly opt every role they want active into this, never a
    module-level production default. Never reachable from any default
    production code path."""
    policy = empty_trust_policy()
    for role, keys in role_keys.items():
        require(role in KEYRING_ROLES, f"unknown trust-policy role {role!r} -- refusing")
        policy["keyrings"][role] = {key_id: {"public_key_hex": public_key_hex, "revoked": key_id in revoked_key_ids} for key_id, public_key_hex in keys.items()}
    return policy
