"""Tests for scripts/review/bench_health.py."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scripts.review.bench_health import AUTHOR_FAMILIES, check_bench_health, main


def test_bench_health_all_families_eligible_with_default_snapshot():
    """All 7 author families have >= 2 eligible seats in clean snapshot."""
    results = check_bench_health(
        routing_snapshot={
            "agents": {
                "claude": {"status": "cool", "health": {"healthy": True}},
                "codex": {"status": "cool", "health": {"healthy": True}},
                "gemini": {"status": "cool", "health": {"healthy": True}},
                "grok": {"status": "cool", "health": {"healthy": True}},
                "glm": {"status": "cool", "health": {"healthy": True}},
            }
        },
        data_egress_policy="local_interactive",
    )

    for family in AUTHOR_FAMILIES:
        assert len(results[family]) >= 2, f"Family {family} has < 2 eligible seats: {results[family]}"


def test_bench_health_main_returns_zero_when_healthy():
    """main() returns 0 when all families have >= 2 eligible seats."""
    mock_snapshot = {
        "agents": {
            "claude": {"status": "cool", "health": {"healthy": True}},
            "codex": {"status": "cool", "health": {"healthy": True}},
            "gemini": {"status": "cool", "health": {"healthy": True}},
            "grok": {"status": "cool", "health": {"healthy": True}},
            "glm": {"status": "cool", "health": {"healthy": True}},
        }
    }

    exit_code = main(["--data-egress-policy", "local_interactive"], routing_snapshot=mock_snapshot)
    assert exit_code == 0


def test_bench_health_main_returns_one_when_unhealthy():
    """main() returns 1 when any family has < 2 eligible seats."""
    mock_snapshot = {
        "agents": {
            "claude": {"status": "unhealthy", "health": {"healthy": False}},
            "codex": {"status": "cool", "health": {"healthy": True}},
            "gemini": {"status": "unhealthy", "health": {"healthy": False}},
            "grok": {"status": "unhealthy", "health": {"healthy": False}},
            "glm": {"status": "unhealthy", "health": {"healthy": False}},
        }
    }

    exit_code = main(["--data-egress-policy", "local_interactive"], routing_snapshot=mock_snapshot)
    assert exit_code == 1
