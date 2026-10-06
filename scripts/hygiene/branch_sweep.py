"""List stale agent branches and delete only those with verifiable safe heads."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import subprocess
import sys
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

from scripts.common.git_context import UnsafeBranchNameError, sanitized_git_env, validate_plain_branch_name
from scripts.orchestration import reap_worktrees as reaper
from scripts.orchestration.task_family.git_safety import remote_protected_branches
from scripts.orchestration.worktree_claims import RELEASED_TASK_STATUSES

AGENTS = frozenset({"codex", "claude", "grok", "agy", "kimi", "cursor", "deepseek", "gemini", "glm"})
PROTECTED = frozenset({"main", "master", "gh-pages", "production"})
SHA_RE = re.compile(r"[0-9a-f]{40,64}\Z")
_ISSUE_NUMBER_RE = re.compile(r"(?<!\d)(\d{3,})(?!\d)")
_COMMIT_ISSUE_RE = re.compile(r"(?<![A-Za-z0-9])#(\d{3,})(?!\d)")
_MERGE_SUBJECT_RE = re.compile(r"^Merge pull request #(\d+)\b")
_SQUASH_SUBJECT_RE = re.compile(r"\(#(\d+)\)\s*$")
_HTTP_STATUS_RE = re.compile(r"HTTP/\d+(?:\.\d+)?\s+(\d+)")
_CLOCK_SKEW = timedelta(seconds=10)
LEDGER_PATH = Path("batch_state") / "branch-archive" / "evidence.jsonl"
_MERGED_PR_ABSENT = (
    "merged-pr evidence refused: branch tip is absent from origin; recovery needs the tip on GitHub"
)
_MERGED_PR_MISMATCH = "merged-pr evidence refused: remote tip does not equal the local tip"
_MERGED_PR_NEWER = "merged-pr evidence refused: a branch commit is newer than the closing merge"
PrLookup = Callable[[Path, str], tuple[list[reaper.PullRequestState], str | None]]


@dataclass(frozen=True)
class Branch:
    name: str
    remote_sha: str | None = None
    local_sha: str | None = None
    remote_date: int | None = None
    local_date: int | None = None


@dataclass(frozen=True)
class Decision:
    branch: str
    classification: str
    reason: str
    remote_sha: str | None
    local_sha: str | None
    age_days: int | None
    remote_deleted: bool = False
    local_deleted: bool = False
    evidence_kind: str | None = None
    evidence_detail: str | None = None


@dataclass(frozen=True)
class IssueClosure:
    """One readable issue timeline. ``closing_pr`` is the single merged closer, if any."""

    closing_pr: int | None


IssueLookup = Callable[[Path, int], tuple[IssueClosure | None, str | None]]


@dataclass
class _EvidenceCache:
    """Patch-ids and the one issue read, reused when ``--apply`` rechecks a branch."""

    patch_ids: dict[str, str | None] = field(default_factory=dict)
    issues: dict[int, tuple[IssueClosure | None, str | None]] = field(default_factory=dict)
    pr_commits: dict[int, list[str]] | None = None


class SweepError(RuntimeError):
    """A failed sweep with the decisions completed before the failure."""

    def __init__(self, message: str, decisions: list[Decision]) -> None:
        super().__init__(message)
        self.decisions = decisions


def _git(repo: Path, *args: str, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        env=sanitized_git_env(),
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )


def _checked(repo: Path, *args: str) -> str:
    result = _git(repo, *args)
    if result.returncode:
        raise RuntimeError(f"git {args[0]} failed: {(result.stderr or result.stdout).strip()}")
    return result.stdout


def _refs(repo: Path) -> list[Branch]:
    # NUL separates fields; Git ref names cannot contain NUL or a line feed.
    output = _checked(
        repo,
        "for-each-ref",
        "--format=%(refname)%00%(objectname)%00%(committerdate:unix)",
        "refs/remotes/origin",
        "refs/heads",
    )
    by_name: dict[str, dict[str, object]] = {}
    for line in output.splitlines():
        fields = line.split("\0")
        if len(fields) != 3:
            raise RuntimeError("git for-each-ref returned a malformed row")
        ref, sha, raw_date = fields
        if ref.startswith("refs/remotes/origin/"):
            kind, name = "remote", ref.removeprefix("refs/remotes/origin/")
        elif ref.startswith("refs/heads/"):
            kind, name = "local", ref.removeprefix("refs/heads/")
        else:
            continue
        if not SHA_RE.fullmatch(sha):
            raise RuntimeError("git for-each-ref returned an invalid SHA")
        row = by_name.setdefault(name, {"name": name})
        row[f"{kind}_sha"] = sha
        row[f"{kind}_date"] = int(raw_date) if raw_date.isdecimal() else None
    return [Branch(**by_name[name]) for name in sorted(by_name)]


def _candidate(name: str) -> bool:
    parts = name.split("/")
    if len(parts) == 1:
        return name.startswith("pr-")
    return parts[0] in AGENTS or parts[0] == "rescue"


def _valid(name: str, repo: Path) -> bool:
    try:
        return validate_plain_branch_name(name, repo_root=repo) == name
    except UnsafeBranchNameError:
        return False


def _active_tasks(repo: Path) -> set[str]:
    task_dir = reaper.control_plane_root(repo) / "batch_state" / "tasks"
    active: set[str] = set()
    for path in task_dir.glob("*.json"):
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise RuntimeError(f"cannot inspect task state {path.name}: {exc}") from exc
        if not isinstance(state, dict):
            raise RuntimeError(f"cannot inspect task state {path.name}: not an object")
        status = state.get("status")
        if isinstance(status, str) and status in RELEASED_TASK_STATUSES:
            continue
        for key in ("worktree_branch", "branch"):
            value = state.get(key)
            if isinstance(value, str):
                active.add(value)
        prep = state.get("worktree_prep")
        if isinstance(prep, dict) and isinstance(prep.get("branch"), str):
            active.add(prep["branch"])
        agent, task_id = state.get("agent"), state.get("task_id")
        if isinstance(agent, str) and isinstance(task_id, str):
            active.add(f"{agent}/{task_id}")
    return active


def _origin_head(repo: Path, branch: str) -> str | None:
    output = _checked(repo, "ls-remote", "--heads", "origin", f"refs/heads/{branch}")
    rows = output.splitlines()
    if not rows:
        return None
    if len(rows) != 1:
        raise RuntimeError("git ls-remote returned multiple heads")
    fields = rows[0].split("\t")
    if len(fields) != 2 or fields[1] != f"refs/heads/{branch}" or not SHA_RE.fullmatch(fields[0]):
        raise RuntimeError("git ls-remote returned an unexpected head")
    return fields[0]


def _age(branch: Branch) -> int | None:
    dates = [date for date in (branch.remote_date, branch.local_date) if date is not None]
    return max(0, int(datetime.now(UTC).timestamp() - max(dates)) // 86400) if dates else None


def _rescue(name: str) -> bool:
    return name == "rescue" or name.startswith("rescue/")


def _numbers(pattern: re.Pattern[str], text: str) -> list[int]:
    found: list[int] = []
    for raw in pattern.findall(text):
        number = int(raw)
        if number > 0 and number not in found:
            found.append(number)
    return found


def _issue_number(name: str, messages: list[str]) -> int | None:
    """The branch's issue: the only number in its name, else the only ``#N`` in its commits."""
    from_name = _numbers(_ISSUE_NUMBER_RE, name)
    if len(from_name) == 1:
        return from_name[0]
    from_messages: list[int] = []
    for message in messages:
        for number in _numbers(_COMMIT_ISSUE_RE, message):
            if number not in from_messages:
                from_messages.append(number)
    return from_messages[0] if len(from_messages) == 1 else None


