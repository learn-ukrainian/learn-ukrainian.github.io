"""Explicit Git credentials for exact registry HTTPS destinations.

Git URL credential scopes match path prefixes. The helper additionally checks
the full credential context before delegating to gh's existing authenticated
store. Only gh and Git handle credential bytes, over their private pipe.
"""

import os
import re
import shlex
from pathlib import Path

import yaml

from scripts.opsec.prepublish import PublishBlocked, real_gh

CONFIG = Path(__file__).resolve().parents[1] / "config" / "fleet_repos.yaml"


def canonical_origins(repository: dict) -> tuple[str, ...]:
    """Derive exact destinations from registry identity, not clone transport."""
    github = repository["github"]
    transport = repository.get("transport", "ssh")
    if transport == "file" and Path(github).is_absolute():
        return (github,)
    if not re.fullmatch(r"[A-Za-z0-9_-][A-Za-z0-9_.-]*/[A-Za-z0-9_-][A-Za-z0-9_.-]*", github):
        raise ValueError("invalid registered repository identity")
    if transport not in ("https", "ssh"):
        raise ValueError("unsupported registered transport")
    bases = (f"https://github.com/{github}", f"git@github.com:{github}", f"ssh://git@github.com/{github}")
    return tuple(base + suffix for base in bases for suffix in (".git", ""))


def verification_credentials(remote: str) -> list[str]:
    """Return command-scope settings; never inspect, copy or persist a token.

    Non-HTTPS and unregistered URLs gain no helper. Resolve gh through the same
    pinned executable mechanism as scripts.publish and scripts.common.github_client,
    before the verifier replaces PATH. Missing gh leaves anonymous fetches usable.
    """
    if not remote.startswith("https://github.com/"):
        return []
    repositories = yaml.safe_load(CONFIG.read_text())["repos"].values()
    if not any(remote in canonical_origins(repository) for repository in repositories):
        return []
    try:
        gh = shlex.quote(real_gh(os.environ))
    except PublishBlocked:
        return []
    path = shlex.quote(remote.removeprefix("https://github.com/"))
    # Reconstruct only the validated context. Do not forward store/erase or
    # arbitrary helper input to gh, and do not expose its diagnostics to records.
    helper = (
        '!f() { [ "$1" = get ] || exit 0; protocol= host= path=; '
        'while IFS="=" read -r key value; do '
        'case "$key" in protocol) protocol=$value;; host) host=$value;; path) path=$value;; esac; done; '
        '[ "$protocol" = https ] && [ "$host" = github.com ] && '
        f'[ "$path" = {path} ] || exit 0; '
        f"printf '%s\\n' protocol=https host=github.com path={path} '' | {gh} auth git-credential get 2>/dev/null; "
        '}; f'
    )
    return [
        "credential.helper=",
        "credential.interactive=false",
        f"credential.{remote}.useHttpPath=true",
        f"credential.{remote}.helper=",
        f"credential.{remote}.helper={helper}",
        "http.followRedirects=false",
        f"http.{remote}.followRedirects=false",
    ]
