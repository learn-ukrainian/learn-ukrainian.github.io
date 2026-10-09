#!/usr/bin/env python
"""Observe, validate, and explicitly close out a task lifecycle ledger.

Read-only reconciliation is the default.  Remote changes require the ``mutate``
subcommand, an exact action, ``--authorize``, and an actor recorded in the
append-only mutation receipt.

Membership-reliant writes require a bounded live, repository-qualified ancestry
read to the claimed registered root (#9794). GitHub has no parentage compare-and-
swap: a re-parent after the final read and before the write remains a read/write
race residual owned by claude-infra.

An explicitly parentless target may instead use complete, exact body membership
from the same invocation's live audit. These reads are fresh observations, not
an atomic snapshot: the audit reads checklists across requests and timestamps
the assembled report afterward. Observed contradictions are refused; unobserved
checklist edits during traversal or between supporting reads and the write remain
a concurrency residual owned by claude-infra, alongside the native-parent race.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Callable, Mapping
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.github_check_rollup import collapse_status_rollup
from scripts.opsec.prepublish import publication_boundary, publication_cli
from scripts.orchestration import task_identity, task_lifecycle
from scripts.publish.github import Request, request_run

Runner = Callable[[list[str], str | None], str]


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_root_from_file() -> Path:
    return Path(__file__).resolve().parents[2]


def _json_file(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise task_lifecycle.LifecycleError(f"cannot read JSON file {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise task_lifecycle.LifecycleError(f"JSON file must contain an object: {path}")
    return value


DEFAULT_COMMAND_TIMEOUT_SECONDS = 60.0


def _default_runner(repo_root: Path) -> Runner:
    @publication_boundary(task_lifecycle.LifecycleError)
    def run(args: list[str], stdin: str | None = None) -> str:
        try:
            completed = request_run(
                args,
                cwd=repo_root,
                input=stdin,
                capture_output=True,
                text=True,
                check=False,
                timeout=DEFAULT_COMMAND_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            raise task_lifecycle.LifecycleError(
                f"{args.verb if isinstance(args, Request) else ' '.join(args[:4])} timed out after {DEFAULT_COMMAND_TIMEOUT_SECONDS}s"
            ) from exc
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "command failed").strip()
            raise task_lifecycle.LifecycleError(
                f"{args.verb if isinstance(args, Request) else ' '.join(args[:4])} failed: {detail[:1000]}"
            )
        return completed.stdout

    return run


_TERMINAL_CONCLUSIONS = frozenset(
    {
        "SUCCESS",
        "FAILURE",
        "ERROR",
        "CANCELLED",
        "NEUTRAL",
        "SKIPPED",
        "TIMED_OUT",
        "ACTION_REQUIRED",
        "STALE",
    }
)
_CHECK_IDENTITY_FIELDS = (
    "workflowName",
    "appSlug",
    "startedAt",
    "completedAt",
    "createdAt",
    "updatedAt",
    "context",
)


def project_closeout_checks(rollup: list[Any]) -> list[Any]:
    """Keep workflow and timestamps, then the latest row of each check identity.

    Collapse runs on the raw rollup so a status context stays a status context.
    Copying ``context`` into ``name`` first would hide ``updatedAt`` from the
    shared timestamp helper.
    """
    checks: list[dict[str, Any]] = []
    for raw in collapse_status_rollup(list(rollup)):
        if not isinstance(raw, dict):
            checks.append(raw)
            continue
        typename = raw.get("__typename")
        if typename == "CheckRun" or (not typename and raw.get("name") and not raw.get("context")):
            conclusion = str(raw.get("conclusion") or "").upper()
            status = str(raw.get("status") or "").upper()
            if not status and conclusion in _TERMINAL_CONCLUSIONS:
                status = "COMPLETED"
            row = {
                "name": raw.get("name"),
                "status": status,
                "conclusion": conclusion,
                "url": raw.get("detailsUrl"),
            }
        else:
            state = str(raw.get("state") or raw.get("conclusion") or "").upper()
            row = {
                "name": raw.get("context") or raw.get("name"),
                "status": "COMPLETED" if state in _TERMINAL_CONCLUSIONS else "IN_PROGRESS",
                "conclusion": state,
                "url": raw.get("targetUrl") or raw.get("detailsUrl"),
            }
        for field in _CHECK_IDENTITY_FIELDS:
            value = raw.get(field)
            if isinstance(value, str) and value.strip():
                row[field] = value
        checks.append(row)
    return checks


class GhGitHubAdapter:
    """Authoritative GitHub reads and the three explicitly allowed mutations."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root.resolve()
        self._run = _default_runner(self.repo_root)

    def _json(self, args: list[str], stdin: str | None = None) -> Any:
        raw = self._run(args, stdin)
        try:
            return json.loads(raw or "null")
        except json.JSONDecodeError as exc:
            raise task_lifecycle.LifecycleError(
                f"GitHub command returned invalid JSON: {args.verb if isinstance(args, Request) else ' '.join(args[:4])}"
            ) from exc

    def registered_stream_epics(self, repository: str | None = None) -> list[int]:
        """Use the checkout's registry only for its resolved repository.

        Init and every mutation observation pass the task identity here, so
        both native ancestry and body fallback consume a bound registry.
        Read-only registry inspection may omit the identity.
        """
        if repository is not None:
            document = self._json(["gh", "repo", "view", "--json", "nameWithOwner"])
            failure = task_lifecycle.repository_evidence_refusal(
                repository, document.get("nameWithOwner") if isinstance(document, dict) else None,
                source="issue-stream registry",
            )
            if failure is not None:
                raise task_lifecycle.LifecycleError(failure)
        try:
            from scripts.orchestration import issue_stream_audit

            registry = issue_stream_audit.load_registry(
                self.repo_root / "scripts" / "config" / "issue_streams.yaml"
            )
        except (OSError, ValueError) as exc:
            raise task_lifecycle.LifecycleError(
                f"cannot load the issue-stream registry: {exc}"
            ) from exc
        return sorted({epic for epics in registry.values() for epic in epics})

    def membership_audit_report(self) -> dict[str, Any]:
        """One fresh, live issue-stream membership audit snapshot.

        Feeds :func:`task_lifecycle.resolve_membership` for the canonical
        native-or-unique-body proof. Callers that need membership for more
        than one issue in a single observation (the lifecycle issue and a
        transferred-scope follow-up issue) must call this ONCE and carry the
        same snapshot through both resolutions rather than re-auditing.

        Scoped to ``self.repo_root`` — never the auditor module's own
        checkout — so a closeout invocation configured for another
        checkout/worktree audits and caches against the SAME repository it is
        validating membership for.
        """
        from scripts.orchestration import issue_stream_audit

        try:
            return issue_stream_audit.run_audit(self.repo_root)
        except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.TimeoutExpired) as exc:
            raise task_lifecycle.LifecycleError(
                f"cannot run the issue-stream membership audit: {exc}"
            ) from exc

    def read_issue_parent(self, repository: str, issue_number: int) -> dict[str, Any] | None:
        """Read a typed, repository-qualified parent; refuse partial/unread data."""
        document = self._json(Request("read-issue-parent", repo=repository, number=issue_number))
        if not isinstance(document, dict) or document.get("errors"):
            raise task_lifecycle.LifecycleError("GitHub parent read failed")
        data = document.get("data")
        repository_doc = data.get("repository") if isinstance(data, dict) else None
        if not isinstance(repository_doc, dict):
            raise task_lifecycle.LifecycleError("GitHub parent repository is unread")
        observed_repository = repository_doc.get("nameWithOwner")
        if (
            not task_lifecycle.repository_identity_valid(observed_repository)
            or observed_repository.casefold() != repository.casefold()
        ):
            raise task_lifecycle.LifecycleError("GitHub parent read repository does not match")
        issue = repository_doc.get("issue")
        if (
            not isinstance(issue, dict)
            or not isinstance(issue.get("number"), int)
            or isinstance(issue["number"], bool)
            or issue["number"] != issue_number
            or "parent" not in issue
        ):
            raise task_lifecycle.LifecycleError("GitHub parent issue is unread or malformed")
        parent = issue["parent"]
        if parent is None:
            return None
        parent_repository = parent.get("repository") if isinstance(parent, dict) else None
        slug = parent_repository.get("nameWithOwner") if isinstance(parent_repository, dict) else None
        number = parent.get("number") if isinstance(parent, dict) else None
        if (
            not task_lifecycle.repository_identity_valid(slug)
            or not isinstance(number, int) or isinstance(number, bool) or number < 1
        ):
            raise task_lifecycle.LifecycleError("GitHub parent identity is malformed")
        return {"number": number, "repository": slug}

    def read_issue(self, repository: str, issue_number: int) -> dict[str, Any]:
        issue = self._json(
            [
                "gh",
                "issue",
                "view",
                str(issue_number),
                "--repo",
                repository,
                "--json",
                "number,state,body,url,closedAt",
            ]
        )
        parent = self.read_issue_parent(repository, issue_number) or {}
        return {
            "number": issue.get("number"),
            "state": str(issue.get("state") or "").upper(),
            "body": issue.get("body") or "",
            "url": issue.get("url"),
            "closed_at": issue.get("closedAt"),
            "parent_epic": parent.get("number"),
            "parent_repository": parent.get("repository"),
        }

    def _read_pr(self, repository: str, pr_number: int) -> dict[str, Any]:
        pr = self._json(
            [
                "gh",
                "pr",
                "view",
                str(pr_number),
                "--repo",
                repository,
                "--json",
                "number,url,state,isDraft,headRefOid,headRefName,mergeCommit,mergedAt,"
                "autoMergeRequest,reviewDecision,reviews,statusCheckRollup,body,"
                "closingIssuesReferences",
            ]
        )
        checks = project_closeout_checks(pr.get("statusCheckRollup") or [])
        auto = pr.get("autoMergeRequest") or {}
        merge_commit = pr.get("mergeCommit") or {}
        closing_references = pr.get("closingIssuesReferences")
        if not isinstance(closing_references, list):
            raise task_lifecycle.LifecycleError("GitHub PR closing-reference response is not a list")
        closing_issue_numbers: list[int] = []
        for reference in closing_references:
            number = reference.get("number") if isinstance(reference, dict) else None
            if not isinstance(number, int) or number < 1:
                raise task_lifecycle.LifecycleError("GitHub PR closing reference lacks a valid issue number")
            closing_issue_numbers.append(number)
        return {
            "number": pr.get("number"),
            "url": pr.get("url"),
            "state": str(pr.get("state") or "").upper(),
            "is_draft": bool(pr.get("isDraft")),
            "head_sha": pr.get("headRefOid"),
            "head_branch": pr.get("headRefName"),
            "merge_sha": merge_commit.get("oid"),
            "merged_at": pr.get("mergedAt"),
            "auto_merge_enabled_at": auto.get("enabledAt"),
            "review_decision": pr.get("reviewDecision"),
            "requested_changes": pr.get("reviewDecision") == "CHANGES_REQUESTED",
            "reviews": pr.get("reviews") or [],
            "checks": checks,
            "body": pr.get("body") or "",
            "closing_issue_numbers": sorted(set(closing_issue_numbers)),
        }

    def _comments(self, repository: str, pr_number: int) -> list[dict[str, Any]]:
        issue_comments = self._json(Request("read-comments", repo=repository, number=pr_number, paginate=True))
        native_reviews = self._json(Request("read-reviews", repo=repository, number=pr_number, paginate=True))
        if not isinstance(issue_comments, list) or not isinstance(native_reviews, list):
            raise task_lifecycle.LifecycleError("GitHub PR comments response is not a list")
        comments = [
            {
                "url": item.get("html_url"),
                "body": item.get("body") or "",
                "author": (item.get("user") or {}).get("login"),
                "created_at": item.get("created_at"),
                "kind": "issue_comment",
            }
            for item in issue_comments
            if isinstance(item, dict)
        ]
        comments.extend(
            {
                "url": item.get("html_url"),
                "body": item.get("body") or "",
                "author": (item.get("user") or {}).get("login"),
                "created_at": item.get("submitted_at"),
                "kind": "pull_request_review",
                "state": str(item.get("state") or "").upper(),
                "commit_id": item.get("commit_id"),
            }
            for item in native_reviews
            if isinstance(item, dict)
        )
        return comments

    def _deployments(self, repository: str, sha: str | None) -> list[dict[str, Any]]:
        if not sha:
            return []
        deployments = self._json(Request("read-deployments", repo=repository, sha=sha))
        result: list[dict[str, Any]] = []
        for deployment in deployments or []:
            deployment_id = deployment.get("id")
            statuses = self._json(Request("read-deployment-statuses", repo=repository, number=deployment_id))
            latest = statuses[0] if statuses else {}
            result.append(
                {
                    "id": deployment_id,
                    "environment": deployment.get("environment"),
                    "sha": deployment.get("sha"),
                    "state": str(latest.get("state") or "").upper(),
                    "url": latest.get("target_url") or latest.get("environment_url"),
                }
            )
        return result

    def _follow_up(
        self,
        repository: str,
        original_issue: int,
        original_body: str,
        remaining_scope: Mapping[str, Any],
    ) -> dict[str, Any] | None:
        follow_up_number = remaining_scope.get("follow_up_issue")
        if remaining_scope.get("status") != "transferred" or not follow_up_number:
            return None
        follow_up = self.read_issue(repository, int(follow_up_number))
        original_ref = f"#{original_issue}"
        follow_up_ref = f"#{follow_up_number}"
        follow_up["reciprocal_links_verified"] = (
            follow_up_ref in original_body and original_ref in str(follow_up.get("body") or "")
        )
        return follow_up

    def _github_observation(self, ledger: Mapping[str, Any]) -> dict[str, Any]:
        identity = ledger["identity"]
        repository = identity["repository"]
        issue = self.read_issue(repository, identity["github_issue_number"])
        follow_up = self._follow_up(
            repository,
            identity["github_issue_number"],
            issue["body"],
            ledger["remaining_scope"],
        )
        # A native parent that is a registered stream epic is conclusive on
        # its own (even when mismatched) and never needs a live audit. A
        # missing native parent (body path) or an unregistered native parent
        # (native-chain path, #9783) — on the lifecycle issue itself or on the
        # transferred-scope follow-up read above — can only be decided by the
        # live membership snapshot, so only those cases fetch it.
        registered_epics = self.registered_stream_epics(repository)
        needs_membership_audit = task_lifecycle.membership_needs_audit(
            issue.get("parent_epic"), registered_epics
        ) or (
            follow_up is not None
            and task_lifecycle.membership_needs_audit(follow_up.get("parent_epic"), registered_epics)
        )
        membership_audit = self.membership_audit_report() if needs_membership_audit else None
        pr_number = ledger["pr"]["number"]
        pr: dict[str, Any] = {
            "number": None,
            "url": None,
            "state": None,
            "is_draft": False,
            "head_sha": None,
            "head_branch": None,
            "merge_sha": None,
            "merged_at": None,
            "auto_merge_enabled_at": None,
            "review_decision": None,
            "requested_changes": False,
            "reviews": [],
            "checks": [],
            "body": "",
            "closing_issue_numbers": [],
        }
        comments: list[dict[str, Any]] = []
        deployments: list[dict[str, Any]] = []
        if pr_number is not None:
            pr = self._read_pr(repository, pr_number)
            comments = self._comments(repository, pr_number)
            if ledger["terminal_goal"] in {"deploy", "certify"}:
                deployments = self._deployments(repository, pr.get("merge_sha") or pr.get("head_sha"))
        return {
            "repository": repository,
            "registered_stream_epics": registered_epics,
            "membership_audit": membership_audit,
            "issue": issue,
            "pr": pr,
            "comments": comments,
            "deployments": deployments,
            "follow_up": follow_up,
        }

    def observe(
        self,
        ledger: Mapping[str, Any],
        *,
        now: str,
        branch: str | None = None,
        worktree: str | None = None,
    ) -> dict[str, Any]:
        canonical = task_lifecycle.validate_lifecycle(ledger)
        try:
            github = self._github_observation(canonical)
        except task_lifecycle.LifecycleError as exc:
            identity = canonical["identity"]
            github = {
                "repository": identity["repository"],
                "registered_stream_epics": [],
                "membership_audit": None,
                "issue": {
                    "number": identity["github_issue_number"],
                    "state": None,
                    "body": "",
                    "url": identity["github_issue_url"],
                    "closed_at": None,
                    "parent_epic": None,
                },
                "pr": {
                    "number": canonical["pr"]["number"],
                    "url": canonical["pr"]["url"],
                    "state": None,
                    "head_sha": None,
                    "head_branch": branch,
                    "merge_sha": None,
                    "checks": [],
                    "requested_changes": False,
                },
                "comments": [],
                "deployments": [],
                "follow_up": None,
                "error": str(exc),
            }
        pr = github["pr"]
        local = task_lifecycle.observe_local_git(
            self.repo_root,
            head_sha=pr.get("head_sha"),
            branch=branch or pr.get("head_branch"),
            worktree=worktree or str(self.repo_root),
        )
        return {
            "schema_version": task_lifecycle.OBSERVATION_SCHEMA_VERSION,
            "observed_at": now,
            "github": github,
            "local": local,
        }

    def update_issue_body(self, repository: str, issue_number: int, body: str) -> None:
        self._run(
            Request("issue-edit", repo=repository, number=issue_number, body=body),
            None,
        )

    def enqueue_pr(self, repository: str, pr_number: int) -> None:
        self._run(
            Request("pr-merge", number=int(str(pr_number)), repo=repository),
            None,
        )

    def close_issue(self, repository: str, issue_number: int) -> None:
        self._run(
            Request("issue-close", number=int(str(issue_number)), repo=repository, reason="completed"),
            None,
        )


