"""Validate a lesson draft (``lesson-draft-v1``) — check 1 of the writer contract (#8431 r3 §7).

Two layers, both deterministic and both plan-free:

1. **Schema** — ``schemas/lesson-draft-<level>-v1.schema.json`` (generated; see
   :mod:`gen_draft_schemas`), with the per-type activity definitions of
   ``schemas/activities-<level>.schema.json`` reachable by ``$ref``.
2. **Code checks** — the invariants JSON Schema cannot express, each named in
   :data:`CODE_CHECKS` so that a failure report says which layer found it.

What this proves is the draft's shape and its declared gaps (contract principle 5). Whether the
step ids, activity ids, ``dialogue.step`` and the evidence-use set arithmetic match the *plan*
is the structure gate (§2, engine E3); this module only takes the plan's activity ``type`` map
when the caller has it, to bind each activity's payload to its exact per-type shape.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from jsonschema import Draft7Validator, Draft202012Validator
from jsonschema.exceptions import best_match
from referencing import Registry, Resource

from scripts.build.fresh.gen_draft_schemas import (
    LEVELS,
    META_KEYS,
    SCHEMAS_DIR,
    draft_schema_filename,
    level_activity_types,
)

SCHEMA_BASE_URI = "https://learn-ukrainian.github.io/schemas/"

#: The inline-markup contract (#8431 r3 §1d, §6) and the accent ban (§3), as the schema's text
#: pattern states it: runs of characters without braces or combining accents, gloss references
#: ``{{gloss:W-<digits>}}`` and quoted-term spans ``{{uk:…}}`` whose content has neither braces
#: nor accents. A token cannot carry both markups; spans do not nest; a stray brace fails.
INLINE_MARKUP_RE = re.compile(r"^(?:[^{}\u0300\u0301]|\{\{gloss:W-[0-9]+\}\}|\{\{uk:[^{}\u0300\u0301]+\}\})*$")
#: Inside an activity payload the level schemas keep their own blank markers — `____`, `{answer}`
#: and `{gap}` in fill-in / cloze sentences, `{{N}}` numbered cloze blanks — so there the rule is:
#: every `{{…}}` token is a gloss reference, a quoted-term span or a numbered blank, single-brace
#: markers are the level schema's, nothing nests, and the accent ban still holds (E1 choice; the
#: contract fixes the markup for writer text fields and leaves item syntax to the level schemas).
ACTIVITY_MARKUP_RE = re.compile(
    r"^(?:[^{}\u0300\u0301]|\{[^{}\u0300\u0301]*\}|\{\{gloss:W-[0-9]+\}\}|\{\{uk:[^{}\u0300\u0301]+\}\}|\{\{[0-9]+\}\})*$"
)
GLOSS_RE = re.compile(r"\{\{gloss:(W-[0-9]+)\}\}")
UK_SPAN_RE = re.compile(r"\{\{uk:([^{}\u0300\u0301]+)\}\}")
COMBINING_ACCENTS = ("\u0300", "\u0301")

#: The invariants validated by code, not by the schema (contract §2, §3, §4, §1c).
CODE_CHECKS: tuple[tuple[str, str], ...] = (
    ("no_combining_accent", "no U+0300/U+0301 in any string of the draft, activity items included (§3)"),
    ("inline_markup", "every string of the draft matches INLINE_MARKUP_RE; activity payload strings match ACTIVITY_MARKUP_RE (§1d, §6)"),
    ("step_ids_unique", "step ids are unique within the draft"),
    ("activity_ids_unique", "activity ids are unique within the draft"),
    ("activity_ref_declared", "every `activity` block and consolidation entry names an id declared in `activities`"),
    ("activity_declared_used", "every declared activity is placed once — in a step or in consolidation"),
    ("dialogue_block_once", "a `dialogue` block appears at most once, and exactly when top-level `dialogue` is present"),
    ("bilingual_equal_length", "`bilingual.uk` and `bilingual.en` have equal length (§2)"),
    ("translation_en_length", "`dialogue.translation_en` has one entry per line, or is absent (§2)"),
    ("gap_steps_exist", "every `gaps[].step` is a step of the draft (§4)"),
    ("gap_steps_empty", "the steps with empty blocks are exactly the steps named in `gaps` (§4)"),
    ("activity_items_per_type", "given the plan's type map, each activity's payload validates against its `<type>-<level>` definition (§1c)"),
)


@dataclass(frozen=True)
class DraftError:
    """One machine-readable failure of check 1: which check, where, why."""

    check: str
    path: str
    reason: str

    def as_dict(self) -> dict[str, str]:
        return {"check": self.check, "path": self.path, "reason": self.reason}


@dataclass
class DraftValidationError(ValueError):
    errors: list[DraftError] = field(default_factory=list)

    def __str__(self) -> str:  # pragma: no cover - message only
        return "; ".join(f"{e.check}@{e.path}: {e.reason}" for e in self.errors)


def _pointer(parts: Iterator | list) -> str:
    return "/" + "/".join(str(p) for p in parts)


@lru_cache(maxsize=8)
def _registry_for(schemas_dir: str) -> Registry:
    """A registry over every ``schemas/*.json`` file, keyed by ``$id`` and by base-relative name."""
    root = Path(schemas_dir)

    def retrieve(uri: str) -> Resource:
        name = uri.split("#", 1)[0].rsplit("/", 1)[-1]
        path = root / name
        if not path.exists():
            raise LookupError(f"no schema file for {uri!r} under {root}")
        with path.open(encoding="utf-8") as handle:
            return Resource.from_contents(json.load(handle))

    return Registry(retrieve=retrieve)


def load_schema(name: str, schemas_dir: Path | None = None) -> dict:
    with ((schemas_dir or SCHEMAS_DIR) / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def draft_validator(level: str | None, schemas_dir: Path | None = None) -> Draft202012Validator:
    """The 2020-12 validator for the level's draft schema (or the level-agnostic one)."""
    schemas_dir = schemas_dir or SCHEMAS_DIR
    schema = load_schema(draft_schema_filename(level), schemas_dir)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, registry=_registry_for(str(schemas_dir)))


def activity_definitions(level: str, schemas_dir: Path | None = None) -> dict[str, dict]:
    """``{type: definition}`` for the level allowlist, resolved from the level schema."""
    level_schema = load_schema(f"activities-{level}.schema.json", schemas_dir)
    types = level_activity_types(level, level_schema)
    return {t: level_schema["definitions"][f"{t}-{level}"] for t in types}


def activity_payload_schema(definition: dict) -> dict:
    """The per-type definition with the meta keys removed — the shape the draft's payload must fit.

    ``type``, ``placement``, ``title``, ``notes`` and the gate flags belong to the plan or the
    engine (contract §2); ``id`` and ``instruction`` are validated by the draft schema.
    """
    properties = {k: v for k, v in definition.get("properties", {}).items() if k not in META_KEYS}
    derived: dict = {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": [k for k in definition.get("required", []) if k not in META_KEYS],
    }
    for keyword in ("allOf", "anyOf", "oneOf", "if", "then", "else", "not", "dependentRequired"):
        if keyword in definition:
            derived[keyword] = definition[keyword]
    return derived


def strings_in(node: object, path: str = "") -> Iterator[tuple[str, str]]:
    """Yield ``(json_pointer, string)`` for every string in the draft (keys excluded)."""
    if isinstance(node, str):
        yield path, node
    elif isinstance(node, list):
        for index, item in enumerate(node):
            yield from strings_in(item, f"{path}/{index}")
    elif isinstance(node, dict):
        for key, value in node.items():
            yield from strings_in(value, f"{path}/{key}")


def _markup_re_for(path: str) -> re.Pattern[str]:
    """The strict writer-text regex, or the payload regex under ``/activities/<i>/<payload key>``."""
    parts = path.split("/")
    if len(parts) > 3 and parts[1] == "activities" and parts[3] not in ("id", "instruction"):
        return ACTIVITY_MARKUP_RE
    return INLINE_MARKUP_RE


def _schema_errors(draft: object, level: str | None, schemas_dir: Path | None) -> list[DraftError]:
    validator = draft_validator(level, schemas_dir)
    errors = sorted(validator.iter_errors(draft), key=lambda e: [str(p) for p in e.absolute_path])
    out: list[DraftError] = []
    for error in errors:
        chosen = best_match([error]) or error
        out.append(DraftError("schema", _pointer(chosen.absolute_path), chosen.message))
    return out


def _code_errors(draft: dict, level: str | None, schemas_dir: Path | None, activity_types: Mapping[str, str] | None) -> list[DraftError]:
    errors: list[DraftError] = []

    for path, text in strings_in(draft):
        if any(accent in unicodedata.normalize("NFD", text) for accent in COMBINING_ACCENTS):
            errors.append(DraftError("no_combining_accent", path, "combining accent (U+0300/U+0301) in a draft string; the writer writes plain text (§3)"))
        elif not _markup_re_for(path).fullmatch(text):
            errors.append(DraftError("inline_markup", path, "string violates the inline-markup contract: only {{gloss:W-…}} and {{uk:…}} (plus the level schema's blank markers inside an activity payload), no nesting, no stray brace"))

    steps = draft.get("steps", [])
    step_ids = [s.get("id") for s in steps]
    for step_id in sorted({s for s in step_ids if step_ids.count(s) > 1}):
        errors.append(DraftError("step_ids_unique", "/steps", f"step id {step_id!r} appears more than once"))

    activities = draft.get("activities", [])
    activity_ids = [a.get("id") for a in activities]
    for activity_id in sorted({a for a in activity_ids if activity_ids.count(a) > 1}):
        errors.append(DraftError("activity_ids_unique", "/activities", f"activity id {activity_id!r} appears more than once"))
    declared = set(activity_ids)

    placed: list[str] = []
    dialogue_blocks: list[str] = []
    for s_index, step in enumerate(steps):
        for b_index, block in enumerate(step.get("blocks", [])):
            path = f"/steps/{s_index}/blocks/{b_index}"
            kind = block.get("kind")
            if kind == "activity":
                placed.append(block.get("ref"))
                if block.get("ref") not in declared:
                    errors.append(DraftError("activity_ref_declared", path + "/ref", f"activity {block.get('ref')!r} is not declared in `activities`"))
            elif kind == "dialogue":
                dialogue_blocks.append(path)
            elif kind == "bilingual" and len(block.get("uk", [])) != len(block.get("en", [])):
                errors.append(DraftError("bilingual_equal_length", path, f"uk has {len(block.get('uk', []))} lines, en has {len(block.get('en', []))}"))
    for c_index, ref in enumerate(draft.get("consolidation", {}).get("activities", [])):
        placed.append(ref)
        if ref not in declared:
            errors.append(DraftError("activity_ref_declared", f"/consolidation/activities/{c_index}", f"activity {ref!r} is not declared in `activities`"))
    for activity_id in activity_ids:
        count = placed.count(activity_id)
        if count != 1:
            errors.append(DraftError("activity_declared_used", "/activities", f"activity {activity_id!r} is placed {count} times; expected once (a step block or consolidation)"))

    has_dialogue = "dialogue" in draft
    if len(dialogue_blocks) > 1:
        errors.append(DraftError("dialogue_block_once", dialogue_blocks[1], "more than one `dialogue` block"))
    elif bool(dialogue_blocks) != has_dialogue:
        errors.append(DraftError("dialogue_block_once", dialogue_blocks[0] if dialogue_blocks else "/dialogue", "a `dialogue` block and the top-level `dialogue` must appear together"))
    if has_dialogue:
        lines = draft["dialogue"].get("lines", [])
        translation = draft["dialogue"].get("translation_en")
        if translation is not None and len(translation) != len(lines):
            errors.append(DraftError("translation_en_length", "/dialogue/translation_en", f"{len(translation)} entries for {len(lines)} lines"))

    gap_steps: list[str] = []
    for g_index, gap in enumerate(draft.get("gaps", [])):
        gap_steps.append(gap.get("step"))
        if gap.get("step") not in step_ids:
            errors.append(DraftError("gap_steps_exist", f"/gaps/{g_index}/step", f"gap names step {gap.get('step')!r}, which is not a step of the draft"))
    empty_steps = {s.get("id") for s in steps if not s.get("blocks")}
    if empty_steps != set(gap_steps):
        errors.append(
            DraftError(
                "gap_steps_empty",
                "/steps",
                f"steps with empty blocks {sorted(empty_steps)} must equal the steps named in gaps {sorted(set(gap_steps))}",
            )
        )

    if activity_types is not None and level is not None:
        errors.extend(_activity_type_errors(draft, level, schemas_dir, activity_types))
    return errors


def _activity_type_errors(draft: dict, level: str, schemas_dir: Path | None, activity_types: Mapping[str, str]) -> list[DraftError]:
    """Code check ``activity_items_per_type``: each payload against its exact ``<type>-<level>`` definition."""
    errors: list[DraftError] = []
    definitions = activity_definitions(level, schemas_dir)
    registry = _registry_for(str(schemas_dir or SCHEMAS_DIR))
    for a_index, activity in enumerate(draft.get("activities", [])):
        path = f"/activities/{a_index}"
        if not isinstance(activity, dict):
            errors.append(DraftError("activity_items_per_type", path, "activity is not an object"))
            continue
        activity_id = activity.get("id")
        type_name = activity_types.get(activity_id)
        if type_name is None:
            errors.append(DraftError("activity_items_per_type", path, f"activity {activity_id!r} has no type in the plan's type map"))
            continue
        if type_name not in definitions:
            errors.append(DraftError("activity_items_per_type", path, f"type {type_name!r} is not in the {level} allowlist {sorted(definitions)}"))
            continue
        payload = {k: v for k, v in activity.items() if k not in ("id", "instruction")}
        checker = Draft7Validator(activity_payload_schema(definitions[type_name]), registry=registry)
        for error in sorted(checker.iter_errors(payload), key=lambda e: [str(p) for p in e.absolute_path]):
            chosen = best_match([error]) or error
            errors.append(DraftError("activity_items_per_type", path + _pointer(chosen.absolute_path), f"{type_name}-{level}: {chosen.message}"))
    return errors


def validate_draft(
    draft: object,
    level: str | None,
    *,
    schemas_dir: Path | None = None,
    activity_types: Mapping[str, str] | None = None,
) -> list[DraftError]:
    """Return every failure of check 1 for ``draft`` (empty when the draft is valid).

    ``level`` selects the per-level schema (``None`` uses the level-agnostic one and skips the
    per-type activity binding). ``activity_types`` is the plan's ``{activity id: type}`` map; when
    given, each activity's payload is validated against its exact ``<type>-<level>`` definition.
    Schema errors stop the code checks: the code checks assume the schema's shape.
    """
    if level is not None and level not in LEVELS:
        raise ValueError(f"unknown level {level!r}; expected one of {LEVELS}")
    errors = _schema_errors(draft, level, schemas_dir)
    if not isinstance(draft, dict):
        return errors
    if errors:
        # The schema binds an activity payload to the union of the level's shapes, so its message
        # for a wrong item names some other type's branch. With the plan's type map the exact
        # per-type message is available: report it instead of the union's for that activity.
        if activity_types is not None and level is not None and isinstance(draft.get("activities"), list):
            typed = _activity_type_errors(draft, level, schemas_dir, activity_types)
            replaced = {e.path.split("/")[2] for e in typed if e.path.startswith("/activities/")}
            errors = [e for e in errors if not (e.path.startswith("/activities/") and e.path.split("/")[2] in replaced)] + typed
        return errors
    return _code_errors(draft, level, schemas_dir, activity_types)


def assert_valid_draft(draft: object, level: str | None, **kwargs) -> None:
    """Raise :class:`DraftValidationError` carrying every failure, or return silently."""
    errors = validate_draft(draft, level, **kwargs)
    if errors:
        raise DraftValidationError(errors)
