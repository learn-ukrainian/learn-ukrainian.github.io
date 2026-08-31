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

from scripts.ci.cf_attest import parse_attestation

AUTO_ARM_OPT_IN_LABEL = "automerge-ok"
BLOCKING_LABELS = frozenset({"do-not-merge", "hold"})
CF_ATTEST_CHECK = "CF attest"
CI_GATE_CHECK = "CI Gate"
ADVISORY_MARKER = "advisory"
GREEN_CONCLUSIONS = frozenset({"SUCCESS", "NEUTRAL", "SKIPPED"})
PENDING_STATES = frozenset({"", "EXPECTED", "IN_PROGRESS", "PENDING", "QUEUED", "REQUESTED", "STALE", "WAITING"})
SHA_RE = re.compile(r"[0-9a-f]{40}", re.IGNORECASE)
DEFAULT_GH_TIMEOUT = 60
ACTION_RUN_ID_RE = re.compile(r"/actions/runs/(?P<run_id>[1-9][0-9]*)(?:/job/[1-9][0-9]*)?/?$")


@dataclass(frozen=True)
class ArmDecision:
    """A deterministic disposition for one pull request."""

    should_arm: bool
    reason: str
    number: int | None = None
    head_sha: str = ""


@dataclass(frozen=True)
class RetryDecision:
    """A deterministic disposition for a one-time stale CF-attest retry."""

    should_rerun: bool
    reason: str
    number: int | None = None
    run_id: int | None = None
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
    return (
        len(matching) == 1
        and _check_outcome(matching[0]) == "green"
        and str(matching[0].get("conclusion") or matching[0].get("state") or "").strip().upper() == "SUCCESS"
    )


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


def _action_run_id(check: Mapping[str, Any]) -> int | None:
    """Extract an Actions run id from GitHub's check details URL."""

    details_url = check.get("detailsUrl")
    if not isinstance(details_url, str):
        return None
    match = ACTION_RUN_ID_RE.search(details_url)
    return int(match.group("run_id")) if match is not None else None


def _retry_candidate(pr: Mapping[str, Any]) -> RetryDecision:
    """Identify the one safe failed-CF shape that may be retried.

    ``CI Gate`` is permitted to be failed only when it belongs to the exact
    same Actions run: it necessarily aggregates a failed ``CF attest`` job.
    All independent checks remain strict green requirements.
    """

    arm_decision = decide_auto_arm(pr)
    if arm_decision.should_arm:
        return RetryDecision(False, "already_green", arm_decision.number, head_sha=arm_decision.head_sha)
    if arm_decision.reason != "cf_attest_not_green_at_head":
        return RetryDecision(False, arm_decision.reason, arm_decision.number)

    number = arm_decision.number
    assert number is not None
    head_sha = pr.get("headRefOid")
    assert isinstance(head_sha, str)
    head_sha = head_sha.casefold()
    latest, error = decide_latest_checks(pr.get("statusCheckRollup"))
    if latest is None:
        return RetryDecision(False, error or "checks_unavailable", number)
    current_checks = list(latest.values())
    cf_checks = [check for check in current_checks if _check_name(check) == CF_ATTEST_CHECK]
    if len(cf_checks) != 1:
        return RetryDecision(False, "cf_attest_ambiguous", number)
    cf_check = cf_checks[0]
    if (
        str(cf_check.get("status") or "").strip().upper() != "COMPLETED"
        or str(cf_check.get("conclusion") or "").strip().upper() != "FAILURE"
    ):
        return RetryDecision(False, "cf_attest_not_completed_failure", number)
    if _parse_timestamp(cf_check.get("startedAt")) is None:
        return RetryDecision(False, "cf_attest_started_at_unavailable", number)
    run_id = _action_run_id(cf_check)
    if run_id is None:
        return RetryDecision(False, "cf_attest_run_unavailable", number)

    for check in current_checks:
        name = _check_name(check)
        assert name is not None
        if name == CF_ATTEST_CHECK or ADVISORY_MARKER in name.casefold():
            continue
        outcome = _check_outcome(check)
        if name == CI_GATE_CHECK and outcome == "failing" and _action_run_id(check) == run_id:
            continue
        if outcome != "green":
            return RetryDecision(False, f"blocking_check_not_green:{name}", number)

    return RetryDecision(True, "failed_cf_attest_needs_exact_head_attestation", number, run_id, head_sha)


def _has_fresh_exact_head_attestation(
    comments: Sequence[Mapping[str, Any]], *, head_sha: str, failed_run_started_at: datetime
) -> bool:
    """Accept only a CF parser-valid APPROVE created after the failed run."""

    for comment in comments:
        body = comment.get("body")
        created_at = _parse_timestamp(comment.get("created_at"))
        if not isinstance(body, str) or created_at is None or created_at <= failed_run_started_at:
            continue
        parsed = parse_attestation(body)
        if parsed is not None and parsed.verdict == "APPROVE" and parsed.head_sha == head_sha.casefold():
            return True
    return False


