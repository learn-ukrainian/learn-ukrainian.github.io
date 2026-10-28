"""Reviewer resolver: task identity, red-team seats and the D-129 seat rules; no AGY review seat (C-2970)."""

from dataclasses import replace

import pytest

from scripts.review.family_exclusions import family_exclusion
from scripts.review.reviewer_resolver import (
    REVIEW_CANDIDATES,
    ResolverInputs,
    evaluate_candidate,
    normalize_review_task_id,
    red_team_seat_refusal,
    resolve_reviewer,
    review_task_id_comparison_keys,
)
from tests.claude_route_accounts import HOST_ACCOUNT


@pytest.mark.parametrize(
    "task_id,expected",
    [
        ("author-one", "author-one"),
        ("AUTHOR-ONE", "author-one"),
        (" author-one ", "author-one"),
        ("CODEX/Author-One", "author-one"),
        ("codex-AUTHOR-ONE", "author-one"),
        ("codex/Author name!", "author-name"),
        ("...", "task"),
    ],
)
def test_review_task_identity_matches_trailer_suffix(task_id, expected):
    assert normalize_review_task_id(task_id, agent="codex") == expected


@pytest.mark.parametrize(
    "task_id,agent,expected",
    [
        ("claude-impl-x", "cursor", {"claude-impl-x", "impl-x"}),
        (" CODEX/Author-One ", "claude", {"codex-author-one", "author-one"}),
        ("cursor/Author name!", "cursor", {"cursor-author-name", "author-name"}),
        ("grok-hermes-author", "codex", {"grok-hermes-author", "hermes-author", "author"}),
        ("custom/author-one", "custom", {"custom-author-one", "author-one"}),
        ("codex/gpt-6.1-sol", "claude", {"codex-gpt-6.1-sol", "gpt-6.1-sol"}),
        ("other-task", "claude", {"other-task"}),
    ],
)
def test_review_task_comparison_keys_include_known_harnesses(task_id, agent, expected):
    assert review_task_id_comparison_keys(task_id, agent=agent) == expected


def test_different_task_comparison_keys_do_not_intersect():
    assert not review_task_id_comparison_keys("other-task", agent="claude") & review_task_id_comparison_keys(
        "codex/author-one", agent="codex"
    )


@pytest.mark.parametrize("risk", ["low", "medium", "high", "critical"])
def test_gemini_is_not_a_review_candidate(risk):
    """Dispatch refuses read-only AGY (C-2970), so no AGY seat can review: the ladder never offers one."""
    assert "gemini-3.8-flash-high" not in REVIEW_CANDIDATES
    assert not [name for name, candidate in REVIEW_CANDIDATES.items() if candidate.route == "agy"]
    snapshot = {route: "unhealthy" for route in {candidate.route for candidate in REVIEW_CANDIDATES.values()}}
    snapshot["agy"] = "healthy"
    result = resolve_reviewer(
        ResolverInputs(author_model="gpt-6.1-sol", risk=risk, routing_snapshot=snapshot, claude_account=HOST_ACCOUNT)
    )
    assert result.selected is None
    assert not [row.name for row in result.trace if row.route == "agy"]


@pytest.mark.parametrize("risk", ["low", "medium"])
def test_explicit_gemini_pin_fails_closed(risk):
    result = resolve_reviewer(
        ResolverInputs(
            author_model="gpt-6.1-sol",
            risk=risk,
            pinned_candidate="gemini-3.8-flash-high",
            pressure_override_reason="C-2970 boundary test",
            claude_account=HOST_ACCOUNT,
        )
    )
    assert result.selected is None
    assert result.fail_closed_reason == "unknown explicit reviewer pin 'gemini-3.8-flash-high'"


