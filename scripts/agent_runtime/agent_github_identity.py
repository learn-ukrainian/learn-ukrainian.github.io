"""Resolve the least-privileged GitHub identity for dispatched agents.

The operator's interactive GitHub token must never be the normal credential
available to an agent shell.  A repository-scoped GitHub App installation
token is preferred, followed by an explicitly provisioned agent token.  The
legacy operator token route remains only to keep existing dispatches fluid
while App setup is rolled out.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import time
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jwt

_GITHUB_API_URL = "https://api.github.com"
_REPO_ROOT = Path(__file__).resolve().parents[2]


class GitHubIdentityError(RuntimeError):
    """Raised when configured agent identity material cannot be used safely."""


@dataclass(frozen=True)
class GitHubIdentity:
    """A resolved token and its deliberately non-secret provenance."""

    token: str | None
    source: str | None


def _read_legacy_token(path: Path) -> str | None:
    """Read a legacy shell token without evaluating shell source."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None

    for line in lines:
        try:
            parts = shlex.split(line, comments=True, posix=True)
        except ValueError:
            continue
        if parts[:1] == ["export"]:
            parts = parts[1:]
        for part in parts:
            for name in ("GH_TOKEN", "GITHUB_TOKEN"):
                prefix = f"{name}="
                if part.startswith(prefix):
                    value = part.removeprefix(prefix)
                    if value:
                        return value
    return None


def _repository_name(repo_root: Path = _REPO_ROOT) -> str:
    """Return the origin repository name for an installation-token scope."""
    try:
        remote = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise GitHubIdentityError("cannot determine the repository for the GitHub App token") from exc

    remote = remote.removesuffix(".git").rstrip("/")
    if ":" in remote and "/" not in remote.split(":", 1)[0]:
        remote = remote.rsplit(":", 1)[1]
    if "/" not in remote:
        raise GitHubIdentityError("cannot determine the repository for the GitHub App token")
    return remote.rsplit("/", 1)[1]


def mint_installation_token(
    *,
    app_id: str,
    private_key: str,
    installation_id: str,
    repository: str | None = None,
    now: int | None = None,
) -> str:
    """Mint a repository-scoped GitHub App installation token.

    The App's installation permissions define the ceiling.  This request adds
    no workflow, admin, or organization-secret permissions.
    """
    issued_at = int(time.time()) if now is None else now
    signing_key = private_key.replace("\\n", "\n")
    assertion = jwt.encode(
        {"iat": issued_at - 60, "exp": issued_at + 9 * 60, "iss": app_id},
        signing_key,
        algorithm="RS256",
    )
    body = json.dumps({"repositories": [repository or _repository_name()]}).encode("utf-8")
    request = urllib.request.Request(
        f"{_GITHUB_API_URL}/app/installations/{installation_id}/access_tokens",
        data=body,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {assertion}",
            "Content-Type": "application/json",
            "User-Agent": "learn-ukrainian-agent-runtime",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            payload: dict[str, Any] = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # HTTP errors deliberately contain no token in the message.
        raise GitHubIdentityError("GitHub App installation token minting failed") from exc

    token = payload.get("token")
    if not isinstance(token, str) or not token:
        raise GitHubIdentityError("GitHub App installation token response did not contain a token")
    return token


def resolve_agent_github_identity(
    *,
    environment: Mapping[str, str] | None = None,
    bash_secrets_path: Path | None = None,
    repository: str | None = None,
) -> GitHubIdentity:
    """Resolve App, dedicated-token, then temporary legacy identity.

    A partial App configuration is an operator setup error, rather than a
    reason to silently fall through to a broader credential.
    """
    env = os.environ if environment is None else environment
    app_fields = {
        "LU_AGENT_GITHUB_APP_ID": env.get("LU_AGENT_GITHUB_APP_ID"),
        "LU_AGENT_GITHUB_APP_PRIVATE_KEY": env.get("LU_AGENT_GITHUB_APP_PRIVATE_KEY"),
        "LU_AGENT_GITHUB_APP_INSTALLATION_ID": env.get("LU_AGENT_GITHUB_APP_INSTALLATION_ID"),
    }
    if any(app_fields.values()):
        if not all(app_fields.values()):
            raise GitHubIdentityError("incomplete LU_AGENT_GITHUB_APP_* configuration")
        return GitHubIdentity(
            token=mint_installation_token(
                app_id=app_fields["LU_AGENT_GITHUB_APP_ID"] or "",
                private_key=app_fields["LU_AGENT_GITHUB_APP_PRIVATE_KEY"] or "",
                installation_id=app_fields["LU_AGENT_GITHUB_APP_INSTALLATION_ID"] or "",
                repository=repository,
            ),
            source="app",
        )

    token = env.get("LU_AGENT_GITHUB_TOKEN")
    if token:
        return GitHubIdentity(token=token, source="token")

    legacy_token = env.get("GH_TOKEN") or env.get("GITHUB_TOKEN")
    if not legacy_token:
        legacy_token = _read_legacy_token(bash_secrets_path or Path.home() / ".bash_secrets")
    if legacy_token:
        print(
            "WARNING: agent dispatch is using the operator GitHub identity; GitHub App setup is required.",
            file=sys.stderr,
        )
        return GitHubIdentity(token=legacy_token, source="legacy")
    return GitHubIdentity(token=None, source=None)
