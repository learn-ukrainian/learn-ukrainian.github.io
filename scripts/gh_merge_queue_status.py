#!/usr/bin/env python3
"""Query and report GitHub Merge Queue status, position, ETA, and CI run for a pull request.

Answers #7814 item 13:
After `gh pr merge` enqueues into the merge queue, this helper prints queue
membership, queue position, ETA (or 'in queue, position unknown'), and the latest
`merge_group` workflow run URL so drivers do not stall on OPEN + CLEAN with only
the '! The merge strategy...' hint.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Ensure repository root is on sys.path for standalone script invocation
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ci.ci_timings import (
    _gh_env,
    extract_pr_number,
    resolve_repository,
)

GRAPHQL_PR_MQ_QUERY = """
query($owner: String!, $name: String!, $number: Int!, $branch: String!) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      number
      title
      state
      merged
      mergeable
      mergeStateStatus
      isInMergeQueue
      isMergeQueueEnabled
      headRefName
      headRefOid
      baseRefName
      mergeQueueEntry {
        id
        position
        state
        enqueuedAt
        estimatedTimeToMerge
        jump
        solo
        headCommit {
          oid
          checkSuites(first: 10) {
            nodes {
              status
              conclusion
              workflowRun {
                id
                url
                event
              }
            }
          }
        }
      }
    }
    mergeQueue(branch: $branch) {
      url
      nextEntryEstimatedTimeToMerge
      entries(first: 50) {
        totalCount
        nodes {
          position
          state
          enqueuedAt
          estimatedTimeToMerge
          pullRequest {
            number
          }
        }
      }
    }
  }
}
"""


def parse_pr_identifier(value: str | int) -> int:
    """Extract integer PR number from a number, '#123', URL, or branch name."""
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if not text:
        raise ValueError("Empty pull request identifier provided.")
    # Match URL like https://github.com/.../pull/1234
    url_m = re.search(r"/pull/(\d+)", text)
    if url_m:
        return int(url_m.group(1))
    # Match queue branch or feature branch with PR number
    pr_num = extract_pr_number(text)
    if pr_num is not None:
        return pr_num
    # Match branch or text with prefix '#123' or 'pr123'
    m = re.search(r"(?:^|[#/_-]|pr)(\d+)(?:[#/_.-]|$)", text, re.IGNORECASE)
    if m:
        return int(m.group(1))
    # Fallback to pure digits if present
    digits = re.findall(r"\d+", text)
    if digits:
        return int(digits[0])
    raise ValueError(f"Could not parse pull request number from: {value!r}")


def format_eta_human(seconds: int | None) -> str | None:
    """Format seconds into a concise human-readable ETA (~X min, ~Xh Ym, <1 min)."""
    if seconds is None:
        return None
    if seconds < 60:
        return "<1 min"
    minutes = round(seconds / 60)
    if minutes < 60:
        return f"~{minutes} min"
    hours = minutes // 60
    rem_min = minutes % 60
    if rem_min == 0:
        return f"~{hours}h"
    return f"~{hours}h {rem_min}m"


def build_summary_line(
    pr_number: int,
    queued: bool,
    position: int | None,
    state: str | None,
    eta_human: str | None,
    run_url: str | None,
    pr_state: str,
    pr_merged: bool,
    merge_state_status: str | None,
) -> str:
    """Build a single deterministic human-readable status line."""
    run_part = f"run={run_url}" if run_url else "run=none"
    if queued:
        if position is not None:
            pos_part = f"position={position}"
            details: list[str] = []
            if state:
                details.append(state)
            if eta_human:
                details.append(f"{eta_human} ETA")
            detail_str = f" ({', '.join(details)})" if details else ""
            return f"PR #{pr_number}: queued=yes, {pos_part}{detail_str}, {run_part}"
        else:
            return f"PR #{pr_number}: queued=yes, position=unknown (in queue, position unknown), {run_part}"
    else:
        if pr_merged:
            return f"PR #{pr_number}: queued=no (merged=yes, state=MERGED), {run_part}"
        elif pr_state == "CLOSED":
            return f"PR #{pr_number}: queued=no (state=CLOSED), {run_part}"
        else:
            status_desc = f"state={pr_state}"
            if merge_state_status:
                status_desc += f", mergeStateStatus={merge_state_status}"
            return f"PR #{pr_number}: queued=no ({status_desc}), {run_part}"


def find_latest_merge_group_run(
    runs: list[dict[str, Any]],
    target_pr: int,
) -> dict[str, Any] | None:
    """Find the most recent merge_group workflow run for target_pr, preferring CI."""
    matching: list[dict[str, Any]] = []
    for r in runs:
        if not isinstance(r, dict):
            continue
        branch = r.get("head_branch") or r.get("headBranch") or ""
        if extract_pr_number(branch) == target_pr:
            matching.append(r)
    if not matching:
        return None
    matching.sort(
        key=lambda r: str(r.get("created_at") or r.get("createdAt") or ""),
        reverse=True,
    )
    newest_created = str(matching[0].get("created_at") or matching[0].get("createdAt") or "")
    same_batch = [
        r
        for r in matching
        if str(r.get("created_at") or r.get("createdAt") or "") == newest_created
    ]
    ci_run = next((r for r in same_batch if str(r.get("name") or "").upper() == "CI"), None)
    return ci_run or matching[0]


@dataclass(frozen=True)
class MergeQueueStatus:
    pr_number: int
    queued: bool
    position: int | None
    state: str | None
    enqueued_at: str | None
    estimated_time_to_merge_seconds: int | None
    estimated_time_to_merge_human: str | None
    latest_merge_group_run_url: str | None
    latest_merge_group_run_status: str | None
    latest_merge_group_run_conclusion: str | None
    pr_state: str
    pr_merged: bool
    pr_merge_state_status: str | None
    queue_url: str | None
    summary_line: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "enqueued_at": self.enqueued_at,
            "estimated_time_to_merge_human": self.estimated_time_to_merge_human,
            "estimated_time_to_merge_seconds": self.estimated_time_to_merge_seconds,
            "latest_merge_group_run_conclusion": self.latest_merge_group_run_conclusion,
            "latest_merge_group_run_status": self.latest_merge_group_run_status,
            "latest_merge_group_run_url": self.latest_merge_group_run_url,
            "position": self.position,
            "pr_merge_state_status": self.pr_merge_state_status,
            "pr_merged": self.pr_merged,
            "pr_number": self.pr_number,
            "pr_state": self.pr_state,
            "queue_url": self.queue_url,
            "queued": self.queued,
            "state": self.state,
            "summary_line": self.summary_line,
        }


def evaluate_status_data(
    graphql_data: dict[str, Any],
    pr_number: int,
    actions_runs: list[dict[str, Any]] | None = None,
) -> MergeQueueStatus:
    """Evaluate raw GraphQL repository payload and Actions runs into MergeQueueStatus."""
    repository = graphql_data.get("data", {}).get("repository") or graphql_data.get("repository") or {}
    pr_obj = repository.get("pullRequest")
    if pr_obj is None:
        raise ValueError(f"Pull request #{pr_number} not found in repository.")

    pr_state = str(pr_obj.get("state") or "OPEN")
    pr_merged = bool(pr_obj.get("merged"))
    merge_state_status = pr_obj.get("mergeStateStatus")
    is_in_mq = bool(pr_obj.get("isInMergeQueue"))
    mq_entry = pr_obj.get("mergeQueueEntry")

    mq_obj = repository.get("mergeQueue") or {}
    queue_url = mq_obj.get("url")
    next_eta = mq_obj.get("nextEntryEstimatedTimeToMerge")

    position: int | None = None
    state: str | None = None
    enqueued_at: str | None = None
    eta_seconds: int | None = None
    head_commit: dict[str, Any] | None = None

    if isinstance(mq_entry, dict):
        position = mq_entry.get("position")
        state = mq_entry.get("state")
        enqueued_at = mq_entry.get("enqueuedAt")
        eta_seconds = mq_entry.get("estimatedTimeToMerge")
        head_commit = mq_entry.get("headCommit")
    elif is_in_mq:
        # Check entries on mergeQueue object
        nodes = mq_obj.get("entries", {}).get("nodes", [])
        for node in nodes:
            if isinstance(node, dict) and node.get("pullRequest", {}).get("number") == pr_number:
                position = node.get("position")
                state = node.get("state")
                enqueued_at = node.get("enqueuedAt")
                eta_seconds = node.get("estimatedTimeToMerge")
                break
        if position is None:
            # isInMergeQueue is true but position could not be resolved from entry
            state = "QUEUED"
            if next_eta is not None:
                eta_seconds = next_eta

    # Check for merge_group workflow run
    run_url: str | None = None
    run_status: str | None = None
    run_conclusion: str | None = None

    if head_commit and isinstance(head_commit, dict):
        check_suites = head_commit.get("checkSuites", {}).get("nodes", [])
        for cs in check_suites:
            if isinstance(cs, dict):
                wf_run = cs.get("workflowRun")
                if isinstance(wf_run, dict) and wf_run.get("url"):
                    run_url = wf_run.get("url")
                    run_status = cs.get("status")
                    run_conclusion = cs.get("conclusion")
                    break

    if not run_url and actions_runs:
        matched_run = find_latest_merge_group_run(actions_runs, pr_number)
        if matched_run:
            run_url = matched_run.get("html_url") or matched_run.get("url")
            run_status = matched_run.get("status")
            run_conclusion = matched_run.get("conclusion")

    eta_human = format_eta_human(eta_seconds)
    summary_line = build_summary_line(
        pr_number=pr_number,
        queued=is_in_mq,
        position=position,
        state=state,
        eta_human=eta_human,
        run_url=run_url,
        pr_state=pr_state,
        pr_merged=pr_merged,
        merge_state_status=merge_state_status,
    )

    return MergeQueueStatus(
        pr_number=pr_number,
        queued=is_in_mq,
        position=position,
        state=state,
        enqueued_at=enqueued_at,
        estimated_time_to_merge_seconds=eta_seconds,
        estimated_time_to_merge_human=eta_human,
        latest_merge_group_run_url=run_url,
        latest_merge_group_run_status=run_status,
        latest_merge_group_run_conclusion=run_conclusion,
        pr_state=pr_state,
        pr_merged=pr_merged,
        pr_merge_state_status=merge_state_status,
        queue_url=queue_url,
        summary_line=summary_line,
    )


def fetch_live_status(
    pr_number: int,
    repo: str,
    branch: str = "main",
    token: str | None = None,
    timeout: int = 30,
) -> MergeQueueStatus:
    """Query GitHub GraphQL and Actions APIs for live merge queue status."""
    if "/" not in repo:
        raise ValueError(f"Invalid repository '{repo}'. Expected 'owner/name'.")
    owner, name = repo.split("/", 1)

    cmd = [
        "gh",
        "api",
        "graphql",
        "-f",
        f"query={GRAPHQL_PR_MQ_QUERY}",
        "-f",
        f"owner={owner}",
        "-f",
        f"name={name}",
        "-F",
        f"number={pr_number}",
        "-f",
        f"branch={branch}",
    ]
    env = _gh_env(token)
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("`gh` CLI tool is required but not installed or not on PATH.") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"GraphQL request timed out after {timeout}s.") from exc

    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        err_msg = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(f"Failed to parse GraphQL response (exit {proc.returncode}): {err_msg}") from exc

    # Check GraphQL errors
    if "errors" in data and not data.get("data", {}).get("repository", {}).get("pullRequest"):
        errors = data.get("errors", [])
        msgs = [e.get("message", "") for e in errors if isinstance(e, dict)]
        if any("Could not resolve to a PullRequest" in m for m in msgs):
            raise ValueError(f"Pull request #{pr_number} not found in repository {repo}.")
        raise RuntimeError(f"GraphQL error: {'; '.join(msgs)}")

    # Fetch merge_group workflow runs (best effort)
    actions_runs: list[dict[str, Any]] = []
    runs_path = f"repos/{owner}/{name}/actions/runs?event=merge_group&per_page=30"
    runs_cmd = ["gh", "api", runs_path]
    try:
        runs_proc = subprocess.run(
            runs_cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=timeout,
            check=False,
        )
        if runs_proc.returncode == 0 and runs_proc.stdout.strip():
            runs_data = json.loads(runs_proc.stdout)
            if isinstance(runs_data, dict):
                actions_runs = runs_data.get("workflow_runs", [])
    except Exception:
        actions_runs = []

    if not actions_runs:
        try:
            rl_cmd = [
                "gh",
                "run",
                "list",
                "-R",
                f"{owner}/{name}",
                "--event",
                "merge_group",
                "-L",
                "30",
                "--json",
                "url,headBranch,status,conclusion,createdAt,name",
            ]
            rl_proc = subprocess.run(
                rl_cmd,
                capture_output=True,
                text=True,
                env=env,
                timeout=timeout,
                check=False,
            )
            if rl_proc.returncode == 0 and rl_proc.stdout.strip():
                rl_data = json.loads(rl_proc.stdout)
                if isinstance(rl_data, list):
                    actions_runs = rl_data
        except Exception:
            actions_runs = []

    return evaluate_status_data(data, pr_number, actions_runs)


def render_output(
    status: MergeQueueStatus,
    *,
    json_only: bool = False,
    line_only: bool = False,
) -> str:
    """Render output according to format flags."""
    json_str = json.dumps(status.to_dict(), indent=2, sort_keys=True)
    if json_only:
        return json_str
    if line_only:
        return status.summary_line
    # Default: emit JSON followed by the single human summary line
    return f"{json_str}\n{status.summary_line}"


def check_and_report_pr_status(
    pr: str | int,
    repo: str | None = None,
    branch: str = "main",
    json_only: bool = False,
    line_only: bool = False,
    fixture_file: str | Path | None = None,
    actions_fixture_file: str | Path | None = None,
    token: str | None = None,
) -> int:
    """Programmatic entry point for checking and printing PR merge queue status."""
    try:
        pr_number = parse_pr_identifier(pr)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    resolved_repo = resolve_repository(repo)

    if fixture_file:
        try:
            with open(fixture_file, encoding="utf-8") as f:
                fix_data = json.load(f)
        except Exception as exc:
            print(f"Error reading fixture {fixture_file}: {exc}", file=sys.stderr)
            return 1

        actions_runs: list[dict[str, Any]] = []
        if actions_fixture_file:
            try:
                with open(actions_fixture_file, encoding="utf-8") as f:
                    act_data = json.load(f)
                    if isinstance(act_data, dict):
                        actions_runs = act_data.get("workflow_runs") or act_data.get("runs") or []
                    elif isinstance(act_data, list):
                        actions_runs = act_data
            except Exception as exc:
                print(f"Error reading actions fixture {actions_fixture_file}: {exc}", file=sys.stderr)
                return 1
        elif isinstance(fix_data, dict) and "actions_runs" in fix_data:
            actions_runs = fix_data["actions_runs"]

        try:
            status = evaluate_status_data(fix_data, pr_number, actions_runs)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
    else:
        auth_token = token or os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        try:
            status = fetch_live_status(
                pr_number=pr_number,
                repo=resolved_repo,
                branch=branch,
                token=auth_token,
            )
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        except RuntimeError as exc:
            print(f"Error querying GitHub: {exc}", file=sys.stderr)
            return 1

    output = render_output(status, json_only=json_only, line_only=line_only)
    print(output)
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Check GitHub Merge Queue status, position, ETA, and CI run for a pull request (#7814 item 13).",
    )
    parser.add_argument(
        "pr",
        help="Pull request number, branch, or URL (e.g. 7814, #7814, https://github.com/.../pull/7814).",
    )
    parser.add_argument(
        "--repo",
        default=None,
        help="GitHub owner/repo (default: detected from git origin or GITHUB_REPOSITORY).",
    )
    parser.add_argument(
        "--branch",
        default="main",
        help="Target base branch for merge queue (default: %(default)s).",
    )
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output structured JSON only.",
    )
    output_group.add_argument(
        "--line",
        "--text",
        action="store_true",
        dest="line_output",
        help="Output single human-readable line only.",
    )
    parser.add_argument(
        "--fixture",
        dest="fixture_file",
        default=None,
        help="Path to recorded JSON fixture for offline evaluation.",
    )
    parser.add_argument(
        "--actions-fixture",
        dest="actions_fixture_file",
        default=None,
        help="Path to recorded GitHub Actions runs fixture file.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI main function."""
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    return check_and_report_pr_status(
        pr=args.pr,
        repo=args.repo,
        branch=args.branch,
        json_only=args.json_output,
        line_only=args.line_output,
        fixture_file=args.fixture_file,
        actions_fixture_file=args.actions_fixture_file,
    )


if __name__ == "__main__":
    sys.exit(main())
