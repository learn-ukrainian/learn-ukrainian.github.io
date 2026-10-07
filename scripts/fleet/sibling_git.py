"""Closed sibling maintenance verbs; no arbitrary Git or shell interface (#9309).

Host Git/SSH and the installed project interpreter are trusted. Repository
configuration, caller environment, and path arguments are not. See
``docs/runbooks/sibling-git.md`` for the supported transport and refusal contract.
"""

from __future__ import annotations

import argparse
import base64
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

import yaml

from scripts.agent_runtime.agent_github_identity import resolve_agent_github_identity, revoke_installation_token
from scripts.orchestration import worktree_claims
from scripts.orchestration.execution_safe_git import LOCAL_COMMANDS, SafeGitRunner
from scripts.orchestration.execution_safe_git import run_git as safe_git
from scripts.orchestration.fleet_repos import load_fleet_repos, resolve_fleet_repo

_GIT = "/usr/bin/git"
_FETCH_REMOTE = "sibling-git-canonical"
_SOURCE_ROOT = Path(__file__).resolve().parents[2]
_REGISTRY_PATH = _SOURCE_ROOT / "scripts/config/fleet_repos.yaml"


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
    transport: str = "ssh"
    github: str = ""


def _registry_transport(key: str) -> str:
    try:
        document = yaml.safe_load(_REGISTRY_PATH.read_text(encoding="utf-8"))
        transport = document["repos"].get(key, {}).get("transport", "ssh")
    except (OSError, yaml.YAMLError, KeyError, TypeError, AttributeError) as exc:
        raise Refusal("cannot inspect registered transport") from exc
    if transport not in ("ssh", "https"):
        raise Refusal("unsupported registered transport")
    return transport


def _https_url(remote: str, github: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9_-][A-Za-z0-9_.-]*/[A-Za-z0-9_-][A-Za-z0-9_.-]*", github) or remote not in (
        f"https://github.com/{github}.git",
        f"https://github.com/{github}",
    ):
        raise Refusal("origin must be the registered canonical HTTPS remote")


