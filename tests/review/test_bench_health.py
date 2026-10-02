"""Tests for scripts/review/bench_health.py."""

from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scripts.review import bench_health
from scripts.review.bench_health import AUTHOR_FAMILIES, check_bench_health, main
from scripts.review.reviewer_resolver import (
    REVIEW_CANDIDATES,
    REVIEW_LADDERS,
    ResolverInputs,
    evaluate_candidate,
    resolve_reviewer,
)

# #9488: the runtime-attested Cursor Grok seat counts for every author family
# outside {xAI, Moonshot}; it closes the Anthropic shortfall below critical.
GROK = "grok-4.7-cursor-fallback"
DEFAULT_COUNTS = {
    "anthropic": ["openai_frontier", GROK],
    "google": ["openai_frontier", GROK, "claude-opus-5-5", "claude-sonnet-5-5"],
    "openai": [GROK, "claude-opus-5-5", "claude-sonnet-5-5"],
    "moonshot": ["openai_frontier", "claude-opus-5-5", "claude-sonnet-5-5"],
    "zhipu": ["openai_frontier", GROK, "claude-opus-5-5", "claude-sonnet-5-5"],
    "xai": ["openai_frontier", "claude-opus-5-5", "claude-sonnet-5-5"],
    "deepseek": ["openai_frontier", GROK, "claude-opus-5-5", "claude-sonnet-5-5"],
}


def _findings(captured):
    return [json.loads(line) for line in captured.err.splitlines() if line.startswith("{")]


def test_bench_health_default_snapshot_closes_the_anthropic_shortfall_below_critical():
    snapshot = {
        "agents": {
            name: {"status": "cool", "health": {"healthy": True}}
            for name in ("claude", "codex", "gemini", "grok", "glm", "cursor", "pool")
        }
    }
    results = check_bench_health(routing_snapshot=snapshot, data_egress_policy="local_interactive")
    assert results == DEFAULT_COUNTS
    for family in AUTHOR_FAMILIES:
        assert len(results[family]) >= 2, f"Family {family} has < 2 eligible seats: {results[family]}"
        assert all(REVIEW_CANDIDATES[name].family != family for name in results[family])
        assert not set(results[family]) & {"grok-4.7", "composer-2.5", "pool", "pool-xs"}
    # Grok has no critical_review role, so the critical Anthropic bench is still Sol alone.
    critical = check_bench_health(routing_snapshot=snapshot, data_egress_policy="local_interactive", risk="critical")
    assert critical["anthropic"] == ["openai_frontier"]
    assert len(critical["anthropic"]) < bench_health.MIN_ELIGIBLE_SEATS
    automatic = resolve_reviewer(ResolverInputs(author_model="claude", data_egress_policy="local_interactive"))
    assert automatic.selected.name == "openai_frontier"
    assert "glm-5.3" not in {entry.name for entry in automatic.trace}


@pytest.mark.parametrize("risk", ["medium", "high", "critical"])
def test_bench_exclusions_match_automatic_resolver(risk, capsys):
    results = check_bench_health(routing_snapshot={}, risk=risk)
    # #9488: only critical keeps the Anthropic shortfall.
    assert main(["--risk", risk], routing_snapshot={}) == (1 if risk == "critical" else 0)
    findings = _findings(capsys.readouterr())
    assert [finding["author_family"] for finding in findings] == (["anthropic"] if risk == "critical" else [])
    for family, seats in results.items():
        resolution = resolve_reviewer(
            ResolverInputs(
                author_model=family,
                author_family=family,
                risk=risk,
                data_egress_policy="local_interactive",
                routing_snapshot={},
            )
        )
        assert set(seats) == {entry.name for entry in resolution.trace if entry.status in {"selected", "eligible"}}
    if risk != "critical":
        return
    finding = findings[0]
    assert finding["type"] == "insufficient_bench_capacity"
    assert finding["minimum"] == 2
    assert finding["counted_seats"] == ["openai_frontier"]
    assert set(finding["excluded_seats"]) == set(REVIEW_CANDIDATES) - {"openai_frontier"}
    assert finding["excluded_seats"]["glm-5.3"] == "retired→cursor"
    assert (
        finding["excluded_seats"]["composer-2.5"] == "sealed endpoint 'cursor' is not pinned for model 'composer-2.5'"
    )
    assert (
        finding["excluded_seats"][GROK] == "missing required review role suitability: code/critical catalog suitability"
    )
    for name in ("pool", "pool-xs"):
        assert (
            finding["excluded_seats"][name] == "ACP participant does not yet pin and attest the concrete Laguna model"
        )


