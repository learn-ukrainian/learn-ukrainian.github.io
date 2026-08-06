"""Formal CF thrash guards (operator 2026-08-06 — empty reseal / re-CF ban).

Preflight only: never spends a formal reviewer. Does not auto-reset branches.
"""

from __future__ import annotations

import json
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from scripts.fleet_comms.formal_review_jobs import FormalReviewJobsError, open_formal_review_jobs
from scripts.fleet_comms.review_publication import ReviewPublicationError, parse_sealed_verdict_payload

_GATE = "cross-family-review"
_GITHUB_STATUS_COMPONENTS = "https://www.githubstatus.com/api/v2/components.json"
_ACTIONS_OUTAGE = frozenset({"major_outage", "partial_outage"})


@dataclass(frozen=True)
class ThrashDecision:
    """Preflight outcome for formal CF."""

    action: str  # continue | already_approved | refuse
    message: str
    exit_code: int  # 0 continue/already_approved; 2 refuse


def _git_diff_empty(repo: Path, base: str, head: str) -> bool | None:
    """True if trees match, False if differ, None if git cannot decide."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), "diff", "--quiet", base, head],
            check=False,
            capture_output=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode == 0:
        return True
    if proc.returncode == 1:
        return False
    return None


def _load_approved_heads(
    *,
    repository: str,
    pr_number: int,
) -> list[tuple[str, str]]:
    """Return (head_sha, review_id) for complete jobs with sealed APPROVED."""
    out: list[tuple[str, str]] = []
    with open_formal_review_jobs() as jobs:
        complete = jobs.list_jobs(
            repository=repository,
            pr=pr_number,
            gate_kind=_GATE,
            state="complete",
            include_attempts=False,
        )
        for job in complete:
            if not job.sealed_verdict_artifact_id:
                continue
            try:
                sealed = jobs.load_sealed_verdict(job.review_id)
            except (FormalReviewJobsError, ReviewPublicationError, OSError):
                continue
            if str(sealed.verdict).upper() != "APPROVED":
                continue
            out.append((job.head_sha.lower(), job.review_id))
    return out


def github_actions_outaged(*, timeout_s: float = 5.0) -> bool | None:
    """True if Actions is in outage, False if OK, None if status unknown."""
    try:
        with urllib.request.urlopen(_GITHUB_STATUS_COMPONENTS, timeout=timeout_s) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError, ValueError):
        return None
    components = payload.get("components")
    if not isinstance(components, list):
        return None
    for item in components:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "")
        if name.casefold() != "actions":
            continue
        status = str(item.get("status") or "").casefold()
        return status in _ACTIONS_OUTAGE
    return None


def evaluate_formal_cf_thrash(
    *,
    repository: str,
    pr_number: int,
    head_sha: str,
    git_repo: Path | None,
    allow_thrash: bool = False,
    check_actions: bool = True,
) -> ThrashDecision:
    """Decide whether formal CF may spend a reviewer for this PR head."""
    head = head_sha.lower().strip()
    if not head:
        return ThrashDecision("continue", "", 0)

    if check_actions and not allow_thrash:
        outaged = github_actions_outaged()
        if outaged is True:
            return thrash_refuse(
                "GitHub Actions is in outage/degraded (githubstatus). "
                "Do not spend formal CF or reseal until Actions recovers. "
                "Override only with --allow-cf-thrash --override-reason …"
            )

    approved = _load_approved_heads(repository=repository, pr_number=pr_number)
    for approved_head, review_id in approved:
        if approved_head == head:
            return ThrashDecision(
                "already_approved",
                f"review-pr: head {head[:12]} already has sealed APPROVED "
                f"({review_id}); not re-spending formal CF",
                0,
            )

    if allow_thrash:
        return ThrashDecision("continue", "", 0)

    if git_repo is not None and approved:
        for approved_head, review_id in approved:
            same = _git_diff_empty(git_repo, approved_head, head)
            if same is True:
                return thrash_refuse(
                    f"tip {head[:12]} has no product tree change since sealed APPROVED "
                    f"head {approved_head[:12]} ({review_id}). Empty reseal commits do not "
                    f"require re-CF. Reset tip to the APPROVED head or land a real product "
                    f"commit. Override only with --allow-cf-thrash --override-reason …"
                )

    return ThrashDecision("continue", "", 0)


def thrash_refuse(message: str) -> ThrashDecision:
    return ThrashDecision("refuse", f"review-pr: thrash guard: {message}", 2)
