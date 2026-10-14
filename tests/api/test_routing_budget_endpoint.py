"""Tests for /api/state/routing-budget."""

from __future__ import annotations

import contextlib
import json
import os
import time
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from scripts.analytics.cost_report import CostRecord
from scripts.api import claude_account_usage, state_router
from scripts.api.monitor_context import fixture_context
from scripts.fleet import reset_reserve


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


def _empty_runtime(agent: str, **_kwargs) -> dict:
    return {
        "source": "agent_runtime_jsonl",
        "window_s": 300,
        "ok": 0,
        "error": 0,
        "rate_limited": 0,
        "timeout": 0,
        "other": 0,
        "total": 0,
        "last_outcome_at": None,
        "last_rate_limited_at": None,
        "models_rate_limited": [],
        "headroom_blocked": False,
        "headroom_reason": "",
    }


def _empty_fleet_burn(agent: str, **_kwargs) -> dict:
    empty_counts = {"ok": 0, "error": 0, "rate_limited": 0, "timeout": 0, "other": 0, "total": 0}
    return {
        "source": "agent_runtime_jsonl",
        "agent": agent,
        "windows": {
            "5h": {"window_s": 18000, "counts": dict(empty_counts), "hours": 0.0},
            "7d": {"window_s": 604800, "counts": dict(empty_counts), "hours": 0.0},
            "30d": {"window_s": 2592000, "counts": dict(empty_counts), "hours": 0.0},
        },
    }


def _mock_cursor_lane(*, auto_pct: float | None = None, api_pct: float = 20.0, login: str = "authenticated") -> dict:
    if login == "NEED_LOGIN":
        return {
            "lane": "cursor",
            "login_state": "NEED_LOGIN",
            "probe_state": "NEED_LOGIN",
            "is_authenticated": False,
            "status": "need_login",
            "provider_windows": {
                "auto": {"window": "monthly", "used_pct": None, "remaining_pct": None, "resets_at": None},
                "api": {"window": "monthly", "used_pct": None, "remaining_pct": None, "resets_at": None},
            },
            "fetched_at": "2026-05-13T20:30:00Z",
        }
    if auto_pct is None:
        return {
            "lane": "cursor",
            "login_state": "authenticated",
            "probe_state": "NEED_PROBE",
            "is_authenticated": True,
            "status": "unknown",
            "provider_windows": {
                "auto": {"window": "monthly", "used_pct": None, "remaining_pct": None, "resets_at": None},
                "api": {"window": "monthly", "used_pct": None, "remaining_pct": None, "resets_at": None},
            },
            "fetched_at": "2026-05-13T20:30:00Z",
        }
    return {
        "lane": "cursor",
        "login_state": "authenticated",
        "probe_state": "healthy",
        "is_authenticated": True,
        "status": "cool",
        "primary_used_pct": auto_pct,
        "tertiary_used_pct": api_pct,
        "provider_windows": {
            "auto": {
                "window": "monthly",
                "label": "Auto",
                "used_pct": auto_pct,
                "remaining_pct": 100.0 - auto_pct,
                "resets_at": "2026-08-01T09:58:38Z",
            },
            "api": {
                "window": "monthly",
                "label": "API",
                "used_pct": api_pct,
                "remaining_pct": 100.0 - api_pct,
                "resets_at": "2026-08-01T09:58:38Z",
            },
        },
        "weekly_resets_at": "2026-08-01T09:58:38Z",
        "fetched_at": "2026-05-13T20:30:00Z",
        "source": "cursor_native",
    }


