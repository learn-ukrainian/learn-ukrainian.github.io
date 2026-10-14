"""List stale agent branches and delete only those with verifiable safe heads.

Expired local report-only branches are archived from this same command: one thin
bundle (history already on origin/main stays out), a receipt line that is re-read
before use, then one compare-and-delete of those local refs. Remote refs and old
bundles stay.
"""

from __future__ import annotations

import argparse
import contextvars
import fcntl
import hashlib
import json
import os
import re
import shlex
import stat
import subprocess
import sys
import tempfile
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

from scripts.common import github_client
from scripts.common.git_context import UnsafeBranchNameError, sanitized_git_env, validate_plain_branch_name
from scripts.common.jsonl import jsonl_lines, physical_lines
from scripts.common.scratch import ensure_scratch_root
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
ARCHIVE_DIR = Path("batch_state") / "branch-archive"
RECEIPT_PATH = ARCHIVE_DIR / "stale-local-receipts.jsonl"
ARCHIVE_LOCK_PATH = ARCHIVE_DIR / "archive.lock"
DEFAULT_ARCHIVE_AFTER_DAYS = 7
# A released task younger than this still names work someone may return to.
# Archival waits. Patch-id deletion and the other dispositions do not.
RECENT_RELEASED_TASK_DAYS = DEFAULT_ARCHIVE_AFTER_DAYS
BUNDLE_REVIEW_DAYS = 90
# main() keeps sweep(repo, apply=...) so wrappers of that signature keep working.
# The CLI threshold is installed for that call; an explicit argument still wins.
_ARCHIVE_AFTER_DAYS: contextvars.ContextVar[int | None] = contextvars.ContextVar(
    "branch_sweep_archive_after_days",
    default=None,
)
_MERGED_PR_ABSENT = "merged-pr evidence refused: branch tip is absent from origin; recovery needs the tip on GitHub"
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
    local_symref: str | None = None


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


