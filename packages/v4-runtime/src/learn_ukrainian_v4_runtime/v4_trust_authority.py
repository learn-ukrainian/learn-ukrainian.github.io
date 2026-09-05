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
text, never held-out membership. The current versioned release selects the
reviewed v2 public keys. Frozen v1 remains historical data, outside the active
allowlist. Active public keys alone do not enable execution, qualify a unit,
or establish a completed row. The corresponding private signing keys
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
import re
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from learn_ukrainian_v4_runtime.resources import resource_root

SCHEMA_VERSION = "v4-trust-policy-v1"
KEYRING_ROLES = ("sources", "a3", "fleet_execution")

# Real lowercase-hex syntax, not merely "the right length" -- a 64-character
# string containing an uppercase letter or a non-hex character must never
# pass a "well-formed sha256/key/signature" check silently truncated to a
# length comparison (PR #7662 repair 5). Shared by every module that signs
# or verifies a payload under this trust authority.
HEX64_RE = re.compile(r"^[a-f0-9]{64}$")
SIGNATURE_HEX_RE = re.compile(r"^[a-f0-9]{128}$")
KEYRING_ENTRY_KEYS = frozenset({"public_key_hex", "revoked"})

_SELF_ROOT = resource_root()
DEFAULT_TRUST_POLICY_RELATIVE = "data/projects/open_model_data/trust/v4_trust_policy_v2.json"
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


def trust_policy_sha256(policy: dict[str, Any]) -> str:
    """The one digest every signed body/receipt binds as ``trust_policy_
    sha256`` (PR #7662 repair 6, Sol F2) -- the sha256 of the policy's own
    canonical-JSON content, never the raw bytes of whatever file (if any) it
    happened to be loaded from. A verifier always recomputes this from the
    exact ``trust_policy`` object it was itself given, so a receipt claiming
    one policy while being checked against a different one always disagrees
    (``TrustAuthorityError``), independent of file formatting/whitespace."""
    validate_trust_policy(policy)
    return sha256_text(canonical_json(policy))


def require_exact_keys(
    body: dict[str, Any], expected_keys: frozenset[str], label: str, *, error_cls: type[Exception] = TrustAuthorityError
) -> None:
    """Fail closed unless ``body`` declares exactly ``expected_keys`` -- a
    signature (even a freshly, correctly recomputed one) can never smuggle
    an unexpected extra field past a verifier that only checks the fields it
    happens to look at (PR #7662 repair 5). Shared by every signed-payload
    verifier in this project's three keyrings (``sources``/``a3``/
    ``fleet_execution``) so a row/source/membership/corpus-text field can
    never ride along in an artifact documented as text-free. ``error_cls``
    lets a cross-module caller (e.g. ``FleetExecutionError``) preserve its
    own error taxonomy rather than leaking this module's own exception type
    across the module boundary."""
    if not isinstance(body, dict):
        raise error_cls(f"{label} must be an object -- refusing")
    if set(body) != expected_keys:
        raise error_cls(f"{label} must declare exactly {sorted(expected_keys)} -- refusing (unexpected or missing key)")


def require_sha256_hex(value: Any, label: str, *, error_cls: type[Exception] = TrustAuthorityError) -> None:
    if not (isinstance(value, str) and bool(HEX64_RE.match(value))):
        raise error_cls(f"{label} must be a lowercase-hex sha256 digest -- refusing")


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
    require(
        isinstance(private_key_hex, str) and len(private_key_hex) == 64,
        "private_key_hex must be 32 raw bytes, hex-encoded -- refusing",
    )
    key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(private_key_hex))
    return key.sign(_domain_separated_message(domain, payload)).hex()