def _configure(monkeypatch, tmp_path: Path, records: list[CostRecord]) -> None:
    budget_path = _write_budget_config(tmp_path)
    # The producer's runtime plane defaults to the shared checkout's ``batch_state``. Pin it to a
    # fixture checkout whose lane-health scan runs over an empty tasks directory (observed idle,
    # so healthy): never the host's live tasks and rate limits, and never an unscannable plane
    # whose unknown health would fail the reserve's health precondition (#9740 A1).
    shared_checkout = tmp_path / "shared-checkout"
    (shared_checkout / "batch_state" / "tasks").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(state_router, "main_checkout_root", lambda _root: shared_checkout)
    monkeypatch.setattr(
        state_router,
        "_load_agent_budgets",
        lambda budget_config_path=None: state_router._read_agent_budgets_file(budget_path),
    )
    monkeypatch.setattr(state_router, "load_cost_records", lambda **_kwargs: records)

    def _mock_cb(provider: str) -> dict | None:
        spent = sum(r.cost_usd_est for r in records if r.agent.startswith(provider))
        is_promo = provider == "claude" and any(r.mtime and r.mtime.date() <= date(2026, 7, 13) for r in records)
        caps = {"claude": 690.0 if is_promo else 460.0, "codex": 1000.0, "gemini": 500.0}
        cap = caps.get(provider)
        if cap and spent > 0:
            pct = round((spent / cap) * 100, 1)
            is_def = pct >= 75.0
            return {
                "lane": provider,
                "primary_used_pct": pct,
                "weekly_used_pct": pct,
                "monthly_cap_usd": None,
                "monthly_used_usd": None,
                "weekly_resets_at": "2026-05-18T00:00:00Z",
                "weekly_pace_delta_pct": 10.0 if is_def else -10.0,
                "will_last_to_reset": not is_def,
                "pace_summary": f"{pct}% used",
                "source": "codexbar",
                "fetched_at": "2026-05-13T20:30:00Z",
                "stale": False,
                "age_s": 0.0,
            }
        return None

    monkeypatch.setattr(state_router, "get_provider_usage_data", _mock_cb)
    monkeypatch.setattr(state_router, "get_cursor_lane_usage", lambda **kwargs: _mock_cursor_lane())
    monkeypatch.setattr(
        state_router,
        "get_api_account_data",
        lambda provider: {
            "kind": "prepaid_credits",
            "probe_state": "NEED_PROBE",
            "fetched_at": None,
            **({"local_only": True} if provider == "deepseek" else {}),
        },
    )
    monkeypatch.setattr(state_router, "summarize_fleet_burn", _empty_fleet_burn)
    monkeypatch.setattr(state_router, "summarize_lane_runtime", _empty_runtime)
    monkeypatch.setattr(
        state_router,
        "persist_provider_snapshot",
        lambda lane, snapshot: {"trend": "flat", "samples": 1},
    )
    monkeypatch.setattr(
        state_router.delegate_api,
        "list_delegate_tasks",
        lambda **_kwargs: {"tasks": []},
    )


# Frozen key sets for the dispatch payload the routing page renders.
# A new or removed key is a shape change and must fail here.
_ROUTING_BUDGET_TOP_LEVEL_KEYS = frozenset(
    {
        "generated_at",
        "agents",
        "reset_reserve",
        "api_accounts",
        "in_flight",
        "recommendation",
        "diagnostics",
        "ranked_by_headroom",
        "transport",
        # Per-account Claude view (#10630); additive, display only.
        "claude_accounts",
        "preferred_claude_account",
    }
)
_ROUTING_BUDGET_RECOMMENDATION_KEYS = frozenset(
    {
        "primary_agent_for_code",
        "rationale",
        "warnings",
    }
)
_ROUTING_BUDGET_DIAGNOSTIC_KEYS = frozenset(
    {
        "records_loaded",
        "missing_cost_records",
        "window_start",
        "stale",
        "data_age_s",
        "stale_threshold_s",
        "reset_imminent_hours",
        "codexbar_data_available",
        "codexbar_freshness",
        "codexbar_max_age_s",
        "fresh_codexbar_requested",
        "fresh_codexbar_blocking",
        "runtime_data_available",
        "runtime_usage_records_7d",
        "budget_ledger_empty",
        "usage_sources",
        "fleet_burn_available",
        "notebook_report_available",
        "notebook_report_max_age_s",
    }
)
_ROUTING_BUDGET_USAGE_SOURCE_KEYS = frozenset(
    {
        "allotment",
        "burn_rate_limit",
        "fleet_burn",
    }
)


def test_routing_budget_shape_lock(monkeypatch, tmp_path):
    """The routing page depends on this key set. Do not add or drop keys."""
    _configure(monkeypatch, tmp_path, [])
    ctx = fixture_context(tmp_path)
    # An observable tasks directory publishes measured counts. A missing
    # directory stays null (unknown load), which the page treats as empty.
    (ctx.roots.batch_state_dir / "tasks").mkdir(parents=True, exist_ok=True)
    app = FastAPI()
    app.state.ctx = ctx
    app.include_router(state_router.router, prefix="/api/state")

    response = TestClient(app).get("/api/state/routing-budget")

    assert response.status_code == 200
    data = response.json()
    assert set(data) == _ROUTING_BUDGET_TOP_LEVEL_KEYS
    assert set(data["recommendation"]) == _ROUTING_BUDGET_RECOMMENDATION_KEYS
    assert set(data["diagnostics"]) == _ROUTING_BUDGET_DIAGNOSTIC_KEYS
    assert set(data["diagnostics"]["usage_sources"]) == _ROUTING_BUDGET_USAGE_SOURCE_KEYS
    assert data["transport"] == "dispatch"
    assert isinstance(data["agents"], dict)
    assert isinstance(data["api_accounts"], dict)
    assert isinstance(data["ranked_by_headroom"], list)
    assert isinstance(data["in_flight"], dict)
    assert all(isinstance(count, int) for count in data["in_flight"].values())


