"""Shared Monitor API pin for hermetic hook and launcher tests (#9711)."""

from __future__ import annotations

# Nothing listens on port 1, so every Monitor call fails fast into the callers'
# fail-open path, exactly as on a CI runner that has no Monitor API.
UNREACHABLE_MONITOR_URL = "http://127.0.0.1:1"
# ``tool-timing.sh`` posts telemetry to its own endpoint variable, not the Monitor one.
UNREACHABLE_TOOL_TIMING_URL = f"{UNREACHABLE_MONITOR_URL}/api/telemetry/tool-timings"