def verify(public_key_hex: str, domain: bytes, payload: dict[str, Any], signature_hex: str) -> None:
    """Fail-closed Ed25519 verification. Never trusts a caller's claim that
    a signature is valid -- always recomputes the domain-separated message
    from ``payload`` and checks it against ``signature_hex`` under
    ``public_key_hex``."""
    require(
        isinstance(public_key_hex, str) and bool(HEX64_RE.match(public_key_hex)),
        "public_key_hex must be 32 raw bytes, lowercase-hex-encoded -- refusing",
    )
    require(
        isinstance(signature_hex, str) and bool(SIGNATURE_HEX_RE.match(signature_hex)),
        "signature_hex must be 64 raw bytes, lowercase-hex-encoded -- refusing",
    )
    try:
        public_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex))
        public_key.verify(bytes.fromhex(signature_hex), _domain_separated_message(domain, payload))
    except (InvalidSignature, ValueError) as exc:
        raise TrustAuthorityError("signature verification failed -- refusing") from exc


# --- text-free trust policy (public keyrings only; no private key here) --


def empty_trust_policy() -> dict[str, Any]:
    """Historical mechanism-only policy and explicit non-production fallback.
    The fixed production loader never falls back to this empty policy."""
    return {"schema_version": SCHEMA_VERSION, "keyrings": {role: {} for role in KEYRING_ROLES}}


def validate_trust_policy(policy: dict[str, Any]) -> None:
    require(
        isinstance(policy, dict) and policy.get("schema_version") == SCHEMA_VERSION,
        "trust policy schema_version mismatch -- refusing",
    )
    keyrings = policy.get("keyrings")
    require(
        isinstance(keyrings, dict) and set(keyrings) == set(KEYRING_ROLES),
        "trust policy must declare exactly the sources/a3/fleet_execution keyrings -- refusing",
    )
    for role, keyring in keyrings.items():
        require(isinstance(keyring, dict), f"trust policy keyring {role!r} must be an object -- refusing")
        for key_id, entry in keyring.items():
            require(
                isinstance(key_id, str) and key_id, f"trust policy keyring {role!r} has a malformed key_id -- refusing"
            )
            require(
                isinstance(entry, dict), f"trust policy keyring {role!r} entry {key_id!r} must be an object -- refusing"
            )
            # Exact allowed key set: a keyring entry can never smuggle an
            # extra field (e.g. a label, a note) that downstream code might
            # later start trusting -- refusing here keeps every entry
            # provably text-free (PR #7662 repair 5).
            require(
                set(entry) == KEYRING_ENTRY_KEYS,
                f"trust policy keyring {role!r} entry {key_id!r} must declare exactly {sorted(KEYRING_ENTRY_KEYS)} -- refusing",
            )
            public_key_hex = entry.get("public_key_hex")
            require(
                isinstance(public_key_hex, str) and bool(HEX64_RE.match(public_key_hex)),
                f"trust policy keyring {role!r} entry {key_id!r} public_key_hex must be 32 raw bytes, lowercase-hex-encoded -- refusing",
            )
            require(
                isinstance(entry.get("revoked"), bool),
                f"trust policy keyring {role!r} entry {key_id!r} must declare revoked true/false -- refusing",
            )


def load_trust_policy(path: Path | None = DEFAULT_TRUST_POLICY_PATH) -> dict[str, Any]:
    """Load the text-free trust policy from ``path``. A missing file is the
    mechanism-only production default (an empty policy) -- never raises on
    a missing file, only on one that exists and is malformed."""
    if path is None or not path.is_file():
        return empty_trust_policy()
    policy = json.loads(path.read_text(encoding="utf-8"))
    validate_trust_policy(policy)
    return policy


