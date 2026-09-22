"""Generate the lesson-draft schemas from the template and the level activity schemas.

The writer contract (#8431 r3 §1c) binds the draft's activity items to the per-type
definitions of ``schemas/activities-<level>.schema.json`` by ``$ref``. Those definitions
are level-specific, so the draft schema is generated once per level from one template,
``schemas/templates/lesson-draft-v1.template.json``, with the generate-and-check pattern
(``--write`` overwrites the committed files, ``--check`` fails when a fresh generation differs).

Per level the generator fills two ``$defs``:

* ``activity`` — the draft's activity object ``{ id, instruction, <payload> }``. The payload
  keys are the union of the level's per-type payload properties (``items``, ``pairs``,
  ``groups`` …), each a ``$ref`` into the level schema; ``type``, ``placement``, ``title`` and
  ``notes`` are never in the draft (the engine takes them from the plan, contract §2). This is
  what the schema can prove without the plan; the exact per-type binding needs the plan's
  ``type`` and is the code check ``activity_items_per_type`` in :mod:`draft_schema`.
* ``activity_types`` — one ``$ref`` per type in the level allowlist to
  ``activities-<level>.schema.json#/definitions/<type>-<level>`` (the allowlist is the set of
  definitions of the level schema, plan schema §2a).

The level-agnostic ``schemas/lesson-draft-v1.schema.json`` is generated from the same template
and delegates its activity shapes to the four level files.

Usage:
  .venv/bin/python scripts/build/fresh/gen_draft_schemas.py --write
  .venv/bin/python scripts/build/fresh/gen_draft_schemas.py --check
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMAS_DIR = REPO_ROOT / "schemas"
TEMPLATE_REL = "templates/lesson-draft-v1.template.json"
LEVELS: tuple[str, ...] = ("a1", "a2", "b1", "b2")

# Activity-level keys the draft never carries: the plan owns type and placement, the engine
# renders titles, and notes / gate flags are not writer output (contract §1, §2).
META_KEYS: frozenset[str] = frozenset(
    {"type", "id", "title", "notes", "instruction", "anchor_id", "vesum_exempt", "source_reading", "placement"}
)

_ACTIVITY_MARK = "__GENERATED_ACTIVITY__"
_ACTIVITY_TYPES_MARK = "__GENERATED_ACTIVITY_TYPES__"


class DraftSchemaGenerationError(ValueError):
    """The template or a level schema is not what the generator needs."""


def draft_schema_filename(level: str | None) -> str:
    return "lesson-draft-v1.schema.json" if level is None else f"lesson-draft-{level}-v1.schema.json"


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def dump_json(obj: dict) -> str:
    """The one serialisation of a generated schema (byte-stable across runs)."""
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def level_activity_types(level: str, level_schema: dict) -> list[str]:
    """The level's activity-type allowlist: the definitions of ``activities-<level>.schema.json``.

    Fails when a definition is not named ``<type>-<level>`` or when the top-level ``oneOf``
    and the definitions disagree, so that the generated ``$ref`` list is the allowlist itself.
    """
    definitions = level_schema.get("definitions")
    if not isinstance(definitions, dict) or not definitions:
        raise DraftSchemaGenerationError(f"activities-{level}: no `definitions` (the contract needs `definitions`, not `$defs`)")
    suffix = f"-{level}"
    types: list[str] = []
    for name in definitions:
        if not name.endswith(suffix) or len(name) <= len(suffix):
            raise DraftSchemaGenerationError(f"activities-{level}: definition {name!r} is not named <type>{suffix}")
        types.append(name[: -len(suffix)])
    listed = {
        entry.get("$ref", "").removeprefix("#/definitions/")
        for entry in level_schema.get("items", {}).get("oneOf", [])
        if isinstance(entry, dict)
    }
    if listed != set(definitions):
        raise DraftSchemaGenerationError(
            f"activities-{level}: items.oneOf and definitions disagree: "
            f"only in oneOf {sorted(listed - set(definitions))}, only in definitions {sorted(set(definitions) - listed)}"
        )
    return sorted(types)


def _level_ref(level: str, type_name: str, *tail: str) -> dict:
    pointer = "/".join((f"#/definitions/{type_name}-{level}", *tail))
    return {"$ref": f"activities-{level}.schema.json{pointer}"}


def build_activity_defs(level: str, level_schema: dict) -> tuple[dict, dict]:
    """Return (``$defs/activity``, ``$defs/activity_types``) for one level."""
    types = level_activity_types(level, level_schema)
    definitions = level_schema["definitions"]
    payload_keys: dict[str, list[str]] = {}
    for type_name in types:
        definition = definitions[f"{type_name}-{level}"]
        properties = definition.get("properties")
        if not isinstance(properties, dict):
            raise DraftSchemaGenerationError(f"activities-{level}: {type_name}-{level} has no `properties`")
        if definition.get("additionalProperties") is not False:
            raise DraftSchemaGenerationError(f"activities-{level}: {type_name}-{level} must set additionalProperties: false")
        for key in properties:
            if key not in META_KEYS:
                payload_keys.setdefault(key, []).append(type_name)
    properties: dict = {
        "id": {"$ref": "#/$defs/activity_id"},
        "instruction": {"$ref": "#/$defs/text"},
    }
    for key in sorted(payload_keys):
        properties[key] = {"anyOf": [_level_ref(level, type_name, "properties", key) for type_name in payload_keys[key]]}
    activity = {
        "type": "object",
        "description": (
            f"One activity of the draft: the plan's id, the writer's instruction and the per-type payload "
            f"of schemas/activities-{level}.schema.json (contract §1c). `type` and `placement` are not "
            "repeated here — the engine takes them from the plan (§2) — so the schema can only bind each "
            "payload key to the union of the level's shapes for that key; the exact per-type binding, given "
            "the plan's type, is the code check activity_items_per_type (scripts/build/fresh/draft_schema.py), "
            "which validates the payload against $defs/activity_types/<type> with the meta keys removed."
        ),
        "additionalProperties": False,
        "required": ["id", "instruction"],
        "properties": properties,
    }
    activity_types = {type_name: _level_ref(level, type_name) for type_name in types}
    return activity, activity_types


def _substitute_strings(node: object, replacements: list[tuple[str, str]]) -> object:
    if isinstance(node, str):
        for old, new in replacements:
            node = node.replace(old, new)
        return node
    if isinstance(node, list):
        return [_substitute_strings(item, replacements) for item in node]
    if isinstance(node, dict):
        return {key: _substitute_strings(value, replacements) for key, value in node.items()}
    return node


def render_schema(template: dict, level: str | None, level_schemas: dict[str, dict]) -> dict:
    """Render the template for one level (or the level-agnostic schema when ``level`` is None)."""
    if level is None:
        replacements = [
            ("lesson-draft-__LEVEL__-v1", "lesson-draft-v1"),
            ("__LEVEL_LABEL__", "any level; activity shapes delegated to the per-level files"),
            ("__MODULE_LEVELS__", "(" + "|".join(LEVELS) + ")"),
        ]
        activity = {
            "description": "The level-agnostic schema accepts any level's activity shapes; the per-level file is the binding one.",
            "anyOf": [{"$ref": f"{draft_schema_filename(lvl)}#/$defs/activity"} for lvl in LEVELS],
        }
        activity_types = {lvl: {"$ref": f"{draft_schema_filename(lvl)}#/$defs/activity_types"} for lvl in LEVELS}
    else:
        replacements = [
            ("__LEVEL__", level),
            ("__LEVEL_LABEL__", level.upper()),
            ("__MODULE_LEVELS__", level),
        ]
        activity, activity_types = build_activity_defs(level, level_schemas[level])
    rendered = copy.deepcopy(template)
    defs = rendered.get("$defs")
    if not isinstance(defs, dict) or defs.get("activity") != _ACTIVITY_MARK or defs.get("activity_types") != _ACTIVITY_TYPES_MARK:
        raise DraftSchemaGenerationError(
            f"template must carry $defs.activity = {_ACTIVITY_MARK!r} and $defs.activity_types = {_ACTIVITY_TYPES_MARK!r}"
        )
    defs["activity"] = activity
    defs["activity_types"] = activity_types
    rendered = _substitute_strings(rendered, replacements)
    leftovers = [s for s in _all_strings(rendered) if "__" in s and s.strip("_") != s]
    if leftovers:
        raise DraftSchemaGenerationError(f"unresolved template placeholder(s): {leftovers[:3]}")
    return rendered


def _all_strings(node: object):
    if isinstance(node, str):
        yield node
    elif isinstance(node, list):
        for item in node:
            yield from _all_strings(item)
    elif isinstance(node, dict):
        for key, value in node.items():
            yield key
            yield from _all_strings(value)


def generate_all(schemas_dir: Path) -> dict[str, str]:
    """Return ``{filename: text}`` for the five generated schema files."""
    template = load_json(schemas_dir / TEMPLATE_REL)
    level_schemas = {level: load_json(schemas_dir / f"activities-{level}.schema.json") for level in LEVELS}
    outputs: dict[str, str] = {}
    for level in (*LEVELS, None):
        outputs[draft_schema_filename(level)] = dump_json(render_schema(template, level, level_schemas))
    return outputs


def check(schemas_dir: Path) -> list[str]:
    """Return the names of committed files that are missing or differ from a fresh generation."""
    stale: list[str] = []
    for name, text in generate_all(schemas_dir).items():
        path = schemas_dir / name
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            stale.append(name)
    return stale


def write(schemas_dir: Path) -> list[str]:
    written: list[str] = []
    for name, text in generate_all(schemas_dir).items():
        (schemas_dir / name).write_text(text, encoding="utf-8")
        written.append(name)
    return written


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__.split("\n\n")[0],
        epilog="Exit codes: 0 generated / committed files are byte-identical; 1 --check found a stale or missing file; "
        "2 the template or a level schema could not be used (the offending file is named).",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="write schemas/lesson-draft-{a1,a2,b1,b2}-v1.schema.json and lesson-draft-v1.schema.json")
    mode.add_argument("--check", action="store_true", help="write nothing; exit 1 if any committed file differs from a fresh generation")
    parser.add_argument("--schemas-dir", type=Path, default=SCHEMAS_DIR, help="schemas directory (tests use a temporary copy)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.check:
            stale = check(args.schemas_dir)
            if stale:
                print("stale generated schema(s): " + ", ".join(stale) + " — run gen_draft_schemas.py --write", file=sys.stderr)
                return 1
            print("lesson-draft schemas are up to date")
            return 0
        for name in write(args.schemas_dir):
            print(f"wrote {args.schemas_dir / name}")
        return 0
    except (DraftSchemaGenerationError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
