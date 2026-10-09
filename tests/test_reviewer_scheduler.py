"""#9740 F1/F5: the reviewer scheduler reads remaining allowance and freshness through the owner.

Missing staleness is unknown (not fresh), and missing in-flight or failure
counts stay unknown (not zero); unknown ranks after any observed value.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from scripts.fleet import credit_lane
from scripts.review import reviewer_scheduler as scheduler


def _candidate(name: str = "openai-frontier", route: str = "codex") -> SimpleNamespace:
    return SimpleNamespace(
        name=name, route=route, concrete_model="gpt-6.1-sol", health_keys=frozenset(), capacity_weight=1.0
    )


def _snapshot(record: dict, **top) -> dict:
    return {"agents": {"codex": record}, **top}


def _key(snapshot: dict, candidate: SimpleNamespace | None = None) -> tuple:
    return scheduler.selection_key(
        candidate or _candidate(), snapshot=snapshot, exact_head="a" * 40, policy_version="v1"
    )


def test_remaining_is_the_owner_tightest_window():
    """F1: windows 40/3/80 read 3 everywhere (the owner's reading), not the first alias."""
    record = {
        "remaining_pct": 40.0,
        "codexbar": {"weekly_remaining_pct": 40.0, "primary_remaining_pct": 3.0, "secondary_remaining_pct": 80.0},
    }
    metrics = scheduler.metrics_for(_candidate(), _snapshot(record, diagnostics={"stale": False}))
    assert metrics.quota_remaining_pct == credit_lane.plan_remaining_pct(record) == 3.0


def test_scheduling_only_observation_cannot_loosen_the_plan_window():
    record = {"remaining_pct": 20.0, "scheduler": {"quota_remaining_pct": 90.0}}
    assert scheduler.metrics_for(_candidate(), _snapshot(record)).quota_remaining_pct == 20.0
    record = {"remaining_pct": 20.0, "scheduler": {"quota_remaining_pct": 5.0}}
    assert scheduler.metrics_for(_candidate(), _snapshot(record)).quota_remaining_pct == 5.0


def test_boolean_and_burn_only_remaining_establish_nothing():
    assert scheduler.metrics_for(_candidate(), _snapshot({"remaining_pct": True})).quota_remaining_pct is None
    assert scheduler.metrics_for(_candidate(), _snapshot({"burn_pct_7d": 95.0})).quota_remaining_pct is None


@pytest.mark.parametrize(
    ("record", "diagnostics", "expected"),
    [
        ({"remaining_pct": 5.0}, None, None),
        ({"remaining_pct": 5.0}, {}, None),
        ({"remaining_pct": 5.0}, {"stale": False}, True),
        ({"remaining_pct": 5.0}, {"stale": True}, False),
        ({"remaining_pct": 5.0, "freshness": "stale_last_good"}, {"stale": False}, False),
        ({"remaining_pct": 5.0, "scheduler": {"quota_stale": False}}, {"stale": True}, True),
    ],
    ids=["no-diagnostics", "staleness-missing", "fresh", "snapshot-stale", "probe-stale", "scheduler-wins"],
)
def test_missing_staleness_is_unknown_not_fresh(record, diagnostics, expected):
    """F5: the recon case ``{remaining_pct: 5}`` with no diagnostics is no longer fresh."""
    snapshot = _snapshot(record, **({"diagnostics": diagnostics} if diagnostics is not None else {}))
    assert scheduler.metrics_for(_candidate(), snapshot).quota_fresh is expected


def test_missing_in_flight_and_failures_stay_unknown():
    metrics = scheduler.metrics_for(_candidate(), _snapshot({"remaining_pct": 50.0}))
    assert (metrics.inflight, metrics.failures) == (None, None)


def test_observed_in_flight_map_without_the_route_is_an_established_zero():
    metrics = scheduler.metrics_for(
        _candidate(), _snapshot({"remaining_pct": 50.0, "runtime": {"error": 0}}, in_flight={"claude": 2})
    )
    assert (metrics.inflight, metrics.failures) == (0, 0)


def test_unknown_freshness_ranks_after_known_stale_and_fresh():
    fresh = _key(_snapshot({"remaining_pct": 10.0}, diagnostics={"stale": False}))
    stale = _key(_snapshot({"remaining_pct": 90.0}, diagnostics={"stale": True}))
    unknown = _key(_snapshot({"remaining_pct": 90.0}))
    headroom_unknown = _key(_snapshot({}, diagnostics={"stale": False}))
    assert fresh < stale < unknown < headroom_unknown


def test_unknown_load_counts_rank_after_observed_counts():
    observed = _key(
        _snapshot(
            {"remaining_pct": 50.0, "runtime": {"error": 3}}, in_flight={"codex": 4}, diagnostics={"stale": False}
        )
    )
    unknown = _key(_snapshot({"remaining_pct": 50.0}, diagnostics={"stale": False}))
    assert observed < unknown
