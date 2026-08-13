#!/usr/bin/env python3
"""Arm auto-merge for abandoned, reviewed PRs in the integration sweep.

The scheduled GitHub Actions workflow is the sole non-interactive owner of
this safety net (#5029). A candidate must be unassigned and unchanged for an
hour, have a current-head approval, satisfy every required branch check, and
resolve through a fresh, unambiguous issue-stream audit. Every unavailable or
malformed input is a refusal, never evidence that a PR is ready.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from scripts.orchestration import issue_stream_audit

IDLE_THRESHOLD = timedelta(hours=1)
# Documented sole required status check (.github/workflows/README.md). Never read
# GET /repos/.../branches/.../protection — that endpoint needs administration,
# which GITHUB_TOKEN cannot grant (#6717).
DOCUMENTED_REQUIRED_CHECK_CONTEXTS = ("CI Gate",)
_REFS_LINE = re.compile(r"(?im)^\s*(?:[-*]\s*)?refs?\s*:?\s*#([1-9][0-9]*)\b")
_FORMAL_REVIEW_HEADING = re.compile(r"(?im)^#{1,6}\s+cross-family review\b")
_FORMAL_REVIEW_HEAD = re.compile(r"(?im)^\s*\*{0,2}head:\*{0,2}\s*`?([0-9a-f]{40})`?\s*$")
_FORMAL_REVIEWER_FAMILY = re.compile(r"(?im)^\s*\*{0,2}reviewer family:\*{0,2}\s*\S+")
_FORMAL_APPROVED = re.compile(r"(?im)\bverdict\s*:\s*approved\b")
_SUCCESSFUL_CONCLUSIONS = frozenset({"SUCCESS", "NEUTRAL", "SKIPPED"})
Runner = Callable[[list[str]], str]


@dataclass(frozen=True)
class Decision:
    """One PR's deterministic integration-sweep disposition."""

    number: int
    eligible: bool
    reason: str


class SweepError(RuntimeError):
    """An unavailable authoritative GitHub input that must stop the sweep."""


def _is_github_http_403(message: str) -> bool:
    """True when gh/API refused with the classic integration permission hole."""

    return "HTTP 403" in message or "Resource not accessible by integration" in message


def _is_schedule_event() -> bool:
    """True for Actions ``schedule`` runs (workflow sets EVENT_NAME / GITHUB_EVENT_NAME)."""

    return any(os.environ.get(key) == "schedule" for key in ("EVENT_NAME", "GITHUB_EVENT_NAME"))


def _parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(UTC)


def _pr_number(pr: Mapping[str, Any]) -> int | None:
    number = pr.get("number")
    return number if isinstance(number, int) and not isinstance(number, bool) and number > 0 else None


def referenced_issue_numbers(pr: Mapping[str, Any]) -> tuple[set[int] | None, str | None]:
    """Return explicit issue references or a fail-closed reason.

    GitHub exposes closing references separately. Non-closing membership is
    deliberately limited to documented ``Refs #N`` lines, so incidental issue
    numbers in prose, commands, or release notes cannot silently acquire a
    stream owner.
    """

    closing = pr.get("closingIssuesReferences")
    if not isinstance(closing, list):
        return None, "closing_references_unavailable"
    numbers: set[int] = set()
    for reference in closing:
        number = reference.get("number") if isinstance(reference, Mapping) else None
        if not isinstance(number, int) or isinstance(number, bool) or number < 1:
            return None, "invalid_closing_reference"
        numbers.add(number)
    body = pr.get("body")
    if not isinstance(body, str):
        return None, "body_unavailable"
    numbers.update(int(match) for match in _REFS_LINE.findall(body))
    if not numbers:
        return None, "no_explicit_issue_reference"
    return numbers, None


