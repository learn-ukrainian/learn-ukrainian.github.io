#!/usr/bin/env python3
"""Safely reap finished repository worktrees.

The CLI is intentionally safe by default: ``--dry-run`` is the default mode,
only paths under the repository's ``.worktrees/`` directory are eligible, and
dirty worktrees are preserved unless ``--preserve-then-reap`` is explicit.

Suggested backstop:

    .venv/bin/python scripts/orchestration/reap_worktrees.py --apply
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.common.acp_runtime_lock import (
    holds_only_git_pointer,
)
from scripts.common.acp_runtime_lock import (
    owner_alive as acp_lock_owner_alive,
)
from scripts.common.acp_runtime_lock import (
    parse_lock_owner as parse_acp_lock_owner,
)
from scripts.control_plane.storage import StoreId
from scripts.control_plane.storage import connect as cp_connect
from scripts.orchestration import reaper_lifecycle
from scripts.path_safety import assert_delete_target

DEFAULT_BUILD_AGE_HOURS = 6
# After the owning agent exits, a sandbox can keep a CPU pinned with no new
# work. This is only the flush window, not a session cap: a live owner is
# never killed, however long the session has already run.
ORPHAN_IDLE_GRACE_S = 120
ORPHAN_MAX_AGE_S = 7200
_ORPHAN_SANDBOX_COMM = "codex-linux-sandbox"
_WORKSPACE_MTIME_SKIP = frozenset({".git", "node_modules", ".venv", "__pycache__"})
_REVIEW_PR_RE = re.compile(r"(?:^|/)review-(\d+)(?:-|$)")

_GIT_ENV_DENYLIST = {
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_NAMESPACE",
    "GIT_CEILING_DIRECTORIES",
    "GIT_DISCOVERY_ACROSS_FILESYSTEM",
    "GIT_COMMON_DIR",
}


@dataclass(frozen=True)
class WorktreeInfo:
    path: Path
    branch: str | None
    head: str | None
    detached: bool = False
    locked_reason: str | None = None


@dataclass(frozen=True)
class PullRequestState:
    number: int | None
    state: str
    head_sha: str | None = None


@dataclass(frozen=True)
class ReapResult:
    path: str
    branch: str | None
    action: str
    reason: str
    dirty: bool | None
    pr: dict[str, Any] | None = None
    error: str | None = None
    branch_pruned: bool = False
    recovery_ref: str | None = None
    owner: str | None = None


def sanitized_git_env() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if key not in _GIT_ENV_DENYLIST and not key.startswith("PRE_COMMIT")
    }


def _run(
    args: list[str],
    *,
    cwd: Path,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
        env=sanitized_git_env(),
    )


def resolve_repo_root(cwd: Path | None = None) -> Path:
    """Resolve the current git worktree root."""
    start = cwd or Path.cwd()
    proc = _run(["git", "rev-parse", "--show-toplevel"], cwd=start)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "not inside a git repository").strip()
        raise RuntimeError(detail)
    return Path((proc.stdout or "").strip()).resolve()


def primary_checkout_root(repo_root: Path) -> Path:
    """Return the primary checkout root that owns the shared .git dir."""
    git_path = repo_root / ".git"
    if git_path.is_dir():
        return repo_root
    if not git_path.is_file():
        return repo_root

    try:
        first_line = git_path.read_text(encoding="utf-8").splitlines()[0]
    except (IndexError, OSError):
        return repo_root
    prefix = "gitdir:"
    if not first_line.startswith(prefix):
        return repo_root

    git_dir = Path(first_line[len(prefix):].strip())
    if not git_dir.is_absolute():
        git_dir = repo_root / git_dir
    git_dir = git_dir.resolve()
    if git_dir.parent.name != "worktrees":
        return repo_root
    common_git_dir = git_dir.parent.parent
    if common_git_dir.name != ".git":
        return repo_root
    return common_git_dir.parent


def _format_failure(proc: subprocess.CompletedProcess[str]) -> str:
    detail = (proc.stderr or proc.stdout or "").strip()
    if detail:
        return detail.splitlines()[-1]
    return f"exit {proc.returncode}"


def _branch_name(raw: str) -> str:
    for prefix in ("refs/heads/", "refs/remotes/origin/"):
        if raw.startswith(prefix):
            return raw[len(prefix):]
    return raw


def parse_worktree_porcelain(output: str) -> list[WorktreeInfo]:
    entries: list[WorktreeInfo] = []
    current: dict[str, Any] | None = None

    def finish() -> None:
        nonlocal current
        if current and current.get("path"):
            entries.append(
                WorktreeInfo(
                    path=Path(current["path"]).resolve(),
                    branch=current.get("branch"),
                    head=current.get("head"),
                    detached=bool(current.get("detached")),
                    locked_reason=current.get("locked_reason"),
                )
            )
        current = None

    for line in output.splitlines():
        if not line:
            finish()
            continue
        if line.startswith("worktree "):
            finish()
            current = {"path": line.removeprefix("worktree ").strip()}
            continue
        if current is None:
            continue
        if line.startswith("HEAD "):
            current["head"] = line.removeprefix("HEAD ").strip()
        elif line.startswith("branch "):
            current["branch"] = _branch_name(line.removeprefix("branch ").strip())
        elif line == "detached":
            current["detached"] = True
        elif line == "locked":
            current["locked_reason"] = current.get("locked_reason") or ""
        elif line.startswith("locked "):
            current["locked_reason"] = line.removeprefix("locked ").strip()
    finish()
    return entries


def list_git_worktrees(repo_root: Path) -> list[WorktreeInfo]:
    proc = _run(["git", "worktree", "list", "--porcelain"], cwd=repo_root)
    if proc.returncode != 0:
        raise RuntimeError(f"git worktree list failed: {_format_failure(proc)}")
    return parse_worktree_porcelain(proc.stdout or "")


def _worktrees_root(repo_root: Path) -> Path:
    return (repo_root / ".worktrees").resolve()


def is_under_worktrees(repo_root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(_worktrees_root(repo_root))
    except ValueError:
        return False
    return True


def _worktree_clean(path: Path) -> bool | None:
    """Return True when the worktree has no meaningful dirty files.

    Dispatch workers often leave an untracked ``.venv`` (or nested site
    venv) which must not block reaping multi-hundred-MB trees.
    """
    proc = _run(["git", "status", "--porcelain", "-uall"], cwd=path)
    if proc.returncode != 0:
        return None
    ignored_prefixes = (".venv/", ".venv", "node_modules/", "node_modules")
    for raw in (proc.stdout or "").splitlines():
        if len(raw) < 4:
            continue
        rel = raw[3:].strip().strip('"')
        if rel in ignored_prefixes or rel.startswith((".venv/", "node_modules/")):
            continue
        return False
    return True


# The states `gh pr list` can report. Anything else is an UNKNOWN, never
# an absence -- callers read "no open PR" as permission to delete.
_PR_STATES = frozenset({"OPEN", "MERGED", "CLOSED"})

_GH_REMOTE_RE = re.compile(r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$")


def _github_owner_repo(repo_root: Path) -> tuple[str, str] | None:
    """Parse the origin remote into an (owner, repo) pair without a network call."""
    proc = _run(["git", "remote", "get-url", "origin"], cwd=repo_root)
    if proc.returncode != 0:
        return None
    match = _GH_REMOTE_RE.search((proc.stdout or "").strip())
    if match is None:
        return None
    return match.group("owner"), match.group("repo")


def _parse_rest_pr_item(item: Any) -> tuple[PullRequestState | None, str | None]:
    """Map one REST pull object onto ``PullRequestState``; unreadable is an error."""
    if not isinstance(item, dict):
        return None, "REST PR payload row is not an object"
    number = item.get("number")
    if isinstance(number, bool) or not isinstance(number, int) or number <= 0:
        return None, "REST PR payload row has no usable PR number"
    # ``merged_at`` is authoritative: REST keeps ``state == "closed"`` for both
    # merged and plainly closed PRs.
    merged_at = item.get("merged_at")
    if isinstance(merged_at, str) and merged_at:
        state = "MERGED"
    else:
        raw_state = item.get("state")
        state = str(raw_state).upper() if isinstance(raw_state, str) else ""
        if state not in _PR_STATES:
            return None, "REST PR payload row has an unusable state"
    head = item.get("head")
    head_sha = head.get("sha") if isinstance(head, dict) else None
    return (
        PullRequestState(
            number=number,
            state=state,
            head_sha=str(head_sha) if head_sha else None,
        ),
        None,
    )


def _query_pr_states_rest(repo_root: Path, branch: str) -> tuple[list[PullRequestState], str | None]:
    """Branch-head PR lookup over the REST core quota (#8536).

    ``gh pr list`` runs on the GraphQL quota, which is shared and easily
    exhausted (#8535); ``GET /repos/{owner}/{repo}/pulls?head=...`` answers
    the same question from the core quota, so it is tried first.
    """
    slug = _github_owner_repo(repo_root)
    if slug is None:
        return [], "REST PR lookup failed: origin owner/repo could not be determined"
    owner, repo = slug
    try:
        proc = _run(
            [
                "gh",
                "api",
                "-X",
                "GET",
                f"repos/{owner}/{repo}/pulls",
                "-f",
                f"head={owner}:{branch}",
                "-f",
                "state=all",
                "-f",
                "per_page=10",
            ],
            cwd=repo_root,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.SubprocessError) as exc:
        return [], f"REST PR lookup failed: {exc}"
    if proc.returncode != 0:
        return [], f"REST PR lookup failed: {_format_failure(proc)}"
    try:
        raw_items = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError as exc:
        return [], f"REST PR lookup returned invalid JSON: {exc}"
    if not isinstance(raw_items, list):
        return [], "REST PR lookup returned a non-list payload"
    states: list[PullRequestState] = []
    for item in raw_items:
        parsed, err = _parse_rest_pr_item(item)
        if err is not None or parsed is None:
            return [], err or "REST PR lookup returned an unusable row"
        states.append(parsed)
    return states, None


def _query_pr_states(repo_root: Path, branch: str | None) -> tuple[list[PullRequestState], str | None]:
    if not branch:
        return [], None
    states, rest_error = _query_pr_states_rest(repo_root, branch)
    if rest_error is None:
        return states, None
    states, graphql_error = _query_pr_states_graphql(repo_root, branch)
    if graphql_error is None:
        return states, None
    # Both transports failed: fail closed and keep both reasons so operators
    # can tell a quota outage from a malformed answer.
    return [], f"{rest_error}; {graphql_error}"


def _query_pr_states_graphql(repo_root: Path, branch: str) -> tuple[list[PullRequestState], str | None]:
    try:
        proc = _run(
            [
                "gh",
                "pr",
                "list",
                "--head",
                branch,
                "--state",
                "all",
                "--json",
                "number,state,headRefOid",
            ],
            cwd=repo_root,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.SubprocessError) as exc:
        return [], f"gh pr list failed: {exc}"
    if proc.returncode != 0:
        return [], f"gh pr list failed: {_format_failure(proc)}"
    try:
        raw_items = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError as exc:
        return [], f"gh pr list returned invalid JSON: {exc}"
    if not isinstance(raw_items, list):
        # Without this, a scalar payload (`123`) raises TypeError in the loop
        # below and a mapping would iterate its keys.
        return [], "gh pr list returned a non-list payload"

    states: list[PullRequestState] = []
    for item in raw_items:
        # A row we cannot read is an UNKNOWN, never an absence. Silently
        # skipping it made `[null]` / `[{}]` parse as "no open PR", and every
        # caller reads an empty list as permission to DELETE the worktree --
        # a destructive fail-open on malformed input. Routing it through the
        # existing error channel makes all callers retain instead, since each
        # one already treats a non-None error as skip/retain.
        parsed, err = _parse_pr_item(item)
        if err is not None or parsed is None:
            return [], err or "gh pr list returned an unusable row"
        states.append(parsed)
    return states, None


def review_pr_number(branch: str | None) -> int | None:
    """Return the PR number encoded in a review branch, if the name has one.

    Review checkouts are named ``<agent>/review-<number>-<slot>``. They are not
    the PR head branch, so ``gh pr list --head`` does not see the merged PR.
    """
    if not branch:
        return None
    name = branch
    for prefix in ("refs/heads/", "refs/remotes/origin/"):
        if name.startswith(prefix):
            name = name[len(prefix) :]
            break
    match = _REVIEW_PR_RE.search(name)
    if match is None:
        return None
    return int(match.group(1))


def _parse_pr_item(item: Any) -> tuple[PullRequestState | None, str | None]:
    if not isinstance(item, dict):
        return None, "gh pr payload row is not an object"
    raw_state = item.get("state")
    state = str(raw_state).upper() if isinstance(raw_state, str) else ""
    if state not in _PR_STATES:
        return None, "gh pr payload row has an unusable state"
    number = item.get("number")
    if isinstance(number, bool) or not isinstance(number, int) or number <= 0:
        return None, "gh pr payload row has no usable PR number"
    head = item.get("headRefOid")
    return (
        PullRequestState(
            number=number,
            state=state,
            head_sha=str(head) if head else None,
        ),
        None,
    )


def _is_not_a_pull_request_error(message: str) -> bool:
    """True when ``gh pr view`` says the number is not a PR (e.g. an issue)."""
    return "Could not resolve to a PullRequest" in message


def _query_pr_by_number_rest(repo_root: Path, number: int) -> tuple[list[PullRequestState], str | None]:
    """Single-PR lookup over the REST core quota (#8536)."""
    slug = _github_owner_repo(repo_root)
    if slug is None:
        return [], "REST PR lookup failed: origin owner/repo could not be determined"
    owner, repo = slug
    try:
        proc = _run(
            ["gh", "api", "-X", "GET", f"repos/{owner}/{repo}/pulls/{number}"],
            cwd=repo_root,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.SubprocessError) as exc:
        return [], f"REST PR lookup failed: {exc}"
    if proc.returncode != 0:
        return [], f"REST PR lookup failed: {_format_failure(proc)}"
    try:
        item = json.loads(proc.stdout or "null")
    except json.JSONDecodeError as exc:
        return [], f"REST PR lookup returned invalid JSON: {exc}"
    parsed, err = _parse_rest_pr_item(item)
    if err is not None or parsed is None:
        return [], err or "REST PR lookup returned an unusable payload"
    return [parsed], None


def _query_pr_by_number(repo_root: Path, number: int) -> tuple[list[PullRequestState], str | None]:
    """Look up one PR by number. Fail closed: an unreadable answer is an error."""
    states, rest_error = _query_pr_by_number_rest(repo_root, number)
    if rest_error is None:
        return states, None
    states, graphql_error = _query_pr_by_number_graphql(repo_root, number)
    if graphql_error is None:
        return states, None
    # The GraphQL reason stays in the combined message: review branches can
    # encode an issue number, and callers recognise the GraphQL "not a
    # PullRequest" answer as an absence rather than an unreadable guard.
    return [], f"{rest_error}; {graphql_error}"


def _query_pr_by_number_graphql(repo_root: Path, number: int) -> tuple[list[PullRequestState], str | None]:
    try:
        proc = _run(
            [
                "gh",
                "pr",
                "view",
                str(number),
                "--json",
                "number,state,headRefOid",
            ],
            cwd=repo_root,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.SubprocessError) as exc:
        return [], f"gh pr view failed: {exc}"
    if proc.returncode != 0:
        return [], f"gh pr view failed: {_format_failure(proc)}"
    try:
        item = json.loads(proc.stdout or "null")
    except json.JSONDecodeError as exc:
        return [], f"gh pr view returned invalid JSON: {exc}"
    parsed, err = _parse_pr_item(item)
    if err is not None or parsed is None:
        return [], err or "gh pr view returned an unusable payload"
    return [parsed], None


@dataclass(frozen=True)
class SandboxProcess:
    """One process row used to decide whether a Codex sandbox is still working."""

    pid: int
    ppid: int
    comm: str
    cwd: Path | None
    age_s: float
    workspace_mtime: float | None = None


def latest_workspace_mtime(root: Path) -> float | None:
    """Newest mtime under ``root``, skipping VCS and dependency trees."""
    try:
        latest = root.stat().st_mtime
    except OSError:
        return None
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in _WORKSPACE_MTIME_SKIP]
        for name in filenames:
            try:
                mtime = os.stat(os.path.join(dirpath, name)).st_mtime
            except OSError:
                continue
            if mtime > latest:
                latest = mtime
    return latest


def select_orphaned_sandboxes(
    processes: list[SandboxProcess],
    *,
    repo_root: Path,
    now: float,
    idle_grace_s: float = ORPHAN_IDLE_GRACE_S,
    max_age_s: float = ORPHAN_MAX_AGE_S,
) -> list[int]:
    """Return pids of Codex sandboxes whose agent is no longer working.

    A live owner (ppid != 1) is a running session and is never selected, at
    any age. An init-reparented sandbox is selected when its worktree has
    gone quiet or its age reaches the hard cap, even if it is still writing.
    """
    worktrees = (repo_root / ".worktrees").resolve()
    selected: list[int] = []
    for proc in processes:
        if proc.comm != _ORPHAN_SANDBOX_COMM or proc.ppid != 1 or proc.cwd is None:
            continue
        try:
            proc.cwd.resolve().relative_to(worktrees)
        except (OSError, ValueError):
            continue
        if (
            proc.age_s < max_age_s
            and proc.workspace_mtime is not None
            and (now - proc.workspace_mtime) < idle_grace_s
        ):
            continue
        selected.append(proc.pid)
    return selected


def _proc_start_age_s(stat_text: str, *, uptime_s: float, ticks_per_sec: int) -> tuple[int, float] | None:
    """Return ``(ppid, age_s)`` from a ``/proc/<pid>/stat`` line."""
    end = stat_text.rfind(")")
    if end < 0:
        return None
    fields = stat_text[end + 2 :].split()
    # After the comm field, index 0 is state (field 3). ppid is field 4,
    # starttime is field 22.
    if len(fields) <= 19:
        return None
    try:
        ppid = int(fields[1])
        start_ticks = int(fields[19])
    except ValueError:
        return None
    if ticks_per_sec <= 0:
        return None
    return ppid, uptime_s - (start_ticks / ticks_per_sec)


def _read_sandbox_processes(
    proc_root: Path = Path("/proc"), *, repo_root: Path
) -> list[SandboxProcess]:
    try:
        uptime_s = float((proc_root / "uptime").read_text(encoding="utf-8").split()[0])
    except (OSError, ValueError, IndexError):
        return []
    ticks = os.sysconf("SC_CLK_TCK") if hasattr(os, "sysconf") else 100
    found: list[SandboxProcess] = []
    try:
        entries = list(proc_root.iterdir())
    except OSError:
        return []
    for entry in entries:
        if not entry.name.isdigit():
            continue
        try:
            comm = (entry / "comm").read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if comm != _ORPHAN_SANDBOX_COMM:
            continue
        try:
            stat_text = (entry / "stat").read_text(encoding="utf-8")
        except OSError:
            continue
        parsed = _proc_start_age_s(stat_text, uptime_s=uptime_s, ticks_per_sec=int(ticks))
        if parsed is None:
            continue
        ppid, age_s = parsed
        try:
            cwd = Path(os.readlink(entry / "cwd"))
        except OSError:
            cwd = None
        found.append(
            SandboxProcess(
                pid=int(entry.name),
                ppid=ppid,
                comm=comm,
                cwd=cwd,
                age_s=age_s,
                workspace_mtime=(
                    latest_workspace_mtime(cwd)
                    if ppid == 1 and cwd is not None and is_under_worktrees(repo_root, cwd)
                    else None
                ),
            )
        )
    return found


def _descendant_pids(root_pid: int, proc_root: Path = Path("/proc")) -> list[int]:
    children: dict[int, list[int]] = {}
    try:
        entries = list(proc_root.iterdir())
    except OSError:
        return []
    for entry in entries:
        if not entry.name.isdigit():
            continue
        try:
            stat_text = (entry / "stat").read_text(encoding="utf-8")
        except OSError:
            continue
        parsed = _proc_start_age_s(stat_text, uptime_s=0.0, ticks_per_sec=1)
        if parsed is None:
            continue
        ppid, _age = parsed
        children.setdefault(ppid, []).append(int(entry.name))
    ordered: list[int] = []
    stack = list(children.get(root_pid, []))
    seen = {root_pid}
    while stack:
        pid = stack.pop()
        if pid in seen:
            continue
        seen.add(pid)
        ordered.append(pid)
        stack.extend(children.get(pid, []))
    return ordered


def stop_orphaned_sandboxes(
    repo_root: Path,
    *,
    now: float | None = None,
    idle_grace_s: float = ORPHAN_IDLE_GRACE_S,
    max_age_s: float = ORPHAN_MAX_AGE_S,
    proc_root: Path = Path("/proc"),
) -> list[int]:
    """SIGKILL ownerless Codex sandboxes once quiet or past the hard age cap.

    Returns the sandbox pids that were signaled. A sandbox still owned by its
    agent is never touched, however long that session has been running.
    """
    selected = select_orphaned_sandboxes(
        _read_sandbox_processes(proc_root, repo_root=repo_root),
        repo_root=repo_root,
        now=time.time() if now is None else now,
        idle_grace_s=idle_grace_s,
        max_age_s=max_age_s,
    )
    signaled: list[int] = []
    for pid in selected:
        victims = [*_descendant_pids(pid, proc_root), pid]
        for victim in victims:
            try:
                os.kill(victim, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                continue
        signaled.append(pid)
    return signaled


def _best_pr(prs: list[PullRequestState]) -> PullRequestState | None:
    # A branch name can be reused. Any open PR is therefore authoritative over
    # historical merged/closed PRs for the same head name.
    for desired in ("OPEN", "MERGED", "CLOSED"):
        for pr_state in prs:
            if pr_state.state == desired:
                return pr_state
    return prs[0] if prs else None


def _query_prs_by_head_sha(
    repo_root: Path,
    head_sha: str | None,
) -> list[PullRequestState]:
    """Find PRs that introduced ``head_sha`` by GitHub commit-SHA search.

    Follow-up CI branches carry a different branch name than the MERGED PR head
    they fix, so ``gh pr list --head <branch>`` misses them.  A search hit means
    ``head_sha`` is a commit added by that PR, i.e. it equals the PR head or is
    an ancestor of it.  Failures are swallowed: this lookup is supplementary to
    the authoritative ``gh pr list --head`` guard and must never fabricate a
    PR-guard error on its own.
    """
    if not head_sha:
        return []
    try:
        proc = _run(
            ["gh", "search", "prs", head_sha, "--json", "number,state"],
            cwd=repo_root,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        return []
    if proc.returncode != 0:
        return []
    try:
        raw_items = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError:
        return []

    states: list[PullRequestState] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        state = str(item.get("state") or "").upper()
        if not state:
            continue
        number = item.get("number")
        states.append(
            PullRequestState(
                number=number if isinstance(number, int) else None,
                state=state,
                head_sha=head_sha,
            )
        )
    return states


def _pr_dict(pr_state: PullRequestState | None) -> dict[str, Any] | None:
    if pr_state is None:
        return None
    return {
        "number": pr_state.number,
        "state": pr_state.state,
        "head_sha": pr_state.head_sha,
    }


def _candidate_branches_for_worktree(repo_root: Path, info: WorktreeInfo) -> list[str]:
    if info.branch is not None:
        return [info.branch]

    candidates: list[str] = []
    dispatch_root = (repo_root / ".worktrees" / "dispatch").resolve()
    try:
        rel = info.path.resolve().relative_to(dispatch_root)
        if len(rel.parts) == 2:
            candidates.append(f"{rel.parts[0]}/{rel.parts[1]}")
    except ValueError:
        pass

    wt_root = _worktrees_root(repo_root)
    try:
        rel_wt = info.path.resolve().relative_to(wt_root)
        rel_str = str(rel_wt)
        if rel_str and rel_str not in candidates:
            candidates.append(rel_str)
        if "-" in rel_str and "/" not in rel_str:
            slash_conv = rel_str.replace("-", "/", 1)
            if slash_conv not in candidates:
                candidates.append(slash_conv)
    except ValueError:
        pass

    return candidates


def _worktree_review_pr_number(repo_root: Path, info: WorktreeInfo) -> int | None:
    for branch in _candidate_branches_for_worktree(repo_root, info):
        number = review_pr_number(branch)
        if number is not None:
            return number
    return None


def _sha_is_ancestor(cwd: Path, sha: str, descendant: str) -> bool:
    """True when ``sha`` is an ancestor of ``descendant``. A git error is not."""
    proc = _run(
        ["git", "merge-base", "--is-ancestor", sha, descendant],
        cwd=cwd,
    )
    return proc.returncode == 0


def _pr_matches_worktree_head(
    info: WorktreeInfo,
    pr_state: PullRequestState | None,
) -> bool:
    """True when the tip is the PR head or an ancestor of that head.

    Callers use this as deletion proof for worktree removal and for merged
    branch pruning. An identical tree at a divergent commit is not
    containment; ``_same_tree_hint`` may report it, and it never returns true
    here. Ancestor of ``origin/main`` is a separate proof, checked beside this
    one. A git error is not ancestry.
    """
    if pr_state is None or not pr_state.head_sha or not info.head:
        return False
    if pr_state.head_sha == info.head:
        return True
    return _sha_is_ancestor(info.path, info.head, pr_state.head_sha)


def _tip_is_ancestor_of_origin_main(info: WorktreeInfo) -> bool:
    """True when the recorded tip, not a same-tree sibling, is on origin/main."""
    if not info.head:
        return False
    return _sha_is_ancestor(info.path, info.head, "origin/main")


def _same_tree_hint(
    info: WorktreeInfo,
    pr_state: PullRequestState | None,
) -> str | None:
    """Report an identical tree. Never deletion proof.

    ``git diff --quiet`` is 0 only when both objects exist and the trees
    match. A missing or dummy head, or any diff, is not a hint.
    """
    if pr_state is None or not pr_state.head_sha or not info.head:
        return None
    if pr_state.head_sha == info.head:
        return None
    tree = _run(
        ["git", "diff", "--quiet", pr_state.head_sha, info.head],
        cwd=info.path,
    )
    if tree.returncode != 0:
        return None
    label = f"PR #{pr_state.number}" if pr_state.number is not None else "PR"
    return f"same tree as {label} head; not deletion proof"


def _live_cwd_paths(repo_root: Path) -> set[Path] | None:
    """Return process working directories, or ``None`` when lsof is unavailable."""
    try:
        proc = _run(["lsof", "-d", "cwd", "-F", "n"], cwd=repo_root, timeout=15)
    except (FileNotFoundError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    paths: set[Path] = set()
    for line in (proc.stdout or "").splitlines():
        if not line.startswith("n/"):
            continue
        try:
            paths.add(Path(line[1:]).resolve())
        except OSError:
            continue
    return paths


def _path_contains(parent: Path, child: Path) -> bool:
    try:
        child.relative_to(parent)
    except ValueError:
        return False
    return True


def _dispatch_task_id(repo_root: Path, info: WorktreeInfo) -> str | None:
    dispatch_root = (repo_root / ".worktrees" / "dispatch").resolve()
    try:
        relative = info.path.resolve().relative_to(dispatch_root)
    except ValueError:
        return None
    return relative.parts[1] if len(relative.parts) == 2 else None


def _dispatch_owner(repo_root: Path, info: WorktreeInfo) -> str:
    dispatch_root = (repo_root / ".worktrees" / "dispatch").resolve()
    try:
        relative = info.path.resolve().relative_to(dispatch_root)
        if len(relative.parts) >= 1 and relative.parts[0]:
            return relative.parts[0]
    except ValueError:
        pass
    if info.branch:
        branch_name = info.branch
        for prefix in ("refs/heads/", "refs/remotes/origin/"):
            if branch_name.startswith(prefix):
                branch_name = branch_name[len(prefix) :]
                break
        if "/" in branch_name:
            owner = branch_name.split("/", 1)[0]
            if owner in {"codex", "claude", "agy", "grok", "cursor", "hermes"}:
                return owner
    return "unattributed"


_ACP_RUNTIME_REASON_PREFIX = "acp runtime "
_ACP_LEGACY_LOCK_MIN_AGE_HOURS = 24.0
# Minimum age for a zero-file dispatch husk before it may be removed.
# ``delegate.py`` creates the dispatch directory before ``git worktree add``
# registers it, so an unregistered empty directory can be mid-creation; the
# provisioning window is seconds, and one hour bounds it with a wide margin
# while still reaping same-day debris.
_DISPATCH_HUSK_MIN_AGE_HOURS = 1.0


def _is_acp_runtime_path(repo_root: Path, path: Path) -> bool:
    """True for a ``runtime-*`` child of ``.worktrees/dispatch/acp/`` itself."""
    acp_root = (repo_root / ".worktrees" / "dispatch" / "acp").resolve()
    try:
        relative = path.resolve().relative_to(acp_root)
    except (OSError, ValueError):
        return False
    return len(relative.parts) == 1 and relative.parts[0].startswith("runtime-")


def _acp_dead_owner_reason(
    *,
    repo_root: Path,
    info: WorktreeInfo,
    now: float | None,
    live_cwds: set[Path] | None,
) -> str | None:
    """Provably-safe reap class for abandoned ACP runtime worktrees (#8344).

    A cancelled or killed ACP ask leaves a detached, no-checkout, locked
    ``runtime-*`` worktree that no other class can clear. Owner-tagged locks
    qualify only when the recorded pid is provably dead (absent, or recycled
    with a different process start time). Legacy locks without owner
    information qualify only past 24h with a conclusive no-live-cwd probe.
    Alive or unknown owners are never eligible; this class never consults PR
    state, so it stays available under --safe-only.
    """
    if not info.detached or info.branch is not None:
        return None
    if not _is_acp_runtime_path(repo_root, info.path):
        return None
    owner = parse_acp_lock_owner(info.locked_reason)
    if owner is None:
        return None
    pid, start_time = owner
    if pid is not None:
        if acp_lock_owner_alive(pid, start_time) is not False:
            return None
        return f"{_ACP_RUNTIME_REASON_PREFIX}lock owner pid={pid} is provably dead"
    age_hours = _worktree_age_hours(info.path, now=now)
    if age_hours is None or age_hours <= _ACP_LEGACY_LOCK_MIN_AGE_HOURS:
        return None
    if live_cwds is None:
        return None
    worktree = info.path.resolve()
    if any(_path_contains(worktree, cwd) for cwd in live_cwds):
        return None
    return (
        f"{_ACP_RUNTIME_REASON_PREFIX}legacy lock age {age_hours:.1f}h "
        f"> {_ACP_LEGACY_LOCK_MIN_AGE_HOURS:g}h; no live process cwd"
    )


def _acp_runtime_cleanup_recheck(repo_root: Path, info: WorktreeInfo) -> str | None:
    """Re-prove every ACP runtime precondition immediately before deletion."""
    fresh: WorktreeInfo | None = None
    for current in list_git_worktrees(repo_root):
        if current.path.resolve() == info.path.resolve():
            fresh = current
            break
    if fresh is None:
        return "acp runtime worktree unregistered during cleanup"
    live_cwds = _live_cwd_paths(repo_root)
    if live_cwds is None:
        return "process-CWD activity probe unavailable during cleanup"
    if _acp_dead_owner_reason(
        repo_root=repo_root,
        info=fresh,
        now=None,
        live_cwds=live_cwds,
    ) is None:
        return "acp runtime lock owner changed during cleanup"
    if not holds_only_git_pointer(info.path):
        return "acp runtime worktree gained files during cleanup"
    return None


def _tree_has_any_file_or_symlink(root: Path) -> bool:
    """True when ``root`` holds any file, symlink, or metadata entry.

    Unreadable directories fail closed and read as non-empty.
    """
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    if entry.is_symlink() or not entry.is_dir(follow_symlinks=False):
                        return True
                    stack.append(Path(entry.path))
        except OSError:
            return True
    return False


def _tree_newest_age_hours(root: Path, now: float | None = None) -> float | None:
    """Age in hours of the newest mtime anywhere in ``root``'s subtree.

    A directory whose subtree was touched recently must not read as old, so
    the top-level mtime alone is not sufficient. ``None`` when any directory
    is unreadable, so callers fail closed.
    """
    try:
        newest = root.stat().st_mtime
    except OSError:
        return None
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            newest = max(newest, entry.stat(follow_symlinks=False).st_mtime)
                            stack.append(Path(entry.path))
                    except OSError:
                        return None
        except OSError:
            return None
    return ((now or time.time()) - newest) / 3600


def _reap_dispatch_husks(
    repo_root: Path,
    *,
    registered: set[Path],
    apply: bool,
    live_cwds: set[Path] | None,
    targets: set[Path] | None,
    now: float | None = None,
) -> list[ReapResult]:
    """Report — and with ``apply`` remove — zero-file dispatch husks (#8344).

    Unregistered placeholder directories under ``.worktrees/dispatch/<agent>/``
    (only empty subdirectories, e.g. ``site/ node_modules/ data/``) are
    invisible to ``git worktree list`` and accumulate forever. A directory
    containing any file, symlink, or git metadata is never touched by this
    rule. Every other guard fails closed too: an unavailable process-CWD
    probe, a live process cwd inside, or a youngest-mtime age below
    ``_DISPATCH_HUSK_MIN_AGE_HOURS`` (measured across the whole subtree, so a
    directory still being provisioned is never "old") all preserve.
    """
    results: list[ReapResult] = []
    dispatch_root = repo_root / ".worktrees" / "dispatch"
    if not dispatch_root.is_dir():
        return results
    for agent_dir in sorted(dispatch_root.iterdir()):
        if agent_dir.is_symlink() or not agent_dir.is_dir():
            continue
        for child in sorted(agent_dir.iterdir()):
            if child.is_symlink() or not child.is_dir():
                continue
            resolved = child.resolve()
            if resolved in registered:
                continue
            if targets is not None and resolved not in targets:
                continue
            owner = agent_dir.name or "unattributed"
            if _tree_has_any_file_or_symlink(resolved):
                continue
            reason = "unregistered dispatch directory contains zero files (empty placeholder husk)"
            if live_cwds is None:
                results.append(
                    ReapResult(
                        path=str(child),
                        branch=None,
                        action="skipped",
                        reason="process-CWD activity probe unavailable",
                        dirty=None,
                        owner=owner,
                    )
                )
                continue
            if any(_path_contains(resolved, cwd) for cwd in live_cwds):
                results.append(
                    ReapResult(
                        path=str(child),
                        branch=None,
                        action="skipped",
                        reason="live process cwd inside unregistered empty directory",
                        dirty=None,
                        owner=owner,
                    )
                )
                continue
            age_hours = _tree_newest_age_hours(resolved, now=now)
            if age_hours is None:
                results.append(
                    ReapResult(
                        path=str(child),
                        branch=None,
                        action="skipped",
                        reason="could not determine husk age; treating as in use",
                        dirty=None,
                        owner=owner,
                    )
                )
                continue
            if age_hours < _DISPATCH_HUSK_MIN_AGE_HOURS:
                results.append(
                    ReapResult(
                        path=str(child),
                        branch=None,
                        action="skipped",
                        reason=(
                            f"empty placeholder husk is only {age_hours:.1f}h old "
                            f"(< {_DISPATCH_HUSK_MIN_AGE_HOURS:g}h minimum)"
                        ),
                        dirty=None,
                        owner=owner,
                    )
                )
                continue
            if not apply:
                reaper_lifecycle.append_journal(
                    repo_root,
                    "observe",
                    path=str(child),
                    branch=None,
                    head=None,
                    reason=reason,
                    pr=None,
                )
                results.append(
                    ReapResult(
                        path=str(child),
                        branch=None,
                        action="would_remove",
                        reason=reason,
                        dirty=False,
                        owner=owner,
                    )
                )
                continue
            if os.environ.get("LU_REAPER_DISABLED") == "1":
                results.append(
                    ReapResult(
                        path=str(child),
                        branch=None,
                        action="skipped",
                        reason="reaper disabled by LU_REAPER_DISABLED=1",
                        dirty=False,
                        owner=owner,
                    )
                )
                continue
            reaper_lifecycle.append_journal(
                repo_root,
                "plan",
                path=str(child),
                branch=None,
                head=None,
                reason=reason,
                pr=None,
            )
            try:
                target = assert_delete_target(child, repo_root=repo_root)
                shutil.rmtree(target)
            except (ValueError, OSError) as exc:
                results.append(
                    ReapResult(
                        path=str(child),
                        branch=None,
                        action="error",
                        reason=reason,
                        dirty=False,
                        owner=owner,
                        error=str(exc),
                    )
                )
                continue
            results.append(
                ReapResult(
                    path=str(child),
                    branch=None,
                    action="removed",
                    reason=reason,
                    dirty=False,
                    owner=owner,
                )
            )
    return results


def classify_preservation(result: ReapResult) -> str:
    if result.action in {"removed", "preserved_then_removed", "would_remove", "would_preserve_then_remove"}:
        return "eligible"
    if result.action == "error":
        err_lower = f"{result.error or ''} {result.reason or ''}".lower()
        if "permission" in err_lower or "denied" in err_lower or "access" in err_lower:
            return "permission_error"
        return "error"
    reason = result.reason.lower()
    if "permission" in reason or "denied" in reason:
        return "permission_error"
    if "primary checkout" in reason:
        return "primary"
    if (
        "active dispatch" in reason
        or "non-terminal dispatch" in reason
        or "live process" in reason
        or "lease" in reason
        or "claim" in reason
        or "reservation" in reason
    ):
        return "active_dispatch"
    if (result.pr and result.pr.get("state") == "OPEN") or ("open" in reason and "pr" in reason):
        return "open_pr"
    if result.dirty is True or reason.startswith("dirty"):
        return "dirty"
    if "unpushed" in reason or "not merged" in reason or "no reap condition" in reason or "ancestry" in reason:
        return "unmerged"
    if (
        "detached" in reason
        or "missing branch" in reason
        or "unknown" in reason
        or "unavailable" in reason
        or "unable to determine" in reason
    ):
        return "detached_unknown"
    if "outside repo" in reason or "foreign" in reason or "not a registered" in reason:
        return "foreign"
    return "uncertain"


# Packet fields that may name the worktree path a live rollover protects.
# ``thread_handoff.source_checkout_binding`` historically recorded only the
# source HEAD SHA; matching on that SHA protected every sibling worktree
# created from the same commit, from any lane (#8536). Protection is by
# recorded path only: a packet that names no path protects nothing (the
# primary checkout is never reaped anyway).
_ROLLOVER_SOURCE_PATH_KEYS = ("path", "repo_root", "worktree", "worktree_path")
_ROLLOVER_PROTECTED_LIST_KEYS = ("protected_worktrees", "protected_paths", "worktrees")


def _normalize_rollover_path(raw: Any, base: Path) -> str | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    try:
        path = Path(raw)
        if not path.is_absolute():
            path = base / path
        return os.path.realpath(path)
    except OSError:
        return None


def _rollover_protected_paths(data: dict[str, Any], base: Path) -> set[str]:
    paths: set[str] = set()
    replacement = data.get("replacement")
    if not isinstance(replacement, dict):
        replacement = {}
    source_checkout = replacement.get("source_checkout")
    if isinstance(source_checkout, dict):
        for key in _ROLLOVER_SOURCE_PATH_KEYS:
            normalized = _normalize_rollover_path(source_checkout.get(key), base)
            if normalized:
                paths.add(normalized)
    for container in (data, replacement):
        for key in _ROLLOVER_PROTECTED_LIST_KEYS:
            entries = container.get(key)
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if isinstance(entry, dict):
                    normalized = _normalize_rollover_path(entry.get("path") or entry.get("worktree"), base)
                else:
                    normalized = _normalize_rollover_path(entry, base)
                if normalized:
                    paths.add(normalized)
    return paths


def _has_active_rollover_lease(repo_root: Path, info: WorktreeInfo) -> str | None:
    primary = primary_checkout_root(repo_root)
    worktree_path = os.path.realpath(info.path)
    for candidate_dir in (
        primary / ".agent" / "thread-rollovers",
        primary / "batch_state" / "thread-rollovers",
    ):
        if not candidate_dir.is_dir():
            continue
        try:
            for lease_file in candidate_dir.glob("*/*/lease.json"):
                try:
                    data = json.loads(lease_file.read_text(encoding="utf-8"))
                    if not isinstance(data, dict):
                        continue
                    cleanup_info = data.get("cleanup", {})
                    if cleanup_info.get("old_automation_ready_to_delete") is True:
                        continue
                    replacement = data.get("replacement", {})
                    active = replacement.get("status") in {"prepared", "pending_start", "resumed"}
                    if active and worktree_path in _rollover_protected_paths(data, primary):
                        return f"active rollover lease {lease_file.parent.name}"
                except Exception:
                    continue
        except Exception:
            continue
    return None


def _has_active_ownership_claim(repo_root: Path, task_id: str | None) -> str | None:
    if not task_id:
        return None
    env_override = (os.environ.get("LEARN_UKRAINIAN_OWNERSHIP_LEDGER") or "").strip()
    if env_override:
        db_path = Path(env_override).expanduser().resolve()
    else:
        db_path = primary_checkout_root(repo_root) / "batch_state" / "tasks" / "write-ownership.sqlite3"
        if not db_path.is_file():
            return None
    try:
        conn = cp_connect(StoreId.WRITE_OWNERSHIP, path=db_path, read_only=True)
        try:
            cur = conn.cursor()
            cur.execute("SELECT task_id, pid FROM write_claims WHERE task_id = ?", (task_id,))
            rows = cur.fetchall()
            for _row_tid, row_pid in rows:
                if row_pid is not None and int(row_pid) > 0:
                    try:
                        os.kill(int(row_pid), 0)
                        return f"active write claim task-id={task_id}"
                    except (ProcessLookupError, ValueError):
                        pass
                    except PermissionError:
                        return f"active write claim task-id={task_id}"
        finally:
            conn.close()
    except Exception as exc:
        return f"active write claim check failed task-id={task_id}: {exc}"
    return None


def _task_record(repo_root: Path, task_id: str | None) -> dict[str, Any] | None:
    if not task_id:
        return None
    task_file = primary_checkout_root(repo_root) / "batch_state" / "tasks" / f"{task_id}.json"
    try:
        payload = json.loads(task_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _task_record_status(repo_root: Path, task_id: str | None) -> str | None:
    payload = _task_record(repo_root, task_id)
    if payload is None:
        return None
    status = payload.get("status")
    return str(status) if status else None


def _task_pid_alive(payload: dict[str, Any] | None) -> bool:
    """Return True only when task JSON names a live process."""
    if not payload:
        return False
    raw_pid = payload.get("pid")
    if raw_pid is None:
        return False
    try:
        pid = int(raw_pid)
    except (TypeError, ValueError):
        return False
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # Exists but not signalable by this user — treat as live.
        return True
    return True


def _activity_reason(
    *,
    repo_root: Path,
    info: WorktreeInfo,
    active_ids: set[str] | None,
    live_cwds: set[Path] | None,
    check_pending: bool = True,
) -> str | None:
    if check_pending and reaper_lifecycle.is_reap_pending(repo_root, info.path):
        return "active reap reservation"

    task_id = _dispatch_task_id(repo_root, info)
    if task_id and active_ids is not None and task_id in active_ids:
        return f"active dispatch task-id={task_id}"
    task_payload = _task_record(repo_root, task_id)
    task_status = None
    if task_payload is not None:
        raw_status = task_payload.get("status")
        task_status = str(raw_status) if raw_status else None
        lease = task_payload.get("lease")
        if isinstance(lease, dict) and lease.get("state") == "active":
            return f"active worker lease task-id={task_id}"
        if task_payload.get("lease_state") == "active":
            return f"active worker lease task-id={task_id}"

    # Stale "running" rows with a dead worker PID must not block reaping forever
    # (observed: multi-hour dispatch workers left status=running after exit).
    if (
        task_status in {"queued", "starting", "running", "needs_finalize"}
        and _task_pid_alive(task_payload)
    ):
        return f"non-terminal dispatch task-id={task_id} status={task_status}"
    if live_cwds is not None:
        worktree = info.path.resolve()
        for cwd in live_cwds:
            if _path_contains(worktree, cwd):
                return f"live process cwd={cwd}"

    rollover_reason = _has_active_rollover_lease(repo_root, info)
    if rollover_reason is not None:
        return rollover_reason

    claim_reason = _has_active_ownership_claim(repo_root, task_id)
    if claim_reason is not None:
        return claim_reason

    return None


def _common_git_dir(repo_root: Path) -> Path:
    proc = _run(["git", "rev-parse", "--git-common-dir"], cwd=repo_root)
    if proc.returncode != 0:
        raise RuntimeError(f"cannot resolve git common dir: {_format_failure(proc)}")
    path = Path((proc.stdout or "").strip())
    if not path.is_absolute():
        path = repo_root / path
    return path.resolve()


class _ReapLock:
    def __init__(self, repo_root: Path) -> None:
        self.path = _common_git_dir(repo_root) / "worktree-reaper.lock"
        self.handle: Any = None

    def __enter__(self) -> None:
        self.handle = self.path.open("a+", encoding="utf-8")
        try:
            fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            self.handle.close()
            raise RuntimeError(f"another worktree cleanup holds {self.path}") from exc

    def __exit__(self, _exc_type: Any, _exc: Any, _tb: Any) -> None:
        if self.handle is not None:
            fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
            self.handle.close()


def _origin_branch_present(path: Path, branch: str | None) -> bool:
    if not branch:
        return False
    verify = _run(
        ["git", "rev-parse", "--verify", "--quiet", f"refs/remotes/origin/{branch}"],
        cwd=path,
    )
    return verify.returncode == 0


def _live_origin_heads_present(path: Path, branch: str | None) -> bool | None:
    """Return whether origin currently has ``branch``. ``None`` if ls-remote failed."""
    if not branch:
        return False
    proc = _run(["git", "ls-remote", "--heads", "origin", branch], cwd=path)
    if proc.returncode != 0:
        return None
    return bool((proc.stdout or "").strip())


def _origin_matches_head(path: Path, branch: str | None) -> bool:
    if not branch:
        return False
    remote_ref = f"origin/{branch}"
    verify = _run(["git", "rev-parse", "--verify", remote_ref], cwd=path)
    if verify.returncode != 0:
        return False
    count = _run(
        ["git", "rev-list", "--left-right", "--count", f"{remote_ref}...HEAD"],
        cwd=path,
    )
    if count.returncode != 0:
        return False
    parts = (count.stdout or "").strip().split()
    return parts == ["0", "0"]


def _worktree_age_hours(path: Path, now: float | None = None) -> float | None:
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return None
    return ((now or time.time()) - mtime) / 3600


def _active_task_ids() -> set[str] | None:
    try:
        import urllib.request
        with urllib.request.urlopen("http://127.0.0.1:8765/api/delegate/active", timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            tasks = data.get("tasks", [])
            return {str(t.get("task_id")) for t in tasks if t.get("task_id")}
    except Exception:
        return None


def _is_ancestor_of_origin_main(path: Path) -> bool:
    proc = _run(["git", "merge-base", "--is-ancestor", "HEAD", "origin/main"], cwd=path)
    return proc.returncode == 0


def _is_head_reachable_from_remote(path: Path, head: str | None = None) -> bool:
    """Return True if ``head`` (or HEAD) is reachable from at least one origin/* ref."""
    target = head or "HEAD"
    proc = _run(
        [
            "git",
            "for-each-ref",
            "--format=%(refname)",
            "--contains",
            target,
            "refs/remotes/origin/",
        ],
        cwd=path,
    )
    if proc.returncode != 0:
        return False
    refs = [line.strip() for line in (proc.stdout or "").splitlines() if line.strip()]
    return bool(refs)


_TERMINAL_DISPATCH_STATUSES = frozenset(
    {
        "done",
        "failed",
        "timeout",
        "rate_limited",
        "cancelled",
        "crashed",
        "dry_run",
        "needs_finalize",
        "no_deliverable",
    }
)


def _is_settled_dispatch_task(
    *,
    repo_root: Path,
    info: WorktreeInfo,
    active_ids: set[str] | None,
) -> tuple[bool, str | None]:
    task_id = _dispatch_task_id(repo_root, info)
    if task_id is None or active_ids is None or task_id in active_ids:
        return False, None
    task_data = _task_record(repo_root, task_id)
    if task_data is None:
        return False, None
    task_status = task_data.get("status")
    if task_status not in _TERMINAL_DISPATCH_STATUSES or _task_pid_alive(task_data):
        return False, None
    return True, str(task_status)


def _terminal_dispatch_reason(
    *,
    repo_root: Path,
    info: WorktreeInfo,
    active_ids: set[str] | None,
) -> str | None:
    """Prove that a dispatch worktree is terminal and no longer owned.

    This deliberately does not infer terminality from a dead PID.  A stale
    ``running`` record may be recoverable; scheduled cleanup may only reap an
    explicit terminal record, a known-empty active-task probe, and a worktree
    HEAD reachable from at least one remote ref (origin/*).
    """
    settled, task_status = _is_settled_dispatch_task(
        repo_root=repo_root,
        info=info,
        active_ids=active_ids,
    )
    if not settled:
        return None
    task_id = _dispatch_task_id(repo_root, info)
    if not _is_head_reachable_from_remote(info.path, info.head):
        return None
    return f"settled dispatch task-id={task_id} status={task_status}"


def _qualifying_reason(
    *,
    repo_root: Path,
    info: WorktreeInfo,
    pr_state: PullRequestState | None,
    build_age_hours: float,
    now: float | None,
    active_ids: set[str] | None = None,
    safe_only: bool = False,
    merged_pr_only: bool = False,
    include_terminal_dispatches: bool = False,
    pr_unknown: bool = False,
) -> str | None:
    """``pr_unknown`` marks the PR state as UNREADABLE rather than absent.

    A failed branch query must not read as "no PR": every reason below that
    consults ``pr_state`` -- directly, or via a ``pr_state is None`` shortcut
    that means "no open PR" -- becomes unsafe, because an OPEN PR may exist
    and simply not be visible. Class B stays available: it never consults
    ``pr_state`` and already requires the head to be an ancestor of
    origin/main or reachable from a remote, so nothing can be lost.
    """
    if pr_state is not None:
        pr_label = f"PR #{pr_state.number}" if pr_state.number is not None else "PR"
        if pr_state.state == "MERGED":
            if _pr_matches_worktree_head(info, pr_state):
                return f"{pr_label} MERGED"
            review_number = _worktree_review_pr_number(repo_root, info)
            if review_number is not None and pr_state.number == review_number:
                if _is_ancestor_of_origin_main(info.path):
                    return f"PR #{review_number} MERGED; review HEAD is on origin/main"
                # Review branches are local-only; a missing origin branch
                # cannot prove that their extra commits are safe to discard.
                return None
            if _tip_is_ancestor_of_origin_main(info):
                return f"{pr_label} MERGED; HEAD is an ancestor of origin/main"
            # Squash merges may leave extra local reconcile commits. A gone
            # origin branch permits cleanup without an exact PR-head match.
            if info.branch is not None and not _origin_branch_present(info.path, info.branch):
                return f"{pr_label} MERGED; origin branch gone"
        if (
            not merged_pr_only
            and pr_state.state == "CLOSED"
            and info.branch is not None
            and _pr_matches_worktree_head(info, pr_state)
        ):
            return f"{pr_label} CLOSED"

    if info.branch is not None and not safe_only:
        # Age alone is not evidence the work is safe to destroy: this return
        # carries no ancestry or remote-reachability precondition. It must
        # therefore respect PR state exactly like the origin-tip return below
        # -- it deleted an aged build/* worktree both under an UNKNOWN PR
        # response and, before that, under a plainly KNOWN OPEN PR.
        if (
            info.branch.startswith("build/")
            and not pr_unknown
            and (pr_state is None or pr_state.state != "OPEN")
        ):
            age_hours = _worktree_age_hours(info.path, now=now)
            if age_hours is not None and age_hours > build_age_hours:
                return f"build branch age {age_hours:.1f}h > {build_age_hours:g}h"

        # Never treat "matches remote tip" as reaped-while-OPEN: open PR
        # worktrees commonly match origin/<branch> and must stay mounted.
        if (
            not pr_unknown
            and (pr_state is None or pr_state.state != "OPEN")
            and _origin_matches_head(info.path, info.branch)
        ):
            return f"HEAD matches origin/{info.branch}"

    if merged_pr_only and not include_terminal_dispatches:
        return None

    # Class B: detached-HEAD worktrees under .worktrees/
    is_under_wt = is_under_worktrees(repo_root, info.path)
    clean = _worktree_clean(info.path)
    task_id = _dispatch_task_id(repo_root, info)
    is_dispatch_candidate = task_id is not None

    if (
        not merged_pr_only
        and not include_terminal_dispatches
        and is_under_wt
        and info.detached
        and clean is True
    ):
        has_matching_task = False
        task_settled = False
        if is_dispatch_candidate:
            task_file = repo_root / "batch_state" / "tasks" / f"{task_id}.json"
            if task_file.exists():
                has_matching_task = True
                try:
                    task_data = json.loads(task_file.read_text(encoding="utf-8"))
                    task_status = task_data.get("status")
                    if task_status in ("done", "failed", "no_deliverable") and (
                        active_ids is None or task_id not in active_ids
                    ):
                        task_settled = True
                except Exception:
                    pass

        ancestor = _is_ancestor_of_origin_main(info.path)
        if has_matching_task and task_settled:
            if not _is_head_reachable_from_remote(info.path, info.head):
                pass
            elif ancestor:
                return f"detached HEAD ancestor of origin/main; settled dispatch task-id={task_id}"
            else:
                return f"detached HEAD settled dispatch task-id={task_id}"

        if ancestor:
            age_hours = _worktree_age_hours(info.path, now=now)
            if age_hours is not None and age_hours > 24.0:
                return f"detached HEAD ancestor of origin/main; age {age_hours:.1f}h > 24h"

    # Optional Class A: settled dispatch worktree.  This class is intentionally
    # narrower than the legacy classes: an explicit terminal task record, no
    # live PID, a known-empty active-task probe, and no open PR are all required.
    if (
        is_dispatch_candidate
        and clean is True
        and (include_terminal_dispatches or not merged_pr_only)
    ):
        terminal_reason = _terminal_dispatch_reason(
            repo_root=repo_root,
            info=info,
            active_ids=active_ids,
        )
        if (
            terminal_reason is not None
            and not pr_unknown
            and (pr_state is None or pr_state.state != "OPEN")
        ):
            return terminal_reason

        # Also PR-dependent: it reads pr_state to decide abandonment.
        if not pr_unknown:
            abandoned = _abandoned_main_dispatch_reason(
                repo_root=repo_root,
                info=info,
                pr_state=pr_state,
                now=now,
            )
            if abandoned is not None:
                return abandoned

    return None


def _abandoned_main_dispatch_reason(
    *,
    repo_root: Path,
    info: WorktreeInfo,
    pr_state: PullRequestState | None,
    now: float | None,
) -> str | None:
    """Reap a dispatch checkout left sitting on origin/main after closeout.

    A brand-new worktree is also created from main, so this class requires the
    origin branch to be gone, no open PR, a clean tree, and age above the
    build-branch threshold. Live CWDs and active tasks are rejected earlier.
    """
    if info.branch is None or (pr_state is not None and pr_state.state == "OPEN"):
        return None
    if not _is_ancestor_of_origin_main(info.path):
        return None
    if _origin_branch_present(info.path, info.branch):
        return None
    age_hours = _worktree_age_hours(info.path, now=now)
    if age_hours is None or age_hours <= DEFAULT_BUILD_AGE_HOURS:
        return None
    task_data = _task_record(repo_root, _dispatch_task_id(repo_root, info))
    if task_data is not None:
        status = task_data.get("status")
        if status not in _TERMINAL_DISPATCH_STATUSES or _task_pid_alive(task_data):
            return None
    return (
        "dispatch HEAD ancestor of origin/main; origin branch gone; "
        f"age {age_hours:.1f}h > {DEFAULT_BUILD_AGE_HOURS:g}h"
    )


def find_needs_finalize_worktrees(repo_root: Path) -> list[dict[str, Any]]:
    """Return all worktrees that have a task record with status 'needs_finalize'."""
    results: list[dict[str, Any]] = []
    try:
        worktrees = list_git_worktrees(repo_root)
    except Exception:
        return []
    for info in worktrees:
        task_id = _dispatch_task_id(repo_root, info)
        if task_id:
            status = _task_record_status(repo_root, task_id)
            if status == "needs_finalize":
                results.append(
                    {
                        "path": str(info.path),
                        "task_id": task_id,
                        "branch": info.branch,
                    }
                )
    return results


def adopt_dispatch_worktrees(repo_root: Path) -> list[dict[str, Any]]:
    """Journal already-mounted dispatch worktrees without inferring ownership.

    Adoption is observation only.  A later enforce pass must still independently
    prove an exact merged PR head and every P0 guard before it removes anything.
    """
    adopted: list[dict[str, Any]] = []
    for info in list_git_worktrees(repo_root):
        task_id = _dispatch_task_id(repo_root, info)
        if task_id is None or not is_under_worktrees(repo_root, info.path):
            continue
        row = {
            "path": str(info.path),
            "branch": info.branch,
            "head": info.head,
            "task_id": task_id,
        }
        reaper_lifecycle.append_journal(repo_root, "adopt", **row)
        adopted.append(row)
    return adopted


def _preserve_dirty_worktree(info: WorktreeInfo) -> str | None:
    branch = info.branch or "detached"
    add_proc = _run(["git", "add", "-A"], cwd=info.path)
    if add_proc.returncode != 0:
        return f"git add failed: {_format_failure(add_proc)}"
    commit_proc = _run(
        [
            "git",
            "commit",
            "--no-verify",
            "-m",
            f"wip: preserve {branch} before reap [skip ci]",
        ],
        cwd=info.path,
    )
    if commit_proc.returncode != 0:
        return f"git commit failed: {_format_failure(commit_proc)}"
    return None


def _remove_worktree(repo_root: Path, info: WorktreeInfo) -> str | None:
    """Remove a worktree only after the caller has completed every P0 guard.

    ``_worktree_clean`` deliberately accepts disposable ignored residue such as
    a worker's ``.venv``. Git still considers that residue when removing a
    worktree, so force is required at this final, guarded deletion boundary.
    """
    try:
        target = assert_delete_target(info.path, repo_root=repo_root)
    except ValueError as exc:
        return f"delete guard refused worktree target: {exc}"
    try:
        proc = _run(
            ["git", "worktree", "remove", "--force", str(target)],
            cwd=repo_root,
        )
    except PermissionError as exc:
        return f"permission denied removing worktree: {exc}"
    except OSError as exc:
        return f"OS error removing worktree: {exc}"
    if proc.returncode != 0:
        failure_msg = _format_failure(proc)
        if "permission" in failure_msg.lower() or "denied" in failure_msg.lower():
            return f"permission denied removing worktree: {failure_msg}"
        return failure_msg
    return None


def _prune_branch(
    repo_root: Path,
    branch: str | None,
    force: bool = False,
    expected_head: str | None = None,
) -> str | None:
    if not branch:
        return None
    if expected_head is None:
        flag = "-D" if force else "-d"
        proc = _run(["git", "branch", flag, "--", branch], cwd=repo_root)
        return None if proc.returncode == 0 else _format_failure(proc)

    current = _run(
        ["git", "rev-parse", "--verify", f"refs/heads/{branch}"],
        cwd=repo_root,
    )
    if (
        current.returncode != 0
        or (current.stdout or "").strip() != expected_head
    ):
        return "branch HEAD changed during cleanup"

    flag = "-D" if force else "-d"
    deleted = _run(["git", "branch", flag, "--", branch], cwd=repo_root)
    return None if deleted.returncode == 0 else _format_failure(deleted)


def _reap_qualified_worktree(
    *,
    repo_root: Path,
    info: WorktreeInfo,
    reason: str,
    dirty: bool | None,
    pr_state: PullRequestState | None,
    apply: bool,
    preserve_then_reap: bool,
    prune_merged_branches: bool,
    require_terminal_dispatch_guards: bool,
    eligible_backlog: int | None = None,
) -> ReapResult:
    expected_head = info.head
    if dirty is None:
        return ReapResult(
            path=str(info.path),
            branch=info.branch,
            action="skipped",
            reason="unable to determine worktree status",
            dirty=None,
            pr=_pr_dict(pr_state),
        )
    if dirty and not preserve_then_reap:
        return ReapResult(
            path=str(info.path),
            branch=info.branch,
            action="skipped",
            reason=f"dirty; qualifies for reap because {reason}",
            dirty=True,
            pr=_pr_dict(pr_state),
        )
    if not apply:
        action = "would_preserve_then_remove" if dirty else "would_remove"
        return ReapResult(
            path=str(info.path),
            branch=info.branch,
            action=action,
            reason=reason,
            dirty=dirty,
            pr=_pr_dict(pr_state),
        )

    if os.environ.get("LU_REAPER_DISABLED") == "1":
        return ReapResult(
            path=str(info.path),
            branch=info.branch,
            action="skipped",
            reason="reaper disabled by LU_REAPER_DISABLED=1",
            dirty=dirty,
            pr=_pr_dict(pr_state),
        )

    cap_allowed, cap_reason = reaper_lifecycle.cap_allows_reap(
        repo_root,
        eligible_backlog=eligible_backlog,
    )
    if not cap_allowed:
        return ReapResult(
            path=str(info.path),
            branch=info.branch,
            action="skipped",
            reason=cap_reason or "first-class daily reap cap reached",
            dirty=dirty,
            pr=_pr_dict(pr_state),
        )

    pending_marked = False
    recovery_ref: str | None = None
    try:
        # This reservation is intentionally before the final TOCTOU checks.
        # Scheduler/delegate consumers can reject a new bind while it exists.
        reaper_lifecycle.mark_reap_pending(
            repo_root,
            worktree_path=info.path,
            branch=info.branch,
            head=expected_head,
            task_id=_dispatch_task_id(repo_root, info),
        )
        pending_marked = True

        if dirty:
            preserve_error = _preserve_dirty_worktree(info)
            if preserve_error is not None:
                return ReapResult(
                    path=str(info.path),
                    branch=info.branch,
                    action="error",
                    reason=f"preserve before reap failed: {reason}",
                    dirty=True,
                    pr=_pr_dict(pr_state),
                    error=preserve_error,
                )
            refreshed_head = _run(["git", "rev-parse", "HEAD"], cwd=info.path)
            if refreshed_head.returncode != 0:
                return ReapResult(
                    path=str(info.path),
                    branch=info.branch,
                    action="error",
                    reason=f"cannot verify preserved worktree HEAD: {reason}",
                    dirty=True,
                    pr=_pr_dict(pr_state),
                    error=_format_failure(refreshed_head),
                )
            expected_head = (refreshed_head.stdout or "").strip()

        current_head_proc = _run(["git", "rev-parse", "HEAD"], cwd=info.path)
        current_head = (current_head_proc.stdout or "").strip()
        if current_head_proc.returncode != 0 or not expected_head or current_head != expected_head:
            return ReapResult(
                path=str(info.path),
                branch=info.branch,
                action="skipped",
                reason=f"HEAD changed during cleanup; originally qualified because {reason}",
                dirty=dirty,
                pr=_pr_dict(pr_state),
            )

        if reason.startswith(_ACP_RUNTIME_REASON_PREFIX):
            # A no-checkout tree is never "clean" for the generic status
            # probe; its safety proof is the dead owner plus the only-.git
            # pointer, both re-verified here, plus an explicit unlock so the
            # final removal needs no double --force past the lock.
            recheck = _acp_runtime_cleanup_recheck(repo_root, info)
            if recheck is not None:
                return ReapResult(
                    path=str(info.path),
                    branch=info.branch,
                    action="skipped",
                    reason=recheck,
                    dirty=dirty,
                    pr=_pr_dict(pr_state),
                )
            unlock = _run(["git", "worktree", "unlock", str(info.path)], cwd=repo_root)
            if unlock.returncode != 0:
                return ReapResult(
                    path=str(info.path),
                    branch=info.branch,
                    action="error",
                    reason=reason,
                    dirty=dirty,
                    pr=_pr_dict(pr_state),
                    error=f"worktree unlock failed: {_format_failure(unlock)}",
                )
        else:
            current_clean = _worktree_clean(info.path)
            if current_clean is not True:
                return ReapResult(
                    path=str(info.path),
                    branch=info.branch,
                    action="skipped",
                    reason=f"worktree changed during cleanup; originally qualified because {reason}",
                    dirty=None if current_clean is None else True,
                    pr=_pr_dict(pr_state),
                )

        if require_terminal_dispatch_guards:
            current_active_ids = _active_task_ids()
            current_live_cwds = _live_cwd_paths(repo_root)
            if current_active_ids is None or current_live_cwds is None:
                return ReapResult(
                    path=str(info.path),
                    branch=info.branch,
                    action="skipped",
                    reason="terminal dispatch guards unavailable during cleanup",
                    dirty=dirty,
                    pr=_pr_dict(pr_state),
                )
            terminal_reason = _terminal_dispatch_reason(
                repo_root=repo_root,
                info=info,
                active_ids=current_active_ids,
            )
            activity = _activity_reason(
                repo_root=repo_root,
                info=info,
                active_ids=current_active_ids,
                live_cwds=current_live_cwds,
                check_pending=False,
            )
            if not _is_head_reachable_from_remote(info.path, current_head):
                return ReapResult(
                    path=str(info.path),
                    branch=info.branch,
                    action="skipped",
                    reason="unpushed_head",
                    dirty=dirty,
                    pr=_pr_dict(pr_state),
                )
            if terminal_reason is None or activity is not None:
                return ReapResult(
                    path=str(info.path),
                    branch=info.branch,
                    action="skipped",
                    reason=activity or "terminal dispatch state changed during cleanup",
                    dirty=dirty,
                    pr=_pr_dict(pr_state),
                )
            if info.branch is not None:
                current_prs, current_pr_error = _query_pr_states(repo_root, info.branch)
                if current_pr_error is not None:
                    return ReapResult(
                        path=str(info.path),
                        branch=info.branch,
                        action="skipped",
                        reason=f"PR guard unavailable during cleanup; {current_pr_error}",
                        dirty=dirty,
                        pr=_pr_dict(pr_state),
                    )
                if any(pr.state == "OPEN" for pr in current_prs):
                    return ReapResult(
                        path=str(info.path),
                        branch=info.branch,
                        action="skipped",
                        reason="open PR appeared during cleanup",
                        dirty=dirty,
                        pr=_pr_dict(pr_state),
                    )

        if reason.startswith("dispatch HEAD ancestor of origin/main"):
            current_active_ids = _active_task_ids()
            current_live_cwds = _live_cwd_paths(repo_root)
            if current_active_ids is None or current_live_cwds is None:
                return ReapResult(
                    path=str(info.path),
                    branch=info.branch,
                    action="skipped",
                    reason="abandoned-main activity probe unavailable during cleanup",
                    dirty=dirty,
                    pr=_pr_dict(pr_state),
                )
            activity = _activity_reason(
                repo_root=repo_root,
                info=info,
                active_ids=current_active_ids,
                live_cwds=current_live_cwds,
                check_pending=False,
            )
            if activity is not None:
                return ReapResult(
                    path=str(info.path),
                    branch=info.branch,
                    action="skipped",
                    reason=activity,
                    dirty=dirty,
                    pr=_pr_dict(pr_state),
                )
            if _origin_branch_present(info.path, info.branch):
                return ReapResult(
                    path=str(info.path),
                    branch=info.branch,
                    action="skipped",
                    reason="origin branch returned during cleanup",
                    dirty=dirty,
                    pr=_pr_dict(pr_state),
                )
            live_origin = _live_origin_heads_present(info.path, info.branch)
            if live_origin is None:
                return ReapResult(
                    path=str(info.path),
                    branch=info.branch,
                    action="skipped",
                    reason="live origin probe unavailable during cleanup",
                    dirty=dirty,
                    pr=_pr_dict(pr_state),
                )
            if live_origin:
                return ReapResult(
                    path=str(info.path),
                    branch=info.branch,
                    action="skipped",
                    reason="origin branch returned during cleanup",
                    dirty=dirty,
                    pr=_pr_dict(pr_state),
                )
            if not _is_ancestor_of_origin_main(info.path):
                return ReapResult(
                    path=str(info.path),
                    branch=info.branch,
                    action="skipped",
                    reason="HEAD left origin/main during cleanup",
                    dirty=dirty,
                    pr=_pr_dict(pr_state),
                )
            if info.branch is not None:
                current_prs, current_pr_error = _query_pr_states(repo_root, info.branch)
                if current_pr_error is not None:
                    return ReapResult(
                        path=str(info.path),
                        branch=info.branch,
                        action="skipped",
                        reason=f"PR guard unavailable during cleanup; {current_pr_error}",
                        dirty=dirty,
                        pr=_pr_dict(pr_state),
                    )
                if any(pr.state == "OPEN" for pr in current_prs):
                    return ReapResult(
                        path=str(info.path),
                        branch=info.branch,
                        action="skipped",
                        reason="open PR appeared during cleanup",
                        dirty=dirty,
                        pr=_pr_dict(pr_state),
                    )

        recovery_ref, recovery_error = reaper_lifecycle.create_recovery_ref(
            repo_root,
            branch=info.branch,
            head=current_head,
        )
        if recovery_error is not None:
            return ReapResult(
                path=str(info.path),
                branch=info.branch,
                action="error",
                reason=f"could not create recovery material; {reason}",
                dirty=dirty,
                pr=_pr_dict(pr_state),
                error=recovery_error,
            )

        # Decide branch deletion while the worktree directory still exists.
        # ``git merge-base`` cannot run with a cwd that ``worktree remove``
        # has already deleted, and a same-tree sibling is not proof.
        prune_contained = False
        if (
            prune_merged_branches
            and info.branch is not None
            and pr_state is not None
            and pr_state.state == "MERGED"
        ):
            prune_contained = _pr_matches_worktree_head(
                info, pr_state
            ) or _tip_is_ancestor_of_origin_main(info)

        remove_error = _remove_worktree(repo_root, info)
        if remove_error is not None:
            return ReapResult(
                path=str(info.path),
                branch=info.branch,
                action="error",
                reason=reason,
                dirty=dirty,
                pr=_pr_dict(pr_state),
                error=remove_error,
                recovery_ref=recovery_ref,
            )

        branch_prune_error = None
        branch_pruned = False
        if prune_contained:
            branch_prune_error = _prune_branch(
                repo_root,
                info.branch,
                force=True,
                expected_head=current_head,
            )
            branch_pruned = branch_prune_error is None

        if branch_prune_error is not None:
            return ReapResult(
                path=str(info.path),
                branch=info.branch,
                action="removed",
                reason=f"{reason}; branch prune failed",
                dirty=dirty,
                pr=_pr_dict(pr_state),
                error=branch_prune_error,
                recovery_ref=recovery_ref,
            )

        reaper_lifecycle.record_reap_for_cap(repo_root)
        return ReapResult(
            path=str(info.path),
            branch=info.branch,
            action="preserved_then_removed" if dirty else "removed",
            reason=reason,
            dirty=dirty,
            pr=_pr_dict(pr_state),
            branch_pruned=branch_pruned,
            recovery_ref=recovery_ref,
        )
    finally:
        if pending_marked:
            reaper_lifecycle.clear_reap_pending(repo_root, info.path)

def _target_filter(target_paths: list[Path] | None) -> set[Path] | None:
    if target_paths is None:
        return None
    return {path.resolve() for path in target_paths}


def reap_worktrees(
    *,
    repo_root: Path,
    apply: bool = False,
    build_age_hours: float = DEFAULT_BUILD_AGE_HOURS,
    preserve_then_reap: bool = False,
    prune_merged_branches: bool = False,
    target_paths: list[Path] | None = None,
    now: float | None = None,
    safe_only: bool = False,
    live_cwds: set[Path] | None = None,
    merged_pr_only: bool = True,
    require_activity_probe: bool | None = None,
    include_terminal_dispatches: bool = False,
) -> list[ReapResult]:
    """Evaluate and optionally reap eligible worktrees.

    Apply mode requires a process-CWD activity probe unless a caller
    deliberately overrides that policy.
    """
    repo_root = repo_root.resolve()
    targets = _target_filter(target_paths)
    results: list[ReapResult] = []
    qualified: list[tuple[WorktreeInfo, str, bool | None, PullRequestState | None]] = []
    active_ids = _active_task_ids()
    if require_activity_probe is None:
        require_activity_probe = bool(apply)
    killed_sandboxes = stop_orphaned_sandboxes(repo_root) if apply else []
    if live_cwds is None or killed_sandboxes:
        live_cwds = _live_cwd_paths(repo_root)
    if require_activity_probe and live_cwds is None:
        raise RuntimeError("process-CWD activity probe unavailable; cleanup skipped")

    with _ReapLock(repo_root):
        worktree_listing = list_git_worktrees(repo_root)
        for info in worktree_listing:
            if targets is not None and info.path.resolve() not in targets:
                continue
            if (
                info.path.resolve() == repo_root.resolve()
                or info.path.resolve() == primary_checkout_root(repo_root).resolve()
            ):
                results.append(
                    ReapResult(
                        path=str(info.path),
                        branch=info.branch,
                        action="skipped",
                        reason="primary checkout",
                        dirty=None,
                        owner=_dispatch_owner(repo_root, info),
                    )
                )
                continue

            if not is_under_worktrees(repo_root, info.path):
                results.append(
                    ReapResult(
                        path=str(info.path),
                        branch=info.branch,
                        action="skipped",
                        reason="outside repo .worktrees/",
                        dirty=None,
                        owner=_dispatch_owner(repo_root, info),
                    )
                )
                continue

            if not info.path.is_dir():
                results.append(
                    ReapResult(
                        path=str(info.path),
                        branch=info.branch,
                        action="skipped",
                        reason=(
                            "registered worktree path is missing; "
                            "run git worktree prune"
                        ),
                        dirty=None,
                        owner=_dispatch_owner(repo_root, info),
                    )
                )
                continue

            activity = _activity_reason(
                repo_root=repo_root,
                info=info,
                active_ids=active_ids,
                live_cwds=live_cwds,
            )
            if activity is not None:
                results.append(
                    ReapResult(
                        path=str(info.path),
                        branch=info.branch,
                        action="skipped",
                        reason=activity,
                        dirty=None,
                        owner=_dispatch_owner(repo_root, info),
                    )
                )
                continue

            # New provably-safe class (#8344): abandoned ACP runtime
            # worktrees. Handled before the PR queries because the class
            # never consults PR state and a no-checkout tree is never
            # "clean" under the generic status probe.
            acp_reason = _acp_dead_owner_reason(
                repo_root=repo_root,
                info=info,
                now=now,
                live_cwds=live_cwds,
            )
            if acp_reason is not None:
                if not holds_only_git_pointer(info.path):
                    results.append(
                        ReapResult(
                            path=str(info.path),
                            branch=info.branch,
                            action="skipped",
                            reason=(
                                "acp runtime worktree holds unexpected files; "
                                f"{acp_reason}"
                            ),
                            dirty=None,
                            owner=_dispatch_owner(repo_root, info),
                        )
                    )
                    continue
                reaper_lifecycle.append_journal(
                    repo_root,
                    "plan" if apply else "observe",
                    path=str(info.path),
                    branch=info.branch,
                    head=info.head,
                    reason=acp_reason,
                    pr=None,
                )
                qualified.append((info, acp_reason, False, None))
                continue

            dirty_state = _worktree_clean(info.path)
            dirty = None if dirty_state is None else not dirty_state

            candidates = _candidate_branches_for_worktree(repo_root, info)
            pr_state = None
            pr_error = None
            all_pr_states: list[PullRequestState] = []
            errors: list[str] = []
            if candidates:
                for cand_branch in candidates:
                    st, err = _query_pr_states(repo_root, cand_branch)
                    if err:
                        errors.append(err)
                    all_pr_states.extend(st)

            review_number = _worktree_review_pr_number(repo_root, info)
            review_err = None
            if review_number is not None:
                review_states, review_err = _query_pr_by_number(repo_root, review_number)
                # A GraphQL "not a PullRequest" answer means the parsed token
                # is an issue number: absence, not an unreadable guard.
                if review_err and not _is_not_a_pull_request_error(review_err):
                    errors.append(review_err)
                all_pr_states.extend(review_states)

            # Follow-up CI branches carry a different branch name than the PR
            # head they fix.  Find the MERGED PR that introduced the worktree
            # HEAD by SHA, but only when that commit is not already on
            # origin/main — otherwise a fresh branch sitting on a merged main
            # tip would be mistaken for a squash-merged follow-up commit.
            if info.head and not _is_ancestor_of_origin_main(info.path):
                all_pr_states.extend(_query_prs_by_head_sha(repo_root, info.head))

            # Any candidate-query error blocks qualification. A supplementary
            # SHA lookup finding *some* PR cannot redeem an unreadable
            # authoritative branch response -- that made UNKNOWN -> retain
            # non-universal on the destructive path.
            pr_state = _best_pr(all_pr_states)
            if errors:
                pr_error = "; ".join(errors)

            if (merged_pr_only or include_terminal_dispatches) and pr_error is not None:
                results.append(
                    ReapResult(
                        path=str(info.path),
                        branch=info.branch,
                        action="skipped",
                        reason=f"PR guard unavailable; {pr_error}",
                        dirty=dirty,
                        pr=_pr_dict(pr_state),
                        owner=_dispatch_owner(repo_root, info),
                    )
                )
                continue

            # An unreadable branch response is UNKNOWN, not "no PR": drop the
            # untrusted pr_state and forbid every PR-dependent reason. Without
            # this, the legacy/manual class deleted on a failed branch query,
            # because a supplementary SHA-search MERGED hit is labelled with
            # the queried worktree SHA, always matches the head, and its
            # "PR #N MERGED" reason does not enable the cleanup-time re-query.
            pr_unknown = pr_error is not None
            reason = _qualifying_reason(
                repo_root=repo_root,
                info=info,
                pr_state=None if pr_unknown else pr_state,
                build_age_hours=build_age_hours,
                now=now,
                active_ids=active_ids,
                safe_only=safe_only,
                merged_pr_only=merged_pr_only,
                include_terminal_dispatches=include_terminal_dispatches,
                pr_unknown=pr_unknown,
            )
            if reason is None:
                if pr_state is not None and pr_state.state == "OPEN":
                    pr_label = f"PR #{pr_state.number}" if pr_state.number is not None else "PR"
                    reason = f"open {pr_label}"
                else:
                    is_settled, _ = _is_settled_dispatch_task(
                        repo_root=repo_root,
                        info=info,
                        active_ids=active_ids,
                    )
                    if (
                        is_settled
                        and is_under_worktrees(repo_root, info.path)
                        and (include_terminal_dispatches or not merged_pr_only)
                        and not _is_head_reachable_from_remote(info.path, info.head)
                    ):
                        reason = "unpushed_head"
                    elif info.detached or info.branch is None:
                        reason = "detached HEAD unknown"
                    else:
                        reason = (
                            f"no reap condition matched; {pr_error}"
                            if pr_error
                            else "no reap condition matched"
                        )
                if not pr_unknown and reason.startswith("no reap condition matched"):
                    hint = _same_tree_hint(info, pr_state)
                    if hint:
                        reason = f"{reason}; {hint}"
                results.append(
                    ReapResult(
                        path=str(info.path),
                        branch=info.branch,
                        action="skipped",
                        reason=reason,
                        dirty=dirty,
                        pr=_pr_dict(pr_state),
                        owner=_dispatch_owner(repo_root, info),
                    )
                )
                continue

            reaper_lifecycle.append_journal(
                repo_root,
                "plan" if apply else "observe",
                path=str(info.path),
                branch=info.branch,
                head=info.head,
                reason=reason,
                pr=_pr_dict(pr_state),
            )
            qualified.append((info, reason, dirty, pr_state))

        # The dynamic daily cap may expand only against a known eligible
        # backlog: worktrees that passed every listing-time safety proof in
        # this run.  Count conservatively — only clean candidates (a dirty
        # one fails the "clean" proof until preserve-then-reap re-verifies
        # it); any doubt means no expansion.
        eligible_backlog = (
            sum(1 for _, _, dirty, _ in qualified if dirty is False) if apply else None
        )
        for info, reason, dirty, pr_state in qualified:
            res = _reap_qualified_worktree(
                repo_root=repo_root,
                info=info,
                reason=reason,
                dirty=dirty,
                pr_state=pr_state,
                apply=apply,
                preserve_then_reap=preserve_then_reap,
                prune_merged_branches=prune_merged_branches,
                require_terminal_dispatch_guards=(
                    include_terminal_dispatches
                    and reason.startswith("settled dispatch task-id=")
                ),
                eligible_backlog=eligible_backlog,
            )
            if res.owner is None:
                res = replace(res, owner=_dispatch_owner(repo_root, info))
            results.append(res)

        # Zero-file unregistered placeholder directories are invisible to
        # ``git worktree list``; sweep them after the registered worktrees.
        results.extend(
            _reap_dispatch_husks(
                repo_root,
                registered={info.path.resolve() for info in worktree_listing},
                apply=apply,
                live_cwds=live_cwds,
                targets=targets,
                now=now,
            )
        )

    if targets is not None:
        seen = {Path(result.path).resolve() for result in results}
        for target in sorted(targets - seen):
            results.append(
                ReapResult(
                    path=str(target),
                    branch=None,
                    action="skipped",
                    reason="target path is not a registered git worktree",
                    dirty=None,
                    owner="unattributed",
                )
            )

    for result in results:
        event = "reap" if result.action in {"removed", "preserved_then_removed"} else "skip"
        reaper_lifecycle.append_journal(
            repo_root,
            event,
            path=result.path,
            branch=result.branch,
            action=result.action,
            reason=result.reason,
            dirty=result.dirty,
            pr=result.pr,
            error=result.error,
            recovery_ref=result.recovery_ref,
        )
    return results


def reap_success_worktree(
    *,
    repo_root: Path,
    worktree_path: Path,
    reason: str,
    apply: bool = True,
    preserve_then_reap: bool = False,
) -> ReapResult:
    """Remove one clean success worktree while keeping its branch."""
    repo_root = repo_root.resolve()
    target = worktree_path.resolve()
    matching = [
        info
        for info in list_git_worktrees(repo_root)
        if info.path.resolve() == target
    ]
    if not matching:
        return ReapResult(
            path=str(target),
            branch=None,
            action="skipped",
            reason="target path is not a registered git worktree",
            dirty=None,
            owner="unattributed",
        )

    info = matching[0]
    owner = _dispatch_owner(repo_root, info)
    if not is_under_worktrees(repo_root, info.path):
        return ReapResult(
            path=str(info.path),
            branch=info.branch,
            action="skipped",
            reason="outside repo .worktrees/",
            dirty=None,
            owner=owner,
        )
    clean = _worktree_clean(info.path)
    dirty = None if clean is None else not clean
    if reason.startswith("settled dispatch") and not _is_head_reachable_from_remote(info.path, info.head):
        return ReapResult(
            path=str(info.path),
            branch=info.branch,
            action="skipped",
            reason="unpushed_head",
            dirty=dirty,
            owner=owner,
        )
    res = _reap_qualified_worktree(
        repo_root=repo_root,
        info=info,
        reason=reason,
        dirty=dirty,
        pr_state=None,
        apply=apply,
        preserve_then_reap=preserve_then_reap,
        prune_merged_branches=False,
        require_terminal_dispatch_guards=False,
    )
    if res.owner is None:
        res = replace(res, owner=owner)
    return res


def _result_payload(result: ReapResult) -> dict[str, Any]:
    return asdict(result)


def _format_result_line(result: ReapResult) -> str:
    branch = result.branch or "-"
    base = f"{result.action.upper()} {result.path} branch={branch} reason={result.reason}"
    if result.error:
        base = f"{base} error={result.error}"
    return base


def format_text_results(results: list[ReapResult], *, apply: bool) -> str:
    remove_actions = {
        "would_remove",
        "would_preserve_then_remove",
        "removed",
        "preserved_then_removed",
    }
    candidates = sum(1 for result in results if result.action in remove_actions)
    skipped = sum(1 for result in results if result.action == "skipped")
    errors = sum(1 for result in results if result.action == "error")
    mode = "APPLY" if apply else "DRY RUN"
    lines = [f"{mode}: {candidates} candidate(s), {skipped} skipped, {errors} error(s)"]
    lines.extend(_format_result_line(result) for result in results)
    return "\n".join(lines)


def aggregate_counts(results: list[ReapResult]) -> dict[str, Any]:
    preservation_classes = {
        "primary": 0,
        "active_dispatch": 0,
        "open_pr": 0,
        "dirty": 0,
        "detached_unknown": 0,
        "permission_error": 0,
        "foreign": 0,
        "unmerged": 0,
    }
    by_owner: dict[str, int] = {}
    reaped = 0
    reaped_by_owner: dict[str, int] = {}
    retained_exceptions = 0

    for r in results:
        owner = r.owner or "unattributed"
        by_owner[owner] = by_owner.get(owner, 0) + 1
        cls = classify_preservation(r)
        if cls == "eligible":
            reaped += 1
            reaped_by_owner[owner] = reaped_by_owner.get(owner, 0) + 1
        else:
            if cls in preservation_classes:
                preservation_classes[cls] += 1
            else:
                preservation_classes[cls] = preservation_classes.get(cls, 0) + 1
            if cls in {"dirty", "permission_error"}:
                retained_exceptions += 1

    return {
        "total": len(results),
        "reaped": reaped,
        "retained": len(results) - reaped,
        "retained_exceptions": retained_exceptions,
        "by_preservation_class": preservation_classes,
        "by_owner": dict(sorted(by_owner.items())),
        "reaped_by_owner": dict(sorted(reaped_by_owner.items())),
    }


def format_aggregate_results(counts: dict[str, Any], *, apply: bool) -> str:
    mode = "APPLY" if apply else "DRY RUN"
    lines = [
        f"{mode} AGGREGATE SUMMARY: {counts['total']} worktree(s) inspected",
        f"  Reaped: {counts['reaped']}",
        f"  Retained: {counts['retained']} (exceptions: {counts['retained_exceptions']})",
        "  By preservation class:",
    ]
    for cls, count in sorted(counts.get("by_preservation_class", {}).items()):
        if count > 0:
            lines.append(f"    {cls}: {count}")
    lines.append("  By owner:")
    for owner, count in sorted(counts.get("by_owner", {}).items()):
        lines.append(f"    {owner}: {count}")
    return "\n".join(lines)


def build_aggregate_summary(
    results_by_repo: dict[str, list[ReapResult]],
    *,
    apply: bool,
) -> dict[str, Any]:
    all_results = [res for res_list in results_by_repo.values() for res in res_list]
    summary = aggregate_counts(all_results)
    repos_summary: dict[str, Any] = {}
    for repo_name, res_list in results_by_repo.items():
        repos_summary[repo_name] = aggregate_counts(res_list)
    return {
        "mode": "apply" if apply else "dry_run",
        "summary": summary,
        "repositories": repos_summary,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Safely reap completed git worktrees under .worktrees/.\n"
            "Use for completed-work cleanup; active or unverifiable worktrees are preserved."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.orchestration.reap_worktrees --dry-run\n"
            "  .venv/bin/python -m scripts.orchestration.reap_worktrees --apply --merged\n"
            "Outputs: removal results; apply writes local journals and recovery refs.\n"
            "Exit codes: 0 on success; nonzero on errors.\n"
            "Related: docs/runbooks/worktree-cleanup.md; issue #7724."
        ),
    )
    parser.add_argument(
        "--repo-root",
        action="append",
        type=Path,
        default=None,
        help="Repository root to inspect. Repeatable.",
    )
    parser.add_argument(
        "--both-repos",
        action="store_true",
        help="Inspect both public and private repository roots.",
    )
    parser.add_argument(
        "--aggregate",
        action="store_true",
        help="Emit aggregate summary of counts and owners without path dumps.",
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=("report", "plan", "apply", "journal", "restore"),
        help="Optional verb: report/plan are dry-run, apply enforces, journal prints evidence.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Print candidates without changing the filesystem (default).",
    )
    mode.add_argument(
        "--apply",
        action="store_true",
        help="Remove eligible worktrees.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON.",
    )
    parser.add_argument(
        "--build-age-hours",
        type=float,
        default=DEFAULT_BUILD_AGE_HOURS,
        help=f"Reap clean build/* worktrees older than this many hours (default: {DEFAULT_BUILD_AGE_HOURS:g}).",
    )
    parser.add_argument(
        "--preserve-then-reap",
        action="store_true",
        help="Commit dirty eligible worktrees locally with --no-verify before removing them.",
    )
    parser.add_argument(
        "--prune-merged-branches",
        action="store_true",
        help=(
            "Delete a local branch only after its MERGED PR head SHA exactly "
            "matches the removed worktree HEAD."
        ),
    )
    parser.add_argument(
        "--safe-only",
        action="store_true",
        help="Restrict reaping to provably-safe classes (merged PRs + settled dispatches + detached-HEAD ancestors).",
    )
    parser.add_argument(
        "--merged",
        action="store_true",
        help=(
            "Restrict cleanup to MERGED PRs with matching heads or gone origin branches; enable branch "
            "pruning. Dirty trees remain untouched unless "
            "--preserve-then-reap is explicit."
        ),
    )
    parser.add_argument(
        "--legacy-classes",
        action="store_true",
        help="Enable pre-P0 non-merged cleanup classes for an explicit manual run.",
    )
    parser.add_argument(
        "--terminal-dispatches",
        action="store_true",
        help=(
            "Also reap clean terminal dispatch worktrees only when their task is "
            "inactive, its PID is dead, and GitHub confirms no open PR."
        ),
    )
    parser.add_argument(
        "--worktree",
        action="append",
        type=Path,
        default=None,
        help="Limit evaluation to a registered worktree path. Repeatable.",
    )
    parser.add_argument("--restore-ref", help="Recovery ref to restore from.")
    parser.add_argument("--restore-branch", help="Branch identity expected for --restore-ref.")
    parser.add_argument("--restore-worktree", type=Path, help="New .worktrees/ target for restore.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.both_repos:
        public_root = primary_checkout_root(resolve_repo_root())
        private_root = public_root.parent / "learn-ukrainian-infra-private"
        repo_roots = [public_root, private_root]
    elif args.repo_root:
        repo_roots = [p.resolve() for p in args.repo_root]
    else:
        repo_roots = [primary_checkout_root(resolve_repo_root())]

    is_multi_or_aggregate = bool(args.both_repos or args.aggregate or len(repo_roots) > 1)
    missing = [p for p in repo_roots if not p.is_dir()]
    if missing:
        sanitize = bool(args.aggregate) or bool(is_multi_or_aggregate and args.json)
        for p in missing:
            target = (p.name or str(p)) if sanitize else str(p)
            print(f"reap_worktrees.py: repository not found: {target}", file=sys.stderr)
        return 2

    apply = bool(args.apply) or args.command == "apply"
    merged_mode = bool(args.merged) or (
        not bool(args.legacy_classes) and not bool(args.terminal_dispatches)
    )
    preserve = bool(args.preserve_then_reap)
    prune = bool(args.prune_merged_branches) or bool(args.merged)
    safe_only = bool(args.safe_only) or merged_mode

    if args.command == "journal":
        for repo_root in repo_roots:
            journal = reaper_lifecycle.journal_path(repo_root)
            print(journal.read_text(encoding="utf-8") if journal.exists() else "")
        return 0
    if args.command == "restore":
        if not (args.restore_ref and args.restore_branch and args.restore_worktree):
            parser.error("restore requires --restore-ref, --restore-branch, and --restore-worktree")
        restored, error = reaper_lifecycle.restore_worktree(
            repo_roots[0],
            recovery_ref=args.restore_ref,
            branch=args.restore_branch,
            worktree_path=args.restore_worktree,
        )
        print(json.dumps({"restored": restored, "error": error}, indent=2))
        return 0 if restored else 2

    results_by_repo: dict[str, list[ReapResult]] = {}
    all_results: list[ReapResult] = []
    for repo_root in repo_roots:
        repo_results = reap_worktrees(
            repo_root=repo_root,
            apply=apply,
            build_age_hours=args.build_age_hours,
            preserve_then_reap=preserve,
            prune_merged_branches=prune,
            target_paths=args.worktree,
            safe_only=safe_only,
            merged_pr_only=merged_mode,
            require_activity_probe=apply,
            include_terminal_dispatches=bool(args.terminal_dispatches),
        )
        results_by_repo[repo_root.name] = repo_results
        all_results.extend(repo_results)

    is_multi_or_aggregate = args.both_repos or args.aggregate or len(repo_roots) > 1
    if is_multi_or_aggregate:
        if args.json:
            print(json.dumps(build_aggregate_summary(results_by_repo, apply=apply), indent=2, sort_keys=True))
        else:
            print(format_aggregate_results(aggregate_counts(all_results), apply=apply))
    else:
        if args.json:
            print(json.dumps([_result_payload(result) for result in all_results], indent=2))
        else:
            print(format_text_results(all_results, apply=apply))

    # Always sweep formal CF temp roots (including $TMPDIR/shielded-reviews)
    # when applying — worktree reaps alone left multi-GB lu-review snaps.
    if apply:
        try:
            if str(PROJECT_ROOT) not in sys.path:
                sys.path.insert(0, str(PROJECT_ROOT))
            from scripts.review.isolation import sweep_review_temp_orphans

            sweep = sweep_review_temp_orphans()
            print(
                "review_temp_sweep: "
                f"roots_reaped={sweep.get('roots_reaped', 0)} "
                f"bytes_freed={sweep.get('bytes_freed', 0)} "
                f"errors={sweep.get('errors', 0)}",
                file=sys.stderr,
            )
        except Exception as exc:
            print(f"review_temp_sweep: skipped ({exc})", file=sys.stderr)
    return 1 if any(result.action == "error" for result in all_results) else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"reap_worktrees.py: {exc}", file=sys.stderr)
        raise SystemExit(2) from None
