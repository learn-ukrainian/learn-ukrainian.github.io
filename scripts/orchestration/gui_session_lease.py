"""Operate a fenced session-stream lease from an exact Codex desktop task.

Active-task proof comes from a paired native ``codex_app.read_thread`` call
recorded in the task's own rollout. Terminal/absent proof comes from a stable,
read-only Codex state-database sample. Raw task content is never retained.
"""

from __future__ import annotations

import argparse
import json
import uuid
from collections.abc import Mapping
from datetime import timedelta
from pathlib import Path
from typing import Any

from agents_extensions.shared.session_streams.app_lifecycle import (
    AppLifecycleReceipt,
    StructuredReadbackAdapter,
    VerifiedAppLifecycleProof,
    make_receipt,
)
from agents_extensions.shared.session_streams.db import SessionStreamDatabase
from agents_extensions.shared.session_streams.model import (
    EntryType,
    HolderKind,
    Lease,
    LeaseHolder,
    SessionState,
    canonical_json,
    isoformat_z,
    parse_timestamp,
    sha256_text,
    utc_now,
)
from agents_extensions.shared.session_streams.store import SessionStreamError, SessionStreamStore
from scripts.orchestration.task_family.codex_state import (
    CleanupThreadRecord,
    CodexStateMissingTaskError,
    discover_state_database,
    read_cleanup_thread_record,
)

READ_THREAD_SOURCE = "codex_app.read_thread"
STATE_SOURCE = "codex_state.thread_presence"
SCHEMA_VERSION = 1
SOURCE_SCHEMA_DIGESTS = {
    READ_THREAD_SOURCE: sha256_text("codex_app.read_thread.redacted.v1"),
    STATE_SOURCE: sha256_text("codex_state.thread_presence.redacted.v1"),
}
NATIVE_STATUS_TYPES = frozenset({"active", "idle", "notLoaded", "terminal", "absent"})


