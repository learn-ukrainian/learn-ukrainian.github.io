"""Worktree creation and observational Git delivery reporting."""

import contextvars
import fcntl
import json
import os
import re
import shutil
import subprocess
import sys
from contextlib import contextmanager, suppress
from datetime import datetime
from functools import partial
from pathlib import Path, PurePosixPath

import yaml

from scripts.common.git_context import sanitized_git_env
from scripts.common.git_credentials import canonical_origins as canonical_origins
from scripts.common.git_credentials import verification_credentials
from scripts.common.repo_root import resolve_repo_root
from scripts.common.task_scratch import TaskScratchError, allocate
from scripts.common.task_store_paths import tasks_dir
from scripts.dispatcher import site_deps
from scripts.dispatcher.types import TaskSpec
from scripts.orchestration.execution_safe_git import run_git as execution_safe_git
from scripts.storage.topology import STORE_FILES

ROOT = resolve_repo_root(Path(__file__), 2)
CONFIG = Path(__file__).resolve().parents[1] / "config" / "fleet_repos.yaml"
# Default trees excluded from dispatch worktrees.
SPARSE_EXCLUDE_DEFAULT = frozenset({
    "curriculum", "wiki", "data/projects", "data/lexicon", "data/datasets", "data/processed",
    "registry/projects", "registry/lexicon/source-inventory",
    "registry/lexicon/source-inventory-review-decisions", "site/src/content", "site/src/data",
})
# Excluded trees a tool reads from the worktree when an owned path is this prefix
# or under it. Curriculum was measured by running the validator and the fresh-build
# engine: both open registry/lexicon/source-inventory, and the engine opens
# site/src/content for built lesson pages. data/lexicon stays excluded; the evidence
# reader uses the primary checkout when the worktree has no copy.
OWNED_PATH_INPUTS = {
    "curriculum": frozenset({"registry/lexicon/source-inventory", "site/src/content"}),
    "tests/projects/open_model_data": frozenset({"data/projects"}),
    "scripts/projects/open_model_data": frozenset({"data/projects"}),
}
GIT_BINARY = shutil.which("git", path=os.defpath)
# Bound for each explicit fetch of the ownership walk. On the 8 GB public repository
# the bounded fetch measured about one second and the blob-less full-history fallback
# about three; 60 seconds leaves headroom for a slow link without hanging a settling task.
VERIFICATION_FETCH_TIMEOUT = 60
# Committer-clock slack below the task start date. Speed depends on this value;
# correctness does not, because _complete_since_task_base checks the fetched graph.
HISTORY_SLACK_SECONDS = 86400


def _verification_git(path: Path, *args: str, strip: bool = True, git_dir: Path | None = None,
                      timeout: float = 30, credential_remote: str | None = None) -> str:
    """Use the system Git with no inherited Git configuration or process redirects."""
    if not GIT_BINARY:
        raise ValueError("system Git unavailable")
    env = {key: os.environ[key] for key in ("HOME", "SSH_AUTH_SOCK", "GH_CONFIG_DIR", "XDG_CONFIG_HOME")
           if key in os.environ}
    env.update(PATH=os.defpath, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull,
               GIT_CONFIG_NOSYSTEM="1", GIT_TERMINAL_PROMPT="0", LC_ALL="C")
    credentials = verification_credentials(credential_remote) if credential_remote else []
    try:
        output = subprocess.run(
            [GIT_BINARY, "--no-replace-objects", "-c", "core.alternateRefsCommand=",
             "-c", f"core.hooksPath={os.devnull}", "-c", "protocol.ext.allow=never",
             *(arg for setting in credentials for arg in ("-c", setting)),
             *([f"--git-dir={git_dir}"] if git_dir else []), "-C", str(path), *args],
            capture_output=True, text=True, check=True, timeout=timeout, env=env,
        ).stdout
    except subprocess.CalledProcessError as exc:
        # Neither transport/helper output nor a credential-bearing URL may
        # become a delivery error, traceback, or durable task record.
        raise subprocess.CalledProcessError(exc.returncode, [GIT_BINARY, args[0]],
                                            output="", stderr="isolated Git command failed") from None
    except subprocess.TimeoutExpired as exc:
        raise subprocess.TimeoutExpired([GIT_BINARY, args[0]], exc.timeout) from None
    return output.strip() if strip else output


def verification_origin(path: Path) -> str:
    entries = [entry.partition("\n") for entry in
               _verification_git(path, "config", "--null", "--includes", "--list", strip=False).split("\0") if entry]
    if any(key.startswith("alias.") or (key.startswith("url.") and
           key.endswith((".insteadof", ".pushinsteadof"))) for key, _, _ in entries):
        raise ValueError("worker Git aliases or URL rewrites cannot be verified")
    urls = [value for key, _, value in entries if key == "remote.origin.url"]
    if len(urls) != 1 or not urls[0] or urls[0].startswith("-"):
        raise ValueError("ownership verification requires one origin URL")
    return urls[0]


def _complete_since_task_base(run, shallow: Path, task_base: str) -> bool:
    """Whether the fetched graph is enough to walk the delivery above the task start.

    Callers walk from the delivery tip, excluding the task start and a merge base
    with the base tip. Single-parent commits are diffed against their parent and
    merges are re-run, which recomputes the merge bases of their parents.

    Every commit the walk inspects needs its real parents. A bounded fetch records
    each shallow boundary commit without parents, so no boundary may lie on a
    tip's path above the task start. A boundary parent is itself present with its
    tree, so a single-parent diff against it is exact, and a merge base found in
    the bounded graph is a real common ancestor of the delivery and the base tip.

    A merge in the inspected range needs the complete ancestry of its parents to
    be recomputed. A graph with shallow boundaries does not provide it, so a
    delivery with any merge above the task start requires non-shallow history.
    """
    tips = ("refs/heads/delivery", "refs/heads/base")
    if task_base not in run("rev-list", *tips).split():
        return False
    if run("rev-parse", "--is-shallow-repository") == "false":
        return True
    return (set(shallow.read_text().split()).isdisjoint(run("rev-list", *tips, "--not", task_base).split())
            and not run("rev-list", "--min-parents=2", "refs/heads/delivery", "--not", task_base))


