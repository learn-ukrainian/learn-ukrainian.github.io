"""CodexBar usage parser and normalization library for capacity checks.

Provides background-threaded asynchronous caching of provider dashboard metrics.
"""

from __future__ import annotations

import json
import os
import subprocess
import threading
import time
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from typing import Any

from scripts.api.state_helpers import cache_get_with_age, cache_set

WEEKLY_WINDOW_MINUTES = 10080
# Reject monthly/long windows when no exact weekly window exists (e.g. 43200 min).
WEEKLY_WINDOW_TOLERANCE_MINUTES = 5040
PACE_TOLERANCE_PCT = 10.0

# Live-measured 2026-08-04: `codexbar usage --json --provider claude` took
# ~17s end-to-end twice in a row (its own dashboard-fetch latency, not a
# hang) while codex returned in ~2s. The prior 2.0s refresh timeout
# guaranteed a false 'unavailable' classification for the claude lane on
# every fresh-refresh call — Monitor/routing then painted a healthy lane as
# capacity-unknown (routing-budget false-red). This floor covers the
# explicit in-process fresh-refresh path
# (state_router.compute_routing_budget(fresh_codexbar=True)) and the
# background scheduler. HTTP handlers never wait for this CLI.
DEFAULT_CODEXBAR_REFRESH_TIMEOUT_S = 25.0

# CodexBar snapshots are operator-facing capacity, not per-request truth.
# 12 minutes sits in the 10–15 min window: long enough that a ~17s Claude
# probe cannot saturate the API, short enough that dispatch still sees
# current allotment. Override with CODEXBAR_CACHE_TTL_S /
# CODEXBAR_REFRESH_INTERVAL_S.
DEFAULT_CODEXBAR_CACHE_TTL_S = 720.0
DEFAULT_CODEXBAR_REFRESH_INTERVAL_S = 720.0

SUBSCRIPTION_PROVIDERS: tuple[str, ...] = (
    "claude",
    "codex",
    "cursor",
    "gemini",
    "grok",
    "kimi",
)

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
_last_failure_data: dict[str, dict[str, Any]] = {}
_refresh_lock = threading.Lock()
_refresh_in_flight = threading.Lock()
_refresh_thread: threading.Thread | None = None
_scheduler_lock = threading.Lock()
_scheduler_stop = threading.Event()
_scheduler_thread: threading.Thread | None = None
_last_refresh_started_at: float | None = None
_last_refresh_finished_at: float | None = None


def _is_usable_capacity(data: dict[str, Any] | None) -> bool:
    """Return whether a probe supplied authoritative capacity, not merely JSON."""
    if not isinstance(data, dict) or data.get("status") != "healthy":
        return False
    weekly_used = data.get("weekly_used_pct")
    return isinstance(weekly_used, (int, float)) and not isinstance(weekly_used, bool)


def _failure_metadata(data: dict[str, Any]) -> dict[str, Any]:
    """Keep failed-probe details separate from usable capacity observations."""
    return {
        "failure_kind": data.get("error_kind") or "unavailable",
        "failure_code": data.get("error_code"),
        "failure_message": data.get("auth_error") or "CodexBar usage data unavailable",
        "last_failure_at": data.get("fetched_at") or datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }


def _record_probe_result(provider: str, data: dict[str, Any] | None) -> bool:
    """Persist only usable capacity; retain failures as diagnostic metadata.

    A CodexBar error is an observation about the failed probe, not a capacity
    value.  In particular, it must never replace a valid last-known-good
    sample, otherwise a single timeout turns a usable lane into unavailable.
    """
    if not _is_usable_capacity(data):
        if isinstance(data, dict):
            _last_failure_data[provider] = _failure_metadata(data)
        return False

    assert data is not None  # narrowed by _is_usable_capacity
    snapshot = dict(data)
    cache_set(f"codexbar_usage:{provider}", snapshot)
    _last_good_data[provider] = (time.monotonic(), snapshot)
    return True


