"""Grok product percents on the lane record and in usage show. No network."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from scripts.api import state_router
from scripts.api import subscription_usage as probes
from scripts.fleet import usage
from tests.api.test_routing_budget_endpoint import _configure

CREDIT = 37.5
NOW = datetime(2026, 10, 16, 12, 0, tzinfo=UTC)
_MISSING = object()
_PRODUCTS = [
    {"product": "builder", "usagePercent": 12.5},
    {"product": "fast", "usagePercent": 0},
    {"product": "voice"},
    {"product": "image", "usagePercent": 101},
    {"product": "", "usagePercent": 4},
    {"product": None, "usagePercent": 4},
    {"usagePercent": 4},
    "image",
    None,
]
_EXPECTED_PRODUCTS = [
    {"product": "builder", "usage_percent": 12.5},
    {"product": "fast", "usage_percent": 0.0},
    {"product": "voice", "usage_percent": None},
    {"product": "image", "usage_percent": None},
]
_PRIVATE_TEXT = ("dropped-marker", "probe-allowed", "authorization", "bearer")


def _payload(product_usage: object) -> dict:
    config: dict = {"creditUsagePercent": CREDIT, "marker": "dropped-marker"}
    if product_usage is not _MISSING:
        config["productUsage"] = product_usage
    return {"config": config, "marker": "dropped-marker"}


def _probe(monkeypatch: pytest.MonkeyPatch, product_usage: object) -> dict:
    monkeypatch.setattr(probes, "_load_grok_bearer", lambda: "probe-allowed")

    def _request(*_args, **_kwargs):
        return 200, _payload(product_usage), None

    monkeypatch.setattr(probes, "_http_json_request", _request)
    return probes._probe_grok_native(timeout_s=1)


def _weekly(record: dict) -> dict[str, float | None]:
    secondary = record["windows"]["secondary"]
    return {
        "weekly_used_pct": record["weekly_used_pct"],
        "weekly_remaining_pct": record["weekly_remaining_pct"],
        "secondary_used_pct": record["secondary_used_pct"],
        "window_used_pct": secondary["used_pct"],
        "window_remaining_pct": secondary["remaining_pct"],
    }


def _served(monkeypatch: pytest.MonkeyPatch, tmp_path, record: dict) -> tuple[dict, dict]:
    _configure(monkeypatch, tmp_path, [])
    observed = dict(record)
    observed.update(freshness="fresh", age_s=0, stale=False)
    def _provider(provider: str):
        return observed if provider == "grok" else None

    monkeypatch.setattr(state_router, "get_provider_usage_data", _provider)
    monkeypatch.setattr(state_router, "get_freshest_lane_usage", lambda **_kwargs: None)
    budget = state_router.compute_routing_budget(NOW)
    return budget, budget["agents"]["grok"]


def _show(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], budget: dict) -> str:
    monkeypatch.setattr(usage, "read_budget", lambda **_kwargs: budget)
    assert usage.main(["show"]) == 0
    return capsys.readouterr().out


def _lane_section(text: str, lane: str) -> str:
    lines = text.splitlines()
    start = next(index for index, line in enumerate(lines) if line.startswith(f"{lane} |"))
    end = next(
        (index for index in range(start + 1, len(lines)) if lines[index] and not lines[index].startswith(" ")),
        len(lines),
    )
    return "\n".join(lines[start:end])


def _assert_public(value: object) -> None:
    blob = json.dumps(value).lower()
    for needle in _PRIVATE_TEXT:
        assert needle not in blob


def test_in_range_missing_and_out_of_range_products(monkeypatch, tmp_path, capsys) -> None:
    record = _probe(monkeypatch, _PRODUCTS)
    plain = _probe(monkeypatch, _MISSING)
    assert _weekly(record) == _weekly(plain)
    assert record["weekly_used_pct"] == CREDIT
    assert record["windows"]["secondary"]["used_pct"] == CREDIT
    assert record["product_usage"] == _EXPECTED_PRODUCTS
    for entry in record["product_usage"]:
        assert set(entry) == {"product", "usage_percent"}
        if entry["usage_percent"] is not None:
            assert isinstance(entry["usage_percent"], float)
    _assert_public(record)

    budget, info = _served(monkeypatch, tmp_path, record)
    assert info["product_usage"] == _EXPECTED_PRODUCTS
    assert info["codexbar"]["product_usage"] == _EXPECTED_PRODUCTS
    assert info["codexbar"]["weekly_used_pct"] == CREDIT
    assert info["burn_pct_7d"] == CREDIT
    assert info["remaining_pct"] == pytest.approx(100.0 - CREDIT)
    for lane, lane_info in budget["agents"].items():
        if lane == "grok":
            continue
        assert "product_usage" not in lane_info
    _assert_public(info)

    text = _show(monkeypatch, capsys, budget)
    grok = _lane_section(text, "grok")
    assert f"secondary (weekly): used={CREDIT:.1f}% rem={100.0 - CREDIT:.1f}% resets=unknown" in grok
    assert "  product builder: 12.5%" in grok
    assert "  product fast: 0.0%" in grok
    assert "  product voice: unknown" in grok
    assert "  product image: unknown" in grok
    assert grok.index("product builder") < grok.index("product fast") < grok.index("product voice")
    assert grok.index("product voice") < grok.index("product image")
    assert text.count("\n  product ") == 4
    assert "dropped-marker" not in text
    assert "probe-allowed" not in text


@pytest.mark.parametrize("product_usage", [_MISSING, None, {"product": "builder", "usagePercent": 1}, "builder", []])
def test_absent_or_empty_product_usage_keeps_credit(monkeypatch, tmp_path, capsys, product_usage) -> None:
    record = _probe(monkeypatch, product_usage)
    assert record["weekly_used_pct"] == CREDIT
    assert record["windows"]["secondary"]["used_pct"] == CREDIT
    assert record["weekly_remaining_pct"] == pytest.approx(100.0 - CREDIT)
    if product_usage == []:
        assert record["product_usage"] == []
    else:
        assert "product_usage" not in record
    _assert_public(record)

    budget, info = _served(monkeypatch, tmp_path, record)
    assert info["codexbar"]["weekly_used_pct"] == CREDIT
    assert info["burn_pct_7d"] == CREDIT
    assert info["remaining_pct"] == pytest.approx(100.0 - CREDIT)
    if product_usage == []:
        assert info["product_usage"] == []
    else:
        assert "product_usage" not in info
    text = _show(monkeypatch, capsys, budget)
    grok = _lane_section(text, "grok")
    assert f"secondary (weekly): used={CREDIT:.1f}%" in grok
    assert "\n  product " not in text
    assert "dropped-marker" not in text
