"""CLI transport, freshness, allotment display, and credential privacy regressions."""

from __future__ import annotations

import copy
import io
import json
import subprocess
from pathlib import Path

import pytest

from scripts.fleet import usage


@pytest.fixture(autouse=True)
def _isolate_agy_quota_observation():
    """AGY quota state is process-global; keep one test's probe off the next."""
    from scripts.api import subscription_usage

    subscription_usage._reset_agy_quota_observation_for_tests()
    yield
    subscription_usage._reset_agy_quota_observation_for_tests()


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
    from scripts.api import state_router, subscription_usage
    from scripts.api.state_helpers import cache_invalidate

    cache_invalidate("codexbar_usage:muse")
    subscription_usage._last_good_data.pop("muse", None)
    subscription_usage._last_failure_data.pop("muse", None)
    monkeypatch.setattr(state_router, "compute_routing_budget", lambda **kw: pytest.fail("cold process read"))
    assert usage.main(["json"]) == 0
    result = json.loads(capsys.readouterr().out)
    muse = result["agents"].pop("muse")
    agy = result["agents"].pop("agy")
    assert result == {**budget, "source": "monitor-api"}
    assert muse["status"] == "unknown"
    assert muse["remaining_pct"] is None
    assert muse["headroom_pct"] is None
    assert muse["resets_at"] is None
    assert muse["freshness"] == "unavailable"
    assert agy["status"] == "unknown"
    assert agy["remaining_pct"] is None
    assert agy["headroom_pct"] is None
    assert agy["freshness"] == "unavailable"
    assert agy["error_kind"] == "unavailable"
    assert agy["quota_groups"] == []
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


def test_prepaid_rejects_non_usd_deepseek():
    from scripts.fleet.prepaid_status import api_lane_status_from_account

    account = {
        "probe_state": "ok",
        "freshness": "fresh",
        "age_s": 1,
        "currency": "CNY",
        "total_balance": 25,
        "is_available": True,
    }
    assert api_lane_status_from_account("deepseek", account) == "unknown"
    account["currency"] = "USD"
    assert api_lane_status_from_account("deepseek", account) == "cool"


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
_MUSE_NULL_PAYLOAD = {"provider": "muse", "usage": {"primary": None, "secondary": None}}


