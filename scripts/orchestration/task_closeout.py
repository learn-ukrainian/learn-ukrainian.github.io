#!/usr/bin/env python
"""Observe, validate, and explicitly close out a task lifecycle ledger.

Read-only reconciliation is the default.  Remote changes require the ``mutate``
subcommand, an exact action, ``--authorize``, and an actor recorded in the
append-only mutation receipt.
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

from scripts.orchestration import task_identity, task_lifecycle

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


def _default_runner(repo_root: Path) -> Runner:
    def run(args: list[str], stdin: str | None = None) -> str:
        completed = subprocess.run(
            args,
            cwd=repo_root,
            input=stdin,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "command failed").strip()
            raise task_lifecycle.LifecycleError(f"{' '.join(args[:4])} failed: {detail[:1000]}")
        return completed.stdout

    return run


class GhGitHubAdapter:
    """Authoritative GitHub reads and the three explicitly allowed mutations."""

    def __init__(self, repo_root: Path, *, runner: Runner | None = None) -> None:
        self.repo_root = repo_root.resolve()
        self._run = runner or _default_runner(self.repo_root)

    def _json(self, args: list[str], stdin: str | None = None) -> Any:
        raw = self._run(args, stdin)
        try:
            return json.loads(raw or "null")
        except json.JSONDecodeError as exc:
            raise task_lifecycle.LifecycleError(
                f"GitHub command returned invalid JSON: {' '.join(args[:4])}"
            ) from exc

    def registered_stream_epics(self) -> list[int]:
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

    @staticmethod
    def _owner_name(repository: str) -> tuple[str, str]:
        try:
            owner, name = repository.split("/", 1)
        except ValueError as exc:
            raise task_lifecycle.LifecycleError("repository must be owner/name") from exc
        return owner, name

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
        owner, name = self._owner_name(repository)
        parent_doc = self._json(
            [
                "gh",
                "api",
                "graphql",
                "-F",
                f"owner={owner}",
                "-F",
                f"name={name}",
                "-F",
                f"number={issue_number}",
                "-f",
                "query=query($owner:String!,$name:String!,$number:Int!){"
                "repository(owner:$owner,name:$name){nameWithOwner issue(number:$number){"
                "number state url parent{number url}}}}",
            ]
        )
        repository_doc = ((parent_doc or {}).get("data") or {}).get("repository") or {}
        parent_issue = repository_doc.get("issue") or {}
        parent = parent_issue.get("parent") or {}
        return {
            "number": issue.get("number"),
            "state": str(issue.get("state") or "").upper(),
            "body": issue.get("body") or "",
            "url": issue.get("url"),
            "closed_at": issue.get("closedAt"),
            "parent_epic": parent.get("number"),
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
                "autoMergeRequest,reviewDecision,reviews,statusCheckRollup,body",
            ]
        )
        checks: list[dict[str, Any]] = []
        for raw in pr.get("statusCheckRollup") or []:
            typename = raw.get("__typename")
            if typename == "CheckRun":
                checks.append(
                    {
                        "name": raw.get("name"),
                        "status": str(raw.get("status") or "").upper(),
                        "conclusion": str(raw.get("conclusion") or "").upper(),
                        "url": raw.get("detailsUrl"),
                    }
                )
            else:
                state = str(raw.get("state") or "").upper()
                checks.append(
                    {
                        "name": raw.get("context") or raw.get("name"),
                        "status": "COMPLETED" if state in {"SUCCESS", "FAILURE", "ERROR"} else "IN_PROGRESS",
                        "conclusion": state,
                        "url": raw.get("targetUrl"),
                    }
                )
        auto = pr.get("autoMergeRequest") or {}
        merge_commit = pr.get("mergeCommit") or {}
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
        }

    def _comments(self, repository: str, pr_number: int) -> list[dict[str, Any]]:
        issue_comments = self._json(
            [
                "gh",
                "api",
                f"repos/{repository}/issues/{pr_number}/comments",
                "--paginate",
            ]
        )
        native_reviews = self._json(
            [
                "gh",
                "api",
                f"repos/{repository}/pulls/{pr_number}/reviews",
                "--paginate",
            ]
        )
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
        deployments = self._json(
            [
                "gh",
                "api",
                "--method",
                "GET",
                f"repos/{repository}/deployments",
                "-f",
                f"sha={sha}",
            ]
        )
        result: list[dict[str, Any]] = []
        for deployment in deployments or []:
            deployment_id = deployment.get("id")
            statuses = self._json(
                ["gh", "api", f"repos/{repository}/deployments/{deployment_id}/statuses"]
            )
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
            "registered_stream_epics": self.registered_stream_epics(),
            "issue": issue,
            "pr": pr,
            "comments": comments,
            "deployments": deployments,
            "follow_up": self._follow_up(
                repository,
                identity["github_issue_number"],
                issue["body"],
                ledger["remaining_scope"],
            ),
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
        request = json.dumps({"body": body}, ensure_ascii=False)
        self._run(
            ["gh", "api", "-X", "PATCH", f"repos/{repository}/issues/{issue_number}", "--input", "-"],
            request,
        )

    def arm_auto_merge(self, repository: str, pr_number: int) -> None:
        self._run(
            [
                "gh",
                "pr",
                "merge",
                str(pr_number),
                "--repo",
                repository,
                "--auto",
                "--squash",
                "--delete-branch",
            ],
            None,
        )

    def close_issue(self, repository: str, issue_number: int) -> None:
        self._run(
            [
                "gh",
                "issue",
                "close",
                str(issue_number),
                "--repo",
                repository,
                "--reason",
                "completed",
            ],
            None,
        )


class StaticObservationAdapter:
    """Hermetic injected observation adapter used by tests and offline replay."""

    def __init__(self, observation: Mapping[str, Any]) -> None:
        self.observation = deepcopy(dict(observation))

    def observe(self, _ledger: Mapping[str, Any], **_kwargs: Any) -> dict[str, Any]:
        return deepcopy(self.observation)


def _replace_checkbox(body: str, ac_id: str) -> str:
    lines = body.splitlines()
    needle = f"**{ac_id}**"
    for index, line in enumerate(lines):
        if needle in line and line.lstrip().startswith("- ["):
            prefix = line[: len(line) - len(line.lstrip())]
            content = line.lstrip()
            lines[index] = prefix + "- [x]" + content[5:]
    suffix = "\n" if body.endswith("\n") else ""
    return "\n".join(lines) + suffix


def evidenced_issue_body(
    ledger: Mapping[str, Any], observation: Mapping[str, Any]
) -> tuple[str, list[str]]:
    evaluation = task_lifecycle.evaluate(ledger, observation)
    valid = {key: set(value) for key, value in evaluation["valid_evidence"].items()}
    body = str(observation["github"]["issue"].get("body") or "")
    checked_ids: list[str] = []
    for criterion in ledger["ac_snapshot"]["criteria"]:
        if not criterion["applicable"]:
            continue
        if set(criterion["required_evidence"]).issubset(valid.get(criterion["id"], set())):
            body = _replace_checkbox(body, criterion["id"])
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
        ledger, before_receipt, _ = task_lifecycle.reconcile(ledger, before, now=now)
        task_lifecycle.write_lifecycle(state_file, ledger)
        operation_id = task_lifecycle.mutation_operation_id(ledger, action)
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
                    adapter.arm_auto_merge(identity["repository"], ledger["pr"]["number"])
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
    identity = task_identity.validate_identity(_json_file(Path(args.identity_file)))
    adapter = GhGitHubAdapter(Path(args.repo_root))
    issue = adapter.read_issue(identity["repository"], identity["github_issue_number"])
    if identity["stream_epic"] not in adapter.registered_stream_epics():
        raise task_lifecycle.LifecycleError(
            "task identity stream epic is absent from scripts/config/issue_streams.yaml"
        )
    if issue["parent_epic"] != identity["stream_epic"]:
        raise task_lifecycle.LifecycleError("issue is not a native child of the identity's exact stream epic")
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
        ledger = existing
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=repo_root_from_file())
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Snapshot authoritative issue ACs into a new lifecycle ledger.")
    init.add_argument("--identity-file", required=True)
    init.add_argument("--ac-policy", required=True)
    init.add_argument("--author-family", required=True)
    init.add_argument("--required-check", action="append", required=True)
    init.add_argument("--pr", type=int)
    init.add_argument("--state-file")
    init.add_argument("--now")
    init.add_argument("--reuse", action="store_true")
    init.set_defaults(func=cmd_init)

    locate = sub.add_parser("locate", help="Resolve the shared ledger path from task-identity.v1.")
    locate.add_argument("--identity-file", required=True)
    locate.set_defaults(func=cmd_locate, state_file=None)

    bind = sub.add_parser("bind-pr", help="Bind the exact PR once; mismatched rebinding fails closed.")
    bind.add_argument("--state-file", required=True)
    bind.add_argument("--pr", type=int, required=True)
    bind.add_argument("--now")
    bind.set_defaults(func=cmd_bind_pr)

    evidence = sub.add_parser("add-evidence", help="Append typed current-task AC evidence.")
    evidence.add_argument("--state-file", required=True)
    evidence.add_argument("--ac-id", required=True)
    evidence.add_argument("--type", choices=sorted(task_lifecycle.EVIDENCE_TYPES), required=True)
    evidence.add_argument("--summary", required=True)
    evidence.add_argument("--url")
    evidence.add_argument("--commit")
    evidence.add_argument("--details", help="JSON object; review evidence records model families and verdict.")
    evidence.add_argument("--now")
    evidence.set_defaults(func=cmd_evidence)

    remaining = sub.add_parser("remaining-scope", help="Record none/open/transferred remaining scope.")
    remaining.add_argument("--state-file", required=True)
    remaining.add_argument("--status", choices=["none", "open", "transferred"], required=True)
    remaining.add_argument("--summary", default="")
    remaining.add_argument("--follow-up-issue", type=int)
    remaining.add_argument("--follow-up-stream-epic", type=int)
    remaining.add_argument("--evidence-id", action="append")
    remaining.add_argument("--now")
    remaining.set_defaults(func=cmd_remaining_scope)

    reconcile = sub.add_parser("reconcile", help="Read GitHub/Git authority and append an idempotent receipt.")
    reconcile.add_argument("--state-file", required=True)
    reconcile.add_argument("--branch")
    reconcile.add_argument("--worktree")
    reconcile.add_argument("--observation-file", help="Hermetic observation fixture; no live GitHub reads.")
    reconcile.add_argument("--now")
    reconcile.set_defaults(func=cmd_reconcile)

    mutate = sub.add_parser("mutate", help="Explicitly authorize one narrow GitHub closeout mutation.")
    mutate.add_argument("action", choices=["sync-acs", "arm-auto-merge", "close-issue"])
    mutate.add_argument("--state-file", required=True)
    mutate.add_argument("--authorize", action="store_true")
    mutate.add_argument("--actor", required=True)
    mutate.add_argument("--branch")
    mutate.add_argument("--worktree")
    mutate.add_argument("--now")
    mutate.set_defaults(func=cmd_mutate)

    carrier = sub.add_parser("carrier", help="Render the exact delegation/ledger/rollover carrier.")
    carrier.add_argument("--state-file", required=True)
    carrier.set_defaults(func=cmd_carrier)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (task_lifecycle.LifecycleError, json.JSONDecodeError, OSError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
