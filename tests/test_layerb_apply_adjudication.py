"""Unit tests for mechanical Layer B adjudication application."""

from __future__ import annotations

import copy

import pytest

import scripts.audit.layerb_apply_adjudication as adjudication
from scripts.audit.layerb_apply_adjudication import ADJUDICATOR, ADJUDICATOR_R2, apply_ruling
from scripts.audit.layerb_label_common import LabelJoinError

EVENT_OUTPUT_ID = "a" * 64


def _span(start: int, role: str = "SUPPORTS") -> dict[str, int | str]:
    return {"start": start, "end": start + 2, "role": role}


def _case(
    *,
    aggregate: str = "NO_RELATION",
    fact_check: str = "REJECT",
    source_relation: str = "NO_RELATION",
    spans: list[dict[str, int | str]] | None = None,
) -> dict[str, object]:
    return {
        "case_id": "case-1",
        "expected_aggregate_relation": aggregate,
        "expected_fact_check_decision": fact_check,
        "candidates_by_event_output_id": {
            EVENT_OUTPUT_ID: [
                {
                    "candidate_id": "candidate-1",
                    "expected_source_relation": source_relation,
                    "expected_support_spans": spans or [],
                }
            ]
        },
    }


def _decision(ruling: str, rationale: str = "Frozen rationale.") -> dict[str, str]:
    return _case_decision("case-1", ruling, rationale=rationale)


def _case_decision(
    case_id: str,
    ruling: str,
    *,
    rationale: str = "Frozen rationale.",
    adjudicator: str = ADJUDICATOR,
) -> dict[str, str]:
    return {
        "case_id": case_id,
        "ruling": ruling,
        "rationale": rationale,
        "adjudicator": adjudicator,
    }


def _round_two_decision(case_id: str, ruling: str = "B") -> dict[str, object]:
    return {
        **_case_decision(case_id, ruling, adjudicator=ADJUDICATOR_R2),
        "round": 2,
        "supersedes_ruling": "UNRESOLVED",
    }


def _digest(*fields: str) -> dict[str, object]:
    return {"case_id": "case-1", "fields": {field: {} for field in fields}}


def _candidate(case: dict[str, object]) -> dict[str, object]:
    groups = case["candidates_by_event_output_id"]
    assert isinstance(groups, dict)
    candidates = groups[EVENT_OUTPUT_ID]
    assert isinstance(candidates, list)
    candidate = candidates[0]
    assert isinstance(candidate, dict)
    return candidate


def _status_pin_documents() -> tuple[dict[str, object], list[dict[str, str]], list[dict[str, object]]]:
    """Build lightweight cases for accounting tests; record validation is patched there."""
    agreed_cases = [
        {"case_id": f"agreed-{index}", "adjudication": {"status": "AGREED"}}
        for index in range(417)
    ]
    adjudicated_ids = [f"adjudicated-{index}" for index in range(116)]
    unresolved_ids = ["unresolved-0", "unresolved-1"]
    decisions = [_case_decision(case_id, "A") for case_id in adjudicated_ids]
    decisions.extend(_case_decision(case_id, "UNRESOLVED") for case_id in unresolved_ids)
    digest = [
        {"case_id": decision["case_id"], "fields": {"expected_aggregate_relation": {}}}
        for decision in decisions
    ]
    cases = [*agreed_cases]
    cases.extend({"case_id": case_id} for case_id in adjudicated_ids)
    cases.extend({"case_id": case_id} for case_id in unresolved_ids)
    return {"cases": cases}, decisions, digest


