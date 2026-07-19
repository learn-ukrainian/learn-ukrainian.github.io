#!/usr/bin/env python3
"""Pure, bounded state machine for one module-completion run.

This helper intentionally has no provider transport and is not imported by the
production track-completion lifecycle. It makes the issue #5452 contract
executable without triggering semantic review calls.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT_PATH = SKILL_ROOT / "contracts" / "bounded-completion.v1.json"
CONTRACT_SCHEMA_PATH = SKILL_ROOT / "schema" / "bounded-completion-contract.v1.schema.json"
RUN_SCHEMA_PATH = SKILL_ROOT / "schema" / "bounded-completion-run.v1.schema.json"

_PROTOCOL_FIELDS = (
    "protocol_version",
    "tool_sha256",
    "prompt_sha256",
    "schema_sha256",
    "reviewer_family",
    "reviewer_model",
)
_EXPECTED_TRANSITIONS = {
    "INSPECT": ["BUILD_REBUILD", "DETERMINISTIC_VERIFICATION"],
    "BUILD_REBUILD": ["DETERMINISTIC_VERIFICATION"],
    "DETERMINISTIC_VERIFICATION": ["SEMANTIC_REVIEW", "FINAL_DISPOSITION"],
    "SEMANTIC_REVIEW": ["CONSOLIDATED_REPAIR", "FINAL_DISPOSITION"],
    "CONSOLIDATED_REPAIR": ["DETERMINISTIC_VERIFICATION"],
    "FINAL_DISPOSITION": ["PUBLICATION"],
    "PUBLICATION": [],
}


class BoundedCompletionError(RuntimeError):
    """Raised when the bounded contract rejects an input or transition."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"[{code}] {message}")


def stable_json(value: object) -> str:
    """Return the canonical JSON representation used for identity hashes."""

    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(value: object) -> str:
    """Hash a JSON-compatible value using the canonical representation."""

    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def read_json(path: Path) -> Any:
    """Read one UTF-8 JSON document."""

    return json.loads(path.read_text(encoding="utf-8"))


def _validate(value: object, schema_path: Path, label: str) -> None:
    schema = read_json(schema_path)
    Draft202012Validator.check_schema(schema)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(value),
        key=lambda error: [str(part) for part in error.absolute_path],
    )
    if not errors:
        return
    details = "; ".join(
        f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}" for error in errors[:8]
    )
    raise BoundedCompletionError("SCHEMA_INVALID", f"Invalid {label}: {details}")


def load_contract(path: Path = DEFAULT_CONTRACT_PATH) -> dict[str, Any]:
    """Load and validate the canonical bounded-completion contract."""

    value = read_json(path)
    if not isinstance(value, dict):
        raise BoundedCompletionError("CONTRACT_INVALID", "Contract root must be an object")
    _validate(value, CONTRACT_SCHEMA_PATH, "bounded-completion contract")
    if value["transitions"] != _EXPECTED_TRANSITIONS:
        raise BoundedCompletionError(
            "CONTRACT_INVALID",
            "Version 1 transition graph differs from the fail-closed canonical graph",
        )
    return value


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _require_sha256(value: object, label: str) -> str:
    if not _is_sha256(value):
        raise BoundedCompletionError("IDENTITY_INVALID", f"{label} must be a lowercase SHA-256")
    return str(value)


def _require_nonnegative_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise BoundedCompletionError("MEASUREMENT_INVALID", f"{label} must be a non-negative integer")
    return value