class Git:
    """One fixed executable and command configuration, including read probes."""

    def __init__(
        self,
        hooks: Path,
        *,
        https_base_url: str | None = None,
        ca_file: Path | None = None,
        api_base_url: str = "https://api.github.com",
        ssl_context=None,
    ):
        # Constructor-only seams; the CLI never takes endpoint or CA overrides.
        self.scratch = hooks
        self.https_base_url = https_base_url
        self.ca_file = ca_file
        self.api_base_url = api_base_url
        self.ssl_context = ssl_context
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
            "--no-pager",
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
            "core.editor=/usr/bin/false",
            "-c",
            "sequence.editor=/usr/bin/false",
            "-c",
            "core.askPass=/usr/bin/false",
            "-c",
            "merge.verifySignatures=false",
            "-c",
            "merge.gpgSign=false",
            "-c",
            "gpg.program=/usr/bin/false",
            "-c",
            "gpg.openpgp.program=/usr/bin/false",
            "-c",
            "gpg.x509.program=/usr/bin/false",
            "-c",
            "gpg.ssh.program=/usr/bin/false",
            "-c",
            "diff.external=/usr/bin/false",
            "-c",
            "credential.helper=",
            "-c",
            "credential.interactive=false",
            "-c",
            "protocol.allow=never",
            "-c",
            "protocol.ssh.allow=always",
            "-c",
            "fetch.writeCommitGraph=false",
        ]

    def run(self, path: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
        if args and args[0] in LOCAL_COMMANDS:
            return safe_git(
                args,
                cwd=path,
                runner=SafeGitRunner(_GIT),
                env=self.env,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
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

    def fetch(self, repo: Repository) -> None:
        args = [
            "-c",
            f"remote.{_FETCH_REMOTE}.url={repo.remote}",
            "fetch",
            "--no-tags",
            "--no-recurse-submodules",
            "--no-auto-maintenance",
            "--refmap=",
            "--upload-pack=git-upload-pack",
            "--",
            _FETCH_REMOTE,
            "refs/heads/main",
        ]
        if repo.transport == "ssh":
            self.text(repo.checkout, *args)
            return
        _safe_config(self, repo.checkout, https=True)
        _https_url(repo.remote, repo.github)
        # Resolve in the parent; no credential material enters other Git verbs.
        app_environment = {
            k: os.environ[k]
            for k in (
                "LU_AGENT_GITHUB_APP_ID",
                "LU_AGENT_GITHUB_APP_INSTALLATION_ID",
                "LU_AGENT_GITHUB_APP_PRIVATE_KEY",
                "LU_AGENT_GITHUB_APP_PRIVATE_KEY_FILE",
            )
            if k in os.environ
        }
        if not any(app_environment.values()):
            raise Refusal("HTTPS transport requires an App installation identity")
        try:
            identity = resolve_agent_github_identity(
                environment=app_environment,
                repository=repo.github,
                permissions={"contents": "read"},
                api_base_url=self.api_base_url,
                ssl_context=self.ssl_context,
            )
        except Exception:
            raise Refusal("restricted installation credential unavailable") from None
        if identity.source != "app" or not identity.token:
            raise Refusal("HTTPS transport requires an App installation identity")
        try:
            url = (
                repo.remote
                if self.https_base_url is None
                else self.https_base_url + repo.remote.removeprefix("https://github.com")
            )
            header = "Authorization: Basic " + base64.b64encode(f"x-access-token:{identity.token}".encode()).decode(
                "ascii"
            )
            env = {
                "PATH": "/usr/bin:/bin",
                "LANG": "C",
                "LC_ALL": "C",
                "HOME": str(self.scratch),
                "GIT_OPTIONAL_LOCKS": "0",
                "GIT_TERMINAL_PROMPT": "0",
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_ALLOW_PROTOCOL": "https",
                "GIT_PROTOCOL_FROM_USER": "0",
            }
            settings = [
                (f"remote.{_FETCH_REMOTE}.url", url),
                ("protocol.https.allow", "always"),
                ("http.followRedirects", "false"),
                ("http.proxy", ""),
                ("http.sslVerify", "true"),
                ("credential.helper", ""),
                ("credential.useHttpPath", "true"),
                ("credential.interactive", "false"),
                ("transfer.credentialsInUrl", "die"),
                (f"http.{url}.extraHeader", header),
            ]
            if self.ca_file is not None:
                settings.append(("http.sslCAInfo", str(self.ca_file)))
            # Match the exact fetch URL so repository URL-specific entries cannot
            # override our transport settings after the last configuration probe.
            settings.extend(
                (f"http.{url}.{key.removeprefix('http.')}", value)
                for key, value in tuple(settings)
                if key.startswith("http.") and not key.startswith(f"http.{url}.")
            )
            env["GIT_CONFIG_COUNT"] = str(len(settings))
            for index, (key, value) in enumerate(settings):
                env[f"GIT_CONFIG_KEY_{index}"] = key
                env[f"GIT_CONFIG_VALUE_{index}"] = value
            try:
                result = subprocess.run(
                    [_GIT, *self.options, "-C", str(repo.checkout), *args[2:]],
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=120,
                    check=False,
                )
            except (OSError, subprocess.SubprocessError):
                raise Refusal("HTTPS fetch failed; maintenance stopped") from None
            if result.returncode:
                raise Refusal("HTTPS fetch failed; maintenance stopped")
        finally:
            try:
                revoke_installation_token(identity.token, api_base_url=self.api_base_url, ssl_context=self.ssl_context)
            except Exception:
                print("Installation credential revocation failed", file=sys.stderr)

    def config(self, path: Path, *, inherited: bool = False) -> list[tuple[str, str, str]]:
        env = self.env.copy()
        if inherited:
            # Read (never execute) installed global/system config to avoid
            # silently dropping required filters or attribute transformations.
            env.pop("GIT_CONFIG_GLOBAL")
            env.pop("GIT_CONFIG_NOSYSTEM")
        result = subprocess.run(
            [_GIT, "-C", str(path), "config", "--null", "--list", "--show-scope"],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if result.returncode:
            raise Refusal("cannot inspect repository configuration")
        fields = result.stdout.split("\0")
        return [
            (scope, *item.split("\n", 1))
            for scope, item in zip(fields[::2], fields[1::2], strict=False)
            if "\n" in item
        ]


@contextmanager
def git_session():
    # No caller-controlled TMPDIR; this directory has no hooks or contents.
    with tempfile.TemporaryDirectory(prefix="sibling-git-", dir="/tmp") as scratch:
        yield Git(Path(scratch))


def _safe_config(git: Git, path: Path, *, https: bool = False) -> None:
    for scope, key, value in git.config(path, inherited=True):
        key = key.lower()
        remote_name = key[7:].rsplit(".", 1)[0] if key.startswith("remote.") else ""
        if (
            key in {"core.worktree", "core.sshcommand", "core.attributesfile"}
            or (key == "core.bare" and value != "false")
            or key.startswith(("include.", "includeif.", "url."))
            or key
            in {
                "core.gitproxy",
                "core.alternaterefscommand",
                "extensions.refstorage",
                "extensions.partialclone",
                "gc.recentobjectshook",
                "gpg.ssh.defaultkeycommand",
            }
            or (
                key.startswith("remote.")
                and key.endswith((".uploadpack", ".vcs", ".proxy", ".proxyauthmethod", ".promisor"))
            )
            # Git resolves remote names before URLs. Reserve our fetch remote
            # entirely; even another URL value would precede a -c override.
            or remote_name == _FETCH_REMOTE
            or any(c in remote_name for c in "/:")
            or key.endswith((".bundleuri", ".bundlecreationtoken"))
            or (key.startswith("bundle.") and key.endswith(".uri"))
            or key.startswith("uploadpack.")
            or key.startswith("http.")
            # Inherited helpers are inspected but excluded from execution;
            # repository and command scopes remain untrusted.
            or (
                key.startswith("credential.")
                and scope not in {"global", "system"}
                and (https or (key.endswith(".helper") and key != "credential.helper"))
            )
            or (key.startswith("diff.") and key.endswith((".command", ".textconv")))
            or (
                key.startswith("gpg.")
                and key.endswith("program")
                and key
                not in {
                    "gpg.program",
                    "gpg.openpgp.program",
                    "gpg.x509.program",
                    "gpg.ssh.program",
                }
            )
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
    transport = _registry_transport(key)
    _safe_config(git, checkout, https=transport == "https")
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
    canonical = f"git@github.com:{spec.github}.git" if transport == "ssh" else f"https://github.com/{spec.github}.git"
    urls = [v for _, k, v in git.config(checkout) if k == "remote.origin.url"]
    if transport == "https":
        if len(urls) != 1:
            raise Refusal("origin must have one registered canonical HTTPS remote")
        _https_url(urls[0], spec.github)
        canonical = urls[0]
    elif urls not in ([canonical], [f"ssh://git@github.com/{spec.github}.git"]):
        raise Refusal("origin must be the registered canonical GitHub SSH remote")
    return Repository(key, checkout, git_dir, common, canonical, transport, spec.github)


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
    git.fetch(repo)
    fetched = git.text(repo.checkout, "rev-parse", "--verify", "FETCH_HEAD^{commit}")
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", fetched):
        raise Refusal("fetch did not return a commit")
    if git.run(repo.checkout, ["merge-base", "--is-ancestor", old, fetched]).returncode:
        raise Refusal("main is diverged or locally ahead; fast-forward refused")
    _checkout_safe(git, repo.checkout, fetched)
    if preflight() != old:
        raise Refusal("checkout changed during fetch")
    added = set(
        git.text(
            repo.checkout,
            "diff",
            "--no-ext-diff",
            "--no-textconv",
            "--no-renames",
            "--name-only",
            "--diff-filter=A",
            "-z",
            old,
            fetched,
            "--",
        ).split("\0")
    ) - {""}
    ignored = set(
        git.text(
            repo.checkout,
            "ls-files",
            "--others",
            "--ignored",
            "--exclude-standard",
            "-z",
        ).split("\0")
    ) - {""}
    if added & ignored:
        raise Refusal("fast-forward would overwrite ignored local files; preserve local work")
    git.text(repo.checkout, "merge", "--ff-only", "--no-edit", "--no-stat", "--no-overwrite-ignore", fetched)
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
    reachability_refusal = None

    def releasable() -> tuple[bool, str]:
        nonlocal reachability_refusal
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
        _safe_config(git, target, https=repo.transport == "https")
        head = git.text(target, "rev-parse", "--verify", "HEAD^{commit}")
        _checkout_safe(git, target, head)
        _clean(git, target)
        # A detached worker commit has no branch keeping it reachable after
        # removal. Task status alone is not proof that its work was pushed.
        reachability_refusal = "HEAD reachability is unknown"
        try:
            if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", head):
                return False, reachability_refusal
            tasks = primary / "batch_state/tasks"
            needles = worktree_claims.worktree_claim_needles(target, target)
            bases = set()
            for state_file in sorted(tasks.iterdir()):
                if state_file.suffix != ".json" or worktree_claims.is_superseded_record(state_file):
                    continue
                raw = state_file.read_bytes()
                if not worktree_claims.record_may_claim_worktree(raw, needles):
                    continue
                state = json.loads(raw)
                if not isinstance(state, dict):
                    return False, reachability_refusal
                claimed = state.get("worktree_path")
                if claimed is None:
                    continue
                if not isinstance(claimed, str):
                    return False, reachability_refusal
                if worktree_claims.resolve_claim_path(claimed, repo_root=repo.checkout) != target:
                    continue
                if "worktree_base_sha" in state:
                    base = state["worktree_base_sha"]
                    if not isinstance(base, str) or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", base):
                        return False, reachability_refusal
                    if git.text(target, "rev-parse", "--verify", f"{base}^{{commit}}") != base:
                        return False, reachability_refusal
                    bases.add(base)
            if len(bases) > 1:
                return False, reachability_refusal
            if bases == {head}:
                reachability_refusal = None
                return True, "registered, clean, unlocked and at recorded base"
            # Only the validated canonical origin's fetched refs count; local
            # branches, tags, other remotes and FETCH_HEAD do not prove a push.
            refs = git.text(
                repo.checkout, "for-each-ref", "--format=%(refname)", "--contains", head, "refs/remotes/origin/"
            ).splitlines()
            if any(ref.startswith("refs/remotes/origin/") and ref != "refs/remotes/origin/HEAD" for ref in refs):
                reachability_refusal = None
                return True, "registered, clean, unlocked and reachable from canonical remote"
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
            return False, reachability_refusal
        reachability_refusal = "HEAD is neither the recorded base nor reachable from canonical remote refs (unpushed)"
        return False, reachability_refusal

    result = worktree_claims.remove_unclaimed_worktree(
        target,
        repo_root=repo.checkout,
        reason="closed sibling maintenance",
        control_root=primary,
        owner_task_id=None,
        force=False,
        releasable=releasable,
        tasks_dir=primary / "batch_state/tasks",
        lock_dir=lock_dir,
        lock_timeout_s=0,
        git_runner=SafeGitRunner(_GIT),
    )
    if result.action != "removed":
        raise Refusal(f"{reachability_refusal or 'cleanup policy refused or removal failed'}; local work preserved")
    return {"repo": repo.key, "verb": "worktree-remove", "removed": True}


def examples(interpreter: str = ".venv/bin/python") -> str:
    prefix = f"{interpreter} -m scripts.fleet.sibling_git"
    return f"{prefix} status --repo infra-private\n{prefix} sync-main --repo infra-private\n{prefix} worktree-remove --repo infra-private '/absolute/sibling/.worktrees/dispatch/codex/finished task'"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Maintain a registered sibling with three closed Git verbs.\nUse from this repository root; raw sibling Git and arbitrary Git arguments receive no exemption.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        allow_abbrev=False,
        epilog=f"Examples (use the shared project's absolute interpreter from a dispatch root):\n{examples()}\n\nOutputs: JSON on stdout; sync-main fetches and fast-forwards main; worktree-remove removes one clean, unlocked, unclaimed dispatch tree without force, only at its recorded base or reachable from canonical origin's fetched refs.\nExit codes: 0 success; 2 invalid invocation or refused maintenance.\nRelated: docs/runbooks/sibling-git.md; scripts/config/fleet_repos.yaml; #9309; #9742.",
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