@pytest.mark.parametrize(
    ("payload", "status", "remaining", "kind", "code", "window"),
    [
        (
            {
                "provider": "muse",
                "source": "PRIVATE_SOURCE",
                "usage": {
                    "primary": {
                        "usedPercent": 20,
                        "windowMinutes": "PRIVATE_MINUTES",
                        "resetsAt": "PRIVATE_RESET",
                        "resetDescription": "PRIVATE_DESCRIPTION",
                        "label": "PRIVATE_LABEL",
                    }
                },
            },
            "healthy",
            80.0,
            None,
            None,
            {
                "used_pct": 20.0,
                "remaining_pct": 80.0,
                "resets_at": None,
                "window_minutes": None,
                "reset_description": None,
            },
        ),
        (
            {"provider": "muse", "error": {"kind": "PRIVATE_KIND", "code": "PRIVATE_CODE"}},
            "unknown",
            None,
            "provider",
            "PROVIDER_ERROR",
            None,
        ),
        ({"provider": "muse", "error": "PRIVATE_ERROR"}, "unknown", None, "provider", "PROVIDER_ERROR", None),
        ({"provider": "muse", "error": {"kind": "provider"}}, "unknown", None, "provider", "PROVIDER_ERROR", None),
        (
            {"provider": "muse", "usage": {"updatedAt": "2000-01-01T00:00:00Z", "primary": {"usedPercent": 20}}},
            "unknown",
            None,
            "fetch_error",
            "STALE_DATA",
            None,
        ),
        (
            {"provider": "muse", "usage": {"updatedAt": "PRIVATE_TIME", "primary": {"usedPercent": 20}}},
            "unknown",
            None,
            "fetch_error",
            "BAD_JSON",
            None,
        ),
        (
            [{"provider": "codex", "usage": {"primary": {"usedPercent": 7}}}, _MUSE_NULL_PAYLOAD],
            "unknown",
            None,
            "unsupported",
            "NO_QUOTA",
            None,
        ),
        (
            {"provider": "PRIVATE_PROVIDER", "usage": {"primary": {"usedPercent": 7}}},
            "unknown",
            None,
            "fetch_error",
            "PROVIDER_MISMATCH",
            None,
        ),
        (
            {"provider": "muse", "usage": {"primary": {"usedPercent": -1}}},
            "unknown",
            None,
            "unsupported",
            "NO_QUOTA",
            None,
        ),
        (
            {"provider": "muse", "usage": {"primary": {"usedPercent": 101}}},
            "unknown",
            None,
            "unsupported",
            "NO_QUOTA",
            None,
        ),
        (
            {"provider": "muse", "usage": {"primary": {"usedPercent": 0}}},
            "healthy",
            100.0,
            None,
            None,
            {
                "used_pct": 0.0,
                "remaining_pct": 100.0,
                "resets_at": None,
                "window_minutes": None,
                "reset_description": None,
            },
        ),
        (
            {"provider": "muse", "usage": {"primary": {"usedPercent": 100}}},
            "healthy",
            0.0,
            None,
            None,
            {
                "used_pct": 100.0,
                "remaining_pct": 0.0,
                "resets_at": None,
                "window_minutes": None,
                "reset_description": None,
            },
        ),
    ],
    ids=[
        "private-metadata",
        "private-error",
        "uncoded-private-error",
        "uncoded-provider-error",
        "stale",
        "invalid-time",
        "wrong-list-provider",
        "wrong-provider",
        "negative",
        "over-full",
        "zero",
        "full",
    ],
)
def test_muse_boundary_reaches_literal_json_and_human_output(
    monkeypatch,
    capsys,
    payload,
    status,
    remaining,
    kind,
    code,
    window,
):
    from scripts.api import subscription_usage as su

    record = su._muse_record_from_codexbar_payload(payload)
    record.update(freshness="fresh", age_s=0.0)
    monkeypatch.setattr(su, "get_provider_usage_data", lambda *args, **kwargs: record)
    monkeypatch.setattr(su, "get_agy_quota_observation", lambda: {})
    monkeypatch.setattr(
        usage,
        "read_budget",
        lambda **kwargs: (
            {
                **usage._attach_status_observations({"agents": {}, "api_accounts": {}, "source": "fixture"}),
                "agents": {"muse": usage._attach_status_observations({})["agents"]["muse"]},
            }
            if kwargs.get("for_display")
            else {"agents": {}, "api_accounts": {}, "source": "fixture"}
        ),
    )
    empty = {
        "used_pct": None,
        "remaining_pct": None,
        "resets_at": None,
        "window_minutes": None,
        "reset_description": None,
    }
    expected = {
        "lane": "muse",
        "status": status,
        "remaining_pct": remaining,
        "headroom_pct": remaining,
        "resets_at": None,
        "freshness": "fresh",
        "age_s": 0.0,
        "error_kind": kind,
        "error_code": code,
        "failure_kind": kind,
        "last_failure_code": code,
        "auth_error": None,
        "codexbar": {
            "freshness": "fresh",
            "age_s": 0.0,
            "headroom_pct": remaining,
            "weekly_resets_at": None,
            "windows": {"primary": window or empty, "secondary": empty, "tertiary": empty},
            "error_kind": kind,
            "failure_kind": kind,
            "last_failure_code": code,
            "primary_remaining_pct": remaining,
            "weekly_remaining_pct": None,
        },
    }
    assert usage.main(["json"]) == 0
    json_text = capsys.readouterr().out
    assert json.loads(json_text) == {"agents": {"muse": expected}, "api_accounts": {}, "source": "fixture"}
    assert usage.main(["show"]) == 0
    human = capsys.readouterr().out
    rem_text = "unknown" if remaining is None else f"{remaining:.1f}"
    quota_text = "unknown" if remaining is None else f"{remaining:.1f}%"
    fail_text = "-" if kind is None else f"{kind}/{code}"
    lines = [
        "source: fixture",
        "Subscriptions (per-lane allotments; blank pools mean the probe did not return them)",
        "lane | status | remaining% | freshness | age_s | fail",
        "agy | unknown | unknown | unavailable | unknown | -",
        "  (no allotment windows; probe returned empty)",
        f"muse | {status} | {rem_text} | fresh | 0.0 | {fail_text}",
        f"  quota: remaining={quota_text} headroom={quota_text} resets=unknown",
    ]
    if window is not None:
        lines.append(f"  primary (window): used={window['used_pct']:.1f}% rem={remaining:.1f}% resets=unknown")
    lines.extend(["", "Prepaid (USD; key cap remaining is not account balance)"])
    lines.extend(
        [
            "",
            "WARN: no usable subscription allotment rows — mix-max is blind. "
            "Run: usage doctor && usage show --fresh; check fail= codes above.",
        ]
    )
    assert human == "\n".join(lines) + "\n"
    assert "PRIVATE_" not in json_text + human


