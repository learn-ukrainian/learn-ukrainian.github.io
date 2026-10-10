"""One durable CI recovery allowance shared by reruns and queue recovery."""

from __future__ import annotations

import json
import re
import sqlite3
import subprocess
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

from scripts.opsec.prepublish import PublishBlocked

MARKER = re.compile(r"<!-- ci-recovery-evidence\s+(\{.*?\})\s*-->", re.S)
SHA = re.compile(r"[0-9a-f]{40}\Z")
NON_CI_REMOVAL_REASONS = {"manual", "merge_conflict", "behind", "MANUAL", "MERGE_CONFLICT", "BEHIND"}


def ledger_path(cwd: Path) -> Path:
    """Anchor both callers to Git's common directory, never a worktree-local store."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        common = Path(result.stdout.strip())
        if not common.is_absolute() or not common.is_dir():
            raise ValueError
    except (OSError, ValueError, subprocess.SubprocessError):
        raise PublishBlocked("RECOVERY_RECORD_UNAVAILABLE: Git common directory unknown") from None
    return common / "ci-recovery.sqlite3"


def first_attempt(path: Path, repo: str, number: int, head: str) -> dict | None:
    """Read durable consumption, including the keeper's pre-migration allowance."""
    try:
        if path.exists():
            with closing(sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)) as db:
                row = db.execute(
                    "SELECT attempt FROM recovery WHERE repo=? AND pr=? AND head=?", (repo.lower(), number, head)
                ).fetchone()
                if row:
                    return json.loads(row[0])
        return _legacy_attempt(path, number, head)
    except (OSError, ValueError, AttributeError, sqlite3.Error):
        raise PublishBlocked("RECOVERY_RECORD_UNAVAILABLE: allowance unreadable") from None


def _legacy_attempt(path: Path, number: int, head: str) -> dict | None:
    legacy = path.parent.parent / "batch_state/merge_queue_keeper.json"
    if legacy.exists():
        state = json.loads(legacy.read_text())
        requeued = state.get("requeued", {})
        if not isinstance(requeued, dict):
            raise ValueError
        if f"{number}:{head}" in requeued:
            return {"action": "re-enqueue (legacy)", "at": requeued[f"{number}:{head}"]}
    return None


def queue_removal_at_head(data: dict | list[dict], head: str) -> bool:
    """Check every GitHub removal, requiring complete, readable pagination.

    Manual removals (including keeper holds), merge conflicts and behind-head
    removals are not CI recovery. They can have a null commit and need no
    failed-run evidence. Null CI removals and unknown null-commit reasons
    always require recovery. Force-push history cannot establish the removed
    head or clear recovery; only an explicit different beforeCommit.oid can
    establish that a removal was at another head.
    """
    try:
        pages = data if isinstance(data, list) else [data]
        if not pages:
            raise ValueError
        at_head, cursors = False, set()
        for index, page in enumerate(pages):
            if page.get("errors"):
                raise ValueError
            pull = page["data"]["repository"]["pullRequest"]
            if pull["headRefOid"] != head:
                raise ValueError
            removals = pull["removals"]
            nodes, info = removals["nodes"], removals["pageInfo"]
            # GitHub totalCount includes other timeline item types even with
            # itemTypes filtering. Only pageInfo establishes completeness.
            if not isinstance(nodes, list) or type(info["hasNextPage"]) is not bool:
                raise ValueError
            if info["hasNextPage"] != (index < len(pages) - 1):
                raise ValueError
            cursor = info["endCursor"]
            if nodes or info["hasNextPage"]:
                if not isinstance(cursor, str) or not cursor or cursor in cursors:
                    raise ValueError
                cursors.add(cursor)
            pushes = pull["pushes"]["nodes"]
            if not isinstance(pushes, list) or len(pushes) > 1:
                raise ValueError
            if pushes:
                push = pushes[0]
                pushed_at = datetime.fromisoformat(push["createdAt"].replace("Z", "+00:00"))
                if pushed_at.tzinfo is None:
                    raise ValueError
            for event in nodes:
                removed_at = datetime.fromisoformat(event["createdAt"].replace("Z", "+00:00"))
                if removed_at.tzinfo is None:
                    raise ValueError
                reason = event.get("reason")
                if reason in NON_CI_REMOVAL_REASONS:
                    continue
                commit = event["beforeCommit"]
                if commit is None:
                    at_head = True
                    continue
                removed_head = commit["oid"]
                if not isinstance(removed_head, str) or not SHA.fullmatch(removed_head):
                    raise ValueError
                at_head |= removed_head == head
        return at_head
    except (ValueError, KeyError, TypeError, AttributeError):
        raise PublishBlocked("RECOVERY_REMOVAL_UNKNOWN: GitHub removal head unreadable; enqueue refused") from None


