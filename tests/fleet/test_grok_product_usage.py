"""Grok product percents on the normalized lane and in usage show. No network."""

from __future__ import annotations

from typing import Any

import pytest

from scripts.api import subscription_usage as probes
from scripts.fleet import usage

CREDIT = 37.5
_MISSING = object()
_TOKEN = "probe-token-not-printed"
_PRODUCTS = [
    {"product": "builder", "usagePercent": 12.5},
    {"product": "fast", "usagePercent": 40},
    {"product": "voice"},
    {"product": "image", "usagePercent": 101},
]


def _payload(product_usage: object) -> dict[str, Any]:
    config: dict[str, Any] = {"creditUsagePercent": CREDIT}
    if product_usage is not _MISSING:
        config["productUsage"] = product_usage
    return {"config": config}


def _probe(monkeypatch: pytest.MonkeyPatch, product_usage: object) -> dict[str, Any]:
    monkeypatch.setattr(probes, "_load_grok_bearer", lambda: _TOKEN)

    def _request(*_args: Any, **_kwargs: Any) -> tuple[int, dict[str, Any], None]:
        return 200, _payload(product_usage), None

    monkeypatch.setattr(probes, "_http_json_request", _request)
    return probes._probe_grok_native(timeout_s=1)


def _credit_line(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "weekly_used_pct": record["weekly_used_pct"],
        "weekly_remaining_pct": record["weekly_remaining_pct"],
        "secondary": record["windows"]["secondary"],
    }


def test_products_keep_percent_and_unknown_for_missing_or_out_of_range(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _probe(monkeypatch, _PRODUCTS)

    assert record["product_usage"] == [
        {"product": "builder", "usage_percent": 12.5},
        {"product": "fast", "usage_percent": 40.0},
        {"product": "voice", "usage_percent": None},
        {"product": "image", "usage_percent": None},
    ]
    assert record["weekly_used_pct"] == CREDIT


def test_product_list_does_not_change_weekly_credit_line(monkeypatch: pytest.MonkeyPatch) -> None:
    baseline = _credit_line(_probe(monkeypatch, _MISSING))
    with_products = _credit_line(_probe(monkeypatch, _PRODUCTS))

    assert with_products == baseline


@pytest.mark.parametrize("raw", [_MISSING, None, "builder", {"product": "builder"}])
def test_absent_or_non_list_products_add_no_key(monkeypatch: pytest.MonkeyPatch, raw: object) -> None:
    record = _probe(monkeypatch, raw)

    assert "product_usage" not in record
    assert record["weekly_used_pct"] == CREDIT


def test_entries_without_a_product_name_are_dropped(monkeypatch: pytest.MonkeyPatch) -> None:
    raw = [
        {"product": "", "usagePercent": 4},
        {"usagePercent": 4},
        "image",
        None,
        {"product": "fast", "usagePercent": 3},
    ]

    record = _probe(monkeypatch, raw)

    assert record["product_usage"] == [{"product": "fast", "usage_percent": 3.0}]


def test_show_prints_one_line_per_product_and_no_token(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _probe(monkeypatch, _PRODUCTS)
    budget = {"source": "test", "agents": {"grok": record}, "api_accounts": {}}

    rendered = usage.format_human(budget)

    assert "  product builder: 12.5%" in rendered
    assert "  product fast: 40.0%" in rendered
    assert "  product voice: unknown" in rendered
    assert "  product image: unknown" in rendered
    assert _TOKEN not in rendered
    assert _TOKEN not in str(record)


def test_show_adds_no_product_lines_without_product_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _probe(monkeypatch, _MISSING)
    rendered = usage.format_human({"source": "test", "agents": {"grok": record}, "api_accounts": {}})

    assert "  product " not in rendered
