"""#9272: review routes retain an eligible identity and bare head pins refuse before effects."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import delegate
from scripts.agent_runtime.target_admission import ReviewAdmissionRefused, resolve_and_admit
from scripts.review import reviewer_resolver


def _args(*extra):
    return delegate.build_parser().parse_args(
        [
            "dispatch",
            "--agent",
            "codex",
            "--model",
            "gpt-6.1-sol",
            "--task-id",
            "review-9272",
            "--mode",
            "read-only",
            "--require-review-verdict",
            "--prompt",
            "Review the branch.",
            *extra,
        ]
    )


def _budget(*, claude="cool", codex="near_cap", cursor="cool"):
    return {
        "agents": {"claude": {"status": claude}, "codex": {"status": codex}, "cursor": {"status": cursor}},
        "diagnostics": {"records_loaded": 5, "stale": False},
    }


def _admit(args, monkeypatch, budget=None):
    monkeypatch.setattr(delegate, "_fetch_routing_budget", lambda: budget or _budget())
    monkeypatch.setattr(delegate, "_load_reset_reserve", lambda *_a, **_k: {})
    routing = delegate._DispatchRouting()
    result = delegate._admit_dispatch_target(
        args,
        agent=args.agent,
        trees=None,
        route=delegate._dispatch_route(
            args, routing, language_lane=delegate._dispatch_is_language_lane(args), review_attempt=args.review_attempt
        ),
    )
    return result, routing


def test_9312_alias_explicit_model_uses_alias_resolved_identity(monkeypatch):
    args = _args("--agent", "gemini", "--model", "gemini-3.1-pro-high", "--review-profile", "ukrainian")
    (refusal, target), routing = _admit(args, monkeypatch)
    assert refusal is None
    assert (target.recipient, target.model) == ("agy", "gemini-3.8-flash-high")
    assert routing.substitution["source"] == "retired-cli"


def test_review_alias_model_is_resolved_once_before_selection(monkeypatch):
    calls = []
    real = delegate._resolve_substitution_model

    def capture(seat, model):
        calls.append((seat, model))
        return real(seat, model)

    monkeypatch.setattr(delegate, "_resolve_substitution_model", capture)
    args = _args("--agent", "gemini", "--model", "gemini-3.1-pro-high", "--review-profile", "ukrainian")
    (refusal, target), _ = _admit(args, monkeypatch)
    assert refusal is None and target.recipient == "agy"
    assert calls == [("agy", "gemini-3.1-pro-high")]


def test_9312_budget_substitute_is_checked_for_its_own_deficit(monkeypatch, capsys):
    budget = _budget(claude="near_cap", codex="cool")
    budget["agents"]["codex"]["codexbar"] = {
        "will_last_to_reset": False,
        "weekly_pace_delta_pct": 12.0,
        "weekly_expected_pct": 40.0,
    }
    args = _args(
        "--agent", "claude", "--model", "claude-opus-5-5", "--check-budget",
        "--review-author-model", "composer-2.5", "--review-risk", "critical",
    )
    (refusal, target), routing = _admit(args, monkeypatch, budget)
    assert refusal and "REVIEW_ROUTE_REFUSED" in refusal and "deficit" in refusal
    assert target is None and routing.substitution is None
    assert "HARD AUTO-SUBSTITUTE" not in capsys.readouterr().err


@pytest.mark.parametrize("subject", [
    ("--owned-path", "scripts/agent_runtime/adapters/codex.py"),
    ("--subject-seat", "codex"),
    ("--subject-family", "openai"),
])
def test_9312_budget_substitute_excludes_governed_seat(monkeypatch, subject):
    args = _args(
        "--agent", "claude", "--model", "claude-opus-5-5", "--check-budget",
        "--review-author-model", "composer-2.5", "--review-risk", "critical", *subject,
    )
    (refusal, target), routing = _admit(args, monkeypatch, _budget(claude="near_cap", codex="cool"))
    assert refusal and "REVIEW_ROUTE_REFUSED" in refusal
    assert target is None and routing.substitution is None


def test_requested_reviewer_is_also_subject_excluded_before_budget(monkeypatch):
    args = _args(
        "--owned-path", "scripts/agent_runtime/adapters/codex.py",
        "--review-author-model", "composer-2.5", "--review-risk", "critical",
    )
    (refusal, target), _ = _admit(args, monkeypatch)
    assert refusal is None and target.recipient == "claude"


@pytest.mark.parametrize("subject", [
    ("--owned-path", "scripts/agent_runtime/adapters/base.py"),
    ("--subject-seat", "unknown-seat"),
    ("--subject-family", "unknown-family"),
])
def test_review_subject_ambiguity_or_invalid_identity_refuses_before_budget(monkeypatch, subject):
    def fail():
        pytest.fail("invalid subject must refuse before budget probe")

    monkeypatch.setattr(delegate, "_fetch_routing_budget", fail)
    args = _args("--check-budget", *subject)
    refusal, target = delegate._admit_dispatch_target(
        args, agent=args.agent, trees=None,
        route=delegate._dispatch_route(args, delegate._DispatchRouting(), language_lane=False, review_attempt=None),
    )
    assert refusal and "REVIEW_ROUTE_REFUSED" in refusal and target is None


def test_9312_alias_without_model_records_only_the_alias(monkeypatch, capsys):
    args = _args("--agent", "gemini", "--review-profile", "ukrainian")
    args.model = None
    (refusal, target), routing = _admit(args, monkeypatch)
    assert refusal is None and target.recipient == "agy"
    assert "REVIEW_IDENTITY_SUBSTITUTED" not in capsys.readouterr().err
    assert routing.substitution["source"] == "retired-cli"
    assert routing.substitution["requested_model"] is None


def test_9312_ineligible_ukrainian_reviewer_has_no_code_substitution_hint():
    with pytest.raises(ReviewAdmissionRefused) as refused:
        resolve_and_admit(
            ("grok",), model="grok-4.7", mode="read-only", review_dispatch=True, review_profile="ukrainian"
        )
    assert "--review-profile ukrainian" in str(refused.value)
    assert "--review-author-model" not in str(refused.value)


def test_9312_merge_heading_is_followed_by_landing_policy():
    workflow = Path("agents_extensions/shared/rules/workflow.md").read_text(encoding="utf-8")
    merge = workflow.split("## Merge policy — ready PRs must not sit", 1)[1]
    assert merge.split("\n\n", 1)[1].startswith("The binding landing order")


@pytest.mark.parametrize(
    "inputs",
    [
        (),
        ("--review-author-model", "claude-opus-5-5"),
        ("--review-risk", "critical"),
        ("--review-profile", "ukrainian"),
    ],
)
def test_review_budget_without_both_trusted_inputs_keeps_requested_reviewer(monkeypatch, capsys, inputs):
    (refusal, target), routing = _admit(_args("--check-budget", *inputs), monkeypatch)
    assert refusal is None
    assert (target.recipient, target.model) == ("codex", "gpt-6.1-sol")
    assert routing.substitution is None
    assert "HARD AUTO-SUBSTITUTE" not in capsys.readouterr().err


@pytest.mark.parametrize("risk", ["low", "medium", "high", "critical"])
def test_review_budget_uses_exact_resolver_choice_and_author_identity(monkeypatch, risk):
    calls = []
    real = reviewer_resolver.resolve_reviewer

    def capture(inputs, **kwargs):
        result = real(inputs, **kwargs)
        calls.append((inputs, result))
        return result

    monkeypatch.setattr(reviewer_resolver, "resolve_reviewer", capture)
    args = _args("--check-budget", "--review-author-model", "claude-opus-5-5", "--review-risk", risk)
    (refusal, target), routing = _admit(args, monkeypatch, _budget(claude="near_cap"))
    assert refusal and target is None  # Author family is excluded; both remaining native seats are exhausted.
    assert routing.substitution is None
    assert calls and all(inputs.author_model == "claude-opus-5-5" and inputs.risk == risk for inputs, _ in calls)
    assert calls[-1][1].selected is None


def test_same_family_requested_reviewer_takes_resolvers_eligible_seat(monkeypatch):
    args = _args("--check-budget", "--review-author-model", "gpt-6.1-sol", "--review-risk", "critical")
    (refusal, target), routing = _admit(args, monkeypatch)
    assert refusal is None
    assert target.recipient == "claude"
    assert reviewer_resolver.resolve_family(target.model) == "anthropic"
    assert routing.substitution["actual_model"] == target.model
    assert routing.substitution["source"] == "reviewer-resolver"


@pytest.mark.parametrize(
    "risk,model", [("critical", "claude-opus-5-5"), ("medium", "claude-fable-5-1")]
)
@pytest.mark.parametrize("flags", [(), ("--check-budget",), ("--check-budget", "--force-agent")])
def test_trusted_eligible_off_ladder_reviewer_is_kept(monkeypatch, capsys, risk, model, flags):
    # #9301 puts Fable 5.1 on the critical ladder; Opus remains an eligible
    # explicit pin outside that ladder. Keep testing the off-ladder premise.
    args = _args(
        "--agent", "claude", "--model", model,
        "--review-author-model", "gpt-6.1-sol", "--review-risk", risk, *flags,
    )
    assert all(
        candidate.concrete_model != args.model
        for rung in reviewer_resolver.REVIEW_LADDERS[risk] for candidate in rung
    )
    (refusal, target), routing = _admit(args, monkeypatch)
    assert refusal is None
    assert (target.recipient, target.model) == ("claude", model)
    assert routing.substitution is None
    assert "SUBSTITUT" not in capsys.readouterr().err


def test_off_ladder_reviewer_is_substituted_when_budget_requires_it(monkeypatch, capsys):
    args = _args(
        "--agent", "claude", "--model", "claude-opus-5-5", "--check-budget",
        "--review-author-model", "composer-2.5", "--review-risk", "critical",
    )
    assert all(
        candidate.concrete_model != args.model
        for rung in reviewer_resolver.REVIEW_LADDERS[args.review_risk] for candidate in rung
    )
    (refusal, target), routing = _admit(args, monkeypatch, _budget(claude="near_cap", codex="cool"))
    assert refusal is None and (target.recipient, target.model) == ("codex", "gpt-6.1-sol")
    assert routing.substitution["actual_agent"] == "codex"
    assert "HARD AUTO-SUBSTITUTE: REVIEW_IDENTITY_SUBSTITUTED:" in capsys.readouterr().err


@pytest.mark.parametrize("flags", [(), ("--force-agent",)])
@pytest.mark.parametrize("seat,model", [("codex", "gpt-6.1-sol"), ("grok", "grok-4.7")])
def test_admission_identity_swap_always_prints_typed_note(monkeypatch, capsys, flags, seat, model):
    args = _args(
        "--agent", seat, "--model", model,
        "--review-author-model", "gpt-6.1-sol", "--review-risk", "critical", *flags,
    )
    (refusal, target), routing = _admit(args, monkeypatch)
    assert refusal is None and target.recipient == "claude"
    assert routing.substitution["actual_model"] == target.model
    assert "REVIEW_IDENTITY_SUBSTITUTED:" in capsys.readouterr().err


def test_gemini_alias_keeps_ukrainian_review_admission(monkeypatch, capsys):
    args = _args("--agent", "gemini", "--review-profile", "ukrainian")
    args.model = None
    (refusal, target), routing = _admit(args, monkeypatch)
    assert refusal is None
    assert (target.recipient, target.model) == ("agy", "gemini-3.8-flash-high")
    assert routing.substitution["actual_agent"] == "agy"
    assert "RETIRED CLI ALIAS:" in capsys.readouterr().err


@pytest.mark.parametrize(
    "flags", [("--review-author-model", "gpt-6.1-sol"), ("--review-risk", "medium"),
              ("--review-author-model", "gpt-6.1-sol", "--review-risk", "critical")],
)
def test_ukrainian_review_resolver_flags_refuse_with_code_only_guidance(monkeypatch, flags):
    (refusal, target), _ = _admit(_args("--review-profile", "ukrainian", *flags), monkeypatch)
    assert target is None
    assert "REVIEW_ROUTE_REFUSED:" in refusal and "code profile only" in refusal


def test_review_resolver_help_and_budget_notice_state_code_profile_only(monkeypatch, capsys):
    parser = delegate.build_parser()
    with pytest.raises(SystemExit) as exit_info:
        parser.parse_args(["dispatch", "--help"])
    assert exit_info.value.code == 0
    help_text = " ".join(capsys.readouterr().out.split())
    assert help_text.count("Code profile only") >= 2
    (refusal, target), _ = _admit(_args("--review-profile", "ukrainian", "--check-budget"), monkeypatch)
    assert refusal is None and target.recipient == "codex"
    assert "code profile only" in capsys.readouterr().err


def test_review_budget_success_matches_exact_in_process_resolver_result(monkeypatch, capsys):
    resolutions = []
    real = reviewer_resolver.resolve_reviewer

    def capture(inputs, **kwargs):
        result = real(inputs, **kwargs)
        resolutions.append(result)
        return result

    monkeypatch.setattr(reviewer_resolver, "resolve_reviewer", capture)
    args = _args("--check-budget", "--review-author-model", "composer-2.5", "--review-risk", "critical")
    (refusal, target), routing = _admit(args, monkeypatch)
    assert refusal is None
    selected = resolutions[-1].selected
    assert (target.recipient, target.model) == (selected.route, selected.concrete_model)
    assert target.recipient == "claude" and selected.quality_tier == "frontier_authority"
    assert routing.substitution["actual_model"] == selected.concrete_model
    output = capsys.readouterr().err
    assert "HARD AUTO-SUBSTITUTE" in output and "grok" not in output


def test_review_budget_substitute_pins_resolver_model(monkeypatch):
    args = _args(
        "--agent",
        "claude",
        "--model",
        "claude-sonnet-5-5",
        "--check-budget",
        "--review-author-model",
        "gpt-6.1-sol",
        "--review-risk",
        "critical",
    )
    (refusal, target), routing = _admit(args, monkeypatch)
    assert refusal is None and target.recipient == "claude"
    assert target.model != "claude-sonnet-5-5"  # Critical reviews require the authority seat.
    assert routing.substitution["actual_model"] == target.model


def test_review_cannot_reselect_a_newly_chosen_seat_in_budget_deficit(monkeypatch):
    budget = _budget()
    budget["agents"]["claude"]["codexbar"] = {
        "will_last_to_reset": False,
        "weekly_pace_delta_pct": 12.0,
        "weekly_expected_pct": 40.0,
    }
    args = _args("--check-budget", "--review-author-model", "gpt-6.1-sol", "--review-risk", "critical")
    (refusal, target), _ = _admit(args, monkeypatch, budget)
    assert "REVIEW_ROUTE_REFUSED" in refusal and target is None


def test_explicit_reviewer_context_window_keeps_its_model(monkeypatch):
    args = _args("--agent", "claude", "--model", "claude-opus-5-5[1m]")
    (refusal, target), routing = _admit(args, monkeypatch)
    assert refusal is None and target.model == "claude-opus-5-5[1m]"
    assert routing.substitution is None


@pytest.mark.parametrize(
    "seat,model",
    [("grok", "grok-4.7"), ("cursor", "grok-4.7"), ("agy", "gemini-3.8-flash-high"), ("kimi", "kimi-code/k3")],
)
def test_ineligible_review_refuses_before_budget_probe(monkeypatch, seat, model):
    def fail():
        pytest.fail("ineligible review must not probe budget")

    monkeypatch.setattr(delegate, "_fetch_routing_budget", fail)
    args = _args("--agent", seat, "--model", model, "--check-budget")
    routing = delegate._DispatchRouting()
    refusal, target = delegate._admit_dispatch_target(
        args,
        agent=seat,
        trees=None,
        route=delegate._dispatch_route(args, routing, language_lane=False, review_attempt=None),
    )
    assert refusal and target is None


@pytest.mark.parametrize("inputs", [(), ("--review-author-model", "claude-opus-5-5", "--review-risk", "critical")])
def test_review_attempt_refuses_budget_substitution_separately(monkeypatch, capsys, inputs):
    (refusal, target), routing = _admit(
        _args("--check-budget", "--review-attempt", "attempt.yaml", *inputs), monkeypatch
    )
    assert "REVIEW_ATTEMPT_IDENTITY_REFUSED" in refusal and target is None
    assert routing.substitution is None
    assert "HARD AUTO-SUBSTITUTE" not in capsys.readouterr().err



@pytest.mark.parametrize("fallbacks", [{}, {"codex": "codex"}])
def test_review_attempt_budget_refusal_without_substitute_names_seat_and_cause(monkeypatch, fallbacks):
    monkeypatch.setattr("scripts.common.fallback_substitutions.load_dispatch_fallbacks", lambda _path: fallbacks)
    (refusal, target), routing = _admit(
        _args("--check-budget", "--review-attempt", "attempt.yaml"), monkeypatch
    )
    assert target is None and routing.substitution is None
    assert refusal == (
        "REVIEW_ATTEMPT_IDENTITY_REFUSED: review attempt refused for codex: "
        "budget guard requires substitution; attempt identity is immutable (#8517)"
    )


def test_retired_review_attempt_refuses_before_route_and_budget_probe(monkeypatch):
    def fail(*_args, **_kwargs):
        pytest.fail("retired review attempt must refuse before routing or probing")

    monkeypatch.setattr(delegate, "_fetch_routing_budget", fail)
    with pytest.raises(ReviewAdmissionRefused) as refused:
        resolve_and_admit(
            ("gemini",), mode="read-only", review_dispatch=True, review_attempt=True, route=fail
        )
    assert str(refused.value) == (
        "REVIEW_ATTEMPT_IDENTITY_REFUSED: review attempt refused: "
        "agent substitution from gemini to agy (retired CLI) is not allowed (#8517)"
    )


def test_review_attempt_with_headroom_keeps_identity(monkeypatch):
    (refusal, target), _ = _admit(
        _args("--check-budget", "--review-attempt", "attempt.yaml"), monkeypatch, _budget(codex="cool")
    )
    assert refusal is None and (target.recipient, target.model) == ("codex", "gpt-6.1-sol")


def test_review_admission_refuses_a_route_ignoring_the_reviewer_selector():
    with pytest.raises(ReviewAdmissionRefused, match="REVIEW_ROUTE_REFUSED"):
        resolve_and_admit(
            ("codex",),
            mode="read-only",
            model="gpt-6.1-sol",
            review_dispatch=True,
            route=lambda request: ("cursor", "grok-4.7", "budget"),
        )


@pytest.mark.parametrize("flags", [(), ("--worktree",), ("--worktree", "--dry-run"), ("--check-budget",)])
def test_bare_pinned_head_refuses_before_probes_worktree_or_task_record(monkeypatch, tmp_path, capsys, flags):
    tasks = tmp_path / "tasks"
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))

    def fail(*_a, **_k):
        pytest.fail("bare pin reached a probe, task record, or worktree effect")

    for name in ("_fetch_routing_budget", "_ensure_worktree", "_write_state_atomic", "tasks_dir"):
        monkeypatch.setattr(delegate, name, fail)
    monkeypatch.setattr(delegate.subprocess, "run", fail)
    monkeypatch.setattr(delegate.subprocess, "Popen", fail)
    monkeypatch.setattr(delegate.urllib.request, "urlopen", fail)
    assert delegate.cmd_dispatch(_args("--pinned-head", "a" * 40, *flags)) == 2
    assert "PINNED_HEAD_TARGET_REQUIRED" in capsys.readouterr().err
    assert not tasks.exists()


@pytest.mark.parametrize("reused,local_head", [(False, "a" * 40), (True, "a" * 40), (True, "b" * 40)])
def test_branch_pin_is_exact_for_new_and_reused_worktrees(monkeypatch, tmp_path, reused, local_head):
    worktree = tmp_path / "worktree"
    if reused:
        worktree.mkdir()
    monkeypatch.setattr(delegate, "_validate_existing_worktree", lambda **_k: None)
    monkeypatch.setattr(delegate, "_fetch_existing_branch", lambda _b: None)
    monkeypatch.setattr(delegate, "_require_local_branch_is_ancestor_of_origin", lambda _b: "a" * 40)
    monkeypatch.setattr(delegate, "_resolve_sha", lambda _p: local_head)
    kwargs = dict(
        agent="codex",
        task_id="review-9272",
        validated_path=worktree,
        base="main",
        branch="codex/subject",
        pinned_head_sha="a" * 40,
    )
    if reused and local_head != "a" * 40:
        with pytest.raises(RuntimeError, match="differs from the pinned head SHA"):
            delegate._resolve_worktree_base_sha(**kwargs)
    else:
        assert delegate._resolve_worktree_base_sha(**kwargs) == "a" * 40
