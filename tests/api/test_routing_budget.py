"""Cursor subscription / routing-budget acceptance tests."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from scripts.api import state_router
from scripts.fleet import capacity_pick, credit_lane

# Captured at import, before the conftest autouse fixture stubs the reader.
REAL_RATE_LIMIT_READER = credit_lane.read_recent_rate_limits


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


def _configure_base(monkeypatch, tmp_path: Path) -> Path:
    budget_path = _write_budget_config(tmp_path)
    (tmp_path / "tasks").mkdir(exist_ok=True)
    (tmp_path / "api_usage").mkdir(exist_ok=True)
    monkeypatch.setattr(state_router, "load_cost_records", lambda **_kwargs: [])
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
        lambda agent, **_kwargs: {
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
    _budget_path = _configure_base(monkeypatch, tmp_path)
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

    data = state_router.compute_routing_budget(datetime(2026, 8, 26, 12, 0, tzinfo=UTC), budget_config_path=_budget_path, tasks_dir=tmp_path / "tasks", project_root=tmp_path, curriculum_root=tmp_path, batch_state_dir=tmp_path)
    cursor = data["agents"]["cursor"]
    assert cursor["status"] == "need_login"
    assert cursor["login_state"] == "NEED_LOGIN"
    assert any("NEED_LOGIN" in w for w in data["recommendation"]["warnings"])
    assert data["recommendation"]["primary_agent_for_code"] != "cursor"


def test_authenticated_cursor_with_fleet_burn_and_empty_codexbar(monkeypatch, tmp_path):
    _budget_path = _configure_base(monkeypatch, tmp_path)
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

    data = state_router.compute_routing_budget(datetime(2026, 8, 26, 12, 0, tzinfo=UTC), budget_config_path=_budget_path, tasks_dir=tmp_path / "tasks", project_root=tmp_path, curriculum_root=tmp_path, batch_state_dir=tmp_path)
    cursor = data["agents"]["cursor"]
    assert cursor["fleet_burn"]["windows"]["7d"]["counts"]["total"] == 3
    assert cursor["provider_windows"]["auto"]["window"] == "monthly"
    assert cursor["provider_windows"]["api"]["window"] == "monthly"
    assert "5h" not in cursor["provider_windows"]
    assert data["recommendation"]["primary_agent_for_code"] == "cursor"


def test_need_probe_with_fleet_burn_still_picks_cursor(monkeypatch, tmp_path):
    """NEED_PROBE + JSONL activity must not leave cursor unknown / unpicked."""
    _budget_path = _configure_base(monkeypatch, tmp_path)
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
    data = state_router.compute_routing_budget(datetime(2026, 8, 26, 12, 0, tzinfo=UTC), budget_config_path=_budget_path, tasks_dir=tmp_path / "tasks", project_root=tmp_path, curriculum_root=tmp_path, batch_state_dir=tmp_path)
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


def test_in_flight_excludes_zombie_running_tasks(tmp_path: Path, monkeypatch) -> None:
    """Context-scoped in-flight counts must match active_delegate_tasks liveness."""
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    dead_pid = 2_147_000_001
    monkeypatch.setattr(
        state_router.delegate_api,
        "_pid_alive",
        lambda pid: int(pid) != dead_pid,
    )
    (tasks / "live.json").write_text(
        '{"task_id":"live","agent":"codex","status":"running","pid":12345}',
        encoding="utf-8",
    )
    (tasks / "zombie.json").write_text(
        f'{{"task_id":"zombie","agent":"codex","status":"running","pid":{dead_pid}}}',
        encoding="utf-8",
    )
    counts = state_router._in_flight_by_agent(tasks)
    assert counts["codex"] == 1


def test_prepaid_thresholds_currency_and_account_cap(monkeypatch, tmp_path):
    path = tmp_path / "budgets.yaml"
    path.write_text("deepseek:\n  near_cap_usd: 10\n  warm_usd: 40\nopenrouter:\n  near_cap_usd: 10\n  warm_usd: 40\n")
    budgets, _ = state_router._load_agent_budgets(path)
    account = {"probe_state": "ok", "freshness": "fresh", "age_s": 0, "currency": "USD", "total_balance": 8}
    assert state_router._api_lane_status_from_account("deepseek", account, budgets) == "near_cap"
    assert state_router._api_lane_status_from_account("deepseek", {**account, "total_balance": 30}, budgets) == "warm"
    assert state_router._api_lane_status_from_account("deepseek", {**account, "total_balance": 40}, budgets) == "cool"
    assert state_router._api_lane_status_from_account("deepseek", {**account, "currency": "CNY"}, budgets) == "unknown"
    router = {**account, "limit_remaining_usd": 80, "account_remaining_usd": 0}
    assert state_router._api_lane_status_from_account("openrouter", router, budgets) == "near_cap"
    router.update(limit_remaining_usd=0, account_remaining_usd=80)
    assert state_router._api_lane_status_from_account("openrouter", router, budgets) == "near_cap"


def test_prepaid_in_flight_and_ranked_entries(monkeypatch, tmp_path):
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    for index, agent in enumerate(("deepseek", "deepseek", "pool", "grok-build")):
        (tasks / f"task{index}.json").write_text(json.dumps({"agent": agent, "status": "spawning"}))
    counts = state_router._in_flight_by_agent(tasks)
    assert counts["deepseek"] == 2
    assert counts["pool"] == 1
    assert counts["grok"] == 1
    ranked = state_router._ranked_api_entries({"deepseek": {
        "probe_state": "ok", "freshness": "fresh", "age_s": 0, "currency": "USD", "total_balance": 30,
    }}, {}, counts)
    row = next(row for row in ranked if row["lane"] == "deepseek")
    assert row["in_flight"] == 2
    assert row["remaining_pct"] is None and row["burn_pct_7d"] is None


def test_subscription_need_login_reaches_capacity_pick(monkeypatch, tmp_path):
    config = _configure_base(monkeypatch, tmp_path)
    monkeypatch.setattr(state_router, "get_provider_usage_data", lambda lane: {
        "freshness": "unavailable", "error_kind": "need_login", "status": "unavailable",
    })
    budget = state_router.compute_routing_budget(
        budget_config_path=config, tasks_dir=tmp_path / "tasks",
        project_root=tmp_path, curriculum_root=tmp_path, batch_state_dir=tmp_path,
    )
    rows = {row["lane"]: row for row in capacity_pick.build_lane_rows(budget)}
    for lane in ("claude", "codex", "kimi", "grok"):
        assert budget["agents"][lane]["probe_state"] == "NEED_LOGIN"
        assert rows[lane]["avoid"] is True


# --- #9517: near-cap lanes with a credit balance ----------------------------

_CREDIT_NOW = datetime(2026, 10, 2, 17, 0, tzinfo=UTC)


def _credit_budget(
    monkeypatch, tmp_path, *, codex_balance=62500.0, claude_used=95.0, default_batch_state=False
) -> dict:
    """routing-budget with Codex 99% used plus ``codex_balance`` credits and Claude at ``claude_used``%.

    ``default_batch_state`` omits ``batch_state_dir`` so the producer resolves its own default.
    """
    budget_path = _write_budget_config(tmp_path)
    _configure_base(monkeypatch, tmp_path)
    fetched_at = "2026-10-02T16:59:00Z"

    def usage(provider):
        if provider == "codex":
            return {
                "lane": "codex",
                "weekly_used_pct": 99.0,
                "weekly_remaining_pct": 1.0,
                "credit_balance": codex_balance,
                "freshness": "fresh",
                "age_s": 60.0,
                "stale": False,
                "fetched_at": fetched_at,
                "source": "codexbar",
            }
        if provider == "claude":
            return {
                "lane": "claude",
                "weekly_used_pct": claude_used,
                "weekly_remaining_pct": 100.0 - claude_used,
                "freshness": "fresh",
                "age_s": 60.0,
                "stale": False,
                "fetched_at": fetched_at,
                "source": "codexbar",
            }
        return {"lane": provider, "weekly_used_pct": None, "status": "unknown", "source": "codexbar"}

    monkeypatch.setattr(state_router, "get_provider_usage_data", usage)
    monkeypatch.setattr(
        state_router, "get_cursor_lane_usage", lambda **_kwargs: {"lane": "cursor", "status": "unknown"}
    )
    monkeypatch.setattr(
        state_router,
        "summarize_fleet_burn",
        lambda agent, **_kwargs: {"source": "agent_runtime_jsonl", "agent": agent, "windows": {}},
    )
    return state_router.compute_routing_budget(
        _CREDIT_NOW,
        budget_config_path=budget_path,
        tasks_dir=tmp_path / "tasks",
        project_root=tmp_path,
        curriculum_root=tmp_path,
        **({} if default_batch_state else {"batch_state_dir": tmp_path}),
    )


def test_near_cap_codex_with_credits_is_recommended_when_no_plan_backed_seat_remains(monkeypatch, tmp_path):
    data = _credit_budget(monkeypatch, tmp_path)
    codex = data["agents"]["codex"]
    assert codex["status"] == "near_cap"  # raw quota vocabulary unchanged
    assert codex["credit"]["state"] == "credit_balance_present"
    assert codex["credit"]["evidence"]["credit_balance"] == 62500.0
    assert data["agents"]["claude"]["credit"] == {"state": "not_configured"}
    rec = data["recommendation"]
    assert rec["primary_agent_for_code"] == "codex"
    assert "draw not verified by the router" in rec["rationale"]
    assert "gpt-6.1-sol, gpt-6-luna" in rec["rationale"]
    assert any(
        w.startswith("recommendation 'codex' is past its plan cap") and "credit-period allowlist" in w
        for w in rec["warnings"]
    )

    # capacity_pick keeps that recommendation instead of suppressing it as AVOID.
    report = capacity_pick.build_report(
        data, active_in_flight={}, admission={"line": "admission: test"}, now=_CREDIT_NOW
    )
    assert report["recommendation"]["primary_agent_for_code"] == "codex"


def test_plan_backed_warm_seat_still_precedes_credit_lane(monkeypatch, tmp_path):
    data = _credit_budget(monkeypatch, tmp_path, claude_used=60.0)
    assert data["agents"]["codex"]["credit"]["state"] == "credit_balance_present"
    assert data["recommendation"]["primary_agent_for_code"] == "claude"


@pytest.mark.parametrize(
    ("balance", "state"),
    [(0.0, "credits_exhausted"), (None, "credits_unverified")],
    ids=["exhausted", "missing"],
)
def test_near_cap_codex_without_usable_credits_is_unchanged(monkeypatch, tmp_path, balance, state):
    data = _credit_budget(monkeypatch, tmp_path, codex_balance=balance)
    assert data["agents"]["codex"]["status"] == "near_cap"
    assert data["agents"]["codex"]["credit"]["state"] == state
    assert data["recommendation"]["primary_agent_for_code"] == "inline_orchestrator"


def test_recent_rate_limit_keeps_the_credit_lane_out(monkeypatch, tmp_path):
    from scripts.fleet import credit_lane

    monkeypatch.setattr(
        credit_lane,
        "read_recent_rate_limits",
        lambda *_a, **_k: {"count": 1, "last_rate_limited_at": "2026-10-02T16:40:00Z"},
    )
    data = _credit_budget(monkeypatch, tmp_path)
    assert data["agents"]["codex"]["credit"]["state"] == "credit_use_unconfirmed"
    assert data["recommendation"]["primary_agent_for_code"] == "inline_orchestrator"


def test_worktree_caller_reads_rate_limits_from_the_shared_runtime_log(monkeypatch, tmp_path):
    """A linked-worktree caller without ``batch_state_dir`` sees the shared checkout's rate limits."""
    from scripts.agent_runtime import usage

    usage._reset_rate_limit_cache_for_tests()
    monkeypatch.setattr(credit_lane, "read_recent_rate_limits", REAL_RATE_LIMIT_READER)
    shared_root = tmp_path / "primary"
    shared_usage = shared_root / "batch_state" / "api_usage"
    shared_usage.mkdir(parents=True)
    (shared_usage / "usage_codex-delegate_2026-10-02.jsonl").write_text(
        json.dumps({"ts": "2026-10-02T16:50:00Z", "outcome": "rate_limited"}) + "\n", encoding="utf-8"
    )
    source_root = Path(state_router.__file__).resolve().parents[2]
    resolved: list[Path] = []

    def shared_checkout(root: Path) -> Path:
        resolved.append(root)
        return shared_root

    monkeypatch.setattr(state_router, "main_checkout_root", shared_checkout)
    monkeypatch.setattr(usage, "_usage_dir", lambda: shared_usage)

    data = _credit_budget(monkeypatch, tmp_path, default_batch_state=True)
    codex = data["agents"]["codex"]
    assert codex["credit"]["state"] == "credit_use_unconfirmed"
    assert codex["credit"]["evidence"]["rate_limited_count"] == 1
    assert resolved == [source_root]
    assert data["recommendation"]["primary_agent_for_code"] == "inline_orchestrator"

    # An explicit batch_state_dir still overrides the shared default.
    explicit = _credit_budget(monkeypatch, tmp_path)
    assert explicit["agents"]["codex"]["credit"]["state"] == "credit_balance_present"


def test_unreadable_credit_policy_publishes_policy_error_and_keeps_near_cap(monkeypatch, tmp_path):
    from scripts.fleet import credit_lane

    def broken(path=None):
        raise ValueError("unreadable")

    monkeypatch.setattr(credit_lane, "load_policy", broken)
    data = _credit_budget(monkeypatch, tmp_path)
    assert data["agents"]["codex"]["credit"]["state"] == "policy_error"
    assert data["agents"]["claude"]["credit"] == {"state": "not_configured"}
    assert data["recommendation"]["primary_agent_for_code"] == "inline_orchestrator"


def test_need_login_credit_lane_is_not_credit_backed():
    present = {"state": "credit_balance_present", "allowed_models": ["gpt-6.1-sol"]}
    assert state_router._credit_backed({"credit": present}) is True
    assert state_router._credit_backed({"credit": present, "probe_state": "NEED_LOGIN"}) is False
    assert state_router._credit_backed({"credit": {"state": "credits_exhausted"}}) is False
    assert state_router._credit_backed(None) is False
