#!/usr/bin/env python3
"""Print Claude weekly used percent from the Monitor routing-budget API.

Used by the Claude cap guard in launcher_core.sh. Prints a number (for
example 90) or "unknown" when the API is down, stale, or the field is
missing. Always exits 0 so the shell decides the policy.
"""
from __future__ import annotations

import json
import os
import urllib.request
from datetime import UTC, datetime


def main() -> None:
    base = os.environ.get("LU_MONITOR_LOOPBACK", "http://127.0.0.1:8765").rstrip("/")
    try:
        with urllib.request.urlopen(base + "/api/state/routing-budget", timeout=4) as r:
            data = json.load(r)
        claude = data["agents"]["claude"]
        bar = claude.get("codexbar") or {}
        # Aggregate diagnostics include other providers' age. Check this
        # response's age separately from Claude's own telemetry freshness.
        generated_at = datetime.fromisoformat(data["generated_at"].replace("Z", "+00:00"))
        if generated_at.tzinfo is None:
            raise ValueError("missing timezone")
        response_age = (datetime.now(UTC) - generated_at).total_seconds()
        if not 0 <= response_age <= 900 or claude.get("stale") or bar.get("stale"):
            raise ValueError("stale")
        pct = bar.get("weekly_used_pct")
        if pct is None:
            raise ValueError("missing")
        print(f"{float(pct):g}")
    except Exception:  # any failure reads as unknown
        print("unknown")


if __name__ == "__main__":
    main()