def test_endpoint_returns_documented_shape(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path, [])
    app = FastAPI()
    app.state.ctx = fixture_context(tmp_path)
    app.include_router(state_router.router, prefix="/api/state")

    response = TestClient(app).get("/api/state/routing-budget")

    assert response.status_code == 200
    data = response.json()
    assert {"agents", "in_flight", "recommendation", "diagnostics", "generated_at"} <= data.keys()
    assert data["diagnostics"]["usage_sources"]["allotment"] in {"codexbar", "codexbar+cursor_native"}
    assert data["diagnostics"]["usage_sources"]["burn_rate_limit"] == "agent_runtime_jsonl"
    assert "runtime" in data["agents"]["codex"]


def test_runtime_headroom_blocked_demotes_lane(monkeypatch, tmp_path):
    """Agent JSONL rate-limit cluster demotes a CodexBar-cool lane."""
    now = datetime(2026, 5, 13, 20, 30, tzinfo=UTC)
    _configure(monkeypatch, tmp_path, [_record("codex (gpt-5.5)", 10.0, now)])

    def _runtime(agent: str, **_kwargs) -> dict:
        base = _empty_runtime(agent)
        if agent == "codex":
            base.update(
                {
                    "ok": 1,
                    "rate_limited": 2,
                    "total": 3,
                    "headroom_blocked": True,
                    "headroom_reason": "rate_limited 5s ago (2 events in last 5min)",
                    "models_rate_limited": ["gpt-5.5"],
                }
            )
        return base

    monkeypatch.setattr(state_router, "summarize_lane_runtime", _runtime)
    monkeypatch.setattr(
        state_router,
        "get_provider_usage_data",
        lambda provider: (
            {
                "lane": provider,
                "primary_used_pct": 5.0,
                "weekly_used_pct": 10.0,
                "weekly_pace_delta_pct": -20.0,
                "will_last_to_reset": True,
                "pace_summary": "ok",
                "stale": False,
                "age_s": 1.0,
            }
            if provider == "codex"
            else None
        ),
    )
    data = state_router.compute_routing_budget(now)

    assert data["agents"]["codex"]["status"] == "hot"
    assert data["agents"]["codex"]["runtime"]["headroom_blocked"] is True
    assert any("runtime headroom blocked" in w for w in data["recommendation"]["warnings"])
    ranked = data["ranked_by_headroom"]
    # blocked codex should not lead healthy free seats when others exist
    first_sub = next(r for r in ranked if r["type"] == "subscription")
    # at least diagnostics declare hybrid sources
    assert data["diagnostics"]["usage_sources"]["burn_rate_limit"] == "agent_runtime_jsonl"
    assert first_sub["lane"]  # smoke


def test_api_projects_sanitized_reserve_and_can_recommend_codex(monkeypatch, tmp_path):
    now = datetime(2026, 5, 13, 20, 30, tzinfo=UTC)
    _configure(
        monkeypatch,
        tmp_path,
        [
            _record("codex (gpt-5.5)", 800.0, now),
            _record("claude", 650.0, now),
            _record("gemini", 480.0, now),
        ],
    )
    monkeypatch.setattr(state_router, "get_freshest_lane_usage", lambda: None)
    monkeypatch.setattr(
        state_router,
        "load_reset_reserve",
        lambda *_args, **_kwargs: {
            "available": True,
            "provider": "codex",
            "remaining_resets": 2,
            "confirmed_at": "2026-05-13T20:00:00Z",
            "expires_at": "2026-05-14T20:00:00Z",
        },
    )
    monkeypatch.setattr(
        state_router,
        "get_provider_usage_data",
        lambda provider: (
            {
                "lane": "codex",
                "primary_used_pct": 70.0,
                "weekly_used_pct": 80.0,
                "weekly_pace_delta_pct": 10.0,
                "weekly_expected_pct": 70.0,
                "will_last_to_reset": False,
                "windows": {"primary": {"remaining_pct": 20.0, "window_minutes": 300}},
                "stale": False,
                "freshness": "fresh",
                "age_s": 1.0,
                "reset_credits": {
                    "available_count": 2,
                    "expires_at": ["2026-05-20T00:00:00Z", "2026-05-21T00:00:00Z"],
                    "fetched_at": now.isoformat(),
                },
            }
            if provider == "codex"
            else None
        ),
    )

    monkeypatch.setattr(
        state_router,
        "_recommend_agent",
        lambda *_args, **_kwargs: {"primary_agent_for_code": "cursor", "rationale": "cooler seat", "warnings": []},
    )
    data = state_router.compute_routing_budget(now)

    assert data["reset_reserve"] == {
        "available": True,
        "provider": "codex",
        "remaining_resets": 2,
        "confirmed_at": "2026-05-13T20:00:00Z",
        "expires_at": "2026-05-14T20:00:00Z",
    }
    assert data["agents"]["codex"]["status"] == "cool"
    assert data["agents"]["codex"]["pace_deficit"]["covered_by"] == ["free full reset"]
    assert data["recommendation"]["primary_agent_for_code"] == "codex"


