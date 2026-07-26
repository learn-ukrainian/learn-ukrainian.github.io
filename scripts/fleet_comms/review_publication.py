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
REVIEW_SCHEMA_VERSION = "code-review-findings.v1"
# GitHub accepts 65,536 characters per comment. Reserve room for markup and
# the explicit truncation notice rather than relying on a remote rejection.
GITHUB_COMMENT_CHAR_LIMIT = 64_000
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
class ReviewFinding:
    """Immutable projection of one validated canonical review finding."""

    finding_id: str
    title: str
    body: str
    priority: str
    confidence: float
    category: str
    path: str
    start_line: int
    end_line: int
    claim_type: str
    verbatim: str
    why_wrong: str
    smallest_fix: str
    sources: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.finding_id,
            "title": self.title,
            "body": self.body,
            "priority": self.priority,
            "confidence": self.confidence,
            "category": self.category,
            "location": {
                "path": self.path,
                "start_line": self.start_line,
                "end_line": self.end_line,
                "claim_type": self.claim_type,
            },
            "verbatim": self.verbatim,
            "why_wrong": self.why_wrong,
            "smallest_fix": self.smallest_fix,
            "sources": list(self.sources),
        }


@dataclass(frozen=True, slots=True)
class ReviewEvidence:
    """Validated review evidence retained with the formal verdict."""

    correctness: str
    explanation: str
    confidence: float
    findings: tuple[ReviewFinding, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": REVIEW_SCHEMA_VERSION,
            "overall": {
                "correctness": self.correctness,
                "explanation": self.explanation,
                "confidence": self.confidence,
            },
            "findings": [finding.to_dict() for finding in self.findings],
        }


@dataclass(frozen=True, slots=True)
class SealedVerdict:
    """Sealed formal-review verdict needed to plan a GitHub gate post.

    Provenance fields (model/family/harness) are required so the PR comment
    never invents CLI-supplied identity after PR-G cutover. ``review_evidence``
    is the immutable canonical projection that makes the public verdict
    auditable; an absent projection is rendered as an explicit warning.
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
    review_evidence: ReviewEvidence | None = None

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
            "review_evidence": (
                self.review_evidence.to_dict() if self.review_evidence is not None else None
            ),
        }


def _validate_reviewer_model(model: str) -> str:
    """Require an exact catalog model id or declared alias for gate provenance."""
    normalized = _require_nonempty_str(model, field="model")
    try:
        from scripts.review.model_catalog import ModelCatalogError, load_model_catalog

        catalog = load_model_catalog()
    except ModelCatalogError as exc:
        raise ReviewPublicationError(f"reviewer_model_catalog_invalid: {exc}") from exc

    models = catalog["models"]
    known_models = set(models)
    known_models.update(
        alias
        for entry in models.values()
        for alias in entry.get("aliases", [])
    )
    if normalized not in known_models:
        raise ReviewPublicationError(f"unknown_reviewer_model: {normalized!r}")
    return normalized


def validate_review_gate_input(
    *,
    verdict: str,
    model: str,
    review_evidence: ReviewEvidence | None,
) -> str:
    """Validate the evidence and provenance needed to grant a review gate.

    A BLOCKED verdict is intentionally allowed without evidence: it is the
    conservative fast path. Every APPROVED verdict, however it arrived, must
    retain canonical evidence so a successful merge gate is auditable.
    """
    normalized_verdict = normalize_verdict(verdict)
    _validate_reviewer_model(model)
    if normalized_verdict == "APPROVED" and (
        review_evidence is None
        or not isinstance(review_evidence, ReviewEvidence)
        or not review_evidence.explanation.strip()
    ):
        raise ReviewPublicationError(
            "approved_review_evidence_required: "
            "verdict=APPROVED review_evidence=missing"
        )
    return normalized_verdict


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


def _canonical_evidence_fields(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Extract the canonical reviewer payload from a wrapper mapping."""
    return {
        field: payload[field]
        for field in ("schema_version", "overall", "findings")
        if field in payload
    }


def _has_canonical_review_evidence(payload: Mapping[str, Any]) -> bool:
    return "schema_version" in payload or "overall" in payload


def _is_degenerate_review_evidence(payload: Mapping[str, Any]) -> bool:
    """Recognize a reviewer that supplied neither explanation nor findings.

    The canonical schema deliberately rejects an empty explanation. Publication
    nevertheless needs to surface this exact reviewer failure rather than turn
    it into a clean-looking verdict or discard it with a generic schema error.
    """
    if payload.get("schema_version") != REVIEW_SCHEMA_VERSION:
        return False
    findings = payload.get("findings")
    overall = payload.get("overall")
    if findings != [] or not isinstance(overall, Mapping):
        return False
    explanation = overall.get("explanation")
    return not isinstance(explanation, str) or not explanation.strip()


