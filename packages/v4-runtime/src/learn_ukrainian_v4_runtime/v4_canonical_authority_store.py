"""V4 canonical authority store (PR #7662 repair 8 -- designated-advisor
GO_REPAIR after repair 7 failed exact-head review).

The operator-approved architecture still holds: the live Fleet Comms
PostgreSQL plane is the single canonical authority for text-free execution
observations and Sources invocation records. Repair 8 moves the *writer*:
``RequestExecutor.execute_capture`` is not a V4 execution origin. Only the
native runner (``scripts.agent_runtime.runner._execute_invocation_plan``)
may claim a binding and persist a terminal observation, from facts of the
process it actually spawned.

Tables:

* ``v4_execution_dispatch_bindings`` -- role-specific pre-execution
  authorization. Author bindings resolve a frozen slot and A3 packet and
  record the service-built source-blind prompt digest; they never accept a
  row hash. Reviewer bindings resolve an authorship receipt and the fixed
  rubric internally.
* ``v4_execution_attempts`` -- one attempt per claimed request. Created
  atomically with ``queued -> running``. Stores only the capability digest.
* ``v4_execution_observations`` -- runner-owned terminal facts for one
  author/reviewer execution.
* ``v4_sources_invocations`` -- typed Sources outcomes keyed by attempt,
  not by a caller-declared request/row correlation.
* ``v4_authorship_receipts`` -- service-resolved author receipts the
  reviewer authorization looks up by opaque id.

There is no public function that accepts a caller-built observation or
Sources record. Production resolution still requires the approved
PostgreSQL plane (``open_production_authority_store``).
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from typing import Any

EXECUTION_OBSERVATION_TABLE = "v4_execution_observations"
SOURCES_INVOCATION_TABLE = "v4_sources_invocations"
EXECUTION_DISPATCH_BINDING_TABLE = "v4_execution_dispatch_bindings"
EXECUTION_ATTEMPT_TABLE = "v4_execution_attempts"
AUTHORSHIP_RECEIPT_TABLE = "v4_authorship_receipts"
EXECUTION_OBSERVATION_ROLES = frozenset({"author", "reviewer"})
AUTHOR_PROMPT_PROFILE = "v4-author-source-blind-v1"
REVIEWER_PROMPT_PROFILE = "v4-reviewer-source-blind-v1"
POSITIVE_V4_VERIFIER_TOOLS = frozenset(
    {
        "verify_word",
        "verify_words",
        "verify_lemma",
        "verify_stress",
        "check_modern_form",
    }
)
EXCLUDED_POSITIVE_V4_TOOLS = frozenset({"vet_vocabulary", "check_russian_shadow"})

HEX64_RE = re.compile(r"^[a-f0-9]{64}$")

# Exact key set for a canonical execution-observation record (same "declare
# exactly this key set" discipline every other durable/signed artifact in
# this project uses -- an extra or missing key refuses closed rather than
# silently passing through).
EXECUTION_OBSERVATION_KEYS = frozenset(
    {
        "runtime_identity",
        "trust_policy_sha256",
        "task_id",
        "run_id",
        "role",
        "attempt_id",
        "status",
        "return_code",
        "seat_or_model",
        "requested_model",
        "harness",
        "executable",
        "argv_digest",
        "session_id",
        "completion_state",
        "terminal_event_observed",
        "process_returncode",
        "raw_capture_artifact_id",
        "raw_capture_sha256",
        "stdout_sha256",
        "stderr_sha256",
        "output_artifact_sha256",
        "aggregate_artifact_sha256",
        "row_content_sha256",
        "prompt_profile",
        "prompt_sha256",
        "packet_sha256",
        "fleet_receipt_sha256",
        "verification_tool_ids",
        "saw_source_text",
        "saw_heldout",
        "saw_eligible_unit_ids",
        "authorship_receipt_sha256",
        "rubric_sha256",
        "verdict",
    }
)

SOURCES_INVOCATION_KEYS = frozenset(
    {
        "invocation_id",
        "attempt_id",
        "ordinal",
        "identifier",
        "tool_id",
        "tool_version",
        "structured_result_sha256",
        "lookup_ids",
        "success",
        "disposition",
        "recorded_at",
    }
)

# Pre-execution dispatch authorization. Author bindings never carry a row
# hash: the runner derives that from structured author output. Reviewer
# bindings never accept packet/rubric/content hashes from the caller.
EXECUTION_DISPATCH_BINDING_KEYS = frozenset(
    {
        "request_id",
        "task_id",
        "run_id",
        "role",
        "slot_id",
        "expected_seat_or_model",
        "expected_harness",
        "prompt_profile",
        "prompt_sha256",
        "packet_sha256",
        "authorship_receipt_id",
        "authorship_receipt_sha256",
        "rubric_sha256",
    }
)


class CanonicalAuthorityStoreError(RuntimeError):
    """The canonical execution/Sources authority store refused an operation."""


class CanonicalAuthorityUnavailableError(CanonicalAuthorityStoreError):
    """The approved canonical PostgreSQL authority is not the resolved plane."""


class ExecutionObservationConflictError(CanonicalAuthorityStoreError):
    """A different execution observation is already recorded for this task_id/run_id/role."""


class ExecutionDispatchBindingConflictError(CanonicalAuthorityStoreError):
    """A different dispatch binding is already recorded for this request/slot."""


class SourcesInvocationConflictError(CanonicalAuthorityStoreError):
    """A different Sources invocation is already recorded for this invocation_id."""


class ExecutionAttemptConflictError(CanonicalAuthorityStoreError):
    """A request already has a V4 execution attempt, or the capability is not active."""


class AuthorshipReceiptConflictError(CanonicalAuthorityStoreError):
    """A different authorship receipt is already recorded for this id or slot."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CanonicalAuthorityStoreError(message)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _row_get(row: Any, column: str, index: int) -> Any:
    return row[column] if isinstance(row, dict) else row[index]