@pytest.mark.parametrize(
    ("inventory_overrides", "provider_overrides", "available"),
    [
        ({}, {}, True),
        ({"available_count": 0, "expires_at": []}, {}, False),
        ({}, {"stale": True, "freshness": "stale_last_good"}, False),
        ({"fetched_at": "2026-05-13T20:00:00Z"}, {}, False),
    ],
)
def test_fresh_refresh_evaluates_reserve_from_response_inventory(
    monkeypatch, tmp_path, inventory_overrides, provider_overrides, available
):
    now = datetime(2026, 5, 13, 20, 30, tzinfo=UTC)
    _configure(monkeypatch, tmp_path, [_record("codex (gpt-5.5)", 800.0, now)])
    monkeypatch.setattr(state_router, "get_freshest_lane_usage", lambda: None)
    monkeypatch.setattr(reset_reserve, "main_checkout_root", lambda _root: tmp_path)
    assertion_path = tmp_path / reset_reserve.RESERVE_RELATIVE_PATH
    assertion_path.parent.mkdir(parents=True)
    assertion_path.write_text(
        json.dumps(
            {
                "schema_version": reset_reserve.SCHEMA_VERSION,
                "provider": "codex",
                "remaining_resets": 5,
                "confirmed_at": "2026-05-13T20:00:00Z",
                "expires_at": "2026-05-14T20:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    cached = {
        "lane": "codex",
        "primary_used_pct": 70.0,
        "weekly_used_pct": 80.0,
        "weekly_pace_delta_pct": 10.0,
        "weekly_expected_pct": 70.0,
        "will_last_to_reset": False,
        "windows": {"primary": {"remaining_pct": 20.0, "window_minutes": 300}},
        "stale": False,
        "freshness": "fresh",
        "age_s": 0,
    }
    refreshed = {
        **cached,
        "reset_credits": {
            "available_count": 2,
            "expires_at": [None, None],
            "fetched_at": now.isoformat(),
            **inventory_overrides,
        },
        **provider_overrides,
    }
    monkeypatch.setattr(
        state_router, "get_provider_usage_data", lambda provider: cached if provider == "codex" else None
    )
    monkeypatch.setattr(state_router, "refresh_provider_usage_data", lambda _providers: {"codex": refreshed})
    # The refresh result need not update the process cache for this response.
    monkeypatch.setattr(reset_reserve, "get_provider_usage_data", lambda _provider: cached)

    before = state_router.compute_routing_budget(now)
    data = state_router.compute_routing_budget(now, fresh_codexbar=True)

    assert before["reset_reserve"] == reset_reserve.unavailable_reserve()
    assert data["agents"]["codex"]["reset_credits"] == refreshed["reset_credits"]
    assert data["agents"]["codex"]["status"] == ("cool" if available else "hot")
    assert data["agents"]["codex"]["pace_deficit"]["uncovered"] is (not available)
    if available:
        assert data["reset_reserve"] == {
            "available": True,
            "provider": "codex",
            "remaining_resets": 2,
            "confirmed_at": "2026-05-13T20:00:00Z",
            "expires_at": "2026-05-14T20:00:00Z",
        }
        assert data["recommendation"]["primary_agent_for_code"] == "codex"
        assert any(
            "Codex reset reserve active (2 confirmed reset(s) remaining)" in w
            for w in data["recommendation"]["warnings"]
        )
    else:
        assert data["reset_reserve"] == reset_reserve.unavailable_reserve()
        assert not any("Codex reset reserve active" in w for w in data["recommendation"]["warnings"])


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
            _record("claude (sonnet)", 683.1, now),
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
        assert st in ("unknown", "unavailable"), f"{lane} should be unknown/unavailable on empty"
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


def test_codexbar_probe_failure_does_not_wipe_ledger_status_and_burn(monkeypatch, tmp_path):
    """When CodexBar lacks weekly_used_pct, retain ledger-derived burn and status instead of 'unavailable'."""
    now = datetime(2026, 5, 13, 20, 30, tzinfo=UTC)
    _configure(monkeypatch, tmp_path, [_record("codex (gpt-5.5)", 100.0, now)])

    def _failing_codexbar(provider: str) -> dict:
        return {
            "lane": provider,
            "primary_used_pct": None,
            "weekly_used_pct": None,
            "status": "unavailable",
            "auth_error": "CodexBar usage data unavailable",
            "error_kind": "unavailable",
            "source": "codexbar",
            "fetched_at": None,
            "stale": False,
            "age_s": None,
        }

    monkeypatch.setattr(state_router, "get_provider_usage_data", _failing_codexbar)

    data = state_router.compute_routing_budget(now)

    codex = data["agents"]["codex"]
    assert codex["status"] == "cool"
    assert codex["burn_pct_7d"] == 10.0
    assert codex["remaining_pct"] == 90.0
    assert codex["codexbar"]["status"] == "unavailable"


def test_http_fresh_codexbar_kicks_background_and_does_not_block(monkeypatch, tmp_path):
    """The HTTP query flag must not wait for the CodexBar CLI.

    Dispatch used to call /api/state/routing-budget?fresh_codexbar=true and
    stall the Monitor worker for ~17–25s (then 504 at the 10s request
    timeout while the thread kept running). HTTP now serves cache/LKG and
    kicks one background refresh.
    """
    _configure(monkeypatch, tmp_path, [])
    blocking_calls = []
    kicked = []

    def _block(*_args, **_kwargs):
        blocking_calls.append("refresh_provider_usage_data")
        raise AssertionError("HTTP must not block on CodexBar CLI")

    monkeypatch.setattr(state_router, "refresh_provider_usage_data", _block)
    monkeypatch.setattr(state_router, "trigger_background_refresh", lambda: kicked.append("kick"))
    monkeypatch.setattr(
        state_router,
        "get_provider_usage_data",
        lambda provider: {
            "lane": provider,
            "weekly_used_pct": 10.0,
            "will_last_to_reset": True,
            "weekly_pace_delta_pct": -20.0,
            "stale": False,
            "age_s": 12.0,
            "freshness": "fresh",
        },
    )

    app = FastAPI()
    app.state.ctx = fixture_context(tmp_path)
    app.include_router(state_router.router, prefix="/api/state")
    response = TestClient(app).get("/api/state/routing-budget?fresh_codexbar=true")

    assert response.status_code == 200
    data = response.json()
    assert blocking_calls == []
    assert kicked == ["kick"]
    assert data["diagnostics"]["fresh_codexbar_requested"] is True
    assert data["diagnostics"]["fresh_codexbar_blocking"] is False


def test_compute_routing_budget_computes_in_flight_once(monkeypatch, tmp_path):
    """compute_routing_budget must scan in-flight tasks once, not per subscription lane (#7596)."""
    now = datetime(2026, 5, 13, 20, 30, tzinfo=UTC)
    _configure(monkeypatch, tmp_path, [_record("codex (gpt-5.5)", 100.0, now)])

    calls = 0
    orig_in_flight = state_router._in_flight_by_agent

    def _counted_in_flight(*args, **kwargs):
        nonlocal calls
        calls += 1
        return orig_in_flight(*args, **kwargs)

    monkeypatch.setattr(state_router, "_in_flight_by_agent", _counted_in_flight)

    data = state_router.compute_routing_budget(now)

    assert calls == 1
    assert "in_flight" in data
    ranked = data.get("ranked_by_headroom", [])
    sub_lanes = [r for r in ranked if r.get("type") == "subscription"]
    assert len(sub_lanes) == len(state_router.SUBSCRIPTION_LANES)
    for row in sub_lanes:
        assert "in_flight" in row


def test_glm_is_not_a_subscription_lane_or_ranked_provider(monkeypatch, tmp_path):
    """Retired GLM/Z.AI seat must not appear in routing-budget lanes or rank."""
    from scripts.api import subscription_usage as subscription_usage_mod

    assert "glm" not in state_router.SUBSCRIPTION_LANES
    assert "glm" not in subscription_usage_mod.SUBSCRIPTION_PROVIDERS
    assert "glm" not in subscription_usage_mod.PROVIDER_TO_LANE
    assert "glm" not in subscription_usage_mod._NATIVE_PROBES

    now = datetime(2026, 5, 13, 20, 30, tzinfo=UTC)
    _configure(monkeypatch, tmp_path, [])
    data = state_router.compute_routing_budget(now)

    assert "glm" not in data["agents"]
    assert all(row.get("lane") != "glm" for row in data.get("ranked_by_headroom", []))


def test_empty_ledger_reports_agentic_pool_unknown(monkeypatch, tmp_path):
    """#9172: zero USD ledger records must not read as a cool agentic pool."""
    now = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)
    _configure(monkeypatch, tmp_path, [])

    data = state_router.compute_routing_budget(now)

    pool = data["agents"]["claude"]["agentic_pool"]
    assert pool["spent_cycle_usd"] is None
    assert pool["burn_pct_cycle"] is None
    assert pool["status"] == "unknown"
    assert pool["active"] is True
    assert pool["monthly_cap_usd"] == 200.0
    assert pool["starts_on"] == "2026-06-15"
    recommendation = data["recommendation"]
    assert recommendation["primary_agent_for_code"] != "claude"
    assert "agentic pool" not in recommendation["rationale"]


def test_records_present_do_not_override_capacity_order_with_agentic_pool(monkeypatch, tmp_path):
    """#10279: pool telemetry remains visible without overriding code capacity order."""
    now = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)
    _configure(monkeypatch, tmp_path, [_record("claude (sonnet)", 10.0, now)])

    data = state_router.compute_routing_budget(now)

    pool = data["agents"]["claude"]["agentic_pool"]
    assert pool["spent_cycle_usd"] == 10.0
    assert pool["burn_pct_cycle"] == 5.0
    assert pool["status"] == "cool"
    recommendation = data["recommendation"]
    assert recommendation["primary_agent_for_code"] == "codex"
    assert "capacity picker order" in recommendation["rationale"]
    assert "agentic pool" not in recommendation["rationale"]