def parse_review_evidence(payload: Mapping[str, Any]) -> ReviewEvidence | None:
    """Validate and freeze canonical reviewer evidence for public rendering.

    ``None`` is reserved for the explicit no-evidence case: an empty explanation
    and no findings. All other malformed evidence fails closed before it can
    produce a misleading GitHub gate comment.
    """
    canonical = _canonical_evidence_fields(payload)
    if _is_degenerate_review_evidence(canonical):
        return None

    try:
        from scripts.review.review_contract import ContractError, validate_reviewer_payload

        validated = validate_reviewer_payload(canonical)
    except ContractError as exc:
        raise ReviewPublicationError(f"review_evidence_invalid: {exc}") from exc

    overall = validated["overall"]
    findings = tuple(
        ReviewFinding(
            finding_id=finding["id"],
            title=finding["title"],
            body=finding["body"],
            priority=finding["priority"],
            confidence=float(finding["confidence"]),
            category=finding["category"],
            path=finding["location"]["path"],
            start_line=int(finding["location"]["start_line"]),
            end_line=int(finding["location"]["end_line"]),
            claim_type=finding["location"]["claim_type"],
            verbatim=finding["verbatim"],
            why_wrong=finding["why_wrong"],
            smallest_fix=finding["smallest_fix"],
            sources=tuple(finding["sources"]),
        )
        for finding in validated["findings"]
    )
    return ReviewEvidence(
        correctness=overall["correctness"],
        explanation=overall["explanation"],
        confidence=float(overall["confidence"]),
        findings=findings,
    )


def verdict_from_review_evidence(evidence: ReviewEvidence) -> str:
    """Derive the only gate verdict consistent with canonical review evidence."""
    if evidence.findings or evidence.correctness == "incorrect":
        return "CHANGES_REQUESTED"
    if evidence.correctness == "correct":
        return "APPROVED"
    return "BLOCKED"


def _verdict_from_degenerate_evidence(_payload: Mapping[str, Any]) -> str:
    """Fail closed when a canonical review supplies no auditable evidence.

    A reviewer-provided correctness label without an explanation or finding is
    not evidence. It must never grant a green formal-review gate.
    """
    return "BLOCKED"