def spent_reason(attempt: dict) -> str:
    """A typed refusal names the first attempt without exposing local paths."""
    return (
        f"RECOVERY_ALLOWANCE_SPENT: first={attempt['action']} at={attempt['at']} run={attempt.get('run_id', 'unknown')}"
    )


def evidence_from_comments(
    comments: list, number: int, head: str, *, authenticated_login: str, run_id: int | None = None
) -> dict:
    """Require the written evidence to already exist on this PR and exact head."""
    from scripts.orchestration.integration_sweep import TRUSTED_ASSOCIATIONS, _author_login, _field

    for comment in reversed(comments):
        if not isinstance(comment, dict) or type(comment.get("id")) is not int or comment["id"] <= 0:
            continue
        if (
            _author_login(comment) != authenticated_login
            or _field(comment, "author_association", "authorAssociation") not in TRUSTED_ASSOCIATIONS
        ):
            continue
        for match in MARKER.finditer(str(comment.get("body", ""))):
            try:
                evidence = json.loads(match[1])
            except ValueError:
                continue
            if not isinstance(evidence, dict):
                continue
            jobs = evidence.get("job_ids")
            if (
                type(evidence.get("pr")) is int
                and evidence["pr"] == number
                and evidence.get("head") == head
                and SHA.fullmatch(head)
                and type(evidence.get("run_id")) is int
                and evidence["run_id"] > 0
                and (run_id is None or evidence["run_id"] == run_id)
                and isinstance(jobs, list)
                and jobs
                and all(type(job) is int and job > 0 for job in jobs)
                and len(set(jobs)) == len(jobs)
                and isinstance(evidence.get("tested_sha"), str)
                and SHA.fullmatch(evidence["tested_sha"])
                and all(
                    isinstance(evidence.get(key), str) and evidence[key].strip()
                    for key in ("failure_evidence", "unrelated_to_diff")
                )
            ):
                return {**evidence, "comment_id": comment["id"]}
    raise PublishBlocked(
        "RECOVERY_EVIDENCE_MISSING: run/job IDs, tested SHA, failure evidence and diff diagnosis required on PR"
    )


def consume(path: Path, repo: str, number: int, head: str, action: str, evidence: dict) -> None:
    """Commit a reservation before mutation; uncertain/failed transport never refunds it."""
    try:
        with closing(sqlite3.connect(path, timeout=30)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                "CREATE TABLE IF NOT EXISTS recovery (repo TEXT, pr INTEGER, head TEXT, attempt TEXT NOT NULL, PRIMARY KEY (repo, pr, head))"
            )
            # The transaction serializes this read and insert across both paths.
            prior = _legacy_attempt(path, number, head)
            row = db.execute(
                "SELECT attempt FROM recovery WHERE repo=? AND pr=? AND head=?", (repo.lower(), number, head)
            ).fetchone()
            if row:
                prior = json.loads(row[0])
            if prior:
                raise PublishBlocked(spent_reason(prior))
            attempt = {**evidence, "action": action, "at": datetime.now(UTC).isoformat()}
            db.execute("INSERT INTO recovery VALUES (?, ?, ?, ?)", (repo.lower(), number, head, json.dumps(attempt)))
    except (OSError, ValueError, AttributeError, sqlite3.Error):
        raise PublishBlocked("RECOVERY_RECORD_UNAVAILABLE: reservation failed; mutation refused") from None
