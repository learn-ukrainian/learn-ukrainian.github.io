#!/usr/bin/env python3
"""Fail-closed authorization for mutations to the fleet's control rails.

The guard deliberately separates *classification* from receipt retrieval.  A
caller supplies exact candidate paths and a current commit SHA; this module
decides whether those paths are ordinary work or rail mutations.  Rail
mutations require a receipt that was re-fetched from a provisioned API/bridge,
following the same authority boundary as ``trails.authority``.  A local JSON
file, an environment claim, an X-Agent trailer, or a model name is never
authority.

The decision function is pure after a receipt has been resolved.  Receipt I/O
is isolated in :class:`ApprovedRailApprovalReceiptResolver` so every
enforcement layer uses the same schema and binding rules.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol

from jsonschema import Draft202012Validator, FormatChecker

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAIL_APPROVAL_RECEIPT_SCHEMA_PATH = (
    PROJECT_ROOT / "agents_extensions/shared/schemas/rail-approval-receipt.v1.schema.json"
)

# Every pattern is matched against the complete normalized repository-relative
# path.  Do not replace this with substring matching: e.g. a learner document
# mentioning ``model_catalog.yaml`` is not a control-rail mutation.
RAIL_PATH_PATTERNS = (
    "agents_extensions/shared/rules/**",
    "agents_extensions/**/agents/**",
    "agents_extensions/**/hooks/**",
    "scripts/guardrails/**",
    "scripts/delegate.py",
    "scripts/agent_runtime/codex_hook_policy.py",
    "scripts/orchestration/rail_approval.py",
    "scripts/orchestration/rail_path_guard.py",
    "scripts/api/main.py",
    "scripts/api/rail_approval_router.py",
    "scripts/config/model_catalog.yaml",
    "agents_extensions/shared/rules/model-assignment.md",
    "scripts/config/fleet_taxonomy.yaml",
    "agents_extensions/shared/schemas/fleet-taxonomy*.schema.json",
    "scripts/config/trails/**",
    "agents_extensions/shared/schemas/trailspec*",
    "agents_extensions/shared/schemas/trailspec*/**",
    "agents_extensions/shared/schemas/step-receipt*",
    "agents_extensions/shared/schemas/step-receipt*/**",
    "agents_extensions/shared/schemas/command-receipt*",
    "agents_extensions/shared/schemas/command-receipt*/**",
    "agents_extensions/shared/schemas/rail-approval-receipt*",
    "agents_extensions/shared/schemas/rail-approval-receipt*/**",
    ".claude/**",
    # The CI and merge-hook implementations are enforcement layers themselves;
    # leaving either mutable without an approval would make the other layers
    # cosmetic rather than defense in depth.
    ".github/workflows/ci.yml",
    "agents_extensions/shared/hooks/guard-pr-merge.py",
    "agents_extensions/shared/hooks/guard-primary-checkout-write.py",
)

APPROVED_RECEIPT_SOURCE_KINDS = frozenset({"api", "bridge"})
APPROVED_ISSUERS = frozenset({"operator", "advisor"})
OPAQUE_RECEIPT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
HEAD_SHA = re.compile(r"^[0-9a-f]{40}$")
_RECEIPT_VALIDATOR: Draft202012Validator | None = None


class RailPathDecisionKind(StrEnum):
    """The typed result of a rail-path authorization decision."""

    ALLOW = "allow"
    DENY = "deny"


@dataclass(frozen=True, slots=True)
class RailPathDecision:
    """A deterministic authorization result suitable for every enforcement layer."""

    kind: RailPathDecisionKind
    reason: str
    rail_paths: tuple[str, ...]

    @property
    def allowed(self) -> bool:
        return self.kind is RailPathDecisionKind.ALLOW


class RailApprovalReceiptError(ValueError):
    """A receipt could not prove authorization for a rail mutation."""


class RailApprovalReceiptStore(Protocol):
    """A provisioned external receipt source, never a caller-controlled file."""

    source_id: str
    source_kind: str

    def fetch_rail_approval_receipt(self, receipt_id: str) -> Mapping[str, Any]:
        """Re-fetch one immutable approval receipt by opaque identifier."""


def _monitor_api_get(path: str) -> tuple[int, str, Mapping[str, str]]:
    """Use the established Monitor client rather than a caller-chosen URL."""
    from scripts.ai_agent_bridge.monitor_client import MonitorClient

    return MonitorClient()._get(path)


class MonitorRailApprovalReceiptStore:
    """The provisioned Monitor API source used by production enforcement.

    Receipt issuance writes the Monitor-owned runtime registry, but a caller
    must use this API projection to fetch it.  Reading a worktree-local JSON
    file directly would turn the receipt into a forgeable caller projection.
    """

    source_id = "monitor-api:/api/rail-approvals"
    source_kind = "api"

    def __init__(
        self,
        *,
        get: Callable[[str], tuple[int, str, Mapping[str, str]]] | None = None,
    ) -> None:
        self._get = get or _monitor_api_get

    def fetch_rail_approval_receipt(self, receipt_id: str) -> Mapping[str, Any]:
        if not OPAQUE_RECEIPT_ID.fullmatch(receipt_id):
            raise RailApprovalReceiptError("rail approval receipt ID must be an opaque approved-source identifier")
        try:
            status, body, _headers = self._get(f"/api/rail-approvals/{receipt_id}")
        except RailApprovalReceiptError:
            raise
        except Exception as exc:
            raise RailApprovalReceiptError("Monitor rail approval API could not re-fetch receipt") from exc
        if status != 200:
            raise RailApprovalReceiptError("Monitor rail approval API could not re-fetch receipt")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            raise RailApprovalReceiptError("Monitor rail approval API returned invalid JSON") from exc
        if not isinstance(payload, Mapping):
            raise RailApprovalReceiptError("Monitor rail approval API returned a non-object receipt")
        return payload


class ProvisionedRailApprovalReceiptBridge:
    """Adapter for a deployment-provisioned bridge when Monitor is unavailable.

    This is intentionally dependency-injected at process bootstrap.  There is
    no environment-variable URL, local-file, or user-supplied bridge fallback:
    those would let a write caller select its own approval authority.
    """

    source_kind = "bridge"

    def __init__(
        self,
        *,
        source_id: str,
        fetcher: Callable[[str], Mapping[str, Any]],
    ) -> None:
        if not source_id:
            raise RailApprovalReceiptError("rail approval bridge must have a stable source_id")
        self.source_id = source_id
        self._fetcher = fetcher

    def fetch_rail_approval_receipt(self, receipt_id: str) -> Mapping[str, Any]:
        return self._fetcher(receipt_id)


@dataclass(frozen=True, slots=True)
class VerifiedRailApprovalReceipt:
    """A receipt schema-checked after a successful external re-fetch."""

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
        raise RailApprovalReceiptError(f"rail approval receipt {field} must be an RFC3339 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RailApprovalReceiptError(
            f"rail approval receipt {field} is not an RFC3339 timestamp"
        ) from exc
    if parsed.tzinfo is None:
        raise RailApprovalReceiptError(
            f"rail approval receipt {field} must include a timezone"
        )
    return parsed.astimezone(UTC)


def _validator() -> Draft202012Validator:
    """Load the immutable versioned schema once; never cache receipt payloads."""
    global _RECEIPT_VALIDATOR
    if _RECEIPT_VALIDATOR is not None:
        return _RECEIPT_VALIDATOR
    try:
        schema = json.loads(RAIL_APPROVAL_RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RailApprovalReceiptError(
            f"cannot load rail approval receipt schema: {exc}"
        ) from exc
    if not isinstance(schema, dict):
        raise RailApprovalReceiptError("rail approval receipt schema root must be an object")
    _RECEIPT_VALIDATOR = Draft202012Validator(schema, format_checker=FormatChecker())
    return _RECEIPT_VALIDATOR


def normalize_repository_path(value: object) -> str:
    """Normalize one exact repository-relative path or reject it fail-closed."""
    if not isinstance(value, str) or not value:
        raise RailApprovalReceiptError("candidate path must be a non-empty string")
    if "\\" in value or value.startswith("/") or "\x00" in value:
        raise RailApprovalReceiptError("candidate path must be a relative POSIX path")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise RailApprovalReceiptError("candidate path is not normalized")
    if any(any(char in part for char in "*?[") for part in parts):
        raise RailApprovalReceiptError("candidate path must be exact, not a glob")
    return "/".join(parts)


def _glob_to_regex(pattern: str) -> re.Pattern[str]:
    """Compile a small POSIX path glob without substring or OS-dependent matching."""
    pieces = pattern.split("/")
    expression = "^"
    for index, piece in enumerate(pieces):
        if piece == "**":
            if index == len(pieces) - 1:
                expression += r"(?:/.*)?"
            else:
                expression += r"(?:/[^/]+)*"
            continue
        if index:
            expression += "/"
        expression += "".join(
            "[^/]*" if char == "*" else re.escape(char)
            for char in piece
        )
    return re.compile(expression + "$")


_RAIL_PATH_REGEXES = tuple(_glob_to_regex(pattern) for pattern in RAIL_PATH_PATTERNS)


def is_rail_path(path: str) -> bool:
    """Return whether an exact, normalized path belongs to the narrow deny-list."""
    return any(regex.fullmatch(path) is not None for regex in _RAIL_PATH_REGEXES)


def validate_rail_approval_receipt_data(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Schema-validate a remotely fetched P6 receipt before inspecting bindings."""
    if not isinstance(payload, Mapping):
        raise RailApprovalReceiptError("rail approval source returned a non-object receipt")
    receipt = dict(payload)
    errors = sorted(_validator().iter_errors(receipt), key=lambda error: tuple(error.path))
    if errors:
        error = errors[0]
        raise RailApprovalReceiptError(
            f"rail approval receipt schema violation: {error.message} at {error.json_path}"
        )
    issued_at = _parse_time(receipt["issued_at"], field="issued_at")
    expires_at = _parse_time(receipt["expires_at"], field="expires_at")
    if expires_at <= issued_at:
        raise RailApprovalReceiptError("rail approval receipt expiry must be after issue time")
    owned_paths = tuple(receipt["owned_paths"])
    try:
        normalized = tuple(normalize_repository_path(path) for path in owned_paths)
    except RailApprovalReceiptError as exc:
        raise RailApprovalReceiptError(f"rail approval receipt owned_paths invalid: {exc}") from exc
    if normalized != owned_paths or len(set(normalized)) != len(normalized):
        raise RailApprovalReceiptError("rail approval receipt owned_paths must be normalized and unique")
    return receipt


