"""Fail-closed TrailSpec v1.1 command executor.

This module owns command execution, never a weak driver.  It persists a UUID
``prepared`` invocation before spawning, evaluates only the resulting immutable
receipt, and uses the SQLite store to make cursor changes and STOP summons
atomic.  It deliberately exposes authority and decision-table protocols without
implementing P4/P2 policy in this package.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

import yaml

from scripts.orchestration.validate_trailspec import (
    TrailSpecValidationError,
    compute_command_receipt_digest,
    compute_trail_hash,
    validate_command_receipt_data,
    validate_step_receipt_data,
    validate_trailspec_data,
)

from .models import (
    AuthorityReceiptUnavailableError,
    CommandExecution,
    DeviationRefusedError,
    ExitClass,
    PreparedInvocation,
    ReceiptChainError,
    TrailRun,
    TrailRunnerError,
    TrailRunResult,
)
from .store import TrailStore, canonical_json, digest_json, utc_now

_OUTCOME_TOKEN = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]*$")
_AUTHORIZATION_REDACTION_PATTERN = re.compile(
    r"(?i)(authorization\s*[:=]\s*(?:bearer\s+)?)\S+"
)
_GITHUB_TOKEN_REDACTION_PATTERN = re.compile(
    r"(?i)\b(github_pat_[A-Za-z0-9_]+|gh[pousr]_[A-Za-z0-9]+)\b"
)
_SECRET_ASSIGNMENT_REDACTION_PATTERN = re.compile(
    r"(?i)((?:[\"'])?\b(?:password|passwd|token|secret|api[_-]?key)\b"
    r"(?:[\"'])?\s*[:=]\s*)(?:\"[^\"\r\n]*\"|'[^'\r\n]*'|[^,\r\n\"']+)"
)
_REDACTION_PATTERNS = (
    _AUTHORIZATION_REDACTION_PATTERN,
    _GITHUB_TOKEN_REDACTION_PATTERN,
    _SECRET_ASSIGNMENT_REDACTION_PATTERN,
)
_MAX_RECEIPT_OUTPUT = 8192


class CommandRunner(Protocol):
    """Injectable command boundary used by deterministic tests and production."""

    def __call__(self, command: dict[str, Any], cwd: Path) -> CommandExecution:
        """Run a fully resolved command without a shell interpolation layer."""


class ReceiptPredicateEvaluator(Protocol):
    """Receipt-only predicate seam; it never executes a command."""

    def matching_labels(
        self, step: dict[str, Any], command_receipt: dict[str, Any]
    ) -> list[str]:
        """Return the labels whose receipt clauses all match."""


class DecisionTableEvaluator(Protocol):
    """P2 seam for typed table predicates; P3 intentionally has no implementation."""

    def evaluate(self, table_id: str, facts: dict[str, Any]) -> str:
        """Evaluate a pinned decision table without launching a command."""


class UnavailableDecisionTableEvaluator:
    """P3's explicit P2 seam: table execution is unavailable until it is wired."""

    def evaluate(self, table_id: str, facts: dict[str, Any]) -> str:
        raise TrailRunnerError(
            f"decision-table predicate '{table_id}' is unavailable until P2/P4 wiring"
        )


class AuthorityReceiptResolver(Protocol):
    """P4-owned approved-source lookup, never a local JSON-file loader."""

    def fetch(self, authority_receipt_id: str, run: TrailRun) -> dict[str, Any]:
        """Re-fetch and validate an authority receipt from an approved source."""


class UnavailableAuthorityReceiptResolver:
    """P3's deliberate fail-closed authority implementation."""

    def fetch(self, authority_receipt_id: str, run: TrailRun) -> dict[str, Any]:
        raise AuthorityReceiptUnavailableError(
            "authority receipt verification is unavailable until P4; local receipt files are refused"
        )


class DefaultReceiptPredicateEvaluator:
    """Evaluate the v1.1 schema's simple command-receipt equality clauses."""

    def matching_labels(
        self, step: dict[str, Any], command_receipt: dict[str, Any]
    ) -> list[str]:
        matches: list[str] = []
        for label, transition in step["transitions"].items():
            clauses = transition["evidence"]["clauses"]
            if all(
                clause["source"] == "command_receipt"
                and command_receipt.get(clause["field"]) == clause["value"]
                for clause in clauses
            ):
                matches.append(label)
        return matches


