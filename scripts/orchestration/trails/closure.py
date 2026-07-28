"""Fail-closed terminal closure for the SQLite-authoritative Trail runner.

Closure is intentionally a sequence of durable local evidence plus fresh
external observations.  It does not claim a transaction spanning GitHub,
fleet-comms, and SQLite: an idempotent command receipt is followed by external
re-observation and only then by the SQLite terminal commit.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from jsonschema import Draft202012Validator, FormatChecker

from .authority import (
    APPROVED_SOURCE_KINDS,
    AuthorityReceiptError,
    VerifiedAuthorityReceipt,
)
from .models import TrailRun, TrailRunnerError
from .store import TrailStore, digest_json, utc_now

PROJECT_ROOT = Path(__file__).resolve().parents[3]
CLOSURE_ATTESTATION_SCHEMA_PATH = (
    PROJECT_ROOT / "agents_extensions/shared/schemas/trail-closure-attestation.v1.schema.json"
)
OPAQUE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
SHA256 = re.compile(r"^[a-f0-9]{64}$")
_CLOSURE_ATTESTATION_VALIDATOR: Draft202012Validator | None = None


class ClosureError(TrailRunnerError):
    """Raised when closure cannot be proven from fresh external evidence."""


class AuthorityReceiptRevalidator(Protocol):
    """The authority resolver's closure-time re-fetch capability."""

    def revalidate(self, receipt: Mapping[str, Any]) -> VerifiedAuthorityReceipt:
        """Re-fetch a consumed receipt and prove it remains immutable and current."""