@pytest.mark.parametrize("risk", ["low", "medium"])
def test_near_cap_sol_precedes_agy_and_grok_for_claude_author(risk):
    result = resolve_reviewer(
        ResolverInputs(
            author_model="claude-opus-5-5",
            risk=risk,
            routing_snapshot={
                "agents": {
                    route: {"status": "near_cap", "remaining_pct": 5, "health": {"healthy": True}}
                    for route in ("claude", "codex")
                },
                "diagnostics": {"stale": False},
            }, claude_account=HOST_ACCOUNT,
        )
    )
    assert result.selected.name == "openai_frontier"
    grok = next(row for row in result.trace if row.name == "grok-4.7-cursor-fallback")
    assert grok.status == "eligible"
    assert result.selected.suitability_rank < grok.suitability_rank


@pytest.mark.parametrize(
    "risk,eligible", [(None, False), ("low", True), ("medium", True), ("high", False), ("critical", False)]
)
def test_role_family_filter_uses_risk(risk, eligible):
    result = family_exclusion(family="google", route="agy", transport="agy", risk=risk)
    assert (result is None) == eligible


@pytest.mark.parametrize("outside_available", [True, False])
def test_red_team_prefers_outside_family_before_same_family(outside_available):
    sol = REVIEW_CANDIDATES["openai_frontier"]
    opus = REVIEW_CANDIDATES["claude-opus-5-5"]
    snapshot = {"claude": "healthy" if outside_available else "unhealthy"}
    result = resolve_reviewer(
        ResolverInputs(author_model="gpt-6-luna", risk="critical", routing_snapshot=snapshot, claude_account=HOST_ACCOUNT),
        ladder=((sol,), (opus,)),
        review_mode="red_team",
    )
    assert result.selected.name == (opus.name if outside_available else sol.name)
    assert result.review_mode == "red_team"
    assert result.limitation == "Separate non-author red-team review; this label does not attest cross-family review."


def test_red_team_pin_cannot_override_outside_family_preference():
    inputs = ResolverInputs(
        author_model="gpt-6.1-sol",
        risk="critical",
        pinned_candidate="openai_frontier",
        pressure_override_reason="adversarial fixture", claude_account=HOST_ACCOUNT,
    )
    result = resolve_reviewer(inputs, review_mode="red_team")
    assert result.selected is None
    assert "failed a hard eligibility gate" in result.fail_closed_reason


@pytest.mark.parametrize(
    "inputs",
    [
        ResolverInputs(author_model="unknown-author", risk="critical", claude_account=HOST_ACCOUNT),
        ResolverInputs(
            author_model="gpt-6.1-sol",
            risk="critical",
            subject_seats=frozenset({"codex"}),
            routing_snapshot={"claude": "unhealthy", "grok": "unhealthy", "cursor": "unhealthy"}, claude_account=HOST_ACCOUNT,
        ),
    ],
)
def test_red_team_keeps_identity_and_subject_gates(inputs):
    assert resolve_reviewer(inputs, review_mode="red_team").selected is None


@pytest.mark.parametrize(
    "reviewer,authors,explicit,expected",
    [
        ("gpt-6.1-sol", ("gpt-6.1-sol",), None, "RED_TEAM_REFUSED: reviewer model equals a branch author model"),
        (
            "cursor:gpt-6.1-sol-high",
            ("CODEX/gpt-6.1-sol[1m]",),
            None,
            "RED_TEAM_REFUSED: reviewer model equals a branch author model",
        ),
        (
            "claude-opus-5-5[1m]",
            ("claude-opus-5-5-high",),
            None,
            "RED_TEAM_REFUSED: reviewer model equals a branch author model",
        ),
        ("gpt-6-luna", ("gpt-6.1-sol",), None, None),
        ("gpt-6.1-sol", (), None, "RED_TEAM_REFUSED: no validated author model; supply --review-author-model"),
        (
            "gpt-6.1-sol",
            ("gpt-6-luna", None),
            None,
            None,
        ),
        ("gpt-6.1-sol", (None,), "gpt-6-luna", None),
        (
            "gpt-6.1-sol",
            ("gpt-6.1-sol",),
            "gpt-6-luna",
            "RED_TEAM_REFUSED: reviewer model equals a branch author model",
        ),
        (
            "gpt-6.1-sol",
            ("gpt-6-luna",),
            "gpt-6.1-sol",
            "RED_TEAM_REFUSED: reviewer model equals a branch author model",
        ),
        (
            "gpt-6.1-sol",
            ("gpt-6-luna",),
            "unlisted-model",
            "RED_TEAM_REFUSED: --review-author-model is not a catalog model; the flag only adds a comparison model",
        ),
    ],
)
def test_red_team_seat_rule_uses_canonical_models(reviewer, authors, explicit, expected):
    assert red_team_seat_refusal((reviewer,), author_models=authors, author_model=explicit) == expected


