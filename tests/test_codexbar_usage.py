"""Tests for codexbar usage fetching, normalization, and routing budget warnings."""

from __future__ import annotations

import json
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

from scripts.analytics.cost_report import CostRecord
from scripts.api import codexbar_usage as codexbar_usage_mod
from scripts.api import subscription_usage as subscription_usage_mod
from scripts.api import state_router
from scripts.api.codexbar_usage import _normalize_provider_data
from scripts.api.state_helpers import cache_invalidate

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
      "accountOrganization": "krisztian.koos@gmail.com's Organization",
      "accountEmail": "krisztian.koos@gmail.com",
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
        "accountOrganization": "krisztian.koos@gmail.com's Organization",
        "accountEmail": "krisztian.koos@gmail.com"
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
        "accountEmail": "krisztian.koos@gmail.com",
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
      "accountEmail": "krisztian.koos@gmail.com",
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
    assert res["windows"]["secondary"]["label"] == "Auto"
    assert res["windows"]["tertiary"]["label"] == "API"
    assert res["windows"]["tertiary"]["used_pct"] == 100.0
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

    # Simulate routing budget calculation state mapping
    def get_status(cb_data):
        weekly_used = cb_data["weekly_used_pct"]
        is_in_deficit = (
            (cb_data.get("will_last_to_reset") is False)
            or (cb_data.get("weekly_pace_delta_pct") is not None and cb_data["weekly_pace_delta_pct"] > 0)
            or (weekly_used >= 90.0)
        )
        if weekly_used >= 90.0:
            return "near_cap"
        elif is_in_deficit:
            return "hot"
        elif weekly_used < 50.0:
            return "cool"
        return "warm"

    assert get_status(res_claude) == "hot"

    # 2. Cool status
    raw_claude["pace"]["secondary"]["willLastToReset"] = True
    raw_claude["pace"]["secondary"]["deltaPercent"] = -10.0
    raw_claude["usage"]["secondary"]["usedPercent"] = 35.0
    res_cool = _normalize_provider_data("claude", raw_claude)
    assert get_status(res_cool) == "cool"

    # 3. Near cap status
    raw_claude["usage"]["secondary"]["usedPercent"] = 92.0
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
    monkeypatch.setattr(state_router, "load_cost_records", lambda: [])
    monkeypatch.setattr(state_router, "summarize_fleet_burn", lambda agent, **kwargs: {
        "source": "agent_runtime_jsonl",
        "agent": agent,
        "windows": {"7d": {"counts": {"total": 0}, "hours": 0.0}},
    })
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