@contextmanager
def _private_remote_git(task_id: str, remote: str):
    """Use one recorded URL in the ownership verifier's private Git namespace."""
    scratch = allocate(task_id + "-ownership")
    try:
        run = partial(_verification_git, scratch.payload_dir, git_dir=scratch.payload_dir, credential_remote=remote)
        run("init", "--bare", "--template=")
        for key, value in (("maintenance.auto", "false"),
                           ("remote.origin.url", remote), ("remote.origin.promisor", "true"),
                           ("remote.origin.partialCloneFilter", "blob:none"),
                           ("extensions.partialClone", "origin")):
            run("config", key, value)
        yield run, scratch.payload_dir
    finally:
        try:
            scratch.remove()
        finally:
            scratch.preserve()


class OriginBaseRequired(ValueError):
    """``ref`` is not the ``origin/<branch>`` form ownership verification accepts."""


def verifiable_origin_base(ref: str) -> str:
    """The base ownership verification accepts: ``refs/remotes/`` stripped, then ``origin/<branch>``.

    A commit SHA, a local branch name, and any other ref raise ``OriginBaseRequired``.
    Dispatch refuses a workspace-write ``--base`` with this check instead of copying it.
    """
    base = ref.removeprefix("refs/remotes/")
    if not base.startswith("origin/"):
        raise OriginBaseRequired("ownership verification requires an origin base")
    return base


@contextmanager
def ownership_git(record: dict):
    """Walk trusted remote objects in a private config/ref namespace.

    A command-line include.path override is not a local-config sandbox. A fresh
    bare Git directory excludes both worker config and config.worktree,
    their includes, grafts and replacement refs. Objects and refs come only from
    the remote URL recorded before provider execution. No local objects are reused.

    The transfer is blob-less and starts at the task start date, so it stays small
    on a multi-gigabyte repository. Blobs are fetched lazily from the same URL only
    when a merge must be re-run. If a remote tip is dated before the cutoff (clock
    skew), that bounded history does not reach the task start on every path, or the
    delivery contains a merge, the full blob-less history is fetched instead and
    must leave the repository unshallow.

    The explicit fetches get VERIFICATION_FETCH_TIMEOUT. Lazy blob transfers run
    inside the caller's commands and share those commands' 30-second timeout.
    """
    remote = record["worktree_remote_url"]
    if verification_origin(Path(record["worktree_path"])) != remote:
        raise ValueError("origin URL changed since dispatch")
    base = verifiable_origin_base(record["worktree_base_ref"])
    task_base = record.get("worktree_start_sha", record["worktree_base_sha"])
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", task_base):
        raise ValueError("task base must be a full object name")
    delivery_ref = f"refs/heads/{record['worktree_branch']}"
    allowed_refs = {delivery_ref}
    if record.get("publish_branch") is not None:
        allowed_refs.add(f"refs/heads/{record['publish_branch']}")
    # Ignore unrecorded branch names so an observed ref cannot widen delivery trust.
    if record.get("remote_ref") in allowed_refs:
        delivery_ref = record["remote_ref"]
    base_ref = f"refs/heads/{base.removeprefix('origin/')}"
    # Distinct refs are required to keep the base independent of the delivery.
    if delivery_ref == base_ref:
        raise ValueError("delivery ref must differ from base ref")
    refspecs = (f"+{base_ref}:refs/heads/base",
                f"+{delivery_ref}:refs/heads/delivery")
    with _private_remote_git(record["task_id"], remote) as (run, git_dir):
        fetch = partial(run, "fetch", "--no-tags", "--no-write-fetch-head", "--filter=blob:none",
                        timeout=VERIFICATION_FETCH_TIMEOUT)
        fetch("--depth=1", "--", "origin", task_base, *refspecs)
        since = int(run("show", "-s", "--format=%ct", task_base)) - HISTORY_SLACK_SECONDS
        # Git selects no history below a tip dated before the cutoff and aborts the
        # bounded fetch; its message does not reach HTTPS clients, so decide by date.
        bounded = min(map(int, run("show", "-s", "--format=%ct", "refs/heads/base",
                                   "refs/heads/delivery").split())) >= since
        if bounded:
            fetch(f"--shallow-since=@{since}", "--", "origin", *refspecs)
        shallow = git_dir / "shallow"
        if not (bounded and _complete_since_task_base(run, shallow, task_base)):
            if run("rev-parse", "--is-shallow-repository") == "false":
                raise ValueError("task base is not reachable from the remote tips")
            fetch("--unshallow", "--", "origin", *refspecs)
            if run("rev-parse", "--is-shallow-repository") != "false":
                raise ValueError("full history could not be fetched")
            if not _complete_since_task_base(run, shallow, task_base):
                raise ValueError("task base is not reachable from the remote tips")
        if run("rev-parse", "--verify", "refs/heads/delivery^{commit}") != record["head_sha"]:
            raise ValueError("remote delivery tip does not match snapshot")
        yield run


