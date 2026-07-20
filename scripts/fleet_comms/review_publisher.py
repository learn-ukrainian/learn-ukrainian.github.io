"""PR-G live verdict publisher: execute planned GitHub gate posts + receipts.

Sol fleet-comms (#5512) PR-G owns the GitHub side of formal review publication:

* resolve current PR head (fail closed on lookup failure)
* plan via pure ``review_publication.plan_publication`` (stale / idempotent / ready)
* when mutate is requested and the plan says ``publish``: post one thin PR comment
  and one commit status under ``fleet/cross-family-review``
* record a durable row in ``github_publications`` (schema v1)

This module still does **not** create formal jobs, seal snapshots, or cut over
``review-pr``. Those remain PR-F / later wiring. Callers that only have a sealed
payload (not a stored job) can publish without a plane DB; receipt recording
requires an open plane store.
"""

from __future__ import annotations

import json
import re
import sqlite3
import subprocess
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.fleet_comms.artifacts import ArtifactStore
from scripts.fleet_comms.contracts import new_id
from scripts.fleet_comms.migrations import apply_migrations
from scripts.fleet_comms.review_publication import (
    DEFAULT_STATUS_CONTEXT,
    PublicationPlan,
    ReviewPublicationError,
    SealedVerdict,
    parse_sealed_verdict_payload,
    plan_publication,
    publication_idempotency_key,
)

Runner = Callable[..., subprocess.CompletedProcess[str]]

_SHA_RE = re.compile(r"^[0-9a-f]{7,64}$", re.IGNORECASE)


class ReviewPublisherError(RuntimeError):
    """Live GitHub publication or receipt recording failed closed."""


@dataclass(frozen=True, slots=True)
class PublicationResult:
    """Outcome of planning and optionally executing a GitHub gate post."""

    plan: PublicationPlan
    publication_id: str | None
    comment_url: str | None
    status_posted: bool
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan": self.plan.to_dict(),
            "publication_id": self.publication_id,
            "comment_url": self.comment_url,
            "status_posted": self.status_posted,
            "summary": self.summary,
        }


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _single_line(value: str, *, label: str) -> str:
    normalized = " ".join(value.split())
    if not normalized:
        raise ReviewPublisherError(f"missing_{label}")
    return normalized


def split_repository(repository: str) -> tuple[str, str]:
    """Parse ``owner/repo``; refuse other shapes."""
    text = _single_line(repository, label="repository")
    if text.count("/") != 1:
        raise ReviewPublisherError(
            f"invalid_repository: expected owner/repo, got {repository!r}"
        )
    owner, repo = text.split("/", 1)
    if not owner or not repo:
        raise ReviewPublisherError(
            f"invalid_repository: expected owner/repo, got {repository!r}"
        )
    return owner, repo


