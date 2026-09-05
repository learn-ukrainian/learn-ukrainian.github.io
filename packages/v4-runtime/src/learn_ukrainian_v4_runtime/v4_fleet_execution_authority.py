#!/usr/bin/env python3
"""Opaque author/reviewer attestation from canonical protected-parent execution.

Production issuers accept task/run identifiers only. They resolve the actual
FleetPG observation, require terminal success, observed model/session/harness,
current execution identity and the fixed active policy, then load the signing
key from the protected service credential resource. The package shares family
resolution and transport contracts with the repository compatibility adapters.

Low-level evidence structures remain useful for explicit synthetic unit tests.
They are not an alternative production authority or proof of native execution.
The separate private authentication/vendor adapter and actual-unit qualification
are deployment integration requirements, not capabilities asserted by these
source-free tests.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from typing import Any

from learn_ukrainian_v4_runtime import v4_trust_authority as trust
from learn_ukrainian_v4_runtime.contracts import CompletionState, ResponseEnvelope
from learn_ukrainian_v4_runtime.identity import (
    CURSOR_AUTO_UNION_FAMILY,
    KNOWN_HARNESS_EXECUTABLES,
    UNRESOLVED_AUTHOR_FAMILIES,
    resolve_author_family,
)

# The one outcome this attester ever signs for -- never a caller-supplied
# argument (PR #7662 repair 6; see ``v4_a7_private_ledger.V4_SHA256`` for
# the identical constant used by every other V4 module).
V4_SHA256 = "78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20"

SCHEMA_VERSION = "v4-fleet-execution-receipt-v1"
AUTHOR_DOMAIN = b"v4-fleet-execution-author-v1"
REVIEWER_DOMAIN = b"v4-fleet-execution-reviewer-v1"

# Exact allowed key sets for the two signed receipt bodies this module ever
# produces or verifies (PR #7662 repair 5). See module docstring.
AUTHOR_RECEIPT_KEYS = frozenset(
    {
        "runtime_identity",
        "schema_version",
        "domain",
        "outcome_sha256",
        "task_id",
        "run_nonce",
        "fleet_receipt_sha256",
        "provider_session_id",
        "model_family",
        "exact_model",
        "harness",
        "prompt_sha256",
        "packet_sha256",
        "row_content_sha256",
        "execution_result_sha256",
        "verification_tool_ids",
        "saw_source_text",
        "saw_heldout",
        "saw_eligible_unit_ids",
        "signer_key_id",
        "issuance_nonce",
        "trust_policy_sha256",
    }
)
REVIEWER_RECEIPT_KEYS = AUTHOR_RECEIPT_KEYS | {"authorship_receipt_sha256", "rubric_sha256", "verdict"}


class FleetExecutionError(ValueError):
    """An author/reviewer execution receipt cannot be issued or verified safely."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise FleetExecutionError(message)


# --- trusted execution evidence (authoritative, never a caller assertion) --


@dataclass(frozen=True, slots=True)
class TaskExecutionState:
    """Authoritative task/runtime-tracking evidence for one fleet execution
    -- never caller-asserted identity. Production custody supplies this from
    the real task-dispatch/tracking state the attester actually observed;
    every test here builds it explicitly as terminal synthetic evidence
    under ``tmp_path``, never a shortcut flag.

    ``seat_or_model`` is the exact runtime-resolved model/seat string the
    attester observed the execution run under -- the only input the model
    family and ``exact_model`` fields of the issued receipt are ever derived
    from (see ``_derive_identity``). ``harness`` must be one of the
    project's canonical durable agent-driver executables
    (``KNOWN_HARNESS_EXECUTABLES``) -- never an arbitrary free string.
    """

    task_id: str
    run_nonce: str
    status: str
    return_code: int
    seat_or_model: str
    harness: str
    session_id: str | None = None

    def __post_init__(self) -> None:
        require(
            isinstance(self.task_id, str) and bool(self.task_id),
            "task_state.task_id must be a nonempty string -- refusing",
        )
        require(
            isinstance(self.run_nonce, str) and bool(self.run_nonce),
            "task_state.run_nonce must be a nonempty string -- refusing",
        )
        require(
            isinstance(self.status, str) and bool(self.status),
            "task_state.status must be a nonempty string -- refusing",
        )
        require(
            isinstance(self.return_code, int) and not isinstance(self.return_code, bool),
            "task_state.return_code must be an int -- refusing",
        )
        require(
            isinstance(self.seat_or_model, str) and bool(self.seat_or_model),
            "task_state.seat_or_model must be a nonempty string -- refusing",
        )
        require(
            isinstance(self.harness, str) and bool(self.harness),
            "task_state.harness must be a nonempty string -- refusing",
        )
        require(
            self.session_id is None or (isinstance(self.session_id, str) and bool(self.session_id)),
            "task_state.session_id must be None or a nonempty string -- refusing",
        )