def test_red_team_evaluation_accepts_different_same_family_model():
    sol = REVIEW_CANDIDATES["openai_frontier"]
    result = evaluate_candidate(sol, ResolverInputs(author_model="gpt-6-luna", claude_account=HOST_ACCOUNT), review_mode="red_team")
    assert result.status == "eligible"


def test_red_team_evaluation_accepts_unknown_history_with_known_author():
    sol = REVIEW_CANDIDATES["openai_frontier"]
    result = evaluate_candidate(
        sol,
        ResolverInputs(author_model="", author_models=("gpt-6-luna", None), author_families=frozenset({"openai"}), claude_account=HOST_ACCOUNT),
        review_mode="red_team",
    )
    assert result.status == "eligible"


@pytest.mark.parametrize(
    "explicit,expected",
    [
        ("codex:gpt-6-luna-high", "eligible"),
        ("claude-opus-5-5", "excluded"),
    ],
)
def test_red_team_flag_conflict_with_validated_author_task(explicit, expected):
    result = evaluate_candidate(
        REVIEW_CANDIDATES["openai_frontier"],
        ResolverInputs(author_model=explicit, author_models=(None, "gpt-6-luna"), author_task_models=("gpt-6-luna",), claude_account=HOST_ACCOUNT),
        review_mode="red_team",
    )
    assert result.status == expected
    if expected == "excluded":
        assert (
            result.reason
            == "RED_TEAM_REFUSED: conflicting author identity; --review-author-model only adds a comparison model, never overwrites recorded task evidence"
        )


# --- D-129 (#10464): reviewer seats ------------------------------------------------------------

SONNET = REVIEW_CANDIDATES["claude-sonnet-5-5"]
RISKS = ("low", "medium", "high", "critical")
D129_AUTHORS = ("claude-opus-5-5", "gpt-6.1-sol", "grok-4.7", "claude-sonnet-5-5")
SECURITY_PATH = "scripts/review/reviewer_resolver.py"
FRONTIER_DOWN = {"codex": "unhealthy", "claude": "unhealthy"}


def claude_on_cursor(row):
    return row.family == "anthropic" and row.transport == "cursor"


def test_no_claude_review_candidate_runs_on_cursor():
    assert not [name for name, candidate in REVIEW_CANDIDATES.items() if claude_on_cursor(candidate)]
    grok_cursor = REVIEW_CANDIDATES["grok-4.7-cursor-fallback"]
    assert (grok_cursor.family, grok_cursor.transport) == ("xai", "cursor")


@pytest.mark.parametrize("author", D129_AUTHORS)
@pytest.mark.parametrize("risk", RISKS)
def test_no_ladder_or_trace_row_reviews_claude_through_cursor(author, risk):
    for snapshot in (None, FRONTIER_DOWN):
        result = resolve_reviewer(ResolverInputs(author_model=author, risk=risk, routing_snapshot=snapshot, claude_account=HOST_ACCOUNT))
        assert result.trace
        assert not [row.name for row in result.trace if claude_on_cursor(row)]
        assert result.selected is None or not claude_on_cursor(result.selected)


@pytest.mark.parametrize("risk", RISKS)
def test_explicit_claude_cursor_pin_stays_excluded(risk):
    result = resolve_reviewer(
        ResolverInputs(
            author_model="gpt-6.1-sol",
            risk=risk,
            pinned_candidate="claude-opus-5-5-cursor-fallback",
            pressure_override_reason="D-129 boundary test", claude_account=HOST_ACCOUNT,
        )
    )
    assert result.selected is None
    assert result.fail_closed_reason == "unknown explicit reviewer pin 'claude-opus-5-5-cursor-fallback'"