def _with_observation_metadata(
    data: dict[str, Any],
    *,
    freshness: str,
    age_s: float | None,
    provider: str,
) -> dict[str, Any]:
    """Add a stable freshness/failure contract without changing capacity data."""
    result = dict(data)
    failure = _last_failure_data.get(provider) or {}
    result.update(
        {
            "freshness": freshness,
            "stale": freshness == "stale_last_good",
            "age_s": age_s,
            "failure_kind": failure.get("failure_kind"),
            "last_failure_at": failure.get("last_failure_at"),
            "last_failure_code": failure.get("failure_code"),
        }
    )
    return result


def _env_positive_float(name: str, default: float) -> float:
    """Read a positive float env override, else ``default``."""
    raw = os.environ.get(name)
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    if value <= 0:
        return default
    return value


def _codexbar_refresh_timeout_s() -> float:
    """Per-provider CLI timeout floor for a blocking CodexBar refresh.

    Override via CODEXBAR_REFRESH_TIMEOUT_S (e.g. a slower box, or CI).
    Read fresh on every call so tests can monkeypatch the env var per-case.
    """
    return _env_positive_float("CODEXBAR_REFRESH_TIMEOUT_S", DEFAULT_CODEXBAR_REFRESH_TIMEOUT_S)


def _codexbar_cache_ttl_s() -> float:
    """How long a successful snapshot is labelled fresh."""
    return _env_positive_float("CODEXBAR_CACHE_TTL_S", DEFAULT_CODEXBAR_CACHE_TTL_S)


def _codexbar_refresh_interval_s() -> float:
    """Background scheduler period. Defaults to the same 12-minute TTL."""
    return _env_positive_float(
        "CODEXBAR_REFRESH_INTERVAL_S", DEFAULT_CODEXBAR_REFRESH_INTERVAL_S
    )


def _periodic_refresh_enabled() -> bool:
    """Start the daemon unless tests or an explicit env override disable it.

    TestClient lifespan must not spawn six CodexBar CLIs on every API test.
    ``CODEXBAR_PERIODIC_REFRESH=1`` forces it on (scheduler unit tests).
    ``CODEXBAR_PERIODIC_REFRESH=0`` forces it off.
    """
    raw = os.environ.get("CODEXBAR_PERIODIC_REFRESH")
    if raw is not None:
        return raw.strip().lower() not in {"0", "false", "off", "no"}
    return os.environ.get("PYTEST_CURRENT_TEST") is None


def _on_demand_refresh_enabled() -> bool:
    """Whether a cache miss may start a one-shot background CLI fan-out."""
    raw = os.environ.get("CODEXBAR_ON_DEMAND_REFRESH")
    if raw is not None:
        return raw.strip().lower() not in {"0", "false", "off", "no"}
    return os.environ.get("PYTEST_CURRENT_TEST") is None


def refresh_provider_usage_data(
    providers: Iterable[str], *, timeout_s: float | None = None
) -> dict[str, dict[str, Any]]:
    """Synchronously refresh selected providers in parallel for an explicit caller.

    The regular API path intentionally remains cache-only and non-blocking. This
    helper is reserved for callers, such as the dispatch budget guard, which
    explicitly need a bounded fresh verdict before acting.

    timeout_s defaults to _codexbar_refresh_timeout_s() (CODEXBAR_REFRESH_TIMEOUT_S,
    25.0s) — a real CLI call, not a hang. Callers should only override this when
    they have their own measured reason to.
    """
    if timeout_s is None:
        timeout_s = _codexbar_refresh_timeout_s()
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
            except Exception as exc:
                data = _normalize_provider_error(
                    provider,
                    {
                        "message": f"CodexBar refresh failed: {exc}",
                        "kind": "fetch_error",
                        "code": "FETCH_ERROR",
                    },
                )
            if _record_probe_result(provider, data):
                # The explicit fresh caller may use only a confirmed capacity
                # sample. Failed probes remain available through
                # get_provider_usage_data() as diagnostic metadata.
                refreshed[provider] = _with_observation_metadata(
                    data,
                    freshness="fresh",
                    age_s=0.0,
                    provider=provider,
                )
    return refreshed