def fetch_pr_head_sha(
    *,
    repository: str,
    pr_number: int,
    runner: Runner = subprocess.run,
) -> str:
    """Return the live PR head OID via ``gh`` (injectable for tests)."""
    if pr_number <= 0:
        raise ReviewPublisherError(f"invalid_pr: {pr_number}")
    owner, repo = split_repository(repository)
    completed = runner(
        [
            "gh",
            "pr",
            "view",
            str(pr_number),
            "--repo",
            f"{owner}/{repo}",
            "--json",
            "headRefOid",
            "--jq",
            ".headRefOid",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        stderr = (completed.stderr or "").strip()
        raise ReviewPublisherError(
            f"gh_pr_head_lookup_failed: pr={pr_number} repo={owner}/{repo} "
            f"exit={completed.returncode}"
            + (f" stderr={stderr[:200]}" if stderr else "")
        )
    head = _single_line(completed.stdout or "", label="head_sha")
    if not _SHA_RE.match(head):
        raise ReviewPublisherError(f"gh_pr_head_invalid: {head!r}")
    return head.lower() if len(head) == 40 else head


def post_pr_comment(
    *,
    repository: str,
    pr_number: int,
    body: str,
    runner: Runner = subprocess.run,
) -> str:
    """Post one PR comment; return the comment URL when gh prints it."""
    owner, repo = split_repository(repository)
    completed = runner(
        [
            "gh",
            "pr",
            "comment",
            str(pr_number),
            "--repo",
            f"{owner}/{repo}",
            "--body",
            body,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        stderr = (completed.stderr or "").strip()
        raise ReviewPublisherError(
            f"gh_pr_comment_failed: pr={pr_number} exit={completed.returncode}"
            + (f" stderr={stderr[:200]}" if stderr else "")
        )
    return _single_line(completed.stdout or "(posted)", label="comment_url")


def post_commit_status(
    *,
    repository: str,
    head_sha: str,
    state: str,
    context: str,
    description: str,
    runner: Runner = subprocess.run,
) -> None:
    """Create a commit status on the exact reviewed SHA."""
    owner, repo = split_repository(repository)
    if state not in {"success", "failure", "error", "pending"}:
        raise ReviewPublisherError(f"invalid_status_state: {state!r}")
    completed = runner(
        [
            "gh",
            "api",
            f"repos/{owner}/{repo}/statuses/{head_sha}",
            "-f",
            f"state={state}",
            "-f",
            f"context={context}",
            "-f",
            f"description={description[:140]}",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        stderr = (completed.stderr or "").strip()
        raise ReviewPublisherError(
            f"gh_commit_status_failed: sha={head_sha} state={state} "
            f"exit={completed.returncode}"
            + (f" stderr={stderr[:200]}" if stderr else "")
        )


def lookup_publication_receipt(
    conn: sqlite3.Connection,
    *,
    review_id: str,
    status_context: str = DEFAULT_STATUS_CONTEXT,
) -> dict[str, Any] | None:
    """Return the durable publication row when one already exists."""
    rid = _single_line(review_id, label="review_id")
    ctx = _single_line(status_context, label="status_context")
    row = conn.execute(
        """SELECT publication_id, review_id, head_sha, status_context, published_at
           FROM github_publications
           WHERE review_id = ? AND status_context = ?""",
        (rid, ctx),
    ).fetchone()
    if row is None:
        return None
    if isinstance(row, sqlite3.Row):
        return dict(row)
    keys = ("publication_id", "review_id", "head_sha", "status_context", "published_at")
    return dict(zip(keys, row, strict=True))


def record_publication_receipt(
    conn: sqlite3.Connection,
    *,
    review_id: str,
    head_sha: str,
    status_context: str = DEFAULT_STATUS_CONTEXT,
    publication_id: str | None = None,
) -> str:
    """Insert one ``github_publications`` row; refuse duplicates."""
    rid = _single_line(review_id, label="review_id")
    sha = _single_line(head_sha, label="head_sha").lower()
    ctx = _single_line(status_context, label="status_context")
    existing = lookup_publication_receipt(conn, review_id=rid, status_context=ctx)
    if existing is not None:
        return str(existing["publication_id"])
    pid = publication_id or new_id("publication")
    try:
        conn.execute(
            """INSERT INTO github_publications(
                publication_id, review_id, head_sha, status_context, published_at
            ) VALUES (?, ?, ?, ?, ?)""",
            (pid, rid, sha, ctx, _utc_now()),
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        raced = lookup_publication_receipt(conn, review_id=rid, status_context=ctx)
        if raced is not None:
            return str(raced["publication_id"])
        raise ReviewPublisherError(
            f"failed to record publication receipt for {rid}: {exc}"
        ) from exc
    return pid


def already_published_key_for_job(
    conn: sqlite3.Connection,
    sealed: SealedVerdict,
    *,
    status_context: str = DEFAULT_STATUS_CONTEXT,
) -> str | None:
    """If a receipt exists for this review, return the pure-module idempotency key."""
    receipt = lookup_publication_receipt(
        conn, review_id=sealed.review_id, status_context=status_context
    )
    if receipt is None:
        return None
    # Receipt proves one effective post for this review_id+context.
    return publication_idempotency_key(
        repository=sealed.repository,
        pr_number=sealed.pr_number,
        head_sha=sealed.head_sha,
        gate_kind=sealed.gate_kind,
    )


def _summary_for(plan: PublicationPlan, *, posted: bool, publication_id: str | None) -> str:
    parts = [
        f"publish-review-verdict: action={plan.action}",
        f"review_id={plan.review_id}",
        f"pr={plan.pr_number}",
        f"verdict={plan.verdict}",
        f"head_sha={plan.head_sha}",
        f"status_context={plan.status_context}",
        f"status_state={plan.status_state or 'none'}",
        f"posted={'true' if posted else 'false'}",
        f"reason={plan.reason}",
    ]
    if publication_id:
        parts.append(f"publication_id={publication_id}")
    return " ".join(parts)


def execute_publication(
    plan: PublicationPlan,
    *,
    runner: Runner = subprocess.run,
    conn: sqlite3.Connection | None = None,
    require_receipt: bool = False,
) -> PublicationResult:
    """Execute a planned publication (or no-op for refuse/skip/dry-run).

    Parameters
    ----------
    plan:
        Output of ``plan_publication`` (never talks to GitHub itself).
    runner:
        Injectable subprocess runner (``gh`` CLI).
    conn:
        Optional plane SQLite connection for ``github_publications`` receipts.
    require_receipt:
        When True and mutate publishes, refuse if ``conn`` is missing so we never
        post without a durable receipt path.
    """
    if plan.action in {"refuse_stale", "skip_idempotent"}:
        return PublicationResult(
            plan=plan,
            publication_id=None,
            comment_url=None,
            status_posted=False,
            summary=_summary_for(plan, posted=False, publication_id=None),
        )

    if plan.action != "publish":
        raise ReviewPublisherError(f"unsupported_plan_action: {plan.action!r}")

    if not plan.mutate:
        return PublicationResult(
            plan=plan,
            publication_id=None,
            comment_url=None,
            status_posted=False,
            summary=_summary_for(plan, posted=False, publication_id=None),
        )

    if plan.comment_body is None or plan.status_state is None:
        raise ReviewPublisherError("publish_plan_incomplete: missing comment or status")

    if require_receipt and conn is None:
        raise ReviewPublisherError(
            "receipt_required: refuse live publish without plane DB connection"
        )

    comment_url = post_pr_comment(
        repository=plan.repository,
        pr_number=plan.pr_number,
        body=plan.comment_body,
        runner=runner,
    )
    description = f"VERDICT: {plan.verdict} review_id={plan.review_id}"
    post_commit_status(
        repository=plan.repository,
        head_sha=plan.head_sha,
        state=plan.status_state,
        context=plan.status_context,
        description=description,
        runner=runner,
    )

    publication_id: str | None = None
    if conn is not None:
        publication_id = record_publication_receipt(
            conn,
            review_id=plan.review_id,
            head_sha=plan.head_sha,
            status_context=plan.status_context,
        )

    return PublicationResult(
        plan=plan,
        publication_id=publication_id,
        comment_url=comment_url,
        status_posted=True,
        summary=_summary_for(plan, posted=True, publication_id=publication_id),
    )


def ensure_job_row_for_receipt(
    store: ArtifactStore,
    sealed: SealedVerdict,
) -> None:
    """Ensure ``formal_review_jobs`` has a row so ``github_publications`` FK can fire.

    PR-F owns full sealed-job lifecycle. PR-G only materializes the unique key
    row when the sealed payload is already authoritative and a receipt is about
    to be written — never invents a different review_id/head.
    """
    from scripts.fleet_comms.formal_review_jobs import (
        FormalReviewJobsError,
        FormalReviewJobService,
    )

    apply_migrations(store.connection)
    # Do not close the service: it shares the caller's ArtifactStore connection.
    service = FormalReviewJobService(store=store)
    existing = service.find_job(
        sealed.repository,
        sealed.pr_number,
        sealed.head_sha,
        sealed.gate_kind,
    )
    if existing is not None:
        if existing.review_id != sealed.review_id:
            raise ReviewPublisherError(
                "formal_job_review_id_mismatch: "
                f"job={existing.review_id!r} sealed={sealed.review_id!r}"
            )
        return
    by_id = None
    try:
        by_id = service.get_job(sealed.review_id, include_attempts=False)
    except FormalReviewJobsError:
        by_id = None
    if by_id is not None:
        sealed_matches_job(
            sealed,
            review_id=by_id.review_id,
            repository=by_id.repository,
            pr_number=by_id.pr_number,
            head_sha=by_id.head_sha,
            gate_kind=by_id.gate_kind,
        )
        return
    service.create_job(
        sealed.repository,
        sealed.pr_number,
        sealed.head_sha,
        sealed.gate_kind,
        review_id=sealed.review_id,
        state="complete",
    )


def publish_sealed_verdict(
    sealed: SealedVerdict | Mapping[str, Any] | str | bytes | Path,
    *,
    current_head_sha: str | None = None,
    mutate: bool = False,
    runner: Runner = subprocess.run,
    store: ArtifactStore | None = None,
    require_receipt: bool = False,
    status_context: str = DEFAULT_STATUS_CONTEXT,
) -> PublicationResult:
    """End-to-end sealed path: parse → head check → plan → optional execute.

    When ``current_head_sha`` is omitted, the live PR head is fetched via ``gh``.
    When ``store`` is provided, receipts are written to its SQLite connection.
    """
    if isinstance(sealed, Path):
        sealed = sealed.read_text(encoding="utf-8")
    if not isinstance(sealed, SealedVerdict):
        sealed = parse_sealed_verdict_payload(sealed)

    head = current_head_sha
    if head is None:
        head = fetch_pr_head_sha(
            repository=sealed.repository,
            pr_number=sealed.pr_number,
            runner=runner,
        )

    conn: sqlite3.Connection | None = None
    already_key: str | None = None
    if store is not None:
        conn = store.connection
        apply_migrations(conn)
        if mutate:
            # Materialize FK parent before any GitHub post when receipts are on.
            ensure_job_row_for_receipt(store, sealed)
        already_key = already_published_key_for_job(
            conn, sealed, status_context=status_context
        )

    plan = plan_publication(
        sealed,
        current_head_sha=head,
        already_published_key=already_key,
        mutate=mutate,
        status_context=status_context,
    )
    return execute_publication(
        plan,
        runner=runner,
        conn=conn,
        require_receipt=require_receipt,
    )


def load_sealed_payload_file(path: Path) -> SealedVerdict:
    """Load and validate a sealed verdict JSON file."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ReviewPublisherError(f"sealed_payload_unreadable: {path}") from exc
    try:
        return parse_sealed_verdict_payload(text)
    except ReviewPublicationError as exc:
        raise ReviewPublisherError(str(exc)) from exc


def sealed_matches_job(
    sealed: SealedVerdict,
    *,
    review_id: str,
    repository: str,
    pr_number: int,
    head_sha: str,
    gate_kind: str,
) -> None:
    """Fail closed when sealed payload does not match the durable job row."""
    if sealed.review_id != review_id:
        raise ReviewPublisherError(
            f"sealed_job_mismatch: review_id sealed={sealed.review_id!r} job={review_id!r}"
        )
    if sealed.repository != repository:
        raise ReviewPublisherError(
            f"sealed_job_mismatch: repository sealed={sealed.repository!r} job={repository!r}"
        )
    if sealed.pr_number != pr_number:
        raise ReviewPublisherError(
            f"sealed_job_mismatch: pr sealed={sealed.pr_number} job={pr_number}"
        )
    if sealed.head_sha.lower() != head_sha.lower():
        raise ReviewPublisherError(
            f"sealed_job_mismatch: head_sha sealed={sealed.head_sha!r} job={head_sha!r}"
        )
    if sealed.gate_kind != gate_kind:
        raise ReviewPublisherError(
            f"sealed_job_mismatch: gate_kind sealed={sealed.gate_kind!r} job={gate_kind!r}"
        )


def dump_plan_json(result: PublicationResult) -> str:
    """JSON dump for CLI dry-run inspection."""
    return json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n"


__all__ = [
    "PublicationResult",
    "ReviewPublisherError",
    "Runner",
    "already_published_key_for_job",
    "dump_plan_json",
    "ensure_job_row_for_receipt",
    "execute_publication",
    "fetch_pr_head_sha",
    "load_sealed_payload_file",
    "lookup_publication_receipt",
    "post_commit_status",
    "post_pr_comment",
    "publish_sealed_verdict",
    "record_publication_receipt",
    "sealed_matches_job",
    "split_repository",
]
