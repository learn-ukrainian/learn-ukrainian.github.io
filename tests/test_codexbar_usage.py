"""Tests for codexbar usage fetching, normalization, and routing budget warnings."""

from __future__ import annotations

import json
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

from scripts.analytics.cost_report import CostRecord
from scripts.api import codexbar_usage as codexbar_usage_mod
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
    assert res["source"] == "codexbar"
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
    assert res["primary_used_pct"] == 44.7
    assert abs(res["primary_remaining_pct"] - 55.3) < 0.01
    assert res["secondary_used_pct"] == 36.0
    assert res["secondary_remaining_pct"] == 64.0
    assert res["tertiary_used_pct"] == 100.0
    assert res["tertiary_remaining_pct"] == 0.0
    # Burn/status alias tracks Total (primary), not Auto (secondary).
    assert res["weekly_used_pct"] == 44.7
    assert abs(res["weekly_remaining_pct"] - 55.3) < 0.01
    assert res["weekly_resets_at"] == "2026-08-01T09:58:38Z"
    assert res["windows"]["primary"]["label"] == "Total"
    assert res["windows"]["secondary"]["label"] == "Auto"
    assert res["windows"]["tertiary"]["label"] == "API"
    assert res["windows"]["tertiary"]["used_pct"] == 100.0
    assert res["windows"]["tertiary"]["remaining_pct"] == 0.0
    assert res["windows"]["primary"]["resets_at"] == "2026-08-01T09:58:38Z"
    # Must not quietly copy Total into the Auto window block.
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


