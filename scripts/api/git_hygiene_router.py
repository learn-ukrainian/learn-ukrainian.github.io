"""Git hygiene endpoint for classifying dirty working-tree state (#1519).

Mounted at /api/git in main.py.

Endpoints:
    GET /api/git/hygiene      Dirty-file taxonomy with remediation hints

Performance benchmark: ``tests/test_git_hygiene_endpoint.py`` creates a
fixture repository with 1000 non-exempt untracked files and asserts
``compute_git_hygiene(...).performance_ms < 500``. The implementation
keeps the common large-dirty-tree path cheap by batching ``git
check-ignore`` and only running per-file ``git diff`` / ``git log`` for
modified tracked files.
"""

from __future__ import annotations

import asyncio
import fnmatch
import json
import os
import shlex
import subprocess
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from .config import PROJECT_ROOT

router = APIRouter(tags=["git"])

POLICY_DOC = PROJECT_ROOT / "docs" / "best-practices" / "git-hygiene.md"
FALLBACK_EXEMPTION_PATTERNS = (
    "wiki/**",
    "data/corpus_audit/draft_tickets/*.md",
)

BUCKET_NAMES = (
    "stale_behind_main",
    "real_wip",
    "untracked_unexempted",
    "intentional_deletions",
)

_GIT_TIMEOUT_S = 2.0
_GIT_ENV_KEYS = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX", "GIT_COMMON_DIR")


class StaleBranch(BaseModel):
    name: str
    upstream_gone: bool
    fully_merged_to_main: bool
    last_commit_sha: str
    last_commit_date: str
    committer: str


class Worktree(BaseModel):
    path: str
    branch: str
    clean: bool | None = None
    upstream_gone: bool | None = None
    fully_merged_to_main: bool | None = None
    disk_bytes: int | None = None
    reason: str


class CleanupReport(BaseModel):
    stale_branches: list[StaleBranch]
    removable_worktrees: list[Worktree]
    protected_worktrees: list[Worktree]
    total_reclaimable_bytes: int
    computed_at: str
    performance_ms: float


def _git_invocation(args: list[str], cwd: Path) -> list[str]:
    git_path = cwd / ".git"
    if git_path.is_file():
        line = git_path.read_text(encoding="utf-8").strip()
        if line.startswith("gitdir:"):
            raw_git_dir = Path(line.removeprefix("gitdir:").strip())
            git_dir = raw_git_dir if raw_git_dir.is_absolute() else cwd / raw_git_dir
            return ["git", f"--git-dir={git_dir}", f"--work-tree={cwd}", *args]
    if git_path.is_dir():
        return ["git", f"--git-dir={git_path}", f"--work-tree={cwd}", *args]
    return ["git", *args]


@dataclass(frozen=True)
class StatusEntry:
    xy: str
    path: str

    @property
    def is_untracked(self) -> bool:
        return self.xy == "??"

    @property
    def is_deleted(self) -> bool:
        return "D" in self.xy

    @property
    def is_modified(self) -> bool:
        return self.xy != "??" and "M" in self.xy


