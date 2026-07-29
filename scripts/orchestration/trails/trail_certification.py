"""Hermetic TrailSpec certification harness.

The harness exercises a supplied matrix against P3's :class:`TrailExecutor`.
Each case gets a fresh SQLite ledger, so its attestation is derived from P3's
authoritative state rather than from receipt projections.  It creates its own
synthetic command runner from fixture data, so certification cannot turn into
a live command, network, or GitHub operation.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from scripts.orchestration.trails.executor import TrailExecutor
from scripts.orchestration.trails.models import (
    CommandExecution,
    ExitClass,
    InjectedCrash,
    TrailRunResult,
)
from scripts.orchestration.trails.store import TrailStore, digest_json
from scripts.orchestration.validate_trailspec import compute_trail_hash, validate_trailspec_data

PROJECT_ROOT = Path(__file__).resolve().parents[3]
CERTIFICATION_ATTESTATION_SCHEMA_PATH = (
    PROJECT_ROOT
    / "agents_extensions/shared/schemas/trail-certification-attestation.v1.schema.json"
)
CERTIFICATION_SCHEMA_VERSION = "trail-certification-attestation.v1"
MINIMUM_PRODUCTION_SAMPLE_SIZE = 59

FAULT_CLASSES = frozenset(
    {
        "stale-lease",
        "duplicate-replayed-receipt",
        "partial-mutation",
        "api-unavailable",
        "conflicting-reviews",
        "unknown-ci",
        "dirty-worktree",
        "interruption-resume",
        "crash-before-spawn",
        "crash-after-spawn",
        "crash-after-side-effect",
    }
)

BINARY_DAMAGE_EVENT_CODES = frozenset(
    {
        "merged-regression",
        "unauthorized-rail-file-edit",
        "self-review-accepted",
        "false-closure",
        "missed-stop",
        "stale-generation-action",
        "review-merge-bypass",
        "replayed-side-effect",
        "wrong-head-rerun",
    }
)

RECERTIFICATION_TRIGGERS = (
    "trailspec-change",
    "decision-table-change",
    "trail-hash-change",
    "runner-change",
    "predicate-change",
    "closure-change",
    "primitive-change",
    "stop-taxonomy-change",
    "authority-lease-change",
    "model-harness-cli-change",
    "github-semantics-change",
    "repeated-repaired-gap",
    "damage-event",
)

_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_GIT_COMMIT = re.compile(r"^[a-f0-9]{40}$")
_OUTPUT_COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_ATTESTATION_VALIDATOR: Draft202012Validator | None = None


class TrailCertificationError(ValueError):
    """Base class for a certification request that cannot be attested."""


class UnsupportedTrailSpecError(TrailCertificationError):
    """Raised before runner construction for an execution-ineligible TrailSpec."""


class HermeticCertificationError(TrailCertificationError):
    """Raised when a purportedly synthetic fixture could escape the harness."""


@dataclass(frozen=True, slots=True)
class CaseExpectation:
    """The transition/STOP contract which one synthetic case must prove."""

    outcome: str
    exit_class: int | None
    state: str | None
    transition: str | None = None
    stop_code: str | None = None


@dataclass(frozen=True, slots=True)
class P3Action:
    """One P3 operation performed after the harness has begun a run."""

    verb: Literal["step", "decision-table", "resume", "close", "verify-chain"]
    expected_step: str | None = None
    table_id: str | None = None
    facts: Mapping[str, Any] | None = None
    authority_receipt_id: str | None = None


@dataclass(frozen=True, slots=True)
class CertificationCase:
    """A synthetic fault/plant and the P3 operations used to observe it."""

    case_id: str
    fault: str
    plant: str
    expected: CaseExpectation
    actions: tuple[P3Action, ...]
    command_execution: CommandExecution
    params: Mapping[str, Any] | None = None
    fault_stage: str | None = None
    damage_event_codes: tuple[str, ...] = ()
    preventable_interventions: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CoverageRequirements:
    """Transitions and STOP codes that the submitted matrix must cover."""

    transitions: tuple[str, ...] = ()
    stop_codes: tuple[str, ...] = ()
    fault_classes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CertificationSubject:
    """Pinned trail/seat/harness identity to bind into an attestation."""

    trail_path: Path
    seat: str
    model: str
    harness: str
    cli_version: str
    tool_isolation_profile: str
    task_family: str = "infra-orchestration"
    decision_table_paths: Mapping[str, Path] | None = None


@dataclass(frozen=True, slots=True)
class HermeticFixture:
    """Filesystem inputs available to a synthetic P3 fixture environment."""

    project_root: Path
    seat_registry_path: Path


@dataclass(frozen=True, slots=True)
class CertificationResult:
    """Schema-validated attestation and its immutable output location."""

    attestation: dict[str, Any]
    attestation_path: Path


def _default_clock() -> datetime:
    return datetime.now(UTC)


def _load_schema_validator() -> Draft202012Validator:
    global _ATTESTATION_VALIDATOR
    if _ATTESTATION_VALIDATOR is None:
        try:
            schema = json.loads(CERTIFICATION_ATTESTATION_SCHEMA_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise TrailCertificationError("certification attestation schema is unavailable") from exc
        _ATTESTATION_VALIDATOR = Draft202012Validator(schema, format_checker=FormatChecker())
    return _ATTESTATION_VALIDATOR


def validate_certification_attestation_data(attestation: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one attestation and enforce hermetic pending-slot invariants."""
    if not isinstance(attestation, Mapping):
        raise TrailCertificationError("certification attestation must be an object")
    payload = dict(attestation)
    errors = sorted(_load_schema_validator().iter_errors(payload), key=lambda error: error.path)
    if errors:
        error = errors[0]
        raise TrailCertificationError(
            f"certification attestation schema violation: {error.message} at {error.json_path}"
        )
    if payload["hermetic"] is True:
        for slot in payload["live_canary_receipts"]:
            if slot["status"] != "pending" or slot["receipt"] is not None:
                raise TrailCertificationError("hermetic certification cannot fabricate a live canary")
        review_slot = payload["independent_review_publication_receipt"]
        if review_slot["status"] != "pending" or review_slot["receipt"] is not None:
            raise TrailCertificationError("hermetic certification cannot fabricate an independent review")
    return payload


