"""Light prepaid USD status helpers for fleet usage / capacity_pick.

Kept free of Monitor ``state_router`` and ``agent_identity`` so
``python -m scripts.fleet.usage show`` works on notebook checkouts that
only have a Monitor URL (no editable ``learn_ukrainian_v4_runtime``).
"""

from __future__ import annotations

import math
import os
from pathlib import Path
from typing import Any

DEFAULT_NEAR_CAP_USD = 5.0
DEFAULT_WARM_USD = 20.0
DEFAULT_API_ACCOUNT_CACHE_TTL_S = 600.0


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_prepaid_budgets(budget_config_path: Path | None = None) -> dict[str, Any]:
    path = budget_config_path or (_repo_root() / "scripts" / "config" / "agent_budgets.yaml")
    try:
        import yaml
    except ImportError:  # pragma: no cover
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except OSError:
        return {}
    return data if isinstance(data, dict) else {}


def api_account_cache_ttl_s() -> float:
    raw = os.environ.get("API_ACCOUNT_CACHE_TTL_S")
    if raw:
        try:
            value = float(raw)
            if math.isfinite(value) and value > 0:
                return value
        except ValueError:
            pass
    return DEFAULT_API_ACCOUNT_CACHE_TTL_S


def api_account_remaining_usd(lane: str, account: dict[str, Any]) -> float | None:
    """OpenRouter: min(key-cap, account balance). DeepSeek: USD total_balance only."""
    if lane == "openrouter":
        candidates: list[float] = []
        for key in ("limit_remaining_usd", "account_remaining_usd"):
            value = account.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
                candidates.append(float(value))
        return min(candidates) if candidates else None
    if lane == "deepseek" and str(account.get("currency") or "").upper() == "USD":
        total = account.get("total_balance")
        if isinstance(total, (int, float)) and not isinstance(total, bool) and math.isfinite(total):
            return float(total)
    return None


def api_lane_status_from_account(
    lane: str,
    account: dict[str, Any],
    budgets: dict[str, Any] | None = None,
) -> str:
    """Map a prepaid account probe to cool/warm/near_cap/unknown."""
    probe_state = str(account.get("probe_state") or "").upper()
    age = account.get("age_s")
    if (
        probe_state != "OK"
        or account.get("freshness") != "fresh"
        or not isinstance(age, (int, float))
        or isinstance(age, bool)
        or not math.isfinite(age)
        or not 0 <= age < api_account_cache_ttl_s()
    ):
        return "unknown"
    if lane == "deepseek" and account.get("is_available") is False:
        return "near_cap"
    remaining = api_account_remaining_usd(lane, account)
    if remaining is None:
        return "unknown"
    config = (budgets if budgets is not None else load_prepaid_budgets()).get(lane) or {}
    if remaining <= 0 or remaining < float(config.get("near_cap_usd", DEFAULT_NEAR_CAP_USD)):
        return "near_cap"
    if remaining < float(config.get("warm_usd", DEFAULT_WARM_USD)):
        return "warm"
    return "cool"
