"""CLI transport, freshness, allotment display, and credential privacy regressions."""

from __future__ import annotations

import io
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from scripts.fleet import usage
from tests.helpers.restore_import_state import restore_import_state


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
    assert "agentic (monthly):" in text
    assert "spent=$5.00/$200.00" in text
    assert "Cursor Models (Auto) (monthly): used=36.0% rem=64.0%" in text
    assert "Other Models (API) (monthly): used=10.0% rem=90.0%" in text
    assert "Grok Bot (weekly): used=22.0% rem=78.0%" in text
    assert "primary (5h): used=0.0% rem=100.0%" in text
    assert "secondary (weekly): used=42.0% rem=58.0%" in text
    assert "fetch_error/429" in text
    assert "tip: Anthropic rate-limited" in text


def test_show_does_not_claim_cool_without_allotment_meters():
    """API-key dispatch cool + NEED_PROBE null windows must display unknown + tip."""
    budget = {
        "source": "monitor-api",
        "agents": {
            "cursor": {
                "status": "cool",
                "freshness": "fresh",
                "age_s": 10,
                "probe_state": "NEED_PROBE",
                "login_state": "authenticated",
                "error_kind": "missing_session_token",
                "provider_windows": {
                    "auto": {
                        "window": "monthly",
                        "label": "Cursor Models (Auto)",
                        "used_pct": None,
                        "remaining_pct": None,
                        "resets_at": None,
                    },
                    "api": {
                        "window": "monthly",
                        "label": "Other Models (API)",
                        "used_pct": None,
                        "remaining_pct": None,
                        "resets_at": None,
                    },
                    "grok_bot": {
                        "window": "weekly",
                        "label": "Grok Bot",
                        "used_pct": None,
                        "remaining_pct": None,
                        "resets_at": None,
                    },
                },
            }
        },
        "api_accounts": {},
    }
    text = usage.format_human(budget)
    assert "cursor | unknown |" in text
    assert "cursor | cool |" not in text
    assert "agent login" in text
    assert "CURSOR_API_KEY alone" in text


def test_show_does_not_claim_cool_with_retained_remaining_pct():
    """NEED_PROBE + null provider windows must not keep cool via leftover remaining_pct."""
    budget = {
        "source": "monitor-api",
        "agents": {
            "cursor": {
                "status": "cool",
                "freshness": "fresh",
                "age_s": 10,
                "remaining_pct": 100.0,
                "probe_state": "NEED_PROBE",
                "login_state": "authenticated",
                "error_kind": "missing_session_token",
                "provider_windows": {
                    "auto": {
                        "window": "monthly",
                        "label": "Cursor Models (Auto)",
                        "used_pct": None,
                        "remaining_pct": None,
                        "resets_at": None,
                    },
                    "api": {
                        "window": "monthly",
                        "label": "Other Models (API)",
                        "used_pct": None,
                        "remaining_pct": None,
                        "resets_at": None,
                    },
                },
            }
        },
        "api_accounts": {},
    }
    text = usage.format_human(budget)
    assert "cursor | unknown | unknown |" in text
    assert "cursor | cool | 100.0 |" not in text
    assert "agent login" in text


def test_show_formats_epoch_resets():
    budget = {
        "source": "monitor-api",
        "agents": {
            "codex": {
                "status": "cool",
                "remaining_pct": 62,
                "codexbar": {
                    "freshness": "fresh",
                    "age_s": 1,
                    "windows": {
                        "primary": {
                            "used_pct": 38.0,
                            "remaining_pct": 62.0,
                            "resets_at": 1789805715,
                            "window_minutes": 300,
                        }
                    },
                },
            }
        },
        "api_accounts": {},
    }
    text = usage.format_human(budget)
    assert "resets=1789805715" not in text
    assert "resets=2026-" in text


