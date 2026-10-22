"""Executable contract tests for the issue #5452 bounded completion slice."""

from __future__ import annotations

import importlib.util
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

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


def _semantic_review_ready_run() -> dict[str, Any]:
    run = bc.start_run(
        target="bio/semantic-ready",
        run_id="8" * 32,
        review_protocol_identity=_protocol(),
        learner_source_sha256=SOURCE_A,
    )
    run = bc.complete_inspection(run, needs_build=False)
    return bc.record_deterministic_verification(
        run,
        learner_source_sha256=SOURCE_A,
        passed=True,
    )


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


def test_budget_exhaustion_rejects_review_repair_and_publication_without_mutation() -> None:
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
        {
            "step": 9,
            "code": "PUBLICATION_BLOCKED",
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

    before = deepcopy(run)
    with pytest.raises(bc.BoundedCompletionError, match="PUBLICATION_BLOCKED"):
        bc.record_publication(run, reference="forbidden-deterministic-publication")
    assert run == before


@pytest.mark.parametrize(
    ("state", "terminal", "publication"),
    [
        ("FINAL_DISPOSITION", False, None),
        (
            "PUBLICATION",
            True,
            {
                "reference": "forged-publication",
                "learner_source_sha256": SOURCE_A,
            },
        ),
    ],
)
def test_forged_publishable_run_without_current_review_evidence_is_rejected(
    state: str,
    terminal: bool,
    publication: dict[str, str] | None,
) -> None:
    forged = bc.start_run(
        target="bio/forged-publishable",
        run_id="9" * 32,
        review_protocol_identity=_protocol(),
        learner_source_sha256=SOURCE_A,
    )
    forged["state"] = state
    forged["terminal"] = terminal
    forged["publication"] = publication
    forged["measurements"]["final_quality_disposition"] = "PUBLISHABLE"
    before = deepcopy(forged)

    with pytest.raises(bc.BoundedCompletionError, match="RUN_INVARIANT"):
        bc.validate_run(forged)
    with pytest.raises(bc.BoundedCompletionError, match="RUN_INVARIANT"):
        bc.record_publication(forged, reference="forged-publication-attempt")
    assert forged == before


def test_terminal_semantic_review_run_rejects_further_action_without_mutation() -> None:
    forged = _semantic_review_ready_run()
    forged["terminal"] = True
    before = deepcopy(forged)

    with pytest.raises(bc.BoundedCompletionError, match="RUN_INVARIANT"):
        bc.record_semantic_review(
            forged,
            review_protocol_identity=_protocol(),
            learner_source_sha256=SOURCE_A,
            evidence_id="forbidden-terminal-review",
            reported_disposition="PASS",
            dimension_scores={
                "engagement": 9.0,
                "pedagogical": 9.0,
                "naturalness": 9.0,
                "decolonization": 9.0,
                "tone": 9.0,
            },
            prompt_bytes=1,
            schema_bytes=1,
        )
    assert forged == before


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
