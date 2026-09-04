"""Request / delivery executor skeleton (Fleet Comms PR-D / #5512).

One path for foreground and background work: create a durable request, resolve
endpoint (incl. permanent Gemini→AGY retirement), run adapter conformance on a
raw capture, store the raw artifact, and advance request state only on proven
completion.

Bridge defaults remain legacy. Opt-in message plane (PR-E) may shadow/dual_write
via ``scripts.fleet_comms.message_plane`` without flipping production defaults.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from scripts.control_plane.storage import (
    Authority,
    ControlPlaneUnsupportedComponentError,
    StoreId,
    assert_component_supported,
)
from scripts.fleet_comms.adapter_conformance import CaptureInput, conform, parse_capture_events
from scripts.fleet_comms.artifacts import ArtifactStore
from scripts.fleet_comms.contracts import CompletionState, ResponseEnvelope, new_id
from scripts.fleet_comms.endpoints import EndpointRegistry, load_endpoint_registry
from scripts.fleet_comms.migrations import apply_migrations
from scripts.fleet_comms.pg_schema import apply_pg_schema

REQUEST_STATES = frozenset(
    {"queued", "running", "complete", "incomplete", "failed", "expired", "dead_lettered"}
)


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True, slots=True)
class RequestRecord:
    request_id: str
    request_message_id: str
    requested_recipient: str
    resolved_recipient: str
    state: str
    expires_at: str
    completion_state: str
    created_at: str
    updated_at: str
    envelope: ResponseEnvelope | None = None
    raw_capture_artifact_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "request_id": self.request_id,
            "request_message_id": self.request_message_id,
            "requested_recipient": self.requested_recipient,
            "resolved_recipient": self.resolved_recipient,
            "state": self.state,
            "expires_at": self.expires_at,
            "completion_state": self.completion_state,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "raw_capture_artifact_id": self.raw_capture_artifact_id,
        }
        if self.envelope is not None:
            payload["envelope"] = self.envelope.to_dict()
        return payload


class RequestExecutorError(RuntimeError):
    """Request executor refused an operation."""


class RequestExecutor:
    """Durable request lifecycle over communications SQLite + artifact store."""

    def __init__(
        self,
        *,
        store: ArtifactStore | None = None,
        registry: EndpointRegistry | None = None,
        root: Path | None = None,
        default_ttl_seconds: int | None = None,
    ) -> None:
        # #7482 interlock, extended by the public #605 slice: pg construction
        # is now allowed (create_request/get_request are dialect-aware), but
        # an injected store must match the CURRENTLY resolved authority in
        # either direction — a store opened under sqlite must not smuggle
        # sqlite SQL into a pg-configured plane (CF r1 finding, PR #7498),
        # and a pg store must not be driven under a sqlite-resolved plane.
        self._authority = assert_component_supported(StoreId.FLEET_COMMS, "request_executor")
        if store is not None and store.authority is not self._authority:
            raise ControlPlaneUnsupportedComponentError(
                "control-plane store 'fleet_comms': injected artifact store "
                f"authority {store.authority.value!r} does not match resolved "
                f"authority {self._authority.value!r} for component "
                "'request_executor' (#7482/#605 mismatch guard)"
            )
        self.store = store or ArtifactStore(root=root)
        self._owns_store = store is None
        self.registry = registry or load_endpoint_registry()
        self.default_ttl_seconds = default_ttl_seconds
        self._conn = self.store.connection
        if self._owns_store:
            if self._authority is Authority.PG:
                apply_pg_schema(self._conn)
            else:
                apply_migrations(self._conn)

    @property
    def authority(self) -> Authority:
        """Resolved control-plane authority this executor opened with (#605)."""
        return self._authority

    @property
    def _is_pg(self) -> bool:
        return self._authority is Authority.PG

    def _commit(self) -> None:
        # psycopg pg connections are autocommit (ArtifactStore pg pattern):
        # bare statements commit on their own and explicit transactions
        # commit at block exit. Only sqlite needs an explicit commit here.
        if not self._is_pg:
            self._conn.commit()

    def close(self) -> None:
        if self._owns_store:
            self.store.close()

    def __enter__(self) -> RequestExecutor:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def create_request(
        self,
        *,
        recipient: str,
        body: str,
        sender: str = "request-executor",
        ttl_seconds: int | None = None,
        conversation_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RequestRecord:
        endpoint, matched_name = self.registry.resolve(recipient)
        # resolve(): live → (endpoint, endpoint.name); retired → (successor, retired_name).
        requested = matched_name
        resolved = endpoint.name
        ttl = ttl_seconds
        if ttl is None:
            ttl = self.default_ttl_seconds if self.default_ttl_seconds is not None else endpoint.default_ttl_seconds
        now = _utc_now()
        expires = now + timedelta(seconds=int(ttl))
        conv = conversation_id or new_id("conversation")
        msg_id = new_id("message")
        req_id = new_id("request")
        now_s = _iso(now)
        expires_s = _iso(expires)

        if self._is_pg:
            # psycopg connection is autocommit (ArtifactStore pg pattern);
            # the three inserts share ONE explicit transaction.
            with self._conn.transaction():
                self._conn.execute(
                    "INSERT INTO conversations(conversation_id, created_at, source, title)"
                    " VALUES (%s, %s, %s, %s) ON CONFLICT (conversation_id) DO NOTHING",
                    (conv, now_s, "request-executor", None),
                )
                self._conn.execute(
                    """INSERT INTO comms_messages(
                        message_id, conversation_id, kind, sender, recipient, body_inline,
                        content_sha256, metadata_json, created_at
                    ) VALUES (%s, %s, 'request', %s, %s, %s, %s, %s, %s)""",
                    (
                        msg_id,
                        conv,
                        sender,
                        resolved,
                        body,
                        None,
                        json.dumps(metadata or {}, sort_keys=True),
                        now_s,
                    ),
                )
                self._conn.execute(
                    """INSERT INTO requests(
                        request_id, request_message_id, requested_recipient, resolved_recipient,
                        state, expires_at, completion_state, invocation_spec_json, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, 'queued', %s, 'unknown', %s, %s, %s)""",
                    (
                        req_id,
                        msg_id,
                        requested,
                        resolved,
                        expires_s,
                        json.dumps(
                            {
                                "recipient": recipient,
                                "requested_recipient": requested,
                                "resolved_recipient": resolved,
                                "ttl_seconds": ttl,
                            },
                            sort_keys=True,
                        ),
                        now_s,
                        now_s,
                    ),
                )
            return self.get_request(req_id)

        self._conn.execute(
            "INSERT OR IGNORE INTO conversations(conversation_id, created_at, source, title) VALUES (?, ?, ?, ?)",
            (conv, now_s, "request-executor", None),
        )
        self._conn.execute(
            """INSERT INTO comms_messages(
                message_id, conversation_id, kind, sender, recipient, body_inline,
                content_sha256, metadata_json, created_at
            ) VALUES (?, ?, 'request', ?, ?, ?, ?, ?, ?)""",
            (
                msg_id,
                conv,
                sender,
                resolved,
                body,
                None,
                json.dumps(metadata or {}, sort_keys=True),
                now_s,
            ),
        )
        self._conn.execute(
            """INSERT INTO requests(
                request_id, request_message_id, requested_recipient, resolved_recipient,
                state, expires_at, completion_state, invocation_spec_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 'queued', ?, 'unknown', ?, ?, ?)""",
            (
                req_id,
                msg_id,
                requested,
                resolved,
                expires_s,
                json.dumps(
                    {
                        "recipient": recipient,
                        "requested_recipient": requested,
                        "resolved_recipient": resolved,
                        "ttl_seconds": ttl,
                    },
                    sort_keys=True,
                ),
                now_s,
                now_s,
            ),
        )
        self._conn.commit()
        return self.get_request(req_id)

    def get_request(self, request_id: str) -> RequestRecord:
        placeholder = "%s" if self._is_pg else "?"
        row = self._conn.execute(
            f"SELECT * FROM requests WHERE request_id = {placeholder}", (request_id,)
        ).fetchone()
        if row is None:
            raise RequestExecutorError(f"request not found: {request_id}")
        return RequestRecord(
            request_id=str(row["request_id"]),
            request_message_id=str(row["request_message_id"]),
            requested_recipient=str(row["requested_recipient"]),
            resolved_recipient=str(row["resolved_recipient"]),
            state=str(row["state"]),
            expires_at=str(row["expires_at"]),
            completion_state=str(row["completion_state"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    def execute_capture(
        self,
        request_id: str,
        *,
        adapter: str | None = None,
        stdout: str = "",
        stderr: str = "",
        returncode: int | None = 0,
        events: tuple[dict[str, Any], ...] = (),
        raw_bytes: bytes | None = None,
        session_id: str | None = None,
        reclaim: bool = False,
        reclaim_stale_after_seconds: int = 7200,
    ) -> RequestRecord:
        """Run adapter conformance on a capture and persist the outcome.

        Production adapters will stream into the artifact store then call this
        with the same bytes. Tests inject fixtures directly.

        #7485 exactly-once: execution starts with an ATOMIC claim — one
        conditional UPDATE from ``queued`` to ``running``. Two concurrent
        executors can no longer both observe ``queued`` and both run the
        capture. A request already ``running`` is claimable only with
        ``reclaim=True`` (explicit crash recovery by the caller).
        """
        ph = "%s" if self._is_pg else "?"
        req = self.get_request(request_id)
        now_s = _iso(_utc_now())
        if req.expires_at < now_s and req.state in {"queued", "running"}:
            self._set_state(request_id, "expired", CompletionState.UNKNOWN)
            raise RequestExecutorError(f"request {request_id} expired")
        if reclaim:
            # #7485 CF r1: reclaim must never steal an ACTIVELY running
            # request — only one whose claim has gone stale (crashed
            # executor). Staleness = updated_at older than the floor.
            stale_cutoff = _iso(
                _utc_now() - timedelta(seconds=max(0, reclaim_stale_after_seconds))
            )
            cursor = self._conn.execute(
                f"""UPDATE requests SET state = 'running', completion_state = {ph},
                   updated_at = {ph}
                   WHERE request_id = {ph} AND expires_at >= {ph}
                   AND (state = 'queued'
                        OR (state = 'running' AND updated_at <= {ph}))""",
                (CompletionState.UNKNOWN.value, now_s, request_id, now_s, stale_cutoff),
            )
        else:
            cursor = self._conn.execute(
                f"""UPDATE requests SET state = 'running', completion_state = {ph},
                   updated_at = {ph}
                   WHERE request_id = {ph} AND state = 'queued'
                   AND expires_at >= {ph}""",
                (CompletionState.UNKNOWN.value, now_s, request_id, now_s),
            )
        # Under pg the claim UPDATE is a single autocommit statement — the
        # same one-atomic-statement claim the sqlite commit provides.
        self._commit()
        if cursor.rowcount != 1:
            current = self.get_request(request_id)
            if current.state == "running":
                detail = (
                    "still fresh — refusing to steal an active claim"
                    if reclaim
                    else "pass reclaim=True only for explicit crash recovery"
                )
                raise RequestExecutorError(
                    f"request {request_id} is already claimed by another "
                    f"executor (state=running); {detail}"
                )
            raise RequestExecutorError(
                f"request {request_id} is not executable (state={current.state})"
            )
        adapter_name = (adapter or req.resolved_recipient).lower()
        capture = CaptureInput(
            adapter=adapter_name,
            stdout=stdout,
            stderr=stderr,
            returncode=returncode,
            events=events,
            raw_bytes=raw_bytes,
            session_id=session_id,
            transport_metadata={"request_id": request_id},
        )
        raw = raw_bytes
        if raw is None:
            raw = "\n".join(
                [stdout or "", "---stderr---", stderr or "", f"---rc={returncode}---"]
            ).encode("utf-8")
        art = self.store.store_bytes(
            raw,
            producer=f"adapter:{adapter_name}",
            retention_class="raw-capture",
            mime_type="application/x-ndjson" if events or stdout.lstrip().startswith("{") else "text/plain",
            logical_filename=f"{request_id}.capture",
        )
        envelope = conform(capture)
        # Rebind envelope to the real artifact id/digest from the store.
        envelope = ResponseEnvelope(
            segments=envelope.segments,
            completion_state=envelope.completion_state,
            provider_stop_reason=envelope.provider_stop_reason,
            terminal_event_observed=envelope.terminal_event_observed,
            process_returncode=envelope.process_returncode,
            transport_metadata={**envelope.transport_metadata, "artifact_store_id": art.artifact_id},
            raw_capture_artifact_id=art.artifact_id,
            raw_capture_sha256=art.sha256,
            session_id=envelope.session_id or session_id,
            token_metadata=envelope.token_metadata,
            tool_call_metadata=envelope.tool_call_metadata,
        )
        # #7485: finalize atomically. The artifact commit above is the ONLY
        # separate commit — a crash after it leaves an unreferenced artifact,
        # which is exactly what garbage_collect_unreferenced() reclaims. All
        # state that must agree (references, request state, reply message)
        # lands in ONE transaction below.
        request_state = self._map_completion_to_request_state(envelope.completion_state)
        now_s = _iso(_utc_now())
        # The same event stream adapter conformance itself read: an explicit
        # events tuple when the runtime supplied one, otherwise the JSONL the
        # provider actually wrote to stdout. The V4 observation's runtime
        # model identity is derived from these, never from a caller field.
        observed_events = tuple(events) if events else tuple(parse_capture_events(stdout))
        if self._is_pg:
            # psycopg autocommit connection: all finalize writes share ONE
            # explicit transaction (create_request pg pattern).
            with self._conn.transaction():
                self._finalize_capture(
                    req=req,
                    request_id=request_id,
                    art=art,
                    envelope=envelope,
                    request_state=request_state,
                    now_s=now_s,
                    events=observed_events,
                )
        else:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._finalize_capture(
                    req=req,
                    request_id=request_id,
                    art=art,
                    envelope=envelope,
                    request_state=request_state,
                    now_s=now_s,
                    events=observed_events,
                )
            except Exception:
                self._conn.rollback()
                raise
            self._conn.commit()
        record = self.get_request(request_id)
        return RequestRecord(
            request_id=record.request_id,
            request_message_id=record.request_message_id,
            requested_recipient=record.requested_recipient,
            resolved_recipient=record.resolved_recipient,
            state=record.state,
            expires_at=record.expires_at,
            completion_state=record.completion_state,
            created_at=record.created_at,
            updated_at=record.updated_at,
            envelope=envelope,
            raw_capture_artifact_id=art.artifact_id,
        )

    def _finalize_capture(
        self,
        *,
        req: RequestRecord,
        request_id: str,
        art: Any,
        envelope: ResponseEnvelope,
        request_state: str,
        now_s: str,
        events: tuple[dict[str, Any], ...] = (),
    ) -> None:
        """All finalize writes; runs inside the caller's open transaction."""
        ph = "%s" if self._is_pg else "?"
        self.store.reference(
            req.request_message_id, art.artifact_id, relation="raw_capture", commit=False
        )
        row = self._conn.execute(
            f"SELECT invocation_spec_json FROM requests WHERE request_id = {ph}",
            (request_id,),
        ).fetchone()
        spec: dict[str, Any] = {}
        if row and row["invocation_spec_json"]:
            try:
                loaded = json.loads(str(row["invocation_spec_json"]))
                if isinstance(loaded, dict):
                    spec = loaded
            except json.JSONDecodeError:
                spec = {}
        spec["raw_capture_artifact_id"] = art.artifact_id
        spec["completion_state"] = envelope.completion_state.value
        # PR #7662 repair 7: the canonical execution observation is written
        # here, in the same transaction that finalizes the request, from
        # facts this boundary derives. Its text-free outcome code is
        # persisted with the request so a refusal is auditable.
        spec["v4_execution_observation"] = self._record_v4_execution_observation(
            request_id=request_id,
            req=req,
            art=art,
            envelope=envelope,
            request_state=request_state,
            events=events,
            now_s=now_s,
            conn=self._conn,
        )
        self._conn.execute(
            f"""UPDATE requests SET state = {ph}, completion_state = {ph}, updated_at = {ph},
               invocation_spec_json = {ph}
               WHERE request_id = {ph}""",
            (
                request_state,
                envelope.completion_state.value,
                now_s,
                json.dumps(spec, sort_keys=True),
                request_id,
            ),
        )
        # Reply message when we have text (even incomplete).
        if envelope.response_text:
            reply_id = new_id("message")
            preview = envelope.response_text[:500]
            self._conn.execute(
                f"""INSERT INTO comms_messages(
                    message_id, conversation_id, in_reply_to, kind, sender, recipient,
                    body_inline, body_artifact_id, content_sha256, metadata_json, created_at
                ) VALUES (
                    {ph},
                    (SELECT conversation_id FROM comms_messages WHERE message_id = {ph}),
                    {ph}, 'reply', {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}
                )""",
                (
                    reply_id,
                    req.request_message_id,
                    req.request_message_id,
                    req.resolved_recipient,
                    "request-executor",
                    preview,
                    art.artifact_id,
                    art.sha256,
                    json.dumps({"completion_state": envelope.completion_state.value}, sort_keys=True),
                    now_s,
                ),
            )
            self.store.reference(reply_id, art.artifact_id, relation="body", commit=False)

    @staticmethod
    def _map_completion_to_request_state(state: CompletionState) -> str:
        if state is CompletionState.COMPLETE:
            return "complete"
        if state is CompletionState.FAILED:
            return "failed"
        if state in {
            CompletionState.LENGTH_LIMITED,
            CompletionState.TRANSPORT_INCOMPLETE,
            CompletionState.UNKNOWN,
        }:
            return "incomplete"
        return "incomplete"

    def requeue_stale_running(self, *, stale_after_seconds: int = 7200) -> list[str]:
        """Reconcile crashed executors: atomically re-queue running requests
        whose claim has gone stale (#7485 CF r1 — production reclaim path).

        Returns the re-queued request ids; unexpired requests only. Callers
        (ops sweeps, ``python -m scripts.fleet_comms requests requeue-stale``)
        then re-execute them normally.

        The default floor (7200s) sits at the adapter HARD-timeout ceiling, so
        a slow-but-alive capture inside the runtime's bounds can never be
        swept (#7504 CF r2); a claimant that legitimately runs longer must
        heartbeat via ``touch_claim()``.
        """
        now = _utc_now()
        now_s = _iso(now)
        cutoff = _iso(now - timedelta(seconds=max(0, stale_after_seconds)))
        ph = "%s" if self._is_pg else "?"
        rows = self._conn.execute(
            f"""SELECT request_id FROM requests
               WHERE state = 'running' AND updated_at <= {ph} AND expires_at >= {ph}
               ORDER BY updated_at""",
            (cutoff, now_s),
        ).fetchall()
        stale_ids = [str(r["request_id"]) for r in rows]
        requeued: list[str] = []
        for request_id in stale_ids:
            cursor = self._conn.execute(
                f"""UPDATE requests SET state = 'queued', updated_at = {ph}
                   WHERE request_id = {ph} AND state = 'running' AND updated_at <= {ph}""",
                (now_s, request_id, cutoff),
            )
            # Each UPDATE is conditional and self-atomic; the rowcount check
            # absorbs the read-then-update race on either engine.
            if cursor.rowcount == 1:
                requeued.append(request_id)
        self._commit()
        return requeued

    def touch_claim(self, request_id: str) -> bool:
        """Heartbeat a running claim (bumps updated_at; #7504 CF r2).

        Long-running claimants call this periodically so neither
        ``requeue_stale_running`` nor a stale-reclaim can steal them.
        Returns False when the request is not currently running.
        """
        ph = "%s" if self._is_pg else "?"
        cursor = self._conn.execute(
            f"UPDATE requests SET updated_at = {ph}"
            f" WHERE request_id = {ph} AND state = 'running'",
            (_iso(_utc_now()), request_id),
        )
        self._commit()
        return cursor.rowcount == 1

    def _set_state(self, request_id: str, state: str, completion: CompletionState) -> None:
        if state not in REQUEST_STATES:
            raise RequestExecutorError(f"invalid request state: {state}")
        ph = "%s" if self._is_pg else "?"
        self._conn.execute(
            f"UPDATE requests SET state = {ph}, completion_state = {ph},"
            f" updated_at = {ph} WHERE request_id = {ph}",
            (state, completion.value, _iso(_utc_now()), request_id),
        )
        self._commit()

    # --- V4 canonical execution authority (PR #7662 repair 6/7) ------------
    #
    # This executor IS the execution service boundary the operator-approved
    # architecture designates as the exclusive writer of
    # ``v4_execution_observations``. Two halves, deliberately split around
    # the execution itself:
    #
    # * ``authorize_v4_execution`` runs BEFORE the model does, while the
    #   request is still ``queued``. It freezes the slot
    #   (``task_id``/``run_id``/``role``), the frozen row/packet digests and
    #   the model the dispatch boundary intends, and derives the harness
    #   itself from the registry-resolved recipient. It cannot be called
    #   after execution starts, so a binding can never be minted to describe
    #   a run that already happened.
    # * ``_build_v4_execution_observation`` runs inside
    #   ``_finalize_capture``'s transaction, AFTER this executor has proven
    #   the request terminal. It accepts nothing from any caller: the
    #   envelope comes from adapter conformance, the result digest from the
    #   artifact this store actually persisted, the runtime model identity
    #   from the provider's own capture events, the harness from the
    #   registry-resolved recipient, the verification tool ids from
    #   canonically recorded Sources invocations, and (for a reviewer) the
    #   verdict from a machine-readable marker in the model's own output.
    #   Anything unobservable, non-terminal, mismatched against the frozen
    #   binding, or cross-run refuses to record at all -- and a refusal is
    #   itself recorded, text-free, as ``v4_execution_observation`` in the
    #   request's own invocation spec, so an operator can see why a slot has
    #   no admissible evidence.

    #: The one machine-readable token a reviewer execution must emit for its
    #: verdict to be independently observable. Only the token is ever
    #: retained -- never the review text around it.
    V4_REVIEW_VERDICT_RE = re.compile(r"^[ \t]*V4-REVIEW-VERDICT:[ \t]*(PASS|FAIL)[ \t]*$", re.MULTILINE)

    def authorize_v4_execution(
        self,
        *,
        request_id: str,
        task_id: str,
        run_id: str,
        role: str,
        expected_seat_or_model: str,
        row_content_sha256: str,
        packet_sha256: str,
        authorship_receipt_sha256: str | None = None,
        rubric_sha256: str | None = None,
    ) -> dict[str, Any]:
        """Bind a still-queued request to one V4 slot, before it executes.

        Refuses once the request has left ``queued`` -- there is no path to
        authorize an execution retroactively. ``expected_harness`` is
        DERIVED here from the registry-resolved recipient, never accepted as
        an argument; the prompt digest is derived later, at finalization,
        from the exact request-body bytes this executor stored.
        """
        from scripts.fleet_comms import v4_canonical_authority_store as v4_store

        req = self.get_request(request_id)
        if req.state != "queued":
            raise RequestExecutorError(
                f"request {request_id} is not authorizable for a V4 slot "
                f"(state={req.state}); only a still-queued request may be bound"
            )
        harness = self._derive_harness(req)
        if harness is None:
            raise RequestExecutorError(
                f"request {request_id} resolves to recipient {req.resolved_recipient!r}, "
                "which is not one of the canonical known harness executables -- refusing"
            )
        binding = {
            "request_id": request_id,
            "task_id": task_id,
            "run_id": run_id,
            "role": role,
            "expected_seat_or_model": expected_seat_or_model,
            "expected_harness": harness,
            "row_content_sha256": row_content_sha256,
            "packet_sha256": packet_sha256,
            "authorship_receipt_sha256": authorship_receipt_sha256,
            "rubric_sha256": rubric_sha256,
        }
        with self.store._transaction() as conn:
            v4_store.record_execution_dispatch_binding(binding, conn=conn, is_pg=self._is_pg, commit=False)
        return binding

    def resolve_v4_execution_dispatch_binding(self, *, request_id: str) -> dict[str, Any] | None:
        from scripts.fleet_comms import v4_canonical_authority_store as v4_store

        return v4_store.resolve_execution_dispatch_binding(request_id=request_id, conn=self._conn, is_pg=self._is_pg)

    def resolve_v4_execution_observation(self, *, task_id: str, run_id: str, role: str) -> dict[str, Any] | None:
        return self.store.resolve_v4_execution_observation(task_id=task_id, run_id=run_id, role=role)

    @staticmethod
    def _derive_harness(req: RequestRecord) -> str | None:
        """The harness is whatever durable agent-driver executable the
        endpoint registry resolved this request to -- never the caller's
        ``adapter=`` override and never a free string."""
        from scripts.orchestration.thread_handoff import KNOWN_HARNESS_EXECUTABLES

        candidate = (req.resolved_recipient or "").strip().lower()
        return candidate if candidate in KNOWN_HARNESS_EXECUTABLES else None

    @staticmethod
    def _derive_observed_model(events: tuple[dict[str, Any], ...]) -> str | None:
        """The exact runtime model identity, read out of the provider's own
        capture events. Returns ``None`` unless the events name exactly one
        model -- an unobserved or self-contradicting identity is never
        guessed and never defaulted to the dispatch's expectation."""
        seen: set[str] = set()
        for event in events or ():
            if not isinstance(event, dict):
                continue
            candidates = [event.get("model")]
            message = event.get("message")
            if isinstance(message, dict):
                candidates.append(message.get("model"))
            for value in candidates:
                if isinstance(value, str) and value.strip():
                    seen.add(value.strip())
        return seen.pop() if len(seen) == 1 else None

    def _derive_prompt_sha256(self, request_message_id: str) -> str | None:
        """Hash the exact prompt bytes this executor durably stored for the
        request -- the dispatch caller never supplies this digest."""
        ph = "%s" if self._is_pg else "?"
        row = self._conn.execute(
            f"SELECT body_inline FROM comms_messages WHERE message_id = {ph}",
            (request_message_id,),
        ).fetchone()
        if row is None:
            return None
        body = row["body_inline"]
        if not isinstance(body, str) or not body:
            return None
        return hashlib.sha256(body.encode("utf-8")).hexdigest()

    @staticmethod
    def _fleet_receipt_sha256(*, req: RequestRecord, request_id: str, request_state: str, completion_state: str, artifact_id: str, now_s: str) -> str:
        """A digest over this request's own durable lifecycle projection --
        the executor's receipt that THIS request, resolved to THIS recipient,
        reached THIS terminal state with THIS capture artifact."""
        projection = {
            "request_id": request_id,
            "request_message_id": req.request_message_id,
            "requested_recipient": req.requested_recipient,
            "resolved_recipient": req.resolved_recipient,
            "state": request_state,
            "completion_state": completion_state,
            "expires_at": req.expires_at,
            "created_at": req.created_at,
            "raw_capture_artifact_id": artifact_id,
            "finalized_at": now_s,
        }
        return hashlib.sha256(
            json.dumps(projection, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

    @classmethod
    def _derive_review_verdict(cls, response_text: str) -> str | None:
        """The reviewer's own verdict token, read out of what the model
        actually produced. Absent, or two different verdicts in one output,
        is unobservable -- never resolved to a default."""
        found = {match.group(1) for match in cls.V4_REVIEW_VERDICT_RE.finditer(response_text or "")}
        return found.pop() if len(found) == 1 else None

    def _build_v4_execution_observation(
        self,
        *,
        binding: dict[str, Any],
        req: RequestRecord,
        request_id: str,
        art: Any,
        envelope: ResponseEnvelope,
        request_state: str,
        events: tuple[dict[str, Any], ...],
        now_s: str,
        conn: Any,
    ) -> tuple[dict[str, Any] | None, str]:
        """Derive one canonical execution observation, or explain the
        refusal. Returns ``(record | None, reason_code)``."""
        from scripts.fleet_comms import v4_canonical_authority_store as v4_store

        if request_state != "complete" or envelope.completion_state is not CompletionState.COMPLETE:
            return None, "refused:not-complete"
        if envelope.terminal_event_observed is not True:
            return None, "refused:no-terminal-event"
        if envelope.process_returncode != 0:
            return None, "refused:nonzero-returncode"
        if not envelope.session_id:
            return None, "refused:no-session-identity"
        harness = self._derive_harness(req)
        if harness is None or harness != binding["expected_harness"]:
            return None, "refused:harness-mismatch"
        observed_model = self._derive_observed_model(events)
        if observed_model is None:
            return None, "refused:model-unobserved"
        if observed_model != binding["expected_seat_or_model"]:
            return None, "refused:model-mismatch"
        prompt_sha256 = self._derive_prompt_sha256(req.request_message_id)
        if prompt_sha256 is None:
            return None, "refused:prompt-unavailable"
        verdict: str | None = None
        if binding["role"] == "reviewer":
            verdict = self._derive_review_verdict(envelope.response_text)
            if verdict is None:
                return None, "refused:verdict-unobserved"
        record = {
            "task_id": binding["task_id"],
            "run_id": binding["run_id"],
            "role": binding["role"],
            "status": "done",
            "return_code": 0,
            "seat_or_model": observed_model,
            "harness": harness,
            "session_id": envelope.session_id,
            "completion_state": envelope.completion_state.value,
            "terminal_event_observed": True,
            "process_returncode": 0,
            "raw_capture_artifact_id": art.artifact_id,
            "raw_capture_sha256": art.sha256,
            "row_content_sha256": binding["row_content_sha256"],
            "prompt_sha256": prompt_sha256,
            "packet_sha256": binding["packet_sha256"],
            "fleet_receipt_sha256": self._fleet_receipt_sha256(
                req=req,
                request_id=request_id,
                request_state=request_state,
                completion_state=envelope.completion_state.value,
                artifact_id=art.artifact_id,
                now_s=now_s,
            ),
            "verification_tool_ids": v4_store.resolve_sources_invocation_tool_ids(
                request_id=request_id, conn=conn, is_pg=self._is_pg
            ),
            # Never a caller-declared attestation: only an execution
            # dispatched through this blind V4 boundary can be observed at
            # all, and the boundary has no argument that could set any of
            # these true. The bytes those flags describe are pinned by
            # ``prompt_sha256``/``packet_sha256`` above, whose blindness
            # posture the A3 builder-packet receipt establishes.
            "saw_source_text": False,
            "saw_heldout": False,
            "saw_eligible_unit_ids": False,
            "authorship_receipt_sha256": binding["authorship_receipt_sha256"],
            "rubric_sha256": binding["rubric_sha256"],
            "verdict": verdict,
        }
        return record, "recorded"

    def _record_v4_execution_observation(
        self,
        *,
        request_id: str,
        req: RequestRecord,
        art: Any,
        envelope: ResponseEnvelope,
        request_state: str,
        events: tuple[dict[str, Any], ...],
        now_s: str,
        conn: Any,
    ) -> str:
        """Runs inside ``_finalize_capture``'s open transaction. Returns the
        text-free outcome code recorded in the request's invocation spec."""
        from scripts.fleet_comms import v4_canonical_authority_store as v4_store

        binding = v4_store.resolve_execution_dispatch_binding(request_id=request_id, conn=conn, is_pg=self._is_pg)
        if binding is None:
            return "unbound"
        record, reason = self._build_v4_execution_observation(
            binding=binding,
            req=req,
            request_id=request_id,
            art=art,
            envelope=envelope,
            request_state=request_state,
            events=events,
            now_s=now_s,
            conn=conn,
        )
        if record is None:
            return reason
        try:
            v4_store._persist_execution_observation(
                record, conn=conn, is_pg=self._is_pg, request_id=request_id, commit=False
            )
        except v4_store.CanonicalAuthorityStoreError:
            # A conflicting observation already owns this slot. Leave the
            # prior evidence exactly as it is and finalize the request
            # normally -- the slot simply has no admissible evidence from
            # this run, which is the fail-closed outcome.
            return "refused:slot-conflict"
        return "recorded"


def open_executor(root: Path | None = None) -> RequestExecutor:
    """Factory used by CLI/tests."""
    return RequestExecutor(root=root)