def _git(
    repo: Path,
    *args: str,
    timeout: int = 30,
    input: str | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        env=sanitized_git_env(),
        input=input,
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


def _occupation_file(path: Path) -> str | None:
    """Read optional Git administrative evidence without following links or blocking on FIFOs."""
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    except FileNotFoundError:
        return None
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_size > 1024 * 1024:
            raise RuntimeError("occupation evidence is not a bounded regular file")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            body = stream.read(1024 * 1024 + 1)
        if len(body) > 1024 * 1024:
            raise RuntimeError("occupation evidence exceeds the read limit")
        try:
            return body.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise RuntimeError("occupation evidence is not UTF-8") from exc
    finally:
        os.close(descriptor)


def _occupation_directory(path: Path) -> bool:
    """Absence is known only when lstat reports ENOENT; unsafe directories refuse the sweep."""
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    if not stat.S_ISDIR(info.st_mode):
        raise RuntimeError("occupation evidence directory is not a real directory")
    return True


def _occupied_worktrees(repo: Path) -> list[reaper.WorktreeInfo]:
    """Census all registrations; refuse any native operation anywhere.

    Git's wt-status.c checks rebase directories, BISECT_LOG, MERGE_HEAD,
    CHERRY_PICK_HEAD and REVERT_HEAD; sequencer.c keeps multi-step replay
    state in sequencer/. Presence is enough to refuse, even if its contents
    are malformed. Never parse operation branch names to permit archival.
    """
    trees = reaper.list_git_worktrees(repo)
    if not trees:
        raise RuntimeError("occupation evidence has no registered worktrees")
    common = Path(_checked(repo, "rev-parse", "--path-format=absolute", "--git-common-dir").rstrip("\n"))
    if not common.is_absolute() or not _occupation_directory(common):
        raise RuntimeError("occupation evidence has no Git common directory")
    # Git lists the primary worktree first. Linked registrations remain readable
    # here even when their checkouts are missing, moved, locked or prunable.
    directories = {trees[0].path: common}
    linked = common / "worktrees"
    if _occupation_directory(linked):
        for directory in linked.iterdir():
            if not _occupation_directory(directory):
                raise RuntimeError("occupation evidence registration disappeared")
            pointer = _occupation_file(directory / "gitdir")
            if not pointer or not pointer.endswith("\n") or "\n" in pointer[:-1]:
                raise RuntimeError("occupation evidence has an invalid worktree pointer")
            gitfile = Path(pointer[:-1])
            if not gitfile.is_absolute():
                gitfile = (directory / gitfile).resolve()
            if gitfile.parent in directories:
                raise RuntimeError("occupation evidence has an ambiguous worktree pointer")
            directories[gitfile.parent] = directory
    if set(directories) != {tree.path for tree in trees}:
        raise RuntimeError("occupation evidence registrations disagree with Git")
    if len(directories) != len(trees):
        raise RuntimeError("occupation evidence has duplicate registrations")
    for tree in trees:
        directory = directories[tree.path]
        if (
            not tree.head
            or not SHA_RE.fullmatch(tree.head)
            or bool(tree.branch) == tree.detached
            or (tree.branch is not None and not _valid(tree.branch, repo))
        ):
            raise RuntimeError("occupation evidence has an unknown worktree HEAD")
        head = _occupation_file(directory / "HEAD")
        if head is None or head.rstrip("\n") != (f"ref: refs/heads/{tree.branch}" if tree.branch else tree.head):
            raise RuntimeError("occupation evidence HEAD disagrees with Git")
        for marker in ("rebase-apply", "rebase-merge", "sequencer"):
            if _occupation_directory(directory / marker):
                raise RuntimeError(f"occupation evidence: in-progress operation ({marker}); sweep refused")
        # BISECT_START also refuses incomplete bisect state with a missing log.
        for marker in ("BISECT_LOG", "BISECT_START", "MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "REBASE_HEAD"):
            if _occupation_file(directory / marker) is not None:
                raise RuntimeError(f"occupation evidence: in-progress operation ({marker}); sweep refused")
    return trees


def _refs(repo: Path) -> list[Branch]:
    # NUL separates fields; Git ref names cannot contain NUL or a line feed.
    output = _checked(
        repo,
        "for-each-ref",
        "--format=%(refname)%00%(objectname)%00%(committerdate:unix)%00%(symref)",
        "refs/remotes/origin",
        "refs/heads",
    )
    by_name: dict[str, dict[str, object]] = {}
    for line in output.splitlines():
        fields = line.split("\0")
        if len(fields) != 4:
            raise RuntimeError("git for-each-ref returned a malformed row")
        ref, sha, raw_date, symref = fields
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
        if kind == "local":
            row["local_symref"] = symref or None
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


def _task_records(repo: Path) -> list[tuple[Path, dict[str, object]]]:
    task_dir = reaper.control_plane_root(repo) / "batch_state" / "tasks"
    records: list[tuple[Path, dict[str, object]]] = []
    for path in task_dir.glob("*.json"):
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise RuntimeError(f"cannot inspect task state {path.name}: {exc}") from exc
        if not isinstance(state, dict):
            raise RuntimeError(f"cannot inspect task state {path.name}: not an object")
        records.append((path, state))
    return records


def _task_branch_names(state: dict[str, object]) -> set[str]:
    names: set[str] = set()
    for key in ("worktree_branch", "branch"):
        value = state.get(key)
        if isinstance(value, str):
            names.add(value)
    prep = state.get("worktree_prep")
    if isinstance(prep, dict) and isinstance(prep.get("branch"), str):
        names.add(prep["branch"])
    agent, task_id = state.get("agent"), state.get("task_id")
    if isinstance(agent, str) and isinstance(task_id, str):
        names.add(f"{agent}/{task_id}")
    return names


def _parse_task_time(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(UTC)


def _task_finished_at(state: dict[str, object], path: Path) -> datetime | None:
    for key in ("finished_at", "updated_at"):
        parsed = _parse_task_time(state.get(key))
        if parsed is not None:
            return parsed
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, UTC)
    except OSError:
        return None


def _active_tasks(repo: Path) -> set[str]:
    active: set[str] = set()
    for _path, state in _task_records(repo):
        status = state.get("status")
        if isinstance(status, str) and status in RELEASED_TASK_STATUSES:
            continue
        active.update(_task_branch_names(state))
    return active


def _recent_released_tasks(repo: Path, *, now: datetime | None = None) -> set[str]:
    """Branches named by a released task that finished inside the recent window.

    An unreadable finish time protects the branch. This set blocks archival only.
    """
    moment = now or datetime.now(UTC)
    window = timedelta(days=RECENT_RELEASED_TASK_DAYS)
    recent: set[str] = set()
    for path, state in _task_records(repo):
        status = state.get("status")
        if not isinstance(status, str) or status not in RELEASED_TASK_STATUSES:
            continue
        finished = _task_finished_at(state, path)
        if finished is not None and moment - finished >= window:
            continue
        recent.update(_task_branch_names(state))
    return recent


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
    # One record per physical line; a commit subject may contain NEL/LS/PS.
    for line in physical_lines(result.stdout):
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
    if isinstance(login, str) and isinstance(name, str) and login and name and "/" not in login and "/" not in name:
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
    # Header fields end at CRLF; NEL/LS/PS are field-value text.
    for line in physical_lines(headers):
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
    return github_client.run(
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
        # Newer commits exclude the branch before any other refusal can be archived.
        branch_dates = _committer_timestamps(repo, f"{base}..{tip}")
        if not branch_dates:
            return decided("report-only", "merged-pr evidence refused: branch committer dates are unreadable")
        if any(stamp > _merge_committer_timestamp(repo, merge) for stamp in branch_dates):
            return decided("report-only", _MERGED_PR_NEWER)
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
        if not branch_files <= pull_files:
            return decided("report-only", "merged PR files do not cover every branch file")
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        return decided("report-only", f"evidence check failed: {exc}")
    return decided(
        "delete-evidence",
        f"issue #{issue} closed by merged pull request #{closure.closing_pr} at {merge[:12]}; branch files covered",
        evidence_kind="merged-pr",
    )


def current_archive_after_days() -> int:
    """Return the threshold ``main`` installed for this call, or the 7-day default."""
    value = _ARCHIVE_AFTER_DAYS.get()
    return DEFAULT_ARCHIVE_AFTER_DAYS if value is None else value


def _archive_reason_settled(reason: str) -> bool:
    """True when report-only means unique local commits, not an unread probe.

    A branch whose commits are newer than the closing merge stays report-only at
    any age. That check runs before these reasons are chosen. A rescue ref is
    never archived from its protective refusal.
    """
    if reason in {
        "no PR and unique commits",
        _MERGED_PR_ABSENT,
        "merged PR files do not cover every branch file",
        "branch changes no files",
    }:
        return True
    if reason.startswith("issue #") and reason.endswith("has no closing merged pull request"):
        return True
    return reason.startswith("closing pull request #") and (
        reason.endswith("merge commit is not on origin/main")
        or reason.endswith("has more than one merge commit on origin/main")
    )


def _pr_checkout_name(name: str) -> bool:
    """True for a local checkout whose name is not the pull request's head branch.

    ``gh`` lookup by this exact name never sees ``pr-*`` or ``<agent>/review-*``.
    The same names are excluded in scheduled worktree cleanup.
    """
    if name.startswith("pr-"):
        return True
    return name.rsplit("/", 1)[-1].startswith("review-")


def _upstream_unpushed(repo: Path, name: str) -> str | None:
    """Refusal when ``name`` has commits its configured upstream does not.

    ``None`` means there is no upstream, or the upstream already contains the tip.
    Any other upstream failure stays report-only.
    """
    shown = _git(repo, "rev-parse", "--abbrev-ref", f"{name}@{{upstream}}")
    if shown.returncode != 0:
        detail = (shown.stderr or shown.stdout or "").strip()
        if "no upstream configured" in detail:
            return None
        return f"upstream check failed: {detail or shown.returncode}"
    upstream = shown.stdout.strip()
    if not upstream or upstream.endswith("@{upstream}"):
        return None
    ahead = _git(repo, "rev-list", "--count", f"{upstream}..{name}")
    if ahead.returncode != 0:
        detail = (ahead.stderr or ahead.stdout or "").strip()
        return f"upstream check failed: {detail or ahead.returncode}"
    count = ahead.stdout.strip()
    if not count.isdecimal():
        return "upstream check failed: unreadable ahead count"
    if count != "0":
        return f"branch has unpushed commits on upstream {upstream}"
    return None


def _consider_archive(
    verdict: Decision,
    branch: Branch,
    *,
    repo: Path,
    prs: list[reaper.PullRequestState],
    archive_after_days: int,
    recent_tasks: set[str],
) -> Decision:
    """Promote a settled local report-only branch once it is old enough to archive."""
    if archive_after_days < 0 or verdict.classification != "report-only" or prs:
        return verdict
    if branch.local_sha is None or verdict.local_sha != branch.local_sha:
        return verdict
    if verdict.age_days is None or verdict.age_days < archive_after_days:
        return verdict
    if _rescue(branch.name):
        return verdict
    if _pr_checkout_name(branch.name):
        return replace(
            verdict,
            reason="local pr-* or review-* checkout is not archived; the name is not the pull request head",
        )
    if branch.name in recent_tasks:
        return replace(
            verdict,
            reason=(
                f"a released task that finished within the last {RECENT_RELEASED_TASK_DAYS} days names this branch"
            ),
        )
    unpushed = _upstream_unpushed(repo, branch.name)
    if unpushed is not None:
        return replace(verdict, reason=unpushed)
    if not _archive_reason_settled(verdict.reason):
        return verdict
    return replace(
        verdict,
        classification="archive-expired",
        reason=(
            f"{verdict.reason}; local ref is at least {archive_after_days} days old "
            "with no pull request, worktree, or live task"
        ),
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
    archive_after_days: int | None = None,
    recent_tasks: set[str] | None = None,
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

    days = current_archive_after_days() if archive_after_days is None else archive_after_days
    if name in protected_branches or not _candidate(name):
        return decision("protected", "outside agent/scratch candidate namespace or protected name")
    if not _valid(name, repo):
        return decision("report-only", "invalid or unsafe branch name")
    if branch.local_symref:
        return decision("report-only", "symbolic local ref is never deleted or archived")
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
    recent = _recent_released_tasks(repo) if recent_tasks is None else recent_tasks
    evidence = _try_evidence(
        repo,
        branch,
        tip,
        issue_lookup=issue_lookup or _query_issue_closure,
        cache=evidence_cache if evidence_cache is not None else _EvidenceCache(),
    )
    if evidence is not None:
        return _consider_archive(
            evidence,
            branch,
            repo=repo,
            prs=prs,
            archive_after_days=days,
            recent_tasks=recent,
        )
    if prs:
        return decision("report-only", "closed/merged PR head does not match branch tip; unique commits")
    return _consider_archive(
        decision("report-only", "no PR and unique commits"),
        branch,
        repo=repo,
        prs=prs,
        archive_after_days=days,
        recent_tasks=recent,
    )


def sweep(
    repo: Path,
    *,
    apply: bool = False,
    pr_lookup: PrLookup = reaper._query_pr_states,
    protected_lookup: Callable[[Path], set[str]] = remote_protected_branches,
    issue_lookup: IssueLookup | None = None,
    archive_after_days: int | None = None,
) -> list[Decision]:
    decisions: list[Decision] = []
    evidence_cache = _EvidenceCache()
    issues = issue_lookup or _query_issue_closure
    days = current_archive_after_days() if archive_after_days is None else archive_after_days
    if days < 0:
        raise RuntimeError("--archive-after-days must be zero or greater")
    try:
        branches = _refs(repo)
        recent = _recent_released_tasks(repo)
        try:
            protected = PROTECTED | protected_lookup(repo)
            protection_error = None
        except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
            protected = PROTECTED
            protection_error = str(exc)
        worktrees = _occupied_worktrees(repo)
        worktree_branches = {item.branch for item in worktrees if item.branch}
        detached_heads = {item.head for item in worktrees if item.detached and item.head}
        active = _active_tasks(repo)
        archive_snapshot = _archive_local_snapshot(repo, branches=branches, worktrees=worktrees)
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
                archive_after_days=days,
                recent_tasks=recent,
            )
            if apply and verdict.classification.startswith("delete-"):
                # Recheck all volatile guards before each destructive call. In particular,
                # stale origin tracking refs cannot authorize deletion of a moved head.
                current_worktrees = _occupied_worktrees(repo)
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
                    archive_after_days=days,
                    recent_tasks=_recent_released_tasks(repo),
                )
                if verdict.classification.startswith("delete-"):
                    verdict = _apply(repo, branch, verdict)
            decisions.append(verdict)
        if apply:
            decisions = _apply_archive(
                repo,
                decisions,
                protected=protected,
                pr_lookup=pr_lookup,
                issue_lookup=issues,
                evidence_cache=evidence_cache,
                archive_after_days=days,
                classification_snapshot=archive_snapshot,
            )
        decisions.extend(_review_bundle_decisions(repo))
        if apply:
            _checked(repo, "fetch", "--prune", "origin")
    except Exception as exc:
        raise SweepError(str(exc), decisions) from exc
    return decisions


def _controlled_file(repo: Path, relative: Path, *, refusal: str) -> Path:
    """Join ``relative`` under the control plane. A symlink at any part is refused."""
    path = reaper.control_plane_root(repo).resolve()
    for part in relative.parts:
        path = path / part
        if path.is_symlink():
            raise RuntimeError(refusal)
    return path


def _ledger_file(repo: Path) -> Path:
    return _controlled_file(repo, LEDGER_PATH, refusal="evidence ledger path contains a symlink")


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


def _write_all(descriptor: int, payload: bytes) -> None:
    """Write every byte. A short ``os.write`` is retried, never treated as done."""
    view = memoryview(payload)
    while len(view):
        written = os.write(descriptor, view)
        if written <= 0:
            raise RuntimeError("receipt write made no progress")
        view = view[written:]


def _read_from(path: Path, offset: int) -> bytes:
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        if offset:
            os.lseek(descriptor, offset, os.SEEK_SET)
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _append_ledger_line(repo: Path, payload: dict[str, object], *, relative: Path | None = None) -> None:
    """Append one JSON line and flush it. The ledger is owner-only and is not a symlink."""
    encoded = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if relative is None:
        path = _ledger_file(repo)
    else:
        path = _controlled_file(repo, relative, refusal="archive path contains a symlink")
    _ensure_ledger_directory(path.parent)
    descriptor = os.open(
        path,
        os.O_APPEND | os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC,
        0o600,
    )
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        os.fchmod(descriptor, 0o600)
        offset = os.fstat(descriptor).st_size
        if relative == RECEIPT_PATH:
            _parse_archive_receipts(os.pread(descriptor, offset, 0))
        try:
            _write_all(descriptor, encoded)
            if os.pread(descriptor, len(encoded), offset) != encoded:
                raise RuntimeError("receipt append is truncated or does not match what was written")
        except (OSError, RuntimeError):
            # Under this writer lock, undo only our failed append. Never repair
            # an existing broken tail or discard another writer's valid record.
            os.ftruncate(descriptor, offset)
            os.fsync(descriptor)
            raise
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


def _retain_archive(verdict: Decision, reason: str) -> Decision:
    return replace(verdict, classification="report-only", reason=reason, local_deleted=False, remote_deleted=False)


@contextmanager
def _archive_lock(repo: Path) -> Iterator[None]:
    """Serialize archive writers on one persistent control-plane lock inode."""
    path = _controlled_file(repo, ARCHIVE_LOCK_PATH, refusal="archive lock path contains a symlink")
    try:
        _ensure_ledger_directory(path.parent)
        descriptor = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    except (OSError, RuntimeError) as exc:
        raise RuntimeError(f"archive lock path unwritable: {exc}") from exc
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise RuntimeError("archive lock path is not a regular file")
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        os.fchmod(descriptor, 0o600)
        yield
    finally:
        # Never unlink the lock: another opener must contend on this same inode.
        os.close(descriptor)


def _bundle_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    finally:
        os.close(descriptor)
    return digest.hexdigest()


def _seal_regular_file(path: Path) -> None:
    """Force owner-only mode and flush the file and its directory. Symlinks are refused."""
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        os.fchmod(descriptor, 0o600)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def _unlink_unverified(path: Path) -> None:
    info = os.lstat(path)
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise RuntimeError("refusing to remove a non-file bundle path")
    os.unlink(path)


def _verify_bundle_heads(repo: Path, bundle: Path, expected: dict[str, str]) -> None:
    info = os.lstat(bundle)
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise RuntimeError("bundle is missing")
    verified = _git(repo, "bundle", "verify", str(bundle))
    if verified.returncode != 0:
        detail = (verified.stderr or verified.stdout).strip()
        raise RuntimeError(f"bundle verify failed: {detail}")
    listed = _git(repo, "bundle", "list-heads", str(bundle))
    if listed.returncode != 0:
        detail = (listed.stderr or listed.stdout).strip()
        raise RuntimeError(f"bundle list-heads failed: {detail}")
    found: dict[str, str] = {}
    for line in listed.stdout.splitlines():
        parts = line.split()
        if len(parts) != 2 or not parts[1].startswith("refs/heads/"):
            continue
        name = parts[1].removeprefix("refs/heads/")
        if not SHA_RE.fullmatch(parts[0]):
            raise RuntimeError("bundle listed an invalid SHA")
        found[name] = parts[0]
    missing = [name for name, sha in expected.items() if found.get(name) != sha]
    if missing:
        raise RuntimeError("bundle is missing a head: " + ", ".join(missing))


def _write_verified_bundle(repo: Path, confirmed: list[tuple[Decision, Branch]]) -> tuple[Path, str]:
    """Verify a private bundle, then publish without replacing any existing name."""
    directory = _controlled_file(repo, ARCHIVE_DIR, refusal="archive path contains a symlink")
    try:
        _ensure_ledger_directory(directory)
    except RuntimeError as exc:
        if "symlink" in str(exc):
            raise
        raise RuntimeError(f"bundle path unwritable: {exc}") from exc
    expected: dict[str, str] = {}
    refs: list[str] = []
    for _verdict, branch in confirmed:
        if not _valid(branch.name, repo) or branch.local_sha is None:
            raise RuntimeError(f"archive retained: unsafe branch name {branch.name}")
        refs.append(f"refs/heads/{branch.name}")
        expected[branch.name] = branch.local_sha
    main_ref = "refs/remotes/origin/main"
    if _git(repo, "rev-parse", "--verify", "--quiet", main_ref).returncode != 0:
        raise RuntimeError("archive retained: origin/main is unavailable")
    prefix = f".stale-local-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-"
    TMPDIR = os.environ.get("TMPDIR") or ensure_scratch_root()
    descriptor, temporary_name = tempfile.mkstemp(prefix=prefix, suffix=".tmp", dir=TMPDIR)
    os.close(descriptor)
    temporary = Path(temporary_name)
    filename = temporary.name.removeprefix(".").removesuffix(".tmp") + ".bundle"
    bundle_path = directory / filename
    relative = (ARCHIVE_DIR / filename).as_posix()
    try:
        _checked(repo, "bundle", "create", str(temporary), *refs, "--not", main_ref)
        _seal_regular_file(temporary)
        _verify_bundle_heads(repo, temporary, expected)
        # link() is atomic and refuses an existing destination, even a symlink.
        # A cross-filesystem scratch root fails closed; never copy into a live archive name.
        os.link(temporary, bundle_path, follow_symlinks=False)
        _seal_regular_file(bundle_path)
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        if isinstance(exc, OSError):
            raise RuntimeError(f"bundle path unwritable: {exc}") from exc
        raise
    finally:
        # Only this run's private staging file is disposable. Published archives stay.
        _unlink_unverified(temporary)
    return bundle_path, relative


def _write_archive_receipts(
    repo: Path,
    confirmed: list[tuple[Decision, Branch]],
    *,
    bundle_path: Path,
    relative: str,
) -> None:
    """Append one receipt per branch, then re-read those lines before any delete."""
    checksum = _bundle_sha256(bundle_path)
    stamped = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    path = _controlled_file(repo, RECEIPT_PATH, refusal="archive path contains a symlink")
    _ensure_ledger_directory(path.parent)
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        offset = 0
    else:
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            raise RuntimeError("archive receipt path is not a regular file")
        offset = info.st_size
    _parse_archive_receipts(_read_from(path, 0) if offset else b"")
    payloads: list[dict[str, object]] = []
    for _verdict, branch in confirmed:
        sha = branch.local_sha
        if sha is None:
            raise RuntimeError("archive receipt requires a local SHA")
        refspec = f"refs/heads/{branch.name}:refs/heads/{branch.name}"
        payload: dict[str, object] = {
            "at": stamped,
            "branch": branch.name,
            "bundle": relative,
            "remote_copy": branch.remote_sha is not None,
            "restore": f"git fetch {shlex.quote(str(bundle_path))} {shlex.quote(refspec)}",
            "restore_prerequisites": (
                "This thin bundle needs its prerequisite commits present. Fetch them from origin "
                "or run the restore command in a clone of this repository."
            ),
            "sha": sha,
            "sha256": checksum,
        }
        payloads.append(payload)
        _append_ledger_line(repo, payload, relative=RECEIPT_PATH)
    body = _read_from(path, offset)
    parsed = _parse_archive_receipts(body)
    if parsed != payloads:
        raise RuntimeError("archive receipt does not match what was written")


def _parse_archive_receipts(body: bytes) -> list[dict[str, object]]:
    """Require complete LF-terminated JSON objects, including every existing record."""
    if not body:
        return []
    reason = f"invalid archive receipt ledger {RECEIPT_PATH.as_posix()}"
    if not body.endswith(b"\n"):
        raise RuntimeError(f"{reason}: truncated tail")
    try:
        parsed = [json.loads(line) for line in jsonl_lines(body.decode("utf-8"))[:-1]]
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{reason}: record is not valid JSON") from exc
    if any(not isinstance(row, dict) for row in parsed):
        raise RuntimeError(f"{reason}: record is not an object")
    return parsed


def _archive_local_snapshot(
    repo: Path,
    *,
    branches: list[Branch] | None = None,
    worktrees: list[reaper.WorktreeInfo] | None = None,
) -> dict[str, tuple[Branch, tuple[reaper.WorktreeInfo, ...], tuple[str, ...]]]:
    """Freeze ref, worktree registration and complete task-record state per branch."""
    refs = _refs(repo) if branches is None else branches
    trees = _occupied_worktrees(repo) if worktrees is None else worktrees
    records = _task_records(repo)
    tasks: dict[str, list[str]] = {}
    for path, state in records:
        finished = _task_finished_at(state, path)
        signature = json.dumps([path.name, state, finished.isoformat() if finished else None], sort_keys=True)
        for name in _task_branch_names(state):
            tasks.setdefault(name, []).append(signature)
    return {
        branch.name: (
            branch,
            tuple(
                sorted(
                    (
                        tree
                        for tree in trees
                        if tree.branch == branch.name
                        or (tree.detached and tree.head in {branch.local_sha, branch.remote_sha} - {None})
                    ),
                    key=lambda tree: str(tree.path),
                )
            ),
            tuple(sorted(tasks.get(branch.name, []))),
        )
        for branch in refs
    }


def _archive_pr_snapshot(
    repo: Path, names: list[str], pr_lookup: PrLookup
) -> dict[str, tuple[list[reaper.PullRequestState], str | None]]:
    """Read the entire selected PR guard batch before inspecting local guards.

    Production uses one GraphQL response, never N sequential branch queries.
    Injected branch readers must agree across two complete passes. They are a
    test/embedding seam, not a substitute for the production batch response.
    """
    if pr_lookup is not reaper._query_pr_states:
        first = {name: pr_lookup(repo, name) for name in names}
        second = {name: pr_lookup(repo, name) for name in names}
        return {
            name: second[name] if first[name] == second[name] else ([], "PR state changed during batch snapshot")
            for name in names
        }
    slug = reaper._github_owner_repo(repo)
    error = "batch PR snapshot unavailable or incomplete"
    unavailable = {name: ([], error) for name in names}
    if slug is None:
        return unavailable
    owner, repository = slug
    fields = " ".join(
        f"b{index}:pullRequests(headRefName:{json.dumps(name)},states:[OPEN,CLOSED,MERGED],first:100)"
        "{nodes{number state headRefOid} pageInfo{hasNextPage}}"
        for index, name in enumerate(names)
    )
    query = f"query{{repository(owner:{json.dumps(owner)},name:{json.dumps(repository)}){{{fields}}}}}"
    try:
        result = github_client.run(
            ["gh", "api", "graphql", "-f", f"query={query}"],
            cwd=repo,
            timeout=30,
            fresh=True,
            capture_output=True,
            text=True,
            check=False,
            env=sanitized_git_env(),
        )
    except (OSError, subprocess.SubprocessError):
        return unavailable
    if result.returncode:
        return unavailable
    try:
        payload = json.loads(result.stdout)
        if not isinstance(payload, dict) or payload.get("errors"):
            return unavailable
        data = payload["data"]["repository"]
        found: dict[str, tuple[list[reaper.PullRequestState], str | None]] = {}
        for index, name in enumerate(names):
            connection = data[f"b{index}"]
            if connection["pageInfo"]["hasNextPage"] is not False:
                return unavailable
            rows = connection["nodes"]
            if not isinstance(rows, list):
                return unavailable
            states: list[reaper.PullRequestState] = []
            for row in rows:
                number, state, sha = row["number"], row["state"], row["headRefOid"]
                if (
                    isinstance(number, bool)
                    or not isinstance(number, int)
                    or number <= 0
                    or state not in {"OPEN", "CLOSED", "MERGED"}
                    or not isinstance(sha, str)
                    or not SHA_RE.fullmatch(sha)
                ):
                    return unavailable
                states.append(reaper.PullRequestState(number, state, sha))
            found[name] = (states, None)
        return found
    except (KeyError, TypeError, ValueError):
        return unavailable


def _archive_delete_blockers(
    repo: Path,
    confirmed: list[tuple[Decision, Branch]],
    *,
    protected: set[str],
    pr_lookup: PrLookup,
    issue_lookup: IssueLookup,
    evidence_cache: _EvidenceCache,
    archive_after_days: int,
    classification_snapshot: dict[str, tuple[Branch, tuple[reaper.WorktreeInfo, ...], tuple[str, ...]]],
) -> list[tuple[str, str]]:
    """Finish every PR read, then compare a complete local snapshot with classification."""
    prs = _archive_pr_snapshot(repo, [branch.name for _, branch in confirmed], pr_lookup)
    found = {item.name: item for item in _refs(repo)}
    worktrees = _occupied_worktrees(repo)
    worktree_branches = {item.branch for item in worktrees if item.branch}
    detached_heads = {item.head for item in worktrees if item.detached and item.head}
    active = _active_tasks(repo)
    recent = _recent_released_tasks(repo)
    final_snapshot = _archive_local_snapshot(repo, branches=list(found.values()), worktrees=worktrees)
    blockers: list[tuple[str, str]] = []
    for _verdict, branch in confirmed:
        current = found.get(branch.name)
        archived = branch.local_sha
        if current is None or archived is None or current.local_sha != archived:
            blockers.append((branch.name, "local head is not the archived SHA"))
            continue
        fresh = _classify(
            repo,
            current,
            worktree_branches=worktree_branches,
            detached_heads=detached_heads,
            active_tasks=active,
            protected_branches=protected,
            pr_lookup=lambda _repo, name: prs[name],
            issue_lookup=issue_lookup,
            evidence_cache=evidence_cache,
            archive_after_days=archive_after_days,
            recent_tasks=recent,
        )
        if fresh.classification != "archive-expired" or fresh.local_sha != archived:
            blockers.append((branch.name, f"{fresh.classification}: {fresh.reason}"))
        elif final_snapshot.get(branch.name) != classification_snapshot.get(branch.name):
            blockers.append((branch.name, "ref, worktree or task record changed since classification"))
    return blockers


def _delete_archived_refs(repo: Path, pairs: list[tuple[str, str]]) -> None:
    """Delete every ref in one transaction, each only if it still has the archived SHA."""
    if not pairs:
        return
    lines: list[str] = []
    for name, sha in pairs:
        if not _valid(name, repo) or not SHA_RE.fullmatch(sha):
            raise RuntimeError(f"unsafe ref {name}")
        lines.append(f"delete refs/heads/{name} {sha}\n")
    # No network or other work follows these last local checks before the ref
    # transaction. Guard changes after these reads remain the residual window;
    # expected SHAs bound head moves, and --no-deref protects symbolic targets.
    trees = _occupied_worktrees(repo)
    active = _active_tasks(repo) | _recent_released_tasks(repo)
    for name, sha in pairs:
        if any(tree.branch == name or (tree.detached and tree.head == sha) for tree in trees):
            raise RuntimeError(f"{name}: skipped-worktree at final delete check")
        if name in active:
            raise RuntimeError(f"{name}: skipped-live-task or recent task at final delete check")
    result = _git(repo, "update-ref", "--stdin", "--no-deref", input="".join(lines))
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(detail or f"git update-ref exited {result.returncode}")


def _apply_archive(
    repo: Path,
    decisions: list[Decision],
    *,
    protected: set[str],
    pr_lookup: PrLookup,
    issue_lookup: IssueLookup,
    evidence_cache: _EvidenceCache,
    archive_after_days: int,
    classification_snapshot: dict[str, tuple[Branch, tuple[reaper.WorktreeInfo, ...], tuple[str, ...]]],
) -> list[Decision]:
    """Hold the archive lock from fresh validation through compare-and-delete."""
    selected = [item for item in decisions if item.classification == "archive-expired"]
    if not selected:
        return decisions
    try:
        with _archive_lock(repo):
            return _apply_archive_locked(
                repo,
                decisions,
                protected=protected,
                pr_lookup=pr_lookup,
                issue_lookup=issue_lookup,
                evidence_cache=evidence_cache,
                archive_after_days=archive_after_days,
                classification_snapshot=classification_snapshot,
            )
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        return [
            _retain_archive(item, f"archive retained: {exc}") if item.classification == "archive-expired" else item
            for item in decisions
        ]


def _apply_archive_locked(
    repo: Path,
    decisions: list[Decision],
    *,
    protected: set[str],
    pr_lookup: PrLookup,
    issue_lookup: IssueLookup,
    evidence_cache: _EvidenceCache,
    archive_after_days: int,
    classification_snapshot: dict[str, tuple[Branch, tuple[reaper.WorktreeInfo, ...], tuple[str, ...]]],
) -> list[Decision]:
    """Bundle, verify, and receipt every expired local branch, then delete those local refs."""
    selected = [item for item in decisions if item.classification == "archive-expired"]
    indexes = {item.branch: index for index, item in enumerate(decisions)}
    found = {item.name: item for item in _refs(repo)}
    worktrees = _occupied_worktrees(repo)
    worktree_branches = {item.branch for item in worktrees if item.branch}
    detached_heads = {item.head for item in worktrees if item.detached and item.head}
    active = _active_tasks(repo)
    recent = _recent_released_tasks(repo)
    confirmed: list[tuple[Decision, Branch]] = []
    rejected: dict[str, str] = {}
    for verdict in selected:
        index = indexes[verdict.branch]
        branch = found.get(verdict.branch)
        if branch is None or branch.local_sha is None or branch.local_sha != verdict.local_sha:
            rejected[verdict.branch] = "local head changed before bundling"
            continue
        fresh = _classify(
            repo,
            branch,
            worktree_branches=worktree_branches,
            detached_heads=detached_heads,
            active_tasks=active,
            protected_branches=protected,
            pr_lookup=pr_lookup,
            issue_lookup=issue_lookup,
            evidence_cache=evidence_cache,
            archive_after_days=archive_after_days,
            recent_tasks=recent,
        )
        if fresh.classification != "archive-expired" or fresh.local_sha != branch.local_sha:
            rejected[verdict.branch] = f"{fresh.classification}: {fresh.reason}"
            continue
        decisions[index] = fresh
        confirmed.append((fresh, branch))
    if rejected:
        described = "; ".join(f"{name}: {why}" for name, why in rejected.items())
        for verdict in selected:
            why = rejected.get(verdict.branch, "another branch in the batch failed validation")
            decisions[indexes[verdict.branch]] = _retain_archive(
                verdict, f"archive retained: {why}; batch kept ({described})"
            )
        return decisions
    confirmed.sort(key=lambda pair: pair[0].branch)
    try:
        bundle_path, relative = _write_verified_bundle(repo, confirmed)
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        reason = str(exc) if str(exc).startswith("archive retained:") else f"archive retained: {exc}"
        for verdict, _branch in confirmed:
            decisions[indexes[verdict.branch]] = _retain_archive(verdict, reason)
        return decisions
    try:
        _write_archive_receipts(repo, confirmed, bundle_path=bundle_path, relative=relative)
    except (OSError, RuntimeError) as exc:
        reason = f"archive retained: receipt failed before deletion: {exc}"
        for verdict, _branch in confirmed:
            decisions[indexes[verdict.branch]] = _retain_archive(verdict, reason)
        return decisions
    blockers = _archive_delete_blockers(
        repo,
        confirmed,
        protected=protected,
        pr_lookup=pr_lookup,
        issue_lookup=issue_lookup,
        evidence_cache=evidence_cache,
        archive_after_days=archive_after_days,
        classification_snapshot=classification_snapshot,
    )
    if blockers:
        described = "; ".join(f"{name}: {why}" for name, why in blockers)
        by_branch = dict(blockers)
        for verdict, branch in confirmed:
            why = by_branch.get(branch.name, "another branch in the batch failed validation")
            decisions[indexes[verdict.branch]] = _retain_archive(
                verdict,
                f"archive retained: {why}; batch kept ({described})",
            )
        return decisions
    try:
        pairs: list[tuple[str, str]] = []
        for _verdict, branch in confirmed:
            sha = branch.local_sha
            if sha is None:
                raise RuntimeError(f"{branch.name} has no archived SHA")
            pairs.append((branch.name, sha))
        _delete_archived_refs(repo, pairs)
    except (OSError, RuntimeError) as exc:
        reason = f"archive retained: compare-and-delete failed: {exc}"
        for verdict, _branch in confirmed:
            decisions[indexes[verdict.branch]] = _retain_archive(verdict, reason)
        return decisions
    for verdict, _branch in confirmed:
        decisions[indexes[verdict.branch]] = replace(verdict, local_deleted=True, remote_deleted=False)
    return decisions


def _review_bundle_decisions(repo: Path) -> list[Decision]:
    """List archive bundles at least 90 days old. Never delete them."""
    try:
        directory = _controlled_file(repo, ARCHIVE_DIR, refusal="archive path contains a symlink")
    except RuntimeError:
        return []
    if not directory.exists():
        return []
    info = os.lstat(directory)
    if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
        return []
    now = datetime.now(UTC).timestamp()
    listed: list[Decision] = []
    for path in sorted(directory.iterdir(), key=lambda item: item.name):
        try:
            child = os.lstat(path)
        except OSError:
            continue
        if stat.S_ISLNK(child.st_mode) or not stat.S_ISREG(child.st_mode) or path.suffix != ".bundle":
            continue
        age_days = max(0, int(now - child.st_mtime) // 86400)
        if age_days < BUNDLE_REVIEW_DAYS:
            continue
        listed.append(
            Decision(
                (ARCHIVE_DIR / path.name).as_posix(),
                "review-bundle",
                "bundle older than 90 days; listed for review; not deleted",
                None,
                None,
                age_days,
            )
        )
    return listed


def _archive_after_days_arg(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("archive-after-days must be an integer") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("archive-after-days must be zero or greater")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "List stale agent and scratch branches, including landed work proven by patch-id or a merged pull request.\n"
            "Use after dispatch cleanup. Dry run is the default; --apply deletes proved-safe branches and archives\n"
            "expired local report-only branches. Do not use it to delete remote branches or archive bundles."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.hygiene.branch_sweep --json\n"
            "  .venv/bin/python -m scripts.hygiene.branch_sweep --apply --json\n"
            "  .venv/bin/python -m scripts.hygiene.branch_sweep --archive-after-days 14 --json\n"
            "Outputs: stdout decisions. --apply appends batch_state/branch-archive/evidence.jsonl on the\n"
            "control-plane checkout before deleting qualifying remote and local refs, then appends an outcome\n"
            "line (remote_deleted, local_deleted, error) and prunes tracking refs.\n"
            "Local report-only branches with no pull request, worktree, or live task, whose age in whole days\n"
            "is at least N (default: 7), are archive-expired. --apply writes one bundle under\n"
            "batch_state/branch-archive/, runs git bundle verify, checks every head, appends one receipt line\n"
            "per branch to stale-local-receipts.jsonl. The bundle excludes history already on origin/main.\n"
            "The receipt is re-read, every guard is checked again, and one compare-and-delete then removes\n"
            "only those local refs. Any failure keeps the whole batch. Remote refs stay.\n"
            "Any native operation in any registered worktree refuses the sweep, even on an unrelated branch.\n"
            "Bundles at least 90 days old are listed as review-bundle and are never deleted.\n"
            "Exit codes: 0 = sweep succeeded; 1 = repository or probe failure; 2 = invalid arguments.\n"
            "Related: issue #9129; issue #9909; issue #10532; docs/runbooks/worktree-cleanup.md; drive-epic §7a."
        ),
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Delete proved-safe branches and append an evidence receipt; default is a dry run that deletes nothing.",
    )
    parser.add_argument(
        "--archive-after-days",
        type=_archive_after_days_arg,
        default=DEFAULT_ARCHIVE_AFTER_DAYS,
        metavar="N",
        help=(
            "Whole days at or above which a local report-only branch with no pull request, worktree, or live "
            "task is archived (default: 7). Example: --archive-after-days 14. Dry-run lists those branches; "
            "--apply writes one verified bundle and receipt, then deletes only the local ref."
        ),
    )
    parser.add_argument("--json", action="store_true", help="Print JSON decisions; default is one readable line each.")
    return parser


def _format_decision(item: Decision) -> str:
    return f"{item.classification}: {item.branch} ({item.reason}; age_days={item.age_days})"


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    token = _ARCHIVE_AFTER_DAYS.set(args.archive_after_days)
    try:
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
                            "archive_after_days": args.archive_after_days,
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
            print(
                json.dumps(
                    {
                        "ok": True,
                        "apply": args.apply,
                        "archive_after_days": args.archive_after_days,
                        "decisions": [asdict(d) for d in decisions],
                    },
                    indent=2,
                )
            )
        else:
            for item in decisions:
                print(_format_decision(item))
        return 0
    finally:
        _ARCHIVE_AFTER_DAYS.reset(token)


if __name__ == "__main__":
    raise SystemExit(main())
