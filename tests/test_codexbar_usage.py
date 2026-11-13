"""Tests for codexbar usage fetching, normalization, and routing budget warnings."""

from __future__ import annotations

import json
import sys
import threading
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.api import codexbar_usage as codexbar_usage_mod
from scripts.api import state_router
from scripts.api import subscription_usage as subscription_usage_mod
from scripts.api.codexbar_usage import _normalize_provider_data
from scripts.api.state_helpers import cache_invalidate
from scripts.api.subscription_usage import (
    compute_usage_pace,
    format_usage_pace_summary,
    pace_is_deficit,
    pace_is_visible,
)
from scripts.telemetry.cost_report import CostRecord


def _fake_private(monkeypatch, outcome=None, *, api_account=None):
    module = SimpleNamespace(
        probe_subscription=lambda *a, **kw: outcome,
        probe_api_account=lambda *a, **kw: api_account,
    )
    monkeypatch.setattr(subscription_usage_mod, "_private_usage", lambda: module)
    return module


@pytest.mark.parametrize("used_pct", [90.0, 98.99, 99.0, 100.0])
@pytest.mark.parametrize("usage_key", ["auto_used_pct", "weekly_used_pct"])
@pytest.mark.parametrize("samples", [1, 2])
def test_provider_trend_deficit_uses_subscription_near_cap_boundary(used_pct, usage_key, samples):
    history = [{usage_key: used_pct - 2.0}] if samples == 2 else []
    history.append({usage_key: used_pct})

    result = subscription_usage_mod.compute_provider_trend("cursor", history=history)

    assert result == {
        "trend": "up" if samples == 2 else "flat",
        "delta_auto_pct": 2.0 if samples == 2 else 0.0,
        "headroom_pct": pytest.approx(100.0 - used_pct),
        "deficit": used_pct >= 99.0,
        "samples": samples,
    }


# Real Claude usage JSON snapshot
CLAUDE_FIXTURE = """[
  {
    "pace": {
      "secondary": {
        "expectedUsedPercent": 47,
        "stage": "farAhead",
        "deltaPercent": 27,
        "summary": "27% in deficit | Expected 47% used | Runs out in 1d 3h",
        "etaSeconds": 100217,
        "willLastToReset": false
      },
      "primary": {
        "expectedUsedPercent": 61,
        "stage": "farBehind",
        "deltaPercent": -54,
        "summary": "54% in reserve | Expected 61% used | Lasts until reset",
        "willLastToReset": true
      }
    },
    "provider": "claude",
    "version": "2.1.205",
    "source": "web",
    "usage": {
      "updatedAt": "2026-07-09T14:13:52Z",
      "primary": {
        "windowMinutes": 300,
        "resetsAt": "2026-07-09T16:09:59Z",
        "resetDescription": "Jul 9 at 6:09PM",
        "usedPercent": 7
      },
      "tertiary": null,
      "accountOrganization": "account-a@example.invalid's Organization",
      "accountEmail": "account-a@example.invalid",
      "providerCost": {
        "period": "Monthly cap",
        "updatedAt": "2026-07-09T14:13:51Z",
        "limit": 20,
        "currencyCode": "EUR",
        "used": 0
      },
      "identity": {
        "loginMethod": "Claude Max 20x",
        "providerID": "claude",
        "accountOrganization": "account-a@example.invalid's Organization",
        "accountEmail": "account-a@example.invalid"
      },
      "secondary": {
        "windowMinutes": 10080,
        "resetsAt": "2026-07-13T06:59:59Z",
        "resetDescription": "Jul 13 at 8:59AM",
        "usedPercent": 74
      },
      "loginMethod": "Claude Max 20x",
      "extraRateWindows": [
        {
          "title": "Daily Routines",
          "window": {
            "windowMinutes": 10080,
            "usedPercent": 0
          },
          "id": "claude-routines"
        },
        {
          "title": "Fable only",
          "id": "claude-weekly-scoped-fable",
          "window": {
            "resetsAt": "2026-07-13T06:59:59Z",
            "usedPercent": 99,
            "windowMinutes": 10080
          }
        }
      ]
    }
  }
]"""

# Real Codex usage JSON snapshot
CODEX_FIXTURE = """[
  {
    "usage": {
      "identity": {
        "accountEmail": "account-a@example.invalid",
        "loginMethod": "Pro 20x",
        "providerID": "codex"
      },
      "primary": {
        "usedPercent": 11,
        "resetsAt": "2026-07-09T16:57:07Z",
        "resetDescription": "6:57 PM",
        "windowMinutes": 300
      },
      "dataConfidence": "high",
      "tertiary": null,
      "extraRateWindows": [],
      "accountEmail": "account-a@example.invalid",
      "codexResetCredits": 0,
      "updatedAt": "2026-07-09T13:49:49Z",
      "loginMethod": "Pro 20x",
      "secondary": {
        "usedPercent": 62,
        "resetsAt": "2026-07-12T19:26:00Z",
        "resetDescription": "Jul 12 at 9:26 PM",
        "windowMinutes": 10080
      }
    },
    "openaiDashboard": {
      "primaryLimit": {
        "windowMinutes": 300,
        "resetDescription": "Resets 6:57 PM",
        "usedPercent": 9
      },
      "secondaryLimit": {
        "windowMinutes": 10080,
        "resetsAt": "2026-07-12T19:26:49Z",
        "resetDescription": "Resets Jul 12, 2026 9:26 PM",
        "usedPercent": 62
      },
      "codeReviewLimit": {
        "usedPercent": 9
      },
      "creditsRemaining": 0,
      "updatedAt": "2026-07-09T13:49:49Z",
      "accountPlan": "Pro 20x"
    },
    "source": "oauth",
    "pace": {
      "primary": {
        "expectedUsedPercent": 46,
        "willLastToReset": true,
        "deltaPercent": -36,
        "summary": "36% in reserve | Expected 46% used | Lasts until reset | 1.5x headroom",
        "stage": "farBehind"
      },
      "secondary": {
        "expectedUsedPercent": 54,
        "willLastToReset": false,
        "deltaPercent": 8,
        "summary": "8% in deficit | Expected 54% used | Runs out in 2d 7h",
        "etaSeconds": 200345,
        "stage": "ahead"
      }
    },
    "credits": {
      "events": [],
      "remaining": 0,
      "updatedAt": "2026-07-09T14:13:57Z"
    },
    "provider": "codex"
  }
]"""


def test_normalize_claude_shape():
    raw_list = json.loads(CLAUDE_FIXTURE)
    res = _normalize_provider_data("claude", raw_list[0])

    assert res["lane"] == "claude"
    assert res["primary_used_pct"] == 7.0
    assert res["weekly_used_pct"] == 74.0
    assert res["primary_remaining_pct"] == 93.0
    assert res["weekly_remaining_pct"] == 26.0
    assert res["monthly_cap_usd"] == 20.0
    assert res["monthly_used_usd"] == 0.0
    assert res["weekly_resets_at"] == "2026-07-13T06:59:59Z"
    assert res["weekly_pace_delta_pct"] == 27.0
    assert res["will_last_to_reset"] is False
    assert "27% in deficit" in res["pace_summary"]
    assert res["source"] == "web"
    assert res["fetched_at"] is not None


def test_normalize_cursor_three_windows():
    """Cursor Pro+ exposes Total/Auto/API as primary/secondary/tertiary."""
    raw = {
        "provider": "cursor",
        "source": "web",
        "usage": {
            "primary": {
                "usedPercent": 44.7,
                "resetsAt": "2026-08-01T09:58:38Z",
                "windowMinutes": 44640,
                "resetDescription": "Resets Aug 1",
            },
            "secondary": {
                "usedPercent": 36.0,
                "resetsAt": "2026-08-01T09:58:38Z",
                "windowMinutes": 44640,
            },
            "tertiary": {
                "usedPercent": 100.0,
                "resetsAt": "2026-08-01T09:58:38Z",
                "windowMinutes": 44640,
            },
        },
    }
    res = _normalize_provider_data("cursor", raw)
    assert res["lane"] == "cursor"
    assert res["primary_used_pct"] == 36.0
    assert res["secondary_used_pct"] == 36.0
    assert res["tertiary_used_pct"] == 100.0
    # Burn/status tracks Auto monthly pool, not Total primary.
    assert res["weekly_used_pct"] is None
    assert res["weekly_remaining_pct"] is None
    assert res["provider_windows"]["auto"]["used_pct"] == 36.0
    assert res["provider_windows"]["api"]["used_pct"] == 100.0
    assert res["windows"]["secondary"]["label"] == "Cursor Models (Auto)"
    assert res["windows"]["tertiary"]["label"] == "Other Models (API)"
    assert res["windows"]["tertiary"]["used_pct"] == 100.0
    assert "grok_bot" in res["provider_windows"]
    assert res["provider_windows"]["grok_bot"]["window"] == "weekly"
    assert res["weekly_resets_at"] == "2026-08-01T09:58:38Z"
    assert res["windows"]["secondary"]["used_pct"] == 36.0


def test_normalize_codex_shape():
    raw_list = json.loads(CODEX_FIXTURE)
    res = _normalize_provider_data("codex", raw_list[0])

    assert res["lane"] == "codex"
    assert res["primary_used_pct"] in (9.0, 11.0)
    assert res["weekly_used_pct"] == 62.0
    assert res["weekly_resets_at"] in ("2026-07-12T19:26:49Z", "2026-07-12T19:26:00Z")
    assert res["weekly_pace_delta_pct"] == 8.0
    assert res["will_last_to_reset"] is False
    assert "8% in deficit" in res["pace_summary"]


def test_deficit_signal_states():
    # 1. Hot status via will_last_to_reset=False
    raw_claude = json.loads(CLAUDE_FIXTURE)[0]
    res_claude = _normalize_provider_data("claude", raw_claude)

    def get_status(cb_data):
        pace = {
            "delta_pct": cb_data.get("weekly_pace_delta_pct"),
            "will_last_to_reset": cb_data.get("will_last_to_reset"),
            "expected_pct": cb_data.get("weekly_expected_pct"),
        }
        return state_router._status_from_weekly_used(cb_data["weekly_used_pct"], pace)

    assert get_status(res_claude) == "hot"

    # 2. Cool status
    raw_claude["pace"]["secondary"]["willLastToReset"] = True
    raw_claude["pace"]["secondary"]["deltaPercent"] = -10.0
    raw_claude["usage"]["secondary"]["usedPercent"] = 35.0
    res_cool = _normalize_provider_data("claude", raw_claude)
    assert get_status(res_cool) == "cool"

    # 3. Near cap status
    raw_claude["usage"]["secondary"]["usedPercent"] = 99.0
    res_near_cap = _normalize_provider_data("claude", raw_claude)
    assert get_status(res_near_cap) == "near_cap"


def test_routing_budget_surfaces_deficit_warnings(monkeypatch):
    # Mock get_provider_usage_data to return a deficit lane
    mock_data = {
        "claude": {
            "lane": "claude",
            "primary_used_pct": 10.0,
            "weekly_used_pct": 85.0,
            "monthly_cap_usd": 20.0,
            "monthly_used_usd": 5.0,
            "weekly_resets_at": "2026-07-13T06:59:59Z",
            "weekly_pace_delta_pct": 15.0,
            "will_last_to_reset": False,
            "pace_summary": "15% in deficit",
            "source": "codexbar",
            "fetched_at": "2026-07-09T14:13:52Z",
            "stale": False,
            "age_s": 10.0,
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
            "fetched_at": "2026-07-09T14:13:52Z",
            "stale": False,
            "age_s": 10.0,
        },
    }

    def mock_usage(provider):
        if provider in mock_data:
            return mock_data[provider]
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

    monkeypatch.setattr(state_router, "get_provider_usage_data", mock_usage)
    monkeypatch.setattr(state_router, "load_cost_records", lambda **_kwargs: [])
    monkeypatch.setattr(
        state_router,
        "summarize_fleet_burn",
        lambda agent, **kwargs: {
            "source": "agent_runtime_jsonl",
            "agent": agent,
            "windows": {"7d": {"counts": {"total": 0}, "hours": 0.0}},
        },
    )
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
            "fetched_at": "2026-07-09T14:13:52Z",
        },
    )

    now = datetime(2026, 7, 9, 16, 13, tzinfo=UTC)
    res = state_router.compute_routing_budget(now)

    assert "claude" in res["agents"]
    assert res["agents"]["claude"]["status"] == "hot"
    assert res["agents"]["codex"]["status"] == "cool"

    # Check that deficit warning was generated for claude, and that it quotes
    # BOTH windows: the weekly-pace deficit AND the 5h reserve (weekly-only
    # wording misled toward over-restriction — user correction 2026-07-09).
    deficit_warnings = [w for w in res["recommendation"]["warnings"] if "lane claude is in deficit" in w]
    assert deficit_warnings
    assert "5h window 10% used" in deficit_warnings[0]
    assert "90% reserve" in deficit_warnings[0]
    assert "weekly-pace signal" in deficit_warnings[0]