@dataclass(frozen=True, slots=True)
class AuthorExecutionObservation:
    """The role-specific structured observation the attester cross-validates
    against ``task_state``/``envelope`` before ever signing an author
    receipt -- never trusted as an identity/outcome assertion on its own.

    ``observed_model`` is what the *observation* independently records the
    execution running under -- it must exactly agree with the authoritative
    ``task_state.seat_or_model`` (``_require_observation_correlation``) or
    the receipt is refused. This is a correlation check only, never a second
    identity source: the signed ``exact_model``/``model_family`` fields are
    still derived solely from ``task_state`` (``_derive_identity``), so a
    caller can never select its own identity by choosing ``observed_model``
    -- it can only ever cause a legitimate observation to be refused for
    disagreeing with the authoritative task state."""

    task_id: str
    run_nonce: str
    observed_model: str
    row_content_sha256: str
    prompt_sha256: str
    packet_sha256: str
    execution_result_sha256: str
    fleet_receipt_sha256: str
    provider_session_id: str | None = None
    verification_tool_ids: tuple[str, ...] = ()
    runtime_identity: dict | None = None
    saw_source_text: bool = False
    saw_heldout: bool = False
    saw_eligible_unit_ids: bool = False


@dataclass(frozen=True, slots=True)
class ReviewerExecutionObservation:
    """The role-specific structured observation the attester cross-validates
    against ``task_state``/``envelope`` before ever signing a reviewer
    receipt -- additionally binds the exact authorship-receipt digest,
    rubric hash, and verdict. See ``AuthorExecutionObservation.
    observed_model`` for the model-correlation contract."""

    task_id: str
    run_nonce: str
    observed_model: str
    row_content_sha256: str
    prompt_sha256: str
    packet_sha256: str
    execution_result_sha256: str
    fleet_receipt_sha256: str
    authorship_receipt_sha256: str
    rubric_sha256: str
    verdict: str
    provider_session_id: str | None = None
    verification_tool_ids: tuple[str, ...] = ()
    runtime_identity: dict | None = None
    saw_source_text: bool = False
    saw_heldout: bool = False
    saw_eligible_unit_ids: bool = False


# --- terminal-execution / cross-evidence validation (fail closed) ----------


def _require_terminal_execution(task_state: TaskExecutionState, envelope: ResponseEnvelope) -> None:
    """The state must be terminal successful (advisor requirement): task
    state ``status == "done"`` with a zero return code, and the response
    envelope must independently confirm ``CompletionState.COMPLETE``, an
    observed terminal event, and a successful (zero) process return code.
    Any nonterminal, failed, length-limited, transport-incomplete, unknown,
    or terminal-event-unobserved execution refuses before signing."""
    require(
        task_state.status == "done",
        f"task state is not terminal successful (status={task_state.status!r}, expected 'done') -- refusing",
    )
    require(
        task_state.return_code == 0,
        f"task state return code is not a successful zero (return_code={task_state.return_code!r}) -- refusing",
    )
    require(
        envelope.completion_state is CompletionState.COMPLETE,
        f"response envelope is not complete (completion_state={envelope.completion_state!r}) -- refusing",
    )
    require(envelope.terminal_event_observed is True, "response envelope did not observe a terminal event -- refusing")
    require(
        envelope.process_returncode == 0,
        f"response envelope process return code is not a successful zero (process_returncode={envelope.process_returncode!r}) -- refusing",
    )