def _require_hex64(value: Any, name: str) -> None:
    _require(
        isinstance(value, str) and bool(HEX64_RE.match(value)),
        f"{name} must be a lowercase sha256 hex digest -- refusing",
    )


# --- fixed production authority selection (PR #7662 repair 7, F3 blocker 2) --


def open_production_authority_store(*, write: bool = False) -> Any:
    """Open the ONE approved canonical authority plane, with no caller input.

    Takes no root, path, DSN, connection or authority argument: production
    resolution is fixed to the live Fleet Comms PostgreSQL plane the
    operator approved. If the resolved control-plane authority for
    ``StoreId.FLEET_COMMS`` is anything other than ``pg`` -- a bare SSH
    shell's SQLite default, a configured local root, an injected store --
    this refuses closed with ``CanonicalAuthorityUnavailableError`` and
    there is no fallback. A missing or unreachable PG plane likewise
    refuses; it never degrades to a local store.

    ``write`` selects a writable versus read-only connection to that same
    fixed plane; it can never select a *different* plane.
    """
    from learn_ukrainian_v4_runtime.scoped_store import ScopedAuthorityStore

    try:
        return ScopedAuthorityStore(write=write)
    except Exception as exc:
        raise CanonicalAuthorityUnavailableError("scoped V4 PostgreSQL custody unavailable -- refusing") from exc


# --- pre-execution dispatch authorization ----------------------------------


def validate_execution_dispatch_binding(binding: dict[str, Any]) -> None:
    _require(
        isinstance(binding, dict) and set(binding) == EXECUTION_DISPATCH_BINDING_KEYS,
        f"execution dispatch binding must declare exactly {sorted(EXECUTION_DISPATCH_BINDING_KEYS)} -- refusing (unexpected or missing key)",
    )
    for name in ("request_id", "task_id", "run_id", "expected_seat_or_model", "expected_harness", "prompt_profile"):
        _require(
            isinstance(binding.get(name), str) and bool(binding[name]),
            f"dispatch binding {name} must be a nonempty string -- refusing",
        )
    _require(
        binding.get("role") in EXECUTION_OBSERVATION_ROLES,
        "dispatch binding role must be 'author' or 'reviewer' -- refusing",
    )
    _require_hex64(binding.get("prompt_sha256"), "dispatch binding prompt_sha256")
    _require_hex64(binding.get("packet_sha256"), "dispatch binding packet_sha256")
    reviewer_only = ("authorship_receipt_id", "authorship_receipt_sha256", "rubric_sha256")
    if binding["role"] == "author":
        _require(
            isinstance(binding.get("slot_id"), str) and bool(binding["slot_id"]),
            "author dispatch binding slot_id must be a nonempty string -- refusing",
        )
        _require(
            binding.get("prompt_profile") == AUTHOR_PROMPT_PROFILE,
            "author dispatch binding must use the source-blind author prompt profile -- refusing",
        )
        _require(
            all(binding.get(field) is None for field in reviewer_only),
            "an author dispatch binding must not carry reviewer-only fields -- refusing",
        )
    else:
        _require(
            binding.get("slot_id") is None, "a reviewer dispatch binding must not carry an author slot_id -- refusing"
        )
        _require(
            binding.get("prompt_profile") == REVIEWER_PROMPT_PROFILE,
            "reviewer dispatch binding must use the source-blind reviewer prompt profile -- refusing",
        )
        _require(
            isinstance(binding.get("authorship_receipt_id"), str) and bool(binding["authorship_receipt_id"]),
            "reviewer dispatch binding authorship_receipt_id must be a nonempty string -- refusing",
        )
        _require_hex64(binding.get("authorship_receipt_sha256"), "dispatch binding authorship_receipt_sha256")
        _require_hex64(binding.get("rubric_sha256"), "dispatch binding rubric_sha256")


