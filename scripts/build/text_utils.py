"""Shared text utilities for V6 pipeline.

Common string operations used across fill_placeholders, dsl_to_mdx, and enrich.
"""

from __future__ import annotations

import re


def strip_stray_quotes(s: str) -> str:
    """Strip leading/trailing single quotes and whitespace from LLM-generated text.

    LLMs sometimes produce "'В'" or "зву́ки'" — this normalizes those artifacts.
    Internal apostrophes (пам'ятка) are preserved.
    """
    return s.strip().strip("'").strip()


_VOCAB_HINT_RE = re.compile(r"(.+?)\s*\((.+?)\)")


def parse_vocab_hint(hint: str | dict) -> tuple[str, str]:
    """Parse a vocabulary hint into (word, translation).

    Handles both v3 string format 'мама (mother)' and v4 dict format
    {word: 'мама', pos: 'noun', definition: 'mother'}.

    Returns (word, "") if no translation found.
    """
    if isinstance(hint, dict):
        word = hint.get("word", "")
        definition = hint.get("definition", "")
        return str(word).strip(), str(definition).strip()
    hint = str(hint).strip()
    match = _VOCAB_HINT_RE.match(hint)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return hint, ""
