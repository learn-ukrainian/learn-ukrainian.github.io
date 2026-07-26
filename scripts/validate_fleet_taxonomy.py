#!/usr/bin/env python3
"""Validator for fleet taxonomy and area assignments registries."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker, ValidationError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_PATH = PROJECT_ROOT / "scripts/config/fleet_taxonomy.yaml"
ASSIGNMENTS_PATH = PROJECT_ROOT / "scripts/config/area_assignments.yaml"
TAXONOMY_SCHEMA_PATH = (
    PROJECT_ROOT / "agents_extensions/shared/schemas/fleet-taxonomy.v1.schema.json"
)
ASSIGNMENTS_SCHEMA_PATH = (
    PROJECT_ROOT / "agents_extensions/shared/schemas/area-assignments.v1.schema.json"
)


class FleetTaxonomyValidationError(Exception):
    """Raised when fleet taxonomy or area assignments validation fails."""


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FleetTaxonomyValidationError(f"File not found: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise FleetTaxonomyValidationError(f"YAML parse error in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise FleetTaxonomyValidationError(f"Root of {path} must be a mapping/dict")
    return data


def _load_schema(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FleetTaxonomyValidationError(f"Schema file not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise FleetTaxonomyValidationError(f"JSON parse error in schema {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise FleetTaxonomyValidationError(f"Root of schema {path} must be a dict")
    return data


def validate_schemas(
    taxonomy_data: dict[str, Any],
    assignments_data: dict[str, Any],
    *,
    taxonomy_schema_path: Path = TAXONOMY_SCHEMA_PATH,
    assignments_schema_path: Path = ASSIGNMENTS_SCHEMA_PATH,
) -> None:
    """Validate raw loaded dicts against JSON Schemas."""
    tax_schema = _load_schema(taxonomy_schema_path)
    ass_schema = _load_schema(assignments_schema_path)

    tax_validator = Draft202012Validator(tax_schema, format_checker=FormatChecker())
    tax_errors = sorted(tax_validator.iter_errors(taxonomy_data), key=lambda e: e.path)
    if tax_errors:
        err = tax_errors[0]
        raise FleetTaxonomyValidationError(
            f"fleet_taxonomy schema violation: {err.message} at {err.json_path}"
        )

    ass_validator = Draft202012Validator(ass_schema, format_checker=FormatChecker())
    ass_errors = sorted(ass_validator.iter_errors(assignments_data), key=lambda e: e.path)
    if ass_errors:
        err = ass_errors[0]
        raise FleetTaxonomyValidationError(
            f"area_assignments schema violation: {err.message} at {err.json_path}"
        )


def validate_injective_aliases(areas: dict[str, Any]) -> dict[str, str]:
    """Enforce that every alias and canonical area ID maps to exactly ONE area."""
    alias_to_area: dict[str, str] = {}
    for area_id, area_data in areas.items():
        if area_data.get("id") != area_id:
            raise FleetTaxonomyValidationError(
                f"Area key '{area_id}' does not match inner id '{area_data.get('id')}'"
            )
        aliases = area_data.get("aliases", [])
        names = set(aliases) | {area_id}
        for name in names:
            if name in alias_to_area:
                prev_area = alias_to_area[name]
                raise FleetTaxonomyValidationError(
                    f"Alias/name '{name}' is not injective: claimed by area '{prev_area}' and area '{area_id}'"
                )
            alias_to_area[name] = area_id
    return alias_to_area


def validate_epic_uniqueness(areas: dict[str, Any]) -> dict[int, str]:
    """Enforce that each epic number belongs to exactly ONE area."""
    epic_to_area: dict[int, str] = {}
    for area_id, area_data in areas.items():
        for epic in area_data.get("epics", []):
            num = epic.get("number")
            if not isinstance(num, int):
                raise FleetTaxonomyValidationError(
                    f"Epic number must be an integer in area '{area_id}'"
                )
            if num in epic_to_area:
                prev_area = epic_to_area[num]
                raise FleetTaxonomyValidationError(
                    f"Epic number {num} belongs to multiple areas: '{prev_area}' and '{area_id}'"
                )
            epic_to_area[num] = area_id
    return epic_to_area


def validate_area_assignments_parity(
    areas: dict[str, Any], assignments: dict[str, Any]
) -> None:
    """Enforce that every area in area_assignments exists in fleet_taxonomy and vice versa."""
    taxonomy_areas = set(areas.keys())
    assignment_areas = set(assignments.keys())

    missing_in_taxonomy = assignment_areas - taxonomy_areas
    if missing_in_taxonomy:
        missing_sorted = sorted(missing_in_taxonomy)
        raise FleetTaxonomyValidationError(
            f"Assignment for unknown area(s) in area_assignments.yaml: {missing_sorted}"
        )

    missing_in_assignments = taxonomy_areas - assignment_areas
    if missing_in_assignments:
        missing_sorted = sorted(missing_in_assignments)
        raise FleetTaxonomyValidationError(
            f"Area(s) in fleet_taxonomy.yaml missing from area_assignments.yaml: {missing_sorted}"
        )


def validate_fleet_taxonomy(
    *,
    taxonomy_path: Path = TAXONOMY_PATH,
    assignments_path: Path = ASSIGNMENTS_PATH,
    taxonomy_schema_path: Path = TAXONOMY_SCHEMA_PATH,
    assignments_schema_path: Path = ASSIGNMENTS_SCHEMA_PATH,
) -> dict[str, Any]:
    """Validate both fleet_taxonomy.yaml and area_assignments.yaml."""
    taxonomy_data = _load_yaml(taxonomy_path)
    assignments_data = _load_yaml(assignments_path)

    validate_schemas(
        taxonomy_data,
        assignments_data,
        taxonomy_schema_path=taxonomy_schema_path,
        assignments_schema_path=assignments_schema_path,
    )

    areas = taxonomy_data["areas"]
    assignments = assignments_data["assignments"]

    alias_to_area = validate_injective_aliases(areas)
    epic_to_area = validate_epic_uniqueness(areas)
    validate_area_assignments_parity(areas, assignments)

    return {
        "ok": True,
        "areas_count": len(areas),
        "epics_count": len(epic_to_area),
        "aliases_count": len(alias_to_area),
        "assignments_count": len(assignments),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate fleet taxonomy and area assignments registries."
    )
    parser.add_argument(
        "--taxonomy",
        type=Path,
        default=TAXONOMY_PATH,
        help="path to fleet_taxonomy.yaml",
    )
    parser.add_argument(
        "--assignments",
        type=Path,
        default=ASSIGNMENTS_PATH,
        help="path to area_assignments.yaml",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="output machine-readable JSON",
    )
    args = parser.parse_args(argv)

    try:
        summary = validate_fleet_taxonomy(
            taxonomy_path=args.taxonomy.resolve(),
            assignments_path=args.assignments.resolve(),
        )
    except FleetTaxonomyValidationError as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        else:
            print(f"Fleet taxonomy validation error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(summary, sort_keys=True, indent=2))
    else:
        print(
            f"Fleet taxonomy valid: {summary['areas_count']} areas, "
            f"{summary['epics_count']} epics, {summary['aliases_count']} aliases, "
            f"{summary['assignments_count']} assignments."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
