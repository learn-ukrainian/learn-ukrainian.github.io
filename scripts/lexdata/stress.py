"""Stress-mark policy for lexdata keys (design r3 §4, §6.1 "Stress").

Policy:
- U+0301 (combining acute) is the stress mark. It must follow exactly one
  Cyrillic vowel letter; anything else is ``stress_invalid`` and the span is
  refused, never repaired.
- U+0300 (combining grave) is accepted on a vowel like U+0301 but never kept
  in any key; ``key_stressed`` carries U+0301 only.
- Checks run on the canonical decomposition, so precomposed letters that hide
  an acute (for example U+0453 = г + U+0301) are seen for what they are.
"""

from __future__ import annotations

import unicodedata

STRESS_POLICY_VERSION = "1"

ACUTE = "́"
GRAVE = "̀"
STRESS_MARKS = frozenset({ACUTE, GRAVE})
# Ukrainian vowel letters, as composed characters.
VOWELS = frozenset("аеєиіїоуюяАЕЄИІЇОУЮЯ")


def _clusters(text: str) -> list[tuple[str, list[str]]]:
    """Split a decomposed string into (base, combining marks) clusters."""
    out: list[tuple[str, list[str]]] = []
    for char in unicodedata.normalize("NFD", text):
        if unicodedata.combining(char) and out:
            out[-1][1].append(char)
        else:
            out.append((char, []))
    return out


def stress_is_valid(text: str) -> bool:
    """True when every stress mark follows one Cyrillic vowel and none repeats."""
    for base, marks in _clusters(text):
        if base in STRESS_MARKS:  # a stress mark with no base letter
            return False
        stress = [mark for mark in marks if mark in STRESS_MARKS]
        if not stress:
            continue
        if len(stress) > 1:
            return False
        letter = unicodedata.normalize("NFC", base + "".join(m for m in marks if m not in STRESS_MARKS))
        if letter not in VOWELS:
            return False
    return True


def has_stress(text: str) -> bool:
    return any(char in STRESS_MARKS for char in unicodedata.normalize("NFD", text))


def _strip(text: str, marks: frozenset[str]) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    return unicodedata.normalize("NFC", "".join(char for char in decomposed if char not in marks))


def stressed_key(text: str) -> str:
    """Keep U+0301, drop U+0300 (callers validate first)."""
    return _strip(text, frozenset({GRAVE}))


def unstressed_key(text: str) -> str:
    return _strip(text, STRESS_MARKS)


def policy_contents() -> dict[str, object]:
    return {
        "version": STRESS_POLICY_VERSION,
        "stress_marks": sorted(f"U+{ord(m):04X}" for m in STRESS_MARKS),
        "kept_in_key_stressed": [f"U+{ord(ACUTE):04X}"],
        "vowels": "".join(sorted(VOWELS)),
    }