@pytest.mark.parametrize("used", [90.0, 98.99, 99.0, 100.0])
def test_claude_weekly_near_cap_status_and_warning_boundary(monkeypatch, tmp_path, used):
    now = datetime(2026, 7, 9, 16, 13, tzinfo=UTC)
    _configure(monkeypatch, tmp_path, [])
    monkeypatch.setattr(
        state_router,
        "get_provider_usage_data",
        lambda provider: {
            "lane": provider,
            "weekly_used_pct": used if provider == "claude" else None,
            "weekly_remaining_pct": 100.0 - used if provider == "claude" else None,
            "weekly_expected_pct": 99.5,
            "weekly_pace_delta_pct": used - 99.5,
            "will_last_to_reset": True,
            "freshness": "fresh",
            "age_s": 0.0,
            "fetched_at": now.isoformat(),
            "stale": False,
        },
    )
    data = state_router.compute_routing_budget(now)
    near_cap = used >= 99.0
    assert data["agents"]["claude"]["status"] == ("near_cap" if near_cap else "cool")
    warnings = data["recommendation"]["warnings"]
    assert any("lane claude is in deficit" in warning for warning in warnings) is near_cap


# ---- per-account Claude rows (#10630) ------------------------------------------

# ``agents.claude`` stays the default-account lane. Its field set is pinned as it
# was before the per-account view existed; the new rows must not change it.
_LEGACY_CLAUDE_LANE_KEYS = frozenset(
    {
        "agentic_pool",
        "burn_pct_7d",
        "codexbar",
        "credit",
        "fleet_burn",
        "health",
        "interactive",
        "pace_deficit",
        "remaining_pct",
        "resets_at",
        "routing_facts",
        "runtime",
        "spent_7d_usd",
        "status",
        "status_source",
        "weekly_cap_usd",
    }
)
_ACCOUNT_EMAIL = "owner-do-not-leak@example.invalid"
_ACCOUNT_UUIDS = {"a": "0a0a0a0a-0a0a-4a0a-8a0a-0a0a0a0a0a0a", "b": "0b0b0b0b-0b0b-4b0b-8b0b-0b0b0b0b0b0b"}