@pytest.mark.parametrize(
    ("envelope", "fraction", "status", "freshness", "kind", "code", "windows", "line"),
    [
        (
            {},
            0.8,
            "healthy",
            "fresh",
            None,
            None,
            [{"window": "5h", "used_pct": 20.0, "remaining_pct": 80.0, "resets_at": None, "window_minutes": 300}],
            "  Gemini Models (5h): used=20.0% rem=80.0% resets=unknown",
        ),
        (
            {"status": "error", "error": {"code": 429, "message": "PRIVATE_ERROR"}},
            0.8,
            "unknown",
            "unavailable",
            "rate_limit",
            429,
            [],
            None,
        ),
        (
            {"error": {"kind": "PRIVATE_KIND", "code": "PRIVATE_CODE"}},
            0.8,
            "unknown",
            "unavailable",
            "provider",
            "PROVIDER_ERROR",
            [],
            None,
        ),
        ({"provider": "PRIVATE_PROVIDER"}, 0.8, "unknown", "unavailable", "fetch_error", "PROVIDER_MISMATCH", [], None),
        ({"status": "PRIVATE_STATUS"}, 0.8, "unknown", "unavailable", "provider", "PROVIDER_ERROR", [], None),
        ({"error": "PRIVATE_ERROR"}, 0.8, "unknown", "unavailable", "provider", "PROVIDER_ERROR", [], None),
        (
            {},
            1.1,
            "unknown",
            "fresh",
            "unsupported",
            "NO_QUOTA",
            [{"window": "5h", "used_pct": None, "remaining_pct": None, "resets_at": None, "window_minutes": 300}],
            "  Gemini Models (5h): used=unknown rem=unknown resets=unknown",
        ),
        (
            {},
            -0.1,
            "unknown",
            "fresh",
            "unsupported",
            "NO_QUOTA",
            [{"window": "5h", "used_pct": None, "remaining_pct": None, "resets_at": None, "window_minutes": 300}],
            "  Gemini Models (5h): used=unknown rem=unknown resets=unknown",
        ),
        (
            {},
            0,
            "healthy",
            "fresh",
            None,
            None,
            [{"window": "5h", "used_pct": 100.0, "remaining_pct": 0.0, "resets_at": None, "window_minutes": 300}],
            "  Gemini Models (5h): used=100.0% rem=0.0% resets=unknown",
        ),
        (
            {},
            1,
            "healthy",
            "fresh",
            None,
            None,
            [{"window": "5h", "used_pct": 0.0, "remaining_pct": 100.0, "resets_at": None, "window_minutes": 300}],
            "  Gemini Models (5h): used=0.0% rem=100.0% resets=unknown",
        ),
    ],
    ids=[
        "private-metadata",
        "rate-limit",
        "private-error",
        "wrong-provider",
        "uncoded-failure-status",
        "uncoded-private-error",
        "over-full",
        "negative",
        "zero",
        "full",
    ],
)
def test_agy_boundary_reaches_literal_json_and_human_output(
    monkeypatch,
    capsys,
    envelope,
    fraction,
    status,
    freshness,
    kind,
    code,
    windows,
    line,
):
    import subprocess

    from scripts.api import subscription_usage as su

    payload = {
        **envelope,
        "command": {
            "data": {
                "groups": [
                    {
                        "name": "Gemini PRIVATE_LABEL",
                        "buckets": [
                            {"window": "5h", "remaining_fraction": fraction, "reset_time": "PRIVATE_RESET"},
                            {"window": "PRIVATE_WINDOW", "remaining_fraction": 0.9},
                        ],
                        "account": "PRIVATE_ACCOUNT",
                        "credits": 987654,
                    }
                ]
            }
        },
    }
    monkeypatch.setattr(su, "_agy_cli_bin", lambda: "/fixture/agy")
    monkeypatch.setattr(
        su.subprocess,
        "run",
        lambda argv, **kwargs: subprocess.CompletedProcess(
            argv,
            0,
            stdout=json.dumps(payload),
            stderr="PRIVATE_STDERR",
        ),
    )
    su._probe_antigravity_native(timeout_s=5)
    observation = su.get_agy_quota_observation()
    observation["age_s"] = 0.0 if freshness == "fresh" else None
    monkeypatch.setattr(su, "get_agy_quota_observation", lambda: observation)
    monkeypatch.setattr(su, "get_provider_usage_data", lambda *args, **kwargs: {})

    def budget(**kwargs):
        if not kwargs.get("for_display"):
            return {"agents": {}, "api_accounts": {}, "source": "fixture"}
        attached = usage._attach_status_observations({"agents": {}, "api_accounts": {}, "source": "fixture"})
        attached["agents"].pop("muse")
        return attached

    monkeypatch.setattr(usage, "read_budget", budget)
    groups = [] if not windows else [{"key": "gemini_models", "label": "Gemini Models", "windows": windows}]
    age = 0.0 if freshness == "fresh" else None
    expected = {
        "lane": "agy",
        "status": status,
        "remaining_pct": None,
        "headroom_pct": None,
        "resets_at": None,
        "freshness": freshness,
        "age_s": age,
        "error_kind": kind,
        "error_code": code,
        "failure_kind": kind,
        "last_failure_code": code,
        "auth_error": None,
        "quota_groups": groups,
        "codexbar": {
            "freshness": freshness,
            "age_s": age,
            "quota_groups": groups,
            "error_kind": kind,
            "error_code": code,
            "failure_kind": kind,
            "last_failure_code": code,
            "source": "agy_cli_usage",
        },
    }
    assert usage.main(["json"]) == 0
    json_text = capsys.readouterr().out
    assert json.loads(json_text) == {"source": "fixture", "agents": {"agy": expected}, "api_accounts": {}}
    assert usage.main(["show"]) == 0
    human = capsys.readouterr().out
    fail = "-" if kind is None else f"{kind}/{code}"
    lines = [
        "source: fixture",
        "Subscriptions (per-lane allotments; blank pools mean the probe did not return them)",
        "lane | status | remaining% | freshness | age_s | fail",
        f"agy | {status} | unknown | {freshness} | {'unknown' if age is None else '0.0'} | {fail}",
    ]
    if line:
        lines.append(line)
    lines.extend(
        [
            "muse | unknown | unknown | unavailable | unknown | -",
            "  quota: remaining=unknown headroom=unknown resets=unknown",
        ]
    )
    lines.extend(["", "Prepaid (USD; key cap remaining is not account balance)"])
    lines.extend(
        [
            "",
            "WARN: no usable subscription allotment rows — mix-max is blind. "
            "Run: usage doctor && usage show --fresh; check fail= codes above.",
        ]
    )
    assert human == "\n".join(lines) + "\n"
    assert "PRIVATE_" not in json_text + human
    assert "987654" not in json_text + human