def test_retired_route_never_counts_even_if_pin_eligible_on_ladder(monkeypatch, capsys):
    # Deliberately put the pin-only seat on the ladder to isolate the route gate.
    monkeypatch.setitem(REVIEW_LADDERS, "medium", (*REVIEW_LADDERS["medium"], (REVIEW_CANDIDATES["glm-5.3"],)))
    pinned = evaluate_candidate(
        REVIEW_CANDIDATES["glm-5.3"],
        ResolverInputs(
            author_model="claude",
            pinned_candidate="glm-5.3",
            data_egress_policy="local_interactive",
            routing_snapshot={"glm": "healthy"},
        ),
    )
    assert pinned.status == "eligible"
    results = check_bench_health(routing_snapshot={"glm": "healthy"})
    assert all("glm-5.3" not in seats for seats in results.values())
    assert results["anthropic"] == ["openai_frontier", GROK]
    # Critical keeps the Anthropic shortfall (#9488), so its finding lists the exclusion.
    assert main(["--risk", "critical"], routing_snapshot={"glm": "healthy"}) == 1
    assert _findings(capsys.readouterr())[0]["excluded_seats"]["glm-5.3"] == "retired→cursor"


@pytest.mark.parametrize("policy", [None, "ci"])
def test_bench_health_preserves_egress_gate(policy, monkeypatch):
    # An automatic seat with an egress requirement must pass it too.
    monkeypatch.setitem(
        REVIEW_CANDIDATES,
        "openai_frontier",
        replace(
            REVIEW_CANDIDATES["openai_frontier"],
            requires_data_egress_policy="local_interactive",
        ),
    )
    results = check_bench_health(routing_snapshot={}, data_egress_policy=policy)
    assert all("glm-5.3" not in seats for seats in results.values())
    assert all("openai_frontier" not in seats for seats in results.values())
    assert results["anthropic"] == [GROK]
    pinned = evaluate_candidate(
        REVIEW_CANDIDATES["glm-5.3"],
        ResolverInputs(
            author_model="claude",
            pinned_candidate="glm-5.3",
            data_egress_policy=policy,
        ),
    )
    assert pinned.status == "excluded"
    assert "data-egress policy fail-closed" in pinned.reason


@pytest.mark.parametrize(
    "status,reason",
    [
        ("unhealthy", "lane health is unhealthy — route is operationally unavailable"),
        ("near_cap", "quota bucket is near cap — automatic assignments are prohibited"),
    ],
)
@pytest.mark.parametrize(
    "route,names",
    [
        ("codex", {"openai_frontier"}),
        ("claude", {"claude-opus-5-5", "claude-sonnet-5-5"}),
    ],
)
def test_bench_health_preserves_capacity_gate(status, reason, route, names, capsys):
    results = check_bench_health(routing_snapshot={route: status})
    assert all(not names.intersection(seats) for seats in results.values())
    assert main([], routing_snapshot={route: status}) == 1
    for finding in _findings(capsys.readouterr()):
        for name in names:
            if REVIEW_CANDIDATES[name].family != finding["author_family"]:
                assert finding["excluded_seats"][name] == reason
    assert results["anthropic"] == ([GROK] if route == "codex" else ["openai_frontier", GROK])


def test_bench_health_preserves_critical_role_gate():
    results = check_bench_health(routing_snapshot={}, review_profile="infra", risk="critical")
    assert all("claude-sonnet-5-5" not in seats for seats in results.values())


def test_catalog_reserves_count_only_on_automatic_ladder():
    medium = check_bench_health(routing_snapshot={})
    critical = check_bench_health(routing_snapshot={}, risk="critical")
    assert "claude-fable-5-1" not in medium["openai"]
    assert "claude-fable-5-1" in critical["openai"]


def test_bench_health_main_returns_zero_when_healthy(monkeypatch, capsys):
    """Exercise the success branch with a hypothetical adequate automatic bench."""
    monkeypatch.setattr(
        bench_health,
        "_bench_inventory",
        lambda *args, **kwargs: (
            {family: ["seat-one", "seat-two"] for family in AUTHOR_FAMILIES},
            {family: {} for family in AUTHOR_FAMILIES},
        ),
    )
    assert main([], routing_snapshot={}) == 0
    captured = capsys.readouterr()
    assert "BENCH HEALTH PASS" in captured.out
    assert captured.err == ""


def test_bench_health_main_returns_one_when_unhealthy(capsys):
    mock_snapshot = {
        "agents": {
            "claude": {"status": "unhealthy", "health": {"healthy": False}},
            "codex": {"status": "cool", "health": {"healthy": True}},
            "gemini": {"status": "unhealthy", "health": {"healthy": False}},
            "grok": {"status": "unhealthy", "health": {"healthy": False}},
            "glm": {"status": "unhealthy", "health": {"healthy": False}},
            "cursor": {"status": "unhealthy", "health": {"healthy": False}},
        }
    }
    assert main(["--data-egress-policy", "local_interactive"], routing_snapshot=mock_snapshot) == 1
    assert {finding["author_family"] for finding in _findings(capsys.readouterr())} == set(AUTHOR_FAMILIES)


def test_bench_health_help_documents_inventory_and_exit_codes(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    help_text = capsys.readouterr().out
    for text in ("automatic routing", "exclusion reasons", "Examples:", "Outputs:", "Exit codes:", "Related:"):
        assert text in help_text
