"""Cursor subscription / routing-budget acceptance tests."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from scripts.api import state_router
from scripts.fleet import capacity_pick


def _write_budget_config(tmp_path: Path) -> Path:
    path = tmp_path / "agent_budgets.yaml"
    path.write_text(
        """
claude:
  interactive:
    weekly_cap_usd: 460
  agentic_pool:
    monthly_cap_usd: 200
    starts_on: "2026-06-15"
codex:
  weekly_cap_usd: 1000
""".lstrip(),
        encoding="utf-8",
    )
    return path


def _configure_base(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(state_router, "BUDGET_CONFIG_PATH", _write_budget_config(tmp_path))
    monkeypatch.setattr(state_router, "load_cost_records", lambda: [])
    monkeypatch.setattr(
        state_router,
        "get_provider_usage_data",
        lambda provider: {
            "lane": provider,
            "weekly_used_pct": None,
            "status": "unknown",
            "source": "codexbar",
        },
    )
    monkeypatch.setattr(
        state_router,
        "persist_provider_snapshot",
        lambda lane, snapshot: {"trend": "flat", "samples": 1},
    )
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
    monkeypatch.setattr(
        state_router.delegate_api,
        "list_delegate_tasks",
        lambda **_kwargs: {"tasks": []},
    )
    monkeypatch.setattr(
        state_router,
        "summarize_lane_runtime",
        lambda agent: {
            "source": "agent_runtime_jsonl",
            "window_s": 300,
            "ok": 0,
            "error": 0,
            "rate_limited": 0,
            "timeout": 0,
            "other": 0,
            "total": 0,
            "headroom_blocked": False,
            "headroom_reason": "",
        },
    )


def test_cursor_logout_surfaces_need_login_without_substitution(monkeypatch, tmp_path):
    _configure_base(monkeypatch, tmp_path)
    monkeypatch.setattr(
        state_router,
        "get_cursor_lane_usage",
        lambda **kwargs: {
            "lane": "cursor",
            "login_state": "NEED_LOGIN",
            "probe_state": "NEED_LOGIN",
            "is_authenticated": False,
            "status": "need_login",
            "provider_windows": {
                "auto": {"window": "monthly", "used_pct": None, "remaining_pct": None, "resets_at": None},
                "api": {"window": "monthly", "used_pct": None, "remaining_pct": None, "resets_at": None},
            },
        },
    )
    monkeypatch.setattr(state_router, "summarize_fleet_burn", lambda agent, **kwargs: {
        "source": "agent_runtime_jsonl",
        "agent": agent,
        "windows": {"7d": {"counts": {"total": 0}, "hours": 0.0}},
    })

    data = state_router.compute_routing_budget(datetime(2026, 8, 26, 12, 0, tzinfo=UTC))
    cursor = data["agents"]["cursor"]
    assert cursor["status"] == "need_login"
    assert cursor["login_state"] == "NEED_LOGIN"
    assert any("NEED_LOGIN" in w for w in data["recommendation"]["warnings"])
    assert data["recommendation"]["primary_agent_for_code"] != "cursor"


def test_authenticated_cursor_with_fleet_burn_and_empty_codexbar(monkeypatch, tmp_path):
    _configure_base(monkeypatch, tmp_path)
    monkeypatch.setattr(
        state_router,
        "get_cursor_lane_usage",
        lambda **kwargs: {
            "lane": "cursor",
            "login_state": "authenticated",
            "probe_state": "healthy",
            "status": "cool",
            "primary_used_pct": 8.0,
            "provider_windows": {
                "auto": {
                    "window": "monthly",
                    "used_pct": 8.0,
                    "remaining_pct": 92.0,
                    "resets_at": "2026-09-01T00:00:00Z",
                },
                "api": {
                    "window": "monthly",
                    "used_pct": 12.0,
                    "remaining_pct": 88.0,
                    "resets_at": "2026-09-01T00:00:00Z",
                },
            },
            "weekly_resets_at": "2026-09-01T00:00:00Z",
            "source": "cursor_native",
        },
    )

    def _fleet(agent: str, **kwargs) -> dict:
        total = 3 if agent == "cursor" else 0
        return {
            "source": "agent_runtime_jsonl",
            "agent": agent,
            "windows": {
                "5h": {"counts": {"total": total}, "hours": 0.5},
                "7d": {"counts": {"total": total}, "hours": 1.0},
                "30d": {"counts": {"total": total}, "hours": 2.0},
            },
        }

    monkeypatch.setattr(state_router, "summarize_fleet_burn", _fleet)

    data = state_router.compute_routing_budget(datetime(2026, 8, 26, 12, 0, tzinfo=UTC))
    cursor = data["agents"]["cursor"]
    assert cursor["fleet_burn"]["windows"]["7d"]["counts"]["total"] == 3
    assert cursor["provider_windows"]["auto"]["window"] == "monthly"
    assert cursor["provider_windows"]["api"]["window"] == "monthly"
    assert "5h" not in cursor["provider_windows"]
    assert data["recommendation"]["primary_agent_for_code"] == "cursor"


def test_need_probe_with_fleet_burn_still_picks_cursor(monkeypatch, tmp_path):
    """NEED_PROBE + JSONL activity must not leave cursor unknown / unpicked."""
    _configure_base(monkeypatch, tmp_path)
    monkeypatch.setattr(
        state_router,
        "get_cursor_lane_usage",
        lambda **kwargs: {
            "lane": "cursor",
            "login_state": "authenticated",
            "probe_state": "NEED_PROBE",
            "status": "unknown",
            "provider_windows": {
                "auto": {"window": "monthly", "used_pct": None, "remaining_pct": None, "resets_at": None},
                "api": {"window": "monthly", "used_pct": None, "remaining_pct": None, "resets_at": None},
            },
            "source": "cursor_native",
        },
    )

    def _fleet(agent: str, **kwargs) -> dict:
        total = 4 if agent == "cursor" else 0
        return {
            "source": "agent_runtime_jsonl",
            "agent": agent,
            "windows": {"7d": {"counts": {"total": total}, "hours": 1.0}},
        }

    monkeypatch.setattr(state_router, "summarize_fleet_burn", _fleet)
    data = state_router.compute_routing_budget(datetime(2026, 8, 26, 12, 0, tzinfo=UTC))
    cursor = data["agents"]["cursor"]
    assert cursor["status"] == "cool"
    assert cursor["probe_state"] == "NEED_PROBE"
    assert cursor["fleet_burn"]["windows"]["7d"]["counts"]["total"] == 4
    assert data["recommendation"]["primary_agent_for_code"] == "cursor"


def test_capacity_pick_orders_cursor_before_agy_when_cool(monkeypatch):
    budget = {
        "generated_at": "2026-08-26T12:00:00Z",
        "agents": {
            "cursor": {
                "status": "cool",
                "login_state": "authenticated",
                "remaining_pct": 92.0,
                "burn_pct_7d": 8.0,
                "provider_windows": {
                    "auto": {"remaining_pct": 92.0, "used_pct": 8.0},
                },
                "fleet_burn": {"windows": {"7d": {"counts": {"total": 2}}}},
            },
            "agy": {"status": "cool", "remaining_pct": 85.0, "burn_pct_7d": 15.0},
            "codex": {"status": "hot", "remaining_pct": 20.0, "burn_pct_7d": 80.0},
        },
        "in_flight": {},
        "recommendation": {"primary_agent_for_code": "cursor", "rationale": "", "warnings": []},
        "diagnostics": {},
    }
    report = capacity_pick.build_report(budget)
    ranked = [p for p in report["pick_order"] if p["pick"] != "AVOID"]
    assert ranked[0]["lane"] == "cursor"
    assert ranked[1]["lane"] == "agy"


def test_capacity_pick_marks_logout_cursor_avoid(monkeypatch):
    budget = {
        "generated_at": "2026-08-26T12:00:00Z",
        "agents": {
            "cursor": {
                "status": "need_login",
                "login_state": "NEED_LOGIN",
                "probe_state": "NEED_LOGIN",
            },
            "agy": {"status": "cool", "remaining_pct": 85.0},
        },
        "in_flight": {},
        "recommendation": {"primary_agent_for_code": "agy", "rationale": "", "warnings": []},
        "diagnostics": {},
    }
    rows = {r["lane"]: r for r in capacity_pick.build_lane_rows(budget)}
    assert rows["cursor"]["avoid"] is True
    assert "NEED_LOGIN" in rows["cursor"]["notes"]
