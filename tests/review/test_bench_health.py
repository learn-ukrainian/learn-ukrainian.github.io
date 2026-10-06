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

# #9769: native Grok counts outside xAI at every risk; the runtime-attested
# Cursor fallback additionally excludes Moonshot authors.
NATIVE_GROK = "grok-4.7"
GROK = "grok-4.7-cursor-fallback"
DEFAULT_COUNTS = {
    "anthropic": ["openai_frontier", NATIVE_GROK, GROK],
    "google": ["openai_frontier", NATIVE_GROK, GROK, "claude-opus-5-5", "claude-sonnet-5-5"],
    "openai": [NATIVE_GROK, GROK, "claude-opus-5-5", "claude-sonnet-5-5"],
    "moonshot": ["openai_frontier", NATIVE_GROK, "claude-opus-5-5", "claude-sonnet-5-5"],
    "zhipu": ["openai_frontier", NATIVE_GROK, GROK, "claude-opus-5-5", "claude-sonnet-5-5"],
    "xai": ["openai_frontier", "claude-opus-5-5", "claude-sonnet-5-5"],
    "deepseek": ["openai_frontier", NATIVE_GROK, GROK, "claude-opus-5-5", "claude-sonnet-5-5"],
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
        assert not set(results[family]) & {"composer-2.5", "pool", "pool-xs"}
    # Both Grok transports now have critical_review suitability.
    critical = check_bench_health(routing_snapshot=snapshot, data_egress_policy="local_interactive", risk="critical")
    assert critical["anthropic"] == ["openai_frontier", NATIVE_GROK, GROK]
    assert len(critical["anthropic"]) >= bench_health.MIN_ELIGIBLE_SEATS
    automatic = resolve_reviewer(ResolverInputs(author_model="claude", data_egress_policy="local_interactive"))
    assert automatic.selected.name == "openai_frontier"
    assert "glm-5.3" not in {entry.name for entry in automatic.trace}


@pytest.mark.parametrize("risk", ["low", "medium", "high", "critical"])
@pytest.mark.parametrize("profile", ["code", "infra"])
def test_bench_exclusions_match_automatic_resolver(risk, profile, capsys):
    results, exclusions = bench_health._bench_inventory(
        {}, data_egress_policy="local_interactive", review_profile=profile, risk=risk
    )
    assert results == check_bench_health(routing_snapshot={}, review_profile=profile, risk=risk)
    assert main(["--risk", risk, "--profile", profile], routing_snapshot={}) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert "BENCH HEALTH PASS" in captured.out
    assert captured.out.count("[EXPECTED single seat]") == 0
    for family, seats in results.items():
        resolution = resolve_reviewer(
            ResolverInputs(
                author_model=family,
                author_family=family,
                review_profile=profile,
                risk=risk,
                data_egress_policy="local_interactive",
                routing_snapshot={},
            )
        )
        assert set(seats) == {entry.name for entry in resolution.trace if entry.status in {"selected", "eligible"}}
    if risk == "high":
        assert {family: results[family] for family in ("anthropic", "openai")} == {
            "anthropic": ["openai_frontier", NATIVE_GROK, GROK],
            "openai": [NATIVE_GROK, GROK, "claude-opus-5-5"],
        }
        for family in set(AUTHOR_FAMILIES) - {"anthropic", "openai"}:
            grok_seats = [] if family == "xai" else [NATIVE_GROK] if family == "moonshot" else [NATIVE_GROK, GROK]
            assert results[family] == ["openai_frontier", *grok_seats, "claude-opus-5-5"]
        # The resolver names the single eligibility rule, not a bench-local list.
        rule = "performed only by gpt-6.1-sol, claude-opus-5-5, grok-4.7"
        assert not {NATIVE_GROK, GROK}.intersection(exclusions["anthropic"])
        assert not {NATIVE_GROK, GROK}.intersection(exclusions["openai"])
        assert rule in exclusions["openai"]["claude-sonnet-5-5"]
        return
    if risk != "critical":
        return
    assert results["anthropic"] == ["openai_frontier", NATIVE_GROK, GROK]
    assert results["openai"] == [NATIVE_GROK, GROK, "claude-opus-5-5"]
    assert set(exclusions["anthropic"]) == set(REVIEW_CANDIDATES) - {"openai_frontier", NATIVE_GROK, GROK}
    assert exclusions["anthropic"]["glm-5.3"] == "retired→cursor"
    assert exclusions["anthropic"]["composer-2.5"] == "sealed endpoint 'cursor' is not pinned for model 'composer-2.5'"
    assert not {NATIVE_GROK, GROK}.intersection(exclusions["anthropic"])
    for name in ("pool", "pool-xs"):
        assert exclusions["anthropic"][name] == "ACP participant does not yet pin and attest the concrete Laguna model"


@pytest.mark.parametrize("risk", ["low", "medium", "high", "critical"])
@pytest.mark.parametrize("family", AUTHOR_FAMILIES)
@pytest.mark.parametrize("count", [0, 1])
def test_only_accepted_family_risk_single_seats_pass(risk, family, count, monkeypatch, capsys):
    seats = ["seat-one"] if count else []
    monkeypatch.setattr(
        bench_health,
        "_bench_inventory",
        lambda *args, **kwargs: (
            {name: seats if name == family else ["seat-one", "seat-two"] for name in AUTHOR_FAMILIES},
            {name: {} for name in AUTHOR_FAMILIES},
        ),
    )
    accepted = risk in {"high", "critical"} and family in {"anthropic", "openai"}
    expected_pass = accepted and count == 1
    assert main(["--risk", risk], routing_snapshot={}) == (0 if expected_pass else 1)
    captured = capsys.readouterr()
    if expected_pass:
        assert "[EXPECTED single seat]" in captured.out
        assert captured.err == ""
    else:
        assert "[EXPECTED single seat]" not in captured.out
        assert _findings(captured) == [
            {
                "type": "insufficient_bench_capacity",
                "author_family": family,
                "minimum": 1 if accepted else 2,
                "counted_seats": seats,
                "excluded_seats": {},
            }
        ]
        assert "BENCH HEALTH FAIL" in captured.err


@pytest.mark.parametrize("risk", ["low", "medium", "high", "critical"])
@pytest.mark.parametrize("snapshot", [{}, {"cursor": "healthy", "pool": "healthy"}])
def test_composer_and_pool_exclusions_are_resolver_gates(risk, snapshot):
    eligible, excluded = bench_health._bench_inventory(
        snapshot, data_egress_policy="local_interactive", review_profile="code", risk=risk
    )
    inputs = ResolverInputs(
        author_model="claude", risk=risk, routing_snapshot=snapshot, data_egress_policy="local_interactive"
    )
    resolution = resolve_reviewer(inputs)
    expected_reasons = {
        "composer-2.5": "sealed endpoint 'cursor' is not pinned for model 'composer-2.5'",
        "pool": "ACP participant does not yet pin and attest the concrete Laguna model",
        "pool-xs": "ACP participant does not yet pin and attest the concrete Laguna model",
    }
    for name, reason in expected_reasons.items():
        evaluation = evaluate_candidate(REVIEW_CANDIDATES[name], inputs)
        assert evaluation.status == "excluded"
        assert evaluation.reason == excluded["anthropic"][name] == reason
        if risk == "high":
            # High's ladder contains Sol, Opus and Grok; these seats are never attempted.
            assert name not in {entry.name for entry in resolution.trace}
        else:
            trace = next(entry for entry in resolution.trace if entry.name == name)
            assert trace.status == "excluded"
            assert trace.reason == reason
        assert name not in eligible["anthropic"]


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
    assert results["anthropic"] == ["openai_frontier", NATIVE_GROK, GROK]
    # Removing Sol and both Grok routes leaves zero seats; still list the retired route.
    assert (
        main(
            ["--risk", "critical"],
            routing_snapshot={"glm": "healthy", "codex": "unhealthy", "grok": "unhealthy", "cursor": "unhealthy"},
        )
        == 1
    )
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
    assert results["anthropic"] == [NATIVE_GROK, GROK]
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
    # Native Grok supplies the second Anthropic seat when Codex is unavailable.
    assert main([], routing_snapshot={route: status}) == (0 if route == "codex" else 1)
    for finding in _findings(capsys.readouterr()):
        for name in names:
            if REVIEW_CANDIDATES[name].family != finding["author_family"]:
                assert finding["excluded_seats"][name] == reason
    assert results["anthropic"] == (
        [NATIVE_GROK, GROK] if route == "codex" else ["openai_frontier", NATIVE_GROK, GROK]
    )
    # Check exclusion reasons even when Grok admission prevents a CLI shortfall.
    _, excluded = bench_health._bench_inventory(
        {route: status}, data_egress_policy="local_interactive", review_profile="code", risk="medium"
    )
    for family in AUTHOR_FAMILIES:
        for name in names:
            if REVIEW_CANDIDATES[name].family != family:
                assert excluded[family][name] == reason


def test_bench_health_preserves_critical_role_gate():
    results = check_bench_health(routing_snapshot={}, review_profile="infra", risk="critical")
    assert all("claude-sonnet-5-5" not in seats for seats in results.values())


@pytest.mark.parametrize("risk", ["high", "critical"])
@pytest.mark.parametrize("status", ["unhealthy", "near_cap"])
@pytest.mark.parametrize("route,family", [("codex", "anthropic"), ("claude", "openai")])
def test_accepted_single_seat_still_requires_available_reviewer(risk, status, route, family, capsys):
    # Disable both newly admitted Grok routes to keep exercising the zero-seat invariant.
    assert main(["--risk", risk], routing_snapshot={route: status, "grok": status, "cursor": status}) == 1
    captured = capsys.readouterr()
    finding = next(item for item in _findings(captured) if item["author_family"] == family)
    assert finding["minimum"] == 1
    assert finding["counted_seats"] == []
    assert "BENCH HEALTH FAIL: At least one author family is below its required reviewer minimum." in captured.err


def test_catalog_reserves_count_only_on_automatic_ladder():
    medium = check_bench_health(routing_snapshot={})
    critical = check_bench_health(routing_snapshot={}, risk="critical")
    assert "claude-fable-5-1" not in medium["openai"]
    # #9583: Fable is no reviewer at any risk.
    assert "claude-fable-5-1" not in critical["openai"]


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
    assert "BENCH HEALTH PASS: All author families meet their required reviewer minimum." in captured.out
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
    assert "Anthropic/OpenAI authors at high/critical risk" in help_text
    assert "Zero seats always fails" in help_text
