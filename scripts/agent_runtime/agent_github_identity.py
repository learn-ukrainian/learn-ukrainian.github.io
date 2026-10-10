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
import ssl
import stat
import subprocess
import sys
import time
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import jwt

from scripts.common.github_client import http_open

_GITHUB_API_URL = "https://api.github.com"
_REPO_ROOT = Path(__file__).resolve().parents[2]
_GIT_TIMEOUT_SECONDS = 30


class GitHubIdentityError(RuntimeError):
    """Raised when configured agent identity material cannot be used safely."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


@dataclass(frozen=True)
class GitHubIdentity:
    """A resolved token and its deliberately non-secret provenance."""

    token: str | None = field(repr=False)
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
            timeout=_GIT_TIMEOUT_SECONDS,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise GitHubIdentityError("cannot determine the repository for the GitHub App token") from exc

    remote = remote.removesuffix(".git").rstrip("/")
    if ":" in remote and "/" not in remote.split(":", 1)[0]:
        remote = remote.rsplit(":", 1)[1]
    if "/" not in remote:
        raise GitHubIdentityError("cannot determine the repository for the GitHub App token")
    return remote.rsplit("/", 1)[1]


def _restricted_opener(ssl_context=None):
    """Exclude ambient proxies, redirects and environment-selected TLS trust."""
    if ssl_context is None:
        trust = ssl.get_default_verify_paths()
        cafile = trust.openssl_cafile if Path(trust.openssl_cafile).is_file() else None
        capath = trust.openssl_capath if Path(trust.openssl_capath).is_dir() else None
        if not cafile and not capath:
            raise ValueError("default TLS trust unavailable")
        ssl_context = ssl.create_default_context(cafile=cafile, capath=capath)
    return urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        _NoRedirect(),
        urllib.request.HTTPSHandler(context=ssl_context),
    )


def revoke_installation_token(
    token: str, *, api_base_url: str = _GITHUB_API_URL, ssl_context=None,
) -> None:
    """Revoke this installation credential without exposing response diagnostics."""
    try:
        request = urllib.request.Request(
            f"{api_base_url}/installation/token",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "User-Agent": "learn-ukrainian-agent-runtime",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            method="DELETE",
        )
        with http_open(request, opener=_restricted_opener(ssl_context).open, timeout=15) as response:
            if response.status != 204:
                raise ValueError("unexpected revocation response")
    except Exception:
        raise GitHubIdentityError("GitHub App installation token revocation failed") from None


def mint_installation_token(
    *,
    app_id: str,
    private_key: str,
    installation_id: str,
    repository: str | None = None,
    now: int | None = None,
    permissions: Mapping[str, str] | None = None,
    api_base_url: str = _GITHUB_API_URL,
    ssl_context=None,
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
    selected = repository or _repository_name()
    request_body: dict[str, Any] = {"repositories": [selected.rsplit("/", 1)[-1]]}
    if permissions is not None:
        request_body["permissions"] = dict(permissions)
    body = json.dumps(request_body).encode("utf-8")
    request = urllib.request.Request(
        f"{api_base_url}/app/installations/{installation_id}/access_tokens",
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
        open_request = urllib.request.urlopen if permissions is None else _restricted_opener(ssl_context).open
        with http_open(request, opener=open_request, timeout=15) as response:
            payload: dict[str, Any] = json.loads(response.read().decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("invalid response")
    except Exception as exc:  # HTTP errors deliberately contain no token in the message.
        raise GitHubIdentityError("GitHub App installation token minting failed") from exc

    token = payload.get("token")
    if not isinstance(token, str) or not token:
        raise GitHubIdentityError("GitHub App installation token response did not contain a token")
    if permissions is not None:
        try:
            repositories = payload["repositories"]
            if not isinstance(repositories, list) or len(repositories) != 1:
                raise ValueError("invalid repository scope")
            if "/" not in selected or repositories[0]["full_name"] != selected:
                raise ValueError("invalid repository identity")
            granted = payload["permissions"]
            levels = {"read": 1, "write": 2, "admin": 3}
            ceilings = {"metadata": "read", **permissions}
            if (
                not isinstance(granted, dict)
                or any(
                    value not in levels or levels[value] > levels.get(ceilings.get(key), 0)
                    for key, value in granted.items()
                )
                or any(granted.get(key) != value for key, value in permissions.items())
            ):
                raise ValueError("invalid permissions")
            expires = datetime.fromisoformat(payload["expires_at"].replace("Z", "+00:00"))
            if expires.tzinfo is None or expires <= datetime.fromtimestamp(time.time() if now is None else issued_at, UTC):
                raise ValueError("invalid expiry")
        except (KeyError, TypeError, ValueError, AttributeError, OverflowError) as exc:
            raise GitHubIdentityError("GitHub App installation token scope or expiry refused") from exc
    return token


def resolve_agent_github_identity(
    *,
    environment: Mapping[str, str] | None = None,
    bash_secrets_path: Path | None = None,
    repository: str | None = None,
    permissions: Mapping[str, str] | None = None,
    api_base_url: str = _GITHUB_API_URL,
    ssl_context=None,
) -> GitHubIdentity:
    """Resolve App, dedicated-token, then temporary legacy identity.

    A partial App configuration is an operator setup error, rather than a
    reason to silently fall through to a broader credential.
    """
    env = os.environ if environment is None else environment
    private_key = env.get("LU_AGENT_GITHUB_APP_PRIVATE_KEY")
    key_file = env.get("LU_AGENT_GITHUB_APP_PRIVATE_KEY_FILE")
    if key_file and not private_key:
        try:
            info = os.stat(key_file, follow_symlinks=False)
            if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) & 0o077:
                raise OSError("key file is not private and regular")
            flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
            fd = os.open(key_file, flags)
            try:
                opened = os.fstat(fd)
                if (
                    not stat.S_ISREG(opened.st_mode)
                    or stat.S_IMODE(opened.st_mode) & 0o077
                    or (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino)
                ):
                    raise OSError("key file changed or is not private and regular")
                with os.fdopen(fd, encoding="utf-8") as stream:
                    fd = None
                    private_key = stream.read()
            finally:
                if fd is not None:
                    os.close(fd)
        except (OSError, UnicodeError):
            raise GitHubIdentityError("cannot read the configured key file") from None
    app_fields = {
        "LU_AGENT_GITHUB_APP_ID": env.get("LU_AGENT_GITHUB_APP_ID"),
        "LU_AGENT_GITHUB_APP_PRIVATE_KEY": private_key,
        "LU_AGENT_GITHUB_APP_INSTALLATION_ID": env.get("LU_AGENT_GITHUB_APP_INSTALLATION_ID"),
    }
    if any(app_fields.values()) or key_file:
        if not all(app_fields.values()):
            raise GitHubIdentityError("incomplete LU_AGENT_GITHUB_APP_* configuration")
        restricted = (
            {}
            if permissions is None
            else {
                "permissions": permissions,
                "api_base_url": api_base_url,
                "ssl_context": ssl_context,
            }
        )
        return GitHubIdentity(
            token=mint_installation_token(
                app_id=app_fields["LU_AGENT_GITHUB_APP_ID"] or "",
                private_key=app_fields["LU_AGENT_GITHUB_APP_PRIVATE_KEY"] or "",
                installation_id=app_fields["LU_AGENT_GITHUB_APP_INSTALLATION_ID"] or "",
                repository=repository,
                **restricted,
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
