"""First-party subscription usage probes for routing-budget capacity checks.

Native HTTP/credential probes replace the retired CodexBar CLI subprocess path.
Provides background-threaded asynchronous caching of provider dashboard metrics.
"""

from __future__ import annotations

import json
import os
import platform
import threading
import contextlib
import urllib.error
import urllib.request
import time
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from scripts.api.state_helpers import cache_get_with_age, cache_set

try:
    from scripts.agent_runtime.adapters.cursor import (
        probe_cursor_login,
        probe_cursor_provider_windows,
    )
except ImportError:  # pragma: no cover
    from agent_runtime.adapters.cursor import (  # type: ignore
        probe_cursor_login,
        probe_cursor_provider_windows,
    )

WEEKLY_WINDOW_MINUTES = 10080
# Reject monthly/long windows when no exact weekly window exists (e.g. 43200 min).
WEEKLY_WINDOW_TOLERANCE_MINUTES = 5040
PACE_TOLERANCE_PCT = 10.0

try:
    from scripts.common.repo_root import main_checkout_root
except ImportError:  # pragma: no cover
    from common.repo_root import main_checkout_root

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

# Native Cursor login + dashboard probe can exceed routing.html's 5s timeout.
# Cache HTTP reads for 10 minutes; background refresh keeps snapshots warm.
DEFAULT_CURSOR_CACHE_TTL_S = 600.0
DEFAULT_API_ACCOUNT_CACHE_TTL_S = 600.0
CURSOR_CACHE_KEY = "cursor_lane_usage"
API_ACCOUNT_PROVIDERS: tuple[str, ...] = ("openrouter", "deepseek")

SUBSCRIPTION_PROVIDERS: tuple[str, ...] = (
    "claude",
    "codex",
    "cursor",
    "gemini",
    "glm",
    "grok",
    "kimi",
)