def _clear_muse_observation() -> None:
    from scripts.api import subscription_usage
    from scripts.api.state_helpers import cache_invalidate

    cache_invalidate("codexbar_usage:muse")
    subscription_usage._last_good_data.pop("muse", None)
    subscription_usage._last_failure_data.pop("muse", None)


@pytest.mark.parametrize("lane", ["muse", "agy"])
@pytest.mark.parametrize("command", ["show", "json"])
@pytest.mark.parametrize("attempt_failed_fetch", [False, True], ids=["cold", "failed-fetch"])
def test_usage_cli_cold_and_failed_fetch_diagnostics(monkeypatch, capsys, lane, command, attempt_failed_fetch):
    from scripts.api import subscription_usage as su

    _clear_muse_observation()
    calls = []

    def failed_probe(*, timeout_s):
        calls.append(timeout_s)
        raise RuntimeError("PRIVATE_PROVIDER_TEXT account@example.com credits=987654")

    def unexpected_fetch(*args, **kwargs):
        pytest.fail("Displaying cached observations must not attempt a provider fetch")

    if attempt_failed_fetch:
        provider = "muse" if lane == "muse" else "gemini"
        monkeypatch.setitem(su._NATIVE_PROBES, provider, failed_probe)
        su.refresh_provider_usage_data([provider], timeout_s=1)
    monkeypatch.setattr(su, "fetch_provider_usage", unexpected_fetch)
    monkeypatch.setattr(su, "trigger_background_refresh", unexpected_fetch)

    def budget(**kwargs):
        if not kwargs.get("for_display"):
            return {"agents": {}, "api_accounts": {}, "source": "fixture"}
        attached = usage._attach_status_observations({"agents": {}, "api_accounts": {}, "source": "fixture"})
        attached["agents"].pop("agy" if lane == "muse" else "muse")
        return attached

    monkeypatch.setattr(usage, "read_budget", budget)
    kind = "fetch_error" if attempt_failed_fetch else "unavailable"
    code = "FETCH_ERROR" if attempt_failed_fetch else None
    expected = {
        "lane": lane,
        "status": "unknown",
        "remaining_pct": None,
        "headroom_pct": None,
        "resets_at": None,
        "freshness": "unavailable",
        "age_s": None,
        "error_kind": kind,
        "error_code": code,
        "failure_kind": kind,
        "last_failure_code": code,
        "auth_error": None,
        "codexbar": {
            "freshness": "unavailable",
            "age_s": None,
            "error_kind": kind,
            "failure_kind": kind,
            "last_failure_code": code,
        },
    }
    if lane == "muse":
        expected["codexbar"].update(
            {
                "headroom_pct": None,
                "weekly_resets_at": None,
                "primary_remaining_pct": None,
                "weekly_remaining_pct": None,
                "windows": {
                    name: {
                        "used_pct": None,
                        "remaining_pct": None,
                        "resets_at": None,
                        "window_minutes": None,
                        "reset_description": None,
                    }
                    for name in ("primary", "secondary", "tertiary")
                },
            }
        )
    else:
        expected["quota_groups"] = []
        expected["codexbar"].update({"error_code": code, "quota_groups": [], "source": "agy_cli_usage"})

    assert usage.main([command]) == 0
    output = capsys.readouterr().out
    if command == "json":
        assert json.loads(output) == {"source": "fixture", "agents": {lane: expected}, "api_accounts": {}}
    else:
        diagnostic = "fetch_error/FETCH_ERROR" if attempt_failed_fetch else "unavailable"
        lines = [
            "source: fixture",
            "Subscriptions (per-lane allotments; blank pools mean the probe did not return them)",
            "lane | status | remaining% | freshness | age_s | fail",
            f"{lane} | unknown | unknown | unavailable | unknown | {diagnostic}",
        ]
        if lane == "muse":
            lines.insert(3, "agy | unknown | unknown | unavailable | unknown | unavailable")
            lines.append("  quota: remaining=unknown headroom=unknown resets=unknown")
        else:
            lines.extend(
                [
                    "muse | unknown | unknown | unavailable | unknown | unavailable",
                    "  quota: remaining=unknown headroom=unknown resets=unknown",
                ]
            )
        lines.extend(
            [
                "",
                "Prepaid (USD; key cap remaining is not account balance)",
                "",
                "WARN: no usable subscription allotment rows — mix-max is blind. "
                "Run: usage doctor && usage show --fresh; check fail= codes above.",
            ]
        )
        assert output == "\n".join(lines) + "\n"
    assert calls == ([1] if attempt_failed_fetch else [])
    assert "PRIVATE_PROVIDER_TEXT" not in output
    assert "account@example.com" not in output
    assert "987654" not in output
    _clear_muse_observation()


