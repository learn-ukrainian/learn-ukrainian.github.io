"""Worktree creation and observational Git delivery reporting."""

import errno
import fcntl
import logging
import os
import re
import shutil
import stat
import subprocess
import time
from contextlib import ExitStack, contextmanager, suppress
from functools import partial
from pathlib import Path

import yaml

from scripts.common.git_context import sanitized_git_env
from scripts.common.git_credentials import canonical_origins as canonical_origins
from scripts.common.git_credentials import verification_credentials
from scripts.common.repo_root import resolve_repo_root
from scripts.common.task_scratch import allocate
from scripts.dispatcher import store
from scripts.dispatcher.environment import npm_shim_dir
from scripts.dispatcher.types import TaskSpec
from scripts.storage.topology import STORE_FILES

ROOT = resolve_repo_root(Path(__file__), 2)
CONFIG = Path(__file__).resolve().parents[1] / "config" / "fleet_repos.yaml"
# Mirrors scripts/delegate.py::_DISPATCH_SPARSE_EXCLUDE_DEFAULT without importing its runtime.
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
# Committer-clock slack below the task base date. Speed depends on this value;
# correctness does not, because _complete_since_task_base checks the fetched graph.
HISTORY_SLACK_SECONDS = 86400
# Bound on waiting for the dispatch worktree lock; a stuck holder must not stall dispatch forever.
WORKTREE_LOCK_TIMEOUT_ENV = "LU_DISPATCH_WORKTREE_LOCK_TIMEOUT_S"
WORKTREE_LOCK_TIMEOUT_S = 120.0


class WorktreeLockTimeout(ValueError):
    """The dispatch worktree lock stayed held past the bounded wait; nothing was created."""


def _worktree_lock_timeout_s() -> float:
    try:
        value = float(os.environ.get(WORKTREE_LOCK_TIMEOUT_ENV) or WORKTREE_LOCK_TIMEOUT_S)
    except ValueError:
        return WORKTREE_LOCK_TIMEOUT_S
    return value if 0 < value < float("inf") else WORKTREE_LOCK_TIMEOUT_S


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
    """Whether the fetched graph is enough to walk the delivery above the task base.

    Callers walk from the delivery tip, excluding the task base and a merge base
    with the base tip. Single-parent commits are diffed against their parent and
    merges are re-run, which recomputes the merge bases of their parents.

    Every commit the walk inspects needs its real parents. A bounded fetch records
    each shallow boundary commit without parents, so no boundary may lie on a
    tip's path above the task base. A boundary parent is itself present with its
    tree, so a single-parent diff against it is exact, and a merge base found in
    the bounded graph is a real common ancestor of the delivery and the base tip.

    A merge in the inspected range needs the complete ancestry of its parents to
    be recomputed. A graph with shallow boundaries does not provide it, so a
    delivery with any merge above the task base requires non-shallow history.
    """
    tips = ("refs/heads/delivery", "refs/heads/base")
    if task_base not in run("rev-list", *tips).split():
        return False
    if run("rev-parse", "--is-shallow-repository") == "false":
        return True
    return (set(shallow.read_text().split()).isdisjoint(run("rev-list", *tips, "--not", task_base).split())
            and not run("rev-list", "--min-parents=2", "refs/heads/delivery", "--not", task_base))