def make_review_protocol_identity(
    *,
    protocol_version: str,
    tool_sha256: str,
    prompt_sha256: str,
    schema_sha256: str,
    reviewer_family: str,
    reviewer_model: str,
) -> dict[str, str]:
    """Build the full review-tooling identity pinned at run start."""

    if not isinstance(protocol_version, str) or not protocol_version:
        raise BoundedCompletionError("PROTOCOL_IDENTITY_INVALID", "protocol_version is required")
    payload = {
        "protocol_version": protocol_version,
        "tool_sha256": _require_sha256(tool_sha256, "tool_sha256"),
        "prompt_sha256": _require_sha256(prompt_sha256, "prompt_sha256"),
        "schema_sha256": _require_sha256(schema_sha256, "schema_sha256"),
        "reviewer_family": reviewer_family,
        "reviewer_model": reviewer_model,
    }
    for field in ("reviewer_family", "reviewer_model"):
        if not isinstance(payload[field], str) or not payload[field].strip():
            raise BoundedCompletionError("PROTOCOL_IDENTITY_INVALID", f"{field} is required")
    return {**payload, "identity_sha256": sha256_json(payload)}


def _validate_protocol_identity(identity: Mapping[str, object]) -> dict[str, str]:
    if set(identity) != {*_PROTOCOL_FIELDS, "identity_sha256"}:
        raise BoundedCompletionError(
            "PROTOCOL_IDENTITY_INVALID",
            "Review protocol identity has missing or unexpected fields",
        )
    rebuilt = make_review_protocol_identity(**{field: identity[field] for field in _PROTOCOL_FIELDS})  # type: ignore[arg-type]
    if rebuilt != dict(identity):
        raise BoundedCompletionError(
            "PROTOCOL_IDENTITY_INVALID",
            "Review protocol identity digest does not match its fields",
        )
    return rebuilt


def _assert_invariants(run: Mapping[str, Any], contract: Mapping[str, Any]) -> None:
    reviews = run["reviews"]
    repairs = run["repairs"]
    measurements = run["measurements"]
    if len(reviews) != measurements["model_call_count"]:
        raise BoundedCompletionError("RUN_INVARIANT", "model_call_count must equal recorded reviews")
    if len(repairs) != measurements["repair_count"]:
        raise BoundedCompletionError("RUN_INVARIANT", "repair_count must equal recorded repairs")
    if len(reviews) > contract["budgets"]["semantic_reviews_total"]:
        raise BoundedCompletionError("RUN_INVARIANT", "Semantic-review budget is exceeded")
    if len(repairs) > contract["budgets"]["consolidated_repairs"]:
        raise BoundedCompletionError("RUN_INVARIANT", "Consolidated-repair budget is exceeded")
    expected_phases = ["INITIAL", "FINAL"][: len(reviews)]
    if [review["phase"] for review in reviews] != expected_phases:
        raise BoundedCompletionError("RUN_INVARIANT", "Review phases must be INITIAL then FINAL")
    current_source = run["learner_source_sha256"]
    for review in reviews:
        if review["valid"] and review["learner_source_sha256"] != current_source:
            raise BoundedCompletionError("RUN_INVARIANT", "Valid review evidence is stale")
    verification = run["deterministic_verification"]
    if verification is not None and verification["passed"] and verification["learner_source_sha256"] != current_source:
        raise BoundedCompletionError("RUN_INVARIANT", "Deterministic evidence is stale")
    publication = run["publication"]
    if publication is not None and publication["learner_source_sha256"] != current_source:
        raise BoundedCompletionError("RUN_INVARIANT", "Publication identity is stale")

    disposition = measurements["final_quality_disposition"]
    state = run["state"]
    terminal = run["terminal"]
    if state == "PUBLICATION" and (publication is None or not terminal or disposition != "PUBLISHABLE"):
        raise BoundedCompletionError("RUN_INVARIANT", "Publication must be terminal and publishable")
    if disposition.startswith("BLOCKED_") and (state != "FINAL_DISPOSITION" or not terminal):
        raise BoundedCompletionError("RUN_INVARIANT", "Blocked disposition must be terminal")
    if disposition == "PUBLISHABLE" and state not in {"FINAL_DISPOSITION", "PUBLICATION"}:
        raise BoundedCompletionError("RUN_INVARIANT", "Publishable disposition is in the wrong state")
    if state == "SEMANTIC_REVIEW" and (verification is None or not verification["passed"]):
        raise BoundedCompletionError("RUN_INVARIANT", "Semantic review requires current deterministic PASS")


