"""PR-F/G glue: create formal job + accept sealed verdict (+ optional publish).

Closes the gap between ``review-pr`` (ask-only) and Sol milestone 2:

1. Resolve immutable PR head via ``gh``
2. Create (or reuse) formal job for ``(repo, pr, head, gate)``
3. ``accept_sealed_verdict`` with full provenance in the sealed payload
4. Optionally ``publish_sealed_verdict`` (``--review-id`` path)

Does **not** invoke reviewers, create sealed worktrees, or cut over ``review-pr``
defaults. Operators/orchestrators call this after a review reply is in hand.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.fleet_comms.formal_review_jobs import (
    FormalReviewJobsError,
    FormalReviewJobService,
)
from scripts.fleet_comms.review_ground_truth import (
    ReviewGroundTruthError,
    fetch_pr_change_inventory,
    validate_findings_against_inventory,
)
from scripts.fleet_comms.review_publication import (
    DEFAULT_GATE_KIND,
    ReviewEvidence,
    ReviewPublicationError,
    SealedVerdict,
    normalize_verdict,
    parse_sealed_verdict_payload,
    parse_verdict_token,
    resolve_verdict_and_evidence,
    validate_review_gate_input,
)
from scripts.fleet_comms.review_publisher import (
    ReviewPublisherError,
    fetch_pr_head_sha,
    publish_sealed_verdict,
    split_repository,
)

Runner = Callable[..., subprocess.CompletedProcess[str]]

DEFAULT_REPOSITORY = "learn-ukrainian/learn-ukrainian.github.io"
_SHA_RE = re.compile(r"^[0-9a-f]{7,64}$", re.IGNORECASE)


class FormalReviewFinalizeError(RuntimeError):
    """Finalize refused an operation (fail closed)."""


@dataclass(frozen=True, slots=True)
class FinalizeResult:
    review_id: str
    repository: str
    pr_number: int
    head_sha: str
    gate_kind: str
    verdict: str
    sealed_verdict_artifact_id: str | None
    published: bool
    publication_summary: str | None
    job_created: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "review_id": self.review_id,
            "repository": self.repository,
            "pr_number": self.pr_number,
            "head_sha": self.head_sha,
            "gate_kind": self.gate_kind,
            "verdict": self.verdict,
            "sealed_verdict_artifact_id": self.sealed_verdict_artifact_id,
            "published": self.published,
            "publication_summary": self.publication_summary,
            "job_created": self.job_created,
        }


def resolve_verdict_token(
    *,
    verdict: str | None = None,
    verdict_text: str | None = None,
    findings_path: Path | None = None,
) -> str:
    """Normalize a verdict from explicit token, free text, or findings JSON."""
    if verdict and str(verdict).strip():
        try:
            return normalize_verdict(verdict)
        except ReviewPublicationError as exc:
            raise FormalReviewFinalizeError(str(exc)) from exc
    if findings_path is not None:
        try:
            payload = json.loads(findings_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise FormalReviewFinalizeError(f"findings_unreadable: {exc}") from exc
        try:
            if not isinstance(payload, dict):
                raise FormalReviewFinalizeError("findings_json_invalid: expected an object")
            return resolve_verdict_and_evidence(payload)[0]
        except ReviewPublicationError as exc:
            raise FormalReviewFinalizeError(str(exc)) from exc
    if verdict_text and str(verdict_text).strip():
        try:
            return parse_verdict_token(verdict_text)
        except ReviewPublicationError as exc:
            raise FormalReviewFinalizeError(str(exc)) from exc
    raise FormalReviewFinalizeError(
        "verdict_required: pass --verdict, --verdict-file, or --findings-json"
    )


def build_sealed_verdict(
    *,
    review_id: str,
    repository: str,
    pr_number: int,
    head_sha: str,
    gate_kind: str,
    verdict: str,
    model: str,
    family: str,
    harness: str,
    review_evidence: ReviewEvidence | None = None,
) -> SealedVerdict:
    """Build a SealedVerdict from explicit fields (provenance never invented)."""
    payload = {
        "review_id": review_id,
        "repository": repository,
        "pr_number": pr_number,
        "head_sha": head_sha,
        "gate_kind": gate_kind,
        "verdict": verdict,
        "model": model,
        "family": family,
        "harness": harness,
        "review_evidence": (
            review_evidence.to_dict() if review_evidence is not None else None
        ),
    }
    try:
        return parse_sealed_verdict_payload(payload)
    except ReviewPublicationError as exc:
        raise FormalReviewFinalizeError(str(exc)) from exc


def finalize_formal_review_verdict(
    *,
    pr_number: int,
    model: str,
    family: str,
    harness: str,
    repository: str = DEFAULT_REPOSITORY,
    gate_kind: str = DEFAULT_GATE_KIND,
    verdict: str | None = None,
    verdict_text: str | None = None,
    findings_path: Path | None = None,
    review_id: str | None = None,
    head_sha: str | None = None,
    publish: bool = False,
    dry_run_publish: bool = False,
    plane_root: Path | None = None,
    runner: Runner = subprocess.run,
) -> FinalizeResult:
    """Create/reuse job, accept sealed verdict, optionally publish to GitHub."""
    if pr_number < 1:
        raise FormalReviewFinalizeError(f"invalid_pr: {pr_number}")
    for label, value in (("model", model), ("family", family), ("harness", harness)):
        if not value or not str(value).strip():
            raise FormalReviewFinalizeError(f"missing_{label}")

    # Validate repository shape early.
    split_repository(repository)

    findings_verdict: str | None = None
    review_evidence: ReviewEvidence | None = None
    if findings_path is not None:
        try:
            findings_payload = json.loads(findings_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise FormalReviewFinalizeError(f"findings_unreadable: {exc}") from exc
        if not isinstance(findings_payload, dict):
            raise FormalReviewFinalizeError("findings_json_invalid: expected an object")
        try:
            findings_verdict, review_evidence = resolve_verdict_and_evidence(findings_payload)
        except ReviewPublicationError as exc:
            raise FormalReviewFinalizeError(str(exc)) from exc

    if verdict and str(verdict).strip():
        try:
            resolved_verdict = normalize_verdict(verdict)
        except ReviewPublicationError as exc:
            raise FormalReviewFinalizeError(str(exc)) from exc
    elif findings_verdict is not None:
        resolved_verdict = findings_verdict
    elif verdict_text and str(verdict_text).strip():
        try:
            resolved_verdict = parse_verdict_token(verdict_text)
        except ReviewPublicationError as exc:
            raise FormalReviewFinalizeError(str(exc)) from exc
    else:
        raise FormalReviewFinalizeError(
            "verdict_required: pass --verdict, --verdict-file, or --findings-json"
        )

    if findings_verdict is not None and resolved_verdict != findings_verdict:
        raise FormalReviewFinalizeError(
            f"review_evidence_verdict_mismatch: verdict={resolved_verdict} "
            f"evidence={findings_verdict}"
        )

    try:
        validate_review_gate_input(
            verdict=resolved_verdict,
            model=model,
            review_evidence=review_evidence,
        )
    except ReviewPublicationError as exc:
        raise FormalReviewFinalizeError(str(exc)) from exc

    sha = head_sha
    if sha is None:
        try:
            sha = fetch_pr_head_sha(
                repository=repository,
                pr_number=pr_number,
                runner=runner,
            )
        except ReviewPublisherError as exc:
            raise FormalReviewFinalizeError(str(exc)) from exc
    sha = sha.strip().lower()
    if not _SHA_RE.match(sha):
        raise FormalReviewFinalizeError(f"invalid_head_sha: {sha!r}")

    # Layer 3 (#5802): refuse findings that cite paths outside GitHub's
    # three-dot PR file surface (two-dot-against-moved-base artifact).
    if review_evidence is not None and review_evidence.findings:
        try:
            inventory = fetch_pr_change_inventory(
                repository=repository,
                pr_number=pr_number,
                runner=runner,
            )
            validate_findings_against_inventory(
                review_evidence,
                inventory,
                expected_head_sha=sha,
            )
        except (ReviewGroundTruthError, ReviewPublicationError) as exc:
            raise FormalReviewFinalizeError(str(exc)) from exc

    job_created = False
    with FormalReviewJobService(root=plane_root) as service:
        try:
            existing = service.find_job(
                repository, pr_number, sha, gate_kind, include_attempts=False
            )
            if existing is None:
                job = service.create_job(
                    repository,
                    pr_number,
                    sha,
                    gate_kind,
                    review_id=review_id,
                    state="running",
                )
                job_created = True
            else:
                job = existing
                if review_id and review_id != job.review_id:
                    raise FormalReviewFinalizeError(
                        f"review_id_mismatch: requested={review_id!r} "
                        f"existing={job.review_id!r}"
                    )

            sealed = build_sealed_verdict(
                review_id=job.review_id,
                repository=repository,
                pr_number=pr_number,
                head_sha=sha,
                gate_kind=gate_kind,
                verdict=resolved_verdict,
                model=model.strip(),
                family=family.strip(),
                harness=harness.strip(),
                review_evidence=review_evidence,
            )
            service.accept_sealed_verdict(job.review_id, sealed)
        except FormalReviewJobsError as exc:
            # Includes concurrent create races and accept failures.
            raise FormalReviewFinalizeError(str(exc)) from exc

        refreshed = service.get_job(job.review_id, include_attempts=False)
        publication_summary: str | None = None
        published = False
        if publish or dry_run_publish:
            try:
                result = publish_sealed_verdict(
                    sealed,
                    mutate=publish and not dry_run_publish,
                    require_receipt=True,
                    store=service.store,
                    runner=runner,
                )
            except ReviewPublisherError as exc:
                raise FormalReviewFinalizeError(str(exc)) from exc
            publication_summary = result.summary
            published = bool(result.status_posted)
            if result.plan.action == "refuse_stale":
                raise FormalReviewFinalizeError(result.plan.reason)

        return FinalizeResult(
            review_id=job.review_id,
            repository=repository,
            pr_number=pr_number,
            head_sha=sha,
            gate_kind=gate_kind,
            verdict=resolved_verdict,
            sealed_verdict_artifact_id=refreshed.sealed_verdict_artifact_id,
            published=published,
            publication_summary=publication_summary,
            job_created=job_created,
        )


def sealed_dict_from_mapping(payload: Mapping[str, Any]) -> SealedVerdict:
    try:
        return parse_sealed_verdict_payload(payload)
    except ReviewPublicationError as exc:
        raise FormalReviewFinalizeError(str(exc)) from exc


__all__ = [
    "DEFAULT_REPOSITORY",
    "FinalizeResult",
    "FormalReviewFinalizeError",
    "build_sealed_verdict",
    "finalize_formal_review_verdict",
    "resolve_verdict_token",
    "sealed_dict_from_mapping",
]
