"""Approved-source authority receipts for TrailSpec summons.

Authority never comes from a path, a local JSON projection, or caller-supplied
payload.  The runner receives an approved bridge/API source at construction and
re-fetches an opaque receipt ID from that source before it can record a receipt.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from jsonschema import Draft202012Validator, FormatChecker

from .models import TrailRun, TrailRunnerError
from .store import digest_json

PROJECT_ROOT = Path(__file__).resolve().parents[3]
AUTHORITY_RECEIPT_SCHEMA_PATH = (
    PROJECT_ROOT / "agents_extensions/shared/schemas/trail-authority-receipt.v1.schema.json"
)
OPAQUE_RECEIPT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
APPROVED_SOURCE_KINDS = frozenset({"api", "bridge"})
_AUTHORITY_RECEIPT_VALIDATOR: Draft202012Validator | None = None


class AuthorityReceiptError(TrailRunnerError):
    """Raised when an authority receipt is absent, malformed, stale, or unbound."""


class AuthorityReceiptSource(Protocol):
    """A provisioned bridge/API source; it is never selected from user input."""

    source_id: str
    source_kind: str

    def fetch_authority_receipt(self, receipt_id: str) -> Mapping[str, Any]:
        """Re-fetch one receipt by its opaque external identifier."""


class LeaseObserver(Protocol):
    """Approved external observation of the lease/fence currently held by a run."""

    def observe_lease(self, run: TrailRun) -> Mapping[str, Any]:
        """Return the current lease identity, step, and optional current PR head."""


@dataclass(frozen=True, slots=True)
class VerifiedAuthorityReceipt:
    """A schema-valid receipt re-fetched and bound to the current external lease."""

    payload: dict[str, Any]
    source_id: str
    digest: str

    @property
    def receipt_id(self) -> str:
        return str(self.payload["receipt_id"])


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _parse_time(value: object, *, field: str) -> datetime:
    if not isinstance(value, str):
        raise AuthorityReceiptError(f"authority receipt {field} must be an RFC3339 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AuthorityReceiptError(f"authority receipt {field} is not an RFC3339 timestamp") from exc
    if parsed.tzinfo is None:
        raise AuthorityReceiptError(f"authority receipt {field} must include a timezone")
    return parsed.astimezone(UTC)


def _validator() -> Draft202012Validator:
    """Build the immutable receipt validator once without caching receipt payloads."""
    global _AUTHORITY_RECEIPT_VALIDATOR
    if _AUTHORITY_RECEIPT_VALIDATOR is not None:
        return _AUTHORITY_RECEIPT_VALIDATOR
    try:
        schema = json.loads(AUTHORITY_RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AuthorityReceiptError(f"cannot load authority receipt schema: {exc}") from exc
    if not isinstance(schema, dict):
        raise AuthorityReceiptError("authority receipt schema root must be an object")
    _AUTHORITY_RECEIPT_VALIDATOR = Draft202012Validator(schema, format_checker=FormatChecker())
    return _AUTHORITY_RECEIPT_VALIDATOR


def validate_authority_receipt_data(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Schema-validate an externally fetched receipt before inspecting its fields."""
    if not isinstance(payload, Mapping):
        raise AuthorityReceiptError("authority source returned a non-object receipt")
    receipt = dict(payload)
    errors = sorted(
        _validator().iter_errors(receipt),
        key=lambda error: tuple(error.path),
    )
    if errors:
        error = errors[0]
        raise AuthorityReceiptError(
            f"authority receipt schema violation: {error.message} at {error.json_path}"
        )
    issued_at = _parse_time(receipt["issued_at"], field="issued_at")
    expires_at = _parse_time(receipt["expires_at"], field="expires_at")
    if expires_at <= issued_at:
        raise AuthorityReceiptError("authority receipt expiry must be after issue time")
    return receipt


