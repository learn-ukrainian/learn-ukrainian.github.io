"""V4 canonical authority store (PR #7662 repair 6/7 -- operator-approved
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

Three narrow, idempotent, conflict-refusing tables:

* ``v4_execution_dispatch_bindings`` -- the *pre-execution* authorization
  for one V4 fleet request: which slot (``task_id``/``run_id``/``role``),
  which row/packet, which model/harness the dispatch boundary expects. It
  is written by ``RequestExecutor.authorize_v4_execution`` while the
  request is still ``queued``, so it can never be minted after the fact to
  describe an execution that already happened. Keyed by ``request_id``,
  with a uniqueness constraint on ``(task_id, run_id, role)`` so two
  requests can never both claim one slot.
* ``v4_execution_observations`` -- the sole durable record of one terminal
  V4 author/reviewer fleet execution. Written ONLY by
  ``RequestExecutor._finalize_capture``, inside the same transaction that
  finalizes the request, from facts that boundary itself derives (see
  ``RequestExecutor._build_v4_execution_observation``): the envelope the
  adapter-conformance layer computed, the artifact digest the store
  actually persisted, the runtime model identity read out of the provider's
  own capture events, the harness implied by the registry-resolved
  recipient, and the pre-frozen dispatch binding. Keyed by
  ``(task_id, run_id, role)``.
* ``v4_sources_invocations`` -- the sole durable record of one sanctioned
  ``mcp__sources__*`` verifier-tool invocation. Written only by the Sources
  MCP wire handler through ``record_sources_invocation_from_tool_result``,
  which builds the record itself out of the arguments the tool was really
  called with and the tool's own genuine result text. Keyed by
  ``invocation_id``.

**There is no public function anywhere that accepts a caller-built
execution-observation or Sources-invocation record and writes it.** Both
writers construct the record from primary evidence; the private
``_persist_execution_observation``/``_persist_sources_invocation``
primitives exist only so this module's own writers (and this project's
tests, which exercise validation branches directly) can reach the SQL. The
remaining enforcement below that line is the credential boundary the
operator approved: the canonical authority is the live Fleet Comms
PostgreSQL plane, reachable only through the deployed service
configuration (``open_production_authority_store``), so a process without
the service account's plane credentials cannot write these tables at all.
That, not a naming convention, is what makes the writer exclusive; the
runbook states this residual explicitly.

Both writes are idempotent by primary key: re-recording a byte-identical
record is a silent no-op (needed for an at-least-once execution boundary
retrying after a crash); re-recording a *different* body under the same key
is refused (``ExecutionObservationConflictError``/``SourcesInvocation
ConflictError``/``ExecutionDispatchBindingConflictError``) -- a caller can
never silently overwrite a previously recorded terminal fact. All use the
dialect-aware pg/sqlite ``INSERT ... DO NOTHING`` + verify-by-readback
idiom this project already uses elsewhere, so the conflict check itself is
race-safe against concurrent writers, not merely a check-then-act sequence.

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
both ledgers in full on every (non-readonly) open, so the tables exist by
the time any function here runs.

Every function except ``open_production_authority_store`` is deliberately
connection-agnostic (it takes an already-open ``conn``/``is_pg`` pair) --
it never opens its own connection or resolves its own plane root, so it
never has to duplicate ``ArtifactStore``/``RequestExecutor``'s
authority-resolution logic (and can never accidentally point a test at the
shared default plane root instead of an isolated ``tmp_path`` one).
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import re
from datetime import UTC, datetime
from typing import Any

EXECUTION_OBSERVATION_TABLE = "v4_execution_observations"
SOURCES_INVOCATION_TABLE = "v4_sources_invocations"
EXECUTION_DISPATCH_BINDING_TABLE = "v4_execution_dispatch_bindings"
EXECUTION_OBSERVATION_ROLES = frozenset({"author", "reviewer"})

HEX64_RE = re.compile(r"^[a-f0-9]{64}$")

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

# The pre-execution dispatch authorization. Deliberately carries only the
# facts that are genuinely knowable BEFORE the model runs: which slot, which
# frozen row/packet, and which model/harness the dispatch boundary intends.
# Everything an execution *produces* (session id, result digest, terminal
# state, return code, verdict, verification tool ids) is absent here by
# design -- those are derived at finalization from the runtime's own
# evidence and can never be pre-declared.
EXECUTION_DISPATCH_BINDING_KEYS = frozenset(
    {
        "request_id",
        "task_id",
        "run_id",
        "role",
        "expected_seat_or_model",
        "expected_harness",
        "row_content_sha256",
        "packet_sha256",
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
    _require(isinstance(value, str) and bool(HEX64_RE.match(value)), f"{name} must be a lowercase sha256 hex digest -- refusing")


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
    from scripts.control_plane.storage import Authority, StoreId, resolve_authority
    from scripts.fleet_comms.artifacts import ArtifactStore

    authority = resolve_authority(StoreId.FLEET_COMMS)
    if authority is not Authority.PG:
        raise CanonicalAuthorityUnavailableError(
            "V4 production authority requires the operator-approved canonical Fleet "
            f"Comms PostgreSQL plane; the resolved authority is {authority.value!r} "
            "-- refusing (no SQLite/local/caller-selected fallback)"
        )
    try:
        store = ArtifactStore(readonly=not write)
    except Exception as exc:
        raise CanonicalAuthorityUnavailableError(
            "V4 production authority: the canonical Fleet Comms PostgreSQL plane is "
            "unavailable -- refusing (no fallback authority)"
        ) from exc
    if store.authority is not Authority.PG:
        with contextlib.suppress(Exception):
            store.close()
        raise CanonicalAuthorityUnavailableError(
            "V4 production authority opened a non-PostgreSQL store -- refusing"
        )
    return store


# --- pre-execution dispatch authorization ----------------------------------


def validate_execution_dispatch_binding(binding: dict[str, Any]) -> None:
    _require(
        isinstance(binding, dict) and set(binding) == EXECUTION_DISPATCH_BINDING_KEYS,
        f"execution dispatch binding must declare exactly {sorted(EXECUTION_DISPATCH_BINDING_KEYS)} -- refusing (unexpected or missing key)",
    )
    for name in ("request_id", "task_id", "run_id", "expected_seat_or_model", "expected_harness"):
        _require(isinstance(binding.get(name), str) and bool(binding[name]), f"dispatch binding {name} must be a nonempty string -- refusing")
    _require(binding.get("role") in EXECUTION_OBSERVATION_ROLES, "dispatch binding role must be 'author' or 'reviewer' -- refusing")
    for name in ("row_content_sha256", "packet_sha256"):
        _require_hex64(binding.get(name), f"dispatch binding {name}")
    reviewer_only = ("authorship_receipt_sha256", "rubric_sha256")
    if binding["role"] == "author":
        _require(
            all(binding.get(field) is None for field in reviewer_only),
            "an author dispatch binding must not carry reviewer-only fields -- refusing",
        )
    else:
        for field in reviewer_only:
            _require_hex64(binding.get(field), f"dispatch binding {field}")


def record_execution_dispatch_binding(binding: dict[str, Any], *, conn: Any, is_pg: bool, commit: bool = True) -> None:
    """Idempotent, conflict-refusing write of one pre-execution dispatch
    authorization. Called only by ``RequestExecutor.authorize_v4_execution``,
    which additionally requires the request to still be ``queued``."""
    validate_execution_dispatch_binding(binding)
    body_sha256 = _sha256_text(_canonical_json(binding))
    ph = "%s" if is_pg else "?"
    params = (binding["request_id"], binding["task_id"], binding["run_id"], binding["role"], body_sha256, _canonical_json(binding), _utc_now())
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

    Private on purpose: the only production writer is ``RequestExecutor.
    _finalize_capture``, which *derives* every field of ``record`` from its
    own execution/capture/dispatch state before calling here. Nothing public
    accepts a caller-built observation. Tests call this directly to exercise
    the negative issuer matrix against records they construct themselves --
    that is testing internals against an isolated ``tmp_path`` plane, never
    a production path (production reaches the canonical plane only through
    ``open_production_authority_store``, which requires the deployed
    PostgreSQL service credentials)."""
    validate_execution_observation(record)
    body_sha256 = _sha256_text(_canonical_json(record))
    ph = "%s" if is_pg else "?"
    params = (record["task_id"], record["run_id"], record["role"], body_sha256, _canonical_json(record), _utc_now(), request_id)
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


