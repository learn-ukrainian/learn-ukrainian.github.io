#!/usr/bin/env python3
"""Validate qualified-human v0.2 adjudications against the frozen packet order."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.projects.ua_eval_harness import build_v02_review_packet as packet

DEFAULT_PACKET = ROOT / "data/projects/ua_eval_harness/v0.2/review_packet_priority_v1.jsonl"
SCHEMA_PATH = ROOT / "data/projects/ua_eval_harness/v0.2/reviewer_decision_schema_v1.json"
DECISION_SCHEMA = "ua_eval_v02_reviewer_decision.v1"
DECISIONS = {"benchmark_defect", "valid_alternative", "model_error", "protected_variation", "unresolved"}


class AnnotationError(ValueError):
    """A decision file is incomplete, unsafe, or not a qualified adjudication."""


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return packet.read_jsonl(path)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AnnotationError(message)


def decision_validator() -> Any:
    """Load and meta-validate the frozen Draft 2020-12 decision schema."""
    try:
        import jsonschema
    except ImportError as exc:
        raise AnnotationError("jsonschema is required for decision validation") from exc
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AnnotationError(f"cannot read decision schema: {exc}") from exc
    try:
        validator_class = jsonschema.validators.validator_for(schema)
        validator_class.check_schema(schema)
    except jsonschema.exceptions.SchemaError as exc:
        raise AnnotationError(f"invalid decision schema: {exc.message}") from exc
    return validator_class(schema)


def _validate_structure(decisions: list[dict[str, Any]]) -> None:
    schema_validator = decision_validator()
    for line_number, decision in enumerate(decisions, 1):
        errors = sorted(schema_validator.iter_errors(decision), key=lambda error: list(error.path))
        if errors:
            path = ".".join(str(part) for part in errors[0].path) or "record"
            raise AnnotationError(f"decision schema violation at line {line_number} ({path}): {errors[0].message}")


def _reviewer_ids(decision: dict[str, Any]) -> set[str]:
    first_pass = decision["first_pass_reviews"]
    return {review["reviewer"]["reviewer_id"] for review in first_pass}


def _validate_resolution(decision: dict[str, Any], *, allow_test_fixtures: bool) -> None:
    first_pass = decision["first_pass_reviews"]
    reviewers = [review["reviewer"] for review in first_pass]
    reviewer_ids = _reviewer_ids(decision)
    _require(len(reviewer_ids) == 2, "first-pass reviewers must have distinct identities")
    _require(
        allow_test_fixtures or not any(reviewer["test_fixture"] for reviewer in reviewers),
        "test-fixture reviewer cannot be imported as a real adjudication",
    )
    proposed = [review["proposed_decision"] for review in first_pass]
    resolution = decision["final_resolution"]
    kind = resolution["kind"]
    state = decision["review_state"]
    verdict = decision["decision"]
    _require((state == "unresolved") == (verdict == "unresolved"), "contradictory decision and review state")
    if proposed[0] == proposed[1]:
        _require(kind == "first_pass_agreement", "matching first-pass reviews require agreement resolution")
        expected_state = "unresolved" if proposed[0] == "unresolved" else "adjudicated"
        _require(state == expected_state and verdict == proposed[0], "final decision must preserve first-pass agreement")
        return
    if kind == "unresolved_conflict":
        _require(state == "unresolved" and verdict == "unresolved", "unresolved conflict requires unresolved final disposition")
        return
    _require(kind == "third_human_adjudication", "first-pass conflict needs third adjudication or unresolved disposition")
    third_review = resolution.get("third_review")
    _require(isinstance(third_review, dict), "third-human adjudication lacks attributable review evidence")
    third = third_review["reviewer"]
    _require(third["reviewer_id"] not in reviewer_ids, "third reviewer must be independent")
    _require(allow_test_fixtures or not third["test_fixture"], "test-fixture reviewer cannot be imported as a real adjudication")
    _require(third_review["proposed_decision"] != "unresolved", "third unresolved review requires unresolved conflict")
    _require(state == "adjudicated" and verdict == third_review["proposed_decision"], "final decision must equal third-human review")
    _require(decision["uncertainty"] == third_review["uncertainty"], "final uncertainty must equal third-human review")
    _require(decision["source_citations"] == third_review["source_citations"], "final citations must equal third-human review")
    _require(decision["rationale"] == third_review["rationale"], "final rationale must equal third-human review")


def validate(
    packet_rows: list[dict[str, Any]], decisions: list[dict[str, Any]], *, allow_test_fixtures: bool = False
) -> None:
    _require(packet_rows, "empty review packet")
    packet.validate_packet_rows(packet_rows)
    expected_packet = packet.build_rows()
    _require([packet.canonical(row) for row in packet_rows] == [packet.canonical(row) for row in expected_packet], "packet is reordered, incomplete, or does not match frozen evidence")
    _require(len(decisions) == len(packet_rows), "missing or extra decisions")
    _validate_structure(decisions)
    packet_ids = [row.get("item_id") for row in packet_rows]
    decision_ids = [row.get("item_id") for row in decisions]
    _require(len(set(decision_ids)) == len(decision_ids), "duplicate decisions")
    _require(decision_ids == packet_ids, "decisions are reordered or do not match packet")
    for packet_row, decision in zip(packet_rows, decisions, strict=True):
        receipts = packet_row["frozen_receipts"]
        _require(decision["source_sha256"] == receipts["source_sha256"], "source receipt mismatch")
        _validate_resolution(decision, allow_test_fixtures=allow_test_fixtures)
        signals = packet_row["coordinator_priority_metadata"]["signals"]
        if decision["decision"] == "protected_variation":
            _require("protected_variation_risk" in signals, "protected-variation decision contradicts packet evidence")
        if decision["decision"] == "benchmark_defect":
            _require("possible_benchmark_defect" in signals, "benchmark-defect decision contradicts packet evidence")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, default=DEFAULT_PACKET)
    parser.add_argument("--decisions", type=Path, required=True)
    args = parser.parse_args()
    try:
        validate(read_jsonl(args.packet), read_jsonl(args.decisions))
    except (AnnotationError, packet.PacketError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