def fetch_codexbar_usage(
    provider: str, *, timeout_s: float | None = None
) -> dict[str, Any]:
    """Run codexbar CLI, parse and normalize provider-specific usage data.

    Returns a normalized dictionary. If the CLI fails, times out, is missing,
    or returns an error/malformed output, returns a normalized record with status='unavailable'
    and auth_error/error_kind set. Never raises exceptions.
    For provider 'gemini', it queries 'gemini' first, and falls back to 'antigravity' if the first fails.
    """
    if timeout_s is None:
        timeout_s = _codexbar_refresh_timeout_s()
    if provider == "gemini":
        data = _fetch_single_provider("gemini", timeout_s=timeout_s)
        if data.get("weekly_used_pct") is not None:
            return data
        fallback_data = _fetch_single_provider("antigravity", timeout_s=timeout_s)
        if fallback_data.get("weekly_used_pct") is not None:
            return fallback_data
        return data
    return _fetch_single_provider(provider, timeout_s=timeout_s)


def _fetch_single_provider(provider: str, timeout_s: float) -> dict[str, Any]:
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
            try:
                cmd = ["codexbar", "usage", "--json", "--provider", provider]
                res = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout_s,
                    check=False,
                )
            except FileNotFoundError:
                return _normalize_provider_error(
                    provider,
                    {"message": "CodexBar CLI binary not found", "kind": "missing_binary", "code": 127},
                )
            # The CLI exits NON-zero on provider/credential errors while still
            # printing the error JSON on stdout (live-verified 2026-07-17: kimi
            # expired credential → rc=1 + error payload). Bail only when there
            # is no parseable payload at all.
            if res.returncode != 0 and not _stdout_has_provider_payload(res.stdout):
                if res.returncode == 127:
                    return _normalize_provider_error(
                        provider,
                        {"message": "CodexBar CLI binary not found", "kind": "missing_binary", "code": 127},
                    )
                return _normalize_provider_error(
                    provider,
                    {
                        "message": (res.stderr.strip() or f"CodexBar CLI exited with non-zero code {res.returncode}"),
                        "kind": "non_zero_exit",
                        "code": res.returncode,
                    },
                )

        try:
            parsed = json.loads(res.stdout)
        except Exception as exc:
            return _normalize_provider_error(
                provider,
                {"message": f"CodexBar CLI stdout is malformed JSON: {exc}", "kind": "malformed_json", "code": "MALFORMED_JSON"},
            )

        if not isinstance(parsed, list) or not parsed:
            return _normalize_provider_error(
                provider,
                {"message": "CodexBar CLI JSON payload is unparseable or empty schema", "kind": "unparseable_schema", "code": "UNPARSEABLE_SCHEMA"},
            )

        first_entry = parsed[0]
        if not isinstance(first_entry, dict):
            return _normalize_provider_error(
                provider,
                {"message": "CodexBar CLI JSON payload entry is unparseable schema", "kind": "unparseable_schema", "code": "UNPARSEABLE_SCHEMA"},
            )

        if "error" in first_entry:
            # Provider/credential error (e.g. expired Kimi credentials)
            return _normalize_provider_error(provider, first_entry["error"])
        return _normalize_provider_data(provider, first_entry)
    except subprocess.TimeoutExpired:
        return _normalize_provider_error(
            provider,
            {"message": f"CodexBar CLI timed out after {timeout_s}s", "kind": "timeout", "code": "TIMEOUT"},
        )
    except Exception as exc:
        return _normalize_provider_error(
            provider,
            {"message": f"CodexBar CLI fetch error: {exc}", "kind": "fetch_error", "code": "FETCH_ERROR"},
        )