def record_execution_dispatch_binding(binding: dict[str, Any], *, conn: Any, is_pg: bool, commit: bool = True) -> None:
    """Idempotent, conflict-refusing write of one pre-execution dispatch
    authorization. Called only by the role-specific authorize methods, which
    recheck ``queued`` inside the same locked transaction."""
    validate_execution_dispatch_binding(binding)
    body_sha256 = _sha256_text(_canonical_json(binding))
    ph = "%s" if is_pg else "?"
    params = (
        binding["request_id"],
        binding["task_id"],
        binding["run_id"],
        binding["role"],
        body_sha256,
        _canonical_json(binding),
        _utc_now(),
    )
    columns = "(request_id, task_id, run_id, role, record_sha256, record_json, recorded_at)"
    values = f"({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})"
    if is_pg:
        conn.execute(
            f"INSERT INTO {EXECUTION_DISPATCH_BINDING_TABLE} {columns} VALUES {values} ON CONFLICT DO NOTHING",
            params,
        )
    else:
        conn.execute(f"INSERT OR IGNORE INTO {EXECUTION_DISPATCH_BINDING_TABLE} {columns} VALUES {values}", params)
        if commit:
            conn.commit()
    slot_owner = conn.execute(
        f"SELECT request_id FROM {EXECUTION_DISPATCH_BINDING_TABLE} WHERE task_id = {ph} AND run_id = {ph} AND role = {ph}",
        (binding["task_id"], binding["run_id"], binding["role"]),
    ).fetchone()
    if slot_owner is not None and _row_get(slot_owner, "request_id", 0) != binding["request_id"]:
        raise ExecutionDispatchBindingConflictError(
            f"slot task_id={binding['task_id']!r} run_id={binding['run_id']!r} role={binding['role']!r} is already bound to another request -- refusing"
        )
    existing = conn.execute(
        f"SELECT record_sha256 FROM {EXECUTION_DISPATCH_BINDING_TABLE} WHERE request_id = {ph}",
        (binding["request_id"],),
    ).fetchone()
    _require(existing is not None, "execution dispatch binding write did not persist -- refusing")
    if _row_get(existing, "record_sha256", 0) != body_sha256:
        raise ExecutionDispatchBindingConflictError(
            f"a different dispatch binding is already recorded for request_id={binding['request_id']!r} -- refusing"
        )


def resolve_execution_dispatch_binding(*, request_id: str, conn: Any, is_pg: bool) -> dict[str, Any] | None:
    _require(isinstance(request_id, str) and bool(request_id), "request_id must be a nonempty string -- refusing")
    ph = "%s" if is_pg else "?"
    row = conn.execute(
        f"SELECT record_json FROM {EXECUTION_DISPATCH_BINDING_TABLE} WHERE request_id = {ph}",
        (request_id,),
    ).fetchone()
    if row is None:
        return None
    binding = json.loads(_row_get(row, "record_json", 0))
    validate_execution_dispatch_binding(binding)
    return binding


# --- terminal execution observations ---------------------------------------


def validate_execution_observation(record: dict[str, Any]) -> None:
    from learn_ukrainian_v4_runtime.execution_identity import validate_execution_identity

    _require(isinstance(record, dict), "execution observation must be an object -- refusing")
    try:
        validate_execution_identity(record.get("runtime_identity"))
    except ValueError as exc:
        raise CanonicalAuthorityStoreError(str(exc)) from exc
    _require_hex64(record.get("trust_policy_sha256"), "execution observation trust policy")
    _require(
        isinstance(record, dict) and set(record) == EXECUTION_OBSERVATION_KEYS,
        f"execution observation record must declare exactly {sorted(EXECUTION_OBSERVATION_KEYS)} -- refusing (unexpected or missing key)",
    )
    _require(
        isinstance(record.get("task_id"), str) and bool(record["task_id"]),
        "execution observation task_id must be a nonempty string -- refusing",
    )
    _require(
        isinstance(record.get("run_id"), str) and bool(record["run_id"]),
        "execution observation run_id must be a nonempty string -- refusing",
    )
    _require(
        isinstance(record.get("attempt_id"), str) and bool(record["attempt_id"]),
        "execution observation attempt_id must be a nonempty string -- refusing",
    )
    _require(
        record.get("role") in EXECUTION_OBSERVATION_ROLES,
        "execution observation role must be 'author' or 'reviewer' -- refusing",
    )
    _require_hex64(record.get("row_content_sha256"), "execution observation row_content_sha256")
    reviewer_only = ("authorship_receipt_sha256", "rubric_sha256", "verdict")
    if record["role"] == "author":
        _require(
            all(record.get(field) is None for field in reviewer_only),
            "an author execution observation must not carry reviewer-only fields -- refusing",
        )
        _require(
            record.get("prompt_profile") == AUTHOR_PROMPT_PROFILE,
            "author observation must bind the source-blind author prompt profile -- refusing",
        )
    else:
        _require(
            all(record.get(field) is not None for field in reviewer_only),
            "a reviewer execution observation must carry every reviewer-only field -- refusing",
        )
        _require(
            record.get("prompt_profile") == REVIEWER_PROMPT_PROFILE,
            "reviewer observation must bind the source-blind reviewer prompt profile -- refusing",
        )