def test_routing_budget_cursor_burns_auto_and_warns_on_api(monkeypatch):
    """Cursor burn tracks Auto monthly pool; exhausted API allotment emits advisory warning."""
    cursor_row = {
        "lane": "cursor",
        "login_state": "authenticated",
        "probe_state": "healthy",
        "primary_used_pct": 36.0,
        "primary_remaining_pct": 64.0,
        "secondary_used_pct": 36.0,
        "secondary_remaining_pct": 64.0,
        "tertiary_used_pct": 100.0,
        "tertiary_remaining_pct": 0.0,
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
                "used_pct": 100.0,
                "remaining_pct": 0.0,
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
                "used_pct": 100.0,
                "remaining_pct": 0.0,
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
    monkeypatch.setattr(state_router, "load_cost_records", lambda: [])
    monkeypatch.setattr(state_router, "summarize_fleet_burn", lambda agent, **kwargs: {
        "source": "agent_runtime_jsonl",
        "agent": agent,
        "windows": {"7d": {"counts": {"total": 0}, "hours": 0.0}},
    })
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
    assert cursor["provider_windows"]["api"]["used_pct"] == 100.0
    api_warnings = [w for w in res["recommendation"]["warnings"] if "API/on-demand" in w]
    assert api_warnings
    assert "100% used" in api_warnings[0]


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
    monkeypatch.setattr(subscription_usage_mod, "_load_kimi_bearer", lambda: "fixture-token")
    monkeypatch.setattr(
        subscription_usage_mod,
        "_http_json_request",
        lambda *args, **kwargs: (
            401,
            {"error": "expired"},
            "Kimi Code CLI credential is expired, please re-authenticate",
        ),
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


def test_kimi_provider_error_with_nonzero_exit_still_surfaces(monkeypatch):
    """HTTP 401 on credential errors must surface the payload, not be swallowed."""
    monkeypatch.setattr(subscription_usage_mod, "_load_kimi_bearer", lambda: "fixture-token")
    monkeypatch.setattr(
        subscription_usage_mod,
        "_http_json_request",
        lambda *args, **kwargs: (401, None, "credential is expired"),
    )
    codexbar_usage_mod._last_good_data.pop("kimi", None)

    res = codexbar_usage_mod.fetch_codexbar_usage("kimi", timeout_s=1.0)

    assert res is not None
    assert res["status"] in ("unavailable", "unknown")
    assert "expired" in (res["auth_error"] or "").lower() or "credential" in (res["auth_error"] or "").lower()


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
    monkeypatch.setattr(subscription_usage_mod, "_load_codex_oauth_token", lambda: None)
    codexbar_usage_mod._last_good_data.pop("codex", None)

    res = codexbar_usage_mod.fetch_codexbar_usage("codex", timeout_s=1.0)
    assert res["status"] == "unavailable"
    assert res["error_kind"] == "need_login"
    assert res["probe_state"] == "NEED_LOGIN"
    assert "credential" in res["auth_error"].lower()


def test_native_probe_unavailable_missing_credentials(monkeypatch):
    """Regression: missing credentials must not masquerade as a healthy 0% lane."""
    monkeypatch.setattr(subscription_usage_mod, "_load_codex_oauth_token", lambda: None)
    codexbar_usage_mod._last_good_data.pop("codex", None)

    res = codexbar_usage_mod.fetch_codexbar_usage("codex", timeout_s=1.0)
    assert res["status"] == "unavailable"
    assert res["error_kind"] == "need_login"
    assert "credential" in res["auth_error"].lower()

    now = datetime(2026, 5, 13, 20, 30, tzinfo=UTC)
    record = CostRecord(
        path=Path("fixture-meta.json"),
        level="a1", slug="fixture", phase="write", agent="codex", model="fixture-model",
        model_source="stored", ok=True, timestamp=now.isoformat(), mtime=now,
        prompt_chars=1, response_chars=1, prompt_tokens_est=1, response_tokens_est=1,
        prompt_tokens_source="stored", response_tokens_source="stored", rate_model="fixture-model",
        used_default_rate=False, cost_usd_est=500.0,
    )
    monkeypatch.setattr(state_router, "load_cost_records", lambda: [record])
    monkeypatch.setattr(state_router, "get_provider_usage_data", lambda p: res if p == "codex" else None)

    data = state_router.compute_routing_budget(now)
    assert data["agents"]["codex"]["status"] == "warm"
    assert data["agents"]["codex"]["burn_pct_7d"] is not None
    assert data["agents"]["codex"]["remaining_pct"] is not None
    assert data["agents"]["codex"]["codexbar"]["status"] == "unavailable"
    assert data["agents"]["codex"]["codexbar"]["error_kind"] == "need_login"


def test_codexbar_unavailable_timeout(monkeypatch):
    """Regression test for timeout: must surface status='unavailable' and auth_error."""
    monkeypatch.setattr(subscription_usage_mod, "_load_codex_oauth_token", lambda: "fixture-token")
    monkeypatch.setattr(
        subscription_usage_mod,
        "_http_json_request",
        lambda *args, **kwargs: (0, None, "timed out after 1s"),
    )
    codexbar_usage_mod._last_good_data.pop("codex", None)

    res = codexbar_usage_mod.fetch_codexbar_usage("codex", timeout_s=1.0)
    assert res["status"] == "unavailable"
    assert res["error_kind"] == "fetch_error"
    assert "timed out" in res["auth_error"].lower()

    now = datetime(2026, 5, 13, 20, 30, tzinfo=UTC)
    record = CostRecord(
        path=Path("fixture-meta.json"),
        level="a1", slug="fixture", phase="write", agent="codex", model="fixture-model",
        model_source="stored", ok=True, timestamp=now.isoformat(), mtime=now,
        prompt_chars=1, response_chars=1, prompt_tokens_est=1, response_tokens_est=1,
        prompt_tokens_source="stored", response_tokens_source="stored", rate_model="fixture-model",
        used_default_rate=False, cost_usd_est=500.0,
    )
    monkeypatch.setattr(state_router, "load_cost_records", lambda: [record])
    monkeypatch.setattr(state_router, "get_provider_usage_data", lambda p: res if p == "codex" else None)

    data = state_router.compute_routing_budget(now)
    assert data["agents"]["codex"]["status"] == "warm"
    assert data["agents"]["codex"]["burn_pct_7d"] is not None
    assert data["agents"]["codex"]["remaining_pct"] is not None
    assert data["agents"]["codex"]["codexbar"]["status"] == "unavailable"
    assert data["agents"]["codex"]["codexbar"]["error_kind"] == "fetch_error"


def test_codexbar_unavailable_nonzero_exit(monkeypatch):
    """Regression test for HTTP failure: must surface status='unavailable' and auth_error."""
    monkeypatch.setattr(subscription_usage_mod, "_load_codex_oauth_token", lambda: "fixture-token")
    monkeypatch.setattr(
        subscription_usage_mod,
        "_http_json_request",
        lambda *args, **kwargs: (500, None, "fatal upstream error"),
    )
    codexbar_usage_mod._last_good_data.pop("codex", None)

    res = codexbar_usage_mod.fetch_codexbar_usage("codex", timeout_s=1.0)
    assert res["status"] == "unavailable"
    assert res["error_kind"] == "fetch_error"
    assert "fatal upstream error" in res["auth_error"]

    now = datetime(2026, 5, 13, 20, 30, tzinfo=UTC)
    record = CostRecord(
        path=Path("fixture-meta.json"),
        level="a1", slug="fixture", phase="write", agent="codex", model="fixture-model",
        model_source="stored", ok=True, timestamp=now.isoformat(), mtime=now,
        prompt_chars=1, response_chars=1, prompt_tokens_est=1, response_tokens_est=1,
        prompt_tokens_source="stored", response_tokens_source="stored", rate_model="fixture-model",
        used_default_rate=False, cost_usd_est=500.0,
    )
    monkeypatch.setattr(state_router, "load_cost_records", lambda: [record])
    monkeypatch.setattr(state_router, "get_provider_usage_data", lambda p: res if p == "codex" else None)

    data = state_router.compute_routing_budget(now)
    assert data["agents"]["codex"]["status"] == "warm"
    assert data["agents"]["codex"]["burn_pct_7d"] is not None
    assert data["agents"]["codex"]["remaining_pct"] is not None
    assert data["agents"]["codex"]["codexbar"]["status"] == "unavailable"
    assert data["agents"]["codex"]["codexbar"]["error_kind"] == "fetch_error"


def test_codexbar_unavailable_malformed_json(monkeypatch):
    """Regression test for malformed JSON: must surface status='unavailable' and auth_error."""
    monkeypatch.setattr(subscription_usage_mod, "_load_codex_oauth_token", lambda: "fixture-token")

    def _bad_json(*args, **kwargs):
        raise json.JSONDecodeError("bad", "doc", 0)

    monkeypatch.setattr(subscription_usage_mod, "_http_json_request", _bad_json)
    codexbar_usage_mod._last_good_data.pop("codex", None)

    res = codexbar_usage_mod.fetch_codexbar_usage("codex", timeout_s=1.0)
    assert res["status"] == "unavailable"
    assert res["error_kind"] == "fetch_error"

    now = datetime(2026, 5, 13, 20, 30, tzinfo=UTC)
    record = CostRecord(
        path=Path("fixture-meta.json"),
        level="a1", slug="fixture", phase="write", agent="codex", model="fixture-model",
        model_source="stored", ok=True, timestamp=now.isoformat(), mtime=now,
        prompt_chars=1, response_chars=1, prompt_tokens_est=1, response_tokens_est=1,
        prompt_tokens_source="stored", response_tokens_source="stored", rate_model="fixture-model",
        used_default_rate=False, cost_usd_est=500.0,
    )
    monkeypatch.setattr(state_router, "load_cost_records", lambda: [record])
    monkeypatch.setattr(state_router, "get_provider_usage_data", lambda p: res if p == "codex" else None)

    data = state_router.compute_routing_budget(now)
    assert data["agents"]["codex"]["status"] == "warm"
    assert data["agents"]["codex"]["burn_pct_7d"] is not None
    assert data["agents"]["codex"]["remaining_pct"] is not None
    assert data["agents"]["codex"]["codexbar"]["status"] == "unavailable"
    assert data["agents"]["codex"]["codexbar"]["error_kind"] == "fetch_error"


def test_codexbar_unavailable_unparseable_schema(monkeypatch):
    """Regression test for empty schema: must surface status='unavailable'."""
    monkeypatch.setattr(subscription_usage_mod, "_load_codex_oauth_token", lambda: "fixture-token")
    monkeypatch.setattr(
        subscription_usage_mod,
        "_http_json_request",
        lambda *args, **kwargs: (200, {}, None),
    )
    codexbar_usage_mod._last_good_data.pop("codex", None)

    res = codexbar_usage_mod.fetch_codexbar_usage("codex", timeout_s=1.0)
    assert res["status"] == "unavailable"

    now = datetime(2026, 5, 13, 20, 30, tzinfo=UTC)
    record = CostRecord(
        path=Path("fixture-meta.json"),
        level="a1", slug="fixture", phase="write", agent="codex", model="fixture-model",
        model_source="stored", ok=True, timestamp=now.isoformat(), mtime=now,
        prompt_chars=1, response_chars=1, prompt_tokens_est=1, response_tokens_est=1,
        prompt_tokens_source="stored", response_tokens_source="stored", rate_model="fixture-model",
        used_default_rate=False, cost_usd_est=500.0,
    )
    monkeypatch.setattr(state_router, "load_cost_records", lambda: [record])
    monkeypatch.setattr(state_router, "get_provider_usage_data", lambda p: res if p == "codex" else None)

    data = state_router.compute_routing_budget(now)
    assert data["agents"]["codex"]["status"] == "warm"
    assert data["agents"]["codex"]["burn_pct_7d"] is not None
    assert data["agents"]["codex"]["remaining_pct"] is not None
    assert data["agents"]["codex"]["codexbar"]["status"] == "unavailable"
    assert data["agents"]["codex"]["codexbar"]["error_kind"] == "unparseable_schema"


def test_dashboard_routing_html_renders_unavailable_explicitly():
    """Prove dashboards/routing.html renders 'unknown' non-numeric display, not 0.0% or 0-width bar."""
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
        codex: {
          status: 'unavailable',
          burn_pct_7d: null,
          remaining_pct: null,
          codexbar: { weekly_used_pct: null, fetched_at: null }
        }
      },
      in_flight: {}
    });

    console.log(innerHTML);
    """
    res = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True, timeout=30)
    out = res.stdout
    assert "0.0%" not in out, f"Dashboard rendered 0.0% for unavailable state: {out}"
    assert 'style="width:0%"' not in out, f"Dashboard rendered 0-width bar for unavailable state: {out}"
    assert "unknown" in out
    assert 'class="bar unavailable"' in out or 'class="pill unknown"' in out


def test_dashboard_routing_html_renders_cursor_auto_api_subscriptions():
    """Subscriptions table must show Cursor Auto + API percents from provider_windows."""
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
          status: 'cool',
          login_state: 'authenticated',
          probe_state: 'healthy',
          provider_windows: {
            auto: { window: 'monthly', label: 'Auto', used_pct: 23, remaining_pct: 77, resets_at: '2026-09-01T00:00:00Z' },
            api: { window: 'monthly', label: 'API', used_pct: 40, remaining_pct: 60, resets_at: '2026-09-01T00:00:00Z' },
          },
          codexbar: { fetched_at: '2026-08-26T12:00:00Z', age_s: 120 },
          fleet_burn: { windows: { '5h': { counts: { total: 1 } }, '7d': { counts: { total: 3 } }, '30d': { counts: { total: 10 } } } },
        },
      },
      in_flight: { cursor: 0 },
    });
    console.log(innerHTML);
    """
    res = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True, timeout=30)
    out = res.stdout
    assert "Auto" in out
    assert "API" in out
    assert "23" in out
    assert "40" in out
    assert "77" in out or "60" in out


