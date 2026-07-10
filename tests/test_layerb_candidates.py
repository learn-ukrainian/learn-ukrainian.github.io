from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from scripts.audit import anchor_primitives
from scripts.audit.layerb_candidates import (
    AnchorSetResult,
    diff_runtime_records_to_label_case,
    map_flat_anchor_reason,
    materialize_candidates,
)
from scripts.audit.layerb_differential_replay import _comparison_failures, replay_gate_results

ROOT = Path(__file__).resolve().parents[1]
LAYERB_FIXTURES = ROOT / "tests" / "fixtures" / "layerb"
QG_FIXTURES = ROOT / "tests" / "fixtures" / "qg_bakeoff"
RUNTIME_SCHEMA = json.loads((ROOT / "schemas" / "qg-layer-a-candidates.v1.schema.json").read_text(encoding="utf-8"))
RUNTIME_VALIDATOR = jsonschema.Draft202012Validator(RUNTIME_SCHEMA)


def _load_cases() -> list[dict[str, Any]]:
    return json.loads((LAYERB_FIXTURES / "multispan_gate_cases.json").read_text(encoding="utf-8"))["cases"]


def _event(*, output: str, query: str = "Пошук", tool_call_id: str = "call-1") -> dict[str, Any]:
    return {
        "tool": "query_wikipedia",
        "input": {"query": query},
        "output": output,
        "status": "completed",
        "tool_call_id": tool_call_id,
    }


def _grounding(excerpt: str, *, query: str = "Пошук") -> dict[str, str]:
    return {
        "tool": "query_wikipedia",
        "query": query,
        "evidence_excerpt": excerpt,
    }


def _validate_runtime(result: AnchorSetResult) -> None:
    errors = sorted(error.message for error in RUNTIME_VALIDATOR.iter_errors(result.to_dict()))
    assert not errors, "; ".join(errors)


def test_ci_differential_replays_all_unit_fixtures_at_pinned_base_values() -> None:
    """PR-A.4: compare every AnchorResult field for all 21 QG fixture replays."""
    expected = json.loads((LAYERB_FIXTURES / "qg_bakeoff_fixture_base_results.json").read_text(encoding="utf-8"))
    actual = replay_gate_results(fixtures_dir=QG_FIXTURES, tau=0.75)

    assert len(list(QG_FIXTURES.glob("*.json"))) == 21
    assert len(actual) == 21
    assert _comparison_failures(expected["records"], actual) == []


def test_ci_differential_replays_phase_zero_skeleton_multispan_cases_at_pinned_base_values() -> None:
    """PR-A.4: skeleton IDs and real-loss ellipsis cases use BASE-SHA records."""
    skeletons = yaml.safe_load(
        (ROOT / "tests" / "fixtures" / "curriculum_qg" / "layer_b_golden_skeletons.yaml").read_text(encoding="utf-8")
    )
    expected = json.loads((LAYERB_FIXTURES / "multispan_gate_base_results.json").read_text(encoding="utf-8"))
    actual = replay_gate_results(cases_path=LAYERB_FIXTURES / "multispan_gate_cases.json", tau=0.75)

    assert {case["case_id"] for case in skeletons["cases"]} == {case["key"] for case in _load_cases()}
    assert len(actual) == 5
    assert _comparison_failures(expected["records"], actual) == []


def test_materializes_same_event_ordered_segments_and_runtime_schema() -> None:
    for case in _load_cases():
        result = materialize_candidates(case["grounding"], case["events"])
        _validate_runtime(result)
        if case["key"] == "adversarial-cross-event-join":
            assert result.decision == "REJECT"
            assert result.reason == "CROSS_EVENT_STITCH_FORBIDDEN"
            assert result.candidates == ()
            continue
        assert result.decision == "ANCHOR"
        assert result.reason == "ANCHORED_ORDERED_SEGMENTS"
        assert result.candidate_set_complete is True
        assert result.candidates
        for candidate in result.candidates:
            assert candidate.match_type == "ORDERED_EXACT_SEGMENTS"
            assert len(candidate.ordered_segment_spans) == 2
            assert (
                candidate.ordered_segment_spans[0].output_normalized_end
                <= candidate.ordered_segment_spans[1].output_normalized_start
            )
            assert (
                candidate.ordered_segment_spans[0].output_raw_end <= candidate.ordered_segment_spans[1].output_raw_start
            )


def test_alignment_round_trips_stress_mark_and_schema_omits_label_only_fields() -> None:
    raw = "Сковоро́да народився у 1722 році."
    result = materialize_candidates(
        _grounding("Сковорода народився у 1722 році.", query="Григорій Сковорода"),
        [_event(output=raw, query="Григорій Сковорода")],
    )

    assert result.decision == "ANCHOR"
    candidate = result.candidates[0]
    segment = candidate.ordered_segment_spans[0]
    assert raw[segment.output_raw_start : segment.output_raw_end] == raw
    assert segment.output_raw_end - segment.output_raw_start > (
        segment.output_normalized_end - segment.output_normalized_start
    )
    serialized = candidate.to_dict()
    assert "expected_source_relation" not in serialized
    assert "expected_support_spans" not in serialized
    assert "event_output_id" in serialized
    _validate_runtime(result)


