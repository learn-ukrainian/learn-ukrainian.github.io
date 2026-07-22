"""Cross-agent epic-stream handoff status + claim (issue #5530).

This is the interim safety path until Sol fleet-comms PR-I (common session
supervisor) owns full automation. It does not invent a second lease model —
it composes ``force_close_expired_session`` + ``open_session`` + typed pins.
"""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .model import EntryType, Lease, LeaseHolder, isoformat_z, parse_timestamp, utc_now
from .store import SessionStreamStore


@dataclass(frozen=True)
class HandoffStatus:
    """Read-only diagnosis for one stream's driver authority."""

    stream_id: str
    session_id: str | None
    session_state: str | None
    lease_state: str | None
    lease_expired: bool | None
    holder_agent: str | None
    holder_harness: str | None
    holder_instance_id: str | None
    holder_process_id: int | None
    holder_process_alive: bool | None
    expires_at: str | None
    heartbeat_at: str | None
    claimable_force_close: bool
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "stream_id": self.stream_id,
            "session_id": self.session_id,
            "session_state": self.session_state,
            "lease_state": self.lease_state,
            "lease_expired": self.lease_expired,
            "holder_agent": self.holder_agent,
            "holder_harness": self.holder_harness,
            "holder_instance_id": self.holder_instance_id,
            "holder_process_id": self.holder_process_id,
            "holder_process_alive": self.holder_process_alive,
            "expires_at": self.expires_at,
            "heartbeat_at": self.heartbeat_at,
            "claimable_force_close": self.claimable_force_close,
            "reason": self.reason,
        }


def _process_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # Process table entry exists; treat as live for force-close safety.
        return True
    return True


def diagnose_handoff(
    store: SessionStreamStore,
    stream_id: str,
    *,
    now: datetime | None = None,
) -> HandoffStatus:
    """Return a portable diagnosis; never mutates the stream."""
    current = now or utc_now()
    dump = store.dump_stream(stream_id)
    sessions = dump.get("sessions") or []
    lease = dump.get("lease")  # current projection (one row per stream)
    live = [s for s in sessions if s.get("state") in {"open", "rolling"}]
    if not live:
        return HandoffStatus(
            stream_id=stream_id,
            session_id=None,
            session_state=None,
            lease_state=None,
            lease_expired=None,
            holder_agent=None,
            holder_harness=None,
            holder_instance_id=None,
            holder_process_id=None,
            holder_process_alive=None,
            expires_at=None,
            heartbeat_at=None,
            claimable_force_close=False,
            reason="no open or rolling session — safe to open a new session",
        )
    session = live[0]
    session_id = str(session["session_id"])
    if lease is None or str(lease.get("session_id") or "") != session_id:
        return HandoffStatus(
            stream_id=stream_id,
            session_id=session_id,
            session_state=str(session.get("state")),
            lease_state=None,
            lease_expired=None,
            holder_agent=None,
            holder_harness=None,
            holder_instance_id=None,
            holder_process_id=None,
            holder_process_alive=None,
            expires_at=None,
            heartbeat_at=None,
            claimable_force_close=False,
            reason="live session without lease projection — refuse claim; investigate dump",
        )
    expires_at = str(lease.get("expires_at") or "")
    heartbeat_at = str(lease.get("heartbeat_at") or "")
    expired = False
    if expires_at:
        expired = current >= parse_timestamp(expires_at)
    pid = int(lease.get("holder_process_id") or 0)
    probe = getattr(store, "_process_probe", None)
    alive = bool(probe(pid)) if callable(probe) else _process_alive(pid)

    lease_state = str(lease.get("state") or "")
    # Dead holder PID is claimable even before wall-clock TTL expires. A crashed
    # local process cannot renew; requiring expiry left launchers blocked for the
    # full launcher TTL (often 6h). Live holders remain untouchable.
    claimable = lease_state == "active" and not alive
    if lease_state == "active" and alive and not expired:
        reason = "live unexpired lease — only the holder may close; claim refused"
    elif lease_state == "active" and alive and expired:
        reason = "lease expired but holder PID still live — claim refused"
    elif claimable:
        if expired:
            reason = "expired lease + dead holder PID — claimable via force-close then open"
        else:
            reason = "dead holder PID (lease unexpired) — claimable via force-close then open"
    else:
        reason = f"lease state {lease_state!r}; inspect dump before claim"
    return HandoffStatus(
        stream_id=stream_id,
        session_id=session_id,
        session_state=str(session.get("state")),
        lease_state=lease_state,
        lease_expired=expired,
        holder_agent=str(lease.get("holder_agent") or "") or None,
        holder_harness=str(lease.get("holder_harness") or "") or None,
        holder_instance_id=str(lease.get("holder_instance_id") or "") or None,
        holder_process_id=pid or None,
        holder_process_alive=alive,
        expires_at=expires_at or None,
        heartbeat_at=heartbeat_at or None,
        claimable_force_close=claimable,
        reason=reason,
    )


