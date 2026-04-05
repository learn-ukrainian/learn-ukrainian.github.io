"""Vocabulary hints normalization — handles both v3 and v4 plan formats.

v3 format: dict with {required: [...], recommended: [...], sight_words: [...]}
v4 format: list of {word: str, pos: str, definition: str} dicts

This module provides a single function to extract a flat word list from either format,
so callers don't need to check the type themselves.
"""

from __future__ import annotations


def extract_vocab_words(vocab_hints: dict | list | None) -> list[str]:
    """Extract a flat list of vocabulary words from plan vocabulary_hints.

    Handles both v3 (dict with required/recommended) and v4 (list of word dicts) formats.

    Returns:
        List of word strings (no POS, no definitions — just the words).
    """
    if not vocab_hints:
        return []

    if isinstance(vocab_hints, list):
        # v4 format: list of {word, pos, definition} dicts or plain strings
        words = []
        for item in vocab_hints:
            if isinstance(item, dict):
                word = item.get("word", "")
                if word:
                    words.append(word)
            elif isinstance(item, str):
                # Strip parenthetical translations: "слово (translation)" → "слово"
                words.append(item.split("(")[0].strip())
        return words

    if isinstance(vocab_hints, dict):
        # v3 format: {required: [...], recommended: [...], sight_words: [...]}
        words = []
        for category in ("required", "recommended", "sight_words"):
            items = vocab_hints.get(category, [])
            if not isinstance(items, list):
                continue
            for item in items:
                if isinstance(item, dict):
                    word = item.get("word", "")
                    if word:
                        words.append(word)
                elif isinstance(item, str):
                    words.append(item.split("(")[0].strip())
        return words

    return []


def format_vocab_for_prompt(vocab_hints: dict | list | None) -> str:
    """Format vocabulary hints for injection into LLM prompts.

    Returns a human-readable string listing vocabulary words.
    """
    words = extract_vocab_words(vocab_hints)
    if not words:
        return "(No vocabulary hints in plan)"
    return ", ".join(words)