@pytest.mark.parametrize("api_used", [90.0, 98.99, 99.0, 100.0])
def test_routing_budget_cursor_burns_auto_and_warns_on_api(monkeypatch, api_used):
    """Cursor burn tracks Auto monthly pool; exhausted API allotment emits advisory warning."""
    cursor_row = {
        "lane": "cursor",
        "login_state": "authenticated",
        "probe_state": "healthy",
        "primary_used_pct": 36.0,
        "primary_remaining_pct": 64.0,
        "secondary_used_pct": 36.0,
        "secondary_remaining_pct": 64.0,
        "tertiary_used_pct": api_used,
        "tertiary_remaining_pct": 100.0 - api_used,
        "weekly_used_pct": None,
        "weekly_remaining_pct": None,
        "provider_windows": {
            "auto": {
                "window": "monthly",
                "label": "Auto",
                "used_pct": 36.0,
                "remaining_pct": 64.0,
                "resets_at": "2026-08-01T09:58:38Z",
            },
            "api": {
                "window": "monthly",
                "label": "API",
                "used_pct": api_used,
                "remaining_pct": 100.0 - api_used,
                "resets_at": "2026-08-01T09:58:38Z",
            },
        },
        "windows": {
            "secondary": {
                "used_pct": 36.0,
                "remaining_pct": 64.0,
                "resets_at": "2026-08-01T09:58:38Z",
                "window_minutes": 44640,
                "label": "Auto",
            },
            "tertiary": {
                "used_pct": api_used,
                "remaining_pct": 100.0 - api_used,
                "resets_at": "2026-08-01T09:58:38Z",
                "window_minutes": 44640,
                "label": "API",
            },
        },
        "monthly_cap_usd": None,
        "monthly_used_usd": None,
        "weekly_resets_at": "2026-08-01T09:58:38Z",
        "weekly_pace_delta_pct": -20.0,
        "will_last_to_reset": True,
        "pace_summary": "-20% pace delta",
        "source": "cursor_native",
        "fetched_at": "2026-07-21T19:00:00Z",
        "stale": False,
        "age_s": 1.0,
        "status": "cool",
        "auth_error": None,
    }

    def mock_usage(provider):
        if provider == "cursor":
            return dict(cursor_row)
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

    monkeypatch.setattr(state_router, "get_provider_usage_data", mock_usage)
    monkeypatch.setattr(state_router, "get_cursor_lane_usage", lambda **kwargs: dict(cursor_row))
    monkeypatch.setattr(state_router, "load_cost_records", lambda **_kwargs: [])
    monkeypatch.setattr(
        state_router,
        "summarize_fleet_burn",
        lambda agent, **kwargs: {
            "source": "agent_runtime_jsonl",
            "agent": agent,
            "windows": {"7d": {"counts": {"total": 0}, "hours": 0.0}},
        },
    )
    monkeypatch.setattr(
        state_router,
        "persist_provider_snapshot",
        lambda lane, snapshot: {"trend": "flat", "samples": 1},
    )

    res = state_router.compute_routing_budget(datetime(2026, 7, 21, 19, 0, tzinfo=UTC))
    cursor = res["agents"]["cursor"]
    assert cursor["burn_pct_7d"] == 36.0
    assert cursor["status"] == "cool"
    assert cursor["provider_windows"]["auto"]["used_pct"] == 36.0
    assert cursor["provider_windows"]["api"]["used_pct"] == api_used
    api_warnings = [w for w in res["recommendation"]["warnings"] if "API/on-demand" in w]
    assert bool(api_warnings) is (api_used >= 99.0)
    if api_warnings:
        assert f"{api_used:.0f}% used" in api_warnings[0]


def test_monthly_window_only_does_not_mislabel_weekly_used_pct():
    """Monthly-only limit windows must not populate weekly_used_pct via first-over-300 fallback."""
    payload = {
        "usage": {
            "primary": {
                "windowMinutes": 300,
                "usedPercent": 10,
                "resetsAt": "2026-07-09T16:09:59Z",
            },
            "tertiary": {
                "windowMinutes": 43200,
                "usedPercent": 75,
                "resetsAt": "2026-08-08T06:59:59Z",
            },
        },
        "openaiDashboard": {},
    }

    res = _normalize_provider_data("codex", payload)

    assert res["primary_used_pct"] == 10.0
    assert res["weekly_used_pct"] != 75.0
    assert res["weekly_used_pct"] == 10.0


# Kimi healthy usage snapshot (weekly + primary windows present)
KIMI_HEALTHY_FIXTURE = """[
  {
    "provider": "kimi",
    "source": "oauth",
    "usage": {
      "primary": {
        "windowMinutes": 300,
        "usedPercent": 12,
        "resetsAt": "2026-07-17T18:00:00Z"
      },
      "secondary": {
        "windowMinutes": 10080,
        "usedPercent": 40,
        "resetsAt": "2026-07-20T18:00:00Z"
      }
    },
    "pace": {
      "secondary": {
        "deltaPercent": -5,
        "willLastToReset": true,
        "summary": "5% in reserve | Expected 45% used"
      }
    }
  }
]"""


# Kimi credential/provider error snapshot (the 2026-07-17 incident shape)
KIMI_ERROR_FIXTURE = """[
  {
    "source": "auto",
    "provider": "kimi",
    "error": {
      "code": 1,
      "message": "Kimi Code CLI credential is expired, please re-authenticate",
      "kind": "provider"
    }
  }
]"""


def test_normalize_kimi_healthy_shape():
    """Healthy kimi payload yields a lane row with window numbers."""
    raw = json.loads(KIMI_HEALTHY_FIXTURE)[0]
    res = _normalize_provider_data("kimi", raw)

    assert res["lane"] == "kimi"
    assert res["primary_used_pct"] == 12.0
    assert res["weekly_used_pct"] == 40.0
    assert res["weekly_resets_at"] == "2026-07-20T18:00:00Z"
    assert res["will_last_to_reset"] is True
    assert res["source"] == "oauth"


def test_kimi_provider_error_surfaces_unknown(monkeypatch):
    """Credential/provider error -> status='unknown' + auth_error, never zero usage."""
    _fake_private(
        monkeypatch,
        {"outcome": "error", "error": {"kind": "provider", "code": 401, "message": "Kimi credential rejected"}},
    )
    codexbar_usage_mod._last_good_data.pop("kimi", None)

    res = codexbar_usage_mod.fetch_codexbar_usage("kimi", timeout_s=1.0)

    assert res is not None
    assert res["lane"] == "kimi"
    assert res["status"] in ("unavailable", "unknown")
    assert res["weekly_used_pct"] is None
    assert res["primary_used_pct"] is None
    assert "credential" in (res["auth_error"] or "").lower() or "rejected" in (res["auth_error"] or "").lower()
    assert res["error_kind"] == "provider"
    assert res["error_code"] == 401


def test_healthy_record_carries_error_shape_defaults():
    """Healthy and error records share one key shape (review-5386 F2)."""
    raw_list = json.loads(KIMI_HEALTHY_FIXTURE)
    res = _normalize_provider_data("kimi", raw_list[0])
    assert res["status"] == "healthy"
    assert res["auth_error"] is None
    assert res["error_kind"] is None
    assert res["error_code"] is None


def test_missing_credentials_returns_need_login(monkeypatch):
    """Missing native credentials must surface NEED_LOGIN, not missing_binary."""
    _fake_private(
        monkeypatch,
        {
            "outcome": "error",
            "error": {"kind": "need_login", "code": "NEED_LOGIN", "message": "Codex OAuth credentials unavailable"},
        },
    )
    codexbar_usage_mod._last_good_data.pop("codex", None)

    res = codexbar_usage_mod.fetch_codexbar_usage("codex", timeout_s=1.0)
    assert res["status"] == "unavailable"
    assert res["error_kind"] == "need_login"
    assert res["probe_state"] == "NEED_LOGIN"
    assert "credential" in res["auth_error"].lower()


def test_native_probe_unavailable_missing_credentials(monkeypatch):
    """Regression: missing credentials must not masquerade as a healthy 0% lane."""
    _fake_private(
        monkeypatch,
        {
            "outcome": "error",
            "error": {"kind": "need_login", "code": "NEED_LOGIN", "message": "Codex OAuth credentials unavailable"},
        },
    )
    codexbar_usage_mod._last_good_data.pop("codex", None)

    res = codexbar_usage_mod.fetch_codexbar_usage("codex", timeout_s=1.0)
    assert res["status"] == "unavailable"
    assert res["error_kind"] == "need_login"
    assert "credential" in res["auth_error"].lower()

    now = datetime(2026, 5, 13, 20, 30, tzinfo=UTC)
    record = CostRecord(
        path=Path("fixture-meta.json"),
        level="a1",
        slug="fixture",
        phase="write",
        agent="codex",
        model="fixture-model",
        model_source="stored",
        ok=True,
        timestamp=now.isoformat(),
        mtime=now,
        prompt_chars=1,
        response_chars=1,
        prompt_tokens_est=1,
        response_tokens_est=1,
        prompt_tokens_source="stored",
        response_tokens_source="stored",
        rate_model="fixture-model",
        used_default_rate=False,
        cost_usd_est=500.0,
    )
    monkeypatch.setattr(state_router, "load_cost_records", lambda **_kwargs: [record])
    monkeypatch.setattr(state_router, "get_provider_usage_data", lambda p: res if p == "codex" else None)

    data = state_router.compute_routing_budget(now)
    assert data["agents"]["codex"]["status"] == "warm"
    assert data["agents"]["codex"]["burn_pct_7d"] is not None
    assert data["agents"]["codex"]["remaining_pct"] is not None
    assert data["agents"]["codex"]["codexbar"]["status"] == "unavailable"
    assert data["agents"]["codex"]["codexbar"]["error_kind"] == "need_login"


def test_codexbar_unavailable_timeout(monkeypatch):
    """Regression test for timeout: must surface status='unavailable' and auth_error."""
    _fake_private(
        monkeypatch,
        {"outcome": "error", "error": {"kind": "fetch_error", "code": "FETCH_ERROR", "message": "request timed out"}},
    )
    codexbar_usage_mod._last_good_data.pop("codex", None)

    res = codexbar_usage_mod.fetch_codexbar_usage("codex", timeout_s=1.0)
    assert res["status"] == "unavailable"
    assert res["error_kind"] == "fetch_error"
    assert "timed out" in res["auth_error"].lower()

    now = datetime(2026, 5, 13, 20, 30, tzinfo=UTC)
    record = CostRecord(
        path=Path("fixture-meta.json"),
        level="a1",
        slug="fixture",
        phase="write",
        agent="codex",
        model="fixture-model",
        model_source="stored",
        ok=True,
        timestamp=now.isoformat(),
        mtime=now,
        prompt_chars=1,
        response_chars=1,
        prompt_tokens_est=1,
        response_tokens_est=1,
        prompt_tokens_source="stored",
        response_tokens_source="stored",
        rate_model="fixture-model",
        used_default_rate=False,
        cost_usd_est=500.0,
    )
    monkeypatch.setattr(state_router, "load_cost_records", lambda **_kwargs: [record])
    monkeypatch.setattr(state_router, "get_provider_usage_data", lambda p: res if p == "codex" else None)

    data = state_router.compute_routing_budget(now)
    assert data["agents"]["codex"]["status"] == "warm"
    assert data["agents"]["codex"]["burn_pct_7d"] is not None
    assert data["agents"]["codex"]["remaining_pct"] is not None
    assert data["agents"]["codex"]["codexbar"]["status"] == "unavailable"
    assert data["agents"]["codex"]["codexbar"]["error_kind"] == "fetch_error"


def test_codexbar_unavailable_malformed_json(monkeypatch):
    """Regression test for malformed JSON: must surface status='unavailable' and auth_error."""
    _fake_private(
        monkeypatch,
        {
            "outcome": "error",
            "error": {"kind": "fetch_error", "code": "FETCH_ERROR", "message": "Native probe failed: JSONDecodeError"},
        },
    )
    codexbar_usage_mod._last_good_data.pop("codex", None)

    res = codexbar_usage_mod.fetch_codexbar_usage("codex", timeout_s=1.0)
    assert res["status"] == "unavailable"
    assert res["error_kind"] == "fetch_error"

    now = datetime(2026, 5, 13, 20, 30, tzinfo=UTC)
    record = CostRecord(
        path=Path("fixture-meta.json"),
        level="a1",
        slug="fixture",
        phase="write",
        agent="codex",
        model="fixture-model",
        model_source="stored",
        ok=True,
        timestamp=now.isoformat(),
        mtime=now,
        prompt_chars=1,
        response_chars=1,
        prompt_tokens_est=1,
        response_tokens_est=1,
        prompt_tokens_source="stored",
        response_tokens_source="stored",
        rate_model="fixture-model",
        used_default_rate=False,
        cost_usd_est=500.0,
    )
    monkeypatch.setattr(state_router, "load_cost_records", lambda **_kwargs: [record])
    monkeypatch.setattr(state_router, "get_provider_usage_data", lambda p: res if p == "codex" else None)

    data = state_router.compute_routing_budget(now)
    assert data["agents"]["codex"]["status"] == "warm"
    assert data["agents"]["codex"]["burn_pct_7d"] is not None
    assert data["agents"]["codex"]["remaining_pct"] is not None
    assert data["agents"]["codex"]["codexbar"]["status"] == "unavailable"
    assert data["agents"]["codex"]["codexbar"]["error_kind"] == "fetch_error"


def test_codexbar_unavailable_unparseable_schema(monkeypatch):
    """Regression test for empty schema: must surface status='unavailable'."""
    _fake_private(
        monkeypatch,
        {
            "outcome": "error",
            "error": {
                "kind": "unparseable_schema",
                "code": "UNPARSEABLE_SCHEMA",
                "message": "Codex usage payload missing rate windows",
            },
        },
    )
    codexbar_usage_mod._last_good_data.pop("codex", None)

    res = codexbar_usage_mod.fetch_codexbar_usage("codex", timeout_s=1.0)
    assert res["status"] == "unavailable"

    now = datetime(2026, 5, 13, 20, 30, tzinfo=UTC)
    record = CostRecord(
        path=Path("fixture-meta.json"),
        level="a1",
        slug="fixture",
        phase="write",
        agent="codex",
        model="fixture-model",
        model_source="stored",
        ok=True,
        timestamp=now.isoformat(),
        mtime=now,
        prompt_chars=1,
        response_chars=1,
        prompt_tokens_est=1,
        response_tokens_est=1,
        prompt_tokens_source="stored",
        response_tokens_source="stored",
        rate_model="fixture-model",
        used_default_rate=False,
        cost_usd_est=500.0,
    )
    monkeypatch.setattr(state_router, "load_cost_records", lambda **_kwargs: [record])
    monkeypatch.setattr(state_router, "get_provider_usage_data", lambda p: res if p == "codex" else None)

    data = state_router.compute_routing_budget(now)
    assert data["agents"]["codex"]["status"] == "warm"
    assert data["agents"]["codex"]["burn_pct_7d"] is not None
    assert data["agents"]["codex"]["remaining_pct"] is not None
    assert data["agents"]["codex"]["codexbar"]["status"] == "unavailable"
    assert data["agents"]["codex"]["codexbar"]["error_kind"] == "unparseable_schema"


