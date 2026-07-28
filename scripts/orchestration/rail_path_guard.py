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
    # Sibling deploy targets of agents_extensions/shared (deployed rule/agent/hook
    # copies are the same tamper class as .claude/**): .gemini/** is git-tracked;
    # .codex/** is gitignored local deploy state, so only the hook/dispatch layers
    # ever see it — the pattern still binds there. .agent/** is DELIBERATELY not a
    # rail path: it is per-session runtime scratch (babysit files, handoffs, tmp)
    # written constantly by live drivers; requiring receipts for it would halt the
    # fleet, and being gitignored it can never reach a PR diff anyway.
    ".gemini/**",
    ".codex/**",
    # The CI and merge-hook implementations are enforcement layers themselves;
    # leaving either mutable without an approval would make the other layers
    # cosmetic rather than defense in depth.
    ".github/workflows/ci.yml",
    "agents_extensions/shared/hooks/guard-pr-merge.py",
    "agents_extensions/shared/hooks/guard-primary-checkout-write.py",
)

APPROVED_RECEIPT_SOURCE_KINDS = frozenset({"api", "bridge"})
APPROVED_ISSUERS = frozenset({"operator", "advisor"})
# This is deliberately narrower than a generic opaque identifier.  It is the
# one receipt grammar shared by issuance, schema validation, the PR-body
# declaration parser, and every production receipt fetch.
RAIL_APPROVAL_RECEIPT_ID_PATTERN = r"rail-approval-[0-9a-f]{32}"
RAIL_APPROVAL_RECEIPT_ID = re.compile(rf"^{RAIL_APPROVAL_RECEIPT_ID_PATTERN}$")
RAIL_APPROVAL_TRAILER_LABEL = "Rail-Approval-Receipt"
RAIL_APPROVAL_TRAILER_PREFIX = f"{RAIL_APPROVAL_TRAILER_LABEL}:"
RAIL_APPROVAL_TRAILER = re.compile(
    rf"^{re.escape(RAIL_APPROVAL_TRAILER_PREFIX)} ({RAIL_APPROVAL_RECEIPT_ID_PATTERN})$"
)
HEAD_SHA = re.compile(r"^[0-9a-f]{40}$")
_RECEIPT_VALIDATOR: Draft202012Validator | None = None


class RailPathDecisionKind(StrEnum):
    """The typed result of a rail-path authorization decision."""

    ALLOW = "allow"
    DENY = "deny"


class RailApprovalDeclarationKind(StrEnum):
    """Typed status for CI's untrusted PR-body receipt locator."""

    NOT_REQUIRED = "not_required"
    PRESENT = "present"
    MISSING = "missing"
    MALFORMED = "malformed"
    MULTIPLE = "multiple"


class RailApprovalPathBinding(StrEnum):
    """How a receipt's owned paths bind to the current candidate paths."""

    MUTATION_CONTAINMENT = "mutation_containment"
    PR_DIFF_EXACT_SET = "pr_diff_exact_set"


@dataclass(frozen=True, slots=True)
class RailPathDecision:
    """A deterministic authorization result suitable for every enforcement layer."""

    kind: RailPathDecisionKind
    reason: str
    rail_paths: tuple[str, ...]

    @property
    def allowed(self) -> bool:
        return self.kind is RailPathDecisionKind.ALLOW


@dataclass(frozen=True, slots=True)
class RailApprovalDeclaration:
    """A declaration result; unlike ``RailPathDecision`` it grants no authority."""

    kind: RailApprovalDeclarationKind
    reason: str
    rail_paths: tuple[str, ...]
    receipt_id: str | None = None

    @property
    def is_present(self) -> bool:
        """Whether one syntactically valid, still-untrusted locator was found."""
        return self.kind is RailApprovalDeclarationKind.PRESENT


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
        if not RAIL_APPROVAL_RECEIPT_ID.fullmatch(receipt_id):
            raise RailApprovalReceiptError("rail approval receipt ID has an invalid rail-approval shape")
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


def rail_paths_from_candidates(candidate_paths: Sequence[str]) -> tuple[str, ...]:
    """Normalize candidate paths and return the protected subset, fail-closed on bad input."""
    normalized = tuple(normalize_repository_path(path) for path in candidate_paths)
    return tuple(path for path in normalized if is_rail_path(path))


