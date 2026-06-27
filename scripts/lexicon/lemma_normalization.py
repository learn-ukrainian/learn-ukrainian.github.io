"""Shared Word Atlas lemma normalization helpers."""

from __future__ import annotations

import unicodedata

ACUTE_STRESS_MARK = "\u0301"


def strip_acute_stress(value: str) -> str:
    """Remove only the combining acute stress mark from a lemma.

    Ukrainian letters such as й and ї decompose through other combining marks
    (U+0306, U+0308); those are part of the letter and must be preserved.
    """

    normalized = unicodedata.normalize("NFD", value)
    if ACUTE_STRESS_MARK not in normalized:
        return value
    return unicodedata.normalize("NFC", normalized.replace(ACUTE_STRESS_MARK, ""))