def test_show_does_not_import_state_router(monkeypatch, budget, capsys):
    """Monitor-backed show must stay light for notebook checkouts without v4."""

    def http(url, **kwargs):
        return io.StringIO(json.dumps(budget))

    monkeypatch.setenv("DELEGATE_MONITOR_API", "http://fixture.invalid:8765/")
    monkeypatch.setattr(usage.urllib.request, "urlopen", http)
    # Remove heavy modules if already imported so accidental import is detectable.
    evicted = [
        name
        for name in list(sys.modules)
        if name.startswith("scripts.api.state_router") or name.startswith("learn_ukrainian_v4_runtime")
    ]
    with restore_import_state(*evicted):
        for name in evicted:
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
        assert "agentic (monthly)" in out


def test_qa_passes_when_allotments_usable(budget, monkeypatch, capsys):
    monkeypatch.setenv("DELEGATE_MONITOR_API", "http://fixture.invalid:8765/")
    monkeypatch.setattr(
        usage.urllib.request,
        "urlopen",
        lambda *a, **kw: io.StringIO(json.dumps(budget)),
    )
    assert usage.main(["qa"]) == 0
    assert "QA PASS" in capsys.readouterr().out


def test_qa_fails_when_only_null_quota_windows(monkeypatch, capsys):
    """Fresh NEED_PROBE with empty Auto/API percentages must not QA PASS."""
    blind = {
        "agents": {
            "cursor": {
                "status": "unknown",
                "freshness": "fresh",
                "age_s": 1,
                "probe_state": "NEED_PROBE",
                "provider_windows": {
                    "auto": {
                        "window": "monthly",
                        "label": "Cursor Models (Auto)",
                        "used_pct": None,
                        "remaining_pct": None,
                        "resets_at": None,
                    },
                    "api": {
                        "window": "monthly",
                        "label": "Other Models (API)",
                        "used_pct": None,
                        "remaining_pct": None,
                        "resets_at": None,
                    },
                    "grok_bot": {
                        "window": "weekly",
                        "label": "Grok Bot",
                        "used_pct": None,
                        "remaining_pct": None,
                        "resets_at": None,
                    },
                },
            }
        },
        "api_accounts": {},
    }
    monkeypatch.setenv("DELEGATE_MONITOR_API", "http://fixture.invalid:8765/")
    monkeypatch.setattr(
        usage.urllib.request,
        "urlopen",
        lambda *a, **kw: io.StringIO(json.dumps(blind)),
    )
    assert usage.main(["qa"]) == 1
    assert "QA FAIL" in capsys.readouterr().out


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


def test_show_renders_codexbar_pace_line_under_window():
    """CodexBar-style pace prints under an allotment window well into its cycle."""
    now = datetime.now(UTC)
    resets = (now + timedelta(days=2)).isoformat().replace("+00:00", "Z")
    budget = {
        "source": "monitor-api",
        "agents": {
            "codex": {
                "status": "cool",
                "remaining_pct": 20,
                "codexbar": {
                    "freshness": "fresh",
                    "age_s": 1,
                    "windows": {
                        "secondary": {
                            "used_pct": 80.0,
                            "remaining_pct": 20.0,
                            "resets_at": resets,
                            "window_minutes": 10080,
                        }
                    },
                },
            }
        },
        "api_accounts": {},
    }
    text = usage.format_human(budget)
    assert "pace:" in text
    assert "Expected" in text and "% used" in text


def test_show_hides_pace_line_when_window_just_started():
    """CodexBar hides pace until enough of the window has elapsed (~1% weekly / ~3% session)."""
    now = datetime.now(UTC)
    resets = (now + timedelta(minutes=299)).isoformat().replace("+00:00", "Z")  # ~1min into a 5h window
    budget = {
        "source": "monitor-api",
        "agents": {
            "codex": {
                "status": "cool",
                "remaining_pct": 99,
                "codexbar": {
                    "freshness": "fresh",
                    "age_s": 1,
                    "windows": {
                        "primary": {
                            "used_pct": 1.0,
                            "remaining_pct": 99.0,
                            "resets_at": resets,
                            "window_minutes": 300,
                        }
                    },
                },
            }
        },
        "api_accounts": {},
    }
    text = usage.format_human(budget)
    assert "pace:" not in text