class TerminalObservationSource(Protocol):
    """A provisioned bridge/API re-observer; never a local receipt projection."""

    source_id: str
    source_kind: str

    def reobserve_terminal(
        self,
        *,
        run: TrailRun,
        terminal_command_receipt: Mapping[str, Any],
        terminal_step_receipt: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Return fresh external terminal, lease/fence, and optional PR-head evidence."""


@dataclass(frozen=True, slots=True)
class ClosureCommit:
    """One terminal closure result, either newly committed or safely replayed."""

    attestation: dict[str, Any]
    attestation_digest: str
    replayed: bool


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _parse_time(value: object, *, field: str) -> datetime:
    if not isinstance(value, str):
        raise ClosureError(f"closure {field} must be an RFC3339 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ClosureError(f"closure {field} is not an RFC3339 timestamp") from exc
    if parsed.tzinfo is None:
        raise ClosureError(f"closure {field} must include a timezone")
    return parsed.astimezone(UTC)


def _validator() -> Draft202012Validator:
    """Build the immutable closure validator once without caching attestations."""
    global _CLOSURE_ATTESTATION_VALIDATOR
    if _CLOSURE_ATTESTATION_VALIDATOR is not None:
        return _CLOSURE_ATTESTATION_VALIDATOR
    try:
        schema = json.loads(CLOSURE_ATTESTATION_SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ClosureError(f"cannot load closure attestation schema: {exc}") from exc
    if not isinstance(schema, dict):
        raise ClosureError("closure attestation schema root must be an object")
    _CLOSURE_ATTESTATION_VALIDATOR = Draft202012Validator(schema, format_checker=FormatChecker())
    return _CLOSURE_ATTESTATION_VALIDATOR


def validate_closure_attestation_data(attestation: Mapping[str, Any]) -> dict[str, Any]:
    """Validate an attestation assembled exclusively from pinned/fresh evidence."""
    if not isinstance(attestation, Mapping):
        raise ClosureError("closure attestation must be an object")
    payload = dict(attestation)
    errors = sorted(
        _validator().iter_errors(payload),
        key=lambda error: tuple(error.path),
    )
    if errors:
        error = errors[0]
        raise ClosureError(
            f"closure attestation schema violation: {error.message} at {error.json_path}"
        )
    _parse_time(payload["closed_at"], field="closed_at")
    return payload


class TrailClosureGate:
    """Re-observe and atomically terminally commit a chain that is already proven intact."""

    def __init__(
        self,
        store: TrailStore,
        observation_source: TerminalObservationSource,
        *,
        authority_resolver: AuthorityReceiptRevalidator | None = None,
        now: Callable[[], datetime] = _utc_now,
    ) -> None:
        if getattr(observation_source, "source_kind", None) not in APPROVED_SOURCE_KINDS:
            raise ClosureError("terminal observation source must be a provisioned bridge or API")
        if not isinstance(getattr(observation_source, "source_id", None), str) or not observation_source.source_id:
            raise ClosureError("terminal observation source must have a stable source_id")
        self.store = store
        self.observation_source = observation_source
        self.authority_resolver = authority_resolver
        self.now = now

    def existing(self, run_id: str) -> ClosureCommit | None:
        """Return the stored immutable terminal result without another external call."""
        stored = self.store.get_closure(run_id)
        if stored is None:
            return None
        attestation = validate_closure_attestation_data(stored["attestation"])
        if digest_json(attestation) != stored["attestation_digest"]:
            raise ClosureError("stored closure attestation digest does not match payload")
        return ClosureCommit(
            attestation=attestation,
            attestation_digest=str(stored["attestation_digest"]),
            replayed=True,
        )

    def close(
        self,
        *,
        run: TrailRun,
        chain_digest: str,
        terminal_invocation: Mapping[str, Any],
        terminal_command_receipt: Mapping[str, Any],
        terminal_step_receipt: Mapping[str, Any],
    ) -> ClosureCommit:
        """Re-observe external state and commit a schema-valid terminal attestation."""
        if run.state != "terminal" or not run.terminal_outcome:
            raise ClosureError("closure requires a terminal TrailSpec run")
        existing = self.existing(run.run_id)
        if existing is not None:
            return existing
        if terminal_invocation.get("resolved_command", {}).get("mutation_class") != "observe":
            raise ClosureError("terminal closure requires a terminal re-observation command")
        if not SHA256.fullmatch(chain_digest):
            raise ClosureError("closure chain digest is invalid")
        self._validate_authority_receipts(run)
        observation = self._reobserve(
            run=run,
            terminal_command_receipt=terminal_command_receipt,
            terminal_step_receipt=terminal_step_receipt,
        )
        self._validate_observation(
            observation=observation,
            run=run,
            terminal_step_receipt=terminal_step_receipt,
        )
        authority_digests = self._authority_digests(run, observation)
        attestation = validate_closure_attestation_data(
            {
                "schema_version": "trail-closure-attestation.v1",
                "run_id": run.run_id,
                "trail_id": run.trail_id,
                "trail_version": run.trail_version,
                "trail_hash": run.trail_hash,
                "terminal_outcome": run.terminal_outcome,
                "chain_digest": chain_digest,
                "terminal_command_receipt_digest": digest_json(dict(terminal_command_receipt)),
                "terminal_step_receipt_digest": digest_json(dict(terminal_step_receipt)),
                "observation_source": self.observation_source.source_id,
                "observation_id": observation["observation_id"],
                "terminal_reobservation_digest": digest_json(observation),
                "lease_id": observation["lease_id"],
                "lease_generation": observation["lease_generation"],
                "fencing_token": observation["fencing_token"],
                "pr_head": observation["pr_head"],
                "authority_receipt_digests": authority_digests,
                "closed_at": self.now().astimezone(UTC).isoformat(timespec="microseconds").replace(
                    "+00:00", "Z"
                ),
            }
        )
        committed = self.store.commit_closure(run_id=run.run_id, attestation=attestation)
        committed_attestation = validate_closure_attestation_data(committed["attestation"])
        return ClosureCommit(
            attestation=committed_attestation,
            attestation_digest=str(committed["attestation_digest"]),
            replayed=committed_attestation != attestation,
        )

    def _validate_authority_receipts(self, run: TrailRun) -> None:
        receipts = self.store.list_authority_receipts(run.run_id)
        if receipts and self.authority_resolver is None:
            raise ClosureError("closure has authority receipts but no approved revalidator")
        for stored in receipts:
            assert self.authority_resolver is not None
            try:
                revalidated = self.authority_resolver.revalidate(stored["receipt"])
            except AuthorityReceiptError as exc:
                raise ClosureError(f"authority receipt {stored['receipt_id']} cannot close: {exc}") from exc
            if revalidated.digest != stored["receipt_digest"]:
                raise ClosureError("re-fetched authority receipt digest differs from durable evidence")
            if revalidated.source_id != stored["source_id"]:
                raise ClosureError("authority receipt source differs from durable evidence")

    def _authority_digests(self, run: TrailRun, observation: Mapping[str, Any]) -> list[str]:
        digests: list[str] = []
        for stored in self.store.list_authority_receipts(run.run_id):
            receipt = stored["receipt"]
            for field in ("lease_id", "lease_generation", "fencing_token"):
                if receipt[field] != observation[field]:
                    raise ClosureError("authority receipt lease/fence is stale at closure")
            receipt_head = receipt.get("pr_head")
            if receipt_head is not None and receipt_head != observation["pr_head"]:
                raise ClosureError("authority receipt PR head is stale at closure")
            digests.append(str(stored["receipt_digest"]))
        return digests

    def _reobserve(
        self,
        *,
        run: TrailRun,
        terminal_command_receipt: Mapping[str, Any],
        terminal_step_receipt: Mapping[str, Any],
    ) -> dict[str, Any]:
        try:
            observed = self.observation_source.reobserve_terminal(
                run=run,
                terminal_command_receipt=terminal_command_receipt,
                terminal_step_receipt=terminal_step_receipt,
            )
        except ClosureError:
            raise
        except Exception as exc:
            raise ClosureError("terminal re-observation is unavailable") from exc
        if not isinstance(observed, Mapping):
            raise ClosureError("terminal re-observation is not an object")
        return dict(observed)

    def _validate_observation(
        self,
        *,
        observation: Mapping[str, Any],
        run: TrailRun,
        terminal_step_receipt: Mapping[str, Any],
    ) -> None:
        required = {
            "observation_id",
            "observed_at",
            "run_id",
            "trail_id",
            "trail_hash",
            "terminal_outcome",
            "lease_id",
            "lease_generation",
            "fencing_token",
            "pr_head",
            "lease_current",
            "terminal_observed",
        }
        if set(observation) != required:
            raise ClosureError("terminal re-observation has an unexpected evidence shape")
        if not isinstance(observation["observation_id"], str) or not OPAQUE_ID.fullmatch(
            observation["observation_id"]
        ):
            raise ClosureError("terminal re-observation has an invalid observation_id")
        _parse_time(observation["observed_at"], field="observed_at")
        expected = {
            "run_id": run.run_id,
            "trail_id": run.trail_id,
            "trail_hash": run.trail_hash,
            "terminal_outcome": run.terminal_outcome,
        }
        for field, value in expected.items():
            if observation[field] != value:
                raise ClosureError(f"terminal re-observation {field} does not bind the terminal run")
        if observation["lease_current"] is not True or observation["terminal_observed"] is not True:
            raise ClosureError("terminal re-observation does not prove current terminal state")
        if not isinstance(observation["lease_id"], str) or not OPAQUE_ID.fullmatch(observation["lease_id"]):
            raise ClosureError("terminal re-observation has an invalid lease_id")
        if type(observation["lease_generation"]) is not int or observation["lease_generation"] < 0:
            raise ClosureError("terminal re-observation has an invalid lease_generation")
        if not isinstance(observation["fencing_token"], str) or not OPAQUE_ID.fullmatch(
            observation["fencing_token"]
        ):
            raise ClosureError("terminal re-observation has an invalid fencing_token")
        observed_head = observation["pr_head"]
        if observed_head is not None and (
            not isinstance(observed_head, str) or not re.fullmatch(r"[0-9a-f]{40}", observed_head)
        ):
            raise ClosureError("terminal re-observation has an invalid PR head")
        expected_head = terminal_step_receipt.get("pr_head")
        if observed_head != expected_head:
            raise ClosureError("terminal re-observation current PR head differs from terminal evidence")