def test_apply_ruling_copies_selected_a_or_b_judgment_fields() -> None:
    draft = _case()
    left = _case(aggregate="ENTAILS", fact_check="ACCEPT", source_relation="ENTAILS", spans=[_span(1)])
    right = _case(
        aggregate="CONTRADICTS",
        fact_check="AUDIT",
        source_relation="CONTRADICTS",
        spans=[_span(7, "CONTRADICTS")],
    )
    digest = _digest(
        "expected_aggregate_relation",
        "expected_fact_check_decision",
        "expected_source_relation",
        "expected_support_spans",
    )

    selected_a = apply_ruling(draft, left, right, _decision("A"), digest)
    selected_b = apply_ruling(draft, left, right, _decision("B"), digest)

    assert selected_a["expected_aggregate_relation"] == "ENTAILS"
    assert selected_a["expected_fact_check_decision"] == "ACCEPT"
    assert _candidate(selected_a)["expected_source_relation"] == "ENTAILS"
    assert selected_b["expected_aggregate_relation"] == "CONTRADICTS"
    assert selected_b["expected_fact_check_decision"] == "AUDIT"
    assert _candidate(selected_b)["expected_source_relation"] == "CONTRADICTS"
    assert selected_b["adjudication"] == {
        "status": "ADJUDICATED",
        "adjudicator": ADJUDICATOR,
        "note": "Frozen rationale.",
    }


def test_apply_ruling_unions_spans_in_a_then_b_order_without_duplicates() -> None:
    draft = _case(spans=[_span(1)])
    left = _case(spans=[_span(1), _span(3, "CONTRADICTS")])
    right = _case(spans=[_span(3, "CONTRADICTS"), _span(5, "UNCERTAINTY")])

    result = apply_ruling(draft, left, right, _decision("UNION"), _digest("expected_support_spans"))

    assert _candidate(result)["expected_support_spans"] == [
        _span(1),
        _span(3, "CONTRADICTS"),
        _span(5, "UNCERTAINTY"),
    ]
    assert result["adjudication"]["status"] == "ADJUDICATED"
    assert "UNION" in result["adjudication"]["note"]


def test_apply_ruling_custom_uses_rationale_selected_b_candidate_values() -> None:
    draft = _case()
    left = _case(aggregate="MIXED", fact_check="AUDIT", source_relation="MIXED", spans=[_span(1)])
    right = _case(
        aggregate="INSUFFICIENT_CONTEXT",
        fact_check="AUDIT",
        source_relation="CONTRADICTS",
        spans=[_span(7, "CONTRADICTS")],
    )
    ruling = "CUSTOM:aggregate_relation=CONTRADICTS,fact_check_decision=ACCEPT"

    result = apply_ruling(
        draft,
        left,
        right,
        _decision(ruling, "B's srel right; frozen custom aggregate."),
        _digest(
            "expected_aggregate_relation",
            "expected_fact_check_decision",
            "expected_source_relation",
            "expected_support_spans",
        ),
    )

    assert result["expected_aggregate_relation"] == "CONTRADICTS"
    assert result["expected_fact_check_decision"] == "ACCEPT"
    assert _candidate(result)["expected_source_relation"] == "CONTRADICTS"
    assert _candidate(result)["expected_support_spans"] == [_span(7, "CONTRADICTS")]


def test_apply_ruling_custom_without_b_source_instruction_keeps_a_candidate_values() -> None:
    draft = _case()
    left = _case(source_relation="NO_RELATION")
    right = _case(source_relation="ENTAILS", spans=[_span(3)])
    ruling = "CUSTOM:aggregate_relation=INSUFFICIENT_CONTEXT,fact_check_decision=AUDIT"

    result = apply_ruling(
        draft,
        left,
        right,
        _decision(ruling, "The source relates thinly but is not decisive."),
        _digest(
            "expected_aggregate_relation",
            "expected_fact_check_decision",
            "expected_source_relation",
            "expected_support_spans",
        ),
    )

    assert result["expected_aggregate_relation"] == "INSUFFICIENT_CONTEXT"
    assert result["expected_fact_check_decision"] == "AUDIT"
    assert _candidate(result)["expected_source_relation"] == "NO_RELATION"
    assert _candidate(result)["expected_support_spans"] == []