def resolve_verdict_and_evidence(payload: Mapping[str, Any]) -> tuple[str, ReviewEvidence | None]:
    """Resolve a verdict and retain any canonical evidence from one payload.

    Legacy payloads may still carry only a top-level ``verdict``. Canonical
    ``code-review-findings.v1`` payloads derive the verdict from their verified
    meaning; an explicit conflicting token fails closed.
    """
    raw_verdict = payload.get("verdict")
    explicit = normalize_verdict(raw_verdict) if raw_verdict is not None else None
    if not _has_canonical_review_evidence(payload):
        if explicit is None:
            raise ReviewPublicationError(
                "findings_json_missing_verdict: expected verdict or canonical review evidence"
            )
        return explicit, None

    evidence = parse_review_evidence(payload)
    derived = (
        verdict_from_review_evidence(evidence)
        if evidence is not None
        else _verdict_from_degenerate_evidence(payload)
    )
    if explicit is not None and explicit != derived:
        raise ReviewPublicationError(
            f"review_evidence_verdict_mismatch: verdict={explicit} evidence={derived}"
        )
    return derived, evidence


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

    A canonical ``review_evidence`` payload derives the verdict. A free-text
    ``verdict_text`` with a ``VERDICT:`` line is accepted only when canonical
    evidence is absent (legacy bridge compatibility).
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

    review_payload: Mapping[str, Any] | None = None
    raw_evidence = data.get("review_evidence")
    if raw_evidence is not None:
        if not isinstance(raw_evidence, Mapping):
            raise ReviewPublicationError("review_evidence_invalid: expected an object")
        review_payload = dict(raw_evidence)
        if "verdict" in data and "verdict" not in review_payload:
            review_payload = {**review_payload, "verdict": data["verdict"]}
    elif _has_canonical_review_evidence(data):
        review_payload = _canonical_evidence_fields(data)
        if "verdict" in data:
            review_payload["verdict"] = data["verdict"]

    review_evidence: ReviewEvidence | None = None
    if review_payload is not None:
        verdict, review_evidence = resolve_verdict_and_evidence(review_payload)
    elif "verdict" in data and data["verdict"] is not None:
        verdict = normalize_verdict(data["verdict"])
    elif data.get("verdict_text"):
        verdict = parse_verdict_token(str(data["verdict_text"]))
    else:
        raise ReviewPublicationError(
            "sealed_payload_missing_verdict: expected verdict field or review evidence"
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
        review_evidence=review_evidence,
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


def _format_location(finding: ReviewFinding) -> str:
    if finding.start_line == finding.end_line:
        return f"{finding.path}:{finding.start_line}"
    return f"{finding.path}:{finding.start_line}-{finding.end_line}"


def _render_finding(finding: ReviewFinding) -> str:
    sources = ", ".join(finding.sources)
    return "\n".join(
        (
            f"### {finding.finding_id} — Severity: {finding.priority}",
            f"**Location:** `{_format_location(finding)}` ({finding.claim_type})",
            f"**Title:** {finding.title}",
            f"**Category:** {finding.category} · **Confidence:** {finding.confidence:g}",
            "",
            f"**Description:** {finding.body}",
            "",
            f"**Why it is wrong:** {finding.why_wrong}",
            "",
            f"**Smallest fix:** {finding.smallest_fix}",
            "",
            f"**Sources:** {sources}",
        )
    )


def _render_evidence(
    *,
    prefix: str,
    evidence: ReviewEvidence | None,
    record_reference: str,
) -> str:
    if evidence is None:
        return "\n\n".join(
            (
                prefix,
                "## Review evidence\n"
                "> **NO EVIDENCE SUPPLIED.** The reviewer supplied no overall explanation "
                "and no findings. This verdict is not independently auditable.",
            )
        )

    overall = "\n".join(
        (
            "## Overall review",
            f"**Correctness:** `{evidence.correctness}` · **Confidence:** {evidence.confidence:g}",
            "",
            evidence.explanation,
        )
    )
    findings = [_render_finding(finding) for finding in evidence.findings]
    complete = "\n\n".join((prefix, overall, "## Findings", "\n\n".join(findings)))
    if len(complete) <= GITHUB_COMMENT_CHAR_LIMIT:
        return complete

    findings_header = "## Findings"
    truncation = (
        "> **FINDINGS TRUNCATED.** Published {published} of {total} findings to stay within "
        "GitHub's comment limit. Full structured review record: {record_reference}."
    )
    baseline = "\n\n".join((prefix, overall, findings_header))
    minimum_notice = truncation.format(
        published=0,
        total=len(findings),
        record_reference=record_reference,
    )
    if len("\n\n".join((baseline, minimum_notice))) > GITHUB_COMMENT_CHAR_LIMIT:
        raise ReviewPublicationError(
            "review_evidence_overall_exceeds_comment_limit: cannot truncate overall explanation"
        )

    published: list[str] = []
    for finding in findings:
        candidate = [*published, finding]
        notice = truncation.format(
            published=len(candidate),
            total=len(findings),
            record_reference=record_reference,
        )
        if len("\n\n".join((baseline, *candidate, notice))) > GITHUB_COMMENT_CHAR_LIMIT:
            break
        published.append(finding)

    notice = truncation.format(
        published=len(published),
        total=len(findings),
        record_reference=record_reference,
    )
    return "\n\n".join((baseline, *published, notice))


def build_review_comment(
    *,
    verdict: str,
    head_sha: str,
    model: str,
    family: str,
    harness: str,
    review_evidence: ReviewEvidence | None = None,
    review_id: str | None = None,
) -> str:
    """Render one auditable formal-review comment for a GitHub PR."""
    verdict = validate_review_gate_input(
        verdict=verdict,
        model=model,
        review_evidence=review_evidence,
    )
    lines = [
        f"VERDICT: {verdict}",
        f"Head SHA: {head_sha}",
    ]
    if review_id is not None:
        lines.append(f"Review ID: {review_id}")
    lines.append(
        "Reviewer provenance: "
        f"model={model}; family={family}; harness={harness}"
    )
    record_reference = (
        f"review ID `{review_id}` (sealed formal-job artifact)"
        if review_id is not None
        else "the supplied `--findings-json` input (legacy publication path)"
    )
    return _render_evidence(
        prefix="\n".join(lines),
        evidence=review_evidence,
        record_reference=record_reference,
    )


def build_verdict_comment(sealed: SealedVerdict) -> str:
    """Render one auditable GitHub comment from a sealed formal review."""
    return build_review_comment(
        verdict=sealed.verdict,
        head_sha=sealed.head_sha,
        review_id=sealed.review_id,
        model=sealed.model,
        family=sealed.family,
        harness=sealed.harness,
        review_evidence=sealed.review_evidence,
    )


# Kept as a compatibility alias while external callers move to the honest name.
build_thin_verdict_comment = build_verdict_comment


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

    validate_review_gate_input(
        verdict=sealed.verdict,
        model=sealed.model,
        review_evidence=sealed.review_evidence,
    )

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
        comment_body=build_verdict_comment(sealed),
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
    "GITHUB_COMMENT_CHAR_LIMIT",
    "REVIEW_SCHEMA_VERSION",
    "STATUS_ERROR",
    "STATUS_FAILURE",
    "STATUS_PENDING",
    "STATUS_SUCCESS",
    "VALID_VERDICTS",
    "CommitStatusState",
    "HeadFreshness",
    "PublicationAction",
    "PublicationPlan",
    "ReviewEvidence",
    "ReviewFinding",
    "ReviewPublicationError",
    "SealedVerdict",
    "assert_head_fresh",
    "build_review_comment",
    "build_thin_verdict_comment",
    "build_verdict_comment",
    "check_head_freshness",
    "map_verdict_to_commit_status",
    "normalize_verdict",
    "parse_review_evidence",
    "parse_sealed_verdict_payload",
    "parse_verdict_token",
    "plan_publication",
    "publication_idempotency_key",
    "resolve_verdict_and_evidence",
    "validate_review_gate_input",
    "verdict_from_review_evidence",
]
