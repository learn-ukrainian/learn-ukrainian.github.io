"""Pure evaluation for executable decision-tables.v1 static lookups.

This module neither invokes commands nor inspects external state.  Callers pass
already-typed values from immutable receipts; this module returns exactly one
configured outcome token or ``STOP-unknown``.  Its only I/O helper reads a
decision-tables document for callers that need to load the checked-in table.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from scripts.orchestration.red_ci_known_failures import VALID_STOP_CODES

STOP_UNKNOWN = "STOP-unknown"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DECISION_TABLES_PATH = PROJECT_ROOT / "scripts/config/trails/decision-tables.v1.yaml"
_ACTION_TOKEN = re.compile(r"^[a-z][a-z0-9-]*$")


def load_decision_tables(path: Path = DEFAULT_DECISION_TABLES_PATH) -> dict[str, Any]:
    """Read a decision-tables YAML document without executing or observing anything else."""
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"Root of {path} must be a mapping")
    return loaded


def evaluate_table(table: Mapping[str, Any], inputs: Mapping[str, Any]) -> str:
    """Return one static-table outcome token, otherwise fail closed as STOP-unknown."""
    if not isinstance(table, Mapping) or table.get("mode") != "static":
        return STOP_UNKNOWN

    declarations = table.get("inputs")
    rows = table.get("rows")
    if not isinstance(declarations, Mapping) or not isinstance(rows, list):
        return STOP_UNKNOWN
    if set(inputs) != set(declarations):
        return STOP_UNKNOWN
    if not _inputs_match_declarations(inputs, declarations):
        return STOP_UNKNOWN

    matching_rows = [row for row in rows if _row_matches(row, inputs, declarations)]
    if len(matching_rows) != 1:
        return STOP_UNKNOWN

    outcome = matching_rows[0].get("outcome") if isinstance(matching_rows[0], Mapping) else None
    if not isinstance(outcome, Mapping):
        return STOP_UNKNOWN
    token = outcome.get("token")
    kind = outcome.get("kind")
    if kind not in {"action", "stop"} or not isinstance(token, str):
        return STOP_UNKNOWN
    if kind == "action" and _ACTION_TOKEN.fullmatch(token):
        return token
    if kind == "stop" and token in VALID_STOP_CODES:
        return token
    return STOP_UNKNOWN


def evaluate_named_table(
    tables_data: Mapping[str, Any],
    table_name: str,
    inputs: Mapping[str, Any],
) -> str:
    """Look up and evaluate one named v1 static table from a loaded document."""
    tables = tables_data.get("tables")
    if tables_data.get("schema_version") != "decision-tables.v1" or not isinstance(tables, Mapping):
        return STOP_UNKNOWN
    table = tables.get(table_name)
    if not isinstance(table, Mapping):
        return STOP_UNKNOWN
    return evaluate_table(table, inputs)


def _inputs_match_declarations(inputs: Mapping[str, Any], declarations: Mapping[str, Any]) -> bool:
    for name, declaration in declarations.items():
        if not isinstance(name, str) or not isinstance(declaration, Mapping):
            return False
        value = inputs.get(name)
        input_type = declaration.get("type")
        if input_type == "boolean":
            if type(value) is not bool:
                return False
        elif input_type == "enum":
            values = declaration.get("values")
            if not isinstance(value, str) or not isinstance(values, list) or value not in values:
                return False
        else:
            return False
    return True


def _row_matches(
    row: Any,
    inputs: Mapping[str, Any],
    declarations: Mapping[str, Any],
) -> bool:
    if not isinstance(row, Mapping):
        return False
    when = row.get("when")
    if not isinstance(when, Mapping):
        return False
    conditions = when.get("all")
    if not isinstance(conditions, list) or not conditions:
        return False
    return all(_condition_matches(condition, inputs, declarations) for condition in conditions)


def _condition_matches(
    condition: Any,
    inputs: Mapping[str, Any],
    declarations: Mapping[str, Any],
) -> bool:
    if not isinstance(condition, Mapping):
        return False
    input_name = condition.get("input")
    if not isinstance(input_name, str) or input_name not in declarations:
        return False
    value = inputs[input_name]
    if "equals" in condition and "one_of" not in condition:
        expected = condition["equals"]
        return type(value) is type(expected) and value == expected
    if "one_of" in condition and "equals" not in condition:
        expected_values = condition["one_of"]
        return isinstance(expected_values, list) and any(
            type(value) is type(expected) and value == expected for expected in expected_values
        )
    return False