class StaticObservationAdapter:
    """Hermetic injected observation adapter used by tests and offline replay."""

    def __init__(self, observation: Mapping[str, Any]) -> None:
        self.observation = deepcopy(dict(observation))

    def observe(self, _ledger: Mapping[str, Any], **_kwargs: Any) -> dict[str, Any]:
        return deepcopy(self.observation)


def evidenced_issue_body(ledger: Mapping[str, Any], observation: Mapping[str, Any]) -> tuple[str, list[str]]:
    evaluation = task_lifecycle.evaluate(ledger, observation)
    valid = {key: set(value) for key, value in evaluation["valid_evidence"].items()}
    body = str(observation["github"]["issue"].get("body") or "")
    checked_ids: list[str] = []
    for criterion in ledger["ac_snapshot"]["criteria"]:
        if not criterion["applicable"]:
            continue
        if set(criterion["required_evidence"]).issubset(valid.get(criterion["id"], set())):
            body = task_lifecycle.check_ac_checkbox(body, criterion["id"])
            checked_ids.append(criterion["id"])
    return body, checked_ids


def _desired_remote_state(
    action: str,
    ledger: Mapping[str, Any],
    observation: Mapping[str, Any],
) -> bool:
    issue = observation["github"]["issue"]
    pr = observation["github"]["pr"]
    if action == "close-issue":
        return str(issue.get("state") or "").upper() == "CLOSED"
    if action == "arm-auto-merge":
        return bool(pr.get("auto_merge_enabled_at")) or str(pr.get("state") or "").upper() == "MERGED"
    expected_body, _ = evidenced_issue_body(ledger, observation)
    return expected_body == issue.get("body")