def test_get_cursor_lane_usage_is_cache_only_on_http_path(monkeypatch):
    """HTTP reads must not block on live Cursor probes."""
    subscription_usage_mod._reset_cursor_usage_state_for_tests()
    probe_calls = {"login": 0, "windows": 0}

    def _login(**kwargs):
        probe_calls["login"] += 1
        return {
            "lane": "cursor",
            "login_state": "authenticated",
            "is_authenticated": True,
            "fetched_at": "2026-08-26T12:00:00Z",
        }

    def _windows(**kwargs):
        probe_calls["windows"] += 1
        return {
            "lane": "cursor",
            "probe_state": "healthy",
            "login_state": "authenticated",
            "provider_windows": {
                "auto": {
                    "window": "monthly",
                    "label": "Auto",
                    "used_pct": 12.0,
                    "remaining_pct": 88.0,
                    "resets_at": None,
                },
                "api": {"window": "monthly", "label": "API", "used_pct": 5.0, "remaining_pct": 95.0, "resets_at": None},
            },
            "fetched_at": "2026-08-26T12:00:00Z",
        }

    monkeypatch.setattr(codexbar_usage_mod, "probe_cursor_login", _login)
    monkeypatch.setattr(codexbar_usage_mod, "probe_cursor_provider_windows", _windows)
    monkeypatch.setenv("CODEXBAR_ON_DEMAND_REFRESH", "0")

    result = codexbar_usage_mod.get_cursor_lane_usage()
    assert result["freshness"] == "unavailable"
    assert probe_calls == {"login": 0, "windows": 0}

    codexbar_usage_mod._record_cursor_probe_result(_windows())
    probe_calls["windows"] = 0
    cached = codexbar_usage_mod.get_cursor_lane_usage()
    assert cached["freshness"] == "fresh"
    assert cached["provider_windows"]["auto"]["used_pct"] == 12.0
    assert probe_calls == {"login": 0, "windows": 0}


@pytest.mark.parametrize("invalidate_cache", [False, True])
def test_cursor_state_reset_prevents_preceding_probe_leaking_into_http_read(monkeypatch, invalidate_cache):
    """A preceding probe must leave neither a fresh cache nor last-good fallback."""
    monkeypatch.setenv("CODEXBAR_ON_DEMAND_REFRESH", "0")
    probe = {"lane": "cursor", "probe_state": "healthy", "fetched_at": "2026-09-03T12:05:00Z"}
    assert subscription_usage_mod._record_cursor_probe_result(probe) is True
    assert subscription_usage_mod._cursor_last_good is not None
    if invalidate_cache:
        cache_invalidate(subscription_usage_mod.CURSOR_CACHE_KEY)
    assert subscription_usage_mod.get_cursor_lane_usage()["freshness"] == (
        "stale_last_good" if invalidate_cache else "fresh"
    )

    subscription_usage_mod._reset_cursor_usage_state_for_tests()

    assert subscription_usage_mod._cursor_last_good is None
    assert subscription_usage_mod.cache_get_with_age(subscription_usage_mod.CURSOR_CACHE_KEY, ttl=600) is None
    assert subscription_usage_mod.get_cursor_lane_usage()["freshness"] == "unavailable"


def test_failed_refresh_never_poison_last_known_good_capacity(monkeypatch):
    """The two-second timeout regression keeps the prior usable capacity."""
    provider = "codex"
    cache_invalidate("codexbar_usage:")
    codexbar_usage_mod._last_good_data.pop(provider, None)
    codexbar_usage_mod._last_failure_data.pop(provider, None)
    healthy = _normalize_provider_data(provider, json.loads(CODEX_FIXTURE)[0])
    timeout = codexbar_usage_mod._normalize_provider_error(
        provider,
        {"kind": "timeout", "code": "TIMEOUT", "message": "timed out after 2s"},
    )
    results = iter([healthy, timeout])
    monkeypatch.setattr(subscription_usage_mod, "fetch_provider_usage", lambda *_args, **_kwargs: next(results))

    assert provider in codexbar_usage_mod.refresh_provider_usage_data([provider], timeout_s=2.0)
    # Expire the short TTL to force use of the LKG branch rather than the
    # still-valid cache entry. The timeout must remain diagnostic-only.
    cache_invalidate(f"codexbar_usage:{provider}")
    assert codexbar_usage_mod.refresh_provider_usage_data([provider], timeout_s=2.0) == {}

    result = codexbar_usage_mod.get_provider_usage_data(provider)
    assert result["freshness"] == "stale_last_good"
    assert result["weekly_used_pct"] == 62.0
    assert result["failure_kind"] == "timeout"
    assert result["last_failure_at"]


def test_malformed_or_provider_failure_is_unavailable_without_lkg(monkeypatch):
    provider = "kimi"
    cache_invalidate("codexbar_usage:")
    codexbar_usage_mod._last_good_data.pop(provider, None)
    codexbar_usage_mod._last_failure_data.pop(provider, None)
    malformed = codexbar_usage_mod._normalize_provider_error(
        provider,
        {"kind": "malformed_json", "code": "MALFORMED_JSON", "message": "malformed"},
    )
    monkeypatch.setattr(subscription_usage_mod, "fetch_provider_usage", lambda *_args, **_kwargs: malformed)

    assert codexbar_usage_mod.refresh_provider_usage_data([provider], timeout_s=2.0) == {}
    result = codexbar_usage_mod.get_provider_usage_data(provider)
    assert result["freshness"] == "unavailable"
    assert result["failure_kind"] == "malformed_json"
    assert result["last_failure_at"]


def test_default_refresh_timeout_floor_matches_real_cli_latency(monkeypatch):
    """Regression: the prior 2.0s default never let the claude lane's CLI
    probe complete (live-measured 2026-08-04: `codexbar usage --json
    --provider claude` took ~17s twice in a row, its own dashboard-fetch
    latency, not a hang), which painted a healthy lane as capacity-unavailable
    — the routing-budget false-red this dispatch fixes."""
    monkeypatch.delenv("CODEXBAR_REFRESH_TIMEOUT_S", raising=False)
    assert codexbar_usage_mod._codexbar_refresh_timeout_s() == codexbar_usage_mod.DEFAULT_CODEXBAR_REFRESH_TIMEOUT_S
    # Comfortable margin above the live-measured ~17s worst case.
    assert codexbar_usage_mod.DEFAULT_CODEXBAR_REFRESH_TIMEOUT_S >= 20.0


def test_timeout_failure_kind_maps_to_fail_open_reviewer_status():
    """Ties this fix to the existing fail-open classification (reviewer_resolver
    operator note 2026-08-03: 'red probe must not ban CF lanes'): a CLI timeout
    must produce status='unavailable', which reviewer_resolver treats as missing
    evidence, never as a dead/unhealthy lane."""
    from scripts.review.reviewer_resolver import _HEALTH_ALIASES

    timeout_result = codexbar_usage_mod._normalize_provider_error(
        "claude",
        {"kind": "timeout", "code": "TIMEOUT", "message": "Native probe timed out after 25.0s"},
    )
    assert timeout_result["status"] == "unavailable"
    assert timeout_result["error_kind"] == "timeout"
    assert _HEALTH_ALIASES[timeout_result["status"]] is None  # fail-open, not "unhealthy"


def test_scheduler_running_skips_on_demand_refresh(monkeypatch):
    """When the API scheduler owns refresh, a cache miss must not spawn another CLI fan-out."""
    provider = "cursor"
    cache_invalidate("codexbar_usage:")
    codexbar_usage_mod._last_good_data.pop(provider, None)
    codexbar_usage_mod._last_failure_data.pop(provider, None)
    kicked = []
    monkeypatch.setattr(codexbar_usage_mod, "_scheduler_is_running", lambda: True)
    monkeypatch.setattr(
        codexbar_usage_mod,
        "trigger_background_refresh",
        lambda: kicked.append("refresh"),
    )
    result = codexbar_usage_mod.get_provider_usage_data(provider)
    assert kicked == []
    assert result["freshness"] == "unavailable"


def test_periodic_refresh_runs_immediately_then_stops(monkeypatch):
    runs = threading.Event()
    release = threading.Event()
    claude_ran = threading.Event()

    def fake_run() -> None:
        runs.set()
        release.wait(timeout=2.0)

    def fake_claude() -> None:
        claude_ran.set()

    monkeypatch.setenv("CODEXBAR_PERIODIC_REFRESH", "1")
    monkeypatch.setenv("CODEXBAR_REFRESH_INTERVAL_S", "30")
    monkeypatch.setattr(subscription_usage_mod, "_run_all_refreshes", fake_run)
    monkeypatch.setattr(subscription_usage_mod, "_refresh_claude_accounts_live", fake_claude)
    monkeypatch.setattr(subscription_usage_mod, "_scheduler_thread", None)
    monkeypatch.setattr(subscription_usage_mod, "_claude_account_scheduler_thread", None)
    try:
        codexbar_usage_mod.start_periodic_refresh(run_immediately=True)
        assert claude_ran.wait(timeout=1.0)
        assert runs.wait(timeout=1.0)
        # The account probe is not waiting on the still-blocked provider pass.
        assert claude_ran.is_set()
        assert codexbar_usage_mod.scheduler_status()["scheduler_running"] is True
        assert codexbar_usage_mod.scheduler_status()["cache_ttl_s"] == 810.0
        assert subscription_usage_mod.DEFAULT_CODEXBAR_CACHE_TTL_S == 810.0
        assert subscription_usage_mod.DEFAULT_CODEXBAR_CACHE_TTL_S > (
            subscription_usage_mod.DEFAULT_CODEXBAR_REFRESH_INTERVAL_S + 60.0
        )
    finally:
        release.set()
        codexbar_usage_mod.stop_periodic_refresh(join_timeout_s=1.0)
    assert codexbar_usage_mod.scheduler_status()["scheduler_running"] is False


def test_overlapping_run_all_refreshes_is_serialized(monkeypatch):
    started = threading.Event()
    release = threading.Event()
    calls = []

    def fake_refresh(providers, *, timeout_s=None):
        calls.append(tuple(providers))
        started.set()
        release.wait(timeout=1.0)
        return {}

    claude_calls: list[str] = []
    monkeypatch.setattr(subscription_usage_mod, "refresh_provider_usage_data", fake_refresh)
    monkeypatch.setattr(subscription_usage_mod, "_refresh_cursor_usage_live", lambda: None)
    monkeypatch.setattr(subscription_usage_mod, "_refresh_api_accounts_live", lambda: None)
    monkeypatch.setattr(
        subscription_usage_mod,
        "_refresh_claude_accounts_live",
        lambda: claude_calls.append("claude"),
    )
    monkeypatch.setattr(subscription_usage_mod, "_refresh_in_flight", threading.Lock())
    worker = threading.Thread(target=subscription_usage_mod._run_all_refreshes, daemon=True)
    worker.start()
    assert started.wait(timeout=1.0)
    subscription_usage_mod._run_all_refreshes()  # must no-op while first is in flight
    release.set()
    worker.join(timeout=1.0)
    assert calls == [tuple(codexbar_usage_mod.SUBSCRIPTION_REFRESH_KEYS)]
    assert claude_calls == []


OPENROUTER_KEY_FIXTURE = {
    "data": {
        "usage": 12.5,
        "usage_daily": 1.2,
        "usage_weekly": 5.0,
        "usage_monthly": 12.5,
        "limit": 100.0,
        "limit_remaining": 87.5,
        "limit_reset": "2026-09-01T00:00:00Z",
        "is_free_tier": False,
    }
}

DEEPSEEK_BALANCE_FIXTURE = {
    "is_available": True,
    "balance_infos": [
        {
            "currency": "USD",
            "total_balance": "42.50",
            "granted_balance": "10.00",
            "topped_up_balance": "32.50",
        }
    ],
}


def test_openrouter_missing_key_returns_need_key(monkeypatch):
    account = subscription_usage_mod._empty_openrouter_account("NEED_KEY")
    _fake_private(monkeypatch, api_account=account)
    result = subscription_usage_mod._probe_openrouter_native(timeout_s=1)
    assert result["probe_state"] == "NEED_KEY"
    assert result["usage_usd"] is None and result["limit_remaining_usd"] is None


def test_openrouter_key_probe_success(monkeypatch):
    account = {
        **subscription_usage_mod._empty_openrouter_account("ok"),
        "usage_usd": 12.5,
        "limit_remaining_usd": 87.5,
        "is_free_tier": False,
    }
    _fake_private(monkeypatch, api_account=account)
    result = subscription_usage_mod._probe_openrouter_native(timeout_s=1)
    assert result == account
    assert result["usage_usd"] == 12.5 and result["limit_remaining_usd"] == 87.5


def test_deepseek_balance_probe_success(monkeypatch):
    account = {
        **subscription_usage_mod._empty_deepseek_account("ok"),
        "currency": "USD",
        "total_balance": 42.5,
        "is_available": True,
    }
    _fake_private(monkeypatch, api_account=account)
    result = subscription_usage_mod._probe_deepseek_native(timeout_s=1)
    assert result == account
    assert result["local_only"] is True and result["total_balance"] == 42.5


def test_compute_routing_budget_includes_api_accounts(monkeypatch, tmp_path):
    budget_path = tmp_path / "agent_budgets.yaml"
    budget_path.write_text("codex:\n  weekly_cap_usd: 1000\n", encoding="utf-8")
    (tmp_path / "tasks").mkdir(exist_ok=True)
    (tmp_path / "api_usage").mkdir(exist_ok=True)
    monkeypatch.setattr(state_router, "load_cost_records", lambda **_kwargs: [])
    monkeypatch.setattr(state_router, "get_provider_usage_data", lambda p: {"lane": p, "weekly_used_pct": None})
    monkeypatch.setattr(
        state_router, "get_cursor_lane_usage", lambda **kwargs: {"lane": "cursor", "probe_state": "NEED_PROBE"}
    )
    monkeypatch.setattr(state_router, "summarize_fleet_burn", lambda *args, **kwargs: {"windows": {}})
    monkeypatch.setattr(state_router, "summarize_lane_runtime", lambda *args, **kwargs: {"headroom_blocked": False})

    openrouter = {
        "kind": "prepaid_credits",
        "probe_state": "ok",
        "usage_usd": 1.0,
        "usage_daily_usd": 0.1,
        "usage_weekly_usd": 0.5,
        "usage_monthly_usd": 1.0,
        "limit_usd": 50.0,
        "limit_remaining_usd": 49.0,
        "limit_reset": None,
        "is_free_tier": False,
        "fetched_at": "2026-08-26T12:00:00Z",
    }
    deepseek = {
        "kind": "prepaid_credits",
        "probe_state": "ok",
        "local_only": True,
        "is_available": True,
        "currency": "USD",
        "total_balance": 25.0,
        "granted_balance": 5.0,
        "topped_up_balance": 20.0,
        "fetched_at": "2026-08-26T12:00:00Z",
    }
    monkeypatch.setattr(
        state_router,
        "get_api_account_data",
        lambda provider: openrouter if provider == "openrouter" else deepseek,
    )

    data = state_router.compute_routing_budget(
        datetime(2026, 8, 26, 12, 0, tzinfo=UTC),
        budget_config_path=budget_path,
        tasks_dir=tmp_path / "tasks",
        project_root=tmp_path,
        curriculum_root=tmp_path,
        batch_state_dir=tmp_path,
    )
    assert "api_accounts" in data
    assert data["api_accounts"]["openrouter"]["limit_remaining_usd"] == 49.0
    assert data["api_accounts"]["deepseek"]["total_balance"] == 25.0
    ranked_api = [row for row in data["ranked_by_headroom"] if row["type"] == "api"]
    assert len(ranked_api) == 2
    assert ranked_api[0]["remaining_usd"] == 49.0