def claim_stream(
    store: SessionStreamStore,
    *,
    stream_id: str,
    agent: str,
    harness: str,
    instance_id: str,
    process_id: int,
    lineage_id: str,
    ttl_seconds: int = 6 * 3600,
    task_id: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Force-close if claimable, open a new session, pin the new driver.

    Returns a machine receipt. Raises ``ValueError`` / store errors on refuse.
    """
    current = now or utc_now()
    status = diagnose_handoff(store, stream_id, now=current)
    holder = LeaseHolder(
        agent=agent,
        harness=harness,
        instance_id=instance_id,
        process_id=process_id,
        task_id=task_id,
    )
    holder.validate()
    # Prefer the store's process probe (same as force-close) so tests and
    # production share one liveness definition.
    probe = getattr(store, "_process_probe", None)
    claimer_live = bool(probe(process_id)) if callable(probe) else _process_alive(process_id)
    if not claimer_live:
        raise ValueError("claimer process_id is not live; refuse claim proof")

    force_closed: dict[str, Any] | None = None
    if status.session_id and status.session_state in {"open", "rolling"}:
        if not status.claimable_force_close:
            raise ValueError(f"cannot claim: {status.reason}")
        # Distinct instance from the dead holder is required by the store.
        if status.holder_instance_id and status.holder_instance_id == instance_id:
            raise ValueError("claimer instance_id must differ from the expired holder instance")
        proof = store.force_close_expired_session(
            stream_id=stream_id,
            session_id=status.session_id,
            candidate=holder,
            now=current,
            reason=f"cross-agent handoff claim by {agent}/{harness} (#5530)",
        )
        force_closed = proof.as_dict()

    lease: Lease = store.open_session(
        stream_id=stream_id,
        holder=holder,
        lineage_id=lineage_id,
        ttl_seconds=ttl_seconds,
        now=current,
        reason=f"handoff-claim {agent} takes driver (#5530)",
    )
    pin_body = (
        f"Driver authority: {agent} ({harness}) holds stream {stream_id} as of "
        f"{isoformat_z(current)}. Prior interim drivers stop orchestrating; "
        f"finish only already-watched in-flight work. Issue #5530."
    )
    store.append_entry(
        lease,
        entry_type=EntryType.BINDING_ORDER,
        body=pin_body,
        idempotency_key=f"handoff-claim-driver-{lease.session_id}",
        now=current,
    )
    store.append_entry(
        lease,
        entry_type=EntryType.STATE,
        body=(
            f"HANDOFF CLAIM {isoformat_z(current)}: {agent}/{harness} opened "
            f"session {lease.session_id} (gen {lease.generation}, fence "
            f"{lease.fencing_token}). force_closed={bool(force_closed)}. "
            f"Fold predecessor dual-write into your driver board before driving."
        ),
        idempotency_key=f"handoff-claim-state-{lease.session_id}",
        now=current,
    )
    return {
        "stream_id": stream_id,
        "prior_status": status.as_dict(),
        "force_closed": force_closed,
        "lease": {
            "session_id": lease.session_id,
            "lease_id": lease.lease_id,
            "generation": lease.generation,
            "fencing_token": lease.fencing_token,
            "expires_at": lease.expires_at,
            "holder": {
                "agent": lease.holder.agent,
                "harness": lease.holder.harness,
                "instance_id": lease.holder.instance_id,
                "process_id": lease.holder.process_id,
                "task_id": lease.holder.task_id,
            },
        },
        "next": (
            "Dual-write fold + stream tail; bind exact rollover packet if any "
            "(#5398: never generic detect with N>1)."
        ),
    }


def default_instance_id(agent: str) -> str:
    return f"{agent}-handoff-{uuid.uuid4().hex[:16]}"
