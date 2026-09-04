"""V4 canonical authority store (PR #7662 repair 6 -- operator-approved
architecture; see ``batch_state/briefs/v4-real-slot-mechanism-repair-6-
approval.md`` and the Sol advisor packet at ``batch_state/tasks/
v4-real-slot-authority-store-advisor.result``).

Before this module existed, no independently-controlled store proved a V4
fleet execution's terminal-event observation, exact runtime identity, or a
sanctioned Sources invocation actually happened -- ``v4_fleet_execution_
authority``/``v4_sources_authority`` accepted that evidence as plain
caller-supplied keyword arguments (``TaskExecutionState``, ``ResponseEnv
elope``, role observations, invocation fields), which only ever proved
internal self-consistency, never genuine execution. The operator approved
extending the live Fleet Comms Postgres plane (``StoreId.FLEET_COMMS``) as
the single canonical authority for both facts.

Two narrow, append-only, idempotent tables, two exclusive writer
boundaries:

* ``v4_execution_observations`` -- the sole durable record of one terminal
  V4 author/reviewer fleet execution. Written only by the real execution
  service boundary (``scripts.fleet_comms.request_executor.RequestExecutor
  .record_v4_execution_observation``), once a request's envelope is already
  durably confirmed ``CompletionState.COMPLETE``. Keyed by
  ``(task_id, run_id, role)``.
* ``v4_sources_invocations`` -- the sole durable record of one sanctioned
  ``mcp__sources__*`` verifier-tool invocation. Written only by the Sources
  MCP wire handler (``.mcp/servers/sources/server.py``), which independently
  re-checks the caller's claimed evidentiary fields are actually present in
  the tool's own genuine result before ever recording them (an "invocation
  attester", never a passthrough recorder -- the same pattern PR #7662
  repair 5 already applies to fleet execution). Keyed by ``invocation_id``.

Both writers are idempotent by primary key: re-recording a byte-identical
record is a silent no-op (needed for an at-least-once execution boundary
retrying after a crash); re-recording a *different* body under the same key
is refused (``ExecutionObservationConflictError``/``SourcesInvocation
ConflictError``) -- a caller can never silently overwrite a previously
recorded terminal fact. Both use the dialect-aware pg/sqlite ``INSERT ...
DO NOTHING`` + verify-by-readback idiom this project already uses
elsewhere, so the conflict check itself is race-safe against concurrent
writers, not merely a check-then-act sequence.

Resolution (``resolve_execution_observation``/``resolve_sources_
invocation``) is the ONLY way ``v4_fleet_execution_authority``/``v4_sources
_authority`` ever learn these facts in production -- neither resolver
accepts or trusts a caller-constructed record; both read back exactly what
a service boundary already durably wrote, or ``None`` if nothing was ever
recorded for that opaque key (which the calling authority module must treat
as an unconditional refusal before any key access, per the Sol acceptance
matrix).

Schema DDL lives in the same numbered-migration-ledger pattern the rest of
this plane uses (``scripts.fleet_comms.pg_schema`` for pg, ``scripts.fleet
_comms.migrations`` for sqlite); ``ArtifactStore.__init__`` already applies
both ledgers in full on every (non-readonly) open, so the two new tables
exist by the time any function here runs.

This module is deliberately connection-agnostic (every function takes an
already-open ``conn``/``is_pg`` pair) -- it never opens its own connection
or resolves its own plane root, so it never has to duplicate ``ArtifactStore
``/``RequestExecutor``'s root-override and authority-resolution logic (and
can never accidentally point a test at the shared default plane root
instead of an isolated ``tmp_path`` one). The sanctioned callers are
``ArtifactStore.record_v4_execution_observation``/``resolve_v4_execution_
observation``/``record_v4_sources_invocation``/``resolve_v4_sources_
invocation`` (and ``RequestExecutor``'s passthrough of the same), which
supply the connection/dialect from their own already-resolved authority.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

EXECUTION_OBSERVATION_TABLE = "v4_execution_observations"
SOURCES_INVOCATION_TABLE = "v4_sources_invocations"
EXECUTION_OBSERVATION_ROLES = frozenset({"author", "reviewer"})

# Exact key set for a canonical execution-observation record (same "declare
# exactly this key set" discipline every other durable/signed artifact in
# this project uses -- an extra or missing key refuses closed rather than
# silently passing through).
EXECUTION_OBSERVATION_KEYS = frozenset(
    {
        "task_id",
        "run_id",
        "role",
        "status",
        "return_code",
        "seat_or_model",
        "harness",
        "session_id",
        "completion_state",
        "terminal_event_observed",
        "process_returncode",
        "raw_capture_artifact_id",
        "raw_capture_sha256",
        "row_content_sha256",
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
        "row_content_sha256",
        "identifier",
        "tool_id",
        "tool_version",
        "request_id",
        "tool_result_sha256",
        "lookup_ids",
        "success",
    }
)


class CanonicalAuthorityStoreError(RuntimeError):
    """The canonical execution/Sources authority store refused an operation."""


class ExecutionObservationConflictError(CanonicalAuthorityStoreError):
    """A different execution observation is already recorded for this task_id/run_id/role."""


class SourcesInvocationConflictError(CanonicalAuthorityStoreError):
    """A different Sources invocation is already recorded for this invocation_id."""


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


def validate_execution_observation(record: dict[str, Any]) -> None:
    _require(
        isinstance(record, dict) and set(record) == EXECUTION_OBSERVATION_KEYS,
        f"execution observation record must declare exactly {sorted(EXECUTION_OBSERVATION_KEYS)} -- refusing (unexpected or missing key)",
    )
    _require(isinstance(record.get("task_id"), str) and bool(record["task_id"]), "execution observation task_id must be a nonempty string -- refusing")
    _require(isinstance(record.get("run_id"), str) and bool(record["run_id"]), "execution observation run_id must be a nonempty string -- refusing")
    _require(record.get("role") in EXECUTION_OBSERVATION_ROLES, "execution observation role must be 'author' or 'reviewer' -- refusing")
    reviewer_only = ("authorship_receipt_sha256", "rubric_sha256", "verdict")
    if record["role"] == "author":
        _require(all(record.get(field) is None for field in reviewer_only), "an author execution observation must not carry reviewer-only fields -- refusing")
    else:
        _require(all(record.get(field) is not None for field in reviewer_only), "a reviewer execution observation must carry every reviewer-only field -- refusing")


def compute_invocation_id(
    *,
    tool_id: str,
    tool_version: str,
    request_id: str,
    row_content_sha256: str,
    identifier: str,
    tool_result_sha256: str,
    lookup_ids: list[str],
) -> str:
    """The deterministic, content-addressed ``invocation_id`` for a Sources
    verifier-tool invocation record. Both the writer (the Sources MCP wire
    handler, which knows every one of these fields at call time) and any
    later caller building an evidence request (who independently knows
    ``request_id`` -- its own claim -- and can hash the tool's returned
    result text itself) compute the identical id from the same public
    formula; nothing about ``invocation_id`` is a secret or a database
    auto-increment a caller would have to be told out-of-band."""
    payload = {
        "tool_id": tool_id,
        "tool_version": tool_version,
        "request_id": request_id,
        "row_content_sha256": row_content_sha256,
        "identifier": identifier,
        "tool_result_sha256": tool_result_sha256,
        "lookup_ids": sorted(lookup_ids),
    }
    return f"v4invocation:{_sha256_text(_canonical_json(payload))}"


def validate_sources_invocation(record: dict[str, Any]) -> None:
    _require(
        isinstance(record, dict) and set(record) == SOURCES_INVOCATION_KEYS,
        f"sources invocation record must declare exactly {sorted(SOURCES_INVOCATION_KEYS)} -- refusing (unexpected or missing key)",
    )
    _require(isinstance(record.get("invocation_id"), str) and bool(record["invocation_id"]), "sources invocation invocation_id must be a nonempty string -- refusing")


def record_execution_observation(record: dict[str, Any], *, conn: Any, is_pg: bool) -> None:
    """Idempotent, conflict-refusing, race-safe write of one durable
    execution observation. Called only by the real execution service
    boundary (``ArtifactStore``/``RequestExecutor``'s ``record_v4_execution_
    observation``) -- never by ``v4_fleet_execution_authority`` or any V4
    production issuer, which only ever *resolve* an already-recorded
    observation."""
    validate_execution_observation(record)
    body_sha256 = _sha256_text(_canonical_json(record))
    ph = "%s" if is_pg else "?"
    params = (record["task_id"], record["run_id"], record["role"], body_sha256, _canonical_json(record), _utc_now())
    if is_pg:
        conn.execute(
            f"""INSERT INTO {EXECUTION_OBSERVATION_TABLE}
                (task_id, run_id, role, record_sha256, record_json, recorded_at)
                VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph})
                ON CONFLICT (task_id, run_id, role) DO NOTHING""",
            params,
        )
    else:
        conn.execute(
            f"""INSERT OR IGNORE INTO {EXECUTION_OBSERVATION_TABLE}
                (task_id, run_id, role, record_sha256, record_json, recorded_at)
                VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph})""",
            params,
        )
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


def resolve_execution_observation(*, task_id: str, run_id: str, role: str, conn: Any, is_pg: bool) -> dict[str, Any] | None:
    """The only sanctioned way ``v4_fleet_execution_authority`` learns an
    execution observation in production -- reads back exactly what
    ``record_execution_observation`` already durably wrote, or ``None`` if
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


