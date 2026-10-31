"""The two shapes a level word-store record takes (#12185).

A lexical record carries `lemma`, `pos` and `forms`. A `kind: formula` record (formulas.py, #9692) carries
printed `text` and `parts` instead and has none of those three. A consumer reads the store through these
helpers rather than assuming the lexical shape. This module imports nothing so any consumer may use it.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def is_formula(record: Any) -> bool:
    return isinstance(record, dict) and record.get("kind") == "formula"


def lexical(records: Iterable[Any]) -> list[dict]:
    """The lexical records among `records`; for consumers that need a lemma, a part of speech or forms."""
    return [r for r in records if isinstance(r, dict) and not is_formula(r)]


def printed(record: dict) -> str | None:
    """How the store prints the record: a formula's text, a lexical record's lemma (None if it has none)."""
    return record.get("text") if is_formula(record) else record.get("lemma")