@contextmanager
def ownership_git(record: dict):
    """Walk trusted remote objects in a private config/ref namespace.

    A command-line include.path override is not a local-config sandbox. A fresh
    bare Git directory excludes both worker config and config.worktree,
    their includes, grafts and replacement refs. Objects and refs come only from
    the remote URL recorded before provider execution. No local objects are reused.

    The transfer is blob-less and starts at the task base date, so it stays small
    on a multi-gigabyte repository. Blobs are fetched lazily from the same URL only
    when a merge must be re-run. If a remote tip is dated before the cutoff (clock
    skew), that bounded history does not reach the task base on every path, or the
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
    task_base = record["worktree_base_sha"]
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
    scratch = allocate(record["task_id"] + "-ownership")
    try:
        run = partial(_verification_git, scratch.payload_dir, git_dir=scratch.payload_dir, credential_remote=remote)
        run("init", "--bare", "--template=")
        for key, value in (("remote.origin.url", remote), ("remote.origin.promisor", "true"),
                           ("remote.origin.partialCloneFilter", "blob:none"),
                           ("extensions.partialClone", "origin")):
            run("config", key, value)
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
        shallow = scratch.payload_dir / "shallow"
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
    finally:
        try:
            scratch.remove()
        finally:
            scratch.preserve()


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


def worktree_plan(repo: Path, agent: str, task_id: str, base: str, cwd=None, worktree=None):
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
    sha = _git(path if cwd else repo, "rev-parse", "--verify", f"{('HEAD' if cwd else base)}^{{commit}}")
    return path, branch, sha


@contextmanager
def worktree_lock(repo: Path):
    """The dispatch worktree lock: creation, removal and attachment to an existing worktree hold it."""
    fd = os.open(repo / ".git" / "dispatch-worktree.lock", os.O_CREAT | os.O_RDWR, 0o600)
    with os.fdopen(fd, "rb") as lock:
        timeout = _worktree_lock_timeout_s()
        deadline = time.monotonic() + timeout
        while True:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise WorktreeLockTimeout(
                        f"worktree_lock_timeout: worktree lock still held after {timeout:g}s"
                    ) from None
                time.sleep(0.05)
        yield


def in_use(path: Path) -> bool:
    """Whether a task record names this worktree or a live process other than this one works inside it.

    Paths compare by canonical identity (symlinks and ``..`` resolved), so every spelling of the worktree
    counts. An unreadable task store counts as in use, so a cleanup that cannot tell keeps the checkout.
    """
    # Path.resolve raises RuntimeError on a symlink loop; a path that cannot be resolved counts as in use.
    try:
        resolved = path.resolve()
        records = []
        # list_tasks skips a task directory it cannot list or stat, so that failure is caught here first.
        with suppress(FileNotFoundError), os.scandir(store.tasks_dir()) as entries:
            for entry in entries:
                if entry.name.endswith(".json"):
                    with suppress(FileNotFoundError):
                        entry.stat()
            records = store.list_tasks(strict=True)
        if any(isinstance(record.get(key), str) and Path(record[key]).resolve() == resolved
               for record in records for key in ("worktree_path", "cwd")):
            return True
        processes = [entry for entry in Path("/proc").iterdir() if entry.name.isdigit() and int(entry.name) != os.getpid()]
    except (OSError, RuntimeError, ValueError):
        return True
    for entry in processes:
        with suppress(OSError, RuntimeError):
            if Path(os.readlink(entry / "cwd")).resolve().is_relative_to(resolved):
                return True
    return False


@contextmanager
def attached_worktree(repo: Path, path: Path):
    """Attach to an existing worktree under the worktree lock, held until the caller's record names it.

    A concurrent dispatch removing a worktree it partly prepared either finishes first, so the root check
    here refuses, or finds this task's record and keeps the worktree.
    """
    with worktree_lock(repo):
        if not (path / ".git").exists() or Path(_git(path, "rev-parse", "--show-toplevel")).resolve() != path.resolve():
            raise ValueError("cwd must name an existing dispatch worktree root")
        yield


def create_worktree(repo: Path, path: Path, branch: str, sha: str, *, full_checkout=False, sparse_include=()) -> None:
    excluded = sparse_excludes(sparse_include)
    run_git = partial(_git, isolate=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Serialize config enablement and keep sparse settings local to the new worktree.
    with worktree_lock(repo):
        run_git(repo, "config", "--local", "extensions.worktreeConfig", "true")
        new_branch = not run_git(repo, "for-each-ref", "--format=%(refname)", f"refs/heads/{branch}")
        added = False
        try:
            run_git(repo, "worktree", "add", "--no-checkout", "--no-track", "-b", branch, str(path), sha)
            added = True
            if full_checkout:
                run_git(path, "sparse-checkout", "disable")
            else:
                run_git(path, "sparse-checkout", "set", "--no-cone", "--", "/*", *(f"!/{name}/" for name in excluded))
            run_git(path, "reset", "--hard", sha)
            provision_links(repo, path)
        except BaseException:
            # Remove only what this call created, and never a worktree another task or process uses; a kept
            # worktree keeps its branch. Git creates the branch before it checks the path, so a refused add
            # can leave a new branch; a pre-existing branch or path is never touched.
            kept = added and in_use(path)
            if added and not kept:
                with suppress(OSError, subprocess.SubprocessError):
                    run_git(repo, "worktree", "remove", "--force", str(path))
            if new_branch and not kept:
                with suppress(OSError, subprocess.SubprocessError):
                    run_git(repo, "update-ref", "-d", f"refs/heads/{branch}", sha)
            raise


def discard_worktree(repo: Path, path: Path, branch: str) -> None:
    """Remove a worktree this dispatch created and never launched in, with its branch (best effort).

    Under the worktree lock, a worktree another task or process uses is kept, and so is a worktree
    whose use cannot be checked because the lock stayed held.
    """
    run_git = partial(_git, isolate=True)
    with suppress(WorktreeLockTimeout), worktree_lock(repo):
        if in_use(path):
            return
        for args in (("worktree", "remove", "--force", str(path)), ("branch", "-D", branch)):
            with suppress(OSError, subprocess.SubprocessError):
                run_git(repo, *args)


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
        delivery.update(
            head_sha=_git(spec.worktree, "rev-parse", "HEAD"),
            commits_ahead=int(_git(spec.worktree, "rev-list", "--count", f"{record['worktree_base_sha']}..HEAD")),
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
