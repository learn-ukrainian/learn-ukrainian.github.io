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
    kimi_coding_oauth.py refresh

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
from collections.abc import Iterable
from pathlib import Path

# Import secret_redactor (stdlib-only helper in parent scripts directory)
try:
    from secret_redactor import redact_text
except ImportError:
    _scripts_dir = str(Path(__file__).resolve().parent.parent)
    if _scripts_dir not in sys.path:
        sys.path.insert(0, _scripts_dir)
    from secret_redactor import redact_text

DEFAULT_OAUTH_HOST = "https://auth.kimi.com"
# Public client id of the Kimi Code CLI device-code flow (no secret).
DEFAULT_CLIENT_ID = "17e5f671-d194-4dfb-9706-5516cb48c098"
DEFAULT_MARGIN_SECONDS = 120
REQUEST_TIMEOUT_SECONDS = 15

_OUT_FILE_ENV = "KIMI_CODE_OAUTH_OUT_FILE"
_OUT_FILE_ENV_ALT = "KIMI_OAUTH_OUT_FILE"


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


_METADATA_KEYS = {
    "token_type",
    "scope",
    "expires_in",
    "expires_at",
    "client_id",
    "grant_type",
    "error",
    "error_description",
    "message",
    "detail",
    "status",
    "host",
    "url",
    "path",
    "filename",
}


def _held_secrets(*sources: dict | None) -> set[str]:
    """Collect known credential string values from dictionary sources and environment."""
    secrets: set[str] = set()
    for src in sources:
        if isinstance(src, dict):
            for k, v in src.items():
                if isinstance(v, str) and v:
                    if k in {"access_token", "refresh_token", "id_token", "client_secret", "secret", "api_key", "token", "password"}:
                        secrets.add(v)
                    elif k not in _METADATA_KEYS:
                        secrets.add(v)
    for env_var in ("KIMI_CODE_OAUTH_CLIENT_SECRET", "KIMI_OAUTH_CLIENT_SECRET"):
        val = os.environ.get(env_var)
        if val:
            secrets.add(val)
    return secrets


def redact_exact(text: str, secrets: Iterable[str]) -> str:
    """Redact known secret strings from text by exact substring match."""
    if not text:
        return text
    result = str(text)
    valid_secrets = sorted({s for s in secrets if isinstance(s, str) and s}, key=len, reverse=True)
    for sec in valid_secrets:
        result = result.replace(sec, "[REDACTED_SECRET]")
    return result


def redact_oauth_text(text: str, secrets: Iterable[str] = ()) -> str:
    """Redact text using exact-value match on held secrets, then redact_text shape matching."""
    if not text:
        return text
    cleaned = redact_exact(text, secrets)
    return redact_text(cleaned)


def _print_err(message: object, secrets: Iterable[str] = ()) -> None:
    """Print an error message to stderr after redacting any token shapes or held secrets."""
    redacted = redact_oauth_text(str(message), secrets)
    print(redacted, file=sys.stderr)


class NoCredentialsError(Exception):
    """Credential file cannot produce a token (missing/unusable)."""

    def __init__(self, message: object = "", secrets: Iterable[str] = ()) -> None:
        msg_str = str(message) if message is not None else ""
        redacted = redact_oauth_text(msg_str, secrets)
        super().__init__(redacted)


class RefreshFailedError(Exception):
    """The refresh grant against the auth host failed."""

    def __init__(self, message: object = "", secrets: Iterable[str] = ()) -> None:
        msg_str = str(message) if message is not None else ""
        redacted = redact_oauth_text(msg_str, secrets)
        super().__init__(redacted)


def _refresh(data: dict) -> dict:
    held = _held_secrets(data)
    refresh_token = data.get("refresh_token")
    if not isinstance(refresh_token, str) or not refresh_token:
        raise NoCredentialsError("no refresh_token in credential file — run `kimi login` again", secrets=held)
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
        raw_detail = exc.read().decode("utf-8", errors="replace")[:200]
        detail = redact_oauth_text(raw_detail, held) or ""
        raise RefreshFailedError(f"token refresh failed: HTTP {exc.code} ({detail})", secrets=held) from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        msg = redact_oauth_text(f"token refresh failed: {exc}", held)
        raise RefreshFailedError(msg, secrets=held) from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("access_token"), str):
        if isinstance(payload, dict):
            held.update(_held_secrets(payload))
        msg = redact_oauth_text("token refresh returned no access_token", held)
        raise RefreshFailedError(msg, secrets=held)

    held.update(_held_secrets(payload))

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


