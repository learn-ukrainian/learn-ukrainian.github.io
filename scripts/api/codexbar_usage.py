"""CodexBar usage parser and normalization library for capacity checks.

Provides background-threaded asynchronous caching of provider dashboard metrics.
"""

from __future__ import annotations

import json
import subprocess
import threading
import time
from datetime import UTC, datetime, timedelta
from typing import Any, Optional

PROVIDER_TO_LANE = {
    "codex": "codex",
    "claude": "claude",
    "cursor": "cursor",
    "gemini": "gemini",
    "antigravity": "gemini",
    "grok": "grok",
}

# In-memory storage for the last successfully fetched usage data (lasts the lifetime of the process)
_last_good_data: dict[str, tuple[float, dict[str, Any]]] = {}
_refresh_lock = threading.Lock()
_refresh_thread: threading.Thread | None = None


def fetch_codexbar_usage(provider: str, *, timeout_s: float = 45.0) -> dict[str, Any] | None:
    """Run codexbar CLI, parse and normalize provider-specific usage data.

    Returns None on failure/timeout/parse error. Never raises exceptions.
    For provider 'gemini', it queries 'gemini' first, and falls back to 'antigravity' if the first fails.
    """
    if provider == "gemini":
        data = _fetch_single_provider("gemini", timeout_s=timeout_s)
        if data is not None:
            return data
        return _fetch_single_provider("antigravity", timeout_s=timeout_s)
    return _fetch_single_provider(provider, timeout_s=timeout_s)


def _fetch_single_provider(provider: str, timeout_s: float) -> dict[str, Any] | None:
    try:
        # Run codexbar usage --json --provider <provider>
        cmd = ["/opt/homebrew/bin/codexbar", "usage", "--json", "--provider", provider]
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
        if res.returncode != 0:
            # Fallback to codexbar in system path
            cmd = ["codexbar", "usage", "--json", "--provider", provider]
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_s,
                check=False,
            )
            if res.returncode != 0:
                return None

        parsed = json.loads(res.stdout)
        if not isinstance(parsed, list) or not parsed:
            return None

        first_entry = parsed[0]
        if "error" in first_entry:
            return None

        return _normalize_provider_data(provider, first_entry)
    except Exception:
        return None


