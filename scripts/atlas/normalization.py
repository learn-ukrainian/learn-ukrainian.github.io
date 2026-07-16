"""Shared Atlas search/entry text normalization (Python side of the dual contract).

Must stay byte-compatible with ``site/src/lib/lexicon/normalize.ts``.
Vectors: ``scripts/atlas/normalization_vectors.json``.
"""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path

VECTORS_PATH = Path(__file__).with_name("normalization_vectors.json")
STRESS = "\u0301"


def normalize_atlas_text(value: str) -> str:
    """NFC → strip U+0301 → Ukrainian/Unicode lowercase → trim."""
    return unicodedata.normalize("NFC", value).replace(STRESS, "").lower().strip()


def normalize_slug_for_hash(slug: str) -> str:
    """NFC-normalize a URL slug before SHA-256 hashing (no case/stress mutation)."""
    return unicodedata.normalize("NFC", slug)


def load_normalization_vectors() -> list[dict[str, str]]:
    payload = json.loads(VECTORS_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema") != "atlas-normalization-vectors":
        raise ValueError(f"invalid normalization vectors at {VECTORS_PATH}")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError(f"normalization vectors missing cases: {VECTORS_PATH}")
    return cases