def validate_run(
    run: Mapping[str, Any],
    *,
    contract_path: Path = DEFAULT_CONTRACT_PATH,
) -> None:
    """Validate a run against both JSON Schema and cross-field invariants."""

    contract = load_contract(contract_path)
    _validate(run, RUN_SCHEMA_PATH, "bounded-completion run")
    _validate_protocol_identity(run["review_protocol_identity"])
    if run["contract_version"] != contract["contract_version"]:
        raise BoundedCompletionError("CONTRACT_DRIFT", "Run contract version is no longer active")
    _assert_invariants(run, contract)


def start_run(
    *,
    target: str,
    run_id: str,
    review_protocol_identity: Mapping[str, object],
    learner_source_sha256: str | None,
    contract_path: Path = DEFAULT_CONTRACT_PATH,
) -> dict[str, Any]:
    """Create a new run with a frozen review protocol identity."""

    contract = load_contract(contract_path)
    protocol = _validate_protocol_identity(review_protocol_identity)
    if learner_source_sha256 is not None:
        learner_source_sha256 = _require_sha256(learner_source_sha256, "learner_source_sha256")
    run: dict[str, Any] = {
        "schema_version": contract["run_schema_version"],
        "contract_version": contract["contract_version"],
        "run_id": run_id,
        "target": target,
        "state": "INSPECT",
        "terminal": False,
        "review_protocol_identity": protocol,
        "learner_source_sha256": learner_source_sha256,
        "deterministic_verification": None,
        "reviews": [],
        "repairs": [],
        "publication": None,
        "measurements": {
            "elapsed_time_ms": 0,
            "model_call_count": 0,
            "repair_count": 0,
            "prompt_bytes": 0,
            "schema_bytes": 0,
            "final_quality_disposition": "PENDING",
        },
        "history": [],
    }
    validate_run(run, contract_path=contract_path)
    return run


