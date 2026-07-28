#!/usr/bin/env python3
"""Validate, extract, and deterministically look up red-CI failure signatures."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime
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
LOOKUP_RECEIPT_SCHEMA_PATH = (
    PROJECT_ROOT / "agents_extensions/shared/schemas/red-ci-lookup-receipt.v1.schema.json"
)

HEX_40_RE = re.compile(r"^[0-9a-f]{40}$")
HEX_64_RE = re.compile(r"^[0-9a-f]{64}$")
ANSI_ESCAPE_RE = re.compile(
    r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))"
)

_RECEIPT_SOURCE_FIELDS = frozenset(
    {
        "repository_id",
        "repository_name",
        "pr_number",
        "run_id",
        "run_attempt",
        "head_sha",
        "job_id",
        "job_name",
        "check_id",
        "check_name",
        "extraction_version",
        "timestamp",
        "raw_signature_lines",
    }
)

# Published 18-code STOP vocabulary. The historic "16" count describes trigger
# classes only; it is not the executable vocabulary. validate_trailspec imports
# this immutable source so direct invocation never depends on package layout.
VALID_STOP_CODES: frozenset[str] = frozenset({
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
})


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


def _canonical_sha256(data: Mapping[str, Any]) -> str:
    """Hash semantic JSON data independently of source JSON/YAML formatting."""
    canonical = json.dumps(
        data, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def compute_signature_digest(normalized_signature_lines: Sequence[str]) -> str:
    """Return the canonical SHA-256 binding for already-normalized signature lines."""
    canonical = json.dumps(
        list(normalized_signature_lines), ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


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


def _epoch_seconds(val: str | datetime) -> float:
    """Return a timezone-aware timestamp as an epoch value for all comparisons."""
    return _parse_iso_instant(val).timestamp()


def _json_epoch(epoch: float) -> int | float:
    """Keep whole-second epochs compact while preserving fractional precision."""
    return int(epoch) if epoch.is_integer() else epoch


def load_and_validate_registry(
    path: Path | str,
    *,
    as_of: datetime | str,
    allow_expired: bool = False,
) -> dict[str, Any]:
    """Load and validate a red-CI known-failures registry document against schema and domain rules.

    Domain rules enforced beyond JSON Schema:
    - Unique entry IDs
    - Anchored-regex enforcement (regex values must start with '^' and end with '$')
    - Timestamp parsing into timezone-aware instants
    - Expired entry enforcement relative to as_of (hard deadline), unless the
      lookup caller needs to examine expired matches fail-closed
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
    as_of_epoch = _epoch_seconds(as_of_dt)

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

        action = entry.get("action", {})
        if action.get("kind") == "stop":
            stop_code = action.get("stop_code", "")
            if stop_code not in VALID_STOP_CODES:
                raise RedCIKnownFailuresValidationError(
                    f"Unknown stop_code '{stop_code}' in entry '{entry_id}': "
                    "must be from the published STOP-code contract"
                )

        # Parse & check timestamps
        governance = entry.get("governance", {})
        _parse_iso_instant(governance.get("added_at", ""))
        _parse_iso_instant(governance.get("reviewed_at", ""))
        review_by_dt = _parse_iso_instant(governance.get("review_by", ""))
        review_by_epoch = _epoch_seconds(review_by_dt)

        if not allow_expired and review_by_epoch < as_of_epoch:
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
        "as_of_epoch": _json_epoch(as_of_epoch),
        "data": data,
    }


