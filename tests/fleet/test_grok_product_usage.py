"""Grok product percents on the normalized lane and in usage show. No network."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from scripts.api import state_router
from scripts.api import subscription_usage as probes
from scripts.fleet import usage

CREDIT = 37.5
_MISSING = object()
_TOKEN = "probe-token-not-printed"
_PRODUCTS = [
    {"product": "builder", "usage_percent": 12.5},
    {"product": "fast", "usage_percent": 40.0},
    {"product": "voice", "usage_percent": None},
    {"product": "image", "usage_percent": None},
]


def _probe(monkeypatch: pytest.MonkeyPatch, product_usage: object) -> dict[str, Any]:
    outcome = {
        "outcome": "data",
        "record": {
            "provider": "grok",
            "source": "grok_cli_proxy",
            "usage": {"secondary": {"windowMinutes": 10080, "usedPercent": CREDIT, "resetsAt": None}},
        },
    }
    if product_usage is not _MISSING:
        outcome["product_usage"] = product_usage
    monkeypatch.setattr(probes, "_private_usage", lambda: SimpleNamespace(probe_subscription=lambda *a, **kw: outcome))
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


def test_absent_private_products_add_no_key(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _probe(monkeypatch, _MISSING)
    assert "product_usage" not in record
    assert record["weekly_used_pct"] == CREDIT


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


def _budget_with_grok(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, record: dict[str, Any]) -> dict[str, Any]:
    """Real compute_routing_budget with only the Grok probe record injected; nothing touches the network."""
    budget_path = tmp_path / "agent_budgets.yaml"
    budget_path.write_text("codex:\n  weekly_cap_usd: 1000\n", encoding="utf-8")
    (tmp_path / "tasks").mkdir()
    (tmp_path / "api_usage").mkdir()
    monkeypatch.setattr(state_router, "load_cost_records", lambda **_kwargs: [])
    monkeypatch.setattr(
        state_router, "persist_provider_snapshot", lambda lane, snapshot: {"trend": "flat", "samples": 1}
    )
    monkeypatch.setattr(
        state_router,
        "get_provider_usage_data",
        lambda lane: record if lane == "grok" else {"lane": lane, "status": "unknown", "source": "codexbar"},
    )
    monkeypatch.setattr(state_router, "get_api_account_data", lambda _provider: {})
    monkeypatch.setattr(
        state_router, "get_cursor_lane_usage", lambda **_kwargs: {"lane": "cursor", "status": "unknown"}
    )
    monkeypatch.setattr(
        state_router,
        "summarize_fleet_burn",
        lambda agent, **_kwargs: {"source": "agent_runtime_jsonl", "agent": agent, "windows": {}},
    )
    return state_router.compute_routing_budget(
        datetime(2026, 10, 20, 12, 0, tzinfo=UTC),
        budget_config_path=budget_path,
        tasks_dir=tmp_path / "tasks",
        project_root=tmp_path,
        curriculum_root=tmp_path,
        batch_state_dir=tmp_path,
    )


def test_budget_grok_lane_keeps_product_lines_through_show(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    record = _probe(monkeypatch, _PRODUCTS)

    budget = _budget_with_grok(monkeypatch, tmp_path, record)
    grok = budget["agents"]["grok"]
    rendered = usage.format_human(budget)

    assert grok["product_usage"] == record["product_usage"]
    assert grok["codexbar"]["weekly_used_pct"] == CREDIT
    assert "  product builder: 12.5%" in rendered
    assert "  product fast: 40.0%" in rendered
    assert "  product voice: unknown" in rendered
    assert "  product image: unknown" in rendered
    assert _TOKEN not in rendered