def compute_weekly_pace_delta_pct(
    used_pct: float,
    resets_at: str,
    *,
    window_minutes: int | None = None,
    now: datetime | None = None,
) -> float | None:
    """Reuse the weekly pace formula from CodexBar normalization (r2 #7139)."""
    try:
        dt_str = resets_at.replace("Z", "+00:00")
        resets_at_dt = datetime.fromisoformat(dt_str)
        resets_at_dt = resets_at_dt.replace(tzinfo=UTC) if resets_at_dt.tzinfo is None else resets_at_dt.astimezone(UTC)
    except (TypeError, ValueError):
        return None
    current_time = (now or datetime.now(UTC)).astimezone(UTC)
    win_mins = WEEKLY_WINDOW_MINUTES if window_minutes is None else int(window_minutes)
    if win_mins <= 0:
        return None
    window_duration_seconds = win_mins * 60
    window_start_dt = resets_at_dt - timedelta(seconds=window_duration_seconds)
    elapsed_seconds = (current_time - window_start_dt).total_seconds()
    if window_duration_seconds <= 0:
        return None
    elapsed_fraction = elapsed_seconds / window_duration_seconds
    elapsed_fraction = max(0.0, min(1.0, elapsed_fraction))
    expected_pct = elapsed_fraction * 100.0
    return float(used_pct) - expected_pct


def lane_is_under_weekly_pace(
    used_pct: float,
    resets_at: str,
    *,
    window_minutes: int | None = None,
    now: datetime | None = None,
    tolerance_pct: float = PACE_TOLERANCE_PCT,
) -> bool:
    delta = compute_weekly_pace_delta_pct(
        used_pct,
        resets_at,
        window_minutes=window_minutes,
        now=now,
    )
    return delta is not None and delta < -tolerance_pct


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
        "status": "unavailable",
        "auth_error": message,
        "error_kind": kind or "unavailable",
        "error_code": code,
    }


def trigger_background_refresh() -> None:
    """Start one bounded parallel refresh without making an API request wait."""
    global _refresh_thread
    with _refresh_lock:
        if _refresh_thread is not None and _refresh_thread.is_alive():
            return
        _refresh_thread = threading.Thread(
            target=_run_all_refreshes,
            name="codexbar-refresh",
            daemon=True,
        )
        _refresh_thread.start()


def _run_all_refreshes() -> None:
    """Refresh every subscription lane. Overlapping callers no-op."""
    global _last_refresh_started_at, _last_refresh_finished_at
    if not _refresh_in_flight.acquire(blocking=False):
        return
    _last_refresh_started_at = time.monotonic()
    try:
        # Bounded probes are parallel. Failed probes cannot poison LKG data.
        # Runs off the HTTP request path — it shares the same realistic timeout
        # floor as the explicit fresh-refresh path (see _codexbar_refresh_timeout_s)
        # rather than the prior 2.0s, which never let the claude lane's ~17s CLI
        # probe complete.
        refresh_provider_usage_data(SUBSCRIPTION_PROVIDERS)
    finally:
        _last_refresh_finished_at = time.monotonic()
        _refresh_in_flight.release()


def _scheduler_is_running() -> bool:
    thread = _scheduler_thread
    return thread is not None and thread.is_alive()


def _periodic_loop(interval_s: float, run_immediately: bool) -> None:
    if run_immediately:
        _run_all_refreshes()
    while not _scheduler_stop.wait(timeout=interval_s):
        _run_all_refreshes()


def start_periodic_refresh(*, run_immediately: bool = True) -> None:
    """Keep CodexBar snapshots warm on a 12-minute timer.

    Idempotent. No-ops when disabled (pytest, or CODEXBAR_PERIODIC_REFRESH=0).
    """
    global _scheduler_thread
    if not _periodic_refresh_enabled():
        return
    with _scheduler_lock:
        if _scheduler_thread is not None and _scheduler_thread.is_alive():
            return
        _scheduler_stop.clear()
        interval_s = _codexbar_refresh_interval_s()
        _scheduler_thread = threading.Thread(
            target=_periodic_loop,
            args=(interval_s, run_immediately),
            name="codexbar-scheduler",
            daemon=True,
        )
        _scheduler_thread.start()