def resolve_stream_epic(
    pr: Mapping[str, Any], membership_report: Mapping[str, Any] | None
) -> tuple[int | None, str | None]:
    """Resolve every explicit PR issue to one exact stream epic, or refuse."""

    report = issue_stream_audit.validate_membership_report(membership_report, max_age_s=3600)
    if report is None:
        return None, "membership_audit_unavailable"
    numbers, reason = referenced_issue_numbers(pr)
    if numbers is None:
        return None, reason
    index = report.get("effective_membership")
    if not isinstance(index, Mapping):
        return None, "membership_index_unavailable"
    epics: set[int] = set()
    for number in numbers:
        entry = index.get(str(number))
        if not isinstance(entry, Mapping) or entry.get("unique_stream") is not True:
            return None, "ambiguous_membership"
        entry_epics = entry.get("epics")
        if not isinstance(entry_epics, list) or len(entry_epics) != 1:
            return None, "ambiguous_membership"
        epic = entry_epics[0]
        if not isinstance(epic, int) or isinstance(epic, bool) or epic < 1:
            return None, "ambiguous_membership"
        epics.add(epic)
    if len(epics) != 1:
        return None, "conflicting_membership"
    return epics.pop(), None


def _has_current_head_approval(pr: Mapping[str, Any]) -> bool:
    head_sha = pr.get("headRefOid")
    reviews = pr.get("reviews")
    if not isinstance(head_sha, str) or not head_sha or not isinstance(reviews, list):
        return False
    for review in reviews:
        if not isinstance(review, Mapping) or str(review.get("state") or "").upper() != "APPROVED":
            continue
        commit = review.get("commit")
        commit_sha = commit.get("oid") if isinstance(commit, Mapping) else commit
        if commit_sha == head_sha:
            return True
    return False


