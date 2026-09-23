#!/usr/bin/env python3
"""Record a completed branch-pinned cross-family review on its exact PR head."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import re
import subprocess
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.fleet_comms.review_publication import DEFAULT_STATUS_CONTEXT
from scripts.fleet_comms.review_publisher import post_commit_status
from scripts.orchestration.integration_sweep import (
    MARKER_PREFIX,
    SHA,
    TRUSTED_ASSOCIATIONS,
    GitHubAdapter,
    SweepError,
    parse_marker,
)
from scripts.review.reviewer_resolver import (
    CURSOR_AUTO_UNION_FAMILY,
    UNRESOLVED_AUTHOR_FAMILIES,
    resolve_author_family,
    resolve_family,
)

VERDICT_LINE = re.compile(r"(?im)^\s*VERDICT:\s*(APPROVE|APPROVED|REQUEST_CHANGES|CHANGES_REQUESTED|BLOCKED)\b")
NORMALIZED = {
    "APPROVE": "APPROVED",
    "APPROVED": "APPROVED",
    "REQUEST_CHANGES": "CHANGES_REQUESTED",
    "CHANGES_REQUESTED": "CHANGES_REQUESTED",
    "BLOCKED": "BLOCKED",
}
TASK_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*(?:/[A-Za-z0-9][A-Za-z0-9._-]*)*\Z")
MAX_COMMENT_BYTES = 65_000


class RecordError(RuntimeError):
    """A review cannot be bound to a trustworthy exact-head verdict."""


def normalize_verdict(reply: str) -> str:
    tokens = {NORMALIZED[token.upper()] for token in VERDICT_LINE.findall(reply)}
    if len(tokens) != 1:
        raise RecordError("review reply has missing or ambiguous VERDICT token")
    return tokens.pop()


def _run_json(args: list[str], *, input_text: str | None = None) -> Any:
    try:
        process = subprocess.run(args, input=input_text, capture_output=True, text=True, check=False, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RecordError("GitHub lookup or publication unavailable") from exc
    if process.returncode:
        raise RecordError((process.stderr or process.stdout or "GitHub command failed")[:500])
    try:
        return json.loads(process.stdout)
    except ValueError as exc:
        raise RecordError("GitHub returned invalid JSON") from exc


def _pages(args: list[str]) -> list[dict[str, Any]]:
    data = _run_json([*args, "--paginate", "--slurp"])
    if not isinstance(data, list) or not all(isinstance(page, list) for page in data):
        raise RecordError("paginated GitHub data incomplete")
    items = [item for page in data for item in page]
    if not all(isinstance(item, dict) for item in items):
        raise RecordError("paginated GitHub data malformed")
    return items


def author_families(repository: str, pr_number: int, task_root: Path) -> set[str]:
    """Resolve every base..head commit from explicit model attribution, fail closed."""
    commits = _pages(["gh", "api", f"repos/{repository}/pulls/{pr_number}/commits?per_page=100"])
    if not commits:
        raise RecordError("PR commit set unavailable")
    families = set()
    for entry in commits:
        message = (entry.get("commit") or {}).get("message")
        if not isinstance(message, str):
            raise RecordError("commit message unavailable")
        trailers = re.findall(r"(?m)^X-Agent:\s*([^\s]+)\s*$", message)
        if len(trailers) != 1 or "/" not in trailers[0]:
            raise RecordError("author model unknown: missing explicit X-Agent model trailer")
        harness, model = trailers[0].split("/", 1)
        if not harness or not model:
            raise RecordError("author model unknown")
        family = resolve_author_family(f"{harness}:{model}" if harness == "cursor" else model)
        if family in UNRESOLVED_AUTHOR_FAMILIES or family == "unknown":
            # The common X-Agent trailer names a task, not a model. Resolve
            # that task's recorded model; the trailer alone is insufficient.
            if not TASK_ID.fullmatch(model):
                raise RecordError("author model unknown")
            try:
                author_task = json.loads((task_root / f"{model}.json").read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                raise RecordError("author task provenance unavailable") from exc
            if author_task.get("repository") != repository or not str(author_task.get("agent") or "").startswith(
                harness
            ):
                raise RecordError("author task provenance conflicts with commit trailer")
            if harness.startswith("cursor"):
                if author_task.get("resolved_model_known") is not True:
                    raise RecordError("author family unknown")
                author_model = author_task.get("resolved_model")
            else:
                author_model = author_task.get("model")
            family = resolve_author_family(str(author_model or ""))
        if family in UNRESOLVED_AUTHOR_FAMILIES or family == "unknown":
            raise RecordError("author family unknown")
        if family == CURSOR_AUTO_UNION_FAMILY:
            raise RecordError("author family mixed or unknown")
        families.add(family)
    return families


def _repo_root() -> Path:
    result = subprocess.run(["git", "rev-parse", "--git-common-dir"], capture_output=True, text=True, check=True)
    return Path(result.stdout.strip()).resolve().parent


@contextmanager
def sha_lock(repository: str, sha: str, lock_root: Path):
    lock_root.mkdir(parents=True, exist_ok=True)
    name = hashlib.sha256(f"{repository}\0{sha}".encode()).hexdigest() + ".lock"
    with (lock_root / name).open("a+") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)


def build_comment(*, sha: str, task_id: str, started: str, verdict: str, model: str, family: str, reply: str) -> str:
    if MARKER_PREFIX in reply:
        raise RecordError("review reply contains reserved verdict marker")
    marker = f"<!-- cf-verdict v1 sha={sha} task={task_id} started={started} verdict={verdict} model={model} family={family} -->"
    prefix = (
        "### Cross-family review\n"
        f"head: {sha}\n"
        f"Reviewer family: {family}\n"
        f"VERDICT: {verdict}\n"
        f"Reviewer model: {model}\n"
        f"Task id: {task_id}\n\n"
        "<details><summary>Reviewer's reply</summary>\n\n"
    )
    suffix = f"\n\n</details>\n\n{marker}"
    available = MAX_COMMENT_BYTES - len((prefix + suffix).encode())
    if available < 0:
        raise RecordError("comment metadata exceeds GitHub limit")
    if len(reply.encode()) > available:
        flag = "\n\n[Review reply truncated to fit GitHub's comment limit.]"
        available -= len(flag.encode())
        if available < 0:
            raise RecordError("comment metadata exceeds GitHub limit")
        reply = reply.encode()[:available].decode("utf-8", errors="ignore") + flag
    return prefix + reply + suffix


def _task(task_id: str, task_root: Path) -> tuple[dict[str, Any], str]:
    if not TASK_ID.fullmatch(task_id):
        raise RecordError("invalid task id")
    task_path = task_root / f"{task_id}.json"
    result_path = task_root / f"{task_id}.result"
    try:
        task = json.loads(task_path.read_text(encoding="utf-8"))
        reply = result_path.read_text(encoding="utf-8")
    except (OSError, ValueError) as exc:
        raise RecordError("review task record or reply unavailable") from exc
    if not isinstance(task, dict):
        raise RecordError("review task record malformed")
    if task.get("status") != "done":
        raise RecordError("review task is not done")
    if not task.get("worktree_branch"):
        raise RecordError("review was not branch-pinned; re-run with --branch <PR head ref>")
    return task, reply


def _pr(repository: str, branch: str, number: int | None) -> dict[str, Any]:
    if number is None:
        matches = _run_json(
            [
                "gh",
                "pr",
                "list",
                "--repo",
                repository,
                "--state",
                "open",
                "--head",
                branch,
                "--limit",
                "2",
                "--json",
                "number,headRefOid,headRefName",
            ]
        )
        if not isinstance(matches, list) or len(matches) != 1:
            raise RecordError("branch must identify exactly one open PR; pass --pr N")
        return matches[0]
    data = _run_json(
        ["gh", "pr", "view", str(number), "--repo", repository, "--json", "number,headRefOid,headRefName,state"]
    )
    if not isinstance(data, dict) or data.get("state") != "OPEN":
        raise RecordError("PR is not open")
    return data


def record(
    task_id: str, *, pr_number: int | None = None, task_root: Path | None = None, lock_root: Path | None = None
) -> dict[str, Any]:
    root = _repo_root() if task_root is None or lock_root is None else None
    task_root = task_root or root / "batch_state" / "tasks"
    lock_root = lock_root or root / "batch_state" / "locks"
    task, reply = _task(task_id, task_root)
    repository = task.get("repository")
    branch = task["worktree_branch"]
    sha = task.get("worktree_base_sha")
    if not isinstance(repository, str) or "/" not in repository:
        raise RecordError("review repository unavailable")
    if not isinstance(sha, str) or not SHA.fullmatch(sha):
        raise RecordError("reviewed SHA missing or invalid")
    model = task.get("resolved_model") if task.get("agent") == "cursor" else task.get("model")
    if task.get("agent") == "cursor" and task.get("resolved_model_known") is not True:
        raise RecordError("Cursor reviewer model unknown")
    if not isinstance(model, str) or not model or re.search(r"\s", model):
        raise RecordError("reviewer model unknown")
    family = resolve_family(model)
    if family in UNRESOLVED_AUTHOR_FAMILIES or family == "unknown":
        raise RecordError("reviewer family unknown")
    verdict = normalize_verdict(reply)
    started_dt = datetime.fromisoformat(str(task.get("started_at") or "").replace("Z", "+00:00"))
    if started_dt.tzinfo is None:
        raise RecordError("review start timestamp missing timezone")
    started = started_dt.astimezone(UTC).isoformat(timespec="microseconds")
    pr = _pr(repository, branch, pr_number)
    if pr.get("headRefName") != branch:
        raise RecordError("review branch does not match PR head ref")
    if pr.get("headRefOid") != sha:
        raise RecordError("PR head moved since review; re-run exact-head review")
    number = pr.get("number")
    if not isinstance(number, int) or number < 1:
        raise RecordError("PR number unavailable")
    families = author_families(repository, number, task_root)
    if family in families:
        raise RecordError("reviewer family equals an author family")
    adapter = GitHubAdapter(Path.cwd())
    login = adapter.identity()
    comment = build_comment(
        sha=sha, task_id=task_id, started=started, verdict=verdict, model=model, family=family, reply=reply
    )
    posted = False
    with sha_lock(repository, sha, lock_root):
        # The PR may move while an earlier recorder owns the lock.
        current = _pr(repository, branch, number)
        if current.get("headRefOid") != sha:
            raise RecordError("PR head moved before publication")
        try:
            comments = adapter.comments(repository, number)
        except SweepError as exc:
            raise RecordError(f"comment lookup failed: {exc}") from exc
        existing = None
        for item in comments:
            body = item.get("body")
            if not isinstance(body, str):
                raise RecordError("comment lookup partial")
            if MARKER_PREFIX in body:
                marker = parse_marker(body)
                if marker is None and f"sha={sha}" in body:
                    raise RecordError("unparseable marker on reviewed SHA")
                if (
                    marker
                    and marker["sha"] == sha
                    and marker["task"] == task_id
                    and item.get("user", {}).get("login") == login
                    and item.get("author_association") in TRUSTED_ASSOCIATIONS
                ):
                    if (
                        marker["started"] != started
                        or marker["verdict"] != verdict
                        or marker["model"] != model
                        or marker["family"] != family
                        or item.get("created_at") != item.get("updated_at")
                    ):
                        raise RecordError("existing verdict marker was edited or conflicts with task")
                    existing = item
                    break
        if existing is None:
            data = _run_json(
                ["gh", "api", "-X", "POST", f"repos/{repository}/issues/{number}/comments", "--input", "-"],
                input_text=json.dumps({"body": comment}),
            )
            comment_id = data.get("id") if isinstance(data, dict) else None
            if not isinstance(comment_id, int):
                raise RecordError("comment post response lacked id; retry to reconcile")
            readback = _run_json(["gh", "api", f"repos/{repository}/issues/comments/{comment_id}"])
            if (
                not isinstance(readback, dict)
                or readback.get("body") != comment
                or readback.get("user", {}).get("login") != login
                or readback.get("author_association") not in TRUSTED_ASSOCIATIONS
                or readback.get("created_at") != readback.get("updated_at")
            ):
                raise RecordError("comment readback mismatch; publication state unknown")
            posted = True
        description = f"VERDICT: {verdict} {family} {task_id}"[:140]
        try:
            post_commit_status(
                repository=repository,
                head_sha=sha,
                state="success" if verdict == "APPROVED" else "failure",
                context=DEFAULT_STATUS_CONTEXT,
                description=description,
            )
            status = "posted"
        except Exception as exc:
            status = f"failed: {exc}"
    return {
        "pr": number,
        "head": sha,
        "task": task_id,
        "verdict": verdict,
        "comment": "posted" if posted else "existing",
        "status": status,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id", required=True, help="Completed branch-pinned review task id")
    parser.add_argument("--pr", type=int, help="Open PR number; otherwise resolve from review branch")
    args = parser.parse_args(argv)
    try:
        result = record(args.task_id, pr_number=args.pr)
    except (RecordError, SweepError, ValueError) as exc:
        print(f"CF verdict refused: {exc}")
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "posted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
