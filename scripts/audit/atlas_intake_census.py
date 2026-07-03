#!/usr/bin/env python3
"""Safe source-family census for full-corpus Atlas intake."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
if sys.path and Path(sys.path[0]).resolve() == SCRIPT_DIR:
    sys.path.pop(0)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit.atlas_intake_gate import (
    classification_counts,
    classify_candidates,
)
from scripts.audit.atlas_intake_registry import (
    REQUIRED_SOURCE_FAMILIES,
    is_registered_source_family,
    registered_source_families,
    registry_payload,
)
from scripts.audit.source_inventory_intake import (
    SourceInventoryError,
    SourceInventoryRecord,
    read_source_inventories,
    source_inventory_candidates,
)

SUPPORTED_INVENTORY_SUFFIXES = {".csv", ".tsv", ".jsonl", ".json", ".yaml", ".yml"}
DEFAULT_INVENTORY_DIR = PROJECT_ROOT / "data/lexicon/source-inventory"
WORKFLOW_ID = "atlas_intake_census.v1"
OMITTED_RAW_FIELDS = ("lemma", "headword", "word", "context", "gloss", "notes", "raw_text")


def discover_inventory_paths(
    inventory_dir: Path = DEFAULT_INVENTORY_DIR,
) -> tuple[Path, ...]:
    """Return supported source-inventory files in deterministic order."""
    return tuple(
        sorted(
            path
            for path in inventory_dir.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_INVENTORY_SUFFIXES
        )
    )


def build_census(
    inventory_paths: Sequence[Path],
    *,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, Any]:
    """Build a safe derived census without raw source text or candidate lemmas."""
    records = read_source_inventories(inventory_paths, project_root=project_root)
    candidates = source_inventory_candidates(records)
    gate_results = classify_candidates(candidates)
    by_family = _family_rows(records)
    registered = set(registered_source_families())
    seen_families = set(by_family)
    unknown_families = sorted(family for family in seen_families if family not in registered)
    missing_required = sorted(set(REQUIRED_SOURCE_FAMILIES) - seen_families)

    inventory_rows = _inventory_rows(records, inventory_paths, project_root)
    return {
        "workflow": WORKFLOW_ID,
        "source_registry": {
            **registry_payload(),
            "missing_required_source_families": missing_required,
            "unknown_source_families": unknown_families,
        },
        "counts": {
            "inventory_files": len(inventory_paths),
            "source_units": _source_unit_count(records),
            "source_rows": len(records),
            "deduped_candidates": len(candidates),
            "registered_source_rows": sum(
                1 for record in records if is_registered_source_family(record.source_family)
            ),
            "unknown_source_rows": sum(
                1 for record in records if not is_registered_source_family(record.source_family)
            ),
        },
        "gate": {
            "workflow": "atlas_intake_gate.v1",
            "classification_counts": classification_counts(gate_results),
        },
        "by_family": {
            family: _family_payload(rows, registered=family in registered)
            for family, rows in sorted(by_family.items())
        },
        "inventory_files": inventory_rows,
        "safety": {
            "raw_text_included": False,
            "omitted_fields": list(OMITTED_RAW_FIELDS),
            "public_boundary": (
                "Census output is derived metadata only: counts, source ids, paths, "
                "and locators. It omits lemmas, contexts, glosses, and raw source text."
            ),
        },
    }


def format_markdown_census(census: Mapping[str, Any]) -> str:
    """Format a compact human-readable census report."""
    counts = census["counts"]
    lines = [
        "# Atlas Intake Source Census",
        "",
        f"- workflow: `{census['workflow']}`",
        f"- inventory_files: {counts['inventory_files']}",
        f"- source_units: {counts['source_units']}",
        f"- source_rows: {counts['source_rows']}",
        f"- deduped_candidates: {counts['deduped_candidates']}",
        "- raw_text_included: false",
        "",
        "## Gate Counts",
        "",
    ]
    gate_counts = census["gate"]["classification_counts"]
    lines.extend(f"- `{key}`: {gate_counts[key]}" for key in sorted(gate_counts))
    lines.extend(["", "## Source Families", ""])
    for family, row in census["by_family"].items():
        lines.append(
            f"- `{family}`: rows={row['source_rows']} units={row['source_units']} "
            f"candidates={row['deduped_candidates']} frequency={row['frequency']}"
        )
    return "\n".join(lines)


def _family_rows(records: Sequence[SourceInventoryRecord]) -> dict[str, list[SourceInventoryRecord]]:
    rows: dict[str, list[SourceInventoryRecord]] = defaultdict(list)
    for record in records:
        rows[record.source_family].append(record)
    return rows


def _family_payload(rows: Sequence[SourceInventoryRecord], *, registered: bool) -> dict[str, Any]:
    candidates = source_inventory_candidates(rows)
    source_units = _source_units(rows)
    extraction_modes = sorted({record.extraction_mode for record in rows})
    inventory_paths = sorted({record.inventory_path for record in rows})
    return {
        "registered": registered,
        "source_rows": len(rows),
        "source_units": len(source_units),
        "deduped_candidates": len(candidates),
        "frequency": sum(record.count for record in rows),
        "inventory_files": len(inventory_paths),
        "inventory_paths": inventory_paths,
        "extraction_modes": extraction_modes,
        "safe_locators": [_source_unit_payload(unit_rows) for unit_rows in source_units],
    }


def _source_units(
    records: Sequence[SourceInventoryRecord],
) -> list[list[SourceInventoryRecord]]:
    grouped: dict[tuple[str, str, str], list[SourceInventoryRecord]] = defaultdict(list)
    for record in records:
        key = (
            record.source_family,
            record.source_id or "<missing-source-id>",
            record.inventory_path,
        )
        grouped[key].append(record)
    return [grouped[key] for key in sorted(grouped)]


def _source_unit_count(records: Sequence[SourceInventoryRecord]) -> int:
    return len(_source_units(records))


def _source_unit_payload(rows: Sequence[SourceInventoryRecord]) -> dict[str, Any]:
    first = rows[0]
    locators = sorted({record.source_locator for record in rows if record.source_locator})
    source_paths = sorted({record.source_path for record in rows if record.source_path})
    return {
        "inventory_path": first.inventory_path,
        "source_id": first.source_id,
        "source_path": source_paths[0] if len(source_paths) == 1 else None,
        "source_locator": locators[0] if len(locators) == 1 else None,
        "source_locator_count": len(locators),
        "headword_rows": len(rows),
        "frequency": sum(record.count for record in rows),
    }


def _inventory_rows(
    records: Sequence[SourceInventoryRecord],
    inventory_paths: Sequence[Path],
    project_root: Path,
) -> list[dict[str, Any]]:
    by_path: dict[str, list[SourceInventoryRecord]] = defaultdict(list)
    for record in records:
        by_path[record.inventory_path].append(record)
    rows: list[dict[str, Any]] = []
    for path in inventory_paths:
        display_path = _display_path(path, project_root)
        path_records = by_path.get(display_path, [])
        rows.append(
            {
                "path": display_path,
                "source_families": sorted({record.source_family for record in path_records}),
                "source_units": _source_unit_count(path_records),
                "source_rows": len(path_records),
                "frequency": sum(record.count for record in path_records),
            }
        )
    return rows


def _display_path(path: Path, project_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(project_root.resolve()))
    except ValueError:
        return str(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--inventory",
        dest="inventory_paths",
        action="append",
        type=Path,
        help="Source inventory file to include; defaults to all committed source-inventory files.",
    )
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    inventory_paths = tuple(args.inventory_paths or discover_inventory_paths())
    if not inventory_paths:
        print("error: no source inventory files found", file=sys.stderr)
        return 2
    try:
        census = build_census(inventory_paths)
    except (FileNotFoundError, SourceInventoryError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.format == "markdown":
        print(format_markdown_census(census))
    else:
        print(json.dumps(census, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