# --- routing-budget stale/wrong lane state regressions (#7646) --------------


def test_coerce_float_accepts_numeric_strings_rejects_bool_empty():
    assert subscription_usage_mod._coerce_float(" 42.5 ") == 42.5
    assert subscription_usage_mod._coerce_float(7) == 7.0
    assert subscription_usage_mod._coerce_float(True) is None
    assert subscription_usage_mod._coerce_float("") is None
    assert subscription_usage_mod._coerce_float("nope") is None
    assert subscription_usage_mod._coerce_float(None) is None


def test_cursor_need_login_is_not_served_fresh_past_short_ttl(monkeypatch):
    """NEED_LOGIN must re-probe quickly, not squat as "fresh" for the full
    10-minute CURSOR_CACHE_TTL_S — and a later successful probe replaces it."""
    from scripts.api import state_helpers as state_helpers_mod

    subscription_usage_mod._reset_cursor_usage_state_for_tests()
    monkeypatch.setenv("CODEXBAR_ON_DEMAND_REFRESH", "0")

    need_login = {
        "lane": "cursor",
        "probe_state": "NEED_LOGIN",
        "login_state": "NEED_LOGIN",
        "is_authenticated": False,
        "status": "need_login",
        "fetched_at": "2026-09-03T12:00:00Z",
    }
    assert codexbar_usage_mod._record_cursor_probe_result(need_login) is True

    # Backdate the cached entry past the short NEED_LOGIN TTL (default 30s)
    # but well within the full healthy-probe TTL (default 600s), so only the
    # NEED_LOGIN-specific short window governs this read.
    entry_ts, entry_val = state_helpers_mod._ttl_cache[codexbar_usage_mod.CURSOR_CACHE_KEY]
    state_helpers_mod._ttl_cache[codexbar_usage_mod.CURSOR_CACHE_KEY] = (entry_ts - 60.0, entry_val)

    stale = codexbar_usage_mod.get_cursor_lane_usage()
    assert stale["freshness"] != "fresh"

    healthy = {
        "lane": "cursor",
        "probe_state": "healthy",
        "login_state": "authenticated",
        "provider_windows": {
            "auto": {"window": "monthly", "label": "Auto", "used_pct": 10.0, "remaining_pct": 90.0, "resets_at": None},
            "api": {"window": "monthly", "label": "API", "used_pct": 2.0, "remaining_pct": 98.0, "resets_at": None},
        },
        "fetched_at": "2026-09-03T12:05:00Z",
    }
    assert codexbar_usage_mod._record_cursor_probe_result(healthy) is True

    replaced = codexbar_usage_mod.get_cursor_lane_usage()
    assert replaced["freshness"] == "fresh"
    assert replaced["probe_state"] == "healthy"


def test_cursor_need_login_within_short_ttl_still_served_fresh(monkeypatch):
    """A brand-new NEED_LOGIN probe is still usable as "fresh" within its
    short cache window (avoids a re-probe storm on every single request)."""
    subscription_usage_mod._reset_cursor_usage_state_for_tests()
    monkeypatch.setenv("CODEXBAR_ON_DEMAND_REFRESH", "0")

    need_login = {
        "lane": "cursor",
        "probe_state": "NEED_LOGIN",
        "login_state": "NEED_LOGIN",
        "is_authenticated": False,
        "status": "need_login",
        "fetched_at": "2026-09-03T12:00:00Z",
    }
    assert codexbar_usage_mod._record_cursor_probe_result(need_login) is True

    result = codexbar_usage_mod.get_cursor_lane_usage()
    assert result["freshness"] == "fresh"
    assert result["probe_state"] == "NEED_LOGIN"


def test_prepaid_failure_preserves_last_good_and_retries_quickly(monkeypatch):
    mod = subscription_usage_mod
    monkeypatch.setattr(mod, "_api_account_last_good", {})
    monkeypatch.setattr(mod, "_api_account_last_failure", {})
    monkeypatch.setattr(mod, "_on_demand_refresh_enabled", lambda: False)
    cache_invalidate("api_account:deepseek")
    good = {"probe_state": "ok", "total_balance": 30, "currency": "USD", "fetched_at": "2026-09-14T12:00:00Z"}
    failed = {"probe_state": "NEED_PROBE", "total_balance": None, "fetched_at": "2026-09-14T12:01:00Z"}
    monkeypatch.setattr(mod, "_probe_api_account_live", lambda *a, **kw: good)
    assert mod.refresh_api_account_data(["deepseek"])["deepseek"]["freshness"] == "fresh"
    original = mod._api_account_last_good["deepseek"]
    monkeypatch.setattr(mod, "_probe_api_account_live", lambda *a, **kw: failed)
    observed = mod.refresh_api_account_data(["deepseek"])["deepseek"]
    assert mod._api_account_last_good["deepseek"] == original
    assert observed["total_balance"] == 30
    assert observed["freshness"] == "stale_last_good"
    assert observed["failure_kind"] == "NEED_PROBE"
    assert mod.get_api_account_data("deepseek")["freshness"] == "stale_last_good"
    called = []
    monkeypatch.setattr(mod, "_on_demand_refresh_enabled", lambda: True)
    monkeypatch.setattr(mod, "_scheduler_is_running", lambda: False)
    monkeypatch.setattr(mod, "trigger_api_account_background_refresh", lambda: called.append(True))
    mod.get_api_account_data("deepseek")
    assert not called
    tick, data = mod._api_account_last_failure["deepseek"]
    mod._api_account_last_failure["deepseek"] = (tick - 31, data)
    # Failure retry must not wait for the much longer scheduler interval.
    monkeypatch.setattr(mod, "_scheduler_is_running", lambda: True)
    mod.get_api_account_data("deepseek")
    assert called == [True]
    monkeypatch.setattr(mod, "_probe_api_account_live", lambda *a, **kw: good)
    assert mod.refresh_api_account_data(["deepseek"])["deepseek"]["freshness"] == "fresh"
    assert "deepseek" not in mod._api_account_last_failure
    cache_invalidate("api_account:deepseek")


def test_cursor_explicit_refresh_is_blocking(monkeypatch):
    mod = subscription_usage_mod
    calls = []

    def refresh():
        calls.append("blocking")
        return {"weekly_used_pct": 20, "freshness": "fresh"}

    monkeypatch.setattr(mod, "_refresh_cursor_usage_live", refresh)
    monkeypatch.setattr(mod, "get_cursor_lane_usage", lambda: (_ for _ in ()).throw(AssertionError("cache-only")))
    monkeypatch.setattr(mod, "_record_probe_result", lambda *a: True)
    result = mod.refresh_provider_usage_data(["cursor"])
    assert calls == ["blocking"]
    assert result["cursor"]["weekly_used_pct"] == 20


def test_subscription_login_failure_clears_on_success(monkeypatch):
    mod = subscription_usage_mod
    monkeypatch.setattr(mod, "_last_failure_data", {})
    monkeypatch.setattr(mod, "_last_good_data", {})
    monkeypatch.setattr(mod, "cache_set", lambda *a: None)
    assert not mod._record_probe_result("codex", {"error_kind": "need_login"})
    assert mod._last_failure_data["codex"]["failure_kind"] == "need_login"
    assert mod._record_probe_result("codex", {"weekly_used_pct": 10})
    assert "codex" not in mod._last_failure_data


def test_management_balance_failure_is_not_a_good_prepaid_sample(monkeypatch):
    account = {**subscription_usage_mod._empty_openrouter_account("NEED_PROBE"), "balance_probe_state": "NEED_PROBE"}
    _fake_private(monkeypatch, api_account=account)
    result = subscription_usage_mod._probe_openrouter_native(timeout_s=1)
    assert result["probe_state"] == result["balance_probe_state"] == "NEED_PROBE"
    assert not subscription_usage_mod._api_account_is_cacheable(result)


def test_management_key_missing_uses_short_cache_ttl(monkeypatch):
    mod = subscription_usage_mod
    monkeypatch.setattr(mod, "_api_account_last_failure", {})
    monkeypatch.setattr(mod, "_api_account_last_good", {})
    monkeypatch.setattr(mod, "_scheduler_is_running", lambda: True)
    monkeypatch.setattr(mod, "_on_demand_refresh_enabled", lambda: True)
    called = []
    monkeypatch.setattr(mod, "trigger_api_account_background_refresh", lambda: called.append(True))
    account = {"probe_state": "ok", "balance_probe_state": "NEED_KEY", "fetched_at": "2026-09-14T12:00:00Z"}
    monkeypatch.setattr(mod, "cache_get_with_age", lambda *a, **kw: (account, 31))
    mod._api_account_last_good["openrouter"] = (time.monotonic() - 31, account)
    result = mod.get_api_account_data("openrouter")
    assert result["freshness"] == "stale_last_good"
    assert called == [True]


# --- CodexBar UsagePace port (usage-pace-secrets-v2) -----------------------
#
# Ground truth values below are taken verbatim from real CodexBar CLI output
# fixtures (CLAUDE_FIXTURE / CODEX_FIXTURE `pace` blocks above), not invented,
# so the port can be checked against the upstream tool byte-for-byte.


def test_compute_usage_pace_matches_codexbar_claude_weekly_fixture():
    """CLAUDE_FIXTURE pace.secondary: expected=47, delta=27, eta=100217s, 'Runs out in 1d 3h'."""
    now = datetime(2026, 7, 9, 14, 13, 52, tzinfo=UTC)
    pace = compute_usage_pace(74.0, "2026-07-13T06:59:59Z", window_minutes=10080, now=now)
    assert pace is not None
    assert pace["stage"] == "far_ahead"
    assert round(pace["delta_pct"]) == 27
    assert round(pace["expected_pct"]) == 47
    assert pace["will_last_to_reset"] is False
    assert round(pace["eta_seconds"]) == 100217
    assert format_usage_pace_summary(pace, kind="weekly") == "27% in deficit | Expected 47% used | Runs out in 1d 3h"


def test_compute_usage_pace_matches_codexbar_claude_primary_headroom_fixture():
    """CLAUDE_FIXTURE pace.primary: expected=61, delta=-54, willLastToReset, headroom hint."""
    now = datetime(2026, 7, 9, 14, 13, 52, tzinfo=UTC)
    pace = compute_usage_pace(7.0, "2026-07-09T16:09:59Z", window_minutes=300, now=now)
    assert pace is not None
    assert round(pace["delta_pct"]) == -54
    assert round(pace["expected_pct"]) == 61
    assert pace["will_last_to_reset"] is True
    summary = format_usage_pace_summary(pace, kind="session")
    assert summary == "54% in reserve | Expected 61% used | Lasts until reset | 1.5× headroom"


@pytest.mark.parametrize(
    "delta_pct,stage",
    [
        (0.0, "on_track"),
        (2.0, "on_track"),
        (-2.0, "on_track"),
        (6.0, "slightly_ahead"),
        (-6.0, "slightly_behind"),
        (12.0, "ahead"),
        (-12.0, "behind"),
        (50.0, "far_ahead"),
        (-50.0, "far_behind"),
    ],
)
def test_pace_stage_thresholds(delta_pct, stage):
    """|delta|<=2 onTrack; <=6 slight; <=12 ahead/behind; else far* (CodexBar UsagePace.stage)."""
    now = datetime(2026, 1, 1, tzinfo=UTC)
    duration_minutes = 10080
    # Fix elapsed at exactly half the window (expected=50%) so `actual = 50 + delta_pct`
    # drives the delta directly without tripping the elapsed==0-but-used>0 guard.
    resets_at = now + timedelta(minutes=duration_minutes / 2)
    used_pct = max(0.0, min(100.0, 50.0 + delta_pct))
    pace = compute_usage_pace(
        used_pct,
        resets_at.isoformat().replace("+00:00", "Z"),
        window_minutes=duration_minutes,
        now=now,
    )
    assert pace is not None
    assert pace["stage"] == stage


def test_compute_usage_pace_accepts_epoch_seconds_and_milliseconds():
    """Codex has emitted raw epoch ints for resetsAt instead of ISO-8601 strings."""
    now = datetime(2026, 1, 1, tzinfo=UTC)
    resets_dt = now + timedelta(days=1)
    epoch_s = int(resets_dt.timestamp())
    from_str = compute_usage_pace(10.0, resets_dt.isoformat().replace("+00:00", "Z"), window_minutes=10080, now=now)
    from_epoch_s = compute_usage_pace(10.0, epoch_s, window_minutes=10080, now=now)
    from_epoch_ms = compute_usage_pace(10.0, epoch_s * 1000, window_minutes=10080, now=now)
    assert from_str is not None and from_epoch_s is not None and from_epoch_ms is not None
    assert round(from_str["delta_pct"], 4) == round(from_epoch_s["delta_pct"], 4)
    assert round(from_str["delta_pct"], 4) == round(from_epoch_ms["delta_pct"], 4)


def test_compute_usage_pace_returns_none_for_unparseable_resets_at():
    now = datetime(2026, 1, 1, tzinfo=UTC)
    assert compute_usage_pace(10.0, "not-a-date", window_minutes=10080, now=now) is None
    assert compute_usage_pace(10.0, None, window_minutes=10080, now=now) is None


def _weekly_resets_after(now: datetime, elapsed_fraction: float) -> str:
    remaining = timedelta(minutes=10080) * (1.0 - elapsed_fraction)
    return (now + remaining).isoformat().replace("+00:00", "Z")


