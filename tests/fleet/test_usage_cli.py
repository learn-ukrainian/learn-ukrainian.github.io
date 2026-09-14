"""CLI transport, freshness and credential privacy regressions."""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from scripts.fleet import usage


@pytest.fixture
def budget():
    return {
        "agents": {"codex": {"status": "cool", "remaining_pct": 80, "codexbar": {"freshness": "fresh", "age_s": 3}}},
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
    text = usage.format_human(budget)
    assert "codex | unknown | unknown | unavailable" in text
    assert "deepseek | near_cap | pick: AVOID" in text
    assert "openrouter | cool | pick: n/a (funding account)" in text
    assert "balance: needs management key | key cap remaining: $50.00" in text
    assert "daily spend: $1.00 | weekly spend: $2.00" in text
    assert "age_s: 4" in text
    budget["api_accounts"]["openrouter"]["balance_probe_state"] = "NEED_PROBE"
    assert "balance: probe unavailable" in usage.format_human(budget)


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