def stop_periodic_refresh(*, join_timeout_s: float = 1.0) -> None:
    """Stop the background scheduler. Safe to call when it was never started."""
    global _scheduler_thread
    _scheduler_stop.set()
    with _scheduler_lock:
        thread = _scheduler_thread
        _scheduler_thread = None
    if thread is not None and thread.is_alive():
        thread.join(timeout=join_timeout_s)


def scheduler_status() -> dict[str, Any]:
    """Process-local snapshot for /api/health. Never calls the CLI."""
    now = time.monotonic()
    started = _last_refresh_started_at
    finished = _last_refresh_finished_at
    return {
        "scheduler_running": _scheduler_is_running(),
        "refresh_in_flight": _refresh_in_flight.locked(),
        "cache_ttl_s": _codexbar_cache_ttl_s(),
        "refresh_interval_s": _codexbar_refresh_interval_s(),
        "last_refresh_age_s": None if finished is None else round(now - finished, 3),
        "last_refresh_started_age_s": None if started is None else round(now - started, 3),
        "providers": list(SUBSCRIPTION_PROVIDERS),
    }


def get_provider_usage_data(provider: str) -> dict[str, Any]:
    """Retrieve provider data from cache.

    HTTP and routing-budget always take this path. The CLI itself is owned by
    the periodic scheduler (API process) or by an explicit
    ``refresh_provider_usage_data`` caller. A cache miss here must not wait.

    When no scheduler is running (CLI in-process callers, tests), a cache miss
    still kicks a one-shot background refresh so the next read can see data.
    """
    cache_key = f"codexbar_usage:{provider}"
    cached = cache_get_with_age(cache_key, ttl=_codexbar_cache_ttl_s())

    if cached is not None:
        val, age = cached
        if _is_usable_capacity(val):
            return _with_observation_metadata(
                val,
                freshness="fresh",
                age_s=age,
                provider=provider,
            )

    # Cache miss or expired. The scheduler owns refresh when the API is up.
    # Under pytest, skip the on-demand CLI fan-out so later tests do not
    # inherit a 25s in-flight lock; tests that need the kick opt in via
    # CODEXBAR_ON_DEMAND_REFRESH=1 or call trigger_background_refresh().
    if not _scheduler_is_running() and _on_demand_refresh_enabled():
        trigger_background_refresh()

    # Serve last good data as stale fallback
    if provider in _last_good_data:
        t_mono, val = _last_good_data[provider]
        return _with_observation_metadata(
            val,
            freshness="stale_last_good",
            age_s=time.monotonic() - t_mono,
            provider=provider,
        )

    # Completely unavailable fallback
    lane = PROVIDER_TO_LANE.get(provider, provider)
    empty_win = {
        "used_pct": None,
        "remaining_pct": None,
        "resets_at": None,
        "window_minutes": None,
        "reset_description": None,
    }
    result = {
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
        "freshness": "unavailable",
        "stale": False,
        "age_s": None,
        "status": "unavailable",
        "auth_error": "CodexBar usage data unavailable",
        "error_kind": "unavailable",
        "error_code": None,
    }
    failure = _last_failure_data.get(provider)
    if failure:
        result.update(
            {
                "auth_error": failure["failure_message"],
                "error_kind": failure["failure_kind"],
                "error_code": failure["failure_code"],
                "failure_kind": failure["failure_kind"],
                "last_failure_at": failure["last_failure_at"],
                "last_failure_code": failure["failure_code"],
            }
        )
    else:
        result.update({"failure_kind": "unavailable", "last_failure_at": None, "last_failure_code": None})
    return result
