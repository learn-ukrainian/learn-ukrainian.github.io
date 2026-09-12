"""Deterministic section ownership for V7 upgrades; never authors lesson prose.

The last outline section closes the module. Earlier sections are packed in
outline order to the lesson word minimum; trailing unplanned source sections
stay with their preceding planned section. Introduction belongs to lesson one.
"""
from __future__ import annotations

import json
import math
import re
import unicodedata
from pathlib import Path

from jsonschema import Draft202012Validator

WORD_MINIMUM = 550
SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas/lesson-map.schema.json"


def _key(text: str) -> str:
    return unicodedata.normalize("NFC", unicodedata.normalize("NFD", text).replace("\u0301", "")).strip()


def source_sections(module_text: str) -> dict[str, str]:
    """Extract exact section bodies, excluding heading-like lines in fences."""
    sections = {"__intro__": ""}
    current = "__intro__"
    fence = None
    for line in module_text.splitlines(keepends=True):
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if marker:
            token = marker[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            sections[current] += line
            continue
        heading = re.match(r"^##\s+(.+?)\s*#*\s*$", line) if fence is None else None
        if heading:
            current = _key(heading[1])
            if current in sections:
                raise ValueError(f"Duplicate original section: {current}")
            sections[current] = ""
        else:
            sections[current] += line
    return sections


def validate_lesson_map(mapping: dict) -> None:
    """Raise ValueError for schema or cross-reference violations."""
    schema = json.loads(SCHEMA_PATH.read_text())
    errors = sorted(Draft202012Validator(schema).iter_errors(mapping), key=lambda e: str(e.path))
    if errors:
        raise ValueError("Invalid lesson map: " + "; ".join(e.message for e in errors))
    lessons = mapping["lessons"]
    numbers = [lesson["n"] for lesson in lessons]
    if numbers != list(range(1, len(lessons) + 1)):
        raise ValueError("Lesson numbers must be contiguous from one")
    if mapping["closes_module"] != numbers[-1]:
        raise ValueError("Only the final lesson closes the module")
    sections = [s for lesson in lessons for s in lesson["sections"]]
    if len(sections) != len(set(sections)):
        raise ValueError("Each section must belong to exactly one lesson")
    provenance = mapping["provenance"]
    ids = [p["new_id"] for p in provenance]
    original_keys = [(p["placement"], p["index"]) for p in provenance]
    if len(ids) != len(set(ids)) or len(original_keys) != len(set(original_keys)):
        raise ValueError("Duplicate activity provenance")
    if any(p["lesson"] not in numbers for p in provenance):
        raise ValueError("Provenance points to a missing lesson")
    for placement in ("inline", "workbook"):
        indexes = sorted(p["index"] for p in provenance if p["placement"] == placement)
        if indexes != list(range(len(indexes))):
            raise ValueError("Original activity indexes must be contiguous")
    if any(item["id"] not in ids for item in mapping["items_min_exempt"]):
        raise ValueError("Item exemption must reference an original activity")


def derive_lesson_map(plan: dict, module_text: str, activities: dict) -> dict:
    """Derive a map solely from outline order, word budgets, and source markers.

    Id-less workbook originals receive stable ``act-wN`` identities. Workbook
    order is allocated proportionally across lessons because originals have no
    section markers; this is placement, not a claim of semantic provenance.
    Explicit workbook ``lesson`` metadata, when provided, takes precedence.
    """
    outline = plan.get("content_outline")
    if not isinstance(outline, list) or not outline:
        raise ValueError("A non-empty content_outline is required")
    sections = source_sections(module_text)
    outline_names = [_key(entry["section"]) for entry in outline]
    if len(set(outline_names)) != len(outline_names):
        raise ValueError("Duplicate outline sections")
    source_names = list(sections)[1:]
    if [name for name in source_names if name in outline_names] != outline_names:
        raise ValueError("Original headings must contain every outline section in order")
    for entry in outline:
        budget = entry.get("words")
        if isinstance(budget, bool) or not isinstance(budget, int) or budget <= 0:
            raise ValueError("Outline words must be a positive integer")
    groups, pending, words = [], [], 0
    for entry, name in zip(outline[:-1], outline_names[:-1], strict=True):
        budget = entry["words"]
        pending.append(name)
        words += budget
        if words >= WORD_MINIMUM:
            groups.append(pending)
            pending, words = [], 0
    if pending:
        groups.append(pending)
    groups.append([outline_names[-1]])
    owners = {name: n for n, group in enumerate(groups, 1) for name in group}
    current_owner = 1
    for name in source_names:
        current_owner = owners.get(name, current_owner)
        owners[name] = current_owner
    lessons = []
    for n, group in enumerate(groups, 1):
        lessons.append({
            "n": n, "title": group[-1],
            "sections": [name for name in source_names if owners[name] == n],
            "minutes": 60, "word_target": WORD_MINIMUM,
            "activities": {"total": 10, "inline": [4, 6], "workbook": [6, 9]},
            "unverified_stress": [], "unverified_lemmas": [],
        })
    marker_owners = {}
    for name, body in sections.items():
        for activity_id in re.findall(r"<!--\s*INJECT_ACTIVITY:\s*([^\s>]+)\s*-->", body):
            if activity_id in marker_owners:
                raise ValueError(f"Duplicate inline activity marker: {activity_id}")
            marker_owners[activity_id] = owners.get(name, 1)
    provenance, exemptions = [], []
    for placement in ("inline", "workbook"):
        originals = activities.get(placement, [])
        for index, activity in enumerate(originals):
            activity_id = activity.get("id") or f"act-w{index + 1}"
            if placement == "inline":
                if not activity.get("id") or activity_id not in marker_owners:
                    raise ValueError("Every original inline activity requires an id and source marker")
                lesson = marker_owners.pop(activity_id)
            else:
                lesson = activity.get("lesson", math.ceil((index + 1) * len(lessons) / len(originals)))
            provenance.append({"placement": placement, "index": index, "new_id": activity_id, "lesson": lesson})
            counts = [len(activity[field]) for field in ("items", "questions", "pairs", "sentences", "words", "statements")
                      if isinstance(activity.get(field), list)]
            if counts and max(counts) < 6:
                exemptions.append({"id": activity_id, "reason": f"{max(counts)}-item original activity preserved from baseline"})
    if marker_owners:
        raise ValueError("Source marker has no original inline activity")
    mapping = {"lessons": lessons, "closes_module": len(lessons), "provenance": provenance,
               "items_min_exempt": exemptions, "proper_names": []}
    validate_lesson_map(mapping)
    return mapping