def _require_observation_correlation(
    task_state: TaskExecutionState,
    envelope: ResponseEnvelope,
    *,
    observation_task_id: str,
    observation_run_nonce: str,
    observation_model: str,
    observation_provider_session_id: str | None,
    observation_execution_result_sha256: str,
) -> None:
    """Exact task-state correlation for task id, run nonce, and observed
    model, plus agreement of the envelope's own raw-capture digest and
    provider session identity with the role-specific structured
    observation. Missing/mismatched evidence refuses closed."""
    require(
        observation_task_id == task_state.task_id,
        "observation task_id does not match the authoritative task state -- refusing",
    )
    require(
        observation_run_nonce == task_state.run_nonce,
        "observation run_nonce does not match the authoritative task state -- refusing",
    )
    require(
        isinstance(observation_model, str)
        and bool(observation_model)
        and observation_model == task_state.seat_or_model,
        "observation observed_model does not match the authoritative task state's seat_or_model -- refusing",
    )
    require(
        isinstance(envelope.raw_capture_sha256, str) and bool(trust.HEX64_RE.match(envelope.raw_capture_sha256)),
        "response envelope carries no well-formed raw_capture_sha256 -- refusing",
    )
    trust.require_sha256_hex(
        observation_execution_result_sha256, "observation.execution_result_sha256", error_cls=FleetExecutionError
    )
    require(
        envelope.raw_capture_sha256 == observation_execution_result_sha256,
        "observation execution_result_sha256 does not match the response envelope's own raw-capture digest -- refusing",
    )
    require(
        isinstance(envelope.session_id, str) and bool(envelope.session_id),
        "response envelope carries no provider session identity -- refusing",
    )
    if task_state.session_id is not None:
        require(
            task_state.session_id == envelope.session_id,
            "task state session_id does not match the response envelope's session_id -- refusing",
        )
    if observation_provider_session_id is not None:
        require(
            observation_provider_session_id == envelope.session_id,
            "observation provider_session_id does not match the response envelope's session_id -- refusing",
        )


def _derive_identity(task_state: TaskExecutionState) -> tuple[str, str, str]:
    """Derive ``(model_family, exact_model, harness)`` purely from
    authoritative task/runtime evidence -- never a caller-supplied family or
    harness override. ``model_family`` is derived with the canonical
    cross-family resolver (never a second family table); unknown,
    ambiguous, conflicting, or unattested/union-only identity all refuse.
    ``harness`` must be one of the project's canonical known durable
    agent-driver executables -- never a free string."""
    family = resolve_author_family(task_state.seat_or_model)
    require(
        family not in UNRESOLVED_AUTHOR_FAMILIES,
        f"task state model family could not be resolved to a concrete family (seat_or_model={task_state.seat_or_model!r}, resolved={family!r}) -- refusing",
    )
    require(
        family != CURSOR_AUTO_UNION_FAMILY,
        f"task state model family resolved to an unattested union family, not a single concrete identity (seat_or_model={task_state.seat_or_model!r}) -- refusing",
    )
    require(
        task_state.harness in KNOWN_HARNESS_EXECUTABLES,
        f"task state harness is not one of the canonical known harness executables {sorted(KNOWN_HARNESS_EXECUTABLES)}: {task_state.harness!r} -- refusing",
    )
    return family, task_state.seat_or_model, task_state.harness


def _require_no_duplicate_tool_ids(verification_tool_ids: tuple[str, ...]) -> None:
    require(
        len(verification_tool_ids) == len(set(verification_tool_ids)),
        "verification_tool_ids must not contain duplicates -- refusing",
    )


# --- issuance engine (attester-only; called only after the observed execution is confirmed) --
#
# ``_issue_author_receipt_from_evidence``/``_issue_reviewer_receipt_from_
# evidence`` are the unchanged repair-5 validation/signing engine -- private
# now (PR #7662 repair 6) because production never calls them directly.
# Tests may still call them directly to exercise this engine's own
# validation branches against synthetic evidence they construct themselves
# (that is testing internals, not a production bypass: neither function
# ever becomes reachable from a production code path). The only production
# entrypoints are ``issue_author_execution_receipt``/``issue_reviewer_
# execution_receipt`` below, which accept opaque ``task_id``/``run_id``
# only and resolve/derive every one of this engine's arguments internally.