def record_sources_invocation(record: dict[str, Any], *, conn: Any, is_pg: bool) -> None:
    """Idempotent, conflict-refusing, race-safe write of one durable Sources
    verifier-tool invocation. Called only by the Sources MCP wire handler,
    after it has independently confirmed the claimed evidentiary fields are
    present in the tool's own genuine result."""
    validate_sources_invocation(record)
    body_sha256 = _sha256_text(_canonical_json(record))
    ph = "%s" if is_pg else "?"
    params = (record["invocation_id"], body_sha256, _canonical_json(record), _utc_now())
    if is_pg:
        conn.execute(
            f"""INSERT INTO {SOURCES_INVOCATION_TABLE}
                (invocation_id, record_sha256, record_json, recorded_at)
                VALUES ({ph}, {ph}, {ph}, {ph})
                ON CONFLICT (invocation_id) DO NOTHING""",
            params,
        )
    else:
        conn.execute(
            f"""INSERT OR IGNORE INTO {SOURCES_INVOCATION_TABLE}
                (invocation_id, record_sha256, record_json, recorded_at)
                VALUES ({ph}, {ph}, {ph}, {ph})""",
            params,
        )
        conn.commit()
    existing = conn.execute(
        f"SELECT record_sha256 FROM {SOURCES_INVOCATION_TABLE} WHERE invocation_id = {ph}",
        (record["invocation_id"],),
    ).fetchone()
    _require(existing is not None, "sources invocation write did not persist -- refusing")
    if _row_get(existing, "record_sha256", 0) != body_sha256:
        raise SourcesInvocationConflictError(f"a different sources invocation is already recorded for invocation_id={record['invocation_id']!r} -- refusing")


def resolve_sources_invocation(*, invocation_id: str, conn: Any, is_pg: bool) -> dict[str, Any] | None:
    """The only sanctioned way ``v4_sources_authority`` learns a Sources
    invocation in production -- reads back exactly what ``record_sources_
    invocation`` already durably wrote, or ``None`` if nothing was ever
    recorded for this ``invocation_id``."""
    _require(isinstance(invocation_id, str) and bool(invocation_id), "invocation_id must be a nonempty string -- refusing")
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