class CodexGuiSessionLeaseAdapter(StructuredReadbackAdapter):
    """Create proofs only from allowlisted, independently read native state."""

    def __init__(self, *, adapter_version: str, verifier_id: str) -> None:
        super().__init__(provider="codex-desktop", adapter_version=adapter_version, verifier_id=verifier_id)

    @staticmethod
    def _allowlisted(readback: Mapping[str, object]) -> dict[str, object]:
        thread = readback.get("thread")
        if not isinstance(thread, Mapping):
            raise ValueError("native readback requires a thread object")
        source = readback.get("source")
        if readback.get("schema_version") != SCHEMA_VERSION or source not in SOURCE_SCHEMA_DIGESTS:
            raise ValueError("unregistered native readback schema or source")
        authority = readback.get("source_authority")
        observed_at = readback.get("observed_at")
        if not isinstance(authority, str) or not authority or not isinstance(observed_at, str) or not observed_at:
            raise ValueError("native readback lacks source authority or observation time")
        parse_timestamp(observed_at)
        allowed_thread = {
            "id": thread.get("id"),
            "kind": thread.get("kind"),
            "host_id": thread.get("host_id"),
            "status_type": thread.get("status_type"),
            "created_at": thread.get("created_at"),
            "updated_at": thread.get("updated_at"),
            "archived": thread.get("archived"),
        }
        for key in ("id", "kind", "host_id", "status_type"):
            if not isinstance(allowed_thread[key], str) or not allowed_thread[key]:
                raise ValueError(f"native readback lacks allowlisted thread field {key}")
        for key in ("created_at", "updated_at"):
            value = allowed_thread[key]
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"native readback field {key} must be a non-negative integer")
        if not isinstance(allowed_thread["archived"], bool):
            raise ValueError("native readback field archived must be boolean")
        if allowed_thread["kind"] != "codex" or allowed_thread["status_type"] not in NATIVE_STATUS_TYPES:
            raise ValueError("native readback is not a supported Codex task state")
        if source == READ_THREAD_SOURCE and allowed_thread["archived"]:
            raise ValueError("an archived task cannot provide active read_thread authority")
        if source == STATE_SOURCE:
            terminal_shape = allowed_thread["status_type"] == "terminal" and allowed_thread["archived"]
            absent_shape = allowed_thread["status_type"] == "absent" and not allowed_thread["archived"]
            if not (terminal_shape or absent_shape):
                raise ValueError("state-database proof must describe an archived or absent task")
        return {
            "schema_version": SCHEMA_VERSION,
            "source": source,
            "source_authority": authority,
            "observed_at": observed_at,
            "thread": allowed_thread,
        }

    def verify_readback(
        self, receipt: AppLifecycleReceipt, readback: Mapping[str, object]
    ) -> VerifiedAppLifecycleProof:
        envelope = self._allowlisted(readback)
        thread = envelope["thread"]
        assert isinstance(thread, Mapping)
        source = str(envelope["source"])
        if receipt.provider != self.provider or receipt.adapter_version != self.adapter_version:
            raise ValueError("receipt provider or adapter version is not registered")
        if (
            receipt.source_schema_digest != SOURCE_SCHEMA_DIGESTS[source]
            or receipt.source_authority != envelope["source_authority"]
        ):
            raise ValueError("receipt source authority/schema does not match native readback")
        if receipt.holder.task_id != thread["id"] or receipt.observed_at != envelope["observed_at"]:
            raise ValueError("receipt task identity or observed_at does not match native readback")
        if receipt.state != thread["status_type"]:
            raise ValueError("receipt lifecycle state does not match native task status")
        if receipt.readback_digest != sha256_text(canonical_json(envelope)):
            raise ValueError("receipt readback digest was not independently computed from native readback")
        receipt.validate()
        return VerifiedAppLifecycleProof(receipt=receipt, verifier_id=self.verifier_id)

    @staticmethod
    def _state_envelope(*, task_id: str, state_db: Path, record: CleanupThreadRecord | None) -> dict[str, object]:
        observed_at = isoformat_z(utc_now())
        authority = f"codex-state-sha256:{sha256_text(str(state_db.resolve()))}"
        if record is None:
            return {
                "schema_version": SCHEMA_VERSION,
                "source": STATE_SOURCE,
                "source_authority": authority,
                "observed_at": observed_at,
                "thread": {
                    "id": task_id,
                    "kind": "codex",
                    "host_id": "local",
                    "status_type": "absent",
                    "created_at": 0,
                    "updated_at": 0,
                    "archived": False,
                },
            }
        archived = record.archived
        if not archived:
            raise ValueError("an unarchived task is not terminal and cannot authorize recovery")
        return {
            "schema_version": SCHEMA_VERSION,
            "source": STATE_SOURCE,
            "source_authority": authority,
            "observed_at": observed_at,
            "thread": {
                "id": task_id,
                "kind": "codex",
                "host_id": "local",
                "status_type": "terminal",
                "created_at": record.created_at,
                "updated_at": record.updated_at,
                "archived": True,
            },
        }

    @classmethod
    def discover_native_readback(
        cls,
        *,
        task_id: str,
        state_db: Path | None = None,
        require_recovery_state: bool = False,
    ) -> dict[str, object]:
        """Read exact native state without accepting a caller-authored activity claim."""
        db = discover_state_database(state_db)
        try:
            record = read_cleanup_thread_record(db, thread_id=task_id)
        except CodexStateMissingTaskError:
            if not require_recovery_state:
                raise ValueError("active GUI proof requires an exact native task row") from None
            envelope = cls._state_envelope(task_id=task_id, state_db=db, record=None)
            return cls._allowlisted(envelope)
        if require_recovery_state:
            envelope = cls._state_envelope(task_id=task_id, state_db=db, record=record)
            return cls._allowlisted(envelope)
        if record.archived:
            raise ValueError("archived Codex task cannot hold or renew a GUI lease")
        rollout = Path(record.rollout_path)
        if not rollout.is_file():
            raise ValueError("Codex rollout path is absent")
        calls: dict[str, str] = {}
        candidates: list[tuple[str, dict[str, object]]] = []
        with rollout.open(encoding="utf-8") as handle:
            for raw_line in handle:
                try:
                    event = json.loads(raw_line)
                    payload = event["payload"]
                    timestamp = event["timestamp"]
                except (KeyError, TypeError, json.JSONDecodeError):
                    continue
                if not isinstance(payload, Mapping) or not isinstance(timestamp, str):
                    continue
                if payload.get("type") == "function_call" and payload.get("name") == "read_thread":
                    try:
                        arguments = json.loads(str(payload["arguments"]))
                    except (KeyError, TypeError, json.JSONDecodeError):
                        continue
                    call_id = payload.get("call_id")
                    if (
                        isinstance(call_id, str)
                        and arguments.get("threadId") == task_id
                        and arguments.get("includeOutputs") is False
                        and isinstance(arguments.get("turnLimit"), int)
                        and 0 < arguments["turnLimit"] <= 10
                        and "cursor" not in arguments
                    ):
                        parse_timestamp(timestamp)
                        calls[call_id] = timestamp
                    continue
                call_id = payload.get("call_id")
                if (
                    payload.get("type") != "function_call_output"
                    or not isinstance(call_id, str)
                    or call_id not in calls
                ):
                    continue
                try:
                    output = json.loads(str(payload["output"]))
                    thread = output["thread"]
                    if parse_timestamp(timestamp) < parse_timestamp(calls[call_id]):
                        raise ValueError("native read_thread output predates its call")
                    envelope = {
                        "schema_version": output["schemaVersion"],
                        "source": READ_THREAD_SOURCE,
                        "source_authority": (
                            f"codex-rollout-sha256:{sha256_text(str(rollout.resolve()))}:call:{call_id}"
                        ),
                        "observed_at": timestamp,
                        "thread": {
                            "id": thread["id"],
                            "kind": thread["kind"],
                            "host_id": thread["hostId"],
                            "status_type": thread["status"]["type"],
                            "created_at": thread["createdAt"],
                            "updated_at": thread["updatedAt"],
                            "archived": False,
                        },
                    }
                    envelope = cls._allowlisted(envelope)
                    envelope_thread = envelope["thread"]
                    assert isinstance(envelope_thread, Mapping)
                    if envelope_thread["id"] == task_id:
                        candidates.append((timestamp, envelope))
                except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                    continue
        if not candidates:
            raise ValueError("no successful paired native read_thread proof for exact task")
        candidates.sort(key=lambda item: item[0])
        return candidates[-1][1]


