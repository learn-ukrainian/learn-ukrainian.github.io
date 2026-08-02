"""Versioned, strict, body-free context-link schema (ADR-018 / #6174).

A context link joins an opaque Entire checkpoint/commit locator to canonical
GitHub, ACP, Fleet, Monitor, rollover, or formal-review evidence. The schema is
deliberately body-free: unknown fields are rejected, and fields or values that
name body-bearing concepts, match known secret/token signatures, look like
long opaque tokens, or contain public Entire refs are refused before anything
is persisted.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

SCHEMA_VERSION = 1

LOCATOR_ID_RE = re.compile(r"^clink_[0-9a-f]{64}$")
SHA256_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
NAMESPACE_RE = re.compile(r"^[a-z][a-z0-9_-]{0,31}:[A-Za-z0-9][A-Za-z0-9._/-]{0,255}$")
CANONICAL_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,255}$")
OPAQUE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
IDENTITY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,255}$")
ROLLOVER_NAMESPACE = "rollover:registry/v1"
ROLLOVER_CANONICAL_ID_RE = re.compile(
    r"^[a-z][a-z0-9-]*/[a-z][a-z0-9-]{0,63}/rollover-[a-z0-9]+(?:-[a-z0-9]+)*$"
)
ROLLOVER_EVIDENCE_LOCATOR_RE = re.compile(
    rf"^{re.escape(ROLLOVER_NAMESPACE)}/{ROLLOVER_CANONICAL_ID_RE.pattern.removeprefix('^').removesuffix('$')}$"
)

ALLOWED_TOP_LEVEL_KEYS = frozenset(
    {
        "schema_version",
        "locator_id",
        "kind",
        "canonical_namespace",
        "canonical_id",
        "canonical_digest",
        "entire_checkpoint_id",
        "git_sha",
        "facets",
        "ingested_at",
    }
)

# Tier-0 headers-only corpus (ADR-018 / rollout plan): mechanically copied,
# allowlisted fields only. No composed intent/outcome/rationale/summary.
ALLOWED_FACET_KEYS = frozenset(
    {
        "repository",
        "source_kind",
        "stream_epic",
        "track",
        "state",
        "labels",
        "touched_paths",
        "actor",
        "model",
        "harness",
        "participants",
        "token_bucket",
        "title",
        "document_path",
        "document_heading",
        "event_ts",
    }
)

FORBIDDEN_KEY_RE = re.compile(
    r"(?i)(prompt|response|transcript|summar|raw_?capture|\bbody\b|bodies|message|artifact|"
    r"secret|password|credential|api[_-]?key|access[_-]?token|refresh[_-]?token|private[_-]?key)"
)

FORBIDDEN_VALUE_PATTERNS = (
    ("private-key", re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |PGP )?PRIVATE KEY-----")),
    ("credential-token", re.compile(r"(?:sk-|gh[pousr]_|AIza)[A-Za-z0-9_-]{16,}")),
    ("aws-access-key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    (
        "jwt-token",
        re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
    ),
    ("bearer-token", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/-]{16,}={0,2}\b")),
    (
        "credential-assignment",
        re.compile(r"(?i)(?:api[_-]?key|access[_-]?token|secret|password)\s*[:=]\s*\S{8,}"),
    ),
    ("public-entire-ref", re.compile(r"refs/entire(?:/|$)")),
)

OPAQUE_RUN_RE = re.compile(r"[A-Za-z0-9_+-]+")
PATH_OPAQUE_RUN_RE = re.compile(r"[A-Za-z0-9+-]+")
GIT_EVIDENCE_LOCATOR_RE = re.compile(r"^git:commit/[0-9a-f]{40}$")

MAX_STRING_BYTES = 1024
MAX_LIST_ITEMS = 64


class SchemaError(ValueError):
    """Raised when a context-link payload violates the body-free schema."""


class LinkKind(StrEnum):
    """Allowlisted canonical receipt kinds a locator may join to."""

    GIT_COMMIT = "git_commit"
    GITHUB_ISSUE = "github_issue"
    GITHUB_PR = "github_pr"
    ACP_CONVERSATION = "acp_conversation"
    FORMAL_REVIEW = "formal_review"
    ROLLOVER = "rollover"
    MONITOR_RUN = "monitor_run"
    FLEET_RECEIPT = "fleet_receipt"


class VerificationStatus(StrEnum):
    """Caller-recorded outcome of resolving evidence against its canonical system."""

    VERIFIED = "verified"
    STALE = "stale"
    PARTIAL_TERMINAL = "partial_terminal"
    DIGEST_MISMATCH = "digest_mismatch"


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def isoformat_z(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("timestamps must be timezone-aware")
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamps must include a timezone")
    return parsed.astimezone(UTC)


def _reject_forbidden_key(path: str) -> None:
    if FORBIDDEN_KEY_RE.search(path):
        raise SchemaError(f"field rejected by body-free rule: {path!r} names a forbidden concept")


def _validate_scalar(
    path: str,
    value: Any,
    *,
    reject_long_opaque: bool = False,
    long_opaque_exemption: re.Pattern[str] | None = None,
) -> None:
    if isinstance(value, bool) or value is None or isinstance(value, int | float):
        return
    if not isinstance(value, str):
        raise SchemaError(f"field {path!r} must be a string, number, or boolean")
    if "\x00" in value:
        raise SchemaError(f"field {path!r} rejected by control-character rule")
    if len(value.encode("utf-8")) > MAX_STRING_BYTES:
        raise SchemaError(f"field {path!r} rejected by size rule")
    for rule, pattern in FORBIDDEN_VALUE_PATTERNS:
        if pattern.search(value):
            raise SchemaError(f"field {path!r} rejected by {rule} rule")
    if reject_long_opaque:
        opaque_runs = [match.group(0) for match in OPAQUE_RUN_RE.finditer(value)]
        split_runs = [run for run in opaque_runs if len(run) >= 16]
        looks_long_opaque = any(len(run) >= 48 for run in opaque_runs) or (
            len(split_runs) >= 2 and sum(map(len, split_runs)) >= 48
        )
        exempt = long_opaque_exemption is not None and long_opaque_exemption.fullmatch(value) is not None
        if looks_long_opaque and not exempt:
            raise SchemaError(f"field {path!r} rejected by long-opaque-token rule")


def validate_identity(
    value: str,
    *,
    field_name: str,
    reject_long_opaque: bool = True,
    long_opaque_exemption: re.Pattern[str] | None = None,
) -> None:
    """Validate one body-free, path-safe externally supplied identity."""
    if not isinstance(value, str) or not IDENTITY_RE.fullmatch(value):
        raise SchemaError(f"{field_name} must be a path-safe identity")
    _validate_scalar(
        field_name,
        value,
        reject_long_opaque=reject_long_opaque,
        long_opaque_exemption=long_opaque_exemption,
    )


def validate_facets(facets: dict[str, Any]) -> None:
    """Enforce the allowlisted, body-free facet contract."""
    if not isinstance(facets, dict):
        raise SchemaError("facets must be an object")
    for key, value in facets.items():
        _reject_forbidden_key(key)
        if key not in ALLOWED_FACET_KEYS:
            raise SchemaError(f"unknown facet field: {key!r}")
        if isinstance(value, list):
            if len(value) > MAX_LIST_ITEMS:
                raise SchemaError(f"facet {key!r} rejected by list-size rule")
            for item in value:
                if key == "touched_paths":
                    _validate_touched_path(item)
                else:
                    _validate_scalar(key, item, reject_long_opaque=True)
        else:
            _validate_scalar(key, value, reject_long_opaque=True)


def _validate_touched_path(value: Any) -> None:
    """Allow real semantic Git paths without admitting opaque path tokens."""
    _validate_scalar("touched_paths", value, reject_long_opaque=False)
    if not isinstance(value, str):
        raise SchemaError("field 'touched_paths' must be a string")
    if value.startswith("/") or "\\" in value or any(
        segment in {"", ".", ".."} for segment in value.split("/")
    ):
        raise SchemaError("field 'touched_paths' must be a relative Git path")
    opaque_runs = [match.group(0) for match in PATH_OPAQUE_RUN_RE.finditer(value)]
    split_runs = [run for run in opaque_runs if len(run) >= 16]
    if any(len(run) >= 48 for run in opaque_runs) or (
        len(split_runs) >= 2 and sum(map(len, split_runs)) >= 48
    ):
        raise SchemaError("field 'touched_paths' rejected by long-opaque-token rule")


@dataclass(frozen=True, slots=True)
class ContextLink:
    """One body-free typed locator join. ``locator_id`` is always derived."""

    kind: LinkKind
    canonical_namespace: str
    canonical_id: str
    canonical_digest: str
    entire_checkpoint_id: str | None = None
    git_sha: str | None = None
    facets: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not isinstance(self.kind, LinkKind):
            raise SchemaError("kind must be an allowlisted LinkKind")
        if not NAMESPACE_RE.fullmatch(self.canonical_namespace):
            raise SchemaError("canonical_namespace must be a typed '<system>:<owner/path>' identity")
        _validate_scalar("canonical_namespace", self.canonical_namespace, reject_long_opaque=True)
        if not CANONICAL_ID_RE.fullmatch(self.canonical_id):
            raise SchemaError("canonical_id must be an exact, path-safe identity")
        canonical_id_exemption = None
        if self.kind is LinkKind.ROLLOVER:
            if self.canonical_namespace != ROLLOVER_NAMESPACE:
                raise SchemaError(f"rollover links must use canonical namespace {ROLLOVER_NAMESPACE!r}")
            if not ROLLOVER_CANONICAL_ID_RE.fullmatch(self.canonical_id):
                raise SchemaError("rollover canonical_id must be an exact registry identity")
            canonical_id_exemption = ROLLOVER_CANONICAL_ID_RE
        _validate_scalar(
            "canonical_id",
            self.canonical_id,
            reject_long_opaque=True,
            long_opaque_exemption=canonical_id_exemption,
        )
        if not SHA256_DIGEST_RE.fullmatch(self.canonical_digest):
            raise SchemaError("canonical_digest must be 'sha256:<64 hex>'")
        if self.entire_checkpoint_id is not None:
            if not isinstance(self.entire_checkpoint_id, str) or not OPAQUE_ID_RE.fullmatch(
                self.entire_checkpoint_id
            ):
                raise SchemaError("entire_checkpoint_id must be an opaque path-safe identifier")
            _validate_scalar("entire_checkpoint_id", self.entire_checkpoint_id, reject_long_opaque=True)
        if self.git_sha is not None and (
            not isinstance(self.git_sha, str) or not GIT_SHA_RE.fullmatch(self.git_sha)
        ):
            raise SchemaError("git_sha must be a full 40-hex commit SHA")
        validate_facets(self.facets)

    @property
    def locator_id(self) -> str:
        """Deterministic ID over kind, namespace, canonical ID, and digest."""
        payload = {
            "schema": "clink.v1",
            "kind": self.kind.value,
            "canonical_namespace": self.canonical_namespace,
            "canonical_id": self.canonical_id,
            "canonical_digest": self.canonical_digest,
        }
        return "clink_" + sha256_text(canonical_json(payload))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "locator_id": self.locator_id,
            "kind": self.kind.value,
            "canonical_namespace": self.canonical_namespace,
            "canonical_id": self.canonical_id,
            "canonical_digest": self.canonical_digest,
            "entire_checkpoint_id": self.entire_checkpoint_id,
            "git_sha": self.git_sha,
            "facets": dict(self.facets),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ContextLink:
        """Strictly parse a caller payload; reject unknown/forbidden fields."""
        if not isinstance(payload, dict):
            raise SchemaError("context link must be a JSON object")
        for key in payload:
            _reject_forbidden_key(key)
            if key not in ALLOWED_TOP_LEVEL_KEYS:
                raise SchemaError(f"unknown field: {key!r}")
        version = payload.get("schema_version", SCHEMA_VERSION)
        if version != SCHEMA_VERSION:
            raise SchemaError(f"unsupported schema_version: {version!r}")
        facets = payload.get("facets") or {}
        validate_facets(facets)
        try:
            kind = LinkKind(payload["kind"])
        except (KeyError, ValueError) as exc:
            raise SchemaError("kind must be an allowlisted LinkKind") from exc
        missing = [
            key
            for key in ("canonical_namespace", "canonical_id", "canonical_digest")
            if not isinstance(payload.get(key), str)
        ]
        if missing:
            raise SchemaError(f"missing required field(s): {', '.join(sorted(missing))}")
        link = cls(
            kind=kind,
            canonical_namespace=payload["canonical_namespace"],
            canonical_id=payload["canonical_id"],
            canonical_digest=payload["canonical_digest"],
            entire_checkpoint_id=payload.get("entire_checkpoint_id"),
            git_sha=payload.get("git_sha"),
            facets=dict(facets),
        )
        link.validate()
        declared = payload.get("locator_id")
        if declared is not None and declared != link.locator_id:
            raise SchemaError("locator_id does not match the derived deterministic ID")
        if "ingested_at" in payload:
            raise SchemaError("ingested_at is projection-assigned and must not be supplied")
        return link


@dataclass(frozen=True, slots=True)
class VerificationEvidence:
    """Caller-provided canonical verification result required for admission.

    The context layer never resolves canonical evidence itself; the caller
    records what its canonical verifier observed. Anything missing, stale,
    partial-terminal, or digest-mismatched is refused/tombstoned by the store.
    """

    verifier: str
    canonical_digest: str
    status: VerificationStatus
    evidence_locator: str
    checked_at: str

    def validate(self) -> None:
        validate_identity(self.verifier, field_name="verifier")
        if not isinstance(self.status, VerificationStatus):
            raise SchemaError("status must be an allowlisted VerificationStatus")
        if not SHA256_DIGEST_RE.fullmatch(self.canonical_digest):
            raise SchemaError("canonical_digest must be 'sha256:<64 hex>'")
        evidence_locator_exemption = GIT_EVIDENCE_LOCATOR_RE
        if self.verifier == "rollover-registry":
            if not ROLLOVER_EVIDENCE_LOCATOR_RE.fullmatch(self.evidence_locator):
                raise SchemaError("rollover-registry evidence_locator must identify one exact registry record")
            evidence_locator_exemption = ROLLOVER_EVIDENCE_LOCATOR_RE
        elif self.evidence_locator.startswith(f"{ROLLOVER_NAMESPACE}/"):
            raise SchemaError("rollover evidence locators require the rollover-registry verifier")
        validate_identity(
            self.evidence_locator,
            field_name="evidence_locator",
            long_opaque_exemption=evidence_locator_exemption,
        )
        try:
            parse_timestamp(self.checked_at)
        except (ValueError, TypeError) as exc:
            raise SchemaError("checked_at must be an ISO-8601 timezone-aware timestamp") from exc

    def to_dict(self) -> dict[str, Any]:
        return {
            "verifier": self.verifier,
            "canonical_digest": self.canonical_digest,
            "status": self.status.value,
            "evidence_locator": self.evidence_locator,
            "checked_at": self.checked_at,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> VerificationEvidence:
        if not isinstance(payload, dict):
            raise SchemaError("verification evidence must be a JSON object")
        allowed = {"verifier", "canonical_digest", "status", "evidence_locator", "checked_at"}
        for key in payload:
            _reject_forbidden_key(key)
            if key not in allowed:
                raise SchemaError(f"unknown verification field: {key!r}")
        try:
            status = VerificationStatus(payload["status"])
        except (KeyError, ValueError) as exc:
            raise SchemaError("status must be an allowlisted VerificationStatus") from exc
        missing = [key for key in allowed - {"status"} if not isinstance(payload.get(key), str)]
        if missing:
            raise SchemaError(f"missing verification field(s): {', '.join(sorted(missing))}")
        evidence = cls(
            verifier=payload["verifier"],
            canonical_digest=payload["canonical_digest"],
            status=status,
            evidence_locator=payload["evidence_locator"],
            checked_at=payload["checked_at"],
        )
        evidence.validate()
        return evidence