def test_alignment_accepts_complete_casefold_expansion_but_rejects_internal_boundary() -> None:
    alignment = anchor_primitives.build_normalized_raw_alignment("Straße")

    assert alignment.normalized == "strasse"
    assert alignment.raw_span_for(0, len(alignment.normalized)) == (0, len("Straße"))
    assert alignment.raw_span_for(4, 5) is None


def test_candidate_ids_ignore_event_order_but_keep_diagnostic_source_index() -> None:
    grounding = _grounding("Сковорода народився у 1722 році.", query="Григорій Сковорода")
    first = _event(
        output="Сковорода народився у 1722 році. Перше джерело.",
        query="Григорій Сковорода",
        tool_call_id="first",
    )
    second = _event(
        output="Сковорода народився у 1722 році. Друге джерело.",
        query="Григорій Сковорода",
        tool_call_id="second",
    )
    forward = materialize_candidates(grounding, [first, second])
    reversed_result = materialize_candidates(grounding, [second, first])

    assert {candidate.candidate_id for candidate in forward.candidates} == {
        candidate.candidate_id for candidate in reversed_result.candidates
    }
    assert {candidate.candidate_id: candidate.source_index for candidate in forward.candidates} != {
        candidate.candidate_id: candidate.source_index for candidate in reversed_result.candidates
    }


def test_enumerates_repeated_ellipsis_assignments_and_audits_explicit_bound() -> None:
    excerpt = "Перша фраза ... Друга фраза"
    output = "Перша фраза. Друга фраза. Перша фраза. Друга фраза."
    result = materialize_candidates(_grounding(excerpt), [_event(output=output)])

    assert result.decision == "ANCHOR"
    assert result.candidate_count_before_dedup == 3
    assert len(result.candidates) == 3
    assert len({candidate.candidate_id for candidate in result.candidates}) == 3
    assert all(candidate.match_type == "ORDERED_EXACT_SEGMENTS" for candidate in result.candidates)

    limited = materialize_candidates(_grounding(excerpt), [_event(output=output)], max_ellipsis_assignments=1)
    assert limited.decision == "AUDIT"
    assert limited.reason == "OUTSIDE_SCAN"
    assert limited.candidate_set_complete is False


def test_unmappable_flat_reason_class_fails_closed_as_audit() -> None:
    result = materialize_candidates(
        _grounding("звичайний текст без власних назв"), [_event(output="звичайний текст без власних назв")]
    )

    assert result.decision == "AUDIT"
    assert result.reason == "INCOMPLETE_CANDIDATE_SET"
    assert result.candidate_set_complete is False


def test_flat_reason_mapping_is_registered_and_unmappable_reasons_audit() -> None:
    mappings = {
        "anchored": ("ANCHOR", "ANCHORED_CONTIGUOUS"),
        "abstain_ambiguous": ("AUDIT", "FUZZY_AMBIGUOUS"),
        "candidate_truncated": ("AUDIT", "OUTSIDE_SCAN"),
        "below_tau": ("REJECT", "BELOW_TAU"),
        "digit_not_aligned": ("REJECT", "DIGIT_NOT_ALIGNED"),
        "insufficient_mass": ("REJECT", "INSUFFICIENT_MASS"),
        "salient_not_aligned": ("REJECT", "SALIENT_NOT_ALIGNED"),
        "no_output": ("AUDIT", "INCOMPLETE_CANDIDATE_SET"),
        "no_salient_anchor": ("AUDIT", "INCOMPLETE_CANDIDATE_SET"),
        "future_unknown_reason": ("AUDIT", "INCOMPLETE_CANDIDATE_SET"),
    }

    assert {reason: map_flat_anchor_reason(reason) for reason in mappings} == mappings
    assert map_flat_anchor_reason("anchored", has_ellipsis=True) == ("ANCHOR", "ANCHORED_ORDERED_SEGMENTS")


def test_diff_utility_reconciles_explicit_runtime_event_id_with_label_grouping() -> None:
    result = materialize_candidates(
        _grounding("Сковорода народився у 1722 році.", query="Григорій Сковорода"),
        [_event(output="Сковорода народився у 1722 році.", query="Григорій Сковорода")],
    )
    runtime_candidate = result.candidates[0].to_dict()
    label_candidate = {
        key: value
        for key, value in runtime_candidate.items()
        if key not in {"schema_version", "event_output_id", "tool_query_matched"}
    }
    label_case = {
        "expected_layer_a_decision": "ANCHOR",
        "expected_layer_a_reason": "ANCHORED_CONTIGUOUS",
        "candidate_set_complete": True,
        "candidates_by_event_output_id": {runtime_candidate["event_output_id"]: [label_candidate]},
    }

    assert diff_runtime_records_to_label_case(result, label_case) == ()
    wrong_label = deepcopy(label_case)
    wrong_label["candidates_by_event_output_id"][runtime_candidate["event_output_id"]][0]["raw_output_sha256"] = (
        "0" * 64
    )
    assert any("raw_output_sha256 differs" in diff for diff in diff_runtime_records_to_label_case(result, wrong_label))