def _assert_mutation_ready(
    action: str,
    ledger: Mapping[str, Any],
    observation: Mapping[str, Any],
) -> dict[str, Any]:
    evaluation = task_lifecycle.evaluate(ledger, observation)
    hard = evaluation["hard_blockers"]
    if action == "sync-acs":
        fatal_fragments = (
            "repository does not match",
            "issue does not match",
            "issue URL does not match",
            "stream epic",
            "acceptance criteria drift",
            "GitHub observation failed",
            "authoritative PR does not match",
        )
        fatal = [item for item in hard if any(fragment in item for fragment in fatal_fragments)]
        if fatal:
            raise task_lifecycle.LifecycleError("AC sync blocked: " + "; ".join(fatal))
    elif action == "arm-auto-merge":
        _assert_closing_references_match_disposition(ledger, observation)
        if hard:
            raise task_lifecycle.LifecycleError("auto-merge blocked: " + "; ".join(hard))
        if task_lifecycle.STATE_RANK.get(evaluation["last_success_state"], -1) < task_lifecycle.STATE_RANK[
            "REVIEW_PASSED"
        ]:
            raise task_lifecycle.LifecycleError("auto-merge requires verified current-head outside-family review")
        if str(observation["github"]["pr"].get("state") or "").upper() != "OPEN":
            raise task_lifecycle.LifecycleError("auto-merge requires an open PR")
        if observation["github"]["pr"].get("is_draft"):
            raise task_lifecycle.LifecycleError("auto-merge requires a ready-for-review PR")
    else:
        if hard:
            raise task_lifecycle.LifecycleError("issue close blocked: " + "; ".join(hard))
        if not evaluation["goal_reached"]:
            raise task_lifecycle.LifecycleError("issue close requires the terminal goal's authoritative remote state")
        if evaluation["preclose_missing_evidence"]:
            raise task_lifecycle.LifecycleError("issue close has missing pre-close AC evidence")
        if evaluation["preclose_unchecked"]:
            raise task_lifecycle.LifecycleError(
                "issue close requires evidenced AC checkboxes: "
                + ", ".join(evaluation["preclose_unchecked"])
            )
        if ledger["remaining_scope"]["status"] == "open":
            raise task_lifecycle.LifecycleError("issue close is blocked by untransferred remaining scope")
    return evaluation


