"""Publish an auditable formal-review verdict to one GitHub PR comment.

Two paths:

1. **Legacy (temporary)** — ``--pr`` + ``--verdict-file``/``--findings-json`` + CLI
   provenance flags. Posts a comment only (no commit status, no receipts).

2. **PR-G sealed path** — ``--sealed-payload`` (JSON matching
   ``scripts.fleet_comms.review_publication.SealedVerdict``). Optionally bind
   ``--review-id`` to a durable formal-job row (identity check only; PR-F still
   owns sealed-job writers). Posts evidence-bearing comment + ``fleet/cross-family-review``
   commit status, with stale-head / idempotent receipt handling.

Full default cutover of all formal CF to ``--review-id`` alone waits for PR-F
to store sealed verdict provenance on the job. Do not invent that as landed.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from scripts.fleet_comms.review_publication import (
    ReviewEvidence,
    ReviewPublicationError,
    build_review_comment,
    resolve_verdict_and_evidence,
    verdict_from_review_evidence,
)

from ._review_safety import MAX_VERDICT_SUMMARY_BYTES, ReviewSafetyError

_VERDICT_RE = re.compile(
    r"\bVERDICT\s*:\s*(APPROVED|CHANGES_REQUESTED|BLOCKED)\b", re.IGNORECASE
)
_MAX_INPUT_BYTES = 64 * 1024
_VALID_VERDICTS = frozenset({"APPROVED", "CHANGES_REQUESTED", "BLOCKED"})


def _single_line(value: str, *, label: str) -> str:
    normalized = " ".join(value.split())
    if not normalized:
        raise ReviewSafetyError(f"missing_{label}")
    return normalized


def _read_small_file(path: Path) -> str:
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise ReviewSafetyError(f"verdict_file_unreadable: {path}") from exc
    if size > _MAX_INPUT_BYTES:
        raise ReviewSafetyError(
            f"verdict_file_exceeds_cap: bytes={size} limit={_MAX_INPUT_BYTES}. "
            "Use canonical findings JSON so the evidence can be published."
        )
    return path.read_text(encoding="utf-8")


def verdict_from_text(text: str) -> str:
    """Extract the required verdict from a legacy free-text input."""
    match = _VERDICT_RE.search(text)
    if not match:
        raise ReviewSafetyError("verdict_missing: expected VERDICT: APPROVED|CHANGES_REQUESTED|BLOCKED")
    return match.group(1).upper()


def review_from_findings_json(path: Path) -> tuple[str, ReviewEvidence | None]:
    """Read canonical findings JSON and retain all publishable review evidence."""
    try:
        payload = json.loads(_read_small_file(path))
    except json.JSONDecodeError as exc:
        raise ReviewSafetyError(f"findings_json_invalid: {path}") from exc
    if not isinstance(payload, dict):
        raise ReviewSafetyError("findings_json_invalid: expected an object")
    try:
        return resolve_verdict_and_evidence(payload)
    except ReviewPublicationError as exc:
        raise ReviewSafetyError(str(exc)) from exc


def verdict_from_findings_json(path: Path) -> str:
    """Compatibility helper returning the verdict resolved from findings JSON."""
    return review_from_findings_json(path)[0]


def _coerce_review_evidence(
    review_evidence: ReviewEvidence | dict[str, Any] | None,
) -> tuple[str | None, ReviewEvidence | None]:
    if review_evidence is None:
        return None, None
    if isinstance(review_evidence, ReviewEvidence):
        return verdict_from_review_evidence(review_evidence), review_evidence
    try:
        return resolve_verdict_and_evidence(review_evidence)
    except ReviewPublicationError as exc:
        raise ReviewSafetyError(str(exc)) from exc


def build_verdict_comment(
    *,
    verdict: str,
    head_sha: str,
    model: str,
    family: str,
    harness: str,
    review_evidence: ReviewEvidence | dict[str, Any] | None = None,
) -> str:
    """Build the complete legacy-path comment through the shared renderer."""
    normalized_verdict = _single_line(verdict, label="verdict").upper()
    if normalized_verdict not in _VALID_VERDICTS:
        raise ReviewSafetyError(f"invalid_verdict: {normalized_verdict!r}")
    evidence_verdict, evidence = _coerce_review_evidence(review_evidence)
    if evidence_verdict is not None and evidence_verdict != normalized_verdict:
        raise ReviewSafetyError(
            f"review_evidence_verdict_mismatch: verdict={normalized_verdict} "
            f"evidence={evidence_verdict}"
        )
    return build_review_comment(
        verdict=normalized_verdict,
        head_sha=_single_line(head_sha, label="head_sha"),
        model=_single_line(model, label="model"),
        family=_single_line(family, label="family"),
        harness=_single_line(harness, label="harness"),
        review_evidence=evidence,
    )


Runner = Callable[..., subprocess.CompletedProcess[str]]


def publish_review_verdict(
    *,
    pr: int,
    verdict: str,
    model: str,
    family: str,
    harness: str,
    review_evidence: ReviewEvidence | dict[str, Any] | None = None,
    dry_run: bool = False,
    runner: Runner = subprocess.run,
) -> str:
    """Legacy path: post one evidence-bearing comment and a bounded summary."""
    if pr <= 0:
        raise ReviewSafetyError(f"invalid_pr: {pr}")
    head = runner(
        ["gh", "pr", "view", str(pr), "--json", "headRefOid", "--jq", ".headRefOid"],
        capture_output=True,
        text=True,
        check=False,
    )
    if head.returncode != 0:
        raise ReviewSafetyError(f"gh_pr_head_lookup_failed: pr={pr} exit={head.returncode}")
    head_sha = _single_line(head.stdout, label="head_sha")
    comment = build_verdict_comment(
        verdict=verdict,
        head_sha=head_sha,
        model=model,
        family=family,
        harness=harness,
        review_evidence=review_evidence,
    )
    if not dry_run:
        posted = runner(
            ["gh", "pr", "comment", str(pr), "--body", comment],
            capture_output=True,
            text=True,
            check=False,
        )
        if posted.returncode != 0:
            raise ReviewSafetyError(f"gh_pr_comment_failed: pr={pr} exit={posted.returncode}")
    summary = (
        f"publish-review-verdict: pr={pr} verdict={verdict.upper()} "
        f"head_sha={head_sha} model={_single_line(model, label='model')} "
        f"family={_single_line(family, label='family')} "
        f"harness={_single_line(harness, label='harness')} "
        f"posted={'false (dry-run)' if dry_run else 'true'}"
    )
    if len(summary.encode("utf-8")) > MAX_VERDICT_SUMMARY_BYTES:
        raise ReviewSafetyError("verdict_summary_exceeds_cap")
    return summary


def _emit_publication_result(args: argparse.Namespace, result: Any) -> int:
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        summary = result.summary
        if len(summary.encode("utf-8")) > MAX_VERDICT_SUMMARY_BYTES:
            print("publish-review-verdict: verdict_summary_exceeds_cap", file=sys.stderr)
            return 2
        print(summary)
    if result.plan.action == "refuse_stale":
        return 3
    return 0


def _handle_review_id_only(args: argparse.Namespace) -> int:
    """PR-F+G path: load sealed verdict from durable job; no CLI provenance."""
    from scripts.fleet_comms.formal_review_jobs import (
        FormalReviewJobsError,
        FormalReviewJobService,
    )
    from scripts.fleet_comms.review_publisher import (
        ReviewPublisherError,
        publish_sealed_verdict,
    )

    plane_root = Path(args.plane_root).expanduser() if args.plane_root else None
    try:
        with FormalReviewJobService(root=plane_root) as service:
            sealed = service.load_sealed_verdict(args.review_id)
            result = publish_sealed_verdict(
                sealed,
                mutate=not args.dry_run,
                # Formal --review-id path always records github_publications receipts.
                require_receipt=True,
                store=service.store,
            )
    except (FormalReviewJobsError, ReviewPublisherError) as exc:
        print(f"publish-review-verdict: {exc}", file=sys.stderr)
        return 2
    return _emit_publication_result(args, result)


def _handle_sealed_path(args: argparse.Namespace) -> int:
    """PR-G sealed path: pure plan + optional GitHub mutate + receipts."""
    from scripts.fleet_comms.artifacts import ArtifactStore
    from scripts.fleet_comms.formal_review_jobs import (
        FormalReviewJobsError,
        FormalReviewJobService,
    )
    from scripts.fleet_comms.review_publisher import (
        ReviewPublisherError,
        load_sealed_payload_file,
        publish_sealed_verdict,
        sealed_matches_job,
    )

    payload_path = Path(args.sealed_payload)
    try:
        sealed = load_sealed_payload_file(payload_path)
    except ReviewPublisherError as exc:
        print(f"publish-review-verdict: {exc}", file=sys.stderr)
        return 2

    plane_root = Path(args.plane_root).expanduser() if args.plane_root else None
    store: ArtifactStore | None = None
    service: FormalReviewJobService | None = None

    try:
        if args.review_id:
            # Bind sealed payload identity to durable job row (fail closed).
            try:
                service = FormalReviewJobService(root=plane_root)
                job = service.get_job(args.review_id, include_attempts=False)
            except FormalReviewJobsError as exc:
                print(f"publish-review-verdict: {exc}", file=sys.stderr)
                return 2
            try:
                sealed_matches_job(
                    sealed,
                    review_id=job.review_id,
                    repository=job.repository,
                    pr_number=job.pr_number,
                    head_sha=job.head_sha,
                    gate_kind=job.gate_kind,
                )
            except ReviewPublisherError as exc:
                print(f"publish-review-verdict: {exc}", file=sys.stderr)
                return 2
            # Persist sealed verdict if not already (enables future --review-id alone).
            try:
                service.accept_sealed_verdict(
                    job.review_id,
                    sealed,
                    record_complete_attempt=not job.has_sealed_verdict,
                )
            except FormalReviewJobsError as exc:
                print(f"publish-review-verdict: {exc}", file=sys.stderr)
                return 2
            store = service.store
        elif plane_root is not None or args.require_receipt:
            store = ArtifactStore(root=plane_root)

        result = publish_sealed_verdict(
            sealed,
            mutate=not args.dry_run,
            require_receipt=bool(args.require_receipt),
            store=store,
        )
    except ReviewPublisherError as exc:
        print(f"publish-review-verdict: {exc}", file=sys.stderr)
        return 2
    finally:
        if service is not None:
            service.close()
        elif store is not None:
            store.close()

    return _emit_publication_result(args, result)


def handle_publish_review_verdict(args: argparse.Namespace) -> int:
    """CLI handler for ``publish-review-verdict``."""
    has_legacy_file = bool(getattr(args, "verdict_file", None) or getattr(args, "findings_json", None))
    has_sealed_file = bool(getattr(args, "sealed_payload", None))
    has_review_id = bool(getattr(args, "review_id", None))

    if has_review_id and not has_sealed_file and not has_legacy_file:
        return _handle_review_id_only(args)
    if has_sealed_file:
        return _handle_sealed_path(args)

    # Legacy path: require CLI provenance flags.
    missing = [
        name
        for name in ("pr", "model", "family", "harness")
        if getattr(args, name, None) in (None, "")
    ]
    if missing:
        print(
            "publish-review-verdict: legacy path requires "
            + ", ".join(f"--{m}" for m in missing)
            + " (or use --sealed-payload / --review-id)",
            file=sys.stderr,
        )
        return 2
    if not has_legacy_file:
        print(
            "publish-review-verdict: provide --verdict-file, --findings-json, "
            "--sealed-payload, or --review-id",
            file=sys.stderr,
        )
        return 2

    try:
        if args.findings_json:
            verdict, review_evidence = review_from_findings_json(Path(args.findings_json))
        else:
            verdict = verdict_from_text(_read_small_file(Path(args.verdict_file)))
            review_evidence = None
        print(
            publish_review_verdict(
                pr=int(args.pr),
                verdict=verdict,
                model=args.model,
                family=args.family,
                harness=args.harness,
                review_evidence=review_evidence,
                dry_run=args.dry_run,
            )
        )
    except ReviewSafetyError as exc:
        print(f"publish-review-verdict: {exc}", file=sys.stderr)
        return 2
    return 0


def register_publish_review_verdict_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "publish-review-verdict",
        help=(
            "Post one auditable formal-review verdict (legacy file path, "
            "--sealed-payload, or --review-id alone after PR-F accept)"
        ),
    )
    source = parser.add_mutually_exclusive_group(required=False)
    source.add_argument("--verdict-file", help="Short text containing a VERDICT line (legacy)")
    source.add_argument(
        "--findings-json",
        help="Findings JSON with a top-level verdict field (legacy)",
    )
    source.add_argument(
        "--sealed-payload",
        help=(
            "PR-G sealed verdict JSON (review_id, repository, pr_number, head_sha, "
            "gate_kind, verdict, model, family, harness). Provenance is never taken "
            "from CLI flags on this path."
        ),
    )
    parser.add_argument(
        "--review-id",
        help=(
            "PR-F durable formal-job id. Alone: reload sealed verdict from the job "
            "and publish (no CLI provenance). With --sealed-payload: bind + accept."
        ),
    )
    parser.add_argument(
        "--plane-root",
        help="Fleet-comms ArtifactStore root for receipts / formal jobs (optional)",
    )
    parser.add_argument(
        "--require-receipt",
        action="store_true",
        help="Refuse live sealed publish when no plane DB is available for receipts",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="On sealed path, emit full PublicationResult JSON",
    )
    # Legacy-only flags (optional at parse time; validated in handler).
    parser.add_argument("--pr", type=int, help="Pull request number (legacy path)")
    parser.add_argument("--model", help="Exact reviewer model ID (legacy path)")
    parser.add_argument("--family", help="Reviewer model family (legacy path)")
    parser.add_argument("--harness", help="Reviewer harness (legacy path)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan / resolve head without posting comment or commit status",
    )
