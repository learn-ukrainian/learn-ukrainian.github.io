"""Tests for /api/state/routing-budget."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from scripts.analytics.cost_report import CostRecord
from scripts.api import state_router


def _write_budget_config(tmp_path: Path) -> Path:
    path = tmp_path / "agent_budgets.yaml"
    path.write_text(
        """
claude:
  interactive:
    weekly_cap_usd: 460
    promo_through: "2026-07-13"
    promo_weekly_cap_usd: 690
  agentic_pool:
    monthly_cap_usd: 200
    starts_on: "2026-06-15"
codex:
  weekly_cap_usd: 1000
gemini:
  weekly_cap_usd: 500
""".lstrip(),
        encoding="utf-8",
    )
    return path


def _record(agent: str, cost_usd: float, mtime: datetime) -> CostRecord:
    return CostRecord(
        path=Path("fixture-meta.json"),
        level="a1",
        slug="fixture",
        phase="write",
        agent=agent,
        model="fixture-model",
        model_source="stored",
        ok=True,
        timestamp=mtime.isoformat(),
        mtime=mtime,
        prompt_chars=1,
        response_chars=1,
        prompt_tokens_est=1,
        response_tokens_est=1,
        prompt_tokens_source="stored",
        response_tokens_source="stored",
        rate_model="fixture-model",
        used_default_rate=False,
        cost_usd_est=cost_usd,
    )


def _configure(monkeypatch, tmp_path: Path, records: list[CostRecord]) -> None:
    monkeypatch.setattr(state_router, "BUDGET_CONFIG_PATH", _write_budget_config(tmp_path))
    monkeypatch.setattr(state_router, "load_cost_records", lambda: records)
    monkeypatch.setattr(
        state_router.delegate_api,
        "list_delegate_tasks",
        lambda **_kwargs: {"tasks": []},
    )


def test_endpoint_returns_documented_shape(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path, [])
    app = FastAPI()
    app.include_router(state_router.router, prefix="/api/state")

    response = TestClient(app).get("/api/state/routing-budget")

    assert response.status_code == 200
    data = response.json()
    assert {"agents", "in_flight", "recommendation", "diagnostics", "generated_at"} <= data.keys()


def test_status_cool_when_burn_under_50(monkeypatch, tmp_path):
    now = datetime(2026, 5, 13, 20, 30, tzinfo=UTC)
    _configure(monkeypatch, tmp_path, [_record("codex (gpt-5.5)", 100.0, now)])

    data = state_router.compute_routing_budget(now)

    assert data["agents"]["claude"]["burn_pct_7d"] == data["agents"]["claude"]["interactive"]["burn_pct_7d"]
    assert data["agents"]["codex"]["burn_pct_7d"] == 10.0
    assert data["agents"]["codex"]["status"] == "cool"


def test_status_hot_when_burn_75_90(monkeypatch, tmp_path):
    now = datetime(2026, 5, 13, 20, 30, tzinfo=UTC)
    _configure(monkeypatch, tmp_path, [_record("codex (gpt-5.5)", 800.0, now)])

    data = state_router.compute_routing_budget(now)

    assert data["agents"]["codex"]["burn_pct_7d"] == 80.0
    assert data["agents"]["codex"]["status"] == "hot"


def test_pre_launch_agentic_pool_before_2026_06_15(monkeypatch, tmp_path):
    now = datetime(2026, 5, 13, 20, 30, tzinfo=UTC)
    _configure(monkeypatch, tmp_path, [_record("claude (sonnet)", 100.0, now)])

    data = state_router.compute_routing_budget(now)

    pool = data["agents"]["claude"]["agentic_pool"]
    assert pool["status"] == "pre_launch"
    assert pool["active"] is False
    assert pool["spent_cycle_usd"] is None


def test_recommendation_picks_coolest_when_one_near_cap(monkeypatch, tmp_path):
    now = datetime(2026, 5, 13, 20, 30, tzinfo=UTC)
    _configure(
        monkeypatch,
        tmp_path,
        [
            _record("claude (sonnet)", 634.8, now),
            _record("codex (gpt-5.5)", 300.0, now),
            _record("gemini (pro)", 300.0, now),
        ],
    )

    data = state_router.compute_routing_budget(now)

    assert data["agents"]["claude"]["interactive"]["status"] == "near_cap"
    assert data["recommendation"]["primary_agent_for_code"] == "codex"


def test_recommendation_inline_when_all_hot(monkeypatch, tmp_path):
    now = datetime(2026, 5, 13, 20, 30, tzinfo=UTC)
    _configure(
        monkeypatch,
        tmp_path,
        [
            _record("claude (sonnet)", 586.5, now),
            _record("codex (gpt-5.5)", 850.0, now),
            _record("gemini (pro)", 425.0, now),
        ],
    )

    data = state_router.compute_routing_budget(now)

    assert data["recommendation"]["primary_agent_for_code"] == "inline_orchestrator"
    assert "all agents near cap" in data["recommendation"]["warnings"][-1]


def test_promo_through_uses_promo_cap_until_expiry(monkeypatch, tmp_path):
    before = datetime(2026, 7, 12, 20, 30, tzinfo=UTC)
    after = datetime(2026, 7, 14, 20, 30, tzinfo=UTC)
    _configure(monkeypatch, tmp_path, [_record("claude (sonnet)", 345.0, before)])

    before_data = state_router.compute_routing_budget(before)

    _configure(monkeypatch, tmp_path, [_record("claude (sonnet)", 345.0, after)])
    after_data = state_router.compute_routing_budget(after)

    assert before_data["agents"]["claude"]["interactive"]["weekly_cap_usd"] == 690.0
    assert before_data["agents"]["claude"]["interactive"]["burn_pct_7d"] == 50.0
    assert after_data["agents"]["claude"]["interactive"]["weekly_cap_usd"] == 460.0
    assert after_data["agents"]["claude"]["interactive"]["burn_pct_7d"] == 75.0