# --- production trust-policy digest pinning (PR #7662 repair 6, Sol F2) ---
#
# The current reviewed policy's exact raw-byte sha256 -- pinned so
# that even a purely cosmetic one-byte drift (a stray space, a reordered
# key that happens to still parse) in the checked-in file refuses to load
# as "production" until a code-reviewed PR adds its new byte digest here.
# This is deliberately a *raw-byte* digest (not ``trust_policy_sha256``'s
# canonical-JSON digest below): a policy file is the one artifact in this
# project where even non-semantic byte drift must be caught, because
# nothing else reviews the file's exact bytes before this loader treats it
# as authoritative.
#
# Rotation: add the new version's file (e.g. ``v4_trust_policy_v2.json``)
# and its byte digest here in one code-reviewed PR; do not mutate this
# frozen v1 file in place. Revocation: remove a digest from this allowlist
# -- ``load_production_trust_policy`` then refuses that exact file content
# even though any signature it already produced remains cryptographically
# valid on its own terms (the receipt-level ``trust_policy_sha256`` check
# below is what makes that signature untrusted downstream).
PRODUCTION_TRUST_POLICY_FILE_DIGEST_ALLOWLIST: frozenset[str] = frozenset(
    {
        "847f14c4ef30ed1755612eef0614bcf606de2967b1ae6ac5c0ede2ade2b4ce72",  # v2, reviewed public keys
    }
)


def load_production_trust_policy() -> tuple[dict[str, Any], str]:
    """The only sanctioned way production code ever loads a trust policy:
    no argument, a fixed repository-relative path, and the raw file bytes'
    own sha256 must already be a code-reviewed entry in
    ``PRODUCTION_TRUST_POLICY_FILE_DIGEST_ALLOWLIST`` -- never a caller-
    selected path or a caller-constructed dict (PR #7662 repair 6, Sol F2;
    ``v4_a7_private_ledger``'s CLI no longer exposes ``--trust-policy`` for
    exactly this reason). Returns ``(policy, trust_policy_sha256(policy))``
    so every caller binds the exact digest it already verified, never one
    it merely trusts by convention."""
    path = DEFAULT_TRUST_POLICY_PATH
    require(path.is_file(), f"production trust-policy file is missing: {path} -- refusing")
    raw = path.read_bytes()
    file_digest = hashlib.sha256(raw).hexdigest()
    require(
        file_digest in PRODUCTION_TRUST_POLICY_FILE_DIGEST_ALLOWLIST,
        f"production trust-policy file digest {file_digest!r} is not in the code-reviewed active allowlist -- refusing (drifted, rotated out, or revoked)",
    )
    policy = json.loads(raw.decode("utf-8"))
    validate_trust_policy(policy)
    return policy, trust_policy_sha256(policy)


def require_trust_policy_binding(
    body: dict[str, Any], trust_policy: dict[str, Any], *, error_cls: type[Exception] = TrustAuthorityError
) -> None:
    """Every signed body this project verifies must declare the exact
    ``trust_policy_sha256`` of the policy it is being checked against --
    recomputed here from the live ``trust_policy`` object itself, never
    trusted from the body or from a separately-passed digest string. Catches
    both a stale/mismatched claim (cross-chain digest disagreement) and a
    body that omits the field entirely."""
    if not (isinstance(body.get("trust_policy_sha256"), str) and bool(HEX64_RE.match(body["trust_policy_sha256"]))):
        raise error_cls("signed body carries no well-formed trust_policy_sha256 -- refusing")
    expected = trust_policy_sha256(trust_policy)
    if body.get("trust_policy_sha256") != expected:
        raise error_cls(
            f"signed body trust_policy_sha256 does not match the trust policy being verified against -- refusing (expected {expected!r}, got {body.get('trust_policy_sha256')!r})"
        )


# --- production signing-key custody (PR #7662 repair 6) --------------------
#
# Root-owned, caller-inaccessible Hramatka path (operator-approved,
# ``batch_state/briefs/v4-real-slot-mechanism-repair-6-approval.md``):
# "Root-owned Hramatka signing credentials under the existing service
# account; operator-owned rotation/revocation." No production code path
# accepts a signing key through a public function argument, a CLI flag, a
# caller-selected environment variable, or a policy object -- this fixed,
# non-parameterizable path is the only place production ever reads one.
#
# Key/ACL provisioning is explicitly out of this mechanism repair's scope
# (see the repair-6 dispatch brief): mechanism-only production has NO key
# material at this path yet, so every role always refuses here until a
# future first-real-row PR provisions it. Tests never call this directly --
# they monkeypatch the module-level indirection point in each authority
# module (``v4_fleet_execution_authority._load_signing_key``, ``v4_sources_
# authority._load_signing_key``, ``v4_a3_reference_check._load_signing_
# key``) with an isolated ephemeral test key, never this real loader.
HRAMATKA_SIGNING_KEY_ROOT = Path("/run/credentials/hramatka-api.service/v4-signing-keys")