def _has_current_head_formal_review(comments: Sequence[Mapping[str, Any]] | None, head_sha: object) -> bool:
    """Accept only the direct-review comment format with an exact head proof."""

    if not isinstance(comments, Sequence) or isinstance(comments, (str, bytes)):
        return False
    if not isinstance(head_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", head_sha):
        return False
    for comment in comments:
        body = comment.get("body") if isinstance(comment, Mapping) else None
        if not isinstance(body, str):
            continue
        head = _FORMAL_REVIEW_HEAD.search(body)
        if (
            _FORMAL_REVIEW_HEADING.search(body)
            and _FORMAL_REVIEWER_FAMILY.search(body)
            and _FORMAL_APPROVED.search(body)
            and head is not None
            and head.group(1).lower() == head_sha.lower()
        ):
            return True
    return False


def _latest_check(checks: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    dated: list[tuple[datetime, Mapping[str, Any]]] = []
    for check in checks:
        timestamp = _parse_timestamp(check.get("startedAt")) or _parse_timestamp(check.get("completedAt"))
        if timestamp is None:
            return None
        dated.append((timestamp, check))
    return max(dated, key=lambda pair: pair[0])[1] if dated else None


def required_checks_green(pr: Mapping[str, Any], required_contexts: Sequence[str]) -> bool:
    """Require the latest instance of every protected context to be green."""

    rollup = pr.get("statusCheckRollup")
    if not isinstance(rollup, list) or not required_contexts:
        return False
    grouped: dict[str, list[Mapping[str, Any]]] = {context: [] for context in required_contexts}
    for raw in rollup:
        if not isinstance(raw, Mapping):
            continue
        name = raw.get("name") or raw.get("context")
        if isinstance(name, str) and name in grouped:
            grouped[name].append(raw)
    for context in required_contexts:
        latest = _latest_check(grouped[context])
        if latest is None or str(latest.get("status") or "").upper() != "COMPLETED":
            return False
        outcome = str(latest.get("conclusion") or latest.get("state") or "").upper()
        if outcome not in _SUCCESSFUL_CONCLUSIONS:
            return False
    return True


def decide(
    pr: Mapping[str, Any],
    membership_report: Mapping[str, Any] | None,
    required_contexts: Sequence[str],
    *,
    now: datetime,
    comments: Sequence[Mapping[str, Any]] | None = None,
) -> Decision:
    """Return whether a PR can safely receive an auto-merge request."""

    number = _pr_number(pr)
    if number is None:
        return Decision(0, False, "invalid_pr_number")
    if pr.get("isDraft") is True:
        return Decision(number, False, "draft")
    if pr.get("autoMergeRequest"):
        return Decision(number, False, "auto_merge_already_enabled")
    assignees = pr.get("assignees")
    if not isinstance(assignees, list):
        return Decision(number, False, "assignees_unavailable")
    if assignees:
        return Decision(number, False, "active_owner_assigned")
    updated_at = _parse_timestamp(pr.get("updatedAt"))
    if updated_at is None:
        return Decision(number, False, "updated_at_unavailable")
    if now - updated_at <= IDLE_THRESHOLD:
        return Decision(number, False, "not_idle_for_one_hour")
    if not required_checks_green(pr, required_contexts):
        return Decision(number, False, "required_ci_not_green")
    epic, reason = resolve_stream_epic(pr, membership_report)
    if epic is None:
        return Decision(number, False, reason or "membership_unavailable")
    native_approval = str(pr.get("reviewDecision") or "").upper() == "APPROVED" and _has_current_head_approval(pr)
    if not native_approval and not _has_current_head_formal_review(comments, pr.get("headRefOid")):
        return Decision(number, False, "current_head_review_missing")
    return Decision(number, True, f"stream_epic_{epic}")


class GitHubAdapter:
    """Thin GitHub CLI adapter; mutations remain explicit in ``arm_auto_merge``."""

    def __init__(self, repo_root: Path, *, runner: Runner | None = None) -> None:
        self.repo_root = repo_root.resolve()
        self._runner = runner or self._default_runner

    def _default_runner(self, args: list[str]) -> str:
        completed = subprocess.run(args, cwd=self.repo_root, text=True, capture_output=True, check=False)
        if completed.returncode != 0:
            message = (completed.stderr or completed.stdout or "GitHub command failed").strip()
            raise SweepError(message[:1000])
        return completed.stdout

    def _json(self, args: list[str]) -> Any:
        try:
            return json.loads(self._runner(args) or "null")
        except json.JSONDecodeError as exc:
            raise SweepError("GitHub command returned invalid JSON") from exc

    def list_open_prs(self, repository: str) -> list[dict[str, Any]]:
        payload = self._json(
            [
                "gh",
                "pr",
                "list",
                "--repo",
                repository,
                "--state",
                "open",
                "--limit",
                "1000",
                "--json",
                "number,isDraft,updatedAt,reviewDecision,reviews,autoMergeRequest,assignees,headRefOid,"
                "statusCheckRollup,body,closingIssuesReferences",
            ]
        )
        if not isinstance(payload, list) or not all(isinstance(item, dict) for item in payload):
            raise SweepError("open PR response is not a list of objects")
        return payload

    def required_check_contexts(self, repository: str, branch: str = "main") -> list[str]:
        """Return required check names without the admin-only protection API.

        Prefer GraphQL / PR rollup ``isRequired`` when the token can read checks;
        otherwise fail closed to the documented sole required context ``CI Gate``.
        Never call ``GET /repos/.../branches/.../protection`` (#6717).
        """

        del branch  # retained for call-site compatibility
        try:
            discovered = self._required_contexts_from_pr_rollup(repository)
        except SweepError as exc:
            if _is_github_http_403(str(exc)):
                # Token cannot read check metadata — documented default, not a crash.
                return list(DOCUMENTED_REQUIRED_CHECK_CONTEXTS)
            raise
        if discovered:
            return discovered
        return list(DOCUMENTED_REQUIRED_CHECK_CONTEXTS)

    def _required_contexts_from_pr_rollup(self, repository: str) -> list[str]:
        """Collect ``isRequired`` check names from open PR status rollups via GraphQL."""

        owner, _, name = repository.partition("/")
        if not owner or not name:
            raise SweepError(f"invalid repository slug: {repository!r}")
        # Compact single-line query — same style as issue_stream_audit GraphQL calls.
        query = (
            "query($owner:String!,$name:String!){"
            "repository(owner:$owner,name:$name){"
            "pullRequests(first:20,states:OPEN){nodes{"
            "commits(last:1){nodes{commit{statusCheckRollup{"
            "contexts(first:100){nodes{"
            "__typename "
            "... on CheckRun{name isRequired} "
            "... on StatusContext{context isRequired}"
            "}}}}}}}}}}"
        )
        payload = self._json(
            [
                "gh",
                "api",
                "graphql",
                "-f",
                f"query={query}",
                "-F",
                f"owner={owner}",
                "-F",
                f"name={name}",
            ]
        )
        if not isinstance(payload, Mapping):
            return []
        errors = payload.get("errors")
        if isinstance(errors, list) and errors:
            messages = "; ".join(
                str(item.get("message") or item) for item in errors if isinstance(item, Mapping)
            )
            if _is_github_http_403(messages) or "Resource not accessible" in messages:
                raise SweepError(messages[:1000] or "GraphQL required-check lookup HTTP 403")
            # Non-permission GraphQL failures: fall through to documented default.
            return []
        data = payload.get("data")
        repository_node = data.get("repository") if isinstance(data, Mapping) else None
        if not isinstance(repository_node, Mapping):
            return []
        pull_requests = repository_node.get("pullRequests")
        nodes = pull_requests.get("nodes") if isinstance(pull_requests, Mapping) else None
        if not isinstance(nodes, list):
            return []
        required: list[str] = []
        seen: set[str] = set()
        for pr_node in nodes:
            if not isinstance(pr_node, Mapping):
                continue
            commits = pr_node.get("commits")
            commit_nodes = commits.get("nodes") if isinstance(commits, Mapping) else None
            if not isinstance(commit_nodes, list):
                continue
            for commit_node in commit_nodes:
                if not isinstance(commit_node, Mapping):
                    continue
                commit = commit_node.get("commit")
                rollup = commit.get("statusCheckRollup") if isinstance(commit, Mapping) else None
                contexts = rollup.get("contexts") if isinstance(rollup, Mapping) else None
                context_nodes = contexts.get("nodes") if isinstance(contexts, Mapping) else None
                if not isinstance(context_nodes, list):
                    continue
                for raw in context_nodes:
                    if not isinstance(raw, Mapping) or raw.get("isRequired") is not True:
                        continue
                    label = raw.get("name") or raw.get("context")
                    if isinstance(label, str) and label and label not in seen:
                        seen.add(label)
                        required.append(label)
        return required

    def comments(self, repository: str, number: int) -> list[dict[str, Any]]:
        payload = self._json(["gh", "api", f"repos/{repository}/issues/{number}/comments", "--paginate"])
        if not isinstance(payload, list) or not all(isinstance(item, dict) for item in payload):
            raise SweepError("PR comments response is not a list of objects")
        return payload

    def arm_auto_merge(self, repository: str, number: int) -> None:
        self._runner(
            [
                "gh",
                "pr",
                "merge",
                str(number),
                "--repo",
                repository,
                "--auto",
                "--squash",
                "--delete-branch",
            ]
        )


def run(
    adapter: GitHubAdapter,
    repository: str,
    *,
    apply: bool,
    now: datetime | None = None,
) -> list[Decision]:
    """Observe every open PR once and optionally arm eligible candidates."""

    observation_time = now or datetime.now(UTC)
    try:
        report = issue_stream_audit.run_audit(adapter.repo_root)
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
        raise SweepError(f"issue-stream audit unavailable: {exc}") from exc
    required_contexts = adapter.required_check_contexts(repository)
    decisions: list[Decision] = []
    for pr in adapter.list_open_prs(repository):
        decision = decide(pr, report, required_contexts, now=observation_time)
        if decision.reason == "current_head_review_missing":
            decision = decide(
                pr,
                report,
                required_contexts,
                now=observation_time,
                comments=adapter.comments(repository, decision.number),
            )
        decisions.append(decision)
    if apply:
        for decision in decisions:
            if decision.eligible:
                adapter.arm_auto_merge(repository, decision.number)
    return decisions


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="GitHub owner/repository")
    parser.add_argument("--apply", action="store_true", help="Arm eligible PRs; default is read-only.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    try:
        decisions = run(GitHubAdapter(args.repo_root), args.repo, apply=args.apply)
    except SweepError as exc:
        message = str(exc)
        # Scheduled runs must not paint main red for GITHUB_TOKEN permission holes
        # (e.g. residual required-context lookup 403). Logic bugs still exit 1.
        if _is_github_http_403(message) and _is_schedule_event():
            print(f"integration sweep skipped: {message}")
            return 0
        print(f"integration sweep refused: {exc}")
        return 1
    print(json.dumps([decision.__dict__ for decision in decisions], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
