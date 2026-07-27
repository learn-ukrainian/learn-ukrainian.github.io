#!/usr/bin/env python3
"""Validator for TrailSpec v1 and StepReceipt v1 schemas and state machine invariants."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRAIL_SPEC_SCHEMA_PATH = (
    PROJECT_ROOT / "agents_extensions/shared/schemas/trailspec.v1.schema.json"
)
STEP_RECEIPT_SCHEMA_PATH = (
    PROJECT_ROOT / "agents_extensions/shared/schemas/step-receipt.v1.schema.json"
)
DEFAULT_EXAMPLE_TRAIL_PATH = (
    PROJECT_ROOT / "scripts/config/trails/rb3-pr-lifecycle.trail.yaml"
)
DECISION_TABLES_SCHEMA_PATH = (
    PROJECT_ROOT / "agents_extensions/shared/schemas/decision-tables.v0.schema.json"
)
DEFAULT_DECISION_TABLES_PATH = (
    PROJECT_ROOT / "scripts/config/trails/decision-tables.v0.yaml"
)

# Published STOP code contract (embedded constant; pending extraction to contract package)
VALID_STOP_CODES: set[str] = {
    "STOP-timeout",
    "STOP-verdict-timeout",
    "STOP-contested",
    "STOP-ci-red",
    "STOP-lease-expired",
    "STOP-precondition-failed",
    "STOP-max-retries-exceeded",
    "STOP-manual-intervention",
    "STOP-circuit-breaker",
    "STOP-concurrency-conflict",
    "STOP-policy-violation",
    "STOP-rate-limit",
    "STOP-unrecoverable-error",
    "STOP-quota-exceeded",
    "STOP-stale-head",
    "STOP-unknown",
    "STOP-rearm-failed",
    "STOP-hygiene-failed",
}


class TrailSpecValidationError(Exception):
    """Raised when TrailSpec or StepReceipt validation fails."""


def _load_yaml_or_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise TrailSpecValidationError(f"File not found: {path}")
    try:
        content = path.read_text(encoding="utf-8")
        data = (
            json.loads(content)
            if path.suffix == ".json"
            else yaml.safe_load(content)
        )
    except Exception as exc:
        raise TrailSpecValidationError(f"Parse error in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise TrailSpecValidationError(f"Root of {path} must be a mapping/dict")
    return data


def _load_schema(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise TrailSpecValidationError(f"Schema file not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise TrailSpecValidationError(f"JSON parse error in schema {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise TrailSpecValidationError(f"Root of schema {path} must be a dict")
    return data


def compute_trail_hash(data: dict[str, Any]) -> str:
    """Compute canonical-JSON SHA-256 hash of a parsed TrailSpec document.

    Canonicalization rule:
    Parse the document (YAML/JSON) into a Python dictionary, then serialize to
    compact JSON with keys sorted (sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    and compute SHA-256 hex digest. This ensures hash stability across formatting/whitespace
    changes while reflecting any semantic content mutation.
    """
    canonical_json = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def validate_step_receipt_data(
    receipt_data: dict[str, Any],
    *,
    receipt_schema_path: Path = STEP_RECEIPT_SCHEMA_PATH,
) -> dict[str, Any]:
    """Validate raw loaded dict against StepReceipt JSON Schema."""
    receipt_schema = _load_schema(receipt_schema_path)
    validator = Draft202012Validator(receipt_schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(receipt_data), key=lambda e: e.path)
    if errors:
        err = errors[0]
        raise TrailSpecValidationError(
            f"StepReceipt schema violation: {err.message} at {err.json_path}"
        )
    return {
        "ok": True,
        "step_id": receipt_data.get("step_id"),
        "run_id": receipt_data.get("run_id"),
    }


def validate_trailspec_data(
    spec_data: dict[str, Any],
    *,
    spec_schema_path: Path = TRAIL_SPEC_SCHEMA_PATH,
) -> dict[str, Any]:
    """Validate raw loaded dict against TrailSpec JSON Schema and domain invariants."""
    spec_schema = _load_schema(spec_schema_path)
    validator = Draft202012Validator(spec_schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(spec_data), key=lambda e: e.path)
    if errors:
        err = errors[0]
        raise TrailSpecValidationError(
            f"TrailSpec schema violation: {err.message} at {err.json_path}"
        )

    # Invariant 1: Stop codes must be from published contract list
    declared_stop_codes = set(spec_data.get("stop_codes", []))
    invalid_stops = declared_stop_codes - VALID_STOP_CODES
    if invalid_stops:
        raise TrailSpecValidationError(
            f"Unknown stop_code(s) {sorted(invalid_stops)}: must be from published 16-item contract list"
        )

    steps = spec_data.get("steps", [])
    step_ids = {s.get("step_id") for s in steps if s.get("step_id")}
    terminal_outcomes = set(spec_data.get("terminal_outcomes", []))

    valid_transition_targets = step_ids | declared_stop_codes | terminal_outcomes

    for step in steps:
        step_id = step.get("step_id", "<unknown>")
        kind = step.get("kind")
        evidence_predicate = step.get("evidence_predicate")

        # Invariant 2: No silent judgment steps (kind != summon must have evidence_predicate)
        if kind != "summon" and evidence_predicate is None:
            raise TrailSpecValidationError(
                f"No silent judgment steps invariant violated: step '{step_id}' with kind '{kind}' lacks an evidence_predicate"
            )

        # Invariant 3: Every transition target must exist in step_ids, stop_codes, or terminal_outcomes
        transitions = step.get("transitions", {})
        for label, target in transitions.items():
            if target not in valid_transition_targets:
                raise TrailSpecValidationError(
                    f"Dangling transition in step '{step_id}' (label '{label}'): target '{target}' does not exist in steps, stop_codes, or terminal_outcomes"
                )

    trail_hash = compute_trail_hash(spec_data)
    return {
        "ok": True,
        "trail_id": spec_data.get("trail_id"),
        "version": spec_data.get("version"),
        "steps_count": len(steps),
        "trail_hash": trail_hash,
    }


def validate_decision_tables_data(
    tables_data: dict[str, Any],
    *,
    tables_schema_path: Path = DECISION_TABLES_SCHEMA_PATH,
) -> dict[str, Any]:
    """Validate a decision-tables document against schema and domain invariants."""
    tables_schema = _load_schema(tables_schema_path)
    validator = Draft202012Validator(tables_schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(tables_data), key=lambda e: e.path)
    if errors:
        err = errors[0]
        raise TrailSpecValidationError(
            f"DecisionTables schema violation: {err.message} at {err.json_path}"
        )

    # Invariant: any row action naming a STOP code must use the published contract list.
    for table_name, table in tables_data.get("tables", {}).items():
        for idx, row in enumerate(table.get("rows", []) or []):
            then = row.get("then", "")
            if then.startswith("STOP-") and then not in VALID_STOP_CODES:
                raise TrailSpecValidationError(
                    f"DecisionTables invariant violated: table '{table_name}' row {idx} "
                    f"names unknown stop code '{then}' (must be from the published contract list)"
                )

    tables = tables_data.get("tables", {})
    return {
        "ok": True,
        "schema_version": tables_data.get("schema_version"),
        "precedence": tables_data.get("precedence"),
        "tables": sorted(tables.keys()),
        "tables_count": len(tables),
    }


def validate_decision_tables(
    tables_path: Path = DEFAULT_DECISION_TABLES_PATH,
    *,
    tables_schema_path: Path = DECISION_TABLES_SCHEMA_PATH,
) -> dict[str, Any]:
    """Validate a decision-tables YAML/JSON file."""
    tables_data = _load_yaml_or_json(tables_path)
    return validate_decision_tables_data(
        tables_data, tables_schema_path=tables_schema_path
    )


def validate_trail_table_refs(
    spec_data: dict[str, Any],
    tables_data: dict[str, Any],
) -> dict[str, Any]:
    """Cross-document check: table-lookup steps must bind a resolvable decision table.

    A missing, misspelled, or unbound reference is a validation failure, not a
    silent no-op. This also fails closed for callers that bypass JSON Schema.
    """
    known_tables = set(tables_data.get("tables", {}).keys())
    bound: dict[str, str] = {}
    for step in spec_data.get("steps", []):
        step_id = step.get("step_id", "<unknown>")
        table_ref = step.get("table")
        if step.get("kind") == "table-lookup" and (
            not isinstance(table_ref, str) or not table_ref
        ):
            raise TrailSpecValidationError(
                f"Missing table binding: table-lookup step '{step_id}' requires a non-empty "
                "string table field"
            )
        if table_ref is None:
            continue
        if table_ref not in known_tables:
            raise TrailSpecValidationError(
                f"Unbound table reference: step '{step_id}' names table '{table_ref}' "
                f"which does not exist in the decision-tables document "
                f"(known: {sorted(known_tables)})"
            )
        bound[step_id] = table_ref
    return {
        "ok": True,
        "trail_id": spec_data.get("trail_id"),
        "bound_steps": bound,
    }


def validate_trailspec(
    *,
    spec_path: Path = DEFAULT_EXAMPLE_TRAIL_PATH,
    receipt_path: Path | None = None,
    spec_schema_path: Path = TRAIL_SPEC_SCHEMA_PATH,
    receipt_schema_path: Path = STEP_RECEIPT_SCHEMA_PATH,
) -> dict[str, Any]:
    """Validate trail spec file and optional step receipt file."""
    spec_data = _load_yaml_or_json(spec_path)
    spec_summary = validate_trailspec_data(spec_data, spec_schema_path=spec_schema_path)

    receipt_summary = None
    if receipt_path is not None:
        receipt_data = _load_yaml_or_json(receipt_path)
        receipt_summary = validate_step_receipt_data(
            receipt_data, receipt_schema_path=receipt_schema_path
        )

    res = {
        "ok": True,
        "spec": spec_summary,
    }
    if receipt_summary is not None:
        res["receipt"] = receipt_summary
    return res


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate TrailSpec v1 and StepReceipt v1 instances."
    )
    parser.add_argument(
        "--spec",
        type=Path,
        default=DEFAULT_EXAMPLE_TRAIL_PATH,
        help="path to TrailSpec YAML/JSON file",
    )
    parser.add_argument(
        "--receipt",
        type=Path,
        default=None,
        help="optional path to StepReceipt JSON/YAML file",
    )
    parser.add_argument(
        "--tables",
        type=Path,
        default=None,
        help="optional path to a decision-tables YAML/JSON file to validate",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="output machine-readable JSON",
    )
    args = parser.parse_args(argv)

    try:
        summary = validate_trailspec(
            spec_path=args.spec.resolve(),
            receipt_path=args.receipt.resolve() if args.receipt else None,
        )
        if args.tables is not None:
            tables_path = args.tables.resolve()
            summary["decision_tables"] = validate_decision_tables(tables_path)
            # Cross-document check: declared table references must resolve. Without
            # this, the CLI would report success on a misspelled/unbound reference
            # even though both documents validate independently.
            summary["table_refs"] = validate_trail_table_refs(
                _load_yaml_or_json(args.spec.resolve()),
                _load_yaml_or_json(tables_path),
            )
    except TrailSpecValidationError as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        else:
            print(f"TrailSpec validation error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(summary, sort_keys=True, indent=2))
    else:
        spec_info = summary["spec"]
        print(
            f"TrailSpec valid: id='{spec_info['trail_id']}' version='{spec_info['version']}' "
            f"steps={spec_info['steps_count']} hash={spec_info['trail_hash']}"
        )
        if "receipt" in summary:
            print(f"StepReceipt valid: step_id='{summary['receipt']['step_id']}'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