def _holder(args: argparse.Namespace, *, task_id: str | None = None, predecessor: bool = False) -> LeaseHolder:
    prefix = "predecessor_" if predecessor else ""
    return LeaseHolder(
        agent=str(getattr(args, f"{prefix}agent")),
        harness=str(getattr(args, f"{prefix}harness")),
        instance_id=str(getattr(args, f"{prefix}instance_id")),
        task_id=task_id or str(args.task_id),
        process_id=None,
        holder_kind=HolderKind.APP_THREAD,
    )


def _proof(
    *,
    adapter: CodexGuiSessionLeaseAdapter,
    envelope: Mapping[str, object],
    operation: str,
    holder: LeaseHolder,
    stream_id: str,
    valid_seconds: int,
    session_id: str | None = None,
    lease_id: str | None = None,
    generation: int | None = None,
    fencing_token: int | None = None,
    rollover_id: str | None = None,
) -> VerifiedAppLifecycleProof:
    allowlisted = adapter._allowlisted(envelope)
    observed_at = str(allowlisted["observed_at"])
    thread = allowlisted["thread"]
    assert isinstance(thread, Mapping)
    source = str(allowlisted["source"])
    receipt = make_receipt(
        operation=operation,
        provider=adapter.provider,
        adapter_version=adapter.adapter_version,
        holder=holder,
        state=str(thread["status_type"]),
        observed_at=observed_at,
        valid_until=isoformat_z(parse_timestamp(observed_at) + timedelta(seconds=valid_seconds)),
        source_schema_digest=SOURCE_SCHEMA_DIGESTS[source],
        source_authority=str(allowlisted["source_authority"]),
        readback_digest=sha256_text(canonical_json(allowlisted)),
        stream_id=stream_id,
        session_id=session_id,
        lease_id=lease_id,
        generation=generation,
        fencing_token=fencing_token,
        rollover_id=rollover_id,
    )
    return adapter.verify_readback(receipt, allowlisted)


