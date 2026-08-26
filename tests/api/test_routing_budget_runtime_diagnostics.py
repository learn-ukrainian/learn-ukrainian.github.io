"""Tests for routing-budget runtime-usage diagnostics honesty (#7085).

The USD cost ledger can be empty while ``/api/runtime/usage`` serves rows.
``diagnostics.runtime_data_available`` must reflect the same 7-day runtime
usage, and the ledger-empty state must be stated, not read as "no data".
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from scripts.api import state_router


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


def _empty_runtime(agent: str) -> dict:
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


def _configure(
    monkeypatch,
    tmp_path: Path,
    *,
    runtime_records_7d: int,
) -> None:
    """Empty USD ledger, quiet 5-minute reactive window, no CodexBar data."""
    monkeypatch.setattr(state_router, "BUDGET_CONFIG_PATH", _write_budget_config(tmp_path))
    monkeypatch.setattr(state_router, "load_cost_records", lambda: [])
    monkeypatch.setattr(state_router, "get_provider_usage_data", _no_codexbar)
    monkeypatch.setattr(
        state_router,
        "get_cursor_lane_usage",
        lambda **kwargs: {
            "lane": "cursor",
            "login_state": "authenticated",
            "probe_state": "NEED_PROBE",
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
    monkeypatch.setattr(state_router, "summarize_lane_runtime", _empty_runtime)
    monkeypatch.setattr(
        state_router,
        "summarize_runtime_usage",
        lambda *, days=7, agent=None, entrypoint=None: {
            "window_days": days,
            "records_total": runtime_records_7d,
            "by_agent": {},
            "by_entrypoint": {},
        },
    )
    monkeypatch.setattr(
        state_router.delegate_api,
        "list_delegate_tasks",
        lambda **_kwargs: {"tasks": []},
    )


def test_runtime_data_available_when_7d_usage_exists_but_ledger_empty(monkeypatch, tmp_path):
    """Acceptance fixture: /api/runtime/usage has rows, USD ledger is empty."""
    now = datetime(2026, 8, 22, 12, 0, tzinfo=UTC)
    _configure(monkeypatch, tmp_path, runtime_records_7d=25)

    data = state_router.compute_routing_budget(now)

    diag = data["diagnostics"]
    assert diag["records_loaded"] == 0
    assert diag["budget_ledger_empty"] is True
    assert diag["runtime_data_available"] is True
    assert diag["runtime_usage_records_7d"] == 25
    assert any("ledger empty" in w and "runtime usage" in w for w in data["recommendation"]["warnings"])


def test_runtime_data_unavailable_when_no_usage_anywhere(monkeypatch, tmp_path):
    now = datetime(2026, 8, 22, 12, 0, tzinfo=UTC)
    _configure(monkeypatch, tmp_path, runtime_records_7d=0)

    data = state_router.compute_routing_budget(now)

    diag = data["diagnostics"]
    assert diag["budget_ledger_empty"] is True
    assert diag["runtime_data_available"] is False
    assert diag["runtime_usage_records_7d"] == 0
    assert not any("runtime usage has" in w for w in data["recommendation"]["warnings"])


def test_runtime_probe_failure_degrades_without_breaking_budget(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path, runtime_records_7d=0)

    def _boom(**_kwargs):
        raise OSError("usage dir unreadable")

    monkeypatch.setattr(state_router, "summarize_runtime_usage", _boom)

    data = state_router.compute_routing_budget(datetime(2026, 8, 22, 12, 0, tzinfo=UTC))

    diag = data["diagnostics"]
    assert diag["runtime_data_available"] is False
    assert diag["runtime_usage_records_7d"] is None
    assert diag["records_loaded"] == 0


def test_reactive_window_alone_still_marks_runtime_available(monkeypatch, tmp_path):
    """A busy 5-minute window keeps runtime_data_available true even at 0 rows in 7d."""
    _configure(monkeypatch, tmp_path, runtime_records_7d=0)

    def _busy_runtime(agent: str) -> dict:
        base = _empty_runtime(agent)
        base.update({"ok": 2, "total": 2})
        return base

    monkeypatch.setattr(state_router, "summarize_lane_runtime", _busy_runtime)

    data = state_router.compute_routing_budget(datetime(2026, 8, 22, 12, 0, tzinfo=UTC))

    assert data["diagnostics"]["runtime_data_available"] is True


def test_empty_ledger_rec_stays_suppressed_when_runtime_exists(monkeypatch, tmp_path):
    """Runtime usage is not an authoritative burn source: with ledger and
    CodexBar both empty, the primary recommendation stays suppressed."""
    now = datetime(2026, 8, 22, 12, 0, tzinfo=UTC)
    _configure(monkeypatch, tmp_path, runtime_records_7d=25)

    data = state_router.compute_routing_budget(now)

    assert data["recommendation"]["primary_agent_for_code"] is None
    for lane in ("claude", "codex"):
        agent = data["agents"][lane]
        status = agent.get("status") or agent.get("interactive", {}).get("status")
        assert status in ("unknown", "unavailable"), f"{lane} must stay unknown on empty ledger"


def test_routing_html_states_ledger_empty_when_runtime_usage_exists():
    """dashboards/routing.html must say "ledger empty, runtime exists" — not a silent $0 week."""
    import subprocess

    script = """
    const fs = require('fs');
    const html = fs.readFileSync('dashboards/routing.html', 'utf8');
    const renderBudgetMatch = html.match(/function renderBudget\\(routing, usage\\) \\{[\\s\\S]*?\\n\\}/);
    if (!renderBudgetMatch) throw new Error('renderBudget not found');

    const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, ch => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[ch]));
    const pct = (value) => {
      const num = Number(value);
      return Number.isFinite(num) ? Math.max(0, Math.min(100, num)) : 0;
    };
    const statusPill = (status) => `<span class="pill ${escapeHtml(status)}">${escapeHtml(status)}</span>`;

    let innerHTML = '';
    const document = {
      getElementById: (id) => ({ set innerHTML(val) { innerHTML = val; } })
    };

    eval(renderBudgetMatch[0]);

    const routing = {
      agents: {
        codex: { status: 'unknown', burn_pct_7d: null, remaining_pct: null, weekly_cap_usd: 1000 }
      },
      in_flight: {},
      diagnostics: { records_loaded: 0, budget_ledger_empty: true, runtime_usage_records_7d: 25 }
    };
    renderBudget(routing, { records_total: 25 });
    console.log(innerHTML);
    """
    res = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True, timeout=30)
    out = res.stdout
    assert "budget ledger is empty" in out, f"missing ledger-empty note: {out}"
    assert "Runtime usage exists (25 call(s) in 7d)" in out, f"missing runtime-exists copy: {out}"
    assert "Burn unknown — USD budget ledger empty" in out, f"missing honest bar title: {out}"
