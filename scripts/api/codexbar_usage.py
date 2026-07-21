"""CodexBar usage parser and normalization library for capacity checks.

Provides background-threaded asynchronous caching of provider dashboard metrics.
"""

from __future__ import annotations

import json
import subprocess
import threading
import time
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from typing import Any, Optional

from scripts.api.state_helpers import cache_get_with_age, cache_set

WEEKLY_WINDOW_MINUTES = 10080
# Reject monthly/long windows when no exact weekly window exists (e.g. 43200 min).
WEEKLY_WINDOW_TOLERANCE_MINUTES = 5040

PROVIDER_TO_LANE = {
    "codex": "codex",
    "claude": "claude",
    "cursor": "cursor",
    "gemini": "gemini",
    "antigravity": "gemini",
    "grok": "grok",
    "kimi": "kimi",
}

# In-memory storage for the last successfully fetched usage data (lasts the lifetime of the process)
_last_good_data: dict[str, tuple[float, dict[str, Any]]] = {}
_refresh_lock = threading.Lock()
_refresh_thread: threading.Thread | None = None


def refresh_provider_usage_data(providers: Iterable[str], *, timeout_s: float = 2.0) -> dict[str, dict[str, Any]]:
    """Synchronously refresh selected providers in parallel for an explicit caller.

    The regular API path intentionally remains cache-only and non-blocking. This
    helper is reserved for callers, such as the dispatch budget guard, which
    explicitly need a bounded fresh verdict before acting.
    """
    unique_providers = tuple(dict.fromkeys(providers))
    if not unique_providers:
        return {}

    refreshed: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=len(unique_providers)) as executor:
        futures = {
            provider: executor.submit(fetch_codexbar_usage, provider, timeout_s=timeout_s)
            for provider in unique_providers
        }
        for provider, future in futures.items():
            try:
                data = future.result()
            except Exception:
                data = None
            if data is None:
                continue
            cache_set(f"codexbar_usage:{provider}", data)
            _last_good_data[provider] = (time.monotonic(), data)
            refreshed[provider] = data
    return refreshed


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
        try:
            cmd = ["/opt/homebrew/bin/codexbar", "usage", "--json", "--provider", provider]
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_s,
                check=False,
            )
        except FileNotFoundError:
            # Homebrew path absent (Intel mac /usr/local, CI, Linux) — the
            # PATH-fallback below must still get its chance (review-5386 F1:
            # letting this reach the outer handler bypassed the fallback).
            res = subprocess.CompletedProcess(cmd, returncode=127, stdout="", stderr="")
        if res.returncode != 0 and not _stdout_has_provider_payload(res.stdout):
            # Fallback to codexbar in system path
            cmd = ["codexbar", "usage", "--json", "--provider", provider]
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_s,
                check=False,
            )
            # The CLI exits NON-zero on provider/credential errors while still
            # printing the error JSON on stdout (live-verified 2026-07-17: kimi
            # expired credential → rc=1 + error payload). Bail only when there
            # is no parseable payload at all — otherwise fall through so the
            # error surfaces as status='unknown' instead of a silent None.
            if res.returncode != 0 and not _stdout_has_provider_payload(res.stdout):
                return None

        parsed = json.loads(res.stdout)
        if not isinstance(parsed, list) or not parsed:
            return None

        first_entry = parsed[0]
        if "error" in first_entry:
            # Provider/credential error (e.g. expired Kimi credentials): surface
            # as status='unknown' with the message carried, never as zero usage.
            return _normalize_provider_error(provider, first_entry["error"])
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
        if win_mins is not None and win_mins == WEEKLY_WINDOW_MINUTES:
            weekly_win = cand
            break

    # Nearest-to-weekly fallback; reject monthly/long windows far from 7d.
    if not weekly_win:
        best_dist: int | None = None
        for cand in limit_candidates:
            win_mins = cand.get("windowMinutes")
            if win_mins is None or win_mins <= 300:
                continue
            dist = abs(int(win_mins) - WEEKLY_WINDOW_MINUTES)
            if dist > WEEKLY_WINDOW_TOLERANCE_MINUTES:
                continue
            if best_dist is None or dist < best_dist:
                weekly_win = cand
                best_dist = dist

    # Absolute fallback (Claude/Codex-shaped providers).
    if not primary_win:
        primary_win = usage.get("primary") or openai_db.get("primaryLimit")
    if not weekly_win:
        weekly_win = usage.get("secondary") or openai_db.get("secondaryLimit") or primary_win

    def _used_pct(win: dict[str, Any] | None) -> float | None:
        if not win or "usedPercent" not in win:
            return None
        return float(win["usedPercent"])

    def _remaining_pct(used: float | None) -> float | None:
        if used is None:
            return None
        return max(0.0, min(100.0, 100.0 - used))

    # Named windows from the provider payload.
    # Cursor Pro+ CodexBar text labels (live-verified 2026-07-21):
    #   primary   = Total  (account-level scarcity → burn/status)
    #   secondary = Auto
    #   tertiary  = API / on-demand
    # All three share the billing-cycle window (~44640 min), not 5h+weekly.
    named_primary = usage.get("primary") if isinstance(usage.get("primary"), dict) else None
    named_secondary = usage.get("secondary") if isinstance(usage.get("secondary"), dict) else None
    named_tertiary = usage.get("tertiary") if isinstance(usage.get("tertiary"), dict) else None

    cursor_window_labels: dict[str, str] | None = None
    if lane == "cursor":
        # Burn/status must track Total, not Auto. The generic absolute fallback
        # wrongly promoted secondary→weekly and understated account pressure.
        primary_win = named_primary or primary_win
        weekly_win = named_primary or weekly_win
        cursor_window_labels = {"primary": "Total", "secondary": "Auto", "tertiary": "API"}

    primary_used_pct = _used_pct(primary_win) if primary_win else _used_pct(named_primary)
    if primary_used_pct is None:
        primary_used_pct = _used_pct(named_primary)

    weekly_used_pct = _used_pct(weekly_win) if weekly_win else _used_pct(named_secondary)
    if weekly_used_pct is None:
        weekly_used_pct = _used_pct(named_secondary)
    if lane == "cursor" and primary_used_pct is not None:
        # Prefer Total even when a leftover weekly_win still points elsewhere.
        weekly_used_pct = primary_used_pct

    secondary_used_pct = _used_pct(named_secondary)
    if secondary_used_pct is None and lane != "cursor" and weekly_used_pct is not None:
        secondary_used_pct = weekly_used_pct

    tertiary_used_pct = _used_pct(named_tertiary)

    weekly_resets_at = None
    if weekly_win:
        weekly_resets_at = weekly_win.get("resetsAt")
    if not weekly_resets_at and primary_win:
        weekly_resets_at = primary_win.get("resetsAt")
    if not weekly_resets_at and named_secondary:
        weekly_resets_at = named_secondary.get("resetsAt")
    if not weekly_resets_at and named_primary:
        weekly_resets_at = named_primary.get("resetsAt")
    if lane == "cursor" and named_primary and named_primary.get("resetsAt"):
        weekly_resets_at = named_primary.get("resetsAt")

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
                elif lane == "cursor" and named_primary and named_primary.get("windowMinutes") is not None:
                    win_mins = int(named_primary["windowMinutes"])

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

    def _window_block(
        win: dict[str, Any] | None,
        used: float | None,
        *,
        label: str | None = None,
    ) -> dict[str, Any]:
        block = {
            "used_pct": used,
            "remaining_pct": _remaining_pct(used),
            "resets_at": (win or {}).get("resetsAt") if isinstance(win, dict) else None,
            "window_minutes": (win or {}).get("windowMinutes") if isinstance(win, dict) else None,
            "reset_description": (win or {}).get("resetDescription") if isinstance(win, dict) else None,
        }
        if label is not None:
            block["label"] = label
        return block

    labels = cursor_window_labels or {}
    return {
        "lane": lane,
        "primary_used_pct": primary_used_pct,
        "primary_remaining_pct": _remaining_pct(primary_used_pct),
        "secondary_used_pct": secondary_used_pct,
        "secondary_remaining_pct": _remaining_pct(secondary_used_pct),
        "tertiary_used_pct": tertiary_used_pct,
        "tertiary_remaining_pct": _remaining_pct(tertiary_used_pct),
        # Back-compat: weekly ≈ secondary for Claude/Codex; Cursor weekly ≈ Total (primary).
        "weekly_used_pct": weekly_used_pct,
        "weekly_remaining_pct": _remaining_pct(weekly_used_pct),
        "windows": {
            "primary": _window_block(
                named_primary or primary_win, primary_used_pct, label=labels.get("primary")
            ),
            "secondary": _window_block(
                named_secondary or (None if lane == "cursor" else weekly_win),
                secondary_used_pct,
                label=labels.get("secondary"),
            ),
            "tertiary": _window_block(named_tertiary, tertiary_used_pct, label=labels.get("tertiary")),
        },
        "monthly_cap_usd": monthly_cap_usd,
        "monthly_used_usd": monthly_used_usd,
        "weekly_resets_at": weekly_resets_at,
        "weekly_pace_delta_pct": weekly_pace_delta_pct,
        "will_last_to_reset": will_last_to_reset,
        "pace_summary": pace_summary,
        # Same key shape as _normalize_provider_error so consumers can use
        # bracket access on either record (review-5386 F2).
        "status": "healthy",
        "auth_error": None,
        "error_kind": None,
        "error_code": None,
        "source": "codexbar",
        "fetched_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }


def _stdout_has_provider_payload(stdout: str) -> bool:
    """True when the CLI printed a parseable provider list despite rc != 0."""
    try:
        parsed = json.loads(stdout)
    except (TypeError, ValueError):
        return False
    return isinstance(parsed, list) and bool(parsed)


def _normalize_provider_error(provider: str, error: Any) -> dict[str, Any]:
    """Normalize a codexbar provider-level error object.

    The CLI can return an error instead of usage, e.g. expired Kimi credentials:
        [{"source":"auto","provider":"kimi","error":{"code":1,"message":"...","kind":"provider"}}]

    This MUST surface as status='unknown' with the message carried (auth_error),
    NEVER as 0% remaining and never as a silently absent row for a subscription lane.
    Mirrors _normalize_provider_data's shape so consumers see a uniform record.
    """
    lane = PROVIDER_TO_LANE.get(provider, provider)
    message: str | None = None
    code: Any = None
    kind: str | None = None
    if isinstance(error, dict):
        message = error.get("message")
        code = error.get("code")
        kind = error.get("kind")

    empty_win = {
        "used_pct": None,
        "remaining_pct": None,
        "resets_at": None,
        "window_minutes": None,
        "reset_description": None,
    }
    return {
        "lane": lane,
        "primary_used_pct": None,
        "primary_remaining_pct": None,
        "secondary_used_pct": None,
        "secondary_remaining_pct": None,
        "tertiary_used_pct": None,
        "tertiary_remaining_pct": None,
        "weekly_used_pct": None,
        "weekly_remaining_pct": None,
        "windows": {"primary": dict(empty_win), "secondary": dict(empty_win), "tertiary": dict(empty_win)},
        "monthly_cap_usd": None,
        "monthly_used_usd": None,
        "weekly_resets_at": None,
        "weekly_pace_delta_pct": None,
        "will_last_to_reset": None,
        "pace_summary": None,
        "source": "codexbar",
        "fetched_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "status": "unknown",
        "auth_error": message,
        "error_kind": kind,
        "error_code": code,
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
    # List of unique providers to refresh
    providers = ["claude", "codex", "cursor", "gemini", "grok", "kimi"]
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
    empty_win = {
        "used_pct": None,
        "remaining_pct": None,
        "resets_at": None,
        "window_minutes": None,
        "reset_description": None,
    }
    return {
        "lane": lane,
        "primary_used_pct": None,
        "primary_remaining_pct": None,
        "secondary_used_pct": None,
        "secondary_remaining_pct": None,
        "tertiary_used_pct": None,
        "tertiary_remaining_pct": None,
        "weekly_used_pct": None,
        "weekly_remaining_pct": None,
        "windows": {"primary": dict(empty_win), "secondary": dict(empty_win), "tertiary": dict(empty_win)},
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
        "auth_error": None,
    }