def _issue_author_receipt_from_evidence(
    *,
    signing_key_hex: str,
    signer_key_id: str,
    outcome_sha256: str,
    task_state: TaskExecutionState,
    envelope: ResponseEnvelope,
    observation: AuthorExecutionObservation,
    issuance_nonce: str,
    trust_policy_sha256: str,
) -> dict[str, Any]:
    """Validate a trusted terminal execution observation and only then sign
    a text-free author execution receipt. Requires every ``saw_*``
    attestation to already be false (fail closed otherwise -- never silently
    coerces), the task state / response envelope to jointly prove a
    terminal, observed, successful execution (``_require_terminal_
    execution``), the role-specific observation to correlate exactly with
    that evidence (``_require_observation_correlation``), and derives
    ``model_family``/``exact_model``/``harness`` from the authoritative task
    state alone (``_derive_identity``) -- never from a caller-supplied
    override."""
    require(observation.saw_source_text is False, "author must attest saw_source_text is false -- refusing")
    require(observation.saw_heldout is False, "author must attest saw_heldout is false -- refusing")
    require(observation.saw_eligible_unit_ids is False, "author must attest saw_eligible_unit_ids is false -- refusing")
    _require_terminal_execution(task_state, envelope)
    _require_observation_correlation(
        task_state,
        envelope,
        observation_task_id=observation.task_id,
        observation_run_nonce=observation.run_nonce,
        observation_model=observation.observed_model,
        observation_provider_session_id=observation.provider_session_id,
        observation_execution_result_sha256=observation.execution_result_sha256,
    )
    model_family, exact_model, harness = _derive_identity(task_state)

    trust.require_sha256_hex(outcome_sha256, "outcome_sha256", error_cls=FleetExecutionError)
    for name, value in (
        ("prompt_sha256", observation.prompt_sha256),
        ("packet_sha256", observation.packet_sha256),
        ("row_content_sha256", observation.row_content_sha256),
        ("execution_result_sha256", observation.execution_result_sha256),
        ("fleet_receipt_sha256", observation.fleet_receipt_sha256),
    ):
        trust.require_sha256_hex(value, name, error_cls=FleetExecutionError)
    require(
        isinstance(issuance_nonce, str) and bool(issuance_nonce), "issuance_nonce must be a nonempty string -- refusing"
    )
    require(
        isinstance(signer_key_id, str) and bool(signer_key_id), "signer_key_id must be a nonempty string -- refusing"
    )
    trust.require_sha256_hex(trust_policy_sha256, "trust_policy_sha256", error_cls=FleetExecutionError)
    tool_ids = tuple(observation.verification_tool_ids)
    _require_no_duplicate_tool_ids(tool_ids)

    body = {
        "schema_version": SCHEMA_VERSION,
        "domain": "author",
        "outcome_sha256": outcome_sha256,
        "task_id": task_state.task_id,
        "run_nonce": task_state.run_nonce,
        "fleet_receipt_sha256": observation.fleet_receipt_sha256,
        "provider_session_id": envelope.session_id,
        "model_family": model_family,
        "exact_model": exact_model,
        "harness": harness,
        "prompt_sha256": observation.prompt_sha256,
        "packet_sha256": observation.packet_sha256,
        "row_content_sha256": observation.row_content_sha256,
        "execution_result_sha256": observation.execution_result_sha256,
        "verification_tool_ids": sorted(tool_ids),
        "saw_source_text": False,
        "saw_heldout": False,
        "saw_eligible_unit_ids": False,
        "signer_key_id": signer_key_id,
        "issuance_nonce": issuance_nonce,
        "trust_policy_sha256": trust_policy_sha256,
        "runtime_identity": observation.runtime_identity,
    }
    trust.require_exact_keys(body, AUTHOR_RECEIPT_KEYS, "author execution receipt", error_cls=FleetExecutionError)
    signature_hex = trust.sign(signing_key_hex, AUTHOR_DOMAIN, body)
    return {**body, "signature_hex": signature_hex}


