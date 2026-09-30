"""Closed sibling maintenance verbs; no arbitrary Git or shell interface (#9309).

Host Git/SSH and the installed project interpreter are trusted. Repository
configuration, caller environment, and path arguments are not. See
``docs/runbooks/sibling-git.md`` for the supported transport and refusal contract.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from scripts.orchestration import worktree_claims
from scripts.orchestration.fleet_repos import load_fleet_repos, resolve_fleet_repo

_GIT = "/usr/bin/git"
_SOURCE_ROOT = Path(__file__).resolve().parents[2]


class Refusal(ValueError):
    """Privacy-safe refusal: never interpolate paths or Git diagnostics."""


def _plain_path(path: Path, *, exists: bool = True) -> Path:
    if any(unicodedata.category(c) in {"Cc", "Cf", "Zl", "Zp"} for c in str(path)):
        raise Refusal("path contains control or formatting characters")
    if not path.is_absolute() or ".." in path.parts:
        raise Refusal("use an absolute path without parent traversal")
    for part in (path, *path.parents):
        if part.is_symlink():
            raise Refusal("symlinked paths are unsupported")
    return path.resolve(strict=exists)


def _git_dir(checkout: Path) -> tuple[Path, Path]:
    marker = checkout / ".git"
    _plain_path(marker)
    if marker.is_dir():
        git_dir = marker
    else:
        text = marker.read_text().strip()
        if not text.startswith("gitdir: ") or "\n" in text:
            raise Refusal("invalid Git pointer file")
        raw = Path(text[8:])
        git_dir = _plain_path(raw if raw.is_absolute() else checkout / raw)
    common_file = git_dir / "commondir"
    if common_file.exists():
        _plain_path(common_file)
        raw = Path(common_file.read_text().strip())
        # Git's generated linked-worktree pointer normally contains ../..
        common = (git_dir / raw).resolve(strict=True) if not raw.is_absolute() else raw.resolve(strict=True)
    else:
        common = git_dir
    return git_dir.resolve(), common


def primary_root(source: Path = _SOURCE_ROOT) -> Path:
    """Resolve our own repository from its marker, never inherited Git state."""
    _, common = _git_dir(_plain_path(source))
    if common.name != ".git":
        raise Refusal("cannot establish the protected repository")
    return _plain_path(common.parent)


@dataclass(frozen=True)
class Repository:
    key: str
    checkout: Path
    git_dir: Path
    common: Path
    remote: str


class Git:
    """One fixed executable and command configuration, including read probes."""

    def __init__(self, hooks: Path):
        # Drop all inherited Git redirects/config and loader/command injection.
        self.env = {k: os.environ[k] for k in ("HOME", "SSH_AUTH_SOCK") if k in os.environ}
        self.env.update(
            {
                "PATH": "/usr/bin:/bin",
                "LANG": "C",
                "LC_ALL": "C",
                "GIT_OPTIONAL_LOCKS": "0",
                "GIT_TERMINAL_PROMPT": "0",
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_SSH_COMMAND": "/usr/bin/ssh -oBatchMode=yes",
                "GIT_ALLOW_PROTOCOL": "ssh",
                "GIT_PROTOCOL_FROM_USER": "0",
            }
        )
        self.options = [
            "-c",
            f"core.hooksPath={hooks}",
            "-c",
            "core.fsmonitor=false",
            "-c",
            "submodule.recurse=false",
            "-c",
            "fetch.recurseSubmodules=false",
            "-c",
            "maintenance.auto=false",
            "-c",
            "gc.auto=0",
            "-c",
            "core.untrackedCache=false",
            "-c",
            "core.pager=cat",
            "-c",
            "credential.helper=",
            "-c",
            "fetch.writeCommitGraph=false",
        ]

    def run(self, path: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [_GIT, *self.options, "-C", str(path), *args],
            env=self.env,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )

    def text(self, path: Path, *args: str) -> str:
        result = self.run(path, list(args))
        if result.returncode:
            raise Refusal(f"Git {args[0]} failed; maintenance stopped")
        return result.stdout if "-z" in args else result.stdout.strip()

    def config(self, path: Path, *, inherited: bool = False) -> list[tuple[str, str]]:
        env = self.env.copy()
        if inherited:
            # Read (never execute) installed global/system config to avoid
            # silently dropping required filters or attribute transformations.
            env.pop("GIT_CONFIG_GLOBAL")
            env.pop("GIT_CONFIG_NOSYSTEM")
        result = subprocess.run(
            [_GIT, "-C", str(path), "config", "--null", "--list"],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if result.returncode:
            raise Refusal("cannot inspect repository configuration")
        return [tuple(item.split("\n", 1)) for item in result.stdout.split("\0") if "\n" in item]


@contextmanager
def git_session():
    # No caller-controlled TMPDIR; this directory has no hooks or contents.
    with tempfile.TemporaryDirectory(prefix="sibling-git-", dir="/tmp") as scratch:
        yield Git(Path(scratch))


def _safe_config(git: Git, path: Path) -> None:
    for key, value in git.config(path, inherited=True):
        key = key.lower()
        if (
            key in {"core.worktree", "core.sshcommand", "core.attributesfile"}
            or (key == "core.bare" and value != "false")
            or key.startswith(("include.", "includeif.", "url."))
            or key in {"core.gitproxy", "extensions.refstorage"}
            or (key.startswith("remote.") and key.endswith((".uploadpack", ".vcs")))
            or key.startswith("uploadpack.")
            or (key.startswith("branch.") and key.endswith(".mergeoptions"))
        ):
            raise Refusal("unsupported redirect, transport, or executable configuration")


def _metadata_safe(git_dir: Path, primary: Path) -> None:
    if not git_dir.is_relative_to(primary.parent) or git_dir.is_relative_to(primary):
        raise Refusal("metadata overlaps the protected repository or leaves the sibling")
    for base, dirs, files in os.walk(git_dir, followlinks=False):
        for name in [*dirs, *files]:
            entry = Path(base) / name
            if entry.is_symlink() or (entry.is_file() and entry.stat().st_nlink > 1):
                raise Refusal("symlinked or shared metadata is unsupported")
    if (git_dir / "objects/info/alternates").exists():
        raise Refusal("shared object metadata is unsupported")


def resolve_repository(key: str, primary: Path, git: Git) -> Repository:
    catalog = load_fleet_repos()
    spec = catalog.get(key)
    if spec is None or spec.default or key == "public":
        raise Refusal("select a registered non-default sibling repository")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", spec.local_name) or not re.fullmatch(
        r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", spec.github
    ):
        raise Refusal("invalid registry repository identity")
    lexical = _plain_path(primary.parent / spec.local_name)
    _, checkout = resolve_fleet_repo(key, primary_root=primary, repos=catalog)
    if checkout != lexical or checkout == primary:
        raise Refusal("checkout overlaps the protected repository")
    git_dir, common = _git_dir(checkout)
    if git_dir != common or not common.is_relative_to(checkout):
        raise Refusal("sibling must own independent metadata beneath its checkout")
    _metadata_safe(common, primary)
    _safe_config(git, checkout)
    actual = git.text(
        checkout,
        "rev-parse",
        "--path-format=absolute",
        "--show-toplevel",
        "--absolute-git-dir",
        "--git-common-dir",
        "--git-path",
        "index",
    ).splitlines()
    expected = [checkout, git_dir, common, git_dir / "index"]
    if len(actual) != 4 or [_plain_path(Path(p), exists=False) for p in actual] != expected:
        raise Refusal("Git paths do not match the independent registered checkout")
    canonical = f"git@github.com:{spec.github}.git"
    urls = [v for k, v in git.config(checkout) if k == "remote.origin.url"]
    if urls not in ([canonical], [f"ssh://git@github.com/{spec.github}.git"]):
        raise Refusal("origin must be the registered canonical GitHub SSH remote")
    return Repository(key, checkout, git_dir, common, canonical)


def _clean(git: Git, checkout: Path) -> None:
    if git.text(checkout, "status", "--porcelain=v1", "--untracked-files=all", "--ignore-submodules=none"):
        raise Refusal("checkout is dirty; preserve local work before maintenance")


def _checkout_safe(git: Git, checkout: Path, commit: str) -> None:
    # Inspect attributes before status can invoke a configured clean filter.
    # Also refuse attribute-declared transformations even if
    # their required global driver would otherwise be dropped by isolation.
    paths = git.text(checkout, "ls-tree", "-r", "--name-only", "-z", commit)
    paths += git.text(checkout, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
    if not paths:
        return
    for name in paths.split("\0"):
        if not name:
            continue
        entry = _plain_path(checkout / name, exists=False)
        if not entry.is_relative_to(checkout) or (entry.is_file() and entry.stat().st_nlink > 1):
            raise Refusal("checkout paths are redirected or shared")
    for source in ([f"--source={commit}"], ["--cached"], []):
        result = subprocess.run(
            [_GIT, *git.options, "-C", str(checkout), "check-attr", *source, "-z", "--stdin", "filter"],
            input=paths,
            env=git.env,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if result.returncode or any(v not in {"unspecified", "unset"} for v in result.stdout.split("\0")[2::3]):
            raise Refusal("checkout filters are unsupported; required transformations are preserved by refusal")
    if any(
        line.startswith(("160000 ", "120000 ")) for line in git.text(checkout, "ls-tree", "-r", commit).splitlines()
    ):
        raise Refusal("submodule and symlink checkouts are unsupported")


def sync_main(repo: Repository, primary: Path, git: Git) -> dict:
    def preflight() -> str:
        if resolve_repository(repo.key, primary, git) != repo:
            raise Refusal("repository identity changed")
        if git.text(repo.checkout, "symbolic-ref", "--quiet", "HEAD") != "refs/heads/main":
            raise Refusal("checkout must already be on main")
        head = git.text(repo.checkout, "rev-parse", "--verify", "HEAD^{commit}")
        _checkout_safe(git, repo.checkout, head)
        _clean(git, repo.checkout)
        return head

    old = preflight()
    git.text(
        repo.checkout,
        "fetch",
        "--no-tags",
        "--no-recurse-submodules",
        "--no-auto-maintenance",
        "--refmap=",
        "--upload-pack=git-upload-pack",
        "--",
        repo.remote,
        "refs/heads/main",
    )
    fetched = git.text(repo.checkout, "rev-parse", "--verify", "FETCH_HEAD^{commit}")
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", fetched):
        raise Refusal("fetch did not return a commit")
    if git.run(repo.checkout, ["merge-base", "--is-ancestor", old, fetched]).returncode:
        raise Refusal("main is diverged or locally ahead; fast-forward refused")
    _checkout_safe(git, repo.checkout, fetched)
    if preflight() != old:
        raise Refusal("checkout changed during fetch")
    git.text(repo.checkout, "merge", "--ff-only", "--no-edit", "--no-stat", fetched)
    if git.text(repo.checkout, "rev-parse", "HEAD") != fetched:
        raise Refusal("fast-forward verification failed")
    _clean(git, repo.checkout)
    return {"repo": repo.key, "verb": "sync-main", "head": fetched, "changed": old != fetched}


def status(repo: Repository, git: Git) -> dict:
    head = git.text(repo.checkout, "rev-parse", "HEAD")
    _checkout_safe(git, repo.checkout, head)
    branch = git.run(repo.checkout, ["symbolic-ref", "--short", "HEAD"])
    worktrees = []
    listing = git.text(repo.checkout, "worktree", "list", "--porcelain", "-z")
    for block in listing.split("\0\0"):
        fields = block.split("\0")
        if not fields or not fields[0].startswith("worktree "):
            continue
        path = Path(fields[0][9:])
        worktrees.append(
            {
                "location": str(path.relative_to(repo.checkout))
                if path.is_relative_to(repo.checkout)
                else "outside checkout",
                "head": next((line[5:] for line in fields if line.startswith("HEAD ")), None),
                "branch": next((line[7:] for line in fields if line.startswith("branch ")), None),
                "locked": any(line == "locked" or line.startswith("locked ") for line in fields),
            }
        )
    return {
        "repo": repo.key,
        "verb": "status",
        "branch": branch.stdout.strip() if branch.returncode == 0 else None,
        "head": head,
        "clean": not bool(git.text(repo.checkout, "status", "--porcelain=v1", "--untracked-files=all")),
        "worktree_count": len(worktrees),
        "worktrees": worktrees,
    }


def worktree_remove(repo: Repository, primary: Path, git: Git, raw: str) -> dict:
    target = _plain_path(Path(raw))
    dispatch = repo.checkout / ".worktrees/dispatch"
    if not target.is_relative_to(dispatch) or len(target.relative_to(dispatch).parts) != 2:
        raise Refusal("removal requires one registered dispatch worktree beneath the sibling dispatch root")
    # Dispatch already established this shared lock. Do not create public
    # metadata merely to remove a sibling tree.
    _, primary_common = _git_dir(primary)
    lock_dir = primary_common / worktree_claims.LOCK_DIR_NAME
    _, lock_file = worktree_claims.lock_path(target, lock_dir=lock_dir)
    if not lock_file.is_file():
        raise Refusal("dispatch ownership lock is missing; use the existing cleanup workflow")
    _plain_path(lock_file)

    def releasable() -> tuple[bool, str]:
        resolve_repository(repo.key, primary, git)
        _plain_path(target)
        marker, common = _git_dir(target)
        if common != repo.common or not marker.is_relative_to(repo.common / "worktrees"):
            return False, "target metadata is not owned by the sibling"
        listing = git.text(repo.checkout, "worktree", "list", "--porcelain", "-z").split("\0\0")
        entries = [entry.split("\0") for entry in listing]
        record = next((entry for entry in entries if f"worktree {target}" in entry), None)
        if record is None or any(line == "locked" or line.startswith("locked ") for line in record):
            return False, "target is unregistered or locked"
        _safe_config(git, target)
        _checkout_safe(git, target, git.text(target, "rev-parse", "HEAD"))
        _clean(git, target)
        return True, "registered, clean and unlocked"

    result = worktree_claims.remove_unclaimed_worktree(
        target,
        repo_root=repo.checkout,
        reason="closed sibling maintenance",
        owner_task_id=None,
        force=False,
        releasable=releasable,
        tasks_dir=primary / "batch_state/tasks",
        lock_dir=lock_dir,
        lock_timeout_s=0,
        git_runner=git.run,
    )
    if result.action != "removed":
        raise Refusal("cleanup policy refused or removal failed; local work preserved")
    return {"repo": repo.key, "verb": "worktree-remove", "removed": True}


def examples(interpreter: str = ".venv/bin/python") -> str:
    prefix = f"{interpreter} -m scripts.fleet.sibling_git"
    return f"{prefix} status --repo infra-private\n{prefix} sync-main --repo infra-private\n{prefix} worktree-remove --repo infra-private '/absolute/sibling/.worktrees/dispatch/codex/finished task'"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Maintain a registered sibling with three closed Git verbs.\nUse from this repository root; raw sibling Git and arbitrary Git arguments receive no exemption.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        allow_abbrev=False,
        epilog=f"Examples (use the shared project's absolute interpreter from a dispatch root):\n{examples()}\n\nOutputs: JSON on stdout; sync-main fetches and fast-forwards main; worktree-remove removes one clean, unlocked, unclaimed dispatch tree without force.\nExit codes: 0 success; 2 invalid invocation or refused maintenance.\nRelated: docs/runbooks/sibling-git.md; scripts/config/fleet_repos.yaml; #9309.",
    )
    parser.add_argument(
        "verb",
        choices=("status", "sync-main", "worktree-remove"),
        help="Closed verb: status, sync-main, or worktree-remove (required).",
    )
    parser.add_argument(
        "--repo", required=True, help="Registered non-default sibling name, e.g. infra-private (required; no default)."
    )
    parser.add_argument(
        "path",
        nargs="?",
        help="For worktree-remove only: absolute registered dispatch path, quoted if it contains spaces.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_intermixed_args(argv)
    if (args.verb == "worktree-remove") != bool(args.path):
        parser.error("only worktree-remove requires a path")
    try:
        primary = primary_root()
        with git_session() as git:
            repo = resolve_repository(args.repo, primary, git)
            if args.verb == "sync-main":
                result = sync_main(repo, primary, git)
            elif args.verb == "worktree-remove":
                result = worktree_remove(repo, primary, git, args.path)
            else:
                result = status(repo, git)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (ValueError, OSError, RuntimeError, subprocess.SubprocessError) as exc:
        reason = str(exc) if isinstance(exc, Refusal) else "dependency or repository validation failed"
        print(
            f"Refused: {reason}.\nRun from this repository root, using the project interpreter:\n{examples()}",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
