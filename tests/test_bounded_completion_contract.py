"""Executable contract tests for the issue #5452 bounded completion slice."""

from __future__ import annotations

import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "agents_extensions" / "shared" / "skills" / "track-completion"
SCRIPT = SKILL_ROOT / "scripts" / "bounded_completion.py"
FIXTURES = ROOT / "tests" / "fixtures" / "bounded_completion"
SPEC = importlib.util.spec_from_file_location("bounded_completion_for_tests", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
bc = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = bc
SPEC.loader.exec_module(bc)

SOURCE_A = "a" * 64
SOURCE_B = "b" * 64


def _fixture(name: str) -> dict[str, Any]:
    return bc.replay_fixture(FIXTURES / name)["run"]


def _protocol() -> dict[str, str]:
    return bc.make_review_protocol_identity(
        protocol_version="5.0.0",
        tool_sha256="1" * 64,
        prompt_sha256="2" * 64,
        schema_sha256="3" * 64,
        reviewer_family="fixture-family",
        reviewer_model="fixture-model",
    )


def test_canonical_contract_pins_states_budgets_quality_and_measurements() -> None:
    contract = bc.load_contract()

    assert contract["contract_version"] == "1.0.0"
    assert contract["states"] == [
        "INSPECT",
        "BUILD_REBUILD",
        "DETERMINISTIC_VERIFICATION",
        "SEMANTIC_REVIEW",
        "CONSOLIDATED_REPAIR",
        "FINAL_DISPOSITION",
        "PUBLICATION",
    ]
    assert contract["budgets"] == {
        "initial_semantic_reviews": 1,
        "consolidated_repairs": 1,
        "final_semantic_reviews": 1,
        "semantic_reviews_total": 2,
    }
    assert contract["review_protocol_freeze"] == {
        "pin_at_run_start": True,
        "drift_policy": "REJECT_WITHOUT_MUTATION",
    }
    assert contract["publication_quality"] == {
        "minimum_per_dimension": 9.0,
        "dimensions": [
            "engagement",
            "pedagogical",
            "naturalness",
            "decolonization",
            "tone",
        ],
        "aggregate_override_allowed": False,
        "threshold_lowering_allowed": False,
    }
    assert contract["measurement_fields"] == [
        "elapsed_time_ms",
        "model_call_count",
        "repair_count",
        "prompt_bytes",
        "schema_bytes",
        "final_quality_disposition",
    ]


def test_contract_schema_rejects_threshold_lowering() -> None:
    contract = bc.load_contract()
    schema = json.loads(bc.CONTRACT_SCHEMA_PATH.read_text(encoding="utf-8"))
    lowered = deepcopy(contract)
    lowered["publication_quality"]["minimum_per_dimension"] = 8.99

    errors = list(Draft202012Validator(schema).iter_errors(lowered))

    assert errors
    assert any("9.0 was expected" in error.message for error in errors)


@pytest.mark.parametrize(
    "fixture_name",
    [
        "success.json",
        "budget-exhaustion.json",
        "protocol-drift.json",
        "quality-floor.json",
    ],
)
def test_every_regression_fixture_replays_to_a_schema_valid_run(
    fixture_name: str,
) -> None:
    result = bc.replay_fixture(FIXTURES / fixture_name)

    bc.validate_run(result["run"])


def test_success_fixture_covers_measurements_and_publication() -> None:
    run = _fixture("success.json")

    assert run["state"] == "PUBLICATION"
    assert run["terminal"] is True
    assert run["measurements"] == {
        "elapsed_time_ms": 98,
        "model_call_count": 2,
        "repair_count": 1,
        "prompt_bytes": 2500,
        "schema_bytes": 800,
        "final_quality_disposition": "PUBLISHABLE",
    }
    assert run["publication"] == {
        "reference": "fixture-publication",
        "learner_source_sha256": SOURCE_B,
    }


def test_material_learner_repair_invalidates_prior_review_evidence() -> None:
    run = _fixture("success.json")
    initial, final = run["reviews"]

    assert initial["learner_source_sha256"] == SOURCE_A
    assert initial["valid"] is False
    assert initial["invalidated_reason"] == "LEARNER_SOURCE_CHANGED"
    assert final["learner_source_sha256"] == SOURCE_B
    assert final["valid"] is True
    assert final["invalidated_reason"] is None
    assert run["repairs"] == [
        {
            "source_before_sha256": SOURCE_A,
            "source_after_sha256": SOURCE_B,
            "invalidated_evidence_ids": ["initial-review"],
        }
    ]


def test_third_review_and_second_repair_fail_closed_after_terminal_stop() -> None:
    result = bc.replay_fixture(FIXTURES / "budget-exhaustion.json")
    run = result["run"]

    assert result["expected_errors"] == [
        {
            "step": 7,
            "code": "SEMANTIC_REVIEW_BUDGET_EXHAUSTED",
            "unchanged": True,
        },
        {
            "step": 8,
            "code": "REPAIR_BUDGET_EXHAUSTED",
            "unchanged": True,
        },
    ]
    assert run["state"] == "FINAL_DISPOSITION"
    assert run["terminal"] is True
    assert run["measurements"] == {
        "elapsed_time_ms": 48,
        "model_call_count": 2,
        "repair_count": 1,
        "prompt_bytes": 2100,
        "schema_bytes": 700,
        "final_quality_disposition": "BLOCKED_BUDGET_EXHAUSTED",
    }
    assert len(run["reviews"]) == 2
    assert len(run["repairs"]) == 1
    assert run["publication"] is None


def test_protocol_drift_rejection_does_not_reopen_or_mutate_active_run() -> None:
    result = bc.replay_fixture(FIXTURES / "protocol-drift.json")
    run = result["run"]

    assert result["expected_errors"] == [{"step": 3, "code": "REVIEW_PROTOCOL_DRIFT", "unchanged": True}]
    assert run["state"] == "SEMANTIC_REVIEW"
    assert run["terminal"] is False
    assert run["reviews"] == []
    assert run["measurements"] == {
        "elapsed_time_ms": 5,
        "model_call_count": 0,
        "repair_count": 0,
        "prompt_bytes": 0,
        "schema_bytes": 0,
        "final_quality_disposition": "PENDING",
    }


def test_reported_pass_below_any_9_point_dimension_fails_closed() -> None:
    run = _fixture("quality-floor.json")
    review = run["reviews"][0]

    assert review["reported_disposition"] == "PASS"
    assert review["contract_disposition"] == "BLOCK"
    assert review["threshold_failures"] == ["tone"]
    assert run["state"] == "CONSOLIDATED_REPAIR"
    assert run["measurements"]["final_quality_disposition"] == "PENDING"
    assert run["publication"] is None


def test_build_rebuild_path_rejoins_deterministic_verification() -> None:
    run = bc.start_run(
        target="bio/unbuilt-fixture",
        run_id="5" * 32,
        review_protocol_identity=_protocol(),
        learner_source_sha256=None,
    )

    run = bc.complete_inspection(run, needs_build=True, elapsed_time_ms=2)
    assert run["state"] == "BUILD_REBUILD"

    run = bc.complete_build(
        run,
        learner_source_sha256=SOURCE_A,
        elapsed_time_ms=3,
    )
    assert run["state"] == "DETERMINISTIC_VERIFICATION"
    assert run["learner_source_sha256"] == SOURCE_A
    assert run["measurements"]["elapsed_time_ms"] == 5


def test_deterministic_failure_is_a_terminal_non_publication_disposition() -> None:
    run = bc.start_run(
        target="bio/deterministic-block",
        run_id="6" * 32,
        review_protocol_identity=_protocol(),
        learner_source_sha256=SOURCE_A,
    )
    run = bc.complete_inspection(run, needs_build=False)
    run = bc.record_deterministic_verification(
        run,
        learner_source_sha256=SOURCE_A,
        passed=False,
    )

    assert run["state"] == "FINAL_DISPOSITION"
    assert run["terminal"] is True
    assert run["measurements"]["final_quality_disposition"] == "BLOCKED_DETERMINISTIC"
    assert run["measurements"]["model_call_count"] == 0
    assert run["publication"] is None


def test_tampered_protocol_identity_is_rejected_at_run_start() -> None:
    protocol = _protocol()
    protocol["identity_sha256"] = "f" * 64

    with pytest.raises(bc.BoundedCompletionError, match="PROTOCOL_IDENTITY_INVALID"):
        bc.start_run(
            target="bio/tampered-protocol",
            run_id="7" * 32,
            review_protocol_identity=protocol,
            learner_source_sha256=SOURCE_A,
        )