def force_refresh_token() -> str:
    """Refresh the stored OAuth credential even when its access token is fresh.

    This is intentionally separate from :func:`cmd_token`: consumers that only
    need a usable token should preserve the current token until its safety
    margin. A health canary, however, must prove the refresh-token grant and
    token rotation still work. The complete read → refresh → atomic write
    sequence stays under the same lock as ``cmd_token`` so a concurrent
    ``apiKeyHelper`` process cannot use or overwrite a stale refresh token.

    The returned token is for trusted in-process callers only. Callers that
    report health must never log or otherwise expose it.
    """
    path = _credentials_path()
    if not path.is_file():
        raise NoCredentialsError(f"credential file not found: {path}")

    lock_path = path.with_suffix(path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        try:
            data = _read_credentials(path)
        except (OSError, ValueError) as exc:
            raise NoCredentialsError(f"cannot read credentials: {exc}") from exc

        held = _held_secrets(data)
        merged = _refresh(data)
        held.update(_held_secrets(merged))
        _write_credentials(path, merged)
        token = _fresh_token(merged, 0)
        if token is None:
            raise RefreshFailedError("refreshed token is already expired", secrets=held)
        return token


def _write_token_to_file(out_path: Path, token: str) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, tmp_name = tempfile.mkstemp(dir=str(out_path.parent), prefix=out_path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(token.strip() + "\n")
        os.chmod(tmp_name, 0o600)
        os.replace(tmp_name, out_path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp_name)
        raise


def _emit_token(token: str) -> int:
    """Write the OAuth token safely.

    Refuses to print a live OAuth token to a terminal (TTY) under any
    circumstances. No opt-in flag is provided that prints to a screen.
    When stdout is a TTY, the token can be delivered to a secure file
    (mode 0600) if KIMI_CODE_OAUTH_OUT_FILE or KIMI_OAUTH_OUT_FILE is set.

    When stdout is not a TTY (piped or redirected), prints token to stdout.
    """
    out_file = os.environ.get(_OUT_FILE_ENV) or os.environ.get(_OUT_FILE_ENV_ALT)
    if out_file:
        out_path = Path(out_file).expanduser()
        try:
            _write_token_to_file(out_path, token)
            _print_err(f"kimi-coding-oauth: token written to {out_path} (mode 0600)")
            return 0
        except OSError as exc:
            _print_err(f"kimi-coding-oauth: cannot write token to {out_path}: {exc}")
            return 3

    if sys.stdout.isatty():
        _print_err(
            "kimi-coding-oauth: refusing to print a live OAuth token to a terminal.\n"
            "  It would persist in scrollback and shell history long after the token expires.\n"
            "  Pipe it (`... token | pbcopy`), redirect it (`... token > token.txt`), or set "
            f"{_OUT_FILE_ENV}=/path/to/file to deliver to a 0600 file."
        )
        return 3

    print(token)
    return 0


def cmd_token() -> int:
    path = _credentials_path()
    margin = _margin_seconds()
    if not path.is_file():
        _print_err(f"kimi-coding-oauth: credential file not found: {path} (run `kimi login`)")
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
            _print_err(f"kimi-coding-oauth: cannot read credentials: {exc}")
            return 2

        held = _held_secrets(data)
        token = _fresh_token(data, margin)
        if token is not None:
            return _emit_token(token)

        try:
            merged = _refresh(data)
            held.update(_held_secrets(merged))
        except NoCredentialsError as exc:
            _print_err(f"kimi-coding-oauth: {exc}", secrets=held)
            return 2
        except RefreshFailedError as exc:
            _print_err(f"kimi-coding-oauth: {exc}", secrets=held)
            return 3
        try:
            _write_credentials(path, merged)
        except OSError as exc:
            _print_err(f"kimi-coding-oauth: cannot write credentials: {exc}", secrets=held)
            return 3

        token = _fresh_token(merged, 0)
        if token is not None:
            return _emit_token(token)
        _print_err("kimi-coding-oauth: refreshed token is already expired", secrets=held)
        return 3


def cmd_refresh() -> int:
    """Force one refresh-token grant for diagnostics and trusted automation."""
    try:
        token = force_refresh_token()
    except NoCredentialsError as exc:
        _print_err(f"kimi-coding-oauth: {exc}")
        return 2
    except RefreshFailedError as exc:
        _print_err(f"kimi-coding-oauth: {exc}")
        return 3
    except OSError as exc:
        _print_err(f"kimi-coding-oauth: cannot write credentials: {exc}")
        return 3
    return _emit_token(token)


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[1] not in {"token", "refresh"}:
        _print_err(__doc__)
        return 64
    return cmd_token() if argv[1] == "token" else cmd_refresh()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

