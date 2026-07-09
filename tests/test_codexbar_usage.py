"""Tests for codexbar usage fetching, normalization, and routing budget warnings."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from scripts.api import state_router
from scripts.api.codexbar_usage import _normalize_provider_data

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
    assert res["monthly_cap_usd"] == 20.0
    assert res["monthly_used_usd"] == 0.0
    assert res["weekly_resets_at"] == "2026-07-13T06:59:59Z"
    assert res["weekly_pace_delta_pct"] == 27.0
    assert res["will_last_to_reset"] is False
    assert "27% in deficit" in res["pace_summary"]
    assert res["source"] == "codexbar"
    assert res["fetched_at"] is not None


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
        is_in_deficit = (cb_data.get("will_last_to_reset") is False) or \
                        (cb_data.get("weekly_pace_delta_pct") is not None and cb_data["weekly_pace_delta_pct"] > 0) or \
                        (weekly_used >= 90.0)
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
        }
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

    now = datetime(2026, 7, 9, 16, 13, tzinfo=UTC)
    res = state_router.compute_routing_budget(now)

    assert "claude" in res["agents"]
    assert res["agents"]["claude"]["status"] == "hot"
    assert res["agents"]["codex"]["status"] == "cool"

    # Check that deficit warning was generated for claude
    assert any("lane claude is in deficit" in w for w in res["recommendation"]["warnings"])