def _rev_list(repo: Path, rev_range: str) -> list[str]:
    result = _git(repo, "rev-list", rev_range, timeout=60)
    if result.returncode:
        raise RuntimeError(f"git rev-list failed: {(result.stderr or result.stdout).strip()}")
    shas = [line for line in result.stdout.splitlines() if line]
    if any(not SHA_RE.fullmatch(sha) for sha in shas):
        raise RuntimeError("git rev-list returned an invalid SHA")
    return shas


def _parse_patch_ids(repo: Path, patch_text: str) -> dict[str, str]:
    if not patch_text.strip():
        return {}
    proc = subprocess.run(
        ["git", "patch-id", "--stable"],
        cwd=repo,
        env=sanitized_git_env(),
        input=patch_text,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    if proc.returncode:
        raise RuntimeError(f"git patch-id failed: {(proc.stderr or proc.stdout).strip()}")
    found: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        parts = line.split()
        if len(parts) != 2 or not SHA_RE.fullmatch(parts[1]):
            raise RuntimeError("git patch-id returned an unreadable row")
        found[parts[1]] = parts[0]
    return found


def _load_patch_ids(repo: Path, cache: dict[str, str | None], shas: list[str]) -> None:
    missing = [sha for sha in shas if sha not in cache]
    for start in range(0, len(missing), 40):
        chunk = missing[start : start + 40]
        log = _git(repo, "log", "-p", "--no-walk", "--pretty=format:%H", *chunk, timeout=120)
        if log.returncode:
            raise RuntimeError(f"git log failed: {(log.stderr or log.stdout).strip()}")
        found = _parse_patch_ids(repo, log.stdout)
        for sha in chunk:
            cache[sha] = found.get(sha)


def _patch_equivalent(repo: Path, cache: _EvidenceCache, base: str, tip: str) -> bool:
    """True when every commit since ``base`` has a stable patch-id on ``origin/main`` since ``base``."""
    unique = _rev_list(repo, f"{base}..{tip}")
    if not unique:
        return False
    on_main = _rev_list(repo, f"{base}..refs/remotes/origin/main")
    _load_patch_ids(repo, cache.patch_ids, unique + on_main)
    main_ids = {cache.patch_ids[sha] for sha in on_main if cache.patch_ids.get(sha)}
    return all(cache.patch_ids.get(sha) in main_ids for sha in unique)


def _committer_timestamps(repo: Path, revision: str) -> list[int]:
    result = _git(repo, "log", "--format=%ct", revision, timeout=60)
    if result.returncode:
        raise RuntimeError(f"git log failed: {(result.stderr or result.stdout).strip()}")
    stamps: list[int] = []
    for line in result.stdout.splitlines():
        if not line.isdecimal():
            raise RuntimeError("git log returned an unreadable committer date")
        stamps.append(int(line))
    return stamps


def _merge_committer_timestamp(repo: Path, sha: str) -> int:
    result = _git(repo, "log", "-1", "--format=%ct", sha, timeout=60)
    if result.returncode:
        raise RuntimeError(f"git log failed: {(result.stderr or result.stdout).strip()}")
    lines = [line for line in result.stdout.splitlines() if line]
    if len(lines) != 1 or not lines[0].isdecimal():
        raise RuntimeError("closing merge committer date is unreadable")
    return int(lines[0])


def _commit_messages(repo: Path, base: str, tip: str) -> list[str]:
    result = _git(repo, "log", "--format=%B%x1e", f"{base}..{tip}", timeout=60)
    if result.returncode:
        raise RuntimeError(f"git log failed: {(result.stderr or result.stdout).strip()}")
    return [part for part in result.stdout.split("\x1e") if part.strip()]


def _changed_files(repo: Path, *args: str) -> set[str]:
    result = _git(repo, *args, timeout=60)
    if result.returncode:
        raise RuntimeError(f"git {args[0]} failed: {(result.stderr or result.stdout).strip()}")
    return {line for line in result.stdout.splitlines() if line}


def _pr_merge_index(repo: Path, cache: _EvidenceCache) -> dict[int, list[str]]:
    if cache.pr_commits is not None:
        return cache.pr_commits
    result = _git(repo, "log", "--format=%H%x1f%s", "refs/remotes/origin/main", timeout=60)
    if result.returncode:
        raise RuntimeError(f"git log failed: {(result.stderr or result.stdout).strip()}")
    found: dict[int, list[str]] = {}
    for line in result.stdout.splitlines():
        sha, separator, subject = line.partition("\x1f")
        if not separator or not SHA_RE.fullmatch(sha):
            raise RuntimeError("git log returned an unreadable subject row")
        numbers: list[int] = []
        merge = _MERGE_SUBJECT_RE.search(subject)
        if merge:
            numbers.append(int(merge.group(1)))
        squash = _SQUASH_SUBJECT_RE.search(subject)
        if squash:
            numbers.append(int(squash.group(1)))
        for number in dict.fromkeys(numbers):
            bucket = found.setdefault(number, [])
            if sha not in bucket:
                bucket.append(sha)
    cache.pr_commits = found
    return found


def _parse_github_time(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    except ValueError:
        return None


def _closes_issue(text: str, issue: int) -> bool:
    return (
        re.search(
            rf"(?i)\b(?:close[ds]?|fix(?:e[ds])?|resolve[ds]?)\s*:?\s+"
            rf"(?:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)?#{issue}(?!\d)",
            text,
        )
        is not None
    )


def _title_mentions(title: str, issue: int) -> bool:
    return re.search(rf"(?<!\d)#{issue}(?!\d)", title) is not None


def _timeline_repository(item: dict[str, object]) -> str | None:
    """Owner/name from a timeline issue, or ``None`` when the payload does not name one."""
    repository = item.get("repository")
    if not isinstance(repository, dict):
        return None
    full_name = repository.get("full_name")
    if isinstance(full_name, str) and full_name.count("/") == 1:
        owner, name = full_name.split("/", 1)
        if owner and name:
            return f"{owner}/{name}"
    owner_field = repository.get("owner")
    login = owner_field.get("login") if isinstance(owner_field, dict) else None
    name = repository.get("name")
    if (
        isinstance(login, str)
        and isinstance(name, str)
        and login
        and name
        and "/" not in login
        and "/" not in name
    ):
        return f"{login}/{name}"
    return None


def _same_origin_repository(item: dict[str, object], origin: tuple[str, str]) -> bool:
    slug = _timeline_repository(item)
    if slug is None:
        return False
    return slug.casefold() == f"{origin[0]}/{origin[1]}".casefold()


def _split_http(raw: str) -> tuple[str, str] | None:
    for separator in ("\r\n\r\n", "\n\n"):
        index = raw.find(separator)
        if index != -1:
            return raw[:index], raw[index + len(separator) :]
    return None


def _parse_issue_timeline(
    raw: str,
    issue: int,
    *,
    origin: tuple[str, str],
) -> tuple[IssueClosure | None, str | None]:
    """Map one timeline response to a closure. Incomplete or malformed input is unreadable.

    A closing pull request counts only when ``source.issue.repository`` is this
    ``origin``. A fork can name the issue; that reference is not a closer.
    """
    parts = _split_http(raw)
    if parts is None:
        return None, "issue timeline has no HTTP header"
    headers, body = parts
    status = _HTTP_STATUS_RE.search(headers)
    if status is None:
        return None, "issue timeline has no HTTP status"
    if status.group(1) != "200":
        return None, f"issue timeline HTTP {status.group(1)}"
    for line in headers.splitlines():
        if line.lower().startswith("link:") and 'rel="next"' in line.lower():
            return None, "issue timeline is incomplete"
    try:
        events = json.loads(body or "null")
    except json.JSONDecodeError as exc:
        return None, f"issue timeline is not JSON: {exc}"
    if not isinstance(events, list):
        return None, "issue timeline is not a list"
    state = "unknown"
    final_closed: datetime | None = None
    last_reopen: datetime | None = None
    keyword: list[tuple[datetime, int]] = []
    titled: list[tuple[datetime, int]] = []
    for event in events:
        if not isinstance(event, dict):
            return None, "issue timeline row is not an object"
        kind = event.get("event")
        if kind in {"closed", "reopened"}:
            moment = _parse_github_time(event.get("created_at"))
            if moment is None:
                return None, f"issue timeline {kind} event has no timestamp"
            if kind == "reopened":
                state = "open"
                last_reopen = moment
                final_closed = None
            else:
                state = "closed"
                final_closed = moment
            continue
        if kind != "cross-referenced":
            continue
        source = event.get("source")
        item = source.get("issue") if isinstance(source, dict) else None
        if not isinstance(item, dict) or not isinstance(item.get("pull_request"), dict):
            continue
        # Forks cross-reference the same issue number. Only this repository can close it.
        if not _same_origin_repository(item, origin):
            continue
        number = item.get("number")
        if isinstance(number, bool) or not isinstance(number, int) or number <= 0:
            return None, "issue timeline pull request has no number"
        merged_at = _parse_github_time(item["pull_request"].get("merged_at"))
        if merged_at is None:
            continue
        title = item.get("title") if isinstance(item.get("title"), str) else ""
        body_text = item.get("body") if isinstance(item.get("body"), str) else ""
        if _closes_issue(f"{title}\n{body_text}", issue):
            keyword.append((merged_at, number))
        elif _title_mentions(title, issue):
            titled.append((merged_at, number))
    if state != "closed" or final_closed is None:
        return IssueClosure(None), None

    def in_episode(merged_at: datetime) -> bool:
        if merged_at > final_closed + _CLOCK_SKEW:
            return False
        return not (last_reopen is not None and merged_at <= last_reopen)

    def choose(candidates: list[tuple[datetime, int]]) -> int | None:
        eligible = [(moment, number) for moment, number in candidates if in_episode(moment)]
        if not eligible:
            return None
        latest = max(moment for moment, _number in eligible)
        numbers = {number for moment, number in eligible if moment == latest}
        return next(iter(numbers)) if len(numbers) == 1 else None

    closing = choose(keyword)
    if closing is None and not keyword:
        closing = choose(titled)
    return IssueClosure(closing), None


def _run_gh(repo: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    """One ``gh`` invocation. ``args`` follow the fixed ``gh`` executable.

    Color flags are removed so a captured body stays JSON.
    """
    env = sanitized_git_env()
    for name in ("CLICOLOR_FORCE", "FORCE_COLOR", "GH_FORCE_TTY"):
        env.pop(name, None)
    env["NO_COLOR"] = "1"
    env["GH_FORCE_TTY"] = "0"
    return subprocess.run(
        ["gh", *args],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def _query_issue_closure(repo: Path, issue: int) -> tuple[IssueClosure | None, str | None]:
    """One REST read of the issue timeline. Any failure is unreadable and authorizes nothing."""
    slug = reaper._github_owner_repo(repo)
    if slug is None:
        return None, "issue evidence unreadable: origin owner/repo could not be determined"
    owner, name = slug
    endpoint = f"repos/{owner}/{name}/issues/{issue}/timeline?per_page=100"
    try:
        proc = _run_gh(repo, ["api", "--include", "-X", "GET", endpoint])
    except (FileNotFoundError, subprocess.SubprocessError) as exc:
        return None, f"issue evidence unreadable: {exc}"
    if proc.returncode:
        detail = (proc.stderr or proc.stdout or "").strip().splitlines()
        return None, f"issue evidence unreadable: {detail[-1] if detail else proc.returncode}"
    closure, error = _parse_issue_timeline(proc.stdout or "", issue, origin=(owner, name))
    if error is not None:
        return None, f"issue evidence unreadable: {error}"
    return closure, None


def _issue_once(
    repo: Path,
    cache: _EvidenceCache,
    lookup: IssueLookup,
    issue: int,
) -> tuple[IssueClosure | None, str | None]:
    if issue not in cache.issues:
        cache.issues[issue] = lookup(repo, issue)
    return cache.issues[issue]


def _try_evidence(
    repo: Path,
    branch: Branch,
    tip: str,
    *,
    issue_lookup: IssueLookup,
    cache: _EvidenceCache,
) -> Decision | None:
    """Accept unique commits only by patch-id, or by a closed issue's merged pull request.

    Returns ``None`` when this path does not apply, so the caller keeps its existing reason.
    A ``rescue/`` branch can match patch-ids only. The issue timeline is read at most once.
    Merged-PR evidence also requires the tip on origin, a matching local tip when one
    exists, and no branch commit newer than the closing merge.
    """

    def decided(kind: str, reason: str, *, evidence_kind: str | None = None) -> Decision:
        return Decision(
            branch.name,
            kind,
            reason,
            branch.remote_sha,
            branch.local_sha,
            _age(branch),
            evidence_kind=evidence_kind,
            evidence_detail=reason if evidence_kind else None,
        )

    try:
        base = _checked(repo, "merge-base", "refs/remotes/origin/main", tip).strip()
        if not SHA_RE.fullmatch(base):
            return decided("report-only", "evidence check failed: merge-base is not a SHA")
        equivalent = _patch_equivalent(repo, cache, base, tip)
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        return decided("report-only", f"evidence check failed: {exc}")
    if equivalent:
        return decided(
            "delete-evidence",
            "every unique commit matches a stable patch-id on origin/main since the merge base",
            evidence_kind="patch-id",
        )
    # Rescue refs stay unless the patch-id proof above holds. File coverage is not enough.
    if _rescue(branch.name):
        return decided("report-only", "rescue branch requires patch-id evidence on origin/main")
    try:
        messages = [] if len(_numbers(_ISSUE_NUMBER_RE, branch.name)) == 1 else _commit_messages(repo, base, tip)
        issue = _issue_number(branch.name, messages)
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        return decided("report-only", f"evidence check failed: {exc}")
    if issue is None:
        return None
    # File coverage is not enough when GitHub never had this tip, or the local ref moved.
    if branch.remote_sha is None:
        return decided("report-only", _MERGED_PR_ABSENT)
    if tip != branch.remote_sha or (branch.local_sha is not None and branch.local_sha != branch.remote_sha):
        return decided("report-only", _MERGED_PR_MISMATCH)
    closure, error = _issue_once(repo, cache, issue_lookup, issue)
    if error is not None:
        return decided("report-only", f"evidence unreadable: {error}")
    if closure is None or closure.closing_pr is None:
        return decided("report-only", f"issue #{issue} has no closing merged pull request")
    try:
        merges = _pr_merge_index(repo, cache).get(closure.closing_pr, [])
        if len(merges) != 1:
            reason = (
                f"closing pull request #{closure.closing_pr} merge commit is not on origin/main"
                if not merges
                else f"closing pull request #{closure.closing_pr} has more than one merge commit on origin/main"
            )
            return decided("report-only", reason)
        merge = merges[0]
        branch_files = _changed_files(repo, "diff", "--name-only", "--no-renames", f"{base}...{tip}")
        if not branch_files:
            return decided("report-only", "branch changes no files")
        pull_files = _changed_files(
            repo,
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "--no-renames",
            "-r",
            "-m",
            "--first-parent",
            merge,
        )
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        return decided("report-only", f"evidence check failed: {exc}")
    if not branch_files <= pull_files:
        return decided("report-only", "merged PR files do not cover every branch file")
    try:
        # A later commit can change a covered file after the merge and still pass the file check.
        branch_dates = _committer_timestamps(repo, f"{base}..{tip}")
        if not branch_dates:
            return decided("report-only", "merged-pr evidence refused: branch committer dates are unreadable")
        if any(stamp > _merge_committer_timestamp(repo, merge) for stamp in branch_dates):
            return decided("report-only", _MERGED_PR_NEWER)
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        return decided("report-only", f"evidence check failed: {exc}")
    return decided(
        "delete-evidence",
        f"issue #{issue} closed by merged pull request #{closure.closing_pr} at {merge[:12]}; branch files covered",
        evidence_kind="merged-pr",
    )


def _classify(
    repo: Path,
    branch: Branch,
    *,
    worktree_branches: set[str],
    detached_heads: set[str],
    active_tasks: set[str],
    protected_branches: set[str],
    pr_lookup: PrLookup,
    issue_lookup: IssueLookup | None = None,
    evidence_cache: _EvidenceCache | None = None,
) -> Decision:
    name = branch.name

    def decision(
        kind: str,
        reason: str,
        *,
        evidence_kind: str | None = None,
        evidence_detail: str | None = None,
    ) -> Decision:
        return Decision(
            name,
            kind,
            reason,
            branch.remote_sha,
            branch.local_sha,
            _age(branch),
            evidence_kind=evidence_kind,
            evidence_detail=evidence_detail,
        )

    if name in protected_branches or not _candidate(name):
        return decision("protected", "outside agent/scratch candidate namespace or protected name")
    if not _valid(name, repo):
        return decision("report-only", "invalid or unsafe branch name")
    if name in worktree_branches:
        return decision("skipped-worktree", "registered worktree uses this branch")
    if (branch.remote_sha or branch.local_sha) in detached_heads:
        return decision("skipped-worktree", "detached worktree uses this branch tip")
    if name in active_tasks:
        return decision("skipped-live-task", "unreleased dispatch names this branch")
    if branch.remote_sha and branch.local_sha and branch.remote_sha != branch.local_sha:
        return decision("report-only", "local and remote tips differ")

    prs, error = pr_lookup(repo, name)
    if error is not None:
        return decision("report-only", f"PR lookup unavailable: {error}")
    if any(pr.state == "OPEN" for pr in prs):
        return decision("skipped-open-PR", "branch has an open PR")
    if any(pr.state not in {"MERGED", "CLOSED"} for pr in prs):
        return decision("report-only", "PR state is unknown")
    tip = branch.remote_sha or branch.local_sha
    if tip is None:
        return decision("report-only", "branch has no readable tip")
    if any(pr.state == "CLOSED" and pr.head_sha == tip for pr in prs):
        return decision("report-only", "closed unmerged PR head matches branch tip")
    if any(pr.state == "MERGED" and pr.head_sha == tip for pr in prs):
        return decision(
            "delete-merged",
            "merged PR head matches branch tip",
            evidence_kind="merged-head",
            evidence_detail="merged PR head matches branch tip",
        )
    main = _git(repo, "rev-parse", "--verify", "refs/remotes/origin/main")
    if main.returncode:
        return decision("report-only", "origin/main is unavailable")
    ancestor = _git(repo, "merge-base", "--is-ancestor", tip, main.stdout.strip())
    if ancestor.returncode == 0:
        return decision(
            "delete-ancestor",
            "branch tip is an ancestor of origin/main",
            evidence_kind="ancestor",
            evidence_detail="branch tip is an ancestor of origin/main",
        )
    if ancestor.returncode != 1:
        return decision("report-only", "ancestry check failed")
    evidence = _try_evidence(
        repo,
        branch,
        tip,
        issue_lookup=issue_lookup or _query_issue_closure,
        cache=evidence_cache if evidence_cache is not None else _EvidenceCache(),
    )
    if evidence is not None:
        return evidence
    if prs:
        return decision("report-only", "closed/merged PR head does not match branch tip; unique commits")
    return decision("report-only", "no PR and unique commits")


def sweep(
    repo: Path,
    *,
    apply: bool = False,
    pr_lookup: PrLookup = reaper._query_pr_states,
    protected_lookup: Callable[[Path], set[str]] = remote_protected_branches,
    issue_lookup: IssueLookup | None = None,
) -> list[Decision]:
    decisions: list[Decision] = []
    evidence_cache = _EvidenceCache()
    issues = issue_lookup or _query_issue_closure
    try:
        branches = _refs(repo)
        try:
            protected = PROTECTED | protected_lookup(repo)
            protection_error = None
        except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
            protected = PROTECTED
            protection_error = str(exc)
        worktrees = reaper.list_git_worktrees(repo)
        worktree_branches = {item.branch for item in worktrees if item.branch}
        detached_heads = {item.head for item in worktrees if item.detached and item.head}
        active = _active_tasks(repo)
        for branch in branches:
            if protection_error and _candidate(branch.name) and branch.name not in PROTECTED:
                decisions.append(
                    Decision(
                        branch.name,
                        "report-only",
                        f"branch protection query unavailable: {protection_error}",
                        branch.remote_sha,
                        branch.local_sha,
                        _age(branch),
                    )
                )
                continue
            verdict = _classify(
                repo,
                branch,
                worktree_branches=worktree_branches,
                detached_heads=detached_heads,
                active_tasks=active,
                protected_branches=protected,
                pr_lookup=pr_lookup,
                issue_lookup=issues,
                evidence_cache=evidence_cache,
            )
            if apply and verdict.classification.startswith("delete-"):
                # Recheck all volatile guards before each destructive call. In particular,
                # stale origin tracking refs cannot authorize deletion of a moved head.
                current_worktrees = reaper.list_git_worktrees(repo)
                verdict = _classify(
                    repo,
                    branch,
                    worktree_branches={w.branch for w in current_worktrees if w.branch},
                    detached_heads={w.head for w in current_worktrees if w.detached and w.head},
                    active_tasks=_active_tasks(repo),
                    protected_branches=protected,
                    pr_lookup=pr_lookup,
                    issue_lookup=issues,
                    evidence_cache=evidence_cache,
                )
                if verdict.classification.startswith("delete-"):
                    verdict = _apply(repo, branch, verdict)
            decisions.append(verdict)
        if apply:
            _checked(repo, "fetch", "--prune", "origin")
    except Exception as exc:
        raise SweepError(str(exc), decisions) from exc
    return decisions


def _ledger_file(repo: Path) -> Path:
    path = reaper.control_plane_root(repo).resolve()
    for part in LEDGER_PATH.parts:
        path = path / part
        if path.is_symlink():
            raise RuntimeError("evidence ledger path contains a symlink")
    return path


def _ensure_ledger_directory(directory: Path) -> None:
    """Create ``directory`` at mode 0o700. A symlink is refused, never followed."""
    missing: list[Path] = []
    current = directory
    while True:
        try:
            info = os.lstat(current)
        except FileNotFoundError:
            missing.append(current)
            if current.parent == current:
                raise RuntimeError("evidence ledger directory is unavailable") from None
            current = current.parent
            continue
        if stat.S_ISLNK(info.st_mode):
            raise RuntimeError("evidence ledger path contains a symlink")
        if not stat.S_ISDIR(info.st_mode):
            raise RuntimeError("evidence ledger directory is not a directory")
        break
    for created in reversed(missing):
        try:
            os.mkdir(created, 0o700)
        except FileExistsError:
            info = os.lstat(created)
            if stat.S_ISLNK(info.st_mode):
                raise RuntimeError("evidence ledger path contains a symlink") from None
            if not stat.S_ISDIR(info.st_mode):
                raise RuntimeError("evidence ledger directory is not a directory") from None


def _append_ledger_line(repo: Path, payload: dict[str, object]) -> None:
    """Append one JSON line and flush it. The ledger is owner-only and is not a symlink."""
    encoded = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode()
    path = _ledger_file(repo)
    _ensure_ledger_directory(path.parent)
    descriptor = os.open(
        path,
        os.O_APPEND | os.O_CREAT | os.O_WRONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
        0o600,
    )
    try:
        os.fchmod(descriptor, 0o600)
        os.write(descriptor, encoded)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        os.fchmod(directory, 0o700)
        os.fsync(directory)
    finally:
        os.close(directory)


def _append_receipt(repo: Path, branch: Branch, verdict: Decision) -> None:
    """Append the intent receipt and flush it before the caller deletes either ref."""
    tip = branch.remote_sha or branch.local_sha
    if tip is None or not SHA_RE.fullmatch(tip):
        raise RuntimeError("evidence receipt requires a tip SHA")
    _append_ledger_line(
        repo,
        {
            "at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "branch": branch.name,
            "evidence_detail": verdict.evidence_detail or verdict.reason,
            "evidence_kind": verdict.evidence_kind or verdict.classification,
            "tip_sha": tip,
        },
    )


def _append_outcome(
    repo: Path,
    branch: Branch,
    *,
    remote_deleted: bool,
    local_deleted: bool,
    error: str | None,
) -> None:
    """Append what the delete attempt actually did. The intent line does not claim success."""
    _append_ledger_line(
        repo,
        {
            "at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "branch": branch.name,
            "error": error,
            "local_deleted": local_deleted,
            "remote_deleted": remote_deleted,
        },
    )


def _apply(repo: Path, branch: Branch, verdict: Decision) -> Decision:
    from dataclasses import replace

    name = branch.name
    if verdict.classification == "delete-ancestor":
        try:
            main = _origin_head(repo, "main")
            tracking_main = _checked(repo, "rev-parse", "refs/remotes/origin/main").strip()
        except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
            return replace(verdict, classification="report-only", reason=f"origin/main verification failed: {exc}")
        if main != tracking_main:
            return replace(verdict, classification="report-only", reason="origin/main tracking ref is stale")
    live: str | None = None
    if branch.remote_sha:
        try:
            live = _origin_head(repo, name)
        except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
            return replace(verdict, classification="report-only", reason=f"remote verification failed: {exc}")
        if live is not None and live != branch.remote_sha:
            return replace(verdict, classification="skipped-moved", reason="origin head changed")
    if verdict.evidence_kind == "merged-pr":
        # Re-check the live origin tip. A stale tracking ref must not delete the only local copy.
        if branch.remote_sha is None or live != branch.remote_sha:
            return replace(verdict, classification="report-only", reason=_MERGED_PR_ABSENT)
        if branch.local_sha is not None and branch.local_sha != branch.remote_sha:
            return replace(verdict, classification="report-only", reason=_MERGED_PR_MISMATCH)
    if live is None and not branch.local_sha:
        return replace(verdict, classification="already-absent", reason="remote head already absent; no local ref")
    try:
        _append_receipt(repo, branch, verdict)
    except (OSError, RuntimeError) as exc:
        return replace(verdict, classification="report-only", reason=f"evidence receipt failed: {exc}")

    def finish(result: Decision, error: str | None) -> Decision:
        try:
            _append_outcome(
                repo,
                branch,
                remote_deleted=result.remote_deleted,
                local_deleted=result.local_deleted,
                error=error,
            )
        except (OSError, RuntimeError) as exc:
            note = f"outcome receipt failed: {exc}"
            return replace(result, reason=f"{result.reason}; {note}")
        return result

    if branch.remote_sha and live is not None:
        try:
            result = _git(
                repo,
                "push",
                "--porcelain",
                f"--force-with-lease=refs/heads/{name}:{branch.remote_sha}",
                "origin",
                f":refs/heads/{name}",
                timeout=60,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            reason = f"remote verification failed: {exc}"
            return finish(replace(verdict, classification="report-only", reason=reason), reason)
        if result.returncode:
            output = (result.stdout + "\n" + result.stderr).strip()
            if "[rejected]" in output and "(stale info)" in output:
                reason = "origin head changed during deletion"
                return finish(replace(verdict, classification="skipped-moved", reason=reason), reason)
            reason = f"remote deletion failed: {output}"
            return finish(replace(verdict, classification="report-only", reason=reason), reason)
        verdict = replace(verdict, remote_deleted=True)
        try:
            if _origin_head(repo, name) is not None:
                reason = "origin head remains after deletion"
                return finish(replace(verdict, classification="report-only", reason=reason), reason)
        except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
            reason = f"remote verification failed: {exc}"
            return finish(replace(verdict, classification="report-only", reason=reason), reason)
    if branch.local_sha:
        # The reaper checks the exact local head again before deleting it.
        try:
            error = reaper._prune_branch(repo, name, force=True, expected_head=branch.local_sha)
        except Exception as exc:
            reason = f"local deletion failed: {exc}"
            return finish(replace(verdict, classification="report-only", reason=reason), reason)
        if error:
            reason = f"local deletion failed: {error}"
            return finish(replace(verdict, classification="report-only", reason=reason), reason)
        verdict = replace(verdict, local_deleted=True)
    if not verdict.remote_deleted and not verdict.local_deleted:
        reason = "remote head already absent; no local ref"
        return finish(replace(verdict, classification="already-absent", reason=reason), reason)
    return finish(verdict, None)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "List stale agent and scratch branches, including landed work proven by patch-id or a merged pull request.\n"
            "Use after dispatch cleanup. Dry run is the default; --apply deletes only branches the sweep has proved safe."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.hygiene.branch_sweep --json\n"
            "  .venv/bin/python -m scripts.hygiene.branch_sweep --apply --json\n"
            "Outputs: stdout decisions. --apply appends batch_state/branch-archive/evidence.jsonl on the\n"
            "control-plane checkout before deleting qualifying remote and local refs, then appends an outcome\n"
            "line (remote_deleted, local_deleted, error) and prunes tracking refs.\n"
            "Exit codes: 0 = sweep succeeded; 1 = repository or probe failure.\n"
            "Related: issue #9129; issue #9909; docs/runbooks/worktree-cleanup.md; drive-epic §7a."
        ),
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Delete proved-safe branches and append an evidence receipt; default is a dry run that deletes nothing.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON decisions; default is one readable line each.")
    return parser


def _format_decision(item: Decision) -> str:
    return f"{item.classification}: {item.branch} ({item.reason}; age_days={item.age_days})"


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        repo = reaper.resolve_repo_root()
        decisions = sweep(repo, apply=args.apply)
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        if args.json:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "error": str(exc),
                        "decisions": [asdict(d) for d in exc.decisions] if isinstance(exc, SweepError) else [],
                    }
                )
            )
        else:
            if isinstance(exc, SweepError):
                for item in exc.decisions:
                    print(_format_decision(item))
            print(f"branch_sweep: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps({"ok": True, "apply": args.apply, "decisions": [asdict(d) for d in decisions]}, indent=2))
    else:
        for item in decisions:
            print(_format_decision(item))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
