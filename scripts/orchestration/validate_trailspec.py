#!/usr/bin/env python3
"""Validate TrailSpec v1/v1.1 and their receipt contracts.

TrailSpec v1 remains an immutable, schema-valid historical format.  The
validator deliberately reports it as execution-ineligible: a prose predicate
cannot be soundly compiled into an executable receipt predicate.  v1.1 adds the
receipt-bound command and transition contracts needed by a future runner.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import UTC, datetime
from itertools import product
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.orchestration.red_ci_known_failures import (
    VALID_STOP_CODES,
    RedCIKnownFailuresValidationError,
    load_and_validate_registry,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRAIL_SPEC_SCHEMA_PATH = (
    PROJECT_ROOT / "agents_extensions/shared/schemas/trailspec.v1.schema.json"
)
TRAIL_SPEC_V11_SCHEMA_PATH = (
    PROJECT_ROOT / "agents_extensions/shared/schemas/trailspec.v1.1.schema.json"
)
STEP_RECEIPT_SCHEMA_PATH = (
    PROJECT_ROOT / "agents_extensions/shared/schemas/step-receipt.v1.schema.json"
)
STEP_RECEIPT_V11_SCHEMA_PATH = (
    PROJECT_ROOT / "agents_extensions/shared/schemas/step-receipt.v1.1.schema.json"
)
COMMAND_RECEIPT_SCHEMA_PATH = (
    PROJECT_ROOT / "agents_extensions/shared/schemas/command-receipt.v1.schema.json"
)
SEAT_TAXONOMY_PATH = PROJECT_ROOT / "scripts/config/fleet_communications.yaml"
DEFAULT_EXAMPLE_TRAIL_PATH = (
    PROJECT_ROOT / "scripts/config/trails/rb3-pr-lifecycle.trail.yaml"
)
DECISION_TABLES_SCHEMA_PATH = (
    PROJECT_ROOT / "agents_extensions/shared/schemas/decision-tables.v0.schema.json"
)
DECISION_TABLES_V1_SCHEMA_PATH = (
    PROJECT_ROOT / "agents_extensions/shared/schemas/decision-tables.v1.schema.json"
)
ESTATE_REGISTRY_SCHEMA_PATH = (
    PROJECT_ROOT / "agents_extensions/shared/schemas/estate-registry.v1.schema.json"
)
DEFAULT_DECISION_TABLES_PATH = (
    PROJECT_ROOT / "scripts/config/trails/decision-tables.v0.yaml"
)
DEFAULT_DECISION_TABLES_V1_PATH = (
    PROJECT_ROOT / "scripts/config/trails/decision-tables.v1.yaml"
)
DEFAULT_ESTATE_REGISTRY_PATH = (
    PROJECT_ROOT / "scripts/config/trails/estate.v1.yaml"
)

_TRAIL_SCHEMA_PATHS = {
    "trailspec.v1": TRAIL_SPEC_SCHEMA_PATH,
    "trailspec.v1.1": TRAIL_SPEC_V11_SCHEMA_PATH,
}
_STEP_RECEIPT_SCHEMA_PATHS = {
    "step-receipt.v1": STEP_RECEIPT_SCHEMA_PATH,
    "step-receipt.v1.1": STEP_RECEIPT_V11_SCHEMA_PATH,
}
_DECISION_TABLES_SCHEMA_PATHS = {
    "decision-tables.v0": DECISION_TABLES_SCHEMA_PATH,
    "decision-tables.v1": DECISION_TABLES_V1_SCHEMA_PATH,
}
_PARAMETER_REFERENCE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")

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


def _compute_canonical_json_digest(data: dict[str, Any]) -> str:
    """Return a SHA-256 digest of semantic JSON data, independent of formatting."""
    canonical_json = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def compute_trail_hash(data: dict[str, Any]) -> str:
    """Compute canonical-JSON SHA-256 hash of a parsed TrailSpec document.

    Canonicalization rule:
    Parse the document (YAML/JSON) into a Python dictionary, then serialize to
    compact JSON with keys sorted (sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    and compute SHA-256 hex digest. This ensures hash stability across formatting/whitespace
    changes while reflecting any semantic content mutation.
    """
    return _compute_canonical_json_digest(data)


def compute_command_receipt_digest(data: dict[str, Any]) -> str:
    """Compute the canonical digest referenced by StepReceipt.command_receipt_digest."""
    return _compute_canonical_json_digest(data)


def _schema_path_for(
    data: dict[str, Any],
    *,
    paths: dict[str, Path],
    label: str,
    supplied_path: Path | None,
) -> Path:
    """Resolve a versioned schema unless a caller explicitly pins one."""
    if supplied_path is not None:
        return supplied_path
    version = data.get("schema_version")
    if not isinstance(version, str) or version not in paths:
        raise TrailSpecValidationError(
            f"Unsupported {label} schema_version {version!r}; expected one of {sorted(paths)}"
        )
    return paths[version]


def _validate_against_schema(
    data: dict[str, Any],
    *,
    schema_path: Path,
    label: str,
) -> None:
    schema = _load_schema(schema_path)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(data), key=lambda error: error.path)
    if errors:
        err = errors[0]
        raise TrailSpecValidationError(
            f"{label} schema violation: {err.message} at {err.json_path}"
        )


def validate_step_receipt_data(
    receipt_data: dict[str, Any],
    *,
    receipt_schema_path: Path | None = None,
) -> dict[str, Any]:
    """Validate raw loaded dict against the version-selected StepReceipt schema."""
    resolved_schema_path = _schema_path_for(
        receipt_data,
        paths=_STEP_RECEIPT_SCHEMA_PATHS,
        label="StepReceipt",
        supplied_path=receipt_schema_path,
    )
    _validate_against_schema(
        receipt_data, schema_path=resolved_schema_path, label="StepReceipt"
    )
    return {
        "ok": True,
        "schema_version": receipt_data.get("schema_version"),
        "step_id": receipt_data.get("step_id"),
        "run_id": receipt_data.get("run_id"),
    }


def validate_command_receipt_data(
    receipt_data: dict[str, Any],
    *,
    receipt_schema_path: Path = COMMAND_RECEIPT_SCHEMA_PATH,
) -> dict[str, Any]:
    """Validate a CommandReceipt v1 document independently of a step receipt."""
    _validate_against_schema(
        receipt_data, schema_path=receipt_schema_path, label="CommandReceipt"
    )
    return {
        "ok": True,
        "invocation_id": receipt_data.get("invocation_id"),
        "step_id": receipt_data.get("step_id"),
        "status": receipt_data.get("status"),
    }


def _load_eligible_seats(seat_registry_path: Path) -> set[str]:
    """Return active seat names from the live fleet taxonomy registry.

    v1.1 deliberately does not carry a static seat enum: endpoint membership
    and state are the registry-controlled eligibility contract.  ``retired``
    endpoints are excluded even though their historic names remain recorded.
    """
    registry = _load_yaml_or_json(seat_registry_path)
    endpoints = registry.get("endpoints")
    if not isinstance(endpoints, list):
        raise TrailSpecValidationError(
            f"Seat taxonomy registry {seat_registry_path} must contain an endpoints list"
        )

    eligible: set[str] = set()
    for endpoint in endpoints:
        if not isinstance(endpoint, dict):
            raise TrailSpecValidationError(
                f"Seat taxonomy registry {seat_registry_path} contains a non-mapping endpoint"
            )
        name = endpoint.get("name")
        state = endpoint.get("state")
        if not isinstance(name, str) or not name:
            raise TrailSpecValidationError(
                f"Seat taxonomy registry {seat_registry_path} has an endpoint without a name"
            )
        if state in {"live", "local_only"}:
            eligible.add(name)
    if not eligible:
        raise TrailSpecValidationError(
            f"Seat taxonomy registry {seat_registry_path} has no eligible live endpoints"
        )
    return eligible


def _validate_v11_seats(spec_data: dict[str, Any], seat_registry_path: Path) -> None:
    eligible = _load_eligible_seats(seat_registry_path)
    unknown = sorted(set(spec_data["seats"]) - eligible)
    if unknown:
        raise TrailSpecValidationError(
            "TrailSpec v1.1 seat eligibility failed: "
            f"{unknown} not present as live/local_only endpoints in {seat_registry_path} "
            f"(eligible: {sorted(eligible)})"
        )


def _validate_v11_invocation_fields(spec_data: dict[str, Any]) -> None:
    """Enforce the static invocation binding that the runner must preserve."""
    declared_parameters = set(spec_data["parameters"])
    for step in spec_data["steps"]:
        step_id = step["step_id"]
        command = step["command"]
        environment = command["environment"]
        if environment.get("TRAIL_INVOCATION_ID") != "{invocation_id}":
            raise TrailSpecValidationError(
                f"Invocation binding violated: step '{step_id}' must set "
                "TRAIL_INVOCATION_ID to '{invocation_id}'"
            )

        argv = command["argv"]
        if command["adapter"] == "typed-primitive":
            try:
                invocation_flag_index = argv.index("--invocation-id")
            except ValueError as exc:
                raise TrailSpecValidationError(
                    f"Invocation binding violated: typed-primitive step '{step_id}' "
                    "must pass --invocation-id {invocation_id}"
                ) from exc
            if (
                invocation_flag_index + 1 >= len(argv)
                or argv[invocation_flag_index + 1] != "{invocation_id}"
            ):
                raise TrailSpecValidationError(
                    f"Invocation binding violated: typed-primitive step '{step_id}' "
                    "must pass --invocation-id {invocation_id}"
                )

        if command["adapter"] == "shell":
            # Fail-closed shell-invocation shape (review finding on #5963): matching
            # only a literal "-c" token let `sh -lc`, `bash --login -c`, `-ec`, etc.
            # smuggle parameter interpolation into a shell-interpreted program string.
            # The shell adapter execs argv DIRECTLY, so a plain command with parameters
            # as discrete argv elements is safe. But if argv[0] is a shell binary (or a
            # wrapper that could reach one), the ONLY accepted shape is exactly
            # [sh|bash, -c, <program>] and the program token may not reference
            # parameters — every other flag spelling or layout is rejected outright.
            _SHELL_BINARIES = {"sh", "bash", "zsh", "dash", "ksh"}
            _WRAPPER_BINARIES = {"env", "nohup", "stdbuf", "nice", "timeout", "xargs"}
            argv0_base = argv[0].rsplit("/", 1)[-1]
            if argv0_base in _WRAPPER_BINARIES:
                raise TrailSpecValidationError(
                    f"Unsupported shell invocation shape in step '{step_id}': wrapper "
                    f"'{argv0_base}' indirection is not allowed for the shell adapter"
                )
            if argv0_base in _SHELL_BINARIES:
                if len(argv) != 3 or argv0_base not in ("sh", "bash") or argv[1] != "-c":
                    raise TrailSpecValidationError(
                        f"Unsupported shell invocation shape in step '{step_id}': "
                        "shell-binary invocations accept exactly [sh|bash, -c, "
                        "<program>] — no other flags or argument layouts"
                    )
                if _PARAMETER_REFERENCE.search(argv[2]):
                    raise TrailSpecValidationError(
                        f"Unquoted parameter interpolation prohibited: shell step "
                        f"'{step_id}' must pass parameters through argv/environment, "
                        "not a -c program"
                    )

        values_to_check = [*argv, *environment.values()]
        for value in values_to_check:
            for reference in _PARAMETER_REFERENCE.findall(value):
                if reference != "invocation_id" and reference not in declared_parameters:
                    raise TrailSpecValidationError(
                        f"Undeclared command parameter '{reference}' in step '{step_id}'"
                    )


def _validate_v11_transition_predicates(spec_data: dict[str, Any]) -> None:
    """Require one distinct, receipt-only predicate identity for every transition."""
    for step in spec_data["steps"]:
        predicate_ids: set[str] = set()
        transitions = step["transitions"]
        for label, transition in transitions.items():
            evidence = transition["evidence"]
            predicate_id = evidence["predicate_id"]
            if predicate_id in predicate_ids:
                raise TrailSpecValidationError(
                    f"Exactly-one-predicate rule violated: step '{step['step_id']}' "
                    f"reuses predicate_id '{predicate_id}' in its transition set"
                )
            predicate_ids.add(predicate_id)
            for clause in evidence["clauses"]:
                if clause["source"] != "command_receipt":
                    raise TrailSpecValidationError(
                        f"Predicate command-execution prohibition violated: step '{step['step_id']}' "
                        f"transition '{label}' must reference command_receipt fields only"
                    )


def _transition_targets(step: dict[str, Any], *, is_v11: bool) -> list[str]:
    transitions = step.get("transitions", {})
    if is_v11:
        return [transition["target"] for transition in transitions.values()]
    return list(transitions.values())


def validate_trailspec_data(
    spec_data: dict[str, Any],
    *,
    spec_schema_path: Path | None = None,
    seat_registry_path: Path = SEAT_TAXONOMY_PATH,
) -> dict[str, Any]:
    """Validate raw loaded dict against TrailSpec JSON Schema and domain invariants."""
    resolved_schema_path = _schema_path_for(
        spec_data,
        paths=_TRAIL_SCHEMA_PATHS,
        label="TrailSpec",
        supplied_path=spec_schema_path,
    )
    _validate_against_schema(
        spec_data, schema_path=resolved_schema_path, label="TrailSpec"
    )
    is_v11 = spec_data["schema_version"] == "trailspec.v1.1"

    # Invariant 1: Stop codes must be from published contract list
    declared_stop_codes = set(spec_data.get("stop_codes", []))
    invalid_stops = declared_stop_codes - VALID_STOP_CODES
    if invalid_stops:
        raise TrailSpecValidationError(
            f"Unknown stop_code(s) {sorted(invalid_stops)}: must be from the published 18-code STOP vocabulary"
        )

    steps = spec_data.get("steps", [])
    step_ids = {s.get("step_id") for s in steps if s.get("step_id")}
    terminal_outcomes = set(spec_data.get("terminal_outcomes", []))

    valid_transition_targets = step_ids | declared_stop_codes | terminal_outcomes

    for step in steps:
        step_id = step.get("step_id", "<unknown>")
        kind = step.get("kind")
        evidence_predicate = step.get("evidence_predicate")

        # v1's prose predicate contract is retained only for backward-compatible
        # validation. v1.1 has one receipt predicate per transition instead.
        if not is_v11 and kind != "summon" and evidence_predicate is None:
            raise TrailSpecValidationError(
                f"No silent judgment steps invariant violated: step '{step_id}' with kind '{kind}' lacks an evidence_predicate"
            )

        for label, transition in step.get("transitions", {}).items():
            target = transition["target"] if is_v11 else transition
            if target not in valid_transition_targets:
                raise TrailSpecValidationError(
                    f"Dangling transition in step '{step_id}' (label '{label}'): target '{target}' does not exist in steps, stop_codes, or terminal_outcomes"
                )

        if is_v11:
            blocked_on = step.get("blocked_on")
            if blocked_on is not None:
                stop_code = blocked_on["stop_code"]
                if stop_code not in VALID_STOP_CODES:
                    raise TrailSpecValidationError(
                        f"Blocked step '{step_id}' names unknown stop_code '{stop_code}'"
                    )
                if stop_code not in declared_stop_codes:
                    raise TrailSpecValidationError(
                        f"Blocked step '{step_id}' stop_code '{stop_code}' must be declared by the trail"
                    )

    if is_v11:
        _validate_v11_seats(spec_data, seat_registry_path)
        _validate_v11_invocation_fields(spec_data)
        _validate_v11_transition_predicates(spec_data)

    # Invariant 4: Graph reachability — every step must be reachable from the first step
    if steps:
        first_step_id = steps[0].get("step_id")
        step_id_to_step = {s.get("step_id"): s for s in steps if s.get("step_id")}

        visited: set[str] = set()
        queue = [first_step_id] if first_step_id in step_id_to_step else []
        while queue:
            curr = queue.pop()
            if curr in visited:
                continue
            visited.add(curr)
            curr_step = step_id_to_step.get(curr, {})
            for target in _transition_targets(curr_step, is_v11=is_v11):
                if target in step_id_to_step and target not in visited:
                    queue.append(target)

        unreachable = sorted(step_ids - visited)
        if unreachable:
            raise TrailSpecValidationError(
                f"Unreachable step(s) {unreachable}: not reachable from start step '{first_step_id}'"
            )

    trail_hash = compute_trail_hash(spec_data)
    return {
        "ok": True,
        "trail_id": spec_data.get("trail_id"),
        "version": spec_data.get("version"),
        "steps_count": len(steps),
        "trail_hash": trail_hash,
        "execution_eligible": is_v11,
        **(
            {}
            if is_v11
            else {
                "execution_refusal": "TrailSpec v1 is schema-valid but execution-ineligible; "
                "the runner must refuse v1 execution and closure."
            }
        ),
    }


def _validate_v11_receipt_binding(
    spec_data: dict[str, Any],
    step_receipt_data: dict[str, Any],
    command_receipt_data: dict[str, Any] | None = None,
) -> None:
    """Bind v1.1 receipts to the immutable pinned trail and selected predicate."""
    expected_values = {
        "trail_id": spec_data["trail_id"],
        "trail_version": spec_data["version"],
        "trail_hash": compute_trail_hash(spec_data),
    }
    for field, expected in expected_values.items():
        if step_receipt_data[field] != expected:
            raise TrailSpecValidationError(
                f"StepReceipt binding violated: {field}={step_receipt_data[field]!r} "
                f"does not match pinned trail value {expected!r}"
            )

    step_by_id = {step["step_id"]: step for step in spec_data["steps"]}
    step_id = step_receipt_data["step_id"]
    step = step_by_id.get(step_id)
    if step is None:
        raise TrailSpecValidationError(
            f"StepReceipt binding violated: unknown step_id '{step_id}'"
        )

    transition_taken = step_receipt_data["transition_taken"]
    transition = step["transitions"].get(transition_taken)
    if transition is None:
        raise TrailSpecValidationError(
            f"StepReceipt transition_taken must be a transition label, not a target: "
            f"'{transition_taken}' is not a label for step '{step_id}'"
        )
    expected_predicate_id = transition["evidence"]["predicate_id"]
    if step_receipt_data["predicate_id"] != expected_predicate_id:
        raise TrailSpecValidationError(
            f"StepReceipt predicate_id '{step_receipt_data['predicate_id']}' does not match "
            f"transition label '{transition_taken}' predicate '{expected_predicate_id}'"
        )

    if command_receipt_data is None:
        return

    command_expected_values = {
        **expected_values,
        "run_id": step_receipt_data["run_id"],
        "step_id": step_id,
        "invocation_id": step_receipt_data["invocation_id"],
        "actor_outcome": step_receipt_data["actor_outcome"],
    }
    for field, expected in command_expected_values.items():
        if command_receipt_data[field] != expected:
            raise TrailSpecValidationError(
                f"CommandReceipt binding violated: {field}={command_receipt_data[field]!r} "
                f"does not match bound StepReceipt/trail value {expected!r}"
            )

    matching_labels = [
        label
        for label, candidate in step["transitions"].items()
        if all(
            command_receipt_data[clause["field"]] == clause["value"]
            for clause in candidate["evidence"]["clauses"]
        )
    ]
    if len(matching_labels) != 1:
        raise TrailSpecValidationError(
            f"Exactly-one-predicate match rule violated for step '{step_id}': "
            f"matched {matching_labels}; runner must park this invocation as STOP-unknown"
        )
    if transition_taken != matching_labels[0]:
        raise TrailSpecValidationError(
            f"StepReceipt transition_taken '{transition_taken}' does not match command "
            f"receipt predicate result '{matching_labels[0]}'"
        )

    if (
        compute_command_receipt_digest(command_receipt_data)
        != step_receipt_data["command_receipt_digest"]
    ):
        raise TrailSpecValidationError(
            "StepReceipt command_receipt_digest does not match the canonical CommandReceipt digest"
        )


def _v1_input_domain(input_name: str, definition: dict[str, Any]) -> list[bool | str]:
    """Return a declared finite input domain or reject a malformed static table."""
    if definition["type"] == "boolean":
        return [False, True]
    if definition["type"] == "enum":
        return definition["values"]
    raise TrailSpecValidationError(
        f"DecisionTables v1 input '{input_name}' has unsupported type "
        f"{definition['type']!r}"
    )


def _validate_v1_condition(
    *,
    table_name: str,
    row_id: str,
    condition: dict[str, Any],
    declarations: dict[str, Any],
) -> None:
    """Check that a v1 condition references a declared input using its real type."""
    input_name = condition["input"]
    if input_name not in declarations:
        raise TrailSpecValidationError(
            f"DecisionTables v1 table '{table_name}' row '{row_id}' references "
            f"undeclared input '{input_name}'"
        )
    definition = declarations[input_name]
    expected_values = (
        [condition["equals"]]
        if "equals" in condition
        else condition["one_of"]
    )
    for expected in expected_values:
        if definition["type"] == "boolean":
            valid = type(expected) is bool
        else:
            valid = isinstance(expected, str) and expected in definition["values"]
        if not valid:
            raise TrailSpecValidationError(
                f"DecisionTables v1 table '{table_name}' row '{row_id}' condition "
                f"for input '{input_name}' has invalid typed value {expected!r}"
            )


def _v1_row_matches(row: dict[str, Any], candidate: dict[str, bool | str]) -> bool:
    """Evaluate a schema-validated row against one finite-domain input tuple."""
    for condition in row["when"]["all"]:
        value = candidate[condition["input"]]
        if "equals" in condition:
            if value != condition["equals"]:
                return False
        elif value not in condition["one_of"]:
            return False
    return True


def _validate_v1_decision_table_uniqueness(tables_data: dict[str, Any]) -> None:
    """Reject v1 static rows that overlap in any declared typed input tuple.

    Empty regions are deliberately allowed: runtime evaluation parks them as
    STOP-unknown. This check enforces the complementary safety property that a
    row order cannot silently choose between multiple matching outcomes.
    """
    for table_name, table in tables_data["tables"].items():
        if table["mode"] != "static":
            continue
        declarations = table["inputs"]
        row_ids = [row["id"] for row in table["rows"]]
        if len(row_ids) != len(set(row_ids)):
            raise TrailSpecValidationError(
                f"DecisionTables v1 table '{table_name}' has duplicate row id(s)"
            )
        for row in table["rows"]:
            for condition in row["when"]["all"]:
                _validate_v1_condition(
                    table_name=table_name,
                    row_id=row["id"],
                    condition=condition,
                    declarations=declarations,
                )

        input_names = list(declarations)
        domains = [_v1_input_domain(name, declarations[name]) for name in input_names]
        for values in product(*domains):
            candidate = dict(zip(input_names, values, strict=True))
            matches = [
                row["id"]
                for row in table["rows"]
                if _v1_row_matches(row, candidate)
            ]
            if len(matches) > 1:
                raise TrailSpecValidationError(
                    "DecisionTables v1 first-match uniqueness violated: "
                    f"table '{table_name}' rows {matches} match typed inputs {candidate}"
                )


def validate_decision_tables_data(
    tables_data: dict[str, Any],
    *,
    tables_schema_path: Path | None = None,
) -> dict[str, Any]:
    """Validate a decision-tables document against schema and domain invariants."""
    resolved_schema_path = _schema_path_for(
        tables_data,
        paths=_DECISION_TABLES_SCHEMA_PATHS,
        label="DecisionTables",
        supplied_path=tables_schema_path,
    )
    tables_schema = _load_schema(resolved_schema_path)
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
            if tables_data["schema_version"] == "decision-tables.v0":
                token = row.get("then", "")
            else:
                outcome = row.get("outcome", {})
                token = outcome.get("token", "") if isinstance(outcome, dict) else ""
            if token.startswith("STOP-") and token not in VALID_STOP_CODES:
                raise TrailSpecValidationError(
                    f"DecisionTables invariant violated: table '{table_name}' row {idx} "
                    f"names unknown stop code '{token}' (must be from the published contract list)"
                )

    if tables_data["schema_version"] == "decision-tables.v1":
        _validate_v1_decision_table_uniqueness(tables_data)

    tables = tables_data.get("tables", {})
    return {
        "ok": True,
        "schema_version": tables_data.get("schema_version"),
        "precedence": tables_data.get(
            "precedence", tables_data.get("matching_policy")
        ),
        "tables": sorted(tables.keys()),
        "tables_count": len(tables),
    }


def validate_decision_tables(
    tables_path: Path = DEFAULT_DECISION_TABLES_PATH,
    *,
    tables_schema_path: Path | None = None,
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


def validate_registry(
    registry_path: Path,
    *,
    as_of: str | datetime | None = None,
) -> dict[str, Any]:
    """Validate a red-CI known-failures registry document via red_ci_known_failures module."""
    resolved_as_of = datetime.now(UTC) if as_of is None else as_of
    try:
        return load_and_validate_registry(registry_path, as_of=resolved_as_of)
    except RedCIKnownFailuresValidationError as exc:
        raise TrailSpecValidationError(str(exc)) from exc


def validate_estate_registry_data(
    registry_data: dict[str, Any],
    *,
    schema_path: Path = ESTATE_REGISTRY_SCHEMA_PATH,
) -> dict[str, Any]:
    """Validate raw loaded dict against EstateRegistry schema."""
    _validate_against_schema(
        registry_data, schema_path=schema_path, label="EstateRegistry"
    )
    return {
        "ok": True,
        "schema_version": registry_data.get("schema_version"),
        "version": registry_data.get("version"),
        "refused_surfaces_count": len(registry_data.get("refused_mutation_surfaces", [])),
    }


def validate_estate_registry(
    registry_path: Path = DEFAULT_ESTATE_REGISTRY_PATH,
    *,
    schema_path: Path = ESTATE_REGISTRY_SCHEMA_PATH,
) -> dict[str, Any]:
    """Validate an estate-registry YAML/JSON file."""
    registry_data = _load_yaml_or_json(registry_path)
    return validate_estate_registry_data(registry_data, schema_path=schema_path)



def validate_trailspec(
    *,
    spec_path: Path = DEFAULT_EXAMPLE_TRAIL_PATH,
    receipt_path: Path | None = None,
    command_receipt_path: Path | None = None,
    registry_path: Path | None = None,
    as_of: str | datetime | None = None,
    spec_schema_path: Path | None = None,
    receipt_schema_path: Path | None = None,
    command_receipt_schema_path: Path = COMMAND_RECEIPT_SCHEMA_PATH,
    seat_registry_path: Path = SEAT_TAXONOMY_PATH,
) -> dict[str, Any]:
    """Validate a versioned trail spec and its optional receipt projections."""
    spec_data = _load_yaml_or_json(spec_path)
    spec_summary = validate_trailspec_data(
        spec_data,
        spec_schema_path=spec_schema_path,
        seat_registry_path=seat_registry_path,
    )

    receipt_summary = None
    step_receipt_data = None
    if receipt_path is not None:
        step_receipt_data = _load_yaml_or_json(receipt_path)
        receipt_summary = validate_step_receipt_data(
            step_receipt_data, receipt_schema_path=receipt_schema_path
        )

    command_receipt_summary = None
    command_receipt_data = None
    if command_receipt_path is not None:
        command_receipt_data = _load_yaml_or_json(command_receipt_path)
        command_receipt_summary = validate_command_receipt_data(
            command_receipt_data, receipt_schema_path=command_receipt_schema_path
        )

    is_v11 = spec_data["schema_version"] == "trailspec.v1.1"
    if not is_v11 and command_receipt_data is not None:
        raise TrailSpecValidationError(
            "TrailSpec v1 is execution-ineligible and cannot bind a CommandReceipt"
        )
    if step_receipt_data is not None:
        expected_receipt_version = "step-receipt.v1.1" if is_v11 else "step-receipt.v1"
        if step_receipt_data["schema_version"] != expected_receipt_version:
            raise TrailSpecValidationError(
                f"TrailSpec {spec_data['schema_version']} requires {expected_receipt_version}, "
                f"got {step_receipt_data['schema_version']}"
            )
        if is_v11:
            _validate_v11_receipt_binding(
                spec_data, step_receipt_data, command_receipt_data
            )
    elif command_receipt_data is not None:
        raise TrailSpecValidationError(
            "A CommandReceipt requires its bound StepReceipt v1.1"
        )

    res = {
        "ok": True,
        "spec": spec_summary,
    }
    if receipt_summary is not None:
        res["receipt"] = receipt_summary
    if command_receipt_summary is not None:
        res["command_receipt"] = command_receipt_summary
    if registry_path is not None:
        res["registry"] = validate_registry(registry_path, as_of=as_of)
    return res


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate TrailSpec v1/v1.1, receipt contracts, and Red-CI registry instances."
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
        help="optional path to version-matched StepReceipt JSON/YAML file",
    )
    parser.add_argument(
        "--command-receipt",
        type=Path,
        default=None,
        help="optional CommandReceipt v1 JSON/YAML file; requires --receipt and a v1.1 trail",
    )
    parser.add_argument(
        "--seat-registry",
        type=Path,
        default=SEAT_TAXONOMY_PATH,
        help="fleet endpoint taxonomy used for TrailSpec v1.1 seat eligibility",
    )
    parser.add_argument(
        "--tables",
        type=Path,
        default=None,
        help="optional path to a decision-tables YAML/JSON file to validate",
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=None,
        help="optional path to a red-CI known-failures registry YAML/JSON file to validate",
    )
    parser.add_argument(
        "--as-of",
        type=str,
        default=None,
        help="optional ISO 8601 timestamp to evaluate registry entry expirations against",
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
            command_receipt_path=(
                args.command_receipt.resolve() if args.command_receipt else None
            ),
            registry_path=args.registry.resolve() if args.registry else None,
            as_of=args.as_of,
            seat_registry_path=args.seat_registry.resolve(),
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
            f"steps={spec_info['steps_count']} hash={spec_info['trail_hash']} "
            f"execution_eligible={spec_info['execution_eligible']}"
        )
        if "receipt" in summary:
            print(f"StepReceipt valid: step_id='{summary['receipt']['step_id']}'")
        if "command_receipt" in summary:
            command_receipt = summary["command_receipt"]
            print(
                "CommandReceipt valid: "
                f"step_id='{command_receipt['step_id']}' "
                f"status='{command_receipt['status']}'"
            )
        if "registry" in summary:
            reg = summary["registry"]
            print(
                f"Registry valid: version='{reg['registry_version']}' "
                f"entries={reg['entries_count']} as_of='{reg['as_of']}'"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