def test_routing_budget_cursor_burns_total_and_warns_on_api(monkeypatch):
    """Cursor burn tracks Total; exhausted API allotment emits an advisory warning."""
    cursor_row = {
        "lane": "cursor",
        "primary_used_pct": 44.7,
        "primary_remaining_pct": 55.3,
        "secondary_used_pct": 36.0,
        "secondary_remaining_pct": 64.0,
        "tertiary_used_pct": 100.0,
        "tertiary_remaining_pct": 0.0,
        "weekly_used_pct": 44.7,
        "weekly_remaining_pct": 55.3,
        "windows": {
            "primary": {
                "used_pct": 44.7,
                "remaining_pct": 55.3,
                "resets_at": "2026-08-01T09:58:38Z",
                "window_minutes": 44640,
                "label": "Total",
            },
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
        "source": "codexbar",
        "fetched_at": "2026-07-21T19:00:00Z",
        "stale": False,
        "age_s": 1.0,
        "status": "healthy",
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
    monkeypatch.setattr(state_router, "load_cost_records", lambda: [])

    res = state_router.compute_routing_budget(datetime(2026, 7, 21, 19, 0, tzinfo=UTC))
    cursor = res["agents"]["cursor"]
    assert cursor["burn_pct_7d"] == 44.7
    assert cursor["status"] == "cool"
    assert cursor["codexbar"]["windows"]["primary"]["label"] == "Total"
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
    assert res["source"] == "codexbar"


def test_kimi_provider_error_surfaces_unknown(monkeypatch):
    """Credential/provider error -> status='unknown' + auth_error, never zero usage."""

    class _FakeResult:
        returncode = 0
        stdout = KIMI_ERROR_FIXTURE
        stderr = ""

    monkeypatch.setattr(codexbar_usage_mod.subprocess, "run", lambda cmd, **kw: _FakeResult())
    # Never fall back to last-good data
    codexbar_usage_mod._last_good_data.pop("kimi", None)

    res = codexbar_usage_mod.fetch_codexbar_usage("kimi", timeout_s=1.0)

    assert res is not None
    assert res["lane"] == "kimi"
    assert res["status"] in ("unavailable", "unknown")
    assert res["weekly_used_pct"] is None
    assert res["primary_used_pct"] is None
    assert "credential is expired" in res["auth_error"]
    assert res["error_kind"] == "provider"
    assert res["error_code"] == 1


def test_kimi_provider_error_with_nonzero_exit_still_surfaces(monkeypatch):
    """LIVE-verified gap (2026-07-17): the CLI exits rc=1 on credential errors
    while printing the error JSON — rc alone must not swallow the payload."""

    class _FakeResult:
        returncode = 1
        stdout = KIMI_ERROR_FIXTURE
        stderr = ""

    monkeypatch.setattr(codexbar_usage_mod.subprocess, "run", lambda cmd, **kw: _FakeResult())
    codexbar_usage_mod._last_good_data.pop("kimi", None)

    res = codexbar_usage_mod.fetch_codexbar_usage("kimi", timeout_s=1.0)

    assert res is not None
    assert res["status"] in ("unavailable", "unknown")
    assert "credential is expired" in res["auth_error"]


def test_healthy_record_carries_error_shape_defaults():
    """Healthy and error records share one key shape (review-5386 F2)."""
    raw_list = json.loads(KIMI_HEALTHY_FIXTURE)
    res = _normalize_provider_data("kimi", raw_list[0])
    assert res["status"] == "healthy"
    assert res["auth_error"] is None
    assert res["error_kind"] is None
    assert res["error_code"] is None


def test_missing_homebrew_binary_reaches_path_fallback(monkeypatch):
    """FileNotFoundError on the homebrew path must not bypass the PATH fallback (review-5386 F1)."""
    calls = []

    def fake_run(cmd, **kw):
        calls.append(cmd[0])
        if cmd[0].startswith("/opt/homebrew"):
            raise FileNotFoundError(cmd[0])

        class _R:
            returncode = 0
            stdout = KIMI_HEALTHY_FIXTURE
            stderr = ""

        return _R()

    monkeypatch.setattr(codexbar_usage_mod.subprocess, "run", fake_run)
    res = codexbar_usage_mod.fetch_codexbar_usage("kimi", timeout_s=1.0)
    assert calls == ["/opt/homebrew/bin/codexbar", "codexbar"]
    assert res is not None and res["lane"] == "kimi" and res["status"] == "healthy"


def test_codexbar_unavailable_missing_binary(monkeypatch):
    """Regression test for missing binary: must surface status='unavailable' and auth_error."""
    def fake_run(cmd, **kw):
        raise FileNotFoundError(cmd[0])

    monkeypatch.setattr(codexbar_usage_mod.subprocess, "run", fake_run)
    codexbar_usage_mod._last_good_data.pop("codex", None)

    res = codexbar_usage_mod.fetch_codexbar_usage("codex", timeout_s=1.0)
    assert res["status"] == "unavailable"
    assert res["error_kind"] == "missing_binary"
    assert "binary not found" in res["auth_error"].lower()

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
    assert data["agents"]["codex"]["codexbar"]["error_kind"] == "missing_binary"


def test_codexbar_unavailable_timeout(monkeypatch):
    """Regression test for timeout: must surface status='unavailable' and auth_error."""
    def fake_run(cmd, **kw):
        raise codexbar_usage_mod.subprocess.TimeoutExpired(cmd, 2.0)

    monkeypatch.setattr(codexbar_usage_mod.subprocess, "run", fake_run)
    codexbar_usage_mod._last_good_data.pop("codex", None)

    res = codexbar_usage_mod.fetch_codexbar_usage("codex", timeout_s=1.0)
    assert res["status"] == "unavailable"
    assert res["error_kind"] == "timeout"
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
    assert data["agents"]["codex"]["codexbar"]["error_kind"] == "timeout"


def test_codexbar_unavailable_nonzero_exit(monkeypatch):
    """Regression test for non-zero exit: must surface status='unavailable' and auth_error."""
    class _FakeResult:
        returncode = 1
        stdout = ""
        stderr = "fatal CLI error"

    monkeypatch.setattr(codexbar_usage_mod.subprocess, "run", lambda cmd, **kw: _FakeResult())
    codexbar_usage_mod._last_good_data.pop("codex", None)

    res = codexbar_usage_mod.fetch_codexbar_usage("codex", timeout_s=1.0)
    assert res["status"] == "unavailable"
    assert res["error_kind"] == "non_zero_exit"
    assert "fatal CLI error" in res["auth_error"]

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
    assert data["agents"]["codex"]["codexbar"]["error_kind"] == "non_zero_exit"


def test_codexbar_unavailable_malformed_json(monkeypatch):
    """Regression test for malformed JSON: must surface status='unavailable' and auth_error."""
    class _FakeResult:
        returncode = 0
        stdout = "not valid json {{"
        stderr = ""

    monkeypatch.setattr(codexbar_usage_mod.subprocess, "run", lambda cmd, **kw: _FakeResult())
    codexbar_usage_mod._last_good_data.pop("codex", None)

    res = codexbar_usage_mod.fetch_codexbar_usage("codex", timeout_s=1.0)
    assert res["status"] == "unavailable"
    assert res["error_kind"] == "malformed_json"
    assert "malformed JSON" in res["auth_error"]

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
    assert data["agents"]["codex"]["codexbar"]["error_kind"] == "malformed_json"


def test_codexbar_unavailable_unparseable_schema(monkeypatch):
    """Regression test for unparseable schema: must surface status='unavailable' and auth_error."""
    class _FakeResult:
        returncode = 0
        stdout = "[]"
        stderr = ""

    monkeypatch.setattr(codexbar_usage_mod.subprocess, "run", lambda cmd, **kw: _FakeResult())
    codexbar_usage_mod._last_good_data.pop("codex", None)

    res = codexbar_usage_mod.fetch_codexbar_usage("codex", timeout_s=1.0)
    assert res["status"] == "unavailable"
    assert res["error_kind"] == "unparseable_schema"
    assert "unparseable" in res["auth_error"].lower()

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
    """Prove dashboards/routing.html renders 'unavailable' non-numeric display, not 0.0% or 0-width bar."""
    import subprocess
    script = """
    const fs = require('fs');
    const html = fs.readFileSync('dashboards/routing.html', 'utf8');
    const renderBudgetMatch = html.match(/function renderBudget\\(routing\\) \\{[\\s\\S]*?\\n\\}/);
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

    renderBudget({
      agents: {
        codex: {
          status: 'unavailable',
          burn_pct_7d: null,
          remaining_pct: null,
          weekly_cap_usd: null
        }
      },
      in_flight: {}
    });

    console.log(innerHTML);
    """
    res = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True)
    out = res.stdout
    assert "0.0%" not in out, f"Dashboard rendered 0.0% for unavailable state: {out}"
    assert "style=\"width:0%\"" not in out, f"Dashboard rendered 0-width bar for unavailable state: {out}"
    assert "unavailable" in out
    assert 'class="bar unavailable"' in out


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
    monkeypatch.setattr(codexbar_usage_mod, "fetch_codexbar_usage", lambda *_args, **_kwargs: next(results))

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
    monkeypatch.setattr(codexbar_usage_mod, "fetch_codexbar_usage", lambda *_args, **_kwargs: malformed)

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
    monkeypatch.setattr(codexbar_usage_mod, "_refresh_thread", None)
    entered = threading.Event()
    release = threading.Event()

    def slow_background() -> None:
        entered.set()
        release.wait(timeout=1.0)

    monkeypatch.setattr(codexbar_usage_mod, "_run_all_refreshes", slow_background)
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
    """The blocking fresh-refresh path (state_router fresh_codexbar=True) must
    pass the realistic default down to the CLI subprocess timeout, not the
    prior 2.0s that starved slow lanes like claude."""
    monkeypatch.delenv("CODEXBAR_REFRESH_TIMEOUT_S", raising=False)
    seen_timeouts = []

    def fake_fetch(provider, *, timeout_s):
        seen_timeouts.append(timeout_s)
        return _normalize_provider_data(provider, json.loads(CODEX_FIXTURE)[0])

    monkeypatch.setattr(codexbar_usage_mod, "fetch_codexbar_usage", fake_fetch)
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

    monkeypatch.setattr(codexbar_usage_mod, "refresh_provider_usage_data", fake_refresh)
    codexbar_usage_mod._run_all_refreshes()
    # No override passed -> refresh_provider_usage_data resolves the shared
    # realistic default itself, instead of the caller hardcoding 2.0.
    assert captured["timeout_s"] is None
    assert "claude" in captured["providers"]


def test_timeout_failure_kind_maps_to_fail_open_reviewer_status():
    """Ties this fix to the existing fail-open classification (reviewer_resolver
    operator note 2026-08-03: 'red probe must not ban CF lanes'): a CLI timeout
    must produce status='unavailable', which reviewer_resolver treats as missing
    evidence, never as a dead/unhealthy lane."""
    from scripts.review.reviewer_resolver import _HEALTH_ALIASES

    timeout_result = codexbar_usage_mod._normalize_provider_error(
        "claude",
        {"kind": "timeout", "code": "TIMEOUT", "message": "CodexBar CLI timed out after 25.0s"},
    )
    assert timeout_result["status"] == "unavailable"
    assert timeout_result["error_kind"] == "timeout"
    assert _HEALTH_ALIASES[timeout_result["status"]] is None  # fail-open, not "unhealthy"
