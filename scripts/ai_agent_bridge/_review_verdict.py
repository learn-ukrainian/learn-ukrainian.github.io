"""Publish a deliberately thin formal-review verdict to one GitHub PR comment.

PR-G cutover note: the eventual ``publish-review-verdict --review-id`` path
(sealed job reload, stale-head check, idempotent status/comment) is prepared in
``scripts/fleet_comms/review_publication.py``. Full default cutover waits for
PR-F formal-jobs table writers; this CLI remains the temporary file/flag-based
poster and must not switch defaults until then.
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
            "Publish only a verdict or findings JSON, never a full review body."
        )
    return path.read_text(encoding="utf-8")


def verdict_from_text(text: str) -> str:
    """Extract the required verdict without retaining the review body."""
    match = _VERDICT_RE.search(text)
    if not match:
        raise ReviewSafetyError("verdict_missing: expected VERDICT: APPROVED|CHANGES_REQUESTED|BLOCKED")
    return match.group(1).upper()


def verdict_from_findings_json(path: Path) -> str:
    """Read a findings JSON document and extract its top-level verdict field."""
    try:
        payload = json.loads(_read_small_file(path))
    except json.JSONDecodeError as exc:
        raise ReviewSafetyError(f"findings_json_invalid: {path}") from exc
    if not isinstance(payload, dict):
        raise ReviewSafetyError("findings_json_invalid: expected an object with a verdict field")
    raw = payload.get("verdict")
    if not isinstance(raw, str) or raw.upper() not in _VALID_VERDICTS:
        raise ReviewSafetyError("findings_json_missing_verdict: expected APPROVED|CHANGES_REQUESTED|BLOCKED")
    return raw.upper()


def build_verdict_comment(*, verdict: str, head_sha: str, model: str, family: str, harness: str) -> str:
    """Build the complete comment body; it intentionally has no review findings."""
    normalized_verdict = _single_line(verdict, label="verdict").upper()
    if normalized_verdict not in _VALID_VERDICTS:
        raise ReviewSafetyError(f"invalid_verdict: {normalized_verdict!r}")
    return "\n".join(
        (
            f"VERDICT: {normalized_verdict}",
            f"Head SHA: {_single_line(head_sha, label='head_sha')}",
            "Reviewer provenance: "
            f"model={_single_line(model, label='model')}; "
            f"family={_single_line(family, label='family')}; "
            f"harness={_single_line(harness, label='harness')}",
        )
    )


Runner = Callable[..., subprocess.CompletedProcess[str]]


def publish_review_verdict(
    *,
    pr: int,
    verdict: str,
    model: str,
    family: str,
    harness: str,
    dry_run: bool = False,
    runner: Runner = subprocess.run,
) -> str:
    """Post one comment and return a bounded, body-free orchestrator summary."""
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


def handle_publish_review_verdict(args: argparse.Namespace) -> int:
    """CLI handler for ``publish-review-verdict``."""
    try:
        verdict = (
            verdict_from_findings_json(Path(args.findings_json))
            if args.findings_json
            else verdict_from_text(_read_small_file(Path(args.verdict_file)))
        )
        print(
            publish_review_verdict(
                pr=args.pr,
                verdict=verdict,
                model=args.model,
                family=args.family,
                harness=args.harness,
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
        help="Post one thin formal-review verdict comment to a PR",
    )
    parser.add_argument("--pr", type=int, required=True, help="Pull request number")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--verdict-file", help="Short text containing a VERDICT line")
    source.add_argument("--findings-json", help="Findings JSON with a top-level verdict field")
    parser.add_argument("--model", required=True, help="Exact reviewer model ID")
    parser.add_argument("--family", required=True, help="Reviewer model family")
    parser.add_argument("--harness", required=True, help="Reviewer harness")
    parser.add_argument("--dry-run", action="store_true", help="Resolve head SHA without posting")
