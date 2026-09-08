"""Digest-bound structured output shared by schema-capable native adapters.

The schema is invocation-local. A schema failure is a failed result, never an
invitation to recover assistant prose or retry without the schema.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from ..result import ParseResult
from .base import InvocationPlan

INVALID_JSON = object()


def load_output_schema(tool_config: dict[str, Any] | None) -> dict[str, Any] | None:
    """Read and verify caller-bound bytes before constructing provider argv."""
    config = tool_config or {}
    path = config.get("output_schema_path")
    digest = config.get("output_schema_sha256")
    if path is None and digest is None:
        return None
    if not isinstance(path, str) or not Path(path).is_absolute():
        raise ValueError("output_schema_path must be a non-empty absolute path")
    if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise ValueError("output_schema_sha256 must be a lowercase SHA-256")
    payload = Path(path).read_bytes()
    if hashlib.sha256(payload).hexdigest() != digest:
        raise ValueError("output schema SHA-256 changed after dispatch validation")
    schema = json.loads(payload)
    if not isinstance(schema, dict):
        raise ValueError("output schema JSON must be an object")
    Draft202012Validator.check_schema(schema)
    return schema


def schema_metadata(schema: dict[str, Any] | None) -> dict[str, Any]:
    return {"output_schema": schema} if schema is not None else {}


def plan_output_schema(plan: InvocationPlan | None) -> dict[str, Any] | None:
    return plan.metadata.get("output_schema") if plan is not None else None


def validate_output(value: Any, schema: dict[str, Any]) -> Any:
    """Validate without leaking reviewer/corpus text into diagnostics."""
    if value is INVALID_JSON:
        raise ValueError("structured output is not valid JSON")
    error = next(Draft202012Validator(schema).iter_errors(value), None)
    if error is not None:
        raise ValueError(f"structured output does not match schema ({error.validator})")
    return value


def structured_result(
    value: Any,
    schema: dict[str, Any],
    *,
    returncode: int,
    terminal_ok: bool = True,
    session_id: str | None = None,
    tool_calls: list[dict[str, Any]] | None = None,
) -> ParseResult:
    """Turn only a successful terminal schema result into canonical JSON."""
    try:
        if returncode != 0 or not terminal_ok:
            raise ValueError("structured output execution did not complete successfully")
        payload = validate_output(value, schema)
        response = json.dumps(payload, ensure_ascii=False, allow_nan=False)
    except ValueError as exc:
        return ParseResult(
            ok=False, response="", stderr_excerpt=str(exc),
            failure_code="structured_output_invalid",
        )
    return ParseResult(
        ok=True, response=response,
        session_id=session_id, tool_calls=tool_calls or [],
    )


def json_value(text: str) -> Any:
    """Decode exact JSON only; missing/truncated/wrapped data fails validation."""
    def reject_constant(_value: str) -> Any:
        raise ValueError("non-JSON numeric constant")

    def finite_float(value: str) -> float:
        result = float(value)
        if not math.isfinite(result):
            raise ValueError("non-finite JSON number")
        return result

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    try:
        return json.loads(text, parse_constant=reject_constant, parse_float=finite_float, object_pairs_hook=unique_object)
    except (TypeError, ValueError):
        return INVALID_JSON