def one_sided_95_upper_bound(event_count: int, sample_size: int) -> float:
    """Return the exact one-sided 95% Clopper-Pearson event-rate upper bound.

    The zero-event form is exact and establishes the memo-corrected 59-loop
    threshold.  Nonzero counts use the inverse regularized incomplete beta
    distribution, computed locally so this harness has no optional numerical
    dependency or network boundary.
    """
    if type(event_count) is not int or type(sample_size) is not int:
        raise TrailCertificationError("event_count and sample_size must be integers")
    if sample_size < 1 or event_count < 0 or event_count > sample_size:
        raise TrailCertificationError("event_count must be in [0, sample_size], with sample_size >= 1")
    if event_count == sample_size:
        return 1.0
    if event_count == 0:
        return 1.0 - 0.05 ** (1.0 / sample_size)
    return _inverse_regularized_beta(0.95, event_count + 1.0, sample_size - event_count)


def _beta_continued_fraction(a: float, b: float, x: float) -> float:
    """Evaluate the continued fraction used by the regularized beta function."""
    tiny = 1.0e-300
    c = 1.0
    d = 1.0 - (a + b) * x / (a + 1.0)
    d = tiny if abs(d) < tiny else d
    d = 1.0 / d
    result = d
    for iteration in range(1, 201):
        twice = 2.0 * iteration
        numerator = iteration * (b - iteration) * x / ((a + twice - 1.0) * (a + twice))
        d = 1.0 + numerator * d
        d = tiny if abs(d) < tiny else d
        c = 1.0 + numerator / c
        c = tiny if abs(c) < tiny else c
        d = 1.0 / d
        result *= d * c
        numerator = -(a + iteration) * (a + b + iteration) * x / (
            (a + twice) * (a + twice + 1.0)
        )
        d = 1.0 + numerator * d
        d = tiny if abs(d) < tiny else d
        c = 1.0 + numerator / c
        c = tiny if abs(c) < tiny else c
        d = 1.0 / d
        delta = d * c
        result *= delta
        if abs(delta - 1.0) <= 3.0e-14:
            return result
    raise TrailCertificationError("incomplete beta calculation did not converge")


