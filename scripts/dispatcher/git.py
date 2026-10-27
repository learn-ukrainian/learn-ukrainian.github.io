"""Worktree creation and observational Git delivery reporting."""

import errno
import fcntl
import logging
import os
import re
import shutil
import stat
import subprocess
from contextlib import ExitStack, contextmanager, suppress
from functools import partial
from pathlib import Path

import yaml

from scripts.common.git_context import sanitized_git_env
from scripts.common.git_credentials import canonical_origins as canonical_origins
from scripts.common.git_credentials import verification_credentials
from scripts.common.repo_root import resolve_repo_root
from scripts.common.task_scratch import allocate
from scripts.dispatcher.environment import npm_shim_dir
from scripts.dispatcher.types import TaskSpec
from scripts.storage.topology import STORE_FILES

ROOT = resolve_repo_root(Path(__file__), 2)
CONFIG = Path(__file__).resolve().parents[1] / "config" / "fleet_repos.yaml"
# Default trees excluded from dispatch worktrees.
SPARSE_EXCLUDE_DEFAULT = frozenset({
    "curriculum", "wiki", "data/projects", "data/lexicon", "data/datasets", "data/processed",
    "registry/projects", "registry/lexicon/source-inventory",
    "registry/lexicon/source-inventory-review-decisions", "site/src/content", "site/src/data",
})
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
        for key, value in (("remote.origin.url", remote), ("remote.origin.promisor", "true"),
                           ("remote.origin.partialCloneFilter", "blob:none"),
                           ("extensions.partialClone", "origin")):
            run("config", key, value)
        yield run, scratch.payload_dir
    finally:
        try:
            scratch.remove()
        finally:
            scratch.preserve()


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
    base = record["worktree_base_ref"].removeprefix("refs/remotes/")
    if not base.startswith("origin/"):
        raise ValueError("ownership verification requires an origin base")
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


def sparse_excludes(includes=()) -> list[str]:
    includes = {name.strip().strip("/") for name in includes}
    if includes - SPARSE_EXCLUDE_DEFAULT:
        raise ValueError("--sparse-include must name a default-excluded tree: " + ", ".join(sorted(SPARSE_EXCLUDE_DEFAULT)))
    return sorted(SPARSE_EXCLUDE_DEFAULT - includes)


def _git(path: Path, *args: str, isolate: bool = False, strip: bool = True) -> str:
    output = subprocess.run(
        ["git", "-C", str(path), *args],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
        env={**(sanitized_git_env(strip_config_injection=True) if isolate else os.environ), "GIT_TERMINAL_PROMPT": "0"},
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


def create_worktree(repo: Path, path: Path, branch: str, sha: str, *, full_checkout=False, sparse_include=(),
                    exact=False) -> None:
    excluded = sparse_excludes(sparse_include)
    # A published start is checked out as that exact object, not a shared replacement.
    no_replace = ("--no-replace-objects",) if exact else ()

    def run_git(where, *args):
        return _git(where, *no_replace, *args, isolate=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Serialize config enablement and keep sparse settings local to the new worktree.
    fd = os.open(repo / ".git" / "dispatch-worktree.lock", os.O_CREAT | os.O_RDWR, 0o600)
    with os.fdopen(fd, "rb") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        run_git(repo, "config", "--local", "extensions.worktreeConfig", "true")
        run_git(repo, "worktree", "add", "--no-checkout", "--no-track", "-b", branch, str(path), sha)
        if full_checkout:
            run_git(path, "sparse-checkout", "disable")
        else:
            run_git(path, "sparse-checkout", "set", "--no-cone", "--", "/*", *(f"!/{name}/" for name in excluded))
        run_git(path, "reset", "--hard", sha)
        provision_links(repo, path)


def provision_links(repo: Path, worktree: Path) -> None:
    """Provision only real primary targets; atomic symlink creation never replaces entries."""
    repo = repo.absolute()
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    node_links = ("node_modules", "site/node_modules")
    if npm_shim_dir() is None:
        logging.getLogger(__name__).warning("Skipping node_modules and site/node_modules: npm/npx guard unavailable")
        node_links = ()
    database_links = tuple(f"data/{STORE_FILES[store][0]}" for store in ("sources", "vesum"))
    for relative in (*database_links, *node_links):
        parts = Path(relative).parts
        with ExitStack() as stack:
            def open_directory(name, parent=None):
                fd = os.open(name, flags, dir_fd=parent)
                stack.callback(os.close, fd)
                return fd

            try:
                source = open_directory(repo)
                for part in parts[:-1]:
                    source = open_directory(part, source)
                target = os.stat(parts[-1], dir_fd=source, follow_symlinks=False)
                if not (stat.S_ISREG(target.st_mode) or stat.S_ISDIR(target.st_mode)):
                    logging.getLogger(__name__).warning("Skipping link %s: source is not a real file or directory", relative)
                    continue
                destination = open_directory(worktree)
                for part in parts[:-1]:
                    with suppress(FileExistsError):
                        os.mkdir(part, dir_fd=destination)
                    destination = open_directory(part, destination)
                os.symlink(repo / relative, parts[-1], dir_fd=destination)
            except OSError as exc:
                if exc.errno not in (errno.ENOENT, errno.ENOTDIR, errno.ELOOP, errno.EEXIST):
                    raise
                logging.getLogger(__name__).warning("Skipping link %s: %s", relative, errno.errorcode[exc.errno])


def snapshot_delivery(spec: TaskSpec, record: dict) -> dict:
    delivery = dict(
        head_sha=None, remote_head_sha=None, remote_ref=None, publish_branch=record.get("publish_branch"),
        push_state="unknown", push_state_reason="observation_failed", commits_ahead=None,
        worktree_dirty_on_exit=None,
    )
    try:
        start_sha = record.get("worktree_start_sha", record["worktree_base_sha"])
        delivery.update(
            head_sha=_git(spec.worktree, "rev-parse", "HEAD"),
            commits_ahead=int(_git(spec.worktree, "rev-list", "--count", f"{start_sha}..HEAD")),
            worktree_dirty_on_exit=bool(_git(spec.worktree, "status", "--porcelain")),
        )
        if spec.mode == "read-only":
            delivery["push_state"] = "not_applicable"
            delivery["push_state_reason"] = "read_only"
        else:
            branches = [record["worktree_branch"]]
            if delivery["publish_branch"] is not None:
                branches.append(delivery["publish_branch"])
            refs = list(dict.fromkeys(f"refs/heads/{name}" for name in branches))
            remote = _git(spec.worktree, "ls-remote", "--heads", "origin", *refs)
            heads = {ref: sha for sha, ref in (line.split() for line in remote.splitlines()) if ref in refs}
            matched = next((ref for ref in refs if heads.get(ref) == delivery["head_sha"]), None)
            delivery["remote_ref"] = matched
            delivery["remote_head_sha"] = heads[matched] if matched else next(iter(heads.values()), None)
            delivery["push_state"] = "pushed" if delivery["remote_head_sha"] == delivery["head_sha"] else "unpushed"
            delivery["push_state_reason"] = (
                "remote_head_matches" if matched else "remote_head_differs" if heads else "remote_branch_missing"
            )
    except (OSError, ValueError, subprocess.SubprocessError):
        pass
    if spec.mode != "read-only" and delivery["worktree_dirty_on_exit"]:
        delivery["push_state"] = "unpushed"
        delivery["push_state_reason"] = "dirty_worktree"
    return delivery
