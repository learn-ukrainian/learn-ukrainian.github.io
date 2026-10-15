#!/usr/bin/env python3
"""Keep one advisory DoR checker comment on an opened or edited issue."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.ci.check_issue_task_quality import (
    FIELDS,
    NON_OVERRIDABLE,
    evaluate_issue,
    issue_is_trivial,
    membership_error,
    observe_membership,
    score_body,
    time_budget,
)
from scripts.common.github_client import GitHubClient, GitHubRateLimited

MARKER = "<!-- issue-task-quality:v1 -->"
BOT_LOGIN = "github-actions[bot]"


def render_comment(issue: dict[str, Any]) -> str:
    issue_body = issue.get("body") or ""
    result = issue.get("_quality") or score_body(
        issue_body, trivial=issue_is_trivial(issue_body, issue.get("labels") or [])
    )
    if result["dor"]["status"] == "PASS":
        details = "DoR card check: PASS (trivial exemption)." if result["trivial"] else "DoR card check: PASS."
    else:
        names = {field.key: field.label for field in FIELDS}
        missing = "\n".join(f"- {names[e['field']]}" for e in result["dor"]["errors"])
        details = f"DoR card check: WARN. Missing fields:\n{missing}"
    membership = result["membership"]
    details += f"\nDoD structure: {result['dod']['status']}. Membership: {membership['status']}."
    codes = [e["code"] for part in (result["dod"], membership) for e in part["errors"]]
    if codes:
        details += "\nStructure and membership findings: " + ", ".join(codes) + "."
    if issue.get("_observed_at"):
        observation = (
            "no native parent observed"
            if membership.get("pending_native_link")
            or any(e["code"] == "membership_missing_parent" for e in membership["errors"])
            else "membership observed"
        )
        details += f"\n{observation} at {issue['_observed_at']}; dispatch re-checks live."
    if membership.get("pending_native_link"):
        details += "\nCanonical body evidence accepted; pending_native_link."
    return f"{MARKER}\n{details}\n\nSee `docs/best-practices/task-quality.md`. This is advisory for issue editing."


def reconcile_comments(issue: dict[str, Any], comments: list[dict[str, Any]], api: Any, path: str) -> None:
    """Update the current bot comment, removing older bot duplicates."""
    body = render_comment(issue)
    matching = [
        comment
        for comment in comments
        if comment.get("user", {}).get("login") == BOT_LOGIN and MARKER in (comment.get("body") or "")
    ]
    if matching:
        keep = matching[0]
        if keep.get("body") != body:
            api("PATCH", f"{path}/comments/{keep['id']}", {"body": body})
        for extra in matching[1:]:
            api("DELETE", f"{path}/comments/{extra['id']}")
    else:
        api("POST", f"{path}/comments", {"body": body})


def check_current_issue(issue: dict, repo: str, number: int, *, opened: bool) -> dict:
    """Allow native parent creation to settle after opened, at most three minutes."""
    deadline = time.monotonic() + 180
    while True:
        try:
            with time_budget(min(60, max(0.01, deadline - time.monotonic()))):
                membership = observe_membership(issue, repo, number)
        except TimeoutError:
            membership = membership_error("membership_timeout")
        if (
            not opened
            or not (
                membership.get("pending_native_link")
                or any(e["code"] == "membership_missing_parent" for e in membership["errors"])
            )
            or time.monotonic() >= deadline
        ):
            return evaluate_issue(issue, membership)
        time.sleep(min(15, max(0, deadline - time.monotonic())))


def _main() -> int:
    token = os.environ["GITHUB_TOKEN"]
    repo = os.environ["GITHUB_REPOSITORY"]
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
    number = int(event["issue"]["number"])
    github = GitHubClient(env={**os.environ, "GH_TOKEN": token})

    def api(method: str, path: str, data: dict[str, str] | None = None) -> Any:
        return github.request(method, f"repos/{repo}{path}", payload=data, fresh=True).require_fresh()

    issue = api("GET", f"/issues/{number}")
    issue["_quality"] = check_current_issue(issue, repo, number, opened=event.get("action") == "opened")
    issue["_observed_at"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    comments: list[dict[str, Any]] = []
    page = 1
    while True:
        batch = api("GET", f"/issues/{number}/comments?per_page=100&page={page}")
        comments.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    reconcile_comments(issue, comments, api, f"/issues/{number}")
    print(f"issue #{number}: advisory DoR comment synchronized")
    codes = set(issue["_quality"]["missing"])
    return int(
        bool(codes & NON_OVERRIDABLE or (event.get("action") == "opened" and "membership_missing_parent" in codes))
    )


def main() -> int:
    try:
        return _main()
    except GitHubRateLimited:
        print("issue quality: skipped rate_limited")
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except GitHubRateLimited as exc:
        print(f"issue quality timer: skipped reset_at={exc.reset_at}")
        sys.exit(0)
