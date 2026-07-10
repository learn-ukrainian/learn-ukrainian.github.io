#!/usr/bin/env python3
"""Apply frozen Layer B adjudication rulings to a complete labels sidecar.

The adjudication decisions, annotator records, and digest are immutable
offline inputs.  This tool does not interpret evidence: it only enforces the
already-recorded A/B/UNION/CUSTOM/UNRESOLVED instructions and writes one
atomic final sidecar.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(project_root / "scripts"))

from scripts.audit.layerb_keys import _build_event_index
from scripts.audit.layerb_label_common import LabelJoinError, atomic_write_json, read_json, sha256_file
from scripts.audit.layerb_label_scaffold import _artifact_events, validate_annotator_record

ADJUDICATOR = "claude-infra (Fable, session d2d784aa)"
ADJUDICATOR_R2 = "claude-infra (Fable, session 053cb131)"
ANNOTATORS = ["annotator-a-claude-opus", "annotator-b-codex-terra"]
CASE_JUDGMENT_FIELDS = {"expected_aggregate_relation", "expected_fact_check_decision"}
CANDIDATE_JUDGMENT_FIELDS = {"expected_source_relation", "expected_support_spans"}
CUSTOM_CASE_FIELD_NAMES = {
    "aggregate_relation": "expected_aggregate_relation",
    "fact_check_decision": "expected_fact_check_decision",
}
CUSTOM_CANDIDATE_FIELD_NAMES = {
    "candidate.expected_source_relation": "expected_source_relation",
    "candidate.expected_support_spans": "expected_support_spans",
}
UNRESOLVED_BLOCKER_PREFIX = "UNRESOLVED case pending re-adjudication: "
STANDING_BLOCKER = "2 UNRESOLVED cases pending re-adjudication"


def _case_map(document: Mapping[str, Any], label: str) -> dict[str, dict[str, Any]]:
    """Return cases keyed by stable ID, rejecting incomplete input shape."""
    cases = document.get("cases")
    if not isinstance(cases, list):
        raise LabelJoinError(f"{label} has no cases list")
    result: dict[str, dict[str, Any]] = {}
    for case in cases:
        if not isinstance(case, Mapping) or not isinstance(case.get("case_id"), str) or not case["case_id"]:
            raise LabelJoinError(f"{label} has a case without a non-empty case_id")
        case_id = str(case["case_id"])
        if case_id in result:
            raise LabelJoinError(f"{label} repeats case_id={case_id}")
        result[case_id] = dict(case)
    return result


def _decision_map(
    decisions: Any,
    *,
    label: str = "adjudication",
    adjudicator: str = ADJUDICATOR,
) -> dict[str, dict[str, Any]]:
    """Index frozen rulings and reject malformed or duplicate decisions."""
    if not isinstance(decisions, list):
        raise LabelJoinError(f"{label} decisions must be a list")
    result: dict[str, dict[str, Any]] = {}
    for decision in decisions:
        if not isinstance(decision, Mapping):
            raise LabelJoinError(f"{label} decisions must contain objects")
        case_id = decision.get("case_id")
        rationale = decision.get("rationale")
        if not isinstance(case_id, str) or not case_id:
            raise LabelJoinError(f"{label} decision has no non-empty case_id")
        if not isinstance(rationale, str) or not rationale:
            raise LabelJoinError(f"{label} decision {case_id} has no rationale")
        if decision.get("adjudicator") != adjudicator:
            raise LabelJoinError(f"{label} decision {case_id} has an unexpected adjudicator")
        if case_id in result:
            raise LabelJoinError(f"{label} decisions repeat case_id={case_id}")
        result[case_id] = dict(decision)
    return result


def _round_two_decision_map(decisions: Any) -> dict[str, dict[str, Any]]:
    """Index and validate frozen Round-2 decisions before applying an overlay."""
    result = _decision_map(
        decisions,
        label="round-2 adjudication",
        adjudicator=ADJUDICATOR_R2,
    )
    for case_id, decision in result.items():
        if decision.get("round") != 2:
            raise LabelJoinError(f"round-2 adjudication decision {case_id} must carry round=2")
        if decision.get("supersedes_ruling") != "UNRESOLVED":
            raise LabelJoinError(
                f"round-2 adjudication decision {case_id} must supersede UNRESOLVED"
            )
    return result


def _overlay_round_two_decisions(
    round_one: Mapping[str, dict[str, Any]], decisions_r2: Any
) -> dict[str, dict[str, Any]]:
    """Replace only Round-1 UNRESOLVED rulings with validated Round-2 records."""
    result = dict(round_one)
    for case_id, decision in _round_two_decision_map(decisions_r2).items():
        previous = round_one.get(case_id)
        if previous is None or previous.get("ruling") != "UNRESOLVED":
            raise LabelJoinError(
                f"round-2 adjudication decision {case_id} does not target a Round-1 UNRESOLVED case"
            )
        result[case_id] = decision
    return result


def _digest_map(digest: Any) -> dict[str, dict[str, Any]]:
    """Index the frozen field-level disagreement digest."""
    if not isinstance(digest, list):
        raise LabelJoinError("adjudication digest must be a list")
    result: dict[str, dict[str, Any]] = {}
    for entry in digest:
        if not isinstance(entry, Mapping):
            raise LabelJoinError("adjudication digest must contain objects")
        case_id = entry.get("case_id")
        fields = entry.get("fields")
        if not isinstance(case_id, str) or not case_id or not isinstance(fields, Mapping):
            raise LabelJoinError("adjudication digest entry is malformed")
        unexpected = sorted(set(fields) - CASE_JUDGMENT_FIELDS - CANDIDATE_JUDGMENT_FIELDS)
        if unexpected:
            raise LabelJoinError(f"adjudication digest {case_id} has unsupported fields: {', '.join(unexpected)}")
        if case_id in result:
            raise LabelJoinError(f"adjudication digest repeats case_id={case_id}")
        result[case_id] = dict(entry)
    return result


def _candidate_groups(case: Mapping[str, Any], label: str) -> Mapping[str, Any]:
    groups = case.get("candidates_by_event_output_id")
    if not isinstance(groups, Mapping):
        raise LabelJoinError(f"{label} case {case.get('case_id')!r} has no candidate groups")
    return groups


def _aligned_candidate_groups(
    target: Mapping[str, Any], source: Mapping[str, Any], label: str
) -> list[tuple[list[Any], list[Any]]]:
    """Pair candidates by immutable event-output ID and list position."""
    target_groups = _candidate_groups(target, "target")
    source_groups = _candidate_groups(source, label)
    if list(target_groups) != list(source_groups):
        raise LabelJoinError(f"candidate event-output IDs differ between target and {label}")
    aligned: list[tuple[list[Any], list[Any]]] = []
    for event_output_id in target_groups:
        target_candidates = target_groups[event_output_id]
        source_candidates = source_groups[event_output_id]
        if not isinstance(target_candidates, list) or not isinstance(source_candidates, list):
            raise LabelJoinError(f"candidate group {event_output_id} is not a list")
        if len(target_candidates) != len(source_candidates):
            raise LabelJoinError(f"candidate count differs for event output {event_output_id}")
        for target_candidate, source_candidate in zip(target_candidates, source_candidates, strict=True):
            if not isinstance(target_candidate, dict) or not isinstance(source_candidate, Mapping):
                raise LabelJoinError(f"candidate group {event_output_id} contains a non-object")
            if target_candidate.get("candidate_id") != source_candidate.get("candidate_id"):
                raise LabelJoinError(f"candidate ID differs for event output {event_output_id}")
        aligned.append((target_candidates, source_candidates))
    return aligned


def _copy_differing_fields(target: dict[str, Any], source: Mapping[str, Any], fields: set[str], label: str) -> None:
    """Copy only digest-listed judgment fields from an adjudicated source side."""
    for field in sorted(fields & CASE_JUDGMENT_FIELDS):
        target[field] = copy.deepcopy(source.get(field))
    candidate_fields = fields & CANDIDATE_JUDGMENT_FIELDS
    if not candidate_fields:
        return
    for target_candidates, source_candidates in _aligned_candidate_groups(target, source, label):
        for target_candidate, source_candidate in zip(target_candidates, source_candidates, strict=True):
            for field in sorted(candidate_fields):
                target_candidate[field] = copy.deepcopy(source_candidate.get(field))


def _union_support_spans(target: dict[str, Any], left: Mapping[str, Any], right: Mapping[str, Any]) -> None:
    """Use A then B spans, retaining each exact span object once per candidate."""
    left_pairs = _aligned_candidate_groups(target, left, "annotator-a")
    right_pairs = _aligned_candidate_groups(target, right, "annotator-b")
    for (target_candidates, left_candidates), (_same_target, right_candidates) in zip(
        left_pairs, right_pairs, strict=True
    ):
        for target_candidate, left_candidate, right_candidate in zip(
            target_candidates, left_candidates, right_candidates, strict=True
        ):
            left_spans = left_candidate.get("expected_support_spans")
            right_spans = right_candidate.get("expected_support_spans")
            if not isinstance(left_spans, list) or not isinstance(right_spans, list):
                raise LabelJoinError("UNION requires expected_support_spans lists")
            union: list[Any] = []
            for span in [*left_spans, *right_spans]:
                if span not in union:
                    union.append(copy.deepcopy(span))
            target_candidate["expected_support_spans"] = union


def _parse_custom_ruling(ruling: str) -> tuple[dict[str, str], dict[str, str]]:
    """Translate frozen CUSTOM assignments into case and candidate changes."""
    if not ruling.startswith("CUSTOM:"):
        raise LabelJoinError(f"not a CUSTOM ruling: {ruling!r}")
    assignments = ruling.removeprefix("CUSTOM:").split(",")
    case_result: dict[str, str] = {}
    candidate_result: dict[str, str] = {}
    for assignment in assignments:
        key, separator, value = assignment.partition("=")
        case_field = CUSTOM_CASE_FIELD_NAMES.get(key)
        candidate_field = CUSTOM_CANDIDATE_FIELD_NAMES.get(key)
        if not separator or not value:
            raise LabelJoinError(f"malformed CUSTOM ruling: {ruling!r}")
        if case_field is not None and case_field not in case_result:
            case_result[case_field] = value
        elif candidate_field is not None and candidate_field not in candidate_result:
            if candidate_field == "expected_support_spans" and value != "EMPTY":
                raise LabelJoinError(f"candidate CUSTOM spans must be literal EMPTY: {ruling!r}")
            candidate_result[candidate_field] = value
        else:
            raise LabelJoinError(f"malformed CUSTOM ruling: {ruling!r}")
    return case_result, candidate_result


def _single_candidate_for_custom(case: dict[str, Any]) -> dict[str, Any]:
    """Return the sole candidate required for a candidate-level CUSTOM ruling."""
    candidates: list[dict[str, Any]] = []
    for event_output_id, group in _candidate_groups(case, "CUSTOM target").items():
        if not isinstance(group, list):
            raise LabelJoinError(f"candidate group {event_output_id} is not a list")
        for candidate in group:
            if not isinstance(candidate, dict):
                raise LabelJoinError(f"candidate group {event_output_id} contains a non-object")
            candidates.append(candidate)
    if len(candidates) != 1:
        raise LabelJoinError(f"candidate-level CUSTOM requires exactly one candidate, found {len(candidates)}")
    return candidates[0]


def _apply_candidate_custom_assignments(case: dict[str, Any], assignments: Mapping[str, str]) -> None:
    """Set explicit candidate CUSTOM assignments without selecting an annotator residual."""
    candidate = _single_candidate_for_custom(case)
    for field, value in assignments.items():
        candidate[field] = [] if field == "expected_support_spans" else value


def _custom_residual_source(decision: Mapping[str, Any]) -> str:
    """Apply the frozen rationale's explicit source-relation instruction.

    The two contradiction customs name a contradiction in the rationale (one
    explicitly says B's source relation is right); their candidate relation
    and spans therefore come from B.  The insufficient-context customs do not
    instruct a B source relation, so their residual candidate fields stay A.
    """
    rationale = str(decision["rationale"]).casefold()
    if "b's srel right" in rationale or ("source says" in rationale and "contradicts" in rationale):
        return "B"
    return "A"


def _adjudication(status: str, note: str, adjudicator: str) -> dict[str, Any]:
    return {"status": status, "adjudicator": adjudicator, "note": note}


def apply_ruling(
    draft_case: Mapping[str, Any],
    annotator_a_case: Mapping[str, Any],
    annotator_b_case: Mapping[str, Any],
    decision: Mapping[str, Any],
    digest_entry: Mapping[str, Any],
) -> dict[str, Any]:
    """Apply one already-recorded ruling without making an evidence judgment."""
    result = copy.deepcopy(dict(draft_case))
    ruling = decision.get("ruling")
    rationale = decision.get("rationale")
    adjudicator = decision.get("adjudicator")
    if not isinstance(ruling, str) or not isinstance(rationale, str) or not isinstance(adjudicator, str):
        raise LabelJoinError(f"malformed adjudication decision for {draft_case.get('case_id')!r}")
    fields = set((digest_entry.get("fields") or {}).keys())
    if ruling == "A":
        _copy_differing_fields(result, annotator_a_case, fields, "annotator-a")
        result["adjudication"] = _adjudication("ADJUDICATED", rationale, adjudicator)
    elif ruling == "B":
        _copy_differing_fields(result, annotator_b_case, fields, "annotator-b")
        result["adjudication"] = _adjudication("ADJUDICATED", rationale, adjudicator)
    elif ruling == "UNION":
        _copy_differing_fields(result, annotator_a_case, fields - {"expected_support_spans"}, "annotator-a")
        _union_support_spans(result, annotator_a_case, annotator_b_case)
        result["adjudication"] = _adjudication(
            "ADJUDICATED",
            rationale + " [UNION: A then B support spans, exact duplicates removed.]",
            adjudicator,
        )
    elif ruling == "UNRESOLVED":
        _copy_differing_fields(result, annotator_a_case, fields, "annotator-a")
        result["adjudication"] = _adjudication("UNRESOLVED", rationale, adjudicator)
    elif ruling.startswith("CUSTOM:"):
        case_assignments, candidate_assignments = _parse_custom_ruling(ruling)
        if candidate_assignments:
            _copy_differing_fields(
                result,
                annotator_a_case,
                fields - CANDIDATE_JUDGMENT_FIELDS,
                "annotator-a",
            )
        else:
            source = annotator_b_case if _custom_residual_source(decision) == "B" else annotator_a_case
            _copy_differing_fields(
                result,
                source,
                fields,
                "annotator-b" if source is annotator_b_case else "annotator-a",
            )
        for field, value in case_assignments.items():
            result[field] = value
        if candidate_assignments:
            _apply_candidate_custom_assignments(result, candidate_assignments)
        result["adjudication"] = _adjudication("ADJUDICATED", rationale, adjudicator)
    else:
        raise LabelJoinError(f"unsupported ruling {ruling!r} for {draft_case.get('case_id')!r}")
    return result


def build_event_outputs(corpus_dir: Path) -> dict[str, str]:
    """Derive the event-output index required by working-record validation."""
    if not corpus_dir.is_dir():
        raise LabelJoinError(f"event corpus directory does not exist: {corpus_dir}")
    events: list[Mapping[str, Any]] = []
    paths = sorted(corpus_dir.glob("*.json"))
    if not paths:
        raise LabelJoinError(f"event corpus contains no JSON artifacts: {corpus_dir}")
    for path in paths:
        artifact = read_json(path)
        if not isinstance(artifact, Mapping):
            raise LabelJoinError(f"event corpus artifact is not an object: {path}")
        events.extend(_artifact_events(artifact))
    return _build_event_index(events)


def _validate_completed_case(case: Mapping[str, Any], event_outputs: Mapping[str, str]) -> None:
    """Validate completed labels with the existing working-record hard checks."""
    working = copy.deepcopy(dict(case))
    working.pop("annotators", None)
    working.pop("adjudication", None)
    validate_annotator_record(working, event_outputs)
    if case.get("annotators") != ANNOTATORS:
        raise LabelJoinError(f"case {case.get('case_id')!r} has incorrect annotators")
    adjudication = case.get("adjudication")
    if not isinstance(adjudication, Mapping) or adjudication.get("status") not in {
        "AGREED",
        "ADJUDICATED",
        "UNRESOLVED",
    }:
        raise LabelJoinError(f"case {case.get('case_id')!r} has incomplete adjudication")
    if any(value is None for value in working.values()):
        raise LabelJoinError(f"case {case.get('case_id')!r} has a null case judgment")
    for candidates in _candidate_groups(case, "completed").values():
        for candidate in candidates:
            if (
                not isinstance(candidate, Mapping)
                or candidate.get("expected_source_relation") is None
                or candidate.get("expected_support_spans") is None
            ):
                raise LabelJoinError(f"case {case.get('case_id')!r} has a null candidate judgment")


def apply_adjudications(
    draft: Mapping[str, Any],
    annotator_a: Mapping[str, Any],
    annotator_b: Mapping[str, Any],
    decisions: Any,
    digest: Any,
    *,
    event_outputs: Mapping[str, str],
    decisions_r2: Any | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return a schema-ready final sidecar and deterministic accounting summary."""
    draft_cases = _case_map(draft, "merge draft")
    a_cases = _case_map(annotator_a, "annotator-a record")
    b_cases = _case_map(annotator_b, "annotator-b record")
    decision_cases = _decision_map(decisions)
    if decisions_r2 is not None:
        decision_cases = _overlay_round_two_decisions(decision_cases, decisions_r2)
    digest_cases = _digest_map(digest)
    if set(decision_cases) != set(digest_cases):
        raise LabelJoinError("decision and digest case IDs differ")
    if set(draft_cases) != set(a_cases) or set(draft_cases) != set(b_cases):
        raise LabelJoinError("draft and annotator case IDs differ")

    for case in a_cases.values():
        validate_annotator_record(case, event_outputs)
    for case in b_cases.values():
        validate_annotator_record(case, event_outputs)

    final_cases: list[dict[str, Any]] = []
    unresolved_case_ids: list[str] = []
    agreed = 0
    for case in draft.get("cases", []):
        case_id = str(case["case_id"])
        if case_id in decision_cases:
            final_case = apply_ruling(
                case, a_cases[case_id], b_cases[case_id], decision_cases[case_id], digest_cases[case_id]
            )
            if final_case["adjudication"]["status"] == "UNRESOLVED":
                unresolved_case_ids.append(case_id)
        else:
            final_case = copy.deepcopy(dict(case))
            adjudication = final_case.get("adjudication")
            if not isinstance(adjudication, Mapping) or adjudication.get("status") != "AGREED":
                raise LabelJoinError(f"non-adjudicated case {case_id} is not already AGREED")
            agreed += 1
        final_case.pop("notes", None)
        final_case["annotators"] = list(ANNOTATORS)
        _validate_completed_case(final_case, event_outputs)
        final_cases.append(final_case)

    statuses = Counter(str(case["adjudication"]["status"]) for case in final_cases)
    expected_statuses = (
        Counter({"AGREED": 417, "ADJUDICATED": 118})
        if decisions_r2 is not None
        else Counter({"AGREED": 417, "ADJUDICATED": 116, "UNRESOLVED": 2})
    )
    expected_unresolved_count = 0 if decisions_r2 is not None else 2
    if agreed != 417 or statuses != expected_statuses:
        raise LabelJoinError(f"unexpected adjudication status counts: {dict(sorted(statuses.items()))}")
    if len(unresolved_case_ids) != expected_unresolved_count:
        raise LabelJoinError(
            f"expected {expected_unresolved_count} UNRESOLVED cases, found {len(unresolved_case_ids)}"
        )

    final = copy.deepcopy(dict(draft))
    final["qualification_eligible"] = decisions_r2 is not None
    final["qualification_blockers"] = (
        []
        if decisions_r2 is not None
        else [
            STANDING_BLOCKER,
            *[UNRESOLVED_BLOCKER_PREFIX + case_id for case_id in sorted(unresolved_case_ids)],
        ]
    )
    final["cases"] = final_cases
    summary = {
        "cases": len(final_cases),
        "rulings": dict(sorted(Counter(str(decision["ruling"]) for decision in decision_cases.values()).items())),
        "adjudication_statuses": dict(sorted(statuses.items())),
        "unresolved_case_ids": sorted(unresolved_case_ids),
    }
    return final, summary


def write_final_sidecar(
    *,
    decisions_path: Path,
    decisions_r2_path: Path | None = None,
    merge_draft_path: Path,
    annotator_a_path: Path,
    annotator_b_path: Path,
    digest_path: Path,
    event_corpus_dir: Path,
    output_path: Path,
) -> dict[str, Any]:
    """Apply frozen records and atomically write the idempotent final sidecar."""
    event_outputs = build_event_outputs(event_corpus_dir)
    final, summary = apply_adjudications(
        read_json(merge_draft_path),
        read_json(annotator_a_path),
        read_json(annotator_b_path),
        read_json(decisions_path),
        read_json(digest_path),
        event_outputs=event_outputs,
        decisions_r2=read_json(decisions_r2_path) if decisions_r2_path is not None else None,
    )
    atomic_write_json(output_path, final)
    return {**summary, "output": str(output_path), "sha256": sha256_file(output_path)}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decisions", type=Path, required=True)
    parser.add_argument("--decisions-r2", type=Path)
    parser.add_argument("--merge-draft", type=Path, required=True)
    parser.add_argument("--annotator-a", type=Path, required=True)
    parser.add_argument("--annotator-b", type=Path, required=True)
    parser.add_argument("--digest", type=Path, required=True)
    parser.add_argument("--event-corpus-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    summary = write_final_sidecar(
        decisions_path=args.decisions,
        decisions_r2_path=args.decisions_r2,
        merge_draft_path=args.merge_draft,
        annotator_a_path=args.annotator_a,
        annotator_b_path=args.annotator_b,
        digest_path=args.digest,
        event_corpus_dir=args.event_corpus_dir,
        output_path=args.output,
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through the CLI
    raise SystemExit(main())