def redact_and_bound_output(value: str, *, limit: int = _MAX_RECEIPT_OUTPUT) -> str:
    """Redact credential-shaped output before producing a bounded receipt digest."""
    redacted = value
    for pattern in _REDACTION_PATTERNS:
        if (
            pattern is _AUTHORIZATION_REDACTION_PATTERN
            or pattern is _SECRET_ASSIGNMENT_REDACTION_PATTERN
        ):
            redacted = pattern.sub(r"\1[REDACTED]", redacted)
        else:
            redacted = pattern.sub("[REDACTED]", redacted)
    if len(redacted) > limit:
        return redacted[:limit] + "[TRUNCATED]"
    return redacted


def _output_digest(value: str) -> str:
    return hashlib.sha256(redact_and_bound_output(value).encode("utf-8")).hexdigest()


def _text_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def subprocess_command_runner(command: dict[str, Any], cwd: Path) -> CommandExecution:
    """Execute a pre-resolved argv command with a timeout and no shell."""
    environment = os.environ.copy()
    environment.update(command["environment"])
    try:
        completed = subprocess.run(
            command["argv"],
            cwd=cwd,
            env=environment,
            check=False,
            text=True,
            capture_output=True,
            timeout=command["timeout_seconds"],
        )
    except subprocess.TimeoutExpired as exc:
        return CommandExecution(
            exit_code=124,
            stdout=_text_output(exc.stdout),
            stderr=_text_output(exc.stderr),
            timed_out=True,
        )
    except OSError as exc:
        return CommandExecution(exit_code=127, stdout="", stderr=str(exc))
    return CommandExecution(
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _decode_stdout_token(execution: CommandExecution) -> str:
    if execution.timed_out:
        return "timeout"
    token = execution.stdout.strip()
    if _OUTCOME_TOKEN.fullmatch(token):
        return token
    return "unparseable-output"


class TrailExecutor:
    """Implement the P3 run lifecycle over one ``TrailStore``."""

    def __init__(
        self,
        store: TrailStore,
        *,
        project_root: Path,
        seat_registry_path: Path | None = None,
        command_runner: CommandRunner = subprocess_command_runner,
        predicate_evaluator: ReceiptPredicateEvaluator | None = None,
        decision_table_evaluator: DecisionTableEvaluator | None = None,
        authority_resolver: AuthorityReceiptResolver | None = None,
        fault_hook: Callable[[str, PreparedInvocation], None] | None = None,
    ) -> None:
        self.store = store
        self.project_root = project_root
        self.seat_registry_path = seat_registry_path
        self.command_runner = command_runner
        self.predicate_evaluator = predicate_evaluator or DefaultReceiptPredicateEvaluator()
        self.decision_table_evaluator = (
            decision_table_evaluator or UnavailableDecisionTableEvaluator()
        )
        self.authority_resolver = authority_resolver or UnavailableAuthorityReceiptResolver()
        self.fault_hook = fault_hook

    @staticmethod
    def _load_trail(path: Path) -> dict[str, Any]:
        try:
            loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            raise TrailRunnerError(f"cannot load trail '{path}': {exc}") from exc
        if not isinstance(loaded, dict):
            raise TrailRunnerError(f"trail '{path}' must contain a YAML object")
        return loaded

    @staticmethod
    def _validate_params(spec: dict[str, Any], params: dict[str, Any]) -> None:
        declared = spec.get("parameters", {})
        if not isinstance(declared, dict):
            raise TrailRunnerError("trail parameters must be an object")
        unknown = sorted(set(params) - set(declared))
        missing = sorted(set(declared) - set(params))
        if unknown or missing:
            raise TrailRunnerError(
                f"parameters do not exactly match TrailSpec: missing={missing}, unknown={unknown}"
            )
        for name, kind in declared.items():
            value = params[name]
            valid = (
                (kind == "string" and isinstance(value, str))
                or (kind == "integer" and isinstance(value, int) and not isinstance(value, bool))
                or (
                    kind == "number"
                    and isinstance(value, (int, float))
                    and not isinstance(value, bool)
                )
                or (kind == "boolean" and isinstance(value, bool))
            )
            if not valid:
                raise TrailRunnerError(
                    f"parameter '{name}' must be a TrailSpec {kind}, got {type(value).__name__}"
                )

    def begin(
        self,
        *,
        trail_path: Path,
        seat: str,
        task_family: str,
        params: dict[str, Any],
    ) -> TrailRunResult:
        """Pin a validated trail in SQLite; v1 starts an inspection-only run."""
        spec = self._load_trail(trail_path)
        try:
            summary = validate_trailspec_data(
                spec,
                **(
                    {"seat_registry_path": self.seat_registry_path}
                    if self.seat_registry_path is not None
                    else {}
                ),
            )
        except TrailSpecValidationError as exc:
            raise TrailRunnerError(str(exc)) from exc
        if seat not in spec["seats"]:
            raise TrailRunnerError(f"seat '{seat}' is not authorized by trail '{spec['trail_id']}'")
        if not isinstance(task_family, str) or not task_family:
            raise TrailRunnerError("task_family must be a non-empty string")
        if not isinstance(params, dict):
            raise TrailRunnerError("params must be a JSON object")
        if spec["schema_version"] == "trailspec.v1.1":
            self._validate_params(spec, params)
        elif params:
            raise TrailRunnerError("TrailSpec v1 supports inspection only and has no typed params")

        run = self.store.create_run(
            run_id=str(uuid.uuid4()),
            spec=spec,
            trail_hash=summary["trail_hash"],
            seat=seat,
            task_family=task_family,
            params=params,
            inspection_only=not summary["execution_eligible"],
        )
        self.store.project_json(
            run_id=run.run_id,
            filename="run.json",
            payload={
                "schema_version": "trail-run-pinned.v1",
                "run_id": run.run_id,
                "trail_id": run.trail_id,
                "trail_version": run.trail_version,
                "trail_hash": run.trail_hash,
                "seat": run.seat,
                "task_family": run.task_family,
                "params": run.params,
                "created_at": run.created_at,
            },
        )
        outcome = "inspection_started" if run.state == "inspection" else "begun"
        return TrailRunResult(
            command="begin",
            exit_class=ExitClass.OK,
            outcome=outcome,
            run_id=run.run_id,
            state=run.state,
            cursor_step=run.cursor_step_id,
            data={
                "trail_id": run.trail_id,
                "trail_version": run.trail_version,
                "trail_hash": run.trail_hash,
                "execution_eligible": spec["schema_version"] == "trailspec.v1.1",
            },
        )

    def status(self, *, run_id: str) -> TrailRunResult:
        """Report SQLite-authoritative cursor and parking state."""
        run = self.store.get_run(run_id)
        return TrailRunResult(
            command="status",
            exit_class=ExitClass.OK,
            outcome="status",
            run_id=run.run_id,
            state=run.state,
            cursor_step=run.cursor_step_id,
            data={
                "trail_id": run.trail_id,
                "trail_hash": run.trail_hash,
                "cursor_generation": run.cursor_generation,
                "parked_stop_code": run.parked_stop_code,
                "parked_reason": run.parked_reason,
                "terminal_outcome": run.terminal_outcome,
                "closure_state": run.closure_state,
                "summons": self.store.list_summons(run_id),
            },
        )

    def _reject_v1_execution(self, command: str, run: TrailRun) -> TrailRunResult:
        return TrailRunResult(
            command=command,
            exit_class=ExitClass.INVALID,
            outcome="execution_ineligible",
            run_id=run.run_id,
            state=run.state,
            cursor_step=run.cursor_step_id,
            error="TrailSpec v1 is inspection/hash/projection only; execution and closure are refused",
        )

    @staticmethod
    def _find_step(run: TrailRun, step_id: str) -> dict[str, Any]:
        for step in run.spec["steps"]:
            if step["step_id"] == step_id:
                return step
        raise ReceiptChainError(f"pinned trail has no step '{step_id}'")

    @staticmethod
    def _resolve_string(value: str, replacements: dict[str, str]) -> str:
        resolved = value
        for name, replacement in replacements.items():
            resolved = resolved.replace("{" + name + "}", replacement)
        if re.search(r"\{[A-Za-z_][A-Za-z0-9_]*\}", resolved):
            raise TrailRunnerError(f"unresolved command placeholder in {value!r}")
        return resolved

    def _resolve_command(
        self, *, run: TrailRun, step: dict[str, Any], invocation_id: str
    ) -> dict[str, Any]:
        command = step["command"]
        replacements = {
            **{name: str(value) for name, value in run.params.items()},
            "invocation_id": invocation_id,
        }
        return {
            "adapter": command["adapter"],
            "argv": [self._resolve_string(value, replacements) for value in command["argv"]],
            "environment": {
                key: self._resolve_string(value, replacements)
                for key, value in command["environment"].items()
            },
            "timeout_seconds": command["timeout_seconds"],
            "mutation_class": command["mutation_class"],
            "outcome_decoder": command["outcome_decoder"],
        }

    @staticmethod
    def _idempotency_key(run: TrailRun, expected_step: str) -> str:
        return digest_json(
            {
                "run_id": run.run_id,
                "cursor_generation": run.cursor_generation,
                "step_id": expected_step,
            }
        )

    def _make_command_receipt(
        self,
        *,
        run: TrailRun,
        prepared: PreparedInvocation,
        execution: CommandExecution,
        actor_outcome: str,
    ) -> dict[str, Any]:
        return {
            "schema_version": "command-receipt.v1",
            "invocation_id": prepared.invocation_id,
            "run_id": run.run_id,
            "trail_id": run.trail_id,
            "trail_version": run.trail_version,
            "trail_hash": run.trail_hash,
            "step_id": prepared.step_id,
            "resolved_command_digest": digest_json(prepared.resolved_command),
            "actor_outcome": actor_outcome,
            "exit_code": execution.exit_code,
            "stdout_digest": _output_digest(execution.stdout),
            "stderr_digest": _output_digest(execution.stderr),
            "artifact_digests": {},
            "prepared_at": prepared.prepared_at,
            "completed_at": utc_now(),
            "status": "complete",
        }

    @staticmethod
    def _step_receipt(
        *,
        run: TrailRun,
        prepared: PreparedInvocation,
        command_receipt: dict[str, Any],
        label: str,
        transition: dict[str, Any],
    ) -> dict[str, Any]:
        evidence = transition["evidence"]
        return {
            "schema_version": "step-receipt.v1.1",
            "trail_id": run.trail_id,
            "trail_version": run.trail_version,
            "trail_hash": run.trail_hash,
            "run_id": run.run_id,
            "step_id": prepared.step_id,
            "task_family": run.task_family,
            "lineage_id": None,
            "pr_head": None,
            "lease_generation": None,
            "predicate_exit": command_receipt["exit_code"],
            "evidence_digest": digest_json(evidence),
            "transition_taken": label,
            "timestamp": utc_now(),
            "idempotency_key": prepared.idempotency_key,
            "invocation_id": prepared.invocation_id,
            "command_receipt_digest": compute_command_receipt_digest(command_receipt),
            "actor_outcome": command_receipt["actor_outcome"],
            "predicate_id": evidence["predicate_id"],
        }

    def _project_completed_receipts(
        self,
        *,
        prepared: PreparedInvocation,
        command_receipt: dict[str, Any],
        step_receipt: dict[str, Any] | None,
    ) -> None:
        prefix = f"{prepared.cursor_generation:06d}-{prepared.invocation_id}"
        self.store.project_json(
            run_id=prepared.run_id,
            filename=f"command-{prefix}.json",
            payload=command_receipt,
        )
        if step_receipt is not None:
            self.store.project_json(
                run_id=prepared.run_id,
                filename=f"step-{prefix}.json",
                payload=step_receipt,
            )

    def _complete_or_return_indeterminate(
        self, **kwargs: Any
    ) -> TrailRun | TrailRunResult:
        """Never report a post-spawn cursor race as a generic runner failure.

        A concurrent claimant can park and mark this invocation indeterminate
        after the parent-owned process has already spawned.  The original
        process must then also return exit 24; it may not project a receipt or
        claim that its possible side effect completed a transition.
        """
        try:
            return self.store.complete_invocation(**kwargs)
        except ReceiptChainError as exc:
            run_id = kwargs["prepared"].run_id
            latest = self.store.get_run(run_id)
            if latest.state == "parked" and latest.parked_stop_code == "STOP-unknown":
                return TrailRunResult(
                    command="step",
                    exit_class=ExitClass.INDETERMINATE,
                    outcome="indeterminate_parked",
                    run_id=run_id,
                    state=latest.state,
                    cursor_step=latest.cursor_step_id,
                    data={"stop_code": latest.parked_stop_code},
                    error=latest.parked_reason or str(exc),
                )
            raise

    def step(
        self,
        *,
        run_id: str,
        expected_step: str,
        idempotency_key: str | None = None,
    ) -> TrailRunResult:
        """Execute exactly the current step once, or fail closed without movement."""
        run = self.store.get_run(run_id)
        if run.spec["schema_version"] != "trailspec.v1.1":
            return self._reject_v1_execution("step", run)

        if idempotency_key is not None:
            prepared_key = idempotency_key
        else:
            if run.state != "active" or run.cursor_step_id != expected_step:
                return TrailRunResult(
                    command="step",
                    exit_class=ExitClass.DEVIATION_REFUSED,
                    outcome="deviation_refused",
                    run_id=run.run_id,
                    state=run.state,
                    cursor_step=run.cursor_step_id,
                    error=(
                        f"step must equal exact current cursor '{run.cursor_step_id}', "
                        f"got '{expected_step}'"
                    ),
                )
            prepared_key = self._idempotency_key(run, expected_step)

        if run.state == "active" and run.cursor_step_id == expected_step:
            current_step = self._find_step(run, expected_step)
            blocked_on = current_step.get("blocked_on")
            if blocked_on is not None:
                parked = self.store.park_blocked(
                    run_id=run_id,
                    expected_step=expected_step,
                    stop_code=blocked_on["stop_code"],
                    reason=blocked_on["reason"],
                    blocked_id=blocked_on["id"],
                )
                return TrailRunResult(
                    command="step",
                    exit_class=ExitClass.BLOCKED_PARKED,
                    outcome="blocked_parked",
                    run_id=run_id,
                    state=parked.state,
                    cursor_step=parked.cursor_step_id,
                    data={"blocked_on": blocked_on, "stop_code": parked.parked_stop_code},
                )
        elif idempotency_key is None:
            # The earlier guard makes this branch defensive should this method be
            # refactored; it maintains the exact-cursor refusal contract.
            return TrailRunResult(
                command="step",
                exit_class=ExitClass.DEVIATION_REFUSED,
                outcome="deviation_refused",
                run_id=run.run_id,
                state=run.state,
                cursor_step=run.cursor_step_id,
                error="step does not name the current active cursor",
            )
        else:
            current_step = self._find_step(run, expected_step)

        invocation_id = str(uuid.uuid4())
        resolved_command = self._resolve_command(
            run=run, step=current_step, invocation_id=invocation_id
        )
        try:
            preparation, value = self.store.prepare_invocation(
                run_id=run_id,
                expected_step=expected_step,
                idempotency_key=prepared_key,
                invocation_id=invocation_id,
                resolved_command=resolved_command,
            )
        except DeviationRefusedError as exc:
            latest = self.store.get_run(run_id)
            return TrailRunResult(
                command="step",
                exit_class=ExitClass.DEVIATION_REFUSED,
                outcome="deviation_refused",
                run_id=run_id,
                state=latest.state,
                cursor_step=latest.cursor_step_id,
                error=str(exc),
            )
        if preparation == "replay":
            stored = TrailRunResult.from_dict(value)  # type: ignore[arg-type]
            return stored
        if preparation == "indeterminate":
            parked = value
            assert isinstance(parked, TrailRun)
            return TrailRunResult(
                command="step",
                exit_class=ExitClass.INDETERMINATE,
                outcome="indeterminate_parked",
                run_id=run_id,
                state=parked.state,
                cursor_step=parked.cursor_step_id,
                data={"stop_code": parked.parked_stop_code},
                error=parked.parked_reason,
            )
        prepared = value
        assert isinstance(prepared, PreparedInvocation)
        if self.fault_hook is not None:
            self.fault_hook("after_prepared_before_spawn", prepared)
        execution = self.command_runner(resolved_command, self.project_root)
        if self.fault_hook is not None:
            self.fault_hook("after_command_before_receipt", prepared)

        decoder = resolved_command["outcome_decoder"]
        actor_outcome = (
            _decode_stdout_token(execution)
            if decoder["source"] == "stdout-token"
            else "artifact-decoder-unavailable"
        )
        command_receipt = self._make_command_receipt(
            run=run,
            prepared=prepared,
            execution=execution,
            actor_outcome=actor_outcome,
        )
        try:
            validate_command_receipt_data(command_receipt)
        except TrailSpecValidationError as exc:
            raise ReceiptChainError(str(exc)) from exc

        matches = self.predicate_evaluator.matching_labels(current_step, command_receipt)
        if len(matches) != 1:
            reason = (
                "receipt predicates matched no transition"
                if not matches
                else f"receipt predicates matched multiple transitions: {matches}"
            )
            result = TrailRunResult(
                command="step",
                exit_class=ExitClass.STOP_PARKED,
                outcome="stop_unknown",
                run_id=run_id,
                state="parked",
                cursor_step=expected_step,
                data={"matched_predicates": matches, "stop_code": "STOP-unknown"},
                error=reason,
            )
            parked = self._complete_or_return_indeterminate(
                prepared=prepared,
                command_receipt=command_receipt,
                step_receipt=None,
                result=result.to_dict(),
                next_state="parked",
                next_cursor_step=expected_step,
                parked_stop_code="STOP-unknown",
                parked_reason=reason,
                summon_state="stop",
            )
            if isinstance(parked, TrailRunResult):
                return parked
            self._project_completed_receipts(
                prepared=prepared, command_receipt=command_receipt, step_receipt=None
            )
            return TrailRunResult(
                command="step",
                exit_class=ExitClass.STOP_PARKED,
                outcome="stop_unknown",
                run_id=run_id,
                state=parked.state,
                cursor_step=parked.cursor_step_id,
                data={"matched_predicates": matches, "stop_code": parked.parked_stop_code},
                error=reason,
            )

        label = matches[0]
        transition = current_step["transitions"][label]
        step_receipt = self._step_receipt(
            run=run,
            prepared=prepared,
            command_receipt=command_receipt,
            label=label,
            transition=transition,
        )
        try:
            validate_step_receipt_data(step_receipt)
        except TrailSpecValidationError as exc:
            raise ReceiptChainError(str(exc)) from exc

        target = transition["target"]
        if target.startswith("STOP-"):
            result = TrailRunResult(
                command="step",
                exit_class=ExitClass.STOP_PARKED,
                outcome="stop_parked",
                run_id=run_id,
                state="parked",
                cursor_step=expected_step,
                data={"transition": label, "stop_code": target},
            )
            parked = self._complete_or_return_indeterminate(
                prepared=prepared,
                command_receipt=command_receipt,
                step_receipt=step_receipt,
                result=result.to_dict(),
                next_state="parked",
                next_cursor_step=expected_step,
                parked_stop_code=target,
                parked_reason=f"transition '{label}' selected {target}",
                summon_state="stop",
            )
            if isinstance(parked, TrailRunResult):
                return parked
            self._project_completed_receipts(
                prepared=prepared,
                command_receipt=command_receipt,
                step_receipt=step_receipt,
            )
            return TrailRunResult(
                command="step",
                exit_class=ExitClass.STOP_PARKED,
                outcome="stop_parked",
                run_id=run_id,
                state=parked.state,
                cursor_step=parked.cursor_step_id,
                data={"transition": label, "stop_code": parked.parked_stop_code},
            )

        if target in run.spec["terminal_outcomes"]:
            result = TrailRunResult(
                command="step",
                exit_class=ExitClass.OK,
                outcome="terminal",
                run_id=run_id,
                state="terminal",
                cursor_step=None,
                data={"transition": label, "terminal_outcome": target},
            )
            terminal = self._complete_or_return_indeterminate(
                prepared=prepared,
                command_receipt=command_receipt,
                step_receipt=step_receipt,
                result=result.to_dict(),
                next_state="terminal",
                next_cursor_step=None,
                terminal_outcome=target,
            )
            if isinstance(terminal, TrailRunResult):
                return terminal
            self._project_completed_receipts(
                prepared=prepared,
                command_receipt=command_receipt,
                step_receipt=step_receipt,
            )
            return TrailRunResult(
                command="step",
                exit_class=ExitClass.OK,
                outcome="terminal",
                run_id=run_id,
                state=terminal.state,
                cursor_step=terminal.cursor_step_id,
                data={"transition": label, "terminal_outcome": terminal.terminal_outcome},
            )

        result = TrailRunResult(
            command="step",
            exit_class=ExitClass.OK,
            outcome="advanced",
            run_id=run_id,
            state="active",
            cursor_step=target,
            data={"transition": label, "next_step": target},
        )
        advanced = self._complete_or_return_indeterminate(
            prepared=prepared,
            command_receipt=command_receipt,
            step_receipt=step_receipt,
            result=result.to_dict(),
            next_state="active",
            next_cursor_step=target,
        )
        if isinstance(advanced, TrailRunResult):
            return advanced
        self._project_completed_receipts(
            prepared=prepared,
            command_receipt=command_receipt,
            step_receipt=step_receipt,
        )
        return TrailRunResult(
            command="step",
            exit_class=ExitClass.OK,
            outcome="advanced",
            run_id=run_id,
            state=advanced.state,
            cursor_step=advanced.cursor_step_id,
            data={"transition": label, "next_step": advanced.cursor_step_id},
        )

    def resume(self, *, run_id: str, authority_receipt_id: str) -> TrailRunResult:
        """Refuse unverified local approvals until P4 supplies approved-source verification."""
        run = self.store.get_run(run_id)
        if run.spec["schema_version"] != "trailspec.v1.1":
            return self._reject_v1_execution("resume", run)
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,255}", authority_receipt_id):
            return TrailRunResult(
                command="resume",
                exit_class=ExitClass.INVALID,
                outcome="authority_receipt_refused",
                run_id=run_id,
                state=run.state,
                cursor_step=run.cursor_step_id,
                error="authority receipt must be an opaque approved-source identifier, not a path",
            )
        try:
            self.authority_resolver.fetch(authority_receipt_id, run)
        except AuthorityReceiptUnavailableError as exc:
            return TrailRunResult(
                command="resume",
                exit_class=ExitClass.INVALID,
                outcome="authority_unavailable",
                run_id=run_id,
                state=run.state,
                cursor_step=run.cursor_step_id,
                error=str(exc),
            )
        return TrailRunResult(
            command="resume",
            exit_class=ExitClass.INVALID,
            outcome="authority_resume_unimplemented",
            run_id=run_id,
            state=run.state,
            cursor_step=run.cursor_step_id,
            error="P4 must bind the approved authority receipt before a parked run can resume",
        )

    def _projection_payload(self, *, run_id: str, filename: str) -> dict[str, Any]:
        path = self.store.projection_path(run_id=run_id, filename=filename)
        try:
            raw = path.read_bytes()
            payload = json.loads(raw)
        except (OSError, json.JSONDecodeError) as exc:
            raise ReceiptChainError(f"missing or invalid receipt projection {path}: {exc}") from exc
        expected = (canonical_json(payload) + "\n").encode("utf-8")
        if raw != expected:
            raise ReceiptChainError(f"receipt projection is not immutable canonical JSON: {path}")
        if not isinstance(payload, dict):
            raise ReceiptChainError(f"receipt projection is not an object: {path}")
        return payload

    def _verify_chain(self, run: TrailRun) -> dict[str, Any]:
        pinned = self._projection_payload(run_id=run.run_id, filename="run.json")
        if (
            pinned.get("run_id") != run.run_id
            or pinned.get("trail_hash") != run.trail_hash
            or pinned.get("trail_id") != run.trail_id
        ):
            raise ReceiptChainError("pinned run projection does not bind the SQLite run")
        if compute_trail_hash(run.spec) != run.trail_hash:
            raise ReceiptChainError("pinned TrailSpec hash does not match SQLite run")
        invocations = self.store.list_invocations(run.run_id)
        if run.spec["schema_version"] == "trailspec.v1":
            if invocations:
                raise ReceiptChainError("TrailSpec v1 inspection run unexpectedly has invocations")
            return {"inspection_only": True, "invocations": 0}

        current_step = run.spec["steps"][0]["step_id"]
        saw_terminal = False
        saw_stop = False
        for expected_generation, invocation in enumerate(invocations):
            if invocation["cursor_generation"] != expected_generation:
                raise ReceiptChainError("invocation cursor generations are not contiguous")
            if invocation["step_id"] != current_step:
                raise ReceiptChainError(
                    f"receipt chain expected step '{current_step}', found '{invocation['step_id']}'"
                )
            if invocation["status"] != "complete" or invocation["command_receipt"] is None:
                raise ReceiptChainError(
                    f"invocation '{invocation['invocation_id']}' lacks a complete command receipt"
                )
            command_receipt = invocation["command_receipt"]
            try:
                validate_command_receipt_data(command_receipt)
            except TrailSpecValidationError as exc:
                raise ReceiptChainError(str(exc)) from exc
            if digest_json(command_receipt) != invocation["command_receipt_digest"]:
                raise ReceiptChainError("SQLite command receipt digest does not match payload")
            prefix = f"{expected_generation:06d}-{invocation['invocation_id']}"
            if self._projection_payload(
                run_id=run.run_id, filename=f"command-{prefix}.json"
            ) != command_receipt:
                raise ReceiptChainError("command receipt projection differs from SQLite authority")
            expected_values = {
                "run_id": run.run_id,
                "trail_id": run.trail_id,
                "trail_version": run.trail_version,
                "trail_hash": run.trail_hash,
                "step_id": current_step,
                "invocation_id": invocation["invocation_id"],
                "resolved_command_digest": invocation["resolved_command_digest"],
            }
            for field, expected in expected_values.items():
                if command_receipt.get(field) != expected:
                    raise ReceiptChainError(
                        f"command receipt {field} does not bind its pinned invocation"
                    )

            step_receipt = self.store.get_step_receipt(invocation["invocation_id"])
            if step_receipt is None:
                if (
                    expected_generation == len(invocations) - 1
                    and run.state == "parked"
                    and run.parked_stop_code == "STOP-unknown"
                ):
                    saw_stop = True
                    continue
                raise ReceiptChainError("complete command receipt lacks its StepReceipt")
            try:
                validate_step_receipt_data(step_receipt)
            except TrailSpecValidationError as exc:
                raise ReceiptChainError(str(exc)) from exc
            if self._projection_payload(run_id=run.run_id, filename=f"step-{prefix}.json") != step_receipt:
                raise ReceiptChainError("step receipt projection differs from SQLite authority")
            step = self._find_step(run, current_step)
            matches = self.predicate_evaluator.matching_labels(step, command_receipt)
            if len(matches) != 1:
                raise ReceiptChainError("stored StepReceipt has zero or multiple matching predicates")
            label = matches[0]
            transition = step["transitions"][label]
            if (
                step_receipt.get("transition_taken") != label
                or step_receipt.get("predicate_id") != transition["evidence"]["predicate_id"]
                or step_receipt.get("command_receipt_digest")
                != compute_command_receipt_digest(command_receipt)
                or step_receipt.get("actor_outcome") != command_receipt["actor_outcome"]
                or step_receipt.get("idempotency_key") != invocation["idempotency_key"]
            ):
                raise ReceiptChainError("StepReceipt does not bind its matching command receipt")
            expected_step_values = {
                "trail_id": run.trail_id,
                "trail_version": run.trail_version,
                "trail_hash": run.trail_hash,
                "run_id": run.run_id,
                "step_id": current_step,
                "task_family": run.task_family,
                "invocation_id": invocation["invocation_id"],
                "predicate_exit": command_receipt["exit_code"],
                "evidence_digest": digest_json(transition["evidence"]),
            }
            for field, expected in expected_step_values.items():
                if step_receipt.get(field) != expected:
                    raise ReceiptChainError(
                        f"StepReceipt {field} does not bind its pinned invocation"
                    )
            target = transition["target"]
            if target.startswith("STOP-"):
                if expected_generation != len(invocations) - 1 or run.state != "parked":
                    raise ReceiptChainError("STOP transition did not terminally park the run")
                if run.parked_stop_code != target:
                    raise ReceiptChainError("run STOP code differs from its StepReceipt transition")
                saw_stop = True
                continue
            if target in run.spec["terminal_outcomes"]:
                if expected_generation != len(invocations) - 1 or run.state != "terminal":
                    raise ReceiptChainError("terminal transition did not terminally complete the run")
                if run.terminal_outcome != target:
                    raise ReceiptChainError("terminal outcome differs from its StepReceipt transition")
                saw_terminal = True
                continue
            current_step = target

        if run.state == "active" and run.cursor_step_id != current_step:
            raise ReceiptChainError("active run cursor does not follow its receipt chain")
        if run.state == "terminal" and not saw_terminal:
            raise ReceiptChainError("terminal run has no terminal StepReceipt")
        if run.state == "parked" and not saw_stop and invocations:
            parked_step = (
                self._find_step(run, run.cursor_step_id)
                if run.cursor_step_id is not None
                else None
            )
            if parked_step is None or parked_step.get("blocked_on") is None:
                raise ReceiptChainError("parked run has no STOP/unknown receipt evidence")
        return {
            "inspection_only": False,
            "invocations": len(invocations),
            "terminal": saw_terminal,
            "parked": run.state == "parked",
        }

    def verify_chain(self, *, run_id: str) -> TrailRunResult:
        """Prove the pinned SQLite and immutable-projection receipt chain matches."""
        run = self.store.get_run(run_id)
        try:
            details = self._verify_chain(run)
        except ReceiptChainError as exc:
            return TrailRunResult(
                command="verify-chain",
                exit_class=ExitClass.INVALID,
                outcome="chain_invalid",
                run_id=run_id,
                state=run.state,
                cursor_step=run.cursor_step_id,
                error=str(exc),
            )
        return TrailRunResult(
            command="verify-chain",
            exit_class=ExitClass.OK,
            outcome="chain_verified",
            run_id=run_id,
            state=run.state,
            cursor_step=run.cursor_step_id,
            data=details,
        )

    def close(self, *, run_id: str) -> TrailRunResult:
        """Expose the CLI verb while refusing P4-owned closure semantics."""
        run = self.store.get_run(run_id)
        if run.spec["schema_version"] != "trailspec.v1.1":
            return self._reject_v1_execution("close", run)
        chain = self.verify_chain(run_id=run_id)
        if chain.exit_class != ExitClass.OK:
            return TrailRunResult(
                command="close",
                exit_class=ExitClass.INVALID,
                outcome="closure_refused_invalid_chain",
                run_id=run_id,
                state=run.state,
                cursor_step=run.cursor_step_id,
                error=chain.error,
            )
        return TrailRunResult(
            command="close",
            exit_class=ExitClass.INVALID,
            outcome="closure_unavailable",
            run_id=run_id,
            state=run.state,
            cursor_step=run.cursor_step_id,
            error=(
                "P4 closure verification is not implemented; P3 never marks a run closed "
                "without authority, lease, head, and terminal re-observation checks"
            ),
        )