def sparse_excludes(includes=(), owned_paths=()) -> list[str]:
    includes = {name.strip().strip("/") for name in includes}
    if includes - SPARSE_EXCLUDE_DEFAULT:
        raise ValueError("--sparse-include must name a default-excluded tree: " + ", ".join(sorted(SPARSE_EXCLUDE_DEFAULT)))
    for raw in owned_paths:
        path = PurePosixPath(raw.strip().replace("\\", "/"))
        if path.is_absolute() or ".." in path.parts:
            continue
        literal = []
        for part in path.parts:
            if any(char in part for char in "*?["):
                break
            literal.append(part)
        if not literal:
            continue
        root = "/".join(literal)
        includes.update(tree for tree in SPARSE_EXCLUDE_DEFAULT
                        if root == tree or root.startswith(tree + "/") or tree.startswith(root + "/"))
        for prefix, trees in OWNED_PATH_INPUTS.items():
            if root == prefix or root.startswith(prefix + "/"):
                includes.update(trees)
    return sorted(SPARSE_EXCLUDE_DEFAULT - includes)


def _git(path: Path, *args: str, isolate: bool = False, strip: bool = True, env: dict | None = None) -> str:
    output = subprocess.run(
        ["git", "-C", str(path), *args],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
        env={**(sanitized_git_env(strip_config_injection=True) if isolate else os.environ), "GIT_TERMINAL_PROMPT": "0",
             **(env or {})},
    ).stdout
    return output.strip() if strip else output


def resolve_repo(key: str | None = None) -> tuple[Path, dict]:
    repos = yaml.safe_load(CONFIG.read_text())["repos"]
    key = key or next(name for name, item in repos.items() if item.get("default"))
    if key not in repos:
        raise ValueError("unknown repository key")
    item = {**repos[key], "key": key}
    return (ROOT if item.get("default") else ROOT.parent / item["local_name"]).resolve(), item


def publish_start(repo: Path, repository: dict, branch: str, task_id: str) -> tuple[str, str]:
    """Start published fix rounds at origin's tip without moving the local PR branch."""
    remote = verification_origin(repo)
    if remote not in canonical_origins(repository):
        raise ValueError("publish branch origin must match the registered canonical repository URL")
    source = f"refs/heads/{branch}"
    with _private_remote_git(task_id, remote) as (run, _):
        try:
            advertised = run("ls-remote", "--exit-code", "--heads", "--", "origin", source)
        except subprocess.CalledProcessError as exc:
            if exc.returncode != 2:
                raise
            raise ValueError("publish branch is absent from the canonical remote") from None
        fields = advertised.split()
        if len(fields) != 2 or fields[1] != source or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", fields[0]):
            raise ValueError("publish branch must advertise one full object name")
        sha = fields[0]
    # Materialize the immutable advertised object, never a worker-writable ref.
    # Shared URL rewrites can make this transfer fail, but cannot change its SHA.
    _verification_git(repo, "fetch", "--no-tags", "--no-write-fetch-head", "--", remote,
                      sha, timeout=VERIFICATION_FETCH_TIMEOUT, credential_remote=remote)
    return sha, remote


def worktree_plan(repo: Path, agent: str, task_id: str, base: str, cwd=None, worktree=None, *, exact=False):
    branch = f"{agent}/{task_id}"
    parent = repo / ".worktrees" / "dispatch" / agent
    path = Path(cwd or worktree or parent / task_id).absolute()
    resolved = path.resolve()
    if not resolved.is_relative_to(parent.resolve()) or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("worktree must be inside the agent's dispatch directory without symlinks")
    if cwd:
        if Path(_git(path, "rev-parse", "--show-toplevel")).resolve() != path.resolve():
            raise ValueError("cwd must name an existing dispatch worktree root")
        if Path(_git(path, "rev-parse", "--path-format=absolute", "--git-common-dir")).resolve() != repo / ".git":
            raise ValueError("cwd belongs to a different repository")
        branch = _git(path, "symbolic-ref", "--short", "HEAD")
    if exact:
        # A published start is used verbatim; shared replace refs must not re-resolve it.
        if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", base):
            raise ValueError("exact start must be a full object name")
        _verification_git(repo, "cat-file", "-e", f"{base}^{{commit}}")
        return path, branch, base
    sha = _git(path if cwd else repo, "rev-parse", "--verify", f"{('HEAD' if cwd else base)}^{{commit}}")
    return path, branch, sha