def _persist_execution_observation(
    record: dict[str, Any],
    *,
    conn: Any,
    is_pg: bool,
    request_id: str | None = None,
    commit: bool = True,
) -> None:
    """Low-level, idempotent, conflict-refusing, race-safe persistence of one
    execution observation.

    Private on purpose: the only production writer is the native runner
    via ``RequestExecutor.finalize_v4_runner_execution``, which derives
    every field from the process it actually spawned. Nothing public
    accepts a caller-built observation. Tests call this directly to exercise
    the negative issuer matrix against records they construct themselves --
    that is testing internals against an isolated ``tmp_path`` plane, never
    a production path (production reaches the canonical plane only through
    ``open_production_authority_store``, which requires the deployed
    PostgreSQL service credentials)."""
    validate_execution_observation(record)
    body_sha256 = _sha256_text(_canonical_json(record))
    ph = "%s" if is_pg else "?"
    params = (
        record["task_id"],
        record["run_id"],
        record["role"],
        body_sha256,
        _canonical_json(record),
        _utc_now(),
        request_id,
    )
    columns = "(task_id, run_id, role, record_sha256, record_json, recorded_at, request_id)"
    values = f"({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})"
    if is_pg:
        conn.execute(
            f"INSERT INTO {EXECUTION_OBSERVATION_TABLE} {columns} VALUES {values} ON CONFLICT (task_id, run_id, role) DO NOTHING",
            params,
        )
    else:
        conn.execute(f"INSERT OR IGNORE INTO {EXECUTION_OBSERVATION_TABLE} {columns} VALUES {values}", params)
        if commit:
            conn.commit()
    existing = conn.execute(
        f"SELECT record_sha256 FROM {EXECUTION_OBSERVATION_TABLE} WHERE task_id = {ph} AND run_id = {ph} AND role = {ph}",
        (record["task_id"], record["run_id"], record["role"]),
    ).fetchone()
    _require(existing is not None, "execution observation write did not persist -- refusing")
    if _row_get(existing, "record_sha256", 0) != body_sha256:
        raise ExecutionObservationConflictError(
            f"a different execution observation is already recorded for task_id={record['task_id']!r} run_id={record['run_id']!r} role={record['role']!r} -- refusing"
        )


def resolve_execution_observation(
    *, task_id: str, run_id: str, role: str, conn: Any, is_pg: bool
) -> dict[str, Any] | None:
    """The only sanctioned way ``v4_fleet_execution_authority`` learns an
    execution observation in production -- reads back exactly what
    ``_persist_execution_observation`` already durably wrote, or ``None`` if
    nothing was ever recorded for this key (an unknown task/run refuses
    before any key access at the caller)."""
    _require(isinstance(task_id, str) and bool(task_id), "task_id must be a nonempty string -- refusing")
    _require(isinstance(run_id, str) and bool(run_id), "run_id must be a nonempty string -- refusing")
    _require(role in EXECUTION_OBSERVATION_ROLES, "role must be 'author' or 'reviewer' -- refusing")
    ph = "%s" if is_pg else "?"
    row = conn.execute(
        f"SELECT record_json FROM {EXECUTION_OBSERVATION_TABLE} WHERE task_id = {ph} AND run_id = {ph} AND role = {ph}",
        (task_id, run_id, role),
    ).fetchone()
    if row is None:
        return None
    record = json.loads(_row_get(row, "record_json", 0))
    validate_execution_observation(record)
    return record


def resolve_execution_observation_for_attempt(*, attempt_id: str, conn: Any, is_pg: bool) -> dict[str, Any] | None:
    _require(isinstance(attempt_id, str) and bool(attempt_id), "attempt_id must be a nonempty string -- refusing")
    ph = "%s" if is_pg else "?"
    row = conn.execute(
        f"SELECT record_json FROM {EXECUTION_OBSERVATION_TABLE} WHERE request_id = "
        f"(SELECT request_id FROM {EXECUTION_ATTEMPT_TABLE} WHERE attempt_id = {ph})",
        (attempt_id,),
    ).fetchone()
    if row is None:
        return None
    record = json.loads(_row_get(row, "record_json", 0))
    validate_execution_observation(record)
    return record


