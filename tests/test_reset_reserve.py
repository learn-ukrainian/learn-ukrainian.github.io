"""Tests for the read-only shared operator Codex reset reserve."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from scripts.fleet import reset_reserve
from scripts.fleet.reset_reserve import (
    SCHEMA_VERSION,
    codex_is_threatened,
    codex_reset_reserve_eligible,
    effective_reset_reserve,
    load_reset_reserve,
    unavailable_reserve,
)

NOW = datetime(2026, 9, 23, 12, tzinfo=UTC)


@pytest.fixture(autouse=True)
def fresh_inventory(monkeypatch):
    monkeypatch.setattr(reset_reserve, "get_provider_usage_data", lambda _provider: _eligible_codex())


def _reserve() -> dict:
    return {"available": True, **{key: value for key, value in _assertion().items() if key != "schema_version"}}


def _write_assertion(root: Path, value: object) -> Path:
    path = root / "batch_state" / "routing_budget" / "operator_reset_reserve.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def _assertion(*, confirmed_at: str = "2026-09-23T10:00:00Z", expires_at: str = "2026-09-24T10:00:00Z") -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "provider": "codex",
        "remaining_resets": 2,
        "confirmed_at": confirmed_at,
        "expires_at": expires_at,
    }


def test_missing_and_malformed_assertions_fail_closed(tmp_path):
    assert load_reset_reserve(tmp_path, now=datetime(2026, 9, 23, 12, tzinfo=UTC)) == unavailable_reserve()
    assert unavailable_reserve()["remaining_resets"] is None
    path = _write_assertion(tmp_path, {**_assertion(), "operator": "private"})
    assert load_reset_reserve(tmp_path, now=datetime(2026, 9, 23, 12, tzinfo=UTC)) == unavailable_reserve()
    path.write_text("{broken", encoding="utf-8")
    assert load_reset_reserve(tmp_path, now=datetime(2026, 9, 23, 12, tzinfo=UTC)) == unavailable_reserve()


@pytest.mark.parametrize(
    "changes",
    [
        {"schema_version": "unknown"},
        {"provider": "claude"},
        {"remaining_resets": 0},
        {"remaining_resets": True},
        {"confirmed_at": "2026-09-23T10:00:00"},
        {"confirmed_at": "2026-09-23T13:00:00Z"},
        {"expires_at": "2026-09-23T12:00:00Z"},
        {"expires_at": "2026-09-23T10:00:00Z"},
    ],
)
def test_invalid_or_expired_assertions_fail_closed(tmp_path, changes):
    now = datetime(2026, 9, 23, 12, tzinfo=UTC)
    _write_assertion(tmp_path, {**_assertion(), **changes})
    assert load_reset_reserve(tmp_path, now=now) == unavailable_reserve()


def test_valid_assertion_is_sanitized_without_mutation(tmp_path):
    now = datetime(2026, 9, 23, 12, tzinfo=UTC)
    path = _write_assertion(tmp_path, _assertion())
    original = path.read_bytes()
    reserve = load_reset_reserve(tmp_path, now=now)
    assert reserve == {
        "available": True,
        "provider": "codex",
        "remaining_resets": 2,
        "confirmed_at": "2026-09-23T10:00:00Z",
        "expires_at": "2026-09-24T10:00:00Z",
    }
    assert path.read_bytes() == original


def test_assertion_is_shared_with_dispatch_worktree_and_expires_on_next_read(tmp_path):
    primary = tmp_path / "primary"
    worktree = primary / ".worktrees" / "dispatch" / "codex" / "task"
    git_worktree_dir = primary / ".git" / "worktrees" / "task"
    git_worktree_dir.mkdir(parents=True)
    worktree.mkdir(parents=True)
    (worktree / ".git").write_text(f"gitdir: {git_worktree_dir}\n", encoding="utf-8")
    _write_assertion(primary, _assertion())

    assert load_reset_reserve(worktree, now=datetime(2026, 9, 23, 12, tzinfo=UTC))["remaining_resets"] == 2
    assert load_reset_reserve(worktree, now=datetime(2026, 9, 24, 10, tzinfo=UTC)) == unavailable_reserve()


def test_old_assertion_survives_and_is_clamped_to_last_credit_expiry(tmp_path):
    assertion = _assertion(confirmed_at="2026-09-20T10:00:00Z", expires_at="2026-11-01T00:00:00Z")
    path = _write_assertion(tmp_path, assertion)
    original = path.read_bytes()
    reserve = load_reset_reserve(tmp_path, now=NOW)
    assert reserve["available"] is True
    assert reserve["remaining_resets"] == 2
    assert reserve["expires_at"] == "2026-10-29T00:00:00Z"
    assert codex_reset_reserve_eligible(reserve, _eligible_codex(), now=NOW)
    assert path.read_bytes() == original


@pytest.mark.parametrize("remaining,count,expected", [(1, 2, 1), (2, 1, 1), (3, 2, 2)])
def test_effective_count_is_bounded_by_assertion_and_inventory(tmp_path, monkeypatch, remaining, count, expected):
    info = _eligible_codex()
    info["reset_credits"]["available_count"] = count
    monkeypatch.setattr(reset_reserve, "get_provider_usage_data", lambda _provider: info)
    _write_assertion(tmp_path, {**_assertion(), "remaining_resets": remaining})
    assert load_reset_reserve(tmp_path, now=NOW)["remaining_resets"] == expected


@pytest.mark.parametrize(
    "inventory",
    [
        None,
        {},
        {"available_count": 0, "expires_at": [], "fetched_at": NOW.isoformat()},
        {"available_count": True, "expires_at": [None], "fetched_at": NOW.isoformat()},
        {"available_count": 1, "expires_at": "unknown", "fetched_at": NOW.isoformat()},
        {"available_count": 1, "expires_at": ["invalid"], "fetched_at": NOW.isoformat()},
        {"available_count": 1, "expires_at": ["2026-09-23T12:00:00Z"], "fetched_at": NOW.isoformat()},
        {"available_count": 1, "expires_at": ["2026-09-22T00:00:00Z"], "fetched_at": NOW.isoformat()},
        {"available_count": 1, "expires_at": [None]},
        {"available_count": 1, "expires_at": [None], "fetched_at": "2026-09-23T11:45:00Z"},
        {"available_count": 1, "expires_at": [None], "fetched_at": "2026-09-23T12:00:01Z"},
    ],
)
def test_unavailable_expired_or_stale_inventory_disables_reserve(tmp_path, monkeypatch, inventory):
    info = _eligible_codex()
    info["reset_credits"] = inventory
    monkeypatch.setattr(reset_reserve, "get_provider_usage_data", lambda _provider: info)
    _write_assertion(tmp_path, _assertion())
    assert load_reset_reserve(tmp_path, now=NOW) == unavailable_reserve()
    assert not codex_reset_reserve_eligible(_reserve(), info, now=NOW)


@pytest.mark.parametrize("changes", [{"freshness": "stale_last_good"}, {"age_s": 900}, {"age_s": float("nan")}])
def test_stale_provider_inventory_fails_closed_in_loader(tmp_path, monkeypatch, changes):
    info = {**_eligible_codex(), **changes}
    monkeypatch.setattr(reset_reserve, "get_provider_usage_data", lambda _provider: info)
    _write_assertion(tmp_path, _assertion())
    assert load_reset_reserve(tmp_path, now=NOW) == unavailable_reserve()


def test_unreadable_provider_inventory_fails_closed(tmp_path, monkeypatch):
    def unreadable(_provider):
        raise OSError("unreadable inventory")

    monkeypatch.setattr(reset_reserve, "get_provider_usage_data", unreadable)
    _write_assertion(tmp_path, _assertion())
    assert load_reset_reserve(tmp_path, now=NOW) == unavailable_reserve()


def test_old_assertion_lapses_at_own_expiry_with_fresh_live_credits(tmp_path):
    _write_assertion(tmp_path, _assertion(confirmed_at="2026-09-20T10:00:00Z", expires_at="2026-09-23T12:00:00Z"))
    info = _eligible_codex()
    before = datetime(2026, 9, 23, 11, 59, 59, tzinfo=UTC)
    info["reset_credits"]["fetched_at"] = before.isoformat()
    reserve = {**_reserve(), "confirmed_at": "2026-09-20T10:00:00Z", "expires_at": "2026-09-23T12:00:00Z"}
    assert codex_reset_reserve_eligible(reserve, info, now=before)
    assert load_reset_reserve(tmp_path, now=NOW) == unavailable_reserve()
    assert not codex_reset_reserve_eligible(reserve, info, now=NOW)


def test_partially_expired_inventory_reduces_count_and_nested_nonexpiring_credit_works():
    info = _eligible_codex()
    info["reset_credits"]["expires_at"][0] = "2026-09-22T00:00:00Z"
    reserve = effective_reset_reserve(_reserve(), info, now=NOW)
    assert reserve["remaining_resets"] == 1
    info["codexbar"]["reset_credits"] = {**info.pop("reset_credits"), "expires_at": [None]}
    bounded = effective_reset_reserve(_reserve(), info, now=NOW)
    assert bounded["available"] is True
    assert bounded["remaining_resets"] == 1
    assert bounded["expires_at"] == _reserve()["expires_at"]


def _eligible_codex() -> dict:
    return {
        "status": "hot",
        "eligible": True,
        "health": {"healthy": True},
        "freshness": "fresh",
        "age_s": 10,
        "reset_credits": {
            "available_count": 2,
            "expires_at": ["2026-10-22T00:00:00Z", "2026-10-29T00:00:00Z"],
            "fetched_at": NOW.isoformat(),
        },
        "codexbar": {
            "will_last_to_reset": False,
            "weekly_used_pct": 25.0,
            "windows": {"primary": {"remaining_pct": 12.0}},
        },
        "runtime": {
            "headroom_blocked": False,
            "rate_limited": 0,
            "last_rate_limited_at": None,
        },
    }


def test_threatened_uses_pace_deficit_not_a_bare_will_last_flag():
    on_pace = {
        "status": "warm",
        "codexbar": {
            "will_last_to_reset": False,
            "weekly_pace_delta_pct": 1.5,
            "weekly_expected_pct": 40.0,
            "weekly_used_pct": 41.5,
        },
    }
    early = {
        "status": "warm",
        "codexbar": {
            "will_last_to_reset": False,
            "weekly_pace_delta_pct": 0.49,
            "weekly_expected_pct": 0.52,
            "weekly_used_pct": 1.0,
        },
    }
    real_deficit = {
        "status": "warm",
        "codexbar": {
            "will_last_to_reset": False,
            "weekly_pace_delta_pct": 7.2,
            "weekly_expected_pct": 17.8,
            "weekly_used_pct": 25.0,
        },
    }
    assert codex_is_threatened(on_pace) is False
    assert codex_is_threatened(early) is False
    assert codex_is_threatened(real_deficit) is True
    assert codex_is_threatened({"status": "near_cap", "codexbar": {"will_last_to_reset": True}}) is True


def test_eligibility_requires_provider_runtime_and_health_headroom():
    reserve = _reserve()
    assert codex_reset_reserve_eligible(reserve, _eligible_codex(), now=NOW)
    for mutate in (
        lambda info: info["runtime"].update(headroom_blocked=True),
        lambda info: info["runtime"].update(rate_limited=1),
        lambda info: info["runtime"].update(summary_error="unavailable"),
        lambda info: info["health"].update(healthy=False),
        lambda info: info.update(eligible=False),
        lambda info: info.update(freshness="stale_last_good"),
        lambda info: info["codexbar"]["windows"]["primary"].update(remaining_pct=0),
        lambda info: info["codexbar"]["windows"].update(secondary={"remaining_pct": 0}),
        lambda info: info["codexbar"]["windows"].update(secondary={"used_pct": 100}),
        lambda info: info["codexbar"].update(weekly_used_pct=100, weekly_remaining_pct=None),
        lambda info: info["codexbar"].update(weekly_used_pct=None, weekly_remaining_pct=None),
        lambda info: info.update(
            notebook_report={
                "source": "notebook-report",
                "freshness": "fresh",
                "age_s": 5,
                "weekly_used_pct": 100,
                "weekly_remaining_pct": 0,
            }
        ),
        lambda info: info.update(
            notebook_report={
                "source": "notebook-report",
                "freshness": "stale_last_good",
                "age_s": 901,
                "weekly_used_pct": 20,
                "weekly_remaining_pct": 80,
            }
        ),
    ):
        info = _eligible_codex()
        mutate(info)
        assert not codex_reset_reserve_eligible(reserve, info, now=NOW)


def test_fresh_notebook_weekly_report_can_supply_missing_codexbar_weekly_window():
    info = _eligible_codex()
    info["codexbar"]["weekly_used_pct"] = None
    info["notebook_report"] = {
        "source": "notebook-report",
        "freshness": "fresh",
        "age_s": 5,
        "weekly_used_pct": 40,
        "weekly_remaining_pct": 60,
    }
    assert codex_reset_reserve_eligible(_reserve(), info, now=NOW)


def test_stale_routing_snapshot_cannot_use_reserve():
    assert not codex_reset_reserve_eligible(
        _reserve(),
        _eligible_codex(),
        snapshot_stale=True,
        now=NOW,
    )
