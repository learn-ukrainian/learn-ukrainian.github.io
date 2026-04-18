"""Shared helpers for deterministic first-occurrence fix application."""

from __future__ import annotations


def _normalize_with_spans(text: str) -> tuple[str, list[tuple[int, int]]]:
    """Collapse whitespace runs and map normalized chars back to original spans."""
    normalized_chars: list[str] = []
    spans: list[tuple[int, int]] = []
    idx = 0

    while idx < len(text):
        if text[idx].isspace():
            start = idx
            while idx < len(text) and text[idx].isspace():
                idx += 1
            if normalized_chars and idx < len(text):
                normalized_chars.append(" ")
                spans.append((start, idx))
            continue

        normalized_chars.append(text[idx])
        spans.append((idx, idx + 1))
        idx += 1

    return "".join(normalized_chars), spans


def apply_fix_pair(
    text: str,
    find: str,
    replace: str,
    *,
    tolerant_whitespace: bool = False,
) -> tuple[str, bool]:
    """Apply find→replace on first occurrence. Returns (new_text, applied).

    When tolerant_whitespace=True, falls back to whitespace-normalized
    search before giving up.
    """
    if find in text:
        return text.replace(find, replace, 1), True

    if not tolerant_whitespace:
        return text, False

    normalized_find, _ = _normalize_with_spans(find)
    if not normalized_find:
        return text, False

    normalized_text, spans = _normalize_with_spans(text)
    idx = normalized_text.find(normalized_find)
    if idx == -1:
        return text, False

    orig_start = spans[idx][0]
    orig_end = spans[idx + len(normalized_find) - 1][1]
    return text[:orig_start] + replace + text[orig_end:], True
