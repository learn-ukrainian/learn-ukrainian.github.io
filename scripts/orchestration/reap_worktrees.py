#!/usr/bin/env python3
"""Safely reap finished repository worktrees.

The CLI is intentionally safe by default: ``--dry-run`` is the default mode,
only paths under the repository's ``.worktrees/`` directory are eligible, and
dirty worktrees are preserved unless ``--preserve-then-reap`` is explicit.

Finished review checkouts (#9129) are reaped under the same safety checks
(clean tree, HEAD on a remote ref, no live process, no unfinished task): a
detached checkout of a superseded open-PR head, a detached checkout with no
task record and no change for 2 h, and a registered checkout under
``/tmp`` or an agent ``scratchpad`` outside ``.worktrees/``.

``--clean-pushed`` (#10778) is a separate, narrower mode: it removes only
dispatch checkouts that are clean, have every commit on origin, are used by
no process or live task and were idle for 60 minutes (:func:`reap_clean_pushed`).

Suggested backstop:

    .venv/bin/python scripts/orchestration/reap_worktrees.py --apply
"""

from __future__ import annotations

import argparse
import contextlib
import contextvars
import fcntl
import hashlib
import json
import os
import re
import secrets
import shutil
import signal
import stat
import subprocess
import sys
import time
from collections.abc import Callable, Iterator
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.common import github_client, task_store_paths
from scripts.common.acp_runtime_lock import (
    holds_only_git_pointer,
)
from scripts.common.acp_runtime_lock import (
    owner_alive as acp_lock_owner_alive,
)
from scripts.common.acp_runtime_lock import (
    parse_lock_owner as parse_acp_lock_owner,
)
from scripts.common.safe_open import safe_open_below
from scripts.control_plane.storage import StoreId
from scripts.control_plane.storage import connect as cp_connect
from scripts.orchestration import reaper_lifecycle, worker_leftovers, worktree_artifacts, worktree_claims, worktree_prep
from scripts.orchestration.dead_worker_state import worker_liveness
from scripts.orchestration.execution_safe_git import COMMIT_COMMANDS, REMOTE_COMMANDS, GitRefusal
from scripts.orchestration.execution_safe_git import run_git as safe_git
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
    head_from_commit_search: bool = False


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
    preserved_artifacts: dict[str, Any] | None = None
    # Report-only findings (#8663): kind, evidence, and a "verify first:"
    # removal command a human runs; the reaper never acts on them.
    needs_attention: dict[str, Any] | None = None


def sanitized_git_env() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if key not in _GIT_ENV_DENYLIST and not key.startswith("PRE_COMMIT")
    }


# While set, every ``_run`` call without an explicit timeout inherits this
# per-call cap. ``_reap_qualified_worktree`` sets it for the region in which
# it holds delegate's per-worktree lock (#8748).
_LOCKED_GIT_BUDGET_S: contextvars.ContextVar[float | None] = contextvars.ContextVar(
    "reap_worktrees_locked_git_budget_s",
    default=None,
)
# Monotonic deadline (``time.monotonic()`` seconds) for that same region.
# Every call's timeout is also clipped to the time left on this deadline.
_LOCKED_REGION_DEADLINE: contextvars.ContextVar[float | None] = contextvars.ContextVar(
    "reap_worktrees_locked_region_deadline",
    default=None,
)


def _remaining_locked_s() -> float | None:
    """Seconds left on the locked-region deadline, or ``None`` outside it."""
    deadline = _LOCKED_REGION_DEADLINE.get()
    if deadline is None:
        return None
    return max(0.0, deadline - time.monotonic())


def _effective_timeout(timeout: float | None) -> float | None:
    """Per-call cap, clipped to the locked-region deadline when one is active."""
    if timeout is None:
        timeout = _LOCKED_GIT_BUDGET_S.get()
    remaining = _remaining_locked_s()
    if remaining is None:
        return timeout
    if timeout is None:
        return remaining
    return min(timeout, remaining)


def _locked_call_timeout(cap: float) -> float:
    """``cap`` clipped to the time left on the locked-region deadline."""
    remaining = _remaining_locked_s()
    if remaining is None:
        return cap
    return min(cap, remaining)


def _run(
    args: list[str],
    *,
    cwd: Path,
    timeout: float | None = None,
    env_overrides: dict[str, str] | None = None,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    env = sanitized_git_env()
    if env_overrides:
        env.update(env_overrides)
    if args and Path(args[0]).name == "gh":
        # FORCE_COLOR and CLICOLOR_FORCE beat NO_COLOR and make gh wrap piped
        # JSON in ANSI. That is not JSON, and a parse error must stay fail-closed,
        # so every JSON gh call is uncolored instead of being repaired later.
        env.pop("FORCE_COLOR", None)
        env["NO_COLOR"] = "1"
        env["CLICOLOR_FORCE"] = "0"
    timeout = _effective_timeout(timeout)
    if timeout is not None and timeout <= 0:
        raise subprocess.TimeoutExpired(args, 0)
    if args and args[0] == "git":
        command = args[1] if len(args) > 1 else ""
        profile = "remote" if command in REMOTE_COMMANDS else "commit" if command in COMMIT_COMMANDS else "local"
        stdin: dict[str, Any] = {} if input_text is None else {"input": input_text}
        return safe_git(
            args[1:],
            cwd=cwd,
            profile=profile,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
            env=env,
            **stdin,
        )
    return subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
        env=env,
    )


def _run_gh(
    args: list[str],
    *,
    cwd: Path,
    timeout: float | None = None,
) -> subprocess.CompletedProcess[str]:
    """Read GitHub through the shared client.

    Modelled argv translates to REST. Every other shape, including
    ``gh pr list --head`` and ``gh search prs``, falls through to native gh
    on that client's colour-safe transport. Callers still parse stdout:
    an empty body is unknown, and a JSON ``[]`` is no PR.
    """
    timeout = _effective_timeout(timeout)
    if timeout is not None and timeout <= 0:
        raise subprocess.TimeoutExpired(args, 0)
    return github_client.run(
        args,
        cwd=cwd,
        fresh=True,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
        env=sanitized_git_env(),
    )


@contextlib.contextmanager
def _bounded_locked_git() -> Iterator[None]:
    """Bound git while delegate's per-worktree lock is held (#8748).

    Two limits, and only these:

    * A call that passes no timeout is capped at :data:`_LOCKED_GIT_TIMEOUT_S`
      (5s). A call that passes one keeps that cap.
    * The whole region shares one monotonic deadline of
      :func:`_locked_region_budget_s` (``DEFAULT_LOCK_TIMEOUT_S`` minus
      :data:`_LOCKED_REGION_MARGIN_S`). Every call, including one with its
      own cap, receives at most the time left. When none is left the call
      raises :class:`subprocess.TimeoutExpired` and the caller skips — it
      does not delete.

    Network probes (``git ls-remote``, ``gh``, :func:`_merged_origin_gone_proof`)
    run before this context. Under it, those results are re-checked with
    local git only (``rev-parse``, ``merge-base``). The context ends before
    ``git worktree remove``. Removal keeps its own
    :data:`worktree_claims.GIT_WORKTREE_REMOVE_TIMEOUT_S` (120s) and is not
    clipped to the time left here: a fraction of a second is enough to kill
    ``git worktree remove --force`` mid-delete. A dispatch waiting on the
    lock that hits its 30s timeout retries. Branch prune is also outside
    this bound.
    """
    budget_token = _LOCKED_GIT_BUDGET_S.set(_LOCKED_GIT_TIMEOUT_S)
    deadline_token = _LOCKED_REGION_DEADLINE.set(time.monotonic() + _locked_region_budget_s())
    try:
        yield
    finally:
        _LOCKED_REGION_DEADLINE.reset(deadline_token)
        _LOCKED_GIT_BUDGET_S.reset(budget_token)


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

    git_dir = Path(first_line[len(prefix) :].strip())
    if not git_dir.is_absolute():
        git_dir = repo_root / git_dir
    git_dir = git_dir.resolve()
    if git_dir.parent.name != "worktrees":
        return repo_root
    common_git_dir = git_dir.parent.parent
    if common_git_dir.name != ".git":
        return repo_root
    return common_git_dir.parent


def control_plane_root(repo_root: Path) -> Path:
    """Return the checkout holding ``repo_root``'s task records, leases, and locks.

    ``repo_root``'s own primary checkout, except a ``--repo`` sibling
    repository, whose dispatch state lives on the public primary (#8624). The
    read-only probes fall back to the repository's own primary when the fleet
    catalog is unreadable; the removal guard (:func:`_enter_dispatch_worktree_guard`)
    refuses instead.
    """
    primary = primary_checkout_root(repo_root)
    try:
        return worktree_claims.control_plane_root(primary)
    except worktree_claims.ControlPlaneError:
        return primary


def _format_failure(proc: subprocess.CompletedProcess[str]) -> str:
    detail = (proc.stderr or proc.stdout or "").strip()
    if detail:
        return detail.splitlines()[-1]
    return f"exit {proc.returncode}"


def _branch_name(raw: str) -> str:
    for prefix in ("refs/heads/", "refs/remotes/origin/"):
        if raw.startswith(prefix):
            return raw[len(prefix) :]
    return raw


