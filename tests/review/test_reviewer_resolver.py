"""Gemini's native low/medium formal-review boundary (#10073)."""

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

GEMINI = REVIEW_CANDIDATES["gemini-3.8-flash-high"]


def test_native_claude_headroom_hold_does_not_exclude_agy_claude_seat(monkeypatch):
    """A hold for one plan must not remove seats running on another quota."""
    import io
    import json

    from scripts.agent_runtime import model_pause

    monkeypatch.setattr(
        model_pause,
        "load_policy",
        lambda: {"headroom": [{"lane": "claude", "pattern": "claude-*", "max_weekly_used_pct": 80}]},
    )
    real_account = model_pause.account_used_pct
    monkeypatch.setattr(model_pause, "account_used_pct", lambda account: lambda lane: 90)
    native = REVIEW_CANDIDATES["claude-opus-5-5"]
    agy = REVIEW_CANDIDATES["claude-opus-5-5-agy"]
    gemini = REVIEW_CANDIDATES["gemini-3.8-flash-high"]
    inputs = ResolverInputs(author_model="gpt-6.1-sol", risk="low", claude_account=HOST_ACCOUNT)

    native_result = evaluate_candidate(native, inputs)
    assert native_result.status == "excluded"
    assert "MODEL_HEADROOM" in native_result.reason
    agy_result = evaluate_candidate(agy, inputs)
    assert agy_result.status == "eligible", agy_result.reason

    real_used = getattr(model_pause.routing_budget_used_pct, "__wrapped__", model_pause.routing_budget_used_pct)
    monkeypatch.setattr(model_pause, "routing_budget_used_pct", real_used)
    monkeypatch.setattr(model_pause, "account_used_pct", real_account)

    def serve(weekly, *, five_hour=1.0, stale=False):
        windows = {
            "five_hour": {"used_pct": five_hour, "remaining_pct": 100 - five_hour},
            "weekly": {"used_pct": weekly, "remaining_pct": 100 - weekly},
        }
        payload = {
            "agents": {
                "claude": {"status": "hot", "codexbar": {"stale": False, "freshness": "fresh", "weekly_used_pct": 90}},
                "gemini": {
                    "status": "hot",
                    "codexbar": {
                        "stale": stale,
                        "freshness": "stale_last_good" if stale else "fresh",
                        "weekly_used_pct": 22,
                        "claude_gpt_windows": windows,
                    },
                    "claude_gpt_windows": windows,
                },
            }
        }
        monkeypatch.setattr(model_pause.urllib.request, "urlopen", lambda *_a, **_k: io.StringIO(json.dumps(payload)))

    serve(100.0)
    exhausted = evaluate_candidate(agy, inputs)
    assert exhausted.status == "excluded"
    assert "MODEL_HEADROOM" in exhausted.reason
    assert evaluate_candidate(gemini, inputs).status == "eligible"
    serve(10.0, five_hour=100.0)
    five_hour = evaluate_candidate(agy, inputs)
    assert five_hour.status == "excluded" and "MODEL_HEADROOM" in five_hour.reason
    serve(10.0)
    assert evaluate_candidate(agy, inputs).status == "eligible"
    serve(10.0, stale=True)
    stale = evaluate_candidate(agy, inputs)
    assert stale.status == "excluded" and "MODEL_HEADROOM_USAGE_UNKNOWN" in stale.reason
    windows = {
        "five_hour": {"used_pct": 10, "remaining_pct": 90},
        "weekly": {"used_pct": float("nan"), "remaining_pct": 90},
    }
    payload = {
        "agents": {
            "claude": {"status": "hot", "codexbar": {"stale": False, "freshness": "fresh", "weekly_used_pct": 90}},
            "gemini": {
                "status": "hot",
                "codexbar": {
                    "stale": False,
                    "freshness": "fresh",
                    "weekly_used_pct": 22,
                    "claude_gpt_windows": windows,
                },
                "claude_gpt_windows": windows,
            },
        }
    }
    monkeypatch.setattr(model_pause.urllib.request, "urlopen", lambda *_a, **_k: io.StringIO(json.dumps(payload)))
    malformed = evaluate_candidate(agy, inputs)
    assert malformed.status == "excluded" and "MODEL_HEADROOM_USAGE_UNKNOWN" in malformed.reason


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


@pytest.mark.parametrize("profile", ["code", "infra"])
@pytest.mark.parametrize("risk", ["low", "medium", "high", "critical"])
@pytest.mark.parametrize("entrypoint", ["evaluate", "pin", "ladder"])
def test_gemini_risk_boundary(profile, risk, entrypoint):
    inputs = ResolverInputs(author_model="gpt-6.1-sol", review_profile=profile, risk=risk, claude_account=HOST_ACCOUNT)
    if entrypoint == "evaluate":
        eligible = evaluate_candidate(GEMINI, inputs).status == "eligible"
    else:
        if entrypoint == "pin":
            inputs = replace(inputs, pinned_candidate=GEMINI.name, pressure_override_reason="boundary test")
        eligible = resolve_reviewer(inputs, ladder=((GEMINI,),)).selected is not None
    assert eligible == (profile == "code" and risk in {"low", "medium"})


