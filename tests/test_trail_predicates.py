"""Tests for pure typed decision-table evaluation."""

from __future__ import annotations

import copy

from scripts.orchestration.trail_predicates import (
    STOP_UNKNOWN,
    evaluate_named_table,
    evaluate_table,
    load_decision_tables,
)


def _queue_inputs(**overrides: object) -> dict[str, object]:
    inputs: dict[str, object] = {
        "is_foreign_lane": False,
        "has_sibling_pr": False,
        "queue_order_derivable": True,
        "dependencies_merged": True,
    }
    inputs.update(overrides)
    return inputs


def test_static_table_returns_the_single_typed_outcome_token() -> None:
    tables = load_decision_tables()

    assert evaluate_table(tables["tables"]["queue-pick"], _queue_inputs()) == "pick-lowest-ready-item"


def test_typed_input_enforcement_parks_invalid_boolean_and_extra_input() -> None:
    tables = load_decision_tables()

    invalid_boolean = _queue_inputs(is_foreign_lane=1)
    assert evaluate_named_table(tables, "queue-pick", invalid_boolean) == STOP_UNKNOWN

    extra_input = _queue_inputs(unexpected=True)
    assert evaluate_named_table(tables, "queue-pick", extra_input) == STOP_UNKNOWN


def test_unknown_enum_input_parks() -> None:
    tables = load_decision_tables()
    inputs = {
        "blocker_class": "unrecognized-blocker",
    }

    assert evaluate_named_table(tables, "summon-vs-park", inputs) == STOP_UNKNOWN
    assert (
        evaluate_named_table(
            tables,
            "settle-status",
            {"task_status": "unrecognized-status", "has_retry_suffix": False},
        )
        == STOP_UNKNOWN
    )


def test_zero_matching_rows_park() -> None:
    tables = load_decision_tables()

    result = evaluate_named_table(
        tables,
        "queue-pick",
        _queue_inputs(dependencies_merged=False),
    )

    assert result == STOP_UNKNOWN


def test_multiple_matching_rows_park() -> None:
    tables = copy.deepcopy(load_decision_tables())
    queue_rows = tables["tables"]["queue-pick"]["rows"]
    queue_rows.append(copy.deepcopy(queue_rows[-1]))

    assert evaluate_named_table(tables, "queue-pick", _queue_inputs()) == STOP_UNKNOWN


def test_malformed_outcome_token_parks() -> None:
    tables = copy.deepcopy(load_decision_tables())
    outcome = tables["tables"]["queue-pick"]["rows"][-1]["outcome"]
    outcome["token"] = "free form prose"

    assert evaluate_named_table(tables, "queue-pick", _queue_inputs()) == STOP_UNKNOWN
