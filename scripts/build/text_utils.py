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


def parse_vocab_hint(hint: str) -> tuple[str, str]:
    """Parse a vocabulary hint like 'мама (mother)' into (word, translation).

    Returns (word, "") if no translation in parentheses.
    """
    hint = str(hint).strip()
    match = _VOCAB_HINT_RE.match(hint)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return hint, ""