@pytest.mark.parametrize("risk", ["low", "medium"])
@pytest.mark.parametrize("scope", ["changed_paths", "owned_paths"])
@pytest.mark.parametrize(
    "path", ["scripts/review/reviewer_resolver.py", "scripts/agent_runtime/adapters/agy.py", ".github/workflows/ci.yml"]
)
def test_gemini_security_paths_override_declared_risk(risk, scope, path):
    inputs = ResolverInputs(author_model="gpt-6.1-sol", risk=risk, **{scope: (path,)}, claude_account=HOST_ACCOUNT)
    result = evaluate_candidate(GEMINI, inputs)
    assert result.status == "excluded"
    assert "security-sensitive" in result.reason
    assert resolve_reviewer(inputs, ladder=((GEMINI,),)).selected is None


@pytest.mark.parametrize("formal", [True, False])
def test_custom_roles_cannot_grant_gemini_high_risk(formal):
    forged = replace(GEMINI, model_roles=frozenset({"critical_review", "standard_review"}))
    assert (
        evaluate_candidate(
            forged, ResolverInputs(author_model="gpt-6.1-sol", risk="critical", formal_review=formal, claude_account=HOST_ACCOUNT)
        ).status
        == "excluded"
    )


def test_gemini_independence_and_unhealthy_route():
    same = evaluate_candidate(GEMINI, ResolverInputs(author_model="gemini-3.8-flash-high", risk="low", claude_account=HOST_ACCOUNT))
    assert same.status == "excluded"
    assert "same family" in same.reason
    unhealthy = evaluate_candidate(
        GEMINI, ResolverInputs(author_model="gpt-6.1-sol", risk="low", routing_snapshot={"agy": "unhealthy"}, claude_account=HOST_ACCOUNT)
    )
    assert unhealthy.status == "excluded"


@pytest.mark.parametrize("risk", ["low", "medium", "high", "critical"])
def test_automatic_ladder_uses_qualified_agy_model_when_other_routes_unavailable(risk):
    snapshot = {route: "unhealthy" for route in {candidate.route for candidate in REVIEW_CANDIDATES.values()}}
    snapshot["agy"] = "healthy"
    result = resolve_reviewer(ResolverInputs(author_model="gpt-6.1-sol", risk=risk, routing_snapshot=snapshot, claude_account=HOST_ACCOUNT))
    assert result.selected.name == (
        "claude-sonnet-5-5-agy" if risk in {"low", "medium"} else "claude-opus-5-5-agy"
    )