def validate_receipt_data(data: Mapping[str, Any]) -> dict[str, Any]:
    """Validate in-memory receipt data, including its digest/content binding."""
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

    expected_digest = compute_signature_digest(data["normalized_signature_lines"])
    if digest != expected_digest:
        raise RedCIKnownFailuresValidationError(
            "Signature receipt digest does not bind normalized_signature_lines"
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


def load_and_validate_receipt(path: Path | str) -> dict[str, Any]:
    """Load and validate a red-CI signature-receipt document from JSON or YAML."""
    return validate_receipt_data(_load_yaml_or_json(Path(path).resolve()))


def _normalize_signature_lines(raw_signature_lines: Iterable[str]) -> list[str]:
    """Strip ANSI and normalize CRLF without altering case or whitespace."""
    normalized: list[str] = []
    for raw_line in raw_signature_lines:
        if not isinstance(raw_line, str):
            raise RedCIKnownFailuresValidationError(
                "raw_signature_lines items must all be strings"
            )
        clean = ANSI_ESCAPE_RE.sub("", raw_line).replace("\r\n", "\n")
        normalized.extend(clean.split("\n"))
    return normalized


def extract_signature_receipt(source: Mapping[str, Any]) -> dict[str, Any]:
    """Build a validated receipt from structured failure metadata and raw lines.

    Extraction is pure and deliberately does not query GitHub. Callers provide the
    job/check identity captured from the failing run; this function performs only
    the permitted ANSI/CRLF normalization and binds the resulting lines by SHA-256.
    """
    if not isinstance(source, Mapping):
        raise RedCIKnownFailuresValidationError("Receipt extraction input must be a mapping/dict")

    if not all(isinstance(key, str) for key in source):
        raise RedCIKnownFailuresValidationError(
            "Receipt extraction input fields must all be strings"
        )
    source_keys = set(source)
    missing = sorted(_RECEIPT_SOURCE_FIELDS - source_keys)
    unexpected = sorted(source_keys - _RECEIPT_SOURCE_FIELDS)
    if missing:
        raise RedCIKnownFailuresValidationError(
            f"Receipt extraction input missing required field(s): {', '.join(missing)}"
        )
    if unexpected:
        raise RedCIKnownFailuresValidationError(
            f"Receipt extraction input has unsupported field(s): {', '.join(unexpected)}"
        )

    raw_lines = source["raw_signature_lines"]
    if not isinstance(raw_lines, list):
        raise RedCIKnownFailuresValidationError("raw_signature_lines must be an array/list")

    normalized_lines = _normalize_signature_lines(raw_lines)
    receipt = {
        "schema_version": "red-ci-signature-receipt.v1",
        **{key: source[key] for key in _RECEIPT_SOURCE_FIELDS - {"raw_signature_lines"}},
        "normalized_signature_lines": normalized_lines,
        "digest": compute_signature_digest(normalized_lines),
    }
    validate_receipt_data(receipt)
    return receipt


def _line_matcher_matches(line_matcher: Mapping[str, Any], line: str) -> bool:
    """Evaluate the already-validated exact or full-regex line matcher."""
    if line_matcher["type"] == "exact":
        return line == line_matcher["value"]
    return re.fullmatch(line_matcher["value"], line) is not None


def _entry_matches_receipt(entry: Mapping[str, Any], receipt: Mapping[str, Any]) -> bool:
    """Return whether one entry fully covers one atomic failed-job receipt."""
    matcher = entry["matcher"]
    if matcher["check_name"]["exact"] != receipt["check_name"]:
        return False

    lines = receipt["normalized_signature_lines"]
    line_matchers = matcher["lines"]
    required = line_matchers["required"]
    accepted = line_matchers["accepted"]

    if not all(
        any(_line_matcher_matches(required_matcher, line) for line in lines)
        for required_matcher in required
    ):
        return False

    return not line_matchers["require_full_coverage"] or all(
        any(_line_matcher_matches(accepted_matcher, line) for accepted_matcher in accepted)
        for line in lines
    )


def _entry_is_expired(entry: Mapping[str, Any], as_of_epoch: float) -> bool:
    """Use epoch comparison so equivalent Z/offset instants behave identically."""
    return _epoch_seconds(entry["governance"]["review_by"]) < as_of_epoch


def validate_lookup_receipt_data(data: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a generated red-CI lookup receipt against its public schema."""
    schema = _load_schema(LOOKUP_RECEIPT_SCHEMA_PATH)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    if errors:
        err = errors[0]
        raise RedCIKnownFailuresValidationError(
            f"Lookup receipt schema violation: {err.message} at {err.json_path}"
        )
    return dict(data)


def lookup_known_failure(
    *,
    registry_path: Path | str,
    receipt_path: Path | str,
    repository_id: str,
    pr: int,
    run_id: int,
    as_of: str | datetime,
) -> dict[str, Any]:
    """Purely match one receipt against every eligible registry entry.

    A matching expired entry intentionally takes precedence over active matches:
    expiry can never silently authorize an action. The returned retry disposition is
    data only; this module contains no rerun operation.
    """
    if not repository_id.strip():
        raise RedCIKnownFailuresValidationError("CLI repository-id must be non-empty")

    receipt_summary = load_and_validate_receipt(receipt_path)
    receipt = receipt_summary["data"]

    if str(receipt["repository_id"]) != repository_id:
        raise RedCIKnownFailuresValidationError(
            "Receipt repository_id does not equal the CLI repository-id"
        )
    if receipt["pr_number"] != pr:
        raise RedCIKnownFailuresValidationError("Receipt pr_number does not equal the CLI pr")
    if receipt["run_id"] != run_id:
        raise RedCIKnownFailuresValidationError("Receipt run_id does not equal the CLI run-id")

    registry_summary = load_and_validate_registry(
        registry_path, as_of=as_of, allow_expired=True
    )
    registry = registry_summary["data"]
    as_of_epoch = _epoch_seconds(as_of)

    active_matches: list[Mapping[str, Any]] = []
    expired_matches: list[Mapping[str, Any]] = []
    for entry in registry["entries"]:
        if _entry_matches_receipt(entry, receipt):
            if _entry_is_expired(entry, as_of_epoch):
                expired_matches.append(entry)
            else:
                active_matches.append(entry)

    if expired_matches:
        result: dict[str, Any] = {
            "schema_version": "red-ci-lookup-receipt.v1",
            "status": "table-unknown",
            "reason": "expired-match",
        }
    elif len(active_matches) > 1:
        result = {
            "schema_version": "red-ci-lookup-receipt.v1",
            "status": "table-unknown",
            "reason": "ambiguous",
        }
    elif not active_matches:
        result = {
            "schema_version": "red-ci-lookup-receipt.v1",
            "status": "table-unknown",
            "reason": "no-match",
        }
    else:
        entry = active_matches[0]
        result = {
            "schema_version": "red-ci-lookup-receipt.v1",
            "status": "matched",
            "entry_id": entry["id"],
            "action": entry["action"],
            "registry_sha256": _canonical_sha256(registry),
            "signature_receipt_sha256": _canonical_sha256(receipt),
            "as_of_epoch": _json_epoch(as_of_epoch),
        }
    return validate_lookup_receipt_data(result)


def aggregate_lookup_results(results: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    """Aggregate atomic lookup data with the red-CI fail-closed precedence rules."""
    if not results:
        return {"kind": "stop", "reason": "malformed"}

    action_kinds: list[str] = []
    for result in results:
        if not isinstance(result, Mapping):
            return {"kind": "stop", "reason": "malformed"}
        if result.get("status") != "matched":
            reason = result.get("reason")
            return {
                "kind": "stop",
                "reason": reason if isinstance(reason, str) else "malformed",
            }
        action = result.get("action")
        if not isinstance(action, Mapping) or not isinstance(action.get("kind"), str):
            return {"kind": "stop", "reason": "malformed"}
        action_kind = action["kind"]
        if action_kind == "stop":
            return {"kind": "stop", "reason": "stop"}
        if action_kind not in {"retry-once", "note-and-proceed"}:
            return {"kind": "stop", "reason": "malformed"}
        action_kinds.append(action_kind)

    if "retry-once" in action_kinds:
        return {"kind": "retry-once"}
    return {"kind": "note-and-proceed"}


def _write_json_output(path: Path, data: Mapping[str, Any]) -> None:
    """Atomically write a receipt without ever targeting an input file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as output_file:
            temp_name = output_file.name
            json.dump(data, output_file, ensure_ascii=False, indent=2, sort_keys=True)
            output_file.write("\n")
        os.replace(temp_name, path)
    except OSError as exc:
        raise RedCIKnownFailuresValidationError(f"Unable to write output {path}: {exc}") from exc
    finally:
        if temp_name is not None:
            Path(temp_name).unlink(missing_ok=True)


def _distinct_output_path(output: Path, *inputs: Path) -> Path:
    """Reject an output path that would overwrite a registry or receipt input."""
    resolved_output = output.resolve()
    if any(resolved_output == input_path.resolve() for input_path in inputs):
        raise RedCIKnownFailuresValidationError(
            "Output path must not overwrite a registry, receipt, or extraction input"
        )
    return resolved_output


def _extract_command(args: argparse.Namespace) -> int:
    source_path = args.input.resolve()
    output_path = _distinct_output_path(args.output, source_path)
    receipt = extract_signature_receipt(_load_yaml_or_json(source_path))
    _write_json_output(output_path, receipt)
    return 0


def _lookup_command(args: argparse.Namespace) -> int:
    registry_path = args.registry.resolve()
    receipt_path = args.receipt.resolve()
    output_path = _distinct_output_path(args.output, registry_path, receipt_path)
    result = lookup_known_failure(
        registry_path=registry_path,
        receipt_path=receipt_path,
        repository_id=args.repository_id,
        pr=args.pr,
        run_id=args.run_id,
        as_of=args.as_of,
    )
    _write_json_output(output_path, result)
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the pure extraction or deterministic lookup CLI without actionable stdout."""
    parser = argparse.ArgumentParser(
        description="Extract and look up red-CI known-failure signature receipts."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    extract_parser = subparsers.add_parser(
        "extract", help="normalize structured failure input into a signature receipt"
    )
    extract_parser.add_argument("--input", type=Path, required=True)
    extract_parser.add_argument("--output", type=Path, required=True)
    extract_parser.set_defaults(handler=_extract_command)

    lookup_parser = subparsers.add_parser(
        "lookup", help="look up one signature receipt without any network access"
    )
    lookup_parser.add_argument("--registry", type=Path, required=True)
    lookup_parser.add_argument("--receipt", type=Path, required=True)
    lookup_parser.add_argument("--repository-id", required=True)
    lookup_parser.add_argument("--pr", type=int, required=True)
    lookup_parser.add_argument("--run-id", type=int, required=True)
    lookup_parser.add_argument("--as-of", required=True)
    lookup_parser.add_argument("--output", type=Path, required=True)
    lookup_parser.set_defaults(handler=_lookup_command)

    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except RedCIKnownFailuresValidationError as exc:
        print(f"red-CI known-failures error: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"red-CI known-failures I/O error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
