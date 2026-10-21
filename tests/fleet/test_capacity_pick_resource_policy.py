"""Cursor leads only with stronger resource evidence (#10263)."""

import pytest

from scripts.fleet.capacity_pick import build_pick_order


@pytest.mark.parametrize(
    ("cursor_remaining", "cursor_in_flight", "expected"),
    [
        (10.0, 3, ["codex", "claude", "cursor"]),
        (95.0, 3, ["codex", "cursor", "claude"]),
        (100.0, 3, ["cursor", "codex", "claude"]),
    ],
)
def test_cursor_priority_follows_headroom_and_load(cursor_remaining, cursor_in_flight, expected):
    rows = [
        {"lane": lane, "status": "cool", "remaining_pct": remaining, "in_flight": in_flight}
        for lane, remaining, in_flight in (
            ("cursor", cursor_remaining, cursor_in_flight),
            ("codex", 90.0, 0),
            ("claude", 80.0, 0),
        )
    ]

    assert [row["lane"] for row in build_pick_order(rows)] == expected


@pytest.mark.parametrize(
    ("headroom", "expected"),
    [
        ({"cursor": 95.0, "codex": 95.0, "claude": 95.0}, ["codex", "claude", "cursor"]),
        ({"cursor": 91.0, "codex": 99.0}, ["codex", "cursor"]),
        ({"cursor": None, "codex": None, "claude": None}, ["codex", "claude", "cursor"]),
    ],
    ids=["equal-band-and-load", "same-band-higher-codex", "missing-headroom"],
)
def test_cursor_does_not_lead_without_stronger_evidence(headroom, expected):
    rows = [
        {"lane": lane, "status": "cool", "remaining_pct": remaining, "in_flight": 0}
        for lane, remaining in headroom.items()
    ]
    assert [row["lane"] for row in build_pick_order(rows)] == expected
