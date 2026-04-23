"""Shared Unicode text helpers for Ukrainian-processing pipelines."""

from __future__ import annotations

import unicodedata

_UKRAINIAN_STRESS_MARK = "\u0301"


def strip_ukrainian_stress(text: str) -> str:
    """Remove Ukrainian acute stress marks without corrupting й/ї."""
    decomposed = unicodedata.normalize("NFD", text)
    without_stress = decomposed.replace(_UKRAINIAN_STRESS_MARK, "")
    return unicodedata.normalize("NFC", without_stress)
