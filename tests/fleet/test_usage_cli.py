"""CLI transport, freshness, allotment display, and credential privacy regressions."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

from scripts.fleet import usage


@pytest.fixture
def budget():
    return {
        "agents": {
            "codex": {
                "status": "cool",
                "remaining_pct": 80,
                "codexbar": {
                    "freshness": "fresh",
                    "age_s": 3,
                    "windows": {
                        "primary": {
                            "used_pct": 20.0,
                            "remaining_pct": 80.0,
                            "resets_at": "2026-09-15T12:00:00Z",
                            "window_minutes": 300,
                        },
                        "secondary": {
                            "used_pct": 40.0,
                            "remaining_pct": 60.0,
                            "resets_at": "2026-09-20T12:00:00Z",
                            "window_minutes": 10080,
                        },
                        "tertiary": {
                            "used_pct": None,
                            "remaining_pct": None,
                            "resets_at": None,
                            "window_minutes": None,
                        },
                    },
                },
            },
            "claude": {
                "status": "unknown",
                "freshness": "unavailable",
                "interactive": {
                    "spent_7d_usd": 12.0,
                    "weekly_cap_usd": 460.0,
                    "burn_pct_7d": None,
                    "status": "unknown",
                },
                "agentic_pool": {
                    "spent_cycle_usd": 5.0,
                    "monthly_cap_usd": 200.0,
                    "burn_pct_cycle": 2.5,
                    "active": True,
                    "status": "cool",
                },
                "codexbar": {"freshness": "unavailable", "failure_kind": "fetch_error", "last_failure_code": 429},
            },
            "cursor": {
                "status": "cool",
                "freshness": "fresh",
                "age_s": 2,
                "probe_state": "NEED_PROBE",
                "provider_windows": {
                    "auto": {
                        "window": "monthly",
                        "label": "Cursor Models (Auto)",
                        "used_pct": 36.0,
                        "remaining_pct": 64.0,
                        "resets_at": "2026-10-01T00:00:00Z",
                    },
                    "api": {
                        "window": "monthly",
                        "label": "Other Models (API)",
                        "used_pct": 10.0,
                        "remaining_pct": 90.0,
                        "resets_at": "2026-10-01T00:00:00Z",
                    },
                    "grok_bot": {
                        "window": "weekly",
                        "label": "Grok Bot",
                        "used_pct": 22.0,
                        "remaining_pct": 78.0,
                        "resets_at": "2026-09-18T00:00:00Z",
                    },
                },
            },
            "kimi": {
                "status": "cool",
                "remaining_pct": 58.0,
                "codexbar": {
                    "freshness": "fresh",
                    "age_s": 1,
                    "windows": {
                        "primary": {
                            "used_pct": 0.0,
                            "remaining_pct": 100.0,
                            "resets_at": "t1",
                            "window_minutes": 300,
                        },
                        "secondary": {
                            "used_pct": 42.0,
                            "remaining_pct": 58.0,
                            "resets_at": "t2",
                            "window_minutes": 10080,
                        },
                    },
                },
            },
        },
        "api_accounts": {
            "deepseek": {
                "probe_state": "ok",
                "freshness": "fresh",
                "age_s": 4,
                "currency": "USD",
                "total_balance": 0,
                "is_available": False,
            },
            "openrouter": {
                "probe_state": "ok",
                "freshness": "fresh",
                "age_s": 5,
                "limit_remaining_usd": 50,
                "account_remaining_usd": None,
                "usage_daily_usd": 1,
                "usage_weekly_usd": 2,
            },
        },
    }


def test_json_uses_monitor_and_preserves_payload(monkeypatch, capsys, budget):
    urls = []

    def http(url, **kwargs):
        urls.append(url)
        assert kwargs["timeout"] == 5
        return io.StringIO(json.dumps(budget))

    monkeypatch.setenv("DELEGATE_MONITOR_API", "http://fixture.invalid:8765/")
    monkeypatch.setattr(usage.urllib.request, "urlopen", http)
    from scripts.api import state_router

    monkeypatch.setattr(state_router, "compute_routing_budget", lambda **kw: pytest.fail("cold process read"))
    assert usage.main(["json"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result == {**budget, "source": "monitor-api"}
    assert urls == ["http://fixture.invalid:8765/api/state/routing-budget?transport=dispatch"]


@pytest.mark.parametrize("argv", [["refresh"], ["show", "--fresh"], ["--fresh", "json"]])
def test_fresh_blocks_for_both_probes(monkeypatch, capsys, budget, argv):
    from scripts.api import state_router, subscription_usage

    calls = []
    monkeypatch.setattr(usage.urllib.request, "urlopen", lambda *a, **kw: pytest.fail("fresh must bypass HTTP"))
    monkeypatch.setattr(
        subscription_usage, "refresh_provider_usage_data", lambda providers: calls.append("subscriptions")
    )
    monkeypatch.setattr(subscription_usage, "refresh_api_account_data", lambda providers: calls.append("prepaid"))

    def compute(**kwargs):
        assert sorted(calls) == ["prepaid", "subscriptions"]
        assert kwargs.get("fresh_codexbar", False) is False
        return budget

    monkeypatch.setattr(state_router, "compute_routing_budget", compute)
    assert usage.main(argv) == 0
    assert "in-process-fresh" in capsys.readouterr().out


def test_offline_falls_back_with_explicit_source(monkeypatch, budget, capsys):
    from scripts.api import state_router, subscription_usage

    monkeypatch.setattr(usage.urllib.request, "urlopen", lambda *a, **kw: (_ for _ in ()).throw(OSError("offline")))
    monkeypatch.setattr(subscription_usage, "refresh_provider_usage_data", lambda providers: {})
    monkeypatch.setattr(subscription_usage, "refresh_api_account_data", lambda providers: {})
    monkeypatch.setattr(state_router, "compute_routing_budget", lambda **kw: budget)
    assert usage.main(["show"]) == 0
    output = capsys.readouterr()
    assert "source: in-process-fresh" in output.out
    assert "Monitor snapshot unavailable" in output.err


def test_show_distinguishes_balance_key_cap_and_unknown(budget):
    budget["source"] = "monitor-api"
    budget["agents"]["codex"]["codexbar"]["freshness"] = "unavailable"
    # Drop windows so top-line stays unknown without allotment rem.
    budget["agents"]["codex"]["codexbar"]["windows"] = None
    text = usage.format_human(budget)
    assert "codex | unknown | unknown | unavailable" in text
    assert " | -" in text or "unavailable | unknown |" in text
    assert "deepseek | near_cap | pick: AVOID" in text
    assert "openrouter | cool | pick: n/a (funding account)" in text
    assert "balance: needs management key | key cap remaining: $50.00" in text
    assert "daily spend: $1.00 | weekly spend: $2.00" in text
    assert "age_s: 4" in text
    budget["api_accounts"]["openrouter"]["balance_probe_state"] = "NEED_PROBE"
    assert "balance: probe unavailable" in usage.format_human(budget)


def test_show_renders_multi_window_allotments(budget):
    text = usage.format_human({**budget, "source": "monitor-api"})
    assert "interactive (weekly):" in text
    assert "agentic/Fable (monthly):" in text
    assert "spent=$5.00/$200.00" in text
    assert "Cursor Models (Auto) (monthly): used=36.0% rem=64.0%" in text
    assert "Other Models (API) (monthly): used=10.0% rem=90.0%" in text
    assert "Grok Bot (weekly): used=22.0% rem=78.0%" in text
    assert "primary (5h): used=0.0% rem=100.0%" in text
    assert "secondary (weekly): used=42.0% rem=58.0%" in text
    assert "fetch_error/429" in text


def test_show_does_not_import_state_router(monkeypatch, budget, capsys):
    """Monitor-backed show must stay light for notebook checkouts without v4."""

    def http(url, **kwargs):
        return io.StringIO(json.dumps(budget))

    monkeypatch.setenv("DELEGATE_MONITOR_API", "http://fixture.invalid:8765/")
    monkeypatch.setattr(usage.urllib.request, "urlopen", http)
    # Remove heavy modules if already imported so accidental import is detectable.
    for name in list(sys.modules):
        if name.startswith("scripts.api.state_router") or name.startswith("learn_ukrainian_v4_runtime"):
            monkeypatch.delitem(sys.modules, name, raising=False)

    real_import = __import__

    def guarded(name, *args, **kwargs):
        if name == "scripts.api.state_router" or name.startswith("scripts.api.state_router."):
            raise AssertionError("show must not import state_router")
        if name == "learn_ukrainian_v4_runtime" or name.startswith("learn_ukrainian_v4_runtime."):
            raise AssertionError("show must not import v4_runtime")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", guarded)
    assert usage.main(["show"]) == 0
    out = capsys.readouterr().out
    assert "Grok Bot (weekly)" in out
    assert "agentic/Fable (monthly)" in out


def test_qa_passes_when_allotments_usable(budget, monkeypatch, capsys):
    monkeypatch.setenv("DELEGATE_MONITOR_API", "http://fixture.invalid:8765/")
    monkeypatch.setattr(
        usage.urllib.request,
        "urlopen",
        lambda *a, **kw: io.StringIO(json.dumps(budget)),
    )
    assert usage.main(["qa"]) == 0
    assert "QA PASS" in capsys.readouterr().out


def test_doctor_does_not_read_credentials_or_print_values(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    secret = tmp_path / ".secret/openrouter-management.key"
    secret.parent.mkdir()
    secret.write_text("secret-file-marker")
    monkeypatch.setenv("OPENROUTER_MANAGEMENT_API_KEY", "secret-env-marker")
    monkeypatch.setattr(Path, "read_text", lambda *a, **kw: pytest.fail("doctor must not read credential contents"))
    assert usage.main(["doctor"]) == 0
    text = capsys.readouterr().out
    assert "env OPENROUTER_MANAGEMENT_API_KEY: present" in text
    assert "file ~/.secret/openrouter-management.key: present" in text
    assert "secret-file-marker" not in text and "secret-env-marker" not in text


def test_refresh_failure_is_nonzero_and_does_not_echo_exception(monkeypatch, capsys):
    monkeypatch.setattr(usage, "read_budget", lambda **kw: (_ for _ in ()).throw(RuntimeError("secret-marker")))
    assert usage.main(["refresh"]) == 1
    assert "secret-marker" not in capsys.readouterr().err