def parse_rail_approval_declaration(body: object) -> RailApprovalDeclaration:
    """Parse exactly one standalone PR-body receipt trailer as an untrusted locator.

    This deliberately does not retrieve a receipt or make an authorization
    decision.  CI can only attest that a syntactically exact locator is present;
    the merge guard later re-fetches the referenced receipt from production and
    applies all authority bindings.
    """
    if not isinstance(body, str):
        return RailApprovalDeclaration(
            RailApprovalDeclarationKind.MALFORMED,
            "rail_approval_declaration_body_unreadable",
            (),
        )
    occurrences = body.count(RAIL_APPROVAL_TRAILER_PREFIX)
    if occurrences == 0:
        return RailApprovalDeclaration(
            RailApprovalDeclarationKind.MISSING,
            "rail_approval_declaration_missing",
            (),
        )
    if occurrences != 1:
        return RailApprovalDeclaration(
            RailApprovalDeclarationKind.MULTIPLE,
            "rail_approval_declaration_multiple",
            (),
        )
    match = next(
        (
            RAIL_APPROVAL_TRAILER.fullmatch(line)
            for line in body.splitlines()
            if RAIL_APPROVAL_TRAILER_PREFIX in line
        ),
        None,
    )
    if match is None:
        return RailApprovalDeclaration(
            RailApprovalDeclarationKind.MALFORMED,
            "rail_approval_declaration_malformed",
            (),
        )
    return RailApprovalDeclaration(
        RailApprovalDeclarationKind.PRESENT,
        "rail_approval_declaration_present",
        (),
        match.group(1),
    )


def inspect_rail_approval_declaration(
    *,
    candidate_paths: Sequence[str],
    body: object,
) -> RailApprovalDeclaration:
    """Classify CI's diff and parse its PR-body declaration without deciding authority."""
    rail_paths = rail_paths_from_candidates(candidate_paths)
    if not rail_paths:
        return RailApprovalDeclaration(
            RailApprovalDeclarationKind.NOT_REQUIRED,
            "non_rail_paths",
            (),
        )
    declaration = parse_rail_approval_declaration(body)
    return RailApprovalDeclaration(
        declaration.kind,
        declaration.reason,
        rail_paths,
        declaration.receipt_id,
    )


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
        if not RAIL_APPROVAL_RECEIPT_ID.fullmatch(receipt_id):
            raise RailApprovalReceiptError(
                "rail approval receipt ID has an invalid rail-approval shape"
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
    path_binding: RailApprovalPathBinding,
    now: datetime,
) -> str | None:
    """Return a refusal reason, or ``None`` only for a current path binding."""
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
    rail_path_set = frozenset(rail_paths)
    if path_binding is RailApprovalPathBinding.PR_DIFF_EXACT_SET:
        if owned_paths != rail_path_set:
            return "rail_approval_path_set_mismatch"
    elif path_binding is RailApprovalPathBinding.MUTATION_CONTAINMENT:
        if not rail_path_set.issubset(owned_paths):
            return "rail_approval_path_mismatch"
    else:  # Runtime callers do not get a permissive fallback for an unknown mode.
        return "invalid_rail_approval_path_binding"
    return None


def decide_rail_path_mutation(
    *,
    task_id: str,
    candidate_paths: Sequence[str],
    head_sha: str,
    receipt: VerifiedRailApprovalReceipt | None = None,
    path_binding: RailApprovalPathBinding = RailApprovalPathBinding.MUTATION_CONTAINMENT,
    now: Callable[[], datetime] = _utc_now,
) -> RailPathDecision:
    """Allow non-rail paths; require a current approval for rail paths.

    ``candidate_paths`` are mutation targets, not ownership globs.  A malformed
    target is denied rather than guessed, while ordinary non-rail paths remain
    unaffected by absent receipts.  Dispatch and checkout-write hooks check a
    bounded mutation attempt, so containment permits an approved larger scope.
    The merge guard passes ``PR_DIFF_EXACT_SET`` because it sees the complete
    current rail diff: equality prevents a receipt for an earlier path set from
    being reused after the PR's protected scope changes.
    """
    try:
        rail_paths = rail_paths_from_candidates(candidate_paths)
    except RailApprovalReceiptError:
        return RailPathDecision(RailPathDecisionKind.DENY, "invalid_candidate_path", ())
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
        path_binding=path_binding,
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
    path_binding: RailApprovalPathBinding = RailApprovalPathBinding.MUTATION_CONTAINMENT,
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
        path_binding=path_binding,
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
        path_binding=path_binding,
        now=now,
    )
