#!/usr/bin/env python3
"""Arm GitHub auto-merge only for explicitly opted-in, fully green PRs.

Issue #7539 deliberately delegates merging to GitHub's existing branch
protection and merge queue.  This scanner never merges directly and never uses
an administrative bypass: it only requests ``gh pr merge --auto`` after the
exact-head CF and CI gates have both passed.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

AUTO_ARM_OPT_IN_LABEL = "automerge-ok"
BLOCKING_LABELS = frozenset({"do-not-merge", "hold"})
CF_ATTEST_CHECK = "CF attest"
CI_GATE_CHECK = "CI Gate"
ADVISORY_MARKER = "advisory"
GREEN_CONCLUSIONS = frozenset({"SUCCESS", "NEUTRAL", "SKIPPED"})
PENDING_STATES = frozenset({"", "EXPECTED", "IN_PROGRESS", "PENDING", "QUEUED", "REQUESTED", "STALE", "WAITING"})
SHA_RE = re.compile(r"[0-9a-f]{40}", re.IGNORECASE)
DEFAULT_GH_TIMEOUT = 60


@dataclass(frozen=True)
class ArmDecision:
    """A deterministic disposition for one pull request."""

    should_arm: bool
    reason: str
    number: int | None = None
    head_sha: str = ""


def _parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(UTC)


def _check_name(check: Mapping[str, Any]) -> str | None:
    for field in ("name", "context"):
        value = check.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _check_key(check: Mapping[str, Any], name: str) -> tuple[str, ...] | None:
    """Return a stable check identity, refusing ambiguous duplicate names."""

    context = check.get("context")
    if isinstance(context, str) and context.strip():
        return ("context", context.strip())
    workflow = check.get("workflowName") or check.get("workflow")
    if isinstance(workflow, str) and workflow.strip():
        return ("check", name, workflow.strip())
    return ("unresolved", name)


def decide_latest_checks(checks: object) -> tuple[dict[tuple[str, ...], Mapping[str, Any]] | None, str | None]:
    """Return latest check rows, or a fail-closed reason for malformed data.

    GitHub includes historical attempts in ``statusCheckRollup``.  A cancelled
    first run must not defeat a newer successful retry, while timestamp ties or
    duplicate unscoped contexts are ambiguous and therefore cannot arm a PR.
    """

    if not isinstance(checks, list) or not checks:
        return None, "checks_unavailable"

    latest: dict[tuple[str, ...], tuple[datetime | None, Mapping[str, Any]]] = {}
    for row in checks:
        if not isinstance(row, Mapping):
            return None, "invalid_check_row"
        name = _check_name(row)
        if name is None:
            return None, "unnamed_check"
        key = _check_key(row, name)
        if key is None:
            return None, "unidentifiable_check"
        timestamp = _parse_timestamp(row.get("startedAt")) or _parse_timestamp(row.get("completedAt"))
        previous = latest.get(key)
        if previous is None:
            latest[key] = (timestamp, row)
            continue
        previous_timestamp, _previous_row = previous
        if timestamp is None or previous_timestamp is None:
            return None, f"ambiguous_check_history:{name}"
        if timestamp == previous_timestamp:
            return None, f"ambiguous_check_history:{name}"
        if timestamp > previous_timestamp:
            latest[key] = (timestamp, row)

    return {key: row for key, (_timestamp, row) in latest.items()}, None


def _check_outcome(check: Mapping[str, Any]) -> str:
    """Normalize a check-run or legacy status context to green/pending/failing."""

    state = str(check.get("state") or "").strip().upper()
    status = str(check.get("status") or "").strip().upper()
    conclusion = str(check.get("conclusion") or "").strip().upper()
    if state and not status and not conclusion:
        if state in GREEN_CONCLUSIONS:
            return "green"
        if state in PENDING_STATES:
            return "pending"
        return "failing"
    if status in PENDING_STATES:
        return "pending"
    if status != "COMPLETED":
        return "failing"
    if conclusion in GREEN_CONCLUSIONS:
        return "green"
    if conclusion in PENDING_STATES:
        return "pending"
    return "failing"


def _label_names(pr: Mapping[str, Any]) -> set[str] | None:
    labels = pr.get("labels")
    if not isinstance(labels, list):
        return None
    names: set[str] = set()
    for label in labels:
        name = label.get("name") if isinstance(label, Mapping) else label
        if not isinstance(name, str) or not name.strip():
            return None
        names.add(name.strip().casefold())
    return names


def _usable_pr_number(value: object) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        return value
    return None


def _required_check_is_green(checks: Sequence[Mapping[str, Any]], expected_name: str) -> bool:
    matching = [check for check in checks if _check_name(check) == expected_name]
    return len(matching) == 1 and _check_outcome(matching[0]) == "green" and str(
        matching[0].get("conclusion") or matching[0].get("state") or ""
    ).strip().upper() == "SUCCESS"


def decide_auto_arm(pr: Mapping[str, Any]) -> ArmDecision:
    """Decide whether fetched current-head PR data can receive auto-merge.

    ``gh pr list --json statusCheckRollup,headRefOid`` supplies the rollup for
    the PR's current head.  The required ``CF attest`` job itself validates the
    exact-head cross-family evidence, so this function intentionally trusts
    only that job's successful conclusion rather than reimplementing it.
    """

    number = _usable_pr_number(pr.get("number"))
    if number is None:
        return ArmDecision(False, "invalid_pr_number")
    if str(pr.get("state") or "").upper() != "OPEN":
        return ArmDecision(False, "not_open", number)
    if str(pr.get("baseRefName") or "") != "main":
        return ArmDecision(False, "not_main_base", number)
    if pr.get("isDraft") is not False:
        return ArmDecision(False, "draft_or_unknown", number)
    if pr.get("autoMergeRequest"):
        return ArmDecision(False, "already_armed_or_queued", number)

    labels = _label_names(pr)
    if labels is None:
        return ArmDecision(False, "labels_unavailable", number)
    if BLOCKING_LABELS & labels:
        return ArmDecision(False, "blocking_label", number)
    if AUTO_ARM_OPT_IN_LABEL not in labels:
        return ArmDecision(False, "opt_in_label_missing", number)

    head_sha = pr.get("headRefOid")
    if not isinstance(head_sha, str) or SHA_RE.fullmatch(head_sha) is None:
        return ArmDecision(False, "invalid_head_sha", number)

    latest, error = decide_latest_checks(pr.get("statusCheckRollup"))
    if latest is None:
        return ArmDecision(False, error or "checks_unavailable", number)
    current_checks = list(latest.values())
    if not _required_check_is_green(current_checks, CF_ATTEST_CHECK):
        return ArmDecision(False, "cf_attest_not_green_at_head", number)
    if not _required_check_is_green(current_checks, CI_GATE_CHECK):
        return ArmDecision(False, "ci_gate_not_green", number)

    for check in current_checks:
        name = _check_name(check)
        assert name is not None
        if ADVISORY_MARKER in name.casefold():
            continue
        outcome = _check_outcome(check)
        if outcome == "pending":
            return ArmDecision(False, f"blocking_check_pending:{name}", number)
        if outcome != "green":
            return ArmDecision(False, f"blocking_check_failing:{name}", number)

    return ArmDecision(True, "cf_attest_and_ci_gate_green", number, head_sha)


def _gh_env(token: str) -> dict[str, str]:
    env = dict(os.environ)
    env["GH_TOKEN"] = token
    env["NO_COLOR"] = "1"
    env["CLICOLOR"] = "0"
    env.pop("CLICOLOR_FORCE", None)
    env.pop("FORCE_COLOR", None)
    return env


def _gh(args: Sequence[str], *, token: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["gh", *args],
        check=False,
        capture_output=True,
        text=True,
        env=_gh_env(token),
        timeout=DEFAULT_GH_TIMEOUT,
    )


def _gh_json(args: Sequence[str], *, token: str) -> Any:
    try:
        completed = _gh(args, token=token)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"gh timed out after {exc.timeout}s") from exc
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise RuntimeError(detail or "gh command failed")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("gh command returned invalid JSON") from exc


PR_JSON_FIELDS = (
    "number,state,baseRefName,isDraft,labels,headRefOid,autoMergeRequest,"
    "statusCheckRollup"
)


def list_open_prs(repo: str, *, token: str) -> list[dict[str, Any]]:
    """Fetch open PRs into the complete data shape consumed by ``decide_auto_arm``."""

    payload = _gh_json(
        [
            "pr",
            "list",
            "--repo",
            repo,
            "--base",
            "main",
            "--state",
            "open",
            "--limit",
            "1000",
            "--json",
            PR_JSON_FIELDS,
        ],
        token=token,
    )
    if not isinstance(payload, list) or not all(isinstance(item, dict) for item in payload):
        raise RuntimeError("open PR response is not a list of objects")
    return payload


def enable_auto_merge(repo: str, number: int, head_sha: str, *, token: str) -> None:
    """Request auto-merge only if GitHub still sees the checked current head."""

    completed = _gh(
        ["pr", "merge", str(number), "--repo", repo, "--match-head-commit", head_sha, "--auto"],
        token=token,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise RuntimeError(detail or f"failed to enable auto-merge for PR #{number}")


def post_audit_comment(repo: str, number: int, head_sha: str, *, token: str) -> None:
    body = f"auto-arm: queued at head {head_sha} (cf-attest+gate green)"
    completed = _gh(["pr", "comment", str(number), "--repo", repo, "--body", body], token=token)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise RuntimeError(detail or f"failed to post audit comment for PR #{number}")


def arm_eligible_prs(
    prs: Sequence[Mapping[str, Any]],
    *,
    enable: Callable[[int, str], None],
    comment: Callable[[int, str], None],
) -> list[ArmDecision]:
    """Evaluate PRs and perform the two thin mutating operations for green ones."""

    decisions: list[ArmDecision] = []
    for pr in prs:
        decision = decide_auto_arm(pr)
        decisions.append(decision)
        if not decision.should_arm:
            continue
        assert decision.number is not None
        enable(decision.number, decision.head_sha)
        comment(decision.number, decision.head_sha)
    return decisions


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY"), help="OWNER/REPO to scan")
    args = parser.parse_args(list(argv) if argv is not None else None)

    if os.environ.get("AUTO_ARM_MERGE_DISABLED") == "1":
        print("auto-arm merge disabled by AUTO_ARM_MERGE_DISABLED=1")
        return 0
    if not args.repo:
        raise SystemExit("--repo or GITHUB_REPOSITORY is required")
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GH_TOKEN or GITHUB_TOKEN is required")

    decisions = arm_eligible_prs(
        list_open_prs(args.repo, token=token),
        enable=lambda number, head_sha: enable_auto_merge(args.repo, number, head_sha, token=token),
        comment=lambda number, head_sha: post_audit_comment(args.repo, number, head_sha, token=token),
    )
    for decision in decisions:
        if decision.reason == "already_armed_or_queued":
            continue
        print(json.dumps({"number": decision.number, "reason": decision.reason, "armed": decision.should_arm}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
