"""Deterministic topology classification for normalized findings."""

from __future__ import annotations

import re
from typing import Any

PLAN_LEVEL_ERROR_CLASSES = {
    "vocab_density",
    "pedagogical_sequence",
    "scenario_grammar_misalignment",
    "plan_contradiction",
}

SECTION_RE = re.compile(r"##\s+([^(/`\n]+)")


def classify_topology(normalized_finding: dict[str, Any]) -> str:
    error_class = str(normalized_finding.get("error_class") or "")
    if error_class in PLAN_LEVEL_ERROR_CLASSES or normalized_finding.get("plan_level"):
        return "plan_level"

    location = str(normalized_finding.get("location") or "")
    issue = str(normalized_finding.get("issue") or "")
    fix = str(normalized_finding.get("fix") or "")
    combined = " ".join(part.lower() for part in (location, issue, fix) if part)

    mentioned_sections = {
        match.group(1).strip().lower()
        for text in (location, issue)
        for match in SECTION_RE.finditer(text)
    }
    if len(mentioned_sections) > 1:
        return "cross_section"

    cross_tokens = (
        "whole module",
        "multiple sections",
        "dialogue arc",
        "vocabulary pacing",
        "activity order",
        "budget distribution",
        "section order",
        "sequence",
    )
    if any(token in combined for token in cross_tokens):
        return "cross_section"

    local_tokens = (
        "sentence",
        "paragraph",
        "for example",
        "exact quote",
        "location: `",
    )
    if any(token in combined for token in local_tokens):
        return "local_to_prose"

    if " / " in location and len(mentioned_sections) == 1:
        return "local_to_prose"
    if location.count("`") >= 2 and len(mentioned_sections) <= 1:
        return "local_to_prose"

    if len(mentioned_sections) == 1 or location.strip().startswith("## "):
        return "section_local"

    return "cross_section"
