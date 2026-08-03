#!/usr/bin/env python3
"""Source-aware integrity gate for saved UA Open-Weight Eval responses.

This module is intentionally adjacent to, rather than part of, the byte-frozen
v0.1.0 suite CLI. It detects runtime/protocol corruption without making a
linguistic judgment about Ukrainian, Russian, historical, or quoted source text.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from scripts.projects.ua_open_weight_eval import suite_cli

ALLOWED_ACTIONS = frozenset({"correct", "preserve", "abstain"})
MODEL_ARTIFACT_PATTERN = re.compile(
    r"<unused\d+>|\[multimodal\]|</?[A-Za-z][A-Za-z0-9_-]*(?:\s[^<>]{0,64})?>"
)
NON_WHITESPACE_C0 = frozenset(chr(value) for value in range(32)) - {"\t", "\n", "\r"}


class IntegrityError(ValueError):
    """Raised when saved output is corrupt or cannot be verified."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise IntegrityError(message)


def response_integrity_summary(
    *,
    sources: Mapping[str, str],
    responses: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Check protocol integrity relative to each exact source string."""

    violation_ids: list[str] = []
    copy_contract_rows = 0
    reserved_marker_rows = 0
    introduced_control_rows = 0
    for item_id in sorted(responses):
        _require(item_id in sources, f"unknown response item: {item_id}")
        source = sources[item_id]
        response = responses[item_id]
        action = response.get("action")
        output_text = response.get("output_text")
        _require(action in ALLOWED_ACTIONS, f"invalid action for {item_id}")
        _require(isinstance(output_text, str) and output_text, f"missing output_text for {item_id}")

        copy_violation = action in {"preserve", "abstain"} and output_text != source
        source_markers = Counter(MODEL_ARTIFACT_PATTERN.findall(source))
        output_markers = Counter(MODEL_ARTIFACT_PATTERN.findall(output_text))
        marker_violation = any(count > source_markers[token] for token, count in output_markers.items())
        source_controls = Counter(character for character in source if character in NON_WHITESPACE_C0)
        output_controls = Counter(character for character in output_text if character in NON_WHITESPACE_C0)
        control_violation = any(count > source_controls[character] for character, count in output_controls.items())

        copy_contract_rows += int(copy_violation)
        reserved_marker_rows += int(marker_violation)
        introduced_control_rows += int(control_violation)
        if copy_violation or marker_violation or control_violation:
            violation_ids.append(item_id)

    return {
        "schema_version": "ua_open_weight_eval_response_integrity.v1",
        "status": "passed" if not violation_ids else "invalid",
        "checked_rows": len(responses),
        "violation_rows": len(violation_ids),
        "copy_contract_violation_rows": copy_contract_rows,
        "reserved_marker_violation_rows": reserved_marker_rows,
        "introduced_control_violation_rows": introduced_control_rows,
        "sample_violation_item_ids": violation_ids[:10],
    }


def require_response_integrity(
    *,
    sources: Mapping[str, str],
    responses: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    summary = response_integrity_summary(sources=sources, responses=responses)
    _require(
        summary["status"] == "passed",
        f"response semantic integrity failed: {suite_cli.canonical_json(summary)}",
    )
    return summary


def verify_saved_integrity(
    responses_path: Path,
    requests_path: Path | None = None,
    expected_count: int | None = None,
) -> dict[str, Any]:
    if requests_path is None:
        sources = {
            suite_cli.request_item_id(position): str(case["source"])
            for position, case in enumerate(suite_cli.read_jsonl(suite_cli.CASES_PATH), 1)
        }
        requests_sha256 = None
    else:
        request_rows = suite_cli.read_jsonl(requests_path)
        sources = {str(row["item_id"]): str(row["source"]) for row in request_rows if row.get("type") == "request"}
        _require(sources, "request packet contains no request rows")
        requests_sha256 = suite_cli.sha256_file(requests_path)

    response_rows = suite_cli.read_jsonl(responses_path)
    if response_rows[0].get("type") == "run":
        response_rows = response_rows[1:]
    responses: dict[str, dict[str, Any]] = {}
    for row in response_rows:
        item_id = row.get("item_id")
        _require(isinstance(item_id, str) and item_id in sources, f"unknown response item: {item_id}")
        _require(item_id not in responses, f"duplicate response item: {item_id}")
        responses[item_id] = row
    expected_count = len(sources) if expected_count is None else expected_count
    _require(0 < expected_count <= len(sources), "expected response count is invalid")
    _require(len(responses) == expected_count, "saved output response count drift")
    if expected_count == len(sources):
        _require(set(responses) == set(sources), "saved output must cover every source exactly once")
    summary = require_response_integrity(sources=sources, responses=responses)
    return {
        **summary,
        "expected_rows": expected_count,
        "responses_sha256": suite_cli.sha256_file(responses_path),
        "requests_sha256": requests_sha256,
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--responses", type=Path, required=True)
    parser.add_argument("--requests", type=Path)
    parser.add_argument("--expected-count", type=int)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = verify_saved_integrity(args.responses, args.requests, args.expected_count)
    except (OSError, IntegrityError, suite_cli.SuiteError) as exc:
        print(f"response-integrity: ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