def _lease_json(lease: Lease, *, state: str = "active") -> dict[str, object]:
    return {
        "stream_id": lease.stream_id,
        "session_id": lease.session_id,
        "lease_id": lease.lease_id,
        "generation": lease.generation,
        "fencing_token": lease.fencing_token,
        "state": state,
        "holder_kind": lease.holder.holder_kind.value,
        "holder_agent": lease.holder.agent,
        "holder_harness": lease.holder.harness,
        "holder_instance_id": lease.holder.instance_id,
        "holder_task_id": lease.holder.task_id,
        "holder_process_id": lease.holder.process_id,
        "heartbeat_at": lease.heartbeat_at,
        "expires_at": lease.expires_at,
        "ttl_seconds": lease.ttl_seconds,
        "version": lease.version,
    }


def _holder_projection(
    store: SessionStreamStore,
    args: argparse.Namespace,
    *,
    allowed_states: frozenset[str] = frozenset({"active"}),
) -> Lease:
    projection = store.lease_projection(args.stream_id)
    if projection is None or projection[1] not in allowed_states:
        expected = "/".join(sorted(allowed_states))
        raise ValueError(f"stream {args.stream_id} has no {expected} lease")
    lease = projection[0]
    if lease.holder != _holder(args):
        raise ValueError("active lease holder does not match the exact Codex GUI task")
    return lease


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Operate a fenced Codex GUI session-stream lease.")
    parser.add_argument("--db", type=Path)
    parser.add_argument("--codex-state-db", type=Path)
    parser.add_argument("--adapter-version", default="v1")
    parser.add_argument("--verifier-id", default="codex-native-readback-v1")
    parser.add_argument("--proof-valid-seconds", type=int, default=120)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--stream-id", required=True)
    parser.add_argument("--agent", default="codex")
    parser.add_argument("--harness", default="codex-desktop")
    parser.add_argument("--instance-id", default="codex-desktop-local")
    subparsers = parser.add_subparsers(dest="action", required=True)
    subparsers.add_parser("status")

    acquire = subparsers.add_parser("acquire")
    acquire.add_argument("--lineage-id", required=True)
    acquire.add_argument("--ttl-seconds", type=int, required=True)
    acquire.add_argument("--session-id", required=True)
    acquire.add_argument("--lease-id", required=True)

    subparsers.add_parser("renew")

    append = subparsers.add_parser("append")
    append.add_argument("--entry-type", choices=tuple(item.value for item in EntryType), required=True)
    append.add_argument("--body", required=True)
    append.add_argument("--idempotency-key", required=True)

    transition = subparsers.add_parser("transition")
    transition.add_argument("--to-state", choices=(SessionState.OPEN.value, SessionState.ROLLING.value), required=True)
    transition.add_argument("--reason", required=True)

    close = subparsers.add_parser("close")
    close.add_argument("--reason", default="Codex GUI task clean exit")

    recover = subparsers.add_parser("recover")
    recover.add_argument("--predecessor-task-id", required=True)
    recover.add_argument("--predecessor-agent", default="codex")
    recover.add_argument("--predecessor-harness", default="codex-desktop")
    recover.add_argument("--predecessor-instance-id", required=True)
    recover.add_argument("--predecessor-session-id", required=True)
    recover.add_argument("--predecessor-lease-id", required=True)
    recover.add_argument("--predecessor-generation", type=int, required=True)
    recover.add_argument("--predecessor-fencing-token", type=int, required=True)
    recover.add_argument("--lineage-id", required=True)
    recover.add_argument("--rollover-id", required=True)
    recover.add_argument("--ttl-seconds", type=int, required=True)
    recover.add_argument("--session-id", required=True)
    recover.add_argument("--lease-id", required=True)
    return parser