def _issue_reviewer_receipt_from_evidence(
    *,
    signing_key_hex: str,
    signer_key_id: str,
    outcome_sha256: str,
    task_state: TaskExecutionState,
    envelope: ResponseEnvelope,
    observation: ReviewerExecutionObservation,
    issuance_nonce: str,
    trust_policy_sha256: str,
) -> dict[str, Any]:
    """Sign a text-free reviewer execution receipt, additionally binding
    the exact authorship-receipt digest, rubric hash, row hash, and
    verdict. Uses the identical trusted-observation validation and identity
    derivation as ``_issue_author_receipt_from_evidence``."""
    require(observation.saw_source_text is False, "reviewer must attest saw_source_text is false -- refusing")
    require(observation.saw_heldout is False, "reviewer must attest saw_heldout is false -- refusing")
    require(
        observation.saw_eligible_unit_ids is False, "reviewer must attest saw_eligible_unit_ids is false -- refusing"
    )
    require(observation.verdict in {"PASS", "FAIL"}, "verdict must be PASS or FAIL -- refusing")
    _require_terminal_execution(task_state, envelope)
    _require_observation_correlation(
        task_state,
        envelope,
        observation_task_id=observation.task_id,
        observation_run_nonce=observation.run_nonce,
        observation_model=observation.observed_model,
        observation_provider_session_id=observation.provider_session_id,
        observation_execution_result_sha256=observation.execution_result_sha256,
    )
    model_family, exact_model, harness = _derive_identity(task_state)

    trust.require_sha256_hex(outcome_sha256, "outcome_sha256", error_cls=FleetExecutionError)
    for name, value in (
        ("prompt_sha256", observation.prompt_sha256),
        ("packet_sha256", observation.packet_sha256),
        ("row_content_sha256", observation.row_content_sha256),
        ("execution_result_sha256", observation.execution_result_sha256),
        ("fleet_receipt_sha256", observation.fleet_receipt_sha256),
        ("authorship_receipt_sha256", observation.authorship_receipt_sha256),
        ("rubric_sha256", observation.rubric_sha256),
    ):
        trust.require_sha256_hex(value, name, error_cls=FleetExecutionError)
    require(
        isinstance(issuance_nonce, str) and bool(issuance_nonce), "issuance_nonce must be a nonempty string -- refusing"
    )
    require(
        isinstance(signer_key_id, str) and bool(signer_key_id), "signer_key_id must be a nonempty string -- refusing"
    )
    trust.require_sha256_hex(trust_policy_sha256, "trust_policy_sha256", error_cls=FleetExecutionError)
    tool_ids = tuple(observation.verification_tool_ids)
    _require_no_duplicate_tool_ids(tool_ids)

    body = {
        "schema_version": SCHEMA_VERSION,
        "domain": "reviewer",
        "outcome_sha256": outcome_sha256,
        "task_id": task_state.task_id,
        "run_nonce": task_state.run_nonce,
        "fleet_receipt_sha256": observation.fleet_receipt_sha256,
        "provider_session_id": envelope.session_id,
        "model_family": model_family,
        "exact_model": exact_model,
        "harness": harness,
        "prompt_sha256": observation.prompt_sha256,
        "packet_sha256": observation.packet_sha256,
        "row_content_sha256": observation.row_content_sha256,
        "execution_result_sha256": observation.execution_result_sha256,
        "authorship_receipt_sha256": observation.authorship_receipt_sha256,
        "rubric_sha256": observation.rubric_sha256,
        "verdict": observation.verdict,
        "verification_tool_ids": sorted(tool_ids),
        "saw_source_text": False,
        "saw_heldout": False,
        "saw_eligible_unit_ids": False,
        "signer_key_id": signer_key_id,
        "issuance_nonce": issuance_nonce,
        "trust_policy_sha256": trust_policy_sha256,
        "runtime_identity": observation.runtime_identity,
    }
    trust.require_exact_keys(body, REVIEWER_RECEIPT_KEYS, "reviewer execution receipt", error_cls=FleetExecutionError)
    signature_hex = trust.sign(signing_key_hex, REVIEWER_DOMAIN, body)
    return {**body, "signature_hex": signature_hex}


# --- production entrypoints: opaque IDs only (PR #7662 repair 6) -----------
#
# The only two functions a real V4 dispatch caller may ever call. Neither
# accepts a signing key, a task-state/envelope/observation object, or an
# outcome/trust-policy argument -- every one of those is resolved or fixed
# internally. ``_resolve_execution_observation``/``_load_signing_key`` are
# the exact module-level indirection points tests monkeypatch with an
# isolated fixture resolver/key; production's own defaults query the real
# canonical Fleet Comms store and fixed Hramatka key custody.


def _open_canonical_authority_store() -> Any:
    """The single module-level indirection point for canonical-authority
    selection (PR #7662 repair 7). Production has exactly one implementation
    and it takes no arguments: the operator-approved live Fleet Comms
    PostgreSQL plane. There is no root, path, DSN, connection, store or
    request-level parameter anywhere on this module's production surface
    that could redirect it to a caller-owned SQLite plane, and a missing or
    unavailable PG plane refuses rather than falling back. Tests substitute
    an isolated ``tmp_path`` store here in-process -- the same
    monkeypatch-the-fixed-internal-loader pattern the Sol acceptance matrix
    sanctions for key custody and the production policy resolver."""
    from learn_ukrainian_v4_runtime import v4_canonical_authority_store as v4_store

    return v4_store.open_production_authority_store()