def _receipt_digest(receipt: Mapping[str, Any]) -> str:
    """Stable digest without importing a TrailSpec-only implementation."""
    import hashlib

    canonical = json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class ApprovedRailApprovalReceiptResolver:
    """Re-fetch P6 receipts from a fixed API/bridge and reject local projections."""

    def __init__(
        self,
        store: RailApprovalReceiptStore,
        *,
        now: Callable[[], datetime] = _utc_now,
    ) -> None:
        if getattr(store, "source_kind", None) not in APPROVED_RECEIPT_SOURCE_KINDS:
            raise RailApprovalReceiptError(
                "rail approval source must be a provisioned bridge or API"
            )
        if not isinstance(getattr(store, "source_id", None), str) or not store.source_id:
            raise RailApprovalReceiptError("rail approval source must have a stable source_id")
        self.store = store
        self.now = now

    def fetch(self, receipt_id: str) -> VerifiedRailApprovalReceipt:
        """Re-fetch a receipt; any unreadable store is an authorization failure."""
        if not OPAQUE_RECEIPT_ID.fullmatch(receipt_id):
            raise RailApprovalReceiptError(
                "rail approval receipt ID must be an opaque approved-source identifier"
            )
        try:
            fetched = self.store.fetch_rail_approval_receipt(receipt_id)
        except RailApprovalReceiptError:
            raise
        except Exception as exc:
            raise RailApprovalReceiptError(
                "approved rail approval source could not re-fetch receipt"
            ) from exc
        receipt = validate_rail_approval_receipt_data(fetched)
        if receipt["receipt_id"] != receipt_id:
            raise RailApprovalReceiptError(
                "rail approval source receipt ID does not match requested ID"
            )
        if receipt["issuer"] not in APPROVED_ISSUERS:
            raise RailApprovalReceiptError(
                f"rail approval receipt issuer {receipt['issuer']!r} is not approved"
            )
        if _parse_time(receipt["expires_at"], field="expires_at") <= self.now().astimezone(UTC):
            raise RailApprovalReceiptError("rail approval receipt has expired")
        return VerifiedRailApprovalReceipt(
            payload=receipt,
            source_id=self.store.source_id,
            digest=_receipt_digest(receipt),
        )


