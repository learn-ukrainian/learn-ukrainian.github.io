#!/usr/bin/env python3
"""Compare two Layer B annotation sidecars without silently resolving labels.

Material comparison is strict: values and list order
matter unless the labeling contract expressly defines a canonical order.  A
materially disagreeing draft intentionally omits ``adjudication`` for that
case, so the full label schema refuses it until a named adjudicator resolves
the evidence-backed difference.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(project_root / "scripts"))

from scripts.audit.layerb_label_common import LabelJoinError, atomic_write_json, read_json

CASE_MATERIAL_FIELDS = (
    "case_id",
    "artifact_sha256",
    "fixture_id",
    "fact_check_id",
    "fact_check_index",
    "expected_layer_a_decision",
    "expected_layer_a_reason",
    "anchor_scan_complete",
    "candidate_set_complete",
    "candidates_by_event_output_id",
    "expected_aggregate_relation",
    "expected_fact_check_decision",
)
CANDIDATE_MATERIAL_FIELDS = (
    "candidate_id",
    "canonical_source_id",
    "source_index",
    "tool_identity",
    "query_identity",
    "raw_output_sha256",
    "normalized_output_sha256",
    "output_capture_complete",
    "anchor_scan_complete",
    "match_type",
    "similarity",
    "eligibility",
    "error_status",
    "ordered_segment_spans",
    "expected_source_relation",
    "expected_support_spans",
)
COSMETIC_FIELDS = (
    "claim",
    "evidence_excerpt",
    "claim_is_true",
    "expected_reviewer_verdict",
    "context_sufficient",
    "failure_class",
    "corpus_verification_status",
    "annotators",
    "adjudication",
)
SPAN_FIELDS = {"ordered_segment_spans", "expected_support_spans"}


def _ordered_json(value: Any) -> str:
    """Canonicalize mapping key order for comparison; list order stays material.

    JSON object key order is a serialization artifact, not annotation data — the
    guide's material-field list never includes it, and independent annotators
    legitimately serialize in different orders (observed 2026-07-10: one sorted
    keys alphabetically, drowning 535/535 cases in key-order noise).
    """
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _same(left: Any, right: Any) -> bool:
    return _ordered_json(left) == _ordered_json(right)


def _cases(document: Mapping[str, Any], label: str) -> dict[str, dict[str, Any]]:
    cases = document.get("cases")
    if not isinstance(cases, list):
        raise LabelJoinError(f"{label} sidecar has no cases list")
    result: dict[str, dict[str, Any]] = {}
    for case in cases:
        if not isinstance(case, Mapping) or not isinstance(case.get("case_id"), str):
            raise LabelJoinError(f"{label} sidecar contains a case without case_id")
        case_id = str(case["case_id"])
        if case_id in result:
            raise LabelJoinError(f"{label} sidecar repeats case_id={case_id}")
        result[case_id] = dict(case)
    return result


def _candidate_differences(left: Any, right: Any) -> list[dict[str, Any]]:
    """Return exact candidate-map differences at the material contract fields."""
    differences: list[dict[str, Any]] = []
    if not isinstance(left, Mapping) or not isinstance(right, Mapping):
        if not _same(left, right):
            differences.append({"field": "candidates_by_event_output_id", "left": left, "right": right})
        return differences
    for event_output_id in list(dict.fromkeys([*left.keys(), *right.keys()])):
        left_candidates = left.get(event_output_id)
        right_candidates = right.get(event_output_id)
        prefix = f"candidates_by_event_output_id.{event_output_id}"
        if not isinstance(left_candidates, list) or not isinstance(right_candidates, list):
            if not _same(left_candidates, right_candidates):
                differences.append({"field": prefix, "left": left_candidates, "right": right_candidates})
            continue
        if len(left_candidates) != len(right_candidates):
            differences.append(
                {"field": prefix + ".list_length", "left": len(left_candidates), "right": len(right_candidates)}
            )
        for index, (left_candidate, right_candidate) in enumerate(zip(left_candidates, right_candidates, strict=False)):
            candidate_prefix = f"{prefix}[{index}]"
            if not isinstance(left_candidate, Mapping) or not isinstance(right_candidate, Mapping):
                if not _same(left_candidate, right_candidate):
                    differences.append({"field": candidate_prefix, "left": left_candidate, "right": right_candidate})
                continue
            for field in CANDIDATE_MATERIAL_FIELDS:
                if not _same(left_candidate.get(field), right_candidate.get(field)):
                    differences.append(
                        {
                            "field": candidate_prefix + "." + field,
                            "left": left_candidate.get(field),
                            "right": right_candidate.get(field),
                        }
                    )
    return differences


def _material_differences(left: Mapping[str, Any], right: Mapping[str, Any]) -> list[dict[str, Any]]:
    differences: list[dict[str, Any]] = []
    for field in CASE_MATERIAL_FIELDS:
        if field == "candidates_by_event_output_id":
            differences.extend(_candidate_differences(left.get(field), right.get(field)))
        elif not _same(left.get(field), right.get(field)):
            differences.append({"field": field, "left": left.get(field), "right": right.get(field)})
    return differences


def _cosmetic_differences(left: Mapping[str, Any], right: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {"field": field, "left": left.get(field), "right": right.get(field)}
        for field in COSMETIC_FIELDS
        if not _same(left.get(field), right.get(field))
    ]


def _span_only(differences: Sequence[Mapping[str, Any]]) -> bool:
    if not differences:
        return False
    return all(any(field in str(difference["field"]) for field in SPAN_FIELDS) for difference in differences)


def merge_annotator_sidecars(
    left_document: Mapping[str, Any], right_document: Mapping[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return a disagreement report and an intentionally incomplete merge draft."""
    left_cases = _cases(left_document, "left")
    right_cases = _cases(right_document, "right")
    all_case_ids = sorted(set(left_cases) | set(right_cases))
    report_cases: list[dict[str, Any]] = []
    span_only_cases: list[str] = []
    cosmetic_only_cases: list[str] = []
    merged_cases: list[dict[str, Any]] = []
    agreed = 0
    disagreeing = 0
    for case_id in all_case_ids:
        left = left_cases.get(case_id)
        right = right_cases.get(case_id)
        if left is None or right is None:
            material = [{"field": "case_presence", "left": left is not None, "right": right is not None}]
            report_cases.append({"case_id": case_id, "material_differences": material, "cosmetic_differences": []})
            if left is not None:
                draft_case = copy.deepcopy(left)
                draft_case.pop("adjudication", None)
                merged_cases.append(draft_case)
            elif right is not None:
                draft_case = copy.deepcopy(right)
                draft_case.pop("adjudication", None)
                merged_cases.append(draft_case)
            disagreeing += 1
            continue
        material = _material_differences(left, right)
        cosmetic = _cosmetic_differences(left, right)
        if material:
            report_cases.append(
                {"case_id": case_id, "material_differences": material, "cosmetic_differences": cosmetic}
            )
            if _span_only(material):
                span_only_cases.append(case_id)
            draft_case = copy.deepcopy(left)
            draft_case.pop("adjudication", None)
            merged_cases.append(draft_case)
            disagreeing += 1
        else:
            draft_case = copy.deepcopy(left)
            draft_case["adjudication"] = {
                "status": "AGREED",
                "adjudicator": None,
                "note": "Independent annotations matched all material fields.",
            }
            merged_cases.append(draft_case)
            agreed += 1
            if cosmetic:
                cosmetic_only_cases.append(case_id)
                report_cases.append({"case_id": case_id, "material_differences": [], "cosmetic_differences": cosmetic})
    merged = copy.deepcopy(dict(left_document))
    merged["cases"] = merged_cases
    report = {
        "report_version": "qg-layer-b-annotation-merge.v2",
        "counts": {
            "left_cases": len(left_cases),
            "right_cases": len(right_cases),
            "agreed": agreed,
            "material_disagreements": disagreeing,
            "span_only_disagreements": len(span_only_cases),
            "cosmetic_only_differences": len(cosmetic_only_cases),
        },
        "span_only_case_ids": span_only_cases,
        "cosmetic_only_case_ids": cosmetic_only_cases,
        "cases": report_cases,
        "comparison_contract": {
            "exact_deep_equality": True,
            "object_key_order_material": False,
            "list_order_material": True,
            "unadjudicated_cases_omit_adjudication": True,
        },
    }
    return report, merged


def write_merge(left_path: Path, right_path: Path, *, output_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    report, merged = merge_annotator_sidecars(read_json(left_path), read_json(right_path))
    output_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_json(output_dir / "disagreement-report.json", report)
    atomic_write_json(output_dir / "merged-sidecar-draft.json", merged)
    return report, merged


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--left", type=Path, required=True)
    parser.add_argument("--right", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    write_merge(args.left, args.right, output_dir=args.output_dir)
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through the CLI
    raise SystemExit(main())