def _copy_run(run: Mapping[str, Any], contract_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    validate_run(run, contract_path=contract_path)
    return deepcopy(dict(run)), load_contract(contract_path)


def _require_state(run: Mapping[str, Any], expected: str) -> None:
    if run["state"] != expected:
        raise BoundedCompletionError(
            "STATE_INVALID",
            f"Expected state {expected}, found {run['state']}",
        )


def _add_elapsed(run: dict[str, Any], elapsed_time_ms: int) -> None:
    run["measurements"]["elapsed_time_ms"] += _require_nonnegative_int(
        elapsed_time_ms,
        "elapsed_time_ms",
    )


def _transition(
    run: dict[str, Any],
    contract: Mapping[str, Any],
    *,
    to_state: str,
    action: str,
    details: Mapping[str, Any] | None = None,
) -> None:
    from_state = run["state"]
    if to_state not in contract["transitions"][from_state]:
        raise BoundedCompletionError(
            "TRANSITION_INVALID",
            f"Contract forbids {from_state} -> {to_state}",
        )
    run["state"] = to_state
    run["history"].append(
        {
            "sequence": len(run["history"]) + 1,
            "action": action,
            "from_state": from_state,
            "to_state": to_state,
            "details": dict(details or {}),
        }
    )


def complete_inspection(
    run: Mapping[str, Any],
    *,
    needs_build: bool,
    elapsed_time_ms: int = 0,
    contract_path: Path = DEFAULT_CONTRACT_PATH,
) -> dict[str, Any]:
    """Record inspection and choose build/rebuild or direct verification."""

    updated, contract = _copy_run(run, contract_path)
    _require_state(updated, "INSPECT")
    if not isinstance(needs_build, bool):
        raise BoundedCompletionError("INPUT_INVALID", "needs_build must be boolean")
    if not needs_build and updated["learner_source_sha256"] is None:
        raise BoundedCompletionError("IDENTITY_INVALID", "A built source identity is required")
    _add_elapsed(updated, elapsed_time_ms)
    _transition(
        updated,
        contract,
        to_state="BUILD_REBUILD" if needs_build else "DETERMINISTIC_VERIFICATION",
        action="inspection_completed",
        details={"needs_build": needs_build},
    )
    validate_run(updated, contract_path=contract_path)
    return updated


def complete_build(
    run: Mapping[str, Any],
    *,
    learner_source_sha256: str,
    elapsed_time_ms: int = 0,
    contract_path: Path = DEFAULT_CONTRACT_PATH,
) -> dict[str, Any]:
    """Record one build or rebuild before semantic evidence exists."""

    updated, contract = _copy_run(run, contract_path)
    _require_state(updated, "BUILD_REBUILD")
    source = _require_sha256(learner_source_sha256, "learner_source_sha256")
    _add_elapsed(updated, elapsed_time_ms)
    updated["learner_source_sha256"] = source
    updated["deterministic_verification"] = None
    _transition(
        updated,
        contract,
        to_state="DETERMINISTIC_VERIFICATION",
        action="build_completed",
        details={"learner_source_sha256": source},
    )
    validate_run(updated, contract_path=contract_path)
    return updated


def record_deterministic_verification(
    run: Mapping[str, Any],
    *,
    learner_source_sha256: str,
    passed: bool,
    elapsed_time_ms: int = 0,
    contract_path: Path = DEFAULT_CONTRACT_PATH,
) -> dict[str, Any]:
    """Bind deterministic evidence to the exact current learner source."""

    updated, contract = _copy_run(run, contract_path)
    _require_state(updated, "DETERMINISTIC_VERIFICATION")
    source = _require_sha256(learner_source_sha256, "learner_source_sha256")
    if source != updated["learner_source_sha256"]:
        raise BoundedCompletionError(
            "LEARNER_SOURCE_DRIFT",
            "Deterministic evidence does not match the active learner source",
        )
    if not isinstance(passed, bool):
        raise BoundedCompletionError("INPUT_INVALID", "passed must be boolean")
    _add_elapsed(updated, elapsed_time_ms)
    updated["deterministic_verification"] = {
        "learner_source_sha256": source,
        "passed": passed,
    }
    if passed:
        next_state = "SEMANTIC_REVIEW"
    else:
        next_state = "FINAL_DISPOSITION"
        updated["terminal"] = True
        updated["measurements"]["final_quality_disposition"] = "BLOCKED_DETERMINISTIC"
    _transition(
        updated,
        contract,
        to_state=next_state,
        action="deterministic_verification_recorded",
        details={"passed": passed, "learner_source_sha256": source},
    )
    validate_run(updated, contract_path=contract_path)
    return updated


def semantic_review_phase(
    run: Mapping[str, Any],
    *,
    review_protocol_identity: Mapping[str, object],
    learner_source_sha256: str,
    contract_path: Path = DEFAULT_CONTRACT_PATH,
) -> str:
    """Fail-closed preflight to run before making a semantic model call."""

    validate_run(run, contract_path=contract_path)
    contract = load_contract(contract_path)
    if len(run["reviews"]) >= contract["budgets"]["semantic_reviews_total"]:
        raise BoundedCompletionError(
            "SEMANTIC_REVIEW_BUDGET_EXHAUSTED",
            "A third semantic review is forbidden",
        )
    _require_state(run, "SEMANTIC_REVIEW")
    observed_protocol = _validate_protocol_identity(review_protocol_identity)
    if observed_protocol != run["review_protocol_identity"]:
        raise BoundedCompletionError(
            "REVIEW_PROTOCOL_DRIFT",
            "Active review tooling differs from the run-start identity",
        )
    source = _require_sha256(learner_source_sha256, "learner_source_sha256")
    if source != run["learner_source_sha256"]:
        raise BoundedCompletionError(
            "LEARNER_SOURCE_DRIFT",
            "Semantic review input differs from the active learner source",
        )
    verification = run["deterministic_verification"]
    if verification is None or not verification["passed"] or verification["learner_source_sha256"] != source:
        raise BoundedCompletionError(
            "DETERMINISTIC_EVIDENCE_STALE",
            "Current deterministic PASS is required before semantic review",
        )
    if not run["reviews"]:
        if run["repairs"]:
            raise BoundedCompletionError("RUN_INVARIANT", "Initial review cannot follow a repair")
        return "INITIAL"
    if len(run["reviews"]) == 1 and len(run["repairs"]) == 1:
        return "FINAL"
    raise BoundedCompletionError(
        "RUN_INVARIANT",
        "Final review requires exactly one initial review and one consolidated repair",
    )


def _normalize_dimension_scores(
    scores: Mapping[str, object],
    contract: Mapping[str, Any],
) -> dict[str, float]:
    dimensions = contract["publication_quality"]["dimensions"]
    if set(scores) != set(dimensions):
        raise BoundedCompletionError(
            "QUALITY_DIMENSIONS_INVALID",
            "Scores must cover exactly the canonical publication dimensions",
        )
    normalized: dict[str, float] = {}
    for dimension in dimensions:
        score = scores[dimension]
        if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 10:
            raise BoundedCompletionError(
                "QUALITY_SCORE_INVALID",
                f"{dimension} must be a number from 0 through 10",
            )
        normalized[dimension] = float(score)
    return normalized


def record_semantic_review(
    run: Mapping[str, Any],
    *,
    review_protocol_identity: Mapping[str, object],
    learner_source_sha256: str,
    evidence_id: str,
    reported_disposition: str,
    dimension_scores: Mapping[str, object],
    prompt_bytes: int,
    schema_bytes: int,
    elapsed_time_ms: int = 0,
    contract_path: Path = DEFAULT_CONTRACT_PATH,
) -> dict[str, Any]:
    """Record one allowed semantic result and apply the 9.0 hard threshold."""

    phase = semantic_review_phase(
        run,
        review_protocol_identity=review_protocol_identity,
        learner_source_sha256=learner_source_sha256,
        contract_path=contract_path,
    )
    updated, contract = _copy_run(run, contract_path)
    if not isinstance(evidence_id, str) or not evidence_id.strip():
        raise BoundedCompletionError("EVIDENCE_INVALID", "evidence_id is required")
    if reported_disposition not in {"PASS", "REVISE", "BLOCK"}:
        raise BoundedCompletionError("DISPOSITION_INVALID", "Unknown semantic disposition")
    scores = _normalize_dimension_scores(dimension_scores, contract)
    minimum = contract["publication_quality"]["minimum_per_dimension"]
    threshold_failures = [
        dimension for dimension in contract["publication_quality"]["dimensions"] if scores[dimension] < minimum
    ]
    contract_disposition = "BLOCK" if reported_disposition == "PASS" and threshold_failures else reported_disposition
    prompt_size = _require_nonnegative_int(prompt_bytes, "prompt_bytes")
    schema_size = _require_nonnegative_int(schema_bytes, "schema_bytes")
    _add_elapsed(updated, elapsed_time_ms)
    updated["measurements"]["model_call_count"] += 1
    updated["measurements"]["prompt_bytes"] += prompt_size
    updated["measurements"]["schema_bytes"] += schema_size
    updated["reviews"].append(
        {
            "phase": phase,
            "evidence_id": evidence_id,
            "review_protocol_identity_sha256": updated["review_protocol_identity"]["identity_sha256"],
            "learner_source_sha256": learner_source_sha256,
            "reported_disposition": reported_disposition,
            "contract_disposition": contract_disposition,
            "dimension_scores": scores,
            "threshold_failures": threshold_failures,
            "valid": True,
            "invalidated_reason": None,
        }
    )

    if contract_disposition == "PASS":
        updated["measurements"]["final_quality_disposition"] = "PUBLISHABLE"
        next_state = "FINAL_DISPOSITION"
    elif phase == "INITIAL":
        next_state = "CONSOLIDATED_REPAIR"
    else:
        updated["measurements"]["final_quality_disposition"] = contract["budget_exhaustion"]["disposition"]
        updated["terminal"] = True
        next_state = "FINAL_DISPOSITION"
    _transition(
        updated,
        contract,
        to_state=next_state,
        action="semantic_review_recorded",
        details={
            "phase": phase,
            "evidence_id": evidence_id,
            "reported_disposition": reported_disposition,
            "contract_disposition": contract_disposition,
            "threshold_failures": threshold_failures,
        },
    )
    validate_run(updated, contract_path=contract_path)
    return updated


def record_consolidated_repair(
    run: Mapping[str, Any],
    *,
    learner_source_sha256: str,
    elapsed_time_ms: int = 0,
    contract_path: Path = DEFAULT_CONTRACT_PATH,
) -> dict[str, Any]:
    """Record the only allowed learner repair and invalidate old evidence."""

    updated, contract = _copy_run(run, contract_path)
    if len(updated["repairs"]) >= contract["budgets"]["consolidated_repairs"]:
        raise BoundedCompletionError(
            "REPAIR_BUDGET_EXHAUSTED",
            "A second consolidated learner repair is forbidden",
        )
    _require_state(updated, "CONSOLIDATED_REPAIR")
    previous_source = updated["learner_source_sha256"]
    if previous_source is None:
        raise BoundedCompletionError("IDENTITY_INVALID", "Repair requires an existing learner source")
    new_source = _require_sha256(learner_source_sha256, "learner_source_sha256")
    if new_source == previous_source:
        raise BoundedCompletionError(
            "NON_MATERIAL_REPAIR",
            "A consolidated learner repair must change the learner-source identity",
        )
    invalidated: list[str] = []
    for review in updated["reviews"]:
        if review["valid"]:
            review["valid"] = False
            review["invalidated_reason"] = "LEARNER_SOURCE_CHANGED"
            invalidated.append(review["evidence_id"])
    if not invalidated:
        raise BoundedCompletionError("RUN_INVARIANT", "Repair must invalidate prior review evidence")
    updated["repairs"].append(
        {
            "source_before_sha256": previous_source,
            "source_after_sha256": new_source,
            "invalidated_evidence_ids": invalidated,
        }
    )
    updated["learner_source_sha256"] = new_source
    updated["deterministic_verification"] = None
    updated["measurements"]["repair_count"] += 1
    _add_elapsed(updated, elapsed_time_ms)
    _transition(
        updated,
        contract,
        to_state="DETERMINISTIC_VERIFICATION",
        action="consolidated_repair_recorded",
        details={
            "source_before_sha256": previous_source,
            "source_after_sha256": new_source,
            "invalidated_evidence_ids": invalidated,
        },
    )
    validate_run(updated, contract_path=contract_path)
    return updated


def record_publication(
    run: Mapping[str, Any],
    *,
    reference: str,
    elapsed_time_ms: int = 0,
    contract_path: Path = DEFAULT_CONTRACT_PATH,
) -> dict[str, Any]:
    """Record publication only after a current publishable disposition."""

    updated, contract = _copy_run(run, contract_path)
    _require_state(updated, "FINAL_DISPOSITION")
    if updated["terminal"] or updated["measurements"]["final_quality_disposition"] != "PUBLISHABLE":
        raise BoundedCompletionError(
            "PUBLICATION_BLOCKED",
            "Only a non-terminal PUBLISHABLE disposition may publish",
        )
    if not isinstance(reference, str) or not reference.strip():
        raise BoundedCompletionError("PUBLICATION_INVALID", "Publication reference is required")
    source = updated["learner_source_sha256"]
    if source is None:
        raise BoundedCompletionError("IDENTITY_INVALID", "Publication requires a learner source")
    _add_elapsed(updated, elapsed_time_ms)
    updated["publication"] = {
        "reference": reference,
        "learner_source_sha256": source,
    }
    updated["terminal"] = True
    _transition(
        updated,
        contract,
        to_state="PUBLICATION",
        action="publication_recorded",
        details={"reference": reference, "learner_source_sha256": source},
    )
    validate_run(updated, contract_path=contract_path)
    return updated


def _fixture_protocol(
    run: Mapping[str, Any],
    override: Mapping[str, object] | None,
) -> dict[str, str]:
    fields = {field: run["review_protocol_identity"][field] for field in _PROTOCOL_FIELDS}
    if override:
        fields.update(override)
    return make_review_protocol_identity(**fields)  # type: ignore[arg-type]


def replay_fixture(
    fixture: Path | Mapping[str, Any],
    *,
    contract_path: Path = DEFAULT_CONTRACT_PATH,
) -> dict[str, Any]:
    """Execute one deterministic regression fixture with fail-closed assertions."""

    value = read_json(fixture) if isinstance(fixture, Path) else deepcopy(dict(fixture))
    if value.get("fixture_version") != "bounded-completion.fixture.v1":
        raise BoundedCompletionError("FIXTURE_INVALID", "Unknown fixture version")
    start = value.get("start")
    steps = value.get("steps")
    if not isinstance(start, dict) or not isinstance(steps, list):
        raise BoundedCompletionError("FIXTURE_INVALID", "Fixture requires start and steps")
    protocol_data = start.get("review_protocol")
    if not isinstance(protocol_data, dict):
        raise BoundedCompletionError("FIXTURE_INVALID", "Fixture review_protocol must be an object")
    run = start_run(
        target=start["target"],
        run_id=start["run_id"],
        review_protocol_identity=make_review_protocol_identity(**protocol_data),
        learner_source_sha256=start.get("learner_source_sha256"),
        contract_path=contract_path,
    )
    expected_errors: list[dict[str, Any]] = []
    for sequence, raw_step in enumerate(steps, start=1):
        if not isinstance(raw_step, dict):
            raise BoundedCompletionError("FIXTURE_INVALID", f"Step {sequence} must be an object")
        step = deepcopy(raw_step)
        action = step.pop("action", None)
        expected_error = step.pop("expect_error", None)
        protocol_override = step.pop("review_protocol_override", None)
        before = deepcopy(run)
        try:
            if action == "complete_inspection":
                candidate = complete_inspection(run, contract_path=contract_path, **step)
            elif action == "complete_build":
                candidate = complete_build(run, contract_path=contract_path, **step)
            elif action == "record_deterministic_verification":
                candidate = record_deterministic_verification(run, contract_path=contract_path, **step)
            elif action == "record_semantic_review":
                candidate = record_semantic_review(
                    run,
                    review_protocol_identity=_fixture_protocol(run, protocol_override),
                    contract_path=contract_path,
                    **step,
                )
            elif action == "record_consolidated_repair":
                candidate = record_consolidated_repair(run, contract_path=contract_path, **step)
            elif action == "record_publication":
                candidate = record_publication(run, contract_path=contract_path, **step)
            else:
                raise BoundedCompletionError("FIXTURE_INVALID", f"Unknown fixture action: {action}")
        except BoundedCompletionError as exc:
            if exc.code != expected_error:
                raise
            if run != before:
                raise BoundedCompletionError(
                    "FAIL_CLOSED_MUTATION",
                    f"Rejected fixture step {sequence} mutated the active run",
                ) from exc
            expected_errors.append({"step": sequence, "code": exc.code, "unchanged": True})
            continue
        if expected_error is not None:
            raise BoundedCompletionError(
                "FIXTURE_EXPECTATION_FAILED",
                f"Step {sequence} expected {expected_error} but succeeded",
            )
        run = candidate
    validate_run(run, contract_path=contract_path)
    return {"run": run, "expected_errors": expected_errors}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate-contract", help="validate the canonical contract and schemas")
    replay = subparsers.add_parser("replay", help="execute one deterministic JSON fixture")
    replay.add_argument("fixture", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for contract validation and fixture replay."""

    args = _build_parser().parse_args(argv)
    if args.command == "validate-contract":
        contract = load_contract()
        Draft202012Validator.check_schema(read_json(RUN_SCHEMA_PATH))
        print(
            json.dumps(
                {
                    "status": "PASS",
                    "contract_version": contract["contract_version"],
                    "run_schema_version": contract["run_schema_version"],
                },
                sort_keys=True,
            )
        )
        return 0
    result = replay_fixture(args.fixture)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