def _account_payload(label: str, weekly_used: float, weekly_expected: float, *, updated: datetime) -> bytes:
    email = f"{label}-{_ACCOUNT_EMAIL}"
    return json.dumps(
        [
            {
                "provider": "claude",
                "source": "oauth",
                "accountId": "0f0e0d0c-0b0a-4908-8706-050403020100",
                "pace": {
                    "primary": {"expectedUsedPercent": 50, "deltaPercent": -10, "summary": "10% in reserve"},
                    "secondary": {
                        "expectedUsedPercent": weekly_expected,
                        "deltaPercent": 5,
                        "summary": "5% in deficit",
                    },
                },
                "usage": {
                    "updatedAt": updated.isoformat(timespec="seconds").replace("+00:00", "Z"),
                    "primary": {"usedPercent": 30, "resetsAt": "2026-10-14T18:00:00Z"},
                    "secondary": {"usedPercent": weekly_used, "resetsAt": "2026-10-18T07:00:00Z"},
                    "accountEmail": email,
                    "identity": {"accountEmail": email},
                },
            }
        ]
    ).encode()


@contextlib.contextmanager
def _open_fixture_directory(path):
    """The production opener's leaf rule (a link is never followed), without its
    walk from root, which refuses the shared temporary directory fixtures live under."""
    try:
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError:
        raise claude_account_usage.ClaudeAccountRefused("claude_account_config_dir_not_private") from None
    try:
        yield fd
    finally:
        os.close(fd)


def _write_private_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value))
    path.chmod(0o600)


def _account_dirs(monkeypatch, tmp_path: Path) -> dict[str, Path]:
    """A fixture home (label ``a``) and a second Claude directory bound to label ``b``,
    each recording its own account; probes and serves run the real binding checks."""
    home = tmp_path / "account-home"
    dirs = {"a": home / ".claude", "b": tmp_path / "account-b"}
    for label, directory in dirs.items():
        directory.mkdir(parents=True, exist_ok=True)
        record = home / ".claude.json" if label == "a" else directory / ".claude.json"
        _write_private_json(record, {"oauthAccount": {"accountUuid": _ACCOUNT_UUIDS[label]}})
    binding = tmp_path / "claude-accounts.json"
    entry = {"config_dir": str(dirs["b"]), "account_uuid": _ACCOUNT_UUIDS["b"]}
    _write_private_json(binding, {"schema_version": 1, "accounts": {"b": entry}})
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("LU_CLAUDE_ACCOUNTS_FILE", str(binding))
    monkeypatch.setattr(claude_account_usage, "_open_claude_directory", _open_fixture_directory)
    return dirs


