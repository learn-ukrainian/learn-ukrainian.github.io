"""Strict token-cost helper for runtime telemetry."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml

BillingModel = Literal["per_token", "subscription", "unknown"]
Provenance = Literal["priced", "no_tokens", "no_price", "subscription"]

_PRICING_PATH = Path(__file__).resolve().parents[1] / "config" / "model_pricing.yaml"
_logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CostResult:
    cost_usd: float | None
    billing_model: BillingModel
    provenance: Provenance


def compute_cost(
    model: str | None,
    tokens: int | None,
    *,
    agent: str | None = None,
) -> CostResult:
    """Compute USD cost only when both tokens and a single-token price exist.

    Split input/output pricing cannot be applied to the runtime's current
    total-token-only record without guessing a blend, so those models resolve
    to ``no_price`` until a later PR records directional token counts.
    """
    try:
        table = _pricing_table()
        model_key = _normalize_key(model)
        model_entry = _lookup_model_entry(table, model_key)
        if model_entry:
            billing_model = str(model_entry.get("billing_model") or "")
            if billing_model == "subscription":
                return CostResult(None, "subscription", "subscription")
            if billing_model == "per_token":
                token_count = _nonnegative_int(tokens)
                if token_count is None:
                    return CostResult(None, "per_token", "no_tokens")
                price = _positive_float(model_entry.get("usd_per_1m_tokens"))
                if price is None:
                    return CostResult(None, "unknown", "no_price")
                return CostResult(
                    cost_usd=(token_count * price) / 1_000_000,
                    billing_model="per_token",
                    provenance="priced",
                )

        if _agent_is_subscription(table, agent):
            return CostResult(None, "subscription", "subscription")
        return CostResult(None, "unknown", "no_price")
    except Exception as exc:  # pragma: no cover - degraded mode only
        _logger.debug("failed to compute telemetry cost: %s: %s", type(exc).__name__, exc)
        return CostResult(None, "unknown", "no_price")


@lru_cache(maxsize=1)
def _pricing_table() -> dict[str, Any]:
    data = yaml.safe_load(_PRICING_PATH.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _normalize_key(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _lookup_model_entry(
    table: dict[str, Any],
    model: str | None,
) -> dict[str, Any] | None:
    if not model:
        return None
    models = table.get("models")
    if not isinstance(models, dict):
        return None
    raw = models.get(model)
    return raw if isinstance(raw, dict) else None


def _agent_is_subscription(table: dict[str, Any], agent: str | None) -> bool:
    if not agent:
        return False
    agents = table.get("subscription_agents")
    if not isinstance(agents, dict):
        return False
    raw = agents.get(str(agent).strip())
    return isinstance(raw, dict) and raw.get("billing_model") == "subscription"


def _positive_float(value: Any) -> float | None:
    try:
        price = float(value)
    except (TypeError, ValueError):
        return None
    return price if price > 0 else None


def _nonnegative_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        count = int(value)
    except (TypeError, ValueError):
        return None
    return count if count >= 0 else None


def _reset_pricing_cache_for_tests() -> None:
    _pricing_table.cache_clear()