def test_apply_ruling_marks_unresolved_without_changing_a_values() -> None:
    draft = _case()
    left = _case(aggregate="ENTAILS", source_relation="ENTAILS", spans=[_span(1)])
    right = _case(aggregate="INSUFFICIENT_CONTEXT", source_relation="NO_RELATION")

    result = apply_ruling(
        draft,
        left,
        right,
        _decision("UNRESOLVED"),
        _digest("expected_aggregate_relation", "expected_source_relation", "expected_support_spans"),
    )

    assert result["expected_aggregate_relation"] == "ENTAILS"
    assert _candidate(result)["expected_source_relation"] == "ENTAILS"
    assert result["adjudication"] == {
        "status": "UNRESOLVED",
        "adjudicator": ADJUDICATOR,
        "note": "Frozen rationale.",
    }


def test_apply_ruling_accepts_direct_agreed_ruling_with_null_adjudicator() -> None:
    result = apply_ruling(
        _case(),
        _case(),
        _case(),
        {
            "case_id": "case-1",
            "ruling": "AGREED",
            "rationale": "Independent annotations matched all material fields.",
            "adjudicator": None,
        },
        _digest(),
    )

    assert result["adjudication"] == {
        "status": "AGREED",
        "adjudicator": None,
        "note": "Independent annotations matched all material fields.",
    }


def test_apply_ruling_custom_sets_single_candidate_and_empty_spans_without_residual_heuristic() -> None:
    draft = _case(source_relation="ENTAILS", spans=[_span(1)])
    left = _case(source_relation="NO_RELATION")
    right = _case(source_relation="CONTRADICTS", spans=[_span(7, "CONTRADICTS")])
    ruling = (
        "CUSTOM:candidate.expected_source_relation=INSUFFICIENT_CONTEXT,"
        "candidate.expected_support_spans=EMPTY,aggregate_relation=INSUFFICIENT_CONTEXT,"
        "fact_check_decision=AUDIT"
    )

    result = apply_ruling(
        draft,
        left,
        right,
        _decision(ruling, "B's srel right, but the candidate custom is explicit."),
        _digest(
            "expected_aggregate_relation",
            "expected_fact_check_decision",
            "expected_source_relation",
            "expected_support_spans",
        ),
    )

    assert result["expected_aggregate_relation"] == "INSUFFICIENT_CONTEXT"
    assert result["expected_fact_check_decision"] == "AUDIT"
    assert _candidate(result)["expected_source_relation"] == "INSUFFICIENT_CONTEXT"
    assert _candidate(result)["expected_support_spans"] == []


def test_apply_ruling_candidate_custom_rejects_multiple_candidates_and_nonempty_spans() -> None:
    draft = _case()
    groups = draft["candidates_by_event_output_id"]
    assert isinstance(groups, dict)
    groups["b" * 64] = [
        {
            "candidate_id": "candidate-2",
            "expected_source_relation": "NO_RELATION",
            "expected_support_spans": [],
        }
    ]
    candidate_ruling = "CUSTOM:candidate.expected_source_relation=INSUFFICIENT_CONTEXT"

    with pytest.raises(LabelJoinError, match="requires exactly one candidate"):
        apply_ruling(draft, _case(), _case(), _decision(candidate_ruling), _digest("expected_source_relation"))

    with pytest.raises(LabelJoinError, match="literal EMPTY"):
        apply_ruling(
            _case(),
            _case(),
            _case(),
            _decision("CUSTOM:candidate.expected_support_spans=NOT_EMPTY"),
            _digest("expected_support_spans"),
        )