@contextmanager
def worktree_lock(repo: Path):
    """Serialize worktree creation, attachment (--cwd) and removal in one repository."""
    fd = os.open(repo / ".git" / "dispatch-worktree.lock", os.O_CREAT | os.O_RDWR, 0o600)
    with os.fdopen(fd, "rb") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def create_worktree(repo: Path, path: Path, branch: str, sha: str, *, full_checkout=False, sparse_include=(),
                    exact=False) -> None:
    excluded = sparse_excludes(sparse_include)
    # A published start is checked out as that exact object, not a shared replacement.
    no_replace = ("--no-replace-objects",) if exact else ()

    def run_git(where, *args):
        return _git(where, *no_replace, *args, isolate=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Serialize config enablement and keep sparse settings local to the new worktree.
    with worktree_lock(repo):
        run_git(repo, "config", "--local", "extensions.worktreeConfig", "true")
        run_git(repo, "worktree", "add", "--no-checkout", "--no-track", "-b", branch, str(path), sha)
        if full_checkout:
            run_git(path, "sparse-checkout", "disable")
        else:
            run_git(path, "sparse-checkout", "set", "--no-cone", "--", "/*", *(f"!/{name}/" for name in excluded))
        run_git(path, "reset", "--hard", sha)
    # Outside the lock: a store miss runs one npm install, and other creations must not wait for it.
    site_deps.provision(repo, path)


# Fixed conventional slots for sandbox refusal and legacy cleanup, never provisioning.
DATABASE_LINKS = tuple(f"data/{STORE_FILES[store][0]}" for store in ("sources", "vesum"))
# Legacy dependency links earlier dispatches provisioned; never provisioned again.
NODE_LINKS = ("node_modules", "site/node_modules")
# Work this branch contains on the canonical remote is published, even after its own branch was deleted.
MAIN_REF = "refs/heads/main"
# A squash merge leaves the task's own commit out of main; its pull-request head ref still proves the push.
PULL_HEADS = "refs/pull/*/head"
PULL_HEAD = re.compile(r"refs/pull/[0-9]+/head")




def snapshot_delivery(spec: TaskSpec, record: dict) -> dict:
    delivery = dict(
        head_sha=None, remote_head_sha=None, remote_ref=None, publish_branch=record.get("publish_branch"),
        push_state="unknown", push_state_reason="observation_failed", commits_ahead=None,
        worktree_dirty_on_exit=None,
    )
    try:
        start_sha = record.get("worktree_start_sha", record["worktree_base_sha"])
        local = partial(execution_safe_git, cwd=spec.worktree, capture_output=True, text=True, check=True, timeout=30)
        delivery.update(
            head_sha=local(["rev-parse", "HEAD"]).stdout.strip(),
            commits_ahead=int(local(["rev-list", "--count", f"{start_sha}..HEAD"]).stdout),
            worktree_dirty_on_exit=bool(local(["status", "--porcelain"]).stdout.strip()),
        )
        if spec.mode == "read-only":
            delivery["push_state"] = "not_applicable"
            delivery["push_state_reason"] = "read_only"
        else:
            branches = [record["worktree_branch"]]
            if delivery["publish_branch"] is not None:
                branches.append(delivery["publish_branch"])
            refs = list(dict.fromkeys(f"refs/heads/{name}" for name in branches))
            remote_url = record["worktree_remote_url"]
            if verification_origin(spec.worktree) != remote_url:
                raise ValueError("origin URL changed since dispatch")
            with _private_remote_git(record["task_id"], remote_url) as (run, _):
                remote = run("ls-remote", "--heads", "origin", *refs)
            heads = {ref: sha for sha, ref in (line.split() for line in remote.splitlines()) if ref in refs}
            matched = next((ref for ref in refs if heads.get(ref) == delivery["head_sha"]), None)
            delivery["remote_ref"] = matched
            delivery["remote_head_sha"] = heads[matched] if matched else next(iter(heads.values()), None)
            delivery["push_state"] = "pushed" if delivery["remote_head_sha"] == delivery["head_sha"] else "unpushed"
            delivery["push_state_reason"] = (
                "remote_head_matches" if matched else "remote_head_differs" if heads else "remote_branch_missing"
            )
    except (OSError, ValueError, subprocess.SubprocessError, TaskScratchError):
        pass
    if spec.mode != "read-only" and delivery["worktree_dirty_on_exit"]:
        delivery["push_state"] = "unpushed"
        delivery["push_state_reason"] = "dirty_worktree"
    return delivery


_REMOTE_SLUG = re.compile(r"(?:https://[^/]+/|git@[^:]+:|ssh://[^/]+/)([\w.-]+/[\w.-]+?)(?:\.git)?/?")


class GitHubRefused(ValueError):
    """The shared GitHub client's reserve or hold admission refused a read; nothing was sent."""


# A run with one GitHub degraded mode (the hourly hygiene run) sets this around settlement: once it
# reports the run degraded, no further GitHub read is sent (github_degraded_when).
_GITHUB_DEGRADED: contextvars.ContextVar = contextvars.ContextVar("dispatcher_github_degraded", default=None)


@contextmanager
def github_degraded_when(degraded):
    """Refuse every GitHub read of this context, before it is sent, while ``degraded()`` is true."""
    token = _GITHUB_DEGRADED.set(degraded)
    try:
        yield
    finally:
        _GITHUB_DEGRADED.reset(token)


def _gh(*args: str) -> str:
    from scripts.common import github_client

    degraded = _GITHUB_DEGRADED.get()
    if degraded is not None and degraded():
        raise GitHubRefused("the run's GitHub reads are degraded")
    proc = github_client.run(["gh", *args], capture_output=True, text=True, check=False, timeout=60)
    if proc.returncode != 0:
        if github_client.refusal_of(proc) is not None:
            raise GitHubRefused("GitHub admission refused the read")
        raise ValueError("GitHub read failed")
    return proc.stdout


def _repo_and_base(record: dict) -> tuple[str | None, str]:
    """The GitHub repository of the remote recorded at dispatch (None when it names none) and the task's base branch."""
    match = _REMOTE_SLUG.fullmatch(record["worktree_remote_url"])
    return (match.group(1) if match else None,
            record["worktree_base_ref"].removeprefix("refs/remotes/").removeprefix("origin/"))


def _accepted_prs(task_id: str, repo: str) -> list[int]:
    """Numbers of ``repo`` pull requests this task accepted through ``pr_ownership``, current or since cleared."""
    from scripts.orchestration import pr_ownership

    data = pr_ownership.load(pr_ownership.state_path())
    # Decision custody stores its decision owner in ``successor``. That is not a task acceptance.
    keys = [
        key for key, handoff in data["handoffs"].items()
        if handoff.get("successor") == task_id and not pr_ownership.decision_custody(handoff)
    ]
    keys += [
        entry["pr"] for entry in data["history"]
        if entry.get("event") == "accepted" and entry.get("successor") == task_id
        and not pr_ownership.decision_custody(entry)
    ]
    return sorted({int(key.rpartition("#")[2]) for key in keys if key.rpartition("#")[0] == repo.casefold()})


def _delivery_prs(record: dict, repo: str) -> list[int]:
    """Numbers of the ``repo`` pull requests that may carry the task's delivery.

    They are the ones it accepted and the merged ones opened from its own or its publish branch.
    """
    numbers = set(_accepted_prs(record["task_id"], repo))
    for branch in sorted({record["worktree_branch"], record.get("publish_branch")} - {None}):
        listed = json.loads(_gh("pr", "list", "--repo", repo, "--head", branch, "--state", "merged",
                                "--json", "number,isCrossRepository,headRefName"))
        numbers.update(pr["number"] for pr in listed if pr["headRefName"] == branch and not pr["isCrossRepository"])
    return sorted(numbers)


def merged_delivery(record: dict) -> dict | None:
    """The merged pull request that carries this task's delivery, or None when none is proven.

    A task that ends with its work merged has nothing left on its own branch to inspect: the
    PR it accepted, or the one opened from its branch, is the delivery, and a worker may have
    reset or deleted the branch after the merge. A candidate counts only when GitHub reports
    it MERGED into the task's base after the task started. Any lookup failure is None, so the
    caller falls back to refusing on the local evidence. ``paths`` is every path the PR
    changed, rename sources included. The task's own head must also be published (nothing
    ahead of the task start, or already in the PR or the base), so merged work never hides
    further work that was not pushed.
    """
    try:
        repo, base = _repo_and_base(record)
        if repo is None:
            return None
        started = datetime.fromisoformat(record["started_at"].replace("Z", "+00:00"))
        for number in _delivery_prs(record, repo):
            pr = json.loads(_gh("pr", "view", str(number), "--repo", repo, "--json", "state,baseRefName,mergedAt"))
            if (pr["state"] != "MERGED" or pr["baseRefName"] != base
                    or datetime.fromisoformat(pr["mergedAt"].replace("Z", "+00:00")) < started):
                continue
            if record.get("commits_ahead") != 0:
                tip, merged = _canonical_publication(
                    record, f"refs/heads/{record.get('publish_branch') or record['worktree_branch']}", record["head_sha"])
                if not (merged or tip == record["head_sha"]):
                    return None
            # One JSON string per line keeps a name with a newline or quote whole.
            changed = _gh("api", "--paginate", f"repos/{repo}/pulls/{number}/files",
                          "--jq", ".[] | (.filename, (.previous_filename // empty)) | @json")
            return dict(repo=repo, number=number, merged_at=pr["mergedAt"],
                        paths=sorted({json.loads(line) for line in changed.split("\n") if line}))
    except (OSError, ValueError, KeyError, TypeError, AttributeError, RuntimeError, subprocess.SubprocessError):
        return None
    return None


def _tree_changes(tree: Path) -> tuple[list[str], list[str]]:
    """Return the tree's uncommitted tracked changes and its untracked files; ignored files are neither.

    Status hides edits to entries flagged assume-unchanged or skip-worktree, so every such entry present
    on disk counts as a change; sparse checkout's skip-worktree entries are absent and do not.
    """
    entries = [entry for entry in _git(tree, "status", "--porcelain", "-z", "--untracked-files=all",
                                       isolate=True, strip=False).split("\0") if entry]
    hidden = [entry[2:] for entry in _git(tree, "ls-files", "-v", "-z", isolate=True, strip=False).split("\0")
              if entry[:1].islower() or entry[:1] == "S"]
    changed = [entry for entry in entries if not entry.startswith("?? ")]
    changed += [f"hidden {name}" for name in hidden if os.path.lexists(tree / name)]
    return changed, [entry[3:] for entry in entries if entry.startswith("?? ")]


def _canonical_publication(record: dict, ref: str, head: str) -> tuple[str | None, bool]:
    """Return the canonical remote's tip of ref and whether it holds head under another ref.

    Only the URL recorded at dispatch is read, in a private Git namespace, so neither the worktree's
    mutable origin nor a configured URL rewrite can redirect the proof. A merged branch may since have
    been deleted, so head also counts as published when a pull-request head ref advertises it exactly
    (GitHub keeps refs/pull/N/head after a squash merge), when, fetched commits-only, a live branch contains it,
    or when the final head of a merged pull request carrying the task's delivery contains it
    (_merged_pr_contains).
    """
    remote = record["worktree_remote_url"]
    if not remote:
        raise ValueError("no canonical remote URL was recorded at dispatch")
    with _private_remote_git(record["task_id"] + "-settle", remote) as (run, _):
        advertised = [line.split() for line in run("ls-remote", "--", "origin", ref, PULL_HEADS).splitlines()]
        tip = next((sha for sha, name in advertised if name == ref), None)
        if tip == head:
            return tip, False
        if any(sha == head and PULL_HEAD.fullmatch(name) for sha, name in advertised):
            return tip, True
        run("fetch", "--no-tags", "--no-write-fetch-head", "--filter=tree:0", "--", "origin",
            "+refs/heads/*:refs/heads/*", timeout=VERIFICATION_FETCH_TIMEOUT)
        if head in run("rev-list", "--branches").split():
            return tip, True
        return tip, _merged_pr_contains(record, run, {name: sha for sha, name in advertised}, head)


def _merged_pr_contains(record: dict, run, pull_heads: dict[str, str], head: str) -> bool:
    """Whether a merged pull request carrying the task's delivery (_delivery_prs) has head among its commits.

    The pull request's branch can gain commits after the worker's last push, such as GitHub's
    update-branch merge of the base, before a squash merge; head is then neither main's nor the
    pull head's exact commit. GitHub must report the pull request MERGED into the task's base with
    the final head that the recorded remote advertises at refs/pull/N/head, and that head, fetched
    commits-only, must contain head. Merged state alone, or the same changes in other commits, is
    not proof. A failed GitHub read raises, so the tree is kept as unknown.
    """
    repo, base = _repo_and_base(record)
    if repo is None:
        return False
    try:
        numbers = _delivery_prs(record, repo)
    except RuntimeError as exc:  # pr_ownership's unreadable or malformed state
        raise ValueError("pull-request ownership state unreadable") from exc
    for number in numbers:
        ref = f"refs/pull/{number}/head"
        if ref not in pull_heads:
            continue
        pr = json.loads(_gh("pr", "view", str(number), "--repo", repo, "--json", "state,baseRefName,headRefOid"))
        if pr["state"] != "MERGED" or pr["baseRefName"] != base or pr["headRefOid"] != pull_heads[ref]:
            continue
        run("fetch", "--no-tags", "--no-write-fetch-head", "--filter=tree:0", "--", "origin", f"+{ref}:{ref}",
            timeout=VERIFICATION_FETCH_TIMEOUT)
        if run("rev-parse", ref) == pull_heads[ref] and head in run("rev-list", ref, "--not", MAIN_REF).split():
            return True
    return False


# Branches the hourly hygiene run pushes a finished task's otherwise unpublished work to; only the operator
# deletes them.
SALVAGE_PREFIX = "refs/heads/salvage/"
# Fixed disposition detail when the public push gate refuses a salvage push, or cannot run.
# Scanner output stays out of the task record.
OPSEC_REFUSAL_DETAIL = "the public push gate refused this range"
# Meaningful ignored output (outside caches and provisioned links) above this keeps a tree for its owner: the
# removal chokepoint only records ignored output, and salvage does not push it.
SALVAGE_IGNORED_LIMIT = 100 * 1024 * 1024
_SALVAGE_AUTHOR = dict(GIT_AUTHOR_NAME="lu-worktree-gc", GIT_AUTHOR_EMAIL="worktree-gc@learn-ukrainian.invalid",
                       GIT_COMMITTER_NAME="lu-worktree-gc", GIT_COMMITTER_EMAIL="worktree-gc@learn-ukrainian.invalid")


class _Kept(Exception):
    """A tree salvage could not make safe to remove, with the disposition reason and detail to record."""

    def __init__(self, reason: str, detail: str | None = None):
        super().__init__(reason)
        self.reason, self.detail = reason, detail


def _snapshot_tree(tree: Path, task_id: str) -> str:
    """The tree object of the checkout's tracked and untracked (not ignored) files.

    They are staged in a scratch copy of the checkout's index, so its own index, HEAD and branch stay as they were.
    """
    index = _git(tree, "rev-parse", "--path-format=absolute", "--git-path", "index", isolate=True)
    scratch = allocate(task_id + "-salvage")
    try:
        scratch.payload_dir.mkdir(exist_ok=True)
        env = {"GIT_INDEX_FILE": str(shutil.copyfile(index, scratch.payload_dir / "index"))}
        _git(tree, "add", "--all", isolate=True, env=env)
        return _git(tree, "write-tree", isolate=True, env=env)
    finally:
        try:
            scratch.remove()
        finally:
            scratch.preserve()


def _salvage_hold(tree: Path, primary: Path, untracked: list[str]) -> tuple[str, str] | None:
    """Why the hourly run keeps a tree whatever its publication: a reason and detail, or None.

    Neither salvage nor removal keeps the content of a nested repository (Git stages it as a bare
    commit pointer), so one with commits that are on none of its remotes, or with uncommitted work,
    keeps the tree. So does meaningful ignored output past SALVAGE_IGNORED_LIMIT.
    """
    from scripts.fleet.regenerable_output import is_regenerable_ignored_path
    from scripts.orchestration.worktree_artifacts import is_disposable_path

    ignored = [name for name in _git(tree, "ls-files", "-z", "--others", "--ignored", "--exclude-standard",
                                     isolate=True, strip=False).split("\0") if name]
    for name in (*untracked, *ignored):
        nested = tree / name
        if name.endswith("/") and os.path.lexists(nested / ".git") and (
                _git(nested, "status", "--porcelain", isolate=True)
                or _git(nested, "rev-list", "-n1", "--all", "--not", "--remotes", isolate=True)):
            return "nested_repository_unpushed", name
    tracked = set(_git(tree, "ls-files", "-z", "--cached", isolate=True, strip=False).split("\0"))
    ignored_names = set(ignored)
    dependency_locks: dict[str, bool] = {}  # one lock verdict per dependency directory, not per file
    total = 0
    for name in ignored:
        if not is_disposable_path(Path(name), worktree=tree, primary=primary) and not is_regenerable_ignored_path(
                name, worktree=tree, tracked=tracked, ignored=ignored_names, release_pins={},
                dependency_locks=dependency_locks):
            total += os.lstat(tree / name).st_size
            if total > SALVAGE_IGNORED_LIMIT:
                return "large_ignored_output", f"over {SALVAGE_IGNORED_LIMIT} bytes outside caches"
    return None


def _require_public_push(tree: Path, remote: str, ref: str, commit: str) -> None:
    """Refuse unless the public push gate would allow pushing ``commit`` to ``ref`` on ``remote``.

    Reuses ``git_push.scan_push`` (the pre-push message scan) and ``lint_opsec_leaks.py
    --commit-range`` (the pre-push gate's blob scan). Any refusal or any failure to run either
    scan raises ``_Kept`` and does not push. The detail is a fixed phrase.
    """
    from scripts.opsec import git_push
    from scripts.opsec.prepublish import OVERRIDE, PublishBlocked

    def refuse() -> None:
        raise _Kept("opsec_refused", OPSEC_REFUSAL_DETAIL)

    snapshot = dict(os.environ)
    try:
        # The message scan excludes history already on the public default branch only when that
        # tip is in this object store. A missing tip makes it scan already-public commits.
        with suppress(OSError, subprocess.SubprocessError):
            _verification_git(tree, "fetch", "--no-tags", "--no-write-fetch-head", "--", remote,
                              "+refs/heads/main:refs/remotes/origin/main", credential_remote=remote,
                              timeout=VERIFICATION_FETCH_TIMEOUT)
        git_dir = _git(tree, "rev-parse", "--absolute-git-dir", isolate=True)
        base = _git(tree, "merge-base", "origin/main", commit, isolate=True)
        environment = dict(os.environ)
        environment.pop(OVERRIDE, None)
        environment.update(GIT_DIR=git_dir, GIT_WORK_TREE=str(tree))
        if GIT_BINARY:
            environment["LU_OPSEC_REAL_GIT"] = GIT_BINARY
        line = f"{commit} {commit} {ref} {'0' * len(commit)}\n".encode()
        try:
            with git_push.deadline(git_push.scan_timeout(environment)):
                git_push.scan_push([remote, remote], line, environment)
        except PublishBlocked:
            refuse()
        except git_push.ScanTimeout:
            refuse()
        # The checkout under salvage can replace its own linter. Run the copy next to this
        # module, and point Git at the salvage objects.
        script = Path(__file__).resolve().parents[2] / "scripts/audit/lint_opsec_leaks.py"
        try:
            script.resolve().relative_to(tree.resolve())
        except ValueError:
            inside = False
        else:
            inside = True
        if inside or not script.is_file():
            refuse()
        lint_env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        lint_env.pop(OVERRIDE, None)
        lint_env.update(GIT_DIR=git_dir, GIT_WORK_TREE=str(tree), GIT_TERMINAL_PROMPT="0")
        completed = subprocess.run(
            [sys.executable, str(script), "--commit-range", f"{base}..{commit}"],
            cwd=script.parents[2], env=lint_env, capture_output=True, text=True, timeout=120, check=False,
        )
        if completed.returncode != 0:
            refuse()
    except _Kept:
        raise
    except Exception:
        refuse()
    finally:
        for key, value in snapshot.items():
            if key not in os.environ:
                os.environ[key] = value


def _salvage(record: dict, tree: Path, head: str, changed: list[str]) -> tuple[str, str]:
    """Push the tree's commits and uncommitted work to a new salvage branch; return the commit and its tree.

    The commit is head itself when nothing is uncommitted, else one commit on head holding the tracked
    and untracked files, with a fixed author and date so a retry builds the same commit. It goes to the
    URL recorded at dispatch only as a new branch: the push leases the branch as absent, so it never
    updates one that exists, even by fast-forward. It counts only once that remote advertises exactly it.
    """
    task_id, remote = record["task_id"], record["worktree_remote_url"]
    ref = SALVAGE_PREFIX + task_id
    if any(entry.startswith("hidden ") for entry in changed):
        raise _Kept("salvage_unverified", "an assume-unchanged or skip-worktree edit cannot be staged")
    try:
        _git(tree, "check-ref-format", ref, isolate=True)
        if not remote or verification_origin(tree) != remote:
            raise _Kept("salvage_unverified", "origin URL changed since dispatch")
        snapshot, commit = _snapshot_tree(tree, task_id), head
        if snapshot != _git(tree, "rev-parse", "HEAD^{tree}", isolate=True):
            when = record.get("finished_at") or record["started_at"]
            commit = _git(tree, "commit-tree", snapshot, "-p", head, "-m", f"salvage: unpublished work of {task_id}",
                          isolate=True, env={**_SALVAGE_AUTHOR, "GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when})
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        raise _Kept("salvage_unverified", f"salvage commit not built ({type(exc).__name__})") from None

    def advertised() -> str | None:
        listing = _verification_git(tree, "ls-remote", "--", remote, ref, credential_remote=remote,
                                    timeout=VERIFICATION_FETCH_TIMEOUT)
        return next((sha for sha, name in (line.split() for line in listing.splitlines()) if name == ref), None)

    try:
        if advertised() is None:
            # The same privacy scans an ordinary public push runs. A refusal is not a transport failure
            # and must not be retried.
            _require_public_push(tree, remote, ref, commit)
            # A refused push (the branch appeared meanwhile, or a transport failure) is judged by what
            # the remote advertises next.
            with suppress(subprocess.CalledProcessError):
                _verification_git(tree, "push", "--quiet", f"--force-with-lease={ref}:", "--", remote,
                                  f"{commit}:{ref}", credential_remote=remote, timeout=VERIFICATION_FETCH_TIMEOUT)
        verified = advertised()
    except _Kept:
        raise
    except (OSError, ValueError, subprocess.SubprocessError):
        raise _Kept("salvage_failed", f"push of {ref} to the recorded remote failed") from None
    if verified is None:
        raise _Kept("salvage_failed", f"push of {ref} to the recorded remote failed")
    if verified != commit:
        raise _Kept("salvage_failed", f"{ref} already holds another commit")
    return commit, snapshot


def _retention_held(record: dict) -> bool:
    """Whether either copy holds the tree; refuse an unreadable or malformed copy.

    A supervisor can still be holding the record from before the hold was set.
    """
    from scripts.dispatcher import store

    hold = store.retention_hold_disposition(record)
    if hold is None:
        return False
    if hold["worktree_disposition_reason"] == "retention_hold":
        return True
    raise _Kept(hold["worktree_disposition_reason"], hold["worktree_disposition_detail"])


def settle_worktree(record: dict, borrowed=lambda: False, salvage: bool = False) -> dict:
    """Remove the task's own worktree when nothing in it can be lost; otherwise record why it stays.

    Runs from outside the worktree after the provider has exited. Uncommitted tracked changes keep the
    tree. A write task that committed keeps it until its HEAD is the publish branch's tip on the
    canonical remote recorded at dispatch (without --branch that is the task branch), a pull-request
    head there, or is already in that remote's main; a task that committed nothing needs no proof.
    borrowed() is asked under the worktree lock, right before removal, whether another task's
    provider may still work in this tree. Removal goes through the guarded chokepoint
    (worktree_claims.remove_unclaimed_worktree), which records ignored output and copies untracked
    files into the task's preserved archive before it removes the checkout.

    With salvage (the hourly hygiene run), a tree kept for uncommitted or unpublished work is pushed to
    a new salvage/<task-id> branch on that remote instead (_salvage), after borrowed() and the worktree
    claims admit it, and is removed only while its HEAD and content still equal what that branch holds;
    a failed or unproven salvage keeps it, and so does every hold _salvage_hold finds.
    """
    def disposition(state, reason, detail=None):
        return dict(worktree_disposition=state, worktree_disposition_reason=reason,
                    **({"worktree_disposition_detail": detail} if detail else {}))

    # An owner hold is decided before any Git read, push, or removal. The disk
    # record wins when this copy is stale.
    try:
        if _retention_held(record):
            return disposition("retained", "retention_hold")
    except _Kept as kept:
        return disposition("retained", kept.reason, kept.detail)
    if record.get("options", {}).get("cwd"):
        return disposition("retained", "borrowed_worktree")
    try:
        repo, tree, branch = resolve_repo(record.get("repo"))[0], Path(record["worktree_path"]), record["worktree_branch"]
        changed, untracked = _tree_changes(tree)
        head, remote, merged = _git(tree, "rev-parse", "HEAD", isolate=True), None, False
        if changed and not salvage:
            return disposition("retained", "dirty", "; ".join(changed[:5]))
        committed = head != record.get("worktree_start_sha", record["worktree_base_sha"])
        if not changed and record["mode"] != "read-only" and committed:
            remote, merged = _canonical_publication(record, f"refs/heads/{record.get('publish_branch') or branch}", head)
        hold = _salvage_hold(tree, repo, untracked) if salvage else None
    except GitHubRefused:
        return disposition("retained", "github_deferred")
    except (OSError, ValueError, KeyError, subprocess.SubprocessError):
        return disposition("retained", "unknown")
    published = head == remote or merged
    unpublished = not changed and record["mode"] != "read-only" and committed and not published
    if unpublished and not salvage:
        return disposition("retained", "unpublished" if remote is None else "remote_mismatch")
    if hold:
        return disposition("retained", *hold)

    from scripts.orchestration import worktree_claims

    salvaged = None
    if changed or unpublished:
        # Claims are checked before the salvage push, and again under the lock before removal.
        if borrowed():
            return disposition("retained", "borrowed_by_live_task")
        refusal = worktree_claims.active_worktree_claim_refusal(
            tree, tasks_dir=tasks_dir(), repo_root=repo, owner_task_id=record["task_id"])
        if refusal is not None:
            return disposition("retained", "removal_refused", refusal)
        try:
            salvaged = _salvage(record, tree, head, changed)
        except _Kept as kept:
            return disposition("retained", kept.reason, kept.detail)
        published = True
    salvage_detail = f"{SALVAGE_PREFIX}{record['task_id']} {salvaged[0]}" if salvaged else None

    def changed_since_inventory(path: Path) -> bool | None:
        with suppress(OSError, ValueError, subprocess.SubprocessError):
            now_changed, now_untracked = _tree_changes(path)
            if _git(path, "rev-parse", "HEAD", isolate=True) != head:
                return True
            if salvaged:
                moved = (_snapshot_tree(path, record["task_id"]) != salvaged[1]
                         or any(entry.startswith("hidden ") for entry in now_changed))
            else:
                moved = (now_changed, now_untracked) != ([], untracked)
            return moved or (salvage and _salvage_hold(path, repo, now_untracked) is not None)
        return None

    with worktree_lock(repo):
        if borrowed():
            return disposition("retained", "borrowed_by_live_task")
        # Untracked files and salvaged edits block a plain removal; the forced one runs only after the dirty
        # probe, which salvage always runs so its HEAD, content and holds are checked again under the lock.
        removal = worktree_claims.remove_unclaimed_worktree(
            tree, repo_root=repo, reason="dispatch settlement", owner_task_id=record["task_id"],
            force=bool(untracked or changed or salvage), dirty_probe=changed_since_inventory, tasks_dir=tasks_dir(),
            task_record=record, preserve_files=untracked or None,
        )
    if removal.action == "skipped":
        return disposition("retained", "removal_refused", removal.reason)
    if removal.action != "removed":
        return disposition("error", "worktree_remove_failed", removal.error or removal.reason)
    try:
        # The task branch goes only when its tip is published or reachable from another ref.
        if not published and _git(repo, "rev-list", "-n1", head, "--not", f"--exclude=refs/heads/{branch}", "--all",
                                  isolate=True):
            return disposition("removed", "branch_kept_unmerged")
        _git(repo, "update-ref", "-d", f"refs/heads/{branch}", head, isolate=True)
    except (OSError, subprocess.SubprocessError):
        return disposition("removed", "branch_delete_failed", salvage_detail)
    return disposition("removed", "salvaged", salvage_detail) if salvaged else disposition("removed", "clean")