def build_production_rail_approval_receipt_resolver(
    *,
    bridge: RailApprovalReceiptStore | None = None,
) -> ApprovedRailApprovalReceiptResolver:
    """Build the fixed production resolver without caller-selected authority.

    Monitor is the ordinary production source.  A deployment with an approved
    bridge may inject it at process bootstrap when Monitor is unavailable; the
    bridge must carry ``source_kind='bridge'`` and is still schema/binding
    checked by :class:`ApprovedRailApprovalReceiptResolver`.  Enforcement code
    never falls back to a local file, arbitrary URL, or environment claim.
    """
    if bridge is not None:
        if getattr(bridge, "source_kind", None) != "bridge":
            raise RailApprovalReceiptError("rail approval fallback must be a provisioned bridge")
        return ApprovedRailApprovalReceiptResolver(bridge)
    return ApprovedRailApprovalReceiptResolver(MonitorRailApprovalReceiptStore())


def _receipt_authorizes(
    receipt: VerifiedRailApprovalReceipt,
    *,
    task_id: str,
    head_sha: str,
    rail_paths: tuple[str, ...],
    now: datetime,
) -> str | None:
    """Return a refusal reason, or ``None`` only for an exact current binding."""
    try:
        payload = validate_rail_approval_receipt_data(receipt.payload)
    except RailApprovalReceiptError:
        return "invalid_rail_approval_receipt"
    if payload["issuer"] not in APPROVED_ISSUERS:
        return "unapproved_rail_approval_issuer"
    if _parse_time(payload["expires_at"], field="expires_at") <= now.astimezone(UTC):
        return "expired_rail_approval_receipt"
    if payload["task_id"] != task_id:
        return "rail_approval_task_mismatch"
    if payload["head_sha"] != head_sha:
        return "rail_approval_head_mismatch"
    owned_paths = frozenset(payload["owned_paths"])
    if any(path not in owned_paths for path in rail_paths):
        return "rail_approval_path_mismatch"
    return None