def test_round_two_overlay_rejects_non_unresolved_targets() -> None:
    with pytest.raises(LabelJoinError, match="does not target a Round-1 UNRESOLVED case"):
        adjudication._overlay_round_two_decisions(
            {"case-1": _case_decision("case-1", "A")},
            [_round_two_decision("case-1")],
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("adjudicator", "not-the-frozen-adjudicator", "unexpected adjudicator"),
        ("round", 1, "must carry round=2"),
        ("supersedes_ruling", "A", "must supersede UNRESOLVED"),
    ],
)
def test_round_two_overlay_requires_frozen_metadata(field: str, value: object, message: str) -> None:
    decision = _round_two_decision("case-1")
    decision[field] = value

    with pytest.raises(LabelJoinError, match=message):
        adjudication._overlay_round_two_decisions(
            {"case-1": _case_decision("case-1", "UNRESOLVED")},
            [decision],
        )


def test_apply_adjudications_preserves_round_one_counts_without_overlay_and_resolves_with_overlay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    draft, decisions, digest = _status_pin_documents()
    monkeypatch.setattr(adjudication, "validate_annotator_record", lambda _case, _outputs: None)
    monkeypatch.setattr(adjudication, "_validate_completed_case", lambda _case, _outputs: None)

    without_overlay, summary_without_overlay = adjudication.apply_adjudications(
        draft,
        copy.deepcopy(draft),
        copy.deepcopy(draft),
        decisions,
        digest,
        event_outputs={},
    )

    assert summary_without_overlay["adjudication_statuses"] == {
        "ADJUDICATED": 116,
        "AGREED": 417,
        "UNRESOLVED": 2,
    }
    assert without_overlay["qualification_eligible"] is False
    assert without_overlay["qualification_blockers"] == [
        "2 UNRESOLVED cases pending re-adjudication",
        "UNRESOLVED case pending re-adjudication: unresolved-0",
        "UNRESOLVED case pending re-adjudication: unresolved-1",
    ]

    with_overlay, summary_with_overlay = adjudication.apply_adjudications(
        draft,
        copy.deepcopy(draft),
        copy.deepcopy(draft),
        decisions,
        digest,
        event_outputs={},
        decisions_r2=[
            _round_two_decision("unresolved-0", "B"),
            _round_two_decision(
                "unresolved-1",
                "CUSTOM:aggregate_relation=INSUFFICIENT_CONTEXT,fact_check_decision=AUDIT",
            ),
        ],
    )

    assert summary_with_overlay["adjudication_statuses"] == {"ADJUDICATED": 118, "AGREED": 417}
    assert summary_with_overlay["unresolved_case_ids"] == []
    assert with_overlay["qualification_eligible"] is True
    assert with_overlay["qualification_blockers"] == []
    resolved_case = next(case for case in with_overlay["cases"] if case["case_id"] == "unresolved-0")
    assert resolved_case["adjudication"]["adjudicator"] == ADJUDICATOR_R2


def test_apply_adjudications_tolerates_cosmetic_only_merge_report_cases(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    material_case = _case()
    cosmetic_case = {
        "case_id": "cosmetic-case",
        "adjudication": {
            "status": "AGREED",
            "adjudicator": None,
            "note": "Only cosmetic differences were found.",
        },
    }
    draft = {"cases": [material_case, cosmetic_case]}
    merge_report_digest = {
        "cases": [
            {
                "case_id": "case-1",
                "material_differences": [{"field": "expected_aggregate_relation"}],
            }
        ],
        "cosmetic_only_case_ids": ["cosmetic-case"],
    }
    monkeypatch.setattr(adjudication, "validate_annotator_record", lambda _case, _outputs: None)
    monkeypatch.setattr(adjudication, "_validate_completed_case", lambda _case, _outputs: None)

    final, summary = adjudication.apply_adjudications(
        draft,
        copy.deepcopy(draft),
        copy.deepcopy(draft),
        [_decision("A")],
        merge_report_digest,
        event_outputs={},
    )

    assert summary["adjudication_statuses"] == {"ADJUDICATED": 1, "AGREED": 1}
    cosmetic_final_case = next(case for case in final["cases"] if case["case_id"] == "cosmetic-case")
    assert cosmetic_final_case["adjudication"] == {
        "status": "AGREED",
        "adjudicator": None,
        "note": "Only cosmetic differences were found.",
    }
