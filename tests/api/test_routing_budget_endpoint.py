"""Tests for /api/state/routing-budget."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
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
kimi:
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
    # These tests assert deterministic ledger calculations. The main API
    # lifespan refreshes CodexBar in a background thread, so isolate that live
    # provider state here; overlay-specific tests replace this stub explicitly.
    monkeypatch.setattr(state_router, "get_provider_usage_data", lambda _provider: None)
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


def test_kimi_is_a_subscription_lane_and_accepts_codexbar_overlay(monkeypatch, tmp_path):
    now = datetime(2026, 7, 16, 20, 30, tzinfo=UTC)
    _configure(monkeypatch, tmp_path, [])

    def _kimi_codexbar(provider: str) -> dict:
        return {
            "lane": provider,
            "primary_used_pct": 0.0 if provider == "kimi" else None,
            "weekly_used_pct": 0.0 if provider == "kimi" else None,
            "monthly_cap_usd": None,
            "monthly_used_usd": None,
            "weekly_resets_at": "2026-07-23T20:17:58Z" if provider == "kimi" else None,
            "weekly_pace_delta_pct": None,
            "will_last_to_reset": True if provider == "kimi" else None,
            "pace_summary": "0% used" if provider == "kimi" else None,
            "source": "codexbar",
            "fetched_at": "2026-07-16T20:30:56Z",
            "stale": False,
            "age_s": 0.0,
        }

    monkeypatch.setattr(state_router, "get_provider_usage_data", _kimi_codexbar)
    data = state_router.compute_routing_budget(now)

    assert data["agents"]["kimi"]["status"] == "cool"
    assert data["agents"]["kimi"]["codexbar"]["weekly_used_pct"] == 0.0
    assert any(row["lane"] == "kimi" and row["type"] == "subscription" for row in data["ranked_by_headroom"])


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


def test_empty_snapshot_marks_unknown_and_suppresses_rec(monkeypatch, tmp_path):
    """AC: empty/absent snapshot → status unknown (not cool), primary=None, no confident rec."""
    now = datetime(2026, 5, 13, 20, 30, tzinfo=UTC)
    _configure(monkeypatch, tmp_path, [])  # empty records

    def _no_codexbar(provider: str) -> dict:
        return {
            "lane": provider,
            "primary_used_pct": None,
            "weekly_used_pct": None,
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
        }

    monkeypatch.setattr(state_router, "get_provider_usage_data", _no_codexbar)

    data = state_router.compute_routing_budget(now)

    assert data["diagnostics"]["records_loaded"] == 0
    assert data["recommendation"]["primary_agent_for_code"] is None
    assert "empty" in (data["recommendation"].get("rationale") or "").lower() or any(
        "empty" in w for w in data["recommendation"].get("warnings", [])
    )
    for lane in ("claude", "codex", "gemini"):
        st = data["agents"][lane].get("status") or data["agents"][lane].get("interactive", {}).get("status")
        assert st == "unknown", f"{lane} should be unknown on empty"
    # ranked includes subs + api unknown
    ranked = data.get("ranked_by_headroom", [])
    assert any(r["lane"] == "deepseek" and r["status"] == "unknown" and r["type"] == "api" for r in ranked)
    assert any(r["lane"] == "codex" and r["type"] == "subscription" for r in ranked)


def test_empty_ledger_uses_fresh_codexbar_for_deficit_verdict(monkeypatch, tmp_path):
    """A guard refresh must retain authoritative deficit data without ledger records."""
    now = datetime(2026, 7, 9, 16, 13, tzinfo=UTC)
    _configure(monkeypatch, tmp_path, [])
    refreshed = {
        "claude": {
            "lane": "claude",
            "primary_used_pct": 10.0,
            "weekly_used_pct": 74.0,
            "monthly_cap_usd": None,
            "monthly_used_usd": None,
            "weekly_resets_at": "2026-07-13T06:59:59Z",
            "weekly_pace_delta_pct": 27.0,
            "will_last_to_reset": False,
            "pace_summary": "27% in deficit",
            "source": "codexbar",
            "fetched_at": "2026-07-09T16:13:00Z",
            "stale": False,
            "age_s": 0.0,
        },
        "codex": {
            "lane": "codex",
            "primary_used_pct": 5.0,
            "weekly_used_pct": 20.0,
            "monthly_cap_usd": None,
            "monthly_used_usd": None,
            "weekly_resets_at": "2026-07-12T19:26:49Z",
            "weekly_pace_delta_pct": -30.0,
            "will_last_to_reset": True,
            "pace_summary": "30% in reserve",
            "source": "codexbar",
            "fetched_at": "2026-07-09T16:13:00Z",
            "stale": False,
            "age_s": 0.0,
        },
    }
    monkeypatch.setattr(
        state_router,
        "refresh_provider_usage_data",
        lambda providers: refreshed,
    )
    monkeypatch.setattr(
        state_router,
        "get_provider_usage_data",
        lambda provider: {"lane": provider, "weekly_used_pct": None},
    )

    data = state_router.compute_routing_budget(now, fresh_codexbar=True)

    assert data["diagnostics"]["records_loaded"] == 0
    assert data["diagnostics"]["codexbar_data_available"] is True
    assert data["agents"]["claude"]["status"] == "hot"
    assert data["recommendation"]["primary_agent_for_code"] is not None
    assert any("lane claude is in deficit" in warning for warning in data["recommendation"]["warnings"])


def test_stale_snapshot_downgrades_to_advisory_no_hard(monkeypatch, tmp_path):
    """AC: generated/data >15min → stale=true, advisory in warnings; never hard block."""
    now = datetime(2026, 5, 13, 20, 30, tzinfo=UTC)
    old = now - timedelta(minutes=20)
    recs = [_record("codex (gpt-5.5)", 100.0, old)]
    _configure(monkeypatch, tmp_path, recs)

    def _no_codexbar(provider: str) -> dict:
        return {
            "lane": provider,
            "primary_used_pct": None,
            "weekly_used_pct": None,
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
        }

    monkeypatch.setattr(state_router, "get_provider_usage_data", _no_codexbar)

    data = state_router.compute_routing_budget(now)

    assert data["diagnostics"]["stale"] is True
    assert data["diagnostics"]["data_age_s"] and data["diagnostics"]["data_age_s"] > 900
    assert any("stale" in w.lower() for w in data.get("recommendation", {}).get("warnings", []))
    # still computes status from old data, but marked
    assert "codex" in data["agents"]


def test_ranked_by_headroom_orders_by_remaining_and_includes_api_unknown(monkeypatch, tmp_path):
    """AC: load-spread ranked view; subs by headroom (low burn first), api=unknown."""
    now = datetime(2026, 5, 13, 20, 30, tzinfo=UTC)
    _configure(
        monkeypatch,
        tmp_path,
        [
            _record("claude (sonnet)", 100.0, now),
            _record("codex (gpt-5.5)", 50.0, now),
            _record("gemini (pro)", 400.0, now),
        ],
    )
    data = state_router.compute_routing_budget(now)
    ranked = data.get("ranked_by_headroom", [])
    # codex lowest burn should sort before higher
    codex_idx = next(i for i, r in enumerate(ranked) if r["lane"] == "codex")
    gemini_idx = next(i for i, r in enumerate(ranked) if r["lane"] == "gemini")
    assert codex_idx < gemini_idx
    api_entry = next((r for r in ranked if r["type"] == "api"), None)
    assert api_entry and api_entry["status"] == "unknown"
    assert "resets_at" in ranked[0]


def test_resets_at_and_reset_aware_present(monkeypatch, tmp_path):
    now = datetime(2026, 5, 13, 20, 30, tzinfo=UTC)
    _configure(monkeypatch, tmp_path, [_record("codex (gpt-5.5)", 10.0, now)])
    data = state_router.compute_routing_budget(now)
    assert "resets_at" in data["agents"]["codex"]
    assert data["diagnostics"].get("reset_imminent_hours") == 6
    # ranked carries it
    assert any("resets_at" in r for r in data.get("ranked_by_headroom", []))


def test_fresh_codexbar_overlay_omits_ledger_stale_warning(monkeypatch, tmp_path):
    """Fresh codexbar overlay must not leave ledger-stale warnings when diagnostics.stale=false."""
    now = datetime(2026, 5, 13, 20, 30, tzinfo=UTC)
    old = now - timedelta(minutes=20)
    recs = [_record("codex (gpt-5.5)", 100.0, old)]
    _configure(monkeypatch, tmp_path, recs)

    def _fresh_codexbar(provider: str) -> dict:
        if provider == "codex":
            return {
                "lane": "codex",
                "primary_used_pct": 5.0,
                "weekly_used_pct": 20.0,
                "monthly_cap_usd": None,
                "monthly_used_usd": None,
                "weekly_resets_at": "2026-07-12T19:26:49Z",
                "weekly_pace_delta_pct": -30.0,
                "will_last_to_reset": True,
                "pace_summary": "30% in reserve",
                "source": "codexbar",
                "fetched_at": "2026-07-09T14:13:52Z",
                "stale": False,
                "age_s": 10.0,
            }
        return {
            "lane": provider,
            "primary_used_pct": None,
            "weekly_used_pct": None,
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
        }

    monkeypatch.setattr(state_router, "get_provider_usage_data", _fresh_codexbar)

    data = state_router.compute_routing_budget(now)

    assert data["diagnostics"]["stale"] is False
    assert not any(">15min" in w or "stale" in w.lower() for w in data["recommendation"]["warnings"])
