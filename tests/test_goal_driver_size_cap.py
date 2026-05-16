"""Tests for the /goal M-cap auto-sizing formula."""

from __future__ import annotations

import io

import pytest

from scripts.goal_driver.size_cap import (
    DYNAMIC_SENTINEL,
    M_CEILING,
    M_FLOOR,
    compute_m,
    format_m,
    main,
)


def test_small_queue_clamps_to_floor() -> None:
    # 3*2 + 5 = 11, below the floor of 15 — clamp up.
    assert compute_m(queue_depth=3) == M_FLOOR


def test_medium_queue_returns_formula_value() -> None:
    # 8*2 + 5 + 2 = 23
    assert compute_m(queue_depth=8, async_waits=2) == 23


def test_huge_queue_clamps_to_ceiling() -> None:
    assert compute_m(queue_depth=500) == M_CEILING


def test_dynamic_returns_none() -> None:
    assert compute_m(queue_depth=0, dynamic=True) is None
    assert compute_m(queue_depth=42, dynamic=True) is None


def test_format_m_renders_infinity_sentinel() -> None:
    assert format_m(None) == DYNAMIC_SENTINEL
    assert format_m(30) == "30"


@pytest.mark.parametrize(
    "queue,async_waits,expected",
    [
        (1, 0, 15),
        (5, 0, 15),
        (10, 0, 25),
        (20, 0, 45),
        (10, 5, 30),
    ],
)
def test_formula_known_points(queue: int, async_waits: int, expected: int) -> None:
    assert compute_m(queue_depth=queue, async_waits=async_waits) == expected


def test_negative_queue_depth_raises() -> None:
    with pytest.raises(ValueError, match="queue_depth"):
        compute_m(queue_depth=-1)


def test_negative_async_waits_raises() -> None:
    with pytest.raises(ValueError, match="async_waits"):
        compute_m(queue_depth=5, async_waits=-2)


def test_cli_prints_value(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["--queue-depth", "8", "--async-waits", "2"])
    assert rc == 0
    out = capsys.readouterr().out.strip()
    assert out == "23"


def test_cli_dynamic_prints_sentinel(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["--dynamic"])
    assert rc == 0
    assert capsys.readouterr().out.strip() == DYNAMIC_SENTINEL


def test_cli_rejects_negative_input(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["--queue-depth", "-5"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "queue_depth" in err


def test_format_m_uses_stdin_marker_safely() -> None:
    # Round-trip: a value the agent might paste into a status line.
    rendered = format_m(compute_m(queue_depth=12, async_waits=1))
    assert rendered == "30"  # 12*2 + 5 + 1 = 30
    # And ensure no surprises from io abstractions.
    assert io.StringIO(rendered).read() == "30"