def test_show_pace_line_accepts_epoch_resets():
    now = datetime.now(UTC)
    epoch_resets = int((now + timedelta(days=1)).timestamp())
    budget = {
        "source": "monitor-api",
        "agents": {
            "codex": {
                "status": "cool",
                "remaining_pct": 40,
                "codexbar": {
                    "freshness": "fresh",
                    "age_s": 1,
                    "windows": {
                        "secondary": {
                            "used_pct": 60.0,
                            "remaining_pct": 40.0,
                            "resets_at": epoch_resets,
                            "window_minutes": 10080,
                        }
                    },
                },
            }
        },
        "api_accounts": {},
    }
    text = usage.format_human(budget)
    assert "pace:" in text


def test_gemini_fail_tip_points_at_agy_cli_not_api_key():
    """Gemini/AGY is a subscription CLI seat — tip must not imply a Gemini API key."""
    budget = {
        "source": "monitor-api",
        "agents": {
            "gemini": {
                "status": "unknown",
                "freshness": "unavailable",
                "error_kind": "provider",
                "last_failure_code": 403,
            }
        },
        "api_accounts": {},
    }
    text = usage.format_human(budget)
    assert "agy --prompt /usage" in text
    assert "OpenRouter + DeepSeek" in text
    assert "API key" in text
    assert "missing credential" not in text.lower()
    assert "no credential" not in text.lower()


@pytest.mark.parametrize(
    ("credit", "suffix"),
    [
        (None, ""),
        ({"state": "not_configured"}, ""),
        (
            {"state": "credit_balance_present", "allowed_models": ["gpt-6.1-sol", "gpt-6-luna"]},
            " | credit_balance_present: credit balance present; draw not verified by the router; "
            "usable for gpt-6.1-sol, gpt-6-luna only",
        ),
        (
            {"state": "credit_use_unconfirmed", "reason": "recent rate limit"},
            " | credit_use_unconfirmed: recent rate limit (plan state applies)",
        ),
        ({"state": "credits_exhausted"}, " | credits_exhausted: no reason given (plan state applies)"),
    ],
    ids=["unpublished", "not-configured", "present", "unconfirmed", "no-reason"],
)
def test_show_names_the_published_credit_state(budget, credit, suffix):
    """#9517: the credits line says when credits are usable and that the draw is unverified."""
    codex = budget["agents"]["codex"]
    codex["credit_balance"] = 62500.0
    if credit is not None:
        codex["credit"] = credit
    assert f"  credits: balance=62500.0{suffix}\n" in usage.format_human(budget) + "\n"


_MUSE_KNOWN_PAYLOAD = {
    "provider": "muse",
    "source": "oauth",
    "usage": {
        "primary": {"usedPercent": 10, "windowMinutes": 300, "resetsAt": "2026-10-13T18:00:00Z"},
        "secondary": {"usedPercent": 30, "windowMinutes": 10080, "resetsAt": "2026-10-20T00:00:00Z"},
    },
}
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
        lambda **kwargs: {
            **usage._attach_status_observations({"agents": {}, "api_accounts": {}, "source": "fixture"}),
            "agents": {"muse": usage._attach_status_observations({})["agents"]["muse"]},
        },
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
        f"muse | {status} | {rem_text} | fresh | 0.0 | {fail_text}",
        f"  quota: remaining={quota_text} headroom={quota_text} resets=unknown",
    ]
    if window is not None:
        lines.append(f"  primary (window): used={window['used_pct']:.1f}% rem={remaining:.1f}% resets=unknown")
    lines.extend(["", "Prepaid (USD; key cap remaining is not account balance)"])
    if remaining is None:
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
    lines.extend(["", "Prepaid (USD; key cap remaining is not account balance)"])
    if status == "unknown":
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
            lines.append("  quota: remaining=unknown headroom=unknown resets=unknown")
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


