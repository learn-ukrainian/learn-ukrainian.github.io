"""Shared JSON-object extraction helpers for agent CLI responses."""
from __future__ import annotations

import json


def _strip_leading_fence(text: str) -> str:
    """Strip one leading markdown code fence header when present."""
    if text.startswith("```json"):
        text = text[len("```json") :]
    elif text.startswith("```"):
        text = text[len("```") :]
    return text.lstrip()


def _find_object_end(text: str, start: int) -> int | None:
    """Return the matching closing brace for the object at ``start``."""
    depth = 0
    in_string = False
    escaped = False

    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index

    return None


def _excerpt(response: str, limit: int = 120) -> str:
    compact = " ".join(response.split())
    if not compact:
        return "<empty>"
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def extract_json_object(response: str) -> dict:
    """Extract the outermost JSON object from an agent CLI response.

    - Strips leading ```json or ``` fences
    - Uses brace-depth counting (NOT greedy regex) to find the outermost {...}
    - Raises ValueError with response excerpt on failure
    """
    text = _strip_leading_fence(response.strip())
    search_from = 0

    while True:
        start = text.find("{", search_from)
        if start < 0:
            break

        end = _find_object_end(text, start)
        if end is None:
            search_from = start + 1
            continue

        candidate = text[start : end + 1]
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            search_from = start + 1
            continue

        if isinstance(payload, dict):
            return payload
        search_from = start + 1

    raise ValueError(
        f"failed to extract JSON object from response excerpt: {_excerpt(response)!r}"
    )