# --- execution attempts (one-attempt capability) ---------------------------


def record_execution_attempt(
    *,
    attempt_id: str,
    request_id: str,
    task_id: str,
    run_id: str,
    role: str,
    capability_digest: str,
    binding_sha256: str,
    conn: Any,
    is_pg: bool,
    commit: bool = True,
) -> None:
    _require(isinstance(attempt_id, str) and bool(attempt_id), "attempt_id must be a nonempty string -- refusing")
    _require(isinstance(request_id, str) and bool(request_id), "request_id must be a nonempty string -- refusing")
    _require(role in EXECUTION_OBSERVATION_ROLES, "attempt role must be 'author' or 'reviewer' -- refusing")
    _require_hex64(capability_digest, "capability_digest")
    _require_hex64(binding_sha256, "binding_sha256")
    ph = "%s" if is_pg else "?"
    params = (attempt_id, request_id, task_id, run_id, role, "running", capability_digest, binding_sha256, _utc_now())
    columns = "(attempt_id, request_id, task_id, run_id, role, state, capability_digest, binding_sha256, started_at)"
    values = f"({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})"
    if is_pg:
        conn.execute(
            f"INSERT INTO {EXECUTION_ATTEMPT_TABLE} {columns} VALUES {values} ON CONFLICT DO NOTHING",
            params,
        )
    else:
        conn.execute(f"INSERT OR IGNORE INTO {EXECUTION_ATTEMPT_TABLE} {columns} VALUES {values}", params)
        if commit:
            conn.commit()
    existing = conn.execute(
        f"SELECT attempt_id, capability_digest FROM {EXECUTION_ATTEMPT_TABLE} WHERE request_id = {ph}",
        (request_id,),
    ).fetchone()
    _require(existing is not None, "execution attempt write did not persist -- refusing")
    if (
        _row_get(existing, "attempt_id", 0) != attempt_id
        or _row_get(existing, "capability_digest", 1) != capability_digest
    ):
        raise ExecutionAttemptConflictError(f"request {request_id!r} already has a V4 execution attempt -- refusing")


def mark_execution_attempt_terminal(*, attempt_id: str, conn: Any, is_pg: bool, commit: bool = True) -> None:
    ph = "%s" if is_pg else "?"
    conn.execute(
        f"UPDATE {EXECUTION_ATTEMPT_TABLE} SET state = 'terminal', terminal_at = {ph} WHERE attempt_id = {ph} AND state = 'running'",
        (_utc_now(), attempt_id),
    )
    if not is_pg and commit:
        conn.commit()


def resolve_active_attempt_by_capability_digest(
    *, capability_digest: str, conn: Any, is_pg: bool
) -> dict[str, Any] | None:
    _require_hex64(capability_digest, "capability_digest")
    ph = "%s" if is_pg else "?"
    row = conn.execute(
        f"SELECT attempt_id, request_id, task_id, run_id, role, state FROM {EXECUTION_ATTEMPT_TABLE} WHERE capability_digest = {ph}",
        (capability_digest,),
    ).fetchone()
    if row is None:
        return None
    return {
        "attempt_id": _row_get(row, "attempt_id", 0),
        "request_id": _row_get(row, "request_id", 1),
        "task_id": _row_get(row, "task_id", 2),
        "run_id": _row_get(row, "run_id", 3),
        "role": _row_get(row, "role", 4),
        "state": _row_get(row, "state", 5),
    }


def resolve_execution_attempt(*, attempt_id: str, conn: Any, is_pg: bool) -> dict[str, Any] | None:
    _require(isinstance(attempt_id, str) and bool(attempt_id), "attempt_id must be a nonempty string -- refusing")
    ph = "%s" if is_pg else "?"
    row = conn.execute(
        f"SELECT attempt_id, request_id, task_id, run_id, role, state FROM {EXECUTION_ATTEMPT_TABLE} WHERE attempt_id = {ph}",
        (attempt_id,),
    ).fetchone()
    if row is None:
        return None
    return {
        "attempt_id": _row_get(row, "attempt_id", 0),
        "request_id": _row_get(row, "request_id", 1),
        "task_id": _row_get(row, "task_id", 2),
        "run_id": _row_get(row, "run_id", 3),
        "role": _row_get(row, "role", 4),
        "state": _row_get(row, "state", 5),
    }