def test_pace_is_deficit_four_routing_cases():
    """Issue #9040 verify: early window, real deficit, on-pace band, near_cap."""
    now = datetime(2026, 9, 28, 7, 51, tzinfo=UTC)

    early = compute_usage_pace(1.0, _weekly_resets_after(now, 52 / 10080), now=now)
    assert early is not None
    assert not pace_is_visible(early, kind="weekly")
    assert pace_is_deficit(early) is None
    assert round(early["delta_pct"], 2) == 0.48
    assert state_router._status_from_weekly_used(1.0, early) == "cool"

    raw_early = {
        "provider": "claude",
        "source": "web",
        "pace": {
            "secondary": {
                "expectedUsedPercent": early["expected_pct"],
                "deltaPercent": early["delta_pct"],
                "willLastToReset": False,
                "summary": "0% in deficit | Expected 1% used | Runs out in 6d",
            }
        },
        "usage": {
            "primary": {"windowMinutes": 300, "usedPercent": 0, "resetsAt": _weekly_resets_after(now, 0.5)},
            "secondary": {
                "windowMinutes": 10080,
                "usedPercent": 1,
                "resetsAt": _weekly_resets_after(now, 52 / 10080),
            },
        },
    }
    normalized_early = _normalize_provider_data("claude", raw_early)
    assert normalized_early["weekly_pace_delta_pct"] == early["delta_pct"]
    assert normalized_early["pace_summary"] == "0% in deficit | Expected 1% used | Runs out in 6d"
    assert normalized_early["will_last_to_reset"] is None
    assert state_router._status_from_weekly_used(1.0, normalized_early) == "cool"

    halfway = compute_usage_pace(60.0, _weekly_resets_after(now, 0.30), now=now)
    assert halfway is not None
    assert pace_is_deficit(halfway) is True
    assert halfway["will_last_to_reset"] is False
    assert state_router._status_from_weekly_used(60.0, halfway) == "hot"

    on_pace = compute_usage_pace(41.5, _weekly_resets_after(now, 0.40), now=now)
    assert on_pace is not None
    assert abs(on_pace["delta_pct"] - 1.5) < 0.05
    assert on_pace["will_last_to_reset"] is False
    assert pace_is_visible(on_pace, kind="weekly")
    assert pace_is_deficit(on_pace) is False
    assert state_router._status_from_weekly_used(41.5, on_pace) == "cool"

    near_cap_pace = compute_usage_pace(99.0, _weekly_resets_after(now, 0.50), now=now)
    assert state_router._status_from_weekly_used(99.0, near_cap_pace) == "near_cap"
    assert (
        state_router._status_from_weekly_used(
            99.0, {"delta_pct": -10.0, "will_last_to_reset": True, "expected_pct": 50.0}
        )
        == "near_cap"
    )


def test_pace_is_deficit_resolves_missing_expected_from_reset():
    """Live records omit weekly_expected_pct. Resolve it; unknown is not a deficit."""
    now = datetime.now(UTC)
    early_reset = (now + timedelta(days=7) - timedelta(minutes=50)).isoformat().replace("+00:00", "Z")
    early = {
        "weekly_pace_delta_pct": 2.5,
        "will_last_to_reset": False,
        "weekly_expected_pct": None,
        "weekly_resets_at": early_reset,
    }
    assert pace_is_deficit(early) is None

    visible_reset = (now + timedelta(minutes=10080 / 2)).isoformat().replace("+00:00", "Z")
    genuine = {
        "weekly_pace_delta_pct": 10.0,
        "will_last_to_reset": False,
        "weekly_expected_pct": None,
        "weekly_resets_at": visible_reset,
    }
    assert pace_is_deficit(genuine) is True

    unresolved = {
        "weekly_pace_delta_pct": 2.5,
        "will_last_to_reset": False,
        "weekly_expected_pct": None,
    }
    assert pace_is_deficit(unresolved) is None


def test_computed_fallback_hides_will_last_until_pace_is_visible(monkeypatch):
    """1% used 52 minutes after reset: raw delta kept, will_last is not False."""
    frozen = datetime(2026, 9, 28, 7, 51, tzinfo=UTC)
    resets = _weekly_resets_after(frozen, 52 / 10080)
    raw = {
        "provider": "claude",
        "source": "web",
        "usage": {
            "primary": {
                "windowMinutes": 300,
                "resetsAt": (frozen + timedelta(hours=4)).isoformat().replace("+00:00", "Z"),
                "usedPercent": 0,
            },
            "secondary": {"windowMinutes": 10080, "resetsAt": resets, "usedPercent": 1},
        },
    }
    real = subscription_usage_mod.compute_usage_pace

    def _paced(used_pct, resets_at, *, window_minutes=None, now=None):
        return real(used_pct, resets_at, window_minutes=window_minutes, now=now or frozen)

    monkeypatch.setattr(subscription_usage_mod, "compute_usage_pace", _paced)
    res = _normalize_provider_data("claude", raw)
    assert res["weekly_pace_delta_pct"] is not None
    assert abs(res["weekly_pace_delta_pct"] - 0.484) < 0.01
    assert res["will_last_to_reset"] is None
    assert res["pace_summary"] is None
    assert pace_is_deficit(res) is None
    assert state_router._status_from_weekly_used(res["weekly_used_pct"], res) == "cool"


def test_pace_is_visible_hides_below_minimum_expected_pct():
    """CodexBar hides pace until enough of the window has elapsed (~3% session / ~1% weekly)."""
    now = datetime(2026, 1, 1, tzinfo=UTC)
    # 1% of a 5h (300min) session window = 3 minutes elapsed -> expected ~1%, below the 3% session floor.
    just_started_session = now - timedelta(minutes=3)
    session_pace = compute_usage_pace(
        1.0,
        (just_started_session + timedelta(minutes=300)).isoformat().replace("+00:00", "Z"),
        window_minutes=300,
        now=now,
    )
    assert session_pace is not None
    assert not pace_is_visible(session_pace, kind="session")

    # Same elapsed fraction against a weekly window clears the 1% weekly floor.
    just_started_weekly = now - timedelta(minutes=101)
    weekly_pace = compute_usage_pace(
        1.0,
        (just_started_weekly + timedelta(minutes=10080)).isoformat().replace("+00:00", "Z"),
        window_minutes=10080,
        now=now,
    )
    assert weekly_pace is not None
    assert pace_is_visible(weekly_pace, kind="weekly")


def test_normalize_claude_shape_fallback_pace_uses_codexbar_summary_format(monkeypatch):
    """No `pace` block -> fallback must produce CodexBar-shaped summary (open window)."""
    frozen = datetime(2026, 9, 15, 12, 0, tzinfo=UTC)
    resets = (frozen + timedelta(days=3)).isoformat().replace("+00:00", "Z")
    raw = {
        "provider": "claude",
        "source": "web",
        "usage": {
            "primary": {
                "windowMinutes": 300,
                "resetsAt": (frozen + timedelta(hours=2)).isoformat().replace("+00:00", "Z"),
                "usedPercent": 10,
            },
            "secondary": {
                "windowMinutes": 10080,
                "resetsAt": resets,
                "usedPercent": 20,
            },
        },
    }
    real = subscription_usage_mod.compute_usage_pace

    def _paced(used_pct, resets_at, *, window_minutes=None, now=None):
        return real(used_pct, resets_at, window_minutes=window_minutes, now=now or frozen)

    monkeypatch.setattr(subscription_usage_mod, "compute_usage_pace", _paced)
    res = _normalize_provider_data("claude", raw)
    assert res["weekly_pace_delta_pct"] is not None
    assert res["pace_summary"] is not None
    assert "Expected" in res["pace_summary"]
    assert "% used" in res["pace_summary"]
    assert "pace delta" not in res["pace_summary"]


def test_codex_private_weekly_window_keeps_weekly_pace(monkeypatch):
    frozen = datetime(2026, 9, 15, 12, tzinfo=UTC)
    real = subscription_usage_mod.compute_usage_pace
    monkeypatch.setattr(
        subscription_usage_mod,
        "compute_usage_pace",
        lambda used, reset, **kw: real(used, reset, **{**kw, "now": frozen}),
    )
    _fake_private(
        monkeypatch,
        {
            "outcome": "data",
            "record": {
                "provider": "codex",
                "source": "codex_oauth",
                "openaiDashboard": {},
                "usage": {
                    "primary": None,
                    "secondary": {
                        "windowMinutes": 10080,
                        "usedPercent": 40,
                        "resetsAt": int(frozen.timestamp()) + 313014,
                    },
                },
            },
        },
    )
    result = subscription_usage_mod._probe_codex_native(timeout_s=5)
    assert result["status"] == "healthy"
    assert result["primary_used_pct"] is None and result["weekly_used_pct"] == 40.0
    assert result["windows"]["secondary"]["window_minutes"] == 10080
    assert "Expected" in result["pace_summary"] and result["will_last_to_reset"] is not None


def test_agy_nonzero_exit_does_not_leak_stdout_stderr(monkeypatch, tmp_path):
    from scripts.api import subscription_usage as su

    marker = "PRIVATE_TOKEN_SHOULD_NOT_ESCAPE"
    fake_bin = tmp_path / "agy"
    fake_bin.write_text("#!/bin/sh\necho OUT\necho ERR >&2\nexit 7\n", encoding="utf-8")
    fake_bin.chmod(0o755)

    class Completed:
        returncode = 7
        stdout = f"stdout {marker}"
        stderr = f"stderr {marker}"

    monkeypatch.setattr(su, "_agy_cli_bin", lambda: str(fake_bin))
    monkeypatch.setattr(
        su.subprocess,
        "run",
        lambda *a, **k: Completed(),
    )
    res = su._probe_antigravity_native(timeout_s=5)
    assert res["status"] == "unavailable"
    assert marker not in str(res.get("auth_error") or "")
    assert "exit 7" in str(res.get("auth_error") or "")


def test_compute_usage_pace_rejects_expired_and_out_of_window():
    from datetime import UTC, datetime, timedelta

    from scripts.api.subscription_usage import compute_usage_pace

    now = datetime(2026, 9, 15, 12, 0, 0, tzinfo=UTC)
    assert compute_usage_pace(25.0, (now - timedelta(seconds=1)).isoformat(), window_minutes=300, now=now) is None
    assert (
        compute_usage_pace(25.0, (now + timedelta(seconds=301 * 60)).isoformat(), window_minutes=300, now=now) is None
    )
    ok = compute_usage_pace(25.0, (now + timedelta(seconds=150 * 60)).isoformat(), window_minutes=300, now=now)
    assert ok is not None


_MUSE_EMAIL = "secret-email-do-not-leak@example.com"
_MUSE_KNOWN = {
    "provider": "muse",
    "source": "oauth",
    "usage": {
        "primary": {"usedPercent": 10, "windowMinutes": 300, "resetsAt": "2026-10-13T18:00:00Z"},
        "secondary": {"usedPercent": 30, "windowMinutes": 10080, "resetsAt": "2026-10-20T00:00:00Z"},
        "accountEmail": _MUSE_EMAIL,
    },
    "credits": {"remaining": 999},
    "identity": {"accountEmail": _MUSE_EMAIL},
}
_MUSE_NULL = {
    "provider": "muse",
    "source": "oauth",
    "usage": {
        "primary": None,
        "secondary": {"usedPercent": None, "windowMinutes": 10080, "resetsAt": None},
    },
}


def _assert_no_sentinel_value(value: object, sentinel: int | float) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_sentinel_value(item, sentinel)
    elif isinstance(value, list):
        for item in value:
            _assert_no_sentinel_value(item, sentinel)
    else:
        assert value not in (sentinel, str(sentinel))


def _assert_muse_has_no_account_material(record: dict) -> None:
    blob = json.dumps(record)
    assert _MUSE_EMAIL not in blob
    _assert_no_sentinel_value(record, 999)


def test_muse_known_windows_publish_remaining_headroom_and_reset():
    record = subscription_usage_mod._muse_record_from_codexbar_payload(_MUSE_KNOWN)
    _assert_muse_has_no_account_material(record)
    assert record["status"] == "healthy"
    assert record["primary_used_pct"] == 10.0
    assert record["primary_remaining_pct"] == 90.0
    assert record["weekly_used_pct"] == 30.0
    assert record["weekly_remaining_pct"] == 70.0
    assert record["headroom_pct"] == 70.0
    assert record["weekly_resets_at"] == "2026-10-20T00:00:00Z"
    assert record["windows"]["primary"]["resets_at"] == "2026-10-13T18:00:00Z"
    assert record["windows"]["secondary"]["remaining_pct"] == 70.0


def test_muse_null_percentages_are_unknown_not_unlimited():
    record = subscription_usage_mod._muse_record_from_codexbar_payload(_MUSE_NULL)
    assert record["status"] == "unknown"
    assert record["error_kind"] == "unsupported"
    assert record["error_code"] == "NO_QUOTA"
    assert record["primary_used_pct"] is None
    assert record["primary_remaining_pct"] is None
    assert record["weekly_used_pct"] is None
    assert record["weekly_remaining_pct"] is None
    assert record["headroom_pct"] is None
    assert record["primary_used_pct"] != 0
    assert record["weekly_remaining_pct"] != 100


def test_muse_omitted_idle_session_keeps_weekly_without_inventing_session():
    """Meta can omit the 5-hour window while weekly usage is present."""
    record = subscription_usage_mod._muse_record_from_codexbar_payload(
        {
            "provider": "muse",
            "usage": {
                "primary": None,
                "secondary": {
                    "usedPercent": 30,
                    "windowMinutes": 10080,
                    "resetsAt": "2026-10-20T00:00:00Z",
                },
            },
        }
    )
    assert record["status"] == "healthy"
    assert record["primary_remaining_pct"] is None
    assert record["weekly_remaining_pct"] == 70.0
    assert record["headroom_pct"] == 70.0
    assert record["weekly_resets_at"] == "2026-10-20T00:00:00Z"


def test_muse_zero_used_is_a_real_remaining_reading():
    record = subscription_usage_mod._muse_record_from_codexbar_payload(
        {
            "provider": "muse",
            "usage": {
                "primary": {"usedPercent": 0, "windowMinutes": 300, "resetsAt": "2026-10-13T18:00:00Z"},
                "secondary": None,
            },
        }
    )
    assert record["status"] == "healthy"
    assert record["primary_used_pct"] == 0.0
    assert record["primary_remaining_pct"] == 100.0
    assert record["headroom_pct"] == 100.0
    assert record["weekly_remaining_pct"] is None


def test_muse_malformed_payload_is_fetch_error():
    for payload in ("nope", ["nope"], {"usage": "nope"}):
        record = subscription_usage_mod._muse_record_from_codexbar_payload(payload)
        assert record["status"] == "unavailable"
        assert record["error_kind"] == "fetch_error"
        assert record["error_code"] == "BAD_JSON"
        assert record["primary_remaining_pct"] is None
        assert record["weekly_remaining_pct"] is None
        assert record.get("headroom_pct") is None


