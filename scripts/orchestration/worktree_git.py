"""Git, GitHub and worktree-activity helpers shared by the cleanup tools.

These are the pieces of the retired worktree reaper that live code still uses:
worktree listing, sanitized git calls, pull-request lookup and scoping,
merge-proof helpers, branch pruning and the task-activity probes. The
dispatcher removes each task's own worktree at settlement; nothing here
removes a worktree.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit

from scripts.common import github_client
from scripts.control_plane.storage import StoreId
from scripts.control_plane.storage import connect as cp_connect
from scripts.orchestration import reaper_lifecycle, worktree_artifacts, worktree_claims
from scripts.orchestration.dead_worker_state import worker_liveness
from scripts.orchestration.execution_safe_git import COMMIT_COMMANDS, REMOTE_COMMANDS
from scripts.orchestration.execution_safe_git import run_git as safe_git
from scripts.orchestration.fleet_repos import canonical_repository, pull_request_repository

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
    repository: str | None = None


@dataclass(frozen=True)
class PullRequestState:
    number: int | None
    state: str
    head_sha: str | None = None
    head_from_commit_search: bool = False
    repository: str | None = None


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
    repository, whose dispatch state lives on the public primary (#8624). It
    falls back to the repository's own primary when the fleet catalog is
    unreadable.
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
    repository = _pr_repository(repo_root)
    return [
        replace(info, repository=repository)
        for info in parse_worktree_porcelain(proc.stdout or "", resolve_paths=resolve_paths)
    ]


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


def _pr_repository(repo_root: Path) -> str | None:
    slug = _github_owner_repo(repo_root)
    return canonical_repository("/".join(slug)) if slug else None


def _scope_pr_rows(
    rows: list[Any],
    repository: str | None,
    *,
    number: int | None = None,
) -> tuple[list[dict[str, Any]], str | None]:
    scoped = []
    for row in rows:
        try:
            actual = pull_request_repository(row, scoped_repository=repository)
        except (TypeError, ValueError) as exc:
            return [], str(exc)
        if repository is not None and actual != repository:
            return [], "PR payload repository does not match requested repository"
        if number is not None and row.get("number") != number:
            return [], "PR payload number does not match requested PR"
        scoped.append({**row, **({"repository": actual} if actual else {})})
    return scoped, None


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
            repository=pull_request_repository(item),
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
    rows, error = _scope_pr_rows([item for page in raw_items for item in page], _pr_repository(repo_root))
    if error:
        return [], error
    states: list[PullRequestState] = []
    for item in rows:
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
                "number,state,headRefOid,url",
                *(["--repo", repository] if (repository := _pr_repository(repo_root)) else []),
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

    raw_items, error = _scope_pr_rows(raw_items, _pr_repository(repo_root))
    if error:
        return [], error
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
            repository=pull_request_repository(item),
        ),
        None,
    )


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
    rows, error = _scope_pr_rows([item], _pr_repository(repo_root), number=number)
    if error or not rows:
        return [], error
    parsed, err = _parse_rest_pr_item(rows[0])
    if err is not None or parsed is None:
        return [], err or "REST PR lookup returned an unusable payload"
    return [parsed], None


def _best_pr(prs: list[PullRequestState]) -> PullRequestState | None:
    # A branch name can be reused. Any open PR is therefore authoritative over
    # historical merged/closed PRs for the same head name.
    for desired in ("OPEN", "MERGED", "CLOSED"):
        for pr_state in prs:
            if pr_state.state == desired:
                return pr_state
    return prs[0] if prs else None


def _sha_is_ancestor(cwd: Path, sha: str, descendant: str) -> bool:
    """True when ``sha`` is an ancestor of ``descendant``. A git error is not."""
    proc = _run(
        ["git", "merge-base", "--is-ancestor", sha, descendant],
        cwd=cwd,
    )
    return proc.returncode == 0


def _pr_belongs_to_checkout(info: WorktreeInfo, pr: PullRequestState) -> bool:
    return pr.repository is None or pr.repository == info.repository


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
    if not _pr_belongs_to_checkout(info, pr_state):
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
        or not _pr_belongs_to_checkout(info, pr)
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
    return _dispatch_task_id_for_path(repo_root, info.path)


def _dispatch_task_id_for_path(repo_root: Path, path: Path) -> str | None:
    dispatch_root = (repo_root / ".worktrees" / "dispatch").resolve()
    try:
        relative = path.resolve().relative_to(dispatch_root)
    except ValueError:
        return None
    return relative.parts[1] if len(relative.parts) == 2 else None


# Packet fields that may name the worktree path a live rollover protects.
# ``thread_handoff.source_checkout_binding`` historically recorded only the
# source HEAD SHA; matching on that SHA protected every sibling worktree
# created from the same commit, from any lane (#8536). Protection is by
# recorded path only: a packet that names no path protects nothing.
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
    probe_attachment_lock: bool = False,
) -> str | None:
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


class _ActiveTaskProbeFailure(RuntimeError):
    def __init__(self, reason: str, fallback_allowed: bool) -> None:
        super().__init__(reason)
        self.reason = reason
        self.fallback_allowed = fallback_allowed


def _active_task_ids() -> set[str] | None:
    import urllib.request

    for attempt in range(2):
        try:
            with urllib.request.urlopen("http://127.0.0.1:8765/api/delegate/active", timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if not isinstance(data, dict) or not isinstance(data.get("tasks"), list):
                    raise ValueError("activity response must contain a tasks list")
                tasks = data["tasks"]
                if any(
                    not isinstance(t, dict) or not isinstance(t.get("task_id"), str) or not t["task_id"] for t in tasks
                ):
                    raise ValueError("activity response contains an invalid task identity")
                return {t["task_id"] for t in tasks}
        except Exception as exc:
            transport = isinstance(exc, TimeoutError | ConnectionError) or (
                isinstance(exc, URLError) and not isinstance(exc, HTTPError)
            )
            if transport and attempt == 0:
                time.sleep(0.2)
                continue
            code = (
                "timeout" if isinstance(exc, TimeoutError) else "transport_error" if transport else "invalid_response"
            )
            raise _ActiveTaskProbeFailure(
                reason=f"active-task probe unavailable [active_task_probe_{code}]: {type(exc).__name__}: {exc}",
                fallback_allowed=transport,
            ) from exc


def _read_active_task_probe() -> set[str] | _ActiveTaskProbeFailure | None:
    """Keep typed failures for callers to resolve against the attributed checkout."""
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


def _preserved_merged_head_valid(
    info: WorktreeInfo, preservation: dict[str, Any], *, require_rescue: bool = True
) -> bool:
    """Verify the exact reaper snapshot, never treat it as a merged commit."""
    head = preservation.get("head_sha")
    tree = preservation.get("tree_sha")
    if (
        preservation.get("parent_sha") != info.head
        or not isinstance(head, str)
        or re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", head) is None
        or not isinstance(tree, str)
        or re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", tree) is None
        or worktree_claims.checked_out_branch(info.path) != info.branch
        or _worktree_clean(info.path) is not True
    ):
        return False
    identity = _run(["git", "rev-list", "--no-walk", "--format=%H%n%P%n%T", "HEAD"], cwd=info.path)
    if identity.returncode != 0 or identity.stdout.splitlines() != [f"commit {head}", head, info.head, tree]:
        return False
    if require_rescue:
        ref = preservation.get("recovery_ref")
        if not isinstance(ref, str) or not ref.startswith("refs/reaper-rescue/"):
            return False
        rescued = _run(["git", "rev-parse", "--verify", ref], cwd=info.path)
        if rescued.returncode != 0 or rescued.stdout.strip() != head:
            return False
    return True


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


def _same_branch_merged_cohort(
    info: WorktreeInfo,
    pr: PullRequestState | None,
    cohort: list[tuple[Path, dict[str, Any]]],
    *,
    preservation: dict[str, Any] | None = None,
) -> bool:
    """Settle inactive same-branch rounds without requiring a done successor."""
    expected_head = info.head
    if preservation is not None:
        if not _preserved_merged_head_valid(info, preservation):
            return False
        expected_head = preservation["head_sha"]
    if (
        not info.branch
        or not info.head
        or pr is None
        or pr.state != "MERGED"
        or pr.head_from_commit_search
        or not _pr_belongs_to_checkout(info, pr)
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
        and tip.stdout.strip() == expected_head
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
    preservation: dict[str, Any] | None = None,
) -> bool:
    """Prove an exact PR head, or a detached cohort's complete earlier lineage.

    Pending same-branch cohorts require a clean checkout at its branch tip,
    absent workers, and complete contained identities. Detached ancestry
    additionally requires a done successor at that checkout head. Missing
    Git objects and commit-search membership alone are never proof.
    A validated preservation binding changes only the expected live branch tip;
    merged ancestry still uses the original checkout head in ``info``.
    """
    if preservation is not None and not _preserved_merged_head_valid(info, preservation):
        return False
    if (
        pr is None
        or pr.state != "MERGED"
        or pr.head_from_commit_search
        or not _pr_belongs_to_checkout(info, pr)
        or not pr.head_sha
        or not info.head
    ):
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
        return _same_branch_merged_cohort(info, pr, cohort, preservation=preservation)
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
            info = WorktreeInfo(
                worktree,
                branch,
                head.stdout.strip(),
                detached=branch is None,
                repository=_pr_repository(worktree),
            )
            if (
                len(creators) != 1
                and len(cohort) >= 2
                and head.returncode == 0
                and branch
                and merged_pr.state == "MERGED"
                and not merged_pr.head_from_commit_search
                and _pr_belongs_to_checkout(info, merged_pr)
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
        PullRequestState(
            proof.get("pr_number"),
            proof.get("pr_state"),
            proof.get("pr_head_sha"),
            repository=proof.get("pr_repository"),
        )
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
    info = WorktreeInfo(
        worktree,
        branch,
        proof.get("head_sha"),
        detached=branch is None,
        repository=_pr_repository(worktree),
    )
    pr = PullRequestState(
        proof.get("pr_number"),
        proof.get("pr_state"),
        proof.get("pr_head_sha"),
        repository=proof.get("pr_repository"),
    )
    preservation = proof.get("preservation")
    expected_head = info.head
    if preservation is not None:
        if not isinstance(preservation, dict) or not _preserved_merged_head_valid(info, preservation):
            raise ValueError("merged continuation preservation head changed")
        expected_head = preservation["head_sha"]
    if (
        (pr.repository is not None and pr.repository != _pr_repository(worktree))
        or proof.get("owner") != creator.get("task_id")
        or proof.get("run_nonce") != creator.get("run_nonce")
        or head.returncode != 0
        or head.stdout.strip() != expected_head
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
            info,
            pr,
            cohort,
            allow_equivalent=proof.get("head_relation") == "patch-equivalent",
            preservation=preservation,
        )
    ):
        raise ValueError("merged continuation preservation proof changed")
    return path, creator


# ``git -c`` overrides that disable the maintenance fetch would otherwise run.
GIT_NO_AUTO_MAINTENANCE = ("-c", "maintenance.auto=false", "-c", "gc.auto=0")
