"""VESUM form-key normalization + hash-shard id (Python side of the dual
contract) — #5882 residual form-level VESUM attestation, Fable GO
SHARDED-EXACT design.

Must stay byte-compatible with ``site/src/lib/lexicon/vesum-form-key.ts``.
Both sides need the SAME key (so a form hashes to the SAME shard client-side
as it was written server-side) and the SAME hash (so the shard id math
agrees). Parity is golden-tested via ``vesum_form_key_vectors.json`` — both
languages consume the identical vector file (see
``tests/test_generate_vesum_form_shards.py`` and
``site/tests/unit/vesum-form-shard.test.ts``).
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.atlas.normalization import normalize_atlas_text

VECTORS_PATH = Path(__file__).with_name("vesum_form_key_vectors.json")

# VESUM's own data uses U+02BC (ʼ, MODIFIER LETTER APOSTROPHE) as the
# Ukrainian orthographic apostrophe. Pasted learner text commonly carries a
# typewriter apostrophe (U+0027) or a curly quote (U+2019, occasionally
# U+02BB) instead. Folding these variants to the canonical codepoint before
# hashing only ever WIDENS a match (never invents a wrong one — the rest of
# the key still has to agree), so it is a safe recall improvement.
_APOSTROPHE_VARIANTS = ("'", "’", "ʻ")  # ' ’ ʻ
_CANONICAL_APOSTROPHE = "ʼ"

VESUM_FORM_SHARD_COUNT = 4096

_FNV_OFFSET_BASIS = 0x811C9DC5
_FNV_PRIME = 0x01000193
_MASK_32 = 0xFFFFFFFF


def vesum_form_key(value: str) -> str:
    """Normalize a word to its VESUM form-shard lookup key."""
    normalized = normalize_atlas_text(value)
    for variant in _APOSTROPHE_VARIANTS:
        normalized = normalized.replace(variant, _CANONICAL_APOSTROPHE)
    return normalized


def fnv1a32(value: str) -> int:
    """FNV-1a 32-bit hash over the UTF-8 bytes of ``value``.

    Deterministic, dependency-free, and byte-identical to the TypeScript
    twin (``site/src/lib/lexicon/vesum-form-key.ts::fnv1a32``, which uses
    ``Math.imul`` for the same wrapping 32-bit multiply).
    """
    h = _FNV_OFFSET_BASIS
    for byte in value.encode("utf-8"):
        h ^= byte
        h = (h * _FNV_PRIME) & _MASK_32
    return h


def vesum_shard_id(form_key: str, shard_count: int = VESUM_FORM_SHARD_COUNT) -> str:
    """Shard id for an already-normalized form key — a zero-padded 3-digit
    hex string regardless of ``shard_count`` (so the width never has to be
    negotiated between the generator and the client)."""
    return format(fnv1a32(form_key) % shard_count, "03x")


def load_vesum_form_key_vectors() -> list[dict[str, str]]:
    payload = json.loads(VECTORS_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema") != "vesum-form-key-vectors":
        raise ValueError(f"invalid VESUM form-key vectors at {VECTORS_PATH}")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError(f"VESUM form-key vectors missing cases: {VECTORS_PATH}")
    return cases