def test_muse_provider_error_drops_message_text():
    record = subscription_usage_mod._muse_record_from_codexbar_payload(
        {"provider": "muse", "error": {"kind": "provider", "code": 1, "message": _MUSE_EMAIL}}
    )
    _assert_muse_has_no_account_material(record)
    assert record["status"] == "unavailable"
    assert record["error_kind"] == "provider"
    assert record["error_code"] == 1
    assert record["auth_error"] == "Muse usage probe failed"
    assert record["weekly_remaining_pct"] is None


def test_muse_rate_limit_payload_stays_non_numeric():
    record = subscription_usage_mod._muse_record_from_codexbar_payload(
        [{"provider": "muse", "error": {"kind": "provider", "code": 429, "message": "slow down"}}]
    )
    assert record["error_kind"] == "rate_limit"
    assert record["error_code"] == 429
    assert record["status"] == "unavailable"
    assert record["primary_remaining_pct"] is None
    assert record["weekly_remaining_pct"] is None
    projected = subscription_usage_mod.project_muse_for_status(
        {**_muse_known_with_freshness(), "error_kind": "rate_limit", "error_code": 429, "freshness": "fresh"}
    )
    assert projected["headroom_pct"] is None
    assert projected["remaining_pct"] is None
    assert projected["resets_at"] is None
    assert projected["status"] == "unknown"


def _muse_known_with_freshness() -> dict:
    record = subscription_usage_mod._muse_record_from_codexbar_payload(_MUSE_KNOWN)
    record["freshness"] = "fresh"
    record["age_s"] = 0
    return record


def test_muse_stale_projection_hides_numeric_headroom():
    record = _muse_known_with_freshness()
    record["freshness"] = "stale_last_good"
    record["age_s"] = 800
    projected = subscription_usage_mod.project_muse_for_status(record)
    assert projected["freshness"] == "stale_last_good"
    assert projected["status"] == "unknown"
    assert projected["remaining_pct"] is None
    assert projected["headroom_pct"] is None
    assert projected["resets_at"] is None
    assert projected["codexbar"]["windows"]["secondary"]["remaining_pct"] is None


def test_muse_fresh_projection_keeps_binding_headroom():
    projected = subscription_usage_mod.project_muse_for_status(_muse_known_with_freshness())
    assert projected == {
        "lane": "muse",
        "status": "healthy",
        "remaining_pct": 70.0,
        "headroom_pct": 70.0,
        "resets_at": "2026-10-20T00:00:00Z",
        "freshness": "fresh",
        "age_s": 0,
        "error_kind": None,
        "error_code": None,
        "failure_kind": None,
        "last_failure_code": None,
        "auth_error": None,
        "codexbar": {
            "freshness": "fresh",
            "age_s": 0,
            "headroom_pct": 70.0,
            "weekly_resets_at": "2026-10-20T00:00:00Z",
            "windows": projected["codexbar"]["windows"],
            "error_kind": None,
            "failure_kind": None,
            "last_failure_code": None,
            "primary_remaining_pct": 90.0,
            "weekly_remaining_pct": 70.0,
        },
    }
    assert projected["codexbar"]["windows"]["primary"]["remaining_pct"] == 90.0
    assert projected["codexbar"]["windows"]["secondary"]["remaining_pct"] == 70.0


def test_muse_probe_reads_muse_usage_json(monkeypatch):
    import subprocess

    captured: dict = {}
    now_ms = int(time.time() * 1000)
    payload = {
        "allowance": {
            "asOfMs": now_ms,
            "tier": _MUSE_EMAIL,
            "weekly": {"usedPercent": 30, "resetsAtMs": now_ms + 5 * 24 * 3600 * 1000},
            "window": {"usedPercent": 10, "resetsAtMs": now_ms + 300 * 1000},
        }
    }

    def fake_run(argv, **kwargs):
        captured["argv"] = argv
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(payload), stderr=_MUSE_EMAIL)

    from tests.opsec_fixtures import TOKEN

    monkeypatch.setenv("GH_TOKEN", TOKEN)
    monkeypatch.setattr(
        subscription_usage_mod.shutil, "which", lambda name: "/usr/bin/muse" if name == "muse" else None
    )
    monkeypatch.setattr(subscription_usage_mod.subprocess, "run", fake_run)
    record = subscription_usage_mod.fetch_provider_usage("muse", timeout_s=5)
    assert captured["argv"] == ["/usr/bin/muse", "usage", "--json"]
    assert captured["kwargs"]["stdin"] is subprocess.DEVNULL
    usage_env = captured["kwargs"]["env"]
    assert usage_env["MUSE_NO_AUTO_UPDATE"] == "1"
    assert "GH_TOKEN" not in usage_env
    assert TOKEN not in usage_env.values()
    assert record["status"] == "healthy"
    assert record["source"] == "muse_usage"
    assert record["weekly_used_pct"] == 30.0
    assert record["headroom_pct"] == 70.0
    _assert_muse_has_no_account_material(record)

    monkeypatch.setattr(subscription_usage_mod.shutil, "which", lambda name: None)
    missing = subscription_usage_mod.fetch_provider_usage("muse", timeout_s=5)
    assert missing["error_code"] == "NO_PROBE"
    assert missing["status"] == "unavailable"
    assert missing["status"] != "healthy"
    assert missing["weekly_used_pct"] is None
    assert missing["weekly_remaining_pct"] is None


def test_muse_allowance_session_drops_secret_shaped_parent_env(monkeypatch):
    """A secret-shaped parent variable must not reach the Muse allowance session.

    The value is the synthetic OPSEC sentinel, never a credential-shaped literal.
    The session env is the runner allowlist for provider ``muse`` plus the two
    CLI lookups that ``muse usage`` honors when they are set.
    """
    from tests.opsec_fixtures import TOKEN

    monkeypatch.setenv("SYNTHETIC_TOKEN", TOKEN)
    monkeypatch.setenv("LU_OPSEC_OVERRIDE", TOKEN)
    monkeypatch.setenv("GH_TOKEN", TOKEN)
    monkeypatch.setenv("XDG_CONFIG_HOME", "/fixture/xdg")
    monkeypatch.setenv("SSL_CERT_FILE", "/fixture/ca.pem")
    monkeypatch.setenv("MUSE_FLAGS", "1")
    monkeypatch.setenv("MUSE_AUTH_PATH", "/fixture/muse-auth")
    monkeypatch.setenv("XDG_DATA_HOME", "/fixture/xdg-data")
    monkeypatch.setenv("SSL_CERT_DIR", "/fixture/certs")

    env = subscription_usage_mod._muse_session_env()

    assert env["MUSE_NO_AUTO_UPDATE"] == "1"
    assert env["XDG_CONFIG_HOME"] == "/fixture/xdg"
    assert env["SSL_CERT_FILE"] == "/fixture/ca.pem"
    assert "SYNTHETIC_TOKEN" not in env
    assert "LU_OPSEC_OVERRIDE" not in env
    assert "GH_TOKEN" not in env
    assert "MUSE_FLAGS" not in env
    assert "MUSE_AUTH_PATH" not in env
    assert "XDG_DATA_HOME" not in env
    assert "SSL_CERT_DIR" not in env
    assert TOKEN not in env.values()


def test_muse_probe_timeout_and_malformed_stdout_stay_unknown(monkeypatch):
    import subprocess

    monkeypatch.setattr(subscription_usage_mod.shutil, "which", lambda name: "/usr/bin/muse" if name == "muse" else None)

    def timeout_run(argv, **kwargs):
        raise subprocess.TimeoutExpired(argv, kwargs.get("timeout"))

    monkeypatch.setattr(subscription_usage_mod.subprocess, "run", timeout_run)
    timed_out = subscription_usage_mod.fetch_provider_usage("muse", timeout_s=1)
    assert timed_out["error_kind"] == "timeout"
    assert timed_out["status"] == "unavailable"
    assert timed_out["weekly_remaining_pct"] is None

    def bad_json(argv, **kwargs):
        return subprocess.CompletedProcess(argv, 0, stdout="not-json", stderr="")

    monkeypatch.setattr(subscription_usage_mod.subprocess, "run", bad_json)
    malformed = subscription_usage_mod.fetch_provider_usage("muse", timeout_s=1)
    assert malformed["error_kind"] == "fetch_error"
    assert malformed["error_code"] == "BAD_JSON"
    assert malformed["primary_remaining_pct"] is None


_AGY_EMAIL = "secret-email-do-not-leak@example.com"
_AGY_FIXTURE = Path(__file__).parent / "fixtures" / "usage_9270" / "agy.json"


def _agy_usage_payload(*groups: dict) -> dict:
    return {"command": {"data": {"groups": list(groups)}}}


def _probe_agy_stdout(monkeypatch, stdout: str, *, returncode: int = 0, reset: bool = True) -> dict:
    import subprocess

    if reset:
        subscription_usage_mod._reset_agy_quota_observation_for_tests()
    monkeypatch.setattr(subscription_usage_mod, "_agy_cli_bin", lambda: "/usr/bin/agy")
    captured: dict = {}

    def fake_run(argv, **kwargs):
        captured["argv"] = list(argv)
        return subprocess.CompletedProcess(argv, returncode, stdout=stdout, stderr=_AGY_EMAIL)

    monkeypatch.setattr(subscription_usage_mod.subprocess, "run", fake_run)
    record = subscription_usage_mod._probe_antigravity_native(timeout_s=5)
    record["_captured_argv"] = captured.get("argv")
    return record


def _agy_window(projected: dict, group_key: str, window: str) -> dict | None:
    for group in projected["quota_groups"]:
        if group["key"] != group_key:
            continue
        for item in group["windows"]:
            if item["window"] == window:
                return item
    return None


def test_agy_fixture_publishes_separate_quota_groups(monkeypatch):
    payload = json.loads(_AGY_FIXTURE.read_text(encoding="utf-8"))
    payload["account_id"] = _AGY_EMAIL
    payload["command"]["data"]["balance"] = 999
    record = _probe_agy_stdout(monkeypatch, json.dumps(payload))
    assert record["_captured_argv"] == [
        "/usr/bin/agy",
        "--prompt",
        "/usage",
        "--output-format",
        "json",
    ]
    assert record["status"] == "healthy"
    assert record["weekly_used_pct"] == pytest.approx(0.15184879302978516)
    assert record["claude_gpt_windows"]["five_hour"]["used_pct"] == 0
    assert "quota_groups" not in record
    projected = subscription_usage_mod.project_agy_for_status(subscription_usage_mod.get_agy_quota_observation())
    blob = json.dumps(projected)
    assert _AGY_EMAIL not in blob
    _assert_no_sentinel_value(projected, 999)
    assert projected["status"] == "healthy"
    assert projected["remaining_pct"] is None
    assert projected["headroom_pct"] is None
    assert projected["freshness"] == "fresh"
    assert projected["codexbar"]["source"] == "agy_cli_usage"
    gemini_weekly = _agy_window(projected, "gemini_models", "weekly")
    claude_weekly = _agy_window(projected, "claude_gpt", "weekly")
    assert gemini_weekly is not None and claude_weekly is not None
    assert gemini_weekly["used_pct"] == pytest.approx(0.15184879302978516)
    assert gemini_weekly["remaining_pct"] == pytest.approx(99.84815120697021)
    assert gemini_weekly["resets_at"] == "2026-10-07T02:23:27Z"
    assert claude_weekly["used_pct"] == 0.0
    assert claude_weekly["remaining_pct"] == 100.0
    assert claude_weekly["resets_at"] == "2026-10-07T07:33:22Z"
    assert gemini_weekly["remaining_pct"] != claude_weekly["remaining_pct"]
    assert _agy_window(projected, "gemini_models", "5h")["remaining_pct"] == 100.0
    assert _agy_window(projected, "claude_gpt", "5h")["resets_at"] == "2026-09-30T12:33:22Z"


def test_agy_groups_do_not_copy_a_window_into_its_sibling(monkeypatch):
    payload = _agy_usage_payload(
        {
            "name": "Gemini Models",
            "buckets": [
                {"window": "5h", "remaining_fraction": 0.5, "reset_time": "2026-10-13T18:00:00Z"},
            ],
        },
        {
            "name": "Claude and GPT models",
            "buckets": [
                {"window": "weekly", "remaining_fraction": 0.25, "reset_time": "2026-10-20T00:00:00Z"},
            ],
        },
    )
    _probe_agy_stdout(monkeypatch, json.dumps(payload))
    projected = subscription_usage_mod.project_agy_for_status(subscription_usage_mod.get_agy_quota_observation())
    assert projected["status"] == "healthy"
    assert projected["remaining_pct"] is None
    gemini = next(group for group in projected["quota_groups"] if group["key"] == "gemini_models")
    claude = next(group for group in projected["quota_groups"] if group["key"] == "claude_gpt")
    assert [item["window"] for item in gemini["windows"]] == ["5h"]
    assert [item["window"] for item in claude["windows"]] == ["weekly"]
    assert gemini["windows"][0]["remaining_pct"] == 50.0
    assert gemini["windows"][0]["resets_at"] == "2026-10-13T18:00:00Z"
    assert claude["windows"][0]["remaining_pct"] == 25.0
    assert claude["windows"][0]["resets_at"] == "2026-10-20T00:00:00Z"


def test_agy_missing_fraction_keeps_reset_and_is_unknown(monkeypatch):
    payload = _agy_usage_payload(
        {
            "name": "Gemini Models",
            "buckets": [
                {"window": "weekly", "remaining_fraction": None, "reset_time": "2026-10-20T00:00:00Z"},
            ],
        }
    )
    _probe_agy_stdout(monkeypatch, json.dumps(payload))
    projected = subscription_usage_mod.project_agy_for_status(subscription_usage_mod.get_agy_quota_observation())
    window = _agy_window(projected, "gemini_models", "weekly")
    assert projected["status"] == "unknown"
    assert projected["error_kind"] == "unsupported"
    assert projected["error_code"] == "NO_QUOTA"
    assert projected["freshness"] == "fresh"
    assert window is not None
    assert window["used_pct"] is None
    assert window["remaining_pct"] is None
    assert window["resets_at"] == "2026-10-20T00:00:00Z"
    assert window["remaining_pct"] != 100


def test_agy_measured_empty_and_full_windows_are_not_unlimited(monkeypatch):
    payload = _agy_usage_payload(
        {
            "name": "Gemini Models",
            "buckets": [
                {"window": "5h", "remaining_fraction": 0, "reset_time": "2026-10-13T18:00:00Z"},
                {"window": "weekly", "remaining_fraction": 1, "reset_time": "2026-10-20T00:00:00Z"},
            ],
        }
    )
    _probe_agy_stdout(monkeypatch, json.dumps(payload))
    projected = subscription_usage_mod.project_agy_for_status(subscription_usage_mod.get_agy_quota_observation())
    assert projected["status"] == "healthy"
    assert _agy_window(projected, "gemini_models", "5h")["used_pct"] == 100.0
    assert _agy_window(projected, "gemini_models", "5h")["remaining_pct"] == 0.0
    assert _agy_window(projected, "gemini_models", "weekly")["used_pct"] == 0.0
    assert _agy_window(projected, "gemini_models", "weekly")["remaining_pct"] == 100.0