@pytest.mark.parametrize("risk", ["low", "medium"])
def test_near_cap_sol_precedes_agy_and_grok_for_claude_author(risk):
    result = resolve_reviewer(
        ResolverInputs(
            author_model="claude-opus-5-5",
            risk=risk,
            routing_snapshot={
                "agents": {
                    **{
                        route: {"status": "near_cap", "remaining_pct": 5, "health": {"healthy": True}}
                        for route in ("claude", "codex")
                    },
                    "muse": {"status": "unhealthy", "health": {"healthy": False}},
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
    "field,value",
    [
        ("participant", "codex"),
        ("catalog_transport", "native_codex"),
        ("sealed_executable", "other.py"),
        ("adapter_transport", "acp"),
    ],
)
def test_native_endpoint_identity_cannot_be_forged(field, value):
    forged = replace(GEMINI, **{field: value})
    result = evaluate_candidate(forged, ResolverInputs(author_model="gpt-6.1-sol", risk="low", claude_account=HOST_ACCOUNT))
    assert result.status == "excluded"
    assert "endpoint identity" in result.reason


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
            routing_snapshot={"claude": "unhealthy", "agy": "unhealthy", "grok": "unhealthy", "cursor": "unhealthy"}, claude_account=HOST_ACCOUNT,
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
FRONTIER_DOWN = {"codex": "unhealthy", "claude": "unhealthy", "agy": "unhealthy"}


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


@pytest.mark.parametrize("stage", ["resolver", "dispatcher", "spawn", "recorder", "generic"])
@pytest.mark.parametrize("case", [
    "admitted", "at_expiry", "after_expiry", "cross_family", "infra", "ukrainian",
    "different_author", "same_model", "wrong_transport", "advice", "security", "high_risk",
])
def test_astra_exception_role_or_expiry_escape(monkeypatch, tmp_path, stage, case):
    """The operator exception never admits Astra outside its seat or at/after expiry."""
    from datetime import UTC, datetime, timedelta

    from scripts.dispatcher import checks
    from scripts.dispatcher.providers import codex
    from scripts.dispatcher.types import TaskSpec
    from scripts.review import model_catalog, record_cf_verdict

    expiry = datetime(2026, 11, 4, tzinfo=UTC)
    clock = expiry if case == "at_expiry" else expiry + timedelta(seconds=1) if case == "after_expiry" else expiry - timedelta(microseconds=1)

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return clock

    monkeypatch.setattr(model_catalog, "datetime", Clock)
    # Loading the catalog after expiry must preserve every other route.
    model_catalog.validate_catalog(model_catalog.load_model_catalog())
    candidate = REVIEW_CANDIDATES["openai_red_team_exception"]
    options = dict(review_mode="red_team", review_profile="code", review_author_model="gpt-6.1-sol",
                   risk="medium", branch="codex/author", pinned_head="a" * 40, pr=42,
                   require_review_verdict=True)
    agent = "codex"
    if case == "cross_family":
        options["review_mode"] = "cross_family"
    elif case in {"infra", "ukrainian"}:
        options["review_profile"] = case
    elif case in {"different_author", "same_model"}:
        options["review_author_model"] = "claude-opus-5-5" if case == "different_author" else "gpt-6-astra"
    elif case == "wrong_transport":
        agent = "cursor"
    elif case == "advice":
        options["requested_role"] = "consequential_advisory"
    elif case in {"security", "high_risk"}:
        options["risk"] = "critical" if case == "security" else "high"
    allowed = case == "admitted"
    if stage == "resolver":
        inputs = ResolverInputs(author_model=options["review_author_model"], review_profile=options["review_profile"],
                                risk=options["risk"], requested_role=options.get("requested_role"), claude_account=HOST_ACCOUNT)
        candidate = replace(candidate, transport="cursor") if agent != "codex" else candidate
        assert (evaluate_candidate(candidate, inputs, review_mode=options["review_mode"]).status == "eligible") == allowed
        selected = resolve_reviewer(inputs, ladder=((candidate,),), review_mode=options["review_mode"]).selected
        assert (selected is not None) == allowed
        if allowed:
            # An available outside-family reviewer always outranks the exception.
            outside = REVIEW_CANDIDATES["claude-opus-5-5"]
            resolution = resolve_reviewer(inputs, ladder=((candidate,), (outside,)), review_mode="red_team")
            assert resolution.selected.concrete_model == "claude-opus-5-5"
            assert evaluate_candidate(candidate, replace(inputs, formal_review=False), review_mode="red_team").status == "excluded"
            assert evaluate_candidate(candidate, replace(inputs, author_models=("gpt-6-astra",)), review_mode="red_team").status == "excluded"
    elif stage in {"dispatcher", "spawn"}:
        prompt = tmp_path / "red-team.md"
        prompt.write_text("Toolful red-team code review of this exact head.")
        if stage == "dispatcher":
            def call():
                return checks.check_model_admission(agent, "gpt-6-astra", "read-only", options, prompt.read_bytes())
        else:
            spec = TaskSpec("reviewer", agent, "gpt-6-astra", "high", "read-only", tmp_path,
                            prompt, tmp_path / "result", options={key: str(value) for key, value in options.items()})
            def call():
                return codex.build(spec, {})
        if allowed:
            call()
            with pytest.raises(ValueError):
                if stage == "dispatcher":
                    checks.check_model_admission(agent, "gpt-6-astra", "workspace-write", options, prompt.read_bytes())
                else:
                    codex.build(replace(spec, mode="workspace-write"), {})
        else:
            with pytest.raises(ValueError):
                call()
    elif stage == "recorder":
        task = dict(agent=agent, model="gpt-6-astra", **options)
        # Final qualification independently enforces risk and requested-role gates.
        if case in {"advice", "security", "high_risk"}:
            facts = record_cf_verdict.BranchReviewFacts(
                repository="example/repo", base_tip_sha="b" * 40, head_sha="a" * 40,
                merge_base_sha="b" * 40, commits=(), existing_families=frozenset({"openai"}),
                incoming_writer=None, incoming_family=None, changed_paths=(), owned_paths=(),
                subject_seats=frozenset(), subject_families=frozenset(), subject_evidence=(),
            )
            task["review_risk"] = options["risk"]
            if case == "advice":
                # A context-free advice activity stays refused even when review flags are supplied.
                assert model_catalog.activity_role_refusal("gpt-6-astra", "consult")
            else:
                with pytest.raises(record_cf_verdict.RecordError):
                    record_cf_verdict._require_qualified_reviewer(facts, task=task, model="gpt-6-astra", family="openai", review_mode="red_team")
        elif allowed:
            assert record_cf_verdict.reviewer_identity(task) == ("gpt-6-astra", "openai")
        else:
            with pytest.raises(record_cf_verdict.RecordError):
                record_cf_verdict.reviewer_identity(task)
    else:
        assert model_catalog.retired_model_refusal("gpt-6-astra")
        assert model_catalog.activity_role_refusal("gpt-6-astra", "review")
        assert model_catalog.activity_role_refusal("gpt-6-astra", "consult")
        with pytest.raises(model_catalog.ModelCatalogError):
            model_catalog.require_execution_model("gpt-6-astra", transport="native_codex")