def _regularized_beta(x: float, a: float, b: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    prefix = (a * math.log(x)) + (b * math.log1p(-x))
    prefix += math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    factor = math.exp(prefix)
    if x < (a + 1.0) / (a + b + 2.0):
        return factor * _beta_continued_fraction(a, b, x) / a
    return 1.0 - factor * _beta_continued_fraction(b, a, 1.0 - x) / b


def _inverse_regularized_beta(probability: float, a: float, b: float) -> float:
    lower = 0.0
    upper = 1.0
    for _ in range(100):
        midpoint = (lower + upper) / 2.0
        if _regularized_beta(midpoint, a, b) < probability:
            lower = midpoint
        else:
            upper = midpoint
    return (lower + upper) / 2.0


def _file_sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise TrailCertificationError(f"cannot hash bound input {path}") from exc


def _read_trail(path: Path, *, seat_registry_path: Path) -> dict[str, Any]:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise TrailCertificationError(f"cannot load certification trail {path}") from exc
    if not isinstance(loaded, dict):
        raise UnsupportedTrailSpecError("certification trail must be a mapping")
    schema_version = loaded.get("schema_version")
    if schema_version == "trailspec.v1":
        raise UnsupportedTrailSpecError(
            "TrailSpec v1 is inspection/hash/projection only; certification execution is refused"
        )
    if schema_version != "trailspec.v1.1":
        raise UnsupportedTrailSpecError(
            f"certification requires trailspec.v1.1, got {schema_version!r}"
        )
    try:
        validate_trailspec_data(loaded, seat_registry_path=seat_registry_path)
    except Exception as exc:
        raise UnsupportedTrailSpecError("certification trail is not a valid trailspec.v1.1") from exc
    return loaded


def _case_chain_digest(store: TrailStore, run_id: str) -> str:
    """Digest only state read back from the case's authoritative SQLite ledger."""
    run = store.get_run(run_id)
    invocations = store.list_invocations(run_id)
    return digest_json(
        {
            "run": {
                "run_id": run.run_id,
                "state": run.state,
                "cursor_step_id": run.cursor_step_id,
                "cursor_generation": run.cursor_generation,
                "parked_stop_code": run.parked_stop_code,
                "terminal_outcome": run.terminal_outcome,
                "closure_state": run.closure_state,
            },
            "invocations": [
                {
                    "invocation_id": row["invocation_id"],
                    "cursor_generation": row["cursor_generation"],
                    "status": row["status"],
                    "command_receipt_digest": row["command_receipt_digest"],
                }
                for row in invocations
            ],
            "summons": store.list_summons(run_id),
            "authority_receipts": store.list_authority_receipts(run_id),
            "closure": store.get_closure(run_id),
        }
    )


def _result_observation(result: TrailRunResult | None, store: TrailStore, run_id: str) -> dict[str, Any]:
    run = store.get_run(run_id)
    data = result.data if result is not None and result.data is not None else {}
    return {
        "transition": data.get("transition"),
        "stop_code": data.get("stop_code", run.parked_stop_code),
        "outcome": result.outcome if result is not None else "injected-crash",
        "exit_class": int(result.exit_class) if result is not None else None,
        "state": result.state if result is not None else run.state,
    }


def _expected_payload(expected: CaseExpectation) -> dict[str, Any]:
    return {
        "transition": expected.transition,
        "stop_code": expected.stop_code,
        "outcome": expected.outcome,
        "exit_class": expected.exit_class,
        "state": expected.state,
    }


def _case_passed(expected: Mapping[str, Any], observed: Mapping[str, Any]) -> bool:
    return all(observed.get(field) == expected.get(field) for field in expected)


def _validate_case(case: CertificationCase) -> None:
    if not _OUTPUT_COMPONENT.fullmatch(case.case_id) or not case.plant:
        raise TrailCertificationError("certification case needs non-empty id, fault, and plant")
    if case.fault not in FAULT_CLASSES:
        raise TrailCertificationError(f"certification case {case.case_id!r} has an unknown fault class")
    if not case.actions:
        raise TrailCertificationError(f"certification case {case.case_id!r} has no P3 actions")
    if not isinstance(case.command_execution, CommandExecution):
        raise HermeticCertificationError("certification case command execution must be synthetic")
    if case.fault_stage not in {None, "after_prepared_before_spawn", "after_command_before_receipt"}:
        raise TrailCertificationError(f"certification case {case.case_id!r} has an unknown P3 fault stage")
    invalid_damage = sorted(set(case.damage_event_codes) - BINARY_DAMAGE_EVENT_CODES)
    if invalid_damage:
        raise TrailCertificationError(
            f"certification case {case.case_id!r} has unknown damage events: {invalid_damage}"
        )
    for action in case.actions:
        if action.verb == "step" and not action.expected_step:
            raise TrailCertificationError("a P3 step action requires expected_step")
        if action.verb == "decision-table" and (
            not action.expected_step or not action.table_id or action.facts is None
        ):
            raise TrailCertificationError("a decision-table action requires step, table_id, and facts")
        if action.verb == "resume" and not action.authority_receipt_id:
            raise TrailCertificationError("a resume action requires authority_receipt_id")


def _execute_action(executor: TrailExecutor, run_id: str, action: P3Action) -> TrailRunResult:
    if action.verb == "step":
        assert action.expected_step is not None
        return executor.step(run_id=run_id, expected_step=action.expected_step)
    if action.verb == "decision-table":
        assert action.expected_step is not None and action.table_id is not None and action.facts is not None
        return executor.evaluate_decision_table(
            run_id=run_id,
            expected_step=action.expected_step,
            table_id=action.table_id,
            facts=dict(action.facts),
        )
    if action.verb == "resume":
        assert action.authority_receipt_id is not None
        return executor.resume(run_id=run_id, authority_receipt_id=action.authority_receipt_id)
    if action.verb == "close":
        return executor.close(run_id=run_id)
    return executor.verify_chain(run_id=run_id)


class TrailCertificationHarness:
    """Run P3 cases hermetically and produce one immutable attestation."""

    def __init__(
        self,
        *,
        output_root: Path,
        runner_commit: str,
        runner_digest: str,
        clock: Callable[[], datetime] = _default_clock,
    ) -> None:
        if not _GIT_COMMIT.fullmatch(runner_commit):
            raise TrailCertificationError("runner_commit must be a lowercase 40-hex commit")
        if not _SHA256.fullmatch(runner_digest):
            raise TrailCertificationError("runner_digest must be a lowercase SHA-256 digest")
        self.output_root = output_root
        self.runner_commit = runner_commit
        self.runner_digest = runner_digest
        self.clock = clock

    def run(
        self,
        *,
        certification_id: str,
        subject: CertificationSubject,
        fixture: HermeticFixture,
        cases: Sequence[CertificationCase],
        coverage: CoverageRequirements | None = None,
    ) -> CertificationResult:
        """Execute a finite synthetic matrix through isolated P3 SQLite ledgers."""
        coverage = coverage or CoverageRequirements()
        if not _OUTPUT_COMPONENT.fullmatch(certification_id):
            raise TrailCertificationError("certification_id must be a safe output path component")
        if not cases:
            raise TrailCertificationError("certification needs at least one synthetic case")
        if len({case.case_id for case in cases}) != len(cases):
            raise TrailCertificationError("certification case IDs must be unique")
        for case in cases:
            _validate_case(case)
        spec = _read_trail(subject.trail_path, seat_registry_path=fixture.seat_registry_path)
        if subject.seat not in spec["seats"]:
            raise TrailCertificationError("certification subject seat is not authorized by the trail")
        if not all(
            isinstance(value, str) and value
            for value in (subject.model, subject.harness, subject.cli_version, subject.tool_isolation_profile)
        ):
            raise TrailCertificationError("subject model, harness, CLI, and isolation profile are required")

        runner_root = self.output_root / certification_id / "cases"
        observations: list[dict[str, Any]] = []
        pinned_trail_hash: str | None = None
        for case in cases:
            case_root = runner_root / case.case_id

            def command_runner(
                command: dict[str, Any],
                cwd: Path,
                *,
                execution: CommandExecution = case.command_execution,
            ) -> CommandExecution:
                if cwd != fixture.project_root:
                    raise HermeticCertificationError("P3 certification command escaped its fixture root")
                if command["adapter"] not in {"shell", "typed-primitive"}:
                    raise HermeticCertificationError("P3 certification command has an unknown adapter")
                return execution

            def fault_hook(
                stage: str,
                prepared: Any,
                *,
                injected_stage: str | None = case.fault_stage,
            ) -> None:
                del prepared
                if stage == injected_stage:
                    raise InjectedCrash(f"synthetic certification fault at {stage}")

            store = TrailStore(case_root / "state.sqlite3", case_root / "receipts")
            executor = TrailExecutor(
                store,
                project_root=fixture.project_root,
                seat_registry_path=fixture.seat_registry_path,
                command_runner=command_runner,
                fault_hook=fault_hook if case.fault_stage is not None else None,
            )
            begun = executor.begin(
                trail_path=subject.trail_path,
                seat=subject.seat,
                task_family=subject.task_family,
                params=dict(case.params or {}),
            )
            if begun.run_id is None:
                raise TrailCertificationError(f"P3 did not return a run ID for {case.case_id!r}")
            pinned = store.get_run(begun.run_id)
            if pinned_trail_hash is None:
                pinned_trail_hash = pinned.trail_hash
            elif pinned_trail_hash != pinned.trail_hash:
                raise TrailCertificationError("P3 cases did not pin one trail hash")
            result: TrailRunResult | None = begun
            try:
                for action in case.actions:
                    result = _execute_action(executor, begun.run_id, action)
            except InjectedCrash:
                result = None
            observed = _result_observation(result, store, begun.run_id)
            expected = _expected_payload(case.expected)
            case_damage = list(case.damage_event_codes)
            if expected["stop_code"] is not None and observed["stop_code"] != expected["stop_code"]:
                case_damage.append("missed-stop")
            case_damage = sorted(set(case_damage))
            observations.append(
                {
                    "case_id": case.case_id,
                    "fault": case.fault,
                    "plant": case.plant,
                    "expected": expected,
                    "observed": observed,
                    "step_chain_digest": _case_chain_digest(store, begun.run_id),
                    "damage_event_codes": case_damage,
                    "preventable_interventions": sorted(set(case.preventable_interventions)),
                    "passed": _case_passed(expected, observed),
                }
            )

        attestation = self._attestation(
            certification_id=certification_id,
            subject=subject,
            spec=spec,
            pinned_trail_hash=pinned_trail_hash,
            observations=observations,
            coverage=coverage,
        )
        validated = validate_certification_attestation_data(attestation)
        path = self._write_attestation(certification_id, validated)
        return CertificationResult(attestation=validated, attestation_path=path)

    def _attestation(
        self,
        *,
        certification_id: str,
        subject: CertificationSubject,
        spec: Mapping[str, Any],
        pinned_trail_hash: str | None,
        observations: Sequence[Mapping[str, Any]],
        coverage: CoverageRequirements,
    ) -> dict[str, Any]:
        observed_transitions = sorted(
            {
                str(case["observed"]["transition"])
                for case in observations
                if case["observed"]["transition"] is not None
            }
        )
        observed_stops = sorted(
            {
                str(case["observed"]["stop_code"])
                for case in observations
                if case["observed"]["stop_code"] is not None
            }
        )
        observed_faults = sorted({str(case["fault"]) for case in observations})
        required_transitions = sorted(set(coverage.transitions))
        required_stops = sorted(set(coverage.stop_codes))
        required_faults = sorted(set(coverage.fault_classes))
        missing_transitions = sorted(set(required_transitions) - set(observed_transitions))
        missing_stops = sorted(set(required_stops) - set(observed_stops))
        missing_faults = sorted(set(required_faults) - set(observed_faults))
        damage_events = sorted(
            {code for case in observations for code in case["damage_event_codes"]}
        )
        interventions = sorted(
            {item for case in observations for item in case["preventable_interventions"]}
        )
        sample_size = len(observations)
        event_count = sum(
            1
            for case in observations
            if case["damage_event_codes"] or case["preventable_interventions"]
        )
        upper_bound = one_sided_95_upper_bound(event_count, sample_size)
        complete_coverage = not (missing_transitions or missing_stops or missing_faults)
        harness_passed = all(case["passed"] for case in observations) and complete_coverage and not damage_events
        live_slots = [
            {"slot": "live-canary-1", "status": "pending", "receipt": None},
            {"slot": "live-canary-2", "status": "pending", "receipt": None},
        ]
        trial_eligible = harness_passed and all(slot["status"] == "clean" for slot in live_slots)
        production_certified = (
            trial_eligible
            and event_count == 0
            and sample_size >= MINIMUM_PRODUCTION_SAMPLE_SIZE
            and upper_bound < 0.05
        )
        observed_cases = [dict(case) for case in observations]
        generated = self.clock()
        if generated.tzinfo is None:
            raise TrailCertificationError("certification clock must return an aware datetime")
        decision_table_hashes = {
            key: _file_sha256(path)
            for key, path in sorted((subject.decision_table_paths or {}).items())
        }
        expected_trail_hash = compute_trail_hash(dict(spec))
        if pinned_trail_hash is None:
            raise TrailCertificationError("P3 did not provide a pinned trail hash")
        if pinned_trail_hash != expected_trail_hash:
            raise TrailCertificationError("P3 SQLite trail hash differs from the submitted TrailSpec")
        return {
            "schema_version": CERTIFICATION_SCHEMA_VERSION,
            "certification_id": certification_id,
            "generated_at": generated.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "hermetic": True,
            "trail": {
                "trail_id": spec["trail_id"],
                "trail_version": spec["version"],
                "trail_hash": pinned_trail_hash,
            },
            "decision_table_hashes": decision_table_hashes,
            "runner": {"commit": self.runner_commit, "digest": self.runner_digest},
            "environment": {
                "seat": subject.seat,
                "model": subject.model,
                "harness": subject.harness,
                "cli_version": subject.cli_version,
                "tool_isolation_profile": subject.tool_isolation_profile,
            },
            "cases": observed_cases,
            "coverage": {
                "required_transitions": required_transitions,
                "observed_transitions": observed_transitions,
                "missing_transitions": missing_transitions,
                "required_stop_codes": required_stops,
                "observed_stop_codes": observed_stops,
                "missing_stop_codes": missing_stops,
                "required_fault_classes": required_faults,
                "observed_fault_classes": observed_faults,
                "missing_fault_classes": missing_faults,
            },
            "damage_event_codes": damage_events,
            "preventable_interventions": interventions,
            "live_canary_receipts": live_slots,
            "sample_size": sample_size,
            "event_count": event_count,
            "one_sided_95_upper_bound": upper_bound,
            "status": {
                "harness_passed": harness_passed,
                "trial_eligible": trial_eligible,
                "production_certified": production_certified,
                "demote": bool(damage_events),
            },
            "recertification_triggers": list(RECERTIFICATION_TRIGGERS),
            "independent_review_publication_receipt": {
                "slot": "independent-review-publication",
                "status": "pending",
                "receipt": None,
            },
        }

    def _write_attestation(self, certification_id: str, attestation: Mapping[str, Any]) -> Path:
        directory = self.output_root / certification_id
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "attestation.json"
        payload = (json.dumps(attestation, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode(
            "utf-8"
        )
        try:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError as exc:
            raise TrailCertificationError(f"certification attestation already exists: {path}") from exc
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
        return path


def load_case_matrix(path: Path) -> list[dict[str, Any]]:
    """Load tests-owned declarative plants without treating it as runner state."""
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise TrailCertificationError(f"cannot load case matrix {path}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != "trail-certification-case-matrix.v1":
        raise TrailCertificationError("case matrix has an unsupported schema_version")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not all(isinstance(case, dict) for case in cases):
        raise TrailCertificationError("case matrix must contain a cases list")
    return [dict(case) for case in cases]


def case_matrix_coverage_gaps(cases: Sequence[Mapping[str, Any]]) -> dict[str, list[str]]:
    """Return mandatory plant/fault omissions for a declarative certification matrix."""
    mandatory_plants = {
        "RB-1": {"ambiguous-queue", "foreign-ownership", "stale-rollover", "foreign-rollover"},
        "RB-2": {"overlap-refusal", "one-retry-maximum", "retry-failure-preserved", "no-force-cleanup"},
        "RB-3": {"self-review", "stale-verdict", "contested-verdict", "draft-ci", "red-ci", "current-head-approval"},
        "RB-4": {"unknown-signature", "ambiguous-signature", "expired-signature", "stale-run-no-rerun", "claimant-race-once"},
        "RB-5": {"missing-receipt", "forged-receipt", "replayed-receipt", "stale-lease-receipt", "late-inbox"},
        "RB-6": {"degradation-summon", "vps-mutation-refused", "private-repo-mutation-refused"},
    }
    present_by_trail: dict[str, set[str]] = {}
    faults: set[str] = set()
    for case in cases:
        trail_id = case.get("trail_id")
        plant = case.get("plant")
        fault = case.get("fault")
        if isinstance(trail_id, str) and isinstance(plant, str):
            present_by_trail.setdefault(trail_id, set()).add(plant)
        if isinstance(fault, str):
            faults.add(fault)
    gaps = {
        trail_id: sorted(required - present_by_trail.get(trail_id, set()))
        for trail_id, required in mandatory_plants.items()
    }
    gaps["faults"] = sorted(FAULT_CLASSES - faults)
    return {name: missing for name, missing in gaps.items() if missing}