def test_dashboard_routing_html_need_login_does_not_render_zero_auto_used():
    """NEED_LOGIN fixture must not paint Auto as 0.0% used."""
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
          status: 'need_login',
          login_state: 'NEED_LOGIN',
          probe_state: 'NEED_LOGIN',
          provider_windows: {
            auto: { window: 'monthly', used_pct: null, remaining_pct: null },
            api: { window: 'monthly', used_pct: null, remaining_pct: null },
          },
        },
      },
      in_flight: {},
    });
    console.log(innerHTML);
    """
    res = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True, timeout=30)
    out = res.stdout
    assert "NEED_LOGIN" in out
    assert "0.0%" not in out
    assert 'style="width:0%"' not in out


def test_get_cursor_lane_usage_is_cache_only_on_http_path(monkeypatch):
    """HTTP reads must not block on live Cursor probes."""
    cache_invalidate(codexbar_usage_mod.CURSOR_CACHE_KEY)
    codexbar_usage_mod._cursor_last_good = None
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
                "auto": {"window": "monthly", "label": "Auto", "used_pct": 12.0, "remaining_pct": 88.0, "resets_at": None},
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


def test_cache_miss_starts_background_refresh_without_waiting(monkeypatch):
    provider = "grok"
    cache_invalidate("codexbar_usage:")
    codexbar_usage_mod._last_good_data.pop(provider, None)
    codexbar_usage_mod._last_failure_data.pop(provider, None)
    monkeypatch.setattr(subscription_usage_mod, "_refresh_thread", None)
    monkeypatch.setenv("CODEXBAR_ON_DEMAND_REFRESH", "1")
    entered = threading.Event()
    release = threading.Event()

    def slow_background() -> None:
        entered.set()
        release.wait(timeout=1.0)

    monkeypatch.setattr(subscription_usage_mod, "_run_all_refreshes", slow_background)
    started = time.monotonic()
    result = codexbar_usage_mod.get_provider_usage_data(provider)
    elapsed = time.monotonic() - started
    release.set()
    assert entered.wait(timeout=0.5)
    assert elapsed < 0.2
    assert result["freshness"] == "unavailable"


def test_default_refresh_timeout_floor_matches_real_cli_latency(monkeypatch):
    """Regression: the prior 2.0s default never let the claude lane's CLI
    probe complete (live-measured 2026-08-04: `codexbar usage --json
    --provider claude` took ~17s twice in a row, its own dashboard-fetch
    latency, not a hang), which painted a healthy lane as capacity-unavailable
    — the routing-budget false-red this dispatch fixes."""
    monkeypatch.delenv("CODEXBAR_REFRESH_TIMEOUT_S", raising=False)
    assert (
        codexbar_usage_mod._codexbar_refresh_timeout_s()
        == codexbar_usage_mod.DEFAULT_CODEXBAR_REFRESH_TIMEOUT_S
    )
    # Comfortable margin above the live-measured ~17s worst case.
    assert codexbar_usage_mod.DEFAULT_CODEXBAR_REFRESH_TIMEOUT_S >= 20.0


def test_refresh_timeout_env_override(monkeypatch):
    """CODEXBAR_REFRESH_TIMEOUT_S lets a slower box or CI raise/lower the floor."""
    monkeypatch.setenv("CODEXBAR_REFRESH_TIMEOUT_S", "9.5")
    assert codexbar_usage_mod._codexbar_refresh_timeout_s() == 9.5

    # Malformed or non-positive overrides fall back to the safe default
    # rather than passing a bad value to subprocess.run(timeout=...).
    monkeypatch.setenv("CODEXBAR_REFRESH_TIMEOUT_S", "not-a-number")
    assert (
        codexbar_usage_mod._codexbar_refresh_timeout_s()
        == codexbar_usage_mod.DEFAULT_CODEXBAR_REFRESH_TIMEOUT_S
    )

    monkeypatch.setenv("CODEXBAR_REFRESH_TIMEOUT_S", "-5")
    assert (
        codexbar_usage_mod._codexbar_refresh_timeout_s()
        == codexbar_usage_mod.DEFAULT_CODEXBAR_REFRESH_TIMEOUT_S
    )


def test_refresh_provider_usage_data_defaults_to_realistic_timeout(monkeypatch):
    """The blocking fresh-refresh path must pass the realistic default to native probes."""
    monkeypatch.delenv("CODEXBAR_REFRESH_TIMEOUT_S", raising=False)
    seen_timeouts = []

    def fake_fetch(provider, *, timeout_s):
        seen_timeouts.append(timeout_s)
        return _normalize_provider_data(provider, json.loads(CODEX_FIXTURE)[0])

    monkeypatch.setattr(subscription_usage_mod, "fetch_provider_usage", fake_fetch)
    codexbar_usage_mod.refresh_provider_usage_data(["codex"])
    assert seen_timeouts == [codexbar_usage_mod.DEFAULT_CODEXBAR_REFRESH_TIMEOUT_S]


def test_background_refresh_no_longer_hardcodes_two_second_timeout(monkeypatch):
    """_run_all_refreshes previously hardcoded timeout_s=2.0 directly, even
    though it runs on a non-blocking daemon thread with no reason to use a
    shorter timeout than the explicit fresh-refresh path."""
    captured = {}

    def fake_refresh(providers, *, timeout_s=None):
        captured["timeout_s"] = timeout_s
        captured["providers"] = tuple(providers)
        return {}

    monkeypatch.setattr(subscription_usage_mod, "refresh_provider_usage_data", fake_refresh)
    monkeypatch.setattr(subscription_usage_mod, "_refresh_cursor_usage_live", lambda: None)
    monkeypatch.setattr(subscription_usage_mod, "_refresh_api_accounts_live", lambda: None)
    monkeypatch.setattr(subscription_usage_mod, "_refresh_in_flight", threading.Lock())
    subscription_usage_mod._run_all_refreshes()
    # No override passed -> refresh_provider_usage_data resolves the shared
    # realistic default itself, instead of the caller hardcoding 2.0.
    assert captured["timeout_s"] is None
    assert "claude" in captured["providers"]
    assert "cursor" not in captured["providers"]


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


def test_default_cache_ttl_is_twelve_minutes(monkeypatch):
    monkeypatch.delenv("CODEXBAR_CACHE_TTL_S", raising=False)
    monkeypatch.delenv("CODEXBAR_REFRESH_INTERVAL_S", raising=False)
    assert codexbar_usage_mod.DEFAULT_CODEXBAR_CACHE_TTL_S == 720.0
    assert codexbar_usage_mod._codexbar_cache_ttl_s() == 720.0
    assert codexbar_usage_mod._codexbar_refresh_interval_s() == 720.0


def test_cache_ttl_env_override(monkeypatch):
    monkeypatch.setenv("CODEXBAR_CACHE_TTL_S", "900")
    monkeypatch.setenv("CODEXBAR_REFRESH_INTERVAL_S", "600")
    assert codexbar_usage_mod._codexbar_cache_ttl_s() == 900.0
    assert codexbar_usage_mod._codexbar_refresh_interval_s() == 600.0
    monkeypatch.setenv("CODEXBAR_CACHE_TTL_S", "nope")
    assert codexbar_usage_mod._codexbar_cache_ttl_s() == 720.0


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

    def fake_run() -> None:
        runs.set()

    monkeypatch.setenv("CODEXBAR_PERIODIC_REFRESH", "1")
    monkeypatch.setenv("CODEXBAR_REFRESH_INTERVAL_S", "30")
    monkeypatch.setattr(subscription_usage_mod, "_run_all_refreshes", fake_run)
    monkeypatch.setattr(subscription_usage_mod, "_scheduler_thread", None)
    try:
        codexbar_usage_mod.start_periodic_refresh(run_immediately=True)
        assert runs.wait(timeout=1.0)
        assert codexbar_usage_mod.scheduler_status()["scheduler_running"] is True
        assert codexbar_usage_mod.scheduler_status()["cache_ttl_s"] == 720.0
    finally:
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

    monkeypatch.setattr(subscription_usage_mod, "refresh_provider_usage_data", fake_refresh)
    monkeypatch.setattr(subscription_usage_mod, "_refresh_cursor_usage_live", lambda: None)
    monkeypatch.setattr(subscription_usage_mod, "_refresh_api_accounts_live", lambda: None)
    monkeypatch.setattr(subscription_usage_mod, "_refresh_in_flight", threading.Lock())
    worker = threading.Thread(target=subscription_usage_mod._run_all_refreshes, daemon=True)
    worker.start()
    assert started.wait(timeout=1.0)
    subscription_usage_mod._run_all_refreshes()  # must no-op while first is in flight
    release.set()
    worker.join(timeout=1.0)
    assert calls == [tuple(codexbar_usage_mod.SUBSCRIPTION_LANES_WITHOUT_CURSOR)]


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


def test_openrouter_missing_key_returns_need_probe(monkeypatch):
    monkeypatch.setattr(subscription_usage_mod, "_load_openrouter_api_key", lambda: None)
    codexbar_usage_mod._api_account_last_good.pop("openrouter", None)
    result = subscription_usage_mod._probe_openrouter_native(timeout_s=1.0)
    assert result["probe_state"] == "NEED_PROBE"
    assert result["usage_usd"] is None
    assert result["limit_remaining_usd"] is None


def test_deepseek_missing_key_returns_need_probe(monkeypatch):
    monkeypatch.setattr(subscription_usage_mod, "_load_deepseek_api_key", lambda: None)
    codexbar_usage_mod._api_account_last_good.pop("deepseek", None)
    result = subscription_usage_mod._probe_deepseek_native(timeout_s=1.0)
    assert result["probe_state"] == "NEED_PROBE"
    assert result["total_balance"] is None
    assert result["local_only"] is True


def test_openrouter_key_probe_success(monkeypatch):
    monkeypatch.setattr(subscription_usage_mod, "_load_openrouter_api_key", lambda: "fixture-openrouter-key")

    def _fake_http(method, url, **kwargs):
        if url.endswith("/key"):
            return 200, dict(OPENROUTER_KEY_FIXTURE), None
        return 0, None, "unexpected url"

    monkeypatch.setattr(subscription_usage_mod, "_http_json_request", _fake_http)
    result = subscription_usage_mod._probe_openrouter_native(timeout_s=1.0)
    assert result["probe_state"] == "ok"
    assert result["usage_usd"] == 12.5
    assert result["limit_remaining_usd"] == 87.5
    assert result["is_free_tier"] is False


def test_deepseek_balance_probe_success(monkeypatch):
    monkeypatch.setattr(subscription_usage_mod, "_load_deepseek_api_key", lambda: "fixture-deepseek-key")
    monkeypatch.setattr(
        subscription_usage_mod,
        "_http_json_request",
        lambda *args, **kwargs: (200, dict(DEEPSEEK_BALANCE_FIXTURE), None),
    )
    result = subscription_usage_mod._probe_deepseek_native(timeout_s=1.0)
    assert result["probe_state"] == "ok"
    assert result["local_only"] is True
    assert result["currency"] == "USD"
    assert result["total_balance"] == 42.5
    assert result["is_available"] is True


def test_compute_routing_budget_includes_api_accounts(monkeypatch, tmp_path):
    monkeypatch.setattr(state_router, "BUDGET_CONFIG_PATH", tmp_path / "agent_budgets.yaml")
    (tmp_path / "agent_budgets.yaml").write_text("codex:\n  weekly_cap_usd: 1000\n", encoding="utf-8")
    monkeypatch.setattr(state_router, "load_cost_records", lambda: [])
    monkeypatch.setattr(state_router, "get_provider_usage_data", lambda p: {"lane": p, "weekly_used_pct": None})
    monkeypatch.setattr(state_router, "get_cursor_lane_usage", lambda **kwargs: {"lane": "cursor", "probe_state": "NEED_PROBE"})
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

    data = state_router.compute_routing_budget(datetime(2026, 8, 26, 12, 0, tzinfo=UTC))
    assert "api_accounts" in data
    assert data["api_accounts"]["openrouter"]["limit_remaining_usd"] == 49.0
    assert data["api_accounts"]["deepseek"]["total_balance"] == 25.0
    ranked_api = [row for row in data["ranked_by_headroom"] if row["type"] == "api"]
    assert len(ranked_api) == 2
    assert ranked_api[0]["remaining_usd"] == 49.0


def test_routing_html_contains_api_accounts_panel():
    text = Path("dashboards/routing.html").read_text(encoding="utf-8")
    assert "API accounts" in text
