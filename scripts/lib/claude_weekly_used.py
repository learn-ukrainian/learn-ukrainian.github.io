#!/usr/bin/env python3
"""Print Claude weekly used percent from the Monitor routing-budget API.

Used by the Claude cap guard in launcher_core.sh. Prints a number (for
example 90) or "unknown" when the API is down, stale, or the field is
missing. LU_MONITOR_LOOPBACK selects the Monitor base URL; the default is
local Monitor telemetry. Proxies and redirects cannot replace that target.
Always exits 0 so the shell decides the policy.
"""
from __future__ import annotations

import json
import math
import os
import urllib.request
from datetime import UTC, datetime
from urllib.parse import urlsplit


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


def main() -> None:
    try:
        base = _monitor_target()
        # Shell-controlled proxy settings and redirects cannot replace the target.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())
        with opener.open(base + "/api/state/routing-budget", timeout=4) as r:
            data = json.load(r)
        claude = data["agents"]["claude"]
        bar = claude.get("codexbar") or {}
        # Aggregate diagnostics include other providers' age. Check this
        # response's age separately from Claude's own telemetry freshness.
        generated_at = datetime.fromisoformat(data["generated_at"].replace("Z", "+00:00"))
        if generated_at.tzinfo is None:
            raise ValueError("missing timezone")
        response_age = (datetime.now(UTC) - generated_at).total_seconds()
        if not -60 <= response_age <= 900 or claude.get("stale") or bar.get("stale"):
            raise ValueError("stale")
        pct = bar.get("weekly_used_pct")
        if isinstance(pct, bool) or not isinstance(pct, (int, float)) or not math.isfinite(pct) or not 0 <= pct <= 100:
            raise ValueError("invalid percentage")
        print(f"{pct:g}")
    except Exception:  # any failure reads as unknown
        print("unknown")


if __name__ == "__main__":
    main()
