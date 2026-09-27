#!/usr/bin/env python3
"""Keep one advisory DoR checker comment on an opened or edited issue."""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path
from typing import Any

from scripts.ci.check_issue_task_quality import FIELDS, issue_is_trivial, score_body

MARKER = "<!-- issue-task-quality:v1 -->"
BOT_LOGIN = "github-actions[bot]"


def render_comment(issue: dict[str, Any]) -> str:
    issue_body = issue.get("body") or ""
    result = score_body(issue_body, trivial=issue_is_trivial(issue_body, issue.get("labels") or []))
    if result["verdict"] == "PASS":
        details = "DoR card check: PASS (trivial exemption)." if result["trivial"] else "DoR card check: PASS."
    else:
        names = {field.key: field.label for field in FIELDS}
        missing = "\n".join(f"- {names[key]}" for key in result["missing"])
        details = f"DoR card check: WARN. Missing fields:\n{missing}"
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


def main() -> int:
    token = os.environ["GITHUB_TOKEN"]
    repo = os.environ["GITHUB_REPOSITORY"]
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
    number = int(event["issue"]["number"])
    root = f"https://api.github.com/repos/{repo}"

    def api(method: str, path: str, data: dict[str, str] | None = None) -> Any:
        payload = json.dumps(data).encode() if data is not None else None
        request = urllib.request.Request(
            root + path,
            data=payload,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28",
                **({"Content-Type": "application/json"} if payload is not None else {}),
            },
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()
        return json.loads(raw) if raw else None

    issue = api("GET", f"/issues/{number}")
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
