"""Fleet-generic harness heartbeat and clean-exit hook surface."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

from .model import Lease, LeaseHolder
from .store import SessionStreamStore

ENV_PREFIX = "SESSION_STREAM_"


@dataclass(frozen=True)
class HookResult:
    action: str
    stream_id: str
    session_id: str
    state: str
    expires_at: str | None = None


def lease_from_environment(environment: Mapping[str, str] | None = None) -> Lease:
    """Load the exact harness-owned lease envelope supplied at process start."""
    values = environment or os.environ

    def required(name: str) -> str:
        value = values.get(f"{ENV_PREFIX}{name}", "").strip()
        if not value:
            raise ValueError(f"missing required hook environment: {ENV_PREFIX}{name}")
        return value

    holder = LeaseHolder(
        agent=required("AGENT"),
        harness=required("HARNESS"),
        instance_id=required("INSTANCE_ID"),
        task_id=values.get(f"{ENV_PREFIX}TASK_ID") or None,
        process_id=int(required("PROCESS_ID")),
    )
    holder.validate()
    return Lease(
        stream_id=required("ID"),
        session_id=required("SESSION_ID"),
        lease_id=required("LEASE_ID"),
        generation=int(required("GENERATION")),
        fencing_token=int(required("FENCING_TOKEN")),
        holder=holder,
        heartbeat_at=values.get(f"{ENV_PREFIX}HEARTBEAT_AT", "1970-01-01T00:00:00Z"),
        expires_at=values.get(f"{ENV_PREFIX}EXPIRES_AT", "1970-01-01T00:00:00Z"),
        ttl_seconds=int(values.get(f"{ENV_PREFIX}TTL_SECONDS", "300")),
        version=int(values.get(f"{ENV_PREFIX}VERSION", "1")),
    )


def heartbeat_hook(
    store: SessionStreamStore,
    lease: Lease,
    *,
    now: datetime | None = None,
) -> HookResult:
    """Renew the exact holder without relying on model-authored commands."""
    renewed = store.heartbeat(lease, now=now)
    return HookResult(
        action="heartbeat",
        stream_id=renewed.stream_id,
        session_id=renewed.session_id,
        state=store.session_state(renewed.stream_id, renewed.session_id).value,
        expires_at=renewed.expires_at,
    )


def clean_exit_hook(
    store: SessionStreamStore,
    lease: Lease,
    *,
    now: datetime | None = None,
) -> HookResult:
    """Close the exact session idempotently when its harness exits cleanly."""
    state = store.close_session(lease, now=now)
    return HookResult(
        action="close",
        stream_id=lease.stream_id,
        session_id=lease.session_id,
        state=state.value,
    )