def test_agy_claude_group_survives_when_gemini_group_is_absent(monkeypatch):
    payload = _agy_usage_payload(
        {
            "name": "Claude and GPT models",
            "buckets": [
                {"window": "5h", "remaining_fraction": 0.8, "reset_time": "2026-10-13T18:00:00Z"},
            ],
        }
    )
    record = _probe_agy_stdout(monkeypatch, json.dumps(payload))
    assert record["error_code"] == "NEED_LOGIN"
    projected = subscription_usage_mod.project_agy_for_status(subscription_usage_mod.get_agy_quota_observation())
    assert projected["status"] == "healthy"
    assert [group["key"] for group in projected["quota_groups"]] == ["claude_gpt"]
    assert _agy_window(projected, "claude_gpt", "5h")["remaining_pct"] == 80.0
    assert _agy_window(projected, "gemini_models", "5h") is None


def test_agy_duplicate_group_keys_stay_distinct(monkeypatch):
    payload = _agy_usage_payload(
        {
            "name": "Claude models",
            "buckets": [{"window": "weekly", "remaining_fraction": 0.9, "reset_time": "2026-10-20T00:00:00Z"}],
        },
        {
            "name": "GPT models",
            "buckets": [{"window": "weekly", "remaining_fraction": 0.1, "reset_time": "2026-10-21T00:00:00Z"}],
        },
    )
    _probe_agy_stdout(monkeypatch, json.dumps(payload))
    projected = subscription_usage_mod.project_agy_for_status(subscription_usage_mod.get_agy_quota_observation())
    keys = [group["key"] for group in projected["quota_groups"]]
    assert keys == ["claude_gpt", "claude_gpt_2"]
    assert _agy_window(projected, "claude_gpt", "weekly")["remaining_pct"] == 90.0
    assert _agy_window(projected, "claude_gpt_2", "weekly")["remaining_pct"] == 10.0


def test_agy_credit_group_and_account_label_are_dropped(monkeypatch):
    payload = _agy_usage_payload(
        {
            "name": "Credits",
            "buckets": [{"window": "weekly", "remaining_fraction": 0.5, "reset_time": "2026-10-20T00:00:00Z"}],
        },
        {
            "name": _AGY_EMAIL,
            "buckets": [{"window": "5h", "remaining_fraction": 0.5, "reset_time": "2026-10-13T18:00:00Z"}],
        },
    )
    _probe_agy_stdout(monkeypatch, json.dumps(payload))
    projected = subscription_usage_mod.project_agy_for_status(subscription_usage_mod.get_agy_quota_observation())
    blob = json.dumps(projected)
    assert _AGY_EMAIL not in blob
    assert "Credits" not in blob
    assert projected["status"] == "healthy"
    assert [group["key"] for group in projected["quota_groups"]] == ["group"]
    assert _agy_window(projected, "group", "5h")["remaining_pct"] == 50.0


def test_agy_malformed_and_rate_limit_drop_numeric_headroom(monkeypatch):
    malformed = _probe_agy_stdout(monkeypatch, "not-json")
    assert malformed["error_code"] == "BAD_JSON"
    projected = subscription_usage_mod.project_agy_for_status(subscription_usage_mod.get_agy_quota_observation())
    assert projected["status"] == "unknown"
    assert projected["freshness"] == "unavailable"
    assert projected["error_kind"] == "fetch_error"
    assert projected["error_code"] == "BAD_JSON"
    assert projected["quota_groups"] == []
    assert _AGY_EMAIL not in json.dumps(projected)

    known = _agy_usage_payload(
        {
            "name": "Gemini Models",
            "buckets": [{"window": "weekly", "remaining_fraction": 0.5, "reset_time": "2026-10-20T00:00:00Z"}],
        }
    )
    _probe_agy_stdout(monkeypatch, json.dumps(known))
    fresh = subscription_usage_mod.project_agy_for_status(subscription_usage_mod.get_agy_quota_observation())
    assert fresh["status"] == "healthy"
    limited = _probe_agy_stdout(monkeypatch, "", returncode=429, reset=False)
    assert limited["status"] == "unavailable"
    hidden = subscription_usage_mod.project_agy_for_status(subscription_usage_mod.get_agy_quota_observation())
    assert hidden["status"] == "unknown"
    assert hidden["error_kind"] == "rate_limit"
    assert hidden["error_code"] == 429
    assert hidden["freshness"] == "stale_last_good"
    assert _agy_window(hidden, "gemini_models", "weekly")["remaining_pct"] is None
    assert _agy_window(hidden, "gemini_models", "weekly")["resets_at"] is None
    _assert_no_sentinel_value(hidden, 50.0)


def test_agy_stale_observation_hides_quota(monkeypatch):
    payload = _agy_usage_payload(
        {
            "name": "Gemini Models",
            "buckets": [{"window": "5h", "remaining_fraction": 0.5, "reset_time": "2026-10-13T18:00:00Z"}],
        }
    )
    _probe_agy_stdout(monkeypatch, json.dumps(payload))
    with subscription_usage_mod._AGY_QUOTA_LOCK:
        snapshot = subscription_usage_mod._agy_quota_parsed[1]
        subscription_usage_mod._agy_quota_parsed = (time.monotonic() - 10_000, snapshot)
    projected = subscription_usage_mod.project_agy_for_status(subscription_usage_mod.get_agy_quota_observation())
    assert projected["freshness"] == "stale_last_good"
    assert projected["status"] == "unknown"
    assert _agy_window(projected, "gemini_models", "5h")["remaining_pct"] is None
    assert _agy_window(projected, "gemini_models", "5h")["resets_at"] is None
    _assert_no_sentinel_value(projected, 50.0)


@pytest.mark.parametrize("value", [-1, 101, 10**400, float("nan"), float("inf"), True, None, "PRIVATE_PERCENT"])
def test_public_percent_rejects_unmeasured_values(value):
    assert subscription_usage_mod._public_percent(value) is None


@pytest.mark.parametrize(
    ("kind", "code", "expected"),
    [
        (None, None, (None, None)),
        ("unavailable", None, ("unavailable", None)),
        ("unavailable", "", ("unavailable", None)),
        ("fetch_error", None, ("fetch_error", None)),
        ("fetch_error", "FETCH_ERROR", ("fetch_error", "FETCH_ERROR")),
        ("PRIVATE_KIND", None, ("provider", None)),
        ("PRIVATE_KIND", "PRIVATE_CODE", ("provider", "PROVIDER_ERROR")),
        ({"private": "PRIVATE_KIND"}, {"private": "PRIVATE_CODE"}, ("provider", "PROVIDER_ERROR")),
        ("provider", 600, ("provider", "PROVIDER_ERROR")),
        ("provider", True, ("provider", "PROVIDER_ERROR")),
        ("provider", "429", ("rate_limit", 429)),
        ("ratelimit", None, ("rate_limit", 429)),
        ("fetch_error", "BAD_JSON", ("fetch_error", "BAD_JSON")),
        ("provider", 1, ("provider", 1)),
    ],
)
def test_public_quota_errors_are_fixed_and_bounded(kind, code, expected):
    assert subscription_usage_mod._public_quota_error(kind, code) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("PRIVATE_RESET", None),
        (True, None),
        (float("inf"), None),
        (10**400, None),
        ("2026-10-20T02:00:00+02:00", "2026-10-20T00:00:00Z"),
        (1792454400000, "2026-10-20T00:00:00Z"),
    ],
)
def test_public_resets_are_canonical_timestamps(value, expected):
    assert subscription_usage_mod._agy_reset_or_none(value) == expected


def test_muse_nested_metadata_is_projected_without_private_text():
    payload = {
        "provider": "muse",
        "source": "PRIVATE_SOURCE",
        "usage": {
            "primary": {
                "usedPercent": 20,
                "windowMinutes": "PRIVATE_MINUTES",
                "resetsAt": "PRIVATE_RESET",
                "resetDescription": "PRIVATE_DESCRIPTION",
                "label": "PRIVATE_LABEL",
                "identity": "PRIVATE_IDENTITY",
            },
        },
    }
    record = subscription_usage_mod._muse_record_from_codexbar_payload(payload)
    projected = subscription_usage_mod.project_muse_for_status({**record, "freshness": "fresh", "age_s": 0})
    assert "PRIVATE_" not in json.dumps(record) + json.dumps(projected)
    assert record["source"] == "codexbar_muse"
    assert projected["codexbar"]["windows"]["primary"] == {
        "used_pct": 20.0,
        "remaining_pct": 80.0,
        "resets_at": None,
        "window_minutes": None,
        "reset_description": None,
    }
    assert projected["remaining_pct"] == 80.0
    assert projected["resets_at"] is None


@pytest.mark.parametrize("provider", ["codex", "PRIVATE_PROVIDER", None, {"private": "PRIVATE_PROVIDER"}])
def test_muse_rejects_explicit_provider_mismatch(provider):
    record = subscription_usage_mod._muse_record_from_codexbar_payload({**_MUSE_KNOWN, "provider": provider})
    assert record["error_kind"] == "fetch_error"
    assert record["error_code"] == "PROVIDER_MISMATCH"
    assert record["primary_remaining_pct"] is None
    assert "PRIVATE_" not in json.dumps(record)


def test_muse_list_prefers_actual_muse_over_unlabelled_and_other_providers():
    record = subscription_usage_mod._muse_record_from_codexbar_payload(
        [
            {"provider": "codex", "usage": {"primary": {"usedPercent": 7}}},
            {"usage": {"primary": {"usedPercent": 3}}},
            _MUSE_NULL,
        ]
    )
    assert record["error_code"] == "NO_QUOTA"
    assert record["headroom_pct"] is None


@pytest.mark.parametrize(
    ("updated_at", "code"),
    [
        ("2000-01-01T00:00:00Z", "STALE_DATA"),
        ("2999-01-01T00:00:00Z", "STALE_DATA"),
        (None, "BAD_JSON"),
        ("PRIVATE_OBSERVATION", "BAD_JSON"),
    ],
)
def test_muse_invalid_observation_cannot_become_a_cached_measurement(updated_at, code):
    record = subscription_usage_mod._muse_record_from_codexbar_payload(
        {
            **_MUSE_KNOWN,
            "usage": {**_MUSE_KNOWN["usage"], "updatedAt": updated_at},
        }
    )
    assert record["error_code"] == code
    assert record["primary_remaining_pct"] is None
    assert record["weekly_remaining_pct"] is None
    assert subscription_usage_mod._record_probe_result("muse", record) is False
    assert "PRIVATE_" not in json.dumps(record)


def test_muse_provider_age_expires_before_a_recent_cache_entry(monkeypatch):
    now = datetime(2026, 10, 13, 12, tzinfo=UTC)

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return now

    monkeypatch.setattr(subscription_usage_mod, "datetime", Clock)
    monkeypatch.setattr(subscription_usage_mod, "_codexbar_cache_ttl_s", lambda: 720)
    record = subscription_usage_mod._muse_record_from_codexbar_payload(
        {
            **_MUSE_KNOWN,
            "usage": {**_MUSE_KNOWN["usage"], "updatedAt": "2026-10-13T11:50:00Z"},
        }
    )
    record.update(freshness="fresh", age_s=0)
    projected = subscription_usage_mod.project_muse_for_status(record)
    assert (projected["freshness"], projected["age_s"], projected["remaining_pct"]) == ("fresh", 600.0, 70.0)
    now += timedelta(seconds=120)
    projected = subscription_usage_mod.project_muse_for_status(record)
    assert (projected["freshness"], projected["age_s"], projected["remaining_pct"]) == ("stale_last_good", 720.0, None)
    assert projected["error_code"] == "STALE_DATA"


@pytest.mark.parametrize("used", [-1, 101, float("nan"), float("inf"), True])
def test_muse_out_of_range_window_is_unknown(used):
    record = subscription_usage_mod._muse_record_from_codexbar_payload(
        {
            "provider": "muse",
            "usage": {"primary": {"usedPercent": used, "windowMinutes": 300}},
        }
    )
    assert record["status"] == "unknown"
    assert record["headroom_pct"] is None
    assert record["windows"]["primary"]["remaining_pct"] is None


def test_agy_public_labels_windows_and_resets_drop_private_metadata(monkeypatch):
    payload = _agy_usage_payload(
        {
            "name": "Gemini PRIVATE_LABEL",
            "buckets": [
                {"window": "PRIVATE_WINDOW", "remaining_fraction": 0.8},
                {"window": "weekly", "remaining_fraction": 0.8, "reset_time": "PRIVATE_RESET"},
            ],
        },
        {"name": "PRIVATE_GROUP", "buckets": [{"window": "5h", "remaining_fraction": 1}]},
    )
    record = _probe_agy_stdout(monkeypatch, json.dumps(payload))
    projected = subscription_usage_mod.project_agy_for_status(subscription_usage_mod.get_agy_quota_observation())
    assert "PRIVATE_" not in json.dumps(record) + json.dumps(projected)
    assert projected["quota_groups"] == [
        {
            "key": "gemini_models",
            "label": "Gemini Models",
            "windows": [
                {
                    "window": "weekly",
                    "used_pct": 20.0,
                    "remaining_pct": 80.0,
                    "resets_at": None,
                    "window_minutes": 10080,
                }
            ],
        },
        {
            "key": "group",
            "label": "Quota group",
            "windows": [
                {"window": "5h", "used_pct": 0.0, "remaining_pct": 100.0, "resets_at": None, "window_minutes": 300}
            ],
        },
    ]


