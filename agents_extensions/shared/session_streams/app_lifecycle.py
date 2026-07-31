"""Provider-neutral, fail-closed proof boundary for GUI-native lease holders.

The session-stream store deliberately does not know how any desktop application
stores task state.  A provider adapter reads that state, reduces it to this
privacy-safe envelope, and returns a verified proof only after validating its
own structured readback.  The store then checks freshness and exact fencing.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from .model import HolderKind, LeaseHolder, canonical_json, parse_timestamp, sha256_text

LIFECYCLE_OPERATIONS = frozenset({"acquire", "renew", "append", "transition", "close", "recover"})
LIFECYCLE_STATES = frozenset({"active", "terminal", "absent"})


@dataclass(frozen=True)
class AppLifecycleReceipt:
    """Immutable, privacy-safe evidence read by one registered app adapter."""

    operation: str
    provider: str
    adapter_version: str
    holder: LeaseHolder
    state: str
    observed_at: str
    valid_until: str
    source_schema_digest: str
    source_authority: str
    readback_digest: str
    stream_id: str
    session_id: str | None = None
    lease_id: str | None = None
    generation: int | None = None
    fencing_token: int | None = None
    rollover_id: str | None = None
    receipt_digest: str = ""

    def canonical_payload(self) -> dict[str, object]:
        return {
            "operation": self.operation,
            "provider": self.provider,
            "adapter_version": self.adapter_version,
            "holder": {
                "kind": self.holder.holder_kind.value,
                "agent": self.holder.agent,
                "harness": self.holder.harness,
                "instance_id": self.holder.instance_id,
                "task_id": self.holder.task_id,
                "process_id": self.holder.process_id,
            },
            "state": self.state,
            "observed_at": self.observed_at,
            "valid_until": self.valid_until,
            "source_schema_digest": self.source_schema_digest,
            "source_authority": self.source_authority,
            "readback_digest": self.readback_digest,
            "stream_id": self.stream_id,
            "session_id": self.session_id,
            "lease_id": self.lease_id,
            "generation": self.generation,
            "fencing_token": self.fencing_token,
            "rollover_id": self.rollover_id,
        }

    def computed_digest(self) -> str:
        return sha256_text(canonical_json(self.canonical_payload()))

    def as_dict(self) -> dict[str, object]:
        """The complete canonical receipt retained in immutable event evidence."""
        return {**self.canonical_payload(), "receipt_digest": self.receipt_digest}

    def validate(self) -> None:
        self.holder.validate()
        if self.holder.holder_kind is not HolderKind.APP_THREAD:
            raise ValueError("app lifecycle receipts require an app_thread holder")
        if self.operation not in LIFECYCLE_OPERATIONS:
            raise ValueError("app lifecycle receipt has an unsupported operation")
        if self.state not in LIFECYCLE_STATES:
            raise ValueError("app lifecycle receipt has an unsupported state")
        if not self.provider or not self.adapter_version or not self.stream_id or not self.source_authority:
            raise ValueError("app lifecycle receipt requires provider, adapter_version, and stream_id")
        for label, digest in (
            ("source_schema_digest", self.source_schema_digest),
            ("readback_digest", self.readback_digest),
        ):
            if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest.lower()):
                raise ValueError(f"{label} must be a SHA-256 digest")
        observed = parse_timestamp(self.observed_at)
        if parse_timestamp(self.valid_until) <= observed:
            raise ValueError("app lifecycle receipt validity window is invalid")
        if self.receipt_digest != self.computed_digest():
            raise ValueError("app lifecycle receipt digest mismatch")


@dataclass(frozen=True)
class VerifiedAppLifecycleProof:
    """A receipt whose provider-specific structured readback was verified."""

    receipt: AppLifecycleReceipt
    verifier_id: str

    def validate_for(
        self,
        *,
        operation: str,
        holder: LeaseHolder,
        stream_id: str,
        now: datetime,
        session_id: str | None = None,
        lease_id: str | None = None,
        generation: int | None = None,
        fencing_token: int | None = None,
        state: str = "active",
        rollover_id: str | None = None,
    ) -> None:
        self.receipt.validate()
        if not self.verifier_id:
            raise ValueError("unverified app lifecycle proof")
        receipt = self.receipt
        if receipt.operation != operation or receipt.state != state:
            raise ValueError("app lifecycle proof operation or state mismatch")
        if receipt.holder != holder or receipt.stream_id != stream_id:
            raise ValueError("app lifecycle proof holder or stream mismatch")
        if (receipt.session_id, receipt.lease_id, receipt.generation, receipt.fencing_token) != (
            session_id,
            lease_id,
            generation,
            fencing_token,
        ):
            raise ValueError("app lifecycle proof fenced lease identity mismatch")
        if receipt.rollover_id != rollover_id:
            raise ValueError("app lifecycle proof rollover continuity mismatch")
        observed = parse_timestamp(receipt.observed_at)
        valid_until = parse_timestamp(receipt.valid_until)
        if observed > now or valid_until <= now:
            raise ValueError("app lifecycle proof is future-dated or expired")


class AppLifecycleAdapter(Protocol):
    """Narrow provider adapter; generic storage never reads private app state."""

    def verify(self, receipt: AppLifecycleReceipt) -> VerifiedAppLifecycleProof: ...


@dataclass(frozen=True)
class StructuredReadbackAdapter:
    """Adapter base for a harness that already verified durable structured readback.

    Provider implementations must override this with independent native-source
    validation.  It intentionally has no caller-controlled trust switch.
    """

    provider: str
    adapter_version: str
    verifier_id: str

    def verify(self, receipt: AppLifecycleReceipt) -> VerifiedAppLifecycleProof:
        raise ValueError("provider adapter must independently validate native structured readback")


def make_receipt(**kwargs: object) -> AppLifecycleReceipt:
    """Build a digest-bound receipt without persisting raw provider readback."""
    provisional = AppLifecycleReceipt(receipt_digest="", **kwargs)  # type: ignore[arg-type]
    return AppLifecycleReceipt(receipt_digest=provisional.computed_digest(), **kwargs)  # type: ignore[arg-type]