def test_usage_cli_shows_agy_missing_fraction_as_unknown(monkeypatch, capsys):
    import subprocess

    from scripts.api import state_router, subscription_usage

    _clear_muse_observation()
    subscription_usage._reset_agy_quota_observation_for_tests()
    monkeypatch.setattr(subscription_usage, "_agy_cli_bin", lambda: "/usr/bin/agy")
    payload = {
        "command": {
            "data": {
                "groups": [
                    {
                        "name": "Gemini Models",
                        "buckets": [
                            {
                                "window": "weekly",
                                "remaining_fraction": None,
                                "reset_time": "2026-10-20T00:00:00Z",
                            }
                        ],
                    }
                ]
            }
        }
    }

    def fake_run(argv, **kwargs):
        return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(payload), stderr="")

    monkeypatch.setattr(subscription_usage.subprocess, "run", fake_run)
    probe = subscription_usage._probe_antigravity_native

    def fetch(provider, *, timeout_s=None):
        if provider in {"gemini", "antigravity"}:
            return probe(timeout_s=1)
        return subscription_usage._normalize_provider_error(
            provider,
            {"message": "skipped", "kind": "unavailable", "code": "SKIP"},
        )

    monkeypatch.setattr(subscription_usage, "fetch_provider_usage", fetch)
    monkeypatch.setattr(subscription_usage, "refresh_api_account_data", lambda providers: {})
    monkeypatch.setattr(
        subscription_usage,
        "_refresh_cursor_usage_live",
        lambda: subscription_usage._normalize_provider_error(
            "cursor",
            {"message": "skipped", "kind": "unavailable", "code": "SKIP"},
        ),
    )
    monkeypatch.setattr(
        state_router,
        "compute_routing_budget",
        lambda **kwargs: {"agents": {}, "api_accounts": {}},
    )
    assert usage.main(["show", "--fresh"]) == 0
    text = capsys.readouterr().out
    assert "agy | unknown | unknown | fresh |" in text
    assert "unsupported/NO_QUOTA" in text
    assert "Gemini Models (weekly): used=unknown rem=unknown resets=2026-10-20T00:00:00Z" in text
    assert "100.0" not in text
    assert "50.0" not in text


