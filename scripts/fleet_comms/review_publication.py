"""PR-G prep: pure helpers for formal-review verdict publication (GitHub gate).

Sol fleet-comms architecture (#5512, sol-fleet-comms-full-arch-r2) assigns PR-G
to the verdict publisher: stale-head protection, idempotent comment + commit
status publication, and auto-merge-compatible context
``fleet/cross-family-review``.

This module is intentionally pure and dry-run-first:

* parse sealed verdict payloads (APPROVED / CHANGES_REQUESTED / BLOCKED)
* compare expected head SHA against the current PR head (fail closed on drift)
* derive a stable idempotency key from ``(repository, pr, head_sha, gate_kind)``
* plan publication (comment body + status state) without calling GitHub

Live GitHub mutation is **not** performed here. The existing bridge command
``publish-review-verdict`` remains the temporary poster; full
``publish-review-verdict --review-id`` cutover waits for PR-F formal-jobs table
writers and must not become the default until those land.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

VALID_VERDICTS = frozenset({"APPROVED", "CHANGES_REQUESTED", "BLOCKED"})
DEFAULT_GATE_KIND = "cross-family-review"
DEFAULT_STATUS_CONTEXT = "fleet/cross-family-review"
# GitHub commit status states used for the merge gate.
STATUS_SUCCESS = "success"
STATUS_FAILURE = "failure"
STATUS_ERROR = "error"
STATUS_PENDING = "pending"

_SHA_RE = re.compile(r"^[0-9a-f]{7,64}$", re.IGNORECASE)
_VERDICT_LINE_RE = re.compile(
    r"\bVERDICT\s*:\s*(APPROVED|CHANGES_REQUESTED|BLOCKED)\b",
    re.IGNORECASE,
)

PublicationAction = Literal["publish", "skip_idempotent", "refuse_stale"]
CommitStatusState = Literal["success", "failure", "error", "pending"]


class ReviewPublicationError(ValueError):
    """Sealed payload or publication plan failed closed."""


@dataclass(frozen=True, slots=True)
class SealedVerdict:
    """Minimal sealed formal-review verdict needed to plan a GitHub gate post.

    Provenance fields (model/family/harness) are required so the thin PR comment
    never invents CLI-supplied identity after PR-G cutover. PR-F owns job
    storage; this structure is the in-memory view the publisher consumes.
    """

    review_id: str
    repository: str
    pr_number: int
    head_sha: str
    gate_kind: str
    verdict: str
    model: str
    family: str
    harness: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "review_id": self.review_id,
            "repository": self.repository,
            "pr_number": self.pr_number,
            "head_sha": self.head_sha,
            "gate_kind": self.gate_kind,
            "verdict": self.verdict,
            "model": self.model,
            "family": self.family,
            "harness": self.harness,
        }


@dataclass(frozen=True, slots=True)
class HeadFreshness:
    """Result of comparing the sealed job head to the live PR head."""

    expected_sha: str
    current_sha: str
    is_fresh: bool

    @property
    def is_stale(self) -> bool:
        return not self.is_fresh


@dataclass(frozen=True, slots=True)
class PublicationPlan:
    """Dry-run-first publication decision; never posts to GitHub by itself."""

    action: PublicationAction
    idempotency_key: str
    review_id: str
    repository: str
    pr_number: int
    head_sha: str
    gate_kind: str
    verdict: str
    status_context: str
    status_state: CommitStatusState | None
    comment_body: str | None
    mutate: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "idempotency_key": self.idempotency_key,
            "review_id": self.review_id,
            "repository": self.repository,
            "pr_number": self.pr_number,
            "head_sha": self.head_sha,
            "gate_kind": self.gate_kind,
            "verdict": self.verdict,
            "status_context": self.status_context,
            "status_state": self.status_state,
            "comment_body": self.comment_body,
            "mutate": self.mutate,
            "reason": self.reason,
        }


def _require_nonempty_str(value: Any, *, field: str) -> str:
    if not isinstance(value, str):
        raise ReviewPublicationError(f"missing_{field}: expected non-empty string")
    normalized = " ".join(value.split())
    if not normalized:
        raise ReviewPublicationError(f"missing_{field}: expected non-empty string")
    return normalized


def _normalize_sha(value: Any, *, field: str = "head_sha") -> str:
    sha = _require_nonempty_str(value, field=field).lower()
    if not _SHA_RE.fullmatch(sha):
        raise ReviewPublicationError(f"invalid_{field}: {sha!r}")
    return sha


def _normalize_pr_number(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ReviewPublicationError(f"invalid_pr_number: {value!r}")
    if value <= 0:
        raise ReviewPublicationError(f"invalid_pr_number: {value}")
    return value


def normalize_verdict(raw: Any) -> str:
    """Return a canonical APPROVED|CHANGES_REQUESTED|BLOCKED verdict."""
    if not isinstance(raw, str):
        raise ReviewPublicationError(
            "invalid_verdict: expected APPROVED|CHANGES_REQUESTED|BLOCKED"
        )
    verdict = raw.strip().upper()
    if verdict not in VALID_VERDICTS:
        raise ReviewPublicationError(
            f"invalid_verdict: {raw!r} "
            "(expected APPROVED|CHANGES_REQUESTED|BLOCKED)"
        )
    return verdict


def parse_verdict_token(text: str) -> str:
    """Extract a VERDICT line from free text without retaining the body."""
    if not isinstance(text, str) or not text.strip():
        raise ReviewPublicationError("verdict_missing: empty payload")
    match = _VERDICT_LINE_RE.search(text)
    if not match:
        raise ReviewPublicationError(
            "verdict_missing: expected VERDICT: APPROVED|CHANGES_REQUESTED|BLOCKED"
        )
    return normalize_verdict(match.group(1))


def parse_sealed_verdict_payload(payload: Mapping[str, Any] | str | bytes) -> SealedVerdict:
    """Parse a sealed formal-review verdict payload (dict or JSON object).

    Accepts either:

    * a mapping / JSON object with explicit fields, or
    * JSON text that decodes to that object.

    The ``verdict`` field is required. A free-text ``verdict_text`` with a
    ``VERDICT:`` line is accepted only when ``verdict`` is absent (bridge
    compatibility while PR-F jobs land).
    """
    data: Mapping[str, Any]
    if isinstance(payload, (str, bytes)):
        raw = payload.decode("utf-8") if isinstance(payload, bytes) else payload
        try:
            loaded = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ReviewPublicationError(f"sealed_payload_invalid_json: {exc.msg}") from exc
        if not isinstance(loaded, dict):
            raise ReviewPublicationError("sealed_payload_invalid: expected a JSON object")
        data = loaded
    elif isinstance(payload, Mapping):
        data = payload
    else:
        raise ReviewPublicationError(
            f"sealed_payload_invalid: unsupported type {type(payload).__name__}"
        )

    if "verdict" in data and data["verdict"] is not None:
        verdict = normalize_verdict(data["verdict"])
    elif data.get("verdict_text"):
        verdict = parse_verdict_token(str(data["verdict_text"]))
    else:
        raise ReviewPublicationError(
            "sealed_payload_missing_verdict: expected verdict field"
        )

    gate_kind = (
        _require_nonempty_str(data["gate_kind"], field="gate_kind")
        if data.get("gate_kind") is not None
        else DEFAULT_GATE_KIND
    )

    return SealedVerdict(
        review_id=_require_nonempty_str(data.get("review_id"), field="review_id"),
        repository=_require_nonempty_str(data.get("repository"), field="repository"),
        pr_number=_normalize_pr_number(data.get("pr_number", data.get("pr"))),
        head_sha=_normalize_sha(data.get("head_sha"), field="head_sha"),
        gate_kind=gate_kind,
        verdict=verdict,
        model=_require_nonempty_str(data.get("model"), field="model"),
        family=_require_nonempty_str(data.get("family"), field="family"),
        harness=_require_nonempty_str(data.get("harness"), field="harness"),
    )


def check_head_freshness(*, expected_sha: str, current_sha: str) -> HeadFreshness:
    """Compare sealed job head against live PR head (case-insensitive full match).

    Publisher head drift must fail closed without posting success (Sol PR-G).
    Short prefixes are not accepted — both sides must be normalized SHAs.
    """
    expected = _normalize_sha(expected_sha, field="expected_sha")
    current = _normalize_sha(current_sha, field="current_sha")
    return HeadFreshness(
        expected_sha=expected,
        current_sha=current,
        is_fresh=expected == current,
    )


def assert_head_fresh(*, expected_sha: str, current_sha: str) -> HeadFreshness:
    """Like :func:`check_head_freshness` but raises on stale head."""
    result = check_head_freshness(expected_sha=expected_sha, current_sha=current_sha)
    if result.is_stale:
        raise ReviewPublicationError(
            f"stale_head: expected={result.expected_sha} current={result.current_sha}"
        )
    return result


def publication_idempotency_key(
    *,
    repository: str,
    pr_number: int,
    head_sha: str,
    gate_kind: str = DEFAULT_GATE_KIND,
) -> str:
    """Stable key for unique formal-review jobs / publication receipts.

    Matches the formal_review_jobs uniqueness constraint::

        UNIQUE (repository, pr_number, head_sha, gate_kind)

    The digest is hex SHA-256 over a canonical encoding so callers can store a
    compact key without delimiter ambiguity.
    """
    repo = _require_nonempty_str(repository, field="repository").lower()
    pr = _normalize_pr_number(pr_number)
    sha = _normalize_sha(head_sha, field="head_sha")
    gate = _require_nonempty_str(gate_kind, field="gate_kind").lower()
    canonical = f"{repo}\n{pr}\n{sha}\n{gate}".encode()
    digest = hashlib.sha256(canonical).hexdigest()
    return f"fleet-pub:{digest}"


def map_verdict_to_commit_status(verdict: str) -> CommitStatusState:
    """Map sealed verdict → GitHub commit status state for the merge gate.

    Sol formal-review service::

        APPROVED            → success
        CHANGES_REQUESTED   → failure
        BLOCKED             → error  (terminal infrastructure / policy block)
    """
    normalized = normalize_verdict(verdict)
    if normalized == "APPROVED":
        return STATUS_SUCCESS
    if normalized == "CHANGES_REQUESTED":
        return STATUS_FAILURE
    return STATUS_ERROR


def build_thin_verdict_comment(sealed: SealedVerdict) -> str:
    """Build the thin PR comment body (no findings, provenance from sealed job)."""
    return "\n".join(
        (
            f"VERDICT: {sealed.verdict}",
            f"Head SHA: {sealed.head_sha}",
            f"Review ID: {sealed.review_id}",
            "Reviewer provenance: "
            f"model={sealed.model}; "
            f"family={sealed.family}; "
            f"harness={sealed.harness}",
        )
    )


def plan_publication(
    sealed: SealedVerdict,
    *,
    current_head_sha: str,
    already_published_key: str | None = None,
    mutate: bool = False,
    status_context: str = DEFAULT_STATUS_CONTEXT,
) -> PublicationPlan:
    """Plan comment + commit-status publication for a sealed verdict.

    Default path is dry-run (``mutate=False``): the plan describes what would be
    posted but performs no GitHub I/O. Callers that intend live mutation must
    pass ``mutate=True`` **and** implement the actual ``gh``/API calls outside
    this module — this function still never talks to GitHub.

    Idempotency: if ``already_published_key`` equals the planned key, action is
    ``skip_idempotent`` (exactly one effective status/comment per job).
    """
    if not isinstance(sealed, SealedVerdict):
        raise ReviewPublicationError("sealed_verdict_invalid: expected SealedVerdict")

    context = _require_nonempty_str(status_context, field="status_context")
    key = publication_idempotency_key(
        repository=sealed.repository,
        pr_number=sealed.pr_number,
        head_sha=sealed.head_sha,
        gate_kind=sealed.gate_kind,
    )

    freshness = check_head_freshness(
        expected_sha=sealed.head_sha,
        current_sha=current_head_sha,
    )
    if freshness.is_stale:
        return PublicationPlan(
            action="refuse_stale",
            idempotency_key=key,
            review_id=sealed.review_id,
            repository=sealed.repository,
            pr_number=sealed.pr_number,
            head_sha=sealed.head_sha,
            gate_kind=sealed.gate_kind,
            verdict=sealed.verdict,
            status_context=context,
            status_state=None,
            comment_body=None,
            mutate=False,
            reason=(
                f"stale_head: expected={freshness.expected_sha} "
                f"current={freshness.current_sha}"
            ),
        )

    if already_published_key is not None and already_published_key == key:
        return PublicationPlan(
            action="skip_idempotent",
            idempotency_key=key,
            review_id=sealed.review_id,
            repository=sealed.repository,
            pr_number=sealed.pr_number,
            head_sha=sealed.head_sha,
            gate_kind=sealed.gate_kind,
            verdict=sealed.verdict,
            status_context=context,
            status_state=None,
            comment_body=None,
            mutate=False,
            reason="already_published: matching idempotency key",
        )

    return PublicationPlan(
        action="publish",
        idempotency_key=key,
        review_id=sealed.review_id,
        repository=sealed.repository,
        pr_number=sealed.pr_number,
        head_sha=sealed.head_sha,
        gate_kind=sealed.gate_kind,
        verdict=sealed.verdict,
        status_context=context,
        status_state=map_verdict_to_commit_status(sealed.verdict),
        comment_body=build_thin_verdict_comment(sealed),
        mutate=bool(mutate),
        reason=(
            "ready_to_publish"
            if mutate
            else "dry_run: no GitHub mutation (pass mutate=True only from an explicit live publisher)"
        ),
    )


__all__ = [
    "DEFAULT_GATE_KIND",
    "DEFAULT_STATUS_CONTEXT",
    "STATUS_ERROR",
    "STATUS_FAILURE",
    "STATUS_PENDING",
    "STATUS_SUCCESS",
    "VALID_VERDICTS",
    "CommitStatusState",
    "HeadFreshness",
    "PublicationAction",
    "PublicationPlan",
    "ReviewPublicationError",
    "SealedVerdict",
    "assert_head_fresh",
    "build_thin_verdict_comment",
    "check_head_freshness",
    "map_verdict_to_commit_status",
    "normalize_verdict",
    "parse_sealed_verdict_payload",
    "parse_verdict_token",
    "plan_publication",
    "publication_idempotency_key",
]
