"""Worktree creation and observational Git delivery reporting."""

import errno
import fcntl
import logging
import os
import stat
import subprocess
from contextlib import ExitStack, suppress
from functools import partial
from pathlib import Path

import yaml

from scripts.common.git_context import sanitized_git_env
from scripts.common.repo_root import resolve_repo_root
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


def sparse_excludes(includes=()) -> list[str]:
    includes = {name.strip().strip("/") for name in includes}
    if includes - SPARSE_EXCLUDE_DEFAULT:
        raise ValueError("--sparse-include must name a default-excluded tree: " + ", ".join(sorted(SPARSE_EXCLUDE_DEFAULT)))
    return sorted(SPARSE_EXCLUDE_DEFAULT - includes)


def _git(path: Path, *args: str, isolate: bool = False) -> str:
    return subprocess.run(
        ["git", "-C", str(path), *args],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
        env={**(sanitized_git_env() if isolate else os.environ), "GIT_TERMINAL_PROMPT": "0"},
    ).stdout.strip()


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


def create_worktree(repo: Path, path: Path, branch: str, sha: str, *, full_checkout=False, sparse_include=()) -> None:
    excluded = sparse_excludes(sparse_include)
    run_git = partial(_git, isolate=True)
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


def snapshot_delivery(spec: TaskSpec, base_sha: str, branch: str) -> dict:
    delivery = dict(
        head_sha=None, remote_head_sha=None, push_state="unknown", commits_ahead=None, worktree_dirty_on_exit=None
    )
    try:
        delivery.update(
            head_sha=_git(spec.worktree, "rev-parse", "HEAD"),
            commits_ahead=int(_git(spec.worktree, "rev-list", "--count", f"{base_sha}..HEAD")),
            worktree_dirty_on_exit=bool(_git(spec.worktree, "status", "--porcelain")),
        )
        if spec.mode == "read-only":
            delivery["push_state"] = "not_applicable"
        else:
            remote = _git(spec.worktree, "ls-remote", "--heads", "origin", f"refs/heads/{branch}")
            delivery["remote_head_sha"] = remote.split()[0] if remote else None
            delivery["push_state"] = "pushed" if delivery["remote_head_sha"] == delivery["head_sha"] else "unpushed"
    except (OSError, ValueError, subprocess.SubprocessError):
        pass
    if spec.mode != "read-only" and delivery["worktree_dirty_on_exit"]:
        delivery["push_state"] = "unpushed"
    return delivery
