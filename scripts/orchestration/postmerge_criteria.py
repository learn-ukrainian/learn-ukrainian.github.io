"""Keep issues with outstanding acceptance criteria open after merge (#11213)."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import date

from scripts.common import github_client
from scripts.fleet_comms.authority import AuthorityService
from scripts.orchestration import task_lifecycle
from scripts.publish.github import publish, read

LANES = frozenset({
    "claude-infra", "codex-devops", "codex-atlas", "grok-monitor",
    "gemini-open-model-data", "claude-cto",
})
_MERGE_TIME = r"\b(?:after\s+merge|post[- ]merge|once\s+merged|after\s+landing)\b"
_EVIDENCE_ACTION = r"\b(?:collect|review|record|capture|publish|provide|measure|observe|monitor|verify)\b"
_EVIDENCE = r"\b(?:evidence|receipts?|measurements?|observations?|table|\d+(?:/\d+)?[- ]runs?)\b"
POST_MERGE_RE = re.compile(
    # A time marker alone can describe code or test behaviour rather than a receipt.
    rf"{_MERGE_TIME}\s*[,;:]?\s*(?:{_EVIDENCE_ACTION}|{_EVIDENCE})"
    rf"|{_EVIDENCE_ACTION}[^.;\n]*{_EVIDENCE}[^.;\n]*{_MERGE_TIME}",
    re.I,
)


def visible_markdown(body: str) -> str:
    """Remove comments, block quotes and fenced examples before parsing items."""
    lines = []
    fence = None
    for line in re.sub(r"<!--.*?-->", "", body, flags=re.S).splitlines():
        stripped = line.lstrip()
        if stripped.startswith(">"):
            continue
        match = re.match(r"(`{3,}|~{3,})(.*)$", stripped)
        if fence:
            if match and match[1][0] == fence[0] and len(match[1]) >= len(fence) and not match[2].strip():
                fence = None
            continue
        if match:
            fence = match[1]
            continue
        lines.append(line)
    return "\n".join(lines)


def acceptance_items(body: str) -> list[dict]:
    """Use the lifecycle grammar, excluding Markdown examples."""
    try:
        return task_lifecycle.parse_issue_acceptance_criteria(visible_markdown(body))
    except task_lifecycle.LifecycleError as exc:
        if str(exc) == "issue body has no stable-ID acceptance criteria":
            return []
        raise


def item_assignment(text: str) -> tuple[str | None, str | None]:
    """Read one recognized owner and one valid ISO calendar deadline."""
    owners = re.findall(r"(?<![\w-])(?:\*\*)?owner:(?:\*\*)?\s*([^\s,;|]+)", text, re.I)
    owners = [value.removesuffix(".") for value in owners]
    owners = [value[1:-1] if value.startswith("`") and value.endswith("`") else value for value in owners]
    dates = re.findall(r"\bdue:\s*([^\s,;|]+)", text, re.I)
    owner = owners[0] if len(owners) == 1 and owners[0] in LANES else None
    due = None
    if len(dates) == 1 and re.fullmatch(r"\d{4}-\d{2}-\d{2}", dates[0]):
        try:
            date.fromisoformat(dates[0])
            due = dates[0]
        except ValueError:
            pass
    return owner, due


def closing_issues(pr: dict, repository: str) -> list[tuple[str, int]]:
    """Combine GitHub closing links with explicit closing keywords in the body."""
    issues = set()
    for reference in pr["closingIssuesReferences"]:
        match = re.fullmatch(r"https://github.com/([^/]+/[^/]+)/issues/(\d+)", reference["url"])
        if not match:
            raise ValueError("invalid closing issue URL")
        issues.add((match[1], int(match[2])))
    for match in re.finditer(
        r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+(?:([\w.-]+/[\w.-]+))?#([1-9]\d*)\b",
        visible_markdown(pr.get("body") or ""), re.I,
    ):
        issues.add((match[1] or repository, int(match[2])))
    return sorted(issues)


def run_postmerge_criteria(pr_number: int, *, apply: bool = False) -> dict:
    """Inspect only this merged PR's issues; dry-run never writes or escalates."""
    pr = json.loads(github_client.check_output(
        ["gh", "pr", "view", str(pr_number), "--json", "state,body,url,closingIssuesReferences"],
        text=True, timeout=60,
    ))
    if pr["state"] != "MERGED":
        raise ValueError("PR must be MERGED before checking post-merge criteria")
    match = re.fullmatch(r"https://github.com/([^/]+/[^/]+)/pull/\d+", pr["url"])
    if not match:
        raise ValueError("invalid PR URL")
    reports = []
    for repository, number in closing_issues(pr, match[1]):
        issue = json.loads(read(
            "issue", repo=repository, number=number, capture_output=True, text=True, check=True, timeout=60,
        ).stdout)
        if issue["state"] not in {"open", "closed"}:
            raise ValueError("issue state unavailable")
        outstanding = [item for item in acceptance_items(issue.get("body") or "") if not item["checked"]]
        report = {"repository": repository, "issue": number, "outstanding": outstanding}
        reports.append(report)
        if not outstanding:
            continue
        lines = []
        unassigned = []
        for item in outstanding:
            owner, due = item_assignment(item["text"])
            lines.append(f"- [ ] {item['id']}: {item['text']} | owner: {owner or 'MISSING'} | due: {due or 'MISSING'}")
            if not owner or not due:
                unassigned.append(item)
        content = "Outstanding acceptance criteria keep this issue unfinished.\n\n" + "\n".join(lines)
        report["comment"] = content
        report["missing_assignment"] = [item["id"] for item in unassigned]
        if not apply:
            continue
        if issue["state"] == "closed":
            publish("issue-reopen", repo=repository, number=number, check=True, capture_output=True, text=True, timeout=60)
        if unassigned:
            key = _item_set_key(repository, number, unassigned)
            with AuthorityService(root=None) as authority:
                authority.enqueue_supervisory_request(
                    sender="codex-devops", recipient="claude-cto",
                    body=f"Issue {repository}#{number} has outstanding criteria missing a recognized owner or valid due date:\n"
                    + "\n".join(f"- {item['id']}: {item['text']}" for item in sorted(unassigned, key=lambda item: item["id"])),
                    correlation_id=f"postmerge-criteria:{repository}#{number}",
                    idempotency_key=f"postmerge-criteria:{key}",
                )
        marker = f"<!-- postmerge-criteria:{_item_set_key(repository, number, outstanding)} -->"
        pages = json.loads(read(
            "comments", repo=repository, number=number, paginate=True, slurp=True,
            capture_output=True, text=True, check=True, timeout=60,
        ).stdout)
        if not any(marker in (comment.get("body") or "") for page in pages for comment in page):
            publish(
                "issue-comment", repo=repository, number=number, body=f"{marker}\n{content}",
                capture_output=True, text=True, check=True, timeout=60,
            )
    return {"pr": pr_number, "apply": apply, "issues": reports,
            "ok": not any(report["outstanding"] for report in reports)}


def _item_set_key(repository: str, number: int, items: list[dict]) -> str:
    payload = [repository.casefold(), number, sorted((item["id"], item["text"]) for item in items)]
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Report outstanding acceptance criteria for a merged PR's issues.\n"
        "Use after merge; dry-run by default. Do not use to close issues or audit old issues.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
        "  .venv/bin/python -m scripts.orchestration.postmerge_criteria --pr 123\n"
        "  .venv/bin/python -m scripts.orchestration.postmerge_criteria --pr 123 --apply\n"
        "Outputs: JSON report; apply reopens unfinished issues, comments once per item set,\n"
        "and sends idempotent supervisory requests to claude-cto for missing assignments.\n"
        "Exit codes: 0 = no outstanding items; 1 = outstanding items; 2 = read/write or state error.\n"
        "Related: docs/best-practices/task-quality.md; #11213.",
    )
    parser.add_argument("--pr", type=int, required=True, help="Merged PR number, e.g. 123, in the current repository.")
    parser.add_argument("--apply", action="store_true", help="Apply reopen, comment and escalation actions (default: dry-run).")
    args = parser.parse_args(argv)
    try:
        result = run_postmerge_criteria(args.pr, apply=args.apply)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