def _assert_closing_references_match_disposition(
    ledger: Mapping[str, Any], observation: Mapping[str, Any]
) -> None:
    """Fail closed when GitHub closing references contradict retained scope."""

    raw_numbers = observation["github"]["pr"].get("closing_issue_numbers")
    if not isinstance(raw_numbers, list) or any(
        not isinstance(number, int) or number < 1 for number in raw_numbers
    ):
        raise task_lifecycle.LifecycleError("authoritative PR closing references are unavailable or malformed")
    closing_numbers = set(raw_numbers)
    remaining_scope = ledger["remaining_scope"]["status"]
    expected = (
        {int(ledger["identity"]["github_issue_number"])}
        if remaining_scope == "none"
        else set()
    )
    unexpected = sorted(closing_numbers - expected)
    if unexpected:
        rendered = ", ".join(f"#{number}" for number in unexpected)
        raise task_lifecycle.LifecycleError(
            "GitHub closing references contradict the declared remaining-scope disposition: "
            f"{rendered}"
        )


def _record_failed_mutation(
    state_file: Path,
    ledger: Mapping[str, Any],
    *,
    operation_id: str,
    action: str,
    authorized_by: str,
    requested_at: str,
    detail: str,
    remote_mutation_performed: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    blocked = deepcopy(dict(ledger))
    blocked["current_state"] = "BLOCKED_WITH_RECEIPT"
    blocked, receipt, _ = task_lifecycle.append_mutation_event(
        blocked,
        operation_id=operation_id,
        action=action,
        status="failed",
        authorized_by=authorized_by,
        requested_at=requested_at,
        completed_at=utc_now(),
        remote_mutation_performed=remote_mutation_performed,
        detail=detail,
    )
    task_lifecycle.write_lifecycle(state_file, blocked)
    return blocked, receipt


def record_unauthorized_mutation(
    state_file: Path,
    *,
    action: str,
    actor: str,
    now: str,
) -> dict[str, Any]:
    """Persist a fail-closed receipt without performing any remote read or write."""
    with task_lifecycle.lifecycle_lock(state_file):
        ledger = task_lifecycle.load_lifecycle(state_file)
        operation_id = task_lifecycle.mutation_operation_id(ledger, action)
        _, receipt = _record_failed_mutation(
            state_file,
            ledger,
            operation_id=operation_id,
            action=action,
            authorized_by=actor,
            requested_at=now,
            detail=(
                "remote mutation denied: explicit --authorize was absent; "
                "rerun the exact action with --authorize after reviewing its gate"
            ),
        )
        return {
            "action": action,
            "operation_id": operation_id,
            "disposition": "blocked",
            "state": "BLOCKED_WITH_RECEIPT",
            "mutation_receipt": receipt,
            "remote_mutation_performed": False,
        }


def _assert_live_memberships(
    adapter: GhGitHubAdapter,
    ledger: Mapping[str, Any],
    *,
    registered_epics: list[int] | None,
    membership_report: Mapping[str, Any] | None,
) -> None:
    """Revalidate all targets using this invocation's registry and live audit."""
    identity = ledger["identity"]
    targets = [(identity["github_issue_number"], identity["stream_epic"])]
    remaining = ledger["remaining_scope"]
    if remaining["status"] == "transferred":
        targets.append((remaining["follow_up_issue"], remaining["follow_up_stream_epic"]))
    for issue_number, epic in targets:
        membership = task_lifecycle.resolve_live_ancestry(
            repository=identity["repository"], issue_number=issue_number,
            stream_epic=epic, registered_epics=registered_epics,
            read_parent=adapter.read_issue_parent,
            membership_report=membership_report,
        )
        if not membership["valid"]:
            raise task_lifecycle.LifecycleError(
                f"live stream epic membership refused for #{issue_number}: {membership['reason']}"
            )


def perform_mutation(
    state_file: Path,
    adapter: GhGitHubAdapter,
    *,
    action: str,
    authorized_by: str,
    branch: str | None,
    worktree: str | None,
    now: str,
) -> dict[str, Any]:
    with task_lifecycle.lifecycle_lock(state_file):
        ledger = task_lifecycle.load_lifecycle(state_file)
        before = adapter.observe(ledger, now=now, branch=branch, worktree=worktree)
        operation_id = task_lifecycle.mutation_operation_id(ledger, action)
        try:
            if before["github"].get("error"):
                raise task_lifecycle.LifecycleError(f"GitHub observation failed: {before['github']['error']}")
            _assert_live_memberships(
                adapter, ledger,
                registered_epics=before["github"].get("registered_stream_epics"),
                membership_report=before["github"].get("membership_audit"),
            )
        except task_lifecycle.LifecycleError as exc:
            _, failed = _record_failed_mutation(
                state_file, ledger, operation_id=operation_id, action=action,
                authorized_by=authorized_by, requested_at=now,
                detail=f"mutation gate rejected the action: {exc}",
            )
            raise task_lifecycle.LifecycleError(
                f"mutation blocked with durable receipt {failed['id']}: {exc}"
            ) from exc
        ledger, before_receipt, _ = task_lifecycle.reconcile(ledger, before, now=now)
        task_lifecycle.write_lifecycle(state_file, ledger)
        prior_status = task_lifecycle.mutation_status(ledger, operation_id)

        if prior_status == "complete" and _desired_remote_state(
            action, ledger, before
        ):
            return {
                "action": action,
                "operation_id": operation_id,
                "replayed": True,
                "remote_mutation_performed": False,
                "observation_receipt": before_receipt,
            }
        if prior_status == "intent" and _desired_remote_state(action, ledger, before):
            recovered_at = utc_now()
            ledger, completed, _ = task_lifecycle.append_mutation_event(
                ledger,
                operation_id=operation_id,
                action=action,
                status="complete",
                authorized_by=authorized_by,
                requested_at=now,
                completed_at=recovered_at,
                remote_mutation_performed=False,
                detail="recovered remote success after local receipt crash; no duplicate mutation",
            )
            task_lifecycle.write_lifecycle(state_file, ledger)
            return {
                "action": action,
                "operation_id": operation_id,
                "mutation_receipt": completed,
                "observation_receipt": before_receipt,
                "replayed": True,
                "remote_mutation_performed": False,
            }

        try:
            _assert_mutation_ready(action, ledger, before)
        except task_lifecycle.LifecycleError as exc:
            _, failed = _record_failed_mutation(
                state_file,
                ledger,
                operation_id=operation_id,
                action=action,
                authorized_by=authorized_by,
                requested_at=now,
                detail=f"mutation gate rejected the action: {exc}",
            )
            raise task_lifecycle.LifecycleError(
                f"mutation blocked with durable receipt {failed['id']}: {exc}"
            ) from exc

        ledger, intent, _ = task_lifecycle.append_mutation_event(
            ledger,
            operation_id=operation_id,
            action=action,
            status="intent",
            authorized_by=authorized_by,
            requested_at=now,
            completed_at=None,
            remote_mutation_performed=False,
            detail="authorized mutation intent persisted before remote action",
        )
        task_lifecycle.write_lifecycle(state_file, ledger)
        remote_performed = False
        try:
            if not _desired_remote_state(action, ledger, before):
                identity = ledger["identity"]
                if action == "sync-acs":
                    body, _ = evidenced_issue_body(ledger, before)
                    adapter.update_issue_body(
                        identity["repository"], identity["github_issue_number"], body
                    )
                elif action == "arm-auto-merge":
                    adapter.enqueue_pr(identity["repository"], ledger["pr"]["number"])
                else:
                    adapter.close_issue(identity["repository"], identity["github_issue_number"])
                remote_performed = True

            after_time = utc_now()
            after = adapter.observe(ledger, now=after_time, branch=branch, worktree=worktree)
            if not _desired_remote_state(action, ledger, after):
                raise task_lifecycle.LifecycleError("authoritative readback did not confirm the requested mutation")
            ledger, after_receipt, _ = task_lifecycle.reconcile(ledger, after, now=after_time)
            ledger, completed, _ = task_lifecycle.append_mutation_event(
                ledger,
                operation_id=operation_id,
                action=action,
                status="complete",
                authorized_by=authorized_by,
                requested_at=now,
                completed_at=after_time,
                remote_mutation_performed=remote_performed,
                detail=(
                    "remote mutation confirmed by readback"
                    if remote_performed
                    else "desired remote state already existed; recovered without duplicate mutation"
                ),
            )
            task_lifecycle.write_lifecycle(state_file, ledger)
            return {
                "action": action,
                "operation_id": operation_id,
                "intent_receipt": intent,
                "mutation_receipt": completed,
                "observation_receipt": after_receipt,
                "replayed": False,
                "remote_mutation_performed": remote_performed,
            }
        except Exception as exc:
            ledger = task_lifecycle.load_lifecycle(state_file)
            _, failed = _record_failed_mutation(
                state_file,
                ledger,
                operation_id=operation_id,
                action=action,
                authorized_by=authorized_by,
                requested_at=now,
                remote_mutation_performed=remote_performed,
                detail=f"mutation/readback failed: {exc}",
            )
            raise task_lifecycle.LifecycleError(
                f"mutation failed with durable receipt {failed['id']}: {exc}"
            ) from exc


def _state_file(args: argparse.Namespace, identity: Mapping[str, Any] | None = None) -> Path:
    if args.state_file:
        return Path(args.state_file).expanduser().resolve()
    if identity is None:
        raise task_lifecycle.LifecycleError("--state-file is required for this command")
    return task_lifecycle.lifecycle_path(Path(args.repo_root), identity)


def _load_policy(path: Path) -> dict[str, Mapping[str, Any]]:
    policy = _json_file(path)
    if not all(isinstance(key, str) and isinstance(value, dict) for key, value in policy.items()):
        raise task_lifecycle.LifecycleError("AC policy must map stable IDs to policy objects")
    return policy


def _adapter(args: argparse.Namespace, ledger: Mapping[str, Any] | None = None):
    if getattr(args, "observation_file", None):
        return StaticObservationAdapter(_json_file(Path(args.observation_file)))
    return GhGitHubAdapter(Path(args.repo_root))


def _write_and_print(path: Path, ledger: Mapping[str, Any], extra: Mapping[str, Any] | None = None) -> int:
    task_lifecycle.write_lifecycle(path, ledger)
    payload = {
        "state_file": str(path),
        "lifecycle": task_lifecycle.carrier_projection(ledger, state_file=str(path)),
        **dict(extra or {}),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    fresh_fields = ("repository", "stream_epic", "issue", "semantic_title", "task_family", "role", "terminal_goal")
    try:
        if args.identity_file:
            if any(getattr(args, field) is not None for field in fresh_fields):
                raise task_lifecycle.LifecycleError("fresh identity options require --fresh-task-id")
            identity = task_identity.validate_identity(_json_file(Path(args.identity_file)))
        else:
            missing = ["--" + field.replace("_", "-") for field in fresh_fields if getattr(args, field) is None]
            if missing:
                raise task_lifecycle.LifecycleError("--fresh-task-id requires " + ", ".join(missing))
            identity = task_identity.build_identity(
                repository=args.repository,
                stream_epic=args.stream_epic,
                stream_epic_url=None,
                github_issue_number=args.issue,
                github_issue_url=None,
                semantic_title=args.semantic_title,
                task_family=args.task_family,
                role=args.role,
                fresh_task_id=args.fresh_task_id,
                terminal_goal=args.terminal_goal,
                lifecycle_state="active",
            )
    except ValueError as exc:
        raise task_lifecycle.LifecycleError(str(exc)) from exc
    adapter = GhGitHubAdapter(Path(args.repo_root))
    issue = adapter.read_issue(identity["repository"], identity["github_issue_number"])
    registered_epics = adapter.registered_stream_epics(identity["repository"])
    # A native parent that is a registered stream epic decides alone in
    # resolve_membership. Only fetch the live audit snapshot when native
    # parentage is absent (body path) or the native parent is an unregistered
    # sub-epic (native-chain path, #9783).
    membership_report = (
        adapter.membership_audit_report()
        if task_lifecycle.membership_needs_audit(issue["parent_epic"], registered_epics)
        else None
    )
    membership = task_lifecycle.resolve_membership(
        issue_number=identity["github_issue_number"],
        stream_epic=identity["stream_epic"],
        native_parent_epic=issue["parent_epic"],
        repository=identity["repository"],
        native_parent_repository=issue.get("parent_repository"),
        registered_epics=registered_epics,
        membership_report=membership_report,
    )
    if not membership["valid"]:
        raise task_lifecycle.LifecycleError(
            "issue membership does not resolve to the identity's exact registered "
            f"stream epic: {membership['reason']}"
        )
    now = args.now or utc_now()
    snapshot = task_lifecycle.build_ac_snapshot(
        issue["body"], _load_policy(Path(args.ac_policy)), finalized_at=now
    )
    ledger = task_lifecycle.build_lifecycle(
        identity,
        author_family=args.author_family,
        ac_snapshot=snapshot,
        required_checks=args.required_check,
        now=now,
        pr_number=args.pr,
    )
    path = _state_file(args, identity)
    if path.exists() and not args.reuse:
        raise task_lifecycle.LifecycleError(f"lifecycle ledger already exists: {path}; use --reuse")
    if path.exists():
        existing = task_lifecycle.load_lifecycle(path)
        if existing["lifecycle_id"] != ledger["lifecycle_id"]:
            raise task_lifecycle.LifecycleError("existing lifecycle ledger belongs to another identity")
        if identity.get("origin") == "fresh" and existing["identity"] != identity:
            raise task_lifecycle.LifecycleError("existing lifecycle ledger does not match the exact fresh task identity")
        ledger = existing
    _assert_live_memberships(
        adapter, ledger, registered_epics=registered_epics,
        membership_report=membership_report,
    )
    return _write_and_print(path, ledger)


def cmd_locate(args: argparse.Namespace) -> int:
    identity = task_identity.validate_identity(_json_file(Path(args.identity_file)))
    path = task_lifecycle.lifecycle_path(Path(args.repo_root), identity)
    print(json.dumps({"state_file": str(path), "exists": path.exists()}, indent=2))
    return 0 if path.exists() else 1


def cmd_bind_pr(args: argparse.Namespace) -> int:
    path = _state_file(args)
    with task_lifecycle.lifecycle_lock(path):
        ledger = task_lifecycle.bind_pr(
            task_lifecycle.load_lifecycle(path), pr_number=args.pr, now=args.now or utc_now()
        )
        return _write_and_print(path, ledger)


def cmd_evidence(args: argparse.Namespace) -> int:
    path = _state_file(args)
    details = json.loads(args.details) if args.details else {}
    if not isinstance(details, dict):
        raise task_lifecycle.LifecycleError("--details must be a JSON object")
    with task_lifecycle.lifecycle_lock(path):
        ledger, record = task_lifecycle.add_evidence(
            task_lifecycle.load_lifecycle(path),
            ac_id=args.ac_id,
            evidence_type=args.type,
            summary=args.summary,
            url=args.url,
            commit=args.commit,
            details=details,
            recorded_at=args.now or utc_now(),
        )
        return _write_and_print(path, ledger, {"evidence": record})


def cmd_remaining_scope(args: argparse.Namespace) -> int:
    path = _state_file(args)
    with task_lifecycle.lifecycle_lock(path):
        ledger = task_lifecycle.set_remaining_scope(
            task_lifecycle.load_lifecycle(path),
            status=args.status,
            summary=args.summary,
            follow_up_issue=args.follow_up_issue,
            follow_up_stream_epic=args.follow_up_stream_epic,
            evidence_ids=args.evidence_id,
            now=args.now or utc_now(),
        )
        return _write_and_print(path, ledger)


def cmd_reconcile(args: argparse.Namespace) -> int:
    path = _state_file(args)
    now = args.now or utc_now()
    with task_lifecycle.lifecycle_lock(path):
        ledger = task_lifecycle.load_lifecycle(path)
        adapter = _adapter(args, ledger)
        observation = adapter.observe(
            ledger, now=now, branch=args.branch, worktree=args.worktree
        )
        ledger, receipt, replayed = task_lifecycle.reconcile(ledger, observation, now=now)
        return _write_and_print(
            path,
            ledger,
            {
                "receipt": receipt,
                "replayed": replayed,
                "human": f"{receipt['disposition']}: {receipt['state']}",
            },
        )


def cmd_mutate(args: argparse.Namespace) -> int:
    if not args.authorize:
        result = record_unauthorized_mutation(
            _state_file(args),
            action=args.action,
            actor=args.actor,
            now=args.now or utc_now(),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    path = _state_file(args)
    adapter = GhGitHubAdapter(Path(args.repo_root))
    result = perform_mutation(
        path,
        adapter,
        action=args.action,
        authorized_by=args.actor,
        branch=args.branch,
        worktree=args.worktree,
        now=args.now or utc_now(),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def cmd_carrier(args: argparse.Namespace) -> int:
    path = _state_file(args)
    carrier = task_lifecycle.carrier_projection(
        task_lifecycle.load_lifecycle(path), state_file=str(path)
    )
    print(json.dumps(carrier, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify typed task closeout evidence.\nUse read-only observation first; mutations need explicit authorization.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  .venv/bin/python -m scripts.orchestration.task_closeout init --help\n  .venv/bin/python -m scripts.orchestration.task_closeout carrier --state-file ledger.json\n  .venv/bin/python -m scripts.orchestration.task_closeout reconcile --state-file ledger.json\nOutputs: Local lifecycle ledgers and JSON receipts; only mutate can change GitHub.\nExit codes: 0: command succeeded; >=1: refused or failed (locate: 1 if absent).\nRelated: task-identity.md, task-lifecycle-closeout.md; #9297, #10143",
    )
    parser.add_argument("--repo-root", type=Path, default=repo_root_from_file(), help='Repository worktree root; defaults to this checkout.')
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser(
        "init", help="Snapshot authoritative issue ACs into a new lifecycle ledger.",
        description="Initialize from a validated envelope or an exact fresh native task ID.\nFresh threads require all identity options and never resume a rollover.",
    )
    source = init.add_mutually_exclusive_group(required=True)
    source.add_argument("--identity-file", help="Existing task-identity.v1 JSON envelope, e.g. identity.json.")
    source.add_argument("--fresh-task-id", help="Exact current native thread ID; required fresh identity options follow.")
    init.add_argument("--repository", help="Fresh identity repository, e.g. org/repo; required with --fresh-task-id.")
    init.add_argument("--stream-epic", type=int, help="Fresh identity registered stream epic number; required with --fresh-task-id.")
    init.add_argument("--issue", type=int, help="Fresh identity GitHub issue number; required with --fresh-task-id.")
    init.add_argument("--semantic-title", help="Fresh identity task description; required with --fresh-task-id.")
    init.add_argument("--task-family", help="Fresh identity lowercase task family slug; required with --fresh-task-id.")
    init.add_argument("--role", help="Fresh identity assigned role, e.g. driver; required with --fresh-task-id.")
    init.add_argument("--terminal-goal", choices=sorted(task_identity.TERMINAL_GOALS), help="Fresh identity completion goal; required with --fresh-task-id.")
    init.add_argument("--ac-policy", required=True, help='JSON mapping of stable AC IDs to due states and evidence types, e.g. ac-policy.json.')
    init.add_argument("--author-family", required=True, help='Implementation author family, e.g. codex.')
    init.add_argument("--required-check", action="append", required=True, help='Required CI check name, e.g. CI Gate; repeat for each check.')
    init.add_argument("--pr", type=int, help='Exact GitHub PR number; init defaults to unbound.')
    init.add_argument("--state-file", help='Lifecycle JSON ledger path; init defaults to the canonical shared issue path.')
    init.add_argument("--now", help='UTC observation timestamp in ISO 8601; defaults to current UTC.')
    init.add_argument("--reuse", action="store_true", help='Reuse a ledger without resetting evidence; default refuses an existing ledger.')
    init.set_defaults(func=cmd_init)

    locate = sub.add_parser("locate", help="Resolve the shared ledger path from task-identity.v1.")
    locate.add_argument("--identity-file", required=True, help='Validated task-identity.v1 JSON envelope, e.g. identity.json.')
    locate.set_defaults(func=cmd_locate, state_file=None)

    bind = sub.add_parser("bind-pr", help="Bind the exact PR once; mismatched rebinding fails closed.")
    bind.add_argument("--state-file", required=True, help='Lifecycle JSON ledger path; init defaults to the canonical shared issue path.')
    bind.add_argument("--pr", type=int, required=True, help='Exact GitHub PR number; init defaults to unbound.')
    bind.add_argument("--now", help='UTC observation timestamp in ISO 8601; defaults to current UTC.')
    bind.set_defaults(func=cmd_bind_pr)

    evidence = sub.add_parser("add-evidence", help="Append typed current-task AC evidence.")
    evidence.add_argument("--state-file", required=True, help='Lifecycle JSON ledger path; init defaults to the canonical shared issue path.')
    evidence.add_argument("--ac-id", required=True, help='Exact stable acceptance criterion ID, e.g. AC-01.')
    evidence.add_argument("--type", choices=sorted(task_lifecycle.EVIDENCE_TYPES), required=True, help='Typed evidence category, e.g. test.')
    evidence.add_argument("--summary", required=True, help='Evidence or remaining-scope description; remaining-scope defaults to empty.')
    evidence.add_argument("--url", help='Public supporting evidence URL; default omitted.')
    evidence.add_argument("--commit", help='Exact evidence commit SHA; default omitted.')
    evidence.add_argument("--details", help="JSON object; review evidence records model families and verdict.")
    evidence.add_argument("--now", help='UTC observation timestamp in ISO 8601; defaults to current UTC.')
    evidence.set_defaults(func=cmd_evidence)

    remaining = sub.add_parser("remaining-scope", help="Record none/open/transferred remaining scope.")
    remaining.add_argument("--state-file", required=True, help='Lifecycle JSON ledger path; init defaults to the canonical shared issue path.')
    remaining.add_argument("--status", choices=["none", "open", "transferred"], required=True, help='Remaining scope disposition: none, open, or transferred.')
    remaining.add_argument("--summary", default="", help='Evidence or remaining-scope description; remaining-scope defaults to empty.')
    remaining.add_argument("--follow-up-issue", type=int, help='Transferred-scope issue number; default omitted.')
    remaining.add_argument("--follow-up-stream-epic", type=int, help='Transferred-scope registered epic number; default omitted.')
    remaining.add_argument("--evidence-id", action="append", help='Supporting ledger evidence ID; repeat as needed; default none.')
    remaining.add_argument("--now", help='UTC observation timestamp in ISO 8601; defaults to current UTC.')
    remaining.set_defaults(func=cmd_remaining_scope)

    reconcile = sub.add_parser("reconcile", help="Read GitHub/Git authority and append an idempotent receipt.")
    reconcile.add_argument("--state-file", required=True, help='Lifecycle JSON ledger path; init defaults to the canonical shared issue path.')
    reconcile.add_argument("--branch", help='Exact implementation branch name; default inferred by the adapter.')
    reconcile.add_argument("--worktree", help='Implementation worktree path; default inferred by the adapter.')
    reconcile.add_argument("--observation-file", help="Hermetic observation fixture; no live GitHub reads.")
    reconcile.add_argument("--now", help='UTC observation timestamp in ISO 8601; defaults to current UTC.')
    reconcile.set_defaults(func=cmd_reconcile)

    mutate = sub.add_parser("mutate", help="Explicitly authorize one narrow GitHub closeout mutation.")
    mutate.add_argument("action", choices=["sync-acs", "arm-auto-merge", "close-issue"], help='One remote closeout action; current-head gates still apply.')
    mutate.add_argument("--state-file", required=True, help='Lifecycle JSON ledger path; init defaults to the canonical shared issue path.')
    mutate.add_argument("--authorize", action="store_true", help='Authorize the selected remote action; default records refusal without mutation.')
    mutate.add_argument("--actor", required=True, help='Attribution for the narrow authorization, e.g. codex/task-id.')
    mutate.add_argument("--branch", help='Exact implementation branch name; default inferred by the adapter.')
    mutate.add_argument("--worktree", help='Implementation worktree path; default inferred by the adapter.')
    mutate.add_argument("--now", help='UTC observation timestamp in ISO 8601; defaults to current UTC.')
    mutate.set_defaults(func=cmd_mutate)

    carrier = sub.add_parser("carrier", help="Render the exact delegation/ledger/rollover carrier.")
    carrier.add_argument("--state-file", required=True, help='Lifecycle JSON ledger path; init defaults to the canonical shared issue path.')
    carrier.set_defaults(func=cmd_carrier)
    return parser


@publication_cli(task_lifecycle.LifecycleError)
def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (task_lifecycle.LifecycleError, json.JSONDecodeError, OSError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