def resolve_execution_observation(*, task_id: str, run_id: str, role: str, conn: Any, is_pg: bool) -> dict[str, Any] | None:
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


# --- sanctioned Sources verifier-tool invocations --------------------------

# Only tools whose primary argument is itself a lexical identifier are
# sanctioned for V4 evidence. ``verify_quote``/``verify_source_attribution``
# are deliberately NOT here (PR #7662 repair 7): their primary argument is
# quote/claim *text*, which must never enter a record documented as
# text-free, and whose presence in a rendered result cannot be policed
# without handling that text. Each entry maps the tool's bare name to the
# argument key the invocation identifier is derived from, and whether that
# argument is a single term or a list of terms.
SANCTIONED_VERIFIER_TOOLS: dict[str, tuple[str, str]] = {
    "verify_word": ("word", "term"),
    "verify_words": ("words", "terms"),
    "verify_lemma": ("lemma", "term"),
    "verify_stress": ("word", "term"),
    "vet_vocabulary": ("words", "terms"),
    "check_modern_form": ("word", "term"),
    "check_russian_shadow": ("word", "term"),
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
    _require(isinstance(record.get("invocation_id"), str) and bool(record["invocation_id"]), "sources invocation invocation_id must be a nonempty string -- refusing")


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


def derive_invocation_identifier(*, tool_name: str, arguments: dict[str, Any]) -> tuple[str, tuple[str, ...]] | None:
    """Derive the invocation identifier from the arguments the tool was
    ACTUALLY called with -- never from a caller-declared identifier field.

    Returns ``(identifier, terms_that_must_appear_in_the_result)`` or
    ``None`` when the tool is unsanctioned or its primary argument is
    missing/malformed. For a single-term tool the identifier is the term
    itself; for a list tool it is a digest of the canonical sorted term
    list, so a long word list never lands in the record verbatim.
    """
    spec = SANCTIONED_VERIFIER_TOOLS.get(tool_name)
    if spec is None or not isinstance(arguments, dict):
        return None
    argument_key, kind = spec
    value = arguments.get(argument_key)
    if kind == "term":
        if not isinstance(value, str) or not value.strip():
            return None
        term = value.strip()
        return term, (term,)
    if not isinstance(value, list) or not value:
        return None
    terms = [item.strip() for item in value if isinstance(item, str) and item.strip()]
    if len(terms) != len(value):
        return None
    unique_terms = tuple(sorted(set(terms)))
    identifier = f"v4termset:{_sha256_text(_canonical_json(list(unique_terms)))}"
    return identifier, unique_terms


def record_sources_invocation_from_tool_result(
    *,
    conn: Any,
    is_pg: bool,
    tool_name: str,
    arguments: dict[str, Any],
    result_text: str,
    tool_version: str,
    request_id: str,
    row_content_sha256: str,
    claimed_lookup_ids: list[str],
    commit: bool = True,
) -> dict[str, Any] | None:
    """Independently build and record ONE genuine Sources invocation.

    This is the only Sources writer. It never accepts a caller-built record
    or a caller-declared identifier: the identifier comes from the arguments
    the tool was really invoked with, ``tool_result_sha256`` is hashed from
    the tool's own returned text, ``tool_version`` is the running server's
    own code digest, and every claimed lookup id must actually occur in that
    result as a delimited token. Returns the recorded record, or ``None``
    when nothing may be recorded (unsanctioned tool, unusable arguments,
    empty result, or an unconfirmed claim). ``request_id`` is the caller's
    own correlation id -- it is stored as declared correlation and is the
    one field here the server cannot independently observe (see the
    runbook's residuals).
    """
    derived = derive_invocation_identifier(tool_name=tool_name, arguments=arguments)
    if derived is None:
        return None
    identifier, required_terms = derived
    if not isinstance(result_text, str) or not result_text.strip():
        return None
    if not (isinstance(request_id, str) and request_id):
        return None
    if not (isinstance(row_content_sha256, str) and HEX64_RE.match(row_content_sha256)):
        return None
    if not (isinstance(claimed_lookup_ids, list) and claimed_lookup_ids):
        return None
    if len(claimed_lookup_ids) > MAX_CLAIMED_LOOKUP_IDS:
        return None
    if not all(isinstance(item, str) and len(item) >= MIN_LOOKUP_ID_LENGTH for item in claimed_lookup_ids):
        return None
    if len(set(claimed_lookup_ids)) != len(claimed_lookup_ids):
        return None
    for term in (*required_terms, *claimed_lookup_ids):
        if not _appears_as_delimited_token(result_text, term):
            return None

    tool_id = f"mcp__sources__{tool_name}"
    record = {
        "invocation_id": compute_invocation_id(
            tool_id=tool_id,
            tool_version=tool_version,
            request_id=request_id,
            row_content_sha256=row_content_sha256,
            identifier=identifier,
            tool_result_sha256=_sha256_text(result_text),
            lookup_ids=list(claimed_lookup_ids),
        ),
        "row_content_sha256": row_content_sha256,
        "identifier": identifier,
        "tool_id": tool_id,
        "tool_version": tool_version,
        "request_id": request_id,
        "tool_result_sha256": _sha256_text(result_text),
        "lookup_ids": sorted(claimed_lookup_ids),
        "success": True,
    }
    _persist_sources_invocation(record, conn=conn, is_pg=is_pg, commit=commit)
    return record


def _persist_sources_invocation(record: dict[str, Any], *, conn: Any, is_pg: bool, commit: bool = True) -> None:
    """Low-level idempotent, conflict-refusing, race-safe persistence of one
    Sources invocation. Private for the same reason as
    ``_persist_execution_observation``: the only writer is ``record_sources_
    invocation_from_tool_result``, which builds the record itself."""
    validate_sources_invocation(record)
    body_sha256 = _sha256_text(_canonical_json(record))
    ph = "%s" if is_pg else "?"
    params = (record["invocation_id"], body_sha256, _canonical_json(record), _utc_now(), record.get("request_id"))
    columns = "(invocation_id, record_sha256, record_json, recorded_at, request_id)"
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
        raise SourcesInvocationConflictError(f"a different sources invocation is already recorded for invocation_id={record['invocation_id']!r} -- refusing")


def resolve_sources_invocation(*, invocation_id: str, conn: Any, is_pg: bool) -> dict[str, Any] | None:
    """The only sanctioned way ``v4_sources_authority`` learns a Sources
    invocation in production -- reads back exactly what ``record_sources_
    invocation_from_tool_result`` already durably wrote, or ``None`` if
    nothing was ever recorded for this ``invocation_id``."""
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


def resolve_sources_invocation_tool_ids(*, request_id: str, conn: Any, is_pg: bool) -> list[str]:
    """Every distinct sanctioned verifier ``tool_id`` durably recorded for
    ``request_id``. This is how ``RequestExecutor`` derives an observation's
    ``verification_tool_ids`` from canonical evidence instead of accepting a
    caller's list."""
    _require(isinstance(request_id, str) and bool(request_id), "request_id must be a nonempty string -- refusing")
    ph = "%s" if is_pg else "?"
    rows = conn.execute(
        f"SELECT record_json FROM {SOURCES_INVOCATION_TABLE} WHERE request_id = {ph}",
        (request_id,),
    ).fetchall()
    tool_ids: set[str] = set()
    for row in rows or ():
        record = json.loads(_row_get(row, "record_json", 0))
        tool_id = record.get("tool_id")
        if isinstance(tool_id, str) and tool_id and record.get("success") is True:
            tool_ids.add(tool_id)
    return sorted(tool_ids)