def load_production_signing_key(role: str) -> tuple[str, str]:
    """Read ``(private_key_hex, signer_key_id)`` for ``role`` from fixed,
    root-owned Hramatka custody. Refuses (fail closed, never a default key)
    when the role is unknown or the key files are not provisioned -- the
    only state mechanism-only production can be in today."""
    require(role in KEYRING_ROLES, f"unknown signing-key role {role!r} -- refusing")
    try:
        key_path = HRAMATKA_SIGNING_KEY_ROOT / f"{role}.key"
        key_id_path = HRAMATKA_SIGNING_KEY_ROOT / f"{role}.key_id"
        require(
            key_path.is_file() and key_id_path.is_file(),
            f"no production signing key is provisioned for role {role!r} at {HRAMATKA_SIGNING_KEY_ROOT} -- refusing "
            "(mechanism-only production; key/ACL provisioning is a first-real-row-PR prerequisite)",
        )
        for path in (key_path, key_id_path):
            require(not path.is_symlink() and not path.stat().st_mode & 0o077, "signing credential permissions -- refusing")
        private_key_hex = key_path.read_text(encoding="utf-8").strip()
        signer_key_id = key_id_path.read_text(encoding="utf-8").strip()
        require(
            bool(HEX64_RE.fullmatch(private_key_hex)), f"production signing key at {key_path} is not 32 raw bytes, hex-encoded -- refusing"
        )
        require(bool(signer_key_id), f"production signer key id at {key_id_path} is empty -- refusing")
        return private_key_hex, signer_key_id
    except OSError as exc:
        raise TrustAuthorityError("no production signing key is provisioned or accessible -- refusing") from exc


def resolve_public_key(policy: dict[str, Any], role: str, key_id: str) -> str:
    require(role in KEYRING_ROLES, f"unknown trust-policy role {role!r} -- refusing")
    require(isinstance(key_id, str) and key_id, "signer key_id must be a nonempty string -- refusing")
    validate_trust_policy(policy)
    keyring = policy["keyrings"][role]
    require(
        key_id in keyring,
        f"unknown/unregistered {role} signer key_id {key_id!r} -- refusing (mechanism-only production has no active key yet)",
    )
    entry = keyring[key_id]
    require(entry.get("revoked") is not True, f"{role} signer key_id {key_id!r} is revoked -- refusing")
    return entry["public_key_hex"]


def verify_with_policy(
    policy: dict[str, Any], role: str, key_id: str, domain: bytes, payload: dict[str, Any], signature_hex: str
) -> None:
    """Resolve ``key_id`` against the pinned ``role`` keyring in ``policy``
    (fail closed on unknown/revoked) and verify the signature against it."""
    public_key_hex = resolve_public_key(policy, role, key_id)
    verify(public_key_hex, domain, payload, signature_hex)


def build_test_trust_policy(
    *, revoked_key_ids: frozenset[str] = frozenset(), **role_keys: dict[str, str]
) -> dict[str, Any]:
    """An unmistakably test-only trust policy: pass e.g.
    ``fleet_execution={"test-key-1": public_key_hex}`` to populate one
    keyring. A role never passed stays empty (still refuses) -- callers must
    explicitly opt every role they want active into this, never a
    module-level production default. Never reachable from any default
    production code path."""
    policy = empty_trust_policy()
    for role, keys in role_keys.items():
        require(role in KEYRING_ROLES, f"unknown trust-policy role {role!r} -- refusing")
        policy["keyrings"][role] = {
            key_id: {"public_key_hex": public_key_hex, "revoked": key_id in revoked_key_ids}
            for key_id, public_key_hex in keys.items()
        }
    return policy
