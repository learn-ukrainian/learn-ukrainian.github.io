"""``case_signal`` derivation for lexdata leaves (design r3 §4, §5.3 R1).

Values: ``lower`` (no capital letter), ``initial_cap`` (the first letter is a
capital and every other letter is lowercase, including a single capital),
``all_caps`` (two or more letters, all capitals) and ``mixed`` (anything
else, for example a capital after a hyphen). Computed over the letters of the
unstressed key, before case folding. A sentence-initial capital is still
``initial_cap``: R1 decides what that means, not this module.
"""

from __future__ import annotations

CASE_SIGNAL_VERSION = "1"
CASE_SIGNALS = frozenset({"lower", "initial_cap", "all_caps", "mixed"})


def derive_case_signal(key_unstressed: str) -> str | None:
    letters = [char for char in key_unstressed if char.isalpha()]
    if not letters:
        return None
    if not any(char.isupper() for char in letters):
        return "lower"
    if len(letters) > 1 and all(char.isupper() for char in letters):
        return "all_caps"
    if letters[0].isupper() and not any(char.isupper() for char in letters[1:]):
        return "initial_cap"
    return "mixed"