PROVIDER_TO_LANE = {
    "codex": "codex",
    "claude": "claude",
    "cursor": "cursor",
    "gemini": "gemini",
    "antigravity": "gemini",
    "agy": "gemini",
    "glm": "glm",
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
_cursor_last_good: tuple[float, dict[str, Any]] | None = None
_cursor_refresh_lock = threading.Lock()
_cursor_refresh_thread: threading.Thread | None = None
_api_account_last_good: dict[str, tuple[float, dict[str, Any]]] = {}
_api_account_refresh_lock = threading.Lock()
_api_account_refresh_thread: threading.Thread | None = None


def _is_usable_capacity(data: dict[str, Any] | None) -> bool:
    """Return whether a probe supplied authoritative capacity, not merely JSON."""
    if not isinstance(data, dict):
        return False
    if data.get("status") in {"unavailable", "unknown", "need_login"}:
        return False
    if data.get("probe_state") in {"NEED_PROBE", "NEED_LOGIN"}:
        return False
    if data.get("login_state") == "NEED_LOGIN":
        return False
    weekly_used = data.get("weekly_used_pct")
    if isinstance(weekly_used, (int, float)) and not isinstance(weekly_used, bool):
        return True
    provider_windows = data.get("provider_windows")
    if isinstance(provider_windows, dict):
        auto = provider_windows.get("auto")
        if isinstance(auto, dict) and isinstance(auto.get("used_pct"), (int, float)):
            return True
    primary_used = data.get("primary_used_pct")
    return isinstance(primary_used, (int, float)) and not isinstance(primary_used, bool)


def _failure_metadata(data: dict[str, Any]) -> dict[str, Any]:
    """Keep failed-probe details separate from usable capacity observations."""
    return {
        "failure_kind": data.get("error_kind") or "unavailable",
        "failure_code": data.get("error_code"),
        "failure_message": data.get("auth_error") or "Subscription usage data unavailable",
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


def _cursor_cache_ttl_s() -> float:
    """How long a successful Cursor native snapshot is labelled fresh."""
    return _env_positive_float("CURSOR_CACHE_TTL_S", DEFAULT_CURSOR_CACHE_TTL_S)


def _api_account_cache_ttl_s() -> float:
    """How long a prepaid API account snapshot is labelled fresh (5–10 min window)."""
    return _env_positive_float("API_ACCOUNT_CACHE_TTL_S", DEFAULT_API_ACCOUNT_CACHE_TTL_S)


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
            provider: executor.submit(fetch_provider_usage, provider, timeout_s=timeout_s)
            for provider in unique_providers
        }
        for provider, future in futures.items():
            try:
                data = future.result()
            except Exception as exc:
                data = _normalize_provider_error(
                    provider,
                    {
                        "message": f"Provider refresh failed: {exc}",
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


def _http_json_request(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    body: bytes | None = None,
    timeout_s: float = 10.0,
) -> tuple[int, Any, str | None]:
    """Perform a bounded HTTP request; return (status, parsed_json_or_none, error_text)."""
    req_headers = dict(headers or {})
    if body is not None and "Content-Type" not in req_headers:
        req_headers["Content-Type"] = "application/json"
    try:
        req = urllib.request.Request(url, data=body, headers=req_headers, method=method)
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            raw = resp.read(4 * 1024 * 1024 + 1)
            if len(raw) > 4 * 1024 * 1024:
                return resp.status, None, "response too large"
            if not raw:
                return resp.status, None, None
            return resp.status, json.loads(raw.decode("utf-8")), None
    except urllib.error.HTTPError as exc:
        err_body = ""
        try:
            err_body = exc.read(4096).decode("utf-8", errors="replace")
        except Exception:
            pass
        parsed = None
        if err_body:
            with contextlib.suppress(json.JSONDecodeError, ValueError):
                parsed = json.loads(err_body)
        return exc.code, parsed, err_body or exc.reason
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
        return 0, None, str(exc)


def _read_json_file(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _load_claude_oauth_token() -> str | None:
    for env_name in ("CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_AUTH_TOKEN"):
        raw = os.environ.get(env_name, "").strip()
        if raw.startswith("sk-ant-oat"):
            return raw
    cred_path = Path.home() / ".claude" / ".credentials.json"
    cred = _read_json_file(cred_path)
    if cred:
        oauth = cred.get("claudeAiOauth")
        if isinstance(oauth, dict):
            token = oauth.get("accessToken")
            if isinstance(token, str) and token.strip():
                return token.strip()
    if platform.system() == "Darwin":
        security = Path("/usr/bin/security")
        if security.is_file():
            try:
                import subprocess

                completed = subprocess.run(
                    [
                        str(security),
                        "find-generic-password",
                        "-s",
                        "Claude Code-credentials",
                        "-w",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                if completed.returncode == 0 and completed.stdout.strip():
                    payload = json.loads(completed.stdout)
                    oauth = payload.get("claudeAiOauth") if isinstance(payload, dict) else None
                    if isinstance(oauth, dict):
                        token = oauth.get("accessToken")
                        if isinstance(token, str) and token.strip():
                            return token.strip()
            except Exception:
                pass
    return None


def _load_codex_oauth_token() -> str | None:
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
    for candidate in (codex_home / "auth.json", Path.home() / ".config" / "codex" / "auth.json"):
        data = _read_json_file(candidate)
        if not data:
            continue
        for key in ("access_token", "accessToken", "token"):
            val = data.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
    return None


def _load_kimi_bearer() -> str | None:
    api_key = os.environ.get("KIMI_CODE_API_KEY", "").strip()
    if api_key:
        return api_key
    cred_path = Path(
        os.environ.get(
            "KIMI_CODE_CREDENTIALS_PATH",
            str(Path.home() / ".kimi-code" / "credentials" / "kimi-code.json"),
        )
    ).expanduser()
    data = _read_json_file(cred_path)
    if data:
        token = data.get("access_token")
        if isinstance(token, str) and token.strip():
            return token.strip()
    return None


def _load_grok_bearer() -> str | None:
    env = os.environ.get("GROK_OAUTH_TOKEN", "").strip()
    if env:
        return env
    grok_home = Path(os.environ.get("GROK_HOME", Path.home() / ".grok")).expanduser()
    data = _read_json_file(grok_home / "auth.json")
    if not data:
        return None
    for scope_key, entry in data.items():
        if not isinstance(entry, dict):
            continue
        key = entry.get("key")
        if isinstance(key, str) and key.strip():
            return key.strip()
    return None


def _load_antigravity_oauth() -> dict[str, Any] | None:
    for path in (
        Path.home() / ".gemini" / "antigravity-cli" / "antigravity-oauth-token",
        Path.home() / ".agy" / "credentials.json",
        Path.home() / ".config" / "agy" / "credentials.json",
    ):
        data = _read_json_file(path)
        if not data:
            continue
        token = data.get("token") if isinstance(data.get("token"), dict) else data
        if isinstance(token, dict) and isinstance(token.get("access_token"), str):
            return token
        if isinstance(data.get("access_token"), str):
            return data
    return None


def _load_glm_api_key() -> str | None:
    for env_name in ("ZAI_API_KEY", "ZHIPU_API_KEY", "GLM_API_KEY", "BIGMODEL_API_KEY"):
        val = os.environ.get(env_name, "").strip()
        if val:
            return val
    secret = Path.home() / ".secret" / "zai.key"
    try:
        if secret.is_file():
            line = secret.read_text(encoding="utf-8").strip().splitlines()[0].strip()
            if line:
                return line
    except OSError:
        pass
    for path in (
        Path.home() / ".coding-relay" / "glm-api-key",
        Path.home() / ".config" / "bigmodel" / "api_key",
        Path.home() / ".config" / "zhipu" / "api_key",
    ):
        try:
            if path.is_file():
                line = path.read_text(encoding="utf-8").strip().splitlines()[0].strip()
                if line:
                    return line
        except OSError:
            continue
    return None


def _load_first_line_secret(path: Path) -> str | None:
    try:
        if path.is_file():
            line = path.read_text(encoding="utf-8").strip().splitlines()[0].strip()
            if line:
                return line
    except OSError:
        pass
    return None


def _load_opencode_provider_key(provider: str) -> str | None:
    path = Path.home() / ".local" / "share" / "opencode" / "auth.json"
    data = _read_json_file(path)
    if not data:
        return None
    entry = data.get(provider)
    if isinstance(entry, dict):
        key = entry.get("key")
        if isinstance(key, str) and key.strip():
            return key.strip()
    return None


def _load_openrouter_api_key() -> str | None:
    env = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if env:
        return env
    key = _load_opencode_provider_key("openrouter")
    if key:
        return key
    return _load_first_line_secret(Path.home() / ".secret" / "openrouter.key")


def _load_deepseek_api_key() -> str | None:
    env = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if env:
        return env
    key = _load_opencode_provider_key("deepseek")
    if key:
        return key
    for path in (
        Path.home() / ".secret" / "deepseek.key",
        Path.home() / ".secret" / "deekseep.key",
    ):
        secret = _load_first_line_secret(path)
        if secret:
            return secret
    return None


def _as_optional_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            return float(stripped)
        except ValueError:
            return None
    return None


def _empty_openrouter_account(probe_state: str = "NEED_PROBE") -> dict[str, Any]:
    return {
        "kind": "prepaid_credits",
        "probe_state": probe_state,
        "usage_usd": None,
        "usage_daily_usd": None,
        "usage_weekly_usd": None,
        "usage_monthly_usd": None,
        "limit_usd": None,
        "limit_remaining_usd": None,
        "limit_reset": None,
        "is_free_tier": False,
        "account_remaining_usd": None,
        "fetched_at": None,
    }


def _empty_deepseek_account(probe_state: str = "NEED_PROBE") -> dict[str, Any]:
    return {
        "kind": "prepaid_credits",
        "probe_state": probe_state,
        "local_only": True,
        "is_available": None,
        "currency": None,
        "total_balance": None,
        "granted_balance": None,
        "topped_up_balance": None,
        "fetched_at": None,
    }


def _probe_openrouter_native(*, timeout_s: float) -> dict[str, Any]:
    fetched_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    api_key = _load_openrouter_api_key()
    if not api_key:
        return _empty_openrouter_account("NEED_PROBE")
    status, payload, err = _http_json_request(
        "GET",
        "https://openrouter.ai/api/v1/key",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        },
        timeout_s=timeout_s,
    )
    if status != 200 or not isinstance(payload, dict):
        result = _empty_openrouter_account("NEED_PROBE")
        result["fetched_at"] = fetched_at
        result["auth_error"] = err or f"OpenRouter key HTTP {status}"
        return result
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    if not isinstance(data, dict):
        result = _empty_openrouter_account("NEED_PROBE")
        result["fetched_at"] = fetched_at
        result["auth_error"] = "OpenRouter key response unparseable"
        return result
    result = {
        "kind": "prepaid_credits",
        "probe_state": "ok",
        "usage_usd": _as_optional_float(data.get("usage")),
        "usage_daily_usd": _as_optional_float(data.get("usage_daily")),
        "usage_weekly_usd": _as_optional_float(data.get("usage_weekly")),
        "usage_monthly_usd": _as_optional_float(data.get("usage_monthly")),
        "limit_usd": _as_optional_float(data.get("limit")),
        "limit_remaining_usd": _as_optional_float(data.get("limit_remaining")),
        "limit_reset": data.get("limit_reset"),
        "is_free_tier": bool(data.get("is_free_tier")),
        "account_remaining_usd": None,
        "fetched_at": fetched_at,
    }
    management_key = os.environ.get("OPENROUTER_MANAGEMENT_API_KEY", "").strip()
    if management_key:
        credits_status, credits_payload, _ = _http_json_request(
            "GET",
            "https://openrouter.ai/api/v1/credits",
            headers={
                "Authorization": f"Bearer {management_key}",
                "Accept": "application/json",
            },
            timeout_s=timeout_s,
        )
        if credits_status == 200 and isinstance(credits_payload, dict):
            credits_data = credits_payload.get("data")
            if not isinstance(credits_data, dict):
                credits_data = credits_payload
            if isinstance(credits_data, dict):
                total = _as_optional_float(credits_data.get("total_credits"))
                used = _as_optional_float(credits_data.get("total_usage"))
                if total is not None and used is not None:
                    result["account_remaining_usd"] = round(total - used, 4)
    return result


def _probe_deepseek_native(*, timeout_s: float) -> dict[str, Any]:
    fetched_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    api_key = _load_deepseek_api_key()
    if not api_key:
        return _empty_deepseek_account("NEED_PROBE")
    status, payload, err = _http_json_request(
        "GET",
        "https://api.deepseek.com/user/balance",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        },
        timeout_s=timeout_s,
    )
    if status != 200 or not isinstance(payload, dict):
        result = _empty_deepseek_account("NEED_PROBE")
        result["fetched_at"] = fetched_at
        result["auth_error"] = err or f"DeepSeek balance HTTP {status}"
        return result
    balance_infos = payload.get("balance_infos")
    rows = balance_infos if isinstance(balance_infos, list) else []
    usd_row = None
    fallback_row = None
    for row in rows:
        if not isinstance(row, dict):
            continue
        if fallback_row is None:
            fallback_row = row
        currency = str(row.get("currency") or "").upper()
        if currency == "USD":
            usd_row = row
            break
    chosen = usd_row or fallback_row
    result = {
        "kind": "prepaid_credits",
        "probe_state": "ok",
        "local_only": True,
        "is_available": bool(payload.get("is_available")),
        "currency": chosen.get("currency") if isinstance(chosen, dict) else None,
        "total_balance": _as_optional_float(chosen.get("total_balance")) if isinstance(chosen, dict) else None,
        "granted_balance": _as_optional_float(chosen.get("granted_balance")) if isinstance(chosen, dict) else None,
        "topped_up_balance": _as_optional_float(chosen.get("topped_up_balance")) if isinstance(chosen, dict) else None,
        "fetched_at": fetched_at,
    }
    return result


_API_ACCOUNT_PROBES = {
    "openrouter": _probe_openrouter_native,
    "deepseek": _probe_deepseek_native,
}


def _api_account_cache_key(provider: str) -> str:
    return f"api_account:{provider}"


def _api_account_is_cacheable(data: dict[str, Any] | None) -> bool:
    if not isinstance(data, dict):
        return False
    if data.get("fetched_at"):
        return True
    return data.get("probe_state") in {"NEED_PROBE", "ok"}


def _record_api_account_result(provider: str, data: dict[str, Any] | None) -> bool:
    if not _api_account_is_cacheable(data):
        return False
    assert data is not None
    snapshot = dict(data)
    cache_set(_api_account_cache_key(provider), snapshot)
    _api_account_last_good[provider] = (time.monotonic(), snapshot)
    return True


def _with_api_account_observation_metadata(
    data: dict[str, Any],
    *,
    freshness: str,
    age_s: float | None,
) -> dict[str, Any]:
    result = dict(data)
    result.update(
        {
            "freshness": freshness,
            "stale": freshness == "stale_last_good",
            "age_s": age_s,
        }
    )
    return result


def _probe_api_account_live(provider: str, *, timeout_s: float | None = None) -> dict[str, Any]:
    if timeout_s is None:
        timeout_s = _codexbar_refresh_timeout_s()
    probe = _API_ACCOUNT_PROBES.get(provider)
    if probe is None:
        empty = _empty_openrouter_account("NEED_PROBE") if provider == "openrouter" else _empty_deepseek_account("NEED_PROBE")
        empty["auth_error"] = f"No prepaid API probe for {provider}"
        return empty
    try:
        return probe(timeout_s=timeout_s)
    except Exception as exc:
        empty = _empty_openrouter_account("NEED_PROBE") if provider == "openrouter" else _empty_deepseek_account("NEED_PROBE")
        empty["fetched_at"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        empty["auth_error"] = f"API account probe failed: {exc}"
        return empty


def refresh_api_account_data(
    providers: Iterable[str], *, timeout_s: float | None = None
) -> dict[str, dict[str, Any]]:
    """Synchronously refresh prepaid API account snapshots for explicit callers."""
    if timeout_s is None:
        timeout_s = _codexbar_refresh_timeout_s()
    unique_providers = tuple(dict.fromkeys(providers))
    if not unique_providers:
        return {}
    refreshed: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=len(unique_providers)) as executor:
        futures = {
            provider: executor.submit(_probe_api_account_live, provider, timeout_s=timeout_s)
            for provider in unique_providers
        }
        for provider, future in futures.items():
            try:
                data = future.result()
            except Exception as exc:
                data = _probe_api_account_live(provider, timeout_s=timeout_s)
                data["auth_error"] = f"API account refresh failed: {exc}"
            if _record_api_account_result(provider, data):
                refreshed[provider] = _with_api_account_observation_metadata(
                    data,
                    freshness="fresh",
                    age_s=0.0,
                )
    return refreshed


def _refresh_api_accounts_live() -> None:
    for provider in API_ACCOUNT_PROVIDERS:
        data = _probe_api_account_live(provider)
        _record_api_account_result(provider, data)


def trigger_api_account_background_refresh() -> None:
    """Start one bounded prepaid API refresh without making an API request wait."""
    global _api_account_refresh_thread
    with _api_account_refresh_lock:
        if _api_account_refresh_thread is not None and _api_account_refresh_thread.is_alive():
            return
        _api_account_refresh_thread = threading.Thread(
            target=_refresh_api_accounts_live,
            name="api-account-refresh",
            daemon=True,
        )
        _api_account_refresh_thread.start()


def get_api_account_data(provider: str) -> dict[str, Any]:
    """Cache-only prepaid API account read; background refresh keeps snapshots warm."""
    cache_key = _api_account_cache_key(provider)
    cached = cache_get_with_age(cache_key, ttl=_api_account_cache_ttl_s())
    if cached is not None:
        val, age = cached
        if _api_account_is_cacheable(val):
            return _with_api_account_observation_metadata(
                val,
                freshness="fresh",
                age_s=age,
            )

    if not _scheduler_is_running() and _on_demand_refresh_enabled():
        trigger_api_account_background_refresh()

    if provider in _api_account_last_good:
        t_mono, val = _api_account_last_good[provider]
        return _with_api_account_observation_metadata(
            val,
            freshness="stale_last_good",
            age_s=time.monotonic() - t_mono,
        )

    if provider == "openrouter":
        return _with_api_account_observation_metadata(
            _empty_openrouter_account("NEED_PROBE"),
            freshness="unavailable",
            age_s=None,
        )
    return _with_api_account_observation_metadata(
        _empty_deepseek_account("NEED_PROBE"),
        freshness="unavailable",
        age_s=None,
    )


def get_api_accounts_snapshot() -> dict[str, dict[str, Any]]:
    """Return both prepaid API account objects (always present)."""
    return {provider: get_api_account_data(provider) for provider in API_ACCOUNT_PROVIDERS}


def _window_from_used_pct(used_pct: float, *, window_minutes: int, resets_at: str | None) -> dict[str, Any]:
    return {
        "windowMinutes": window_minutes,
        "usedPercent": used_pct,
        "resetsAt": resets_at,
    }


def _probe_claude_native(*, timeout_s: float) -> dict[str, Any]:
    token = _load_claude_oauth_token()
    if not token:
        return _normalize_provider_error(
            "claude",
            {"message": "Claude OAuth credentials unavailable", "kind": "need_login", "code": "NEED_LOGIN"},
        )
    status, payload, err = _http_json_request(
        "GET",
        "https://api.anthropic.com/api/oauth/usage",
        headers={
            "Authorization": f"Bearer {token}",
            "anthropic-beta": "oauth-2025-04-20",
            "anthropic-version": "2023-06-01",
        },
        timeout_s=timeout_s,
    )
    if status == 401 or status == 403:
        return _normalize_provider_error(
            "claude",
            {"message": "Claude OAuth token rejected", "kind": "provider", "code": status},
        )
    if status != 200 or not isinstance(payload, dict):
        return _normalize_provider_error(
            "claude",
            {"message": err or f"Claude usage HTTP {status}", "kind": "fetch_error", "code": status or "FETCH_ERROR"},
        )
    limits = payload.get("limits") if isinstance(payload.get("limits"), list) else []
    primary = None
    weekly = None
    for item in limits:
        if not isinstance(item, dict):
            continue
        window_type = str(item.get("type") or item.get("window_type") or "").lower()
        used = item.get("utilization") or item.get("used_percent") or item.get("usedPercent")
        if used is None and isinstance(item.get("used"), (int, float)):
            total = item.get("limit") or item.get("total")
            if isinstance(total, (int, float)) and total:
                used = float(item["used"]) / float(total) * 100.0
        if not isinstance(used, (int, float)):
            continue
        resets = item.get("resets_at") or item.get("resetsAt")
        if window_type in {"five_hour", "5h", "primary"} or item.get("window_minutes") == 300:
            primary = _window_from_used_pct(float(used), window_minutes=300, resets_at=resets)
        elif window_type in {"seven_day", "weekly", "secondary"} or item.get("window_minutes") == 10080:
            weekly = _window_from_used_pct(float(used), window_minutes=10080, resets_at=resets)
    # Anthropic OAuth shape also exposes five_hour / seven_day top-level keys.
    for key, win_mins in (("five_hour", 300), ("seven_day", 10080)):
        block = payload.get(key)
        if isinstance(block, dict) and block.get("utilization") is not None:
            target = primary if win_mins <= 300 else weekly
            if target is None:
                target = _window_from_used_pct(
                    float(block["utilization"]),
                    window_minutes=win_mins,
                    resets_at=block.get("resets_at") or block.get("resetsAt"),
                )
                if win_mins <= 300:
                    primary = target
                else:
                    weekly = target
    usage = {"primary": primary, "secondary": weekly}
    return _normalize_provider_data(
        "claude",
        {"provider": "claude", "source": "claude_oauth", "usage": usage},
    )


def _probe_codex_native(*, timeout_s: float) -> dict[str, Any]:
    token = _load_codex_oauth_token()
    if not token:
        return _normalize_provider_error(
            "codex",
            {"message": "Codex OAuth credentials unavailable", "kind": "need_login", "code": "NEED_LOGIN"},
        )
    status, payload, err = _http_json_request(
        "GET",
        "https://chatgpt.com/backend-api/wham/usage",
        headers={"Authorization": f"Bearer {token}"},
        timeout_s=timeout_s,
    )
    if status in {401, 403}:
        return _normalize_provider_error(
            "codex",
            {"message": "Codex OAuth token rejected", "kind": "provider", "code": status},
        )
    if status != 200 or not isinstance(payload, dict):
        return _normalize_provider_error(
            "codex",
            {"message": err or f"Codex usage HTTP {status}", "kind": "fetch_error", "code": status or "FETCH_ERROR"},
        )
    rate = payload.get("rate_limit") if isinstance(payload.get("rate_limit"), dict) else payload
    primary = rate.get("primary_window") if isinstance(rate, dict) else None
    secondary = rate.get("secondary_window") if isinstance(rate, dict) else None

    def _map_win(win: dict[str, Any] | None) -> dict[str, Any] | None:
        if not isinstance(win, dict):
            return None
        used = win.get("used_percent") or win.get("usedPercent")
        if used is None and isinstance(win.get("used"), (int, float)):
            limit = win.get("limit")
            if isinstance(limit, (int, float)) and limit:
                used = float(win["used"]) / float(limit) * 100.0
        if not isinstance(used, (int, float)):
            return None
        return _window_from_used_pct(
            float(used),
            window_minutes=int(win.get("window_minutes") or win.get("windowMinutes") or 300),
            resets_at=win.get("reset_at") or win.get("resetsAt"),
        )

    usage = {
        "primary": _map_win(primary) or _map_win(rate.get("primary") if isinstance(rate, dict) else None),
        "secondary": _map_win(secondary) or _map_win(rate.get("secondary") if isinstance(rate, dict) else None),
    }
    if usage["primary"] is None and usage["secondary"] is None:
        return _normalize_provider_error(
            "codex",
            {"message": "Codex usage payload missing rate windows", "kind": "unparseable_schema", "code": "UNPARSEABLE_SCHEMA"},
        )
    return _normalize_provider_data(
        "codex",
        {"provider": "codex", "source": "codex_oauth", "usage": usage, "openaiDashboard": {}},
    )


def _probe_kimi_native(*, timeout_s: float) -> dict[str, Any]:
    token = _load_kimi_bearer()
    if not token:
        return _normalize_provider_error(
            "kimi",
            {"message": "Kimi Code credentials unavailable", "kind": "need_login", "code": "NEED_LOGIN"},
        )
    status, payload, err = _http_json_request(
        "GET",
        "https://api.kimi.com/coding/v1/usages",
        headers={"Authorization": f"Bearer {token}"},
        timeout_s=timeout_s,
    )
    if status in {401, 403}:
        return _normalize_provider_error(
            "kimi",
            {"message": "Kimi credential rejected", "kind": "provider", "code": status},
        )
    if status != 200 or not isinstance(payload, dict):
        return _normalize_provider_error(
            "kimi",
            {"message": err or f"Kimi usage HTTP {status}", "kind": "fetch_error", "code": status or "FETCH_ERROR"},
        )
    usage_block = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}
    limits = payload.get("limits") if isinstance(payload.get("limits"), list) else []
    weekly_used = None
    weekly_reset = None
    if usage_block:
        used = usage_block.get("used")
        limit = usage_block.get("limit")
        if isinstance(used, (int, float)) and isinstance(limit, (int, float)) and limit:
            weekly_used = float(used) / float(limit) * 100.0
        weekly_reset = usage_block.get("resetTime") or usage_block.get("reset_time")
    primary = None
    for item in limits:
        if not isinstance(item, dict):
            continue
        detail = item.get("detail") if isinstance(item.get("detail"), dict) else {}
        used = detail.get("used")
        limit = detail.get("limit")
        if not isinstance(used, (int, float)) or not isinstance(limit, (int, float)) or not limit:
            continue
        primary = _window_from_used_pct(
            float(used) / float(limit) * 100.0,
            window_minutes=300,
            resets_at=detail.get("resetTime") or detail.get("reset_time"),
        )
        break
    secondary = (
        _window_from_used_pct(weekly_used, window_minutes=10080, resets_at=weekly_reset)
        if weekly_used is not None
        else None
    )
    return _normalize_provider_data(
        "kimi",
        {"provider": "kimi", "source": "kimi_code_api", "usage": {"primary": primary, "secondary": secondary}},
    )


def _probe_grok_native(*, timeout_s: float) -> dict[str, Any]:
    token = _load_grok_bearer()
    if not token:
        return _normalize_provider_error(
            "grok",
            {"message": "Grok OAuth credentials unavailable", "kind": "need_login", "code": "NEED_LOGIN"},
        )
    status, payload, err = _http_json_request(
        "GET",
        "https://cli-chat-proxy.grok.com/v1/billing?format=credits",
        headers={
            "Authorization": f"Bearer {token}",
            "x-xai-token-auth": "xai-grok-cli",
            "Accept": "application/json",
        },
        timeout_s=timeout_s,
    )
    if status in {401, 403}:
        return _normalize_provider_error(
            "grok",
            {"message": "Grok credential rejected", "kind": "provider", "code": status},
        )
    if status != 200 or not isinstance(payload, dict):
        return _normalize_provider_error(
            "grok",
            {"message": err or f"Grok billing HTTP {status}", "kind": "fetch_error", "code": status or "FETCH_ERROR"},
        )
    config = payload.get("config") if isinstance(payload.get("config"), dict) else {}
    used_pct = config.get("creditUsagePercent")
    if used_pct is None:
        on_demand_used = config.get("onDemandUsed")
        on_demand_cap = config.get("onDemandCap")
        if isinstance(on_demand_used, dict) and isinstance(on_demand_cap, dict):
            used_val = on_demand_used.get("val")
            cap_val = on_demand_cap.get("val")
            if isinstance(used_val, (int, float)) and isinstance(cap_val, (int, float)) and cap_val:
                used_pct = float(used_val) / float(cap_val) * 100.0
    resets_at = None
    current_period = config.get("currentPeriod")
    if isinstance(current_period, dict):
        resets_at = current_period.get("end")
    if not resets_at:
        resets_at = config.get("billingPeriodEnd")
    weekly = (
        _window_from_used_pct(float(used_pct), window_minutes=10080, resets_at=resets_at)
        if isinstance(used_pct, (int, float))
        else None
    )
    return _normalize_provider_data(
        "grok",
        {"provider": "grok", "source": "grok_cli_proxy", "usage": {"secondary": weekly}},
    )


def _probe_antigravity_native(*, timeout_s: float) -> dict[str, Any]:
    token_data = _load_antigravity_oauth()
    if not token_data or not isinstance(token_data.get("access_token"), str):
        return _normalize_provider_error(
            "gemini",
            {"message": "Antigravity OAuth credentials unavailable", "kind": "need_login", "code": "NEED_LOGIN"},
        )
    access_token = token_data["access_token"]
    _, assist_payload, _ = _http_json_request(
        "POST",
        "https://daily-cloudcode-pa.googleapis.com/v1internal:loadCodeAssist",
        headers={"Authorization": f"Bearer {access_token}"},
        body=json.dumps({"metadata": {"ideType": "ANTIGRAVITY"}}).encode("utf-8"),
        timeout_s=timeout_s,
    )
    project = ""
    if isinstance(assist_payload, dict):
        project = str(assist_payload.get("cloudaicompanionProject") or "")
    status, quota_payload, err = _http_json_request(
        "POST",
        "https://daily-cloudcode-pa.googleapis.com/v1internal:retrieveUserQuotaSummary",
        headers={"Authorization": f"Bearer {access_token}"},
        body=json.dumps({"project": project} if project else {}).encode("utf-8"),
        timeout_s=timeout_s,
    )
    if status in {401, 403}:
        return _normalize_provider_error(
            "gemini",
            {"message": "Antigravity OAuth token rejected", "kind": "provider", "code": status},
        )
    if status != 200 or not isinstance(quota_payload, dict):
        return _normalize_provider_error(
            "gemini",
            {
                "message": err or f"Antigravity quota HTTP {status}",
                "kind": "fetch_error",
                "code": status or "FETCH_ERROR",
            },
        )
    buckets = quota_payload.get("buckets") or quota_payload.get("quotaBuckets") or []
    pro_remaining = None
    flash_remaining = None
    pro_reset = None
    flash_reset = None
    if isinstance(buckets, list):
        for bucket in buckets:
            if not isinstance(bucket, dict):
                continue
            model_id = str(bucket.get("modelId") or bucket.get("model_id") or "").lower()
            remaining = bucket.get("remainingFraction") or bucket.get("remaining_fraction")
            if not isinstance(remaining, (int, float)):
                continue
            reset = bucket.get("resetTime") or bucket.get("reset_time")
            if "pro" in model_id and (pro_remaining is None or remaining < pro_remaining):
                pro_remaining = float(remaining)
                pro_reset = reset
            elif "flash" in model_id and (flash_remaining is None or remaining < flash_remaining):
                flash_remaining = float(remaining)
                flash_reset = reset
    def _used_from_remaining(rem: float | None) -> float | None:
        if rem is None:
            return None
        return max(0.0, min(100.0, 100.0 - rem * 100.0))

    primary = (
        _window_from_used_pct(_used_from_remaining(flash_remaining), window_minutes=300, resets_at=flash_reset)
        if flash_remaining is not None
        else None
    )
    secondary = (
        _window_from_used_pct(_used_from_remaining(pro_remaining), window_minutes=10080, resets_at=pro_reset)
        if pro_remaining is not None
        else None
    )
    return _normalize_provider_data(
        "gemini",
        {"provider": "gemini", "source": "antigravity_oauth", "usage": {"primary": primary, "secondary": secondary}},
    )


def _probe_glm_native(*, timeout_s: float) -> dict[str, Any]:
    api_key = _load_glm_api_key()
    if not api_key:
        return _normalize_provider_error(
            "glm",
            {"message": "GLM/Z.AI API key unavailable", "kind": "need_login", "code": "NEED_LOGIN"},
        )
    host = os.environ.get("Z_AI_API_HOST", "api.z.ai").strip() or "api.z.ai"
    if not host.startswith("http"):
        host = f"https://{host}"
    quota_url = os.environ.get("Z_AI_QUOTA_URL", f"{host.rstrip('/')}/api/monitor/usage/quota/limit")
    status, payload, err = _http_json_request(
        "GET",
        quota_url,
        headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
        timeout_s=timeout_s,
    )
    if status in {401, 403}:
        return _normalize_provider_error(
            "glm",
            {"message": "GLM API key rejected", "kind": "provider", "code": status},
        )
    if status != 200 or not isinstance(payload, dict):
        return _normalize_provider_error(
            "glm",
            {"message": err or f"GLM quota HTTP {status}", "kind": "fetch_error", "code": status or "FETCH_ERROR"},
        )
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    limits = data.get("limits") if isinstance(data.get("limits"), list) else []
    token_limits: list[tuple[int, dict[str, Any]]] = []
    for item in limits:
        if not isinstance(item, dict) or item.get("type") != "TOKENS_LIMIT":
            continue
        unit = str(item.get("unit") or item.get("timeUnit") or "").lower()
        number = item.get("number") or item.get("duration")
        minutes = 300
        if unit in {"minute", "minutes", "time_unit_minute"} and isinstance(number, (int, float)):
            minutes = int(number)
        elif unit in {"hour", "hours"} and isinstance(number, (int, float)):
            minutes = int(number) * 60
        elif unit in {"day", "days"} and isinstance(number, (int, float)):
            minutes = int(number) * 1440
        used = item.get("usedPercent") or item.get("used_percent")
        if used is None and isinstance(item.get("usage"), (int, float)) and isinstance(item.get("limit"), (int, float)):
            if item["limit"]:
                used = float(item["usage"]) / float(item["limit"]) * 100.0
        if not isinstance(used, (int, float)):
            continue
        resets = item.get("nextResetTime") or item.get("next_reset_time")
        if isinstance(resets, (int, float)) and resets > 10_000_000_000:
            resets = datetime.fromtimestamp(float(resets) / 1000.0, tz=UTC).isoformat().replace("+00:00", "Z")
        token_limits.append(
            (
                minutes,
                _window_from_used_pct(float(used), window_minutes=minutes, resets_at=resets if isinstance(resets, str) else None),
            )
        )
    token_limits.sort(key=lambda pair: pair[0])
    primary = token_limits[0][1] if token_limits else None
    secondary = token_limits[1][1] if len(token_limits) > 1 else None
    return _normalize_provider_data(
        "glm",
        {"provider": "glm", "source": "zai_quota_api", "usage": {"primary": primary, "secondary": secondary}},
    )


_NATIVE_PROBES = {
    "claude": _probe_claude_native,
    "codex": _probe_codex_native,
    "kimi": _probe_kimi_native,
    "grok": _probe_grok_native,
    "gemini": _probe_antigravity_native,
    "antigravity": _probe_antigravity_native,
    "glm": _probe_glm_native,
}


def fetch_provider_usage(provider: str, *, timeout_s: float | None = None) -> dict[str, Any]:
    """Probe a subscription lane via first-party HTTP/credential paths.

    Never shells out to CodexBar. On missing credentials returns NEED_LOGIN /
    NEED_PROBE shaped records, not fabricated 0% usage.
    """
    if timeout_s is None:
        timeout_s = _codexbar_refresh_timeout_s()
    if provider == "cursor":
        return get_cursor_lane_usage()
    probe = _NATIVE_PROBES.get(provider)
    if probe is None:
        return _normalize_provider_error(
            provider,
            {"message": f"No native probe for provider {provider}", "kind": "unavailable", "code": "NO_PROBE"},
        )
    try:
        return probe(timeout_s=timeout_s)
    except Exception as exc:
        return _normalize_provider_error(
            provider,
            {"message": f"Native probe failed: {exc}", "kind": "fetch_error", "code": "FETCH_ERROR"},
        )


def fetch_codexbar_usage(provider: str, *, timeout_s: float | None = None) -> dict[str, Any]:
    """Backward-compatible alias for :func:`fetch_provider_usage`."""
    return fetch_provider_usage(provider, timeout_s=timeout_s)


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
    cursor_provider_windows: dict[str, Any] | None = None
    if lane == "cursor":
        # Cursor Ultra: monthly Auto + API pools only. Do not mash Total into burn/status.
        auto_win = named_secondary
        api_win = named_tertiary
        primary_win = auto_win
        weekly_win = None
        cursor_window_labels = {"secondary": "Auto", "tertiary": "API"}
        auto_used = _used_pct(auto_win) if auto_win else _used_pct(named_secondary)
        api_used = _used_pct(api_win) if api_win else _used_pct(named_tertiary)
        resets_at = None
        if auto_win and auto_win.get("resetsAt"):
            resets_at = auto_win.get("resetsAt")
        elif api_win and api_win.get("resetsAt"):
            resets_at = api_win.get("resetsAt")
        elif named_primary and named_primary.get("resetsAt"):
            resets_at = named_primary.get("resetsAt")
        cursor_provider_windows = {
            "auto": {
                "window": "monthly",
                "label": "Auto",
                "used_pct": auto_used,
                "remaining_pct": _remaining_pct(auto_used),
                "resets_at": resets_at,
                "window_minutes": (auto_win or {}).get("windowMinutes"),
            },
            "api": {
                "window": "monthly",
                "label": "API",
                "used_pct": api_used,
                "remaining_pct": _remaining_pct(api_used),
                "resets_at": resets_at,
                "window_minutes": (api_win or {}).get("windowMinutes"),
            },
        }

    auto_win = named_secondary if lane == "cursor" else None
    api_win = named_tertiary if lane == "cursor" else None

    primary_used_pct = _used_pct(primary_win) if primary_win else _used_pct(named_primary)
    if primary_used_pct is None:
        primary_used_pct = _used_pct(named_primary)
    if lane == "cursor" and cursor_provider_windows:
        primary_used_pct = cursor_provider_windows["auto"]["used_pct"]
        secondary_used_pct = primary_used_pct
        tertiary_used_pct = cursor_provider_windows["api"]["used_pct"]
    else:
        secondary_used_pct = _used_pct(named_secondary)
        tertiary_used_pct = _used_pct(named_tertiary)

    weekly_used_pct = _used_pct(weekly_win) if weekly_win else _used_pct(named_secondary)
    if weekly_used_pct is None:
        weekly_used_pct = _used_pct(named_secondary)
    if lane == "cursor":
        weekly_used_pct = None
    elif secondary_used_pct is None and weekly_used_pct is not None:
        secondary_used_pct = weekly_used_pct

    weekly_resets_at = None
    if weekly_win:
        weekly_resets_at = weekly_win.get("resetsAt")
    if not weekly_resets_at and primary_win:
        weekly_resets_at = primary_win.get("resetsAt")
    if not weekly_resets_at and named_secondary:
        weekly_resets_at = named_secondary.get("resetsAt")
    if not weekly_resets_at and named_primary:
        weekly_resets_at = named_primary.get("resetsAt")
    if lane == "cursor" and cursor_provider_windows:
        auto_resets = cursor_provider_windows["auto"].get("resets_at")
        if auto_resets:
            weekly_resets_at = auto_resets

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
        pace_used = primary_used_pct if lane == "cursor" else weekly_used_pct
        if weekly_resets_at and pace_used is not None:
            try:
                dt_str = weekly_resets_at.replace("Z", "+00:00")
                resets_at_dt = datetime.fromisoformat(dt_str)
                current_time = datetime.now(UTC)

                win_mins = 10080
                if weekly_win and weekly_win.get("windowMinutes") is not None:
                    win_mins = int(weekly_win["windowMinutes"])
                elif lane == "cursor" and cursor_provider_windows:
                    auto_resets = cursor_provider_windows["auto"].get("resets_at")
                    if auto_resets:
                        weekly_resets_at = auto_resets
                    win_mins = cursor_provider_windows["auto"].get("window_minutes")
                    if win_mins is not None:
                        win_mins = int(win_mins)

                window_duration_seconds = win_mins * 60
                window_start_dt = resets_at_dt - timedelta(seconds=window_duration_seconds)
                elapsed_seconds = (current_time - window_start_dt).total_seconds()

                if window_duration_seconds > 0:
                    elapsed_fraction = elapsed_seconds / window_duration_seconds
                    elapsed_fraction = max(0.0, min(1.0, elapsed_fraction))
                    expected_pct = elapsed_fraction * 100.0
                    weekly_pace_delta_pct = pace_used - expected_pct

                    margin = 10.0
                    is_in_deficit = pace_used > expected_pct + margin
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
    result = {
        "lane": lane,
        "primary_used_pct": primary_used_pct,
        "primary_remaining_pct": _remaining_pct(primary_used_pct),
        "secondary_used_pct": secondary_used_pct,
        "secondary_remaining_pct": _remaining_pct(secondary_used_pct),
        "tertiary_used_pct": tertiary_used_pct,
        "tertiary_remaining_pct": _remaining_pct(tertiary_used_pct),
        # Back-compat weekly for Claude/Codex only; Cursor has monthly auto/api pools.
        "weekly_used_pct": weekly_used_pct,
        "weekly_remaining_pct": _remaining_pct(weekly_used_pct),
        "windows": {
            "primary": _window_block(
                named_primary or primary_win, primary_used_pct, label=labels.get("primary")
            ),
            "secondary": _window_block(
                named_secondary or (auto_win if lane == "cursor" else weekly_win),
                secondary_used_pct,
                label=labels.get("secondary"),
            ),
            "tertiary": _window_block(named_tertiary or api_win, tertiary_used_pct, label=labels.get("tertiary")),
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
        "source": data.get("source") or "native_probe",
        "fetched_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }
    if cursor_provider_windows is not None:
        result["provider_windows"] = cursor_provider_windows
    return result


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
        "source": "native_probe",
        "fetched_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "status": "unavailable",
        "auth_error": message,
        "error_kind": kind or "unavailable",
        "error_code": code,
    }
    if kind == "need_login":
        result["probe_state"] = "NEED_LOGIN"
        result["login_state"] = "NEED_LOGIN"
    return result


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
        refresh_provider_usage_data(SUBSCRIPTION_LANES_WITHOUT_CURSOR)
        _refresh_cursor_usage_live()
        _refresh_api_accounts_live()
    finally:
        _last_refresh_finished_at = time.monotonic()
        _refresh_in_flight.release()


SUBSCRIPTION_LANES_WITHOUT_CURSOR: tuple[str, ...] = tuple(
    p for p in SUBSCRIPTION_PROVIDERS if p != "cursor"
)


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


def _routing_budget_state_dir() -> Path:
    source_repo_root = Path(__file__).resolve().parents[2]
    repo_root = main_checkout_root(source_repo_root)
    path = repo_root / "batch_state" / "routing_budget"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _provider_lkg_path() -> Path:
    return _routing_budget_state_dir() / "provider_lkg.json"


def _read_provider_lkg() -> dict[str, Any]:
    path = _provider_lkg_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _write_provider_lkg(data: dict[str, Any]) -> None:
    path = _provider_lkg_path()
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def persist_provider_snapshot(lane: str, snapshot: dict[str, Any]) -> dict[str, Any]:
    """Append a sanitized provider snapshot to on-disk LKG (max 8 per lane)."""
    lkg = _read_provider_lkg()
    lane_key = str(lane)
    history = lkg.get(lane_key)
    if not isinstance(history, list):
        history = []
    provider_windows = snapshot.get("provider_windows") if isinstance(snapshot.get("provider_windows"), dict) else {}
    auto = provider_windows.get("auto") if isinstance(provider_windows.get("auto"), dict) else {}
    api = provider_windows.get("api") if isinstance(provider_windows.get("api"), dict) else {}
    entry = {
        "at": snapshot.get("fetched_at") or datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "source": snapshot.get("source"),
        "auto_used_pct": auto.get("used_pct", snapshot.get("primary_used_pct")),
        "api_used_pct": api.get("used_pct", snapshot.get("tertiary_used_pct")),
        "weekly_used_pct": snapshot.get("weekly_used_pct"),
    }
    history.append(entry)
    lkg[lane_key] = history[-8:]
    _write_provider_lkg(lkg)
    return compute_provider_trend(lane_key, history=lkg[lane_key])


def compute_provider_trend(lane: str, *, history: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Derive simple trend/deficit/headroom hints from the last two on-disk samples."""
    rows = history if history is not None else _read_provider_lkg().get(lane, [])
    if not isinstance(rows, list) or not rows:
        return {"trend": None, "delta_auto_pct": None, "samples": 0}
    if len(rows) == 1:
        auto = rows[-1].get("auto_used_pct")
        if isinstance(auto, (int, float)):
            headroom = max(0.0, 100.0 - float(auto))
            return {
                "trend": "flat",
                "delta_auto_pct": 0.0,
                "headroom_pct": headroom,
                "deficit": float(auto) >= 90.0,
                "samples": 1,
            }
        weekly = rows[-1].get("weekly_used_pct")
        if isinstance(weekly, (int, float)):
            headroom = max(0.0, 100.0 - float(weekly))
            return {
                "trend": "flat",
                "delta_auto_pct": 0.0,
                "headroom_pct": headroom,
                "deficit": float(weekly) >= 90.0,
                "samples": 1,
            }
        return {"trend": None, "delta_auto_pct": None, "samples": 1}
    prev, cur = rows[-2], rows[-1]
    prev_auto = prev.get("auto_used_pct") if isinstance(prev.get("auto_used_pct"), (int, float)) else prev.get("weekly_used_pct")
    cur_auto = cur.get("auto_used_pct") if isinstance(cur.get("auto_used_pct"), (int, float)) else cur.get("weekly_used_pct")
    if not isinstance(cur_auto, (int, float)):
        return {"trend": None, "delta_auto_pct": None, "samples": len(rows)}
    delta = float(cur_auto) - float(prev_auto or 0.0)
    trend = "up" if delta > 1.0 else "down" if delta < -1.0 else "flat"
    headroom = max(0.0, 100.0 - float(cur_auto))
    return {
        "trend": trend,
        "delta_auto_pct": round(delta, 2),
        "headroom_pct": headroom,
        "deficit": float(cur_auto) >= 90.0,
        "samples": len(rows),
    }


def _fetch_cursor_lane_usage_live(*, prefer_native: bool = True) -> dict[str, Any]:
    """Probe Cursor login + native Auto/API pools (blocking; background/scheduler only)."""
    login = probe_cursor_login()
    if not login.get("is_authenticated"):
        return {
            **login,
            "probe_state": "NEED_LOGIN",
            "provider_windows": {
                "auto": {"window": "monthly", "label": "Auto", "used_pct": None, "remaining_pct": None, "resets_at": None},
                "api": {"window": "monthly", "label": "API", "used_pct": None, "remaining_pct": None, "resets_at": None},
            },
        }

    native = probe_cursor_provider_windows()
    if prefer_native and native.get("probe_state") == "healthy":
        merged = dict(native)
    else:
        merged = dict(native)

    if native.get("probe_state") == "healthy" or _is_usable_capacity(merged):
        trend = persist_provider_snapshot("cursor", merged)
        merged["trend"] = trend
        auto_used = None
        if isinstance(merged.get("provider_windows"), dict):
            auto_block = merged["provider_windows"].get("auto")
            if isinstance(auto_block, dict):
                auto_used = auto_block.get("used_pct")
        if auto_used is None:
            auto_used = merged.get("primary_used_pct")
        if isinstance(auto_used, (int, float)):
            merged["headroom_pct"] = max(0.0, 100.0 - float(auto_used))
            merged["deficit"] = bool(trend.get("deficit"))
    return merged


def _cursor_probe_is_cacheable(data: dict[str, Any] | None) -> bool:
    """Any completed Cursor probe (including NEED_LOGIN) is worth caching."""
    if not isinstance(data, dict):
        return False
    if data.get("fetched_at"):
        return True
    return data.get("probe_state") in {"NEED_LOGIN", "NEED_PROBE", "healthy"}


def _record_cursor_probe_result(data: dict[str, Any] | None) -> bool:
    global _cursor_last_good
    if not _cursor_probe_is_cacheable(data):
        return False
    assert data is not None
    snapshot = dict(data)
    cache_set(CURSOR_CACHE_KEY, snapshot)
    _cursor_last_good = (time.monotonic(), snapshot)
    return True


def _with_cursor_observation_metadata(
    data: dict[str, Any],
    *,
    freshness: str,
    age_s: float | None,
) -> dict[str, Any]:
    result = dict(data)
    result.update(
        {
            "freshness": freshness,
            "stale": freshness == "stale_last_good",
            "age_s": age_s,
        }
    )
    return result


def _refresh_cursor_usage_live() -> dict[str, Any] | None:
    data = _fetch_cursor_lane_usage_live()
    if _record_cursor_probe_result(data):
        return _with_cursor_observation_metadata(data, freshness="fresh", age_s=0.0)
    return None


def trigger_cursor_background_refresh() -> None:
    """Start one bounded Cursor native refresh without making an API request wait."""
    global _cursor_refresh_thread
    with _cursor_refresh_lock:
        if _cursor_refresh_thread is not None and _cursor_refresh_thread.is_alive():
            return
        _cursor_refresh_thread = threading.Thread(
            target=_refresh_cursor_usage_live,
            name="cursor-usage-refresh",
            daemon=True,
        )
        _cursor_refresh_thread.start()


def get_cursor_lane_usage(*, prefer_native: bool = True) -> dict[str, Any]:
    """Cursor lane: cache-only HTTP path; native probe runs in background."""
    cached = cache_get_with_age(CURSOR_CACHE_KEY, ttl=_cursor_cache_ttl_s())
    if cached is not None:
        val, age = cached
        if _cursor_probe_is_cacheable(val):
            return _with_cursor_observation_metadata(
                val,
                freshness="fresh",
                age_s=age,
            )

    if not _scheduler_is_running() and _on_demand_refresh_enabled():
        trigger_cursor_background_refresh()

    if _cursor_last_good is not None:
        t_mono, val = _cursor_last_good
        return _with_cursor_observation_metadata(
            val,
            freshness="stale_last_good",
            age_s=time.monotonic() - t_mono,
        )

    return _with_cursor_observation_metadata(
        {
            "lane": "cursor",
            "login_state": "unknown",
            "probe_state": "NEED_PROBE",
            "status": "unknown",
            "provider_windows": {
                "auto": {"window": "monthly", "label": "Auto", "used_pct": None, "remaining_pct": None, "resets_at": None},
                "api": {"window": "monthly", "label": "API", "used_pct": None, "remaining_pct": None, "resets_at": None},
            },
            "fetched_at": None,
            "source": "cursor_native",
        },
        freshness="unavailable",
        age_s=None,
    )


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
        "source": "native_probe",
        "fetched_at": None,
        "freshness": "unavailable",
        "stale": False,
        "age_s": None,
        "status": "unavailable",
        "auth_error": "Subscription usage data unavailable",
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