def retry_stale_cf_attests(
    prs: Sequence[Mapping[str, Any]],
    *,
    get_run: Callable[[int], Mapping[str, Any]],
    get_comments: Callable[[int], Sequence[Mapping[str, Any]]],
    rerun: Callable[[int], None],
) -> list[RetryDecision]:
    """Rerun failed CF-attest workflow jobs exactly once after a fresh CF comment.

    GitHub exposes ``run_attempt`` on the workflow run, which provides durable
    idempotency per run/head without adding a mutable PR comment protocol.
    """

    decisions: list[RetryDecision] = []
    for pr in prs:
        candidate = _retry_candidate(pr)
        if not candidate.should_rerun:
            decisions.append(candidate)
            continue
        assert candidate.number is not None
        assert candidate.run_id is not None
        assert candidate.head_sha
        run = get_run(candidate.run_id)
        if (
            run.get("run_attempt") != 1
            or str(run.get("head_sha") or "").casefold() != candidate.head_sha
            or str(run.get("status") or "").upper() != "COMPLETED"
            or str(run.get("conclusion") or "").upper() != "FAILURE"
        ):
            decisions.append(
                RetryDecision(
                    False,
                    "cf_attest_run_not_initial_failed_head",
                    candidate.number,
                    candidate.run_id,
                    candidate.head_sha,
                )
            )
            continue
        latest, _error = decide_latest_checks(pr.get("statusCheckRollup"))
        assert latest is not None
        cf_check = next(check for check in latest.values() if _check_name(check) == CF_ATTEST_CHECK)
        failed_run_started_at = _parse_timestamp(cf_check.get("startedAt"))
        assert failed_run_started_at is not None
        if not _has_fresh_exact_head_attestation(
            get_comments(candidate.number),
            head_sha=candidate.head_sha,
            failed_run_started_at=failed_run_started_at,
        ):
            decisions.append(
                RetryDecision(
                    False,
                    "exact_head_attestation_missing_or_stale",
                    candidate.number,
                    candidate.run_id,
                    candidate.head_sha,
                )
            )
            continue
        rerun(candidate.run_id)
        decisions.append(
            RetryDecision(
                True,
                "reran_failed_cf_attest_after_exact_head_attestation",
                candidate.number,
                candidate.run_id,
                candidate.head_sha,
            )
        )
    return decisions


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


PR_JSON_FIELDS = "number,state,baseRefName,isDraft,labels,headRefOid,autoMergeRequest,statusCheckRollup"


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


def get_workflow_run(repo: str, run_id: int, *, token: str) -> Mapping[str, Any]:
    payload = _gh_json(["api", f"repos/{repo}/actions/runs/{run_id}"], token=token)
    if not isinstance(payload, Mapping):
        raise RuntimeError("workflow run response is not an object")
    return payload


def list_pr_comments(repo: str, number: int, *, token: str) -> list[Mapping[str, Any]]:
    payload = _gh_json(
        [
            "api",
            "--paginate",
            "--slurp",
            f"repos/{repo}/issues/{number}/comments?per_page=100",
        ],
        token=token,
    )
    if not isinstance(payload, list) or not all(isinstance(page, list) for page in payload):
        raise RuntimeError("PR comments response is not a list of pages")
    comments = [item for page in payload for item in page]
    if not all(isinstance(item, Mapping) for item in comments):
        raise RuntimeError("PR comments response contains a non-object")
    return comments


def rerun_failed_jobs(repo: str, run_id: int, *, token: str) -> None:
    completed = _gh(["run", "rerun", str(run_id), "--repo", repo, "--failed"], token=token)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise RuntimeError(detail or f"failed to rerun failed jobs for Actions run {run_id}")


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

    prs = list_open_prs(args.repo, token=token)
    retry_decisions = retry_stale_cf_attests(
        prs,
        get_run=lambda run_id: get_workflow_run(args.repo, run_id, token=token),
        get_comments=lambda number: list_pr_comments(args.repo, number, token=token),
        rerun=lambda run_id: rerun_failed_jobs(args.repo, run_id, token=token),
    )
    decisions = arm_eligible_prs(
        prs,
        enable=lambda number, head_sha: enable_auto_merge(args.repo, number, head_sha, token=token),
        comment=lambda number, head_sha: post_audit_comment(args.repo, number, head_sha, token=token),
    )
    for decision in retry_decisions:
        if decision.should_rerun:
            print(json.dumps({"number": decision.number, "reason": decision.reason, "rerun": True}))
    for decision in decisions:
        if decision.reason == "already_armed_or_queued":
            continue
        print(json.dumps({"number": decision.number, "reason": decision.reason, "armed": decision.should_arm}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