def _resolve_execution_observation(*, task_id: str, run_id: str, role: str) -> dict[str, Any] | None:
    """Resolve one canonical observation, or refuse. ``None`` means the
    canonical authority was reachable and simply holds no record for this
    opaque key; an authority that is not the approved PostgreSQL plane, or
    that is unreachable, raises -- both outcomes refuse before any key
    access, and neither ever degrades to a local store."""
    from learn_ukrainian_v4_runtime import v4_canonical_authority_store as v4_store

    try:
        store = _open_canonical_authority_store()
    except v4_store.CanonicalAuthorityUnavailableError as exc:
        raise FleetExecutionError(
            f"canonical V4 execution authority unavailable -- refusing (no key access): {exc}"
        ) from exc
    try:
        return store.resolve_v4_execution_observation(task_id=task_id, run_id=run_id, role=role)
    except Exception as exc:
        raise FleetExecutionError("canonical V4 execution authority read failed -- refusing (no key access)") from exc
    finally:
        with contextlib.suppress(Exception):
            store.close()


def _load_signing_key(role: str) -> tuple[str, str]:
    return trust.load_production_signing_key(role)


def _task_state_from_record(record: dict[str, Any]) -> TaskExecutionState:
    return TaskExecutionState(
        task_id=record["task_id"],
        run_nonce=record["run_id"],
        status=record["status"],
        return_code=record["return_code"],
        seat_or_model=record["seat_or_model"],
        harness=record["harness"],
        session_id=record["session_id"],
    )


def _envelope_from_record(record: dict[str, Any]) -> ResponseEnvelope:
    return ResponseEnvelope(
        segments=(),
        completion_state=CompletionState(record["completion_state"]),
        terminal_event_observed=record["terminal_event_observed"],
        process_returncode=record["process_returncode"],
        raw_capture_artifact_id=record["raw_capture_artifact_id"],
        raw_capture_sha256=record["raw_capture_sha256"],
        session_id=record["session_id"],
    )


def _author_observation_from_record(record: dict[str, Any]) -> AuthorExecutionObservation:
    return AuthorExecutionObservation(
        task_id=record["task_id"],
        run_nonce=record["run_id"],
        observed_model=record["seat_or_model"],
        row_content_sha256=record["row_content_sha256"],
        prompt_sha256=record["prompt_sha256"],
        packet_sha256=record["packet_sha256"],
        execution_result_sha256=record["raw_capture_sha256"],
        fleet_receipt_sha256=record["fleet_receipt_sha256"],
        provider_session_id=record["session_id"],
        verification_tool_ids=tuple(record["verification_tool_ids"]),
        runtime_identity=record["runtime_identity"],
        saw_source_text=record["saw_source_text"],
        saw_heldout=record["saw_heldout"],
        saw_eligible_unit_ids=record["saw_eligible_unit_ids"],
    )


def _reviewer_observation_from_record(record: dict[str, Any]) -> ReviewerExecutionObservation:
    return ReviewerExecutionObservation(
        task_id=record["task_id"],
        run_nonce=record["run_id"],
        observed_model=record["seat_or_model"],
        row_content_sha256=record["row_content_sha256"],
        prompt_sha256=record["prompt_sha256"],
        packet_sha256=record["packet_sha256"],
        execution_result_sha256=record["raw_capture_sha256"],
        fleet_receipt_sha256=record["fleet_receipt_sha256"],
        authorship_receipt_sha256=record["authorship_receipt_sha256"],
        rubric_sha256=record["rubric_sha256"],
        verdict=record["verdict"],
        provider_session_id=record["session_id"],
        verification_tool_ids=tuple(record["verification_tool_ids"]),
        runtime_identity=record["runtime_identity"],
        saw_source_text=record["saw_source_text"],
        saw_heldout=record["saw_heldout"],
        saw_eligible_unit_ids=record["saw_eligible_unit_ids"],
    )


def _issuance_nonce(*, role: str, task_id: str, run_id: str) -> str:
    """Deterministic, never caller-supplied -- re-issuing against the same
    resolved observation always reproduces the identical receipt (repeat
    issuance is idempotent, not a fresh nonce every call)."""
    return trust.sha256_text(f"v4-fleet-execution-issuance-v1\x00{role}\x00{task_id}\x00{run_id}")