def _run_git(
    args: list[str],
    *,
    cwd: Path,
    input_text: str | None = None,
    timeout_s: float = _GIT_TIMEOUT_S,
) -> tuple[int, str, str]:
    try:
        env = os.environ.copy()
        for key in _GIT_ENV_KEYS:
            env.pop(key, None)
        proc = subprocess.run(
            _git_invocation(args, cwd),
            cwd=cwd,
            env=env,
            input=input_text,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        return 124, "", f"TimeoutExpired after {exc.timeout}s"
    except (FileNotFoundError, PermissionError, OSError) as exc:
        return 127, "", f"{type(exc).__name__}: {exc}"


def _isoformat_z(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _list_local_branches(cwd: Path) -> list[dict[str, Any]]:
    code, stdout, _stderr = _run_git(
        [
            "for-each-ref",
            "--format=%(refname:short)%00%(upstream:short)%00%(upstream:track)"
            "%00%(objectname:short)%00%(committerdate:unix)%00%(committername)",
            "refs/heads",
        ],
        cwd=cwd,
    )
    if code != 0:
        return []

    branches: list[dict[str, Any]] = []
    for line in stdout.splitlines():
        parts = line.split("\x00")
        if len(parts) != 6:
            continue
        name, upstream, upstream_track, sha, timestamp, committer = parts
        try:
            committed_at = datetime.fromtimestamp(int(timestamp), UTC)
            last_commit_date = _isoformat_z(committed_at)
        except (OSError, ValueError):
            last_commit_date = ""
        branches.append({
            "name": name,
            "upstream_gone": bool(upstream and "gone" in upstream_track.lower()),
            "last_commit_sha": sha,
            "last_commit_date": last_commit_date,
            "committer": committer,
        })
    return branches


def _list_worktrees(cwd: Path) -> list[dict[str, Any]]:
    code, stdout, _stderr = _run_git(["worktree", "list", "--porcelain"], cwd=cwd)
    if code != 0:
        return []

    worktrees: list[dict[str, Any]] = []
    current: dict[str, Any] = {}
    for line in stdout.splitlines():
        if not line.strip():
            if current:
                worktrees.append(current)
                current = {}
            continue

        key, _, value = line.partition(" ")
        if key == "worktree":
            current["path"] = value
        elif key == "HEAD":
            current["head"] = value
        elif key == "branch":
            current["branch"] = value.removeprefix("refs/heads/")
        elif key == "detached":
            current["branch"] = "(detached HEAD)"
            current["detached"] = True
        elif key in {"locked", "prunable"}:
            current[key] = value or True

    if current:
        worktrees.append(current)
    return worktrees


def _is_branch_merged_to_main(branch: str, cwd: Path) -> bool:
    code, stdout, _stderr = _run_git(["cherry", "main", branch], cwd=cwd)
    if code == 0:
        lines = [line.strip() for line in stdout.splitlines() if line.strip()]
        return all(line.startswith("-") for line in lines)

    code, stdout, _stderr = _run_git(["branch", "--merged", "main", "--format=%(refname:short)"], cwd=cwd)
    if code != 0:
        return False
    return branch in {line.strip() for line in stdout.splitlines() if line.strip()}


def _is_worktree_clean(path: Path, cwd: Path) -> bool:
    del cwd
    code, stdout, _stderr = _run_git(["status", "--porcelain"], cwd=path)
    return code == 0 and not stdout.strip()


def _disk_bytes(path: Path) -> int | None:
    try:
        proc = subprocess.run(
            ["du", "-sk", str(path)],
            capture_output=True,
            text=True,
            timeout=_GIT_TIMEOUT_S,
            check=False,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError, OSError):
        return None
    if proc.returncode != 0:
        return None
    first = proc.stdout.split(maxsplit=1)[0] if proc.stdout.split() else ""
    try:
        return int(first) * 1024
    except ValueError:
        return None


def _active_task_ids(project_root: Path | None = None) -> set[str]:
    tasks_dir = (project_root or PROJECT_ROOT) / "batch_state" / "tasks"
    active: set[str] = set()
    try:
        task_files = list(tasks_dir.glob("*.json"))
    except OSError:
        return active

    for path in task_files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if payload.get("status") != "running":
            continue
        active.add(path.stem)
        task_id = payload.get("task_id")
        if isinstance(task_id, str) and task_id:
            active.add(task_id)
    return active


def _is_protected(
    path: Path,
    branch: str,
    active_task_ids: set[str],
    project_root: Path | None = None,
) -> tuple[bool, str | None]:
    root = project_root or PROJECT_ROOT
    try:
        if path.resolve() == root.resolve():
            return True, "primary checkout"
    except OSError:
        pass

    normalized = path.as_posix()
    if "interactive" in normalized:
        return True, "interactive session (contains 'interactive' in path)"

    parts = path.parts
    for idx in range(len(parts) - 2):
        if parts[idx] == ".worktrees" and parts[idx + 1] == "dispatch":
            task_id = parts[idx + 3] if len(parts) > idx + 3 else path.name
            if task_id in active_task_ids or path.name in active_task_ids:
                return True, "active dispatch (matches .worktrees/dispatch/**)"
    return False, None


def _display_worktree_path(path: Path, project_root: Path) -> str:
    try:
        if path.resolve() == project_root.resolve():
            return str(path)
    except OSError:
        pass
    try:
        return path.relative_to(project_root).as_posix()
    except ValueError:
        return str(path)


def _worktree_reason(upstream_gone: bool, fully_merged_to_main: bool, clean: bool) -> str:
    reasons: list[str] = []
    if upstream_gone:
        reasons.append("upstream gone")
    if fully_merged_to_main:
        reasons.append("fully merged to main")
    if clean:
        reasons.append("working tree clean")
    return ", ".join(reasons)


def compute_git_cleanup(project_root: Path | None = None) -> CleanupReport:
    if project_root is None:
        project_root = PROJECT_ROOT

    started = time.perf_counter()
    computed_at = _isoformat_z(datetime.now(UTC))
    branches = _list_local_branches(project_root)
    worktrees = _list_worktrees(project_root)
    checked_out_branches = {
        record["branch"]
        for record in worktrees
        if record.get("branch") and record.get("branch") != "(detached HEAD)"
    }

    branch_state: dict[str, dict[str, Any]] = {}
    stale_branches: list[StaleBranch] = []
    for branch in branches:
        name = branch["name"]
        fully_merged = _is_branch_merged_to_main(name, project_root)
        state = {**branch, "fully_merged_to_main": fully_merged}
        branch_state[name] = state

        if name == "main" or name.startswith("origin/") or name in checked_out_branches:
            continue
        if branch["upstream_gone"] or fully_merged:
            stale_branches.append(StaleBranch(**state))

    active_task_ids = _active_task_ids(project_root)
    removable_worktrees: list[Worktree] = []
    protected_worktrees: list[Worktree] = []
    for record in worktrees:
        raw_path = record.get("path")
        if not raw_path:
            continue
        path = Path(raw_path)
        branch = record.get("branch") or "(detached HEAD)"
        display_path = _display_worktree_path(path, project_root)

        protected, reason = _is_protected(path, branch, active_task_ids, project_root)
        if protected:
            protected_worktrees.append(Worktree(path=display_path, branch=branch, reason=reason or "protected"))
            continue

        state = branch_state.get(branch)
        if state is None:
            continue
        upstream_gone = bool(state["upstream_gone"])
        fully_merged = bool(state["fully_merged_to_main"])
        if not (upstream_gone or fully_merged):
            continue
        clean = _is_worktree_clean(path, project_root)
        if not clean:
            continue

        disk_bytes = _disk_bytes(path)
        removable_worktrees.append(
            Worktree(
                path=display_path,
                branch=branch,
                clean=clean,
                upstream_gone=upstream_gone,
                fully_merged_to_main=fully_merged,
                disk_bytes=disk_bytes,
                reason=_worktree_reason(upstream_gone, fully_merged, clean),
            )
        )

    total_reclaimable_bytes = sum(
        item.disk_bytes for item in removable_worktrees if item.disk_bytes is not None
    )
    return CleanupReport(
        stale_branches=stale_branches,
        removable_worktrees=removable_worktrees,
        protected_worktrees=protected_worktrees,
        total_reclaimable_bytes=total_reclaimable_bytes,
        computed_at=computed_at,
        performance_ms=round((time.perf_counter() - started) * 1000, 2),
    )


def _parse_status(stdout: str) -> list[StatusEntry]:
    entries: list[StatusEntry] = []
    for line in stdout.splitlines():
        if len(line) < 4:
            continue
        xy = line[:2]
        path = line[3:]
        if " -> " in path:
            path = path.rsplit(" -> ", 1)[1]
        entries.append(StatusEntry(xy=xy, path=path.strip()))
    return entries


def _extract_policy_exemptions(policy_doc: Path = POLICY_DOC) -> list[str]:
    """Load exemption paths from the policy doc, with an explicit fallback.

    The policy's "Exemption paths" section is the source of truth for
    human-facing rules. We parse backticked path patterns from that
    section so the endpoint does not silently drift from the documented
    exemptions.
    """
    patterns: list[str] = []
    try:
        lines = policy_doc.read_text(encoding="utf-8").splitlines()
    except OSError:
        return list(FALLBACK_EXEMPTION_PATTERNS)

    in_section = False
    for line in lines:
        if line.startswith("## "):
            in_section = line.strip() == "## Exemption paths"
            continue
        if not in_section or not line.lstrip().startswith("- "):
            continue

        parts = line.split("`")
        for idx in range(1, len(parts), 2):
            candidate = parts[idx].strip()
            if candidate:
                patterns.append(candidate)

    return sorted(set(patterns or FALLBACK_EXEMPTION_PATTERNS))


def _matches_pattern(path: str, pattern: str) -> bool:
    normalized = path.strip("/")
    normalized_pattern = pattern.strip()
    if not normalized_pattern:
        return False

    if normalized_pattern.endswith("/"):
        return normalized.startswith(normalized_pattern.strip("/") + "/")
    if normalized_pattern.endswith("/**"):
        prefix = normalized_pattern[:-3].strip("/")
        return normalized == prefix or normalized.startswith(prefix + "/")
    if fnmatch.fnmatchcase(normalized, normalized_pattern.strip("/")):
        return True

    # The policy documents draft tickets as ``*.md`` because that is
    # today's file type, but the exemption is operationally the draft
    # ticket directory.
    if normalized_pattern.endswith("/*.md"):
        prefix = normalized_pattern[:-5].strip("/")
        return normalized.startswith(prefix + "/")
    return False


def _exemption_key(path: str, patterns: list[str], ignored: set[str]) -> str | None:
    if path in ignored:
        return "gitignored"
    for pattern in patterns:
        if _matches_pattern(path, pattern):
            if path == "wiki" or path.startswith("wiki/"):
                return "wiki"
            if path.startswith("data/corpus_audit/draft_tickets/"):
                return "draft_tickets"
            return "other"
    return None


def _check_ignored(paths: list[str], cwd: Path) -> set[str]:
    if not paths:
        return set()
    code, stdout, _stderr = _run_git(
        ["check-ignore", "--stdin"],
        cwd=cwd,
        input_text="\n".join(paths) + "\n",
    )
    if code not in {0, 1}:
        return set()
    return {line.strip() for line in stdout.splitlines() if line.strip()}


def _git_diff(path: str, cwd: Path) -> str:
    code, stdout, _stderr = _run_git(["diff", "HEAD", "--", path], cwd=cwd)
    return stdout if code == 0 else ""


def _recent_commits(path: str, cwd: Path) -> list[str]:
    code, stdout, _stderr = _run_git(
        ["log", "--format=%H", "HEAD~20..HEAD", "--", path],
        cwd=cwd,
    )
    if code != 0:
        code, stdout, _stderr = _run_git(["log", "--format=%H", "-20", "--", path], cwd=cwd)
    if code != 0:
        return []
    return [line.strip() for line in stdout.splitlines() if line.strip()]


def _diff_added_definition(diff: str) -> bool:
    for line in diff.splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        stripped = line[1:].lstrip()
        if stripped.startswith(("def ", "class ", "@")):
            return True
    return False


def _changed_lines(diff: str, prefix: str) -> set[str]:
    header = prefix * 3
    return {
        line[1:].strip()
        for line in diff.splitlines()
        if line.startswith(prefix) and not line.startswith(header) and line[1:].strip()
    }


def _commit_patch(commit: str, path: str, cwd: Path) -> str:
    code, stdout, _stderr = _run_git(
        ["show", "--format=", "--unified=0", commit, "--", path],
        cwd=cwd,
    )
    return stdout if code == 0 else ""


def _is_stale_behind_main(path: str, diff: str, commits: list[str], cwd: Path) -> bool:
    if not commits:
        return False

    working_additions = _changed_lines(diff, "+")
    working_removals = _changed_lines(diff, "-")
    if not working_removals:
        return False

    for commit in commits[:5]:
        patch = _commit_patch(commit, path, cwd)
        commit_added = _changed_lines(patch, "+")
        commit_removed = _changed_lines(patch, "-")
        if working_additions & commit_removed and working_removals & commit_added:
            return True

    return False


def _same_subtree(path: str, directory: str) -> bool:
    return path == directory or path.startswith(directory.rstrip("/") + "/")


def _intentional_deletion_files(
    deleted: list[str],
    modified_or_untracked: set[str],
) -> tuple[list[str], str | None]:
    by_dir: dict[str, list[str]] = {}
    for path in deleted:
        directory = str(Path(path).parent).replace("\\", "/")
        if directory == ".":
            continue
        by_dir.setdefault(directory, []).append(path)

    chosen: list[str] = []
    patterns: list[str] = []
    used: set[str] = set()
    for directory, files in sorted(by_dir.items(), key=lambda item: (-len(item[1]), item[0])):
        if len(files) < 3:
            continue
        if any(_same_subtree(path, directory) for path in modified_or_untracked):
            continue
        fresh = [path for path in sorted(files) if path not in used]
        if not fresh:
            continue
        chosen.extend(fresh)
        used.update(fresh)
        patterns.append(f"{directory}/*")

    if not chosen:
        return [], None
    return chosen, ", ".join(patterns)


def _bucket(count_files: list[str], **extra: Any) -> dict[str, Any]:
    bucket: dict[str, Any] = {
        "count": len(count_files),
        "files": sorted(count_files),
    }
    bucket.update(extra)
    return bucket


def _suggestions(buckets: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    suggestions: list[dict[str, Any]] = []

    stale_files = buckets["stale_behind_main"]["files"]
    if stale_files:
        quoted = " ".join(shlex.quote(path) for path in stale_files)
        suggestions.append({
            "action": "restore_to_head",
            "rationale": "pre-merge content; main moved past these files",
            "files": stale_files,
            "command": f"git checkout HEAD -- {quoted}",
        })

    wip_files = buckets["real_wip"]["files"]
    if wip_files:
        quoted = " ".join(shlex.quote(path) for path in wip_files)
        suggestions.append({
            "action": "stash_wip",
            "rationale": "local definitions or decorators need a stash or commit, not restore",
            "files": wip_files,
            "command": f"git stash push -m git-hygiene-wip -- {quoted}",
        })

    untracked_files = buckets["untracked_unexempted"]["files"]
    if untracked_files:
        first = untracked_files[0]
        pattern = f"{first.split('/', 1)[0]}/" if "/" in first else first
        suggestions.append({
            "action": "gitignore_pattern",
            "pattern": pattern,
            "rationale": "untracked files are neither ignored nor policy-exempt",
            "files": untracked_files,
        })

    deletion_pattern = buckets["intentional_deletions"].get("pattern")
    if deletion_pattern:
        suggestions.append({
            "action": "commit_deletions",
            "rationale": "coherent deletion cluster with no modified or untracked files in the same subtree",
            "pattern": deletion_pattern,
            "files": buckets["intentional_deletions"]["files"],
        })

    return suggestions


def compute_git_hygiene(project_root: Path | None = None) -> dict[str, Any]:
    if project_root is None:
        project_root = PROJECT_ROOT

    started = time.perf_counter()
    generated_at = _isoformat_z(datetime.now(UTC))
    policy_doc = project_root / "docs" / "best-practices" / "git-hygiene.md"
    exemption_patterns = _extract_policy_exemptions(policy_doc)

    code, stdout, stderr = _run_git(
        ["status", "--short", "--porcelain=v1", "--untracked-files=all"],
        cwd=project_root,
    )
    if code != 0:
        return {
            "generated_at": generated_at,
            "dirty_total": 0,
            "exempt": {"wiki": 0, "draft_tickets": 0, "gitignored": 0, "other": 0, "total": 0},
            "buckets": {name: _bucket([]) for name in BUCKET_NAMES},
            "suggestions": [],
            "health": "blocked_imports",
            "error": stderr.strip() or "git status failed",
            "performance_ms": round((time.perf_counter() - started) * 1000, 2),
        }

    entries = _parse_status(stdout)
    untracked_paths = [entry.path for entry in entries if entry.is_untracked]
    ignored_paths = _check_ignored(untracked_paths, project_root)

    exempt = {"wiki": 0, "draft_tickets": 0, "gitignored": 0, "other": 0, "total": 0}
    non_exempt_entries: list[StatusEntry] = []
    for entry in entries:
        key = _exemption_key(entry.path, exemption_patterns, ignored_paths)
        if key is not None:
            exempt[key] += 1
            exempt["total"] += 1
            continue
        non_exempt_entries.append(entry)

    stale: list[str] = []
    real_wip: list[str] = []
    modified_or_untracked = {
        entry.path for entry in non_exempt_entries if entry.is_modified or entry.is_untracked
    }

    for entry in non_exempt_entries:
        if not entry.is_modified:
            continue
        diff = _git_diff(entry.path, project_root)
        commits = _recent_commits(entry.path, project_root)
        if _is_stale_behind_main(entry.path, diff, commits, project_root):
            stale.append(entry.path)
        elif _diff_added_definition(diff) and not commits:
            real_wip.append(entry.path)

    untracked = [entry.path for entry in non_exempt_entries if entry.is_untracked]
    deleted = [entry.path for entry in non_exempt_entries if entry.is_deleted]
    intentional_deletions, deletion_pattern = _intentional_deletion_files(
        deleted,
        modified_or_untracked,
    )

    buckets = {
        "stale_behind_main": _bucket(stale),
        "real_wip": _bucket(real_wip),
        "untracked_unexempted": _bucket(untracked),
        "intentional_deletions": _bucket(intentional_deletions, pattern=deletion_pattern),
    }

    dirty_total = len(non_exempt_entries)
    blocked_imports = any(entry.is_deleted and entry.path.endswith(".py") for entry in non_exempt_entries)
    health = "clean" if dirty_total == 0 else "blocked_imports" if blocked_imports else "dirty"

    return {
        "generated_at": generated_at,
        "dirty_total": dirty_total,
        "exempt": exempt,
        "buckets": buckets,
        "suggestions": _suggestions(buckets),
        "health": health,
        "performance_ms": round((time.perf_counter() - started) * 1000, 2),
    }


@router.get("/hygiene")
async def git_hygiene():
    """Classify current working-tree drift into actionable buckets."""
    return await asyncio.to_thread(compute_git_hygiene)


@router.get("/cleanup", response_model=CleanupReport, response_model_exclude_none=True)
async def git_cleanup() -> CleanupReport:
    """Classify stale branches and removable worktrees without changing git state."""
    return await asyncio.to_thread(compute_git_cleanup)
