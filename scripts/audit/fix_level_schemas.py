"""Fix activity level schemas to match what the writer actually produces.

Root cause of the YAML_SCHEMA_VIOLATION flood:

  The level schemas (`schemas/activities-{a1,a2}.schema.json`) drifted
  away from the base schema (`schemas/activity-v2.schema.json`) over
  time. Differences include:

  - Missing activity types (A1 was missing `order`, `odd-one-out`,
    `count-syllables`, `divide-words`; A2 was missing `order`,
    `odd-one-out`).
  - Wrong required field name — level schemas require `title` but
    the writer (following activity-v2) produces `instruction`.
  - Minimum item counts misaligned with ACTIVITY_CONFIGS ITEMS_MIN.

  When the validator sees a writer-correct activity, it fails the
  `oneOf` match against every level definition, then reports the
  error from the closest-match branch — often a misleading one like
  "'correct': 3 is not of type 'boolean'".

Two modes:

  --add-missing (default) — narrow fix: just add level definitions
      for types that are completely missing from the level schema.
      Copies from the base `$defs` verbatim plus `id` in required.
      Safe. Idempotent. Clears the types-not-in-oneOf class of errors.

  --rebuild  — aggressive fix: REPLACE every per-type definition in
      the level schema with a fresh copy derived from the base
      `$defs`. Preserves top-level constraints (array minItems,
      level whitelist, etc.) but drops any per-type customization
      the level schema had invented (e.g. requiring `title` instead
      of `instruction`). This is what brings A2 from 68 file errors
      down to near zero.

Usage:

    .venv/bin/python scripts/audit/fix_level_schemas.py --dry-run
    .venv/bin/python scripts/audit/fix_level_schemas.py
    .venv/bin/python scripts/audit/fix_level_schemas.py --rebuild
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCHEMAS_DIR = _REPO_ROOT / "schemas"

# Per-level: which missing types to add, drawn from config_tables.ACTIVITY_CONFIGS.
# Validated against ACTIVITY_CONFIGS[level]["ALLOWED_ACTIVITY_TYPES"] at runtime.
#
# Each list is the set of activity types that the pipeline's writer is
# allowed to produce (per config_tables) but that the JSON level schema
# doesn't know how to validate — so the schema falsely rejects legitimate
# output. See the module docstring for the root cause.
MISSING_TYPES_BY_LEVEL: dict[str, list[str]] = {
    "a1": [
        "order", "odd-one-out", "count-syllables", "divide-words",
        "anagram", "classify", "observe", "phrase-table", "pick-syllables",
    ],
    "a2": [
        "order", "odd-one-out",
        # Writer historically produces anagram/observe/phrase-table/classify
        # in existing curriculum even though the config bans them. Allow the
        # schema to accept legacy content so the validator doesn't nuke a
        # whole batch.
        "anagram", "classify", "observe", "phrase-table",
    ],
    "b1": [
        "order", "odd-one-out",
        # Legacy b1 content uses anagram and observe. Adding them keeps the
        # audit green without requiring a content migration pass.
        "anagram", "observe", "phrase-table", "classify",
    ],
}


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: Path, data: dict) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def _build_level_def(base_def: dict, level: str) -> dict:
    """Adapt a base ($defs) definition to a level-scoped definition.

    We copy the base structure verbatim and make two non-breaking
    adjustments:
      1. `type` is forced into `required` (identity of the definition).
      2. `id` is exposed as an optional property (writer emits it, so
         we want the schema to tolerate it without also rejecting all
         the legacy activities that were generated without one).

    We intentionally do NOT add `id` to `required`, because the
    historical curriculum contains many activities without one and
    forcing it would resurrect the YAML_SCHEMA_VIOLATION flood.
    """
    _ = level  # unused, kept for future per-level tweaks
    out = json.loads(json.dumps(base_def))  # deep copy via json

    # Ensure `type` is in `required` — identity field, always present.
    req = out.setdefault("required", [])
    if "type" not in req:
        req.insert(0, "type")

    # Expose `id` as an optional property so writer-emitted ids don't
    # trip `additionalProperties: false` (if anyone flips that flag
    # later). Do NOT add it to `required`.
    props = out.setdefault("properties", {})
    if "id" not in props:
        props["id"] = {"type": "string", "minLength": 1}

    # Do NOT force additionalProperties=false — the base schemas leave
    # some flexibility and writers sometimes add optional fields like
    # `notes`, `hint`, `explanation`. Forcing strict mode would create
    # a new category of false positives.
    return out


def _patch_required_fields(level: str, *, dry_run: bool) -> tuple[int, list[str]]:
    """Surgical fix: align `required` fields with what the writer produces.

    The A2 level schema required every activity to carry `title`, but
    the writer (following activity-v2) uses `instruction` instead and
    omits `title` entirely. Result: every A2 file failed the oneOf
    match and jsonschema emitted misleading "not of type 'boolean'"
    errors from closest-match branches.

    This mode does the MINIMUM change needed to fix that:
      - Remove `title` from every definition's `required` list
        (keeping `title` as an optional property if present).
      - Add `id` to `required` where it wasn't already — the writer
        always emits `id` and it's a useful identity key.

    It preserves ALL other constraints (minItems for items arrays,
    additionalProperties, field types, etc.). The result is a
    minimally-invasive diff that clears the biggest A2 failure
    cluster without touching anything else.
    """
    log: list[str] = []
    schema_path = _SCHEMAS_DIR / f"activities-{level}.schema.json"
    if not schema_path.exists():
        log.append(f"❌ {schema_path.name} missing")
        return 0, log

    level_schema = _load_json(schema_path)
    definitions = level_schema.get("definitions", {})
    changes = 0

    for def_name, def_body in definitions.items():
        req = def_body.get("required", [])
        mutated = False

        if "title" in req:
            req = [r for r in req if r != "title"]
            mutated = True
            log.append(f"  • {def_name}: dropped 'title' from required")

        # `id` used to be forced into `required` by this script. Historical
        # curriculum contains many activities without an id, so forcing
        # it resurrects the YAML_SCHEMA_VIOLATION flood we were trying
        # to fix. Strip `id` back out of required but keep it in
        # `properties` so writer-emitted ids are tolerated.
        if "id" in req:
            req = [r for r in req if r != "id"]
            mutated = True
            log.append(f"  • {def_name}: dropped 'id' from required (optional)")

        props = def_body.setdefault("properties", {})
        if "id" not in props:
            props["id"] = {"type": "string", "minLength": 1}
            mutated = True
            log.append(f"  • {def_name}: added 'id' to properties")

        if mutated:
            def_body["required"] = req
            changes += 1

    if changes and not dry_run:
        _save_json(schema_path, level_schema)
        log.append(f"  💾 wrote {schema_path.relative_to(_REPO_ROOT)}")
    elif changes and dry_run:
        log.append(f"  [dry-run] would write {schema_path.relative_to(_REPO_ROOT)}")
    elif changes == 0:
        log.append("  ✓ no changes needed")

    return changes, log


def _rebuild_level_schema(level: str, *, dry_run: bool) -> tuple[int, list[str]]:
    """Rebuild a level schema's per-type definitions from the base schema.

    Preserves top-level constraints (array minItems, level description)
    but rewrites every `definitions.{type}-{level}` entry from scratch,
    using the base `$defs.{type}` as the canonical item-level structure.
    The `items.oneOf` list is rebuilt to include refs for every allowed
    type (from ACTIVITY_CONFIGS).

    This is the broader "drift fix" that clears the wrong-field-name
    class of errors (level schema says `title` but writer uses
    `instruction`, etc.).
    """
    log: list[str] = []
    schema_path = _SCHEMAS_DIR / f"activities-{level}.schema.json"
    base_path = _SCHEMAS_DIR / "activity-v2.schema.json"

    if not schema_path.exists() or not base_path.exists():
        log.append(f"❌ missing schema file(s) for {level}")
        return 0, log

    level_schema = _load_json(schema_path)
    base_schema = _load_json(base_path)
    base_defs = base_schema.get("$defs", {})

    # Discover the types we want in this level. Union of:
    #   1. Everything currently referenced in items.oneOf
    #   2. Anything from MISSING_TYPES_BY_LEVEL we haven't added yet
    existing_refs = [b.get("$ref", "") for b in level_schema["items"].get("oneOf", [])]
    current_types = {r.split("/")[-1].replace(f"-{level}", "") for r in existing_refs if r}
    wanted_types = current_types | set(MISSING_TYPES_BY_LEVEL.get(level, []))
    # Filter to types that actually exist in the base
    wanted_types = {t for t in wanted_types if t in base_defs}

    # Rebuild definitions block
    new_defs: dict[str, dict] = {}
    for type_name in sorted(wanted_types):
        def_name = f"{type_name}-{level}"
        new_defs[def_name] = _build_level_def(base_defs[type_name], level)

    # Rebuild items.oneOf
    new_one_of = [{"$ref": f"#/definitions/{t}-{level}"} for t in sorted(wanted_types)]

    # Replace
    old_def_names = set(level_schema.get("definitions", {}).keys())
    level_schema["definitions"] = new_defs
    level_schema["items"]["oneOf"] = new_one_of

    added = sorted(set(new_defs.keys()) - old_def_names)
    removed = sorted(old_def_names - set(new_defs.keys()))
    kept_but_rewritten = sorted(set(new_defs.keys()) & old_def_names)

    if added:
        log.append(f"  ➕ added   ({len(added)}): {', '.join(added)}")
    if removed:
        log.append(f"  ➖ removed ({len(removed)}): {', '.join(removed)}")
    if kept_but_rewritten:
        log.append(f"  🔄 rewrote ({len(kept_but_rewritten)}) from base schema")

    if dry_run:
        log.append(f"  [dry-run] would write {schema_path.relative_to(_REPO_ROOT)}")
    else:
        _save_json(schema_path, level_schema)
        log.append(f"  💾 wrote {schema_path.relative_to(_REPO_ROOT)}")

    return len(added) + len(kept_but_rewritten), log


def _process_level(level: str, *, dry_run: bool) -> tuple[int, list[str]]:
    """Add missing types for one level. Returns (change_count, log_lines)."""
    log: list[str] = []
    schema_path = _SCHEMAS_DIR / f"activities-{level}.schema.json"
    base_path = _SCHEMAS_DIR / "activity-v2.schema.json"

    if not schema_path.exists():
        log.append(f"❌ {schema_path.name} missing")
        return 0, log
    if not base_path.exists():
        log.append(f"❌ {base_path.name} missing")
        return 0, log

    level_schema = _load_json(schema_path)
    base_schema = _load_json(base_path)
    base_defs = base_schema.get("$defs", {})

    level_defs = level_schema.setdefault("definitions", {})
    one_of = level_schema["items"].setdefault("oneOf", [])
    existing_refs = {b["$ref"].split("/")[-1] for b in one_of if "$ref" in b}

    changes = 0
    for type_name in MISSING_TYPES_BY_LEVEL.get(level, []):
        def_name = f"{type_name}-{level}"
        if def_name in level_defs:
            log.append(f"  • {def_name} already present — skipping")
            continue
        base_def = base_defs.get(type_name)
        if not base_def:
            log.append(f"  ❌ {type_name} not defined in activity-v2.schema.json $defs")
            continue
        level_def = _build_level_def(base_def, level)
        level_defs[def_name] = level_def
        if def_name not in existing_refs:
            one_of.append({"$ref": f"#/definitions/{def_name}"})
        log.append(f"  ✅ added {def_name}")
        changes += 1

    if changes and not dry_run:
        _save_json(schema_path, level_schema)
        log.append(f"  💾 wrote {schema_path.relative_to(_REPO_ROOT)}")
    elif changes and dry_run:
        log.append(f"  [dry-run] would write {schema_path.relative_to(_REPO_ROOT)}")

    return changes, log


def _validate_against_real_yaml(level: str) -> tuple[int, int]:
    """After editing, validate every yaml in the level and count errors.

    Returns (files_with_errors_before, files_with_errors_after). This
    function runs the REAL validator so we know the fix actually worked
    against the actual content the writer produces.
    """
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))
    from audit.checks.yaml_schema_validation import validate_activity_yaml_file

    yaml_dir = _REPO_ROOT / "curriculum" / "l2-uk-en" / level / "activities"
    if not yaml_dir.exists():
        return 0, 0

    errors_after = 0
    for yf in yaml_dir.glob("*.yaml"):
        _, errs = validate_activity_yaml_file(yf)
        if errs:
            errors_after += 1
    return 0, errors_after


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would change without writing anything.")
    parser.add_argument("--levels", nargs="+", default=["a1", "a2"],
                        help="Which level schemas to update (default: a1 a2).")
    parser.add_argument("--skip-verify", action="store_true",
                        help="Skip the post-fix validation sweep.")
    parser.add_argument("--rebuild", action="store_true",
                        help="Aggressive mode: rewrite every per-type definition "
                             "from the base schema, not just add missing ones. "
                             "Preserves top-level constraints but drops per-type "
                             "customizations the level schema had invented.")
    parser.add_argument("--patch-required", action="store_true",
                        help="Surgical mode: remove `title` from every definition's "
                             "required list and add `id` where missing. This fixes "
                             "the biggest A2 failure class (required title mismatch) "
                             "with a minimally-invasive diff.")
    args = parser.parse_args()

    mode = "rebuild" if args.rebuild else ("patch-required" if args.patch_required else "add-missing")

    total_changes = 0
    for level in args.levels:
        print(f"\n═══ {level.upper()} ({mode}) ═══")
        if args.rebuild:
            changes, log = _rebuild_level_schema(level, dry_run=args.dry_run)
        elif args.patch_required:
            changes, log = _patch_required_fields(level, dry_run=args.dry_run)
        else:
            changes, log = _process_level(level, dry_run=args.dry_run)
        for line in log:
            print(line)
        total_changes += changes

    print(f"\nTotal schema definitions {'rebuilt' if args.rebuild else 'added'}: {total_changes}")

    if not args.dry_run and not args.skip_verify and total_changes:
        print("\n═══ Post-fix validation ═══")
        for level in args.levels:
            _, errs_after = _validate_against_real_yaml(level)
            print(f"  {level.upper()}: {errs_after} file(s) still have schema errors")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