def _populate_accounts(monkeypatch, tmp_path: Path, *, b_fails: bool = False, age_s: float = 0.0) -> None:
    """Fill the per-account cache from fixtures, as the background refresh would."""
    dirs = _account_dirs(monkeypatch, tmp_path)
    updated = datetime.now(UTC) - timedelta(seconds=age_s)

    def run(codexbar, env, *, timeout_s, max_bytes):
        if env["CLAUDE_CONFIG_DIR"] == str(dirs["b"]):
            if b_fails:
                raise claude_account_usage._ProbeFailed("timeout")
            return _account_payload("b", 20, 47, updated=updated)
        return _account_payload("a", 74, 47, updated=updated)

    monkeypatch.setattr(claude_account_usage, "_codexbar_bin", lambda: "/fixture/bin/codexbar")
    monkeypatch.setattr(claude_account_usage, "_run_codexbar", run)
    claude_account_usage.refresh_claude_account_usage()


def _routing_client(tmp_path: Path) -> TestClient:
    app = FastAPI()
    app.state.ctx = fixture_context(tmp_path)
    app.include_router(state_router.router, prefix="/api/state")
    return TestClient(app)


# Fails on origin/main: the payload has no ``claude_accounts`` key.
def test_endpoint_publishes_one_row_per_claude_account(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path, [])
    _populate_accounts(monkeypatch, tmp_path)

    response = _routing_client(tmp_path).get("/api/state/routing-budget")

    assert response.status_code == 200
    data = response.json()
    assert set(data["claude_accounts"]) == {"claude:a", "claude:b"}
    row_a, row_b = data["claude_accounts"]["claude:a"], data["claude_accounts"]["claude:b"]
    assert row_a["status"] == row_b["status"] == "ok"
    assert row_a["weekly"]["left_pct"] == 26.0
    assert row_a["weekly"]["leftover_pct"] == 0
    assert row_b["weekly"]["left_pct"] == 80.0
    assert row_b["weekly"]["leftover_pct"] == 57
    assert row_b["session5h"]["left_pct"] == 70.0
    assert row_b["session5h"]["leftover_pct"] == 40
    assert data["preferred_claude_account"] == "b"


def test_endpoint_stays_200_when_one_account_probe_fails(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path, [])
    _populate_accounts(monkeypatch, tmp_path, b_fails=True)

    response = _routing_client(tmp_path).get("/api/state/routing-budget")

    assert response.status_code == 200
    rows = response.json()["claude_accounts"]
    assert rows["claude:a"]["status"] == "ok"
    assert rows["claude:a"]["weekly"]["leftover_pct"] == 0
    assert rows["claude:b"]["status"] == "unknown"
    assert rows["claude:b"]["reason"] == "timeout"
    assert rows["claude:b"]["weekly"]["left_pct"] is None
    assert response.json()["preferred_claude_account"] is None


def test_endpoint_payload_carries_no_account_identity_or_path(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path, [])
    _populate_accounts(monkeypatch, tmp_path)

    response = _routing_client(tmp_path).get("/api/state/routing-budget")
    body = response.text

    # The rows are present, so the absence checks below are not vacuous.
    rows = response.json()["claude_accounts"]
    assert {row["status"] for row in rows.values()} == {"ok"}
    for forbidden in (
        _ACCOUNT_EMAIL,
        "example.invalid",
        "0f0e0d0c-0b0a-4908-8706-050403020100",
        *_ACCOUNT_UUIDS.values(),
        str(tmp_path),
        "account-b",
        "accountEmail",
        "accountId",
        "accountUuid",
        "CLAUDE_CONFIG_DIR",
        "config_dir",
    ):
        assert forbidden not in body, forbidden


def test_request_path_never_spawns_the_account_probe(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path, [])
    spawned: list[str] = []

    def forbidden(*_args, **_kwargs):
        spawned.append("probe")
        raise AssertionError("request path must not probe")

    monkeypatch.setattr(claude_account_usage, "probe_account", forbidden)
    monkeypatch.setattr(claude_account_usage, "_run_codexbar", forbidden)
    monkeypatch.setattr(claude_account_usage, "refresh_claude_account_usage", forbidden)
    client = _routing_client(tmp_path)

    cold = client.get("/api/state/routing-budget")
    warm = client.get("/api/state/routing-budget")
    in_process = state_router.compute_routing_budget(tasks_dir=tmp_path / "tasks")

    assert cold.status_code == warm.status_code == 200
    assert spawned == []
    assert {row["status"] for row in cold.json()["claude_accounts"].values()} == {"unknown"}
    assert set(in_process["claude_accounts"]) == {"claude:a", "claude:b"}