def test_usage_cli_shows_muse_known_window(monkeypatch, capsys):
    from scripts.api import state_router, subscription_usage

    _clear_muse_observation()

    def fetch(provider, *, timeout_s=None):
        if provider == "muse":
            return subscription_usage._muse_record_from_codexbar_payload(_MUSE_KNOWN_PAYLOAD)
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
        lambda **kwargs: {
            "agents": {
                "cursor": {
                    "status": "cool",
                    "freshness": "fresh",
                    "remaining_pct": 64.0,
                    "provider_windows": {
                        "auto": {
                            "label": "Cursor Models (Auto)",
                            "window": "monthly",
                            "used_pct": 36.0,
                            "remaining_pct": 64.0,
                            "resets_at": "2026-10-01T00:00:00Z",
                        }
                    },
                },
                "grok": {
                    "status": "cool",
                    "freshness": "fresh",
                    "remaining_pct": 80.0,
                    "codexbar": {
                        "freshness": "fresh",
                        "windows": {
                            "secondary": {
                                "used_pct": 20.0,
                                "remaining_pct": 80.0,
                                "resets_at": "2026-10-18T00:00:00Z",
                                "window_minutes": 10080,
                            }
                        },
                    },
                },
            },
            "api_accounts": {},
        },
    )
    assert usage.main(["show", "--fresh"]) == 0
    text = capsys.readouterr().out
    assert "muse | healthy | 70.0 | fresh |" in text
    assert "quota: remaining=70.0% headroom=70.0% resets=2026-10-20T00:00:00Z" in text
    assert "primary (5h): used=10.0% rem=90.0% resets=2026-10-13T18:00:00Z" in text
    assert "secondary (weekly): used=30.0% rem=70.0% resets=2026-10-20T00:00:00Z" in text
    assert "Cursor Models (Auto) (monthly): used=36.0% rem=64.0%" in text
    assert "secondary (weekly): used=20.0% rem=80.0% resets=2026-10-18T00:00:00Z" in text


def test_usage_cli_shows_muse_unsupported_as_unknown(monkeypatch, capsys):
    from scripts.api import state_router, subscription_usage

    _clear_muse_observation()

    def fetch(provider, *, timeout_s=None):
        if provider == "muse":
            return subscription_usage._muse_record_from_codexbar_payload(_MUSE_NULL_PAYLOAD)
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
    assert "muse | unknown | unknown | unavailable | unknown | unsupported/NO_QUOTA" in text
    assert "quota: remaining=unknown headroom=unknown resets=unknown" in text
    assert "70.0" not in text
    assert "100.0" not in text


def test_usage_cli_stale_and_rate_limit_muse_hide_headroom():
    from scripts.api import subscription_usage

    known = subscription_usage._muse_record_from_codexbar_payload(_MUSE_KNOWN_PAYLOAD)
    known["freshness"] = "stale_last_good"
    known["age_s"] = 800
    stale = usage.format_human(
        {
            "source": "fixture",
            "agents": {"muse": subscription_usage.project_muse_for_status(known)},
            "api_accounts": {},
        }
    )
    assert "muse | unknown | unknown | stale_last_good | 800 | -" in stale
    assert "quota: remaining=unknown headroom=unknown resets=unknown" in stale
    assert "70.0" not in stale

    limited = dict(known)
    limited["freshness"] = "fresh"
    limited["age_s"] = 1
    limited["error_kind"] = "rate_limit"
    limited["error_code"] = 429
    text = usage.format_human(
        {
            "source": "fixture",
            "agents": {"muse": subscription_usage.project_muse_for_status(limited)},
            "api_accounts": {},
        }
    )
    assert "muse | unknown | unknown | fresh | 1 | rate_limit/429" in text
    assert "quota: remaining=unknown headroom=unknown resets=unknown" in text
    assert "70.0" not in text


def _agy_split_payload() -> dict:
    return {
        "command": {
            "data": {
                "groups": [
                    {
                        "name": "Gemini Models",
                        "buckets": [
                            {
                                "window": "5h",
                                "remaining_fraction": 0.5,
                                "reset_time": "2026-10-13T18:00:00Z",
                            }
                        ],
                    },
                    {
                        "name": "Claude and GPT models",
                        "buckets": [
                            {
                                "window": "weekly",
                                "remaining_fraction": 0.25,
                                "reset_time": "2026-10-20T00:00:00Z",
                            }
                        ],
                    },
                ]
            }
        }
    }