def _normalize_provider_data(provider: str, data: dict[str, Any]) -> dict[str, Any]:
    lane = PROVIDER_TO_LANE.get(provider, provider)
    usage = data.get("usage") or {}
    openai_db = data.get("openaiDashboard") or {}

    # Extract limit windows
    limit_candidates: list[dict[str, Any]] = []
    for k in ["primary", "secondary", "tertiary"]:
        val = usage.get(k)
        if isinstance(val, dict):
            limit_candidates.append(val)
    for k in ["primaryLimit", "secondaryLimit"]:
        val = openai_db.get(k)
        if isinstance(val, dict):
            limit_candidates.append(val)

    primary_win = None
    weekly_win = None

    # Identify primary (<= 5h) and weekly (7d = 10080m) limits
    for cand in limit_candidates:
        win_mins = cand.get("windowMinutes")
        if win_mins is not None and win_mins <= 300:
            primary_win = cand
            break

    for cand in limit_candidates:
        win_mins = cand.get("windowMinutes")
        if win_mins is not None and win_mins == 10080:
            weekly_win = cand
            break

    # Fallback weekly if a monthly or longer limit is present
    if not weekly_win:
        for cand in limit_candidates:
            win_mins = cand.get("windowMinutes")
            if win_mins is not None and win_mins > 300:
                weekly_win = cand
                break

    # Absolute fallback
    if not primary_win:
        primary_win = usage.get("primary") or openai_db.get("primaryLimit")
    if not weekly_win:
        weekly_win = usage.get("secondary") or openai_db.get("secondaryLimit") or primary_win

    primary_used_pct = None
    if primary_win and "usedPercent" in primary_win:
        primary_used_pct = float(primary_win["usedPercent"])

    weekly_used_pct = None
    if weekly_win and "usedPercent" in weekly_win:
        weekly_used_pct = float(weekly_win["usedPercent"])

    weekly_resets_at = None
    if weekly_win:
        weekly_resets_at = weekly_win.get("resetsAt")
    if not weekly_resets_at and primary_win:
        weekly_resets_at = primary_win.get("resetsAt")

    monthly_cap_usd = None
    monthly_used_usd = None
    provider_cost = usage.get("providerCost")
    if isinstance(provider_cost, dict):
        if "limit" in provider_cost:
            monthly_cap_usd = float(provider_cost["limit"])
        if "used" in provider_cost:
            monthly_used_usd = float(provider_cost["used"])

    # Extract pace values if available
    pace = data.get("pace") or {}
    weekly_pace = pace.get("secondary") if isinstance(pace, dict) else None

    weekly_pace_delta_pct = None
    will_last_to_reset = None
    pace_summary = None

    if isinstance(weekly_pace, dict):
        weekly_pace_delta_pct = weekly_pace.get("deltaPercent")
        if weekly_pace_delta_pct is not None:
            weekly_pace_delta_pct = float(weekly_pace_delta_pct)
        will_last_to_reset = weekly_pace.get("willLastToReset")
        if will_last_to_reset is not None:
            will_last_to_reset = bool(will_last_to_reset)
        pace_summary = weekly_pace.get("summary")
    else:
        # Fallback manual calculation of pace
        if weekly_resets_at and weekly_used_pct is not None:
            try:
                dt_str = weekly_resets_at.replace("Z", "+00:00")
                resets_at_dt = datetime.fromisoformat(dt_str)
                current_time = datetime.now(UTC)

                win_mins = 10080
                if weekly_win and weekly_win.get("windowMinutes") is not None:
                    win_mins = int(weekly_win["windowMinutes"])

                window_duration_seconds = win_mins * 60
                window_start_dt = resets_at_dt - timedelta(seconds=window_duration_seconds)
                elapsed_seconds = (current_time - window_start_dt).total_seconds()

                if window_duration_seconds > 0:
                    elapsed_fraction = elapsed_seconds / window_duration_seconds
                    elapsed_fraction = max(0.0, min(1.0, elapsed_fraction))
                    expected_pct = elapsed_fraction * 100.0
                    weekly_pace_delta_pct = weekly_used_pct - expected_pct

                    margin = 10.0
                    is_in_deficit = weekly_used_pct > expected_pct + margin
                    will_last_to_reset = not is_in_deficit
                    pace_summary = f"{weekly_pace_delta_pct:.1f}% pace delta | Expected {expected_pct:.1f}% used"
            except Exception:
                pass

    return {
        "lane": lane,
        "primary_used_pct": primary_used_pct,
        "weekly_used_pct": weekly_used_pct,
        "monthly_cap_usd": monthly_cap_usd,
        "monthly_used_usd": monthly_used_usd,
        "weekly_resets_at": weekly_resets_at,
        "weekly_pace_delta_pct": weekly_pace_delta_pct,
        "will_last_to_reset": will_last_to_reset,
        "pace_summary": pace_summary,
        "source": "codexbar",
        "fetched_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }


def trigger_background_refresh() -> None:
    """Spawns a background thread to update the cache for all providers sequentially."""
    global _refresh_thread
    with _refresh_lock:
        if _refresh_thread is not None and _refresh_thread.is_alive():
            return
        _refresh_thread = threading.Thread(target=_run_all_refreshes, daemon=True)
        _refresh_thread.start()


def _run_all_refreshes() -> None:
    from scripts.api.state_helpers import cache_set

    # List of unique providers to refresh
    providers = ["claude", "codex", "cursor", "gemini", "grok"]
    for provider in providers:
        try:
            data = fetch_codexbar_usage(provider)
            if data is not None:
                cache_key = f"codexbar_usage:{provider}"
                cache_set(cache_key, data)
                _last_good_data[provider] = (time.monotonic(), data)
        except Exception:
            pass


def get_provider_usage_data(provider: str) -> dict[str, Any]:
    """Retrieve provider data from cache.

    Triggers a background refresh on cache miss/expiration.
    Returns a normalized record indicating stale/unknown state.
    """
    from scripts.api.state_helpers import cache_get_with_age

    cache_key = f"codexbar_usage:{provider}"
    cached = cache_get_with_age(cache_key, ttl=300.0)

    if cached is not None:
        val, age = cached
        if isinstance(val, dict):
            res = dict(val)
            res["stale"] = False
            res["age_s"] = age
            return res

    # Cache miss or expired: trigger update background thread
    trigger_background_refresh()

    # Serve last good data as stale fallback
    if provider in _last_good_data:
        t_mono, val = _last_good_data[provider]
        res = dict(val)
        res["stale"] = True
        res["age_s"] = time.monotonic() - t_mono
        return res

    # Completely unknown fallback
    lane = PROVIDER_TO_LANE.get(provider, provider)
    return {
        "lane": lane,
        "primary_used_pct": None,
        "weekly_used_pct": None,
        "monthly_cap_usd": None,
        "monthly_used_usd": None,
        "weekly_resets_at": None,
        "weekly_pace_delta_pct": None,
        "will_last_to_reset": None,
        "pace_summary": None,
        "source": "codexbar",
        "fetched_at": None,
        "stale": False,
        "age_s": None,
        "status": "unknown",
    }
