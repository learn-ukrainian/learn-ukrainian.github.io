#!/usr/bin/env python3
"""Print Claude weekly used percent from the Monitor routing-budget API.

Used by the Claude cap guard in launcher_core.sh. Prints a number (for
example 90) or "unknown" when the API is down, stale, or the field is
missing. LU_MONITOR_LOOPBACK selects the Monitor base URL; the default is
local Monitor telemetry. Proxies and redirects cannot replace that target.
Always exits 0 so the shell decides the policy.

The number is the meter of the Claude account this launch runs as (#10630):
the launch's ``CLAUDE_CONFIG_DIR``. No directory, or the host's default login
directory, is the default account, whose meter is the ``agents.claude`` lane
row. Another directory is the account the private account bindings
(``LU_CLAUDE_ACCOUNTS_FILE``, else the user's ``claude_accounts.json``) bind
to it, read from its ``claude_accounts`` row. A directory no binding names is
an account this reader cannot name, so its usage is unknown. The reader runs
isolated (``python -I``), so it reads the bindings itself rather than through
``scripts.fleet.claude_account_lane``.
"""

from __future__ import annotations

import json
import math
import os
import re
import stat
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

DEFAULT_ACCOUNT = "a"
_BINDINGS_MAX_BYTES = 65536


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("redirect refused")


def _monitor_target() -> str:
    """Use the configured Monitor URL without exposing it in diagnostics."""
    base = os.environ.get("LU_MONITOR_LOOPBACK", "http://127.0.0.1:8765").strip().rstrip("/")
    target = urlsplit(base)
    if (
        target.scheme not in {"http", "https"}
        or not target.hostname
        or target.username is not None
        or target.password is not None
        or target.query
        or target.fragment
    ):
        raise ValueError("invalid telemetry target")
    return base


def _bindings_file() -> Path | None:
    """``LU_CLAUDE_ACCOUNTS_FILE`` if set (empty means none), else the user's learn-ukrainian bindings file."""
    if "LU_CLAUDE_ACCOUNTS_FILE" in os.environ:
        value = os.environ["LU_CLAUDE_ACCOUNTS_FILE"]
        return Path(value) if value else None
    base = os.environ.get("XDG_CONFIG_HOME")
    if not base or not Path(base).is_absolute():
        base = str(Path.home() / ".config")
    return Path(base) / "learn-ukrainian" / "claude_accounts.json"


def _bound_labels() -> dict[str, str]:
    """``{label: config_dir}`` from the private bindings file; empty when it is absent, not private or invalid."""
    path = _bindings_file()
    if path is None:
        return {}
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError:
        return {}
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
            return {}
        raw = os.read(fd, _BINDINGS_MAX_BYTES + 1)
    except OSError:
        return {}
    finally:
        os.close(fd)
    if len(raw) > _BINDINGS_MAX_BYTES:
        return {}
    try:
        data = json.loads(raw)
    except ValueError:
        return {}
    accounts = data.get("accounts") if isinstance(data, dict) and data.get("schema_version") == 1 else None
    if not isinstance(accounts, dict):
        return {}
    return {
        label: entry["config_dir"]
        for label, entry in accounts.items()
        if isinstance(label, str)
        and re.fullmatch(r"[a-z]", label)
        and label != DEFAULT_ACCOUNT
        and isinstance(entry, dict)
        and isinstance(entry.get("config_dir"), str)
        and Path(entry["config_dir"]).is_absolute()
    }


def _same_directory(left: Path, right: Path) -> bool:
    try:
        return left.samefile(right)
    except OSError:
        return False


def launch_account() -> str | None:
    """The account label this launch runs as, or None when no binding names its login directory."""
    configured = os.environ.get("CLAUDE_CONFIG_DIR", "")
    if not configured:
        return DEFAULT_ACCOUNT
    directory = Path(configured).expanduser()
    if _same_directory(directory, Path.home() / ".claude"):
        return DEFAULT_ACCOUNT
    named = [label for label, bound in _bound_labels().items() if _same_directory(directory, Path(bound))]
    return named[0] if len(named) == 1 else None


def _weekly_used_pct(data: dict, account: str) -> object:
    """The weekly used-% the snapshot holds for ``account``; raises when that meter is stale or missing."""
    if account == DEFAULT_ACCOUNT:
        claude = data["agents"]["claude"]
        bar = claude.get("codexbar") or {}
        if claude.get("stale") or bar.get("stale"):
            raise ValueError("stale")
        return bar.get("weekly_used_pct")
    row = data["claude_accounts"][f"claude:{account}"]
    if row.get("status") != "ok" or row.get("stale") is not False:
        raise ValueError("stale")
    left = (row.get("weekly") or {}).get("left_pct")
    if isinstance(left, bool) or not isinstance(left, (int, float)) or not 0 <= left <= 100:
        raise ValueError("invalid percentage")
    return 100.0 - left


def main() -> None:
    try:
        account = launch_account()
        if account is None:
            raise ValueError("launch account unknown")
        base = _monitor_target()
        # Shell-controlled proxy settings and redirects cannot replace the target.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())
        with opener.open(base + "/api/state/routing-budget", timeout=4) as r:
            data = json.load(r)
        # Aggregate diagnostics include other providers' age. Check this
        # response's age separately from Claude's own telemetry freshness.
        generated_at = datetime.fromisoformat(data["generated_at"].replace("Z", "+00:00"))
        if generated_at.tzinfo is None:
            raise ValueError("missing timezone")
        response_age = (datetime.now(UTC) - generated_at).total_seconds()
        if not -60 <= response_age <= 900:
            raise ValueError("stale")
        pct = _weekly_used_pct(data, account)
        # Overshoot above 100% is real usage: clamp it so the cap fails closed.
        if isinstance(pct, bool) or not isinstance(pct, (int, float)) or not math.isfinite(pct) or pct < 0:
            raise ValueError("invalid percentage")
        # Fixed-point output: the launcher accepts only plain decimal digits.
        print(f"{min(pct, 100):.6f}".rstrip("0").rstrip("."))
    except Exception:  # any failure reads as unknown
        print("unknown")


if __name__ == "__main__":
    main()
