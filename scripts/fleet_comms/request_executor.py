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
        # Repair 8: execute_capture is not a V4 execution origin. The native
        # runner writes observations after an actual Popen. Generic
        # message-plane capture remains non-authoritative for V4.
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

    # --- V4 native-runner execution origin (PR #7662 repair 8) -------------
    #
    # execute_capture is not a V4 authority. Role-specific authorization
    # freezes a source-blind prompt against a still-queued request. The
    # native runner then claims that exact binding immediately before Popen
    # and finalizes from the process it actually spawned.

    def _lock_queued_request(self, request_id: str) -> RequestRecord:
        """Inside the caller's open transaction: lock the request row (PG
        ``FOR UPDATE``, SQLite ``BEGIN IMMEDIATE``) and refuse unless it is
        still ``queued``."""
        ph = "%s" if self._is_pg else "?"
        if self._is_pg:
            row = self._conn.execute(
                f"SELECT * FROM requests WHERE request_id = {ph} FOR UPDATE",
                (request_id,),
            ).fetchone()
        else:
            row = self._conn.execute(
                f"SELECT * FROM requests WHERE request_id = {ph}",
                (request_id,),
            ).fetchone()
        if row is None:
            raise RequestExecutorError(f"request not found: {request_id}")
        state = str(row["state"])
        if state != "queued":
            raise RequestExecutorError(
                f"request {request_id} is not authorizable for a V4 slot "
                f"(state={state}); only a still-queued request may be bound"
            )
        return RequestRecord(
            request_id=str(row["request_id"]),
            request_message_id=str(row["request_message_id"]),
            requested_recipient=str(row["requested_recipient"]),
            resolved_recipient=str(row["resolved_recipient"]),
            state=state,
            expires_at=str(row["expires_at"]),
            completion_state=str(row["completion_state"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    def authorize_author_execution(self, *, request_id: str, slot_id: str, expected_seat: str) -> dict[str, Any]:
        """Resolve frozen slot + A3 packet, build the source-blind author
        prompt internally, and bind the still-queued request. Does not
        accept a row/packet/content hash from the caller."""
        from scripts.fleet_comms import v4_canonical_authority_store as v4_store
        from scripts.fleet_comms import v4_execution_origin as origin

        packet_sha256 = origin.load_a3_packet_commitment()
        origin.load_frozen_slot(slot_id)
        prompt = origin.build_author_prompt(slot_id=slot_id, packet_sha256=packet_sha256, expected_seat=expected_seat)
        task_id, run_id = origin.new_task_run_ids(slot_id=slot_id, role="author")
        with self.store._transaction() as conn:
            req = self._lock_queued_request(request_id)
            harness = origin.derive_harness(req.resolved_recipient)
            binding = {
                "request_id": request_id,
                "task_id": task_id,
                "run_id": run_id,
                "role": "author",
                "slot_id": slot_id,
                "expected_seat_or_model": expected_seat,
                "expected_harness": harness,
                "prompt_profile": origin.AUTHOR_PROMPT_PROFILE,
                "prompt_sha256": origin.prompt_digest(prompt),
                "packet_sha256": packet_sha256,
                "authorship_receipt_id": None,
                "authorship_receipt_sha256": None,
                "rubric_sha256": None,
            }
            v4_store.record_execution_dispatch_binding(binding, conn=conn, is_pg=self._is_pg, commit=False)
        return {**binding, "authorized_prompt": prompt}

    def authorize_reviewer_execution(
        self,
        *,
        request_id: str,
        authorship_receipt_id: str,
        expected_seat: str,
    ) -> dict[str, Any]:
        """Resolve the author receipt + fixed rubric internally, build the
        exact review prompt, and bind the still-queued request. Does not
        accept packet/rubric/content hashes from the caller."""
        from scripts.fleet_comms import v4_canonical_authority_store as v4_store
        from scripts.fleet_comms import v4_execution_origin as origin

        packet_sha256 = origin.load_a3_packet_commitment()
        rubric_sha256 = origin.load_review_rubric_sha256()
        with self.store._transaction() as conn:
            req = self._lock_queued_request(request_id)
            authorship = v4_store.resolve_authorship_receipt(receipt_id=authorship_receipt_id, conn=conn, is_pg=self._is_pg)
            if authorship is None:
                raise RequestExecutorError(f"unknown authorship_receipt_id {authorship_receipt_id!r} -- refusing")
            authorship_sha256 = hashlib.sha256(
                json.dumps(authorship, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            prompt = origin.build_reviewer_prompt(
                authorship_receipt_sha256=authorship_sha256,
                rubric_sha256=rubric_sha256,
                packet_sha256=packet_sha256,
                expected_seat=expected_seat,
            )
            task_id, run_id = origin.new_task_run_ids(slot_id=authorship_receipt_id, role="reviewer")
            harness = origin.derive_harness(req.resolved_recipient)
            binding = {
                "request_id": request_id,
                "task_id": task_id,
                "run_id": run_id,
                "role": "reviewer",
                "slot_id": None,
                "expected_seat_or_model": expected_seat,
                "expected_harness": harness,
                "prompt_profile": origin.REVIEWER_PROMPT_PROFILE,
                "prompt_sha256": origin.prompt_digest(prompt),
                "packet_sha256": packet_sha256,
                "authorship_receipt_id": authorship_receipt_id,
                "authorship_receipt_sha256": authorship_sha256,
                "rubric_sha256": rubric_sha256,
            }
            v4_store.record_execution_dispatch_binding(binding, conn=conn, is_pg=self._is_pg, commit=False)
        return {**binding, "authorized_prompt": prompt}

    def resolve_v4_execution_dispatch_binding(self, *, request_id: str) -> dict[str, Any] | None:
        from scripts.fleet_comms import v4_canonical_authority_store as v4_store

        return v4_store.resolve_execution_dispatch_binding(request_id=request_id, conn=self._conn, is_pg=self._is_pg)

    def resolve_v4_execution_observation(self, *, task_id: str, run_id: str, role: str) -> dict[str, Any] | None:
        return self.store.resolve_v4_execution_observation(task_id=task_id, run_id=run_id, role=role)

    def resolve_authorized_prompt(self, *, request_id: str) -> str:
        """Reconstruct the exact authorized prompt from the frozen binding."""
        from scripts.fleet_comms import v4_execution_origin as origin

        binding = self.resolve_v4_execution_dispatch_binding(request_id=request_id)
        if binding is None:
            raise RequestExecutorError(f"no V4 binding for request {request_id}")
        if binding["role"] == "author":
            prompt = origin.build_author_prompt(
                slot_id=binding["slot_id"],
                packet_sha256=binding["packet_sha256"],
                expected_seat=binding["expected_seat_or_model"],
            )
        else:
            prompt = origin.build_reviewer_prompt(
                authorship_receipt_sha256=binding["authorship_receipt_sha256"],
                rubric_sha256=binding["rubric_sha256"],
                packet_sha256=binding["packet_sha256"],
                expected_seat=binding["expected_seat_or_model"],
            )
        if origin.prompt_digest(prompt) != binding["prompt_sha256"]:
            raise RequestExecutorError("authorized prompt does not reproduce from the frozen profile -- refusing")
        return prompt

    def claim_v4_runner_execution(self, *, request_id: str) -> dict[str, Any]:
        """Atomically require the exact binding and ``queued -> running``
        while creating the one-attempt capability. Called by the native
        runner immediately before Popen."""
        if self._is_pg:
            raise RequestExecutorError("legacy V4 runner claim is retired; use the protected packaged V4 service runtime")
        from scripts.fleet_comms import v4_canonical_authority_store as v4_store
        from scripts.fleet_comms import v4_execution_origin as origin

        now_s = _iso(_utc_now())
        ph = "%s" if self._is_pg else "?"
        with self.store._transaction() as conn:
            req = self._lock_queued_request(request_id)
            binding = v4_store.resolve_execution_dispatch_binding(request_id=request_id, conn=conn, is_pg=self._is_pg)
            if binding is None:
                raise RequestExecutorError(f"request {request_id} has no V4 binding -- refusing to start")
            cursor = conn.execute(
                f"""UPDATE requests SET state = 'running', completion_state = {ph}, updated_at = {ph}
                   WHERE request_id = {ph} AND state = 'queued'""",
                (CompletionState.UNKNOWN.value, now_s, request_id),
            )
            if cursor.rowcount != 1:
                raise RequestExecutorError(f"request {request_id} could not be claimed for V4 execution")
            token, digest = origin.mint_capability_token()
            attempt_id = origin.new_attempt_id()
            binding_sha256 = hashlib.sha256(
                json.dumps(binding, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            v4_store.record_execution_attempt(
                attempt_id=attempt_id,
                request_id=request_id,
                task_id=binding["task_id"],
                run_id=binding["run_id"],
                role=binding["role"],
                capability_digest=digest,
                binding_sha256=binding_sha256,
                conn=conn,
                is_pg=self._is_pg,
                commit=False,
            )
        return {
            "attempt_id": attempt_id,
            "capability_token": token,
            "binding": binding,
            "request": req,
        }

    def finalize_v4_runner_execution(
        self,
        *,
        request_id: str,
        attempt_id: str,
        review_cmd: list[str],
        transported_prompt: bytes,
        stdout: bytes,
        stderr: bytes,
        output_bytes: bytes,
        returncode: int | None,
        parse_ok: bool,
        parse_response: str,
        parse_session_id: str | None,
        requested_model: str,
    ) -> str:
        """Derive and persist one observation from the process the native
        runner actually spawned. Refuses rather than defaulting missing
        actual-model/session telemetry."""

        raise RequestExecutorError("raw caller finalization is retired; use the protected packaged V4 service runtime")

    def _persist_runner_observation(
        self,
        *,
        conn: Any,
        binding: dict[str, Any],
        req: RequestRecord,
        request_id: str,
        attempt_id: str,
        review_cmd: list[str],
        transported_prompt: bytes,
        stdout: bytes,
        stderr: bytes,
        output_bytes: bytes,
        returncode: int | None,
        parse_ok: bool,
        parse_response: str,
        parse_session_id: str | None,
        requested_model: str,
        events: tuple[dict[str, Any], ...],
        now_s: str,
        art: Any,
    ) -> str:
        raise RequestExecutorError("caller-shaped V4 observations are retired; protected parent capture is required")

    def persist_v4_authorship_receipt(self, receipt: dict[str, Any], *, task_id: str, run_id: str) -> None:
        from scripts.fleet_comms import v4_canonical_authority_store as v4_store

        with self.store._transaction() as conn:
            v4_store.persist_authorship_receipt(receipt, task_id=task_id, run_id=run_id, conn=conn, is_pg=self._is_pg, commit=False)


def open_executor(root: Path | None = None) -> RequestExecutor:
    """Factory used by CLI/tests."""
    return RequestExecutor(root=root)
