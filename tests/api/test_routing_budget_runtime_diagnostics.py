"""Tests for routing-budget runtime-usage diagnostics honesty (#7085).

The USD cost ledger can be empty while ``/api/runtime/usage`` serves rows.
``diagnostics.runtime_data_available`` must reflect the same 7-day runtime
usage, and the ledger-empty state must be stated, not read as "no data".
"""

from __future__ import annotations

import json
import os
import time
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

from scripts.agent_runtime import usage as usage_mod
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
    budget_path = _write_budget_config(tmp_path)
    monkeypatch.setattr(
        state_router,
        "_load_agent_budgets",
        lambda budget_config_path=None, **_: state_router._read_agent_budgets_file(budget_path),
    )
    monkeypatch.setattr(state_router, "load_cost_records", lambda **_kwargs: [])
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
    monkeypatch.setattr(
        state_router,
        "summarize_fleet_burn",
        lambda agent, **kwargs: {
            "source": "agent_runtime_jsonl",
            "agent": agent,
            "windows": {"7d": {"counts": {"total": 0}, "hours": 0.0}},
        },
    )
    monkeypatch.setattr(state_router, "summarize_lane_runtime", _empty_runtime)
    monkeypatch.setattr(
        state_router,
        "summarize_runtime_usage",
        lambda *, days=7, agent=None, entrypoint=None, usage_dir=None: {
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

    def _busy_runtime(agent: str, **_kwargs) -> dict:
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


def test_routing_html_subscriptions_renders_cursor_windows_without_fabricating_zero():
    """Subscriptions section shows provider windows; missing data is unknown, not 0%."""
    import subprocess

    script = """
    const fs = require('fs');
    const html = fs.readFileSync('dashboards/routing.html', 'utf8');
    const start = html.indexOf('function escapeHtml');
    const end = html.indexOf('function renderAgents');
    if (start < 0 || end < 0) throw new Error('subscription render helpers not found');
    const helpers = html.slice(start, end);

    let innerHTML = '';
    const document = {
      getElementById: (id) => ({ set innerHTML(val) { innerHTML = val; } })
    };
    eval(helpers);

    renderSubscriptions({
      agents: {
        cursor: {
          status: 'unknown',
          login_state: 'authenticated',
          probe_state: 'NEED_PROBE',
          provider_windows: {
            auto: { window: 'monthly', used_pct: null, remaining_pct: null },
            api: { window: 'monthly', used_pct: null, remaining_pct: null },
          },
        },
        codex: { status: 'unknown', burn_pct_7d: null, codexbar: { weekly_used_pct: null } },
      },
      in_flight: {},
      diagnostics: { records_loaded: 0, budget_ledger_empty: true, runtime_usage_records_7d: 25 }
    });
    console.log(innerHTML);
    """
    res = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True, timeout=30)
    out = res.stdout
    assert "NEED_PROBE" in out or "unknown" in out
    assert "0.0%" not in out
    assert "Fleet burn" in out or "5h:" in out


def _stamp(now: float, age_s: float, *, utc: bool = True) -> str:
    moment = datetime.fromtimestamp(now - age_s, tz=UTC).replace(microsecond=0)
    if utc:
        return moment.strftime("%Y-%m-%dT%H:%M:%SZ")
    return moment.astimezone(timezone(timedelta(hours=2))).isoformat()


def _usage_corrupt_line(kind: str, now: float) -> bytes:
    """One bad usage line. The in-string kind is JSON except for byte 0xFF."""
    if kind == "json-non-object":
        return b"[]\n"
    if kind == "invalid-utf8":
        return b"\xff\n"
    if kind == "invalid-utf8-in-string":
        payload = json.dumps(
            {
                "ts": _stamp(now, 45),
                "outcome": "ok",
                "duration_s": 10,
                "model": "MODEL_TOKEN",
            }
        ).encode("ascii")
        return payload.replace(b"MODEL_TOKEN", b"gemini-\xff") + b"\n"
    raise AssertionError(kind)


def _append(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


def _available_quota(provider: str) -> dict:
    resets = (datetime.now(UTC) + timedelta(days=6)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "lane": provider,
        "primary_used_pct": 12.0,
        "weekly_used_pct": 12.0,
        "primary_remaining_pct": 88.0,
        "weekly_remaining_pct": 88.0,
        "weekly_resets_at": resets,
        "will_last_to_reset": True,
        "source": "codexbar",
        "fetched_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "stale": False,
        "age_s": 1,
        "freshness": "fresh",
        "status": "cool",
    }


def test_gemini_subscription_row_counts_agy_activity_and_keeps_faults(monkeypatch, tmp_path):
    """API row for Gemini shows AGY plus legacy rows once, faults included, controls unchanged."""
    usage_mod._reset_rate_limit_cache_for_tests()
    now = time.time()
    day = datetime.fromtimestamp(now, tz=UTC).strftime("%Y-%m-%d")
    batch = tmp_path / "batch_state"
    usage = batch / "api_usage"
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    agy = usage / f"usage_agy-dispatch_{day}.jsonl"
    gemini = usage / f"usage_gemini-dispatch_{day}.jsonl"
    for record in (
        {"ts": _stamp(now, 30), "outcome": "ok"},
        {"ts": _stamp(now, 25), "outcome": "error"},
        {"ts": _stamp(now, 40), "outcome": "timeout"},
        {"ts": _stamp(now, 35), "outcome": "cancelled"},
        {
            "ts": _stamp(now, 10),
            "outcome": "rate_limited",
            "model": "gemini-3.8-flash-high",
            "duration_s": 3600,
        },
        {"ts": _stamp(now, 6 * 3600 + 30), "outcome": "ok"},
    ):
        _append(agy, record)
    _append(
        gemini,
        {
            "ts": _stamp(now, 20, utc=False),
            "outcome": "rate_limited",
            "model": "gemini-3.5-flash",
            "duration_s": 1800,
        },
    )
    _append(gemini, {"ts": _stamp(now, 10 * 86400 + 30), "outcome": "error"})
    _append(gemini, {"ts": _stamp(now, 40 * 86400), "outcome": "timeout"})
    with gemini.open("a", encoding="utf-8") as handle:
        handle.write("{not-json\n")
    os.link(gemini, usage / f"usage_agy-alias_{day}.jsonl")
    missing = usage / "missing-usage.jsonl"
    for name in ("agy", "gemini"):
        (usage / f"usage_{name}-missing_{day}.jsonl").symlink_to(missing)
    stale = usage / f"usage_gemini-stale_{day}.jsonl"
    _append(stale, {"ts": _stamp(now, 40 * 86400), "outcome": "rate_limited", "model": "stale-hidden"})
    os.utime(stale, (now - 40 * 86400, now - 40 * 86400))
    _append(usage / f"usage_codex-bridge_{day}.jsonl", {"ts": _stamp(now, 15), "outcome": "ok", "duration_s": 1800})
    _append(usage / f"usage_claude-bridge_{day}.jsonl", {"ts": _stamp(now, 15), "outcome": "error"})
    _append(usage / f"usage_grok-bridge_{day}.jsonl", {"ts": _stamp(now, 15), "outcome": "timeout"})
    _append(usage / f"usage_glm-bridge_{day}.jsonl", {"ts": _stamp(now, 15), "outcome": "ok"})

    budget_path = _write_budget_config(tmp_path)
    monkeypatch.setattr(state_router, "load_cost_records", lambda **_kwargs: [])
    monkeypatch.setattr(state_router, "get_provider_usage_data", _available_quota)
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

    data = state_router.compute_routing_budget(
        datetime.now(UTC),
        budget_config_path=budget_path,
        tasks_dir=tasks,
        batch_state_dir=batch,
    )

    assert "agy" not in data["agents"]
    gemini_row = data["agents"]["gemini"]
    runtime = gemini_row["runtime"]
    assert runtime["ok"] == 1
    assert runtime["error"] == 1
    assert runtime["timeout"] == 1
    assert runtime["other"] == 1
    assert runtime["rate_limited"] == 2
    assert runtime["total"] == 6
    assert runtime["models_rate_limited"] == ["gemini-3.5-flash", "gemini-3.8-flash-high"]
    assert runtime["headroom_blocked"] is True
    assert runtime["unreadable"] == {"files": 1, "lines": 1, "records": 1, "total": 3}
    assert gemini_row["codexbar"]["weekly_used_pct"] == 12.0
    assert gemini_row["codexbar"]["weekly_remaining_pct"] == 88.0
    assert gemini_row["status"] == "hot"
    assert any("lane gemini" in warning and "rate_limited" in warning for warning in data["recommendation"]["warnings"])

    burn = gemini_row["fleet_burn"]
    assert burn["agent"] == "gemini"
    assert burn["windows"]["5h"]["counts"] == {
        "ok": 1,
        "error": 1,
        "rate_limited": 2,
        "timeout": 1,
        "other": 1,
        "total": 6,
    }
    assert burn["windows"]["5h"]["hours"] == 1.5
    assert burn["windows"]["7d"]["counts"]["ok"] == 2
    assert burn["windows"]["7d"]["counts"]["total"] == 7
    assert burn["windows"]["30d"]["counts"]["error"] == 2
    assert burn["windows"]["30d"]["counts"]["total"] == 8
    assert burn["unreadable"] == {"files": 1, "lines": 1, "records": 0, "total": 2}

    codex = data["agents"]["codex"]
    claude = data["agents"]["claude"]
    grok = data["agents"]["grok"]
    assert (codex["runtime"]["ok"], codex["runtime"]["total"], codex["runtime"]["rate_limited"]) == (1, 1, 0)
    assert codex["runtime"]["unreadable"]["total"] == 0
    assert codex["fleet_burn"]["windows"]["5h"]["counts"]["total"] == 1
    assert codex["fleet_burn"]["windows"]["5h"]["hours"] == 0.5
    assert codex["status"] == "cool"
    assert (claude["runtime"]["error"], claude["runtime"]["total"]) == (1, 1)
    assert claude["fleet_burn"]["windows"]["7d"]["counts"]["total"] == 1
    assert (grok["runtime"]["timeout"], grok["runtime"]["total"]) == (1, 1)
    assert grok["fleet_burn"]["windows"]["30d"]["counts"]["total"] == 1
    assert data["agents"]["cursor"]["runtime"]["total"] == 0
    assert data["agents"]["kimi"]["runtime"]["total"] == 0


@pytest.mark.parametrize(
    "corrupt_kind",
    ["json-non-object", "invalid-utf8", "invalid-utf8-in-string"],
)
def test_gemini_api_row_keeps_burn_when_agy_evidence_is_corrupt(monkeypatch, tmp_path, corrupt_kind):
    """The Gemini routing-budget row keeps 5h/7d/30d hours when AGY evidence is corrupt.

    A JSON non-object, a standalone invalid byte, or an invalid byte inside a
    JSON string is one unreadable line. Replacement decoding would count the
    third as an extra runtime ok.
    """
    usage_mod._reset_rate_limit_cache_for_tests()
    now = time.time()
    corrupt_line = _usage_corrupt_line(corrupt_kind, now)
    if corrupt_kind == "invalid-utf8-in-string":
        replaced = json.loads(corrupt_line.decode("utf-8", errors="replace"))
        assert replaced["outcome"] == "ok"
        assert replaced["model"] == "gemini-\ufffd"
        with pytest.raises(UnicodeDecodeError):
            corrupt_line.decode("utf-8", errors="strict")
    day = datetime.fromtimestamp(now, tz=UTC).strftime("%Y-%m-%d")
    batch = tmp_path / "batch_state"
    usage = batch / "api_usage"
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    agy = usage / f"usage_agy-dispatch_{day}.jsonl"
    gemini = usage / f"usage_gemini-dispatch_{day}.jsonl"
    _append(agy, {"ts": _stamp(now, 60), "outcome": "ok", "duration_s": 3600})
    with agy.open("ab") as handle:
        handle.write(b"\n")
        handle.write(corrupt_line)
        handle.write(b"\n")
    _append(agy, {"ts": _stamp(now, 6 * 3600 + 60), "outcome": "ok", "duration_s": 7200})
    _append(
        gemini,
        {
            "ts": _stamp(now, 30),
            "outcome": "rate_limited",
            "duration_s": 1800,
            "model": "gemini-3.8-flash-high",
        },
    )
    _append(gemini, {"ts": _stamp(now, 10 * 86400 + 60), "outcome": "error", "duration_s": 3600})
    os.link(gemini, usage / f"usage_agy-alias_{day}.jsonl")
    (usage / f"usage_agy-dir_{day}.jsonl").mkdir()
    missing = usage / "missing-usage.jsonl"
    for name in ("agy", "gemini"):
        (usage / f"usage_{name}-missing_{day}.jsonl").symlink_to(missing)
    codex_path = usage / f"usage_codex-bridge_{day}.jsonl"
    _append(codex_path, {"ts": _stamp(now, 15), "outcome": "ok", "duration_s": 1800})
    with codex_path.open("ab") as handle:
        handle.write(b"[]\n")
    _append(usage / f"usage_claude-bridge_{day}.jsonl", {"ts": _stamp(now, 3 * 86400), "outcome": "error"})
    _append(usage / f"usage_glm-bridge_{day}.jsonl", {"ts": _stamp(now, 15), "outcome": "ok", "duration_s": 100000})

    budget_path = _write_budget_config(tmp_path)
    monkeypatch.setattr(state_router, "load_cost_records", lambda **_kwargs: [])
    monkeypatch.setattr(state_router, "get_provider_usage_data", _available_quota)
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

    data = state_router.compute_routing_budget(
        datetime.now(UTC),
        budget_config_path=budget_path,
        tasks_dir=tasks,
        batch_state_dir=batch,
    )

    assert "agy" not in data["agents"]
    gemini_row = data["agents"]["gemini"]
    burn = gemini_row["fleet_burn"]
    direct = usage_mod.summarize_fleet_burn("gemini", usage_dir=usage, now=now)
    agy_direct = usage_mod.summarize_fleet_burn("agy", usage_dir=usage, now=now)
    assert burn["agent"] == "gemini"
    assert burn["windows"]["5h"]["counts"]["total"] == 2
    assert burn["windows"]["5h"]["hours"] == 1.5
    assert burn["windows"]["7d"]["counts"]["total"] == 3
    assert burn["windows"]["7d"]["hours"] == 3.5
    assert burn["windows"]["30d"]["counts"]["error"] == 1
    assert burn["windows"]["30d"]["counts"]["total"] == 4
    assert burn["windows"]["30d"]["hours"] == 4.5
    assert burn["windows"]["5h"]["window_s"] == 5 * 3600
    assert burn["unreadable"] == {"files": 2, "lines": 1, "records": 0, "total": 3}
    assert burn["windows"] == direct["windows"] == agy_direct["windows"]
    assert burn["unreadable"] == direct["unreadable"] == agy_direct["unreadable"]

    runtime = gemini_row["runtime"]
    assert runtime["ok"] == 1
    assert runtime["rate_limited"] == 1
    assert runtime["total"] == 2
    assert runtime["unreadable"] == burn["unreadable"]
    agy_runtime = usage_mod.summarize_lane_runtime("agy", usage_dir=usage, now=now)
    assert agy_runtime["total"] == runtime["total"]
    assert agy_runtime["unreadable"] == runtime["unreadable"]

    codex = data["agents"]["codex"]
    claude = data["agents"]["claude"]
    assert codex["fleet_burn"]["windows"]["5h"]["counts"]["total"] == 1
    assert codex["fleet_burn"]["windows"]["5h"]["hours"] == 0.5
    assert codex["fleet_burn"]["unreadable"] == {"files": 0, "lines": 1, "records": 0, "total": 1}
    assert codex["runtime"]["total"] == 1
    assert codex["runtime"]["unreadable"]["lines"] == 1
    assert claude["fleet_burn"]["windows"]["5h"]["counts"]["total"] == 0
    assert claude["fleet_burn"]["windows"]["7d"]["counts"]["total"] == 1
    assert claude["fleet_burn"]["unreadable"]["total"] == 0
    assert claude["runtime"]["total"] == 0
    assert data["agents"]["cursor"]["fleet_burn"]["windows"]["30d"]["counts"]["total"] == 0
    assert data["agents"]["kimi"]["runtime"]["total"] == 0


def test_gemini_api_row_counts_literal_ufffd_and_refuses_invalid_bytes(monkeypatch, tmp_path):
    """The API Gemini row keeps a real U+FFFD model and drops a 0xFF inside a string."""
    usage_mod._reset_rate_limit_cache_for_tests()
    now = time.time()
    day = datetime.fromtimestamp(now, tz=UTC).strftime("%Y-%m-%d")
    batch = tmp_path / "batch_state"
    usage = batch / "api_usage"
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    agy = usage / f"usage_agy-dispatch_{day}.jsonl"
    gemini = usage / f"usage_gemini-dispatch_{day}.jsonl"
    _append(agy, {"ts": _stamp(now, 60), "outcome": "ok", "duration_s": 3600})
    ufffd_line = (
        json.dumps(
            {
                "ts": _stamp(now, 40),
                "outcome": "rate_limited",
                "duration_s": 1800,
                "model": "gemini-\ufffd",
            },
            ensure_ascii=False,
        )
        + "\n"
    ).encode("utf-8")
    assert b"\xef\xbf\xbd" in ufffd_line and b"\xff" not in ufffd_line
    bad_line = _usage_corrupt_line("invalid-utf8-in-string", now)
    with agy.open("ab") as handle:
        handle.write(ufffd_line)
        handle.write(bad_line)
    _append(agy, {"ts": _stamp(now, 6 * 3600 + 60), "outcome": "timeout", "duration_s": 7200})
    _append(gemini, {"ts": _stamp(now, 10 * 86400 + 60), "outcome": "error", "duration_s": 3600})
    os.link(gemini, usage / f"usage_agy-alias_{day}.jsonl")
    _append(usage / f"usage_codex-bridge_{day}.jsonl", {"ts": _stamp(now, 15), "outcome": "ok", "duration_s": 1800})
    _append(usage / f"usage_claude-bridge_{day}.jsonl", {"ts": _stamp(now, 3 * 86400), "outcome": "error"})

    budget_path = _write_budget_config(tmp_path)
    monkeypatch.setattr(state_router, "load_cost_records", lambda **_kwargs: [])
    monkeypatch.setattr(state_router, "get_provider_usage_data", _available_quota)
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

    data = state_router.compute_routing_budget(
        datetime.now(UTC),
        budget_config_path=budget_path,
        tasks_dir=tasks,
        batch_state_dir=batch,
    )

    assert "agy" not in data["agents"]
    gemini_row = data["agents"]["gemini"]
    runtime = gemini_row["runtime"]
    burn = gemini_row["fleet_burn"]
    direct = usage_mod.summarize_fleet_burn("gemini", usage_dir=usage, now=now)
    agy_direct = usage_mod.summarize_fleet_burn("agy", usage_dir=usage, now=now)
    agy_runtime = usage_mod.summarize_lane_runtime("agy", usage_dir=usage, now=now)
    expected_unreadable = {"files": 0, "lines": 1, "records": 0, "total": 1}
    assert runtime["ok"] == 1
    assert runtime["rate_limited"] == 1
    assert runtime["total"] == 2
    assert runtime["models_rate_limited"] == ["gemini-\ufffd"]
    assert runtime["headroom_blocked"] is False
    assert runtime["unreadable"] == expected_unreadable
    assert agy_runtime["total"] == runtime["total"]
    assert agy_runtime["models_rate_limited"] == runtime["models_rate_limited"]
    assert agy_runtime["unreadable"] == runtime["unreadable"]
    assert burn["windows"]["5h"]["counts"]["total"] == 2
    assert burn["windows"]["5h"]["hours"] == 1.5
    assert burn["windows"]["7d"]["counts"]["total"] == 3
    assert burn["windows"]["7d"]["hours"] == 3.5
    assert burn["windows"]["30d"]["counts"]["error"] == 1
    assert burn["windows"]["30d"]["counts"]["total"] == 4
    assert burn["windows"]["30d"]["hours"] == 4.5
    assert burn["unreadable"] == expected_unreadable
    assert burn["windows"] == direct["windows"] == agy_direct["windows"]
    assert burn["unreadable"] == direct["unreadable"] == agy_direct["unreadable"]

    codex = data["agents"]["codex"]
    claude = data["agents"]["claude"]
    assert codex["runtime"]["total"] == 1
    assert codex["runtime"]["unreadable"]["total"] == 0
    assert codex["fleet_burn"]["windows"]["5h"]["hours"] == 0.5
    assert claude["runtime"]["total"] == 0
    assert claude["fleet_burn"]["windows"]["7d"]["counts"]["total"] == 1
    assert claude["fleet_burn"]["unreadable"]["total"] == 0