def test_legacy_claude_lane_is_unchanged_by_account_rows(monkeypatch, tmp_path):
    """Legacy readers see the same default-account lane with or without the new rows."""
    _configure(monkeypatch, tmp_path, [])
    _account_dirs(monkeypatch, tmp_path)  # same fixture home for both computations
    now = datetime(2026, 10, 14, 15, 0, tzinfo=UTC)

    without_rows = state_router.compute_routing_budget(now=now, tasks_dir=tmp_path / "tasks")
    _populate_accounts(monkeypatch, tmp_path)
    with_rows = state_router.compute_routing_budget(now=now, tasks_dir=tmp_path / "tasks")

    assert set(without_rows["agents"]["claude"]) == _LEGACY_CLAUDE_LANE_KEYS
    assert json.dumps(with_rows["agents"]["claude"], sort_keys=True, default=str) == json.dumps(
        without_rows["agents"]["claude"], sort_keys=True, default=str
    )
    assert [row["lane"] for row in with_rows["ranked_by_headroom"]].count("claude") == 1
    assert not any(str(lane).startswith("claude:") for lane in with_rows["agents"])
    assert with_rows["recommendation"] == without_rows["recommendation"]


def test_withdrawn_snapshot_clears_the_account_preference():
    payload = {
        "recommendation": {"primary_agent_for_code": "claude", "warnings": []},
        "agents": {},
        "claude_accounts": {"claude:a": {"status": "ok"}},
        "preferred_claude_account": "a",
    }
    withdrawn = state_router._withdraw_routing_authorization(payload)
    assert withdrawn["preferred_claude_account"] is None
    assert withdrawn["claude_accounts"] == {"claude:a": {"status": "ok"}}


# Fails on b62a4a3243: a warm routing snapshot served the account rows frozen at compute time.
def test_warm_snapshot_serves_live_account_rows(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path, [])
    _populate_accounts(monkeypatch, tmp_path)
    client = _routing_client(tmp_path)

    first = client.get("/api/state/routing-budget").json()
    assert first["claude_accounts"]["claude:b"]["status"] == "ok"
    assert first["preferred_claude_account"] == "b"

    claude_account_usage._record("b", None, "timeout")  # the next background probe of b fails
    warm = client.get("/api/state/routing-budget").json()

    assert warm["diagnostics"] == first["diagnostics"]  # served from the routing cache
    assert warm["claude_accounts"]["claude:b"]["status"] == "stale"
    assert warm["claude_accounts"]["claude:b"]["reason"] == "timeout"
    assert warm["preferred_claude_account"] is None


# Fails on e75cb7e113: a warm routing snapshot kept serving b's row ``ok`` and
# preferred after b's binding was removed.
def test_warm_snapshot_withholds_a_row_whose_binding_was_removed(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path, [])
    _populate_accounts(monkeypatch, tmp_path)
    client = _routing_client(tmp_path)
    first = client.get("/api/state/routing-budget").json()
    assert first["claude_accounts"]["claude:b"]["status"] == "ok"

    _write_private_json(tmp_path / "claude-accounts.json", {"schema_version": 1, "accounts": {}})
    warm = client.get("/api/state/routing-budget").json()

    assert warm["diagnostics"] == first["diagnostics"]  # served from the routing cache
    row_b = warm["claude_accounts"]["claude:b"]
    assert (row_b["status"], row_b["reason"]) == ("unknown", "claude_account_binding_missing")
    assert row_b["weekly"]["left_pct"] is None
    assert warm["claude_accounts"]["claude:a"]["status"] == "ok"
    assert warm["preferred_claude_account"] is None


# Fails on b62a4a3243: a 710 s old sample served 60 s later still reported ``ok``,
# its frozen age, and the account preference, past the 720 s account TTL.
def test_aged_snapshot_reads_account_freshness_at_serve_time(monkeypatch, tmp_path):
    monkeypatch.setenv("CODEXBAR_CACHE_TTL_S", "720")
    _configure(monkeypatch, tmp_path, [])
    _populate_accounts(monkeypatch, tmp_path, age_s=710)
    fields = claude_account_usage.routing_budget_fields()
    assert {row["status"] for row in fields["claude_accounts"].values()} == {"ok"}
    assert fields["preferred_claude_account"] == "b"
    snapshot = {**fields, "diagnostics": {"data_age_s": 0, "stale_threshold_s": 900}}

    served_at = time.time() + 60
    monkeypatch.setattr(time, "time", lambda: served_at)
    served = state_router._aged_routing_budget(snapshot, 60)

    row_b = served["claude_accounts"]["claude:b"]
    assert row_b["status"] == "stale"
    assert row_b["reason"] == "expired"
    assert row_b["age_s"] >= 770
    assert served["preferred_claude_account"] is None
    assert snapshot["claude_accounts"] is fields["claude_accounts"]  # the stored snapshot is not mutated