@pytest.mark.parametrize("fresh", [False, True], ids=["monitor", "fresh"])
@pytest.mark.parametrize("diagnostic", ["muse", "agy", "both"])
@pytest.mark.parametrize("known_lane", [None, "claude", "codex", "gemini", "grok", "cursor", "kimi"])
@pytest.mark.parametrize("command", ["qa", "show", "refresh"])
def test_cli_routing_health_counts_only_authoritative_rows(monkeypatch, capsys, fresh, diagnostic, known_lane, command):
    from scripts.api import state_router
    from scripts.api import subscription_usage as su

    _clear_muse_observation()
    routing = {
        "agents": {
            lane: {
                "status": "unknown",
                "remaining_pct": None,
                "freshness": "unavailable",
                "failure_kind": "fetch_error",
                "last_failure_code": "TIMEOUT",
            }
            for lane in ("claude", "codex", "gemini", "grok", "cursor", "kimi")
        },
        "api_accounts": {},
    }
    if known_lane is not None:
        routing["agents"][known_lane] = {
            "status": "cool",
            "remaining_pct": 80.0,
            "freshness": "fresh",
            "codexbar": {"windows": {"primary": {"used_pct": 20.0, "remaining_pct": 80.0}}},
        }
    original = copy.deepcopy(routing)
    payloads = {
        "/fixture/codexbar": {
            "provider": "muse",
            "usage": {"primary": {"usedPercent": 60}},
            "account": "PRIVATE_ACCOUNT account@example.invalid",
            "credits": 987654321,
        },
        "/fixture/agy": {
            "command": {
                "data": {
                    "groups": [
                        {
                            "name": "Claude and GPT PRIVATE_LABEL",
                            "buckets": [{"window": "5h", "remaining_fraction": 0.5}],
                        }
                    ]
                }
            },
            "account": "PRIVATE_ACCOUNT account@example.invalid",
            "credits": 987654321,
        },
    }
    monkeypatch.setattr(su, "_codexbar_bin", lambda: "/fixture/codexbar")
    monkeypatch.setattr(su, "_agy_cli_bin", lambda: "/fixture/agy")

    def run(argv, **kwargs):
        assert argv[0] in payloads
        return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(payloads[argv[0]]), stderr="PRIVATE_STDERR")

    monkeypatch.setattr(su.subprocess, "run", run)
    real_refresh = su.refresh_provider_usage_data
    providers = {"muse": ["muse"], "agy": ["gemini"], "both": ["muse", "gemini"]}[diagnostic]
    refreshes = []

    def refresh(requested):
        assert set(providers) <= set(requested)
        refreshes.append("subscription")
        return real_refresh(providers, timeout_s=1)

    monkeypatch.setattr(su, "refresh_provider_usage_data", refresh)
    monkeypatch.setattr(su, "refresh_api_account_data", lambda requested: refreshes.append("prepaid"))
    monkeypatch.setattr(state_router, "compute_routing_budget", lambda **kwargs: routing)
    http_reads = []

    def http(url, **kwargs):
        http_reads.append(url)
        return io.StringIO(json.dumps(routing))

    monkeypatch.setattr(usage.urllib.request, "urlopen", http)
    if not fresh and command != "refresh":
        real_refresh(providers, timeout_s=1)

    try:
        expected_exit = 1 if command == "qa" and known_lane is None else 0
        assert usage.main([command] + (["--fresh"] if fresh else [])) == expected_exit
        public = capsys.readouterr()
        if command == "qa" and known_lane is None:
            assert public.out == "QA FAIL:\n- no usable subscription allotment rows (mix-max blind)\n"
        else:
            warning = (
                "WARN: no usable subscription allotment rows — mix-max is blind. "
                "Run: usage doctor && usage show --fresh; check fail= codes above."
            )
            assert (warning in public.out) == (known_lane is None)
            if command == "qa":
                assert public.out.splitlines()[0] == "QA PASS: 1 subscription lane(s) have usable allotment signal(s)"
            if diagnostic in {"muse", "both"}:
                assert "muse | healthy | 40.0 | fresh |" in public.out
                assert "  primary (window): used=60.0% rem=40.0% resets=unknown" in public.out
            if diagnostic in {"agy", "both"}:
                assert "agy | healthy | unknown | fresh |" in public.out
                assert "  Claude and GPT models (5h): used=50.0% rem=50.0% resets=unknown" in public.out
        for sentinel in ("PRIVATE_", "account@example.invalid", "987654321"):
            assert sentinel not in public.out + public.err
        assert public.err == ""
        assert routing == original
        assert len(http_reads) == (0 if fresh or command == "refresh" else 1)
        assert sorted(refreshes) == (["prepaid", "subscription"] if fresh or command == "refresh" else [])
    finally:
        _clear_muse_observation()
        su._reset_agy_quota_observation_for_tests()


@pytest.mark.parametrize("agents", [{}, {"codex": "malformed"}])
def test_cli_qa_rejects_missing_or_malformed_routing_despite_fresh_diagnostics(monkeypatch, capsys, agents):
    from scripts.api import subscription_usage as su

    monkeypatch.setattr(
        usage.urllib.request,
        "urlopen",
        lambda *args, **kwargs: io.StringIO(json.dumps({"agents": agents, "api_accounts": {}})),
    )
    monkeypatch.setattr(
        su,
        "get_provider_usage_data",
        lambda *args, **kwargs: {"freshness": "fresh", "windows": {"primary": {"used_pct": 0}}},
    )
    assert usage.main(["qa"]) == 1
    expected = (
        "QA FAIL: routing-budget agents missing\n"
        if not agents
        else "QA FAIL:\n- codex: not an object\n- no usable subscription allotment rows (mix-max blind)\n"
    )
    assert capsys.readouterr().out == expected