def test_usage_cli_shows_agy_groups_beside_muse_cursor_and_grok(monkeypatch, capsys):
    import subprocess

    from scripts.api import state_router, subscription_usage

    _clear_muse_observation()
    subscription_usage._reset_agy_quota_observation_for_tests()
    monkeypatch.setattr(subscription_usage, "_agy_cli_bin", lambda: "/usr/bin/agy")

    def fake_run(argv, **kwargs):
        return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(_agy_split_payload()), stderr="")

    monkeypatch.setattr(subscription_usage.subprocess, "run", fake_run)
    probe = subscription_usage._probe_antigravity_native

    def fetch(provider, *, timeout_s=None):
        if provider in {"gemini", "antigravity"}:
            return probe(timeout_s=1)
        if provider == "muse":
            return subscription_usage._muse_record_from_codexbar_payload(_MUSE_KNOWN_PAYLOAD)
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
        lambda **kwargs: {
            "agents": {
                "cursor": {
                    "status": "cool",
                    "freshness": "fresh",
                    "remaining_pct": 64.0,
                    "provider_windows": {
                        "auto": {
                            "label": "Cursor Models (Auto)",
                            "window": "monthly",
                            "used_pct": 36.0,
                            "remaining_pct": 64.0,
                            "resets_at": "2026-10-01T00:00:00Z",
                        }
                    },
                },
                "grok": {
                    "status": "cool",
                    "freshness": "fresh",
                    "remaining_pct": 80.0,
                    "codexbar": {
                        "freshness": "fresh",
                        "windows": {
                            "secondary": {
                                "used_pct": 20.0,
                                "remaining_pct": 80.0,
                                "resets_at": "2026-10-18T00:00:00Z",
                                "window_minutes": 10080,
                            }
                        },
                    },
                },
            },
            "api_accounts": {},
        },
    )
    assert usage.main(["show", "--fresh"]) == 0
    text = capsys.readouterr().out
    assert "agy | healthy | unknown | fresh |" in text
    assert "Gemini Models (5h): used=50.0% rem=50.0% resets=2026-10-13T18:00:00Z" in text
    assert "Claude and GPT models (weekly): used=75.0% rem=25.0% resets=2026-10-20T00:00:00Z" in text
    assert "Gemini Models (weekly)" not in text
    assert "Claude and GPT models (5h)" not in text
    assert "muse | healthy | 70.0 | fresh |" in text
    assert "Cursor Models (Auto) (monthly): used=36.0% rem=64.0%" in text
    assert "secondary (weekly): used=20.0% rem=80.0% resets=2026-10-18T00:00:00Z" in text


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


def test_usage_cli_stale_and_rate_limit_agy_hide_headroom():
    from scripts.api import subscription_usage

    groups = subscription_usage._agy_quota_groups_from_payload(_agy_split_payload())
    stale = usage.format_human(
        {
            "source": "fixture",
            "agents": {
                "agy": subscription_usage.project_agy_for_status(
                    {
                        "quota_groups": groups,
                        "freshness": "stale_last_good",
                        "age_s": 800,
                        "error_kind": None,
                        "error_code": None,
                    }
                )
            },
            "api_accounts": {},
        }
    )
    assert "agy | unknown | unknown | stale_last_good | 800 | -" in stale
    assert "used=unknown rem=unknown resets=unknown" in stale
    assert "50.0" not in stale
    assert "25.0" not in stale
    assert "75.0" not in stale

    limited = usage.format_human(
        {
            "source": "fixture",
            "agents": {
                "agy": subscription_usage.project_agy_for_status(
                    {
                        "quota_groups": groups,
                        "freshness": "fresh",
                        "age_s": 1,
                        "error_kind": "rate_limit",
                        "error_code": 429,
                    }
                )
            },
            "api_accounts": {},
        }
    )
    assert "agy | unknown | unknown | fresh | 1 | rate_limit/429" in limited
    assert "50.0" not in limited
    assert "2026-10-13" not in limited