def persist_authorship_receipt(
    receipt: dict[str, Any], *, task_id: str, run_id: str, conn: Any, is_pg: bool, commit: bool = True
) -> None:
    _require(
        isinstance(receipt, dict) and isinstance(receipt.get("receipt_id"), str) and receipt["receipt_id"],
        "authorship receipt_id must be a nonempty string -- refusing",
    )
    from learn_ukrainian_v4_runtime import v4_a7_private_ledger as ledger

    observation = resolve_execution_observation(task_id=task_id, run_id=run_id, role="author", conn=conn, is_pg=is_pg)
    _require(observation is not None, "authorship origin is unresolved -- refusing")
    signed = receipt.get("execution_receipt", {})
    _require(
        signed.get("task_id") == task_id and signed.get("run_nonce") == run_id
        and signed.get("execution_result_sha256") == observation["raw_capture_sha256"],
        "authorship origin does not match canonical capture -- refusing",
    )
    _require(
        ledger.build_authorship_receipt(
            author_execution_receipt=signed, row_content_sha256=observation["row_content_sha256"]
        ) == receipt,
        "authorship receipt does not match verified execution -- refusing",
    )
    body_sha256 = _sha256_text(_canonical_json(receipt))
    ph = "%s" if is_pg else "?"
    params = (receipt["receipt_id"], task_id, run_id, body_sha256, _canonical_json(receipt), _utc_now())
    columns = "(receipt_id, task_id, run_id, record_sha256, record_json, recorded_at)"
    values = f"({ph}, {ph}, {ph}, {ph}, {ph}, {ph})"
    if is_pg:
        conn.execute(
            f"INSERT INTO {AUTHORSHIP_RECEIPT_TABLE} {columns} VALUES {values} ON CONFLICT DO NOTHING",
            params,
        )
    else:
        conn.execute(f"INSERT OR IGNORE INTO {AUTHORSHIP_RECEIPT_TABLE} {columns} VALUES {values}", params)
        if commit:
            conn.commit()
    existing = conn.execute(
        f"SELECT record_sha256 FROM {AUTHORSHIP_RECEIPT_TABLE} WHERE receipt_id = {ph}",
        (receipt["receipt_id"],),
    ).fetchone()
    _require(existing is not None, "authorship receipt write did not persist -- refusing")
    if _row_get(existing, "record_sha256", 0) != body_sha256:
        raise AuthorshipReceiptConflictError(
            f"a different authorship receipt is already recorded for {receipt['receipt_id']!r} -- refusing"
        )


def resolve_authorship_receipt(*, receipt_id: str, conn: Any, is_pg: bool) -> dict[str, Any] | None:
    _require(isinstance(receipt_id, str) and bool(receipt_id), "receipt_id must be a nonempty string -- refusing")
    ph = "%s" if is_pg else "?"
    row = conn.execute(
        f"SELECT record_json FROM {AUTHORSHIP_RECEIPT_TABLE} WHERE receipt_id = {ph}",
        (receipt_id,),
    ).fetchone()
    if row is None:
        return None
    return json.loads(_row_get(row, "record_json", 0))


# --- sanctioned Sources verifier-tool invocations --------------------------

# Only tools with a typed supporting-claim contract are sanctioned for
# positive V4 evidence. ``verify_quote``/``verify_source_attribution`` remain
# excluded (text arguments). ``vet_vocabulary`` and ``check_russian_shadow``
# are Sol-approved exclusions until they gain a typed supporting-claim
# contract -- they may still run as ordinary tools, but they never mint
# positive V4 evidence.
SANCTIONED_VERIFIER_TOOLS: dict[str, tuple[str, str]] = {
    "verify_word": ("word", "term"),
    "verify_words": ("words", "terms"),
    "verify_lemma": ("lemma", "term"),
    "verify_stress": ("word", "term"),
    "check_modern_form": ("word", "term"),
}

# A claimed lookup id shorter than this cannot be meaningfully distinguished
# from an incidental fragment of a rendered result, so it is refused rather
# than accepted on a substring coincidence.
MIN_LOOKUP_ID_LENGTH = 3
MAX_CLAIMED_LOOKUP_IDS = 64


def validate_sources_invocation(record: dict[str, Any]) -> None:
    _require(
        isinstance(record, dict) and set(record) == SOURCES_INVOCATION_KEYS,
        f"sources invocation record must declare exactly {sorted(SOURCES_INVOCATION_KEYS)} -- refusing (unexpected or missing key)",
    )
    _require(
        isinstance(record.get("invocation_id"), str) and bool(record["invocation_id"]),
        "sources invocation invocation_id must be a nonempty string -- refusing",
    )


def compute_invocation_id(
    *,
    tool_id: str,
    tool_version: str,
    attempt_id: str,
    ordinal: int,
    identifier: str,
    structured_result_sha256: str,
    lookup_ids: list[str],
) -> str:
    """Content-addressed invocation id. Bound to the authenticated attempt,
    never to a caller-declared request/row correlation."""
    payload = {
        "tool_id": tool_id,
        "tool_version": tool_version,
        "attempt_id": attempt_id,
        "ordinal": ordinal,
        "identifier": identifier,
        "structured_result_sha256": structured_result_sha256,
        "lookup_ids": sorted(lookup_ids),
    }
    return f"v4invocation:{_sha256_text(_canonical_json(payload))}"