def _run(args: argparse.Namespace) -> dict[str, object]:
    if args.proof_valid_seconds <= 0 or args.proof_valid_seconds > 600:
        raise ValueError("--proof-valid-seconds must be between 1 and 600")
    uuid.UUID(str(args.task_id))
    database = SessionStreamDatabase(args.db) if args.db else SessionStreamDatabase(repo_root=Path.cwd())
    if args.action != "status":
        database.connect().close()
    store = SessionStreamStore(database)
    adapter = CodexGuiSessionLeaseAdapter(
        adapter_version=args.adapter_version,
        verifier_id=args.verifier_id,
    )
    if args.action == "status":
        envelope = adapter.discover_native_readback(task_id=args.task_id, state_db=args.codex_state_db)
        projection = store.lease_projection(args.stream_id)
        thread = envelope["thread"]
        assert isinstance(thread, Mapping)
        return {
            "ok": True,
            "action": "status",
            "native": {
                "task_id": thread["id"],
                "status": thread["status_type"],
                "observed_at": envelope["observed_at"],
                "readback_digest": sha256_text(canonical_json(envelope)),
            },
            "lease": _lease_json(projection[0], state=projection[1]) if projection else None,
            "audit": store.audit(),
        }

    holder = _holder(args)
    if args.action == "acquire":
        projection = store.lease_projection(args.stream_id)
        if projection is None:
            generation, fencing_token = 1, 1
        elif (
            projection[1] == "active"
            and projection[0].holder == holder
            and projection[0].session_id == args.session_id
            and projection[0].lease_id == args.lease_id
        ):
            generation, fencing_token = projection[0].generation, projection[0].fencing_token
        else:
            generation = projection[0].generation + 1
            fencing_token = projection[0].fencing_token + 1
        envelope = adapter.discover_native_readback(task_id=args.task_id, state_db=args.codex_state_db)
        proof = _proof(
            adapter=adapter,
            envelope=envelope,
            operation="acquire",
            holder=holder,
            stream_id=args.stream_id,
            valid_seconds=args.proof_valid_seconds,
            session_id=args.session_id,
            lease_id=args.lease_id,
            generation=generation,
            fencing_token=fencing_token,
        )
        lease = store.open_session(
            stream_id=args.stream_id,
            holder=holder,
            lineage_id=args.lineage_id,
            ttl_seconds=args.ttl_seconds,
            session_id=args.session_id,
            lease_id=args.lease_id,
            app_proof=proof,
        )
        return {"ok": True, "action": "acquire", "lease": _lease_json(lease)}

    if args.action == "recover":
        predecessor_holder = _holder(args, task_id=args.predecessor_task_id, predecessor=True)
        predecessor_envelope = adapter.discover_native_readback(
            task_id=args.predecessor_task_id,
            state_db=args.codex_state_db,
            require_recovery_state=True,
        )
        successor_envelope = adapter.discover_native_readback(task_id=args.task_id, state_db=args.codex_state_db)
        predecessor = Lease(
            stream_id=args.stream_id,
            session_id=args.predecessor_session_id,
            lease_id=args.predecessor_lease_id,
            generation=args.predecessor_generation,
            fencing_token=args.predecessor_fencing_token,
            holder=predecessor_holder,
            heartbeat_at=str(predecessor_envelope["observed_at"]),
            expires_at=str(predecessor_envelope["observed_at"]),
            ttl_seconds=1,
            version=1,
        )
        projection = store.lease_projection(args.stream_id)
        if (
            projection is not None
            and projection[1] == "active"
            and projection[0].holder == holder
            and projection[0].session_id == args.session_id
            and projection[0].lease_id == args.lease_id
        ):
            generation, fencing_token = projection[0].generation, projection[0].fencing_token
        else:
            generation = predecessor.generation + 1
            fencing_token = predecessor.fencing_token + 1
        predecessor_thread = predecessor_envelope["thread"]
        assert isinstance(predecessor_thread, Mapping)
        predecessor_proof = _proof(
            adapter=adapter,
            envelope=predecessor_envelope,
            operation="recover",
            holder=predecessor_holder,
            stream_id=args.stream_id,
            valid_seconds=args.proof_valid_seconds,
            session_id=predecessor.session_id,
            lease_id=predecessor.lease_id,
            generation=predecessor.generation,
            fencing_token=predecessor.fencing_token,
            rollover_id=args.rollover_id,
        )
        if predecessor_proof.receipt.state not in {"terminal", "absent"}:
            raise ValueError("recovery predecessor is neither archived nor absent")
        successor_proof = _proof(
            adapter=adapter,
            envelope=successor_envelope,
            operation="recover",
            holder=holder,
            stream_id=args.stream_id,
            valid_seconds=args.proof_valid_seconds,
            session_id=args.session_id,
            lease_id=args.lease_id,
            generation=generation,
            fencing_token=fencing_token,
            rollover_id=args.rollover_id,
        )
        lease = store.recover_app_session(
            predecessor,
            successor=holder,
            lineage_id=args.lineage_id,
            ttl_seconds=args.ttl_seconds,
            rollover_id=args.rollover_id,
            predecessor_proof=predecessor_proof,
            successor_proof=successor_proof,
            session_id=args.session_id,
            lease_id=args.lease_id,
        )
        return {"ok": True, "action": "recover", "lease": _lease_json(lease)}

    lease = _holder_projection(
        store,
        args,
        allowed_states=frozenset({"active", "released"}) if args.action == "close" else frozenset({"active"}),
    )
    envelope = adapter.discover_native_readback(task_id=args.task_id, state_db=args.codex_state_db)
    proof = _proof(
        adapter=adapter,
        envelope=envelope,
        operation=args.action,
        holder=holder,
        stream_id=args.stream_id,
        valid_seconds=args.proof_valid_seconds,
        session_id=lease.session_id,
        lease_id=lease.lease_id,
        generation=lease.generation,
        fencing_token=lease.fencing_token,
    )
    if args.action == "renew":
        renewed = store.heartbeat(lease, app_proof=proof)
        return {"ok": True, "action": "renew", "lease": _lease_json(renewed)}
    if args.action == "append":
        entry = store.append_entry(
            lease,
            entry_type=EntryType(args.entry_type),
            body=args.body,
            idempotency_key=args.idempotency_key,
            app_proof=proof,
        )
        return {
            "ok": True,
            "action": "append",
            "entry": {
                "entry_id": entry.entry_id,
                "stream_id": entry.stream_id,
                "session_id": entry.session_id,
                "type": entry.type.value,
                "body_sha256": entry.body_sha256,
                "idempotency_key": entry.idempotency_key,
            },
        }
    if args.action == "transition":
        state = store.transition_session(
            lease,
            to_state=SessionState(args.to_state),
            reason=args.reason,
            app_proof=proof,
        )
        return {"ok": True, "action": "transition", "state": state.value}
    if args.action == "close":
        state = store.close_session(lease, reason=args.reason, app_proof=proof)
        return {"ok": True, "action": "close", "state": state.value}
    raise ValueError(f"unsupported GUI lease action: {args.action}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = _run(args)
    except (OSError, ValueError, SessionStreamError) as exc:
        print(json.dumps({"ok": False, "action": args.action, "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