@pytest.mark.parametrize("nested", [False, True])
@pytest.mark.parametrize(
    ("envelope", "kind", "code"),
    [
        ({"status": "error", "error": {"code": 429, "message": "PRIVATE_ERROR"}}, "rate_limit", 429),
        ({"status": "RATE_LIMITED"}, "rate_limit", 429),
        ({"error": {"kind": "PRIVATE_KIND", "code": "PRIVATE_CODE"}}, "provider", "PROVIDER_ERROR"),
        ({"status": "PRIVATE_STATUS"}, "provider", "PROVIDER_ERROR"),
        ({"provider": "PRIVATE_PROVIDER"}, "fetch_error", "PROVIDER_MISMATCH"),
    ],
)
def test_agy_failed_envelope_cannot_publish_healthy_quota(monkeypatch, nested, envelope, kind, code):
    payload = _agy_usage_payload({"name": "Gemini Models", "buckets": [{"window": "5h", "remaining_fraction": 0.8}]})
    _probe_agy_stdout(monkeypatch, json.dumps(payload))
    (payload["command"] if nested else payload).update(envelope)
    record = _probe_agy_stdout(monkeypatch, json.dumps(payload), reset=False)
    projected = subscription_usage_mod.project_agy_for_status(subscription_usage_mod.get_agy_quota_observation())
    assert (record["error_kind"], record["error_code"]) == (kind, code)
    assert (projected["status"], projected["freshness"], projected["error_kind"], projected["error_code"]) == (
        "unknown",
        "stale_last_good",
        kind,
        code,
    )
    assert _agy_window(projected, "gemini_models", "5h")["remaining_pct"] is None
    assert "PRIVATE_" not in json.dumps(record) + json.dumps(projected)


@pytest.mark.parametrize("lane", ["muse", "agy"])
def test_public_projection_does_not_trust_cached_provider_metadata(lane):
    record = {
        "freshness": "fresh",
        "age_s": "PRIVATE_AGE",
        "error_kind": "PRIVATE_KIND",
        "error_code": "PRIVATE_CODE",
        "failure_kind": "PRIVATE_FAILURE",
        "source": "PRIVATE_SOURCE",
        "account": "PRIVATE_ACCOUNT",
        "credits": 987654,
        "windows": {
            "primary": {
                "used_pct": 20,
                "remaining_pct": 80,
                "resets_at": "PRIVATE_RESET",
                "window_minutes": "PRIVATE_MINUTES",
                "reset_description": "PRIVATE_DESCRIPTION",
                "label": "PRIVATE_LABEL",
            }
        },
        "quota_groups": [
            {"key": "PRIVATE_KEY", "label": "PRIVATE_LABEL", "windows": []},
            {
                "key": "gemini_models",
                "label": "PRIVATE_LABEL",
                "windows": [
                    {"window": "PRIVATE_WINDOW", "used_pct": 20, "remaining_pct": 80},
                    {"window": "5h", "used_pct": 20, "remaining_pct": 80, "resets_at": "PRIVATE_RESET"},
                ],
            },
        ],
    }
    project = (
        subscription_usage_mod.project_muse_for_status
        if lane == "muse"
        else subscription_usage_mod.project_agy_for_status
    )
    public = project(record)
    assert "PRIVATE_" not in json.dumps(public)
    _assert_no_sentinel_value(public, 987654)
    assert (public["status"], public["remaining_pct"], public["age_s"], public["error_kind"], public["error_code"]) == (
        "unknown",
        None,
        None,
        "provider",
        "PROVIDER_ERROR",
    )
    if lane == "agy":
        assert public["quota_groups"] == [
            {
                "key": "gemini_models",
                "label": "Gemini Models",
                "windows": [
                    {"window": "5h", "used_pct": None, "remaining_pct": None, "resets_at": None, "window_minutes": 300},
                ],
            }
        ]


# --- Codex account b (#12692): one usage row per subscription account ---------

_CODEX_ACCOUNT_KEYS = ("codex", "codex:a", "codex:b")


@pytest.fixture
def two_codex_accounts(monkeypatch):
    """The private boundary answers by account label, without any credential fixture."""
    for key in _CODEX_ACCOUNT_KEYS:
        monkeypatch.delitem(subscription_usage_mod._last_good_data, key, raising=False)
        monkeypatch.delitem(subscription_usage_mod._last_failure_data, key, raising=False)
    cache_invalidate("codexbar_usage:")
    rejected = set()
    answers = {"sub": (11.0, 22.0), "b-sub": (66.0, 77.0)}

    def probe(provider, *, timeout_s, account=None):
        assert provider == "codex" and timeout_s == 1
        if account in rejected:
            return {
                "outcome": "error",
                "error": {"kind": "token_rejected", "code": 401, "message": "Codex OAuth token rejected"},
            }
        session, weekly = answers[account]
        return {
            "outcome": "data",
            "record": {
                "provider": "codex",
                "source": "codex_oauth",
                "openaiDashboard": {},
                "usage": {
                    "primary": {"windowMinutes": 300, "usedPercent": session, "resetsAt": None},
                    "secondary": {"windowMinutes": 10080, "usedPercent": weekly, "resetsAt": None},
                },
            },
        }

    module = _fake_private(monkeypatch)
    module.probe_subscription = probe
    yield rejected
    cache_invalidate("codexbar_usage:")


def test_two_codex_accounts_publish_two_rows_with_their_own_numbers(two_codex_accounts):
    refreshed = subscription_usage_mod.refresh_provider_usage_data(_CODEX_ACCOUNT_KEYS, timeout_s=1.0)
    assert set(refreshed) == set(_CODEX_ACCOUNT_KEYS)

    rows = codexbar_usage_mod.codex_account_usage_snapshot(kick_refresh=False)
    assert set(rows) == {"codex:a", "codex:b"}
    a, b = rows["codex:a"], rows["codex:b"]
    assert (a["codex_account"], a["primary_used_pct"], a["weekly_used_pct"]) == ("sub", 11.0, 22.0)
    assert (b["codex_account"], b["primary_used_pct"], b["weekly_used_pct"]) == ("b-sub", 66.0, 77.0)
    assert a["freshness"] == b["freshness"] == "fresh"
    # Compatibility: ``codex`` keeps meaning account a until slice B moves its consumers.
    legacy = subscription_usage_mod.get_provider_usage_data("codex", kick_refresh=False)
    assert (legacy["codex_account"], legacy["weekly_used_pct"]) == ("sub", 22.0)
    assert "fixture-token" not in json.dumps(rows) + json.dumps(legacy)


@pytest.mark.parametrize(("expired", "healthy"), [("codex:b", "codex:a"), ("codex:a", "codex:b")])
def test_expired_codex_token_marks_only_that_account_unavailable(two_codex_accounts, expired, healthy):
    subscription_usage_mod.refresh_provider_usage_data(_CODEX_ACCOUNT_KEYS, timeout_s=1.0)
    two_codex_accounts.add("b-sub" if expired == "codex:b" else "sub")
    # The expired account has no earlier good reading to fall back to.
    for key in subscription_usage_mod._stored_usage_keys(expired):
        subscription_usage_mod._last_good_data.pop(key, None)
        cache_invalidate(f"codexbar_usage:{key}")

    refreshed = subscription_usage_mod.refresh_provider_usage_data(_CODEX_ACCOUNT_KEYS, timeout_s=1.0)
    assert expired not in refreshed and healthy in refreshed

    rows = codexbar_usage_mod.codex_account_usage_snapshot(kick_refresh=False)
    dead, live = rows[expired], rows[healthy]
    assert dead["status"] == "unavailable"
    assert (dead["failure_kind"], dead["last_failure_code"]) == ("token_rejected", 401)
    assert dead["weekly_used_pct"] is None and dead["primary_used_pct"] is None
    assert dead["codex_account"] == ("b-sub" if expired == "codex:b" else "sub")
    expected_numbers = (66.0, 77.0) if healthy == "codex:b" else (11.0, 22.0)
    assert (live["primary_used_pct"], live["weekly_used_pct"]) == expected_numbers
    assert live["failure_kind"] is None
    assert "fixture-token" not in json.dumps(rows)


@pytest.fixture
def private_binding(tmp_path, monkeypatch):
    from scripts.opsec import prepublish

    monkeypatch.setattr(prepublish, "primary_root", lambda: tmp_path / "public")
    monkeypatch.setattr(prepublish, "catalog", lambda: {"infra-private": {"local_name": "private"}})
    directory = tmp_path / "private" / "tools" / "fleet_usage"
    directory.mkdir(parents=True)
    monkeypatch.delitem(sys.modules, "_lu_private_fleet_usage", raising=False)
    subscription_usage_mod._load_private_usage.cache_clear()
    yield directory / "usage.py"
    subscription_usage_mod._load_private_usage.cache_clear()
    sys.modules.pop("_lu_private_fleet_usage", None)


_REQUIRED_PRIVATE_ENTRY_POINTS = (
    "probe_subscription",
    "probe_api_account",
    "api_key_present",
    "prepaid_remaining_usd",
    "prove_claude_owner",
    "credential_inventory",
)


def _private_module_source(*, version="1", missing=None):
    lines = [f"INTERFACE_VERSION = {version}"]
    for name in _REQUIRED_PRIVATE_ENTRY_POINTS:
        if name != missing:
            lines.append(f"def {name}(*args, **kwargs): return None")
    return "\n".join(lines)


@pytest.mark.parametrize("version", ["0", "2", "True", "1.0", "'1'"])
def test_private_binding_incompatible_version_is_unavailable(private_binding, version):
    private_binding.write_text(_private_module_source(version=version))
    result = subscription_usage_mod.fetch_provider_usage("codex:b", timeout_s=1)
    assert result["error_code"] == "PRIVATE_TOOLING_UNAVAILABLE"
    assert result["codex_account"] == "b-sub"
    assert result["weekly_used_pct"] is None


@pytest.mark.parametrize("missing", _REQUIRED_PRIVATE_ENTRY_POINTS)
def test_private_binding_missing_entry_point_is_unavailable(private_binding, missing):
    private_binding.write_text(_private_module_source(missing=missing))
    result = subscription_usage_mod.fetch_provider_usage("claude", timeout_s=1)
    assert result["error_code"] == "PRIVATE_TOOLING_UNAVAILABLE"
    assert result["status"] == "unavailable"
    assert result["weekly_used_pct"] is None


@pytest.mark.parametrize("provider", ["claude", "codex", "codex:a", "codex:b", "kimi", "grok"])
def test_absent_private_binding_subscription_fails_closed(private_binding, provider, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: pytest.fail("public probe must never discover credentials"))
    result = subscription_usage_mod.fetch_provider_usage(provider, timeout_s=1)
    assert result["error_code"] == "PRIVATE_TOOLING_UNAVAILABLE"
    assert result["error_kind"] == "unavailable"
    assert result["auth_error"] == "private usage tooling unavailable"
    assert result["primary_used_pct"] is None and result["weekly_used_pct"] is None
    assert subscription_usage_mod._probe_glm_native(timeout_s=1)["error_code"] == "PRIVATE_TOOLING_UNAVAILABLE"


@pytest.mark.parametrize("provider", ["openrouter", "deepseek"])
def test_absent_private_binding_prepaid_needs_probe(private_binding, provider):
    result = subscription_usage_mod._probe_api_account_live(provider, timeout_s=1)
    assert result["probe_state"] == "NEED_PROBE"
    assert result["auth_error"] == "private usage tooling unavailable"
    assert result.get("total_balance") is None and result.get("account_remaining_usd") is None


def test_private_binding_load_failure_is_quiet_and_unavailable(private_binding, capsys):
    private_binding.write_text("print('SYNTHETIC_PRIVATE_DETAIL')\nraise RuntimeError('SYNTHETIC_PRIVATE_DETAIL')")
    result = subscription_usage_mod.fetch_provider_usage("claude", timeout_s=1)
    assert result["error_code"] == "PRIVATE_TOOLING_UNAVAILABLE"
    assert capsys.readouterr() == ("", "")
    assert "SYNTHETIC_PRIVATE_DETAIL" not in json.dumps(result)


@pytest.mark.parametrize("provider", ["claude", "codex", "codex:a", "codex:b", "kimi", "grok"])
def test_private_outcome_keeps_public_normalization(monkeypatch, provider):
    outcome = {
        "outcome": "data",
        "record": {
            "provider": "codex" if provider.startswith("codex") else provider,
            "source": "synthetic",
            "openaiDashboard": {},
            "usage": {
                "primary": {"windowMinutes": 300, "usedPercent": 12.5, "resetsAt": None},
                "secondary": {"windowMinutes": 10080, "usedPercent": 37.5, "resetsAt": None},
            },
            "credit_balance": 0,
            "reset_credits": {"available_count": 0, "expires_at": []},
        },
    }
    seen = []
    module = _fake_private(monkeypatch)

    def probe(name, *, timeout_s, account=None):
        seen.append((name, timeout_s, account))
        return outcome

    module.probe_subscription = probe
    result = subscription_usage_mod.fetch_provider_usage(provider, timeout_s=3)
    assert result["status"] == "healthy"
    assert result["primary_used_pct"] == 12.5 and result["weekly_used_pct"] == 37.5
    assert result["primary_remaining_pct"] == 87.5 and result["weekly_remaining_pct"] == 62.5
    assert result["windows"]["secondary"]["window_minutes"] == 10080
    if provider.startswith("codex"):
        label = "b-sub" if provider == "codex:b" else "sub"
        assert seen == [("codex", 3, label)]
        assert result["codex_account"] == label
        assert result["credit_balance"] == 0 and result["reset_credits"]["available_count"] == 0
    else:
        assert seen == [(provider, 3, None)]


def test_path_loaded_private_module_normalizes_data(private_binding, capsys):
    outcome = {
        "outcome": "data",
        "record": {
            "provider": "codex",
            "source": "synthetic",
            "openaiDashboard": {},
            "usage": {
                "primary": {"windowMinutes": 300, "usedPercent": 12.5, "resetsAt": None},
                "secondary": {"windowMinutes": 10080, "usedPercent": 37.5, "resetsAt": None},
            },
        },
    }
    private_binding.write_text(
        "from __future__ import annotations\n"
        "from dataclasses import dataclass\n"
        "@dataclass\n"
        "class Outcome:\n"
        "    value: dict\n"
        + _private_module_source()
        + "\nprint('SYNTHETIC_PRIVATE_DETAIL')\n"
        + "def probe_subscription(provider, *, timeout_s, account=None):\n"
        + "    assert (provider, timeout_s, account) == ('codex', 3, 'b-sub')\n"
        + f"    return Outcome({outcome!r}).value\n"
    )
    result = subscription_usage_mod.fetch_provider_usage("codex:b", timeout_s=3)
    assert result["status"] == "healthy"
    assert result["codex_account"] == "b-sub"
    assert (result["primary_used_pct"], result["weekly_used_pct"]) == (12.5, 37.5)
    assert (result["primary_remaining_pct"], result["weekly_remaining_pct"]) == (87.5, 62.5)
    assert result["source"] == "synthetic"
    assert capsys.readouterr() == ("", "")
