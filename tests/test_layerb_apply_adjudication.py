"""Unit tests for mechanical Layer B adjudication application."""

from __future__ import annotations

from scripts.audit.layerb_apply_adjudication import ADJUDICATOR, apply_ruling

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
    return {
        "case_id": "case-1",
        "ruling": ruling,
        "rationale": rationale,
        "adjudicator": ADJUDICATOR,
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
