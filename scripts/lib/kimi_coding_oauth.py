#!/usr/bin/env python3
"""Print a fresh Kimi Code (coding subscription) OAuth access token.

Reads the credential file written by ``kimi login``
(default ``~/.kimi-code/credentials/kimi-code.json``). If the stored access
token is still valid beyond the safety margin, it is printed as-is; otherwise
the token is refreshed via the standard OAuth ``refresh_token`` grant against
the Kimi auth host and the credential file is updated atomically (keeping the
rotated ``refresh_token`` when the server returns one).

Used by ``start-kimicc.sh --endpoint coding`` both at launch time and as the
Claude Code ``apiKeyHelper`` command, which re-invokes this script periodically
so long sessions survive the short (~15 min) access-token lifetime.

Stdlib-only: safe to run with any Python 3.9+.

Usage:
    kimi_coding_oauth.py token

Exit codes:
    0  token printed on stdout
    2  no usable credentials (file missing / no refresh_token)
    3  refresh request failed

Environment overrides:
    KIMI_CODE_CREDENTIALS_PATH   credential file location
    KIMI_CODE_OAUTH_HOST         auth host (default https://auth.kimi.com)
    KIMI_CODE_OAUTH_CLIENT_ID    OAuth client id (default: kimi-code CLI id)
    KIMI_CODE_OAUTH_MARGIN       seconds of required remaining validity (default 120)
"""

from __future__ import annotations

import contextlib
import fcntl
import json
import os
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_OAUTH_HOST = "https://auth.kimi.com"
# Public client id of the Kimi Code CLI device-code flow (no secret).
DEFAULT_CLIENT_ID = "17e5f671-d194-4dfb-9706-5516cb48c098"
DEFAULT_MARGIN_SECONDS = 120
REQUEST_TIMEOUT_SECONDS = 15


def _credentials_path() -> Path:
    override = os.environ.get("KIMI_CODE_CREDENTIALS_PATH")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".kimi-code" / "credentials" / "kimi-code.json"


def _margin_seconds() -> int:
    raw = os.environ.get("KIMI_CODE_OAUTH_MARGIN", "")
    try:
        return max(0, int(raw)) if raw else DEFAULT_MARGIN_SECONDS
    except ValueError:
        return DEFAULT_MARGIN_SECONDS


def _read_credentials(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("credential file is not a JSON object")
    return data


def _fresh_token(data: dict, margin: int) -> str | None:
    token = data.get("access_token")
    expires_at = data.get("expires_at")
    if not isinstance(token, str) or not token:
        return None
    if not isinstance(expires_at, (int, float)):
        return None
    if expires_at - time.time() <= margin:
        return None
    return token


class NoCredentialsError(Exception):
    """Credential file cannot produce a token (missing/unusable)."""


class RefreshFailedError(Exception):
    """The refresh grant against the auth host failed."""


def _refresh(data: dict) -> dict:
    refresh_token = data.get("refresh_token")
    if not isinstance(refresh_token, str) or not refresh_token:
        raise NoCredentialsError("no refresh_token in credential file — run `kimi login` again")
    host = os.environ.get("KIMI_CODE_OAUTH_HOST") or os.environ.get("KIMI_OAUTH_HOST") or DEFAULT_OAUTH_HOST
    client_id = os.environ.get("KIMI_CODE_OAUTH_CLIENT_ID") or DEFAULT_CLIENT_ID
    body = "&".join(
        [
            "grant_type=refresh_token",
            "refresh_token=" + urllib.parse.quote(refresh_token, safe=""),
            "client_id=" + urllib.parse.quote(client_id, safe=""),
        ]
    ).encode("utf-8")
    request = urllib.request.Request(
        host.rstrip("/") + "/api/oauth/token",
        data=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:200]
        raise RefreshFailedError(f"token refresh failed: HTTP {exc.code} ({detail})") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RefreshFailedError(f"token refresh failed: {exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("access_token"), str):
        raise RefreshFailedError("token refresh returned no access_token")

    merged = dict(data)
    merged["access_token"] = payload["access_token"]
    if isinstance(payload.get("refresh_token"), str) and payload["refresh_token"]:
        merged["refresh_token"] = payload["refresh_token"]
    if isinstance(payload.get("token_type"), str):
        merged["token_type"] = payload["token_type"]
    if isinstance(payload.get("scope"), str):
        merged["scope"] = payload["scope"]
    expires_in = payload.get("expires_in")
    if isinstance(expires_in, (int, float)) and expires_in > 0:
        merged["expires_in"] = int(expires_in)
        merged["expires_at"] = time.time() + float(expires_in)
    elif isinstance(payload.get("expires_at"), (int, float)):
        merged["expires_at"] = float(payload["expires_at"])
    else:
        # Server gave no lifetime; assume the kimi-code default so the next
        # margin check behaves sanely instead of treating it as immortal.
        merged["expires_at"] = time.time() + 900.0
    return merged


def _write_credentials(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    backup = path.with_suffix(path.suffix + ".bak")
    # Backup is best-effort; the atomic replace below is the real guard.
    # It holds the same tokens, so it gets the same owner-only permissions.
    with contextlib.suppress(OSError):
        backup.write_bytes(path.read_bytes())
        os.chmod(backup, 0o600)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
            handle.write("\n")
        os.chmod(tmp_name, 0o600)
        os.replace(tmp_name, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp_name)
        raise


def cmd_token() -> int:
    path = _credentials_path()
    margin = _margin_seconds()
    if not path.is_file():
        print(f"kimi-coding-oauth: credential file not found: {path} (run `kimi login`)", file=sys.stderr)
        return 2

    # Serialize refreshes across concurrent apiKeyHelper invocations. The lock
    # file is ours; the kimi CLI does not take it, so after acquiring we
    # re-read and re-check in case another process already refreshed.
    lock_path = path.with_suffix(path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        try:
            data = _read_credentials(path)
        except (OSError, ValueError) as exc:
            print(f"kimi-coding-oauth: cannot read credentials: {exc}", file=sys.stderr)
            return 2

        token = _fresh_token(data, margin)
        if token is not None:
            print(token)
            return 0

        try:
            merged = _refresh(data)
        except NoCredentialsError as exc:
            print(f"kimi-coding-oauth: {exc}", file=sys.stderr)
            return 2
        except RefreshFailedError as exc:
            print(f"kimi-coding-oauth: {exc}", file=sys.stderr)
            return 3
        try:
            _write_credentials(path, merged)
        except OSError as exc:
            print(f"kimi-coding-oauth: cannot write credentials: {exc}", file=sys.stderr)
            return 3

        token = _fresh_token(merged, 0)
        if token is None:
            print("kimi-coding-oauth: refreshed token is already expired", file=sys.stderr)
            return 3
        print(token)
        return 0


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[1] != "token":
        print(__doc__, file=sys.stderr)
        return 64
    return cmd_token()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