def immutable_evidence_identifier(*, namespace: str, source_version: str, typed_result: dict[str, Any]) -> str:
    """Server-derived ``vesum:``/``sources:`` id. Never an echoed lexical argument."""
    _require(namespace in {"vesum", "sources"}, "evidence identifier namespace must be vesum or sources -- refusing")
    digest = _sha256_text(_canonical_json({"source_version": source_version, "typed_result": typed_result}))
    return f"{namespace}:{digest}"


def _appears_as_delimited_token(text: str, term: str) -> bool:
    """True only when ``term`` occurs in ``text`` bounded by non-word
    characters on both sides.

    A bare ``term in text`` substring test accepts an accidental fragment of
    an unrelated word (``"ok" in "книжок"``), which is exactly the
    "substring coincidence" a spoofed claim would exploit. Requiring
    delimiters removes that class of false positive without needing to
    understand the tool's rendered layout.
    """
    if not term:
        return False
    start = 0
    while True:
        index = text.find(term, start)
        if index < 0:
            return False
        before = text[index - 1] if index > 0 else ""
        after_index = index + len(term)
        after = text[after_index] if after_index < len(text) else ""
        if not _is_word_char(before) and not _is_word_char(after):
            return True
        start = index + 1


def _is_word_char(char: str) -> bool:
    return bool(char) and (char.isalnum() or char in {"_", "-", "'", "’"})


def next_sources_invocation_ordinal(*, attempt_id: str, conn: Any, is_pg: bool) -> int:
    ph = "%s" if is_pg else "?"
    row = conn.execute(
        f"SELECT COUNT(*) AS n FROM {SOURCES_INVOCATION_TABLE} WHERE attempt_id = {ph}",
        (attempt_id,),
    ).fetchone()
    return int(_row_get(row, "n", 0)) + 1 if row is not None else 1


def record_sources_invocation_from_typed_outcome(
    *,
    conn: Any,
    is_pg: bool,
    attempt_id: str,
    tool_name: str,
    tool_version: str,
    typed_outcome: dict[str, Any],
    commit: bool = True,
) -> dict[str, Any] | None:
    """The only Sources writer. Builds the record from a typed handler
    outcome and an authenticated attempt. Never accepts a caller row hash,
    request id, or lookup-id list. Unsuccessful dispositions are stored
    with ``success=false`` and are not issuable."""
    if tool_name not in SANCTIONED_VERIFIER_TOOLS or tool_name in EXCLUDED_POSITIVE_V4_TOOLS:
        return None
    if not isinstance(typed_outcome, dict):
        return None
    attempt = resolve_execution_attempt(attempt_id=attempt_id, conn=conn, is_pg=is_pg)
    if attempt is None or attempt.get("state") != "running":
        return None
    disposition = typed_outcome.get("disposition")
    if not isinstance(disposition, str) or not disposition:
        return None
    success = typed_outcome.get("success") is True and disposition == "supported"
    identifiers = typed_outcome.get("evidence_identifiers") if success else []
    if success:
        if not (isinstance(identifiers, list) and identifiers):
            return None
        if not all(
            isinstance(item, str) and (item.startswith("vesum:") or item.startswith("sources:")) for item in identifiers
        ):
            return None
        if len(set(identifiers)) != len(identifiers) or len(identifiers) > MAX_CLAIMED_LOOKUP_IDS:
            return None
    else:
        identifiers = []
    ordinal = next_sources_invocation_ordinal(attempt_id=attempt_id, conn=conn, is_pg=is_pg)
    structured_digest = _sha256_text(_canonical_json(typed_outcome))
    identifier = identifiers[0] if identifiers else f"sources:unsuccessful-{structured_digest}"
    recorded_at = _utc_now()
    tool_id = f"mcp__sources__{tool_name}"
    record = {
        "invocation_id": compute_invocation_id(
            tool_id=tool_id,
            tool_version=tool_version,
            attempt_id=attempt_id,
            ordinal=ordinal,
            identifier=identifier,
            structured_result_sha256=structured_digest,
            lookup_ids=list(identifiers) if identifiers else [identifier],
        ),
        "attempt_id": attempt_id,
        "ordinal": ordinal,
        "identifier": identifier,
        "tool_id": tool_id,
        "tool_version": tool_version,
        "structured_result_sha256": structured_digest,
        "lookup_ids": sorted(identifiers) if identifiers else [identifier],
        "success": success,
        "disposition": disposition,
        "recorded_at": recorded_at,
    }
    _persist_sources_invocation(record, conn=conn, is_pg=is_pg, commit=commit)
    return record


