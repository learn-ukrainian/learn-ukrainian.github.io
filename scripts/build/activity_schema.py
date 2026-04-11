"""Shared helpers for activity YAML structural handling."""

from __future__ import annotations


def normalize_quiz_option_text(option: object) -> str | None:
    """Return a comparable quiz option text key for legacy and current shapes."""
    if isinstance(option, str):
        text = option
    elif isinstance(option, dict):
        text = option.get("text")
        if not isinstance(text, str):
            return None
    else:
        return None
    return " ".join(text.split())


def dedupe_quiz_options(options: list[object]) -> tuple[list[object], bool]:
    """Deduplicate quiz options by normalized text and merge dict correctness."""
    deduped: list[object] = []
    key_to_index: dict[str, int] = {}
    changed = False

    for option in options:
        key = normalize_quiz_option_text(option)
        if key is None:
            deduped.append(dict(option) if isinstance(option, dict) else option)
            continue

        existing_index = key_to_index.get(key)
        if existing_index is None:
            key_to_index[key] = len(deduped)
            deduped.append(dict(option) if isinstance(option, dict) else option)
            continue

        changed = True
        existing = deduped[existing_index]

        if isinstance(existing, dict):
            existing["correct"] = bool(existing.get("correct", False)) or _option_correct(option)
            continue

        if isinstance(option, dict) and _option_correct(option):
            deduped[existing_index] = {"text": existing, "correct": True}

    return deduped, changed


def _option_correct(option: object) -> bool:
    return isinstance(option, dict) and bool(option.get("correct", False))