class ApprovedAuthorityReceiptResolver:
    """Validate receipts from a fixed bridge/API and current external lease evidence."""

    def __init__(
        self,
        source: AuthorityReceiptSource,
        lease_observer: LeaseObserver,
        *,
        approved_issuers: set[str] | frozenset[str],
        now: Callable[[], datetime] = _utc_now,
    ) -> None:
        if getattr(source, "source_kind", None) not in APPROVED_SOURCE_KINDS:
            raise AuthorityReceiptError("authority source must be a provisioned bridge or API")
        if not isinstance(getattr(source, "source_id", None), str) or not source.source_id:
            raise AuthorityReceiptError("authority source must have a stable source_id")
        if not approved_issuers:
            raise AuthorityReceiptError("authority resolver requires at least one approved issuer")
        self.source = source
        self.source_id = source.source_id
        self.lease_observer = lease_observer
        self.approved_issuers = frozenset(approved_issuers)
        self.now = now

    def fetch(self, authority_receipt_id: str, run: TrailRun) -> dict[str, Any]:
        """Re-fetch and bind a resume receipt; no local file path can reach this path."""
        if not OPAQUE_RECEIPT_ID.fullmatch(authority_receipt_id):
            raise AuthorityReceiptError("authority receipt ID must be an opaque approved-source identifier")
        try:
            fetched = self.source.fetch_authority_receipt(authority_receipt_id)
        except AuthorityReceiptError:
            raise
        except Exception as exc:
            raise AuthorityReceiptError("approved authority source could not re-fetch receipt") from exc
        receipt = validate_authority_receipt_data(fetched)
        if receipt["receipt_id"] != authority_receipt_id:
            raise AuthorityReceiptError("authority source receipt ID does not match requested ID")
        self._validate_common(receipt)
        self._validate_run_binding(receipt, run)
        self._validate_current_lease(receipt, run)
        return receipt

    def revalidate(self, receipt: Mapping[str, Any]) -> VerifiedAuthorityReceipt:
        """Re-fetch an already stored receipt and prove the immutable payload is unchanged."""
        stored = validate_authority_receipt_data(receipt)
        receipt_id = str(stored["receipt_id"])
        try:
            fetched = self.source.fetch_authority_receipt(receipt_id)
        except AuthorityReceiptError:
            raise
        except Exception as exc:
            raise AuthorityReceiptError("approved authority source could not re-fetch receipt") from exc
        current = validate_authority_receipt_data(fetched)
        if digest_json(current) != digest_json(stored):
            raise AuthorityReceiptError("re-fetched authority receipt differs from consumed evidence")
        self._validate_common(current)
        return VerifiedAuthorityReceipt(
            payload=current,
            source_id=self.source.source_id,
            digest=digest_json(current),
        )

    def _validate_common(self, receipt: Mapping[str, Any]) -> None:
        issuer = receipt["issuer"]
        if issuer not in self.approved_issuers:
            raise AuthorityReceiptError(f"authority receipt issuer {issuer!r} is not approved")
        if _parse_time(receipt["expires_at"], field="expires_at") <= self.now().astimezone(UTC):
            raise AuthorityReceiptError("authority receipt has expired")

    @staticmethod
    def _validate_run_binding(receipt: Mapping[str, Any], run: TrailRun) -> None:
        expected = {
            "run_id": run.run_id,
            "trail_id": run.trail_id,
            "trail_version": run.trail_version,
            "trail_hash": run.trail_hash,
            "step_id": run.cursor_step_id,
            "cursor_generation": run.cursor_generation,
        }
        for field, value in expected.items():
            if receipt.get(field) != value:
                raise AuthorityReceiptError(
                    f"authority receipt {field} does not bind the current run state"
                )

    def _validate_current_lease(self, receipt: Mapping[str, Any], run: TrailRun) -> None:
        try:
            observed = self.lease_observer.observe_lease(run)
        except Exception as exc:
            raise AuthorityReceiptError("current lease observation is unavailable") from exc
        if not isinstance(observed, Mapping):
            raise AuthorityReceiptError("current lease observation is not an object")
        expected = {
            "run_id": run.run_id,
            "step_id": run.cursor_step_id,
            "lease_id": receipt["lease_id"],
            "lease_generation": receipt["lease_generation"],
            "fencing_token": receipt["fencing_token"],
        }
        for field, value in expected.items():
            if observed.get(field) != value:
                raise AuthorityReceiptError(
                    f"authority receipt {field} does not match current external lease"
                )
        receipt_head = receipt.get("pr_head")
        if receipt_head is not None and observed.get("pr_head") != receipt_head:
            raise AuthorityReceiptError("authority receipt PR head is stale")
