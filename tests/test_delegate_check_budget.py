"""Tests for delegate.py --check-budget pre-dispatch guard."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import pytest

from scripts.fleet import claude_account_lane
from tests.claude_route_accounts import HOST_ACCOUNT, account
from tests.helpers.claude_account_fixtures import (
    UNVERIFIED_ROW as _UNVERIFIED_ROW,
)
from tests.helpers.claude_account_fixtures import (
    account_row as _account_row,
)
from tests.helpers.claude_account_fixtures import (
    accounts_budget as _accounts_budget,
)
from tests.helpers.claude_account_fixtures import (
    default_claude_lane as _default_claude_lane,
)


@pytest.fixture(autouse=True)
def _allow_notebook_dispatch(monkeypatch):
    monkeypatch.setenv("LU_ALLOW_NOTEBOOK_DISPATCH", "1")


# --- #9740 round 2: the budget guard acts on the owner's routing facts -----------------


# --- #10619: a claude dispatch is judged on its selected account's meter ----------------


def test_account_view_keeps_route_facts_but_not_the_default_accounts_meter():
    shared_runtime = {
        "source": "agent_runtime_jsonl",
        "window_s": 300,
        "ok": 3,
        "error": 1,
        "total": 6,
        "circuit_open": False,
        "unreadable": {"total": 0},
    }
    rate_limits = {
        "rate_limited": 2,
        "last_rate_limited_at": "2026-10-15T08:00:00Z",
        "models_rate_limited": ["claude-opus-5-5"],
        "headroom_blocked": True,
        "headroom_reason": "rate_limited 10s ago (2 events in last 5min)",
    }
    scheduler = {"inflight": 1, "capacity_exhausted": False, "circuit_open": False}
    lane = _default_claude_lane("near_cap") | {
        "runtime": shared_runtime | rate_limits,
        "scheduler": scheduler | {"quota_remaining_pct": 0.5, "quota_stale": False},
        "eligible": True,
        "credit_balance": 25.0,
        "fable_weekly": {"used_pct": 3.0},
        "login_state": "NEED_LOGIN",
        "probe_state": "NEED_LOGIN",
    }

    view, unknown = claude_account_lane.lane_view(_account_row(89.0), lane)

    assert unknown is None
    # Route facts stay: spawn health, eligibility, the scheduler's concurrency and runtime outcome counts.
    assert view["health"] == {"healthy": True} and view["eligible"] is True
    assert view["runtime"] == shared_runtime and view["scheduler"] == scheduler
    for key in ("credit_balance", "fable_weekly", "login_state", "probe_state"):
        assert key not in view
    # The account's own probe shape carries no credit or Fable reading, never the default account's.
    assert view["codexbar"]["credit_balance"] is None
    assert view["codexbar"]["fable_weekly"]["used_pct"] is None
    assert "login_state" not in view["codexbar"] and "probe_state" not in view["codexbar"]
    assert "status" not in view["codexbar"]
    # Unattributed rate limits never mark the selected account hot (#10619 finding 2).
    assert view["status"] == view["interactive"]["status"] == "cool"


@pytest.mark.parametrize(
    ("row", "reason"),
    [
        (None, "no account row"),
        (_UNVERIFIED_ROW, "claude_account_unverified"),
        ({**_UNVERIFIED_ROW, "reason": None}, "status unknown"),
        (_account_row(None), "weekly or session left_pct unknown"),
        (_account_row(89.0, session_left=None), "weekly or session left_pct unknown"),
        (_account_row(True), "weekly or session left_pct unknown"),
        (_account_row(101.0), "weekly or session left_pct unknown"),
        (_account_row(float("nan")), "weekly or session left_pct unknown"),
    ],
)
def test_account_view_without_a_usable_meter_is_unknown(row, reason):
    lane = _default_claude_lane("healthy")

    view, unknown = claude_account_lane.lane_view(row, lane)

    assert unknown == reason
    assert view == {"status": "unknown", "freshness": "unavailable", "health": {"healthy": True}}


@pytest.mark.parametrize("status", [[], ["ok"], {}, {"ok": True}, 1, None])
def test_account_view_with_a_non_string_status_is_unknown(status):
    row = {**_account_row(89.0), "status": status}

    view, unknown = claude_account_lane.lane_view(row, {})

    assert unknown is not None
    assert view["status"] == "unknown" and view["freshness"] == "unavailable"


def test_account_view_of_a_stale_row_reads_stale_last_good():
    view, unknown = claude_account_lane.lane_view(_account_row(0.5, status="stale"), {})

    assert unknown is None
    assert view["freshness"] == view["codexbar"]["freshness"] == "stale_last_good"
    assert view["codexbar"]["stale"] is True


# --- #10619 round 2: reselection, unattributed rate limits, ordinary-dispatch evidence -----


def _unattributed_rate_limited_lane(tmp_path: Path) -> dict:
    """The lane row after two unattributed claude rate limits, as the producer publishes it.

    ``summarize_lane_runtime`` reads two records that carry no account label;
    the producer then marks a cool meter hot.
    """
    from scripts.agent_runtime.usage import summarize_lane_runtime

    now = datetime.now(UTC)
    records = [
        {
            "ts": (now - timedelta(seconds=age)).isoformat(),
            "agent": "claude",
            "entrypoint": "cli",
            "model": "claude-opus-5-5",
            "outcome": "rate_limited",
        }
        for age in (40, 10)
    ]
    usage = tmp_path / "usage"
    usage.mkdir()
    (usage / "usage_claude-cli_fixture.jsonl").write_text("".join(json.dumps(r) + "\n" for r in records))
    runtime = summarize_lane_runtime("claude", usage_dir=usage, now=now.timestamp())
    assert runtime["headroom_blocked"] is True
    lane = _default_claude_lane("healthy") | {"runtime": runtime, "status": "hot"}
    lane["interactive"] = {**lane["interactive"], "status": "hot"}
    return lane


def test_select_account_reads_only_a_non_default_label_and_keeps_the_payload(tmp_path):
    lane = _unattributed_rate_limited_lane(tmp_path)
    budget = _accounts_budget(lane, {"b": _account_row(89.0)})

    host_view, host_evidence = claude_account_lane.select_account(budget, account=HOST_ACCOUNT)
    assert host_evidence == {"label": "a", "meter": "agents.claude"}
    # #10770: the default account keeps its lane row and every shared fact; only b's meter is gone.
    # The view holds frozen copies and its binding entry (round 2), so "kept" is equality.
    assert host_view["agents"] == budget["agents"] and host_view["agents"]["claude"] == lane
    binding = host_view[claude_account_lane.BINDING_KEY]
    assert binding["label"] == "a" and binding["evidence"] == host_evidence
    assert {key: value for key, value in host_view.items() if key != claude_account_lane.BINDING_KEY} == {
        **budget,
        "claude_accounts": {},
    }
    flat = {"claude": "healthy"}
    assert claude_account_lane.select_account(flat, account=account("b")) == (flat, {"label": "b", "meter": None})

    selected, evidence = claude_account_lane.select_account(budget, account=account("b"))

    assert selected["agents"]["claude"]["remaining_pct"] == pytest.approx(89.0)
    # #10770 round 2: every other lane is the payload's own record, held as a deeply immutable copy.
    assert selected["agents"]["codex"] == budget["agents"]["codex"]
    with pytest.raises(TypeError, match="immutable"):
        selected["agents"]["codex"]["status"] = "hot"
    assert budget["agents"]["claude"] is lane  # the caller's payload is not modified
    assert evidence["unattributed_rate_limits"] == {
        key: lane["runtime"][key] for key in sorted(claude_account_lane.ACCOUNT_RATE_LIMIT_FIELDS)
    }
