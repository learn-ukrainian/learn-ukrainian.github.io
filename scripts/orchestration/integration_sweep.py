#!/usr/bin/env python3
"""Read-only, exact-head PR landing report. The local keeper owns mutations (#8564)."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.gh_merge_queue_status import GRAPHQL_PR_MQ_QUERY

Runner = Callable[[list[str]], str]
SHA = re.compile(r"[0-9a-f]{40}\Z")
MARKER = re.compile(
    r"<!-- cf-verdict v1 sha=(?P<sha>[0-9a-f]{40}) task=(?P<task>[^\s]+) "
    r"started=(?P<started>[^\s]+) verdict=(?P<verdict>APPROVED|CHANGES_REQUESTED|BLOCKED) "
    r"model=(?P<model>[^\s]+) family=(?P<family>[^\s]+) -->\Z"
)
MARKER_PREFIX = "<!-- cf-verdict"
TRUSTED_ASSOCIATIONS = frozenset({"OWNER", "MEMBER", "COLLABORATOR"})
REJECTED = frozenset({"CHANGES_REQUESTED", "BLOCKED"})
SUCCESSFUL = frozenset({"SUCCESS", "NEUTRAL", "SKIPPED"})
REQUIRED_CHECKS = ("CI Gate",)
DEFAULT_GH_TIMEOUT_SECONDS = 60.0


class SweepError(RuntimeError):
    """An authoritative lookup failed; no landing decision can follow."""


@dataclass(frozen=True)
class Verdict:
    state: str
    task: str | None = None
    model: str | None = None
    family: str | None = None
    started: datetime | None = None
    untrusted_markers: tuple[str, ...] = ()


@dataclass(frozen=True)
class PRReport:
    number: int
    head: str
    observed_at: str
    state: str
    blockers: tuple[str, ...]
    untrusted_markers: tuple[str, ...] = ()


def _timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(UTC) if parsed.tzinfo else None


def _field(comment: Mapping[str, Any], *keys: str) -> Any:
    return next((comment[key] for key in keys if key in comment), None)


def _author_login(comment: Mapping[str, Any]) -> str | None:
    author = _field(comment, "user", "author")
    if isinstance(author, Mapping):
        login = author.get("login")
        return login if isinstance(login, str) else None
    return None


def parse_marker(body: str) -> dict[str, str] | None:
    """Accept only an intact recorder comment with one terminal marker."""
    if body.count(MARKER_PREFIX) != 1 or not body.startswith("### Cross-family review\n"):
        return None
    last = body.rstrip("\n").split("\n")[-1]
    match = MARKER.fullmatch(last)
    if match is None:
        return None
    item = match.groupdict()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}(?:Z|\+00:00)", item["started"]):
        return None
    if _timestamp(item["started"]) is None:
        return None
    if (
        f"head: {item['sha']}" not in body
        or f"Reviewer family: {item['family']}" not in body
        or f"VERDICT: {item['verdict']}" not in body
        or f"Reviewer model: {item['model']}" not in body
        or f"Task id: {item['task']}" not in body
    ):
        return None
    return item


def lookup_verdict(
    comments: Sequence[Mapping[str, Any]] | None,
    sha: str,
    authenticated_login: str | None,
    *,
    complete: bool = True,
) -> Verdict:
    """Resolve the latest review start for one SHA; malformed or edited evidence poisons it."""
    if not complete or not isinstance(comments, Sequence) or isinstance(comments, (str, bytes)):
        return Verdict("unknown")
    if not SHA.fullmatch(sha) or not authenticated_login:
        return Verdict("unknown")
    candidates: list[tuple[datetime, int, dict[str, str]]] = []
    untrusted: list[str] = []
    legacy = False
    other_head = False
    for index, comment in enumerate(comments):
        if not isinstance(comment, Mapping):
            return Verdict("unknown")
        body = comment.get("body")
        if not isinstance(body, str):
            return Verdict("unknown")
        if MARKER_PREFIX not in body:
            if re.search(r"(?im)^\s*VERDICT:", body):
                legacy = True
            continue
        marker = parse_marker(body)
        login = _author_login(comment)
        association = _field(comment, "author_association", "authorAssociation")
        if login != authenticated_login or association not in TRUSTED_ASSOCIATIONS:
            untrusted.append(str(_field(comment, "id", "databaseId") or index))
            continue
        if marker is None:
            return Verdict("unknown", untrusted_markers=tuple(untrusted))
        if marker["sha"] != sha:
            other_head = True
            continue
        created = _timestamp(_field(comment, "created_at", "createdAt"))
        updated = _timestamp(_field(comment, "updated_at", "updatedAt"))
        if created is None or updated is None or created != updated:
            return Verdict("unknown", untrusted_markers=tuple(untrusted))
        candidates.append((_timestamp(marker["started"]), index, marker))
    if not candidates:
        state = "CF-unrecorded" if legacy else "CF-stale" if other_head else "needs-CF"
        return Verdict(state, untrusted_markers=tuple(untrusted))
    latest_start = max(item[0] for item in candidates)
    tied = [item for item in candidates if item[0] == latest_start]
    # At a true timestamp tie any rejection wins, irrespective of comment arrival order.
    winner = next((item for item in tied if item[2]["verdict"] in REJECTED), tied[0])
    marker = winner[2]
    return Verdict(marker["verdict"], marker["task"], marker["model"], marker["family"], latest_start, tuple(untrusted))


def _check_blockers(pr: Mapping[str, Any], required: Sequence[str] = REQUIRED_CHECKS) -> list[str]:
    checks = pr.get("statusCheckRollup")
    if not isinstance(checks, list):
        return ["CI unknown"]
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for check in checks:
        if not isinstance(check, Mapping):
            return ["CI unknown"]
        name = check.get("name") or check.get("context")
        if isinstance(name, str) and name != "fleet/cross-family-review":
            grouped.setdefault(name, []).append(check)
    blockers = []
    for name in set(required) | set(grouped):
        versions = grouped.get(name, [])
        if not versions:
            blockers.append(f"CI pending {name}")
            continue
        dated = [(_timestamp(item.get("startedAt") or item.get("createdAt")), item) for item in versions]
        if any(timestamp is None for timestamp, _ in dated):
            blockers.append(f"CI unknown {name}")
            continue
        latest = max(dated, key=lambda pair: pair[0])[1]
        status = str(latest.get("status") or latest.get("state") or "").upper()
        outcome = str(latest.get("conclusion") or latest.get("state") or "").upper()
        if status not in {"COMPLETED", "SUCCESS", "FAILURE", "ERROR"}:
            blockers.append(f"CI pending {name}")
        elif outcome not in SUCCESSFUL:
            blockers.append(f"CI red {name}" if outcome else f"CI pending {name}")
    return sorted(blockers)


def classify_pr(pr: Mapping[str, Any], verdict: Verdict, *, queued: bool | None, observed_at: str) -> PRReport:
    """Expose a deterministic, importable state classifier for the queue keeper."""
    number = pr.get("number")
    head = pr.get("headRefOid")
    if not isinstance(number, int) or number < 1 or not isinstance(head, str) or not SHA.fullmatch(head):
        return PRReport(int(number or 0), str(head or "")[:12], observed_at, "unknown", ("invalid PR identity",))
    blockers: list[str] = []
    if pr.get("isDraft") is True:
        blockers.append("draft")
    if verdict.state != "APPROVED":
        blockers.append(verdict.state)
    blockers.extend(_check_blockers(pr))
    mergeable = str(pr.get("mergeable") or "").upper()
    if mergeable in {"CONFLICTING", "DIRTY"}:
        blockers.append("merge conflict")
    if queued is None:
        blockers.append("queue lookup unknown")
    if pr.get("isDraft") is True:
        state = "blocked draft"
    elif queued is True:
        state = "queued"
    elif pr.get("autoMergeRequest"):
        state = "armed"
    elif verdict.state == "unknown" or queued is None or "CI unknown" in " ".join(blockers):
        state = "CF-unknown" if verdict.state == "unknown" else "unknown"
    elif verdict.state in {"needs-CF", "CF-unrecorded", "CF-stale"}:
        state = verdict.state
    elif verdict.state in REJECTED:
        state = "CF-rejected"
    elif any(item.startswith("CI red") for item in blockers):
        state = "CI-red " + ", ".join(item.removeprefix("CI red ") for item in blockers if item.startswith("CI red"))
    elif any(item.startswith("CI pending") for item in blockers):
        state = "CI-pending"
    elif "merge conflict" in blockers:
        state = "blocked merge conflict"
    else:
        state = "ready"
    return PRReport(number, head[:12], observed_at, state, tuple(blockers), verdict.untrusted_markers)


class GitHubAdapter:
    """Read-only GitHub CLI boundary. Paged lookups use --slurp and reject malformed pages."""

    def __init__(self, repo_root: Path, *, runner: Runner | None = None) -> None:
        self.repo_root = repo_root.resolve()
        self._runner = runner or self._default_runner

    def _default_runner(self, args: list[str]) -> str:
        try:
            result = subprocess.run(
                args,
                cwd=self.repo_root,
                text=True,
                capture_output=True,
                timeout=DEFAULT_GH_TIMEOUT_SECONDS,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise SweepError(f"{' '.join(args[:4])} timed out after {DEFAULT_GH_TIMEOUT_SECONDS}s") from exc
        if result.returncode:
            raise SweepError((result.stderr or result.stdout or "GitHub lookup failed")[:1000])
        return result.stdout

    def _json(self, args: list[str]) -> Any:
        try:
            return json.loads(self._runner(args))
        except (ValueError, TypeError) as exc:
            raise SweepError("GitHub returned invalid JSON") from exc

    def identity(self) -> str:
        login = self._runner(["gh", "api", "user", "--jq", ".login"]).strip()
        if not login:
            raise SweepError("authenticated gh identity unavailable")
        return login

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
                "number,isDraft,headRefOid,headRefName,baseRefName,autoMergeRequest,statusCheckRollup,mergeable",
            ]
        )
        if not isinstance(payload, list) or len(payload) >= 1000 or not all(isinstance(item, dict) for item in payload):
            raise SweepError("open PR list partial or malformed")
        return payload

    def comments(self, repository: str, number: int) -> list[dict[str, Any]]:
        pages = self._json(
            ["gh", "api", f"repos/{repository}/issues/{number}/comments?per_page=100", "--paginate", "--slurp"]
        )
        if not isinstance(pages, list) or not all(isinstance(page, list) for page in pages):
            raise SweepError("PR comments pagination incomplete")
        comments = [item for page in pages for item in page]
        if not all(isinstance(item, dict) for item in comments):
            raise SweepError("PR comments malformed")
        return comments

    def queue_membership(self, repository: str, pr: Mapping[str, Any]) -> bool:
        owner, name = repository.split("/", 1)
        number = pr["number"]
        data = self._json(
            [
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
                f"number={number}",
                "-f",
                f"branch={pr.get('baseRefName') or 'main'}",
            ]
        )
        if not isinstance(data, dict) or data.get("errors"):
            raise SweepError("merge queue GraphQL lookup incomplete")
        repo = (data.get("data") or {}).get("repository")
        node = repo.get("pullRequest") if isinstance(repo, dict) else None
        if (
            not isinstance(node, dict)
            or node.get("headRefOid") != pr.get("headRefOid")
            or not isinstance(node.get("isInMergeQueue"), bool)
        ):
            raise SweepError("merge queue head moved or membership unavailable")
        return node["isInMergeQueue"]


def run(adapter: GitHubAdapter, repository: str, *, now: datetime | None = None) -> list[PRReport]:
    observed = (now or datetime.now(UTC)).isoformat(timespec="microseconds")
    prs = adapter.list_open_prs(repository)
    try:
        login = adapter.identity()
    except SweepError:
        login = None
    rows = []
    for pr in prs:
        number, head = pr.get("number"), pr.get("headRefOid")
        if not isinstance(number, int) or number < 1 or not isinstance(head, str) or not SHA.fullmatch(head):
            rows.append(classify_pr(pr, Verdict("unknown"), queued=None, observed_at=observed))
            continue
        try:
            verdict = lookup_verdict(adapter.comments(repository, number), head, login)
        except SweepError:
            verdict = Verdict("unknown")
        try:
            queued = adapter.queue_membership(repository, pr)
        except (SweepError, ValueError, KeyError):
            queued = None
        rows.append(classify_pr(pr, verdict, queued=queued, observed_at=observed))
    return rows


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="GitHub owner/repository")
    parser.add_argument("--report", action="store_true", help="Print the read-only PR state report")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text")
    parser.add_argument("--apply", action="store_true", help="Retired: automatic landing is owned by the local keeper")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    if args.apply:
        print("integration sweep refused: --apply is retired; this sweep is report-only")
        return 2
    try:
        rows = run(GitHubAdapter(args.repo_root), args.repo)
    except SweepError as exc:
        print(f"integration sweep refused: {exc}")
        return 1
    if args.json:
        print(json.dumps([asdict(row) for row in rows], sort_keys=True))
    else:
        for row in rows:
            blockers = ", ".join(row.blockers) or "none"
            untrusted = f" untrusted-marker={','.join(row.untrusted_markers)}" if row.untrusted_markers else ""
            print(
                f"#{row.number} head={row.head} observed_at={row.observed_at} state={row.state} blockers={blockers}{untrusted}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
