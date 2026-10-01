"""Tests for scripts/review/bench_health.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scripts.review.bench_health import AUTHOR_FAMILIES, check_bench_health, main
from scripts.review.reviewer_resolver import REVIEW_CANDIDATES, ResolverInputs, resolve_reviewer


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
        assert all(REVIEW_CANDIDATES[name].family != family for name in results[family])
        assert not set(results[family]) & {"grok-4.7", "grok-4.7-cursor-fallback", "composer-2.5", "pool", "pool-xs"}

    assert results["anthropic"] == ["openai_frontier", "glm-5.3"]
    # The bench's explicit-pin reserve is not promoted into automatic routing.
    automatic = resolve_reviewer(ResolverInputs(author_model="claude", data_egress_policy="local_interactive"))
    assert automatic.selected.name == "openai_frontier"
    assert "glm-5.3" not in {entry.name for entry in automatic.trace}


@pytest.mark.parametrize("policy", [None, "ci"])
def test_bench_health_pin_reserve_preserves_egress_gate(policy):
    results = check_bench_health(routing_snapshot={}, data_egress_policy=policy)
    assert all("glm-5.3" not in seats for seats in results.values())
    assert results["anthropic"] == ["openai_frontier"]


@pytest.mark.parametrize("status", ["unhealthy", "near_cap"])
def test_bench_health_pin_reserve_preserves_capacity_gate(status):
    results = check_bench_health(routing_snapshot={"glm": status})
    assert all("glm-5.3" not in seats for seats in results.values())
    assert results["anthropic"] == ["openai_frontier"]


def test_bench_health_preserves_critical_role_gate():
    results = check_bench_health(routing_snapshot={}, review_profile="infra", risk="critical")
    assert all("claude-sonnet-5-5" not in seats for seats in results.values())


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


def test_bench_health_help_documents_inventory_and_exit_codes(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    help_text = capsys.readouterr().out
    for text in ("explicit-pin reserves", "automatic routing", "Examples:", "Outputs:", "Exit codes:", "Related:"):
        assert text in help_text