def issue_author_execution_receipt(*, task_id: str, run_id: str) -> dict[str, Any]:
    """The only production-facing way to obtain a signed author execution
    receipt (PR #7662 repair 6, Sol minimal API). Accepts opaque
    ``task_id``/``run_id`` only: resolves the trusted execution observation
    from the canonical Fleet Comms authority store
    (``_resolve_execution_observation`` -- unknown/ambiguous/incomplete
    records refuse before any key access), the signing key from fixed
    Hramatka custody (``_load_signing_key``), and the pinned production
    trust-policy digest (``v4_trust_authority.load_production_trust_
    policy``) -- never from a caller-supplied argument."""
    require(isinstance(task_id, str) and bool(task_id), "task_id must be a nonempty string -- refusing")
    require(isinstance(run_id, str) and bool(run_id), "run_id must be a nonempty string -- refusing")
    record = _resolve_execution_observation(task_id=task_id, run_id=run_id, role="author")
    require(
        record is not None,
        f"unknown task_id/run_id for an author execution observation: {task_id!r}/{run_id!r} -- refusing (no key access)",
    )
    from learn_ukrainian_v4_runtime.execution_identity import validate_execution_identity

    try:
        validate_execution_identity(record.get("runtime_identity"))
    except ValueError as exc:
        raise FleetExecutionError(str(exc)) from exc
    _, resolved_trust_policy_sha256 = trust.load_production_trust_policy()
    require(record.get("trust_policy_sha256") == resolved_trust_policy_sha256, "execution policy is not active -- refusing before key access")
    _require_terminal_execution(_task_state_from_record(record), _envelope_from_record(record))
    signing_key_hex, signer_key_id = _load_signing_key("fleet_execution")
    return _issue_author_receipt_from_evidence(
        signing_key_hex=signing_key_hex,
        signer_key_id=signer_key_id,
        outcome_sha256=V4_SHA256,
        task_state=_task_state_from_record(record),
        envelope=_envelope_from_record(record),
        observation=_author_observation_from_record(record),
        issuance_nonce=_issuance_nonce(role="author", task_id=task_id, run_id=run_id),
        trust_policy_sha256=resolved_trust_policy_sha256,
    )


def issue_reviewer_execution_receipt(*, task_id: str, run_id: str) -> dict[str, Any]:
    """The only production-facing way to obtain a signed reviewer execution
    receipt. Identical opaque-ID-only contract as ``issue_author_execution_
    receipt``, resolving a reviewer-role canonical observation instead."""
    require(isinstance(task_id, str) and bool(task_id), "task_id must be a nonempty string -- refusing")
    require(isinstance(run_id, str) and bool(run_id), "run_id must be a nonempty string -- refusing")
    record = _resolve_execution_observation(task_id=task_id, run_id=run_id, role="reviewer")
    require(
        record is not None,
        f"unknown task_id/run_id for a reviewer execution observation: {task_id!r}/{run_id!r} -- refusing (no key access)",
    )
    from learn_ukrainian_v4_runtime.execution_identity import validate_execution_identity

    try:
        validate_execution_identity(record.get("runtime_identity"))
    except ValueError as exc:
        raise FleetExecutionError(str(exc)) from exc
    _, resolved_trust_policy_sha256 = trust.load_production_trust_policy()
    require(record.get("trust_policy_sha256") == resolved_trust_policy_sha256, "execution policy is not active -- refusing before key access")
    _require_terminal_execution(_task_state_from_record(record), _envelope_from_record(record))
    signing_key_hex, signer_key_id = _load_signing_key("fleet_execution")
    return _issue_reviewer_receipt_from_evidence(
        signing_key_hex=signing_key_hex,
        signer_key_id=signer_key_id,
        outcome_sha256=V4_SHA256,
        task_state=_task_state_from_record(record),
        envelope=_envelope_from_record(record),
        observation=_reviewer_observation_from_record(record),
        issuance_nonce=_issuance_nonce(role="reviewer", task_id=task_id, run_id=run_id),
        trust_policy_sha256=resolved_trust_policy_sha256,
    )


# --- verification (A7's own private ledger; never mints a receipt) ---------


