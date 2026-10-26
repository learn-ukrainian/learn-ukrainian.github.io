"""Worktree creation and observational Git delivery reporting."""

import fcntl
import os
import subprocess
from pathlib import Path

import yaml

from scripts.common.repo_root import resolve_repo_root
from scripts.dispatcher.types import TaskSpec

ROOT = resolve_repo_root(Path(__file__), 2)
CONFIG = Path(__file__).resolve().parents[1] / "config" / "fleet_repos.yaml"


def _git(path: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(path), *args],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
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


def create_worktree(repo: Path, path: Path, branch: str, sha: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Git's sparse-checkout setup writes shared repository config even for a fresh tree.
    fd = os.open(repo / ".git" / "dispatch-worktree.lock", os.O_CREAT | os.O_RDWR, 0o600)
    with os.fdopen(fd, "rb") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        _git(repo, "worktree", "add", "--no-track", "-b", branch, str(path), sha)
        _git(path, "sparse-checkout", "disable")


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
    return delivery