def record_sources_invocation_from_tool_result(
    *,
    conn: Any,
    is_pg: bool,
    tool_name: str,
    arguments: dict[str, Any],
    result_text: str,
    tool_version: str,
    request_id: str | None = None,
    row_content_sha256: str | None = None,
    claimed_lookup_ids: list[str] | None = None,
    attempt_id: str | None = None,
    typed_outcome: dict[str, Any] | None = None,
    commit: bool = True,
) -> dict[str, Any] | None:
    """Retired caller-correlation path. Production must call
    ``record_sources_invocation_from_typed_outcome`` with an authenticated
    attempt. Remaining keyword arguments are accepted only so stale callers
    fail closed instead of recording."""
    _ = arguments, result_text, request_id, row_content_sha256, claimed_lookup_ids
    if typed_outcome is None or not attempt_id:
        return None
    return record_sources_invocation_from_typed_outcome(
        conn=conn,
        is_pg=is_pg,
        attempt_id=attempt_id,
        tool_name=tool_name,
        tool_version=tool_version,
        typed_outcome=typed_outcome,
        commit=commit,
    )


def _persist_sources_invocation(record: dict[str, Any], *, conn: Any, is_pg: bool, commit: bool = True) -> None:
    """Low-level idempotent, conflict-refusing, race-safe persistence of one
    Sources invocation. Private for the same reason as
    ``_persist_execution_observation``: the only writer is ``record_sources_
    invocation_from_tool_result``, which builds the record itself."""
    validate_sources_invocation(record)
    body_sha256 = _sha256_text(_canonical_json(record))
    ph = "%s" if is_pg else "?"
    params = (
        record["invocation_id"],
        body_sha256,
        _canonical_json(record),
        record.get("recorded_at") or _utc_now(),
        record.get("attempt_id"),
    )
    columns = "(invocation_id, record_sha256, record_json, recorded_at, attempt_id)"
    values = f"({ph}, {ph}, {ph}, {ph}, {ph})"
    if is_pg:
        conn.execute(
            f"INSERT INTO {SOURCES_INVOCATION_TABLE} {columns} VALUES {values} ON CONFLICT (invocation_id) DO NOTHING",
            params,
        )
    else:
        conn.execute(f"INSERT OR IGNORE INTO {SOURCES_INVOCATION_TABLE} {columns} VALUES {values}", params)
        if commit:
            conn.commit()
    existing = conn.execute(
        f"SELECT record_sha256 FROM {SOURCES_INVOCATION_TABLE} WHERE invocation_id = {ph}",
        (record["invocation_id"],),
    ).fetchone()
    _require(existing is not None, "sources invocation write did not persist -- refusing")
    if _row_get(existing, "record_sha256", 0) != body_sha256:
        raise SourcesInvocationConflictError(
            f"a different sources invocation is already recorded for invocation_id={record['invocation_id']!r} -- refusing"
        )


def resolve_sources_invocation(*, invocation_id: str, conn: Any, is_pg: bool) -> dict[str, Any] | None:
    """The only sanctioned way ``v4_sources_authority`` learns a Sources
    invocation in production -- reads back exactly what ``record_sources_
    invocation_from_tool_result`` already durably wrote, or ``None`` if
    nothing was ever recorded for this ``invocation_id``."""
    _require(
        isinstance(invocation_id, str) and bool(invocation_id), "invocation_id must be a nonempty string -- refusing"
    )
    ph = "%s" if is_pg else "?"
    row = conn.execute(
        f"SELECT record_json FROM {SOURCES_INVOCATION_TABLE} WHERE invocation_id = {ph}",
        (invocation_id,),
    ).fetchone()
    if row is None:
        return None
    record = json.loads(_row_get(row, "record_json", 0))
    validate_sources_invocation(record)
    return record


def resolve_sources_invocation_tool_ids(*, attempt_id: str, conn: Any, is_pg: bool) -> list[str]:
    """Every distinct sanctioned verifier ``tool_id`` durably recorded for
    this authenticated attempt. Request-only correlation is not a source of
    V4 evidence."""
    _require(isinstance(attempt_id, str) and bool(attempt_id), "attempt_id must be a nonempty string -- refusing")
    ph = "%s" if is_pg else "?"
    rows = conn.execute(
        f"SELECT record_json FROM {SOURCES_INVOCATION_TABLE} WHERE attempt_id = {ph}",
        (attempt_id,),
    ).fetchall()
    tool_ids: set[str] = set()
    for row in rows or ():
        record = json.loads(_row_get(row, "record_json", 0))
        tool_id = record.get("tool_id")
        if isinstance(tool_id, str) and tool_id and record.get("success") is True:
            tool_ids.add(tool_id)
    return sorted(tool_ids)
