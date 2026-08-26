"""Backward-compatible import path for subscription usage probes.

The implementation lives in :mod:`scripts.api.subscription_usage`. CodexBar CLI
subprocesses are retired; native HTTP/credential probes own the fetch path.
"""

from __future__ import annotations

from scripts.api import subscription_usage as _subscription_usage

# Re-export the full public surface (star import skips leading-underscore names).
from scripts.api.subscription_usage import (  # noqa: F401
    CURSOR_CACHE_KEY,
    DEFAULT_CODEXBAR_CACHE_TTL_S,
    DEFAULT_CODEXBAR_REFRESH_INTERVAL_S,
    DEFAULT_CODEXBAR_REFRESH_TIMEOUT_S,
    DEFAULT_CURSOR_CACHE_TTL_S,
    PACE_TOLERANCE_PCT,
    PROVIDER_TO_LANE,
    SUBSCRIPTION_LANES_WITHOUT_CURSOR,
    SUBSCRIPTION_PROVIDERS,
    WEEKLY_WINDOW_MINUTES,
    WEEKLY_WINDOW_TOLERANCE_MINUTES,
    compute_provider_trend,
    compute_weekly_pace_delta_pct,
    fetch_codexbar_usage,
    fetch_provider_usage,
    get_cursor_lane_usage,
    get_provider_usage_data,
    lane_is_under_weekly_pace,
    persist_provider_snapshot,
    refresh_provider_usage_data,
    scheduler_status,
    start_periodic_refresh,
    stop_periodic_refresh,
    trigger_background_refresh,
    trigger_cursor_background_refresh,
    trigger_api_account_background_refresh,
    API_ACCOUNT_PROVIDERS,
    DEFAULT_API_ACCOUNT_CACHE_TTL_S,
    get_api_account_data,
    get_api_accounts_snapshot,
    refresh_api_account_data,
)

# Tests and legacy callers import underscore-prefixed helpers from this module.
_normalize_provider_data = _subscription_usage._normalize_provider_data
_normalize_provider_error = _subscription_usage._normalize_provider_error
_codexbar_refresh_timeout_s = _subscription_usage._codexbar_refresh_timeout_s
_codexbar_cache_ttl_s = _subscription_usage._codexbar_cache_ttl_s
_codexbar_refresh_interval_s = _subscription_usage._codexbar_refresh_interval_s
_record_probe_result = _subscription_usage._record_probe_result
_record_cursor_probe_result = _subscription_usage._record_cursor_probe_result
_run_all_refreshes = _subscription_usage._run_all_refreshes
_refresh_in_flight = _subscription_usage._refresh_in_flight
_refresh_thread = _subscription_usage._refresh_thread
_scheduler_thread = _subscription_usage._scheduler_thread
_last_good_data = _subscription_usage._last_good_data
_last_failure_data = _subscription_usage._last_failure_data
_cursor_last_good = _subscription_usage._cursor_last_good
probe_cursor_login = _subscription_usage.probe_cursor_login
probe_cursor_provider_windows = _subscription_usage.probe_cursor_provider_windows
_http_json_request = _subscription_usage._http_json_request
_load_kimi_bearer = _subscription_usage._load_kimi_bearer
_load_codex_oauth_token = _subscription_usage._load_codex_oauth_token
_load_claude_oauth_token = _subscription_usage._load_claude_oauth_token
_scheduler_is_running = _subscription_usage._scheduler_is_running
_refresh_cursor_usage_live = _subscription_usage._refresh_cursor_usage_live
_load_deepseek_api_key = _subscription_usage._load_deepseek_api_key
_load_openrouter_api_key = _subscription_usage._load_openrouter_api_key
_api_account_last_good = _subscription_usage._api_account_last_good