@pytest.mark.parametrize("author", ("claude-opus-5-5", "gpt-6.1-sol", "grok-4.7"))
@pytest.mark.parametrize("risk", RISKS)
def test_sonnet_reviews_routine_code_only(author, risk):
    result = resolve_reviewer(ResolverInputs(author_model=author, risk=risk, claude_account=HOST_ACCOUNT))
    names = [row.name for row in result.trace]
    assert (SONNET.name in names) == (risk in {"low", "medium"})
    if risk in {"high", "critical"}:
        assert result.selected is None or result.selected.name != SONNET.name
        assert evaluate_candidate(SONNET, ResolverInputs(author_model=author, risk=risk, claude_account=HOST_ACCOUNT)).status == "excluded"


@pytest.mark.parametrize("risk", ["low", "medium"])
@pytest.mark.parametrize("scope", ["changed_paths", "owned_paths"])
def test_security_path_at_routine_risk_resolves_critical_without_sonnet(risk, scope):
    routine = ResolverInputs(author_model="gpt-6.1-sol", risk=risk, claude_account=HOST_ACCOUNT)
    # Control: on its own ladder Sonnet reviews routine code.
    assert resolve_reviewer(routine, ladder=((SONNET,),)).selected.name == SONNET.name
    secure = replace(routine, **{scope: (SECURITY_PATH,)})
    assert resolve_reviewer(secure, ladder=((SONNET,),)).selected is None
    result = resolve_reviewer(secure)
    assert result.resolved_risk == "critical"
    assert SONNET.name not in [row.name for row in result.trace]
    assert result.selected.name != SONNET.name


@pytest.mark.parametrize("author", ("claude-opus-5-5", "gpt-6.1-sol", "claude-sonnet-5-5"))
def test_critical_grok_is_eligible_but_frontier_authority_is_selected(author):
    healthy = {"codex": "healthy", "claude": "healthy", "grok": "healthy", "cursor": "healthy"}
    result = resolve_reviewer(ResolverInputs(author_model=author, risk="critical", routing_snapshot=healthy, claude_account=HOST_ACCOUNT))
    trace = {row.name: row for row in result.trace}
    assert trace["grok-4.7-cursor-fallback"].status == "eligible"
    assert result.selected.name == ("openai_frontier" if author.startswith("claude") else "claude-opus-5-5")
    assert result.selected.family != "xai"
    assert (result.selected.quality_tier, trace["grok-4.7-cursor-fallback"].quality_tier) == (
        "frontier_authority",
        "frontier_practical",
    )


def test_critical_grok_is_excluded_for_an_xai_author():
    result = resolve_reviewer(ResolverInputs(author_model="grok-4.7", risk="critical", claude_account=HOST_ACCOUNT))
    trace = {row.name: row for row in result.trace}
    assert "grok-4.7" not in trace
    assert trace["grok-4.7-cursor-fallback"].status == "excluded"
    assert result.selected.family != "xai"


def test_critical_cursor_grok_is_selected_when_frontier_is_ineligible():
    cursor = resolve_reviewer(
        ResolverInputs(author_model="gpt-6.1-sol", risk="critical", routing_snapshot=FRONTIER_DOWN, claude_account=HOST_ACCOUNT)
    )
    assert cursor.selected.name == "grok-4.7-cursor-fallback"
    assert cursor.selected.invocation == REVIEW_CANDIDATES["grok-4.7-cursor-fallback"].invocation
    assert "--model grok-4.7-high" in cursor.selected.invocation
    assert "grok-4.7" not in {row.name for row in cursor.trace}
    assert {row.name: row.status for row in cursor.trace}["grok-4.7-cursor-fallback"] == "selected"
    fallback = resolve_reviewer(
        ResolverInputs(
            author_model="gpt-6.1-sol", risk="critical", routing_snapshot={**FRONTIER_DOWN, "grok": "unhealthy"}, claude_account=HOST_ACCOUNT
        )
    )
    assert fallback.selected.name == "grok-4.7-cursor-fallback"
