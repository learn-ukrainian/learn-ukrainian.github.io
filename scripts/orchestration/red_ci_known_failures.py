#!/usr/bin/env python3
"""Red-CI known-failures registry and signature-receipt stage 1 validation module."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_SCHEMA_PATH = (
    PROJECT_ROOT / "agents_extensions/shared/schemas/red-ci-known-failures.v1.schema.json"
)
RECEIPT_SCHEMA_PATH = (
    PROJECT_ROOT / "agents_extensions/shared/schemas/red-ci-signature-receipt.v1.schema.json"
)

HEX_40_RE = re.compile(r"^[0-9a-f]{40}$")
HEX_64_RE = re.compile(r"^[0-9a-f]{64}$")


class RedCIKnownFailuresValidationError(Exception):
    """Raised when red-CI known-failures registry or signature receipt validation fails."""


class _StringTimestampSafeLoader(yaml.SafeLoader):
    """SafeLoader minus implicit timestamp coercion (codex F001): PyYAML turns
    unquoted ISO-8601 scalars into datetime objects, which the string-typed
    schema then rejects — a normal unquoted YAML registry would be unusable.
    Timestamps stay strings; _parse_iso_instant owns the parsing."""


_StringTimestampSafeLoader.yaml_implicit_resolvers = {
    key: [(tag, regexp) for tag, regexp in resolvers if tag != "tag:yaml.org,2002:timestamp"]
    for key, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def _load_yaml_or_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RedCIKnownFailuresValidationError(f"File not found: {path}")
    try:
        content = path.read_text(encoding="utf-8")
        data = (
            json.loads(content)
            if path.suffix == ".json"
            else yaml.load(content, Loader=_StringTimestampSafeLoader)
        )
    except Exception as exc:
        raise RedCIKnownFailuresValidationError(f"Parse error in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise RedCIKnownFailuresValidationError(f"Root of {path} must be a mapping/dict")
    return data


def _load_schema(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RedCIKnownFailuresValidationError(f"Schema file not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RedCIKnownFailuresValidationError(f"JSON parse error in schema {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise RedCIKnownFailuresValidationError(f"Root of schema {path} must be a dict")
    return data


def _parse_iso_instant(val: str | datetime) -> datetime:
    """Parse string or datetime to timezone-aware instant."""
    if isinstance(val, datetime):
        if val.tzinfo is None:
            raise RedCIKnownFailuresValidationError(
                f"Timestamp '{val}' must be timezone-aware"
            )
        return val
    if not isinstance(val, str):
        raise RedCIKnownFailuresValidationError(f"Invalid timestamp type: {type(val)}")
    val_clean = val.strip()
    if val_clean.endswith("Z") or val_clean.endswith("z"):
        val_clean = val_clean[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(val_clean)
    except Exception as exc:
        raise RedCIKnownFailuresValidationError(f"Invalid ISO 8601 timestamp '{val}': {exc}") from exc
    if dt.tzinfo is None:
        raise RedCIKnownFailuresValidationError(f"Timestamp '{val}' must be timezone-aware")
    return dt


def load_and_validate_registry(
    path: Path | str,
    *,
    as_of: datetime | str,
) -> dict[str, Any]:
    """Load and validate a red-CI known-failures registry document against schema and domain rules.

    Domain rules enforced beyond JSON Schema:
    - Unique entry IDs
    - Anchored-regex enforcement (regex values must start with '^' and end with '$')
    - Timestamp parsing into timezone-aware instants
    - Expired entry enforcement relative to as_of (hard deadline)
    """
    path_obj = Path(path).resolve()
    data = _load_yaml_or_json(path_obj)

    registry_schema = _load_schema(REGISTRY_SCHEMA_PATH)
    validator = Draft202012Validator(registry_schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    if errors:
        err = errors[0]
        raise RedCIKnownFailuresValidationError(
            f"Registry schema violation: {err.message} at {err.json_path}"
        )

    # as_of is REQUIRED at this layer (glm F4): the module stays deterministic;
    # wall-clock convenience lives only in the CLI wrapper.
    as_of_dt = _parse_iso_instant(as_of)

    seen_ids: set[str] = set()
    entries = data.get("entries", [])
    for entry in entries:
        entry_id = entry.get("id")
        if not entry_id:
            raise RedCIKnownFailuresValidationError("Entry missing required 'id'")
        if entry_id in seen_ids:
            raise RedCIKnownFailuresValidationError(f"Duplicate entry id: '{entry_id}'")
        seen_ids.add(entry_id)

        # Matcher anchored regex enforcement
        lines = entry.get("matcher", {}).get("lines", {})
        all_line_matchers = lines.get("required", []) + lines.get("accepted", [])
        for line_m in all_line_matchers:
            if line_m.get("type") == "regex":
                val = line_m.get("value", "")
                if not (val.startswith("^") and val.endswith("$")):
                    raise RedCIKnownFailuresValidationError(
                        f"Unanchored regex in entry '{entry_id}': '{val}' "
                        "(regex matchers must be anchored with ^...$)"
                    )
                try:
                    re.compile(val)
                except re.error as exc:
                    raise RedCIKnownFailuresValidationError(
                        f"Malformed regex in entry '{entry_id}': '{val}' ({exc})"
                    ) from exc

        # Parse & check timestamps
        governance = entry.get("governance", {})
        _parse_iso_instant(governance.get("added_at", ""))
        _parse_iso_instant(governance.get("reviewed_at", ""))
        review_by_dt = _parse_iso_instant(governance.get("review_by", ""))

        if review_by_dt < as_of_dt:
            raise RedCIKnownFailuresValidationError(
                f"Registry entry '{entry_id}' expired at review_by={review_by_dt.isoformat()} "
                f"relative to as_of={as_of_dt.isoformat()}"
            )

        for ev in entry.get("evidence", []):
            _parse_iso_instant(ev.get("observed_at", ""))

    return {
        "ok": True,
        "schema_version": data.get("schema_version"),
        "registry_version": data.get("registry_version"),
        "entries_count": len(entries),
        "as_of": as_of_dt.isoformat(),
        "data": data,
    }


def load_and_validate_receipt(path: Path | str) -> dict[str, Any]:
    """Load and validate a red-CI signature-receipt document against schema and hex constraints."""
    path_obj = Path(path).resolve()
    data = _load_yaml_or_json(path_obj)

    receipt_schema = _load_schema(RECEIPT_SCHEMA_PATH)
    validator = Draft202012Validator(receipt_schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    if errors:
        err = errors[0]
        raise RedCIKnownFailuresValidationError(
            f"Signature receipt schema violation: {err.message} at {err.json_path}"
        )

    head_sha = data.get("head_sha", "")
    if not HEX_40_RE.match(head_sha):
        raise RedCIKnownFailuresValidationError(
            f"Invalid head_sha in receipt: '{head_sha}' (must be 40 lowercase hex)"
        )

    digest = data.get("digest", "")
    if not HEX_64_RE.match(digest):
        raise RedCIKnownFailuresValidationError(
            f"Invalid digest in receipt: '{digest}' (must be 64 lowercase hex)"
        )

    _parse_iso_instant(data.get("timestamp", ""))

    return {
        "ok": True,
        "schema_version": data.get("schema_version"),
        "pr_number": data.get("pr_number"),
        "run_id": data.get("run_id"),
        "head_sha": head_sha,
        "digest": digest,
        "data": data,
    }