def _verify_common(
    receipt: dict[str, Any],
    *,
    domain_name: str,
    domain: bytes,
    expected_keys: frozenset[str],
    trust_policy: dict[str, Any],
    outcome_sha256: str,
    row_content_sha256: str,
) -> dict[str, Any]:
    require(isinstance(receipt, dict), f"{domain_name} execution receipt must be an object -- refusing")
    body = {k: v for k, v in receipt.items() if k != "signature_hex"}
    trust.require_exact_keys(body, expected_keys, f"{domain_name} execution receipt", error_cls=FleetExecutionError)
    require(
        body.get("schema_version") == SCHEMA_VERSION and body.get("domain") == domain_name,
        f"malformed {domain_name} execution receipt -- refusing",
    )
    require(
        body.get("outcome_sha256") == outcome_sha256,
        f"{domain_name} execution receipt is bound to a different outcome -- refusing",
    )
    require(
        body.get("row_content_sha256") == row_content_sha256,
        f"{domain_name} execution receipt is not bound to this row's content hash -- refusing",
    )
    for flag in ("saw_source_text", "saw_heldout", "saw_eligible_unit_ids"):
        require(body.get(flag) is False, f"{domain_name} execution receipt attests {flag} is not false -- refusing")
    for name in ("model_family", "exact_model", "harness", "task_id", "run_nonce", "provider_session_id"):
        require(
            isinstance(body.get(name), str) and body[name],
            f"{domain_name} execution receipt is missing {name} -- refusing",
        )
    require(
        body.get("model_family") not in UNRESOLVED_AUTHOR_FAMILIES
        and body.get("model_family") != CURSOR_AUTO_UNION_FAMILY,
        f"{domain_name} execution receipt carries an unresolved/union model family -- refusing",
    )
    require(
        body.get("harness") in KNOWN_HARNESS_EXECUTABLES,
        f"{domain_name} execution receipt harness is not one of the canonical known harness executables -- refusing",
    )
    for name in ("prompt_sha256", "packet_sha256", "execution_result_sha256", "fleet_receipt_sha256"):
        trust.require_sha256_hex(
            body.get(name), f"{domain_name} execution receipt {name}", error_cls=FleetExecutionError
        )
    signature_hex = receipt.get("signature_hex")
    require(
        isinstance(signature_hex, str) and bool(signature_hex),
        f"{domain_name} execution receipt carries no signature -- refusing",
    )
    try:
        trust.verify_with_policy(
            trust_policy, "fleet_execution", body.get("signer_key_id"), domain, body, signature_hex
        )
    except trust.TrustAuthorityError as exc:
        raise FleetExecutionError(
            f"{domain_name} execution receipt failed signature verification -- refusing: {exc}"
        ) from exc
    from learn_ukrainian_v4_runtime.execution_identity import validate_execution_identity

    try:
        validate_execution_identity(body.get("runtime_identity"))
    except ValueError as exc:
        raise FleetExecutionError(str(exc)) from exc
    trust.require_trust_policy_binding(body, trust_policy, error_cls=FleetExecutionError)
    return body


def verify_author_execution_receipt(
    receipt: dict[str, Any], *, trust_policy: dict[str, Any], outcome_sha256: str, row_content_sha256: str
) -> None:
    _verify_common(
        receipt,
        domain_name="author",
        domain=AUTHOR_DOMAIN,
        expected_keys=AUTHOR_RECEIPT_KEYS,
        trust_policy=trust_policy,
        outcome_sha256=outcome_sha256,
        row_content_sha256=row_content_sha256,
    )


def verify_reviewer_execution_receipt(
    receipt: dict[str, Any],
    *,
    trust_policy: dict[str, Any],
    outcome_sha256: str,
    row_content_sha256: str,
    authorship_receipt_sha256: str,
    rubric_sha256: str,
) -> None:
    body = _verify_common(
        receipt,
        domain_name="reviewer",
        domain=REVIEWER_DOMAIN,
        expected_keys=REVIEWER_RECEIPT_KEYS,
        trust_policy=trust_policy,
        outcome_sha256=outcome_sha256,
        row_content_sha256=row_content_sha256,
    )
    require(
        body.get("authorship_receipt_sha256") == authorship_receipt_sha256,
        "reviewer execution receipt is bound to a different authorship receipt -- refusing",
    )
    require(
        body.get("rubric_sha256") == rubric_sha256,
        "reviewer execution receipt is bound to a different rubric -- refusing",
    )
    require(
        body.get("verdict") in {"PASS", "FAIL"}, "reviewer execution receipt verdict must be PASS or FAIL -- refusing"
    )