def decide_rail_path_mutation(
    *,
    task_id: str,
    candidate_paths: Sequence[str],
    head_sha: str,
    receipt: VerifiedRailApprovalReceipt | None = None,
    now: Callable[[], datetime] = _utc_now,
) -> RailPathDecision:
    """Allow non-rail paths; require an exact, current approval for rail paths.

    ``candidate_paths`` are mutation targets, not ownership globs.  A malformed
    target is denied rather than guessed, while ordinary non-rail paths remain
    unaffected by absent receipts.
    """
    try:
        normalized = tuple(normalize_repository_path(path) for path in candidate_paths)
    except RailApprovalReceiptError:
        return RailPathDecision(RailPathDecisionKind.DENY, "invalid_candidate_path", ())
    rail_paths = tuple(path for path in normalized if is_rail_path(path))
    if not rail_paths:
        return RailPathDecision(RailPathDecisionKind.ALLOW, "non_rail_paths", ())
    if not isinstance(task_id, str) or not task_id.strip():
        return RailPathDecision(RailPathDecisionKind.DENY, "invalid_task_id", rail_paths)
    if not isinstance(head_sha, str) or not HEAD_SHA.fullmatch(head_sha):
        return RailPathDecision(RailPathDecisionKind.DENY, "invalid_head_sha", rail_paths)
    if receipt is None:
        return RailPathDecision(
            RailPathDecisionKind.DENY,
            "rail_approval_receipt_required",
            rail_paths,
        )
    reason = _receipt_authorizes(
        receipt,
        task_id=task_id,
        head_sha=head_sha,
        rail_paths=rail_paths,
        now=now(),
    )
    if reason is not None:
        return RailPathDecision(RailPathDecisionKind.DENY, reason, rail_paths)
    return RailPathDecision(RailPathDecisionKind.ALLOW, "rail_approval_verified", rail_paths)


def decide_rail_path_mutation_with_production_receipt(
    *,
    task_id: str,
    candidate_paths: Sequence[str],
    head_sha: str,
    receipt_id: str | None,
    resolver: ApprovedRailApprovalReceiptResolver | None = None,
    now: Callable[[], datetime] = _utc_now,
) -> RailPathDecision:
    """Resolve a receipt from the fixed source, then make the normal decision.

    This keeps dispatch and hook layers from accidentally trusting a receipt
    payload supplied by their caller.  Source failures become denials rather
    than exceptions that a caller might mishandle as an allow.
    """
    preliminary = decide_rail_path_mutation(
        task_id=task_id,
        candidate_paths=candidate_paths,
        head_sha=head_sha,
        now=now,
    )
    if preliminary.allowed or preliminary.reason != "rail_approval_receipt_required":
        return preliminary
    if receipt_id is None:
        return preliminary
    try:
        receipt = (resolver or build_production_rail_approval_receipt_resolver()).fetch(receipt_id)
    except RailApprovalReceiptError as exc:
        reason = (
            "expired_rail_approval_receipt"
            if "has expired" in str(exc)
            else "rail_approval_receipt_unreadable"
        )
        return RailPathDecision(RailPathDecisionKind.DENY, reason, preliminary.rail_paths)
    return decide_rail_path_mutation(
        task_id=task_id,
        candidate_paths=candidate_paths,
        head_sha=head_sha,
        receipt=receipt,
        now=now,
    )