def parse_worktree_porcelain(output: str, *, resolve_paths: bool = True) -> list[WorktreeInfo]:
    """Parse ``git worktree list --porcelain``; ``resolve_paths=False`` keeps registered spellings."""
    entries: list[WorktreeInfo] = []
    current: dict[str, Any] | None = None

    def finish() -> None:
        nonlocal current
        if current and current.get("path"):
            entries.append(
                WorktreeInfo(
                    path=Path(current["path"]).resolve() if resolve_paths else Path(current["path"]),
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


def list_git_worktrees(
    repo_root: Path, *, timeout: float | None = None, resolve_paths: bool = True
) -> list[WorktreeInfo]:
    """List registered worktrees; an expired ``timeout`` raises :class:`RuntimeError`."""
    try:
        proc = _run(["git", "worktree", "list", "--porcelain"], cwd=repo_root, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"git worktree list timed out after {exc.timeout:g}s") from exc
    if proc.returncode != 0:
        raise RuntimeError(f"git worktree list failed: {_format_failure(proc)}")
    return parse_worktree_porcelain(proc.stdout or "", resolve_paths=resolve_paths)


def _worktrees_root(repo_root: Path) -> Path:
    return (repo_root / ".worktrees").resolve()


def is_under_worktrees(repo_root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(_worktrees_root(repo_root))
    except ValueError:
        return False
    return True


def _worktree_clean(path: Path, *, timeout: float | None = None) -> bool | None:
    """Return True when the worktree has no meaningful dirty files.

    Untracked known caches and verified provisioned links are disposable;
    real environments and tracked changes retain the tree. Callers
    holding delegate's per-worktree lock pass
    :data:`_LOCKED_GIT_STATUS_TIMEOUT_S` so a wedged ``git status``
    surfaces as :class:`subprocess.TimeoutExpired` (a skip) instead of
    holding the lock (#8748).
    """
    proc = _run(["git", "status", "--porcelain", "-uall"], cwd=path, timeout=timeout)
    if proc.returncode != 0:
        return None
    primary = primary_checkout_root(path)
    for raw in (proc.stdout or "").splitlines():
        if len(raw) < 4:
            continue
        rel = raw[3:].strip().strip('"')
        if raw[:2] == "??" and worktree_artifacts.is_disposable_path(Path(rel), worktree=path, primary=primary):
            continue
        return False
    return True


# The states `gh pr list` can report. Anything else is an UNKNOWN, never
# an absence -- callers read "no open PR" as permission to delete.
_PR_STATES = frozenset({"OPEN", "MERGED", "CLOSED"})

_GITHUB_HOST = "github.com"
# SCP-style SSH. The host is the whole token between ``git@`` and ``:``;
# ``notgithub.com`` and ``prefix.github.com`` do not match.
_SCP_GITHUB_REMOTE_RE = re.compile(
    r"^git@github\.com:(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+)$",
    re.IGNORECASE,
)


def _github_owner_ok(owner: str) -> bool:
    """GitHub login: 1–39 alphanumerics or single hyphens, not at either end."""
    if not re.fullmatch(r"[A-Za-z0-9-]{1,39}", owner):
        return False
    return not owner.startswith("-") and not owner.endswith("-") and "--" not in owner


def _github_repo_ok(repo: str) -> bool:
    """One repository segment. A transport ``.git`` suffix is removed by the caller."""
    if not repo or repo.endswith(".git") or repo.startswith(".") or repo.endswith(".") or ".." in repo:
        return False
    return re.fullmatch(r"[A-Za-z0-9._-]{1,100}", repo) is not None


def _accept_github_slug(owner: str, repo: str) -> tuple[str, str] | None:
    if repo.endswith(".git"):
        repo = repo[: -len(".git")]
    if not _github_owner_ok(owner) or not _github_repo_ok(repo):
        return None
    return owner, repo


def _parse_github_origin(remote_url: str) -> tuple[str, str] | None:
    """Owner and repository for an HTTPS or SSH GitHub origin, else None.

    The host must be exactly ``github.com``. A ``.git`` suffix is optional.
    Owner and repository must each be one GitHub path segment, so a host that
    only contains the GitHub name cannot select some other repository.
    """
    text = remote_url
    if not text or any(char.isspace() for char in text) or "\\" in text:
        return None
    scp = _SCP_GITHUB_REMOTE_RE.fullmatch(text)
    if scp is not None:
        return _accept_github_slug(scp.group("owner"), scp.group("repo"))
    try:
        parts = urlsplit(text)
        if parts.scheme not in {"https", "ssh"} or parts.query or parts.fragment:
            return None
        # ``.port`` raises ValueError for a non-numeric or out-of-range port.
        # That is an unknown origin, not a sweep-wide crash.
        host = parts.hostname
        port = parts.port
    except ValueError:
        return None
    if host is None or host.lower() != _GITHUB_HOST or port is not None:
        return None
    if parts.scheme == "ssh" and parts.username != "git":
        return None
    path = parts.path[:-1] if parts.path.endswith("/") else parts.path
    segments = path.split("/")
    if len(segments) != 3 or not segments[1] or not segments[2]:
        return None
    return _accept_github_slug(segments[1], segments[2])


def _github_owner_repo(repo_root: Path) -> tuple[str, str] | None:
    """Parse the origin remote into an (owner, repo) pair without a network call."""
    raw = _configured_origin_url(repo_root)
    if raw is None:
        return None
    try:
        return _parse_github_origin(raw[:-1].decode("ascii"))
    except UnicodeError:
        return None


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
        proc = _run_gh(
            [
                "gh",
                "api",
                "--paginate",
                "--slurp",
                "-X",
                "GET",
                f"repos/{owner}/{repo}/pulls?"
                + urlencode({"head": f"{owner}:{branch}", "state": "all", "per_page": 100}),
            ],
            cwd=repo_root,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.SubprocessError) as exc:
        return [], f"REST PR lookup failed: {exc}"
    if proc.returncode != 0:
        return [], f"REST PR lookup failed: {_format_failure(proc)}"
    # Empty stdout is not the empty list. ``[]`` is a real "no PR" answer;
    # a blank body is an unknown guard and must not license removal.
    if not proc.stdout:
        return [], "REST PR lookup returned empty output"
    try:
        raw_items = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return [], f"REST PR lookup returned invalid JSON: {exc}"
    if not isinstance(raw_items, list) or any(not isinstance(page, list) for page in raw_items):
        return [], "REST PR lookup returned a non-list page"
    states: list[PullRequestState] = []
    for page in raw_items:
        for item in page:
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
        proc = _run_gh(
            [
                "gh",
                "pr",
                "list",
                "--head",
                branch,
                "--state",
                "all",
                "--limit",
                "1000",
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
    # Empty stdout is not the empty list. ``[]`` is a real "no PR" answer;
    # a blank body is an unknown guard and must not license removal.
    if not proc.stdout:
        return [], "gh pr list returned empty output"
    try:
        raw_items = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return [], f"gh pr list returned invalid JSON: {exc}"
    if not isinstance(raw_items, list):
        # Without this, a scalar payload (`123`) raises TypeError in the loop
        # below and a mapping would iterate its keys.
        return [], "gh pr list returned a non-list payload"
    if len(raw_items) >= 1000:
        return [], "gh pr list reached its limit; PR state is incomplete"

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
        proc = _run_gh(
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
        proc = _run_gh(
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
        if proc.age_s < max_age_s and proc.workspace_mtime is not None and (now - proc.workspace_mtime) < idle_grace_s:
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


def _read_sandbox_processes(proc_root: Path = Path("/proc"), *, repo_root: Path) -> list[SandboxProcess]:
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
) -> tuple[list[PullRequestState], str | None]:
    """Find PRs that introduced ``head_sha`` by GitHub commit-SHA search.

    Follow-up CI branches carry a different branch name than the MERGED PR head
    they fix, so ``gh pr list --head <branch>`` misses them.  A search hit means
    ``head_sha`` is a commit added by that PR, i.e. it equals the PR head or is
    an ancestor of it.  Returns ``(states, error)`` like the other PR queries:
    a failed search is an error, never an empty answer, because an unrecorded
    checkout may be named by no other PR guard.
    """
    if not head_sha:
        return [], None
    try:
        proc = _run_gh(
            ["gh", "search", "prs", head_sha, "--json", "number,state"],
            cwd=repo_root,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.SubprocessError) as exc:
        return [], f"{_PR_LOOKUP_FAILED} (gh search prs: {type(exc).__name__})"
    if proc.returncode != 0:
        return [], f"{_PR_LOOKUP_FAILED} (gh search prs exit {proc.returncode})"
    # Empty stdout is not the empty list. ``[]`` is a real "no PR" answer;
    # a blank body is an unknown guard and must not license removal.
    if not proc.stdout:
        return [], f"{_PR_LOOKUP_FAILED} (gh search prs returned empty output)"
    try:
        raw_items = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return [], f"{_PR_LOOKUP_FAILED} (gh search prs returned malformed JSON)"
    if not isinstance(raw_items, list):
        return [], f"{_PR_LOOKUP_FAILED} (gh search prs returned a non-list)"

    states: list[PullRequestState] = []
    for item in raw_items:
        # ``[null]`` and ``[{}]`` used to be skipped, which is an empty list,
        # and an empty list is permission to delete. Any row that is not a PR
        # object makes the whole answer unknown.
        parsed, err = _parse_search_pr_item(item, head_sha)
        if err is not None or parsed is None:
            return [], err or f"{_PR_LOOKUP_FAILED} (gh search prs returned an unusable row)"
        states.append(parsed)
    return states, None


def _parse_search_pr_item(item: Any, head_sha: str) -> tuple[PullRequestState | None, str | None]:
    """Map one ``gh search prs`` row; anything else is an unknown, not an absence."""
    if not isinstance(item, dict):
        return None, f"{_PR_LOOKUP_FAILED} (gh search prs row is not an object)"
    raw_state = item.get("state")
    state = str(raw_state).upper() if isinstance(raw_state, str) else ""
    if state not in _PR_STATES:
        return None, f"{_PR_LOOKUP_FAILED} (gh search prs row has an unusable state)"
    number = item.get("number")
    if isinstance(number, bool) or not isinstance(number, int) or number <= 0:
        return None, f"{_PR_LOOKUP_FAILED} (gh search prs row has no usable PR number)"
    return (
        PullRequestState(number=number, state=state, head_sha=head_sha, head_from_commit_search=True),
        None,
    )


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


def _merged_equivalent(info: WorktreeInfo, pr: PullRequestState | None) -> bool:
    """Prove every checkout patch against an authoritative merged PR head.

    Cherry omits merges, so divergent merge commits must refuse this class.
    Missing objects, malformed output and dirty checkouts are not proof.
    """
    if (
        pr is None
        or pr.state != "MERGED"
        or pr.head_from_commit_search
        or not pr.head_sha
        or not info.head
        or _worktree_clean(info.path) is not True
    ):
        return False
    for sha in (info.head, pr.head_sha):
        obj = _run(["git", "cat-file", "-t", sha], cwd=info.path)
        if obj.returncode != 0 or obj.stdout.strip() != "commit":
            return False
    merges = _run(["git", "rev-list", "--min-parents=2", f"{pr.head_sha}..{info.head}"], cwd=info.path)
    if merges.returncode != 0 or merges.stdout.strip():
        return False
    cherry = _run(["git", "cherry", pr.head_sha, info.head], cwd=info.path)
    return bool(
        cherry.returncode == 0 and all(re.fullmatch(r"- [a-f0-9]{40}", line) for line in cherry.stdout.splitlines())
    )


def _merged_head_relation(info: WorktreeInfo, pr: PullRequestState) -> str:
    if pr.head_sha == info.head:
        return "exact"
    if info.head and pr.head_sha and _sha_is_ancestor(info.path, info.head, pr.head_sha):
        return "ancestor"
    return "patch-equivalent"


def _tip_is_ancestor_of_origin_main(info: WorktreeInfo) -> bool:
    """True when the recorded tip, not a same-tree sibling, is on origin/main."""
    if not info.head:
        return False
    return _sha_is_ancestor(info.path, info.head, "origin/main")


def _merged_origin_gone_proof(info: WorktreeInfo, pr_state: PullRequestState) -> tuple[bool, str]:
    """Prove a local tip is contained in a merged PR or patch-equivalent upstream.

    Fetch both sources of proof live. A missing ref, ambiguous Git result, or
    failed probe retains the worktree and identifies commits for inspection.
    """
    if info.head is None:
        return False, "needs_attention; unproven commits: unknown; worktree HEAD unavailable"

    def unproven(shas: list[str], failure: str) -> tuple[bool, str]:
        return False, f"needs_attention; unproven commits: {', '.join(shas or [info.head])}; {failure}"

    def local_commits() -> list[str]:
        try:
            listed = _run(["git", "rev-list", f"origin/main..{info.head}"], cwd=info.path)
        except (OSError, subprocess.SubprocessError):
            return [info.head]
        return listed.stdout.splitlines() if listed.returncode == 0 else [info.head]

    try:
        primary = primary_checkout_root(info.path)
        if pr_state.number is None or not pr_state.head_sha:
            return unproven(local_commits(), "PR head unavailable")
        live_branch = _run(
            ["git", "ls-remote", "--heads", "origin", info.branch or ""],
            cwd=primary,
            timeout=30,
        )
        if live_branch.returncode != 0:
            detail = f": {live_branch.code}" if isinstance(live_branch, GitRefusal) else ""
            return unproven(local_commits(), f"origin branch probe failed{detail}")
        if live_branch.stdout.strip():
            return unproven(local_commits(), "origin branch returned")

        fetched_pr = _run(
            ["git", "fetch", "--no-tags", "origin", f"refs/pull/{pr_state.number}/head"],
            cwd=primary,
            timeout=30,
        )
        if fetched_pr.returncode != 0:
            return unproven(local_commits(), "PR head fetch failed")
        fetched_sha = _run(["git", "rev-parse", "--verify", "FETCH_HEAD"], cwd=primary)
        if fetched_sha.returncode != 0 or fetched_sha.stdout.strip() != pr_state.head_sha:
            return unproven(local_commits(), "fetched PR head does not match PR state")

        fetched_main = _run(
            ["git", "fetch", "--no-tags", "origin", "+refs/heads/main:refs/remotes/origin/main"],
            cwd=primary,
            timeout=30,
        )
        if fetched_main.returncode != 0:
            return unproven(local_commits(), "origin/main fetch failed")

        for descendant in (pr_state.head_sha, "origin/main"):
            ancestor = _run(
                ["git", "merge-base", "--is-ancestor", info.head, descendant],
                cwd=info.path,
            )
            if ancestor.returncode == 0:
                return True, ""
            if ancestor.returncode != 1:
                return unproven(local_commits(), "ancestry probe failed")

        cherry = _run(["git", "cherry", "origin/main", info.head], cwd=info.path)
        if cherry.returncode != 0:
            return unproven(local_commits(), "patch-equivalence probe failed")
        lines = cherry.stdout.splitlines()
        if any(len(line.split()) != 2 or line[0] not in "+-" for line in lines):
            return unproven(local_commits(), "patch-equivalence output invalid")
        unmatched = [line.split()[1] for line in lines if line.startswith("+")]
        if unmatched:
            return unproven(unmatched, "commits are not patch-equivalent upstream")
        return True, ""
    except (OSError, subprocess.SubprocessError):
        return unproven(local_commits(), "git containment probe failed")


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


def _open_file_probe_visibility_reason(deadline: float, proc_root: Path = Path("/proc")) -> str | None:
    """An empty lsof selection is proof only with a complete process view.

    Inaccessible process FDs/maps can be silently omitted by lsof. Require
    readable procfs entries; platforms without this visibility proof retain
    foreign checkouts. Process exits and closed FDs during the scan are safe.
    """
    unavailable = "open-file activity probe unavailable; foreign checkout preserved"
    try:
        # Linux UAPI PID_NS_INIT_INO (include/uapi/linux/nsfs.h), also used
        # by systemd. Comparing self with PID 1 alone accepts nested namespaces.
        initial_pid_namespace = f"pid:[{0xEFFFFFFC}]"
        if any(
            str((proc_root / process / "ns" / "pid").readlink()) != initial_pid_namespace for process in ("self", "1")
        ):
            return unavailable
        proc_mounts = 0
        for line in (proc_root / "self" / "mountinfo").read_text(encoding="utf-8").splitlines():
            fields = line.split()
            separator = fields.index("-")
            mountpoint = fields[4]
            if mountpoint == str(proc_root):
                proc_mounts += 1
                options = set(fields[5].split(",")) | set(fields[separator + 3].split(","))
                if (
                    fields[3] != "/"
                    or fields[separator + 1] != "proc"
                    or any(option.split("=", 1)[0] in {"hidepid", "subset", "pidns"} for option in options)
                ):
                    return unavailable
            elif mountpoint.startswith(f"{proc_root}/"):
                component = mountpoint[len(str(proc_root)) + 1 :].split("/", 1)[0]
                if component.isdigit() or component in {"self", "thread-self"}:
                    return unavailable
        if proc_mounts != 1:
            return unavailable
        processes = [entry for entry in proc_root.iterdir() if entry.name.isdigit()]
        if not processes:
            return unavailable
        for process in processes:
            if time.monotonic() >= deadline:
                return "open-file activity probe timed out; foreign checkout preserved"
            try:
                for fd in (process / "fd").iterdir():
                    if time.monotonic() >= deadline:
                        return "open-file activity probe timed out; foreign checkout preserved"
                    try:
                        fd.readlink()
                    except FileNotFoundError:
                        continue
                (process / "maps").read_bytes()
            except FileNotFoundError:
                if process.exists():
                    return unavailable
    except (OSError, ValueError, IndexError):
        return unavailable
    if time.monotonic() >= deadline:
        return "open-file activity probe timed out; foreign checkout preserved"
    return None


def _open_file_activity_reason(worktree: Path, *, timeout: float | None = None) -> str | None:
    """Prove no open or mapped files in a foreign checkout; never expose paths.

    No FD filter: lsof includes memory mappings as well as ordinary FDs.
    Cross nested mount points, but do not follow symlinks outside the tree.
    lsof exits 1 for an empty selection; diagnostics invalidate that proof.
    The shared runner also clips this probe to the locked-region deadline.
    """
    budget = _effective_timeout(15 if timeout is None else timeout)
    assert budget is not None
    deadline = time.monotonic() + budget
    try:
        proc = _run(
            ["lsof", "+w", "-n", "-P", "-F", "p", "+D", str(worktree), "-x", "f"],
            cwd=worktree.parent,
            timeout=budget,
        )
    except subprocess.TimeoutExpired:
        return "open-file activity probe timed out; foreign checkout preserved"
    except (OSError, subprocess.SubprocessError):
        return "open-file activity probe unavailable; foreign checkout preserved"
    if any(re.fullmatch(r"p[0-9]+", line) for line in (proc.stdout or "").splitlines()):
        return "live process has open or mapped files inside foreign checkout"
    if proc.returncode != 1 or (proc.stdout or "").strip() or (proc.stderr or "").strip():
        return "open-file activity probe unavailable; foreign checkout preserved"
    return _open_file_probe_visibility_reason(deadline)


def _dispatch_task_id(repo_root: Path, info: WorktreeInfo) -> str | None:
    return _dispatch_task_id_for_path(repo_root, info.path)


def _dispatch_task_id_for_path(repo_root: Path, path: Path) -> str | None:
    dispatch_root = (repo_root / ".worktrees" / "dispatch").resolve()
    try:
        relative = path.resolve().relative_to(dispatch_root)
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
_GIT_INITIALIZING_LOCK_REASON = worktree_prep.INITIALIZING_LOCK_REASON
# Minimum age for a zero-file dispatch husk before it may be removed.
# ``delegate.py`` creates the dispatch directory before ``git worktree add``
# registers it, so an unregistered empty directory can be mid-creation; the
# provisioning window is seconds, and one hour bounds it with a wide margin
# while still reaping same-day debris.
_DISPATCH_HUSK_MIN_AGE_HOURS = 1.0
# How long the husk sweep waits for the per-path worktree lock before it
# skips. ``git worktree add`` writes its admin registration
# (``.git/worktrees/<name>/gitdir``) before ``.git`` appears in the target,
# so the sweep's listing snapshot can predate a registration that is already
# committed (#8711); the final re-check runs under the same lock dispatch
# holds. A dispatch add holds that lock only briefly at this granularity, so
# a short wait bounds the sweep without stalling it.
_DISPATCH_HUSK_LOCK_TIMEOUT_S = 10.0
# Per-call cap for a git command that passes no timeout while a per-worktree
# lock is held: the husk removal's locked re-check, and every otherwise
# unbounded git call inside :func:`_bounded_locked_git`. A hung ``git worktree
# list`` would otherwise hold that lock indefinitely and a waiting dispatch
# would fail on its own 30s lock timeout (#8748); an expired bound skips.
_LOCKED_GIT_TIMEOUT_S = 5.0
# Per-call cap for the tree-walking git calls in the qualified-reap locked
# region: ``git status --porcelain -uall`` and the preserve ``git add`` /
# ``git commit``. Measured 0.31s on a 283MB dispatch worktree (#8748
# follow-up). This cap is still clipped by the region deadline below.
_LOCKED_GIT_STATUS_TIMEOUT_S = 15.0
# The locked region must finish inside a dispatch's
# ``worktree_claims.DEFAULT_LOCK_TIMEOUT_S`` wait (30s) and still leave this
# margin so the holder releases the lock before the waiter gives up.
_LOCKED_REGION_MARGIN_S = 5.0
# A preserve ``git add``/``git commit`` killed under the lock can leave
# ``<admin>/index.lock``. A later sweep names a lock this old when no live
# process has it open. The reaper never deletes the lock itself.
_STALE_INDEX_LOCK_MIN_AGE_S = 600.0


def _locked_region_budget_s() -> float:
    """Seconds the qualified-reap locked region may hold the per-worktree lock.

    ``worktree_claims.DEFAULT_LOCK_TIMEOUT_S`` minus :data:`_LOCKED_REGION_MARGIN_S`.
    """
    return max(0.0, worktree_claims.DEFAULT_LOCK_TIMEOUT_S - _LOCKED_REGION_MARGIN_S)


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
    """Re-prove every ACP runtime precondition immediately before deletion.

    Runs under delegate's per-worktree lock, so the listing inherits the
    locked-git budget (:func:`_bounded_locked_git`); a wedged or failed
    listing is a skip reason here, never an exception escaping the guard
    (#8748).
    """
    fresh: WorktreeInfo | None = None
    try:
        worktrees = list_git_worktrees(repo_root)
    except RuntimeError as exc:
        return f"acp runtime worktree list unavailable during cleanup ({exc})"
    for current in worktrees:
        if current.path.resolve() == info.path.resolve():
            fresh = current
            break
    if fresh is None:
        return "acp runtime worktree unregistered during cleanup"
    live_cwds = _live_cwd_paths(repo_root)
    if live_cwds is None:
        return "process-CWD activity probe unavailable during cleanup"
    if (
        _acp_dead_owner_reason(
            repo_root=repo_root,
            info=fresh,
            now=None,
            live_cwds=live_cwds,
        )
        is None
    ):
        return "acp runtime lock owner changed during cleanup"
    if not holds_only_git_pointer(info.path):
        return "acp runtime worktree gained files during cleanup"
    return None


def _names_path(claimed: object, path: Path) -> bool:
    """True when ``claimed`` is a non-empty path string resolving to ``path``."""
    if not isinstance(claimed, str) or not claimed:
        return False
    try:
        return Path(claimed).resolve() == path.resolve()
    except (OSError, RuntimeError):
        return False


def _initializing_leftover_result(repo_root: Path, info: WorktreeInfo) -> ReapResult | None:
    """Report-only class (#8663): a worktree dispatch's stopped ``git worktree add`` left.

    Applies to a worktree git still locks ``initializing`` whose dispatch
    task record carries the ``worktree_prep`` reservation for this path.
    Such a worktree is never removed, unlocked or pruned automatically:
    every ownership proof tried for that left a race in which a foreign or
    completed worktree qualified. While the reserving dispatch may still be
    running its add, the result says so; otherwise it is
    ``needs_attention: initializing_leftover`` with the evidence and a
    removal command marked "verify first:"; each pass journals it as a
    ``needs_attention`` event. Returns ``None`` for any other worktree.
    """
    if info.locked_reason != _GIT_INITIALIZING_LOCK_REASON:
        return None
    task_id = _dispatch_task_id(repo_root, info)
    payload = _task_record(repo_root, task_id)
    prep = payload.get("worktree_prep") if payload is not None else None
    if payload is None or not isinstance(prep, dict) or not _names_path(prep.get("path"), info.path):
        return None
    owner = _dispatch_owner(repo_root, info)
    status = payload.get("status")
    if status in ("running", "spawning") and not worktree_prep.is_orphaned_prep_record(payload):
        return ReapResult(
            path=str(info.path),
            branch=info.branch,
            action="skipped",
            reason=f"active dispatch task-id={task_id} status={status}: git worktree add may still be running",
            dirty=None,
            owner=owner,
        )
    command = worktree_prep.verify_first_command(repo_root, info.path)
    finding = {
        "kind": worktree_prep.LEFTOVER_KIND,
        "task_id": task_id,
        "task_status": status,
        "worktree_prep": prep,
        "evidence": worktree_prep.leftover_evidence(prep, info.path),
        "command": command,
    }
    reason = (
        f"needs_attention: {worktree_prep.LEFTOVER_KIND}; task-id={task_id} status={status}; "
        f"git worktree add left this worktree locked 'initializing'; never removed automatically; {command}"
    )
    return ReapResult(
        path=str(info.path),
        branch=info.branch,
        action="skipped",
        reason=reason,
        dirty=None,
        owner=owner,
        needs_attention=finding,
    )


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


def _admin_registered_worktree_paths(common_git_dir: Path) -> set[Path]:
    """Worktree paths named by a ``.git/worktrees/*/gitdir`` registration.

    ``git worktree add`` writes this admin entry before ``.git`` appears in
    the target directory, and ``git worktree list --porcelain`` can lag it
    (#8711), so the locked re-check reads the admin directory directly. Each
    ``gitdir`` file holds the path of the target's ``.git`` file; git 2.48+
    can record it relative (``worktree.useRelativePaths`` /
    ``--relative-paths``), resolved the way git resolves it — against the
    admin entry's own directory. Only a proven absence
    (``FileNotFoundError``/``NotADirectoryError``) reads as "no
    registrations"; every other read failure raises: the caller fails closed.
    """
    registered: set[Path] = set()
    admin_dir = common_git_dir / "worktrees"
    # ``iterdir()`` directly: ``is_dir()`` also answers False on EACCES, which
    # would read an untraversable admin dir as "no registrations" (#8748).
    try:
        entries = list(admin_dir.iterdir())
    except (FileNotFoundError, NotADirectoryError):
        return registered
    except OSError as exc:
        raise RuntimeError(f"git worktree admin dir {admin_dir} unreadable: {exc}") from exc
    for entry in entries:
        gitdir = entry / "gitdir"
        # Only a proven absence skips an entry; ``Path.is_file()`` would also
        # turn an untraversable entry into "no registration" on interpreters
        # that swallow EACCES (#8748).
        try:
            raw = gitdir.read_text(encoding="utf-8", errors="surrogateescape").strip()
        except (FileNotFoundError, NotADirectoryError):
            continue
        except OSError as exc:
            raise RuntimeError(f"git worktree registration {gitdir} unreadable: {exc}") from exc
        if not raw:
            continue
        target = Path(raw)
        if not target.is_absolute():
            target = entry / target
        registered.add(target.parent.resolve())
    return registered


def _remove_dispatch_husk_locked(repo_root: Path, *, child: Path, resolved: Path) -> str | None:
    """Re-check registration and emptiness under delegate's per-path lock, then remove (#8711).

    Dispatch holds :func:`worktree_claims.worktree_lock` for the target path
    across its whole ``git worktree add``, so while this holds the same lock
    no add can be mid-registration: either the add registered first (and the
    fresh re-check below sees it) or it waits and then finds the directory
    gone. Returns a skip reason, or ``None`` after the husk was removed.
    Raises :class:`worktree_claims.WorktreeLockError` when the lock is not
    taken and :class:`RuntimeError` when a re-check probe fails or a git call
    outlives ``_LOCKED_GIT_TIMEOUT_S``; the caller turns both into a skip,
    never a removal.

    The lock directory comes from the strict
    :func:`worktree_claims.control_plane_root`, like
    :func:`_enter_dispatch_worktree_guard`: a mutating caller must refuse
    when the fleet catalog is unreadable, never fall back to the local
    checkout — delegate holds the lock on the public primary for a
    ``--repo`` sibling, so locking anywhere else would not exclude it
    (#8711 review). A lock directory that cannot be resolved is reported
    with the guard's :data:`worktree_claims.LOCK_UNAVAILABLE` reason.
    """
    try:
        control_root = worktree_claims.control_plane_root(primary_checkout_root(repo_root))
        lock_dir = _common_git_dir(control_root, timeout=_LOCKED_GIT_TIMEOUT_S) / worktree_claims.LOCK_DIR_NAME
    except RuntimeError as exc:
        return f"{worktree_claims.LOCK_UNAVAILABLE} ({exc})"
    common_git_dir = _common_git_dir(repo_root, timeout=_LOCKED_GIT_TIMEOUT_S)
    with worktree_claims.worktree_lock(child, lock_dir=lock_dir, timeout_s=_DISPATCH_HUSK_LOCK_TIMEOUT_S):
        listing = {info.path for info in list_git_worktrees(repo_root, timeout=_LOCKED_GIT_TIMEOUT_S)}
        if resolved in listing:
            return "path registered as a git worktree during the locked re-check; a concurrent add claimed it"
        admin_registered = _admin_registered_worktree_paths(common_git_dir)
        if resolved in admin_registered:
            return "path registered in .git/worktrees/*/gitdir during the locked re-check; a concurrent add claimed it"
        if _tree_has_any_file_or_symlink(resolved):
            return "files appeared in the husk during the locked re-check; treating as in use"
        age_hours = _tree_newest_age_hours(resolved)
        if age_hours is None:
            raise RuntimeError(f"could not determine husk age during the locked re-check: {resolved}")
        if age_hours < _DISPATCH_HUSK_MIN_AGE_HOURS:
            return (
                f"empty placeholder husk is only {age_hours:.1f}h old "
                f"(< {_DISPATCH_HUSK_MIN_AGE_HOURS:g}h minimum) at the locked re-check; treating as in use"
            )
        target = assert_delete_target(child, repo_root=repo_root)
        shutil.rmtree(target)
    return None


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
    directory still being provisioned is never "old") all preserve. The
    removal itself runs under delegate's per-path worktree lock with a fresh
    registration re-check (#8711): the ``registered`` snapshot this sweep was
    called with can predate a concurrent ``git worktree add``, which writes
    its admin registration before ``.git`` appears in the target.
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
                refusal = _remove_dispatch_husk_locked(repo_root, child=child, resolved=resolved)
            except worktree_claims.WorktreeLockError as exc:
                results.append(
                    ReapResult(
                        path=str(child),
                        branch=None,
                        action="skipped",
                        reason=f"{worktree_claims.lock_refusal(exc)} ({exc})",
                        dirty=False,
                        owner=owner,
                    )
                )
                continue
            except RuntimeError as exc:
                results.append(
                    ReapResult(
                        path=str(child),
                        branch=None,
                        action="skipped",
                        reason=f"husk registration re-check failed closed ({exc})",
                        dirty=False,
                        owner=owner,
                    )
                )
                continue
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
            if refusal is not None:
                results.append(
                    ReapResult(
                        path=str(child),
                        branch=None,
                        action="skipped",
                        reason=refusal,
                        dirty=False,
                        owner=owner,
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
    if result.needs_attention is not None or reason.startswith(("needs_attention;", "needs_attention:")):
        return "needs_attention"
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
    primary = control_plane_root(repo_root)
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
        db_path = control_plane_root(repo_root) / "batch_state" / "tasks" / "write-ownership.sqlite3"
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
                    record = _task_record(repo_root, task_id) or {"pid": int(row_pid)}
                    if record.get("pid") != int(row_pid):
                        record = {"pid": int(row_pid)}
                    if worker_liveness(record) is not False:
                        return f"active write claim task-id={task_id}"
        finally:
            conn.close()
    except Exception as exc:
        return f"active write claim check failed task-id={task_id}: {exc}"
    return None


def _task_record(repo_root: Path, task_id: str | None) -> dict[str, Any] | None:
    if not task_id:
        return None
    task_file = control_plane_root(repo_root) / "batch_state" / "tasks" / f"{task_id}.json"
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
    """Protect workers whose identity is live or unknown; pid-less records use status."""
    if not payload or not payload.get("pid"):
        return False
    return worker_liveness(payload) is not False


def _activity_reason(
    *,
    repo_root: Path,
    info: WorktreeInfo,
    active_ids: set[str] | None,
    live_cwds: set[Path] | None,
    check_pending: bool = True,
    probe_attachment_lock: bool = False,
) -> str | None:
    if check_pending and reaper_lifecycle.is_reap_pending(repo_root, info.path):
        return "active reap reservation"

    primary = primary_checkout_root(repo_root)
    try:
        control_root = worktree_claims.control_plane_root(primary)
    except worktree_claims.ControlPlaneError as exc:
        return f"{worktree_claims.LOCK_UNAVAILABLE} ({exc})"
    review_claim = worktree_claims.active_worktree_claim_refusal(
        info.path,
        tasks_dir=control_root / "batch_state" / "tasks",
        repo_root=primary,
        review_inputs_only=True,
    )
    if review_claim is not None:
        return review_claim
    if probe_attachment_lock:
        # Before publication, input preparation holds this transient lock.
        # Report it preserved at plan time too. Locked removal rechecks skip
        # this probe because they already hold the same lock themselves.
        try:
            lock_refusal = worktree_claims.existing_worktree_lock_refusal(
                info.path, lock_dir=worktree_claims.repository_lock_dir(control_root)
            )
        except worktree_claims.WorktreeLockError as exc:
            return f"{worktree_claims.LOCK_UNAVAILABLE} ({exc})"
        if lock_refusal is not None:
            return f"{lock_refusal} (active dispatch attachment)"

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

    # Terminal metadata can precede process exit. A live PID protects the
    # checkout regardless of status; a dead PID alone never proves settlement.
    if _task_pid_alive(task_payload):
        return f"live process task-id={task_id} status={task_status}"
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


_UNSETTLED_TASK_STATUSES = frozenset({"queued", "starting", "spawning", "running"})


def _process_reader() -> worker_leftovers.ProcessReader:
    """Seam for tests: the live ``/proc`` and cgroup reader."""
    return worker_leftovers.ProcFsReader()


def _task_leftover_scope(repo_root: Path, path: Path) -> tuple[worker_leftovers.WorkerScope | None, str | None]:
    """The scope of a settled task's possibly live background jobs (#8991).

    ``(scope, None)`` when its exit scan found jobs or could not tell;
    ``(None, None)`` when there is nothing to stop, or the worker is still
    running and owns its processes; ``(None, refusal)`` when the record says
    jobs may be alive but its scope does not match the task's launch
    identity (:func:`worker_leftovers.scope_from_record`).
    """
    task_id = _dispatch_task_id_for_path(repo_root, path)
    record = _task_record(repo_root, task_id)
    if record is None or task_id is None:
        return None, None
    if str(record.get("status") or "") in _UNSETTLED_TASK_STATUSES or _task_pid_alive(record):
        return None, None
    return worker_leftovers.scope_from_record(record, task_id=task_id)


def live_cwds_for_reap(repo_root: Path, path: Path, live_cwds: set[Path] | None) -> set[Path] | None:
    """``live_cwds`` without the worktree's own settled background jobs.

    A settled task's leftover jobs hold its worktree as their cwd, which would
    keep it from ever being reaped. When every process inside ``path`` is one
    of those jobs, their cwds are dropped here and the jobs are stopped just
    before removal (:func:`_stop_task_background_jobs`); any other holder
    keeps the whole set.
    """
    if live_cwds is None:
        return None
    scope, _refusal = _task_leftover_scope(repo_root, path)
    if scope is None or not worker_leftovers.only_leftovers_hold(path, scope, reader=_process_reader()):
        return live_cwds
    root = path.resolve()
    return {cwd for cwd in live_cwds if not _path_contains(root, cwd)}


def _stop_task_background_jobs(repo_root: Path, path: Path) -> str | None:
    """Stop a settled task's leftover jobs before its worktree goes; refusal reason or None.

    Only processes inside that worker's own scope unit, or on the Popen
    fallback carrying its task marker, are signalled. A record whose scope
    does not match the task's launch identity is refused, never acted on.
    """
    scope, refusal = _task_leftover_scope(repo_root, path)
    if refusal is not None:
        task_id = _dispatch_task_id_for_path(repo_root, path)
        return f"background jobs of task-id={task_id} may be alive but its recorded scope is refused ({refusal})"
    if scope is None:
        return None
    try:
        stopped = worker_leftovers.stop_leftovers(scope, reader=_process_reader())
    except Exception as exc:  # a failed stop must leave the worktree, never crash the sweep
        return f"background jobs of task-id={scope.task_id} could not be stopped ({type(exc).__name__}: {exc})"
    if not stopped.ok:
        survivors = ", ".join(str(proc.pid) for proc in stopped.survivors) or "unknown"
        if stopped.unsignalled:
            survivors = f"{survivors}; not signalled {', '.join(map(str, stopped.unsignalled))}"
        return f"background jobs of task-id={scope.task_id} could not be stopped ({stopped.error}; pids {survivors})"
    live_cwds = _live_cwd_paths(repo_root)
    if live_cwds is None:
        return "process-CWD activity probe unavailable after stopping background jobs"
    root = path.resolve()
    for cwd in live_cwds:
        if _path_contains(root, cwd):
            return f"live process cwd={cwd}"
    return None


def _common_git_dir(repo_root: Path, *, timeout: float | None = None) -> Path:
    try:
        proc = _run(["git", "rev-parse", "--git-common-dir"], cwd=repo_root, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"git rev-parse --git-common-dir timed out after {exc.timeout:g}s") from exc
    if proc.returncode != 0:
        raise RuntimeError(f"cannot resolve git common dir: {_format_failure(proc)}")
    path = Path((proc.stdout or "").strip())
    if not path.is_absolute():
        path = repo_root / path
    return path.resolve()


DEFAULT_REAP_LOCK_TIMEOUT_S = 30.0


class _ReapLockBusy(RuntimeError):
    """Another cleanup held the reaper lock for the whole wait."""


class _ReapLock:
    def __init__(self, repo_root: Path, *, timeout_s: float | None = None) -> None:
        self.path = _common_git_dir(repo_root) / "worktree-reaper.lock"
        self.handle: Any = None
        self.timeout_s = DEFAULT_REAP_LOCK_TIMEOUT_S if timeout_s is None else timeout_s

    def __enter__(self) -> None:
        try:
            with contextlib.ExitStack() as cleanup:
                directory = os.open(self.path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
                cleanup.callback(os.close, directory)
                descriptor = safe_open_below(directory, self.path.name, os.O_RDWR | os.O_CREAT)
                try:
                    if os.fstat(descriptor).st_nlink != 1:
                        raise RuntimeError("unsafe reaper lock: hardlinked file")
                    self.handle = os.fdopen(descriptor, "r+", encoding="utf-8")
                except BaseException:
                    os.close(descriptor)
                    raise
        except OSError as exc:
            raise RuntimeError(f"reaper lock unavailable or unsafe: {exc}") from exc
        deadline = time.monotonic() + self.timeout_s
        try:
            while True:
                try:
                    fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError as exc:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        self.handle.seek(0)
                        try:
                            raw_pid = self.handle.read(32).strip()
                        except UnicodeError:
                            raw_pid = ""
                        holder = raw_pid if raw_pid.isascii() and raw_pid.isdigit() else "unknown"
                        raise _ReapLockBusy(
                            f"another worktree cleanup holds {self.path}; holder pid={holder}; "
                            f"waited {self.timeout_s:g}s"
                        ) from exc
                    time.sleep(min(0.05, remaining))
            self.handle.seek(0)
            self.handle.truncate()
            self.handle.write(str(os.getpid()))
            self.handle.flush()
        except BaseException:
            self.handle.close()
            raise

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
    """Return whether origin has ``branch``; None on failure, reporting typed refusals."""
    if not branch:
        return False
    # Called before the per-worktree lock. 30s is this probe's own cap; it is
    # not part of the locked-region deadline. The locked re-check uses the
    # local remote-tracking ref (:func:`_origin_branch_present`) instead.
    proc = _run(["git", "ls-remote", "--heads", "origin", branch], cwd=primary_checkout_root(path), timeout=30)
    if proc.returncode != 0:
        if isinstance(proc, GitRefusal):
            print(f"live origin proof unavailable: {proc.code}", file=sys.stderr)
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


class _ActiveTaskProbeFailure(RuntimeError):
    def __init__(self, reason: str, fallback_allowed: bool) -> None:
        super().__init__(reason)
        self.reason = reason
        self.fallback_allowed = fallback_allowed


def _active_task_ids() -> set[str] | None:
    try:
        import urllib.request

        with urllib.request.urlopen("http://127.0.0.1:8765/api/delegate/active", timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if not isinstance(data, dict) or not isinstance(data.get("tasks"), list):
                raise ValueError("activity response must contain a tasks list")
            tasks = data["tasks"]
            if any(not isinstance(t, dict) or not isinstance(t.get("task_id"), str) or not t["task_id"] for t in tasks):
                raise ValueError("activity response contains an invalid task identity")
            return {t["task_id"] for t in tasks}
    except Exception as exc:
        transport = isinstance(exc, TimeoutError | ConnectionError) or (
            isinstance(exc, URLError) and not isinstance(exc, HTTPError)
        )
        code = "timeout" if isinstance(exc, TimeoutError) else "transport_error" if transport else "invalid_response"
        raise _ActiveTaskProbeFailure(
            reason=f"active-task probe unavailable [active_task_probe_{code}]: {type(exc).__name__}: {exc}",
            fallback_allowed=transport,
        ) from exc


def _read_active_task_probe() -> set[str] | _ActiveTaskProbeFailure | None:
    """Keep typed failures for the reaper; delegate callers handle them as unknown."""
    try:
        return _active_task_ids()
    except _ActiveTaskProbeFailure as exc:
        return exc


def _resolve_activity_probe(
    repo_root: Path,
    info: WorktreeInfo,
    probe: set[str] | _ActiveTaskProbeFailure | None,
) -> tuple[set[str] | None, str | None]:
    """Resolve a transport outage for this attributed checkout only.

    Local terminal status never stands in for global Monitor availability.
    Missing task records leave Monitor activity unknown for class-specific
    guards. Invalid records, state or PID retain the tree; every other
    deletion guard and the locked recheck still apply.
    """
    if not isinstance(probe, _ActiveTaskProbeFailure):
        return probe, None
    if not probe.fallback_allowed:
        return None, probe.reason
    task_id = _dispatch_task_id(repo_root, info)
    if task_id and (Path(task_id).name != task_id or task_id in {".", ".."}):
        return None, f"{probe.reason}; local_task_unattributed"
    task_file = control_plane_root(repo_root) / "batch_state" / "tasks" / f"{task_id}.json" if task_id else None
    try:
        try:
            raw_payload = task_file.read_text(encoding="utf-8") if task_file else None
        except FileNotFoundError:
            raw_payload = None
        if raw_payload is None:
            reaper_lifecycle.append_journal(
                repo_root,
                "activity-probe-unattributed",
                path=str(info.path),
                task_id=task_id,
                reason=probe.reason,
                source="no_local_task_record",
            )
            return None, None
        payload = json.loads(raw_payload)
        if not isinstance(payload, dict) or payload.get("task_id") != task_id:
            return None, f"{probe.reason}; local_task_identity_mismatch"
        recorded_path = payload.get("worktree_path") or payload.get("cwd")
        if not isinstance(recorded_path, str) or not recorded_path:
            return None, f"{probe.reason}; local_task_binding_missing"
        bound_path = Path(recorded_path)
        if not bound_path.is_absolute():
            bound_path = control_plane_root(repo_root) / bound_path
        if bound_path.resolve() != info.path.resolve():
            return None, f"{probe.reason}; local_task_binding_mismatch"
        pid = payload.get("pid")
        if pid is not None and (type(pid) is not int or pid <= 0):
            return None, f"{probe.reason}; local_task_pid_invalid"
        if _task_pid_alive(payload):
            return None, f"{probe.reason}; local_task_live_process task-id={task_id}"
        if payload.get("status") not in _TERMINAL_DISPATCH_STATUSES:
            return None, f"{probe.reason}; local_task_nonterminal task-id={task_id}"
    except (OSError, ValueError, TypeError) as exc:
        return None, f"{probe.reason}; local_task_probe_error: {type(exc).__name__}: {exc}"
    reaper_lifecycle.append_journal(
        repo_root,
        "activity-probe-fallback",
        path=str(info.path),
        task_id=task_id,
        reason=probe.reason,
        source="local_task_record",
        status=payload["status"],
    )
    return set(), None


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


_DETACHED_CLEAN_CONTAINED_PREFIX = "detached clean contained"


def _tree_holds_only_disposable_residue(path: Path, *, timeout: float | None = None) -> bool:
    """True only for ignored regenerable caches or verified provisioned links.

    Deliberately stricter than :func:`_worktree_clean`: only status ``!!``
    (ignored) is tolerated, so any staged, modified, renamed or untracked entry
    preserves the tree. Both allowlists are fixed rather than read from
    ``.gitignore`` or ``info/exclude``. Provisioned links must resolve to the
    same relative path in this repository's primary checkout; no target is
    opened or removed here. A git or resolution failure is not proof.
    """
    status = _run(
        ["git", "status", "--porcelain=v1", "-z", "--ignored", "--untracked-files=all"],
        cwd=path,
        timeout=timeout,
    )
    if status.returncode != 0:
        return False
    for entry in (status.stdout or "").split("\0"):
        if not entry:
            continue
        # ``XY <path>``; rename/copy entries carry a status other than ``!!``.
        if not entry.startswith("!! "):
            return False
        relative = entry[3:]
        try:
            primary = primary_checkout_root(path)
            if not worktree_artifacts.is_disposable_path(Path(relative), worktree=path, primary=primary):
                return False
        except (OSError, RuntimeError):
            return False
    return True


def _detached_clean_contained_reason(
    *,
    repo_root: Path,
    info: WorktreeInfo,
    active_ids: set[str] | None,
    timeout: float | None = None,
    attention: list[str] | None = None,
) -> str | None:
    """Provably-safe class: a clean detached dispatch checkout whose HEAD is pushed.

    A worker's baseline or scratch checkout (``git worktree add --detach``)
    holds nothing unique once its HEAD is an ancestor of ``origin/main`` or
    contained in some ``origin/*`` ref and the tree has no tracked, untracked,
    or non-disposable ignored changes. It is a Class B superset that needs neither
    a settled task record nor a 24h age, and it never consults PR state:
    nothing is lost even if a PR names the commit. A locked checkout, an
    active or non-terminal task bound to the path, and live cwds (checked by
    :func:`_activity_reason` before this runs, and again at removal) all keep
    it preserved. An unavailable active-task probe fails closed, like the
    terminal-dispatch path, and is reported through ``attention``.
    """
    if not info.detached or info.branch is not None or not info.head:
        return None
    if info.locked_reason is not None:
        return None
    if _is_acp_runtime_path(repo_root, info.path):
        return None
    task_id = _dispatch_task_id(repo_root, info)
    if task_id is None:
        return None
    if active_ids is None:
        if attention is not None:
            attention.append("active-task probe unavailable; detached clean contained checkout preserved")
        return None
    if task_id in active_ids:
        return None
    task_status = _task_record_status(repo_root, task_id)
    if task_status is not None and task_status not in _TERMINAL_DISPATCH_STATUSES:
        return None
    if not _tree_holds_only_disposable_residue(info.path, timeout=timeout):
        return None
    if _is_ancestor_of_origin_main(info.path):
        contained = "an ancestor of origin/main"
    elif _is_head_reachable_from_remote(info.path, info.head):
        contained = "contained in an origin/* ref"
    else:
        return None
    return f"{_DETACHED_CLEAN_CONTAINED_PREFIX}: HEAD {info.head[:12]} is {contained}"


def _detached_clean_contained_recheck(repo_root: Path, info: WorktreeInfo) -> str | None:
    """Re-prove the class immediately before deletion, under delegate's lock.

    Returns a skip reason, or ``None`` when every precondition still holds.
    """
    try:
        worktrees = list_git_worktrees(repo_root)
    except RuntimeError as exc:
        return f"detached worktree list unavailable during cleanup ({exc})"
    fresh = next((wt for wt in worktrees if wt.path.resolve() == info.path.resolve()), None)
    if fresh is None:
        return "detached worktree unregistered during cleanup"
    current_active_ids, probe_error = _resolve_activity_probe(repo_root, fresh, _read_active_task_probe())
    if current_active_ids is None:
        return f"{probe_error or 'active-task probe unavailable'} during cleanup"
    current_live_cwds = _live_cwd_paths(repo_root)
    if current_live_cwds is None:
        return "process-CWD activity probe unavailable during cleanup"
    activity = _activity_reason(
        repo_root=repo_root,
        info=fresh,
        active_ids=current_active_ids,
        live_cwds=current_live_cwds,
        check_pending=False,
    )
    if activity is not None:
        return activity
    if (
        _detached_clean_contained_reason(
            repo_root=repo_root,
            info=fresh,
            active_ids=current_active_ids,
            timeout=_LOCKED_GIT_STATUS_TIMEOUT_S,
        )
        is None
    ):
        return "detached clean contained proof changed during cleanup"
    return None


# Review-checkout classes (#9129). Native ``codex exec`` reviews and agent
# scratchpads register worktrees the task-bound classes never see; each class
# below removes only a clean checkout whose HEAD is already on a remote ref.
_SUPERSEDED_PR_REASON_PREFIX = "superseded PR #"
_PR_LOOKUP_FAILED = "pr lookup failed; kept"
_UNRECORDED_DETACHED_REASON = "unrecorded detached checkout"
_FOREIGN_CHECKOUT_REASON = "foreign registered checkout"
_UNRECORDED_DETACHED_MIN_AGE_HOURS = 2.0
_FOREIGN_SCRATCH_DIR = "scratchpad"


def _foreign_scratch_roots() -> tuple[Path, ...]:
    """Roots under which a registered worktree outside ``.worktrees/`` is scratch."""
    candidates = [Path("/tmp"), Path("/var/tmp")]
    tmpdir = os.environ.get("TMPDIR")
    if tmpdir:
        candidates.append(Path(tmpdir))
    roots: list[Path] = []
    for candidate in candidates:
        with contextlib.suppress(OSError):
            resolved = candidate.resolve()
            if resolved.parent != resolved and resolved not in roots:
                roots.append(resolved)
    return tuple(roots)


def _foreign_scratch_root(repo_root: Path, path: Path) -> Path | None:
    """The approved deletion root above a foreign scratch checkout, else ``None``.

    A scratch checkout sits strictly below a temp root or below a directory
    named ``scratchpad`` (Claude and agent session scratch space). Anything
    inside the repository itself is never foreign.
    """
    try:
        resolved = path.resolve()
    except OSError:
        return None
    for owned in (repo_root.resolve(), primary_checkout_root(repo_root).resolve()):
        if _path_contains(owned, resolved):
            return None
    for root in _foreign_scratch_roots():
        if resolved != root and _path_contains(root, resolved):
            return root
    parts = resolved.parts
    for index in range(len(parts) - 2, 0, -1):
        if parts[index] == _FOREIGN_SCRATCH_DIR:
            return Path(*parts[: index + 1])
    return None


def _review_checkout_gate(
    *,
    repo_root: Path,
    info: WorktreeInfo,
    active_ids: set[str] | None,
    attention: list[str] | None,
    require_detached: bool,
    timeout: float | None = None,
) -> bool:
    """Safety checks every review-checkout class shares.

    A tree holding only regenerable ignored caches or verified provisioned links
    (the same exhaustive guard as the detached clean contained class: no
    tolerance for real ``.venv`` or ``node_modules`` entries, tracked changes,
    or other ignored files),
    HEAD on a remote ref, unlocked, and no task that is still unfinished. Live process cwds and active tasks are refused earlier by
    :func:`_activity_reason` and again at removal. An unavailable active-task
    probe fails closed, like the detached clean contained class.
    """
    if not info.head or info.locked_reason is not None:
        return False
    if require_detached and (not info.detached or info.branch is not None):
        return False
    if _is_acp_runtime_path(repo_root, info.path):
        return False
    if active_ids is None:
        if attention is not None:
            attention.append("active-task probe unavailable; review checkout preserved")
        return False
    task_id = _dispatch_task_id(repo_root, info)
    if task_id is not None:
        if task_id in active_ids:
            return False
        status = _task_record_status(repo_root, task_id)
        if status is not None and status not in _TERMINAL_DISPATCH_STATUSES:
            return False
    if not _tree_holds_only_disposable_residue(info.path, timeout=timeout):
        return False
    return _is_head_reachable_from_remote(info.path, info.head)


def _review_pr_context(
    repo_root: Path,
    info: WorktreeInfo,
) -> tuple[list[PullRequestState], list[PullRequestState], int | None, list[str]]:
    """PR states naming a checkout: ``(all_states, commit_search_hits, review_number, errors)``.

    A GraphQL "not a PullRequest" answer for the parsed review token means the
    token is an issue number: absence, not an unreadable guard.
    """
    all_states: list[PullRequestState] = []
    errors: list[str] = []
    for cand_branch in _candidate_branches_for_worktree(repo_root, info):
        states, err = _query_pr_states(repo_root, cand_branch)
        if err:
            errors.append(err)
        all_states.extend(states)

    review_number = _worktree_review_pr_number(repo_root, info)
    if review_number is not None:
        review_states, review_err = _query_pr_by_number(repo_root, review_number)
        if review_err and not _is_not_a_pull_request_error(review_err):
            errors.append(review_err)
        all_states.extend(review_states)

    # Follow-up CI branches carry a different branch name than the PR head they
    # fix. Find the MERGED PR that introduced the worktree HEAD by SHA, but only
    # when that commit is not already on origin/main -- otherwise a fresh branch
    # sitting on a merged main tip would be mistaken for a squash-merged
    # follow-up commit.
    commit_prs: list[PullRequestState] = []
    if info.head and not _is_ancestor_of_origin_main(info.path):
        commit_prs, sha_error = _query_prs_by_head_sha(repo_root, info.head)
        if sha_error:
            errors.append(sha_error)
        all_states.extend(commit_prs)
    return all_states, commit_prs, review_number, errors


def _current_open_pr_heads(
    repo_root: Path,
    pr_states: list[PullRequestState],
    commit_prs: list[PullRequestState],
) -> tuple[dict[int, str], str | None]:
    """Current head of every open PR that names this checkout, or an error.

    A commit-search hit carries the queried commit as its head, so the real
    head is read by number. An unreadable head is an error, never a guess.
    """
    heads: dict[int, str] = {}
    for state in pr_states:
        if state.state != "OPEN" or state.number is None:
            continue
        if any(state is hit for hit in commit_prs):
            fresh, error = _query_pr_by_number(repo_root, state.number)
            fresh_open = next((pr for pr in fresh if pr.number == state.number), None)
            if error is not None or fresh_open is None or not fresh_open.head_sha:
                return {}, f"PR #{state.number} head unavailable: {error or 'no head'}"
            if fresh_open.state == "OPEN":
                heads[state.number] = fresh_open.head_sha
        elif state.head_sha:
            heads[state.number] = state.head_sha
        else:
            return {}, f"PR #{state.number} head unavailable"
    return heads, None


def _review_checkout_reason(
    *,
    repo_root: Path,
    info: WorktreeInfo,
    pr_states: list[PullRequestState],
    commit_prs: list[PullRequestState],
    review_number: int | None,
    active_ids: set[str] | None,
    now: float | None,
    attention: list[str] | None = None,
    timeout: float | None = None,
) -> str | None:
    """Reap classes for a detached review checkout the task-bound classes miss.

    * superseded PR checkout: HEAD is a commit of an open PR, but no longer
      that PR's head. A checkout AT an open PR's current head is kept.
    * unrecorded detached checkout: no task record and older than two hours.
    """
    if not _review_checkout_gate(
        repo_root=repo_root,
        info=info,
        active_ids=active_ids,
        attention=attention,
        require_detached=True,
        timeout=timeout,
    ):
        return None
    heads, head_error = _current_open_pr_heads(repo_root, pr_states, commit_prs)
    if head_error is not None:
        return None
    if info.head in heads.values():
        return None

    related = {pr.number for pr in commit_prs if pr.number is not None}
    if review_number is not None:
        related.add(review_number)
    superseded = sorted(related & heads.keys())
    if superseded:
        number = superseded[0]
        return f"{_SUPERSEDED_PR_REASON_PREFIX}{number} head {info.head[:12]} (current {heads[number][:12]})"

    task_id = _dispatch_task_id(repo_root, info)
    if _task_record_status(repo_root, task_id) is None:
        mtime = latest_workspace_mtime(info.path)
        if mtime is not None:
            age_hours = ((time.time() if now is None else now) - mtime) / 3600
            if age_hours > _UNRECORDED_DETACHED_MIN_AGE_HOURS:
                return _UNRECORDED_DETACHED_REASON
    return None


def _foreign_checkout_reason(
    *,
    repo_root: Path,
    info: WorktreeInfo,
    active_ids: set[str] | None,
    attention: list[str] | None = None,
    timeout: float | None = None,
) -> str | None:
    """A registered scratch checkout outside ``.worktrees/`` under the same proof."""
    if not _review_checkout_gate(
        repo_root=repo_root,
        info=info,
        active_ids=active_ids,
        attention=attention,
        require_detached=False,
        timeout=timeout,
    ):
        return None
    activity = _open_file_activity_reason(info.path, timeout=timeout)
    if activity is not None:
        if attention is not None:
            attention.append(activity)
        return None
    return _FOREIGN_CHECKOUT_REASON


def _is_review_checkout_reason(reason: str) -> bool:
    return reason.startswith(_SUPERSEDED_PR_REASON_PREFIX) or reason in {
        _UNRECORDED_DETACHED_REASON,
        _FOREIGN_CHECKOUT_REASON,
    }


def _review_checkout_class(reason: str) -> str:
    if reason.startswith(_SUPERSEDED_PR_REASON_PREFIX):
        return "superseded"
    return "foreign" if reason == _FOREIGN_CHECKOUT_REASON else "unrecorded"


def _review_checkout_recheck(
    repo_root: Path,
    info: WorktreeInfo,
    reason: str,
    now: float | None = None,
) -> str | None:
    """Re-prove a review-checkout class under delegate's lock; a skip reason or ``None``.

    The class is derived again from fresh state, not carried over from
    qualification: the tree residue, the remote containment, the PR heads
    (re-read; an unreadable or now-equal head keeps the checkout), the age and
    task-record test, and detached HEAD for the detached classes.
    """
    try:
        worktrees = list_git_worktrees(repo_root)
    except RuntimeError as exc:
        return f"worktree list unavailable during cleanup ({exc})"
    fresh = next((wt for wt in worktrees if wt.path.resolve() == info.path.resolve()), None)
    if fresh is None:
        return "worktree unregistered during cleanup"
    current_active_ids, probe_error = _resolve_activity_probe(repo_root, fresh, _read_active_task_probe())
    if current_active_ids is None:
        return f"{probe_error or 'active-task probe unavailable'} during cleanup"
    current_live_cwds = _live_cwd_paths(repo_root)
    if current_live_cwds is None:
        return "process-CWD activity probe unavailable during cleanup"
    activity = _activity_reason(
        repo_root=repo_root,
        info=fresh,
        active_ids=current_active_ids,
        live_cwds=current_live_cwds,
        check_pending=False,
    )
    if activity is not None:
        return activity
    klass = _review_checkout_class(reason)
    all_states, commit_prs, review_number, errors = _review_pr_context(repo_root, fresh)
    if errors:
        return f"PR guard unavailable during cleanup; {'; '.join(errors)}"
    if klass == "foreign":
        attention: list[str] = []
        fresh_reason = _foreign_checkout_reason(
            repo_root=repo_root,
            info=fresh,
            active_ids=current_active_ids,
            attention=attention,
            timeout=_LOCKED_GIT_STATUS_TIMEOUT_S,
        )
        if attention:
            return attention[0]
    else:
        fresh_reason = _review_checkout_reason(
            repo_root=repo_root,
            info=fresh,
            pr_states=all_states,
            commit_prs=commit_prs,
            review_number=review_number,
            active_ids=current_active_ids,
            now=now,
            timeout=_LOCKED_GIT_STATUS_TIMEOUT_S,
        )
    if fresh_reason is None or _review_checkout_class(fresh_reason) != klass:
        return "review checkout proof changed during cleanup"
    return None


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
    attention: list[str] | None = None,
) -> str | None:
    """``pr_unknown`` marks the PR state as UNREADABLE rather than absent.

    A failed branch query must not read as "no PR": every reason below that
    consults ``pr_state`` -- directly, or via a ``pr_state is None`` shortcut
    that means "no open PR" -- becomes unsafe, because an OPEN PR may exist
    and simply not be visible. Class B stays available: it never consults
    ``pr_state`` and already requires the head to be an ancestor of
    origin/main or reachable from a remote, so nothing can be lost.
    """
    if not pr_unknown and (pr_state is None or pr_state.state != "OPEN"):
        try:
            abandoned = _terminal_abandon_matches(repo_root, info.path)
            if abandoned is not None:
                # Owner abandonment can discard unmerged work. Neither the
                # scheduled merged-only default nor safe-only opts into it.
                if merged_pr_only or safe_only:
                    raise ValueError("terminal-abandon requires merged_pr_only=False and safe_only=False")
                if not isinstance(active_ids, set) or any(
                    member.get("task_id") in active_ids for _, member in abandoned
                ):
                    raise ValueError("terminal-abandon live task probe unavailable or active")
                return "terminal-abandon.v1 verified owner ABANDON and preservation"
        except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError) as exc:
            if attention is not None:
                attention.append(f"terminal-abandon refused: {exc}")
            return None
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
            if include_terminal_dispatches and _merged_equivalent(info, pr_state):
                return f"{pr_label} MERGED; patch-equivalent"
            # A squash merge may leave a divergent local tip. Prove every
            # patch is upstream before allowing cleanup of a deleted branch.
            if info.branch is not None and not _origin_branch_present(info.path, info.branch):
                proved, detail = _merged_origin_gone_proof(info, pr_state)
                if proved:
                    return f"{pr_label} MERGED; origin branch gone"
                if attention is not None:
                    attention.append(detail)
                return None
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
        if info.branch.startswith("build/") and not pr_unknown and (pr_state is None or pr_state.state != "OPEN"):
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

    if not merged_pr_only and not include_terminal_dispatches and is_under_wt and info.detached and clean is True:
        has_matching_task = False
        task_settled = False
        if is_dispatch_candidate:
            task_file = control_plane_root(repo_root) / "batch_state" / "tasks" / f"{task_id}.json"
            if task_file.exists():
                has_matching_task = True
                try:
                    task_data = json.loads(task_file.read_text(encoding="utf-8"))
                    task_status = task_data.get("status")
                    if task_status in ("done", "failed", "no_deliverable") and (
                        active_ids is not None and task_id not in active_ids
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
    if is_dispatch_candidate and clean is True and (include_terminal_dispatches or not merged_pr_only):
        terminal_reason = _terminal_dispatch_reason(
            repo_root=repo_root,
            info=info,
            active_ids=active_ids,
        )
        if terminal_reason is not None and not pr_unknown and (pr_state is None or pr_state.state != "OPEN"):
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


def _worktree_git_dir(path: Path) -> Path | None:
    """Return the git admin directory for ``path``, without invoking git."""
    pointer = path / ".git"
    try:
        if pointer.is_file():
            line = pointer.read_text(encoding="utf-8").splitlines()[0]
            prefix = "gitdir:"
            if not line.startswith(prefix):
                return None
            git_dir = Path(line[len(prefix) :].strip())
            if not git_dir.is_absolute():
                git_dir = path / git_dir
            return git_dir
        if pointer.is_dir():
            return pointer
    except OSError:
        return None
    return None


def _process_holds_file(path: Path) -> bool | None:
    """True when a live process has ``path`` open. ``None`` if that cannot be told."""
    try:
        target = str(path.resolve())
    except OSError:
        return None
    proc_root = Path("/proc")
    if not proc_root.is_dir():
        return None
    try:
        entries = list(proc_root.iterdir())
    except OSError:
        return None
    saw_pid = False
    for entry in entries:
        if not entry.name.isdigit():
            continue
        try:
            fds = list((entry / "fd").iterdir())
        except OSError:
            continue
        saw_pid = True
        for fd in fds:
            try:
                linked = os.readlink(fd)
            except OSError:
                continue
            if linked == target or linked.startswith(f"{target} "):
                return True
    if not saw_pid:
        return None
    return False


def _stale_index_lock(path: Path) -> Path | None:
    """Return ``<admin>/index.lock`` when it is stale, else ``None``.

    Stale means the file is a regular file older than
    :data:`_STALE_INDEX_LOCK_MIN_AGE_S` and no live process has it open.
    Unknown liveness is not stale. This never deletes the lock.
    """
    git_dir = _worktree_git_dir(path)
    if git_dir is None:
        return None
    lock = git_dir / "index.lock"
    try:
        st = lock.stat()
    except OSError:
        return None
    if not stat.S_ISREG(st.st_mode):
        return None
    if time.time() - st.st_mtime < _STALE_INDEX_LOCK_MIN_AGE_S:
        return None
    held = _process_holds_file(lock)
    if held is not False:
        return None
    return lock


def _preserve_dirty_worktree(info: WorktreeInfo, *, timeout: float | None = None) -> str | None:
    branch = info.branch or "detached"
    add_proc = _run(["git", "add", "-A"], cwd=info.path, timeout=timeout)
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
        timeout=timeout,
    )
    if commit_proc.returncode != 0:
        return f"git commit failed: {_format_failure(commit_proc)}"
    return None


def _prune_branch(
    repo_root: Path,
    branch: str | None,
    force: bool = False,
    expected_head: str | None = None,
    timeout: float | None = None,
) -> str | None:
    if not branch:
        return None
    if expected_head is None:
        flag = "-D" if force else "-d"
        proc = _run(["git", "branch", flag, "--", branch], cwd=repo_root, timeout=timeout)
        return None if proc.returncode == 0 else _format_failure(proc)

    current = _run(
        ["git", "rev-parse", "--verify", f"refs/heads/{branch}"],
        cwd=repo_root,
        timeout=timeout,
    )
    if current.returncode != 0 or (current.stdout or "").strip() != expected_head:
        return "branch HEAD changed during cleanup"

    flag = "-D" if force else "-d"
    deleted = _run(["git", "branch", flag, "--", branch], cwd=repo_root, timeout=timeout)
    return None if deleted.returncode == 0 else _format_failure(deleted)


_ClaimIdentity = tuple[str, str, str, str, int]


def _pid_proven_absent(record: dict[str, Any]) -> bool:
    """Return True only when the record names a valid positive integer PID that no process holds.

    A missing, null, malformed, boolean, zero or negative PID proves nothing, and
    neither does a probe that fails for any reason other than "no such process".
    """
    pid = record.get("pid")
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        return False
    return worker_liveness(record) is False


def _needs_finalize_claim_identity(record: dict[str, Any]) -> _ClaimIdentity | None:
    """Bind a settled-claim proof to its task, branch, head, nonce and worker PID."""
    identity = (
        record.get("task_id"),
        record.get("worktree_branch"),
        record.get("final_branch_head_commit"),
        record.get("run_nonce"),
    )
    pid = record.get("pid")
    if all(isinstance(part, str) and part for part in identity) and type(pid) is int and pid > 0:
        return (*identity, pid)  # type: ignore[return-value]
    return None


def _needs_finalize_claim_proven_settled(repo_root: Path, record: dict[str, Any]) -> _ClaimIdentity | None:
    """Return the record's identity when its work is proven merged and its worker proven gone.

    The record's PID must be a valid positive integer that a probe proves absent,
    and its branch must have a MERGED PR whose head is exactly the head the task
    recorded on exit. Anything unknown (no task id, branch or recorded head, a
    bad PID, a failed PR lookup) returns ``None`` and keeps the claim. This runs
    a network lookup, so it must not run while the dispatch lock is held.
    """
    identity = _needs_finalize_claim_identity(record)
    if identity is None or not _pid_proven_absent(record):
        return None
    _, branch, head, _, _ = identity
    states, error = _query_pr_states(repo_root, branch)
    if error is None and any(state.state == "MERGED" and state.head_sha == head for state in states):
        return identity
    return None


def _released_reuse_claim_proven_settled(
    repo_root: Path, worktree: Path, record: dict[str, Any], *, tasks_dir: Path
) -> list[tuple[Path, dict[str, Any]]] | None:
    """Prove a released creator via its exact-head merged successor, outside the lock."""
    from scripts.fleet import ignored_task_output

    try:
        if record.get("status") != "needs_finalize" or _needs_finalize_claim_identity(record) is None:
            return None
        matches = ignored_task_output.matching_worktree_records(
            worktree, tasks_dir, repo_root=repo_root, publish_cache=False
        )
        cohort = ignored_task_output._current_reuse_records(matches, tasks_dir)
        _, creator = ignored_task_output.reused_worktree_creator(
            matches, worktree, repo_root=repo_root, tasks_dir=tasks_dir
        )
        if creator != record or any(member.get("keep_worktree") for _, member in matches):
            return None
        receipt = record["preserved_artifacts"]
        release = receipt["retention_release"]
        finalized = release["finalized_by"]
        if (
            receipt.get("retention_disposition") not in {"released", "retrieved"}
            or receipt.get("owner") != record["task_id"]
            or receipt.get("task_id") != record["task_id"]
            or receipt.get("run_nonce") != record["run_nonce"]
            or release.get("owner") != record["task_id"]
            or release.get("run_nonce") != record["run_nonce"]
            or not receipt.get("retrieval_proof_sha256")
            or release.get("retrieval_proof_sha256") != receipt["retrieval_proof_sha256"]
            or not all(_pid_proven_absent(member) for _, member in cohort)
        ):
            return None
        head = _run(["git", "rev-parse", "HEAD"], cwd=worktree)
        if head.returncode != 0 or head.stdout.strip() != finalized["head_sha"]:
            return None
        for _, successor in cohort:
            if (
                successor.get("worktree_reused") is True
                and successor.get("status") == "done"
                and successor.get("task_id") == finalized["task_id"]
                and successor.get("run_nonce") == finalized["run_nonce"]
                and successor.get("final_branch_head_commit") == finalized["head_sha"]
                and _needs_finalize_claim_proven_settled(repo_root, successor) is not None
            ):
                return matches
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError):
        pass
    return None


def _same_branch_merged_cohort(
    info: WorktreeInfo, pr: PullRequestState | None, cohort: list[tuple[Path, dict[str, Any]]]
) -> bool:
    """Settle inactive same-branch rounds without requiring a done successor."""
    if (
        not info.branch
        or not info.head
        or pr is None
        or pr.state != "MERGED"
        or pr.head_from_commit_search
        or not pr.head_sha
        or _worktree_clean(info.path) is not True
        or not _pr_matches_worktree_head(info, pr)
    ):
        return False
    branch = worktree_claims.checked_out_branch(info.path)
    tip = _run(["git", "rev-parse", "--verify", f"refs/heads/{info.branch}"], cwd=info.path)
    return bool(
        branch == info.branch
        and tip.returncode == 0
        and tip.stdout.strip() == info.head
        and len(cohort) >= 2
        and all(
            member.get("status") in _TERMINAL_DISPATCH_STATUSES
            and not member.get("keep_worktree")
            and member.get("lease_state") != "active"
            and not (isinstance(member.get("lease"), dict) and member["lease"].get("state") == "active")
            and member.get("worktree_branch") == info.branch
            and _needs_finalize_claim_identity(member) is not None
            and _pid_proven_absent(member)
            and _sha_is_ancestor(info.path, member["final_branch_head_commit"], info.head)
            for _, member in cohort
        )
    )


def _continuation_head_is_merged(
    info: WorktreeInfo,
    pr: PullRequestState | None,
    cohort: list[tuple[Path, dict[str, Any]]],
    *,
    allow_equivalent: bool = False,
) -> bool:
    """Prove an exact PR head, or a detached cohort's complete earlier lineage.

    Pending same-branch cohorts require a clean checkout at its branch tip,
    absent workers, and complete contained identities. Detached ancestry
    additionally requires a done successor at that checkout head. Missing
    Git objects and commit-search membership alone are never proof.
    """
    if pr is None or pr.state != "MERGED" or pr.head_from_commit_search or not pr.head_sha or not info.head:
        return False
    if allow_equivalent and not _pr_matches_worktree_head(info, pr) and _merged_equivalent(info, pr):
        return bool(cohort) and all(
            _needs_finalize_claim_identity(member) is not None
            and _sha_is_ancestor(info.path, member["final_branch_head_commit"], info.head)
            for _, member in cohort
        )
    if info.branch and any(
        member.get("worktree_reused") is True and member.get("status") == "needs_finalize" for _, member in cohort
    ):
        return _same_branch_merged_cohort(info, pr, cohort)
    if pr.head_sha == info.head:
        return True
    branch = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=info.path)
    return bool(
        info.detached
        and branch.returncode == 0
        and branch.stdout.strip() == "HEAD"
        and _worktree_clean(info.path) is True
        and _pr_matches_worktree_head(info, pr)
        and any(
            member.get("worktree_reused") is True
            and member.get("status") == "done"
            and member.get("final_branch_head_commit") == info.head
            for _, member in cohort
        )
        and all(
            _needs_finalize_claim_identity(member) is not None
            and _sha_is_ancestor(info.path, member["final_branch_head_commit"], info.head)
            for _, member in cohort
        )
    )


def _retention_release_present(matches: list[tuple[Path, dict[str, Any]]]) -> bool:
    """True when a record carries a release receipt, or its artifact field is unreadable."""
    for _, member in matches:
        artifacts = member.get("preserved_artifacts")
        if artifacts is None:
            continue
        if not isinstance(artifacts, dict) or artifacts.get("retention_release"):
            return True
    return False


def _switched_branch_structural_cohort(
    matches: list[tuple[Path, dict[str, Any]]],
    worktree: Path,
    *,
    repo_root: Path,
    tasks_dir: Path,
) -> tuple[Path, dict[str, Any]] | None:
    """One creator whose checkout moved off the recorded branch.

    Later rounds may still name the dispatch-time branch, or the round that
    switched may already name the checkout branch. A third branch name, a
    checkout that is still on the creator's branch, retention intent, or a
    successor that is not reused and terminal stays ambiguous.
    """
    from scripts.fleet import ignored_task_output

    cohort = ignored_task_output._current_reuse_records(matches, tasks_dir)
    creators = [item for item in cohort if ignored_task_output.record_created_worktree(item[1])]
    if any(
        isinstance(member.get("worktree_reap_proof"), dict)
        and member["worktree_reap_proof"].get("head_relation") == "patch-equivalent"
        for _, member in cohort
    ):
        # Preservation must consume and revalidate the patch proof, rather
        # than entering the older exact-head switched-branch path.
        return None
    if len(creators) != 1 or len(cohort) < 2:
        return None
    if any(member.get("keep_worktree") for _, member in matches) or _retention_release_present(matches):
        return None
    branch = worktree_claims.checked_out_branch(worktree)
    creator_branch = creators[0][1].get("worktree_branch")
    if (
        not isinstance(branch, str)
        or not branch
        or branch in {"HEAD", "main", "master"}
        or not isinstance(creator_branch, str)
        or not creator_branch
        or creator_branch == branch
    ):
        return None
    allowed_names = {creator_branch, branch}
    if any(member.get("worktree_branch") not in allowed_names for _, member in cohort):
        return None
    try:
        target = worktree.resolve(strict=True)
    except (OSError, RuntimeError):
        return None
    allowed_status = worktree_claims.RELEASED_TASK_STATUSES | {"needs_finalize"}
    for _, member in cohort:
        location = member.get("worktree_path") or member.get("cwd")
        if not isinstance(location, str):
            return None
        try:
            if worktree_claims.resolve_claim_path(location, repo_root=repo_root) != target:
                return None
        except (OSError, RuntimeError, ValueError):
            return None
        if member is creators[0][1]:
            continue
        status = member.get("status")
        if member.get("worktree_reused") is not True or not isinstance(status, str) or status not in allowed_status:
            return None
    return creators[0]


def _resolve_merged_reuse_creator(
    matches: list[tuple[Path, dict[str, Any]]],
    worktree: Path,
    *,
    repo_root: Path,
    tasks_dir: Path,
    merged_pr: PullRequestState | None = None,
) -> tuple[Path, dict[str, Any], bool]:
    """Return ``(path, creator, alternate)``.

    ``alternate`` is the switched-branch binding. Pending same-branch rounds
    additionally require the complete merged-cohort proof before removal.
    An exact MERGED source head may bind a cohort without one creator. Its
    first record holds the preservation receipt, without becoming a creator.
    """
    from scripts.fleet import ignored_task_output

    try:
        path, creator = ignored_task_output.reused_worktree_creator(
            matches, worktree, repo_root=repo_root, tasks_dir=tasks_dir
        )
    except ValueError:
        if merged_pr is not None and _checkout_pr_repository(worktree) is not None:
            cohort = ignored_task_output._current_reuse_records(matches, tasks_dir)
            creators = [item for item in cohort if ignored_task_output.record_created_worktree(item[1])]
            head = _run(["git", "rev-parse", "HEAD"], cwd=worktree)
            branch = worktree_claims.checked_out_branch(worktree)
            info = WorktreeInfo(worktree, branch, head.stdout.strip(), detached=branch is None)
            if (
                len(creators) != 1
                and len(cohort) >= 2
                and head.returncode == 0
                and branch
                and merged_pr.state == "MERGED"
                and not merged_pr.head_from_commit_search
                and merged_pr.head_sha == info.head
                and not any(member.get("keep_worktree") for _, member in matches)
                and not _retention_release_present(matches)
                and all(
                    member.get("worktree_branch") == branch
                    and member.get("status") in _TERMINAL_DISPATCH_STATUSES
                    and member.get("lease_state") != "active"
                    and not (isinstance(member.get("lease"), dict) and member["lease"].get("state") == "active")
                    and _pid_proven_absent(member)
                    and isinstance(member.get("worktree_path") or member.get("cwd"), str)
                    and worktree_claims.resolve_claim_path(
                        member.get("worktree_path") or member.get("cwd"), repo_root=repo_root
                    )
                    == worktree.resolve(strict=True)
                    for _, member in cohort
                )
            ):
                path, custodian = cohort[0]
                return path, custodian, False
            if (
                len(creators) == 1
                and len(cohort) >= 2
                and head.returncode == 0
                and not any(member.get("keep_worktree") for _, member in matches)
                and not _retention_release_present(matches)
                and not _pr_matches_worktree_head(info, merged_pr)
                and _merged_equivalent(info, merged_pr)
                and all(
                    member.get("status") in _TERMINAL_DISPATCH_STATUSES
                    and (member is creators[0][1] or member.get("worktree_reused") is True)
                    and member.get("lease_state") != "active"
                    and not (isinstance(member.get("lease"), dict) and member["lease"].get("state") == "active")
                    and _pid_proven_absent(member)
                    and _needs_finalize_claim_identity(member) is not None
                    and _sha_is_ancestor(worktree, member["final_branch_head_commit"], info.head)
                    for _, member in cohort
                )
            ):
                path, creator = creators[0]
                return path, creator, False
        structural = _switched_branch_structural_cohort(matches, worktree, repo_root=repo_root, tasks_dir=tasks_dir)
        if structural is not None:
            path, creator = structural
            return path, creator, True
        cohort = ignored_task_output._current_reuse_records(matches, tasks_dir)
        creators = [item for item in cohort if ignored_task_output.record_created_worktree(item[1])]
        branch = worktree_claims.checked_out_branch(worktree)
        if (
            len(creators) != 1
            or len(cohort) < 2
            or not branch
            or any(member.get("keep_worktree") for _, member in matches)
            or _retention_release_present(matches)
            or any(
                member.get("worktree_branch") != branch
                or member.get("status") not in _TERMINAL_DISPATCH_STATUSES
                or (member is not creators[0][1] and member.get("worktree_reused") is not True)
                or not isinstance(member.get("worktree_path") or member.get("cwd"), str)
                or worktree_claims.resolve_claim_path(
                    member.get("worktree_path") or member.get("cwd"), repo_root=repo_root
                )
                != worktree.resolve(strict=True)
                for _, member in cohort
            )
        ):
            raise
        path, creator = creators[0]
        return path, creator, False
    return path, creator, False


def _real_directory(path: Path) -> Path | None:
    """Absolute directory with no symlink and no ``.`` or ``..`` component."""
    try:
        if not path.is_absolute():
            return None
        if any(part in {"", ".", ".."} for part in path.parts):
            return None
        current = Path(path.anchor)
        for part in path.parts[1:]:
            current = current / part
            if current.is_symlink() or not current.is_dir():
                return None
        return current
    except OSError:
        return None


def _git_identity_output(cwd: Path, args: list[str]) -> bytes | None:
    """Raw Git stdout, with no text decoding or whitespace/path normalization."""
    try:
        proc = safe_git(
            args,
            cwd=cwd,
            profile="local",
            capture_output=True,
            text=False,
            check=False,
            timeout=_effective_timeout(None),
            env=sanitized_git_env(),
        )
    except (OSError, ValueError, UnicodeError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0 or not isinstance(proc.stdout, bytes) or not proc.stdout:
        return None
    return proc.stdout


def _proven_linked_worktree_primary(worktree: Path) -> Path | None:
    """A registered dispatch checkout, identified only by Git's raw output.

    The common directory names a tentative primary. Git run in that primary
    must list the primary first and this exact checkout once. The checkout
    stays within that primary's cleanup root; another repository's copied
    registration cannot claim a checkout under this repository.
    """
    checkout = _real_directory(worktree)
    if checkout is None:
        return None
    common = _git_identity_output(checkout, ["rev-parse", "--path-format=absolute", "--git-common-dir"])
    if common is None or not common.endswith(b"/.git\n") or common.count(b"\n") != 1:
        return None
    try:
        primary = Path(os.fsdecode(common[: -len(b"/.git\n")]))
        if _real_directory(primary / ".git") is None or common != os.fsencode(primary / ".git") + b"\n":
            return None
        checkout.relative_to(primary / ".worktrees")
    except (OSError, ValueError, UnicodeError):
        return None
    listed = _git_identity_output(primary, ["worktree", "list", "--porcelain"])
    if listed is None or not listed.endswith(b"\n\n"):
        return None
    records = listed[:-2].split(b"\n\n")
    pattern = (
        rb"worktree [^\n\0]+\nHEAD (?:[0-9a-f]{40}|[0-9a-f]{64})\n"
        rb"(?:branch refs/heads/[^\n\0]+|detached)"
        rb"(?:\n(?:locked|prunable)(?: [^\n\0]*)?)*"
    )
    if any(re.fullmatch(pattern, record) is None for record in records):
        return None
    registrations = [record.partition(b"\n")[0] for record in records]
    if not registrations or registrations[0] != b"worktree " + os.fsencode(primary):
        return None
    if registrations.count(b"worktree " + os.fsencode(checkout)) != 1:
        return None
    return primary


def _configured_origin_url(repo: Path) -> bytes | None:
    """Exactly one raw origin value from Git config, including its terminator."""
    raw = _git_identity_output(repo, ["config", "--get", "remote.origin.url"])
    if raw is None or not raw.endswith(b"\n") or raw.count(b"\n") != 1 or b"\0" in raw:
        return None
    return raw


def _checkout_pr_repository(worktree: Path) -> Path | None:
    """Git-proven primary with the checkout's identical raw origin, or None.

    Identity failure precedes any pull-request query or removal authorization.
    """
    try:
        root = _proven_linked_worktree_primary(worktree)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    if root is None or _github_owner_repo(root) is None:
        return None
    origin = _configured_origin_url(worktree)
    if origin is None or origin != _configured_origin_url(root):
        return None
    return root


def _switched_branch_merge_proven(
    _repo_root: Path,
    worktree: Path,
    cohort: list[tuple[Path, dict[str, Any]]],
    *,
    expected_head: str | None = None,
) -> bool:
    """Exact merged head of the checkout branch, with every recorded commit contained.

    The pull request is read from the repository that owns ``worktree``.
    ``_repo_root`` is the caller's task-record root and may be the public
    control plane; it is not the pull-request repository. An owning
    repository that cannot be resolved is not proven.

    A ``done`` or ``needs_finalize`` successor must have recorded that head.
    ``needs_finalize`` is the status a switched round keeps while its record
    still names the dispatch-time branch. Unknown git objects, a dirty tree,
    a live or unknown process, and any commit that is not an ancestor retain.
    """
    from scripts.fleet import ignored_task_output

    # Prove Git identity before querying a pull request or authorizing deletion.
    pr_repo = _checkout_pr_repository(worktree)
    if pr_repo is None:
        return False
    if not cohort or not all(_pid_proven_absent(member) for _, member in cohort):
        return False
    if _worktree_clean(worktree) is not True:
        return False
    branch = worktree_claims.checked_out_branch(worktree)
    creators = [item for item in cohort if ignored_task_output.record_created_worktree(item[1])]
    if len(creators) != 1 or not isinstance(branch, str) or not branch:
        return False
    creator_branch = creators[0][1].get("worktree_branch")
    if not isinstance(creator_branch, str) or creator_branch == branch:
        return False
    allowed_names = {creator_branch, branch}
    if any(member.get("worktree_branch") not in allowed_names for _, member in cohort):
        return False
    head_proc = _run(["git", "rev-parse", "HEAD"], cwd=worktree)
    if head_proc.returncode != 0:
        return False
    head = head_proc.stdout.strip()
    if not head or (expected_head is not None and head != expected_head):
        return False
    proving = False
    for _, member in cohort:
        if _needs_finalize_claim_identity(member) is None:
            return False
        commit = member.get("final_branch_head_commit")
        if not isinstance(commit, str) or not _sha_is_ancestor(worktree, commit, head):
            return False
        if (
            member.get("worktree_reused") is True
            and member.get("status") in {"done", "needs_finalize"}
            and commit == head
        ):
            proving = True
    if not proving:
        return False
    states, error = _query_pr_states(pr_repo, branch)
    if error is not None:
        return False
    pr = _best_pr(states)
    return bool(pr is not None and pr.state == "MERGED" and not pr.head_from_commit_search and pr.head_sha == head)


def _record_in_cohort(record: dict[str, Any], cohort: list[tuple[Path, dict[str, Any]]]) -> bool:
    return any(
        member.get("task_id") == record.get("task_id") and member.get("run_nonce") == record.get("run_nonce")
        for _, member in cohort
    )


def switched_branch_member_proven(repo_root: Path, worktree: Path, record: dict[str, Any], *, tasks_dir: Path) -> bool:
    """True when ``record`` is a member of a switched-branch cohort with a merged exact head."""
    return _merged_reuse_claim_proven_settled(repo_root, worktree, record, tasks_dir=tasks_dir) is not None


def _preservation_merged_creator(
    matches: list[tuple[Path, dict[str, Any]]], worktree: Path, *, repo_root: Path, tasks_dir: Path
) -> tuple[Path, dict[str, Any]]:
    """Consume the reaper's proof using current identities and local Git under its lock."""
    from scripts.fleet import ignored_task_output as output

    cohort = output._current_reuse_records(matches, tasks_dir)
    creators = [item for item in cohort if output.record_created_worktree(item[1])]
    if not cohort:
        raise ValueError("merged continuation preservation owner unavailable")
    holder = creators[0] if len(creators) == 1 else cohort[0]
    proof = holder[1].get("worktree_reap_proof")
    proof_pr = (
        PullRequestState(proof.get("pr_number"), proof.get("pr_state"), proof.get("pr_head_sha"))
        if isinstance(proof, dict)
        else None
    )
    path, creator, alternate = _resolve_merged_reuse_creator(
        matches, worktree, repo_root=repo_root, tasks_dir=tasks_dir, merged_pr=proof_pr
    )
    cohort = output._current_reuse_records(matches, tasks_dir)
    if alternate or not isinstance(proof, dict) or proof.get("schema") != "merged-reuse-reap.v1":
        raise ValueError("merged continuation preservation proof unavailable")
    head = _run(["git", "rev-parse", "HEAD"], cwd=worktree)
    branch = worktree_claims.checked_out_branch(worktree)
    info = WorktreeInfo(worktree, branch, proof.get("head_sha"), detached=branch is None)
    pr = PullRequestState(proof.get("pr_number"), proof.get("pr_state"), proof.get("pr_head_sha"))
    if (
        proof.get("owner") != creator.get("task_id")
        or proof.get("run_nonce") != creator.get("run_nonce")
        or head.returncode != 0
        or head.stdout.strip() != info.head
        or proof.get("clean") is not True
        or _worktree_clean(worktree) is not True
        or proof.get("head_relation") != _merged_head_relation(info, pr)
        or any(member.get("keep_worktree") for _, member in matches)
        or _retention_release_present(matches)
        or not all(
            _pid_proven_absent(member)
            and member.get("status") in _TERMINAL_DISPATCH_STATUSES
            and member.get("lease_state") != "active"
            and not (isinstance(member.get("lease"), dict) and member["lease"].get("state") == "active")
            for _, member in cohort
        )
        or proof.get("members")
        != [
            {
                "task_id": member.get("task_id"),
                "run_nonce": member.get("run_nonce"),
                "branch": member.get("worktree_branch"),
                "head_sha": member.get("final_branch_head_commit"),
                "pid": member.get("pid"),
            }
            for _, member in cohort
        ]
        or not _continuation_head_is_merged(
            info, pr, cohort, allow_equivalent=proof.get("head_relation") == "patch-equivalent"
        )
    ):
        raise ValueError("merged continuation preservation proof changed")
    return path, creator


def _terminal_abandon_matches(repo_root: Path, worktree: Path) -> list[tuple[Path, dict[str, Any]]] | None:
    """An explicit record opts into the whole fail-closed abandon proof."""
    from scripts.fleet import ignored_task_output as output

    primary = control_plane_root(repo_root)
    tasks_dir = task_store_paths.tasks_dir()
    matches = output.matching_worktree_records(worktree, tasks_dir, repo_root=primary, publish_cache=False)
    if not any("worktree_abandon" in member for _, member in matches):
        return None
    output.terminal_abandon_creator(matches, worktree, primary=primary, tasks_dir=tasks_dir)
    return matches


def _merged_reuse_claim_proven_settled(
    repo_root: Path, worktree: Path, record: dict[str, Any], *, tasks_dir: Path
) -> list[tuple[Path, dict[str, Any]]] | None:
    """Settle a keep-false creator via a successor contained in a merged PR.

    This is merge evidence, not retention release. Existing release receipts
    continue through their original verifier; ignored bytes still pass the
    mandatory preservation gate before removal. A checkout that moved onto a
    new branch is settled from that branch's merged head, including a
    ``needs_finalize`` successor whose recorded commit is that head.
    """
    from scripts.fleet import ignored_task_output

    try:
        if record.get("status") != "needs_finalize" or _needs_finalize_claim_identity(record) is None:
            return None
        matches = ignored_task_output.matching_worktree_records(
            worktree, tasks_dir, repo_root=repo_root, publish_cache=False
        )
        cohort = ignored_task_output._current_reuse_records(matches, tasks_dir)
        if (
            len(cohort) < 2
            or any(member.get("keep_worktree") for _, member in matches)
            or _retention_release_present(matches)
            or not all(_pid_proven_absent(member) for _, member in cohort)
            or not _record_in_cohort(record, cohort)
        ):
            return None
        try:
            _, creator, alternate = _resolve_merged_reuse_creator(
                matches, worktree, repo_root=repo_root, tasks_dir=tasks_dir
            )
        except ValueError:
            branch = worktree_claims.checked_out_branch(worktree)
            pr_repo = _checkout_pr_repository(worktree)
            if pr_repo is None:
                return None
            states, error = _query_pr_states(pr_repo, branch) if branch else ([], None)
            if error is not None:
                return None
            _, creator, alternate = _resolve_merged_reuse_creator(
                matches, worktree, repo_root=repo_root, tasks_dir=tasks_dir, merged_pr=_best_pr(states)
            )
        if alternate:
            if _switched_branch_merge_proven(repo_root, worktree, cohort):
                return matches
            branch = worktree_claims.checked_out_branch(worktree)
            pr_repo = _checkout_pr_repository(worktree)
            if pr_repo is None:
                return None
            states, error = _query_pr_states(pr_repo, branch) if branch else ([], None)
            if error is not None:
                return None
            _, creator, alternate = _resolve_merged_reuse_creator(
                matches, worktree, repo_root=repo_root, tasks_dir=tasks_dir, merged_pr=_best_pr(states)
            )
            if alternate:
                return None
        head = _run(["git", "rev-parse", "HEAD"], cwd=worktree)
        if head.returncode != 0:
            return None
        branch = worktree_claims.checked_out_branch(worktree)
        info = WorktreeInfo(worktree, branch, head.stdout.strip(), detached=branch is None)
        if branch is not None:
            states, error = _query_pr_states(repo_root, branch)
            if error is None and (
                _same_branch_merged_cohort(info, _best_pr(states), cohort)
                or (
                    _merged_equivalent(info, _best_pr(states))
                    and _continuation_head_is_merged(info, _best_pr(states), cohort, allow_equivalent=True)
                )
            ):
                return matches
        if creator != record:
            return None
        for _, successor in cohort:
            if (
                successor.get("worktree_reused") is True
                and successor.get("status") == "done"
                and successor.get("final_branch_head_commit") == head.stdout.strip()
                and _needs_finalize_claim_identity(successor) is not None
            ):
                states, error = _query_pr_states(repo_root, successor["worktree_branch"])
                pr = _best_pr(states)
                if error is None and _continuation_head_is_merged(info, pr, cohort):
                    return matches
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError, AttributeError):
        pass
    return None


def _record_merged_reuse_proof(
    repo_root: Path,
    info: WorktreeInfo,
    pr: PullRequestState | None,
    *,
    tasks_dir: Path,
    allow_equivalent: bool = False,
) -> dict[str, Any] | None:
    """Record merged-head containment proof under the caller's worktree lock.

    Task locks follow the worktree lock. The complete cohort is re-read before
    publishing; preservation still handles all ignored output independently.
    """
    from scripts.fleet import ignored_task_output
    from scripts.orchestration.task_record_store import task_record_path

    matches = ignored_task_output.matching_worktree_records(
        info.path, tasks_dir, repo_root=repo_root, publish_cache=False
    )
    cohort = ignored_task_output._current_reuse_records(matches, tasks_dir)
    if len(cohort) < 2 or any(member.get("keep_worktree") for _, member in matches):
        return None
    path, creator, alternate = _resolve_merged_reuse_creator(
        matches, info.path, repo_root=repo_root, tasks_dir=tasks_dir, merged_pr=pr
    )
    if alternate:
        proven_head = _switched_branch_merge_proven(repo_root, info.path, cohort, expected_head=info.head)
        real_pr = (
            pr is not None and pr.state == "MERGED" and not pr.head_from_commit_search and pr.head_sha == info.head
        )
        if not proven_head or not real_pr:
            if _retention_release_present(matches):
                return None  # Preserve #9940's explicit receipt-release path.
            raise ValueError("continuation requires a proven merged PR head containing the checkout")
    elif not _continuation_head_is_merged(info, pr, cohort, allow_equivalent=allow_equivalent):
        if _retention_release_present(matches):
            return None  # Preserve #9940's explicit receipt-release path.
        raise ValueError("continuation requires a proven merged PR head containing the checkout")
    assert pr is not None
    if any(
        not isinstance(member.get(key), str) or not member[key].strip()
        for _, member in matches
        for key in ("task_id", "run_nonce")
    ):
        raise ValueError("continuation run identity unavailable")
    if path not in (
        task_record_path(tasks_dir, creator["task_id"]),
        task_record_path(tasks_dir / "archive", creator["task_id"]),
    ):
        raise ValueError("continuation creator has no canonical task record")
    if not all(_pid_proven_absent(member) for _, member in cohort):
        raise ValueError("continuation process absence unavailable")
    proof = {
        "schema": "merged-reuse-reap.v1",
        "owner": creator["task_id"],
        "run_nonce": creator["run_nonce"],
        "head_sha": info.head,
        "pr_head_sha": pr.head_sha,
        "head_relation": _merged_head_relation(info, pr),
        "pr_number": pr.number,
        "pr_state": pr.state,
        "clean": True,
        "members": [
            {
                "task_id": member["task_id"],
                "run_nonce": member["run_nonce"],
                "branch": member.get("worktree_branch"),
                "head_sha": member.get("final_branch_head_commit"),
                "pid": member["pid"],
            }
            for _, member in cohort
        ],
    }
    with contextlib.ExitStack() as stack:
        for member_path, member in sorted(matches):
            stack.enter_context(ignored_task_output.artifacts.task_state_lock(member_path))
            if json.loads(member_path.read_text(encoding="utf-8")) != member:
                raise ValueError("continuation records changed before merged-head proof")
        if (
            ignored_task_output.matching_worktree_records(
                info.path, tasks_dir, repo_root=repo_root, publish_cache=False
            )
            != matches
        ):
            raise ValueError("continuation cohort changed before merged-head proof")
        if not all(_pid_proven_absent(member) for _, member in cohort):
            raise ValueError("continuation process absence changed before merged-head proof")
        head = _run(["git", "rev-parse", "HEAD"], cwd=info.path)
        if head.returncode != 0 or head.stdout.strip() != info.head or _worktree_clean(info.path) is not True:
            raise ValueError("checkout changed before merged-head proof")
        rebound_path, rebound_creator, rebound_alternate = _resolve_merged_reuse_creator(
            matches, info.path, repo_root=repo_root, tasks_dir=tasks_dir, merged_pr=pr
        )
        if rebound_path != path or rebound_creator != creator or rebound_alternate != alternate:
            raise ValueError("continuation records changed before merged-head proof")
        if alternate:
            if not _switched_branch_merge_proven(repo_root, info.path, cohort, expected_head=info.head):
                raise ValueError("continuation ancestry changed before merged-head proof")
        elif not _continuation_head_is_merged(info, pr, cohort, allow_equivalent=allow_equivalent):
            raise ValueError("continuation ancestry changed before merged-head proof")
        reaper_lifecycle._atomic_write(path, dict(creator, worktree_reap_proof=proof))
    return proof


def _enter_dispatch_worktree_guard(
    stack: contextlib.ExitStack,
    *,
    repo_root: Path,
    info: WorktreeInfo,
) -> str | None:
    """Take delegate's per-worktree lock and refuse another task's live claim (#8610).

    Dispatch holds the same lock from before it touches a checkout until it
    publishes the task record that names it, so while ``stack`` holds the lock
    no attachment can land and every earlier one is visible to the claim
    scan. The owner task derived from a dispatch path is exempt: the
    qualifying class already decided its record. Any other task record with
    an unfinished status that names the checkout refuses removal. Returns a
    skip reason, or ``None`` with the lock held until ``stack`` closes.

    Records and locks are read from :func:`control_plane_root`: for a
    ``--repo`` sibling repository that is the public primary, where dispatch
    writes them (#8624).
    """
    primary = primary_checkout_root(repo_root)
    try:
        control_root = worktree_claims.control_plane_root(primary)
        lock_dir = _common_git_dir(control_root, timeout=_LOCKED_GIT_TIMEOUT_S) / worktree_claims.LOCK_DIR_NAME
    except worktree_claims.ControlPlaneError as exc:
        return f"{worktree_claims.LOCK_UNAVAILABLE} ({exc})"
    except RuntimeError as exc:
        return f"worktree lock unavailable ({exc})"
    tasks_dir = control_root / "batch_state" / "tasks"
    owner_task_id = _dispatch_task_id(repo_root, info)
    claim_scan = {
        "tasks_dir": tasks_dir,
        "repo_root": primary,
        "owner_task_id": owner_task_id,
        "owner_state_file": tasks_dir / f"{owner_task_id}.json" if owner_task_id else None,
    }
    owner_record = _task_record(repo_root, owner_task_id) if owner_task_id else None
    owner_attempt = None
    owner_needs_merge_proof = False
    if owner_record is not None and owner_record.get("status") == "needs_finalize":
        nonce = owner_record.get("run_nonce")
        if not isinstance(nonce, str) or not nonce or not _pid_proven_absent(owner_record):
            return f"needs_finalize owner {owner_task_id} attempt unknown; retain until nonce and absent PID are proven"
        owner_attempt = (nonce, owner_record.get("pid"))
        # Single-record owners retain main's guard. Only continuation cohorts
        # without #9940's receipt-based release need the extra merge proof.
        from scripts.fleet import ignored_task_output

        try:
            members = ignored_task_output.matching_worktree_records(
                info.path, tasks_dir, repo_root=primary, publish_cache=False
            )
            owner_needs_merge_proof = len(
                ignored_task_output._current_reuse_records(members, tasks_dir)
            ) >= 2 and not owner_record.get("preserved_artifacts", {}).get("retention_release")
        except (OSError, ValueError, RuntimeError):
            return f"needs_finalize owner {owner_task_id} cohort unavailable; retain until attribution is proven"

    # Prove every needs_finalize claim's merge before taking the lock: the PR lookup
    # is a network call that would otherwise hold delegate's dispatch lock.
    proven: set[_ClaimIdentity] = set()
    reused_proofs: dict[_ClaimIdentity, list[tuple[Path, dict[str, Any]]]] = {}
    merged_reuse_proofs: dict[_ClaimIdentity, list[tuple[Path, dict[str, Any]]]] = {}
    abandon_proofs: list[list[tuple[Path, dict[str, Any]]]] = []

    def prove(record: dict[str, Any]) -> bool:
        try:
            abandoned = _terminal_abandon_matches(primary, info.path)
            if abandoned is not None and any(member == record for _, member in abandoned):
                active = _read_active_task_probe()
                if not isinstance(active, set) or any(member.get("task_id") in active for _, member in abandoned):
                    return False
                abandon_proofs.append(abandoned)
                return True
        except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError):
            return False
        merged_reuse = _merged_reuse_claim_proven_settled(primary, info.path, record, tasks_dir=tasks_dir)
        if merged_reuse is not None:
            identity = _needs_finalize_claim_identity(record)
            if identity is not None:
                merged_reuse_proofs[identity] = merged_reuse
                return True
        reuse = _released_reuse_claim_proven_settled(primary, info.path, record, tasks_dir=tasks_dir)
        if reuse is not None:
            identity = _needs_finalize_claim_identity(record)
            if identity is not None:
                reused_proofs[identity] = reuse
                return True
        identity = _needs_finalize_claim_proven_settled(primary, record)
        if identity is not None:
            proven.add(identity)
        return identity is not None

    worktree_claims.active_worktree_claim_refusal(info.path, settled_claim=prove, **claim_scan)
    if owner_needs_merge_proof and not prove(owner_record):
        return f"active task {owner_task_id} needs_finalize merge proof unavailable"

    try:
        stack.enter_context(worktree_claims.worktree_lock(info.path, lock_dir=lock_dir))
    except worktree_claims.WorktreeLockError as exc:
        return f"{worktree_claims.lock_refusal(exc)} ({exc})"
    except RuntimeError as exc:
        return f"worktree lock unavailable ({exc})"

    def still_settled(record: dict[str, Any]) -> bool:
        # Under the lock: no network. The record must still be the one proven.
        if any(any(member == record for _, member in matches) for matches in abandon_proofs):
            try:
                current = _terminal_abandon_matches(primary, info.path)
                return current in abandon_proofs
            except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError):
                return False
        identity = _needs_finalize_claim_identity(record)
        if identity in merged_reuse_proofs:
            from scripts.fleet import ignored_task_output

            try:
                current = ignored_task_output.matching_worktree_records(
                    info.path, tasks_dir, repo_root=primary, publish_cache=False
                )
                head = _run(["git", "rev-parse", "HEAD"], cwd=info.path)
                return bool(
                    current == merged_reuse_proofs[identity]
                    and head.returncode == 0
                    and head.stdout.strip() == info.head
                    and all(
                        _pid_proven_absent(member)
                        for _, member in ignored_task_output._current_reuse_records(current, tasks_dir)
                    )
                )
            except (OSError, ValueError, RuntimeError):
                return False
        if identity in reused_proofs:
            from scripts.fleet import ignored_task_output

            try:
                current = ignored_task_output.matching_worktree_records(
                    info.path, tasks_dir, repo_root=primary, publish_cache=False
                )
                head = _run(["git", "rev-parse", "HEAD"], cwd=info.path)
                finalized = record["preserved_artifacts"]["retention_release"]["finalized_by"]
                return bool(
                    current == reused_proofs[identity]
                    and head.returncode == 0
                    and head.stdout.strip() == finalized["head_sha"]
                    and all(
                        _pid_proven_absent(member)
                        for _, member in ignored_task_output._current_reuse_records(current, tasks_dir)
                    )
                )
            except (OSError, ValueError, KeyError, TypeError, RuntimeError):
                return False
        return identity is not None and identity in proven and _pid_proven_absent(record)

    if owner_attempt is not None:
        current_owner = _task_record(repo_root, owner_task_id)
        if (
            current_owner is None
            or (current_owner.get("run_nonce"), current_owner.get("pid")) != owner_attempt
            or not _pid_proven_absent(current_owner)
            or (owner_needs_merge_proof and not still_settled(current_owner))
        ):
            return f"needs_finalize owner {owner_task_id} attempt changed; retain until current attempt is qualified"
    return worktree_claims.active_worktree_claim_refusal(info.path, settled_claim=still_settled, **claim_scan)


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
    fallback_probe: _ActiveTaskProbeFailure | None = None,
    eligible_backlog: int | None = None,
    now: float | None = None,
) -> ReapResult:
    expected_head = info.head
    abandoning = reason.startswith("terminal-abandon.v1 ")
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
        from scripts.fleet import ignored_task_output

        try:
            control_root = control_plane_root(repo_root)
            matches = ignored_task_output.matching_worktree_records(
                info.path, task_store_paths.tasks_dir(), repo_root=control_root, publish_cache=False
            )
            cohort = ignored_task_output._current_reuse_records(matches, task_store_paths.tasks_dir())
            if abandoning:
                if _terminal_abandon_matches(repo_root, info.path) is None:
                    raise ValueError("terminal-abandon proof disappeared")
            elif len(cohort) > 1:
                _creator_path, _creator, alternate = _resolve_merged_reuse_creator(
                    matches,
                    info.path,
                    repo_root=control_root,
                    tasks_dir=task_store_paths.tasks_dir(),
                    merged_pr=pr_state,
                )
                if any(member.get("keep_worktree") for _, member in matches):
                    raise ValueError("keep_worktree intent set; retrieval and owner release required")
                if not all(_pid_proven_absent(member) for _, member in cohort):
                    raise ValueError("continuation process absence unavailable")
                if alternate:
                    real_pr = (
                        pr_state is not None
                        and pr_state.state == "MERGED"
                        and not pr_state.head_from_commit_search
                        and pr_state.head_sha == info.head
                    )
                    if not real_pr or not _switched_branch_merge_proven(
                        repo_root, info.path, cohort, expected_head=info.head
                    ):
                        raise ValueError("continuation requires a proven merged PR head containing the checkout")
                else:
                    released = _retention_release_present(matches)
                    if not released and not _continuation_head_is_merged(
                        info, pr_state, cohort, allow_equivalent=reason.endswith("MERGED; patch-equivalent")
                    ):
                        raise ValueError("continuation requires a proven merged PR head containing the checkout")
        except (OSError, ValueError, RuntimeError) as exc:
            return ReapResult(
                path=str(info.path),
                branch=info.branch,
                action="skipped",
                reason=f"continuation ownership or retention refused: {exc}",
                dirty=dirty,
                pr=_pr_dict(pr_state),
            )
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
    dispatch_guard = contextlib.ExitStack()
    try:
        # Search only establishes commit membership, not the actual PR head.
        # Refresh by number before acquiring the dispatch/worktree lock.
        if pr_state is not None and pr_state.head_from_commit_search:
            from scripts.fleet import ignored_task_output

            tasks_dir = task_store_paths.tasks_dir()
            matches = ignored_task_output.matching_worktree_records(
                info.path, tasks_dir, repo_root=control_plane_root(repo_root), publish_cache=False
            )
            cohort = ignored_task_output._current_reuse_records(matches, tasks_dir)
        else:
            cohort = []
        if len(cohort) >= 2:
            states, error = _query_pr_by_number(repo_root, pr_state.number) if pr_state.number else ([], None)
            fresh = next((state for state in states if state.number == pr_state.number), None)
            if error is not None or fresh is None or fresh.head_from_commit_search:
                return ReapResult(
                    path=str(info.path),
                    branch=info.branch,
                    action="skipped",
                    reason="commit-search PR head unavailable",
                    dirty=dirty,
                    pr=_pr_dict(pr_state),
                )
            pr_state = fresh
        # This reservation is intentionally before the final TOCTOU checks.
        # Scheduler/delegate consumers can reject a new bind while it exists.
        if not reaper_lifecycle.mark_reap_pending(
            repo_root,
            worktree_path=info.path,
            branch=info.branch,
            head=expected_head,
            task_id=_dispatch_task_id(repo_root, info),
        ):
            return ReapResult(
                path=str(info.path),
                branch=info.branch,
                action="skipped",
                reason="active reap reservation",
                dirty=dirty,
                pr=_pr_dict(pr_state),
            )
        pending_marked = True

        # Network proofs before the per-worktree lock. ``ls-remote``, ``gh``,
        # and ``_merged_origin_gone_proof`` are not part of the locked-region
        # deadline. Under the lock the same facts are re-checked with local
        # git only (remote-tracking ref, the snapshot just taken).
        origin_gone: tuple[bool, str] | None = None
        if reason.endswith("MERGED; origin branch gone") and pr_state is not None:
            origin_gone = _merged_origin_gone_proof(info, pr_state)
        live_origin: bool | None = None
        pr_snapshot: tuple[list[PullRequestState], str | None] | None = None
        if reason.startswith("dispatch HEAD ancestor of origin/main"):
            live_origin = _live_origin_heads_present(info.path, info.branch)
        if info.branch is not None and (
            require_terminal_dispatch_guards or reason.startswith("dispatch HEAD ancestor of origin/main")
        ):
            pr_snapshot = _query_pr_states(repo_root, info.branch)

        guard_refusal = _enter_dispatch_worktree_guard(dispatch_guard, repo_root=repo_root, info=info)
        if guard_refusal is not None:
            return ReapResult(
                path=str(info.path),
                branch=info.branch,
                action="skipped",
                reason=f"{guard_refusal}; originally qualified because {reason}",
                dirty=dirty,
                pr=_pr_dict(pr_state),
            )

        if fallback_probe is not None:
            # Re-read bound terminal state and PID under the attachment lock,
            # including merged-PR classes that do not re-probe Monitor below.
            current_ids, probe_error = _resolve_activity_probe(repo_root, info, fallback_probe)
            current_cwds = _live_cwd_paths(repo_root)
            refusal = probe_error or (
                "process-CWD activity probe unavailable during cleanup" if current_cwds is None else None
            )
            if refusal is None:
                refusal = _activity_reason(
                    repo_root=repo_root,
                    info=info,
                    active_ids=current_ids,
                    live_cwds=current_cwds,
                    check_pending=False,
                )
            if refusal is not None:
                return ReapResult(
                    path=str(info.path),
                    branch=info.branch,
                    action="skipped",
                    reason=refusal,
                    dirty=dirty,
                    pr=_pr_dict(pr_state),
                )

        # A settled worker's background jobs die with its worktree, never
        # after it into a deleted cwd (#8991); if they survive, it stays.
        leftover_refusal = _stop_task_background_jobs(repo_root, info.path)
        if leftover_refusal is not None:
            return ReapResult(
                path=str(info.path),
                branch=info.branch,
                action="skipped",
                reason=f"{leftover_refusal}; originally qualified because {reason}",
                dirty=dirty,
                pr=_pr_dict(pr_state),
            )

        # The block below holds delegate's per-worktree lock. Git inside
        # ``_bounded_locked_git`` is bounded: each call at most
        # ``_LOCKED_GIT_TIMEOUT_S`` (or the timeout it passes, such as the
        # 15s status/add/commit cap), and every call also at most the time
        # left on the region deadline (``DEFAULT_LOCK_TIMEOUT_S`` minus
        # ``_LOCKED_REGION_MARGIN_S``). A timeout there skips and does not
        # delete. That context ends before removal. Removal keeps its own
        # 120s bound, then the lock is released before branch prune.
        bounded_git = _bounded_locked_git()
        bounded_git.__enter__()
        prune_contained = False
        try:
            if dirty:
                stale_lock = _stale_index_lock(info.path)
                if stale_lock is not None:
                    return ReapResult(
                        path=str(info.path),
                        branch=info.branch,
                        action="skipped",
                        reason=(
                            f"stale index.lock at {stale_lock} (no live git process "
                            f"holds it; older than {_STALE_INDEX_LOCK_MIN_AGE_S / 60:g} minutes); "
                            f"originally qualified because {reason}"
                        ),
                        dirty=True,
                        pr=_pr_dict(pr_state),
                    )
            if dirty and not abandoning:
                preserve_error = _preserve_dirty_worktree(info, timeout=_LOCKED_GIT_STATUS_TIMEOUT_S)
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
            elif _is_review_checkout_reason(reason):
                recheck = _review_checkout_recheck(repo_root, info, reason, now)
                if recheck is not None:
                    return ReapResult(
                        path=str(info.path),
                        branch=info.branch,
                        action="skipped",
                        reason=f"{recheck}; originally qualified because {reason}",
                        dirty=dirty,
                        pr=_pr_dict(pr_state),
                    )
            elif reason.startswith(_DETACHED_CLEAN_CONTAINED_PREFIX):
                recheck = _detached_clean_contained_recheck(repo_root, info)
                if recheck is not None:
                    return ReapResult(
                        path=str(info.path),
                        branch=info.branch,
                        action="skipped",
                        reason=f"{recheck}; originally qualified because {reason}",
                        dirty=dirty,
                        pr=_pr_dict(pr_state),
                    )
            elif abandoning:
                try:
                    if _terminal_abandon_matches(repo_root, info.path) is None:
                        raise ValueError("terminal-abandon proof disappeared")
                except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError) as exc:
                    owner = _dispatch_owner(repo_root, info) or "infra lane"
                    return ReapResult(
                        path=str(info.path),
                        branch=info.branch,
                        action="skipped",
                        reason=(
                            f"terminal-abandon refused: {exc}; owner={owner}; "
                            "awaited=owner refreshes exact-head ABANDON and verified preservation proof"
                        ),
                        dirty=dirty,
                        pr=_pr_dict(pr_state),
                        owner=owner,
                    )
            else:
                current_clean = _worktree_clean(info.path, timeout=_LOCKED_GIT_STATUS_TIMEOUT_S)
                if current_clean is not True:
                    return ReapResult(
                        path=str(info.path),
                        branch=info.branch,
                        action="skipped",
                        reason=f"worktree changed during cleanup; originally qualified because {reason}",
                        dirty=None if current_clean is None else True,
                        pr=_pr_dict(pr_state),
                    )

            if reason.endswith("MERGED; patch-equivalent") and not _merged_equivalent(info, pr_state):
                return ReapResult(
                    path=str(info.path),
                    branch=info.branch,
                    action="skipped",
                    reason="merged-equivalent Git proof changed during cleanup",
                    dirty=dirty,
                    pr=_pr_dict(pr_state),
                )

            if reason.endswith("MERGED; origin branch gone"):
                assert pr_state is not None
                proved, detail = origin_gone if origin_gone is not None else (False, "origin-gone proof was not taken")
                if current_head != info.head:
                    proved, detail = False, "HEAD changed after origin-gone proof"
                elif _origin_branch_present(info.path, info.branch):
                    proved, detail = False, "origin branch returned during cleanup"
                if not proved:
                    return ReapResult(
                        path=str(info.path),
                        branch=info.branch,
                        action="skipped",
                        reason=detail,
                        dirty=dirty,
                        pr=_pr_dict(pr_state),
                    )

            if require_terminal_dispatch_guards:
                current_active_ids, probe_error = _resolve_activity_probe(repo_root, info, _read_active_task_probe())
                current_live_cwds = _live_cwd_paths(repo_root)
                if current_active_ids is None or current_live_cwds is None:
                    return ReapResult(
                        path=str(info.path),
                        branch=info.branch,
                        action="skipped",
                        reason=probe_error or "terminal dispatch guards unavailable during cleanup",
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
                    if pr_snapshot is None:
                        current_prs, current_pr_error = [], "PR snapshot missing"
                    else:
                        current_prs, current_pr_error = pr_snapshot
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
                current_active_ids, probe_error = _resolve_activity_probe(repo_root, info, _read_active_task_probe())
                current_live_cwds = _live_cwd_paths(repo_root)
                if current_active_ids is None or current_live_cwds is None:
                    return ReapResult(
                        path=str(info.path),
                        branch=info.branch,
                        action="skipped",
                        reason=probe_error or "abandoned-main activity probe unavailable during cleanup",
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
                    if pr_snapshot is None:
                        current_prs, current_pr_error = [], "PR snapshot missing"
                    else:
                        current_prs, current_pr_error = pr_snapshot
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
                timeout=_locked_call_timeout(reaper_lifecycle.DEFAULT_GIT_TIMEOUT_SECONDS),
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
            if (
                prune_merged_branches
                and info.branch is not None
                and pr_state is not None
                and pr_state.state == "MERGED"
            ):
                prune_contained = _pr_matches_worktree_head(info, pr_state) or _tip_is_ancestor_of_origin_main(info)
        finally:
            bounded_git.__exit__(None, None, None)

        # Outside the region deadline. The deadline is the dispatch lock
        # wait minus a margin (~25s); clipping removal to a leftover
        # fraction of a second kills ``git worktree remove --force``
        # mid-delete. Removal keeps :data:`GIT_WORKTREE_REMOVE_TIMEOUT_S`
        # (120s). A waiter that hits its 30s lock timeout retries.
        # Legacy classes retain their force setting. Proven continuation
        # cohorts use ordinary Git removal after mandatory preservation.
        control_root = control_plane_root(repo_root)
        preservation_receipt: dict[str, Any] = {}
        try:
            merged_reuse_proof = (
                None
                if abandoning
                else _record_merged_reuse_proof(
                    control_root,
                    info,
                    pr_state,
                    tasks_dir=task_store_paths.tasks_dir(),
                    allow_equivalent=reason.endswith("MERGED; patch-equivalent"),
                )
            )
        except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError) as exc:
            detail = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
            return ReapResult(
                path=str(info.path),
                branch=info.branch,
                action="skipped",
                reason=f"merged continuation proof unavailable: {detail}",
                dirty=dirty,
                pr=_pr_dict(pr_state),
            )
        if merged_reuse_proof is not None:
            preservation_receipt["merged_head_proof"] = merged_reuse_proof
        foreign_root = None if is_under_worktrees(repo_root, info.path) else _foreign_scratch_root(repo_root, info.path)
        approval: dict[str, Any] = {} if foreign_root is None else {"approved_temp_roots": (foreign_root,)}
        target = info.path
        if merged_reuse_proof is not None or reason.endswith("MERGED; patch-equivalent"):
            try:
                target = assert_delete_target(info.path, repo_root=repo_root, **approval)
            except ValueError as exc:
                return ReapResult(
                    path=str(info.path),
                    branch=info.branch,
                    action="error",
                    reason=reason,
                    dirty=dirty,
                    pr=_pr_dict(pr_state),
                    error=f"delete guard refused worktree target: {exc}",
                    recovery_ref=recovery_ref,
                    preserved_artifacts=preservation_receipt or None,
                )
        remove_error = worktree_claims.git_worktree_remove(
            repo_root,
            target,
            force=merged_reuse_proof is None and not reason.endswith("MERGED; patch-equivalent"),
            control_root=control_root,
            task_id=_dispatch_task_id(repo_root, info),
            tasks_dir=task_store_paths.tasks_dir(),
            preservation_receipt=preservation_receipt,
            **approval,
        )
        preserved_artifacts = preservation_receipt or None
        if remove_error is not None:
            preservation_failed = remove_error.startswith("artifact preservation failed:")
            return ReapResult(
                path=str(info.path),
                branch=info.branch,
                action="skipped" if preservation_failed else "error",
                reason=remove_error if preservation_failed else reason,
                dirty=dirty,
                pr=_pr_dict(pr_state),
                error=None if preservation_failed else remove_error,
                recovery_ref=recovery_ref,
                preserved_artifacts=preserved_artifacts,
            )

        # Prune and the daily-cap write do not need the per-worktree lock.
        # A waiter blocked on removal can proceed as soon as the checkout is gone.
        dispatch_guard.close()

        # Removal succeeded, so this is no longer the "never delete" bound.
        # A prune timeout is a branch-prune error on an already-removed tree.
        branch_prune_error = None
        branch_pruned = False
        if prune_contained:
            try:
                branch_prune_error = _prune_branch(
                    repo_root,
                    info.branch,
                    force=True,
                    expected_head=current_head,
                    timeout=_LOCKED_GIT_TIMEOUT_S,
                )
            except subprocess.TimeoutExpired as exc:
                branch_prune_error = f"branch prune timed out after {exc.timeout:g}s"
            branch_pruned = branch_prune_error is None

        reaper_lifecycle.record_reap_for_cap(repo_root)
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
                preserved_artifacts=preserved_artifacts,
            )
        return ReapResult(
            path=str(info.path),
            branch=info.branch,
            action="preserved_then_removed" if dirty else "removed",
            reason=reason,
            dirty=dirty,
            pr=_pr_dict(pr_state),
            branch_pruned=branch_pruned,
            recovery_ref=recovery_ref,
            preserved_artifacts=preserved_artifacts,
        )
    except subprocess.TimeoutExpired as exc:
        # A git call outlived its locked-region bound (#8748): skip, never
        # delete — the killed git leaves the tree's state unproven.
        return ReapResult(
            path=str(info.path),
            branch=info.branch,
            action="skipped",
            reason=(f"git call timed out after {exc.timeout:g}s during cleanup; originally qualified because {reason}"),
            dirty=dirty,
            pr=_pr_dict(pr_state),
            recovery_ref=recovery_ref,
        )
    finally:
        dispatch_guard.close()
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
    Owner abandonment requires both ``merged_pr_only=False`` and
    ``safe_only=False``; the default scheduled policy excludes that class.
    """
    repo_root = repo_root.resolve()
    targets = _target_filter(target_paths)
    results: list[ReapResult] = []
    qualified: list[tuple[WorktreeInfo, str, bool | None, PullRequestState | None]] = []
    active_probe = _read_active_task_probe()
    if require_activity_probe is None:
        require_activity_probe = bool(apply)
    killed_sandboxes = stop_orphaned_sandboxes(repo_root) if apply else []
    if live_cwds is None or killed_sandboxes:
        live_cwds = _live_cwd_paths(repo_root)
    if require_activity_probe and live_cwds is None:
        raise RuntimeError("process-CWD activity probe unavailable; cleanup skipped")

    with _ReapLock(repo_root):
        if apply and os.environ.get("LU_REAPER_DISABLED") != "1":
            # Release only reservations; every deletion still passes the normal
            # activity, ownership, cleanliness and exact merged-head proofs below.
            pending = reaper_lifecycle._read_mapping(reaper_lifecycle.pending_path(repo_root)).get("paths")
            if isinstance(pending, dict) and pending:
                control_root = worktree_claims.control_plane_root(primary_checkout_root(repo_root))
                lock_dir = worktree_claims.repository_lock_dir(control_root)
                for raw_path in pending:
                    target = Path(raw_path)
                    if not target.is_absolute() or not is_under_worktrees(repo_root, target):
                        continue
                    if targets is not None and target.resolve() not in targets:
                        continue
                    reaper_lifecycle.recover_orphaned_reap_pending(repo_root, target, lock_dir=lock_dir)
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

            foreign = not is_under_worktrees(repo_root, info.path)
            if foreign and _foreign_scratch_root(repo_root, info.path) is None:
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
                        reason=("registered worktree path is missing; run git worktree prune"),
                        dirty=None,
                        owner=_dispatch_owner(repo_root, info),
                    )
                )
                continue

            active_ids, probe_error = _resolve_activity_probe(repo_root, info, active_probe)
            if probe_error is not None:
                results.append(
                    ReapResult(
                        path=str(info.path),
                        branch=info.branch,
                        action="skipped",
                        reason=probe_error,
                        dirty=None,
                        owner=_dispatch_owner(repo_root, info),
                    )
                )
                continue

            activity = _activity_reason(
                repo_root=repo_root,
                info=info,
                active_ids=active_ids,
                live_cwds=live_cwds_for_reap(repo_root, info.path, live_cwds),
                probe_attachment_lock=not apply,
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
                            reason=(f"acp runtime worktree holds unexpected files; {acp_reason}"),
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

            # Report-only class (#8663): a dispatch worktree a stopped
            # ``git worktree add`` left under git's ``initializing`` lock is
            # reported for a human and never qualifies for removal.
            leftover = _initializing_leftover_result(repo_root, info)
            if leftover is not None:
                results.append(leftover)
                continue

            dirty_state = _worktree_clean(info.path)
            dirty = None if dirty_state is None else not dirty_state

            pr_state = None
            pr_error = None
            all_pr_states, commit_prs, review_number, errors = _review_pr_context(repo_root, info)

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
            attention: list[str] = []
            if pr_state is not None and pr_state.state == "CLOSED" and dirty is True:
                try:
                    abandoned = _terminal_abandon_matches(repo_root, info.path)
                    refusal = "closed PR dirty tree requires terminal-abandon.v1" if abandoned is None else None
                except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError) as exc:
                    refusal = f"terminal-abandon refused: {exc}"
                if refusal is not None:
                    results.append(
                        ReapResult(str(info.path), info.branch, "skipped", refusal, dirty, _pr_dict(pr_state))
                    )
                    continue
            if foreign:
                # A foreign scratch checkout is never a candidate for the
                # PR- or task-bound classes, only for the one class below --
                # and never while PR discovery for it has failed.
                reason = (
                    None
                    if pr_unknown
                    else _foreign_checkout_reason(
                        repo_root=repo_root,
                        info=info,
                        active_ids=active_ids,
                        attention=attention,
                    )
                )
            else:
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
                    attention=attention,
                )
            # Provably-safe class: a clean, pushed, detached dispatch checkout.
            # It never reads PR state for its own proof, but an open PR named
            # by the path still keeps the checkout mounted, like every other
            # class; the legacy classes above get first refusal.
            if (
                not foreign
                and reason is None
                and not attention
                and not (pr_state is not None and pr_state.state == "OPEN")
            ):
                reason = _detached_clean_contained_reason(
                    repo_root=repo_root,
                    info=info,
                    active_ids=active_ids,
                    attention=attention,
                )
            # Review checkouts the classes above cannot see (#9129): a
            # superseded PR head, or a detached checkout with no task record.
            # An unreadable PR guard forbids them, like every PR-dependent class.
            if not foreign and reason is None and not attention and not pr_unknown:
                reason = _review_checkout_reason(
                    repo_root=repo_root,
                    info=info,
                    pr_states=all_pr_states,
                    commit_prs=commit_prs,
                    review_number=review_number,
                    active_ids=active_ids,
                    now=now,
                    attention=attention,
                )
            if attention:
                results.append(
                    ReapResult(
                        path=str(info.path),
                        branch=info.branch,
                        action="skipped",
                        reason=attention[0],
                        dirty=dirty,
                        pr=_pr_dict(pr_state),
                        owner=_dispatch_owner(repo_root, info),
                    )
                )
                continue
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
                        reason = f"no reap condition matched; {pr_error}" if pr_error else "no reap condition matched"
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
        eligible_backlog = sum(1 for _, _, dirty, _ in qualified if dirty is False) if apply else None
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
                    include_terminal_dispatches and reason.startswith("settled dispatch task-id=")
                ),
                fallback_probe=active_probe if isinstance(active_probe, _ActiveTaskProbeFailure) else None,
                eligible_backlog=eligible_backlog,
                now=now,
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
        extra: dict[str, Any] = {}
        if result.needs_attention is not None:
            event = "needs_attention"
            extra["needs_attention"] = result.needs_attention
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
            **extra,
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
    matching = [info for info in list_git_worktrees(repo_root) if info.path.resolve() == target]
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


# Clean, fully pushed, idle dispatch worktrees (#10778).
#
# A finished dispatch checkout with no changes, no untracked files and every
# commit on origin holds nothing that Git does not already keep, yet the
# classes above retain many of them (unknown ownership, ``needs_finalize``).
# This mode removes exactly those trees. Every guard runs once to select a
# candidate and again under delegate's per-worktree lock, immediately before
# ``remove_unclaimed_worktree`` runs its own claim scan, the ignored-output
# preservation gate and a non-force ``git worktree remove``.

CLEAN_PUSHED_MIN_IDLE_S = 3600.0
CLEAN_PUSHED_REASON = "clean, no untracked files, all commits on origin, no process or live task, idle >= 60 min"
DEFAULT_CLEAN_PUSHED_ACTOR = "worktree-reaper (clean-pushed)"
ABANDON_LOG_RELATIVE = Path("batch_state") / "worktree-abandon-log.jsonl"
_FUSER = "fuser"
_CLEAN_PUSHED_PROBE_TIMEOUT_S = 10.0
_CLEAN_PUSHED_STATUS_TIMEOUT_S = 15.0
_CLEAN_PUSHED_WORKTREE_LOCK_TIMEOUT_S = 5.0
_CLEAN_PUSHED_LIVE_STATUSES = frozenset({"spawning", "running"})
_CLEAN_PUSHED_FETCH_TIMEOUT_S = 60.0
_CLEAN_PUSHED_MOVE_TIMEOUT_S = 60.0
_CLEAN_PUSHED_CENSUS_TIMEOUT_S = 60.0
# Same depth as ``.worktrees/dispatch/<agent>/<task>/``: a checkout waits here
# as ``.worktrees/.reaping/<agent>-<random>/<task>/`` between its last check
# and its removal. ``<random>`` is 128 bits; the directory is 0700.
QUARANTINE_RELATIVE = Path(".worktrees") / ".reaping"
# Written into the holder before the move; a later run recovers from it.
QUARANTINE_RECORD = ".reaper-quarantine.json"
_QUARANTINE_SCHEMA = "clean-pushed-quarantine.v1"
# ``intent``: moved (or about to be), Git removal not started; restorable.
# ``removing``: Git removal may have started; never restored automatically.
_QUARANTINE_STAGES = frozenset({"intent", "removing"})
UNPUBLISHED_REFLOG_COMMIT = "unpublished_reflog_commit"
UNINSPECTABLE_PROCESS = "uninspectable_process"
LATE_CHANGE = "late_change"
REFS_STALE = "refs_stale"


@dataclass(frozen=True)
class CleanPushedOutcome:
    """One worktree's disposition. ``path`` is repository-relative.

    ``action`` is ``removed``, ``would_remove`` (dry run), ``skipped`` (a
    guard refused; nothing was touched) or ``error`` (the removal failed and
    was not retried).
    """

    path: str
    action: str
    reason: str
    head: str | None = None
    branch: str | None = None
    task_status: str | None = None
    size_mb: int | None = None


@dataclass(frozen=True)
class CleanPushedReport:
    """Result of :func:`reap_clean_pushed`.

    ``removed`` holds the trees removed, or in a dry run the trees that would
    be. ``skipped`` holds every refusal and failed removal with its reason.
    ``refusal`` is set when the whole run did nothing, for example because
    another cleanup held the reaper lock (``lock_busy``) or ``git fetch
    --prune origin`` or the ``git ls-remote`` census failed (``refs_stale``). ``uninspectable`` lists pids of
    this user's processes whose open files could not be read (every tree is
    then kept), ``late_change`` the trees that changed between their last
    check and removal, and ``unpublished_reflog_commit`` the trees whose HEAD
    reflog names a commit no origin ref contains.
    """

    dry_run: bool
    removed: tuple[CleanPushedOutcome, ...]
    skipped: tuple[CleanPushedOutcome, ...]
    freed_mb: int
    lock_busy: bool = False
    refusal: str | None = None
    refs_stale: bool = False
    uninspectable: tuple[int, ...] = ()
    late_change: tuple[str, ...] = ()
    unpublished_reflog_commit: tuple[str, ...] = ()
    census_refs: int = 0
    census_missing: int = 0

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class _TaskClaim:
    name: str
    path: Path
    record: dict[str, Any]


@dataclass
class _TaskIndex:
    by_path: dict[Path, list[_TaskClaim]]
    unparsable: list[tuple[str, bytes]]
    unreadable: list[str]
    listing_error: str | None = None


def _build_task_index(tasks_dir: Path, repo_root: Path) -> _TaskIndex:
    """Index task records by the checkout their ``worktree_path`` or ``cwd`` names. Read-only."""
    index = _TaskIndex(by_path={}, unparsable=[], unreadable=[])
    try:
        state_files = sorted(tasks_dir.glob("*.json"))
    except OSError as exc:
        index.listing_error = f"task records unreadable ({type(exc).__name__})"
        return index
    for state_file in state_files:
        if worktree_claims.is_superseded_record(state_file):
            continue
        try:
            raw = state_file.read_bytes()
        except FileNotFoundError:
            continue
        except OSError:
            index.unreadable.append(state_file.name)
            continue
        try:
            record = json.loads(raw)
        except (ValueError, RecursionError):
            record = None
        if not isinstance(record, dict):
            index.unparsable.append((state_file.name, raw))
            continue
        claimed: set[Path] = set()
        for key in ("worktree_path", "cwd"):
            value = record.get(key)
            if value is None or value == "":
                continue
            try:
                if not isinstance(value, str):
                    raise ValueError(key)
                claimed.add(worktree_claims.resolve_claim_path(value, repo_root=repo_root))
            except (OSError, RuntimeError, ValueError):
                index.unparsable.append((state_file.name, raw))
                claimed.clear()
                break
        for path in claimed:
            index.by_path.setdefault(path, []).append(_TaskClaim(state_file.name, state_file, record))
    return index


def _worker_proven_gone(record: dict[str, Any]) -> bool:
    """True when the record names no worker pid, or its worker is proven dead."""
    return not record.get("pid") or worker_liveness(record) is False


def _task_claim_refusal(name: str, record: dict[str, Any]) -> str | None:
    """Refuse a live or unknown task. ``needs_finalize`` and finished tasks pass once their worker is gone."""
    task = record.get("task_id") or name.removesuffix(".json")
    status = record.get("status")
    if status in _CLEAN_PUSHED_LIVE_STATUSES:
        return f"task {task} is {status}"
    if status != worktree_claims.NEEDS_FINALIZE_STATUS and status not in worktree_claims.RELEASED_TASK_STATUSES:
        return f"task {task} status {status!r} is not settled"
    if not _worker_proven_gone(record):
        return f"task {task} worker is live or unknown"
    return None


def _reread_claims(claims: list[_TaskClaim], path: Path, repo_root: Path) -> tuple[list[_TaskClaim], str | None]:
    """Re-read each indexed claim; a record that changed its claim drops out, an unreadable one refuses."""
    fresh: list[_TaskClaim] = []
    for claim in claims:
        try:
            record = json.loads(claim.path.read_bytes())
        except FileNotFoundError:
            continue
        except (OSError, ValueError, RecursionError):
            return [], f"task record {claim.name} unreadable"
        if not isinstance(record, dict):
            return [], f"task record {claim.name} unreadable"
        names: set[Path] = set()
        for key in ("worktree_path", "cwd"):
            value = record.get(key)
            if isinstance(value, str) and value:
                try:
                    names.add(worktree_claims.resolve_claim_path(value, repo_root=repo_root))
                except (OSError, RuntimeError, ValueError):
                    return [], f"task record {claim.name} unreadable"
            elif value not in (None, ""):
                return [], f"task record {claim.name} unreadable"
        if path in names:
            fresh.append(_TaskClaim(claim.name, claim.path, record))
    return fresh, None


def _tree_mtime_sources(path: Path, common_git_dir: Path) -> tuple[list[Path], str | None]:
    """The checkout's HEAD, index and HEAD reflog, inside the shared ``.git/worktrees/``."""
    git_dir = _worktree_git_dir(path)
    if git_dir is None:
        return [], "git admin directory unresolvable"
    try:
        git_dir.resolve(strict=True).relative_to((common_git_dir / "worktrees").resolve(strict=True))
    except (OSError, ValueError):
        return [], "git admin directory is outside the repository's .git/worktrees/"
    sources = [git_dir / "HEAD", git_dir / "index"]
    reflog = git_dir / "logs" / "HEAD"
    if reflog.exists():
        sources.append(reflog)
    return sources, None


def _newest_mtime(paths: list[Path], *, required: int) -> tuple[float | None, str | None]:
    """Newest mtime; the first ``required`` paths must exist, the rest may be absent."""
    newest: float | None = None
    for position, candidate in enumerate(paths):
        try:
            mtime = candidate.stat().st_mtime
        except FileNotFoundError:
            if position < required:
                return None, f"{candidate.name} missing; activity unknown"
            continue
        except OSError:
            return None, f"{candidate.name} unreadable; activity unknown"
        newest = mtime if newest is None else max(newest, mtime)
    return newest, None


def _inside(target: str, root: str) -> bool:
    target = target.removesuffix(" (deleted)")
    return target == root or target.startswith(f"{root}/")


def _proc_status(base: Path) -> dict[str, str] | None:
    """Fields of ``/proc/<pid>/status``, world-readable even for a non-dumpable process; ``None`` once it exited."""
    try:
        text = (base / "status").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    return {key: value.strip() for key, _, value in (line.partition(":") for line in text.splitlines()) if value}


def _session_infrastructure(base: Path, status: dict[str, str], uid: int, proc_root: Path) -> bool:
    """A non-dumpable process of this user that never works inside a checkout.

    Only two kinds, both identified by kernel facts rather than by what the
    process reports about itself: the user's systemd manager and its
    ``(sd-pam)`` helper, the only members of the manager's ``init.scope``
    cgroup (systemd starts every unit, including dispatch workers, in a
    cgroup of its own); and OpenSSH's per-connection ``sshd-session`` whose
    parent is the root-owned privileged ``sshd-session``/``sshd``.
    """
    try:
        cgroup = (base / "cgroup").read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return False
    if cgroup == [f"0::/user.slice/user-{uid}.slice/user@{uid}.service/init.scope"]:
        return True
    sshd = {"sshd-session", "sshd"}
    if status.get("Name") not in sshd:
        return False
    parent = _proc_status(proc_root / status.get("PPid", ""))
    return parent is not None and parent.get("Name") in sshd and parent.get("Uid", "").split()[:1] == ["0"]


# ``PF_KTHREAD`` in the ``flags`` field (field 9) of ``/proc/<pid>/stat``.
_PF_KTHREAD = 0x00200000
_STAT_HEAD = re.compile(r"\d+ \(")


def _stat_kind(base: Path) -> str:
    """``gone``, ``zombie``, ``kernel``, ``user`` or ``unknown``, from ``/proc/<pid>/stat`` (#10778).

    The kernel sets ``PF_KTHREAD`` on kernel threads; a pid number proves
    nothing, because in a PID namespace pid 2 and its children are ordinary
    userspace processes. ``comm`` may hold spaces and parentheses, so the
    fields are read after the last ``)``.
    """
    try:
        text = (base / "stat").read_text(encoding="utf-8", errors="replace")
    except (FileNotFoundError, ProcessLookupError):
        return "gone"
    except OSError:
        return "unknown"
    head, closing, tail = text.rpartition(")")
    fields = tail.split()
    if not closing or not _STAT_HEAD.match(head) or len(fields) < 7:
        return "unknown"
    try:
        flags = int(fields[6])
    except ValueError:
        return "unknown"
    if fields[0] in {"Z", "X"}:
        return "zombie"
    return "kernel" if flags & _PF_KTHREAD else "user"


def _uninspectable_same_user(base: Path, proc_root: Path) -> bool:
    """True when a live process of this user denied inspection (it is not dumpable).

    Zombies and kernel threads (``PF_KTHREAD``) have nothing to inspect. A
    process whose real, effective or saved uid differs is another user's,
    which this scan cannot see, exactly as ``fuser`` cannot. A process of
    this user whose ``stat`` cannot be read or parsed is unknown and counts.
    """
    status = _proc_status(base)
    if status is None:
        return False
    uid = os.getuid()
    if status.get("Uid", "").split()[:3] != [str(uid)] * 3:
        return False
    kind = _stat_kind(base)
    if kind in {"gone", "zombie", "kernel"}:
        return False
    return kind == "unknown" or not _session_infrastructure(base, status, uid, proc_root)


def _proc_users_inside(
    root: Path,
    *,
    deadline: float,
    proc_root: Path = Path("/proc"),
    uninspectable: list[int] | None = None,
) -> bool | None:
    """True when a visible process has its cwd, root, executable, an open or a mapped file inside ``root``.

    ``fuser <dir>`` reports only processes using the directory itself; this
    also covers a shell or test runner whose working directory is a
    subdirectory, and a working directory that is ``root``'s inode under
    another name. ``None`` when the process table cannot be listed or the
    scan runs out of time. A live process of this user that denies
    inspection is appended to ``uninspectable`` (#10778): it may be using
    ``root``. Other users' processes are invisible here, as they are to
    ``fuser``.
    """
    prefix = str(root)
    try:
        identity = (root.stat().st_dev, root.stat().st_ino)
        entries = [entry for entry in os.scandir(proc_root) if entry.name.isdigit()]
    except OSError:
        return None
    if not entries:
        return None
    for entry in entries:
        if time.monotonic() >= deadline:
            return None
        base = Path(entry.path)
        denied = False
        links = [base / "cwd", base / "root", base / "exe"]
        try:
            links.extend((base / "fd").iterdir())
        except PermissionError:
            denied = True
        except OSError:
            pass
        for link in links:
            try:
                if _inside(os.readlink(link), prefix):
                    return True
            except PermissionError:
                denied = True
            except OSError:
                continue
        try:
            cwd = (base / "cwd").stat()
            if (cwd.st_dev, cwd.st_ino) == identity:
                return True
        except PermissionError:
            denied = True
        except OSError:
            pass
        try:
            maps = (base / "maps").read_text(encoding="utf-8", errors="replace")
        except PermissionError:
            denied = True
            maps = ""
        except OSError:
            maps = ""
        for line in maps.splitlines():
            fields = line.split(None, 5)
            if len(fields) == 6 and _inside(fields[5], prefix):
                return True
        if denied and uninspectable is not None and _uninspectable_same_user(base, proc_root):
            uninspectable.append(int(entry.name))
    return None if time.monotonic() >= deadline else False


def _process_refusal(path: Path, uninspectable: set[int] | None = None) -> str | None:
    """Refuse when ``fuser`` or the process table shows a user; any probe failure counts as in use.

    ``uninspectable`` collects this run's uninspectable pids; once it holds
    one, every tree is kept for the rest of the run.
    """
    fuser = _FUSER if os.path.isabs(_FUSER) else shutil.which(_FUSER)
    if fuser is None or not os.access(fuser, os.X_OK):
        return "fuser unavailable; treated as in use"
    try:
        proc = _run([fuser, "-s", str(path)], cwd=path.parent, timeout=_CLEAN_PUSHED_PROBE_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return "fuser timed out; treated as in use"
    except (OSError, subprocess.SubprocessError) as exc:
        return f"fuser failed ({type(exc).__name__}); treated as in use"
    if proc.returncode == 0:
        return "in use: fuser reports a process using the checkout"
    if proc.returncode != 1 or (proc.stderr or "").strip() or (proc.stdout or "").strip():
        return f"fuser failed (exit {proc.returncode}); treated as in use"
    budget = _effective_timeout(_CLEAN_PUSHED_PROBE_TIMEOUT_S)
    denied: list[int] = []
    users = _proc_users_inside(path, deadline=time.monotonic() + (budget or 0.0), uninspectable=denied)
    if users is None:
        return "process table probe unavailable; treated as in use"
    if users:
        return "in use: a process works inside the checkout"
    if uninspectable is not None:
        uninspectable.update(denied)
        denied = sorted(uninspectable)
    if denied:
        return f"{UNINSPECTABLE_PROCESS} {denied[0]}: a process of this user cannot be inspected"
    return None


_INDEX_MODES = {"100644": False, "100755": True}


def _matches_index(file: Path, info: os.stat_result, mode: str, blob: str, algorithm: str) -> bool:
    """True when ``file`` on disk is byte-identical to its index blob, with the same type and exec bit."""
    if mode == "120000":
        if not stat.S_ISLNK(info.st_mode):
            return False
        target = os.fsencode(os.readlink(file))
        digest = hashlib.new(algorithm, f"blob {len(target)}\0".encode())
        digest.update(target)
        return digest.hexdigest() == blob
    if mode not in _INDEX_MODES:
        return False  # a gitlink or an unknown mode: never proven unchanged
    if not stat.S_ISREG(info.st_mode) or bool(info.st_mode & 0o111) != _INDEX_MODES[mode]:
        return False
    digest = hashlib.new(algorithm, f"blob {info.st_size}\0".encode())
    read = 0
    with file.open("rb", buffering=0) as handle:  # raw bytes: no clean/smudge filter
        while chunk := handle.read(1 << 20):
            read += len(chunk)
            digest.update(chunk)
    return read == info.st_size and digest.hexdigest() == blob


def _hidden_change_refusal(path: Path) -> str | None:
    """Refuse when an assume-unchanged or skip-worktree file present on disk differs from the index (#10778).

    ``git status`` and ``git worktree remove`` both trust those flags, so an
    edit behind them is invisible to every other guard. A sparse checkout's
    excluded entries carry skip-worktree with no file on disk; they pass.
    Unfiltered bytes are compared, so a clean/smudge difference refuses too.
    """
    form = _run(["git", "rev-parse", "--show-object-format"], cwd=path, timeout=_CLEAN_PUSHED_PROBE_TIMEOUT_S)
    algorithm = (form.stdout or "").strip()
    if form.returncode != 0 or algorithm not in {"sha1", "sha256"}:
        return "object format unknown"
    try:
        listing = _run(["git", "ls-files", "-v", "-s", "-z"], cwd=path, timeout=_CLEAN_PUSHED_STATUS_TIMEOUT_S)
    except ValueError:
        return "index listing unreadable"
    if listing.returncode != 0:
        return "index listing failed"
    hidden = "hidden change: a file flagged assume-unchanged or skip-worktree differs from the index"
    for record in (listing.stdout or "").split("\0"):
        if not record:
            continue
        meta, _, name = record.partition("\t")
        fields = meta.split()
        if len(fields) != 4 or not name:
            return "index listing unreadable"
        tag, mode, blob, _stage = fields
        if not (tag.islower() or tag == "S"):
            continue
        file = path / name
        try:
            info = file.lstat()
        except (FileNotFoundError, NotADirectoryError):
            continue
        except OSError:
            return hidden
        try:
            if not _matches_index(file, info, mode, blob, algorithm):
                return hidden
        except OSError:
            return hidden
    return None


@dataclass(frozen=True)
class _OriginCensus:
    """What ``git ls-remote origin`` advertised for heads and tags at the start of the run (#10778).

    ``tips`` are the advertised commits (annotated tags peeled) present in
    the local object store; ``missing`` counts advertised objects that are
    not, which leaves any commit they might contain unproven. Local
    remote-tracking refs are never consulted: a narrowed fetch refspec
    leaves them stale.
    """

    tips: tuple[str, ...]
    missing: int
    refs: int


def _origin_census(primary: Path) -> tuple[_OriginCensus | None, str | None]:
    """Census of origin's heads and tags (bounded); ``(census, None)`` or ``(None, failure)``."""
    label = "git ls-remote --heads --tags origin"
    try:
        proc = _run(
            ["git", "ls-remote", "--heads", "--tags", "origin"], cwd=primary, timeout=_CLEAN_PUSHED_CENSUS_TIMEOUT_S
        )
    except subprocess.TimeoutExpired:
        return None, f"{label} timed out after {_CLEAN_PUSHED_CENSUS_TIMEOUT_S:g}s"
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        return None, f"{label} failed ({type(exc).__name__})"
    if proc.returncode != 0:
        return None, f"{label} failed (exit {proc.returncode})"
    form = _run(["git", "rev-parse", "--show-object-format"], cwd=primary, timeout=_CLEAN_PUSHED_PROBE_TIMEOUT_S)
    width = {"sha1": 40, "sha256": 64}.get((form.stdout or "").strip()) if form.returncode == 0 else None
    if width is None:
        return None, "object format unknown"
    advertised: dict[str, str] = {}
    peeled: dict[str, str] = {}
    for line in (proc.stdout or "").splitlines():
        oid, tab, ref = line.partition("\t")
        if (
            not tab
            or len(oid) != width
            or oid.strip("0123456789abcdef")
            or not ref.startswith(("refs/heads/", "refs/tags/"))
        ):
            return None, f"{label} printed an unexpected line"
        if ref.endswith("^{}"):
            peeled[ref.removesuffix("^{}")] = oid
        else:
            advertised[ref] = oid
    if not advertised:
        return _OriginCensus(tips=(), missing=0, refs=0), None
    proofs = sorted({peeled.get(ref, oid) for ref, oid in advertised.items()})
    check = _run(
        ["git", "cat-file", "--batch-check=%(objectname) %(objecttype)"],
        cwd=primary,
        timeout=_CLEAN_PUSHED_PROBE_TIMEOUT_S,
        input_text="\n".join(proofs) + "\n",
    )
    rows = [row.split() for row in (check.stdout or "").splitlines()]
    if check.returncode != 0 or len(rows) != len(proofs) or any(len(row) != 2 for row in rows):
        return None, "advertised objects could not be looked up locally"
    tips = tuple(oid for oid, kind in rows if kind == "commit")
    missing = sum(1 for _oid, kind in rows if kind == "missing")
    return _OriginCensus(tips=tips, missing=missing, refs=len(advertised)), None


def _unpublished(path: Path, revisions: list[str], census: _OriginCensus) -> bool:
    """True when a commit reachable from ``revisions`` is reachable from no census tip.

    Raises ``RuntimeError`` when Git cannot answer.
    """
    if not revisions:
        return False
    stdin = [*revisions, *(f"^{tip}" for tip in census.tips)]
    proc = _run(
        ["git", "rev-list", "--max-count=1", "--stdin"],
        cwd=path,
        timeout=_CLEAN_PUSHED_PROBE_TIMEOUT_S,
        input_text="\n".join(stdin) + "\n",
    )
    if proc.returncode != 0:
        raise RuntimeError("rev-list failed")
    return bool((proc.stdout or "").strip())


def _publication_unproven(census: _OriginCensus, refusal: str) -> str:
    """``refusal``, or ``refs_stale`` when advertised objects missing locally might contain the commit."""
    if census.missing:
        return f"{REFS_STALE}: publication unproven; {census.missing} advertised origin object(s) missing locally"
    return refusal


_PSEUDOREF_NAME = re.compile(r"[A-Z][A-Z_]*")
# Pseudorefs that name only objects (one per line); any other content is unknown.
_OBJECT_PSEUDOREFS = frozenset(
    {"ORIG_HEAD", "MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "REBASE_HEAD", "AUTO_MERGE"}
)


def _is_oid(text: str, width: int) -> bool:
    return len(text) == width and not text.strip("0123456789abcdef")


def _private_git_dir(path: Path) -> tuple[Path | None, int | None, str | None]:
    """The checkout's own git directory (``git rev-parse --git-dir``) and object id width; else a failure."""
    proc = _run(
        ["git", "rev-parse", "--path-format=absolute", "--git-dir", "--git-common-dir", "--show-object-format"],
        cwd=path,
        timeout=_CLEAN_PUSHED_PROBE_TIMEOUT_S,
    )
    lines = (proc.stdout or "").splitlines()
    if proc.returncode != 0 or len(lines) != 3:
        return None, None, "git directory unresolvable"
    width = {"sha1": 40, "sha256": 64}.get(lines[2])
    if width is None:
        return None, None, "object format unknown"
    private, common = Path(lines[0]), Path(lines[1])
    if not private.is_absolute() or _real_directory(private) is None or private.resolve() == common.resolve():
        return None, None, "the checkout has no private git directory of its own"
    if (private / "reftable").exists() or (common / "reftable").exists():
        return None, None, "reftable ref storage is not inspected"
    return private, width, None


def _named_in_file(file: Path, relative: str, width: int) -> list[str] | None:
    """Object ids ``file`` names: a reflog, a loose ref or a pseudoref; ``[]`` for none, ``None`` when unknown."""
    try:
        if not stat.S_ISREG(file.lstat().st_mode):
            return None
        lines = file.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    if relative.startswith("logs/"):
        named = []
        for line in lines:
            fields = line.split(" ", 2)
            if len(fields) != 3 or not (_is_oid(fields[0], width) and _is_oid(fields[1], width)):
                return None
            named.extend(fields[:2])
        return named
    if relative == "FETCH_HEAD":
        heads = [line.partition("\t")[0] for line in lines if line]
        return heads if all(_is_oid(oid, width) for oid in heads) else None
    if relative.startswith("refs/") or relative == "HEAD" or relative in _OBJECT_PSEUDOREFS:
        if len(lines) == 1 and lines[0].startswith("ref: ") and relative not in _OBJECT_PSEUDOREFS:
            return []  # a symbolic ref: its target is a shared branch, which survives removal
        if not lines or not all(_is_oid(line, width) for line in lines):
            return None
        return lines
    return lines if len(lines) == 1 and _is_oid(lines[0], width) else []


def _raise(error: OSError) -> None:
    raise error


def _private_history(path: Path) -> tuple[list[str], str | None]:
    """Every object id the checkout's private git directory records; ``([], failure)`` when not all are readable.

    Removal deletes that directory: HEAD and every per-worktree ref
    (``refs/worktree/``, ``refs/bisect/``, ``refs/rewritten/``), the
    reflog of each (``logs/``, both sides of every entry), and the
    top-level pseudorefs (``ORIG_HEAD``, ``FETCH_HEAD``, ``MERGE_HEAD``,
    ``AUTO_MERGE`` and any other all-caps file holding one object id).
    """
    private, width, failure = _private_git_dir(path)
    if failure:
        return [], failure
    assert private is not None and width is not None
    files: list[tuple[Path, str]] = []
    try:
        for top in private.iterdir():
            if top.name in {"logs", "refs"}:
                if top.is_symlink() or not top.is_dir():
                    return [], f"{top.name} is not a real directory"
                for directory, dirs, names in os.walk(top, onerror=_raise):
                    for name in dirs:
                        if (Path(directory) / name).is_symlink():
                            return [], "a symbolic link in the ref store"
                    for name in names:
                        file = Path(directory) / name
                        files.append((file, file.relative_to(private).as_posix()))
            elif _PSEUDOREF_NAME.fullmatch(top.name):
                files.append((top, top.name))
    except OSError:
        return [], "private git directory unreadable"
    null = "0" * width
    named: list[str] = []
    for file, relative in files:
        oids = _named_in_file(file, relative, width)
        if oids is None:
            return [], f"{relative} unreadable or unparseable"
        named.extend(oid for oid in oids if oid != null)
    return list(dict.fromkeys(named)), None


def _reflog_refusal(path: Path, census: _OriginCensus) -> str | None:
    """Refuse when an object this checkout alone records is on no origin ref (#10778).

    Removal deletes the checkout's private git directory, whose reflogs,
    per-worktree refs and pseudorefs may be the last records of a commit
    that was reset away (:func:`_private_history`). Each must be a commit
    present locally and contained in an advertised head or tag; anything
    unreadable, missing or not a commit keeps the tree. The stash is shared
    by every checkout and survives removal.
    """
    named, failure = _private_history(path)
    if failure:
        return f"{UNPUBLISHED_REFLOG_COMMIT}: recovery history unknown ({failure})"
    if not named:
        return None
    kinds = _run(  # peeled: a tag counts only when it names a commit
        ["git", "cat-file", "--batch-check=%(objecttype)"],
        cwd=path,
        timeout=_CLEAN_PUSHED_PROBE_TIMEOUT_S,
        input_text="".join(f"{oid}^{{}}\n" for oid in named),
    )
    rows = (kinds.stdout or "").splitlines()
    if kinds.returncode != 0 or len(rows) != len(named):
        return "reflog check failed"
    if any(row.split()[-1:] == ["missing"] for row in rows):
        return f"{UNPUBLISHED_REFLOG_COMMIT}: the recovery history names an object missing locally"
    if any(row != "commit" for row in rows):
        return f"{UNPUBLISHED_REFLOG_COMMIT}: the recovery history names an object that is not a commit"
    try:
        unpublished = _unpublished(path, named, census)
    except RuntimeError:
        return "reflog check failed"
    if unpublished:
        return _publication_unproven(
            census, f"{UNPUBLISHED_REFLOG_COMMIT}: the recovery history names a commit no origin ref contains"
        )
    return None


def _git_refusal(path: Path, expected_head: str | None, census: _OriginCensus) -> str | None:
    """HEAD unchanged, the tree clean (flagged index entries included) and every commit on an origin head or tag."""
    try:
        head = _run(["git", "rev-parse", "--verify", "HEAD"], cwd=path, timeout=_CLEAN_PUSHED_PROBE_TIMEOUT_S)
        if head.returncode != 0:
            return "HEAD unresolvable"
        if not expected_head or (head.stdout or "").strip() != expected_head:
            return "HEAD moved since the worktree listing"
        status = _run(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=path,
            timeout=_CLEAN_PUSHED_STATUS_TIMEOUT_S,
        )
        if status.returncode != 0:
            return "git status failed"
        if (status.stdout or "").strip():
            return "dirty or untracked files"
        refusal = _hidden_change_refusal(path)
        if refusal:
            return refusal
        try:
            unpushed = _unpublished(path, [expected_head], census)
        except RuntimeError:
            return "unpushed-commit check failed"
        if unpushed:
            return _publication_unproven(census, "commits not on origin")
        return _reflog_refusal(path, census)
    except subprocess.TimeoutExpired:
        return "git probe timed out"


@dataclass(frozen=True)
class _CleanPushedContext:
    primary: Path
    dispatch_root: Path
    common_git_dir: Path
    tasks_dir: Path
    index: _TaskIndex
    census: _OriginCensus
    now: float | None = None
    uninspectable: set[int] = field(default_factory=set)


def _location_refusal(info: WorktreeInfo, ctx: _CleanPushedContext, tree: Path) -> str | None:
    """``info.path`` must be a dispatch checkout; ``tree`` (it, or its quarantine) a real directory."""
    path = info.path
    if path == ctx.primary or path.resolve() == ctx.primary.resolve():
        return "primary checkout"
    try:
        relative = path.relative_to(ctx.dispatch_root)
    except ValueError:
        try:
            path.relative_to(ctx.primary.resolve() / QUARANTINE_RELATIVE)
        except ValueError:
            return "outside .worktrees/dispatch/"
        return "left in the reaper quarantine by an interrupted run; restore it (runbook)"
    if len(relative.parts) != 2:
        return "not a .worktrees/dispatch/<agent>/<task>/ checkout"
    if relative.parts[0] == "acp":
        return "ACP runtime checkout; the ACP sweep owns it"
    if _real_directory(tree) is None:
        return "path is a symlink, missing, or not a directory"
    return None


def _clean_pushed_refusal(
    info: WorktreeInfo,
    ctx: _CleanPushedContext,
    claims: list[_TaskClaim],
    *,
    recheck: bool,
    tree: Path | None = None,
) -> tuple[str | None, list[_TaskClaim]]:
    """Every guard of the mode, cheapest first. Returns ``(refusal, current claims)``.

    Identity guards (location, lock, reservation, leases, task claims) judge
    ``info.path``; content guards (activity, Git, processes) inspect
    ``tree``, which is ``info.path`` or, after the move, its quarantine.
    """
    path = info.path
    tree = path if tree is None else tree
    refusal = _location_refusal(info, ctx, tree)
    if refusal:
        return refusal, claims
    if info.locked_reason is not None:
        return "git worktree is locked", claims
    if reaper_lifecycle.is_reap_pending(ctx.primary, path):
        return "reap reservation pending", claims
    task_id = _dispatch_task_id_for_path(ctx.primary, path)
    lease = _has_active_rollover_lease(ctx.primary, info) or _has_active_ownership_claim(ctx.primary, task_id)
    if lease:
        return lease, claims
    if ctx.index.listing_error:
        return ctx.index.listing_error, claims
    if ctx.index.unreadable:
        return f"task record {ctx.index.unreadable[0]} unreadable", claims
    needles = worktree_claims.worktree_claim_needles(path, path)
    for name, raw in ctx.index.unparsable:
        if worktree_claims.record_may_claim_worktree(raw, needles):
            return f"task record {name} unreadable", claims
    if recheck:
        claims, refusal = _reread_claims(claims, path.resolve(), ctx.primary)
        if refusal:
            return refusal, claims
    for claim in claims:
        refusal = _task_claim_refusal(claim.name, claim.record)
        if refusal:
            return refusal, claims
    sources, refusal = _tree_mtime_sources(tree, ctx.common_git_dir)
    if refusal:
        return refusal, claims
    required = len(sources[:2])
    sources += [claim.path for claim in claims]
    if task_id:
        sources.append(ctx.tasks_dir / f"{task_id}.json")
    newest, refusal = _newest_mtime(sources, required=required)
    if refusal or newest is None:
        return refusal or "activity unknown", claims
    idle_s = (ctx.now if ctx.now is not None else time.time()) - newest
    if idle_s < CLEAN_PUSHED_MIN_IDLE_S:
        return f"last activity {max(0, int(idle_s // 60))} min ago (< 60 min)", claims
    refusal = _git_refusal(tree, info.head, ctx.census)
    if refusal:
        return refusal, claims
    return _process_refusal(tree, ctx.uninspectable), claims


def _tree_size_mb(root: Path) -> int:
    """Allocated size like ``du -sm``: no symlinks followed, one filesystem, hard links once."""
    seen: set[tuple[int, int]] = set()
    total = 0
    try:
        device = root.lstat().st_dev
    except OSError:
        return 0
    stack = [root]
    while stack:
        directory = stack.pop()
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    try:
                        status = entry.stat(follow_symlinks=False)
                    except OSError:
                        continue
                    if status.st_dev != device or (status.st_dev, status.st_ino) in seen:
                        continue
                    seen.add((status.st_dev, status.st_ino))
                    total += status.st_blocks * 512
                    if stat.S_ISDIR(status.st_mode):
                        stack.append(Path(entry.path))
        except OSError:
            continue
    return round(total / (1024 * 1024))


def _display_path(path: Path, primary: Path) -> str:
    """Repository-relative spelling; never an absolute host path."""
    try:
        return path.relative_to(primary).as_posix()
    except ValueError:
        return f"<external>/{path.name}"


def _task_status(claims: list[_TaskClaim]) -> str | None:
    newest: tuple[float, str] | None = None
    for claim in claims:
        status = claim.record.get("status")
        try:
            mtime = claim.path.stat().st_mtime
        except OSError:
            mtime = 0.0
        if isinstance(status, str) and (newest is None or mtime > newest[0]):
            newest = (mtime, status)
    return newest[1] if newest else None


def append_abandon_log(control_root: Path, entry: dict[str, Any]) -> None:
    """Append one fsync'd line to ``batch_state/worktree-abandon-log.jsonl``."""
    path = control_root / ABANDON_LOG_RELATIVE
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            handle.write(json.dumps(entry) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _refresh_origin_refs(primary: Path) -> str | None:
    """``git fetch --prune origin`` (no tags, no submodules, bounded); the failure, or ``None``.

    It brings origin's objects here, so the census tips can be checked for
    ancestry; the refs it updates prove nothing (a narrowed fetch refspec
    leaves some stale), :func:`_origin_census` does. Runs before the reaper
    lock is taken: no remote read may happen under it.
    """
    try:
        proc = _run(
            ["git", "fetch", "--no-tags", "origin", "--prune"], cwd=primary, timeout=_CLEAN_PUSHED_FETCH_TIMEOUT_S
        )
    except subprocess.TimeoutExpired:
        return f"git fetch --prune origin timed out after {_CLEAN_PUSHED_FETCH_TIMEOUT_S:g}s"
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        return f"git fetch --prune origin failed ({type(exc).__name__})"
    if proc.returncode != 0:
        return f"git fetch --prune origin failed (exit {proc.returncode})"
    return None


def _move_worktree(primary: Path, source: Path, destination: Path) -> str | None:
    """``git worktree move`` (an atomic rename that git records); the failure, or ``None``."""
    try:
        proc = _run(
            ["git", "worktree", "move", str(source), str(destination)],
            cwd=primary,
            timeout=_CLEAN_PUSHED_MOVE_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        return "git worktree move timed out"
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        return f"git worktree move failed ({type(exc).__name__})"
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip().splitlines()
        return f"git worktree move failed: {detail[-1] if detail else f'exit {proc.returncode}'}"
    return None


_Entry = tuple[int, ...]
# Rewritten by ``git worktree move`` (the checkout's ``.git`` pointer, the admin
# ``gitdir``) or refreshed by any Git command (``index``): only their type counts.
_VOLATILE_TREE = frozenset({".git"})
_VOLATILE_ADMIN = frozenset({"gitdir", "index"})


@dataclass(frozen=True)
class _Manifest:
    """Metadata of every entry of a checkout and of its Git admin directory (#10778).

    Paths are relative, so a manifest taken before the quarantine move
    compares equal to one taken after it. A write changes a file's ctime,
    which no process can set back, so any change since the manifest shows.
    """

    admin: Path
    tree: dict[str, _Entry]
    admin_entries: dict[str, _Entry]


def _entries(root: Path, volatile: frozenset[str]) -> dict[str, _Entry]:
    """Every entry below ``root`` (not ``root`` itself), symlinks not followed; raises ``OSError``."""
    entries: dict[str, _Entry] = {}
    stack = [(root, "")]
    while stack:
        directory, prefix = stack.pop()
        with os.scandir(directory) as listing:
            for entry in listing:
                name = prefix + entry.name
                info = entry.stat(follow_symlinks=False)
                kind = stat.S_IFMT(info.st_mode)
                if name in volatile:
                    entries[name] = (kind,)
                    continue
                entries[name] = (
                    kind,
                    stat.S_IMODE(info.st_mode),
                    info.st_dev,
                    info.st_ino,
                    info.st_nlink,
                    info.st_size,
                    info.st_mtime_ns,
                    info.st_ctime_ns,
                )
                if kind == stat.S_IFDIR:
                    stack.append((Path(entry.path), f"{name}/"))
    return entries


def _manifest(tree: Path) -> _Manifest:
    """The manifest of ``tree`` and its admin directory; raises ``OSError`` when either is unreadable."""
    admin = _worktree_git_dir(tree)
    if admin is None:
        raise OSError("git admin directory unresolvable")
    return _Manifest(admin=admin, tree=_entries(tree, _VOLATILE_TREE), admin_entries=_entries(admin, _VOLATILE_ADMIN))


def _missing_entries(tree: Path, manifest: _Manifest) -> int:
    """How many entries of ``manifest`` no longer exist: a failed Git removal deleted some of them."""
    gone = sum(1 for name in manifest.tree if not os.path.lexists(tree / name))
    return gone + sum(1 for name in manifest.admin_entries if not os.path.lexists(manifest.admin / name))


def _final_recheck(tree: Path, baseline: _Manifest) -> str | None:
    """The last look at the quarantined ``tree`` before Git removes it (#10778).

    The tree and its admin directory must be exactly as they were before
    artifact preservation, and no visible process may use it; unknown
    visibility (an unlistable process table, an exhausted budget, a process
    of this user that denies inspection) refuses. The reaper holds no handle
    inside the tree here: every file it hashed and every directory it listed
    is closed. This narrows the window between the guards and removal; it
    cannot close it (runbook: residual risk).
    """
    try:
        current = _manifest(tree)
    except OSError:
        return "content unreadable"
    if current != baseline:
        return "content changed since the pre-preservation manifest"
    budget = _effective_timeout(_CLEAN_PUSHED_PROBE_TIMEOUT_S)
    denied: list[int] = []
    users = _proc_users_inside(tree, deadline=time.monotonic() + (budget or 0.0), uninspectable=denied)
    if users is None:
        return "process visibility unknown"
    if users:
        return "in use: a process works inside the checkout"
    if denied:
        return f"{UNINSPECTABLE_PROCESS} {denied[0]}: a process of this user cannot be inspected"
    return None


def _fsync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _write_quarantine_record(holder: Path, record: dict[str, Any]) -> None:
    """Durably replace ``holder``'s record: write and fsync a temporary file, rename it, fsync ``holder``."""
    temporary = holder / f"{QUARANTINE_RECORD}.tmp"
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, holder / QUARANTINE_RECORD)
    _fsync_directory(holder)


def _clear_quarantine(holder: Path) -> None:
    """Drop the record and the empty holder. A failure leaves a record with no checkout, which a later run clears.

    The record is kept while anything else is in the holder: a later run
    reports that entry instead of losing track of it (#10778).
    """
    with contextlib.suppress(OSError):
        if os.listdir(holder) != [QUARANTINE_RECORD]:
            return
        (holder / QUARANTINE_RECORD).unlink()
        holder.rmdir()
        _fsync_directory(holder.parent)


def _new_holder(root: Path, agent: str) -> Path:
    """A fresh 0700 holder with a 128-bit random name inside the private quarantine root."""
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = root.lstat()
    if _real_directory(root) is None or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise OSError("quarantine directory is not a private real directory")
    holder = root / f"{agent}-{secrets.token_hex(16)}"
    holder.mkdir(mode=0o700)
    _fsync_directory(root)
    return holder


def _move_back(primary: Path, staged: Path, original: Path) -> str | None:
    """Move ``staged`` to ``original`` by naming its parent: Git then refuses when ``original`` exists again.

    Naming ``original`` itself would move the checkout *into* a directory that
    reappeared there.
    """
    if staged.name != original.name:
        return "quarantined name differs from the original"
    return _move_worktree(primary, staged, original.parent)


def _settle_quarantine(
    primary: Path,
    holder: Path,
    staged: Path,
    original: Path,
    record: dict[str, Any],
    baseline: _Manifest,
    removal_started: bool,
) -> None:
    """After Git ran or a guard refused: clear, restore, or keep the quarantined checkout.

    Git removed it: clear the record. Git started and some entry is gone: keep
    the remains in the quarantine (the record stays ``removing``). Otherwise
    nothing was deleted: mark the record restorable and move the checkout back,
    never over a path that exists again.
    """
    if not os.path.lexists(staged):
        _clear_quarantine(holder)
        return
    if removal_started and _missing_entries(staged, baseline):
        raise RuntimeError("git removal stopped partway; the remains are kept in the quarantine (runbook)")
    with contextlib.suppress(OSError):  # left at ``removing``, a later run keeps the checkout
        _write_quarantine_record(holder, record)
    if os.path.lexists(original):
        raise RuntimeError(f"cannot move the checkout back: {original.name} exists again; kept in quarantine")
    failure = _move_back(primary, staged, original)
    if failure is not None:
        raise RuntimeError(f"cannot move the checkout back ({failure}); it is kept in the quarantine")
    _clear_quarantine(holder)


def _quarantine_stager(
    primary: Path,
    original: Path,
    verify: Callable[[Path], str | None],
    baseline: Callable[[], _Manifest | None],
) -> worktree_claims.RemovalStager:
    """Move the checkout out of reach, re-run every guard there, then one final re-check (#10778).

    Before the move a record of the checkout's original path and directory
    identity is written durably into the holder, so a later run can recover
    from a crash at any point. After the move no dispatch, shell or worker
    reaches the checkout by its known path, and a process already inside
    shows the quarantine path in ``/proc``. Every guard runs again on the
    quarantined path; the record then turns ``removing`` and
    :func:`_final_recheck` compares the tree with ``baseline()`` (taken
    before artifact preservation) and looks for holders once more,
    immediately before Git. A refusal, or a checkout Git did not remove, is
    moved back to ``original`` (:func:`_settle_quarantine`).
    """

    @contextlib.contextmanager
    def stage(target: Path) -> Iterator[Path]:
        manifest = baseline()
        if manifest is None:
            raise worktree_claims.RemovalStageRefused("no pre-preservation manifest")
        holder: Path | None = None
        try:
            holder = _new_holder(primary / QUARANTINE_RELATIVE, original.parent.name)
            identity = target.lstat()
            record: dict[str, Any] = {
                "schema": _QUARANTINE_SCHEMA,
                "original": original.relative_to(primary.resolve()).as_posix(),
                "task": original.name,
                "dev": identity.st_dev,
                "ino": identity.st_ino,
                "stage": "intent",
                "at": reaper_lifecycle.utc_now().isoformat(),
            }
            _write_quarantine_record(holder, record)
        except (OSError, ValueError) as exc:
            if holder is not None:
                _clear_quarantine(holder)
            detail = exc.strerror if isinstance(exc, OSError) and exc.strerror else str(exc.args[0] if exc.args else "")
            raise worktree_claims.RemovalStageRefused(f"quarantine unavailable ({detail})") from None
        staged = holder / original.name
        failure = _move_worktree(primary, target, holder)
        if failure is not None:
            if os.path.lexists(staged) or not os.path.lexists(target):
                raise RuntimeError(f"{failure}; checkout state after the failed move needs inspection")
            _clear_quarantine(holder)
            raise worktree_claims.RemovalStageRefused(failure)
        removal_started = False
        try:
            _fsync_directory(holder)
            _fsync_directory(original.parent)
            refusal = verify(staged)
            if refusal:
                raise worktree_claims.RemovalStageRefused(f"{LATE_CHANGE}: {refusal}")
            _write_quarantine_record(holder, {**record, "stage": "removing"})
            refusal = _final_recheck(staged, manifest)
            if refusal:
                raise worktree_claims.RemovalStageRefused(f"{LATE_CHANGE}: final re-check: {refusal}")
            removal_started = True
            yield staged
        finally:
            _settle_quarantine(primary, holder, staged, original, record, manifest, removal_started)

    return stage


def _read_quarantine_record(holder: Path) -> dict[str, Any] | None:
    """The holder's record when it is a regular file of the current schema naming a dispatch path; else ``None``."""
    path = holder / QUARANTINE_RECORD
    try:
        if not stat.S_ISREG(path.lstat().st_mode):
            return None
        record = json.loads(path.read_bytes())
    except (OSError, ValueError, RecursionError):
        return None
    if not isinstance(record, dict) or record.get("schema") != _QUARANTINE_SCHEMA:
        return None
    original, task = record.get("original"), record.get("task")
    if not isinstance(original, str) or not isinstance(task, str) or record.get("stage") not in _QUARANTINE_STAGES:
        return None
    if not all(isinstance(record.get(key), int) and not isinstance(record.get(key), bool) for key in ("dev", "ino")):
        return None
    parts = Path(original).parts
    if len(parts) != 4 or parts[:2] != (".worktrees", "dispatch") or parts[3] != task:
        return None
    if any(part in {"", ".", ".."} or "/" in part for part in parts) or "/" in task:
        return None
    return record


def _restore_refusal(
    record: dict[str, Any], staged: Path, original: Path, registered: dict[Path, WorktreeInfo], ctx: _CleanPushedContext
) -> str | None:
    """Why a quarantined checkout may not be moved back; ``None`` when every restore guard passes."""
    if record["stage"] != "intent":
        return "Git removal may have started, so it may be partially deleted"
    if _real_directory(staged) is None:
        return "not a real directory"
    try:
        info = staged.lstat()
    except OSError:
        return "unreadable"
    if (info.st_dev, info.st_ino) != (record["dev"], record["ino"]):
        return "directory identity differs from the record"
    entry = registered.get(staged.resolve())
    if entry is None:
        return "not a registered worktree"
    if entry.locked_reason is not None:
        return "git worktree is locked"
    if os.path.lexists(original):
        return "its original path exists again and is never overwritten"
    if original.parent.parent != ctx.dispatch_root or _real_directory(original.parent) is None:
        return "its original parent directory is missing or not a real directory"
    return None


def _recover_quarantine(
    primary: Path, ctx: _CleanPushedContext, listing: list[WorktreeInfo], *, control_root: Path, dry_run: bool
) -> tuple[list[CleanPushedOutcome], set[Path], bool]:
    """Judge what an interrupted run left in ``.worktrees/.reaping/`` (#10778).

    A checkout whose record says Git removal never started is moved back,
    under delegate's per-worktree lock of its original path, when every
    restore guard passes (:func:`_restore_refusal`). Everything
    else is kept and reported: no or an unreadable record, removal possibly
    started, another directory under the recorded name, an occupied
    original path. A record left with no checkout is cleared. Returns
    ``(outcomes, paths judged, whether a checkout moved)``.
    """
    root = primary.resolve() / QUARANTINE_RELATIVE
    outcomes: list[CleanPushedOutcome] = []
    handled: set[Path] = set()
    if not os.path.lexists(root):
        return outcomes, handled, False
    registered = {info.path.resolve(): info for info in listing}
    if _real_directory(root) is None:
        handled.update(path for path in registered if path.parent.parent == root)
        reason = "quarantine: the quarantine directory is not a real directory; inspect it (runbook)"
        return (
            [CleanPushedOutcome(path=_display_path(root, primary.resolve()), action="skipped", reason=reason)],
            handled,
            False,
        )
    moved = False
    for holder in sorted(root.iterdir()):
        handled.update(path for path in registered if path.parent == holder)

        def keep(why: str, where: Path = holder) -> None:
            outcomes.append(
                CleanPushedOutcome(
                    path=_display_path(where, primary.resolve()),
                    action="skipped",
                    reason=f"quarantine: {why}; inspect it (runbook)",
                )
            )

        if holder.is_symlink() or not holder.is_dir():
            keep("not a directory")
            continue
        record = _read_quarantine_record(holder)
        if record is None:
            keep("no readable quarantine record")
            continue
        staged = holder / record["task"]
        original = primary.resolve() / record["original"]
        try:
            contents = set(os.listdir(holder))
        except OSError:
            keep("unreadable holder")
            continue
        if contents - {QUARANTINE_RECORD, record["task"]}:
            keep("unexpected entries next to the record")
            continue
        if not os.path.lexists(staged):
            if not dry_run:
                _clear_quarantine(holder)
            continue
        refusal = _restore_refusal(record, staged, original, registered, ctx)
        if refusal:
            keep(f"kept: {refusal}", staged)
            continue
        handled.add(original)
        shown = _display_path(original, primary.resolve())
        if dry_run:
            reason = "would restore it from the reaper quarantine (interrupted run)"
            outcomes.append(CleanPushedOutcome(path=shown, action="skipped", reason=reason))
            continue
        try:
            with worktree_claims.worktree_lock(
                original,
                lock_dir=worktree_claims.repository_lock_dir(control_root),
                timeout_s=_CLEAN_PUSHED_WORKTREE_LOCK_TIMEOUT_S,
            ):
                refusal = _restore_refusal(record, staged, original, registered, ctx)
                failure = refusal or _move_back(primary, staged, original)
        except worktree_claims.WorktreeLockError as exc:
            failure = worktree_claims.lock_refusal(exc)
        if failure is not None:
            keep(f"restore failed: {failure}", staged)
            continue
        moved = True
        _clear_quarantine(holder)
        reason = "restored from the reaper quarantine (interrupted run); kept this run"
        try:
            reaper_lifecycle.append_journal(primary, "clean-pushed-restored", path=shown)
        except OSError as exc:
            reason += f"; journal write failed ({exc})"
        outcomes.append(CleanPushedOutcome(path=shown, action="skipped", reason=reason))
    return outcomes, handled, moved


def reap_clean_pushed(
    *,
    repo_root: Path | None = None,
    dry_run: bool = True,
    actor: str = DEFAULT_CLEAN_PUSHED_ACTOR,
    lock_timeout_s: float | None = None,
) -> CleanPushedReport:
    """Remove clean, fully pushed, idle dispatch worktrees; dry run by default (#10778).

    First ``git fetch --prune origin`` refreshes local objects and
    ``git ls-remote --heads --tags origin`` takes the census that alone
    proves publication (:class:`_OriginCensus`), both outside the reaper
    lock; if either fails the run does nothing (``refs_stale``). A
    registered checkout is then removed only when all of
    these hold, each checked again under delegate's per-worktree lock
    immediately before removal: it is exactly
    ``.worktrees/dispatch/<agent>/<task>/`` (not ACP, not a symlink, not
    locked, not reserved); ``git status --porcelain --untracked-files=all``
    is empty and no assume-unchanged or skip-worktree file on disk differs
    from the index; HEAD and every object its private git directory records
    (per-worktree refs, every reflog, pseudorefs) are commits that are
    ancestors of an advertised origin head or tag present locally (unproven while an advertised object is missing:
    ``refs_stale``); neither ``fuser`` nor the process table shows a user, and no
    live process of this user denies inspection (a probe failure counts as
    in use; an uninspectable process keeps every tree for the run); no task
    record claiming it is ``spawning``, ``running``, unsettled, unreadable or
    has a live worker; and its HEAD, index and claiming task records are all
    older than 60 minutes. Removal goes through
    :func:`worktree_claims.remove_unclaimed_worktree` without ``force``, so
    the shared claim scan and ignored-output preservation (256 MiB cap) still
    apply. Right before git removes it, the checkout is recorded and moved to
    ``.worktrees/.reaping/``, every guard runs again there, and one final
    re-check compares it with its pre-preservation manifest and scans for
    holders (:func:`_quarantine_stager`); a change since the last check
    (``late_change``) moves it back. What an interrupted run left in the
    quarantine is judged first (:func:`_recover_quarantine`). A failed
    removal is reported and never retried. Each removal is journalled as intent and
    as confirmed, then appended to ``batch_state/worktree-abandon-log.jsonl``.
    Branches are never touched.

    The whole run holds the reaper lock; if another cleanup holds it for
    ``lock_timeout_s`` (default :data:`DEFAULT_REAP_LOCK_TIMEOUT_S`) the run
    does nothing and reports ``lock_busy``.
    """
    primary = primary_checkout_root((repo_root or resolve_repo_root()).resolve())

    def refused(reason: str, *, busy: bool = False, stale: bool = False) -> CleanPushedReport:
        return CleanPushedReport(
            dry_run=dry_run, removed=(), skipped=(), freed_mb=0, lock_busy=busy, refusal=reason, refs_stale=stale
        )

    if not dry_run and os.environ.get("LU_REAPER_DISABLED") == "1":
        return refused("reaper disabled by LU_REAPER_DISABLED=1")
    fetch_failure = _refresh_origin_refs(primary)
    if fetch_failure is not None:
        return refused(f"{REFS_STALE}: {fetch_failure}", stale=True)
    census, census_failure = _origin_census(primary)
    if census is None:
        return refused(f"{REFS_STALE}: {census_failure}", stale=True)
    try:
        lock = _ReapLock(primary, timeout_s=lock_timeout_s)
        lock.__enter__()
    except _ReapLockBusy as exc:
        return refused(str(exc), busy=True)
    except RuntimeError as exc:
        return refused(str(exc))
    removed: list[CleanPushedOutcome] = []
    skipped: list[CleanPushedOutcome] = []
    late: list[str] = []
    try:
        try:
            control_root = worktree_claims.control_plane_root(primary)
            common_git_dir = _common_git_dir(primary)
            listing = list_git_worktrees(primary, resolve_paths=False)
        except (worktree_claims.ControlPlaneError, RuntimeError) as exc:
            return refused(str(exc))
        tasks_dir = control_root / "batch_state" / "tasks"
        ctx = _CleanPushedContext(
            primary=primary,
            dispatch_root=primary.resolve() / ".worktrees" / "dispatch",
            common_git_dir=common_git_dir,
            tasks_dir=tasks_dir,
            index=_build_task_index(tasks_dir, primary),
            census=census,
        )
        recovered, handled, moved = _recover_quarantine(
            primary, ctx, listing, control_root=control_root, dry_run=dry_run
        )
        skipped.extend(recovered)
        if moved:
            try:
                listing = list_git_worktrees(primary, resolve_paths=False)
            except RuntimeError as exc:
                return refused(str(exc))
        for info in listing:
            if info.path.resolve() in handled:
                continue
            shown = _display_path(info.path, primary)
            claims = list(ctx.index.by_path.get(info.path.resolve(), ()))
            refusal, claims = _clean_pushed_refusal(info, ctx, claims, recheck=False)
            outcome = CleanPushedOutcome(
                path=shown,
                action="skipped",
                reason=refusal or CLEAN_PUSHED_REASON,
                head=info.head,
                branch=info.branch,
                task_status=_task_status(claims),
            )
            if refusal:
                skipped.append(outcome)
                continue
            outcome = replace(outcome, size_mb=_tree_size_mb(info.path))
            if dry_run:
                removed.append(replace(outcome, action="would_remove"))
                continue

            def guards(
                tree: Path | None = None, info: WorktreeInfo = info, claims: list[_TaskClaim] = claims
            ) -> str | None:
                try:
                    with _bounded_locked_git():
                        why, _ = _clean_pushed_refusal(info, ctx, claims, recheck=True, tree=tree)
                except subprocess.TimeoutExpired:
                    why = "re-check timed out"
                return why

            baseline: dict[str, _Manifest] = {}

            def recheck(
                guards: Callable[[], str | None] = guards,
                info: WorktreeInfo = info,
                baseline: dict[str, _Manifest] = baseline,
            ) -> tuple[bool, str]:
                why = guards()
                if why:
                    return False, f"re-check: {why}"
                # Under the per-worktree lock and before artifact preservation:
                # what the final re-check compares the quarantined tree with.
                try:
                    baseline["tree"] = _manifest(info.path)
                except OSError:
                    return False, "re-check: content unreadable"
                return True, ""

            def taken(baseline: dict[str, _Manifest] = baseline) -> _Manifest | None:
                return baseline.get("tree")

            try:
                reaper_lifecycle.append_journal(
                    primary,
                    "clean-pushed-remove",
                    stage="intent",
                    path=shown,
                    head=info.head,
                    branch=info.branch,
                    task_status=outcome.task_status,
                    size_mb=outcome.size_mb,
                )
            except OSError as exc:
                skipped.append(replace(outcome, action="error", reason=f"journal write failed ({exc}); run stopped"))
                break
            removal = worktree_claims.remove_unclaimed_worktree(
                info.path,
                repo_root=primary,
                reason=CLEAN_PUSHED_REASON,
                owner_task_id=None,
                releasable=recheck,
                force=False,
                control_root=control_root,
                tasks_dir=tasks_dir,
                lock_timeout_s=_CLEAN_PUSHED_WORKTREE_LOCK_TIMEOUT_S,
                settled_claim=_worker_proven_gone,
                stage_removal=_quarantine_stager(primary, info.path, guards, taken),
            )
            if removal.action != "removed":
                detail = f"{removal.reason}: {removal.error}" if removal.error else removal.reason
                if detail.startswith(worktree_claims.REMOVAL_STAGE_REFUSED):
                    detail = detail.removeprefix(worktree_claims.REMOVAL_STAGE_REFUSED)
                    if detail.startswith(LATE_CHANGE):
                        late.append(shown)
                skipped.append(
                    replace(outcome, action="error" if removal.action == "error" else "skipped", reason=detail)
                )
                continue
            entry = {
                "ts": reaper_lifecycle.utc_now().isoformat(),
                "actor": actor,
                "path": shown,
                "head": info.head,
                "branch": info.branch,
                "task_status": outcome.task_status,
                "reason": CLEAN_PUSHED_REASON,
                "size_mb": outcome.size_mb,
            }
            try:
                reaper_lifecycle.append_journal(primary, "clean-pushed-removed", stage="confirmed", path=shown)
                append_abandon_log(control_root, entry)
            except OSError as exc:
                skipped.append(
                    replace(outcome, action="error", reason=f"removed, but log write failed ({exc}); run stopped")
                )
                break
            removed.append(replace(outcome, action="removed"))
    finally:
        lock.__exit__(None, None, None)
    return CleanPushedReport(
        dry_run=dry_run,
        removed=tuple(removed),
        skipped=tuple(skipped),
        freed_mb=sum(outcome.size_mb or 0 for outcome in removed),
        uninspectable=tuple(sorted(ctx.uninspectable)),
        late_change=tuple(late),
        unpublished_reflog_commit=tuple(
            outcome.path for outcome in skipped if UNPUBLISHED_REFLOG_COMMIT in outcome.reason
        ),
        census_refs=census.refs,
        census_missing=census.missing,
    )


def format_clean_pushed_report(report: CleanPushedReport) -> str:
    mode = "DRY RUN" if report.dry_run else "APPLY"
    verb = "would remove" if report.dry_run else "removed"
    if report.refusal:
        return f"{mode} clean-pushed: nothing done: {report.refusal}"
    errors = sum(1 for outcome in report.skipped if outcome.action == "error")
    lines = [
        f"{mode} clean-pushed: {len(report.removed)} {verb} ({report.freed_mb} MB), "
        f"{len(report.skipped) - errors} skipped, {errors} error(s); origin refs refreshed (git fetch --prune origin); "
        f"origin census: {report.census_refs} heads and tags (git ls-remote), {report.census_missing} missing locally"
    ]
    if report.uninspectable:
        lines.append(f"{UNINSPECTABLE_PROCESS}: pid(s) {', '.join(map(str, report.uninspectable))}; every tree kept")
    for outcome in (*report.removed, *report.skipped):
        lines.append(
            f"{outcome.action.upper()} {outcome.path} branch={outcome.branch or '-'} "
            f"task_status={outcome.task_status or '-'} size_mb={outcome.size_mb if outcome.size_mb is not None else '-'} "
            f"reason={outcome.reason}"
        )
    return "\n".join(lines)


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
    attention = sum(1 for result in results if result.needs_attention is not None)
    mode = "APPLY" if apply else "DRY RUN"
    summary = f"{mode}: {candidates} candidate(s), {skipped} skipped, {errors} error(s)"
    if attention:
        summary = f"{summary}, {attention} need(s) attention"
    lines = [summary]
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
        "needs_attention": 0,
    }
    by_owner: dict[str, int] = {}
    reaped = 0
    reaped_by_owner: dict[str, int] = {}
    retained_exceptions = 0
    needs_attention: list[dict[str, Any]] = []

    for r in results:
        if r.needs_attention is not None:
            needs_attention.append(
                {"path": r.path, "kind": r.needs_attention.get("kind"), "command": r.needs_attention.get("command")}
            )
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
        "needs_attention": needs_attention,
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
    attention = counts.get("needs_attention") or []
    if attention:
        lines.append("  Needs attention (never removed automatically):")
        for item in attention:
            lines.append(f"    {item['kind']}: {item['path']}")
            lines.append(f"      {item['command']}")
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
            "Use for completed-work cleanup; active or unverifiable worktrees are preserved.\n"
            "Also reaps clean, pushed review checkouts: superseded open-PR heads, detached\n"
            "checkouts with no task record older than 2h, and registered /tmp or scratchpad checkouts."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.orchestration.reap_worktrees --dry-run\n"
            "  .venv/bin/python -m scripts.orchestration.reap_worktrees --apply --merged\n"
            "  .venv/bin/python -m scripts.orchestration.reap_worktrees --clean-pushed [--apply]\n"
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
        help=(
            "Preserve dirty eligible worktrees before removing them. Verified terminal-abandon copies "
            "current files without changing HEAD; other classes commit locally with --no-verify."
        ),
    )
    parser.add_argument(
        "--prune-merged-branches",
        action="store_true",
        help=("Delete a local branch only after its MERGED PR head SHA exactly matches the removed worktree HEAD."),
    )
    parser.add_argument(
        "--safe-only",
        action="store_true",
        help="Restrict reaping to provably-safe classes (merged PRs + settled dispatches + detached-HEAD ancestors + clean pushed detached dispatch checkouts); excludes owner abandonment.",
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
        help="Enable non-merged cleanup classes for an explicit manual run, including verified owner abandonment unless --safe-only is set.",
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
    parser.add_argument(
        "--clean-pushed",
        action="store_true",
        help=(
            "Only remove dispatch worktrees that are clean, have no untracked files, have every commit "
            "on origin, are used by no process or live task, and were idle for 60 minutes (#10778). "
            "Dry run unless --apply; never forces; never deletes branches."
        ),
    )
    parser.add_argument(
        "--actor",
        default=DEFAULT_CLEAN_PUSHED_ACTOR,
        help="Actor recorded in batch_state/worktree-abandon-log.jsonl by --clean-pushed --apply.",
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
    merged_mode = bool(args.merged) or (not bool(args.legacy_classes) and not bool(args.terminal_dispatches))
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

    if args.clean_pushed:
        status = 0
        for repo_root in repo_roots:
            report = reap_clean_pushed(repo_root=repo_root, dry_run=not apply, actor=args.actor)
            print(json.dumps(report.as_dict(), indent=2) if args.json else format_clean_pushed_report(report))
            if any(outcome.action == "error" for outcome in report.skipped):
                status = 1
            elif report.refusal and not (
                report.lock_busy or report.refs_stale or report.refusal.startswith("reaper disabled")
            ):
                status = 2
        return status

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
