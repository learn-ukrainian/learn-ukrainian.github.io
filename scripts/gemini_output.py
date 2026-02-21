"""
Gemini output extraction utilities.

Pure functions for extracting delimited content from Gemini CLI output.
Strips thinking tokens and other noise, returning only the structured
content between ===TAG_START=== / ===TAG_END=== delimiters.

Usage:
    from gemini_output import extract_delimited, extract_yaml, validate_output

    text = extract_delimited(raw_output, "CONTENT")
    data = extract_yaml(raw_output, "ACTIVITIES")
    result = validate_output(raw_output, expected_tags=["CONTENT", "ACTIVITIES"])
"""

import re
from typing import Optional

import yaml

# Phase → expected delimiter tags
PHASE_TAGS: dict[int | str, list[str]] = {
    0: ["RESEARCH"],
    1: ["META_OUTLINE"],
    2: ["CONTENT"],
    "2-section": ["SECTION_CONTENT"],
    "2-summary": ["SUMMARY"],
    3: ["ACTIVITIES", "VOCABULARY"],
    5: ["REVIEW"],
    6: ["REVIEW"],
    "fix": ["CONTENT", "ACTIVITIES", "VOCABULARY", "CHANGES"],
    "fix-content": ["CONTENT", "CHANGES"],
    "fix-activities": ["ACTIVITIES", "VOCABULARY", "CHANGES"],
    "7-final-review": ["FINAL_REVIEW"],
}

# All known tags (union of all phase tags)
ALL_TAGS: list[str] = sorted(
    {tag for tags in PHASE_TAGS.values() for tag in tags}
)

# Legacy end markers (for backward compat with older outputs)
_LEGACY_END_MARKERS = ["---END---"]


def extract_delimited(text: str, tag: str) -> Optional[str]:
    """Extract content between ===TAG_START=== and ===TAG_END=== delimiters.

    Also supports ===ARTIFACT_START=== as a fallback if the specific tag is missing.

    Args:
        text: Raw Gemini output (may contain thinking tokens, noise).
        tag: Delimiter tag name (e.g., "CONTENT", "ACTIVITIES").

    Returns:
        Stripped content between delimiters, or None if not found.
    """
    # 1. Try specific semantic tag (preferred)
    # Use findall + take LAST match: Gemini often echoes the template's
    # delimiters before producing its own output, so the first match may
    # be the template echo rather than the real content.
    # Tolerate optional whitespace around delimiters (Gemini sometimes
    # adds spaces or doesn't put them on a clean line).
    pattern = re.compile(
        rf"\s*==={re.escape(tag)}_START===\s*\n?(.*?)\n?\s*==={re.escape(tag)}_END===\s*",
        re.DOTALL,
    )
    matches = pattern.findall(text)
    if matches:
        return matches[-1].strip()

    # 2. Try generic ARTIFACT tag (fallback) — also take last match
    pattern_artifact = re.compile(
        r"\s*===ARTIFACT_START===\s*\n?(.*?)\n?\s*===ARTIFACT_END===\s*",
        re.DOTALL,
    )
    artifact_matches = pattern_artifact.findall(text)
    if artifact_matches:
        return artifact_matches[-1].strip()

    return None


def extract_yaml(text: str, tag: str) -> Optional[dict | list]:
    """Extract delimited content and parse as YAML.

    Args:
        text: Raw Gemini output.
        tag: Delimiter tag name.

    Returns:
        Parsed YAML (dict or list), or None if not found or parse error.
    """
    content = extract_delimited(text, tag)
    if content is None:
        return None
    try:
        return yaml.safe_load(content)
    except yaml.YAMLError:
        return None


def has_complete_pair(text: str, tag: str) -> bool:
    """Check if text contains a complete START/END delimiter pair for tag.
    
    Checks for both specific ===TAG_START=== and generic ===ARTIFACT_START===.
    """
    if f"==={tag}_START===" in text and f"==={tag}_END===" in text:
        return True
    return "===ARTIFACT_START===" in text and "===ARTIFACT_END===" in text


def find_complete_pairs(text: str, tags: list[str]) -> list[str]:
    """Return tags that have complete START/END pairs in text."""
    return [tag for tag in tags if has_complete_pair(text, tag)]


def find_missing_pairs(text: str, tags: list[str]) -> list[str]:
    """Return tags that are missing complete START/END pairs.

    Useful for truncation detection: if a tag has START but no END,
    the output was likely truncated.
    """
    return [tag for tag in tags if not has_complete_pair(text, tag)]


def has_any_end_marker(text: str) -> bool:
    """Check if text contains any known end delimiter.

    Includes both standard ===TAG_END=== markers and legacy ---END---
    markers for backward compatibility.
    """
    for tag in ALL_TAGS:
        if f"==={tag}_END===" in text:
            return True
    for marker in _LEGACY_END_MARKERS:
        if marker in text:
            return True
    return False


def validate_output(
    text: str, expected_tags: list[str]
) -> dict:
    """Validate Gemini output against expected delimiter tags.

    Args:
        text: Raw Gemini output.
        expected_tags: Tags that should be present (from PHASE_TAGS).

    Returns:
        Dict with keys:
            complete: list[str]   - tags with complete pairs
            missing: list[str]    - tags without complete pairs
            truncated: list[str]  - tags with START but no END (likely truncated)
            valid: bool           - True if all expected tags are complete
    """
    complete = find_complete_pairs(text, expected_tags)
    missing = find_missing_pairs(text, expected_tags)

    # Detect truncation: tag has START but no END
    truncated = [
        tag for tag in missing
        if f"==={tag}_START===" in text
    ]

    return {
        "complete": complete,
        "missing": missing,
        "truncated": truncated,
        "valid": len(missing) == 0,
    }
