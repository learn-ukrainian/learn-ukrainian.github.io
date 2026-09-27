"""Generates and loads the activity placement table (issue #8889 r5 §B2).

A per-level, per-type placement value (``inline | workbook | both |
forbidden``) is never hand-typed: it is derived from two sources that must
both agree before a type is usable at a level —

1. **The runtime allowlist**: a type must be *defined* in
   ``schemas/activities-<level>.schema.json`` (the existence gate; the plan
   validator's own ``_activity_allowlist`` reads the same definitions).
2. **The pedagogy doc**: its placement comes from the §3 "Type → level
   matrix" table of ``docs/best-practices/activity-pedagogy.md`` (cell legend
   ``B`` both, ``I`` inline, ``W`` workbook, ``-`` not allowed).

Where the two disagree — a type the schema still defines but the doc forbids
or never lists (``classify``, deprecated in favour of ``group-sort``; a
handful of B1+ types whose schema definition never shipped), or a type the
doc allows but no schema defines it at that level — the resolution is always
``forbidden``: the doc's pedagogical judgement can remove a type the schema
still technically shapes, and a type with no schema definition cannot be
rendered regardless of what the doc says. Every such disagreement is recorded
in the ``discrepancies`` section instead of being silently resolved.

Scope: the six CORE fresh-build levels plan-validate operates on (a1, a2, b1,
b2, c1, c2) — the levels with both a ``schemas/activities-<level>.schema.json``
file and a plan-validate consumer. The pedagogy doc's matrix additionally
covers the seminar tracks (hist, bio, istorio, lit, oes, ruth); those never
reach plan-validate (a different pipeline validates seminar plans), so they
are out of scope here.

``scripts/curriculum/validate/placement_table.yaml`` is the generated,
committed artifact (the same generate-and-check pattern as ``_arc.yaml`` in
scripts/curriculum/arc/generate_arc.py): ``--write`` regenerates it,
``--check`` compares a fresh generation against the committed file byte for
byte. Never hand-edit the YAML.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]

PEDAGOGY_DOC_REL = "docs/best-practices/activity-pedagogy.md"
PLACEMENT_TABLE_REL = "scripts/curriculum/validate/placement_table.yaml"
PLACEMENT_TABLE_SCHEMA = 1

#: CORE fresh-build levels plan-validate operates on. Each has
#: schemas/activities-<level>.schema.json and (via DOC_COLUMN_BY_LEVEL) a
#: column in the pedagogy doc's §3 matrix.
CORE_LEVELS = ("a1", "a2", "b1", "b2", "c1", "c2")

#: The pedagogy doc's §3 matrix header spells two columns "<level>-core"
#: (b1-core, c1-core) where the schema file and plan-validate's level
#: argument say "b1"/"c1"; every other column equals the level name.
DOC_COLUMN_BY_LEVEL = {level: level for level in CORE_LEVELS} | {"b1": "b1-core", "c1": "c1-core"}

_MATRIX_HEADING_RE = re.compile(r"^### Type → level matrix\s*$")
_TABLE_SEPARATOR_RE = re.compile(r"^\|[\s:|-]*-[\s:|-]*\|?\s*$")

#: Cell legend of the §3 matrix (documented at the top of that section).
_CELL_TO_PLACEMENT = {"B": "both", "I": "inline", "W": "workbook"}

PLACEMENT_VALUES = frozenset({"inline", "workbook", "both", "forbidden"})


class PlacementTableError(Exception):
    """The pedagogy doc or a level schema cannot be read deterministically."""


def _split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def parse_pedagogy_matrix(doc_text: str) -> dict[str, dict[str, str]]:
    """``{type: {doc_column: cell}}`` from the §3 "Type → level matrix" table.

    Tables only: the matrix must be the first Markdown table after the
    "### Type → level matrix" heading (blank lines allowed in between; any
    other content before the table fails generation, as does a row whose
    cell count disagrees with the header).
    """
    lines = doc_text.splitlines()
    start = next((i for i, line in enumerate(lines) if _MATRIX_HEADING_RE.match(line)), None)
    if start is None:
        raise PlacementTableError('no "### Type → level matrix" heading found in the pedagogy doc')
    i = start + 1
    while i < len(lines) and not lines[i].strip().startswith("|"):
        if lines[i].strip():
            raise PlacementTableError(f"non-table content before the matrix table: {lines[i]!r}")
        i += 1
    if i >= len(lines) or i + 1 >= len(lines) or not _TABLE_SEPARATOR_RE.match(lines[i + 1]):
        raise PlacementTableError("no Markdown table found after the matrix heading")
    header = _split_row(lines[i])
    if not header or header[0] != "Type":
        raise PlacementTableError(f"unexpected matrix header: {header!r}")
    columns = header[1:]
    matrix: dict[str, dict[str, str]] = {}
    j = i + 2
    while j < len(lines) and lines[j].strip().startswith("|"):
        cells = _split_row(lines[j])
        if len(cells) != len(header):
            raise PlacementTableError(f"matrix row has {len(cells)} cells, expected {len(header)}: {lines[j]!r}")
        type_name, values = cells[0], cells[1:]
        if type_name in matrix:
            raise PlacementTableError(f"duplicate matrix row for type {type_name!r}")
        matrix[type_name] = dict(zip(columns, values, strict=True))
        j += 1
    if not matrix:
        raise PlacementTableError("the matrix table has no data rows")
    return matrix


def schema_activity_types(level: str, schema_path: Path | None = None) -> set[str]:
    """The activity types ``schemas/activities-<level>.schema.json`` defines.

    Mirrors ``validate._activity_allowlist``'s reading of the same file (the
    ``-<level>`` suffix is stripped from every definition key); this is the
    existence gate of the precedence rule.
    """
    schema_path = schema_path or REPO_ROOT / f"schemas/activities-{level}.schema.json"
    if not schema_path.is_file():
        raise PlacementTableError(f"{schema_path} does not exist")
    definitions = json.loads(schema_path.read_text(encoding="utf-8")).get("definitions", {})
    suffix = f"-{level}"
    types: set[str] = set()
    for key in definitions:
        if not key.endswith(suffix):
            raise PlacementTableError(f"{schema_path} definition {key!r} lacks the {suffix} suffix")
        types.add(key[: -len(suffix)])
    return types


def build_placement_table(doc_text: str, doc_rel_path: str, doc_sha256: str) -> dict:
    """The full ``placement_table.yaml`` payload (issue #8889 r5 §B2).

    Precedence: a type is usable at a level only when it is *both* defined in
    that level's runtime allowlist *and* allowed a placement (any cell but
    ``-``) by the pedagogy doc's matrix for that level's column. Wherever the
    two disagree the type is ``forbidden`` and the disagreement is recorded
    in ``discrepancies`` with how it was resolved.
    """
    matrix = parse_pedagogy_matrix(doc_text)
    schema_types = {level: schema_activity_types(level) for level in CORE_LEVELS}
    all_types = sorted(set(matrix) | {activity_type for types in schema_types.values() for activity_type in types})

    levels: dict[str, dict[str, str]] = {}
    discrepancies: list[dict] = []
    for level in CORE_LEVELS:
        doc_column = DOC_COLUMN_BY_LEVEL[level]
        entries: dict[str, str] = {}
        for activity_type in all_types:
            schema_allows = activity_type in schema_types[level]
            row = matrix.get(activity_type)
            cell = row.get(doc_column, "-") if row is not None else "-"
            doc_allows = cell in _CELL_TO_PLACEMENT
            entries[activity_type] = _CELL_TO_PLACEMENT[cell] if schema_allows and doc_allows else "forbidden"
            if schema_allows != doc_allows:
                discrepancies.append(
                    {
                        "type": activity_type,
                        "level": level,
                        "schema": "allowed" if schema_allows else "not_defined",
                        "doc": cell if row is not None else "not_listed",
                        "resolution": "forbidden",
                    }
                )
        levels[level] = dict(sorted(entries.items()))
    return {
        "placement_table_schema": PLACEMENT_TABLE_SCHEMA,
        "source_doc": {"path": doc_rel_path, "sha256": doc_sha256},
        "schema_paths": {level: f"schemas/activities-{level}.schema.json" for level in CORE_LEVELS},
        "levels": levels,
        "discrepancies": sorted(discrepancies, key=lambda entry: (entry["type"], entry["level"])),
    }


def render_placement_table(table: dict) -> str:
    """The deterministic YAML text: fixed key order (as built), trailing newline."""
    text = yaml.safe_dump(table, sort_keys=False, allow_unicode=True, width=10**6)
    if not text.endswith("\n"):
        text += "\n"
    return text


def generate(doc_path: Path) -> str:
    """Generate the placement_table.yaml text from the pedagogy doc at doc_path."""
    doc_bytes = doc_path.read_bytes()
    doc_text = doc_bytes.decode("utf-8")
    try:
        doc_rel_path = doc_path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        doc_rel_path = doc_path.as_posix()
    table = build_placement_table(doc_text, doc_rel_path, hashlib.sha256(doc_bytes).hexdigest())
    return render_placement_table(table)


def load_placement_table(path: Path | None = None) -> dict:
    """Load the committed (or overridden, for tests) placement_table.yaml."""
    path = path or REPO_ROOT / PLACEMENT_TABLE_REL
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("levels"), dict):
        raise PlacementTableError(f"{path} is not a valid placement table (missing or malformed 'levels' key)")
    return data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="generate_placement_table",
        description=(
            "Generate scripts/curriculum/validate/placement_table.yaml from "
            "docs/best-practices/activity-pedagogy.md's §3 type-level matrix, intersected with "
            "each level's schemas/activities-<level>.schema.json allowlist (issue #8889 r5 §B2).\n"
            "Use after either source changes; never hand-edit placement_table.yaml — plan-validate's "
            "ACTIVITY_PLACEMENT_FORBIDDEN / ACTIVITY_PLACEMENT_NOT_ALLOWED checks and a dedicated test "
            "both require the committed file to be byte-identical to a fresh run of this generator."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python scripts/curriculum/validate/placement_table.py --write
  .venv/bin/python scripts/curriculum/validate/placement_table.py --check

Outputs:
  --write   writes scripts/curriculum/validate/placement_table.yaml (overwrites)
  --check   writes nothing; compares a fresh generation against the committed file

Exit codes:
  0  generation succeeded / committed file is byte-identical
  1  --check found the committed file missing or different
  2  the pedagogy doc or a level schema could not be parsed, or bad CLI usage

Related:
  Consumer: scripts/curriculum/validate/validate.py (ACTIVITY_PLACEMENT_FORBIDDEN, ACTIVITY_PLACEMENT_NOT_ALLOWED)
  Sources: docs/best-practices/activity-pedagogy.md §3; schemas/activities-<level>.schema.json
  Design: issue #8889 r5 §B2; implementation header comment 5855658208 (A1-P2)
""",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--check",
        action="store_true",
        help="Compare a fresh generation against the committed placement_table.yaml; exit 1 if missing or different",
    )
    mode.add_argument(
        "--write",
        action="store_true",
        help="Write the generated YAML to scripts/curriculum/validate/placement_table.yaml, overwriting it",
    )
    parser.add_argument(
        "--doc",
        type=Path,
        default=None,
        help="Override the pedagogy doc path (default: docs/best-practices/activity-pedagogy.md); tests only",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Override the placement_table.yaml path that --write writes and --check compares against; tests only",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    doc_path = args.doc or REPO_ROOT / PEDAGOGY_DOC_REL
    out_path = args.output or REPO_ROOT / PLACEMENT_TABLE_REL
    try:
        generated = generate(doc_path)
    except (PlacementTableError, OSError, UnicodeDecodeError) as error:
        print(f"error: cannot generate the placement table from {doc_path}: {error}", file=sys.stderr)
        return 2
    if args.write:
        out_path.write_text(generated, encoding="utf-8")
        print(f"wrote {out_path} ({len(generated.splitlines())} lines)")
        return 0
    if not out_path.exists():
        print(f"error: {out_path} does not exist; run with --write", file=sys.stderr)
        return 1
    committed = out_path.read_text(encoding="utf-8")
    if committed == generated:
        print(f"ok: {out_path} is byte-identical to a fresh generation from {doc_path}")
        return 0
    print(
        f"error: {out_path} differs from a fresh generation from {doc_path}; "
        "regenerate with --write (never edit placement_table.yaml by hand)",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
